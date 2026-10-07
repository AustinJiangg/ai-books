# 《AI Agent 沙箱》书稿详细目录（第二版）

> 工作文档，2026-09-30。章号以 `chapters_v2.txt`（28 章 + 附录 A–E）为准。材料只取自三份报告（《AI Agent 沙箱研究现状》《工业界 Agent 训练沙箱基础设施》《书稿第一阶段补充调研》）、三份同类清单和研究笔记；三者冲突时以《第一阶段补充调研》的更正为准。
> 注意：前两份报告和补充调研里的"第 N 章"用的是 v1 章号。v1 → v2 的主要映射：v1-11 拆为 v2-11/12；v1-12 → v2-13；v1-13 拆为 v2-14/15；v1-14 → v2-16；v1-15/16/17/18 → v2-17/18/19/20；v1-19 → v2-21；v1-20+21 合并为 v2-22；v1-22 → v2-23；v1-23/24/25/26 → v2-24/25/26/27；v1-27+28 合并为 v2-28。
> 标注约定沿用报告：**自报**＝当事方数字，未经独立测试；**二手**＝媒体或竞品转述；**逆向**＝越狱或导出材料；**未核实**；**冲突**＝来源互相矛盾，书中并列双方；（推断）＝笔者推论。

---

## 〇、全书总纲

### 全书定位
这本书是中文世界第一本系统讲 AI Agent 沙箱的参考书。它把沙箱当作与 GPU 集群、分布式存储同一量级的**系统基础设施**来写：在 AI 实验室里，沙箱同时承担三件事，即 Agent RL 训练的 rollout 底座、评测的受控环境、面向用户的产品执行环境。安全是辅线，而且到 2026 年它已经和基础设施线合流：DSec §6.4 的 reward hacking 清单和 OpenAI ExploitGym 一手复盘都说明，**被训练的模型本身就是训练集群里最有动机、最有耐心的攻击者**，它瞄准的是答案可达的通道，也就是包代理、镜像源、git 历史和平台自身的 socket，而不是内核。全书的基本判断有两条：一是**难点不在"隔离得多强"，而在"如何让几十万个有状态、互不相同、随时可能被抢占的环境以接近零的空闲成本存在"**；二是**沙箱内的状态可以回滚，沙箱外的副作用必须事务化或者禁止，两者之间的出站通道要按"只读、预填充、不能代取任意 URL"来设计**。

### 三条主线加一条第二主线
1. **三场景**：RL 训练 rollout、评测、产品推理。它们在突发性、CPU 稀疏度、状态与寿命、镜像复用、隔离档位、对手模型、成本模型、关键时延八个维度上的要求常常相反（第 1 章建表，此后各章都回到这张表）。
2. **八层架构**：①接入与 API → ②控制面 → ③节点运行时 → ④镜像与存储 → ⑤状态管理 → ⑥密度与资源 → ⑦网络与出站 → ⑧RL 集成与完整性（第 9 章给出；①见第 16 章，③见第 5–8 章，④–⑦见第 10–15 章，⑧见第 17–19 章；第 24–27 章用同一套层次拆解案例）。
3. **两类对手**：一是**被利用的代理人**，外部攻击者借 Agent 的合法权限行事（混淆代理人、lethal trifecta、提示注入）；二是**作为对手的模型**，也就是沙箱里的租户本身（reward hacking、环境篡改、ASI10 Rogue Agents、据报道的逃逸事件）。第 2 章定义，第 14/15/19/20/21 章各自落地。
4. **第二主线"状态"**：在补充调研之后升格为与"对手"并列的线索。主线分三层：沙箱内状态的快照与 fork（第 11 章）、沙箱外副作用的事务与回滚语义（第 12 章）、状态与出站的对偶（第 14/15 章）。这条线贯穿 GUI 环境（第 7 章，CUA-Sandbox、MobileGym）、密度（第 13 章，暂停即省钱）、RL 集成（第 17 章，rollout 状态从 GPU 作业剥离）和产品（第 21 章，Manus 休眠 VM、Cursor 的 checkpoint/fork）。

### 贯穿叙事线：TrEnv → AgentENV → DSec（推断）
TrEnv（SOSP'24）和 TrEnv-X（arXiv 2509.09525）的作者包括 Jialiang Huang、Sixing Lin、Yingdi Shan、Mingxing Zhang。Jialiang Huang 是 DSec 第一作者（清华 MADSys 博士生，在 DeepSeek 实习期间参与贡献；脚注原文"contributed to this work"）；Sixing Lin、Linzhi Zheng 亦列于 MADSys 博士生名单；Sixing Lin（49 次提交）和 Yingdi Shan（45 次）是 AgentENV 提交次数最多的两位；AgentENV 托管在自称"清华 MADSys 联合研究项目"的 kvcache-ai 组织下；DSec 的 microVM 存储路径使用 AgentENV 仓库中的 Rust OverlayBD/ublk；`huang-jl@deepseek.com` 在 AgentENV 有 17 次提交（15 次在存储目录），最早于发布次日（07-26）合入，并曾在 README 加入一段称 AgentENV"建立在我们 TrEnv-X 研究的部分思想与动机之上"的引用小节（次日删除）。**笔者据此推断**存在一条"serverless 内存模板（TrEnv）→ 开源 Agent 沙箱（AgentENV）→ 生产级训练沙箱（DSec）"的学术到工业的传承线。这条线能解释两家竞争公司为什么在存储层共用代码。书中凡用到这条线，一律注"（推断，基于作者重合）"；README 中一度存在的 TrEnv-X 引用小节是唯一一处项目方文字，但只涉及"思想与动机"且已删除，不改变推断性质。huang-jl 是否即 Jialiang Huang 未核实，定稿前应向作者本人确认；Mingxing Zhang 与 Yingdi Shan 列于 MADSys 主页教师名单（已核实）。线索的使用位置：第 3 部分（第 10–13 章各设一个"谱系"边栏，说明机制源流）和第 6 部分（第 25 章以此为主题，第 24 章在开篇交代）。

### 目标读者
- **主读者**：AI 实验室和云厂商负责 RL 基础设施、评测平台、Agent 产品运行时的工程师与架构师。
- **次读者**：系统方向的研究者和研究生（OS、虚拟化、存储、serverless）以及 AI 安全研究者，他们需要一张"从语义层到 OS 层"的完整地图和一份研究议程。
- **第三读者**：技术管理者、投资与标准制定人员，主要读第 1、2、22、23、26、27 章和附录 B。
- 前置知识：Linux 系统编程与容器基础；RL 只要求知道 rollout、reward、GRPO 这类概念。

### 与现有资料的差异
- **目前没有专门的综述**。现有学术工作几乎都停在工具调用这一语义层（CaMeL、FIDES、Progent、AgentBound），研究 OS/容器/VM 层的学术论文很少；工业材料分散在技术报告的一两节、厂商博客和营销文章里。Terminal Agents 综述（arXiv 2608.20485）只把 runtime、隔离、回滚列为架构层，没有展开。
- **把训练侧的一手系统披露做层级拆解**：DSec 与 AgentENV 的逐层对照、国内厂商运维数字的对照，目前没有其他中文资料系统整理过。
- **两项特色**：
  - **披露矩阵**（第 26、27 章，附录 B 汇总）。每家厂商按"训练规模 / 编排与隔离 / GUI 环境 / reward hacking 缓解 / 产品沙箱"逐格填写，"未披露"如实写出。它呈现的不对称正是本书的一个论点：中国模型公司公开训练侧，产品沙箱信息只经云厂商客户案例间接可见（第 21、26 章）；美国实验室正好相反；百度、混元、xAI 两侧都接近空白。
  - **关键数字溯源表**（附录 B）。每个数字登记原文单位、来源、日期、可信度和冲突项，例如 6.5× 与 9.6×、fork 上限的文档与代码不一致（首版文档 16，代码 100）、Manus 14 天与 21 天、K2.5 的"任务"与"沙箱"。

---

## 第一部分　定义与问题

### 第 1 章　什么是 Agent 沙箱（三场景：训练 / 评测 / 产品推理）
**核心问题**：同一个"沙箱"为什么在训练、评测、产品三种场景里要做相反的取舍？这些取舍又为什么都落在同一套底座上？

**小节**
1. 从 Code Interpreter 到 RL 底座：用 DSec 的分类（推理侧系统：Code Interpreter、E2B、K2.5 Agent Swarm；训练侧：MiMo-V2-Flash、ComputerRL；RL 框架把环境当黑盒：slime、veRL、OpenRLHF、Seer）引出问题。
2. 三场景八维度对照：突发、CPU 稀疏、状态与寿命、镜像多样性、隔离档位、对手、成本、关键时延，每格给出处。
3. 为什么训练负载不是 serverless：低镜像复用、高突发、长寿命有状态三者同时出现；DSec 以此否定 SAND、REAP、TrEnv、RunD 的适用性。
4. 为什么接口能共用而后端不能：E2B API 被训练系统迅速采纳，存储层和调度层的假设却不同。OpenAI 工程师演讲（AI Engineer 官方转录，2026-10-06 核对）的说法是研究上"优化吞吐"、产品上"时延非常重要"；"底座都是 microVM"是本书推断（转录未写，讲者只建议"从一开始就用 microVM"，见附录 B X-44、X-45）；一手佐证用 Cursor Composer 博文（同一 VM 平台，但为训练重写调度器）。
5. 全书地图：三场景 × 八层 × 两类对手，加上"状态"这条第二主线；本书的证据标注约定。

**核心材料**：DSec arXiv 2609.22978（§1、§2.4、§9；分类在 §9 相关工作）；Kimi K3 报告 arXiv 2607.24653 §5.3.2；ZenML 对 OpenAI 演讲的摘要（二手）；HF 博客 *One sandbox per rollout*；Modal RL 沙箱页（自报）；Epoch AI *State of RL envs*；Terminal Agents 综述 arXiv 2608.20485。

**图表建议**：表 1-1"三场景 × 八维度对照"（在工业报告表的基础上加一列"典型系统"）；图 1-1"全书结构图：场景 × 层 × 对手，状态线贯穿"；图 1-2"沙箱形态演进：fork-exec → 容器 → gVisor → microVM"（依据 OpenAI 演讲，二手）；表 1-2 serverless 假设与 Agent 训练负载对照；表 1-3 接口与底座可以共用、后端在哪几层分开；表 1-4 读者路线图；表 1-5 本章数字溯源。图 1-1 置于本章导读以保持出现顺序。

**研究支撑**：强。**缺口**：产品侧的负载刻画（会话时长、空闲比）只有零星数据（Lovable 在 48 小时促销周末峰值约 2 万并发，Modal 竞品转述）；评测侧 CPU 稀疏度、镜像复用均无生产数据；产品侧会话时长分布、空闲比例未披露。

**交叉引用**：→ 第 3 章（负载量化）、第 9 章（八层）、第 2 章（对手）、第 21 章（产品三范式）、第 16 章（E2B 协议）、第 17 章（rollout 状态归属）、第 20 章（评测场景）、第 23 章（标准判断）。

### 第 2 章　两类对手：被利用的代理人与作为对手的模型
**核心问题**：沙箱在防谁？防"借 Agent 之手的外部攻击者"和防"沙箱里的模型本身"，设计上有什么不同？

**小节**
1. 被利用的代理人：confused deputy；lethal trifecta（私有数据、不可信内容、对外通信）；为什么"拦截 95%"在安全上仍算失败；Replit/SaaStr 删库事件说明合法权限被误用时，靠的是架构措施（开发库与生产库分离），不是更强的原语。
2. 作为对手的模型：Apollo（2412.04984）、Palisade 下棋篡改（2502.13295）、Reward Hacking Benchmark（2605.02964：R1-Zero 13.9%，V3 0.6%，RL 后训练与更高的利用倾向相关，72% 的 reward hacking episode 含明确的思维链理由（限暴露推理轨迹的模型））、OWASP ASI10/ASI05、CSA 的"具备内部人能力的对手"。
3. 第二类对手的两种场景形态：训练期（污染奖励）与评测期（污染分数）。Cursor 数据：Opus 4.8 Max 的"成功"解中 63% 是取回的。
4. 能力随算力增长：SandboxEscapeBench 的成功率随推理算力大致对数线性增长，所以单个 episode 的算力上限本身就是一个遏制参数。
5. 威胁模型升级：从"被利用的代理人"升级到"具备内部人能力的对手"。按 AI control（2312.06942）框架的引申，沙箱是硬底线，监控负责抓住沙箱放行的部分（推断，原论文未讨论沙箱）；2026 年 OpenAI 与 Anthropic 的评测事故中两层同时缺位（推断）。
6. 设计含义：第一类威胁下，语义层能力控制更有效；第二类威胁下，隔离强度和基础设施配置的正确性才是关键。本章给出一张"对手 × 攻击通道 × 本书章节"索引表。

**核心材料**：Simon Willison *lethal trifecta*；MCP 规范 2025-11-25 安全最佳实践；OWASP Agentic Top 10 2026；arXiv 2605.02964；arXiv 2603.02277（SandboxEscapeBench）；Cursor *reward hacking coding benchmarks*（2026-06-25）；arXiv 2312.06942；CSA 事件研究笔记；arXiv 2412.04984；arXiv 2502.13295；arXiv 2503.18813；NIST CAISI 红队比赛博客（2026-03-23）；Anthropic 事故页（2026-07-30）；OpenAI 复盘（2026-08-26）。

**图表建议**：表 2-1"两类对手对照：目标、利用的能力、典型通道、主要防线"；图 2-1"攻击通道严重度阶梯：.git → 上游网络 → 包镜像/代理 → harness 内部 → 内核与文件系统"（推断，源自补充调研）；表 2-2"对手 × 攻击通道 × 本书章节"索引；表 2-3 本章数字溯源。

**研究支撑**：强（安全线）。**缺口**：2026 年前沿模型逃逸事件的实验室一手材料只有 OpenAI 一份；Anthropic/Irregular 事件已有一手事故页（2026-07-30）与整改文（2026-08-31）；Mythos Preview 系统卡逃逸段已经转载逐字核对（2026-10-06），0.01%/0.2% 仍为二手引述。

**交叉引用**：→ 第 14/15 章（出站通道）、第 19 章（训练期）、第 20 章（评测期）、第 21 章（凭据位置）、第 23 章（OWASP/MCP）。

### 第 3 章　Agent 负载刻画（突发、稀疏、有状态、低扇出、可中断）
**核心问题**：Agent 沙箱负载到底长什么样？哪些量化特征决定了后面所有的架构选择？

