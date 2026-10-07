# Firecracker 技术手册

一本关于 **Firecracker**（[firecracker-microvm/firecracker](https://github.com/firecracker-microvm/firecracker)，tag `v1.12.1`）
的教材式技术手册，并逐层讲解 **e2b 定制版**与本项目的 **aarch64（鲲鹏 / openEuler）适配版**（含 checkpoint / restore 扩展）
在它之上改了什么、为什么改、代价是什么。也讲 guest 内核的配置，但不讲内核源码。

Firecracker 是 e2b 沙箱的执行引擎：一个进程一台 microVM，KVM 之上的极简 VMM。e2b 需要它做两件上游没有的事 ——
让宿主进程直接读 guest 内存、按页判断哪些内存值得导出；本项目又在 aarch64 上让它跑起来，并加了
原地回滚与硬件脏页跟踪，使暂停的成本正比于改动量、恢复不必重建进程。全书先把上游讲透（进程与控制面、
内存与 vCPU、设备、快照、安全），再按版本谱系一层层讲改动。

未特别说明处，全书讲的都是**上游 v1.12.1**；e2b 定制版与 ARM 适配版的改动分别集中在第九、第十部分。
版本称谓与术语见 [`STYLE.md`](STYLE.md)，图的画法见 [`FIGURE-GUIDE.md`](FIGURE-GUIDE.md)，编写计划见 [`OUTLINE.md`](OUTLINE.md)。

---

## 怎么读

| 你是 | 建议路径 |
|---|---|
| 想先看个全貌 | **00 → 01** |
| 不熟悉 KVM / virtio / Rust 系统编程 | **02 → 03 → 04 → 05**，然后 **07 → 11 → 12** |
| 要接手 Firecracker 代码的工程师 | **07 → 12**，然后 **13 → 15 → 25 → 26 → 36 → 37 → 38**，再按部补全 |
| 只关心快照与内存 | **13 → 14 → 36 → 37 → 38 → 39 → 40**，然后 **49 → 54** |
| 做 aarch64 适配与鲲鹏部署 | **18 → 19**，然后 **57 → 63** |
| 做 checkpoint / restore 后续开发 | **14 → 37 → 40 → 53 → 57**，然后 **64 → 73** 全部 |
| 要升级 Firecracker 版本 | **01 → 55 → 78**，再按 78 的重放清单读对应篇 |
| 评审 / 决策者 | **00 → 49 → 57 → 64** |

---

## 目录

### 第〇部分　导读

| # | 文档 | 内容 |
|---|---|---|
| 00 | [`00-overview.md`](00-overview.md) | 全书导读与 Firecracker 总览 |
| 01 | [`01-lineage-and-repo-map.md`](01-lineage-and-repo-map.md) | 三层版本谱系与仓库地图 |

### 第一部分　预备知识

| # | 文档 | 内容 |
|---|---|---|
| 02 | [`02-microvm-design-tradeoffs.md`](02-microvm-design-tradeoffs.md) | microVM 与 Firecracker 的设计取舍 |
| 03 | [`03-kvm-api-primer.md`](03-kvm-api-primer.md) | 本书用到的 KVM API |
| 04 | [`04-virtio-and-mmio-primer.md`](04-virtio-and-mmio-primer.md) | virtio 与 virtio-mmio 基础 |
| 05 | [`05-rust-and-crates-primer.md`](05-rust-and-crates-primer.md) | 本书用到的 Rust 与依赖 crate |
| 06 | [`06-build-run-debug.md`](06-build-run-debug.md) | 构建、运行与调试环境 |

### 第二部分　进程与控制面

| # | 文档 | 内容 |
|---|---|---|
| 07 | [`07-process-startup.md`](07-process-startup.md) | 进程启动：从参数到运行 |
| 08 | [`08-api-server.md`](08-api-server.md) | API server：Unix socket 上的 HTTP 与请求解析 |
| 09 | [`09-rpc-interface.md`](09-rpc-interface.md) | rpc_interface：Preboot 与 Runtime 两个控制器 |
| 10 | [`10-vm-resources-and-config.md`](10-vm-resources-and-config.md) | 资源模型：VmResources 与 vmm_config |
| 11 | [`11-builder.md`](11-builder.md) | builder：从配置到运行中的 microVM |
| 12 | [`12-vmm-event-loop-and-exit.md`](12-vmm-event-loop-and-exit.md) | Vmm、事件循环与退出路径 |

### 第三部分　内存与 vCPU

| # | 文档 | 内容 |
|---|---|---|
| 13 | [`13-guest-memory.md`](13-guest-memory.md) | guest 内存：GuestMemoryMmap、区域与 memslot |
| 14 | [`14-dirty-page-tracking.md`](14-dirty-page-tracking.md) | 脏页跟踪：KVM 日志与用户态位图 |
| 15 | [`15-vcpu-threads-and-state-machine.md`](15-vcpu-threads-and-state-machine.md) | vCPU 线程与状态机 |
| 16 | [`16-x86-64-vcpu.md`](16-x86-64-vcpu.md) | x86_64 vCPU：寄存器、CPUID、MSR 与引导协议 |
| 17 | [`17-x86-64-platform.md`](17-x86-64-platform.md) | x86_64 平台：内存布局、ACPI、mptable 与时钟 |
| 18 | [`18-aarch64-vcpu.md`](18-aarch64-vcpu.md) | aarch64 vCPU：KVM_ARM_VCPU_INIT、寄存器与 PSCI |
| 19 | [`19-aarch64-platform.md`](19-aarch64-platform.md) | aarch64 平台：内存布局、FDT 与 GIC |

### 第四部分　CPU 模板

| # | 文档 | 内容 |
|---|---|---|
| 20 | [`20-cpu-templates.md`](20-cpu-templates.md) | CPU 模板机制：静态、自定义与序列化 |
| 21 | [`21-x86-64-cpuid-msr-normalization.md`](21-x86-64-cpuid-msr-normalization.md) | x86_64 CPUID 与 MSR 归一化 |
| 22 | [`22-aarch64-templates-and-helper.md`](22-aarch64-templates-and-helper.md) | aarch64 模板与 cpu-template-helper |

### 第五部分　设备

| # | 文档 | 内容 |
|---|---|---|
| 23 | [`23-bus-and-mmio-device-manager.md`](23-bus-and-mmio-device-manager.md) | 设备总线与 MMIO 设备管理器 |
| 24 | [`24-legacy-devices.md`](24-legacy-devices.md) | legacy 设备：串口、i8042、RTC 与 boot timer |
| 25 | [`25-virtio-device-model-and-transport.md`](25-virtio-device-model-and-transport.md) | virtio 设备模型与 MMIO 传输层 |
| 26 | [`26-virtqueue-implementation.md`](26-virtqueue-implementation.md) | virtqueue 实现：queue.rs、iovec 与 iov_deque |
| 27 | [`27-virtio-block.md`](27-virtio-block.md) | virtio-block：请求解析与 I/O 引擎 |
| 28 | [`28-io-uring-engine.md`](28-io-uring-engine.md) | io_uring 引擎 |
| 29 | [`29-vhost-user-block.md`](29-vhost-user-block.md) | vhost-user 块设备 |
| 30 | [`30-virtio-net.md`](30-virtio-net.md) | virtio-net：tap、收发路径与 offload |
| 31 | [`31-dumbo-tcpip-stack.md`](31-dumbo-tcpip-stack.md) | dumbo：内建 TCP/IP 栈 |
| 32 | [`32-mmds.md`](32-mmds.md) | MMDS：元数据服务与 token |
| 33 | [`33-vsock.md`](33-vsock.md) | vsock：设备、连接状态机与 unix muxer |
| 34 | [`34-balloon.md`](34-balloon.md) | balloon：气球、统计与 free page 汇报 |
| 35 | [`35-entropy-vmgenid-rate-limiter.md`](35-entropy-vmgenid-rate-limiter.md) | entropy、vmgenid 与速率限制器 |

### 第六部分　快照

| # | 文档 | 内容 |
|---|---|---|
| 36 | [`36-snapshot-overview-and-format.md`](36-snapshot-overview-and-format.md) | 快照总览：文件、版本与 MicrovmState |
| 37 | [`37-snapshot-create.md`](37-snapshot-create.md) | 创建快照：save_state、内存导出与 Diff |
| 38 | [`38-snapshot-load.md`](38-snapshot-load.md) | 加载快照：restore、内存后端与设备重建 |
| 39 | [`39-uffd-backend.md`](39-uffd-backend.md) | userfaultfd 后端与缺页处理 |
| 40 | [`40-device-persist.md`](40-device-persist.md) | 设备状态的 Persist：逐设备的保存与恢复 |
| 41 | [`41-snapshot-tools-and-compat.md`](41-snapshot-tools-and-compat.md) | snapshot-editor、rebase-snap 与兼容性 |

### 第七部分　安全与可观测

| # | 文档 | 内容 |
|---|---|---|
| 42 | [`42-seccomp.md`](42-seccomp.md) | seccomp：seccompiler、过滤器与安装时机 |
| 43 | [`43-jailer.md`](43-jailer.md) | jailer：chroot、cgroup 与 namespace |
| 44 | [`44-logging-and-metrics.md`](44-logging-and-metrics.md) | 日志与 metrics |
| 45 | [`45-gdb-tracing-and-kani.md`](45-gdb-tracing-and-kani.md) | GDB 调试、tracing 与形式化验证 |

### 第八部分　工程

| # | 文档 | 内容 |
|---|---|---|
| 46 | [`46-code-organization-and-build.md`](46-code-organization-and-build.md) | 代码组织、依赖与构建 |
| 47 | [`47-testing.md`](47-testing.md) | 测试体系：单元、集成与性能 |
| 48 | [`48-release-and-compat-policy.md`](48-release-and-compat-policy.md) | 发布策略、版本与兼容承诺 |

### 第九部分　e2b 定制版

| # | 文档 | 内容 |
|---|---|---|
| 49 | [`49-why-e2b-forked.md`](49-why-e2b-forked.md) | 为什么分叉：e2b 的内存管线要什么 |
| 50 | [`50-memory-mappings-api.md`](50-memory-mappings-api.md) | /memory/mappings：把 guest 内存的宿主地址交出去 |
| 51 | [`51-memory-resident-empty-api.md`](51-memory-resident-empty-api.md) | /memory：常驻页与零页位图 |
| 52 | [`52-memory-dirty-api.md`](52-memory-dirty-api.md) | /memory/dirty：pagemap 与写保护位的脏页判据 |
| 53 | [`53-uffd-write-protection.md`](53-uffd-write-protection.md) | uffd 写保护：让脏页判据成立的最后一环 |
| 54 | [`54-optional-memfile-snapshot.md`](54-optional-memfile-snapshot.md) | 可选 memfile 的快照与 e2b 的暂停流程 |
| 55 | [`55-seccomp-build-upload-and-upstream-fixes.md`](55-seccomp-build-upload-and-upstream-fixes.md) | seccomp、构建发布脚本与合入的上游修复 |
| 56 | [`56-guest-kernel-requirements-and-e2b-configs.md`](56-guest-kernel-requirements-and-e2b-configs.md) | guest 内核：Firecracker 的要求与 e2b 的内核配置 |

### 第十部分　ARM 适配版

| # | 文档 | 内容 |
|---|---|---|
| 57 | [`57-which-fork-commit-and-uffd-wp.md`](57-which-fork-commit-and-uffd-wp.md) | 迁入的版本：54a1c1a 与被放弃的 uffd 写保护 |
| 58 | [`58-building-and-running-on-aarch64.md`](58-building-and-running-on-aarch64.md) | 在 aarch64 上构建与运行 |
| 59 | [`59-aarch64-vs-x86-64-runtime-paths.md`](59-aarch64-vs-x86-64-runtime-paths.md) | aarch64 与 x86_64 运行路径的差异清单 |
| 60 | [`60-kunpeng-openeuler-host.md`](60-kunpeng-openeuler-host.md) | 鲲鹏 950 与 openEuler 宿主环境 |
| 61 | [`61-guest-kernel-on-arm.md`](61-guest-kernel-on-arm.md) | ARM 上的 guest 内核：arm64 配置与部署中的内核文件 |
| 62 | [`62-aarch64-seccomp-filter.md`](62-aarch64-seccomp-filter.md) | aarch64 的 seccomp 过滤器 |
| 63 | [`63-integration-with-e2b-infra.md`](63-integration-with-e2b-infra.md) | 与 e2b infra 的对接：版本目录、内核参数与 RPM |
| 64 | [`64-checkpoint-extension-overview.md`](64-checkpoint-extension-overview.md) | checkpoint / restore 扩展总览：目标、四个扩展点与分工 |
| 65 | [`65-dirty-tracking-backend.md`](65-dirty-tracking-backend.md) | 脏页跟踪后端：KVM 写保护与 HDBSS |
| 66 | [`66-hdbss.md`](66-hdbss.md) | HDBSS：鲲鹏硬件脏页跟踪与 KVM 能力 |
| 67 | [`67-dirty-bitmap-sidecar.md`](67-dirty-bitmap-sidecar.md) | dirty_bitmap_path：sidecar 与 FCDB 格式 |
| 68 | [`68-save-dirty-bitmap-api.md`](68-save-dirty-bitmap-api.md) | PUT /snapshot/save-dirty-bitmap |
| 69 | [`69-rollback-api-and-phases.md`](69-rollback-api-and-phases.md) | PUT /snapshot/rollback：阶段、参数与响应 |
| 70 | [`70-rollback-memory.md`](70-rollback-memory.md) | 回滚的内存写回 |
| 71 | [`71-rollback-vcpu-and-gic.md`](71-rollback-vcpu-and-gic.md) | 回滚的 vCPU 与 GIC |
| 72 | [`72-rollback-devices.md`](72-rollback-devices.md) | 回滚的设备状态 |
| 73 | [`73-failure-model-faulted-and-seccomp.md`](73-failure-model-faulted-and-seccomp.md) | 失败模型、Faulted 状态与 seccomp 白名单 |

### 附录

| # | 文档 | 内容 |
|---|---|---|
| 74 | [`74-glossary.md`](74-glossary.md) | 术语表 |
| 75 | [`75-code-map.md`](75-code-map.md) | 代码地图：crate、模块与篇目 |
| 76 | [`76-api-reference.md`](76-api-reference.md) | API 端点总表 |
| 77 | [`77-config-cli-env-metrics-reference.md`](77-config-cli-env-metrics-reference.md) | 配置项、命令行参数、环境变量与 metrics 总表 |
| 78 | [`78-layer-diff-tables.md`](78-layer-diff-tables.md) | 三层差异总表（文件级） |
| 79 | [`79-reading-upstream-code.md`](79-reading-upstream-code.md) | 阅读上游代码的方法与常见问题 |

---

## 相关手册

- [e2b 服务端基础设施技术手册](../e2b-infra/README.md)：Firecracker 的调用方（orchestrator）怎么用它；第 03、28、31、37、70 篇与本书关系最密切。
- [checkpoint / restore 手册](../../e2b-infra-docs/rollback/docs/README.md)：本书第十部分 checkpoint / restore 扩展的设计动机、orchestrator 侧实现、测试与性能。
