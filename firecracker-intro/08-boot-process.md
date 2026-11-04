# 08. 启动全过程：从 InstanceStart 到看到登录提示

> **《彻底搞懂 Firecracker》系列 · 第八篇**
>
> **读完本篇，你能理解：**
> - Firecracker 在收到 `InstanceStart` 后，按什么顺序搭建出一台虚拟机
> - ARM64 microVM 的“物理地址地图”：内存、设备、中断控制器各在哪里
> - ARM64 内核 `Image` 的格式，以及 Firecracker 如何加载它
> - 设备树（FDT）是什么，Firecracker 往里面写了哪些内容
> - 启动时 vCPU 寄存器的初始值，以及其他 CPU 核如何通过 PSCI 被唤醒
> - 从 Guest 内核启动到用户态 init 运行的全过程
>
> **前置知识：** 第 03 篇（Stage-2、vGIC、PSCI、`KVM_SET_ONE_REG`）、第 05 篇（实际启动过一次）、第 07 篇（线程模型）。
>
> **版本：** Firecracker v1.17.0，ARM64。

---

## 引子：没有 BIOS 的开机

真实的 ARM64 服务器开机时，过程大致是这样的：

```
上电 → 固件（如 UEFI/TF-A）初始化硬件 → 引导程序（如 GRUB）→ 读取内核和设备描述 → 跳到内核
```

固件做了大量工作：初始化内存控制器、枚举设备、准备一份“硬件说明书”（设备树或 ACPI 表）交给内核。

Firecracker 没有固件，也没有引导程序。**这些工作全部由 Firecracker 自己在宿主机上用几毫秒完成**，然后直接把 vCPU 的 PC 指向内核入口。这一篇就跟着代码，把这个过程一步步走一遍。

---

## 一、整体流程

当 `PUT /actions {"action_type": "InstanceStart"}` 到达 VMM 线程，Firecracker 调用 `build_microvm_for_boot` 函数（位于 `src/vmm/src/builder.rs`）。按执行顺序，它做了这些事：

```
 ① 分配 Guest 内存（mmap）
 ② 准备内核命令行
 ③ 创建 KVM 虚拟机（KVM_CREATE_VM）
 ④ 创建 vCPU（KVM_CREATE_VCPU），并创建虚拟中断控制器 vGIC
 ⑤ 把 Guest 内存注册给 KVM（KVM_SET_USER_MEMORY_REGION）
 ⑥ 加载内核 Image 到 Guest 内存；加载 initrd（如果有）
 ⑦ 创建并挂载设备：RTC、串口、balloon、block、net、pmem、vsock、rng、virtio-mem、VMGenID、VMClock……
 ⑧ 初始化每个 vCPU，设置启动寄存器
 ⑨ 生成设备树（FDT），写进 Guest 内存
 ⑩ 创建 vCPU 线程（初始为暂停状态），然后让它们开始运行
```

接下来逐个展开最关键的步骤。

---

## 二、ARM64 microVM 的地址地图

在讲加载之前，先看看 Guest 眼中的“物理地址空间”（准确地说是 IPA 空间）是怎么划分的。这些常量定义在 `src/vmm/src/arch/aarch64/layout.rs`：

```
IPA 地址
0x0000_0000 ┌─────────────────────────────────┐
            │          （未使用）               │
            ├─────────────────────────────────┤  ≈ 1 GiB 下方
            │  vGIC（分发器、重分发器等）         │
0x4000_0000 ├─────────────────────────────────┤  MMIO32_MEM_START（1 GiB）
            │  启动计时设备（可选，--boot-timer）  │  每个设备占 4 KiB（0x1000）
0x4000_1000 │  RTC（PL031）                    │
0x4000_2000 │  串口（16550）                    │
            │  virtio-mmio 设备 1、2、3 ……       │
            │  ……                             │
0x7000_0000 │  PCI 配置空间（启用 PCI 时）        │  DRAM 起始前 256 MiB
0x8000_0000 ├─────────────────────────────────┤  DRAM_MEM_START（2 GiB）
            │  系统保留区（2 MiB）               │
0x8020_0000 │  ★ 内核 Image 加载到这里           │
            │  内核的代码、数据、BSS             │
            │  ……（Guest 可用内存）              │
            │  initrd（如果有，放在 FDT 前面）    │
            │  ★ 设备树 FDT（最后 2 MiB）        │
  DRAM 末尾  ├─────────────────────────────────┤
            │  ……                             │
 256 GiB    ├─────────────────────────────────┤  MMIO64_MEM_START
            │  64 位 MMIO（PCI 设备 BAR 等）     │
 512 GiB    └─────────────────────────────────┘
```

