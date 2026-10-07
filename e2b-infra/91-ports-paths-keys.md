# 91 · 端口、路径与存储键总表

> 全书出现过的端口号、宿主目录、对象存储键、Redis 键与 Postgres 表，集中成五张查阅表。
> 每一行给出取值来源与讲解它的篇目；正文只在表本身说不清楚的地方补几句。
>
> **读者**：部署、排障或改配置时需要「这个数字是从哪来的」的人　**预备**：无　
> **代码**：`packages/shared/pkg/consts/`、`packages/orchestrator/internal/cfg/model.go`、
> `packages/shared/pkg/storage/`、`packages/api/internal/sandbox/storage/redis/`、`packages/db/`

---

## 0. 怎么用这几张表

本篇是一份索引，不是一篇讲解。表里的每个取值都从三处对齐过：Go 代码里的 `envDefault`
与常量、GCP 部署的 Terraform 变量与 Nomad job、以及单机离线版的 `e2b-deploy/dep/.env`
与它渲染的 hcl。三者不一致的行都保留了各自的值，因为排障时最常踩的坑正是
「代码里写着 A，机器上跑的是 B」。凡是本书没有对应篇目讲解、或代码里读不出确切来源的条目，
都在表下的注里标出。术语与版本称谓按[写作规约](STYLE.md)。

---

## 1. 进程端口

优先级从低到高是：Go 代码的 `envDefault` 或 flag 默认值、Terraform 变量、Nomad job 注入的环境变量。
「GCP 部署」列取 `iac/provider-gcp/variables.tf` 的默认值，
「ARM 单机」列取 `e2b-deploy/dep/.env` 与 `dep/template-manager.hcl` 的取值。

