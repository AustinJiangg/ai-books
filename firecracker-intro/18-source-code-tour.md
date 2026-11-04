# 18. 源码导读：Firecracker 代码库地图

> **《彻底搞懂 Firecracker》系列 · 第十八篇（终篇）**
>
> **读完本篇，你能：**
> - 了解 Firecracker 仓库的整体结构，知道每个目录是干什么的
> - 沿着“启动进程 → 处理 API → 构建虚拟机 → 运行 vCPU → 处理设备 I/O”的主线读懂关键代码
> - 找到前面每一篇讲过的机制在源码中的位置
> - 在 ARM64 机器上构建 Firecracker、运行测试，并做一个小修改
> - 知道如何继续深入和参与贡献
>
> **前置知识：** 本系列前 17 篇。能读懂基础的 Rust 语法（`struct`、`impl`、`enum`、`match`、`Result`）会很有帮助，但不是必须的——本篇以“找到并理解”为目标，而不是逐行讲解。
>
> **版本：** 以 2026 年 11 月的主线代码为参照（版本号 1.18.0-dev，与 v1.17.0 结构一致）。代码会持续演进，函数名和行号可能变化，请以你手上的代码为准。

---

## 引子：拿着地图进城

前 17 篇里，我们从外部观察 Firecracker：它做了什么、为什么这样做。这一篇我们走进它的内部。

一个十几万行代码（含测试）的项目，直接从第一行读起很容易迷路。正确的方法是**带着问题、沿着主线**：先建立全局地图，再顺着一次请求或一次 I/O 的路径深入，每次只关心与当前问题相关的代码。

---

## 一、获取代码

```bash
git clone https://github.com/firecracker-microvm/firecracker
cd firecracker
git checkout v1.17.0     # 如果想与本系列的版本基线一致；不切换则是最新主线
```

推荐用支持 Rust 的编辑器（如装了 rust-analyzer 的 VS Code）打开，便于跳转定义和查找引用。

---

## 二、仓库全景

```
firecracker/
├── src/                     Rust 源码（一个 Cargo workspace，含多个 crate）
│   ├── firecracker/         主程序：命令行解析、API 服务器、进程入口
│   ├── vmm/                 ★ 核心：虚拟机的构建、运行、设备、快照……
│   ├── jailer/              jailer 程序（第 14 篇）
│   ├── seccompiler/         seccomp 规则编译器（第 13 篇）
│   ├── snapshot-editor/     快照编辑工具（第 15 篇）
│   ├── rebase-snap/         旧的快照 rebase 工具（已弃用）
│   ├── cpu-template-helper/ CPU 模板辅助工具（第 16 篇）
│   ├── acpi-tables/         x86 ACPI 表生成
│   ├── utils/               通用小工具
│   ├── log-instrument*/     函数级追踪插桩（第 16 篇）
│   └── clippy-tracing/      代码检查辅助
├── resources/
│   ├── seccomp/             各架构的 seccomp 规则 JSON（第 13 篇）
│   ├── guest_configs/       官方 Guest 内核配置（含 ARM64）
│   ├── rootfs/              构建 CI rootfs 的脚本和文件（如 fcnet-setup.sh）
│   └── rebuild.sh           构建 CI 内核和 rootfs 的总脚本
├── tests/                   Python（pytest）编写的集成测试
│   ├── framework/           测试框架：启动 microVM、发 API 请求的封装
│   ├── host_tools/          测试用的宿主机工具（如内存测量）
│   └── integration_tests/   functional / performance / security / style / build
├── tools/
│   └── devtool              开发工具入口：在容器中构建、测试
├── docs/                    所有设计文档与使用文档（本系列大量参考）
├── SPECIFICATION.md         性能与稳定性承诺（第 04 篇）
├── CHANGELOG.md             版本变更记录
└── SECURITY.md              安全漏洞报告流程
```

### 2.1 核心 crate：`src/vmm/src/`