几个要点：

- **内存从 2 GiB 处开始**，这是 ARM 推荐的内存布局习惯。配置 1024 MiB 内存，Guest 看到的内存范围就是 `0x8000_0000 ~ 0xBFFF_FFFF`；
- **设备都在内存下方**的 1 GiB ~ 2 GiB 区间。这一段在 Stage-2 页表中没有映射，Guest 访问时会触发第 03 篇讲的 MMIO 退出；
- **内存最大可以配置到 1022 GiB**，超过 256 GiB 时内存会被分成两段，跳过 64 位 MMIO 区域。

---

## 三、加载内核

### 3.1 ARM64 Image 格式

第 05 篇提到，ARM64 上 Firecracker 只接受未压缩的 `Image` 格式内核。这个格式非常简单：文件开头是一个 64 字节的头部，后面紧跟内核代码，整体可以直接放进内存执行。

头部结构（来自 Linux 内核文档 `Documentation/arch/arm64/booting.rst`）：

| 偏移 | 大小 | 字段 | 含义 |
|------|------|------|------|
| 0x00 | 4 | `code0` | 第一条指令（跳转到真正的入口） |
| 0x04 | 4 | `code1` | 第二条指令 |
| 0x08 | 8 | `text_offset` | 加载偏移（现代内核为 0） |
| 0x10 | 8 | `image_size` | 内核运行时需要的总内存大小（含 BSS） |
| 0x18 | 8 | `flags` | 字节序、页大小等标志 |
| 0x20 | 24 | 保留 | |
| 0x38 | 4 | `magic` | 魔数 `0x644d5241`，即 ASCII 的 `ARM\x64` |
| 0x3C | 4 | 保留 | 指向 PE 头的偏移（用于 UEFI 启动） |

动手看看你下载的内核：

```bash
cd ~/fc-lab
xxd -l 64 $(ls vmlinux-* | tail -1)
```

在第 4 行（偏移 0x30）你能看到 `4152 4d64`，就是 `ARM\x64`。偏移 0x10 处的 8 个字节（小端序）就是 `image_size`。

### 3.2 Firecracker 怎么加载

Firecracker 使用 rust-vmm 的 `linux-loader` 库中的 PE 加载器：

1. 读取头部，校验魔数；
2. 计算加载地址：内核必须放在 2 MiB 对齐的地址上，Firecracker 选择 `0x8020_0000`（DRAM 起始 + 2 MiB 系统保留区）；
3. 把整个文件内容复制到 Guest 内存的这个位置；
4. 返回入口地址（就是加载地址本身，因为 `code0` 就在文件开头）。

这就是第 03 篇 tinyvmm 里“把 `guest.bin` 拷进内存”的完全体——只是地址和大小不同而已。

> 💡 **为什么不支持压缩内核？** 解压需要额外的时间和代码（x86 的 bzImage 自带解压代码，ARM64 的 `Image.gz` 则需要引导程序来解压）。Firecracker 追求启动速度，干脆要求用户提供解压好的内核。

### 3.3 内核命令行

Firecracker 会对你提供的 `boot_args` 做一些补充：

- 如果某块磁盘设置了 `is_root_device: true`，追加 `root=/dev/vda rw`（或 `ro`、或 `root=PARTUUID=...`）；
- 如果没有启用 PCI，追加 `pci=off`，让内核不必去探测 PCI 总线；
- 如果你完全没提供 `boot_args`，使用默认值 `reboot=k panic=1 nomodule 8250.nr_uarts=0 i8042.noaux i8042.nomux i8042.dumbkbd swiotlb=noforce`。注意默认值里 `8250.nr_uarts=0` 会**关闭串口**，这是生产环境为了性能和安全的默认选择，所以学习时一定要自己提供带 `console=ttyS0` 的参数。

在 Guest 里执行 `cat /proc/cmdline` 可以看到最终生效的命令行。

在 ARM64 上，命令行不是写在某个固定的内存地址，而是写进设备树的 `/chosen` 节点里（见下节）。

---

## 四、设备树：给 Guest 的“硬件说明书”

### 4.1 为什么需要设备树

x86 的 PC 有很多“约定俗成”的硬件位置（比如串口总在 I/O 端口 `0x3F8`），内核可以直接去那里找。ARM 的世界则千差万别：每块板子、每台服务器的设备地址、中断号都不一样。

