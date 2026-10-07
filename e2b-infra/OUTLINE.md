# 全书大纲

本文件是这本书的**编写计划**：讲哪些主题、每篇写什么、面向谁、依赖哪些代码事实。
体例、术语与口径在 [`STYLE.md`](STYLE.md)；读者导览在 [`README.md`](README.md)。
本文件是给**编写者与维护者**看的。

---

## 一、全书结构

| 部 | 主题 | 篇目 | 面向 |
|---|---|---|---|
| 〇 | 导读 | 00–01 | 所有读者 |
| 一 | 预备知识 | 02–09 | 不熟悉虚拟化 / 内核接口 / 编排工具的读者 |
| 二 | 总体架构 | 10–14 | 所有读者；工程师必读 |
| 三 | API 服务 | 15–24 | 工程师 |
| 四 | Orchestrator：沙箱运行时 | 25–40 | 工程师；全书核心 |
| 五 | 模板构建 | 41–47 | 工程师 |
| 六 | envd：沙箱内守护进程 | 48–52 | 工程师、SDK 开发者 |
| 七 | 边缘与流量 | 53–57 | 工程师、运维 |
| 八 | 数据与可观测 | 58–62 | 工程师、运维 |
| 九 | 上游的部署与开发 | 63–66 | 运维、工程师 |
| 十 | ARM 适配版 | 67–87 | 本项目所有参与者 |
| 附录 | 术语表、代码地图、配置与端口总表 | 88–91 | 查阅 |

篇幅分配的依据：上游 2026.09 约 7.8 万行有效 Go 代码（不含测试与生成代码；orchestrator 3.3 万、api 1.9 万、
shared 1.2 万、envd 0.6 万、db 0.5 万、其余 0.4 万）加上 IaC；ARM 适配约 5300 行补丁、
少量 Firecracker / 内核改动、约 4000 行部署脚本与 RPM spec。按代码量 ARM 应占约一成，
本书提到约两成半，因为 ARM 适配与后续功能开发是本项目的主要工作。

状态图例：`○` 未写　`◐` 草稿　`●` 完成　`◎` 已审校

> **2026-09-08：92 篇（00–91）全部完成并审校**（正文约 40.9 万汉字，不含代码块与表格）。下表状态已更新。

---

## 二、代码基线与阅读位置

| 基线 | 位置 | 说明 |
|---|---|---|
| 上游 2026.09 | `tmp/e2b-book-src/upstream/` | commit `f8c2f0cde`（ARM 补丁提交的父提交，即上游 tag `2026.09`） |
| ARM 适配版（infra） | `tmp/e2b-book-src/arm/` | commit `fbee6fcd1`，比上游多出 94 个文件的改动；`git diff f8c2f0cde fbee6fcd1` 即完整补丁 |
| ARM 适配版（Firecracker） | `tmp/e2b-book-src/kasandbox-arm/firecracker/` | e2b-dev/firecracker 分支 `firecracker-v1.12-direct-mem` 的 `54a1c1a` + ARM 构建修复（commit `b8e85c3`） |
| ARM 适配版（内核） | `fc-kernels-arm/` | e2b-dev/fc-kernels 的 arm64 config 与补丁 |
| 单机离线版 | `e2b-infra/` | RPM spec、`e2b-deploy/`、`single-node-offline-deploy.md`、`deploy-docs/`、`benchmark/` |
| SDK 适配 | `e2b-arm/`（分支 `jll` 相对 `e2b@2.20.0`） | 只看与 ARM 部署相关的部分（http 连接配置等），checkpoint SDK 不在本书范围 |

所有路径相对于 `/home/austin/projects/e2b-repo/`。

---

## 三、篇目与编写要点

每篇的要点分四块：**讲什么**（bullets）、**代码**（必读位置）、**图表**（建议）、**衔接**（前后篇）。
编写者按要点写，但不受其束缚 —— 读代码时发现要点有误，以代码为准并在交付说明中指出。

### 第〇部分　导读

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 00 | `00-overview.md` | 全书导读与系统总览 | ◎ |
| 01 | `01-e2b-ecosystem.md` | e2b 生态与仓库地图 | ◎ |

**00 · 全书导读与系统总览**（最后写，全书完成后）
一篇读完全貌，给评审、决策者与第一天到岗的新人。5000 字上限。
- e2b 是什么、解决什么问题、一句话架构
- 六个进程（api、orchestrator、template-manager、envd、client-proxy、docker-reverse-proxy）
  与四类存储各自干什么
- 沙箱从模板快照拉起、用完即弃或暂停成新快照 —— 这个循环是全书主线
- 上游与 ARM 适配版的关系：改了什么、为什么、代价
- 分读者的阅读路径（与 README 一致）
- 图：一张全系统结构图（mermaid）

**01 · e2b 生态与仓库地图**
- e2b-dev 组织下的仓库：E2B（SDK + CLI）、code-interpreter、desktop、infra、firecracker（分叉，2026-08 已归档）、
  fc-kernels、dashboard、mcp-server、e2b-cookbook、fragments、surf / open-computer-use；各自定位与语言
- 客户端 → 服务端的调用面：SDK 调 REST API 管理沙箱，直接调 envd 在沙箱里执行；CLI 走模板构建
- infra 仓库的目录结构：`packages/*` 十三个目录十二个 Go 模块、`iac/`（含 `iac/modules/job-*`）、`spec/`、`tests/`、`scripts/`；go.work 工作区（`helm/` 是 ARM 适配版新增）
- 每个 package 的一句话职责与代码量（表）
- 本书聚焦服务端；SDK / desktop / code-interpreter 只在第 52、83 篇涉及
- 代码：`go.work`、各 `packages/*/README.md`、`Makefile`、`spec/*.yml`
- 图：仓库关系图；package 依赖图（shared 被谁依赖）

### 第一部分　预备知识

面向没有虚拟化 / 内核接口背景的读者。每篇讲**本书用得到的**那部分，不做综述；
每篇末尾要明确指出「这些概念在本书哪几篇被用到」。

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 02 | `02-why-sandbox.md` | AI 代码沙箱：问题、威胁模型与隔离谱系 | ◎ |
| 03 | `03-firecracker-primer.md` | Firecracker 入门 | ◎ |
| 04 | `04-kvm-and-memory-virtualization.md` | KVM 与内存虚拟化 | ◎ |
| 05 | `05-userfaultfd.md` | userfaultfd：把缺页交给用户态 | ◎ |
| 06 | `06-block-devices-nbd-cow.md` | 块设备、NBD 与写时复制 | ◎ |
| 07 | `07-linux-networking-for-sandboxes.md` | 沙箱网络的内核基础 | ◎ |
| 08 | `08-go-service-toolkit.md` | 本书用到的 Go 服务工程 | ◎ |
| 09 | `09-nomad-consul-terraform.md` | Nomad、Consul 与 Terraform | ◎ |

**02 · AI 代码沙箱：问题、威胁模型与隔离谱系**
- 场景：LLM 生成的代码必须被执行，它不可信、多租户、生命周期短、要秒级启动
- 威胁模型：代码逃逸、横向访问其它租户、访问宿主内网、资源耗尽、数据外泄
- 隔离谱系：进程 + seccomp、容器（namespaces + cgroups）、gVisor、microVM、完整 VM；
  各自的隔离边界、启动代价、密度；给出数量级而非具体数字
- 为什么 e2b 选 microVM + 快照：硬件隔离边界 + 从快照恢复得到的秒级启动
- 「沙箱从不冷启动」—— 这个设计事实是全书主线，在这里第一次点明
- 代码：无；引用 `packages/orchestrator/internal/sandbox/network/` 的默认拒绝网段作为威胁模型落地的例子
- 图：隔离谱系对比表

**03 · Firecracker 入门**
- 它是什么、砍掉了什么（无 BIOS、无 PCI、virtio-mmio、极简设备）、进程模型（一个 VM 一个进程）
- REST API over Unix socket：machine-config、boot-source、drives、network-interfaces、mmds、
  snapshot/create、snapshot/load、vm（pause/resume）、balloon；给出 e2b 用到的子集
- jailer 与 seccomp；e2b 是否用 jailer（读 `fc/process.go` 确认）
- 快照：vmstate 文件与内存文件；Full 与 Diff；`track_dirty_pages`；加载时的内存后端：File 与 Uffd
- MMDS：给 guest 传元数据的通道，e2b 用它把 sandbox 元数据交给 envd
- 版本：e2b 用的是自己的分叉（第 70 篇）；上游 2026.09 默认版本常量在 `packages/shared/pkg/feature-flags/flags.go`
- 代码：`packages/shared/pkg/fc/client/`（生成的 API 客户端，看 operations 列表）、`packages/orchestrator/internal/sandbox/fc/client.go`
- 图：Firecracker 进程与宿主资源关系图；快照 create/load 时序

**04 · KVM 与内存虚拟化**
- `/dev/kvm`、VM fd、vCPU fd、`KVM_RUN` 循环、VM-Exit
- 两级地址翻译：guest 虚拟 → guest 物理（GPA）→ 宿主物理；EPT / Stage-2
- memslot：guest 物理内存就是 VMM 进程的一段虚拟内存；这决定了「内存文件可以 mmap 后交给 KVM」
- 缺页在两层各自的含义；宿主缺页由谁处理 —— 为第 5 篇铺垫
- 大页（2 MiB HugeTLB）：TLB、缺页次数、预留与碎片；e2b 里 hugepages 是模板级选项
- 脏页跟踪的三种来源（KVM dirty log、写保护、硬件）—— 只给概念，细节在第 37、72 篇
  与 checkpoint / restore 手册第 7 篇
