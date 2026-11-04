# 10. 设备模型：virtio-mmio 全解析

> **《彻底搞懂 Firecracker》系列 · 第十篇**
>
> **读完本篇，你能理解：**
> - virtio 规范的三层结构：设备类型、传输方式、虚拟队列
> - virtio-mmio 的寄存器布局，以及 Guest 驱动初始化设备的完整握手流程
> - virtqueue（分离式环形队列）的三个组成部分和数据流动方式
> - ioeventfd 与 irqfd 如何把“通知”和“中断”的开销降到最低
> - ARM64 上中断是怎样从 Firecracker 送到 Guest 的
> - Firecracker 如何防御恶意 Guest 构造的队列数据
> - MMIO 与 PCI 两种传输方式的区别
>
> **前置知识：** 第 02 篇（virtio 简介）、第 03 篇（MMIO 退出、vGIC）、第 07 篇（事件循环、eventfd）、第 09 篇（Guest 内存与 VMM 共享）。
>
> **版本：** Firecracker v1.17.0，ARM64。

---

## 引子：餐厅的点菜单与出菜口

回到第 07 篇的餐厅：Guest 是顾客，Firecracker 的 VMM 线程是后厨。virtio 定义的就是**顾客和后厨之间的协作方式**：

- **点菜单（描述符表）**：顾客写下“我要什么，放在哪个盘子里”；
- **待做队列（可用环）**：顾客把点菜单的编号挂到后厨窗口；
- **出菜队列（已用环）**：后厨做完，把编号挂到出菜窗口；
- **叫号铃（通知）**：顾客挂好单后按一下铃；
- **广播（中断）**：后厨出菜后广播一声。

关键在于：顾客可以一次挂好几张单再按一次铃，后厨也可以一次出好几道菜再广播一次。这一篇就把这套流程讲透。

---

## 一、virtio 的三层结构

virtio 是由 OASIS 组织维护的开放标准（当前为 1.x 版本）。它分为三层：

```
┌──────────────────────────────────────────────────┐
│ 设备类型层：网卡、块设备、vsock、气球、熵源……           │  “这是什么设备，有哪些专属配置和请求格式”
├──────────────────────────────────────────────────┤
│ 虚拟队列层：virtqueue（描述符表 + 可用环 + 已用环）     │  “数据怎么在 Guest 和设备之间传递”
├──────────────────────────────────────────────────┤
│ 传输层：MMIO、PCI、Channel I/O（大型机）             │  “Guest 怎么发现设备、怎么访问它的寄存器”
└──────────────────────────────────────────────────┘
```

三层彼此独立：同一个 virtio-net 设备，可以通过 MMIO 呈现，也可以通过 PCI 呈现，上层逻辑完全不变。Firecracker 的代码结构也是这样划分的：`devices/virtio/` 下按设备类型分目录（`net`、`block`、`vsock`……），`devices/virtio/transport/` 下是 MMIO 和 PCI 两种传输实现，`devices/virtio/queue.rs` 实现虚拟队列。

### 1.1 Firecracker 支持的 virtio 设备

| 设备 | virtio 设备 ID | Guest 驱动（内核配置项） | 后端 |
|------|--------------|----------------------|------|
| net | 1 | `CONFIG_VIRTIO_NET` | 宿主机 TAP 设备 |
| block | 2 | `CONFIG_VIRTIO_BLK` | 宿主机文件或块设备 |
| rng（熵源） | 4 | `CONFIG_HW_RANDOM_VIRTIO` | 宿主机 `getrandom` |
| balloon | 5 | `CONFIG_VIRTIO_BALLOON` | Guest 内存本身 |
| vsock | 19 | `CONFIG_VIRTIO_VSOCKETS` | 宿主机 Unix socket |
| mem | 24 | `CONFIG_VIRTIO_MEM` | Guest 内存的可热插拔区域 |
| pmem | 27 | `CONFIG_VIRTIO_PMEM` | 宿主机文件，直接映射为 Guest 内存 |

在 Guest 里可以验证：

```bash
for d in /sys/bus/virtio/devices/*; do
  echo "$(basename $d): device=$(cat $d/device) driver=$(basename $(readlink $d/driver))"
done
```

