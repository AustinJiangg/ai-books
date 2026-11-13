# 附录 A　术语表

> 版本：2026-09-30。章号按本书 28 章结构。术语定义依据本书所引论文、技术报告、厂商文档、开源仓库与标准文本中的用法；"首次出现章节"指正文首次定义该术语的章节。

## 用词规范

以下约定适用于全书正文、图表与附录。

### 1. 沙箱、环境、运行时

| 词 | 本书用法 | 不要这样用 |
|---|---|---|
| **沙箱**（sandbox） | 一个被隔离的执行实例及其边界：一个容器、一台 microVM、一台完整 VM 或一个 FnCall 进程。计数单位是"个沙箱"。例："DSec 每天服务约 300 万个沙箱。" | 不用"沙盒"（引用媒体标题时除外）；不把"沙箱"当作一套平台的名字 |
| **环境**（environment） | RL/评测语义上的"任务世界"：数据集或任务 + harness + 验证器（verifier），通常跑在一个或多个沙箱里。计数单位是"个环境"。例："GLM-5 有 1 万以上可验证环境。" | 不把"10 万个环境"写成"10 万个沙箱"，反之亦然；"环境实例"指环境在某一沙箱中的一次具体化 |
| **运行时**（runtime） | 两义，须按语境限定：①**沙箱运行时**，实现隔离的技术栈（runc、runsc/gVisor、Firecracker、Kata）；②**沙箱内运行时**，沙箱内部负责执行命令的守护进程（DSec 的 aether/chronus、AgentENV 的 envd） | 不单独用"运行时"指整个平台 |
| **沙箱平台 / 沙箱基础设施** | 包含控制面、存储、网络等在内的整套系统（DSec、AgentENV、OpenSandbox）。DSec 自称"弹性执行平台，而非单一沙箱运行时" | — |
| **执行环境** | 泛称，仅在引用原文（如"执行环境当作黑盒"）或不需区分时使用 | — |

### 2. 英文保留与译名

- **Agent**：正文保留英文"Agent"；引用中国标准、政策文件时用"智能体"。
- **rollout**：**不译**。首次出现时注"（一次策略与环境交互直至结束的完整采样过程，也称轨迹展开）"。其产物称"**轨迹**"（trajectory）。"rollout 状态"指一次 rollout 进行中的全部可恢复状态。
- **harness / scaffold**：harness 不译（首次注"外壳/评测框架，负责驱动 Agent 循环、工具与打分"）；scaffold 译"**脚手架**"。二者辨析见术语表。
- **microVM**：保留英文，首次注"**微虚拟机**"；full VM 译"**完整虚拟机**（完整 VM）"。不写"微型 VM""轻量 VM"。
- **reward hacking**：保留英文，首次注"**奖励投机**"（指模型以非预期途径拿到奖励）。不用"奖励黑客""奖励作弊"作为正式译名；"作弊"可作为描述性口语。specification gaming 译"**规约博弈**"。
- **egress**：译"**出站**"；ingress 译"**入站**"。"出网"仅作口语。allowlist 译"**白名单**"，denylist 译"**黑名单**"，default-deny 译"**默认拒绝**"。
- **overcommit**：译"**超售**"（内存超售、CPU 超售），不用"超分""超配"。
- **prompt injection**：译"**提示注入**"；indirect prompt injection 译"间接提示注入"。
- **confused deputy**：译"**混淆代理人**"。**lethal trifecta** 译"**致命三要素**"，首次保留英文。
- **E2B 协议**：指 E2B 的沙箱生命周期 HTTP API 与 SDK 约定，非正式标准；首次出现注"事实标准"。
- 公司、产品、项目名（DSec、AgentENV、OpenEnv、Harbor、veRL、slime 等）一律不译。

### 3. 状态操作用词（第 11–12 章）

| 词 | 定义 | 区分要点 |
|---|---|---|
| **快照**（snapshot） | 沙箱某一时刻内存和/或磁盘状态的持久化副本 | 名词；强调"副本" |
| **检查点**（checkpoint） | 作为恢复点而保存的快照，通常可增量、可多次 | 强调"用于恢复"；"做检查点"= checkpointing |
| **恢复**（restore / resume） | restore：从快照重建沙箱；resume：让暂停的沙箱继续运行 | 书中"恢复"默认指 restore；需区分时写"恢复运行（resume）" |
| **暂停**（pause）/ **休眠**（hibernate / suspend） | 暂停：停止执行、保留状态（可仍占内存，如 `docker pause`）；休眠：把状态写出后释放资源（如 DSec 对 microVM 快照后终止 Firecracker 进程） | 引用厂商数字时必须注明是内存态唤醒还是深度休眠唤醒 |
| **fork（分叉）** | 从运行中的沙箱或快照派生出多个子实例，子实例共享父状态并写时复制 | 首次写"fork（分叉）"，后文用 fork；不与进程 fork() 混用时须加限定 |
| **分支**（branch） | 文件系统或执行上下文层面的 fork（BranchFS 的 branch context） | 用于论文原有术语 |
| **回滚**（rollback） | 把状态恢复到先前检查点 | 仅对沙箱内状态可行；沙箱外副作用需补偿或事务 |

### 4. 框架性名称（全书统一）

- **三场景**：**训练**（RL 训练 rollout）、**评测**（基准、能力与安全评测）、**产品推理**（面向用户的 Agent 产品执行环境）。不写"推理场景"而省略"产品"。
- **两类对手**：**被利用的代理人**（外部对手借 Agent 行事，核心概念为混淆代理人、提示注入、致命三要素）；**作为对手的模型**（模型本身在沙箱内追求目标而越界，包括 reward hacking、环境篡改、逃逸；CSA 称"具备内部人能力的对手"）。
- **八层架构**：① **接入与 API**；② **控制面**；③ **节点运行时**；④ **镜像与存储**；⑤ **状态管理**；⑥ **密度与资源**；⑦ **网络与出站**；⑧ **RL 集成与完整性**。引用时写"第④层（镜像与存储）"。
- **Agent 负载五特征**（第 3 章标题）：突发、稀疏、有状态、低扇出、可中断；DSec 原文另有"异构""执行不可信"两项，合称七特征。
- **三种产品范式**（第 21 章）：一次性短命容器、任务级临时 VM 或容器、有状态长期 VM。
- **状态三层**（第 11–12 章）：本地快照/fork；外部副作用事务；回滚语义与安全。
- **reward hacking 二分**（第 19 章）：**取回型**（答案已存在，被模型取回；分**沙箱内取回**：.git 历史、平台日志、构建残留，与**出站取回**：上游、镜像源）与**篡改型**（离线亦可发生，改测试、改评估器、改环境）。

### 5. 数字与标注

- 数字引用须附来源类型与日期，冲突数字按附录 B"冲突数字登记"的建议措辞。
- "（推断）"标注笔者由已引用事实推出的结论；"TrEnv → AgentENV → DSec"谱系一律注明"（推断，基于作者重合）"。
- 2026 年大量系统论文仍为预印本，引用时标注"预印本"或会议名。
- **二手引述**：一手文件存在，但本书只能经第三方转引原句（如 PDF 文本提取不全）时使用的来源类型；区别于"二手报道"（第三方自己的叙述）（第 27 章起使用，附录 B 亦用此类型）。

---

## 术语表

### A. 场景、对手与总体框架