- 代码：无；引用 `packages/orchestrator/internal/sandbox/uffd/memory/` 的地址区间结构作为「memslot 在用户态的镜像」
- 图：两级翻译示意；VMM 进程地址空间与 guest 物理地址的对应

**05 · userfaultfd：把缺页交给用户态**
- 动机：按需加载内存，页从哪来由用户态决定（远端对象存储、本地缓存、另一个文件）
- API：`userfaultfd()`、`UFFDIO_API`、`UFFDIO_REGISTER`（MISSING / WP / MINOR）、
  读事件、`UFFDIO_COPY`、`UFFDIO_ZEROPAGE`、`UFFDIO_WRITEPROTECT`、`UFFDIO_CONTINUE`
- 事件循环：读 fd 得 `uffd_msg`，找页、`UFFDIO_COPY` 填页并唤醒
- 写保护（WP）：`UFFDIO_COPY_MODE_WP`、`UFFD_FEATURE_WP_ASYNC`、pagemap 的 bit 57；
  这是 e2b 判断脏页的机制（第 37 篇）；ARM 上的限制（第 72 篇）
- Firecracker 侧如何把 uffd 交出来：snapshot/load 的 `mem_backend: {backend_type: Uffd, backend_path}`，
  通过 Unix socket 传 fd 与内存映射描述
- 大页与 uffd：HugeTLB 区域的注册与 COPY 单位
- 代码：`packages/orchestrator/internal/sandbox/uffd/userfaultfd/`（常量、ioctl 封装）
- 图：缺页 → 事件 → 填页时序

**06 · 块设备、NBD 与写时复制**
- 块设备抽象；guest 看到的 virtio-blk 后端是宿主上的一个文件或设备
- NBD：内核客户端 `/dev/nbdN` 与用户态服务器的协议（握手、读写请求）；为什么 e2b 用 NBD 把
  「从对象存储按需拉块」变成一个块设备；`nbds_max`、连接数、`nowatch` udev 规则
- 稀疏文件与空洞；`fallocate`、`SEEK_HOLE`；写时复制的两种实现：文件系统级（reflink）与应用级（overlay + 脏块位图）
- e2b 的 overlay 思路：只读基底（模板 rootfs）+ 每沙箱写层（cache 文件）+ 位图；细节在第 30、33 篇
- ext4 作为 guest 根文件系统：模板构建时怎么造出来（第 43 篇）
- 代码：`packages/orchestrator/internal/sandbox/nbd/`、`packages/orchestrator/internal/sandbox/block/`（只看接口）
- 图：guest 写请求穿过 virtio-blk → NBD → overlay → cache / 远端 的路径

**07 · 沙箱网络的内核基础**
- 网络命名空间；veth 对；tap 设备与 VMM 的关系；桥接与路由
- NAT：SNAT / DNAT、iptables 与 nftables、conntrack；「每个沙箱同一个 guest IP、宿主侧用不同 netns 隔离」的思路
- DNS：沙箱怎么解析域名；宿主的解析器与沙箱的关系
- 出站过滤：默认拒绝的内网网段（威胁模型的落地）；TCP 防火墙在用户态做的事（第 35 篇）
- 入站：沙箱端口如何被外界访问 —— 域名编码 port 与 sandbox ID，由 client-proxy 转发（第 53 篇）
- 代码：`packages/orchestrator/internal/sandbox/network/`（slot、netns 建立脚本）、`packages/orchestrator/internal/tcpfirewall/`
- 图：一个沙箱的网络路径（guest → tap → netns → 宿主 → 外网）

**08 · 本书用到的 Go 服务工程**
- go.work 多模块工作区；`packages/shared` 作为公共库
- gRPC + protobuf：`orchestrator.proto`、`template-manager.proto`、`info.proto`、`proxy.proto`；生成物在 `packages/shared/pkg/grpc/`
- Connect-RPC：envd 的 process / filesystem 服务；与 gRPC 的关系；HTTP/1.1 与 HTTP/2
- OpenAPI 优先：`spec/openapi*.yml` → oapi-codegen → Gin handler 接口；`packages/api/internal/api/`
- 数据访问：sqlc 生成的查询（`packages/db/queries`）与迁移
- OpenTelemetry：tracer、meter、logger 的组织（`packages/shared/pkg/telemetry`、`logger`）
- 特性开关：LaunchDarkly 客户端与本地 fallback（`packages/shared/pkg/feature-flags`）
- 代码生成入口：`make generate`、各 package 的 `generate.go`
- 图：四种接口技术在系统中的位置（一张结构图）

**09 · Nomad、Consul 与 Terraform**
- Nomad 的模型：server / client、job / group / task、driver（docker、raw_exec）、constraint、resources、network 端口
- Consul：服务注册、健康检查、DNS 接口；e2b 用 Consul 做什么（读 nomad job 的 `service` 块与 api 的 discovery 代码）
- Terraform：模块、状态、provider；e2b 的 `iac/provider-gcp` 结构一览（细节在第 63 篇）
- Packer 构建的节点磁盘镜像里装了什么（`iac/provider-gcp/nomad-cluster-disk-image/`）
- 为什么上游选 Nomad 而不是 Kubernetes；ARM 适配版补了 k8s 路径（第 76、78 篇）
- 代码：`iac/provider-gcp/nomad/jobs/*.hcl`、`iac/provider-gcp/nomad-cluster/scripts/`
- 图：Nomad 集群拓扑（server 集群、api 节点、build 节点、client 节点）

### 第二部分　总体架构

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 10 | `10-system-architecture.md` | 系统架构：组件、进程、端口与数据流 | ◎ |
| 11 | `11-object-model.md` | 对象模型与状态机 | ◎ |
| 12 | `12-sandbox-lifecycle-walkthrough.md` | 端到端走查：一个沙箱的一生 | ◎ |
| 13 | `13-storage-landscape.md` | 存储全景 | ◎ |
| 14 | `14-config-flags-versions.md` | 配置、特性开关与版本约定 | ◎ |

**10 · 系统架构：组件、进程、端口与数据流**
- 进程清单与职责：api、orchestrator、template-manager（可与 orchestrator 同进程，看 `ORCHESTRATOR_SERVICES`）、
  client-proxy（edge）、docker-reverse-proxy、envd、dashboard-api、otel-collector / logs-collector
- 控制面与数据面：api ↔ orchestrator 走 gRPC；SDK ↔ envd 走 client-proxy 转发的 HTTP；模板推送走 docker-reverse-proxy
- 端口表（从 nomad job 与 consts 读）；进程之间的依赖方向
- 三类节点：api 节点、build 节点、client（沙箱）节点；每类跑什么
- 一次请求的三条典型路径：创建沙箱、在沙箱里执行命令、构建模板 —— 只画图，细节在第 12、41 篇
- 代码：`packages/shared/pkg/consts/`、`iac/provider-gcp/nomad/jobs/*.hcl`、各 package 的 `main.go`
- 图：全系统结构图（本书的「地图」，后面各篇反复引用）；三条路径的时序图

**11 · 对象模型与状态机**
- team / user / tier；template / build / alias / tag；sandbox 与 snapshot（pause 产生的 build）；node / cluster
- ID 的形态与生成规则：sandbox ID、build ID（UUID）、template ID、`sandboxID-clientID` 组合；`packages/shared/pkg/id`
- sandbox 状态机：starting → running → pausing → paused → (resumed) / killed；auto-pause 与 timeout 的语义；
  在 api、orchestrator、redis 里各自的表示
- build 状态机：waiting → building → ready / failed；snapshot 的 build 与模板的 build 共用什么
- node 状态：ready / draining / unhealthy；从 orchestrator 的 `ServiceInfo` 到 api 的 nodemanager
- 代码：`packages/shared/pkg/models/`（或 db 生成的类型）、`packages/api/internal/sandbox/`、
  `packages/shared/pkg/sandbox-catalog/`、`packages/orchestrator/internal/sandbox/sandbox.go` 的 Metadata
- 图：对象关系图；sandbox 状态机（stateDiagram）

**12 · 端到端走查：一个沙箱的一生**
- 从 `Sandbox.create()` 开始：SDK 发什么请求、带什么头；api 认证、配额检查、选节点、调 orchestrator Create
- orchestrator 侧：ResumeSandbox 的阶段（只列，细节在第 27 篇）；envd init；返回 client ID
- SDK 直接与 envd 通信：域名如何编码、client-proxy 如何找到节点、envd 如何验 access token
- 生命周期：timeout 续期、auto-pause、kill；Pause 路径的产物去哪
- 每一步涉及哪些进程、哪些存储、哪些日志 —— 作为后面各篇的索引
- 代码：`packages/api/internal/handlers/sandbox_create.go`（或同名）、`packages/orchestrator/internal/server/sandboxes.go`、
  `packages/client-proxy/`、`packages/envd/internal/api/`
- 图：一张完整时序图（这是全书最重要的图之一，25 个节点上限可以放宽到 35）

