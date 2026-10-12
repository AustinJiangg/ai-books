# 68 · 已知问题与技术债

> 本篇把前面各篇在读代码时记下的问题汇成一份清单：每条给出现象、代码位置、后果与详讲的篇目，按正确性、可用性、可运维性、安全与信任边界、供应链与构建、文档漂移六类排列。
> 它不是缺陷报告，而是一张「这套系统在哪些假设下工作、假设不成立时会怎样」的索引。
>
> **读者**：要在生产中部署、运维或二次开发 AgentENV 的人；想核对某个结论出处的读者。　**预备**：无，每条都链回详讲篇目。　**代码**：各条已列

---

## 0. 本篇要回答的问题

1. 这份清单从哪里来，收了什么、没收什么？「推论」条目与事实条目怎样区分？
2. 哪些问题会让系统状态或数据出错，哪些只是让请求失败或卡住？
3. 哪几条问题的后果超出单台沙箱——会影响整台节点、整个集群或整个仓库？
4. 系统在哪些地方把「集群内可信」当成前提？前提不成立时暴露的是什么？
5. 构建与发布链上有哪些未固定、未校验的环节？
6. 哪些文档、注释与代码不一致，读文档时应该以哪一侧为准？

---

## 1. 这份清单怎么读

### 1.1 来源与纳入原则

条目来自第 01–67 篇与附录第 71、72 篇正文中指出的问题，以及各篇编写时记下、要求本篇汇总的事项。汇总时做了三件事：

- **去重合并。** 同一处代码在几篇里从不同角度被提到（例如 ublk-daemon 的故障模型在第 04、08、40、41 篇都出现），这里合成一条，链接到讲得最完整的那一篇。
- **保留推论标记。** 原文标为「推论」的条目在这里仍标「推论：」。这类条目的现象由代码结构推出，没有在运行环境中复现，读者应当把它们当作待验证的假设。
- **删掉被更正推翻的条目。** 编写过程中有几条早期结论被后续核实推翻，它们不再出现；删去的条目与理由列在 §8。

纳入的标准是「代码里能指出位置」。部署建议、性能观感与「可以做得更好」一类的意见不收。语气上，本篇只描述取舍与后果，不评判设计；许多条目是有意的取舍（例如单 API key、集中式 ublk-daemon），它们出现在这里是因为后果需要被运维者知道，而不是因为它们是错误。

### 1.2 六个类别

| 类别 | 判断标准 | 编号前缀 |
|---|---|---|
| 正确性 | 某种交错、崩溃或输入下，持久状态、数据或返回结果可能是错的 | C |
| 可用性 | 状态不会错，但请求会失败、卡住或得到与契约不符的响应 | A |
| 可运维性 | 资源泄漏或不回收、配置与默认值分叉、观测缺口、遗留代码与测试缺口 | O |
| 安全与信任边界 | 某个组件被默认为可信，或某个凭据、隔离手段的覆盖面小于名字暗示的范围 | S |
| 供应链与构建 | 构建、生成、发布、安装链上未固定或未校验的环节 | B |
| 文档漂移 | `docs/src/**`、README、`CLAUDE.md`、配置注释、代码注释与代码行为不一致 | D |

一个问题可能同时属于两类（例如 P2P 不校验 sha256 既是安全问题也是正确性问题），这时按「后果最先由谁承担」归类，只出现一次。

### 1.3 表格的列

每条一行：**编号 | 现象 | 位置 | 后果 | 详讲**。位置写仓库相对路径与函数名，同一格内后出现的短文件名与前面的路径同目录。详讲链到对应篇的小节。文档漂移表把「后果」一列换成「实际行为」。
「位置」是定位用的入口，不保证列全所有调用点。重要条目在表外另有一小段，讲清楚后果的传播路径。

### 1.4 汇总

| 类别 | 条目数 | 表外重点条目 |
|---|---|---|
| 正确性 | 39 | 对象存储仓库的弱一致 catalog；持久记录的两阶段标记 |
| 可用性 | 41 | Firecracker REST 调用无超时；ublk-daemon 无崩溃恢复；`Schedule()` 不排除 UNHEALTHY |
| 可运维性 | 72 | managed layers 无 GC |
| 安全与信任边界 | 18 | P2P 信任边界；控制面 gRPC 无认证 |
| 供应链与构建 | 20 | 生成代码无漂移检查 |
| 文档漂移 | 30 | `docs/src/internals/*` 的几处主要偏差；startup pack 的版本称呼 |
| 合计 | 220 | 其中 45 条标为推论 |

---

## 2. 正确性

这一类条目的共同点是：某种交错、崩溃或少见的输入之后，**持久状态与实际不符**，而系统不会自己发现。
它们集中在三处——沙箱生命周期里「先改记录、再做副作用、失败再回滚」的两阶段序列，快照仓库在对象存储上的 catalog，以及崩溃时的落盘顺序。
前两处有一个共同的根：AgentENV 的状态机与仓库都假设「并发写同一对象的情况很少」，因此在没有原子原语的地方用「读-改-写」加回读来近似。

### 2.1 对象存储仓库的弱一致 catalog

POSIX 仓库用按名字的文件锁把「写 alias」到「写 record」整段包起来；对象存储没有改名与锁，`src/snapshot/repository/backends/oss/repository.rs` 里的 catalog 操作于是分成两种写法。
卷记录与 BuildKit 缓存 head 用 ETag 条件写（`put_bytes_conditionally()`），是真 CAS；而快照的 alias、模板构建状态与 startup 描述符用的是无条件读改写。
后果有三：`bind_alias()` 以「对方 record 是否存在」判断 alias 是否陈旧，而 alias 先于 record 写入，推论：两个发布者可能都成功、alias 只指向后者，读者的一次 `get()` 也可能删掉正在提交的 alias；
`try_start_build()` 不排他，两台节点可能同时构建同一个模板，后写者覆盖前者；`attach_memory_startup_descriptor()` 与删除交错时会让已删除的记录复活，而它的制品目录可能已被删掉。
模板记录因为 Waiting 记录先于 alias 写入而不受第一种交错影响，受影响的是带名字的沙箱快照。
第 48 篇指出同一文件里已有条件写的实现，record 与 alias 迁移到 `if_none_match` / `if_match` 可以补上这三个缺口；条件写注释里关于服务端是否支持条件写头的说法彼此矛盾，迁移前需要先在目标服务上核实（§7 D-21）。

### 2.2 持久记录的两阶段标记

resume 先把盘上记录标成 Resuming（`mark_resuming()`），成功后删除、失败后回滚（`rollback_resuming()`，`src/orchestrator/persistence/mod.rs`）。
这个设计保证了「重启时看到 Resuming 的记录就知道它可能已被消费」，但回滚本身失败时只记 warn：内存里沙箱回到 Paused，盘上仍是 Resuming，下一次重启会把这台完好的暂停沙箱当作已消费而丢弃。
`src/orchestrator/service.rs` 的 `resume_sandbox_inner()` 还有一条更直接的路径：`mark_resuming()` 之后若发现缺少 `paused_state`，函数直接返回错误而不回滚，记录同样卡在 Resuming。
两条路径的后果相同——暂停沙箱在下次重启时丢失——而在重启之前没有任何信号。