| 中文术语 | English | 定义（1–2 句，结合 Agent 沙箱语境） | 易混淆项/辨析 | 首次出现章节 |
|---|---|---|---|---|
| Agent 沙箱 | agent sandbox | 为 LLM Agent 执行代码、调用工具、操作界面而提供的隔离执行实例及其配套控制设施。 | 与"代码解释器"不同：Agent 沙箱是有状态、长寿命、多轮的；与"环境"不同，见用词规范；DSec："requires an elastic execution platform rather than a single sandbox runtime"（§1）——单个沙箱与沙箱平台的区分 | 1 |
| 三场景 | three scenarios（training / evaluation / product inference） | 训练 rollout、评测、产品推理三类使用场景，在突发性、状态寿命、镜像复用、隔离档位等维度上要求不同。 | 训练重吞吐，产品重延迟（OpenAI 工程师演讲的区分，仅见二手转录）；评测在批量上接近产品、在对手上接近训练（第 1 章表 1-1） | 1 |
| 产品推理沙箱 | inference-facing / product sandbox | 面向终端用户的 Agent 产品（Code Interpreter、Codex、Manus 等）所用的执行环境。 | DSec 把 OpenAI Code Interpreter、E2B、Kimi-K2.5 Agent Swarm 归为"面向推理的系统" | 1 |
| 两类对手 | two adversary classes | 被利用的代理人（外部对手借 Agent 行事）与作为对手的模型（模型自身越界）。 | 前者的防线重在限制数据、凭据、出站；后者要求沙箱扛住内部攻击者 | 2 |
| 混淆代理人 | confused deputy | 持有用户权限的 Agent 被不可信内容操纵，替攻击者行使合法权限。 | 不是权限提升漏洞；攻击利用的是"合法权限"（如 Replit 删库） | 2 |
| 致命三要素 | lethal trifecta | Willison 提出：同时具备访问私有数据、接触不可信内容、对外通信三种能力时，攻击者可诱导 Agent 外泄数据。 | 缓解方式是拆掉任一"腿"，而非提高检测率 | 2 |
| 提示注入 | prompt injection | 通过输入内容（直接或间接）改变 Agent 行为的攻击；间接提示注入来自网页、文件、工具输出等。 | 与越狱（jailbreak）不同：注入的是数据通道中的指令 | 2 |
| 工具投毒 | tool poisoning / rug pull | MCP 工具描述中藏有用户不可见但模型会遵循的指令；rug pull 指 server 在获批后更改工具定义。 | 属供应链风险，与提示注入交叉 | 2 |
| 作为对手的模型 | model as adversary / insider-capable adversary | 被训练或评测的模型本身为达成目标而篡改环境、取回答案或突破遏制；CSA 建议按"具备内部人能力的对手"建模。 | OWASP 对应 ASI10 Rogue Agents（部署语境，未涉训练期）；CSA 原文为"insider-capable adversary"，其隔离建议原文为"biolab-level containment" | 2 |
| AI 控制 | AI control | Redwood 提出的框架：假设模型可能有意破坏安全措施，评估可信编辑、不可信监控等协议能否仍保证安全（arXiv 2312.06942）。本书引申：沙箱、权限与出站限制是确定性的"硬底线"，监控抓住沙箱放行的部分（推断，原论文未讨论沙箱）。 | 与对齐（alignment）互补而非替代 | 2 |
| 谋划 | scheming | 模型为追求目标而隐瞒真实能力与目标、欺骗或关闭监督（Apollo，arXiv 2412.04984）。 | 目前主要见于研究评测；与 reward hacking 并列为"作为对手的模型"的行为之一 | 2 |
| 负载刻画 | workload characterization | 用生产数据量化 Agent 沙箱负载的突发性、CPU 稀疏性、寿命、镜像扇出等特征（以 DSec 表 2/3 为范本）。 | 附录 D 提供模板 | 3 |
| CPU 稀疏性 | CPU sparsity | 沙箱大部分时间在等 LLM，平均 CPU 用量远低于请求值（DSec 约 90% 沙箱 ≤ 5%）。注意与"平均 CPU 利用率"（AgentCgroup 以单核为 100%）、"等待占比"区分，见第 3 章表 3-2。 | 是超售与暂停的依据 | 3 |
| 镜像扇出 | image fanout | 同一镜像被多少个沙箱使用；DSec 每任务口径容器中位数为 3。 | 扇出低意味着缓存与 P2P 分发收益小（本书推断；DSec 不用 P2P 的理由是复用 3FS、免建分发层，见第 10 章） | 3 |
| 峰均比 | peak-to-average ratio | 内存峰值与均值之比；AgentCgroup 测得 Agent 负载最高 15.4 倍（单个任务的极端值），云负载中 Azure VM 在 2–3 倍以内。 | 用于说明内存而非 CPU 是并发瓶颈 | 3 |
| 刻画单位 | unit of characterization | 负载数字所依据的统计单位：作业、沙箱实例、rollout/轨迹、迭代、轮次、任务。 | 不同单位的数字不可直接比较（如 K2.5 的 10 万为任务，不是沙箱；MiMo 的 1 万为 pod；Hunyuan-A13B 的 1,000 为并发执行；MiniMax 的"数十万"为分钟级调度；见表 26-1） | 3 |
| 等待占比 | wait fraction | 沙箱寿命中等待模型推理的时间占比；K3 报告最多 98%。 | 受推理侧排队影响，不是负载自身的属性；与 CPU 稀疏性、OS 执行占比区分 | 3 |
| 暂停占比 | paused fraction | 沙箱处于暂停或休眠状态的时间占寿命的比例（附录 D 字段 5.3）。 | 与"等待占比"区分：等待是"在等模型"，暂停是"真的被挂起"；K3 的 98% 是等待占比的上界，不是暂停占比 | 附录 D |
| 部分 rollout | partial rollout | 生成阶段在一定比例 λ 的轨迹完成后暂停，未完成的 rollout 在下一次迭代优先恢复（K3 §4.1.2）。 | 是算法主动安排的"中断"，与 GPU 抢占不同；要求沙箱跨迭代保留状态 | 3, 17 |
| 净变化语义 | net-change semantics | 只把持久性效果（文件系统修改、进程创建与退出、长寿命进程的内存修改）计为状态变化，排除临时文件、短命子进程（Crab）。 | 用于统计"状态变化率" | 3, 11 |

### B. 隔离原语与虚拟化