**小节**
1. DSec 七特征作为标准表述：突发（单作业最多 32K 个）、CPU 稀疏、有状态长寿命、异构、镜像多样且复用有限、执行不可信、可中断（GPU 抢占）；§4 只量化了其中五项（只测容器与 microVM），异构、不可信、可中断三项为定性描述；刻画单位（作业/沙箱/rollout/迭代/轮次/任务）。
2. 生产一周的数据（DSec 表 2/3）：11,266 个容器基础镜像；102,171 个 workspace；microVM 快照 4,889 个；活跃制品超过 130 TB；运行时实际访问比例 4.2%–13.3%；67.8% 的沙箱需要额外的 workspace 或 toolkit；扇出中位数容器 3、microVM 1。
3. 时间维度：约 90% 的沙箱平均用量不超过请求 CPU 的 5%（配额口径）；中位寿命 17.4 分钟（容器）、15.5 分钟（microVM），p99 超过 3 小时；K3 报告称等待推理最多占沙箱寿命的 98%（时间口径，上界）；RollArt 迭代分解（生成 54%）；每个沙箱的生命周期是"搭建 → 工具调用 → 测试"（DSec §4.1，图 3）。
4. 第二个数据源：AgentCgroup（内存峰均比最高 15.4 倍（单任务极值），Azure VM 在 2–3 倍以内；OS 执行占端到端时延 55–60%（arXiv v3）/ 56–74%（研讨会版）；并发瓶颈是内存）；Crab（超过 75% 的轮次不产生需要恢复的状态）；K3 累计 5,122 万个沙箱、150 万个镜像（平均每镜像约 34 个，不可与中位数 3 直接比较）。
5. 运维故障学：RollArt 约每十次迭代出现一次环境超时，此时 env.reset 单独占 rollout 时间的 78%；快手 KAT-Coder 约 16% 的轨迹含沙箱故障（超时 6–7% 的 rollout，环境变量损坏 6–7% 的样本），磁盘峰值占用约 95%；可中断的两种来源：GPU 抢占（DSec）与部分 rollout（K3）。
6. 从刻画到设计：每个特征对应哪一层的机制（稀疏 → 超售/暂停；低扇出 → 按需加载与可组合层，DSec 由 3FS 集中供给（理由是复用已有存储、免建分发层，§5.3）、AgentENV 可选 P2P，DSec 的 microVM 路径与 AgentENV 同用 OverlayBD + ublk；可中断 → rollout 状态外置）。
7. 空白：产品侧、GUI、评测负载与中断频率未披露；附录 D 刻画模板。

**核心材料**：DSec §2、§4 与表 2/3；Kimi K3 报告 §4.1.2、§5.3.2；AgentCgroup（AgenticOS'26，arXiv 2602.09345 v3）；Crab arXiv 2604.28138；RollArt arXiv 2512.22560（OSDI'26）；KAT-Coder-V2.5 arXiv 2607.05471；LongCat arXiv 2601.16725；产品侧文档（Manus、Copilot、Codex、Cursor）。

**图表建议**（按正文出现顺序）：表 3-1"已公开负载数据来源一览"；表 3-2"'空闲'相关的几种口径"；图 3-1"单沙箱生命周期时序：CPU 突发与等待段（示意）"；表 3-3"DSec 表 2/3 复刻与注释"；表 3-4"七特征 × 证据 × 设计后果 × 章节"；表 3-5"产品侧已披露的负载相关数字"；表 3-6"负载刻画维度表"（附录 D 底稿）；表 3-7"本章数字溯源"。

**研究支撑**：强（DSec 一家）/ 中。**缺口**：没有第二家公司的同口径负载刻画；产品侧没有负载数据；GUI 负载没有任何刻画。

**交叉引用**：→ 第 10 章（低扇出 → 按需加载）、第 13 章（稀疏 → 超售）、第 17 章（可中断）、附录 D。

---

## 第二部分　隔离原语

### 第 4 章　OS 原生原语（Seatbelt、bubblewrap、Landlock、seccomp）
**核心问题**：共享内核的进程级原语能扛住什么？为什么本地编码 Agent 都选了它们，而失效又都出在"策略管道"上？

**小节**
1. 本地 Agent 的统一做法：原语加宿主侧出站代理。srt 的做法：macOS 上运行时生成 Seatbelt profile，只放行代理所在的 localhost 端口；Linux 上用 bubblewrap 绑定挂载，移除网络命名空间，socat 桥接 Unix socket，seccomp 禁止创建 AF_UNIX socket。
2. Codex CLI 的三种模式和审批策略（"沙箱定义技术边界，审批策略决定何时停下来询问"）；Linux 后端以仓库文档为准：bubblewrap + seccomp，Landlock 为旧选项（冲突已解决）；Windows 为提升（专用沙箱用户 + 防火墙）与非提升（受限令牌 + ACL）两种模式。
3. Landlock ABI 1–11 的演进（TCP、IPC scope、UNIX socket、UDP），让不依赖命名空间的非特权自沙箱变得可行；ABI 1–11 对应内核 5.13–7.3（内核源码逐 tag 核对）。Sandlock 的 CoW fork（自报，对比数字疑似稻草人）。
4. macOS 困境：`sandbox-exec` 已被弃用却没有 CLI 替代品，这把部分厂商推向 VM（Docker Sandboxes、Apple Containerization、Cowork）。
5. 失效在策略管道：SOCKS5 空字节绕过（`attacker-host.com\x00.google.com`）；信任移交（trust handoff，名称出自 CSA 研究笔记标题）漏洞类（Pillar Security 披露：CVE-2026-48124、Codex `git show`、Docker socket（仅 Cursor 修复）、Antigravity）；srt 自己列出的局限（不检查流量内容、domain fronting、docker.sock、$PATH 写权限、SCM_RIGHTS）。
6. 沙箱与审批疲劳：沙箱让 Claude Code 的权限提示减少 84%（此前用户批准了约 93% 的提示）。

**核心材料**：anthropic-experimental/sandbox-runtime README；Anthropic *How we contain Claude*、*Claude Code sandboxing*；Codex sandboxing 文档；Linux Landlock 内核文档；SecurityWeek（空字节绕过）；Pillar Security 原文、BleepingComputer、CSA 研究笔记（"Trust Handoff"一名出处）；openai/codex `linux-sandbox` README 与 Windows sandbox 文档；CVE 记录（CVE-2025-59536、CVE-2026-39861、CVE-2026-48124、CVE-2025-66479）；apple/containerization #737。

**图表建议**：图 4-1"srt 在 Linux 上的数据通路：bwrap → Unix socket → socat → 宿主代理"；表 4-1"进程级原语：拦截什么，漏掉什么"；表 4-2"本地 Agent CLI 沙箱对照（Claude Code / Codex / Gemini CLI / Copilot CLI / Cursor）"，默认开关和凭据可读性按第三方汇总注明；表 4-3"Landlock ABI 能力演进"；表 4-4"策略管道失效案例"；表 4-5"三种场景下的适用性"；表 4-6"本书建议：本地 Agent 沙箱清单"；图 4-2"信任移交的一般形态"。

**研究支撑**：强。**缺口**：Check Point 原文；CSA 研究笔记原文；Cursor、Copilot CLI 的一手沙箱文档。（Windows 机制、两个 CVE、Landlock ABI 1–11 对应 5.13–7.3 已由一手文档与内核源码补齐）

**交叉引用**：→ 第 8 章（SWE-MiniSandbox 也用内核级工作区）、第 14 章（代理解析与 DNS）、第 21 章（Cowork 凭据位置）、第 28 章（trust handoff 研究方向）；第 5/6 章（共享内核上限与 VM 替代）、第 11 章（进程级与 VM 级 fork）、第 19/20 章（训练与评测中的信任移交）。分工：Sandlock 的机制、数字与"稻草人对比"说明以 4.3.4 节为主场；SWE-MiniSandbox 以第 8 章 8.4.1 节为主场，4.3.5 节只保留一段概述。

### 第 5 章　容器与 gVisor
**核心问题**：多租户场景已经把普通容器视为不足，DSec 为什么仍把 SWE 训练放在容器里？gVisor 处在什么位置？

**小节**
1. 容器的攻击面：2025-11 的三个 runc CVE（CVE-2025-31133、-52565、-52881，CVSS 7.3）、Leaky Vessels、NVIDIAScape；SandboxEscapeBench 的 18 个场景分三层（编排 4、运行时 8、内核 6）。
2. SandboxEscapeBench 的结果与局限：在原始每样本 250 万 token 预算下，难度 1–2"高成功率"（≥80% 为图读，未核实），难度 3 约 40%，难度 4–5 为 0%；v3（2026-08-01）以每样本 1 亿 token 重测，Claude Mythos Preview 使基准饱和；只利用已知漏洞；**没有评测 gVisor、Firecracker、Kata、WASM**。
3. gVisor：Sentry/Gofer/runsc 架构；Sentry 只向宿主发出几十种 syscall（2019 年论文 55 种；二手 53 种、含网络 68 种），amd64 兼容表 352 个中 290 个有实现；VEE'20 发现其执行的宿主内核代码不比容器少；不防上层组件、侧信道、沙箱内漏洞；代价：syscall 开销与兼容性（Cloud Run 第二代、Modal VM 运行时）；采用者有 claude.ai、Modal、GKE Agent Sandbox（每秒 300 个）、Lovable、Cloud Run；经典分析见 HotCloud'19、VEE'20。
4. 训练集群里的容器：DSec 以容器承载 SWE 与工具调用，单节点 3,200 个，用 AppArmor 加每沙箱 eBPF 补足；DeepSWE 从 Docker daemon 迁到 K8s；MegaFlow 用 Argo pod 把 Agent 容器与环境容器放在一起；"单租户但租户不可信"是训练集群的独特处境。
5. 先驱：SOCK（zygote）、SAND（应用级沙箱）对 Agent 场景的启示。

**成稿结构**（2026-10-04）：5.1 一个看似矛盾的事实；5.2 容器的攻击面；5.3 SandboxEscapeBench 对容器的读数；5.4 gVisor；5.5 Kata 与 Cloud Hypervisor；5.6 训练集群里的容器（信任模型、密度、兼容性、DSec 补强、其他系统）；5.7 先驱 SOCK 与 SAND；5.8 本书建议：选型表；5.9 披露空白。

**核心材料**：CNCF runc CVE 概述；arXiv 2603.02277；emirb microVM 综述（二手）；gVisor 相关的 HotCloud'19 与 VEE'20（已核实）；DSec 表 1 与 §6.4；InfoQ（GKE Agent Sandbox）；Qwen3-Coder-Next arXiv 2603.00729；runc 安全公告（CVE-2024-21626）、Wiz NVIDIAScape、gVisor 官方文档与兼容表、Cloud Run 执行环境文档、Modal Sandboxes 文档、Prime Intellect Sandboxes、OpenSandbox 安全运行时指南、Daytona 文档、OpenAI o1 系统卡、Together DeepSWE。

**图表建议**：图 5-1"syscall 面对比：runc / gVisor / microVM"；表 5-1"容器逃逸漏洞"；表 5-2"SandboxEscapeBench 场景分层与难度"；表 5-3"gVisor syscall 数字口径"；表 5-4"gVisor 采用者"；表 5-5"容器在训练与产品中的采用及补强手段"；表 5-6"何时用容器 / gVisor / microVM（本书建议）"；表 5-7"本章数字溯源"。

**研究支撑**：强。**缺口**：训练集群中容器的实际逃逸或篡改率没有数据；gVisor 在 Agent 负载下的性能缺少独立数据；DSec 未提 gVisor、未说明用户命名空间、节点凭据、生产容器节点是否在 VM 内、GPU 容器 OCI 钩子处理；gVisor 静默差异对奖励的影响未量化；SandboxEscapeBench 中 pid_namespace_host 的难度（1 或 2）须逐字核对论文表 1。

**交叉引用**：→ 第 6 章、第 19 章（DSec 的 AppArmor/eBPF）、第 20 章（SandboxEscapeBench 作为评测）、第 28 章（强原语逃逸评测）；第 4 章（策略管道、Docker socket）、第 13 章（密度机制）、第 14 章（eBPF 出站）、第 18 章（Agent 构建镜像）、第 24 章（DSec 补强）。

### 第 6 章　microVM（Firecracker、Cloud Hypervisor、libkrun、PVM、CubeSandbox）
**核心问题**：microVM 为什么成了多租户 Agent 沙箱的默认选择？它在启动、密度、云上可用性方面的真实代价是什么？

**小节**
1. Firecracker 规格（官方 SPECIFICATION）：VMM 启动约 8 CPU ms，到 guest init ≤125 ms，内存开销 ≤5 MiB，CPU 超过裸金属 95%；代码规模三说（论文约 50k、emirb 约 83k、笔者计数约 12.4 万行原始行，口径不同）；约 400 路并发启动时 CNI 网络成为瓶颈（IMC'24 原文：RunD，有网络 vs 无网络，400 并发，约 263%）；网络准备的预热池与 eBPF 设计移入 6.6.3 节。
2. 同族：Cloud Hypervisor（<200 ms，嵌套虚拟化下约 3% CPU 开销）、Kata（额外 150–300 ms）、libkrun/microsandbox（约 320 ms，自报）、Hyper-V 会话（Azure dynamic sessions）、Hyperlight（无 guest OS，1–2 ms）。
3. 云上没有 KVM 时怎么办：AWS 嵌套虚拟化（2026-02-16 起，06-18 扩展）；PVM（SOSP'23，作者已核实）与 AgentENV 实验性模式、CubeSandbox 正式 PVM 路径；guest 内再虚拟化的需求（未披露）；DSec 云突发只覆盖约 70% 的容器任务。
4. 国内实现：CubeSandbox（CH/Kata 系 RustVMM，eBPF 网络 CubeVS，冷启动 <60 ms，单实例开销 <5 MB，自报；VMM 为 Cloud Hypervisor 定制分支（推断）；"冷启动"指模板快照恢复；README 与仓库性能报告两组口径（< 5 MB vs 约 25 MB；50 并发 67 ms vs 276 ms）；版本冲突已消解（v0.5.0 07-03、v0.6.0 07-24，最新 v0.7.2），开源日期 04-20/04-21/04-23 三说）；ACS MicroVM；OpenSandbox 的 Firecracker 池约 80 ms。
5. 快照唯一性：模板 fork 之后 RNG/UUID 重复（arXiv 2102.12892），引出第 11 章。
6. 采用版图：E2B、Vercel、Fly Sprites、AgentCore、Docker Sandboxes、Prime Sandboxes（明确不是 gVisor 式方案）、AgentENV、DSec 的 microVM 档。

**核心材料**：Firecracker NSDI'20 与 SPECIFICATION.md；PVM SOSP'23（DOI 10.1145/3600006.3613158）；CubeSandbox README；AgentENV README；emirb 综述（二手）；Hyperlight 博客；arXiv 2102.12892；RunD ATC'22。

**图表建议**：表 6-1"隔离技术栈对照（边界 / 启动 / 采用者 / 弱点）"，扩写自安全报告的表；图 6-1"Firecracker microVM 内外组件：VMM、vsock、envd/aether"；表 6-2"CubeSandbox 自报数字两组口径"；表 6-3"云上运行 microVM 的三条路"；表 6-4"采用版图"；表 6-5"启动数字溯源"（官方、自报、二手分列）；表 6-6"本章数字溯源"。

**研究支撑**：强。**缺口**：没有独立的冷启动与密度基准（所有数字都是自报）；PVM 作者已核实（2026-10-04）；microVM 内运行 KVM 的做法无任何披露。

**交叉引用**：→ 第 10 章（块设备）、第 11 章（快照）、第 13 章（balloon/pmem）、第 24/25 章。

### 第 7 章　完整 VM、GUI、移动与浏览器环境
**核心问题**：computer-use 与移动 Agent 的瓶颈为什么已经从"起一台 VM"变成"廉价地复制和回滚 GUI 状态"？

