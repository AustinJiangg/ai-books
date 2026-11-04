# 04. Firecracker 是什么，为什么会诞生

> **《彻底搞懂 Firecracker》系列 · 第四篇**
>
> **读完本篇，你能理解：**
> - AWS Lambda 遇到了什么问题，逼出了 Firecracker
> - “microVM”的确切含义，以及 Firecracker 官方承诺的性能指标
> - Firecracker 的设计原则：极简、安全、快速、高密度
> - 它提供了哪些功能，刻意不做哪些事，以及原因
> - 它和 QEMU、Cloud Hypervisor、gVisor、Kata Containers 的关系
> - 本系列所用的版本基线和版本发布规律
>
> **前置知识：** 第 01～03 篇。

---

## 引子：一个函数，一台虚拟机

想象这样一个服务：用户上传一段代码（一个“函数”），你保证有请求来时运行它，没请求时不收钱。这就是 **Serverless**，AWS Lambda 是最早的大规模实践者之一。

这个服务的需求非常苛刻：

1. **隔离必须是虚拟机级别的**：同一台物理机上跑着成千上万个互不相识的客户的代码，其中可能有攻击者；
2. **启动必须极快**：请求到来时才启动环境，用户等不了几秒；
3. **开销必须极低**：每个函数可能只用 128 MB 内存，如果光“环境”本身就要吃掉几百 MB，生意就没法做；
4. **密度必须极高**：一台服务器要能同时跑成千上万个实例，并且每秒钟创建、销毁大量实例。

传统虚拟机满足第 1 条，不满足 2～4 条；容器满足 2～4 条，不满足第 1 条。Firecracker 就是为了同时满足这四条而生的。

---

## 一、诞生的故事

### 1.1 Lambda 早期的做法

Lambda 早期为每个客户分配独立的 EC2 虚拟机，在虚拟机里用容器运行该客户的多个函数。不同客户之间靠虚拟机隔离，同一客户的函数之间靠容器隔离。

这种方式安全，但浪费：一个只偶尔被调用的小函数，也要占用一整台虚拟机的一部分，客户越多、虚拟机越多，资源碎片越严重。

### 1.2 为什么不直接用 QEMU？

KVM 已经提供了硬件虚拟化，配套的 QEMU 是最成熟的用户态 VMM。为什么不直接用？

QEMU 的设计目标是**通用**：能模拟几十种 CPU 架构，上百种设备，能跑 Windows、各种 BSD、各种老旧操作系统，支持 BIOS/UEFI 启动、热迁移、USB、显卡、声卡……它的代码规模是百万行级别的 C 代码。

对 Lambda 来说，这些功能 99% 都用不上，却带来三个代价：

- **攻击面大**：代码越多，漏洞越多，第 02 篇提到的 VENOM 漏洞就出在一个没人用的软驱模拟器里；
- **启动慢**：完整的固件初始化、设备枚举需要时间；
- **内存开销大**：VMM 进程自身就要占用不少内存。

### 1.3 Firecracker 的诞生

AWS 的工程师决定：**只保留 serverless 和容器场景需要的最小功能集，用内存安全的 Rust 重新写一个 VMM。** 项目最初基于 Google 为 ChromeOS 开发的 crosvm 起步（crosvm 同样用 Rust 编写），后来逐渐演化成独立的代码库。

- **2018 年 11 月**，AWS 在 re:Invent 大会上宣布开源 Firecracker，许可证为 Apache 2.0；
- **2020 年**，团队在系统领域顶级会议 NSDI 上发表论文《Firecracker: Lightweight Virtualization for Serverless Applications》，系统阐述了设计取舍；
- 此后它成为 AWS Lambda 和 AWS Fargate 的底层虚拟化技术，也被大量第三方项目采用（第 17 篇）。