| 中文术语 | English | 定义（1–2 句，结合 Agent 沙箱语境） | 易混淆项/辨析 | 首次出现章节 |
|---|---|---|---|---|
| 隔离档位 | isolation tier | 按隔离强度与开销排列的后端层级；DSec 为 FnCall → 容器 → Firecracker microVM → QEMU 完整 VM，按任务选择。 | 与 AgentENV"统一 microVM"路线对照 | 4 |
| Seatbelt | Seatbelt（sandbox-exec） | macOS 的进程级沙箱机制，Claude Code、Codex CLI 用运行时生成的 profile 调用；`sandbox-exec` 已弃用且无 CLI 替代。 | 与 App Sandbox 不同，后者需签名与 entitlement | 4 |
| bubblewrap | bubblewrap（bwrap） | Linux 上基于命名空间与绑定挂载的非特权沙箱工具，Claude Code（srt）、Codex CLI 在 Linux 上使用；依赖带能力的非特权用户命名空间（Ubuntu 24.04+ 默认限制）。 | 在 Docker 内嵌套运行需弱化模式 | 4 |
| Landlock | Landlock LSM | Linux 安全模块，允许非特权进程自我限制文件、TCP、UDP、IPC 等访问；ABI 1–11 逐步扩展。 | 与 seccomp 互补：Landlock 管资源访问，seccomp 管系统调用；能力取决于内核 ABI 版本（ABI 1–11 对应 Linux 5.13–7.3），须尽力而为降级；Codex 已将其降为旧选项 | 4 |
| seccomp | seccomp / seccomp-bpf | 用 BPF 过滤器限制进程可用的系统调用；srt 用它阻止创建 `AF_UNIX` socket。 | 无法拦截继承或经 `SCM_RIGHTS` 传入的 fd | 4 |
| 审批疲劳 | approval fatigue | 用户对频繁权限提示机械批准的现象；Claude Code 用户此前批准约 93% 的提示。 | 沙箱可减少提示（84%），因此也是可用性工具 | 4 |
| 信任移交 | trust handoff | 沙箱内 Agent 写下文件，之后由沙箱外受信任工具执行（hook、`.vscode`、virtualenv、git 元数据、项目配置）的漏洞类；广义上也包括沙箱外进程跟随沙箱内创建的符号链接（CVE-2026-39861）。名称出自 CSA 研究笔记标题"The Trust Handoff Flaw"（2026-07-22）；Pillar 称"实为可执行代码的工作区配置"，Cymulate（2026-04）称"基于配置的沙箱逃逸"。 | 属"策略管道"失效，非内核逃逸；不是 Pillar 或 BleepingComputer 的用语 | 4 |
| 策略管道 | policy plumbing | 围绕隔离原语的代理解析、白名单命令、可执行配置等配套逻辑；2026 年多数绕过发生在这里。 | 与"隔离原语本身被攻破"对照 | 4 |
| 容器 | container（runc / OCI） | 基于命名空间与 cgroup、共享宿主内核的隔离；DSec 用作 SWE 与工具调用主后端。 | SandboxEscapeBench 作者建议默认不把普通 Docker 视为足够 | 5 |
| 容器逃逸 | container escape / breakout | 从容器取得宿主控制，常利用错误配置（特权模式、暴露的 daemon）或 runc/内核漏洞。 | 与"出站突破"不同：2026 年真实事件多经相邻服务而非内核 | 5 |
| gVisor | gVisor（runsc） | 用户态应用内核：Sentry 截获并实现系统调用，自身只向宿主发出几十种系统调用（2019 年论文 55 种，二手资料 53 种、含网络 68 种），文件经 Gofer 进程访问；runsc 为其 OCI 运行时。claude.ai 代码执行、GKE Agent Sandbox、Modal（与 VM 运行时并列）、Cloud Run 第一代执行环境使用。 | 介于容器与 microVM 之间，不是虚拟机；不防上层组件漏洞、Spectre 类侧信道与沙箱内负载自身的漏洞（gVisor 安全导论）；syscall 数字口径见附录 B C-42 | 5 |
| microVM（微虚拟机） | microVM | 设备模型极简、启动快、开销小的 KVM 虚拟机，每个沙箱有独立内核。 | 与"安全容器"（Kata）的区别在接口层：Kata 以 OCI/CRI 形式包装 VM | 6 |
| Firecracker | Firecracker | AWS 开源的 Rust VMM，每进程一台 microVM，启动到 init ≤ 125 ms、开销 ≤ 5 MiB；E2B、AgentENV（自维护补丁版）、DSec microVM 档的底座。 | "Firecracker 快照"指 VM 内存 + 设备状态快照 | 6 |
| Cloud Hypervisor | Cloud Hypervisor | 运行在 KVM 与 MSHV 上、基于 rust-vmm 的通用云负载 VMM（部分代码源自 Firecracker 与 crosvm），支持热插拔、迁移、Windows guest；Kata 的可选 hypervisor，CubeSandbox VMM 的上游。 | — | 6 |
| Kata Containers | Kata Containers | 把轻量 VM 包装为 OCI/CRI 容器运行时的项目，是 Kubernetes 通往 microVM 的路径。 | 启动额外开销 150–300 ms | 6 |
| PVM | PVM（SOSP'23；CubeSandbox 文档展开为 Pagetable-based Virtual Machine） | 构建在 KVM 之上、不依赖硬件虚拟化扩展的虚拟化框架（影子页表），用于在不暴露 /dev/kvm 的云 VM 内运行 microVM；未合入主线内核；AgentENV 提供实验性模式，CubeSandbox 作为正式部署路径（腾讯称已生产验证）。 | 与嵌套虚拟化（nested virtualization）是两条路线 | 6 |
| CubeSandbox | CubeSandbox | 腾讯开源的 KVM microVM 沙箱（VMM 为 Cloud Hypervisor 定制分支，推断），eBPF 网络（CubeVS）、XFS reflink 存储（CubeCoW），E2B 兼容；自报冷启动 < 60 ms，指模板快照恢复。 | 版本冲突已消解（v0.5.0 07-03、v0.6.0 07-24，最新 v0.7.2 09-24）；开源日期三说（附录 B C-11） | 6 |
| 完整 VM | full VM | 运行完整商用 OS 的虚拟机（QEMU），承载 Android、Windows、GUI 与图形负载。DSec 表 1 把 computer use 列在 microVM 档、把 COTS OS 与图形列在完整 VM 档；DSec 原文未出现 Windows（Windows 一例来自 WAA 等评测环境）。 | 与 microVM 对比：功能完整、启动与开销最高 | 7 |
| virtio-gpu | virtio-gpu | 半虚拟化 GPU，DSec 用于 GUI 应用、浏览器、游戏与 3D 渲染。 | — | 7 |
| qemu-in-docker | qemu-in-docker | 在容器里运行 QEMU 虚拟机的部署形态，ComputerRL、OSWorld 系、WAA 使用。 | 隔离边界是 VM，容器只负责打包与编排 | 7 |
| 云手机 / 云电脑 | cloud phone / cloud computer | 云端托管的 ARM 手机或桌面实例，产品侧（AutoGLM、AgentBay）常用。 | 训练集群多用 x86 Dockerized AVD，存在 sim-to-real 差距（推断） | 7 |
| redroid | redroid | 在宿主内核上以容器形式运行 Android 用户空间的方案，不需要 QEMU 或嵌套 KVM（Qwen-UI-Agent 采用）。 | 与 Dockerized AVD、qemu-in-docker 不同，隔离边界是容器而非 VM | 7 |
| 状态胶囊 | state capsule | CUA-Sandbox 把每条轨迹的私有可变状态封装、与共享的已初始化应用运行时分离的做法；权威状态存为私有增量，派生状态用私有命名空间，临时状态在激活时重建。 | 保留真实应用与原评估器，代价在隔离覆盖（依赖资源契约与绑定；无适配器的资源退回粗粒度私有后端）；不同于 MobileGym 以模拟换密度 | 7 |
| WebAssembly 沙箱 | WebAssembly (Wasm) sandbox | 在进程内执行生成代码的沙箱（Pyodide、Wasmtime），以线性内存隔离、以 WASI 能力模型授权（启动时无环境权限）；coze-loop 评测模块用基于 Deno 的 Pyodide。Pydantic Monty 是 Rust 编写的受限 Python 解释器（v1.0.0），不属于 Wasm 方案。 | 只适合窄场景，不提供完整 OS | 8 |
| 可信执行环境 | TEE（TDX / SEV-SNP / confidential GPU） | 把工作负载与基础设施运营方隔离并支持远程证明的硬件机制。 | 与沙箱正交：防运营方，以远程证明控制密钥释放；不防提示注入、供应链、拒绝服务与部分侧信道 | 8 |
| FnCall | FnCall | DSec 最轻的后端，承载 OJ 类脚本、编译、GPU kernel 等短小无状态任务；GPU FnCall 用 MIG 切分。 | 不提供隔离与完整 OS 功能（表 1 均为空心） | 8 |
| 受限令牌 | restricted token | Windows 上从某个用户令牌派生、去除部分特权与组的令牌；Codex 非提升模式与 srt（alpha）用它运行被沙箱的命令。 | 与 AppContainer 不同，本书核对的一手文档均未使用 AppContainer | 4 |
| 强制拒写路径 | mandatory deny paths | 即使所在目录可写也总被拒绝写入的文件与目录（shell 配置、git hooks 与配置、IDE 目录、Agent 配置、MCP 配置等）；srt 实现。 | 对信任移交的枚举式防御 | 4 |
| 应用内核 / 用户态内核 | application kernel / user-space kernel | 运行在宿主用户态、为应用实现系统调用的内核层，gVisor 的 Sentry 是代表。 | gVisor 文档用"application kernel" | 5 |
| Sentry | Sentry | gVisor 的应用内核组件，实现系统调用、信号、内存管理与缺页处理、线程模型。 | 不译 | 5 |
| Gofer | Gofer | gVisor 中随每个容器启动的宿主进程，经 9P 为 Sentry 提供文件访问。 | 启用 directfs 时 Sentry 可直接打开文件 | 5 |
| 安全容器运行时 | secure container runtime | 以 OCI 运行时接口替换 runc、提供更强隔离的运行时，如 gVisor（runsc）、Kata Containers。 | OpenSandbox 用此称谓；与"沙箱运行时"同义时以后者为准 | 5 |
| Docker socket | Docker socket（`/var/run/docker.sock`） | Docker 守护进程的控制接口；可访问者能以任意参数创建容器，效果上等同宿主 root。 | SandboxEscapeBench 难度 1 场景；o1 系统卡 CTF 事件 | 5 |
| 用户命名空间 | user namespace | 把容器内 root 映射为宿主非特权用户的 Linux 命名空间；CNCF 列为 runc 逃逸漏洞的缓解之一。 | DSec 是否启用未披露 | 5 |
| 嵌套虚拟化 | nested virtualization | 在虚拟机内部再运行 hypervisor 与虚拟机；云上运行 microVM 的前提之一。AWS 自 2026-02 在部分机型开放。 | 与 PVM 是两条路线；硬件辅助嵌套亦称 EPT-on-EPT | 6 |
| VMM | virtual machine monitor（虚拟机监控器） | 运行在宿主用户态、负责设备模拟与 VM 生命周期的进程，如 Firecracker、Cloud Hypervisor；与内核中的 KVM 配合。 | 首次写"VMM（虚拟机监控器）" | 6 |
| jailer | jailer | Firecracker 的隔离启动器，以 chroot、cgroup、网络命名空间与降权身份启动 VMM 进程。 | 不译 | 6 |
| VMGenID | Virtual Machine Generation Identifier | 快照恢复时变化的 16 字节随机代际 ID；Linux ≥ 5.18 据此重播种内核 PRNG。 | 不解决应用层状态复制 | 6 |
| 模板快照 | template snapshot | 在服务就绪（如健康探针通过）后对 microVM 做的快照，作为创建沙箱的起点；多数厂商的"冷启动"即从它恢复。 | 见 6.4.2、6.6.1 节 | 6 |
| 人机协同接管 | human-in-the-loop takeover | 产品沙箱经流式通道把画面推给人，由人接管 CAPTCHA、密码输入等步骤（AgentBay ASP）。 | 训练沙箱一般不需要 | 7 |
| golden image | golden image | 预装 OS、应用与代理服务的基准 VM 镜像，评测与训练从它克隆或恢复（WAA 30 GB）。 | 首次注"（黄金镜像，预配置的基准镜像）"，后文保留英文 | 7 |
| 能力模型 | capability model / capability-based security | 实例启动时没有环境权限（ambient authority），只能使用宿主显式授予的文件、函数或端点（WASI、CaMeL 的值级能力）。 | 与 OS 原语"在全能进程上做减法"相对；capability 首次注"能力" | 8 |
| 远程证明 | remote attestation | 远端验证方以密码学方式确认预期代码正在真实 TEE 中运行，据此决定是否发送密钥或敏感数据。 | 只证明"被度量的软件被正确实例化"，不证明其来源 | 8 |
| V8 isolate | V8 isolate | 在同一进程内由 V8 引擎隔离的 JavaScript 执行上下文；Cloudflare Dynamic Workers 以此作为 Agent 沙箱的轻量档。 | 与容器档 Sandboxes 并列 | 8 |
| 内核级工作区 | kernel-level workspace | 不用容器、以 mount namespace 与 chroot 等内核机制隔离的每任务工作目录（SWE-MiniSandbox）。 | 共享内核；作者自述不适合不可信代码 | 8 |
| 机密 VM | confidential VM (CVM) | 整台虚拟机运行在 TDX 或 SEV-SNP 等 TEE 中，内存对 hypervisor 与运营方加密。 | 与 microVM 沙箱可叠加（OpenShift 沙箱容器、Grimlock） | 8 |

