# E 组笔记：分布式控制面 / 部署与工程 / Firecracker 补丁层 / 仓库全貌

> 源：AgentENV `v0.2.3`（tag 对象 4890d5e → commit 6cccaa7，2026-09-30）；Firecracker fork `kvcache-ai/firecracker`（`aenv-deps` = 90288c39）。
> 记号：`S/` = AgentENV 仓库根，`F/` = fc-aenv 仓库根。行数均为 `wc -l`（含注释与空行）。
> 标 **[推断]** 的为根据代码推理、未运行验证；标 **[未验证]** 的为无法从本地仓库确认。

---

## 0. 一页速览（给 Part 0 用）

- AgentENV = 一个 Rust workspace（单节点运行时 `server`、CLI `aenv`、存储栈 overlaybd/ublk、guest 内 envd 等）+ 一个独立 Go module `services/`（gateway + scheduler，可选的多节点控制面）。
- 单节点模式下 **不需要** Go 控制面：客户端直接打 `server`（默认 `127.0.0.1:8000`）。多节点时：客户端 → gateway(HTTP :8080) → scheduler(gRPC :9090) 决定节点 → gateway 反向代理到节点 `server:8000`。
- 节点 → scheduler 的唯一主动链路是 `src/observability/reporter.rs` 的 gRPC 心跳（默认 5s）+ 生命周期事件；P2P 发现走 `src/p2p/discovery/scheduler.rs`，同一个 proto。
- Firecracker 使用 kvcache-ai fork 的 `1.15.1-patch-v1`（= tag `aenv-deps`，上游 v1.15.1 + 7 个补丁）；PVM 模式改用另一个 fork `kvcache-ai/firecracker-next v1.17.0-next.1`。
- Guest kernel KVM 版 `vmlinux-6.1.175`，PVM 版 `6.12.33-pvm`。两仓库中均**没有** AgentENV 专属的 guest kernel config。
- 发布：git tag `vX.Y.Z` → `.github/workflows/release.yml` 校验 workspace 版本、构建 CLI(4 平台)/server bundle(x86_64 kvm+pvm、aarch64 kvm)/Docker 镜像、git-cliff 生成 release notes。仓库**无 CHANGELOG 文件**。

---

## 1. 仓库全貌（Part 0）

### 1.1 LOC 表（git ls-files，排除生成代码）

按语言（非生成）：

| 语言 | 行数 |
|---|---|
| Rust | 170,878 |
| Go | 13,364（含 `containerd-plain-snapshotter` 627 行；services 内约 12.7k，其中测试约 6.9k） |
| Markdown | 9,242 |
| YAML | 6,412（其中 `.github` 2,233，`src/api/openapi.yml` 等） |
| Shell | 5,477 |
| Python | 1,335 |
| TOML | 1,097 |
| Proto | 661 |
| Makefile | 471 |
| TypeScript | 416（e2b TS SDK 兼容测试） |
| Dockerfile | 347 |

生成代码（排除在外）：`src/api/generated` Rust 20,539；`services/api/proto/*.pb.go` 3,227；`thirdparty/firecracker-client` Rust 2,155 + yaml 1,940 + md 662；`src/custom_extension_api/generated` Rust 621。

按区域（Top，非生成）：

| 区域 | 行数 | 备注 |
|---|---|---|
| storage/overlaybd | 43,173 | Rust 重写的 overlaybd（最大单块） |
| src/sandbox | 20,535 | 其中 `src/sandbox/firecracker/` 9,449 |
| src/snapshot | 18,762 | |
| src/api | 14,320 | 手写 impl 11,354 + openapi.yml 2,966 |
| src/orchestrator | 12,381 | |
| src/image | 10,279 | |
| crates/aenv | 10,138 | CLI |
| docs/src | 7,240 | mdBook |
| storage/ublk-daemon | 6,743 | |
| services/gateway | 6,108 | 生产 2,555 / 测试 3,533 |
| services/scheduler | 5,419 | 生产 2,686 / 测试 2,713 |
| scripts/tests | 5,317 | e2e shell 套件 |
| src（根级 .rs） | 5,075 | lib.rs、cfg.rs 等 |
| storage/ublk | 4,131 | |
| src/setup | 3,407 | 依赖下载/主机准备 |
| src/template | 3,380 | |
| src/p2p | 3,320 | |
| tests/ | 3,118 | Rust 集成测试 |
| crates/benchmarks | 2,939 | |
| thirdparty/envd | 2,753 | |
| .github | 2,296 | 13 个 workflow + 3 个 composite action |
| src/overlaybd | 1,889 | |
| storage/util | 1,869 | |
| src/observability | 1,701 | 节点侧可观测/心跳 |
| services/shared | 1,250 | config/logging/buckets |
| adev | 1,197 | 开发者工具（codegen/coverage/mutants） |
| crates/e2e-tests | 813 | |
| storage/uffd-core | 808 | **不在 workspace，reference-only** |
| containerd-plain-snapshotter | 798 | v0.2.3 新增 Go 代码 |
| deploy/k8s | 723 | |
| crates/object-store-operator 680 / warm-pool 617 / linux-cap 231 / observability 101 / test-support 95 / shell-util 58 | | |

### 1.2 Cargo workspace（`S/Cargo.toml`）

- `[workspace.package] version = "0.2.3"`，成员 19 个：`.`、`adev`、`crates/{aenv,benchmarks,e2e-tests,linux-cap,observability,object-store-operator,test-support,shell-util,warm-pool}`、`src/api/generated`、`src/custom_extension_api/generated`、`thirdparty/{firecracker-client,envd}`、`storage/{util,overlaybd,ublk,ublk-daemon}`。
- `storage/uffd-core` 不是成员（CLAUDE.md 明说 "reference-only and excluded"）；`instance.rs::load_snapshot_uffd` 也带 `#[allow(dead_code)]` —— uffd 恢复路径目前是保留/实验物。
- 关键依赖：tokio、axum 0.8、tonic/prost 0.14、rocksdb 0.24、opendal(S3)、iroh 1.0.3 + iroh-blobs（P2P）、io-uring、libublk-rs-sys（git rev c6a3e06）、tikv-jemallocator。
- feature `vendored-openssl`（release 构建静态 OpenSSL）。dev profile 对 sha2/rocksdb 等强制 opt-level=3。
- `rust-toolchain.toml`：`channel = "stable"`（不锁具体版本）+ clippy/rustfmt。`.cargo/config.toml`：`cargo adev` 别名。
- `build.rs`：用 `tonic_prost_build` 把 `services/api/proto/scheduler.proto` 编译为 **仅客户端**；把 `src/image/content.proto`、`build_history.proto` 编译为服务端；注入 `AENV_GIT_COMMIT`（短 SHA，并跟踪 HEAD/packed-refs 变化）。

### 1.3 发布历史

| tag | 日期 | 与上一 tag 差异 |
|---|---|---|
| v0.1.0 | 2026-07-25 | 初次开源（8f028b1 "Initial open-source release"） |
| v0.1.1 | 2026-08-03 | 39 commits，117 files，+9,374/−1,961 |
| v0.1.2 | 2026-08-10 | 30 commits，+9,110/−5,618 |
| v0.1.3 | 2026-08-20 | 42 commits，+5,768/−1,461 |
| v0.2.0 | 2026-09-03 | 52 commits，192 files，+18,093/−2,961 |
| v0.2.1 | 2026-09-11 | 23 commits，+13,418/−2,541 |
| v0.2.2 | 2026-09-18 | 19 commits，+3,512/−2,482 |
| v0.2.3 | 2026-09-30 | 24 commits，143 files，+20,085/−799 |

全仓库 230 个 commit（squash 风格）。约每周一版。

