# 全书大纲

本文件是这本书的**编写计划**：讲哪些主题、每篇写什么、面向谁、依赖哪些代码事实。
体例、术语与口径在 [`STYLE.md`](STYLE.md)；图的画法在 [`FIGURE-GUIDE.md`](FIGURE-GUIDE.md)；读者导览在 [`README.md`](README.md)。
本文件是给**编写者与维护者**看的。

---

## 一、全书结构

| 部 | 主题 | 篇目 | 面向 |
|---|---|---|---|
| 〇 | 导读 | 00–01 | 所有读者 |
| 一 | 预备知识 | 02–06 | 不熟悉 KVM / virtio / Rust 系统编程的读者 |
| 二 | 进程与控制面 | 07–12 | 工程师；全书主线的起点 |
| 三 | 内存与 vCPU | 13–19 | 工程师；全书核心之一 |
| 四 | CPU 模板 | 20–22 | 工程师 |
| 五 | 设备 | 23–35 | 工程师 |
| 六 | 快照 | 36–41 | 工程师；全书核心之二，后两部分都建立在它上面 |
| 七 | 安全与可观测 | 42–45 | 工程师、运维 |
| 八 | 工程 | 46–48 | 维护者 |
| 九 | e2b 定制版 | 49–56 | 本项目所有参与者 |
| 十 | ARM 适配版 | 57–73 | 本项目所有参与者 |
| 附录 | 术语表、代码地图、API / 配置总表、差异总表 | 74–79 | 查阅 |

篇幅分配的依据：上游 v1.12.1 约 9.4 万行 Rust（不含测试与内联测试模块，第 01 篇实测；vmm 约 7.7 万，其中 devices 2.9 万、arch 1.1 万、
cpu_config 0.6 万、dumbo 0.7 万；firecracker 主 crate 0.6 万、jailer 0.3 万、acpi-tables 0.3 万、
cpu-template-helper 0.3 万、其余工具 0.3 万）。e2b 定制版在其上改了 18 个源码文件、约 +696 行，外加 guest 内核配置；
ARM 适配版对 Firecracker 源码的改动约 +1660 行（其中 checkpoint / restore 扩展约 +1600：`rollback.rs` 656 行新文件，
`vstate/memory.rs` +276、`vstate/vm.rs` +139），内核零改动。
按代码量两层改动合计不到上游的 3%，本书给它们约三成篇幅（第九、第十部分共 25 篇），
因为这些改动是本项目的工作，读者要拿它们继续开发。

状态图例：`○` 未写　`◐` 草稿　`●` 完成　`◎` 已审校

> **2026-09-15：80 篇（00–79）全部完成并审校。**

---

## 二、代码基线与阅读位置

| 基线 | 位置 | 说明 |
|---|---|---|
| 上游 v1.12.1 | `tmp/e2b-book-src/fc-upstream/` | firecracker-microvm/firecracker tag `v1.12.1`（commit `d990331f7`），git worktree |
| e2b 定制版 | `tmp/e2b-book-src/fc-e2b/` | e2b-dev/firecracker 分支 `firecracker-v1.12-direct-mem` 的 `a41d3fb`（上游 v1.12.1 之后 28 个提交）。这是 e2b infra 2026.09 钉的默认版本 `v1.12.1_a41d3fb`（`packages/shared/pkg/feature-flags/flags.go`）。差异：`git -C tmp/e2b-book-src/fc-e2b diff v1.12.1 a41d3fb`；提交：`git -C tmp/e2b-book-src/fc-e2b log v1.12.1..a41d3fb`。该 clone 带 `upstream` 远端与全部 tag |
| e2b 定制版（guest 内核） | GitHub e2b-dev/fc-kernels，release `v0.0.8`（commit `b8cea06`，2026-02-10，infra 2026.09 之前的最后一个 release）；本机没有 clone，用 `gh api` / `gh release` 查，需要文件时下到 `tmp/e2b-book-src/fc-kernels/`（编写者自己拉，只读） | 只有 config 与构建 / 发布脚本，没有内核源码补丁 |
| ARM 适配版 | `tmp/e2b-book-src/kasandbox-jll/firecracker/` | KASandbox 分支 `jll` 的 `3863c76`：迁入 e2b 分叉的 `54a1c1a`（比 a41d3fb 少两个提交，见第 57 篇）+ 同事的 ARM 构建修复与 HDBSS 使能 + 本项目的 checkpoint / restore 扩展。**部署在鲲鹏上的 `firecracker.arm` 就是从它构建的**（e2b-infra 提交 8266156 说明）。中间状态 `tmp/e2b-book-src/kasandbox-arm/firecracker/`（`b8e85c3`，checkpoint 扩展之前）用来把「ARM 构建修复」与「checkpoint 扩展」分开看。差异：`git -C KASandbox diff 9e880db b8e85c3 -- firecracker`（ARM 构建修复）、`git -C KASandbox diff b8e85c3 3863c76 -- firecracker`（HDBSS + checkpoint 扩展）；e2b 分叉两个版本之间：`git -C tmp/e2b-book-src/fc-e2b diff 54a1c1a a41d3fb` |
| ARM 适配版（guest 内核） | 无源码改动。部署用的 `e2b-infra/vmlinux.bin.arm` 是 e2b-dev/fc-kernels release `v0.0.12`（2026-04-10 构建的 6.1.158 arm64），与 v0.0.8 的 config 相同 | 第 61 篇讲部署里的内核文件布局 |
| e2b infra（调用方） | `tmp/e2b-book-src/upstream/`、`tmp/e2b-book-src/arm/` | 只在需要说明「谁调用这个 API」时看：`packages/orchestrator/internal/sandbox/fc/`、`packages/shared/pkg/fc/firecracker.yml` |
| 单机离线版 | `e2b-infra/` | `e2b-infra.spec`、`e2b-deploy/dep/init-client.sh`（内核与 firecracker 的目录布局） |
| 上游文档 | `tmp/e2b-book-src/fc-upstream/docs/` | `design.md`、`snapshotting/`、`cpu_templates/`、`mmds/`、`jailer.md`、`seccomp.md` 等。是参考，不是依据：以代码为准 |

所有路径相对于 `/home/austin/projects/e2b-repo/`。firecracker 仓库内的路径（正文里引用的）相对于仓库根，
KASandbox 里就是相对于 `firecracker/` 目录。

**不要**读 `KASandbox/`、`KASandbox_0904/`、`infra-arm/` 的工作树，不要读 `fc-kernels-arm/`（那是另一套方案的内核仓库，与本书无关），
也不要读 `/home/austin/projects/firecracker-1.12.1/`（无 git 信息的解包副本）与 `kvcache-ai/firecracker-aenv`（另一个项目）。
KASandbox 的 `jll-xfs` 分支是 XFS + reflink 路线，Firecracker 侧只少一个 `save-dirty-bitmap` 端点，本书只在第 68 篇提一句。

---

## 三、篇目与编写要点

每篇的要点分四块：**讲什么**（bullets）、**代码**（必读位置）、**图表**（建议）、**衔接**（前后篇）。
编写者按要点写，但不受其束缚 —— 读代码时发现要点有误，以代码为准并在交付说明中指出。
要点里写「确认」的地方是编写者必须到代码里核实的事实，大纲作者没有逐条验证。

### 第〇部分　导读

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 00 | `00-overview.md` | 全书导读与 Firecracker 总览 | ◎ |
| 01 | `01-lineage-and-repo-map.md` | 三层版本谱系与仓库地图 | ◎ |

**00 · 全书导读与 Firecracker 总览**（最后写，全书完成后）
一篇读完全貌，给评审、决策者与第一天到岗的新人。5000 字上限。
- Firecracker 是什么：一个进程一台 microVM，KVM 之上的极简 VMM；砍掉了什么、留下了什么
- 一台 microVM 的生命周期：配置（API）→ 构建（builder）→ 运行（vCPU 线程 + 事件循环）→ 暂停 / 快照 / 恢复 → 退出
- 三条主线：控制面（API → VmmAction → 控制器）、数据面（virtio 设备与队列）、状态面（快照与恢复）
- 三层版本的关系：上游做了什么、e2b 为什么改、ARM 适配版改了什么与扩展了什么；每层各一句话
- 分读者的阅读路径（与 README 一致）
- 图：一张进程内结构图（线程、总线、设备、KVM fd）；一张三层谱系图

**01 · 三层版本谱系与仓库地图**
- 三层的提交谱系：上游 `v1.12.1` → e2b `firecracker-v1.12-direct-mem@a41d3fb`（28 个提交，含合入的上游 v1.12 分支修复；infra 2026.09 钉的 `v1.12.1_a41d3fb`）→ KASandbox `firecracker/`（迁入 `54a1c1a`，比 a41d3fb 少两个提交）+ ARM 构建修复 + HDBSS + checkpoint / restore 扩展（`3863c76`，部署的 `firecracker.arm`）
- 每层改了多少：文件数 / 行数表（数据来自 `git diff --stat`，命令见本文件第二节）；改在哪些模块
- guest 内核也放进谱系：e2b-dev/fc-kernels v0.0.8（配置，无补丁）→ ARM 部署用 v0.0.12 官方 arm64 构建（无改动）
- e2b-dev/firecracker 的其它分支（v1.10 / v1.13 / v1.14 的 direct-mem 分支、arm64-uffd-fix）只提一句，第 53、55、57 篇用到时再展开
- 仓库目录结构：`src/*` 各 crate 一句话职责与行数（表）；`resources/`（seccomp 过滤器、guest 配置）、`tests/`、`tools/`、`docs/`
- e2b infra 怎么消费 Firecracker：二进制放 `/fc-versions/<版本名>/firecracker`，版本名 `v<版本>_<hash>`；ARM 单机版里叫 `v1.13.1`（只点到，第 63 篇展开）
- 代码：`Cargo.toml`（workspace members）、`src/*/Cargo.toml`、`git log` 输出、`scripts/build.sh`、`tmp/e2b-book-src/upstream/packages/shared/pkg/feature-flags/flags.go`
- 图：三层谱系图（flowchart，节点是提交，边标改动摘要）；crate 依赖图

### 第一部分　预备知识

面向没有 KVM / virtio / Rust 系统编程背景的读者。每篇讲**本书用得到的**那部分，不做综述；
每篇末尾要明确指出「这些概念在本书哪几篇被用到」。

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 02 | `02-microvm-design-tradeoffs.md` | microVM 与 Firecracker 的设计取舍 | ◎ |
| 03 | `03-kvm-api-primer.md` | 本书用到的 KVM API | ◎ |
| 04 | `04-virtio-and-mmio-primer.md` | virtio 与 virtio-mmio 基础 | ◎ |
| 05 | `05-rust-and-crates-primer.md` | 本书用到的 Rust 与依赖 crate | ◎ |
| 06 | `06-build-run-debug.md` | 构建、运行与调试环境 | ◎ |

**02 · microVM 与 Firecracker 的设计取舍**
- 问题：多租户、不可信负载、秒级启动、高密度；传统 VMM（QEMU）的代价在哪
- Firecracker 的取舍：无 BIOS、无 PCI、只有 virtio-mmio、五种 virtio 设备 + 串口 + 键盘控制器（x86）/ RTC（aarch64）；一个进程一台 VM；API 线程 + VMM 线程 + 每 vCPU 一个线程
- 威胁模型与三道防线：KVM 隔离边界、seccomp、jailer；「设备模型越小攻击面越小」
- 与 e2b 的关系：e2b 需要的正是「从快照秒级恢复」+ 「宿主直接读 guest 内存」，这决定了后面三层的改动方向（只点到）
- 代码：`docs/design.md`（读它，但正文以代码为准）、`src/vmm/src/lib.rs` 的 `Vmm` 结构、`src/firecracker/src/main.rs` 线程创建处
- 图：进程 / 线程 / KVM fd 结构图；隔离层次表

**03 · 本书用到的 KVM API**
- `/dev/kvm` → VM fd → vCPU fd 三级；`KVM_CREATE_VM`、`KVM_CREATE_VCPU`、`KVM_RUN`、`KVM_SET_USER_MEMORY_REGION`
- 内存槽位（memslot）：GPA ↔ HVA 映射；`KVM_MEM_LOG_DIRTY_PAGES` 与 `KVM_GET_DIRTY_LOG`（读一次即清零：这个语义是第 14、68 篇的关键）
- 中断投递：irqfd、ioeventfd、`KVM_IRQ_LINE`；x86 的 irqchip、aarch64 的 GIC 设备（`KVM_CREATE_DEVICE`）
- vCPU 状态：`KVM_GET/SET_REGS`、`SREGS`、`FPU`、`XSAVE`、`MSRS`（x86）；`KVM_ARM_VCPU_INIT`、`KVM_GET/SET_ONE_REG`（aarch64）；`KVM_GET/SET_MP_STATE`
- 能力查询与使能：`KVM_CHECK_EXTENSION`、`KVM_ENABLE_CAP`（第 66 篇 HDBSS 用它）
- Rust 侧封装：`kvm-ioctls` / `kvm-bindings` crate 的对应方法；Firecracker 自己的封装在 `src/vmm/src/vstate/kvm.rs`
- 代码：`src/vmm/src/vstate/kvm.rs`、`src/vmm/src/vstate/vm.rs`（只看 ioctl 调用处）、`src/vmm/src/arch/*/kvm.rs`
- 图：三级 fd 与 ioctl 归属表；memslot 映射示意（flowchart）

