# 07. 进程与线程模型

> **《彻底搞懂 Firecracker》系列 · 第七篇**
>
> **读完本篇，你能理解：**
> - 一个 Firecracker 进程里有哪些线程，各自负责什么
> - 为什么设备模拟集中在一个“事件循环”线程里
> - epoll 与 eventfd：事件驱动编程的两块基石
> - vCPU 线程如何运行 Guest、如何处理 MMIO、如何被暂停
> - 一次网络发包在三类线程之间是怎样流转的
> - Rust 和 rust-vmm 在其中扮演的角色
>
> **前置知识：** 第 01 篇（进程、线程、系统调用）、第 03 篇（`KVM_RUN` 循环）、第 06 篇（API 线程与 VMM 线程的通信）。
>
> **版本：** Firecracker v1.17.0。

---

## 引子：一家只有一个前台、一个后厨、几个服务员的餐厅

把一台 microVM 想象成一家小餐厅：

- **前台（API 线程）**：接电话、记订单，但从不进后厨；
- **后厨总管（VMM 线程）**：一个人负责所有设备的“出菜”——网络、磁盘、vsock……他盯着一块“叫号屏”，哪个设备有事就处理哪个；
- **服务员（vCPU 线程）**：每个服务员代表 Guest 的一个 CPU 核，绝大多数时间都在“替 Guest 干活”，偶尔遇到 Guest 要碰设备，就跑去后厨门口喊一声。

这一篇就是要把这家餐厅的运营方式讲清楚。

---

## 一、一个进程，一台 microVM

第 04 篇说过，Firecracker 的一个进程只管一台 microVM。在宿主机上看，一台 microVM 就是一个普通 Linux 进程：

- Guest 内存是这个进程里 `mmap` 出来的一块地址空间；
- Guest 的每个 vCPU 是这个进程里的一个线程；
- 进程退出，microVM 就消失。

这带来一个很大的好处：**宿主机上所有现成的进程管理工具都能直接用于管理 microVM**。`ps` 能看到它、`kill` 能结束它、cgroups 能限制它的 CPU 和内存、`top` 能看到它占多少资源、`perf` 能分析它的性能。

---

## 二、三类线程

在第 05 篇的实验中，用 `ps -eLf | grep firecracker` 或 `top -H` 能看到这些线程：

| 线程名 | 数量 | 职责 |
|-------|------|------|
| `firecracker` | 1 | **VMM 线程**（主线程）：运行事件循环，驱动所有设备模拟，处理来自 API 的指令 |
| `fc_api` | 1 | **API 线程**：运行 HTTP 服务器，解析请求，转交给 VMM 线程 |
| `fc_vcpu 0`、`fc_vcpu 1` …… | 每个 vCPU 一个 | **vCPU 线程**：循环调用 `KVM_RUN` 运行 Guest，处理同步的 MMIO 访问 |

```
            Firecracker 进程
┌──────────────────────────────────────────────────┐
│                                                  │
│   fc_api 线程          firecracker 线程（VMM）      │
│   ┌──────────┐ 通道+   ┌──────────────────────┐   │
│   │HTTP 服务器│ eventfd │ 事件循环（epoll）      │   │
│   │ 解析请求  │ ──────▶ │  ├ API 指令           │   │
│   └──────────┘ ◀────── │  ├ virtio-net 设备    │   │
│        ▲       结果     │  ├ virtio-block 设备  │   │
│        │                │  ├ vsock / balloon …  │   │
│    Unix socket          │  ├ 串口输入、定时器     │   │
│                         │  └ 指标定时刷新        │   │
│                         └──────────▲───────────┘   │
│                                    │ eventfd       │
│   fc_vcpu 0      fc_vcpu 1         │（队列通知）    │
│   ┌────────┐    ┌────────┐         │               │
│   │KVM_RUN │    │KVM_RUN │ ────────┘               │
│   │ 循环    │    │ 循环    │                         │
│   └────────┘    └────────┘                         │
│        Guest 内存（mmap，所有线程共享）               │
└──────────────────────────────────────────────────┘
```

> 💡 主线（尚未发布的 v1.18 开发版）里新增了可选的“块设备多队列”功能，开启后每个队列会有一个独立的 `blk_worker` 线程处理磁盘 I/O。本系列以 v1.17 为准，默认只有上面三类线程。

