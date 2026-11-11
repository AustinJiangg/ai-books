# 大纲

**读者**：会一点编程（能看懂简单的 C 代码）、但没学过操作系统和硬件的新手。
**写法**：从现实问题出发，先讲“为什么需要”，再讲“是什么”，最后讲“怎么用、坑在哪”。每篇有生活类比、文字图和可以自己跑的小实验，结尾有“本篇小结”表格。
**约定**：代码用 C + Linux；涉及硬件细节时以 ARM64（aarch64）为例，必要时对比 x86；裸机实验统一用 QEMU 的 `virt` 机器（不需要真开发板）；涉及虚拟机监控程序时以 Firecracker（v1.17.0）为例。与本仓库《mmap 从零讲透》《彻底搞懂 Firecracker》重叠的内容（页表、缺页、KVM 基础）只简要回顾并给出链接。
**规模**：15 篇，每篇约 3500～6000 字，合计约 6 万字（另有示例代码）。

## 第一部分　打地基：CPU 怎么和外设说话

### 第 1 篇　从点亮一盏灯说起：程序怎么控制硬件

- 一个问题：`printf` 的字最后是怎么跑到屏幕/串口上的，CPU 只会读写内存和算数，怎么“指挥”一块网卡
- 外设内部有“控制面板”：寄存器的直观类比（遥控器按钮、仪表盘）
- 两种思路：专用 I/O 指令（端口 I/O，x86 的 `in`/`out`）与内存映射 I/O（把设备寄存器“摆”在地址里，用普通的 load/store 访问）
- 历史小故事：PDP-11 的 Unibus、x86 的 64K 端口空间、ARM/RISC-V 为什么只有 MMIO
- MMIO 的一句话定义，以及它和“内存”“mmap”这两个容易混的词有什么关系
- 实验：`cat /proc/ioports`（x86）与 `cat /proc/iomem` 先看一眼
- 引子：地址明明是给内存用的，设备是怎么“住”进去的

### 第 2 篇　地址空间与总线：一个地址到底送到了哪里

- 物理地址空间是一张“城市地图”：不是所有地址都通向内存条
- 地址译码：总线/互连如何根据地址把一次读写路由到 DRAM、ROM 或某个设备
- 读一张真实的内存映射表：QEMU `virt` 机器（Flash、GIC、PL011 UART、RTC、virtio-mmio、PCIe、DRAM 各在哪）
- SoC、片上互连（AXI/APB 简介，只讲概念）
- 系统怎么知道设备在哪：写死、设备树 `reg` 属性、ACPI、PCI 枚举（后面详讲）
- 访问一个“空洞”地址会怎样：总线错误、外部中止、读回全 F
- 实验：解读 `/proc/iomem`；用 `dtc` 反编译 QEMU 导出的设备树，对照地址
- 和虚拟地址的关系：CPU 发出的是虚拟地址，经 MMU 翻译后才是物理地址（回顾，链接 mmap 书第 3 篇）

### 第 3 篇　设备寄存器：设备的“控制面板”

- 寄存器的分类：控制、状态、数据、中断相关；偏移量与基址
- 位域：一个 32 位寄存器里塞多个开关；掩码、移位、读-改-写
- 寄存器和内存的本质区别：读写有“副作用”
  - 读一次值就变（FIFO 数据寄存器、读清零）
  - 写 1 清零（W1C）、只读、只写、写入的值读不回来
  - 写入会触发动作（启动传输、按门铃）
- 手把手读一份数据手册：ARM PL011 UART 的 DR、FR、IBRD/FBRD、LCR_H、CR 寄存器
- 用 C 描述寄存器：宏定义偏移、结构体映射法、位域语法为什么不推荐
- 小结：为什么后面那么多“坑”都来自“寄存器不是内存”

### 第 4 篇　第一个 MMIO 程序：在 QEMU 上裸机输出 Hello

- 环境准备：`qemu-system-aarch64`、交叉编译器 `aarch64-linux-gnu-gcc`
- 最小裸机程序：启动汇编、链接脚本、栈、跳到 C 的 `main`
- 往 `0x09000000` 写字符：轮询 FR 的 TXFF 位，再写 DR
- 从串口读字符：做一个回显程序
- 再控制一个设备：读 PL031 RTC 的计数寄存器拿到时间
- 用 GDB 连 QEMU 单步看 `str`/`ldr` 指令访问设备地址
- 实验：故意不等 FIFO 空、故意写错地址，看会发生什么
- 引出问题：同样的代码加了 `-O2` 为什么输出没了

## 第二部分　正确地访问 MMIO：坑在哪里

### 第 5 篇　volatile 与编译器：为什么你的寄存器读写“消失了”

