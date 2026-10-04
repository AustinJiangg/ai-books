# A-api：API / 接入层与客户端工具 调研笔记

源：kvcache-ai/AgentENV v0.2.3（commit 6cccaa7），仓库根记为 `S/`。代码为准，docs 仅参考。
所有路径相对仓库根。"fn" 指函数/方法名；`ApiImpl::xxx` 表示 `impl <Trait> for ApiImpl` 中的方法。

---

## 0. 一页总览（写书前先记住的 10 个事实）

1. HTTP 服务 = **OpenAPI 生成的 axum 路由**（crate `agentenv_http_server`，`src/api/generated`）+ 手写 `ApiImpl` 实现 6 个 trait（Admin/Default/Sandboxes/Snapshots/Templates/Volumes）+ 手写 `/proxy` 反向代理 + 手写 BuildKit WebSocket 隧道 + `/metrics`。拼装在 `src/api/server.rs::new()`。
2. 认证只有**一把部署级 API Key**（`X-API-Key`，常量时间比较）。OpenAPI 里继承自 E2B 的 Bearer / X-Team-ID / X-Admin-Token 等 securityScheme **在实现中全部退化为"检查 X-API-Key"**（`impls/auth.rs` 的两个 adapter 忽略 `_key` 参数）。没有多租户/team 概念。
3. 真正的鉴权决策在外层中间件 `impls/auth.rs::require_auth()`：它先区分 control-plane 与 data-plane（proxy）请求，再对 data-plane 按 "envd 端口 + secure" / "应用端口 + allowPublicTraffic" 决策。
4. 两类沙箱凭据 `envdAccessToken`（头 `X-Access-Token`）与 `trafficAccessToken`（头 `e2b-traffic-access-token`）都是 **HMAC-SHA256(seed, subject) 无状态派生**（`src/sandbox/access.rs::SandboxAccessTokenGenerator`），不存库；subject 分别为 `"{sandbox_id}"` 和 `"sandbox-traffic-{sandbox_id}"`。
5. 反向代理三种入口：`/proxy[/*]` 前缀、**fallback（任意未匹配路径 + 路由头）**、Host 名 `{port}-{sandboxID}.{domain}`。路由头 `x-agentenv-sandbox-id`/`x-agentenv-target-port`，E2B 别名 `e2b-sandbox-id`/`e2b-sandbox-port`。
6. 代理对暂停沙箱可**自动恢复**（单次尝试，60s 超时，`NewTimeout::EnsureMinimum(300s)`）。
7. 模板 = 快照记录（`SnapshotRecord`，source=Template），**templateID == buildID == SnapshotId**（E2B 中两者不同，AgentENV "compatibility mode" 强制相等）。
8. 两条模板构建路径：E2B 风格 steps（`POST /v2/templates/{t}/builds/{b}`，仅支持 RUN/ENV/ARG/WORKDIR/USER/EXPOSE/VOLUME/LABEL，COPY/ADD/filesHash 显式 400）与 AgentENV 原生 Dockerfile/BuildKit 路径（`PUT .../builder` + `GET .../builder` WebSocket 隧道，客户端本地 `buildctl` 驱动远端 microVM 里的 buildkitd）。
9. custom extension = 外部 HTTP 服务的 4 个生命周期 hook（start-fresh/start-resume/patch-params/stop），客户端由 openapi-generator `rust` 生成；RAII `CustomExtensionHookGuard` 保证 stop 与 start 的 `sandboxInstanceId` 配对。
10. `aenv` CLI（~10k 行）同步 ureq 走控制面、reqwest 走 envd Connect-RPC（HTTP/1.1，经 fallback 代理），并内含 `aenv build`（BuildKit 隧道）和 `aenv codex`（远端执行的本地 Codex）。

---

## 1. 模块地图（行数 = `wc -l`，含测试）

### 1.1 服务端手写代码（src/api，合计 11,354 行）
| 文件 | 行数 | 职责 |
|---|---|---|
| `src/api/mod.rs` | 5 | 导出 `server`、`ApiImpl` |
| `src/api/server.rs` | 188 | `new()` 组装 Router + 中间件栈；`optional_connect_body()` 修补生成代码对空 body 的拒绝（含 2 个测试） |
| `src/api/proxy.rs` | 3198 | 反向代理（HTTP/SSE/WebSocket、Host 路由、自动恢复、头清洗）；**1203 行起为测试（41 个）**，正文约 1200 行 |
| `src/api/openapi.yml` | 2966 | 主 API 规范（OpenAPI 3.0.0，title "AgentENV API"，version 0.1.0；71 个 components/schemas+securitySchemes） |
| `src/api/impls/mod.rs` | 183 | `ApiImpl` 结构体、依赖注入、错误映射助手（`repository_error`、`internal_error`、`client_or_server_response`）、`/health` |
| `src/api/impls/auth.rs` | 164 | `require_auth()` 中间件、`ApiKeyAuthHeader`/`ApiAuthBasic` adapter、三个头常量 |
| `src/api/impls/sandbox.rs` | 2404 | Sandboxes trait 全部 handler（create/cold/fork/connect/pause/resume/snapshot/network/custom-ext/metrics/list）；2068 行起测试 |
| `src/api/impls/template.rs` | 1142 | Templates trait（v3 create、v2 build start、status/logs、alias、list、delete、builder PUT/DELETE 适配） |
| `src/api/impls/template_helpers.rs` | 300 | E2B steps → `TemplateBuildSpec`（`apply_e2b_template_step()`）、基础源解析 |
| `src/api/impls/image_build.rs` | 518 | Dockerfile/BuildKit 构建会话 `BuildSessions`/`BuildSession`/`SessionState`，`allocate_image_build()`、`run_image_build()` |
| `src/api/impls/image_build/transport.rs` | 266 | `GET /templates/{t}/builds/{b}/builder` WebSocket↔TCP 桥（`connect()`、`bridge()`），`MAX_TUNNEL_CONNECTIONS=8` |
| `src/api/impls/image_build/worker.rs` | 286 | builder microVM 准备（`builder_template()`、`initialize_builder_template()`、`prepare_builder()`、`START_BUILDKIT`/`STOP_BUILDKIT` 脚本） |
| `src/api/impls/image_build/cache.rs` | 154 | BuildKit 缓存卷 fork/发布/回收 |
| `src/api/impls/image_build/cleanup.rs` | 104 | 启动恢复 `recover_image_builds()` + 30s 周期清理 `start_image_build_cleanup()` |
| `src/api/impls/image_build/tests.rs` | 936 | 构建流程测试 |
| `src/api/impls/snapshots.rs` | 194 | Snapshots trait（list/get，仅 Sandbox 来源记录） |
| `src/api/impls/volumes.rs` | 314 | Volumes trait + `resolve_volume_mounts()`（预留/物化/路径重叠校验） |
| `src/api/impls/attached_drives.rs` | 368 | cold sandbox 附加盘解析/校验（sub_path、disk_size_mb） |
| `src/api/impls/pagination.rs` | 461 | `PaginationCursor<T>`：base64url(`RFC3339__value[__asc]`) 游标，内存排序分页 |
| `src/api/impls/admin.rs` | 169 | Admin trait：`/nodes`、`/nodes/{id}`（单节点视角） |

### 1.2 生成代码
| 目录 | .rs 行数 | 说明 |
|---|---|---|
| `src/api/generated/` (crate `agentenv_http_server`) | 20,539 | openapi-generator **7.22.0**，`-g rust-axum`；`models.rs` 11,188；`server/mod.rs` 7,012（路由+每个 op 的 handler 模板）；`types.rs` 790（`Nullable`、`Object`）；`apis/*.rs` trait 定义（sandboxes 619、templates 345、volumes 131、snapshots 73、admin 69、default 35）；`header.rs` 188 |
| `src/custom_extension_api/generated/` (crate `custom_extension_client`) | 621 | `-g rust`（reqwest 客户端），`apis/default_api.rs` 208 + 6 个 model |
| `src/custom_extension_api/openapi.yml` | 218 | hook 规范（AgentENV 调用外部服务） |
| `openapitools.json` | 7 | 锁 generator-cli 版本 7.22.0 |

生成流程：`make agentenv-server` → `cargo adev codegen server` → `adev/src/codegen.rs::run_server()`：npx `@openapitools/openapi-generator-cli generate -g rust-axum -i src/api/openapi.yml -o src/api/generated --additional-properties=packageName=agentenv_http_server,hideGenerationTimestamp=true` → **后处理 `fix_duplicate_auth_trait()`**（正则删除重复的 `ApiKeyAuthHeader` trait 块；因 spec 有多个 apiKey 型 scheme，生成器会重复输出该 trait；原为 Python 脚本 `fix_rust_axum_duplicate_auth_trait.py` 的 Rust 移植）→ `cargo fmt -p agentenv_http_server`。`make custom-extension-client` → `-g rust`。CONTRIBUTING.md:106 提示 custom extension 生成器不会删除孤儿 model 文件，需手动清理。Makefile:295 把 openapi.yml 软链到 `docs/src/openapi.yml` 供 Stoplight Elements 渲染（`docs/src/api/index.md` 只是一个 iframe）。

