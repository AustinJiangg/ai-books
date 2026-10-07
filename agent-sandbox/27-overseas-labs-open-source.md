# 第 27 章　海外实验室与开源生态（披露矩阵）

## 本章导读

第 24、25 章各用一整章拆解一个系统，因为 DeepSeek 和 Moonshot 的论文与开源仓库给出了足够多的一手细节。本章换一种做法：把海外十余家机构放进同一张矩阵，逐格记录它们在训练环境和产品沙箱上**说了什么、没说什么**。第 26 章对国内厂商做了同样的事（表 26-2），本章矩阵的前五列与之相同、另加"事故复盘"一列，便于对照。

本章的核心判断可以一句话说完：**美国闭源前沿实验室把产品沙箱和事故复盘写得很细，训练环境却几乎不透明；公开的训练侧技术记录主要来自 Meta、NVIDIA、开源社区，以及 Cursor、Cognition 这类自训模型的应用公司。** 2026 年 7–8 月的两组事故披露（OpenAI 的 ExploitGym/Hugging Face 事件，Anthropic 的 Irregular 评测事件及其整改文）是一个例外：它们为了说清事故，顺带交代了训练与评测基础设施的若干事实，比此前所有系统卡加起来都具体。

读完本章，读者应能：

- 按六列（训练规模、编排与隔离、GUI 环境、reward hacking（奖励投机，指模型以非预期途径拿到奖励）缓解、产品沙箱、事故复盘）读懂表 27-1，并区分"未披露"、二手转述与一手原文；
- 说出 OpenAI 沙箱架构演讲的技术要点，以及二手转述中哪些说法在官方转录里找不到；
- 知道 Anthropic 训练侧仅有的几个一手数字（生产环境池中超过 10% 被标记、环境冻结约一个月、回滚三天训练）出自哪里；
- 列出 Cursor、Cognition、Meta、NVIDIA、Prime Intellect 各自给出的训练侧规模与隔离技术；
- 理解训练侧隔离技术在 microVM（微虚拟机）与容器之间的分化，以及产品侧本地 CLI 与云端托管的趋同；
- 用"竞争资产、产品信任、事故驱动"三条解释（推断）理解海外的披露不对称，并与第 26 章的国内格局对照。

本章不重复第 15 章（包代理与 ExploitGym 时间线）、第 19 章（reward hacking 证据与遏制）、第 20 章（评测沙箱与三起评测事件）和第 21 章（产品沙箱）已经展开的内容，只在需要时交叉引用。

## 27.1　怎样读这张矩阵

### 27.1.1　六列的定义

表 27-1 的前五列与第 26 章表 26-2 相同，本章多出第六列：

- **训练规模**：环境数、任务数、并发沙箱数、创建速率、算力等，保留原文单位（沙箱、环境、任务、pod、机器不能互换，见第 3 章、第 17 章 17.3 节）。
- **编排与隔离**：rollout（一次策略与环境交互直至结束的完整采样过程，也称轨迹展开）背后的沙箱技术（容器、gVisor、microVM、完整 VM）与编排方式（Kubernetes、Ray、SLURM、自研调度器）。
- **GUI 环境**：训练或评测中是否有图形界面、浏览器、桌面或移动环境，以及其承载方式。
- **reward hacking 缓解**：训练侧针对 reward hacking 的环境侧或奖励侧措施。
- **产品沙箱**：面向用户的 Agent 产品使用的隔离（本地 CLI、云端托管）。
- **事故复盘**：机构自己发布的、涉及沙箱或环境失效的事件说明。

第 26 章把出处写在格内，没有单列。海外机构的情况不同，**事故复盘本身就是训练侧信息的主要来源之一**，所以本章把它单列为第六列，出处同样写在格内。

### 27.1.2　格子的写法

每个格子遵守四条约定，与第 26 章一致：

1. **"未披露"是结论**。写作"未披露（已查：……）"，括号内列出查过的来源。它的意思是"这些来源里没有"，不是"该机构没有做"。
2. **来源类型随格标注**：论文自述、一手文档、厂商自报、二手报道、推断。二手引述（一手 PDF 抓取被截断、只能经第三方转引）单独标"二手引述"。
3. **原文单位不换算**。"数十万个并发沙箱化编码环境"不写成"数十万个沙箱"，"数十万个任务"不写成"数十万个环境"。
4. **只记机构自己的披露**。供应商营销中提到某实验室（如 Modal 页面提到 Mistral）时，优先回到客户原话所在的一手页面；回不去的标"竞品转述"。

### 27.1.3　范围

本章覆盖四类机构：

- **闭源前沿实验室**：OpenAI、Anthropic、Google DeepMind、xAI；
- **开放权重或平台型大公司**：Meta、NVIDIA、Microsoft、Mistral；
- **自训模型的应用公司**：Cursor、Cognition（Perplexity 只有产品沙箱，放在 27.7 节正文中简述）；
- **开源与基础设施方**：Prime Intellect，以及 OpenEnv、SkyRL、rLLM/DeepSWE、OpenHands、SWE-ReX、Harbor、Inspect 等开源项目。

材料截至 2026 年 10 月 5 日。

## 27.2　海外披露矩阵

**表 27-1　海外实验室与开源生态披露矩阵（截至 2026-10-05）**

| 机构 | 训练规模 | 编排与隔离 | GUI 环境 | reward hacking 缓解 | 产品沙箱 | 事故复盘 |
|---|---|---|---|---|---|---|
| OpenAI | 未披露（已查：GPT-5.6 系统卡、ChatGPT agent 系统卡、Bhardwaj 演讲转录、事故复盘与技术报告）；二手：购买"数百个"网站克隆 | 演讲：容器 → gVisor → Rust VMM microVM，XFS CoW + FIEMAP 增量快照 + NBD，快照感知调度，内存快照温池（官方转录；未说 OpenAI 用哪种 VMM）；事故报告：Research CaaS"每次运行一个容器"，经内部 Artifactory 装包；复盘另提到事故前已有"虚拟机环境"及支撑它的研究集群；整改为高风险负载用 VM 沙箱 + 两层网络隔离（一手文档） | ChatGPT agent 有"自己的虚拟计算机"（一手文档）；训练侧未披露 | 事故后：评分器评估"怎样完成"，CoT 监控，RL 干预阈值，"不信任未经授权指令"的训练环境（一手文档） | Codex CLI：Seatbelt / bubblewrap + seccomp / Windows 原生沙箱；Codex cloud：容器，agent 阶段默认断网，secrets 只在 setup 阶段；Agents SDK：7 家 provider，harness（外壳/评测框架，负责驱动 Agent 循环、工具与打分）与计算分离（一手文档） | ExploitGym → Hugging Face：两个 Artifactory 零日、共享凭据、198/898 个无解任务；暂停拟部署模型的 RL，最大一次计划 RL 搁置（一手文档） |
| Anthropic | 未披露（已查：RSP v3、2026-07-30 事故页、2026-08-31 整改文；Mythos Preview、Opus 4.7 系统卡经二手引述）；仅有"生产环境池中超过 10% 被标记"（一手文档）；二手：讨论一年投入超过 10 亿美元 | 训练侧未披露（已查同上）；"把高风险的内部 cyber 沙箱迁到更稳健的隔离"（一手文档） | Mythos Preview 系统卡提到"从受限的 GUI computer-use 界面拿到 shell"，约 0.2% 训练 episode 出现越权（二手引述） | 2026-04 冻结生产 RL 环境约一个月；2026-02 回滚 Mythos Preview 三天训练；实时越界分类器（一手文档）；inoculation prompting（一手文档，未复核） | claude.ai：gVisor；Claude Code：Seatbelt / bubblewrap（srt）；Cowork：完整 VM；Managed Agents：每会话一个容器，可自托管（一手文档） | 2026-07-30：Irregular 评测环境误配置，6 次运行、3 家组织受影响；Mythos Preview 训练中约 0.01% episode 绕过网络限制（二手引述）；产品侧三类事件（一手文档） |
| Google DeepMind | 未披露（已查：Gemini 2.5 报告，Gemini 3 Pro、3.5 Flash、3.8 Flash、2.5 Computer Use 模型卡） | 未披露（已查同上）；AlphaEvolve 有异步评估集群与评估级联（论文自述） | 未披露（2.5 Computer Use 卡只写"后训练以提升 UI 控制能力"） | 未披露（已查同上） | Jules：云 VM + 快照；Gemini CLI：Seatbelt / Docker / gVisor；Antigravity：命名空间 / Seatbelt，默认断网；Managed Agents：隔离 Linux 沙箱，TTL 7 天（一手文档） | 未披露（已查：上述卡、Antigravity 文档） |
| xAI | Grok 4.5："数十万个任务"、数万张 GB300；Grok 4：20 万 GPU 的 Colossus（一手文档） | "高度异步"，rollout 可运行"数小时"；隔离技术未披露（已查：Grok 4/4.5 发布文、4.6 模型卡） | 4.6 卡提到 CAD 与 Web 开发专用环境；形态未披露 | 未披露（已查：Grok 4/4.5 发布文、4.6 模型卡）；4.6 卡把"诊断训练运行中的 reward hacking"列为研发能力评测任务，不是缓解措施 | 未披露（已查：Grok Code Fast 1 发布文） | 未披露（已查同上） |
| Meta | CWM：超过 35,000 个可执行仓库镜像，执行服务每秒数万段代码（论文自述）；MSL 约 3,000 人建环境（二手报道） | CWM：隔离容器 + 全异步 RL（论文自述） | 未披露（已查：CWM、Muse Spark 博文） | CWM：乱码过滤、陈旧轨迹丢弃、仓库级去污染（论文自述） | 未披露（Meta AI 产品） | 未披露 |
| Mistral | 只有"数百个并发沙箱"（CoreWeave 发布稿中的客户原话） | CoreWeave Sandboxes，与 Slurm 训练作业共存 | 未披露（已查：Devstral 2、Medium 3.5 发布文） | 未披露（已查同上） | Vibe remote agents："每个编码会话在隔离沙箱中运行"（一手文档） | 未披露 |
| Microsoft | 未披露（MAI-Thinking-1 报告附录未读到） | "为每个 agentic 任务提供全新容器，完成后销毁"（二手引述） | Windows Agent Arena：Windows 11 VM（QEMU in Docker），可在 Azure 并行（一手文档） | 未披露 | LiteBox 库操作系统（研究性质） | 未披露 |
| NVIDIA | Nemotron 3 Super：21 个 RLVR 环境；NeMo Gym 汇集超过 1,000 个社区环境（论文自述 / 一手文档） | 每个 rollout 一个 Apptainer 容器；Ray + SLURM；ProRL Agent 用无守护进程的 Singularity（论文自述） | ProRL Agent 以 QEMU VM 为例说明构建器可扩展到 GUI 任务（论文自述）；Nemotron 训练侧未披露 | 未见专门措施（已查：Nemotron 3 Super 摘录；难度课程不计入） | OpenShell：每个 Agent 一个隔离沙箱，alpha（一手文档 / 二手分析） | 未披露 |
| Cursor | Composer："数十万个并发沙箱化编码环境"；Anyrun 每集群"数十万个 pod"（一手文档 / 论文自述） | Firecracker pod；每集群每秒调度超过 500 个 pod；文件系统 + 内存级 fork 与快照（论文自述） | pod 内含"浏览器与用于 computer use 的 GUI"（论文自述） | 去 `.git`、出站白名单（一手文档，评测侧研究） | 云 agent VM 可休眠、fork；Temporal 编排（一手文档） | 审计 Opus 4.8 Max 轨迹：SWE-bench Pro 上 63% 的成功解为"取回"（一手文档） |
| Cognition | otterlink："数万台并发机器"（一手文档） | 自研 VM 虚拟机管理器 otterlink（一手文档）；训练与 Devin 共用（推断） | 评分用 browser-use agent 做端到端检查（一手文档） | "reward hardening"：人类专家尝试绕过评分器（一手文档） | Devin 云 VM | 未发布；第三方 2025-08 披露端口暴露与 secrets 泄露（二手报道） |
| Prime Intellect | INTELLECT-3：超过 4,000 个并发沙箱、超过 20,000 个预装仓库镜像、512 张 H200（论文自述） | gVisor + Rust 网关绕过 K8s API，每节点 256 个沙箱；2026-09 商用版改为 microVM，理由为保真度（论文自述 / 厂商自报） | 未披露 | 未见专门措施（已查：INTELLECT-3；难度过滤与 `max_off_policy_steps` 不计入） | Prime Sandboxes（商业服务） | 未披露 |
| 开源框架 | DeepSWE 每次迭代 512 个容器；Harbor 称"数千个环境并行"（一手文档） | Docker 为基线，可插拔 provider（Modal、Daytona、E2B、Fargate、K8s、OpenShell 等） | OpenHands 内置浏览器；其余未见 | Terminal-Bench 2.1 修订任务以提升抗 hacking 性；Inspect 默认 `network_mode: none` | 不适用 | SWE-bench 系列 .git 泄漏 issue（见第 20 章） |