`git log --oneline v0.2.2..v0.2.3` 归纳（24 条）：
- **快照启动加速（主线）**：`7eb9fc6` 记录 startup first-touch 并解耦上传 manifest；`f0ea548` resume 时并发预取 startup manifest；`cd0c13c` 记录并解析 POSIX startup manifest；`599edb4` 通过共享内存设备预取 POSIX startup；`875faee` 测试与文档；`7e56ce8` 录制期间保留 template workspace。
- **E2B 兼容**：`187f654` 支持 E2B v2 sandbox create/connect；`7f19ffd` E2B 兼容的 build status/logs（gateway 也改了路由）；`13cbf10` sandbox metrics 采集 API（gateway 新增 `sandbox_metrics.go` 聚合）。
- **CLI**：`6aa185b` 原生 Codex sandbox 会话 + `8a6594f` 文档；`531a002` 模板/快照名动态补全；`d660f5f` build help 示例；`725810d` 修复 HTTPS 下 rustls crypto provider。
- **存储/性能**：`8cd6793` overlaybd 远程 I/O 独立 runtime；`04f8786` seal 时只查 upper index；`8ff079c` P2P 发布已提交的 OSS layer。
- **新组件**：`5353143` containerd plain snapshotter（Go，`containerd-plain-snapshotter/`）。
- 其他：`59b36a4` free-page reporting order + 调优指南；`2f48c9c` 默认 readiness 用内置 busybox；`1f0c8a2` MinIO 测试镜像换 pgsty/silo；两个 Go 依赖 bump；`6cccaa7` 版本号 bump。

依赖版本稳定性：`config/deps_manifest.toml` 中 firecracker `1.15.1-patch-v1` 与 kernel `vmlinux-6.1.175` 从 v0.1.0 到 v0.2.3 **从未变化**；manifest 只有 5 次修改（初始、PVM 支持 12825e4、ARM64 8b29280、静态二进制+bundle overlaybd 19c8bd3、tools 0.1.1 f58d55e）。

### 1.4 约定文件

- `AGENTS.md` 与 `CLAUDE.md` 内容完全一致（各 242 行，首行注明 "AGENTS.md links to this file"）。结构：行为准则（Think/Simplicity/Surgical/Goal-driven，明显面向 LLM 编码代理）→ Core Concepts（snapshot/template、volume、OverlayBD/ublk、OSS）→ Build and Validate → Conventions → **Code Map 表** → Constraints to Preserve（lifecycle/storage/capture/volumes/registries/P2P/scheduler/extensions）→ Generated Code 表 → 文档链接。书中 Part 0 的"仓库地图"可直接引用其 Code Map 表。
- 关键约定：Conventional Commits（feat/fix/refactor/ci/chore）；PR 从 fork 提；非 root 跑测试，特权测试经 `scripts/run-with-capabilities.sh` 委托 `CAP_NET_ADMIN/CAP_SYS_ADMIN`；隔离的 `AENV_TEST_STATE_DIR`/`AENV_TEST_DEPS_PATH`。
- Scheduler 约束（CLAUDE.md 原文要点）："Assignments/heartbeats own bindings; lifecycle events are best-effort and do not establish bindings… Redis query-only replicas serve existing-sandbox lookups; scheduling still requires the primary."
- 生成代码再生成命令表：`make agentenv-server`、`make custom-extension-client`、`make firecracker-client`（→ `cargo adev codegen firecracker`，openapi-generator，见 `adev/src/codegen.rs::run_firecracker`）、`make envd-http-client`、`make -C services proto`。
- `CONTRIBUTING.md`（116 行）：issue 分类、大改动（API/生命周期/快照格式/控制面/主机设置）需先达成设计共识。
- `.opencodereview/rule.json`：代码评审排除 generated 与 firecracker-client。
- 文档链接腐化：CLAUDE.md "Details by Topic" 指向的 `docs/src/concepts/snapshots.md`、`volumes.md`、`custom-extension.md` **均不存在**（实际是 `concepts/snapshots/index.md` 等目录形式）。

---

## 2. Part 8 分布式控制面

### 2.0 模块地图（`S/services/`，Go 1.25 构建镜像，README 写 Go 1.21+）

| 文件 | 行数 | 职责 |
|---|---|---|
| `api/proto/scheduler.proto` | 271 | 唯一契约：13 个 RPC |
| `gateway/cmd/main.go` | 198 | 读配置、建 2 个 gRPC client（primary / query-only）、HTTP :8080 + metrics :9102、优雅关停 10s |
| `gateway/internal/server.go` | 1,005 | 路由判定、认证、反向代理、RecordAssignment |
| `gateway/internal/host_route.go` | 143 | `{port}-{sandboxID}.{domain}` 解析 |
| `gateway/internal/schedule_hint.go` | 154 | 从请求体抽取调度 hint（≤64KiB） |
| `gateway/internal/cluster_list.go` | 429 | `GET /sandboxes`、`/v2/sandboxes` 全节点扇出合并+分页 |
| `gateway/internal/node_list.go` | 205 | `GET /nodes`、`/nodes/{id}` |
| `gateway/internal/sandbox_metrics.go` | 183 | 多 sandbox metrics 按节点分组扇出（v0.2.3 新增） |
| `gateway/internal/metrics.go` | 238 | Prometheus：http/upstream/scheduler RPC 直方图 |
| `scheduler/cmd/main.go` | 263 | 选 store、选 discovery、注册 gRPC + health；`--query-only` |
| `scheduler/internal/service.go` | 377 | 13 个 RPC 实现 + QueryOnlyService |
| `scheduler/internal/node_registry.go` | 448 | `AtomicNodeRegistry`：发现节点 + 心跳观测 + 状态推导 + CPU 交集 |
| `scheduler/internal/store.go` | 315 | `InMemoryBindingStore` + `InMemoryArtifactStore`(LRU) |
| `scheduler/internal/redis_store.go` | 313 | `RedisBindingStore`（Lua 脚本原子更新） |
| `scheduler/internal/kubernetes_discovery.go` | 348 | EndpointSlice + Pod informer |
| `scheduler/internal/cpu_template.go` | 301 | Firecracker CPU config JSON 按位与求交集 |
| `scheduler/internal/strategy.go` | 60 | round_robin / random |
| `scheduler/internal/filter.go` | 88 | `FilterByResourceLimit` |
| `scheduler/internal/metrics.go` | 141 | |
| `scheduler/internal/types.go` | 32 | `Node`、`RichNode` |
| `shared/config/config.go` | 489 | JSON 配置 + 环境变量覆盖 |
| `shared/logging/logging.go` | 47 | zap，auto/console/json |
| `shared/observability/buckets.go` | 57 | 与 Rust `crates/observability` 共享直方图桶（注释要求同步） |

环境变量覆盖：`SCHEDULER_{GRPC_LISTEN_ADDR,METRICS_LISTEN_ADDR,STRATEGY,BINDING_TTL,REDIS_ADDR,ARTIFACT_STORE_CAPACITY,ARTIFACT_LOOKUP_NODE_LIMIT}`、`GATEWAY_{HTTP_LISTEN_ADDR,METRICS_LISTEN_ADDR,SCHEDULER_ADDR,QUERY_ONLY_SCHEDULER_ADDR,REQUEST_TIMEOUT,SANDBOX_PROXY_DOMAINS,DEBUG_MODE}`。注意 `report_ttl` 没有环境变量覆盖。

gRPC 方法（proto 名 → Go 生成名）：Schedule、ListNodes、LookupNode、RecordAssignment、Heartbeat、ReportSandboxEvent、ListObservedNodes、ListP2pPeers(`ListP2PPeers`)、RecordP2pArtifact、ForgetP2pArtifact、LookupP2pArtifact、GetNode、UnregisterNode。（README "gRPC API" 列表漏了 4 个 P2P 方法。）

### 2.1 章：Gateway

**入口** `server.go::Handler()`：故意不用 `http.ServeMux`（避免 `%2F` 被规范化/301），手写分派；外包 `authenticate` 与 `instrumentGatewayHTTP`。

**认证** `authenticate()`：
- 数据面请求（`isSandboxDataPlaneRequest`：显式 `/proxy`、host 路由命中、或带完整 sandbox-id + target-port 头且非控制面路径）以及 `/health`、`/metrics` **不鉴权**，直接放行——理由：只有节点知道 sandbox 的 ingress 策略（public/private traffic token `e2b-traffic-access-token`、secure envd `X-Access-Token`）。
- 其余请求要求 `X-API-Key` 与 gateway 的 key 恒定时间比较（`singleHeaderMatches` + `crypto/subtle`）。gateway 不生成 key，读 `AENV_API_KEY` 或 `/run/secrets/api-key`；所有节点须同 key。

