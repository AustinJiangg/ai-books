# 附录

> **《彻底搞懂 Firecracker》系列 · 附录**
>
> - A. 术语表（中英对照）
> - B. 常见问题与排错手册
> - C. 推荐阅读
>
> **版本：** Firecracker v1.17.0，ARM64。

---

## A. 术语表

按首次出现的篇章大致排序。括号内为首次详细讲解的篇号。

### A.1 计算机基础

| 术语 | 英文 | 解释 |
|------|------|------|
| 寄存器 | Register | CPU 内部极快的小容量存储，CPU 当前状态的载体（01） |
| 程序计数器 | Program Counter (PC) | 指向下一条要执行的指令的地址（01） |
| 内存映射 I/O | Memory-Mapped I/O (MMIO) | 通过读写特定地址来访问设备（01） |
| 中断 | Interrupt | 设备主动通知 CPU 的机制（01） |
| 通用中断控制器 | Generic Interrupt Controller (GIC) | ARM 上管理和分发中断的硬件（01、03） |
| 异常级别 | Exception Level (EL0～EL3) | ARM64 的特权等级（01） |
| 系统调用 | System Call | 用户程序请求内核服务的通道（01） |
| 页表 / MMU | Page Table / Memory Management Unit | 虚拟地址到物理地址的翻译机制（01） |
| TLB | Translation Lookaside Buffer | 地址翻译结果的缓存（09） |
| 命名空间 | Namespace | Linux 隔离进程“能看到什么”的机制（02） |
| 控制组 | cgroups | Linux 限制进程“能用多少资源”的机制（02） |

### A.2 虚拟化

| 术语 | 英文 | 解释 |
|------|------|------|
| 宿主机 / 客户机 | Host / Guest | 真实机器 / 虚拟机中的系统（02） |
| 虚拟机监视器 | Hypervisor / VMM | 创建和管理虚拟机的软件；本系列中 KVM 为内核部分，Firecracker 为用户态 VMM（02） |
| 陷入-模拟 | Trap-and-Emulate | Guest 的敏感操作被拦截并由 Hypervisor 模拟（02） |
| 半虚拟化 | Paravirtualization | Guest 知道自己在虚拟机中并主动配合（02） |
| 硬件辅助虚拟化 | Hardware-assisted Virtualization | CPU 提供专用特权层和第二阶段地址翻译（02、03） |
| 虚拟机退出 / 进入 | VM Exit / VM Entry | Guest 陷入 Hypervisor / 返回 Guest（03） |
| 虚拟化主机扩展 | VHE | 让宿主内核直接运行在 EL2 的 ARM 特性（03） |
| 中间物理地址 | IPA | Guest 内核眼中的“物理地址”（03） |
| 第二阶段翻译 | Stage-2 Translation | IPA 到真实物理地址的翻译，由 KVM 控制（03） |
| 电源状态协调接口 | PSCI | ARM 上启动 CPU、关机、重启的标准接口（03、08） |
| 内存槽 | Memory Slot | 注册给 KVM 的一段 Guest 内存（03） |
| 设备树 | Device Tree / FDT / DTB | 描述硬件构成的数据结构（08） |
| 微型虚拟机 | microVM | 完整硬件隔离 + 极简设备模型的轻量虚拟机（04） |

### A.3 virtio 与设备

