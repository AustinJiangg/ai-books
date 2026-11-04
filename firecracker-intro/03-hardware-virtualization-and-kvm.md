# 03. 硬件虚拟化与 KVM（以 ARM64 为主）

> **《彻底搞懂 Firecracker》系列 · 第三篇**
>
> **读完本篇，你能理解：**
> - ARM64 的 EL2 是怎样把 Guest“关”起来的：陷阱配置、Stage-2 翻译
> - VHE 是什么，为什么 Linux 宿主内核能直接跑在 EL2
> - Guest 访问设备时，硬件和 KVM 一步步发生了什么（MMIO 退出的完整链路）
> - 虚拟中断控制器（vGIC）和虚拟定时器的作用
> - KVM 的用户态接口：`/dev/kvm`、VM fd、vCPU fd、`KVM_RUN` 循环
> - 亲手用不到 100 行 C 代码，在 ARM64 上创建一台“迷你虚拟机”并让它打印 `Hi`
>
> **前置知识：** 第 01 篇（异常级别、页表、MMIO、系统调用）、第 02 篇（陷入-模拟、KVM 与 VMM 分工）。
>
> **实验环境：** ARM64 Linux，`/dev/kvm` 可读写，装有 `gcc`、`binutils`。

---

## 引子：导演组的“遥控器”

上一篇我们说，Hypervisor 像《楚门的世界》的导演组。这一篇要揭开导演组手里的遥控器到底长什么样：

- 在**硬件层面**，遥控器是 EL2 的一组系统寄存器，它们决定 Guest 做哪些事会被“叫停”；
- 在**软件层面**，遥控器是 Linux 提供的 `/dev/kvm` 设备文件，用户态程序（比如 Firecracker）通过它创建和驾驶虚拟机。

本篇读完，你会亲手用这个遥控器开一台最小的虚拟机。Firecracker 做的事情，本质上就是这个最小虚拟机的“完全体”。

---

## 一、EL2：为 Hypervisor 准备的特权层

### 1.1 回顾异常级别

```
EL0  应用程序
EL1  操作系统内核
EL2  Hypervisor          ← 本篇主角
EL3  安全监控固件
```

当 CPU 运行 Guest 时，Guest 的应用在 EL0，Guest 的内核在 EL1——和在真机上一模一样，所以绝大多数指令都能全速执行。区别在于：EL2 上的 Hypervisor 提前设置好了一系列“开关”，决定 Guest 在 EL1/EL0 做某些事情时，CPU 要不要自动跳到 EL2。

### 1.2 关键寄存器：HCR_EL2

**HCR_EL2（Hypervisor Configuration Register）** 是最重要的一个开关面板。它里面有很多位，每一位控制一类行为。几个典型的位：

| 位 | 含义（通俗版） |
|----|--------------|
| `VM` | 打开 Stage-2 地址翻译：Guest 看到的“物理地址”不再是真物理地址 |
| `IMO` / `FMO` | 物理中断（IRQ/FIQ）来了，先交给 EL2 处理，而不是直接交给 Guest |
| `TWI` / `TWE` | Guest 执行 `WFI`/`WFE`（“我没事干，睡一会儿”）时陷入 EL2，Hypervisor 可以趁机把物理 CPU 让给别人 |
| `TVM` 等 | Guest 修改某些系统寄存器时陷入，便于 Hypervisor 观察 |
| `TSC` | Guest 执行 `SMC`（调用 EL3 固件）时陷入 EL2 |

你不需要记住这些名字。重要的是理解这个思路：**Hypervisor 通过配置寄存器位，精确选择“哪些行为需要我来管”**。不需要管的，Guest 就直接在硬件上跑。

### 1.3 陷入时发生了什么

当 Guest 触发了一个被配置为“需要陷入”的行为，CPU 会：