```
vmm/src/
├── lib.rs               Vmm 结构体：一台运行中的 microVM，暂停/恢复/停止
├── builder.rs           ★ 构建 microVM：从配置启动，或从快照恢复（第 08、15 篇）
├── resources.rs         VmResources：所有用户配置的集合
├── rpc_interface.rs     ★ API 动作的定义与分发（第 06 篇）
├── vmm_config/          每类配置的数据结构与校验（machine_config、boot_source、drive……）
├── vstate/              与 KVM 打交道的状态
│   ├── kvm.rs           打开 /dev/kvm，检查能力
│   ├── vm.rs            VM 级：内存槽注册、中断（irqfd）……
│   ├── vcpu.rs          ★ vCPU 线程、KVM_RUN 循环、退出处理（第 07 篇）
│   ├── memory.rs        Guest 内存的分配与映射（第 09 篇）
│   └── interrupts.rs    中断路由
├── arch/
│   ├── aarch64/         ★ ARM64 专属
│   │   ├── layout.rs    地址地图常量（第 08 篇）
│   │   ├── fdt.rs       生成设备树
│   │   ├── vcpu.rs      vCPU 初始化、启动寄存器、PSCI 特性
│   │   ├── regs.rs      ARM 寄存器的读写与保存
│   │   ├── gic/         vGIC（GICv2 / GICv3 / ITS）
│   │   ├── cache_info.rs 从宿主机读取缓存层级
│   │   ├── vm.rs、kvm.rs ARM64 的 VM 与 KVM 细节
│   │   └── mod.rs       内核加载、configure_system_for_boot
│   └── x86_64/          x86 专属（ACPI、CPUID、MSR……）
├── device_manager/      设备的注册：分配 MMIO 地址、中断号，注册 ioeventfd（第 10 篇）
├── devices/
│   ├── virtio/          ★ virtio 设备
│   │   ├── queue.rs     virtqueue 的实现（第 10 篇）
│   │   ├── transport/   mmio.rs 与 pci/（第 10 篇）
│   │   ├── net/ block/ vsock/ balloon/ rng/ mem/ pmem/
│   │   └── vhost_user.rs
│   ├── legacy/          串口、PL031 RTC、i8042（x86）……
│   ├── pseudo/          启动计时设备（第 16 篇）
│   ├── acpi/            VMGenID、VMClock 等
│   └── pci/             PCI 总线与根端口
├── mmds/                元数据服务（第 11 篇）
├── dumbo/               MMDS 用的极简网络协议栈（第 11 篇）
├── rate_limiter/        令牌桶限速器（第 12 篇）
├── io_uring/            Async 块设备引擎的 io_uring 封装（第 12 篇）
├── snapshot/、persist.rs 快照的序列化与恢复（第 15 篇）
├── cpu_config/          CPU 模板（第 16 篇）
├── seccomp.rs           加载 seccomp 过滤器（第 13 篇）
├── signal_handler.rs    SIGSYS、SIGBUS 等信号处理
├── logger/              日志与指标（第 06、16 篇）
└── gdb/                 Guest 内核调试支持（第 16 篇）
```

---

## 三、主线一：从 `main` 到 API 就绪

**入口：`src/firecracker/src/main.rs`**

```
main()
 └─ main_exec()
     ├─ 解析命令行参数（--api-sock、--config-file、--no-api、--enable-pci、--boot-timer……）
     ├─ 处理 --version、--snapshot-version、--describe-snapshot 等“打印后退出”的参数
     ├─ 初始化日志、指标
     ├─ resize_fdtable()：预先扩大文件描述符表（第 15 篇提到的恢复优化之一）
     ├─ 准备 seccomp 过滤器（内置的、--seccomp-filter 指定的、或 --no-seccomp）
     └─ 分两条路：
         ├─ --no-api：run_without_api()        → build_microvm_from_json() → 进入事件循环
         └─ 默认：    run_with_api()           （在 api_server_adapter.rs）
```

**`src/firecracker/src/api_server_adapter.rs` 中的 `run_with_api()`：**

1. 创建一对通道（`mpsc`）和一个 eventfd，用于 API 线程与 VMM 线程通信（第 06 篇第五节）；
2. 创建名为 `fc_api` 的线程，在其中安装 API 线程的 seccomp 过滤器，运行 HTTP 服务器（`src/firecracker/src/api_server/`）；
3. 当前线程（主线程，即 VMM 线程）进入“开机前”阶段：不断接收 API 指令，交给 `PrebootApiController` 处理，直到收到 `InstanceStart` 或 `LoadSnapshot`；
4. 虚拟机构建完成后，创建 `ApiServerAdapter` 作为事件循环的一个订阅者，此后的 API 请求由 `RuntimeApiController` 处理；
5. 进入 `event_manager.run()` 的无限循环。

