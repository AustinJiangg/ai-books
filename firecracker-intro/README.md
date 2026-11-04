# 彻底搞懂 Firecracker

一本写给计算机新手的 Firecracker 教程。读者只需要会用 Linux 命令行，不要求学过操作系统或虚拟化。从“一台电脑是怎么跑起来的”讲起，依次铺垫特权级、系统调用、虚拟内存、硬件虚拟化与 KVM，再动手启动第一台 microVM，然后拆开讲线程模型、启动过程、内存、virtio 设备、网络、存储、安全模型与 jailer、快照、性能与可观测性，最后介绍生态并带读源码。约 6 万字（另有大量命令与示例代码），18 篇正文加附录。

以 Firecracker **v1.17.0**（2026 年 11 月的最新稳定版）为基线；默认以 **ARM64（aarch64）** 宿主机为例，x86 只在差异明显时对比。每篇都有可以在自己机器上跑的实验，开头写明前置知识，结尾有小结表和思考题。

## 目录

### 第一部分　打地基

- [第 1 篇　一台电脑是怎么跑起来的](01-how-a-computer-runs.md)
- [第 2 篇　虚拟化入门：在一台电脑里再造一台电脑](02-virtualization-basics.md)
- [第 3 篇　硬件虚拟化与 KVM（以 ARM64 为主）](03-hardware-virtualization-and-kvm.md)

### 第二部分　认识 Firecracker

- [第 4 篇　Firecracker 是什么，为什么会诞生](04-what-is-firecracker.md)
- [第 5 篇　动手：在 ARM64 机器上跑起第一台 microVM](05-first-microvm.md)
- [第 6 篇　Firecracker 的 API：如何“遥控”一台虚拟机](06-api.md)

### 第三部分　拆开引擎盖：内部原理

- [第 7 篇　进程与线程模型](07-process-and-threads.md)
- [第 8 篇　启动全过程：从 InstanceStart 到看到登录提示](08-boot-process.md)
- [第 9 篇　内存：Guest 眼里的“物理内存”从哪来](09-memory.md)
- [第 10 篇　设备模型：virtio-mmio 全解析](10-virtio.md)
- [第 11 篇　网络：让 microVM 连上世界](11-networking.md)
- [第 12 篇　存储：rootfs、块设备与 I/O](12-storage.md)

### 第四部分　安全

- [第 13 篇　安全模型：为什么敢把陌生人的代码放进来](13-security-model.md)
- [第 14 篇　Jailer：给 Firecracker 再套一层笼子](14-jailer.md)

### 第五部分　高级特性与生产实践

- [第 15 篇　快照与恢复：毫秒级“复活”一台虚拟机](15-snapshots.md)
- [第 16 篇　性能与可观测性](16-performance-and-observability.md)
- [第 17 篇　生态与真实应用](17-ecosystem.md)

### 第六部分　融会贯通

- [第 18 篇　源码导读：Firecracker 代码库地图](18-source-code-tour.md)
- [附录　术语表、常见问题与排错、推荐阅读](19-appendix.md)

编写用文件：[`OUTLINE.md`](OUTLINE.md)（各篇要点）。

## 怎么读

- 第 1～3 篇是概念地基，还没出现 Firecracker 本身，但后面每一篇都建立在它们之上（寄存器、MMIO、中断、EL2、Stage-2、`KVM_RUN` 循环），建议按顺序读。第 3 篇末尾用不到 100 行 C 代码写一个最小的 ARM64 虚拟机，是理解后文的钥匙。
- 第 4～6 篇是上手篇：读完就能自己启动、配置、控制 microVM。只想会用 Firecracker，读到这里即可。
- 第 7～12 篇讲原理，可以按兴趣挑着读，但第 10 篇（virtio）是第 11、12 篇的基础。
- 第 13～16 篇面向生产部署：安全、jailer、快照、性能调优。
- 第 17、18 篇把视野放大：别人怎么用 Firecracker，以及怎样读它的源码。
- 每篇末尾有小结表，复习时过一遍小结即可；遇到报错先查附录 B。
- 实验需要一台 `/dev/kvm` 可读写的 ARM64 Linux 机器，第 2 篇第九节有完整的环境检查步骤。命令输出中的地址、版本号、耗时随机器而异，看量级即可。

想按代码深入（含 e2b 定制版、ARM 适配与 checkpoint 扩展），读完本书可以接着读本仓库的《Firecracker 技术手册》（[网页版](https://austinjiangg.github.io/ai-books/html/firecracker.html) · [Markdown](../firecracker/README.md)）。