**路由判定** `handleProxy()`，按优先级得到 `routeSource`：
1. `host`：`parseHostRoute(r.Host, domains)` 解析 `{port}-{sandboxID}.{domain}`（sandboxID 须 RFC1123 小写 label，整体 ≤63 字符）；与头冲突时以 host 为准并 debug 日志。
2. 网关本地聚合（仅当无 host 路由且无路由头）：`/sandboxes/metrics` 类（`isSandboxMetricsListRequest`）、`GET /sandboxes|/v2/sandboxes`（cluster list）、`GET /nodes`、`/nodes/{id}`。
3. `path`：`isSandboxControlPlaneRequest`——`GET/DELETE /sandboxes/{id}`、`GET .../metrics`、`POST .../{pause,resume,fork,connect,timeout,refreshes,snapshots}`、`PUT .../network`、`GET/PATCH .../custom-extension-params`、`POST /v2/sandboxes/{id}/connect`。从路径取 sandboxID。
4. 模板构建：`POST /v2/templates/{t}/builds/{b}` 或 `PUT /templates/{t}/builds/{b}/builder` → `schedule`（新分配）；`/templates/{t}/builds/{b}/{status,logs}` → 按 buildID 当作"sandbox"查绑定，GET 且 NotFound 时回落到调度（已完成/旧 build 在共享模板仓库）。
5. `header`：`x-agentenv-sandbox-id` / `e2b-sandbox-id`（端口头 `x-agentenv-target-port` / `e2b-sandbox-port`）。
6. 都没有 → `schedule`。

**选节点**：有 sandboxID → `queryOnlyScheduler.LookupNode`（未配置 query-only 时即 primary）；否则 `buildScheduleHint(r)` → `scheduler.Schedule`。gRPC 错误映射 `writeSchedulerError`：InvalidArgument→400、NotFound→404、Unavailable→503。

**转发**：`upstreamTargetPath`——数据面（header/host）请求在上游路径前加 `/proxy`，host 路由还注入 `x-agentenv-sandbox-id`/`x-agentenv-target-port` 头；控制面原样。`httputil.ReverseProxy`，流式（grpc/connect+/SSE 等，`isStreamingRequest`）与 WebSocket 用 `FlushInterval=-1` 且不受 `request_timeout`(默认 90s) 限制。`debug_mode` 时回写 `x-agentenv-node-id`。

**写绑定** `shouldRecordAssignment` + `ModifyResponse` → `recordAssignmentFromResponse`：
- 仅 2xx；对 `POST /sandboxes|/v2/sandboxes|/sandboxes-cold`（新建）、`POST /sandboxes/{id}/fork`（按源路由，但为子 sandbox 建绑定）、模板 builder 分配。
- sandboxID 来源顺序：响应头 sandbox-id → 读响应体（上限 `forward_response_size` 默认 4MiB，超限返回 502 "upstream response too large"）解析 JSON（fork 用 `extractForkSandboxIDsFromResponse`）。
- 超时 `min(request_timeout, 5s)`。**普通 sandbox 的 RecordAssignment 失败只记 warn，不影响客户端 201**；模板 build 失败则返回 503。依赖下一次心跳自愈（见 2.3）。

**集群列表** `cluster_list.go::handleClusterList`：`ListNodes`（含 lingering）→ 每节点并发 GET → 任一失败即整体失败（"strict all-or-nothing"，4xx 透传、其余 502）→ 按 startedAt 排序、按 sandboxID 去重 → v2 在网关内分页（`nextToken` 编码时间+ID，`x-next-token`、`x-total-running` 头）。`listedSandbox` 保留原始 JSON（86956a6 引入，保证新增字段透传）。

**指标**：`agentenv_gateway_http_request_duration_seconds{method,route,route_source,status}`、`..._upstream_proxy_duration_seconds`、`..._scheduler_rpc_duration_seconds{rpc,status}`。

### 2.2 章：Scheduler（放置算法 + 绑定存储）

**进程装配** `scheduler/cmd/main.go::main`：
- `createBindingStore`：`redis_addr` 非空 → `NewRedisBindingStore`（启动即 Ping），否则 `NewInMemoryBindingStore(binding_ttl)`。
- `--query-only`：只注册 `QueryOnlyService`（仅 LookupNode，其余返回 Unimplemented），要求 Redis。
- 正常模式：`NewAtomicNodeRegistry(nil, report_ttl)`；discovery `kubernetes` → `runKubernetesDiscoveryWithRetry`（指数退避），否则 static `registry.Set(cfg.nodes, nil)`；`NewService(... WithArtifactStore, WithNodeResourceLimit)`；`RunObservedNodesMetrics` 每 15s 刷新节点状态指标。
- 附 gRPC health server（compose 用 `grpc_health_probe`）；SIGTERM → NOT_SERVING → GracefulStop 10s → 强停。

**放置算法** `service.go::Schedule`：
1. `nodes.Snapshot(allowLingering=false)`：发现列表去掉 lingering，按 ID 排序。
2. 每个节点配上 `PeekObserved(id)`（最近一次心跳的原始 NodeSnapshot，可能为 nil）→ `[]RichNode`。
3. `FilterByResourceLimit`（`filter.go`）：无快照的节点**保留**；有快照则检查 `max_sandbox_count`、`max_sandbox_starting_count`、`max_cpu_used_percent`、`max_cpu_allocated_percent`(allocated_cpu*100/cpu_count，可>100 表示超卖)、`max_memory_used_percent`、`max_memory_allocated_percent`，以及三项 "including paused"（`max_sandbox_count_including_paused`、`max_allocated_cpu_including_paused`、`max_allocated_memory_bytes_including_paused`，README 未列出后三项）。
4. `strategy.Select(eligible, hint)`：`RoundRobinStrategy`（原子计数器 mod len）或 `RandomStrategy`；hint（`NewColdSandboxHint{cpu,mem,images,metadata}` / `NewSandboxHint{metadata}`）**当前两种策略都忽略**，只用于日志 `summarizeScheduleHint`。接口 `Strategy` 预留了负载感知扩展点。
5. 空 → `codes.Unavailable "no nodes available"`。

**绑定存储**（sandboxID → Node{id,endpoint}，带 TTL，默认 30s）：
- 接口 `BindingStore{Get, Record, ReconcileNode}`（`store.go`）。
- InMemory：`bindings` + 反向索引 `nodeBinding[node][sandbox]`；`Get` 时惰性过期删除。
- `ReconcileNode(node, ids)`：心跳携带的完整 sandbox 名单 → 名单内全部 upsert 并续期 TTL；该节点名下不在名单内的全部删除；空名单 → 删光该节点绑定。
- Redis：key `agentenv:scheduler:bindings:sandbox:{id}`（JSON，`PX ttl`）+ `...:node:{node}`（SET，TTL 1h）；`redisRecordBindingScript` / `redisReconcileNodeScript` 两个 Lua 脚本保证原子迁移（旧节点 SREM）。单次操作超时 2s。
- `RecordAssignment` 校验节点在发现列表中且 endpoint 一致（`Contains`），否则 InvalidArgument。

**节点注册表** `node_registry.go::AtomicNodeRegistry`：
- 两层数据：`nodesByID`/`lingeringIDs`（来自发现：static 配置或 k8s）与 `observed`（来自心跳）。`Set()` 替换发现列表时，删除不再存在节点的观测记录并使 CPU 交集失效。
- 心跳只接受发现列表里的节点（否则 `ErrNodeNotInRegistry` → InvalidArgument；节点侧把它识别为 `HeartbeatNodeNotConfigured` 并打印 "ensure AENV_NODE_ID matches..."）。
- 状态推导 `deriveObservedNodeViewLocked`（proto 注释里有完整表）：超 `report_ttl` → UNHEALTHY；不在发现中 → CONNECTING；lingering → LINGERING；否则用节点自报（节点总是报 READY）。

