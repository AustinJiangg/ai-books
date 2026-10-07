# 第 1 章　什么是 Agent 沙箱（三场景：训练 / 评测 / 产品推理）

## 本章导读

"沙箱"这个词在 2026 年同时指三样东西。用户在对话产品里让模型跑一段 Python，背后是一个用完即弃的容器；一家实验室训练编码 Agent，一个作业就可能请求上万个沙箱，每个都要在几秒内就位、持续几十分钟到几小时、随时可能因为 GPU 作业被抢占而暂停；一个评测团队跑一轮安全评测，只有几百个任务，却要保证里面那个能力最强的模型碰不到真实的互联网。三者都叫 Agent 沙箱，用的也常常是同一类隔离技术，但它们对吞吐、时延、状态、成本和对手的要求，常常方向相反。

本章是全书的总论，回答两个问题：同一个"沙箱"为什么在训练、评测、产品推理三种场景里要做相反的取舍？这些取舍又为什么最终落在同一套底座上？本章不展开具体机制，只给出把后文各章串起来的框架。图 1-1 先给出全书的结构，1.5 节逐项解释。

```mermaid
flowchart LR
    W["负载刻画<br/>第 3 章"]
    subgraph S["三场景（第 1 章）"]
        direction TB
        T["训练 rollout<br/>第 17–19 章"]
        E["评测<br/>第 20 章"]
        P["产品推理<br/>第 21 章"]
    end
    ST(["第二主线：状态<br/>贯穿 ⑤ ⑦ ⑧ 层<br/>沙箱内可回滚（第 11 章）<br/>沙箱外须事务化或禁止<br/>（第 12 章）<br/>出站只读、预填充<br/>（第 14–15 章）"])
    subgraph L["八层架构（第 9 章）"]
        direction TB
        L1["① 接入与 API · 第 16 章"]
        L2["② 控制面 · 第 9 章"]
        L3["③ 节点运行时 · 第 4–8 章"]
        L4["④ 镜像与存储 · 第 10 章"]
        L5["⑤ 状态管理 · 第 11–12 章"]
        L6["⑥ 密度与资源 · 第 13 章"]
        L7["⑦ 网络与出站<br/>第 14–15 章"]
        L8["⑧ RL 集成与完整性<br/>第 17–19 章"]
        L1 --> L2 --> L3 --> L4 --> L5 --> L6 --> L7 --> L8
    end
    subgraph A["两类对手（第 2 章）"]
        direction TB
        A1["被利用的代理人<br/>主要见第 14、15、<br/>21、23 章"]
        A2["作为对手的模型<br/>主要见第 15、19、<br/>20、24 章"]
    end
    subgraph CF[" "]
        direction TB
        C["案例与产业<br/>第 22–27 章"] --> F["开放问题<br/>第 28 章"]
    end
    W --> L
    S --> L
    ST -.-> L
    L --> A
    L --> CF
```

**图 1-1　全书结构图：三场景 × 八层 × 两类对手，"状态"主线贯穿**（示意图，依据目录 v2 总纲与第 9 章表 9-1 绘制；"两类对手"一栏只列主要章节，完整索引见第 2 章表 2-2）

读完本章，读者应能：

- 说清"Agent 沙箱"与"环境""沙箱平台"的区别，以及它为什么从产品里的一项功能变成了 RL 训练的底座；
- 用表 1-1 的八个维度比较训练、评测、产品推理三种场景，知道每一格的出处，以及哪些格至今"未披露"；
- 解释为什么 Agent 训练负载不是 serverless 负载，以及这个判断推出了第三部分的哪些设计；
- 理解"接口可以共用、后端不能共用"的含义，知道分歧落在八层中的哪几层；
- 使用 1.5 节的全书地图、证据标注约定、主要判断与读者路线图，找到自己要读的章节。

## 1.1　从 Code Interpreter 到 RL 底座

### 1.1.1　一个定义

本书所说的 **Agent 沙箱**（agent sandbox），是为 LLM Agent 执行代码、调用工具、操作界面而提供的隔离执行实例，以及让它可以被成批创建、暂停、回收的配套设施（附录 A）。它要和两个相邻概念分开：

- **环境**（environment）是 RL 与评测语义上的"任务世界"，即任务、harness（外壳/评测框架，负责驱动 Agent 循环、工具与打分）与验证器的组合，通常跑在一个或多个沙箱里。"1 万个环境"和"1 万个沙箱"不是一回事（见第 18 章）。
- **沙箱平台**是包含控制面、存储、网络等在内的整套系统。DeepSeek 在 DSec 论文中说，支撑 Agent 负载"需要一个弹性执行平台，而不是单一的沙箱运行时"（requires an elastic execution platform rather than a single sandbox runtime）（DSec §1；论文自述；arXiv 预印本）。本书第三部分讨论的正是这样的平台。

Agent 沙箱与早期的"代码解释器"也不同：后者执行一段代码、返回结果就结束；前者要在同一个实例里多轮改文件、装依赖、起服务，有状态、寿命长（附录 A）。下面会看到，正是"有状态"把沙箱从一项产品功能推成了一类基础设施。

### 1.1.2　三个阶段

沙箱进入大模型产品，最早的形态是代码解释器：用户上传一个文件，模型写一段代码，在一个一次性容器里跑完。ChatGPT 代码解释器没有一手架构披露，研究者通过提示注入看到的是一个 Debian 容器，上传文件位于 `/mnt/data`（0DIN，2024-11-14；二手报道，逆向；见第 21 章）。这一阶段的沙箱是产品的一个功能部件，设计假设是"沙箱里只有用户这次上传的文件"（见 21.1 节）。

第二阶段，沙箱成了可以单独购买的服务。E2B 一类厂商以 API 出售隔离执行实例，Manus 2025 年用 E2B 的 Firecracker microVM（微虚拟机）为每个任务提供一台云端虚拟计算机（E2B 客户案例，2025-05-06；厂商自报；附录 B C-05）。产品形态从"执行一段代码"变成"让 Agent 在一台电脑里工作几个小时"，状态开始跨轮次、跨会话保留。

第三阶段，沙箱成了 Agent RL 训练的底座。Hugging Face 2026 年 9 月的综述博文以 *One sandbox per rollout* 为题概括了这一变化（HF 博文，2026-09-11；二手报道）。博文引用了 Liquid AI 对其 LFM2.5 模型训练的描述："每次 rollout（一次策略与环境交互直至结束的完整采样过程，也称轨迹展开）都运行在一个有独立运行时的专属沙箱中"（Each rollout runs in a dedicated sandbox with its own runtime）（HF 博文转引 Liquid AI；二手引述）。规模随之上了几个数量级：Kimi K2 报告称其 Kubernetes 沙箱基础设施支持"超过 10,000 个并发沙箱实例"（K2 技术报告 §3.2.1；论文自述）；Cursor 称训练 Composer"需要在云端运行数十万个并发的沙箱化编码环境"（Cursor Composer 博文，2025-10-29；一手文档）；DSec 的单个规模单元在典型的一天里服务约 300 万个沙箱，峰值并发约 38 万（摘要称超过 380,000），创建速率超过每秒 5,000 个（DSec §2.4、摘要；论文自述）。Kimi K3 把"带持久化 rollout 状态与沙箱状态的百万 token Agent RL"写进了技术报告摘要（"million-token agentic RL with persistent rollout and sandbox states"）（Kimi K3 技术报告摘要，arXiv 2607.24653 v2，2026-08-07；论文自述）。

引用这些数字时要先看单位。K2 的 1 万以上是并发沙箱实例；K2.5 的"最多 10 万"是 Rollout Manager 编排的并发 agent **任务**，不是并发沙箱（K2.5 技术报告；论文自述；附录 B C-09、X-09）；DSec 的 38 万是并发沙箱，每秒 5,000 个以上是创建速率。三种口径不能互相换算（见第 3、9、26 章）。

### 1.1.3　DSec 的分类：问题从哪里来

在相关工作一节，DSec 把已有系统分成几类，每一类都只覆盖 Agent 训练负载的一部分（DSec §9；论文自述；分类的完整讨论见 24.1.4 节）：