---

## 三、事件驱动：epoll 与 eventfd

在讲 VMM 线程之前，需要先了解两个 Linux 机制。

### 3.1 问题：一个人怎么同时盯着很多件事

VMM 线程要同时处理：网卡收到的数据包（TAP 设备可读了）、Guest 发出的网络请求（virtio 队列有新内容）、磁盘请求、vsock 连接、API 指令、定时器……如果为每件事开一个线程，线程数会很多，彼此之间还要加锁，复杂且容易出错。

更好的办法是**事件驱动**：一个线程同时“监听”很多个事件源，谁有事就处理谁，没事就睡觉。

### 3.2 epoll：“叫号屏”

**epoll** 是 Linux 提供的事件监听机制。用法分三步：

```c
int ep = epoll_create1(0);                    // 1. 创建一块“叫号屏”
epoll_ctl(ep, EPOLL_CTL_ADD, tap_fd, &ev1);   // 2. 把要监听的文件描述符登记上去
epoll_ctl(ep, EPOLL_CTL_ADD, queue_evt, &ev2);
for (;;) {
    int n = epoll_wait(ep, events, 64, -1);   // 3. 睡觉，直到有事件发生
    for (int i = 0; i < n; i++)
        dispatch(events[i]);                  //    逐个处理
}
```

在 Linux 里，“一切皆文件”：TAP 网卡、socket、定时器、eventfd 都是文件描述符，都可以登记到 epoll 上统一监听。

### 3.3 eventfd：最简单的“门铃”

**eventfd** 是一个特殊的文件描述符，内部只有一个 64 位计数器：

- 往里**写**一个数，计数器增加，监听它的 epoll 就会被唤醒——相当于按门铃；
- 从里**读**一次，计数器清零——相当于应门。

eventfd 在 Firecracker 中无处不在：

| 用途 | 谁按门铃 | 谁应门 |
|------|---------|-------|
| API 指令到达 | API 线程 | VMM 线程 |
| Guest 通知 virtio 队列有新请求（ioeventfd） | KVM（在内核里） | VMM 线程 |
| 设备给 Guest 发中断（irqfd） | VMM 线程 | KVM（在内核里） |
| 让 vCPU 暂停/退出 | VMM 线程 | vCPU 线程 |

ioeventfd 和 irqfd 是 KVM 提供的“快捷通道”，第 10 篇会详细讲，这里先记住：**它们让设备通知不必经过 vCPU 线程绕一圈。**

### 3.4 Firecracker 中的事件循环

Firecracker 使用 rust-vmm 社区的 `event-manager` 库实现事件循环。每个需要监听事件的组件（每个设备、API 处理器、指标定时器等）都实现一个“订阅者”（Subscriber）接口：

```rust
// 简化示意
trait MutEventSubscriber {
    // 初始化时：告诉事件循环“我要监听哪些 fd”
    fn init(&mut self, ops: &mut EventOps);
    // 事件发生时：被事件循环回调
    fn process(&mut self, event: Events, ops: &mut EventOps);
}
```

主线程的最后一件事，就是进入一个无限循环，不停地调用 `event_manager.run()`。所有设备模拟都在这里被驱动。

---

## 四、VMM 线程：一个人的后厨

### 4.1 为什么只用一个线程

把所有设备模拟放在一个线程里，看起来会成为瓶颈，但这是一个经过权衡的选择：

- **简单**：所有设备状态只被一个线程修改，不需要锁，不会有数据竞争；
- **安全**：代码路径更容易审查，seccomp 规则也只需要为这一个线程设计；
- **可预测**：每个 microVM 的 I/O 处理最多消耗一个宿主机 CPU 核，便于做容量规划；
- **够用**：Serverless 场景下单个 microVM 的 I/O 量通常不大，真正需要高吞吐的场景可以靠多台 microVM 横向扩展。

官方规格中提到，在给 VMM 线程独占一个宿主机 CPU 核的条件下，网络吞吐可达 25 Gbps 量级（第 04 篇的 SPECIFICATION）。

代价也很明显：**一个慢设备会拖累其他设备**。历史上就修过“磁盘后端太慢导致所有其他设备饿死”的问题（v1.13 修复）。

