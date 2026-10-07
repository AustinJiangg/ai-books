# 89 · 代码地图

> 把四个仓库的目录、ARM 补丁的 94 个文件、以及各处已知的残留代码，一一对到本书的篇目上。
> 读代码时从这里查「这个目录归哪一篇讲」，读书时从这里查「这一篇对应哪些代码」。
>
> **读者**：所有需要在代码与本书之间来回跳的读者。 　**预备**：无，可随时查阅。
> 　**代码**：`tmp/e2b-book-src/upstream/` 的目录树、`git diff f8c2f0cde fbee6fcd1`、`fc-kernels-arm/`、`e2b-infra/`、`e2b-arm/`

---

## 0. 怎么用这张地图

本篇是索引，不是叙述。四张表回答四个不同的问题。

第 1 节按上游 2026.09 的目录树排列：`packages/*` 的十三个目录展开到二级或三级，
另加 `iac/`、`spec/`、`tests/`、`scripts/`、`.github/`。每行一句话职责，加上讲解它的篇目。
一个目录可能对应多篇，也可能一篇都没有 —— 后一种情况在表里写「未展开」，
说明本书没有专门讲它，而不是它不存在。

第 2 节按 ARM 补丁的文件排列。分类沿用[第 67 篇 §3](67-arm-port-overview.md#3-改动地图)的五类
（A 架构相关、B guest 发行版相关、C 部署环境替换、D 参数放宽与兼容降级、E 可观测埋点），
判据也是那一节的判据：去掉这条改动，系统在什么条件下会坏。
文件按补丁里的路径顺序分组，不按类别顺序，方便对着 `git diff --stat` 的输出逐行核对。

第 3 节是 infra 之外的三个仓库：分叉 Firecracker、fc-kernels 的 arm64 配置、
单机离线版的 `e2b-infra`，以及 SDK 侧的 `e2b-arm`。这些仓库的代码量远小于 infra，
但它们决定了最终交付物的形状。

第 4 节是「残留与孤儿」：本书各篇在读代码时发现的、仓库里存在但没有调用方或没有读取方的东西。
它们不是 bug，多数是演进过程中留下的旧路径。把它们集中列出来，是为了让后来的读者
在遇到某个看起来重要、搜遍全仓库却找不到调用点的符号时，能先在这里确认一下。
需要修的那些进入[第 86 篇 · 已知问题与技术债](86-known-issues-and-debt.md)，本节只负责登记。

链接的约定：表里的篇号即链接，指向那一篇的文件；论断落在某一节时带上小节锚点。

---

## 1. 上游 2026.09 的目录

### 1.1 packages/api —— REST API 服务

| 目录 | 职责 | 篇目 |
|---|---|---|
| `packages/api/main.go`、`internal/cfg` | 进程装配、配置读取、依赖注入顺序 | [15](15-api-service-structure.md) |
| `internal/api` | 由 `spec/openapi.yml` 生成的类型与路由骨架 | [15](15-api-service-structure.md)、[17](17-sandbox-create-api.md) |
| `internal/handlers` | 全部 HTTP 处理器；`store.go` 是共享依赖容器 | [17](17-sandbox-create-api.md)、[18](18-sandbox-lifecycle-api.md)、[22](22-template-api.md)、[24](24-api-metrics-and-analytics.md) |
| `internal/auth`、`internal/middleware` | 鉴权中间件挂载、请求体上限、限流位（无速率限流） | [16](16-auth-and-multitenancy.md) |
| `internal/orchestrator` | 节点池、放置、生命周期与到期驱逐 | [19](19-node-management-and-placement.md)、[18](18-sandbox-lifecycle-api.md) |
| `internal/orchestrator/nodemanager` | 单个 orchestrator 节点的连接、状态与构建缓存视图 | [19](19-node-management-and-placement.md) |
| `internal/orchestrator/placement` | best-of-K 放置算法与打分 | [19](19-node-management-and-placement.md) |
| `internal/orchestrator/placement/cpu_compatibility.go` | 放置前的机器画像过滤：`isNodeCPUCompatible()`，build 的 `CPUArchitecture` 为空即放行 | [19](19-node-management-and-placement.md)、[73](73-cgroup-and-host-compat.md) |
| `internal/orchestrator/evictor` | 沙箱到期后的驱逐循环 | [18](18-sandbox-lifecycle-api.md) |
| `internal/sandbox` | 沙箱运行态对象与状态机（`states.go`） | [20](20-sandbox-state-storage.md) |
| `internal/sandbox/storage`（`memory`、`redis`、`populate_redis`） | 三种运行态后端，`memory` 装配下带 Redis 影子写 | [20](20-sandbox-state-storage.md)、[13](13-storage-landscape.md) |
| `internal/sandbox/reservations`（含 `redis`） | 创建期的名额预留，防止同一节点被打爆 | [19](19-node-management-and-placement.md) |
| `internal/clusters`（含 `discovery/local.go`、`mocks`） | 多集群注册表与本地集群发现 | [21](21-clusters-and-discovery.md) |
| `internal/template-manager` | 向 template-manager 发起构建、轮询状态 | [23](23-template-manager-client.md) |
| `internal/template`、`internal/team`、`internal/cache` | 模板元数据、团队配额、进程内缓存 | [22](22-template-api.md)、[16](16-auth-and-multitenancy.md) |
| `internal/db` | 对 `packages/db` 的薄封装 | [58](58-postgres-schema-and-migrations.md) |
| `internal/analytics_collector`、`internal/metrics` | 分析事件外发与 API 自身指标 | [24](24-api-metrics-and-analytics.md) |
| `internal/constants`、`internal/utils` | 常量与工具 | 未展开 |

### 1.2 packages/orchestrator —— 沙箱运行时与模板构建

| 目录 | 职责 | 篇目 |
|---|---|---|
| `main.go`、`internal/cfg`、`internal/service` | 进程装配、服务身份、机器信息探测 | [25](25-orchestrator-process.md) |
| `internal/server` | gRPC 服务端：Create / Resume / Pause / Kill 与并发闸门 | [25](25-orchestrator-process.md)、[27](27-resume-sandbox.md) |
| `internal/sandbox`（`sandbox.go`、`map.go`、`cleanup.go`） | Sandbox 对象、Factory、注册表与清理链 | [26](26-sandbox-object.md)、[27](27-resume-sandbox.md) |
| `internal/sandbox/fc` | Firecracker 进程的启动、配置、快照与恢复 | [28](28-firecracker-process-management.md) |
| `internal/sandbox/uffd`（`userfaultfd`、`memory`、`prefetch`、`fdexit`） | 用户态缺页服务、内存映射与预取 | [31](31-uffd-memory-backend.md)、[32](32-memory-prefetch-and-hugepages.md) |
| `internal/sandbox/block`（含 `metrics`） | 块设备抽象：Cache、Overlay、Storage 三层 | [30](30-block-layer.md) |
| `internal/sandbox/nbd`（含 `testutils`） | NBD 设备池与内核块设备对接 | [33](33-nbd-and-rootfs.md) |
| `internal/sandbox/rootfs` | rootfs 的 overlay 组装 | [33](33-nbd-and-rootfs.md) |
| `internal/sandbox/template`、`internal/sandbox/build` | 模板产物的本地缓存与打开 | [34](34-template-cache-and-local-storage.md) |
| `internal/sandbox/network` | 网络槽位、netns、tap、防火墙与 TCP 代理 | [35](35-sandbox-networking.md) |
| `internal/sandbox/cgroup` | 宿主侧 cgroup v2 记账 | [38](38-cgroups-and-host-stats.md) |
| `internal/sandbox/socket` | 等待 Firecracker 的 API socket 就绪 | [28](28-firecracker-process-management.md) |
| `internal/sandbox/envd`、`envd.go` | 与沙箱内 envd 的初始化与健康交互 | [36](36-orchestrator-proxy-and-envd-client.md) |
| `internal/sandbox/checks.go`、`health.go` | 周期健康检查与不健康判定 | [39](39-health-errors-and-teardown.md) |
| `internal/sandbox/snapshot.go`、`diffcreator.go` | pause 产物的生成与差分 | [37](37-pause-and-snapshot.md) |
| `internal/sandbox/hoststats*.go`、`internal/metrics` | 宿主与沙箱指标采集 | [38](38-cgroups-and-host-stats.md) |
| `internal/proxy` | 节点内到各沙箱 envd 的反向代理 | [36](36-orchestrator-proxy-and-envd-client.md) |
| `internal/template/build`（`phases`、`layer`、`core`、`commands`、`storage` 等） | 模板构建的阶段机、层缓存与 rootfs 构造 | [41](41-template-build-overview.md)–[45](45-layers-and-build-cache.md) |
| `internal/template/server`、`internal/template/cache`、`internal/template/metadata` | template-manager 的 gRPC 服务端与构建缓存 | [46](46-template-manager-service.md) |
| `internal/nfsproxy`（含 `mocks`）、`internal/volumes` | 团队卷的 NFS 代理与卷服务 | [40](40-volumes-and-nfsproxy.md) |
| `internal/portmap`、`internal/tcpfirewall` | 端口映射服务与 TCP 层防火墙 | [35](35-sandbox-networking.md) |
| `internal/hyperloopserver` | 沙箱内可访问的宿主小服务 | [48](48-envd-overview.md) |
| `internal/healthcheck`、`internal/factories`、`internal/events` | 健康端点、cmux/HTTP 工厂、事件发送 | [25](25-orchestrator-process.md)、[61](61-events-and-webhooks.md) |
| `cmd/*`（12 个子命令） | 离线调试工具：inspect-build、resume-build、hammer-file 等 | [47](47-orchestrator-dev-tools.md) |
| `scripts/` | 构建与打包辅助脚本 | [65](65-build-and-release.md) |

### 1.3 packages/envd —— 沙箱内守护进程

| 目录 | 职责 | 篇目 |
|---|---|---|
| `main.go`、`internal/api` | HTTP 面：`/init`、`/files`、`/envs`、鉴权与签名 | [48](48-envd-overview.md)、[50](50-envd-filesystem-service.md) |
| `spec/process`、`spec/filesystem` | Connect-RPC 的 proto 定义 | [49](49-envd-process-service.md)、[50](50-envd-filesystem-service.md) |
| `internal/services/process`（含 `handler`） | 进程启动、PTY、信号与流式输出 | [49](49-envd-process-service.md) |
| `internal/services/filesystem` | 文件读写、监听与目录操作 | [50](50-envd-filesystem-service.md) |
| `internal/services/cgroups` | guest 内的 cgroup 权重设置 | [51](51-envd-ports-permissions-metrics.md) |
| `internal/services/legacy` | 旧版 SDK 的兼容端点 | [52](52-envd-legacy-and-sdk-compat.md) |
| `internal/port`、`internal/permissions` | 端口扫描上报、用户与权限 | [51](51-envd-ports-permissions-metrics.md) |
| `internal/host` | MMDS 读取与宿主元数据 | [48](48-envd-overview.md) |
| `internal/logs`、`internal/execcontext`、`internal/utils` | 日志外发、执行上下文、工具 | [51](51-envd-ports-permissions-metrics.md) |

### 1.4 packages/shared —— 跨服务公共库

| 目录 | 职责 | 篇目 |
|---|---|---|
| `pkg/storage`（含 `header`、`lock`、`mocks`） | 对象存储抽象、模板产物读写、映射表格式、分片缓存 | [13](13-storage-landscape.md)、[29](29-template-artifact-format.md) |
| `pkg/proxy` | 反向代理框架：连接池、错误页、host 解析 | [54](54-shared-proxy-library.md) |
| `pkg/sandbox-catalog` | 沙箱位置目录，供 edge 定址 | [55](55-sandbox-catalog-and-routing.md) |
| `pkg/sandbox-network` | 默认拒绝网段与防火墙规则定义 | [02](02-why-sandbox.md)、[35](35-sandbox-networking.md) |
| `pkg/clusters`、`pkg/clusters/discovery` | 集群模型与 Nomad 服务发现 | [21](21-clusters-and-discovery.md) |
| `pkg/http`、`pkg/http/edge` | HTTP 服务骨架与 edge API 的生成客户端 | [56](56-edge-api.md) |
| `pkg/grpc` | gRPC 服务端与客户端的公共配置 | [08](08-go-service-toolkit.md)、[25](25-orchestrator-process.md) |
| `pkg/feature-flags` | LaunchDarkly 驱动的特性开关与数值 flag | [14](14-config-flags-versions.md) |
| `pkg/env`、`pkg/consts` | 环境变量读取与全局常量 | [14](14-config-flags-versions.md)、[10](10-system-architecture.md) |
| `pkg/telemetry`、`pkg/logger`、`pkg/logs` | OpenTelemetry、结构化日志与沙箱日志 | [60](60-telemetry.md) |
| `pkg/events`、`pkg/edge` | 沙箱事件的定义与投递 | [61](61-events-and-webhooks.md) |
| `pkg/keys`、`pkg/id` | API key 的生成与哈希、各类 ID | [16](16-auth-and-multitenancy.md)、[11](11-object-model.md) |
| `pkg/artifacts-registry`、`pkg/dockerhub` | 镜像仓库抽象（GCP / Local）与 Docker Hub 拉取 | [57](57-docker-reverse-proxy.md)、[43](43-rootfs-construction.md) |
| `pkg/fc` | 由 `firecracker.yml` 生成的 Firecracker API 客户端与模型 | [03](03-firecracker-primer.md)、[28](28-firecracker-process-management.md) |
| `pkg/redis`、`pkg/factories` | Redis 客户端与工厂 | [20](20-sandbox-state-storage.md) |
| `pkg/cache`、`pkg/smap`、`pkg/utils`、`pkg/ioutils` | 通用缓存、并发 map、Promise / ErrorOnce 等工具 | [08](08-go-service-toolkit.md) |
| `pkg/limit`、`pkg/connlimit` | 上传限速与连接数上限 | [35](35-sandbox-networking.md)、[13](13-storage-landscape.md) |
| `pkg/synchronization` | 周期同步循环的通用骨架 | [19](19-node-management-and-placement.md) |
| `pkg/machineinfo`、`pkg/health` | 机器信息与健康状态类型 | [25](25-orchestrator-process.md) |
| `pkg/templates` | 模板版本与能力门槛常量 | [14](14-config-flags-versions.md) |
| `pkg/apierrors` | HTTP 错误的统一形状 | [15](15-api-service-structure.md) |

### 1.5 其余 packages

| 目录 | 职责 | 篇目 |
|---|---|---|
| `packages/auth` | 独立 Go module：API key 与 access token 的认证 | [16](16-auth-and-multitenancy.md) |
| `packages/db`（`migrations`、`queries`、`pkg`、`client`、`schema`、`scripts`） | PostgreSQL 迁移、sqlc 查询、连接池与重试 | [58](58-postgres-schema-and-migrations.md)、[11](11-object-model.md) |
| `packages/clickhouse`（`migrations`、`pkg/batcher`、`pkg/events`、`pkg/hoststats`） | 指标与事件的列存写入与批处理 | [59](59-clickhouse.md) |
| `packages/client-proxy` | 边缘代理进程：按域名定址到沙箱 | [53](53-client-proxy-edge.md)、[55](55-sandbox-catalog-and-routing.md) |
| `packages/docker-reverse-proxy` | 模板构建期的镜像仓库鉴权代理 | [57](57-docker-reverse-proxy.md) |
| `packages/dashboard-api` | 面向 dashboard 的独立 API 进程 | 未展开（[01](01-e2b-ecosystem.md) 提及） |
| `packages/nomad-nodepool-apm` | Nomad autoscaler 的节点池 APM 插件 | [64](64-nomad-jobs.md) |
| `packages/otel-collector` | OpenTelemetry collector 的配置与测试 | [60](60-telemetry.md) |
| `packages/local-dev` | 本地开发用的 docker-compose、Grafana / Mimir / Tempo 配置与种子数据 | [66](66-local-development.md) |

### 1.6 仓库级目录

| 目录 / 文件 | 职责 | 篇目 |
|---|---|---|
| `iac/provider-gcp`（`main.tf`、`api.tf`、`variables.tf` 等） | GCP 上的整套基础设施定义 | [63](63-gcp-terraform.md) |
| `iac/provider-gcp/init` | 项目初始化：API 启用、状态桶 | [63](63-gcp-terraform.md) |
| `iac/provider-gcp/nomad-cluster`、`nomad-cluster-disk-image` | 集群机器组、启动脚本与 Packer 节点镜像 | [63](63-gcp-terraform.md)、[09](09-nomad-consul-terraform.md) |
| `iac/provider-gcp/nomad/jobs` | 留在 provider 下的 job：api、redis、template-manager、docker-reverse-proxy、nomad-autoscaler、clean-nfs-cache | [64](64-nomad-jobs.md) |
| `iac/provider-gcp/redis`、`remote-repository` | Redis 实例与镜像仓库 | [63](63-gcp-terraform.md) |
| `iac/modules/job-*`（9 个） | 与 provider 解耦的 job 模块：orchestrator、client-proxy、clickhouse、loki、ingress、otel-collector 等 | [64](64-nomad-jobs.md) |
| `iac/provider-aws` | 只有一个 `Makefile`，无实质资源 | 未展开 |
| `spec/openapi.yml` | 主 REST API 的契约，生成 api 的类型与路由 | [17](17-sandbox-create-api.md)、[22](22-template-api.md) |
| `spec/openapi-edge.yml` | edge API 契约，仓库内只生成客户端 | [56](56-edge-api.md) |
| `spec/openapi-dashboard.yml`、`openapi-hyperloop.yml` | dashboard-api 与 hyperloop 的契约 | [56](56-edge-api.md)（简述） |
| `tests/integration` | Go 写的端到端集成测试与种子数据 | [62](62-testing.md) |
| `tests/periodic-test` | 周期巡检，目前只有时钟同步一项 | [62](62-testing.md) |
| `scripts/` | 版本递增、迁移时间戳检查、依赖完整性等辅助脚本 | [65](65-build-and-release.md) |
| `.github/workflows`（17 个） | 构建、部署、lint、测试与 OpenAPI 校验流水线 | [62](62-testing.md)、[65](65-build-and-release.md) |
| `.github/actions`（7 个） | 复合 action：build-packages、host-init、start-services 等 | [65](65-build-and-release.md)、[66](66-local-development.md) |
| `go.work`、`Makefile`、`VERSION`、`.mockery.yaml`、`.golangci.yml` | 工作区、顶层构建入口、版本串、mock 与 lint 配置 | [01](01-e2b-ecosystem.md)、[65](65-build-and-release.md) |
| `DEV.md`、`DEV-LOCAL.md`、`self-host.md`、`.devcontainer` | 开发与自托管文档 | [66](66-local-development.md) |

---

## 2. ARM 补丁的 94 个文件

以下按 `git diff --stat f8c2f0cde fbee6fcd1` 的输出顺序列出，路径省略仓库根前缀。
「性质」列的字母是[第 67 篇 §3](67-arm-port-overview.md#3-改动地图)的五类；
一个文件身兼两职时写成 `A/D` 的形式，前者是主要性质。

### 2.1 流水线与二进制

| 文件 | 性质 | 改动 | 篇目 |
|---|---|---|---|
| `.github/actions/host-init/init-client.sh` | C | 去 GCP 化的宿主初始化；大页节点改走 `hugepages-2048kB`，被单机离线版复用 | [80](80-single-node-rpm.md)、[82](82-host-kernel-nbd-hugepages.md) |
| `bin/orchestrator` | C | 直接提交进树的编译产物，供启动脚本拷贝为 orchestrator 与 template-manager | [67](67-arm-port-overview.md)、[86](86-known-issues-and-debt.md) |

### 2.2 helm/（全部新增，13 个文件）

| 文件 | 性质 | 改动 | 篇目 |
|---|---|---|---|
| `helm/Chart.yaml`、`helm/values-template.yaml` | C | chart 元数据与待渲染的值模板 | [78](78-helm-k8s-deployment.md) |
| `helm/templates/orchestrator.yaml` | C | orchestrator 以 DaemonSet 形式跑在每个节点 | [78](78-helm-k8s-deployment.md) |
| `helm/templates/template-manager.yaml` | C | 模板构建服务的 Deployment | [78](78-helm-k8s-deployment.md) |
| `helm/templates/api.yaml`、`edge.yaml` | C | api 与 edge 的 Deployment 与 Service | [78](78-helm-k8s-deployment.md) |
| `helm/templates/rbac-orchestrator.yaml` | C | orchestrator 读取节点与 Pod 所需的 RBAC | [76](76-k8s-discovery.md)、[78](78-helm-k8s-deployment.md) |
| `helm/templates/redis.yaml`、`clickhouse.yaml`、`loki.yaml` | C | 依赖组件的 in-cluster 部署 | [78](78-helm-k8s-deployment.md) |
| `helm/templates/otel-collector.yaml`、`logs-collector.yaml` | C | 可观测链路的采集端 | [78](78-helm-k8s-deployment.md)、[60](60-telemetry.md) |

### 2.3 iac/（Nomad 形态去 GCP 化，20 个文件）

| 文件 | 性质 | 改动 | 篇目 |
|---|---|---|---|
| `iac/provider-gcp/nomad-cluster-disk-image/setup/install-consul.sh`、`install-nomad.sh` | C | 从本地包安装，去掉外网下载 | [79](79-nomad-multinode-deployment.md) |
| `iac/provider-gcp/nomad-cluster-disk-image/setup/nomad.service` | C | 新增的 systemd 单元 | [79](79-nomad-multinode-deployment.md) |
| `iac/provider-gcp/nomad-cluster/scripts/run-consul.sh`、`run-nomad.sh` | C | 整脚本重写，去掉 GCP 元数据服务依赖 | [79](79-nomad-multinode-deployment.md) |
| `iac/provider-gcp/nomad-cluster/scripts/start-client.sh`、`start-server.sh` | C | 去掉 GCP 磁盘挂载与 `gsutil`，就地取二进制 | [79](79-nomad-multinode-deployment.md)、[80](80-single-node-rpm.md) |
| `iac/provider-gcp/nomad-cluster/scripts/uninstall-consul.sh`、`uninstall-nomad.sh` | C | 新增卸载脚本 | [79](79-nomad-multinode-deployment.md) |
| `iac/provider-gcp/nomad/jobs/deploy.sh`、`env.template` | C | 新增：用 `envsubst` 渲染 job 并按条件删块 | [79](79-nomad-multinode-deployment.md) |
| `iac/provider-gcp/nomad/jobs/api.hcl`、`redis.hcl`、`template-manager.hcl` | C | 改为读 `.env`、去掉 GCP 专有变量 | [79](79-nomad-multinode-deployment.md)、[64](64-nomad-jobs.md) |
| `iac/provider-gcp/nomad/jobs/orchestrator.hcl`、`edge.hcl`、`clickhouse.hcl`、`loki.hcl`、`otel-collector.hcl`、`logs-collector.hcl` | C | 新增：把上游 `iac/modules/job-*` 里的 job 落到 provider 目录 | [79](79-nomad-multinode-deployment.md)、[64](64-nomad-jobs.md) |

### 2.4 构建方式（Dockerfile 与 Makefile，11 个文件）

| 文件 | 性质 | 改动 | 篇目 |
|---|---|---|---|
| `packages/{api,clickhouse,client-proxy,db,envd,orchestrator}/Makefile` | A/C | 去掉写死的 `GOARCH=amd64` 与 `--platform linux/amd64`；envd 按 `uname -m` 推导 | [85](85-dev-workflow-and-packaging.md) |
| `packages/{api,clickhouse,client-proxy,db,orchestrator}/Dockerfile` | C | 由多阶段交叉编译 + `FROM scratch` 改为拷贝已编译二进制 + `FROM ubuntu:24.04` | [85](85-dev-workflow-and-packaging.md)、[80](80-single-node-rpm.md) |

### 2.5 packages/api 与 packages/shared 的服务发现改造（16 个文件）

| 文件 | 性质 | 改动 | 篇目 |
|---|---|---|---|
| `shared/pkg/clusters/discovery/interface.go` | C | 新增 `ServiceDiscovery` 接口与 `Allocation` 结构 | [76](76-k8s-discovery.md) |
| `shared/pkg/clusters/discovery/k8s.go` | C | 新增：用 Kubernetes API 列 Pod 作为节点来源 | [76](76-k8s-discovery.md) |
| `shared/pkg/clusters/discovery/nomad.go` | C | 改为实现新接口 | [76](76-k8s-discovery.md) |
| `api/internal/orchestrator/discovery.go`、`k8s_discovery.go`、`nomad_discovery.go` | C | 按 `ORCHESTRATOR_TYPE` 分派两种发现方式 | [76](76-k8s-discovery.md) |
| `api/internal/orchestrator/client.go`、`orchestrator.go`、`lifecycle.go` | C | 节点连接与同步循环改用抽象后的发现结果 | [76](76-k8s-discovery.md) |
| `api/internal/clusters/cluster.go`、`clusters_sync.go`、`instance.go`、`discovery/local.go` | C | 本地集群的实例来源随之调整 | [76](76-k8s-discovery.md)、[21](21-clusters-and-discovery.md) |
| `api/internal/handlers/store.go`、`api/main.go` | C | 装配处新的构造参数 | [76](76-k8s-discovery.md) |
| `api/go.mod`、`go.sum`、`shared/go.mod`、`go.sum`、`orchestrator/go.mod`、`go.sum` | C | 引入 `client-go` 与 MinIO SDK 依赖 | [76](76-k8s-discovery.md)、[75](75-minio-storage.md) |

### 2.6 对象存储与开关（3 个文件）

| 文件 | 性质 | 改动 | 篇目 |
|---|---|---|---|
| `shared/pkg/storage/storage_minio.go` | C | 新增 300 行的 MinIO provider | [75](75-minio-storage.md) |
| `shared/pkg/storage/storage.go` | C | 新增 `MinioBucket`，默认 provider 由 `GCPBucket` 改为它 | [75](75-minio-storage.md)、[13](13-storage-landscape.md) |
| `shared/pkg/feature-flags/flags.go` | C/D | Firecracker 版本常量改 `v1.13.1`；四个数值 flag 放大 | [77](77-api-and-flags-on-arm.md)、[70](70-firecracker-fork.md) |

### 2.7 架构相关（A 类）

| 文件 | 性质 | 改动 | 篇目 |
|---|---|---|---|
| `orchestrator/internal/sandbox/fc/process.go` | A/D/E | 五个 x86 内核参数按 `runtime.GOARCH` 下发；`CLONE_INTO_CGROUP` 整段注释掉；插入恢复阶段耗时日志 | [71](71-orchestrator-arm-fc-changes.md) |
| `orchestrator/internal/sandbox/fc/client.go` | A | `smt` 由 `true` 改 `false`；去掉 `TrackDirtyPages` 字段 | [71](71-orchestrator-arm-fc-changes.md)、[68](68-aarch64-virtualization-differences.md) |
| `orchestrator/internal/sandbox/uffd/userfaultfd/userfaultfd.go` | A | 读缺页的 `UFFDIO_COPY_MODE_WP` 三行注释掉 | [72](72-uffd-on-arm.md) |
| `orchestrator/internal/service/machineinfo/main.go` | A | arm64 上 `gopsutil` 读不到 CPU 字段时回退为 `arm64` / `0` | [73](73-cgroup-and-host-compat.md) |
| `orchestrator/.../build/core/systeminit/busybox.go` | A | `go:embed` 按 `runtime.GOARCH` 在两份二进制间选择 | [74](74-template-build-on-arm.md) |
| `orchestrator/.../systeminit/busybox_1.35_arm64`、`busybox_1.36.1-2_arm64` | A | 新增的 arm64 busybox 位；补丁树里是 3611 字节的 HTML 占位，真实二进制由 RPM 的 `%prep` 覆盖 | [74](74-template-build-on-arm.md)、[80](80-single-node-rpm.md) |
| `orchestrator/.../build/core/oci/oci.go` | A | `DefaultPlatform.Architecture` 由 `amd64` 改 `arm64` | [74](74-template-build-on-arm.md) |

### 2.8 guest 发行版相关（B 类）

| 文件 | 性质 | 改动 | 篇目 |
|---|---|---|---|
| `orchestrator/.../build/phases/base/provision.sh` | B | 按 `/etc/os-release` 的 `ID` 在 `dnf` 与 `apt-get` 之间分支，包列表随之调整 | [74](74-template-build-on-arm.md) |
| `orchestrator/.../build/phases/finalize/configure.sh` | B | 解释器改 `#!/bin/sh`，用户与组创建改用 openEuler 上存在的形式 | [74](74-template-build-on-arm.md) |
| `orchestrator/.../build/commands/user.go` | B | 与 `configure.sh` 同款的发行版分支 | [74](74-template-build-on-arm.md) |
| `orchestrator/.../rootfs/files/envd.service.tpl` | B | 删掉 6 行 cgroup 相关的 systemd 指令 | [74](74-template-build-on-arm.md) |
| `orchestrator/.../rootfs/files/inittab.tpl` | B | 一行换行修正 | [74](74-template-build-on-arm.md) |

### 2.9 参数放宽与兼容降级（D 类）

| 文件 | 性质 | 改动 | 篇目 |
|---|---|---|---|
| `orchestrator/internal/sandbox/checks.go` | D | 健康检查间隔 20 s → 300 s，超时 100 ms → 60000 ms | [73](73-cgroup-and-host-compat.md)、[39](39-health-errors-and-teardown.md) |
| `orchestrator/internal/sandbox/uffd/uffd.go` | D | `uffdMsgListenerTimeout` 10 s → 120 s | [72](72-uffd-on-arm.md) |
| `orchestrator/internal/sandbox/socket/socket.go` | D | 新增 300 s 上限，可由 `SOCKET_WAIT_TIMEOUT_SECONDS` 覆盖；`Wait` 改用 `context.Background()` | [71](71-orchestrator-arm-fc-changes.md) |
| `orchestrator/internal/server/sandboxes.go` | D | 请求超时 60 s → 300 s、获取超时 15 s → 300 s、每节点并发 3 → 30、`TryAcquire` 改带超时的 `Acquire` | [71](71-orchestrator-arm-fc-changes.md) |
| `orchestrator/internal/server/main.go` | D | 并发上限改为可由 `MAX_STARTING_INSTANCES_PER_NODE` 覆盖 | [71](71-orchestrator-arm-fc-changes.md) |
| `orchestrator/internal/sandbox/network/pool.go` | D/E | 新槽位池 32 → 300、复用池 100 → 1000；加一行池水位日志 | [71](71-orchestrator-arm-fc-changes.md)、[35](35-sandbox-networking.md) |
| `orchestrator/internal/sandbox/cgroup/manager.go` | D | 无 cgroup v2 时不再报错，返回空实现；`Initialize` 在 v1 上跳过 | [73](73-cgroup-and-host-compat.md) |
| `orchestrator/internal/sandbox/block/cache.go` | D | `WriteAtWithoutLock` 加 `recover`、mmap 空指针与偏移范围检查 | [73](73-cgroup-and-host-compat.md)、[30](30-block-layer.md) |
| `shared/pkg/grpc/server.go` | D | `MaxConcurrentStreams(1000)`，`MaxConnectionAge` / `MaxConnectionIdle` 显式置 0 | [77](77-api-and-flags-on-arm.md) |
| `envd/internal/host/mmds.go` | D | `DisableKeepAlives` 由 `true` 改为保留连接，`MaxIdleConns` 10、`IdleConnTimeout` 90 s | [77](77-api-and-flags-on-arm.md)、[48](48-envd-overview.md) |
| `api/internal/sandbox/sandbox_features.go` | D | 版本串切分先判长度，避免越界 panic | [77](77-api-and-flags-on-arm.md) |

### 2.10 可观测埋点（E 类）

| 文件 | 性质 | 改动 | 篇目 |
|---|---|---|---|
| `orchestrator/internal/sandbox/sandbox.go` | E | `ResumeSandbox()` 沿恢复路径插入九段 `[ResumeSandbox]` 耗时日志 | [84](84-arm-performance.md)、[27](27-resume-sandbox.md) |

---

## 3. 其它仓库

### 3.1 分叉 Firecracker

代码在 `tmp/e2b-book-src/kasandbox-arm/firecracker/`，路径相对该仓库根。

| 文件 | 职责 | 篇目 |
|---|---|---|
| `src/vmm/src/persist.rs` | 快照的保存与加载，含 uffd 后端的注册模式选择 | [70](70-firecracker-fork.md)、[04](04-kvm-and-memory-virtualization.md) |
| `src/vmm/src/rpc_interface.rs` | API 请求分派；分叉新增 `GetMemoryMappings` / `GetMemory` / `GetMemoryDirty` 三个端点 | [70](70-firecracker-fork.md)、[03](03-firecracker-primer.md) |
| `src/vmm/src/vstate/memory.rs`、`vstate/vm.rs`、`vstate/kvm.rs` | guest 内存区域、KVM 虚拟机与内存槽管理 | [04](04-kvm-and-memory-virtualization.md) |
| `src/vmm/src/vstate/vcpu.rs` | vCPU 线程与状态机 | [03](03-firecracker-primer.md) |
| `src/vmm/src/builder.rs`、`resources.rs` | 从配置构造 VM；启动参数与设备装配 | [28](28-firecracker-process-management.md) |
| `src/vmm/src/arch/aarch64/mod.rs`、`layout.rs` | aarch64 的内存布局与启动约定 | [68](68-aarch64-virtualization-differences.md) |
| `src/vmm/src/arch/aarch64/fdt.rs` | 设备树生成，替代 x86 的 ACPI / MPTable | [68](68-aarch64-virtualization-differences.md) |
| `src/vmm/src/arch/aarch64/gic/` | GICv2 / GICv3 中断控制器的状态保存与恢复 | [68](68-aarch64-virtualization-differences.md) |
| `src/vmm/src/arch/aarch64/vcpu.rs`、`regs.rs`、`vm.rs`、`kvm.rs` | aarch64 寄存器的读写与快照序列化 | [68](68-aarch64-virtualization-differences.md)、[70](70-firecracker-fork.md) |
| `src/vmm/src/main.rs`（`resize_fdtable()`） | ARM 构建修复中被注释掉的一处文件描述符表扩容 | [70](70-firecracker-fork.md) |
| `src/vmm/src/devices/virtio/` | virtio 块设备、网络与 balloon | [06](06-block-devices-nbd-cow.md)、[03](03-firecracker-primer.md) |
| `src/vmm/src/mmds/` | MMDS 元数据服务，envd 的配置来源 | [48](48-envd-overview.md) |

### 3.2 fc-kernels-arm

| 文件 | 职责 | 篇目 |
|---|---|---|
| `build.sh`、`Makefile`、`kernel_versions.txt` | 内核编译入口与版本清单 | [69](69-guest-kernel-for-arm.md) |
| `configs/arm64/6.1.158.config`、`6.1.102.config` | arm64 的 guest 内核配置 | [69](69-guest-kernel-for-arm.md) |
| `configs/x86_64/` | 上游原有的 x86 配置，作对照 | [69](69-guest-kernel-for-arm.md) |
| `patches/6.1.158/0001-virtio_balloon-*.patch` | balloon 提示等待 ACK | [87](87-beyond-checkpoint-restore.md) |
| `patches/6.1.158/0002-overlayfs-hot-switch-*.patch` | overlayfs 热切换，服务于后续的 checkpoint / restore | [87](87-beyond-checkpoint-restore.md) |
| `build-rootfs.sh`、`inject-rootfs.sh`、`start-microvm.sh`、`demo/` | 内核的本地验证手段 | [69](69-guest-kernel-for-arm.md) |
| `scripts/upload-release-to-gcs.sh`、`migrate-gcs-arch.sh`、`terraform/` | 上游的发布路径，离线部署不用 | 未展开 |

### 3.3 e2b-infra（单机离线版）

| 文件 / 目录 | 职责 | 篇目 |
|---|---|---|
| `e2b-infra.spec` | RPM 打包：`%prep` 打补丁并覆盖 busybox、`%build` 宿主直编、`%install` 布置目录 | [80](80-single-node-rpm.md)、[85](85-dev-workflow-and-packaging.md) |
| `0001-adapted-for-arm-architecture.patch` | 第 2 节那 94 个文件的补丁本体 | [67](67-arm-port-overview.md) |
| `patch_e2b.py` | 打补丁的辅助脚本 | [85](85-dev-workflow-and-packaging.md) |
| `e2b-deploy/build.sh` | 安装与启动的总入口，`-i` 装组件、`-s` 起服务 | [80](80-single-node-rpm.md) |
| `e2b-deploy/build_prod.py`、`dep/main.py`、`dep/build_api.py` | 部署编排与渲染 | [80](80-single-node-rpm.md) |
| `e2b-deploy/dep/{install,run,start,uninstall}-{consul,nomad,client,server}.sh` | 单机 Nomad 与 Consul 的安装、启动与卸载 | [80](80-single-node-rpm.md)、[79](79-nomad-multinode-deployment.md) |
| `e2b-deploy/dep/init-client.sh` | 宿主初始化：大页、nbd、内核参数、目录 | [82](82-host-kernel-nbd-hugepages.md) |
| `e2b-deploy/dep/nginx.conf`、`daemon.json`、`harbor.cnf` | 入口反代、Docker 与 Harbor 配置 | [81](81-single-node-traffic.md) |
| `e2b-deploy/dep/minio.service`、`minio.yml` | MinIO 的部署形态 | [75](75-minio-storage.md)、[80](80-single-node-rpm.md) |
| `e2b-deploy/dep/template-manager.hcl`、`default.hcl` | 单机上的 Nomad job 与客户端配置 | [80](80-single-node-rpm.md) |
| `e2b-deploy/dep/connection_config.py`、`code_interpreter_sync.py`、`e2b-sdk-checkpoint/` | SDK 侧连接配置与模板同步 | [83](83-sdk-adaptation.md) |
| `vmlinux.bin.arm`、`vmlinux.bin.arm.openeuler`、`firecracker.arm`、`busybox_*_arm64` | 随包分发的二进制 | [69](69-guest-kernel-for-arm.md)、[70](70-firecracker-fork.md)、[80](80-single-node-rpm.md) |
| `benchmark/` | 压测脚本与阶段耗时解析（`parse_report.py`、`run_benchmark.py`） | [84](84-arm-performance.md) |
| `deploy-docs/`、`single-node-offline-deploy.md`、`docs/zh/` | 部署与运维文档 | [80](80-single-node-rpm.md)、[81](81-single-node-traffic.md) |
| `rollback/` | checkpoint / restore 手册，不属本书范围 | [87](87-beyond-checkpoint-restore.md) |

### 3.4 e2b-arm（SDK 覆盖层）

| 目录 | 职责 | 篇目 |
|---|---|---|
| `packages/js-sdk/src/connectionConfig.ts` | JS SDK 的域名、超时与请求头配置 | [83](83-sdk-adaptation.md) |
| `packages/js-sdk/src/sandbox`、`envd`、`api` | 沙箱对象、envd 客户端与 REST 客户端 | [52](52-envd-legacy-and-sdk-compat.md)、[83](83-sdk-adaptation.md) |
| `packages/python-sdk/e2b/connection_config.py` | Python SDK 的同名配置 | [83](83-sdk-adaptation.md) |
| `packages/python-sdk/e2b/sandbox{,_sync,_async}`、`envd` | 同步与异步两套沙箱接口 | [83](83-sdk-adaptation.md) |
| `packages/python-sdk/e2b/checkpointd`、`spec/checkpointd` | checkpoint 客户端，不属本书范围 | [87](87-beyond-checkpoint-restore.md) |
| `packages/cli` | 模板构建与管理的命令行 | [22](22-template-api.md)、[41](41-template-build-overview.md) |
| `packages/connect-python`、`spec/` | Connect-RPC 的 Python 运行时与 proto 契约 | [08](08-go-service-toolkit.md) |

---

## 4. 残留与孤儿

以下都是本书各篇在读代码时确认过**没有调用方或没有读取方**的东西。
它们分三种：生成器留下的产物、被后续改动绕开的旧路径、写了但还没接上消费端的数据。
除非另有说明，这些都是上游 2026.09 的现象，与 ARM 适配无关。

| 对象 | 位置 | 性质 | 发现于 |
|---|---|---|---|
| `get_memory_dirty_parameters.go`、`get_memory_dirty_responses.go` | `packages/shared/pkg/fc/client/operations/` | 生成产物；`firecracker.yml` 里该端点没有 `operationId`，全仓库无引用，实际用的是 `dirty_memory.go` 一路 | [03](03-firecracker-primer.md) |
| `packages/shared/pkg/models` | 不存在 | 大纲与旧文档里出现过的包名；实际类型在 `packages/db/queries/models.go` 与 `packages/db/pkg/types` | [11](11-object-model.md) |
| `SNAPSHOT_CACHE_DIR` | 环境变量 | 旧路径残留；pause 的差分实际落在 `DEFAULT_CACHE_DIR` 下 | [13](13-storage-landscape.md) |
| `ListCachedBuilds` 与 `buildCache` | `api/internal/orchestrator/nodemanager/builds.go` | 只写不读；缓存亲和性没有接进放置算法 | [19](19-node-management-and-placement.md) |
| `packages/api/internal/clusters/mocks` | 目录 `mocks.go` | 生成的 mock，无任何测试 import | 本篇核对 |
| `.github/workflows/fc-test.yml` | 工作流 | `on: workflow_call`，但仓库内没有任何 workflow 调用它 | 本篇核对 |
| `SandboxLogger.Metrics()` | `packages/shared/pkg/logger/` | 无调用点 | [60](60-telemetry.md) |
| `ParseSandboxCatalogCreateEvent` | `packages/shared/pkg/sandbox-catalog/` | 无调用者 | [55](55-sandbox-catalog-and-routing.md) |
| `sandbox_events`、`sandbox_host_stats` 两张表 | `packages/clickhouse/migrations/` | 仓库内只写不读，消费方在 infra 之外 | [59](59-clickhouse.md) |
| `LocalArtifactsRegistry.Delete()` | `packages/shared/pkg/artifacts-registry/` | 空实现；`Local` provider 下删除模板不回收镜像 | [46](46-template-manager-service.md) |
| `TEMPLATE_BUCKET_NAME="skip"` | `iac/provider-gcp/nomad/jobs/api.hcl` | 占位值残留，api 不打开对象存储 | [13](13-storage-landscape.md)、[64](64-nomad-jobs.md) |
| `LOCAL_CLUSTER_ENDPOINT`、`LOCAL_CLUSTER_TOKEN` | edge 的 job 与 helm 模板 | 上游与 ARM 适配版都没有读取方 | [56](56-edge-api.md) |
| `EDGE_PORT`、`EDGE_SECRET`、`SERVICE_DISCOVERY_*` | ARM 的 `edge.hcl` 与 `helm/templates/edge.yaml` | 从上游 job 抄来的变量，client-proxy 不读 | [53](53-client-proxy-edge.md)、[78](78-helm-k8s-deployment.md) |
| 三份 `.env.local` 中的部分条目 | 仓库根与 `packages/*` | 无读取方 | [66](66-local-development.md)、[90](90-config-reference.md) |
| `busybox_1.36.1-2_arm64` | ARM 补丁新增 | 两份 arm64 busybox 里只有 `1.35` 那份被 `go:embed` 引用 | [67](67-arm-port-overview.md)、[74](74-template-build-on-arm.md) |
| `iac/provider-aws` | 目录 | 只有一个 `Makefile`，没有资源定义 | 本篇核对 |

有两条需要区别对待。其一，`get_memory_dirty_*.go` 与 `clusters/mocks` 是生成器的产物，
删掉它们不会改变行为，但下一次 `make generate` 又会长出来 —— 要治的是生成配置而不是文件。
其二，`sandbox_events` 与 `sandbox_host_stats` 的「只写不读」是仓库边界造成的假象：
消费方是 e2b 闭源的 dashboard，不在 infra 里。把它们和真正的死代码混在一起会误判。

---

## 延伸阅读

- [第 01 篇 · e2b 生态与仓库地图 §3](01-e2b-ecosystem.md#3-infra-仓库的骨架)：本篇第 1 节的叙述版，含各 package 的代码量与依赖关系。
- [第 10 篇 · 系统架构 §2](10-system-architecture.md#2-进程清单)：按进程而不是按目录看同一份代码。
- [第 67 篇 · ARM 适配总览 §3](67-arm-port-overview.md#3-改动地图)：本篇第 2 节的分类依据与逐类展开。
- [第 86 篇 · 已知问题与技术债 §7](86-known-issues-and-debt.md#7-继承自上游的问题)：第 4 节里需要动手修的那些。
- [第 88 篇 · 术语表](88-glossary.md)、[第 90 篇 · 环境变量与配置项总表](90-config-reference.md)、
  [第 91 篇 · 端口、路径与存储键总表](91-ports-paths-keys.md)：另外三张查阅表。
