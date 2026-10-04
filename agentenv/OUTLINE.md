# 全书大纲

本文件是这本书的**编写计划**：讲哪些主题、每篇写什么、面向谁、依赖哪些代码事实。
体例、术语与口径在 [`STYLE.md`](STYLE.md)；图的画法在 [`FIGURE-GUIDE.md`](FIGURE-GUIDE.md)；读者导览在 [`README.md`](README.md)。
本文件是给**编写者与维护者**看的。

---

## 一、全书结构

| 部 | 主题 | 篇目 | 面向 |
|---|---|---|---|
| 〇 | 导读 | 00–01 | 所有读者 |
| 一 | 预备知识 | 02–07 | 不熟悉 io_uring / ublk / overlaybd / 网络命名空间 / Rust 异步的读者 |
| 二 | 总体架构 | 08–11 | 所有读者；工程师必读 |
| 三 | API 层 | 12–18 | 工程师、SDK 使用者 |
| 四 | orchestrator：沙箱状态机 | 19–24 | 工程师 |
| 五 | 沙箱运行时 | 25–33 | 工程师；全书主线之一 |
| 六 | 存储：overlaybd 与 ublk | 34–44 | 工程师；全书核心 |
| 七 | 镜像、快照与模板 | 45–53 | 工程师；全书核心之二 |
| 八 | 分布式控制面 | 54–58 | 工程师、运维 |
| 九 | 部署与工程 | 59–64 | 运维、维护者 |
| 十 | 对照与延伸 | 65–68 | 本项目所有参与者 |
| 附录 | 术语表、代码地图、配置 / API / 制品总表 | 69–73 | 查阅 |

篇幅分配的依据（数据来自 v0.2.3 的 `git ls-files` + `wc -l`，含测试，不含生成代码约 2.6 万行）：
Rust 约 17.1 万行、Go 约 1.3 万行。按区域：`storage/overlaybd` 4.3 万、`src/sandbox` 2.1 万、`src/snapshot` 1.9 万、
`src/api` 1.1 万（另有 `openapi.yml` 3000 行）、`src/orchestrator` 1.2 万（其中测试 0.6 万）、`src/image` 1.0 万、
`crates/aenv` 1.0 万、`storage/ublk-daemon` 0.7 万、`storage/ublk` 0.4 万、`services/`（Go）1.3 万（其中测试约一半）、
`src/setup` 0.3 万、`src/template` 0.3 万、`src/p2p` 0.3 万。
存储（第六部分）按代码量占三成，给 11 篇；快照与镜像（第七部分）给 9 篇；Firecracker 补丁层只有约 +1000 行，
但它是内存快照路径成立的前提，给 1 篇并在第 03、42 篇中展开用法。

状态图例：`○` 未写　`◐` 草稿　`●` 完成　`◎` 已审校

---

## 二、代码基线与阅读位置

| 基线 | 位置 | 说明 |
|---|---|---|
| AgentENV v0.2.3 | `tmp/e2b-book-src/agentenv/` | kvcache-ai/AgentENV tag `v0.2.3`（commit `6cccaa7842bd`，2026-09-30）。clone 方法见 `tools/briefs/agentenv/WRITER-BRIEF.md`。main 在其后只有 5 个可观测性与 clippy 小修，不影响正文 |
| AENV 补丁版 Firecracker | `tmp/e2b-book-src/fc-aenv/` | kvcache-ai/firecracker tag `aenv-deps`（commit `90288c39`，发布资产名 `1.15.1-patch-v1`，即 `config/deps_manifest.toml` 的 `[firecracker.kvm]`）。clone 带 `upstream` 远端与 tag `v1.15.1`（commit `f82c0bd0`）。差异：`git -C tmp/e2b-book-src/fc-aenv diff v1.15.1 aenv-deps`（30 文件，+1219 −145，其中 `src/` 26 文件 +1018 −138）；提交：`git -C … log v1.15.1..aenv-deps`（7 个） |
| 上游 Firecracker v1.15.1 | 同上 clone 的 tag `v1.15.1` | 只在需要说明「上游原本怎样」时看。Firecracker 本身的机制不在本书展开，链接 Firecracker 手册 |
| e2b infra（对照） | `tmp/e2b-book-src/upstream/` | e2b-dev/infra tag `2026.09`（commit `f8c2f0cde`），即 e2b 手册的基线。**只在第 65、66 篇与各篇「与 e2b infra 的对照」短节里用**；优先读 e2b 手册对应篇，不够时才读代码 |
| 上游 overlaybd（对照） | `tmp/e2b-book-src/overlaybd-upstream/`（编写者自己 clone containerd/overlaybd，只读） | 只在需要核实「与上游 C++ 格式兼容」的论断时看（第 05、34、35 篇与附录 73） |
| overlaybd 工具 | GitHub kvcache-ai/overlaybd tag `static-v1.0.18-aenv.1` | AgentENV 只用它的 `overlaybd-create/apply/commit/resize` 二进制；本书不讲它的源码，只讲调用方式 |
| AgentENV 文档 | `tmp/e2b-book-src/agentenv/docs/src/` | mdBook 站点源码。**是参考，不是依据**；调研已发现多处与代码不符（见第 68 篇要点） |

所有路径相对于 `/home/austin/projects/e2b-repo/`。AgentENV 仓库内的路径（正文里引用的）相对于仓库根。

**不要**读 `/home/austin/projects/kvcache-ai/` 下的任何工作树（版本不确定），不要读 kvcache-ai/firecracker 的
`v1.15.1-patch`（= `v1.15.1-patch-v2`）、`v1.15.1-patch-nestedvirt`、`v1.16.1-patch` 分支作为基线 ——
它们只在第 67 篇作为「补丁栈的后续」各提一句。PVM 用的 kvcache-ai/firecracker-next 不在本书范围，第 61 篇只讲 AgentENV 侧怎么切换。

---

## 三、篇目与编写要点

每篇的要点分四块：**讲什么**（bullets）、**代码**（必读位置）、**图表**（建议）、**衔接**（前后篇）。
编写者按要点写，但不受其束缚 —— 读代码时发现要点有误，以代码为准并在交付说明中指出。
要点里写「确认」的地方是编写者必须到代码里核实的事实，大纲作者只做过一轮调研，没有逐条验证。

### 第〇部分　导读

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 00 | `00-overview.md` | 全书导读与 AgentENV 总览 | ○ |
| 01 | `01-repo-map-and-versions.md` | 仓库地图、版本与依赖 | ○ |

**00 · 全书导读与 AgentENV 总览**（最后写，全书完成后）
一篇读完全貌，给评审、决策者与第一天到岗的新人。5000 字上限。
- AgentENV 是什么：为 agentic RL 训练大规模运行 agent 环境的平台；E2B 兼容 API；单节点即可用，多节点加 Go 控制面
- 四个设计目标（来自 README，正文要落到机制）：镜像多样性靠 overlaybd 按需加载；空闲便宜靠快照暂停恢复；原生快照与 fork；长期运行的密度靠 ublk + 共享页缓存 + balloon
- 一个沙箱的一生（压缩版第 09 篇）：create → running → pause → resume → kill
- 三条主线：控制面（API → orchestrator → backend）、数据面（反向代理 → envd / 用户端口）、状态面（overlaybd 层栈 + 快照仓库）
- 与 e2b infra 的关系：同一套 SDK 契约，实现路线不同（NBD vs ublk、uffd vs 块设备 File 后端、Go 单体 vs Rust 节点 + Go 控制面），各一句话，指向第 65、66 篇
- 分读者的阅读路径（与 README 一致）
- 图：一张节点内部结构图（server 进程、ublk-daemon 进程、FC 进程、内核 ublk、存储）；一张多节点拓扑图

**01 · 仓库地图、版本与依赖**
- 版本：v0.1.0（2026-07-25）到 v0.2.3（2026-09-30）八个 tag，约每周一版；无 CHANGELOG 文件，release notes 由 git-cliff 生成；v0.2.3 的 24 个提交分组（startup pack、E2B v2 兼容、CLI Codex、远端 IO runtime、containerd plain snapshotter）
- `config/deps_manifest.toml`：Firecracker（KVM：`1.15.1-patch-v1`；PVM：firecracker-next `v1.17.0-next.1`）、内核（`vmlinux-6.1.175` / `6.12.33-pvm`）、tools 盘镜像 `agentenv-tools:0.1.1`、overlaybd 工具 `v1.0.18-aenv.1`、regctl；从 v0.1.0 起 FC 与内核版本未变（确认）
- Cargo workspace 19 个成员；`storage/uffd-core` 不在其中；Go module `services/`；生成代码清单（`src/api/generated`、`thirdparty/firecracker-client`、`src/custom_extension_api/generated`、`services/api/proto/*.pb.go`）与再生成命令
- 目录地图：每个顶层目录 / crate 一句话职责与行数（表）；`AGENTS.md` / `CLAUDE.md` 的 Code Map 表可作为起点（两文件内容相同）
- 进程视角：节点上有三类进程 —— `server`、`uvm-ublk-daemon`、每沙箱一个 `firecracker`；多节点再加 `gateway`、`scheduler`
- 代码：`Cargo.toml`、`config/deps_manifest.toml`、`build.rs`、`Makefile`、`AGENTS.md`、`git tag` / `git log` 输出
- 图：组件依赖图（crate → crate）；版本时间线表

### 第一部分　预备知识

面向没有相关背景的读者。每篇讲**本书用得到的**那部分，不做综述；每篇末尾明确指出「这些概念在本书哪几篇被用到」。

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 02 | `02-why-agentenv.md` | agent 环境的规模问题与 AgentENV 的取舍 | ○ |
| 03 | `03-firecracker-for-agentenv.md` | 本书用到的 Firecracker：快照、内存后端与脏页 | ○ |
| 04 | `04-io-uring-and-ublk.md` | io_uring 与 ublk | ○ |
| 05 | `05-overlaybd-and-lazy-loading.md` | overlaybd、LSMT 与 OCI 镜像按需加载 | ○ |
| 06 | `06-netns-iptables-transparent-proxy.md` | 网络命名空间、iptables 与透明代理 | ○ |
| 07 | `07-rust-async-primer.md` | 本书用到的 Rust 异步与依赖 crate | ○ |

**02 · agent 环境的规模问题与 AgentENV 的取舍**
- 问题：agentic RL 要同时跑大量各不相同的环境（README 称生产中 150 万镜像，只引用、不展开）；环境长时间空闲；需要分叉做并行探索
- 由此推出的四条要求：镜像不能预热到每台机器；空闲环境要能快速释放 CPU / 内存；暂停与 fork 的成本要正比于改动量；长期运行时密度不能衰减
- 每条要求对应的机制与代价（表）：overlaybd 按需加载 ↔ 冷读走网络；快照暂停 ↔ 恢复时缺页；ublk + 共享页缓存 ↔ 单 daemon 单点；balloon + DAMON ↔ guest 内核要求
- 为什么是 microVM 而不是容器：隔离边界；只点到，链接 Firecracker 手册第 02 篇
- 代码：`README.md`、`docs/src/concepts/overview.md`（读，但论断以代码为准）
- 图：要求 → 机制 → 代价 的三列表；不画装饰图

**03 · 本书用到的 Firecracker：快照、内存后端与脏页**
- 不复述 Firecracker；只讲 AgentENV 依赖的那几个行为，每条给出 Firecracker 手册对应篇的链接（延伸阅读里）
- 快照 = vmstate + 内存文件；Full / Diff；`track_dirty_pages` 与 KVM dirty log
- 恢复时的两种内存后端：File（mmap 内存文件，MAP_PRIVATE，写入 COW 到匿名页 —— 确认上游 v1.15.1 `vstate/memory.rs` 的 mmap 标志）与 Uffd
- AgentENV 用到但上游没有的四个补丁行为（只列，第 67 篇展开）：可选 `mem_file_path`、`GET /vm/dirty-memory-ranges`、seek 取内存文件大小（块设备可作内存文件）、drive 的 `direct`（O_DIRECT）
- balloon 的 free page reporting 与 guest 内 DAMON reclaim：AgentENV 的 boot args 与 `PUT /balloon` 配置
- CPU 模板与 `cpu-template-helper`：为什么跨机型恢复快照要求 CPUID 交集（第 57 篇用）
- 代码：`thirdparty/firecracker-client/firecracker.yaml`、`src/sandbox/firecracker/instance.rs`（看调用了哪些端点）、`config/default.toml` 的 `[firecracker] boot_args`；fc-aenv 的 `src/vmm/src/vstate/memory.rs`、`src/vmm/src/persist.rs`
- 图：快照文件与内存后端关系图；本书用到的 FC 端点表（端点 | 上游 / 补丁 | 本书哪篇）