### 1.3 认证/身份相关
| 文件 | 行数 | 职责 |
|---|---|---|
| `src/api_key.rs` | 252 | `ApiKey`：解析顺序 env `AENV_API_KEY` → `/run/secrets/api-key` → `$AENV_HOME/secrets/api-key` → 自动生成 `e2b_`+64hex；`matches()` 用 `subtle::ConstantTimeEq` |
| `src/managed_secret.rs` | 273 | 托管密钥文件通用工具：0600/属主 uid/父目录 0700 校验、`tempfile`+`persist_noclobber` 原子创建、并发创建竞争处理（`CreateOutcome::{Created,Existing}`） |
| `src/sandbox/access.rs` | 422 | `SandboxAccessTokenGenerator`（HMAC-SHA256），`EnvdAccessToken`（Debug 脱敏），seed 解析 `load_or_create()` |
| `src/identity.rs` | 117 | `NodeIdentity`（node_id/cluster_id/service_instance_id/commit/version），供 `/nodes` 与可观测性 |

### 1.4 custom extension
| 文件 | 行数 | 职责 |
|---|---|---|
| `src/sandbox/custom_extension/mod.rs` | 10 | re-export |
| `src/sandbox/custom_extension/client.rs` | 814 | `CustomExtensionClient`（进程级单例 `GLOBAL_CLIENT: OnceLock`）、`CustomExtensionHookGuard`（RAII）、`SandboxInstanceId`（UUIDv7）；368 行起测试（内置一次性 HTTP server） |
| 调用点 | — | `src/sandbox/firecracker/sandbox.rs`：1887（start-fresh）、2129（start-resume，pack_recording VM 跳过）、1447（stop）、1702（Drop）；`src/orchestrator/service.rs:2030-2100` `patch_sandbox_custom_extension_params()` |

### 1.5 二进制（src/bin）
| 文件 | 行数 | 职责 |
|---|---|---|
| `src/bin/server.rs` | 270 | 节点进程 main：jemalloc（`malloc_conf` 1s decay）、`--setup-only`/`--setup-host`、能力检查、`ApiKey::resolve`、P2P/overlaybd/ublk 初始化、`FirecrackerPool::prime`、构造 `ApiImpl`、`recover_image_builds()`、监听 `API_ADDR`（默认 `0.0.0.0:8000`）且 **每连接 TCP_NODELAY**（注释：envd Connect-RPC 小帧 + Nagle = ~40ms 下限）、SIGTERM/Ctrl+C 优雅关闭顺序 |
| `src/bin/aenv-snapshot-image.rs` | 110 | 独立工具：把已提交快照的 rootfs 发布为普通 OCI 镜像，stdout 只打印镜像引用；不启动 KVM/ublk/网络；registry 认证交给 `regctl` 读取 docker config |

### 1.6 aenv CLI（crates/aenv，.rs 合计 10,077 行）
| 文件 | 行数 | 职责 |
|---|---|---|
| `src/main.rs` | 100 | clap 命令树；`install_crypto_provider()`（reqwest=aws-lc-rs 与 ureq=ring 并存，必须显式装 provider，否则 `wss://` BuildKit 隧道 panic） |
| `src/auth.rs` | 57 | 凭据 TOML（`url`,`api_key`）存于 `ProjectDirs("aenv").config_dir()/credentials`，0600 |
| `src/client/mod.rs` | 149 | `Client`：ureq（同步，connect 5s / request 120s）+ reqwest（异步）；所有控制面请求加 `X-API-Key`；`format_status_error()` 401 提示重新 `aenv auth` |
| `src/client/sandboxes.rs` | 259 | `create_sandbox()`→`POST /sandboxes`（**v1 已弃用端点，但显式 `secure:true`**）、`create_cold_sandbox()`、`list_sandboxes()`→`/v2/sandboxes`、connect/timeout/refresh/pause/delete |
| `src/client/templates.rs` | 171 | `/v2/templates`、`/templates/aliases/{a}`、`/v3/templates`、`/v2/templates/{t}/builds/{b}`、status 轮询 |
| `src/client/snapshots.rs` | 325 | 创建、分页遍历（limit=100，重复 token 防死循环、截止时间） |
| `src/client/volumes.rs` | 116 | volume CRUD、`validate_volume_reference()` |
| `src/client/files.rs` | 338 | `EnvdFilesClient`：经代理访问 envd HTTP 文件接口（upload/download/stat/list_dir/make_dir） |
| `src/client/buildkit.rs` | 262 | `bind_local()`（0700 临时目录下 unix socket）、`buildkit_tunnel()`（每个 buildctl 连接开一条 WS，上限 32 并发）、`bridge()` |
| `src/grpc/mod.rs` | 537 | envd Connect 协议客户端 `Transport`：HTTP/1.1-only，unary/server_stream/client_stream，envelope 编解码；头 `x-agentenv-sandbox-id`、`x-agentenv-target-port: 49983`、`Connect-Protocol-Version: 1`、可选 `X-Access-Token`；用户名走 Basic auth |
| `src/commands/*.rs` | — | auth 30、build 476、codex/{mod 115, guest 714, project 536, runtime 1013, socket 556, assets/Dockerfile 18}、completion 1062（动态补全）、connect 957（交互 PTY、重连/看门狗）、delete 16、download 642、exec 45、list 45、pause 16、pull 123、resume 19、snapshot 84、start 224、template 297、timeout 18、upload 375、volume 129 |
| `src/output.rs` / `progress.rs` / `pty.rs` | 47/142/23 | 表格/JSON 输出、进度条、终端尺寸与 raw mode |

### 1.7 相关但不在本区域（交叉引用）
- `services/gateway`（Go，约 6,088 行）：多节点网关，同名头常量（`server.go:26-33`，另有 `x-agentenv-node-id`），`schedule_hint.go`/`cluster_list.go` 对 `/sandboxes`、`/sandboxes-cold`、`/v2/sandboxes` 特殊处理。网关**不做沙箱鉴权**，只转发（proxy-design.md）。
- `thirdparty/envd`：fork 自 e2b-dev 的 envd（Connect-RPC，端口 `tools.control_plane_port = 49983`，`config/default.toml:65`）。
- e2e：`scripts/tests/e2e/suites/06_proxy.sh`、`08_auth.sh`、`09_e2b_compat.sh`（用官方 `e2b` CLI 跑 sandbox list/create 等）、`17_buildkit.sh`。

---

## 2. 分章要点

### 第 3.1 章 OpenAPI 代码生成与服务骨架

**问题**：要与 E2B SDK 线兼容（字段名、状态码、头），同时快速迭代；手写 axum 路由易与 spec 漂移。
**方案**：spec-first。`src/api/openapi.yml` 是唯一真相，生成 `agentenv_http_server` crate（trait + models + router），手写代码只实现 trait。

关键结构：
- 生成的 trait 形如 `apis::sandboxes::Sandboxes<E>`，每个 op 一个 async 方法，签名固定为 `(&self, method, host, cookies, claims, [path_params], [query_params], [body]) -> Result<XxxResponse, E>`；响应是**按状态码枚举**（如 `SandboxesSandboxIdPausePostResponse::Status204_TheSandboxWasPausedSuccessfullyAndCanBeResumed`、`Status409_Conflict(Error)`），带响应头的变体为 struct（如 `Status201_TheSandboxWasCreatedSuccessfully { body, x_agentenv_sandbox_id }`）。→ 书中可讲"用类型系统穷举状态码"的好处与冗长代价（sandbox.rs 中大量 `match err { ... => StatusXXX(...) }`）。
- 生成的 handler 模板（`generated/src/server/mod.rs`，例 `sandboxes_sandbox_id_pause_post` @2654）：①按 securitySchemes 调 `extract_claims_from_header(&headers, "X-Team-ID")` / `extract_claims_from_auth_header(Bearer, &headers, "authorization")`，`None.or(..).or(..)`，全无则 401；②`tokio::task::spawn_blocking` 做参数校验（validator crate）；③调用 trait；④对 JSON 序列化也用 `spawn_blocking`。
- `ApiImpl`（`impls/mod.rs`）字段：`orchestrator: Arc<Orchestrator>`、`snapshot_manager`、`template_builder`、`image_resolver`、`volume_manager`、`observability: Option<Arc<ObservabilityService>>`、`proxy_client: ProxyClient`、`sandbox_proxy_domains: Vec<String>`、`api_key: ApiKey`、`build_sessions: Arc<BuildSessions>`、`build_logs`。`Claims` 是空结构体（`pub struct Claims;`）——身份信息为零，仅表示"已通过"。
- 错误映射：`ApiImpl::repository_error()`（InvalidRequest→400；NotFound 系列→404；AliasConflict/VolumeNameConflict/IntegrityMismatch→409；Unsupported→500）；`impl From<OrchestratorError> for models::Error`（ShuttingDown→503，SandboxNotFound→404，InvalidSandboxState→400，SandboxOperationConflict→409，SandboxOperationFailed→500 并拼接 cause 链）；`internal_error()` 遍历 `source()` 链去重拼接消息。`bad_request_for_repository_build_error()` 在构建/发布语境下把 AliasConflict 视为 400 而不是 409（同一错误在不同端点映射不同）。