**`src/firecracker/src/api_server/`：**

- `mod.rs`：基于 `micro_http` 的服务器循环；
- `parsed_request.rs`：把 HTTP 方法 + 路径映射到具体的请求解析函数；
- `request/` 目录：每个资源一个文件（`drive.rs`、`net.rs`、`machine_configuration.rs`……），负责把 JSON 反序列化成 `VmmAction`。

**`src/vmm/src/rpc_interface.rs`：**

- `enum VmmAction`：所有 API 动作的“总目录”，比如 `ConfigureBootSource`、`InsertBlockDevice`、`InsertNetworkDevice`、`StartMicroVm`、`CreateSnapshot`、`LoadSnapshot`、`Pause`、`Resume`……
- `PrebootApiController::handle_preboot_request()`：开机前的请求处理，大部分只是修改 `VmResources`；
- `RuntimeApiController::handle_request()`：运行时的请求处理，不被允许的操作会返回 `OperationNotSupportedPostBoot` 之类的错误。

> 🔍 **阅读练习 1：** 在 `parsed_request.rs` 中找到 `PUT /drives/{id}` 的处理入口，一路跟到 `VmResources` 中保存磁盘配置的地方。看看 `is_root_device` 是如何影响内核命令行的（提示：`vmm_config/boot_source.rs` 中的 `root=/dev/vda`）。

---

## 四、主线二：构建虚拟机

**`src/vmm/src/builder.rs` 中的 `build_microvm_for_boot()`**

这就是第 08 篇第一节那十个步骤的代码实现。对照阅读：

| 第 08 篇的步骤 | 代码中的位置 |
|--------------|------------|
| 分配 Guest 内存 | `vm_resources` 中分配内存的方法 → `vstate/memory.rs` |
| 准备内核命令行 | `boot_cmdline`；未启用 PCI 时插入 `pci=off` |
| 创建 VM、vCPU、vGIC | `Kvm::new()`、`KvmVm::new()`、`vm.create_vcpus()`（ARM64 上会调用 `setup_irqchip` → `arch/aarch64/gic/create_gic`，先尝试 GICv3 再退回 GICv2） |
| 注册内存 | `vm.register_dram_memory_regions()` |
| 加载内核 | `load_kernel()` → `arch/aarch64/mod.rs` 中用 `linux_loader` 的 PE 加载器 |
| 挂载设备 | `attach_block_devices()`、`attach_net_devices()`、`attach_unixsock_vsock_device()`…… → `device_manager/` |
| 配置 vCPU、生成 FDT | `configure_system_for_boot()` → `arch/aarch64/mod.rs` → `vcpu.configure()` 与 `fdt::create_fdt()` |
| 启动 vCPU 线程 | `vcpus` 被移入各自的线程，先处于暂停状态，随后恢复运行 |

从快照恢复的路径是同一个文件中的 `build_microvm_from_snapshot()`，它不加载内核、不生成 FDT，而是从快照状态中恢复 vCPU 寄存器和设备状态（各组件实现了 `snapshot/persist.rs` 中的 `Persist` trait，提供 `save()` 和 `restore()`）。

> 🔍 **阅读练习 2：** 打开 `arch/aarch64/vcpu.rs`，找到 `setup_boot_regs()`。确认第 08 篇第五节中的三个寄存器（PSTATE、PC、X0）是如何设置的，以及为什么只有 0 号 vCPU 设置 PC。

> 🔍 **阅读练习 3：** 打开 `arch/aarch64/fdt.rs`，找到 `create_fdt()`。对照你在第 08 篇导出的 `guest.dtb`，逐个找到每个节点是由哪个函数生成的。

---

## 五、主线三：vCPU 的一生

**`src/vmm/src/vstate/vcpu.rs`**

vCPU 线程被实现为一个**状态机**：

