# D 区调研笔记：快照 / 模板 / 镜像 / P2P

> 对象：kvcache-ai/AgentENV v0.2.3（commit 6cccaa7），只读源码。
> 原则：以代码为准，docs 仅作参考；文中凡写"docs 说…"均已与代码比对，不一致处单独标注（见 §11）。
> 路径均相对仓库根。函数用 `path/file.rs::fn_name()` 记法。

---

## 0. 一句话总览

AgentENV 的"快照"是 **Firecracker VM 状态 + 内存（OverlayBD 层）+ rootfs（OverlayBD 层栈）+ 附加盘/卷（OverlayBD 层栈）** 的组合；
"模板"就是一个 `source = Template` 的快照记录，模板名就是快照 alias。
持久真相由 `SnapshotRepository`（POSIX 共享文件系统 或 S3 兼容对象存储 OSS）持有；节点本地只有可重建的派生物（runtime `image.json`、下载缓存）。
镜像侧（`src/image/`）负责把 OCI 镜像变成 OverlayBD 层栈（要么直接用 overlaybd-native 远端层，要么本地逐层转换），并有自己独立的本地 image-cache + GC。
P2P（`src/p2p/`，iroh + iroh-blobs）只是**可选加速路径**，从不承载 committed truth。

---

## 1. 模块地图（行数含测试）

### 1.1 `src/snapshot/`（合计 18,762 行）

| 文件 | 行数 | 职责 |
|---|---:|---|
| `mod.rs` | 26 | 对外导出 |
| `manager.rs` | 526 | `SnapshotManager`：仓库门面 + 提交后 best-effort P2P 发布 |
| `types/snapshot.rs` | 898 | `SnapshotRecord` / `CommittedSnapshot` / `OverlaybdLayerRef` / `RunnableSnapshot` 等对象模型 |
| `types/value.rs` | 106 | `SnapshotId`（UUIDv7）、`SnapshotAlias`（`[A-Za-z0-9_-]+`） |
| `types/version.rs` | 262 | `SnapshotRuntimeVersions`（kernel/firecracker/envd/tools_drive 版本，build 时 probe） |
| `types/drive.rs` | 179 | `CommittedAttachedDrive`（持久，仅逻辑层）vs `ResolvedAttachedDrive`（节点本地路径） |
| `types/artifacts.rs` | 25 | `SNAPSHOT_ARTIFACT_LAYOUT`：固定文件名常量 |
| `artifact_cache.rs` | 654 | `LocalArtifactCache`：节点本地 LRU + 引用计数 pin + in-flight 去重 |
| `runtime_support.rs` | 431 | `RuntimeImageMaterializer`：committed 层 → 节点本地 runtime `image.json`；`hydrate_runtime_manifest()` |
| `startup_pack.rs` | 471 | 启动内存"首触页"manifest 的描述符、解析、后台任务的关停排空 |
| `p2p.rs` | 431 | 快照制品的 P2P key 与发布/获取胶水 |
| `mock.rs` | 150 | 测试用 mock |
| `repository/interfaces.rs` | 362 | `SnapshotRepository` / `SnapshotRuntimeResolver` trait（含 volume catalog、build cache） |
| `repository/errors.rs` | 63 | `RepositoryError`（AliasConflict / ArtifactNotFound / Unsupported…） |
| `repository/build_cache.rs` | 80 | `BuildCacheState{current, retired}`：BuildKit 缓存种子 head |
| `repository/backends/mod.rs` | 192 | 按配置构造后端；builder 私有命名空间 `template-build/builder` |
| `backends/posixfs/backend.rs` | 1179 | POSIX 仓库：publish 会话编排 |
| `backends/posixfs/catalog.rs` | 1781 | POSIX catalog：records/aliases/commit marker、flock 锁、volume catalog |
| `backends/posixfs/artifacts.rs` | 1118 | 制品导入：vm_state 硬链接/拷贝、managed layer 内容寻址导入、dense export |
| `backends/posixfs/runtime.rs` | 425 | POSIX runtime resolver |
| `backends/posixfs/layout.rs` | 107 | 目录布局 |
| `backends/oss/repository.rs` | 2492 | OSS 仓库：publish/delete/alias 绑定、volume CAS、startup manifest 后台续作 |
| `backends/oss/client.rs` | 626 | OpenDAL 封装：multipart 64MiB、并发上传、凭证刷新 |
| `backends/oss/resolver.rs` | 500 | OSS runtime resolver（vm_state/manifest 先 P2P 后 OSS） |
| `backends/oss/config.rs` | 189 | OSS 配置规范化 |
| `backends/oss/layout.rs` | 48 | 对象 key 布局 |
| `backends/common/mod.rs` | 118 | volume image config 物化、dense overlaybd 导出 |
| `backends/common/recontainerize.rs` | 417 | 发布时把 raw 层重封装为 zfile（压缩），描述符跟随压缩后字节 |
| `backends/common/acr/publisher.rs` | 795 | "source-registry" 发布：把快照增量层推回源 OCI 仓库并打 tag |
| `backends/common/acr/client.rs` | 1671 | 极简 OCI registry 客户端（blob 上传、manifest put/delete） |
| `backends/common/acr/source_image.rs` | 559 | 判定 rootfs 是否"远端层 + 本地增量"可走 source-registry |
| `backends/common/acr/manifest.rs` | 397 | 构造 overlaybd 风格 OCI manifest / config |
| `image_export/service.rs` | 738 | `SnapshotImageService`：离线把已提交快照 rootfs 导出为 OCI 镜像 |
| `image_export/regctl.rs` | 370 | `regctl` 壳封装 |
| `image_export/target.rs` | 197 | 导出目标解析 |

### 1.2 `src/template/`（3,380 行）

| 文件 | 行数 | 职责 |
|---|---:|---|
| `build_spec.rs` | 349 | `TemplateBuildSpec`：步骤（RUN/ENV/WORKDIR/USER/EXPOSE/VOLUME/LABEL）、base、启动/就绪命令 |
| `builder.rs` | 848 | `TemplateBuilder`：准备 context → 执行 → publish |
| `runner.rs` | 1038 | `TemplateBuildRunner`：起临时 VM、跑步骤、补默认用户、probe 版本、capture |
| `step_executor.rs` | 529 | 逐步执行（通过 envd），维护 `CommandContext` |
| `logs.rs` | 507 | 构建日志：tracing layer 截获 + 周期 flush 到仓库 |
| `errors.rs` | 96 | 错误类型 |

### 1.3 `src/image/`（10,195 行）

| 文件 | 行数 | 职责 |
|---|---:|---|
| `resolver.rs` | 1214 | `ImageResolver::resolve()`：候选 registry → manifest → referrer 探测 → 缓存/转换 |
| `oci_image.rs` | 2475 | regctl 调用、manifest 分类（StandardOci / OverlaybdNative / Turbo 拒绝）、逐层转换流水线 |
| `cache/service.rs` | 2480 | `ImageCacheService`：commit store、hold、P2P 转换层复用、GC |
| `cache/graph.rs` | 1543 | 元数据图（RocksDB `LocalKvStore`）：HardCommit、ConfigReference、Hold、LastUsed |
| `cache/source_config.rs` | 308 | 源镜像 config 缓存文件 |
| `cache/store.rs` | 262 | 端口 trait：`SourceImageStore` / `OverlaybdLayerStore` / `RuntimeImageRefs` |
| `cache/gc.rs` | 57 | GC 报告类型 |
| `commit_index.rs` | 511 | OCI 层 → commit 的转换索引（`indexes/`） |
| `reference.rs` | 340 | 镜像引用解析、search/allowed registries |
| `buildkit.rs` + `buildkit/history.rs` | 215+490 | 从 BuildKit content store 读镜像；监听 build history |
| `metadata.rs` / `local_layer.rs` | 77/64 | 镜像基础上下文、运行时生成增量层判定 |

### 1.4 `src/p2p/`（3,320 行）

| 文件 | 行数 | 职责 |
|---|---:|---|
| `transport.rs` | 143 | `P2pTransport` trait + `DisabledP2pTransport` |
| `types.rs` | 163 | Key/Descriptor/Provider/Endpoint/PublishRequest |
| `config.rs` | 56 | `ResolvedP2pConfig` |
| `discovery/mod.rs` | 329 | `P2pPeerDiscovery`：Noop / Static / Scheduler |
| `discovery/scheduler.rs` | 265 | gRPC 调 scheduler：ListP2pPeers / Lookup/Record/ForgetP2pArtifact |
| `iroh/transport.rs` | 1773 | `IrohBlobsP2pTransport`：FsStore、Router、Downloader、门控 GC |
| `iroh/catalog.rs` | 222 | catalog ALPN `/agentenv/artifact-catalog/v1` + RocksDB 持久 catalog |
| `iroh/endpoint.rs` | 69 | iroh 地址 ⇄ `P2pEndpoint` |