**Router 组装**（`server.rs::new()`），顺序很关键：
```
agentenv_http_server::server::new(api_impl)          // 生成的路由
  .route_layer(optional_connect_body)                // 仅作用于已匹配的生成路由
  .merge(proxy::router(api_impl))                    // /proxy, /proxy/{*}, .fallback(proxy_via_fallback)
  .merge(image_build::router(api_impl))              // GET /templates/{t}/builds/{b}/builder (WS)
  .route("/metrics", get(metrics_handler))           // Prometheus
  .layer(sandbox_proxy_classifier)                   // 内层：Host 路由改写+直接代理
  .layer(require_auth)                               // 中层：鉴权
  .layer(prometheus::http_metrics_middleware)        // 最外层：HTTP 指标
```
请求实际经过：metrics → auth → classifier → 路由/fallback。注释："Keep the generated control-plane API as the primary router, then merge in the hand-written `/proxy/*` entrypoints needed for the temporary reverse proxy contract"（"temporary" 字样值得在书中点出）。

`optional_connect_body()`：生成的 `Json<Option<ConnectSandboxV2>>` 接受 `null` 但拒绝空 body，而 v2 契约允许无 body。中间件只对 `MatchedPath == "/v2/sandboxes/{sandbox_id}/connect"` 的 POST 生效：空 body 时改写为 `"null"` 并补 `Content-Type: application/json`、`Content-Length: 4`、删 `Transfer-Encoding`。测试 `optional_connect_body_preserves_json_and_body_limits` 覆盖 8 种组合 + 413。→ 典型"生成代码与契约不符时用中间件打补丁"案例。

`/health` 返回 204（`impls/mod.rs::health_get`）。未匹配且无路由头的请求由 `proxy_via_fallback` 返回 JSON `Error{code:404,"route not found: METHOD path"}`（便于 JSON 客户端解析）。

**设计权衡**：
- 生成器 bug 用后处理正则修（`fix_duplicate_auth_trait`），对生成器版本脆弱（找不到块会 bail）。
- 安全方案在 spec 中按字母序命名（`AuthProviderBearerAuth` 在 `AuthProviderTeamAuth` 前、`AdminApiKeyAuth` 在 `AdminTeamAuth` 前，spec 注释说明是为了"Bearer 先于 Team 校验"），说明生成器按名字排序调用 extractor。
- spec 中 `x-api-group: list` 扩展字段（8 处）在 Rust/Go 代码中无消费者（可能供外部工具/网关未来使用）。

建议图：①生成管线流程图（openapi.yml → npx generator → 后处理 → fmt → crate）；②分层结构图（生成 trait / ApiImpl / Orchestrator 等下游）；③中间件洋葱图（metrics→auth→classifier→router/fallback）。

---

### 第 3.2 章 认证与凭据

**三层凭据**（docs/concepts/authentication 与代码一致）：
| 凭据 | 头 | 作用域 | 生成 | 校验点 |
|---|---|---|---|---|
| API Key | `X-API-Key` | 控制面全部 API（含 /nodes） | `src/api_key.rs::ApiKey::resolve()` | `ApiImpl::has_valid_api_key()`（`single_header` 要求恰好一个值）+ 生成 handler 的 adapter |
| envdAccessToken | `X-Access-Token` | 仅 secure 沙箱的 envd 端口 | `SandboxAccessTokenGenerator::generate(id)` = hex(HMAC(seed, id)) | `require_auth` → `orchestrator.validate_envd_access_token()` |
| trafficAccessToken | `e2b-traffic-access-token` | `allowPublicTraffic:false` 沙箱的非 envd 端口 | `generate_traffic(id)` = hex(HMAC(seed, "sandbox-traffic-"+id)) | `ApiImpl::has_valid_traffic_access_token()` |

**API Key 细节**（`api_key.rs`）：长度 32–256、字符 `[A-Za-z0-9._~-]`；文件最多 258 字节（允许 `\n`/`\r\n`）；外部密钥用 `O_NONBLOCK` 打开（防 FIFO 阻塞）且必须是普通文件，但允许 k8s 风格 symlink（测试 `external_secret_allows_kubernetes_style_symlinks`）；托管密钥目录 0700、文件 0600（`managed_secret.rs` 校验 mode==0600 且属主为有效 uid，否则拒绝启动）；`Debug` 输出 `ApiKey([REDACTED])`。网关只读前两个来源，不自动生成 → 多节点必须显式共享 key（docs）。

**access-token seed**（`access.rs::load_or_create(config, managed_seed_must_exist)`）：优先 `[sandbox].access_token_hash_seed`（env `AENV_SANDBOX_ACCESS_TOKEN_HASH_SEED`），否则 `$AENV_HOME/secrets/sandbox-access-token-hash-seed`（32 字节 = 64 位小写 hex）；若已存在"受 token 保护的持久化沙箱"而 seed 文件丢失 → 拒绝启动并提示恢复（避免静默轮换导致老沙箱永远不可访问）；配置了 `cluster.scheduler_endpoint` 但用节点本地 seed 时打 warn（集群各节点必须同 seed）。`matches_for()` 先 hex 解码到 32 字节缓冲，用 `Mac::verify_slice`（常量时间），并 `& decoded`（非短路）合并。

**中间件决策树** `impls/auth.rs::require_auth()`（书中最值得画的流程图）：
1. `proxy_request = proxy::is_sandbox_proxy_request(req, domains)`：路径以 `/proxy` 开头；或 Host 匹配 `{port}-{id}.{domain}`（解析错误也算 proxy）；或**无 MatchedPath 且带路由头**（`x-agentenv-sandbox-id`/`e2b-sandbox-id`）。
2. 非 proxy 且路径为 `/health`/`/metrics` → 放行。
3. 非 proxy（控制面）：必须有效 `X-API-Key`，否则 401；另外若路径参数含 `sandbox_id` 且对应沙箱 `metadata.template_builder == true` → **404**（隐藏内部 builder VM，不让用户 API 操作）。
4. proxy：`route_for_auth()` 解析 (sandbox_id, port)；解析不出 → 删 `x-access-token`，若是 `/proxy` 前缀或带 API key 则放行到 handler（handler 返回 400），否则 401。
5. 有 API key 则从请求中**删除 `x-api-key`**（不把平台密钥泄露给沙箱应用；不匹配的 X-API-Key 值原样转发给应用）。
6. 查 metadata：不存在→代理风格 404；template_builder→404。
7. `envd_request = target_port == effective_envd_port(metadata)`（暂停态记录的 control_plane_port 优先，否则全局 49983）。
8. envd 请求：`authorized = !secure || 有效 X-Access-Token`；非 envd：`authorized = allow_public_traffic || 有效 traffic token`。**X-API-Key 永远不是数据面凭据**。
9. 未授权 401；`envd_authorized` 为假时删除 `x-access-token`（只把验证过的 token 转给 envd）。traffic token 由 `proxy::sanitize_request_headers()` 剥离。

**生成层 adapter**：`impl ApiKeyAuthHeader for ApiImpl::extract_claims_from_header(&self, headers, _key)` 和 `impl ApiAuthBasic::extract_claims_from_auth_header(.., _kind, headers, _key)` 都只是 `has_valid_api_key(headers).then_some(Claims)`。注释："The outer middleware is authoritative. This adapter keeps the E2B-compatible generated router from rejecting its API-key request." 生成代码中 key 名统计：`X-Team-ID` 33 处、`X-API-Key` 4 处、`X-Admin-Token` 2 处（/nodes）——全部被忽略。即 `/nodes` 虽然 spec 声明 `AdminApiKeyAuth (X-Admin-Token)`，实际用 `X-API-Key`。

**响应中下发 token**：`ApiImpl::sandbox_model()`（sandbox.rs:451）：`traffic_access_token` 仅在 `!allow_public_traffic` 时 `Nullable::Present`，否则显式 `Null`；`envd_access_token` 仅 secure 时有；`domain` = `sandbox_proxy_domains[0]`（cfg.rs 注释 "domains[0] is the advertised sandbox response domain"）。`sandbox_detail_model()` 只下发 envd token。
**生命周期**：fork 子沙箱用子 id 重新派生（`orchestrator/service.rs:728` `source_metadata.secure.then(|| self.access_tokens.generate(child.sandbox_id))`）→ 独立凭据；pause/resume/重启不变（确定性派生）。

**权衡/已知限制**：无 per-sandbox 吊销（只能换 seed 全量轮换）；单 API key 无租户隔离、无 scope；非 secure 沙箱的 envd 端口对任何能到达 API 端口且知道 UUID 的人开放（UUID 作为唯一屏障）；v1 `POST /sandboxes` 默认 `secure=false`，v2 强制 true。

建议图：凭据关系图（API key / seed → 两类 token）；`require_auth` 决策流程图；一张"请求类型 × 所需凭据"表。

---

### 第 3.3 章 沙箱 API