1. 保存 Guest 当前的 PC 和状态到 EL2 的寄存器（`ELR_EL2`、`SPSR_EL2`）；
2. 把**陷入原因**写进 `ESR_EL2`（Exception Syndrome Register）——比如“数据访问异常，访问地址在 `FAR_EL2`/`HPFAR_EL2` 里，是一次 1 字节的写，数据在寄存器 `w0`”；
3. 跳到 EL2 预先设定的异常向量，执行 Hypervisor 的代码。

Hypervisor 处理完，执行 `ERET` 指令返回 Guest，Guest 从被打断的地方继续。

这一来一回，就是常说的 **VM Exit**（虚拟机退出）和 **VM Entry**（重新进入）。每次 VM Exit 都要保存/恢复大量寄存器，代价通常在微秒级甚至更低，但如果频繁发生，性能就会明显下降。**减少 VM Exit 的次数**，是所有虚拟化优化的核心目标之一。

---

## 二、VHE：让宿主内核直接住进 EL2

### 2.1 一个尴尬的问题

KVM 是 Linux 内核的一部分，而 Linux 内核传统上运行在 EL1。但 Hypervisor 的核心代码必须在 EL2 执行。早期的 ARM64 KVM 只好把自己拆成两半：

- 大部分 KVM 代码和 Linux 内核一起在 EL1；
- 一小段“世界切换”代码放在 EL2（叫 hyp 代码）。

每次 Guest 退出，CPU 先进 EL2，再跳回 EL1 让 KVM 处理，处理完又要经过 EL2 才能回到 Guest。多了一来一回，性能有损失。

### 2.2 VHE 的解决方案

ARMv8.1 引入了 **VHE（Virtualization Host Extensions）**。打开 `HCR_EL2.E2H` 位后，EL2 变得“像 EL1 一样好用”：原本只为 EL1 设计的内核可以几乎不加修改地直接运行在 EL2。

于是现代 ARM64 服务器上的典型布局是：

```
              Guest                          Host
EL0   Guest 应用                Host 应用（Firecracker 进程在这里）
EL1   Guest 内核                       （空）
EL2   ────────── Linux 宿主内核 + KVM（VHE 模式）──────────
```

宿主内核本身就在 EL2，KVM 处理 VM Exit 不需要再多跳一次。你在第 02 篇用 `dmesg | grep -i kvm` 看到的 “VHE mode initialized” 之类的字样，说的就是这个。

> 💡 **延伸：** 近年的 Linux 还有 **nVHE** 与 **pKVM（protected KVM）** 模式，它们刻意把一小段可信代码留在 EL2、把宿主内核降到 EL1，以便让宿主内核也无法偷看 Guest 内存。这属于更高级的安全话题，Firecracker 当前的常规部署不依赖它。

---

## 三、Stage-2：Guest 的“物理内存”是假的

### 3.1 三种地址

在虚拟机里，一次内存访问会涉及三种地址：

| 名字 | 全称 | 谁维护映射 |
|------|------|-----------|
| **VA** | 虚拟地址（Guest 进程看到的） | — |
| **IPA** | 中间物理地址（Guest 内核以为的“物理地址”） | Guest 内核的页表（Stage-1） |
| **PA** | 真实物理地址 | Hypervisor 的页表（Stage-2） |

```
Guest 进程的 VA ──Stage-1（Guest 页表）──▶ IPA ──Stage-2（KVM 页表）──▶ PA
```

两次翻译都由 CPU 的 MMU **硬件自动完成**，结果还会缓存在 TLB 里，所以正常访问内存几乎没有额外开销。Stage-2 页表的基地址放在 `VTTBR_EL2` 寄存器里，只有 EL2 能修改。

Guest 可以随意改写自己的 Stage-1 页表，但它只能决定“VA 映射到哪个 IPA”。IPA 最终落在哪块真实内存，由 KVM 说了算。这就是 Guest 无法触碰其他虚拟机内存的根本原因。

### 3.2 Stage-2 缺页：两种情况

