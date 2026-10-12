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

条目来自第 01–66 篇正文中指出的问题，以及各篇编写时记下、要求本篇汇总的事项。汇总时做了三件事：

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

每条一行：**编号 | 现象 | 位置 | 后果 | 详讲**。位置写仓库相对路径与函数名；路径省略时与同一格里前一个路径相同。详讲链到对应篇的小节。
「位置」是定位用的入口，不保证列全所有调用点。重要条目在表外另有一小段，讲清楚后果的传播路径。

### 1.4 汇总

| 类别 | 条目数 | 表外重点条目 |
|---|---|---|
| 正确性 | 见 §2 | 对象存储仓库的弱一致 catalog；持久记录的两阶段标记 |
| 可用性 | 见 §3 | Firecracker REST 调用无超时；ublk-daemon 无崩溃恢复；`Schedule()` 不排除 UNHEALTHY |
| 可运维性 | 见 §4 | managed layers 无 GC |
| 安全与信任边界 | 见 §5 | P2P 信任边界；控制面 gRPC 无认证 |
| 供应链与构建 | 见 §6 | 生成代码无漂移检查 |
| 文档漂移 | 见 §7 | `docs/src/internals/*` 的几处主要偏差 |

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
| C-11 | `SnapshotRecord::mark_committed()` 不检查原状态 | `src/snapshot/types/snapshot.rs` | Error 状态的模板记录可直接变成 Ready | [第 46 篇 §2.2](46-snapshot-object-model.md#22-来源与模板状态) |
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