- **serverless 系统**（SAND、REAP、TrEnv、RunD）"为短命、无状态的函数优化冷启动延迟与资源共享"；
- **面向推理的系统**（OpenAI Code Interpreter、E2B、Kimi-K2.5 的 Agent Swarm）；
- **训练系统**（小米 MiMo-V2-Flash、智谱 ComputerRL）"提到了各自的执行环境，但主要关注模型与训练设计"；
- **RL 框架**（slime、veRL、OpenRLHF、Seer）"把执行环境当作黑盒，假定沙箱可用且配置正确"（They treat the execution environment as a black box, assuming that sandboxes are available and correctly configured）。

这组划分本身就是一个论点：产品侧有成熟的沙箱服务，RL 侧有成熟的训练框架，但两者之间那一层，也就是"成千上万个有状态、互不相同、随时可能被抢占的沙箱怎样以接近零的空闲成本存在"，在 DSec 之前几乎没有一手的系统披露（见第 3、24 章）。

还要补上 DSec 分类里没有单列的第三种场景：**评测**。评测曾被当作训练的附属品，任务集固定、批量有限、跑完就拆。2026 年它却成了事故最集中的地方：OpenAI 的 ExploitGym 评测中，内部模型 IM1 借评测集群的包代理实现出站，最终入侵 Hugging Face（OpenAI 复盘，2026-08-26；一手文档；附录 B C-10）；Anthropic 的一手事故页称，评测提示告诉 Claude 环境没有互联网，但"由于我们与评测伙伴之间的误解，情况并非如此，互联网访问是可用的"（Anthropic 事故页，2026-07-30；一手文档；评测伙伴为 Irregular，附录 B B15-07；两起事件的定义位置见 2.5.3 节，细节见第 12、20 章）。这两起事件把评测从"小事"变成了与训练、产品并列的第三种场景（见第 20 章）。

## 1.2　三场景八维度对照

表 1-1 按八个维度比较三种场景，最后一行列出典型系统。每格给出代表性事实与出处；没有任何一手或二手来源的格，写"未披露"。表中只选每格最有代表性的一两个数字，完整数据在所注章节。

**表 1-1　三场景 × 八维度对照**

| 维度 | 训练（RL rollout） | 评测 | 产品推理 |
|---|---|---|---|
| **突发性** | 单个作业最多请求 32K 个沙箱（DSec §1、§4.1）；创建能力超过每秒 5,000 个，日均约 35 个/秒（DSec §2.4；论文自述；日均为笔者推算）。K3：数万个沙箱"可能需要在数秒内创建"（K3 §5.3.2；论文自述）。见第 3、9 章 | "一批几百个 trial"，无吞吐数字（OpenSandbox 社区用例；厂商自报，未核实）；OSWorld-Verified 在 AWS 上最多 50 个环境并发（XLANG 博客；一手文档）。见第 20 章 | Lovable 在 48 小时促销周末期间峰值约 2 万个并发沙箱（Modal 资源页，2026-07；二手报道，竞品转述）。会话到达分布未披露。见第 21 章 |
| **CPU 稀疏度** | 约 90% 的沙箱平均 CPU 用量不超过请求量的 5%（DSec §4.3；论文自述）；等待模型推理最多占沙箱寿命的 98%（K3 §5.3.2；论文自述，上界）。见第 3、13 章 | 未披露。最接近的是单任务受控测量（非评测平台数据）：AgentCgroup 在 144 个 SWE-rebench 任务上测得平均 CPU 利用率 13.2%（Haiku 4.5）与 7.6%（GLM-4.7-Flash）（arXiv v3；论文自述）。见第 3 章 | 未披露（会话内活跃与空闲比例无任何产品公开；第 3 章 3.8.2 节） |
| **状态与寿命** | 容器中位寿命 17.4 分钟、microVM 15.5 分钟，p99 均超过 3 小时（DSec §4.3；论文自述）；部分 rollout 跨迭代恢复（K3 §4.1.2；论文自述）。见第 3、11、17 章 | 单任务一次性：OSWorld 2.0 上 Claude Opus 4.7 单任务平均 318.4 步（单动作设置；论文自述，预印本），步数随模型而变。单个评测沙箱的寿命分布未披露。见第 7、20 章 | 跨度极大：Copilot 云 agent 单会话上限 59 分钟（GitHub 文档）；Codex cloud 容器缓存最长 12 小时（OpenAI 文档）；Manus 闲置超过 7 天（Free）或 21 天（Pro）后回收（Manus 博客，2026-01-14）（均为一手文档）。见第 21 章 |
| **镜像多样性与复用** | 一周内 11,266 个容器基础镜像、活跃制品超过 130 TB；容器扇出中位数 3、microVM 中位数 1；运行时只读 4.2%–13.3%（DSec 表 2、表 3、§4.4；论文自述）。见第 10 章 | 任务集固定、镜像随任务版本化；规模数字未见统一披露。WAA 用 30 GB 的 Windows golden image（一手文档）。见第 20 章 | 未披露。多用少数通用模板、扇出可能远高于训练侧（推断，第 3 章）。见第 16、21 章 |
| **隔离档位** | 按任务选档：DSec 四档后端（FnCall、容器、Firecracker microVM、QEMU 完整 VM），生产以容器与 microVM 为主、比例未披露（DSec；论文自述）；AgentENV 统一 microVM（K3 §5.3.2；论文自述）。见第 5、6、24、25 章 | 事故前 OpenAI Research CaaS 为"每次运行一个容器"，事故后高风险负载改为 VM 沙箱与两层网络隔离（OpenAI 事故技术报告；一手文档）；UK AISI 建议默认把普通 Docker 隔离视为不足（SandboxEscapeBench；论文自述）。见第 5、20 章 | 多租户云端趋同于 microVM 或 gVisor；本地 CLI 用 Seatbelt、bubblewrap 等 OS 原生原语（各家一手文档）。Kimi 四项 Agent 产品运行在阿里云 ACS MicroVM 上（阿里云博客，2026-03-12；厂商自报）。见第 4、6、21 章 |
| **对手** | 作为对手的模型：DSec §6.4 记录扫端口、借 Go 代理取回代码、碰平台控制 socket 等行为（论文自述）；Anthropic 冻结期标记了超过 10% 的生产 RL 环境（一手文档，2026-08-31）。见第 19、24 章 | 作为对手的模型，且评测期会"取回答案"：Cursor 审计 SWE-bench Pro 上 Opus 4.8 Max 的成功解，63% 为取回（Cursor 博文，2026-06-25；一手文档）；ExploitGym、Anthropic/Irregular 事件出口都在评测基础设施。见第 19、20 章 | 被利用的代理人：提示注入借 Agent 的合法权限行事；本书检索范围内没有主流产品公开确认面向用户的沙箱发生 VM 级或内核级逃逸（第 21 章）。见第 2、14、21 章 |
| **成本模型** | 自建集群，空闲成本表现为节点数：DSec 单个规模单元近 160 个 CPU 节点、3 万核、约 250 TB DRAM（DSec §2.4；论文自述）。见第 13 章 | 大头是 token：WAA 一轮 VM 费用约 8 美元，模型费用 15–100 美元（WAA 仓库；一手文档）；OSWorld 2.0 前沿模型单任务约 25–72 美元（论文自述）。见第 20 章 | 按秒计费，空闲成本表现为账单：阿里云 ACS 中国内地标价每 vCPU 每小时 0.078 元、每 GiB 每小时 0.039 元（ACS 文档，2026-06-22；一手文档）。见第 13、22 章 |
| **关键时延** | 创建吞吐与环境可靠性：发生环境超时的迭代中，env.reset 消耗 rollout 时间的 78%（RollArt §3.1；论文自述，OSDI'26）；研究上"要优化吞吐"（OpenAI 演讲，AI Engineer 官方转录）。见第 3、9、17 章 | 墙钟时间与失败重跑：WAA 在 Azure 上用 40 台 VM 并行，一轮全量约 30–35 分钟（WAA 仓库；一手文档）；OSWorld-Verified 并行化后称评测时间缩短到"数分钟"（一手文档，原文无具体数）。见第 20 章 | 冷启动与交互时延：E2B 约 150 ms（厂商与第三方对比的常见口径，非独立测试）；"30 步的 Agent 运行不能从 60 秒冷启动开始"（Genspark，E2B 客户案例；厂商自报）；产品上"时延非常重要"（OpenAI 演讲，AI Engineer 官方转录）。见第 6、22 章 |
| **典型系统** | DSec、AgentENV（Kimi K3）、Cursor Anyrun、RollArt、ProRL Agent | SandboxEscapeBench / Inspect、Harbor、OSWorld、WAA、OpenAI Research CaaS | claude.ai、ChatGPT 代码解释器、Codex cloud、Manus、E2B、阿里云 ACS、腾讯 AGS |

