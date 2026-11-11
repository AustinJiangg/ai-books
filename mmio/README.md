# MMIO 从零讲透

一本写给计算机新手的 MMIO（内存映射 I/O）教程。读者只需要会一点 C、能看懂简单的程序，不要求学过操作系统或硬件。从“CPU 怎么指挥一盏 LED 灯”讲起，依次讲清地址空间与总线、设备寄存器，再逐层拆解正确访问 MMIO 要过的几道关——编译器与 `volatile`、内存属性与缓存、顺序与屏障，然后讲中断、DMA，进入 Linux 内核驱动、PCI/PCIe、用户态访问（`/dev/mem`、UIO、VFIO），最后讲虚拟机里的 MMIO 与 virtio-mmio，并汇总常见坑与安全话题。约 6 万字，13 篇。

本书只读不练，没有需要动手的实验；文中的 C 代码都是帮助理解的示例片段，不追求完整可编译。涉及硬件细节时以 ARM64（aarch64）为例，必要时对比 x86。

## 目录

### 第一部分　打地基：CPU 怎么和外设说话

- [第 1 篇　从点亮一盏灯说起：程序怎么控制硬件](01-controlling-hardware.md)
- [第 2 篇　地址空间与总线：一个地址到底送到了哪里](02-address-space-and-bus.md)
- [第 3 篇　设备寄存器：设备的“控制面板”](03-device-registers.md)

### 第二部分　正确地访问 MMIO：坑在哪里

- [第 4 篇　volatile 与编译器：为什么寄存器读写会“消失”](04-volatile-and-compiler.md)
- [第 5 篇　内存属性与缓存：设备内存为什么不能被缓存](05-memory-attributes-and-cache.md)
- [第 6 篇　顺序与屏障：先写数据，再按门铃](06-ordering-and-barriers.md)
- [第 7 篇　设备怎么“回话”：轮询与中断](07-polling-and-interrupts.md)
- [第 8 篇　MMIO 与 DMA：控制走 MMIO，数据走 DMA](08-mmio-and-dma.md)

### 第三部分　操作系统里的 MMIO

- [第 9 篇　Linux 内核驱动里的 MMIO](09-linux-kernel-mmio.md)
- [第 10 篇　PCI 与 PCIe：设备地址是“谈”出来的](10-pci-and-pcie.md)
- [第 11 篇　在用户态访问 MMIO：/dev/mem、UIO 与 VFIO](11-userspace-mmio.md)

### 第四部分　虚拟化与全景

- [第 12 篇　虚拟机里的 MMIO 与 virtio-mmio](12-mmio-in-virtual-machines.md)
- [第 13 篇　全景、常见坑与安全](13-big-picture.md)

编写用文件：[`OUTLINE.md`](OUTLINE.md)（各篇要点）。

## 怎么读

- 第 1～3 篇是概念地基：MMIO 是什么、设备住在哪里、寄存器和内存有什么不同。第 3 篇的结论“寄存器不是内存”是全书的主线。
- 第 4～8 篇是核心：按“编译器 → 缓存 → CPU 乱序 → 中断 → DMA”的顺序，讲清楚正确访问设备要过的每一关。只想弄懂 MMIO 原理，读完前 8 篇即可。
- 第 9～11 篇进入 Linux：内核驱动怎么写、PCI 设备的地址怎么来、用户程序怎么直接访问设备。
- 第 12 篇讲虚拟机，第 13 篇把全书串起来，并附常见坑汇总和术语表。
- 每篇末尾有“本篇小结”表格，复习时过一遍小结即可。
- 本仓库的[《mmap 从零讲透》](../mmap/README.md)（虚拟内存、页表）和[《彻底搞懂 Firecracker》](../firecracker-intro/README.md)（KVM、virtio）与本书互为补充，文中重叠处会给出链接。