ARM 的解决方案是**设备树（Device Tree）**：一份结构化的数据，描述“这台机器有几个 CPU、内存在哪、有哪些设备、它们的地址和中断号是多少”。内核启动时读取它，按图索骥初始化硬件。

设备树有两种形式：

- **DTS**（Device Tree Source）：人类可读的文本格式；
- **DTB / FDT**（Device Tree Blob / Flattened Device Tree）：编译后的二进制格式，内核实际读取的是这个。

服务器级 ARM64 机器也可以用 ACPI 表代替设备树。Firecracker 在 x86 上使用 ACPI，在 ARM64 上使用设备树。

### 4.2 Firecracker 生成的设备树

Firecracker 用 `vm-fdt` 库在内存中直接生成 FDT（代码在 `src/vmm/src/arch/aarch64/fdt.rs`）。它创建的节点包括：

| 节点 | 内容 |
|------|------|
| 根节点 | `compatible = "linux,dummy-virt"`——第 05 篇启动日志里 `Machine model` 的来源 |
| `/cpus` | 每个 vCPU 一个子节点，带 MPIDR（CPU 编号）、`enable-method = "psci"`，以及从宿主机读取的缓存层级信息 |
| `/memory` | 内存的起始地址和大小 |
| `/chosen` | 内核命令行（`bootargs`）、initrd 位置、随机数种子（v1.16 起） |
| `/intc` | vGIC 中断控制器：版本（GICv3 或 GICv2）和寄存器地址 |
| `/timer` | ARM 通用定时器（`arm,armv8-timer`）及其中断号 |
| `/psci` | 声明支持 PSCI 0.2，调用方式为 `hvc` |
| `/apb-pclk` | 一个固定频率的时钟，供 RTC 等设备使用 |
| 设备节点 | RTC（`arm,pl031`）、串口（`ns16550a`）、每个 virtio-mmio 设备（`virtio,mmio`，带地址和中断号） |
| `/vmgenid`、`/vmclock` | 快照相关的辅助设备（第 15 篇） |
| PCI 主桥 | 启用 PCI 时：`pci-host-ecam-generic` |

### 4.3 设备树放在哪

ARM64 Linux 的启动约定要求：设备树必须放在 8 字节对齐的地址，大小不超过 2 MiB，**地址通过 `x0` 寄存器告诉内核**。

Firecracker 把它放在 **Guest 内存的最后 2 MiB**（如果内存小于 2 MiB 则放在 DRAM 起始处）。

### 4.4 动手：把设备树拿出来看

Guest 内核会把它收到的原始设备树暴露在 `/sys/firmware/fdt`。启动一台 microVM，在宿主机上执行：

```bash
cd ~/fc-lab
KEY_NAME=./$(ls *.id_rsa | tail -1)
scp -i $KEY_NAME root@172.16.0.2:/sys/firmware/fdt ./guest.dtb

# 宿主机上安装设备树编译器（Debian/Ubuntu：apt install device-tree-compiler）
dtc -I dtb -O dts guest.dtb 2>/dev/null | less
```

你会看到类似这样的内容（节选，具体数值随配置变化）：

```dts
/ {
    compatible = "linux,dummy-virt";
    #address-cells = <0x02>;
    #size-cells = <0x02>;
    interrupt-parent = <0x01>;

    cpus {
        cpu@0 {
            device_type = "cpu";
            compatible = "arm,arm-v8";
            enable-method = "psci";
            reg = <0x00 0x00>;
            ...
        };
        cpu@1 { ... };
    };

    memory@ram {
        device_type = "memory";
        reg = <0x00 0x80000000 0x00 0x40000000>;   /* 起点 2 GiB，大小 1 GiB */
    };

    chosen {
        bootargs = "keep_bootcon console=ttyS0 reboot=k panic=1 pci=off root=/dev/vda rw";
        ...
    };

    psci {
        compatible = "arm,psci-0.2";
        method = "hvc";
    };

    uart@40002000 {
        compatible = "ns16550a";
        reg = <0x00 0x40002000 0x00 0x1000>;
        ...
    };

    virtio_mmio@40003000 {
        compatible = "virtio,mmio";
        reg = <0x00 0x40003000 0x00 0x1000>;
        interrupts = <0x00 ... 0x01>;
        dma-coherent;
    };
    ...
};
```

把这份文件和第二节的地址地图对照着看，你会发现一切都对上了。

---

## 五、设置 vCPU：开机时 CPU 的状态

### 5.1 初始化 vCPU

