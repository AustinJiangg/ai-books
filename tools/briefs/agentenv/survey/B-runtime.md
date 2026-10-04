# B-runtime：节点编排器（Orchestrator）与沙箱运行时（Sandbox Runtime）源码调研笔记

> 仓库：kvcache-ai/AgentENV，tag v0.2.3，commit 6cccaa7（"chore(release): bump version to v0.2.3"）
> 范围：src/orchestrator、src/sandbox、src/setup、src/virtualization.rs、src/privileges.rs、src/volume.rs、src/local_store.rs、src/cfg*、config/default.toml、src/bin/server.rs、crates/warm-pool、crates/linux-cap、thirdparty/envd、thirdparty/firecracker-client
> 以代码为准；文档只作参照，文档与代码冲突处在第 8 节列出。
> 记法：`path/file.rs::fn_name()`；"FC" = Firecracker；"ns" = network namespace。

---

## 0. 一句话总览

每个节点上跑一个 `server` 进程。进程里有一个泛型 `Orchestrator<S,F,P>`，它维护沙箱状态机（metadata store + 进程内句柄表 + 代理路由表），通过 `SandboxBackendFactory` / `SandboxBackend` 两个 trait 驱动具体后端（只有 Firecracker 一种实现）。Firecracker 后端负责：
- 一个 FC 进程，跑在每沙箱独立的 netns 里；
- 若干 ublk 块设备，由独立的 `uvm-ublk-daemon` 进程提供 overlaybd 后端：tools 盘、用户 rootfs、内存快照、extra drive / volume；
- envd（guest 内 e2b 守护进程）的 HTTP/gRPC 客户端；
- 可选的自定义扩展 HTTP hook。

Pause 不走上游的 "dump 整个 memfile"。做法是：先打一个 state-only 的 Diff 快照，再调用**非上游**的 `GET /vm/dirty-memory-ranges` 拿到脏页区间，用 `process_vm_readv` 直接从 FC 进程地址空间读出这些页，写成一层 overlaybd layer。Resume 时把多层叠好的内存镜像做成只读 ublk 设备，以 `BackendType::File` 交给 FC 去 mmap。

---

## 1. 模块地图（行数含单元测试）

### 1.1 orchestrator（合计 12,381 行，其中 tests.rs 5,808 行，共 104 个测试）
| 文件 | 行数 | 职责 |
|---|---|---|
| `src/orchestrator/mod.rs` | 117 | 对外导出；`SandboxOperation` 枚举；`OrchestratorError`（含 `VirtualizationModeMismatch` / `ShuttingDown` / `InvalidSandboxState` / `SandboxOperationConflict` 等） |
| `src/orchestrator/types.rs` | 106 | `SandboxState`（8 态）、`CreateSandboxRequest`、`SandboxLaunchSource{Snapshot,Image}`、`SandboxForkChildSpec`、生命周期事件类型 |
| `src/orchestrator/launch_plan.rs` | 126 | `LaunchPlan{Create,Resume}`，把"建 + 启动"统一成一条 `launch_sandbox()` 流水线；提供 `transitional_state()`、`transitional_metadata()` |
| `src/orchestrator/service.rs` | 3,041 | `Orchestrator` 本体，包含全部生命周期操作、后台任务、shutdown |
| `src/orchestrator/sandbox_metrics.rs` | 266 | 通过 `#[path]` 挂在 service 下。周期性/事件驱动地采样 guest 指标（envd `/metrics`），带保留期与"代数"校验 |
| `src/orchestrator/metrics.rs` | 294 | `OrchestratorMetrics` 快照：两个原子计数器，其余字段从 store 现算；`SandboxContribution` 定义"状态→资源计数"的映射 |
| `src/orchestrator/proxy.rs` | 119 | `ProxyRouteTable`（sandbox_id → host_interaction_ip + version）与 `ProxyLookupResult` |
| `src/orchestrator/store/mod.rs` | 111 | `MetadataStore` trait（以 CAS 原语为核心）、`StoreError::StateConflict`、`SandboxListFilter` |
| `src/orchestrator/store/metadata.rs` | 195 | `SandboxMetadata`（serde，持久化单位）、`NewTimeout{UseExisting,Set,EnsureMinimum,None}`、`SandboxTimeoutAction{Pause,Delete}` |
| `src/orchestrator/store/in_memory.rs` | 1,038 | `InMemoryMetadataStore`：每条记录配一个 `watch::Sender<Option<SandboxState>>`；用 `BTreeSet<(expires_at,id)>` 做过期索引 |
| `src/orchestrator/persistence/mod.rs` | 142 | `SandboxPersister` trait 与 `DisabledSandboxPersister` |
| `src/orchestrator/persistence/file_backed.rs` | 872 | `FileBackedSandboxPersister`：RocksDB `records.db` 加 `artifacts/<id>/<uuidv7>/` |
| `src/orchestrator/persistence/mock.rs` | 146 | 测试用 `RecordingPersister` |
| `src/orchestrator/tests.rs` | 5,808 | 基于 `sandbox/mock.rs` 的并发/回滚测试 |

### 1.2 sandbox（合计 20,535 行）
| 文件 | 行数 | 职责 |
|---|---|---|
| `src/sandbox/mod.rs` | 113 | 导出；`FreshSandboxBuildSpec`、`SandboxLaunchConfig`（launch 时的运行期输入） |
| `src/sandbox/backend.rs` | 453 | 核心抽象：`SandboxBackend`、`SandboxBackendFactory`、`PausedSandboxState`（不透明、可 encode）、`SandboxCaptureError{Recoverable,Terminal}`、`RuntimeArtifactSet`、`CapturedSandboxSnapshot`、`SandboxExecutor` |
| `src/sandbox/process.rs` | 372 | `Executor` / `ProcessHandle` / `ProcessOpts`：在 envd process gRPC 之上封装 run/start/stdin/signal；输出上限 10 MiB；root 用户通过 `authorization: Basic cm9vdDo=`（即 "root:"）切换 |
| `src/sandbox/access.rs` | 422 | `SandboxAccessTokenGenerator`：HMAC-SHA256(seed, sandbox_id)，另有 traffic token（前缀 `sandbox-traffic-`）；seed 来自配置或 `$HOME/secrets/sandbox-access-token-hash-seed`（32 字节 hex） |
| `src/sandbox/manifest.rs` | 340 | `SandboxSnapshotManifest`（backend="firecracker"、vm_state、memory、rootfs、attached_drives、volume_drive_slots、physical_extra_drive_count、memory_startup_pack） |
| `src/sandbox/metrics.rs` | 80 | `SandboxMetric`（envd `/metrics` 的映射） |
| `src/sandbox/envd.rs` | 355 | `EnvdInstance`：health 探测、`/init`、`/metrics`、process/filesystem gRPC 客户端；`live` 原子标志用于失效 |
| `src/sandbox/envd/user.rs` | 326 | Dockerfile `USER` 为数字或 `uid:gid` 时，读 guest 的 /etc/passwd、/etc/group 解析，必要时追加 passwd 条目 |
| `src/sandbox/extra_drive.rs` | 686 | `ExtraDrive::Overlaybd{…, volume, snapshot_output_dir, sub_path}`；挂载路径校验（保留 /proc /sys /dev /run /agentenv /opt/agentenv）；`prepare_extra_drives()` |
| `src/sandbox/mock.rs` | 508 | 测试后端 |
| `src/sandbox/custom_extension/client.rs` | 814 | 外部 HTTP hook：start-fresh / start-resume / patch-params / stop；`CustomExtensionHookGuard` 保证 stop 恰好送达一次 |
| `src/sandbox/firecracker/mod.rs` | 27 | 子模块入口 |
| `src/sandbox/firecracker/sandbox.rs` | 3,558 | `FirecrackerSandbox`：start_fresh / start_resume / pause_to_dir / snapshot_to_dir / stop / fork / 卷冻结等 |
| `src/sandbox/firecracker/instance.rs` | 758 | `FirecrackerInstance`：进程 spawn（setns 进 netns）、全部 REST 调用 |
| `src/sandbox/firecracker/config.rs` | 1,000 | `FirecrackerCommonConfig` / `FirecrackerSandboxConfig` / `FirecrackerSnapshotConfig`（后者 serde，即 paused state 本体）；`PersistentSnapshotRootGuard`；`MAX_EXTRA_DRIVES=24` |
| `src/sandbox/firecracker/factory.rs` | 259 | `FirecrackerSandboxFactory`：build / build_from_snapshot / build_from_paused_state / decode_paused_state；extra boot args 前缀白名单过滤 |
| `src/sandbox/firecracker/pool.rs` | 429 | `FirecrackerPool`：预 spawn 的 (Slot, FC 进程, work_dir) 三元组，只用于 resume |
| `src/sandbox/firecracker/mmds.rs` | 171 | `MmdsMetadata`（e2b 字段名 instanceID / envID / address / accessTokenHash，accessTokenHash 为 SHA-512）加 flatten extra |
| `src/sandbox/firecracker/overlaybd_snapshot.rs` | 1,290 | 脏页→overlaybd 层；内存/rootfs/drive 层栈重写、继承层硬链接、超限压缩 |
| `src/sandbox/firecracker/process_vm_reader.rs` | 131 | `ProcessVmReader`：把 FC 进程的 HVA 空间当作 overlaybd `VirtualFile` 读取 |
| `src/sandbox/firecracker/startup_pack.rs` | 1,433 | 启动页包（startup pack）：录制（一次性 VM + 专用内存设备）与本地预取 |
| `src/sandbox/firecracker/socket.rs` | 288 | `UnixSocketClient`：hyper legacy client 走 UDS |
| `src/sandbox/firecracker/connector.rs` | 105 | `UnixConnector`（tower Service） |
| `src/sandbox/network/mod.rs` | 72 | 常量（`agentenv-ns-` / `veth-` 前缀）、`prepare_runtime()` 清理残留 netns、`NetworkError` |
| `src/sandbox/network/address_plan.rs` | 100 | 由槽位号算出 3 个 IP；内部网段 deny 列表 |
| `src/sandbox/network/slot.rs` | 1,237 | `Slot`：一个 netns，包含 veth/vpeer/tap0、ns 内 iptables、egress policy 应用、cleanup |
| `src/sandbox/network/manager.rs` | 1,389 | `NetworkManager` 单例：`AtomicBitSet` 槽位位图、`WarmPool<Slot>`、全局 host iptables、atexit 清理、冲突探测（iptables-save / nft / ip route） |
| `src/sandbox/network/policy.rs` | 820 | `SandboxNetworkPolicy{allow_public_traffic, base_policy{Default,Allow,Deny}, egress{allowed_cidrs, allowed_domains, denied_cidrs}}`；生成 iptables 规则 |
| `src/sandbox/network/egress_proxy.rs` | 1,103 | ns 内透明代理（0.0.0.0:15000）：SO_ORIGINAL_DST、HTTP Host / TLS SNI 解析、可信解析、relay；policy 分 pending/active 两阶段 |
| `src/sandbox/network/resolver.rs` | 274 | `HostNetResolver`：常驻 host netns 的 hickory 解析线程 |
| `src/sandbox/network/iptables_util.rs` | 290 | 全部规则经由 `iptables-restore --noflush` 批量提交 |
| `src/sandbox/ublk/device.rs` | 941 | `UblkDeviceManager` 单例（daemon 客户端）；共享只读设备（Weak 去重，保持 cache_fd 打开）；restack 快照；pack 录制 RPC |
| `src/sandbox/ublk/overlaybd.rs` | 372 | `OverlaybdConfig`、`OverlaybdRuntimeHandle`、`compact_layers()`、压缩输出模式 |