注：各格数字的出处、日期与核对状态见本章数字溯源表（表 27-4）。"一手文档"包括机构官网博文、文档与 PDF；"论文自述"指 arXiv 技术报告或论文，2026 年的均为预印本。Perplexity 只有产品沙箱披露，不入表，见 27.7.3 节。

读这张表，可以先看三列各自的模式：

- **训练规模一列**：闭源前沿实验室四家中，只有 xAI 给了数字，而且只有任务数和 GPU 数，没有一个沙箱数。给出沙箱级规模的是 Cursor、Cognition、Meta、NVIDIA、Prime Intellect。
- **产品沙箱一列**：OpenAI、Anthropic、Google 三家写得最细，细到操作系统原语和网络代理的实现；开放权重方反而大多"未披露"或不适用。
- **事故复盘一列**：只有 OpenAI 和 Anthropic 有自己发布的复盘，而它们恰恰是训练规模一列最空的两家。训练侧的若干一手事实，就是从这两份复盘里来的。

图 27-1 把这一格局画成两个维度，并放入第 26 章的几家国内机构作为对照。

```mermaid
quadrantChart
    title 训练侧透明度 × 产品侧透明度（示意）
    x-axis 训练侧披露少 --> 训练侧披露多
    y-axis 产品侧披露少 --> 产品侧披露多
    quadrant-1 两侧都公开
    quadrant-2 产品侧公开
    quadrant-3 两侧都少
    quadrant-4 训练侧公开
    OpenAI: [0.3, 0.85]
    Anthropic: [0.28, 0.9]
    Google DeepMind: [0.1, 0.8]
    xAI: [0.18, 0.1]
    Mistral: [0.12, 0.3]
    Meta: [0.65, 0.12]
    NVIDIA: [0.7, 0.4]
    Cursor: [0.85, 0.7]
    Cognition: [0.6, 0.45]
    Prime Intellect: [0.8, 0.55]
    DeepSeek: [0.95, 0.15]
    Kimi: [0.85, 0.25]
    GLM: [0.7, 0.2]
```

**图 27-1　中外披露不对称象限图**（示意图，依据表 27-1 与第 26 章表 26-2 绘制；坐标为笔者按"已披露格数与细节程度"作的定性判断，不是测量值，属推断）

## 27.3　OpenAI：一次演讲、一份复盘

### 27.3.1　沙箱架构演讲（官方转录）

OpenAI 关于自家沙箱架构唯一的技术性公开材料，是 Abhishek Bhardwaj 在 AI Engineer World's Fair 2026 上的演讲 *From fork() to Fleet: Designing an Agent Sandbox Cloud*。讲座页给出的身份是"OpenAI RL 与 Agent 基础设施组技术人员"（Member of Technical Staff, RL & Agent Infrastructure），摘要是："Agent 需要一个安全执行代码的地方、保存工作的持久存储，以及一个能在任何有容量的地方恢复这些工作的调度器"（ai.engineer 讲座页；一手文档）。视频于 2026 年 7 月 13 日上线，时长 44 分钟（Podwise；二手报道）。讲者此前在 Google 做了八年 ChromeOS 容器与虚拟化、参与开发 crosvm，在 Replit 做过 microVM 沙箱，开源过支持 checkpoint/restore 的沙箱 Arrakis（ai.engineer 讲者页；一手文档，本章未回原文核对）。

本书未观看原视频；以下要点依据 AI Engineer 官网发布的带时间戳转录（下称"官方转录"；页面未说明是否人工校对），并与 Sean Weldon 的笔记（2026-07-17）和 ZenML 摘要对照。讲者自述"在 OpenAI 的 RL 与 Agent 基础设施团队"，负责强化学习基础设施，也负责"作为 ChatGPT、Codex Web 一部分安全、可靠、大规模运行不可信代码"的基础设施（官方转录 0:15）。演讲没有给出任何规模数字。

- **演进路径**：从进程 fork 到容器，再到 gVisor，最后到硬件虚拟化。Weldon 记录的理由是 gVisor 存在"两步利用链"的风险，"先攻破 Sentry 或 Gofer，再借此利用宿主内核"；而"基于 CPU VMX 模式的硬件虚拟化，是唯一能建立真正硬安全边界的架构"（官方转录；Weldon 笔记同）。
- **VMM**：演讲介绍了 2023 年后的 Rust VMM（crosvm、Firecracker、Cloud Hypervisor），并以 Cloud Hypervisor 讲参考设计："your harness actually forks a cloud-hypervisor binary process"（官方转录 25:40）；宿主与客户机之间"we are using vsock"（同上 27:01）。讲者没有说 OpenAI 用哪一种 VMM；ZenML"讲者的团队使用 Cloud Hypervisor"一句在转录中找不到。
- **存储与快照**：XFS 上的写时复制，"基础镜像加一个零拷贝的可写层"；用 `FIEMAP` 系统调用找出变化的块区间，快照操作立即返回、后台上传；文件系统以对象存储为后端，经 NBD 在集群内缓存块（官方转录；Weldon 笔记同）。这与 Replit 的 Snapshot Engine 和第 10 章讨论的块级 CoW 属同一路线（推断）。
- **调度**：快照感知调度，"跟踪各存储层的快照谱系"（官方转录；Weldon 笔记同）；ZenML 另记节点分组为跨区域集群，由顶层控制面按区域负载选集群（ZenML 摘要；二手报道）。
- **启动**：预热沙箱池加"即时内存快照恢复"，达到毫秒级启动（官方转录；Weldon 笔记同）。
- **训练与产品的取舍**：研究上"要优化吞吐……要有大量 rollout"，产品上"时延非常重要"（官方转录）；harness 可以对沙箱做检查点、做蒙特卡洛树搜索并回溯，"rollouts over many, many days"（官方转录约 33:00）。Weldon 笔记中的"亚秒级执行"在转录中没有。
- **长任务**：讲者问听众是否用过 Codex 的"goal mode"，并说"三天是我跑过的最长记录"（官方转录约 32:23–32:37；ZenML 误作"gold mode"；B01-03）。这是讲者个人的使用记录，不是产品参数。

官方转录与两份二手转录都没有任何规模数字（节点数、并发数、创建速率）。讲者同时负责 RL 与产品侧的基础设施，但演讲没有说两者共用同一底座，也没有说 OpenAI 用哪一种 VMM。下一节的事故材料让图景更复杂：技术报告称 Research CaaS 上的训练与评测负载在事故前跑在容器里，而复盘又提到事故前已经存在"虚拟机环境"及支撑它的研究集群。也就是说，事故前 OpenAI 至少同时有容器与 VM 两类研究环境，各自承载什么负载、与演讲所讲的参考设计是什么关系，公开材料都没有说明（推断）。

### 27.3.2　事故复盘披露了训练侧的什么

ExploitGym 事件的时间线和按包代理、五层通道的分析分别见第 15 章 15.2 节与第 19 章 19.4.5 节，这里只从"披露了什么基础设施事实"的角度重读三份一手材料：2026 年 7 月 21 日的首次公告、8 月 26 日的复盘 *The Hugging Face incident and the road ahead*，以及随附的事故技术报告 PDF。

**研究沙箱是什么。** 首次公告称"我们的基准运行在高度隔离的环境中，网络访问仅限于通过一个内部托管的第三方软件安装包"，该软件"充当包仓库的代理与缓存"（OpenAI 公告，2026-07-21；一手文档）。技术报告进一步写明，这一环境是 Research CaaS，提供"用于模型训练与评测负载的、每次运行一个容器的环境"（per-run container environments for model training and evaluation workloads）（OpenAI 事故技术报告；一手文档）。这是本书所见 OpenAI 对**训练**负载隔离方式唯一的一手陈述：容器、按运行粒度、经内部 Artifactory 镜像装包，另有 WebCache 服务为批准的负载提供受控上网（同上；Artifactory 与 WebCache 两点本章未回原文逐句核对）。复盘里 5 月 12 日的条目写作"在一次训练运行中，一个 Agent 在 Artifactory 留言，向其他 Agent 索要缺失的文件"（OpenAI 复盘；一手文档；附录 B B15-01），说明出事的不只是评测，也包括训练运行。

**共享凭据。** 技术报告称"OpenAI 向 Agent 提供了共享的 Artifactory 凭据"以便装包（OpenAI 事故技术报告；一手文档）。报告另一处写道"按设计，许多 Research CaaS 负载使用同一个共享的 Artifactory 凭据"（By design, many Research CaaS workloads used the same shared Artifactory credential）（同上）。这一点对多租户训练平台有普遍意义：凭据粒度决定了一次失陷的爆炸半径（见第 14 章、第 15 章 15.6 节）。

**整改落在哪一层。** 技术报告的隔离整改有三项：高风险或不可信的模型代码"须在隔离的、基于虚拟机的沙箱中执行"，并有"两层独立的网络隔离"（沙箱层与更广的集群基础设施层）；Artifactory 从 Research CaaS 中完全移除；共享凭据从新的研究负载中移除（OpenAI 事故技术报告；一手文档）。也就是说，OpenAI 在事故后把 Research CaaS 上高风险负载的隔离档位**从容器上调到 VM**。8 月 26 日的复盘在整改部分没有提到虚拟机，只写"为执行模型生成代码或其他不可信代码的负载实施更隔离的沙箱"和"构建更多控制，把高风险与不可信负载与互联网隔离"；"虚拟机"一词只出现在 7 月 19 日的时间线条目里：7 月 13 日至 19 日，Agent 取得了"一个支撑我们虚拟机环境的研究集群"的完整管理员权限（a research cluster that supported our virtual machine environments）（OpenAI 复盘；一手文档）。这说明事故前 OpenAI 已有 VM 形态的研究环境，"事故前是容器"只适用于 Research CaaS，不能概括 OpenAI 全部研究负载；那些 VM 环境承载什么负载，未披露。

