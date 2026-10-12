# 73 · 持久化制品与磁盘格式总表

> 本附录把散在第六、七部分的落盘对象集中成几张表：快照仓库里的每个制品由谁写、谁读、谁删、有没有回收；节点本地每个目录装什么、丢了会怎样；
> 全书出现的磁盘格式各有什么魔数、定义在哪里；以及每种格式与上游 overlaybd 是否兼容、依据是什么。每一行都链到详细讲解的篇目与小节。
>
> **读者**：排查磁盘占用、做迁移或备份、或想核对格式兼容性的读者。　**预备**：[第 46 篇 · 快照对象模型与 SnapshotManager](46-snapshot-object-model.md)、[第 05 篇 · overlaybd、LSMT 与 OCI 镜像按需加载](05-overlaybd-and-lazy-loading.md)。
> **代码**：`src/snapshot/types/artifacts.rs`、`src/snapshot/repository/backends/{posixfs,oss}/layout.rs`、`src/cfg.rs`、`storage/overlaybd/src/lsmt/format.rs`、`storage/overlaybd/src/compression/zfile.rs`、`storage/overlaybd/src/backend/cache/{mod,meta}.rs`、`storage/overlaybd/src/{startup_pack,startup_manifest,prefetch}.rs`

---

## 0. 本篇要回答的问题

1. 一个已提交快照由哪些制品组成？每个制品由哪段代码写入、被谁读取、在什么时候删除？哪些制品永远不会被回收？
2. 一个节点的 `$AENV_HOME` 与 `$AENV_RUNTIME` 下各有哪些目录？哪些必须备份，哪些可以重建，哪些只在运行期存在？
3. 全书出现的磁盘格式各用什么魔数、在哪个文件里定义、在哪一篇详讲？
4. 哪些格式与上游 overlaybd 兼容，哪些是 AgentENV 或 Rust 版 overlaybd 的扩展？Hybrid RW、ZFile 的压缩 index、块缓存 key 这几处容易说错的地方，准确的口径是什么？

---

## 1. 怎样读这些表