### 1.3 其它
| 文件 | 行数 | 职责 |
|---|---|---|
| `src/bin/server.rs` | 270 | 进程入口与启动/关闭顺序（见 §2.4） |
| `src/lib.rs` | 22 | 模块声明 |
| `src/cfg.rs` | 2,199 | confique `AppConfig`；`ConfigManager` 全局单例；路径归一化（`$AENV_HOME` / `$AENV_RUNTIME`）；validate |
| `src/cfg/network.rs` | 181 | `[network.egress]` / `[network.internal]`；固定 VM 链路 CIDR `169.254.0.20/30`；`NETWORK_MAX_SLOTS=32768` |
| `src/cfg/image.rs` | 262 | `[image.*]`（不在本范围，略） |
| `config/default.toml` | 403 | 默认配置（§6） |
| `config/deps_manifest.toml` | — | FC / 内核 / tools / overlaybd 版本与下载 URL，按 kvm/pvm 区分 |
| `src/virtualization.rs` | 52 | `VirtualizationMode{Kvm(默认),Pvm}` |
| `src/privileges.rs` | 333 | 能力契约（CAP_NET_ADMIN、CAP_SYS_ADMIN）；线程内作用域能力；`spawn_tokio_command_scoped()` |
| `crates/linux-cap/src/lib.rs` | 223 | capset/prctl 的薄封装（读 /proc/self/status，设置 ambient） |
| `crates/warm-pool/src/lib.rs` | 608 | 通用 `WarmPool<T>`：水位线、几何增长的 fill_target、condvar 维护线程 |
| `src/volume.rs` | 1,279 | `VolumeManager`：卷目录（权威在 snapshot repository）、预留/释放、发布 backing |
| `src/local_store.rs` | 238 | `LocalKvStore`：RocksDB 异步封装，三档持久性 Memory/Wal/Sync |
| `src/setup/mod.rs` | 169 | `ensure_provisioning` / `ensure_host` / `ensure_environment` |
| `src/setup/deps.rs` | 1,557 | 下载 FC、内核、tools 镜像（ghcr OCI→ext4/overlaybd）、regctl；生成 overlaybd global config |
| `src/setup/packages.rs` | 581 | 发行版探测与包安装/检查 |
| `src/setup/overlaybd.rs` | 612 | overlaybd 静态工具安装 |
| `src/setup/kvm.rs` | 100 | KVM/PVM 模式与 /dev/kvm 检查 |
| `src/setup/ublk.rs` | 118 | 加载 ublk_drv，写 udev 规则 |
| `src/setup/network_capacity.rs` | 270 | sysctl 容量阈值，写 /etc/sysctl.d/99-aenv.conf |
| `thirdparty/envd` | src 214 + http-client | tonic 生成的 filesystem/process 客户端；`DualClient` 自动探测 H2/H1；`x-access-token` 头；http-client 由 OpenAPI 生成（/health /metrics /init /envs /files /files/compose） |
| `thirdparty/firecracker-client` | 2,155 | **只生成了 models**（`--global-property models,supportingFiles`，见 `adev/src/codegen.rs::run_firecracker()`），`apis/` 只有 configuration.rs 和 mod.rs，没有 default_api。真正的 HTTP 调用由 `socket.rs` 自己实现 |

---

## 2. 系统架构与一次沙箱的生命周期（Part 2 素材）

### 2.1 对象模型（建议画类图）
```
Orchestrator<S: MetadataStore, F: SandboxBackendFactory, P: SandboxPersister>
 ├─ store: S (InMemoryMetadataStore)        —— 权威状态：SandboxMetadata + watch 通道
 ├─ sandboxes: RwLock<HashMap<Id, Arc<Mutex<Box<dyn SandboxBackend>>>>>  —— 只存活着的 VM 句柄
 ├─ proxy_routes: RwLock<ProxyRouteTable>   —— 只存可代理的 Running 沙箱，版本号单调递增
 ├─ deletions: Mutex<HashMap<Id, Arc<Mutex<DeleteProgress>>>> —— 删除的可重入进度
 ├─ persister: P (FileBacked/Disabled)       —— 只持久化 Paused 状态
 ├─ factory: F (FirecrackerSandboxFactory)
 ├─ access_tokens / image_refs(RuntimeImageRefs, 防 GC) / volume_manager
 ├─ sandbox_event_tx: broadcast<SandboxLifecycleEvent> (容量 1024)
 └─ shutdown_tx: watch<bool>, shutdown_outcome: OnceCell (单飞)

FirecrackerSandbox (impl SandboxBackend)
 ├─ launch: LaunchMode{Fresh(FirecrackerSandboxConfig) | Resume(FirecrackerSnapshotConfig)}
 ├─ work_dir: TempDir (agentenv-fc-XXXX，FC 的 CWD，放相对路径 symlink)
 ├─ fc_instance: FirecrackerInstance (进程 + UnixSocketClient)
 ├─ network_slot: Option<Slot>
 ├─ envd_instance: Option<EnvdInstance>
 ├─ rootfs_runtime / extra_drive_runtimes: OverlaybdRuntimeHandle (可写 ublk)
 ├─ tools_ublk_device / mem_ublk_device: SharedReadOnlyDevice (跨沙箱共享)
 ├─ mem_dedicated_device (仅 pack 录制)、startup_prefetch_task
 ├─ live_snapshot_root: Arc<PersistentSnapshotRootGuard> (Drop 时 rm -rf)
 └─ custom_extension_hook_guard
```
关键设计：metadata store 与运行期句柄表分离。store 存"逻辑状态"；`sandboxes` 存"是否有活着的 VM"；`proxy_routes` 存"是否可接流量"。三者之间的不一致（例如 Running 但没有路由）在 `proxy_lookup_for()` 中显式返回为 `RouteMissing`。锁顺序固定为 sandboxes → proxy_routes（见 `detach_sandbox_handle_and_route()` 与 `upsert_proxy_route_if_current_handle()` 中的注释）。

### 2.2 磁盘布局（建议作图）
- `$AENV_HOME`（默认 /var/lib/aenv）
  - `persisted-sandboxes/records.db`（RocksDB，Sync 持久性）
  - `persisted-sandboxes/artifacts/<sandbox_id>/<uuidv7>/`：vm_state.bin、mem_overlaybd/overlaybd.commit、mem_image.json、rootfs/、drives/<id>/、inherited-layers/
  - `firecracker-work/agentenv-fc-*/`：FC CWD，内含 firecracker.socket、rootfs.ext4 → tools 设备、user-rootfs → /dev/ublkbN、`<drive>` symlink、`agentenv_volume_slot_N.img`（4 KiB 占位）、overlaybd/（runtime upper）、logs/
  - `firecracker-work/managed-snapshots/<id>/<uuid>/`：未启用持久化时 pause 的产物，以及 fork/capture 的临时产物
  - `secrets/sandbox-access-token-hash-seed`
  - `volumes/catalog`、`deps/`、`logs/serial/<id>/`
- `$AENV_RUNTIME`（默认 /run/aenv）
  - `netns/agentenv-ns-<uuidv7>`：bind mount 出来的 netns 文件

### 2.3 状态机（Part 4 第 1 章核心图）
状态：`Creating, Resuming, Running, Snapshotting, Forking, Pausing, Paused, Killing`。不存在 "Killed" 态，删除完成即从 store 移除，`watch` 通道发出 `None`。

| 起始 → 目标 | 触发 | CAS 期望集合 | 代码 |
|---|---|---|---|
| ∅ → Creating | create（成功 `start_nowait` 之后才 `store.add`） | — | `launch_sandbox()` |
| Creating → Running | `wait_for_ready` 成功 | [Creating] | `launch_sandbox()` 中 `update_if_state` |
| Creating → ∅ | 任一阶段失败 / shutdown | — | `rollback_failed_launch_metadata()`：Create 计划直接 `store.remove` |
| Running → Pausing | 显式 pause；或过期且 timeout_action=Pause | [Running] | `pause_sandbox_inner()`；`claim_expired_running_sandbox()` |
| Pausing → Paused | `backend.pause` 成功并持久化 | 直接 `store.update` | `pause_sandbox_impl()` |
| Pausing → Running | 可恢复的失败 | [Pausing] | 同上（恢复句柄与路由） |
| Pausing → ∅ | Terminal 失败（运行期已被改动） | — | stop + finalize_terminal_volumes + remove |
| Paused → Resuming | resume / 代理 auto_resume | [Paused] | `resume_sandbox_inner()`（随后 `persister.mark_resuming`） |
| Resuming → Running | 成功 | [Resuming] | `launch_sandbox()`，之后 `persister.delete_record` |
| Resuming → Paused | 失败 | [Resuming] | `rollback_failed_launch_metadata()` + `persister.rollback_resuming` |
| Running → Snapshotting → Running | capture_snapshot / snapshot_volume_mounts | [Running] / [Snapshotting] | `begin/finish/fail_snapshot_operation()` |
| Running → Forking → Running | fork | [Running] / [Forking] | `fork_sandbox_inner()` |
| Running/Paused → Killing → ∅ | delete；或过期且 timeout_action=Delete | [Running, Paused] | `delete_sandbox_inner()` / `delete_sandbox_impl()` |
| Killing → 原状态 | 卷捕获可恢复失败（非 builder） | [Killing] | `delete_sandbox_impl()` |