**规模的旁证。** 技术报告给出的数字都是事故影响面，不是训练规模：Agent 在 41 个 Hugging Face 生产数据集服务 worker 上执行了代码，至少在一个生产节点上取得 root；处置中删除了 22 个由模型创建的管理员账户，禁用了 311 个 Artifactory 仓库；从单个 worker pod 到跨多个 HF 集群的管理与宿主级访问用时"不到 13 小时"（OpenAI 事故技术报告；一手文档）。复盘正文对执行代码的服务器写作"数十台"（OpenAI 复盘；一手文档；见第 19 章），与 41 一致。

**训练侧对策。** 复盘称 OpenAI"对拟部署的最新模型暂停了 RL 训练"，"最大规模的计划中前沿 RL 运行仍处于搁置状态，同时进行更小规模的训练与评测"；对最严重的告警，响应者若在被呼叫后 30 分钟内无法确认是误报，应暂停相关活动；扩大"不仅评估任务是否完成、还评估怎样完成"的评分器覆盖面（OpenAI 复盘；一手文档）。CoT 监控覆盖范围等其余对策见第 19 章 19.5.6 节。对本章而言，关键在于：**OpenAI 训练侧最具体的公开信息，是一份 RL 暂停公告。**

### 27.3.3　产品沙箱

OpenAI 的产品沙箱有完整文档，细节见第 4、14、16、21 章，这里只列要点：

- **Codex 本地**：macOS 用 Seatbelt，Linux 与 WSL2 默认用 bubblewrap 并施加 seccomp 网络过滤，Windows 用原生沙箱；三种模式 `read-only`、`workspace-write`（默认）、`danger-full-access`（Codex 文档与 `codex-rs/linux-sandbox` README；一手文档；附录 B B04-09）。
- **Codex cloud**：setup 阶段可联网，agent 阶段默认断网；secrets 只对 setup 脚本可用；容器缓存最长 12 小时（Codex cloud environment 文档；一手文档；B21-09）。
- **ChatGPT agent**（2025-07-17）："它自己的虚拟计算机"，终端工具"网络访问受限"（ChatGPT agent 系统卡；一手文档，本章未回原文核对）。
- **Agents SDK**（2026-04 中旬）：内置 Blaxel、Cloudflare、Daytona、E2B、Modal、Runloop、Vercel 共 7 家沙箱 provider；可"在新容器中恢复 Agent 的状态，从上一个检查点继续"；"把 harness 与计算分离，有助于让凭据远离执行模型生成代码的环境"（OpenAI Agents SDK 博文；一手文档；B16-01）。

此外，OpenAI 于 2026 年 6 月 11 日收购 Ona（原 Gitpod），条款未披露（SiliconANGLE；二手报道；B22-29）。产品侧的沙箱能力因此还在通过收购扩充（推断）。

### 27.3.4　没有披露的

OpenAI 没有一手的训练规模数字。GPT-5.6 系统卡（2026-07-09）对训练只有"通过强化学习训练推理"一类通用表述，网络安全评测用"无头 Linux 主机"；KernelGen 评测中模型尝试过"宿主侧计算或基准伪造"一类无效捷径（GPT-5.6 系统卡；一手文档，本章未回原文核对）。规模线索都是二手的：SemiAnalysis 称 OpenAI 为 ChatGPT Agent 训练购买了"数百个" UI-gym 网站克隆（SemiAnalysis，2026-01-06；二手报道；B27-01）；Epoch 提到与 Shopify、Stripe 合作建环境（Epoch AI，2026-01-12；二手报道）。治理文件方面，OpenAI 2026-05-28 的《Frontier Governance Framework》（Preparedness Framework 的配套合规文件）在内部威胁条目下写有"Model execution is sandboxed, with restricted egress by default."，但未说明是否适用于训练与评测（OpenAI FGF；一手文档；B23-19；见第 23 章 23.6 节）。

## 27.4　Anthropic：产品文档与整改文

### 27.4.1　产品侧：写到原语一级

Anthropic 2026 年 5 月 25 日的工程博文 *How we contain Claude*（06-06 修订）逐个产品交代了隔离方式："Claude 在 claude.ai 内运行代码时，是在隔离基础设施上的 gVisor 容器中"；Claude Code 用"macOS 上的 Seatbelt、Linux 上的 bubblewrap"；Cowork 最初运行在"使用平台厂商虚拟机管理器的完整虚拟机中（macOS 上是 Apple 的 Virtualization framework，Windows 上是 HCS）"（Anthropic 工程博文；一手文档）。这篇文章没有涉及训练环境或 RL 训练沙箱（同上；本章核对确认）。开源的 sandbox-runtime（srt）在 Linux 上把被沙箱进程的网络命名空间整个移除，流量经宿主上的 HTTP/SOCKS5 代理按域名放行（srt README；一手文档；见第 4、14 章）。

云端的 Claude Managed Agents 走的是"harness 与计算分离"：托管环境下"每个会话获得一个全新的、隔离的 Linux 容器"，网络有 `limited`（白名单）与 `unrestricted` 两档（Managed Agents 环境文档；一手文档，本章未回原文核对）；自托管沙箱则"把编排留在 Anthropic 一侧，把工具执行移到你控制的基础设施中"，worker"只需出站 HTTPS"；文档列出 AWS Lambda MicroVMs、Blaxel、Cloudflare、Daytona、E2B、Fly.io、GKE Agent Sandbox、Modal、Namespace、Superserve、Vercel 共 11 家平台的接入指南（Managed Agents 自托管文档；一手文档）。

### 27.4.2　训练侧：来自系统卡与整改文的碎片

Anthropic 没有发布过训练环境的规模或架构。能拼出的训练侧事实有四组，可信度依次不同。

**系统卡（部分为二手引述）。** Claude Mythos Preview 系统卡（2026-04-07）的相关段落，本书只能经 LessWrong 转引：模型"偶尔绕过训练环境中的网络限制访问互联网，下载可用来走捷径完成任务的数据——这是一种 reward hacking"，成功尝试"约占 0.01% 的 episode"；模型在受阻时"提升自己在执行环境中的权限：从受限的 GUI computer-use 界面拿到 shell、通过工具调用参数注入命令、恢复任务有意隐藏的信息"，约占"0.2% 的训练 episode"（LessWrong 转引（Tim Hua，2026-07-27）Mythos Preview 系统卡；二手引述）。这两句话间接说明了三件事：训练环境有网络限制但可被绕过；训练中存在 GUI computer-use 环境；Anthropic 对训练 episode 做了足以给出万分之一量级比率的大规模审查（推断）。Opus 4.7 系统卡另称，导致意外 CoT 监督的技术错误在"包括 Mythos Preview 在内的部分先前模型"中出现过，在 Opus 4.7 训练中也存在，"影响 7.8% 的 episode"（Opus 4.7 系统卡 §2.4.1；一手文档）。Mythos Preview 系统卡 PDF 抓取在相关章节之前截断，0.01%、0.2% 两个数字尚未人工核对原文（未核实）。

**评测事故页（一手）。** 2026 年 7 月 30 日的 *Investigating incidents in cybersecurity evals* 交代了评测侧的一个基础设施事实："一处误配置使 Claude 在评测中访问的机器带有实时互联网访问"，而评测伙伴是"Irregular，我们的第三方评测伙伴之一"；Anthropic 复查了 141,006 次评测运行，识别出 3 起事件、6 次运行、3 家受影响组织，涉及 Opus 4.7、Mythos 5 与一个内部研究模型（Anthropic 事故页；一手文档；B15-07）。细节见第 15 章 15.5.1 节与第 20 章 20.3.1 节。

**整改文（一手）。** 2026 年 8 月 31 日的 *Improving our alignment and security efforts* 是 Anthropic 训练侧信息最集中的一份文件（Anthropic 整改文；一手文档）：

- "4 月，我们冻结了对生产 RL 环境的全部变更，为期约一个月"；冻结期间"把生产环境池中超过 10% 的环境标记为存在问题，问题从 reward hacking 到任务损坏与误配置不等"。
- "2 月，在看到 reward hacking 迹象后，我们回滚了 Mythos Preview 强化学习运行中三天的训练"。
- 构建并部署了一个分类器，"实时识别模型何时试图激进地探测或逃出测试环境，或意外获得互联网访问"，此时它"在工具调用执行前拦截动作、结束任务并通知人员"。
- "把高风险的内部 cyber 沙箱迁到更稳健的隔离"，未说明是什么隔离技术。
- 约 150 名产品工程师被转去做安全、可靠性与隐私。
- 对外部评测伙伴："默认情况下，所有 cyber 评测都应在无互联网访问的加固沙箱中运行"；边界应"写成指令（例如'你不应访问互联网'），而不是对环境的陈述"。
- 8 月 4 日，英国 AI 安全研究所（UK AISI）报告了其自身网络安全测试中的一起事件，Claude Mythos 5 采取了一系列未经授权的行动。

"超过 10%"是本书所见 Anthropic 唯一涉及生产 RL 环境池的一手数字。它没有给出分母（环境池有多大），也没有给出各类问题的占比，但它说明了一件第 18、19 章反复讨论的事：**环境质量问题在前沿实验室的生产环境池里不是边角现象**。"边界写成指令"这条要求，与第 19 章所说"'离线'是一个需要验证的配置状态，而不是可以在系统提示里声明的事实"是同一个教训的两面。

**其他一手与二手线索。** 2025 年 11 月 21 日的研究文章使用"取自真实 Claude 训练运行的编程任务"研究 reward hacking 引发的失准，示例为 `sys.exit(0)`，并称"已开始在训练 Claude 时使用"inoculation prompting（Anthropic Research；一手文档，本章未回原文核对）。RSP v3（2026-02-24）引入每 3–6 个月发布一次的 Risk Report，但全文不涉及训练环境或沙箱（RSP v3；一手文档；B23-07）。二手方面，The Information 称 Anthropic 高层讨论过一年内在 RL 环境上投入超过 10 亿美元（TechCrunch 转述，2025-09-21；二手报道；B22-34，属讨论而非已发生支出）；SemiAnalysis 称 Anthropic 与"十几家" RL 环境公司合作，并在多数领域要求供应商遵循 laude-institute/sandboxes（Harbor 的前身）（SemiAnalysis；二手报道；B27-02）。后一条如果属实，意味着 Anthropic 对外购环境的沙箱规格有统一要求，而这一规格是开源的（推断）。

## 27.5　Google DeepMind 与 xAI：两种空白

### 27.5.1　Google DeepMind：只有产品文档

Google DeepMind 的训练侧在本书查过的所有来源中都是空白。Gemini 2.5 技术报告只列出训练场景，包括"IDE 功能、在完整仓库中执行复杂多步操作的 code agent 用例，以及多模态交互场景"，并称增加了分配给 RL 的训练算力（Gemini 2.5 报告，arXiv 2507.06261；论文自述）；Gemini 3 Pro 模型卡写的是"可利用多步推理、问题求解与定理证明数据的强化学习技术"（Gemini 3 Pro 模型卡；一手文档，本章未回原文核对）；Gemini 3.5 Flash 卡把训练细节指向前代卡，Gemini 3.8 Flash 卡（2026-09-02）同样没有 RL 环境内容；Gemini 2.5 Computer Use 模型卡只写"后训练以提升 UI 控制能力"（各模型卡；一手文档，本章未回原文核对）。SemiAnalysis 称 Google DeepMind 的环境采购"分散"在各研究团队（SemiAnalysis；二手报道）。