注：①"未披露"均为结论，不以推测填格；"（推断）"为笔者推论。②阿里云博客另称 Kimi 场景峰值"每分钟数万个沙箱"，但把它与产品上线和"模型后训练阶段"写在同一节，未说明属于哪一侧，本表不把它归入任何一列（附录 B B21-19、B26-15）。③各格数字的完整口径与其他来源见所注章节与本章数字溯源表；"一批几百个 trial"在第 3 章核对中未能回原文核实。

读这张表之前要注意，同一行里的数字口径并不相同。"突发性"一行，DSec 的 32K 是单个作业的请求上限，Lovable 的 2 万是特定促销活动期间的峰值并发，OSWorld-Verified 的 50 是评测框架的并发上限；"状态与寿命"一行，DSec 给的是中位数与 p99，产品侧给的全是策略上限。它们只能用来比较量级与方向，不能横向排名（见 3.1.2 节、3.8.2 节）。

从这张表可以先读出三点。

**第一，训练与产品在多数维度上方向相反。** 训练要的是突发下的创建吞吐，产品要的是单次交互的时延；训练的镜像几乎每个沙箱都不一样，产品多用少数模板（后者为推断）；训练的空闲成本由实验室自己吞掉，表现为节点数，产品的空闲成本出现在客户账单上，在"按活跃 CPU 计费"之后又部分转给了厂商（推断，见第 13、22 章）。OpenAI 一位工程师在演讲中的说法是："研究上我们要优化吞吐……要跑大量 rollout……产品上时延非常重要"（on research, we want to optimize for throughput. We want to run many, many training loops at scale, uh, and have many, many rollouts… In product, latency is very important.）（AI Engineer 官方转录；Weldon 笔记中的"亚秒级"为其转述，转录中没有）。

**第二，评测不是"小号的训练"。** 它的批量接近产品，状态接近一次性容器，对手却和训练一样是模型本身，而且评测中的模型往往是能力最强、还没有发布的那个。2026 年最严重的事故都出在评测环境里（见第 20 章）。评测还有一个其他两种场景都没有的特性：隔离设置本身会改变测量结果。Cursor 的对照实验显示，只改 harness 的隔离设置，同一基准上不同模型的分数变化可相差二十倍以上（Cursor 博文；一手文档；倍数为笔者推算，见第 19、20 章）。所以本书把隔离级别视为评测规格的一部分（本书建议，见第 20 章）。

**第三，空白集中在产品侧和评测侧。** 训练侧至少有 DSec 一份按"生产周 × 沙箱实例"口径的完整刻画；产品侧公开的几乎全是策略上限与总量，评测侧连这些也很少（见 3.8 节）。表中的"未披露"不是本书没查到，而是在本书检索范围内没有任何当事方公开。

## 1.3　为什么训练负载不是 serverless

### 1.3.1　DSec 的划界

从表面看，Agent 沙箱与 serverless 函数很像：都是短时间内拉起大量隔离实例，都在意冷启动，都希望空闲时不付钱。十年来 serverless 社区积累了一整套答案：快照恢复、模板 fork、按需加载、P2P 分发、预热池。DSec 在相关工作中明确划了一条界线：这些系统面向短命、无状态的函数，"这类负载通常以高扇出复用一组有限的镜像，许多系统假定所需镜像已在本地"；而 Agent 训练"使用的是长寿命、有状态的沙箱，它们取自一个超出单节点存储、每个镜像扇出很低的镜像库"（Agentic training instead uses long-lived, stateful sandboxes drawn from an image corpus that exceeds single-node storage and has low per-image fanout.）（DSec §9；论文自述）。

被划在界线另一侧的名单里有 TrEnv，而 DSec 第一作者 Jialiang Huang 正是 TrEnv 的作者之一。这条连线以及它与 AgentENV 的关系，本书在第 25 章专门讨论；凡涉及 TrEnv → AgentENV → DSec 的传承，一律是笔者的推断（推断，基于作者重合）。可以确定的事实只有一句：DSec 的 microVM 存储路径使用了 AgentENV 仓库中开源的 Rust OverlayBD/ublk 组件（论文称"我们参与贡献"）（DSec §7；论文自述）。

### 1.3.2　三个特征同时出现

单看任何一项特征，serverless 都有现成答案（见第 10 章）。问题在于三项同时出现。表 1-2 把 serverless 的经典假设与 Agent 训练的实测放在一起。

**表 1-2　serverless 假设与 Agent 训练负载对照**

| 维度 | serverless 的经典假设 | Agent 训练的实测（出处；类型） | 后果与展开章节 |
|---|---|---|---|
| 镜像复用 | 少量镜像、高扇出，镜像多半已在本地 | 一周 11,266 个容器基础镜像加 102,171 个 workspace；容器扇出中位数 3、p90 为 28（DSec 表 2、§4.4；论文自述）；K3 训练与评测共在 1,505,678 个镜像上创建 51,219,741 个沙箱（K3 §5.3.2；论文自述） | 本地缓存与 P2P 收益有限；按需加载与可组合层成为主路径（第 10 章） |
| 数据量 | 镜像可整体预拉取 | 一周活跃制品超过 130 TB，平台管理 PB 量级的层与镜像；运行时只读 4.2%–13.3%（DSec §2.4、§4.4、表 3；论文自述） | 整体预拉取把大部分 I/O 花在不会被读的数据上（第 10 章） |
| 到达模式 | 请求连续到达，可按均值扩容 | 单个作业最多 32K 个沙箱；峰值创建能力与日均速率相差两个数量级以上（DSec；论文自述；倍数为笔者推算） | 控制面按峰值设计，创建关键路径上不能有一致性写（第 9 章） |
| 状态与寿命 | 短命、无状态，用完即焚 | 寿命 p99 超过 3 小时；文件修改、依赖与服务在多次调用间保留（DSec §2.3、§4.3；论文自述） | 暂停而非销毁；检查点要增量、反复、藏在等待时间里（第 11 章） |
| 资源形态 | 执行期间 CPU 繁忙 | 约 90% 沙箱 CPU 用量不超过请求的 5%（DSec §4.3；论文自述）；单任务受控测量中内存峰均比最高 15.4 倍（AgentCgroup，单任务极值；论文自述） | 瓶颈从 CPU 转到内存（第 13 章） |
| 中断 | 函数短到不必考虑抢占 | GPU 训练作业会在 rollout 中途被抢占（DSec §1；论文自述） | rollout 状态要放在可抢占 GPU 池之外（第 17 章） |
| 租户 | 租户是外部用户，代码通常无意攻击平台 | "Agent 执行不可信"（DSec §1；论文自述）；早期容器沙箱中观察到"由 Agent 的非预期操作引起的内核崩溃和死锁"（K3 §5.3.2；论文自述） | 隔离档位与完整性是训练平台的一部分（第 5、19 章） |

注：DSec 原文列出七项负载特征（突发、高密度、有状态长寿命、异构、环境多样、执行不可信、可中断）；本书取突发、稀疏、有状态、低扇出、可中断五项作为全书负载框架（见第 3 章）。K3 的"每镜像约 34 个沙箱"为累计均值，不能与 DSec 一周切片的中位数 3 直接比较（附录 B B25-06）。