| 术语 | 英文 | 解释 |
|------|------|------|
| virtio | VIRTIO | 为虚拟机设计的标准化设备接口（02、10） |
| 虚拟队列 | virtqueue | Guest 与设备交换数据的共享内存结构（10） |
| 描述符表 | Descriptor Table | 描述 Guest 内存中缓冲区的数组（10） |
| 可用环 / 已用环 | Available Ring / Used Ring | 驱动→设备的请求队列 / 设备→驱动的完成队列（10） |
| 特性协商 | Feature Negotiation | 驱动与设备确定共同支持的功能（10） |
| ioeventfd | ioeventfd | Guest 写特定地址时由 KVM 直接触发的 eventfd（07、10） |
| irqfd | irqfd | 写入后由 KVM 直接向 Guest 注入中断的 eventfd（07、10） |
| MSI-X | MSI-X | PCI 的消息信号中断，可按队列分配（10） |
| TAP | TAP device | 第 2 层虚拟网卡，用户态程序读写以太网帧（11） |
| vsock | virtio-vsock | Host 与 Guest 之间基于 CID 和端口的 socket 通信（11） |
| CID | Context ID | vsock 地址；宿主机固定为 2（11） |
| MMDS | MicroVM Metadata Service | Firecracker 内置的元数据服务（11） |
| 气球 | Balloon | 回收 Guest 空闲内存的设备（09） |
| 令牌桶 | Token Bucket | Firecracker 限速器使用的算法（12） |

### A.4 Firecracker 专有概念

| 术语 | 解释 |
|------|------|
| API socket | Firecracker 的控制接口，Unix 域套接字上的 REST API（06） |
| VMM 线程 | 运行事件循环、处理所有设备 I/O 的主线程（07） |
| `fc_api` / `fc_vcpu N` | API 线程 / vCPU 线程的线程名（07） |
| jailer | 以 root 布置沙箱后降权 exec 成 Firecracker 的启动器（14） |
| seccomp 过滤器 | 每个线程独立的系统调用白名单（13） |
| CPU 模板 | 控制 Guest 可见 CPU 特性的配置（16） |
| 快照 | 状态文件 + 内存文件，用于暂停后在新进程中恢复（15） |
| 差量快照 | 只保存脏页的快照（开发者预览）（15） |
| UFFD 后端 | 由用户态程序处理快照内存缺页的加载方式（15） |
| VMGenID / VMClock | 帮助 Guest 感知“已从快照恢复”的设备（15） |
| dumbo | Firecracker 内置的极简网络协议栈，服务于 MMDS（11） |
| 开发者预览 | Developer Preview，可试用但不建议生产使用的功能（04） |

---

## B. 常见问题与排错手册

### B.1 环境与权限

**问：`/dev/kvm` 不存在。**
答：宿主机没有可用的 KVM。物理机请确认固件从 EL2 引导内核且内核启用了 KVM（`lsmod | grep kvm` 或检查内核配置）；云主机通常需要裸金属实例。见第 02 篇第九节。

**问：有 `/dev/kvm`，但 Firecracker 报权限错误。**
答：当前用户没有读写权限。加入 `kvm` 组（并重新登录），或使用 ACL：`sudo setfacl -m u:${USER}:rw /dev/kvm`。

**问：`curl` 连接 API socket 失败。**
答：确认 Firecracker 正在运行、socket 路径一致；如果 Firecracker 用 `sudo` 运行，`curl` 也要用 `sudo`；在 jailer 下 socket 位于 chroot 目录中。可用 `ss -a | grep <socket 路径>` 或 `socat - UNIX-CONNECT:<socket 路径>` 检查。

**问：启动时报 API socket 文件已存在。**
答：上一次运行遗留的文件，删除后重试。

### B.2 启动问题

**问：`InstanceStart` 返回与内核文件相关的错误。**
答：检查路径；在 ARM64 上必须是未压缩的 `Image` 格式（`file` 命令应显示 “ARM64 boot executable Image”），不能是 x86 内核或 `Image.gz`。

**问：串口没有任何输出。**
答：内核参数缺少 `console=ttyS0`；没提供 `boot_args` 时默认参数里有 `8250.nr_uarts=0`，会关闭串口。ARM64 上建议加 `keep_bootcon`。也可能是用 `--daemonize` 或在后台运行导致看不到标准输出，可通过 `PUT /serial` 把串口输出重定向到文件。

**问：内核启动卡在 `VFS: Unable to mount root fs`。**
答：rootfs 不是有效的文件系统（用 `e2fsck -fn` 检查）；没有任何磁盘设置 `is_root_device: true`；Guest 内核缺少对应文件系统的驱动；镜像带分区表但没有指定 `partuuid`。