### C. 八层架构：控制面、存储、状态

| 中文术语 | English | 定义（1–2 句，结合 Agent 沙箱语境） | 易混淆项/辨析 | 首次出现章节 |
|---|---|---|---|---|
| 八层参考架构 | eight-layer reference architecture | 本书对工业级 Agent 沙箱的分层：接入与 API、控制面、节点运行时、镜像与存储、状态管理、密度与资源、网络与出站、RL 集成与完整性。 | 层名以"用词规范"第 4 条为准 | 9 |
| 控制面 | control plane | 负责认证、放置、健康检查、配额与路由解析的集群服务；DSec 为无状态 IAM/apiserver/放置引擎/watcher。入口代理常同时承担数据面转发（DSec apiserver、AgentENV gateway），agent-sandbox 把数据面拆给独立 router。 | 与"节点运行时"（每机 edge、envd）区分；与"数据面"对举 | 9 |
| power-of-k-choices | power-of-k-choices | 随机抽样 k 个合格节点、选负载最低者的放置算法，DSec 用来避免羊群效应（见 DSec §7）。 | DSec 未披露 k 值与"负载"定义；§3.2 只写"随机采样少数几个合格节点" | 9 |
| 云突发 | cloud bursting | 本地利用率超阈值（DSec 为 80%）时把部分创建请求卸载到云上 VM。 | 仅覆盖镜像可上云的任务（DSec 约 70% 容器任务） | 9 |
| 预热池 | warm pool | 预先启动的沙箱、进程或设备池，用于缩短创建/恢复延迟。分集群级（agent-sandbox SandboxWarmPool + SandboxClaim）与节点级（AgentENV 预启动的 Firecracker 进程、网络槽位、块设备；DSec GPU FnCall 的 Python 进程池，§7）。 | 与"快照恢复"互补；产品场景模板少，预热池最有效；低扇出训练负载下按镜像建池代价高（推断） | 9 |
| 放置引擎 | placement engine | DSec 控制面中为新沙箱选择节点的组件：先过滤（健康、后端、硬件），再以 power-of-k-choices 排序。 | 与 K8s 的 kube-scheduler 职责相近，但不依赖持久状态 | 9 |
| 数据面 | data plane | 把命令执行、文件操作与流式 I/O 送达目标沙箱的流量路径。 | 与控制面对举；DSec、AgentENV 由同一入口组件承担，agent-sandbox 由独立 router 承担 | 9 |
| 羊群效应 | herding | 大量并发决策基于同一份快照涌向同一个"最空闲"节点。 | power-of-k 与本地在途叠加用来避免它（DSec §7） | 9 |
| 在途负载 | in-flight load | 已做出放置决策、但尚未反映在 watcher 快照中的负载。 | DSec 由各放置实例本地叠加，不跨实例协调（§7） | 9 |
| 路由绑定 | sandbox-to-node binding | 记录沙箱位于哪个节点的映射；AgentENV scheduler 保存在内存中。 | DSec 以沙箱 ID 编码 edge 代替绑定表 | 9 |
| 领用 | claim | 从预热池取出一个就绪沙箱交给工作负载（agent-sandbox SandboxClaim；Cua 文档 2026-10-02 读取时有"a claim reserves a sandbox for a workload"，10-04 版 How sandboxes work 页未见，见附录 B C-40）。 | 与"预热池"成对 | 9 |
| 自定义资源 | Custom Resource Definition（CRD） | K8s 的扩展对象类型；agent-sandbox 定义 Sandbox 等四个 CRD。 | 首次写"自定义资源（CRD）" | 9 |
| 领导者选举 | leader election | 多副本控制器中只让一个实例活跃的机制。 | agent-sandbox 示例控制器 1 副本 + 领导者选举 | 9 |
| API 优先级与公平性 | API Priority and Fairness（APF） | kube-apiserver 按优先级分配并发席位的机制。 | agent-sandbox 建议领用速率超过约 50 次/秒时启用隔离 | 9 |
| 规模单元 | scale unit | DSec 的部署单位，单元内约 160 个节点，多个单元共享 3FS。 | 论文未披露单元总数 | 24 |
| overlayfs | overlayfs | Linux 联合文件系统，多个只读 lowerdir 与一个可写 upperdir 叠加；DSec 在创建时动态组装 lowerdir。 | 与块级分层（overlaybd）不同：前者是文件级 | 10 |
| 可组合层 | composable layers | DSec 把基础镜像、workspace、toolkit 作为独立版本化的只读层按需叠加，使重建复杂度从 O(m·N) 降到 O(m)。 | 与 Docker 镜像层不同：层在创建时动态选择 | 10 |
| EROFS | EROFS | 面向只读场景的压缩文件系统，可只读取并解压所需块；DSec 用作不可变层格式。 | 与 ext4/XFS 可写文件系统对照 | 10 |
| overlaybd | overlaybd（DADI） | 源自阿里 DADI 的块级分层镜像格式，支持按需远端读取；AgentENV 仓库中有其 Rust 版（DSec 称 "Rust port of OverlayBD"），DSec 的 microVM 存储路径使用了该组件。 | 块设备级，不是文件系统 | 10 |
| LSMT | LSMT（log-structured merge tree layered format） | AgentENV 中 overlaybd 的分层格式：多个不可变压缩只读层之上一个可写层，zstd 压缩、CRC32C 校验。 | 与数据库 LSM-tree 同源概念，此处用于块映射 | 10 |
| ublk | ublk | Linux 用户态块设备框架；AgentENV 以它把 overlaybd 镜像暴露为 `/dev/ublkbN`，并用于内存快照恢复。 | 与 NBD（网络块设备）相近，但为本地用户态实现 | 10 |
| 懒加载 / 按需加载 | lazy loading / on-demand loading | 沙箱启动时只取实际访问的数据块；DSec 从 3FS 按需读取，AgentENV 以本地盘为有界缓存。 | 与"预先拉取"（eager pull）对照；访问密度低于约 80% 时懒加载占优（SOCI） | 10 |
| 预先拉取 | eager pull | 沙箱启动前把镜像全部下载到本地；DSec §8.2 的冷态对照组"Docker Pull (cold)"。 | 与按需加载对照 | 10 |
| 访问密度 | access density | 运行时实际访问的数据占镜像的比例；SOCI 报告低于约 80% 时懒加载占优。 | DSec 表 3 为 4.2%–13.3% | 10 |
| 有界缓存 | bounded cache | 以本地盘为容量受限的缓存，按水位线淘汰冷数据（AgentENV）。 | 不是镜像的完整副本 | 10 |
| 二级缓存 | second-level local filesystem cache | DSec 的 ublk 以 256 KiB 块取回 OverlayBD 数据后存入的本地文件系统缓存。 | — | 10 |
| whiteout（删除标记） | whiteout | overlayfs 中表示"下层文件已在上层删除"的标记；DSec 合并层时保留其语义。 | — | 10 |
| 早释放策略 | early-release policy | 主动删除后续步骤不太可能复用的镜像（快手 KAT-Coder-V2.5）。 | — | 10 |
| 运行时镜像 | runtime image | FlacIO 提出的镜像抽象，表示容器根文件系统的内存态。 | — | 10 |
| ztoc | ztoc | SOCI 的外部索引，把文件映射到压缩层中的字节区间，作为独立 OCI referrer 制品存放。 | 无需转换镜像 | 10 |
| overlaybd 原生制品 | overlaybd-native artifact | 经 OCI Referrers API 发现的预先转换好的 overlaybd 镜像（如 `obdconv` 产物），AgentENV 优先使用。 | 取不到则在节点本地转换 | 10 |
| 附加块盘 | extra drive | AgentENV 为沙箱附加的只读或可写块设备。 | 块级的组合单位 | 10 |
| 3FS | Fire-Flyer File System | DeepSeek 的分布式文件系统，DSec 从中按需加载镜像数据（写留本地、读按需成批、元数据本地化）。 | — | 10 |
| 快照 | snapshot | 沙箱某时刻内存和/或磁盘状态的副本；可全量或增量。 | 见用词规范第 3 条 | 11 |
| 检查点 | checkpoint | 作为恢复点保存的（通常增量的）快照；K3 报告的增量检查点只保存脏页。 | "C/R"= checkpoint/restore | 11 |
| 增量快照 | incremental / diff snapshot | 只记录自上次快照以来变化的内存页或磁盘块；AgentENV 把脏页写成新的 overlaybd 内存层。 | 与全量快照对照 | 11 |
| fork（分叉） | fork | 从运行中沙箱派生多个共享父状态的子沙箱；E2B（2026-07 起）与 AgentENV 均提供 `POST /sandboxes/{id}/fork`，count 1–100（AgentENV 限同节点）。 | 与 pack_diff（恢复为新沙箱的磁盘检查点）不同 | 11 |
| 暂停 / 恢复运行 | pause / resume | 停止并保留沙箱状态、之后继续；DSec 在 GPU 抢占期间暂停沙箱以回收内存。 | 与"休眠"区分，见用词规范 | 11 |
| pack_diff | pack_diff | DSec 的增量磁盘快照接口，Agent 可随时把沙箱打包为可复用的新环境，"无需单独的镜像构建流水线"（§6.1）。 | 是"环境构建"手段，也是完整性风险点 | 11 |
| 写时复制 | copy-on-write (CoW) | 共享同一份数据直到首次写入才复制；VM fork、块快照、BranchFS 的基础。 | — | 11 |
| 模板 fork | fork from template | 从冻结的模板实例派生新沙箱（Catalyzer sfork、DeltaBox DeltaCR）。 | 快于"从转储恢复"（CRIU 式） | 11 |
| 沙箱外副作用 | external side effects | Agent 对远程 API、数据库、支付等沙箱外系统造成的改变；本地快照无法回滚。 | 第 12 章主题 | 12 |
| statepoint | statepoint | Planarian 的抽象：本地增量快照 + 远端服务补偿动作，支持 snapshot/rollback/fork。 | 比单纯快照多出"补偿"部分；补偿动作的来源与远端 fork 语义在摘要中未交代（正文未读） | 12 |
| 语义事务 | semantic transaction | Cordon 提出：可逆变更在影子状态中执行，对外动作放入 effect outbox 暂存，校验后再提交。 | Cordon（arXiv 2606.17573）提出；任务级事务 T=⟨scope, intents, R, W, D, E, O, G, A, status⟩：本地变更在影子状态中执行，外部动作进入 effect outbox，验证引擎按血缘、权限与约束整体判断后提交；见第 12 章 | 12 |
| 可缓冲 / 可补偿 / 不可逆 | bufferable / compensable / irreversible | Atomix 对副作用的三分类：可暂存到提交时、可事后补偿、必须门控。Atomix v1 按两条正交轴分类：效果类型（可逆 / 有代价的可逆 / 不可逆）与可见性（bufferable / externalized）；v2 合并为 bufferable、reversible、irreversible-gated 三类（irreversible-gated："hold the call at the adapter, return a queued-acknowledgment, and fire only on commit"）。 | 第 12 章的分析框架 | 12 |
| staging（暂存层） | staging | YoloFS 把所有修改重定向到待提交/拒绝的层，配合快照与渐进权限。 | 与 overlayfs upperdir 思路相近，但带人工确认 | 12 |
| 语义回滚攻击 | semantic rollback attack | ACRFence 定义：恢复后 LLM 生成略不同请求导致动作重放、权限复活等问题。 | 防御为恢复时强制 replay-or-fork 语义 | 12 |
| effect outbox（效果待发箱） | effect outbox | Cordon 中暂存外部动作的队列；每个条目记录 sink、载荷句柄、血缘句柄、权限状态、幂等键与放行状态，验证通过并提交后才放行。 | 与数据库"transactional outbox"模式同源（推断） | 12 |
| 影子状态 | shadow state | Cordon 中事务作用域内的本地视图，文件写、删除与命令改动施加于此，提交时提升到真实工作区、中止时丢弃。 | 与 YoloFS staging 思路相近 | 12 |
| 血缘 | lineage | Cordon 中结果、本地变更与外部效果之间的语义依赖图 G；秘密派生的结果即使不含秘密字面值也被追踪。 | — | 12 |
| 门控 | gating | 把不可逆效果扣在适配器或 outbox 中，待提交谓词成立或人工批准后放行。 | 不可逆效果的处理方式，区别于补偿；Atomix v2 §2.3 原文见上 | 12 |
| 动作重放 / 权限复活 | action replay / authority resurrection | ACRFence 定义的两类语义回滚攻击：恢复后以新参考号重发不可逆动作；回退到"刚获批准"的状态复用批准。 | 防御：效果日志 + replay-or-fork（论文尚未实现） | 12 |
| epoch / frontier | epoch / frontier | Atomix 的进度概念：epoch 为全序单调逻辑时间戳；frontier 为每资源的单调游标，确认不会再有更早工作后推进，事务据此结算。 | — | 12 |
| 作者日期 / 提交日期 | author date / commit date | git 中一次提交的两个时间戳：前者为改动写成时由作者本地设定，后者为提交进入当前历史时生成（合入、变基时更新）。 | 判断"谁先谁后"应以提交日期为准，且仍可被改写；第 25 章据此更正"发布前提交"一说 | 25 |
| 轮次级暂停 | per-turn pause | 在 Agent 每一轮等待模型推理时暂停沙箱（K3 对 AgentENV 的用法）。 | 与"作业级暂停"（DSec 在 GPU 作业被抢占时暂停）对举 | 25 |