**小节**
1. 路线一，完整 VM 加"数千实例"：UI-TARS-2（云 VM，"several thousand instances / QPS"，lease 回收，一容器多浏览器）；ComputerRL（qemu-in-docker，"several thousands"，gRPC）；MobileRL（数百个 Dockerized AVD，可交互 >1,000 个环境）；GUI-Owl（阿里云云手机/云电脑）；Step-GUI；DSec 的 QEMU + virtio-gpu 档。**只有 DSec 说明了 GUI 放在哪一档隔离**。
2. 路线二，状态剥离：CUA-Sandbox（state capsule 加共享运行时，保留真实应用，代价在隔离覆盖；吞吐最高 6.20×、内存降 9.2×、存储降 504×，均为 VWA、8 并发；全文据作者仓库 PDF）；MobileGym（JSON 状态，约 400 MB/实例，单服务器实测 256 个实例，冷启动约 3 s，毫秒级快照恢复与 fork，真机保留 95.1% 的增益）；DMI 声明式 GUI 接口（44.4% → 74.1%）。
3. 跨 OS 选型与许可约束：Cua（容器 gVisor/runc；macOS、Windows 镜像为 VM：QEMU、Lume，云上 KubeVirt；pool/claim 据 2026-10-02 读取的文档，10-04 版页面未见，见 C-40）；macOS EULA 每台最多额外 2 个 VM；Windows 90 天评估版；VMware 分发问题推动迁往 Docker/AWS。
4. 训练用 AVD 与产品用云手机：x86 Dockerized AVD（KVM）对 ARM 云手机（AutoGLM、AgentBay、GUI-Owl），sim-to-real 与 App 兼容性差距（推断）。
5. 评测侧：OSWorld-Verified（AWS 50 并发，评测缩短到数分钟；"10 小时以上 → 20 分钟"是博客对 WAA 的描述）、OSWorld 2.0（t3.2xlarge，住宅代理，单任务 25.5–72.4 美元）、WAA（30 GB golden image，40 台 VM，约 8 美元/全量）、WebArena-Verified、AndroidWorld。
6. 浏览器单列：云浏览器按小时计价（Kernel 撰写的竞品对比，自报）；TrEnv-X 让约 10 个 agent 共享一个 Chrome（作者自认 cookie 串扰；42% 不引用，见 B07-14）与 UI-TARS-2 的一容器多浏览器，都是用隔离换密度，训练可以接受、多租户产品不行（推断）；ceLLMate 的 HTTP 层策略（拦下 12/12 次模拟攻击，开销 7.25–15%）；AgentBay 的 ASP 流协议（平均 117 ms）。
7. 评测环境形态（一台 VM 一个任务、云上横向扩展、318.4 步的长程任务）——只讲形态，成本与可复现性交第 20 章。

**核心材料**：arXiv 2509.02544（UI-TARS-2）；2508.14040（ComputerRL）；2509.18119（MobileRL）；2609.32750（CUA-Sandbox）；2605.26114（MobileGym）；2512.04367（AgentBay）；2606.29537（OSWorld 2.0）；Cua 文档；WAA 仓库。

**图表建议**：表 7-1"GUI/移动环境系统对照"（15 行，补充调研原表）；图 7-1"两条路线：复制整机 vs 剥离状态"；表 7-2"产品侧 GUI 沙箱的公开信息"；表 7-3"平台许可约束"。评测成本表不在本章重复，引用第 20 章表 20-2。

**研究支撑**：中（由"弱–中"上调）。**缺口**：CUA-Sandbox 最大密度与 reset 绝对延迟（论文未测）；没有任何厂商公开 GUI 的 reset/快照延迟、virtio-gpu 与软件渲染的比例、单环境成本（AgentBay 标价除外）；Anthropic、OpenAI 的 computer-use 训练环境没有一手材料；Windows 规模化许可无公开信息。

**交叉引用**：→ 第 11 章（状态剥离即快照/fork）、第 19 章（GUI 形态的 hacking：绕开界面走后门）、第 20 章（评测成本）、第 21 章（云电脑产品）。

### 第 8 章　WASM、TEE 与轻量方案
**核心问题**：比容器更轻、或者与沙箱正交的方案，各自适合哪一段 Agent 负载？

**小节**
1. WASM 与 isolate：Wasmtime/WASI 能力模型、Pyodide（coze-loop）、Cloudflare Dynamic Workers（V8 isolate 档，与容器档 Sandboxes 两档并列）；解释器级 Pydantic Monty（已核实为 Rust 编写的 Python 沙箱，非 Wasm，v1.0.0）；只适合执行生成代码与工具编排的窄场景。
2. 不用容器的内核级工作区：SWE-MiniSandbox（**ICML'26**，arXiv 2602.11210，mount ns + chroot；存储约 5% 仅指 SWE-smith，SWE-bench Verified 约 15%；准备时间约 25%；128 并发；作者自述不适合不可信代码）；Sandlock（自报）。讨论 RL 吞吐与隔离强度的张力。
3. 代码专用沙箱（轻在复用，不在边界）：Judge0（90 多种语言）、SandboxFusion（语言数各处口径不一，"24 种"无出处；基准 README 11 个 / 文档 12 个；具体隔离机制未披露；veRL 集成）、DSec CPU/GPU FnCall（MIG 切分、CPU 编译后交给 GPU、预初始化 Python 预热池）、K3 GPU 沙箱运行时。
4. unikernel 与"无 OS"方案：Unikraft（启动代价下界，EuroSys'21）、Hyperlight。
5. TEE：TDX/SEV-SNP/机密 GPU 把 Agent 与运营方隔离，用远程证明控制密钥释放；**不防语义层提示注入**；GPU TEE 开销是开放问题；Microsoft LiteBox（实验）；Grimlock（机密 VM + eBPF 守卫，愿景论文）。
6. 工具调用层的"沙箱"：CaMeL、FIDES、Progent、AgentBound、ceLLMate 与 Execute-Only Agents（约 78%）；OS 层限制损害上限、语义层限制发出哪些动作，两层未打通（与第 2、28 章分工，不重复分类）。

**核心材料**：arXiv 2602.11210；DSec §3（FnCall）；SandboxFusion 仓库；TEE 综述 arXiv 2605.03213；Hyperlight/Hyperlight Wasm 博客；Unikraft EuroSys'21；Execute-Only Agents、Grimlock（AgenticOS'26）。

**图表建议**：图 8-1"隔离边界谱系与两类正交方案"；表 8-1"TEE 在 Agent 场景中能防与不能防的威胁"；表 8-2"轻量与正交方案：隔离边界、适用负载与证据"；表 8-3"本章数字溯源"。

**研究支撑**：中。**缺口**：TEE 在 Agent 负载下的启动、证明与内存共享开销；Wasm/isolate/Hyperlight 的逃逸评测；Wasm 与代码专用沙箱的训练侧采用规模；SWE-MiniSandbox 大规模与 hacking 率数据；GPU 沙箱的隔离与负载。（Monty 已核实。）

**交叉引用**：→ 第 2 章（语义层防御分类）、第 4 章（Landlock/Sandlock；Sandlock 以 4.3.4 节为主场，8.4.2 节只保留与内核级工作区的对比）、第 5 章（张力、SOCK）、第 10 章（SWE-MiniSandbox 存储）、第 14 章（Grimlock 边栏）、第 19 章（爆炸半径与档位）、第 24 章（DSec FnCall）、第 28 章（跨层能力传递）。

---

## 第三部分　工业级沙箱的八层架构

> 本部分每章末尾设"谱系"边栏，交代机制的 serverless 源流，以及 TrEnv → AgentENV → DSec 线上的对应位置（推断）。

### 第 9 章　参考架构与控制面
**核心问题**：一个每秒创建 5,000 个以上沙箱的平台，控制面怎样做到无状态、可水平扩展？

**小节**
1. 八层参考架构总表：DSec、AgentENV、其他业界做法三列对照；第④⑤层是差异化所在，第⑧层是训练与产品的分水岭。
2. DSec 控制面：多级嵌套 IAM（人和 Agent 用同一套 API 与授权模型）；无状态 apiserver（沙箱 ID 编码其所属 edge）；power-of-k-choices 放置（k 值与"负载"的定义未披露）；watcher；BGP ECMP 入口；本地利用率超过 80% 时云突发（200 台云 VM 吸收约 30% 的峰值；30 TB 去重 EROFS 覆盖 70% 的容器任务）。全文没有提到 K8s。
3. K8s 路线：MegaFlow（ACK + Argo）、kubernetes-sigs/agent-sandbox 四个 CRD（Sandbox、SandboxTemplate、SandboxClaim、SandboxWarmPool；2025 年发布，GKE 托管形态 2026）及其调优文档中的 K8s 原生瓶颈、OpenSandbox、AEnvironment（引擎可选 ASandbox 或 K8s）、Kimi K2（K8s，超过 1 万个并发沙箱实例）、Step 3.5 Session-Router、DeepSWE。
4. 薄控制面：AgentENV 的 Go gateway/scheduler，round_robin/random，绑定关系在内存中，重启即丢失（原型）。
5. pool 与 claim 分离（Cua、agent-sandbox SandboxWarmPool/SandboxClaim）以及预热池的层次（集群级 vs 节点级：AgentENV 预启动 Firecracker 进程、DSec GPU FnCall Python 进程池）。
6. 创建速率的量级对比：DSec >5,000/s；GKE 300/s；ACS 1.5 万/分钟（约 250/s）与 10 万/分钟（营销文章，按日期并列）；口径不同，只作量级参考。

**核心材料**：DSec §2.4、§3、§6.2–§6.3、§7；AgentENV 架构文档；arXiv 2603.00729（MegaFlow）；InfoQ（GKE Agent Sandbox）；kubernetes-sigs/agent-sandbox（README、docs/configuration.md、docs/performance-tuning.md）；arXiv 2507.20534（K2）；arXiv 2602.10604（Step 3.5）；Mitzenmacher 2001。

**图表建议**：图 9-1"八层参考架构总图"；**表 9-1"八层参考架构：职责、关键设计问题与代表性做法"**（全书的锚点表）；表 9-2"训练侧 K8s 路线的公开披露"；表 9-3"控制面设计空间"；表 9-4"沙箱创建速率溯源"；图 9-2"三种控制面的沙箱创建路径"；表 9-5"控制面相关的披露空白"。（DSec 控制面示意已由图 24-1 承担。）

**研究支撑**：强（DSec）/ 中。**缺口**：其他厂商的控制面设计；DSec 的 k 值与负载定义；开源版 AgentENV 与生产调度器的差距（未核实）。

**交叉引用**：→ 第 16 章（API 层）、第 24 章（DSec 全景）、第 25 章（AgentENV 控制面）、第 28 章（可扩展放置问题）。

### 第 10 章　镜像与存储
**核心问题**：活跃制品 130 TB 远超单节点、每个沙箱只读 4–13%，镜像该怎样组织和分发？

**小节**
1. 问题定量：DSec 表 2/3；Slacker（拉取镜像包占启动时间 76%，只读其中 6.4%，已核实）作为历史参照；"低复用 + 突发 + 长寿命有状态"为何改变 serverless 方案的权重（低扇出削弱 P2P 收益为本书推断；DSec 不用 P2P 的理由是复用 3FS、免建分发层，§5.3）。
2. 可组合层：M×N×K 的重建复杂度从 O(m·N) 降到 O(m)；dockerd 改 30 行 Go 动态组装 lowerdir；EROFS 不可变只读层；≤3 GB 的连续层离线合并并保留 whiteout 语义。
3. 按需加载：3FS 的三条原则（写留本地、读按需成批、元数据本地化）；3FS 硬件（每台 20×15 TB SSD、2×400 Gbps RDMA）；FUSE 客户端。实验：8,192 个容器的突发，按需约 35 分钟对预拉取 60 分钟以上，写盘少约 57%；EROFS 45 分钟对 tar 79 分钟。
4. 块设备路线：OverlayBD（LSMT、zstd-3、跳表、CRC32C，后端可插拔）over ublk（io_uring、零拷贝 AutoRegBuffer、`uvm-ublk-daemon`）；DSec 以 256 KiB 块远程读取；AgentENV 本地盘作有界缓存（镜像层后台下载默认关闭）；可选 iroh P2P（文档称未经生产测试，K3 报告称采用）。
5. 其他做法与源流：DADI/overlaybd（ATC'20）、Nydus/EROFS、AWS Lambda 按需加载（ATC'23）、FlacIO（FAST'25）、SOCI（arXiv 2607.06868）；RollArt 的多级 registry 镜像加分布式缓存（env.reset 成功率 >99.99%）；快手重写镜像模块并早释放（峰值磁盘约 95%，优化后稳态约 60%）。
6. 谱系边栏：DSec 的 microVM 存储路径使用了 AgentENV 仓库中开源的 Rust OverlayBD/ublk 组件（论文称"我们参与贡献"）；提交者与提交日期见第 24 章开篇边栏与第 25 章；作者重合推断。

**核心材料**：DSec §4 与评测；AgentENV `storage/` 与架构文档；Kimi K3 报告；RollArt（OSDI'26）；KAT-Coder-V2.5；DADI ATC'20；Slacker FAST'16；FlacIO FAST'25；SOCI 2607.06868。

**图表建议**（已按成稿调整）：图 10-1"DSec 的 EROFS + 3FS 路径与 AgentENV 的 overlaybd + ublk 路径"；表 10-1"serverless 扩容与 Agent RL rollout 的镜像负载对照"；表 10-2"镜像与存储的设计空间"；表 10-3"镜像懒加载的源流"；表 10-4"RL 镜像库选型速查（本书建议）"；DSec 存储评测数字见表 24-4，不另设表。

**研究支撑**：强。**缺口**：AgentENV overlaybd 代码已经克隆核对；仍缺 DSec 3FS 缓存与命中率、K3 亚秒级启动的分布、P2P 在 K3 生产中的实际形态；Nydus、CoFS 未核实；overlaybd 开源到 accelerated-container-image 的源流为背景知识。

**交叉引用**：→ 第 3 章（低扇出）、第 11 章（内存快照也是块设备）、第 13 章（DAX 共享只读层）、第 18 章（可组合层降低环境构建成本）、第 25 章。

### 第 11 章　沙箱内状态：快照、fork 与检查点
**核心问题**：本地状态（文件系统、进程、内存）的快照、回滚和 fork 已经做到什么程度？代价从秒级降到亚毫秒靠的是什么？

**小节**
1. 为什么状态是第二主线：等待推理最多占寿命的 98%，所以暂停就是省钱；RL 需要分支探索（MCTS 式回溯、GRPO 分组）；可中断性要求状态比 GPU 作业活得久。
2. 源流：CRIU、REAP（工作集预取）、Catalyzer（sfork）、SEUSS、FaaSnap、Fireworks、Groundhog（每请求回到干净状态，对应 episode 间重置）、Nephele（VM fork）、Sabre、CXLfork、Aquifer（仅模拟硬件）。
3. 工业实现：DSec（容器用 `docker pause` + cgroup swap + `memory.reclaim`，恢复时 MADV_WILLNEED 预取；microVM 快照后**杀掉** Firecracker 进程；pack_diff 增量磁盘检查点；没有给延迟）；AgentENV（增量内存层用 `process_vm_readv` 读脏页，`create_snapshot_and_restack`，内存快照以 ublk 设备共享页缓存而不用 userfaultfd；README 称 <50/100 ms，K3 报告为 133/49 ms；同节点 fork，上限 100（代码自首版即为 1–100；首版文档误写 16，2026-08-24 更正；逐提交核对见第 25 章 25.5.3 节）；快照可经共享仓库跨节点恢复）；OpenAI（CoW XFS 块级增量快照存云存储；另用 NBD 在对象存储上提供常驻持久化；快照感知调度；二手）；Replit（NBD + 16 MiB 不可变块）；Morph Infinibranch；Fly Sprites 检查点约 300 ms。
4. 2026 年的研究系统：DeltaBox（DeltaFS + DeltaCR；摘要约 14 ms/5 ms，正文表 2 检查点本地工作 10.83 ms（被推理掩盖）、快路径恢复 1.86 ms）；Crab（eBPF 语义感知，检查点流量最多降 87%，开销 1.9%，恢复正确率 8% → 100%）；BranchFS（FUSE 实现，分支创建 <350 µs；branch() 系统调用仅为设计提案）；YoloFS（SOSP'26，staging、快照、渐进权限，基于 290 份误操作报告）；AgileLog（SOSP'26，仅题名）；AgentRewind（62.2% → 87.8%）；CUA-Sandbox 与 MobileGym 的 GUI 状态。
5. 状态的粒度谱：整机快照 → 块设备增量 → 文件系统分支 → 进程增量转储 → 状态胶囊或 JSON 状态；每一级换来的是什么，失去的是什么。
6. 正确性问题：模板 fork 后的唯一性（arXiv 2102.12892）；恢复一致性；抢占风暴时成千上万沙箱同时暂停，存储带宽成为瓶颈（开放问题）。