并发语义，逐条：
- 所有公开操作都套一层 `run_cancellation_safe()`，内部 `tokio::spawn`。HTTP 调用方取消请求不会中断状态转换，结果通过 oneshot 回传。
- `wait_for_transition()` 基于 `store.wait_while_in_states()`（watch 通道），超时 `WAIT_TRANSITION_TIMEOUT=60s`，用来兜底"持锁任务 panic 未回滚"的情况。
- 重复 pause：碰到 Pausing 就 `join_concurrent_pause()` 等待并映射结果（Paused 返回 Ok；Running 返回 InvalidState，表示对方失败）。重复 resume 同理走 `join_concurrent_resume()`。resume 一个 Running 的沙箱只更新 timeout。
- delete 遇到任意过渡态：先等过渡结束，再重试 CAS，**绝不让两个删除者同时跑**。若 Killing 回滚到稳定态，也继续重试。
- in_memory 的 `notify_state` 必须用 `send_replace`（注释写明：用 `send` 时若无接收者，值不会更新，后订阅者会读到陈旧状态）。
- `keep_alive_for()` 遇到 Creating/Resuming/Snapshotting/Forking 会先等待。`allow_shorter=false` 时不会缩短 TTL。

### 2.4 server 启动顺序（`src/bin/server.rs::main()`）
1. jemalloc（`malloc_conf: dirty_decay_ms:1000,muzzy_decay_ms:1000,background_thread:true`）、日志、prometheus recorder。
2. `ConfigManager::init_global[_from_path]`，读 `AENV_CONFIG_PATH` 或 `--config`，缺省为 `CARGO_MANIFEST_DIR/config/default.toml`。
3. `--setup-only` → `setup::ensure_provisioning()` 后退出；`--setup-host` → `setup::ensure_host()`（需 root）后退出。
4. `privileges::require_runtime_capabilities()`：非 root 时要求 CAP_NET_ADMIN 与 CAP_SYS_ADMIN 处于"可委派"状态（inheritable + permitted）。随后 `clear_ambient_capabilities()`。
5. API key、NodeIdentity、P2P transport、镜像缓存 P2P、`OverlaybdP2pRuntime`。
6. `setup::ensure_environment()`：建 runtime_path；`prepare_network_runtime` 清理残留 netns；检查包、KVM/PVM、ublk；下载依赖；生成 overlaybd global config；RLIMIT_NOFILE 提到 65536；检查 ip_forward=1；sysctl 容量检查。
7. `UblkDeviceManager::init_global_from_config_with_p2p_publish_url()`，在这里拉起 ublk daemon。
8. `FirecrackerPool::prime(10s)`：预热到 low_watermark（尽力而为）。
9. SnapshotManager、TemplateBuilder（共享 `cluster_cpu_arc`，即 CPU 模板 JSON）、ImageResolver、VolumeManager。
10. `Orchestrator::with_file_backed_store_factory_and_volumes()`：`load_all` 持久记录 → 加载/创建 token seed → 启动 metrics 任务 → 启动 auto-evict 任务 → 若 GC 开启，先 `reconcile_paused_at_startup`（fail-closed）再启动镜像维护任务。
11. Observability 与 reporter；`ApiImpl`；`recover_image_builds`；axum 监听（入站连接 TCP_NODELAY，注释说明 envd Connect-RPC 小帧与 Nagle 会叠出约 40ms 的地板延迟）。
12. 关闭（SIGINT/SIGTERM）：drain startup manifest 任务（15s）→ 停 build cleanup → reporter shutdown → **`orchestrator.shutdown()`：把所有 Running 沙箱 pause 落盘（template builder 例外，直接删除），最多 3 轮** → 清理 NetworkManager → FC pool shutdown → ublk daemon shutdown → overlaybd p2p → p2p transport。

### 2.5 一次完整生命周期 walkthrough（Part 2 主线章节）
以"从模板创建 → 运行 → 暂停 → 恢复 → 删除"为例。

**(A) Create from snapshot（模板）**
`Orchestrator::create_sandbox()` → `run_cancellation_safe` → `create_sandbox_inner()`：
1. 若 `secure`，用 `access_tokens.generate(id)` 生成 envd token。
2. 校验快照的 `virtualization_mode` 与节点一致，否则返回 `VirtualizationModeMismatch`。
3. 组装 `SandboxLaunchConfig`：extra_mmds["imageConfigs"]、env_vars、`network_policy.runtime_policy()`（无规则时为 None）、custom_extension_params（launch 值优先，否则继承快照）、extra_drives（volume）。
4. 组装 transitional `SandboxMetadata`（state=Creating）。
5. 进入 `launch_sandbox(LaunchPlan::for_create_from_snapshot)`：
   1. `build_sandbox()` → `factory.build_from_snapshot()` → `FirecrackerSandbox::from_snapshot()` → `snapshot_config_for_launch()`：`FirecrackerSnapshotConfig::from_runnable_snapshot()`，然后覆写 mmds、token、policy、env、追加 volume drive。这一步只构造对象和 work_dir。
   2. `protect_image_refs(StartingSandbox)`：防止镜像 GC 删掉要打开的层。
   3. `start_nowait()`：FC 进程起来并完成 snapshot load + resume（见 §3.1 resume 调用序列）。
   4. 检查 shutdown → 句柄放入 `sandboxes` → 释放 StartingSandbox pin → `store.add(Creating)`。
   5. 检查 shutdown → `wait_for_ready()`：envd health 轮询 → 通知 ublk daemon "sandbox ready"（放行后台下载）→ `POST /init` → 挂载新 volume。
   6. 检查 shutdown → CAS Creating→Running（写 resources、timeout）→ 取 `host_interaction_ip` → `upsert_proxy_route_if_current_handle`（Arc::ptr_eq 防止陈旧句柄）。
   7. 返回 metadata；计数器加 1；广播 `Create` 事件。
   失败时按阶段 `FailedLaunchStage{Registered, TransitionalPersisted, RunningPersisted}` 走 `cleanup_failed_launch()`：仅当句柄仍是当前句柄时才回滚共享状态；stop 后端；Create 计划 remove，Resume 计划回到 Paused。

**(B) Create fresh（冷启动，OCI 镜像）**
差异：`SandboxLaunchSource::Image` → `FreshSandboxBuildSpec{image_config_path(overlaybd), context, resources(未指定时取 [machine] 的 vcpu_count/mem_size_mib，disk_size_mib=0 表示由 rootfs 设备实际大小回填，见 default_fresh_sandbox_resources()、resources_with_runtime_info()), extra_drives, extra_boot_args}` → `factory.build()` → `FirecrackerSandbox::new_with_id()`。这里会把 drives 分成 physical 与 volume 两组，并按 `min(volume.max_volume_count, 24 - physical)` 预留 volume slot，最后走 `start_fresh()`（见 §3.1）。

**(C) Pause**：`pause_sandbox()` → CAS Running→Pausing → `pause_sandbox_impl()`：
1. 读 runtime_artifacts，`protect_image_refs(PausedSandbox)`。失败则退回 Running。
2. `persister.allocate_artifact_root()` → `artifacts/<id>/<uuidv7>`。
3. `detach_sandbox_handle_and_route()`：从这一刻起不再接流量。
4. `backend.pause(Some(root))` → `FirecrackerSandbox::pause_to_dir()`（§3.1）。
5. 失败处理：Terminal 时 stop + remove，**句柄不放回**；Recoverable 时放回句柄与路由并回到 Running（trait 约定 Recoverable 返回前后端已恢复运行）。
6. `persister.persist_paused(metadata(state=Paused, paused_state), root, state)`。持久化失败则 `backend.resume()` 原地恢复；恢复也失败才 stop + remove。
7. `store.update(Paused)` → `backend.stop()`（SIGTERM FC，释放 ublk 与 slot）→ 广播 `Pause`。

**(D) Resume**：`resume_sandbox()` → 读 metadata → 校验 mode → CAS Paused→Resuming → `persister.mark_resuming()`（记录写成 lifecycle=Resuming，崩溃后启动时据此丢弃）→ `launch_sandbox(LaunchPlan::for_resume)` → `factory.build_from_paused_state()` → `from_snapshot_config_with_override()`（换上新的 token 与 mmds.instanceID）→ `start_resume()` → wait_ready → CAS Resuming→Running → 路由 → `persister.delete_record()`（**只删记录，保留 artifacts**，因为运行中的 VM 还引用这些层）→ 释放 PausedSandbox pin → 广播 `Resume`。

**(E) Kill**：`delete_sandbox()` → `deletion_progress` 锁 → CAS {Running,Paused}→Killing → `delete_sandbox_impl()`，可重入状态机 `DeleteProgress{Capture → Stop{capture_failed} → Release{capture_failed} → Done}`：
1. Capture：若之前是 Running 且挂了 volume，`freeze_and_snapshot_volumes()`（guest 内 busybox fsfreeze，然后 restack 卷的 upper）；随后 `publish_sandbox_volume_backings()`。可恢复失败时先 thaw，再把状态退回原态并返回错误，由调用方重试。
2. Stop：`backend.stop()`。
3. Release：capture 失败则 `fail_backings`（卷标记为 Failed）；`replace_owner_for(owner, None)` 释放卷预留；`remove_deleted_sandbox()`：store.remove → 广播 Delete → `persister.delete_record_and_artifacts()`（删整个 `artifacts/<id>`）→ unpin → 删除 deletions 条目。
4. 任一步失败都保留 progress。下次 delete 从断点继续，不会重复 capture。

---

## 3. Part 5 运行时各章素材

### 3.1 Firecracker 进程与客户端（Ch "FC process & client"）

**进程 spawn**：`instance.rs::spawn_with_netns()`
- 参数：`--api-sock <work_dir>/firecracker.socket --mmds-size-limit 1048576 --http-api-max-payload-size 1048576`。MMDS 上限从默认 50 KiB 提到 1 MiB，因为 MMDS 里要塞 imageConfigs。
- `process_group(0)`，CWD 设为 work_dir（所有 drive 路径都是相对 CWD 的 symlink 名）。
- 通过 `privileges::spawn_tokio_command_scoped(cmd, &[], before)` 启动：先在临时 launcher 线程里 `setns(netns, CLONE_NEWNET)`（这一步需要 CAP_SYS_ADMIN），再把线程能力集设成**空**，然后 spawn，所以 FC 进程**不带任何能力**。`kill_on_drop(true)`。
- spawn 后写 `/proc/<pid>/oom_score_adj = 1000`，让 OOM killer 优先杀 FC、保住 server。
- `wait_for_ready()` 轮询 socket 文件是否出现（默认 socket_timeout 3s、poll 1ms）。期间若进程已退出，把 stderr 末尾 4 KiB 带进错误信息。
- `stop(timeout)`：SIGTERM，等待 socket_timeout，超时 SIGKILL，然后删 socket。不调用 FC 的 `SendCtrlAltDel` 等 API。

