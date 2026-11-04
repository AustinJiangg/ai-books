# 16. 性能与可观测性

> **《彻底搞懂 Firecracker》系列 · 第十六篇**
>
> **读完本篇，你能：**
> - 说清楚“microVM 的性能”具体包括哪些可测量的指标
> - 动手测量启动时间、内存开销、网络和磁盘吞吐
> - 知道影响这些指标的主要因素以及对应的调优手段
> - 理解 CPU 模板的用途，学会在 ARM64 上使用它
> - 读懂 Firecracker 的指标输出，用宿主机工具定位瓶颈
>
> **前置知识：** 第 05～12 篇。
>
> **版本：** Firecracker v1.17.0，ARM64。

---

## 引子：先测量，再优化

性能调优最常见的错误是“凭感觉优化”。这一篇的思路是：

1. 先明确要关心哪些指标；
2. 学会准确地测量它们；
3. 理解每个指标受什么因素影响；
4. 最后才是调优。

---

## 一、要关心哪些指标

| 类别 | 指标 | 对谁重要 |
|------|------|---------|
| 启动 | VMM 进程就绪时间、从 `InstanceStart` 到 Guest `init`、到应用可服务 | Serverless 冷启动 |
| 快照 | 加载耗时、恢复后首个请求的延迟 | 预热池、快速伸缩 |
| 密度 | 每台 microVM 的额外内存开销、每秒可创建的数量 | 成本 |
| 计算 | Guest 内 CPU 密集任务相对裸机的性能 | 计算型负载 |
| I/O | 网络吞吐与延迟、磁盘吞吐与 IOPS、VMM 线程 CPU 占用 | 数据密集型负载 |

回顾第 04 篇的官方承诺：VMM 启动约 8 CPU 毫秒、启动到 init ≤125 毫秒、VMM 内存开销 ≤5 MiB、计算性能 >95% 裸机。这些数字都有严格前提，你自己的测量结果应该和你自己的配置比较，而不是和这些数字直接比较。

---

## 二、测量启动时间

### 2.1 启动时间的组成

```
  启动 firecracker 进程
       │  ① VMM 就绪（API socket 可用）           官方：约 8 CPU 毫秒
       ▼
  配置（若干 API 请求）
       │  ② 配置耗时                              取决于你的编排系统
       ▼
  InstanceStart
       │  ③ VMM 搭建虚拟机（第 08 篇的十个步骤）    几毫秒
       ▼
  Guest 内核开始执行
       │  ④ 内核启动                              取决于内核配置、设备数量、串口
       ▼
  /sbin/init 开始执行                            官方：③+④ ≤125 毫秒
       │  ⑤ 用户态启动                            取决于 init 系统（systemd vs 简单脚本）
       ▼
  应用就绪（可以处理请求）
```

### 2.2 方法一：启动计时设备（--boot-timer）

Firecracker 提供了一个专门用于测量启动时间的“伪设备”。启动时加上 `--boot-timer` 参数，它会出现在 MMIO 区域的起始位置（ARM64 上是 `0x4000_0000`）。当 Guest 往这个地址写入字节值 `123` 时，Firecracker 会在日志中打印从开始启动到此刻经过的时间：

```
Guest-boot-time =  95123 us 95 ms,  28456 CPU us 28 CPU ms
```

Guest 应该在“认为自己启动完成”的时刻写入这个值——比如 init 脚本的最后一步。在 Guest 中写物理地址需要 `/dev/mem` 访问权限（Guest 内核需开启 `CONFIG_DEVMEM`），例如用一小段 Python：

```python
# Guest 内，以 root 运行
import mmap, os
fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
m = mmap.mmap(fd, 4096, mmap.MAP_SHARED, mmap.PROT_WRITE, offset=0x40000000)
m[0] = 123
```

如果 Guest 里有带 `devmem` 小工具的 busybox，也可以用 `devmem 0x40000000 8 123`。

### 2.3 方法二：外部计时

不修改 Guest 的话，可以在宿主机上计时“从开始到某个可观察事件”，比如第 08 篇中“直到能 SSH 登录”的脚本。也可以把串口输出接到一个程序，记录看到某行特定文字（如 `login:`）的时刻。