---

## 二、virtio-mmio 传输层

### 2.1 寄存器布局

每个 virtio-mmio 设备在 Guest 物理地址空间里占一个 4 KiB 的窗口（第 08 篇地址地图中 `0x4000_3000` 起的那些）。窗口内的寄存器按 virtio 规范定义：

| 偏移 | 寄存器 | 方向 | 作用 |
|------|-------|------|------|
| `0x000` | MagicValue | 读 | 固定为 `0x74726976`，即小端序的 ASCII `"virt"` |
| `0x004` | Version | 读 | 2 表示现代（非传统）virtio-mmio |
| `0x008` | DeviceID | 读 | 设备类型，如 1=网卡、2=块设备 |
| `0x00c` | VendorID | 读 | 厂商 ID |
| `0x010` | DeviceFeatures | 读 | 设备支持的特性位（配合 `0x014` 的选择器分段读取） |
| `0x020` | DriverFeatures | 写 | 驱动接受的特性位（配合 `0x024` 的选择器） |
| `0x030` | QueueSel | 写 | 选择接下来要配置的队列编号 |
| `0x034` | QueueNumMax | 读 | 该队列最大长度 |
| `0x038` | QueueNum | 写 | 驱动设置的队列长度 |
| `0x044` | QueueReady | 读写 | 队列是否就绪 |
| `0x050` | **QueueNotify** | 写 | **“叫号铃”**：写入队列编号表示该队列有新请求 |
| `0x060` | InterruptStatus | 读 | 中断原因：位 0 = 队列有更新，位 1 = 配置有变化 |
| `0x064` | InterruptACK | 写 | 确认已处理中断 |
| `0x070` | **Status** | 读写 | **设备状态**，初始化握手的核心 |
| `0x080`/`0x084` | QueueDescLow/High | 写 | 描述符表在 Guest 内存中的地址 |
| `0x090`/`0x094` | QueueDriverLow/High | 写 | 可用环的地址 |
| `0x0a0`/`0x0a4` | QueueDeviceLow/High | 写 | 已用环的地址 |
| `0x0fc` | ConfigGeneration | 读 | 配置空间的版本号，用于检测读取过程中配置是否变化 |
| `0x100` 起 | Config | 读写 | 设备专属配置（如网卡 MAC 地址、磁盘容量） |

Guest 读写这些寄存器，就是第 03 篇讲的 MMIO 退出：vCPU 陷入 KVM，KVM 退出到 Firecracker 的 vCPU 线程，Firecracker 的 MMIO 总线根据地址找到对应设备的传输层对象，执行读写。

### 2.2 设备发现

Guest 内核怎么知道 `0x4000_3000` 有一个 virtio 设备？在 ARM64 上，答案是**设备树**（第 08 篇）：

```dts
virtio_mmio@40003000 {
    compatible = "virtio,mmio";
    reg = <0x00 0x40003000 0x00 0x1000>;
    interrupts = <0x00 0x?? 0x01>;
    dma-coherent;
};
```

内核的 `virtio_mmio` 驱动看到 `compatible = "virtio,mmio"` 的节点，就去读这个地址的 MagicValue 和 DeviceID，再交给对应类型的驱动（如 `virtio_net`）。

（在 x86 上不用设备树，Firecracker 通过 ACPI 表或内核命令行参数 `virtio_mmio.device=…` 告诉内核设备的位置。）

### 2.3 初始化握手

Guest 驱动和设备之间通过写 **Status 寄存器**完成一套握手。每个状态位的含义：

| 位值 | 名称 | 含义 |
|------|------|------|
| 1 | ACKNOWLEDGE | 驱动：“我发现你了” |
| 2 | DRIVER | 驱动：“我知道怎么驱动你” |
| 8 | FEATURES_OK | 驱动：“特性协商完成” |
| 4 | DRIVER_OK | 驱动：“一切就绪，开始工作吧” |
| 64 | DEVICE_NEEDS_RESET | 设备：“我出错了，需要重置” |
| 128 | FAILED | 驱动：“我放弃了” |

完整流程：