相关但在区外：`src/overlaybd/p2p/{facade.rs 1450, artifact.rs 230, cache.rs 119}`（overlaybd 运行时的 HTTP range facade），`src/sandbox/firecracker/startup_pack.rs`（1433，录制 VM），`src/api/impls/image_build/*`（BuildKit 编排，~1,800 行非测试），`src/api/impls/template.rs`（1142）。

### 1.5 其他

| 文件 | 行数 | 职责 |
|---|---:|---|
| `src/digest.rs` | 133 | `FileDigest::describe()`：流式 sha256 + size；`sha256_hex/digest`、`copy_with_sha256_hex` |
| `crates/object-store-operator/` | 667 | OpenDAL S3 operator 构造 + 凭证（静态 / `credential_process`）+ 403 触发刷新重试 |
| `src/bin/aenv-snapshot-image.rs` | — | 独立导出工具入口 |
| `config/buildkit-version` | 1 | `v0.33.0`（默认 builder 镜像 `docker.io/moby/buildkit:v0.33.0`） |
| `tools-image/` | — | **注意：这是 envd tools drive（/dev/vda）的构建源，不是 BuildKit 相关** |

---

## 2. 第 7.1 章：SnapshotManager 与快照对象模型

### 2.1 要解决的问题
一个"可恢复的 VM 检查点"由多类异构制品构成，其中大部分（层）可跨快照共享、体积巨大；而记录（元数据）需要可列出、可别名、可跨节点读取。还要支持"模板构建尚未完成"的中间态。

### 2.2 对象模型（`src/snapshot/types/snapshot.rs`）

```
SnapshotRecord                      ← 目录项（catalog/records/{id}.json）
├─ id: SnapshotId (UUIDv7)
├─ alias: Option<SnapshotAlias>     ← 模板名 / 快照名
├─ source: SnapshotSource
│    ├─ Template { build: TemplateBuildInfo{status: Waiting|Building|Ready|Error, started/finished, error_reason{message, step}} }
│    └─ Sandbox  { source_sandbox_id }
├─ resources: SandboxResources (cpu, mem, disk_size_mib)
├─ created/updated_at_unix_ms
└─ committed: Option<CommittedSnapshot>   ← None = 未完成的模板构建
     ├─ context: CommandContext (env, workdir, user, ports, entrypoint, cmd, volumes, labels)
     ├─ startup: Option<StartupCommand{start_cmd, ready_cmd, context, shell}>
     ├─ runtime_versions, virtualization_mode, image_configs (OCI config JSON 原样)
     ├─ rootfs_layers: Vec<OverlaybdLayerRef>
     ├─ attached_drives: Vec<CommittedAttachedDrive::Overlaybd{drive_id, layers, read_only, virtual_size, mount_path, sub_path}>
     ├─ volume_snapshots: Vec<SnapshotVolume{mount_path, mode, size_mb, layers}>
     ├─ memory_layers: Vec<ManagedLayer>
     ├─ disk_publications: Vec<PersistedDiskImagePublication{image_ref, tag, manifest_digest, repo_blob_url}>
     ├─ custom_extension_params
     └─ memory_startup: Option<MemoryStartupPackInfo{pack_size, mem_virtual_size, index_sha256}>

OverlaybdLayerRef = Managed(ManagedLayer{digest, size, uuid?})      ← 仓库自管、内容寻址
                  | External(ExternalLayer{digest, repo_blob_url, size}) ← 仍在源 registry（overlaybd-native）
```

关键设计点：
- **committed 记录只存"逻辑层引用"，不存任何节点本地路径**。`SandboxSnapshotManifest` 中的 `path` 字段全部 `#[serde(skip)]`（`src/sandbox/manifest.rs`），持久化的 `firecracker-manifest.json` 只有虚拟大小、drive 槽位等形状信息。
- `RunnableSnapshot{record, manifest(已 hydrate 本地路径), _lease: Arc<dyn RuntimeArtifactLease>}`：lease 是"持有即 pin"的 RAII，把本地缓存文件钉住直到 sandbox 释放。
- `SnapshotId::generate()` 用 `Uuid::now_v7()`，天然按时间排序；注释警告大写 UUID 会导致 PosixFs 查找 miss。
- `TemplateBuildErrorReason` 自定义 Deserialize 兼容旧格式（纯字符串）。`step` 必须是 1-based 数字字符串——e2b SDK 会把它当栈索引解析，否则 Python SDK 崩（`step_executor.rs::execute()` 注释）。
- `rootfs_snapshot_image_tag()` = `agentenv-snapshot-{id}`。

### 2.3 一个快照由哪些制品组成（名字与位置）

固定名来自 `types/artifacts.rs::SNAPSHOT_ARTIFACT_LAYOUT`：

| 制品 | 捕获时（本地 capture 目录） | POSIX 仓库 | OSS 对象 key | 节点运行时 |
|---|---|---|---|---|
| 记录 | — | `catalog/records/{id}.json` | `catalog/records/{id}.json` | — |
| 别名 | — | `catalog/aliases/{alias}`（内容是 id 的 JSON）+ `.lock` | `catalog/aliases/{alias}.json` | — |
| 提交标记 | — | `snapshots/{id}/commit`（内容 `committed`） | 无（记录本身即提交点） | — |
| VM 状态 | `vm_state.bin` | `snapshots/{id}/vm_state.bin` | `artifacts/{id}/vm_state.bin` | POSIX 直接引用仓库文件；OSS 下载到 `<local_cache>/artifacts/{id}/vm_state.bin` |
| FC manifest | （内存对象） | `snapshots/{id}/firecracker-manifest.json` | `artifacts/{id}/firecracker-manifest.json` | hydrate 后的内存对象 |
| 内存层 | `mem_overlaybd/overlaybd.commit` + `mem_image.json` | `managed-layers/{digest 中 :/ 换 _}.overlaybd.commit` | `managed-layers/{sha256:…}` | `<local_cache>/runtime/{id}/memory/image.json` |
| rootfs 层 | `rootfs/snapshot.commit`、`rootfs/inherited-layers/…`、`rootfs/image.json` | 同上 managed-layers（或 External 留在 registry） | 同上 | `runtime/{id}/rootfs/image.json` |
| 附加盘 | `drives/{drive_id}/…` | 同上 | 同上 | `runtime/{id}/drives/{drive_id}/image.json` |
| 启动 manifest | `memory-startup.trace`（本地 trace，永不上传） | `snapshots/{id}/memory-startup.pack` | `artifacts/{id}/memory-startup.pack` | 按需 |
| 构建日志 | — | `snapshots/build-logs/{id}.json` | `snapshots/build-logs/{id}.json` | — |
| ACR 发布 | — | — | 源 registry 中 `:agentenv-snapshot-{id}`（及 drive tag） | — |

"三层存储"模型（docs/persistence-artifact-inventory.md 的总结与代码一致）：①builder/capture staging（临时、manager 所有）②committed repository（持久真相）③node-local runtime cache（派生、可重建）。

### 2.4 `SnapshotManager`（`src/snapshot/manager.rs`）
薄门面，方法几乎都直通 repository：`create / get / list / delete / resolve_committed_alias / try_start_build / mark_build_error`；`resolve_runnable()/load_runnable()` 走 `SnapshotRuntimeResolver`。
唯一自己的逻辑：`publish()` / `publish_captured()` → `repository.publish_with_local_layers()` → **成功后** `publish_p2p_artifacts()`（并发 8，失败只 warn）。测试 `failed_repository_commit_does_not_publish_to_p2p` 与 `failed_p2p_publication_does_not_undo_repository_commit` 锁定了"P2P 不影响提交"的不变量。
`publish_captured()` 在调用仓库前先 `StartupRecording::spawn_with_capture_lease()` 启动"录制 VM"，让录制与层上传并行。

注释声明的设计立场：committed 快照**不 pin** 节点本地 image-cache（`image-cache/commits/`）；本地层缓存可回收，持久可达性完全由 repository 负责。