### 2.4 Guest 内部分析

```bash
dmesg | head -3                         # 内核最早的时间戳
dmesg | grep -E 'Run /sbin/init|Run /init'
systemd-analyze                         # 如果使用 systemd
systemd-analyze blame | head
```

### 2.5 动手：启动时间对比实验

准备四种配置，各启动 10 次取中位数：

| 实验 | 内核参数 | rootfs |
|------|---------|--------|
| A | `console=ttyS0 reboot=k panic=1` | Ubuntu（systemd） |
| B | `reboot=k panic=1 8250.nr_uarts=0`（关闭串口） | Ubuntu |
| C | `console=ttyS0 reboot=k panic=1 init=/init` | Alpine 最小 rootfs（第 12 篇） |
| D | 与 B 相同，再加 `huge_pages: "2M"` | Ubuntu |

一个简单的批量测试脚本骨架：

```bash
#!/bin/bash
# 用法：sudo ./boottest.sh vm_config.json 10
CONFIG=$1; N=${2:-10}
for i in $(seq 1 $N); do
  rm -f /tmp/fc.sock /tmp/fc.log
  start=$(date +%s%N)
  ./firecracker --api-sock /tmp/fc.sock --config-file $CONFIG \
      --boot-timer --log-path /tmp/fc.log --level Info > /tmp/fc.out 2>&1 &
  PID=$!
  # 等待 Guest 写入启动完成信号（需要 Guest 在启动末尾写 123 到 0x40000000）
  until grep -q 'Guest-boot-time' /tmp/fc.log 2>/dev/null; do sleep 0.005; done
  grep -o 'Guest-boot-time = *[0-9]* us' /tmp/fc.log
  kill $PID; wait $PID 2>/dev/null
done
```

你应该能观察到：关闭串口（B vs A）和更简单的 init（C vs A）对启动时间影响都非常显著。

### 2.6 加快启动的手段

| 手段 | 原理 |
|------|------|
| **关闭串口控制台** | 每个字符都是一次 MMIO 退出，内核启动日志有数百行 |
| 内核参数加 `quiet` | 减少日志输出量 |
| **精简 Guest 内核** | 只编译需要的驱动，去掉模块加载、不需要的子系统。可以参考官方仓库 `resources/guest_configs/` 中 ARM64 的 microVM 内核配置 |
| **精简用户态** | 用简单的 init 或专门的 Guest 代理代替完整的 systemd |
| 使用大页 | 减少 Stage-2 缺页次数（第 09 篇），官方测试显示可显著缩短启动时间 |
| 用快照代替启动 | 把以上全部跳过（第 15 篇） |
| 预热镜像的宿主机页缓存 | 内核和 rootfs 的读取不必访问磁盘 |
| 减少设备数量 | 每个设备都需要 Guest 驱动初始化 |

---

## 三、测量内存开销

### 3.1 区分“Guest 内存”和“VMM 开销”

Firecracker 进程的 RSS 包括两部分：Guest 内存中被访问过的页，以及 VMM 自身的开销（代码、堆、设备缓冲区等）。要分开看，可以查看进程的内存映射：

```bash
FC_PID=$(pgrep -f 'firecracker --api-sock' | head -1)

# 列出最大的几块映射，Guest 内存是那块大小等于 mem_size_mib 的匿名映射
sudo awk '/^[0-9a-f]+-[0-9a-f]+ /{range=$1} /^Rss:/{print $2, range}' /proc/$FC_PID/smaps \
    | sort -n -r | head -5

# 总 RSS
grep VmRSS /proc/$FC_PID/status
```

总 RSS 减去 Guest 内存映射的 RSS，就是 VMM 的额外开销。按官方规格，1 vCPU、128 MiB 的配置下，这部分应在 5 MiB 左右（取决于设备配置和负载）。

### 3.2 降低 Guest 内存占用

回顾第 09 篇：气球设备、空闲页报告、大页的取舍、快照共享页缓存，都会影响宿主机上的实际内存占用。