```
驱动                                         设备（Firecracker）
 │ 写 Status = 0                              → 重置设备
 │ 写 Status |= ACKNOWLEDGE                   →
 │ 写 Status |= DRIVER                        →
 │ 读 DeviceFeatures（分两段，每段 32 位）       ← 我支持：EVENT_IDX、MRG_RXBUF、MAC……
 │ 写 DriverFeatures                          → 我接受其中的：EVENT_IDX、MAC……
 │ 写 Status |= FEATURES_OK                   → 设备检查：接受的特性是我支持的子集吗？
 │ 读 Status，确认 FEATURES_OK 仍然置位          ← 是（否则设备会清除该位）
 │ 对每个队列：
 │   写 QueueSel、读 QueueNumMax、写 QueueNum
 │   在 Guest 内存中分配描述符表、可用环、已用环
 │   写三个地址寄存器、写 QueueReady = 1
 │ 读写设备专属配置（如读 MAC 地址）
 │ 写 Status |= DRIVER_OK                     → ★ 设备“激活”
```

**特性协商**是 virtio 能长期演进的关键：新版本的设备可以增加特性，旧驱动不认识就不接受，双方仍然能按旧方式工作。

当 Firecracker 看到 `DRIVER_OK`，就会**激活**设备：把队列地址记录下来、校验它们确实落在 Guest 内存范围内，然后把该设备的事件源（队列通知的 eventfd、TAP 设备的 fd 等）注册到 VMM 线程的事件循环里。从这一刻起，设备开始处理 I/O。

> 💡 Firecracker 对握手顺序的检查相当严格：不按顺序写状态、在错误的阶段写队列配置、清除已经置位的状态位（除了重置）等操作都会被拒绝。这也是防御恶意 Guest 的一部分。

---

## 三、虚拟队列：virtqueue

### 3.1 三个组成部分

Firecracker 使用的是 virtio 的**分离式虚拟队列**（split virtqueue）。一个队列由三块位于 Guest 内存中的数据结构组成，由驱动分配，地址通过前面的寄存器告诉设备：

**① 描述符表（Descriptor Table）**——“点菜单”

一个数组，每个元素描述一块 Guest 内存缓冲区：

```c
struct virtq_desc {
    le64 addr;    // 缓冲区在 Guest 物理内存中的地址
    le32 len;     // 长度
    le16 flags;   // NEXT：还有下一个；WRITE：设备往这里写（否则设备从这里读）
    le16 next;    // 下一个描述符的编号
};
```

多个描述符可以通过 `NEXT` 链起来，组成一个完整请求。比如一次磁盘读请求：

```
描述符 0：请求头（读、扇区号）   设备只读
   ↓ next
描述符 1：数据缓冲区 4 KiB      设备可写（WRITE）
   ↓ next
描述符 2：状态字节 1 字节        设备可写（WRITE）
```

**② 可用环（Available Ring）**——“待做队列”，驱动写、设备读

```c
struct virtq_avail {
    le16 flags;
    le16 idx;          // 驱动下一个要写的位置（只增不减，取模使用）
    le16 ring[N];      // 每项是一个描述符链的“头编号”
};
```

**③ 已用环（Used Ring）**——“出菜队列”，设备写、驱动读

```c
struct virtq_used {
    le16 flags;
    le16 idx;                              // 设备下一个要写的位置
    struct { le32 id; le32 len; } ring[N]; // 处理完的链的头编号，以及写入了多少字节
};
```

### 3.2 一次请求的完整流程

以 Guest 读磁盘为例：

```
Guest 驱动                                      Firecracker（VMM 线程）
① 准备 3 个描述符（请求头、数据缓冲、状态）
② 把头编号写入 avail.ring[avail.idx % N]
③ avail.idx += 1（内存屏障保证顺序）
④ 写 QueueNotify = 0 ───────────────────────▶ （经 ioeventfd 唤醒，见第四节）
                                              ⑤ 比较 avail.idx 与自己记录的位置，
                                                 发现有 1 个新请求
                                              ⑥ 顺着描述符链读出请求头：读第 X 扇区
                                              ⑦ 从宿主机文件读 4 KiB，
                                                 直接写入描述符 1 指向的 Guest 内存
                                              ⑧ 往描述符 2 写入状态 OK
                                              ⑨ used.ring[used.idx % N] = {id: 头编号, len: 4097}
                                              ⑩ used.idx += 1
                                  ◀────────── ⑪ 发中断（经 irqfd，见第四节）
⑫ 中断处理：比较 used.idx，取出完成的请求
⑬ 回收描述符，唤醒等待这次读的进程
```