**HTTP 客户端**：`socket.rs::UnixSocketClient` 基于 hyper-util legacy Client 和 `UnixConnector`。`firecracker_client` crate 只提供 serde models（OpenAPI 生成，API 1.15.1）。没有 per-request 超时（见 §8）。

**Fresh 启动 FC API 调用序列**（`start_fresh()` → `configure_microvm()` → `start()`）：
0. 准备工作：`link_tools_drive`（work_dir/rootfs.ext4 → tools 共享 ublk 设备，或旧版 ext4 文件）；`create_overlaybd_runtime_device`（用户镜像，可写）→ symlink `user-rootfs`；`prepare_extra_drives`；拼 boot args（`init=/init` 若缺失则补上、`agentenv_drives=vdc:/mnt/x[:sub],…`、`ip=…`、custom ext 返回的 args、DAMON 监控区间 `add_damon_monitor_region()`）；`NetworkManager::allocate_any()`；`slot.set_egress_policy()`；custom ext `start_fresh` hook；spawn FC；等待 socket。
1. `PUT /logger`：仅在配置了 `firecracker.log_level` 时调用。
2. `PUT /machine-config` `{vcpu_count, mem_size_mib, smt:false, track_dirty_pages}`
3. `PUT /cpu-config`：仅在有 CPU 模板 JSON（`cluster_cpu_arc`）时调用。
4. `PUT /boot-source` `{kernel_image_path, boot_args}`
5. `PUT /drives/rootfs`：tools 盘，`is_root_device=true, read_only=true, direct=false, io_engine=Sync`，对应 /dev/vda。
6. `PUT /drives/user_rootfs`：`rw, direct=true(O_DIRECT), io_engine=Async, rate_limiter`（预启动限流），对应 /dev/vdb。
7. `PUT /drives/<physical extra>`：每个一次，`direct=true, Async`，对应 /dev/vdc 起。
8. `PUT /drives/agentenv_volume_slot_<i>`：预留 slot；已有 volume 先 `bind_volume_drive_slot`（删占位文件，改为 symlink）。
9. `PUT /network-interfaces/eth0` `{host_dev_name: tap0}`
10. `PUT /mmds/config` `{version: V2, network_interfaces:[eth0]}`
11. `PUT /mmds`（MmdsMetadata JSON，超过 1 MiB 直接报错）
12. `PUT /balloon` `{amount_mib:0, deflate_on_oom:true, free_page_reporting:true}`：与 guest 内 DAMON reclaim 配合，把冷 pagecache 还给宿主。
13. `PUT /actions {action_type: InstanceStart}`

**Resume / 从快照启动的 FC API 调用序列**（`start_resume()`）：
0. `UblkDeviceManager::is_available()` 快速失败检查。若无自定义 stdout/stderr 路径，尝试 `FirecrackerPool::try_acquire(capture_output)`：命中则直接换上 warm 的 slot + work_dir + FC 进程，并迁移日志文件（`relocate_warm_log()`，处理 EXDEV）。
1. tools 盘 symlink；rootfs `create_overlaybd_runtime_device(requested=known=rootfs_virtual_size, allow_shrink=false)` → symlink。
2. `prepare_snapshot_backing_drives()`（Resume 模式）；`prepare_volume_drive_slots()`：**所有 slot 占位文件都必须存在**，因为 snapshot load 会重新打开 vm_state 里记录的每个路径。已在快照里的 volume 在 load **之前**完成 bind。
3. 未用到 warm pool 时：allocate slot 并 spawn FC。随后 `set_egress_policy`；custom ext `start_resume` hook（pack 录制 VM 不触发）；构造 `EnvdInstance`。
4. 内存设备：普通路径用 `get_or_create_shared_mem()`，同一 mem image.json 的所有沙箱**共享一个只读 ublk 设备**；startup pack 若来自 OSS 走 `prefetch_startup_pack`，若是 LocalPath 走 `submit_local_startup_prefetch`。pack 录制路径用 `create_dedicated_mem_device()` + `start_pack_recording()`。
5. 冷 spawn 时等待 socket。
6. `PUT /logger`（可选）
7. `PUT /snapshot/load` `{snapshot_path: vm_state.bin, mem_backend:{backend_type: File, backend_path: /dev/ublkbN}, resume_vm:false, track_dirty_pages, network_overrides:[{iface_id: eth0, host_dev_name: tap0}]}`
8. 对**本次新加**的 volume：`bind_volume_drive_slot` 后 `PATCH /drives/<slot> {path_on_host}`，让 FC 重新打开文件并读到真实容量。
9. `PUT /mmds`：MMDS 数据不在 vm_state 里，必须重写。
10. `PATCH /drives/user_rootfs {rate_limiter}`：`reconcile_disk_rate_limiter()` 按当前节点配置覆写快照里继承下来的限流，未配置的维度显式设为 disabled。
11. `PATCH /vm {state: Resumed}`
注释说明：balloon 状态在 vm_state.bin 里，不重新配置；cpu-config 不能在 load 后设置，因此 `from_runnable_snapshot` 故意不设。

**Pause FC API 调用序列**（`pause_to_dir()` → `snapshot_to_dir()` → `snapshot_memory_to_overlaybd()`）：
1. 若有可写持久卷，经 envd 在 guest 内执行 `/agentenv/bin/busybox sync`。
2. `PATCH /vm {state: Paused}`
3. `PUT /snapshot/create {snapshot_path: <dir>/vm_state.bin, snapshot_type: Diff}`：**不带 mem_file_path**（非上游语义：只存状态）。
4. `GET /vm/dirty-memory-ranges` → `DirtyMemoryRanges{page_size:4096, memory_size, ranges[{base_host_virt_addr, image_offset, length}]}`（非上游）。
5. `convert_dirty_memory_to_overlaybd(pid, ranges)`：`dirty_ranges_to_segment_mappings()` 把每个范围切成 512 字节扇区的 `SegmentMapping`，其中 `offset` 为镜像扇区、`moffset` 为 HVA 扇区，并校验 4K 对齐与目标区间不重叠；以 `ProcessVmReader(pid)` 作为源 `VirtualFile`，`compact_to()` 生成 `mem_overlaybd/overlaybd.commit`（并发 32，本地始终 Raw，发布时再压缩）。
6. `build_mem_snapshot_image_config()`：如果本次是从快照 resume 的 VM，就继承上一份 mem_image.json 的 lowers，再把新层压在顶上。runtime-owned 的后缀层以硬链接（或复制）方式搬进 `inherited-layers/NNNN/`；超出预算 `32 - prefix/4` 时压缩成 `mem_compacted.commit`。写出 `mem_image.json`。
7. rootfs：`restack_snapshot_overlaybd_rootfs()` → ublk daemon `restack_snapshot`（close_seal 当前 upper，使之成为新的最底层 lower），写到 `<dir>/rootfs/`。
8. 非 volume extra drive 写到 `<dir>/drives/<id>/snapshot.commit`；volume 写到其持久 `snapshot_output_dir`，文件名 `snapshot-<uuid>.commit`，避免覆盖仍被引用的 lower。
9. 组装 `FirecrackerSnapshotConfig`（common 中记录当前 network_policy、custom params、drives、rootfs_virtual_size）与 `SandboxSnapshotManifest`。
- VM 在第 2 步后一直处于 paused。capture/fork 结束后 `PATCH /vm Resumed` 原地恢复（`FirecrackerSandbox::resume()`）；pause 则由 orchestrator 持久化后 stop。
- `snapshot_volumes()`：sync → `PATCH /vm Paused` → restack 卷 → `PATCH /vm Resumed`。
- 未使用的接口：`load_snapshot_uffd()`（`#[allow(dead_code)]`，UFFD backend）。

**Fork**（`FirecrackerSandbox::fork()`）：`pause()`（写到 managed 临时根）→ 立即 `resume()` 源 VM → 每个子 VM `snapshot_config_for_fork()`（只允许替换 launch-time volume drive，不能追加）→ `from_snapshot_config_with_override(child_id, token)` → `join_all(child.start())`。子 VM 共享同一 managed_snapshot_root 的 Arc，最后一个引用释放时目录被删。orchestrator 层规定：有 volume 的源沙箱必须使用 `fork_sandbox_with_specs`。

**Stop 顺序**（`FirecrackerSandbox::stop()`，顺序有讲究）：cancel 预取 → FC SIGTERM/SIGKILL → envd invalidate → 释放 rootfs ublk（必须在 FC 停之后、网络清理之前）→ 释放 tools 共享设备（显式释放，避免与同镜像的后续 resume 竞争）→ 删除 pack 专用内存设备 → 释放 extra drive 设备 → custom ext stop hook（在释放 slot **之前**）→ `NetworkManager::release(slot)` → 停预取 reader → 释放共享内存设备。`Drop` 走尽力清理路径：ublk 设备留给 daemon，slot 释放。

### 3.2 Startup pack（启动页包）
- 目的：冷恢复时，按 first-touch 顺序预取内存页，减少缺页导致的远端读放大。
- 录制：`startup_pack.rs::record_startup_pack()`，在 publish 快照后异步执行，失败不影响发布。
  1. `derive_recording_mem_config()`：复制 mem image.json 并强制 `download_override.enable=false`。
  2. `config.pack_recording=true` → `FirecrackerSandbox::from_snapshot_config` → `start_nowait()`：使用**专用、非共享**的内存设备（共享设备或块设备 page cache 会掩盖 first-touch 读），在 snapshot load **之前**调用 `start_pack_recording(dev_id, output, window{max_pages, min_window_ms=200, quiet_ms=300, max_window_ms=2000})`。
  3. 每 200ms 轮询 `pack_recording_status`，直到 Done/Failed，受 `record_budget_secs=10` 限制。shutdown 时由 `startup_manifest_abort_notify` 中断。
  4. 无论成败都要 abort（限时 3s）并 stop VM。产出 `{snapshot_dir}/memory-startup.trace`，由 publisher 展开成 v4 manifest（exact-order prefix + merged ranges）。
- 消费：`consume_enabled` 开关。OssUrl 来源交给 daemon 的 `prefetch_startup_pack`；LocalPath 来源由 `submit_local_startup_prefetch()` 直接按 manifest span 读共享内存块设备（spawn_blocking，全局信号量限 4 个并发读，同一设备/manifest 去重，订阅者引用计数，`consume_timeout_secs=30`）。
- 配置在 `[snapshot.memory_startup_pack]`，默认 `enabled=false, consume_enabled=false`。default.toml 中没有这一节。