**handler 一览**（全部在 `src/api/impls/sandbox.rs`，`impl Sandboxes<()> for ApiImpl`）：
- `sandboxes_post()`（v1 创建，warm 路径）：`snapshot_manager.load_runnable(template_id)`（模板/快照别名或 ID）→ `network_policy_from_create()` → `validate_custom_extension_params()`（非空 params 但未配置 `[custom_extension].url` → 400）→ 卷：若请求未给 `volumeMounts` 且快照含 `volume_snapshots`，则 `restore_snapshot_volume_mounts()` 恢复快照里的卷（`extra_drives_in_snapshot = true`）→ `prepare_volume_mounts()` 预留卷（pending owner）→ 构造 `CreateSandboxRequest{ source: SandboxLaunchSource::Snapshot, timeout, timeout_action: autoPause==false ? Delete : Pause, auto_resume, user_metadata, env_vars, network_policy, secure: body.secure==Some(true), custom_extension_params, volume_mounts }` → `orchestrator.create_sandbox()` → `finish_volume_reservation()` 把卷 owner 从 pending 改为 sandbox id；失败则删沙箱并回滚 owner、清理恢复出的卷。返回 201 + 头 `x-agentenv-sandbox-id`。全程 `SandboxStageTimer::new("create_warm")` 分阶段计时。
- `v2_sandboxes_post()`：把 `NewSandboxV2` 转为 `NewSandbox`，**强制 `secure: Some(true)`、timeout 默认 300**，委托 v1 并逐一映射响应枚举。注意 `mcp` 字段被拷贝进 `NewSandbox` 但 `sandboxes_post` 从未读取 → **mcp 参数被静默忽略**。
- `sandboxes_cold_post()`（AgentENV 原生 `/sandboxes-cold`）：`image_resolver.resolve(&body.image)`（可能拉取并转换 OCI 层，"tens of seconds"）→ `cold_start_resources()`（cpu/mem/diskSizeMB）→ `resolve_attached_drives()`（附加盘）→ 网络/扩展/卷 → `SandboxLaunchSource::Image{ image_ref, overlaybd_config_path, context, resources, extra_drives, extra_boot_args, image_configs }`。错误链中若含 `uvm_ublk_daemon::InvalidRequestError` 则转 400。TODO（:676）："Move cold-start image resolution into an async create operation once the API supports 202 Accepted + status polling."
- `sandboxes_sandbox_id_connect_post()`：Creating/Resuming/Running/Snapshotting/Forking → `keep_alive_for(id, timeout, false)`（只延长不缩短）返回 200；Killing → 404；Pausing/Paused → `resume_sandbox(id, NewTimeout::Set(t))` 返回 201。`v2_..._connect_post` 委托 v1，body 可省略（timeout 默认 300）。
- `sandboxes_sandbox_id_timeout_post()`：`keep_alive_for(id, t, true)`（覆盖 TTL，可缩短）；`..._refreshes_post()`：`keep_alive_for(id, duration, false)`（仅延长）。两者区别对应 E2B 语义。
- `..._pause_post()`、`..._resume_post()`（resume 未给 timeout 时用 `orchestrator.default_sandbox_timeout_secs`，**默认 15 秒**，`config/default.toml:210`——与 v2 的 300 不一致，值得一提）、`..._delete()`、`..._get()`（`SandboxDetail`）。
- `..._fork_post()`（AgentENV 原生）：count 1..=100；若源沙箱有卷，先 `orchestrator.snapshot_volume_mounts()` + `volume_manager.recover_backings()`，再 `prepare_volume_fork_specs()` 为每个子沙箱准备卷副本；`fork_sandbox_with_specs(id, child_specs, NewTimeout)`；返回 201 + `Vec<SandboxForkResult{sandbox|error}>`（部分成功语义，失败子沙箱的卷被 `cleanup_fork_volume_children()` 回收）。spec 描述：源沙箱"briefly paused, snapshotted with its full memory state, and resumed on its node, keeping its ID and expiration untouched"。
- `..._snapshots_post()`：`SnapshotAlias::parse(name)` → `orchestrator.capture_snapshot()` → `snapshot_sandbox_volumes()` → `snapshot_manager.publish_captured(SnapshotPublishMetadata{ id: SnapshotId::generate(), alias, source: Sandbox{source_sandbox_id}, context, startup, resources, runtime_versions, virtualization_mode, image_configs, volume_snapshots, custom_extension_params }, captured)` → 201 `SnapshotInfo`。
- `..._network_put()`：`network_policy_from_update()`（API 层传入占位 `allow_public_traffic=true`，但 `orchestrator/service.rs:1968` `replace_sandbox_network_policy_inner()` 用 `metadata.network_policy.allow_public_traffic` 覆盖回原值 → PUT network 只改 egress，不会改变 private/public ingress）→ `replace_sandbox_network_policy()`。校验：`validate_ipv4_cidrs()` 拒绝 IPv6；`validate_domain_allowlist()` 要求 allowOut 含域名时 denyOut 必须包含 `ALL_INTERNET_TRAFFIC_CIDR`（注释：E2B 的域名检查只对 TCP 80/443 生效）。
- `..._custom_extension_params_get()/patch()`：见 3.x custom extension 章节；patch 中 extension 拒绝 → 400。
- `sandboxes_metrics_get()`（CSV ids，最新样本，缺失者省略）、`..._metrics_get()`（start/end 闭区间，节点本地、有界、重启丢失）。
- `sandboxes_get()`（v1，仅 Running，`metadata` 查询为 urlencoded `k=v&k2=v2`，`parse_metadata_filter()`）、`v2_sandboxes_get()`：state 只给 1 个才过滤（多个视为不过滤，注释说明只有两种外部状态）；`order` asc/desc；`startedAfter`、`template`；`nextToken` 游标且校验排序方向一致；响应头 `x-next-token`、`x-total-running`。

**状态映射**（对外只有 running/paused）：`impl From<SandboxState> for models::SandboxState`：Pausing/Paused/Snapshotting/Forking → Paused，其余 → Running。`end_at()` 对无过期沙箱返回 "100 年后"。`client_id: ""` 注释 "Deprecated field, only reserved for E2B Python SDK"。

**分页**（`pagination.rs`）：游标 = base64url(`{RFC3339}__{id}` 或 `..__asc`)，与 E2B token 形态兼容；`paginate()` 对全量列表内存排序后切片（按 created_at, id 比较）→ 非流式，大规模下 O(N log N) 每页。

建议图：创建沙箱时序图（API → SnapshotManager → VolumeManager 预留 → Orchestrator.create → 完成预留/回滚）；connect 状态分支图；fork 部分成功结果示意。

---

### 第 3.4 章 模板 / 快照 / 卷 API

**模板 = 快照记录**：`SnapshotRecord.source = SnapshotSource::Template{..}`；`ApiImpl::build_record(template, build)`（template.rs:314）要求 `template == build`，否则 404 "build not found for template"。

E2B 风格模板流程（v3 + v2）：
1. `v3_templates_post()`：必须有 name；`SnapshotId::generate()`；`template_build_record_from_v3_request()` → `snapshot_manager.create(record)`（状态 Waiting）；返回 202 `TemplateRequestResponseV3(templateID=buildID=id, public=true, aliases=[name], tags=[], names=[name])`。
2. `v2_templates_template_id_builds_build_id_post()`：校验 id 相等（"templateID and buildID must match in AgentENV compatibility mode"）；`template_build_start_base_source()`（fromImage / fromTemplate 二选一，均无则 DefaultImage）；`template_build_spec_from_start_request()`（startCmd/readyCmd + steps → `apply_e2b_template_step()`，`stamp_source_steps()` 记录客户端步骤号，用于错误定位）；`snapshot_manager.try_start_build()`（仓库 CAS，防重复/跨节点并发启动）；`build_logs.start()`；`orchestrator.register_template_build(sandbox_id)`（构建用 VM 标记为 template_builder，对用户 API 隐藏）；`tokio::spawn` 后台构建，失败 `mark_v2_build_error()`。
3. 轮询 `templates_template_id_builds_build_id_status_get()`：附带日志（offset/limit≤100/level），失败 reason 带 step 时附带该 step 的 ≥Warn 日志（`query_build_reason_logs()`）；若 BuildKit 会话 "starting" 强制报 Waiting，"finishing" 时把 Ready 报为 Building（注释："A sequential CLI build must observe the newly published cache seed."）。
4. `..._logs_get()`：`query_build_logs()` 支持 cursor(ms)/direction(backward)/level/source（temporary 内存 vs persistent 仓库）。
- 支持的 steps：RUN、ENV/ARG（ARG 当 ENV 处理！）、WORKDIR、USER、EXPOSE、VOLUME、LABEL；`COPY`/`ADD` → 400 "not supported yet"；`filesHash` 非空 → 400 "filesHash/COPY support is not implemented yet"。→ E2B SDK 的 `copy()` 不可用，是兼容性缺口。
- `templates_aliases_alias_get()` → `resolve_committed_alias()`，返回 `TemplateAliasResponse(id, public=false)`。
- `templates_template_id_delete()`：活跃构建会话 → 409；不存在 → 204（幂等）。
- `templates_get()`（全量）、`v2_templates_get()`（分页）、`templates_template_id_get()`。