**CPU 模板交集**（易被忽视的跨节点机制）：
- 节点启动时若存在 `deps/firecracker/<ver>/cpu-template-helper`，`ObservabilityService::new` 调 `machine::dump_cpu_config` 得到本机 CPU config JSON，放进首个心跳 `MachineInfo.cpu_config_json`。
- scheduler 在同一 `cluster_id` 内所有观测节点都报了 config 后，`IntersectCpuConfigs`（`cpu_template.go`，CPUID/MSR bitmap 按位与、kvm_capabilities 取交）算交集，**每节点只下发一次**（`intersectionSent`），经 `HeartbeatResponse.cpu_config_json` 返回。
- 节点存入 `cluster_cpu_arc`（`src/bin/server.rs`），被 `FirecrackerSandboxFactory::with_cpu_config` 与 `TemplateBuilder::with_cpu_config` 使用（PUT `/cpu-config`），目的是让快照可以在异构 CPU 节点间恢复。相关 fix：`0475f40` sanitize singleton intersection、`d9a63e3` 过滤 KVM 管理的 CPUID leaf 0x1f。

**P2P 索引**（仅 hint，详见 P2P 章）：`InMemoryArtifactStore`，key=(cluster,backend,key)→node 集合，LRU 容量默认 1,000,000，`artifact_lookup_node_limit` 限制返回数；`LookupP2pArtifact` 再经 `FilterP2pPeers` 只保留 READY 且上报了 p2p endpoint 的节点。`ListP2pPeers` 同理。**不在 Redis，primary 重启即丢**。

**HA 模型**：primary（读写，含发现/心跳/调度）+ N 个 query-only（只读 Redis，仅 LookupNode）。gateway 用 `query_only_scheduler_addr` 做数据面查找。primary 宕机时：已有 sandbox 的请求可继续路由；新建、RecordAssignment、列表、节点详情、P2P 全部失败。k8s base 中 scheduler 为 `replicas: 1`，未提供 query-only 部署清单。

### 2.3 章：心跳与节点可观测（Rust 节点侧）

模块地图 `S/src/observability/`（1,701 行）：

| 文件 | 行数 | 内容 |
|---|---|---|
| `mod.rs` | 23 | 导出 |
| `model.rs` | 51 | `NodeSnapshot`、`MachineInfo`、`NodeMetricsSnapshot` |
| `machine.rs` | 71 | `detect_machine_info`（/proc/cpuinfo）、`dump_cpu_config`（调用 cpu-template-helper） |
| `host.rs` | 519 | `HostMetricsCollector`：CPU%、内存、磁盘 |
| `service.rs` | 112 | `ObservabilityService::node_snapshot()`：合并 orchestrator 运行时计数 + 主机指标 + sandbox ID 列表 |
| `reporter.rs` | 587 | `ObservabilityReporter`：心跳循环、事件循环、UnregisterNode |
| `prometheus.rs` | 338 | 节点 HTTP/阶段直方图：`agentenv_http_request_duration_seconds`、`agentenv_sandbox_stage_duration_seconds`、`agentenv_sandbox_stage_inflight` 等 |

`crates/observability/src/lib.rs`（91 行）：`init_prometheus_recorder()`（metrics-exporter-prometheus，统一 `DURATION_BUCKETS`，注释 "Keep in sync with services/shared/observability/buckets.go"）、`metrics_handler`、`serve_metrics`；被 server 与 ublk-daemon 共用。

**心跳流程** `reporter.rs::start()` 中 `heartbeat_join` 任务：
1. 首次等待 100ms，之后 `interval`（`[observability.scheduler_report] interval_secs` 默认 5，最小 1）。
2. `send_heartbeat`：`service.node_snapshot()` → `build_heartbeat_request`（status 固定 READY；sandbox_ids = `Orchestrator::list_sandbox_ids()`，即 store 中全部 sandbox（含 paused）+ 进行中的 template build ID；附 p2p_endpoint）→ tonic，单次超时 10s。
3. 成功：重置 backoff；**清空 `pending_cpu_config_json`（只发一次）**；若响应带 cpu_config_json 则 `store_cluster_cpu_config`。
4. 失败：指数退避 interval→×2→上限 60s。
- `event_join` 任务：订阅 orchestrator `SandboxLifecycleEvent` 广播，批量 `ReportSandboxEvent`（CREATE/DELETE/PAUSE/RESUME/FORK）。**scheduler 端 `ReportSandboxEvent` 只打 debug 日志后丢弃**（"scheduler ignored sandbox event batch"）。
- `shutdown()`：若曾成功心跳，调用 `UnregisterNode(node_id, service_instance_id)`，重试（200ms×attempt）；scheduler 端校验 service_instance_id 一致（不一致 → FailedPrecondition，防止新实例被旧实例注销），删除观测记录、`ReconcileNode(node, nil)` 清空该节点全部绑定、`ForgetNode` 清 P2P 索引。
- `src/bin/server.rs` 关停顺序：drain startup manifest 任务(15s) → **先 reporter.shutdown（注销）** → orchestrator.shutdown（运行中 sandbox 持久化为 Paused）→ FC pool → ublk daemon → overlaybd p2p → p2p transport。

配置（`config/default.toml`）：`[cluster] scheduler_endpoint`（共享给心跳与 P2P 发现）；`[observability] enabled = true`；`[observability.scheduler_report] enabled = false, interval_secs = 5`；`[node_identity] node_id = "node-a", cluster_id = 全零 UUID, service_instance_id = "service-instance-a"`。环境变量 `AENV_NODE_ID`、`AENV_OBSERVABILITY_SCHEDULER_REPORT_ENABLED`、`AENV_OBSERVABILITY_SCHEDULER_ENDPOINT`。

**一致性模型（书中值得画时序图）**：绑定的真相源 = 节点心跳名单；RecordAssignment 只是"提前写入"，让新建后到下一次心跳之间也能路由。TTL(30s) = 6 个心跳周期的容忍度。节点失联 30s 后其绑定自然过期 → LookupNode NotFound → 404。

### 2.4 章：P2P（另一组负责，此处只列控制面接口）

- 节点侧调用全部在 `src/p2p/discovery/scheduler.rs`：`list_p2p_peers`(L201)、`lookup_p2p_artifact`(L104)、`record_p2p_artifact`(L124)、`forget_p2p_artifact`(L143)；刷新间隔 `peer_discovery_refresh_interval_secs = 5`。
- p2p endpoint 通过 `HeartbeatRequest.p2p_endpoint{backend,address}` 上报，存于 `observedNodeRecord.p2pEndpoint`。

### 2.5 章：services API（proto 契约与节点 HTTP API 的关系）

- 节点 HTTP API 由 `src/api/openapi.yml`（E2B 兼容）定义，gateway 不解析 schema，只识别若干路径模式（2.1 的列表）。新增节点 API 时若需要按 sandbox 路由，必须同步修改 `isSandboxControlPlaneRequest`——这是一个隐式耦合点（`7f19ffd`、`13cbf10`、`187f654` 都同时改了 Rust API 与 gateway）。
- proto 同时被 Go（`make -C services proto` 生成 `.pb.go`，入库）和 Rust（`build.rs` 构建期生成，不入库）消费。
- `ScheduleRequest` 字段 1 已 `reserved`（原 `string hint`），改为结构化 `ScheduleRequestHint` oneof。

### 2.6 端到端流程（建议插图）

**创建**：Client `POST /sandboxes` (X-API-Key) → gateway `authenticate` → `handleProxy` 无 sandboxID → `buildScheduleHint`（读≤64KiB body 并还原）→ `Schedule` → 选 node → ReverseProxy 到 `http://node:8000/sandboxes` → 2xx → `recordAssignmentFromResponse` 解析 `sandboxID` → `RecordAssignment` → 返回客户端。
**数据面**：Client → `49983-<sbx>.sandbox.example.com/...` → `parseHostRoute` → `LookupNode`（query-only）→ 转发到 `node/proxy/...` + 注入头 → 节点 proxy 校验 traffic token / envd token。
**心跳**：node 每 5s `Heartbeat` → registry 更新观测 + `ReconcileNode` 刷新绑定 TTL / 删除消失的 sandbox → 可能回带 CPU 交集。
**节点下线（k8s）**：Pod Terminating → EndpointSlice `terminating=true` → registry lingering（不再被 Schedule 选中，但 ListNodes 仍含，列表聚合仍访问）→ preStop 轮询 `GET /sandboxes` 直到 0（`terminationGracePeriodSeconds: 3600`）→ 进程退出时 UnregisterNode。

### 2.7 失败处理一览