- 编译器眼中的内存：它可以合并、删除、缓存到寄存器、重排、拆分你的读写
- 实验：轮询状态寄存器的循环在 `-O2` 下变成死循环，`objdump` 对比汇编
- `volatile` 保证了什么：每次访问都真实发生、不与其他 volatile 访问重排、按程序顺序
- `volatile` 不保证什么：不保证 CPU 层面的顺序、不保证原子性、不保证访问宽度
- 访问宽度与对齐：8/16/32/64 位寄存器必须用对应宽度访问；结构体与 memcpy 的坑
- Linux 为什么不直接用 `volatile` 指针：`readl`/`writel` 等访问函数的由来（第 10 篇详讲）
- 小结表：编译器优化与 MMIO 冲突的五种形态

### 第 6 篇　内存属性与缓存：设备内存为什么不能被缓存

- 回顾缓存与缓存行；如果把 UART 的数据寄存器缓存住会发生什么
- 推测读与预取：CPU 可能“提前”读一个地址——对内存无害，对 FIFO 是灾难
- ARM64 的内存类型：Normal 与 Device；Device 的 nGnRnE / nGnRE / nGRE / GRE 四种含义（聚合、重排、提前写响应）
- MAIR 寄存器与页表项里的 AttrIndx：一页内存是什么属性由页表决定
- x86 对照：MTRR、PAT，UC、WC、WT、WB
- 写合并（Write-Combining）：为什么显存帧缓冲用 WC 而控制寄存器用 UC
- Device 内存上的限制：未对齐访问报错、不能用某些指令（如独占访问、`DC ZVA`）、`memcpy` 为什么要换成 `memcpy_toio`
- 实验：在第 4 篇的裸机程序里开 MMU，把 UART 页配置成 Normal 可缓存，观察异常现象

### 第 7 篇　顺序与屏障：先写数据，再按门铃

- 经典场景：先往设备写好参数，最后写“开始”寄存器；顺序错了设备拿到半成品
- CPU 层面的乱序：写缓冲、乱序执行、多核；ARM64 是弱内存序（回顾 mmap 书第 8 篇）
- “提前写响应”（posted write）：写指令完成 ≠ 设备收到；读回同一设备以“冲刷”写
- ARM64 屏障：`DMB`、`DSB`、`ISB` 分别管什么，`osh`/`ish`/`sy` 范围
- 普通内存与 MMIO 之间的顺序：为什么写完 DMA 缓冲区再按门铃需要屏障
- Linux 的约定：`writel` 自带屏障、`writel_relaxed` 不带；`wmb`、`dma_wmb`、`mb` 的区别
- 一个真实 bug 的复盘（以典型网卡驱动门铃顺序问题为例）
- 小结：一张“什么时候需要哪种屏障”的决策表

### 第 8 篇　设备怎么“回话”：轮询与中断

- 轮询：一直读状态寄存器；优点、缺点、什么时候反而更好（高性能网络、NVMe 轮询模式）
- 中断：设备拉一根线，CPU 暂停当前工作去处理
- ARM64 的中断控制器 GIC：Distributor、Redistributor、CPU interface——它们本身也是 MMIO（或系统寄存器）
- 中断处理里的 MMIO：读中断状态、写清除、为什么清晚了会“中断风暴”
- 电平触发与边沿触发；中断屏蔽寄存器
- MSI/MSI-X：中断本身就是一次对特定地址的 MMIO 写
- 实验：在裸机程序里配置 GIC 和 PL011 接收中断，按键触发中断回显

### 第 9 篇　MMIO 与 DMA：控制走 MMIO，数据走 DMA

- 为什么不能全靠 MMIO 搬数据：CPU 一个字一个字搬太慢
- DMA 的思路：CPU 用 MMIO 告诉设备“数据在内存哪里、多长”，设备自己去读写内存
- 描述符环（ring）：生产者/消费者索引，门铃（doorbell）寄存器的作用
- 一次网卡发包的完整流程：填描述符 → 屏障 → 写门铃 → 设备 DMA → 中断 → 回收
- DMA 与缓存一致性：一致性 DMA 与流式 DMA、`dma_map_single`、ARM64 上的缓存维护
- IOMMU/SMMU：给设备也装上“页表”，防止乱写内存
- 小结：MMIO、DMA、中断三者的分工图

## 第三部分　操作系统里的 MMIO

### 第 10 篇　Linux 内核驱动里的 MMIO

- 内核也用虚拟地址：`ioremap` 把设备物理地址映射进内核地址空间，并设好 Device 属性
- `__iomem` 标记与 sparse 检查：为什么不能直接解引用
- 访问函数家族：`readb/w/l/q`、`writeb/w/l/q`、`_relaxed` 版本、`ioread32`、`memcpy_fromio`
- 资源管理：`request_mem_region`、`/proc/iomem` 里的占用记录、`devm_*` 自动释放
- 设备树到驱动：`platform_device`、`platform_get_resource`、`devm_platform_ioremap_resource`
- 实战：写一个最小 platform 驱动，在 QEMU `virt` 上读 PL031 RTC 并通过 sysfs 导出
- regmap：寄存器访问的抽象层，简介即可
- 调试：`/sys/kernel/debug`、`devmem2`、ftrace 的 `mmiotrace`（x86）