**13 · 存储全景**
- 四类存储：Postgres（元数据）、Redis（沙箱运行态与目录）、ClickHouse（指标与事件）、对象存储（模板与快照产物）
- 节点本地：模板缓存目录、build 缓存、NBD 缓存文件、内存 diff 缓存；NFS（Filestore）共享缓存
- 谁写谁读：一张矩阵表（进程 × 存储）
- 对象存储的键布局（`packages/shared/pkg/storage/template.go`）；provider 抽象（GCS / S3 / Local；ARM 增 MinIO，第 75 篇）
- 一致性边界：什么以 Postgres 为准、什么以 Redis 为准、什么允许陈旧
- 代码：`packages/shared/pkg/storage/`、`packages/db/`、`packages/api/internal/sandbox/storage/`、`packages/orchestrator/internal/template/cache/`
- 图：存储矩阵；对象存储键布局（text）

**14 · 配置、特性开关与版本约定**
- 环境变量：各进程读哪些（`.env.template`、nomad job 的 env、`packages/*/main.go`、`packages/shared/pkg/env`）
- feature flags：LaunchDarkly 的 flag 清单（`flags.go`）与默认值；没有 LaunchDarkly 时怎么工作；
  哪些 flag 影响放置、预取、并发
- 版本三元组：kernel 版本、Firecracker 版本、envd 版本 —— 存在模板 metadata 里，节点本地要有对应的二进制
  （`/fc-versions/`、`/fc-kernels/`、envd 内嵌进 rootfs）
- 版本兼容规则：模板用哪个 FC 版本恢复；升级 FC 时旧快照怎么办
- 仓库版本号 `VERSION` 与镜像 tag
- 代码：`packages/shared/pkg/feature-flags/flags.go`、`packages/shared/pkg/env/`、`packages/orchestrator/internal/cfg/`、
  `packages/orchestrator/internal/template/metadata/`
- 图：配置项分类表；版本三元组与目录布局（text）

### 第三部分　API 服务

`packages/api`，约 1.9 万行。每篇讲一个职责域，篇与篇之间按请求处理链路排序。

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 15 | `15-api-service-structure.md` | API 服务的结构 | ◎ |
| 16 | `16-auth-and-multitenancy.md` | 认证与多租户 | ◎ |
| 17 | `17-sandbox-create-api.md` | 创建沙箱 | ◎ |
| 18 | `18-sandbox-lifecycle-api.md` | 沙箱生命周期 API | ◎ |
| 19 | `19-node-management-and-placement.md` | 节点管理与放置 | ◎ |
| 20 | `20-sandbox-state-storage.md` | 沙箱运行态存储 | ◎ |
| 21 | `21-clusters-and-discovery.md` | 集群与服务发现 | ◎ |
| 22 | `22-template-api.md` | 模板 API | ◎ |
| 23 | `23-template-manager-client.md` | API 侧的构建管理 | ◎ |
| 24 | `24-api-metrics-and-analytics.md` | API 的指标、日志与分析事件 | ◎ |

**15 · API 服务的结构**
- `main.go` 的启动顺序：配置、数据库、Redis、orchestrator 客户端、template-manager 客户端、Gin、gRPC（给 edge 用）
- OpenAPI → 生成代码 → `handlers` 实现 `ServerInterface`；路由表怎么来的；请求校验在哪层
- 中间件链：认证、限流、otel、日志、panic 恢复；错误响应模型
- 与 orchestrator 的连接管理：每节点一个 gRPC 客户端，何时建、何时断（`packages/api/internal/orchestrator/client.go`）
- 优雅退出与健康检查
- 代码：`packages/api/main.go`、`packages/api/internal/api/`、`packages/api/internal/handlers/store.go`、`packages/api/internal/middleware/`
- 图：请求处理链（flowchart）；handler 依赖图

**16 · 认证与多租户**
- 三种凭证：API key（团队级，管理沙箱）、access token（用户级，管理模板与团队）、sandbox access token（沙箱级，给 envd）；
  admin token；supabase JWT（dashboard）
- 存储与哈希：`packages/db/pkg/auth/`、`packages/shared/pkg/keys/`、hash seed
- team 与 tier：并发沙箱上限、最大时长、资源上限如何在创建路径上被检查
- `packages/auth`（独立模块）与 `packages/dashboard-api` 的职责
- 代码：`packages/auth/pkg/auth/`（认证已全部在此独立模块）、`packages/db/pkg/auth/`、`packages/api/internal/handlers/auth.go`、`packages/shared/pkg/keys/`
- 图：三种凭证的作用域表；认证流程图

**17 · 创建沙箱**
- `POST /sandboxes` 的请求体：template、timeout、metadata、env vars、secure、auto-pause、allow internet / network config
- 处理链：认证 → 解析模板与 build → 配额 → 生成 sandbox ID 与 access token → 选节点（第 19 篇）→ 调 orchestrator Create
  → 写运行态存储（第 20 篇）→ 返回
- 失败路径：节点资源不足重试、orchestrator 返回错误时的清理、并发去重
- 与 `POST /sandboxes/{id}/resume` 共享什么（都走 orchestrator Create，只是 build 来源不同）
- 代码：`packages/api/internal/handlers/sandbox_create.go`、`packages/api/internal/orchestrator/create_instance.go`（或同名）、`packages/api/internal/sandbox/`
- 图：创建路径的时序图；请求字段 → orchestrator 请求字段的映射表

**18 · 沙箱生命周期 API**
- connect、timeout、refreshes、kill、pause、resume、list（v1 / v2 分页）、metrics、logs 各自的语义
- 生命周期管理器：api 侧的 timer / 到期扫描如何驱动 kill 与 auto-pause（`packages/api/internal/orchestrator/lifecycle.go`）
- 并发与幂等：同一沙箱同时 pause 与 kill 怎么办；跨 api 实例的协调（Redis）
- pause 的完整链路：api → orchestrator Pause → 产物 → build 记录 → 沙箱从运行态移除
- 代码：`packages/api/internal/handlers/sandbox_*.go`、`packages/api/internal/orchestrator/lifecycle.go`、`packages/api/internal/orchestrator/pause_instance.go`（或同名）
- 图：生命周期状态与 API 的对应（stateDiagram）

**19 · 节点管理与放置**
- nodemanager：节点如何被发现（第 21 篇）、状态同步（ServiceInfo 轮询）、健康判断、draining
- 放置算法：best-of-k 采样、资源预留（CPU / 内存过量分配比）、alpha 权重；为什么不是全局最优
- 节点上的沙箱计数与缓存构建（ListCachedBuilds）在放置里的作用
- 失败重试与「节点被标坏」的条件
- 代码：`packages/api/internal/orchestrator/nodemanager/`、`packages/api/internal/orchestrator/placement/`、`flags.go` 中的 best-of-k 参数
- 图：放置决策流程；参数表

**20 · 沙箱运行态存储**
- 两个后端：memory（单实例）与 redis（多实例）；接口 `packages/api/internal/sandbox/storage/`
- 存什么：sandbox 记录、到期时间、节点归属、状态；expiring 列表的实现
- reservations：创建过程中的占位，防止并发超配（`packages/api/internal/sandbox/reservations/redis`）
- 与 sandbox-catalog（edge 用的目录）的关系与一致性
- 迁移到 Redis 的动机（多 api 实例）与代价
- 代码：上述目录 + `packages/shared/pkg/sandbox-catalog/`
- 图：数据结构表（key 布局）；创建期间的占位时序

**21 · 集群与服务发现**
- cluster 的概念：一组 orchestrator 节点 + edge 实例，可能不在 api 所在的网络；`packages/api/internal/clusters/`
- 发现方式：Nomad（服务注册）与本地静态配置（`discovery/local.go`）；实例同步循环
- 跨集群路由：api 如何把请求发到远端集群的 edge，再由 edge 转给 orchestrator
- 节点 ID 与 nomad node ID 的对应
- 代码：`packages/api/internal/clusters/`、`packages/shared/pkg/clusters/discovery/`、`packages/shared/pkg/http/edge/`
- 图：单集群与多集群拓扑
- ARM 差异：k8s 发现（第 76 篇）

**22 · 模板 API**
- v2 / v3 templates：创建模板记录、触发构建、文件按 hash 上传（`/templates/{id}/files/{hash}`）、别名与标签、删除保护
- 模板可见性：团队私有 / 公共；alias 解析规则
- 构建请求体如何变成 template-manager 的 TemplateCreate 请求（步骤列表、Dockerfile、start / ready 命令）
- 代码：`packages/api/internal/handlers/template_*.go`、`packages/api/internal/template/`、`packages/api/internal/cache/templates/`
- 图：模板 / 构建 / 别名关系；构建触发时序

**23 · API 侧的构建管理**
- template-manager 客户端：选择 build 节点、TemplateCreate、状态轮询、日志拉取、取消与删除
- 构建状态在 Postgres 里的记录与更新；失败原因如何回传
- 并发构建的取消范围（同 tag 的重叠构建）
- 代码：`packages/api/internal/template-manager/`
- 图：构建状态机；api ↔ template-manager 时序

**24 · API 的指标、日志与分析事件**
- `/sandboxes/{id}/metrics`、`/sandboxes/metrics`、`/teams/{id}/metrics`：数据从 ClickHouse 来，怎么查
- `/sandboxes/{id}/logs`：从 Loki 查；v2 版本的差异
- analytics collector：发给外部分析服务的事件；posthog
- 每个端点的数据来源表
- 代码：`packages/api/internal/analytics_collector/`、`packages/api/internal/handlers/sandbox_metrics.go`（或同名）、`packages/shared/pkg/logs/loki/`、`packages/clickhouse/pkg/`
- 图：端点 → 数据源矩阵

### 第四部分　Orchestrator：沙箱运行时