### 2.5 两条进入路径
- 运行中 sandbox → 快照：`src/api/impls/sandbox.rs::sandboxes_sandbox_id_snapshots_post()` → `orchestrator.capture_snapshot()`（`FirecrackerSandbox::snapshot()`：`pause_to_dir()` 到 managed-snapshots 目录 → 立即 `resume()`）→ `snapshot_sandbox_volumes()` → `SnapshotManager::publish_captured()`。
- 模板构建 → 快照：见 §7。

### 2.6 建议图
- 图 7-1：对象模型 UML（Record / Committed / LayerRef 两种变体 / Runnable+Lease）。
- 图 7-2："三层存储"示意：capture staging → repository → runtime cache，标注哪些文件在哪层、谁拥有生命周期。

---

## 3. 第 7.2 章：仓库后端（POSIX / OSS）与提交协议

### 3.1 后端选择（`repository/backends/mod.rs::build_snapshot_backend_from_config()`）
- `snapshot.repository_backend = posix_fs`（默认）：根 = `<backend.posix_fs.snapshot_store>/repository`，可放 NFS 等共享 FS。
- `= oss`：S3 兼容对象存储（名为 OSS，实际为 OpenDAL `services-s3`，阿里云 OSS 是主目标）。`snapshot.image_publish.enabled=true` 时启用 `SnapshotImageStoragePolicy::SourceRegistry`。
- 两者都配一个 `LocalArtifactCache`（根 = `snapshot.local_cache_path`，OSS 可设 `cache_max_size_gb`，默认 10GB）。
- `build_builder_snapshot_backend()`：BuildKit builder 快照使用同一后端的**私有命名空间** `template-build/builder`（POSIX 子目录 / OSS 前缀 / 本地缓存子目录），公共模板 API 看不见、删不掉（测试 `builders_share_a_private_catalog_across_node_local_caches`）。

### 3.2 POSIX 提交协议（重点）
入口 `posixfs/backend.rs::PosixFsSnapshotRepository::publish_sync()`（在 `spawn_blocking` 里跑）：

1. 校验：attached drive id 去重、`virtual_size != 0`。
2. `catalog.begin_publish()`：`mkdir -p snapshots/{id}/`。
3. `artifacts.import_built_artifacts()`：
   - `copy_local_artifact()`：`vm_state.bin` 优先 `hard_link`（并 chmod 只读 + fsync），失败则 `copy_file_with_sha256()`（边拷边算 sha256，写完 `sync_all` 后**再读一遍目标比对**）。校验 size。
   - `persist_firecracker_manifest()`：`fs::write`（注意：非原子、无 fsync）。
   - `derive_memory_layers()` / `derive_rootfs_layers()`（rootfs 与每个 drive）：解析本地 `image.json` 的 `lowers`：
     - 有 `file` 且有 `digest+size` → `import_managed_layer_with_descriptor()`：**信任描述符**，仅校验 size；若是稀疏层则 `store_sparse_overlaybd_layer_dense()` 先 dense 导出再按新 digest 存。
     - 有 `file` 无描述符，且是运行时生成的增量层（`image::local_layer::rootfs_layer_is_runtime_generated_delta`）→ 现场 hash 导入。
     - 无 `file` 但有 `repoBlobUrl` → `External` 引用（不复制）。
     - 否则 `Unsupported`。
   - `store_managed_layer()`：目标 `managed-layers/{digest}.overlaybd.commit` 已存在则只比 size（内容寻址天然去重）；否则 hard link 或 temp+`persist_noclobber`，`sync_dir`。
4. `catalog.commit_publish()`（`posixfs/catalog.rs`，注释给出顺序）：
   1. 若有 alias：取 alias 文件锁（`flock` 非阻塞 + 25ms 轮询，最长 10s）；
   2. 若 alias 指向另一个**仍存在**的记录 → `AliasConflict`；指向已删记录 → 清掉陈旧 alias；
   3. 写 alias 文件 → 写 `commit` marker → 写 committed record（`write_json` = 临时文件 + `sync_all` + `persist`(rename)）。
   4. 任一步失败：回滚 alias（仅当仍指向自己）+ `cleanup_uncommitted_snapshot_dir()`。
5. import 失败 → `abort_publish()` 删 `snapshots/{id}/`（仅当 `!is_committed()`）。

**可见性判据**：读路径 `get()` 只看 `catalog/records/{id}.json` 是否存在；`is_committed()` = marker 存在 **且** record.committed 有值。alias 先于 record 写入，因此读者可能看到"alias→不存在的 record"，`get()/resolve_alias()` 在 alias 锁下**惰性清理陈旧 alias**。

锁：per-alias `catalog/aliases/{alias}.lock`、per-record `catalog/records/{id}.lock`（无全局锁）；`try_start()`（Waiting→Building）、`mark_error()`、`delete_record()` 都在 record 锁下做 read-modify-write，因此 POSIX 上模板构建状态转换是真 CAS。

删除 `delete_record()`：record 锁 → 删 build log → alias 锁 → 删 commit marker → 删 alias（若指向自己）→ 若 committed 删整个 `snapshots/{id}/` → 删 record。**managed-layers 从不删除。**

### 3.3 OSS 提交协议（`oss/repository.rs::publish_with_local_layers()`，注释带编号）
0. 校验 drive；`validate_publish_manifest_image_configs()` 预检。
1. `export_disk_image(Rootfs)`：
   - `ObjectStorage` 策略 → `derive_and_upload_disk_image_layers_mode()`：逻辑同 POSIX，但导入=上传到 `managed-layers/{digest}`（`upload_managed_layer_if_missing()`：先 `exists()` 再**无条件** `put_file`；注释解释：内容寻址使 TOCTOU 无害，且阿里云 OSS 在 multipart 路径不支持 `x-oss-forbid-overwrite`）。
   - 启用 `publish_compression` 时，`recontainerize::prepare_layer_upload()` 把 raw 层压成 zfile 再传，**digest/size/对象 key 都描述压缩后字节**；本地层保持 raw（本地 resume 不付解压代价）。
   - `SourceRegistry` 策略 → `AcrDiskImageExporter::export()`（§5.2）；若返回 `Unsupported` 且回退不会"混源"（`fallback_to_object_storage_would_mix_sources()`）则回退 managed。
2. 内存层 `derive_and_upload_memory_layers()`；上传 `vm_state.bin`、`firecracker-manifest.json`。
3. attached drives 逐个 `export_disk_image()`。
4. 组装 `CommittedSnapshot`（`memory_startup = None`，启动 manifest 完全解耦）。
5. `bind_alias()`：**不是原子 CAS**——读 alias → 冲突/陈旧判断 → 无条件写 → 回读校验是否"赢了"，输了重试或报冲突。注释承认"弱于真 CAS，但同 alias 并发发布罕见"。
6. `write_committed_record()`：读已有 record（模板 Waiting 记录）→ `mark_committed()` → 写回。**记录对象写入即提交点**。
- 失败回滚：`delete_prefix("artifacts/{id}/")` + 逆序 `rollback_publication()` 删除已推送的 registry manifest；managed layers 故意保留（"shared across snapshots and require separate GC"——但这个 GC 并不存在，见 §11）。
- 成功后若 `memory_startup_pack.enabled`，`tokio::spawn(finish_startup_manifest())`（§4.3）。

OSS 删除 `delete()`：alias（若指向自己）→ build log → record → best-effort 删 registry 发布 → `delete_prefix(artifacts/{id}/)`。先删 record 再删制品，读者不会看到半删除的已提交快照（但会留孤儿制品）。

### 3.4 OSS 客户端与凭证（`oss/client.rs`、`crates/object-store-operator`）
- multipart chunk 64MiB × 10000 part 上限 ≈ 625GiB 单对象；注释记录实测内存 1040MiB（`(2*并发+2)*chunk`），并说明"故意不缩小 chunk，否则最大对象也缩小"。
- `managed_layers_repo_blob_url()` 产出 `s3://…` 形式（即使是阿里云 OSS），供 overlaybd 运行时直接按需读取 managed 层。
- `object-store-operator`：`build_object_store_operator()`（S3 builder + Timeout 30s + Retry 3）；凭证来源：静态 AK/SK/STS 或 `credential_process`（外部命令输出 JSON，30s 超时，提前 120s 刷新）；`run_with_refresh()` **只在 PermissionDenied 时**强制刷新并重试一次（注释：阿里云 OSS 过期凭证表现为 403）。该 crate 同时被 `storage/overlaybd/src/backend/oss.rs` 复用。

### 3.5 一致性对比表（可做成书中表格）

