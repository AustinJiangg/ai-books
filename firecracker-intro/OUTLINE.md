# 大纲

**读者**：会用 Linux 命令行、但没学过操作系统和虚拟化的新手。
**写法**：先讲“为什么需要”，再讲“是什么”，最后讲“怎么用、坑在哪”。每篇有生活类比、文字图、可以自己跑的实验，结尾有小结表和思考题。
**约定**：以 Firecracker v1.17.0 为基线；默认以 ARM64（aarch64）宿主机为例，x86 只在差异明显时对比；涉及 VMM 时以 Firecracker 为例。涉及版本的内容对照官方仓库源码与文档核对，主线未发布的功能单独注明。
**规模**：18 篇正文加附录，每篇约 3000～6000 字。

## 第一部分　打地基

### 第 1 篇　一台电脑是怎么跑起来的

- CPU、内存、存储、外设（厨房类比）；CPU 只能直接处理内存里的东西
- 指令与寄存器（`x0`～`x30`、PC、SP、PSTATE），取指-译码-执行，多核
- 内存地址与存储层次
- 外设：MMIO 与中断、GIC
- 内核的职责；ARM64 异常级别 EL0～EL3
- 系统调用：`svc`、`x8` 放调用号；实验：不链接 libc 的汇编 hello、`strace`
- 进程、虚拟内存与页表、线程；实验：`/proc` 观察
- 多租户隔离问题：共享内核的风险，引出虚拟机

### 第 2 篇　虚拟化入门

- Host、Guest、Hypervisor、VMM 的区分（KVM 与 Firecracker 的分工）
- 陷入-模拟；Popek-Goldberg 条件
- 三条路线：纯软件模拟、半虚拟化、硬件辅助
- 设备虚拟化：完全模拟、virtio、直通
- Type 1 / Type 2；KVM 的位置；QEMU、Firecracker、Cloud Hypervisor、crosvm
- 容器：namespace 与 cgroups；实验：`unshare` 手工造容器；gVisor
- 对比表；实验：检查 `/dev/kvm`

### 第 3 篇　硬件虚拟化与 KVM

- HCR_EL2、陷入时的 ESR_EL2 / ELR_EL2；VM Exit 的代价
- VHE；nVHE 与 pKVM 简介
- VA → IPA → PA；Stage-2 缺页的两种情况；一次 MMIO 退出的完整旅程
- vGIC、虚拟定时器、PSCI
- KVM 三层 fd、常用 ioctl、`kvm_run`、`KVM_RUN` 循环
- 实验：不到 100 行 C 的 ARM64 迷你 VMM，输出 `Hi`；与 Firecracker 对照
- x86 对照表

## 第二部分　认识 Firecracker

### 第 4 篇　Firecracker 是什么

- Lambda 的需求；为什么不直接用 QEMU；诞生历史与 NSDI 2020 论文
- microVM 的含义；SPECIFICATION 中的承诺指标；为什么快
- 设计原则：极简、安全、快速、高密度；设备清单
- 刻意不做的事
- 与 QEMU、crosvm、Cloud Hypervisor、rust-vmm、Kata、gVisor 的关系
- 版本里程碑（v1.13～v1.17）、支持的平台与内核、开发者预览
- 实验：下载发布包，认识各个二进制

### 第 5 篇　动手跑起第一台 microVM

- 启动 microVM 需要的三样东西
- 获取 Firecracker、CI 内核（ARM64 `Image` 格式）与 Ubuntu rootfs，转 ext4 并放入 SSH 公钥
- 用 `curl` 依次配置 logger、machine-config、boot-source、drives、network-interfaces，`InstanceStart`
- SSH 登录、联网；在 Guest 里观察设备与设备树；在宿主机观察线程
- `--config-file` 一条命令启动；`--enable-pci`
- 常见问题排查表；清理

### 第 6 篇　Firecracker 的 API

- REST over Unix socket 的理由；Swagger 规范
- 状态机：Not started → Running ⇄ Paused
- 资源全景表（开机前 / 运行中）；machine-config、drives、network-interfaces、actions 字段
- 请求在 API 线程与 VMM 线程之间的旅程
- 错误处理；日志与指标
- 实验：纯标准库的 Python 控制脚本，暂停与恢复

## 第三部分　拆开引擎盖

### 第 7 篇　进程与线程模型

- 一进程一 VM；`firecracker`、`fc_api`、`fc_vcpu N` 三类线程
- epoll 与 eventfd；`event-manager` 订阅者
- 单 VMM 线程的取舍
- vCPU 线程：同步 MMIO、ioeventfd、信号唤醒与 VcpuEvent
- 案例：Guest 发一个网络包的全过程
- 为什么用 Rust；rust-vmm 组件
- 实验：线程列表、CPU 占用、`strace`、暂停时的线程状态

### 第 8 篇　启动全过程