当 Guest 访问某个 IPA，而 Stage-2 页表里还没有对应条目时，CPU 会陷入 EL2（Stage-2 abort）。KVM 会查看这个 IPA 属于哪种区域：

**情况 A：属于 Guest 内存。** 用户态 VMM 之前通过 `KVM_SET_USER_MEMORY_REGION` 告诉过 KVM：“IPA 从 `0x8000_0000` 开始的 128 MB，对应我进程里 `mmap` 出来的这块地址”。KVM 就在宿主内核里找到（或分配）对应的物理页，补上 Stage-2 映射，然后返回 Guest 重试。整个过程 Guest 无感，用户态 VMM 也不参与。

这意味着 Guest 内存是**按需分配**的：Guest 没碰过的内存，宿主机根本没分配物理页。这正是 Firecracker 能“超卖内存”的基础（第 9 篇详述）。

**情况 B：不属于任何内存区域。** 那这一定是在访问设备（MMIO）。KVM 从 `ESR_EL2` 里解析出“读还是写、几个字节、用的哪个寄存器”，如果设备是 KVM 内部模拟的（比如中断控制器），就直接处理；否则就**退出到用户态**，把这个请求交给 VMM。

### 3.3 一次 MMIO 退出的完整旅程

假设 Guest 内核里的串口驱动执行了一条 `strb w0, [x1]`，`x1` 指向串口的 MMIO 地址：

```
① Guest（EL1）执行 strb w0, [x1]
② MMU 做 Stage-2 翻译，发现该 IPA 无映射 → 陷入 EL2
③ KVM 读 ESR_EL2：写操作，1 字节，数据来自 w0
④ KVM 查到这个地址不属于内存、也不是内核模拟的设备
⑤ KVM 把信息填进共享结构 kvm_run：
       exit_reason = KVM_EXIT_MMIO
       mmio.phys_addr = 地址, mmio.len = 1, mmio.data = 'A', is_write = 1
⑥ ioctl(KVM_RUN) 返回到用户态 —— Firecracker 的 vCPU 线程醒来
⑦ Firecracker 根据地址找到串口设备模型，调用它的 write 函数，把 'A' 写到 stdout
⑧ vCPU 线程再次调用 ioctl(KVM_RUN)，KVM 让 PC 跳过那条 strb，回到 Guest
```

步骤 ⑥⑦ 要从内核返回用户态再回来，比纯内核内处理更慢。这就是为什么 virtio 要尽量“攒一批再通知”（第 10 篇）。

---

## 四、中断和时钟也要“虚拟”

### 4.1 vGIC：虚拟中断控制器

真实机器上，GIC 负责把设备中断分发给各个 CPU 核。虚拟机里，Guest 内核也需要一个 GIC 来管理中断，否则它没法正常工作。

ARM 的 GICv2/GICv3 都在硬件里提供了**虚拟化支持**：

- 每个物理 CPU 有一组“列表寄存器”（List Registers），Hypervisor 往里面填一条“请给 Guest 注入 33 号中断”，CPU 进入 Guest 后硬件就会让 Guest 感知到这个中断，不需要 Guest 每次确认中断都陷入；
- GIC 的“分发器”（Distributor）部分由 KVM 在内核里模拟。

Firecracker 在启动时会请 KVM 创建一个内核态 vGIC（通过 `KVM_CREATE_DEVICE`），之后设备想给 Guest 发中断，只需要写一个 eventfd，KVM 就会把它变成对应的虚拟中断（这个机制叫 **irqfd**，第 10 篇详述）。

### 4.2 虚拟定时器

Guest 内核需要时钟来调度进程、计时。ARM64 的通用定时器（Generic Timer）本身就提供了**虚拟计数器**和**虚拟定时器**：

- 虚拟计数器 = 物理计数器 − 偏移量（`CNTVOFF_EL2`），Hypervisor 设置偏移量后，Guest 读到的时间是“从它开机算起”的；
- Guest 设置虚拟定时器到期时，硬件直接产生中断，由 KVM 转交给 Guest。

