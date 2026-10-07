# e2b 服务端基础设施技术手册

一本关于 **e2b 服务端基础设施**（[e2b-dev/infra](https://github.com/e2b-dev/infra)，tag `2026.09`）
及其 **aarch64（鲲鹏 / openEuler）适配版**的教材式技术手册。

e2b 用 Firecracker microVM 给 AI 生成的代码提供隔离执行环境。它的核心设计是：**沙箱从不冷启动**，
一律从模板快照恢复；用完即弃，或者再暂停成一个新的快照。全书围绕这个循环展开：快照怎么造出来、
怎么被拉起、运行时的内存与磁盘怎么按需加载、网络怎么隔离、暂停时改动怎么被增量导出，
以及把整套系统搬到 aarch64 与私有环境时哪些假设不再成立。

未特别说明处，全书讲的都是**上游 2026.09**；ARM 适配版的差异集中在[第十部分](#第十部分arm-适配版)。
版本称谓与术语见 [`STYLE.md`](STYLE.md)，图的画法见 [`FIGURE-GUIDE.md`](FIGURE-GUIDE.md)。

---

## 怎么读

| 你是 | 建议路径 |
|---|---|
| 想先看个全貌 | **00** |
| 不熟悉虚拟化 / 内核接口 | **02 → 03 → 04 → 05 → 06 → 07**，然后 **10 → 12** |
| 后端工程师，要接手上游代码 | **10 → 11 → 12**，然后按部读第三至第八部分；orchestrator 的最短路径是 **26 → 27 → 29 → 30 → 31 → 33 → 35 → 37** |
| 做 ARM 适配与后续开发 | **10 → 12 → 27 → 31 → 37**，然后 **67 → 87** 全部 |
| 运维 / 部署 | **10 → 13 → 14**，然后 **63 → 66**（上游）或 **78 → 82**（ARM） |
| SDK / 应用开发者 | **12 → 48 → 52 → 53** |
| 评审 / 决策者 | **00 → 67 → 86** |

---

## 目录

### 第〇部分　导读

| # | 文档 | 内容 |
|---|---|---|
| 00 | [`00-overview.md`](00-overview.md) | 全书导读与系统总览 |
| 01 | [`01-e2b-ecosystem.md`](01-e2b-ecosystem.md) | e2b 生态与仓库地图 |

### 第一部分　预备知识

| # | 文档 | 内容 |
|---|---|---|
| 02 | [`02-why-sandbox.md`](02-why-sandbox.md) | AI 代码沙箱：问题、威胁模型与隔离谱系 |
| 03 | [`03-firecracker-primer.md`](03-firecracker-primer.md) | Firecracker 入门 |
| 04 | [`04-kvm-and-memory-virtualization.md`](04-kvm-and-memory-virtualization.md) | KVM 与内存虚拟化 |
| 05 | [`05-userfaultfd.md`](05-userfaultfd.md) | userfaultfd：把缺页交给用户态 |
| 06 | [`06-block-devices-nbd-cow.md`](06-block-devices-nbd-cow.md) | 块设备、NBD 与写时复制 |
| 07 | [`07-linux-networking-for-sandboxes.md`](07-linux-networking-for-sandboxes.md) | 沙箱网络的内核基础 |
| 08 | [`08-go-service-toolkit.md`](08-go-service-toolkit.md) | 本书用到的 Go 服务工程 |
| 09 | [`09-nomad-consul-terraform.md`](09-nomad-consul-terraform.md) | Nomad、Consul 与 Terraform |

### 第二部分　总体架构

| # | 文档 | 内容 |
|---|---|---|
| 10 | [`10-system-architecture.md`](10-system-architecture.md) | 系统架构：组件、进程、端口与数据流 |
| 11 | [`11-object-model.md`](11-object-model.md) | 对象模型与状态机 |
| 12 | [`12-sandbox-lifecycle-walkthrough.md`](12-sandbox-lifecycle-walkthrough.md) | 端到端走查：一个沙箱的一生 |
| 13 | [`13-storage-landscape.md`](13-storage-landscape.md) | 存储全景 |
| 14 | [`14-config-flags-versions.md`](14-config-flags-versions.md) | 配置、特性开关与版本约定 |

### 第三部分　API 服务

| # | 文档 | 内容 |
|---|---|---|
| 15 | [`15-api-service-structure.md`](15-api-service-structure.md) | API 服务的结构 |
| 16 | [`16-auth-and-multitenancy.md`](16-auth-and-multitenancy.md) | 认证与多租户 |
| 17 | [`17-sandbox-create-api.md`](17-sandbox-create-api.md) | 创建沙箱 |
| 18 | [`18-sandbox-lifecycle-api.md`](18-sandbox-lifecycle-api.md) | 沙箱生命周期 API |
| 19 | [`19-node-management-and-placement.md`](19-node-management-and-placement.md) | 节点管理与放置 |
| 20 | [`20-sandbox-state-storage.md`](20-sandbox-state-storage.md) | 沙箱运行态存储 |
| 21 | [`21-clusters-and-discovery.md`](21-clusters-and-discovery.md) | 集群与服务发现 |
| 22 | [`22-template-api.md`](22-template-api.md) | 模板 API |
| 23 | [`23-template-manager-client.md`](23-template-manager-client.md) | API 侧的构建管理 |
| 24 | [`24-api-metrics-and-analytics.md`](24-api-metrics-and-analytics.md) | API 的指标、日志与分析事件 |

### 第四部分　Orchestrator：沙箱运行时

| # | 文档 | 内容 |
|---|---|---|
| 25 | [`25-orchestrator-process.md`](25-orchestrator-process.md) | orchestrator 进程 |
| 26 | [`26-sandbox-object.md`](26-sandbox-object.md) | Sandbox 对象与 Factory |
| 27 | [`27-resume-sandbox.md`](27-resume-sandbox.md) | ResumeSandbox：从快照拉起一台沙箱 |
| 28 | [`28-firecracker-process-management.md`](28-firecracker-process-management.md) | Firecracker 进程管理 |
| 29 | [`29-template-artifact-format.md`](29-template-artifact-format.md) | 模板产物格式 |
| 30 | [`30-block-layer.md`](30-block-layer.md) | block 包：缓存、overlay 与分片读取 |
| 31 | [`31-uffd-memory-backend.md`](31-uffd-memory-backend.md) | 内存后端：uffd 服务 |
| 32 | [`32-memory-prefetch-and-hugepages.md`](32-memory-prefetch-and-hugepages.md) | 预取与大页 |
| 33 | [`33-nbd-and-rootfs.md`](33-nbd-and-rootfs.md) | 磁盘：NBD 服务器与 rootfs |
| 34 | [`34-template-cache-and-local-storage.md`](34-template-cache-and-local-storage.md) | 模板缓存与本地存储 |
| 35 | [`35-sandbox-networking.md`](35-sandbox-networking.md) | 沙箱网络 |
| 36 | [`36-orchestrator-proxy-and-envd-client.md`](36-orchestrator-proxy-and-envd-client.md) | 代理与 envd 通信 |
| 37 | [`37-pause-and-snapshot.md`](37-pause-and-snapshot.md) | Pause：脏页判定与差分导出 |
| 38 | [`38-cgroups-and-host-stats.md`](38-cgroups-and-host-stats.md) | cgroup、资源记账与主机统计 |
| 39 | [`39-health-errors-and-teardown.md`](39-health-errors-and-teardown.md) | 健康检查、错误语义与清理 |
| 40 | [`40-volumes-and-nfsproxy.md`](40-volumes-and-nfsproxy.md) | Volumes 与 NFS proxy |

### 第五部分　模板构建

| # | 文档 | 内容 |
|---|---|---|
| 41 | [`41-template-build-overview.md`](41-template-build-overview.md) | 构建总览：从 Dockerfile 到可恢复的快照 |
| 42 | [`42-build-phases.md`](42-build-phases.md) | 阶段流水线 |
| 43 | [`43-rootfs-construction.md`](43-rootfs-construction.md) | rootfs 制作 |
| 44 | [`44-build-sandbox-and-commands.md`](44-build-sandbox-and-commands.md) | 构建期沙箱与命令 |
| 45 | [`45-layers-and-build-cache.md`](45-layers-and-build-cache.md) | 层与构建缓存 |
| 46 | [`46-template-manager-service.md`](46-template-manager-service.md) | template-manager 服务 |
| 47 | [`47-orchestrator-dev-tools.md`](47-orchestrator-dev-tools.md) | 本地开发工具（cmd/） |

### 第六部分　envd：沙箱内守护进程

| # | 文档 | 内容 |
|---|---|---|
| 48 | [`48-envd-overview.md`](48-envd-overview.md) | envd 总览 |
| 49 | [`49-envd-process-service.md`](49-envd-process-service.md) | 进程服务 |
| 50 | [`50-envd-filesystem-service.md`](50-envd-filesystem-service.md) | 文件系统服务与文件接口 |
| 51 | [`51-envd-ports-permissions-metrics.md`](51-envd-ports-permissions-metrics.md) | 端口、权限与指标 |
| 52 | [`52-envd-legacy-and-sdk-compat.md`](52-envd-legacy-and-sdk-compat.md) | legacy 服务与 SDK 兼容 |

### 第七部分　边缘与流量

| # | 文档 | 内容 |
|---|---|---|
| 53 | [`53-client-proxy-edge.md`](53-client-proxy-edge.md) | client-proxy（edge） |
| 54 | [`54-shared-proxy-library.md`](54-shared-proxy-library.md) | 共享代理库 |
| 55 | [`55-sandbox-catalog-and-routing.md`](55-sandbox-catalog-and-routing.md) | 沙箱目录与跨节点路由 |
| 56 | [`56-edge-api.md`](56-edge-api.md) | edge API |
| 57 | [`57-docker-reverse-proxy.md`](57-docker-reverse-proxy.md) | docker-reverse-proxy |

### 第八部分　数据与可观测

| # | 文档 | 内容 |
|---|---|---|
| 58 | [`58-postgres-schema-and-migrations.md`](58-postgres-schema-and-migrations.md) | Postgres 模式与迁移 |
| 59 | [`59-clickhouse.md`](59-clickhouse.md) | ClickHouse |
| 60 | [`60-telemetry.md`](60-telemetry.md) | 遥测：tracing、metrics、logs |
| 61 | [`61-events-and-webhooks.md`](61-events-and-webhooks.md) | 沙箱事件与 webhook |
| 62 | [`62-testing.md`](62-testing.md) | 测试体系 |

### 第九部分　上游的部署与开发

| # | 文档 | 内容 |
|---|---|---|
| 63 | [`63-gcp-terraform.md`](63-gcp-terraform.md) | GCP 上的部署 |
| 64 | [`64-nomad-jobs.md`](64-nomad-jobs.md) | Nomad job 详解 |
| 65 | [`65-build-and-release.md`](65-build-and-release.md) | 构建与发布 |
| 66 | [`66-local-development.md`](66-local-development.md) | 本地开发环境 |

### 第十部分　ARM 适配版

| # | 文档 | 内容 |
|---|---|---|
| 67 | [`67-arm-port-overview.md`](67-arm-port-overview.md) | ARM 适配总览 |
| 68 | [`68-aarch64-virtualization-differences.md`](68-aarch64-virtualization-differences.md) | aarch64 与 x86 的虚拟化差异 |
| 69 | [`69-guest-kernel-for-arm.md`](69-guest-kernel-for-arm.md) | guest 内核 |
| 70 | [`70-firecracker-fork.md`](70-firecracker-fork.md) | e2b 的 Firecracker 分叉与 ARM 构建 |
| 71 | [`71-orchestrator-arm-fc-changes.md`](71-orchestrator-arm-fc-changes.md) | orchestrator 的 ARM 改动 I：FC 启动、超时与并发 |
| 72 | [`72-uffd-on-arm.md`](72-uffd-on-arm.md) | orchestrator 的 ARM 改动 II：写保护退化 |
| 73 | [`73-cgroup-and-host-compat.md`](73-cgroup-and-host-compat.md) | orchestrator 的 ARM 改动 III：宿主兼容 |
| 74 | [`74-template-build-on-arm.md`](74-template-build-on-arm.md) | 模板构建的 ARM 改动 |
| 75 | [`75-minio-storage.md`](75-minio-storage.md) | MinIO 存储 provider |
| 76 | [`76-k8s-discovery.md`](76-k8s-discovery.md) | Kubernetes 服务发现 |
| 77 | [`77-api-and-flags-on-arm.md`](77-api-and-flags-on-arm.md) | API 层与特性开关默认值的调整 |
| 78 | [`78-helm-k8s-deployment.md`](78-helm-k8s-deployment.md) | 部署形态一：Helm / Kubernetes |
| 79 | [`79-nomad-multinode-deployment.md`](79-nomad-multinode-deployment.md) | 部署形态二：Nomad 多节点 |
| 80 | [`80-single-node-rpm.md`](80-single-node-rpm.md) | 部署形态三：单机离线 RPM |
| 81 | [`81-single-node-traffic.md`](81-single-node-traffic.md) | 单机流量架构 |
| 82 | [`82-host-kernel-nbd-hugepages.md`](82-host-kernel-nbd-hugepages.md) | 宿主内核要求与调优 |
| 83 | [`83-sdk-adaptation.md`](83-sdk-adaptation.md) | SDK 侧适配 |
| 84 | [`84-arm-performance.md`](84-arm-performance.md) | ARM 性能实测 |
| 85 | [`85-dev-workflow-and-packaging.md`](85-dev-workflow-and-packaging.md) | 开发与出包工作流 |
| 86 | [`86-known-issues-and-debt.md`](86-known-issues-and-debt.md) | 已知问题与技术债 |
| 87 | [`87-beyond-checkpoint-restore.md`](87-beyond-checkpoint-restore.md) | 后续功能开发：checkpoint / restore 与展望 |

### 附录

| # | 文档 | 内容 |
|---|---|---|
| 88 | [`88-glossary.md`](88-glossary.md) | 术语表 |
| 89 | [`89-code-map.md`](89-code-map.md) | 代码地图 |
| 90 | [`90-config-reference.md`](90-config-reference.md) | 环境变量与配置项总表 |
| 91 | [`91-ports-paths-keys.md`](91-ports-paths-keys.md) | 端口、路径与存储键总表 |

---

## 相关手册

- checkpoint / restore（沙箱活着时的高频快速回滚）：[`../../e2b-infra-docs/rollback/docs/`](../../e2b-infra-docs/rollback/docs/README.md)
- 单机离线部署操作手册：[`../../e2b-infra/single-node-offline-deploy.md`](../../e2b-infra/single-node-offline-deploy.md)；
  逐脚本讲解：[`../../e2b-infra/deploy-docs/`](../../e2b-infra/deploy-docs/README.md)