| 场景 | 行为 | 代码 |
|---|---|---|
| 无可用节点 / 全被资源过滤 | 503 | `Schedule` → Unavailable |
| sandbox 绑定不存在/过期 | 404 | `lookupNode` NotFound |
| Redis 不可用 | 503 "binding store unavailable" | `lookupNode`/`RecordAssignment`/`Heartbeat` |
| 上游节点连接失败 | 502 "upstream unavailable"；超时 504 | `proxyRequest.ErrorHandler` |
| 集群列表任一节点失败 | 整体 502 | `fetchClusterList` |
| RecordAssignment 失败（普通 sandbox） | 仅 warn，等心跳自愈 | `recordAssignmentFromResponse` |
| 节点不在 scheduler 配置中 | 心跳 InvalidArgument，节点 error 日志 + 退避 | `Heartbeat` / reporter |
| scheduler 宕机 | 节点心跳退避至 60s；query-only 继续服务 Lookup | |
| 创建请求转发后节点 5xx | 直接透传，**不重试其他节点** | gateway 无重试逻辑 |

---

## 3. Part 9 部署与工程

### 3.1 章：主机准备

- `scripts/docker-setup.sh`（80 行，需 root）：写 `/etc/modprobe.d/aenv-ublk.conf`（`ublks_max=4096`）、加载 `ublk_drv`（缺失则 apt 装 `linux-modules-extra-$(uname -r)`）、持久化 modules-load；写 `/etc/sysctl.d/99-aenv.conf`（neigh gc_thresh 4096/8192/16384、`nf_conntrack_max=1048576`、`pid_max=4194304`、`inotify.max_user_instances=8192`）。
- `server --setup-only`（`src/setup/`，3,407 行）：`deps.rs::ensure` → `ensure_firecracker`、`ensure_kernel`、`ensure_regctl`、overlaybd release tools、`ensure_tools`（tools drive OCI 镜像 `ghcr.io/kvcache-ai/agentenv-tools:0.1.1`）。`packages.rs` 处理系统包（manifest `[packages.runtime_commands]`）。
- `server --setup-host --runtime-user U --runtime-group G`（root）：KVM 访问（`setup/kvm.rs`，含 KVM/PVM 互斥校验 `validate_mode`）、ublk（`setup/ublk.rs`）、网络容量（`setup/network_capacity.rs`）。
- 依赖路径版本化：`deps/firecracker/<version>/firecracker`、`deps/kernel/<version>/vmlinux.bin`（`cfg.rs::resolved_*_path`），所以升级 manifest 版本会自然下载新文件。
- 主机内核要求：6.8+（ublk）。

### 3.2 章：单节点 / Compose / K8s 部署

**一键安装** `scripts/install.sh`（431 行）：下载 latest release 的 `aenv-linux-<arch>.tar.gz`（aenv + aenv-buildctl + manifest.json）与 `aenv-server-linux-<arch>[-pvm].tar.gz`（server、ublk daemon、`deps/` 预下载依赖、default.toml、overlaybd.json）→ 安装到 `/usr/local/bin`、`/var/lib/aenv` → `server --setup-only` + `--setup-host` → 写 `/etc/default/aenv`（API_ADDR=127.0.0.1:8000 等）与 systemd unit（User=aenv，`AmbientCapabilities=CAP_NET_ADMIN CAP_SYS_ADMIN`，`NoNewPrivileges`，`LimitMEMLOCK=infinity`，`KillMode=process`，`TimeoutStopSec=30`）。API key 自动生成在 `${DATA_DIR}/secrets/api-key`。`scripts/install-cli.sh`（183 行）只装 CLI（linux/darwin × x86_64/aarch64）。

**Docker 镜像** `deploy/docker/Dockerfile.agentenv`（131 行）：cargo-chef 多阶段（chef→planner→build-deps→builder）→ `ubuntu:24.04` runtime-base（运行时包列表**硬编码**，与 manifest 手工同步，见 manifest 注释 85120b97）→ deps-stage 跑 `/server --setup-only` 预烘焙 `/workspace/env` → 最终镜像再跑一次"权威" `--setup-only` → `ENTRYPOINT ["/server"]`。`ARG AENV_VIRTUALIZATION_MODE=kvm|pvm`。gateway/scheduler：`golang:1.25` 构建 → distroless static；scheduler 额外带 `grpc_health_probe`。

**Compose** `deploy/docker-compose.yml`（111 行）：scheduler + gateway(`8000:8080`) + agentenv-a/b（privileged、`/dev:/dev`、`/dev/kvm`、healthcheck `/health`）。两个节点共享 named volume `agentenv-snapshot-store`（POSIX 快照仓库）与 `agentenv-auth`（secrets，gateway 以 `/run/secrets` 只读挂载读取 api-key）。控制面配置 `deploy/docker/config/default.json`：static 节点 `node-a→http://agentenv-a:8000`、`node-b→http://agentenv-b:8000`。依赖顺序：节点 healthy → scheduler healthy → gateway。Make：`deploy-up/down/logs/ps/build`。

**K8s** `deploy/k8s/`（kustomize）：
- base：namespace `agentenv-system`；ServiceAccount + Role/RoleBinding（scheduler watch EndpointSlice/Pod）；scheduler Deployment(1) + Service；gateway Deployment(1) + ClusterIP Service；`agentenv-node` DaemonSet（privileged，hostPath `/var/lib/aenv` 与 `/dev`，`AENV_NODE_ID` 取 Pod 名，preStop 等待 sandbox 清空，grace 3600s，readiness/liveness `/health`）；headless Service `agentenv-nodes`（discovery 用）；ublk-daemon metrics Service；ConfigMap（agentenv.toml/scheduler.json/gateway.json/sandbox-proxy-config）+ Secret `agentenv-auth`。
- scheduler k8s 配置：`discovery.mode=kubernetes, service_name=agentenv-nodes, port=8000`。节点 ID = EndpointSlice `TargetRef.Name`（Pod 名）；只取 `Serving=true`；`Terminating=true` → lingering；支持 `ignore_pod_selector` / `no_schedule_pod_selector`；IPv6 用方括号。
- `deploy/k8s/run.sh`（229 行）：render/apply/delete；`bootstrap_api_key` 若集群里无 `agentenv-auth` secret 则生成随机 key 创建。
- overlay `local-dev`：hostPath 改 `/var/lib/aenv`、挂载仓库 `env/` 到 `/workspace/env`、固定 sandbox access-token hash seed。Make：`k8s-render/apply/delete[-dev]`、`k8s-build`、`k8s-load-dev`（导入 k3s containerd）、`k8s-refresh-dev`、`k8s-redeploy`。

文档对应：`docs/src/deployment/{docker,docker-compose,static-multi-node,kubernetes,manual-compile,pvm}.md`。

### 3.3 章：PVM

- 用途：云 VM 无嵌套虚拟化时。PVM（SOSP'23 论文）由宿主内核模块 `kvm_pvm` 提供 `/dev/kvm` 兼容接口，AgentENV 仍走 Firecracker + /dev/kvm。
- 宿主：kvcache-ai/linux `pvm-kernel-6.12.33` 预编译 deb/rpm（`CONFIG_KVM_PVM=m`），需手动安装重启、`modprobe kvm_pvm`；AgentENV **不负责**装/载。
- 客户机：`[kernel.pvm] 6.12.33-pvm`（virt-pvm/linux `pvm-612` 分支，`CONFIG_PVM_GUEST`）；`[firecracker.pvm] v1.17.0-next.1` 来自另一个 fork `kvcache-ai/firecracker-next`（与 KVM 用的 1.15.1-patch-v1 是**不同代码线**）。
- 代码隔离点：`setup/kvm.rs::validate_mode`（KVM 模式下若 kvm_pvm 已加载则拒绝启动；PVM 模式要求已加载；PVM 仅 x86_64）；`cfg.rs` 在 PVM 下强制 `memory_snapshot.track_dirty_pages=false`，显式设 true 则报错 "has not been tested"；快照/持久化 sandbox 记录 `virtualization_mode`，跨模式拒绝恢复（`template/builder.rs`、`orchestrator/persistence/file_backed.rs`）。
- 安装：`AENV_VIRTUALIZATION_MODE=pvm` 走 install.sh（下载 `-pvm` bundle）/ Docker `aenv-server:<tag>-pvm` / 源码构建。release 只为 x86_64 构建 PVM bundle。
- **[推断/未验证]**：AgentENV 的内存快照路径唯一走 `/vm/dirty-memory-ranges`（见 4.3），PVM 下关闭了 dirty tracking，因此 firecracker-next 必须也实现该端点并在无 dirty log 时返回全量范围；该 fork 不在本地，无法确认。