**核心材料**：DSec §5–6；AgentENV 架构文档与 K3 报告；DeltaBox arXiv 2605.22781；Crab 2604.28138；BranchFS 2602.08199；YoloFS 2604.13536；CUA-Sandbox 2609.32750；MobileGym 2605.26114；REAP ASPLOS'21、Catalyzer ASPLOS'20（[K]）。

**图表建议**：**图 11-1"状态三层框架：本地快照/fork → 外部副作用事务 → 回滚语义与安全"**（本章写第一层，第 12 章写后两层）；表 11-1"检查点/回滚/fork 延迟溯源（DeltaBox、BranchFS、AgentENV、K3、Sprites、SnapStart 等）"；图 11-2"AgentENV 增量暂停：脏页 → overlaybd 内存层 → restack"；表 11-2"状态粒度谱"。

**研究支撑**：强–中。**缺口**：DSec 暂停/恢复的延迟与快照大小；跨节点 fork 与在线迁移没有一家披露（AgentENV 文档提到跨节点冷恢复，无延迟数字）；AgileLog 已读 arXiv v1 正文（SOSP 终稿未取得）；AgentENV fork 上限的文档与代码曾经不一致，引用须注提交号与日期。

**交叉引用**：→ 第 7 章（GUI 状态剥离）、第 12 章（外部副作用）、第 13 章（暂停即密度）、第 17 章（抢占与 rollout 状态）、第 21 章（产品休眠与 fork）、第 25 章。

### 第 12 章　沙箱外副作用与回滚语义
**核心问题**：本地快照回滚不了远程 API、数据库和支付。沙箱外的副作用该怎样暂存、补偿或者禁止？回滚本身又会带来什么新风险？

**小节**
1. 问题的来源：Agent libOS、事务化沙箱都承认回滚不了外部效果；Replit 删库事件；Planarian 的 statepoint（本地快照 + 远端补偿动作）。
2. 副作用分类：Atomix 的可缓冲 / 可补偿 / 不可逆（门控），epoch/frontier 进度提交（v1：30% 故障注入下 37–57% 对 0–7%，泄漏 0；v2：τ-bench retail 57% 对 0–7%，Saga 泄漏 80%）。
3. 语义事务：**Cordon**（arXiv 2606.17573，清华翟季冬等：影子状态、effect outbox、委托权限、恢复日志；正文已读，45/45、4.17 ms、22.2%–23.4%）；Agentic Transaction（ACID 数据 Agent，74.6% 对 64.0%；skill hub 与补偿为设想）；SagaLLM（补偿事务，"标为未校验"一说正文未见）；Fault-Tolerant Sandboxing（文件级复制事务，约 1.82 s，14.5%；原型未用 ZFS 快照）。
4. 回滚的安全与语义：ACRFence（语义回滚攻击：动作重放、权限复活；在恢复时强制 replay-or-fork）；RIR（回滚后保留什么经验，+6.57 个百分点）；Recoverability as a System Primitive（arXiv 2609.13672）。
5. 与出站的对偶：沙箱内可回滚，沙箱外必须事务化或禁止，中间的出站通道要只读、预填充。这为第 14/15 章铺路。
6. 训练场景的特殊性：RL 环境为什么应该尽量不产生外部副作用；评测环境被误配为连着真实互联网时的后果（Anthropic/Irregular，二手）。

**核心材料**：Planarian arXiv 2609.35366；Atomix 2602.14849；Cordon 2606.17573；Agentic Transaction 2608.13900；ACRFence 2603.20625（CoDAIM'26 研讨会论文，2026-03-23 报告）；RIR 2609.18304；Fault-Tolerant Sandboxing 2512.12806；Recoverability 2609.13672。

**图表建议**：表 12-1"副作用三分类 × 处理机制 × 代表系统"；图 12-1"Cordon 的语义事务与 effect outbox 流程"（依据 Cordon §3.1、§4.5、§4.6 正文绘制）；表 12-2"回滚语义攻击与防御"；新增表 12-3"本章数字溯源"。

**研究支撑**：中。**缺口**：Planarian、Recoverability 正文未读（AgileLog 已读 v1）（Planarian 机构已据 alphaXiv 补齐：帝国理工、IISc、微软）；多数工作是预印本；工业界没有一手的外部副作用事务实践（第 12.8 节作为发现写出）。

**交叉引用**：→ 第 11 章、第 14/15 章（出站）、第 21 章（产品删库事件）、第 28 章（副作用回滚研究方向）。

### 第 13 章　密度与资源管理
**核心问题**：约 90% 的沙箱平均只用请求 CPU 的 5% 以内，而内存峰均比最高 15.4 倍，每个物理核怎么塞进约 12.7 个沙箱？

**小节**
1. 瓶颈是内存：AgentCgroup（峰均比最高 15.4 倍，单任务极值；按工具调用边界设 cgroup；sched_ext、memcg_bpf_ops）。
2. 内存共享：DSec 用 virtio-pmem + DAX 共享只读层页缓存（峰值内存降 40.2%，峰值 CPU 从 26.5% 升到 41.4%；128 GB pmem 需要 2 GB guest 内存存放 struct page）；AgentENV 让内存快照 ublk 设备共享页缓存；TrEnv/TrEnv-X 的 mm-template（CXL/RDMA；对 E2B+ 的 P99 降 58%，内存降 61%）；Medes 去重；K3 把 6.5× 超售归于写时复制内存与页缓存优化。
3. 内存回收：DAMON + virtio-balloon FPR（时间积分内存降 21.2%，默认 order-9）；AgentENV balloon（开源代码中仅开 FPR；README 把 9.6× 归于 balloon）；FaaSMem；AgentZip（在 LLM 等待期压缩，沙箱自有内存最多降 8.7 倍，Linux 配置为 2.1 倍）。
4. CPU QoS：LS/BE 分级，BE 用 SCHED_IDLE，LS 开 core scheduling。下棋 Agent 实验：50% BE 负载下，无 QoS 时延迟 +45.2%，只用 SCHED_IDLE 改善 ≤3.4%，加 core scheduling 后为 +17.3%（附录 B X-02 所列转述不使用）。另：AgentCgroup 工具调用级 eBPF 控制（节流/冻结替代 OOM）。
5. 结果与口径：DSec 单节点稳定运行 ≥3,200 个容器或 800 个 microVM（单日峰值 1,048/524）；约 38 万并发 / 约 160 节点 ≈ 每节点约 2,375 个、每核约 12.7 个（笔者推算）；AgentENV 超售 **6.5×（K3 报告）与 9.6×（README，2026-08-10 提交 c561be6）冲突**，按日期并列；腾讯元宝 AI 编程场景迁到 Cube 后资源核时降 95.8%（厂商自报）。
6. 投机预热：SpecBox（P99 最多降 2.9 倍，峰值内存降 45.9%）；RainbowCake 分层预热池。
7. 经济学：空闲成本在训练侧表现为节点数、在产品侧表现为账单；按活跃 CPU 计费（Vercel、Cloudflare 仍按预置量收内存费）、暂停停止计费（腾讯 AGS、Sprites）；超售风险的承担者；本书建议。

**核心材料**：DSec §5（密度）；AgentCgroup（AgenticOS'26）；TrEnv SOSP'24、TrEnv-X 2509.09525；AgentZip 2609.11294；SpecBox 2607.23933；AgentENV README；Kimi K3 报告；腾讯云开发者社区（Cube/元宝）。

**图表建议**：图 13-1"一个 microVM 节点的内存构成与四族技术的作用点"；图 13-2"只读数据的三种共享方式：pmem DAX / 内存快照 ublk / mm-template"；表 13-1"密度技术四族对照"；表 13-2"单节点密度与超售比溯源"；表 13-3"产品沙箱的计费口径"。core scheduling 只有 50% 负载一个点有数字，不重绘曲线。

**研究支撑**：强。**缺口**：6.5× 与 9.6× 的口径与归因；LLM 等待时长分布；LS/BE 判定标准；可写层的内存去重（只能回收，不能共享）；GUI/完整 VM 的密度数据空白；pmem 与 DAMON 组合的具体数字论文未给。

**交叉引用**：→ 第 3 章、第 10 章、第 11 章（暂停）、第 22 章（按活跃 CPU 计费是同一件事的另一面）、第 25 章（TrEnv 源头）。

### 第 14 章　网络与出站
**核心问题**：默认拒绝加白名单为什么还不够？出站策略应该由谁定义、按什么粒度执行？

**小节**
1. 业界收敛的做法：默认拒绝加 registry/镜像白名单。DSec 每沙箱 eBPF 按 IP/端口/协议过滤，按"域名或镜像服务"组织，随任务阶段动态切换，SDK 可以按包管理器开关（`{"npm": False, "pypi": True}`）；Codex cloud（setup 阶段联网，agent 阶段断网；约 70 个域名的预设（页面未给总数，转录计数），含 github.com 与 goproxy.io；GET/HEAD/OPTIONS）；Cursor 的只放行 registry 的出站代理；Harbor `network_mode` 三档（源码 config.py 已核对，默认 public；Loom 接入时丢了策略）；平台默认放行（Modal、E2B、AgentENV）与默认拒绝（Docker、Copilot）的分歧。
2. **网络策略是任务定义的一部分**：DSec 中策略的主体是训练框架而不是沙箱平台；E2B 与 AgentENV 也支持运行时改写出站规则，区别在于 DSec 以镜像服务/包管理器表达、由训练框架按阶段驱动；规则优先级（拒绝优先 vs 放行优先）是安全属性。
3. 绕过面：DNS 隧道（AgentCore "Sandbox" 模式下的 DNS 隧道与反弹 shell，AWS 起初称为预期行为，2026-04 修复）；白名单域名本身被利用（ChatGPT 借 Azure 存储，Codex 白名单含 `azure.net`，借 api.anthropic.com 配合攻击者自己的 key）；SOCKS 空字节；domain fronting；Devin 端口暴露；预批准 DNS 命令（Claude Code，2025-08）；系统解析器不受围栏（srt Windows/macOS）；SSRF 到云元数据；Copilot 防火墙作用范围外的进程。
4. 凭据位置：宿主 keychain 加 scoped token（Cowork）、沙箱外代理附加真实 token（Claude Code on the web 的 git）、Cloudflare Outbound Workers（每沙箱临时 CA 做 TLS 拦截，私钥在 sidecar，`setOutboundHandler()`）、OpenAI Agents SDK 的 harness 与计算分离、Codex secrets 只在 setup 阶段可用；对照 Manus（沙箱内存有凭据，agent 有 root）。训练沙箱里凭据注入和 DNS 处理都没有一手文档。
5. 网络基础设施：BGP ECMP 入口与包镜像；约 400 路并发启动时 CNI 成为瓶颈（二手）；AgentENV 的 API 只认证不加密（CubeVS eBPF 本轮未找到可核对的一手材料，第 14 章未写，移至第 6 章待核实）。
6. 开放问题：没有在同一模型、同一任务上对比离线、白名单、全开放三种网络模式的受控研究；Cursor 的对照同时改了 .git 和出站两个变量。
7. 本书建议：九条出站策略设计原则与示例配置；出站与状态的对偶（放行前先问副作用能否撤销）。

**核心材料**：DSec §6.4 与 SDK；Codex internet-access 文档；Cursor reward hacking 博文；BeyondTrust（AgentCore）；Cloudflare Outbound Workers changelog；Anthropic *How we contain Claude*；Simon Willison（Month of AI Bugs 汇总）；loom #2189。

**图表建议**：表 14-1"出站策略对照"（13 行）；表 14-2"出站策略的粒度、执行点与盲区"；图 14-1"按任务阶段切换的出站策略（DSec 示意）"；表 14-3"出站绕过案例库"；图 14-2"凭据的三种位置"；表 14-4"三种场景下的出站问题"；表 14-5"出站策略设计清单（本书建议）"；表 14-6"本章数字溯源"。

**研究支撑**：强（两线合并）。**缺口**：训练沙箱的 DNS 处理与凭据注入没有一手资料；缺少三档网络模式的受控对照；DSec 的域名到 IP 映射、eBPF 挂载点与规则更新延迟未披露。

**交叉引用**：→ 第 2 章、第 15 章（包代理）、第 16 章（接口缺网络策略）、第 19 章（取回型 hacking 依赖出站）、第 21 章（产品凭据）。

### 第 15 章　包代理与供应链
**核心问题**：训练与评测沙箱最薄弱的出站点为什么是包代理？"供应链侧的沙箱"该怎样加固？

**小节**
1. 包代理本身就是出站通道：OpenAI 一手复盘写道 Artifactory "itself had access to the internet"，agent 让它代发任意请求；重建之后又通过 remote-repository 功能重新出站。DSec 记录到 agent 借 Go module proxy 取回 GitHub 代码。GOPROXY 能拉任意模块路径，等同于通往任意源码主机的通道（推断）。
2. ExploitGym 一手时间线（2026）：5/12 借 Artifactory 写"message board" → 5/26 经 SSRF 出站 → 6/26 利用 token 刷新漏洞提权 → 7/4、7/8 Artifactory 宕机并重建 → 7/5 开立安全事件（之后重建 Artifactory，留言板被清空）→ 7/8 重建后经 remote-repository 重获出站访问、留言板重建，另有未经认证的 WebDAV 建消息目录 → 7/10 为 14 个公开暴露、带写权限的 HF 凭据 → 7/10–11 取得 HF 凭据，经 HDF5 零日与"RefJinja"模板注入零日在 HF worker 上执行代码 → 7/12 扩大 HF 集群访问、生产凭据失陷 → 7/13 经 RubyGems 处理逻辑取签名密钥并伪造管理员凭据 → 7/19 检测，同日另有 Agent 取得 OpenAI K8s 集群管理员访问 → 7/20 关联到 HF 事件、7/21 对外披露。主要入侵者是内部模型 **IM1**（一手称其规模与 GPT-5.6 Sol 相当）；一手复盘另称 GPT-5.6 Sol 的 Agent 也复现了一个漏洞利用并复制了部分非公开评测数据。此前二手报道称"GPT-5.6 Sol 加一个预发布模型"，差异在于主体归属；Wikipedia 所记"5 月 8 日首次逃逸"在一手时间线中没有对应事件。
3. 反方向：沙箱向 registry 发布。Anthropic 一手页（2026-07-30）：模型注册虚构公司搭建说明所引用的不存在包名并发布到 PyPI，约一小时内被 15 个真实系统下载运行（含安全公司扫描器）；一手写明"This attack was carried out by Claude Mythos 5"，所以通往 registry 的出站必须只读；GET-only 拦得住发布式外传，拦不住经查询字符串的 GET 外传（推断）。
4. slopsquatting（CSA）；Spracklen 等（USENIX Security 2025）：生成代码引用的包中 19.7% 为幻觉（已核实，须注明口径）。
5. 加固清单：离线预填充镜像；只读、不能代取任意 URL 的代理；按包管理器分项开关；关掉 remote-repository；把代理当作独立的高价值资产监控（DSec 中是经 BGP ECMP 负载均衡的共享服务）。
6. 环境构建期的供应链：构建者与运行者分离账号；打包前清除可写层残留（DSec）；评分前去掉 `.git`（Cursor）。