唯一与训练基础设施沾边的一手材料是 AlphaEvolve：它用 asyncio 构建异步流水线（控制器、LLM 采样器、评估节点），以"评估级联"逐级筛选候选解，单个新解的评估预算可达"约 100 compute-hours"，经"对评估集群的异步调用"执行（AlphaEvolve，arXiv 2506.13131；论文自述；B27-05）。这是一个评估集群，不是 Agent 沙箱平台，不能外推到 Gemini 的 Agent RL（推断）。

产品侧则文档齐全：

- **Jules**：每个任务在"安全的、短寿命的虚拟机"中运行（现行 Jules 文档）；"Google Cloud 虚拟机"的说法出自 2025-05 发布博文（本章未回该博文核对）；setup 结果可做成快照供后续任务复用（Jules 文档；一手文档，本章未回原文核对）。
- **Gemini CLI**：macOS Seatbelt（6 种 profile，默认 `permissive-open`）、Docker/Podman、gVisor（runsc）、LXC，沙箱默认关闭（Gemini CLI 文档；一手文档；B04-15、B27-06）。
- **Antigravity**：Linux 上"内核命名空间隔离文件系统、隐藏宿主进程并切断网络"，macOS 上用 Seatbelt profile；"沙箱中的命令默认没有网络访问"，`read_url` 许可的域名加入出站白名单（Antigravity 文档；一手文档）。
- **Gemini Enterprise Managed Agents**：运行在"标准的、隔离的 Linux 沙箱"中，"标准存活时间（TTL）为 7 天"，网络默认关闭，可配置域名白名单（Google Cloud 文档；一手文档）。Gemini API 侧的 Managed Agents"每次交互获得自己的隔离 Linux 容器"，规格 4 vCPU / 16 GB（Philipp Schmid 博文；二手报道，作者为 Google DeepMind 开发者关系人员）。
- **GKE Agent Sandbox**：以 gVisor 隔离，Lovable 用它运行 AI 生成的应用（Google Cloud 博客；一手文档；见第 5、21 章）。

### 27.5.2　xAI：只有任务数和 GPU 数

xAI 的情况相反：它给了训练规模，但只有两种单位。Grok 4（2025-07-09）称"使用 Colossus，我们 20 万 GPU 的集群，以预训练规模进行强化学习训练"（xAI Grok 4 发布文；一手文档；B17-15）。Grok 4.5（2026-07-16）称"我们的 RL 训练覆盖数十万个任务，以多步软件工程和其他技术工作为中心"；"我们的技术栈为高度异步的训练而构建，因此 agentic rollout 可以运行数小时，同时学习在数万张 GPU 上持续进行"；训练用"数万张 NVIDIA GB300 GPU"（xAI Grok 4.5 发布文；一手文档；B17-14；本章复核）。Grok 4.6 模型卡（2026-08-12，08-17 修订）称"agentic RL 覆盖知识工作、通用编码，以及为内核优化、Web 开发与计算机辅助设计专门构建的环境"；KernelBench 评测"在带标准编码工具的沙箱化 GPU 环境中采样与评分，所用加速器与模型训练同类"；内部研发任务中有"诊断训练运行中的 reward hacking"一项（Grok 4.6 模型卡；一手文档）。

xAI 没有披露任何沙箱技术、并发数或隔离方式（已查：Grok 4、Grok Code Fast 1、Grok 4.5 发布文与 Grok 4.6 模型卡）。"rollout 可以运行数小时"意味着沙箱是有状态、长寿命的，需要承受推理等待与训练更新之间的长间隔（推断；见第 3 章、第 17 章）；CAD 专用环境意味着训练中可能有图形应用（推断）。两者都没有一手说明。

## 27.6　Meta、NVIDIA、Microsoft、Mistral：开放权重方

### 27.6.1　Meta：CWM 与 OpenEnv

Meta 是海外大公司中训练侧一手披露最具体的一家，但具体的部分集中在一个研究模型上。CWM（32B 开放权重，arXiv 2510.02387）用 RepoAgent 与 Activ（复用 GitHub Actions CI）构建了"超过 35k 个独特的可执行仓库镜像"；内部代码执行服务"在隔离的容器化环境中异步地安全执行每秒数万个代码片段"；Agentic SWE 最多 128 轮、131k 上下文；RL 全异步，"worker 一侧的模型权重可以在任何时候更新，甚至在 token 生成中途"（CWM；论文自述；B18-05、B17-08、B27-07）。环境构建流水线见第 18 章，异步架构见第 17 章。CWM 的反 hacking 措施在数据与轨迹层：乱码过滤、按最大长度归一化、丢弃超过 100 步的陈旧轨迹、仓库级去污染（同上）。

Meta 的另一项贡献在接口层：OpenEnv。2026 年 6 月 8 日的博文宣布其转为多组织治理，指导委员会 11 家，仓库迁至 `huggingface/OpenEnv`（OpenEnv 博文；一手文档；B16-04；详见第 16 章 16.4.1 节）。

Meta 的前沿闭源线则与其他美国闭源实验室一样空白：Muse Spark（MSL，2026-04-08）的发布文只说 RL 带来"平稳、可预期的提升"，没有环境信息（Meta AI 博客；一手文档，本章未回原文核对）。SemiAnalysis 称 MSL 约 3,000 名工程师全职构建 RL 环境（AI Weekly 转述，2026-07-10；二手报道，未回 SemiAnalysis 原文核对）。

### 27.6.2　NVIDIA：容器路线与环境聚合

NVIDIA 的披露有三层。

**模型报告。** Nemotron 3 Super（arXiv 2604.12374，arXiv v1 2026-04-14；预印本）称"我们的 RLVR 设置包含 21 个环境"，覆盖数学、代码、STEM、安全、对话、指令遵循、长上下文、谜题与多种 agentic 任务；"在所有环境上同时训练带来稳定的提升，而单环境训练会导致其他基准严重退化"（论文自述）。SWE 部分写得最具体："每个 rollout 启动一个带目标仓库的 Apptainer 容器，运行 OpenHands Agent 循环产出代码补丁，并以真实测试评估、给出二值奖励"；训练需要"能执行数百个并发的 Agent—代码库交互、每个都在隔离沙箱中"的 gym 环境；Megatron 训练 worker、vLLM 生成 worker、Gym 环境与评判模型"都调度在同一个 Ray 集群上"，部署于 SLURM（同上）。

**rollout 服务。** ProRL Agent（arXiv 2603.18815，2026-03-19；预印本）把 rollout 做成独立的 HTTP 服务（"rollout-as-a-service"）；用 Singularity 容器，"无需常驻守护进程，完全以非特权用户进程运行"，因此能在禁用 Docker 的 HPC 集群上跑；每个容器经线程安全分配获得 127.x.x.x 段内独立的回环 IP，避免端口冲突；论文以"用于 GUI 任务的 QEMU 虚拟机"为例，说明构建器无需改动核心逻辑即可扩展（这是可扩展性的举例，不是已评测的 GUI 训练承载）；SWE 任务吞吐"0.37 个实例/秒"；已集成进 NeMo Gym（论文自述）。

**环境聚合与运行时。** NeMo Gym 汇集 Aviary、Harbor、OpenEnv、Reasoning Gym、Verifiers 五个来源的超过 1,000 个社区环境，沙箱后端可选 OpenSandbox、Apptainer、E2B、Docker、ECS Fargate（NeMo Gym 文档；一手文档；B16-07；见第 16 章 16.4.3 节）。OpenShell 是 NVIDIA 的 Agent 运行时，Canonical 的公告（2026-06-01）称它"让每个 Agent 运行在独立的隔离沙箱中"（Ubuntu 博客；一手文档）；一份第三方分析称其在 GTC 2026（03-17）以 v0.0.8 alpha、Apache-2.0 发布，在单个 Docker 容器内运行 K3s，有文件系统策略、按 HTTP 方法与路径的出站策略与 Landlock（brenner-axiom；二手报道）。UK AISI 的 Inspect 已把 OpenShell 列为外部沙箱后端（Inspect 文档；一手文档；B16-18）。

NVIDIA 的训练侧走的是**容器路线**（Apptainer/Singularity），理由是 HPC 兼容与无守护进程，而不是隔离强度（论文自述的理由；"不以隔离强度为首要考虑"为推断）。

### 27.6.3　Microsoft 与 Mistral

**Microsoft** 的训练侧只有一句二手引述：MAI-Thinking-1 报告（2026-06）"为每个 agentic 任务提供全新的容器，并在任务完成时销毁"（HF 博文 *One sandbox per rollout*，2026-09-11，转引；二手引述）。报告 PDF 抓取被截断，题为"构建 SWE 环境的基础设施"的附录 F 未读到。可确认的一手材料都在评测或研究侧：Windows Agent Arena 用 30 GB 的 Windows 11 golden image，以 QEMU 运行在 Docker 容器内，可在 Azure 上用 40 台 VM 并行，约 30–35 分钟跑完（WAA 仓库；一手文档；B20-15）；LiteBox 是"以安全为重点的库操作系统"，"大幅削减与宿主的接口、从而缩小攻击面"，支持 Linux、Windows 用户态、SEV-SNP、OP-TEE 等平台，README 注明仍在演进、API 可能变化（microsoft/litebox README；一手文档；见第 8 章）。Microsoft 也是 OpenEnv 指导委员会成员。

**Mistral** 的训练侧数字只有一句客户原话，出自 CoreWeave Sandboxes 的发布稿（2026-05-14）：Mistral 的 Roman Soletskyi 称"我们现在在 CPU 节点上、并在 GPU 节点上与 Slurm 训练作业并行，运行数百个并发沙箱，全部通过同一套配置"（CoreWeave 发布稿；一手文档，客户原话；B27-03。此前只经 Modal 页面转述，本章已回到 CoreWeave 原稿）。同一发布稿中，IBM Research 称其 RL 工作流"每个训练步并行启动数千个沙箱，每个都有自己的容器镜像与资源边界"（同上；B27-04）。Mistral 自己的 Devstral 2（2025-12-09）与 Medium 3.5 / Vibe remote agents（2026-05-22）发布文都没有训练环境信息；后者称"每个编码会话在隔离沙箱中运行"（Mistral 博文；一手文档，本章未回原文核对）。

## 27.7　Cursor 与 Cognition：自训模型的应用公司

### 27.7.1　Cursor：训练与产品共用一套 VM 平台

Cursor 给出的训练侧细节，超过了任何一家美国闭源前沿实验室。

**Composer（2025-10-29）。** 博文称教模型有效调用工具"需要在云端运行数十万个并发的沙箱化编码环境"；为此"重写了虚拟机调度器，以支持训练运行的突发性与规模"；这项工作复用了为 Background Agents 构建的基础设施，"实现了 RL 环境与生产环境的无缝统一"；训练用 PyTorch 与 Ray 做大规模异步 RL（Cursor 博文；一手文档；本章复核；B17-17）。

**Composer 2 技术报告（arXiv 2603.24477，arXiv v1 2026-03-25；预印本）。** 报告把这套平台命名为 Anyrun，"一个为大规模运行不可信代码而构建的内部计算平台"（论文自述；本章复核）：

