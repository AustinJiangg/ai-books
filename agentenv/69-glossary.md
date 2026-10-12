# 69 · 术语表

> 本附录收录全书固定译法的术语（STYLE.md 第三节）与正文第 01–66 篇中反复出现的其它术语、类型名与格式名，每条给一句定义，并链到首次详细讲解它的篇目与小节。
> 术语按七个类别分组，组内按英文名或标识符的字母顺序排列。
>
> **读者**：读到一个陌生词、或想确认某个词在本书里的确切含义的读者。　**预备**：无。
> **代码**：本篇不引代码；各条的代码位置见所链篇目。

---

## 0. 本篇要回答的问题

1. 本书里一个术语的固定中文译法是什么，对应哪个英文词或代码标识符？
2. 它在 AgentENV v0.2.3 里指的是什么？
3. 想深入时应该读哪一篇的哪一节？

---

## 1. 怎样用这张表

「详讲」一栏指向**首次详细讲解**该术语的位置；一个术语在多处有不同侧面的展开时，最多再列一两处。
第一部分（02–07）是预备知识，一般概念（netns、io_uring、Firecracker 快照）链到那里；AgentENV 特有的机制链到正文篇目。
排序时忽略标识符前缀符号（`/`、`$`、反引号），大小写不敏感。

称谓有固定口径：「AgentENV」即 AgentENV v0.2.3；「AENV 补丁版 Firecracker」「上游 Firecracker v1.15.1」「Rust 版 overlaybd」「上游 overlaybd」「overlaybd 工具」「e2b infra」不混用（见 [STYLE.md](STYLE.md) 第二节）。
标为「AgentENV 扩展」的格式与上游 overlaybd 不兼容；兼容性的逐项依据见[第 73 篇 §5](73-artifacts-and-formats-reference.md#5-与上游-overlaybd-的兼容性对照)。

## 2. 虚拟化与 Firecracker

本组 28 条。

| 术语 | 英文 / 标识符 | 定义 | 详讲 |
|---|---|---|---|
| AENV 补丁版 Firecracker | AENV-patched Firecracker | kvcache-ai/firecracker tag `aenv-deps`：上游 Firecracker v1.15.1 之上 7 个提交，AgentENV 用到其中四个行为（可选 `mem_file_path`、脏页区间、seek 取内存文件大小、drive `direct`）。 | [第 03 篇 §4](03-firecracker-for-agentenv.md#4-aenv-补丁版-firecracker-的四个被用到的行为)、[第 67 篇](67-firecracker-patch-layer.md) |
| balloon 设备 | balloon | guest 内的 virtio 内存气球，宿主经它请 guest 归还空闲页。 | [第 03 篇 §5](03-firecracker-for-agentenv.md#5-balloon-与-damon把内存还给宿主) |
| 内核命令行 | boot args | 冷启动时传给 guest 内核的参数串，由配置默认值、扩展 hook 与 API 的 `extraBootArgs` 拼成。 | [第 27 篇 §2.1](27-start-pause-resume-sequences.md#21-boot-args-的拼装) |
| CPU 模板 | CPU template | 向 guest 暴露的 CPUID / MSR 集合；快照记住了它，所以恢复节点必须能提供同一组特性。 | [第 03 篇 §6](03-firecracker-for-agentenv.md#6-cpu-模板与跨节点恢复)、[第 57 篇 §5.1](57-heartbeat-and-cpu-intersection.md#51-问题快照记住了-cpu) |
| DAMON | DAMON | Linux 的数据访问监视框架，可据冷热把宿主内存回收；本书在内存归还的语境下提到。 | [第 03 篇 §5](03-firecracker-for-agentenv.md#5-balloon-与-damon把内存还给宿主) |
| 脏页区间 | dirty memory ranges | AENV 补丁版 Firecracker 新增的 `GET /vm/dirty-memory-ranges` 返回的区间列表，每项给出 HVA、内存镜像偏移与长度；暂停时据此只写脏页。 | [第 42 篇 §2.2](42-memory-snapshot-over-ublk.md#22-dirtymemoryranges-的语义) |
| 脏页 | dirty page | 自上次快照以来被 guest 写过的内存页；KVM 的脏页位图与 File 后端私有映射下的 COW 页是两种判据。 | [第 03 篇 §2.3](03-firecracker-for-agentenv.md#23-脏页从哪里来)、[第 42 篇 §2.3](42-memory-snapshot-over-ublk.md#23-两种-vm-上的脏页) |
| O_DIRECT 盘 | drive `direct` | AENV 补丁版 Firecracker 给 drive 加的选项：以 `O_DIRECT` 打开后端文件，绕过宿主页缓存；可写盘用它，tools 盘不用。 | [第 26 篇 §6](26-sandbox-block-devices.md#6-o_direct哪些盘绕过宿主页缓存) |
| envd | envd | guest 内的代理进程，提供进程、文件系统等 API；AgentENV 随 tools 盘分发它。 | [第 28 篇 §3](28-mmds-and-envd.md#3-envdguest-里的代理人) |
| Executor | Executor | 宿主经 envd 在 guest 里执行命令的封装，缺省以 envd 默认用户运行。 | [第 28 篇 §6](28-mmds-and-envd.md#6-executor宿主在-guest-里的手) |
| File 内存后端 | File memory backend | 恢复快照时把内存文件 mmap 进 guest 的后端；AgentENV 让它指向 ublk 内存设备。 | [第 03 篇 §3.2](03-firecracker-for-agentenv.md#32-file-后端) |
| Firecracker 快照 | Firecracker snapshot | Firecracker 的 `vm_state` 状态文件加内存文件；区别于仓库里的已提交快照。 | [第 03 篇 §2](03-firecracker-for-agentenv.md#2-快照状态文件加内存) |
| Full 与 Diff 快照 | Full / Diff snapshot | Firecracker 的两种快照类型：Full 写全部内存，Diff 只写脏页。 | [第 03 篇 §2.2](03-firecracker-for-agentenv.md#22-full-与-diff) |
| 客户机 / 宿主机 | guest / host | microVM 内部与运行它的物理（或虚拟）机器；首次出现后用英文。 | [第 02 篇 §4](02-why-agentenv.md#4-为什么是-microvm) |
| 宿主虚拟地址 | HVA（host virtual address） | guest 内存在 Firecracker 进程地址空间里的地址；内存层的段映射把它存进 `moffset`。 | [第 42 篇 §2.4](42-memory-snapshot-over-ublk.md#24-区间到段映射moffset-存-hva) |
| `/init` 请求 | `/init` | 宿主在 guest 就绪后发给 envd 的初始化请求，下发访问令牌、环境变量等；每次启动（含 resume）都发。 | [第 28 篇 §4.2](28-mmds-and-envd.md#42-init-的内容) |
| jailer | jailer | Firecracker 自带的隔离启动器；AgentENV 不用它，改为自己进入 netns 并清空能力。 | [第 25 篇 §5](25-backend-and-firecracker-process.md#5-不用-jailer哪些隔离有哪些没有) |
| KVM | KVM | Linux 内核的硬件辅助虚拟化接口，缺省的虚拟化模式。 | [第 61 篇 §2.1](61-pvm.md#21-virtualizationmode) |
| 微型虚拟机 | microVM | 只带最少设备模型的轻量虚拟机，沙箱的隔离单位。 | [第 02 篇 §4](02-why-agentenv.md#4-为什么是-microvm) |
| MMDS | MMDS | Firecracker 的元数据服务；AgentENV 用它向 guest 带外传递沙箱身份与源镜像配置。 | [第 28 篇 §2](28-mmds-and-envd.md#2-mmds带外的身份) |
| 跨进程读内存 | `process_vm_readv` / `ProcessVmReader` | 从 Firecracker 进程地址空间按 HVA 读脏页的系统调用及其封装，暂停时用它把脏页写成层。 | [第 42 篇 §2.5](42-memory-snapshot-over-ublk.md#25-processvmreader-与-compact_to) |
| PVM | PVM | 不依赖硬件嵌套虚拟化的半虚拟化方案，用于宿主本身是虚拟机的场合；需要另一套 Firecracker 与内核。 | [第 61 篇](61-pvm.md) |
| 快照兼容域 | snapshot compatibility domain | 快照记下的虚拟化模式等属性；模式不符的快照不能在本节点恢复。 | [第 61 篇 §5](61-pvm.md#5-快照兼容域) |
| tools 盘 | tools drive | 每台沙箱都挂的只读盘，装 envd、busybox 与 `/init` 脚本，版本钉在快照上。 | [第 26 篇 §7](26-sandbox-block-devices.md#7-tools-盘的来源与版本) |
| Uffd 内存后端 | Uffd memory backend | 恢复快照时由外部进程经 userfaultfd 回答缺页的后端；AgentENV 保留实现但不用。 | [第 03 篇 §3.1](03-firecracker-for-agentenv.md#31-uffd-后端)、[第 44 篇](44-uffd-alternative.md) |
| userfaultfd | userfaultfd（uffd） | Linux 把缺页交给用户态处理的机制。 | [第 44 篇 §2.2](44-uffd-alternative.md#22-握手) |
| 虚拟化模式 | virtualization mode | 配置键选择的 KVM 或 PVM，决定下载哪套 Firecracker、内核与 tools 盘。 | [第 61 篇 §2](61-pvm.md#2-一个配置键三样制品) |
| VM 状态文件 | `vm_state` | Firecracker 快照中的设备与 vCPU 状态文件，仓库里存为 `vm_state.bin`。 | [第 03 篇 §2.1](03-firecracker-for-agentenv.md#21-两个文件) |

## 3. 存储

本组 49 条。

| 术语 | 英文 / 标识符 | 定义 | 详讲 |
|---|---|---|---|
| AsyncIoRing | `AsyncIoRing` | 以 slab key 作 `user_data` 的 io_uring 异步封装，ublk 库的数据面基础。 | [第 40 篇 §5](40-ublk-library.md#5-asyncioring-与取消安全) |
| 后台下载 | background download | 把远端层整段拉进节点块缓存的调度器任务，与前台缺块读共用位图。 | [第 39 篇 §5](39-block-cache-and-background-download.md#5-后台下载调度器) |
| 节点块缓存 | block cache | 远端层按块落在节点磁盘上的缓存，带位图与 `meta.bin`（魔数 `OBCH`），双水位按条目 LRU 驱逐。 | [第 39 篇 §2](39-block-cache-and-background-download.md#2-缓存在读链上的位置与条目组织) |
| cache_fd | `cache_fd` | 节点为共享只读设备保留的一个打开句柄，防止最后一个打开者关闭时内核清掉块设备页缓存。 | [第 26 篇 §4.4](26-sandbox-block-devices.md#44-cache_fd保住页缓存的那个打开者) |
| 压实 | compact | 按合并后的映射把多层重写成一层；首次出现后可用 compact。 | [第 37 篇 §4](37-seal-restack-compact.md#4-compact按映射重写成单层) |
| ublk-daemon | daemon（`uvm-ublk-daemon`） | 持有全部 ublk 设备的独立进程，经 Unix socket RPC 为 `server` 建删设备、restack、写内存层。 | [第 41 篇](41-ublk-daemon.md) |
| discard | discard | 块设备的「这段不再需要」请求，Rust 版 overlaybd 记为零映射。 | [第 36 篇 §5](36-read-write-paths-and-rw-layouts.md#5-discard) |
| 下载准入 | `download_gate` | 节点级的前台 / 后台下载准入闸门，envd 就绪前压住后台下载。 | [第 39 篇 §6.1](39-block-cache-and-background-download.md#61-download_gate) |
| 附加盘 | extra drive | 冷启动时随沙箱创建的块设备，生命期随沙箱。 | [第 31 篇 §2](31-extra-drives-and-volumes.md#2-两类盘附加盘与卷) |
| 首触页 | first-touch page | 恢复后 guest 第一次访问的内存页，按访问顺序录成 trace。 | [第 43 篇 §2](43-startup-pack-and-prefetch.md#2-录制一台一次性的-vm) |
| Hybrid 布局 | hybridLogStructured | 可写层布局之一：能原地覆盖就原地写，否则追加；header flags bit5，与上游默认分支同位同义，是 AgentENV 的缺省。 | [第 36 篇 §4.3](36-read-write-paths-and-rw-layouts.md#43-hybrid能原地就原地不能就追加)、[第 34 篇 §6](34-lsmt-format-and-index.md#6-与上游的兼容边界) |
| 镜像配置 | `image.json` | 描述一个 overlaybd 镜像的 lower 列表与 upper 的配置文件，Rust 版 overlaybd 据它装配层栈。 | [第 36 篇 §2.1](36-read-write-paths-and-rw-layouts.md#21-从-imagejson-到-imagefile) |
| ImageFile | `ImageFile` | Rust 版 overlaybd 中一个打开的镜像：层栈、读写入口与 restack。 | [第 36 篇 §2](36-read-write-paths-and-rw-layouts.md#2-层栈装配) |
| io_uring | io_uring | Linux 的提交队列 / 完成队列异步 I/O 接口。 | [第 04 篇 §2](04-io-uring-and-ublk.md#2-io_uring两个环与一个-user_data) |
| jump table | jump table | ZFile 里记录每个压缩块偏移的两级表。 | [第 35 篇 §4](35-zfile-compression.md#4-jump-table两级偏移) |
| 层 / 层栈 | layer / layer stack | overlaybd 的一层是一个 LSMT 文件；多层按顺序叠成层栈，上层覆盖下层。 | [第 05 篇 §2.2](05-overlaybd-and-lazy-loading.md#22-lsmt每层一个文件多层一张索引)、[第 36 篇 §2](36-read-write-paths-and-rw-layouts.md#2-层栈装配) |
| 运行时层数预算 | layer budget | 限制运行时层栈深度的公式（缺省上限 32 减去稳定前缀层数的四分之一），超出时触发 compact。 | [第 37 篇 §5](37-seal-restack-compact.md#5-运行时层数预算) |
| 按需加载 | lazy loading（on-demand loading） | 只在读到时才从远端取对应的块，而不是先下载整个镜像。 | [第 05 篇 §2.4](05-overlaybd-and-lazy-loading.md#24-按需加载) |
| LogStructured 布局 | LogStructured | 可写层布局之一：数据与映射都只追加。 | [第 36 篇 §4.1](36-read-write-paths-and-rw-layouts.md#41-logstructured追加数据追加映射) |
| 下层 / 可写层 | lower / upper | 层栈中的只读层与唯一的可写层；首次出现后可用英文。 | [第 34 篇 §3](34-lsmt-format-and-index.md#3-四种层文件形态) |
| LSMT | LSMT | overlaybd 的层文件格式：数据区加段映射索引，头尾为 `HeaderTrailer`，与上游兼容。 | [第 34 篇](34-lsmt-format-and-index.md) |
| 内存层 | memory layer | 内存快照对应的 overlaybd 层：脏页数据加以 HVA 为 `moffset` 的段映射。 | [第 42 篇 §2.6](42-memory-snapshot-over-ublk.md#26-压到层栈上) |
| 块缓存元数据 | `OBCH`（`meta.bin`） | 节点块缓存条目的元数据文件魔数，AgentENV 扩展。 | [第 39 篇 §4.3](39-block-cache-and-background-download.md#43-metabin-与崩溃语义) |
| overlaybd | overlaybd | 以块设备形式按需读容器镜像的分层格式与实现；本书区分 Rust 版 overlaybd、上游 overlaybd 与 overlaybd 工具三个称谓。 | [第 05 篇 §4.1](05-overlaybd-and-lazy-loading.md#41-谁做什么) |
| overlaybd 工具 | overlaybd tools | kvcache-ai/overlaybd 发布的 `overlaybd-create/apply/commit/resize` 二进制，用于离线转换与扩容。 | [第 05 篇 §4.1](05-overlaybd-and-lazy-loading.md#41-谁做什么)、[第 41 篇 §5.2](41-ublk-daemon.md#52-为什么扩容要调-c-工具) |
| OverlaybdTarget | `OverlaybdTarget` | ublk 库里把块请求接到 `ImageFile` 的 target 实现。 | [第 40 篇 §7](40-ublk-library.md#7-overlaybdtarget) |
| 页缓存 | page cache | 内核块设备 / 文件页缓存；共享只读设备靠它在多台 VM 间去重。 | [第 04 篇 §4.4](04-io-uring-and-ublk.md#44-块设备的页缓存)、[第 42 篇 §4.3](42-memory-snapshot-over-ublk.md#43-页缓存即去重) |
| 预合并索引缓存 | `PMIDX001` | 把多层合并后的索引落盘复用的缓存文件格式，AgentENV 扩展。 | [第 34 篇 §5](34-lsmt-format-and-index.md#5-预合并索引缓存pmidx001) |
| 重叠层 | restack | 封存当前 upper、把它压到 lower 栈顶、换上新的空 upper；首次出现后用 restack。 | [第 37 篇 §3](37-seal-restack-compact.md#3-restack封存并换上新-upper) |
| ReuseZero | `ReuseZero` | Hybrid 写入的一类 fragment：把数据写进 zeroed 映射保留的物理段；Rust 版 overlaybd 独有。 | [第 36 篇 §4.3](36-read-write-paths-and-rw-layouts.md#43-hybrid能原地就原地不能就追加) |
| 运行时物化 | runtime materialization | daemon 在沙箱工作目录里生成运行时镜像（复制配置、准备 upper、按需扩容）再建设备的过程。 | [第 41 篇 §5](41-ublk-daemon.md#5-运行时物化)、[第 26 篇 §5.1](26-sandbox-block-devices.md#51-运行时物化) |
| RuntimeDispatchFile | `RuntimeDispatchFile` | 把 `VirtualFile` 操作派发到固定 tokio runtime 的装饰器，解决多 runtime 下的 I/O 归属问题。 | [第 38 篇 §4.3](38-virtualfile-chain-and-remote-io.md#43-runtimedispatchfile) |
| Rust 版 overlaybd | Rust overlaybd | AgentENV 仓库内的 `storage/overlaybd` crate，用 Rust 重写的 overlaybd 在线数据面。 | [第 05 篇 §4](05-overlaybd-and-lazy-loading.md#4-上游-overlaybd-与-agentenv-的分工) |
| 封存 | seal | 把可写层原地封口成只读层：写 index 与 trailer，不复制数据。 | [第 37 篇 §2](37-seal-restack-compact.md#2-seal原地封口) |
| 段映射 | segment mapping | LSMT 索引的单元：逻辑扇区区间到某层物理偏移（`moffset`）的映射。 | [第 34 篇 §2.2](34-lsmt-format-and-index.md#22-disksegmentmapping) |
| 共享只读设备 | shared read-only device | 多台沙箱共用的同一个只读 ublk 设备（如内存设备），由节点与 daemon 两级引用计数管理。 | [第 26 篇 §4](26-sandbox-block-devices.md#4-共享只读设备与两级引用计数)、[第 42 篇 §4](42-memory-snapshot-over-ublk.md#4-恢复一个只读设备n-台-vm) |
| Sparse 布局 | Sparse | 可写层布局之一：数据写到与逻辑偏移相同的物理位置。 | [第 36 篇 §4.2](36-read-write-paths-and-rw-layouts.md#42-sparse写到逻辑偏移) |
| startup manifest | startup manifest（`AENVMF01`） | 由首触页 trace 展开、写进仓库的预取清单（`memory-startup.pack`），AgentENV 扩展格式。 | [第 43 篇 §3](43-startup-pack-and-prefetch.md#3-两种格式trace-与-manifest) |
| 启动包 | startup pack | 首触页 trace 与 startup manifest 的统称；首次出现后可用英文。 | [第 43 篇](43-startup-pack-and-prefetch.md) |
| SwitchFile | `SwitchFile` | 读链上的装饰器，v0.2.3 中只负责识别 ZFile 并切到解压读。 | [第 38 篇 §3.3](38-virtualfile-chain-and-remote-io.md#33-tar-适配与-switchfile) |
| trace | trace（`AENVTRC1`） | startup pack 录制产出的首触页序列，只留在节点本地；与上游 trace prefetch 的格式不同。 | [第 43 篇 §3.1](43-startup-pack-and-prefetch.md#31-字节布局) |
| ublk | ublk | Linux 的用户态块设备框架：内核经 io_uring 透传命令把块请求交给用户态 server。 | [第 04 篇 §3](04-io-uring-and-ublk.md#3-ublk三个设备节点与控制面) |
| ublk 特性位 | `UBLK_F_*` | 内核 ublk 驱动报告的能力位，AgentENV 看其中三个决定行为。 | [第 04 篇 §5.1](04-io-uring-and-ublk.md#51-agentenv-看的三个特性位) |
| 上游 overlaybd | upstream overlaybd | containerd/overlaybd（C++），本书只在核实格式兼容时提到。 | [第 05 篇 §4.2](05-overlaybd-and-lazy-loading.md#42-格式兼容的边界) |
| 透传命令 | `URING_CMD` | io_uring 把任意命令交给驱动的操作码，ublk 的控制面与数据面都用它。 | [第 04 篇 §2.3](04-io-uring-and-ublk.md#23-透传命令uring_cmd) |
| VirtualFile | `VirtualFile` | Rust 版 overlaybd 的文件抽象 trait；本地、tar、ZFile、registry、OSS、缓存都是它的实现或装饰器。 | [第 38 篇 §2](38-virtualfile-chain-and-remote-io.md#2-virtualfile-trait) |
| 卷 | volume | 持久块存储，可挂到多个沙箱；权威在快照仓库，本地是缓存。 | [第 31 篇 §6](31-extra-drives-and-volumes.md#6-volumemanager权威在仓库本地是缓存)、[第 16 篇 §5](16-snapshot-and-volume-api.md#5-卷对象) |
| 卷槽位 | volume slot | 冷启动时预留的 virtio-blk 设备，恢复后用来热插卷。 | [第 31 篇 §3](31-extra-drives-and-volumes.md#3-设备命名与槽位) |
| ZFile | ZFile | overlaybd 的分块压缩文件格式，带 jump table 支持随机读，与上游兼容。 | [第 35 篇](35-zfile-compression.md) |

## 4. 快照与镜像

本组 29 条。

| 术语 | 英文 / 标识符 | 定义 | 详讲 |
|---|---|---|---|
| 快照镜像导出工具 | `aenv-snapshot-image` | 把已提交快照的 rootfs 发布为 overlaybd-native OCI 镜像的离线工具。 | [第 50 篇 §3](50-rootfs-as-oci-image.md#3-离线导出aenv-snapshot-image) |
| 别名 | alias | 指向快照 id 的名字（如模板名），存于仓库 catalog。 | [第 48 篇 §6.1](48-object-storage-repository.md#61-alias读-写-回读) |
| 制品 | artifact | 快照的组成文件：vm_state、manifest、层、startup manifest 等。 | [第 46 篇 §4](46-snapshot-object-model.md#4-一个快照的制品) |
| builder 模板 | BuildKit builder template | 运行 buildkitd 的模板，构建时从它热启动 builder VM。 | [第 53 篇 §3](53-buildkit-in-microvm.md#3-builder-模板) |
| 缓存种子 | cache seed | BuildKit 缓存的只读卷；后续构建从仓库里的头指针派生工作卷。 | [第 53 篇 §5](53-buildkit-in-microvm.md#5-缓存种子) |
| 捕获 | capture | 把运行中 VM 的内存、设备状态与盘写成产物的过程；pause、snapshot、fork 共用一段代码。 | [第 27 篇 §6](27-start-pause-resume-sequences.md#6-capture-与-pause同一段代码四种收尾) |
| catalog | catalog | 仓库里的记录与别名目录；POSIX 后端用锁文件，对象存储后端用读-写-回读。 | [第 47 篇 §2](47-posix-repository.md#2-目录布局)、[第 48 篇 §6](48-object-storage-repository.md#6-没有-cas-时的-catalog) |
| 已提交载荷 | `CommittedSnapshot` | 已提交快照记录中恢复所需的全部逻辑信息，不含节点本地路径。 | [第 46 篇 §2.3](46-snapshot-object-model.md#23-committedsnapshot恢复需要的全部逻辑信息) |
| fork | fork | 从一台运行中的沙箱在同节点分叉出多台，共享只读内存设备与层。 | [第 51 篇](51-fork.md) |
| 持有者 | hold | image-cache 中保护 commit 不被 GC 的引用，分 operation、runtime、paused 三个命名空间。 | [第 45 篇 §5.3](45-oci-to-overlaybd.md#53-三类持有者) |
| 节点镜像缓存 | image-cache | 节点本地存放 OCI 转换结果的缓存，带元数据图、三类持有者与 fail-closed GC。 | [第 45 篇 §5](45-oci-to-overlaybd.md#5-节点本地的-image-cache) |
| lease | lease | 本地制品缓存发给一次启动的租约，只覆盖启动窗口。 | [第 49 篇 §6.2](49-resolve-and-artifact-cache.md#62-lease-只覆盖启动窗口) |
| 本地制品缓存 | `LocalArtifactCache` | 对象存储后端在节点上缓存小制品（vm_state、manifest 等）的组件。 | [第 49 篇 §6](49-resolve-and-artifact-cache.md#6-localartifactcache) |
| 托管层 | `managed-layers/` | 仓库里按 digest 命名的层存放位置；两种后端都不回收。 | [第 47 篇 §3.2](47-posix-repository.md#32-导入层按-lower-的形态分流)、[第 48 篇 §7](48-object-storage-repository.md#7-不回收的层) |
| 快照 manifest | manifest（`firecracker-manifest.json`） | 快照的形状信息（设备、内存、盘），不含节点本地路径。 | [第 46 篇 §3](46-snapshot-object-model.md#3-manifest形状进仓库路径留在节点) |
| OCI 镜像 | OCI image | 标准容器镜像（manifest + tar 层）；AgentENV 逐层转换成 overlaybd 层。 | [第 05 篇 §3.2](05-overlaybd-and-lazy-loading.md#32-标准-oci逐层转换)、[第 45 篇 §4](45-oci-to-overlaybd.md#4-标准-oci逐层转换) |
| overlaybd-native 镜像 | overlaybd-native image | 层本身已是 overlaybd 格式的 OCI 镜像，可直接远端按需读，不下载 blob。 | [第 05 篇 §3.1](05-overlaybd-and-lazy-loading.md#31-overlaybd-native直接读远端层)、[第 45 篇 §3](45-oci-to-overlaybd.md#3-overlaybd-native不下载任何-blob) |
| 暂停沙箱产物 | persisted sandbox | 暂停沙箱的记录与产物，存在 `$AENV_HOME/persisted-sandboxes`，只能在原节点恢复。 | [第 22 篇 §3.3](22-persistence-across-restarts.md#33-产物目录) |
| 发布 | publish | 把捕获产物导入快照仓库并写入记录的提交协议。 | [第 47 篇 §3](47-posix-repository.md#3-publish导入然后提交)、[第 48 篇 §3](48-object-storage-repository.md#3-publish编号的七步) |
| 重封装 | recontainerize | 发布时把本地 raw 层封装成 ZFile 再上传。 | [第 35 篇 §7.1](35-zfile-compression.md#71-本地-raw发布时压缩) |
| referrers | referrers | OCI 的引用查询接口，用来给标准镜像找对应的 overlaybd 加速层。 | [第 45 篇 §2.4](45-oci-to-overlaybd.md#24-referrers给标准镜像找加速层) |
| regctl | regctl | 外部 registry 命令行工具，AgentENV 用它取 manifest 与推送镜像。 | [第 45 篇 §6](45-oci-to-overlaybd.md#6-调用-regctl-的两条约束) |
| resolve | resolve | 把仓库记录变成节点上可运行的 `RunnableSnapshot`：定位制品、物化 `image.json`。 | [第 49 篇](49-resolve-and-artifact-cache.md) |
| 可运行快照 | `RunnableSnapshot` | 带节点本地路径、可直接交给后端启动的快照。 | [第 46 篇 §2.5](46-snapshot-object-model.md#25-runnablesnapshot) |
| 快照 | snapshot | 仓库里的已提交快照：一条记录加一组制品；区别于 Firecracker 的快照文件。 | [第 46 篇 §2](46-snapshot-object-model.md#2-记录已提交载荷与可运行快照) |
| 快照仓库 | snapshot repository | POSIX 或对象存储后端，快照的持久真相。 | [第 46 篇 §5](46-snapshot-object-model.md#5-三层存储)、[第 47 篇](47-posix-repository.md)、[第 48 篇](48-object-storage-repository.md) |
| SnapshotManager | `SnapshotManager` | 仓库与运行时缓存之上的一层薄门面。 | [第 46 篇 §6](46-snapshot-object-model.md#6-snapshotmanager一层薄门面) |
| 模板 | template | source = Template 的快照记录，可带构建状态。 | [第 15 篇 §2](15-template-build-api.md#2-模板即快照记录)、[第 46 篇 §2.2](46-snapshot-object-model.md#22-来源与模板状态) |
| 模板构建器 | template builder | 在构建 VM 里逐步执行命令、最后捕获并发布模板的组件。 | [第 52 篇](52-template-builder.md) |

## 5. 编排与 API

本组 31 条。

| 术语 | 英文 / 标识符 | 定义 | 详讲 |
|---|---|---|---|
| 部署级 API key | API key | 控制面请求携带的部署级密钥，常数时间比较。 | [第 13 篇 §2](13-authentication.md#2-部署级-api-key) |
| 驱逐 | auto-eviction（eviction） | TTL 到期后由回收任务执行 pause 或 delete。 | [第 23 篇 §4](23-auto-eviction-and-ttl.md#4-回收任务) |
| 自动恢复 | auto-resume | 数据面请求命中暂停沙箱时，反向代理先把它恢复再转发。 | [第 17 篇 §4](17-reverse-proxy.md#4-自动恢复) |
| 取消安全 | cancellation safety | future 在任意 `await` 点被丢弃时不留下不一致状态的性质；orchestrator 把操作 spawn 出去以免随请求一起死。 | [第 07 篇 §5](07-rust-async-primer.md#5-取消与取消安全)、[第 19 篇 §6](19-state-machine-and-concurrency.md#6-取消安全操作不随请求一起死) |
| CAS | compare-and-swap | 元数据存储上「状态等于期望值才转换」的原子原语，所有状态转换经它。 | [第 19 篇 §4](19-state-machine-and-concurrency.md#4-cas-原语) |
| 冷启动 | cold start | 从 OCI 镜像而不是快照启动 VM（`/sandboxes-cold` 与模板构建用）。 | [第 14 篇 §3.4](14-sandbox-api.md#34-冷启动-sandboxes-cold)、[第 27 篇 §3](27-start-pause-resume-sequences.md#3-冷启动的配置序列) |
| connect | connect | 一个端点覆盖「已运行则连上、已暂停则拉起」。 | [第 14 篇 §5](14-sandbox-api.md#5-connect一个端点覆盖连上或拉起) |
| 控制面 / 数据面 | control plane / data plane | 控制面是带 API key 的管理请求；数据面是送进 guest 的流量，用沙箱级 token。 | [第 13 篇 §4.1](13-authentication.md#41-控制面还是数据面) |
| 自定义扩展 | custom extension | 可选的外部 HTTP 服务，经四个 hook 跟随沙箱生命周期；首次出现后可用英文。 | [第 33 篇 §2](33-custom-extension-hooks.md#2-契约四个-hook) |
| 删除进度 | `DeleteProgress` | 删除操作可重入的进度记录，捕获、停止、释放分步推进。 | [第 21 篇 §3](21-deletion-and-volume-capture.md#3-deleteprogress可重入的进度) |
| E2B 兼容 | E2B compatibility | 让 E2B SDK 可以直接指向 AgentENV 的 API 形状与行为；偏差逐项列在矩阵里。 | [第 18 篇](18-e2b-compatibility.md) |
| 冻结 | freeze（`fsfreeze`） | 删除时在 guest 里冻结卷的文件系统，使封存下来的 upper 干净且不再有写入。 | [第 21 篇 §4.1](21-deletion-and-volume-capture.md#41-为什么是冻结) |
| 沙箱句柄 | handle（sandbox handle） | orchestrator 句柄表里指向活着 VM 的对象；回滚按句柄身份只撤销自己的东西。 | [第 20 篇 §4.2](20-launch-plan-and-rollback.md#42-句柄身份只回滚自己的东西) |
| hook guard | hook guard | 把一个运行时实例的扩展 hook 生命周期包成 RAII 的对象：先记实例 id 再发 start，保证 stop 能配对。 | [第 33 篇 §4.2](33-custom-extension-hooks.md#42-guard先记-id再发请求) |
| launch plan | `LaunchPlan` | 冷启动与恢复共用的启动流水线描述，分阶段带检查点与回滚。 | [第 20 篇 §2](20-launch-plan-and-rollback.md#2-launchplan一条流水线两种计划) |
| 生命周期事件 | lifecycle event | orchestrator 发布的 Create 等五类沙箱事件，订阅者是 guest 指标采样任务与心跳上报器。 | [第 24 篇 §4](24-metrics-and-events.md#4-生命周期事件) |
| orchestrator | `Orchestrator` | 节点内的沙箱状态机与操作编排者，持有元数据存储、句柄表与路由表。 | [第 10 篇 §4.1](10-node-process-and-object-model.md#41-orchestrator-的字段) |
| 暂停状态 | `PausedSandboxState` | 后端交给 orchestrator 的不透明暂停状态 trait 对象。 | [第 10 篇 §4.4](10-node-process-and-object-model.md#44-pausedsandboxstate不透明的暂停状态) |
| 持久化器 | persister | 把暂停沙箱的记录写进 RocksDB 并在重启时 `load_all()` 的组件。 | [第 22 篇 §2](22-persistence-across-restarts.md#2-持久化器接口) |
| 可恢复 / 终止错误 | `Recoverable` / `Terminal` | 捕获错误的两类：前者保证 VM 已恢复运行，后者表示 VM 已被改动、不能再当作可运行。 | [第 20 篇 §7.1](20-launch-plan-and-rollback.md#71-两类错误的约定) |
| 两阶段 resume 标记 | resuming marker | resume 前把持久记录改成 Resuming，重启时据此丢弃半途的恢复。 | [第 22 篇 §5](22-persistence-across-restarts.md#5-两阶段-resume-标记) |
| 反向代理 | reverse proxy | 节点内 `/proxy` 与 Host 路由入口，以及多节点的 gateway，把数据面流量转进 guest。 | [第 17 篇](17-reverse-proxy.md) |
| 运行时路由表 | route table | orchestrator 维护的沙箱 id 到上游地址映射，`/init` 之后才发布。 | [第 17 篇 §3.1](17-reverse-proxy.md#31-运行时路由表) |
| 沙箱 | sandbox | 一台 microVM 及其附属资源（netns 槽位、块设备、进程）；API 与代码里的 sandbox。 | [第 25 篇 §3](25-backend-and-firecracker-process.md#3-firecrackersandbox一份资源清单) |
| 沙箱级 token | sandbox token（envd / traffic access token） | 以部署级 seed 为密钥、对沙箱 id 做 HMAC 派生的无状态凭据，不落盘。 | [第 13 篇 §3](13-authentication.md#3-沙箱级-token无状态派生) |
| 实例身份 | `SandboxInstanceId` | 同一沙箱每次运行时实例的 id，用于让 stop hook 与 start 配对。 | [第 33 篇 §4](33-custom-extension-hooks.md#4-实例身份sandboxinstanceid-与-hook-guard) |
| 沙箱状态 | `SandboxState` | 八个状态：Creating、Resuming、Running、Snapshotting、Forking、Pausing、Paused、Killing；只有 Running 与 Paused 稳定。 | [第 19 篇 §2](19-state-machine-and-concurrency.md#2-八个状态) |
| 规范驱动 | spec-driven server | 由 `openapi.yml` 生成 trait 与 handler、手写实现填进去的服务骨架。 | [第 12 篇 §2](12-spec-driven-server.md#2-生成管线) |
| 状态折叠 | state folding | 对外 API 把八个内部状态折成 running / paused 两个。 | [第 14 篇 §8.1](14-sandbox-api.md#81-八个状态折成两个) |
| 过期时间 | TTL / timeout | 沙箱的存活时长与到期动作；正文写 TTL，API 字段名照写 `timeout`。 | [第 23 篇 §2](23-auto-eviction-and-ttl.md#2-ttl-的数据表示) |
| 预热池 | warm pool | 提前备好与身份无关的资源（网络槽位、块设备、Firecracker 进程），按水位补充。 | [第 32 篇 §2](32-warm-pools.md#2-通用实现warmpool) |

## 6. 网络

本组 13 条。

| 术语 | 英文 / 标识符 | 定义 | 详讲 |
|---|---|---|---|
| /31 与 link-local | `/31`, link-local | `/31` 用于 veth 点对点链路；guest 与 tap 之间固定用 link-local 段 `169.254.0.20/30`，所有槽位相同，是快照 ABI 的一部分。 | [第 06 篇 §3.3](06-netns-iptables-transparent-proxy.md#33-31-与-link-local-地址)、[第 29 篇 §2.3](29-network-slots.md#23-为什么-vm-地址必须固定) |
| conntrack | conntrack | 内核的连接跟踪表，状态匹配与 NAT 依赖它。 | [第 06 篇 §4.4](06-netns-iptables-transparent-proxy.md#44-conntrack-与状态匹配) |
| 出站策略 | egress policy | 每个沙箱的出站规则（CIDR 与域名的放行 / 拒绝，加未命中时的缺省去向），`SandboxNetworkPolicy` 表示。 | [第 30 篇 §2](30-egress-policy-and-proxy.md#2-策略对象与-api-映射) |
| iptables | iptables / netfilter | 内核包过滤框架及其规则工具；槽位规则用 `iptables-restore` 原子提交。 | [第 06 篇 §4](06-netns-iptables-transparent-proxy.md#4-netfilter-与-iptables)、[第 29 篇 §4.3](29-network-slots.md#43-iptables-的提交方式) |
| 地址转换 | NAT | 改写包的源或目的地址；槽位在命名空间里用 SNAT / DNAT 在固定的 VM 地址与每槽位唯一的 host interaction IP 之间转换。 | [第 06 篇 §4.3](06-netns-iptables-transparent-proxy.md#43-地址转换) |
| 网络命名空间 | netns（network namespace） | 内核隔离网络栈的单位，每个槽位一个。 | [第 06 篇 §2](06-netns-iptables-transparent-proxy.md#2-网络命名空间) |
| NetworkManager | `NetworkManager` | 槽位的分配、复用与清理单例。 | [第 29 篇 §5](29-network-slots.md#5-networkmanager分配复用与清理) |
| REDIRECT | REDIRECT / `SO_ORIGINAL_DST` | 把连接改送本机端口的 iptables 目标；代理再用 `SO_ORIGINAL_DST` 取回原目的地。 | [第 06 篇 §5.1](06-netns-iptables-transparent-proxy.md#51-redirect-之后原目的地在哪里) |
| 槽位 | slot | 网络槽位：一个预建的 netns 加 tap、veth 与规则；块设备语境下另有卷槽位。 | [第 29 篇 §4](29-network-slots.md#4-创建一个槽位) |
| Host 与 SNI | SNI / Host | 透明代理从 HTTP Host 头或 TLS SNI 读出域名，按域名授权。 | [第 06 篇 §5.2](06-netns-iptables-transparent-proxy.md#52-看见域名host-与-sni) |
| tap | tap | 一端是网卡、一端是文件描述符的虚拟接口，Firecracker 经它收发 guest 的包。 | [第 06 篇 §3.1](06-netns-iptables-transparent-proxy.md#31-tap一端是网卡一端是文件描述符) |
| 透明代理 | transparent proxy | guest 不知情时截住出站连接、按域名判定后转发的 egress 代理。 | [第 06 篇 §5](06-netns-iptables-transparent-proxy.md#5-透明代理)、[第 30 篇 §4](30-egress-policy-and-proxy.md#4-透明代理) |
| veth | veth | 跨命名空间的一对虚拟网卡，连接槽位与宿主。 | [第 06 篇 §3.2](06-netns-iptables-transparent-proxy.md#32-veth跨命名空间的一根网线) |

## 7. 控制面

本组 17 条。

| 术语 | 英文 / 标识符 | 定义 | 详讲 |
|---|---|---|---|
| 绑定 | binding | scheduler 里 sandbox → node 的映射，内存或 Redis 存储。 | [第 56 篇 §3](56-scheduler.md#3-绑定) |
| CPU 模板交集 | CPU template intersection | scheduler 对集群节点 CPU 特性求交，下发给节点作为冷启动的 CPU 模板。 | [第 57 篇 §5](57-heartbeat-and-cpu-intersection.md#5-cpu-模板交集) |
| EndpointSlice | EndpointSlice | Kubernetes 的服务端点对象，scheduler 的 kubernetes 发现模式据它找节点。 | [第 56 篇 §4.2](56-scheduler.md#42-kubernetes) |
| gateway | gateway | 多节点的无状态入口：认证分界、路由判定、反向代理与写绑定。 | [第 55 篇](55-gateway.md) |
| 心跳 | heartbeat | 节点定期向 scheduler 报告的节点快照，scheduler 据此推导节点状态。 | [第 57 篇 §3](57-heartbeat-and-cpu-intersection.md#3-心跳循环) |
| iroh | iroh | AgentENV P2P 制品传输使用的点对点库。 | [第 58 篇 §3](58-p2p-artifact-transport.md#3-iroh-后端) |
| 节点 | node | 运行 `server` 进程的一台宿主机。 | [第 08 篇 §2](08-system-architecture.md#2-单节点三类进程) |
| 节点快照 | node snapshot | 心跳携带的节点容量、沙箱名单与主机指标。 | [第 57 篇 §2](57-heartbeat-and-cpu-intersection.md#2-节点快照) |
| 节点状态 | `NodeStatus` | READY、CONNECTING、UNHEALTHY 等，由发现状态与心跳情况推导。 | [第 54 篇 §4](54-control-plane-overview.md#4-节点状态) |
| P2P 制品 | P2P key / descriptor / provider | P2P 传输的三个抽象：消费者编码的 key、查找结果 descriptor、本地或对等节点 provider。 | [第 58 篇 §2](58-p2p-artifact-transport.md#2-抽象keydescriptorprovider) |
| HTTP 门面 | P2P HTTP facade | 节点本地的 HTTP 服务，让 Rust 版 overlaybd 按范围读 P2P 制品。 | [第 58 篇 §5](58-p2p-artifact-transport.md#5-overlaybd-的-http-门面) |
| 放置 | placement | scheduler 为新沙箱选节点：资源过滤后按策略选择。 | [第 56 篇 §2](56-scheduler.md#2-放置) |
| primary 与 query-only | primary / query-only | scheduler 的两种角色：primary 维护节点表与放置，query-only 只从 Redis 查绑定。 | [第 56 篇 §6.1](56-scheduler.md#61-两种角色) |
| Redis | Redis | 绑定的可选持久存储，primary 与 query-only 共享。 | [第 56 篇 §3.3](56-scheduler.md#33-redis-实现) |
| 调度提示 | schedule hint | gateway 从创建请求提取的资源与模板信息，用于向 scheduler 要节点。 | [第 55 篇 §4](55-gateway.md#4-选节点) |
| scheduler | scheduler | 多节点的放置、绑定、节点注册与 HA 服务，提供 13 个 gRPC。 | [第 56 篇](56-scheduler.md)、[第 54 篇 §3](54-control-plane-overview.md#3-13-个-rpc) |
| 注销节点 | `UnregisterNode` | 节点关闭时先向 scheduler 注销、再暂停沙箱落盘的 RPC。 | [第 57 篇 §4.1](57-heartbeat-and-cpu-intersection.md#41-unregisternode) |

## 8. 工程

本组 20 条。

| 术语 | 英文 / 标识符 | 定义 | 详讲 |
|---|---|---|---|
| adev | `adev` | 仓库自带的开发与 CI 工具：codegen、coverage、mutants。 | [第 64 篇 §2.3](64-build-codegen-release.md#23-adev开发与-ci-工具) |
| 节点目录 | `$AENV_HOME` / `$AENV_RUNTIME` | 节点的持久目录（缺省 `/var/lib/aenv`）与运行期目录（缺省 `/run/aenv`）。 | [第 10 篇 §5](10-node-process-and-object-model.md#5-节点磁盘布局) |
| async_trait | `async_trait` / `?Send` | 让 trait 方法返回 boxed future 的宏；`?Send` 变体允许 `!Send` future。 | [第 07 篇 §3.2](07-rust-async-primer.md#32-async_trait-与-send) |
| 能力 | capability | Linux capability；常驻 `server` 只以「可委派」形式持有 `CAP_NET_ADMIN` 与 `CAP_SYS_ADMIN`。 | [第 59 篇 §5.2](59-host-setup-and-privileges.md#52-契约两项能力以可委派的形式持有)、[第 06 篇 §2.4](06-netns-iptables-transparent-proxy.md#24-需要哪些权限) |
| 配置单例 | `ConfigManager` | 用 `OnceLock` 持有的全局配置单例。 | [第 11 篇 §3.1](11-configuration.md#31-configmanager-与-oncelock) |
| DaemonSet | DaemonSet / preStop | Kubernetes 部署节点的方式；preStop 给关闭序列留出 3600 s。 | [第 60 篇 §5.2](60-deployment.md#52-节点-daemonset)、[第 60 篇 §5.3](60-deployment.md#53-prestop-与-3600-s) |
| 依赖清单 | `deps_manifest.toml` | 编进二进制的外部依赖版本表（Firecracker、内核、tools 盘、overlaybd 工具）。 | [第 01 篇 §3](01-repo-map-and-versions.md#3-外部依赖configdeps_manifesttoml)、[第 59 篇 §3.1](59-host-setup-and-privileges.md#31-manifest编进二进制的版本表) |
| 环境补齐 | `ensure_environment()` | 普通启动时对宿主只校验、对 `$AENV_HOME` 补齐依赖与配置的步骤。 | [第 10 篇 §2.4](10-node-process-and-object-model.md#24-ensure_environment校验加补齐) |
| 生成代码 | generated code | 由 `openapi.yml`、`firecracker.yaml`、`envd.yaml`、`scheduler.proto` 生成并入库的代码；讲行为时引用来源。 | [第 64 篇 §3](64-build-codegen-release.md#3-生成代码)、[第 01 篇 §5](01-repo-map-and-versions.md#5-生成代码) |
| linux-cap | `linux-cap` | 读取与委派 Linux 能力集合的小 crate。 | [第 59 篇 §5.4](59-host-setup-and-privileges.md#54-linux-cap-crate) |
| LocalSet | `LocalSet` / `spawn_local` | tokio 在单线程上运行 `!Send` 任务的机制。 | [第 07 篇 §2.2](07-rust-async-primer.md#22-localset-与-spawn_local) |
| 能力委托脚本 | `run-with-capabilities.sh` | 以委派能力运行需要特权的测试的脚本。 | [第 63 篇 §3](63-testing-and-benchmarks.md#3-能力委托run-with-capabilitiessh) |
| 运行时 | runtime | 两种语境：tokio runtime（调度并执行 future 的执行器），或「运行时目录 / 运行时层」（沙箱运行期产生的文件）。 | [第 07 篇 §2.3](07-rust-async-primer.md#23-一个进程里的多个-runtime)、[第 37 篇 §5.2](37-seal-restack-compact.md#52-预算公式) |
| Send 与 !Send future | `Send` / `!Send` future | 能否在线程间移动的 future；决定它能交给多线程 runtime 还是只能 `spawn_local`。 | [第 07 篇 §3](07-rust-async-primer.md#3-send-与-send-future) |
| 宿主准备 | `--setup-host` / `--setup-only` | `server` 的两种一次性模式：以 root 准备宿主，或只下载依赖与生成配置。 | [第 59 篇 §2](59-host-setup-and-privileges.md#2-三种模式的分工) |
| spawn_blocking | `spawn_blocking` | 把阻塞操作移到 tokio 阻塞线程池的接口。 | [第 07 篇 §4.2](07-rust-async-primer.md#42-spawn_blocking-的两个约束) |
| systemd 单元 | systemd unit | `install.sh` 生成的服务单元，以 `aenv` 用户与两项环境能力运行 `server`。 | [第 60 篇 §2.3](60-deployment.md#23-systemd-单元逐项) |
| tokio | tokio | Rust 的异步运行时；AgentENV 一个进程里有多个 runtime。 | [第 07 篇 §2](07-rust-async-primer.md#2-tokio-的执行模型) |
| tools 盘构建源 | `tools-image/` | 从 e2b infra 编译 envd、加 busybox 与 `/init` 生成 tools 盘镜像的构建目录。 | [第 64 篇 §5](64-build-codegen-release.md#5-tools-盘镜像) |
| Cargo workspace | Cargo workspace | 根 `Cargo.toml` 列出的 19 个成员 crate。 | [第 01 篇 §4.1](01-repo-map-and-versions.md#41-19-个成员) |

## 9. 容易混淆的几组词

| 词 | 区分 | 详讲 |
|---|---|---|
| 快照 / Firecracker 快照 | 前者是仓库里的已提交记录加制品；后者是 Firecracker 写出的 `vm_state` 与内存文件，是前者的一部分制品 | [第 46 篇 §2](46-snapshot-object-model.md#2-记录已提交载荷与可运行快照)、[第 03 篇 §2](03-firecracker-for-agentenv.md#2-快照状态文件加内存) |
| 暂停 / 快照 / fork | pause 把 VM 写成节点本地的暂停产物并停掉 VM；snapshot 在仓库里提交一份快照，VM 继续运行；fork 在同节点从一次捕获起多台 VM | [第 51 篇 §6](51-fork.md#6-pausesnapshotfork-对照) |
| 附加盘 / 卷 | 附加盘随沙箱生灭；卷独立存在、可跨沙箱挂载，删除沙箱时才把内容提交进仓库 | [第 31 篇 §2](31-extra-drives-and-volumes.md#2-两类盘附加盘与卷)、[第 21 篇 §1](21-deletion-and-volume-capture.md#1-问题删除是卷的提交点) |
| 槽位 | 网络槽位是一个 netns；卷槽位是冷启动时预留的 virtio-blk 设备 | [第 29 篇 §4](29-network-slots.md#4-创建一个槽位)、[第 31 篇 §3](31-extra-drives-and-volumes.md#3-设备命名与槽位) |
| runtime | tokio runtime 与「运行时目录 / 运行时层」两种语境，靠上下文区分 | [第 07 篇 §2.3](07-rust-async-primer.md#23-一个进程里的多个-runtime)、[第 37 篇 §5.2](37-seal-restack-compact.md#52-预算公式) |
| seal / restack / compact | seal 原地封口一层；restack 是 seal 加换新 upper；compact 把多层重写成一层 | [第 37 篇](37-seal-restack-compact.md) |
| trace / startup manifest | trace（`AENVTRC1`）只在节点本地；startup manifest（`AENVMF01`）由 trace 展开、写进仓库；与上游 trace prefetch 的 trace 是第三种格式 | [第 43 篇 §3](43-startup-pack-and-prefetch.md#3-两种格式trace-与-manifest)、[§5](43-startup-pack-and-prefetch.md#5-上游兼容的-trace-prefetch) |
| 块缓存 / image-cache / 本地制品缓存 | 块缓存存远端层的块；image-cache 存 OCI 转换产物；本地制品缓存存对象存储快照的小制品 | [第 39 篇](39-block-cache-and-background-download.md)、[第 45 篇 §5](45-oci-to-overlaybd.md#5-节点本地的-image-cache)、[第 49 篇 §6](49-resolve-and-artifact-cache.md#6-localartifactcache) |
| 反向代理 / 透明代理 | 反向代理把入站数据面流量送进 guest；透明代理截住 guest 的出站连接执行出站策略 | [第 17 篇](17-reverse-proxy.md)、[第 30 篇 §4](30-egress-policy-and-proxy.md#4-透明代理) |
| 控制面（请求类别）/ 控制面（gateway 与 scheduler） | 前者指带 API key 的管理请求，与数据面相对；后者指第八部分讲的多节点服务，靠上下文区分 | [第 13 篇 §4.1](13-authentication.md#41-控制面还是数据面)、[第 54 篇](54-control-plane-overview.md) |

---

## 10. 小结

- 全书的固定译法以 STYLE.md 第三节为准，本表在其上补充了正文中反复出现的类型名（`ImageFile`、`LaunchPlan`、`CommittedSnapshot` 等）与格式名（`PMIDX001`、`OBCH`、`AENVTRC1`、`AENVMF01`）。
- AENV 补丁版 Firecracker 的行为（脏页区间、可选 `mem_file_path`、drive `direct`、seek 取内存文件大小）不属于上游 Firecracker v1.15.1，条目里都标明了来源。
- `PMIDX001`、`OBCH`、`AENVTRC1`、`AENVMF01` 是 AgentENV 扩展；LSMT、ZFile 与上游兼容；Hybrid 布局与上游默认分支同位同义，只有 `ReuseZero` 是 Rust 版 overlaybd 独有。
- 「快照」默认指仓库里的已提交快照；「槽位」「runtime」「控制面」各有两义，第 9 节列出了区分方式。
- 每条的「详讲」只指向首次详讲位置；某个机制在后续篇目里的用法，从那一节的交叉链接继续读。

---

## 延伸阅读 / 下一篇

- [第 70 篇 · 代码地图：crate、模块与篇目](70-code-map.md)：按目录查实现文件与讲解篇目。
- [第 71 篇 · 配置项、环境变量与端口总表](71-config-env-ports-reference.md)、[第 72 篇 · 接口总表](72-api-reference.md)、[第 73 篇 · 持久化制品与磁盘格式总表](73-artifacts-and-formats-reference.md)：配置键、端点与格式的总表。
- [STYLE.md](STYLE.md) 第二、三节：称谓口径与术语固定译法的出处。