### 3.4 章：aenv CLI（另一组）

- 仅记录发布相关：`scripts/release/package-cli.sh` 打包 `aenv` + 匹配版本的 `buildctl`（版本在 `config/buildkit-version`）+ `manifest.json`；CLI 构建矩阵 linux x86_64/aarch64、darwin x86_64/aarch64。

### 3.5 章：测试与基准

| 层次 | 位置 | 入口 |
|---|---|---|
| Rust 单元 + 能力测试 | 各 crate `#[cfg(test)]` | `make test-unit`（agentenv/envd/linux-cap lib；aenv bin；`--ignored` 能力测试经 `run-with-capabilities.sh`；ublk lib；3 个脚本自检） |
| Rust 集成 | `tests/integration/{fc,orchestrator,snapshot,snapshot_attached_drive,process,posix_startup_pack,envd_supervisor,ublk}.rs`（共 3,118 行）+ `tests/common/mod.rs` | `make test-agent-integration`（需 /dev/kvm、ublk、netns） |
| OSS 快照 E2E | `crates/e2e-tests/tests/snapshot_oss_e2e_test.rs`（794 行）+ `crates/test-support/src/minio.rs`（MinIO 容器助手） | 同上，`--ignored` |
| 存储 | storage/* 自带测试 | `make test-ublk`（含 `oss_backend_minio`） |
| envd | `scripts/tests/test_envd.sh` | `make test-envd` |
| HTTP E2E | `scripts/tests/e2e/run_e2e.sh` + `suites/01..17_*.sh`（health、lifecycle、timeout、metadata、template、proxy、pagination、auth、e2b 兼容、**10_cluster_deployment**、**11_node_metrics**、shared repository、snapshot、code interpreter、volume、randomized volume、buildkit）+ e2b Python/TS SDK 兼容脚本 | `make test-e2e`（single-node）/`test-e2e-compose`/`test-e2e-k8s`/`test-e2e-all`；`E2E_MODE`、`SUITE_FILTER` |
| BuildKit | `scripts/buildkit/test.py` | `make test-buildkit` |
| Go | `services/**/_test.go`（6.9k 行，测试 ≥ 生产代码；scheduler 测试需本地 Redis） | `make -C services test fmt-check vet` |
| 基准 | `crates/benchmarks/benches/{snapshot,ublk_overlaybd,orchestrator_store,oci_conversion_pipeline}_benchmark.rs`（2,898 行） | `make bench[-snapshot|-ublk|-orchestrator-store|-oci-conversion]`（release + 安装 ublk daemon） |
| E2B 基准 | `scripts/e2b/run-e2b-benchmark.sh` | workflow `e2b-benchmark.yml`（手动） |
| 变异/覆盖 | `adev/src/{mutants,coverage}.rs` | `cargo adev mutants`（workflow 手动）/`make coverage`（cargo-llvm-cov，main push，结果发布到元数据分支，非阻塞） |

CI workflows（`.github/workflows/`）：`ci.yml`（fmt/clippy/test-unit，PR+push）、`services-ci.yml`（Go build/test/fmt/vet，装 Redis）、`integration-tests.yml`（KVM 集成 + single-node/compose 两种 E2E，用 `sg kvm`，构建三镜像，装 e2b CLI 与 Python SDK）、`envd-tests.yml`、`ublk-tests.yml`、`coverage.yml`、`mutation-tests.yml`、`benchmark.yml`、`e2b-benchmark.yml`、`docs.yml`、`publish-tools-image.yml`、`open-code-review.yml`（`pull_request_target`）、`release.yml`。**k8s E2E 不在 CI 中**。composite actions：`rust-ci-setup`、`sandbox-ci-setup`、`sandbox-artifacts-cleanup`。

### 3.6 章：构建与发布

- 根 `Makefile`（302 行）：`PROFILE=debug|release`；`AENV_HOME_PATH=/var/lib/aenv`；能力 runner 通过 `CARGO_TARGET_<HOST>_RUNNER` 注入；`services-%`/`gateway-%`/`scheduler-%` 转发到 Go Makefile；`docs`/`docs-serve`（软链 `src/api/openapi.yml` 后 `mdbook build`）。
- `adev/`（1,197 行）：`codegen.rs`（openapi-generator 生成 firecracker/envd/agentenv-server/custom-extension）、`coverage.rs`、`mutants.rs`、`ensure_tool.rs`、`config.rs`（其中示例 `[kernel] version = "vmlinux-6.1.102"` 是测试样例，非真实）。
- `tools-image/`：guest `/dev/vda` 工具盘源码（从 e2b-dev/infra 编译 envd + BusyBox + `/init` + `/agentenv/pivot-init`），导出为带 `io.agentenv.tools-drive.format=oci-rootfs-v1` 标签的 OCI 镜像；`publish-tools-image.yml` 手动发布 `ghcr.io/kvcache-ai/agentenv-tools`。
- 发布流程 `release.yml`（398 行，tag 触发）：
  1. `validate-version`：tag 必须等于 `cargo metadata` 中所有包的版本。
  2. CLI 4 平台构建（`--locked`）+ `package-cli.sh`。
  3. server：ubuntu-22.04（x86_64，modes "kvm pvm"）与 ubuntu-22.04-arm（aarch64，kvm），`OPENSSL_STATIC=1 --features vendored-openssl`，strip；每个 mode：改写 default.toml 的 `virtualization_mode`、在临时 HOME 跑 `server --setup-only` 把 Firecracker/kernel/tools/overlaybd/regctl 预下载进 bundle `deps/`。
  4. GitHub Release：`SHA256SUMS`、git-cliff（`cliff.toml`：feat/fix/refactor/perf/docs 分组，ci/chore/style/test/build 跳过）生成 notes 并前置文档链接。
  5. Docker：多架构 KVM 镜像 `ghcr.io/<owner>/aenv-server:<tag>` + manifest；PVM 镜像 `:<tag>-pvm`、`:latest-pvm`（仅 amd64）。
- 文档站：`docs/book.toml`（mdBook + mdbook-mermaid 0.17 + 自定义 version-selector），`docs.yml` 按版本发布到 gh-pages（tag→版本目录，main→dev）；API 参考用 stoplight-elements 渲染 openapi.yml。

---

## 4. Part 10：Firecracker 补丁层

### 4.1 版本对应关系（已核实）

- `config/deps_manifest.toml`：`[firecracker.kvm] version = "1.15.1-patch-v1"`，`url = https://github.com/kvcache-ai/firecracker/releases/download/aenv-deps/firecracker-{version}-{arch}.tgz`；`[kernel.kvm] vmlinux-6.1.175` 同一 release `aenv-deps` 下 `{version}-{arch}`。
- 下载逻辑：`src/setup/deps.rs::ensure_firecracker` → `resolve_url` 替换 `{version}`/`{arch}` → `download_file`（reqwest，整体读入内存后写 `.tmp` 再 rename）→ `extract_firecracker` 从 tgz 中找出 `firecracker` 与 `cpu-template-helper`。可被 `[firecracker] binary_path/version/url` 覆盖。
- F 中 tag `aenv-deps` = 90288c39，该 commit 把所有 crate 版本从 `1.15.1` 改为 `1.15.1-patch-v1`（swagger `version: 1.15.1-patch-v1`）→ 与 manifest 吻合。release 资产列表本身无法从本地查询 **[未验证]**。
- `S/thirdparty/firecracker-client/firecracker.yaml` 与 `aenv-deps` 的 `src/firecracker/swagger/firecracker.yaml` 除 `version:` 行外**完全一致**（diff 为空）；但 client crate 的 Cargo 版本与 yaml `version` 仍写 `1.15.1`。
- 生成的 client 只有 models（45 个）+ `apis/configuration.rs`；实际 HTTP 调用是手写的 `src/sandbox/firecracker/instance.rs`（`request`/`request_no_content` over UDS）。

### 4.2 补丁表：`git log v1.15.1..aenv-deps`（7 commits；总 diff 30 files，+1,219/−145）