**Dockerfile/BuildKit 路径**（AgentENV 原生，`image_build*.rs`）：
- `PUT /templates/{t}/builds/{b}/builder` → `start_image_build()` → `BuildSessions::reserve()`（409 已开始；超过 `template_build.max_concurrent_builds`（默认 4，cfg 测试）→ **429**）→ `allocate_image_build()`：校验 `cache_size_mb <= volume.max_size_mb`、状态 Waiting、`try_start_build()` CAS（注释 "also excludes starts on another node or through the legacy API"）、持久化 `BuildJournal{cache:"aenv-buildkit-work-{id}"}` 到 `LocalKvStore`（崩溃恢复用）、注册 template build、spawn `run_image_build()`；返回 202 + `TemplateBuilder{imageName}` + 头 `x-agentenv-build-id`。
- `run_image_build()`：`wait_for_image_build()`（统一 deadline 与取消）→ `builder_template()`（`OnceCell` 进程内共享；按 `(版本1, builder_image, cpu, mem, BUILDER_READY, virtualization_mode)` 的 SHA256 作 alias `builder-{hex}`，多节点并发首建遇 AliasConflict 则复用）→ `prepare_builder()`（fork 缓存卷挂到 `/var/lib/buildkit`）→ `START_BUILDKIT` → `BuildkitHistory::wait_for_image()` 等待客户端 solve 完成得到 digest → `BuildkitContent` 拉内容 → `image_resolver.resolve_buildkit()` 转 overlaybd → `release_builder()` → `template_builder.build_and_publish_with_id()`（用同一 id 发布模板）→ 可选 `publish_build_cache()`。`supervise_image_build()` 用 `catch_unwind` 兜 panic；`finish_image_build()` 置 `SessionState::Finished(reason)` 并清理。
- `GET /templates/{t}/builds/{b}/builder`（**不在 openapi.yml 中**，手写 `transport.rs::connect()`）：仅 `SessionState::Ready(addr)` 时允许；连接数信号量（`try_read_owned`，上限 8，"never queue waiters"，超限 429）；10s TCP 连接超时（504/502）；WS 帧/消息上限 1MiB；`bridge()` 二进制帧↔TCP，20s ping；会话 Cancelled/Finished 时主动断开（注释："Stopping a VM need not close its host TCP sockets"）。鉴权走 `require_auth` 控制面分支（需 X-API-Key）。
- `DELETE .../builder` → `cancel_image_build()`。
- 恢复：`recover_image_builds()` 扫描 journal 前缀 `build/`，逐个 `retry_image_build_cleanup()`，不让单个失败阻塞其他；`start_image_build_cleanup()` 每 30s 重试（Weak 引用，ApiImpl 释放即退出）。

**快照 API**（`snapshots.rs`）：`snapshots_get()` 只列 `SnapshotListFilter::sandbox_snapshots(sandbox_id, name)`，仅降序游标；`snapshots_snapshot_id_get()` 对 Template 来源记录返回 404（注释：模板记录走模板 API）。`SnapshotInfo` 可含已发布 rootfs `image_ref`（与 `aenv-snapshot-image` 呼应）。

**卷 API**（`volumes.rs`）：`volumes_post()` mode `exclusive`（默认）/`ro`，可 `fromVolume` 克隆或 `image` 初始化（经 image_resolver），size 默认 `DEFAULT_VOLUME_SIZE_MB`；`resolve_volume_mounts()`：数量上限 `max_volume_count`、路径 normalize 后**前缀重叠拒绝**、单卷大小上限、同卷重复挂载拒绝、`reserve(volume, owner)` → `materialize_backing()` → 生成 `ExtraDrive`；失败统一 `replace_owner_for(owner, None, reserved)` 回滚。E2B docs：TS SDK 的 volume create/list/delete 可用，"direct volume content API is not supported"。

建议图：模板记录状态机（Waiting→Building→Ready/Error）；E2B steps 构建时序；BuildKit 隧道拓扑图（本地 buildctl → unix socket → aenv WS → API → TCP → builder microVM 内 buildkitd）；卷预留/owner 转移时序。

---

### 第 3.5 章 反向代理（`src/api/proxy.rs`）

**入口**（`proxy::router()`）：`ANY /proxy`、`ANY /proxy/{*proxy_path}` → `proxy_via_prefix()`（剥 `/proxy` 前缀，`strip_proxy_prefix`）；`.fallback(proxy_via_fallback)`（有路由头才代理，保留原路径；注释：镜像分布式网关的 header 分发，使 `E2B_SANDBOX_URL=${E2B_API_URL}` 在单机与多节点一致）；Host 路由在中间件 `sandbox_proxy_classifier()` 中完成：`parse_host_proxy_route()` 解析 `{port}-{uuid}.{domain}`（小写、去尾点、去 `:port`、label 不得含点、域名本身视为控制面），成功后**把解析结果写入 `x-agentenv-sandbox-id`/`x-agentenv-target-port` 头**，在中间件内手动 `WebSocketUpgrade::from_request_parts()` 后直接调用 `proxy_request()`（因此 Host 路由优先于 axum 路由匹配——路径像控制面 API 也会被代理）。三种来源以 `HttpRouteSource::{ProxyPrefix, ProxyHeader, ProxyHost}` 写入 response extension 供 Prometheus 打标签。

**路由头**：`SANDBOX_ID_HEADER="x-agentenv-sandbox-id"`、`E2B_SANDBOX_ID_HEADER="e2b-sandbox-id"`、`TARGET_PORT_HEADER="x-agentenv-target-port"`、`E2B_TARGET_PORT_HEADER="e2b-sandbox-port"`；`first_header_value()` AgentENV 头优先；端口须 u16>0；id 须 UUID。

**解析**（`resolve_proxy_request()`）：循环调 `orchestrator.proxy_lookup_for()`（运行时路由表 `proxy_routes` 读锁，不碰沙箱 mutex）→ `ProxyLookupResult::{Ready(target), NotFound, Paused{auto_resume}, Unavailable(state), RouteMissing}`；`Paused{auto_resume:true}` → `try_auto_resume()`（`timeout(60s, resume_sandbox(id, NewTimeout::EnsureMinimum(auto_resume_min_sandbox_timeout)))`，默认 300s）后再循环一次，第二次仍不行 → `AutoResumeFailed`。上游 URI = `http|ws://{target.ip}:{port}{path}?{query}`（直连沙箱 host interaction IP）。

**HTTP 转发**（`proxy_http_request()`）：`sanitize_request_headers()` 删 4 个路由头、`e2b-traffic-access-token`、Host、hop-by-hop（含 Connection 提名的头、keep-alive）；`inject_forwarded_headers()` 加 `x-forwarded-host/proto/method/uri`；Host 改为上游 authority。超时模型 `wait_for_upstream_response_headers_with_activity_timeout()`：请求体上传阶段为**空闲超时 30s（每个 data frame 重置）**，上传结束后切换为**响应头超时 30s**（`track_request_body_activity()` 用 `watch` 通道；sender 随 body drop 而关闭作为"上传结束"信号）；响应体流式透传（SSE/大文件）。envd `POST /process.Process/StreamInput`（长期 client-streaming attach）特殊日志 "client attached/detached"，`is_benign_stream_input_disconnect()` 通过错误字符串 `"client error (SendRequest)"` 识别（注释：hyper-util 的 ErrorKind 私有，只能比字符串）。
**连接池**：`build_proxy_client()`：`set_nodelay(true)`、connect 5s、**`pool_max_idle_per_host(0)` 禁用连接复用**（注释："Interaction IPs are reused across sandbox runtime generations… a pooled connection can retain a stale VM flow."）。

**WebSocket**（`proxy_websocket_request()`）：`is_websocket_upgrade_request()`（Connection 含 upgrade 且 Upgrade 含 websocket）；删 `sec-websocket-*` 再用 tokio-tungstenite `connect_async` 与上游握手（30s 超时→504）；上游 HTTP 拒绝 → 状态与 body 原样返回（`map_websocket_handshake_rejection_response`）；传播上游选中的 subprotocol；101 响应附加上游非握手头（X-Request-Id、Set-Cookie 等）；`bridge_websocket_streams()` 双向帧转换（`axum_message_to_tungstenite`/`tungstenite_message_to_axum`）。

**错误映射**（`proxy_error_response()`，text/plain）：400（缺/坏路由头、坏 Host、坏 URI）、404 sandbox not found、410 Gone（不可代理状态/暂停且未开 auto-resume）、502（auto-resume 失败、RouteMissing、上游失败）、504（auto-resume 超时、响应头/握手超时）、500 无 body。

**测试**：41 个（HTTP、SSE、大 body、WS、头、路径保留 `//api`、错误映射、鉴权组合），约 2000 行。

**设计权衡**：每请求一次 TCP 连接 vs 陈旧流；auto-resume 把冷启动延迟藏进首个请求（客户端须容忍最长 60s）；单次 resume 尝试避免风暴；Host 路由要求通配 DNS + 网关；`effective_envd_port()` 读暂停态记录的端口以兼容端口配置变更。

建议图：三入口汇聚图；`resolve_proxy_request` 状态机（含 auto-resume 环）；上传空闲/响应头双阶段超时时序图；WS 握手-桥接时序图；头清洗前后对比表。

---

### 第 3.6 章 E2B 兼容层