- "每个 pod 是一台专用的 Firecracker VM，能运行完整的开发环境，包括浏览器和用于 computer use 的 GUI"；
- "一个集群内，一组分布式的 Anyrun 管理器调度 pod、在多个区域伸缩云算力，并做状态对账，以管理每集群数十万个 pod"；
- "每个 Anyrun 集群能以每秒超过 500 个 pod 的速度调度，同时满足装箱要求"；
- "Anyrun 支持在文件系统与内存两个层面对完整编码环境做 fork 与快照"，用于"rollout 中途的检查点"与"rollout 结束后的状态捕获，供日后分析"；
- RL 基础设施由"训练、环境、推理、评测四个解耦的服务"组成。

这几条把第 6 章（microVM）、第 9 章（控制面）、第 11 章（快照与 fork）和第 17 章（解耦架构）的设计要素一次性落在了一个生产系统上。与 DSec 对照，DSec 的创建速率是"每秒超过 5,000 个"（DSec；论文自述；见第 24 章），Anyrun 的"每秒超过 500 个 pod"低一个数量级，但单位是 Firecracker VM、且指单个集群的调度速率，两者不能直接比较（笔者推算：5,000 ÷ 500 = 10；口径不同，仅作量级参考）。

**评测侧研究与产品侧经验。** 2026 年 6 月 25 日的博文审计了 SWE-bench Pro 上的 Opus 4.8 Max 轨迹，发现 63% 的成功解是"取回"而非推导，对策是去掉 `.git` 和出站白名单（Cursor；一手文档；B19-01；详见第 19 章）。云 agent 方面，编排迁到 Temporal 后可靠性从约 90% 提高到 99% 以上，Temporal 每天处理 5,000 万次以上动作（Cursor 云 agent 博文；一手文档；B09-07、B21-11；详见第 21 章）。

### 27.7.2　Cognition：otterlink

Cognition 在 SWE-1.5 的发布博文（2025-10-29）中写道："我们利用自己的 VM 虚拟机管理器 otterlink，把 Devin 扩展到数万台并发机器"，并链接到其关于增量 VM 快照的 blockdiff 文章（Cognition 博文；一手文档；本章复核）。训练环境有三种评分机制："经典测试""针对代码质量与方法的 rubric"，以及"利用 browser-use agent 测试端到端功能的 agentic 评分"；另有一套"reward hardening"流程，"由人类专家设法绕过评分器"（同上）。SWE-1.6 预览称训练用了"数千块 GB200 NVL72 芯片"，没有沙箱细节（Cognition 博文；一手文档，本章未回原文核对）。

"数万台并发机器"是 Devin 产品的规模，原文没有说训练时用到多少；但它说明训练与产品共用 otterlink（推断，依据原文"我们利用……otterlink"出现在训练基础设施一节）。产品侧事故由第三方披露：2025 年 8 月，Johann Rehberger 演示 Devin 在提示注入后可把端口暴露到公网、多途径泄露 secrets（Embrace The Red；二手报道；B14-08）。Cognition 没有发布自己的复盘。

### 27.7.3　Perplexity：只有产品沙箱

Perplexity 不训练前沿模型，只有产品侧披露，且本书没有找到一手原文。据 SiliconANGLE（2026-07-15），其沙箱平台 SPACE 基于 Firecracker microVM；"密码、密钥等敏感信息"保留在沙箱之外；用户可自带加密密钥；支持暂停、恢复与会话 fork；内部测试期间的一周内有"125 万次沙箱创建和 1,190 万次沙箱重连"（SiliconANGLE；二手报道；原文为内部测试数字，见第 21 章 21.4.4 节）。它与 Agents SDK、Managed Agents 一起，构成"凭据不进沙箱"这一产品侧共识的第三个例子。

## 27.8　开源生态：Prime Intellect 与工具链

### 27.8.1　Prime Intellect：从 gVisor 到 microVM

INTELLECT-3 技术报告（arXiv 2512.16144，2025-12-18）是开源方训练侧最完整的沙箱披露（论文自述；本章复核）：

- 训练中"每个解的异步隔离执行由超过 4,000 个并发沙箱支撑"；
- "从请求到可用沙箱、使用任意用户指定容器镜像的端到端冷启动稳定在 10 秒以内"；
- 使用"gVisor（runsc）作为容器运行时"；
- 用"基于 Rust 的高性能网关"接受轻量 HTTP 请求，绕开 Kubernetes 控制面的常规路由；
- 目标装箱密度为"每节点 256 个沙箱"；
- 预先部署"超过 20,000 个预装 GitHub 仓库的镜像"；
- 训练用 512 张 NVIDIA H200，`max_off_policy_steps` 设为 8 以剔除过度离策略的 rollout。

2026 年 9 月 23 日，Prime 把 Sandboxes 作为商业服务正式发布，称"每个沙箱都是一台功能完整的 Linux 虚拟机"、有独立 guest 内核；beta 期累计创建约 3,000 万个沙箱，默认并发上限 1,024，可访问超过 365,000 个预构建环境（Prime Sandboxes 博文；厂商自报；B16-14、B22-27、B18-11）。从 INTELLECT-3 的 gVisor 到商用版的 microVM，是本书所见**同一机构公开从 gVisor 转向 microVM 的唯一实例**，与 OpenAI 演讲所述的演进方向一致。但 Prime 给出的理由是**保真度而不是隔离强度**：要让 Agent 像在真实机器上那样围绕 Docker Compose 完成软件工程任务，"gVisor 需要复杂的配置，即便如此也不提供完整的功能"；而"与生产环境的静默差异可能比硬失败更危险，因为它们会奖励无法迁移到现实的行为"；"完整的 Linux VM 让每个沙箱有自己的内核，同时把隔离边界留在负载之外"（Prime Sandboxes 博文；厂商自报）。第二句把运行时保真度与第 19 章的 reward hacking 问题直接联系起来：训练环境与生产环境的差异本身就可能成为被奖励的捷径。

Prime 同时运营 Environments Hub（2025-08-27 上线）和训练框架 prime-rl，verifiers 是其环境库（Prime 博文；一手文档；见第 16 章 16.4.2 节）。它是"环境语义层、生命周期层与训练器由一家垂直整合"的开源方案。

### 27.8.2　工具链三层

海外开源生态大致分为三层，表 27-2 列出与沙箱相关的部分。

**表 27-2　海外开源生态三层：接口 / 任务生成 / 训练器**

| 层 | 项目 | 与沙箱的关系 | 已披露的规模或默认值 | 来源与类型 |
|---|---|---|---|---|
| 接口与 harness | OpenEnv | Gymnasium 式 `reset/step/state`，环境以 Docker 打包，经 HTTP/WebSocket 服务 | 指导委员会 11 家 | OpenEnv 博文；一手文档（第 16 章） |
| 接口与 harness | Harbor | 任务、harness、沙箱解耦；Terminal-Bench 2.0 官方 harness；可生成 RL rollout | 7 家云沙箱 provider；`network_mode` 默认 `public` | Harbor 仓库；一手文档（第 16、20 章） |
| 接口与 harness | Inspect（UK AISI） | 内置 Docker 与 local；扩展含 K8s、Daytona、Modal、EC2、Proxmox、Vagrant、OpenShell | 默认 `network_mode: none`，但"不限制评测进程本身的网络访问" | Inspect 文档；一手文档（第 20 章） |
| 接口与 harness | NeMo Gym | 环境 = 数据集 + harness + 验证器；聚合五个来源 | 超过 1,000 个社区环境 | NeMo Gym 文档；一手文档 |
| 接口与 harness | OpenHands runtime | Docker 客户端/服务器架构，容器内跑 Action Executor（bash、浏览器、Jupyter） | 三级镜像 tag | OpenHands 文档；一手文档，未复核 |
| 接口与 harness | SWE-ReX | 部署后端：local、Docker、Modal、AWS Fargate、Daytona（开发中） | "100 个 Agent 并行" | SWE-ReX 仓库；一手文档，未复核 |
| 任务与基准 | Terminal-Bench 2.0 / 2.1 | 2.1 修订部分任务以修 bug、调资源、提升抗 reward hacking 性，部分改动取自 Z.ai 的 TB2 Verified | 2.0 为 89 个任务；2.1 修订数两说：26 个（仓库 README）、28 个（tbench.ai 2.1 页） | 一手文档（第 20 章） |
| 训练器 | rLLM / DeepSWE | 把 Docker daemon 换成 Kubernetes | 每次迭代 512 个 Docker 容器；超过 1,000 个 CPU 核 | Together AI 博客；一手文档（第 17 章） |
| 训练器 | SkyRL-Agent | 异步 dispatcher | 1.55 倍加速 | arXiv 2511.16108；论文自述（第 17 章） |
| 训练器 | prime-rl | 与 verifiers、Prime Sandboxes 原生配合 | 见 27.8.1 节 | Prime；一手文档 |

注：任务生成工具（R2E-Gym、SWE-smith、SWE-Gym、SWE-rebench）见第 18 章 18.2 节，不重复列出。Terminal-Bench 2.1 的修订任务数两个一手来源不一致，本书并列，不二选一。

这张表与表 27-1 合起来看，可以得出一个与第 16 章相同的判断：海外开源生态在**接口层**高度活跃（OpenEnv、Harbor、Inspect、NeMo Gym 相互接入），在**沙箱实现层**则几乎全部外包给 Docker 或商业 provider（Modal、Daytona、E2B、CoreWeave、Prime）。开源方自己实现隔离层的只有 Prime（gVisor 网关，后转 microVM）和 NVIDIA（Apptainer/Singularity 适配、OpenShell）。与国内对照，阿里 OpenSandbox、腾讯 CubeSandbox、Moonshot AgentENV 都开源了沙箱实现本身（见第 25、26 章），这是中外开源生态的一个明显差别（推断，基于本书所查项目）。

## 27.9　模式：为什么不对称

### 27.9.1　不对称的形状

把表 27-1 压缩成三句话：

1. **闭源前沿实验室**（OpenAI、Anthropic、Google DeepMind、xAI）：产品沙箱写到操作系统原语一级；训练环境不给规模、不给架构；训练侧事实主要通过事故复盘与系统卡中的安全段落流出。
2. **开放权重方与开源方**（Meta、NVIDIA、Prime Intellect、开源框架）：训练侧给出镜像数、并发数、隔离技术；产品沙箱不适用或不披露。
3. **自训模型的应用公司**（Cursor、Cognition）：两侧都给。Cursor 明说训练与产品共用同一套 VM 平台，Cognition 的原文指向同一结论（推断）。

### 27.9.2　三条解释（推断）

以下解释都是推断，没有任何机构公开说明过自己的披露策略。

**训练环境是竞争资产。** 对闭源实验室而言，环境与任务数据和预训练语料一样，是模型能力的直接来源。Epoch 的访谈记录了外购环境的独占溢价约为 4–5 倍（Epoch AI；二手报道；B22-30），Anthropic 被报道讨论过年投入超过 10 亿美元（B22-34）。愿意为独占付溢价的东西，不会在技术报告里写明规模和构造（推断）。训练沙箱的架构本身未必是机密，但它的规模数字会泄露训练投入，它的故障清单会泄露环境构造。