```
start_threaded()      创建名为 "fc_vcpu N" 的线程，在线程中安装 vCPU 的 seccomp 过滤器
   └─ run()           状态机主循环
       ├─ paused()    等待 Resume 等指令（第 07 篇第五节的 VcpuEvent）
       └─ running()   反复调用 run_emulation()，同时检查是否收到暂停/退出指令
              └─ run_emulation()
                  └─ KVM_RUN，然后 match 退出原因：
                      MmioRead / MmioWrite → 交给 MMIO 总线（vstate/bus.rs）找到设备处理
                      SystemEvent          → PSCI 关机/重启 → 结束 microVM
                      FailEntry / InternalError → 报错
                      被信号打断（EINTR）   → 返回状态机检查指令
```

MMIO 总线（`vstate/bus.rs`）就是一张“地址区间 → 设备对象”的表：vCPU 线程拿到退出地址，在表里查到对应的设备，调用它的 `read` 或 `write`。

> 🔍 **阅读练习 4：** 在 `vcpu.rs` 中找到注册信号处理函数的地方（搜索 `sigrtmin`），理解 VMM 线程是如何“踢醒”一个正在 `KVM_RUN` 中的 vCPU 线程的。

---

## 六、主线四：一次 virtio I/O

### 6.1 设备的注册

**`src/vmm/src/device_manager/mmio.rs`**：为每个 virtio 设备分配一段 MMIO 地址（4 KiB）和一个中断号，把设备的传输层对象挂到 MMIO 总线上，并为每个队列调用 `register_ioevent()`——这就是第 10 篇的 ioeventfd：当 Guest 往该设备的 `QueueNotify` 地址写入队列号时，KVM 直接触发对应的 eventfd。

### 6.2 传输层的寄存器处理

**`src/vmm/src/devices/virtio/transport/mmio.rs`**：

- `read()` / `write()`：根据偏移量处理第 10 篇表格中的各个寄存器。比如偏移 `0x70` 是设备状态寄存器，写入时调用 `set_device_status()`；
- 文件开头可以看到 `MMIO_MAGIC_VALUE = 0x7472_6976`（`"virt"`）；
- 当状态变为 `DRIVER_OK` 时，调用设备的激活逻辑。

### 6.3 队列

**`src/vmm/src/devices/virtio/queue.rs`**：

| 函数 | 作用 |
|------|------|
| `Queue::initialize()` | 激活时校验描述符表、可用环、已用环的地址是否落在 Guest 内存中 |
| `Queue::pop()` | 从可用环取出下一个请求，返回 `DescriptorChain` |
| `DescriptorChain::next_descriptor()` | 沿着描述符链走到下一个 |
| `Queue::add_used()` | 往已用环写入一个完成项 |
| `Queue::prepare_kick()` | 结合 EVENT_IDX 判断是否需要给 Guest 发中断 |
| `enable_notification()` 等 | 通知抑制 |

### 6.4 设备实现：以网卡为例

**`src/vmm/src/devices/virtio/net/`**：

- `event_handler.rs`：实现事件循环的订阅者接口，声明要监听的 fd（TX/RX 队列的 eventfd、TAP 的 fd、限速器的定时器），事件到来时分发；
- `device.rs`：
  - `process_tx_queue_event()` → `process_tx()`：从 TX 队列取包，检查限速器，判断是否发往 MMDS（交给 `dumbo`），否则写入 TAP；
  - `process_rx_queue_event()`、TAP 可读事件 → `process_rx()`：从 TAP 读包，写入 Guest 预先提供的 RX 缓冲区；
  - `process_rx_rate_limiter_event()` / `process_tx_rate_limiter_event()`：限速器定时器到期后恢复处理；
- `tap.rs`：打开 `/dev/net/tun`，绑定 TAP 设备，设置 vnet header 和卸载特性。

块设备在 `devices/virtio/block/virtio/` 中，入口是 `process_queue_event()`；同步与 io_uring 两种引擎在其下的 `io/` 目录中。

> 🔍 **阅读练习 5：** 跟踪第 07 篇第七节“Guest 发送一个网络包”的完整路径：从 `event_handler.rs` 收到 TX 队列事件开始，到 `tap.rs` 中写入 TAP 为止。记下途中经过的每个函数。