`packages/orchestrator`，约 3.3 万行，全书核心。按「进程 → 对象 → 恢复路径 → 内存 → 磁盘 → 网络 → 暂停 → 资源 → 错误」排序。

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 25 | `25-orchestrator-process.md` | orchestrator 进程 | ◎ |
| 26 | `26-sandbox-object.md` | Sandbox 对象与 Factory | ◎ |
| 27 | `27-resume-sandbox.md` | ResumeSandbox：从快照拉起一台沙箱 | ◎ |
| 28 | `28-firecracker-process-management.md` | Firecracker 进程管理 | ◎ |
| 29 | `29-template-artifact-format.md` | 模板产物格式 | ◎ |
| 30 | `30-block-layer.md` | block 包：缓存、overlay 与分片读取 | ◎ |
| 31 | `31-uffd-memory-backend.md` | 内存后端：uffd 服务 | ◎ |
| 32 | `32-memory-prefetch-and-hugepages.md` | 预取与大页 | ◎ |
| 33 | `33-nbd-and-rootfs.md` | 磁盘：NBD 服务器与 rootfs | ◎ |
| 34 | `34-template-cache-and-local-storage.md` | 模板缓存与本地存储 | ◎ |
| 35 | `35-sandbox-networking.md` | 沙箱网络 | ◎ |
| 36 | `36-orchestrator-proxy-and-envd-client.md` | 代理与 envd 通信 | ◎ |
| 37 | `37-pause-and-snapshot.md` | Pause：脏页判定与差分导出 | ◎ |
| 38 | `38-cgroups-and-host-stats.md` | cgroup、资源记账与主机统计 | ◎ |
| 39 | `39-health-errors-and-teardown.md` | 健康检查、错误语义与清理 | ◎ |
| 40 | `40-volumes-and-nfsproxy.md` | Volumes 与 NFS proxy | ◎ |

**25 · orchestrator 进程**
- `main.go`：服务组合（`ORCHESTRATOR_SERVICES`）、gRPC server、info 服务（ServiceInfo / 状态覆盖）、
  健康检查 HTTP、hyperloop server（给 envd 回调用）、指标
- 启动时做的事：网络槽位池预热、模板缓存、NBD 设备池、feature flags、持久化恢复（重启后找回沙箱？读代码确认）
- 与 nomad 的关系：raw_exec 跑在宿主、需要 root、依赖的宿主目录
- 优雅退出：draining 状态、等待沙箱
- 代码：`packages/orchestrator/main.go`、`internal/server/main.go`、`internal/service/`、`internal/hyperloopserver/`、`internal/healthcheck/`
- 图：进程内部件图；启动顺序

**26 · Sandbox 对象与 Factory**
- `Sandbox` 结构：Metadata（Config / Runtime / StartedAt / EndAt）、Resources、进程句柄、Cleanup、exit 通道
- Factory：持有的共享资源（网络池、设备池、模板缓存、feature flags、cgroup manager、持久化）
- 生命周期方法的语义：`Wait`、`Close`、`Stop`、`Shutdown`、`Pause` 各自等什么、清什么、能否重入
- `Cleanup` 的栈式清理与优先级（`cleanup.go`）
- sandbox map（`map.go`）与并发访问
- 代码：`internal/sandbox/sandbox.go`、`cleanup.go`、`map.go`、`metrics.go`
- 图：Sandbox 对象与宿主资源的持有关系；清理顺序

**27 · ResumeSandbox：从快照拉起一台沙箱**
- 入口：orchestrator `Create` RPC → `ResumeSandbox`；参数从哪来
- 并行阶段：网络槽位、模板拉取（memfile / rootfs / snapfile / metadata）、rootfs overlay、cgroup、FC 进程启动、
  uffd socket、snapshot/load、resume、MMDS、envd init
- 每阶段的等待点与失败回滚；`errgroup` 的用法；超时来源
- 「快照加载后 guest 看到的世界」：时间、网络、envd 的重新初始化
- 与 `CreateSandbox`（模板构建时的冷启动）的区别 —— 只有构建路径冷启动
- 代码：`internal/sandbox/sandbox.go` 的 `ResumeSandbox()`、`CreateSandbox()`；`internal/server/sandboxes.go`
- 图：阶段时序图（并行段用 par）；阶段耗时的量级表（引用第 84 篇的实测）
- ARM 差异：埋点日志与超时调整（第 71 篇）

**28 · Firecracker 进程管理**
- `fc/process.go`：命令行组装、netns 内启动（`ip netns exec` 还是 `nsenter`，读代码）、stdout / stderr 采集、
  API socket 等待、cgroup 放置（`CLONE_INTO_CGROUP`）
- `fc/client.go`：machine-config、boot-source、drive、network-interface、mmds、snapshot、vm 的调用顺序
- 内核参数表：每个参数的用途（`pci=off`、`i8042.*`、`random.trust_cpu`、`clocksource`、`panic`、`reboot=k`、`ipv6.autoconf`、`systemd.journald.forward_to_console`）
- MMDS 元数据结构与 envd 怎么读
- 进程退出的观测：`Wait`、退出码、日志中的 panic
- 代码：`internal/sandbox/fc/`、`internal/sandbox/socket/`
- 图：启动时序；参数表
- ARM 差异：参数按架构分支、cgroup FD 移除（第 71、73 篇）

**29 · 模板产物格式**
- 五个文件：`snapfile`、`memfile`、`memfile.header`、`rootfs.ext4`、`rootfs.ext4.header`、`metadata.json`
- header 格式：`packages/shared/pkg/storage/header/`（Metadata、Mapping、block size、build ID 链）
- diff 链：pause 产生的 build 只含脏块，header 把每个块指向「最近一次写它的 build」；读一个块要查 header 再定位到某个 build 的文件与偏移
- 版本字段与兼容；hugepages 与 block size 的关系
- 本地缓存与远端的对应键
- 代码：`packages/shared/pkg/storage/header/`、`packages/shared/pkg/storage/template.go`、`internal/sandbox/build/`、`internal/template/metadata/`
- 图：文件布局（text）；header 映射示意；diff 链示意

**30 · block 包：缓存、overlay 与分片读取**
- 接口：`ReadonlyDevice`、`Device`、`Slicer` 等（读 `block/` 里的接口定义）
- `Cache`：mmap 的本地文件 + 已缓存位图；`WriteAtWithoutLock` 的约束
- `Overlay`：读走缓存或基底、写进缓存并置脏；`Export`（导出脏块，pause 用）
- `Chunker`：从 storage 按 chunk 拉取并写入缓存；并发与去重
- storage 读取路径：header 定位 → build 文件 → 范围读
- 代码：`internal/sandbox/block/*.go`、`internal/sandbox/build/`
- 图：读写路径 flowchart；类图（可选）
- ARM 差异：`WriteAtWithoutLock` 的防御性检查（第 73 篇）

**31 · 内存后端：uffd 服务**
- `uffd.go`：Unix socket 服务、接收 FC 传来的 uffd fd 与内存区间描述、事件循环、`Ready`、退出与 fdexit
- 缺页处理：地址 → guest 物理偏移 → block 读（走第 30 篇）→ `UFFDIO_COPY`；EEXIST 处理
- 写保护位的设置规则：读缺页保留 WP、写缺页不保留；这是脏页判定的基础
- 并发：多 vCPU 同时缺页；错误时怎么让 guest 停下
- `memory/` 的区间结构；`userfaultfd/` 的 ioctl 封装
- 代码：`internal/sandbox/uffd/`
- 图：缺页事件时序；地址映射
- ARM 差异：WP 被禁用（第 72 篇）

**32 · 预取与大页**
- 预取：为什么需要（首次缺页太慢）、预取什么（上一次运行的缺页集合？读 `prefetch/` 与 `MemoryPrefetchData`）、
  fetch worker 与 copy worker 的并发
- 大页：模板级选项、`MachineConfiguration.HugePages`、hugetlbfs 预留、对缺页次数与内存占用的影响
- 成本与收益：预取带宽 vs 首次访问延迟；表
- 代码：`internal/sandbox/uffd/prefetch/`、`sandbox.go` 的 `MemoryPrefetchData`、`flags.go` 中的预取参数
- 图：预取与按需缺页的时间线对比

**33 · 磁盘：NBD 服务器与 rootfs**
- `nbd/`：设备池（`/dev/nbdN` 的分配与回收）、服务器（`go-nbd`？读代码）、连接与断开、超时
- `rootfs/`：provider 抽象；NBD 路径与直接文件路径；Firecracker 看到的是什么
- 从 guest 写到 cache 文件的完整路径；断开时的数据落盘
- 设备数上限（`nbds_max`）与并发沙箱数的关系
- 代码：`internal/sandbox/nbd/`、`internal/sandbox/rootfs/`
- 图：数据路径；设备生命周期

**34 · 模板缓存与本地存储**
- 模板缓存：`internal/template/cache/`、`internal/sandbox/template/`；缓存项的生命周期与引用计数；本地目录布局
- build 缓存：内存 diff 与磁盘 diff 的本地文件；`GenerateDiffCachePath`
- NFS 共享缓存：Filestore 挂载、`clean-nfs-cache` 的清理策略（LRU？读 `cmd/clean-nfs-cache/`）
- 缓存失效与磁盘水位
- 代码：上述目录 + `internal/template/build/storage/`、`cmd/clean-nfs-cache/`
- 图：本地目录布局（text）；缓存查找顺序