### 3.3 MMDS
- `mmds.rs::MmdsMetadata`：字段名与 e2b 兼容，`instanceID`=sandbox_id、`envID`=snapshot_id/image_ref、`address`=logs collector（始终为空串）、`accessTokenHash`=SHA-512(token)，无 token 时为 SHA-512("")。extra 以 flatten 方式合并到顶层，保留字段不可覆盖。目前唯一的 extra 是 `imageConfigs`（原始 OCI 镜像配置，供 guest 侧使用）。
- MMDS V2，只挂在 eth0 上。Fresh 时在 boot 前写入；resume 时在 load 后重写，此时 sandbox_id 和 token 哈希都要换成新的。
- guest 端（envd）用 accessTokenHash 校验 token，用 instanceID 识别实例。

### 3.4 网络（详见 §4）

### 3.5 envd 集成
- 地址：`http://<host_interaction_ip>:<control_plane_port=49983>`，host 侧经 DNAT 到达 VM。
- `EnvdInstance::wait_for_ready()`：每 `poll_ms=3ms` 调一次 `GET /health`，单次探测 1s 超时，总时长 `init_timeout_secs=60`。
- `init()`：`POST /init {accessToken, envVars, defaultWorkdir, defaultUser, timestamp}`，同时带 `X-Access-Token` 头。USER 为数字或 `uid:gid` 时，先以 root 做一次 init，再读 /etc/passwd 解析（必要时追加条目），之后二次 init。**resume 后也会重新 init**，用于同步时钟和 token。
- 引导 HTTP 客户端 `pool_max_idle_per_host(0)`：同一 IP 会被后续 VM 复用，不能保留旧连接。
- gRPC：`thirdparty/envd/src/transport.rs::DualClient` 首次请求用 `OPTIONS /` 探测是否支持 H2 prior knowledge，失败则回退 H1；TCP_NODELAY；`x-access-token` 标记为 sensitive。
- `Executor`：root 用户通过 `authorization: Basic cm9vdDo=` 指定。运行期大量 guest 操作（mount、fsfreeze、sync）都依赖 tools 盘里的 `/agentenv/bin/busybox`。
- 指标：`GET /metrics` → `SandboxMetric`，由 sandbox_metrics 任务采集。

### 3.6 Extra drives 与 volumes
- 设备命名：vda=tools（root，带 /init）、vdb=用户镜像、vdc… = physical extra drive，之后是 volume slot，最多 24 个（c..z，见 `MAX_EXTRA_DRIVES`、`volume.rs::MAX_VOLUME_MOUNTS=24`）。
- Fresh 启动的挂载由 guest init 读 boot arg `agentenv_drives=vdc:/mnt/data,vdd:/mnt/logs:sub/path` 完成。从快照启动时**新加**的 volume 不在 guest 挂载命名空间里，需要在 envd ready 后由 host 经 envd 执行 `busybox mount -n`：只读 volume 加 `-o ro,noload`（崩溃一致快照的 ext4 带 needs-recovery 标志，只读设备无法回放日志）；带 sub_path 时先挂到 `/run/agentenv-drive-<id>`，再 `--bind`，然后 `umount -l` stage 目录。
- "预留 slot" 机制：FC 在 snapshot restore 之后不能新增 virtio-blk 设备，所以第一次启动时就按 `volume.max_volume_count`（默认 4）预留 `agentenv_volume_slot_<i>`，以 4 KiB 占位文件形式存在。之后通过替换 symlink 再 PATCH path 实现"热插"。manifest 记录 `volume_drive_slots` 与 `physical_extra_drive_count`。旧快照的 `volume_drive_slots==0` 时，所有 drive 都视为 physical。
- volume 删除流程中的冻结：`freeze_and_snapshot_volumes()` 里，guest 内脚本先打开挂载点 fd，校验设备号不等于根文件系统，再 `fsfreeze`（30s 超时）。挂载点**先压栈再 await**，以便取消时仍保留 thaw 义务。RPC 失败一律视为 Terminal，因为 ioctl 的结果未知。
- `VolumeManager`（`src/volume.rs`）：权威记录在 `SnapshotRepository`（reserve_volume / replace_volume_owner_for），本地只是缓存。模式 ReadOnly（可多挂）或 Exclusive（单 owner）；状态 Ready/Uploading/Failed；默认大小 64 GiB，上限 256 GiB。

### 3.7 Warm pools
| 池 | 实现 | 元素 | 使用点 | 备注 |
|---|---|---|---|---|
| network | `NetworkManager.pool: WarmPool<Slot>` | 已建好的 netns + veth + tap + 基础 iptables | `allocate_any()` 快路径；`release()` 回池 | 回池时**不重建 namespace**。通过 `user_egress_rules_present` 判断下一个租户是否要先清用户规则。维护线程按水位补充/排空 |
| block | ublk daemon 内部（`uvm_ublk_daemon::PoolConfig`） | overlaybd 设备 | `acquire_overlaybd` | `maintenance_enabled` 被强制设为 false，因为设备形状与镜像/大小相关，只能在请求路径上异步补充 |
| firecracker | `FirecrackerPool: WarmPool<WarmFirecracker{slot, fc_instance, work_dir}>` | 已 spawn 且 socket 就绪的 FC 进程（尚未配置） | **只用于 `start_resume`**（快照 load 要求进程未配置） | 自带单 worker 的 tokio runtime；`fill_concurrency=4`；`atexit` 钩子；stdout/stderr 捕获设置不一致时不复用 |
- `crates/warm-pool`：`compute_maintenance_action()` 返回 Fill/Drain/Idle。`fill_target` 初值为 low_watermark，**只要出现一次获取压力就翻倍，直到 high_watermark，并且在进程生命周期内只升不降**（注释明说这是有意为之）。开启 maintenance 时 `release()` 可以超过 high（交给维护线程 drain）；关闭时超过 high 直接拒绝。维护线程通过 condvar 唤醒。
- 默认 `low=2, high=64`，三个池共用这组水位。

### 3.8 内存导出：process_vm_readv 与脏页区间
- 为什么不用上游 `mem_file_path`：上游会把整块 guest 内存写成一个文件，再由外部转换。这里直接从 FC 地址空间按脏页区间读，一步生成 overlaybd 层，没有中间 memfile，写入量与"脏页数"成正比，不随 VM 内存大小增长。
- 脏页的含义：resume 后的 VM 内存是 MAP_PRIVATE mmap 一个只读 ublk 块设备，脏页就是发生过 COW 的页；fresh 启动的 VM 则是启动以来写过的页。`track_dirty_pages=false` 时（PVM 下被强制关闭），配置注释写的是 "use mincore"，也就是改为按驻留页统计（推测在 FC 补丁内部实现，未在本仓库代码中出现）。
- API 文档说明该查询 "logically non-clearing"：外部消费失败时脏位保留，下次快照仍会包含这些页。
- `ProcessVmReader` 的 TODO：`process_vm_readv` 是同步调用，目前直接跑在 tokio worker 上（见 §8）。
- 内存层栈：每次 pause 产生一层新层压在继承层之上。快照目录自包含（继承层硬链接进来），并对 runtime-owned 后缀的层数设预算，避免触及 overlaybd 255 层上限。
- Resume 的内存路径：只读共享 ublk 设备，`cache_fd` 常驻打开以保住 page cache，跨沙箱共享 page cache，等于天然的内存去重。

### 3.9 KVM vs PVM
- `VirtualizationMode` 是**节点级**配置，也是**快照兼容域**：持久 Paused 记录、snapshot、模板都记录 mode，create/resume 时不匹配就拒绝（`VirtualizationModeMismatch`）。`file_backed.rs::load_all()` 遇到其它 mode 的记录时，保留元数据和产物，但不提供可恢复状态（`into_metadata_without_runtime_state`），两种 mode 的记录可共存。
- 检查逻辑在 `setup/kvm.rs::check()`：PVM 仅支持 x86_64，且要求 `/sys/module/kvm_pvm` 存在；KVM 模式下若检测到已加载 kvm_pvm 则拒绝启动；两种模式都使用 /dev/kvm。
- 依赖按 mode 区分（`deps_manifest.toml`）：KVM 用 `kvcache-ai/firecracker 1.15.1-patch-v1` 与 `vmlinux-6.1.175`；PVM 用 `kvcache-ai/firecracker-next v1.17.0-next.1` 与 `6.12.33-pvm` 内核。
- PVM 模式在 normalize 阶段强制 `memory_snapshot.track_dirty_pages=false`，validate 再兜底一次（注释："has not been tested"）。
- 运行时代码路径（instance/sandbox）**没有任何 KVM/PVM 分支**，差异全部体现在二进制、内核和配置上。

### 3.10 自定义扩展 hook（Part 4 "custom extension hooks" 章）
- `[custom_extension].url`（环境变量 `AENV_CUSTOM_EXTENSION_URL`），`timeout_ms=5000`。
- 接口：`POST {url}/sandbox-hook/start-fresh {sandbox_id, instance_id, netns_path, host_interaction_ip, params}`，可返回 `extra_boot_args`；`start-resume` 参数相同；`patch-params` 返回完整的新 params；`stop` 尽力送达，失败只记日志。
- 每次 start 生成一个新的 `SandboxInstanceId(uuidv7)`。sandbox_id 在 pause/resume 之间不变，扩展方应以 (sandbox_id, instance_id) 识别实例，并忽略过期的 stop。
- 除 stop 外，任何 hook 失败都会让对应生命周期操作失败。
- `patch_sandbox_custom_extension_params()`：hook 在**不持有沙箱锁**的情况下调用；成功后写入后端并 CAS 更新 store；与 pause 竞争时返回 InvalidState。
- params 会持久化进快照与 committed snapshot。创建时的 launch 值优先，否则继承。

---

## 4. 网络设计（具体到地址与规则）