### 4.2 暂停时发生什么

当你调用 `PATCH /vm {"state": "Paused"}`，VMM 线程会：

1. 通知所有 vCPU 线程暂停（见下节）；
2. 自己停止轮询设备事件，只继续处理 API 指令。

所以暂停状态下，vCPU 和所有设备都是静止的——这正是快照所需要的“一致状态”（第 15 篇）。

---

## 五、vCPU 线程：替 Guest 干活的服务员

### 5.1 核心循环

每个 vCPU 线程的主体就是第 03 篇那个 `KVM_RUN` 循环。在 Firecracker 的 Rust 代码中，退出处理的大致逻辑是：

```rust
// 简化自 src/vmm/src/vstate/vcpu.rs
match vcpu_fd.run() {
    Ok(VcpuExit::MmioRead(addr, data))  => mmio_bus.read(addr, data),   // 同步处理
    Ok(VcpuExit::MmioWrite(addr, data)) => mmio_bus.write(addr, data),  // 同步处理
    Ok(VcpuExit::SystemEvent(type_, _)) => /* PSCI 关机/重启 → 结束 microVM */,
    Ok(VcpuExit::InternalError) | Ok(VcpuExit::FailEntry(..)) => /* 报错退出 */,
    Err(e) if e.errno() == libc::EINTR => /* 被信号打断，检查是否要暂停 */,
    ...
}
```

### 5.2 MMIO 是“同步”处理的

注意 `MmioRead` 和 `MmioWrite` 是**在 vCPU 线程里直接处理**的：vCPU 线程根据地址找到设备（MMIO 总线就是一张“地址区间 → 设备”的表），调用设备的读写函数，拿到结果后立刻继续 `KVM_RUN`。

这里的“设备读写”通常是很轻的操作，比如：

- Guest 读 virtio 设备的配置寄存器（“你支持哪些特性？”）；
- Guest 往串口写一个字符；
- Guest 读 RTC 时间。

而**重活**——真正的网络收发、磁盘读写——不在 vCPU 线程里做，而是交给 VMM 线程。两者之间靠 ioeventfd 衔接：Guest 写 virtio 的“队列通知”寄存器时，KVM 在内核里直接把它变成一次 eventfd 写入，**连 vCPU 线程都不惊动**，VMM 线程的 epoll 就醒了。

### 5.3 怎么让一个正在跑 Guest 的线程停下来

vCPU 线程大部分时间都在 `ioctl(KVM_RUN)` 里，也就是在 Guest 中执行代码。VMM 线程要让它暂停，怎么通知它？

答案是**信号**。Firecracker 给每个 vCPU 线程发送一个实时信号（`SIGRTMIN`），这会让 `KVM_RUN` 立即返回 `EINTR` 错误。vCPU 线程回到 Firecracker 的代码里，检查自己的消息通道，发现有 `Pause` 指令，就进入等待状态。

vCPU 线程能接收的指令包括：

| 指令 | 作用 |
|------|------|
| `Pause` | 暂停 |
| `Resume` | 恢复运行 |
| `SaveState` | 保存寄存器等状态（快照时） |
| `DumpCpuConfig` | 导出 CPU 配置（CPU 模板工具使用） |
| `Finish` | 结束线程 |

这种“信号 + 消息通道”的组合，是 Firecracker 控制 vCPU 的标准做法。

### 5.4 Guest 的 vCPU 就是宿主机的线程

这一点有几个重要推论：

- **宿主机调度器决定 vCPU 什么时候跑**：Guest 以为自己有 2 个 CPU，但宿主机可能把这两个线程调度到同一个物理核上轮流跑，这就是 CPU 超卖；
- **可以用 cgroups 限制 vCPU 的算力**：给 Firecracker 进程设置 CPU 配额，Guest 能用的算力就被限制了；
- **可以绑核**：用 `taskset` 或 cgroups 的 `cpuset` 把 vCPU 线程固定到某些物理核上，减少抖动；
- **Guest 空闲时几乎不占宿主机 CPU**：Guest 执行 `WFI`（等待中断）时，KVM 会让 vCPU 线程在内核里睡眠，直到有中断要投递。

---

## 六、API 线程：只说不做的前台