三项特征叠加的效果是，serverless 的每一个答案都要重新加权。按需加载依然成立，而且更必要；P2P 与共享缓存从主路径退为加速手段；预热池在低扇出下难以维持，因为不知道该预热哪个镜像（见第 9、10 章）；快照从"一次快照、多次恢复"的冷启动优化，变成了"高频、增量、在关键路径旁边"的暂停机制（见第 11 章）；可写层从可以忽略的东西变成需要设计的对象（见第 10 章）。

这一判断还解释了为什么"空闲"是 Agent 沙箱的核心经济问题。如果寿命的绝大部分时间都在等模型，而状态又不能丢，那么平台的难点就不在"隔离得多强"，而在"如何让几十万个有状态、互不相同、随时可能被抢占的环境以接近零的空闲成本存在"。这是全书的第一个基本判断，第 3 章用负载数据论证它，第 10、11、13 章分别从存储、状态、密度三个方向回答它。

### 1.3.3　评测与产品更像 serverless 吗

不完全是。评测的任务集固定、可以提前构建镜像，在镜像复用上比训练更接近 serverless；但 OSWorld 2.0 上前沿模型单任务要走数百步（Claude Opus 4.7 平均 318.4 步），单个任务的状态并不短命（见表 1-1）。产品侧的一次性短命容器（第 21 章的范式一）最接近 serverless，而 Manus 一类有状态长期 VM（范式三）寿命以天计甚至常驻，闲置一到三周才回收（Manus 博客；见 21.1 节）。可见，"不是 serverless"在三种场景里成立的理由不同：训练是三项特征叠加，评测主要是状态寿命，产品的范式三主要是跨会话状态（推断，基于表 1-1）。

## 1.4　为什么接口能共用而后端不能

### 1.4.1　接口在收敛

2026 年沙箱的接口层出现了明显的收敛。E2B 的沙箱生命周期 HTTP API 与 SDK 约定（本书称"E2B 协议"，事实标准，非正式标准）被训练系统迅速采纳：kvcache-ai 组织（清华 MADSys 牵头）在 2026 年 7 月 25 日开源、用于 Kimi K3 训练的 AgentENV 提供 E2B 兼容 API，从 E2B 迁移只需改一个环境变量（AgentENV README；一手文档；附录 B C-19、B16-08）；腾讯 CubeSandbox、腾讯云 AGS、阿里云 ACS 也宣称兼容（见第 16 章表 16-1）。OpenAI Agents SDK 内置了 7 家可互换的沙箱 provider（OpenAI，2026-04-15；一手文档）。

协议本身也在向训练需求靠拢。2026 年 7 月 15 日，E2B 把 `POST /sandboxes/{sandboxID}/fork` 写入控制面规范，`count` 取值 1–100，7 月 21 日在 changelog 公告（e2b-dev/infra 提交 643d726；E2B changelog；一手文档）。AgentENV 7 月 25 日首次公开时已带路径相同、上限同为 100 的 fork 接口；它的首版文档误写为 16 个，2026 年 8 月 24 日更正，上限本身从未改变（附录 B C-02、X-31）。"E2B 不支持 fork"的旧说法已经过时（附录 B B16-12）。

不过，"兼容"的证据几乎都是实现者自述，兼容的深度也分 SDK、控制面、guest 内 envd 三层；兼容者处于跟随位置，E2B 每加一个字段，"兼容"的含义就变一次（见 16.2 节）。

### 1.4.2　底座相同

后端技术也有趋同之处。OpenAI 一位 RL 与 Agent 基础设施组工程师在 AI Engineer World's Fair 2026 上的演讲 *From fork() to Fleet*，据 AI Engineer 官网发布的转录（并对照 ZenML 摘要与 Weldon 笔记），描述了一条从进程 fork、到容器、到 gVisor、再到硬件虚拟化的演进路径。ZenML 摘要的记录是：最简单的做法是"为每次工具调用 fork 一个进程来执行请求的代码"；容器靠命名空间与 cgroups 两个 Linux 原语；gVisor 在用户空间重新实现了 Linux 内核的大部分；硬件虚拟化"借助 CPU 级抽象提供最强的安全边界"（ZenML 摘要；二手报道）。Weldon 的笔记把这条路径概括为"由越来越复杂的威胁模型驱动的演进"（Weldon 笔记；二手报道）。图 1-2 按这条路径绘制。

```mermaid
flowchart TB
    subgraph PATH["演进路径"]
        direction LR
        F["进程 fork/exec<br/>每次工具调用一个进程<br/>边界：宿主 OS 权限"] --> C["容器<br/>命名空间 + cgroups<br/>边界：共享宿主内核"]
        C --> G["gVisor<br/>用户态内核 Sentry<br/>边界：截获系统调用"]
        G --> V["硬件虚拟化 / microVM<br/>Rust VMM（crosvm、<br/>Firecracker、Cloud Hypervisor）<br/>边界：独立 guest 内核"]
    end
    subgraph NOW["2026 年仍在用"]
        direction LR
        F1["fork/exec 一档<br/>本地 CLI 的 OS 原生原语<br/>（第 4 章）<br/>DSec FnCall（第 8 章）"]
        C1["容器一档<br/>DSec 容器档（第 5 章）<br/>NVIDIA 每 rollout 一个<br/>Apptainer 容器（第 27 章）"]
        G1["gVisor 一档<br/>INTELLECT-3 训练沙箱<br/>（第 27 章）"]
        V1["microVM 一档<br/>E2B、AgentENV、Cursor、<br/>DSec microVM 档（第 6 章）"]
        F1 ~~~ C1 ~~~ G1 ~~~ V1
    end
    PATH -.-> NOW
```

**图 1-2　沙箱形态演进：fork-exec → 容器 → gVisor → microVM**（示意图。上排演进路径依据 OpenAI 工程师演讲的 ZenML 摘要与 Weldon 笔记绘制，**二手报道**，本书未能观看原视频，已用 AI Engineer 官方转录核对；下排"2026 年仍在用"的例子依据第 4–8、27 章的一手材料，是笔者的归纳）

这张图要和下排一起读。演进路径描述的是"边界越来越硬"，不是"后者取代前者"：到 2026 年四种形态全部在生产中并存，DSec 一个平台就同时提供 FnCall、容器、microVM 和完整 VM 四档，按任务选择（见第 24 章）。训练侧的隔离选择也在分化：与产品共用平台的（Cursor、Cognition）用 VM 或 microVM；以 HPC 或研究集群为底座、已披露的多用容器（推断，见 27.9.3 节）。OpenAI 的讲者同时负责 RL 与 ChatGPT、Codex Web 的不可信代码执行基础设施，他建议"从一开始就用 microVM"，但没有说 OpenAI 自己用的是什么（AI Engineer 官方转录）。ZenML 称"讲者的团队使用 Cloud Hypervisor"，官方转录中没有这句话，演讲只是以 Cloud Hypervisor 为例讲参考设计（附录 B X-44）。

### 1.4.3　后端为什么分开

接口相同、VMM 相同，为什么后端还是不能共用？下面三个例子从不同侧面说明这个问题。

**Cursor：同一平台，重写调度器。** Cursor 说，训练 Composer 的工作"复用了为 Background Agents 构建的基础设施"，"实现了 RL 环境与生产环境的无缝统一"；但为此要"重写虚拟机调度器，以支持训练运行的突发性与规模"（rewriting our virtual machine scheduler to support the bursty nature and scale of training runs）（Cursor Composer 博文；一手文档）。底座和接口共用，调度层却必须按训练负载重做。

**DSec：自有 SDK。** 迄今公开得最完整的训练沙箱没有走 E2B 协议。DSec 的 libdsec 在创建请求里按沙箱声明后端、资源、空闲 TTL 与语义级网络规则（如"镜像服务""包管理器"），并按任务阶段切换（DSec §2.1、§6.3、§6.5；论文自述；见 16.2.4 节）。这些字段都是 E2B 协议没有的。