### 4.1 拓扑
```
[VM eth0 169.254.0.21/30] ⇄ [tap0 169.254.0.22/30] ─(ns 内转发)─ [vpeer 10.12.(2i+1)/31]
        │                    ↑ nat PREROUTING -i tap0 → AGENTENV-EGRESS-PROXY (80/443 REDIRECT :15000)
        │                    └─ EgressProxy listener (ns 内 0.0.0.0:15000)
   netns /run/aenv/netns/agentenv-ns-<uuidv7>
                                   ⇅ veth pair
[host veth-<i> 10.12.(2i)/31]  ── host 路由: 10.11.0.<i>/32 via 10.12.(2i+1) dev veth-<i>
                                   └→ host MASQUERADE → Internet
```
- 地址计划（`address_plan.rs::slot_ips(idx)`）：host_interaction_ip = `10.11.0.0/16` 的第 idx 个地址；veth_host = `10.12.0.0/16` 的第 2·idx 个；veth_vm(vpeer) = 第 2·idx+1 个；VM 链路固定为 `169.254.0.20/30`，VM=.21、TAP=.22。**所有 slot 的 VM 和 tap 地址完全相同**：快照 ABI 依赖这一点，因为 fresh 启动经内核 `ip=` 参数配置网络，而 resume 不会重放 boot args（见 `cfg/network.rs` 注释）。
- slot 0 保留不用；`NETWORK_MAX_SLOTS=32768`。配置校验要求 host_interaction_cidr 至少 32768 个地址、veth_cidr 至少 65536 个，且三段互不重叠。
- 内核参数：`ip=169.254.0.21::169.254.0.22:255.255.255.252:instance:eth0:off:<dns>`。dns 取 /run/systemd/resolve/resolv.conf 或 /etc/resolv.conf 中第一个非 loopback 的 IPv4，取不到则用 8.8.8.8。
- 创建流程（`slot.rs::create_network()`）：新开一个 OS 线程 → `unshare(CLONE_NEWNET)` → bind mount `/proc/thread-self/ns/net` 到 netns 文件 → 在线程内建 current_thread runtime，经 rtnetlink：建 veth 对（veth-i / vpeer）→ 把 veth-i 移回 host ns（fd 取自 `HOST_NS_FD`，进程首次调用时从 `/proc/thread-self/ns/net` 抓取）→ lo up → vpeer 配 /31 地址（不设 broadcast，RFC 3021，需要手搓 netlink 消息）→ `ip tuntap add tap0 mode tap`（作用域 CAP_NET_ADMIN）→ tap0 配地址并 up → 默认路由经 veth_host → 写 ns 内 `ip_forward=1` → tap0/vpeer 的 ARP `retrans_time_ms=100`（issue #272，降低 resume 尾延迟）→ ns 内 iptables。回到 host 侧：veth-i 配 /31 地址并 up，`ip route add <hip>/32 via <vpeer> dev veth-i`（注释：netlink 在 /31 网关上有兼容问题）→ host veth 的 ARP 调优。
- FC 进程通过 setns 进入该 ns，`tap0` 在 ns 内可见。

### 4.2 iptables 规则
**宿主全局规则**（`manager.rs::global_host_iptables_commands()`，NetworkManager 初始化时安装一次，shutdown 时删除；cidr = host_interaction_cidr）：
```
filter INPUT  -I 1: -i veth-+ -s 10.11.0.0/16 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
filter INPUT  -I 2: -i veth-+ -s 10.11.0.0/16 -j REJECT      # 沙箱不能主动访问宿主
filter FORWARD -A : -i veth-+ -s 10.11.0.0/16 -j ACCEPT      # 宿主 FORWARD 默认 DROP 时仍可转发
filter FORWARD -A : -o veth-+ -d 10.11.0.0/16 -m state --state RELATED,ESTABLISHED -j ACCEPT
nat POSTROUTING -A : -s 10.11.0.0/16 -j MASQUERADE
```
**每个 ns 的基础规则**（`slot.rs::configure_namespace_iptables_rules()`）：
```
filter FORWARD -A: -i tap0 -o vpeer -j ACCEPT
filter FORWARD -A: -i vpeer -o tap0 -m state --state RELATED,ESTABLISHED -j ACCEPT
nat POSTROUTING -A: -o vpeer -s 169.254.0.21 -j SNAT --to <hip>
nat POSTROUTING -A: -o vpeer -s <vpeer_ip> -j SNAT --to <hip>     # 代理发起的连接
nat PREROUTING  -A: -i vpeer -d <hip> -j DNAT --to 169.254.0.21     # host→VM (envd/代理)
```
**egress 链**（`policy.rs::initialize_namespace_egress_chain()`）：
```
filter: new AGENTENV-EGRESS, new AGENTENV-USER-EGRESS
filter FORWARD -I 1: -i tap0 -o vpeer -j AGENTENV-EGRESS
AGENTENV-EGRESS:
  -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  -d <dns>/32 -p udp --dport 53 -j ACCEPT ; 同 tcp
  -d 10.11.0.0/16 -j REJECT ; -d 10.12.0.0/16 -j REJECT ; -d 169.254.0.20/30 -j REJECT  (内部网段)
  -d <always_denied_cidrs...> -j REJECT   (默认 RFC1918、100.64/10、127/8、169.254/16)
  -j AGENTENV-USER-EGRESS
nat: new AGENTENV-EGRESS-PROXY ; nat PREROUTING -I 1: -i tap0 -j AGENTENV-EGRESS-PROXY
```
**用户规则**（`build_user_egress_commands()`，每次先 `-F AGENTENV-USER-EGRESS`）：依次为 allowed_cidrs ACCEPT → denied_cidrs REJECT →（base=Deny 时）`-d 0.0.0.0/0 -j REJECT`。只处理 IPv4，IPv6 条目保留但不生效。
**代理重定向**（`build_egress_proxy_commands()`，先 `-F`）：有域名 allow 时添加 `-i tap0 -p tcp --dport {80,443} -j REDIRECT --to-ports 15000`。
- 全部规则通过 `iptables-restore --noflush` 按表分组一次提交（`iptables_util.rs`）。不使用 nft，nft 只出现在 `log_external_conflicts()` 的冲突探测中，用来扫描 nft ruleset 里是否引用了 AgentENV 网段。

### 4.3 策略语义与 egress proxy
- `SandboxNetworkPolicy::runtime_policy()`：没有运行期规则（base≠Deny 且无显式条目）时返回 None，此时 `set_egress_policy` 走快路径，不做任何改动（除非上一个租户留下了规则）。
- API 层约束（`api/impls/sandbox.rs::validate_domain_allowlist()`）：allowOut 里出现域名时，denyOut 必须包含 `0.0.0.0/0`。域名检查只作用于 TCP 80/443，其它端口只看 CIDR。
- 判定顺序（`is_ip_allowed()`）：绝对拒绝（always_denied + 内部网段）→ allowed_cidrs → denied_cidrs → 有域名规则则拒绝 → base≠Deny 才放行。`is_domain_allowed()`：支持 `*` 和 `*.suffix` 通配；**域名 allow 优先于用户 CIDR deny**（与 E2B 一致），但绝对拒绝依然有效。
- 代理连接处理（`egress_proxy.rs::handle_connection()`）：`getsockopt(SO_ORIGINAL_DST)` 取原始目的地。若原 IP 被 CIDR 允许，直接连原 IP；否则最多读 64 KiB / 10s 的 preface，解析 HTTP Host 或 TLS SNI → `select_upstream()` → 用 **host ns** 中的 `HostNetResolver`（hickory，每次解析 5s 超时，最多 16 个并发）解析域名，guest 无法通过 /etc/hosts 或 DNS 劫持 → 过滤掉被绝对拒绝的地址 → 逐个连接（30s 超时）→ 写回 preface → 双向 relay。授权**按 TCP 连接**进行，keep-alive 上后续的 HTTP 请求不再检查。
- 线程模型：每个 ns 一个 listener 线程（setns 进 ns 后 bind；nonblocking accept，空闲时 sleep 5ms），每个连接一个线程，每个代理最多 256 个连接。
- 策略替换不中断：`set_egress_policy()` 先 `ensure_listener` 并把新策略写入 pending；若之前没有 active 策略就立即 activate（保持原先默认放行的行为），然后在 ns 线程里提交 iptables；成功后 activate pending（原来有 active 的情况），或在新策略不需要代理时 deactivate（停止 listener，但已有连接保留原策略快照，直到 teardown 才断开）。失败时有旧策略则 discard pending，没有则 teardown。
- orchestrator 层（`replace_sandbox_network_policy_inner()`）：只允许在 Running 状态下替换；保留 `allow_public_traffic`（不允许借此修改）；无句柄时返回 `SandboxOperationConflict`；先改运行期，再写 store。pause 时当前策略写入快照，resume 时重新应用。

### 4.4 生命周期与清理
- `Slot::cleanup()`：teardown 代理 → 删除 host veth（会连带删掉 vpeer）→ 循环 umount netns 文件直到 EINVAL → 删除文件。`Drop` 走同步路径。
- `NetworkManager` 初始化时扫描 `/sys/class/net/veth-*` 并预留对应 slot，避免与残留接口或其它进程冲突；同时检查 `ip route`、`iptables-save`、`nft` 中的冲突并告警。
- 启动时 `network::prepare_runtime()`：清除 `$RUNTIME/netns/agentenv-ns-*` 的残留 bind mount。
- 宿主容量 sysctl（`setup/network_capacity.rs`）：neigh gc_thresh1/2/3 = 4096/8192/16384、nf_conntrack_max = 1048576、pid_max = 4194304、inotify max_user_instances = 8192，写入 `/etc/sysctl.d/99-aenv.conf`；在容器内默认跳过（可用 `AENV_FORCE_SYSCTL_TUNING` 强制）。

---

## 5. Firecracker REST 端点使用清单

| 方法/路径 | 用途 | 调用位置 | 是否上游 |
|---|---|---|---|
| PUT /logger | 可选日志 | `instance.rs::set_logger()` ← `sandbox.rs::configure_logger()`（fresh 与 resume 都会调） | 上游 |
| PUT /machine-config | vcpu / mem / smt=false / track_dirty_pages | `set_machine_config()` ← `configure_microvm()` | 上游 |
| PUT /cpu-config | CPU 模板（原始 JSON 透传） | `set_cpu_config()` | 上游 |
| PUT /boot-source | 内核与 boot args | `set_boot_source()` | 上游 |
| PUT /drives/{id} | rootfs / user_rootfs / extra / volume slot | `add_drive()`，**使用 `direct` 字段（O_DIRECT）** | **`direct` 非上游**（yaml 中描述为"使用 O_DIRECT 打开，对不对齐的 buffer 自动用 bounce buffer"） |
| PATCH /drives/{id} | ① 限流 reconcile ② 为新 volume 改 path_on_host | `patch_drive_rate_limiter()`、`patch_drive_path()` ← `start_resume()` | 上游（PartialDrive） |
| PUT /network-interfaces/eth0 | host_dev_name=tap0 | `add_network_interface()` | 上游 |
| PUT /mmds/config | V2、eth0 | `set_mmds_config()` | 上游 |
| PUT /mmds | 写数据 | `set_mmds()`（fresh 与 resume） | 上游 |
| PUT /balloon | free_page_reporting | `set_balloon()` | 上游（free_page_reporting 为较新版本特性） |
| PUT /actions InstanceStart | 启动 | `start()` | 上游 |
| PATCH /vm Paused / Resumed | 暂停/恢复 | `pause()` / `resume()` | 上游 |
| PUT /snapshot/create | `snapshot_type=Diff`，**不带 mem_file_path** = 只存状态 | `create_state_only_snapshot()` | **非上游**：上游 mem_file_path 是必填项；本 yaml 中只有 snapshot_path 必填，并注明"未指定则只保存 VM 状态" |
| GET /vm/dirty-memory-ranges | 脏页区间（HVA + image_offset） | `get_dirty_memory_ranges()` ← `snapshot_memory_to_overlaybd()` | **非上游** |
| PUT /snapshot/load | `mem_backend{File: ublk 设备路径}`、network_overrides、track_dirty_pages、resume_vm=false | `load_snapshot_file()` ← `start_resume()` | network_overrides 是较新的上游特性；用块设备作为 File backend 是用法上的创新 |
| PUT /snapshot/load (Uffd) | 未使用 | `load_snapshot_uffd()`（dead_code） | 上游 |
| GET /vm/guest-memory-regions | **yaml 中定义但代码未使用**（返回各内存区域的 HVA/size/offset/page_size，供外部进程直接读内存） | — | **非上游**，可作为"补丁 FC 的接口全貌"来介绍 |
| 进程参数 `--mmds-size-limit`、`--http-api-max-payload-size` | 1 MiB | `spawn_with_netns()` | 上游 |