**04 · io_uring 与 ublk**
- io_uring：SQ / CQ、SQE / CQE、`user_data`；fixed file 与 fixed buffer、sparse 注册表（IORING_REGISTER_BUFFERS2）；`IORING_OP_URING_CMD`（UringCmd16 / UringCmd80）
- ublk：内核驱动 `ublk_drv` 把块 I/O 交给用户态；`/dev/ublk-control`、`/dev/ublkcN`（字符设备）、`/dev/ublkbN`（块设备）；控制命令 ADD_DEV / SET_PARAMS / START_DEV / STOP_DEV / DEL_DEV / GET_FEATURES；数据面 FETCH_REQ 与 COMMIT_AND_FETCH_REQ 循环；mmap 出来的 `ublksrv_io_desc` 数组
- 特性位：`UBLK_F_AUTO_BUF_REG`、`UBLK_F_UPDATE_SIZE`、`UBLK_F_USER_RECOVERY`；内核版本要求（确认：文档写 6.8+，AUTO_BUF_REG 与 UPDATE_SIZE 实际需要更新的内核，给一张「最低可用 / 全部特性」分级表，版本号以内核源码或 changelog 为证，拿不准就写推论）
- 与 NBD、TCMU 的对比：为什么用户态块设备选 ublk（只讲到够读第六部分）
- 代码：`storage/ublk/src/ctrl.rs`、`storage/ublk/src/queue.rs`、`storage/ublk/src/ublk_caps.rs`、`storage/util/src/io_ring/uring.rs`（只看用法）
- 图：ublk 控制面与数据面总图（control / ublkc / ublkb / 用户态 server）；FETCH → COMMIT_AND_FETCH 时序图

**05 · overlaybd、LSMT 与 OCI 镜像按需加载**
- 问题：容器镜像按层 tar 存放，启动前要全量下载解包；块设备镜像 + 按需读可以跳过这一步
- overlaybd（DADI）的思路：每层是一个块级 LSMT 文件，多层索引合并，按 4 KiB / 扇区粒度从远端按需读；ZFile 压缩保持随机访问
- 上游 containerd/overlaybd（C++，tcmu 前端）与 AgentENV 的分工：**在线数据面是 Rust 重写**（`storage/overlaybd`），格式与上游逐字节兼容；**离线转换与扩容仍用 C++ 工具**（`overlaybd-create/apply/commit/resize`，kvcache-ai 分叉 `v1.0.18-aenv.1`）；未迁移的上游特性（turboOCI、gzip 索引、OCF 缓存）
- 两种镜像格式：overlaybd-native（远端层直接按需读）与标准 OCI（逐层转换成 overlaybd 层）；OCI referrers 找加速层
- 代码：`storage/overlaybd/src/lsmt/format.rs`（只看常量与注释）、`storage/overlaybd/src/tools/oci.rs`、`src/setup/overlaybd.rs`、`src/image/oci_image.rs` 的格式分类处
- 图：C++ 工具与 Rust 运行时的职责分界图；「OCI tar 层 → overlaybd 层 → 合并视图」示意

**06 · 网络命名空间、iptables 与透明代理**
- netns、veth pair、tap；`setns` / `unshare(CLONE_NEWNET)` 与 netns 文件的 bind mount
- iptables 的表与链：filter（INPUT / FORWARD）、nat（PREROUTING / POSTROUTING）；SNAT / DNAT / MASQUERADE / REDIRECT；conntrack 状态匹配；`iptables-restore --noflush`
- 透明代理：REDIRECT 到本地端口后用 `SO_ORIGINAL_DST` 取原目的地；HTTP Host 与 TLS SNI 嗅探
- /31 点对点地址（RFC 3021）与 link-local 地址
- 代码：`src/sandbox/network/slot.rs`、`src/sandbox/network/iptables_util.rs`、`src/sandbox/network/egress_proxy.rs`（只看系统调用处）
- 图：一个 netns 内外的接口与路由示意；iptables 包路径（只画本书用到的链）
- 衔接：第 29、30 篇；e2b 手册第 07 篇是同主题的另一视角，只在延伸阅读里链

**07 · 本书用到的 Rust 异步与依赖 crate**
- 不是 Rust 教程；讲读这份代码要认识的东西：tokio 多线程 runtime 与 `current_thread` + `LocalSet`；`Send` 与 `!Send` future；`spawn_blocking` 的代价；取消安全（cancellation safety）与 `tokio::spawn` 包一层的写法；`watch` / `broadcast` / `oneshot` / `Notify`；`OnceLock` 全局单例
- 依赖 crate 各一段：axum / tower（中间件洋葱）、hyper-util、tonic / prost、confique、RocksDB、opendal、iroh / iroh-blobs、io-uring、libublk-rs-sys、tikv-jemallocator、arc-swap、dashmap、roaring
- 代码组织纪律：`thiserror`、`SAFETY` 注释、clippy 配置（看 `Cargo.toml` 的 lints）
- 代码：`Cargo.toml`、`src/orchestrator/service.rs` 的 `run_cancellation_safe()`、`storage/ublk/src/dev.rs` 的 `queue_work()`、`storage/overlaybd/src/io/vfile_io.rs`
- 图：本书出现的几类 runtime / 线程一览表（谁、几个、跑什么）

### 第二部分　总体架构

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 08 | `08-system-architecture.md` | 系统架构：单节点与多节点 | ○ |
| 09 | `09-sandbox-lifecycle-walkthrough.md` | 一个沙箱的一生 | ○ |
| 10 | `10-node-process-and-object-model.md` | 节点进程：启动、关闭与对象模型 | ○ |
| 11 | `11-configuration.md` | 配置体系 | ○ |

**08 · 系统架构：单节点与多节点**
- 单节点：客户端直连 `server`（默认 `:8000`）；节点内部的子系统（API、orchestrator、sandbox、snapshot、template、image、p2p、observability）与外部进程（ublk-daemon、FC）
- 多节点：客户端 → gateway（HTTP）→ scheduler（gRPC）决定节点 → gateway 反向代理到节点；节点只经心跳与 scheduler 交互
- 存储拓扑：快照仓库（POSIX 共享文件系统或 S3 兼容对象存储）是持久真相；节点本地只有可重建的派生物
- 三种流量：控制面（`X-API-Key`）、数据面（反向代理到 guest，凭据在节点验证）、制品流（仓库 / registry / P2P）
- 代码：`src/bin/server.rs`、`src/lib.rs`、`docs/src/internals/architecture.md`（对照）、`services/README.md`
- 图：节点内部组件图；多节点拓扑图；三种流量的路径对照表

**09 · 一个沙箱的一生**
全书主线走读，后面各部分是这一篇每个步骤的展开。每一步只讲「发生了什么、在哪个模块」，细节链接到对应篇。
- 从模板创建：`POST /v2/sandboxes` → `create_sandbox_inner()` → `launch_sandbox()`：构造后端 → `start_nowait()`（FC 进程、snapshot load、共享内存设备）→ `store.add(Creating)` → `wait_for_ready()`（envd health、`/init`）→ CAS 到 Running → 写代理路由
- 运行：反向代理把请求送到 guest；envd 执行命令
- 暂停：CAS Running → Pausing → 摘路由 → state-only Diff 快照 → 脏页区间 → `process_vm_readv` → 内存层；rootfs restack → 持久化记录 → stop FC
- 恢复：Paused → Resuming → 新 FC（可能来自预热池）→ 共享只读内存设备 → `snapshot/load`（File 后端）→ 重写 MMDS → resume → 重新 `/init`
- 删除：DeleteProgress（Capture → Stop → Release）
- 冷启动（从 OCI 镜像）与从模板创建的差异一节
- 代码：`src/orchestrator/service.rs`、`src/orchestrator/launch_plan.rs`、`src/sandbox/firecracker/sandbox.rs` 的 `start_fresh()` / `start_resume()` / `pause_to_dir()` / `stop()`
- 图：五步时序图（拆成「创建」与「暂停 / 恢复」两张，参与者 api / orch / fc / ublkd / envd）