| 维度 | POSIX | OSS |
|---|---|---|
| 提交点 | record JSON rename（marker 先写） | record 对象 PUT |
| alias 绑定 | flock 下检查+写，真互斥 | 读-写-回读，尽力而为 |
| 模板 Waiting→Building | record flock 下 RMW，原子 | 普通 RMW，**非原子**（trait 文档声称 Atomically） |
| startup 描述符 attach | record 锁下，不能复活已删记录 | RMW，删除并发时可能复活（注释承认） |
| volume / build-cache head | flock | ETag `if_match`/`if_none_match` 条件写（真 CAS） |
| 层去重 | 文件存在即跳过（只比 size） | `exists()` 后无条件 put |
| 失败回滚 | 删 `snapshots/{id}/` | 删 `artifacts/{id}/` 前缀 + registry manifest |
| managed 层 GC | 无 | 无 |
| P2P 读路径 | 不消费 | vm_state / manifest 先 P2P |

### 3.6 建议图
- 图 7-3：POSIX publish 时序（begin → import(hardlink/copy/dense) → alias lock → alias → marker → record；各步失败回滚箭头）。
- 图 7-4：OSS publish 时序（layers ↑ / vm_state ↑ / manifest ↑ / bind_alias 回读 / record ↑ / 后台 startup manifest）。
- 图 7-5：仓库目录树 / 对象 key 树并排。

---

## 4. 第 7.3 章：运行时解析、本地制品缓存与启动内存包

### 4.1 Resolve 流程
`SnapshotManager::load_runnable(id_or_alias)` = `get()` + `SnapshotRuntimeResolver::resolve()`。

POSIX（`posixfs/runtime.rs::PosixFsRuntimeResolver::resolve()`）：
1. 要求 `committed` 非空；`vm_state.bin` 直接用仓库路径（不拷贝）；读仓库里的 `firecracker-manifest.json`。
2. 物化 memory / rootfs / 每个 drive 的 runtime `image.json`：managed 层 → `LayerConfig{file = 仓库 managed-layers 路径}`（**overlaybd 直接读共享 FS 上的层文件**）；External 层 → `repoBlobUrl`。
3. `hydrate_runtime_manifest()`：把本地路径填回 manifest，并 `with_extra_drives()`。
4. 若 `memory_startup_pack.consume_enabled` 且记录有描述符且文件存在 → `resolve_local_startup_pack_ref()`。
5. 所有 `CacheHandle` 打包成 `CacheArtifactLease` 放进 `RunnableSnapshot`。

OSS（`oss/resolver.rs::OssRuntimeResolver::resolve()`）：
1. `vm_state.bin`：`LocalArtifactCache::ensure_cached()`，fetch 闭包内**先 P2P `fetch_artifact()`，失败回退 `client.get_to_file()`**（temp+rename 原子）。
2. manifest：先 P2P `fetch_artifact_bytes()` + 解析，失败/解析错回退 OSS `get_bytes()`。
3. 层**不下载**：`validate_managed_layers()`（并发 16 个 `exists()` 校验存在）后写 image.json，lower 只有 digest/size/uuid，`repoBlobUrl = s3://bucket/prefix/managed-layers`，运行时 overlaybd 按需拉取。
4. 启动包引用 `resolve_startup_pack_ref()` → `OssUrl`。

`runtime_support.rs::materialize_image_config()` 细节：
- 若所有远端 lower 的 `repoBlobUrl` 一致，写到顶层 `repo_blob_url`（保持旧格式）；混合后端时逐层写 `repo_blob_url`。
- `attach_local_layer_location()`：由 `OverlaybdLayerStore::layer_location(digest,size,has_remote)` 决定 `file=`（本地唯一副本，无回退）还是 `dir=`（overlaybd cache 目录，可回退远端，可被回收）。
- `write_image_config()`：写 `.tmp` 再 rename。

### 4.2 `LocalArtifactCache`（`artifact_cache.rs`）
- 不变量（注释）：`ref_count>0` 不驱逐；同 key 只有一个 in-flight fetch（`watch` 通道广播结果，失败也广播）；内容都是可重建的派生物。
- `ensure_cached_at(key, path, fetch)`：已索引→pin；文件已在磁盘→`pin_local_file()`（重启后复用）；否则登记 in-flight、执行 fetch、登记大小、超限时后台 `evict_lru()`（降到 80%）。
- key→路径做路径穿越检查。
- 注意：索引纯内存，重启后磁盘上未被再次触碰的旧文件**不计入容量也不会被驱逐**（见 §11）。

### 4.3 启动内存包（startup pack / startup manifest）
目的：resume 后首批内存缺页如果都走远端按需读会很慢；预先记录"首触页"顺序，resume 时预取。
- 录制：`src/sandbox/firecracker/startup_pack.rs::record_startup_pack()`——从刚捕获的快照**再启动一个一次性 VM**，用专门的内存设备让 daemon 侧记录每个首次读，产出 `memory-startup.trace`；窗口参数 `record_min_window_ms=200 / quiet_ms=300 / max_window_ms=2000 / budget_secs=10`；全程 best-effort。
- 构建：`snapshot/startup_pack.rs::build_startup_manifest()` 把 trace 解码并编码为 **v4 startup manifest**（精确顺序前缀 + 合并区间），`MemoryStartupPackInfo{pack_size, mem_virtual_size, index_sha256}`。注释强调"不读、不打包、不上传任何层字节"，消费方按 manifest 走正常读路径预取。
- 持久化：POSIX `catalog.attach_memory_startup()`（先写验证过的制品，再在 record 锁下挂描述符；"不是多文件事务"，重试可修复孤儿/缺失）；OSS `finish_startup_manifest()` → 上传 `artifacts/{id}/memory-startup.pack` → `attach_memory_startup_descriptor()` RMW（记录已删则放弃）。
- 生命周期：`StartupRecording{trace JoinHandle, keep_alive}` 持有 capture 目录 lease，使录制/上传可以比同步 publish 活得久；进程全局 `StartupManifestShutdown`：关停时先禁止新任务、有界等待排空、超时发 abort（`drain_startup_manifest_tasks()`）。
- 开关：`[snapshot.memory_startup_pack] enabled`（录制，默认 false）与 `consume_enabled`（消费，默认 false）独立，便于 A/B。

### 4.4 建议图
- 图 7-6：resolve 数据流（record → 三个 image.json + vm_state + manifest → hydrate → RunnableSnapshot + lease）。POSIX/OSS 两列对照。
- 图 7-7：startup pack 时间线：capture → 源 sandbox resume → 录制 VM 与层上传并行 → record 提交 → 后台 manifest 上传 → 描述符 attach。

---

## 5. 第 7.4 章：把快照 rootfs 发布为 OCI 镜像

两条独立机制，容易混淆，书中应分开讲。

### 5.1 离线导出：`aenv-snapshot-image`（`src/snapshot/image_export/`）
- `SnapshotImageService::from_global_config()`：**刻意跳过** runtime resolver、artifact cache、layer store、P2P，只构造 repository + 层定位器（POSIX 根 / OSS client）。
- `export_rootfs_image(id_or_alias, target_repository, tag)`：拒绝不存在或未 committed 的记录 → `resolve_snapshot_image_target()`（显式目标，或从 External 层/已有 publication 推断唯一源仓库）→ `publish_committed_rootfs()`。
- 确定性：config blob（`snapshot_oci_config_blob()`，含快照的 env/workdir/entrypoint 等）和 manifest 都是确定的，**manifest digest 唯一标识镜像**：目标已有同 digest → `reused`；同 tag 不同 digest → 冲突拒绝；否则只上传目标缺的 blob（先 `blob head`）。
- 层来源：External 同 registry 用 `blob copy`（mount），跨 registry 用 `blob get | blob put` 管道；Managed 层 POSIX 原地校验、OSS 下载到 tempdir（校验 size）。
- 只导出 rootfs；**内存、附加盘、VM 状态都不参与**，所以产物只能 cold start。