**问：内核启动后提示找不到 init（`No working init found`）。**
答：rootfs 中没有 `/sbin/init`，或用 `init=` 指定的程序不存在、没有执行权限、依赖的库缺失。

**问：Guest 里执行 `reboot` 后 Firecracker 退出了。**
答：这是设计行为。Firecracker 不实现 Guest 重启，需要由上层重新创建 microVM。

### B.3 网络问题

**问：SSH 连不上 Guest。**
答：依次检查：宿主机 `ip addr show tap0` 是否存在且为 UP；Guest 里 `ip addr` 是否配置了预期 IP（CI 镜像根据 MAC 推算 IP，MAC 要对应）；宿主机防火墙是否阻止；Guest 是否运行了 sshd。

**问：Guest 无法访问外网。**
答：Guest 需要默认路由和 DNS；宿主机需要开启 `ip_forward`，配置 NAT（MASQUERADE），且 FORWARD 链允许转发。

**问：启动第二台 microVM 时提示 TAP 设备忙。**
答：每台 microVM 需要独立的 TAP 设备；或者旧进程尚未完全退出。

**问：在 jailer 下打不开 TAP 设备。**
答：降权后的 Firecracker 没有 `CAP_NET_ADMIN`，TAP 需要用 `ip tuntap add ... user <uid> group <gid>` 创建；同时 TAP 必须位于 Firecracker 所在的网络命名空间中。

**问：Guest 访问不到 MMDS。**
答：确认开机前通过 `/mmds/config` 把该网卡加入了 `network_interfaces`；Guest 内有到 MMDS 地址的路由（`ip route add 169.254.169.254 dev eth0`）；使用 V2 时先 `PUT /latest/api/token` 获取令牌。

### B.4 存储问题

**问：两台 microVM 用同一个 rootfs 文件后文件系统损坏。**
答：可写镜像绝对不能共享。共享时必须以只读方式挂载（`is_read_only: true`），可写部分使用每台独立的盘或 overlay。

**问：在 jailer 下提示找不到磁盘或内核文件。**
答：API 与配置中的路径都相对于 chroot 根目录，文件需要事先放进 `<chroot_base>/firecracker/<id>/root/` 并设置正确的属主和权限。

**问：磁盘性能很差。**
答：检查是否配置了限速器；后端文件是否在慢速存储上；考虑 `Async` 引擎（开发者预览）或 PCI 传输；测试时注意宿主机页缓存的影响。

### B.5 内存问题

**问：Firecracker 进程收到 `SIGBUS` 后退出。**
答：最常见的原因是使用 `huge_pages: "2M"` 时宿主机的大页池不足。增大 `/sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages`。

**问：Guest 里释放了内存，宿主机上进程的 RSS 却没有下降。**
答：正常现象。需要使用气球设备或空闲页报告来回收（第 09 篇）。

**问：Firecracker 进程被 OOM Killer 杀死。**
答：宿主机内存超卖过度，或 cgroup 的 `memory.max` 设置得太小（需要比 Guest 内存大一些，为 VMM 自身留出余量）。

### B.6 安全与 seccomp

**问：Firecracker 以退出码 148 退出。**
答：触发了 seccomp 违规（调用了白名单外的系统调用）。检查日志和 `seccomp.num_faults` 指标。可能是使用了不在支持列表中的宿主机内核或 C 库导致新的系统调用路径，也可能是遭受攻击。不要通过 `--no-seccomp` 绕过，应查明原因或报告问题。

**问：jailer 创建很慢。**
答：系统中挂载点过多会显著拖慢 jailer（`pivot_root` 需要处理挂载传播）；并发创建大量 jailer 时更明显。减少挂载点数量。

**问：jailer 启动后 Firecracker 无法打开 `/dev/kvm`。**
答：chroot 所在的文件系统可能以 `nodev` 选项挂载，导致 jailer 用 `mknod` 创建的设备文件无法使用。