**04 · virtio 与 virtio-mmio 基础**
- 为什么是 virtio：半虚拟化设备的契约；前端驱动 / 后端设备；特性协商
- virtqueue：描述符表、可用环、已用环；描述符链；`next_avail` / `next_used` 索引；通知（kick）与中断
- virtio-mmio 传输层：寄存器布局（MagicValue、DeviceID、QueueSel、QueueNotify、InterruptStatus…）、设备状态机（ACKNOWLEDGE → DRIVER → FEATURES_OK → DRIVER_OK）、内核命令行里的 `virtio_mmio.device=` 参数
- 与 PCI 传输的对比：为什么 Firecracker 只用 mmio
- 本书用到的五种设备类型 ID：net 1、block 2、rng 4、balloon 5、vsock 19
- 代码：`src/vmm/src/devices/virtio/generated/`（virtio 头文件的 bindgen 产物）、`src/vmm/src/devices/virtio/mmio.rs`（只看寄存器常量与状态位）
- 图：virtqueue 三个环的布局（```text）；mmio 状态机（flowchart）

**05 · 本书用到的 Rust 与依赖 crate**
- 不是 Rust 教程；讲读这份代码要认识的东西：workspace 与 crate、`cfg(target_arch)` 条件编译、`unsafe` 块与 `SAFETY` 注释规范（clippy `undocumented_unsafe_blocks`）、`thiserror` + `displaydoc` 的错误枚举写法、`Arc<Mutex<T>>` 共享设备、`mpsc` 通道
- 关键依赖 crate 各一段：`vm-memory`（`GuestMemoryMmap`、`GuestAddress`、`Bytes`、`VolatileSlice`）、`kvm-ioctls` / `kvm-bindings`、`vmm-sys-util`（`EventFd`、errno）、`event-manager`（`MutEventSubscriber`）、`micro_http`、`serde` / `bincode`（快照序列化）、`seccompiler`（自带 crate）、`linux-loader`、`vm-superio`（串口 / RTC）、`vm-allocator`、`userfaultfd`
- 生成代码：`bindgen` 出来的 `generated/` 目录与 `tools/bindgen.sh`
- lints 配置（`Cargo.toml` 的 `[workspace.lints]`）说明了代码的纪律
- 代码：`Cargo.toml`、`src/vmm/Cargo.toml`、`src/vmm/src/vstate/memory.rs`（看 `vm-memory` 的用法）
- 图：crate 依赖表（内部 crate / 外部 crate 两张）

**06 · 构建、运行与调试环境**
- `tools/devtool`：容器化构建（`fcuvm` 镜像）、`build --release`、`test`、`checkstyle`；本机 cargo 直接构建的条件（musl target、`rust-toolchain.toml`）
- 产物：`build/cargo_target/<target>/release/firecracker`、`jailer`、`seccompiler-bin`、`snapshot-editor`、`rebase-snap`、`cpu-template-helper`
- 手动跑一台 microVM：准备内核（`resources/guest_configs/`、`resources/rebuild.sh`）与 rootfs、启动进程、用 `curl --unix-socket` 配置、启动、pause、snapshot；`--config-file` 一次性配置；`--no-api`
- 命令行参数总览（表）：`--api-sock`、`--id`、`--seccomp-filter`、`--no-seccomp`、`--log-path`、`--level`、`--metrics-path`、`--boot-timer`、`--mmds-size-limit`、`--http-api-max-payload-size`、`--describe-snapshot`、`--enable-pci`（确认 v1.12.1 是否有）
- 调试：日志级别、`--log-path`、`RUST_BACKTRACE`、gdb 特性（第 45 篇）
- 代码：`tools/devtool`、`tools/devctr/Dockerfile`、`src/firecracker/src/main.rs` 的 `build_arg_parser` / 参数解析、`Makefile`（e2b 加的，只提一句）
- 图：构建流程图；命令行参数表

### 第二部分　进程与控制面

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 07 | `07-process-startup.md` | 进程启动：从参数到运行 | ◎ |
| 08 | `08-api-server.md` | API server：Unix socket 上的 HTTP 与请求解析 | ◎ |
| 09 | `09-rpc-interface.md` | rpc_interface：Preboot 与 Runtime 两个控制器 | ◎ |
| 10 | `10-vm-resources-and-config.md` | 资源模型：VmResources 与 vmm_config | ◎ |
| 11 | `11-builder.md` | builder：从配置到运行中的 microVM | ◎ |
| 12 | `12-vmm-event-loop-and-exit.md` | Vmm、事件循环与退出路径 | ◎ |

**07 · 进程启动：从参数到运行**
- `main()` → `main_exec()`：panic hook、参数解析、日志 / metrics 初始化、`--describe-snapshot` 短路
- 进程级加固：`enable_ssbd_mitigation()`（aarch64）、`resize_fdtable()`（为什么要预扩 fd 表：快照恢复性能；ARM 适配版把它注释掉了 —— 第 58 篇讲原因）、seccomp 过滤器加载（`--seccomp-filter` 自定义 / 默认内嵌 / `--no-seccomp`）
- 两条路：`run_with_api()`（API 线程 + VMM 线程）与 `run_without_api()`（`--no-api` + `--config-file`，单线程）
- `InstanceInfo`：id、state、vmm_version、app_name；e2b 定制版加了 `memory_regions`，ARM 适配版加了 `dirty_tracking`（点到）
- 退出码 `FcExitCode`：每个值的含义
- 代码：`src/firecracker/src/main.rs`、`src/firecracker/src/api_server_adapter.rs` 的 `run_with_api()`、`src/firecracker/src/seccomp.rs`、`src/vmm/src/lib.rs` 的 `FcExitCode`
- 图：启动时序（sequenceDiagram：main、API 线程、VMM 线程、vCPU 线程）；退出码表

**08 · API server：Unix socket 上的 HTTP 与请求解析**
- `micro_http`：为什么自己写一个 HTTP/1.1 子集（无依赖、可 seccomp、可控内存）；`HttpServer`、`ServerRequest`、请求体大小上限
- `ApiServer`：接收请求 → `ParsedRequest::try_from()` 路由（方法 + 路径段 + 可选 body）→ `VmmAction` → 经通道送 VMM 线程 → 等响应 → HTTP 响应
- `parsed_request.rs`：路径到解析函数的映射表；`RequestAction::Sync`；错误到 HTTP 状态码的映射（400 / 404 / 405 / 500）
- `request/*.rs`：每个端点的解析器一览（表：路径、方法、解析函数、产生的 VmmAction）；e2b 定制版加的 `request/memory.rs` 与 ARM 适配版加的 `snapshot` 子路径在各自部分讲
- 同步语义：一次只处理一个请求，请求在 VMM 线程上串行执行；这决定了 API 调用的时延就是 VMM 动作的时延
- swagger 文件 `src/firecracker/swagger/firecracker.yaml` 是契约；e2b infra 从它生成客户端
- 代码：`src/firecracker/src/api_server/mod.rs`、`parsed_request.rs`、`request/`、`src/firecracker/src/api_server_adapter.rs`
- 图：请求处理时序（sequenceDiagram：client、API 线程、VMM 线程）；端点表

**09 · rpc_interface：Preboot 与 Runtime 两个控制器**
- `VmmAction` 枚举：全部变体分类表（配置类、查询类、控制类、快照类）
- `PrebootApiController`：启动前允许的动作，每个动作改 `VmResources`；`InstanceStart` 触发 `build_microvm_for_boot()`；`LoadSnapshot` 触发 `build_microvm_from_snapshot()`，然后控制器切换
- `RuntimeApiController`：运行后允许的动作；`Pause` / `Resume` / `CreateSnapshot` / `FlushMetrics` / `PATCH` 类更新；不允许的动作返回 `OperationNotSupportedPostBoot`
- 状态机：NotStarted → Running ⇄ Paused；哪些动作要求 Paused（`CreateSnapshot`）；`VmState`
- `VmmData` 响应枚举与 `VmmActionError`
- 锁：`Arc<Mutex<Vmm>>`，API 动作在 VMM 线程上拿锁执行；与事件循环的关系
- 代码：`src/vmm/src/rpc_interface.rs`（全文）、`src/vmm/src/vmm_config/instance_info.rs`
- 图：动作与状态的允许矩阵（表）；控制器切换状态图（flowchart 或 stateDiagram，≤5 状态）

**10 · 资源模型：VmResources 与 vmm_config**
- `VmResources`：`machine_config`、`boot_source`、`block`（`BlockBuilder`）、`net_builder`、`vsock`、`balloon`、`entropy`、`mmds`、`mmds_size_limit`、`boot_timer`、`cpu_template`
- `MachineConfig`：`vcpu_count`、`mem_size_mib`、`smt`、`cpu_template`、`track_dirty_pages`、`huge_pages`（`HugePageConfig::None` / `Hugetlbfs2M`）；`MachineConfigUpdate` 的 PATCH 语义与校验（smt 与 vcpu 奇偶、aarch64 不支持 smt 等，确认）
- `BootSourceConfig`：kernel、initrd、boot_args；`default_kernel_cmdline()`；`BootConfig` 打开文件
- 各设备配置结构：`BlockDeviceConfig`（path_on_host / is_root_device / is_read_only / cache_type / io_engine / rate_limiter / socket 用于 vhost-user）、`NetworkInterfaceConfig`、`VsockDeviceConfig`、`BalloonDeviceConfig`、`EntropyDeviceConfig`、`MmdsConfig`（version、ipv4_address、network_interfaces）
- `from_json()`：`--config-file` 路径与 API 路径共用同一套校验
- 代码：`src/vmm/src/resources.rs`、`src/vmm/src/vmm_config/*.rs`
- 图：资源结构图（flowchart：VmResources 下挂各配置）；配置项表

**11 · builder：从配置到运行中的 microVM**
- `build_microvm_for_boot()` 的步骤：创建 guest 内存（`create_guest_memory` / `vm_resources.allocate_guest_memory`，确认函数名）→ `create_vmm_and_vcpus()`（Kvm、Vm、vCPU fd、MMIO 总线、irqchip / GIC）→ `register_memory_regions` → `load_kernel` / initrd → 内核命令行 → 挂设备（block、net、vsock、balloon、entropy、vmgenid、boot timer、串口）→ `configure_system_for_boot`（arch 相关：第 17 / 19 篇）→ `start_vcpus` → seccomp
- `build_and_boot_microvm()` 与 `run_without_api` 的关系
- `attach_*` 函数族与 `MMIODeviceManager::register_mmio_virtio_for_boot()`：设备地址与中断号怎么分配、怎么写进内核命令行（`virtio_mmio.device=`）
- 串口：`setup_serial_device()`、stdin / stdout 非阻塞
- `build_microvm_from_snapshot()` 只点到（第 38 篇）
- 代码：`src/vmm/src/builder.rs`（全文）、`src/vmm/src/device_manager/mmio.rs`（注册部分）
- 图：构建流程（flowchart，按阶段分列）；设备挂载顺序表

**12 · Vmm、事件循环与退出路径**
- `Vmm` 结构的字段与各自归属：`vm`、`vcpus_handles`、`mmio_device_manager`、`acpi_device_manager`（x86）、`pio_device_manager`（x86）、`uffd`、`shutdown_exit_code`、`events_observer`、`resource_allocator`
- `EventManager`（event-manager crate）：VMM 线程的主循环；哪些东西是 subscriber（API 通道、每个 virtio 设备的事件处理器、vCPU 退出事件 `exit_evt`、串口 stdin、balloon 定时器…）；`Vmm` 自己也实现 `MutEventSubscriber` 处理 vCPU 退出
- vCPU 退出 → `Vmm::stop()` → `FcExitCode`；`send_ctrl_alt_del()`（x86 i8042）；guest 关机 / reboot 的表现
- 信号处理：`signal_handler.rs`（SIGSYS 记录 seccomp 违规、SIGBUS / SIGSEGV、SIGHUP / SIGTERM / SIGINT）
- metrics 定时 flush、`FlushMetrics` 动作
- 代码：`src/vmm/src/lib.rs`（`Vmm` 与 `MutEventSubscriber for Vmm`）、`src/vmm/src/signal_handler.rs`、`src/firecracker/src/api_server_adapter.rs`（事件循环的驱动处）
- 图：事件循环与 subscriber 结构图；退出路径 flowchart

### 第三部分　内存与 vCPU

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 13 | `13-guest-memory.md` | guest 内存：GuestMemoryMmap、区域与 memslot | ◎ |
| 14 | `14-dirty-page-tracking.md` | 脏页跟踪：KVM 日志与用户态位图 | ◎ |
| 15 | `15-vcpu-threads-and-state-machine.md` | vCPU 线程与状态机 | ◎ |
| 16 | `16-x86-64-vcpu.md` | x86_64 vCPU：寄存器、CPUID、MSR 与引导协议 | ◎ |
| 17 | `17-x86-64-platform.md` | x86_64 平台：内存布局、ACPI、mptable 与时钟 | ◎ |
| 18 | `18-aarch64-vcpu.md` | aarch64 vCPU：KVM_ARM_VCPU_INIT、寄存器与 PSCI | ◎ |
| 19 | `19-aarch64-platform.md` | aarch64 平台：内存布局、FDT 与 GIC | ◎ |

**13 · guest 内存：GuestMemoryMmap、区域与 memslot**
- `arch_memory_regions()`：x86 的 32 位 MMIO 空洞把内存分成两段；aarch64 从 `DRAM_MEM_START`（0x8000_0000）单段
- 区域的物理后备：匿名 mmap、memfd（`create_memfd`）、HugeTLB 2 MiB（`HugePageConfig`）、快照恢复时的文件 mmap 与 uffd；`GuestRegionMmap` / `GuestMemoryMmap` / `MmapRegion` 的关系；`FileOffset`
- `Vm::register_memory_region()`：每个区域一个 memslot，`KVM_MEM_LOG_DIRTY_PAGES` 由 `track_dirty_pages` 决定；`max_memslots`
- `GuestMemoryExtension` trait：`memfd_backed` / `anonymous` / `snapshot_file` / `dump` / `dump_dirty` / `reset_dirty` / `describe`（确认名字）；`GuestMemoryState` 序列化进快照
- 用户态位图（`Bitmap`）：`vm-memory` 的 `AtomicBitmap`，设备写 guest 内存时标脏；与 KVM 日志的分工在第 14 篇
- 大页的限制：与 uffd、与 balloon 的关系（`docs/hugepages.md`）
- 代码：`src/vmm/src/vstate/memory.rs`、`src/vmm/src/arch/*/mod.rs` 的 `arch_memory_regions`、`src/vmm/src/vstate/vm.rs` 的 `register_memory_region`
- 图：GPA 布局（```text 两个架构各一）；区域 / memslot / 位图关系图

**14 · 脏页跟踪：KVM 日志与用户态位图**
- 问题：Diff 快照要知道哪些页自上次快照以来被写过；写页的有两方 —— guest（经 KVM）和设备（经 VMM 进程）
- KVM 侧：memslot 带 `KVM_MEM_LOG_DIRTY_PAGES` → 写保护 / 脏位收集 → `KVM_GET_DIRTY_LOG` 读取并清零；`Vm::get_dirty_bitmap()` 逐 slot 收集成 `DirtyBitmap = HashMap<slot, Vec<u64>>`；`reset_dirty_bitmap()`
- VMM 侧：`GuestMemoryMmap` 的每个区域带 `AtomicBitmap`，`vm-memory` 在 `write` 路径自动标脏；`reset_dirty()`；哪些路径会绕过它（直接拿裸指针写的地方，确认）
- 合并：`dump_dirty()` 里 `is_kvm_page_dirty || is_firecracker_page_dirty`；`create_snapshot()` 之后「把已激活设备的队列重新标脏」的原因（注释里写了：运行时不标脏队列页）
- 代价：写保护缺页的开销、`track_dirty_pages=false` 时 Diff 快照的行为（确认：报错还是退化成 Full）
- 这一篇是第 37、52、64–67 篇的地基
- 代码：`src/vmm/src/vstate/vm.rs`（`get_dirty_bitmap`、`reset_dirty_bitmap`）、`src/vmm/src/vstate/memory.rs`（`dump_dirty`、`reset_dirty`）、`src/vmm/src/persist.rs` 的 `create_snapshot`
- 图：两张位图与合并流程（flowchart）；写路径与标脏责任表

**15 · vCPU 线程与状态机**
- `Vcpu::new()` / `start_threaded()`：每个 vCPU 一个 OS 线程，线程内先装 seccomp 再进 `run()`
- 状态机（`utils/sm.rs` 的 `StateMachine`）：`running` → `paused` → `exited`；事件 `VcpuEvent`（Pause / Resume / SaveState / DumpCpuConfig / Exit…）与响应 `VcpuResponse`；`VcpuHandle` 的通道与 kick 信号（`register_kick_signal_handler`，用 `SIGRTMIN` 打断 `KVM_RUN`，确认信号号）
- `run_emulation()` 与 `handle_kvm_exit()`：`MmioRead` / `MmioWrite` 走 MMIO 总线、`IoIn` / `IoOut`（x86）走 PIO 总线、`Hlt` / `Shutdown` / `SystemEvent`（aarch64 PSCI 关机 / 重启）、`Debug`（gdb）、`FailEntry` / `InternalError`；`VcpuEmulation` 的分类
- `SaveState` 在 paused 状态下执行 `KvmVcpu::save_state()`；ARM 适配版加了 `RestoreState`（点到）
- 退出：`exit_evt` 通知 VMM 线程；`FcExitCode` 的来源
- 代码：`src/vmm/src/vstate/vcpu.rs`（全文）、`src/vmm/src/utils/sm.rs`
- 图：vCPU 状态机（flowchart，编号边 + 表）；KVM exit 分类表