**兼容手段清单（代码证据）**：
- 路径与 schema 直接沿用 E2B OpenAPI 形态（`/sandboxes`、`/v2/sandboxes`、`/v3/templates`、`/v2/templates/{t}/builds/{b}`、`/templates/aliases/{alias}`、`/nodes`…），字段名 `sandboxID`/`templateID`/`envdVersion`/`clientID`/`envdAccessToken`/`trafficAccessToken`/`domain`。
- 安全方案保留 E2B 的 `ApiKeyAuth`/`AuthProviderBearerAuth+AuthProviderTeamAuth`/`AdminApiKeyAuth+AdminTeamAuth`，但实现只认 `X-API-Key`（见 3.2）。
- 生成的 API key 前缀 `e2b_`（`GENERATED_API_KEY_PREFIX`），docs 称 "E2B-compatible key"，SDK 用 `E2B_API_KEY`。
- 代理头别名 `e2b-sandbox-id`/`e2b-sandbox-port`、traffic token 头 `e2b-traffic-access-token`、envd 头 `X-Access-Token`、envd 端口 49983、Host 形态 `{port}-{sandboxID}.{domain}`、`domain` 字段回传。
- fallback 代理使 `E2B_SANDBOX_URL=${E2B_API_URL}` 可用（E2B SDK 默认对数据面另起 host；AgentENV 让 SDK 直接打 API 端口 + 头）。
- `client_id: ""` 仅为 E2B Python SDK 保留；`ListedSandbox`/`SandboxDetail` 同理。
- 分页 `x-next-token` 游标、`x-total-running` 头。
- `refreshes`（只延长）与 `timeout`（覆盖）语义区分；v1/v2 connect；`autoPause`/`autoResume`。
- 网络策略 `allowOut`/`denyOut`/`allowInternetAccess`/`allowPublicTraffic`，域名规则须配合 ALL_TRAFFIC deny（与 E2B 行为一致的注释）。
- 模板 "AgentENV compatibility mode"：templateID==buildID。
- envd 本身是 E2B envd 的 fork（`thirdparty/envd`），SDK 的 commands/files 走同一协议。
- e2e `09_e2b_compat.sh` 用官方 `e2b` CLI 验证。

**兼容缺口 / 偏差**（写 "兼容性矩阵" 用）：
- 无 team/多租户/access token（Bearer）语义；`teamID` 查询参数不起作用；X-Admin-Token 不生效。
- 模板 steps 不支持 COPY/ADD/filesHash → SDK `Template().copy()` 不可用；ARG 被当作 ENV。
- `mcp` 字段接收但忽略。
- E2B 直接卷内容 API 不支持（docs）。
- sandbox ID 为 UUID（E2B 原生为短 ID），SDK 不受影响但用户可见。
- 对外状态只有 running/paused（内部 Snapshotting/Forking/Pausing 被折叠）。
- v1 默认 non-secure，v2 强制 secure。
- AgentENV 扩展（E2B SDK 不会调用）：`/sandboxes-cold`、`/fork`、`/custom-extension-params`、`.../builder`（PUT/DELETE/GET-WS）、`/proxy*`、`/metrics`、`x-agentenv-*` 头。

（注：上述"是否为 E2B 上游端点"的划分基于对 E2B 公开 OpenAPI 的了解，`/sandboxes/{id}/network`、`/snapshots/{id}`、`/v2/sandboxes/{id}/connect`、`/volumes` 等较新端点建议写作时与 e2b-dev/infra 的 spec 再核对一次。）

建议图：E2B SDK → AgentENV 的请求映射图（控制面 vs 数据面）；兼容矩阵表。

---

### 第 3.7 章 节点 / Admin API（体量小）

- `GET /nodes`（`admin.rs::nodes_get`）：observability 关闭 → `[]`；`clusterID` 不匹配 → `[]`；否则单元素 `[Node::from(observability.node_snapshot())]`。即**每个节点只报告自己**；集群视图由网关/scheduler 聚合（`services/gateway/internal/cluster_list.go`、metrics.go 对 `/nodes` 特殊处理）。
- `GET /nodes/{nodeID}`：observability 关闭 → 404 "observability is disabled on this node"；node_id/cluster 不匹配 → 404；返回 `NodeDetail(cluster_id, version, commit, node_id, service_instance_id, machine_info, NodeStatusReady(恒定), sandbox_count, metrics, create_successes, create_fails, paused_sandbox_count)`。
- 身份来源 `identity.rs::NodeIdentity::from_config()`：node_id = 配置或 hostname（HOSTNAME → /proc/sys/kernel/hostname → /etc/hostname）；cluster_id 解析失败 warn 并用 nil UUID；service_instance_id 缺省 UUIDv7（每进程变化）；commit 编译期 `option_env!("AENV_GIT_COMMIT")`（测试保证运行时 env 不能覆盖）。
- spec 写 `AdminApiKeyAuth (X-Admin-Token)`，实际 X-API-Key。状态恒为 Ready（无 draining/unhealthy）。
- `/metrics`（Prometheus，`agentenv_observability::metrics_handler`）与 `/health` 免鉴权。

→ 建议并入其他章（见第 5 节）。

---

### 第 X 章（orchestrator 部分）custom extension 生命周期 hook

**问题**：让外部系统（如网络/计费/sidecar 控制器）在沙箱生命周期关键点介入，且 sandbox id 在 pause/resume 间复用、stop 通知可能乱序。
**接口**（`src/custom_extension_api/openapi.yml`，AgentENV 作为客户端）：
| hook | 时机 | 失败语义 | 请求 | 响应 |
|---|---|---|---|---|
| `POST /sandbox-hook/start-fresh` | 网络槽分配后、microVM 配置前（`firecracker/sandbox.rs:1887`，ip boot arg 之后） | 失败 → 创建失败 | sandboxId, sandboxInstanceId, networkNamespacePath, hostInteractionIp, customExtensionParams | `extraBootArgs`（追加到内核命令行，在 `add_damon_monitor_region` 之前） |
| `POST /sandbox-hook/start-resume` | 从快照恢复、网络槽就绪后（:2129；`pack_recording` VM 不触发） | 失败 → resume 失败 | 同上 | — |
| `POST /sandbox-hook/patch-params` | 用户 `PATCH /sandboxes/{id}/custom-extension-params` | 失败 → 400，保持旧值 | sandboxId, patch（原样透传） | 新的完整 params |
| `POST /sandbox-hook/stop` | VM 进程停止后、释放网络槽前（:1447）；含 pause；Drop 时 fire-and-forget | best-effort，只记日志 | sandboxId, sandboxInstanceId | — |
- 快照捕获中的原地 pause+resume **不触发 stop、不换 instance id**。
- 配置：`[custom_extension].url`（env `AENV_CUSTOM_EXTENSION_URL`），`timeout_ms` 默认 5000；未配置则所有 hook 跳过；`CustomExtensionClient::global()` 惰性构建（reqwest client 构建失败则禁用并 warn）。
- `CustomExtensionHookGuard`：`start_fresh()`/`start_resume()` **在发送前先记录新的 `SandboxInstanceId`（UUIDv7）**，这样"请求已被处理但响应超时"的情况下 teardown 仍发出匹配的 stop；extension 未处理过的 start 会忽略该 stop（非最新实例）。`stop(self)` 同步 await；`Drop` 若仍持有 instance id，则 `Handle::try_current()` spawn 异步 stop（无 runtime 时 warn 跳过）。`FirecrackerSandbox::drop` 中 `self.custom_extension_hook_guard.take()` 即触发。
- patch 流程（`orchestrator/service.rs::patch_sandbox_custom_extension_params`）：仅 Running；**不持沙箱锁调用 hook**（避免 pause/stop 被 extension 延迟阻塞）；之后锁内 `update_custom_extension_params()`，再 `store.update_if_state(Running)`；与并发 pause 竞争时返回 InvalidSandboxState（→409），注释承认 "acceptable since extension state should be transient like network policy"。**运行时不串行化同一沙箱的并发 patch**（spec 明说由 extension 自理）。
- params 是不透明 JSON object；`None` 与 `{}` 等价（`custom_extension_params_is_empty()`）；随快照持久化（`SnapshotPublishMetadata.custom_extension_params`），resume/从快照创建时带回。创建时非空 params + 未配置 extension → 400。
- AGENTS.md 规则摘要："Start/patch failures fail the operation; stop is best-effort, including pause. Pair start/stop with a per-runtime sandboxInstanceId. Forward patches verbatim, store returned full params, and preserve them across snapshots/resume."
- 测试（client.rs:483 起）：start_fresh 返回 boot args、空 params 发 `{}`、非 2xx 失败、guard stop 只发一次、失败的 start 仍在 drop 时发匹配 stop 等。

建议图：sandbox 生命周期时间线上的 4 个 hook 位置；乱序 stop 与 instance id 判定时序图；RAII guard 状态图（None → Some(id) → stop/Drop）。

---

### 第 9.x 章 aenv CLI