---

## 七、其他值得一看的地方

| 主题 | 位置 | 关联篇章 |
|------|------|---------|
| seccomp 规则 | `resources/seccomp/aarch64-unknown-linux-musl.json`；加载逻辑在 `src/vmm/src/seccomp.rs` | 13 |
| jailer 的每个步骤 | `src/jailer/src/env.rs`（chroot、pivot_root、mknod、降权、PID 文件）、`cgroup.rs`（cgroup v1/v2） | 14 |
| 令牌桶 | `src/vmm/src/rate_limiter/` | 12 |
| MMDS | `src/vmm/src/mmds/`（数据存储、令牌） + `src/vmm/src/dumbo/`（ARP/IP/TCP） | 11 |
| 气球 | `src/vmm/src/devices/virtio/balloon/` | 09 |
| vsock 与 Unix socket 的转接 | `src/vmm/src/devices/virtio/vsock/` | 11 |
| 启动计时设备 | `src/vmm/src/devices/pseudo/boot_timer.rs`（魔数 123） | 16 |
| 快照的版本与 CRC | `src/vmm/src/snapshot/` | 15 |
| 默认内核命令行 | `src/vmm/src/vmm_config/boot_source.rs` 中的 `DEFAULT_KERNEL_CMDLINE` | 08 |
| 指标的定义 | `src/vmm/src/logger/metrics.rs` | 16 |
| 形式化验证 | 代码中带 `#[cfg(kani)]` 的模块，例如 `arch/aarch64/mod.rs` 末尾验证内存区域划分的证明 | 13 |
| API 规范 | `src/firecracker/swagger/firecracker.yaml` | 06 |

---

## 八、动手：构建、测试、修改

### 8.1 构建

官方推荐使用 `tools/devtool`，它在一个预先准备好的容器里构建，保证工具链一致。宿主机需要安装并运行 Docker：

```bash
cd firecracker
tools/devtool build              # 调试版
tools/devtool build --release    # 发布版
ls build/cargo_target/aarch64-unknown-linux-musl/debug/
```

产物包括 `firecracker`、`jailer` 等，可以直接替换第 05 篇中下载的二进制来使用。

> 💡 调试版的 Firecracker 默认使用空的 seccomp 过滤器（避免调试断言触发未预期的系统调用），所以不要用调试版做安全相关的实验。

### 8.2 运行测试

```bash
tools/devtool test -- integration_tests/functional/test_api.py   # 运行某个集成测试文件
tools/devtool test -- --ignore integration_tests/performance      # 跳过性能测试
```

单元测试散布在各个源码文件末尾的 `#[cfg(test)] mod tests` 里；集成测试在 `tests/integration_tests/` 下，用 Python 编写，通过 `tests/framework/` 启动真正的 microVM 并检查行为。性能测试的基线是在 AWS `.metal` 实例上测得的，在其他机器上运行不通过是正常的。

### 8.3 一个小修改：在 MMIO 退出时打印日志

为了亲眼看到第 10 篇描述的初始化握手，我们在 virtio-mmio 的状态寄存器写入处加一行日志。

打开 `src/vmm/src/devices/virtio/transport/mmio.rs`，找到 `write()` 中处理偏移 `0x70` 的分支（`0x70 => self.set_device_status(v)`），改成：

```rust
0x70 => {
    crate::logger::info_unrestricted!(
        "virtio-mmio @ {:#x}: driver writes status {:#04x}", base, v
    );
    self.set_device_status(v)
}
```

几点说明：`base` 是 `write()` 的参数，表示设备的 MMIO 基地址；这里特意用 `info_unrestricted!` 而不是 `info!`，因为从 v1.16 起普通的 `info!` 会按调用点限速（每 5 秒最多 10 条），而这一处在启动时会被多个设备连续触发，可能有日志被丢弃。如果你的版本中宏的名字不同，参照文件中已有的日志调用调整即可。

重新构建，用新的二进制启动 microVM（日志级别 `Info`），然后查看日志：

```bash
grep 'driver writes status' firecracker.log
```

你会看到每个 virtio 设备依次被写入 `0x00` → `0x01` → `0x03` → `0x0b` → `0x0f`，对应 第 10 篇的 重置 → ACKNOWLEDGE → +DRIVER → +FEATURES_OK → +DRIVER_OK。理论和实践在这里完全对上了。

