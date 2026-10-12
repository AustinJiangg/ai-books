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