**35 · 沙箱网络**
- slot：一套 netns / veth / tap / IP 的预分配；池（新槽位与复用槽位）；槽位编号与 IP 的推导
- 建立一个槽位的步骤（读 `network/` 里的脚本或 netlink 调用）：netns、veth、tap、地址、路由、NAT 规则、DNS
- 出站过滤：默认拒绝的网段；`tcpfirewall`（用户态 TCP 防火墙）的机制与限制（每沙箱连接数）
- 沙箱之间的隔离；同一 guest IP 的复用
- 回收：清理规则与复用的风险（conntrack 残留）
- 代码：`internal/sandbox/network/`、`internal/tcpfirewall/`、`internal/portmap/`
- 图：一个槽位的网络拓扑；池的状态机
- ARM 差异：池大小（第 71 篇）

**36 · 代理与 envd 通信**
- orchestrator 内的 proxy（`internal/proxy/`）：给 edge 转发的沙箱流量入口；按 sandbox ID 找槽位 IP
- envd 客户端（`internal/sandbox/envd/`、`envd.go`）：`/init` 请求（access token、env vars、时间同步？）、超时与重试
- hyperloop：envd 回调 orchestrator 的通道（`/me`、`/logs`），做什么
- access token 的生成、传递与校验位置
- 代码：上述目录 + `internal/hyperloopserver/`
- 图：三条通道（edge → proxy → envd；orchestrator → envd init；envd → hyperloop）

**37 · Pause：脏页判定与差分导出**
- Pause RPC 的步骤：暂停 VM → snapshot/create（vmstate + 内存）→ 内存脏页判定 → 导出内存 diff → 导出磁盘 diff → 写 header 与 metadata → 上传 → 停沙箱
- 内存脏页判定：pagemap 读取（`present && !uffd-wp`）；上游 2026.09 是否已经改为从 Firecracker 拿脏页（看 `#1937` 相关代码：`GET /memory/dirty`？读代码确认哪条路径在用）
- `diffcreator.go`：diff 文件生成、header 合并规则
- 磁盘 diff：overlay 的 `Export`、块的紧凑写出与 header 偏移
- 上传：并发、重试、失败时的状态
- 与 Checkpoint RPC（SDK 的 `create_snapshot()`）的区别：snapshot 后以同一 sandbox ID 拉起新进程
- 代码：`sandbox.go` 的 `Pause()`、`pauseProcessMemory`、`pauseProcessRootfs`；`snapshot.go`、`diffcreator.go`；`internal/sandbox/build/`
- 图：Pause 时序；产物生成流程
- ARM 差异：脏页判据退化（第 72 篇）；与 checkpoint / restore 手册第 4 篇的关系

**38 · cgroup、资源记账与主机统计**
- cgroup v2：根 cgroup、每沙箱 cgroup、`CLONE_INTO_CGROUP` 的原子放置、限制项（CPU / 内存？读代码）
- host stats：采样什么、给谁用（放置、指标）；`hoststats*.go`
- 沙箱指标：CPU / 内存 / 磁盘用量从哪读（envd 上报还是宿主读）；ClickHouse 写入
- 代码：`internal/sandbox/cgroup/`、`hoststats.go`、`hoststats_collector.go`、`metrics.go`
- 图：资源记账的数据流
- ARM 差异：关闭宿主侧记账并在无 cgroup v2 时跳过初始化（第 73 篇）

**39 · 健康检查、错误语义与清理**
- `checks.go`：envd 健康探测的间隔与超时；失败几次算死；死了做什么
- 退出路径：guest 主动退出、FC 崩溃、宿主 kill、超时；每种路径谁先发现、清理顺序
- 错误分类：可重试 / 不可重试；gRPC 状态码映射（`server/sandboxes.go`）
- 清理的不变量：NBD 断开先于文件删除、槽位归还先于复用、cgroup 删除时机
- 代码：`checks.go`、`health.go`、`cleanup.go`、`server/sandboxes.go`
- 图：退出路径矩阵；清理顺序
- ARM 差异：健康检查参数放宽（第 73 篇）

**40 · Volumes 与 NFS proxy**
- Volume 概念（API 的 `/volumes`）与 orchestrator 的 Volume 服务（`internal/volumes/`）
- `nfsproxy`：为什么要在宿主上代理 NFS（jailed、logged、recovery 子包）；沙箱如何挂载
- 安全边界与失败恢复
- 代码：`internal/nfsproxy/`、`internal/volumes/`、`orchestrator.proto` 的 Volume 服务
- 图：挂载路径

### 第五部分　模板构建

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 41 | `41-template-build-overview.md` | 构建总览：从 Dockerfile 到可恢复的快照 | ◎ |
| 42 | `42-build-phases.md` | 阶段流水线 | ◎ |
| 43 | `43-rootfs-construction.md` | rootfs 制作 | ◎ |
| 44 | `44-build-sandbox-and-commands.md` | 构建期沙箱与命令 | ◎ |
| 45 | `45-layers-and-build-cache.md` | 层与构建缓存 | ◎ |
| 46 | `46-template-manager-service.md` | template-manager 服务 | ◎ |
| 47 | `47-orchestrator-dev-tools.md` | 本地开发工具（cmd/） | ◎ |

**41 · 构建总览**
- 输入：Dockerfile / 步骤列表 + 基础镜像 + start / ready 命令 + 资源规格；输出：一个 build（五个文件）
- 与 Docker build 的本质区别：产物是**运行中系统的快照**，不是镜像层
- 主流程：拉镜像 → 造 rootfs → 冷启动沙箱 → 执行步骤 → 跑 start 命令、等 ready → pause 成快照
- 构建在哪跑（build 节点）、多久、失败怎么办
- 代码：`internal/template/build/build.go`（或主文件）、`internal/template/server/`
- 图：主流程 flowchart

**42 · 阶段流水线**
- `phases/`：base、steps、user、finalize、optimize 各阶段做什么、输入输出、能否跳过（缓存命中）
- 阶段之间的沙箱状态：哪些阶段需要沙箱在跑、哪些只操作文件
- 日志与进度回报
- 代码：`internal/template/build/phases/`
- 图：阶段图；阶段 × 缓存矩阵

**43 · rootfs 制作**
- OCI 拉取与认证（`core/oci/`）；层解包成 ext4（`core/filesystem/`）；大小与预留
- systeminit：busybox 作为 init、`inittab.tpl`、provision 脚本的执行时机
- `provision.sh`：装哪些包、为什么、对 guest 发行版的假设（apt / dpkg）
- envd 注入与 `envd.service.tpl`；systemd 单元里的资源设置
- `configure.sh`（finalize 阶段）：默认用户、sudo、`/code`
- 代码：`internal/template/build/core/`、`phases/base/`、`phases/finalize/`
- 图：rootfs 生成流程；文件注入清单表
- ARM 差异：busybox arm64、平台、openEuler guest（第 74 篇）

**44 · 构建期沙箱与命令**
- 构建期沙箱怎么起（`sandbox/template_build.go`、`CreateSandbox` 冷启动）；与运行期沙箱的区别
- `sandboxtools`：在沙箱里跑命令的通道（走 envd）、日志流
- `commands/`：RUN、COPY、ENV、WORKDIR、USER、ARG 等的实现；COPY 的文件如何进沙箱（hash 上传的文件）
- 失败与重试
- 代码：`internal/template/build/commands/`、`sandboxtools/`、`internal/sandbox/template_build.go`
- 图：一条 RUN 指令的执行路径

**45 · 层与构建缓存**
- `layer/`：层的 hash 计算（指令 + 上下文）、缓存查找、命中时跳过阶段
- 缓存存储：本地与对象存储的 paths；`storage/cache/`
- 与 Docker 层缓存的异同；失效条件
- 代码：`internal/template/build/layer/`、`storage/`、`metrics/`
- 图：hash 链；缓存命中判定 flowchart

**46 · template-manager 服务**
- gRPC：TemplateCreate、TemplateBuildStatus、TemplateBuildDelete、InitLayerFileUpload
- 服务内部：构建队列、并发限制、状态存储、日志写入（`writer/`、`buildlogger/`）
- 与 orchestrator 同进程时共享什么
- 代码：`internal/template/server/`、`internal/template/build/writer/`、`buildlogger/`
- 图：服务结构；一次构建的状态流

**47 · 本地开发工具（cmd/）**
- `create-build`、`resume-build`、`inspect-build`、`mount-build-rootfs`、`show-build-diff`、`copy-build`、`hammer-file`、
  `simulate-gcs-traffic`、`simulate-nfs-traffic`、`clean-nfs-cache`：各自做什么、怎么用、在排障中的价值
- 用 `resume-build -iterations` 做恢复耗时测量的方法
- 代码：`packages/orchestrator/cmd/`、`packages/orchestrator/README.md`
- 图：工具 × 场景表

### 第六部分　envd：沙箱内守护进程

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 48 | `48-envd-overview.md` | envd 总览 | ◎ |
| 49 | `49-envd-process-service.md` | 进程服务 | ◎ |
| 50 | `50-envd-filesystem-service.md` | 文件系统服务与文件接口 | ◎ |
| 51 | `51-envd-ports-permissions-metrics.md` | 端口、权限与指标 | ◎ |
| 52 | `52-envd-legacy-and-sdk-compat.md` | legacy 服务与 SDK 兼容 | ◎ |

