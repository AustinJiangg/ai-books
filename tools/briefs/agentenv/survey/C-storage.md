# C. 存储子系统源码调研笔记（AgentENV v0.2.3 / 6cccaa7）

> 范围：`storage/overlaybd`、`storage/ublk`、`storage/ublk-daemon`、`storage/util`、`storage/uffd-core`，
> 以及节点侧胶水 `src/overlaybd/`、`src/sandbox/ublk/`、`src/sandbox/firecracker/overlaybd_snapshot.rs`
> 等。以代码为准，文档只作背景。下文路径都相对仓库根目录。
> 记号说明：【核实】表示已对照代码确认；【推断】表示从代码推断出来、但需要对照上游 C++ 或内核源码再确认。

---

## 0. 一页结论（写书时先读这段）

1. **AgentENV 的 overlaybd 是用 Rust 重写的运行时，替换了 C++ 的 overlaybd-tcmu**。读写数据面完全由 Rust 实现：LSMT、ZFile、registryfs_v2、OSS、tar、full-file cache、后台下载、prefetch trace。磁盘格式（LSMT header/trailer、16B 段映射、ZFile header/trailer/jump table、CRC32C 变体）都刻意与上游逐字节对齐，代码注释里多处写着 “Keep parity with upstream OverlayBD / C++”。
2. **C++ 的 overlaybd 工具仍然要用**（`config/deps_manifest.toml [overlaybd] v1.0.18-aenv.1`，kvcache-ai fork 的静态链接 release），但只用于**离线**步骤：`overlaybd-create/apply/commit`（OCI tar 层转 ext4 overlaybd 层，见 `storage/overlaybd/src/tools/oci.rs`、`src/image/oci_image.rs`），以及 `overlaybd-resize`（daemon 为扩容运行时镜像而起的子进程，见 `storage/ublk-daemon/src/runtime.rs::run_resize_tool()`）。C++ 生成的 commit 由 Rust 运行时读取；Rust 生成的 upper 和 sealed 层又会被 `overlaybd-resize` 读写，所以两边**双向兼容**是实际在跑的约束，并且有 `validate_rw_header_pair_paths()` 专门检查“外部工具原地改过的 upper”。
3. **AgentENV 新增的格式和机制**（上游没有，或与上游不兼容）：Hybrid RW 布局（header flag bit5）、premerged index 缓存文件（`PMIDX001`）、full-file cache 的 `meta.bin`（magic `OBCH`，用 roaring bitmap 记录块存在性）、startup manifest（`AENVMF01`）、zero-copy seal（直接把 upper 原地封口并 rename，同时增量算 sha256）、`NO_PHYSICAL_OFFSET` 哨兵。
4. **ublk 部分没有复用 libublk 的 queue 实现**，只借用了 `libublk-rs-sys` 的 FFI 绑定，自己基于 io_uring `UringCmd16/UringCmd80` 写了 ctrl/queue。每个 queue 一个 OS 线程，线程里跑 current_thread tokio + LocalSet，每个 tag（slot）一个 local task。**overlaybd target 实际不支持 zero-copy**：`AutoRegBuffer` 分支直接报错，daemon 也没有打开 `UBLK_F_AUTO_BUF_REG`。默认配置是 1 个 queue、depth 16、每 IO 256 KiB。
5. **ublk-daemon** 是单独的进程，节点通过 UDS 发 RPC，每个连接只发一个请求，帧格式是 4B 大端长度加 JSON。daemon 负责：运行时目录物化、warm 设备池（用占位镜像加 `swap_state` 热切换 target）、Shared/Exclusive 两种访问模式（内存设备做 refcount 共享）、restack 快照、startup pack 录制和预取。**daemon 不支持崩溃恢复**：没有 `UBLK_F_USER_RECOVERY`，客户端 watchdog 只把 daemon 标记为 dead，之后所有 RPC 直接失败。
6. **内存快照链路**：暂停时调用 Firecracker 的 `PUT /snapshot/create`（Diff，只存状态），再调用 fork 版 Firecracker 新增的 `GET /vm/dirty-memory-ranges`，得到 `(base_host_virt_addr, image_offset, length)` 列表。把它转成 `SegmentMapping`，其中 **moffset 字段存的是 FC 进程的 HVA（以扇区为单位）**，然后把 `ProcessVmReader`（基于 `process_vm_readv`）当作“第 0 层文件”传给通用的 `compact_to()`，直接写出一个 sealed LSMT 层。恢复时由 daemon 用 Shared 模式起一个只读 ublk 设备（`/dev/ublkbN`），作为 Firecracker `BackendType::File` 内存后端；同一快照的多个沙箱共享这个设备和它的页缓存。节点侧还专门保持一个打开的 fd，防止最后一个 opener 关闭时内核清空页缓存。
7. **uffd-core** 是保留的另一套方案（userfaultfd 缺页处理，`MemoryImageBackend` trait 加 overlaybd 实现），已被排除在 workspace 之外；FC 侧对应的 `load_snapshot_uffd()` 标着 `#[allow(dead_code)]`。

---

## 1. 模块地图与行数

统计方法：`#[cfg(test)]` 之后的内联测试，以及 `tests/`、`benches/`、`examples/`、`tests.rs`，都算作“测试”。数字是近似值。