API 线程运行一个精简的 HTTP 服务器（Firecracker 团队自己维护的 `micro_http` 库），它的工作非常单纯：

1. 从 Unix socket 读取 HTTP 请求；
2. 解析路径和 JSON，转换成内部的指令结构；
3. 通过通道把指令发给 VMM 线程，并写 eventfd 唤醒它；
4. 等待结果，转换成 HTTP 响应。

它**不碰 Guest 内存，不处理任何 Guest 数据**。即使攻击者能控制 API 请求的内容（比如上层编排系统被攻破），API 线程能做的事情也被 seccomp 严格限制。

---

## 七、完整案例：Guest 发送一个网络包

把三类线程串起来，看一次完整的网络发包：

```
 Guest 内核                vCPU 线程        KVM（内核）       VMM 线程            宿主机网络
───────────────────────────────────────────────────────────────────────────────────────
① virtio-net 驱动把数据包
  放进 Guest 内存，在 TX
  队列里登记它
② 写“队列通知”寄存器 ─────────────────▶ 命中 ioeventfd，
  （一次 MMIO 写）                       写 eventfd
                                        Guest 立刻继续运行
                                        （vCPU 线程无感）
                                                         ▶ ③ epoll 醒来，
                                                             TX 队列有新包
                                                           ④ 检查限速器
                                                           ⑤ 从 Guest 内存
                                                             读出数据包
                                                           ⑥ 写入 TAP fd ───▶ 宿主机网络栈
                                                           ⑦ 在 used 队列
                                                             登记“已发送”
                                        ◀───────────────── ⑧ 写 irqfd
                                        注入虚拟中断
⑨ Guest 收到中断，
  回收发送缓冲区
```

这里最值得注意的是：**整个过程中，vCPU 线程完全没有退出到用户态**。第②步的 MMIO 写在 KVM 内部就被 ioeventfd 截获并转换了。这是 virtio + ioeventfd + irqfd 组合的威力，第 10 篇会看到更多细节。

（如果 Guest 的目标地址是 MMDS 的 IP，第⑥步会改为交给 Firecracker 内置的一个小型网络栈处理，见第 11 篇。）

---

## 八、为什么是 Rust

### 8.1 VMM 的安全困境

VMM 是一个“处理不可信输入”的程序：Guest 可以往共享内存里写任意数据，往设备寄存器写任意值，virtio 队列里的描述符可能指向任意地址、长度可能是任意数字。历史上 C 语言编写的 VMM 出过大量“Guest 构造恶意数据 → VMM 越界读写 → 逃逸到宿主机”的漏洞。

### 8.2 Rust 带来了什么

- **内存安全**：在不使用 `unsafe` 的代码中，编译器保证不会出现越界访问、释放后使用、空指针解引用；
- **线程安全**：类型系统阻止在线程之间不安全地共享可变数据，从根上避免数据竞争；
- **没有垃圾回收**：性能和内存占用接近 C，没有 GC 停顿；
- **显式的 `unsafe`**：与硬件和系统调用打交道的底层代码必须标记为 `unsafe`，审查时可以重点关注这些地方。

Rust 不是万能的——逻辑错误、整数溢出导致的错误计算、`unsafe` 块里的错误依然可能发生（第 04 篇的版本历史里就能看到一些这样的修复）。所以 Firecracker 还配合了模糊测试（fuzzing）、形式化验证（用 Kani 工具证明部分关键代码的性质）、seccomp 和 jailer 等多层防御。

### 8.3 rust-vmm 积木

Firecracker 依赖的几个关键 rust-vmm 组件：

| 库 | 作用 |
|----|------|
| `kvm-bindings`、`kvm-ioctls` | KVM 数据结构的 Rust 定义和 ioctl 的安全封装 |
| `vm-memory` | Guest 内存的抽象：地址类型、安全的读写接口 |
| `linux-loader` | 加载 Linux 内核（ARM64 的 `Image`、x86 的 ELF/bzImage）、构造内核命令行 |
| `vm-fdt` | 生成设备树（第 08 篇） |
| `vm-superio` | 串口、RTC 等简单传统设备的模拟 |
| `event-manager` | 基于 epoll 的事件循环框架 |
| `vmm-sys-util` | eventfd、信号、定时器等 Linux 系统工具的封装 |