| # | commit | 日期/作者 | 文件数 | +/− | 内容 | AgentENV 调用点 |
|---|---|---|---|---|---|---|
| 1 | c3ec7aef | 2026-02-03 huang-jl | 1 | +3/−2 | `feat(pmem)`：virtio-pmem 用 `seek(End)` 取文件大小替代 `fstat`（块设备如 dm snapshot `fstat` 返回 0） | **未使用**：S 中无 `/pmem` 调用 |
| 2 | caccb127 | 2026-03-05 huang-jl | 8 | +277/−18 | `feat(snapshot)`：`PUT /snapshot/create` 的 `mem_file_path` 变为可选，缺省时只保存 VM state（`SnapshotCreateParams.mem_file_path: Option<PathBuf>`，`persist.rs`）；附带新增 FC 仓库 CLAUDE.md 161 行 | `instance.rs::create_state_only_snapshot`（L468，`snapshot_type=Diff`，不填 mem_file_path）← `sandbox.rs::snapshot_memory_to_overlaybd`（L1337） |
| 3 | d571a650 | 2026-03-22 huang-jl | 13 | +382/−84 | `feat(virtio-blk)`：Drive 新字段 `direct: bool`，以 `O_DIRECT` 打开 backing file，对齐不满足时自动 bounce buffer（`io/mod.rs`、`async_io.rs`、`sync_io.rs`；持久化到 snapshot state） | `instance.rs::add_drive(..., direct, io_engine, ...)`（L317）；`sandbox.rs` L2419 tools 盘 `/dev/vda` direct=false/Sync；L2440 用户 rootfs `/dev/vdb` direct=true/Async；L2508 extra drives direct=true/Async（后端都是 ublk 块设备，绕过宿主 page cache） |
| 4 | 8c42a29d | 2026-03-27 huang-jl | 5 | +302/−134 | `feat(vmm)`：新 RPC `GET /vm/guest-memory-regions`，返回 `[GuestRegionUffdMapping{base_host_virt_addr,size,offset,page_size}]`，供外部进程 `process_vm_readv` 直接读 guest 内存；post-boot only | **未直接使用**（S 中无调用；client 有 model）。思路被 #7 取代 |
| 5 | 41385d4e | 2026-04-22 huang-jl | 1 | +9/−5 | `feat(snapshot)`：`vstate/memory.rs` 用 seek 取内存镜像文件大小，使块设备（ublk）可作为 memory file | `instance.rs::load_snapshot_file`（L523）← `sandbox.rs` L2269，`mem_device_path` 是 ublk overlaybd 设备（`UblkDeviceManager::create_dedicated_mem_device` 或共享设备），`track_dirty_pages` 取配置 |
| 6 | 2a6598dc | 2026-05-07 huang-jl | 5 | +53/−30 | `fix: rebase onto v1.15.1`：把前述补丁适配到上游 v1.15.1（主要 async_io） | — |
| 7 | 90288c39 | 2026-07-14 Hygge-Gezelligheid | 13 | +350/−29 | `feat: expose dirty memory ranges`：`GET /vm/dirty-memory-ranges` → `DirtyMemoryRanges{page_size,memory_size,ranges:[{base_host_virt_addr,image_offset,length}]}`；`Vm::get_dirty_memory_ranges_preserve` 读 KVM dirty log 后**写回** FC 内部 bitmap（"逻辑上不清除"，外部消费失败下次快照仍能看到）；同义于 `dump_dirty` 语义；版本号 → 1.15.1-patch-v1 | `instance.rs::get_dirty_memory_ranges`（L480）← `sandbox.rs::snapshot_memory_to_overlaybd` L1351 → `convert_dirty_memory_to_overlaybd(firecracker_pid, &ranges, ...)` 经 `process_vm_reader.rs::ProcessVmReader`（`process_vm_readv` 从 FC 进程地址空间读）直接打包成 overlaybd 内存层（`overlaybd_snapshot.rs`） |

**组合效果（书中可作为核心论点）**：AgentENV 的快照内存路径不再让 Firecracker 写 `mem.bin`：
1. `PUT /snapshot/create`（无 mem_file_path）只写 `vm_state.bin`（补丁 2）；
2. `GET /vm/dirty-memory-ranges` 拿到脏页的 HVA + 镜像偏移（补丁 7）；
3. AgentENV 用 `process_vm_readv` 直接从 FC 进程读脏页，写入 overlaybd 层（可增量叠加）；
4. 恢复时 overlaybd 层经 ublk 暴露为块设备，作为 file backend 的 memory file（补丁 5 使块设备大小可识别）；
5. 磁盘侧 ublk 设备用 O_DIRECT（补丁 3）避免宿主 page cache 双重缓存。
`process_vm_reader.rs` 中 TODO：`process_vm_readv` 同步执行在 Tokio worker 上，未 offload。

### 4.3 patch-v2 与其他分支

- `origin/v1.15.1-patch` = tag `v1.15.1-patch-v2` = 9fbc98e4（总 diff 相对 v1.15.1：38 files，+2,497/−149），在 aenv-deps 之上 2 个 commit：
  - `dcb1186c`（2026-08-20，PR #18，Yicheng Lin）：`PUT /vm/pre-fault-memory`，paused-only；在支持 `KVM_CAP_PRE_FAULT_MEMORY` 的 x86_64 上，将页对齐 GPA 范围分摊到各 vCPU 线程调用 `KVM_PRE_FAULT_MEMORY`；aarch64 不支持；拒绝 hotpluggable 范围；更新 seccomp 规则。13 files，+1,241/−4（`vstate/prefault.rs` 602 行）。
  - `9fbc98e4`（2026-08-26，PR #20）：release v2；顺带"expose guest physical addresses for memory regions"（`persist.rs` 34 行改动，guest-memory-regions 返回值增加 GPA 字段；11 files，+61/−24），版本 → 1.15.1-patch-v2。
  - **AgentENV v0.2.3 不使用**：manifest 仍为 patch-v1；S 中全仓库 grep `pre-fault|prefault|patch-v2` 零命中；client yaml 无该端点。可作为"下一步预取优化"的伏笔（v0.2.3 的 startup manifest 预取目前在 ublk/overlaybd 层做）。
- `origin/v1.15.1-patch-nestedvirt`：在 aenv-deps 之上加 3 个 commit（`d5cd39ac` 保存嵌套 vCPU 状态、`af3ee416` nested SVM 的 `MSR_VM_HSAVE_PA`、`c7e1cceb` 保留仅 VMXON 的嵌套状态，2026-06~09）——支持 guest 内再跑 KVM 的快照；S 未引用。
- `origin/v1.16.1-patch`：HEAD 2038188f 即上游 `v1.16.1^{}`，**无任何自定义补丁**（占位分支，为将来 rebase 准备）。
- 另有 dependabot 分支 2 个，忽略。

### 4.4 Guest kernel 配置来源（只陈述事实）

- S 中无任何 kernel `.config`、无构建脚本；kernel 只以预编译 `vmlinux` 资产形式从 `kvcache-ai/firecracker` release `aenv-deps` 下载。
- F 中 `resources/guest_configs/` 有上游 Firecracker CI 配置：`microvm-kernel-ci-{x86_64,aarch64}-{5.10,6.1}.config`、`ci.config`、`pcie.config`、`virtio-pmem.config`、`virtio-mem.config`、`vmclock.config`、`ftrace.config`、`debug.config`；`resources/rebuild.sh::build_al_kernels` 用 Amazon Linux 内核源码 + `microvm-kernel-ci-$ARCH-6.1.config` 叠加 ci/pcie/pmem/mem/vmclock 片段构建 6.1 内核。
- `git diff v1.15.1 aenv-deps -- resources/` 为空 → **fork 未修改任何 guest config**。命名 `vmlinux-6.1.175` 与上游 FC CI 工件命名一致，**[推断]** 即用上游 6.1 CI 配置构建（或直接取自上游 CI 工件），但无法从仓库确认具体 config。
- 运行时相关事实：`src/sandbox/firecracker/config.rs::DEFAULT_BOOT_ARGS` = `console=ttyS0 reboot=k panic=1 pci=off` + 一组 `damon_reclaim.*` 参数（min_age 100ms、quota 20ms/1GiB/500ms、wmarks 990/990/200‰、skip_anon=Y）→ 隐含要求 guest 内核开启 `CONFIG_DAMON_RECLAIM`；`pci=off` 表明走 virtio-mmio。v0.2.3 `59b36a4` 新增 free-page reporting order 设置（与 balloon free page reporting 相关）。
- PVM guest：6.12.33，`CONFIG_PVM_GUEST`，来自 virt-pvm/linux `pvm-612`。