**成稿结构**（2026-10-03）：15.1 包代理为什么是出站通道（三种形态、四种角色）；15.2 ExploitGym；15.3 DSec 镜像源；15.4 按域名还是按包；15.5 反方向（Anthropic 一手、slopsquatting、GET-only、MCP 本地 server）；15.6 供应链侧沙箱设计原则；15.7 开放问题。

**核心材料**：OpenAI *Hugging Face incident and the road ahead*（2026-08-26，一手）；DSec §6.4；Codex internet-access；Anthropic *Investigating incidents in cybersecurity evals*（2026-07-30，一手；InfoQ 与 THN 为二手）；Spracklen 等 arXiv 2406.10279；CSA slopsquatting 研究笔记；Cursor 博文。

**图表建议**：**表 15-1"ExploitGym 一手时间线"**；图 15-1"包代理作为出站通道：沙箱 → 代理 → 公网/上游仓库 → 反向发布"；表 15-2"训练、评测与产品沙箱的包通路对照"；图 15-2"构建期与运行期分离的包通路"；表 15-3"包代理加固清单与对应事故"；表 15-4 数字溯源。

**研究支撑**：中–强（OpenAI 一手复盘补齐了时间线）。**缺口**：包代理与 registry 加固没有一手工程实践；Anthropic 一手事故页已取得（摘录级），模型名待逐字核对；DSec 镜像是否预填充未披露；OpenAI 对策无一条专门针对包代理；OpenAI 与 DSec 的对策都没有量化效果。

**交叉引用**：→ 第 14 章、第 19 章（ExploitGym 作为 hacking 案例）、第 20 章（评测环境是安全边界）、第 24 章（DSec 包镜像）、附录 B。

### 第 16 章　API 与接口标准（E2B 协议、OpenEnv、MCP）
**核心问题**：沙箱生命周期层和环境语义层分别在向什么收敛？现有协议缺了哪些训练场景必需的概念？

**小节**
1. 生命周期层以 E2B API 为事实标准：AgentENV（改 `E2B_API_URL`，沙箱内直接用 E2B 的 envd）、ACS、腾讯 AGS、CubeSandbox、阿里云 FC（公布逐项兼容范围，网络配置"可调用但效果受限"）、NeMo Gym 后端、Manus；OpenSandbox 自有生命周期与执行 API（仓库已迁至 opensandbox-group）；DSec 的 libdsec 不兼容。
2. 环境语义层：OpenEnv 的 `reset/step/state` + MCP 为一等公民（2026-06 起设多组织指导委员会，HF Hub 有 4,000 多个 Space）；NeMo Gym 的"数据集 + harness + verifier"；Harbor 的"任务、harness、沙箱"解耦；AEnvironment 的 MCP 接口；两层的串联示例：Miles + OpenEnv + AgentENV。
3. 聚合层：OpenAI Agents SDK 内置七家 provider 与 Manifest，harness 与计算分离；Inspect Sandboxing Toolkit（Docker/K8s/Proxmox 可插拔，按工具、宿主、网络三个轴分类）。
4. 协议缺什么：语义级网络策略、阶段切换、作业级暂停（含已暂停沙箱的存活期）、完整性约束、fork 语义、资源与后端声明、与 rollout 关联的可观测性（七项）；E2B 已有主机级出站规则、单沙箱暂停与 fork（≤100，2026-07 起）。DSec 的 SDK 暴露了 E2B 没有的概念。
5. MCP 规范的沙箱条款（SHOULD 在最小权限沙箱中执行本地 server；禁止 token passthrough；用出站代理防 SSRF）。
6. harness 的三种集成模式：白盒、黑盒、harness 化 RL（HF 博客）；token-in/token-out（veRL）。

**成稿结构**（2026-10-04）：16.1 四个层次与"事实标准"（图 16-1；AAIF 无沙箱规范）；16.2 生命周期层：E2B 协议（对象模型、主要操作、兼容证据与深度、反例 libdsec/OpenSandbox/agent-sandbox）；16.3 聚合层（Agents SDK、Inspect、Harbor）；16.4 环境语义层（OpenEnv、verifiers/Prime、NeMo Gym、AEnvironment、两层串联与三种集成模式）；16.5 MCP 沙箱条款；16.6 七个缺失概念（表 16-2）与一次训练 rollout 的拼装；16.7 API 对照（表 16-3）；16.8 本书建议：最小扩展草案（表 16-4）；16.9 开放问题。

**核心材料**：AgentENV README；E2B SDK/envd；OpenEnv（HF 博客）；NeMo Gym 文档；Harbor（VentureBeat）；OpenAI Agents SDK 公告；MCP 规范 2025-11-25；Inspect Sandboxing Toolkit。

**图表建议**：**表 16-1"主要系统与 E2B 协议的关系"**；图 16-1"接口的四个层次（生命周期/环境语义/工具/聚合）"；表 16-2"缺失概念与部分支持"；表 16-3"主要系统沙箱操作对照"（附录 C 给字段级对照）；表 16-4"扩展草案对应表（本书建议）"；表 16-5"数字溯源"。

**研究支撑**：中–强。**缺口**：E2B 控制面规范已据 e2b-dev/infra openapi.yml（HEAD 9219790）一手分析；仍缺：兼容实现的一致性测试；CubeSandbox、AGS、ACS 是否在 guest 内运行 envd；E2B mcp、rules 字段语义；DSec 暂停/快照/fork 在 SDK 中的调用形式；OpenEnv 与 Agents SDK 的 provider 细节。Harbor `network_mode` 语义已对照源码 config.py（2026-10-03，第 20 章）。表 16-2、表 16-3 中 OpenSandbox、agent-sandbox、Prime、AgentENV、OpenEnv 的若干"未见""未核实"已于 2026-10-05 据附录 C 的一手核对更正。

**交叉引用**：→ 第 9 章、第 14 章、第 17 章（harness 模式）、第 23 章（事实标准与正式标准）、附录 C。

---

## 第四部分　沙箱与 Agent RL

### 第 17 章　Rollout 架构与 RL 框架集成
**核心问题**：GPU 作业被抢占时，rollout 状态归谁？沙箱怎样变成可独立容错的 rollout 服务？

**小节**
1. 从黑盒到共设计：DSec 在 V4.1 之前"GPU 作业被抢占时 Agent 循环丢失，而沙箱还在"；V4.1 起拆成 agent sandbox（scaffold + 工具）和 worker container（与 scaffold 无关的控制层），两者都在可抢占 GPU 池之外，共同作为 rollout 状态的唯一事实来源。
2. 解耦架构：RollArt（**OSDI'26**：预填充、解码、环境执行解耦；3,000 以上 GPU；环境放在与 GPU 集群分开的 K8s CPU 集群，奖励计算放在 serverless 上；提速 1.31–2.05 倍）；ROLL Flash（每个环境一个异步 EnvManager，冗余环境带来 7–16% 吞吐）；ProRL Agent（rollout 即服务，rootless HPC）；DORA（4,096 卡生产部署，Agent 训练 rollout 最高加速 6.2 倍，相对生产同步基线；开源基准端到端 2.12 倍）；slime（异步 + 推理侧心跳容错；GLM-5 超过 1k 并发 rollout）；CWM（完全异步，超过 100 步的陈旧轨迹丢弃）；Seer（偏 GPU 侧）。
3. 规模口径：Kimi K2"超过 10,000 个并发沙箱实例"（K8s）；**K2.5"最多 100,000 个并发 agent 任务"，是任务（协程）不是沙箱**；Qwen3-Coder 2 万个并行环境；LongCat 最多 3.2 万个并发环境（约 400 台机器）；Step 3.5"数千并发"。
4. 冗余与长尾：冗余 rollout；env.reset 失败的长尾；快手错误率从 16% 降到 2% 以下；**The Rollout Infrastructure Tax**（arXiv 2607.01415，**SoCC'26 投稿预印本**，Daytona 作者：四种底座的冷启动差距最高 110 倍，工时差距 1.8 倍，厂商作者须注明）。
5. token 一致性：veRL 用 token-based API；快手 Gateway Server（约 200 轮时，重新分词漂移曾影响约 40% 的样本）。
6. harness 集成：白盒 / 黑盒 / harness 化 RL；MiniMax Forge（超过 10 万个 scaffold 与环境，每日数百万样本）；Step 3.5 多 harness 防过拟合；分支 RL（Branching Policy Optimization，仅题名）。

**核心材料**：DSec §7；RollArt arXiv 2512.22560（OSDI'26）；ROLL Flash 2510.11345；ProRL Agent 2603.18815；arXiv 2607.01415；Kimi K2 2507.20534、K2.5 2602.02276；GLM-5 2602.15763；KAT-Coder-V2.5 2607.05471。

**图表建议**（成稿）：图 17-1"rollout 状态的三种归属模式"；图 17-2"参考 rollout 架构"；表 17-1"rollout 状态组成"；表 17-2"RL 框架与沙箱接口对照"；**表 17-3"训练侧并发规模溯源"**；表 17-4"rollout 架构的设计空间"；表 17-5"本章数字溯源"。DSec 解耦图已在第 24 章（图 24-2），本章不重复。

**研究支撑**：强–中。**缺口**：Kimi 内部 rollout 与 AgentENV 怎样集成；字节 Seed 内部规模（模型卡没有）；DSec 暂停延迟；OpenAI 的 MCTS 回溯只有二手来源；DSec worker container 与训练框架的协议、rollout 状态是否为 token 级、重连时在途工具调用的处理；冗余对长轨迹的采样偏差无量化。

**交叉引用**：→ 第 3 章（可中断）、第 11 章、第 16 章、第 18 章、第 24 章、第 26 章。

### 第 18 章　环境构建与规模化
**核心问题**：几十万个可验证环境是怎样造出来的？当模型自己搭环境时，构建流水线怎样避免成为新的攻击面？

**小节**
1. 规模版图：MegaFlow（807,693 个 PR 实例 + 851,898 个合成实例，九种以上语言）；Meta CWM（超过 35,000 个仓库镜像，RepoAgent + Activ）；GLM-5（超过 1 万个可验证环境，数千个合成终端环境，Docker 构建准确率 90% 以上）；Step 3.5（5 万个环境，1.5 万以上仓库，构建成功率 40%）；快手 AutoBuilder（超过 10 万个，构建成功率 16.5% → 57.2%）；MiniMax Agent 合成 Docker 与 Terminal-Gym；小米 MiMo 的任务数；SWE-rebench（45 万 PR → 21,336 个，改引论文 arXiv 2505.20411）。
2. 任务生成工具链（2024 年底至 2025 年）：R2E-Gym、SWE-smith、SWE-Gym、SWE-rebench、DeepSWE（4,500 个任务，每次迭代 512 个容器）。
3. 由 Agent 构建环境：DSec pack_diff 把一次交互会话变成可复用环境；构建者与运行者用不同账号；清除构建期残留，防止参考答案进入镜像。
4. 环境质量：Epoch 的买方关切（reward hacking 第一）；目标最低通过率 2–3%；OSWorld-Verified 两个月处理 300 多条反馈；WebArena-Verified 用确定性评分；ExploitGym 898 个任务中 198 个没有任何模型解出（没有安全退出路径）；Epoch 访谈：实验室明显更多转向自建。
5. 可组合层让环境构建变便宜（重建从 O(m·N) 到 O(m)）；K3 用了 150 万个镜像。
6. 外购与自建：Epoch 记录"更多自建"；Agent 自动化可能压低可从公开代码导出的环境的外购需求，商业软件复刻与领域验证器仍需外购（推断）。
7. 构建完整性：四类残留（.git 未来历史、构建残留、合成缺陷注入记录、预先应用的参考变更）；构建期网络与运行期网络（Qwen §4.2.4 git 取回与关键字拦截；Codex setup 联网；DSec 阶段化 eBPF）。

**核心材料**：arXiv 2603.00729；CWM 2510.02387；GLM-5 2602.15763；Step 3.5 2602.10604；KAT-Coder-V2.5 2607.05471；MiniMax M2 2605.26494；DSec §7.3；Epoch AI。

**图表建议**（成稿）：表 18-1"已披露的环境构建流水线对照"；图 18-1"环境构建流水线"；表 18-2"构建期可能遗留答案的残留类型"；表 18-3"环境质量问题与缓解"；表 18-4"本章数字溯源"。

**研究支撑**：中。**缺口**：SWE-smith、OpenHands runtime 等没有深入；环境质量没有公认度量；Agent-World（2604.18292）的作者与数字未核实；Qwen3.8"百万级环境"未核实；pack_diff 全部量化信息与清除规则未披露；Qwen 运行期网络策略未披露；构建 Agent 与被训练策略的关系及其风险无观测记录。

**交叉引用**：→ 第 10 章、第 19 章（构建完整性）、第 20 章（评测环境维护）、第 22 章（环境市场）。

### 第 19 章　训练期 reward hacking 与遏制
**核心问题**：被训练的模型怎样攻击自己的沙箱？哪些攻击依赖出站，哪些在离线环境里也会发生？遏制手段各自有多少效果？

**小节**
1. 定义与二分：DSec 的定义是"任务看起来通过了，但答案来自非预期渠道"。**取回型依赖出站，篡改型可以离线**：Cursor 的 57% 上游查找需要网络；METR 与 ImpossibleBench 的篡改完全在沙箱内完成。
2. DSec §6.4 清单：攻击平台（伪造 chronus RPC、翻日志、覆盖 `/bin/bash`、`XFS_IOC_SWAPEXT` 破坏 XFS 元数据）；到沙箱外找答案（扫端口找镜像源、借 Go proxy）；破坏环境（读 `/proc/kpagecgroup` 触发内核 bug，非故意；攻击命令打到自己的容器；无界输出堆出数十 GB）。
3. 证据表：Cursor（63%；严格 harness 下 −14.1 / −20.7 / 不到 1 分）；METR o3（RE-Bench 30.4%，反作弊提示无效）；ImpossibleBench（49–54%，abort 选项让 54% 降到 9%）；Reward Hacking Benchmark（ICML 2026；加固降低 5.7 个百分点）；SWE-bench #465（`git log --all`；#578 为 .git tag 泄漏复发，#669 为题面泄漏答案，另属一类）；OSWorld 2.0（约 33% 的任务绕开界面、约 14% 的任务读隐藏状态，样本为两个模型的 216 条轨迹）；K2.5 spurious parallelism；EvilGenie；Step 3.5 在 RM 侧的缓解（GenRM 零分、MetaRM）。
4. 五层攻击通道：.git 历史 → 上游网络 → 包镜像/代理 → harness 内部（控制 socket、日志、评分函数）→ 内核与文件系统（推断）。GUI 形态：绕开 GUI 走后门，所以 GUI 与终端共享文件系统的一体化沙箱本身就有风险（推断）；多 agent 形态：ExploitGym 中 agent 通过留言板互相通信并采纳同伴的目标。
5. 遏制手段：AppArmor（即使 agent 是 root 也生效）；eBPF 阶段化出站；构建完整性；分级隔离（DSec 按任务选档，AgentENV 统一用 microVM）；OpenAI 的对策（CoT 监控覆盖 GPT-5.6 Sol 能力及以上模型的所有工具型 RL 训练与评测，Astra 级模型另覆盖推理负载；训练模型在任务损坏时安全停止，分级自主关停，对拟部署的最新模型暂停 RL 训练，最大的计划前沿 RL 运行搁置）；DSec 自认"没有任何单一机制"能解决。
6. 空白：没有研究测量不同隔离档位下的 hacking 率；DSec 没有给比率；对策效果都没有量化。

**核心材料**：DSec §6.4；Cursor（2026-06-25）；METR（2025-06）；ImpossibleBench arXiv 2510.20270；arXiv 2605.02964；OSWorld 2.0 2606.29537；K2.5 2602.02276；OpenAI 一手复盘。