**架构**：同步 `ureq` 处理控制面 REST（`Client::get/post/delete` 统一加 `X-API-Key`）；`reqwest` 处理异步/流式（envd、BuildKit、build_request）；每个命令自建 current-thread tokio runtime（`commands::tokio_rt()`）。凭据：`aenv auth`（`rpassword` 隐藏输入）写 `~/.config/aenv/credentials`（TOML，0600）。
**命令**：auth、codex(setup/start/resume/finish|recover)、pull、build、start、exec、upload、download、completion(隐藏)、connect(cn)、pause、resume、list(ls)、delete(rm)、timeout、snapshot(snap)、template(templates: list/delete/watch)、volume。`resolve_template()`：UUID 直用，否则 `/templates/aliases/{a}`。`DEFAULT_TIMEOUT_SECS=300`。
**envd 数据面**（`grpc/mod.rs`）：模块注释说明选 Connect 而非 gRPC 的原因——原生 gRPC 需要 proxy↔envd 的 HTTP/2，现有代理不支持；Connect unary=POST、server-streaming=单请求+分块 envelope（flag 0x00 data / 0x02 end），HTTP/1.1 直通；不加 `/proxy` 前缀，靠 fallback 路由。客户端：`http1_only`、禁重定向、`pool_max_idle_per_host(0)`、TCP keepalive 3s/1s/2 次、Linux `tcp_user_timeout 3s`、本地地址绕过系统代理（`bypass_proxy_for_base_url`）。测试保证 envd 请求**不带 x-api-key**。
**connect/start**（`commands/connect.rs::attach()`）：先 `POST /sandboxes/{id}/connect`（取 envd token、必要时恢复），`Process/Start` 起 PTY，shell 探测脚本 `INTERACTIVE_SHELL_DISPATCHER`（bash→sh→`/agentenv/bin/busybox sh`）；`StreamInput` client-stream 每 10s keepalive（注释对齐代理 `PROXY_REQUEST_BODY_IDLE_TIMEOUT` 30s）；输出流断开自动重连、看门狗、暂停探测（退出码 130 表示沙箱被暂停）、每 60s 有活动才 `refreshes` 续期。大量毫秒级常量（OUTPUT_IDLE_TIMEOUT 500ms 等）可作为"交互式远程终端的鲁棒性工程"案例。
**start**：`--cold` 走 `/sandboxes-cold`，`--disk-size-mb` 必须能被 1024 整除，`--volume MOUNT=VOL` 可重复（本地也校验重叠），`-d` 只打印 ID；测试 `secure_flag_is_not_accepted`（CLI 不暴露 secure 开关，恒为 secure）。
**build**（`commands/build.rs`）：`POST /v3/templates` → `PUT .../builder`（timeout/startCmd/readyCmd）→ 轮询 status 至 building → `bind_local()` 建 unix socket → 并发运行本地 `buildctl --addr unix://… build --frontend dockerfile.v0 --local context=… --local dockerfile=… --output type=image,name={imageName},oci-mediatypes=true`（支持 --build-arg、--secret、--no-cache、--progress）与 `buildkit_tunnel()`（每个 buildctl 连接一条 `ws(s)://…/builder` WS，带 X-API-Key）→ 等 ready；失败/Ctrl-C/超时（timeout+600s）时 5s 内 `DELETE .../builder` 清理。**秘密与上下文从不上传到 API 服务的 HTTP body，而是经隧道直达 builder 内 buildkitd**。
**pull**：从基础镜像建模板（`probe_ready_cmd(port)`、`default_name()` 取镜像叶子名）。
**upload/download**：经 envd HTTP 文件 API；目录递归、拒绝 symlink、远端路径必须绝对、POSIX 拼接、download 预检与 `--force`、失败不留临时文件。
**codex**（Linux only）：`setup` 准备 executor 模板（`assets/Dockerfile`：node:22 + `@openai/codex@0.155.1`，用户 uid 1001，`CODEX_HOME=/codex-home`）；`start` 打包项目→`POST /sandboxes {secure:true, autoPause:true, network.allowPublicTraffic:false, metadata.purpose:"codex-project"}`→上传→沙箱内起 `codex exec-server --listen ws://0.0.0.0:4501` 与 UI 服务 4502（bearer token 存 `/codex-home/ui-token`）→ 本地 native Codex 经 `/proxy` WS（头 `e2b-sandbox-port`、`e2b-traffic-access-token`）连远端执行器；`finish` 导出文件后删沙箱（manifest 先持久化再执行不可逆删除）。是"私有 ingress + secure envd + WS 代理"的完整用例。
**completion**（1062 行）：clap_complete `unstable-dynamic`，候选来自 API（活跃沙箱、模板/快照）。

建议图：CLI 分层图（commands → client(ureq/reqwest) / grpc(Connect) → API 控制面 / 代理数据面）；`aenv build` 时序图；`aenv connect` 重连状态图；`aenv codex` 拓扑。

---

## 3. HTTP 端点全表

handler 均为 `ApiImpl` 的 trait 方法（文件：sb=`impls/sandbox.rs`，tp=`impls/template.rs`，sn=`impls/snapshots.rs`，vo=`impls/volumes.rs`，ad=`impls/admin.rs`，md=`impls/mod.rs`）。"E2B 形" = 路径/语义源自 E2B API；"原生" = AgentENV 扩展。鉴权：除标注外均需 `X-API-Key`。

### 3.1 E2B 形（控制面）
| 方法 | 路径 | handler | 说明 |
|---|---|---|---|
| GET | `/health` | md `health_get` | 204，免鉴权 |
| GET | `/sandboxes` | sb `sandboxes_get` | v1 列表（deprecated，仅 Running，metadata 过滤） |
| POST | `/sandboxes` | sb `sandboxes_post` | v1 创建（deprecated；secure 默认 false）；201 + `x-agentenv-sandbox-id` |
| POST | `/v2/sandboxes` | sb `v2_sandboxes_post` | v2 创建（强制 secure，timeout 默认 300） |
| GET | `/v2/sandboxes` | sb `v2_sandboxes_get` | 分页列表；state/order/startedAfter/template/metadata；头 `x-next-token`、`x-total-running` |
| GET | `/sandboxes/metrics` | sb `sandboxes_metrics_get` | 批量最新指标（CSV `sandbox_ids`） |
| GET | `/sandboxes/{sandboxID}` | sb `sandboxes_sandbox_id_get` | 详情（含 envdAccessToken） |
| DELETE | `/sandboxes/{sandboxID}` | sb `sandboxes_sandbox_id_delete` | kill，204 |
| GET | `/sandboxes/{sandboxID}/metrics` | sb `sandboxes_sandbox_id_metrics_get` | 历史指标（节点本地，有界） |
| POST | `/sandboxes/{sandboxID}/pause` | sb `sandboxes_sandbox_id_pause_post` | 暂停 204 |
| POST | `/sandboxes/{sandboxID}/resume` | sb `sandboxes_sandbox_id_resume_post` | 恢复 201（缺省 timeout = 15s 配置值） |
| POST | `/sandboxes/{sandboxID}/connect` | sb `sandboxes_sandbox_id_connect_post` | 运行中延长 TTL(200)/暂停则恢复(201)（deprecated） |
| POST | `/v2/sandboxes/{sandboxID}/connect` | sb `v2_sandboxes_sandbox_id_connect_post` | 同上，body 可省略 |
| POST | `/sandboxes/{sandboxID}/timeout` | sb `sandboxes_sandbox_id_timeout_post` | 覆盖 TTL |
| POST | `/sandboxes/{sandboxID}/refreshes` | sb `sandboxes_sandbox_id_refreshes_post` | 只延长 TTL |
| PUT | `/sandboxes/{sandboxID}/network` | sb `sandboxes_sandbox_id_network_put` | 替换 egress 策略（待核对上游） |
| POST | `/sandboxes/{sandboxID}/snapshots` | sb `sandboxes_sandbox_id_snapshots_post` | 创建持久快照（可命名 alias） |
| GET | `/snapshots` | sn `snapshots_get` | 列 sandbox 来源快照（sandboxID/name 过滤，分页） |
| GET | `/snapshots/{snapshotID}` | sn `snapshots_snapshot_id_get` | 按 ID/alias 取（待核对上游） |
| POST | `/v3/templates` | tp `v3_templates_post` | 创建模板记录（202，templateID=buildID） |
| GET | `/v2/templates` | tp `v2_templates_get` | 分页列表 |
| GET | `/templates` | tp `templates_get` | 全量列表 |
| GET | `/templates/{templateID}` | tp `templates_template_id_get` | 模板及构建 |
| DELETE | `/templates/{templateID}` | tp `templates_template_id_delete` | 删除（活跃构建 409；不存在 204） |
| POST | `/v2/templates/{templateID}/builds/{buildID}` | tp `v2_templates_template_id_builds_build_id_post` | 启动 E2B steps 构建 |
| GET | `/templates/{templateID}/builds/{buildID}/status` | tp `templates_template_id_builds_build_id_status_get` | 状态 + 日志 |
| GET | `/templates/{templateID}/builds/{buildID}/logs` | tp `templates_template_id_builds_build_id_logs_get` | 日志（cursor/direction/level/source） |
| GET | `/templates/aliases/{alias}` | tp `templates_aliases_alias_get` | alias → id |
| GET | `/volumes` | vo `volumes_get` | 列卷（分页） |
| POST | `/volumes` | vo `volumes_post` | 建卷（exclusive/ro，fromVolume/image） |
| GET | `/volumes/{volumeID}` | vo `volumes_volume_id_get` | 取卷（ID 或名） |
| DELETE | `/volumes/{volumeID}` | vo `volumes_volume_id_delete` | 删卷 |