本篇的表按位置分三组：快照仓库（持久真相，可多节点共享）、节点本地（`$AENV_HOME` 与 `$AENV_RUNTIME`）、以及两者之外的源 registry。
这个三分法与[第 46 篇 §5](46-snapshot-object-model.md#5-三层存储)的「捕获暂存 / 已提交仓库 / 节点运行时缓存」一致，另外加上不进快照仓库的暂停沙箱产物（[第 22 篇](22-persistence-across-restarts.md)）。

表里的「GC」一栏只回答一个问题：**除了显式删除父对象之外，有没有代码会主动回收它**。「随删除」表示它只在所属快照、沙箱或卷被删除时一并删掉；
「无」表示 v0.2.3 没有任何代码删除它；「有」时写出机制名。删除中途失败留下的孤儿统一归入「无人清理」，因为两种仓库后端都没有启动期扫描（[第 47 篇 §7](47-posix-repository.md#7-崩溃一致性的边界)、[第 48 篇 §5](48-object-storage-repository.md#5-读与删除)）。

路径约定：仓库内的路径相对于 POSIX 仓库根 `<snapshot_store>/repository/` 或对象存储的 `<prefix>/`；两者不同时分别写出。
节点路径用缺省配置（`src/cfg.rs`：`home_path` 缺省 `/var/lib/aenv`，`runtime_path` 缺省 `/run/aenv`），全部可经配置改写（[第 11 篇](11-configuration.md)）。

---

## 2. 快照仓库里的制品

### 2.1 已提交快照

固定文件名来自 `src/snapshot/types/artifacts.rs` 的 `SNAPSHOT_ARTIFACT_LAYOUT`，两种后端的键名分别由 `posixfs/layout.rs` 的 `PosixFsSnapshotArtifactLayout` 与 `oss/layout.rs` 的 `OssSnapshotArtifactLayout` 给出。
四个位置之间的名字对照见[第 46 篇 §4](46-snapshot-object-model.md#4-一个快照的制品)；下表只关心生命周期。

| 制品（位置） | 谁写 | 谁读 | 谁删 | GC |
|---|---|---|---|---|
| 记录：`catalog/records/{id}.json`（[47 §2](47-posix-repository.md#2-目录布局)、[48 §2](48-object-storage-repository.md#2-对象布局)） | publish 的提交步：POSIX 临时文件加 rename，对象存储一次 PUT；模板的 Waiting 记录在 `create()` 时先写 | `get()`、`list()`、两种 resolver | POSIX `delete_record()` 最后删；对象存储 `delete()` 先删记录、后删制品 | 无；无启动扫描 |
| 别名：POSIX `catalog/aliases/{alias}`，对象存储 `…/{alias}.json`（[47 §5](47-posix-repository.md#5-锁按名字加不设全局锁)、[48 §6.1](48-object-storage-repository.md#61-alias读-写-回读)） | publish 时绑定；POSIX 在 alias 锁内，对象存储读-写-回读 | `resolve_alias()` | 删除快照时仅当仍指向自己才删 | 惰性：读到指向不存在记录的 alias 时删掉 |
| 提交标记：`snapshots/{id}/commit`，仅 POSIX（[47 §3.4](47-posix-repository.md#34-提交)） | 提交步写入，内容为 `committed` | 回滚与清理时判断是否已提交 | `delete_record()` | 随删除 |
| VM 状态：POSIX `snapshots/{id}/vm_state.bin`，对象存储 `artifacts/{id}/vm_state.bin`（[49 §3](49-resolve-and-artifact-cache.md#3-posix-后端不复制直接指向仓库)、[49 §4](49-resolve-and-artifact-cache.md#4-对象存储后端只下载小的层留在远端)） | publish 导入 | POSIX：Firecracker 直接读仓库文件；对象存储：先试 P2P、再下载到 `snapshot-local-cache/artifacts/{id}/` | 随快照目录或 `artifacts/{id}/` 前缀删除 | 随删除；删除或发布中途失败的残留无人清理 |
| Firecracker manifest：`…/{id}/firecracker-manifest.json`（[46 §3](46-snapshot-object-model.md#3-manifest形状进仓库路径留在节点)） | publish 导入，路径字段 `#[serde(skip)]` | 每次 resolve 读入内存，不进缓存 | 同上 | 随删除 |
| 共享层：POSIX `managed-layers/sha256_<hex>.overlaybd.commit`，对象存储 `managed-layers/sha256:<hex>`（[47 §3.3](47-posix-repository.md#33-内容寻址的写入)、[48 §4](48-object-storage-repository.md#4-层上传)） | publish 导入内存层、rootfs 层与附加盘层；卷 backing 发布 | Rust 版 overlaybd：POSIX 经 `file=` 直接读，对象存储经 `s3://` 按需读并过节点块缓存 | **无人** | **无**，两种后端都没有（[47 §6](47-posix-repository.md#6-删除)、[48 §7](48-object-storage-repository.md#7-不回收的层)） |
| startup manifest：`…/{id}/memory-startup.pack`（[49 §7](49-resolve-and-artifact-cache.md#7-startup-manifest-制品)） | 提交之后的后台任务，经 `attach_memory_startup()` 或 `attach_memory_startup_descriptor()` 补写 | resolve 生成引用，预取路径消费（[第 43 篇 §4](43-startup-pack-and-prefetch.md#4-消费两条路径)） | 随快照目录或前缀删除 | 随删除 |
| 构建日志：`snapshots/build-logs/{id}.json` | 模板构建经 `write_build_logs()`（[第 52 篇 §6](52-template-builder.md#6-构建日志)） | 模板日志接口经 `read_build_logs()`（`src/api/impls/template.rs`） | 两种后端的删除都先删它 | 随删除 |

两条规律。第一，每个快照独有的制品放在按 id 命名的目录或前缀下，删除快照时一起消失；层放在按 digest 命名的共享位置，删除快照时不动。
第二，两种后端的删除顺序相反：POSIX 最后删记录，保证「记录还在就能重试删除」；对象存储先删记录，保证「看得见的记录都是完整的」，代价是失败时留下无人引用的制品对象（[第 48 篇 §9](48-object-storage-repository.md#9-两种后端的一致性对比)）。

### 2.2 卷与构建缓存

| 制品（位置） | 谁写 | 谁读 | 谁删 | GC |
|---|---|---|---|---|
| 卷记录：`volumes/records/{volume_id}.json`，别名 `volumes/aliases/{name}`（[第 31 篇 §6](31-extra-drives-and-volumes.md#6-volumemanager权威在仓库本地是缓存)） | `VolumeManager`；对象存储侧用 ETag 条件写 | `VolumeManager::get()` 每次向仓库取 | `VolumeManager::delete()`，卷被持有时拒绝 | 记录随删除；`pending-` 孤儿预留无回收（[第 16 篇](16-snapshot-and-volume-api.md)） |
| 卷的层：同快照的 `managed-layers/` | `publish_volume_backing()`；删除沙箱时才是卷内容的提交点（[第 21 篇 §4.5](21-deletion-and-volume-capture.md#45-发布-backing)） | 挂载时物化成本节点 `image.json` | 无人 | 无；这也是源卷删除后克隆卷仍可用的前提 |
| BuildKit 缓存头指针：`template-build/cache-head.json`（[第 53 篇 §5.4](53-buildkit-in-microvm.md#54-头指针的条件写)） | `replace_build_cache_head()`，POSIX 用 flock，对象存储用 ETag | `fork_build_cache()` | 文件本身不删 | 退役种子卷由 `collect_retired_build_caches()` 回收卷记录；种子引用的层不回收（[第 53 篇 §5.5](53-buildkit-in-microvm.md#55-退役与回收)） |

### 2.3 仓库之外：源 registry 与 P2P

| 制品（位置） | 谁写 | 谁读 | 谁删 | GC |
|---|---|---|---|---|
| 快照 rootfs 的 OCI manifest 与层 blob（源 registry，[第 50 篇 §2](50-rootfs-as-oci-image.md#2-共同的格式overlaybd-native-manifest)） | 发布时推回源 registry，或离线工具 `aenv-snapshot-image` | 按 overlaybd-native 镜像冷启动的节点 | 发布回滚按 manifest digest 删；对象存储后端删快照后 best-effort `delete_disk_publications()` | blob 留给 registry 自己的 GC（[第 50 篇 §4.3](50-rootfs-as-oci-image.md#43-回退与失败)） |
| P2P 内容存储：`$AENV_HOME/p2p/store`（[第 58 篇 §3.4](58-p2p-artifact-transport.md#34-fetch校验与-gc)） | 发布与自广告的 fetch | 对端节点的 fetch 与范围读 | `unpublish()` 删命名 tag | 门控 GC：只在启动时与 unpublish 之后跑 mark/sweep；删除快照不 unpublish 其制品 |

---

## 3. 节点本地目录

### 3.1 目录树

回顾：下面这棵树以[第 10 篇 §5](10-node-process-and-object-model.md#5-节点磁盘布局)为底，补上了 image-cache 与卷的下一级目录（`src/setup/deps.rs` 的 `write_generated_overlaybd_global_configs()`、`src/volume.rs` 的卷数据路径、`src/bin/server.rs` 打开 `volumes/catalog`）。

```text
$AENV_HOME  (缺省 /var/lib/aenv)
├── deps/                          firecracker、kernel、tools 盘、overlaybd 工具、regctl，按版本分目录
├── overlaybd/                     每次启动重写的 overlaybd 全局配置
├── ublk/uvm-ublk-daemon           daemon 二进制
├── secrets/                       api-key、sandbox-access-token-hash-seed
├── persisted-sandboxes/
│   ├── records.db/                RocksDB，暂停记录
│   └── artifacts/<sandbox_id>/<uuidv7>/   每次暂停一代产物
├── volumes/data/<volume_id>/      卷的本地层栈与 image.json
├── template-builds/               模板构建 journal（RocksDB）
├── image-cache/
│   ├── configs/ indexes/ commits/ metadata/ staging/
│   ├── remote-blocks/             rootfs 块缓存，内含 premerged-index/
│   ├── memory-blocks/             内存快照块缓存
│   └── convert-blocks/ resize-blocks/   C++ 工具专用缓存
├── snapshot-store/                POSIX 快照仓库的缺省位置
├── snapshot-local-cache/
│   ├── runtime/<snapshot_id>/     物化的 image.json
│   └── artifacts/<snapshot_id>/   对象存储下载的 vm_state.bin
├── p2p/store/                     iroh 内容存储
├── firecracker-work/
│   ├── agentenv-fc-XXXX/          每台沙箱的工作目录
│   └── managed-snapshots/<sandbox_id>/<uuidv7>/   fork 与快照捕获
└── logs/                          ublk-daemon.log、serial/<sandbox_id>/

$AENV_RUNTIME  (缺省 /run/aenv)
├── netns/agentenv-ns-<uuidv7>     bind mount 的网络命名空间
└── ublk-daemon.sock               ublk-daemon 控制 socket
```

`[firecracker] work_dir` 未设置时，`managed-snapshots/` 落在系统临时目录的 `aenv/` 下（`managed_snapshot_base()`）；模板构建的捕获另在系统临时目录建 `snapshot-{id}-` 前缀的目录（[第 46 篇 §5](46-snapshot-object-model.md#5-三层存储)）。
startup pack 录制产出的 `memory-startup.trace` 写在捕获目录里（`src/sandbox/firecracker/startup_pack.rs` 的注释），随捕获目录的 lease 一起回收。

### 3.2 每个目录的生命周期

| 目录 | 写者与读者 | 回收机制 | 丢了会怎样 | 详见 |
|---|---|---|---|---|
| `secrets/` | `SandboxAccessTokenGenerator::load_or_create()` 与 API key 生成 | 从不删除 | 必须保留：有 secure 暂停沙箱时缺种子会拒绝启动 | [第 22 篇 §6.2](22-persistence-across-restarts.md#62-令牌种子) |
| `persisted-sandboxes/records.db` | `FileBackedSandboxPersister`，`Sync` 档逐次 fsync；`load_all()` 在启动时读 | 沙箱删除时删；启动时按清理规则删无效记录 | 必须保留：暂停沙箱全部丢失 | [第 22 篇 §3.1](22-persistence-across-restarts.md#31-记录格式)、[§6.1](22-persistence-across-restarts.md#61-清理规则) |
| `persisted-sandboxes/artifacts/` | 暂停时 `allocate_artifact_root()` 建新一代；resume 读 | `delete_record_and_artifacts()` 删整个沙箱目录；`cleanup_orphan_artifacts()` 只按沙箱 id 判定，旧代目录一直累积 | 必须保留 | [第 22 篇 §3.3](22-persistence-across-restarts.md#33-产物目录) |
| `volumes/data/<id>/` | `VolumeManager` 物化与创建 | 删卷时删 | 卷记录与已发布层在仓库；暂停期间只在本地 restack、尚未发布的卷内容会丢 | [第 31 篇 §6](31-extra-drives-and-volumes.md#6-volumemanager权威在仓库本地是缓存)、[第 21 篇 §7](21-deletion-and-volume-capture.md#7-卷的内容还在哪些时刻被发布) |
| `template-builds/` | 构建 journal，`LocalKvStore` 的 `Sync` 档 | 启动时 `recover_image_builds()` 收尾 | 进行中的构建无法收尾 | [第 15 篇 §4.6](15-template-build-api.md#46-崩溃恢复) |
| `image-cache/` 的 configs、indexes、commits、metadata | `ImageCacheService`；元数据图在 RocksDB | 维护任务：容量驱逐拆根，`run_gc()` 按「宁可不删」判定，失败时不启动 GC | 可重建，代价是重新转换；schema 不符时整库清空、hold 丢失 | [第 45 篇 §5.1](45-oci-to-overlaybd.md#51-目录)、[§5.5](45-oci-to-overlaybd.md#55-宁可不删的-gc)、[第 22 篇 §6.3](22-persistence-across-restarts.md#63-镜像-gc-的-fail-closed) |
| `remote-blocks/`、`memory-blocks/` | ublk-daemon 内 Rust 版 overlaybd 的块缓存 | 两条水位间按条目 LRU 驱逐、跳过忙条目；每 300 s checkpoint `meta.bin` | 可重建；未 checkpoint 的块与条目重启后丢失 | [第 39 篇 §2.4](39-block-cache-and-background-download.md#24-一个节点上的四个缓存目录)、[§4.2](39-block-cache-and-background-download.md#42-驱逐按条目按-lru跳过忙条目) |
| `remote-blocks/premerged-index/` | 打开只读层栈时后台写入 `.pmidx` | 按文件修改时间淘汰，上限为块缓存容量的 1/16，夹在 64 MiB 与 1 GiB 之间 | 可重建，下次打开重新合并 | [第 34 篇 §5.3](34-lsmt-format-and-index.md#53-去重写入与清理) |
| `convert-blocks/`、`resize-blocks/` | `overlaybd-apply` 与 `overlaybd-resize` 的 C++ 文件缓存 | 由 C++ 缓存自行驱逐 | 可重建 | [第 39 篇 §2.4](39-block-cache-and-background-download.md#24-一个节点上的四个缓存目录) |
| `snapshot-store/` | POSIX 仓库（`posix_fs` 缺省） | 见第 2 节 | 就是快照仓库本身；多节点必须改为共享路径或对象存储 | [第 47 篇](47-posix-repository.md) |
| `snapshot-local-cache/` | `LocalArtifactCache` 与 `RuntimeImageMaterializer` | 超限时按 LRU 删引用计数为 0 的条目到 80%；索引纯内存，重启后未再请求的旧文件既不计量也不驱逐 | 可重建 | [第 49 篇 §6](49-resolve-and-artifact-cache.md#6-localartifactcache)、[§6.3](49-resolve-and-artifact-cache.md#63-重启取消与多实例) |
| `p2p/store/` | iroh FsStore | 门控 GC | 可重建，邻居节点失去这份副本 | [第 58 篇 §3.4](58-p2p-artifact-transport.md#34-fetch校验与-gc) |
| `deps/`、`overlaybd/` | `ensure_environment()` 补齐依赖、每次启动重写全局配置 | `deps/` 只增不减 | 可重建，下次启动重新下载 | [第 10 篇 §2.4](10-node-process-and-object-model.md#24-ensure_environment校验加补齐)、[第 59 篇 §3.2](59-host-setup-and-privileges.md#32-版本化路径与存在即已安装) |
| `firecracker-work/agentenv-fc-XXXX/` | 每台沙箱一个 `TempDir`，含 socket、设备链接、可写层 | 句柄释放时删除；进程被 SIGKILL 后无人回收 | 纯运行期 | [第 26 篇 §5.4](26-sandbox-block-devices.md#54-可写层住在工作目录里) |
| `firecracker-work/managed-snapshots/` | 快照与 fork 的捕获 | `PersistentSnapshotRootGuard` 析构时删整个源沙箱目录；fork 捕获要等整棵树结束 | 纯运行期 | [第 51 篇 §3](51-fork.md#3-共享什么独占什么) |
| `logs/` | ublk-daemon 日志与串口日志 | 本书未核实回收逻辑 | 只影响排障 | [第 10 篇 §5](10-node-process-and-object-model.md#5-节点磁盘布局) |
| `$AENV_RUNTIME/netns/` | 网络槽位 bind mount | 启动时 `prepare_network_runtime()` 清理残留 | 纯运行期 | [第 29 篇](29-network-slots.md) |
| `$AENV_RUNTIME/ublk-daemon.sock` | ublk-daemon | 随 daemon 进程 | 纯运行期 | [第 41 篇](41-ublk-daemon.md) |

按「丢了会怎样」归类：**必须备份**的是 `secrets/`、`persisted-sandboxes/`，以及用 POSIX 后端且未另配路径时的 `snapshot-store/`；
`volumes/data/` 在有暂停沙箱挂着卷时也属于这一类。其余目录都可以从仓库、registry 或依赖源重建，只是要重新下载或重新转换。
推论：备份与迁移时把 `persisted-sandboxes/` 整体搬到新路径并不可行，因为记录里存的是绝对路径，`decode()` 不使用传入的 `artifact_root`，搬家后的记录会在下次启动时作为「产物缺失」被删除（[第 22 篇 §3.3](22-persistence-across-restarts.md#33-产物目录)）。

---

## 4. 磁盘格式魔数一览

### 4.1 有魔数的格式

| 魔数 | 格式 | AgentENV 侧定义 | 归属 | 详讲 |
|---|---|---|---|---|
| `LSMT\0\1\2`（u64 LE `0x00020100544d534c`）加固定 UUID `magic1` | LSMT 层头尾 `HeaderTrailer`，390 B，独占 4 KiB | `storage/overlaybd/src/lsmt/format.rs` 的 `HeaderTrailer::MAGIC0` / `MAGIC1`；校验在 `lsmt/file/helper.rs` 的 `verify_ht()` | 与上游兼容 | [第 34 篇 §2.1](34-lsmt-format-and-index.md#21-headertrailer) |
| `ZFile\0\x01\0` 加 `tuji.yyf@Alibaba` | ZFile 头尾，各 512 B，有效 96 B | `storage/overlaybd/src/compression/zfile.rs` 的 `MAGIC0` / `MAGIC1`；识别在 `is_zfile()` | 与上游兼容 | [第 35 篇 §2](35-zfile-compression.md#2-文件布局) |
| `ustar`；空 tar 用 `xxtar` | 远端 blob 的单文件 tar 包裹 | `storage/overlaybd/src/backend/tar.rs` 的 `TMAGIC` / `TMAGIC_EMPTY` | 与上游兼容 | [第 38 篇 §3.3](38-virtualfile-chain-and-remote-io.md#33-tar-适配与-switchfile) |
| `3270449184`（u32） | 上游 trace prefetch 的 trace 文件，24 B 头加 24 B 记录 | `storage/overlaybd/src/prefetch.rs` 的 `TRACE_MAGIC` | 与上游兼容 | [第 43 篇 §5](43-startup-pack-and-prefetch.md#5-上游兼容的-trace-prefetch) |
| `PMIDX001` | 预合并索引缓存 `.pmidx`，104 B 头加映射体 | `storage/overlaybd/src/lsmt/file/types.rs` 的 `PREMERGED_INDEX_MAGIC`；读回在 `helper.rs` 的 `decode_premerged_index_artifact()` | AgentENV 扩展 | [第 34 篇 §5.2](34-lsmt-format-and-index.md#52-key-与文件格式) |
| `0x4F424348`（`OBCH`） | 节点块缓存条目的 `meta.bin` | `storage/overlaybd/src/backend/cache/mod.rs` 的 `META_MAGIC`；布局在 `backend/cache/meta.rs` 的 `CacheMetaDisk` | AgentENV 扩展 | [第 39 篇 §4.3](39-block-cache-and-background-download.md#43-metabin-与崩溃语义) |
| `AENVTRC1` | startup pack 录制的首触页 trace，只在节点本地 | `storage/overlaybd/src/startup_pack.rs` 的 `TRACE_MAGIC`，`encode_trace()` / `decode_trace()` | AgentENV 扩展 | [第 43 篇 §3.1](43-startup-pack-and-prefetch.md#31-字节布局) |
| `AENVMF01` | startup manifest，仓库文件名 `memory-startup.pack` | `storage/overlaybd/src/startup_manifest.rs` 的 `MANIFEST_MAGIC`，`encode_manifest()` / `decode_manifest()` | AgentENV 扩展 | [第 43 篇 §3.1](43-startup-pack-and-prefetch.md#31-字节布局)、[§3.3](43-startup-pack-and-prefetch.md#33-名字的混用) |

两个同名常量值得留意：`prefetch.rs` 与 `startup_pack.rs` 都有一个叫 `TRACE_MAGIC` 的常量，前者是上游 trace 格式的 u32，后者是 AgentENV 的 8 字节 `AENVTRC1`，两种 trace 互不相通。
上游 trace 记的是每一层内的偏移，`AENVTRC1` 记的是内存镜像的逻辑页（[第 43 篇 §5](43-startup-pack-and-prefetch.md#5-上游兼容的-trace-prefetch)）。

### 4.2 只有版本字段的格式

下面这些持久对象没有魔数，靠版本字段或 key 前缀识别。它们的共同点是版本不符时**丢弃而不迁移**，所以升级格式就等于清空。

| 对象 | 版本标识 | 不符时 | 详讲 |
|---|---|---|---|
| 暂停记录（`records.db` 中的 JSON） | `RECORD_VERSION = 1`（`src/orchestrator/persistence/file_backed.rs`） | 删记录，产物交给孤儿清理 | [第 22 篇 §6.1](22-persistence-across-restarts.md#61-清理规则) |
| image-cache 元数据图（RocksDB） | `schema/version` = 1（`src/image/cache/graph.rs` 的 `SCHEMA_VERSION`） | 整库清空重写，hold 随之丢失 | [第 45 篇 §5.2](45-oci-to-overlaybd.md#52-元数据图) |
| 预合并索引的 key 与文件 | key 前缀 `overlaybd-premerged-index-key-v1`；文件头 `format_version` 与 `merge_version` 都为 1 | 视为未命中，重新合并 | [第 34 篇 §5.2](34-lsmt-format-and-index.md#52-key-与文件格式) |
| 块缓存 `meta.bin` | `version = 1`，另校验 `block_size` 与 CRC32C | 删除整个条目目录；改 `refillSize` 等于清空缓存 | [第 39 篇 §4.3](39-block-cache-and-background-download.md#43-metabin-与崩溃语义) |
| startup manifest | 版本字段为 4；消费端探测魔数，旧格式一律拒绝 | 放弃预取，按需恢复 | [第 43 篇 §3.3](43-startup-pack-and-prefetch.md#33-名字的混用) |
| overlaybd `image.json` | 无版本；字段沿用上游 camelCase | 上游未迁移的字段直接报错 | [第 05 篇 §4.3](05-overlaybd-and-lazy-loading.md#43-没有迁移的上游特性)、[第 36 篇 §2.1](36-read-write-paths-and-rw-layouts.md#21-从-imagejson-到-imagefile) |

---

## 5. 与上游 overlaybd 的兼容性对照

「Rust 版 overlaybd 与上游兼容」只对一部分格式成立。下表把第 05、34、35、39、43 篇的结论合在一起，依据一栏给出上游 containerd/overlaybd 默认分支（commit `e2a2ef3`，浅 clone）中的对应位置。
浅 clone 没有历史，表中「上游也有」只说明默认分支当前有，不说明从哪个版本开始有。

| 格式 | 兼容与否 | 依据 |
|---|---|---|
| LSMT `HeaderTrailer` 字段与 magic，flags bit0–bit2、bit4（Sparse RW） | 兼容 | 上游 `src/overlaybd/lsmt/file.cpp` 的 `HeaderTrailer` 与 `FLAG_SHIFT_*`、`FLAG_SPARSE_RW = 4`（[第 34 篇 §6](34-lsmt-format-and-index.md#6-与上游的兼容边界)） |
| LSMT flags bit3 | 两边都未定义 | 上游 `file.cpp` 的 flag 列表跳过 3 |
| LSMT flags bit5（Hybrid RW） | **同位同义**：上游默认分支也定义 `FLAG_HYBRID_RW = 5`（「1:hybrid rw 0:append rw」），bit4 与 bit5 同时置位两边都拒绝，原地改写已映射区间、空洞追加的主体语义一致；它不是 AgentENV 扩展 | 上游 `file.cpp`；Rust 侧 `storage/overlaybd/src/lsmt/format.rs`（[第 34 篇 §6](34-lsmt-format-and-index.md#6-与上游的兼容边界)、[第 36 篇 §4.3](36-read-write-paths-and-rw-layouts.md#43-hybrid能原地就原地不能就追加)） |
| Hybrid 写入复用零段物理空间（`ReuseZero`） | **Rust 版独有**：上游遇到本层 zeroed 映射一律追加；推论：Rust 版重放上游写过 discard 的 hybrid upper 时，可能把上游的占位 `moffset` 当作可复用空间，反方向安全 | Rust 侧 `plan_hybrid_write()`；上游 RW 层 `discard()`（[第 34 篇 §6](34-lsmt-format-and-index.md#6-与上游的兼容边界)） |
| `SegmentMapping` 50 / 14 / 55 / 1 / 8 位域 | 兼容 | 上游 `src/overlaybd/lsmt/index.h`（[第 34 篇 §2.2](34-lsmt-format-and-index.md#22-disksegmentmapping)） |
| compact 的索引补齐与 `index_size` 计数 | 兼容 | 上游 compact 用 invalid mapping 补到 4 KiB 并计入 `index_size` |
| backed zero 与 `NO_PHYSICAL_OFFSET` 哨兵 | Rust 版扩展：磁盘上的 zeroed 位不变，差别在 Rust 版怎样解释 `moffset` | `ReadOnlyIndex::new()` 的规范化（[第 34 篇 §2.3](34-lsmt-format-and-index.md#23-两种零段)） |
| ZFile 头尾字段与偏移，flags bit0–bit4 | 兼容 | 上游 `src/overlaybd/zfile/zfile.cpp`；Rust 侧 `HeaderTrailer::decode_from_512()`（[第 35 篇 §8](35-zfile-compression.md#8-与上游-overlaybd-的兼容性)） |
| ZFile flags bit5（压缩 index） | 上游有定义、无使用；Rust 版未实现。上游 `FLAG_SHIFT_IDX_COMP = 5` 只被 `set_compress_index()` 置位，而这个函数在上游没有调用者，所以上游自身也不产出带 bit5 的文件 | 上游 `zfile.cpp`（[第 35 篇 §8](35-zfile-compression.md#8-与上游-overlaybd-的兼容性)） |
| ZFile raw CRC32C、块 CRC seed 100007、jump table | 兼容 | 上游 `crc32c_extend()`；Rust 侧 `crc32c()`、`crc32c_salt()`、`JumpTable::build()`（[第 35 篇 §3](35-zfile-compression.md#3-校验一种rawcrc32c)） |
| ZFile 算法 LZ4、ZSTD（级别 3） | 兼容 | Rust 侧 `create_compressor()` 与 `ZSTD_C_LEVEL` |
| ZFile 算法 MINI_LZO（algo 0） | Rust 版不支持，`create_compressor()` 只认 1、2。上游 `compressor.h` 定义了 `MINI_LZO = 0`，但上游默认分支的 `create_compressor()` 同样只构造 LZ4 与 ZSTD，其它值报 EINVAL | 上游 `src/overlaybd/zfile/compressor.{h,cpp}` |
| ZFile 字典 | Rust 版不写；读端按 `dict_size` 跳过，与上游一致 | `ZFileBuilder` 从不写 dict |
| 远端 blob 的单文件 tar 包裹 | 兼容 | 上游 `src/overlaybd/tar/tar_file.cpp` 的 `TMAGIC_EMPTY "xxtar"`（[第 38 篇 §3.3](38-virtualfile-chain-and-remote-io.md#33-tar-适配与-switchfile)） |
| 上游 trace prefetch 格式（magic 3270449184） | 兼容；上游的动态预取清单未迁移，遇到时报错 | 上游 `src/prefetch.cpp` 的 `TRACE_MAGIC`（[第 43 篇 §5](43-startup-pack-and-prefetch.md#5-上游兼容的-trace-prefetch)） |
| `image.json` | 字段沿用上游；`upper.mode` 等是 AgentENV 新增；`targetFile`、`targetDigest`、`gzipIndex` 未迁移，打开时报错 | 上游 `src/config.h` 的 `UpperConfig` 只有 `index`、`data`、`target`、`gzipIndex`（[第 05 篇 §4.2](05-overlaybd-and-lazy-loading.md#42-格式兼容的边界)） |
| 节点块缓存的落盘格式（`data` 加 `meta.bin`，按条目一个目录） | 不兼容：上游用 photon 的 `new_full_file_cached_fs()`，把 `cacheDir` 下每个文件当作扁平缓存项；所以 C++ 工具另用 `convert-blocks/` 与 `resize-blocks/` | 上游 `src/image_service.cpp`；Rust 侧 `backend/cache/meta.rs`（[第 39 篇 §2.4](39-block-cache-and-background-download.md#24-一个节点上的四个缓存目录)） |
| 块缓存 key | 不同：上游经 `cache_fn_trans_sha256()` 按 digest 命名条目，同一层从不同 registry 拉取会命中同一条目；Rust 版照搬了这个变换，但在线路径 `open_cached_blob()` 直接以**完整 URL** 作键，所以**不按 digest 跨 registry 共享**。P2P 的 key 只按 digest，与此不同 | 上游 `src/image_service.cpp`；Rust 侧 `ImageService::open_cached_blob()`（[第 39 篇 §2.2](39-block-cache-and-background-download.md#22-条目与键)、[第 58 篇 §4](58-p2p-artifact-transport.md#4-三个消费者与-key-空间)） |
| 缓存类型 `ocf`、`download` | 未迁移，构建缓存时报错 | Rust 侧 `ImageService`（[第 05 篇 §4.3](05-overlaybd-and-lazy-loading.md#43-没有迁移的上游特性)） |
| 预合并索引 `PMIDX001` | AgentENV 扩展，只在本地缓存目录，不进入任何层文件 | [第 34 篇 §5](34-lsmt-format-and-index.md#5-预合并索引缓存pmidx001) |
| 块缓存 `meta.bin`（`OBCH`） | AgentENV 扩展 | [第 39 篇 §4.3](39-block-cache-and-background-download.md#43-metabin-与崩溃语义) |
| startup pack 的 trace（`AENVTRC1`）与 manifest（`AENVMF01`） | AgentENV 扩展，上游无对应物 | [第 43 篇 §3](43-startup-pack-and-prefetch.md#3-两种格式trace-与-manifest) |
| 块设备前端 | 不是磁盘格式，列在这里防止误读：上游的经典前端是 TCMU，默认分支也已带 ublk 前端（`src/ublk/`）；AgentENV 两者都不用，设备由自己的 Rust ublk 库与 ublk-daemon 提供 | 上游 `src/ublk/`；[第 05 篇 §4.1](05-overlaybd-and-lazy-loading.md#41-谁做什么)、[第 41 篇](41-ublk-daemon.md) |

三条容易说错的口径，在此统一：

- **Hybrid RW 不是 AgentENV 扩展。** 它与上游默认分支同位同义；独有的是 `ReuseZero` 这一写入策略，而不是 bit5 本身。
- **ZFile 的两处「不支持」不构成与上游产出的文件不兼容。** 压缩 index 与 MINI_LZO 在上游默认分支里也没有生产者；推论：只有第三方工具写出这两种文件时，Rust 版才会读不了。
- **块缓存不按 digest 去重。** 同一 digest 的层换一个 `repoBlobUrl` 就是另一个缓存条目；跨 registry 共享只在 P2P 层面成立。

兼容性的证据是逐字段对齐与已知向量，不是交叉测试：推论：仓库里没有用上游 C++ 产出的 LSMT 或 ZFile 文件作夹具的测试（[第 35 篇 §8](35-zfile-compression.md#8-与上游-overlaybd-的兼容性)）。
反方向的写入只有一处：ublk-daemon 扩容时调用 overlaybd 工具的 `overlaybd-resize` 原地修改 Rust 写出的 upper，之后用 `validate_rw_header_pair_paths()` 做结构检查（[第 41 篇 §5.2](41-ublk-daemon.md#52-为什么扩容要调-c-工具)）。

---

## 6. 小结

- 快照独有的制品（记录、VM 状态、Firecracker manifest、startup manifest、构建日志）放在按 id 命名的位置，随快照删除；层放在按 digest 命名的 `managed-layers/`，两种后端都**从不回收**。
- 两种仓库的删除顺序相反：POSIX 留下「可见但不可运行」的记录、可重试；对象存储留下无人引用的制品对象、无人清理；两者都没有启动期扫描。
- 节点上必须备份的只有 `secrets/`、`persisted-sandboxes/`、缺省 POSIX 仓库 `snapshot-store/`，以及挂着暂停沙箱卷时的 `volumes/data/`；其余目录都可重建。
- 有回收机制的本地缓存各用一套规则：image-cache 是 fail-closed GC 加按源配置的 LRU，块缓存是双水位按条目 LRU，`premerged-index/` 按写入时间淘汰，`snapshot-local-cache/` 是只覆盖本次进程的内存索引 LRU，P2P 是门控 GC。
- 只增不减的位置：仓库的 `managed-layers/`、`deps/`、暂停沙箱的旧代产物目录、重启前留下的 `snapshot-local-cache/` 文件。
- 魔数格式中，LSMT、ZFile、tar 包裹、上游 trace 与上游兼容；`PMIDX001`、`OBCH`、`AENVTRC1`、`AENVMF01` 是 AgentENV 扩展。
- 只靠版本字段识别的持久对象（暂停记录、image-cache 元数据图、块缓存条目）在版本不符时一律丢弃，没有迁移路径。
- Hybrid RW 与上游默认分支同位同义，`ReuseZero` 才是 Rust 版独有；ZFile 压缩 index 上游有定义无使用，MINI_LZO 不支持；块缓存 key 是完整 URL，不按 digest 跨 registry 共享。

---

## 延伸阅读 / 下一篇

- [第 46 篇 · 快照对象模型与 SnapshotManager](46-snapshot-object-model.md)：制品与三层存储的来历。
- [第 47 篇 · POSIX 仓库与提交协议](47-posix-repository.md)、[第 48 篇 · 对象存储仓库：上传、回滚与弱一致](48-object-storage-repository.md)：两种后端的提交、删除与一致性。
- [第 34 篇 · LSMT 格式与索引](34-lsmt-format-and-index.md)、[第 35 篇 · ZFile 压缩](35-zfile-compression.md)、[第 39 篇 · 节点块缓存与后台下载](39-block-cache-and-background-download.md)：各格式的字节布局。
- [第 68 篇 · 已知问题与技术债](68-known-issues-and-debt.md)：不回收的层、只增不减的目录等条目的汇总。
- [第 71 篇 · 配置项、环境变量与端口总表](71-config-env-ports-reference.md)：本篇路径对应的配置键。
- 上游格式说明：containerd/overlaybd 仓库的 `src/overlaybd/zfile/format_spec.md`。