第 ⑦ 步体现了第 09 篇讲的共享内存：Firecracker 直接往 Guest 内存写数据，**没有任何额外拷贝**——就是一次 `pread` 系统调用，目标地址是 Guest 内存在 Firecracker 进程里的映射。

### 3.3 批量与通知抑制

真实负载下，驱动往往一次放入很多请求，只写一次 QueueNotify；设备也往往处理完一批请求，只发一次中断。

virtio 还提供了 **`VIRTIO_RING_F_EVENT_IDX`** 特性，让双方更精确地告诉对方“我希望在你处理到第几个时再通知我”。比如设备正在忙着处理队列时，驱动后续放入的请求就不必再按铃了。Firecracker 的网卡、块设备、vsock 都支持这个特性（vsock 从 v1.16 起），能显著减少 VM Exit 和中断次数。

---

## 四、ioeventfd 与 irqfd：把通知开销压到最低

### 4.1 没有它们会怎样

如果没有任何优化，“写 QueueNotify”的路径是：

```
Guest 写寄存器 → 陷入 KVM → 退出到用户态 vCPU 线程 → 找到设备 → 通知 VMM 线程 → 返回 KVM → 回到 Guest
```

vCPU 线程要从内核出来再回去，Guest 在这期间被挂起。

### 4.2 ioeventfd：在内核里“短路”通知

激活设备时，Firecracker 为每个队列创建一个 eventfd，并调用 KVM 的 `KVM_IOEVENTFD`：

> “当 Guest 往地址 `设备基址 + 0x050` 写入值 i 时，请直接往第 i 个 eventfd 写 1，不要退出到用户态。”

于是路径变成：

```
Guest 写 QueueNotify → 陷入 KVM → KVM 匹配到 ioeventfd，写 eventfd → 立刻回到 Guest
                                         │
                                         └──▶ VMM 线程的 epoll 被唤醒
```

vCPU 线程完全没有离开内核，Guest 几乎立刻继续执行。处理 I/O 的工作异步地交给了 VMM 线程。

### 4.3 irqfd：在内核里“直通”中断

反方向也是一样。Firecracker 为每个设备的中断创建一个 eventfd，调用 `KVM_IRQFD`：

> “当这个 eventfd 被写入时，请向 Guest 注入第 N 号中断。”

VMM 线程处理完请求，只需 `write(irq_eventfd, 1)`，KVM 就会通过 vGIC 把中断送进 Guest。不需要 vCPU 线程参与，不需要任何额外的用户态往返。

### 4.4 ARM64 上的中断编号

在 ARM GIC 中，设备中断属于 **SPI（共享外设中断）**，编号从 32 开始。Firecracker 在 ARM64 上为传统（MMIO）设备分配 SPI 32～127 这个范围内的中断号，每个设备一个。

这也带来一个实际限制：MMIO 模式下能挂载的设备数量受中断号数量限制。官方在 v1.15 的说明中给出的上限是 ARM64 上 92 个设备（x86 上 17 个），因为 RTC、串口、VMClock 等也要占用中断号。对绝大多数场景来说绰绰有余。

### 4.5 动手：观察中断

在 Guest 里：

```bash
grep -i virtio /proc/interrupts
```

你会看到类似：

```
           CPU0       CPU1
 14:        123          0     GICv3  38 Edge      virtio0
 15:       4567          0     GICv3  39 Edge      virtio1
```

`GICv3 38` 表示 GIC 上的 38 号中断（SPI）。用 `ping` 制造网络流量，或用 `dd if=/dev/vda of=/dev/null bs=1M count=100 iflag=direct` 制造磁盘读取，再看对应的计数增加了多少，和请求次数比较——你会发现中断次数远少于请求次数，这就是批量处理的效果。

在宿主机上，看 Firecracker 的指标：