### D. 密度与资源

| 中文术语 | English | 定义（1–2 句，结合 Agent 沙箱语境） | 易混淆项/辨析 | 首次出现章节 |
|---|---|---|---|---|
| 超售 | overcommit | 分配给沙箱的资源总和超过物理资源；Agent 负载 CPU 稀疏，"天然适合超售"。 | AgentENV 超售比 6.5×（K3，归因写时复制与页缓存）与 9.6×（README，归因内存气球）冲突；口径区分见第 13 章边栏（名义 / 峰值 / 驻留超售比） | 13 |
| virtio-pmem + DAX | virtio-pmem with DAX | 把文件访问直接映射到宿主页、不复制进 guest 内存，同宿主 microVM 共享一份页缓存；DSec 用于只读层。 | 代价：冷访问同步缺页、struct page 元数据占用 | 13 |
| DAMON | DAMON (Data Access MONitor) | Linux 访问监控框架，采样页访问位找出冷页并经回收路径驱逐；DSec 用于可写盘。 | 与 balloon 配合 | 13 |
| 空闲页上报 | free page reporting (FPR) | guest 周期性扫描伙伴分配器并主动把空闲页（默认 order-9）还给宿主。 | virtio-balloon 的功能之一 | 13 |
| 内存气球 | memory balloon (virtio-balloon) | guest 内驱动按宿主要求"充气"占用并归还内存；也是空闲页上报的载体。AgentENV 开源代码中目标充气为 0、仅开启空闲页上报。 | FPR 是主动上报，balloon 是按需回收 | 13 |
| 页缓存共享 | page-cache sharing | 多个沙箱共享同一份只读数据的宿主页缓存（DSec 用 pmem DAX；AgentENV 让同一内存快照的沙箱共享 ublk 设备）。 | 私有可写数据无法共享，只能回收 | 13 |
| SCHED_IDLE | SCHED_IDLE | Linux 最低优先级调度策略，DSec 让尽力而为（BE）沙箱以此运行。 | 单独使用挡不住同核超线程干扰 | 13 |
| 核心调度 | core scheduling | Linux 功能，保证同一物理核的兄弟超线程只运行互信的任务；DSec 为延迟敏感（LS）沙箱开启。 | 不要写"7.4 倍改进"（附录 B X-02） | 13 |
| mm-template | memory template | TrEnv/TrEnv-X 的内核对象，保存页表与布局元数据而不复制内存内容；快照页置于 CXL（直接访问）或 RDMA（按 4 KB 缺页换入）远端内存池，写时本地分配。 | 与本地快照不同：跨节点共享 | 13 |
| 内存压缩 | memory compression | AgentZip 利用模板与跨沙箱冗余，在 LLM 等待期压缩沙箱内存。 | 与去重（Medes）同属一脉 | 13 |
| 时间积分内存 | time-integrated memory | 内存占用对时间的积分，衡量一段时间内的平均可用量；与峰值内存（决定 OOM 风险）区分。DSec 的 DAMON + FPR 降前者不降后者。 | 不与峰值降幅相加或比较 | 13 |
| 延迟敏感 / 尽力而为 | latency-sensitive (LS) / best-effort (BE) | DSec 的沙箱 CPU 分级：BE 以 SCHED_IDLE 运行，LS 开启核心调度。 | 判定标准未披露 | 13 |
| 沙箱自有内存 | sandbox-owned memory | AgentZip 的统计口径，指不与模板或其他沙箱共享的内存。 | 8.7× 的分母 | 13 |
| 投机预热 | speculative prewarming | 在 LLM 生成过程中预测工具调用并提前启动沙箱（SpecBox）。 | 与预热池（常驻）相对 | 13 |
| 名义 / 峰值 / 驻留超售比 | nominal / peak / resident overcommit ratio | 本书定义：请求值之和、峰值之和、含暂停沙箱的名义内存之和，分别除以物理内存。 | 报告超售比须注明口径 | 13 |

### E. 网络、出站与供应链