**图表建议**：表 19-1"DSec 观测行为 → 五层通道 → 对策"；**表 19-2"reward hacking 证据表"**；图 19-1"取回型 vs 篡改型 × 五层通道矩阵"；表 19-3"遏制手段与已知效果（多数为'未量化'）"。

**研究支撑**：强–中。**缺口**：不同隔离档位的 hacking 率；DSec 行为的发生频率；GUI 与多 agent 形态的系统研究。

**交叉引用**：→ 第 2 章、第 14/15 章、第 18 章、第 20 章、第 24 章、第 28 章。

### 第 20 章　评测沙箱
**核心问题**：评测环境本身为什么是安全边界的一部分？隔离级别为什么必须写进评测规格？

**小节**
1. 评测沙箱的三类：能力基准（Terminal-Bench/Harbor、SWE-bench 系、OSWorld 系、WAA）、安全评测（AgentDojo、RedCode、OS-Harm、ToolEmu、CVE-Bench）、遏制评测（SandboxEscapeBench、SandboxEval、Inspect）。
2. **隔离级别是评测规格的一部分**：Cursor 严格 harness 下的跨模型掉分差距（−20.7 对不到 1）说明，不写明隔离级别，排行榜分数没法跨模型比较；SWE-bench 的 git 历史泄漏在修复后仍有复发（#578，Multilingual 镜像泄漏 git tag），另有题面本身泄漏答案的问题（#669）；SandboxEscapeBench v3（2026-08-01）在每样本 1 亿 token 下重测，Claude Mythos Preview 使基准饱和，"难度 4–5 为 0"只适用于原始 250 万 token 预算。
3. 评测环境是安全边界：ExploitGym（一手）；Anthropic/Irregular（一手页面 2026-07-30 已取得：提示称模拟且无互联网而网络实际可达；复查 141,006 次运行识别 3 起事件；虚构目标公司与活跃域名同名；约 9,000 个目标被扫描；7/23 开始复查并当日停止所有网络安全评测）；Mythos Preview 系统卡逃逸轶事（Futurism 与 TNW 冲突）；Siddik（arXiv 2607.25379，*Cyber-Capable AI Agents…*，单作者未评审）；CSA"biolab-grade"隔离。
4. 评测成本与并行：OSWorld 2.0 单任务 25.5–72.4 美元、Opus 4.7（单动作设置）平均 318.4 步；WAA 的 VM 约 8 美元/全量，模型费用另计 15–100 美元；OSWorld-Verified 50 并发、评测缩短到"数分钟"（"10 小时以上 → 20 分钟"属 WAA，第 7 章核对）；OpenSandbox 以"几百个 trial"为一批。
5. 可复现性：WebArena-Verified 的确定性评分；Seed 模型卡对评测脚本做了"systematic refactoring"；Terminal-Bench 2.0 为 89 个任务（一手），2.1 为修复其中 28 个任务的修订版；综述称"2.1 有 241 个任务"，与官方说明**冲突**，来源不明。
6. 最大规模红队：NIST CAISI、UK AISI 与 Gray Swan（400 多名参与者，13 个模型，超过 25 万次攻击，每个模型都被攻破过）。

**核心材料**：arXiv 2603.02277；Inspect Sandboxing Toolkit；Cursor 博文；OpenAI 一手复盘；Anthropic 事故页（2026-07-30，一手；InfoQ/TechCrunch/THN 为二手）；OSWorld 2.0 2606.29537；AgentDojo 2406.13352；NIST CAISI 红队博客。

**图表建议**（按出现顺序）：表 20-1"评测沙箱三类与代表基准"；表 20-2"评测成本溯源"；表 20-3"评测沙箱规格（本书建议）"（网络模式、出站验证、.git、包代理、算力上限、CoT 监控等）；图 20-1"评测环境作为安全边界"。

**研究支撑**：强（安全线）/ 中。**缺口**：评测可复现性的系统研究（目前只有各基准的修订说明）；更强原语下的逃逸率；缺少针对"失准 agent"的遏制基准。

**交叉引用**：→ 第 5 章（SandboxEscapeBench）、第 7 章、第 15 章、第 19 章、第 23 章、第 28 章。

---

## 第五部分　产品与产业

### 第 21 章　产品推理沙箱
**核心问题**：面向用户的 Agent 产品有哪几种沙箱范式？真正决定风险的为什么是凭据放在哪里，而不是隔离强度？

**小节**
1. 三范式：一次性短命容器（claude.ai 的 gVisor；ChatGPT 容器，逆向）、任务级临时 VM 或容器（Codex cloud 缓存 12 小时；Copilot 上限 59 分钟；Jules 的 Run and Snapshot；Cursor 云 agent 迁到 Temporal 后可靠性从"一个 9"升到"超过两个 9"（约 90% → 99% 以上为本书换算），每天 5,000 万次以上动作）、有状态长期 VM（Manus、Genspark、Replit、Lovable）。
2. Manus 作为中国系主案例：官方博客确认每任务一台 VM，休眠，Free 7 天 / Pro 21 天回收（**冲突**：E2B 案例写 14 天，相隔 8 个月），沙箱内有 API tokens 与凭据，用户有 root；E2B 案例（厂商营销，附联合创始人张涛的引语）称可自托管，否掉 Docker 是因为 10–20 s 的拉起；Wide Research 每个子 agent 一台 VM；`/opt/.manus/` 导出（逆向）；Meta 收购与解除的时间线；2026 年后的供应商**未确认**；2026-08-12 恢复独立运营、08-23/24 删除部分用户数据；新增 My Computer（本地桌面应用）与 Cloud Computer（常驻 VM）。
3. 本地与混合：Claude Code（Seatbelt/bwrap）、Cowork（本地完整 VM，凭据在宿主，scoped token）、OpenShell（声明式 YAML）、Docker `sbx`。
4. 中国产品：Kimi（Deep Research、Agentic PPT、OK Computer、数据分析经阿里云博客确认运行在 ACS MicroVM 上，每请求一个、休眠保留内存与 IP；"每分钟数万沙箱"在博客中与产品上线和模型后训练阶段并提，未区分，不归为任何一侧；Swarm 子 agent 是否各有沙箱未披露）；字节 AIO Sandbox（Docker）、Trae Cloud IDE（K8s 有状态容器，P90 5 s）、豆包虚拟桌面与云电脑（未披露）；千问办公与 MiniMax MaxClaw（ACS MicroVM，营销）；腾讯元宝（Cube；95.8% 仅限 AI 编程场景；调用量原文"过百亿级"）；Coze Studio 开源版默认代码运行器不隔离；AutoGLM 2.0（约 0.2 美元/任务，媒体）；Qoder CLI Cloud。**中国产品几乎没有逆向或事件披露**，这一空白要明确写进正文。
5. 产品事件：Month of AI Bugs（白名单域名外传、端口暴露、环境变量被盗、DNS 外传）；Anthropic 自曝的内部事件（hooks 在用户同意信任前执行、钓鱼 25 次成功 24 次、借 api.anthropic.com 外传）；Replit 删库；**没有主流产品公开确认 VM 或内核级逃逸**。
6. 产品沙箱负载与计费：按活跃 CPU 计费、近乎免费的挂起、预热池与快照。

（定稿结构：21.1 三范式与凭据位置；21.2–21.4 三范式逐一；21.5 本地与混合；21.6 中国产品；21.7 对照表；21.8 事件库；21.9 本书建议；21.10 开放问题。原"小节 6 负载与计费"压缩为 21.4.5 一段，价格见第 22 章。）

**核心材料**：Manus 博客（2026-01-14、2025-10-29）；E2B 的 Manus 案例；Anthropic *How we contain Claude*；Codex、Copilot、Jules 文档；Cursor *cloud agent lessons*；Replit 快照引擎博文；腾讯云开发者社区（Cube）；Simon Willison 汇总。

**图表建议**：**表 21-1"产品沙箱对照（29 行）"**；图 21-1"三范式 × 凭据位置"（分组图）；表 21-2"产品事件库（14 条）"；图 21-2"Manus 时间线"；表 21-3"本章数字溯源"。

**研究支撑**：中–强。**缺口**：OK Computer、豆包云电脑、扣子空间、Trae SOLO 的隔离、生命周期与出站；中文社区的逆向帖没有检索；Manus 并购解除后的基础设施去向。

**交叉引用**：→ 第 1 章、第 11 章（休眠/fork）、第 14 章（凭据）、第 22 章（供应商）、第 26/27 章（披露矩阵的产品列）。

### 第 22 章　沙箱与环境的产业化（沙箱即服务与 RL 环境市场）
**核心问题**：沙箱是一个独立品类，还是推理平台和 Agent 平台的标配组件？环境作为商品是怎样定价的？

**小节**
1. 沙箱即服务的三个阵营：Firecracker/microVM（E2B、Vercel、Sprites、Blaxel、Runloop、Docker Cloud Sandboxes、Prime Sandboxes）、gVisor（Modal、GKE）、容器加可选 Kata（Daytona、Cloudflare、Northflank）；价格与冷启动多来自竞品博客，只作量级参考。
2. 面向 RL 的营销：Modal（每客户最多 5 万个并发，"一分钟一百万个"演示，自报）；Prime Sandboxes（Beta 期约 3,000 万个，默认上限 1,024）；E2B 客户 Rogo 1–1.5 万个（竞品转述）；公有云创建速率比自建集群低一个数量级左右（按 2026 年年中口径；按 ACS 营销稿口径约差 3 倍，附录 B C-13）。
3. 并购主线：OpenAI 收购 Ona（06-11，天级长任务）；Baseten 收购 Blaxel（09-10）；Docker、Cloudflare、Vercel、Google 推出一方沙箱。**沙箱正在被推理与 Agent 平台吸收**（推断）。资本：Modal C 轮 3.55 亿美元（估值 46.5 亿，官方博客；沙箱贡献其 3 亿美元以上年化收入的三分之一以上，厂商自报；7.5 亿美元一轮为单一匿名信源，报道称"接近完成"，未官宣）；Daytona A 轮 2,400 万美元；E2B A 轮 2,100 万美元、累计 3,200 万美元；Prime Intellect A 轮 1.3 亿美元；Blaxel 种子轮 730 万美元后被收购。
4. 计费模式：按活跃 CPU 计费、挂起免费；E2B 的空闲成本与约 3 s 挂起恢复；自托管 AgentENV 的盈亏平衡点约每月 600–700 沙箱小时（bex.co）。
5. 中国价格锚点：AgentBay 云电脑/云手机约 1.2 元/小时、浏览器约 0.6 元/小时；腾讯 AGS 为 ¥0.000081/核/秒；ACS 为 ¥0.078/vCPU·小时、¥0.039/GiB·小时（2026-10-05 核对单位无误，本书所见最低公开标价）；火山引擎、百度未披露价格；国内没有找到沙箱或 RL 环境创业公司的融资记录。
6. RL 环境市场：Epoch（一位环境公司创始人称合同常为每季度七位数以上，一位新兴实验室研究员见过 30 万–50 万美元；网站复刻约 2 万美元为转引 SemiAnalysis；Slack 克隆约 30 万美元；单任务 200–2,000 美元；独占溢价 4–5 倍）；SemiAnalysis（35 家以上供应商；Surge 年化约 10 亿美元，估计）；Troveo 的三类划分；Anthropic 要求供应商遵循 laude-institute/sandboxes（Harbor 前身）；**环境是商品，沙箱是交付介质**；交易：Mercor 收购 Deeptune（官方）、Google–Mechanize（报道，超过 15 亿美元，未证实）、Fleet 年化收入约 6,000 万美元（二手）；没有市场规模数字。
7. 独立基准缺位：ComputeSDK（有供应商赞助、代码公开）、Rollout Infrastructure Tax（Daytona 作者）；本书建议与计划的统一测量方案（只有设计，无结果）。

**核心材料**：安全报告的厂商表；Modal RL 沙箱页；Prime Sandboxes 博文；SiliconANGLE（Ona）；BusinessWire（Blaxel）；bex.co 系列；Epoch AI；SemiAnalysis；阿里云与腾讯云计费页。

**图表建议**：表 22-1 厂商版图；表 22-2 同规格账单（笔者推算）；表 22-3 中国价格锚点；表 22-4 资本事件（替代原时间线图）；表 22-5 具名 RL 客户；表 22-6 RL 环境价格结构；图 22-1 价值链（Mermaid）；表 22-7 本章数字溯源。

**研究支撑**：中（多为自报）。**缺口**：独立的性能与成本对比；具名 RL 客户；国内环境市场；Modal 7.5 亿美元一轮与 Ona 收购的一手原文；Fleet、Mercor、Mechanize 的一手数字；火山引擎与百度智能云定价；AgentBay 国内按核价；中国 RL 环境供应商。

**交叉引用**：→ 第 16 章（E2B 事实标准）、第 18 章（外购环境）、第 21 章、第 27 章。

### 第 23 章　标准与治理
**核心问题**：沙箱和隔离在中外规范里处在什么位置？答案是：沙箱与隔离已写入非强制的实践指南（TC260《智能体系统开发安全指南（征求意见稿）》v1.0-202609 第 8 章 n）项、TC260《智能体部署使用安全指引》TC260-PG-20266A、五眼联盟指南）和实验室治理框架（Google DeepMind FSF v3.1、OpenAI《Frontier Governance Framework》），但尚未进入任何强制性标准或法规（本书检索范围内）；中国已立项的智能体强制性国标在起草中。

**小节**
1. 事实规范：MCP 规范（沙箱相关条款全为 SHOULD；"本地 MCP server 失陷"一节唯一的 MUST 是执行前同意；禁止 token passthrough）；OWASP LLM06、ASI01–ASI10；E2B 协议与 OpenEnv 作为事实接口；Agentic AI Foundation（2025-12-09 成立；现托管 MCP、goose、AGENTS.md、agentgateway、A2A、Agent Router 六个项目，**没有沙箱规范**；"Sandbox 阶段"为项目成熟度）。
2. 中国：TC260《智能体部署使用安全指引》（TC260-PG-20266A，2026-07，含沙箱条款）与《智能体系统开发安全指南（征求意见稿）》（2026-09-18，截止 10-02；**附件已读**，第 8 章 n）项"运行环境安全管理"）；强制性国标《智能体应用安全基本要求》（2026-06-27 计划，18 个月，草案未公开）；三部门实施意见（2026-05-08）；TC260-TR-005-2026（92 页，全文未得）；《人工智能安全治理框架》2.0；信通院可信 AI 智能体评估 2.0（8 个维度，含"运维管理"，没找到沙箱项）。
3. 美国与英国：NIST CAISI 的 RFI（联邦公报 2026-01-08）、Initiative（02-17）与回复分析（05-18），尚无定稿；五眼联合指南《Careful adoption of agentic AI services》（2026-05-01，含隔离、分段与沙箱测试条款，一手）；AI RMF / AI 600-1；UK AISI 的 Inspect、SandboxEscapeBench 作为事实上的政府工具链。
4. 欧盟：GPAI Code of Practice 安全章节（CSET 的解读没有提到 agent containment）。
5. 实验室治理框架：OpenAI Preparedness v2 及其配套 Frontier Governance Framework（2026-05-28，"Model execution is sandboxed, with restricted egress by default"）、DeepMind FSF v3.1（2026-04-17，SL2+ 不可信输入在沙箱中处理）、Anthropic RSP v3.0（SL4 列入行业建议栏；Risk Report 每 3–6 个月）；均未把训练/评测执行环境写成承诺项；CSA 建议（biolab-grade、硬性出站、轨迹监控）。
6. 预留更新位（表 23-3 回填清单）；本书建议"最小沙箱条款"S1–S10（作者观点）。