**月之暗面：同一家公司，两套后端。** 第三个例子来自同一家公司的两侧。训练侧，K3 报告写道："我们使用多种沙箱运行时来满足 Kimi K3 后训练与评测的多样化需求，包括传统的基于容器的运行时、GPU 沙箱运行时，以及……一个名为 AgentENV 的基于 microVM 的新沙箱运行时"（K3 §5.3.2；论文自述；见 25.1.1 节）。产品侧，阿里云的客户案例称 Kimi 的 Deep Research、Agentic PPT、OK Computer 与数据分析四项产品运行在 ACS 的 MicroVM 上，每个请求分配一个，休眠时保留内存、临时存储与 IP（阿里云博客，2026-03-12；厂商自报；见 21.6.2 节）。AgentENV 与 ACS 都宣称兼容 E2B 协议（见表 16-1），两侧在接口上很可能可以互通，后端却分属与合作方共同开发的开源平台和公有云服务（推断）。阿里云博客在同一节还提到模型后训练阶段，但没有说明训练侧用了 ACS 的哪一部分（附录 B B21-19）。

把这些例子放到八层架构里（见第 9 章），分歧落在哪几层就清楚了。表 1-3 逐层对照。

**表 1-3　接口与底座可以共用，后端在哪几层分开**

| 层 | 训练侧的要求 | 产品侧的要求 | 能否共用 | 展开章节 |
|---|---|---|---|---|
| ① 接入与 API | 生命周期操作 + 后端声明、阶段化网络策略、作业级暂停、fork 语义 | 生命周期操作、文件、命令、PTY | 生命周期部分可以共用（E2B 协议）；训练需要的七个概念现有协议都不完整 | 第 16 章 |
| ② 控制面 | 按峰值设计创建吞吐（DSec 超过每秒 5,000 个）；预热难以针对低扇出镜像 | 预热池换单次时延；按用户配额 | 难：Cursor 为此重写了调度器 | 第 9 章 |
| ③ 节点运行时 | 按任务选档；租户是模型 | 多租户趋同于 microVM/gVisor | 可以：VMM 与隔离原语相同 | 第 4–8 章 |
| ④ 镜像与存储 | 库大、扇出低、读得少、来得猛 | 少数模板、高扇出（推断） | 难：缓存与分发假设相反 | 第 10 章 |
| ⑤ 状态管理 | 抢占时按作业批量暂停；GRPO 分组与树搜索要 fork | 会话休眠与唤醒；按用户保留 | 部分：机制相同，触发者与粒度不同 | 第 11、12 章 |
| ⑥ 密度与资源 | 空闲成本是实验室的节点数 | 空闲成本是客户的账单 | 部分：技术相同，风险承担方不同 | 第 13 章 |
| ⑦ 网络与出站 | 策略属于任务定义，按阶段切换；包通路要只读预填充 | 策略由用户或平台定义；凭据位置决定风险 | 部分：执行机制相同，策略主体不同 | 第 14、15 章 |
| ⑧ RL 集成与完整性 | rollout 状态必须活得比 GPU 作业久；harness 要自我保护 | 不需要 | 不能：这是训练沙箱与产品沙箱的分水岭 | 第 17、19 章 |

注：本表为本书归纳。"训练需要的七个概念"指语义级网络策略、阶段切换、作业级暂停、完整性约束、fork 语义、资源与后端声明、与 rollout 关联的可观测性（见 16.6 节表 16-2）。

最后一行是关键。产品沙箱不需要回答"GPU 作业被抢占时 rollout 状态归谁"；训练沙箱不回答这个问题，就会在每次抢占时丢掉 Agent 循环。DSec 自 V4.1 起让 agent sandbox 与 worker container 在可抢占 GPU 池之外共同作为 rollout 状态的唯一事实来源，抢占时由 RL 框架主动暂停相关沙箱（DSec §6.2、§6.3；论文自述；见 17.1 节、24.3.8 节）。第 9 章据此把第⑧层称为训练沙箱与产品沙箱的分水岭，把第④、⑤层称为差异化所在。

## 1.5　全书地图

### 1.5.1　三条主线加一条第二主线

全书沿四条线组织（图 1-1）。

**三场景。** 训练 rollout、评测、产品推理，按表 1-1 的八个维度比较。第 17–19 章写训练，第 20 章写评测，第 21 章写产品，第 22 章写它们背后的产业；此后各章凡给出设计建议，都分场景说明。

**八层架构。** ① 接入与 API、② 控制面、③ 节点运行时、④ 镜像与存储、⑤ 状态管理、⑥ 密度与资源、⑦ 网络与出站、⑧ RL 集成与完整性（第 9 章）。①见第 16 章，③见第 4–8 章，④–⑦见第 10–15 章，⑧见第 17–19 章；第 24–27 章用同一套层次拆解案例。这八层是本书对 DSec 与 AgentENV 两份一手披露逐项对齐后归纳出来的，DSec 论文本身没有这种编号（见第 9 章）。

**两类对手。** 一是**被利用的代理人**：外部攻击者借 Agent 的合法权限行事，核心概念是混淆代理人（confused deputy）、致命三要素（lethal trifecta）和提示注入。二是**作为对手的模型**：沙箱里的租户本身为达成目标而越界，包括 reward hacking（奖励投机，指模型以非预期途径拿到奖励）、环境篡改和逃逸，CSA 称之为"具备内部人能力的对手"（附录 A）。第 2 章给出定义；产品侧主要面对前者（第 21 章），训练与评测主要面对后者（第 19、20 章），出站与包代理两者都要面对（第 14、15 章）。

**第二主线：状态。** 状态是与"对手"并列的线索，分三层：沙箱内状态的快照与 fork（第 11 章）、沙箱外副作用的事务化与回滚语义（第 12 章）、状态与出站的对偶（第 14、15 章）。它贯穿 GUI 环境（第 7 章）、密度（第 13 章，暂停即省钱）、RL 集成（第 17 章，rollout 状态从 GPU 作业剥离）和产品（第 21 章，休眠 VM 与 fork）。全书的第二个基本判断就在这条线上：**沙箱内的状态可以回滚，沙箱外的副作用必须事务化或者禁止，两者之间的出站通道要按"只读、预填充、不能代取任意 URL"来设计。**

### 1.5.2　证据标注约定

本书讨论的大部分系统是 2026 年才公开的，材料以预印本、厂商文档和事故复盘为主，口径混乱、互相矛盾的数字很多。为此全书使用一套固定的标注（详见第 24 章开头的体例说明与附录 B）：

- **来源类型。** 每个数字首次出现时在括注中写明出处与类型：论文自述、一手文档、厂商自报、二手报道、二手引述、笔者推算。"笔者推算"写明算式。所有数字登记在各章末的"本章数字溯源"表，并与附录 B 编号对应。
- **发表状态。** 2026 年的系统论文标"预印本""投稿"或会议名（如 RollArt 为 OSDI'26）。
- **冲突并列。** 来源互相矛盾时并列各方并注日期，不二选一，按附录 B"冲突数字登记"的建议措辞引用。例如 AgentENV 的内存超售比，K3 报告称最高 6.5 倍，项目 README（2026-08-10）称生产中 9.6 倍，两者归因的机制也不同（附录 B C-01）。
- **不应引用。** 附录 B 列出过时、误读或仅凭记忆的说法，正文只在纠正时提及。例如 K2.5 的"10 万个并发沙箱"（应为任务，X-09）、AgentENV"fork 上限 16 个"（X-31）。
- **"未披露"是结论。** 披露矩阵（第 26、27 章）中，一格要么写"事实 + 出处"，要么写"未披露（已查：……）"，不许用推测填格。
- **推断。** 笔者由已引事实推出的结论标"（推断）"。TrEnv → AgentENV → DSec 的谱系每次出现都注"（推断，基于作者重合）"；DSec 与 AgentENV 的关系只用固定句式："DSec 的 microVM 存储路径使用了 AgentENV 仓库中开源的 Rust OverlayBD/ublk 组件（论文称'我们参与贡献'）"，不写"基于 AgentENV"。
- **本书建议。** 作者给出的设计建议、草案和测量协议一律标"本书建议"，它们不是任何现行标准。
- **常见更正。** 几条在早期材料中反复出现的说法，全书统一按附录 B 更正：DSec 论文署名作者 131 人（C-03a）；E2B 自 2026 年 7 月起支持 fork（B16-12）；Kimi 产品运行在阿里云 ACS 上，阿里云所称"每分钟数万个沙箱"不归属训练或产品任何一侧（B21-19）；Anthropic 2026 年 7 月 30 日披露的事件起因是与评测伙伴 Irregular 之间的误解（B15-07）；SandboxEscapeBench 在 v3 的 1 亿 token 预算下已被 Mythos Preview 饱和（B20-22）。