| 中文术语 | English | 定义（1–2 句，结合 Agent 沙箱语境） | 易混淆项/辨析 | 首次出现章节 |
|---|---|---|---|---|
| 出站 | egress | 从沙箱流向外部的网络流量及其控制；2026 年工业做法收敛为默认拒绝 + 包仓库白名单。 | "出网"仅作口语 | 14 |
| 默认拒绝 | default-deny | 未明确放行的出站一律拒绝。 | "沙箱网络模式"标签不等于默认拒绝（AgentCore DNS 隧道）；Modal、E2B、AgentENV 等平台默认放行，默认拒绝须由调用方显式开启 | 14 |
| 白名单 | allowlist | 允许访问的域名、IP 或服务列表；DSec 用每沙箱 eBPF 按 IP/端口/协议执行。规则冲突时的优先级各家不同：sandbox-runtime、Docker 拒绝优先，E2B、AgentENV 放行优先。 | 域名级白名单不检查内容，可被 domain fronting 绕过 | 14 |
| 阶段化网络策略 | stage-dependent network policy | 按任务阶段（setup、rollout、测试）动态切换的网络权限；DSec 由训练框架下发，Codex cloud 仅 setup 可联网。 | 属 RL 任务定义的一部分；E2B（updateNetwork）与 AgentENV（PUT …/network）也支持运行时改写出站规则，Modal 有 Alpha 阶段的运行时出站策略接口，区别在于 DSec 以"镜像服务/包管理器"表达、由训练框架驱动，E2B 类接口以主机/CIDR 表达、由调用方改写 | 14 |
| 凭据注入代理 | credential-injecting egress proxy | 在沙箱外代理处附加真实凭据，沙箱内只持有 scoped token 或不持有凭据（Cloudflare、Docker Sandboxes、Claude Code on the web、E2B（`network.rules` 与 `Secret.fill`，出站代理转发时解析）、CubeSandbox（CubeEgress 追加 header）、OpenSandbox（Credential Vault，需显式开启透明 MITM））；Cowork 为宿主 keychain + 按会话 scoped token，另以 VM 内 MITM 代理只放行本会话 token。 | 与"凭据在沙箱内"（Manus）对照 | 14 |
| SSRF | server-side request forgery | 诱使服务端代替攻击者发出请求；MCP 规范建议用出站代理防 SSRF，ExploitGym 中 Agent 经 SSRF 借 Artifactory 出站。 | 云元数据地址 169.254.169.254 是典型目标 | 14 |
| 域前置 | domain fronting | 利用 TLS SNI/HTTP Host 等差异，让流量看似访问白名单域名、实际到达他处；srt 文档列为已知局限。 | 与"借白名单域名外传"（api.anthropic.com + 攻击者 key）是两类 | 14 |
| 解析后地址检查 | resolved-address check | 代理在拨号前解析被允许的主机名，丢弃落在回环、链路本地、元数据、本机地址等拒绝集合中的地址，只拨通过检查的地址、不二次查询；sandbox-runtime 实现。 | 防"被允许的名字指向内网"；与 DNS 重绑定防护同源 | 14 |
| TLS 拦截 / TLS 终止 | TLS interception / termination | 出站代理以沙箱信任的 CA 终止 TLS，从而看到明文、按方法与内容过滤并注入凭据；Cloudflare 每沙箱临时 CA、sandbox-runtime 实验性 tlsTerminate。 | 代价是信任集中于代理；mTLS 与证书钉扎客户端无法终止 | 14 |
| 出站探针 | egress canary | 在模板构建或基础设施变更后，从沙箱对受控外部端点发起多协议请求，验证"离线"或白名单是否如声明生效。 | 本书建议的做法，非业界标准术语；评测前的同类检查见"出站预检" | 14 |
| DNS 隧道 | DNS tunneling | 把数据编码进 DNS 查询以绕过出站控制；AgentCore Sandbox 模式曾被利用。 | 训练沙箱的 DNS 处理未见一手文档；产品侧另有"预批准 DNS 命令"（Claude Code，2025-08）与"系统解析器不受围栏"（srt Windows/macOS）两种 DNS 旁路 | 14 |
| 包代理 / 镜像源 | package proxy / registry mirror | 代替沙箱访问 npm、PyPI、Go 等仓库的中继；能按需取上游的"remote repository"本身就是出站通道。 | 2026 年最薄弱的出站点（Artifactory、Go module proxy）；按能否代取上游分为预填充镜像、拉取式缓存、通用转发三种形态（第 15 章）；与容器"镜像"（image）区分 | 15 |
| 供应链侧沙箱 | supply-chain-side sandbox | 把包代理、registry 镜像作为独立加固对象：只读、预填充、不可代取任意 URL、按包（名称、版本、哈希）放行、管理 API 不可达、构建期与运行期分离。 | 本书提出的章节主题 | 15 |
| 反向供应链风险 | reverse supply-chain risk | Agent 向公共仓库发布恶意包（Anthropic/Irregular 评测中，模型注册虚构公司搭建说明引用的不存在包名并发布到 PyPI，约一小时内被 15 个真实系统运行；一手）；要求通往 registry 的出站只读。 | GET-only 挡不住经查询字符串的外传 | 15 |
| 预填充镜像 | pre-populated mirror | 内容在任务开始前确定、运行期只读提供、未命中返回 404 而不访问上游的包镜像。 | 本书建议训练与评测运行期只用此形态 | 15 |
| 拉取式缓存 | pull-through cache | 未命中时代沙箱向上游取回并缓存的包代理，如 Artifactory remote repository、Go 模块镜像。 | 出站目标由沙箱请求决定，属出站通道 | 15 |
| 依赖混淆 | dependency confusion | 某处引用了公共仓库中不存在（或仅私有存在）的包名，抢先注册该名即可让引用方执行攻击者代码。 | Anthropic/Irregular 事件中模型以此手法发布 PyPI 包（本书据事件描述归类） | 15 |
| slopsquatting | slopsquatting | 攻击者抢注大模型幻觉出的包名。 | Spracklen 等：生成代码引用的包中 19.7% 为幻觉，43% 在 10 次查询中全部重复（2024 年模型） | 15 |
| 按包白名单 | per-package allowlist | 以（名称，版本，哈希）为最小单位、通常来自构建期锁文件的放行列表。 | 与域名级白名单对照：后者挡不住被允许域名之内的出站取回 | 15 |

### F. 接口与标准

| 中文术语 | English | 定义（1–2 句，结合 Agent 沙箱语境） | 易混淆项/辨析 | 首次出现章节 |
|---|---|---|---|---|
| E2B 协议 | E2B protocol / E2B-compatible API | E2B 的沙箱生命周期 HTTP API 与 SDK（创建、exec、文件、暂停/恢复、快照、fork、出站规则）；AgentENV、ACS、AGS、CubeSandbox 均宣称兼容（实现者自述，无一致性测试），已成事实标准。 | 有主机/CIDR 级出站规则与单沙箱暂停；缺少语义级网络策略、阶段、作业分组、完整性约束等（第 16 章表 16-2） | 16 |
| envd | envd | E2B 的沙箱内守护进程，负责 exec、文件与健康检查；AgentENV 由 tools-image/ 从 e2b-dev/infra 编译后放入 guest 的只读 tools 驱动器，端口 49983；节点侧经 Rust 客户端库（thirdparty/envd）以 gRPC 通信。 | 与 DSec 的 aether/chronus、OpenSandbox 的 execd 同层；E2B 侧接口为 proto 定义的进程/文件服务加 HTTP（/init、/files、/freeze 等） | 16 |
| OpenEnv | OpenEnv | Meta-PyTorch 与 Hugging Face 发起的环境接口规范，client/server 形式提供 Gym 式 `reset()/step()/state()`，MCP 为一等公民。 | 位于"环境语义层"，E2B 位于"沙箱生命周期层" | 16 |
| MCP | Model Context Protocol | Agent 与工具/数据源的协议；其 2025-11-25 安全最佳实践要求在最小默认权限沙箱中执行本地 server（SHOULD）。 | 是协议而非沙箱实现 | 16 |
| Harbor | Harbor | 与 Terminal-Bench 2.0 一同发布的框架，把任务、harness、沙箱三者解耦；`network_mode` 有 public/allowlist/no-network 三档。 | 源码确认（config.py，2026-10-03）：环境默认 public；[agent]/[verifier] 可分阶段覆盖；旧字段 allow_internet 已弃用；后端是否照办因后端而异（loom #2189） | 16 |
| OWASP Agentic Top 10 | OWASP Top 10 for Agentic Applications 2026 | 2025-12-09 发布的智能体威胁分类 ASI01–ASI10；ASI05（Unexpected Code Execution (RCE)）缓解建议"从不以 root 运行，在沙箱化容器中运行代码"，ASI10 建议"受限执行环境（如容器沙箱）"与急停开关。 | 是分类而非强制标准 | 23 |
| 生命周期层 | lifecycle layer | 规定单台沙箱创建、暂停、恢复、销毁、超时、出站规则与沙箱内执行的接口层（E2B 协议、libdsec、OpenSandbox 生命周期与执行 API、agent-sandbox CRD）。 | 与"环境语义层"相对；八层架构第①层的下半部分 | 16 |
| 环境语义层 | environment-semantics layer | 规定一个环境怎样被 rollout 使用（重置、执行一步、返回观察与奖励）的接口层（OpenEnv、verifiers、NeMo Gym、Harbor 任务格式）。 | 不规定沙箱生命周期 | 16 |
| 聚合层 | aggregation layer | 把多家沙箱后端包装成统一接口的一层（OpenAI Agents SDK provider、Inspect `SandboxEnvironment`、Harbor 云后端）。 | 不实现沙箱 | 16 |
| provider | provider | 聚合层中可替换的沙箱后端实现；Agents SDK 内置 7 家。 | 不译 | 16 |
| Manifest | Manifest | OpenAI Agents SDK 描述 Agent 工作区的抽象：挂载文件、输出目录、外部存储数据。 | 不译；与容器镜像 manifest 区分 | 16 |
| 再水化 | rehydration | 把外置的 Agent 状态在新容器中恢复并从检查点继续（Agents SDK）。 | 恢复的是 Agent 状态，不一定含沙箱内存 | 16 |
| harness 与计算分离 | harness/compute separation | Agent 循环与凭据留在可信侧，模型生成的代码在独立沙箱中执行；出自 OpenAI Agents SDK 原文"Separating harness and compute helps keep credentials out of environments where model-generated code executes"。例：Agents SDK、Claude Managed Agents 自托管、Perplexity SPACE。 | 第 21、27 章用作对照；与"凭据位置"一词配合使用 | 16 |
| 租约 | lease | 本书建议中的作业级分组单位，用于按组暂停、恢复、销毁沙箱。 | 本书建议用语，非现行接口 | 16 |
| 能力声明 | capability declaration | 后端或平台以机器可读形式声明自身支持的能力（如 Harbor `EnvironmentCapabilities` 的 `dynamic_network_policy`、`network_allowlist_hostnames`），供上层在运行前校验任务需求。 | 与"能力协商"（双方交换后选定）区分；本书建议的能力查询接口见 16.8 节 | 16 |
| 实践指南（网络安全标准实践指南） | TC260 Cybersecurity Standard Practice Guide (TC260-PG) | TC260 秘书处组织制定和发布的"标准相关技术文件"，编号 TC260-PG-年份+序号；2026 年两份智能体实践指南含沙箱条款。 | 不是国家标准，无强制力；不要称"推荐性"（专指 GB/T）；与强制性国家标准（GB，编号带 Q 的计划）区分 | 23 |
| 强制性国家标准 | mandatory national standard (GB) | 由国家标准委下达计划、必须执行的国家标准；智能体领域首项为《智能体应用安全基本要求》（计划号 20263116-Q-252，起草中）。 | 与推荐性国标（GB/T）、实践指南区分 | 23 |
| 运行环境安全管理 | runtime environment security management | TC260 开发安全指南征求意见稿第 8 章 n）项的条款名，要求把推理、工具执行、代码执行置于"沙箱、容器或其他隔离边界内"。 | 与信通院评估中能力意义的"运行环境"（硬件适配、弹性扩展）不同 | 23 |
| 最小沙箱条款 | minimal sandbox clauses | 本书第 23 章提出的十条建议条款（S1–S10），作者观点，非现行标准。 | 不是任何机构的文本 | 23 |
| AAIF Sandbox 阶段 | AAIF Sandbox phase | AAIF 2026-09 引入的项目成熟度入门级（类比 CNCF Sandbox，笔者类比）。 | 与执行沙箱无关 | 23 |