**16 · x86_64 vCPU：寄存器、CPUID、MSR 与引导协议**
- `KvmVcpu`（x86）：`configure()` 的顺序 —— CPUID（经 CPU 模板归一化，第 21 篇）、MSR、寄存器（`regs.rs` 的 `setup_regs` / `setup_sregs` / `setup_fpu`）、GDT / IDT（`gdt.rs`）、页表（identity 映射到长模式，确认）
- 两种引导协议：Linux 64 位直接引导（`configure_64bit_boot`，boot_params / zero page / E820）与 PVH（`configure_pvh`，`hvm_start_info`）；怎么选（内核 ELF note）
- `save_state()` / `restore_state()`：保存哪些（`kvm_regs`、`sregs`、`fpu`、`xsave` / `xcrs`、`msrs`、`lapic`、`mp_state`、`vcpu_events`、`debug_regs`、`tsc_khz`）；恢复的顺序要求（代码注释里写了 ordering requirements，要讲清）；`MSR_EXCEPTION_LIST` 与 e2b 定制版合入的 `MSR_TSC_RATE`（点到，第 55 篇）
- `xstate.rs`：XSAVE 区域大小与 `KVM_GET_XSAVE2`
- 代码：`src/vmm/src/arch/x86_64/vcpu.rs`、`regs.rs`、`gdt.rs`、`msr.rs`、`xstate.rs`、`interrupts.rs`、`src/vmm/src/arch/x86_64/mod.rs` 的 `configure_pvh` / `configure_64bit_boot`
- 图：vCPU 配置顺序 flowchart；VcpuState 字段表

**17 · x86_64 平台：内存布局、ACPI、mptable 与时钟**
- `layout.rs`：常量表（内核加载地址、cmdline、boot params、初始页表、MMIO 空洞、IRQ 范围）
- `KvmVm`（x86）：`KVM_CREATE_IRQCHIP`、`KVM_CREATE_PIT2`、`KVM_SET_TSS_ADDR`、`KVM_SET_IDENTITY_MAP_ADDR`；`VmState` 保存 pit / irqchip 状态（`save_state` / `restore_state`）
- ACPI：`acpi-tables` crate（RSDP、XSDT、FADT、MADT、DSDT / AML）；`src/vmm/src/acpi/`：什么时候生成、放在哪；`AcpiDeviceManager` 与 vmgenid；`add_virtio_aml()`
- mptable：`mptable.rs`；与 ACPI 的关系（内核配置 `no-acpi` 时靠它，确认）
- `cpu_model.rs`：厂商与型号识别；`kvm.rs` 的 `KVM_CAP` 检查清单
- 时钟：kvm clock、`tsc_khz`；快照跨机器恢复时的 TSC 问题（点到第 41 篇）
- 代码：`src/vmm/src/arch/x86_64/layout.rs`、`vm.rs`、`mptable.rs`、`kvm.rs`、`cpu_model.rs`、`src/vmm/src/acpi/`、`src/acpi-tables/src/`
- 图：GPA 布局（```text）；ACPI 表关系图

**18 · aarch64 vCPU：KVM_ARM_VCPU_INIT、寄存器与 PSCI**
- `KvmVcpu`（aarch64）：`KVM_ARM_PREFERRED_TARGET` → `KVM_ARM_VCPU_INIT`（特性位：PSCI 0.2、power off 非主核、SVE 等，确认）→ `KVM_ARM_VCPU_FINALIZE`（SVE）；`configure()` 设置 PC / X0（FDT 地址）/ PSTATE
- `regs.rs`：`Aarch64RegisterVec` 与寄存器 ID 编码（`KVM_REG_ARM64 | size | class | index`）；`get_registers` / `set_registers`；`MPIDR_EL1` 与 `construct_kvm_mpidrs()`（GIC 需要）
- `save_state()` / `restore_state()`：`KVM_GET_REG_LIST` 得到全部寄存器再逐个 `GET_ONE_REG`；`mp_state`；恢复顺序；`KVM_ARM_VCPU_INIT` 在恢复路径里也要调（这是第 71 篇「回滚为什么要 reinit」的伏笔）
- `cache_info.rs`：从宿主 sysfs 读缓存拓扑写进 FDT
- PSCI：guest 关机 / 重启经 `KVM_EXIT_SYSTEM_EVENT`
- 代码：`src/vmm/src/arch/aarch64/vcpu.rs`、`regs.rs`、`cache_info.rs`、`kvm.rs`
- 图：vCPU 初始化顺序 flowchart；寄存器 ID 编码（```text）

**19 · aarch64 平台：内存布局、FDT 与 GIC**
- `layout.rs`：DRAM 起点、MMIO 区、FDT 位置（内存末尾？确认）、IRQ 基数
- `fdt.rs`：生成设备树的每个节点（cpus、memory、chosen、gic、timer、psci、virtio_mmio 设备、串口、RTC、vmgenid、缓存）；`create_fdt()` 的输入是设备管理器里的 `MMIODeviceInfo`
- GIC：`gic/mod.rs` 选择 v3 或 v2（`KVM_CREATE_DEVICE`）；`GICDevice` trait；寄存器保存 / 恢复（`dist_regs` / `redist_regs` / `icc_regs`，`KVM_DEV_ARM_VGIC_GRP_*` 属性）；快照里的 `GicState`；`KVM_DEV_ARM_VGIC_SAVE_PENDING_TABLES`
- `ArchVm`（aarch64）：`setup_irqchip()` 在 vCPU 创建之后（注释解释了顺序）；`VmState` 只有 GIC；ARM 适配版在这里加了 `enable_hdbss()`（点到）
- 与 x86 的对照表：没有 ACPI（v1.12.1 是否已有 aarch64 ACPI，确认）、没有 PIT / irqchip、没有 i8042、有 RTC
- 代码：`src/vmm/src/arch/aarch64/mod.rs`、`layout.rs`、`fdt.rs`、`gic/`、`vm.rs`
- 图：GPA 布局（```text）；FDT 节点树（```text）；GIC 状态保存流程

### 第四部分　CPU 模板

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 20 | `20-cpu-templates.md` | CPU 模板机制：静态、自定义与序列化 | ◎ |
| 21 | `21-x86-64-cpuid-msr-normalization.md` | x86_64 CPUID 与 MSR 归一化 | ◎ |
| 22 | `22-aarch64-templates-and-helper.md` | aarch64 模板与 cpu-template-helper | ◎ |

**20 · CPU 模板机制：静态、自定义与序列化**
- 问题：快照要在不同宿主间迁移，guest 看到的 CPU 特性必须稳定；模板就是「对 guest 撒谎的清单」
- `CpuConfiguration`（每架构一种）、`CustomCpuTemplate`（JSON：`cpuid_modifiers` / `msr_modifiers` / `reg_modifiers`）、`StaticCpuTemplate`（T2、T2S、T2CL、T2A、C3、V1N1）
- `templates.rs`：`CpuTemplateType`、`GetCpuTemplate`、模板应用到 `CpuConfiguration` 的流程；`templates_serde.rs` 的位掩码字符串语法（`0b0xx1…`）
- `PUT /cpu-config` 端点与 `machine-config.cpu_template` 的关系；模板存进快照（确认：存的是模板还是应用后的配置）
- 代码：`src/vmm/src/cpu_config/templates.rs`、`templates_serde.rs`、`mod.rs`、`docs/cpu_templates/cpu-templates.md`、`schema.json`
- 图：模板应用流程（flowchart）；静态模板一览表

**21 · x86_64 CPUID 与 MSR 归一化**
- `cpuid/mod.rs`：`Cpuid` 枚举（Intel / Amd）、`CpuidKey` / `CpuidEntry`、从 KVM 取 `KVM_GET_SUPPORTED_CPUID`
- `normalize.rs` 三层：通用（`common.rs`：厂商、拓扑 leaf 0xB / 0x1F、APIC id、特性位掩蔽如 `deterministic cache parameters`）、Intel、AMD；每层的关键 leaf 与为什么改
- 静态模板：`t2.rs` 等，每个模板一段：目标（Skylake 级、Cascade Lake 级、AMD Milan 级）、掩掉了哪些特性、加了什么 MSR
- `custom_cpu_template.rs`（x86）：`CpuidRegisterModifier`、`RegisterValueFilter`；MSR 白名单（哪些 MSR 允许改）
- 与快照兼容的关系（`validate_cpu_vendor`、`validate_cpu_manufacturer_id`）
- e2b 定制版合入的两处上游修复（AMD host cpu features 检查、`MSR_TSC_RATE` 例外）在第 55 篇
- 代码：`src/vmm/src/cpu_config/x86_64/`（全部）、`docs/cpu_templates/cpuid-normalization.md`
- 图：归一化流水线 flowchart；模板对比表

**22 · aarch64 模板与 cpu-template-helper**
- aarch64 的 `CpuConfiguration` 就是寄存器向量；`V1N1` 静态模板（Neoverse V1 伪装成 N1：改哪些 ID 寄存器）；`custom_cpu_template.rs`（aarch64）：`reg_modifiers`、允许修改的寄存器范围（`ID_AA64*`）
- 鲲鹏上有没有可用的静态模板：没有（V1N1 针对 Graviton3）；本项目不用模板（确认 e2b infra 传的 `cpu_template`）
- `cpu-template-helper` 工具：`template dump` / `strip` / `verify`、`fingerprint dump` / `compare`；它怎么起一台 microVM 来读配置（`build_microvm_from_config`）；e2b 定制版与 ARM 适配版为它补的 `InstanceInfo` 字段（点到）
- 代码：`src/vmm/src/cpu_config/aarch64/`、`src/cpu-template-helper/src/`、`docs/cpu_templates/cpu-template-helper.md`
- 图：helper 子命令表；V1N1 修改的寄存器表

### 第五部分　设备

每篇一个设备或一层机制。设备篇的固定节：设备的契约（guest 看到什么）、配置与挂载、数据面路径、事件处理、
metrics、状态保存（只点到，第 40 篇统一讲）。

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 23 | `23-bus-and-mmio-device-manager.md` | 设备总线与 MMIO 设备管理器 | ◎ |
| 24 | `24-legacy-devices.md` | legacy 设备：串口、i8042、RTC 与 boot timer | ◎ |
| 25 | `25-virtio-device-model-and-transport.md` | virtio 设备模型与 MMIO 传输层 | ◎ |
| 26 | `26-virtqueue-implementation.md` | virtqueue 实现：queue.rs、iovec 与 iov_deque | ◎ |
| 27 | `27-virtio-block.md` | virtio-block：请求解析与 I/O 引擎 | ◎ |
| 28 | `28-io-uring-engine.md` | io_uring 引擎 | ◎ |
| 29 | `29-vhost-user-block.md` | vhost-user 块设备 | ◎ |
| 30 | `30-virtio-net.md` | virtio-net：tap、收发路径与 offload | ◎ |
| 31 | `31-dumbo-tcpip-stack.md` | dumbo：内建 TCP/IP 栈 | ◎ |
| 32 | `32-mmds.md` | MMDS：元数据服务与 token | ◎ |
| 33 | `33-vsock.md` | vsock：设备、连接状态机与 unix muxer | ◎ |
| 34 | `34-balloon.md` | balloon：气球、统计与 free page 汇报 | ◎ |
| 35 | `35-entropy-vmgenid-rate-limiter.md` | entropy、vmgenid 与速率限制器 | ◎ |

**23 · 设备总线与 MMIO 设备管理器**
- `Bus`（`devices/bus.rs`）：地址区间 → 设备的有序表；`read` / `write` 分发；`BusDevice` 枚举（v1.12.1 是枚举还是 trait object，确认）
- `MMIODeviceManager`：`register_mmio_virtio()`（分配地址与 IRQ、注册 ioeventfd / irqfd）、`register_mmio_serial` / `rtc` / `boot_timer`；`MMIODeviceInfo`；`resource_allocator`（`vm-allocator`：地址与 IRQ 分配）
- 内核命令行参数生成：`add_virtio_device_to_cmdline()`、`add_mmio_serial_to_cmdline()`
- `for_each_virtio_device()` / `with_virtio_device_with_id()`：运行时 PATCH 与快照遍历都靠它们；`kick_devices()`（resume 时）
- x86 的 `PortIODeviceManager`（`legacy.rs`）与 `AcpiDeviceManager`
- 代码：`src/vmm/src/devices/bus.rs`、`src/vmm/src/device_manager/mmio.rs`、`legacy.rs`、`acpi.rs`、`resources.rs`
- 图：总线与设备管理器结构图；MMIO 地址 / IRQ 分配表

**24 · legacy 设备：串口、i8042、RTC 与 boot timer**
- 串口：`vm-superio` 的 `Serial` + `SerialWrapper`；stdin 作为输入事件源、stdout 输出；x86 走 PIO 0x3f8，aarch64 走 MMIO；`emulate_serial_init()` 的用途
- i8042（x86）：只为 ctrl-alt-del 重启；`send_ctrl_alt_del()`
- RTC PL031（aarch64）：只读时钟
- boot timer：`--boot-timer` 时挂的伪设备，guest 内核写一个魔法地址来测启动时延
- 这些设备在快照里怎么处理（串口状态不保存？确认）
- 代码：`src/vmm/src/devices/legacy/`、`src/vmm/src/devices/pseudo/boot_timer.rs`、`src/vmm/src/builder.rs` 的 `setup_serial_device` / `attach_legacy_devices_aarch64`
- 图：两架构 legacy 设备对照表

**25 · virtio 设备模型与 MMIO 传输层**
- `VirtioDevice` trait：`avail_features` / `acked_features` / `device_type` / `queues` / `queue_events` / `interrupt_trigger` / `read_config` / `write_config` / `activate` / `is_activated` / `reset`；`DeviceState`（Inactive / Activated(mem)）
- `MmioTransport`：把 mmio 寄存器读写翻译成 trait 调用；`device_status` 状态机；`queue_select`；驱动写 `QueueNotify` → ioeventfd → 设备的事件处理器
- 中断：`IrqTrigger`（irqfd + `interrupt_status` 位：USED_RING / CONFIG）
- 事件处理器模式：每个设备一个 `*/event_handler.rs`，实现 `MutEventSubscriber`，注册队列 eventfd、rate limiter eventfd、tap fd 等
- 激活前后的行为：激活前收到 kick 怎么办；`reset` 是否实现（确认）
- 代码：`src/vmm/src/devices/virtio/device.rs`、`mmio.rs`、`src/vmm/src/devices/virtio/mod.rs`（类型 ID、`ActivateError`）、任一设备的 `event_handler.rs`
- 图：mmio 写 → 设备的调用链（sequenceDiagram）；DeviceState 状态图（≤5 状态）