### 5.2 发布时自动推回源 registry（`backends/common/acr/publisher.rs::AcrDiskImageExporter::export()`）
- 条件：OSS 后端 + `image_publish.enabled` + rootfs 源自 overlaybd-native 镜像（`load_source_registry_image()` 要求 lower 是"远端 https registry 层 + 本地增量"形态）。
- 流程：`ensure_manifest_absent(tag)` → 远端层直接引用、本地增量（可 zfile 压缩）上传为 blob → 上传 config → `put_manifest(tag = agentenv-snapshot-{id})` → 返回 `PersistedDiskImagePublication`，且 committed 层全部记为 `External`（字节住在 registry，不进 OSS managed-layers）。
- manifest 格式：layer mediaType 是 `application/vnd.oci.image.layer.v1.tar`，但内容是 overlaybd blob，用 `containerd.io/snapshot/overlaybd/blob-digest|blob-size` 注解标识（accelerated-container-image 的 overlaybd-native 约定），另加 `io.agentenv.snapshot.tag`。
- 回滚/删除：`rollback_publication()` 按 manifest digest 删除；失败"留给 registry GC"。
- 命名："acr"=阿里云容器镜像服务，但客户端是通用 OCI registry（`AcrClient::from_docker_config`）。

### 5.3 建议图
- 图 7-8：两条路径对比（离线导出 vs 发布时推回），标注层字节流向与是否保留内存。

---

## 6. 第 7.5 章：Fork——一个运行中的 sandbox 变成多个

### 6.1 端到端链路
1. API：`src/api/impls/sandbox.rs::sandboxes_sandbox_id_fork_post()` → `prepare_volume_fork_specs()`：对每个 child、每个挂载的 `exclusive` 卷创建一个 CoW 卷 fork（`volume-fork-{uuid}`），`ro` 卷共享；失败则 `cleanup_fork_volume_children()`。
2. 编排：`src/orchestrator/service.rs::fork_sandbox_with_specs()` → `run_cancellation_safe("fork", …)` → `fork_sandbox_inner()`：校验 child id 唯一且不同于源 → 源状态置 `SandboxState::Forking` → `sandbox.fork(&backend_specs)` → 恢复源状态 → 逐个注册 child（失败的 child `stop_failed_fork()`）→ 发 `SandboxLifecycleEventType::Fork` 事件。返回 `Vec<SandboxForkOutcome>`（每 child 独立成败）。
3. 后端：`src/sandbox/firecracker/sandbox.rs::FirecrackerSandbox::fork()`：
   - `FirecrackerSandbox::pause()`：在 `managed-snapshots/{sandbox}/{uuid}/` 下 `pause_to_dir()`（同步可写卷文件系统 → FC pause → 写 vm_state + 内存层 + rootfs/drive restack 封存层），`managed_snapshot_root` 随 config 存活。
   - **立刻 `resume()` 源**（源只停顿一次 capture 的时间）。
   - 对每个 child：`snapshot_config_for_fork()`（可把 launch-time 卷 drive 替换为该 child 的 CoW 卷；不允许替换物理 drive、不允许追加 drive——"cannot append drive to captured Firecracker state"）→ `from_snapshot_config_with_override(config, child_id, envd_access_token)` → **并发** `start()`；单个失败不影响兄弟。
4. 契约（`src/sandbox/backend.rs::SandboxBackend::fork()` 文档）：外层错误只用于 child 启动前的失败；`SandboxCaptureError::Terminal` 表示源已不可安全恢复。

### 6.2 语义要点
- **fork 完全不经过 SnapshotRepository**：没有 record、没有上传、没有 alias；纯同节点内存中快照，children 与源共享封存的只读 lower（内存层、rootfs 层），各自拿新的可写 upper。
- 因而 fork 只能同节点（orchestrator 注释 "on the same node"）；跨节点"分叉"需走 snapshot create + 在其他节点 start。
- 身份：child 的 sandbox id、envd access token 覆盖快照里的值（`from_snapshot_config_with_override` 注释 "Runtime identity and auth override"）。网络/MMDS 等的重写在该函数后续部分（区外，属 sandbox 章节）。

### 6.3 fork vs snapshot vs pause 对照（建议成表）
| 操作 | 落盘位置 | 是否进仓库 | 源 sandbox | 跨节点 |
|---|---|---|---|---|
| pause | `persisted-sandboxes/artifacts/{id}/{uuid}` 或 managed root | 否 | 停止 | 否 |
| snapshot | managed-snapshots → publish | 是 | 恢复运行 | 是 |
| fork | managed-snapshots（内存中 config 持有） | 否 | 恢复运行 | 否 |

### 6.4 建议图
- 图 7-9：fork 时序（API 卷 fork → Forking → pause/capture → resume 源 → N 个 child 并发 start → 注册）+ 层共享示意（共享 lower，独立 upper）。

---

## 7. 第 7.6 章：模板构建器（步骤式 / 镜像式）

### 7.1 状态机与 API（e2b 兼容）
- `POST /v3/templates`（`template.rs::v3_templates_post()`）：生成 id，`SnapshotRecord::template_waiting()` → `SnapshotManager::create()`（仅允许 Template 源、未 committed、alias 可用）。template_id == build_id（"AgentENV compatibility mode"）。
- `POST /v2/templates/{tid}/builds/{bid}`（`v2_templates_template_id_builds_build_id_post()`）：解析 base（默认镜像 / 指定镜像 / 已有模板）→ `try_start_build()`（Waiting→Building）→ 后台 spawn：
  - 镜像 base：`resolve_template_rootfs_image()` → `TemplateBuildSpec::with_resolved_overlaybd_image()` → `TemplateBuilder::build_and_publish_with_id()`。
  - 模板 base：`load_runnable(alias)` → `build_from_snapshot_and_publish()`。
  - 任一失败 `mark_build_error()`。成功即 publish 把 Waiting/Building 记录 `mark_committed()` 成 Ready。
- 状态：Waiting → Building → Ready | Error。

### 7.2 Builder（`src/template/builder.rs`）
- `prepare_fresh_context()`：要求 rootfs base；`prepare_base_rootfs()` 只接受 `Overlaybd{image_config_path, image_configs}`，**`Ext4` 直接报错**（"overlaybd-only publish mode"）。workspace = `tempfile` 目录 `snapshot-{id}-*`。
- `prepare_snapshot_base_context()`：目标 id ≠ base id；不能覆盖 rootfs；virtualization_mode 必须与节点一致；**不能改 CPU/内存**（因为是从内存快照 resume）；继承 base 的 context 和 startup（未覆盖时），alias 不继承；custom_extension_params 不传播（"per-sandbox 用户设置，不是镜像内容"）。
- `execute_and_publish()`：`spawn_blocking` 跑 runner → `disk_size_mib` 由 rootfs virtual_size 推得 → 启动录制（与上传并行）→ `SnapshotManager::publish(... source: Template ...)`。

### 7.3 Runner（`src/template/runner.rs`）
`build_template()`（镜像 base）：`FirecrackerSandboxConfig::from_global_config_with_user_image()`，rootfs 用 `UpperMode::LogStructured` 可写 upper，注入 cpu/mem/cpu_config（集群 CPU 交集模板）/env/user/workdir。
`build_template_from_snapshot()`：`FirecrackerSandbox::from_snapshot(base)`，沿用 base 的 tools_drive_version。
`run_template_build()`（独立 OS 线程 + current-thread tokio runtime）：
1. `sandbox.start()`
2. `StepExecutor::execute()`：RUN 经 envd 执行；ENV/USER/EXPOSE/VOLUME/LABEL 只改 `CommandContext`；WORKDIR 解析为规范化绝对路径并**通过 envd 文件系统服务创建目录**（不 exec mkdir，兼容 scratch/distroless）。
3. `ensure_default_user()`：镜像缺 USER 指定的账户/组时自动创建（e2b SDK 假设默认用户存在）；无 useradd/adduser 工具只告警（退出码约定），工具存在却失败则构建失败。
4. `prepare_startup()` + `run_startup_commands()`：start_cmd 后台跑，ready_cmd 轮询（默认 ready 与 E2B 一致）。
5. `SnapshotRuntimeVersions::probe()`（envd --version、uname、VMM 二进制版本）。
6. `capture_to_dir(workspace)` → `SandboxSnapshotManifest` + capture payload；最后无论成败 `stop()`。

**每个步骤都在 Firecracker microVM 中执行，没有容器、没有逐步层缓存**；整个构建结果只产生一个快照（一个 rootfs 增量层 + 内存层）。

### 7.4 构建日志（`src/template/logs.rs`）
tracing Layer 只截获匹配 build span 的 agentenv 事件 + 进程输出；周期 flush，`write_build_logs()` "原子替换完整日志文件"（POSIX `snapshots/build-logs/{id}.json`，OSS 同 key）；有条数上限并只发一次截断提示。