---

## 四、测量 I/O 性能

### 4.1 网络

```bash
# 宿主机
iperf3 -s -B 172.16.0.1

# Guest 内（需要安装 iperf3）
iperf3 -c 172.16.0.1 -t 20          # Guest → Host
iperf3 -c 172.16.0.1 -t 20 -R       # Host → Guest
```

同时在宿主机上观察各线程的 CPU 占用：

```bash
top -H -p $FC_PID
# 或者
pidstat -t -p $FC_PID 1
```

通常你会看到 VMM 线程（`firecracker`）的 CPU 占用很高——它在搬运所有数据包。当它接近 100% 时，就是单 VMM 线程的瓶颈（第 07 篇）。

影响网络性能的因素：

| 因素 | 说明 |
|------|------|
| PCI vs MMIO | PCI 模式下的 MSI-X 中断减少了退出次数（第 10 篇） |
| Guest 是否启用了卸载特性 | TSO、校验和卸载、MRG_RXBUF 能大幅减少包数量 |
| MTU | 更大的 MTU 意味着更少的包；v1.16 起可以通过 `mtu` 字段告知 Guest |
| VMM 线程是否独占一个核 | 与 vCPU 线程或其他进程抢 CPU 会降低吞吐 |
| 限速器 | 确认没有意外配置限速 |

### 4.2 磁盘

使用 `fio` 是最标准的方法：

```bash
# Guest 内：对数据盘 /dev/vdb 做 4K 随机读测试（直接 I/O，绕过 Guest 缓存）
fio --name=randread --filename=/dev/vdb --rw=randread --bs=4k \
    --iodepth=32 --ioengine=libaio --direct=1 --runtime=30 --time_based

# 顺序读吞吐
fio --name=seqread --filename=/dev/vdb --rw=read --bs=1M \
    --iodepth=8 --ioengine=libaio --direct=1 --runtime=30 --time_based
```

可以分别比较：`io_engine` 为 `Sync` 与 `Async`、后端文件在宿主机页缓存中与不在、`cache_type` 不同取值等情况下的结果。注意宿主机页缓存会让读测试结果“好得不真实”，测量真实磁盘性能前可以在宿主机上执行 `echo 3 | sudo tee /proc/sys/vm/drop_caches`。

---

## 五、CPU 层面的调优

### 5.1 vCPU 数量

- vCPU 是宿主机线程，**分配多于物理核心数的 vCPU 不会带来更多算力**，反而增加调度开销；
- 对单线程应用，1 个 vCPU 往往就够了，多出来的 vCPU 只会让 Guest 内核付出额外的同步成本；
- 超卖时，要考虑所有 microVM 同时繁忙的最坏情况。

### 5.2 绑核

用 cgroup 的 `cpuset`（jailer 的 `--cgroup cpuset.cpus=...`）把一台 microVM 的线程限定在特定的物理核上，可以：

- 减少线程在核之间迁移带来的缓存失效；
- 避免与其他租户共享核（降低侧信道风险，第 13 篇）；
- 在 NUMA 机器上，配合 `cpuset.mems` 把内存和 CPU 固定在同一个 NUMA 节点。

更细粒度的做法是：把 vCPU 线程和 VMM 线程分别绑到不同的核上（需要在 Firecracker 启动后，根据线程名找到线程 ID 再设置）。

### 5.3 CPU 模板

**问题：** Guest 内核和程序启动时会检测 CPU 支持哪些特性（指令集扩展、安全特性等），然后据此选择代码路径。这带来两个问题：

1. **快照的可移植性**：在支持特性 X 的机器上创建的快照，恢复到不支持 X 的机器上，Guest 一旦使用 X 就会崩溃；
2. **一致性与安全**：不同宿主机的 CPU 差异暴露给 Guest，可能泄露硬件信息，也让行为不一致。

**CPU 模板**的作用就是控制 Guest 看到的 CPU 特性：隐藏一部分，让不同型号的宿主机呈现出相同的“CPU 画像”。