对每个 vCPU，Firecracker 调用 `KVM_ARM_VCPU_INIT`，并指定一些特性位：

- **PSCI 0.2**：让 KVM 在内核里实现 PSCI 接口；
- **POWER_OFF**：除了 0 号 vCPU，其余 vCPU 初始处于“关机”状态；
- 可能还有 PMU（性能计数器）、SVE（可伸缩向量扩展）、指针认证等，取决于宿主机能力和 CPU 模板（第 16 篇）。

### 5.2 启动寄存器

ARM64 Linux 的启动约定（同样来自 `booting.rst`）规定，跳进内核时：

- MMU 必须关闭，数据缓存必须关闭；
- 中断必须屏蔽；
- CPU 处于 EL2 或 EL1；
- `x0` = 设备树的物理地址，`x1`～`x3` = 0。

Firecracker 对 0 号 vCPU 用 `KVM_SET_ONE_REG` 设置：

| 寄存器 | 值 | 含义 |
|-------|-----|------|
| `PSTATE` | EL1h，D/A/I/F 全部屏蔽 | 运行在 EL1，屏蔽所有异常和中断 |
| `PC` | `0x8020_0000` | 内核入口 |
| `X0` | FDT 地址（内存末尾 2 MiB 处） | 告诉内核设备树在哪 |

其余 vCPU 只设置 `PSTATE`，PC 由 Guest 内核稍后通过 PSCI 指定。

此外，Firecracker 还会做一些细节处理，比如：在宿主内核支持时，把 Guest 看到的物理计数器清零，避免 Guest 读到宿主机的开机时长（v1.11 起）；按宿主机的真实缓存层级修正 `CLIDR_EL1` 寄存器等。

对照第 03 篇的 tinyvmm：当时我们只设置了 PC，因为那段小程序不需要设备树。

### 5.3 多核启动：PSCI CPU_ON

Guest 内核在 0 号 CPU 上初始化到一定阶段后，读取设备树发现还有其他 CPU，且 `enable-method = "psci"`，就会执行：

```
hvc #0    ; x0 = PSCI_CPU_ON 功能号，x1 = 目标 CPU 的 MPIDR，x2 = 入口地址，x3 = 参数
```

这条 `hvc` 指令陷入 EL2，KVM 在内核里处理：设置目标 vCPU 的 PC 和 `x0`，把它从“关机”状态改为“运行”，唤醒对应的 vCPU 线程。**整个过程 Firecracker 用户态代码完全不参与。**

你可以在 Guest 的启动日志里看到：

```bash
# Guest 内
dmesg | grep -iE 'psci|smp|CPU1'
```

会出现类似 `psci: PSCIv1.x detected in firmware`、`CPU1: Booted secondary processor` 的字样。

---

## 六、启动 vCPU 线程

一切就绪后，Firecracker 为每个 vCPU 创建一个线程（命名为 `fc_vcpu N`），线程一开始处于暂停状态。待 VMM 完成所有设置后，向所有 vCPU 线程发送 `Resume` 指令，它们开始各自的 `KVM_RUN` 循环。

`InstanceStart` 请求返回成功的那一刻，0 号 vCPU 已经在执行内核的第一条指令了。

---

## 七、Guest 内核里发生了什么

从内核入口到出现登录提示，Guest 内部大致经历这些阶段：

```
① 内核入口（head.S）：建立初始页表，打开 MMU
② 解析设备树：认识 CPU、内存、命令行
③ 初始化内存管理、调度器
④ 初始化 GIC、定时器 → 开始能接收中断
⑤ 通过 PSCI 启动其余 CPU
⑥ 按设备树初始化设备驱动：串口 → 控制台可用；PL031 → 读到时间；
   virtio-mmio → 发现 virtio-blk、virtio-net……
⑦ 挂载根文件系统（/dev/vda）
⑧ 执行 /sbin/init（Ubuntu 中是 systemd）
⑨ systemd 启动各项服务，包括 fcnet-setup（配置网络）、sshd、串口登录
```

Firecracker 官方承诺的“≤125 毫秒”，计算的是从收到 `InstanceStart` 到第 ⑧ 步开始的时间，而且使用的是精简内核、最小 rootfs、关闭串口。我们用的 Ubuntu rootfs 跑完整个 systemd 启动流程，从第 ⑧ 步到出现登录提示还需要额外的时间。

### 7.1 动手：看看时间都花在哪

在 Guest 里：