**48 · envd 总览**
- 启动：systemd 单元、监听端口（49983）、从 MMDS 读元数据（`internal/host/mmds.go`）
- `/init`：orchestrator 调用时做什么（access token、env vars、hostname、时间？）；快照恢复后的重新初始化
- 认证：access token 的校验位置；哪些接口免认证（health）
- 日志导出（`logs/exporter`）到 hyperloop
- 与 SDK 的两条协议：Connect-RPC（process / filesystem）与 REST（files、envs、health、metrics、init）
- 代码：`packages/envd/main.go`、`internal/api/`、`internal/host/`、`internal/logs/`、`spec/envd.yaml`
- 图：envd 内部结构；与外界的三条通道

**49 · 进程服务**
- `process.proto`：Start、Connect、Update、StreamInput、SendInput、SendSignal、List；流式响应的模式
- PTY 与非 PTY；stdout / stderr 合流；退出码；环境变量与 cwd
- 用户切换（以哪个用户跑）与权限（`internal/permissions/`）
- 断线重连：Connect 到已有进程
- 代码：`internal/services/process/`、`handler/`
- 图：Start 的流式时序

**50 · 文件系统服务与文件接口**
- `filesystem.proto`：Stat、MakeDir、Move、ListDir、Remove、WatchDir、Create/Get/RemoveWatcher
- REST `/files`：上传下载、多文件、路径与用户
- watch 的实现（inotify / fsnotify）与限制
- 代码：`internal/services/filesystem/`、`internal/api/`（files）
- 图：接口表

**51 · 端口、权限与指标**
- 端口扫描（`internal/port/`）：发现沙箱内监听端口，给谁用
- 权限模型：请求携带的用户、默认用户、root 的限制
- cgroups 服务（`services/cgroups`）与 `/metrics`
- 代码：`internal/port/`、`internal/permissions/`、`internal/services/cgroups/`
- 图：指标来源表

**52 · legacy 服务与 SDK 兼容**
- `services/legacy/`：旧协议为什么还在、谁在用；与新协议的映射
- e2b SDK（JS / Python）与 code-interpreter 如何调用 envd；HTTP/2 与连接复用；域名与端口编码
- 版本协商：envd 版本存在模板 metadata 里；SDK 的兼容矩阵
- 代码：`internal/services/legacy/`、`e2b-arm/packages/python-sdk/e2b/connection_config.py`（只看连接层）
- 图：SDK → envd 的调用面表

### 第七部分　边缘与流量

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 53 | `53-client-proxy-edge.md` | client-proxy（edge） | ◎ |
| 54 | `54-shared-proxy-library.md` | 共享代理库 | ◎ |
| 55 | `55-sandbox-catalog-and-routing.md` | 沙箱目录与跨节点路由 | ◎ |
| 56 | `56-edge-api.md` | edge API | ◎ |
| 57 | `57-docker-reverse-proxy.md` | docker-reverse-proxy | ◎ |

**53 · client-proxy（edge）**
- 进程结构：上游 2026.09 的 client-proxy 只有流量代理端口与健康端口（读 `packages/client-proxy/main.go` 与 `iac/modules/job-client-proxy/jobs/client-proxy.hcl`）；「edge API」的服务端不在本仓库（见第 56 篇）
- 域名解析：`<port>-<sandboxID>.<domain>` 的解析规则（`packages/shared/pkg/proxy/host.go` 的 `parseHost`；clientID 已退化为常量，不参与寻址）；从 sandbox ID 找到节点（sandbox catalog）
- 转发到 orchestrator 的 proxy 端口；WebSocket 与长连接；错误页
- 代码：`packages/client-proxy/`、`internal/proxy/`
- 图：请求路径；域名解析规则表

**54 · 共享代理库**
- `packages/shared/pkg/proxy/`：连接池（`pool/`）、模板化错误页（`template/`）、超时、重试
- orchestrator 侧与 edge 侧共用什么
- 代码：`packages/shared/pkg/proxy/`
- 图：类结构与复用关系

**55 · 沙箱目录与跨节点路由**
- sandbox catalog：Redis 里的 sandbox → 节点映射；写入者（api）与读取者（edge）；TTL
- resume-on-connect：`proxy.proto` 的 `ResumeSandbox` —— 访问已暂停沙箱时由 edge 触发恢复？读代码确认
- 多 edge 实例与一致性
- 代码：`packages/shared/pkg/sandbox-catalog/`、`packages/shared/pkg/grpc/proxy/`、`packages/client-proxy/`
- 图：查找时序

**56 · edge API**
- `openapi-edge.yml`：service discovery、节点列表、日志与指标代理、`/v1/info`；这是一份**只生成客户端**的规范（`packages/shared/pkg/http/edge/cfg.yaml`），服务端实现不在 infra 仓库 —— 说明这一事实、推测它的部署位置（标为推论）
- api 如何通过 edge 客户端访问远端集群（`packages/api/internal/clusters/discovery/remote.go`，第 21 篇的另一半）
- ARM 适配版的 `edge.hcl` / `helm/templates/edge.yaml` 里跑的是什么镜像、开了哪些端口（读 ARM 补丁）
- 代码：`packages/shared/pkg/http/edge/`、`packages/api/internal/clusters/discovery/remote.go`、ARM 补丁中的 edge job
- 图：端点表

**57 · docker-reverse-proxy**
- 模板构建时 CLI 推镜像到 e2b 的 registry：认证（access token 换 registry token）、转发到 Artifact Registry
- 代码：`packages/docker-reverse-proxy/`
- 图：推送时序

### 第八部分　数据与可观测

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 58 | `58-postgres-schema-and-migrations.md` | Postgres 模式与迁移 | ◎ |
| 59 | `59-clickhouse.md` | ClickHouse | ◎ |
| 60 | `60-telemetry.md` | 遥测：tracing、metrics、logs | ◎ |
| 61 | `61-events-and-webhooks.md` | 沙箱事件与 webhook | ◎ |
| 62 | `62-testing.md` | 测试体系 | ◎ |

**58 · Postgres 模式与迁移**
- 表与关系：teams、users、tiers、api_keys、access_tokens、envs（模板）、env_builds、env_aliases、snapshots、
  clusters、volumes 等（以 `packages/db/migrations/` 为准）
- 迁移工具（goose）与 migrator 容器；本地 migrate
- sqlc 查询的组织；事务边界
- `packages/db/pkg/retry`、`testutils`
- 代码：`packages/db/`
- 图：ER 图（mermaid erDiagram 或 classDiagram）

**59 · ClickHouse**
- 表：沙箱指标、事件、主机统计；`packages/clickhouse/migrations/`
- batcher：批量写入的队列、大小与延迟参数
- 查询侧：api 的 metrics 端点
- 代码：`packages/clickhouse/`
- 图：写入路径；表结构表

**60 · 遥测：tracing、metrics、logs**
- OpenTelemetry 的组织：`packages/shared/pkg/telemetry`（tracer、meter、exporter）、`logger`（zap + otel）
- otel-collector 与 logs-collector 的 nomad job；Loki；Grafana
- 沙箱日志（`logger/sandbox`）与 envd 日志的汇聚
- 关键 span 与 metric 名称表（从代码中的常量收集）
- 代码：`packages/shared/pkg/telemetry/`、`packages/shared/pkg/logger/`、`packages/otel-collector/`、`iac/provider-gcp/nomad/jobs/otel-collector.hcl`、`logs-collector.hcl`
- 图：遥测数据流

**61 · 沙箱事件与 webhook**
- `packages/shared/pkg/events`、orchestrator 的 `internal/events`、`sbxEventsService`：事件类型、投递、失败处理
- 执行指标事件（`executionEventDataKey`）
- 代码：上述目录
- 图：事件流

**62 · 测试体系**
- 单元测试的组织与 mocks（`generate-mocks`）
- 集成测试（`tests/integration`）：依赖什么环境、怎么跑
- periodic-test 与 benchmark（`benchmark_test.go`）
- 代码：`tests/`、各 package 的 `_test.go`
- 图：测试层次表

### 第九部分　上游的部署与开发

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 63 | `63-gcp-terraform.md` | GCP 上的部署 | ◎ |
| 64 | `64-nomad-jobs.md` | Nomad job 详解 | ◎ |
| 65 | `65-build-and-release.md` | 构建与发布 | ◎ |
| 66 | `66-local-development.md` | 本地开发环境 | ◎ |

**63 · GCP 上的部署**
- `iac/provider-gcp`：main、api、docker-reverse-proxy、redis、remote-repository、nomad-cluster、nomad-cluster-disk-image、nomad
- 节点池：server、api、build、client、clickhouse；机器规格与磁盘；Filestore
- 节点初始化脚本（`start-client.sh` 等）：装 FC 与内核、nbd、hugepages、目录
- secrets 与域名（Cloudflare）
- `self-host.md` 的步骤为什么是那个顺序
- 代码：`iac/`、`self-host.md`
- 图：GCP 资源拓扑

**64 · Nomad job 详解**
- 每个 job：api、edge、orchestrator、template-manager、redis、clickhouse、loki、otel-collector、logs-collector、
  docker-reverse-proxy、nomad-autoscaler、clean-nfs-cache：driver、资源、端口、env、constraint、健康检查
- `deploy.sh` 与 `env.template` 的渲染
- 代码：`iac/provider-gcp/nomad/jobs/`（api、redis、docker-reverse-proxy、template-manager、nomad-autoscaler、clean-nfs-cache）与 `iac/modules/job-*/jobs/`（orchestrator、client-proxy、ingress、loki、clickhouse、otel-collector、logs-collector、dashboard-api）
- 图：job × 节点池矩阵

**65 · 构建与发布**
- Makefile 目标：build、build-and-upload、copy-public-builds、version；Docker 镜像与 GCS 二进制
- 版本号与 `VERSION`；CI（`.github/`）
- 代码：`Makefile`、`packages/*/Makefile`、`scripts/`
- 图：发布流水线