### 3.2 AgentENV 原生（控制面）
| 方法 | 路径 | handler | 说明 |
|---|---|---|---|
| POST | `/sandboxes-cold` | sb `sandboxes_cold_post` | 直接从外部 OCI 镜像冷启动（cpu/mem/disk/attachedDrives/extraBootArgs） |
| POST | `/sandboxes/{sandboxID}/fork` | sb `sandboxes_sandbox_id_fork_post` | 1..100 份 fork，逐个结果 |
| GET | `/sandboxes/{sandboxID}/custom-extension-params` | sb `..._custom_extension_params_get` | 当前扩展参数 |
| PATCH | `/sandboxes/{sandboxID}/custom-extension-params` | sb `..._custom_extension_params_patch` | 经 extension hook 打补丁 |
| PUT | `/templates/{templateID}/builds/{buildID}/builder` | tp `templates_template_id_builds_build_id_builder_put` → `start_image_build` | 准备 BuildKit worker；202 + `x-agentenv-build-id`；429 并发上限 |
| DELETE | `/templates/{templateID}/builds/{buildID}/builder` | tp `..._builder_delete` → `cancel_image_build` | 取消构建并释放 worker |
| GET (WS) | `/templates/{templateID}/builds/{buildID}/builder` | `image_build/transport.rs::connect` | **手写，不在 spec**；BuildKit 字节流隧道 |
| GET | `/metrics` | `agentenv_observability::metrics_handler` | Prometheus，免鉴权（非 proxy 时） |

### 3.3 节点 / admin
| 方法 | 路径 | handler | 说明 |
|---|---|---|---|
| GET | `/nodes` | ad `nodes_get` | 仅本节点（或空）；spec 声明 X-Admin-Token，实际 X-API-Key |
| GET | `/nodes/{nodeID}` | ad `nodes_node_id_get` | 本节点详情 |

### 3.4 代理（数据面）
| 方法 | 路径/条件 | handler | 说明 |
|---|---|---|---|
| ANY | `/proxy` | `proxy.rs::proxy_via_prefix` | 转发到上游 `/` |
| ANY | `/proxy/{*proxy_path}` | `proxy_via_prefix` | 剥前缀转发（保留编码与 `//`） |
| ANY | 任意未匹配路径 + 路由头 | `proxy_via_fallback` | 原路径转发；无路由头则 JSON 404 |
| ANY | Host = `{port}-{uuid}.{domain}`（配置 `[sandbox_proxy].domains`） | 中间件 `sandbox_proxy_classifier` → `proxy_request` | 优先于路由匹配 |
- 路由头：`x-agentenv-sandbox-id` / `e2b-sandbox-id`（UUID）；`x-agentenv-target-port` / `e2b-sandbox-port`（u16>0）。
- 数据面凭据：`X-Access-Token`（secure 沙箱的 envd 端口 49983）、`e2b-traffic-access-token`（private ingress 的其他端口）。转发前剥离：4 个路由头、traffic token、匹配的平台 X-API-Key、未验证的 X-Access-Token、hop-by-hop、Host；注入 `x-forwarded-{host,proto,method,uri}`。
- 控制面响应头：`x-agentenv-sandbox-id`（创建）、`x-agentenv-build-id`（builder PUT）、`x-next-token`、`x-total-running`。网关额外使用 `x-agentenv-node-id`（Go 侧）。

### 3.5 custom extension（AgentENV 调用外部）
`POST {url}/sandbox-hook/start-fresh` | `/start-resume` | `/patch-params` | `/stop`（见上）。

---

## 4. 意外点 / 遗留 / 技术债（"已知问题"章素材）

1. **安全方案名不副实**：spec 中 Bearer/Team/Admin 方案全部只校验 X-API-Key；`Claims` 为空结构；`X-Team-ID`/`teamID` 无意义；`/nodes` 的 X-Admin-Token 不生效。读 spec 的人会被误导。
2. **双重鉴权**：外层 `require_auth` + 生成 handler 内 adapter 各查一次 API key（无害但冗余）；控制面带 `sandbox_id` 路径参数的请求还会额外 `get_sandbox()` 一次以隐藏 template-builder VM（每次控制面请求多一次存储读）。
3. **生成器后处理**：`fix_duplicate_auth_trait()` 正则依赖生成器输出格式；`optional_connect_body` 中间件修补生成器对可选 body 的处理；custom extension 生成器不删孤儿文件。
4. **`mcp` 字段被静默忽略**（`v2_sandboxes_post` 复制、`sandboxes_post` 不读）。
5. **resume 缺省 TTL 15s**（`default_sandbox_timeout_secs=15`）vs v2 create/connect 默认 300s、auto-resume 最小 300s——不一致。
6. **network PUT 的占位值**：`network_policy_from_update()` 传 `allow_public_traffic=true` 占位，靠 orchestrator（service.rs:1968）回填原值——正确但跨层隐式约定，属可读性债（ingress 无法通过 API 事后修改）。
7. **TODO** `sandbox.rs:676`：cold start 同步解析镜像，等 202+轮询；客户端需长超时（spec 描述亦提醒）。
8. **模板 steps 缺 COPY/ADD/filesHash**；ARG 当 ENV。
9. **代理 "temporary reverse proxy contract"**（server.rs 注释）；`is_send_request_failure_text()` 靠错误字符串匹配 hyper-util 私有错误；`pool_max_idle_per_host(0)` 每请求新建 TCP。
10. **分页为内存全量排序**（`PaginationCursor::paginate`），沙箱/模板量大时成本线性增长；v2 list 多 state 参数退化为不过滤。
11. **token 不可单独吊销**；集群 seed 不一致只 warn 不 fail；非 secure 沙箱 envd 无鉴权（UUID 即凭据）。
12. **BuildKit 隧道并发上限不一致**：服务端 8（`MAX_TUNNEL_CONNECTIONS`，超限 429 不排队），CLI 端本地允许 32 并发连接，buildctl 多连接时可能撞 429。
13. **`/templates/{t}/builds/{b}/builder` GET 不在 openapi.yml**，文档站（Stoplight）看不到。
14. `x-api-group: list` 扩展无消费者。
15. `/nodes` 恒报 `NodeStatusReady`，无 draining/unhealthy 状态。
16. `aenv` 仍用 deprecated `POST /sandboxes`（自行加 `secure:true`），而非 v2。
17. `client_id: ""` 等 E2B 兼容占位字段。
18. custom extension：patch 不串行化、与 pause 的竞争以 409 告终（注释承认可接受）；stop best-effort 且可能乱序，靠 instance id 去重，正确性外包给 extension。
19. 运行时依赖全局单例：`ConfigManager::global_config()`、`CustomExtensionClient::global()`（OnceLock，配置变更需重启）、`auto_resume_min_sandbox_timeout()`/`default_sandbox_timeout()` 的 OnceLock 缓存。
20. 测试中的超时常量用 `#[cfg(test)]` 切换（proxy.rs 4 组），可作为"可测试性设计"小节素材。
21. `aenv codex` 硬编码 Codex 版本 0.155.1 与端口 4501/4502。

---

## 5. 章节划分建议

现有计划（Part 3 七章：OpenAPI&骨架 / 认证 / 沙箱 API / 模板快照卷 API / 反向代理 / E2B 兼容 / 节点 admin）基本合理，建议调整：

1. **合并"节点/Admin API"**：手写仅 169 行 + identity 117 行，逻辑是"单节点自报 + 网关聚合"。建议并入 3.1（作为"最简单的 trait 实现示例"开篇）或并入可观测性/集群章节（与 ObservabilityService、gateway cluster_list 一起讲更完整）。
2. **拆分"模板/快照/卷 API"**：模板相关代码 template.rs 1142 + template_helpers 300 + image_build 全家 ~2260（含测试）远大于快照(194)+卷(314)。建议：
   - 3.4 模板构建 API（E2B steps 路径 + Dockerfile/BuildKit 隧道路径 + 构建日志/状态/恢复），与 Part 9 `aenv build` 互相引用；
   - 3.5 快照与卷 API（含沙箱 snapshot/fork 中的卷处理、卷预留 owner 转移、分页）。
3. **E2B 兼容章节定位**：兼容性是贯穿性设计约束，建议保留为独立章但放在 Part 3 最后（3.7），以"兼容矩阵 + 偏差清单 + SDK 请求映射"收束；其余章节遇到兼容点用旁注引用。或者放在 Part 3 开头作为"为什么 spec 长这样"的动机章——二选一，推荐放最后（读者已理解各 API 后再看矩阵更有效）。
4. **认证章覆盖 proxy 鉴权**：`require_auth` 同时处理控制面与数据面，代理章应聚焦转发机制（路由、自动恢复、超时、WS），鉴权只引用 3.2 的决策树，避免重复。
5. **custom extension hooks** 放 orchestrator 部分合理（调用点在 firecracker 后端与 orchestrator service），但其 HTTP 契约与生成客户端可在 3.1 代码生成小节提一句（同一套 openapi-generator，方向相反：服务端 stub vs 客户端）。
6. **aenv CLI（Part 9）** 内容足够撑一章，可再分小节：控制面客户端 / envd Connect 客户端与交互终端鲁棒性 / build 隧道 / codex 案例。`aenv-snapshot-image` 二进制可放快照章或 CLI 章附录。

推荐最终 Part 3：
- 3.1 规范驱动的服务骨架（codegen、trait、Router/中间件洋葱、错误映射、/health /metrics，附 /nodes 示例）
- 3.2 认证与凭据（API key、托管密钥、HMAC token、require_auth 决策树）
- 3.3 沙箱生命周期 API
- 3.4 模板构建 API（steps 与 BuildKit 两条路径）
- 3.5 快照与卷 API
- 3.6 反向代理
- 3.7 E2B 兼容性：矩阵与偏差