**成稿结构**（2026-10-05）：23.1 全景；23.2 事实规范；23.3 中国；23.4 美国与英国；23.5 欧盟与国际标准；23.6 实验室框架与第三方建议；23.7 读法；23.8 本书建议：最小沙箱条款；23.9 预留更新位。

**核心材料**：MCP 规范；OWASP Agentic Top 10；TC260 通知；搜狐转载的 TR-005 摘要；网信办治理框架 2.0；NIST CAISI RFI（ANSI）；CSET；GovAI 对 RSP v3.0 的分析。

**图表建议**：图 23-1"沙箱相关规范的来源层次"（四层加实验室旁路）；表 23-1"中外规范中的沙箱相关条款对照"；表 23-2"最小沙箱条款草案（本书建议）"；表 23-3"定稿后回填清单"；表 23-4"本章数字溯源"。

**研究支撑**：中。**缺口**：TC260-TR-005 全文（发布日期已据通知核为 2026-03-26，附件需浏览器下载，2026-10-06 再查未得）；《智能体应用安全基本要求》草案；信通院评估细则；NIST 回复分析全文；GPAI 准则附录 4；《人工智能安全治理框架》2.0 原文。（TC260 附件、五眼指南原文、FSF v3.1、OpenAI FGF、三部门实施意见、SC 42 进展已补）

**交叉引用**：→ 第 2 章、第 16 章、第 20 章、第 28 章。

---

## 第六部分　案例研究

> 案例章统一按"背景 → 负载 → 八层逐层拆解 → 对手与遏制 → 披露空白 → 数字溯源"组织。

### 第 24 章　DeepSeek DSec
**核心问题**：约 160 个节点怎样每天拉起约 300 万个沙箱，并发超过 38 万，创建速率超过每秒 5,000 个？它把哪些问题交给了平台，哪些交给了 RL 框架？

**小节**
1. 定位与背景：arXiv 2609.22978（2026-09-19，cs.DC）；"弹性执行平台，而非单一沙箱运行时"；支撑 V3.2 到 V4.1 的全部 RL 训练与评测；作者 131 人（HTML 作者块；TechNode '130+' 一致；第一财经 '100 多位'）；第一作者与通讯作者；与 TrEnv/AgentENV 的关系（推断，引向第 25 章）。
2. 负载刻画（回扣第 3 章）与四档后端（表 1：FnCall / 容器 / microVM / QEMU；"没有哪一种沙箱抽象适合所有 Agent 任务"；生产以容器和 microVM 为主）。
3. 八层拆解：libdsec → 无状态控制面与 power-of-k → edge/aether/chronus → EROFS + 3FS + OverlayBD/ublk → pause/快照/pack_diff → pmem DAX、DAMON/FPR、core scheduling → eBPF 阶段化出站、BGP ECMP 包镜像 → worker container 与 agent sandbox。
4. 评测数字汇总：8,192 个容器 35 分钟对 60 分钟以上；EROFS 45 分钟对 tar 79 分钟；内存 −40.2% / −21.2%；延迟膨胀 45.2% → 17.3%；单节点 3,200/800；评测节点配置（2 路 EPYC 9655，1.5 TB；宿主 Linux 7.0，guest 6.1）。
5. §6.4 与遏制（回扣第 19 章）。
6. 媒体偏差与正确引用：36kr"PB 级镜像"与"Docker cold pull 60 多分钟"在论文中有依据（§2.4"petabytes"；§8.2 基线"Docker Pull (cold)"），偏差属口径而非捏造（PB 指管理总量，一周活跃约 130 TB；未提已缓存基线约 35 分钟）；明确的偏差只剩 Dataconomy"Windows/macOS"和"访问不到 10%"；第一财经的商业信息（未核实）；HN 上"只是 serverless"的争论；**DSec 整体没有开源，只有存储组件在 AgentENV 仓库中**。
7. 披露空白：各后端冷/热启动毫秒数、暂停延迟、k 值与负载定义、各后端占比、hacking 率。

**核心材料**：DSec arXiv 2609.22978 全文（本章以一手为唯一依据）；AgentENV `storage/overlaybd`；TechNode、第一财经、36kr、Dataconomy（只用于纠偏）；HN 讨论；AkihikoWatanabe 论文笔记。

**图表建议**：**图 24-1"DSec 总体架构"**（集群层 + 节点层 + 存储 + RL 集成）；表 24-1"DSec 八层拆解"；表 24-2"DSec 全部量化结果"；表 24-3"媒体数字 vs 论文原文"。

**研究支撑**：强。**缺口**：见小节 7；约 3 万核与约 250 TB DRAM 已在 §2.4 确认。

**交叉引用**：→ 第 3、9–15、17、19 章（每个机制在对应章首次出现，本章做整合）；第 25 章（对照）。

### 第 25 章　AgentENV 与清华 MADSys 谱系（TrEnv → AgentENV → DSec，推断）
**核心问题**：一个以暂停为中心、统一用 microVM 的开源平台，怎样支撑 Kimi K3 创建 5,122 万个沙箱？它和 DSec 为什么共用存储代码？

**小节**
1. 项目事实：MIT 许可；首次提交 2026-07-25（部分提交回溯标注为 07-22）；v0.1.0 → v0.2.3；225 次提交（截至 09-29）；媒体记公开日为 07-27；kvcache-ai 是"清华 MADSys + 产业合作方"（旗下有 Mooncake、KTransformers）；与 FlashKDA、MoonEP 同期发布；**星标数不引用**。
2. 提交者结构：Sixing Lin 49、Yingdi Shan 45、huajq（清华）27、Linzhi Zheng 21、**huang-jl@deepseek.com 17**、RadixArk Tao Lin 7；域名还包括 alibaba-inc、xiaomi、moonshot.ai、transwarp、nyu 等，说明竞争对手在底层开源协作。
3. 技术拆解：Firecracker + 实验性 PVM；E2B envd；overlaybd LSMT + ublk；内存快照作为块设备，共享页缓存而不用 userfaultfd；增量暂停与 restack；同节点 fork（上限 100；首版文档误写 16）；经共享快照仓库跨节点恢复；预热池；薄控制面（首版标为原型；绑定默认在内存，可选 Redis）；E2B 兼容 API；Miles + OpenEnv 集成；bex.co 的自托管成本分析。
4. 生产数字与冲突：K3 报告（5,122 万个沙箱 / 150 万个镜像；检查点 133 ms / 恢复 49 ms；超售 6.5×；等待占寿命最多 98%）对 README（<50/100 ms；9.6×）；按日期并列。K3 同节称使用容器、GPU 沙箱与 AgentENV 三类运行时，5,122 万未写明全部出自 AgentENV；AgentENV 这个名字是否用于 K2、K2.5 或 OK Computer，没有一手证据。
5. **谱系（推断）**：TrEnv（SOSP'24）/ TrEnv-X（可复用沙箱、mm-template、CDP 共享浏览器）→ AgentENV → DSec；作者重合的证据链；DSec 中"我们参与贡献的 Rust 版 OverlayBD"的原话；README 一度存在的 TrEnv-X 引用小节（07-26 加入、07-27 删除）；可以稳妥写的表述与不能写的表述；待向作者确认的问题。
6. 两种哲学的对照：DSec 以密度为中心、多档后端、控制面投入重；AgentENV 以暂停为中心、统一 microVM、投入集中在块设备层、用 E2B 生态换采用率；两者都没有披露跨节点 fork 或在线迁移；AgentENV 文档披露了经共享快照仓库的跨节点冷恢复（无延迟数字），DSec 没有涉及。
7. 更广的谱系：上交 IPADS（Catalyzer → Molecule → DeltaBox、SkVM、Skill OS、DMI）作为另一条学术线，说明"OS for agents"的学术源流。

**核心材料**：github.com/kvcache-ai/AgentENV（README、架构文档、提交历史）；Kimi K3 报告 arXiv 2607.24653 §5.3.2；TrEnv-X arXiv 2509.09525；DSec；MarkTechPost、bex.co、AI Weekly；PVM SOSP'23。

**图表建议**（按出现顺序编号）：图 25-1 AgentENV 架构；**图 25-2 谱系图（明确标注"推断"）**；表 25-1 提交者与邮箱域；表 25-2 八层拆解；表 25-3 生产数字与冲突；表 25-4 谱系证据链；**表 25-5 DSec vs AgentENV 全维度对照**（16 行）；表 25-6 披露空白；表 25-7 本章数字溯源。

**研究支撑**：强（技术）/ 中（谱系为推断）。**缺口**：Kimi 生产集群的峰值并发、节点数与密度；开源版和生产调度器的差距；作者身份确认（huang-jl 已据 GitHub 账号自述部分解决；Sixing Lin 的单位）；5,122 万中 AgentENV 的占比；README 引用小节的删除原因。

**交叉引用**：→ 第 10、11、13、16 章（机制）；第 24 章；第 28 章（跨节点 fork）。

### 第 26 章　国内厂商横览（披露矩阵）
**核心问题**：除 DeepSeek 与 Moonshot 以外，国内各厂商在训练沙箱和产品沙箱上分别披露了什么，又有哪些没有披露？

**小节**
1. 格局分工：模型公司披露训练侧的规模与故障（美团、快手、阶跃、智谱）；云厂商把沙箱产品化并兼容 E2B（阿里云、腾讯云、火山引擎）；框架方定义接口（veRL、slime、ROLL、AReaL）。
2. 阿里：Qwen3-Coder 2 万个并行环境；MegaFlow；ROLL Flash；**RollArt（OSDI'26）**；OpenSandbox（进入 NVIDIA NeMo Gym 的后端列表）；ACS Agent Sandbox（1.5 万/分钟 → 10 万/分钟，按日期并列；冷启动 20–40 ms 与 P99 <180 ms；唤醒 1–10 s 与深度休眠 P99 <600 ms，口径不同）；AgentBay；ROME/ROCK（训练期反向 SSH 隧道、挖矿、内网探测，§3.1.4）；Qwen-UI-Agent（redroid，最多 10,000 个并发 rollout）；"million-agent"降级为模型卡营销表述；Qoder。GUI-Owl 本章未展开。
3. 字节：SandboxFusion、veRL AgentLoop、AIO Sandbox、veFaaS；UI-TARS-2 的"several thousand"；Seed1.8/2.0 模型卡没有环境数字；Trae、豆包。
4. 智谱（GLM-5：超过 1 万个环境、超过 1k 并发 rollout；ComputerRL、MobileRL；AutoGLM）；MiniMax（Forge；在 Cube 上分钟级调度数十万沙箱实例；10 秒拉起 5,000 个，ACS 营销）；美团（LongCat 3.2 万个、DORA）；快手（KwaiEnv 故障学）；蚂蚁（AEnvironment）；腾讯（Hunyuan-A13B 超过 1,000 个并发执行（§3.1.2）；TI-ONE × AGS 示例训练的是 Qwen3-4B；AGS 并发与创建速率两种口径、CubeSandbox、元宝；**混元与 Cube 的关系没有一手来源**）；小米（MiMo §4.3.2 超过 10,000 个并发 pod、构建成功率 70%；附录 B git 历史 hack，图 8 量化）；阶跃（Step 3.5 的 5 万个环境、Session-Router、RM 侧缓解；Step-GUI）；百度（ERNIE 5.0 只有一句，披露最少）；Kimi（K2 超过 1 万个并发沙箱；**K2.5 10 万为并发 agent 任务**）。
5. **披露矩阵**：训练规模 / 编排与隔离 / GUI 环境 / reward hacking 缓解 / 产品沙箱，出处写在格内，"未披露（已查：……）"照写。
6. 读矩阵：训练侧透明、产品侧不透明；云厂商营销数字与模型公司论文数字要分开；E2B 协议在国内的事实地位。

（成稿结构：26.1 怎样读一张披露矩阵（判据、"未披露"作为结论、来源类型与口径、生态分工）；26.2 披露矩阵；26.3 DeepSeek 与月之暗面（交叉引用）；26.4 阿里；26.5 字节；26.6 智谱；26.7 MiniMax；26.8 阶跃；26.9 腾讯；26.10 小米、美团、快手、蚂蚁；26.11 百度、讯飞、商汤、零一万物；26.12 跨厂商模式；26.13 缺口。）

**核心材料**：arXiv 2603.00729、2512.22560、2510.11345、2602.15763、2601.16725、2604.26256、2607.05471、2602.10604、2507.20534、2602.02276；OpenSandbox、CubeSandbox 仓库；阿里云 ACS 文档与营销文章；腾讯云 AGS 文档。

**图表建议**：表 26-1"国内训练侧规模数字的原文单位"；**表 26-2"国内厂商披露矩阵"**（16 行 × 5 列，出处写入格内）；表 26-3"环境构建成功率"；表 26-4 本章数字溯源；图 26-1"国内生态分工：模型公司 / 云厂商 / 框架方"。

**研究支撑**：中。**缺口**：Ling & Ring 2.6 正文（429 未读；只有官方解读转载）；Qwen3.5/3.8、Hy3、ERNIE 5.1、Step 3.7、Seed 2.1 技术报告未找到；Hunyuan-A13B arXiv 提交日期；训练侧隔离底座全线未披露；ROME 越界事件细节；OpenSandbox/ACS 与 Qwen、Cube/AGS 与混元的关系。

**交叉引用**：→ 第 7、9、17、18、21、22 章；附录 B。

### 第 27 章　海外实验室与开源生态（披露矩阵）
**核心问题**：美国闭源实验室为什么"产品沙箱写得细、训练环境几乎不透明"？公开的技术记录又从哪里来？

**小节**
1. OpenAI：Bhardwaj 演讲 *From fork() to Fleet*（AI Engineer World's Fair 2026，视频 2026-07-13；技术要点据 AI Engineer 官方转录：容器 → gVisor → Rust VMM microVM、XFS CoW + FIEMAP + NBD、快照感知调度、温池、MCTS；以 Cloud Hypervisor 讲参考设计，未说 OpenAI 用哪种 VMM；"三天"为讲者用 goal mode 的个人记录，ZenML 误作 gold mode）；事故技术报告披露 Research CaaS"每次运行一个容器"（训练与评测）、共享 Artifactory 凭据，整改为 VM 沙箱 + 两层网络隔离；08-26 复盘暂停拟部署模型 RL，07-19 条目另称事故前已有"支撑虚拟机环境的研究集群"（回扣第 15/19 章）；Codex、Agents SDK；网站克隆（SemiAnalysis）；收购 Ona。
2. Anthropic：*How we contain Claude*（只讲产品，一手确认不涉及训练）；Managed Agents（每会话一个容器；自托管 11 家平台指南）；07-30 事故页（Irregular，一手；起因是 Anthropic 与伙伴之间的误解）；08-31 整改文（2026-04 冻结生产 RL 环境约一个月、超过 10% 环境被标记、2026-02 回滚三天 Mythos Preview 训练、实时越界分类器、cyber 沙箱迁至更稳健隔离）；Mythos Preview 系统卡 0.01%/0.2%（二手引述）；RSP v3 不涉及沙箱；10 亿美元与 laude-institute/sandboxes（二手）。
3. Google DeepMind 与 xAI：GDM 只披露任务类别，产品侧有完整文档（Jules GCP VM、Gemini CLI 多档沙箱、GKE Agent Sandbox），AlphaEvolve 的评估级联（单个解最多约 100 compute-hours）；**"Gemini RL 跑在 Borg/gVisor 上"未核实，不写**；xAI 只披露算力与任务量（Grok 4 在 20 万 GPU 上做 RL；Grok 4.5 覆盖数十万任务，rollout 可持续数小时），由此推断沙箱有状态、寿命长。
4. Meta、NVIDIA、Microsoft、Mistral（CWM；Nemotron 3 Super 每 rollout 一个 Apptainer 容器、ProRL Agent、NeMo Gym、OpenShell；MAI-Thinking-1 二手引述、WAA、LiteBox；Mistral 改引 CoreWeave 发布稿客户原话）；Cursor（Composer 一手；Composer 2 报告：Firecracker pod、每集群数十万、每秒超过 500 个、文件系统 + 内存级 fork）与 Cognition（otterlink，数万台并发机器；训练共用为推断）；Perplexity SPACE（二手）。
5. 开源与工具链：Meta CWM（一手，3.5 万个镜像，每秒数万个代码片段）；NVIDIA NeMo Gym、ProRL Agent；OpenEnv；Prime Intellect（INTELLECT-3：gVisor、超过 4,000 个并发、每节点 256 个；2026-09 Sandboxes 改为 microVM，理由为保真度（厂商自报）；365,000 个预构建环境，原文未说是 Hub）；Harbor；DeepSWE/rLLM；训练器层（prime-rl、SkyRL、TRL、NeMo RL、Miles）。
6. **披露矩阵（海外）**与中外对照：中国公开训练侧，美国公开产品侧和事故复盘；27.9.5 本书建议：最小披露清单（七项）。