这篇论文强烈推荐有兴趣的读者阅读，[附录 C](19-appendix.md#c-推荐阅读) 有链接。

---

## 二、什么是 microVM

**microVM** 不是一个严格的技术术语，而是一种定位：

> 具备完整虚拟机隔离能力（独立的 Guest 内核、硬件虚拟化边界），但只提供运行现代 Linux 工作负载所需的最少设备和功能，从而让启动速度、内存开销和创建速率接近容器。

“micro”指的是**设备模型和功能集**很小，不是指虚拟机的规格小。一台 Firecracker microVM 照样可以配 32 个 vCPU、几十 GB 内存。

### 2.1 官方承诺的指标

Firecracker 仓库里有一份 `SPECIFICATION.md`，列出了团队承诺并用集成测试持续验证的指标（在 AWS 的 `.metal` 实例上测得）。几个最有代表性的：

| 指标 | 承诺值 |
|------|-------|
| VMM 进程启动（直到 API socket 可用） | 约 8 CPU 毫秒 |
| 从收到 `InstanceStart` 到 Guest 开始执行 `/sbin/init` | ≤ 125 毫秒（最小化内核与根文件系统、关闭串口） |
| VMM 线程自身的内存开销（1 vCPU、128 MiB 配置） | ≤ 5 MiB |
| 纯计算性能 | 大于同等裸机性能的 95% |
| 创建速率 | 每个宿主机物理核每秒稳定创建 5 个 microVM |

最后一条换算一下：一台 36 核的服务器，每秒能创建 180 台 microVM。

> ⚠️ 这些数字有严格的前提条件（精简的 Guest 内核、关闭串口输出等）。你在自己机器上用默认配置测，结果会有出入。第 16 篇会教你怎么测，以及什么因素影响结果。

### 2.2 microVM 为什么快

| 传统虚拟机启动要做的事 | Firecracker 的做法 |
|---------------------|------------------|
| 加载 BIOS/UEFI 固件，初始化芯片组 | **没有固件**，VMM 直接把内核放进内存、设置好寄存器，从内核入口开始执行 |
| 固件枚举 PCI 总线、探测硬件 | 默认用 virtio-mmio，设备信息直接写在设备树里，内核不需要探测（也可选 PCI，见第 10 篇） |
| 运行引导程序（GRUB），读取磁盘找到内核 | **没有引导程序**，内核路径由 API 直接指定 |
| 初始化显卡、USB、声卡等设备 | **根本没有这些设备** |
| VMM 进程本身加载大量模块 | 一个静态链接的小二进制，几毫秒就绪 |

---

## 三、设计原则

结合官方设计文档和论文，Firecracker 的设计可以归纳为四条原则。

### 3.1 极简（Minimalism）

只实现必要的设备，每增加一个功能都要经过严格审视。当前（v1.17）的设备清单大致如下：

| 类别 | 设备 | 说明 |
|------|------|------|
| virtio | **block** | 块设备（磁盘），后端是宿主机上的文件或块设备 |
| virtio | **net** | 网卡，后端是宿主机上的 TAP 设备 |
| virtio | **vsock** | Host 与 Guest 之间的 socket 通信，不经过网络 |
| virtio | **balloon** | 内存气球，动态回收 Guest 空闲内存 |
| virtio | **rng** | 熵源，给 Guest 提供随机数 |
| virtio | **pmem** | 持久内存设备（v1.14 起） |
| virtio | **mem** | 内存热插拔（v1.14 起） |
| 传统设备（ARM64） | 16550 串口、PL031 RTC 时钟 | 控制台输出与实时时钟 |
| 传统设备（x86） | 16550 串口、i8042 键盘控制器（仅用于复位） | |
| 平台 | VMGenID、VMClock | 帮助 Guest 感知“我刚从快照恢复”（第 15 篇） |
| KVM 内核模拟 | ARM64：GIC 与定时器；x86：APIC/IOAPIC/PIT | |

再加上一个特殊的“伪设备”：**MMDS（microVM 元数据服务）**，让 Guest 通过网络读取宿主机配置的元数据（第 11 篇）。

### 3.2 安全（Security）

- **用 Rust 编写**：Rust 在编译期杜绝了大部分内存安全错误（缓冲区溢出、释放后使用等），而这类错误正是 C 语言 VMM 历史上最主要的漏洞来源；
- **纵深防御**：假设 Guest 已经完全被攻击者控制，仍然要通过多道防线保护宿主机——KVM 虚拟化边界、精简的设备模型、seccomp 系统调用过滤、jailer 进程沙箱（第 13、14 篇）；
- **一个进程只管一台 microVM**：即使某个 Firecracker 进程被攻破，攻击者也只拿到了这台 microVM 的资源，而不是所有 microVM。

### 3.3 快速（Speed）

启动快、创建快、快照恢复快。为了这一点，Firecracker 宁可放弃一些通用性（比如不支持 BIOS 启动）。

### 3.4 高密度与可超卖（Density & Oversubscription）

Firecracker 允许宿主机 CPU 和内存**超卖**：所有 microVM 配置的 vCPU 总数和内存总量，可以超过物理机实际拥有的数量。因为大多数 serverless 函数大部分时间是空闲的，按需分配才能把硬件用满（第 9 篇讲内存按需分配的原理）。

---

## 四、Firecracker 刻意不做的事

理解一个系统，往往要从它**拒绝做什么**开始。下面这些是 Firecracker 明确不支持或不打算支持的：

| 不做 | 原因 |
|------|------|
| BIOS / UEFI 启动 | 为了快，直接引导 Linux 内核 |
| 运行 Windows 等非 Linux 系统 | Guest 只支持 Linux（社区有人试过 FreeBSD/OSv 等，但不是官方目标） |
| 显卡、USB、声卡等外设 | Serverless 和容器场景不需要，徒增攻击面 |
| 设备直通（VFIO） | 影响快照、迁移和密度，也增加攻击面 |
| 虚拟机在线热迁移 | 用快照恢复替代（第 15 篇） |
| Guest 内“真正”的重启 | Guest 执行 `reboot` 时 Firecracker 直接退出，由上层编排系统决定是否重新创建 |
| 网络流量过滤 | Firecracker 只负责把数据包在 Guest 和 TAP 之间搬运，过滤由宿主机网络栈（iptables/nftables）负责 |
| 管理多台 microVM | 一个进程一台；编排、调度、镜像管理交给上层系统 |

最后一条尤其重要：**Firecracker 不是一个“平台”，而是一个“零件”。** 它不会帮你下载镜像、分配 IP、调度到哪台机器。这些都要你（或第 17 篇介绍的那些上层项目）来做。

---

## 五、与相关技术的关系

### 5.1 同类 VMM

| 项目 | 语言 | 定位 | 与 Firecracker 的关系 |
|------|------|------|---------------------|
| **QEMU** | C | 通用模拟器和 VMM，功能最全 | 设计理念的“反面”，Firecracker 为它做减法 |
| **crosvm** | Rust | ChromeOS 上运行 Linux 应用和 Android | Firecracker 早期的起点 |
| **Cloud Hypervisor** | Rust | 面向云工作负载，支持热插拔、VFIO、更多设备 | 与 Firecracker 共同维护 rust-vmm 公共组件 |
| **Firecracker** | Rust | Serverless、多租户沙箱 | 本系列主角 |

**rust-vmm** 是一个开源社区，把 VMM 中通用的部分（KVM 绑定、内存管理、virtio 队列、内核加载器等）做成独立的 Rust 库，供多个 VMM 共享。Firecracker 用到了其中的 `kvm-ioctls`、`vm-memory`、`linux-loader` 等（第 18 篇源码导读会看到）。

### 5.2 Firecracker 之上的项目

| 项目 | 作用 |
|------|------|
| **Kata Containers** | 让 Kubernetes 的每个 Pod 跑在一台轻量虚拟机里，可以选择 Firecracker 作为 VMM |
| **firecracker-containerd** | 让 containerd 用 Firecracker microVM 运行容器 |
| **Flintlock** 等 | 管理 microVM 生命周期的上层工具 |

第 17 篇会详细介绍这些项目以及 AI 代码沙箱等新兴场景。

### 5.3 与 gVisor 的区别

gVisor 和 Firecracker 都试图解决“容器隔离不够强”的问题，但思路不同：

- **gVisor**：不引入 Guest 内核，而是在用户态重新实现一个兼容 Linux 系统调用的“内核”，拦截应用的系统调用；
- **Firecracker**：给每个工作负载一个真正的 Linux 内核，依靠硬件虚拟化隔离。

Firecracker 的系统调用兼容性是 100%（因为 Guest 里就是真 Linux），代价是需要 KVM，也就需要裸金属机或支持嵌套虚拟化的环境。

---

## 六、版本与支持策略

### 6.1 本系列的版本基线

Firecracker 大约每两到三个月发布一个新版本，遵循语义化版本号。**本系列以 2026 年 11 月时的最新稳定版 v1.17.0 为准**。涉及近期才加入的功能时，会注明从哪个版本开始提供。

几个与本系列相关的近期里程碑：

| 版本 | 重要变化 |
|------|---------|
| v1.13 | 快照功能正式“一般可用”（GA）；新增可选的 **PCI 传输方式**（`--enable-pci`）；ARM64 支持 PVTime |
| v1.14 | 新增 virtio-pmem、virtio-mem 内存热插拔、balloon 空闲页报告/提示、`/serial` 接口 |
| v1.15 | 新增 VMClock 设备 |
| v1.16 | PCI 设备热插拔（开发者预览）、网卡可声明 MTU、ARM64 设备树提供随机数种子；宿主内核支持 6.18 |
| v1.17 | 透明大页选项、块设备 discard、Guest 内核支持 6.18、支持 Graviton5 |

想确认你手里的版本：

```bash
./firecracker --version
```

### 6.2 支持的平台和内核

- **宿主机架构**：x86_64（Intel、AMD）和 aarch64（AWS Graviton 系列等）；
- **宿主机内核**：官方测试并支持 5.10、6.1、6.18 等长期支持版本（以仓库中 `docs/kernel-policy.md` 为准）；
- **Guest 内核**：同样有官方支持列表，建议使用官方 CI 提供的内核配置或其衍生版本。

使用不在支持列表中的内核通常也能跑，但出了问题官方不保证修复。

### 6.3 “开发者预览”功能

Firecracker 的部分功能标记为 **developer preview**，意思是“可以试用，但不建议生产使用，接口可能变化”。例如异步块设备 I/O 引擎（io_uring）、差量快照、PCI 设备热插拔都属于这一类。本系列遇到时会特别标出。

---

## 七、动手：先认识一下这个二进制

在你的 ARM64 机器上下载最新版本（第 05 篇会完整使用它）：

```bash
ARCH="$(uname -m)"
release_url="https://github.com/firecracker-microvm/firecracker/releases"
latest=$(basename $(curl -fsSLI -o /dev/null -w %{url_effective} ${release_url}/latest))
echo "最新版本：${latest}"

curl -L ${release_url}/download/${latest}/firecracker-${latest}-${ARCH}.tgz | tar -xz
ls release-${latest}-${ARCH}/
```

你会看到几个文件：

| 文件 | 作用 |
|------|------|
| `firecracker-vX.Y.Z-aarch64` | VMM 主程序 |
| `jailer-vX.Y.Z-aarch64` | 沙箱启动器（第 14 篇） |
| `seccompiler-bin-…` | 把 JSON 格式的 seccomp 规则编译成过滤器（第 13 篇） |
| `snapshot-editor-…`、`rebase-snap-…` | 快照文件处理工具（第 15 篇） |
| `cpu-template-helper-…` | CPU 模板辅助工具（第 16 篇） |
| `firecracker_spec-vX.Y.Z.yaml` | API 的 OpenAPI（Swagger）规范，第 06 篇会用到 |
| `seccomp-filter-…json` | 默认 seccomp 规则的 JSON 源文件 |
| `V1N1-….json`、`T2-….json` 等 | 预置的 CPU 模板示例 |
| `*.debug`、`SHA256SUMS` 等 | 调试符号和校验文件 |

看看主程序的特点：

```bash
cd release-${latest}-${ARCH}
FC=./firecracker-${latest}-${ARCH}

ls -lh $FC              # 大小只有几 MB
file $FC                # statically linked：静态链接，不依赖系统的任何动态库
$FC --version
$FC --help | head -40   # 浏览一下命令行参数
```

“静态链接”意味着这个二进制把用到的库全部打包进去了（Firecracker 默认用 musl libc 编译）。好处是：放进 jailer 的 chroot 牢笼里后，不需要任何其他文件就能运行——第 14 篇你会看到这一点有多重要。

---

## 小结

| 要点 | 内容 |
|------|------|
| 为什么诞生 | Serverless 需要“虚拟机的隔离 + 容器的速度与密度” |
| microVM | 完整的硬件虚拟化隔离 + 最小化的设备与功能集 |
| 核心指标 | ≤125 ms 启动到 init、≤5 MiB VMM 开销、每核每秒 5 台 |
| 设计原则 | 极简、安全（Rust + 纵深防御）、快速、高密度可超卖 |
| 不做什么 | 固件、Windows、外设、直通、热迁移、真重启、流量过滤、多 VM 管理 |
| 生态位置 | 一个 VMM“零件”，被 Lambda、Fargate、Kata 等上层系统使用 |

---

## 思考题

1. 为什么“一个 Firecracker 进程只运行一台 microVM”能提高安全性？如果一个进程管理 100 台 microVM，会有什么风险？
2. Firecracker 没有 BIOS，那 Guest 内核启动时需要的“硬件信息”（几个 CPU、多少内存、设备在哪）从哪里来？（第 8 篇揭晓）
3. Guest 里执行 `reboot`，Firecracker 为什么选择直接退出，而不是重启 Guest？
4. 如果你要运行一个需要 GPU 的 AI 推理任务，Firecracker 是好选择吗？
5. 静态链接的二进制有什么安全上的好处？

---

## 下一篇预告

**[05. 动手：在 ARM64 机器上跑起第一台 microVM](05-first-microvm.md)**

理论铺垫到此为止。下一篇我们准备 Guest 内核和根文件系统，用 `curl` 一步步配置并启动 microVM，登录进去看看“楚门”眼中的世界。