这让 Guest 读时间不需要陷入，非常高效。快照恢复时如何处理时间，是第 15 篇会讨论的一个难点。

### 4.3 PSCI：电源管理的“标准接口”

Guest 内核怎么启动第二个 CPU 核？怎么关机、重启？在 ARM64 上，这些操作通过 **PSCI（Power State Coordination Interface）** 完成：内核执行 `HVC` 或 `SMC` 指令，带上功能号（如 `CPU_ON`、`SYSTEM_OFF`、`SYSTEM_RESET`）。

KVM 在内核里直接实现了 PSCI：

- `CPU_ON`：KVM 唤醒对应的 vCPU，让它从指定地址开始执行；
- `SYSTEM_OFF` / `SYSTEM_RESET`：KVM 退出到用户态，`exit_reason = KVM_EXIT_SYSTEM_EVENT`，由 VMM 决定怎么做。

Firecracker 收到这两种事件时会结束整个 microVM 进程。这就是为什么在 Guest 里执行 `reboot` 会让 Firecracker 直接退出——它并不实现真正的“重启”（第 5 篇会看到）。

---

## 五、KVM 的用户态接口

### 5.1 三层文件描述符

KVM 的所有功能都通过对文件描述符调用 `ioctl` 来使用，按作用范围分成三层：

```
open("/dev/kvm")                    → kvm_fd   系统级：查询能力、创建 VM
   └─ ioctl(kvm_fd, KVM_CREATE_VM)  → vm_fd    虚拟机级：内存、中断控制器、vCPU
         └─ ioctl(vm_fd, KVM_CREATE_VCPU) → vcpu_fd  vCPU 级：寄存器、运行
```

`ioctl` 本身就是一个系统调用（第 01 篇），意思是“对这个文件执行一个特殊控制命令”。

### 5.2 常用 ioctl 一览

| 层级 | ioctl | 作用 |
|------|-------|------|
| kvm | `KVM_GET_API_VERSION` | 查询 API 版本（固定为 12） |
| kvm | `KVM_CHECK_EXTENSION` | 查询是否支持某个能力 |
| kvm | `KVM_CREATE_VM` | 创建一台虚拟机 |
| kvm | `KVM_GET_VCPU_MMAP_SIZE` | 查询 `kvm_run` 共享结构的大小 |
| vm | `KVM_SET_USER_MEMORY_REGION` | 把用户态内存注册为 Guest 内存（一个“内存槽”） |
| vm | `KVM_CREATE_VCPU` | 创建 vCPU |
| vm | `KVM_ARM_PREFERRED_TARGET` | ARM64 专属：查询推荐的 vCPU 类型 |
| vm | `KVM_CREATE_DEVICE` | 创建内核模拟设备，如 vGIC |
| vm | `KVM_IRQFD` / `KVM_IOEVENTFD` | 用 eventfd 投递中断 / 接收 MMIO 通知 |
| vcpu | `KVM_ARM_VCPU_INIT` | ARM64 专属：初始化 vCPU（可附带特性，如 PSCI 0.2、关机状态启动） |
| vcpu | `KVM_SET_ONE_REG` / `KVM_GET_ONE_REG` | 读写单个寄存器（PC、X0、PSTATE、系统寄存器） |
| vcpu | `KVM_RUN` | 运行 vCPU，直到发生需要用户态处理的退出 |

### 5.3 kvm_run：内核与用户态的“传话本”

每个 vCPU 都有一块共享内存，叫 `struct kvm_run`。用户态通过 `mmap(vcpu_fd)` 映射它。每次 `KVM_RUN` 返回，KVM 就把退出原因和细节写在这里：