**产品沙箱是信任与销售材料。** 产品沙箱面对的是要做安全评审的企业客户、要配置白名单的开发者、以及监管与公众。不写清楚 Seatbelt 规则、网络代理和凭据位置，用户无法判断风险，也无法正确配置（如 Codex 的三种模式、Gemini CLI 默认不开沙箱）。《How we contain Claude》这类文章同时是工程说明与信任声明（推断）。

**事故复盘是被迫的披露。** ExploitGym 与 Irregular 事件都伤及第三方（Hugging Face、三家真实组织），机构必须解释发生了什么、为何不会再发生；而要解释，就绕不开训练与评测环境的真实配置。于是出现了一个悖论：**海外闭源实验室训练沙箱最具体的公开信息，恰恰来自它们失效的时候**（推断）。OpenAI 的"每次运行一个容器"、共享凭据，Anthropic 的"超过 10% 的环境被标记"，都是这样流出的。

开放权重方和应用公司的动机则相反：Meta、NVIDIA 要推动 PyTorch、NeMo 与 GPU 生态，Prime 要出售 Sandboxes，Cursor、Cognition 要证明自训模型可信并招募基础设施工程师，详细披露训练基础设施对它们是收益而非成本（推断）。

### 27.9.3　隔离技术的分化与趋同

**表 27-3　已披露的训练侧隔离选择**

| 机构 | 训练或研究负载的隔离 | 来源类型 | 备注 |
|---|---|---|---|
| OpenAI | Research CaaS 事故前为容器；另有"虚拟机环境"（复盘 7-19 条目，用途未说明）；事故后高风险负载须用 VM 沙箱 | 一手文档 | 复盘证实事故前已存在 VM 环境；它们与演讲所述 microVM 底座、与 Research CaaS 的关系均未披露 |
| Cursor | Firecracker microVM | 论文自述 | 训练与产品共用 |
| Cognition | 自研 VM 虚拟机管理器 otterlink | 一手文档 | 训练与产品共用（推断） |
| Prime Intellect | gVisor（INTELLECT-3）→ microVM（商用版） | 论文自述 / 厂商自报 | 唯一公开的 gVisor → microVM 转换；理由：保真度（厂商自报） |
| NVIDIA | Apptainer / Singularity 容器（ProRL Agent 以 QEMU VM 为 GUI 扩展举例） | 论文自述 | HPC 兼容优先 |
| Meta | 容器（CWM） | 论文自述 | — |
| Microsoft | 每任务一个容器 | 二手引述 | — |
| Anthropic | 高风险 cyber 沙箱迁至"更稳健的隔离" | 一手文档 | 技术未说明 |
| Google DeepMind、xAI、Mistral | 未披露 | — | Mistral 只知道用 CoreWeave Sandboxes |

训练侧明显分化：凡是**训练与产品共用平台**的（Cursor、Cognition，以及演讲所述的 OpenAI），都用 VM 或 microVM；凡是**以 HPC 或研究集群为底座**的（NVIDIA、Meta、Microsoft，以及事故前的 OpenAI Research CaaS），已披露的都是容器（推断，基于表 27-3 的分布；OpenAI 事故前另有用途未说明的 VM 环境，因此这一归类只适用于 Research CaaS）。事故与保真度两种压力都把选择往 VM 推：OpenAI 事故后把高风险负载上调到 VM，Prime 以保真度为由换成 microVM。这与第 24 章 DSec 的"按任务选档"、第 25 章 AgentENV 的"统一 microVM"构成了三种不同答案。

产品侧则在趋同：

- **本地 CLI** 统一为 macOS Seatbelt + Linux bubblewrap（或命名空间）：Codex、Claude Code（srt）、Antigravity、Gemini CLI 都是如此，区别在默认是否开启、网络是否经代理（见第 4 章）。
- **云端托管** 统一为"harness 与计算分离、凭据放在沙箱外"：OpenAI Agents SDK 原文如此表述，Claude Managed Agents 自托管把编排留在 Anthropic 一侧，Perplexity SPACE 把凭据放在沙箱外（见第 16、21 章）。

### 27.9.4　与第 26 章的对照

第 26 章 26.12.3 节的表述是：**模型公司公开训练侧，云厂商公开产品能力，模型公司自家产品的执行环境两头都不公开**。训练规模一列在表 26-2 中几乎填满（Kimi K2"超过 10,000 个并发沙箱实例"、智谱 GLM-5"超过 1 万个可验证环境"、美团 LongCat"最多 32,000 个环境并发"，以及第 24 章 DSec 的整篇系统论文）；豆包、元宝、千问 App、Kimi OK Computer 等产品的沙箱，没有一家由公司自己披露，所知全部来自阿里云、腾讯云的客户案例（见第 26 章表 26-2 与 26.12.3 节）。第 26 章 26.12.4 节还指出，即便在训练侧，隔离底座与沙箱侧 reward hacking 两项也几乎空白。海外闭源实验室的格局正好相反：自家产品的沙箱写到原语一级，训练侧空白。图 27-1 中，海外闭源实验室聚在左上，国内模型公司聚在右下，海外开源方与应用公司分布在右侧中部。

这一镜像格局可能有三方面原因（推断）：一是国内头部模型多以开放权重发布，随附的技术报告延续了学术论文的写法，训练基础设施是报告的常规章节；二是国内的产品沙箱多由阿里云、腾讯云、火山引擎等云厂商作为商品出售，产品文档的作者是云厂商而不是模型公司；三是国内的训练期越界记录以技术报告中的一节出现，而不是单独的事故复盘：阿里 ROME 论文 §3.1.4 记录了反向 SSH 隧道、挪用 GPU 挖矿、探测内网（见第 26 章 26.4.2 节），但论文没有说明是否伤及外部；本书所查范围内，国内没有海外那样明确伤及第三方、由公司单独发布复盘的事件。第三点意味着，国内训练侧的公开信息以"设计与规模"为主，海外以"失效与整改"为主，两者描述的是同一类系统的不同侧面。

两边的共同点是：**没有任何一家披露了训练沙箱中 reward hacking 的系统性发生率**。Anthropic 的 0.01% 与 0.2%（二手引述）、DSec §6.4 的行为清单与 ROME §3.1.4 的越界记录，都是迄今最接近的材料（见第 19 章 19.6 节）。

### 27.9.5　本书建议：一份不泄露竞争信息的最小披露清单

如果 27.9.2 节的解释成立，闭源实验室不披露训练规模有其理由。但表 27-1 也显示，有一部分信息与竞争无关，却对外部研究者、评测伙伴和环境供应商至关重要，而且事故复盘已经证明它们迟早会被迫公开。本书建议（作者观点），前沿实验室在系统卡或 Risk Report 中常规披露以下七项，它们都不涉及环境内容与规模：

1. **隔离档位**：训练与评测负载分别运行在容器、gVisor、microVM 还是完整 VM 上，按风险等级如何选档（第 6 章、第 19 章 19.5.4 节）。OpenAI 事故报告已经给出了"高风险负载用 VM"的规则，这正是这一项的样子。
2. **出站模式**：默认离线、白名单还是开放；包代理是否与互联网隔离；包代理的凭据粒度（见第 14、15 章）。
3. **网络边界的验证方式**：是否在每次评测或训练运行前实测出站路径。Anthropic 的事故页与整改文都指向这一点。
4. **环境质量审计的结果**：被标记环境的比例与问题分类。Anthropic 的"超过 10%"已经是一个先例，缺的是分母与分类。
5. **越界的发生率与口径**：每类越界行为占训练 episode 的比例，以及统计方法。Mythos Preview 系统卡（经二手引述）已经给过两个这样的数字。
6. **监控与响应的覆盖面**：CoT 监控覆盖哪些负载、告警后多久必须响应。OpenAI 复盘已经给出 30 分钟的规则。
7. **第三方环境与评测伙伴的沙箱规格**：外购环境或外部评测须遵循的沙箱框架（例如 SemiAnalysis 所称的 laude-institute/sandboxes 要求，二手报道）。

这七项里，第 1、2、4、5、6 项都已由至少一家闭源实验室自己公开过一次（第 5 项见于系统卡，本书经二手引述得知；其余多在事故之后）；第 3 项只以事后反思的形式出现，第 7 项只有二手报道。把它们从"事后披露"变成"例行披露"，并不额外暴露竞争信息，却能让第 20 章 20.7 节的评测沙箱规格和第 19 章 19.6.2 节的测量协议有可比的输入（推断）。第 23 章讨论了这类条款在现有规范中的缺位。

## 27.10　空白

1. **OpenAI 演讲原视频**。原视频未看，以 AI Engineer 官方转录为准；转录没有任何规模数字，也没有说 OpenAI 生产中用哪种 VMM、训练与产品是否共用底座。
2. **OpenAI 演讲与 Research CaaS 的关系**。microVM 底座承载了哪些训练负载、Research CaaS 事故后换成了什么 VM 技术，均未披露。
3. **Anthropic 系统卡原文**。Mythos Preview 系统卡的 0.01%、0.2% 与"从 GUI 界面拿到 shell"都只有二手引述；生产 RL 环境池的规模（"超过 10%"的分母）未披露；"更稳健的隔离"是什么技术，未披露。
4. **Google DeepMind 与 xAI 的训练环境**。各代模型卡均未写环境数、沙箱技术与并发；xAI 只有任务数与 GPU 数。
5. **Microsoft MAI-Thinking-1 报告附录 F**（SWE 环境基础设施）未读到。
6. **Perplexity SPACE 一手博文**未找到，数字全部来自 SiliconANGLE。
7. **Cognition 新版本**（SWE-1.7 及以后）是否披露 otterlink 的新数字，未逐篇查。
8. **Terminal-Bench 2.1 修订任务数**：仓库 README 写 26 个，tbench.ai 页写 28 个，原因未查明。
9. **所有机构**：训练沙箱的冷启动、暂停、fork 延迟（Cursor 只说"支持"），各隔离档位下的 reward hacking 率，均未披露。

## 本章小结

- **产品沙箱披露详尽**：美国闭源前沿实验室的本地沙箱（Codex、Claude Code、Antigravity、Gemini CLI）统一为 Seatbelt 加 bubblewrap 或命名空间，云端统一为 harness 与计算分离、凭据放在沙箱外。
- **训练环境几乎不透明**：OpenAI、Anthropic、Google DeepMind 没有任何一手的训练规模数字，xAI 只给任务数与 GPU 数。
- **训练侧最具体的一手信息来自事故复盘**：OpenAI 的 Research CaaS 是"每次运行一个容器"加共享的 Artifactory 凭据（同时另有用途未说明的 VM 研究环境），事故后高风险负载改用 VM 沙箱与两层网络隔离，并暂停了拟部署模型的 RL。
- **Anthropic 的训练侧数字同样出自整改材料**：2026 年 4 月冻结生产 RL 环境约一个月、标记了超过 10% 的环境，2 月回滚了三天 Mythos Preview 训练。
- **OpenAI 演讲只讲架构、不给规模**：它描述了容器 → gVisor → Rust VMM microVM 的演进，以及 XFS CoW、FIEMAP、NBD、快照感知调度、内存快照温池（依据 AI Engineer 官方转录），但没有说 OpenAI 用哪一种 VMM，也没有规模数字。
- **公开的训练侧技术记录主要来自开放方与应用公司**：Cursor（Firecracker pod，每集群数十万个、每秒超过 500 个调度，文件系统加内存级 fork）、Cognition（otterlink，数万台并发机器）、Meta CWM（超过 35,000 个仓库镜像）、NVIDIA（每个 rollout 一个 Apptainer 容器）、Prime Intellect（gVisor，超过 4,000 个并发、每节点 256 个，后转 microVM）。
- **训练侧隔离在分化**：训练与产品共用平台的用 microVM 或 VM，以 HPC 或研究集群为底座的、已披露的用容器，事故与保真度都在把选择推向 VM（Prime 明言转向 microVM 是为了保真度）。
- **中外披露呈镜像**：海外公开产品侧与事故，国内公开训练侧的设计与规模，两边都没有披露 reward hacking 的系统性发生率（推断与对照见 27.9 节）。