第 18 篇源码导读时会看到这些库在代码中的位置。

---

## 九、动手：观察线程的行为

启动一台 microVM（第 05 篇），然后在宿主机上做这些实验。

**实验 1：线程列表**

```bash
FC_PID=$(pgrep -f 'firecracker --api-sock' | head -1)
ls /proc/$FC_PID/task/
for t in /proc/$FC_PID/task/*; do echo "$(basename $t) $(cat $t/comm)"; done
```

**实验 2：谁在消耗 CPU**

在 Guest 里制造 CPU 负载：

```bash
# Guest 内
yes > /dev/null &
```

在宿主机上：

```bash
top -H -p $FC_PID
```

你会看到某个 `fc_vcpu` 线程接近 100%，其他线程几乎为 0。

再在 Guest 里制造网络负载（比如 `curl` 下载一个大文件，或者用第 05 篇的网络 `ping -f`），会看到 `firecracker`（VMM 线程）的 CPU 占用上升。

**实验 3：用 strace 看 vCPU 线程的系统调用**

```bash
VCPU_TID=$(for t in /proc/$FC_PID/task/*; do [ "$(cat $t/comm)" = "fc_vcpu 0" ] && basename $t; done)
sudo strace -p $VCPU_TID -c   # 运行几秒后按 Ctrl+C
```

你会看到几乎全是 `ioctl`（就是 `KVM_RUN`），偶尔有 `write`（串口输出）。在 Guest 里执行 `dmesg` 刷屏，`write` 的次数会明显增加。

**实验 4：暂停时 vCPU 线程在干什么**

```bash
sudo curl -X PATCH --unix-socket /tmp/firecracker.socket \
    -d '{"state":"Paused"}' http://localhost/vm
cat /proc/$VCPU_TID/wchan; echo     # 线程在内核里等什么
cat /proc/$VCPU_TID/status | grep State
sudo curl -X PATCH --unix-socket /tmp/firecracker.socket \
    -d '{"state":"Resumed"}' http://localhost/vm
```

暂停时 vCPU 线程处于睡眠状态（`S`），等待 VMM 线程的消息。

---

## 小结

| 线程 | 职责 | 关键机制 |
|------|------|---------|
| `fc_api` | HTTP 解析，转发指令 | `micro_http`、通道 + eventfd |
| `firecracker`（VMM） | 所有设备的异步 I/O，处理 API 指令 | epoll 事件循环、`event-manager` |
| `fc_vcpu N` | 运行 Guest，同步处理 MMIO | `KVM_RUN` 循环、信号唤醒 |

| 设计选择 | 好处 | 代价 |
|---------|------|------|
| 一进程一 VM | 隔离好，能复用宿主机进程管理工具 | 每个 VM 有少量固定开销 |
| 单 VMM 线程 | 无锁、简单、可预测 | 单 VM 的 I/O 上限受一个核限制 |
| ioeventfd / irqfd | 设备通知不经过 vCPU 线程和用户态 | 需要 KVM 支持 |
| Rust | 消除绝大部分内存安全漏洞 | 学习曲线；`unsafe` 部分仍需审查 |

---

## 思考题

1. 如果一个设备的处理函数里不小心写了一个死循环，会发生什么？Guest 还能继续运行吗？
2. 为什么串口输出（Guest 写一个字符）是在 vCPU 线程同步处理的，而网络发包是在 VMM 线程异步处理的？
3. 给一台 4 vCPU 的 microVM 只分配宿主机 1 个物理核（用 `taskset`），Guest 会看到几个 CPU？性能会怎样？
4. 为什么让 vCPU 暂停要用信号，而不是直接往它的消息通道里发一条消息？
5. 一台 microVM 的“总 CPU 开销”应该怎么计算？哪些线程算 Guest 的，哪些算“虚拟化开销”？

---

## 下一篇预告

**[08. 启动全过程：从 InstanceStart 到看到登录提示](08-boot-process.md)**

按下 `InstanceStart` 后的一百多毫秒里，Firecracker 做了什么？我们将跟随启动流程：分配内存、加载 ARM64 内核、生成设备树、设置 vCPU 寄存器、通过 PSCI 唤醒其他核。