```c
struct kvm_run {
    __u32 exit_reason;        // 为什么退出：KVM_EXIT_MMIO、KVM_EXIT_SYSTEM_EVENT ……
    union {
        struct { __u64 phys_addr; __u8 data[8]; __u32 len; __u8 is_write; } mmio;
        struct { __u32 type; ... } system_event;
        ...
    };
};
```

### 5.4 所有 VMM 都长这样

无论是 QEMU、Firecracker 还是 Cloud Hypervisor，每个 vCPU 线程的核心都是这个循环：

```c
for (;;) {
    ioctl(vcpu_fd, KVM_RUN, 0);           // 让 Guest 跑，直到它“碰到墙”
    switch (run->exit_reason) {
    case KVM_EXIT_MMIO:          handle_mmio(run);     break;  // 交给设备模型
    case KVM_EXIT_SYSTEM_EVENT:  handle_power(run);    break;  // 关机/重启
    default:                     report_error(run);    return;
    }
}
```

Firecracker 的 Rust 代码里，对应的就是 vCPU 线程中对 `VcpuExit::MmioRead`、`VcpuExit::MmioWrite`、`VcpuExit::SystemEvent` 等情况的匹配处理（第 7、18 篇会对着源码看）。

---

## 六、动手：写一个最小的 ARM64 虚拟机

我们来做一台只有 64 KB 内存、一个 vCPU、两个“设备地址”的虚拟机：

- 往 `0x1000` 写一个字节 = 打印这个字符（一个最简陋的“串口”）；
- 往 `0x2000` 写任意值 = 关机。

### 6.1 Guest 程序

新建 `guest.S`：

```asm
    .text
    .global _start
_start:
    mov  x1, #0x1000        // “串口”地址：这里没有内存，访问会触发 MMIO 退出
    mov  w0, #'H'
    strb w0, [x1]           // 打印 H
    mov  w0, #'i'
    strb w0, [x1]           // 打印 i
    mov  w0, #'\n'
    strb w0, [x1]           // 换行
    mov  x1, #0x2000        // “关机”地址
    strb w0, [x1]
1:  b    1b                 // 不应该走到这里
```

把它编译成**纯机器码**（去掉 ELF 文件头等包装）：

```bash
as guest.S -o guest.o
objcopy -O binary guest.o guest.bin
ls -l guest.bin             # 只有几十个字节
```

### 6.2 VMM 程序

新建 `tinyvmm.c`：