---

## 5. 意外发现 / 技术债（Part 10 "已知问题"章素材）

控制面：
1. **Schedule 不排除 UNHEALTHY / 从未心跳的节点**。`Schedule` 只用 `Snapshot(false)` 去掉 lingering；`deriveObservedNodeViewLocked` 推导出的 UNHEALTHY 状态只用于展示和 P2P 过滤。static 模式下一个宕机节点仍会被 round-robin 选中，导致约 1/N 的创建请求 502。`FilterByResourceLimit` 还会用宕机前最后一次的快照数据判断。测试 `TestScheduleOnlyConsidersReadyNodes` 名不副实，只验证了 lingering。`Snapshot()` 的注释 "filtered by their derived status" 也与实现不符。（k8s 模式下 readiness probe 会让失败 Pod 变 not-serving，部分缓解。）
2. **调度 hint 未被使用**：gateway 为 `/sandboxes-cold` 解析 cpu/mem/images/metadata，但两种内置策略都忽略；没有负载感知或镜像亲和策略。
3. **ReportSandboxEvent 是空实现**：节点持续发送事件批次，scheduler 只打 debug 日志。
4. **CPU config 只上报一次**：节点成功心跳后清空 `pending_cpu_config_json`。scheduler 重启后观测记录全部丢失，节点不会再报 CPU config → `allConfigsReadyLocked` 永远为 false → 新加入节点拿不到交集，已有节点保留旧交集。**[推断]**
5. **心跳名单与 RecordAssignment 的竞态**：节点在 T1 采集 sandbox_ids，T2 新 sandbox 入 store，T3 gateway RecordAssignment，T4 该心跳到达 → `ReconcileNode` 删除刚写入的绑定，直到下一次心跳（≤5s）才恢复，期间对该 sandbox 的请求 404。**[推断，未复现]**
6. 普通 sandbox 的 RecordAssignment 失败被吞（只 warn），依赖心跳自愈；与 5 叠加时窗口更大。
7. **节点关停先 UnregisterNode 再暂停 sandbox**：注销会清空该节点全部绑定，之后到节点重启并首次心跳之前，paused sandbox 的 resume/connect 请求均 404（运行中的 sandbox 也一样，若关停很慢）。
8. Redis Lua 脚本访问未在 `KEYS` 中声明的拼接 key（旧节点 `:node:` 集合、`:sandbox:` key）→ **不兼容 Redis Cluster**，只能单实例/主从。
9. P2P artifact 索引与节点注册表都只在 primary 内存中，HA 不覆盖；k8s 清单不含 query-only/Redis 部署，HA 只停留在 README 描述。
10. gateway 对创建请求不做失败重试/换节点；集群列表"全有或全无"，任何一个节点慢/挂会让 `GET /sandboxes` 整体失败（设计取舍，但规模上去后是可用性问题）。
11. gateway 的路由规则是路径模式硬编码（`isSandboxControlPlaneRequest` 等），节点 API 每加一个按 sandbox 路由的端点都要同步改 Go 代码，易遗漏。
12. 静态模式节点列表写死在 JSON；node_id 必须与 `AENV_NODE_ID` 精确匹配，否则心跳被拒（只有日志提示）。
13. `report_ttl` 无环境变量覆盖（其他关键参数都有）。

部署/工程：
14. 依赖下载**无校验和**：`download_file` 不校验 sha256，也无签名；整个文件读入内存（kernel/FC tgz 尚可）。release bundle 只对最终 tar.gz 生成 SHA256SUMS。
15. `rust-toolchain.toml` 用 `stable` 不锁版本，release 用 `dtolnay/rust-toolchain@stable`，构建不可完全复现。
16. Dockerfile 运行时包列表与 `deps_manifest.toml [packages.*]` 需人工同步（manifest 注释自承）。
17. 文档漂移：services/README 写 hostPath `/var/lib/agentenv`，实际 DaemonSet 是 `/var/lib/aenv`；README gRPC 列表漏 4 个 P2P RPC；资源限制表漏 3 个 including_paused 字段；CLAUDE.md 有 3 个失效文档链接。
18. k8s E2E（`make test-e2e-k8s`）不在 CI；`storage/uffd-core` 与 `load_snapshot_uffd` 是未接入的遗留代码。
19. Compose 两节点共享 secrets 与 POSIX 快照仓库 volume —— 这是"多节点模拟"，不代表生产拓扑。

Firecracker 层：
20. 维护两条 FC 代码线：KVM 用 kvcache-ai/firecracker 1.15.1-patch-v1，PVM 用 kvcache-ai/firecracker-next v1.17.0-next.1；dirty-memory-ranges 等补丁在 PVM 线上是否等价 **[未验证]**。
21. 补丁 #1（pmem seek）、#4（guest-memory-regions）在 v0.2.3 中无调用；patch-v2 的 pre-fault API、nestedvirt 分支均已存在但未被采用；v1.16.1-patch 分支是空壳——补丁栈 rebase 到新上游的工作尚未开始。
22. client crate 版本号仍标 1.15.1，与实际 swagger（patch-v1）不一致，容易误导。
23. `process_vm_readv` 在 Tokio worker 上同步执行（代码内 TODO）。

---

## 6. 章节划分建议

Part 8（控制面）建议调整为 5 章：
1. **8.1 控制面总览与 proto 契约**（把原"services api"提前）：为什么单节点不需要它、13 个 RPC 分组（调度/绑定/观测/P2P/生命周期）、Go/Rust 双端生成、状态推导表。
2. **8.2 Gateway：路由判定与反向代理**：认证分界（控制面 API key vs 数据面节点自验）、6 种 routeSource、`/proxy` 改写、流式/WebSocket、集群列表聚合与分页、metrics 聚合。
3. **8.3 Scheduler：放置、绑定与 HA**：Filter→Strategy 两段式、BindingStore（内存/Redis Lua）、query-only 副本、k8s EndpointSlice 发现与 lingering。
4. **8.4 心跳、节点可观测与 CPU 模板交集**：节点侧 reporter、ReconcileNode"心跳即真相"一致性模型、注销与优雅下线、Prometheus 指标双端统一桶、CPU 交集（这一节很独特，值得单列小节）。
5. **8.5 P2P 发现接口**（与 P2P 内部章交叉引用，控制面只讲索引与对等节点过滤）。
另在 8.3 或 8.4 末尾放"失败模式表"（2.7）。

Part 9（部署与工程）建议 6 章基本保持，但微调：
1. 9.1 主机准备与依赖供给（docker-setup.sh、`--setup-only/--setup-host`、deps manifest、版本化路径）。
2. 9.2 单节点安装与 systemd（install.sh、权限模型：aenv 用户 + ambient caps）。
3. 9.3 Compose 与 K8s 多节点（含 preStop drain、kustomize overlay、run.sh 自动生成密钥）。
4. 9.4 PVM（建议与 4.x 的 FC 双代码线问题互相引用）。
5. 9.5 测试金字塔与基准（表 3.5；强调能力委托 runner 与 CI 中的 KVM）。
6. 9.6 构建、代码生成与发布（Makefile/adev/build.rs/release.yml/git-cliff/文档站/tools-image）。
aenv CLI 章由他组负责，可放到 Part 9 之外（更像"使用"而非"部署"）。

Part 10：
- **10.x Firecracker 补丁层**：按"内存快照零拷贝打包"这一主线讲补丁 2/5/7 + process_vm_readv，再讲 O_DIRECT（补丁 3），最后附表列出未使用补丁、patch-v2 pre-fault、nestedvirt、v1.16.1 空分支与 PVM fork；guest kernel 来源作为小节。
- **10.y 已知问题与技术债**：直接用第 5 节清单，按"正确性 / 可用性 / 可运维性 / 供应链 / 文档"分类。

Part 0：仓库地图可复用 CLAUDE.md Code Map + 1.1 LOC 表；版本表用 1.3；强调"生成代码约 2.6 万行不计入"。