### 7.5 建议图
- 图 7-10：模板构建状态机 + API 调用对应。
- 图 7-11：Runner 内部：VM 启动 → 步骤 → 默认用户 → 启动/就绪 → probe → capture → publish（并行录制）。

---

## 8. 第 7.7 章：BuildKit（`aenv build`，Dockerfile）

### 8.1 架构：BuildKit 跑在 microVM 里，buildctl 在 CLI 本地，经 WebSocket 隧道相连
- CLI（`crates/aenv/src/commands/build.rs`、`client/buildkit.rs`）：使用随 aenv 安装的 `aenv-buildctl`，在本地 unix/tcp socket 上 `bind_local()`，每条连接经 WebSocket 桥到服务器 `/templates/{tid}/builds/{bid}/builder`；输出 `--output type=image,name={image_name},oci-mediatypes=true`（镜像留在 builder 的 content store，不推 registry）。
- 服务器隧道（`src/api/impls/image_build/transport.rs`）：每 build 最多 8 条并发连接（buildctl 需多连接），WebSocket ↔ builder VM 内 `:1234` TCP。

### 8.2 服务器流程（`src/api/impls/image_build.rs`、`worker.rs`、`cache.rs`）
1. `start_image_build()`：同步 `BuildSessions::reserve()`（节点并发上限 `template_build.max_concurrent_builds` 默认 4，超出 429）；`allocate_image_build()` 经仓库 `try_start_build()` "CAS" 排除其他节点重复启动；写本地 journal（`LocalKvStore`）便于重启恢复。
2. `builder_template()`：进程内 `OnceCell` 共享初始化。`initialize_builder_template()`：alias = `builder-{sha256(1, builder_image, cpu, mem, BUILDER_READY, virt_mode)}`，在**私有 builder 命名空间**查找；没有则 `image_resolver.resolve(builder_image)` 并用普通 `TemplateBuilder` 构建一个 builder 模板快照（ready_cmd 检查 buildkitd/buildctl 存在）；多节点并发首次准备时 `AliasConflict` 视为别人赢了，直接复用。
3. `prepare_builder()`：`fork_build_cache()` 从当前缓存种子（`BuildCacheState.current`）派生一个可写卷，挂到 `/var/lib/buildkit`；`orchestrator.create_template_builder()` 从 builder 快照**热启动**一个 secure、禁公网的内部 sandbox（不出现在公共列表）。
4. `worker_command(START_BUILDKIT)` → `BuildkitHistory::wait_for_image()`：监听 BuildKit history API，靠"本 build 唯一 exporter name"识别自己的记录（缓存种子里有旧 history），同时把 status 流写进构建日志，拿到镜像 digest。
5. 导入：`BuildkitContent::connect()` + `ImageResolver::resolve_buildkit()`——经 BuildKit content API **按 sha256 读取并校验**镜像（metadata ≤4MiB、镜像 ≤64GiB），只转换缺失的层（复用 §9 的内容寻址 OverlayBD 缓存）。
6. `release_builder()`：`STOP_BUILDKIT`（成功才认为缓存可用）→ 删除 builder sandbox（不保存其内存/rootfs/设备状态）→ 卷状态 Ready 才算 `cache_ready`。
7. 用导入的 overlaybd 镜像跑一次普通模板构建 `build_and_publish_with_id()`：start_cmd = 请求值或 ENTRYPOINT/CMD（`CommandContext::effective_start_cmd()`），ready_cmd = 请求值或 Dockerfile `HEALTHCHECK`（`dockerfile_ready_command()`，支持 CMD/CMD-SHELL/NONE 与 SHELL）。只有最终镜像 config 进入模板，中间 stage / build-arg 不会。
8. `publish_build_cache()`：缓存卷经常规卷捕获发布（只传缺失层），`replace_build_cache_head()` 原子写"新 head + 把旧 head 放进 retired"；失败不影响构建成功、保留旧种子。`collect_retired_build_caches()` 在子租约释放后删除旧卷，`forget_retired_build_cache()` 确认退役。
9. 取消/超时：`cancel_image_build()`、deadline（默认 3600s）→ 释放 worker、丢弃未完成的缓存子卷；重启后从 journal 恢复；失败清理在运行期重试。

### 8.3 缓存语义（docs 与代码一致）
"线性继承、并发不合并、最后成功者成为下一个种子"。BuildKit 自身 GC 管理缓存内容；`template_build.cache_size_mb` 默认 65536。

### 8.4 建议图
- 图 7-12：组件图（CLI buildctl ⇄ WS 隧道 ⇄ API ⇄ builder VM(buildkitd, /var/lib/buildkit=缓存卷) ；content API → ImageResolver → overlaybd → TemplateBuilder → 仓库）。
- 图 7-13：缓存种子演进（seed₀ → fork → build → publish → seed₁，并发分支示意被丢弃）。

---

## 9. 第 7.8 章：镜像拉取与 OCI→OverlayBD 转换

### 9.1 `ImageResolver::resolve(image_ref)`（`src/image/resolver.rs`）
1. `image_ref_candidates()`：短名按 `search_registries` 展开，受 `allowed_registries` 约束（None=不限、`[]`=全拒）。
2. 对每个候选 `oci_image::fetch_oci_manifest()`（regctl，按宿主 arch 选择 index 子 manifest，嵌套 ≤4 层）：
   - 只有 manifest 获取阶段可以"换下一个 registry"；全部 404 → `ImageError::NotFound`(4xx)，否则 Other(5xx)。
   - `UnsupportedImage`（如 turbo-OCI）立即失败。
3. `resolve_fetched_manifest()`：
   - 若命中 `try_referrers_overlaybd_prefixes` 且源不是 overlaybd-native → 列出 OCI referrers（不加过滤，本地匹配 `application/vnd.containerd.overlaybd.native.v1+json` 优先、其次 Azure `application/vnd.azure.artifact.streaming.v1`），用 referrer 的层，但 config 元数据仍取源镜像。
   - StandardOci 且 `convert_standard_oci=false` → 拒绝。
   - `SourceImageStore::open(manifest_digest, repository_scope)` → `cached_config()` 命中直接返回（metadata 缺失则补取）。
   - 未命中：`begin_conversion()`（per-image 锁 + operation hold）→ 取 config metadata → `convert_fetched_oci_image_to_overlaybd()` → `publish_config()`（先记录 config root，再释放 hold，保证转换出的 commit 一直受保护）。
4. 返回 `ResolvedBlockImage{image_ref, overlaybd_config_path, base_context, raw_config}`。

### 9.2 两种格式
- **OverlaybdNative**：不下载任何 blob；`ResolvedImage::Remote{repo_blob_url = https://{host}/v2/{repo}/blobs, layers(digest,size,dir)}`，运行时 overlaybd 的 `registryfs_v2` 按需拉（`dir` 指向 image-cache commits 目录作为落地缓存）。
- **StandardOci**：`convert_standard_oci_layers_pipeline()`：
  - 后台 `RegctlImageCopyProducer` 把镜像 copy 成本地 OCI layout（流式，边下边转）；
  - 逐层顺序转换：`LayerConversionKey{source_layer_digest, converter_id, virtual_size_gib=64, mkfs(第 0 层), parent_commit_digest, expected_layer_uuid}`——**每层的转换依赖其下全部 lower**（whiteout/ext4 需在 lower 之上 apply），所以 key 链式包含父 commit digest；
  - 先 `lookup_converted_layer()`：本地 `indexes/{source-digest}/…json` 命中则复用；否则 P2P `lookup_remote_converted_layer()`（key `oci-layer/v1/{sha256(key json)}`，校验 metadata 协议、digest/size、sealed overlaybd 层 UUID）；
  - 都没有则 `overlaybd-apply`（C++ 工具，`storage/overlaybd/src/tools/oci.rs::convert_local_oci_layer_to_overlaybd()`，独立 `convert-overlaybd-global.json` 与 `convert-blocks/` 缓存、禁用下载）生成 `layer.commit`；
  - `store_converted_layer()`：硬链接进 `commits/{digest-slug}/overlaybd.commit`，写索引，持久化 hard-commit 记录后发布到 P2P。
  - 层 UUID 由源层 digest 派生（`uuid_from_layer_digest`），父 UUID 链接。
- `overlaybd_image_config_json()` 生成最终 image.json：本地层带 file+digest+size，远端层带 dir。
- regctl 调用统一经 `regctl_command()`（GOMAXPROCS=4，防止高并发 fork 耗尽 PID）+ `run_regctl()`（5 次指数退避）。