```c
#include <fcntl.h>
#include <linux/kvm.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>

#define GUEST_BASE 0x10000   /* Guest 内存从 IPA 0x10000 开始 */
#define MEM_SIZE   0x10000   /* 64 KB，兼容 4K 和 64K 页的宿主机 */

static void die(const char *msg) { perror(msg); exit(1); }

int main(void) {
    /* 1. 打开 KVM */
    int kvm = open("/dev/kvm", O_RDWR | O_CLOEXEC);
    if (kvm < 0) die("open /dev/kvm");
    printf("KVM API version: %d\n", ioctl(kvm, KVM_GET_API_VERSION, 0));

    /* 2. 创建虚拟机 */
    int vm = ioctl(kvm, KVM_CREATE_VM, 0);
    if (vm < 0) die("KVM_CREATE_VM");

    /* 3. 准备 Guest 内存：在本进程里 mmap 一块，再把 guest.bin 拷进去 */
    uint8_t *mem = mmap(NULL, MEM_SIZE, PROT_READ | PROT_WRITE,
                        MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (mem == MAP_FAILED) die("mmap guest memory");
    FILE *f = fopen("guest.bin", "rb");
    if (!f) die("open guest.bin");
    size_t n = fread(mem, 1, MEM_SIZE, f);
    fclose(f);
    printf("loaded %zu bytes of guest code\n", n);

    /* 4. 告诉 KVM：IPA [GUEST_BASE, GUEST_BASE+MEM_SIZE) 对应这块内存 */
    struct kvm_userspace_memory_region region = {
        .slot = 0,
        .guest_phys_addr = GUEST_BASE,
        .memory_size = MEM_SIZE,
        .userspace_addr = (uint64_t)mem,
    };
    if (ioctl(vm, KVM_SET_USER_MEMORY_REGION, &region) < 0)
        die("KVM_SET_USER_MEMORY_REGION");

    /* 5. 创建并初始化 vCPU（ARM64 必须先 PREFERRED_TARGET 再 VCPU_INIT） */
    int vcpu = ioctl(vm, KVM_CREATE_VCPU, 0);
    if (vcpu < 0) die("KVM_CREATE_VCPU");
    struct kvm_vcpu_init init;
    if (ioctl(vm, KVM_ARM_PREFERRED_TARGET, &init) < 0)
        die("KVM_ARM_PREFERRED_TARGET");
    if (ioctl(vcpu, KVM_ARM_VCPU_INIT, &init) < 0)
        die("KVM_ARM_VCPU_INIT");

    /* 6. 设置 PC：让 vCPU 从 Guest 代码的第一条指令开始 */
    uint64_t pc = GUEST_BASE;
    struct kvm_one_reg reg = {
        .id = KVM_REG_ARM64 | KVM_REG_SIZE_U64 | KVM_REG_ARM_CORE |
              KVM_REG_ARM_CORE_REG(regs.pc),
        .addr = (uint64_t)&pc,
    };
    if (ioctl(vcpu, KVM_SET_ONE_REG, &reg) < 0) die("set PC");

    /* 7. 映射 kvm_run 共享结构 */
    int run_size = ioctl(kvm, KVM_GET_VCPU_MMAP_SIZE, 0);
    struct kvm_run *run = mmap(NULL, run_size, PROT_READ | PROT_WRITE,
                               MAP_SHARED, vcpu, 0);
    if (run == MAP_FAILED) die("mmap kvm_run");

    /* 8. 经典的 KVM_RUN 循环 */
    for (;;) {
        if (ioctl(vcpu, KVM_RUN, 0) < 0) die("KVM_RUN");
        switch (run->exit_reason) {
        case KVM_EXIT_MMIO:
            if (run->mmio.is_write && run->mmio.phys_addr == 0x1000) {
                putchar(run->mmio.data[0]);          /* “串口”输出 */
                fflush(stdout);
            } else if (run->mmio.is_write && run->mmio.phys_addr == 0x2000) {
                printf("guest requested shutdown\n");
                return 0;
            } else {
                printf("unhandled MMIO at 0x%llx\n",
                       (unsigned long long)run->mmio.phys_addr);
                return 1;
            }
            break;
        default:
            printf("unexpected exit reason %u\n", run->exit_reason);
            return 1;
        }
    }
}
```

编译运行：

```bash
gcc -O2 -o tinyvmm tinyvmm.c
./tinyvmm
```

预期输出：

```
KVM API version: 12
loaded 40 bytes of guest code
Hi
guest requested shutdown
```

（加载的字节数可能因汇编器版本略有不同。）

### 6.3 你刚才做了什么

用一张表对照 Firecracker：

| tinyvmm 做的事 | Firecracker 对应的工作 | 详见 |
|---------------|----------------------|------|
| `mmap` 64 KB 当 Guest 内存 | 按 `mem_size_mib` 分配 Guest 内存（可选大页） | 第 9 篇 |
| 把 `guest.bin` 拷进内存 | 把 Linux 内核 `Image` 加载到 `0x8020_0000` | 第 8 篇 |
| 设置 PC | 设置 PC=内核入口，X0=设备树地址，PSTATE | 第 8 篇 |
| 什么都没告诉 Guest | 生成设备树（FDT），告诉 Guest 有哪些 CPU、内存、设备 | 第 8 篇 |
| 一个 `0x1000` 假串口 | 一个真正的 16550 串口模型 + RTC + virtio 设备 | 第 10 篇 |
| 没有中断控制器 | 创建 vGIC，用 irqfd 注入中断 | 第 10 篇 |
| 单线程 | API 线程 + VMM 事件循环线程 + 每个 vCPU 一个线程 | 第 7 篇 |
| 无任何安全措施 | seccomp、jailer、cgroups、namespace | 第 13、14 篇 |