```bash
dmesg | head -5                      # 内核最早的日志，时间戳从 0 开始
dmesg | grep -E 'Run /sbin/init|Freeing unused kernel'   # 内核交棒给用户态的时刻
systemd-analyze                      # 用户态启动花了多久（如果 rootfs 里有 systemd）
systemd-analyze blame | head -10     # 最慢的服务
```

再试一个对比：在宿主机上用脚本精确计量“从发出 InstanceStart 到能 SSH”的时间：

```bash
start=$(date +%s%N)
sudo curl -s -X PUT --unix-socket /tmp/firecracker.socket \
    -d '{"action_type":"InstanceStart"}' http://localhost/actions
until ssh -i $KEY_NAME -o ConnectTimeout=1 -o StrictHostKeyChecking=no \
      root@172.16.0.2 true 2>/dev/null; do sleep 0.05; done
end=$(date +%s%N)
echo "可 SSH 用时：$(( (end - start) / 1000000 )) ms"
```

然后把 `boot_args` 里的 `console=ttyS0` 去掉（串口输出会拖慢启动），再测一次，比较差别。第 16 篇会更系统地分析启动性能。

---

## 八、x86 上有什么不同

如果你将来在 x86 上使用 Firecracker，启动流程的主要差别是：

| 方面 | ARM64 | x86_64 |
|------|-------|--------|
| 内核格式 | 未压缩 `Image` | ELF 格式 `vmlinux`；v1.17 起也支持 `bzImage` |
| 启动协议 | ARM64 Linux 启动约定 | Linux 64 位启动协议，或 PVH 启动（v1.12 起） |
| 硬件描述 | 设备树 | ACPI 表（旧内核可用 MPTable，已弃用） |
| 内存起点 | 2 GiB | 0（低地址有若干保留区，3 GiB～4 GiB 有 MMIO 空洞） |
| 多核启动 | PSCI | APIC 的 INIT/SIPI 机制，由 KVM 模拟 |
| 额外设备 | — | i8042 键盘控制器（用于复位）、KVM 内核模拟的 PIC/IOAPIC/PIT |

---

## 小结

```
InstanceStart
   │
   ├─ mmap Guest 内存（从 IPA 0x8000_0000 起）
   ├─ KVM_CREATE_VM / KVM_CREATE_VCPU / 创建 vGIC
   ├─ KVM_SET_USER_MEMORY_REGION
   ├─ 加载 Image → 0x8020_0000
   ├─ 创建设备，分配 MMIO 地址（1 GiB 起）和中断号
   ├─ KVM_ARM_VCPU_INIT（PSCI 0.2；非 0 号 vCPU 初始关机）
   ├─ 0 号 vCPU：PC=内核入口，X0=FDT 地址，PSTATE=EL1h+屏蔽中断
   ├─ 生成 FDT → 写到内存末尾 2 MiB
   └─ 启动 vCPU 线程 → KVM_RUN
          │
          └─ Guest 内核：解析 FDT → 初始化 GIC/定时器 → PSCI 启动其他核
                         → 驱动设备 → 挂载 /dev/vda → /sbin/init
```

| 概念 | 一句话解释 |
|------|-----------|
| 无固件启动 | VMM 代替固件准备好一切，直接跳进内核 |
| ARM64 Image | 64 字节头 + 内核代码，魔数 `ARM\x64` |
| 设备树 | 告诉 Guest 硬件构成的数据结构，地址通过 X0 传递 |
| PSCI CPU_ON | Guest 内核唤醒其他 CPU 的方式，由 KVM 在内核中处理 |
| `linux,dummy-virt` | Firecracker ARM64 microVM 的“机器型号” |

---

## 思考题

1. 如果把一个 x86 的 vmlinux 文件交给 ARM64 上的 Firecracker，会在哪一步失败？
2. 为什么设备树要放在内存的末尾，而不是紧挨着内核？
3. Guest 内核怎么知道串口在 `0x4000_2000`？如果 Firecracker 在设备树里写错了地址会怎样？
4. 0 号以外的 vCPU 线程在 Guest 内核调用 PSCI `CPU_ON` 之前，在做什么？会消耗宿主机 CPU 吗？
5. 默认命令行里为什么有 `8250.nr_uarts=0`？关闭串口对启动时间和安全各有什么影响？

---

## 下一篇预告

**[09. 内存：Guest 眼里的“物理内存”从哪来](09-memory.md)**

我们已经知道 Guest 内存是 Firecracker 进程里 `mmap` 出来的一块。下一篇深入看：它是怎么按需分配的、大页能带来什么、气球设备如何回收内存、内存超卖的原理与风险。