### 2.3 生命周期与状态机

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| C-01 | `mark_resuming()` 后缺 `paused_state` 直接返回，不回滚 | `src/orchestrator/service.rs` 的 `resume_sandbox_inner()` | 记录卡在 Resuming，下次重启丢弃该暂停沙箱 | [第 20 篇 §7.2](20-launch-plan-and-rollback.md#72-失败点与动作) |
| C-02 | `rollback_resuming()` 失败只记 warn | `src/orchestrator/persistence/mod.rs` | 同上，见 §2.2 | [第 22 篇 §5](22-persistence-across-restarts.md#5-两阶段-resume-标记) |
| C-03 | 网络策略与扩展参数的更新不持逻辑锁 | `src/sandbox/network/slot.rs` 的 `set_egress_policy()`；扩展参数 patch | 与 pause 并发时 VM 与元数据短暂不一致 | [第 19 篇 §7](19-state-machine-and-concurrency.md#7-同一沙箱上的并发操作) |
| C-04 | 推论：iptables 脚本含 filter 与 nat 两个 `COMMIT`，只在单表内原子 | `set_egress_policy()` | filter 成功、nat 失败时 `user_egress_rules_present` 与内核状态不一致 | [第 30 篇 §5.2](30-egress-policy-and-proxy.md#52-代理的两阶段状态) |
| C-05 | pause / snapshot / fork 的 Terminal 失败后直接发布卷，与删除路径的 `fail_backings()` 口径不一致 | `service.rs` 的 `finalize_terminal_volumes()`；`src/volume.rs` | 推论：失败恰在 restack 之后、写配置之前时，可能把指向旧层的 backing 标成 Ready | [第 21 篇 §7](21-deletion-and-volume-capture.md#7-卷的内容还在哪些时刻被发布) |
| C-06 | Terminal 捕获失败时沙箱已被移除，函数仍返回错误 | `service.rs` 的 `delete_sandbox_impl()` | 调用方看到失败而沙箱已不存在 | [第 21 篇 §5](21-deletion-and-volume-capture.md#5-捕获失败的两条去路) |
| C-07 | 句柄身份不一致时启动报成功，却没有发布路由 | `src/orchestrator/service.rs` 的启动流水线 | 沙箱 Running 但代理不可达 | [第 20 篇 §4.2](20-launch-plan-and-rollback.md#42-句柄身份只回滚自己的东西) |
| C-08 | 错误分类缺省 `Recoverable`；pause 失败不删已分配的产物目录 | `src/orchestrator/` 错误约定 | 未分类的失败按可恢复处理；产物目录累积 | [第 20 篇 §7.1](20-launch-plan-and-rollback.md#71-两类错误的约定) |
| C-09 | 推论：fork 先封存卷、后捕获内存，期间源沙箱仍在运行 | `src/orchestrator/service.rs` 的 fork 路径 | 子沙箱的卷与内存可能来自不同时刻 | [第 51 篇 §4](51-fork.md#4-卷克隆独占卷共享只读卷) |
| C-10 | 显式传 `{}` 会覆盖从快照继承的扩展参数 | 扩展参数合并逻辑 | 与「absent 等价于 `{}`」的契约不符 | [第 33 篇 §5.2](33-custom-extension-hooks.md#52-随快照持久化与继承) |
| C-11 | `SnapshotRecord::mark_committed()` 不检查原状态 | `src/snapshot/types/snapshot.rs` | Error 状态的模板记录可直接变成 Ready；POSIX 仓库的 `committed_record_unlocked()` 在记录不存在且来源是模板时直接造一条 Ready 记录，推论：可复活已删除的模板 | [第 46 篇 §2.2](46-snapshot-object-model.md#22-来源与模板状态)、[第 47 篇 §3.4](47-posix-repository.md#34-提交) |
| C-12 | 推论：基于模板的构建未覆盖 startup 时，继承的 `start_cmd` 会被再启动一次 | `src/template/builder.rs` | 构建 VM 里出现重复的启动进程 | [第 52 篇 §4.3](52-template-builder.md#43-启动命令与就绪命令) |
| C-13 | 推论：Waiting 记录里的资源与基础模板的 cpu / mem 必须一致 | `src/template/runner.rs` | 基础模板规格非默认时构建失败 | [第 52 篇 §2.2](52-template-builder.md#22-模板-base从快照恢复) |

### 2.4 落盘与崩溃一致性

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| C-14 | 暂停记录 fsync，内存层与 vm_state 未见 fsync | `src/orchestrator/persistence/` 与 pause 写路径 | 推论：掉电后记录完整而产物不完整 | [第 22 篇 §3.2](22-persistence-across-restarts.md#32-rocksdb-与持久性) |
| C-15 | POSIX 仓库 manifest 用 `fs::write`（非原子、无 fsync）；commit 标记不 fsync；`write_json` 不 fsync 父目录 | `src/snapshot/repository/backends/posixfs/` | 崩溃后可能留下半写的 manifest 或丢失的提交 | [第 47 篇 §7](47-posix-repository.md#7-崩溃一致性的边界) |
| C-16 | 推论：POSIX 提交不取 record 锁 | `posixfs/catalog.rs` | 与 `mark_error()` 或 delete 并发时可能复活被删的模板 | [第 47 篇 §5](47-posix-repository.md#5-锁按名字加不设全局锁) |
| C-17 | 推论：NFS 以 `local_lock` 挂载时 flock 不跨节点 | `posixfs/` 的锁 | 多节点共享 POSIX 仓库时锁失效 | [第 47 篇 §5](47-posix-repository.md#5-锁按名字加不设全局锁) |
| C-18 | 拷贝导入不做哈希校验；硬链接导入后 chmod 只读会连带改节点本地文件 | `posixfs/` 导入路径 | 静默损坏不可发现；节点侧文件权限被改 | [第 47 篇 §3.1](47-posix-repository.md#31-导入固定制品) |
| C-19 | 推论：record PUT 结果不确定时，回滚可能删掉已提交快照的制品 | `oss/repository.rs` 的 publish 回滚 | 已提交的快照无法恢复 | [第 48 篇 §3.1](48-object-storage-repository.md#31-回滚) |
| C-20 | `bind_alias()` 读-写-回读；推论：两发布者都成功、读者删掉正在提交的 alias | `oss/repository.rs` 的 `bind_alias()`、`resolve_alias()` | 见 §2.1 | [第 48 篇 §6.1](48-object-storage-repository.md#61-alias读-写-回读) |
| C-21 | `try_start_build()`、`mark_build_error()` 是无条件读改写 | `oss/repository.rs` | 推论：同一模板被两台节点重复构建，后写者覆盖 | [第 48 篇 §6.2](48-object-storage-repository.md#62-模板状态普通的读改写) |
| C-22 | `attach_memory_startup_descriptor()` 与删除交错 | `oss/repository.rs` | 已删除记录复活，指向可能已删的制品 | [第 48 篇 §6.3](48-object-storage-repository.md#63-startup-描述符) |
| C-23 | builder 模板「由 alias 提交保证唯一」在对象存储后端不严格成立 | `src/api/impls/image_build.rs` 与 `bind_alias()` | 推论：并发首建可能各自成功 | [第 53 篇 §3.3](53-buildkit-in-microvm.md#33-首建与并发首建) |
| C-24 | 继承自对象存储快照的 rootfs 层再次发布时记为带桶地址的 External 引用 | `oss/repository.rs` 的层记法 | 换桶或改 prefix 后无法解析 | [第 48 篇 §4.3](48-object-storage-repository.md#43-继承层的两种记法) |
| C-25 | 外部层缺 digest 时以 `external:{index}` 作键 | `src/snapshot/types/snapshot.rs` 的层引用 | 不同快照的外部层可能同键 | [第 46 篇 §2.4](46-snapshot-object-model.md#24-两种层引用) |

### 2.5 存储引擎与内存

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| C-26 | Sparse 布局 discard 的零映射只在内存 | `storage/overlaybd/src/` 的 RW 布局 | 推论：重开后可能读出 lower 的旧内容 | [第 36 篇 §5](36-read-write-paths-and-rw-layouts.md#5-discard) |
| C-27 | 重放上游 RW 索引时保留 zeroed 映射的 moffset 并当作 backed zero | Rust 版 overlaybd 的索引重放 | 推论：之后的 `ReuseZero` 可能覆盖上游后来追加的数据 | [第 34 篇 §6](34-lsmt-format-and-index.md#6-与上游的兼容边界) |
| C-28 | live 层栈不压缩，层数预算无配置项 | `src/sandbox/ublk/device.rs` 与 `image_file.rs` 的 restack | 推论：约第 256 次 restack 失败且为 Terminal | [第 37 篇 §5.3](37-seal-restack-compact.md#53-预算管不到的地方) |
| C-29 | 发布 ZFile 时 `verify=0`，数据块无 CRC | ZFile 发布路径 | 远端字节损坏不可检出 | [第 35 篇 §3](35-zfile-compression.md#3-校验一种rawcrc32c) |
| C-30 | `track_dirty_pages=false`（PVM 下强制）时退回 `mincore` | AENV 补丁版 Firecracker 的 `dirty-memory-ranges` | 写出量不再正比于改动量；开 swap 时可能漏报页 | [第 03 篇 §3.2](03-firecracker-for-agentenv.md#32-file-后端) |
| C-31 | schema 版本不符时 image-cache 的 RocksDB 整库清空 | `src/image/` 的 image-cache 元数据 | hold 丢失，GC 可能删掉仍在用的转换结果 | [第 45 篇 §5.2](45-oci-to-overlaybd.md#52-元数据图) |
| C-32 | 推论：模式不符的持久记录不被 pin | 启动时 `load_all()` 与镜像 GC | 镜像 GC 可能删掉它们依赖的层 | [第 22 篇 §6.3](22-persistence-across-restarts.md#63-镜像-gc-的-fail-closed) |
| C-33 | 推论：P2P 复用转换层依赖 `overlaybd-apply` 输出逐字节确定 | `src/image/oci_image.rs` 的 `uuid_from_layer_digest()` | 工具输出不确定时复用的层与本地转换不同 | [第 45 篇 §4.2](45-oci-to-overlaybd.md#42-三级查找) |
| C-34 | 推论：同 tag 并发导出互相覆盖；删除快照后 registry GC 可能回收仍被沙箱使用的 blob | `src/snapshot/repository/backends/common/acr/` | 镜像内容与快照不符或缺失 | [第 50 篇 §4.3](50-rootfs-as-oci-image.md#43-回退与失败) |
| C-35 | tag 先于 record 可见，回滚失败时 tag 残留 | `acr/publisher.rs` | registry 中出现没有对应快照的 tag | [第 50 篇 §4.3](50-rootfs-as-oci-image.md#43-回退与失败) |
| C-36 | 推论：对象存储下从快照创建的沙箱在暂停时重读内存层 `image.json` | `LocalArtifactCache` | 若已被 LRU 驱逐，pause 失败 | [第 49 篇 §6.2](49-resolve-and-artifact-cache.md#62-lease-只覆盖启动窗口) |
| C-37 | 跨重启复用制品只看文件是否存在 | `LocalArtifactCache` | 仓库路径变化后复用陈旧文件 | [第 49 篇 §6.3](49-resolve-and-artifact-cache.md#63-重启取消与多实例) |
| C-38 | CPU 交集：`intersectionSent` 先于 `ReconcileNode` 置位；崩溃重启的节点再也拿不到交集；交集随节点加入收窄 | `services/scheduler/internal/node_registry.go` | 早先的快照不在新交集覆盖内，跨节点恢复可能因 CPU 特性不符失败 | [第 57 篇 §5.5](57-heartbeat-and-cpu-intersection.md#55-边界与失效模式) |
| C-39 | 推论：fork 先 `snapshot_volume_mounts()` 暂停封存卷、恢复，再暂停捕获内存；两次之间源沙箱照常运行 | `src/api/impls/sandbox.rs` 的 fork 处理 | 子沙箱的卷与内存可能来自不同时刻 | [第 31 篇 §5](31-extra-drives-and-volumes.md#5-暂停与快照时卷去了哪里) |

---

## 3. 可用性

这一类条目不会让状态出错，但会让请求失败、挂起，或得到与 spec 不符的响应。最重要的三条都与「某个依赖坏了之后，系统多久、以什么方式发现」有关：
Firecracker 卡住时没有人发现，ublk-daemon 死掉时发现了但无法恢复，节点宕机时 scheduler 的推导发现了而选择节点的代码不看。

### 3.1 Firecracker REST 调用无超时

`src/sandbox/firecracker/socket.rs` 的 `UnixSocketClient::request()` 直接 await hyper 的请求，外层没有 `tokio::time::timeout`，连接器也没有设超时；
`socket_timeout_secs`（缺省 3 s）只覆盖「socket 文件出现」这一步。Firecracker 进程一旦在某个调用里卡住，持有该沙箱 `Mutex` 的启动、恢复或暂停任务就一直挂着。
其它等待者靠 `wait_for_transition()` 的 60 s 兜底放弃，持锁任务本身跑在 `run_cancellation_safe()` 的独立任务里，也不会因请求方断开而结束，于是沙箱停在过渡态，直到有人从外部杀掉那个 Firecracker 进程——socket 断开后挂起的请求才以错误返回，回滚路径随之运行。
对比之下，同一个 `server` 对 ublk-daemon 的 RPC 按请求类型分级设了超时。困难在于 `PUT /snapshot/create` 与 `PUT /snapshot/load` 的耗时与内存大小相关，统一的短超时会误杀大 VM，所以需要的是按端点分级的上限而不是一个常数。

### 3.2 ublk-daemon 没有崩溃恢复

`storage/ublk-daemon/src/client.rs` 的 `spawn_watchdog()` 在子进程退出时把 `daemon_dead` 置位，此后每次 `call()` 直接失败，不重启、不重连。
内核侧 AgentENV 不设置 `UBLK_F_USER_RECOVERY`，daemon 退出后设备不会进入等待接管的状态；推论（依据 ublk 驱动语义）：在途与后续块请求以错误结束，运行中沙箱的 rootfs、附加盘与卷 I/O 出错，内存设备上尚未进入页缓存的页被访问时 Firecracker 的缺页无法完成。
节点侧 `src/sandbox/ublk/device.rs` 的 `UblkDeviceManager::is_available()` 只看客户端对象是否存在，daemon 死后仍返回真，`start_resume()` 开头的快速失败检查照样通过，失败推迟到第一个设备 RPC。
所以一次 daemon 崩溃的影响面是整台节点上全部运行中的沙箱，恢复手段只有重启 `server`，而 `server` 重启时只能找回已经暂停落盘的沙箱。
这是「一个集中的特权进程拥有全部设备」这一取舍的另一面；要缩小故障面又不放弃集中管理，前提是 daemon 能从持久状态重建设备表与镜像栈，而这些状态现在只在内存里。

### 3.3 `Schedule()` 不排除 UNHEALTHY 节点

scheduler 的 `services/scheduler/internal/node_registry.go` 有一套状态推导（`deriveObservedNodeViewLocked()`：距上次心跳超过 `report_ttl`，缺省 30 s，即 UNHEALTHY），
但 `service.go` 的 `Schedule()` 调用的 `AtomicNodeRegistry.Snapshot(false)` 只按 `lingeringIDs` 过滤，函数注释「filtered by their derived status」与实现不符。
测试 `TestScheduleOnlyConsidersReadyNodes` 只构造了一个 active 与一个 lingering 节点，从未构造心跳超时的节点，名字暗示的性质没有被验证。
后果在静态发现模式下最明显：宕机的节点仍在发现列表里，`FilterByResourceLimit()` 还用它最后一次的容量快照判断，round-robin 照常选中它，gateway 不重试，这部分创建请求得到 502。
推论：N 个节点坏一个，约 1/N 的创建请求失败，直到运维把它从配置里删除。Kubernetes 模式下 readiness 失败的 Pod 会从 EndpointSlice 的 serving 集合消失，问题被部分缓解。

### 3.4 阻塞与挂起

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| A-01 | Firecracker REST 调用无超时 | `src/sandbox/firecracker/socket.rs` 的 `UnixSocketClient::request()` | 见 §3.1 | [第 25 篇 §6.2](25-backend-and-firecracker-process.md#62-没有请求超时) |
| A-02 | ublk-daemon 死后不重启、不重连；`is_available()` 仍为真 | `storage/ublk-daemon/src/client.rs` 的 `spawn_watchdog()`；`src/sandbox/ublk/device.rs` | 见 §3.2 | [第 41 篇 §6.1](41-ublk-daemon.md#61-daemon-先死) |
| A-03 | `wait_for_ublk_dev()` 在 async handler 里 `std::thread::sleep` 轮询，最长约 30 s | `storage/ublk/src/lib.rs` | 推论：udev 迟迟不生效时几个并发建设备请求即可占满 daemon 的 4 个 worker | [第 41 篇 §7](41-ublk-daemon.md#7-技术债与文档漂移) |
| A-04 | `enable_acceleration()` 在 async 路径上同步 `connect_timeout` | `storage/overlaybd/src/image/image_service.rs` | 推论：P2P 门面不可达时每次打开镜像最多多等 1 s | [第 38 篇 §3.4](38-virtualfile-chain-and-remote-io.md#34-registryfs_v2) |
| A-05 | `process_vm_readv` 同步跑在 tokio worker 上 | `src/sandbox/firecracker/process_vm_reader.rs` 的 `ProcessVmReader` | 大内存暂停时占住 worker | [第 42 篇 §6](42-memory-snapshot-over-ublk.md#6-代价边界与技术债) |
| A-06 | 首次主机采样在 tokio worker 上 `thread::sleep` 100 ms | `src/observability/` 主机指标 | 启动后第一次心跳与 `GET /nodes` 阻塞 worker | [第 57 篇 §2.2](57-heartbeat-and-cpu-intersection.md#22-主机指标) |
| A-07 | 推论：`auto_evict_interval_ms = 0` 会 panic | `src/orchestrator/service.rs` 的驱逐循环 | 配置错误直接让驱逐任务崩溃 | [第 23 篇 §4.1](23-auto-eviction-and-ttl.md#41-节拍与退出) |
| A-08 | 解压器报错不重试 | `storage/overlaybd/src/` 的 ZFile 读路径 | 一次瞬时远端错误直接变成 guest I/O 错误 | [第 35 篇 §5.1](35-zfile-compression.md#51-打开) |
| A-09 | in-flight 取数时调用方 future 被 drop，条目永不清理 | `LocalArtifactCache` | 该 key 在进程生命期内一直失败 | [第 49 篇 §6.3](49-resolve-and-artifact-cache.md#63-重启取消与多实例) |
| A-10 | 一个坏 record 让 `list()` 整体失败 | `posixfs/catalog.rs` | 模板与快照列表接口不可用 | [第 47 篇 §4](47-posix-repository.md#4-可见性只看-record) |
| A-11 | OSS 10,000 分片上限无前置检查；403 重试从头重传整个文件；无 Expiration 的凭证永不主动刷新 | `src/snapshot/repository/backends/oss/client.rs` | 超大层上传中途失败；长期运行后凭证过期 | [第 48 篇 §4.4](48-object-storage-repository.md#44-分片上传与凭证) |

### 3.5 集群路径

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| A-12 | `Schedule()` 只按 lingering 过滤，不看推导出的 UNHEALTHY | `services/scheduler/internal/node_registry.go` 的 `Snapshot()` | 见 §3.3 | [第 56 篇 §2.4](56-scheduler.md#24-不排除-unhealthy-节点) |
| A-13 | `withinLimit` 用 `>`，计数等于上限的节点仍可选中；starting 不计入 `MaxSandboxCount` | `services/scheduler/internal/filter.go` | 上限可被超出一台及启动中的数量 | [第 56 篇 §2.2](56-scheduler.md#22-资源上限) |
| A-14 | 策略名拼错静默退回 round_robin | `services/scheduler/internal/strategy.go` 的 `NewStrategy()` | 配置错误不可见 | [第 56 篇 §2.3](56-scheduler.md#23-策略) |
| A-15 | 不在集群内运行时 Kubernetes 发现永久停止，health 仍报 SERVING | scheduler 的 kubernetes 发现 | 节点列表冻结而探针正常 | [第 56 篇 §4.2](56-scheduler.md#42-kubernetes) |
| A-16 | query-only 副本只能撑到绑定过期（缺省 30 s） | Redis 绑定只由 primary 续期 | primary 长时间不可用时数据面路由同样失效 | [第 56 篇 §6.2](56-scheduler.md#62-primary-不可用时) |
| A-17 | 静态发现下注销不能让 gateway 停止送新请求；推论：关闭中的节点仍被调度 | scheduler 的 static 发现 | 滚动重启期间请求打到正在关闭的节点 | [第 56 篇 §4.1](56-scheduler.md#41-static) |
| A-18 | 关闭时先 `UnregisterNode` 再暂停落盘 | `src/observability/reporter.rs` 的 `unregister_node()` 与关闭序列 | 重启完成前该节点上的沙箱对 gateway 返回 404 | [第 22 篇 §7](22-persistence-across-restarts.md#7-崩溃一致性边界) |
| A-19 | gateway 遇节点不可达或 5xx 不重试 | `services/gateway/internal/server.go` | 单节点瞬时故障直接暴露给客户端 | [第 55 篇 §5.3](55-gateway.md#53-错误与重试) |
| A-20 | 推论：gateway 超时比节点更严 | gateway `request_timeout`（代码缺省 30 s） | 大文件下载与自动恢复可能被截断 | [第 55 篇 §5.2](55-gateway.md#52-超时) |
| A-21 | 一个节点缺 `cpu-template-helper` 会阻塞整个集群的 CPU 交集；scheduler 重启后交集不再重算 | `node_registry.go` | 新快照无法获得可移植的 CPU 模板 | [第 57 篇 §5.5](57-heartbeat-and-cpu-intersection.md#55-边界与失效模式) |
| A-22 | scheduler 与 gateway 不知道虚拟化模式；DaemonSet 写死 `kvm` | `services/`；`deploy/k8s/base/agentenv-daemonset.yaml` | 推论：混合集群里请求被放到另一种模式的节点，得到 500 | [第 61 篇 §7](61-pvm.md#7-多节点模式不在调度器的视野里) |

### 3.6 API 契约

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| A-23 | TTL 缺省值有三套：`default_sandbox_timeout_secs` 15 s、v2 create / connect 300 s、auto-resume 至少 300 s | `src/api/impls/sandbox.rs` | resume 传 `{}` 可把 TTL 缩到 15 s | [第 14 篇 §4](14-sandbox-api.md#4-四个改-ttl-的入口) |
| A-24 | 对暂停沙箱调 `/timeout`、`/refreshes` 返回 HTTP 500 而 body code 为 400；同一错误按端点映射成 409 / 400 / 500；ShuttingDown（503）多被塞进 500 变体 | `src/api/impls/sandbox.rs` | 客户端无法按状态码区分可重试与不可重试 | [第 14 篇 §6](14-sandbox-api.md#6-pauseresumedelete-与错误码) |
| A-25 | 状态折叠把 Killing 算 running、Snapshotting / Forking 算 paused，而 state 过滤按内部状态精确匹配 | `From<SandboxState>` 与列表过滤 | 过渡态沙箱从过滤列表中消失；GET 删除中的沙箱报 running 而 connect 返回 404 | [第 18 篇 §5](18-e2b-compatibility.md#5-偏差矩阵) |
| A-26 | spec 写 `limit` 缺省 100，代码省略时返回全部 | 列表 handler | 大部署下单次响应无界 | [第 14 篇 §8.3](14-sandbox-api.md#83-游标分页) |
| A-27 | Pausing 时 connect 返回 400 | `src/api/impls/sandbox.rs` | 无法表达「稍后重试」 | [第 23 篇 §6](23-auto-eviction-and-ttl.md#6-与其它操作的交互) |
| A-28 | 代理流量不续期 TTL | `src/api/proxy.rs` | 只靠数据面活动的沙箱会被驱逐 | [第 23 篇 §7](23-auto-eviction-and-ttl.md#7-与代理自动恢复的联动) |
| A-29 | 恢复中并发到达的代理请求得 410 而不等待；格式错的 WebSocket 升级先触发自动恢复再 400 | `src/api/proxy.rs` 的 `resolve_proxy_request()` | 冷沙箱的第一批并发请求部分失败；无效请求也唤醒沙箱 | [第 17 篇 §4](17-reverse-proxy.md#4-自动恢复) |
| A-30 | 转发阶段 502 / 504 空 body；响应头到达后无超时；`x-forwarded-proto` 写死 `http`；首 label 带连字符的主机名一律判为数据面 | `src/api/proxy.rs` | 排障缺信息；guest 内应用看到错误的协议 | [第 17 篇 §7](17-reverse-proxy.md#7-错误映射) |
| A-31 | `VirtualizationModeMismatch` 无 API 映射 | `src/orchestrator/mod.rs` | 返回 500 而不是可理解的 4xx | [第 61 篇 §5.3](61-pvm.md#53-不符时的后果) |
| A-32 | 模板 API：spec 允许 `name` 带 `:tag` 而代码返回 400；templateID 与 buildID 不符在两条路径分别返回 400 / 404，重复 start 分别 400 / 409；`force` 被忽略；`public` 恒为 true、alias 查询恒为 false | `src/api/impls/image_build.rs` | E2B 客户端行为与预期不符 | [第 15 篇 §3.2](15-template-build-api.md#32-支持的步骤) |
| A-33 | 步骤路径不支持 COPY / ADD，ARG 当作 ENV；推论：USER 不影响后续 RUN 的身份；RUN 依赖 `/bin/bash` | `src/template/runner.rs` | Dockerfile 语义与 e2b infra 不同 | [第 52 篇 §4.1](52-template-builder.md#41-逐步执行) |
| A-34 | 启动命令推导在步骤路径禁用、BuildKit 路径仍从 ENTRYPOINT / CMD 推导 | `src/template/builder.rs`；BuildKit 前端 | 同一镜像经两条前端得到不同的 `start_cmd` | [第 53 篇 §4.6](53-buildkit-in-microvm.md#46-启动命令的推导) |
| A-35 | 步骤路径构建崩溃后记录永远 Building；`max_concurrent_builds` 与删除时 409 只覆盖 BuildKit 会话 | `src/template/runner.rs` | 卡住的模板需人工清理；步骤路径不受并发限制 | [第 15 篇 §3.3](15-template-build-api.md#33-这条路径没有会话) |
| A-36 | `pending-` 孤儿卷预留无回收，卷永久 409 且 API 不暴露持有者 | `src/volume.rs` 的预留 | 崩溃后该卷不可再挂载 | [第 16 篇 §7.2](16-snapshot-and-volume-api.md#72-owner-的三次变化) |
| A-37 | `fromVolume` 与 `image` 同给时 `image` 静默忽略；`fromVolume` 要求大小相等而 `sizeMB` 缺省 64 GiB；删卷竞态映射 500；快照别名冲突返回 400；spec 没有快照删除端点 | `src/api/impls/` 的卷与快照 handler | 调用方难以正确使用 | [第 16 篇 §6.1](16-snapshot-and-volume-api.md#61-volumes_post) |
| A-38 | 卷槽位数在首次冷启动时固化；init 挂载失败只 WARN，而热插失败则创建失败 | `src/sandbox/extra_drive.rs` 与卷接线 | 调大 `max_volume_count` 后 API 放行的卷数可超过旧模板的槽位 | [第 31 篇 §7](31-extra-drives-and-volumes.md#7-代价与边界) |
| A-39 | `autoPause` 缺省与 e2b 相反；`maskRequestHost` 接受而不读；`GET /health` 返回 204 | `src/api/impls/` | 依赖 e2b 缺省的客户端行为改变 | [第 18 篇 §5](18-e2b-compatibility.md#5-偏差矩阵) |
| A-40 | aenv 客户端允许 32 条并发隧道而服务端上限 8；单条隧道失败中止整个 build | `crates/aenv/` 与 `GET …/builder` | 并发高的构建以 429 失败 | [第 62 篇 §5](62-aenv-cli.md#5-aenv-build本地-buildctl-与远端-buildkitd) |
| A-41 | aenv：`from_env` 不读环境变量；暂停、删除、丢失都以 130 退出；keepalive 常量与代理 30 s 空闲超时是隐式契约 | `crates/aenv/src/client/mod.rs` | 脚本无法区分退出原因；改一侧超时会断开交互终端 | [第 62 篇 §4.3](62-aenv-cli.md#43-几个机制) |

---

## 4. 可运维性

这一类条目在短期内不影响请求，却决定了一台节点或一个仓库能稳定运行多久、出了问题能否被看见。
最集中的模式是**只增不减**：仓库的层、节点的目录、P2P 的发布、daemon 里的设备，都有「谁来删」没有答案的路径。
其次是配置的分叉：同一个键在代码默认、`config/default.toml`、文档与部署清单里有不同的值。

### 4.1 managed layers 没有 GC

两种仓库后端都**从不删除 `managed-layers/` 下的层**。POSIX 后端删除快照只删 record、alias、commit 标记与构建日志；
对象存储后端（`src/snapshot/repository/backends/oss/repository.rs` 的 `delete()`）删 record、alias、构建日志、磁盘镜像发布与 `artifacts/{id}/` 前缀，发布失败的回滚也明确跳过层，两处注释写着层「跨快照共享、需要单独 GC」，全仓库没有对应实现。
不回收的理由是结构性的：层没有引用计数，发布时「先 `exists()` 后直接引用」是一次不加锁的引用获取，任何回收器都可能删掉一个正在被新快照引用的层。
这一点也是「源卷删除后克隆卷仍可用」的前提（[第 16 篇](16-snapshot-and-volume-api.md)）。
代价是仓库单调增长：删除快照、模板与卷都不释放层空间，发布失败与删除中途失败留下的层也加入其中；对象存储按容量计费，这个增长直接是成本。
同样的结构出现在 BuildKit builder 模板、缓存种子与工作卷的 managed 层上。运维侧目前只能离线扫描全部 record 计算可达集后手工清理，且必须在没有发布进行时做。

### 4.2 不回收的资源与泄漏

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| O-01 | 两种仓库都不删除 `managed-layers/` | `posixfs/catalog.rs`、`oss/repository.rs` 的 `delete()` | 见 §4.1 | [第 47 篇 §6](47-posix-repository.md#6-删除)、[第 48 篇 §7](48-object-storage-repository.md#7-不回收的层) |
| O-02 | builder 模板无 GC；缓存种子与工作卷的 managed 层不回收 | BuildKit 前端 | 构建越多仓库越大 | [第 53 篇 §5.5](53-buildkit-in-microvm.md#55-退役与回收) |
| O-03 | POSIX 仓库的锁文件从不删除；没有启动扫描 | `posixfs/` | 锁目录随名字数增长；崩溃留下的陈旧 alias 无人处理 | [第 47 篇 §5](47-posix-repository.md#5-锁按名字加不设全局锁) |
| O-04 | 删除快照不 unpublish 其 P2P 制品 | `src/p2p/` 与仓库 `delete()` | P2P 存储只增不减，直到本地 GC | [第 58 篇 §3.4](58-p2p-artifact-transport.md#34-fetch校验与-gc) |
| O-05 | fork 捕获目录只在整棵树消失时回收 | `src/sandbox/firecracker/sandbox.rs` | 长寿源沙箱下目录累积 | [第 51 篇 §3](51-fork.md#3-共享什么独占什么) |
| O-06 | 反复暂停与恢复的沙箱，每一代 vm_state 与新层都是真实占用 | `$AENV_HOME/persisted-sandboxes` | 节点磁盘随暂停次数增长 | [第 22 篇 §3.3](22-persistence-across-restarts.md#33-产物目录) |
| O-07 | 同一运行中 VM 被反复捕获时内存层越来越大（脏位不清除） | AENV 补丁版 Firecracker 的 `dirty-memory-ranges`；`overlaybd_snapshot.rs` | 每次 `snapshot()` 重写自启动以来的全部脏页 | [第 42 篇 §6](42-memory-snapshot-over-ublk.md#6-代价边界与技术债) |
| O-08 | 客户端 RPC 超时不取消 daemon 内的处理 | `storage/ublk-daemon/src/client.rs` | 推论：留下节点不知道的 active 设备，shared 计数永不归零 | [第 41 篇 §3.3](41-ublk-daemon.md#33-三类错误与超时) |
| O-09 | 池设备换镜像或改容量失败时既不回池也不拆除 | `storage/ublk-daemon/src/server.rs` 的 `prepare_overlaybd_device()` | 设备泄漏在 daemon | [第 41 篇 §4.3](41-ublk-daemon.md#43-一台池化设备的流转) |
| O-10 | 不经 `stop()` 的 Drop 不释放块设备；`FirecrackerInstance::stop()` 恒返回 Ok | `src/sandbox/firecracker/sandbox.rs`、`instance.rs` | rootfs 与附加盘设备泄漏在 daemon；停止失败不可见 | [第 25 篇 §7.3](25-backend-and-firecracker-process.md#73-没有调用-stop-时) |
| O-11 | 残留网络接口的槽位位只占不清 | `src/sandbox/network/` 槽位分配 | 槽位容量随残留永久减少 | [第 29 篇 §6.5](29-network-slots.md#65-残留接口永久占位) |
| O-12 | 删除进度不跨重启；启动时不回收卷预留；Killing 态无人重试；`deletions` 表留残留项 | `src/orchestrator/service.rs` | 中途崩溃的删除需人工处理 | [第 21 篇 §8](21-deletion-and-volume-capture.md#8-代价与边界)、[第 23 篇 §8](23-auto-eviction-and-ttl.md#8-失败与串行的代价) |
| O-13 | `volume-restore-*` 卷在沙箱删除后只释放不删除 | `src/volume.rs` | 恢复出来的卷累积 | [第 16 篇 §8](16-snapshot-and-volume-api.md#8-从快照恢复卷) |
| O-14 | 节点块缓存：被打开文件钉住的条目使容量上限变软；未 checkpoint 的条目重启后丢失；sandbox-ready 集合不清理；`CachedFile::evict_range` 退化为整文件驱逐 | `storage/overlaybd/src/backend/cache/` | 磁盘占用可超过配置；重启后重新下载 | [第 39 篇 §4.2](39-block-cache-and-background-download.md#42-驱逐按条目按-lru跳过忙条目) |
| O-15 | `deps/` 只增不减 | `src/setup/deps.rs` | 升级后旧版本依赖留在磁盘 | [第 59 篇 §3.2](59-host-setup-and-privileges.md#32-版本化路径与存在即已安装) |

### 4.3 关闭、重启与持久记录

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| O-16 | 关闭时 pause 串行执行；三轮仍失败则跳过网络清理 | `Orchestrator::shutdown()` | 关闭时间正比于运行中沙箱数；失败时留下网络残留 | [第 10 篇 §3.2](10-node-process-and-object-model.md#32-orchestratorshutdown只把-paused-留到下次) |
| O-17 | systemd `KillMode=process` + `TimeoutStopSec=30` 与串行 pause 冲突；Compose 无 `stop_grace_period` | `deploy/` 的 systemd 单元与 Compose 文件 | 超时后只杀 `server`，Firecracker 成为孤儿 | [第 60 篇 §2.3](60-deployment.md#23-systemd-单元逐项) |
| O-18 | SIGKILL 后孤儿 Firecracker 进程、`firecracker-work/`、`managed-snapshots/` 无人回收；构建 VM 同样 | 节点启动路径 | 需外部清理（如 systemd 按 cgroup） | [第 22 篇 §7](22-persistence-across-restarts.md#7-崩溃一致性边界) |
| O-19 | 记录版本不符即删、无迁移；`decode()` 忽略 `artifact_root`、记录依赖绝对路径；无法删除的残留目录阻止启动；旧 `"Cow"` 后端记录只能丢弃 | `src/orchestrator/persistence/` | 升级或搬迁 `$AENV_HOME` 会丢失暂停沙箱 | [第 22 篇 §6.1](22-persistence-across-restarts.md#61-清理规则) |
| O-20 | 暂停不清 `expires_at`，暂停沙箱每轮被克隆再跳过；可恢复失败每拍重试 | `src/orchestrator/store/` 与驱逐循环 | 驱逐开销随暂停沙箱数线性增长 | [第 23 篇 §8](23-auto-eviction-and-ttl.md#8-失败与串行的代价) |
| O-21 | 暂停沙箱的记录与产物只在原节点 | `$AENV_HOME/persisted-sandboxes` | 节点丢失即暂停沙箱丢失 | [第 08 篇 §5](08-system-architecture.md#5-存储拓扑什么是真相) |
| O-22 | 节点重启后 P2P catalog 不重新登记到 scheduler；自广告不合并先前 provider（TODO） | `src/p2p/` | 重启后的节点不再被当作制品来源 | [第 58 篇 §3.5](58-p2p-artifact-transport.md#35-scheduler-侧的索引) |
| O-23 | image-cache 同镜像转换锁只在进程内；推论：regctl 复制整个镜像（已命中的层也下载） | `src/image/` | 多实例共享缓存目录时重复转换；带宽浪费 | [第 45 篇 §5.1](45-oci-to-overlaybd.md#51-目录) |

### 4.4 配置与默认值

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| O-24 | 配置文件缺失不报错，静默用代码默认值；代码默认与 `default.toml` 在 `boot_args`、`capacity_gb`、`remote_blocks.max_size_gb`（10 vs 100）、`node_id` 上不同 | `src/cfg.rs` | 路径写错时节点以另一套参数运行 | [第 11 篇 §6.3](11-configuration.md#63-没有配置文件时) |
| O-25 | 内核命令行两份默认：`DEFAULT_BOOT_ARGS` 与 `default.toml` 不一致 | `src/sandbox/firecracker/config.rs` | DAMON 参数需两边同步；推论：缺 `init=/init` 时 guest 能否起来取决于 tools 盘布局 | [第 11 篇 §6.1](11-configuration.md#61-内核命令行的两份默认) |
| O-26 | ublk-daemon 用自己的 `DaemonTomlConfig` 读同一文件，`deps_path` 缺省 `./env` | `storage/ublk-daemon/src/main.rs` | 推论：按默认文件部署时冷启动扩容找不到 `overlaybd-resize` | [第 11 篇 §5](11-configuration.md#5-同一个文件的第二个读者) |
| O-27 | `startup_prewarm` 在 `server` 侧缺省 true、daemon 侧按 `UBLK_F_UPDATE_SIZE` 决定；`[pool.network] startup_prewarm` 无读取者；`[pool.network] enabled=false` 不阻止缓存 | `src/cfg.rs`、`src/sandbox/network/manager.rs` | 读配置的人得出相反结论 | [第 32 篇 §7](32-warm-pools.md#7-代价与边界) |
| O-28 | `default.toml` 写死 `service_instance_id = "service-instance-a"`，Compose 与 k8s 都不覆盖 | `config/default.toml` | `UnregisterNode` 的防误注销校验失效 | [第 54 篇 §3.2](54-control-plane-overview.md#32-消息设计里的几个决定) |
| O-29 | `cluster_id` 解析失败降级为 nil UUID 而非拒绝启动；`/nodes` 恒报 Ready | `src/api/impls/` | 配置错误不可见 | [第 12 篇 §6](12-spec-driven-server.md#6-最小的实现health-与-nodes) |
| O-30 | 环境变量命名不一：`AGENTENV_MEMORY_SNAPSHOT_TRACK_DIRTY_PAGES`、`AENV_OBSERVABILITY_SCHEDULER_ENDPOINT`、`API_ADDR` | `src/cfg.rs` | 按前缀或节名推断变量名会漏掉 | [第 11 篇 §6.2](11-configuration.md#62-环境变量的命名) |
| O-31 | `docker-setup.sh` 与 `--setup-host` 都写 `/etc/sysctl.d/99-aenv.conf`，只有后者含 `ip_forward` | `scripts/`、`src/setup/` | 先后运行可能丢掉转发，节点拒绝启动 | [第 59 篇 §4.2](59-host-setup-and-privileges.md#42-容器宿主docker-setupsh) |
| O-32 | k8s base 清单：每个节点各有自己的快照仓库；无 Redis、query-only、生产 token seed；hostPath 盖住镜像里预烘焙的依赖；不经 `run.sh` 直接 apply 得到空 key 而启动失败 | `deploy/k8s/` | 清单不能直接用于多节点生产 | [第 60 篇 §5.5](60-deployment.md#55-清单里没有的部件) |
| O-33 | 槽位容量要算上网络池与进程池的占用；`--setup-host` 不设 `ublks_max`、不改 `/dev/kvm` 权限 | `src/setup/` | 实际可用槽位少于配置值 | [第 59 篇 §4.1](59-host-setup-and-privileges.md#41---setup-host-做了什么) |
| O-34 | `[pool.block].maintenance_enabled` 不起作用 | `src/cfg.rs` 的 `block_pool_config()` 恒写 `false` | 设置这个键没有任何效果 | [第 71 篇 §7](71-config-env-ports-reference.md#7-不一致与技术债) |
| O-35 | 省略 `[pool.block].enabled` 时 `server` 与 daemon 的缺省不同；配置文件不存在时 `server` 仍把编译期缺省路径作为 `--config` 传给 daemon | `src/cfg.rs`；`storage/ublk-daemon/src/main.rs` | 推论：两个进程对「池是否开着」看法不一；没有配置文件时 daemon 读文件失败而起不来，与 `server` 的静默回退相反 | [第 71 篇 §3](71-config-env-ports-reference.md#3-ublk-daemon-读的键) |
| O-36 | `BackendConfig::posix_fs` 是 `Option` 且无 `#[config(nested)]`，内层的 `env = "AENV_SNAPSHOT_STORE"` 不参与加载 | `src/cfg.rs` 的 `PosixFsBackendConfig` | 推论：设置 `AENV_SNAPSHOT_STORE` 不改变仓库根，而 `env-vars.md` 称它可以覆盖 | [第 71 篇 §7](71-config-env-ports-reference.md#7-不一致与技术债) |
| O-37 | gateway 与 scheduler 的 `-config` 文件不存在即启动失败；JSON 里的时长字段必须写成字符串 | `services/shared/config/config.go` 的 `load()` | 与节点「文件缺失静默回退」的行为相反；写成数字的时长直接报错 | [第 71 篇 §4.1](71-config-env-ports-reference.md#41-加载顺序) |
| O-38 | `[custom_extension].url` 的示例端口 9090 与 scheduler 缺省 gRPC 端口相同；gateway 9102、scheduler 9101 指标端口在 Compose 与 k8s 清单里未发布；`[tools].control_plane_port` 只改宿主一侧，`aenv` 写死 `ENVD_PORT_STR = "49983"` | `config/default.toml`；`deploy/`；`crates/aenv/src/grpc/mod.rs` | 照抄示例会与 scheduler 冲突；控制面指标需另行暴露；改 envd 端口后连不上 guest | [第 71 篇 §6.2](71-config-env-ports-reference.md#62-部署清单里的映射) |
| O-39 | `UblkDaemonClient::shutdown()` 丢弃 `Shutdown` RPC 的结果，随后等待 daemon 退出不设上限 | `storage/ublk-daemon/src/client.rs`；调用方 `src/sandbox/ublk/device.rs` 的 `shutdown_daemon()` | 推论：daemon 收到请求后卡住时，节点关闭随之挂起，直到外部超时 | [第 72 篇 §4](72-api-reference.md#4-ublk-daemon-的-14-种-rpc) |

### 4.5 观测

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| O-40 | Terminal 失败移除沙箱不发 Delete 事件；删除沙箱不清指标样本；按 `dev_id` 的 gauge 不移除 | `src/observability/` | 事件流与指标里残留幽灵沙箱与设备 | [第 24 篇 §4.1](24-metrics-and-events.md#41-谁发发什么) |
| O-41 | route 标签把 connect / timeout / refreshes 归为 `unmatched`；stage 计时不覆盖 delete、驱逐与关闭时的暂停 | `src/observability/` | 这些操作的延迟分布不可见 | [第 24 篇 §5.2](24-metrics-and-events.md#52-指标一览) |
| O-42 | `ReportSandboxEvent` 在 scheduler 端只记 debug 丢弃 | `src/observability/reporter.rs` 与 scheduler | 节点事件对集群不可见，同步全靠心跳 | [第 24 篇 §4.1](24-metrics-and-events.md#41-谁发发什么) |
| O-43 | gateway 的 `RecordAssignment` 失败只记 warn | `services/gateway/internal/server.go` | 绑定缺失要到数据面 404 时才暴露 | [第 55 篇 §6.2](55-gateway.md#62-失败时的两种处理) |
| O-44 | gateway 的 404 不区分沙箱不存在与绑定缺失，且是纯文本；hint 只为 debug 日志缓冲 | `server.go` | 排障时无法区分两类问题 | [第 55 篇 §4](55-gateway.md#4-选节点) |
| O-45 | 没有指标区分「没有 startup pack」与「pack 失败」；`PackRecordingStatus` / `PrefetchStartupPack` RPC 总是返回 Ok | `storage/ublk-daemon/src/server.rs` | 预取失效不可见 | [第 43 篇 §6](43-startup-pack-and-prefetch.md#6-代价与边界) |
| O-46 | `FG_REMOTE_INFLIGHT` 统计所有读而非只远端读 | `storage/overlaybd/src/download_gate.rs` | 前台优先的判断基于偏大的计数 | [第 39 篇 §6.1](39-block-cache-and-background-download.md#61-download_gate) |
| O-47 | 集群沙箱列表每翻一页都向所有节点拉全量 | gateway 本地聚合 | 列表开销正比于页数乘节点数 | [第 55 篇 §7.1](55-gateway.md#71-集群沙箱列表) |
| O-48 | 主机 CPU% 是距任何调用者上次读 `/proc/stat` 的差值，`GET /nodes` 与心跳共享基线 | `src/observability/` | 两个读者互相扰动读数 | [第 57 篇 §2.2](57-heartbeat-and-cpu-intersection.md#22-主机指标) |

### 4.6 遗留代码与无调用者的路径

这些条目本身不改变行为，但会误导读代码的人：一个看起来负责某件事的函数，实际上从未被调用；一个注释描述的守卫并不存在。

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| O-49 | 遗留 CLI `uvm-ublk`：一进程一设备，`Recovery` 分支 `unimplemented!()` | `storage/ublk/src/main.rs` | 与 daemon 并存，易被当作恢复工具 | [第 40 篇 §8](40-ublk-library.md#8-遗留代码与技术债) |
| O-50 | `spawn_data_io_ring_worker()` 无调用者；`UserBuffer` 的 fixed 注册未被使用；`slot_task()` 两处 EINTR FIXME | `storage/ublk/src/lib.rs` | 死代码与未决的错误处理 | [第 40 篇 §8](40-ublk-library.md#8-遗留代码与技术债) |
| O-51 | `update_size` 与 `get_features` RPC 只有测试使用；`get_features` 在池关闭时恒为 0 | `storage/ublk-daemon/src/client.rs` | 接口面大于实际使用面 | [第 41 篇 §7](41-ublk-daemon.md#7-技术债与文档漂移) |
| O-52 | `load_snapshot_uffd()` 以 `#[allow(dead_code)]` 保留，`resume_vm=true` | `src/sandbox/firecracker/instance.rs` | 若重新启用会跳过新卷、MMDS 与限流的补发 | [第 44 篇 §6](44-uffd-alternative.md#6-遗留状态) |
| O-53 | 非 ublk rootfs 分支不可达，且会 `copy_cow()` 复制 tools 盘链接 | `sandbox.rs` 的 `snapshot_to_dir()` | 误导；若被走到会复制错误的盘 | [第 27 篇 §8](27-start-pause-resume-sequences.md#8-遗留路径与技术债) |
| O-54 | `TemplateBuildRootfsBase::Ext4` 与 `TemplateBuildSpec::from_existing_rootfs()` 只有测试使用 | `src/template/` | 生产路径直接报错 | [第 52 篇 §8](52-template-builder.md#8-技术债与边界) |
| O-55 | `OrchestratorError::InvalidTimeout` 从未构造，匹配它的分支是死代码 | `src/orchestrator/mod.rs`、`src/api/impls/sandbox.rs` | TTL 校验看似存在而实际不在这一层 | [第 14 篇 §4](14-sandbox-api.md#4-四个改-ttl-的入口) |
| O-56 | `RecordingVerdict::Fail` 从未构造，注释描述的录制质量守卫不存在；`pack_planner` 的 v2 预算模型已失效（传 `u64::MAX`） | `storage/ublk/src/impls/startup_pack_recorder.rs`；`storage/overlaybd/src/backend/cache/startup_pack_task.rs` | 劣质 trace 不会被拒绝 | [第 43 篇 §6](43-startup-pack-and-prefetch.md#6-代价与边界) |
| O-57 | `WaitPending` 分支不可达且注释不符；`DEFAULT_MAX_REFILLING` 不真正限制并发 | `storage/overlaybd/src/backend/cache/bk_download.rs`、`cache_store.rs` | 后台下载并发不受名字暗示的约束 | [第 39 篇 §5.5](39-block-cache-and-background-download.md#55-下载完成之后) |
| O-58 | `CachedFs` 在 crate 外无调用者，移植自上游的 basename 键变换只在这里生效 | `storage/overlaybd/src/backend/cache/cached_fs.rs` | 「按 digest 跨 registry 共享缓存」不成立 | [第 39 篇 §2.2](39-block-cache-and-background-download.md#22-条目与键) |
| O-59 | `set_switch_file()` 除测试外无调用者，SwitchFile 只做 ZFile 识别 | `storage/overlaybd/src/backend/switch.rs` | 「后台下载完成后切到本地文件」不发生 | [第 38 篇 §3.3](38-virtualfile-chain-and-remote-io.md#33-tar-适配与-switchfile) |
| O-60 | `/p2p-control/publish-layer` 无调用者，daemon 下载的层从不发布 | `src/overlaybd/p2p/` | 层只能经转换路径进入 P2P | [第 58 篇 §5.3](58-p2p-artifact-transport.md#53-中途出错为什么不回退) |
| O-61 | group commit 在生产中从未打开；upper 索引重放两遍；每次写后都刷新大小 | `storage/overlaybd/src/` 的 RW 布局 | 代码路径多于运行路径 | [第 36 篇 §6.2](36-read-write-paths-and-rw-layouts.md#62-其它值得记下的点) |
| O-62 | ZFile `level` 不被读取；本地与远端两套 digest，重封装后 uuid 为 nil | ZFile 发布 | 配置项无效；同一层两种身份 | [第 35 篇 §7.1](35-zfile-compression.md#71-本地-raw发布时压缩) |
| O-63 | 两份 `ProcessVmReader`（现行与 `uffd-core`）实现不一致；`uffd-core` 不在 workspace、不受 clippy 检查 | `src/sandbox/firecracker/process_vm_reader.rs`、`storage/uffd-core/` | 修一处漏一处 | [第 44 篇 §6](44-uffd-alternative.md#6-遗留状态) |
| O-64 | 同一概念的重复定义：`RestackSnapshotTerminalFailure` 两份；两套 registry 客户端（regctl 与 `AcrClient`）；`schedule_hint.go` 手工镜像 openapi 字段 | `src/sandbox/ublk/device.rs` 与 `storage/overlaybd/`；`acr/client.rs`；`services/` | 两侧可能静默分叉 | [第 37 篇 §3.3](37-seal-restack-compact.md#33-terminal-分界与不回滚的理由)、[第 54 篇 §6](54-control-plane-overview.md#6-契约之外的耦合) |
| O-65 | 槽位命名误导：drive id `rootfs` 与文件名 `rootfs.ext4` 实指 tools 盘 | `src/sandbox/firecracker/` | 读代码与日志时易误判哪块盘出了问题 | [第 26 篇 §2.1](26-sandbox-block-devices.md#21-命名) |
| O-66 | `src/snapshot/mock.rs` 是 `pub` 模块，编进生产库 | `src/snapshot/mod.rs` | 测试替身成为公开接口 | [第 63 篇 §4.1](63-testing-and-benchmarks.md#41-trait-替身) |
| O-67 | 约 50 处 `SAFETY` 注释对约 117 处 `unsafe`，无工具强制；`build_restore_script()` 的 `debug_assert` 实际要求表名字典序 | 全仓库；`src/sandbox/network/iptables_util.rs` | 不变量只靠人工维护 | [第 07 篇 §8](07-rust-async-primer.md#8-代码组织纪律)、[第 29 篇 §4.3](29-network-slots.md#43-iptables-的提交方式) |

### 4.7 测试缺口

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| O-68 | `TestScheduleOnlyConsidersReadyNodes` 只验证不选 lingering，从未构造心跳超时的节点 | `services/scheduler/internal/service_test.go` | 测试名掩盖了 A-12 | [第 56 篇 §2.4](56-scheduler.md#24-不排除-unhealthy-节点) |
| O-69 | E2E 跳过的 suite 记为 pass；`09_e2b_compat.sh` 缺工具时记 pass | `scripts/tests/` 的 E2E 脚本 | 绿色结果不代表被执行 | [第 63 篇 §2.4](63-testing-and-benchmarks.md#24-http-端到端套件) |
| O-70 | 三个 ignored 用例没有任何入口运行；覆盖率不含它们 | `tests/` 与 CI | 这些路径实际无人验证 | [第 63 篇 §2.1](63-testing-and-benchmarks.md#21-单元测试与能力测试) |
| O-71 | 覆盖率与变异测试 `continue-on-error`；基准无基线与阈值；snapshot 基准冒烟失败时静默跳过；OCI 转换基准手抄生产流水线 | `.github/workflows/`、`crates/benchmarks/` | 回归不会让 CI 失败 | [第 63 篇 §5](63-testing-and-benchmarks.md#5-ci-矩阵)、[第 63 篇 §6](63-testing-and-benchmarks.md#6-基准) |
| O-72 | PVM 没有任何测试 | 全仓库 | PVM 路径的行为只能推论 | [第 61 篇 §4.3](61-pvm.md#43-pvm-下的语义只能推论) |

---

## 5. 安全与信任边界

AgentENV 的安全模型可以用一句话概括：**一个部署是一个信任域**。控制面只有一个 API key，没有租户；集群内的节点、scheduler 与 P2P 对端彼此信任；
宿主网络与防火墙被假设为已经把节点间端口限制在集群内。这一类条目列出的，是这些前提在代码里的具体落点，以及前提不成立时暴露的面。
多数条目是有意的取舍，记在这里是因为部署者需要知道该由哪一层补上。

### 5.1 P2P 的信任边界

P2P 子系统的校验链有一个共同的锚点：descriptor 来自对端本人（[第 58 篇 §6](58-p2p-artifact-transport.md#6-失败原则与信任边界)）。具体地：

- `src/p2p/iroh/transport.rs` 以 `BlobsProtocol::new(&store, None)` 创建 blobs 协议，没有访问控制，知道 hash 就能取字节；catalog ALPN 同样无鉴权，端点缺省监听 `0.0.0.0` 的系统分配端口。
- 快照固定制品（vm_state、manifest）的 key 只含快照 ID，record 里没有它们的 digest；iroh 只验证「字节与对端报的 hash 一致」，一个能回答 catalog 请求的对端可以为这个 key 提供任意内容。
- overlaybd 层的校验比较的是对端 metadata 里的 digest 与请求 URL 里的 digest，二者都不来自对字节的 sha256 计算；P2P 路径也不经过 registry 认证，节点能否读到某层只取决于集群里是否有对端持有它。
- scheduler 的心跳与 P2P RPC 没有鉴权，任何能报出一个发现列表里节点 ID 的进程，都能把自己的 endpoint 登记为该节点的 P2P 地址。

合起来的后果是：开启 P2P 后，快照 vm_state 与镜像层的完整性取决于集群里最弱的一台节点；在多租户或节点不完全受信的环境里，这等于把 guest 内存与根文件系统的内容交给任何一台被攻破的节点。
默认配置把 P2P 标为 EXPERIMENTAL，关闭它只损失加速，不影响正确性。补强的方向在代码里已有先例——本地 `/p2p-control/publish-layer` 端点因为「回环只是进程边界、不是信任边界」而重算了 digest。

### 5.2 条目表

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| S-01 | P2P catalog 与 blobs 无访问控制；固定制品 key 无 digest；层校验不重算 sha256；绕过 registry 认证 | `src/p2p/iroh/transport.rs`；`src/overlaybd/p2p/facade.rs` | 见 §5.1 | [第 58 篇 §6](58-p2p-artifact-transport.md#6-失败原则与信任边界) |
| S-02 | scheduler gRPC 明文无认证；gateway 到 scheduler 无 TLS；心跳可冒充节点登记 P2P 地址 | `services/scheduler/`、`services/gateway/` | 能连上 scheduler 端口即可改绑定与路由 | [第 54 篇 §7](54-control-plane-overview.md#7-信任边界) |
| S-03 | spec 声明的 `X-Team-ID`、Bearer、`X-Admin-Token` 一律退化为检查 `X-API-Key`；`Claims` 是空结构体 | `src/api/impls/auth.rs` 的 `has_valid_api_key()` | 单 key、无租户、无只读 scope；读 spec 的人会误判 `/nodes` 需要 admin token | [第 13 篇 §5](13-authentication.md#5-生成层的副检查与名不副实的安全方案) |
| S-04 | 数据面 token 不能单独吊销；显式 seed 被改无检测、旧 token 静默失效；集群 seed 不一致只告警 | `src/api/impls/auth.rs` 的派生与校验 | 泄露的 token 只能靠轮换全局 seed 失效 | [第 13 篇 §3.3](13-authentication.md#33-生命周期) |
| S-05 | 非 secure 沙箱的 envd 只靠 UUID 保护，v1 创建缺省非 secure；不检查「私有入口必须 secure」 | `src/api/impls/sandbox.rs`；`require_auth()` | 知道沙箱 ID 即可访问其 envd | [第 13 篇 §4.3](13-authentication.md#43-数据面)、[第 18 篇 §5](18-e2b-compatibility.md#5-偏差矩阵) |
| S-06 | 推论：宿主 FORWARD 策略是数据面鉴权的前提 | `src/sandbox/network/` | 宿主 FORWARD 默认放行时外部主机可直连 guest 端口，绕过代理鉴权 | [第 29 篇 §6.1](29-network-slots.md#61-依赖宿主防火墙的前提) |
| S-07 | Firecracker 与 `server` 同 uid，不用 jailer | `src/sandbox/firecracker/instance.rs` 的 `spawn_with_netns()` | 推论：VMM 逃逸后可读其它沙箱的 ublk 块设备与 `secrets/` | [第 25 篇 §5](25-backend-and-firecracker-process.md#5-不用-jailer哪些隔离有哪些没有) |
| S-08 | 「Firecracker 不带能力」只在 `server` 非 root 时成立；Compose 与 DaemonSet 都是特权容器内的 root | `src/privileges.rs`；`deploy/` | 容器部署下 Firecracker 拿到完整能力集 | [第 59 篇 §6](59-host-setup-and-privileges.md#6-边界与代价) |
| S-09 | ublk-daemon 不为子进程清 ambient 能力 | `storage/ublk-daemon/src/runtime.rs` 的 `run_resize_tool()` | 推论：`overlaybd-resize` 带 `CAP_SYS_ADMIN` 运行 | [第 59 篇 §6](59-host-setup-and-privileges.md#6-边界与代价) |
| S-10 | ublk-daemon 的 metrics 监听 `0.0.0.0:9103`，无鉴权 | `storage/ublk-daemon/src/main.rs` | 设备与镜像信息对网络可见 | [第 41 篇 §2.1](41-ublk-daemon.md#21-拉起与就绪) |
| S-11 | `deactivate()` 停止监听但不断开已授权的连接 | `src/sandbox/network/` 的出站代理 | 移除策略后旧连接按旧策略继续 | [第 30 篇 §5.2](30-egress-policy-and-proxy.md#52-代理的两阶段状态) |
| S-12 | 预热槽位回池不清代理连接、conntrack 与邻居表；推论：扩展在 netns 里的改动随槽位残留 | `src/sandbox/network/manager.rs` | 上一个沙箱的连接状态与网络改动可能被下一个沙箱继承 | [第 30 篇 §6.4](30-egress-policy-and-proxy.md#64-预热槽位的跨租户残留) |
| S-13 | 扩展 hook 返回的 boot args 不过滤，只有 API 的 `extraBootArgs` 过白名单 | `src/sandbox/firecracker/` 的 boot args 拼装 | 扩展的错误参数直接进入 guest 内核命令行 | [第 27 篇 §2.1](27-start-pause-resume-sequences.md#21-boot-args-的拼装) |
| S-14 | 模板构建 VM 用缺省出站策略（可上网）；扩展也会看到 API 查不到的构建 VM sandboxId | `src/template/runner.rs` | 构建步骤可访问任意外部地址 | [第 52 篇 §8](52-template-builder.md#8-技术债与边界)、[第 33 篇 §6](33-custom-extension-hooks.md#6-代价与边界) |
| S-15 | 宿主会改写 guest 的 `/etc/passwd` | `src/sandbox/envd/user.rs` 与 `/init` 流程 | guest 内用户数据库被宿主修改 | [第 28 篇 §4.3](28-mmds-and-envd.md#43-数字-user两次-init) |
| S-16 | 500 响应原样返回内部错误链 | `src/api/impls/` 的错误映射 | 内部路径与依赖信息泄露给调用方 | [第 12 篇 §5](12-spec-driven-server.md#5-错误映射) |
| S-17 | `aenv` 保存凭据先 `fs::write` 再 chmod 0600 | `crates/aenv/` | 按 umask 可读的短窗口 | [第 62 篇 §2](62-aenv-cli.md#2-分层) |
| S-18 | 块设备池回收时 `clear_page_cache()` 失败只告警，设备照常进池 | `src/sandbox/ublk/` 的块设备池 | 推论：旧租户的页可能残留在页缓存里 | [第 32 篇 §4](32-warm-pools.md#4-块设备池) |

---

## 6. 供应链与构建

这一类条目关心的是「同一个 tag 能否得到同一份产物、产物能否被验证」。AgentENV 在主路径上做了固定：openapi-generator 的包装器与 jar 版本、Rust 工具链、`Cargo.lock`、依赖 manifest 都是钉住的。
未固定或未校验的环节集中在旁路——protoc、Go 镜像、tools 盘镜像的引用方式、安装脚本、文档站与测试用的第三方镜像。
其中「生成代码无漂移检查」影响面最大：OpenAPI 产物与 Go 的 `.pb.go` 都入库，CI 不重新生成比较，而 Rust 侧的 gRPC 代码每次构建生成；spec、proto 与入库产物三者的一致性只靠评审。

| 编号 | 现象 | 位置 | 后果 | 详讲 |
|---|---|---|---|---|
| B-01 | OpenAPI 产物与 `.pb.go` 入库，CI 没有「重新生成并比较」的检查；Rust 侧只生成客户端、每次构建生成 | `adev/src/codegen.rs`、`services/Makefile`、`build.rs` | spec、proto 与产物可能静默不一致 | [第 64 篇 §3](64-build-codegen-release.md#3-生成代码)、[第 54 篇 §5.3](54-control-plane-overview.md#53-不对称的后果) |
| B-02 | server 后处理 `fix_duplicate_auth_trait()` 是逐字正则；生成的 `new()` 中 `ApiKeyAuthHeader` 约束重复四次 | `adev/src/codegen.rs` | 生成器格式一变，后处理静默失效 | [第 12 篇 §2](12-spec-driven-server.md#2-生成管线) |
| B-03 | protoc 版本三处不一致：CI `33.4`、release 用 apt 包、入库 `.pb.go` 头为 `3.21.12` | `Makefile` 的 `ci-deps`；`.github/workflows/release.yml` | 推论：proto 用新语法时发布构建先失败 | [第 64 篇 §3](64-build-codegen-release.md#3-生成代码) |
| B-04 | `adev` 下载 protoc 不校验，文件非空即跳过 | `adev/src/` | 半截或被替换的二进制不会被发现 | [第 64 篇 §2.3](64-build-codegen-release.md#23-adev开发与-ci-工具) |
| B-05 | release 流水线不依赖 CI 测试 | `.github/workflows/release.yml` | 未通过测试的提交也能打包发布 | [第 64 篇 §4](64-build-codegen-release.md#4-发布流水线) |
| B-06 | gateway / scheduler 镜像不随版本发布，仓库清单只引用本地 `:latest`；Go 镜像不注入版本与提交号 | `services/`、`deploy/` | 集群组件版本不可追溯 | [第 64 篇 §4.5](64-build-codegen-release.md#45-节点镜像) |
| B-07 | 节点镜像与 release bundle 是两次独立构建：镜像内不带 `--locked`、不用 vendored-openssl | `Dockerfile` 与 release workflow | 同一版本号的两种产物依赖可能不同 | [第 64 篇 §4.5](64-build-codegen-release.md#45-节点镜像) |
| B-08 | 推论：`.dockerignore` 排除 `.git`，镜像里的提交号为 `unknown` | `build.rs` 的提交号注入 | 镜像无法对应到提交 | [第 64 篇 §2.4](64-build-codegen-release.md#24-buildrs构建时生成与提交号) |
| B-09 | 推论：Dockerfile 的 `RUSTUP_TOOLCHAIN=${RUST_VERSION}` 无对应 `ARG` | `Dockerfile` | 工具链变量可能为空，退回 `rust-toolchain.toml` | [第 60 篇 §3](60-deployment.md#3-docker-镜像) |
| B-10 | `install.sh` 用 GitHub API 返回的资产摘要而不用 `SHA256SUMS`；两个安装脚本本身不在 `SHA256SUMS` 里 | `scripts/install.sh`、`scripts/install-cli.sh` | 校验链依赖 API 而非发布物自身 | [第 64 篇 §4.4](64-build-codegen-release.md#44-github-release) |
| B-11 | 依赖下载只有传输层保证；`OverlaybdInstalledRelease.digest` 恒为 None | `src/setup/deps.rs` | 已安装依赖无法事后校验 | [第 59 篇 §3.3](59-host-setup-and-privileges.md#33-下载只有传输层的保证) |
| B-12 | `publish-tools-image.yml` 的 `tools_version` 缺省 `0.1.0`，其它处为 `0.1.1`；manifest 按 tag 而非 digest 引用 tools 盘镜像 | `.github/workflows/`、`config/deps_manifest.toml` | tag 被重推时节点拿到不同内容 | [第 64 篇 §5](64-build-codegen-release.md#5-tools-盘镜像) |
| B-13 | `[envd] version` 只声明不核对；`runtime_versions` 只核对 tools 盘版本 | `src/sandbox/envd.rs`、`src/orchestrator/` | guest 内 envd 版本与声明不符时无人发现 | [第 28 篇 §3.1](28-mmds-and-envd.md#31-来源与拉起)、[第 61 篇 §5.1](61-pvm.md#51-为什么模式要跟着状态走) |
| B-14 | `thirdparty/firecracker-client` 版本号写 `1.15.1`，描述的却是 AENV 补丁版 Firecracker 的 API | `thirdparty/firecracker-client/Cargo.toml` | 版本号不说明 API 来自补丁版 | [第 64 篇 §3](64-build-codegen-release.md#3-生成代码) |
| B-15 | mdBook 版本未固定 | `docs/book.toml` 与文档 workflow | 文档站构建不可复现 | [第 64 篇 §6](64-build-codegen-release.md#6-文档站) |
| B-16 | 测试依赖未固定：`test_envd.sh` 用第三方 `envd-debug:latest`；E2B 基准克隆未固定版本的个人 fork；兼容性套件的 SDK 版本不固定 | `scripts/tests/`、`crates/benchmarks/` | 测试结果随外部仓库漂移 | [第 63 篇 §2.5](63-testing-and-benchmarks.md#25-外围对象)、[第 63 篇 §6](63-testing-and-benchmarks.md#6-基准) |
| B-17 | zstd 层先经 `zstd -dc` 管道解压再交给工具，绕开工具缺陷 | `src/image/` 的层转换 | 依赖宿主 `zstd` 二进制，且多一次拷贝 | [第 45 篇 §4.4](45-oci-to-overlaybd.md#44-一层的转换) |
| B-18 | guest 内核配置不可追溯：两个仓库都没有 `vmlinux-6.1.175` 的配置与构建脚本；上游 6.1 CI 配置写着 `# CONFIG_DAMON_RECLAIM is not set` | `config/deps_manifest.toml` 的 `[kernel.kvm]`；补丁版 Firecracker 的 `resources/guest_configs/` | 推论：若内核按上游配置构建，`damon_reclaim.*` 参数被忽略，guest 内冷页回收静默失效 | [第 67 篇 §7.2](67-firecracker-patch-layer.md#72-boot-args-隐含的要求) |
| B-19 | 补丁版 `VirtioBlockState` 新增 `direct` 字段靠 `#[serde(default)]` 兼容旧快照，而状态文件是 bitcode 编码，`SNAPSHOT_VERSION` 未提升 | 补丁版 Firecracker 的 `src/vmm/src/devices/virtio/block/virtio/persist.rs` | 推论：补丁版与上游 v1.15.1 的状态文件互相读不了，报的是反序列化错误而不是版本不符 | [第 67 篇 §4](67-firecracker-patch-layer.md#4-drive-的-direct补丁-③-与-⑥) |
| B-20 | 快照元数据记录 `firecracker_version`，恢复时只核对 tools 盘版本 | `SnapshotRuntimeVersions` 与恢复路径 | 换 Firecracker 二进制后旧快照能否恢复要到 load 时才知道 | [第 67 篇 §6](67-firecracker-patch-layer.md#6-补丁栈的后续) |

---

## 7. 文档漂移

AgentENV 的 `docs/src/**`、README、`CLAUDE.md` 与配置注释是参考，不是依据。本书各篇读代码时记下了它们与代码不一致的地方；
漂移的方向大多是「文档描述的是设计意图或旧版本」，而不是笔误。读文档时，凡涉及行为的句子都应以代码为准。

### 7.1 startup pack 的版本称呼

内存 startup manifest 的称呼在代码里不统一：仓库里的文件名是 `memory-startup.pack`，内容却是 manifest 而不是打包的页数据；记录里的描述符字段 `index_sha256` 实为整个 manifest 的 sha256；
魔数是 `AENVMF01`、版本字段为 4，而注释里 `default.toml` 与 `startup_pack.rs` 称 v4，`src/cfg.rs`、`src/sandbox/ublk/device.rs`、`startup_pack_task.rs` 称 v3，`oss/resolver.rs` 称 v2。
本书统一称它为 startup manifest（`AENVMF01`，格式版本 4）。旧格式在消费端一律被拒绝、退回按需加载，所以混用不影响行为，只影响阅读（[第 43 篇 §3.3](43-startup-pack-and-prefetch.md#33-名字的混用)）。

### 7.2 条目表

| 编号 | 现象 | 位置 | 实际行为 | 详讲 |
|---|---|---|---|---|
| D-01 | host interaction 地址写「/31 per slot」 | `docs/src/internals/networking.md` | host interaction 地址不是每槽位一个 /31 | [第 29 篇 §2.2](29-network-slots.md#22-地址计划) |
| D-02 | 「移除策略或槽位时关闭所有被跟踪的连接」 | `networking.md` | `deactivate()` 不断开已有连接 | [第 30 篇 §5.2](30-egress-policy-and-proxy.md#52-代理的两阶段状态) |
| D-03 | `host_ns_fd` 注释写 `/proc/1/ns/net`；`Slot::cleanup()` 注释仍说删除 MASQUERADE | `src/sandbox/network/slot.rs` | 注释描述的是旧实现 | [第 29 篇 §4.1](29-network-slots.md#41-为什么要开线程)、[第 29 篇 §5.3](29-network-slots.md#53-清理) |
| D-04 | `/dev/vda` 标成 rootfs；状态列表只有 Creating、Running、Pausing、Paused、Resuming、Killing | `docs/src/internals/architecture.md` | `/dev/vda` 是 tools 盘；漏列 Snapshotting、Forking | [第 26 篇 §2.1](26-sandbox-block-devices.md#21-命名)、[第 19 篇 §2](19-state-machine-and-concurrency.md#2-八个状态) |
| D-05 | 「AutoReg zero-copy, kernel 6.8+」；README 与部署文档写 6.8+ | `architecture.md`、`README.md` | `UPDATE_SIZE` 与 `AUTO_BUF_REG` 都在 6.16 首次出现 | [第 04 篇 §5.2](04-io-uring-and-ublk.md#52-分级表) |
| D-06 | `zero_copy` 日志字段按 `UBLK_F_SUPPORT_ZERO_COPY` 判断 | `storage/ublk/src/dev.rs` | 实际设置的是 `UBLK_F_AUTO_BUF_REG`，日志恒为假 | [第 40 篇 §8](40-ublk-library.md#8-遗留代码与技术债) |
| D-07 | 设备号「allocated in the daemon」；把 `/dev/ublkcN` 称作 control 设备 | `architecture.md` | 设备号由内核分配；控制命令走 `/dev/ublk-control` | [第 41 篇 §7](41-ublk-daemon.md#7-技术债与文档漂移) |
| D-08 | 查询「dirty/present memory ranges」 | `architecture.md` | 缺省路径报告写过的页，present 只在关闭脏页跟踪时成立 | [第 42 篇 §6](42-memory-snapshot-over-ublk.md#6-代价边界与技术债) |
| D-09 | `fetch_byte_range` 返回 `Result<Bytes>` | `docs/src/internals/p2p-design.md` | 代码返回 `Result<P2pByteStream>` | [第 58 篇 §2](58-p2p-artifact-transport.md#2-抽象keydescriptorprovider) |
| D-10 | 三处与代码不符：模板构建暂存位置、记录文件名、「image-cache 没有统一 GC」 | `docs/src/internals/persistence-artifact-inventory.md` | 见详讲 | [第 46 篇 §5](46-snapshot-object-model.md#5-三层存储) |
| D-11 | 三个链接指向不存在的 `docs/src/concepts/custom-extension.md`、`snapshots.md`、`volumes.md` | `CLAUDE.md`（即 `AGENTS.md`） | 链接失效 | [第 01 篇 §6.3](01-repo-map-and-versions.md#63-go部署与周边) |
| D-12 | query-only HA「只覆盖数据面」 | `services/README.md` | 覆盖一切按已有沙箱路由的请求，但时间上受绑定 TTL 限制 | [第 56 篇 §6.2](56-scheduler.md#62-primary-不可用时)、[第 55 篇 §5](55-gateway.md#5-转发) |
| D-13 | 称 gateway 使用 P2P scheduler API；写 Go 1.21+；限额列表漏 `including_paused` 三项 | `services/README.md` | gateway 不调 P2P RPC；`go.mod` 为 1.25.0 | [第 54 篇 §2](54-control-plane-overview.md#2-三个角色与调用方向)、[第 56 篇 §2.2](56-scheduler.md#22-资源上限) |
| D-14 | proto 状态表「无心跳 → CONNECTING」 | `services/api/proto/scheduler.proto` | 代码里没有对应 | [第 57 篇 §3.3](57-heartbeat-and-cpu-intersection.md#33-节点状态由谁推导) |
| D-15 | `boot_args` 默认值写的是文件里的值；`remote_blocks.max_size_gb` 写 100 | `docs/src/configuration/reference.md` | 代码默认是 `DEFAULT_BOOT_ARGS` 与 10 | [第 11 篇 §6.3](11-configuration.md#63-没有配置文件时) |
| D-16 | 称扩展 `timeout_ms` 不管 stop | `config/default.toml` | stop 同样受这个超时限制 | [第 33 篇 §2](33-custom-extension-hooks.md#2-契约四个-hook) |
| D-17 | 称 `credential_process` 优先于静态凭证 | `config/default.toml` | 两者同配直接报错 | [第 48 篇 §4.4](48-object-storage-repository.md#44-分片上传与凭证) |
| D-18 | 安装 `target/debug/aenv-snapshot-image` | `docs/src/concepts/snapshots/use.md` | 文档让用户装调试构建 | [第 50 篇 §3.1](50-rootfs-as-oci-image.md#31-工具的形状) |
| D-19 | `Snapshot()` 注释「filtered by their derived status」 | `services/scheduler/internal/node_registry.go` | 只过滤 lingering | [第 56 篇 §2.4](56-scheduler.md#24-不排除-unhealthy-节点) |
| D-20 | `src/cfg.rs` 注释写 startup pack「OSS backend only」与「v3」 | `src/cfg.rs` | `recording_enabled_for()` 对所有后端生效，manifest 版本为 4 | [第 43 篇 §6](43-startup-pack-and-prefetch.md#6-代价与边界) |
| D-21 | `bind_alias()` 注释称阿里云 OSS 不支持条件写头，与层上传注释、卷代码的条件写自相矛盾 | `oss/repository.rs` | 卷记录已在用 `if_match` / `if_none_match` | [第 48 篇 §6.4](48-object-storage-repository.md#64-同一个文件里的真-cas) |
| D-22 | 注释「stop 恰好送达一次」 | `src/custom_extension_api/` 的 hook guard | 实为恰好发出一次 | [第 33 篇 §4.2](33-custom-extension-hooks.md#42-guard先记-id再发请求) |
| D-23 | warm-pool 模块文档提到「进程退出 hook」；daemon 侧 `startup_prewarm` 名不副实 | `crates/warm-pool/`；`storage/ublk-daemon/` | 该 hook 不存在 | [第 32 篇 §7](32-warm-pools.md#7-代价与边界) |
| D-24 | `validate_mount_path()` 注释举例「`/p` 会遮住 `/proc`」 | `src/sandbox/extra_drive.rs` | `Path::starts_with` 按路径分量比较，`/p` 不会被拒绝 | [第 31 篇 §2.1](31-extra-drives-and-volumes.md#21-入口校验) |
| D-25 | `FirecrackerSandbox::pause()` 文档注释的根目录层级与代码不符 | `src/sandbox/firecracker/sandbox.rs` | 与 `pause_to_dir()` 实际创建的层级不同 | [第 51 篇 §2.3](51-fork.md#23-后端停一次起-n-台) |
| D-26 | `buckets.go` 的同步注释指向已不含桶定义的文件 | `services/` | 改桶时找不到另一侧 | [第 57 篇 §6](57-heartbeat-and-cpu-intersection.md#6-共用的直方图桶) |
| D-27 | 遗留 CLI 注释「NOTE: why we use fork」，代码里没有 fork | `storage/ublk/src/main.rs` | 注释与代码无关 | [第 40 篇 §8](40-ublk-library.md#8-遗留代码与技术债) |
| D-28 | 环境变量表漏列 `AGENTENV_MEMORY_SNAPSHOT_TRACK_DIRTY_PAGES`（只在 `reference.md` 的说明文字里出现）与编译期的 `AENV_GIT_COMMIT` | `docs/src/configuration/env-vars.md` | 两个变量都被代码读取 | [第 71 篇 §7](71-config-env-ports-reference.md#7-不一致与技术债) |
| D-29 | 补丁版 `CHANGELOG.md` 只列补丁 ⑦，PR 号写成 `#XXXX` 占位，且放在已发布的 `[1.15.1]` 节 | 补丁版 Firecracker 的 `CHANGELOG.md` | 其余六个补丁在变更记录里不可见 | [第 67 篇 §2](67-firecracker-patch-layer.md#2-七个提交) |
| D-30 | swagger 称 `GET /vm/dirty-memory-ranges` 面向已暂停、已启动的 VM | 补丁版 Firecracker 的 `firecracker.yaml` | 代码不检查 Paused，运行中的 VM 也能调用，结果只代表某一刻 | [第 67 篇 §3.2](67-firecracker-patch-layer.md#32-get-vmdirty-memory-ranges补丁-⑦) |

---

## 8. 汇总时删去与复核的条目

### 8.1 删去的条目

下列说法曾在编写过程中出现，经后续核实被推翻或无法在 v0.2.3 中定位，不再列为问题：

| 原说法 | 删去理由 | 现行口径 |
|---|---|---|
| Hybrid RW（flags bit5）是 AgentENV 扩展 | 上游 overlaybd 默认分支 `lsmt/file.cpp` 已定义 `FLAG_HYBRID_RW = 5` | 与上游同位同义，`ReuseZero` 为 Rust 版独有（[第 34 篇 §6](34-lsmt-format-and-index.md#6-与上游的兼容边界)） |
| 上游 overlaybd 只有 TCMU 前端 | 上游默认分支已带 ublk 前端 `src/ublk/` | 「TCMU」只对经典前端成立 |
| `ReloadableIDAllocator` 是死代码 | `AsyncIoRing` 用它分配 sparse 表下标 | 不是技术债（[第 40 篇 §8](40-ublk-library.md#8-遗留代码与技术债)） |
| SwitchFile 在后台下载完成后切到本地文件 | 这是规划笔记对代码的误读，不是代码的缺陷 | 改记为 O-59（`set_switch_file()` 无调用者） |
| 节点块缓存按 digest 跨 registry 共享 | 同上，属笔记误读 | 改记为 O-58（`CachedFs` 无调用者） |
| gateway `request_timeout` 的 90 s 只写在 `local.json` | 90 s 写在三份部署配置里，代码缺省 30 s | 只保留 A-20 的超时差异 |
| `services/README.md` 的 Limitations 节称绑定全在内存 | v0.2.3 的 README 没有这一节，正文写的是可选 Redis | 不列 |
| `sandbox-testing.md` 的 `[firecracker]` 写法、`template-builder-testing.md` 的记录路径与方法名 | 规划阶段的条目，正文各篇未展开，抽查未能定位不一致之处 | 不列，留待复核 |
| 「节点本地只有可重建的派生物」 | 这是早期大纲的说法，不是代码的问题 | 实际情况记为 O-21 |

### 8.2 抽查核实

汇总时对最关键的十余条回到 AgentENV v0.2.3 代码重新核对，结论与各篇一致：

- A-01：`src/sandbox/firecracker/socket.rs` 的 `UnixSocketClient::request()` 直接 `self.client.request(req).await`，无超时包装。
- A-02：`storage/ublk-daemon/src/client.rs` 的 `spawn_watchdog()` 只置 `daemon_dead`；`src/sandbox/ublk/device.rs` 的 `is_available()` 只返回 `self.client.is_some()`。
- A-12 / O-68 / D-19：`node_registry.go` 的 `Snapshot()` 只按 `lingeringIDs` 过滤，注释仍写「filtered by their derived status」；`service_test.go` 的 `TestScheduleOnlyConsidersReadyNodes` 只构造 active 与 lingering 两个节点。
- O-01：`oss/repository.rs` 的 `delete()` 不触及 `managed-layers/`，两处注释写「require separate GC」；POSIX catalog 的删除只移除 record、alias、commit 标记与日志。
- C-20：`bind_alias()` 以 `MAX_ALIAS_BIND_ATTEMPTS = 5` 做读-写-回读。
- C-11：`SnapshotRecord::mark_committed()` 不检查原状态，直接把模板构建置为 Ready。
- S-01：`src/p2p/iroh/transport.rs` 以 `BlobsProtocol::new(&store, None)` 注册 blobs 协议。
- S-10：daemon 的 metrics 地址缺省 `0.0.0.0:9103`。
- O-10：`FirecrackerInstance::stop()` 忽略 kill 与 wait 的结果，恒返回 `Ok(())`。
- O-55、O-56：`OrchestratorError::InvalidTimeout` 与 `RecordingVerdict::Fail` 只在定义与 match 中出现，没有构造点。
- D-06：`storage/ublk/src/dev.rs` 的日志按 `UBLK_F_SUPPORT_ZERO_COPY` 判断，`ctrl.rs` 设置的是 `UBLK_F_AUTO_BUF_REG`。
- O-34、O-39：`src/cfg.rs` 的 `block_pool_config()` 恒写 `maintenance_enabled: false`；`UblkDaemonClient::shutdown()` 以 `let _ =` 丢弃 `Shutdown` RPC 的结果，再无上限地等待 `daemon_exited`。
- O-37：`services/shared/config/config.go` 的 `load()` 在给了路径而 `os.ReadFile` 失败时直接返回错误。
- D-09、D-11、D-13、D-18、D-24：分别对照 `p2p-design.md` 与 `src/p2p/transport.rs`、`CLAUDE.md` 的链接目标、`services/README.md` 与 `go.mod`、`snapshots/use.md`、`extra_drive.rs` 的比较方式。

---

## 9. 小结

- 正确性问题集中在两处近似原子：对象存储 catalog 用读-改-写加回读代替 CAS，生命周期用「先标记、再副作用、失败回滚」而回滚失败无人处理；两者的后果都是持久状态与实际不符，且在重启或并发交错之前没有信号。
- 影响面超出单台沙箱的三条可用性问题——Firecracker 调用无超时、ublk-daemon 无崩溃恢复、`Schedule()` 不排除 UNHEALTHY——都与「依赖坏了之后多久被发现」有关，修补方向分别是分级超时、可重建的 daemon 状态、让放置使用已有的状态推导。
- 「只增不减」是可运维性的主线：仓库层、builder 模板、P2P 发布、fork 与暂停目录、daemon 设备都有没有回收者的路径；仓库层不回收是有引用计数缺失作为理由的结构性取舍，代价是存储成本单调增长。
- 一个部署是一个信任域：单 API key 无租户，集群内节点、scheduler 与 P2P 对端互信，宿主防火墙被当作数据面鉴权的前提；开启 P2P 时，制品完整性取决于集群里最弱的节点。
- 构建链的主路径是钉住的，未固定的是旁路：protoc、Go 镜像、tools 盘镜像引用、安装脚本的校验来源；入库的生成代码没有漂移检查。
- 文档与注释的漂移多数指向旧设计；行为以代码为准，startup manifest 的称呼以 `AENVMF01` / 格式版本 4 为准。
- 220 条里有 45 条标「推论：」，是从代码结构推出、未经运行验证的假设，判断优先级之前应先复现。

---

## 延伸阅读 / 下一篇

- [第 65 篇 · 与 e2b infra 的对照（一）](65-vs-e2b-infra-architecture.md)、[第 66 篇 · 与 e2b infra 的对照（二）](66-vs-e2b-infra-storage-and-memory.md)：本篇许多取舍在 e2b infra 里有不同的答案。
- [第 67 篇 · AENV 补丁版 Firecracker 与 guest 内核](67-firecracker-patch-layer.md)：C-30、O-07 依赖的补丁行为，以及 B-18 至 B-20 涉及的内核与状态文件。
- [第 71 篇 · 配置项、环境变量与端口总表](71-config-env-ports-reference.md)：O-24 至 O-39 涉及的键与默认值。
- [第 73 篇 · 持久化制品与磁盘格式总表](73-artifacts-and-formats-reference.md)：各制品「谁删、有没有 GC」一栏与 §4.2 对应。
- [e2b 手册第 37 篇 · 暂停与快照](../e2b-infra/37-pause-and-snapshot.md)：同一类系统在暂停路径上的失败处理。