### 1.5.3　全书的主要判断

以下按部分列出全书的核心结论，各附章号。它们是各章经独立核对后的结论摘要，论证与限定条件在对应章节。

**第一部分　定义与问题**

- 三种场景在多数维度上方向相反，但落在同一类底座上；接口可以共用，第②、④层后端难以共用，第⑧层不能共用（本章）。
- 沙箱要防两类对手：防"被利用的代理人"，语义层能力控制更有效；防"作为对手的模型"，隔离强度与基础设施配置的正确性才是关键（第 2 章；凭据位置的作用见第 21 章）。
- Agent 负载的五个核心特征是突发、稀疏、有状态、低扇出、可中断；"空闲"有配额、时间、单任务时延几种口径，98%、90%、55%–60% 并不矛盾；产品侧与 GUI 负载几乎没有刻画（第 3 章）。

**第二部分　隔离原语**

- 2025–2026 年本地沙箱的失效几乎都发生在原语周围的"策略管道"上，而不是原语被攻破（第 4 章）。
- 训练集群是"单租户、但租户不可信"：DSec 把 SWE 与工具调用任务放在容器里，是信任模型、密度与兼容性三者权衡的结果，其有效性会随模型能力变化（第 5 章）。
- microVM 已是多租户 Agent 沙箱的默认选项，但所有启动与密度数字都是厂商自报或二手转述，没有独立的横向基准（第 6 章）。
- GUI 环境的瓶颈已从"起一台 VM"转到"廉价地复制与回滚 GUI 状态"（第 7 章）。
- TEE 防运营方不防模型；语义层防御是"工具调用层的沙箱"，与 OS 层沙箱叠加使用，不能互相替代（第 8 章）。

**第三部分　八层架构**

- 差异化在第④、⑤层，分水岭在第⑧层，公开资料的空白在第②层；控制面的关键不在"用不用 K8s"，而在创建关键路径上有没有一致性写（推断）（第 9 章）。
- Agent RL 的镜像负载是"库大、扇出低、读得少、来得猛"，可组合层与按需加载解决的是不同瓶颈（第 10 章）。
- 检查点从"一次快照、多次恢复"变成"反复、增量、藏在等待时间里"；模板 fork 的唯一性、抢占风暴下的存储带宽缺少公开工程数据（第 11 章）。
- 快照止于沙箱边界；外部副作用的事务化在工业界还没有一手实践记录（第 12 章）。
- 密度的瓶颈是内存而不是 CPU；空闲的成本在训练侧是节点数，在产品侧是账单（第 13 章）。
- 默认拒绝加白名单只回答了"连哪里"；凭据位置决定被注入后的损失（第 14 章）。
- 包代理不是缓存，而是一条出站通道，有时还是写信道、提权跳板和信任根；本书建议把包通路从网络层搬到存储层（第 15 章）。
- 生命周期层向 E2B 协议收敛，环境语义层向 Gym 式接口加 MCP 收敛，两层都缺少训练场景必需的七个概念（第 16 章）。

**第四部分　沙箱与 Agent RL**

- rollout 进行到一半时状态归谁，是训练沙箱必须回答的问题；明确回答了的公开系统只有 DSec 与 ProRL Agent（第 17 章）。
- 环境构建正在被 Agent 自动化，构建流水线是 reward hacking 的上游攻击面，构建期卫生应写进 RL 任务定义（第 18 章）。
- 被训练的模型是训练集群里最有动机的攻击者，它瞄准的往往是答案可达的通道（.git 历史、上游网络、包代理、harness 内部），而不是内核；生产对策几乎都没有量化效果（第 19 章）。
- 评测环境本身是安全边界的一部分，隔离级别本身是评测规格的一部分；"离线"必须验证，不能声明（第 20 章）。

**第五部分　产品与产业**

- 产品沙箱分三种范式；决定用户风险的不是隔离档位，而是凭据放在哪里；本书检索范围内没有主流产品公开确认面向用户的沙箱发生 VM 级或内核级逃逸（第 21 章）。
- 沙箱正在被平台吸收为标准组件，RL 环境正在变成有价格的商品；没有可信的市场规模数字，也没有独立基准（第 22 章）。
- 沙箱与隔离已写入非强制的实践指南和实验室治理框架，但（在本书检索范围内）尚未进入任何强制性标准或法规；现有规范几乎都只针对"被利用的代理人"，没有覆盖训练与评测中"作为对手的模型"（第 23 章）。

**第六部分　案例研究**

- DSec 是一个以密度为中心、按任务选档的弹性执行平台；负载特征几乎一一对应到八层中的机制（第 24 章）。
- AgentENV 以暂停为中心、统一 microVM，机制最透明，生产使用却比 DSec 更不透明；TrEnv → AgentENV → DSec 的谱系是推断（推断，基于作者重合）（第 25 章）。
- 国内模型公司公开训练侧，产品沙箱信息只经云厂商客户案例间接可见；百度、讯飞、商汤、零一万物的训练侧接近空白（第 26 章）。
- 美国闭源前沿实验室公开产品沙箱与事故复盘，训练环境几乎不透明；公开的训练侧技术记录主要来自 Meta、NVIDIA、开源社区与 Cursor、Cognition 这类自训模型的应用公司（第 27 章）。

**第七部分　前沿**

- 上述各章列出的"未披露"与开放问题，汇总为一份工程问题清单与研究议程（第 28 章）。

### 1.5.4　读者路线图

本书面向三类读者。表 1-4 给出建议的阅读路线。所有路线都建议先读本章与第 3 章，并把附录 B 作为查数字的工具。

**表 1-4　读者路线图**

| 读者 | 关心的问题 | 建议路线 | 可略读 |
|---|---|---|---|
| RL 基础设施工程师 | 怎样拉起、暂停、回收几十万个有状态沙箱；rollout 状态归谁 | 第 3 → 9 → 10 → 11 → 13 → 17 → 18 → 24 → 25 章；再读第 19 章（完整性）、第 16 章（接口） | 第 7 章（除非做 GUI）、第 22 章 |
| 评测平台与安全研究者 | 怎样让"离线"可验证；隔离设置怎样影响分数；模型能做什么 | 第 2 → 5 → 14 → 15 → 19 → 20 章；再读第 12 章（不可逆效果）、第 23 章 | 第 10、13 章 |
| Agent 产品运行时工程师 | 选什么隔离档位；凭据放在哪里；怎样计费与休眠 | 第 2 → 4 → 6 → 14 → 21 → 22 章；再读第 11 章（休眠与 fork）、第 16 章（E2B 协议） | 第 17、18 章 |
| 系统方向研究者与研究生 | 哪些问题有 serverless 先例、哪些没有；开放问题在哪里 | 第 3 → 9 → 10 → 11 → 12 → 13 章，各章"谱系"边栏；第 25、28 章 | 第 22、26、27 章的商业细节 |
| 技术管理者、投资与标准制定人员 | 格局、价格、披露、规范处于什么阶段 | 本章 → 第 2 → 22 → 23 → 26 → 27 章；附录 B | 第 4–15 章的机制细节 |

注：本表为本书建议。前置知识为 Linux 系统编程与容器基础；RL 只要求知道 rollout、reward、GRPO 这类概念（目录 v2 总纲）。

## 本章小结