- `build_microvm_for_boot` 的十个步骤
- ARM64 地址地图（`layout.rs`）
- ARM64 `Image` 头部与加载；内核命令行的自动补充与默认值
- 设备树：节点清单、放置位置；实验：导出并反编译 `/sys/firmware/fdt`
- vCPU 初始化与启动寄存器；PSCI CPU_ON 多核启动
- Guest 内核启动阶段；实验：测量可 SSH 用时
- x86 对照

### 第 9 篇　内存

- `mmap` + `MAP_NORESERVE`；三层映射；按需分配；实验：VmSize 与 VmRSS
- Guest 释放的内存不归还；virtio-balloon；空闲页报告与提示
- 大页：原理、`2M` 与 `Transparent`；实验：预留大页；ARM64 页大小
- 脏页跟踪；virtio-mem 内存热插拔
- 超卖的收益与风险；swap、KSM、Rowhammer 建议

### 第 10 篇　设备模型：virtio-mmio 全解析

- virtio 三层结构；Firecracker 支持的 virtio 设备
- virtio-mmio 寄存器表；设备树发现；Status 握手与特性协商；激活
- 分离式 virtqueue：描述符表、可用环、已用环；一次磁盘读；EVENT_IDX
- ioeventfd 与 irqfd；ARM64 SPI 中断号与设备数上限；实验：观察中断
- 防御恶意 Guest 的检查
- 串口与 PL031 RTC
- virtio-pci：开启方式、与 MMIO 对比

### 第 11 篇　网络

- TUN 与 TAP；收发包路径；vnet header 与卸载；MAC
- 三种宿主机方案：路由 + NAT、网桥、每 VM 一个网络命名空间
- 流量过滤是宿主机的责任；nftables 示例
- 网络限速器
- MMDS：dumbo 协议栈、配置、V2 令牌、为什么需要令牌
- vsock：CID、映射到 Unix socket、`CONNECT <port>` 协议；实验：socat；典型用途

### 第 12 篇　存储

- 块设备与 virtio-block 请求类型；为什么只支持原始格式
- 制作 rootfs：Alpine minirootfs + 自写 init；从容器镜像导出
- 多块磁盘、只读共享 + overlay、运行中更换后端文件
- `cache_type` 与 `io_engine`
- 令牌桶限速器；实验：`dd` 验证限速
- virtio-pmem、initrd、vhost-user-blk；生产建议

## 第四部分　安全

### 第 13 篇　安全模型

- 威胁模型：攻击者、可信方、保护目标
- 纵深防御五道屏障
- seccomp：原理、每线程白名单、参数过滤、仍被允许的调用与 jailer 的配合、违规退出码 148；实验
- 侧信道与宿主机缓解
- 拒绝服务防御；生产安全检查清单

### 第 14 篇　Jailer

- 先布置牢房再降权 exec 的思路
- jailer 的 15 个步骤与参数
- 实验：专用用户、cgroup v2、网络命名空间与 TAP 属主、chroot 中的文件、配置文件、启动
- 验证：用户、能力集、seccomp、根目录、命名空间、cgroup；清理
- 生产做法与常见坑（`nodev`）

## 第五部分　高级特性与生产实践

### 第 15 篇　快照与恢复

- 快照的组成；磁盘由用户管理；CRC 不防篡改
- 实验：创建与恢复；恢复时覆盖 TAP 名与 vsock 路径
- `MAP_PRIVATE` 按需加载与写时复制；恢复后的热身
- 差量快照与 `snapshot-editor`；UFFD 后端
- 克隆的唯一性陷阱；VMGenID、VMClock、vsock 重置；需要自己做的事
- 兼容性要求；应用模式

### 第 16 篇　性能与可观测性

- 指标分类；启动时间的组成
- `--boot-timer`；外部计时；实验：四组启动对比；加快启动的手段
- 内存开销的测量；`iperf3` 与 `fio`
- vCPU 数量、绑核、CPU 模板（V1N1、自定义模板、cpu-template-helper）
- 指标字段、日志限速、宿主机工具、GDB 与 tracing；调优速查表

### 第 17 篇　生态与真实应用

- AWS Lambda、SnapStart、Fargate
- Kata Containers、firecracker-containerd、Flintlock、Weave Ignite
- Fly.io；AI 代码沙箱（E2B）
- 自建平台的组件图与工程难点；SDK 与工具

## 第六部分　融会贯通

### 第 18 篇　源码导读

- 获取代码；仓库全景与 `src/vmm/src` 目录地图
- 主线一：`main` 到 API 就绪；`VmmAction`、两个 Controller
- 主线二：`build_microvm_for_boot` 与快照恢复路径
- 主线三：vCPU 状态机
- 主线四：设备注册、MMIO 传输层、`queue.rs`、virtio-net
- 其他位置速查；构建、测试；实验：在状态寄存器写入处加日志观察握手
- 阅读顺序、上游项目、参与贡献；全系列回顾

### 附录

- A. 术语表（中英对照）
- B. 常见问题与排错手册
- C. 推荐阅读