FC 版本说明：KVM 使用 `1.15.1-patch-v1`（kvcache-ai fork），PVM 使用 `firecracker-next v1.17.0-next.1`。client 模型生成自 1.15.1 的 yaml。升级流程见 `docs/src/internals/sandbox-testing.md §4.1`（该节中 `[firecracker]` 的写法已过时，见 §8）。

---

## 6. 配置系统概览（Part 2 "config system" 章）

### 6.1 机制
- 使用 confique 派生的 `AppConfig`。加载顺序 `AppConfig::builder().env().file(path).load()`，**环境变量优先于文件**，其次才是代码中 `#[config(default)]` 的默认值。
- `normalize(config_dir)`：展开 `$AENV_HOME` / `$AENV_RUNTIME` 占位符，相对路径以配置文件所在目录为基准；PVM 模式关闭 dirty tracking；处理 cluster 与 sandbox_proxy 的归一化。
- `validate()`：模板构建、卷上限、磁盘限流、内存快照选项、后台下载上限、overlaybd global config 路径不得冲突、池配置合法性。
- `ConfigManager::global()`：`OnceLock` 单例。全代码库通过 `ConfigManager::global_config()` 随处取配置，属于隐式依赖；测试中会注入 `TEST_ACCESS_TOKEN_HASH_SEED`。
- 不支持热加载，修改配置需重启进程。

### 6.2 default.toml 各节（共 403 行）
| 节 | 关键键（默认值） | 消费方 |
|---|---|---|
| 顶层 | `home_path="/var/lib/aenv"`、`virtualization_mode="kvm"`、runtime_path（代码默认 /run/aenv）、deps_path（`$AENV_HOME/deps`） | 全局 |
| `[firecracker]` | `boot_args="console=ttyS0 reboot=k panic=1 pci=off mitigations=off init=/init page_reporting.page_reporting_order=6 damon_reclaim.*…"`、`socket_timeout_secs=3`、`socket_poll_ms=1`、可选 binary_path / version / url / work_dir / serial_dir / log_level / allowed_extra_boot_args_prefixes | sandbox/firecracker |
| `[kernel]` `[tools]` | `control_plane_port=49983`（envd 端口）；tools 版本 | deps / sandbox |
| `[image.*]` | resolver、cache（100GB）、gc（1800s 间隔，0.95/0.70 水位） | 镜像层（不在本范围），orchestrator 维护任务使用 gc_schedule |
| `[p2p]` | `enabled=false`、iroh | 不在本范围 |
| `[custom_extension]` | url（空）、timeout_ms=5000 | §3.10 |
| `[cluster]` `[sandbox_proxy]` | domains=[] | API/代理 |
| `[network.egress]` | always_denied_cidrs（6 段） | §4 |
| `[network.internal]` | host_interaction_cidr=10.11.0.0/16、veth_cidr=10.12.0.0/16 | §4 |
| `[machine]` | mem_size_mib=1024、vcpu_count=2；`[machine.disk_rate_limit]` enabled=false、bandwidth/iops 及其 burst | FC 配置 |
| `[envd]` | version=0.5.15、init_timeout_secs=60、poll_ms=3 | runtime policy |
| `[sandbox]` | access_token_hash_seed（可选） | access.rs |
| `[volume]` | max_size_mb=262144、max_volume_count=4 | slot 预留 / VolumeManager |
| `[orchestrator]` | metrics_interval_secs=15、metrics_retention_secs=3600、auto_evict_interval_ms=1000、**default_sandbox_timeout_secs=15**、auto_resume_min_sandbox_timeout_secs=300、persisted_sandbox_store_path=`$AENV_HOME/persisted-sandboxes` | orchestrator |
| `[snapshot]` | repository_backend=posix_fs、p2p_enabled、`[snapshot.publish_compression]` lz4；`memory_startup_pack`（代码默认全部关闭） | 快照层 / startup pack |
| `[ublk]` / `[ublk.overlaybd]` | daemon_metrics_listen_addr、read_only=false、runtime_upper_mode=hybridLogStructured、allow_shrink=false、resize_timeout_secs=120、remote_io_workers、download_enable=false、p2p 超时 | ublk |
| `[pool]` | low_watermark=2、high_watermark=64；`[pool.network]` maintenance_enabled；`[pool.block]` enabled；`[pool.firecracker]` enabled、startup_prewarm、fill_concurrency=4 | §3.7 |
| `[memory_snapshot]` | track_dirty_pages=true、overlaybd_global_config_path；`[memory_snapshot.background_download]` enable / delay / try_cnt / block_size=16MiB / concurrency=4 / max_inflight_blocks=16 | 内存快照 |
| `[template_build]` | max_concurrent_builds=4、buildkit 镜像、builder 16 核 / 32 GB、cache 64 GB | 模板构建（不在本范围） |
| `[observability]` | enabled；scheduler_report（5s） | observability |
| `[node_identity]` | node_id / cluster_id / service_instance_id | 集群 |

### 6.3 环境变量（本范围内代码中定义的）
`AENV_CONFIG_PATH`、`AENV_HOME_PATH`、`AENV_RUNTIME_PATH`、`AENV_DEPS_PATH`、`AENV_VIRTUALIZATION_MODE`、`AENV_FIRECRACKER_WORK_DIR`、`AENV_FIRECRACKER_SERIAL_DIR`、`AENV_SNAPSHOT_STORE`、`AENV_SNAPSHOT_LOCAL_CACHE_PATH`、`AENV_SANDBOX_PROXY_DOMAINS`、`AENV_SANDBOX_ACCESS_TOKEN_HASH_SEED`（集群部署时各节点必须一致，否则 token 无法跨节点验证）、`AENV_UBLK_DAEMON_BINARY_PATH`、`AENV_UBLK_DAEMON_METRICS_LISTEN_ADDR`、**`AGENTENV_MEMORY_SNAPSHOT_TRACK_DIRTY_PAGES`**（前缀与其它变量不一致）、`AENV_PERSISTED_SANDBOX_STORE_PATH`、`AENV_CUSTOM_EXTENSION_URL`、`AENV_OBSERVABILITY_*`、`AENV_NODE_ID` / `AENV_CLUSTER_ID` / `AENV_SERVICE_INSTANCE_ID`、`AENV_FORCE_SYSCTL_TUNING`、`API_ADDR`（默认 0.0.0.0:8000，直接用 `std::env::var` 读取，不经过 confique）、`AENV_API_KEY`、`AENV_LOG_*`。

---

## 7. 持久化、自动回收、指标（Part 4 后几章素材）

### 7.1 跨重启持久化（`persistence/file_backed.rs`）
- **只持久化 Paused 沙箱**，Running 状态不落盘。可靠性靠两点：优雅关闭时 `shutdown()` 把所有 Running 沙箱 pause 落盘（template builder 例外，直接删除），重启后 `load_all()` 恢复为 Paused；用户再 resume，或经代理触发 auto_resume。
- 记录格式：`PersistedPausedRecord{version:1, lifecycle: Paused|Resuming, metadata: SandboxMetadata, artifact_root, state: Value(FirecrackerSnapshotConfig 的 JSON)}`，key 为 sandbox_id，存于 RocksDB，durability=Sync（每次写都 fsync）。
- 两阶段 resume 标记：`mark_resuming` 先写 Resuming，成功后 `delete_record`，失败则 `rollback_resuming`。启动时遇到 Resuming 记录**直接丢弃记录和产物**，因为无法确定 VM 是否已经跑起来、是否改写过层。
- `load_all()` 的清理规则：版本不符、反序列化失败、`decode_paused_state` 失败（`validate_persisted()` 检查产物文件是否存在、tools_drive_version 是否为空等）都会删除记录；mode 不符的记录保留但不可恢复；没有对应记录的 `artifacts/<id>` 目录被视为孤儿并删除。
- `PausedSandboxState` 对 orchestrator 不透明（`Any` + `encode()` + `runtime_artifacts()`），解码由 factory 负责，持久层不认识 Firecracker。
- token seed 的耦合：若存在 secure 或 `allow_public_traffic=false` 的持久记录，而 managed seed 文件丢失，启动直接失败（`persisted_sandboxes_require_managed_seed()`），避免恢复后 token 失配。
- 镜像 GC 的 fail-closed 规则：启动时先为所有恢复出来的 Paused 沙箱 pin 住产物，再 `reconcile_paused`；任一步失败就不启动维护任务（宁可不 GC，也不误删）。

### 7.2 自动回收（auto-eviction）
- `start_auto_evict_task()`：每 `auto_evict_interval_ms=1000` 触发一次，`MissedTickBehavior::Skip`；持有 `Weak<Self>`，orchestrator 被 drop 后任务退出；收到 shutdown 信号退出；shutdown 期间跳过回收。
- `evict_expired_sandboxes()`：`store.list_expired(now)`（BTreeSet 范围查询）→ 只处理 Running → **先拿 `deletion_progress` 锁**（与显式删除互斥）→ `claim_expired_running_sandbox()`：在 CAS 回调里**再判一次 `is_expired(cutoff)`**，防止期间 keep-alive 延长了 TTL → 认领为 Pausing 或 Killing → 直接调用 `pause_sandbox_impl` 或 `delete_sandbox_impl(prev=Running)`。
- 回收是**串行**的，单轮遍历中逐个 await。大量沙箱同时过期时，一轮可能远超 1s（见 §8）。
- TTL 语义：`NewTimeout::Set` / `EnsureMinimum`（auto-resume 时至少 300s）/ `UseExisting` / `None`（不过期）。默认 TTL 只有 15s，与 E2B 默认一致（需结合 API 层确认）。