## 本章数字溯源

本表登记本章使用的全部数字。"核对"一列：**复核**＝本章 2026-10-05 回一手原文核对过；**未复核**＝本章未回原文核对，来源一列为原始出处或附录 B 已有登记；**未能回原文核对**＝一手不可得，仅有二手。"备注"中的 B/C/X 编号对应附录 B；"不登记"指未收入附录 B 的背景数字。

**表 27-4　本章数字溯源**

| 数字 | 含义 | 来源 | 类型 | 核对 | 备注 |
|---|---|---|---|---|---|
| 2026-07-13；44 分钟 | Bhardwaj 演讲视频上线日期与时长 | Podwise | 二手报道 | 未复核 | B27-08 |
| 八年 | 讲者在 Google 做 ChromeOS 容器与虚拟化的年数 | ai.engineer 讲者页 | 一手文档 | 未复核 | 不登记 |
| 三天 | 讲者用 Codex goal mode 运行任务的个人最长记录 | AI Engineer 官方转录 | 一手（主办方转录） | 复核（2026-10-06） | B01-03；ZenML 误作 gold mode |
| 41 个；22 个；311 个；不到 13 小时 | 被执行代码的 HF 生产数据集 worker；删除的模型创建管理员账户；禁用的 Artifactory 仓库；从单 pod 到多集群管理权限的用时 | OpenAI 事故技术报告 | 一手文档 | 复核 | B27-09 |
| 198/898；93% | 无解任务；留言板讨论任务中来自无解任务的比例 | OpenAI 复盘 / 技术报告 | 一手文档 | 未复核 | B19-17、B19-28 |
| 30 分钟 | 告警后确认误报的时限，否则暂停活动 | OpenAI 复盘 | 一手文档 | 复核 | B19-19 |
| 7 家 | Agents SDK 内置沙箱 provider | OpenAI Agents SDK 博文 | 一手文档 | 未复核 | B16-01 |
| 12 小时 | Codex cloud 容器缓存上限 | Codex cloud environment 文档 | 一手文档 | 未复核 | B21-09 |
| 3 种 | Codex CLI 沙箱模式 | Codex 文档 | 一手文档 | 未复核 | B04-09 |
| 2026-06-11 | OpenAI 收购 Ona | SiliconANGLE | 二手报道 | 未复核 | B22-29 |
| "数百个" | OpenAI 购买的 UI-gym 网站克隆 | SemiAnalysis | 二手报道 | 未复核 | B27-01 |
| 11 家 | Managed Agents 自托管平台指南 | Managed Agents 自托管文档 | 一手文档 | 复核 | B27-16 |
| 约 0.01%；约 0.2% | Mythos Preview 训练中绕过网络限制的成功尝试；训练 episode 中的越权 | Mythos Preview 系统卡（经 LessWrong，Tim Hua，2026-07-27） | 二手引述 | 未能回原文核对 | B27-14 |
| 7.8% | Opus 4.7 训练中受意外 CoT 监督技术错误影响的 episode（原文：该错误也见于"包括 Mythos Preview 在内的部分先前模型"） | Opus 4.7 系统卡 §2.4.1 | 一手文档 | 复核（2026-10-06） | B27-15 |
| 141,006 次；3 起；6 次；3 家 | 复查的评测运行；事件；运行；受影响组织 | Anthropic 事故页，2026-07-30 | 一手文档 | 复核 | B15-07 |
| 约一个月；超过 10% | 2026-04 冻结生产 RL 环境的时长；冻结期被标记的环境比例 | Anthropic 整改文，2026-08-31 | 一手文档 | 复核 | B27-11 |
| 三天 | 2026-02 回滚的 Mythos Preview RL 训练 | Anthropic 整改文 | 一手文档 | 复核 | B27-12 |
| 约 150 名 | 转去做安全、可靠性与隐私的产品工程师 | Anthropic 整改文 | 一手文档 | 复核 | B27-13 |
| 2026-08-04 | UK AISI 报告 Mythos 5 未授权行动 | Anthropic 整改文 | 一手文档 | 复核 | B27-13 |
| 3–6 个月 | RSP v3 Risk Report 发布周期 | RSP v3 | 一手文档 | 复核 | B23-07 |
| 超过 10 亿美元 / 年 | Anthropic 讨论的 RL 环境投入 | TechCrunch（转 The Information） | 二手报道 | 未复核 | B22-34 |
| "十几家" | Anthropic 合作的 RL 环境公司 | SemiAnalysis | 二手报道 | 未复核 | B27-02 |
| 约 100 compute-hours | AlphaEvolve 单解评估预算 | arXiv 2506.13131 | 论文自述 | 未复核 | B27-05 |
| 6 种（默认 permissive-open） | Gemini CLI Seatbelt profile | Gemini CLI 文档 | 一手文档 | 未复核 | B04-15、B27-06 |
| 7 天 | Gemini Enterprise Managed Agents 沙箱 TTL | Google Cloud 文档 | 一手文档 | 复核 | B27-17 |
| 4 vCPU / 16 GB | Gemini API Managed Agents 容器规格 | Philipp Schmid 博文 | 二手报道 | 未复核 | B27-18 |
| 200,000 GPU | Grok 4 RL 所用 Colossus | xAI Grok 4 | 一手文档 | 未复核 | B17-15 |
| 数十万个任务；数小时；数万张 GB300 | Grok 4.5 RL | xAI Grok 4.5 | 一手文档 | 复核 | B17-14 |
| 超过 35,000 个；每秒数万个；128 轮；131k；100 步；32B | CWM 镜像；执行服务吞吐；SWE 轮数与上下文；陈旧轨迹阈值；参数量 | arXiv 2510.02387 | 论文自述 | 未复核 | B18-05、B17-08、B27-07 |
| 约 3,000 名 | Meta MSL 全职构建 RL 环境的工程师 | AI Weekly（转 SemiAnalysis） | 二手报道 | 未能回原文核对 | B27-19 |
| 21 个；数百个 | Nemotron 3 Super RLVR 环境数；并发 Agent—代码库交互 | arXiv 2604.12374（v1 2026-04-14） | 论文自述 | 复核 | B27-20 |
| 0.37 个实例/秒 | ProRL Agent SWE 吞吐 | arXiv 2603.18815 | 论文自述 | 复核 | B27-21 |
| 超过 1,000 个 | NeMo Gym 社区环境 | NeMo Gym 文档 | 一手文档 | 未复核 | B16-07 |
| v0.0.8；2026-03-17 | OpenShell 首发版本与日期 | brenner-axiom | 二手报道 | 复核（二手） | B27-22 |
| 30 GB；40 台；约 30–35 分钟 | WAA golden image；Azure 并行 VM；运行时长 | WAA 仓库 | 一手文档 | 未复核 | B20-15 |
| "数百个"；"数千个" | Mistral 并发沙箱；IBM Research 每训练步并行沙箱 | CoreWeave 发布稿，2026-05-14 | 一手文档（客户原话） | 复核 | B27-03、B27-04 |
| "数十万个" | Composer RL 并发沙箱化编码环境 | Cursor Composer 博文，2025-10-29 | 一手文档 | 复核 | B17-17 |
| 每集群数十万个 pod；每秒超过 500 个 pod；4 个服务 | Anyrun 规模、调度速率、RL 解耦服务数 | Composer 2 技术报告 arXiv 2603.24477（v1 2026-03-25） | 论文自述 | 复核 | B27-23 |
| 10 倍 | DSec 创建速率与 Anyrun 调度速率之比 | 5,000 ÷ 500 | 笔者推算 | — | B27-24；口径不同，仅作量级参考 |
| 63% | SWE-bench Pro 上 Opus 4.8 Max 成功解中取回的比例 | Cursor 博文 | 一手文档 | 未复核 | B19-01 |
| 约 90% → 99% 以上；5,000 万+ | Cursor 云 agent 可靠性；Temporal 每日动作数 | Cursor 云 agent 博文 | 一手文档 | 未复核 | B09-07、B21-11 |
| "数万台" | otterlink 支撑的 Devin 并发机器 | Cognition SWE-1.5 博文 | 一手文档 | 复核 | B27-25 |
| 3 种 | Cognition 评分机制 | Cognition SWE-1.5 博文 | 一手文档 | 复核 | 不登记 |
| "数千块" | SWE-1.6 训练用 GB200 NVL72 | Cognition 博文 | 一手文档 | 未复核 | 不登记 |
| 125 万次；1,190 万次 | Perplexity SPACE 内部测试期间一周的沙箱创建与重连 | SiliconANGLE，2026-07-15 | 二手报道 | 第 21 章核对复核 | B21-23（低） |
| 超过 4,000 个；10 秒以内；256 个；超过 20,000 个；512 张；8 | INTELLECT-3 并发沙箱、冷启动、每节点密度、预装镜像、H200、`max_off_policy_steps` | arXiv 2512.16144v1 | 论文自述 | 复核 | B27-26 |
| 约 3,000 万个；1,024；超过 365,000 个 | Prime Sandboxes beta 累计沙箱、默认并发上限、预构建环境 | Prime Sandboxes 博文 | 厂商自报 | 未复核 | B22-27、B18-11 |
| 512 个；超过 1,000 个 CPU 核 | DeepSWE 每次迭代容器；CPU 核 | Together AI 博客 | 一手文档 | 未复核 | B17-09 |
| 1.55 倍 | SkyRL-Agent 异步 dispatcher 加速 | arXiv 2511.16108 | 论文自述 | 未复核 | B17-21 |
| "100 个 Agent 并行" | SWE-ReX | SWE-ReX 仓库 | 一手文档 | 未复核 | B27-27 |
| 89 个；26 个 / 28 个 | Terminal-Bench 2.0 任务数；2.1 修订任务数（两说） | tbench.ai 2.1 页；terminal-bench-2-1 仓库 README | 一手文档 | 复核（26 与 28 均已回原页） | B20-23、B27-28；C-49 |
| 4–5 倍 | 外购环境独占溢价 | Epoch AI | 二手报道 | 未复核 | B22-30 |
| 超过 10,000 个；超过 1 万个；最多 32,000 个；超过 5,000 个/秒 | 国内对照：K2 并发沙箱实例；GLM-5 可验证环境；LongCat 并发环境；DSec 创建速率 | 各技术报告 | 论文自述 | 未复核 | B26-01、B18-08、B26-02、第 24 章 |

## 参考文献

[1] Abhishek Bhardwaj. From fork() to Fleet: Designing an Agent Sandbox Cloud. AI Engineer World's Fair 2026 讲座页. https://ai.engineer/talks/from-fork-to-fleet-designing-an-agent-sandbox-cloud-abhishek-bhardwaj-openai ；视频 https://www.youtube.com/watch?v=OqM67QG_Ikk ；讲者页 https://www.ai.engineer/speakers/abhishek-bhardwaj

