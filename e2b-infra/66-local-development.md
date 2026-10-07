# 66 · 本地开发环境

> 上游把 e2b 部署在 GCP 上，靠 Nomad、Consul、GCS、Cloudflare 的通配符域名与 LaunchDarkly 把
> 各个部件粘在一起。这些东西在一台笔记本上一个都没有。本篇讲上游怎么给每一样准备一个替身，
> 哪些进程必须在宿主机上裸跑、哪些可以塞进容器，以及一次从零到跑通 base 模板要按什么顺序做。
>
> **读者**：要改这套代码的工程师。
> **预备**：[第 10 篇 · 系统架构](10-system-architecture.md)、[第 14 篇 · 配置、特性开关与版本约定](14-config-flags-versions.md)。
> **代码**：`DEV-LOCAL.md`、`DEV.md`、`Makefile`、`packages/local-dev/`、
> `packages/{api,orchestrator,client-proxy}/.env.local`、`packages/shared/scripts/`

---

## 0. 本篇要回答的问题

1. 本地一套 e2b 里，哪些进程必须在宿主机上裸跑、哪些可以放进容器？分界线是什么？
2. `modprobe nbd`、大页、KVM、root 这四个系统前置分别是给谁准备的，缺一个会看到什么错？
3. `ENVIRONMENT=local` 这一个变量改变了多少条代码路径？
4. 没有 GCS、没有 Consul、没有通配符域名，本地分别拿什么顶上去？
5. 一次完整的 bring-up 要做哪些步骤，为什么是这个顺序？
6. 怎么用本地的 api 去驱动一台远程 orchestrator？

---

## 1. 本地环境的分界线

生产形态里，一台 client 节点上跑的是 orchestrator，它要打开 `/dev/kvm`、创建 network namespace、
绑定 `/dev/nbd*`、从 HugeTLB 池里要内存、往 `/var/run/netns` 里写文件。这些能力要么依赖宿主内核的
具体状态，要么需要 root。api、client-proxy 则只是普通的网络服务。

这条差别决定了本地环境的切法：**有状态的外部依赖进容器，需要内核能力的进程在宿主机上裸跑**。
`DEV-LOCAL.md` 的开头因此写着「Linux is required for developing on bare metal」——
macOS 上跑不起来的不是 Go 代码，是 KVM 与 NBD。

具体分成三层：

- **容器层**：`packages/local-dev/docker-compose.yaml` 里的十一个服务，全是被依赖方
  （数据库、缓存、遥测后端），没有一个是 e2b 自己的代码。
- **宿主进程层**：api、orchestrator（同进程内还带着 template-manager）、client-proxy，
  各自 `make run-local`，各占一个终端。
- **沙箱层**：orchestrator 拉起的 Firecracker 进程，跑在宿主机上，用宿主的 KVM、netns、NBD 与大页。

```mermaid
flowchart TB
  SDK["SDK 或 tsx 脚本"] --> API["api :3000<br/>宿主进程"]
  SDK --> CP["client-proxy :3002<br/>宿主进程"]
  API --> PG["postgres :5432<br/>容器"]
  API --> CH["clickhouse :9000<br/>容器"]
  API --> REDIS["redis :6379 容器<br/>沙箱目录"]
  CP --> REDIS
  API -->|"gRPC :5008"| ORCH["宿主 root 进程<br/>orchestrator<br/>与 template-manager"]
  CP -->|"HTTP :5007"| ORCH
  API --> OTEL["otel-collector<br/>:4317 容器"]
  ORCH --> OTEL
  ORCH --> FC["Firecracker 进程<br/>KVM netns NBD 大页"]
  ORCH --> FS["本地模板存储<br/>orchestrator 下的 tmp"]
  OTEL --> GRAF["grafana :53000 容器"]
```

三个服务之间没有服务发现，全靠写死的 `localhost` 与固定端口。为什么可以写死，见 §5。

---

## 2. 四个系统前置

`DEV-LOCAL.md` 的「System prep」只有两条命令，但实际上有四个前提，每一个都对应一段会失败的代码。