在 ARM64 上，CPU 特性通过一组 ID 寄存器（如 `ID_AA64ISAR0_EL1`、`ID_AA64PFR0_EL1` 等）描述。Firecracker 的 CPU 模板可以修改这些寄存器中的特定位，也可以指定 vCPU 初始化特性和要求的 KVM 能力。

**静态模板：** ARM64 上有一个预置模板 **V1N1**，让 Neoverse V1 处理器（如 Graviton3）对 Guest 呈现为 Neoverse N1（如 Graviton2），从而让快照可以在这两代处理器之间迁移。发布包中附带了它的 JSON 定义（`V1N1-v1.17.0.json`）。

**自定义模板：** 通过 `PUT /cpu-config` 提供，ARM64 上的格式类似：

```json
{
  "kvm_capabilities": ["171", "172"],
  "vcpu_features": [ { "index": 0, "bitmap": "0b11xxxxx" } ],
  "reg_modifiers": [
    {
      "addr": "0x603000000013c020",
      "bitmap": "0bxxxxxxxxxxxx0000xxxxxxxxxxxx0000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
  ]
}
```

| 字段 | 含义 |
|------|------|
| `kvm_capabilities` | 要求宿主机 KVM 必须具备的能力编号（前面加 `!` 表示不检查某项默认能力） |
| `vcpu_features` | 修改 `KVM_ARM_VCPU_INIT` 的特性位，如启用指针认证 |
| `reg_modifiers` | 修改某个寄存器：`addr` 是 KVM 的寄存器 ID，`bitmap` 中 `0`/`1` 表示强制设置该位，`x` 表示保持原值 |

上面这个示例（来自官方文档）的作用是：要求宿主机支持指针认证，为 vCPU 开启指针认证特性，并把某个寄存器的两组 4 位字段清零。v1.17 起，在 6.15 以上的宿主内核上，模板还可以修改 `MIDR_EL1` 等实现标识寄存器。

**cpu-template-helper 工具：** 发布包中的这个工具帮助你制作和维护模板：

```bash
CTH=$(ls release-*/cpu-template-helper-* | grep -v debug)

# 在每种型号的宿主机上导出“Guest 默认看到的 CPU 配置”
sudo $CTH template dump --output cpu-config-hostA.json

# 对比多台机器的导出结果，去掉相同部分，得到差异
$CTH template strip --paths cpu-config-hostA.json cpu-config-hostB.json --suffix _stripped

# 验证模板在当前宿主机上能否生效
sudo $CTH template verify --template my-template.json

# 记录宿主机的“CPU 指纹”，日后对比以发现固件或内核升级带来的变化
sudo $CTH fingerprint dump --output fingerprint-hostA.json
```

---

## 六、可观测性

### 6.1 Firecracker 指标

配置 `/metrics` 后（第 06 篇），Firecracker 每 60 秒输出一行 JSON。一些最有用的字段：

| 分组 | 字段示例 | 用途 |
|------|---------|------|
| `api_server` | 进程启动时间、各类请求计数 | 控制面健康状况 |
| `vcpu` | `exit_mmio_read`、`exit_mmio_write`，以及对应的延迟统计（最小/最大/总和） | 判断 MMIO 退出是否过多 |
| `block`、`block_<drive_id>` | 读写字节数、请求数、`flush_count`、限速器节流次数、I/O 延迟 | 磁盘负载与瓶颈 |
| `net`、`net_<iface_id>` | 收发字节数与包数、TAP 读写失败、限速器节流次数、`tx_spoofed_mac_count` | 网络负载、异常行为 |
| `vsock`、`balloon`、`entropy` | 各设备的计数 | |
| `seccomp` | `num_faults` | **安全告警**，正常应为 0 |
| `latencies_us` | 暂停、恢复、创建/加载快照的耗时 | 快照性能 |
| `uart` | 串口读写计数、限速丢弃的字节数 | 串口滥用 |

v1.17 起还可以通过 `emit_id` 和 `properties` 字段在每条指标中带上实例 ID 和自定义标签，方便集中收集。

计算某个时间段的速率时，注意大多数计数器是**自上次输出以来的增量**，而非累计值（具体以官方 `docs/metrics.md` 为准）。