**10 · 节点进程：启动、关闭与对象模型**
- 启动顺序（`src/bin/server.rs::main()`）：jemalloc 配置 → 配置 → `--setup-only` / `--setup-host` 分支 → 能力检查 → API key / 身份 / P2P → `ensure_environment()` → 拉起 ublk-daemon → 预热 FC 池 → 各服务 → orchestrator（恢复持久记录）→ 监听（每连接 TCP_NODELAY 的原因）
- 关闭顺序：drain startup manifest 任务 → 注销 → **把所有 Running 沙箱 pause 落盘** → 清网络 → FC 池 → ublk-daemon → P2P；为什么只持久化 Paused（第 22 篇展开）
- 对象模型：`Orchestrator<S, F, P>` 的三张表（metadata store / 运行期句柄表 / 代理路由表）与锁顺序；`SandboxBackend` / `SandboxBackendFactory` trait；`PausedSandboxState` 对 orchestrator 不透明的设计
- 节点磁盘布局：`$AENV_HOME`（默认 `/var/lib/aenv`）与 `$AENV_RUNTIME`（默认 `/run/aenv`）下的目录
- 代码：`src/bin/server.rs`、`src/orchestrator/service.rs`（结构体与构造）、`src/sandbox/backend.rs`、`src/orchestrator/persistence/file_backed.rs`（目录）
- 图：启动顺序分列图（三列，按 FIGURE-GUIDE 长链分列法）；对象关系图；磁盘布局 ```text 树

**11 · 配置体系**
- confique 派生的 `AppConfig`；优先级：环境变量 > 文件 > 代码默认值；`ConfigManager::global()` 单例与隐式依赖的代价；不支持热加载
- `normalize()`：`$AENV_HOME` / `$AENV_RUNTIME` 占位符、相对路径基准、PVM 模式强制关闭 dirty tracking；`validate()` 的检查项
- `config/default.toml` 各节一览（表：节 | 关键键与默认值 | 消费方 | 本书哪篇），详细键值放附录 71
- 不一致之处：`DEFAULT_BOOT_ARGS` 与 default.toml 的 `boot_args` 不同；`AGENTENV_MEMORY_SNAPSHOT_TRACK_DIRTY_PAGES` 前缀；`API_ADDR` 不走 confique（确认）
- 代码：`src/cfg.rs`、`src/cfg/*.rs`、`config/default.toml`、`src/sandbox/firecracker/config.rs`（`DEFAULT_BOOT_ARGS`）
- 图：配置加载与归一化流程（≤ 6 步）；配置节表

### 第三部分　API 层

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 12 | `12-spec-driven-server.md` | 规范驱动的服务骨架 | ○ |
| 13 | `13-authentication.md` | 认证与凭据 | ○ |
| 14 | `14-sandbox-api.md` | 沙箱生命周期 API | ○ |
| 15 | `15-template-build-api.md` | 模板构建 API | ○ |
| 16 | `16-snapshot-and-volume-api.md` | 快照与卷 API | ○ |
| 17 | `17-reverse-proxy.md` | 反向代理 | ○ |
| 18 | `18-e2b-compatibility.md` | E2B 兼容性：矩阵与偏差 | ○ |

**12 · 规范驱动的服务骨架**
- spec-first：`src/api/openapi.yml` 是唯一真相；openapi-generator 7.22.0 `rust-axum` 生成 `agentenv_http_server` crate；手写 `ApiImpl` 只实现六个 trait
- 生成管线：`make agentenv-server` → `adev/src/codegen.rs::run_server()` → 后处理 `fix_duplicate_auth_trait()`（正则删重复 trait）→ `cargo fmt`；对生成器版本的脆弱性
- 生成的 trait 与「按状态码枚举的响应」：类型穷举状态码的好处与冗长代价；生成 handler 的固定步骤（claims 提取、`spawn_blocking` 校验与序列化）
- Router 组装与中间件顺序：metrics → `require_auth` → `sandbox_proxy_classifier` → 生成路由 / `/proxy` / BuildKit 隧道 / `/metrics` / fallback；`optional_connect_body()` 修补生成代码不接受空 body 的问题
- 错误映射：`repository_error()`、`From<OrchestratorError>`、同一错误在不同端点映射不同状态码的例子
- 最简单的 trait 实现做示例：`/nodes` 与 `/health`（`admin.rs` 169 行）；`NodeIdentity` 的来源
- 反方向的同一套生成器：custom extension 客户端（`-g rust`），只提一句，第 33 篇展开
- 代码：`src/api/server.rs`、`src/api/impls/mod.rs`、`src/api/impls/admin.rs`、`src/identity.rs`、`adev/src/codegen.rs`、`src/api/generated/src/server/mod.rs`（看一个 handler 模板）
- 图：生成管线流程图；中间件洋葱图

**13 · 认证与凭据**
- 三类凭据：部署级 API key（`X-API-Key`）、`envdAccessToken`（`X-Access-Token`）、`trafficAccessToken`（`e2b-traffic-access-token`）；表：凭据 | 头 | 作用域 | 生成 | 校验点
- API key 的解析顺序（环境变量 → `/run/secrets/api-key` → `$AENV_HOME/secrets/api-key` → 自动生成 `e2b_` 前缀）；常量时间比较；托管密钥文件的权限校验与原子创建（`managed_secret.rs`）
- 两类 token 都是 HMAC-SHA256(seed, subject) 无状态派生：不存库、pause / resume 不变、fork 子沙箱重新派生；代价是不能单个吊销；集群各节点 seed 必须一致；seed 丢失而存在受保护持久记录时拒绝启动
- `require_auth()` 决策树：先分控制面 / 数据面，再按「envd 端口 + secure」「应用端口 + allowPublicTraffic」判定；X-API-Key 永远不是数据面凭据，并在转发前剥离；隐藏 template builder VM（返回 404）
- spec 里继承自 E2B 的 Bearer / Team / Admin 安全方案在实现中全部退化为检查 X-API-Key；`Claims` 是空结构体 —— 没有租户概念
- 代码：`src/api/impls/auth.rs`、`src/api_key.rs`、`src/managed_secret.rs`、`src/sandbox/access.rs`、`src/api/impls/sandbox.rs` 的 `sandbox_model()`
- 图：凭据派生关系图；`require_auth` 决策流程图（≤ 20 节点，必要时拆两张）；「请求类型 × 所需凭据」表

**14 · 沙箱生命周期 API**
- v1 / v2 创建：`sandboxes_post()` 的步骤（解析快照 → 网络策略 → 扩展参数校验 → 卷预留 → `create_sandbox()` → 完成预留或回滚）；v2 强制 secure、timeout 默认 300；`mcp` 字段被静默忽略
- 冷启动 `/sandboxes-cold`：同步解析并可能转换镜像（TODO：改成 202 + 轮询）
- connect / timeout / refreshes 三者的语义差别（延长、覆盖、只延长）；pause / resume；resume 缺省 TTL 取 `default_sandbox_timeout_secs`（15 s）与 v2 的 300 s 不一致
- `PUT /network`：只改出站策略，ingress（allowPublicTraffic）不可改，跨层的占位约定
- 列表与分页：游标格式、内存全量排序；对外只有 running / paused 两种状态的折叠规则
- fork 与 snapshot 两个端点只讲 API 形状，机制在第 51、46 篇
- 代码：`src/api/impls/sandbox.rs`、`src/api/impls/pagination.rs`、`src/api/impls/attached_drives.rs`
- 图：创建时序（api / snap / vol / orch）；connect 按状态分支图

**15 · 模板构建 API**
- 模板就是 source = Template 的快照记录；templateID == buildID（「compatibility mode」）
- E2B 风格两步：`POST /v3/templates`（Waiting）→ `POST /v2/templates/{t}/builds/{b}`（`try_start_build()` → 后台构建）→ 轮询 status / logs；支持的步骤与不支持的 COPY / ADD / filesHash；ARG 当 ENV
- Dockerfile / BuildKit 路径：`PUT …/builder`（并发上限 429）→ 手写的 `GET …/builder` WebSocket 隧道（不在 spec 里）→ `DELETE …/builder`；服务端 8 条隧道上限与 CLI 32 并发的不一致
- 构建会话的崩溃恢复：`BuildJournal` 与 `recover_image_builds()`、30 s 周期清理
- 只讲 API 与会话；构建器内部在第 52、53 篇
- 代码：`src/api/impls/template.rs`、`src/api/impls/template_helpers.rs`、`src/api/impls/image_build.rs`、`src/api/impls/image_build/{transport,cleanup}.rs`
- 图：两条构建路径的 API 调用对照（两张小时序图或一张表）

**16 · 快照与卷 API**
- `POST /sandboxes/{id}/snapshots` → `capture_snapshot()` → `snapshot_sandbox_volumes()` → `publish_captured()`；`GET /snapshots` 只列沙箱来源的快照，模板记录返回 404
- 卷：exclusive / ro 两种模式；`fromVolume` 克隆与 `image` 初始化；`resolve_volume_mounts()` 的校验（数量、路径前缀重叠、大小）；预留 → 物化 → owner 从 pending 改为沙箱 id 的转移与回滚
- 从快照创建时恢复快照里的卷
- 代码：`src/api/impls/snapshots.rs`、`src/api/impls/volumes.rs`、`src/volume.rs`（只看 API 用到的接口）
- 图：卷预留与 owner 转移时序图

**17 · 反向代理**
- 三种入口：`/proxy` 前缀、fallback（未匹配路径 + 路由头）、Host 名 `{port}-{uuid}.{domain}`（在中间件里完成，优先于路由匹配）；路由头及 E2B 别名
- 解析：`proxy_lookup_for()` 读路由表不碰沙箱锁；`ProxyLookupResult` 五种结果；暂停沙箱的自动恢复（单次、60 s、TTL 至少 300 s）
- HTTP 转发：头清洗与 `x-forwarded-*`；两阶段超时（上传空闲 30 s → 响应头 30 s）；流式响应透传；**禁用连接池**的原因（同一 host interaction IP 跨代复用）
- WebSocket：握手、子协议、双向帧桥接；上游拒绝时原样返回
- 错误映射表（400 / 404 / 410 / 502 / 504）
- 鉴权只引用第 13 篇的决策树，不重复
- 代码：`src/api/proxy.rs`（正文约 1200 行，测试 41 个）
- 图：三入口汇聚图；`resolve_proxy_request` 状态图（含自动恢复环，按 FIGURE-GUIDE 改画 flowchart）；两阶段超时时序图

**18 · E2B 兼容性：矩阵与偏差**
- 兼容手段清单：路径与字段名、安全方案名、`e2b_` key 前缀、代理头别名、traffic token 头、envd 端口 49983、Host 形态、`domain` 字段、fallback 代理让 `E2B_SANDBOX_URL=${E2B_API_URL}` 成立、`client_id` 占位、分页头
- 偏差与缺口：无 team / 多租户；COPY / ADD 不支持；`mcp` 忽略；卷内容 API 不支持；sandbox ID 是 UUID；状态折叠；v1 / v2 secure 默认值不同
- AgentENV 扩展端点（E2B SDK 不会调用）
- 验证方式：e2e 套件 `09_e2b_compat.sh` 与 Python / TS SDK 兼容脚本
- 端点「是否 E2B 上游就有」的划分要对照 e2b infra 2026.09 的 `spec/openapi.yml` 逐条核实（确认）
- 代码：`src/api/openapi.yml`、`src/api/impls/*`、`scripts/tests/e2e/suites/09_e2b_compat.sh`；e2b infra 的 spec
- 图：E2B SDK 请求映射图（控制面 / 数据面）；兼容矩阵表

### 第四部分　orchestrator：沙箱状态机

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 19 | `19-state-machine-and-concurrency.md` | 状态机与并发控制 | ○ |
| 20 | `20-launch-plan-and-rollback.md` | launch plan 与失败回滚 | ○ |
| 21 | `21-deletion-and-volume-capture.md` | 删除与卷的捕获提交 | ○ |
| 22 | `22-persistence-across-restarts.md` | 跨重启持久化 | ○ |
| 23 | `23-auto-eviction-and-ttl.md` | 自动驱逐与 TTL | ○ |
| 24 | `24-metrics-and-events.md` | 指标与生命周期事件 | ○ |

**19 · 状态机与并发控制**
- 八个状态：Creating、Resuming、Running、Snapshotting、Forking、Pausing、Paused、Killing；没有 Killed（删除即从 store 移除，watch 发 None）
- 转换表：起始 → 目标 | 触发 | CAS 期望集合 | 代码位置（来自调研，逐条确认）
- `MetadataStore` 以 CAS 原语为核心；`InMemoryMetadataStore` 每条记录一个 `watch` 通道；`send_replace` 而不是 `send` 的原因
- `run_cancellation_safe()`：HTTP 调用方取消不打断状态转换；`wait_for_transition()` 60 s 兜底
- 并发同类操作：`join_concurrent_pause()` / `join_concurrent_resume()` 复用对方结果；delete 遇到过渡态先等再重试
- 测试：`orchestrator/tests.rs` 104 个测试覆盖的并发场景，作为「怎样验证状态机」的一节
- 代码：`src/orchestrator/types.rs`、`src/orchestrator/store/*`、`src/orchestrator/service.rs`、`src/orchestrator/tests.rs`
- 图：状态机（flowchart + 编号边 + 图下表，按 FIGURE-GUIDE「密集转移的状态机」）

**20 · launch plan 与失败回滚**
- `LaunchPlan{Create, Resume}` 把创建与恢复统一成一条 `launch_sandbox()` 流水线；`transitional_state()`
- 三个 shutdown 检查点；`FailedLaunchStage{Registered, TransitionalPersisted, RunningPersisted}` 与 `cleanup_failed_launch()`；句柄 `Arc::ptr_eq` 防止陈旧回滚
- 镜像引用保护：`protect_image_refs(StartingSandbox / PausedSandbox)` 防止镜像 GC 删掉要打开的层
- 同样的 begin / finish / fail 模式用于 Snapshotting 与 Forking（`capture_snapshot`、`snapshot_volume_mounts`、fork 的 orchestrator 一侧）
- Pause 的失败语义：`SandboxCaptureError{Recoverable, Terminal}`；Recoverable 返回前后端已恢复运行；持久化失败时原地 resume
- 代码：`src/orchestrator/launch_plan.rs`、`src/orchestrator/service.rs`（`launch_sandbox`、`cleanup_failed_launch`、`pause_sandbox_impl`、`begin/finish/fail_snapshot_operation`）、`src/sandbox/backend.rs`
- 图：launch 流水线与各失败阶段的回滚动作（分列图）

**21 · 删除与卷的捕获提交**
- 可重入删除：`DeleteProgress{Capture → Stop → Release → Done}`；失败保留进度，下次从断点继续，不重复 capture
- Capture：运行中且挂了卷时 `freeze_and_snapshot_volumes()`（guest 内 busybox fsfreeze、先压栈再 await 以保住 thaw 义务）→ restack 卷 → 发布 backing；可恢复失败先 thaw 再回到原状态
- Release：capture 失败时把卷标记为 Failed；释放卷预留；删除记录与产物
- 与 auto-eviction 共用 `deletion_progress` 锁
- 代码：`src/orchestrator/service.rs`（`delete_sandbox_inner` / `delete_sandbox_impl`）、`src/sandbox/firecracker/sandbox.rs`（`freeze_and_snapshot_volumes`）、`src/volume.rs`
- 图：DeleteProgress 状态图；freeze / restack / thaw 时序图

**22 · 跨重启持久化**
- 只持久化 Paused：Running 不落盘，靠关闭时全部 pause；template builder 例外直接删除
- 记录格式 `PersistedPausedRecord{version, lifecycle, metadata, artifact_root, state}`，RocksDB `records.db`、Sync 持久性；产物目录 `artifacts/<id>/<uuidv7>/`
- 两阶段 resume 标记：`mark_resuming` → 成功 `delete_record`（保留产物）/ 失败 `rollback_resuming`；启动时遇到 Resuming 直接丢弃记录与产物的理由
- `load_all()` 的清理规则：版本不符、解码失败、产物缺失 → 删；virtualization mode 不符 → 保留但不可恢复；孤儿目录 → 删
- 耦合点：token seed 丢失时拒绝启动；镜像 GC 的 fail-closed（先 pin 再 reconcile）
- 崩溃一致性边界：SIGKILL server 时 FC 子进程可能成为孤儿（调研未见回收逻辑，确认）；resume 后旧产物目录保留到 kill
- 代码：`src/orchestrator/persistence/{mod,file_backed}.rs`、`src/local_store.rs`、`src/orchestrator/service.rs`（shutdown）
- 图：Paused → Resuming → Running 的记录状态与崩溃点表；目录 ```text 树

**23 · 自动驱逐与 TTL**
- `NewTimeout{UseExisting, Set, EnsureMinimum, None}` 与 `SandboxTimeoutAction{Pause, Delete}`；过期索引 `BTreeSet<(expires_at, id)>`
- `start_auto_evict_task()`：1 s 周期、`MissedTickBehavior::Skip`、`Weak<Self>`；`claim_expired_running_sandbox()` 在 CAS 回调里二次校验过期
- 回收串行执行：大量同时过期时的延迟放大（技术债）
- 与代理自动恢复的联动（`EnsureMinimum(300 s)`）
- 代码：`src/orchestrator/service.rs`、`src/orchestrator/store/metadata.rs`、`src/orchestrator/store/in_memory.rs`
- 图：TTL 的生命周期示意（keep-alive、过期、认领、pause / delete）

**24 · 指标与生命周期事件**
- `OrchestratorMetrics`：两个原子计数器，其余从 store 现算，不会漂移；`SandboxContribution` 的状态 → 资源映射（含 paused 单独计数，供调度做「含暂停沙箱」的容量限制）
- guest 指标采样：周期 15 s + 事件触发；`try_lock` 不阻塞生命周期操作；以代理路由 version 作「代数」丢弃跨 pause / resume 的样本；保留 3600 s
- `SandboxLifecycleEvent` broadcast（容量 1024）与订阅方（observability reporter）
- Prometheus 指标一览（orchestrator 与 ublk 操作时延）
- 代码：`src/orchestrator/metrics.rs`、`src/orchestrator/sandbox_metrics.rs`、`src/sandbox/metrics.rs`、`src/observability/prometheus.rs`
- 图：采样与代数校验时序图

### 第五部分　沙箱运行时

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 25 | `25-backend-and-firecracker-process.md` | 后端抽象与 Firecracker 进程 | ○ |
| 26 | `26-sandbox-block-devices.md` | 沙箱的块设备：tools 盘、rootfs 与内存设备 | ○ |
| 27 | `27-start-pause-resume-sequences.md` | 启动、暂停与恢复的 Firecracker 调用序列 | ○ |
| 28 | `28-mmds-and-envd.md` | MMDS 与 envd | ○ |
| 29 | `29-network-slots.md` | 网络（一）：槽位、命名空间与地址计划 | ○ |
| 30 | `30-egress-policy-and-proxy.md` | 网络（二）：出站策略与透明代理 | ○ |
| 31 | `31-extra-drives-and-volumes.md` | 附加盘与卷：预留槽位与热插 | ○ |
| 32 | `32-warm-pools.md` | 预热池：网络、块设备与 Firecracker 进程 | ○ |
| 33 | `33-custom-extension-hooks.md` | 自定义扩展 hook | ○ |

**25 · 后端抽象与 Firecracker 进程**
- `SandboxBackend` / `SandboxBackendFactory`；`FirecrackerSandbox` 的字段（work_dir、fc_instance、network_slot、envd、各 ublk 句柄、hook guard）
- 进程 spawn：`spawn_with_netns()` 在临时线程里 `setns` 进 netns、把线程能力集清空后再 spawn —— FC 进程不带任何能力；`process_group(0)`、`kill_on_drop`；`oom_score_adj = 1000`；`--mmds-size-limit` 与 `--http-api-max-payload-size` 提到 1 MiB 的原因
- 不用 jailer：哪些隔离由 netns + 无能力进程 + KVM 提供，哪些没有（推论，与 Firecracker 手册第 43 篇对照）
- HTTP 客户端：`firecracker_client` 只生成了 models，真正的请求由 `socket.rs` 手写的 UDS hyper 客户端发出；**没有请求超时**的后果
- stop：SIGTERM → 等待 → SIGKILL；stop 时的资源释放顺序及每一步为什么在那个位置
- 代码：`src/sandbox/backend.rs`、`src/sandbox/firecracker/{instance,socket,connector,factory}.rs`、`src/privileges.rs`、`src/sandbox/firecracker/sandbox.rs` 的 `stop()`
- 图：进程与能力关系图；stop 顺序分列图

**26 · 沙箱的块设备：tools 盘、rootfs 与内存设备**
- 节点侧视角（daemon 内部在第 41 篇）：一个沙箱有哪些块设备、从哪里来、怎么释放
- 设备命名：vda = tools 盘（只读、root 设备、含 `/init` 与 busybox）、vdb = 用户 rootfs（可写 overlaybd）、vdc 起 = 物理附加盘，之后是卷槽位；最多 24 个
- `UblkDeviceManager` 单例：共享只读设备（tools、内存）以 canonical image.json 为 key 的 `Weak` 去重 + daemon 侧 refcount（两级）；`cache_fd` 保住页缓存的原因（引用代码注释）
- rootfs：`create_overlaybd_runtime_device()`、`OverlaybdRuntimeHandle`；可写 upper 的三种模式（默认 hybridLogStructured，确认）
- 为什么磁盘用 O_DIRECT（补丁 drive `direct`）：避免宿主页缓存双重缓存；tools 盘为什么不用
- tools 盘的来源：`tools-image/`（envd + busybox + `/init`）与 `agentenv-tools` OCI 镜像
- 代码：`src/sandbox/ublk/{device,overlaybd}.rs`、`src/sandbox/firecracker/sandbox.rs`（`link_tools_drive`、drive 配置）、`tools-image/`、`src/setup/deps.rs` 的 `ensure_tools`
- 图：一个沙箱的设备栈（FC → /dev/vdX → ublkb → daemon → overlaybd 层）；两级 refcount 示意

**27 · 启动、暂停与恢复的 Firecracker 调用序列**
- Fresh 启动：准备工作（tools 盘、rootfs 设备、附加盘、boot args 拼装、网络槽位、出站策略、扩展 hook）→ `PUT /logger`（可选）→ machine-config → cpu-config（有 CPU 交集时）→ boot-source → drives → network-interfaces → mmds/config → mmds → balloon → InstanceStart
- Resume：预热池命中与否两条路 → tools / rootfs / 附加盘 / 卷槽位（所有槽位占位文件必须存在的原因）→ 共享内存设备 → `snapshot/load`（File 后端 = ublk 块设备、network_overrides、resume_vm = false）→ 新卷 `PATCH /drives` → 重写 MMDS → 重设磁盘限流 → `PATCH /vm Resumed`；cpu-config 不能在 load 后设置
- Pause：sync 可写卷 → `PATCH /vm Paused` → state-only Diff 快照 → `GET /vm/dirty-memory-ranges` → 内存成层（第 42 篇）→ rootfs restack（第 37、41 篇）→ 附加盘与卷 → 组装 `FirecrackerSnapshotConfig` 与 manifest
- capture（为 snapshot / fork）与 pause 的区别：原地 resume vs stop
- boot args 的组成：`agentenv_drives=`、`ip=`、DAMON 区间、扩展返回的参数、白名单前缀
- 遗留：`load_snapshot_uffd()`（dead_code）、非 ublk rootfs 分支
- 代码：`src/sandbox/firecracker/sandbox.rs`（`start_fresh`、`configure_microvm`、`start_resume`、`pause_to_dir`、`snapshot_to_dir`）、`src/sandbox/firecracker/config.rs`、`src/sandbox/manifest.rs`
- 图：三张时序图（fresh / resume / pause，各 ≤ 14 消息）；FC 端点调用表

**28 · MMDS 与 envd**
- MMDS：`MmdsMetadata` 字段与 e2b 兼容（instanceID、envID、address、accessTokenHash = SHA-512）；V2、只挂 eth0；fresh 时启动前写、resume 后重写的原因；`imageConfigs` extra
- envd：guest 内的 e2b 守护进程（tools 盘里，版本 `[envd] version`）；地址 `http://<host_interaction_ip>:49983`
- `EnvdInstance`：health 轮询（3 ms 间隔、60 s 总时长）、`POST /init`（token、env、workdir、user、时间戳）、resume 后再次 init；USER 为数字或 `uid:gid` 时读 guest passwd 的两次 init
- gRPC 客户端 `DualClient`：先探测 H2，失败回落 H1；引导客户端不保留连接的原因
- `Executor`：以 root 运行（Basic `root:`）；运维通道依赖 tools 盘的 busybox
- 代码：`src/sandbox/firecracker/mmds.rs`、`src/sandbox/envd.rs`、`src/sandbox/envd/user.rs`、`src/sandbox/process.rs`、`thirdparty/envd/src/transport.rs`
- 图：ready → init 时序图

**29 · 网络（一）：槽位、命名空间与地址计划**
- 拓扑：VM eth0 ⇄ tap0 ⇄（netns 内转发）⇄ vpeer ⇄ veth ⇄ 宿主；地址计划 `slot_ips(idx)`：host interaction `10.11.0.0/16`、veth `10.12.0.0/16`、VM 链路固定 `169.254.0.20/30`
- **所有槽位的 VM 与 tap 地址相同**：快照 ABI 依赖这一点（fresh 经内核 `ip=` 配置，resume 不重放 boot args）
- 创建流程：新线程 `unshare` → bind mount netns 文件 → rtnetlink 建 veth / 移回宿主 / 配 /31（手搓 netlink 消息）/ tap / 路由 / ARP 调优（issue #272）→ ns 内 iptables
- 宿主全局规则与每 ns 基础规则（逐条给出，确认）；全部用 `iptables-restore --noflush` 批量提交，nft 只用于冲突探测
- `NetworkManager`：位图分配、启动时扫描残留 veth、冲突探测；`Slot::cleanup()`；容量 sysctl
- 代码：`src/sandbox/network/{mod,address_plan,slot,manager,iptables_util}.rs`、`src/cfg/network.rs`、`src/setup/network_capacity.rs`
- 图：拓扑与地址图；包路径（入站 DNAT / 出站 SNAT）

**30 · 网络（二）：出站策略与透明代理**
- `SandboxNetworkPolicy`：allowPublicTraffic、base policy、allowed / denied CIDR、allowed domains；`runtime_policy()` 为 None 时的快路径
- egress 链：conntrack → DNS → 内部网段与 always-denied 网段 REJECT → 用户链；用户规则顺序；只处理 IPv4
- 判定顺序 `is_ip_allowed()` / `is_domain_allowed()`；域名 allow 优先于用户 CIDR deny（与 E2B 一致），绝对拒绝仍有效；API 层要求域名规则必须配合 deny `0.0.0.0/0`
- 透明代理：80 / 443 REDIRECT 到 ns 内 `:15000` → `SO_ORIGINAL_DST` → 嗅探 Host / SNI → 在宿主 ns 用 hickory 解析（guest 无法劫持 DNS）→ 连接 → relay；授权按 TCP 连接，keep-alive 上后续请求不再检查
- 策略替换不中断：pending / active 两阶段；线程模型（每 ns 一个 listener 线程、每连接一个线程、5 ms 轮询 accept）的代价
- 预热网络槽位跨租户复用时的残留（conntrack、邻居缓存）—— 安全讨论
- 代码：`src/sandbox/network/{policy,egress_proxy,resolver}.rs`、`src/api/impls/sandbox.rs`（`validate_domain_allowlist`）、`src/orchestrator/service.rs`（`replace_sandbox_network_policy_inner`）
- 图：egress 判定流程图；代理连接时序图；策略替换两阶段表

**31 · 附加盘与卷：预留槽位与热插**
- 问题：FC 在快照恢复后不能新增 virtio-blk 设备；卷却要在恢复时挂上
- 预留槽位：首次启动按 `volume.max_volume_count`（默认 4）预留 `agentenv_volume_slot_<i>`，4 KiB 占位文件；之后替换 symlink + `PATCH /drives` 实现「热插」；manifest 记录 `volume_drive_slots` 与 `physical_extra_drive_count`
- guest 内挂载：fresh 由 init 读 `agentenv_drives=`；恢复后新加的卷由宿主经 envd 执行 `busybox mount`；只读卷加 `ro,noload` 的原因（崩溃一致快照的 ext4 日志）；sub_path 的 bind 流程
- `ExtraDrive` 与挂载路径保留表；`VolumeManager`：权威记录在快照仓库、本地是缓存；模式、状态、大小上限
- 卷的 CoW fork（fork 时 exclusive 卷每个子沙箱一份，ro 共享）只讲接口，fork 本身在第 51 篇
- 代码：`src/sandbox/extra_drive.rs`、`src/volume.rs`、`src/sandbox/firecracker/sandbox.rs`（`prepare_volume_drive_slots`、`bind_volume_drive_slot`、mount 逻辑）
- 图：设备命名与槽位示意（```text）；恢复时热插卷的时序图

**32 · 预热池：网络、块设备与 Firecracker 进程**
- 通用 `WarmPool<T>`：低 / 高水位、`fill_target` 遇到获取压力翻倍且只升不降（有意为之）、condvar 维护线程
- 三个池：网络槽位（回池不重建 namespace）、块设备（在 daemon 里，请求路径上异步补充，因为设备形状与镜像 / 大小相关）、FC 进程（已 spawn、socket 就绪、未配置；**只用于 resume**，因为 snapshot load 要求未配置的进程）
- 默认水位 low = 2、high = 64 三池共用；`pool.network.enabled = false` 并不彻底关闭的问题
- 代码：`crates/warm-pool/src/lib.rs`、`src/sandbox/network/manager.rs`、`src/sandbox/firecracker/pool.rs`、`storage/ublk-daemon/src/server.rs`（`PoolState`，只引用）
- 图：水位与 fill_target 演进示意；三池对照表

**33 · 自定义扩展 hook**
- 问题：让外部系统（网络、计费、sidecar 控制器）在生命周期关键点介入；sandbox id 跨 pause / resume 复用，stop 可能乱序
- 四个 hook：start-fresh（可返回 extra boot args）、start-resume、patch-params、stop；各自的调用时机与失败语义（表）
- `SandboxInstanceId`（UUIDv7）与 `CustomExtensionHookGuard`：发送前先记录 instance id，保证超时也能发出匹配的 stop；Drop 时 fire-and-forget
- patch 不持沙箱锁调用 hook；与 pause 竞争时返回 409；不串行化并发 patch（交给扩展方）
- params 随快照持久化；未配置扩展而传 params → 400
- 代码：`src/sandbox/custom_extension/client.rs`、`src/custom_extension_api/openapi.yml`、`src/orchestrator/service.rs`（`patch_sandbox_custom_extension_params`）、`src/sandbox/firecracker/sandbox.rs` 的调用点
- 图：生命周期时间线上的四个 hook 位置；乱序 stop 与 instance id 判定时序图

### 第六部分　存储：overlaybd 与 ublk

全书核心。第 34–39 篇讲 Rust 版 overlaybd（格式、读写、封存、后端、缓存），第 40–41 篇讲 ublk 与 daemon，
第 42–43 篇讲建立在它们之上的内存快照与启动加速，第 44 篇讲被替代的 uffd 方案。

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 34 | `34-lsmt-format-and-index.md` | LSMT 格式与索引 | ○ |
| 35 | `35-zfile-compression.md` | ZFile 压缩 | ○ |
| 36 | `36-read-write-paths-and-rw-layouts.md` | 读写路径与三种可写布局 | ○ |
| 37 | `37-seal-restack-compact.md` | 封存、restack 与 compact | ○ |
| 38 | `38-virtualfile-chain-and-remote-io.md` | VirtualFile 装饰器链与远端 I/O 运行时 | ○ |
| 39 | `39-block-cache-and-background-download.md` | 节点块缓存与后台下载 | ○ |
| 40 | `40-ublk-library.md` | ublk 库 | ○ |
| 41 | `41-ublk-daemon.md` | ublk-daemon | ○ |
| 42 | `42-memory-snapshot-over-ublk.md` | 内存快照：脏页成层与共享只读设备 | ○ |
| 43 | `43-startup-pack-and-prefetch.md` | 启动加速：trace prefetch 与 startup pack | ○ |
| 44 | `44-uffd-alternative.md` | uffd 方案与对比 | ○ |

**34 · LSMT 格式与索引**
- `HeaderTrailer`（390 B，占一个 4 KiB 块）字段表；flags 各位（含 AgentENV 新增的 bit5 hybrid_rw）；`index_size` 是条数不是字节
- `DiskSegmentMapping`（16 B）位域：offset 50 位、length 14 位、moffset 55 位、zeroed 1 位、tag 8 位；单位扇区；`NO_PHYSICAL_OFFSET` 哨兵；有物理空间的零段与无物理空间的零段
- 层文件的四种物理形态：sealed 只读层、RW 对（data + index）、Sparse RW、Hybrid RW
- 索引：`ReadOnlyIndex`（排序 Vec + 二分）、`MutableIndex`（BTreeSet，插入时切掉重叠）、`ComboIndex`；**tag 0 = 最新层而 RW 层放在 layers 末尾**的约定；255 层上限来自 u8 tag
- premerged index 缓存（AgentENV 新增，`PMIDX001`）：key 的构成、LRU 清理、进程内合并去重
- 死代码：`LinearizedBptree` / `IndexLBPT` 只有测试引用
- 与上游格式兼容的证据（C++ 生成的 commit 被 Rust 读，Rust 写的层被 `overlaybd-resize` 读写；`validate_rw_header_pair_paths()`）
- 代码：`storage/overlaybd/src/lsmt/{format,index}.rs`、`storage/overlaybd/src/lsmt/file/{types,readonly,stack,helper}.rs`
- 图：HeaderTrailer 字段表与映射位域（```text）；四种文件布局纵向对比（```text）；多层合并与 tag 方向（flowchart）

**35 · ZFile 压缩**
- 布局：Header 512 B（有效 96 B）、dict（恒为 0）、压缩块（可选 4 B CRC）、index（每块编码长度）、Trailer；flags；`CompressOptions`（默认 LZ4、4 KiB 块）
- CRC 变体：上游 `crc32c_extend` 的 raw CRC32C，用标准硬件 CRC32C 换算的写法；块 CRC 的 seed
- jump table 两级结构：每组一个 u64 绝对偏移 + 组内 u16 delta，O(1) 定位，因此单块编码长度必须 < 64 KiB
- 读路径：合并连续完整块的批读（与上游策略的区别）、CRC 失败时精确驱逐后重读、线程内缓冲池
- 写路径：`ZFileBuilder` 与常驻 `WorkerPool`（每 worker 一个压缩上下文、有界队列、按序号重排）；`ZFileCompactWriter` 让 compact 与压缩一步完成
- AgentENV 的策略：本地 sealed 层始终 raw，只在发布时按 `[snapshot.publish_compression]` 重封装；读端靠魔数自动识别
- 代码：`storage/overlaybd/src/compression/zfile.rs`、`storage/overlaybd/src/backend/switch.rs`、`src/snapshot/repository/backends/common/recontainerize.rs`
- 图：ZFile 纵向布局（```text）；jump table 两级结构（```text）；批读合并示意

**36 · 读写路径与三种可写布局**
- 层栈装配：`image.json`（兼容上游 camelCase）→ `ImageFile::open()` → 并行打开 lowers（32 路）→ upper → `stack_files()`；`LiveImageState` 外套 `tokio::RwLock` 的目的（restack 原子换栈）
- 读：512 对齐检查、按 4 MiB 分片、索引读锁下查映射、空洞与零段填 0；Hybrid 下读当前 upper 时持读锁到 I/O 结束；前台读计数（`FgReadGuard`）
- 写：LogStructured 追加 + 16 B 映射追加（group commit、增量 sha256 的前提）；Sparse 写到 `HEADER + offset`；Hybrid 的 InPlace / ReuseZero / Append 三类 fragment —— 避免 upper 无限增长，代价是原地写可能撕裂，快照正确性依赖 quiesce
- discard 在三种布局下的实现
- 潜在死锁：`write_at*()` 持读锁时再次取读锁、restack 写锁排队（推论，确认有无测试）
- 代码：`storage/overlaybd/src/image/image_file.rs`、`storage/overlaybd/src/lsmt/file/readwrite.rs`（`read_internal_into_generic`、`write_internal_generic`、`plan_hybrid_write`、`discard_range`）、`storage/overlaybd/src/config.rs`
- 图：层栈装配流程；Hybrid 写入 fragment 拆分示例（```text）；三种布局对比表

**37 · 封存、restack 与 compact**
- seal（`LSMTFile::close_seal()`）：原地封口，不拷贝数据 —— 在数据文件 EOF 写 index、补齐、从 header 复制 trailer；返回增量 digest
- restack（`ImageFile::create_snapshot_and_restack()`）：七步；第 2 步之后的失败一律 `RestackSnapshotTerminalFailure`，不回滚的理由（rename 已改变磁盘状态）；跨文件系统时节点侧的处理
- `compact_to()`：给定源层与映射写出单层 sealed 文件；chunk 可跨层；零块检测关闭（与上游当前行为一致）；调用者清单（commit / flatten / export、运行时层压缩、**内存脏页成层**）
- 运行时层数预算：运行时拥有的后缀层预算 `32 - stable_prefix / 4`，超出整体压缩；未超出时硬链接进快照目录
- 代码：`storage/overlaybd/src/lsmt/file/{readwrite,helper}.rs`、`storage/overlaybd/src/image/{image_file,snapshot}.rs`、`src/sandbox/firecracker/overlaybd_snapshot.rs`（`capture_live_overlaybd_snapshot`、`rewrite_lowers_with_runtime_roots`）、`src/sandbox/ublk/overlaybd.rs`（`compact_layers`）
- 图：restack 时序图（标出 Terminal 分界）；seal 前后文件布局对比（```text）

**38 · VirtualFile 装饰器链与远端 I/O 运行时**
- `VirtualFile` trait；`io-uring` feature 下返回 `!Send` future 的 `*_with_ctx` 系列；`vfile_io.rs` 用零大小策略类型单态化同一份代码（Send 给后台、!Send 给 ublk queue）—— 绕开 async 闭包 HRTB 限制
- 后端：`LocalFile`（同步 pread / pwrite 的 TODO 与原因；ctx 路径走 io_uring；O_DIRECT 用对齐缓冲）、`registryfs_v2`（Range GET、认证挑战缓存、重定向缓存）、OSS（opendal S3；分片上传内存峰值推导）、tar 适配（只服务单文件 tar 包裹的 blob）、`SwitchFile`（自动识别 ZFile、后台下载完成后切到本地）
- P2P HTTP 门面在读链上的位置（`/p2p-http/<origin>`、`/p2p-uuid/<uuid>`），机制在第 58 篇
- **多 runtime 陷阱**：opendal / reqwest 把连接任务绑到当前 runtime，而每个 ublk queue 有自己的、随设备销毁的 runtime；`RuntimeDispatchFile` 与每 `ImageService` 一个 `obd-remote-io` runtime 的解法；`shutdown_background` 的原因
- 代码：`storage/overlaybd/src/io/{virtual_file,vfile_io,dispatch_file}.rs`、`storage/overlaybd/src/backend/{local,registryfs_v2,oss,tar,switch}.rs`、`storage/overlaybd/src/image/image_service.rs`（`remote_runtime`）
- 图：一次远端读穿过的装饰器栈（自下而上）；有无 RuntimeDispatchFile 时连接任务归属对比

**39 · 节点块缓存与后台下载**
- full-file cache（AgentENV 自研，与上游元数据格式不兼容）：每远端文件一个目录 `{data, meta.bin}`；key 只取 digest 使跨 registry 共享；稀疏 data 文件整体 mmap + roaring bitmap（块默认 256 KiB）
- loader 选举：同一块只回源一次，其他请求挂 waker；`reserve_range` RAII 保证容量记账；回填与驱逐的屏障
- `meta.bin` 格式（`OBCH`）、checkpoint 周期、驱逐水位与默认容量
- 后台下载：每 `FileCacheBackend` 一个调度器、只限制执行；chunk 16 MiB；对冲重试；完成后经 `SwitchFile` 切本地
- `download_gate`：前台读在途时挂起后台块，但保留下限防饿死；**依赖单进程假设**；内存设备的后台下载等 envd 就绪（`NotifySandboxReady`，20 s 兜底）
- 代码：`storage/overlaybd/src/backend/cache/{full_file_cache,bk_download,meta}*`、`storage/overlaybd/src/download_gate.rs`
- 图：cache 结构图（data mmap + bitmap + block_states）；loader 选举流程；前台 / 后台准入示意

**40 · ublk 库**
- 为什么不用 libublk 的 queue（引用 `queue.rs` 开头注释）；只借用 `libublk-rs-sys` 的 FFI
- 控制面：`UVMUblkCtrl` 经独立 ctrl ring 线程提交 UringCmd80；已实现的命令；`UPDATE_SIZE` 的自定义编码与特性位
- 数据面：每 queue 一个 OS 线程（current_thread + LocalSet），每 tag 一个 slot task；`on_thread_park` 时批量 submit 的技巧；为什么每 queue 独立 ring（共享 ring 时 DEL_DEV 卡住）
- `UserBuffer` 与 `AutoRegBuffer`：AutoReg 在库里支持，但 `OverlaybdTarget` 拒绝它、daemon 也不开 —— 零拷贝只停留在库层面（推论原因：LSMT 一次请求拆到多层、ZFile 要解压）
- `OverlaybdTarget`：`ArcSwap` 状态可热切换（预热池用）、ublk 参数、支持的操作与错误码映射
- `AsyncIoRing`（`storage/util`）：slab key 作 user_data、future 被 drop 时标记 cancelled 防止 key 复用后误投递 —— 取消安全的关键
- 死代码：遗留 CLI `uvm-ublk`、`spawn_data_io_ring_worker`、`ReloadableIDAllocator`；日志里检查的特性位与实际设置的不一致
- 代码：`storage/ublk/src/{ctrl,dev,queue,io_buffer,ublk_caps}.rs`、`storage/ublk/src/impls/overlaybd_target.rs`、`storage/util/src/io_ring/*`
- 图：queue 线程内部结构；UserBuffer 与 AutoReg 数据路径对比

**41 · ublk-daemon**
- 进程模型：由节点 spawn、委派 CAP_SYS_ADMIN、独立进程组、stdout 打印 `ready`；pidfd 监听父进程退出（比 `PR_SET_PDEATHSIG` 可靠的原因）；RLIMIT_NOFILE；4 线程主 runtime
- RPC 协议：一连接一请求、4 B 大端长度 + JSON、上限 16 MiB；14 种请求（表）；三类错误语义（invalid_request / error / terminal_error）
- `ImageServiceCache`：按 global config 懒建 `ImageService`（rootfs 与内存用不同 global 配置）
- 预热池：`PoolState`（idle / active_exclusive / active_shared + 反向索引）、按镜像粒度的锁；**占位镜像** + `BLKFLSBUF` + `swap_state`，使空闲池不钉住业务镜像；Shared 获取的双重检查
- 运行时物化：改写 lower 路径、建 upper、必要时调 C++ `overlaybd-resize`（GiB 粒度、全局串行、超时 kill）并用 Rust 复验
- 故障模型：没有 `UBLK_F_USER_RECOVERY`，daemon 崩溃后客户端 watchdog 只做快速失败；单进程集中管理换来全局准入与共享缓存，代价是单点
- 代码：`storage/ublk-daemon/src/{main,server,protocol,runtime,client}.rs`
- 图：节点 / daemon / 内核部署图；池中设备状态图；RPC 请求表

**42 · 内存快照：脏页成层与共享只读设备**
本部分的高潮；与第 27 篇分工：27 讲 FC 调用顺序，本篇讲数据怎么变成层、层怎么变回内存。
- 暂停：state-only Diff 快照 → `GET /vm/dirty-memory-ranges`（`DirtyMemoryRanges` 的语义：与快照文件相同的连续镜像布局、去掉 MMIO 空洞、逻辑上不清除）→ `dirty_ranges_to_segment_mappings()`：**moffset 字段存 FC 进程的 HVA** → `ProcessVmReader` 把 `process_vm_readv` 包成 `VirtualFile` 当作「第 0 层」→ `compact_to()` 并发 32 写出 sealed 层 → 继承上一份 lowers、必要时压缩
- 写入量正比于脏页数，不随 VM 内存大小增长；没有中间 memfile；`process_vm_readv` 同步跑在 tokio worker 上（TODO）
- 「脏页」在 fresh VM 与 resumed VM 上分别指什么（resumed：MAP_PRIVATE 后发生 COW 的页 —— 推论，依据 FC File 后端实现）；`track_dirty_pages = false`（PVM）时的行为（确认）
- 恢复：`get_or_create_shared_mem()` → 同一快照的所有沙箱共享一个只读 `/dev/ublkbN` → `snapshot/load` File 后端 → 缺页链路（FC mmap → 块设备页缓存 → ublk → daemon → LSMT → 本地 / 缓存 / 远端）；页缓存跨沙箱共享 = 天然内存去重
- 两级 refcount 与 `cache_fd`；stop 时显式 release 避免与下一次 resume 竞争
- 代码：`src/sandbox/firecracker/sandbox.rs`（`snapshot_memory_to_overlaybd`、resume 中的内存设备段）、`src/sandbox/firecracker/{overlaybd_snapshot,process_vm_reader}.rs`、`src/sandbox/ublk/device.rs`、`thirdparty/firecracker-client/src/models/dirty_memory_ranges.rs`；fc-aenv 中 `get_dirty_memory_ranges_preserve`
- 图：暂停管线（flowchart，标出 moffset = HVA）；恢复时共享拓扑（N 个 FC → 一个 ublkb → 页缓存 → daemon）；内存层栈演进（fresh → pause1 → resume → pause2 → 压缩）

**43 · 启动加速：trace prefetch 与 startup pack**
- 问题：从远端恢复时首批缺页逐个回源，延迟叠加
- 录制：发布快照后用该快照起一个一次性 VM，内存设备用**专用、非共享**设备（共享设备的页缓存会掩盖首次触达）；`StartupPackRecorder`（原子 bitmap + 有序首触日志、按读延迟估算远端字节）；窗口参数；全程 best-effort
- manifest：`AENVMF01`（头 + 精确顺序前缀 + 合并区间）；只记位置不打包页数据；`memory-startup.pack` 文件名与「v2 / v3 / v4」版本称呼混用（统一口径，写在第 68 篇）
- 消费：OSS 来源交给 daemon `prefetch_startup_pack`（`pack_planner` 只用元数据把逻辑页翻译成最终对象的 256 KiB 块，与缺页共用 loader 选举）；本地来源由节点直接按 span 读共享设备
- 上游兼容的 acceleration layer trace（`prefetch.rs` 的 record / replay）
- 开关：`[snapshot.memory_startup_pack] enabled / consume_enabled` 默认关闭
- 代码：`src/sandbox/firecracker/startup_pack.rs`、`src/snapshot/startup_pack.rs`、`storage/ublk/src/impls/startup_pack_recorder.rs`、`storage/overlaybd/src/{startup_manifest,startup_pack,pack_planner,prefetch}.rs`、`storage/overlaybd/src/backend/cache/startup_pack_task.rs`
- 图：录制、发布、预取三段图

**44 · uffd 方案与对比**
- `storage/uffd-core`（不在 workspace）：`UffdHandle` 经 UDS 接收 uffd 与区域映射、缺页循环（UFFDIO_COPY / 零页）、Remove 事件的处理约束；`MemoryImageBackend` trait；它的快照路径同样是 `ProcessVmReader` + `compact_to` —— 现行方案从这里演化而来
- 被替代的原因（推论，依据代码与文档）：每 VM 一个用户态缺页 handler、每页一次 UFFDIO_COPY、无法跨 VM 共享页缓存、脏页只能粗估
- 对比表：uffd vs ublk + File 后端（页缓存共享、脏页跟踪、故障面、额外线程与 socket、对 FC 的要求）
- 与 e2b infra 的 uffd 后端对照一句话，链 e2b 手册第 31 篇（延伸阅读）
- 代码：`storage/uffd-core/src/*`、`src/sandbox/firecracker/instance.rs` 的 `load_snapshot_uffd()`
- 图：两种方案的缺页路径对比图；对比表

### 第七部分　镜像、快照与模板

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 45 | `45-oci-to-overlaybd.md` | 从 OCI 镜像到 overlaybd 层栈 | ○ |
| 46 | `46-snapshot-object-model.md` | 快照对象模型与 SnapshotManager | ○ |
| 47 | `47-posix-repository.md` | POSIX 仓库与提交协议 | ○ |
| 48 | `48-object-storage-repository.md` | 对象存储仓库：上传、回滚与弱一致 | ○ |
| 49 | `49-resolve-and-artifact-cache.md` | 从记录到可运行：resolve 与本地制品缓存 | ○ |
| 50 | `50-rootfs-as-oci-image.md` | 快照 rootfs 作为 OCI 镜像 | ○ |
| 51 | `51-fork.md` | fork：同节点的内存分叉 | ○ |
| 52 | `52-template-builder.md` | 模板构建器 | ○ |
| 53 | `53-buildkit-in-microvm.md` | BuildKit：在 microVM 里跑 Dockerfile | ○ |

**45 · 从 OCI 镜像到 overlaybd 层栈**
- `ImageResolver::resolve()`：候选 registry 展开（search / allowed registries）→ regctl 取 manifest（按宿主架构选子 manifest）→ 只有取 manifest 阶段可以换 registry → referrers 找 overlaybd-native 加速层 → 分类（StandardOci / OverlaybdNative / turbo 拒绝）
- OverlaybdNative：不下载任何 blob，运行时 `registryfs_v2` 按需拉
- StandardOci 逐层转换流水线：regctl copy 生产者 ‖ 转换消费者；`LayerConversionKey` 链式包含父 commit digest（whiteout 与 ext4 需在全部 lower 之上 apply）；三级查找：本地索引 → P2P → `overlaybd-apply`；层 UUID 由源层 digest 派生
- 本地 image-cache：目录、RocksDB 元数据图（HardCommit、ConfigReference、Hold、LastUsed）；fail-closed GC 的保留条件；容量驱逐；committed 快照不 pin image-cache
- regctl 的 `GOMAXPROCS = 4` 与重试
- 代码：`src/image/{resolver,oci_image,commit_index,reference}.rs`、`src/image/cache/*`、`storage/overlaybd/src/tools/oci.rs`
- 图：resolve 决策树；逐层转换流水线；image-cache 元数据图与 GC 保留条件

**46 · 快照对象模型与 SnapshotManager**
- `SnapshotRecord` / `CommittedSnapshot` / `OverlaybdLayerRef{Managed, External}` / `RunnableSnapshot` + lease；committed 记录只存逻辑层引用，不存节点本地路径（manifest 的 path 字段 `#[serde(skip)]`）
- 一个快照由哪些制品组成：表（制品 | capture 目录 | POSIX 仓库 | OSS key | 节点运行时）
- 三层存储：capture staging → committed repository → node-local runtime cache；各层的所有者与生命周期
- `SnapshotManager`：薄门面；`publish()` 成功后才 best-effort P2P 发布（两个测试锁定该不变量）；`publish_captured()` 先启动 startup 录制使其与上传并行
- 模板是 source = Template 的记录，状态 Waiting → Building → Ready | Error；`step` 必须是 1-based 数字字符串的原因（e2b SDK）
- 代码：`src/snapshot/types/*`、`src/snapshot/manager.rs`、`src/sandbox/manifest.rs`、`docs/src/internals/persistence-artifact-inventory.md`（对照）
- 图：对象模型类图；三层存储示意

**47 · POSIX 仓库与提交协议**
- 布局：`catalog/records`、`catalog/aliases`、`snapshots/{id}/`、`managed-layers/`
- publish：begin → 导入制品（vm_state 硬链接或边拷边算 sha256 再回读校验；层：有描述符则信任只比 size、运行时增量现场 hash、远端层只记引用；稀疏层 dense 导出）→ commit：alias 锁 → 冲突 / 陈旧判断 → 写 alias → 写 commit marker → 写 record（temp + fsync + rename）
- 可见性判据：只看 record；alias 先于 record 写入，读路径在锁下惰性清理陈旧 alias
- 锁：per-alias、per-record `flock`，无全局锁；模板状态转换是真 CAS
- 删除顺序；**managed-layers 从不删除**；marker 与 record 之间崩溃留下的孤儿；`firecracker-manifest.json` 非原子写
- 运行时直接读共享文件系统上的 managed 层（`file=` 指向仓库）—— 共享 FS 读性能决定冷启动
- 代码：`src/snapshot/repository/backends/posixfs/*`、`src/snapshot/repository/interfaces.rs`
- 图：publish 时序图（含失败回滚箭头）；仓库目录树（```text）

**48 · 对象存储仓库：上传、回滚与弱一致**
- 「OSS」实为 opendal S3 兼容后端；URL 用 `s3://`
- publish 七步（引用注释编号）：层上传（先 exists 再无条件 put，内容寻址使 TOCTOU 无害）、发布压缩使 digest 描述压缩后字节、vm_state 与 manifest、附加盘、`bind_alias()`（读-写-回读，弱于 CAS）、写 record 即提交点；失败回滚删 `artifacts/{id}/` 前缀与已推 registry manifest
- 凭证：静态或 `credential_process`、提前刷新、只在 403 时强制刷新重试（`crates/object-store-operator`）；分片上传 64 MiB × 10000 的上限与内存峰值
- 一致性：`try_start_build` 文档写「Atomically」而实现是普通 RMW；同文件里卷与 build-cache head 已用条件写实现真 CAS —— catalog 本可迁移
- POSIX 与 OSS 一致性对比表（提交点、alias、模板状态、startup 描述符、卷、层去重、回滚、GC、P2P）放在本篇末尾
- 代码：`src/snapshot/repository/backends/oss/*`、`src/snapshot/repository/backends/common/recontainerize.rs`、`crates/object-store-operator/src/*`
- 图：publish 时序图；对比表

**49 · 从记录到可运行：resolve 与本地制品缓存**
- POSIX resolve：vm_state 直接用仓库路径；物化三个运行时 `image.json`（managed 层 `file=` 仓库路径、External 层 `repoBlobUrl`）；hydrate manifest；lease 打包
- OSS resolve：vm_state 先 P2P 后 OSS 下载到本地缓存；manifest 同理；**层不下载**，只并发校验存在，运行时按需拉
- `materialize_image_config()`：`file=`（唯一本地副本）与 `dir=`（可回退远端、可回收）的选择
- `LocalArtifactCache`：pin 引用计数、同 key 单 in-flight、LRU 降到 80%；**索引纯内存**，重启后未再访问的旧文件不计入也不驱逐（技术债）
- startup manifest 制品的生命周期（与第 43 篇分工：这里只讲制品与 attach，录制与消费在 43）
- 代码：`src/snapshot/repository/backends/{posixfs/runtime,oss/resolver}.rs`、`src/snapshot/runtime_support.rs`、`src/snapshot/artifact_cache.rs`、`src/snapshot/startup_pack.rs`
- 图：resolve 数据流（POSIX / OSS 两列）

**50 · 快照 rootfs 作为 OCI 镜像**
两条独立机制，分开讲。
- 离线导出 `aenv-snapshot-image`：刻意跳过 runtime resolver / cache / P2P；确定性 config 与 manifest，manifest digest 唯一标识镜像（复用 / 冲突 / 只传缺失 blob）；只导出 rootfs，产物只能冷启动
- 发布时推回源 registry（「acr」模块，实为通用 OCI registry 客户端）：条件（OSS 后端 + `image_publish.enabled` + rootfs 是「远端 registry 层 + 本地增量」）；tag `agentenv-snapshot-{id}`；manifest 的 overlaybd-native 注解约定；committed 层记为 External；回滚
- 代码：`src/bin/aenv-snapshot-image.rs`、`src/snapshot/image_export/*`、`src/snapshot/repository/backends/common/acr/*`
- 图：两条路径对比图（层字节流向、是否保留内存）

**51 · fork：同节点的内存分叉**
- 端到端链路：API（count 1..100；exclusive 卷每子沙箱一个 CoW fork，ro 卷共享）→ orchestrator（Forking 状态、逐个注册子沙箱、部分成功语义）→ 后端（pause 到 managed 目录 → **立即 resume 源** → 每个子沙箱 `snapshot_config_for_fork()` + 身份与 token 覆盖 → 并发 start）
- fork **不经过快照仓库**：没有记录、没有上传；子沙箱共享封存的 lower，各有新 upper；因此只能同节点；不允许追加 drive 的原因
- pause / snapshot / fork 三者对照表（落盘位置、是否进仓库、源沙箱状态、能否跨节点）
- 代码：`src/api/impls/sandbox.rs`（`sandboxes_sandbox_id_fork_post`、`prepare_volume_fork_specs`）、`src/orchestrator/service.rs`（`fork_sandbox_with_specs`）、`src/sandbox/firecracker/sandbox.rs`（`fork`、`snapshot_config_for_fork`）
- 图：fork 时序图；层共享示意（共享 lower、独立 upper）

**52 · 模板构建器**
- 两种 base：镜像（`build_template()`）与已有模板（`build_template_from_snapshot()`，不能改 CPU / 内存、不继承 alias 与扩展参数）
- `TemplateBuildRunner`：独立 OS 线程 + current_thread runtime；VM 启动 → 逐步执行（RUN 经 envd；ENV / USER 等只改上下文；WORKDIR 经 envd 文件服务创建）→ 补默认用户 → 启动 / 就绪命令 → 版本探测 → capture；**每步都在 microVM 里执行，没有逐步层缓存**，整个构建只产生一个快照
- 从 ENTRYPOINT / CMD 推导 start_cmd 在步骤路径被禁用（PID 1 问题），BuildKit 路径仍在用 —— 两条前端不一致
- 构建日志：tracing layer 截获、周期 flush、原子替换
- Ext4 base 是死代码
- 代码：`src/template/*`
- 图：runner 内部流程（分列图）

**53 · BuildKit：在 microVM 里跑 Dockerfile**
- 架构：buildctl 在 CLI 本地，buildkitd 在 builder microVM 里，中间是 WebSocket 隧道；秘密与上下文不经过 API 的 HTTP body
- builder 自身也是一个模板快照：alias = `builder-{sha256(...)}`，放在快照仓库的私有命名空间 `template-build/builder`；多节点并发首建时 AliasConflict 即复用
- 构建流程：reserve → 从缓存种子 fork 可写卷挂到 `/var/lib/buildkit` → 热启动 builder 沙箱 → 监听 BuildKit history 认出自己的记录 → content API 按 sha256 读镜像 → 转 overlaybd（只转缺失层）→ 释放 builder → 普通模板构建发布
- 缓存种子：线性继承、并发不合并、最后成功者成为下一个种子；`replace_build_cache_head()` 的条件写；退役与回收
- 取消、超时、重启恢复
- 代码：`src/api/impls/image_build.rs`、`src/api/impls/image_build/{worker,cache,transport}.rs`、`src/image/buildkit*.rs`、`src/snapshot/repository/build_cache.rs`、`crates/aenv/src/commands/build.rs`（只看隧道端）
- 图：组件图（CLI ⇄ 隧道 ⇄ API ⇄ builder VM；content API → resolver → 仓库）；缓存种子演进图

### 第八部分　分布式控制面

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 54 | `54-control-plane-overview.md` | 控制面总览与 proto 契约 | ○ |
| 55 | `55-gateway.md` | gateway：路由判定与反向代理 | ○ |
| 56 | `56-scheduler.md` | scheduler：放置、绑定与 HA | ○ |
| 57 | `57-heartbeat-and-cpu-intersection.md` | 心跳、节点可观测与 CPU 模板交集 | ○ |
| 58 | `58-p2p-artifact-transport.md` | P2P 制品传输 | ○ |

**54 · 控制面总览与 proto 契约**
- 为什么单节点不需要它；多节点时的三个角色（gateway、scheduler、节点）
- `services/api/proto/scheduler.proto` 的 13 个 RPC 分组：调度、绑定、观测、P2P、生命周期；Go 端生成入库、Rust 端 `build.rs` 构建期只生成客户端
- 节点状态推导表（proto 注释）；隐式耦合：节点新增按 sandbox 路由的端点时必须同步改 gateway 的路径模式
- 代码：`services/api/proto/scheduler.proto`、`build.rs`、`services/README.md`
- 图：三角色与 RPC 方向图；RPC 分组表

**55 · gateway：路由判定与反向代理**
- 认证分界：控制面在 gateway 验 API key；数据面不验，交给节点（只有节点知道 ingress 策略）
- 不用 `http.ServeMux` 的原因；`routeSource` 的优先级：host → 网关本地聚合（列表、节点、metrics）→ 路径里的 sandbox id → 模板构建 → 路由头 → 调度
- 选节点：已有 sandbox 走 query-only 的 `LookupNode`；新建走 `Schedule`（提取 hint，但策略不用）
- 转发：数据面路径加 `/proxy` 前缀、host 路由注入头；流式与 WebSocket 不受请求超时限制
- 写绑定：从响应头或响应体取 sandbox id 后 `RecordAssignment`；普通沙箱失败只 warn（依赖心跳自愈），模板构建失败返回 503
- 集群列表：全节点扇出、全有或全无、合并分页
- 代码：`services/gateway/internal/*`、`services/gateway/cmd/main.go`
- 图：路由判定流程图；创建请求时序图（client / gw / sched / node）

**56 · scheduler：放置、绑定与 HA**
- 放置：发现列表去掉 lingering → 配上最近心跳快照 → `FilterByResourceLimit`（含三项 including paused）→ round-robin / random；hint 被忽略；**不排除 UNHEALTHY 节点**（技术债，测试名不副实）
- 绑定存储：sandbox → node，TTL 30 s；内存实现与 Redis 实现（Lua 脚本原子迁移；不兼容 Redis Cluster）；`ReconcileNode` 让「心跳名单即真相」
- 发现：static 与 kubernetes（EndpointSlice + Pod informer、terminating → lingering、节点 ID = Pod 名）
- HA：primary + query-only 副本；primary 宕机时哪些功能还在；P2P 索引与注册表只在 primary 内存
- 失败模式表（来自调研，逐条确认）
- 代码：`services/scheduler/internal/*`、`services/scheduler/cmd/main.go`
- 图：放置两段式流程；绑定一致性时序图（RecordAssignment 与心跳的竞态，标推论）；失败模式表

**57 · 心跳、节点可观测与 CPU 模板交集**
- 节点侧：`ObservabilityService::node_snapshot()` 合并运行时计数、主机指标（CPU 取两次 `/proc/stat`）、沙箱 ID 名单；reporter 心跳循环（5 s、失败指数退避到 60 s）与事件循环（scheduler 端只打日志丢弃）
- 注销：`UnregisterNode` 校验 service_instance_id 防误注销；关闭时先注销再 pause 落盘带来的 404 窗口
- **CPU 模板交集**：节点用 `cpu-template-helper` dump 本机 CPU 配置、首个心跳上报一次 → scheduler 在同一 cluster 全部上报后按位求交 → 经心跳响应下发 → 节点 `PUT /cpu-config` 用于所有新沙箱与模板构建；目的：快照可在异构 CPU 节点间恢复；scheduler 重启后不再重算的问题（推论）
- Prometheus：节点与控制面共用直方图桶
- 代码：`src/observability/*`、`crates/observability/src/lib.rs`、`services/scheduler/internal/{node_registry,cpu_template}.go`、`src/bin/server.rs`（`cluster_cpu_arc`）
- 图：心跳时序图；CPU 交集流程图

**58 · P2P 制品传输**
- 抽象：`P2pTransport`、key / descriptor / provider；`DisabledP2pTransport` 让调用方无条件调用
- iroh 后端：FsStore + RocksDB catalog；不用公共发现与中继；一个 Router 两个 ALPN（blobs 数据、`/agentenv/artifact-catalog/v1` 元数据）；publish / lookup（本地 → scheduler 索引 → 全部 peer）/ fetch（BLAKE3 校验、TempTag 防 GC、成功后自广告）/ 门控 GC
- 发现：scheduler 的 `ListP2pPeers`；endpoint 经心跳上报
- 三个消费者与 key 空间（表）：快照固定制品、overlaybd 层的 HTTP range 门面、转换层复用；各自的校验与回退
- overlaybd P2P HTTP 门面（`src/overlaybd/p2p/facade.rs`）：正负缓存、超时、中途出错不回退 origin 的原因
- 失败原则：P2P 失败只是缓存未命中；**信任边界**：catalog 无鉴权、固定制品没有记录 digest —— 集群内 peer 被视为可信
- 代码：`src/p2p/*`、`src/overlaybd/p2p/*`、`src/snapshot/p2p.rs`、`services/scheduler/internal/store.go`（artifact store）
- 图：拓扑图（节点 A / B / C + scheduler 索引）；lookup 三级与自广告时序图；key 空间表

### 第九部分　部署与工程

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 59 | `59-host-setup-and-privileges.md` | 宿主准备、依赖供给与权限模型 | ○ |
| 60 | `60-deployment.md` | 单节点安装、Compose 与 Kubernetes | ○ |
| 61 | `61-pvm.md` | PVM：没有嵌套虚拟化时 | ○ |
| 62 | `62-aenv-cli.md` | aenv CLI | ○ |
| 63 | `63-testing-and-benchmarks.md` | 测试与基准 | ○ |
| 64 | `64-build-codegen-release.md` | 构建、代码生成与发布 | ○ |

**59 · 宿主准备、依赖供给与权限模型**
- 三种模式的分工：`--setup-only`（无特权下载依赖）、`--setup-host`（root 一次性配置宿主：KVM、ublk、udev、sysctl）、运行时 `ensure_environment()`（只校验）
- 依赖供给：manifest → 版本化路径 `deps/firecracker/<ver>/`、`deps/kernel/<ver>/`；下载无校验和（技术债）；tools 盘 OCI 镜像转 ext4 / overlaybd
- 权限模型：运行用户 + CAP_NET_ADMIN / CAP_SYS_ADMIN 处于可委派状态；清 ambient；线程作用域能力与 `spawn_tokio_command_scoped()`；`linux-cap` crate；FC 子进程无能力
- `scripts/docker-setup.sh`：ublk 模块参数、modules-load、sysctl
- 代码：`src/setup/*`、`src/privileges.rs`、`crates/linux-cap/src/lib.rs`、`scripts/docker-setup.sh`
- 图：三种模式职责表；能力在进程与线程间的流向图

**60 · 单节点安装、Compose 与 Kubernetes**
- install.sh：两个 bundle（CLI、server + 预下载 deps）、systemd unit（User=aenv、AmbientCapabilities、`KillMode=process` 等，逐项说明原因）、API key 位置
- Docker 镜像：cargo-chef 多阶段、运行时包列表硬编码与 manifest 手工同步、构建期预烘焙 deps
- Compose：两节点共享快照仓库与 secrets 卷 —— 是「多节点模拟」不是生产拓扑
- Kubernetes：kustomize base 与 local-dev overlay；节点 DaemonSet（privileged、hostPath、节点 ID = Pod 名、preStop 等待沙箱清空、grace 3600 s）；scheduler 用 EndpointSlice 发现；`run.sh` 生成密钥；没有 query-only / Redis 清单
- 代码：`scripts/install.sh`、`scripts/install-cli.sh`、`deploy/docker/*`、`deploy/docker-compose.yml`、`deploy/k8s/**`
- 图：三种部署形态对照表；k8s 资源关系图

**61 · PVM：没有嵌套虚拟化时**
- PVM 是什么（宿主内核模块 `kvm_pvm` 提供 `/dev/kvm` 兼容接口），只讲到够理解 AgentENV 的切换；论文只引用
- AgentENV 侧：`VirtualizationMode` 是节点级配置也是快照兼容域；`setup/kvm.rs::validate_mode` 的互斥校验；PVM 只支持 x86_64；PVM 下强制关闭 dirty tracking；依赖按 mode 切换（firecracker-next、6.12.33-pvm 内核）
- 运行时代码没有 KVM / PVM 分支：差异全在二进制、内核与配置
- 未核实处：firecracker-next 是否实现 `dirty-memory-ranges` 及无 dirty log 时的语义（标推论）
- 代码：`src/virtualization.rs`、`src/setup/kvm.rs`、`src/cfg.rs`（normalize / validate）、`src/orchestrator/persistence/file_backed.rs`（mode 处理）、`docs/src/deployment/pvm.md`
- 图：KVM / PVM 对照表

**62 · aenv CLI**
- 分层：同步 ureq 走控制面、reqwest 走 envd 与 BuildKit；每命令一个 current_thread runtime；凭据文件
- envd 数据面用 Connect 协议而非 gRPC 的原因（代理不支持 HTTP/2）；HTTP/1.1、禁连接池、TCP keepalive 与 `tcp_user_timeout`；不带 X-API-Key
- `connect`：PTY、shell 探测、StreamInput 10 s keepalive（对齐代理 30 s 空闲超时）、断线重连、看门狗、暂停探测、按活动续期 —— 交互式远程终端的鲁棒性工程
- `build`：本地 `buildctl` + 每连接一条 WebSocket 的隧道；清理
- `codex`：私有 ingress + secure envd + WebSocket 代理的完整用例
- 仍用 deprecated `POST /sandboxes`；动态补全
- 代码：`crates/aenv/src/**`
- 图：CLI 分层图；`aenv build` 时序图

**63 · 测试与基准**
- 测试金字塔表：Rust 单元与能力测试（`run-with-capabilities.sh` 委托能力）、集成测试（需 /dev/kvm、ublk、netns）、OSS E2E（MinIO）、存储测试、HTTP E2E 套件（17 个 suite，single-node / compose / k8s 三种模式）、BuildKit、Go、基准
- CI workflows 一览；k8s E2E 不在 CI
- 可测试性设计：mock 后端、`#[cfg(test)]` 切换超时常量、orchestrator 并发测试
- 基准：四个 bench 测什么（不给数字）；E2B 基准脚本
- 代码：`Makefile`、`tests/**`、`crates/{e2e-tests,benchmarks,test-support}/**`、`scripts/tests/**`、`.github/workflows/*`
- 图：测试金字塔表；CI 矩阵表

**64 · 构建、代码生成与发布**
- 根 Makefile 与 `adev/`（codegen、coverage、mutants）；`build.rs`（proto、`AENV_GIT_COMMIT`）；`rust-toolchain.toml` 不锁版本
- 生成代码再生成命令表
- 发布：tag → `release.yml`（校验版本、CLI 四平台、server 三个 bundle 并预下载 deps、git-cliff、多架构镜像与 PVM 镜像）
- tools 盘镜像：`tools-image/`（从 e2b infra 编译 envd + busybox + `/init`）与 `publish-tools-image.yml`
- 文档站：mdBook + mermaid + stoplight 渲染 openapi
- 代码：`Makefile`、`adev/src/*`、`build.rs`、`.github/workflows/release.yml`、`cliff.toml`、`tools-image/`、`docs/book.toml`
- 图：发布流水线分列图

### 第十部分　对照与延伸

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 65 | `65-vs-e2b-infra-architecture.md` | 与 e2b infra 的对照（一）：架构、控制面与 API | ○ |
| 66 | `66-vs-e2b-infra-storage-and-memory.md` | 与 e2b infra 的对照（二）：存储、内存恢复与模板 | ○ |
| 67 | `67-firecracker-patch-layer.md` | AENV 补丁版 Firecracker 与 guest 内核 | ○ |
| 68 | `68-known-issues-and-debt.md` | 已知问题与技术债 | ○ |

**65 · 与 e2b infra 的对照（一）：架构、控制面与 API**
- 对照维度表：语言与进程结构（Go 单体 orchestrator + api + client-proxy vs Rust 节点 + Go gateway / scheduler）；控制面（Nomad / Consul、PostgreSQL、Redis vs 单节点自足 + 可选 scheduler）；认证与多租户（team / access token vs 单 API key）；反向代理（client-proxy + orchestrator proxy vs 节点内代理 + gateway）；网络（每沙箱 netns 的做法异同）；envd（同一个 envd，AgentENV 只做客户端）
- 每一维先讲两边各自解决什么问题，再讲取舍；不评优劣
- 依据：e2b 手册第 10、15、16、19、35、53 篇；e2b infra 代码只在手册不够时看
- 图：两套架构并排图；对照表

**66 · 与 e2b infra 的对照（二）：存储、内存恢复与模板**
- 块设备：NBD + 用户态 COW vs ublk + overlaybd 层栈
- 内存：uffd 缺页 + 模板 memfile vs 只读 ublk 块设备作 File 后端、页缓存跨沙箱共享
- 暂停：e2b 定制版的 `/memory/*` API 与可选 memfile（Firecracker 手册第 50–54 篇）vs AENV 补丁的 `dirty-memory-ranges` + `process_vm_readv` —— 两个分叉独立地走到了相似的方向，差别在哪里
- 模板构建：Docker 构建 + 转换 vs 在 microVM 里执行步骤 / BuildKit
- 快照存储：GCS / 模板缓存 vs POSIX / S3 仓库 + P2P
- 依据：e2b 手册第 05、06、29–37、41–46 篇；Firecracker 手册第 49–54 篇
- 图：内存恢复路径并排图；对照表

**67 · AENV 补丁版 Firecracker 与 guest 内核**
- 补丁表：7 个提交（commit | 文件数 | +/- | 内容 | AgentENV 调用点）
- 主线：「快照内存不经过 mem.bin」—— 可选 `mem_file_path`（补丁 2）+ `dirty-memory-ranges`（补丁 7，读 KVM dirty log 后写回内部位图，逻辑上不清除）+ seek 取文件大小让块设备作内存文件（补丁 5）；再讲 drive `direct`（补丁 3）
- 未被使用的补丁：pmem seek（补丁 1）、`/vm/guest-memory-regions`（补丁 4，思路被补丁 7 取代）
- 补丁栈的后续：patch-v2 的 `PUT /vm/pre-fault-memory`（x86_64 only，v0.2.3 未用）、nestedvirt 分支、空的 v1.16.1-patch 分支；client crate 版本号仍写 1.15.1
- 与 e2b 定制版的平行关系（Firecracker 手册第 50、54 篇）只在一节里对照
- guest 内核：`vmlinux-6.1.175` 从 `aenv-deps` release 下载，两仓库都没有专属 config，fork 未改 `resources/guest_configs`（推论：用上游 CI 配置构建）；boot args 隐含的内核要求（DAMON reclaim、free page reporting、`pci=off`）
- 代码：fc-aenv 的 `git log -p v1.15.1..aenv-deps`；`thirdparty/firecracker-client/firecracker.yaml`；`src/sandbox/firecracker/instance.rs`；`config/deps_manifest.toml`；`src/setup/deps.rs`
- 图：补丁 → 调用点映射图；补丁表

**68 · 已知问题与技术债**
- 按「正确性 / 可用性 / 可运维性 / 供应链 / 文档」分类，每条：现象、位置、后果、可能的方向；语气中性
- 来源：各篇调研中记录的问题（第 13、14、17、22、23、25、30、36、40、41、47–49、52、56–59、67 篇）；编写本篇前先汇总各篇交付说明中「发现的问题」
- 文档漂移专节：`docs/src/internals/*` 与代码不一致之处、`CLAUDE.md` 失效链接、startup pack 版本称呼
- 代码：各篇已列
- 图：分类汇总表

### 附录

| # | 文件 | 标题 | 状态 |
|---|---|---|---|
| 69 | `69-glossary.md` | 术语表 | ○ |
| 70 | `70-code-map.md` | 代码地图：crate、模块与篇目 | ○ |
| 71 | `71-config-env-ports-reference.md` | 配置项、环境变量与端口总表 | ○ |
| 72 | `72-api-reference.md` | 接口总表：HTTP、Firecracker、daemon RPC 与 gRPC | ○ |
| 73 | `73-artifacts-and-formats-reference.md` | 持久化制品与磁盘格式总表 | ○ |

**69 · 术语表**：STYLE.md 第三节术语 + 正文出现的其它术语；每条一句定义 + 首次详细讲解的篇目链接。

**70 · 代码地图**：按目录 / crate 列模块、行数、一句话职责、讲解篇目；生成代码单列。

**71 · 配置项、环境变量与端口总表**：`config/default.toml` 全部节与键（键 | 默认值 | 作用 | 篇目）；环境变量（含不在 confique 体系里的）；端口（8000、49983、15000、9103、gateway 8080 / 9102、scheduler 9090 等，逐个确认）。

**72 · 接口总表**：HTTP 端点（E2B 形 / 原生 / 节点 / 代理入口；方法 | 路径 | handler | 篇目）；AgentENV 调用的 FC 端点（上游 / 补丁）；ublk-daemon 14 种 RPC；scheduler 13 个 gRPC；扩展 hook 4 个。

**73 · 持久化制品与磁盘格式总表**：快照制品清单（谁写、谁读、谁删、有没有 GC）；节点本地目录；磁盘格式魔数一览（`LSMT`、ZFile、`PMIDX001`、`OBCH`、`AENVMF01`）；与上游 overlaybd 的兼容性对照表（格式 | 兼容与否 | 依据）。

---

## 四、编写流程

1. **规划**（本文件）：主编完成，用户过目后才开写。
2. **编写**：每篇由一个子任务独立完成，输入是 `tools/briefs/agentenv/WRITER-BRIEF.md` + 本文件中该篇的要点；
   一个子任务负责 3–4 篇相邻篇目；一波最多 10 个子任务并行。
   顺序：第二至九部分 → 第一部分（预备知识按正文实际用到的写）→ 第十部分（第 68 篇最后写，汇总各篇交付说明）→ 附录 → 00。
3. **审校**：每 8–10 篇一个审校子任务（`tools/briefs/agentenv/REVIEWER-BRIEF.md`），抽查代码论断、统一术语、修链接；
   编写者交付说明里给其它篇目的建议汇总到 `tools/briefs/agentenv/review-notes.md`，审校时逐条处理。
4. **图**：`tools/figcheck.sh agentenv` 全 PASS；WARN 的图按 `tools/briefs/FIGURE-FIXER-BRIEF.md` 返工。
5. **验收**：主编逐部抽读，跑 `tools/mdlinks.py agentenv`、`tools/mdmermaid.mjs agentenv/*.md`、`tools/figcheck.sh agentenv`，
   打包 `dist/agentenv.html`，用 chromium 截图看排版，更新 README 的版本行与版本表，提交、打 tag、发 Release。

每篇完成后把本文件状态列改为 `●`，审校后改为 `◎`。