**26 · virtqueue 实现：queue.rs、iovec 与 iov_deque**
- `Queue`：`size`、`ready`、`desc_table` / `avail_ring` / `used_ring` 的 GPA、`next_avail` / `next_used`、`num_added`；`pop()` / `pop_or_enable_notification()` / `add_used()` / `prepare_kick()`；`DescriptorChain` 迭代（`next_descriptor`）；`is_valid()` 校验
- 事件抑制 / 通知抑制（`VIRTIO_RING_F_EVENT_IDX`）：`used_event` / `avail_event` 的实现
- `IoVecBuffer` / `IoVecBufferMut`（`iovec.rs`）：把描述符链变成 iovec 数组、`read_volatile_at` / `write_volatile_at`；`iov_deque.rs`：环形 iovec（net RX 用），用 memfd 双映射实现的环
- Kani 证明在这些文件里（`#[cfg(kani)]`），第 45 篇讲
- 快照里的 `QueueState`
- 代码：`src/vmm/src/devices/virtio/queue.rs`、`iovec.rs`、`iov_deque.rs`
- 图：三个环与索引的示意（```text）；pop / add_used 流程 flowchart

**27 · virtio-block：请求解析与 I/O 引擎**
- 配置：`path_on_host`、`is_root_device`、`is_read_only`、`cache_type`（Unsafe / Writeback）、`io_engine`（Sync / Async）、`rate_limiter`；`partuuid`；根设备怎么进内核命令行（`root=` / `PARTUUID=`）
- `Block` 枚举（Virtio / VhostUser）与 `VirtioBlock`：`disk` 属性（大小、`disk_id`）、config space
- 请求：`Request::parse()`（header 描述符 → 数据描述符 → status 描述符）；`RequestType`（In / Out / Flush / GetDeviceID / Unsupported）；`ProcessingResult`
- `FileEngine`：`Sync`（pread / pwrite）与 `Async`（io_uring，第 28 篇）；`process_queue()` 的循环与 rate limiter 的介入点
- 运行时 `PATCH /drives/{id}`：换后端文件（`update_disk_image`）与限速器
- metrics（`metrics.rs` 每设备一套）
- 与 e2b 的关系：e2b 用 NBD 设备作为 `path_on_host`（一句话链接 e2b 手册）
- 代码：`src/vmm/src/devices/virtio/block/`（`device.rs`、`virtio/device.rs`、`virtio/request.rs`、`virtio/io/`、`virtio/event_handler.rs`）
- 图：请求处理 flowchart；配置项表

**28 · io_uring 引擎**
- 为什么自己封装 io_uring 而不用 crate：seccomp 可控、无依赖
- `io_uring/mod.rs`：`IoUring::new()`（`io_uring_setup`、mmap SQ / CQ）、`push()` / `submit()` / `pop()`；`restriction.rs`（`IORING_REGISTER_RESTRICTIONS` 只允许 read / write / fsync，安全考虑）；`probe.rs`
- `operation/`：`Sqe` / `Cqe` 封装、`OpCode`；`queue/submission.rs` / `completion.rs` 的环操作
- 块设备 `async_io.rs`：`AsyncFileEngine`，completion eventfd 进事件循环、`pending` 计数、`drain()` 在 pause / snapshot 时的作用
- 内核版本要求与 `io_engine=Async` 的可用性检查
- 代码：`src/vmm/src/io_uring/`（全部）、`src/vmm/src/devices/virtio/block/virtio/io/async_io.rs`
- 图：SQ / CQ 环与用户态 / 内核态分工（```text 或 flowchart）；提交 / 完成时序

**29 · vhost-user 块设备**
- 问题：把块设备后端放到另一个进程（如 SPDK），Firecracker 只做前端
- `vhost_user.rs`：协议实现（`VhostUserMaster`？确认类型名）、消息（GET_FEATURES、SET_MEM_TABLE、SET_VRING_*、SET_PROTOCOL_FEATURES…）、Unix socket 连接
- `block/vhost_user/device.rs`：配置（`socket`）、`activate()` 时把 memslot 表与 vring 描述交给后端、`config` 读取（`VHOST_USER_GET_CONFIG`）
- 快照与 vhost-user：恢复时怎么重连（`VhostUserBlockState`、`update_vhost_user_block_config`）
- metrics（`vhost_user_metrics.rs`）
- 代码：`src/vmm/src/devices/virtio/vhost_user.rs`、`block/vhost_user/`、`docs/api_requests/block-vhost-user.md`
- 图：前后端进程与消息时序（sequenceDiagram，≤6 参与者）

**30 · virtio-net：tap、收发路径与 offload**
- 配置：`iface_id`、`host_dev_name`、`guest_mac`、`rx_rate_limiter` / `tx_rate_limiter`；tap 设备打开与 `TUNSETIFF` / `TUNSETOFFLOAD` / vnet header（`tap.rs`）
- TX 路径：guest 写 TX 队列 → kick → `process_tx()` → 从描述符链读帧 → `write` 到 tap；MMDS 拦截点（目标 IP 是 MMDS 地址就交给 dumbo，第 31 / 32 篇）
- RX 路径：tap 可读 → `process_rx()` → `RxBuffers`（用 `IoVecBufferMut` 预解析 RX 描述符链：`parse_rx_descriptors()`、`rx_buffer.parsed_descriptors` / `used_descriptors` / `used_bytes`）→ `readv` 到 guest 内存 → `add_used`；`rx_deferred_frame` 的处理；这一段是第 72 篇「回滚要重建 RX 缓存」的伏笔
- offload：`VIRTIO_NET_F_GUEST_CSUM` / `TSO` / `UFO` 等特性与 tap offload 的对应；`mtu`
- rate limiter 的介入：eventfd 定时器、`RateLimiter::consume()`；`PATCH /network-interfaces/{id}`
- metrics
- 代码：`src/vmm/src/devices/virtio/net/device.rs`、`tap.rs`、`event_handler.rs`、`persist.rs`（`RxBufferState`）
- 图：TX / RX 路径 flowchart（分两列）；RX 缓存结构（```text）

**31 · dumbo：内建 TCP/IP 栈**
- 问题：MMDS 要回应 guest 的 HTTP 请求，但不能引入宿主网络栈；所以在 net 设备里内建一个只够用的栈
- `pdu/`：ethernet / arp / ipv4 / tcp / udp 的帧解析与构造（`bytes.rs` 的零拷贝视图）
- `tcp/`：`Connection`（简化的 TCP 状态机：只做服务端、无拥塞控制、固定窗口）、`Endpoint`（HTTP 请求的接收与响应）、`handler.rs`（`TcpIPv4Handler`：连接表、超时、RST）
- `dumbo/mod.rs`：`MmdsNetworkStack`：`detour_frame()` 判断帧是否发给 MMDS（IP、MAC、ARP）、`write_next_frame()` 产生回包
- 限制清单（不支持什么）与安全考虑（不可信 guest 输入的解析）
- 代码：`src/vmm/src/dumbo/`（全部）、`docs/mmds/mmds-design.md` 的 Dumbo 一节
- 图：帧的分流 flowchart；TCP 连接状态（flowchart 编号边）

**32 · MMDS：元数据服务与 token**
- 用途：给 guest 传元数据（e2b 用它把沙箱元数据交给 envd —— 一句话链接）
- 配置：`PUT /mmds/config`（version V1 / V2、`ipv4_address`、`network_interfaces`）；`PUT /mmds` / `PATCH /mmds` 写数据；`GET /mmds` 读回
- `data_store.rs`：JSON 树、大小限制（`--mmds-size-limit`）、`PATCH` 的合并语义
- `mmds/mod.rs`：请求路由（GET 路径 → JSON 子树，IMDS 风格的文本 / JSON 输出格式）、状态码
- V2：`token.rs`（PUT `/latest/api/token`、TTL、`X-metadata-token` 头）、`token_headers.rs`；为什么要 V2（SSRF 防护）
- `ns.rs`：把 dumbo 的 HTTP 请求接到 MMDS
- 快照里的 MMDS 状态（`persist.rs`）
- 代码：`src/vmm/src/mmds/`（全部）、`src/firecracker/src/api_server/request/mmds.rs`、`docs/mmds/mmds-user-guide.md`
- 图：请求路径时序（guest → net 设备 → dumbo → mmds）；V1 / V2 对比表

**33 · vsock：设备、连接状态机与 unix muxer**
- 契约：guest CID、宿主侧 Unix socket（`uds_path`）；guest 连宿主：`uds_path` 的 `CONNECT <port>` 握手；宿主连 guest：`uds_path_<port>` 监听
- `packet.rs`：vsock 帧头（`VsockPacket`）、与描述符链的映射
- `csm/`：`VsockConnection` 状态机（`ConnState`：LocalInit / PeerInit / Established / LocalClosed / PeerClosed / Killed）、流控（`peer_buf_alloc` / `fwd_cnt`）、`txbuf.rs`
- `unix/muxer.rs`：`VsockMuxer` 把多个连接复用到设备的 RX / TX 队列上；`muxer_rxq.rs` / `muxer_killq.rs`；epoll 管理宿主侧 fd
- `device.rs` / `event_handler.rs`：RX / TX / event 队列；`VIRTIO_VSOCK_EVENT_TRANSPORT_RESET`（快照恢复后通知 guest 连接失效：`docs/snapshotting/snapshot-support.md` 的 Vsock device reset）
- 代码：`src/vmm/src/devices/virtio/vsock/`（全部）
- 图：连接状态机（flowchart 编号边 + 表）；muxer 结构图

**34 · balloon：气球、统计与 free page 汇报**
- 契约：`amount_mib` 目标、`deflate_on_oom`、`stats_polling_interval_s`；inflate / deflate / stats 三个队列（+ free page hinting / reporting 队列，确认 v1.12.1 是否有）
- `device.rs`：`process_inflate()` 把 guest 归还的页 `madvise(MADV_DONTNEED)`（`util.rs` 的 `remove_range`，对 HugeTLB 的处理）；`process_deflate()`；`process_stats()` 与 `BalloonStats` 字段
- 运行时 `PATCH /balloon`、`PATCH /balloon/statistics`；`GET /balloon/statistics`
- 定时器：stats 轮询 eventfd
- 与快照、与脏页的关系（归还的页在快照里怎么算）
- e2b 是否用 balloon（确认 e2b infra 的调用；不用就说明为什么这一篇仍要读）
- 代码：`src/vmm/src/devices/virtio/balloon/`（全部）、`docs/ballooning.md`
- 图：inflate 流程 flowchart；配置与统计字段表

**35 · entropy、vmgenid 与速率限制器**
- entropy（virtio-rng）：`rng/device.rs` 用 `aws-lc-rs` 生成随机数填 guest 缓冲；rate limiter；为什么快照恢复后需要它（`docs/snapshotting/random-for-clones.md`）
- vmgenid：ACPI（x86）/ FDT（aarch64）设备，16 字节 generation id 写在 guest 内存，快照恢复时 `notify_guest()`（中断）让 guest 重新播种；ARM 适配版加的 `refresh_generation()`（点到）
- rate limiter：`TokenBucket`（size、one_time_burst、refill_time）、`RateLimiter`（bandwidth + ops 两个桶）、`consume()` / `manual_replenish()`、timerfd 驱动的阻塞 / 解除；快照里的 `RateLimiterState`
- 代码：`src/vmm/src/devices/virtio/rng/`、`src/vmm/src/devices/acpi/vmgenid.rs`、`src/vmm/src/rate_limiter/`
- 图：令牌桶示意（flowchart 或 ```text）；三个设备的配置表

### 第六部分　快照

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 36 | `36-snapshot-overview-and-format.md` | 快照总览：文件、版本与 MicrovmState | ◎ |
| 37 | `37-snapshot-create.md` | 创建快照：save_state、内存导出与 Diff | ◎ |
| 38 | `38-snapshot-load.md` | 加载快照：restore、内存后端与设备重建 | ◎ |
| 39 | `39-uffd-backend.md` | userfaultfd 后端与缺页处理 | ◎ |
| 40 | `40-device-persist.md` | 设备状态的 Persist：逐设备的保存与恢复 | ◎ |
| 41 | `41-snapshot-tools-and-compat.md` | snapshot-editor、rebase-snap 与兼容性 | ◎ |