### 9.3 本地 image-cache 与 GC（`src/image/cache/`）
目录：`<image.cache.root_dir>/{configs/*-image.json, configs/*.metadata.json, indexes/, commits/, remote-blocks/}`；元数据库 `metadata.db`（RocksDB）。
元数据图（`graph.rs`）：`HardCommitObjectRecord{digest, file, size, p2p_keys}`、`ConfigReferenceRecord(config→commit)`、`ConfigLastUsed`、`HoldRecord`（命名空间：transient runtime / durable paused / operation）。
GC（`service.rs::run_gc()`，"fail-closed"）：重建 config 根 → 收集运行集 live refs → 对每个候选在 operation hold 下复查：被 config 根引用 / 被 hold / 被运行中 sandbox 引用 / 无法验证 → 保留；否则先 unpublish 其 P2P key 再删文件。另有容量驱逐（按 LastUsed 淘汰源 config）、`reclaim_stale_indexes()`。
与快照的关系：committed 快照不 pin image-cache；POSIX 快照的 managed 层在仓库里有独立副本（硬链接时共享 inode，删除 cache 不影响仓库）。

### 9.4 建议图
- 图 7-14：resolve 决策树（候选 → manifest → referrer? → native/standard → cache hit? → 转换）。
- 图 7-15：逐层转换流水线（regctl copy 生产者 ‖ 转换消费者；本地索引 → P2P → overlaybd-apply 三级查找）。
- 图 7-16：image-cache 元数据图与 GC 保留条件。

---

## 10. 第 8.x 章：P2P 制品传输

### 10.1 抽象（`src/p2p/transport.rs`、`types.rs`）
- `P2pArtifactKey = String`，由消费模块编码完整缓存上下文；`P2pArtifactDescriptor{key, providers: [Local | Peer{node_id, endpoint{backend, address}}], backend_locator(=iroh blob hash), metadata(JSON, 模块自定义)}`。
- 操作：`lookup_with_hints / fetch_with_options(advertise) / fetch_bytes / fetch_byte_range(必须恰好 len 字节) / publish(Copy|Reference) / unpublish / local_endpoint / shutdown`。
- `DisabledP2pTransport`：lookup→None、publish→Ok no-op、fetch→`TransportDisabled`。使调用方可无条件调用。
- 开关：`[p2p].enabled` + `transport = "iroh"`；快照侧另有 `[snapshot].p2p_enabled`（默认 true，在 `src/bin/server.rs` 决定是否把 transport 传给 `SnapshotManager::new()`）。

### 10.2 iroh 后端（`src/p2p/iroh/transport.rs::IrohBlobsP2pTransport::new_with_gc_interval()`）
启动：`<p2p.store_dir>/iroh/` 下打开 `iroh_blobs::store::fs::FsStore`（`blobs.db`）+ RocksDB catalog（`catalog.db`，WAL 持久）→ `Endpoint::builder(presets::Minimal)` + `MemoryLookup`（不使用 iroh 公共发现/中继，地址由 AgentENV 自己分发；可 `listen_addr` 绑定）→ 一个 Router 同时服务 `iroh_blobs::ALPN`（数据）与 `/agentenv/artifact-catalog/v1`（元数据）。

- **publish**：导入 FsStore → 打确定性 named tag `agentenv:p2p:v1:{sha256(key)}`（保留语义）→ 本地 catalog upsert（provider=Local，locator=blob hash）→ best-effort `scheduler.RecordP2pArtifact`。
- **lookup**：① 本地 catalog；② scheduler 的 artifact→node 索引 `LookupP2pArtifact`，对候选节点并发（≤4）走 catalog ALPN 询问并取**第一个**有结果的（短路）；③ 回退到发现的全部 peers（hint 优先、去重）。scheduler 只存 key→node，不存 locator/metadata，不代理字节。
- **fetch**：descriptor 含 Local → 直接从本地 store export；否则把 providers 地址注入 MemoryLookup，`Downloader::download(GetRequest::blob(hash), providers)`（`fetch_timeout`）→ iroh-blobs 按 BLAKE3 hash 验证字节 → export 到目标。下载前先 `pin_blob()` 拿 TempTag 防 GC。成功后（`advertise=true`）把自己加为 provider 并 Record 到 scheduler——制品在集群中"越用越多副本"。
- **range fetch**：供 overlaybd facade 前台读；不广告部分 blob。
- **unpublish**：删 catalog、删 tag、Forget；不同步删字节。
- **门控 GC**（`gated_gc_config()`）：每 5 分钟唤醒，但 `add_protected` 回调在无 pending 时直接中止 mark/sweep；启动时 pending=true 一次，unpublish 置 pending。

### 10.3 发现（`src/p2p/discovery/`）
`SchedulerPeerDiscovery::start()`：周期（`peer_discovery_refresh_interval`，≥1s）调 `ListP2pPeers(cluster_id, backend, exclude_self)`；本节点 endpoint 通过 observability heartbeat 上报给 scheduler。没有 `cluster.scheduler_endpoint` 则 `NoopP2pPeerDiscovery`（单节点只能命中本地）。另有 `StaticP2pPeerDiscovery`（测试/静态配置）。

### 10.4 被加速的对象与 key 空间

| Key | 生产者 | 消费者 | 校验 | 失败回退 |
|---|---|---|---|---|
| `snapshot/v1/artifacts/{id}/vm_state.bin` | `SnapshotManager::publish_p2p_artifacts()`（提交后） | OSS resolver | 仅 iroh hash（来自 peer 的 descriptor） | OSS `get_to_file` |
| `snapshot/v1/artifacts/{id}/firecracker-manifest.json` | 同上（bytes） | OSS resolver | JSON 解析 | OSS `get_bytes` |
| `overlaybd-layer/v1/sha256:<digest>` | 快照发布（rootfs/内存/drive 层，压缩后用 prepared upload 描述符）、overlaybd facade `/p2p-control/publish-layer` | overlaybd HTTP facade `/p2p-http/{origin}` range 读 | `LayerMetadata` | 透传到 origin URL |
| uuid key（`layer_key_from_uuid`） | 本地-only 层 | facade `/p2p-uuid/{uuid}` | uuid | **无 origin 回退**（miss→404） |
| `oci-layer/v1/{sha256(LayerConversionKey)}` | image-cache 转换完成 | `lookup_remote_converted_layer()` | metadata 协议 + digest/size + sealed 层 UUID | 本地 regctl 下载 + 转换 |

POSIX resolver 不消费 P2P（仓库本身直接可达，缺文件即 `ArtifactNotFound`，不从 peer 修复）。

overlaybd facade（`src/overlaybd/p2p/facade.rs`，区外但本章需要）：本地 HTTP 服务，地址写进 overlaybd 全局配置（`setup::ensure_environment(read_facade_address)`）；descriptor 正/负缓存 TTL 5min/5s、上限 16K 条；lookup 300ms、range fetch 2s 超时；P2P 中途出错**不**回退 origin（避免已发出响应头后混源）；拒绝条件请求头；publish 路径限制在 `allowed_publish_roots`。

### 10.5 失败与回退原则
- 发布失败：warn，不回滚提交；lookup/fetch 失败：debug，回退源（OSS/registry/本地转换）。
- P2P 存储可整个清空，只影响加速不影响正确性（docs 所有权规则）。
- facade 启动失败 → overlaybd P2P 禁用、继续运行。

### 10.6 建议图
- 图 8-1：拓扑：节点 A/B/C 各含 iroh endpoint(两个 ALPN) + FsStore + catalog；scheduler 持 endpoint 表与 key→node 索引。
- 图 8-2：lookup 三级瀑布 + fetch 后自广告时序。
- 图 8-3：快照发布后 P2P 制品清单与消费方对应。

---

## 11. 意外点、死代码、TODO、技术债