| crate / 目录 | 源码行 | 测试/bench/example 行 | 职责（一句话） |
|---|---|---|---|
| `storage/overlaybd`（crate 名 `overlaybd`） | ≈25.5k | ≈17.6k | Rust 版 overlaybd：LSMT 分层、ZFile、后端、缓存、镜像服务 |
| ├ `src/lsmt/`（format/index/file/*） | 5.0k | 4.7k（`file/tests.rs` 4051） | LSMT 磁盘格式、索引结构、RO/RW 文件、栈叠加、compact |
| ├ `src/compression/zfile.rs` | 2.4k | 0.7k | ZFile 只读读取器、Builder（多线程压缩）、CompactWriter |
| ├ `src/image/`（image_file / image_service / snapshot / helper） | 2.0k | 2.8k | 解析 image.json，组装层栈，restack、close_seal，远端运行时 |
| ├ `src/io/`（virtual_file / vfile_io / dispatch_file） | 0.56k | 0.18k | `VirtualFile` trait、`IoCtx`、Direct/Ctx 读写策略、`RuntimeDispatchFile` |
| ├ `src/backend/local.rs` | 0.8k | 0.2k | 本地文件：同步 pread/pwrite，或经 io_uring（ctx 路径） |
| ├ `src/backend/registryfs_v2.rs` | 1.9k | 0.9k | OCI registry blob 的 Range 读取、Bearer/Basic 认证、P2P 加速地址 |
| ├ `src/backend/oss.rs` | 0.66k | 0.07k | 基于 opendal 的 S3/OSS 读取与分片上传 |
| ├ `src/backend/tar.rs` | 0.7k | 0.33k | 剥掉“单文件 tar”的头尾（remote blob 是 tar 包裹的 commit） |
| ├ `src/backend/switch.rs` | 0.23k | 0.31k | 自动识别 ZFile 并解包；后台下载完成后切到本地文件 |
| ├ `src/backend/cache/`（full_file_cache、bk_download、startup_pack_task、meta） | 5.9k | 3.3k | 节点级块缓存（稀疏 data 文件 + mmap + roaring bitmap）、后台下载调度器 |
| ├ `src/sys/` | 1.1k | 0.35k | 跨平台原语：打洞、预留空间、page cache 驱逐、xattr、稀疏判定（Linux/macOS） |
| ├ `src/tools/`（oci.rs、packaging.rs） | 0.68k | 0.43k | 调用 C++ overlaybd-create/apply/commit；把 raw/ext4 打包成层 |
| ├ 顶层：`config.rs` `prefetch.rs` `download_gate.rs` `pack_planner.rs` `startup_manifest.rs` `startup_pack.rs` `metrics.rs` `dense_export.rs` `ext4_stat.rs` | 3.2k | 1.5k | 配置（兼容上游 JSON）、trace 录制/回放、前后台准入、启动包规划等 |
| `storage/ublk`（crate `uvm-ublk`） | ≈2.8k | ≈1.3k（`tests/overlaybd.rs` 892） | ublk ctrl/dev/queue/io_buffer，`OverlaybdTarget`，`StartupPackRecorder` |
| `storage/ublk-daemon`（crate `uvm-ublk-daemon`） | ≈4.1k | ≈2.6k（`tests/ublk_daemon_test.rs` 1253） | daemon 进程：RPC server/client、运行时物化、warm pool、restack |
| `storage/util`（crate `storage-util`） | ≈1.6k | ≈0.2k | `AsyncIoRing`、`IoRingWorker`、`MMapRegion`、`AlignedBuffer`、`CompactWriter`、`ReloadableIDAllocator` |
| `storage/uffd-core`（crate `uvm-uffd-core`，**不在 workspace**） | 784 | 0 | userfaultfd 内存恢复的备选方案 |
| `src/overlaybd/p2p/`（facade/artifact/cache） | ≈1.9k（facade 1450，含测试约 600） | — | 节点侧 P2P HTTP 门面（`/p2p-http/<origin>`、`/p2p-uuid/<uuid>`、`/p2p-control/publish-layer`） |
| `src/sandbox/ublk/`（device.rs 941、overlaybd.rs 372） | 1.3k | — | `UblkDeviceManager` 单例、共享只读设备 refcount、compact_layers |
| `src/sandbox/firecracker/overlaybd_snapshot.rs` | 1290（测试约 480） | — | rootfs restack 快照、内存脏页转层、运行时层后缀压缩 |
| `src/sandbox/firecracker/process_vm_reader.rs` | 131 | — | 用 `process_vm_readv` 实现的 `VirtualFile`（offset 就是 HVA） |
| `src/sandbox/firecracker/startup_pack.rs` | 1433 | — | startup pack 录制编排、本地预取 |
| `src/setup/overlaybd.rs`（612）、`src/setup/ublk.rs`（118） | — | — | 下载 C++ 工具、udev 规则、modprobe |
| `containerd-plain-snapshotter/`（Go，627 行） | — | — | **与 overlaybd 无关**：一个 bind-mount 现成 rootfs 的 containerd proxy snapshotter，仓库内没有任何引用，独立小工具 |

---

## 2. 分章节素材

### 第 1 章（建议）LSMT 磁盘格式

**要解决的问题**：块设备镜像需要分层、写时复制，还要能从远端按需读取。LSMT 用“日志式追加数据加段映射索引”表示每一层，多层索引合并后得到一次查找就能定位的视图。

**关键类型**
- `storage/overlaybd/src/lsmt/format.rs`：`HeaderTrailer`（packed，390B）、`DiskSegmentMapping`（16B）、`NO_PHYSICAL_OFFSET`
- `storage/overlaybd/src/lsmt/index.rs`：`Segment`、`SegmentMapping`、`LogIndex` trait、`ReadOnlyIndex`、`MutableIndex`（BTreeSet）、`ComboIndex`、`LinearizedBptree`/`IndexLBPT`
- `storage/overlaybd/src/lsmt/file/types.rs`：常量 `ALIGNMENT=512`、`HEADER_SIZE=4096`、`MAX_IO_SIZE=4MiB`、`MAX_STACK_LAYERS=255`、`INVALID_SEGMENT_OFFSET=(1<<50)-1`

**HeaderTrailer 字节布局**【核实，`const _: assert size==390`】，小端，占用一个 4 KiB 块（`SPACE=4096`），其余字节填 0：

| 偏移 | 长度 | 字段 | 说明 |
|---|---|---|---|
| 0 | 8 | magic0 | `"LSMT\0\1\2"` = `0x00020100544d534c` |
| 8 | 16 | magic1 | UUID `d2637e65-4494-4c08-d2a2-c8ec4fcfae8a`（字节序见代码 `MAGIC1`） |
| 24 | 4 | size | sizeof(HeaderTrailer)=390 |
| 28 | 4 | flags | bit0 header(1)/trailer(0)；bit1 data(1)/index(0)；bit2 sealed；bit4 sparse_rw；**bit5 hybrid_rw（AgentENV 新增）**；bit3 未定义（上游为 GC，【推断】） |
| 32 | 8 | index_offset | **字节**偏移；未封口的 index 文件里固定为 4096（`set_unsealed_index_offset`） |
| 40 | 8 | index_size | 映射**条数**，不是字节数 |
| 48 | 8 | virtual_size | 字节 |
| 56 | 37 | uuid | 带连字符的 UUID 字符串，以 `\0` 结尾 |
| 93 | 37 | parent_uuid | 同上 |
| 130 | 2 | reserved | |
| 132 | 1 | version | 默认 1 |
| 133 | 1 | sub_version | 默认 1 |
| 134 | 256 | user_tag | |

**DiskSegmentMapping（16B）位域**【核实，`from_memory()/to_memory()`】，单位都是 512B 扇区：
```
data_low  (u64 LE): offset[0..50) | length[50..64)   → 最大逻辑地址 2^50 扇区，单段最长 16383 扇区（≈8 MiB）
data_high (u64 LE): moffset[0..55) | zeroed[55] | tag[56..64)
```
- 内存里的 `SegmentMapping{segment, moffset, zeroed, tag}`。`moffset == (1<<55)-1`（即 `NO_PHYSICAL_OFFSET`）表示“没有物理空间的零段”。
- 有“backed zero”和“unbacked zero”两种零段：Hybrid upper 经 discard 后保留物理区间，置 `zeroed=1` 但 moffset 仍然有效，之后写入可以复用这段空间（`WriteFragment::ReuseZero`）。`ReadOnlyIndex::new()` 会把下层所有 zeroed 段的 moffset 统一改成 `NO_PHYSICAL_OFFSET`（注释说：上游写出的零段 moffset 是任意占位值）；RW 重放时不做这一步。
- 磁盘上 tag 一律写 0，加载时 `load_index_and_reset_tags()` 再重置。tag 只在内存合并视图中表示层号。

**层文件的物理形态**
1. **Sealed 只读层**（`.commit`）：`[Header 4K][数据（扇区对齐）][index：N×16B，补齐到 512][补 0 到 4K 对齐][Trailer 4K]`。Trailer 固定在 `file_size-4096`，`verify_ht(is_trailer=true)` 要求 magic 正确、是 trailer、是 data file、已 sealed。打开流程：`LSMTReadOnlyFile::open()`，先 `verify_ht` 头，再 `verify_ht` 尾，然后 `load_index_and_reset_tags(trailer.index_offset, index_size)`。
2. **RW 对（LogStructured）**：`upper.data`（4K header 加追加写入的数据）和 `upper.index`（4K header，flags 标为 index file、`index_offset=4096`，后面是追加的 16B 映射流）。重新打开时从 index 文件重放映射（`LSMTFile::open()`）。
3. **Sparse RW**：只有 data 文件，预先 truncate 到 `virtual_size+4096`，写入直接落在 `HEADER+逻辑偏移`。重新打开时用 SEEK_DATA/SEEK_HOLE 恢复映射（`create_mappings_from_sparse()`）。只在 Linux 上允许（`sys::sparse_extents_are_reliable()`，因为 APFS 会预分配大约 16–20 MiB 的空洞，这段注释很长，适合做旁注）。
4. **Hybrid RW**（AgentENV 新增）：数据文件以日志方式追加，但已有物理段可以**原地覆盖**（`plan_hybrid_write()` 把一次写拆成 InPlace/ReuseZero/Append 三类 fragment）。目的是避免 upper 无限增长；代价是原地写可能在主机崩溃时产生撕裂块，所以快照正确性依赖 quiesce/sync（见 `types.rs::WriteFragment` 的注释）。

**索引结构**
- `ReadOnlyIndex`：已排序的 Vec，`lookup()` 用 `partition_point` 二分查找。`merge()` 从 i=n-1 倒序插入 `MutableIndex`，所以 **tag 0 = 最新层**（注释原文 “The smaller the tag is, the newer the data is”）。
- `MutableIndex`：`BTreeSet<SegmentMapping>`。`insert()` 切掉与新段重叠的旧段，保留左右残片，这是“新写覆盖旧写”的核心。
- `ComboIndex{upper: MutableIndex, lower: Arc<ReadOnlyIndex>}`：先查 upper，upper 的空隙再去 lower 查。构造时 upper 的 tag 全部加 `ro_layers_count`（有 `FIXME: why do not alter upper directly?`）。
- `LSMTFile.layers` 的顺序是 `[top, top-1, …, bottom, rw]`，`rw_tag = lower 数`。读取时 `layers[m.tag]` 加上 `moffset*512` 就是物理位置。这个“合并索引里 tag 0 最新，但 RW 层放在最后”的约定容易让人糊涂，书里值得画一张图。
- **`LinearizedBptree`/`IndexLBPT`（移植自上游的线性化 B+ 树）在 crate 内没有被任何代码引用**，属于死代码，只有测试覆盖。

**Premerged index 缓存（AgentENV 新增）**：`open_files_ro_with_premerged_cache()`（`lsmt/file/stack.rs`）。以所有层的 `(uuid, size, index_offset, index_size, version…)` 计算摘要作为 key，把合并后的映射写到 `<cacheDir>/premerged-index/<digest>.pmidx`（头部 magic `PMIDX001`，含 format/merge version、layer_count、mapping_count、body_len、key_digest、body sha256），写入方式是 tmp 加 rename，并按 cacheSizeGB/16（clamp 到 64 MiB–1 GiB）做 LRU 式清理。同一个 key 用进程内 Weak 锁做合并，避免重复计算。这样几十层的镜像在冷启动时不用每次都重新 merge。

**建议配图**：①HeaderTrailer 字段表；②16B 映射位域图；③sealed 文件纵向布局；④RW 对（data+index）布局；⑤三层叠加的 merge 示意，标出 tag 方向。

---

### 第 2 章 ZFile 压缩

**关键**：`storage/overlaybd/src/compression/zfile.rs`

**布局**【核实】：
```
[Header 512B][dict(dict_size，实际恒为0)][block_0 压缩数据 (+4B CRC)][block_1 …]…[index: u32×N 每块编码长度][Trailer 512B]
```
- Header/Trailer 的 512B 中只有前 96B 是有效 body：
  `0 magic0 "ZFile\0\x01\0" | 8 magic1 "tuji.yyf@Alibaba"(16B) | 24 size=96 | 28 digest(u32,CRC32C) | 32 flags(u64) | 40 index_offset | 48 index_size(条数) | 56 original_file_size | 64 index_crc | 68 reserved | 72..96 CompressOptions`
- flags：bit0 header；bit1 data file；bit2 sealed；bit3 header_overwrite；bit4 calc_digest。
- `CompressOptions`（24B）：`block_size u32 | algo u8(1=LZ4,2=ZSTD) | level u8 | use_dict u8 | pad | reserved u32@8 | dict_size u32@12 | verify u8@16`。默认 LZ4，block 4 KiB，zstd level 3。
- 读取限制 `block_size ≤ MAX_READ_SIZE(64KiB)`。
- **CRC 变体**：用的是上游 `crc32c_extend()` 那种 “raw” CRC32C（init 0、无 xor）。代码用 `!crc32c_append(!state, data)` 把硬件加速的标准 CRC32C 转成这个变体，块 CRC 的 seed 是质数 100007（`crc32c_salt`）。注释讲得很清楚，可以直接引用。
- **Header digest**：先把 digest 字段清零，再对 512B 整体算 CRC32C（`write_header_trailer()`、`is_valid()`）。
- `header_overwrite`：完成时把 trailer 的信息覆盖写回 header（`CompressArgs.overwrite_header`），这样读者只读头部就能拿到 index 位置，用于流式场景，或在 trailer 不位于文件尾时使用（【推断】）。`load_jump_table()` 先检查这一位再决定去哪里读 trailer。

**JumpTable**：每 `group_size = 65536/block_size` 个块存一个 u64 绝对偏移（`partial_offset`），组内用 u16 存累计 delta（`deltas`），因此单块编码长度必须小于 64K。`offset_at(i)` 是 O(1)。这与上游 jump table 的设计一致。加载 index 时用 1 MiB 分块、32 路并发读取（`JUMP_TABLE_READ_*`）。

**读路径** `ZFileRO::pread_inner()`：
1. 由 `[offset, offset+len)` 算出块范围 `[begin_idx, end_idx)`。
2. `plan_coalesced_batch()`：连续若干个**完整**编码块，只要总跨度不超过 64 KiB 就合成一次后端读（注释特意说明与上游 `min(MAX_READ_SIZE, full span)` 的区别：不会读到下一个块的一部分，因此没有重复字节）。
3. 每块先校验 CRC（verify 打开时），再解压。完整块直接解压进调用者缓冲区，首尾块经过 scratch 缓冲。
4. CRC 或解压失败时，按精确范围 `evict_range` 后单独重读该块，最多 3 次。
5. 每线程有缓冲池（`PooledBatchBuffer`），指标每 1024 次 pread 采样一次（`ZFILE_PREAD_SAMPLE_INTERVAL`）。
6. `pread_with_ctx()` 让底层读走 ublk queue 的 io_uring，解压仍在 queue 线程上同步执行。

**写路径**：`ZFileBuilder`（`new()` 先写 header，`write()` 攒满整块后压缩，`finish()` 写 index、index_crc、trailer，可选再覆盖 header）。`args.workers>1` 时启用常驻 `WorkerPool`（每个 worker 自带一个 compressor，因为 zstd 上下文创建昂贵；队列有界 `workers*2`，按 seq 重排保证顺序）。有 TODO：`pool.recv()` 会阻塞当前 async 任务。`ZFileCompactWriter` 实现 `CompactWriter`（缓冲 512 KiB），可以直接作为 `compact_to()` 的输出，于是 “LSMT compact 加 ZFile 压缩” 一次完成。

**AgentENV 的使用策略**：本地 sealed 层**始终保持 raw**，只在 publish 时按 `[snapshot.publish_compression]` 重新打包成 ZFile 上传（`src/sandbox/ublk/overlaybd.rs::OverlaybdCompactOutput`、`create_commit_args()`；`overlaybd_snapshot.rs` 模块注释）。读取端由 `backend/switch.rs::try_open_zfile()` 通过 `is_zfile()` 魔数自动识别。

**配图**：ZFile 纵向布局；jump table 的两级结构；coalesced batch 示意。

---

### 第 3 章 读写路径与层栈（ImageFile、restack、seal、compact）

**层栈装配**（`storage/overlaybd/src/image/image_file.rs`）：
```
image.json(ImageConfig, 兼容上游 camelCase 字段)
 └ ImageFile::open → init_image_file
    ├ open_lowers（buffer_unordered 32 路并行）
    │   每层：本地 file/dir(overlaybd.commit|overlaybd.sealed) → LocalFile → TarFile 适配 → SwitchFile(自动 ZFileRO)
    │         本地缺失且有 uuid → P2P uuid facade
    │         远端：[P2P uuid] → repoBlobUrl/digest → registryfs_v2|OSS → RuntimeDispatchFile → CachedFile → Tar → Switch
    │   → open_files_ro_with_premerged_cache → LSMTReadOnlyFile
    ├ open_upper → LocalFile(data)+LocalFile(index) → open_file_rw → LSMTFile
    └ stack_files(upper, lower) → LSMTFile(ComboIndex)
```
- `ImageFileBase::{ReadOnly(LSMTReadOnlyFile), ReadWrite(LSMTFile)}`，外面套 `tokio::RwLock<LiveImageState>`，目的是让 restack 能原子地替换整个栈。
- 不支持的上游特性会显式报错：`targetFile/targetDigest/gzipIndex`（warp/turboOCI/gzip 索引）、`cacheType=ocf|download`。`nr_io_rings` 字段只留在配置里，没有被使用。
- `acceleration_layer=true` 时弹出最后一个 lower 当作 trace 层（`prefetch.rs` Replay 模式）；`record_trace_path` 走 Record 模式，并关闭后台下载。

**读**（`LSMTFile::read_internal_into_generic()`）：检查 512 对齐，截到 vsize，按 `max_io_size`（4 MiB）分片；每片先在索引读锁下 `lookup`，得到映射；`read_mappings_into_generic()` 中空洞和 zeroed 段填 0，其他段 `read_exact(layers[tag], moffset*512)`。Hybrid 模式下，如果读到当前 upper 的数据，就**在物理 IO 期间一直持有读锁**，防止和原地写撕裂。`ImageFile` 读入口还创建 `download_gate::FgReadGuard`，统计前台在途读，供后台下载让路。

**写**（`write_internal_generic()`）：
- LogStructured：拿索引写锁，在 `rw_data_append_offset`（内存游标，避免每次 `size()`）追加数据，`idx.insert`，再追加 16B 到 index 文件。group commit 可选（`set_index_group_commit()`，缓冲达到阈值后批量写）。`AppendDigestTracker` 同时增量计算 sha256，前提是数据文件从 4096 开始严格顺序追加，否则放弃。
- Sparse：写到 `HEADER+offset`，不写 index。
- Hybrid：写锁一直持有到物理 IO 结束（注释写明是有意为之）。
- discard：Sparse 做打洞，Log 追加 zeroed 映射，Hybrid 保留物理段并标记 zeroed，空隙补“无物理零段”。

**seal**（`LSMTFile::close_seal()`）：把 sealed 标志从 false 换成 true（防止重入），flush group commit，取 upper 的映射，tag 归 0，zeroed 段的 moffset 改成 `NO_PHYSICAL_OFFSET`；在**数据文件当前 EOF** 写 index（补齐 512，填充字节是 `0xff`），补 0 到 4K，从 header 复制出 trailer，改 vsize/index_offset/index_size，设 sealed、data、trailer 标志后写入。返回 `LayerDescriptor{sha256, size}`（来自增量 digest）。也就是说 **seal 是原地封口，不拷贝数据**，`ImageFile::close_seal()` 之后只需 rename。

**restack**（`ImageFile::create_snapshot_and_restack()`，由 daemon 的 `RestackSnapshot` RPC 调用）：
1. 拿 `state.write()`，阻塞所有 IO。
2. 记下 lowers（bottom→top），然后 `close_seal_and_reopen()`，把旧 upper 作为只读层重新打开。
3. rename `upper.data` 到 `output_layer_path`（要求同一文件系统；跨文件系统的情况由节点侧先 restack 到同目录再原子拷贝，见 `capture_live_overlaybd_snapshot()`）。
4. `prepare_runtime_upper()` 用同样的路径和模式建一个新的空 upper，`open_file_rw`。
5. `open_files_ro_with_premerged_cache(lowers + 刚封的层)`，再 `stack_files`。
6. `state.config.lowers.push(...)`，`state.base` 换成新栈。
7. 第 2 步之后任何失败都包装成 `RestackSnapshotTerminalFailure`，RPC 返回 `TerminalError`，节点据此把卷标记为不可安全恢复。设计取舍：**不回滚**，因为 rename 之后已经改变了磁盘状态。

**compact**（`lsmt/file/helper.rs::compact_to()`）：通用的“给定源层数组和映射数组，写出单层 sealed 文件”。先写 header（uuid 默认 nil，“Keep parity with OverlayBD C++”），然后把非零映射按 `writer.buffer_size()` 打包成 `CompactChunk`（一个 chunk 可以跨多个源段、跨层），并发数为 `concurrency`（默认 1）；零段只记录索引。最后写 index 和 trailer。上游的 zero-block 检测被关闭（`COMPACT_ZERO_DETECTION_ENABLED=false`，注释说上游 `is_zero_block()` 也被短路）。它的调用者有：`LSMTFile::commit/flatten/export_upper_as_sealed`、`merge_files_ro`、`compact_layers`（节点侧运行时层压缩），以及**内存脏页转层**（见第 7 章）。

**运行时层数预算**：`overlaybd_snapshot.rs::rewrite_lowers_with_runtime_roots()`。“运行时拥有的后缀层”的预算是 `32 - stable_prefix/4`（最小为 1），超出就整体 `compact_layers` 成一层。目的是远离 255 层（tag 只有 u8）的硬上限。未超出时，把这些层硬链接或拷贝到快照目录下的 `inherited-layers/NNNN/`。

**潜在问题（值得在书里讨论）**：`ImageFile::write_at*()` 在持有 `state.read()` 的情况下调用 `refresh_size_metadata()`，后者再次 `self.state.read().await`。tokio RwLock 是写优先的公平锁，如果此时 restack 的 `write()` 正在排队，第二次 read 会排在 writer 后面，而 writer 又在等第一次 read 释放，结果是**可能死锁**【推断，未见测试覆盖】。实际中 restack 发生在 VM 已暂停之后，触发概率低。另外每次写都刷新一次 size，也是额外开销。

**配图**：层栈装配管线（VirtualFile 装饰器链）；restack 七步时序图；Hybrid 写入 fragment 拆分示意。

---

### 第 4 章 后端：local / registry / OSS / tar / cache，以及远端 IO 调度运行时

**`VirtualFile` trait**（`io/virtual_file.rs`）：`read_at/read_at_into/write_at/write_bytes_at/size/truncate/sync/seek_data/seek_hole/discard/evict_range/evict_all/f*xattr`。在 `io-uring` feature 下另有 `*_with_ctx(IoCtx)` 系列，返回 **非 Send** 的 `LocalBoxFuture`，因为 `AsyncIoRing` 内部用了 `Rc`。`vfile_io.rs` 用 ZST 策略类型 `DirectRead/DirectWrite/CtxRead/CtxWrite` 做单态化：同一份 LSMT/ZFile/cache 代码既能产生 Send future 给后台使用，也能产生 !Send future 给 ublk queue 使用。注释说明这是绕开 async 闭包 HRTB 限制的写法，可以作为 Rust 设计案例。

**LocalFile**（`backend/local.rs`）：
- 普通 `read_at_into/write_at` **在当前线程同步 pread/pwrite**。TODO 里解释了不能用 spawn_blocking 的原因：`&mut [u8]` 不满足 `'static`，而且 spawn_blocking 不可取消，用裸指针会有 UAF 风险。
- ctx 路径通过 io_uring 提交 `Read/Write(Fd)`。注意用的是普通 fd，**不是 fixed file，也不是 fixed buffer**。O_DIRECT 时使用 4K 对齐的 `AlignedBuffer`。
- 不超过 4 KiB 的 buffered 写走同步 pwrite 快速路径（`BUFFERED_PWRITE_FAST_PATH_MAX`），注释承认这是一种取舍。
- `io_engine==2`（上游 libaio 编号）时下层只读文件打开 O_DIRECT。

**registryfs_v2**（名字对齐上游 registryfs_v2）：Range GET，支持 Basic/Bearer（`WWW-Authenticate` 挑战缓存 300s，token 最短剩余 30s），跟随重定向并缓存 URL 信息，默认重试 3 次，每 5 分钟刷新 HTTP client。`set_accelerate_address()` 对应上游的 P2P 加速地址：在 `RemoteOpenMode::Direct` 下由 P2P 门面充当缓存。

**OSS**（`backend/oss.rs`）：基于 opendal S3；URL scheme 为 `s3://` 或 `oss://`。分片上传 `upload_file_streaming()` 的注释里有 part size 与 10,000 分片上限、内存峰值 `(2c+2)·part` 的推导表，适合做旁注。

**tar 适配**（`backend/tar.rs`）：注释说明“不是完整的 tar 实现，只服务于 overlaybd remote blob：一个文件加 tar 头尾”。支持 ustar、GNU longname、PAX path/size，以及空 tar 魔数 `xxtar`。只做偏移平移（`base_offset`）。

**SwitchFile**（`backend/switch.rs`）：内部是 `m_file`（源）加 `m_local_file`（RwLock）。后台下载完成后 `set_switch_file(path)` 重新打开本地文件（同样经过 tar 和 zfile 识别），之后的 IO 都切到本地，切换失败则保持原状（有测试）。

**RuntimeDispatchFile**（`io/dispatch_file.rs`）——**这是一个很好的“踩坑”案例**：opendal/reqwest 会把连接驱动任务 `tokio::spawn` 到当前 runtime，而每个 ublk queue 都有自己的 current_thread runtime，设备销毁时 runtime 随之销毁。如果 HTTP 连接池是进程共享的，就会出现：①设备 B 的读被设备 A 的 queue 线程驱动；②销毁 A 时杀掉 B 正在用的连接。解决办法是每个 `ImageService` 建一个专用多线程 runtime `obd-remote-io`（`remoteIoWorkers`，AgentENV 配置默认 4），所有远端 open/read/size 都 `handle.spawn` 到那里执行，再在调用方 await。`read_at_into` 故意保留默认实现（多一次拷贝），因为 `&mut [u8]` 不能跨任务传递。`remote_runtime()`（`image_service.rs`）里，cache 后台 worker 和下载调度器的构造也放到这个 runtime 上，原因相同。注意 `Runtime::drop` 在 async 上下文里会 panic，所以要用 `shutdown_background`。

**Full-file cache**（`backend/cache/full_file_cache/*`）——AgentENV 自研，与上游 full_file_cache 的元数据格式不兼容：
- 每个远端文件对应一个目录 `<cacheDir>/<sha256(key)>/{data, meta.bin}`。key 经 `basename_transform` 变成 `/<basename>`（即 digest），因此同一 digest 在不同 registry 之间也能共享缓存。
- `data` 是稀疏文件，整体 mmap（`MMapRegion`），读命中时直接从 mmap 拷贝。`index: RwLock<RoaringBitmap>`，每块 1 bit，块大小默认 256 KiB。
- 缺失的块通过 `block_states: HashMap<blk, wakers>` 做 **loader 选举**（同一块只回源一次，其他请求挂 waker 等待）；回源时用 `read_at_into` 直接写进 mmap 页。远端源因为经过 RuntimeDispatchFile，会多一次块大小的拷贝。
- `reserve_range` 返回 RAII guard：失败或取消时打洞回收，保证容量记账准确。`refill_eviction_barrier` 协调回填和驱逐。
- `meta.bin`：`CacheMetaDiskHeader{magic "OBCH"(0x4f424348), version 1, source_size, block_size, last_access, hits, misses, refills}`，后面是 key_len、key、roaring 序列化、CRC32C。每 300s 做一次 checkpoint，每 1s 跑一次驱逐循环，水位 90%。
- 默认值：容量 4 GiB，单次预取上限 32 MiB，最大并发回填 128。

**后台下载**（`backend/cache/bk_download.rs`、`download_gate.rs`）：
- 每个 `FileCacheBackend` 一个调度器，按 cache_id 去重；只限制**执行**：`max_concurrent_files` 个文件任务、`max_inflight_blocks` 个 chunk（chunk 默认 16 MiB）；单块超时后对冲重试，最多 3 次。
- `download_gate`：进程全局计数前台在途读。有前台读时，后台块会被挂起，但保留下限（后台 floor；startup 类预取的 floor 更高），防止饿死。注释明确说**依赖单进程假设**（所有设备都在同一个 daemon 进程里）。
- 内存快照设备的后台下载会等沙箱 envd 就绪（`NotifySandboxReady` RPC），最多等 `SANDBOX_READY_FALLBACK=20s`。
- 下载完成后通过 switch 切到本地，或者直接从 cache 读。

**P2P HTTP 门面**（`src/overlaybd/p2p/facade.rs`，节点主进程里的 axum 服务）：`GET /p2p-http/{*origin}` 先查 P2P（lookup 超时 300ms，range 读取超时 2s），未命中再回源；`GET /p2p-uuid/{uuid}` 只走 P2P，未命中返回 404；`POST /p2p-control/publish-layer` 由 daemon 在层完成后调用发布（限制在允许的根目录内）。descriptor 命中缓存 5 分钟，未命中缓存 5 秒。这套接口与上游 overlaybd 的“accelerate address”用法同构。

**配图**：一次远端读穿过的装饰器栈（自下而上：HTTP → Dispatch → CachedFile → Tar → Switch/ZFile → LSMT → ImageFile → ublk）；cache 的 loader 选举状态机；三种 runtime（ublk queue 的 current_thread、obd-remote-io、daemon 主 runtime 4 线程）之间的关系。

---

### 第 5 章 ublk 库（`storage/ublk`）

**依赖**：`libublk-rs-sys`（git rev `c6a3e06`，只用 FFI 常量和结构体）、`io-uring 0.7.9`。`queue.rs` 开头写着 “The original ublkqueue from libublk is not flexible for our use case, we try to build our own.”

**控制面**（`ctrl.rs::UVMUblkCtrl`）：打开 `/dev/ublk-control`，通过 ctrl ring（`IoRingWorker<Entry128>` 独立线程）提交 `UringCmd80`。已实现的命令：
`UBLK_U_CMD_GET_FEATURES`、`ADD_DEV`、`SET_PARAMS`、`START_DEV`、`STOP_DEV`、`DEL_DEV`、`GET_DEV_INFO`，以及自定义编码的 `UBLK_U_CMD_UPDATE_SIZE`（`ublk_caps.rs`：`_IOWR('u',0x15, ublksrv_ctrl_cmd)` = `0xC0207515`，对应特性位 `UBLK_F_UPDATE_SIZE = 1<<10`；注释提醒 bit0 是 `UBLK_F_SUPPORT_ZERO_COPY`，不要搞混）。
- Builder 默认值：`nr_queues=1, depth=16, max_io_buf_bytes=256KiB, flags=0, dev_id=u32::MAX`（由内核分配）。
- `zero_copy(true)` 只会设置 `UBLK_F_AUTO_BUF_REG`。
- `load_ublk_module()` 依次尝试 `modprobe ublk_drv`、`sudo -n modprobe`。
- **使用到的 UBLK_F_\***：只有 `UBLK_F_AUTO_BUF_REG`（库支持，但生产路径不开）和 `UBLK_F_UPDATE_SIZE`（只做检测）。**没有使用** `UBLK_F_USER_RECOVERY*`、`UBLK_F_UNPRIVILEGED_DEV`、`UBLK_F_USER_COPY`、`UBLK_F_NEED_GET_DATA`。

**设备**（`dev.rs`）：
- `UVMUblkDevBuilder::build()`：`add_dev`，然后重试打开 `/dev/ublkcN`（每 25ms 一次，最多 64 次，等 udev 生效）。
- `start()`：`get_dev_info` 校验状态为 `UBLK_S_DEV_DEAD`，每个 queue 起一个线程，然后 `set_params`、`start_dev`。
- `queue_work()`：每个 queue 是一个 OS 线程 `ublk-q-<dev>-<qid>`，线程里用 current_thread runtime 加 `LocalSet`。runtime 设置了 **`on_thread_park` 钩子，在线程空闲时调用 `uring.submit()`**，这样 SQE 被批量提交（这是关键性能技巧）。每个 tag 一个 `slot_task`。
- 注释解释了为什么每个 queue 用独立 ring、不跨设备共享：共享 ring 加注册 cdev fd 时，DEL_DEV 会卡住，因为 rsrc_node 的引用计数会被其他设备持有。
- `slot_task(tag)`：分配缓冲（AutoReg 或 User，User 按 512 对齐并注册到 ring 的 sparse buffer 表），发 `UBLK_U_IO_FETCH_REQ`，然后循环：读 mmap 的 `ublksrv_io_desc[tag]`，调用 `tgt.handle_io_request()`，再发 `UBLK_U_IO_COMMIT_AND_FETCH_REQ`（把结果作为 result）。代码中有两处 `FIXME: should we handle EINTR?` 和一处 `TODO: update auto buffer's size`。

**queue**（`queue.rs::UVMUblkQueue::new()`）：ring 参数为 `sqe=cqe=depth*2`、`nr_sparse_buffer=depth*4`、`nr_sparse_file=16`。spawn_local 一个 `handle_completion()`（用 AsyncFd 监听 ring fd 可读，然后收割 CQE）。cdev 注册为 fixed file（`register_fd`）。`UblkQueueIoDesc` 对 cdev 做 mmap，偏移为 `UBLKSRV_CMD_BUF_OFFSET + qid * round_up(UBLK_MAX_QUEUE_DEPTH*sizeof(desc), page)`，`PROT_READ|MAP_SHARED|MAP_POPULATE`。IO 命令通过 `UringCmd16(Fixed(cdev_idx))` 提交；AutoReg 时用 `override_sqe!` 宏改写 `sqe.addr = ublk_auto_buf_reg_to_sqe_addr(..)`（`RawSqe` 是从 libublk 抄来的布局，属于不安全代码）。

**io_buffer**（`io_buffer.rs`）：
- `UserBuffer`：用户态分配、对齐，并 `register_buffer` 进 ring。`io_cmd.addr` 指向它，内核把写数据拷进来、把读结果拷出去。
- `AutoRegBuffer`：只占用 sparse buffer 表里的一个下标（`occupy_sparse_buffer_index`），由内核在请求到达时自动把请求页注册到该下标（UBLK_F_AUTO_BUF_REG），用户态用 `ReadFixed/WriteFixed(buf_index)` 让后端文件和块设备请求页直接 DMA/拷贝，**不经过用户态缓冲**。此时 `io_cmd.addr` 必须为 0。
- `IOBuffer::split_at`、`IOBufferView::read_all_from_fixed/write_all_into_fixed` 提供分片的 fixed IO。

**OverlaybdTarget**（`impls/overlaybd_target.rs`）：
- 状态放在 `ArcSwap<TargetState{image, dev_sectors, logical_bs_shift(=ImageFile.block_size=512→9), physical_bs_shift=12, discard_supported}>`，可以热切换（`swap_state()`，warm pool 用，前提是设备空闲）。另有 `ArcSwapOption<StartupPackRecorder>`。
- ublk 参数（`build_ublk_params()`）：BASIC，加上可写时的 DISCARD；`io_min_shift=logical`，`io_opt_shift=12`，`max_sectors=max_io_buf_bytes>>9`（即 512 扇区），discard 粒度 512，`max_discard_segments=1`，`max_write_zeroes_sectors=0`。
- 支持 Read、Write、Flush（`image.sync()`）、Discard；WriteZeroes 和 Zone 系列返回错误。错误码映射见 `anyhow_to_ublk_errno()`（例如 PermissionDenied 映射为 EROFS）。
- **Read/Write 只接受 `IOBuffer::User`，AutoReg 直接 bail**。原因【推断】：LSMT 需要按映射把一次请求拆到多个层文件和多个偏移，而且 ZFile 要解压，fixed-buffer 零拷贝只适合 1:1 直通的 target（如 loop），所以零拷贝能力目前只停留在库层面。
- 每个读请求先调用 `recorder.observe_submit()` 记录首次触达的页（用于 startup pack）。

**内核版本**：文档写的是 “kernel 6.8+”，并称 AutoRegBuffer “kernel 6.8+”。【需核实】据上游内核历史，`UBLK_F_AUTO_BUF_REG` 和 `UBLK_U_CMD_UPDATE_SIZE` 都是 2025 年（约 6.15–6.16）才合入的，6.8 内核上 GET_FEATURES 不会返回 bit10。daemon 对此有降级：`detect_ublk_features()` 遇到 ENOTTY/EINVAL/EOPNOTSUPP 时视为 0；不支持 UPDATE_SIZE 时，warm pool 只复用 `dev_sectors` 相同的设备（`take_idle_device()`），并且默认关闭 startup_prewarm（`pool_config.startup_prewarm = … unwrap_or(update_size_supported)`）。写书时建议给出“最低 6.x 可用、6.16+ 才能用上全部特性”的分级表。

**遗留 CLI**：`storage/ublk/src/main.rs`（`uvm-ublk create/delete`），每个进程一个设备，只支持单 queue（`nr_queues!=1` 时报错），`Recovery => unimplemented!()`，注释 “NOTE: why we use fork” 已经过时（代码里并没有 fork）。实际已被 daemon 取代。`lib.rs::spawn_data_io_ring_worker()` 没有调用方。

**配图**：ublk 控制面和数据面总图（/dev/ublk-control、ublkcN 的 mmap desc、UringCmd FETCH/COMMIT_AND_FETCH 循环）；queue 线程内部（LocalSet、depth 个 slot task、completion task、on_thread_park submit）；UserBuffer 与 AutoReg 的数据流对比。

---

### 第 6 章 ublk-daemon

**进程模型**（`storage/ublk-daemon/src/main.rs`）：
- 由节点进程 `UblkDaemonClient::new()` spawn。需要 CAP_SYS_ADMIN 有效并委派给子进程（`configure_daemon_capabilities`），子进程放在独立进程组（`process_group(0)`，避免 Ctrl+C 中断 restack），stdout 打印 `ready` 作为就绪信号（等待 30s）。
- daemon 启动步骤：把 RLIMIT_NOFILE 提到 1,048,576；建 4 线程 tokio 主 runtime；启动 metrics HTTP（默认 `0.0.0.0:9103`）；创建默认 `ImageService`；ctrl ring 是 `spawn_io_ring_worker::<Entry128>(0)`；读取 `[pool.block]`、`[ublk.overlaybd].resize_timeout_secs`；检测 ublk 特性；对父进程 `pidfd_open` 并监听可读事件（父进程退出即关闭，注释说明比 `PR_SET_PDEATHSIG` 更可靠，因为后者按线程触发）。SIGTERM/SIGINT 也会触发关闭。
- 处理过期 socket：能 connect 上说明已有进程在用，直接报错；connect 失败就删掉。

**RPC 协议**（`protocol.rs`）：一个连接只处理一个请求（`handle_connection` 里 `recv_message` 一次），帧为 `u32 BE 长度 + JSON`，上限 16 MiB。用 serde 的 tag 枚举：

| 请求 `kind` | 字段 | 正常响应 `status` | 说明 |
|---|---|---|---|
| `create_overlaybd` | image_config, global_config | `device_created{dev_id, device_path}` | 原始设备，不物化运行时（mem dedicated 和非池路径用） |
| `create_overlaybd_runtime_device` | source_image_config, global_config, runtime_dir, read_only, runtime_upper_mode(默认 LogStructured), requested_virtual_size?, known_source_virtual_size?, allow_shrink | `overlaybd_runtime_device_created{dev_id, device_path, actual_virtual_size, runtime_image_config_path}` | rootfs/extra drive：改写 lower 路径、建 upper、必要时调用 `overlaybd-resize` 并复验 |
| `delete` | dev_id | `deleted` | 先中止录制，再 quiesce（STOP_DEV 后最多等 5s 让 queue 线程退出），**drop 掉持有 cdev fd 的对象**，然后 DEL_DEV |
| `restack_snapshot` | dev_id, output_layer_path | `restack_snapshot_created{descriptor?, data_stat?, ext4_used_bytes?}` | 池化设备会持有按 image 粒度的写锁；顺带读取 ext4 superblock 统计已用空间 |
| `get_features` | — | `features{flags}` | |
| `notify_sandbox_ready` | device_key | `ok` | 释放被 envd 就绪门挡住的后台下载 |
| `start_pack_recording` | dev_id, output, max_pages, min_window_ms, quiet_ms, max_window_ms | `ok` | 挂载 `StartupPackRecorder`，按 100ms tick 判定窗口 |
| `pack_recording_status` | dev_id | `pack_recording{state: recording / done{pages,bytes,remote_bytes,path} / failed{reason}}` | |
| `abort_pack_recording` | dev_id | `ok` | 幂等 |
| `prefetch_startup_pack` | image_config, global_config, url, pack_size, index_sha256, mem_virtual_size, timeout_secs | 总是 `ok` | 尽力而为 |
| `acquire_overlaybd` | image_config, global_config, virtual_size?, access_mode(exclusive/shared) | `device_acquired{dev_id, device_path}` | warm pool |
| `release_overlaybd` | dev_id | `released` | |
| `update_size` | dev_id, new_sectors | `size_updated` | 需要 `UBLK_F_UPDATE_SIZE` |
| `shutdown` | — | `ok` | |
| 错误 | | `terminal_error{message}` / `invalid_request{message}` / `error{message}` | Terminal 表示状态已被改动，不能重试 |

客户端超时：默认 30s，snapshot 360s，runtime device 可配置。

**ImageServiceCache**：按规范化后的 global_config 路径懒加载创建 `ImageService`（rootfs 和 mem 用不同的 global 配置，比如 `mem-overlaybd-global.json`），每个 service 有自己的 remote runtime 和 cache。

**Warm pool**（`server.rs::PoolState`）：
- `idle`（`warm_pool` crate，提供低/高水位）、`active_exclusive{dev_id→ActiveExclusive}`、`active_shared{(image_config, global_config)→ActiveShared{refcount}}`，以及反向索引 `shared_by_dev_id`（注释说用 `iter_mut` 扫描在并发 release 下会死锁，所以加了这个）。
- `image_locks`：按 image 粒度的 RwLock，让 restack 和同镜像的 open 互斥，但不会串行化无关镜像。
- **占位镜像**：`placeholder_for(virtual_size)` 按大小懒构建 daemon 自有的空 sparse 镜像（无 lower，纯本地）。归还设备时先 `BLKFLSBUF`（`clear_page_cache`，ioctl 0x1261）清块设备页缓存，再 `swap_state` 到同尺寸的占位镜像，这样空闲池**不会钉住业务镜像**（不持有其 ImageFile 和远端连接）。
- 获取：`prepare_overlaybd_device()` 有空闲设备就 `swap_state`，必要时再 `update_size`；没有就 `create_new_device()`（ADD、START，然后 `wait_for_ublk_dev` 最多约 30s，同时处理 udev 权限竞争）。
- Shared 获取有双重检查：并发时如果对方先插入，就停掉自己多建的设备。
- 补充：`schedule_idle_pool_refill()` 用 CAS 合并补充请求，失败时退避 1s。

**生命周期与故障**：
- 关闭顺序（`stop_all_devices()`）：中止录制，删除 managed 设备，然后依次处理 active exclusive、active shared、idle。
- 启动失败清理（`cleanup_failed_ublk_start()`）：STOP（遇到 ENODEV 就提前返回），等 5s，drop，用同一 dev_id 新建 ctrl 再 DEL。
- **daemon 崩溃**：客户端 watchdog 在子进程退出后设置 `daemon_dead`，之后 RPC 立刻失败，**没有自动重启或重连，也没有 ublk user recovery**。内核里的 ublk 设备会因为 server 退出被内核清理（ublkc 关闭，设备进入 DEAD），正在跑的 VM 的块 IO 会出错【推断】。这是可以在书里讨论的取舍：单进程集中管理换来了全局准入（download gate）和共享 cache，代价是单点故障。
- `metrics_server.rs` 只有 37 行。

**运行时物化**（`runtime.rs::materialize_runtime_contents()`）：解析 base vsize（可由调用方提供，否则打开镜像读取）→ `validate_requested_virtual_size`（默认不允许缩小）→ 判定 upper 模式 Absent/Existing/Create → `prepare_runtime_upper` → 改写并写出 `runtime_dir/image.json` → 如果大小有变化，在 daemon 全局互斥锁下运行 `overlaybd-resize --config … --size <GiB> --service_config_path <resize-global>`（使用隔离的 cacheDir `resize-blocks/`，下载关闭；超时 kill；输出读取有上限）→ `verify_resized_runtime` 用 Rust 重新打开校验。注意 resize 只按 GiB 粒度（`target_size / GIB`）。

**配图**：节点、daemon、内核三者的部署图；设备在 pool 中的状态机（new → active exclusive/shared(refcount) → release → BLKFLSBUF → swap 到占位镜像 → idle → acquire → swap 到业务镜像）；RPC 时序（resume 时 acquire shared → FC load）。

---

### 第 7 章 基于 ublk 的内存快照（核心亮点）

**暂停/创建**（`src/sandbox/firecracker/sandbox.rs::snapshot_memory_to_overlaybd()`，以及 `overlaybd_snapshot.rs`）：
1. `fc_instance.create_state_only_snapshot(vm_state_path)`：`PUT /snapshot/create`，`snapshot_type=Diff`。注释说明 “The memory data path is handled by AgentENV through dirty memory ranges”，也就是 FC 只写 `vm_state.bin`，不写内存文件。
2. `GET /vm/dirty-memory-ranges`，这是 kvcache-ai fork 版 Firecracker 新增的 API。返回 `DirtyMemoryRanges{page_size, memory_size, ranges:[{base_host_virt_addr, image_offset, length}]}`，语义是“与快照文件相同的连续内存镜像布局”（`thirdparty/firecracker-client/src/models/dirty_memory_ranges.rs`），image_offset 已经去掉 MMIO 空洞。
3. `dirty_ranges_to_segment_mappings()`：校验 page_size 必须为 4096，以及各项 4K 对齐、不越界；按 `Segment::MAX_LENGTH`（16383 扇区）切段，生成 `SegmentMapping{offset=image_offset/512, length, moffset=HVA/512, zeroed=false, tag=0}`；排序后拒绝目标区间重叠。**这里复用了 moffset 字段来存“源地址”**，是一个巧妙的复用。
4. `ProcessVmReader::new(fc_pid)`：`VirtualFile` 实现里 offset 就是 HVA，`read_at_into` 调用 `process_vm_readv` 并循环处理短读和 EINTR。有 TODO：这是同步调用，跑在 tokio worker 上。
5. `publish_memory_overlaybd_layer()`：`compact_to(&[ProcessVmReader], mappings, memory_size, CommitArgs)`，并发 32（`DIRECT_MEMORY_SNAPSHOT_COMPACTION_CONCURRENCY`），写到 `mem_overlaybd/overlaybd.commit.tmp` 后 rename，失败时删除 tmp。本地输出总是 raw（mode 由调用方传入）。
6. `build_mem_snapshot_image_config()`：继承恢复时用的 memory image.json 的 lowers，追加新层，必要时按层数预算压缩运行时后缀（`mem_compacted.commit`）。于是**内存快照也是增量分层的**：每次暂停只写自上次恢复以来的脏页。
- 和 uffd 方案的对比：FC 自己跟踪脏页（KVM dirty log），不需要用户态缺页处理；读取用一次 `process_vm_readv` 系统调用即可，不经过 FC 写文件，也不需要额外的临时内存文件。

**恢复**（`sandbox.rs` 约 2155–2280 行）：
1. 非录制 VM：如果 snapshot 带有 startup pack 且来源是 OSS，先发 `prefetch_startup_pack` RPC。
2. `UblkDeviceManager::get_or_create_shared_mem(spec, mem_virtual_size)`（`src/sandbox/ublk/device.rs`）：
   - 节点侧以 canonicalize 后的 image_config 为 key，用 `DashMap<key, Weak<SharedReadOnlyDeviceInner>>` 先尝试 upgrade 复用。如果同一 key 正在释放，就等待 `Notify`。
   - 未命中时：池开启则发 `AcquireOverlaybd{access_mode: Shared}`，由 daemon 侧 refcount（第二层计数）；池关闭则 `CreateOverlaybd`。
   - **`cache_fd`**：节点另外 `File::open(/dev/ublkbN)` 并一直持有。注释：“Linux clears a block device's page cache when its last opener closes (blkdev_put_whole -> kill_bdev). Keep an opener between sandbox launches; the daemon's /dev/ublkcN handle does not keep /dev/ublkbN open.” 这样前后两次启动之间页缓存不会丢失。
   - 最后一个 Arc 被 drop 时异步 release 并清理条目。stop 时显式调用 `release()`，避免和下一次 resume 竞争。
3. `fc_instance.load_snapshot_file(vm_state, /dev/ublkbN, [("eth0","tap0")], resume_vm=false, track_dirty_pages)`：`BackendType::File`。
4. Firecracker 的 File 后端会把内存文件 **MAP_PRIVATE** 映射【推断：仓库内没有这段代码，依据是上游 Firecracker 的实现和 `architecture.md` 中 “mmaps the block device and COWs pages into anonymous memory on first write”】。读缺页命中块设备页缓存（多个 VM 共享），写入则在本进程内 COW 到匿名页，所以块设备永远是只读的，`OverlaybdTarget` 也是只读（不支持 discard）。
5. 读请求的链路：guest 缺页 → FC mmap → 块设备页缓存未命中 → ublk → daemon 的 queue 线程 → ImageFile → LSMT 合并索引 → 本地 commit，或远端（经过 cache 和 P2P）。
- 沙箱 envd 就绪后调用 `notify_sandbox_ready(device_key)`，放开后台下载。

**Startup pack（首触页预取）——值得单独成一节**：
- 录制：发布快照后，用该快照启动一个一次性 VM，内存设备用 **dedicated**（非共享，否则共享页缓存会把首次触达掩盖掉，见注释）。daemon 在设备上挂 `StartupPackRecorder`（`storage/ublk/src/impls/startup_pack_recorder.rs`）：原子 bitmap 加有序首触日志，只覆盖 16 GiB 设备空间；按读延迟估算远端字节（>某阈值即认为是远端，本地约 0.1ms，OSS 约 20ms）。窗口状态机参数为 `min_window/quiet/max_window`。输出 trace（`startup_pack.rs` 编解码，上限为 1 GiB 覆盖内存）。
- 发布：trace 展开成 manifest（`startup_manifest.rs`，`AENVMF01`：32B 头，然后是 prefix pages，然后是按首触序排列的 `(start,len)` 区间表）。
- 恢复：`pack_planner.rs` 只用元数据（LSMT 合并索引、ZFile jump table 的 extent、tar base offset），把逻辑页翻译成**最终对象的 256 KiB 块**；`startup_pack_task.rs` 合并相邻块（最多 64 块即 16 MiB 一次读），在下载调度器里以 startup 类优先级回填同一份 cache（与 guest 缺页共用 loader 选举去重）。
- 版本命名混乱：注释中同时出现 “v2 startup memory pack”（`image_service.rs`）、“v3 startup manifest”（`protocol.rs`、`startup_pack_task.rs`）、“v4 startup manifest”（`src/sandbox/firecracker/startup_pack.rs`），而文件魔数是 `AENVMF01`。写书时需要统一说法。

**配图**：暂停时序（FC Diff → dirty ranges → mapping（moffset=HVA）→ ProcessVmReader → compact_to → commit）；恢复时的共享拓扑（N 个 FC 进程 → 一个 /dev/ublkbN → 页缓存 → daemon）；两级 refcount 示意；startup pack 的录制、发布、预取三段图。

---

### 第 8 章 io_uring 工具层（`storage/util`）

- `io_ring/uring.rs::AsyncIoRing<S: Entry|Entry128>`：`Rc<RefCell<IoUring>>`，**单线程**使用。每个 SQE 的 user_data 是 slab key；`RingFuture` 被 drop 时若 CQE 还没到，就把 slot 标记为 cancelled，`reap_cqe` 收到迟到的结果后回收 slot，防止 slab key 被复用后结果误投递，这是取消安全的关键设计。`handle_completion()` dup 一份 ring fd 交给 tokio `AsyncFd`，可读时收割 CQE。
- `AsyncIoRingBuilder`：`nr_sparse_buffer`（IORING_REGISTER_BUFFERS2 稀疏表，内核上限 1<<14）、`nr_sparse_file`（上限 1<<20）、`set_fds`（与前者互斥）、sqe/cqe 数量（上限 32768/65536）。
- 提供 `register_buffer`、`occupy_sparse_buffer_index`/`release_sparse_buffer_index`（给 AUTO_BUF_REG 用）、`register_fd`/`unregister_fd(_sync)`。
- `io_ring/worker.rs::IoRingWorker`：独立线程加 current_thread runtime，经 mpsc 接收 `IoRingRequest{Io, OccupySparseBuffer, ReleaseSparseBuffer, RegisterBuffer…}`，`IoRingHandle` 可以跨线程（Send）提交。线程局部变量 `URING`/`URING128`。**生产中只有 ublk ctrl ring 用它**（Entry128）。数据面的 `spawn_data_io_ring_worker` 没有调用方。
- `io_ring/mod.rs`：`IoUringSubmitter{Box,SendBox}` trait 家族，以及 `read/write_exact_at(_fixed)` 循环（处理短读和 EINTR）。
- 其他：`MMapRegion`（cache 用）、`AlignedBuffer`（O_DIRECT 用）、`CompactWriter/CompactBuffer`（compact 输出抽象：Vec 或 ZFile）、`AlwaysSend`（把已知安全的 future 包装成 Send，用于 `buffer_unordered`）。
- **`ReloadableIDAllocator`（223 行）在 storage/util 之外没有任何引用**，是旧方案中由用户态分配 dev_id 的遗留物；现在 dev_id 由内核分配（`dev_id=u32::MAX`）。
- 编译约束：`io-uring` feature 在非 Linux 目标上会 `compile_error!`；overlaybd crate 本身可以在 macOS 上编译（有 sys/ 的 macOS 分支，作为开发便利）。

**配图**：AsyncIoRing 的 future/slab/CQE 生命周期（包括取消路径）；三类 ring 的归属（ublk queue ring = 每 queue 线程局部；ctrl ring = IoRingWorker 线程；LocalFile ctx 读复用 queue ring）。

---

### 第 9 章 uffd-core（保留的备选方案）

- `storage/uffd-core`（784 行，**不在 workspace 成员中**，`Cargo.toml` 的 members 没有它；FC 侧 `load_snapshot_uffd()` 标为 `#[allow(dead_code)]`）。
- `handler.rs::UffdHandle`：绑定 UDS，等待 FC 连接，通过 SCM_RIGHTS 接收 uffd 和 `GuestRegionUffdMapping{base_host_virt_addr, size, offset, page_size}`（`scm.rs`），进入缺页循环：Pagefault 时调用 `backend.read_page_at_offset()`，然后 UFFDIO_COPY 或零页；Remove（virtio-balloon 的 MADV_DONTNEED）时记为 Removed。注释说明不能在处理 Remove 时 drain，否则内核的 mmap_changing 计数会卡住。因为 FC 的 uffd 没有实现 WP 模式，所以“访问过即视为脏”。
- `backend.rs::MemoryImageBackend` trait：`pagesize/read_page_at_offset/snapshot(peer_pid, regions, dirty_pages, layer_dir, writer)`。
- `overlaybd.rs::OverlaybdMemoryImage`：底层就是 `ImageFile`，snapshot 时同样用 `ProcessVmReader` 加 `compact_to`（与现行方案相同的“HVA 当 moffset”技巧，说明现行方案就是从这里演化来的）。
- 被替换的原因（可以从代码和文档推断）：每个 VM 一个用户态缺页 handler、每页一次 UFFDIO_COPY，**无法跨 VM 共享页缓存**；脏页只能粗略估计；需要额外的线程和 socket。ublk 加 File 后端则把共享交给内核页缓存。

---

## 3. ublk 细节速查

| 项 | 值 / 位置 |
|---|---|
| 控制命令 | GET_FEATURES、ADD_DEV、SET_PARAMS、START_DEV、STOP_DEV、DEL_DEV、GET_DEV_INFO、UPDATE_SIZE（`ctrl.rs`，`UringCmd80`，ctrl ring 为 Entry128） |
| IO 命令 | `UBLK_U_IO_FETCH_REQ`、`UBLK_U_IO_COMMIT_AND_FETCH_REQ`（`UringCmd16`，cdev 为 fixed file） |
| 用到的特性位 | `UBLK_F_AUTO_BUF_REG`（库支持，生产不开）、`UBLK_F_UPDATE_SIZE=1<<10`（检测后决定池策略）；dev.rs 的日志里检查的却是 `UBLK_F_SUPPORT_ZERO_COPY`，与实际设置的位不一致（小 bug） |
| 未用 | USER_RECOVERY(_REISSUE/_FAIL_IO)、UNPRIVILEGED_DEV、USER_COPY、NEED_GET_DATA、ZONED |
| 队列 | `nr_hw_queues=1`（daemon 不改），每 queue 一个线程 `ublk-q-<dev>-<qid>`，queue depth 16，每 slot 一个 256 KiB UserBuffer（512 对齐），ring sqe/cqe=32，sparse buf=64，sparse file=16 |
| 设备参数 | logical 512、physical 4096、io_opt 4096、max_sectors 512（256 KiB）、discard 仅在可写时提供 |
| 设备节点 | `/dev/ublkcN`（char，daemon 持有）、`/dev/ublkbN`（block）；udev 规则 `src/setup/ublk.rs` 设置 MODE 0660 和当前组 |
| 等待 | cdev 打开重试 64×25ms；`wait_for_ublk_dev` 等 bdev 可读约 30s（区分 NotFound 与 PermissionDenied） |
| 内核版本 | 文档写 6.8+；AUTO_BUF_REG 和 UPDATE_SIZE 需要更新的内核（【需核实】，约 6.15–6.16） |

---

## 4. ublk-daemon RPC 与生命周期

见第 6 章的表格。补充：
- **一个连接一个请求**，所以客户端每次调用都要重新 connect，没有长连接和多路复用，简单可靠。
- daemon 侧的 `ManagedDevice{dev, image}`（非池设备）和 `PoolState`（池设备）是两套并存的表。`RestackSnapshot`/`Delete` 先查 managed，再查 pool。
- 失败语义分三类：`invalid_request`（参数错误，可以改参数重试）、`error`（可重试）、`terminal_error`（已经改动了状态，例如 restack rename 之后失败）。
- 节点侧 `UblkDeviceManager` 是全局单例（`init_global`），`is_available()`；`shutdown_daemon()` 用于节点优雅退出。

---

## 5. 内存快照端到端（压缩版，可直接作为章节骨架）

```
[暂停]
FC: PATCH /vm Paused
 → PUT /snapshot/create {snapshot_type: Diff}           → vm_state.bin（不含内存）
 → GET /vm/dirty-memory-ranges                           → [{hva, image_offset, len}], memory_size, page_size=4096
AgentENV:
 → dirty_ranges_to_segment_mappings: (offset=img/512, len≤16383, moffset=hva/512)
 → compact_to([ProcessVmReader(fc_pid)], mappings, memory_size, Raw, concurrency=32)
      每个 chunk: process_vm_readv(fc_pid, hva..) → 写 data；最后 index+trailer
 → mem_overlaybd/overlaybd.commit（sealed LSMT，raw）
 → memory image.json = 继承的 lowers（可能压缩为 mem_compacted.commit）+ 新层
[rootfs 同时]
 → RestackSnapshot RPC → daemon: ImageFile::create_snapshot_and_restack（原地 seal + rename + 新 upper）
[发布（可选）]
 → 重打包成 ZFile（publish_compression）→ OSS managed-layers/{digest}；P2P 宣告
 → 可选：起一次性 VM 录制 startup trace → manifest 上传
[恢复]
 → (OSS pack) PrefetchStartupPack RPC
 → get_or_create_shared_mem: 节点 Weak 表 →（池）AcquireOverlaybd{Shared} → daemon refcount++ / 复用或新建设备（swap_state）
 → 节点保持 /dev/ublkbN 的 cache_fd
 → PUT /snapshot/load {mem_backend: File(/dev/ublkbN), resume_vm:false, track_dirty_pages}
 → FC mmap（MAP_PRIVATE，见上游）→ 缺页 → bdev 页缓存（同快照的 VM 共享）→ ublk → daemon → LSMT → 本地/缓存/远端
 → envd ready → NotifySandboxReady → 放开后台下载
[停止]
 → 停 FC → release 共享句柄 → 节点 refcount 归零 → ReleaseOverlaybd → daemon refcount 归零 → BLKFLSBUF → swap 到占位镜像 → idle
```

---

## 6. 意外发现、死代码、TODO 与技术债

1. **零拷贝只停留在库层面**：`OverlaybdTarget` 拒绝 `AutoReg`；daemon 从不调用 `.zero_copy(true)`；文档写 “AutoRegBuffer（zero-copy…kernel 6.8+）” 容易误导读者。
2. **daemon 无崩溃恢复**：没有 UBLK_F_USER_RECOVERY，客户端 watchdog 只做“快速失败”。`uvm-ublk` CLI 里有 `Recovery => unimplemented!()`。
3. **死代码**：`LinearizedBptree/IndexLBPT`（只有测试使用）；`ReloadableIDAllocator`（无引用）；`spawn_data_io_ring_worker`（无调用）；`GlobalConfig.nr_io_rings`（仅保留默认值）；`load_snapshot_uffd`（dead_code）；`uffd-core` 整个 crate；`storage/ublk/src/main.rs` 遗留 CLI（单 queue，注释过时）；`LSMTFile::create(sparse_rw: bool)` 标为 legacy helper。
4. **潜在死锁**：`ImageFile::write_at*` 持有 `state.read()` 的同时又调用 `refresh_size_metadata()` 再读一次锁（见第 3 章）。
5. **seal 时 index 补齐用 0xff**，而 `compact_to` 用 `INVALID_SEGMENT_OFFSET`（长度为 0 的映射）补齐。两者都不会被解析（受 index_size 限制），但风格不一致；`load_index` 里 `m.offset()==u64::MAX` 的判断永远不会成立（offset 只有 50 位）。
6. **dev.rs 的日志字段 `zero_copy` 检查的是 `UBLK_F_SUPPORT_ZERO_COPY`**，而 builder 设置的是 `UBLK_F_AUTO_BUF_REG`。
7. `FIXME: should we handle EINTR?`（`dev.rs` 两处）；`TODO: update auto buffer's size according to io_desc`；`ComboIndex::new` 的 `FIXME`；`ZFileBuilder` 的 `pool.recv()` 阻塞（TODO）；`LocalFile::read_at_into/write_at` 同步阻塞（TODO，有详细原因说明）；`ProcessVmReader` 同步 `process_vm_readv`（TODO）。
8. **Startup pack 版本号混用 v2/v3/v4**，魔数却是 `AENVMF01`。
9. **Resize 依赖 C++ 子进程**，只有 GiB 粒度，全局串行（一把 resize 锁），超时默认 120s。
10. `download_gate` 和 premerged-index 锁都是**进程全局**状态，注释写明依赖“所有设备在一个 daemon 进程中”。
11. 未迁移的上游特性：warp/turboOCI（`targetFile/targetDigest`）、gzip 索引、OCF/download 缓存类型。因此 AgentENV 不支持 turboOCI 或 gzip 原生懒加载，OCI 层必须先通过 C++ 工具转成 overlaybd。
12. `containerd-plain-snapshotter`（Go）在仓库里完全孤立，与存储章节无关，建议放到附录或者不写。
13. 层数硬上限 255（tag 是 u8），节点用 32 层左右的预算加压缩来规避。
14. `RestackSnapshotTerminalFailure` 在 overlaybd crate 和 ublk-daemon client 中各定义了一份（同名两个类型）。

---

## 7. 对“第 6 部分”章节拆分的建议

原计划约 10 章：LSMT、zfile、读写与层栈、后端+远端调度、ublk 库、ublk-daemon、内存快照、io_uring 工具层、uffd-core，外加两章预备知识。建议调整如下：

1. **预备知识 A：ublk 与 io_uring 入门**（保留）。建议加入 io_uring 的 URING_CMD、fixed file/buffer、sparse 表，以及 ublk 的 FETCH/COMMIT_AND_FETCH 循环。**把原第 8 章“io_uring 工具层”的 AsyncIoRing 部分并入这里或 ublk 库章**：它只有约 1.6k 行，单独成章偏薄，而且读者需要先理解 AsyncIoRing 才能看懂 queue。
2. **预备知识 B：overlaybd/DADI、LSMT 与 OCI 懒加载入门**（保留），增加“上游 C++ 组件与 AgentENV Rust 重写的分工图”，即第 0 节第 2 点。
3. **第 1 章 LSMT 格式与索引**（保留），premerged index 缓存可以放在本章末尾。
4. **第 2 章 ZFile**（保留，篇幅中等）。
5. **第 3 章 读写路径、seal/restack/compact**：内容很多，**建议拆成两章**：3a 读写路径与 RW 三种布局（Log/Sparse/Hybrid）；3b seal（原地封口加增量 digest）、restack 事务、compact_to 和层数预算。
6. **第 4 章 后端与远端 IO**：**建议拆成两章**：4a VirtualFile 装饰器链（local/tar/switch/registry/OSS/P2P 门面）与 RuntimeDispatchFile（这是很好的“多 runtime 陷阱”案例）；4b 节点级块缓存与后台下载（full_file_cache、loader 选举、bk_download、download_gate）。cache 加下载约 6k 行源码，值得独立成章。
7. **第 5 章 ublk 库**（保留，吸收 AsyncIoRing），重点讲为什么自己写 queue、每 queue 一个线程的 LocalSet、on_thread_park 批量提交、UserBuffer 与 AutoReg 的区别，以及为什么 overlaybd 用不了零拷贝。
8. **第 6 章 ublk-daemon**（保留），包括 RPC、warm pool 与占位镜像、两种访问模式、运行时物化与 C++ resize、故障模型。
9. **第 7 章 内存快照 over ublk**（保留，作为本部分高潮）。
10. **新增第 8 章 启动加速：trace prefetch 与 startup pack**：录制器、manifest、pack_planner、startup_pack_task，加上上游兼容的 acceleration layer trace（`prefetch.rs`）。这部分跨越 ublk、daemon、cache 和 sandbox，约 3k 行，是 AgentENV 的独创点，放在第 7 章里会显得臃肿。
11. **第 9 章 uffd-core 与方案对比**：篇幅可以缩小（不到 800 行），定位为“设计演化与对比”：uffd 与 ublk+File 后端在页缓存共享、脏页跟踪、故障面上的比较。可以和第 7 章合并成“7 + 7 附”。
12. **附录（新增建议）：与上游 overlaybd 的兼容性对照表**，列出格式（LSMT/ZFile/tar/config.json 字段）兼容与否、AgentENV 扩展（hybrid、PMIDX、OBCH、AENVMF01、NO_PHYSICAL_OFFSET、zero-copy seal）、未迁移特性，以及 C++ 工具的用途清单（create/apply/commit/resize）。

调整后约 11–12 章（含 2 章预备知识）。如果篇幅受限，优先合并 9 到 7，以及把 io_uring 工具层并入 5。

---

## 8. 与上游 containerd/overlaybd（C++）的兼容性对照（供附录）

| 项 | 状态 | 依据 |
|---|---|---|
| LSMT HeaderTrailer、16B 映射、4K header/trailer、512 对齐 | 兼容（字段逐字节相同） | `lsmt/format.rs`；C++ commit 被 Rust 读取，Rust 层被 `overlaybd-resize` 读取 |
| LSMT sparse RW（flag bit4） | 兼容 | `create_mappings_from_sparse` |
| Hybrid RW（flag bit5） | **AgentENV 扩展**，上游无法打开这种 upper；封口后的产物是标准格式 | `RwLayout::HybridLogStructured` |
| 零段的 moffset | Rust 写 `(1<<55)-1`，读取时把上游任意值归一化 | `ReadOnlyIndex::new` |
| commit 的 uuid 默认值 | nil，与 C++ 一致 | `compact_to` 注释 |
| zero block 检测 | 关闭，与上游当前行为一致 | `COMPACT_ZERO_DETECTION_ENABLED` |
| ZFile header/trailer/jump table/CRC 变体 | 兼容 | `zfile.rs` 注释 |
| ZFile dict | 字段保留，未实现（dict_size 恒为 0） | |
| 读取合并策略 | 与上游不同（只合并完整块，上限 64K），格式无关 | `plan_coalesced_batch` |
| tar 包裹的 remote blob、`overlaybd.commit` 命名 | 兼容 | `backend/tar.rs`、`layer_metadata.rs` |
| image.json / overlaybd.json 字段 | 大部分兼容（camelCase），新增 `upper.mode`、`remoteIoWorkers`、`ossConfig` 等 | `config.rs` |
| registryfs_v2、P2P accelerate address | 行为对齐 | `registryfs_v2.rs`、`p2p/facade.rs` |
| full file cache 磁盘格式 | **不兼容**（自研 meta.bin 加 roaring bitmap） | `backend/cache/meta.rs` |
| trace prefetch（acceleration layer） | 对齐上游的 record/replay（magic 3270449184） | `prefetch.rs` |
| warp/turboOCI/gzip 索引/OCF 缓存 | 未迁移，遇到即报错 | `image_file.rs`、`image_service.rs` |
| tcmu 前端 | 用 ublk 替代 | `storage/ublk` |
| OCI 转换（apply 解包 tar 成 ext4）、resize | 仍用 C++ 工具 v1.0.18-aenv.1；`ensure_tools_converter_v1()` 固定 converter v1，以保证块布局在运行时升级后不变 | `src/setup/overlaybd.rs`、`tools/oci.rs`、`runtime.rs` |

---

## 9. 线程与运行时模型总表（daemon 进程内）

| 执行体 | 类型 | 数量 | 承载的工作 | 来源 |
|---|---|---|---|---|
| 主 runtime | tokio multi-thread | 4 worker | UDS accept 和每连接 handler、pool refill、pack recording 窗口任务、restack | `ublk-daemon/src/main.rs` |
| ctrl ring 线程 | `IoRingWorker<Entry128>` | 1 | 所有 ublk 控制命令（ADD/START/STOP/DEL/SET_PARAMS/GET_FEATURES/UPDATE_SIZE） | `spawn_io_ring_worker(0)` |
| ublk queue 线程 | OS 线程 + current_thread + LocalSet | 每设备 nr_queues 个（=1） | depth 个 slot task；本地 IO 经 queue ring 提交（ctx 路径）；LSMT/ZFile 解压在本线程同步执行 | `ublk/src/dev.rs::queue_work` |
| obd-remote-io | tokio multi-thread | `remoteIoWorkers`（默认 4），每 ImageService 一个 | registry/OSS HTTP、cache 后台 worker（驱逐/checkpoint）、bk_download 调度器 | `io/dispatch_file.rs` |
| tokio blocking pool | spawn_blocking | 按需 | `LocalFile::read_at`（Bytes 版本）、`write_bytes_at`、premerged-index 清理扫描 | `backend/local.rs`、`lsmt/file/helper.rs` |
| ZFile 压缩 worker | OS 线程 | `workers`（≤64） | 发布时的 ZFile 压缩 | `compression/zfile.rs::WorkerPool` |
| metrics HTTP | 主 runtime 中的任务 | 1 | Prometheus | `metrics_server.rs` |

节点主进程这边：`UblkDeviceManager` 运行在 agentenv 的 runtime 上；内存脏页转层时的 `compact_to(ProcessVmReader)` 也在节点进程里执行（因为需要读 FC 进程内存，必须和 FC 处在同一用户、有 ptrace 权限的上下文中【推断】），不经过 daemon。

**同步/异步边界中值得在书里点出来的地方**：
- queue 线程上的读请求，如果命中 `LocalFile` 的 ctx 路径，就是真正的异步 io_uring；但如果经过 `RuntimeDispatchFile`（远端），就变成“把任务投递到 obd-remote-io，然后 await JoinHandle”。所以一个 queue 线程可以同时挂起 depth（16）个远端请求而不阻塞线程。
- 落到 `CachedFile` 命中路径时，是从 mmap 拷贝数据（可能触发主缺页，阻塞 queue 线程）。
- ZFile 解压是 CPU 密集操作，在 queue 线程同步执行，会占住该设备唯一的 queue（nr_queues=1）。这是一个可以讨论的性能权衡。

---

## 10. 关键函数索引（写作时按此查源码）

**LSMT**
- `storage/overlaybd/src/lsmt/format.rs`：`DiskSegmentMapping::from_memory()/to_memory()`、`HeaderTrailer::{new, verify_magic, set_sealed, set_hybrid_rw…}`
- `storage/overlaybd/src/lsmt/index.rs`：`MutableIndex::insert()`、`ReadOnlyIndex::merge()/lookup()`、`ComboIndex::lookup()`、`compress_raw_index()`
- `storage/overlaybd/src/lsmt/file/readonly.rs`：`LSMTReadOnlyFile::open()/commit()`
- `storage/overlaybd/src/lsmt/file/readwrite.rs`：`LSMTFile::open()/create_with_metadata()/write_internal_generic()/plan_hybrid_write()/discard_range()/close_seal()/close_seal_and_reopen()/export_upper_as_sealed()/read_internal_into_generic()/read_mappings_into_generic()`
- `storage/overlaybd/src/lsmt/file/stack.rs`：`open_files_ro()`、`open_files_ro_with_premerged_cache()`、`stack_files()`、`merge_files_ro()`、`verify_layer_order()`
- `storage/overlaybd/src/lsmt/file/helper.rs`：`verify_ht()`、`load_index()`、`create_mappings_from_sparse()`、`compact_to()`、`initialize_file_rw_paths()`、`validate_rw_header_pair_paths()`、premerged 系列

**ZFile**
- `storage/overlaybd/src/compression/zfile.rs`：`load_jump_table()`、`JumpTable::build()/offset_at()`、`ZFileRO::pread_inner()/plan_coalesced_batch()`、`ZFileBuilder::new()/write()/finish()`、`WorkerPool`、`ZFileCompactWriter`、`zfile_compress()/zfile_decompress()/zfile_validation_check()/is_zfile()`

**镜像与后端**
- `storage/overlaybd/src/image/image_file.rs`：`ImageFile::open()/init_image_file()/open_lowers()/open_lower_layer()/open_ro_remote()/open_ro_p2p_uuid()/close_seal()/create_snapshot_and_restack()`
- `storage/overlaybd/src/image/image_service.rs`：`remote_runtime()`、`build_file_cache()`、`open_backend_source_with_size()`、`open_remote_blob_with_size()`、`submit_bk_downloads()`、`prefetch_startup_pack()`、`export_upper_as_oss_sealed()`
- `storage/overlaybd/src/io/dispatch_file.rs`：`build_remote_io_runtime()`、`RuntimeDispatchFile::dispatch()`
- `storage/overlaybd/src/backend/cache/full_file_cache/cache_store.rs`：`CachedFile::read_at_with_flags()`、`do_refill_block_generic()`、`background_refill_range()`、`refill_block_run()`
- `storage/overlaybd/src/backend/cache/bk_download.rs`、`storage/overlaybd/src/download_gate.rs`：`FgReadGuard`、`notify_sandbox_ready()`

**ublk / daemon**
- `storage/ublk/src/ctrl.rs`：`UVMUblkCtrlBuilder::build()`、`UVMUblkCtrl::{add_dev,set_params,start_dev,stop_dev,del_dev,get_features,update_size}`
- `storage/ublk/src/dev.rs`：`UVMUblkDevBuilder::build()`、`UVMUblkDev::start()/del()/wait_for_bg_tasks()`、`queue_work()`、`UVMUblkQueue::slot_task()`、trait `UVMUblkTarget`
- `storage/ublk/src/queue.rs`：`UVMUblkQueue::new()/prep_slot()/submit_and_fetch_for_slot()`、`UblkQueueIoDesc::new()`
- `storage/ublk/src/impls/overlaybd_target.rs`：`OverlaybdTarget::open()/from_opened_image()/swap_state()/handle_io_request()`、`build_ublk_params()`
- `storage/ublk-daemon/src/server.rs`：`run_with_ready_signal()`、`handle_connection()`、`create_overlaybd_device()`、`handle_restack_snapshot()`、`acquire_shared()/acquire_exclusive()/idle_released_device()/prepare_overlaybd_device()`、`clear_page_cache()`、`quiesce_ublk_device()/cleanup_failed_ublk_start()`
- `storage/ublk-daemon/src/runtime.rs`：`materialize_runtime_contents()`、`run_resize_tool()`、`verify_resized_runtime()`
- `storage/ublk-daemon/src/client.rs`：`UblkDaemonClient::new()/spawn_watchdog()/call()`

**节点侧**
- `src/sandbox/ublk/device.rs`：`UblkDeviceManager::get_or_create_shared_readonly()`、`SharedReadOnlyDeviceInner::drop`、`restack_snapshot_device()`
- `src/sandbox/ublk/overlaybd.rs`：`compact_layers()`、`create_commit_args()`、`OverlaybdCompactOutput`
- `src/sandbox/firecracker/overlaybd_snapshot.rs`：`dirty_ranges_to_segment_mappings()`、`convert_dirty_memory_to_overlaybd()`、`publish_memory_overlaybd_layer()`、`capture_live_overlaybd_snapshot()`、`rewrite_lowers_with_runtime_roots()`、`build_mem_snapshot_image_config()`
- `src/sandbox/firecracker/sandbox.rs`：`snapshot_memory_to_overlaybd()`（约 1336 行）、resume 中的内存设备获取与 `load_snapshot_file`（约 2155–2280 行）
- `src/sandbox/firecracker/instance.rs`：`create_state_only_snapshot()`、`get_dirty_memory_ranges()`、`load_snapshot_file()`、`load_snapshot_uffd()`（dead）

---

## 11. 建议的配图清单（汇总）

1. 存储子系统全景图：节点进程、daemon、内核 ublk、FC，以及本地/远端存储。
2. C++ 工具与 Rust 运行时的职责分界（离线转换和 resize 用 C++，在线数据面用 Rust）。
3. LSMT HeaderTrailer 字段表，以及 16B 映射的位域图。
4. Sealed 层、RW 对、Sparse、Hybrid 四种文件布局的纵向对比。
5. 多层合并索引与 tag 方向（tag 0 最新，RW 层的 tag 为 n）。
6. Hybrid 写入时 InPlace/ReuseZero/Append 的拆分示例。
7. restack 七步时序，以及 TerminalFailure 的分界点。
8. ZFile 布局与两级 jump table。
9. VirtualFile 装饰器链（远端读的完整调用栈）。
10. 多 runtime 陷阱：没有 RuntimeDispatchFile 和有它两种情况下，HTTP 连接任务归属对比。
11. Full-file cache：bitmap、mmap 和 loader 选举。
12. 前台读和后台下载之间的 download_gate 准入。
13. ublk FETCH/COMMIT_AND_FETCH 循环，以及 queue 线程内部结构。
14. UserBuffer 与 AutoReg 的数据路径对比，并说明 overlaybd 为什么用不了 AutoReg。
15. daemon 中设备在 pool 里的状态机（含占位镜像 swap）。
16. 内存快照暂停管线（moffset=HVA 的复用）。
17. 恢复时共享内存设备的拓扑，以及两级 refcount 和 cache_fd。
18. Startup pack 的录制、发布、预取三段图。
19. uffd 方案与 ublk+File 后端方案的对比表。