| 进程与用途 | 上游代码默认 | GCP 部署 | ARM 单机 | 来源篇目 |
|---|---|---|---|---|
| api：对外 REST 与 `/health` | 80（`--port`） | 50001 | 3000 | [第 10 篇 §4](10-system-architecture.md#4-端口表) |
| api：gRPC，供 edge 调 `ResumeSandbox` | 5009 | 5009 | 5009 | [第 55 篇](55-sandbox-catalog-and-routing.md) |
| orchestrator：gRPC 与 HTTP `/health` 复用 | 5008 | 5008 | 5008 | [第 25 篇](25-orchestrator-process.md) |
| orchestrator：沙箱 HTTP 反向代理 | 5007 | 5007 | 5007 | [第 36 篇](36-orchestrator-proxy-and-envd-client.md) |
| orchestrator：hyperloop，沙箱内向宿主发起 | 5010 | 5010 | 5010 | [第 36 篇 §5](36-orchestrator-proxy-and-envd-client.md#5-通道三hyperloop) |
| orchestrator：NFS 代理 | 5011 | 5011 | 5011，未启用 | [第 40 篇](40-volumes-and-nfsproxy.md) |
| orchestrator：portmapper | 5012 | 5012 | 5012，未启用 | [第 35 篇 §6](35-sandbox-networking.md#6-portmap一个只回答两个问题的-rpc-服务) |
| orchestrator：出口 TCP 防火墙 HTTP / TLS / 其它 | 5016 / 5017 / 5018 | 同左 | 同左 | [第 35 篇 §5](35-sandbox-networking.md#5-tcp-防火墙进程) |
| template-manager：gRPC | 5008 | 5008 | 5008，与 orchestrator 同进程 | [第 46 篇](46-template-manager-service.md) |
| client-proxy：沙箱流量入口 | 3002 | 3002 | 3002 | [第 53 篇](53-client-proxy-edge.md) |
| client-proxy：健康检查 | 3003 | 3001 | 3003 | [第 53 篇](53-client-proxy-edge.md) |
| docker-reverse-proxy：Registry 协议 | 5000（`--port`） | 5000 | 5000，未部署 | [第 57 篇](57-docker-reverse-proxy.md) |
| dashboard-api：REST | 3010 | Nomad 动态分配 | 未部署 | [第 10 篇 §4](10-system-architecture.md#4-端口表) |
| envd：沙箱内 HTTP 与 Connect-RPC | 49983 | 49983 | 49983 | [第 48 篇](48-envd-overview.md) |
| ingress：Traefik web 入口 / 控制面 | 无 | 8800 / 8900 | 未部署，改用 nginx 80 / 443 | [第 81 篇](81-single-node-traffic.md) |
| Nomad：HTTP API | 无 | 4646 | 4646 | [第 09 篇](09-nomad-consul-terraform.md) |
| Consul：HTTP API / 本机 DNS | 无 | 8500 / 8600 | 8500 / 8600 | [第 09 篇](09-nomad-consul-terraform.md) |
| Redis：运行态与路由目录 | 无 | 6379 | 6379 | [第 20 篇](20-sandbox-state-storage.md) |
| Loki：日志查询 | 无 | 3100 | 3100，非默认部署 | [第 60 篇](60-telemetry.md) |
| ClickHouse：原生 / HTTP 健康 / 指标 | 无 | 9000 / 8123 | 9000 / 8123 / 9363，默认副本数 0 | [第 59 篇](59-clickhouse.md) |
| otel-collector：OTLP gRPC / HTTP / 健康 / 自身指标 | 无 | 4317 / 4318 / 13133 / 8888 | 同左 | [第 60 篇](60-telemetry.md) |
| logs-collector：Vector 接收 / 健康 | 无 | 30006 / 44313 | 30006 / 44313 | [第 60 篇](60-telemetry.md) |
| PostgreSQL | 无 | 托管实例 | 5432，本机容器 | [第 58 篇](58-postgres-schema-and-migrations.md) |
| MinIO：S3 接口 / 控制台 | 无 | 不适用 | 9000 / 9001 | [第 75 篇](75-minio-storage.md) |
| Harbor：镜像仓库 HTTP | 无 | 不适用 | 2900 | [第 80 篇](80-single-node-rpm.md) |

五处差异值得单独记住。

**client-proxy 的健康端口三方不一致。** 代码里 `packages/client-proxy/internal/cfg/model.go`
的 `HEALTH_PORT` 默认 3003，GCP 的 `client_proxy_health_port` 是 3001，
单机离线版的 `EDGE_HEALTH_PORT` 又回到 3003。三个数字都在用，排障时以进程实际拿到的环境变量为准。

**orchestrator 的 5008 同时承载 gRPC 与 HTTP `/health`**，靠 `main.go` 里的 `cmux` 在同一个监听上分流。
端口值来自 `packages/shared/pkg/consts/sandboxes.go` 的 `OrchestratorAPIPort`
（读 `ORCHESTRATOR_PORT`，缺省 5008）与 `internal/cfg/model.go` 的 `GRPC_PORT`（同样缺省 5008），
两处是各自独立的解析，改端口时要一起改。

**5010 到 5018 只对沙箱可见。** 它们监听在宿主上，沙箱经由
`SANDBOX_ORCHESTRATOR_IP`（`internal/sandbox/network/pool.go` 的 `Config`，默认 `192.0.2.1`，
一个文档保留地址）访问，集群里其它节点访问不到。

**单机离线版只跑四个 Nomad job**：`deploy.sh` 的 `JOBS` 数组是 redis、template-manager、edge、api。
真正执行沙箱的 orchestrator 逻辑不在 `orchestrator.hcl` 里，而是由 `dep/template-manager.hcl`
以 `ORCHESTRATOR_SERVICES = "orchestrator,template-manager"` 在同一个进程里跑起来的，
命令行是 `/usr/bin/template-manager --port 5008`。

**单机离线版上 MinIO 与 ClickHouse 的默认端口都是 9000。** 前者来自 `build.sh` 的 `MINIO_PORT`，
后者来自 `.env` 的 `CLICKHOUSE_SERVER_PORT`。默认配置下 `CLICKHOUSE_SERVER_COUNT=0`，
ClickHouse 不部署，所以冲突不会发生；把 ClickHouse 打开时必须先改掉其中一个。

`.env` 里还留着一个 `DNS_PORT=5353`。上游 2026.09 的 `iac/` 与 `packages/` 里没有任何地方读它
（唯一的同名变量在 `packages/api/.env.local` 里，值是 9953）。**推论**：这是 client-proxy
早期自带 DNS 服务时的遗留变量，现在不起作用。

---

## 2. 宿主目录与文件

除注明外，路径都由 `packages/orchestrator/internal/cfg/model.go` 的 `BuilderConfig`
与 `packages/shared/pkg/storage/sandbox.go` 的 `Config` 定义，
由 `packages/orchestrator/main.go` 的 `ensureDirs()` 以 `0700` 创建（空值跳过），
先经 `makePathsAbsolute()` 转成绝对路径。

| 路径 | 环境变量或常量 | 内容 | 来源篇目 |
|---|---|---|---|
| `/orchestrator` | `ORCHESTRATOR_BASE_PATH` | 节点本地盘的根，其余四个目录都拼在它下面 | [第 13 篇 §4.1](13-storage-landscape.md#41-一个-client-节点的目录) |
| `/orchestrator/build` | `DEFAULT_CACHE_DIR` | 分片缓存文件与 pause 产生的 diff；进程启动时整目录清空 | [第 34 篇 §3](34-template-cache-and-local-storage.md#3-节点本地目录谁建谁删) |
| `/orchestrator/template` | `TEMPLATE_CACHE_DIR` | `<build-id>/cache/<uuid>/` 下的 snapfile 与 metadata.json | [第 34 篇 §3](34-template-cache-and-local-storage.md#3-节点本地目录谁建谁删) |
| `/orchestrator/sandbox` | `SANDBOX_CACHE_DIR` | `rootfs-<sandbox-id>-<rand>.cow` 与同名 `.link` | [第 33 篇](33-nbd-and-rootfs.md) |
| `/orchestrator/build-templates` | `TEMPLATES_DIR` | 模板构建期的中间产物 | [第 42 篇](42-build-phases.md) |
| `/orchestrator/shared-store/chunks-cache` | `SHARED_CHUNK_CACHE_PATH` | NFS 共享分片缓存的挂载点 | [第 34 篇 §7](34-template-cache-and-local-storage.md#7-nfs-共享缓存一个只能靠-atime-的清理器) |
| `/orchestrator.lock` | `ORCHESTRATOR_LOCK_PATH` | 同一节点上防止两个 orchestrator 同时跑的文件锁 | [第 25 篇](25-orchestrator-process.md) |
| `/mnt/snapshot-cache` | `SNAPSHOT_CACHE_DIR` | 65 GiB tmpfs；上游 2026.09 里没有代码写入它 | [第 34 篇 §3](34-template-cache-and-local-storage.md#3-节点本地目录谁建谁删) |
| `/mnt/hugepages` | 开机脚本常量 | hugetlbfs 挂载点，2 MiB 大页 | [第 32 篇](32-memory-prefetch-and-hugepages.md) |
| `/fc-vm` | `SANDBOX_DIR` | 每台沙箱在私有挂载命名空间里挂的 tmpfs，放 rootfs 与内核的符号链接 | [第 28 篇](28-firecracker-process-management.md) |
| `/fc-versions/<version>/firecracker` | `FIRECRACKER_VERSIONS_DIR` | Firecracker 二进制，按版本目录分开 | [第 28 篇](28-firecracker-process-management.md) |
| `/fc-kernels/<kernel-version>/vmlinux.bin` | `HOST_KERNELS_DIR` | guest 内核镜像，文件名常量 `SandboxKernelFile` | [第 69 篇](69-guest-kernel-for-arm.md) |
| `/fc-envd/envd` | `HOST_ENVD_PATH` | 要注入沙箱的 envd 二进制 | [第 48 篇](48-envd-overview.md) |
| `/mnt/disks/fc-envs/v1/<template-id>/builds/<build-id>` | `envsDisk` 常量 | v1 版模板的 rootfs 目录，已废弃 | [第 29 篇 §7](29-template-artifact-format.md#7-两套版本字段) |
| `/var/run/netns/ns-<slot-idx>` | `netNamespacesDir` 常量 | 每个网络槽位一个 netns，配套 `veth-<idx>` 与槽内 `tap0` | [第 35 篇 §2](35-sandbox-networking.md#2-建立一个槽位createnetwork-的完整步骤) |
| `/dev/nbd<N>` | `nbd/pool.go` 拼出 | rootfs 的块设备；模块加载参数决定设备数 | [第 33 篇](33-nbd-and-rootfs.md) |
| `/tmp/fc-<sandbox-id>-<rand>.sock` | `SandboxFirecrackerSocketPath()` | Firecracker 的 API socket | [第 28 篇](28-firecracker-process-management.md) |
| `/tmp/uffd-<sandbox-id>-<rand>.sock` | `SandboxUffdSocketPath()` | userfaultfd handler 的 socket | [第 31 篇](31-uffd-memory-backend.md) |
| `/tmp/templates`、`/tmp/build-cache` | `LOCAL_TEMPLATE_STORAGE_BASE_PATH`、`LOCAL_BUILD_CACHE_STORAGE_BASE_PATH` | `Local` provider 的两个桶根目录 | [第 13 篇 §3.4](13-storage-landscape.md#34-provider-抽象三种访问形态) |
| `/opt/e2b-infra/` | RPM 安装前缀 | 脚本、`nomad/*.hcl` 模板、`.env`、helm chart | [第 80 篇](80-single-node-rpm.md) |
| `/opt/e2b-infra/bin/` | 同上 | 全部二进制、goose、两套 migrations、内核与 Firecracker 镜像 | [第 80 篇](80-single-node-rpm.md) |
| `/opt/e2b-infra/bin/fc-netns-exec` | `E2B_FC_NETNS_EXEC_HELPER` | 进 netns 拉起 Firecracker 的助手，单机离线版的部署包提供 | [第 80 篇](80-single-node-rpm.md) |
| `/usr/bin/orchestrator`、`/usr/bin/template-manager` | `start-client.sh` 复制 | 同一个二进制的两份拷贝，raw_exec 直接执行 | [第 80 篇](80-single-node-rpm.md) |
| `/etc/udev/rules.d/97-nbd-device.rules` | 开机脚本写入 | 对 `nbd*` 设置 `OPTIONS:="nowatch"`，关掉 inotify 监听 | [第 82 篇](82-host-kernel-nbd-hugepages.md) |

三点补充。

**三个 `/fc-*` 目录在 GCP 上是只读的 gcsfuse 挂载**（`start-client.sh` 分别挂
`FC_ENV_PIPELINE_BUCKET_NAME`、`FC_KERNELS_BUCKET_NAME`、`FC_VERSIONS_BUCKET_NAME`），
在单机离线版里是 `init-client.sh` 从 `/opt/e2b-infra/bin/` 复制出来的普通目录。
`/fc-vm` 两边都是空目录，真正的内容在每台沙箱自己的挂载命名空间里。

**NBD 设备数两边不同。** 上游的 `start-client.sh` 与 `init-client.sh` 都执行
`modprobe nbd nbds_max=4096`；单机离线版把这一段从脚本里去掉了，改为一次性加载定制的
`nbd` 模块并固定 `nbds_max=512`，理由与后果见[第 82 篇](82-host-kernel-nbd-hugepages.md)。

**路径里的随机段是防误删的。** `/orchestrator/template` 下的 `<uuid>` 与
`/orchestrator/build`、`/orchestrator/sandbox` 下文件名末尾的 20 字符随机串，
都是为了让「同一个 build 的旧缓存项正在关闭、新缓存项刚建好」这个场景里旧项不会删掉新项的文件。

---

## 3. 对象存储键

两个桶：产物桶由 `TEMPLATE_BUCKET_NAME` 指定，装模板与快照的产物；
层缓存桶由 `BUILD_CACHE_BUCKET_NAME` 指定，装构建层缓存。
键名分别由 `packages/shared/pkg/storage/template.go` 与
`packages/orchestrator/internal/template/build/storage/paths/paths.go` 拼出。

| 键 | 桶 | 内容 | 来源篇目 |
|---|---|---|---|
| `<build-id>/memfile` | 产物桶 | guest 内存，整代或 diff | [第 29 篇 §2](29-template-artifact-format.md#2-一代产物六个对象) |
| `<build-id>/memfile.header` | 产物桶 | 内存块到某一代 build ID 的映射表 | [第 29 篇 §3](29-template-artifact-format.md#3-header-的字节布局) |
| `<build-id>/rootfs.ext4` | 产物桶 | 根文件系统，整代或 diff | [第 29 篇 §2](29-template-artifact-format.md#2-一代产物六个对象) |
| `<build-id>/rootfs.ext4.header` | 产物桶 | rootfs 块的映射表 | [第 29 篇 §3](29-template-artifact-format.md#3-header-的字节布局) |
| `<build-id>/snapfile` | 产物桶 | Firecracker 的 VM 状态快照 | [第 37 篇](37-pause-and-snapshot.md) |
| `<build-id>/metadata.json` | 产物桶 | 模板元数据：产物版本、内核 / Firecracker / envd 版本 | [第 29 篇 §7](29-template-artifact-format.md#7-两套版本字段) |
| `<cache-scope>/index/<sha256-hex>` | 层缓存桶 | JSON，只存一个 build ID，是弱引用 | [第 45 篇 §3](45-layers-and-build-cache.md#3-查找两跳索引是弱引用) |
| `<cache-scope>/files/<sha256-hex>.tar` | 层缓存桶 | `COPY` 指令要拷进沙箱的文件包 | [第 45 篇 §5](45-layers-and-build-cache.md#5-两个桶一个-scope) |

产物桶的键里**没有模板 ID**，只有 build ID；「哪个模板的哪一代」这层关系在 Postgres 的
`envs` 与 `env_build_assignments` 里。删除一个 build 就是
`DeleteObjectsWithPrefix(ctx, "<build-id>")`，因此删除前必须确认没有后代的 header 还指着它。

`<cache-scope>` 由 api 传下来，`create_template.go` 与 `upload_template_layer_files.go`
都填 `teamID.String()`，orchestrator 侧以 `templateID` 兜底。层缓存因此在团队内跨模板复用，
但不跨团队复用。

单机离线版把两个桶都放在 MinIO 上（`STORAGE_PROVIDER=MinioBucket`，
`storage_minio.go` 是 ARM 适配版新增的 provider），桶名沿用上游的
`e2b-dev-fc-templates` 与 `e2b-dev-fc-cache`；键布局与上游完全一致，
详见[第 75 篇](75-minio-storage.md)。

---

## 4. Redis 键

分隔符是 `:`（`packages/shared/pkg/redis/keys.go` 的 `CreateKey()`）。
`{teamID}` 外面的花括号是 Redis Cluster 的 hash tag，由同一文件的 `SameSlot()` 加上，
作用是让一个团队的键落在同一个槽上，从而能对它们跑 Lua 脚本、`MGET` 与事务。

| 键 | 类型与生存期 | 内容 | 来源篇目 |
|---|---|---|---|
| `sandbox:storage:{teamID}:sandboxes:<sandboxID>` | String，无 TTL | 一条沙箱运行态记录的 JSON | [第 20 篇 §3.1](20-sandbox-state-storage.md#31-键布局) |
| `sandbox:storage:{teamID}:index` | Set | 该团队的 sandbox ID 集合 | [第 20 篇 §3.1](20-sandbox-state-storage.md#31-键布局) |
| `sandbox:storage:global:expiration` | ZSet | 成员 `teamID:sandboxID`，分值为 `EndTime` 毫秒 | [第 20 篇 §3.2](20-sandbox-state-storage.md#32-到期扫描) |
| `sandbox:storage:global:teams` | ZSet，空闲 1 小时剪枝 | 成员 teamID，分值为最近一次 `Add` 的 Unix 秒 | [第 20 篇 §3.2](20-sandbox-state-storage.md#32-到期扫描) |
| `sandbox:storage:{teamID}:transition::<sandboxID>` | String，70 s | 正在进行的状态迁移 ID | [第 20 篇 §3.3](20-sandbox-state-storage.md#33-状态迁移) |
| `sandbox:storage:{teamID}:transition::<sandboxID>:<transitionID>` | String，30 s | 空串表示成功，非空为失败原因 | [第 20 篇 §3.3](20-sandbox-state-storage.md#33-状态迁移) |
| `sandbox:storage:{teamID}:reservations:pending` | ZSet，90 s 后按陈旧清理 | 创建期占位的 sandbox ID | [第 20 篇 §4](20-sandbox-state-storage.md#4-reservations创建期的占位) |
| `sandbox:storage:{teamID}:reservations:<sandboxID>:result` | String，30 s | 创建结果的 JSON | [第 20 篇 §4](20-sandbox-state-storage.md#4-reservations创建期的占位) |
| `lock:<任意键>` | String，60 s | redislock 的持有者标记 | [第 20 篇 §3.3](20-sandbox-state-storage.md#33-状态迁移) |
| `sandbox:catalog:<sandboxID>` | String，TTL 为团队档位的 `max_length_hours` | 路由目录项：orchestrator 的 ID 与 IP、执行 ID、启动时刻 | [第 55 篇 §2](55-sandbox-catalog-and-routing.md#2-表里存了什么以及为什么存这些) |
| `sandbox.events.stream` | Stream | 沙箱事件，`XADD` 写入 | [第 61 篇 §4](61-events-and-webhooks.md#4-投递一个接口三个实现) |
| `wh:<team-id>` | 任意类型，只判断存在 | 存在即为该团队开启事件投递 | [第 61 篇 §5](61-events-and-webhooks.md#5-按需投递与校验) |
| `template:info:{<templateID>}:<tag>` | String，5 min | 模板加构建加集群的解析结果 | [第 22 篇 §3](22-template-api.md#3-名字怎么解析) |
| `template:alias:<namespace/alias>` 或 `template:alias:<templateID>` | String，5 min | 别名到 templateID 与 teamID，含否定墓碑 | [第 22 篇 §3](22-template-api.md#3-名字怎么解析) |
| `template:metadata:<templateID>` | String，5 min | 模板的 public 标志与 clusterID | [第 22 篇 §3](22-template-api.md#3-名字怎么解析) |
| `template:build:<buildID>` | String，5 min | 一次构建的状态与归属 | [第 22 篇 §4](22-template-api.md#4-一次构建请求的两段) |

四点说明。

**`transition` 键名里的双冒号不是笔误。** 常量 `transitionKeyPrefix` 的字面值就是 `"transition:"`，
`CreateKey()` 拼接时又加了一个分隔符。

**锁键是「`lock:` + 被锁的键名」**，由 `packages/shared/pkg/redis/lock.go` 的 `GetLockKey()` 生成，
所以沙箱记录锁与迁移键锁是两把不同的锁。

**`wh:<team-id>` 的写方不在 infra 仓库里。** 全仓库对 `events.DeliveryKey()` 的引用只有定义处
与 `EventsService.Publish()` 里的一次 `EXISTS`，没有任何地方写这个键。

**运行态后端由 `SANDBOX_STORAGE_BACKEND` 选择**，上游默认 `memory`。这个取值装配出来的不是纯内存后端，
而是把 memory 与 redis 包在一起的影子写外壳：读走 memory，写同时落 Redis。
单机离线版的 `.env` 把它设成 `redis`，也就是直接读 Redis。

---

## 5. Postgres 表

`packages/db/migrations/` 下的 goose 迁移累积出下面这些对象，最终态可以从
sqlc 生成的 `packages/db/queries/models.go` 一次读完。除 `auth.users` 外都在 `public` schema。

| 表或视图 | 主键 | 装什么 | 来源篇目 |
|---|---|---|---|
| `auth.users` | `id` | 只有 `id` 与 `email`，正常由外部身份系统写入 | [第 58 篇 §2.1](58-postgres-schema-and-migrations.md#21-身份租户与配额) |
| `users` | `id`，同时是 `auth.users` 的外键 | `auth.users` 的同 schema 副本，由触发器同步 | [第 58 篇 §2.1](58-postgres-schema-and-migrations.md#21-身份租户与配额) |
| `teams` | `id` | 租户；`tier` 指向 `tiers`，`cluster_id` 可空 | [第 16 篇](16-auth-and-multitenancy.md) |
| `users_teams` | 代理键 | 用户与团队的多对多成员关系 | [第 16 篇](16-auth-and-multitenancy.md) |
| `tiers` | 文本 ID | 档位基线：并发数、vCPU、内存、磁盘、最长时长 | [第 16 篇](16-auth-and-multitenancy.md) |
| `addons` | `id` | 带生效区间的配额增量，叠加在档位之上 | [第 58 篇 §2.1](58-postgres-schema-and-migrations.md#21-身份租户与配额) |
| `team_limits`（视图） | 无 | 档位基线与生效中 addon 求和后的六个配额数 | [第 58 篇 §2.1](58-postgres-schema-and-migrations.md#21-身份租户与配额) |
| `team_api_keys` | `id` | 团队 API key，前缀 `e2b_`，只存哈希 | [第 16 篇](16-auth-and-multitenancy.md) |
| `access_tokens` | `id` | 用户访问令牌，前缀 `sk_e2b_`，只存哈希 | [第 16 篇](16-auth-and-multitenancy.md) |
| `envs` | 20 字符文本 ID | 模板；`source` 区分 template / snapshot / snapshot_template | [第 58 篇 §2.2](58-postgres-schema-and-migrations.md#22-模板构建与快照) |
| `env_aliases` | `id`（UUID） | 模板别名，`alias` 与 `namespace` 上有唯一索引 | [第 58 篇 §2.2](58-postgres-schema-and-migrations.md#22-模板构建与快照) |
| `env_builds` | `id`（UUID） | 一次构建：状态、资源规格、各版本号 | [第 58 篇 §3](58-postgres-schema-and-migrations.md#3-构建状态status-与-status_group) |
| `env_build_assignments` | 代理键 | 模板与构建的多对多边，带 `tag` 与 `source` | [第 58 篇 §2.2](58-postgres-schema-and-migrations.md#22-模板构建与快照) |
| `snapshots` | `id` | 每行一个被暂停的 `sandbox_id`，`config` 是 JSONB | [第 37 篇](37-pause-and-snapshot.md) |
| `snapshot_templates` | `envs.id` | 某个快照被固化成模板时的来源沙箱 | [第 58 篇 §2.2](58-postgres-schema-and-migrations.md#22-模板构建与快照) |
| `clusters` | `id` | 远端集群的 endpoint、TLS 标志、token、沙箱代理域名 | [第 21 篇](21-clusters-and-discovery.md) |
| `volumes` | `id` | 持久卷，`UNIQUE (team_id, name)` | [第 40 篇](40-volumes-and-nfsproxy.md) |
| `_migrations` | goose 维护 | 迁移版本记录表，表名由 `migrator.go` 的 `trackingTable` 指定 | [第 58 篇 §5](58-postgres-schema-and-migrations.md#5-迁移goosemigrator-容器与在线安全) |

命名有历史包袱：**模板在数据库里叫 `envs`，构建叫 `env_builds`**。
`auth.users` 由第一条迁移 `20000101000000_auth.sql` 连同 `auth` schema 一起建出；
`packages/db/scripts/migrator.go` 在数据库版本低于这条迁移时还会先跑一次 `setupAuthSchema()` 兜底，
所以没有外部身份系统的部署也能起来。
`team_limits` 是视图不是表，sqlc 把它当只读表处理，认证路径上的查询全部 `JOIN` 它。

---

## 延伸阅读

- [第 10 篇 · 系统架构：组件、进程、端口与数据流 §4](10-system-architecture.md#4-端口表)：端口表的出处，以及每个进程为什么存在。
- [第 13 篇 · 存储全景 §1](13-storage-landscape.md#1-五类存储五种约束)：五类存储的约束、进程与存储的读写矩阵。
- [第 14 篇 · 配置、特性开关与版本约定 §1.1](14-config-flags-versions.md#11-环境变量谁定义谁注入)：环境变量是怎么被读进来的。
- [第 90 篇 · 环境变量与配置项总表 §2](90-config-reference.md#2-环境变量)：本篇不收的那些非端口、非路径的配置项。
- [第 89 篇 · 代码地图 §1](89-code-map.md#1-上游-202609-的目录)：从目录找到负责它的篇目。
- [第 88 篇 · 术语表](88-glossary.md)：表里出现的名词。