### 第 11 篇　PCI 与 PCIe：设备地址是“谈”出来的

- 为什么 PCI 设备地址不能写死：插槽、热插拔、设备数量不确定
- 配置空间：每个设备都有的“身份证 + 申请表”（Vendor ID、Device ID、Class、BAR）
- BAR：设备声明“我需要多大一块 MMIO 空间”，系统分配基址；探测大小的“写全 1 再读回”技巧
- 32/64 位 BAR、可预取（prefetchable）、I/O BAR
- ECAM：配置空间本身也是通过 MMIO 访问的
- 枚举过程：固件/内核如何扫描总线、分配地址、建好桥的窗口
- 实验：`lspci -vv` 读懂 Region 行；`/sys/bus/pci/devices/*/resource`；在 QEMU 上加一个 `edu` 教学设备观察 BAR
- 驱动侧：`pci_iomap`、`pci_resource_start`

### 第 12 篇　在用户态访问 MMIO：/dev/mem、UIO 与 VFIO

- 用户程序能不能直接摸硬件：可以，但要靠 `mmap` 把设备物理地址映射进来（呼应 mmap 书第 12 篇）
- `/dev/mem`：最原始的方式；`CONFIG_STRICT_DEVMEM` 与安全限制
- sysfs 的 `resource0`：直接 `mmap` 一个 PCI BAR
- 用户态 mmap 设备内存时页表属性怎么设：`pgprot_noncached`、`pgprot_writecombine`
- UIO：最小的用户态驱动框架，中断怎么通知
- VFIO：配合 IOMMU 的安全方案，容器/组/设备三层；DPDK、SPDK 的高性能用户态驱动
- 实验：用户态程序 mmap QEMU `edu` 设备的 BAR0，读身份寄存器、做一次阶乘运算
- 风险清单：写错地址把机器搞挂、权限、与内核驱动抢设备

## 第四部分　虚拟化与真实世界

### 第 13 篇　虚拟机里的 MMIO：陷入与模拟

- 客户机里的驱动以为自己在写真设备，其实背后没有硬件：怎么做到的
- 两阶段地址翻译回顾（链接 Firecracker 书第 9 篇）；MMIO 区域在 stage-2 里故意“不映射”
- 一次 MMIO 写的完整旅程：客户机 `str` → stage-2 数据中止 → 陷入 EL2 → KVM 解码 ESR（ISV、SAS、SRT、WnR）→ `KVM_EXIT_MMIO` → VMM 处理 → 返回客户机
- x86 对照：EPT violation / EPT misconfiguration 与指令解码
- Firecracker 里的 MMIO 总线：vCPU 线程收到 exit 后如何按地址找到设备
- 代价：一次 MMIO 退出要几微秒，为什么虚拟设备要尽量少碰寄存器
- 优化：`ioeventfd`/`irqfd`、内核内模拟的设备（GIC 在 KVM 内）、设备直通时 BAR 直接映射进 stage-2
- 实验：用 `perf kvm stat` 或 KVM tracepoint 统计 MMIO 退出

### 第 14 篇　virtio-mmio：为虚拟机量身设计的 MMIO 设备

- 为什么要“半虚拟化”设备：模拟真网卡太慢太复杂
- virtio-mmio 寄存器布局：MagicValue（`0x74726976`，即 “virt”）、Version、DeviceID、特性协商、队列配置、QueueNotify、InterruptStatus、配置空间
- 设备初始化握手：ACKNOWLEDGE → DRIVER → FEATURES_OK → DRIVER_OK
- virtqueue：描述符表、可用环、已用环；QueueNotify 就是门铃（呼应第 9 篇）
- 客户机怎么发现设备：设备树节点、内核命令行 `virtio_mmio.device=`
- Firecracker 的 virtio-mmio 实现导读：设备在地址空间里怎么排布、写 QueueNotify 后发生了什么
- virtio-mmio 与 virtio-pci 的对比：为什么 Firecracker 早期选 MMIO，以及后来的 PCI 支持（以源码核对为准）
- 实验：在 Firecracker（或 QEMU）客户机里查看 `/sys/bus/virtio/devices` 与 `/proc/iomem` 中的 virtio-mmio 区域

### 第 15 篇　全景、排错与安全

- 一次按键从设备到程序的全链路复盘：把 15 篇串起来
- 常见坑汇总表：忘了 volatile、用错访问宽度、缓存属性错误、缺屏障、W1C 误清、读清零被调试器偷读
- 调试工具清单：`/proc/iomem`、`lspci`、`devmem2`、`mmiotrace`、QEMU `-d` 与 `info mtree`、KVM tracepoint、逻辑分析仪（简介）
- 安全话题：DMA 攻击与 IOMMU、`/dev/mem` 的风险、MMIO 相关的 CPU 漏洞（如 MMIO Stale Data）简介
- 其他架构速览：RISC-V、x86 的 MMIO 现状
- 术语表（中英对照）与延伸阅读
