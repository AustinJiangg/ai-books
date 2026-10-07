# AgentENV 技术手册

一本关于 **AgentENV**（[kvcache-ai/AgentENV](https://github.com/kvcache-ai/AgentENV)，tag `v0.2.3`）的教材式技术手册，
并讲解它依赖的 **AENV 补丁版 Firecracker**（kvcache-ai/firecracker `aenv-deps`，上游 v1.15.1 之上 7 个提交）
在上游之上加了什么、为什么加。

AgentENV 是为 agentic RL 训练大规模运行 agent 环境的沙箱平台，对外提供 E2B 兼容的 API。
它和 e2b infra 面对同一组问题（隔离、秒级启动、低成本暂停、海量镜像），但走了另一条路：
用 Rust 重写的 overlaybd 加 ublk 提供块设备与按需加载，把内存快照也做成 overlaybd 层、
恢复时以只读块设备交给 Firecracker 映射，让同一快照的沙箱共享宿主页缓存；
暂停时只导出脏页，fork 不经过仓库；单节点自足，多节点时加一层 Go 写的 gateway 与 scheduler。
全书先讲总体架构与沙箱的一生，再按 API、编排、运行时、存储、快照、控制面、部署的顺序展开，最后与 e2b infra 逐项对照。

未特别说明处，全书讲的都是 **AgentENV v0.2.3**。版本称谓与术语见 [`STYLE.md`](STYLE.md)，
图的画法见 [`FIGURE-GUIDE.md`](FIGURE-GUIDE.md)，编写计划见 [`OUTLINE.md`](OUTLINE.md)。

> **编写进度**：74 篇中已完成 1 篇（第 19 篇），其余未写。续写方法见 `tools/briefs/agentenv/HANDOFF.md`。

---

## 怎么读

| 你是 | 建议路径 |
|---|---|
| 想先看个全貌 | **00 → 08 → 09** |
| 不熟悉 io_uring / ublk / overlaybd | **04 → 05**，然后 **34 → 36 → 40 → 41** |
| 要接手 AgentENV 代码的工程师 | **01 → 08 → 09 → 10**，然后 **19 → 20 → 25 → 27**，再按部补全 |
| 只关心快照与内存 | **03 → 27 → 37 → 42 → 43**，然后 **46 → 47 → 49 → 51** |
| 做存储层开发 | **04 → 05**，然后 **34 → 44** 全部，再读 **45** |
| 用 E2B SDK 接入 AgentENV | **12 → 13 → 14 → 17 → 18** |
| 做多节点部署与运维 | **54 → 58**，然后 **59 → 61** |
| 熟悉 e2b infra，想知道差在哪 | **65 → 66 → 67**，再按两篇里的链接回到正文 |
| 评审 / 决策者 | **00 → 02 → 65 → 66 → 68** |

---

## 目录

### 第〇部分　导读

| # | 文档 | 内容 |
|---|---|---|
| 00 | [`00-overview.md`](00-overview.md) | 全书导读与 AgentENV 总览 |
| 01 | [`01-repo-map-and-versions.md`](01-repo-map-and-versions.md) | 仓库地图、版本与依赖 |

### 第一部分　预备知识

| # | 文档 | 内容 |
|---|---|---|
| 02 | [`02-why-agentenv.md`](02-why-agentenv.md) | agent 环境的规模问题与 AgentENV 的取舍 |
| 03 | [`03-firecracker-for-agentenv.md`](03-firecracker-for-agentenv.md) | 本书用到的 Firecracker：快照、内存后端与脏页 |
| 04 | [`04-io-uring-and-ublk.md`](04-io-uring-and-ublk.md) | io_uring 与 ublk |
| 05 | [`05-overlaybd-and-lazy-loading.md`](05-overlaybd-and-lazy-loading.md) | overlaybd、LSMT 与 OCI 镜像按需加载 |
| 06 | [`06-netns-iptables-transparent-proxy.md`](06-netns-iptables-transparent-proxy.md) | 网络命名空间、iptables 与透明代理 |
| 07 | [`07-rust-async-primer.md`](07-rust-async-primer.md) | 本书用到的 Rust 异步与依赖 crate |

### 第二部分　总体架构

| # | 文档 | 内容 |
|---|---|---|
| 08 | [`08-system-architecture.md`](08-system-architecture.md) | 系统架构：单节点与多节点 |
| 09 | [`09-sandbox-lifecycle-walkthrough.md`](09-sandbox-lifecycle-walkthrough.md) | 一个沙箱的一生 |
| 10 | [`10-node-process-and-object-model.md`](10-node-process-and-object-model.md) | 节点进程：启动、关闭与对象模型 |
| 11 | [`11-configuration.md`](11-configuration.md) | 配置体系 |

### 第三部分　API 层

| # | 文档 | 内容 |
|---|---|---|
| 12 | [`12-spec-driven-server.md`](12-spec-driven-server.md) | 规范驱动的服务骨架 |
| 13 | [`13-authentication.md`](13-authentication.md) | 认证与凭据 |
| 14 | [`14-sandbox-api.md`](14-sandbox-api.md) | 沙箱生命周期 API |
| 15 | [`15-template-build-api.md`](15-template-build-api.md) | 模板构建 API |
| 16 | [`16-snapshot-and-volume-api.md`](16-snapshot-and-volume-api.md) | 快照与卷 API |
| 17 | [`17-reverse-proxy.md`](17-reverse-proxy.md) | 反向代理 |
| 18 | [`18-e2b-compatibility.md`](18-e2b-compatibility.md) | E2B 兼容性：矩阵与偏差 |

### 第四部分　orchestrator：沙箱状态机

| # | 文档 | 内容 |
|---|---|---|
| 19 | [`19-state-machine-and-concurrency.md`](19-state-machine-and-concurrency.md) | 状态机与并发控制 |
| 20 | [`20-launch-plan-and-rollback.md`](20-launch-plan-and-rollback.md) | launch plan 与失败回滚 |
| 21 | [`21-deletion-and-volume-capture.md`](21-deletion-and-volume-capture.md) | 删除与卷的捕获提交 |
| 22 | [`22-persistence-across-restarts.md`](22-persistence-across-restarts.md) | 跨重启持久化 |
| 23 | [`23-auto-eviction-and-ttl.md`](23-auto-eviction-and-ttl.md) | 自动驱逐与 TTL |
| 24 | [`24-metrics-and-events.md`](24-metrics-and-events.md) | 指标与生命周期事件 |

### 第五部分　沙箱运行时

| # | 文档 | 内容 |
|---|---|---|
| 25 | [`25-backend-and-firecracker-process.md`](25-backend-and-firecracker-process.md) | 后端抽象与 Firecracker 进程 |
| 26 | [`26-sandbox-block-devices.md`](26-sandbox-block-devices.md) | 沙箱的块设备：tools 盘、rootfs 与内存设备 |
| 27 | [`27-start-pause-resume-sequences.md`](27-start-pause-resume-sequences.md) | 启动、暂停与恢复的 Firecracker 调用序列 |
| 28 | [`28-mmds-and-envd.md`](28-mmds-and-envd.md) | MMDS 与 envd |
| 29 | [`29-network-slots.md`](29-network-slots.md) | 网络（一）：槽位、命名空间与地址计划 |
| 30 | [`30-egress-policy-and-proxy.md`](30-egress-policy-and-proxy.md) | 网络（二）：出站策略与透明代理 |
| 31 | [`31-extra-drives-and-volumes.md`](31-extra-drives-and-volumes.md) | 附加盘与卷：预留槽位与热插 |
| 32 | [`32-warm-pools.md`](32-warm-pools.md) | 预热池：网络、块设备与 Firecracker 进程 |
| 33 | [`33-custom-extension-hooks.md`](33-custom-extension-hooks.md) | 自定义扩展 hook |

### 第六部分　存储：overlaybd 与 ublk

| # | 文档 | 内容 |
|---|---|---|
| 34 | [`34-lsmt-format-and-index.md`](34-lsmt-format-and-index.md) | LSMT 格式与索引 |
| 35 | [`35-zfile-compression.md`](35-zfile-compression.md) | ZFile 压缩 |
| 36 | [`36-read-write-paths-and-rw-layouts.md`](36-read-write-paths-and-rw-layouts.md) | 读写路径与三种可写布局 |
| 37 | [`37-seal-restack-compact.md`](37-seal-restack-compact.md) | 封存、restack 与 compact |
| 38 | [`38-virtualfile-chain-and-remote-io.md`](38-virtualfile-chain-and-remote-io.md) | VirtualFile 装饰器链与远端 I/O 运行时 |
| 39 | [`39-block-cache-and-background-download.md`](39-block-cache-and-background-download.md) | 节点块缓存与后台下载 |
| 40 | [`40-ublk-library.md`](40-ublk-library.md) | ublk 库 |
| 41 | [`41-ublk-daemon.md`](41-ublk-daemon.md) | ublk-daemon |
| 42 | [`42-memory-snapshot-over-ublk.md`](42-memory-snapshot-over-ublk.md) | 内存快照：脏页成层与共享只读设备 |
| 43 | [`43-startup-pack-and-prefetch.md`](43-startup-pack-and-prefetch.md) | 启动加速：trace prefetch 与 startup pack |
| 44 | [`44-uffd-alternative.md`](44-uffd-alternative.md) | uffd 方案与对比 |

### 第七部分　镜像、快照与模板

| # | 文档 | 内容 |
|---|---|---|
| 45 | [`45-oci-to-overlaybd.md`](45-oci-to-overlaybd.md) | 从 OCI 镜像到 overlaybd 层栈 |
| 46 | [`46-snapshot-object-model.md`](46-snapshot-object-model.md) | 快照对象模型与 SnapshotManager |
| 47 | [`47-posix-repository.md`](47-posix-repository.md) | POSIX 仓库与提交协议 |
| 48 | [`48-object-storage-repository.md`](48-object-storage-repository.md) | 对象存储仓库：上传、回滚与弱一致 |
| 49 | [`49-resolve-and-artifact-cache.md`](49-resolve-and-artifact-cache.md) | 从记录到可运行：resolve 与本地制品缓存 |
| 50 | [`50-rootfs-as-oci-image.md`](50-rootfs-as-oci-image.md) | 快照 rootfs 作为 OCI 镜像 |
| 51 | [`51-fork.md`](51-fork.md) | fork：同节点的内存分叉 |
| 52 | [`52-template-builder.md`](52-template-builder.md) | 模板构建器 |
| 53 | [`53-buildkit-in-microvm.md`](53-buildkit-in-microvm.md) | BuildKit：在 microVM 里跑 Dockerfile |

### 第八部分　分布式控制面

| # | 文档 | 内容 |
|---|---|---|
| 54 | [`54-control-plane-overview.md`](54-control-plane-overview.md) | 控制面总览与 proto 契约 |
| 55 | [`55-gateway.md`](55-gateway.md) | gateway：路由判定与反向代理 |
| 56 | [`56-scheduler.md`](56-scheduler.md) | scheduler：放置、绑定与 HA |
| 57 | [`57-heartbeat-and-cpu-intersection.md`](57-heartbeat-and-cpu-intersection.md) | 心跳、节点可观测与 CPU 模板交集 |
| 58 | [`58-p2p-artifact-transport.md`](58-p2p-artifact-transport.md) | P2P 制品传输 |

### 第九部分　部署与工程

| # | 文档 | 内容 |
|---|---|---|
| 59 | [`59-host-setup-and-privileges.md`](59-host-setup-and-privileges.md) | 宿主准备、依赖供给与权限模型 |
| 60 | [`60-deployment.md`](60-deployment.md) | 单节点安装、Compose 与 Kubernetes |
| 61 | [`61-pvm.md`](61-pvm.md) | PVM：没有嵌套虚拟化时 |
| 62 | [`62-aenv-cli.md`](62-aenv-cli.md) | aenv CLI |
| 63 | [`63-testing-and-benchmarks.md`](63-testing-and-benchmarks.md) | 测试与基准 |
| 64 | [`64-build-codegen-release.md`](64-build-codegen-release.md) | 构建、代码生成与发布 |

### 第十部分　对照与延伸

| # | 文档 | 内容 |
|---|---|---|
| 65 | [`65-vs-e2b-infra-architecture.md`](65-vs-e2b-infra-architecture.md) | 与 e2b infra 的对照（一）：架构、控制面与 API |
| 66 | [`66-vs-e2b-infra-storage-and-memory.md`](66-vs-e2b-infra-storage-and-memory.md) | 与 e2b infra 的对照（二）：存储、内存恢复与模板 |
| 67 | [`67-firecracker-patch-layer.md`](67-firecracker-patch-layer.md) | AENV 补丁版 Firecracker 与 guest 内核 |
| 68 | [`68-known-issues-and-debt.md`](68-known-issues-and-debt.md) | 已知问题与技术债 |

### 附录

| # | 文档 | 内容 |
|---|---|---|
| 69 | [`69-glossary.md`](69-glossary.md) | 术语表 |
| 70 | [`70-code-map.md`](70-code-map.md) | 代码地图：crate、模块与篇目 |
| 71 | [`71-config-env-ports-reference.md`](71-config-env-ports-reference.md) | 配置项、环境变量与端口总表 |
| 72 | [`72-api-reference.md`](72-api-reference.md) | 接口总表：HTTP、Firecracker、daemon RPC 与 gRPC |
| 73 | [`73-artifacts-and-formats-reference.md`](73-artifacts-and-formats-reference.md) | 持久化制品与磁盘格式总表 |

---

## 相关手册

- [e2b 服务端基础设施技术手册](../e2b-infra/README.md)：同一组问题的另一种实现；第 65、66 篇的对照以它为依据，第 05、06、31、33、37 篇与本书第六、七部分关系最密切。
- [Firecracker 技术手册](../firecracker/README.md)：本书不展开 Firecracker 本身；第 36–39 篇（快照与内存后端）、第 14 篇（脏页跟踪）、第 49–54 篇（e2b 定制版的内存 API）是本书第 03、42、67 篇的背景。