**66 · 本地开发环境**
- `DEV-LOCAL.md`：local-infra、seed、build base template、各服务 run-local
- `packages/local-dev`
- 调试技巧：远程 orchestrator、日志、常见错误
- 代码：`DEV-LOCAL.md`、`packages/local-dev/`、`Makefile`
- 图：本地拓扑

### 第十部分　ARM 适配版

本部分的主线：**上游在 x86 + Ubuntu guest + GCP 上做的假设，在 aarch64 + openEuler + 私有环境上哪些不成立，
分别怎么处理，代价是什么。** 每篇都要回答「改了什么 / 为什么 / 代价与后果 / 有没有更好的做法」。
凡引用补丁内容，以 `tmp/e2b-book-src/arm/` 与 `git diff f8c2f0cde fbee6fcd1` 为准。

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 67 | `67-arm-port-overview.md` | ARM 适配总览 | ◎ |
| 68 | `68-aarch64-virtualization-differences.md` | aarch64 与 x86 的虚拟化差异 | ◎ |
| 69 | `69-guest-kernel-for-arm.md` | guest 内核 | ◎ |
| 70 | `70-firecracker-fork.md` | e2b 的 Firecracker 分叉与 ARM 构建 | ◎ |
| 71 | `71-orchestrator-arm-fc-changes.md` | orchestrator 的 ARM 改动 I：FC 启动、超时与并发 | ◎ |
| 72 | `72-uffd-on-arm.md` | orchestrator 的 ARM 改动 II：写保护退化 | ◎ |
| 73 | `73-cgroup-and-host-compat.md` | orchestrator 的 ARM 改动 III：宿主兼容 | ◎ |
| 74 | `74-template-build-on-arm.md` | 模板构建的 ARM 改动 | ◎ |
| 75 | `75-minio-storage.md` | MinIO 存储 provider | ◎ |
| 76 | `76-k8s-discovery.md` | Kubernetes 服务发现 | ◎ |
| 77 | `77-api-and-flags-on-arm.md` | API 层与特性开关默认值的调整 | ◎ |
| 78 | `78-helm-k8s-deployment.md` | 部署形态一：Helm / Kubernetes | ◎ |
| 79 | `79-nomad-multinode-deployment.md` | 部署形态二：Nomad 多节点 | ◎ |
| 80 | `80-single-node-rpm.md` | 部署形态三：单机离线 RPM | ◎ |
| 81 | `81-single-node-traffic.md` | 单机流量架构 | ◎ |
| 82 | `82-host-kernel-nbd-hugepages.md` | 宿主内核要求与调优 | ◎ |
| 83 | `83-sdk-adaptation.md` | SDK 侧适配 | ◎ |
| 84 | `84-arm-performance.md` | ARM 性能实测 | ◎ |
| 85 | `85-dev-workflow-and-packaging.md` | 开发与出包工作流 | ◎ |
| 86 | `86-known-issues-and-debt.md` | 已知问题与技术债 | ◎ |
| 87 | `87-beyond-checkpoint-restore.md` | 后续功能开发：checkpoint / restore 与展望 | ◎ |

**67 · ARM 适配总览**
- 目标平台：鲲鹏 920B / 950、openEuler、无外网、私有对象存储与镜像仓库、Nomad 单机或 k8s
- 改动地图：94 个文件按「架构相关 / 发行版相关 / 部署环境相关 / 参数放宽 / 可观测埋点」五类分组，表
- 四个仓库与交付形态（infra 补丁、Firecracker 二进制、内核二进制、RPM）
- 改动的三种性质：必要的架构适配、环境替换（GCS → MinIO，Nomad → k8s）、经验性调参 —— 后两类可回退
- 阅读顺序
- 代码：`git diff --stat f8c2f0cde fbee6fcd1`
- 图：改动分类表；四个仓库到 RPM 的融合图

**68 · aarch64 与 x86 的虚拟化差异**
- KVM on arm64：Stage-2、VHE、GICv3 与中断、PSCI、定时器（arch timer vs kvm-clock）
- 启动：无 BIOS / PCI 的差异在 arm64 上更自然；FDT 与内核加载；`pci=off`、`i8042` 等参数为什么只属于 x86
- 页大小与大页：4K / 64K 内核、2 MiB HugeTLB 在 arm64 上的条件
- 脏页跟踪：arm64 上 userfaultfd WP 的支持时间线（内核版本）与 HDBSS（ARMv9.5）
- Firecracker 对 aarch64 的支持状态（上游 CI、已知限制）
- 代码：`src/vmm/src/arch/aarch64/`（分叉 Firecracker）
- 图：差异对照表

**69 · guest 内核**
- fc-kernels 的构建流程：`kernel_versions.txt`、`configs/arm64/6.1.158.config`、`build.sh`、输出命名
- arm64 config 里与 e2b 相关的项：virtio-mmio、overlayfs、userfaultfd、hugetlb、network、cgroup
- 内核补丁：`0001-virtio_balloon-*`（上游同款）、`0002-overlayfs-hot-switch-checkpoint.patch`（后续功能，只提及，第 87 篇）
- `vmlinux.bin.arm` 与 `vmlinux.bin.arm.openeuler` 两个二进制的差别与用途
- 内核参数在 ARM 上的差异（第 71 篇）
- 代码：`fc-kernels-arm/`、`e2b-infra.spec` 的 Source4–6
- 图：构建流程；config 项表

**70 · e2b 的 Firecracker 分叉与 ARM 构建**
- e2b-dev/firecracker 的 `firecracker-v1.12-direct-mem` 分支相对上游 v1.12.1 加了什么（读代码：内存直接映射 / uffd 相关 / `GET /memory/dirty`？以 `kasandbox-arm/firecracker` 在 `b8e85c3` 的代码为准，对照上游 v1.12.1 的已知 API）
- 这个分叉已于 2026-08 归档，上游 infra 如何过渡（`flags.go` 的默认版本常量）
- ARM 上的构建：`scripts/build.sh` 的改动、`main.rs` 的改动（coredump 修复）、静态链接
- 版本命名：二进制装到 `/fc-versions/v1.13.1/`，与源码 1.12.1 的关系
- 代码：`tmp/e2b-book-src/kasandbox-arm/firecracker/`，`git -C KASandbox diff 9e880db b8e85c3 -- firecracker/`
- 图：分叉关系图；API 扩展表

**71 · orchestrator 的 ARM 改动 I：FC 启动、超时与并发**
- `fc/process.go`：内核参数按 `runtime.GOARCH` 分支；`clocksource=kvm-clock` 只在 x86；埋点日志
- `fc/client.go`：SMT 关闭、`track_dirty_pages` 移除 —— 后果
- 超时与并发：`socket.Wait` 超时、`uffdMsgListenerTimeout`、`requestTimeout`、`acquireTimeout`、
  `maxStartingInstancesPerNode` 及其环境变量化、`TryAcquire` → `Acquire`；网络池大小
- 每一项：上游值 / ARM 值 / 改动理由（推论要标注）/ 副作用
- 代码：补丁中 `internal/sandbox/fc/`、`socket/`、`uffd/uffd.go`、`server/`、`network/pool.go`
- 图：参数对照表

**72 · orchestrator 的 ARM 改动 II：写保护退化**
- 上游脏页判据：`UFFDIO_COPY_MODE_WP` + pagemap bit 57；ARM 适配版注释掉 WP —— 为什么（内核对 HugeTLB / arm64 的 WP 支持；读上游 `#1989` 的 `UFFD_FEATURE_WP_ASYNC` 定义）
- 后果：「读过即脏」，内存 diff 是真实脏页集的超集；正确性不变、成本模型变
- 实测量级（引用 `deploy-docs/09` 的数据，注明条件）
- 修复方向：HDBSS 硬件标脏（checkpoint / restore 手册第 7 篇）、内核升级后恢复 WP
- 代码：补丁中 `uffd/userfaultfd/userfaultfd.go`；上游 `uffd/userfaultfd/`
- 图：判据对照表；超集示意

**73 · orchestrator 的 ARM 改动 III：宿主兼容**
- cgroup：`NewManager` 在无 v2 时不再报错、`Initialize` 跳过、`CLONE_INTO_CGROUP` 注释掉 —— 沙箱资源记账因此失去什么
- `machineinfo`：gopsutil 在 arm64 上拿不到 Family / Model 的 fallback
- 健康检查：间隔 20 s → 300 s、超时 100 ms → 60 s —— 后果（死沙箱发现延迟）
- `block/cache.go` 的 recover 与范围检查：防什么（SIGBUS？）、是否真能防
- `envd.service.tpl` 去掉的 cgroup 相关项
- 代码：补丁中 `cgroup/manager.go`、`service/machineinfo/`、`checks.go`、`block/cache.go`、`rootfs/files/`
- 图：改动 × 后果表

**74 · 模板构建的 ARM 改动**
- busybox：arm64 二进制嵌入与按架构选择；1.35 与 1.36.1 的差别
- OCI 默认平台改为 arm64 —— 硬编码的问题
- openEuler guest：`provision.sh` 的发行版检测、dnf、包列表变化（去掉 fuse3 / iptables / git / nfs-common 的后果）；
  `configure.sh` 改 `#!/bin/sh`、`useradd` / `wheel`；`commands/user.go` 同样的分支
- `inittab.tpl` 的换行修正
- 代码：补丁中 `internal/template/build/`
- 图：发行版差异表