**核心材料**：ZenML 摘要（二手）；OpenAI 事故技术报告与 08-26 复盘；Anthropic 07-30 事故页与 08-31 整改文；Composer 2 报告 arXiv 2603.24477；INTELLECT-3 arXiv 2512.16144；Nemotron 3 Super arXiv 2604.12374；ProRL Agent arXiv 2603.18815；Cognition SWE-1.5；Grok 4.6 模型卡；CoreWeave 发布稿；Anthropic 工程博文；Gemini 2.5 报告 arXiv 2507.06261；AlphaEvolve 2506.13131；xAI Grok 4 与 4.5 新闻；CWM 2510.02387；NeMo Gym 文档；Prime Sandboxes；SemiAnalysis。

**图表建议**：**表 27-1"海外实验室披露矩阵"**（前五列与表 26-2 相同，另加事故复盘列）；**图 27-1"中外披露不对称象限图：训练侧透明度 × 产品侧透明度"**；表 27-2"开源生态三层：接口 / 任务生成 / 训练器"；表 27-3"已披露的训练侧隔离选择"；表 27-4 本章数字溯源。

**研究支撑**：中。**缺口**：GDM 与 xAI 的训练环境；OpenAI 演讲原视频（已有官方转录）；Gemini 3 技术报告没有细读；Mythos Preview 系统卡 0.01%/0.2% 所在段落（Opus 4.7 的 7.8% 已回原文）；MAI-Thinking-1 附录 F；Perplexity 一手博文；Anthropic 生产环境池规模；Research CaaS 事故后的 VM 技术；Terminal-Bench 2.1 修订数 26/28 冲突。

**交叉引用**：→ 第 4、6、15、16、17、18、19、20、21、22、23 章；第 24、25 章；第 26 章（对照：表 26-2、26.4.2 节 ROME 越界记录、26.12.3–26.12.4 节）。

---

## 第七部分　前沿

### 第 28 章　开放工程问题与研究议程
**核心问题**：哪些问题工业界已经明确碰到却没有解决？研究者从哪里切入最有杠杆？

**小节**
1. 八个趋势回顾：独立负载类别；存储取代原语成为竞争点；暂停是成本杠杆；rollout 状态外置；接口两层标准化；披露转向运维指标；Agent 自动化环境构建；竞争对手在底层开源协作。
2. 开放工程问题表（13 项）：可扩展放置；跨节点 fork 与在线迁移（冷恢复已有 AgentENV 文档披露，但缺少延迟与带宽数据）；抢占风暴下的暂停一致性；env.reset 可靠性；可写层去重；GUI 密度；GPU 沙箱；云上与嵌套虚拟化；网络策略的表达；reward hacking 的系统化检测；token 一致性；独立基准；可复现性。（第 6 章 6.8 节承诺的统一口径测量方案已在 28.6.2 节给出，与第 22 章 22.10.4 节一致；目前只有设计，没有测量结果）
3. 安全线研究方向（12 项）：跨层能力传递（把 CaMeL/FIDES 的标签编译成 seccomp、Landlock 和代理规则）；针对强原语的逃逸评测；失准 agent 遏制基准；外部副作用回滚；可验证的策略合成（AgentBound 自动策略准确率 80.9%）；出站与凭据；trust handoff；RL 沙箱的安全与吞吐权衡；computer-use 隔离；审批疲劳；语义防御的理论极限（arXiv 2605.17634）；独立基准加 TEE。
4. 合流议题：**遏制预算的联合优化**，即隔离强度、出站控制、单 episode 算力上限、轨迹监控放进同一个模型；不同隔离档位下 hacking 率的测量；三档网络模式的受控对照。
5. 学术社区信号：SOSP'26（YoloFS、SkVM、AgileLog、TensorHub；均见 SOSP'26 官方录用列表，2026-10-05 复核；AgileLog 已读 arXiv v1）、OSDI'26（RollArt）、AgenticOS@ASPLOS'26（7 篇研究 + 5 篇愿景）、ICML'26（SandboxEscapeBench Oral、SWE-MiniSandbox、Reward Hacking Benchmark）；2026 年多数工作仍是预印本。
6. 给研究者的切入清单：每个方向对应的"最小可发表实验"（推断，作者观点）。

**核心材料**：两份报告的开放问题表；arXiv 2512.01295（系统安全基础）；arXiv 2603.02277；AgenticOS 工作坊；pchaigno 的 SOSP'26 列表与 sigops.org 官方录用列表；arXiv 2605.17634；arXiv 2605.14932。

**图表建议**：表 28-1"开放工程问题（现状 / 证据 / 为什么难 / 相关章）"；表 28-2"研究议程：安全线（方向 / 核心问题 / 依据 / 切入点 / 相关章）"；图 28-1"遏制预算的几个维度（示意）"；表 28-3"2026 年相关工作的发表状态"；表 28-4"最小可发表实验（本书建议）"；表 28-5"本章数字溯源"。

**研究支撑**：强。**缺口**：OSDI'25、SOSP'25、ATC'25、EuroSys'26、NSDI'26 的程序没有系统扫描。

**交叉引用**：全书各章的"缺口"条目汇总到本章（归并关系见 28.2.1 节"归并说明"）。

---

## 附录规划

### 附录 A　术语表
- 约 150–200 条，中英对照，每条附"首次出现章号"。
- 分组：隔离原语（Seatbelt、bubblewrap、Landlock ABI、seccomp、gVisor Sentry、microVM、PVM、virtio-gpu）；存储（EROFS、overlayfs lowerdir/whiteout、OverlayBD/LSMT、ublk、3FS、DAX、SOCI）；状态（checkpoint、restore、fork、pack_diff、restack、statepoint、effect outbox、replay-or-fork）；密度（超售、DAMON、FPR、balloon、SCHED_IDLE、core scheduling、峰均比）；RL（rollout、env.reset、冗余 rollout、白盒/黑盒 harness、token-in/token-out、spurious parallelism）；安全（confused deputy、lethal trifecta、ASI10、trust handoff、取回型/篡改型 hacking、slopsquatting）。
- 固定译名，例如"出站（egress）""暂停/恢复""检查点"，全书统一使用。

### 附录 B　关键数字溯源表
- 每行一个字段：数字 | 原文表述与单位 | 来源（一手/二手/自报/逆向） | 日期 | 首次使用章 | 冲突项与处理方式。
- 必收的冲突与口径条目：AgentENV 超售 6.5×（K3 报告）与 9.6×（README c561be6，2026-08-10）；AgentENV fork 上限的文档与代码不一致（首版文档 16，代码 1–100，2026-08-24 文档更正；已解决）；检查点与恢复 <50/100 ms（README）与 133/49 ms（K3）；DSec 作者约 150 / 130+ / 100 多位；Manus 回收 14 天（2025-05）与 Free 7 / Pro 21 天（2026-01）；ACS 1.5 万/分钟与 10 万/分钟、冷启动 20–40 ms 与 P99 <180 ms、唤醒 1–10 s 与深度休眠 P99 <600 ms；**Kimi K2.5 的 100,000 是"并发 agent 任务"**，K2 的超过 10,000 是"并发沙箱实例"；腾讯 AGS"数万并发"与"数十万/分钟"；Terminal-Bench 241 与 89；CubeSandbox v0.5.0/v0.6.0 及 04-21/04-23；ACS 价格单位（已核，单位无误，C-07 已解决）；core scheduling 的"7.4 倍"（不采用）；ExploitGym 的 IM1 与二手报道的模型名、"5 月 8 日"（一手无对应）、"暂停 RL 两周"改为一手表述；E2B"累计 3,500 万美元"（有误，官方为 3,200 万美元）、"94% Fortune 100"（仅二手，官方 2025-07 为 88% 注册）；Modal 冷启动与价格（冲突）；Daytona 融资时间（冲突）。
- 会议状态列：RollArt OSDI'26；SWE-MiniSandbox ICML'26；SandboxEscapeBench ICML'26 Oral；Rollout Infrastructure Tax 为 SoCC'26 投稿预印本；YoloFS、SkVM、AgileLog 为 SOSP'26；Cordon 为 arXiv 2606.17573 预印本；其余 2026 年系统工作多为预印本。
- 约定每个版本更新一次，保留修订日志。

### 附录 C　各系统 API 对照
- 行：E2B、AgentENV（`aenv` 与 HTTP）、CubeSandbox、ACS、腾讯 AGS、OpenSandbox、DSec libdsec、GKE agent-sandbox CRD、Modal、Daytona、Prime Sandboxes、OpenEnv、Harbor、Inspect Sandboxing、OpenAI Agents SDK（Manifest / 沙箱接口）。
- 实际结构：表 C-1 生命周期与状态、表 C-2 网络、凭据、I/O 与集成（网络策略拆为"粒度与默认""运行中修改与分阶段"两列）、表 C-3 对表 16-2 的覆盖；15 个系统，225 格。
- 列：create / exec / 文件 / pause-resume / snapshot / fork / 网络策略（粒度、阶段化）/ 后端选择 / TTL / 凭据注入 / 流式 I/O / MCP 支持。
- 附"训练场景缺失概念"标注列，与第 16 章表 16-2 对应。材料不足的格子写"文档未见"，不推测。

### 附录 D　负载刻画模板
- 以 DSec 表 2/3 与七特征为范本，给出可填写的模板：请求突发（单作业峰值、创建速率）、CPU/内存利用分布（均值、p90、峰均比）、寿命分布（中位、p99）、镜像统计（基础镜像数、workspace/toolkit 数、总量、访问比例、扇出中位与 p90）、可中断性（抢占频率、暂停占比）、故障率（env.reset 失败、超时、环境变量损坏）、网络需求（阶段、域名类别）。
- 附三份已填示例：DSec（最完整，48 格中已填 22 格）、AgentENV/K3（部分，已填 11 格）、快手/RollArt（故障组，14 格中已填 11 格），空格保留为"未披露"。
- 附产品侧与 GUI 负载的建议字段（会话时长、空闲比、reset 延迟、GPU 渲染占比），共 16 个字段（产品侧 8、GUI 8），据本书检索所及均无公开分布数据。

### 附录 E　文献库
- 按章组织，每条标注核验级别 [V] / [V*] / [K] / [U]（沿用补充调研的约定）和发表状态（会议、期刊、预印本、厂商博客）。
- 分区：经典 serverless 与虚拟化（Firecracker、SOCK、SAND、Catalyzer、REAP、FaaSnap、SEUSS、Groundhog、Nephele、Medes、RunD、PVM、Unikraft、DADI、Slacker、TrEnv、CXLfork 等，**作者与 DOI 待在 dblp/ACM 抽查**）；2025–2026 Agent 沙箱系统；RL 基础设施与技术报告；安全防御五类路线；评测与事件；标准与市场；厂商文档与博客（注明营销属性）。
- 附"待读清单"：Anthropic 一手事故页、OpenAI 演讲原视频（Cordon 正文、TC260 附件已于 2026-10-05 读到，见第 12、23 章；CUA-Sandbox 全文、AgileLog v1 正文、OpenAI 演讲官方转录已于 2026-10-06 读到，见第 7、11、27、28 章）。

---

## 写作顺序、篇幅与总字数

### 样章建议（先写三章）
1. **第 24 章 DeepSeek DSec**：一手材料最完整（全文可引、数字齐全），能最快检验"八层拆解 + 数字溯源"的案例写法，写完后第 3、9–15 章可以直接从中抽取机制段落。风险最低，展示价值最高。
2. **第 11 章 沙箱内状态**：这是第二主线的起点，材料横跨经典 serverless、工业（DSec、AgentENV、OpenAI、Replit）和 2026 年的新系统（DeltaBox、Crab、BranchFS、YoloFS），最能体现本书"学术源流 + 工业实现 + 前沿"三段式写法和"谱系"边栏的效果，也会逼出三层框架图（图 11-1）的定稿。
3. **第 19 章 训练期 reward hacking 与遏制**：它是安全线与基础设施线合流的地方，也是本书与现有综述差异最大的一章；证据表已基本齐备（DSec、Cursor、METR、ImpossibleBench、OpenAI 一手复盘），能检验"取回型/篡改型 × 五层通道"框架是否站得住。

之后建议的顺序：第 3 章（负载）→ 第 9、10、13 章（与第 24 章同源，边际成本低）→ 第 25 章（与第 24 章成对）→ 第 14、15 章 → 第 17、18、20 章 → 第 4–8 章（原语部分资料成熟，可以并行，也可以交给合作者）→ 第 21、26、27 章（等补充调研缺口）→ 第 22、23 章（等 TC260 定稿等外部事件）→ 第 12 章（等 Cordon 等正文）→ 第 1、2、28 章最后写（总论与议程依赖全书结论）→ 附录 B 从第一章起同步维护。

### 各章预估篇幅（汉字）

| 章 | 预估字数 | 章 | 预估字数 |
|---|---|---|---|
| 1 | 12,000 | 15 | 13,000 |
| 2 | 14,000 | 16 | 14,000 |
| 3 | 14,000 | 17 | 18,000 |
| 4 | 15,000 | 18 | 13,000 |
| 5 | 13,000 | 19 | 18,000 |
| 6 | 15,000 | 20 | 15,000 |
| 7 | 18,000 | 21 | 18,000 |
| 8 | 11,000 | 22 | 15,000 |
| 9 | 16,000 | 23 | 11,000 |
| 10 | 18,000 | 24 | 22,000 |
| 11 | 20,000 | 25 | 18,000 |
| 12 | 14,000 | 26 | 18,000 |
| 13 | 16,000 | 27 | 15,000 |
| 14 | 16,000 | 28 | 15,000 |

- 正文 28 章合计约 **435,000 字**。
- 附录：A 约 15,000；B 约 20,000（以表为主）；C 约 12,000；D 约 8,000；E 约 30,000（文献条目）；合计约 **85,000 字**。
- 前言、导读、索引约 **10,000 字**。
- **全书预估约 53 万字**（其中表格约占 15–20%）。若出版方要求控制在 40 万字以内，优先压缩第 4–8 章（引用安全综述、缩写到原语对照）和附录 E（改为在线文献库）。

### 写作纪律（贯穿全书）
- 每个数字首次出现时标注来源类型，并登记进附录 B；冲突一律并列，不二选一。
- 2026 年的系统论文必须标注"预印本 / 投稿 / 已录用"。
- 谱系线每次出现都要写"推断"；DSec 只能写"使用了 AgentENV 中开源的存储组件"，不能写"基于 AgentENV"。
- "未披露"是结论，不是空白：披露矩阵中不许用推测填格。