- **Agent 沙箱是有状态的隔离执行实例及其配套设施**，与"环境""沙箱平台"不同。
- 它经历了三个阶段：产品功能（代码解释器）、独立服务（E2B 一类）、RL 底座（DSec、AgentENV、Cursor）。
- DSec 把已有系统分为 serverless、推理侧、训练侧与 RL 框架四类，指出没有一类覆盖 Agent 训练负载，RL 框架"把执行环境当作黑盒"。
- **三场景在八个维度上常常方向相反**：训练要突发下的创建吞吐，产品要单次交互的时延；训练镜像低扇出，产品多用模板（推断）；训练的空闲成本是节点数，产品的是账单。
- **评测不是小号的训练**：批量小、状态短，对手却是最强的模型，隔离设置还会改变分数。
- 产品侧与评测侧的负载大多未披露。
- **训练负载不是 serverless**：低镜像复用、高突发、长寿命有状态三者同时出现（DSec §9），serverless 的每个答案都要重新加权——按需加载更必要，P2P 与预热退为辅助，快照变成高频增量的暂停机制，内存成为第一约束。
- **接口与底座趋同**：E2B 协议被 AgentENV 等训练系统采纳，E2B 也在 2026 年 7 月加入了 fork；底座趋同于 microVM（OpenAI 演讲所述演进路径，据 AI Engineer 官方转录）。
- **后端仍然分开**：Cursor 要为训练重写 VM 调度器，DSec 用自有 SDK 声明后端、TTL 与阶段化网络规则，分歧集中在控制面、存储与 RL 集成。
- 第⑧层的 rollout 状态归属是训练沙箱与产品沙箱的分水岭。
- **全书地图**是三场景 × 八层 × 两类对手，加上"状态"这条第二主线。
- 证据按来源类型标注，冲突并列，"未披露"作为结论写出，推断与本书建议单独标明。
- 标准方面，沙箱与隔离已写入非强制的实践指南和实验室治理框架，但尚未进入任何强制性标准或法规（第 23 章）。

## 本章数字溯源

本表登记本章使用的数字与日期。"核对"列中，"复核"指本书写作时回一手原文核对过，"沿用"指沿用对应章节已核对的结论。

**表 1-5　本章数字溯源**

| 数字 | 含义 | 原文位置 / 来源 | 类型 | 核对 | 附录 B |
|---|---|---|---|---|---|
| 约 160 个节点；3 万核；约 250 TB DRAM | DSec 单个规模单元 | DSec §2.4 | 论文自述 | 复核 | B24-02、B24-05 |
| 约 300 万个/天；峰值约 38 万（摘要称超过 380,000）；超过 5,000 个/秒 | DSec 日服务量、峰值并发、创建速率 | DSec §2.4、摘要 | 论文自述 | 复核 | B24-03、B24-04、B24-06 |
| 约 34.7 个/秒 | DSec 日均创建速率（3,000,000 ÷ 86,400） | 由上行推算 | 笔者推算 | — | B24-14 |
| 最多 32K 个 | 单个作业请求的沙箱数 | DSec §1、§4.1 | 论文自述 | 沿用 | B03-01 |
| 约 90%；5% | CPU 用量不超过请求 5% 的沙箱比例 | DSec §4.3 | 论文自述 | 沿用 | B03-03 |
| 17.4 分钟；15.5 分钟；p99 超过 3 小时 | 容器与 microVM 中位寿命 | DSec §4.3 | 论文自述 | 沿用 | B03-04 |
| 11,266 个；102,171 个 | 一周容器基础镜像与 workspace 数 | DSec 表 2 | 论文自述 | 沿用 | B03-05 |
| 超过 130 TB；PB 量级 | 一周活跃制品；平台管理的层与镜像 | DSec §4.4、§2.4 | 论文自述 | 沿用 | B03-07、B24-13 |
| 中位数 3、p90 28；中位数 1 | 容器与 microVM 镜像扇出 | DSec §4.4 | 论文自述 | 沿用 | B03-08 |
| 4.2%–13.3% | 运行时实际访问比例 | DSec 表 3 | 论文自述 | 沿用 | B03-09；X-06 |
| 131 人 | DSec 论文署名作者 | DSec 作者块 | 论文自述 | 沿用 | B24-09；C-03a |
| 最多 98% | 等待模型推理占沙箱寿命 | K3 §5.3.2 | 论文自述 | 沿用 | B03-10 |
| 51,219,741 个；1,505,678 个 | K3 训练与评测创建的沙箱数与镜像数 | K3 §5.3.2 | 论文自述 | 沿用 | B25-05、B25-06；X-34 |
| 2026-07-27；2026-08-07 | K3 报告 v1、v2 日期 | arXiv 摘要页 | 一手文档 | 复核 | B01-07 |
| 超过 10,000 个 | K2 并发沙箱实例（Kubernetes） | K2 §3.2.1 | 论文自述 | 沿用 | B26-01；C-25 |
| 最多 100,000 个 | K2.5 并发 agent 任务（非沙箱） | K2.5 技术报告 | 论文自述 | 沿用 | C-09；X-09 |
| 数十万个 | Cursor Composer 训练的并发沙箱化编码环境 | Cursor Composer 博文，2025-10-29 | 一手文档 | 复核 | B17-17 |
| 约 2 万个；48 小时 | Lovable 促销周末峰值并发沙箱 | Modal 资源页，2026-07 | 二手报道（竞品转述） | 复核 | B01-01 |
| 一批几百个 | 评测 trial 批量 | OpenSandbox 社区用例 | 厂商自报 | 未能回原文核对 | B01-02 |
| 最多 50 个 | OSWorld-Verified 在 AWS 上的并发环境 | XLANG 博客，2025-07-28 | 一手文档 | 沿用 | B20-12 |
| 13.2%；7.6%；144 个 | AgentCgroup 平均 CPU 利用率与任务数 | AgentCgroup arXiv v3 §3.3 | 论文自述 | 沿用 | 第 3 章表 3-2 |
| 318.4 步 | OSWorld 2.0 上 Claude Opus 4.7 单任务平均步数（单动作设置） | arXiv 2606.29537 | 论文自述 | 沿用 | B20-14 |
| 40 台；约 30–35 分钟；约 8 美元；15–100 美元；30 GB | WAA 在 Azure 上并行的 VM 数、一轮全量墙钟时间、VM 费用、模型费用、golden image | WAA 仓库 | 一手文档 | 沿用 | B20-15 |
| 约 25–72 美元 | OSWorld 2.0 前沿模型单任务成本 | arXiv 2606.29537 | 论文自述 | 沿用 | B20-13 |
| 59 分钟 | Copilot 云 agent 单会话上限 | GitHub 文档 | 一手文档 | 沿用 | B21-10 |
| 12 小时 | Codex cloud 容器缓存上限 | Codex cloud 文档 | 一手文档 | 沿用 | B21-09 |
| 7 天 / 21 天 | Manus 闲置回收（2026-01） | Manus 博客，2026-01-14 | 一手文档 | 沿用 | B21-01；C-04 |
| 2025 年；2025-05-06 | Manus 使用 E2B Firecracker microVM 的年份；E2B 客户案例日期 | E2B 客户案例 | 厂商自报 | 沿用 | C-05 |
| 0.078 元；0.039 元 | 阿里云 ACS 每 vCPU·小时、每 GiB·小时标价 | ACS 文档，2026-06-22 | 一手文档 | 沿用 | B22-41；C-07 |
| 每分钟数万个 | 阿里云博客所称 Kimi 场景峰值沙箱数（不归属任何一侧） | 阿里云博客，2026-03-12 | 厂商自报 | 沿用 | B21-19、B26-15 |
| 约 150 ms | E2B 冷启动（常见口径） | Morph、E2B 客户案例等 | 二手报道 / 厂商自报 | 沿用 | B22-02；C-18 |
| 60 秒；30 步 | Genspark 对冷启动的要求 | E2B 客户案例，2026-05-07 | 厂商自报 | 沿用 | B21-13 |
| 78% | 环境超时迭代中 env.reset 占 rollout 时间 | RollArt §3.1 | 论文自述 | 沿用 | B10-14 |
| 63% | Opus 4.8 Max 成功解中取回的比例 | Cursor 博文，2026-06-25 | 一手文档 | 沿用 | B19-01 |
| 二十倍以上 | 隔离设置引起的模型分数变化之比（20.7 分对不到 1 分） | Cursor 博文 | 笔者推算 | 沿用 | B19-02 |
| 超过 10% | Anthropic 冻结期被标记的生产 RL 环境比例 | Anthropic，2026-08-31 | 一手文档 | 沿用 | B27-11 |
| 2026-07-30 | Anthropic 事故页发布日期（"误解"原句出处） | Anthropic 事故页 | 一手文档 | 复核 | B15-07 |
| 2026-08-26 | OpenAI ExploitGym 复盘日期（主体为内部模型 IM1） | OpenAI 复盘 | 一手文档 | 沿用 | C-10 |
| 2026-09-11 | HF 博文 *One sandbox per rollout* 日期 | HF 博文 | 二手报道 / 二手引述 | 复核 | B01-08 |
| 1 亿 token；100% | SandboxEscapeBench v3 预算；Mythos Preview 至少成功一次的样本比例 | arXiv 2603.02277v3 | 论文自述 | 沿用 | B20-22 |
| 7 家 | OpenAI Agents SDK 内置沙箱 provider | OpenAI，2026-04-15 | 一手文档 | 沿用 | B16-01 |
| 2026-07-15；2026-07-21；1–100 | E2B fork 写入规范与公告日期；count 取值 | e2b-dev/infra 643d726；E2B changelog | 一手文档 | 沿用 | B16-12 |
| 2026-07-25；100（首版文档误写 16，2026-08-24 更正） | AgentENV 开源日期；fork 上限 | AgentENV 仓库 | 一手文档 | 沿用 | C-19；C-02；X-31 |
| 1 个 | 从 E2B 迁移到 AgentENV 需改的环境变量数 | AgentENV README | 一手文档 | 沿用 | B16-08 |
| 6.5 倍；9.6 倍 | AgentENV 内存超售比（K3；README 2026-08-10） | K3 §5.3.2；AgentENV README | 论文自述；一手文档 | 沿用 | C-01 |
| 15.4 倍 | AgentCgroup 内存峰均比（单任务极值） | AgentCgroup | 论文自述 | 沿用 | B03-12 |
| 2024-11-14 | 0DIN 关于 ChatGPT 代码解释器容器的逆向文章 | 0DIN | 二手报道（逆向） | 沿用 | 第 21 章表 21-2 |