### 6.4 用 strace 观察

```bash
strace -e trace=ioctl,mmap ./tinyvmm 2>&1 | grep -E 'ioctl|mmap' | head -20
```

你会看到一连串 `ioctl(..., KVM_CREATE_VM, ...)`、`KVM_SET_USER_MEMORY_REGION`、`KVM_RUN`……每一次 `KVM_RUN` 返回，就是一次退出到用户态。数一数 `KVM_RUN` 出现了几次——应该正好是 Guest 写 MMIO 的次数（4 次）。

---

## 七、顺带一提：x86 上是什么样

如果你将来接触 x86 服务器，概念几乎一一对应，只是名字不同：

| ARM64 | x86（Intel） |
|-------|-------------|
| EL2 | VMX root 模式 |
| Guest 在 EL1/EL0 | VMX non-root 模式 |
| HCR_EL2 等寄存器 | VMCS（虚拟机控制结构）中的控制字段 |
| Stage-2 | EPT（AMD 叫 NPT） |
| VM Exit 原因在 ESR_EL2 | VM Exit 原因在 VMCS |
| PSCI | ACPI、键盘控制器复位等 |
| GIC / vGIC | APIC / IOAPIC |
| 设备树（FDT） | ACPI 表 / MPTable |

x86 还有“端口 I/O”（`in`/`out` 指令）这一套 ARM 没有的设备访问方式。KVM 用户态接口（`/dev/kvm`、`KVM_RUN`、`kvm_run`）在两种架构上基本一致，这也是 Firecracker 能同时支持两种架构的原因：大部分代码共享，架构相关部分放在 `arch/aarch64` 和 `arch/x86_64` 目录里。

---

## 小结

| 概念 | 一句话解释 |
|------|-----------|
| HCR_EL2 | EL2 的“开关面板”，决定 Guest 哪些行为会陷入 |
| VM Exit / Entry | Guest 陷入 Hypervisor / 返回 Guest，频繁发生会拖慢性能 |
| VHE | 让宿主 Linux 内核直接运行在 EL2，减少切换开销 |
| IPA / Stage-2 | Guest 以为的物理地址 / 由 KVM 控制的第二级翻译 |
| MMIO 退出 | Guest 访问无内存映射的地址 → KVM → 用户态 VMM 处理 |
| vGIC / 虚拟定时器 | 硬件辅助的中断与时钟虚拟化 |
| PSCI | ARM64 上启动 CPU、关机、重启的标准接口 |
| kvm / vm / vcpu fd | KVM 的三层控制接口 |
| `KVM_RUN` 循环 | 所有 KVM 系 VMM 的心脏 |

---

## 思考题

1. 为什么 Guest 访问普通内存不需要用户态 VMM 参与，而访问设备需要？
2. 在 tinyvmm 中，如果把 Guest 内存改成从 IPA `0x1000` 开始，Guest 往 `0x1000` 写字节会发生什么？
3. tinyvmm 的 Guest 如果执行 `wfi`（等待中断）会怎样？提示：我们没有创建中断控制器。
4. Guest 内存是“按需分配”的。启动一台配置了 1 GB 内存的 microVM 后，宿主机上立刻就少了 1 GB 内存吗？
5. 为什么 virtio 设备要尽量减少“写通知寄存器”的次数？

---

## 下一篇预告

**[04. Firecracker 是什么，为什么会诞生](04-what-is-firecracker.md)**

有了 KVM 这台“发动机”，AWS 为什么还要重新造一辆车？我们会讲 Lambda 遇到的多租户难题、Firecracker 的设计原则，以及它刻意不做的那些事。