### 7.3 指标
- `OrchestratorMetrics`：create 成功/失败两个计数器为原子量，其余字段在 `metrics_snapshot()` 中扫描 store 现算，因此不会漂移。映射规则在 `SandboxContribution::new()`：running 计数包含 Running/Pausing/Snapshotting/Forking/Killing；starting 计数包含 Creating/Resuming；CPU 和内存按非 Paused 状态统计，Paused 单独计入 paused_*，供调度器做"含暂停沙箱"的容量上限。
- Guest 指标（`sandbox_metrics.rs`）：定时（15s）采样，或在收到 Create/Resume/Fork 事件后立即对该沙箱采样一次。并发度 `ceil(n/5)`。用 `handle.try_lock()` 取锁，锁被占用就跳过，绝不阻塞生命周期操作。在锁内生成 future，锁外 await，200ms 超时。以 proxy route 的 version 作为"代数"：采样前后代数不一致（期间发生过 pause/resume）就丢弃结果。环形保留 3600s，`sandbox_metrics_history()` 提供查询。
- 生命周期事件 broadcast 供 observability reporter 订阅，用于上报调度器。
- ublk 操作时延的 prometheus 直方图：`agentenv_ublk_operation_duration_seconds`（device.rs）。

---

## 8. 意外发现、遗留代码、TODO 与技术债

1. **FC REST 调用没有超时**：`socket.rs::UnixSocketClient::request()` 直接 `client.request(req).await`。FC 卡死时，持有沙箱 Mutex 的操作会一直挂住，只能靠 orchestrator 层 `wait_for_transition` 的 60s 让**其它等待者**放弃，持锁任务本身不会结束。
2. **`process_vm_readv` 在 tokio worker 上同步执行**（`process_vm_reader.rs` 的 TODO）。pause 大内存 VM 时会占用 worker，影响同节点其它请求。
3. **FC 子进程在 server 崩溃时可能变成孤儿**：使用了 `process_group(0)` 与 `kill_on_drop`，但 SIGKILL server 时 Drop 不会执行。重启后 `prepare_runtime` 会清理 netns 挂载，代码中未见回收残留 FC 进程的逻辑（ublk 设备由 daemon 管理）。写书时可作为"崩溃一致性边界"的讨论点。
4. 每次 resume 后旧的 `artifacts/<id>/<uuid>` 目录会**一直保留到 kill**。新快照目录通过硬链接自包含，旧目录理论上可以删除；反复 pause/resume 会累积目录（硬链接不额外占数据空间，但 vm_state 和新层是真实占用）。
5. `snapshot_to_dir()` 中非 ublk 的 rootfs 分支 `copy_cow(work_dir/rootfs.ext4)`：`ROOTFS_DRIVE_PATH="rootfs.ext4"` 现在实际指向 tools 盘的 symlink，fresh 启动又总会设置 ublk_config，所以该分支基本是**遗留死路径**。
6. `load_snapshot_uffd()` 标注 `#[allow(dead_code)]`。UFFD 方案已被"ublk 块设备 + File backend"取代（architecture.md 也写明不用 userfaultfd）。
7. `UblkBackend` 反序列化时识别旧的 `"Cow"` 后端并直接报错，要求重建（device.rs）。旧版 tools 盘使用 ext4 文件，`ensure_legacy_tools_drive` 仍在维护这条路径。
8. `config.rs::DEFAULT_BOOT_ARGS` 与 default.toml 的 `boot_args` 不一致：前者没有 `mitigations=off`、`init=/init`、`page_reporting_order`。两份 DAMON 参数需要同步维护。
9. `metrics.rs` 的文档注释称 running 计数包含 "Pausing, Snapshotting, and Killing"，代码还包含 Forking。注释过时。
10. `slot.rs` 注释说 host ns fd 取自 `/proc/1/ns/net`，代码实际用 `/proc/thread-self/ns/net`，并要求"在任何 unshare 之前首次调用"。隐含约束：首次调用 `host_ns_fd()` 的线程必须位于 host ns。
11. docs/internals/networking.md 的拓扑图写 host interaction 为 "/31 per slot"，代码实际是每个 slot 一个 /32 路由目标，该地址不配置在任何接口上。
12. docs/internals/sandbox-testing.md §4.1 写的是更新 `[firecracker]` 条目，manifest 现在已拆成 `[firecracker.kvm]` 与 `[firecracker.pvm]`。
13. 环境变量前缀不统一：`AGENTENV_MEMORY_SNAPSHOT_TRACK_DIRTY_PAGES` 与其余 `AENV_*`；`API_ADDR` 不在 confique 体系里。
14. network 池的 `pool.network.enabled=false` 只会关掉 maintenance，`release()` 仍会缓存 slot，最多到 high_watermark。所谓"禁用"并不彻底。
15. `fill_target` 只升不降：经历一次突发后，空闲的 FC 进程和 netns 会长期保留（最多 64 个），这是有意为之。
16. egress proxy 是 thread-per-connection 加 5ms 轮询 accept，每 ns 一个线程，规模大时线程数可观。域名授权只看首包，keep-alive 上后续的 Host 变更不受控（与 E2B 一致，注释已说明）。
17. 用户 egress 规则只处理 IPv4，`SandboxNetworkPolicy` 中保留的 IPv6 条目会被静默忽略（注释有说明）。
18. warm network slot 跨租户复用同一个 netns：只清空用户链和代理状态，conntrack 表与 ARP 邻居缓存不重置。存在理论上的跨租户残留，可在安全章节讨论。
19. auto-evict 串行执行且持有 `deletion_progress` 锁。大量同时过期时 pause 逐个完成，每个都要等内存导出。
20. `firecracker_client` 只生成 models，README 里 API 端点表为空。读者容易误以为"使用生成的 API 客户端"。
21. 测试覆盖：orchestrator/tests.rs 有 104 个测试，覆盖并发 pause/resume/delete、各阶段回滚、shutdown 竞态，适合作为书中"如何验证状态机"的配套材料。

---

## 9. 对章节划分的建议

**Part 2（架构）**
- 建议把 "server 启动/关闭序列" 单独成节，甚至单独一章：它串起 setup、ublk daemon、pool prime、orchestrator 恢复、shutdown 时 pause 全部沙箱，是理解"为什么只持久化 Paused"的前提。
- 对象模型一章用 §2.1 的类图，重点讲三张表（store / sandboxes / proxy_routes）的分工与锁顺序，以及 `PausedSandboxState` 的不透明设计（后端与持久化解耦）。
- 配置系统可以精简为一节加一张附录表：confique 的 env > file > default 优先级与路径占位符讲清即可，详细键值放附录。

**Part 4（Orchestrator，建议 6 章，与原计划对应但调整顺序与内容）**
1. 状态机与并发控制：CAS + watch + `run_cancellation_safe` + join_concurrent_*，配状态转换表。
2. Launch plan 与失败回滚：`launch_sandbox` 流水线、`FailedLaunchStage`、句柄 ptr_eq 防陈旧、三次 shutdown 检查点。建议**并入 fork、capture_snapshot、snapshot_volumes**，它们共享 Snapshotting/Forking 的 begin/fail/finish 模式。
3. 删除与卷的三段式提交：`DeleteProgress` 可重入删除、freeze/thaw、卷 backing 发布。原计划没有这一章，但这是 orchestrator 中最精巧的部分，建议新增。
4. 跨重启持久化：Paused-only 策略、Resuming 两阶段标记、孤儿清理、mode 兼容域、token seed 耦合、镜像 GC fail-closed。
5. Auto-eviction 与 TTL：NewTimeout 语义、过期索引、二次过期校验，并与代理 auto-resume 联动（`ProxyLookupResult::Paused`、EnsureMinimum 300s）。
6. 指标与事件：OrchestratorMetrics 现算方式、guest 采样的代数机制、broadcast 事件。
- 自定义扩展 hook 建议**挪到 Part 5**，或作为 Part 5 网络章之后的短章。它在 Firecracker 后端里被调用（start_fresh / start_resume / stop 位于 sandbox.rs），只有 patch-params 在 orchestrator，放在运行时部分叙述更自然。

**Part 5（Sandbox runtime，建议 9 到 10 章）**
1. 后端抽象与 Firecracker 进程/客户端：trait 设计、models-only client、UDS hyper、spawn（setns + 空能力集 + oom_score_adj）、完整的 fresh/resume/pause API 序列（§3.1）。
2. 块设备栈（新增，强烈建议）：ublk daemon、overlaybd runtime device、tools / rootfs / mem 共享只读设备、restack 快照、O_DIRECT 选择。后续 startup pack、内存导出、卷都依赖这一层（可与 C 部分的存储章交叉引用）。
3. 内存快照：dirty ranges → process_vm_readv → overlaybd 层 → 叠层与压缩预算 → resume 时的 File backend mmap（原计划第 8 章，建议提前，紧跟块设备章）。
4. Startup pack：录制与消费，依赖前两章。
5. MMDS 与 envd 集成：MMDS 内容少，可与 envd 合成一章（init、token、USER 解析、DualClient、busybox 运维通道）。
6. 网络 I：Slot、namespace、地址计划、iptables、宿主规则。
7. 网络 II：egress policy 语义、透明代理、可信解析、无中断策略替换。网络部分内容足以拆两章。
8. Extra drives 与 volumes：设备命名、预留 slot 热插、guest 内挂载、fsfreeze。
9. Warm pools：通用 WarmPool 与三类池，说明 FC 池只服务 resume 的原因。
10. KVM vs PVM：内容较薄（运行时没有分支），建议压缩为一节，放进 Part 9 部署或第 1 章末尾。

**Part 9（Host setup）**：三种模式 `--setup-only` / `--setup-host` / 运行时 `ensure_environment` 的分工（无特权构建、root 一次性宿主配置、非 root 运行时只做校验）；能力模型（CAP_NET_ADMIN / CAP_SYS_ADMIN、ambient 清理、线程作用域能力）；udev 规则、modules-load、sysctl。建议把 `privileges.rs` 与 `linux-cap` 放在这一章讲"最小权限"。

**建议的图**：① 对象与三张表关系图 ② 状态机图（含失败回滚边）③ create / pause / resume 时序图（orchestrator ↔ backend ↔ FC API ↔ ublk daemon ↔ envd 四条泳道）④ 磁盘布局树 ⑤ 网络拓扑与 iptables 链流向图 ⑥ egress 代理连接判定流程图 ⑦ 内存层栈演进图（fresh → pause1 → resume → pause2 → 压缩）⑧ 设备命名 vda/vdb/vdc… 与预留 slot 示意 ⑨ DeleteProgress 状态图 ⑩ WarmPool 水位与 fill_target 增长曲线。
