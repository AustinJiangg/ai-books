# 72 · 接口总表：HTTP、Firecracker、daemon RPC 与 gRPC

> 本附录把散在全书的接口集中成几张表：节点 `server` 对外暴露的每个 HTTP 端点及其 handler、AgentENV 调用的每个 Firecracker 端点、
> ublk-daemon 的 14 种 RPC、scheduler 的 13 个 gRPC、custom extension 的 4 个 hook，以及 P2P 门面的 3 个 HTTP 端点。每一行都链到详细讲解的篇目与小节。
>
> **读者**：写客户端、做集成、排查「这个请求最后落到哪段代码」的读者。　**预备**：[第 08 篇 · 系统架构：单节点与多节点](08-system-architecture.md)、[第 12 篇 · 规范驱动的服务骨架](12-spec-driven-server.md)。
> **代码**：`src/api/openapi.yml`、`src/api/server.rs`、`src/api/proxy.rs`、`src/api/impls/`、`src/api/impls/image_build/transport.rs`、`src/sandbox/firecracker/instance.rs`、`storage/ublk-daemon/src/{protocol,client}.rs`、`services/api/proto/scheduler.proto`、`services/scheduler/internal/service.go`、`src/custom_extension_api/openapi.yml`、`src/overlaybd/p2p/facade.rs`

---

## 0. 本篇要回答的问题

1. 节点 `server` 的 HTTP 路由由哪几部分拼成？每个端点由哪个 handler 实现，它在 e2b infra 2026.09 的 spec 里属于第 18 篇的哪一类？
2. AgentENV 调用了哪些 Firecracker 端点，在哪个函数里调用，哪些依赖 AENV 补丁版 Firecracker 的行为？
3. ublk-daemon 的 14 种请求各返回什么、谁在调用、哪些没有调用者？
4. scheduler 的 13 个 gRPC 分别由 gateway 还是节点调用，调用点在哪里？
5. 节点作为客户端调用的外部 HTTP 接口（custom extension hook）与它在本机起的辅助 HTTP 服务（P2P 门面、daemon 指标）各有哪些端点？

---

## 1. 怎样读这些表