```bash
# 需要先配置了 /metrics（见第 06 篇）
sudo curl -X PUT --unix-socket /tmp/firecracker.socket \
    -d '{"action_type":"FlushMetrics"}' http://localhost/actions
tail -n 1 metrics.json | jq '.vcpu'
```

`exit_mmio_read` 和 `exit_mmio_write` 记录的是**退出到用户态**的 MMIO 访问次数。由于 QueueNotify 走 ioeventfd，大量 I/O 并不会让这两个数字暴涨——主要增长来自配置寄存器读写、InterruptStatus/ACK 等。

---

## 五、防御恶意 Guest

virtqueue 的所有内容——描述符地址、长度、链的结构、环的索引——都由 Guest 写入。**Firecracker 必须假设这些数据是恶意构造的。**可能的攻击包括：

| 攻击 | Firecracker 的防御 |
|------|-----------------|
| 描述符地址指向 Guest 内存之外（企图读写 Firecracker 进程的其他内存） | 所有 Guest 内存访问都通过 `vm-memory` 库的带边界检查的接口，越界访问返回错误而不是崩溃或越权 |
| 描述符链形成环（无限循环） | 限制链长度不超过队列大小 |
| `avail.idx` 声称有比队列长度还多的新请求 | 检测到后停止处理该队列（历史上曾修复过相关的拒绝服务问题） |
| 队列地址与 MMIO 区域重叠 | 激活时检查，拒绝激活设备 |
| 极大的长度值导致宿主机分配大量内存 | 对特定设备设置上限，如熵源单次请求最多 64 KiB（v1.16 修复） |
| 在握手的错误阶段修改队列配置 | 状态机严格校验 |

这里也能看出 Rust 的价值：即使检查有遗漏，越界访问在安全 Rust 中通常会变成一个可控的错误或 panic，而不是悄无声息的内存破坏。主线代码还在持续增加额外的纵深防御检查，比如对每次队列访问都重新校验边界。

---

## 六、传统设备：串口与 RTC

除了 virtio，Firecracker 在 ARM64 上还模拟了两个简单的传统设备，都基于 rust-vmm 的 `vm-superio` 库：

| 设备 | 地址 | 作用 |
|------|------|------|
| 16550 UART 串口 | `0x4000_2000` | 控制台输入输出。Guest 每写一个字符就是一次 MMIO 退出，所以大量串口输出会明显拖慢 Guest |
| PL031 RTC | `0x4000_1000` | 实时时钟，Guest 启动时读取当前时间 |

串口输出默认打印到 Firecracker 进程的标准输出；v1.14 起可以通过 `PUT /serial` 指定输出文件，v1.16 起还可以给串口输出配置限速。

**生产环境建议：** 关闭串口（在启动参数中不加 `console=ttyS0`，或使用默认参数中的 `8250.nr_uarts=0`）。原因有二：串口输出可能包含 Guest 的敏感数据；恶意 Guest 可以疯狂往串口写数据，消耗宿主机的磁盘或日志系统。

---

## 七、另一种选择：virtio-pci（v1.13 起）

### 7.1 怎么开启

```bash
sudo ./firecracker --api-sock /tmp/firecracker.socket --enable-pci ...
```

开启后，所有 virtio 设备都通过 PCI 传输方式呈现。Guest 内核需要支持 PCI（`CONFIG_PCI`、`CONFIG_VIRTIO_PCI`），ARM64 上中断依赖 GICv3 的 ITS（中断翻译服务）来实现 MSI-X。

### 7.2 两种方式对比

| 方面 | virtio-mmio | virtio-pci |
|------|------------|-----------|
| 设备发现 | 设备树中逐个列出 | Guest 枚举 PCI 总线（配置空间通过 ECAM 访问） |
| 中断 | 每设备一个线中断（SPI），所有队列共享 | MSI-X，**每个队列可以有独立的中断** |
| 中断处理 | Guest 需要读 InterruptStatus 判断原因，再写 ACK——两次 MMIO 退出 | MSI-X 中断本身就携带“哪个队列”的信息，省掉这两次退出 |
| 多队列扩展性 | 较差 | 好，适合多 vCPU、多队列 |
| 设备数量上限 | 受 SPI 数量限制 | 更高 |
| 热插拔 | 不支持 | 支持（v1.16 起，开发者预览） |
| 启动开销 | 极低 | 略高（需要枚举 PCI） |
| 实现复杂度 | 低 | 较高 |