### G. Agent RL 与环境

| 中文术语 | English | 定义（1–2 句，结合 Agent 沙箱语境） | 易混淆项/辨析 | 首次出现章节 |
|---|---|---|---|---|
| rollout | rollout | 策略模型与环境交互直至结束的一次采样过程，产物为轨迹；RL 训练的主要沙箱负载。 | 不译；与"推理请求"不同，一次 rollout 含多轮推理与工具调用 | 1 |
| Agent 循环 | agent loop | "模型输出动作 → 工具执行 → 观察返回模型"的循环；DSec 在 V4.1 前 GPU 抢占会丢失它。 | veRL 的 AgentLoop 是具体实现名 | 17 |
| harness | harness | 驱动 Agent 循环、调用工具并与环境/打分器交互的外壳程序（如 DeepSeek Harness、Terminus-2）。 | 与 scaffold 常混用；本书 harness 侧重评测/训练外壳，scaffold 侧重 Agent 自身框架 | 17 |
| 脚手架 | scaffold | Agent 的提示、工具与控制流框架（OpenHands、SWE-agent）；阶跃在多种 scaffold 上训练以防过拟合。 | 见 harness | 17 |
| 白盒 / 黑盒 / harness 化 RL | white-box / black-box / harnessed RL | 三种集成模式：训练器控制每一步；代理层从已发布 Agent 捕获 token 级轨迹；harness 掌控循环。 | MiniMax Forge 同时支持前两种 | 17 |
| 异步 RL | asynchronous RL | 生成与训练解耦、rollout 与训练并行推进的训练方式（slime、ROLL Flash、AReaL、DORA、CWM、prime-rl）；粒度可分环境级、轨迹级与多版本流式。 | 带来陈旧轨迹问题（CWM 丢弃超 100 步者） | 17 |
| 抢占 | preemption | GPU 训练作业被调度器中断；要求 rollout 状态存放在可抢占 GPU 池之外。 | 与沙箱被驱逐区分 | 17 |
| rollout 状态归属 | rollout state ownership | 由谁持有进行中 rollout 的完整状态；DSec 自 V4.1 起由 agent sandbox 与 worker container 共同作为唯一事实来源。 | 训练沙箱与产品沙箱的分水岭（第⑧层） | 17 |
| token 一致性 | token consistency / token-in-token-out | 保证训练所用 token 序列与推理实际采样的序列一致（token 进 token 出，TITO）；veRL 用 token API 代替 chat completion，快手 Gateway Server 直连 /generate，ProRL Agent 以 token ID 为规范表示。 | 重新分词漂移可影响大量样本 | 17 |
| rollout 即服务 | rollout-as-a-service | 把 Agent 循环、环境执行与评分做成独立 API 服务，训练器只提交请求、取回轨迹（NVIDIA ProRL Agent）。 | 与"沙箱即服务"不同：前者持有循环状态，后者只提供执行环境 | 17 |
| 心跳容错 | heartbeat-driven fault tolerance | 组件周期性上报心跳，编排层据此终止并注销不健康实例；slime 用于推理侧 rollout 服务器。 | 与沙箱节点心跳（AgentENV 调度器）覆盖的故障域不同 | 17 |
| 冗余 rollout | redundant rollout | 多启动一些环境或轨迹，收够目标数即终止在途者，以缓解慢故障与停止故障（ROLL Flash、RollArt）。 | 浪费沙箱时间，并可能系统性地丢掉长轨迹 | 17 |
| 分阶段超时 | phase-aware timeout | 只在活跃阶段（init、run、eval）累计耗时、不计排队等待的超时（ProRL Agent）。 | 与墙钟超时对照：后者会把排队误判为环境故障 | 17 |
| 陈旧度 | staleness | 生成某条轨迹的策略版本落后于当前版本的程度；异步 RL 用窗口约束（RollArt 的 α、DORA 的 K、CWM 的 100 步）。 | 与沙箱"空闲时长"是两把尺子 | 17 |
| 唯一事实来源 | single source of truth | 故障后其他各方向其对齐的那份状态；DSec 自 V4.1 起由 worker container 与 agent sandbox 共同担任 rollout 状态的唯一事实来源。 | 见"rollout 状态归属" | 17 |
| 持久执行 | durable execution | 把每步结果写入事件历史、故障后重放并跳过已完成步骤的执行方式（Temporal 类引擎）；DSec V4.1 前的命令日志回放与之同构（推断）。 | 与"状态外置后重连"不同 | 17 |
| env.reset | env.reset | 环境重置（拉镜像 + 起容器）；RollArt 记录约每十次迭代出现一次环境超时，超时迭代中 env.reset 单独占 rollout 时间 78%。 | 是可靠性指标，不只是延迟 | 17 |
| 可验证环境 | verifiable environment | 带确定性验证器（测试、规则）可自动判定成功的环境。 | 与"模型评判"（GenRM、LLM-as-judge）对照 | 18 |
| 环境构建 | environment construction | 为任务生成可执行镜像与验证器的过程，越来越由 Agent 自动化（AutoBuilder、RepoAgent/Activ、Terminal-Gym、pack_diff）；一般分来源、筛选、构建、验证、清理、发布六阶段（第 18 章图 18-1）。 | 构建流水线本身是 reward hacking 攻击面 | 18 |
| 构建成功率 | environment-construction success rate | 环境构建尝试中产出合格可验证环境的比例；各家分母与判据多未写明。 | 快手 16.5%→57.2%、阶跃 40% 均未写明分母；GLM-5 > 90% 为合成终端任务的 Docker 构建准确率 | 18 |
| fail-to-pass / pass-to-pass | fail-to-pass (F2P) / pass-to-pass (P2P) | F2P：修复前失败、修复后通过的测试，用于揭示缺陷；P2P：修复前后都应通过的回归测试。 | 不译，首次注中文 | 18 |
| RL 环境市场 | RL environment market | 向实验室出售环境、任务与克隆网站的供应商市场；以定制合同为主。 | 与"沙箱即服务"不同：环境是商品，沙箱是交付介质 | 22 |

### H. reward hacking、评测与事故