**36 · 快照总览：文件、版本与 MicrovmState**
- 两个文件：vmstate（`snapshot_path`）与 memfile（`mem_file_path`）；Full / Diff；`track_dirty_pages` 的前提
- `MicrovmState`：`vm_info`、`vm_state`（arch）、`vcpu_states`、`memory_state`（区域描述）、`device_states`、`acpi_dev_state`（x86）；`VmInfo`（mem_size_mib、smt、cpu_template、boot_source、huge_pages）
- `snapshot/mod.rs`：文件头（magic、版本 `SNAPSHOT_VERSION`、`Version` 类型）、bincode 序列化、CRC64 尾（`crc.rs`）；`Snapshot::save()` / `load()`；`--describe-snapshot`
- 版本策略（`docs/snapshotting/versioning.md`）：快照版本与 Firecracker 版本的对应、向后兼容的承诺
- API：`PUT /snapshot/create`、`PUT /snapshot/load`、`PATCH /vm`（Paused / Resumed）；`SnapshotType`
- 安全：快照复用的风险（随机数、网络身份、vsock 连接），后面各篇展开
- 代码：`src/vmm/src/persist.rs`（结构定义部分）、`src/vmm/src/snapshot/`、`src/vmm/src/vmm_config/snapshot.rs`、`docs/snapshotting/snapshot-support.md`
- 图：vmstate 文件布局（```text）；MicrovmState 结构图

**37 · 创建快照：save_state、内存导出与 Diff**
- 前提：Paused；`RuntimeApiController::create_snapshot()` 的检查（Diff 要求 `track_dirty_pages`，确认）
- `create_snapshot()` → `Vmm::save_state()`：`vm.save_state()`（irqchip / GIC）、每个 vCPU `SaveState`、`mmio_device_manager.save()`（第 40 篇）、`memory_state`
- `snapshot_state_to_file()`：写文件、CRC、fsync
- `Vm::snapshot_memory_to_file()`：Full 走 `dump()`，Diff 走 `get_dirty_bitmap()` + `dump_dirty()`（按页写、`seek` 跳过干净页，产物是稀疏文件）；写完后 `reset_dirty_bitmap()` / `reset_dirty()`；「已激活设备的队列重新标脏」
- 内存文件的大小与稀疏：`set_len(expected_size)`；Diff 快照必须与上一个内存文件合并才能用（`rebase-snap`，第 41 篇）
- 代价：暂停时长与脏页数正比；e2b 为什么不满足于此（第 49 篇）
- 代码：`src/vmm/src/persist.rs` 的 `create_snapshot` / `snapshot_state_to_file`、`src/vmm/src/lib.rs` 的 `save_state`、`src/vmm/src/vstate/vm.rs` 的 `snapshot_memory_to_file`、`src/vmm/src/vstate/memory.rs` 的 `dump` / `dump_dirty`
- 图：create 时序（sequenceDiagram：API、VMM、vCPU、Vm、GuestMemory）；Diff 导出 flowchart

**38 · 加载快照：restore、内存后端与设备重建**
- `PUT /snapshot/load`：`LoadSnapshotParams`（`snapshot_path`、`mem_backend` {File | Uffd}、`track_dirty_pages`、`resume_vm`、`network_overrides`）
- `restore_from_snapshot()`：读 vmstate、`snapshot_state_sanity_check()`、CPU 厂商校验、建 guest 内存（`guest_memory_from_file()` mmap 私有映射 / `guest_memory_from_uffd()`）、`build_microvm_from_snapshot()`
- `build_microvm_from_snapshot()`：`create_vmm_and_vcpus`、注册内存、`vm.restore_state()`（irqchip / GIC）、每个 vCPU `restore_state()`、`mmio_device_manager` 从 `DeviceStates` 重建（第 40 篇）、串口、`resume_vm` 时 `kick_devices()`
- 网络覆盖：`network_overrides` 换 tap 名（`docs/snapshotting/network-for-clones.md`）
- 「恢复出来的 VM 是 Paused」：为什么默认不自动 resume
- 与 e2b 的关系：e2b 只用 Uffd 后端 + `resume_vm`（一句话链接）
- 代码：`src/vmm/src/persist.rs` 的 `restore_from_snapshot` 及其下各函数、`src/vmm/src/builder.rs` 的 `build_microvm_from_snapshot`、`src/vmm/src/rpc_interface.rs` 的 `load_snapshot`
- 图：load 时序；两种内存后端对比表

**39 · userfaultfd 后端与缺页处理**
- 问题：mmap 文件后备的内存在恢复后按需从磁盘读，VMM 无法介入；uffd 把缺页交给宿主侧进程
- `MemBackendType::Uffd`：Firecracker 建匿名映射、注册 uffd（`UFFDIO_REGISTER`，MISSING 模式；WP 模式是否用，确认）、把 uffd fd 与 `GuestRegionUffdMapping`（每区域的 base_host_virt_addr / size / offset / page_size）经 Unix socket 发给外部 handler（`send_uffd_handshake()`）
- handler 一侧：`src/firecracker/examples/uffd/`（`on_demand_handler.rs`、`fault_all_handler.rs`、`uffd_utils.rs`）：`UFFDIO_COPY` / `UFFDIO_ZEROPAGE`、balloon 归还页的 `UFFD_EVENT_REMOVE` 处理
- 与大页的关系（HugeTLB 页的 uffd 支持）；性能特征
- e2b 的 uffd handler 在 orchestrator 里（一句话链接 e2b 手册第 31 篇）
- 代码：`src/vmm/src/persist.rs` 的 `guest_memory_from_uffd` / `send_uffd_handshake`、`src/vmm/src/vstate/memory.rs`（uffd 相关）、`src/firecracker/examples/uffd/`、`docs/snapshotting/handling-page-faults-on-snapshot-resume.md`
- 图：握手与缺页时序（sequenceDiagram：Firecracker、handler、内核）；`GuestRegionUffdMapping` 字段表

**40 · 设备状态的 Persist：逐设备的保存与恢复**
- `Persist` trait（`snapshot/persist.rs`）：`type State`、`type ConstructorArgs`、`save()` / `restore()`
- `device_manager/persist.rs`：`DeviceStates`（每类设备一个 Vec，`ConnectedDeviceState` 含 transport 状态 `MmioTransportState`、设备状态、地址与 IRQ 信息）；`save()` 遍历；`restore()` 按原地址与 IRQ 重建并重新注册 ioeventfd / irqfd；`SharedDeviceType`
- `VirtioDeviceState`（`devices/virtio/persist.rs`）：`avail_features` / `acked_features` / `queues`（`QueueState`）/ `interrupt_status` / `activated`
- 逐设备：net（`NetState` 含 `RxBufferState`、tap 重开）、block（`VirtioBlockState` 含文件重开、`FileEngineTypeState`）、vsock（`VsockState`，恢复后发 TRANSPORT_RESET）、balloon、rng、rate limiter（`RateLimiterState`）、mmds（`MmdsState`）、legacy 与 vmgenid 的处理
- 恢复后与恢复前的差异清单：哪些运行时状态不保存（例如正在飞行的 io_uring 请求 —— `drain` 保证为空）
- 这一篇是第 72 篇「回滚的设备状态」的基础
- 代码：`src/vmm/src/snapshot/persist.rs`、`src/vmm/src/device_manager/persist.rs`、`src/vmm/src/devices/virtio/persist.rs`、各设备的 `persist.rs`
- 图：DeviceStates 结构图；保存 / 恢复 flowchart

**41 · snapshot-editor、rebase-snap 与兼容性**
- `rebase-snap`：把 Diff 内存文件合并到 Full 内存文件上（按稀疏文件的 data / hole 段 `lseek(SEEK_DATA)`，确认实现）；多层 Diff 的链式合并
- `snapshot-editor`：`edit-vmstate remove-regs`（aarch64 去掉某些寄存器）、`edit-memory rebase`、`info-vmstate version` / `vcpu-states`
- 兼容性：宿主内核版本、CPU 型号 / 模板、Firecracker 版本；`docs/snapshotting/versioning.md` 的兼容矩阵；跨机器恢复的坑（TSC、CPU 特性、`vmgenid`）
- e2b 不用 rebase-snap（自己在 orchestrator 里做映射表合并），但原理相同 —— 一句话链接
- 代码：`src/rebase-snap/src/main.rs`、`src/snapshot-editor/src/`、`docs/snapshotting/snapshot-editor.md`
- 图：rebase 示意（```text 稀疏文件叠加）；兼容性矩阵表

### 第七部分　安全与可观测

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 42 | `42-seccomp.md` | seccomp：seccompiler、过滤器与安装时机 | ◎ |
| 43 | `43-jailer.md` | jailer：chroot、cgroup 与 namespace | ◎ |
| 44 | `44-logging-and-metrics.md` | 日志与 metrics | ◎ |
| 45 | `45-gdb-tracing-and-kani.md` | GDB 调试、tracing 与形式化验证 | ◎ |

**42 · seccomp：seccompiler、过滤器与安装时机**
- 过滤器源文件：`resources/seccomp/<target>.json`：按线程（`vmm`、`api`、`vcpu`）分三张表，每条 `syscall` + 可选 `args` 条件 + `comment`；`unimplemented.json`
- `seccompiler` crate：JSON → BPF（`compile_from_json`）；`seccompiler-bin` 工具；构建时 `build.rs` 把编译好的 BPF 内嵌进二进制（`src/firecracker/build.rs`，确认）
- 安装时机：VMM 线程在进入事件循环前、API 线程启动时、每个 vCPU 线程在 `run()` 开头；`--seccomp-filter` / `--no-seccomp`；违规时 SIGSYS → `signal_handler.rs` 记录 metrics 后退出
- 怎么读一张过滤器表：以 vmm 线程的 `ioctl` 条件（KVM ioctl 白名单）为例
- 三层改动都碰过这个文件（e2b 加 `mincore` / `pread64`，checkpoint 加 vcpu ioctl 白名单 —— 第 55、62、73 篇）
- 代码：`resources/seccomp/`、`src/seccompiler/src/`、`src/firecracker/src/seccomp.rs`、`src/vmm/src/seccomp.rs`、`docs/seccomp.md`、`docs/seccompiler.md`
- 图：编译与安装流程 flowchart；三线程过滤器规模表

**43 · jailer：chroot、cgroup 与 namespace**
- jailer 做什么：以 root 起、建 chroot（`--chroot-base-dir/<exec_file_name>/<id>/root`）、拷贝 / 硬链接可执行文件、挂载 / dev 节点（`/dev/kvm`、`/dev/net/tun`）、cgroup（v1 / v2，`--cgroup`）、`--netns`、pid namespace（`--new-pid-ns`）、`--daemonize`、资源限制（`--resource-limit`）、切换 uid / gid、`exec` Firecracker（`--`  之后的参数透传）
- `Env::run()` 的顺序与每步的原因；`cgroup.rs` 的两版实现；`chroot.rs` 的 `pivot_root`
- e2b 不用 jailer（自己用 netns + 进程管理）—— 说明什么安全属性由谁提供（一句话链接 e2b 手册第 28 篇）
- 代码：`src/jailer/src/`（全部）、`docs/jailer.md`
- 图：jailer 步骤 flowchart；参数表

**44 · 日志与 metrics**
- `logger/logging.rs`：`Logger`（`log` crate 后端）、级别、`--log-path` / `--level` / `--show-level` / `--show-log-origin`、模块过滤（确认）
- `logger/metrics.rs`：`METRICS` 全局结构（每个子系统一个结构体：`api_server`、`block`、`net`、`vcpu`、`vmm`、`latencies_us`、`seccomp`…）、`IncMetric` / `StoreMetric` / `SharedIncMetric` 的实现（原子计数 + 上次 flush 值）、`FlushMetrics` 动作与定时 flush、JSON 输出格式
- 每设备 metrics（`block/virtio/metrics.rs`、`net/metrics.rs` 按设备 id 分组）
- `latencies_us`：`vmm_pause_vm`、`vmm_resume_vm`、`vmm_full_create_snapshot`、`vmm_diff_create_snapshot`、`vmm_load_snapshot` 等 —— e2b 与 ARM 适配版都靠这些看时延
- 代码：`src/vmm/src/logger/`、`src/firecracker/src/metrics.rs`、`docs/logger.md`、`docs/metrics.md`
- 图：metrics 结构树（```text）；关键 latencies 表

**45 · GDB 调试、tracing 与形式化验证**
- gdb 特性（`--features gdb`）：`gdb/target.rs` 实现 `gdbstub` 的 `Target`（断点、单步、读写寄存器 / 内存）、`gdb/arch/`、`event_loop.rs`；`KVM_SET_GUEST_DEBUG`；`docs/gdb-debugging.md`
- tracing 特性：`log-instrument` 过程宏在每个函数入口 / 出口打日志；`clippy-tracing` 工具批量加 / 去 `#[instrument]`；`docs/tracing.md`
- Kani：`#[cfg(kani)]` 证明 harness（queue、iovec、rate_limiter、ethernet pdu、arch）；`tests/integration_tests/test_kani.py`；证明的是什么、不证明什么；`docs/formal-verification.md`
- 代码：`src/vmm/src/gdb/`、`src/log-instrument/`、`src/clippy-tracing/`、`src/vmm/src/devices/virtio/queue.rs` 的 kani 模块
- 图：三种工具的适用场景对比表

### 第八部分　工程

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 46 | `46-code-organization-and-build.md` | 代码组织、依赖与构建 | ◎ |
| 47 | `47-testing.md` | 测试体系：单元、集成与性能 | ◎ |
| 48 | `48-release-and-compat-policy.md` | 发布策略、版本与兼容承诺 | ◎ |

**46 · 代码组织、依赖与构建**
- workspace 成员与 `default-members`（jailer 为什么不在默认里：musl 静态链接）；每个 crate 的职责与依赖方向
- `vmm` crate 的模块树（与本书篇目的映射：附录第 75 篇给全表，这里给主干）
- 构建目标 `x86_64-unknown-linux-musl` / `aarch64-unknown-linux-musl`；`rust-toolchain.toml`；`profile.release`（lto、panic=abort）
- 生成代码（`bindgen`）的管理；`deny.toml`（cargo-deny）；`.buildkite` / GitHub Actions（只概述）
- 代码：`Cargo.toml`、`src/*/Cargo.toml`、`tools/devtool`、`tools/bindgen.sh`
- 图：crate 依赖图；模块树（```text）

**47 · 测试体系：单元、集成与性能**
- 单元测试：内联 `mod tests`、`test_utils/`（mock 内核、`default_vmm()`）、`src/vmm/tests/integration_tests.rs`（进程内起真 VM）
- 集成测试（pytest）：`tests/framework/`（`microvm.py` 的 `Microvm` 类、`artifacts.py` 拉内核 / rootfs、`http_api.py`、`jailer.py`、`state_machine.py`）；`tests/integration_tests/{build,functional,security,performance,style}` 各讲一段，列关键用例（`test_snapshot_basic.py`、`test_pause_resume.py`、`test_dirty_pages_in_full_snapshot.py`、`test_seccomp.py`、`test_jail.py`、`test_snapshot_ab.py`）
- A/B 性能测试（`tools/ab_test.py`、`framework/ab_test.py`）：怎么比较两个提交
- e2b 定制版对测试的改动（`test_api.py` 加了 memory 端点用例、`test_shut_down.py` 删断言、`tools/test.sh` 限制用例）在第 55 篇
- 本项目在 aarch64 上能跑哪些（无 devtool 容器时怎么跑单元测试）—— 如实说明限制
- 代码：`tests/`、`tools/test.sh`、`tools/ab_test.py`
- 图：测试层次表；`Microvm` 测试夹具的生命周期 flowchart

**48 · 发布策略、版本与兼容承诺**
- `docs/RELEASE_POLICY.md`：主要 / 次要版本的支持期、补丁版本；`docs/kernel-policy.md`：支持的宿主与 guest 内核版本
- API 兼容：`docs/api-change-runbook.md`；swagger 版本号与二进制版本
- 快照兼容承诺（回顾第 41 篇）
- `CHANGELOG.md` 里 v1.12.x 的要点：v1.12.1 相对 v1.12.0 修了什么（读 CHANGELOG）；v1.13 / v1.14 新增了什么（只列与本项目相关的：PCI、`--enable-pci`、内存热插？确认）—— 给「升级到新版要重做哪些定制」的判断依据
- 工具：`tools/release*.sh`、`tools/bump-version.sh`、`tools/gh_release.py`
- 代码：`docs/RELEASE_POLICY.md`、`docs/kernel-policy.md`、`CHANGELOG.md`、`tools/release.sh`
- 图：版本支持时间线表

### 第九部分　e2b 定制版

这一部分讲 e2b-dev/firecracker 分支 `firecracker-v1.12-direct-mem` 的 `a41d3fb` 相对上游 v1.12.1 的全部改动，
以及 e2b 为 Firecracker 准备的 guest 内核配置。每篇都要回答：上游为什么没有、e2b 为什么需要、改在哪、谁调用、代价。
调用方的代码在 `tmp/e2b-book-src/upstream/packages/orchestrator/internal/sandbox/fc/`（只读，不讲）。

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 49 | `49-why-e2b-forked.md` | 为什么分叉：e2b 的内存管线要什么 | ◎ |
| 50 | `50-memory-mappings-api.md` | /memory/mappings：把 guest 内存的宿主地址交出去 | ◎ |
| 51 | `51-memory-resident-empty-api.md` | /memory：常驻页与零页位图 | ◎ |
| 52 | `52-memory-dirty-api.md` | /memory/dirty：pagemap 与写保护位的脏页判据 | ◎ |
| 53 | `53-uffd-write-protection.md` | uffd 写保护：让脏页判据成立的最后一环 | ◎ |
| 54 | `54-optional-memfile-snapshot.md` | 可选 memfile 的快照与 e2b 的暂停流程 | ◎ |
| 55 | `55-seccomp-build-upload-and-upstream-fixes.md` | seccomp、构建发布脚本与合入的上游修复 | ◎ |
| 56 | `56-guest-kernel-requirements-and-e2b-configs.md` | guest 内核：Firecracker 的要求与 e2b 的内核配置 | ◎ |

**49 · 为什么分叉：e2b 的内存管线要什么**
- e2b 的循环：模板快照 → uffd 恢复 → 运行 → 暂停成新快照（只讲到能理解需求的程度，延伸阅读链接 e2b 手册第 12、37 篇）
- 上游 create snapshot 的三个不合适：Diff 快照必须落盘成稀疏文件、脏页判据只有 KVM 日志、宿主进程拿不到 guest 内存的 HVA 因此无法跨进程直读
- e2b 的方案：三个只读端点 + 可选 memfile + uffd 写保护：orchestrator 通过 `/proc/<pid>/mem` 直读 guest 内存，自己决定哪些页要导出（resident、非零、dirty 三张位图的交集）
- 28 个提交的分组：功能提交（`03e506146` 暴露映射 + 可选 memfile、`54a1c1ad3` dirty memory API、`8fc760f61` uffd 写保护）、修修补补（编译错误、spec 字段、版本）、合入上游 v1.12 分支、CI 与脚本；分组表
- 版本名 `v1.12.1_a41d3fb` 怎么来的（`scripts/build.sh`）、infra 2026.09 在哪里钉它（`flags.go` 的 `DefaultFirecackerV1_12Version`），以及同一文件里的 `v1.10.1_30cbb07` 是什么（`firecracker-v1.10-direct-mem` 分支，本书不讲）
- 改动清单表（文件、+/- 行、所属篇）
- 代码：`git -C tmp/e2b-book-src/fc-e2b log --stat v1.12.1..a41d3fb`、`tmp/e2b-book-src/upstream/packages/shared/pkg/feature-flags/flags.go`
- 图：e2b 内存管线中 Firecracker 的位置（flowchart）；改动分布表

**50 · /memory/mappings：把 guest 内存的宿主地址交出去**
- `GuestMemoryRegionMapping` {base_host_virt_addr, size, offset, page_size}；`Vm::guest_memory_mappings()`：遍历区域，`offset` 是各区域在「扁平内存文件」里的偏移
- `InstanceInfo.memory_regions` 字段（`Option`，何时填，确认：`GET /` 是否返回）
- API：`GET /memory/mappings` → `VmmAction::GetMemoryMappings` → `VmmData::MemoryMappings`；只允许运行后（Preboot 返回 `OperationNotSupportedPreBoot`）
- 安全含义：把 HVA 交给了外部进程；这只在「orchestrator 与 Firecracker 同信任域」下成立；seccomp 没变
- 调用方怎么用：orchestrator 用 `process_vm_readv` 还是 `/proc/pid/mem`（读 `fc/memory.go` 确认，一句话）
- 代码：`src/vmm/src/vstate/vm.rs`（`GuestMemoryRegionMapping`、`guest_memory_mappings`）、`src/vmm/src/rpc_interface.rs`、`src/firecracker/src/api_server/request/memory.rs`、`src/firecracker/swagger/firecracker.yaml`
- 图：区域 → 映射 → 扁平偏移示意（```text）；请求处理时序