---

## 九、继续深入

### 9.1 推荐的阅读顺序

1. `docs/design.md`：官方设计文档，篇幅不长；
2. `src/vmm/src/builder.rs`：一次读懂虚拟机是如何拼装起来的；
3. `src/vmm/src/vstate/vcpu.rs`：vCPU 状态机；
4. `src/vmm/src/devices/virtio/queue.rs` + 任意一个设备（推荐 `rng`，最简单）；
5. `src/vmm/src/arch/aarch64/`：ARM64 的所有特殊处理；
6. 某个你感兴趣的特性的完整实现（快照、MMDS、气球……）。

### 9.2 相关的上游项目

- **rust-vmm**（GitHub 上的 `rust-vmm` 组织）：`kvm-ioctls`、`vm-memory`、`linux-loader`、`event-manager`、`vm-superio`、`vm-fdt` 等库的源码；
- **Linux 内核**：`arch/arm64/kvm/`（ARM64 KVM 实现）、`virt/kvm/`（通用 KVM）、`drivers/virtio/`（Guest 侧 virtio 驱动），以及 `Documentation/virt/kvm/api.rst`（KVM API 的权威文档）；
- **virtio 规范**：OASIS 发布的 *Virtual I/O Device (VIRTIO) Specification*；
- **Cloud Hypervisor**：另一个基于 rust-vmm 的 VMM，代码结构有不少相似之处，对比阅读很有收获。

### 9.3 参与贡献

- 阅读仓库中的 `CONTRIBUTING.md`，了解提交 PR 的流程和代码规范（例如提交需要签署 DCO）；
- 从文档改进、测试补充或标记为适合新手的 issue 入手；
- 安全问题**不要**在公开 issue 中提交，按照 `SECURITY.md` 中的流程报告。

---

## 全系列回顾

```
第一部分 打地基
  01 电脑如何运转 ─ 02 虚拟化路线 ─ 03 ARM64 硬件虚拟化与 KVM
第二部分 认识 Firecracker
  04 是什么、为什么 ─ 05 第一台 microVM ─ 06 API
第三部分 内部原理
  07 线程模型 ─ 08 启动过程 ─ 09 内存 ─ 10 virtio ─ 11 网络 ─ 12 存储
第四部分 安全
  13 安全模型与 seccomp ─ 14 jailer
第五部分 高级特性与生产实践
  15 快照 ─ 16 性能与可观测性 ─ 17 生态
第六部分 融会贯通
  18 源码导读
```

如果要用一句话总结 Firecracker：**它用硬件虚拟化获得隔离，用极简的设备模型、Rust 和多层沙箱获得安全，用“只做必要的事”获得速度和密度。** 现在，你已经能从 ARM64 的 EL2 一路讲到 virtqueue 的描述符，从 seccomp 规则讲到快照的唯一性陷阱——希望你在之后的实践中，能把这些知识用在构建真正的系统上。

---

## 思考题

1. 为什么开机前的请求由 `PrebootApiController` 处理，运行时由 `RuntimeApiController` 处理？把它们合并成一个会有什么问题？
2. 在 `queue.rs` 中，`pop()` 返回的是 `Result<Option<…>, InvalidAvailIdx>`。三种可能的结果分别对应什么情况？
3. 如果要给 Firecracker 增加一种新的 virtio 设备，需要修改哪些地方？（提示：API、配置、设备实现、device_manager、快照、seccomp、文档、测试）
4. 在你做的“打印设备状态”实验里，为什么状态值是 `0x0b` 而不是 `0x08`？
5. 选一个你最感兴趣的特性，用一页纸写出它从 API 请求到底层系统调用的完整调用链。

---

## 附录

术语表、排错手册和推荐阅读见 **[附录](19-appendix.md)**。想继续按代码深入 Firecracker（含 e2b 定制版、ARM 适配与 checkpoint 扩展），可以接着读本仓库的《Firecracker 技术手册》（[网页版](https://austinjiangg.github.io/ai-books/html/firecracker.html) · [Markdown](../firecracker/README.md)）。