**75 · MinIO 存储 provider**
- `storage_minio.go`：接口实现（Open / Upload / Delete / List / 范围读）、超时常量、缓冲区、SSL
- 与 GCS / S3 provider 的对照：哪些语义不同（范围读、分段上传、错误映射）
- 配置：`STORAGE_PROVIDER=MinioBucket`、endpoint / key / secret 环境变量；默认 provider 改为 MinIO 的影响
- 单机离线版实际用的是 Local 还是 MinIO（读 `deploy-docs/10` 与 nomad job env）
- 代码：`packages/shared/pkg/storage/storage_minio.go`、`storage.go`
- 图：provider 对照表

**76 · Kubernetes 服务发现**
- 抽象：`discovery.ServiceDiscovery` 接口、`Allocation`；Nomad 实现的改造；k8s 实现（in-cluster config、label selector）
- api 侧的 `NodeDiscovery`：`k8s_discovery.go`（按节点 label 找 orchestrator）与 `nomad_discovery.go`
- 选择逻辑：环境变量 / 配置决定用哪个
- 与 Helm 部署（第 78 篇）的对应
- 代码：补丁中 `packages/shared/pkg/clusters/discovery/`、`packages/api/internal/orchestrator/*discovery.go`、`clusters/`
- 图：两种发现方式对照

**77 · API 层与特性开关默认值的调整**
- `flags.go`：`max-sandboxes-per-node` 200 → 10000、过量分配 400 → 1200、envd init 超时 50 ms → 120 s、预取 worker 数
- `grpc/server.go`：`MaxConcurrentStreams`、连接年龄
- api 的 `sandbox_features.go`、`handlers/store.go`、`clusters/` 的改动
- 每项的动机（推论标注）与风险
- 代码：补丁中 `packages/api/`、`packages/shared/pkg/feature-flags/`、`grpc/`
- 图：参数对照表

**78 · 部署形态一：Helm / Kubernetes**
- `helm/`：Chart、values 模板、每个 template（api、edge、orchestrator、template-manager、redis、clickhouse、loki、otel、logs-collector、rbac）
- orchestrator 在 k8s 里怎么跑（DaemonSet？特权？hostPath？读 yaml）；节点 label
- 与 Nomad 形态的对照：什么概念对应什么
- 代码：`helm/`
- 图：k8s 资源拓扑

**79 · 部署形态二：Nomad 多节点**
- `e2b-infra/README.md` 的多节点安装：四个集群（api / build / default / server）、前提（Postgres、Harbor、MinIO）
- 补丁里对 nomad job 与集群脚本的改动（`iac/provider-gcp/nomad/jobs/*.hcl`、`nomad-cluster/scripts/*.sh`）：去 GCP 化
- `docs/zh/install.md` 的流程
- 代码：`e2b-infra/README.md`、`docs/zh/`、补丁中 `iac/`
- 图：多节点拓扑

**80 · 部署形态三：单机离线 RPM**
- `e2b-infra.spec`：Source 列表、`%prep` 的 patch 与工具链、`%build` 的离线 Go 构建、`%install` 的目录映射
- `build.sh -i`：装 Postgres、MinIO、Harbor、Nginx、SDK；`build.sh -s`：Consul、Nomad、ACL、宿主调优、job 提交
- `/opt/e2b-infra` 布局；`init-client.sh` / `start-client.sh` 与上游脚本的关系
- 本篇是原理讲解；操作步骤引用 `single-node-offline-deploy.md` 与 `deploy-docs/`，不复制
- 代码：`e2b-infra/e2b-infra.spec`、`e2b-deploy/build.sh`、`e2b-deploy/dep/*.sh`
- 图：安装流程；目录布局（text）

**81 · 单机流量架构**
- dnsmasq 分流（`*.e2b.app` → 127.0.0.1、`*.consul` → Consul DNS）、iptables 80 → 3002、nginx 443 → Harbor
- 三类流量的完整链路：SDK → api；SDK → 沙箱（client-proxy → orchestrator proxy → envd）；构建期拉镜像
- 与上游（Cloudflare + GCP LB）的对照
- 代码：`e2b-deploy/dep/nginx.conf`、`build.sh` 中的 dnsmasq / iptables 段、`deploy-docs/07`
- 图：流量路径图

**82 · 宿主内核要求与调优**
- nbd 模块：`nbds_max`、自编译模块的固化、udev 规则；hugepages 预留；KVM 与 `/dev/kvm` 权限；SELinux
- openEuler 内核版本与 userfaultfd / HugeTLB 的能力；`HDBSS_KUNPENG950_KERNEL_6.6.0_515.md` 的要点（只提能力，不讲 checkpoint）
- `build.sh -s` 里的 sysctl 与 ulimit
- 代码：`single-node-offline-deploy.md` §0、`build.sh`、`init-client.sh`
- 图：宿主能力清单表

**83 · SDK 侧适配**
- e2b Python SDK 2.20.0 与 code_interpreter 2.4.1 的配套；`connection_config.py` 的 http / 域名改动；`code_interpreter_sync.py`
- 为什么要改 SDK：私有域名、http 而非 https、自签证书
- `build.sh` 的 `install_e2b` 与 `install.py` 的覆盖层
- 代码：`e2b-deploy/dep/connection_config.py`、`code_interpreter_sync.py`、`e2b-arm/packages/python-sdk/e2b/connection_config.py`
- 图：SDK 配置项表

**84 · ARM 性能实测**
- 测什么：沙箱恢复各阶段耗时（`[ResumeSandbox]` 埋点）、并发创建、模板构建
- `benchmark/` 的工具：`run_benchmark.py`、`parse_report.py`、`build_template.py`；口径说明
- 已有数据（引用 benchmark 目录下的报告，注明机型 / 内核 / 并发）；与上游公开数字的对照
- 瓶颈：FC 启动（netns exec）、uffd、envd init；`FC启动优化-netns-exec.md` 的结论
- 代码：`e2b-infra/benchmark/`
- 图：阶段耗时分解图（表）；瓶颈表

**85 · 开发与出包工作流**
- 两条线：源码线（infra-arm 工作树 → 编译 → 直接换二进制）与部署线（重生成 patch → RPM）
- `regen-e2b-infra-patch.sh` 的思路：纯净 tarball + 全量补丁；`patch_e2b.py`
- 四个仓库的融合方式（`仓库融合说明.md`）
- 代码：`deploy-docs/08`、`仓库融合说明.md`、`e2b-infra.spec`
- 图：两条线的流程图

**86 · 已知问题与技术债**
- 清单：读过即脏、cgroup 记账缺失、健康检查放宽、OCI 平台硬编码、超时全面放宽、去掉的 guest 包、
  `DefaultFirecrackerVersion` 命名、默认 provider 改动对上游合并的影响
- 每项：现象、根因、影响范围、建议修法、与上游合并的策略
- 图：问题 × 严重度 × 修法表

**87 · 后续功能开发：checkpoint / restore 与展望**
- 问题：原生 pause / resume 的成本模型不适合高频回滚；checkpoint / restore 手册的定位与阅读入口
- 三处关键能力的一页概览：HDBSS 硬件标脏、分叉 Firecracker 的原地回滚接口、磁盘分层封存；只讲「是什么」，链接过去
- overlayfs 热切换内核补丁（fc-kernels 的 `0002`）的意图
- 展望：多架构共存（同一集群 x86 + arm64）、上游合并策略、k8s 形态成熟度
- 代码：`e2b-infra-docs/rollback/docs/00-design-overview.md`、`fc-kernels-arm/patches/6.1.158/`
- 图：功能关系图

### 附录

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 88 | `88-glossary.md` | 术语表 | ◎ |
| 89 | `89-code-map.md` | 代码地图 | ◎ |
| 90 | `90-config-reference.md` | 环境变量与配置项总表 | ◎ |
| 91 | `91-ports-paths-keys.md` | 端口、路径与存储键总表 | ◎ |

**88 · 术语表**：每条 2–4 句，给出英文、定义、首次出现的篇目。按拼音或字母排序。
**89 · 代码地图**：目录 → 职责 → 讲解篇目；分上游与 ARM 补丁两张表。
**90 · 配置总表**：环境变量 / feature flag / 常量，含默认值、读取位置、ARM 适配版的改动、讲解篇目。
**91 · 端口、路径与存储键总表**：进程端口、宿主目录、对象存储键、Redis key、Postgres 表，各一张表。

---

## 四、编写流程

1. **规划**（本文件 + STYLE.md）。
2. **分波编写**：按部派发，每篇一个编写者，并行；编写者只写自己那一篇。
   - 第 1 波：第〇（01）、一、二部分
   - 第 2 波：第三、四部分
   - 第 3 波：第五、六、七、八部分
   - 第 4 波：第九、十部分
   - 第 5 波：00 与附录（依赖全书）
3. **每波审校**：对照 STYLE.md 的自检清单；`tools/mdlinks.py` 查链接与锚点；`tools/mdmermaid.mjs` 查 mermaid；
   抽查代码论断；统一术语；补交叉链接的锚点。
4. **全书终审**：通读一遍，处理重复与矛盾；更新本文件的状态列；生成 README 的目录。

### 编写者交付物

- 文档本身（`e2b-infra/NN-xxx.md`）
- 一段交付说明（写在回复里，不进文档）：本篇的核心论断清单、未能从代码验证而标为推论的地方、
  发现的与大纲不符之处、建议其它篇目补充或修改的地方