**节点 HTTP 路由的组成。** `src/api/server.rs` 的 `new()` 按顺序拼出节点的 axum 路由器：
先是 openapi-generator 从 `src/api/openapi.yml` 生成的控制面路由（`agentenv_http_server::server::new()`），只对它挂 `optional_connect_body()`；
再 `merge` 进 `proxy::router()`（`/proxy`、`/proxy/{*proxy_path}` 与 fallback）和 `impls::image_build::router()`（BuildKit 隧道）；
最后手写一条 `GET /metrics`。外层由内到外依次是 `sandbox_proxy_classifier()`（Host 名路由）、`require_auth()`（鉴权）与 `http_metrics_middleware()`（[第 12 篇 §4.1](12-spec-driven-server.md#41-servernew)）。

**handler 列。** 生成路由的 handler 是生成 trait 的方法，实现都在 `src/api/impls/` 下的 `impl <Trait><()> for ApiImpl` 里：
`Sandboxes`（`sandbox.rs`）、`Templates`（`template.rs`）、`Snapshots`（`snapshots.rs`）、`Volumes`（`volumes.rs`）、`Admin`（`admin.rs`）与 `Default`（`mod.rs`）。
表里只写方法名；手写路由写出文件与函数名。

**「类」列。** 沿用[第 18 篇 §4](18-e2b-compatibility.md#4-端点对照以-e2b-infra-202609-为参照)对照 e2b infra 2026.09 `spec/openapi.yml` 得到的四类：

| 类 | 含义 |
|---|---|
| 甲 | 两边都有（同名不等于同形，形状差异见第 18 篇 §4、§5） |
| 乙 | E2B 形状，但 2026.09 的 spec 里没有 |
| 丙 | AgentENV 扩展，E2B SDK 不会调用 |
| 丁 | 2026.09 有、AgentENV 没有（本篇不逐条列出，见第 18 篇 §4） |

**鉴权。** 所有节点路由都经过 `require_auth()`：控制面请求要 `X-API-Key`，非代理请求的 `/health` 与 `/metrics` 免鉴权，数据面请求按沙箱 token 判定（[第 13 篇 §4](13-authentication.md#4-require_auth-的决策)）。
下面的表不再逐行写鉴权要求。

**路径参数。** 表里把 `{sandboxID}` 简写成 `{id}`，`{templateID}` / `{buildID}` 简写成 `{t}` / `{b}`，与第 14、15 篇一致。

---

## 2. 节点 HTTP 端点

### 2.1 E2B 形：沙箱

`Sandboxes` trait，实现在 `src/api/impls/sandbox.rs`。机制在[第 14 篇](14-sandbox-api.md)，端点总览见[第 14 篇 §2](14-sandbox-api.md#2-端点一览)。

| 方法 | 路径 | handler | 类 | 篇目 |
|---|---|---|---|---|
| `POST` | `/sandboxes` | `sandboxes_post()` | 甲 | [14 §3.1](14-sandbox-api.md#31-sandboxes_post-的步骤) |
| `POST` | `/v2/sandboxes` | `v2_sandboxes_post()` | 乙 | [14 §3.3](14-sandbox-api.md#33-v2一层字段适配) |
| `GET` | `/sandboxes` | `sandboxes_get()` | 甲 | [14 §8](14-sandbox-api.md#8-列表状态折叠与分页) |
| `GET` | `/v2/sandboxes` | `v2_sandboxes_get()` | 甲 | [14 §8.3](14-sandbox-api.md#83-游标分页) |
| `GET` | `/sandboxes/{id}` | `sandboxes_sandbox_id_get()` | 甲 | [14 §8.1](14-sandbox-api.md#81-八个状态折成两个) |
| `DELETE` | `/sandboxes/{id}` | `sandboxes_sandbox_id_delete()` | 甲 | [14 §6](14-sandbox-api.md#6-pauseresumedelete-与错误码)、[21 §2](21-deletion-and-volume-capture.md#2-入口与互斥) |
| `POST` | `/sandboxes/{id}/pause` | `sandboxes_sandbox_id_pause_post()` | 甲 | [14 §6](14-sandbox-api.md#6-pauseresumedelete-与错误码) |
| `POST` | `/sandboxes/{id}/resume` | `sandboxes_sandbox_id_resume_post()` | 甲 | [14 §6](14-sandbox-api.md#6-pauseresumedelete-与错误码) |
| `POST` | `/sandboxes/{id}/connect` | `sandboxes_sandbox_id_connect_post()` | 甲 | [14 §5](14-sandbox-api.md#5-connect一个端点覆盖连上或拉起) |
| `POST` | `/v2/sandboxes/{id}/connect` | `v2_sandboxes_sandbox_id_connect_post()` | 乙 | [14 §5](14-sandbox-api.md#5-connect一个端点覆盖连上或拉起) |
| `POST` | `/sandboxes/{id}/timeout` | `sandboxes_sandbox_id_timeout_post()` | 甲 | [14 §4](14-sandbox-api.md#4-四个改-ttl-的入口) |
| `POST` | `/sandboxes/{id}/refreshes` | `sandboxes_sandbox_id_refreshes_post()` | 甲 | [14 §4](14-sandbox-api.md#4-四个改-ttl-的入口) |
| `PUT` | `/sandboxes/{id}/network` | `sandboxes_sandbox_id_network_put()` | 乙 | [14 §7](14-sandbox-api.md#7-put-network只换出站策略)、[30 §5](30-egress-policy-and-proxy.md#5-不中断地替换策略) |
| `POST` | `/sandboxes/{id}/snapshots` | `sandboxes_sandbox_id_snapshots_post()` | 甲 | [16 §3](16-snapshot-and-volume-api.md#3-创建快照) |
| `GET` | `/sandboxes/metrics` | `sandboxes_metrics_get()` | 甲 | [24 §3.5](24-metrics-and-events.md#35-存储与查询) |
| `GET` | `/sandboxes/{id}/metrics` | `sandboxes_sandbox_id_metrics_get()` | 甲 | [24 §3.5](24-metrics-and-events.md#35-存储与查询) |

v1 与 v2 的 connect 是两个 handler：`v2_sandboxes_sandbox_id_connect_post()` 允许请求体缺省，这是 `server.rs` 的 `optional_connect_body()` 专门为它补上的（[第 12 篇 §4.2](12-spec-driven-server.md#42-两个补丁可选-body-与-json-404)）。
`POST /sandboxes` 与 `POST /sandboxes/{id}/resume` 在 spec 里标为 deprecated，仍然可用。

### 2.2 E2B 形：模板、快照与卷

`Templates`（`template.rs`）、`Snapshots`（`snapshots.rs`）、`Volumes`（`volumes.rs`）三个 trait。

| 方法 | 路径 | handler | 类 | 篇目 |
|---|---|---|---|---|
| `POST` | `/v3/templates` | `v3_templates_post()` | 甲 | [15 §3.1](15-template-build-api.md#31-时序) |
| `POST` | `/v2/templates/{t}/builds/{b}` | `v2_templates_template_id_builds_build_id_post()` | 甲 | [15 §3.1](15-template-build-api.md#31-时序) |
| `GET` | `/templates/{t}/builds/{b}/status` | `templates_template_id_builds_build_id_status_get()` | 甲 | [15 §5](15-template-build-api.md#5-状态与日志接口) |
| `GET` | `/templates/{t}/builds/{b}/logs` | `templates_template_id_builds_build_id_logs_get()` | 甲 | [15 §5](15-template-build-api.md#5-状态与日志接口) |
| `GET` | `/templates` | `templates_get()` | 甲 | [15 §2](15-template-build-api.md#2-模板即快照记录) |
| `GET` | `/v2/templates` | `v2_templates_get()` | 乙 | [15 §2](15-template-build-api.md#2-模板即快照记录) |
| `GET` | `/templates/{t}` | `templates_template_id_get()` | 甲 | [15 §2](15-template-build-api.md#2-模板即快照记录) |
| `DELETE` | `/templates/{t}` | `templates_template_id_delete()` | 甲 | [15 §2](15-template-build-api.md#2-模板即快照记录)、[16 §4](16-snapshot-and-volume-api.md#4-读取快照) |
| `GET` | `/templates/aliases/{alias}` | `templates_aliases_alias_get()` | 甲 | [15 §2](15-template-build-api.md#2-模板即快照记录) |
| `GET` | `/snapshots` | `snapshots_get()` | 甲 | [16 §4](16-snapshot-and-volume-api.md#4-读取快照) |
| `GET` | `/snapshots/{snapshotID}` | `snapshots_snapshot_id_get()` | 乙 | [16 §4](16-snapshot-and-volume-api.md#4-读取快照) |
| `POST` | `/volumes` | `volumes_post()` | 甲 | [16 §6.1](16-snapshot-and-volume-api.md#61-volumes_post) |
| `GET` | `/volumes` | `volumes_get()` | 甲 | [16 §6.2](16-snapshot-and-volume-api.md#62-读取与列表) |
| `GET` | `/volumes/{volumeID}` | `volumes_volume_id_get()` | 甲 | [16 §6.2](16-snapshot-and-volume-api.md#62-读取与列表) |
| `DELETE` | `/volumes/{volumeID}` | `volumes_volume_id_delete()` | 甲 | [16 §6.3](16-snapshot-and-volume-api.md#63-删除) |

spec 里没有删除快照的端点；沙箱快照只能经 `DELETE /templates/{t}` 删除，而这个 handler 不检查记录来源（[第 16 篇 §4](16-snapshot-and-volume-api.md#4-读取快照)）。

### 2.3 AgentENV 原生（丙类）

| 方法 | 路径 | handler | 类 | 篇目 |
|---|---|---|---|---|
| `POST` | `/sandboxes-cold` | `sandboxes_cold_post()`（`sandbox.rs`） | 丙 | [14 §3.4](14-sandbox-api.md#34-冷启动-sandboxes-cold) |
| `POST` | `/sandboxes/{id}/fork` | `sandboxes_sandbox_id_fork_post()`（`sandbox.rs`） | 丙 | [51 §2](51-fork.md#2-端到端链路)、[14 §9](14-sandbox-api.md#9-fork-与-snapshot只看-api-形状) |
| `GET` | `/sandboxes/{id}/custom-extension-params` | `sandboxes_sandbox_id_custom_extension_params_get()` | 丙 | [33 §5](33-custom-extension-hooks.md#5-扩展参数存储继承与修改) |
| `PATCH` | `/sandboxes/{id}/custom-extension-params` | `sandboxes_sandbox_id_custom_extension_params_patch()` | 丙 | [33 §5.3](33-custom-extension-hooks.md#53-patchhook-在锁外) |
| `PUT` | `/templates/{t}/builds/{b}/builder` | `templates_template_id_builds_build_id_builder_put()`（`template.rs`） | 丙 | [15 §4.2](15-template-build-api.md#42-受理put-builder) |
| `DELETE` | `/templates/{t}/builds/{b}/builder` | `templates_template_id_builds_build_id_builder_delete()` | 丙 | [15 §4.5](15-template-build-api.md#45-取消与清理) |
| `GET`（WebSocket） | `/templates/{t}/builds/{b}/builder` | 手写：`image_build/transport.rs` 的 `connect()` | 丙 | [15 §4.4](15-template-build-api.md#44-隧道get-builder) |

最后一行不在 `openapi.yml` 里。`impls::image_build::router()` 只注册这一条 `GET` 路由，它与生成路由里同一路径的 `PUT` / `DELETE` 在 `merge` 后共存；
会话不处于 Ready 时返回 409 `builder is not ready`，并发隧道连接数上限是 `MAX_TUNNEL_CONNECTIONS`（8）。

### 2.4 节点与观测

| 方法 | 路径 | handler | 类 | 篇目 |
|---|---|---|---|---|
| `GET` | `/health` | `health_get()`（`Default`，`mod.rs`），恒 204 | 甲 | [12 §6](12-spec-driven-server.md#6-最小的实现health-与-nodes) |
| `GET` | `/nodes` | `nodes_get()`（`Admin`，`admin.rs`） | 甲 | [12 §6](12-spec-driven-server.md#6-最小的实现health-与-nodes) |
| `GET` | `/nodes/{nodeID}` | `nodes_node_id_get()`（`Admin`） | 甲 | [12 §6](12-spec-driven-server.md#6-最小的实现health-与-nodes) |
| `GET` | `/metrics` | 手写：`agentenv_observability::metrics_handler`（`server.rs` 挂载） | 丙 | [24 §5.1](24-metrics-and-events.md#51-记录器与暴露位置) |

### 2.5 代理入口（丙类，数据面）

| 方法 | 路径或匹配条件 | handler（`src/api/proxy.rs`） | 路径改写 | 篇目 |
|---|---|---|---|---|
| 任意 | `/proxy` | `proxy_via_prefix()` | 去掉 `/proxy`，空路径补成 `/` | [17 §2](17-reverse-proxy.md#2-三个入口) |
| 任意 | `/proxy/{*proxy_path}` | `proxy_via_prefix()` | 只去掉开头的 `/proxy` | [17 §2](17-reverse-proxy.md#2-三个入口) |
| 任意 | 未匹配任何路由、带路由头 | fallback：`proxy_via_fallback()` | 原样保留 | [17 §2](17-reverse-proxy.md#2-三个入口) |
| 任意 | 未匹配任何路由、无路由头 | fallback：`proxy_via_fallback()` | 返回 JSON 404 | [12 §4.2](12-spec-driven-server.md#42-两个补丁可选-body-与-json-404) |
| 任意 | `Host` 为 `{port}-{id}.{domain}`，路径不以 `/proxy` 开头 | 中间件 `sandbox_proxy_classifier()` 直接调 `proxy_request()` | 原样保留 | [17 §2](17-reverse-proxy.md#2-三个入口) |

路由头是 `x-agentenv-sandbox-id` / `x-agentenv-target-port`，E2B 别名 `e2b-sandbox-id` / `e2b-sandbox-port` 优先级较低。
Host 名入口在路由匹配之后运行，所以它会截走本来匹配到控制面路由的请求（[第 17 篇 §2](17-reverse-proxy.md#2-三个入口)）。

### 2.6 多节点时 gateway 对这些端点的处理

多节点部署里客户端先到 gateway。gateway 不实现上面的 handler，只决定把请求送到哪台节点，或者自己聚合（[第 55 篇 §3.2](55-gateway.md#32-六种路由来源)）：

| 端点 | gateway 的处理 | 篇目 |
|---|---|---|
| `GET /health` | 无路由头、非沙箱 Host 时本地返回 204 | [55](55-gateway.md) |
| `GET /metrics` | 公共监听上返回 404；gateway 指标在单独的监听上 | [55](55-gateway.md) |
| `GET /sandboxes`、`GET /v2/sandboxes` | 无路由头时并发请求所有节点并合并、重新分页 | [55 §7](55-gateway.md#7-gateway-本地聚合) |
| `GET /sandboxes/metrics` | 按 `LookupNode` 分组后分发 | [55 §7](55-gateway.md#7-gateway-本地聚合) |
| `GET /nodes` | 用 `ListObservedNodes` 本地拼出 | [55 §7](55-gateway.md#7-gateway-本地聚合) |
| `GET /nodes/{nodeID}` | `GetNode` 解析地址后转发 | [55 §7](55-gateway.md#7-gateway-本地聚合) |
| 带 `{id}` 的沙箱端点 | 路径取 ID，`LookupNode` | [55 §3.2](55-gateway.md#32-六种路由来源) |
| `PUT …/builder`、`POST /v2/templates/{t}/builds/{b}` | `Schedule` 分配节点 | [55 §3.2](55-gateway.md#32-六种路由来源) |
| `…/status`、`…/logs`、`GET` / `DELETE …/builder` | 以构建 ID `LookupNode`；status 与 logs 缺绑定时退回 `Schedule` | [55 §3.2](55-gateway.md#32-六种路由来源) |
| 创建沙箱与其余不带 ID 的管理端点 | `Schedule` 任选一台 | [55 §3.2](55-gateway.md#32-六种路由来源) |
| 数据面（Host 名、路由头、`/proxy`） | Host 转成路由头、改写成 `/proxy` 前缀后转发 | [55](55-gateway.md)、[17 §2](17-reverse-proxy.md#2-三个入口) |

---

## 3. AgentENV 调用的 Firecracker 端点

AgentENV 经 Firecracker 的 API socket（UDS）手写 REST 请求：包装方法都在 `src/sandbox/firecracker/instance.rs` 的 `FirecrackerInstance` 上，
底层是 `socket.rs` 的 `UnixSocketClient`，请求没有超时（[第 25 篇 §6](25-backend-and-firecracker-process.md#6-和-firecracker-说话手写的-uds-客户端)）。
调用位置除特别注明外都是 `src/sandbox/firecracker/sandbox.rs` 里 `FirecrackerSandbox` 的方法。「来源」一栏与[第 27 篇 §7](27-start-pause-resume-sequences.md#7-端点调用表)、[第 03 篇 §7](03-firecracker-for-agentenv.md#7-本书用到的-firecracker-端点)同一口径。

| 端点 | 包装方法 | 调用位置 | 来源 | 篇目 |
|---|---|---|---|---|
| `PUT /logger` | `set_logger()` | `configure_logger()`：配了 `firecracker.log_level` 时，冷启动与恢复都调 | 上游 | [27 §3](27-start-pause-resume-sequences.md#3-冷启动的配置序列) |
| `PUT /machine-config` | `set_machine_config()` | `configure_microvm()`（冷启动） | 上游 | [27 §3](27-start-pause-resume-sequences.md#3-冷启动的配置序列) |
| `PUT /cpu-config` | `set_cpu_config()` | `configure_microvm()`，有集群 CPU 配置时 | 上游 | [27 §3](27-start-pause-resume-sequences.md#3-冷启动的配置序列)、[57 §5](57-heartbeat-and-cpu-intersection.md#5-cpu-模板交集) |
| `PUT /boot-source` | `set_boot_source()` | `configure_microvm()` | 上游 | [27 §2.1](27-start-pause-resume-sequences.md#21-boot-args-的拼装) |
| `PUT /drives/{id}` | `add_drive()` | `configure_microvm()`（tools 盘、rootfs）、`configure_extra_drives()` | 上游；`direct` 字段为补丁新增 | [27 §3](27-start-pause-resume-sequences.md#3-冷启动的配置序列)、[26 §6.1](26-sandbox-block-devices.md#61-补丁做了什么) |
| `PATCH /drives/{id}`（路径） | `patch_drive_path()` | `start_resume()`：load 之后给新卷槽位换后端路径 | 上游 | [31 §4.3](31-extra-drives-and-volumes.md#43-新卷load-之后热插) |
| `PATCH /drives/{id}`（限流） | `patch_drive_rate_limiter()` | `start_resume()`：调和 rootfs 限流 | 上游 | [27 §4.2](27-start-pause-resume-sequences.md#42-load-与-load-之后) |
| `PUT /network-interfaces/eth0` | `add_network_interface()` | `configure_microvm()`；恢复时由 load 的 `network_overrides` 代替 | 上游 | [27 §3](27-start-pause-resume-sequences.md#3-冷启动的配置序列) |
| `PUT /mmds/config` | `set_mmds_config()` | `configure_microvm()` | 上游 | [28](28-mmds-and-envd.md) |
| `PUT /mmds` | `set_mmds()` | `configure_microvm()`、`start_resume()` | 上游 | [28](28-mmds-and-envd.md) |
| `PUT /balloon` | `set_balloon()` | `configure_microvm()` | 上游 | [27 §3](27-start-pause-resume-sequences.md#3-冷启动的配置序列) |
| `PUT /actions`（InstanceStart） | `start()` | `start_fresh()` | 上游 | [27 §3](27-start-pause-resume-sequences.md#3-冷启动的配置序列) |
| `PATCH /vm`（Paused） | `pause()` | `pause_to_dir()`、`snapshot_volumes()` | 上游 | [27 §5.1](27-start-pause-resume-sequences.md#51-序列) |
| `PATCH /vm`（Resumed） | `resume()` | `start_resume()`；capture 后由 `FirecrackerSandbox::resume()` 调用 | 上游 | [27 §4.2](27-start-pause-resume-sequences.md#42-load-与-load-之后)、[27 §6](27-start-pause-resume-sequences.md#6-capture-与-pause同一段代码四种收尾) |
| `PUT /snapshot/create` | `create_state_only_snapshot()` | `snapshot_memory_to_overlaybd()` | 上游；不带 `mem_file_path` 依赖补丁 | [27 §5.1](27-start-pause-resume-sequences.md#51-序列)、[03 §4](03-firecracker-for-agentenv.md#4-aenv-补丁版-firecracker-的四个被用到的行为) |
| `GET /vm/dirty-memory-ranges` | `get_dirty_memory_ranges()` | `snapshot_memory_to_overlaybd()` | 补丁新增 | [42 §2.2](42-memory-snapshot-over-ublk.md#22-dirtymemoryranges-的语义) |
| `PUT /snapshot/load`（File 后端） | `load_snapshot_file()` | `start_resume()` | 上游；内存文件为块设备时取大小靠补丁的 seek | [27 §4.2](27-start-pause-resume-sequences.md#42-load-与-load-之后)、[42 §4.1](42-memory-snapshot-over-ublk.md#41-取设备) |
| `PUT /snapshot/load`（Uffd 后端） | `load_snapshot_uffd()` | 无调用者，`#[allow(dead_code)]` 保留 | 上游 | [44](44-uffd-alternative.md)、[27 §8](27-start-pause-resume-sequences.md#8-遗留路径与技术债) |

补丁行为的实现与完整补丁清单在[第 67 篇](67-firecracker-patch-layer.md)。表中四处依赖补丁 —— drive `direct`、可选 `mem_file_path`、`dirty-memory-ranges`、seek 取内存文件大小 —— 与第 03 篇 §4 列出的四个行为一一对应。
`[memory_snapshot] track_dirty_pages` 关闭时 `GET /vm/dirty-memory-ranges` 照样被调用，差别只在 Firecracker 内部用 KVM dirty log 还是 `mincore`（[第 42 篇 §5](42-memory-snapshot-over-ublk.md#5-关闭脏页跟踪时)）。
`socket.rs` 测试里出现的 `GET /vm` 等请求只用于测试 `UnixSocketClient`，生产路径不调用。

---

## 4. ublk-daemon 的 14 种 RPC

协议定义在 `storage/ublk-daemon/src/protocol.rs`：每条消息是 4 字节大端长度加 JSON（上限 16 MiB），请求是以 `kind` 为标签的 `DaemonRequest`，响应是以 `status` 为标签的 `DaemonResponse`；
一个 UDS 连接只承载一个请求（[第 41 篇 §3.1](41-ublk-daemon.md#31-帧与连接)）。客户端是同一 crate 的 `client.rs` 里的 `UblkDaemonClient`，每个请求对应一个同名方法。

| 请求 `kind` | 成功响应 `status` | 作用 | 节点侧调用者 | 篇目 |
|---|---|---|---|---|
| `create_overlaybd` | `device_created` | 按给定 image.json 原样建设备，进 managed 表 | 录制用专用内存设备；块设备池关闭时的共享设备 | [41 §3.2](41-ublk-daemon.md#32-请求一览) |
| `create_overlaybd_runtime_device` | `overlaybd_runtime_device_created` | 物化运行时目录后建独占设备 | rootfs、附加盘 | [41 §5](41-ublk-daemon.md#5-运行时物化) |
| `delete` | `deleted` | 先中止录制，再拆 managed 表里的设备 | `delete_device()` | [41 §3.2](41-ublk-daemon.md#32-请求一览) |
| `acquire_overlaybd` | `device_acquired` | 按 `exclusive` / `shared` 从池中取设备 | 共享只读设备 | [41 §4.3](41-ublk-daemon.md#43-一台池化设备的流转) |
| `release_overlaybd` | `released` | 归还；shared 计数归零才回池 | `release_device()` | [41 §4.3](41-ublk-daemon.md#43-一台池化设备的流转)、[26 §4.3](26-sandbox-block-devices.md#43-daemon-一级activesharedrefcount) |
| `update_size` | `size_updated` | 在线改设备容量 | 无（只有 daemon 集成测试） | [41 §3.2](41-ublk-daemon.md#32-请求一览) |
| `get_features` | `features` | 返回启动时探测的特性位；池关闭时恒为 0 | 无（只有 daemon 集成测试） | [41 §3.2](41-ublk-daemon.md#32-请求一览) |
| `restack_snapshot` | `restack_snapshot_created` | 封存 upper、换上新 upper，返回层描述 | `restack_snapshot_device()` | [37](37-seal-restack-compact.md)、[41 §3.3](41-ublk-daemon.md#33-三类错误与超时) |
| `start_pack_recording` | `ok` | 开始首触页录制 | startup pack 录制 VM | [43 §2.3](43-startup-pack-and-prefetch.md#23-startuppackrecorder) |
| `pack_recording_status` | `pack_recording` | 查询录制状态 | 同上 | [43 §2.5](43-startup-pack-and-prefetch.md#25-节点侧的等待与收尾) |
| `abort_pack_recording` | `ok` | 中止录制 | 同上 | [43 §2.5](43-startup-pack-and-prefetch.md#25-节点侧的等待与收尾) |
| `prefetch_startup_pack` | `ok`（恒回） | 按 startup manifest 回填块缓存 | 对象存储来源的恢复 | [43 §4.2](43-startup-pack-and-prefetch.md#42-对象存储来源交给-daemon-回填块缓存) |
| `notify_sandbox_ready` | `ok` | 放开被 envd 就绪门挡住的后台下载 | envd 就绪后 | [39 §6.2](39-block-cache-and-background-download.md#62-envd-就绪信号) |
| `shutdown` | `ok`（客户端不看结果） | 请求 daemon 退出；客户端最多等回复 5 s，随后等进程退出 | `shutdown_daemon()` | [41 §2.2](41-ublk-daemon.md#22-何时退出) |

任何请求都可能得到三种错误响应：`terminal_error`（已改动 live 状态，设备不可安全继续用）、`invalid_request`（改参数可重试）、`error`（未改状态，可原样重试），
映射规则在 daemon 的 `handle_connection()`（[第 41 篇 §3.3](41-ublk-daemon.md#33-三类错误与超时)）。超时只在客户端：普通请求 30 s，`shutdown` 5 s，`restack_snapshot` 360 s，
`create_overlaybd_runtime_device` 取 360 s 与「扩容超时 + 120 s」的较大者；客户端超时不取消 daemon 内的处理。

ublk-daemon 另有一个 HTTP 监听：`storage/ublk-daemon/src/metrics_server.rs` 的 `spawn()` 在 `[ublk].daemon_metrics_listen_addr`（`config/default.toml` 为 `0.0.0.0:9103`）上用 `serve_metrics()` 暴露 Prometheus 指标，留空则不开，没有鉴权（[第 24 篇 §5.1](24-metrics-and-events.md#51-记录器与暴露位置)）。

---

## 5. scheduler 的 13 个 gRPC

`services/api/proto/scheduler.proto` 只定义一个服务 `scheduler.v1.Scheduler`。服务端实现是 `services/scheduler/internal/service.go` 的 `Service`；
query-only 角色用 `QueryOnlyService`，它只实现 `LookupNode`，其余方法落到生成的 `UnimplementedSchedulerServer`（[第 54 篇 §3.4](54-control-plane-overview.md#34-query-only-服务)）。
Go 生成名把 `P2p` 写成 `P2P`（`ListP2PPeers()`），线上的方法名仍是 proto 里的 `/scheduler.v1.Scheduler/ListP2pPeers`。
调用方一列沿用[第 54 篇 §3.1](54-control-plane-overview.md#31-分组)的核对结果；gateway 侧文件在 `services/gateway/internal/`，节点侧是 Rust 生成的 tonic 客户端。

| RPC | 调用方 | 调用点 | 落到 scheduler 的状态 | 篇目 |
|---|---|---|---|---|
| `Schedule` | gateway | `server.go` 的 `handleProxy()` | 发现列表 + 最近心跳快照 | [56 §2](56-scheduler.md#2-放置) |
| `ListNodes` | gateway | `cluster_list.go` 的 `handleClusterList()` | 发现列表，含下线中节点 | [55 §7.1](55-gateway.md#71-集群沙箱列表) |
| `LookupNode` | gateway | `server.go` 的 `handleProxy()`、`sandbox_metrics.go` 的 `handleSandboxMetricsList()` | 绑定表（内存或 Redis） | [56 §3](56-scheduler.md#3-绑定) |
| `RecordAssignment` | gateway | `server.go` 的 `recordAssignment()` | 绑定表 | [55 §6](55-gateway.md#6-写绑定)、[56 §3](56-scheduler.md#3-绑定) |
| `ListObservedNodes` | gateway | `node_list.go` 的 `handleNodeList()` | 观测记录，读取时推导状态 | [55 §7.2](55-gateway.md#72-节点列表与节点详情) |
| `GetNode` | gateway | `node_list.go` 的 `handleNodeDetail()` | 观测记录 | [55 §7.2](55-gateway.md#72-节点列表与节点详情) |
| `Heartbeat` | 节点 | `src/observability/reporter.rs` 的 `send_heartbeat()` | 观测记录、绑定表、CPU 交集 | [57 §3](57-heartbeat-and-cpu-intersection.md#3-心跳循环) |
| `ReportSandboxEvent` | 节点 | `reporter.rs` 的 `send_sandbox_events()` | 无：只打 debug 日志 | [54 §3.1](54-control-plane-overview.md#31-分组) |
| `UnregisterNode` | 节点 | `reporter.rs` 的 `unregister_node()`（由 `shutdown()` 调用） | 删观测记录、清该节点绑定与 P2P 索引 | [57 §4.1](57-heartbeat-and-cpu-intersection.md#41-unregisternode) |
| `ListP2pPeers` | 节点 | `src/p2p/discovery/scheduler.rs` 的 `list_scheduler_p2p_peers()` | 心跳里的 P2P 端点 | [58 §3.3](58-p2p-artifact-transport.md#33-lookup三级) |
| `LookupP2pArtifact` | 节点 | `scheduler.rs` 的 `peers_for_key()` | P2P 制品索引（仅 primary 内存） | [58 §3.5](58-p2p-artifact-transport.md#35-scheduler-侧的索引) |
| `RecordP2pArtifact` | 节点 | `scheduler.rs` 的 `record_key()` | P2P 制品索引 | [58 §3.5](58-p2p-artifact-transport.md#35-scheduler-侧的索引) |
| `ForgetP2pArtifact` | 节点 | `scheduler.rs` 的 `forget_key()` | P2P 制品索引 | [58 §3.5](58-p2p-artifact-transport.md#35-scheduler-侧的索引) |

gateway 用 6 个、节点用 7 个，两边没有交集；scheduler 从不主动调用任何一方。失败用四个 gRPC 状态码表达，gateway 的 `writeSchedulerError()` 把它们映射成 400 / 404 / 503 / 502（[第 54 篇 §3.3](54-control-plane-overview.md#33-错误码约定)）。
连接是明文、无认证的（[第 54 篇 §7](54-control-plane-overview.md#7-信任边界)）。

---

## 6. custom extension 的 4 个 hook

方向与节点 API 相反：节点是客户端，扩展服务是服务端。契约是 `src/custom_extension_api/openapi.yml`，生成的客户端在 `src/custom_extension_api/generated/`，
手写包装是 `src/sandbox/custom_extension/client.rs` 的 `CustomExtensionClient`。`[custom_extension].url` 为空时所有 hook 都跳过；四个 hook 共用 `timeout_ms`（缺省 5000）。

| 方法与路径 | operationId | 包装方法 | 调用时机 | 篇目 |
|---|---|---|---|---|
| `POST /sandbox-hook/start-fresh` | `sandboxStartFresh` | `hook_start_fresh()` | 冷启动：分配网络槽位之后、spawn Firecracker 之前；可返回 `extraBootArgs`；失败则启动失败 | [33 §3.1](33-custom-extension-hooks.md#31-start-fresh唯一能影响启动的-hook) |
| `POST /sandbox-hook/start-resume` | `sandboxStartResume` | `hook_start_resume()` | 恢复：网络槽位与 FC 进程就绪之后、加载快照之前；失败则恢复失败 | [33 §3.2](33-custom-extension-hooks.md#32-start-resume在快照加载之前) |
| `POST /sandbox-hook/patch-params` | `sandboxPatchParams` | `hook_patch_params()` | `PATCH /sandboxes/{id}/custom-extension-params`；失败返回 400，保留旧值 | [33 §5.3](33-custom-extension-hooks.md#53-patchhook-在锁外) |
| `POST /sandbox-hook/stop` | `sandboxStop` | `hook_stop()` | 运行时拆除：FC 停止之后、释放网络槽位之前；失败只记日志 | [33 §3.3](33-custom-extension-hooks.md#33-stop拆除序列中间的一步) |

四个 hook 的请求体与响应要点见[第 33 篇 §2](33-custom-extension-hooks.md#2-契约四个-hook)。snapshot 与 fork 的原地捕获不触发任何 hook；模板构建 VM 也会触发 start 与 stop hook。

---

## 7. P2P 门面的 3 个 HTTP 端点

P2P 打开时，`server` 进程在 `127.0.0.1` 的随机端口上起一个 HTTP 服务（`src/overlaybd/p2p/facade.rs` 的 `P2pHttpFacadeServer::start()`），它的调用方是 ublk-daemon 里的 Rust 版 overlaybd，不对外暴露。

| 方法 | 路径 | handler | 行为 | 篇目 |
|---|---|---|---|---|
| `GET` | `/p2p-http/{*origin}` | `handle_http_facade()` | 单段 Range 读；先查 P2P，拿到流之前失败则转 origin；拿到流之后出错不回退 | [58 §5.2](58-p2p-artifact-transport.md#52-一次范围读)、[58 §5.3](58-p2p-artifact-transport.md#53-中途出错为什么不回退) |
| `GET` | `/p2p-uuid/{uuid}` | `handle_uuid_facade()` | 只走 P2P；未命中 404，取数失败 502 | [58 §5.3](58-p2p-artifact-transport.md#53-中途出错为什么不回退) |
| `POST` | `/p2p-control/publish-layer` | `handle_publish_layer()` | 只接受回环地址，路径须在允许的发布根下，重算大小与 sha256 后发布 | [58 §5.3](58-p2p-artifact-transport.md#53-中途出错为什么不回退) |

第三个端点的地址被一路传进 ublk-daemon 的 `ImageService`，但 v0.2.3 中没有代码调用它。

---

## 8. 小结

- 节点 HTTP 路由由三部分 `merge` 而成：生成的控制面路由、`proxy::router()`（`/proxy` 两条加 fallback）与 BuildKit 隧道的一条 `GET`；`GET /metrics` 是唯一另外手写挂上的控制面路由。Host 名入口不是路由，而是中间件。
- 生成路由的 handler 都是 `impl <Trait><()> for ApiImpl` 的方法，按 `Sandboxes`、`Templates`、`Snapshots`、`Volumes`、`Admin`、`Default` 六个 trait 分在 `src/api/impls/` 的六个文件里。
- 按第 18 篇的四类：乙类五个（v2 创建、v2 connect、`PUT /network`、`GET /snapshots/{id}`、`GET /v2/templates`），丙类是冷启动、fork、扩展参数、builder 会话、`/metrics` 与全部代理入口，其余控制面端点为甲类。
- v1 与 v2 connect 是两个不同的 handler，只有 v2 允许缺省请求体。spec 里没有删除快照的端点。
- AgentENV 用到的 Firecracker 端点都经 `FirecrackerInstance` 的包装方法发出；其中四处依赖 AENV 补丁版 Firecracker，`load_snapshot_uffd()` 是没有调用者的遗留路径。
- ublk-daemon 的 14 种请求里 `update_size` 与 `get_features` 在节点侧没有调用者，`prefetch_startup_pack` 恒回 `ok`；超时只在客户端，且不取消 daemon 里的处理。
- scheduler 的 13 个 gRPC 按调用方严格分成两组：gateway 6 个（放置、绑定、观测查询），节点 7 个（心跳、事件、注销、P2P 四个）；`ReportSandboxEvent` 在服务端只打日志，query-only 服务只实现 `LookupNode`。
- 节点作为客户端调用扩展的 4 个 hook，除 stop 外失败都会让对应操作失败；P2P 门面的 3 个端点只服务本机的 ublk-daemon，其中 `publish-layer` 无人调用。

---

## 延伸阅读 / 下一篇

- [第 12 篇 · 规范驱动的服务骨架](12-spec-driven-server.md)：生成 trait、路由组装与中间件顺序。
- [第 18 篇 · E2B 兼容性：矩阵与偏差](18-e2b-compatibility.md)：四类端点的完整划分与丁类端点。
- [第 27 篇 · 启动、暂停与恢复的 Firecracker 调用序列](27-start-pause-resume-sequences.md)、[第 67 篇 · AENV 补丁版 Firecracker 与 guest 内核](67-firecracker-patch-layer.md)：Firecracker 端点的调用顺序与补丁实现。
- [第 41 篇 · ublk-daemon](41-ublk-daemon.md)、[第 54 篇 · 控制面总览与 proto 契约](54-control-plane-overview.md)：两套 RPC 的协议细节。
- [第 71 篇 · 配置项、环境变量与端口总表](71-config-env-ports-reference.md)：本篇各监听地址对应的配置键与端口。
- [第 73 篇 · 持久化制品与磁盘格式总表](73-artifacts-and-formats-reference.md)：接口之外的另一类契约。
- [Firecracker 手册第 08 篇](../firecracker/08-api-server.md)：上游 API server 怎样把 REST 请求变成 VMM 动作；[Firecracker 手册第 38 篇](../firecracker/38-snapshot-load.md)：上游 `PUT /snapshot/load` 的实现。