**NBD 模块。** `sudo modprobe nbd nbds_max=64`。orchestrator 用 NBD 把 rootfs 暴露给 Firecracker
（[第 33 篇 §1](33-nbd-and-rootfs.md#1-设备池一种在进程之外的资源)）。设备池在启动时读
`/sys/module/nbd/parameters/nbds_max` 来决定池子大小，`internal/sandbox/nbd/pool.go` 的
`getMaxDevices()` 在这个文件不存在时直接返回 `ErrNBDModuleNotLoaded`，错误文本就是
`NBD module not loaded`。`nbds_max` 同时是**并发沙箱数的硬上限**：一个沙箱占一个 `/dev/nbdX`，
64 就是 64。`packages/orchestrator/README.md` 给开发工具建议的是 4096，并附一条 udev 规则
把 NBD 设备的 inotify 监听关掉；这条规则在 `DEV-LOCAL.md` 里没有，但在设备数量大时同样值得加。

**大页。** `sudo sysctl -w vm.nr_hugepages=2048`，也就是预留 4 GiB 的 2 MiB HugeTLB。
Firecracker 的 machine config 在 `internal/sandbox/fc/client.go` 里被设成
`models.MachineConfigurationHugePagesNr2M`，guest 内存是从 HugeTLB 池里拿的
（[第 32 篇 §5.2](32-memory-prefetch-and-hugepages.md#52-一个开关同时决定四个粒度)）。这个池子是**预留**的：
不够时 Firecracker 起不来，够了也不会还给普通页分配器。2048 页够同时跑几台 512 MiB 的沙箱，
再多要自己加。

**KVM。** 没有 `/dev/kvm` 就没有 Firecracker。云上的开发机要选支持嵌套虚拟化的实例类型，
这也是 `DEV.md` 里那套「连到 GCP 上的一台 client 实例去开发」的直接原因。

**root。** orchestrator 要建 netns、绑 NBD 设备、写 `/orchestrator` 这类绝对路径下的目录，
所以 `DEV-LOCAL.md` 给的是 `sudo make -C packages/orchestrator run-local`。注意它把编译与运行
拆成了两条：`make build-debug`（普通用户）与 `sudo make run-local`（root）。这样 Go 的构建缓存
不会被 root 写坏，代价是 `run-local` 这个目标本身不带编译依赖，改完代码忘了重新 `build-debug`
就会跑到旧二进制。

预取二进制是第五件事，但它不需要特权：`make download-public-kernels` 把内核放进
`packages/fc-kernels/`，`make download-public-firecrackers` 把 Firecracker 放进
`packages/fc-versions/builds/` 并 `chmod +x`。两个目录正好是 orchestrator `.env.local` 里
`HOST_KERNELS_DIR` 与 `FIRECRACKER_VERSIONS_DIR` 指向的位置。两条命令都走 `gsutil` 从
`gs://e2b-prod-public-builds` 拉，因此**本地开发仍然需要外网**。

---

## 3. 容器那一半：`make local-infra`

根 `Makefile` 的 `local-infra` 转给 `packages/local-dev`，后者先用 `envsubst` 把
`packages/clickhouse/local/config.tpl.xml` 渲染成 `clickhouse-config-generated.xml`，
再 `docker compose up --abort-on-container-failure`。加了 `--abort-on-container-failure`
意味着任何一个容器退出，整组都停——本地环境不做部分可用。

| 容器 | 端口 | 谁在用 |
|---|---|---|
| postgres 17.4 | 5432 | api 的主库与 auth 库 |
| clickhouse 25.4 | 8123 / 9000 | 沙箱指标与主机统计 |
| redis 7.4 | 6379 | 沙箱目录（api 写、client-proxy 读） |
| otel-collector | 4317 / 4318 | 三个服务的 trace、metric、log |
| loki / mimir / tempo | 3100 / 内部 / 3200 | collector 的三个后端 |
| vector | 30006 | 沙箱日志（`LOGS_COLLECTOR_ADDRESS`） |
| grafana 12 | 53000 | 看上面这些，免登录 |
| memcached | 11211 | tempo 的分片缓存 |

`otel-collector.yaml` 的四条 pipeline 说明了遥测的落点：traces 进 tempo，metrics 进 mimir，
logs 进 loki，另有一条 `metrics/clickhouse` 过滤后写 ClickHouse——生产里靠不同后端承担的分工，
本地一比一复刻（[第 60 篇 §4.1](60-telemetry.md#41-otel-collector每节点一个)）。grafana 的端口从 3000 改到 53000，
因为 3000 留给了 api。

代价是这一层不小：十一个容器、几个 GiB 的镜像，而且镜像来自公网。只想调 orchestrator 内部逻辑
时，[第 47 篇 · 本地开发工具](47-orchestrator-dev-tools.md) 的 `create-build` / `resume-build`
是更轻的路子——它们完全不需要这一层。

---

## 4. 预备：迁移、envd、种子数据

三条命令，顺序不能换。

`make -C packages/db migrate-local` 用 goose 对
`postgres://postgres:postgres@localhost:5432/postgres` 跑 `migrations/` 下的全部迁移。
它与生产用的 `migrate` 目标的唯一区别是连接串写死，不读 `.env.<env>`。
`make -C packages/clickhouse migrate-local` 同理，直接用 `go tool goose ... clickhouse up`，
而生产的 `migrate` 要先 build 一个 migrator 镜像再在 docker 网络里跑。

`make -C packages/envd build` 编出要嵌进模板的 envd。orchestrator 的 `.env.local` 把
`HOST_ENVD_PATH` 指向 `../envd/bin/envd`，模板构建时把这个二进制塞进 rootfs
（[第 43 篇 · rootfs 制作](43-rootfs-construction.md)）。上游这条目标写死
`CGO_ENABLED=0 GOOS=linux GOARCH=amd64`。

`make -C packages/local-dev seed-database` 跑 `seed-local-database.go`。它做四件事：
往 `auth.users` 插一个固定 UUID 的用户、插一个 tier 为 `base_v1` 的 team、把两者关联并置为
`is_default`、再写一个 access token 与一个 team API key。token 的明文是写死的
（`89215020937a4c989cde33d7bc647715` 与 `53ae1fed82754c17ad8077fbc8bcdd90`），
库里存的是 `keys.NewSHA256Hashing()` 的哈希与掩码（[第 16 篇 · 认证与多租户](16-auth-and-multitenancy.md)）。
所以 `DEV-LOCAL.md` 末尾那四行客户端配置不是示例，是**这段代码的输出**。

脚本里 `upsertLocalCluster` 被整段注释掉了。本地不需要在库里建集群记录，因为本地集群是代码里
硬编码的（下一节）。

---

## 5. `ENVIRONMENT=local` 打开了什么

`packages/shared/pkg/env/env.go` 里只有两个判断：`IsLocal()` 要求 `ENVIRONMENT` 等于 `local`，
`IsDevelopment()` 放宽到 `dev` 或 `local`。三个服务的 `.env.local` 都设了 `ENVIRONMENT=local`，
于是下面这些分支同时生效。这是本地环境能省掉 Nomad、Consul 与域名的全部原因。

| 位置 | 本地行为 | 生产行为 |
|---|---|---|
| `api/internal/clusters/discovery/local.go` `Query()` | 返回一个写死的节点：IP 取 `TESTS_ORCH_INSTANCE_HOST`（默认 `localhost`），端口取 `ORCHESTRATOR_PORT`（默认 5008） | 查 Nomad allocation |
| `api/internal/orchestrator/orchestrator.go` | `skipNomadSync = true` | 周期性与 Nomad 对账 |
| `api/internal/orchestrator/lifecycle.go` `addSandboxToRoutingTable()` | 非 Nomad 托管的节点也写进 Redis 沙箱目录 | 只写 Nomad 托管节点 |
| `orchestrator/main.go` `newStorage()` | 网络槽位状态存本地 `/var/run/netns`，不连 Consul | `StorageKV`，要 `CONSUL_TOKEN` |
| `orchestrator/main.go` 启动锁 | 跳过 `ORCHESTRATOR_LOCK_PATH` 的崩溃检测 | 锁文件已存在就拒绝启动 |
| `shared/pkg/proxy/host.go` `GetTargetFromRequest()` | 允许用 `E2b-Sandbox-Id` / `E2b-Sandbox-Port` 请求头指定目标 | 只认 `<port>-<sandboxID>.<domain>` 形式的 Host |
| api、orchestrator、template-manager 的退出流程 | 去掉 15 秒的 draining 等待 | 等负载均衡摘流 |
| `api/internal/analytics_collector/auth.go` | 不带分析服务的认证 | 带 |
| `shared/pkg/feature-flags/flags.go` | 一批开关的 fallback 值是 `IsDevelopment()`，即默认打开 | 默认关，由 LaunchDarkly 下发 |

其中最关键的是**代理的 header 路由**。生产里沙箱地址是 `3000-<sandboxID>.e2b.app`，靠通配符 DNS
落到 edge；本地没有域名，`parseHost()` 会因为找不到点而直接报 `ErrInvalidHost`。
`GetTargetFromRequest(true)` 让 client-proxy 与 orchestrator 的代理先看请求头，
SDK 把 `E2B_SANDBOX_URL` 指到 `http://localhost:3002` 时走的就是这条路
（[第 54 篇 · 共享代理库](54-shared-proxy-library.md)）。

特性开关那一行有副作用要留意：`use-nfs-for-snapshots`、`use-nfs-for-templates` 这类开关的
fallback 是 `IsDevelopment()`，本地默认为真，而 `SHARED_CHUNK_CACHE_PATH` 在 `.env.local` 里没设。
`internal/sandbox/template/cache.go` 的 `useNFSCache()` 对这种组合的处理是打一条
`NFSCache feature flag is enabled but cache path is not set` 的 warning 然后当作关闭。
日志里看到它是正常的，不是配置错误。另外没有 `LAUNCH_DARKLY_API_KEY` 时
`feature-flags/client.go` 的 `NewClient()` 会退回内置的 offline store，不会去连外网。

---

## 6. 三个服务的 `run-local`

三个 Makefile 用同一个套路：

```make
define setup_local_env
	$(eval include .env.local)
	$(eval export $(shell sed 's/=.*//' .env.local))
endef
```

`.env.local` 是**签进仓库**的文件（不是被忽略的本地覆盖），三个包各一份，`run-local` 把它整份
导出到环境里，再补一个 `NODE_ID=$(HOSTNAME)`。所以「本地配置」这件事是可读的：想知道某个服务
本地怎么配，看它的 `.env.local` 就够了。

**api**（`make -C packages/api run-local`）先 `build-debug` 再跑，监听 3000。
`.env.local` 里除了 postgres、clickhouse、redis、loki 的连接串，还有
`SANDBOX_ACCESS_TOKEN_HASH_SEED` 这类生产里属于 secret 的值，本地填的是占位字符串。
`cfg.Parse()` 对 `POSTGRES_CONNECTION_STRING` 与 `LOKI_URL` 标了 `required`，少一个就启动失败。
另有一个 `make dev` 目标用 `air` 做热重载，它调的是 `make run` 而不是 `run-local`，
读的是 `.env.<env>` 而非 `.env.local`——两套入口不要混。

**orchestrator**（`make -C packages/orchestrator build-debug && sudo make -C packages/orchestrator run-local`）
是唯一需要 root 的。它的 `.env.local` 值得逐组看：

| 变量 | 值 | 作用 |
|---|---|---|
| `ORCHESTRATOR_SERVICES` | `orchestrator,template-manager` | 一个进程同时提供两个 gRPC 服务（[第 46 篇](46-template-manager-service.md)） |
| `STORAGE_PROVIDER` | `Local` | 模板产物落盘而不是进 GCS |
| `LOCAL_TEMPLATE_STORAGE_BASE_PATH` | `./tmp/local-template-storage` | 落在哪 |
| `ARTIFACTS_REGISTRY_PROVIDER` | `Local` | 容器镜像从本机 Docker daemon 取 |
| `ORCHESTRATOR_BASE_PATH`、`SANDBOX_CACHE_DIR`、`SNAPSHOT_CACHE_DIR` | `./tmp/...` | 各级缓存目录 |
| `HOST_KERNELS_DIR`、`FIRECRACKER_VERSIONS_DIR`、`HOST_ENVD_PATH` | `../fc-kernels` 等 | 指向 §2 下载与 §4 编译的产物 |
| `PERSISTENT_VOLUME_MOUNTS` | `test-volume-type:./.data/test-volume` | 持久卷（[第 40 篇](40-volumes-and-nfsproxy.md)） |

这些相对路径由 `internal/cfg/model.go` 的 `makePathsAbsolute()` 在解析后转成绝对路径，
基准是**进程的工作目录**，也就是 `packages/orchestrator/`。因此本地所有沙箱状态都堆在
`packages/orchestrator/tmp/` 下面，清干净等于重置环境。没被 `.env.local` 覆盖的
`SANDBOX_DIR` 仍取默认值 `/fc-vm`，会在根目录下真的建出来——这是 root 运行的又一处代价。

`PERSISTENT_VOLUME_MOUNTS` 有个硬要求：`cfg.Parse()` 会对每个挂载点 `os.Stat()`，
目录不存在就返回 `failed to access persistent volume mount` 并直接退出。第一次跑之前要
`mkdir -p packages/orchestrator/.data/test-volume`。

**client-proxy**（`make -C packages/client-proxy run-local`）最简单，监听 3002。
它从 Redis 沙箱目录查出沙箱所在的 orchestrator IP，然后转发到该 IP 的 5007 端口
（`internal/proxy/proxy.go` 的 `orchestratorProxyPort` 常量）。本地这个 IP 是
`127.0.0.1`，于是「跨节点路由」在一台机器上退化成一次本地回环
（[第 53 篇 · client-proxy](53-client-proxy-edge.md)）。它的 `.env.local` 里没有
`API_GRPC_ADDRESS`，所以 `main.go` 里那个「访问已暂停沙箱时自动恢复」的 resumer 不会被装上。

值得指出的是，这三份 `.env.local` 里有若干**在上游 2026.09 的代码里已经没有读取方**的条目：
api 的 `LOCAL_CLUSTER_ENDPOINT`、`LOCAL_CLUSTER_TOKEN`、`DNS_PORT`、`PERSISTENT_VOLUME_MOUNTS`，
client-proxy 的 `EDGE_SECRET`、`EDGE_URL`、`SD_EDGE_PROVIDER`、`SD_ORCHESTRATOR_PROVIDER`、
`SKIP_ORCHESTRATOR_READINESS_CHECK`。全仓检索不到对应的 `env:` 标签或 `GetEnv` 调用。
按着它们去代码里找机制会白费工夫。

---

## 7. 造出第一个模板

服务起来之后还没有任何模板，创建沙箱会因为找不到模板而失败。
`make -C packages/shared/scripts local-build-base-template` 补上这一步：它 `npm install` 之后用
`tsx` 跑 `build.prod.ts`，内容只有一句 `Template.build(template, { alias: "base", memoryMB: 512, skipCache: true })`，
模板本身是 `template.ts` 里的 `Template().fromBaseImage()`。凭据来自同目录的 `.env.local`——
正是 §4 种子数据里那两个 token，`E2B_API_URL` 指向 `http://localhost:3000`。

这条命令是**从外部走完整条构建链路**的：SDK 调 api 的模板接口，api 通过 template-manager
客户端把构建派给 orchestrator 进程里的 template-manager，后者按阶段流水线做出 rootfs 与内存快照
（[第 41 篇 · 构建总览](41-template-build-overview.md)）。链路上有两个地方在本地换了实现：

- `ARTIFACTS_REGISTRY_PROVIDER=Local` 让 `shared/pkg/artifacts-registry/registry_local.go` 生效，
  它用 `daemon.Image()` 从**本机 Docker daemon** 按 `templateID:buildID` 取镜像。
- 拉公共基础镜像时，`DOCKERHUB_REMOTE_REPOSITORY_URL` 没设，
  `shared/pkg/dockerhub/repository.go` 返回 noop 实现，`remote.Image()` **直连 Docker Hub**。
  生产里这一跳走的是 GCP 的 remote repository 代理（[第 57 篇](57-docker-reverse-proxy.md)）。

`build/core/oci/oci.go` 的 `DefaultPlatform` 写死 `linux/amd64`，拉镜像时按这个平台选 manifest。

构建产物落在 `packages/orchestrator/tmp/local-template-storage/` 下，键的布局与对象存储上一致
（[第 29 篇 · 模板产物格式](29-template-artifact-format.md)），只是前缀从 bucket 换成了目录。
之后 `E2B_API_KEY` 那套配置就能创建沙箱了，模板 ID 用 `base`。

---

## 8. 调试

**本地断点。** 三个包的 `build-debug` 都是
`CGO_ENABLED=1 go build -race -gcflags=all="-N -l"`：关内联与优化让 delve 的行号与变量可用，
同时开竞态检测器。代价是慢——`-race` 会显著拉高延迟，测启动耗时不要用这个二进制。

**远程 orchestrator。** 这是上游给「本地代码 + 真实节点」准备的路子，两半合起来才成立。
一半是 `make connect-orchestrator`（根 `Makefile` 转给 `tests/integration`）：它用 `gcloud`
找到 client 实例组里的第一台机器，然后 `gcloud compute ssh ... -NL 5008:localhost:5008`
把远端 orchestrator 的 gRPC 端口打到本机 5008。另一半是 §5 那条本地服务发现——
本地 api 认定的 orchestrator 就是 `TESTS_ORCH_INSTANCE_HOST:5008`。隧道一建，
本地 api 与本地 client-proxy 驱动的就是远端那台 orchestrator 上的真实沙箱。
`packages/clickhouse/Makefile` 的 `connect-clickhouse` 是同一手法的另一个实例。

`DEV.md` 给的是另一个方向：把开发环境整个搬到远端。`gcloud compute config-ssh` 之后用 VS Code
的 Remote SSH 连到 orch-client 实例，在那台机器上编译、运行、挂 Go 调试器。它解决的是
本机没有 KVM 或没有 Linux 的情况，代价是编辑体验与网络绑定。

**看日志与指标。** 三个服务都往 `localhost:4317` 发 OTLP，沙箱日志走 `localhost:30006` 的 vector，
两条最后都进 loki，在 `http://localhost:53000` 的 grafana 里查。`E2B_DEBUG=true` 会让
`env.IsDebug()` 为真，日志器切到控制台友好的模式。api 还有 `make profiler metric=heap interval=90`，
它是 `go tool pprof -http :9991` 指向 `localhost:3000/debug/pprof/`。

**集成测试。** `tests/integration` 的 `.env.local` 用的正是同一组 token 与
`TESTS_SANDBOX_TEMPLATE_ID=base`，也就是说 §4 与 §7 做完之后，
`make test-integration` 可以直接打本地这套（[第 62 篇 · 测试体系](62-testing.md)）。

---

## 9. 常见错误

| 现象 | 原因 | 处置 |
|---|---|---|
| `NBD module not loaded` | 没 `modprobe nbd` | 见 §2；重启后要重做 |
| `failed to access persistent volume mount` | `.data/test-volume` 不存在 | 先 `mkdir -p` |
| Firecracker 起不来、guest 内存分配失败 | 大页不足或已被别的沙箱占满 | 加 `vm.nr_hugepages`，或清掉残留沙箱 |
| api 启动报 required 变量缺失 | 没走 `run-local`，`.env.local` 没被导出 | 用 `run-local`，不要直接跑 `./bin/api` |
| seed 报外键或关系错误 | 迁移没跑完就 seed | 先 `migrate-local`，两个库都要 |
| 模板构建时找不到内核或 Firecracker | 没跑 `download-public-*`，或版本号对不上目录名 | 按 `HOST_KERNELS_DIR` / `FIRECRACKER_VERSIONS_DIR` 核对目录 |
| 沙箱起来了但 envd 连不上 | 没 `make -C packages/envd build`，`HOST_ENVD_PATH` 指空 | 先编 envd 再建模板 |
| 改了代码但行为没变 | `run-local` 不含编译依赖 | 重新 `build-debug` |
| 通过 `localhost:3002` 访问沙箱返回 invalid host | 客户端没带 `E2b-Sandbox-Id` 头，也没有可解析的域名 | 用 SDK 与 `E2B_SANDBOX_URL`，见 §5 |
| 端口 3000 / 5432 / 6379 被占 | 本机已有同名服务 | 停掉冲突进程；这些端口在代码与配置里写死 |

还有一类不是错误的噪音：`NFSCache feature flag is enabled but cache path is not set`（§5）、
以及 orchestrator 退出时不等 15 秒就关闭连接导致的下游报错——本地是刻意跳过 draining 的。

---

## 10. 这套环境覆盖不到什么

本地环境是**功能等价**而不是**形态等价**，下面这些行为在这里试不出来：

- 多节点：只有一台 orchestrator，放置算法、节点排空、跨节点路由都退化
  （[第 19 篇](19-node-management-and-placement.md)、[第 55 篇](55-sandbox-catalog-and-routing.md)）。
- 真实对象存储：`Local` provider 是本地文件读写，分片拉取的延迟与失败模式完全不同
  （[第 13 篇 · 存储全景](13-storage-landscape.md)）。
- Nomad 与 Consul：job 的资源约束、健康检查、KV 里的网络槽位分配都被绕开
  （[第 64 篇 · Nomad job 详解](64-nomad-jobs.md)）。
- 特性开关的真实取值：本地是 offline store 的 fallback，与生产下发的值可能相反。
- 边缘：没有 edge、没有 TLS、没有通配符域名（[第 56 篇 · edge API](56-edge-api.md)）。

需要在这些维度上验证的改动，只能上真实环境（[第 63 篇 · GCP 上的部署](63-gcp-terraform.md)、
[第 65 篇 · 构建与发布](65-build-and-release.md)）。反过来，只想调 orchestrator 内部的
块层、uffd、恢复路径时，本篇这一整套都是多余的——用
[第 47 篇 §2](47-orchestrator-dev-tools.md#2-环境自举local-mode-做了什么) 讲的 local mode
更省事，它把同一批环境变量在进程内填好，不需要数据库、不需要 api。

---

## 11. ARM 适配版的差异

本地开发工作流的形状不变，改的是构建目标的架构。ARM 适配版把
`packages/orchestrator/Makefile` 的 `build-debug`、`packages/envd/Makefile` 的 `build`
里写死的 `GOARCH=amd64` 去掉或改成按 `uname -m` 推导（`x86_64` 对 `amd64`、`aarch64` 对 `arm64`），
`packages/api`、`packages/client-proxy` 的镜像构建也从固定 `--platform linux/amd64` 改为按机器架构。
没有这几处改动，`run-local` 在 aarch64 上编出来的是跑不了的 x86 二进制。
`build/core/oci/oci.go` 里那个写死的 `DefaultPlatform` 属于构建链路，见
[第 74 篇 · 模板构建的 ARM 改动](74-template-build-on-arm.md)；宿主的 nbd 与大页在
openEuler/aarch64 上的具体要求见 [第 82 篇 · 宿主内核要求与调优](82-host-kernel-nbd-hugepages.md)。
单机离线版有一套自己的源码线与出包线，见
[第 85 篇 · 开发与出包工作流](85-dev-workflow-and-packaging.md)。

---

## 12. 小结

- 本地环境的切分依据是**要不要内核能力**：需要 KVM、netns、NBD、大页的进程裸跑在宿主机上，
  其余的被依赖方进容器。因此这套环境只能在 Linux 上跑，且 orchestrator 必须 root。
- 四个系统前置各有对应的失败点：NBD 模块决定并发沙箱上限，大页是预留而非按需，
  KVM 决定能不能跑 Firecracker，root 决定能不能建 netns 与设备。
- `ENVIRONMENT=local` 一个变量替换掉了服务发现、网络槽位存储、启动锁、优雅退出与代理路由五件事，
  这是本地能省掉 Nomad、Consul 与通配符域名的根本原因。
- 生产依赖的替身是逐个换的：GCS 换成 `Local` 文件存储，Artifact Registry 换成本机 Docker daemon，
  Docker Hub 代理换成直连，Consul KV 换成 `/var/run/netns`，LaunchDarkly 换成 offline store。
- bring-up 顺序有依赖：系统前置与二进制下载 → 容器层 → 两个库的迁移 → envd → 种子数据 →
  三个服务 → base 模板。跳过任何一步的报错都出现在下一步。
- 三份 `.env.local` 是签进仓库的、可读的本地配置事实来源，但其中有一批条目在 2026.09 的代码里
  已无读取方，不能当作机制线索。
- 「本地 api + 远端 orchestrator」靠的是 SSH 端口转发加上本地服务发现的写死地址，
  这是排查只在真实节点上复现的问题的主要手段。
- 本地环境验证不了多节点、真实对象存储、Nomad 约束与真实特性开关取值；
  只调 orchestrator 内部逻辑时，[第 47 篇](47-orchestrator-dev-tools.md)的命令行工具比这一整套更省事。

---

## 延伸阅读 / 下一篇

- [第 47 篇 · 本地开发工具（cmd/）](47-orchestrator-dev-tools.md)：不需要 api 与数据库的另一条本地路径。
- [第 62 篇 · 测试体系](62-testing.md)：集成测试怎么复用这套环境。
- [第 63 篇 · GCP 上的部署](63-gcp-terraform.md)、[第 64 篇 · Nomad job 详解](64-nomad-jobs.md)：
  本地被替换掉的那些部件在生产里长什么样。
- [第 65 篇 · 构建与发布](65-build-and-release.md)：同一批 Makefile 目标在发布链路上的用法。
- [第 85 篇 · 开发与出包工作流](85-dev-workflow-and-packaging.md)：单机离线版的源码线与出包线。
- 上游文档 `DEV-LOCAL.md`、`DEV.md`、`packages/orchestrator/README.md`。