**51 · /memory：常驻页与零页位图**
- `Vm::get_memory_info()`：对每个区域 `mincore()` 得到宿主页粒度的常驻向量；按 guest 页粒度（`page_size` 来自 `huge_pages`）折算 resident 位；对常驻页 `memcmp` 全零判 empty；两张 `Vec<u64>` 位图按扁平页序
- 为什么要这两张图：uffd 恢复的 VM 里大部分页从未被触碰（不常驻），常驻但全零的页也不必导出 —— 导出量从内存大小降到工作集
- 代价：`memcmp` 每页一次的 CPU 开销、只能在 Paused 下有意义（代码是否强制，确认）、大页时 `mincore` 的粒度问题
- `mincore_bitmap()` 独立函数（给 `/memory/dirty` 复用）
- seccomp：`mincore` 进白名单
- 代码：`src/vmm/src/vstate/vm.rs` 的 `get_memory_info` / `mincore_bitmap`、`src/vmm/src/vmm_config/instance_info.rs` 的 `MemoryResponse`
- 图：位图计算 flowchart；`unsafe` 块里的边界处理说明表

**52 · /memory/dirty：pagemap 与写保护位的脏页判据**
- `utils/pagemap.rs`：读 `/proc/self/pagemap`，每页 8 字节：bit 63 present、bit 57 「write-protected」（uffd-wp）；`is_page_dirty = present && !wp`
- `Vmm::get_dirty_memory()`：先 `mincore` 过滤常驻页，再逐页 `pread` pagemap；只允许 Paused（`OperationNotSupportedWhileRunning`）
- 判据的含义：页被 uffd 写保护，guest 第一次写时内核（异步模式）清掉写保护位 —— 所以「present 且不再 WP」= 被写过；写保护是谁、何时加上的：第 53 篇
- 与 KVM 脏页日志的对比表（谁维护、粒度、清零语义、开销）
- 代价：每页一次 `pread`，8 GiB 内存 200 万次系统调用的量级（只说数量级，不给测量数）；`info!` 打印耗时
- seccomp：`pread64` 进白名单（x86 表里；aarch64 表在 ARM 适配版才补 —— 第 62 篇）
- ARM 适配版为什么另引入 HDBSS（点到第 65 篇）
- 代码：`src/vmm/src/utils/pagemap.rs`、`src/vmm/src/lib.rs` 的 `get_dirty_memory`、`src/vmm/src/rpc_interface.rs` 的 `get_dirty_memory_info`
- 图：pagemap 条目位布局（```text）；三种脏页判据对比表

**53 · uffd 写保护：让脏页判据成立的最后一环**
- 提交 `8fc760f61`：`userfaultfd` crate 换成 e2b 分叉（分支 `feat_write_protection`，特性 `linux5_7` / `linux5_13` / `linux6_7`）；`guest_memory_from_uffd()` 请求 `EVENT_REMOVE | MISSING_HUGETLBFS | WP_ASYNC`、以 `MISSING | WRITE_PROTECT` 注册每个区域、大页时立刻 `write_protect()` 整个区域；匿名内存为什么不能在这里加保护（首次缺页会清掉 WP 位，要由 uffd handler 在 `UFFDIO_COPY` 时带 WP 模式 —— 这是 orchestrator 侧的事，一句话链接 e2b 手册第 31 篇）
- 同步与异步写保护的区别（内核文档）；异步模式要求宿主内核 6.7+；这就是 e2b 生产环境的内核前提
- 这个提交与第 52 篇判据的关系：没有它，pagemap 的 WP 位永远是 0，`/memory/dirty` 会把所有常驻页都算成脏
- 分叉自己的另一个分支 `firecracker-v1.12-direct-mem-arm64-uffd-fix`（`136ef0e01`）：把三处写保护代码用 `cfg(target_arch = "x86_64")` 关掉，因为 arm64 内核没有 uffd 写保护（`UFFD_FEATURE_WP_ASYNC`、`UFFDIO_REGISTER_MODE_WP`、`UFFDIO_WRITEPROTECT`）；这是第 57 篇的伏笔，这里只点到
- `lib.rs` 里那段 TODO 注释：有了 WP 事件其实可以不读 pagemap —— 说明设计还在演进
- 代码：`git -C tmp/e2b-book-src/fc-e2b show 8fc760f61`、`src/vmm/src/persist.rs` 的 `guest_memory_from_uffd`、`src/vmm/Cargo.toml`；对照 `git show 136ef0e01`
- 图：注册 / 写保护 / 首次写 / 读 pagemap 的时序（sequenceDiagram：Firecracker、内核、handler、orchestrator）；特性与内核版本要求表

**54 · 可选 memfile 的快照与 e2b 的暂停流程**
- `CreateSnapshotParams.mem_file_path` 改为 `Option`；swagger 去掉 required；`create_snapshot()` 里只有给了路径才 `snapshot_memory_to_file()`
- 没有 memfile 的 create 还做什么：写 vmstate、队列重新标脏；Diff 类型此时是否还读 KVM 日志（确认：`snapshot_memory_to_file` 不调用则 `get_dirty_bitmap` 也不调用，KVM 日志不清零 —— 这个副作用要写清）
- e2b 的完整暂停流程（从 Firecracker 视角）：`PATCH /vm Paused` → `GET /memory/mappings` → `GET /memory` → `GET /memory/dirty` → `PUT /snapshot/create`（无 memfile）→ orchestrator 直读页 → 杀进程；时序图
- 代价与限制：vmstate 与内存不再由同一个 `create` 原子产生；`track_dirty_pages` 是否还需要
- 测试改动：`test_api.py` 的新增用例
- 代码：`src/vmm/src/vmm_config/snapshot.rs`、`src/vmm/src/persist.rs`、`tests/integration_tests/functional/test_api.py`、e2b infra 的 `fc/memory.go`（只看调用顺序）
- 图：e2b 暂停时序（sequenceDiagram，≤6 参与者）；参数对比表

**55 · seccomp、构建发布脚本与合入的上游修复**
- seccomp：x86 表加 `mincore` + `pread64`、aarch64 表只加 `mincore`（为什么不对称：分叉只在 x86 上跑）；格式整理
- `scripts/build.sh`：版本名 `v<swagger 版本>_<7 位 hash>`、`tools/devtool -y build --release`、产物路径写死 x86_64；`scripts/upload.sh`：`gsutil` 传到 `<project>-fc-versions` 桶与 public builds；`Makefile`；`.tool-versions`
- `tools/test.sh` 限制测试集、`test_shut_down.py` 去掉线程数断言、CI runner 改动、删掉 dependency changes 检查：说明分叉的维护姿态（够用即可）
- 来自上游 v1.12 分支的提交：`fix: update AMD host cpu features checks`、`fix: add MSR_TSC_RATE to the MSR_EXCEPTION_LIST`、`chore: Add ibpb_exit_to_user as host only feature`、Spectre 检查 URL、`test_reboot` 断言；各自修了什么、对 aarch64 是否有影响；怎么确认某个提交是上游的（`git log upstream/firecracker-v1.12`）
- 分叉的后续：a41d3fb 之后的三个提交（swagger 文档、kvmclock 修复 `210cbac`）、`firecracker-v1.13` / `firecracker-v1.14-direct-mem` 分支；对本项目的含义：升级时要重放的改动清单（第 78 篇差异总表的用法）
- e2b infra 侧怎么消费版本名（`FirecrackerVersionsDir`、`fc-versions` 桶）—— 一句话
- 代码：`resources/seccomp/*.json`（diff）、`scripts/`、`Makefile`、`tools/test.sh`、`git -C tmp/e2b-book-src/fc-e2b log --format='%h %an %s' v1.12.1..a41d3fb`
- 图：构建 → 上传 → 节点拉取的流程图；提交来源分类表

**56 · guest 内核：Firecracker 的要求与 e2b 的内核配置**
- Firecracker 对 guest 内核的要求：`docs/rootfs-and-kernel-setup.md`、`docs/kernel-policy.md`；上游自带的 CI config `resources/guest_configs/microvm-kernel-ci-{x86_64,aarch64}-6.1.config` 与 `resources/rebuild.sh`；必需项（virtio-mmio、serial、PVH / EFI stub、ACPI 或 FDT、initrd、`virtio_mmio.device=` 命令行）
- e2b-dev/fc-kernels 仓库（release `v0.0.8`，infra 2026.09 对应）：`kernel_versions.txt`（6.1.102、6.1.158）、`configs/{x86_64,arm64}/<版本>.config`、`build.sh`（从 kernel.org 取源码、`make vmlinux`、产物命名）、`Makefile`、GitHub Actions 发布到 release 与 GCS
- e2b 的 x86_64 config 相对 Firecracker CI config 的差异（约 64 行，按类归纳：overlayfs / ext4 / xfs、cgroup / namespace、landlock、nfs v3、wireguard、网络 / 调度选项）；arm64 config 相对 aarch64 CI config 的差异（约 41 行）
- 没有源码补丁：这一层的「定制」只有配置；后来（v0.0.8 之后）加的 balloon wait-ACK 补丁不在 2026.09 范围，只提一句
- e2b infra 怎么选内核：`DefaultKernelVersion = "vmlinux-6.1.158"`（`packages/api/internal/cfg/model.go`）、`/fc-kernels/<版本>/vmlinux.bin`、内核命令行由 orchestrator 拼（`fc/kernel_args.go`，一句话，第 63 篇展开）
- 本篇不讲内核源码
- 代码：`tmp/e2b-book-src/fc-upstream/resources/guest_configs/`、`docs/rootfs-and-kernel-setup.md`、e2b-dev/fc-kernels `v0.0.8`（`gh release view v0.0.8 -R e2b-dev/fc-kernels`；文件用 `gh api repos/e2b-dev/fc-kernels/contents/<path>?ref=b8cea06` 或 clone 到 `tmp/e2b-book-src/fc-kernels/` 后 checkout `b8cea06`）
- 图：构建与发布流程 flowchart；config 差异分类表

### 第十部分　ARM 适配版

这一部分讲 KASandbox `firecracker/` 目录（`jll` 分支 `3863c76`）相对 e2b 定制版的全部内容，分两段：
前 7 篇是「让它在鲲鹏 / openEuler 上跑起来」（迁入的版本与放弃的写保护、构建、aarch64 代码路径、宿主环境、内核、seccomp、与 infra 对接），
后 10 篇是本项目为 checkpoint / restore 加的扩展（HDBSS 脏页跟踪、脏位图 sidecar、save-dirty-bitmap、原地回滚）。
每篇都要区分「上游本来就支持 aarch64 的部分」「同事做的部分」与「本项目做的部分」，但按 STYLE 不写人名。
设计动机、orchestrator 侧的账本 / 差分树 / 磁盘分层、测试与性能在 checkpoint / restore 手册里，只在延伸阅读里链接。

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 57 | `57-which-fork-commit-and-uffd-wp.md` | 迁入的版本：54a1c1a 与被放弃的 uffd 写保护 | ◎ |
| 58 | `58-building-and-running-on-aarch64.md` | 在 aarch64 上构建与运行 | ◎ |
| 59 | `59-aarch64-vs-x86-64-runtime-paths.md` | aarch64 与 x86_64 运行路径的差异清单 | ◎ |
| 60 | `60-kunpeng-openeuler-host.md` | 鲲鹏 950 与 openEuler 宿主环境 | ◎ |
| 61 | `61-guest-kernel-on-arm.md` | ARM 上的 guest 内核：arm64 配置与部署中的内核文件 | ◎ |
| 62 | `62-aarch64-seccomp-filter.md` | aarch64 的 seccomp 过滤器 | ◎ |
| 63 | `63-integration-with-e2b-infra.md` | 与 e2b infra 的对接：版本目录、内核参数与 RPM | ◎ |
| 64 | `64-checkpoint-extension-overview.md` | checkpoint / restore 扩展总览：目标、四个扩展点与分工 | ◎ |
| 65 | `65-dirty-tracking-backend.md` | 脏页跟踪后端：KVM 写保护与 HDBSS | ◎ |
| 66 | `66-hdbss.md` | HDBSS：鲲鹏硬件脏页跟踪与 KVM 能力 | ◎ |
| 67 | `67-dirty-bitmap-sidecar.md` | dirty_bitmap_path：sidecar 与 FCDB 格式 | ◎ |
| 68 | `68-save-dirty-bitmap-api.md` | PUT /snapshot/save-dirty-bitmap | ◎ |
| 69 | `69-rollback-api-and-phases.md` | PUT /snapshot/rollback：阶段、参数与响应 | ◎ |
| 70 | `70-rollback-memory.md` | 回滚的内存写回 | ◎ |
| 71 | `71-rollback-vcpu-and-gic.md` | 回滚的 vCPU 与 GIC | ◎ |
| 72 | `72-rollback-devices.md` | 回滚的设备状态 | ◎ |
| 73 | `73-failure-model-faulted-and-seccomp.md` | 失败模型、Faulted 状态与 seccomp 白名单 | ◎ |

**57 · 迁入的版本：54a1c1a 与被放弃的 uffd 写保护**
- KASandbox 把 e2b 分叉整目录放进 `firecracker/`（没有 git 历史）；怎么核对它是哪个提交：与 `54a1c1a` 的树 `diff -r` 只差三个测试用二进制
- 54a1c1a 与 infra 2026.09 钉的 a41d3fb 差两个提交：`8fc760f61` uffd 写保护（第 53 篇）与一个 CI 文件；源码上只差写保护那一处
- 为什么 arm64 上不能带写保护：arm64 内核没有 `UFFD_FEATURE_WP_ASYNC` / `UFFDIO_REGISTER_MODE_WP` / `UFFDIO_WRITEPROTECT`，`guest_memory_from_uffd()` 的 `require_features` 或 `register_with_mode` 会失败，快照恢复直接报错；e2b 自己的 `firecracker-v1.12-direct-mem-arm64-uffd-fix` 分支（`136ef0e01`）用 `cfg(x86_64)` 关掉三处，作为对照；ARM 适配版选 54a1c1a 是等价的做法（推论：迁入时是否有意为之，标推论）
- 后果：aarch64 上 `/memory/dirty` 的 pagemap 判据失去写保护位的支撑（present 且 WP 位恒为 0 → 所有常驻页都算脏）；orchestrator 侧的 ARM 补丁怎么应对（`FC_TRACK_DIRTY_PAGES=true` 与 KVM 日志路线，一句话链接 e2b 手册第 37 篇）；这也是后面引入 HDBSS 的动机之一（第 65 篇）
- `Cargo.lock` / `userfaultfd` 依赖回到上游 crate 的含义
- 代码：`git -C tmp/e2b-book-src/fc-e2b diff 54a1c1a a41d3fb`、`git -C tmp/e2b-book-src/fc-e2b show 136ef0e01`、`tmp/e2b-book-src/kasandbox-arm/firecracker/src/vmm/src/persist.rs`
- 图：三个版本（54a1c1a / a41d3fb / arm64-uffd-fix）在写保护上的差异表；uffd 注册流程对照 flowchart

**58 · 在 aarch64 上构建与运行**
- `scripts/build.sh` 的改动：按 `uname -m` 选 target 目录；devtool 容器在 aarch64 上的可用性（`fcuvm` 镜像有 arm64 版？确认 `tools/devtool` 怎么选镜像）；无容器时用本机 cargo + `aarch64-unknown-linux-musl` 的条件
- `main.rs` 的改动：`resize_fdtable()` 整段注释掉 —— 它做什么（把 fd 表预扩到 rlimit 上限，减少恢复时的 fd 表扩容）、在 openEuler 24.03 上为什么 coredump（提交信息只说 coredump in 2403；原因标推论）、后果（快照恢复时 fd 表按需增长，性能影响的量级）
- 构建产物 `firecracker.arm` 怎么进 e2b-infra 的 RPM（`Source8`）、装到 `/fc-versions/v1.13.1/`（点到第 63 篇）
- 跑起来需要的宿主条件：`/dev/kvm`、GICv3、内核版本、页大小（4 KiB 内核 vs 64 KiB 内核对 Firecracker 的影响：`host_page_size()` 的使用处）
- 代码：`git -C KASandbox diff 9e880db b8e85c3 -- firecracker`、`tools/devtool`（镜像选择）、`src/firecracker/src/main.rs`、`e2b-infra/e2b-infra.spec`
- 图：构建流程（aarch64 版）；改动表

**59 · aarch64 与 x86_64 运行路径的差异清单**
- 以「一台 microVM 的生命周期」为线索，逐阶段列出两架构走的不同代码：内存布局、vCPU 创建与配置、引导（FDT vs boot params / ACPI）、中断（GIC vs irqchip / PIT / IOAPIC）、legacy 设备（RTC vs i8042 / PIO 串口）、vmgenid 的接入方式、`KVM_EXIT_SYSTEM_EVENT` vs `Hlt` / `Shutdown`、快照里的 `VmState` 内容、CPU 模板、gdb 支持、seccomp 表、uffd 写保护（第 57 篇）
- 每项给代码位置（`#[cfg(target_arch = …)]` 的分叉点）
- 上游对 aarch64 的功能限制清单（从 `docs/` 与 CHANGELOG 里找：不支持的特性）
- 这一篇是给读完第三部分的读者做「aarch64 索引」用的，可以多用表
- 代码：`grep -rn 'target_arch' src/vmm/src`、第三部分各篇引用的文件
- 图：生命周期各阶段两架构对照表（主体）；`cfg` 分叉点分布图

**60 · 鲲鹏 950 与 openEuler 宿主环境**
- 宿主：鲲鹏 950（架构代际，确认）、openEuler 24.03、内核 6.6.0-515（HDBSS 支持的内核 —— 点到第 66 篇）；KVM 相关能力：`KVM_CAP_ARM_*`、GICv3 / ITS、SVE、`KVM_CAP_ARM_HW_DIRTY_STATE_TRACK`（502，非主线）
- Firecracker 在这台机器上的检查项：`KvmVcpu` 的 `KVM_ARM_PREFERRED_TARGET`、`cache_info.rs` 读 sysfs 的路径是否存在、`enable_ssbd_mitigation()` 的 prctl 在此内核的行为
- 页大小：openEuler 内核默认页大小与 HugeTLB；Firecracker 的 `host_page_size()` 与 `HugePageConfig`；uffd 在 arm64 上可用的部分（MISSING 模式、`MISSING_HUGETLBFS`）与不可用的部分（写保护）
- 与 x86 云主机的对照：没有 ACPI 表这一套的影响、没有 CPU 模板可用
- 相关文档：仓库根的 `HDBSS_KUNPENG950_KERNEL_6.6.0_515.md`（只作为背景，以代码与内核文档为准；其中的性能数字不引用）
- 代码：`src/vmm/src/arch/aarch64/`（能力检查处）、`src/vmm/src/arch/aarch64/kvm.rs`
- 图：宿主软硬件栈图；能力检查表

**61 · ARM 上的 guest 内核：arm64 配置与部署中的内核文件**
- 回顾第 56 篇：fc-kernels 的 arm64 支持是 e2b 自己加的（`b8cea06`，v0.0.8）；本项目对内核**零改动**
- arm64 config 相对 x86_64 config 的差异按类归纳（架构选项、PSCI、GIC、串口 `SERIAL_AMBA_PL011`、RTC PL031、virtio、文件系统、cgroup / namespace）；产物是 PE 格式的 `Image` 还是 ELF `vmlinux`（读 `build.sh` 与提交 `7fa4f34` 确认；Firecracker aarch64 的 `load_kernel()` 要什么格式）
- 部署里的内核文件：`e2b-infra/vmlinux.bin.arm` 是 fc-kernels release `v0.0.12`（2026-04-10 构建，`strings` 里的 `Linux version 6.1.158 … aarch64-linux-gnu-gcc`）；v0.0.8 → v0.0.12 只改了脚本、config 未动；`init-client.sh` 把它铺到 `/fc-kernels/vmlinux-6.1.158/` 与 `/fc-kernels/vmlinux-6.1.102/`（兼容旧模板）；RPM 里另有一个 openEuler 6.6.0 变体只提一句「存在、备用、本书不讲」
- 内核命令行在 aarch64 上的差异（`fc/kernel_args.go` 是否按架构分支，确认；`console=ttyS0` vs `ttyAMA0`）
- 本篇不讲内核源码
- 代码：e2b-dev/fc-kernels `v0.0.8` / `v0.0.12`（`gh release view`）、`e2b-infra/e2b-infra.spec`、`e2b-infra/e2b-deploy/dep/init-client.sh`、`tmp/e2b-book-src/arm/packages/orchestrator/internal/sandbox/fc/kernel_args.go`
- 图：内核文件从 release 到 `/fc-kernels/` 的流向（flowchart）；arm64 与 x86_64 config 差异分类表

**62 · aarch64 的 seccomp 过滤器**
- `resources/seccomp/aarch64-unknown-linux-musl.json` 与 x86 表的结构差异（没有 PIO 相关、有 GIC 的 `KVM_DEV_*` ioctl 等）
- e2b 定制版只给 aarch64 加了 `mincore`；ARM 适配版补了 `pread64` 与四个 vcpu ioctl（`KVM_SET_ONE_REG`、`KVM_SET_MP_STATE`、`KVM_ARM_VCPU_INIT`、`KVM_ARM_VCPU_FINALIZE`）（第 73 篇细讲）；「放行 vmm 线程的 pread64」的来龙去脉：`/memory/dirty` 在 aarch64 上第一次调用就 SIGSYS（`FcExitCode::BadSyscall`），而 ARM 单机版建模板必走这条路
- 怎么验证一张过滤器表：`seccompiler-bin` 编译、`--seccomp-filter` 加载、跑一遍 API 看 `seccomp.num_faults` metrics 与 `dmesg`
- 怎么加一条规则：格式、`args` 条件写法、注释规范
- 代码：`resources/seccomp/aarch64-unknown-linux-musl.json`（两层 diff）、`src/vmm/src/signal_handler.rs`、e2b-infra 提交 `8266156` 的说明
- 图：各层对该文件的改动表；规则条目格式（```json）

**63 · 与 e2b infra 的对接：版本目录、内核参数与 RPM**
- orchestrator 怎么起 Firecracker：`fc/process.go`（命令行：`--api-sock`、seccomp？、netns 里 `ip netns exec`）、`fc/config.go`（`/fc-versions/<版本>/firecracker`、`/fc-kernels/<版本>/vmlinux.bin`）、`fc/kernel_args.go`（内核命令行：console、reboot、panic、pci=off、`virtio_mmio` 参数由 Firecracker 加）、`fc/client.go`（用哪些 API）、`fc/mmds.go`
- ARM 单机版：`e2b-infra.spec` 的 `Source8: firecracker.arm` → `/opt/e2b-infra/bin/firecracker` → `init-client.sh` 拷进 `/fc-versions/v1.13.1/`；「源码 1.12.1 装成 v1.13.1」的原因（e2b 手册第 70 篇已讲，这里只回顾 + 链接）
- 版本名怎么进数据库 / 模板（`FirecrackerVersion` 字段）
- Firecracker 侧看到的完整 API 调用序列（创建 / 恢复 / 暂停 / checkpoint）：作为第九部分与后面 10 篇的调用背景
- XFS + reflink 路线（KASandbox `jll-xfs`、e2b-infra `xfs-reflink` 分支）：Firecracker 侧只少 `save-dirty-bitmap` 端点，其余相同，一句话
- 代码：`tmp/e2b-book-src/arm/packages/orchestrator/internal/sandbox/fc/`、`e2b-infra/e2b-infra.spec`、`e2b-infra/e2b-deploy/dep/init-client.sh`
- 图：文件与目录布局（```text）；调用序列表

**64 · checkpoint / restore 扩展总览：目标、四个扩展点与分工**
- 目标：高频 checkpoint 与快速 restore —— 暂停的成本正比于脏页、恢复不重建进程；上游「杀进程 + 从快照重建」的成本构成（进程 / KVM / vCPU / GIC / 设备重建 + 工作集回填）—— `rollback.rs` 文件头的注释是很好的起点，但用自己的话讲
- 四个扩展点：（1）脏页跟踪后端可选 HDBSS；（2）`create` 时可写脏位图 sidecar；（3）`PUT /snapshot/save-dirty-bitmap`；（4）`PUT /snapshot/rollback` 原地回滚；外加 `Faulted` 状态与 `dirty_tracking` 能力上报
- 提交分组（`git -C KASandbox log b8e85c3..3863c76 -- firecracker`）：HDBSS 使能与硬化、sidecar 与 seccomp、回滚主体、RX 缓存修复、诊断日志、vCPU 路线收敛、seccomp pread64；改动清单表（文件、行数、篇）
- 与 e2b 定制版三个只读端点的关系：仍然保留，orchestrator 在哪种模式用哪套（只点到，链接 checkpoint 手册第 09 篇）
- 与 orchestrator 的分工：Firecracker 提供原语，账本 / 差分树 / 回滚决策在 orchestrator
- 代码：`git -C KASandbox diff --stat b8e85c3 3863c76 -- firecracker`、`src/vmm/src/rollback.rs` 文件头
- 图：四个扩展点在快照生命周期中的位置（flowchart）；改动表

**65 · 脏页跟踪后端：KVM 写保护与 HDBSS**
- `DirtyTrackingBackend` {Off, KvmWriteProtect, Hdbss} 与 `VmCommon.dirty_tracking`；`as_str()` 用于能力上报（`InstanceInfo.dirty_tracking`，`GET /` 可见）
- `Vm::setup_dirty_tracking()`：只有 `track_dirty_pages` 打开（区域带位图）才「armed」；aarch64 上尝试 `enable_hdbss(order)`，失败则回退 KVM 写保护，`FC_HDBSS_REQUIRED` 时失败即报 `HdbssRequired`；x86 固定 KVM 写保护；环境变量 `FC_HDBSS_ORDER`（默认 1）—— 为什么用环境变量而不是 API 字段（如实说明这是权宜，代价是不可观测、不可按 VM 配置）
- 调用点：`build_microvm_for_boot()` 与 `build_microvm_from_snapshot()` 在 `register_memory_regions` 之后
- 与上游 `KVM_MEM_LOG_DIRTY_PAGES` 的关系：HDBSS 是同一份 KVM 脏页日志的另一种硬件采集方式，`get_dirty_bitmap()` 的调用方式不变（加了一行耗时日志）
- 与第 57 篇的关系：aarch64 没有 uffd 写保护，pagemap 判据不可用，所以脏页判据回到 KVM 日志一侧，HDBSS 让这一侧的开销可接受
- 代码：`src/vmm/src/vstate/vm.rs`（`DirtyTrackingBackend`、`setup_dirty_tracking`、`dirty_tracking`）、`src/vmm/src/arch/aarch64/vm.rs` 的 `enable_hdbss`、`src/vmm/src/builder.rs`、`src/vmm/src/lib.rs` 的 `instance_info()`
- 图：后端选择 flowchart；三种后端对比表

**66 · HDBSS：鲲鹏硬件脏页跟踪与 KVM 能力**
- 硬件机制：ARM FEAT_HDBSS（hardware dirty state tracking，硬件把脏页 PTE 地址追加到一个缓冲区，满了触发异常）；与传统「写保护 + 缺页」的区别：不再每页一次 VM exit
- KVM 侧：`KVM_CAP_ARM_HW_DIRTY_STATE_TRACK`（值 502，openEuler 6.6.0-515 内核的非主线补丁）、`KVM_ENABLE_CAP` 的 `args[0]` = 缓冲区 order；`enable_hdbss()` 直接 `libc::ioctl` 而不经 `kvm-ioctls`（为什么：binding 里没有）；`KVM_ENABLE_CAP` 的 ioctl 号常量 `0x4068_AEA3` 怎么来的
- 语义边界：使能后 `KVM_GET_DIRTY_LOG` 返回的仍是同一个位图接口；精度 / 延迟 / 缓冲区溢出时的行为（以内核文档 / 仓库根的 HDBSS 文档为准，标注推论）
- 内核前提与探测：能力号不存在时 `ioctl` 返回 EINVAL → 回退
- 代价：只在鲲鹏 950 + 特定内核可用；`order` 的取舍
- 代码：`src/vmm/src/arch/aarch64/vm.rs` 的 `enable_hdbss`、仓库根 `HDBSS_KUNPENG950_KERNEL_6.6.0_515.md`（背景）
- 图：写保护路径 vs HDBSS 路径对比（flowchart 两列）；ioctl 参数表

**67 · dirty_bitmap_path：sidecar 与 FCDB 格式**
- `CreateSnapshotParams.dirty_bitmap_path`（可选；给了它必须也给 `mem_file_path`，否则 `DirtyBitmapWithoutMemFile`）
- `dump_dirty()` 改为返回合并后的扁平位图（KVM ∥ 用户态，按扁平页序）；Full 快照的位图是全 1（末字截断）；`snapshot_memory_to_file()` 多了 `dirty_bitmap_path` 参数，写完 memfile 后写 sidecar 并 fsync
- FCDB 格式：magic `FCDB`、version 1、page_size u64、num_pages u64、位图字（小端）；`serialize_dirty_bitmap()` / `deserialize_dirty_bitmap()` 及其校验（长度、版本、magic）
- 为什么需要它：orchestrator 不必再自己判断稀疏文件哪些页有数据（`SEEK_DATA` 不可靠 / 粒度问题），回滚时也能拿它当 revert 位图
- 单元测试 `test_dump_dirty_returns_merged_flat_bitmap` / `test_restore_dirty_is_dump_dirty_inverse` 说明了契约
- 代码：`src/vmm/src/vmm_config/snapshot.rs`、`src/vmm/src/vstate/memory.rs`（`dump_dirty`、`serialize_dirty_bitmap`、`deserialize_dirty_bitmap`）、`src/vmm/src/vstate/vm.rs` 的 `snapshot_memory_to_file`、`src/vmm/src/persist.rs`
- 图：FCDB 字节布局（```text）；create 流程中 sidecar 的位置 flowchart

**68 · PUT /snapshot/save-dirty-bitmap**
- 用途：不导出内存、只把「自上次快照 / 回滚以来的脏页」写成 FCDB —— 给 orchestrator 做累计脏位图 / 决策用
- `rollback::save_dirty_bitmap()`：要求 Paused；`get_dirty_bitmap()` 读 KVM 日志（读即清零）→ 折叠进用户态位图（`userspace_bitmap_flat()` / 区域位图 `mark_dirty`，确认实现）→ 序列化写文件；「KVM 的读是破坏性的，所以先折叠进用户态位图」这个不变量
- 与 `create`（sidecar）的区别：不 reset、不导出、不动 KVM 之外的状态
- API：`SaveDirtyBitmapParams { path }`、`VmmAction::SaveDirtyBitmap`、Preboot 不允许
- 代价与陷阱：连续两次调用第二次看到什么；与 `create` 交错时位图的归属
- XFS 路线没有这个端点（一句话：那条路线用 reflink 拿差分，不需要累计位图 —— 以 checkpoint 手册第 18 篇为准，只链接）
- 代码：`src/vmm/src/rollback.rs` 的 `save_dirty_bitmap` / `userspace_bitmap_flat`、`src/vmm/src/rpc_interface.rs` 的 `save_dirty_bitmap`、`src/firecracker/src/api_server/request/snapshot.rs`
- 图：位图流向 flowchart（KVM 日志 → 用户态位图 → 文件）；调用序列表

**69 · PUT /snapshot/rollback：阶段、参数与响应**
- `RollbackSnapshotParams { snapshot_path, mem_file_path, revert_bitmap_path?, resume_vm }`；`RollbackResponse { restored_pages, restored_bytes, timings_us: {validate, quiesce, memory, vcpus, gic, devices, total} }`
- `rollback_snapshot()` 的阶段顺序（读代码列全，大致是：校验状态与参数 → 读 vmstate → `validate_topology` → 决定 revert 位图（给了文件就用文件，否则用当前脏页位图？确认）→ `quiesce_devices` → 内存写回 → vCPU → GIC → 设备状态 → 清位图 → 计时）；每阶段一段，细节放 70–72 篇
- 执行环境：VMM 线程、VM Paused、世界静止；`RuntimeApiController::rollback_snapshot()` 的包装（`resume_vm`、metrics 复用 `vmm_pause_vm`？确认并如实指出、失败时置 Faulted）
- 与 `load` 的对比表：重建什么 / 不重建什么、成本正比于什么
- 代码：`src/vmm/src/rollback.rs` 的 `rollback_snapshot`、`src/vmm/src/rpc_interface.rs`、`src/vmm/src/vmm_config/snapshot.rs`
- 图：阶段 flowchart（编号 + 表）；load vs rollback 对比表

**70 · 回滚的内存写回**
- 输入：目标快照的 memfile（Full 或已合并）+ revert 位图（哪些页要从文件写回）
- `GuestMemoryExtension::restore_dirty()`：按扁平位图逐区域找连续脏页段、`seek` + `read_exact_volatile` 到 guest 内存的 `VolatileSlice`；返回页数 / 字节数
- revert 位图从哪来：`revert_bitmap_path`（FCDB）或当前 KVM ∥ 用户态位图（含义：把自目标快照以来脏的页全部写回）；两者的正确性前提（orchestrator 必须保证位图覆盖了所有偏离页 —— 这是契约，链接 checkpoint 手册）
- 写回后的位图处理：`reset_dirty_bitmap()` / `reset_dirty()`（回滚点成为新的脏页基线）
- 与 uffd 后备内存的交互：写回是 VMM 进程写匿名页 → 是否触发 uffd MISSING、页从未被填充时怎样（读代码 / 标推论）
- 代价：写回量 = 位图里的页数；大页时的粒度
- 代码：`src/vmm/src/vstate/memory.rs` 的 `restore_dirty`、`src/vmm/src/rollback.rs` 的内存阶段
- 图：位图 → 段 → 写回 flowchart；测试用例里的例子（```text）

**71 · 回滚的 vCPU 与 GIC**
- 上游只有「新进程里恢复 vCPU」；回滚要在**已有** vCPU fd 上写回状态：`VcpuEvent::RestoreState(Arc<VcpuState>)` → paused 状态机分支 → `KvmVcpu::restore_state_in_place()` → `restore_state()`；`VcpuResponse::RestoredState`；`Vmm::restore_vcpu_states_in_place()` 的收发与错误映射
- aarch64 的关键：`restore_state()` 里包含 `KVM_ARM_VCPU_INIT`（架构定义的复位）+ `FINALIZE` + 全部 `SET_ONE_REG` + `MP_STATE`；为什么「只写寄存器」不够（内核侧的 vCPU 状态 —— 定时器、PMU、SVE 上下文、pending 异常 —— 只写寄存器覆盖不到；讲成两种做法的设计取舍，不引用具体数字、不写过程叙事）
- x86 的 `restore_state_in_place()` 只是转发（本项目不在 x86 跑，如实说明未验证）
- GIC：rollback.rs 里 GIC 阶段调的是什么（确认），`KVM_DEV_ARM_VGIC_GRP_*` 在运行中的 GIC 上重设；`construct_kvm_mpidrs`
- seccomp：vcpu 线程新增四个 ioctl 白名单（第 73 篇）
- 代码：`src/vmm/src/vstate/vcpu.rs`（`RestoreState` 分支）、`src/vmm/src/arch/aarch64/vcpu.rs`、`src/vmm/src/lib.rs` 的 `restore_vcpu_states_in_place`、`src/vmm/src/rollback.rs` 的 vCPU / GIC 阶段
- 图：vCPU 回滚时序（sequenceDiagram：VMM 线程、vCPU 线程、KVM）；两种 vCPU 恢复路线对比表

**72 · 回滚的设备状态**
- 前提：设备对象不重建，只把逻辑状态写回。`validate_topology()`：目标快照的 `DeviceStates` 与当前设备管理器的设备数量、类型、id、顺序必须一致，否则拒绝（为什么：地址、IRQ、fd 都绑定在现有对象上）
- `quiesce_devices()`：让设备停在安全点（io_uring drain？rate limiter？读代码列全）
- `apply_device_states()` / `apply_one_device()`：按类型分派 —— `MmioTransport::apply_state()`（transport 寄存器）、`VirtioDeviceState` 写回（队列索引、特性、中断状态；用各 `*State::virtio_state()` 访问器）、block / rng / balloon / vsock 的处理差异；vhost-user 块设备不支持（`virtio_state()` 返回 `None`）
- net 的特殊处理：`apply_net_rx_cache()` → `Net::rollback_rx_buffers()`：为什么 RX 预解析缓存必须重建（`next_avail` 回退 + 重新 `parse_rx_descriptors` + 恢复 `used_descriptors` / `used_bytes`）；不重建会怎样（描述符链与 guest 内存不一致 → 挂死）
- vmgenid：`refresh_generation()` 让 guest 知道「时间倒流」；vsock 是否发 TRANSPORT_RESET（确认）
- `log_queue_diagnostics()`：pause 与 apply 后打印每个设备的队列生产 / 消费位置与 RX 缓存 —— 诊断用途，代价
- 代码：`src/vmm/src/rollback.rs`（`validate_topology`、`quiesce_devices`、`apply_device_states`、`apply_one_device`、`apply_net_rx_cache`、`log_queue_diagnostics`）、`src/vmm/src/devices/virtio/persist.rs` 的 `apply_state`、`net/device.rs` 的 `rollback_rx_buffers`、各 `persist.rs` 的访问器、`devices/acpi/vmgenid.rs` 的 `refresh_generation`
- 图：设备状态写回 flowchart（按类型分列）；RX 缓存重建前后（```text）

**73 · 失败模型、Faulted 状态与 seccomp 白名单**
- `RollbackError` 枚举与 `faults_vm()`：内存写回之前的错误（校验、位图、文件）无副作用，VM 仍 Paused 可 resume；从内存写回开始的错误让 VM 处于「两个时刻的混合」→ 置 `VmState::Faulted`
- `Faulted` 的传播：`resume_vm()` / `pause_vm()` 返回 `VmFaulted`，`create_snapshot` 拒绝，`GET /` 可见；orchestrator 的预期动作（杀进程重建 —— 链接 checkpoint 手册第 14 篇）
- 计时与回报：`RollbackTimings` 各阶段 μs、`restored_pages` / `restored_bytes`；日志行
- seccomp：aarch64 vcpu 线程新增 `KVM_SET_ONE_REG`、`KVM_SET_MP_STATE`、`KVM_ARM_VCPU_INIT`、`KVM_ARM_VCPU_FINALIZE`；vmm 线程 `pread64`；每条为什么需要、不加会在哪一步 SIGSYS
- 未覆盖的情况清单（如实）：x86 未验证、vhost-user 不支持、balloon 在回滚中的处理、大页、与 uffd 后备内存的交互
- 测试：`test_restore_dirty_is_dump_dirty_inverse` 等单元测试覆盖了什么、没覆盖什么；集成验证在 checkpoint 手册第 21–26 篇
- 代码：`src/vmm/src/rollback.rs`（`RollbackError`、`faults_vm`）、`src/vmm/src/lib.rs`（`VmFaulted`、`pause_vm` / `resume_vm`）、`src/vmm/src/rpc_interface.rs`、`src/vmm/src/vmm_config/instance_info.rs`、`resources/seccomp/aarch64-unknown-linux-musl.json`
- 图：错误分类与 VM 状态转移（flowchart 编号边 + 表）；seccomp 新增规则表

### 附录

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 74 | `74-glossary.md` | 术语表 | ◎ |
| 75 | `75-code-map.md` | 代码地图：crate、模块与篇目 | ◎ |
| 76 | `76-api-reference.md` | API 端点总表 | ◎ |
| 77 | `77-config-cli-env-metrics-reference.md` | 配置项、命令行参数、环境变量与 metrics 总表 | ◎ |
| 78 | `78-layer-diff-tables.md` | 三层差异总表（文件级） | ◎ |
| 79 | `79-reading-upstream-code.md` | 阅读上游代码的方法与常见问题 | ◎ |

**74 · 术语表**
- STYLE.md 第三节的全部术语 + 正文中出现的其它术语，每条：中文、英文、一句话定义、首次出现的篇
- 按字母序（英文）排列；不少于 80 条
- 无图

**75 · 代码地图：crate、模块与篇目**
- 每个 crate → 模块 → 文件 → 讲它的篇目；`vmm` crate 按目录树展开（```text）
- 两层改动涉及的文件单独标注（e2b / ARM 两列打勾）
- 无 mermaid，用表与 ```text

**76 · API 端点总表**
- 上游 v1.12.1 全部端点（方法、路径、Preboot / Runtime 允许、对应 `VmmAction`、篇）+ e2b 定制版三个 GET + ARM 适配版两个 PUT；`PUT /snapshot/create` 的参数变化按层标注
- 每个端点的请求 / 响应 JSON 骨架（从 swagger 抄要点，不全抄）
- 表为主

**77 · 配置项、命令行参数、环境变量与 metrics 总表**
- 命令行参数表（第 6 篇的完整版）；`machine-config` 等配置项全表；环境变量（`FC_HDBSS_ORDER`、`FC_HDBSS_REQUIRED`、`RUST_BACKTRACE`…）；`latencies_us` 与关键 metrics 表；退出码表
- 表为主

**78 · 三层差异总表（文件级）**
- 两张 `git diff --stat` 表（上游 → e2b a41d3fb、e2b 54a1c1a → ARM 3863c76）加一张「54a1c1a 与 a41d3fb 之差」的小表，每行：文件、+/-、改动摘要一句、篇；内核一行（fc-kernels v0.0.8：config 差异、无补丁）；升级 Firecracker 时的重放清单（按依赖顺序）
- 表为主

**79 · 阅读上游代码的方法与常见问题**
- 怎么从一个 API 路径追到执行代码（`parsed_request.rs` → `VmmAction` → 控制器 → `Vmm` 方法）；怎么从一个 `cfg(target_arch)` 找到另一架构的对应实现；怎么找一个设备的四个文件（device / event_handler / persist / metrics）；怎么用 `git log -S` 追一个常量的来历；怎么读 seccomp 表；怎么在没有 devtool 的机器上跑单元测试
- 常见问题：为什么 `create` 之后要重新标脏队列页、为什么 aarch64 恢复 vCPU 要 reinit、为什么 API 是同步的、`track_dirty_pages` 关闭时 Diff 快照会怎样、为什么 ARM 上没有 uffd 写保护…（每条给出篇目链接，不重复正文）
- 无图或一张 flowchart

---

## 四、编写流程

1. **规划**（本文件）：由主编（Fable）完成，用户过目后才开写。
2. **编写**：每篇由一个 opus 子任务独立完成，输入是 `tools/briefs/firecracker/WRITER-BRIEF.md` + 本文件中该篇的要点；
   一个子任务负责 3–4 篇相邻篇目；一波最多 10 个子任务并行。顺序：第一至八部分（上游）→ 第九、第十部分 → 附录 → 00。
3. **审校**：每 8–10 篇一个审校子任务（`tools/briefs/firecracker/REVIEWER-BRIEF.md`），抽查代码论断、统一术语、修链接。
4. **图**：`tools/figcheck.sh firecracker` 全 PASS；WARN 的图按 `tools/briefs/FIGURE-FIXER-BRIEF.md` 返工。
5. **验收**：主编逐部抽读，跑 `tools/mdlinks.py firecracker`、`tools/mdmermaid.mjs firecracker/*.md`、`tools/figcheck.sh firecracker`，
   打包 `dist/firecracker.html`，用 chromium 截图看排版，更新 README 的版本行与版本表，提交、打 tag、发 Release。

每篇完成后把本文件状态列改为 `●`，审校后改为 `◎`。