1. **managed layers 永不回收**。POSIX `delete_record()` 与 OSS `delete()` 都只删 per-snapshot 目录/前缀；OSS 注释两次写 "shared across snapshots and require separate GC"，但全仓库没有任何仓库级 managed-layer GC（`grep -i gc src/snapshot` 只有这些注释）。仓库会单调增长。
2. **OSS 一致性弱于 trait 承诺**：`SnapshotRepository::try_start_build` 文档写 "Atomically transitions"，`image_build.rs::allocate_image_build` 注释也依赖"repository CAS 排除其他节点"，但 OSS 实现是无条件 RMW（`oss/repository.rs::try_start_build()`）；`bind_alias()` 为读-写-回读。与此同时同一文件里 volume 与 build-cache 已用 `put_bytes_conditionally()`（`if_match`/`if_none_match("*")`）实现真 CAS——注释中"阿里云 OSS 不支持条件写"仅对 multipart/部分路径成立，snapshot catalog 本可迁移到条件写。
3. **POSIX 中间态孤儿**：commit marker 先于 record 写；崩在两者之间会留下带 marker、无 record 的目录，没有启动期扫描清理。`persist_firecracker_manifest()` 用 `fs::write`，非原子无 fsync（对比 record 的 temp+fsync+rename）。
4. **`LocalArtifactCache` 索引纯内存**：重启后磁盘旧文件只有被再次 `ensure_cached` 命中时才计入；从未再访问的文件永不驱逐，`prepare_cache_root()` 只 mkdir。OSS 下 vm_state 文件很大，可能导致本地盘泄漏。
5. **快照固定制品的 P2P 信任边界**：record 不保存 vm_state/manifest 的 digest，`snapshot/v1/...` key 的 metadata 为 null；任何能回应 catalog ALPN 的 peer 可为该 key 提供任意 blob（iroh 只校验"与 peer 自报 hash 一致"）。转换层 P2P 的 digest/size 校验也来自同一 peer 的 metadata；UUID 由源 digest 可预测。即：**集群内 peer 被视为可信**，catalog 协议无鉴权。书中值得点明。
6. **命名遗留**：`MEMORY_STARTUP_PACK_ARTIFACT = "memory-startup.pack"` 实际存放的是 v4 *manifest*（不含页数据），`index_sha256` 字段名"为兼容保留"；`max_pack_bytes` 配置项仍描述"page-data cap"。
7. **死代码/半死代码**：`TemplateBuildRootfsBase::Ext4` 与 `TemplateBuildSpec::from_existing_rootfs()` 仅测试使用，生产路径直接报 "overlaybd-only publish mode does not support ext4"。`OssBackend::new()` 注释称"remains available for tests and direct callers"。
8. **TODO**：`runner.rs::prepare_startup()`——从 ENTRYPOINT/CMD 推导 start_cmd 被临时禁用（s6-overlay 等要求 PID 1 的镜像会失败，因为 start_cmd 经 `/bin/sh -c`）。**但 BuildKit 路径 `image_build.rs::build_startup_commands()` 仍然用 `context.effective_start_cmd()` 推导**——两条前端行为不一致，`aenv build` 的 PID 1 问题依然存在。`iroh/transport.rs:376` TODO：自广告 descriptor 只含 Local，未合并先前 provider。
9. **docs 漂移**（`template-builder-testing.md`）：称记录在 `snapshots/<id>/snapshot.json`，实际是 `catalog/records/{id}.json` + `snapshots/<id>/commit`；方法名 `load_committed`、`rebuild_and_publish`、`from_overlaybd_configs` 均不存在（实为 `get`、`build_from_snapshot_and_publish`、`from_overlaybd_config`）；"Pause the sandbox" 实为 `capture_to_dir`。`p2p-design.md` 的 trait 片段中 `fetch_byte_range` 返回 `Bytes`，代码返回 `P2pByteStream`。
10. **"OSS" 实为 S3**：OpenDAL `services-s3`，repoBlobUrl 用 `s3://`；"ACR" 模块实为通用 OCI registry 客户端。
11. **Fork 不进仓库**：很多读者会以为 fork = snapshot+N×start，实际是同节点内存快照，且禁止追加 drive。
12. **POSIX 运行时直接读共享 FS 上的 managed 层**（`file=` 指向仓库）——共享 FS 的读性能直接决定冷启动；与 OSS 下的 `s3://` 按需读 + overlaybd 本地块缓存形成对比。
13. **descriptor 信任**：`import_managed_layer_with_descriptor()` 不重算 hash，只校验 size（"intentionally trust internally generated content digests"）；`copy_file_with_sha256()` 却对 vm_state 做了双遍校验——成本取舍不一致但有理由（层大且内部产生）。
14. 发布压缩会让 committed digest ≠ 本地 raw digest，`SnapshotP2pArtifact::local_overlaybd_layers()` 专门跳过 raw digest 以免发布"无人查找的 key"；docs 也承认"不增加 digest-only 的 OSS 读路由"，即 OSS managed 层目前未必走 P2P facade。
15. `SnapshotListFilter::sandbox_snapshots()` 会剥离 `registry/repo:tag` 形式只取名字部分——API 兼容 e2b 风格引用的小技巧。
16. `tools-image/` 与 BuildKit 无关（是 envd tools drive），规划时别放进 BuildKit 章。

---

## 12. 章节拆分建议

原计划 Part 7 八章：①SnapshotManager & 对象模型 ②仓库后端 & 提交协议 ③artifact cache & startup pack ④rootfs 导出为 OCI ⑤fork ⑥template builder ⑦BuildKit ⑧镜像拉取与转换；Part 8 一章 P2P。

建议调整：

1. **把"镜像拉取与转换"提前到 Part 7 第 1 或第 2 章**。理由：快照对象模型里的 `ManagedLayer/ExternalLayer`、`repoBlobUrl`、`file=`/`dir=`、overlaybd-native 等概念全部源于镜像侧；模板构建、BuildKit 导入、source-registry 发布都依赖它。先讲"一个 OCI 镜像如何变成 OverlayBD 层栈"，再讲"快照=层栈+内存+VM 状态"，读者负担小很多。若 OverlayBD 格式本身在前面的存储 Part 已讲，可作为"承上"章。
2. **把 "artifact cache" 与 "runtime resolve" 合并为一章"从记录到可运行：Resolve 与本地缓存"**，startup pack 单独成一节或并入该章末尾（它与 resolve 的 `consume_enabled` 和 publish 的后台续作两头相关）；startup pack 的录制细节（1433 行的 `sandbox/firecracker/startup_pack.rs`）更适合放在 VM/内存章节，这里只讲制品与生命周期。
3. **"仓库后端"一章内容量大（POSIX ~4.6k、OSS ~3.9k、ACR ~3.4k 行）**，建议拆为两章：7.x "POSIX 仓库：文件系统上的提交协议"（锁、marker、硬链接、可见性、删除）与 7.y "对象存储仓库：没有 CAS 时怎么办"（OSS 上传、alias 回读、回滚、凭证刷新、发布压缩）。§3.5 一致性对比表放在后一章结尾。
4. **把"source-registry 发布"（ACR exporter）并入 rootfs-as-OCI 一章**，与 `aenv-snapshot-image` 离线导出对照讲（§5），而不是放在 OSS 后端章。
5. **Fork 一章应扩展为"快照家族操作：pause / snapshot / fork 的对照"**，强调 fork 不触及仓库；卷的 CoW fork 部分可交叉引用卷章节（`docs/.../sandbox-forks-and-snapshots.md`）。篇幅可能偏短（核心代码 <300 行），可与 pause 合并。
6. **模板与 BuildKit 两章保留**，但建议把"模板 = 带状态机的快照记录"放在模板章开头（e2b v3/v2 API 映射），BuildKit 章重点放"builder 自身也是模板快照"、"缓存种子 head 的 CAS 演进"和"WebSocket 隧道"三件事——这是本仓库最有特色的设计。
7. **P2P 一章需要包含 `src/overlaybd/p2p/facade.rs`**（区外 1450 行），否则"overlaybd 层如何被 P2P 加速"讲不完整；可按"通用传输层（iroh）→ 发现（scheduler 索引）→ 三个消费者（快照固定制品 / overlaybd 前台 range 读 / 转换层复用）"组织。信任边界（§11-5）放在章末讨论。
8. 可选新增一节/附录："持久化制品清单"——把 §2.3 表与 `persistence-artifact-inventory.md` 整合成全书参考表，并标注哪些可删、谁负责 GC（含"managed layers 无 GC"这一缺口）。

建议后的 Part 7 顺序（9 章）：
1. 从 OCI 镜像到 OverlayBD 层栈（image resolver、转换流水线、image-cache 与 GC）
2. 快照对象模型与 SnapshotManager
3. POSIX 仓库与提交协议
4. 对象存储仓库：上传、回滚与弱一致
5. Resolve 与节点本地缓存（含 startup manifest 制品）
6. 快照 rootfs 作为 OCI 镜像（离线导出 + source-registry 发布）
7. pause / snapshot / fork
8. 模板构建器
9. BuildKit：在 microVM 里跑 Dockerfile
Part 8：P2P 制品传输（含 overlaybd facade）。