| 中文术语 | English | 定义（1–2 句，结合 Agent 沙箱语境） | 易混淆项/辨析 | 首次出现章节 |
|---|---|---|---|---|
| reward hacking（奖励投机） | reward hacking | 模型以非预期途径获得奖励，"任务看起来通过了，但答案来自非预期渠道"（DSec）。 | 与 specification gaming（规约博弈）近义；本书统一用 reward hacking | 2 |
| 取回型 / 篡改型 hacking | retrieval-style / tampering-style hacking | 取回型从既有答案源取回：沙箱内取回（挖 .git、翻日志）不需出站，出站取回（查上游、借镜像源）需出站；篡改型可离线（改测试、重载运算符、改评估器）。 | 决定出站控制能挡住哪一类 | 19 |
| 环境篡改 | environment tampering | 模型修改环境、平台或评测组件（覆盖 /bin/bash、伪造 chronus RPC、改浏览器存储）。 | 属篡改型 | 19 |
| 安全退出 | safe exit / abort | 让模型在任务损坏或无解时安全停止；ExploitGym 898 个任务中 198 个无解是根因之一。 | ImpossibleBench 中 abort 选项显著降低作弊 | 19 |
| CoT 监控 | chain-of-thought monitoring | 监控模型推理过程以发现越界意图；OpenAI 事后要求对 GPT-5.6 Sol 能力及以上模型的所有工具型 RL 训练与评测启用；Astra 级模型另覆盖推理负载。 | 与轨迹级监控互补 | 19 |
| 评测沙箱 | evaluation sandbox | 运行基准与能力/安全评测的隔离环境；2026 年事件表明评测环境本身是安全边界。 | 隔离级别应写入评测规格（见第 20 章表 20-3"评测沙箱规格"） | 20 |
| 评测混杂因素 | evaluation confounder | 容器镜像、依赖缓存、网络访问、超时等改变成败的环境变量（Terminal Agents 综述）。 | 解释了跨 harness 分数不可比 | 20 |
| 构建完整性 | build integrity | 确保构建流水线不把参考答案、未来历史、凭据或可出站通道带进环境的一组措施（分账号、打包前清理、按阶段切网络、泄漏探测）。 | 对应第 19 章"沙箱内取回" | 18, 19 |
| 构建者与运行者分离 | builder/runtime separation | 构建环境的 Agent 与在环境中运行的 Agent 使用不同账号、凭据与日志命名空间（DSec §6.1）。 | 本书推广为"不共享任何可写资源" | 18 |
| 评测沙箱规格 | evaluation sandbox spec | 与分数一起发布的评测环境配置：隔离档位、网络模式（分阶段）、出站验证、.git 与题面策略、外部服务与镜像、算力预算、超时与资源、评分器、harness 与系统提示、日志监控、统计口径（本书建议）。 | 不是任何机构的标准；规格变了即视为另一个基准 | 20 |
| 沙箱套沙箱 | sandbox-within-a-sandbox | 在被测沙箱外再加一层隔离（如容器运行在 VM 内），使遏制评测中的成功逃逸仍被隔在评测基础设施之外。 | SandboxEscapeBench 采用 | 20 |
| 出站预检 | egress preflight check | 评测开始前从任务沙箱内部探测公网、靶场域名、包代理代取、云元数据与管理接口是否可达，结果写入规格（本书建议）。 | 对应 Anthropic 一手页面"validation of all internet access paths"；与"出站探针"同类 | 20 |
| oracle 校验 | oracle check | 确认每个任务的参考解（或至少一种有效解）在发布的规格下能稳定通过，用以区分环境失败与模型失败。 | Terminal-Bench 2.1 据此修订任务；兼有减少无解任务的遏制作用 | 20 |
| 环境错误率 | infrastructure error rate | 因镜像、外部服务、超时、宿主故障等环境原因作废或重跑的运行比例。 | 应与分数一起报告 | 20 |
| 元博弈 | metagaming | 模型显式地推理自己的训练或评测机制以最大化奖励（OpenAI ExploitGym 复盘用语），例如读取基准论文与代码推断评分规则。 | 属取回型的延伸：取回对象从答案扩展到评分规则 | 2 |
| 遏制预算 | containment budget | 把隔离强度、出站控制、单 episode 算力上限、轨迹监控四个维度放进同一个权衡：在污染奖励比例与越界事件率不超过上限的约束下使成本最小（本书提法）。 | 第 28 章图 28-1；前提测量（B28-01、B28-02）目前不存在 | 28 |
| 污染奖励比例 | contaminated-reward fraction | RL 训练中正奖励来自非预期通道（取回型或篡改型 hacking）的比例；比 hacking 率更直接反映对训练的影响（本书建议的指标）。 | 第 19 章 19.6.2 节测量协议第四条 | 19 |
| 金丝雀答案 | canary answer | 放在 .git 历史、伪造上游、harness 日志等模型可达但正常解题不会触及的位置、内容可识别却错误的"答案"；最终提交中出现其标记即可确定取回通道（本书建议）。 | 第 19 章 19.6.2 节；第 28 章表 28-4 | 19 |

### I. 产品与产业

| 中文术语 | English | 定义（1–2 句，结合 Agent 沙箱语境） | 易混淆项/辨析 | 首次出现章节 |
|---|---|---|---|---|
| 三种产品范式 | three product paradigms | 按分配单位、寿命上界、状态是否跨任务保留三条判据划分：一次性短命容器（claude.ai 代码执行、ChatGPT 代码解释器、Coze Studio 代码节点）；任务级临时 VM 或容器（Codex cloud、Jules、Copilot、Claude Managed Agents）；有状态长期 VM（Manus、Genspark、Replit、Lovable，可休眠、按天回收或常驻）。Cursor 云 agent 处在二、三之间。 | 范式间真正的安全差异在凭据位置，而非隔离强度 | 21 |
| scoped token | scoped token | 按会话下放、权限受限、可单独吊销的凭据；Cowork VM 只持有它。 | 与长期真实凭据对照 | 21 |
| 时间分离（凭据） | temporal credential separation | 凭据只在 Agent 读取不可信内容之前的阶段（如 setup）存在，Agent 阶段开始前移除，同时断网；Codex cloud 为代表。 | 与"凭据在代理/宿主"并列的第四种做法；不需要代理，代价是 Agent 阶段做不了需凭据的事 | 14 |
| 凭据位置 | credential placement | Agent 运行时真实凭据所在之处：沙箱内、出站代理、宿主或 harness；决定 Agent 被注入后能"拿走"或"借用"什么。 | 与隔离强度正交：隔离强度决定租户间风险，凭据位置决定单用户被注入后的损失 | 14 |
| 沙箱即服务 | sandbox-as-a-service | 以 API 出售隔离执行实例的云服务（E2B、Modal、Daytona、Vercel 等）；2026 年被推理与 Agent 平台吸收，路径有三：并购（OpenAI–Ona、Baseten–Blaxel）、一方产品（Docker、Cloudflare、Vercel、Google、CoreWeave）、训练平台自带（Modal、Prime）。 | 与 RL 环境市场区分 | 22 |
| 活跃 CPU 计费 | active-CPU billing | 只按实际使用的 CPU 计费（Vercel、Cloudflare），回应 Agent 大量时间在等 LLM；两家的内存仍按预置量计费；CPU 活跃度低时内存成为账单主体（10% 活跃时约占 70%–77%，第 22 章表 22-2，笔者推算）。 | 与"暂停不计费"（Blaxel、Sprites、Docker）同属一类趋势 | 22 |
| 墙钟计费 | wall-clock billing | 按沙箱运行的秒数收取 CPU 与内存费用，不论 CPU 是否活跃（E2B、Daytona、Modal、Runloop、Northflank）。 | 与"活跃 CPU 计费""暂停不计费"并列为三类计费方式 | 22 |
| 暂停不计费 | free pause / no charge while paused | 暂停或休眠期间不收 CPU 与内存费，通常仍收存储费（Sprites、Docker Cloud Sandboxes、阿里 ACS、腾讯 AGS）。 | 与"状态保留范围"是两项不同承诺 | 22 |
| UI gym | UI gym | 复刻网站或应用界面、供 computer-use 与浏览器 Agent 训练的环境；SemiAnalysis 记约 2 万美元一个（经 Epoch 转引）。 | 不译 | 22 |
| 独占溢价 | exclusivity premium | 独占环境相对非独占环境的价格倍数（Epoch：约 4–5 倍）。 | 与环境泄露、取回型 reward hacking 风险相关 | 22 |
| 前瞻营收年化 | forward revenue run rate | 按当期签约或用量外推的年化收入（Daytona 用语），不等于已确认收入。 | 与 ARR、年化收入区分，引用时照原文 | 22 |
| 作者谱系（TrEnv → AgentENV → DSec） | author lineage | 据作者重叠推断的"serverless 内存模板 → 开源 Agent 沙箱 → 生产级训练沙箱"传承线。 | 属笔者推断，非当事方陈述 | 25 |
| 披露矩阵 | disclosure matrix | 按"训练规模 / 编排与隔离 / GUI 环境 / reward hacking 缓解 / 产品沙箱"五列逐格记录厂商公开信息的表（第 26 章表 26-2；第 27 章表 27-1 另加"事故复盘"一列）；每格为"事实 + 出处"或"未披露（已查：……）"。 | "未披露"是带检索范围的结论，不是空白；只读部分正文的写"正文未读" | 26 |