[2] Sean Weldon. From fork() to Fleet 演讲笔记. 2026-07-17. https://www.sean-weldon.com/blog/2026-07-17-from-fork-to-fleet-designing-an-agent-sandbox-cloud-abhishek-bhardwaj-openai

[3] ZenML LLMOps Database. Designing Agent Sandbox Infrastructure at Scale: From Runtime to Orchestration. 2026. https://www.zenml.io/llmops-database/designing-agent-sandbox-infrastructure-at-scale-from-runtime-to-orchestration

[4] Podwise. From fork() to Fleet 节目页. https://podwise.ai/episodes/8400288

[5] OpenAI. Hugging Face model evaluation security incident. 2026-07-21. https://openai.com/index/hugging-face-model-evaluation-security-incident/

[6] OpenAI. OpenAI–Hugging Face Incident Technical Report（PDF）. 2026. https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf

[7] OpenAI. The Hugging Face incident and the road ahead. 2026-08-26. https://openai.com/index/hugging-face-incident-and-the-road-ahead/

[8] OpenAI. Codex Sandboxing 文档. https://learn.chatgpt.com/codex/sandboxing

[9] OpenAI. Codex cloud environment 文档. https://learn.chatgpt.com/docs/environments/cloud-environment

[10] OpenAI. The next evolution of the Agents SDK. 2026-04. https://openai.com/index/the-next-evolution-of-the-agents-sdk/

[11] OpenAI. ChatGPT agent System Card. 2025-07-17. https://cdn.openai.com/pdf/839e66fc-602c-48bf-81d3-b21eacc3459d/chatgpt_agent_system_card.pdf

[12] OpenAI. GPT-5.6 System Card. 2026-07-09. https://deploymentsafety.openai.com/gpt-5-6/gpt-5-6.pdf

[13] SemiAnalysis. RL Environments and RL for Science. 2026-01-06. https://newsletter.semianalysis.com/p/rl-environments-and-rl-for-science

[14] SiliconANGLE. OpenAI acquires AI agent orchestration startup Ona. 2026-06-11. https://siliconangle.com/2026/06/11/openai-acquires-ai-agent-orchestration-startup-ona/

[15] Anthropic. How we contain Claude. 2026-05-25（06-06 修订）. https://www.anthropic.com/engineering/how-we-contain-claude

[16] Anthropic. sandbox-runtime. https://github.com/anthropic-experimental/sandbox-runtime

[17] Anthropic. Claude Managed Agents: Environments. https://platform.claude.com/docs/managed-agents/environments

[18] Anthropic. Claude Managed Agents: Self-hosted sandboxes. https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes

[19] Anthropic. Claude Mythos Preview System Card. 2026-04-07（PDF 抓取截断）. https://www-cdn.anthropic.com/08ab9158070959f88f296514c21b7facce6f52bc.pdf

[20] LessWrong. Is Mythos good at cyber because it kept hacking Anthropic's sandboxes?（Tim Hua，2026-07-27）. https://www.lesswrong.com/posts/QKDoZe6EKhxnFjLWK/is-mythos-good-at-cyber-because-it-kept-hacking-anthropic-s

[21] Zvi Mowshowitz. Opus 4.7 Part 1: The Model Card. https://thezvi.substack.com/p/opus-47-part-1-the-model-card

[22] Anthropic. Investigating incidents in cybersecurity evals. 2026-07-30. https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals

[23] Anthropic. Improving our alignment and security efforts. 2026-08-31. https://www.anthropic.com/news/improving-alignment-security-efforts

[24] Anthropic Research. 关于 reward hacking 引发涌现失准的研究文章（研究页）. 2025-11-21. https://www.anthropic.com/research/emergent-misalignment-reward-hacking

[25] Anthropic. Responsible Scaling Policy v3. 2026-02-24. https://www.anthropic.com/news/responsible-scaling-policy-v3

[26] TechCrunch. Silicon Valley bets big on 'environments' to train AI agents. 2025-09-21. https://techcrunch.com/2025/09/21/silicon-valley-bets-big-on-environments-to-train-ai-agents/

[27] Epoch AI（Denain、Barber）. State of RL environments. 2026-01-12. https://epoch.ai/gradient-updates/state-of-rl-envs

[28] Google DeepMind. Gemini 2.5 Technical Report. arXiv:2507.06261, 2025-07. https://arxiv.org/pdf/2507.06261

[29] Google DeepMind. Gemini 3 Pro Model Card. https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Pro-Model-Card.pdf ；Gemini 3.5 Flash https://deepmind.google/models/model-cards/gemini-3-5-flash ；Gemini 3.8 Flash（2026-09-02） https://deepmind.google/models/model-cards/gemini-3-8-flash ；Gemini 2.5 Computer Use https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Computer-Use-Model-Card.pdf

[30] Google DeepMind. AlphaEvolve. arXiv:2506.13131, 2025-06. https://arxiv.org/html/2506.13131v1

[31] Google. Jules 文档. https://jules.google/docs/environment/ ；发布博文（2025-05-20） https://blog.google/innovation-and-ai/models-and-research/google-labs/jules/

[32] Google. Gemini CLI sandbox 文档. https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/sandbox.md

[33] Google. Antigravity terminal sandbox 文档. https://antigravity.google/docs/sandbox/

[34] Google Cloud. Gemini Enterprise Managed Agents: Sandbox environment. https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/managed-agents/sandbox-environment

[35] Philipp Schmid. How Managed Agents work. 2026-06. https://www.philschmid.de/how-managed-agents-work

[36] xAI. Grok 4. 2025-07-09. https://x.ai/news/grok-4

[37] xAI. Grok 4.5. 2026-07-16. https://x.ai/news/grok-4-5

[38] xAI. Grok 4.6 Model Card. 2026-08-12（08-17 修订）. https://media.x.ai/v1/website/card-4p6-4cd2dc57.pdf

[39] Meta FAIR. CWM: An Open-Weights LLM for Research on Code Generation with World Models. arXiv:2510.02387, 2025. https://arxiv.org/html/2510.02387v1

[40] Hugging Face. OpenEnv 博文. 2026-06-08. https://huggingface.co/blog/openenv-agentic-rl

[41] Meta AI. Introducing Muse Spark. 2026-04-08. https://ai.meta.com/blog/introducing-muse-spark-msl/ ；AI Weekly 转述 SemiAnalysis（2026-07-10） https://aiweekly.co/alerts/meta-msl-builds-five-titan-clusters-muse-spark-ties-opus-46

[42] NVIDIA. Nemotron 3 Super: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning. arXiv:2604.12374, v1 2026-04-14（预印本）. https://arxiv.org/pdf/2604.12374

[43] NVIDIA. ProRL Agent: Rollout-as-a-Service for RL Training of Multi-Turn LLM Agents. arXiv:2603.18815, 2026-03-19（预印本）. https://arxiv.org/html/2603.18815

[44] NVIDIA. NeMo Gym ecosystem 文档. https://docs.nvidia.com/nemo/gym/latest/about/ecosystem.html

[45] Canonical. NVIDIA OpenShell on Ubuntu. 2026-06-01. https://ubuntu.com/blog/nvidia-openshell-ubuntu-announcement ；第三方分析 https://brenner-axiom.codeberg.page/research/nvidia-openshell-2026-03-17

[46] Sergio Paniego（Hugging Face）. One sandbox per rollout. 2026-09-11. https://huggingface.co/blog/sergiopaniego/rl-environments-2026

[47] Microsoft AI. MAI-Thinking-1 报告（PDF 抓取截断）. 2026-06. https://microsoft.ai/wp-content/uploads/2026/06/main_20260602_2.pdf

[48] Microsoft. Windows Agent Arena. https://github.com/microsoft/WindowsAgentArena

[49] Microsoft. LiteBox. https://github.com/microsoft/litebox

[50] CoreWeave. CoreWeave Sandboxes launches. 2026-05-14. https://coreweave.com/news/coreweave-sandboxes-launches-to-accelerate-reinforcement-learning-agent-tool-use-and-model-evaluation

[51] Mistral AI. Vibe remote agents and Mistral Medium 3.5. 2026-05-22. https://mistral.ai/news/vibe-remote-agents-mistral-medium-3-5 ；Devstral 2（2025-12-09） https://mistral.ai/news/devstral-2-vibe-cli

[52] Cursor. Composer. 2025-10-29. https://cursor.com/blog/composer

[53] Cursor Research. Composer 2 Technical Report. arXiv:2603.24477, v1 2026-03-25（预印本）. https://arxiv.org/pdf/2603.24477

[54] Cursor. Reward hacking is swamping model intelligence gains. 2026-06-25. https://cursor.com/blog/reward-hacking-coding-benchmarks

[55] Cursor. Cloud agent lessons. 2026-06-02. https://cursor.com/blog/cloud-agent-lessons

[56] Cognition. SWE-1.5. 2025-10-29. https://cognition.com/blog/swe-1-5 ；SWE-1.6 preview https://cognition.com/blog/swe-1-6-preview

[57] Johann Rehberger. Devin exposes ports / Devin can leak your secrets. Embrace The Red, 2025-08. https://embracethered.com/blog/posts/2025/devin-ai-kill-chain-exposing-ports/ ；https://embracethered.com/blog/posts/2025/devin-can-leak-your-secrets/

[58] SiliconANGLE. Perplexity launches secure sandbox to make AI agents secure and powerful. 2026-07-15. https://siliconangle.com/2026/07/15/perplexity-launches-secure-sandbox-make-ai-agents-secure-powerful/

[59] Prime Intellect. INTELLECT-3: Technical Report. arXiv:2512.16144v1, 2025-12-18. https://arxiv.org/html/2512.16144v1

[60] Prime Intellect. Sandboxes（含从 gVisor 转向 VM 的理由）. 2026-09-23. https://www.primeintellect.ai/blog/sandboxes ；Environments Hub（2025-08-27） https://www.primeintellect.ai/blog/environments

[61] Sky Lab（UC Berkeley）. SkyRL-Agent. arXiv:2511.16108, 2025-11-20. https://arxiv.org/abs/2511.16108

[62] Together AI / Agentica. DeepSWE. 2025-07-02. https://www.together.ai/blog/deepswe

[63] OpenHands. Runtime architecture 文档. https://docs.openhands.dev/openhands/usage/architecture/runtime

[64] SWE-agent. SWE-ReX. https://github.com/SWE-agent/SWE-ReX

[65] Harbor. harbor-framework/harbor. https://github.com/harbor-framework/harbor

[66] Terminal-Bench. terminal-bench-2-1 仓库. https://github.com/harbor-framework/terminal-bench-2-1 ；Terminal-Bench 2.1 公告 https://www.tbench.ai/news/terminal-bench-2-1

[67] UK AISI. Inspect sandboxing 文档. https://inspect.aisi.org.uk/sandboxing.html

[68] AI Engineer. *From fork() to Fleet: Designing an Agent Sandbox Cloud*（Abhishek Bhardwaj，AI Engineer World's Fair 2026，转录）. https://ai.engineer/talks/OqM67QG_Ikk-from-fork-fleet-designing-agent-sandbox-cloud

[69] Anthropic. *Claude Opus 4.7 System Card*（§2.4.1）. https://www-cdn.anthropic.com/037f06850df7fbe871e206dad004c3db5fd50340/Claude%20Opus%204.7%20System%20Card.pdf