## 参考文献

[1] DeepSeek-AI. *DeepSeek Elastic Compute (DSec): A Sandbox Infrastructure for Effective Agentic Training at Scale*. arXiv:2609.22978v1, 2026-09-19（预印本）. https://arxiv.org/html/2609.22978v1

[2] Kimi Team. *Kimi K3: Open Frontier Intelligence*（技术报告）. arXiv:2607.24653（v1 2026-07-27，v2 2026-08-07）. https://arxiv.org/abs/2607.24653

[3] Kimi Team. *Kimi K2*（技术报告）. arXiv:2507.20534. https://arxiv.org/html/2507.20534v1

[4] Kimi Team. *Kimi K2.5*（技术报告）. arXiv:2602.02276. https://arxiv.org/pdf/2602.02276

[5] Cursor. *Composer*. 2025-10-29. https://cursor.com/blog/composer

[6] Cursor. *Reward hacking is swamping model intelligence gains*. 2026-06-25. https://cursor.com/blog/reward-hacking-coding-benchmarks

[7] Sergio Paniego（Hugging Face）. *One sandbox per rollout, or how labs run RL for agents in 2026*. 2026-09-11. https://huggingface.co/blog/sergiopaniego/rl-environments-2026

[8] Modal. *Best sandboxes for RL environments*（资源页，竞品转述）. 2026-07. https://modal.com/resources/best-sandboxes-rl-environments

[9] Abhishek Bhardwaj. *From fork() to Fleet: Designing an Agent Sandbox Cloud*. AI Engineer World's Fair 2026 讲座页. https://ai.engineer/talks/from-fork-to-fleet-designing-an-agent-sandbox-cloud-abhishek-bhardwaj-openai ；官方转录页（2026-10-06 读取）. https://ai.engineer/talks/OqM67QG_Ikk-from-fork-fleet-designing-agent-sandbox-cloud

[10] ZenML LLMOps Database. *Designing Agent Sandbox Infrastructure at Scale: From Runtime to Orchestration*（OpenAI 演讲摘要，二手）. 2026. https://www.zenml.io/llmops-database/designing-agent-sandbox-infrastructure-at-scale-from-runtime-to-orchestration

[11] Sean Weldon. *From fork() to Fleet* 演讲笔记（二手）. 2026-07-17. https://www.sean-weldon.com/blog/2026-07-17-from-fork-to-fleet-designing-an-agent-sandbox-cloud-abhishek-bhardwaj-openai

[12] OpenAI. *The Hugging Face incident and the road ahead*. 2026-08-26. https://openai.com/index/hugging-face-incident-and-the-road-ahead/

[13] OpenAI. *OpenAI–Hugging Face Incident Technical Report*（PDF）. 2026. https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf

[14] Anthropic. *Investigating incidents in cybersecurity evals*. 2026-07-30（08-03 更新）. https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals

[15] Anthropic. *Improving our alignment and security efforts*. 2026-08-31. https://www.anthropic.com/news/improving-alignment-security-efforts

[16] Rahul Marchand 等（UK AI Security Institute）. *Quantifying Frontier LLM Capabilities for Container Sandbox Escape*（SandboxEscapeBench）. arXiv:2603.02277v3, 2026-08-01；ICML 2026 Oral. https://arxiv.org/html/2603.02277v3

[17] kvcache-ai. AgentENV README 与仓库. GitHub. https://github.com/kvcache-ai/AgentENV

[18] E2B. 控制面规范 e2b-dev/infra `spec/openapi.yml`（提交 643d726）. https://github.com/e2b-dev/infra ；E2B fork 文档. https://docs.e2b.dev/sandbox/fork ；E2B changelog. https://e2b.dev/changelog

[19] E2B. *How Manus uses E2B to provide agents with virtual computers*（客户案例）. 2025-05-06. https://e2b.dev/blog/how-manus-uses-e2b-to-provide-agents-with-virtual-computers

[20] E2B. *Genspark*（客户案例）. 2026-05-07. https://e2b.dev/customers/genspark

[21] Manus. *Understanding Manus sandbox*. 2026-01-14. https://manus.im/blog/manus-sandbox

[22] OpenAI. *The next evolution of the Agents SDK*. 2026-04-15. https://openai.com/index/the-next-evolution-of-the-agents-sdk/

[23] OpenAI. *Codex cloud environment*（产品文档）. https://learn.chatgpt.com/docs/environments/cloud-environment

[24] GitHub. *About Copilot coding agent*（产品文档）. https://docs.github.com/copilot/concepts/agents/coding-agent/about-coding-agent

[25] 阿里云. *Deep Dive: How Kimi's AI Agent Runs on Alibaba Cloud*. 2026-03-12. https://www.alibabacloud.com/blog/deep-dive-how-kimis-ai-agent-runs-on-alibaba-cloud_602942

[26] 阿里云. ACS Agent Sandbox 用户指南（含计费说明）. 2026-06-22（修改日期）. https://help.aliyun.com/zh/cs/user-guide/agent-sandbox/

[27] Yusheng Zheng 等. *AgentCgroup: Understanding and Controlling OS Resources of AI Agents*. arXiv:2602.09345（v3 2026-07-22）；AgenticOS'26. https://arxiv.org/abs/2602.09345

[28] Wei Gao 等. *RollArt: Disaggregated Multi-Task Agentic RL Training at Scale*. OSDI'26. https://www.usenix.org/conference/osdi26/presentation/gao

[29] OSWorld 2.0. arXiv:2606.29537v1, 2026-06-28（预印本）. https://arxiv.org/html/2606.29537v1

[30] Microsoft. Windows Agent Arena（GitHub 仓库）. https://github.com/microsoft/WindowsAgentArena

[31] XLANG Lab. OSWorld-Verified 博客. 2025-07-28. https://xlang.ai/blog/osworld-verified

[32] 0DIN（Marco Figueroa）. *Prompt injecting your way to shell: OpenAI's containerized ChatGPT environment*. 2024-11-14. https://0din.ai/blog/prompt-injecting-your-way-to-shell-openai-s-containerized-chatgpt-environment

[33] 阿里云开发者社区. OpenSandbox 文章（评测用例）. 2026-09-11（抓取所示日期）. https://developer.aliyun.com/article/1762374

---