官方入门文档目前建议开启 PCI，因为它对 virtio 设备有更高的吞吐和更低的延迟。但 MMIO 依然是默认选项，结构简单、启动最快，也是理解 virtio 本质最好的入口——这正是本系列以它为主线讲解的原因。

### 7.3 动手：对比两种方式

分别用默认方式和 `--enable-pci` 启动同一台 microVM，在 Guest 里比较：

```bash
ls /sys/bus/virtio/devices/
ls /sys/bus/pci/devices/ 2>/dev/null      # PCI 模式下才有内容
cat /proc/interrupts | grep -iE 'virtio|ITS|MSI'
cat /proc/cmdline                         # 默认方式下能看到 pci=off
```

如果有兴趣，还可以用 `iperf3` 在宿主机和 Guest 之间测量网络吞吐，比较两种方式的差别（第 16 篇有更系统的性能测试方法）。

---

## 小结

```
            Guest                                 Firecracker
┌───────────────────────────┐            ┌─────────────────────────────┐
│ virtio 驱动                │  MMIO 寄存器 │ 传输层（MMIO/PCI）             │
│  ├ 握手：Status 1→2→8→4     │◀──────────▶│  ├ 状态机校验                  │
│  ├ 特性协商                 │  vCPU 线程   │  └ DRIVER_OK → 激活设备        │
│  └ 分配队列                 │  同步处理     │                              │
│                           │            │ 设备层（net/block/vsock/…）     │
│ virtqueue（在 Guest 内存）   │  共享内存    │  ├ 读描述符（带边界检查）         │
│  描述符表 / 可用环 / 已用环   │◀══════════▶│  ├ 与后端交换数据（TAP/文件/…）   │
│                           │            │  └ 写已用环                    │
│ 写 QueueNotify ────────────┼─ioeventfd─▶│ VMM 线程 epoll 唤醒            │
│ 中断处理 ◀─────────────────┼──irqfd─────┤ write(irq_evt)               │
└───────────────────────────┘   (KVM)    └─────────────────────────────┘
```

| 概念 | 一句话解释 |
|------|-----------|
| virtio-mmio | 用一个 4 KiB 寄存器窗口呈现 virtio 设备，通过设备树发现 |
| Status 握手 | ACKNOWLEDGE → DRIVER → FEATURES_OK → DRIVER_OK |
| 描述符表 | 描述 Guest 内存中的缓冲区，可链接成请求 |
| 可用环 / 已用环 | 驱动→设备的请求队列 / 设备→驱动的完成队列 |
| ioeventfd | Guest 写通知寄存器时，KVM 直接唤醒 VMM 线程 |
| irqfd | VMM 线程写 eventfd，KVM 直接向 Guest 注入中断 |
| 防御 | 所有 Guest 提供的地址、长度、索引都视为不可信并严格校验 |

---

## 思考题

1. 为什么描述符表、可用环、已用环要由 Guest 驱动分配在 Guest 内存中，而不是由 Firecracker 分配？
2. 如果 Guest 驱动没有写 `DRIVER_OK` 就开始往队列里放请求并按铃，Firecracker 会怎样？
3. 在 MMIO 模式下，Guest 收到一个 virtio 中断后，为什么要读 InterruptStatus？这一步会触发 MMIO 退出吗？
4. 已用环里的 `len` 字段有什么用？对于网卡收包和磁盘读，它分别表示什么？
5. 假设 Firecracker 处理磁盘请求时，没有检查描述符的 `addr + len` 是否越界。一个恶意 Guest 可以做什么？

---

## 下一篇预告

**[11. 网络：让 microVM 连上世界](11-networking.md)**

virtio-net 的后端是宿主机上的 TAP 设备。下一篇从 TAP 讲起，搞清楚数据包从 Guest 到互联网的完整路径、多台 microVM 的网络规划、MMDS 元数据服务的原理，以及不走网络的 vsock 通信。