### 6.2 日志

- 生产环境使用 `Info` 或 `Warning` 级别；调试时临时调到 `Debug`；
- v1.16 起，`Error`/`Warning`/`Info` 级别的日志按调用点限速（每 5 秒每处最多 10 条），防止日志被刷爆；
- 日志写入命名管道时，如果管道满了，日志会丢失，并在 `logger` 指标中计数。

### 6.3 宿主机工具

| 工具 | 用途 |
|------|------|
| `top -H`、`pidstat -t` | 按线程看 CPU 占用：区分 vCPU 与 VMM 线程 |
| `perf top -p <PID>`、`perf record` | 定位 VMM 线程在哪些函数上花时间（发布包附带了 `.debug` 符号文件） |
| `strace -c -p <TID>` | 统计某个线程的系统调用 |
| `/proc/<PID>/smaps` | 内存映射分析 |
| `/sys/kernel/debug/kvm/` | KVM 的全局与每 VM 统计（需挂载 debugfs，以 root 查看），如各类退出次数 |
| bpftrace / eBPF 工具 | 追踪 KVM 事件、TAP 收发等内核路径 |

### 6.4 更深入的调试

- **GDB 调试 Guest 内核**（v1.10 起）：用带 `gdb` 特性编译的 Firecracker，可以把 GDB 连接到 Guest 内核进行源码级调试，见官方 `docs/gdb-debugging.md`；
- **追踪（tracing）**：编译时开启函数级插桩，记录 Firecracker 内部函数的调用和耗时，见 `docs/tracing.md`。

这两项都需要自己编译 Firecracker，属于开发调试用途，不用于生产。

---

## 七、调优速查表

| 目标 | 首先尝试 |
|------|---------|
| 启动更快 | 关串口、精简内核与 init、大页、快照 |
| 内存更省 | 合理设定 `mem_size_mib`、气球/空闲页报告、共享只读镜像（pmem）、快照共享页缓存 |
| 网络更快 | PCI 传输、确认卸载特性生效、VMM 线程独占核、合适的 MTU |
| 磁盘更快 | `Async` 引擎（评估风险）、后端放本地 SSD、`Unsafe` 缓存模式、PCI 传输 |
| 延迟更稳 | 绑核、关闭超卖、NUMA 亲和 |
| 快照可迁移 | CPU 模板统一特性，同型号宿主机 |

---

## 小结

| 要点 | 内容 |
|------|------|
| 启动测量 | `--boot-timer` + Guest 写 123 到 `0x4000_0000`；或外部计时 |
| 内存测量 | 进程 RSS 减去 Guest 内存映射的 RSS |
| I/O 测量 | `iperf3`、`fio`，同时观察 VMM 线程 CPU |
| 最大启动瓶颈 | 串口输出、systemd、未精简的内核 |
| CPU 模板 | 控制 Guest 可见的 CPU 特性；ARM64 有 V1N1 静态模板和自定义模板 |
| 指标 | 每 60 秒输出；`seccomp.num_faults` 是安全告警 |

---

## 思考题

1. 为什么关闭串口能显著加快启动？用第 03、10 篇的知识解释。
2. 一台 microVM 的网络吞吐上不去，你观察到 VMM 线程 CPU 只有 30%，而某个 vCPU 线程接近 100%。瓶颈可能在哪里？
3. 使用 V1N1 模板后，Guest 在 Graviton3 上运行会失去哪些能力？换来了什么？
4. 测量“VMM 内存开销”时，为什么要在 Guest 启动完成后再测，而不是刚启动 Firecracker 进程时测？
5. 如何设计一个实验，证明“多台 microVM 从同一快照恢复时共享了宿主机页缓存”？

---

## 下一篇预告

**[17. 生态与真实应用](17-ecosystem.md)**

Firecracker 只是一个零件。下一篇看看它被装进了哪些“整车”：AWS Lambda 与 Fargate、Kata Containers、firecracker-containerd、AI 代码沙箱，以及如果你要自己搭一个 microVM 平台，需要考虑哪些组件。