### B.7 快照问题

**问：加载快照时报版本不兼容。**
答：快照格式版本与当前 Firecracker 不兼容。用 `firecracker --snapshot-version` 查看支持的版本，用 `--describe-snapshot <文件>` 查看快照的版本，必要时用对应版本重新生成快照。

**问：恢复后 Guest 网络不通。**
答：恢复环境中 TAP 设备名需要与快照时一致（或用 `network_overrides` 覆盖）；网络连接状态不保证在恢复后保持，必要时在 Guest 内重新建立；多个克隆需要网络命名空间隔离。

**问：恢复后文件系统报错。**
答：磁盘不在快照中。恢复时使用的磁盘内容必须与创建快照时一致。

**问：恢复后头几个请求很慢。**
答：内存按需加载导致大量缺页。把快照放在本地快速存储上、预热页缓存、使用大页，或使用 UFFD 自定义预取。

**问：从同一快照恢复的多个实例生成了相同的随机值。**
答：唯一性问题。确认 Guest 内核支持 VMGenID（ARM64 需 6.10 以上或回移植补丁）；用户态程序在恢复后重新初始化随机状态与凭证（第 15 篇第五节）。

---

## C. 推荐阅读

### C.1 官方资料

| 资料 | 地址 |
|------|------|
| Firecracker 官网 | https://firecracker-microvm.github.io |
| GitHub 仓库 | https://github.com/firecracker-microvm/firecracker |
| 入门指南 | 仓库 `docs/getting-started.md` |
| 设计文档 | 仓库 `docs/design.md` |
| 规格承诺 | 仓库 `SPECIFICATION.md` |
| 生产环境主机配置 | 仓库 `docs/prod-host-setup.md` |
| jailer | 仓库 `docs/jailer.md` |
| 快照 | 仓库 `docs/snapshotting/` 目录 |
| 网络 | 仓库 `docs/network-setup.md`、`docs/mmds/`、`docs/vsock.md` |
| 内核支持策略 | 仓库 `docs/kernel-policy.md` |
| API 规范 | 仓库 `src/firecracker/swagger/firecracker.yaml` |
| 变更记录 | 仓库 `CHANGELOG.md` |
| Go SDK | https://github.com/firecracker-microvm/firecracker-go-sdk |

### C.2 论文

- Alexandru Agache 等，*Firecracker: Lightweight Virtualization for Serverless Applications*，NSDI 2020。
  https://www.usenix.org/conference/nsdi20/presentation/agache
  系统阐述了 Firecracker 的设计动机、取舍以及在 Lambda 中的应用，强烈推荐。

### C.3 底层技术

| 主题 | 资料 |
|------|------|
| KVM API | Linux 内核文档 `Documentation/virt/kvm/api.rst`（在线版：https://docs.kernel.org/virt/kvm/api.html） |
| ARM64 Linux 启动约定 | Linux 内核文档 `Documentation/arch/arm64/booting.rst` |
| ARM 架构 | Arm Architecture Reference Manual for A-profile（关于 EL2、Stage-2、GIC 的权威资料） |
| virtio 规范 | OASIS *Virtual I/O Device (VIRTIO) Specification* |
| 设备树 | Devicetree Specification（https://www.devicetree.org） |
| seccomp | `man 2 seccomp`；Linux 内核文档 `Documentation/userspace-api/seccomp_filter.rst` |
| userfaultfd | `man 2 userfaultfd` |
| rust-vmm | https://github.com/rust-vmm |

### C.4 相关项目

| 项目 | 说明 |
|------|------|
| Cloud Hypervisor | 另一个基于 rust-vmm 的 Rust VMM，可对比阅读 |
| crosvm | ChromeOS 的 VMM，Firecracker 的起点 |
| Kata Containers | 用轻量虚拟机运行容器，支持 Firecracker |
| firecracker-containerd | 让 containerd 在 Firecracker 中运行容器 |
| gVisor | 用户态内核方案，与 microVM 思路对比 |

---

*全系列完。*
