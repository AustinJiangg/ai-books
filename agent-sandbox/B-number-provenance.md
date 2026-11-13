# 附录 B　关键数字溯源表

> 版本：2026-09-30 初版，2026-10-06 修订（见文末版本说明）。整理范围：本书各章引用的关键数字，来源为论文与技术报告、厂商文档与博客、开源仓库、媒体报道和标准文本。**本表只登记这些来源中已有的数字，不新增任何数字**；凡"笔者推算"均由表内已引用数字推出，并注明推算式。
>
> **章号**："使用章节"一列按本书 28 章的章号填写；"附录 C""附录 D"表示该数字在相应附录中使用。
>
> **优先级**：同一事实有多个来源时，以一手来源和较晚的回原文核对结果为准（例如 RollArt 属 OSDI'26、GLM-5 的"1 万+"已一手确认、ExploitGym 以 OpenAI 一手复盘为准、K2.5 的 10 万是"任务"）。
>
> **来源类型**：论文自述＝论文/技术报告中作者对自身系统的陈述；厂商自报＝厂商官网、文档、营销文或客户案例，未经独立测试；一手文档＝当事方官方文档/博客/仓库/标准文本（非营销性描述）或当事方事故复盘；二手报道＝媒体、竞品、聚合博客、Wikipedia、第三方逆向；二手引述＝一手文件存在，但本书只能经第三方转引原句（如 PDF 文本提取不全），区别于第三方自己的叙述；笔者推算＝由表内数字推导。
>
> **可信度**：高＝一手来源逐字或近逐字、无冲突；中＝厂商自报/营销、摘要式读取转述、或存在需按日期并列的冲突；低＝仅二手/聚合/Wikipedia、背景知识（[K]，未回原文核实）、疑似解析错误或自相矛盾。
>
> **引用约定**：书中引用中、低可信度数字时，应在正文写明"据××自报""据××报道"及日期；引用存在冲突的数字时，按"冲突数字登记"一节的建议措辞。

## 目录

- [第一部分　定义与问题（第 1–3 章）](#第一部分定义与问题)
- [第二部分　隔离原语（第 4–8 章）](#第二部分隔离原语)
- [第三部分　八层架构（第 9–16 章）](#第三部分工业级沙箱的八层架构)
- [第四部分　沙箱与 Agent RL（第 17–20 章）](#第四部分沙箱与-agent-rl)
- [第五部分　产品与产业（第 21–23 章）](#第五部分产品与产业)
- [第六部分　案例研究（第 24–27 章）](#第六部分案例研究)
- [第七部分　前沿（第 28 章）](#第七部分前沿)
- [附录专用数字（附录 C）](#附录专用数字)
- [冲突数字登记](#冲突数字登记)
- [不应引用的数字](#不应引用的数字)
- [参考链接](#参考链接)

---

## 第一部分　定义与问题

### 第 1 章　什么是 Agent 沙箱（三场景）

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B01-01 | 峰值约 2 万并发（20,000 concurrent） | 产品侧峰值并发沙箱 | Lovable（Modal 页面转述） | [Modal：Best sandboxes for RL environments][modal-rl] | 二手报道（竞品转述） | 2026-07 | 中 | 属 Modal 营销页对客户的描述；条件为"48 小时促销周末"期间的峰值（"Lovable reached up to 20,000 concurrent Sandboxes at peak during a 48-hour promotional weekend"）；2026-10-05 第 1 章复核原句一致 | 1, 21, 22, 附录 D |
| B01-02 | "几百个 trial"一批 | 评测场景典型批量 | OpenSandbox 社区用例 | [阿里云开发者社区 OpenSandbox 文章][aliyun-osb] | 厂商自报 | 2026-09-11（抓取所示发布日期，可能为更新日期） | 中 | 无具体吞吐数字；未能回原文核实（正文标"未核实"） | 1, 20 |
| B01-03 | 三天 | 讲者用 Codex goal mode 运行任务的个人最长记录（不是产品参数） | OpenAI（工程师演讲） | [AI Engineer 官方转录](https://ai.engineer/talks/OqM67QG_Ikk-from-fork-fleet-designing-agent-sandbox-cloud) | 一手（主办方转录） | 2026 | 中 | 原话："how many of you have used goal mode in Codex…"；"I think three days is my record for running, uh, uh, something."；ZenML 误作 "gold mode"；转录未说明是否人工校对，原视频未看 | 3, 27 |
| B01-04 | 12.5% | Terminal-Bench 诊断中的"环境退出率" | Terminal Agents 综述 | [Terminal Agents: A Survey, arXiv 2608.20485][termsurvey] | 论文自述 | 2026-08 | 中 | LLM 摘要式读取，表格需手工核对；综述把环境列为评测混杂因素 | 20 |
| B01-05 | "Research contexts prioritize throughput, requiring many parallel rollouts for training optimization. Production contexts prioritize latency, demanding sub-second execution for responsive user experiences."（非数字，登记为引语附注） | OpenAI 工程师演讲对训练与产品取舍的表述 | OpenAI（Bhardwaj 演讲） | [Sean Weldon 笔记](https://www.sean-weldon.com/blog/2026-07-17-from-fork-to-fleet-designing-an-agent-sandbox-cloud-abhishek-bhardwaj-openai)；[ZenML 摘要][zenml] | 二手报道 | 2026-07-17 | 中 | ZenML 相近原句："In research, throughput is paramount—running many training loops at scale with many rollouts in parallel."；"In product, latency dominates."（2026-10-05 复核）。两份转录均未写"底座都是 microVM"，该说法为本书推断，不应作引语（X-45，另见 X-44）；原视频未核实 | 1, 27 |
| B01-06 | 4 类（serverless：SAND、REAP、TrEnv、RunD；推理侧：OpenAI Code Interpreter、E2B、Kimi-K2.5 Agent Swarm；训练侧：MiMo-V2-Flash、ComputerRL；RL 框架：slime、veRL、OpenRLHF、Seer） | DSec 相关工作对已有系统的划分（非数字，登记为分类附注） | DSec | [DSec §9][dsec] | 论文自述 | 2026-09-19 | 高 | 位于 §9（相关工作），不在 §1–2；原句："They treat the execution environment as a black box, assuming that sandboxes are available and correctly configured."；"Agentic training instead uses long-lived, stateful sandboxes drawn from an image corpus that exceeds single-node storage and has low per-image fanout."（2026-10-05 复核） | 1, 3, 10, 24 |
| B01-07 | v1 2026-07-27；v2 2026-08-07；摘要"million-token agentic RL with persistent rollout and sandbox states" | Kimi K3 技术报告版本日期与摘要中的沙箱表述 | Kimi K3 | [arXiv 2607.24653](https://arxiv.org/abs/2607.24653) | 一手文档 | 2026-08-07 | 高 | 2026-10-05 读取摘要页 | 1, 25 |
| B01-08 | 2026-09-11；"Each rollout runs in a dedicated sandbox with its own runtime." | HF 博文日期；博文转引 Liquid AI 对 LFM2.5 训练的描述 | Liquid AI（经 HF） | [HF 博文][hf-rl] | 二手引述 | 2026-09-11 | 中 | 不是 HF 作者对标题 *One sandbox per rollout* 的释义；Liquid AI 原文未读 | 1, 17 |

### 第 2 章　两类对手

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B02-01 | "95% of attacks" | 护栏产品宣称拦截率；Willison 认为 95% 在安全意义上仍是失败 | Simon Willison（lethal trifecta） | [The lethal trifecta][willison] | 一手文档（作者博客） | 2025-06-16 | 高 | 95% 是被批评的厂商说法，不是实测；原文："they'll almost always carry confident claims that they capture "95% of attacks" or similar... but in web application security 95% is very much a failing grade"（2026-10-05 复核） | 2, 14 |
| B02-02 | 2025-12-09；100+ 贡献者；ASI01–ASI10 | OWASP Agentic Top 10 2026 发布日期、贡献者数、条目数 | OWASP GenAI | [OWASP Top 10 for Agentic Applications 2026][owasp] | 一手文档 | 2025-12-09 | 高 | 条目名称已由 OWASP PDF（genai.owasp.org/download/52117）经抓取确认（2026-10-05）；ASI05 原文："Never run as root. Run code in sandboxed containers with strict limits including network access"；ASI10 定义原文："Rogue Agents are malicious or compromised AI Agents that deviate from their intended function or authorized scope…creating a containment gap for traditional rule-based systems" | 2, 23 |
| B02-03 | 1,206 条高管记录；1,196+ 条公司资料；连续九天；（二手）4,000 条虚构人物记录 | Replit/SaaStr 删库事件 | Replit Agent | [Lemkin，SaaStr 官网](https://www.saastr.com/replits-new-release-address-most-of-the-challenges-we-hit-vibe-coding-but-is-prosumer-vibe-coding-really-ready-for-commercial-apps-yet)（2025-08-02）；[The Register](https://www.theregister.com/2025/07/21/replit_saastr_vibe_coding_incident/)（2025-07-21，4,000 条） | 一手文档（4,000 条为二手） | 2025-08-02 | 高 | 原文："After nine mad days of us vibe coding, Replit's AI Agent deleted a production database containing 1,206 executive records and 1,196+ company profiles…"；"12 天试验"只见于 Business Insider（2025-07-22，二手），当事人原文只说"nine mad days"，正文不用（X-49、C-58）；4,000 条为 The Register 转引 Lemkin 帖子，原文是"虚构人物"数据库，与删库孰先孰后未交代；vectara/Slashdot 不再作主来源；合法权限误用案例，不是沙箱逃逸 | 2, 12, 21 |
| B02-04 | 250,000+ 次攻击；400+ 参与者；13 个前沿模型；每个目标至少被攻破一次 | 大规模 Agent 红队比赛 | NIST CAISI、UK AISI、Gray Swan | [NIST CAISI 博客][nist-comp] | 一手文档 | 2026-03-23 | 高 | 2026-10-05 复核原文："Across more than 250,000 attack attempts from over 400 participants"；"at least one successful attack was found against all of the target frontier models"；另有"universal"攻击族"often able to transfer across scenarios and models" | 2, 20, 23 |
| B02-05 | 77% vs 84% | AgentDojo 上"可证明安全"完成率 vs 无防御 | CaMeL | [CaMeL, arXiv 2503.18813][camel] | 论文自述 | v1 2025-03-24，v2 2025-06-24（SaTML 2026 据附录 E，未回原文核对） | 高 | 常被引用的效用代价；摘要原文："solving 77% of tasks with provable security (compared to 84% with an undefended system) in AgentDojo"（2026-10-05 复核）；效用代价 7 个百分点为笔者推算（B02-14） | 2, 28 |
| B02-06 | 最多 57% | 保留的前沿模型性能（摘要："up to 57% of the performance of frontier models"，未写基准名；OSWorld 待正文核对） | NOVA（CaMeLs Can Use Computers Too） | [arXiv 2601.09923][nova] | 论文自述 | 2026-01 | 高 | 仍存在 Branch Steering 攻击 | 2, 7 |
| B02-07 | "四分之三被测查询开销低于 30%" | 执行隔离架构开销 | IsolateGPT/SecGPT | [arXiv 2403.04960][isolategpt] | 论文自述 | 2024-03（NDSS 2025） | 高 | ACE 展示了能攻破它的新攻击 | 2 |
| B02-08 | ASR 41.2% → 2.2% | AgentDojo 攻击成功率降幅 | Progent（早期版本） | [Progent, arXiv 2504.11703][progent] | 论文自述 | 2025-04 | 低 | [K] 背景知识，未核实 | 2 |
| B02-09 | 中位 53 ms；宽松策略下社工成功 74.6% vs 限制策略 879 次中 0% | 工具调用前授权延迟与效果 | Open Agent Passport（OAP） | [arXiv 2603.20953][oap] | 论文自述 | 2026-03 | 中 | 单作者规范论文，未同行评审 | 2, 16 |
| B02-10 | 72% | 含明确思维链理由（explicit chain-of-thought rationale）的 reward hacking episode 比例；§6.4 口径限于暴露推理轨迹的模型 | Reward Hacking Benchmark | [arXiv 2605.02964][rhb] | 论文自述 | 2026-05-03 | 高 | 见 B19 组；摘要原文："72% of reward hacking episodes include explicit chain-of-thought rationale, suggesting models often frame exploits as legitimate problem-solving"（2026-10-05 回 arXiv 摘要页再次确认）；§6.4："For models exposing explicit reasoning traces, 72% of exploit episodes include an explicit rationale"。原文不是"在 CoT 中陈述作弊动机"，也不是"explicit reasoning"（X-46）；作者另提醒 reward hacking 可能不被说出口（"Absence ≠ Innocence"，§6.4）（2026-10-05 已回原文核对） | 2, 19 |
| B02-11 | 2025-06；2025-07；2025-12-29；约 2026-04；2026-06-13；2026-08-12；2026-08-23 至 24 | Manus 迁新加坡、关停中国业务、Meta 宣布收购、北京要求解除、Meta 切断系统访问、Manus 宣布恢复独立运营、删除收购日及之后的部分用户数据 | Manus / Meta | [Rest of World][row-manus]；[CNBC][cnbc-manus]；[TNW][tnw-manus]；[TechCrunch][tc-manus]；Caixin Global（见 B21-20） | 二手报道 | 见左 | 中 | 与沙箱基础设施去向的关系未披露；2026-06：TechCrunch 原文为"Meta has cut Manus off from its internal systems"并阻止员工在内部项目中使用 Manus 工具；"停止数据共享"出自 Bloomberg（经 ppc.land 转述） | 21, 26 |
| B02-12 | 6 个 agentic 评测；5 个模型；"over 85% of follow-up questions" | Apollo in-context scheming 评测环境数；表现出谋划能力的模型数（o1、Claude 3.5 Sonnet、Claude 3 Opus、Gemini 1.5 Pro、Llama 3.1 405B）；o1 在追问中保持欺骗的比例 | Apollo Research | [arXiv 2412.04984](https://arxiv.org/abs/2412.04984) | 论文自述 | v1 2024-12-06；v2 2025-01-14 | 高 | 目标由研究者在上下文中给定并要求"strongly follow"；另有少数只给目标即出现谋划的情形；2026-10-05 复核摘要页 | 2, 19 |
| B02-13 | v1 2023-12-12；v5 2024-07-23；GPT-4（不可信）/ GPT-3.5（可信） | AI control 论文版本与实验设定 | Redwood Research | [arXiv 2312.06942](https://arxiv.org/abs/2312.06942) | 论文自述 | 2023-12-12 | 高 | Comments 原文"ICML version"链接 OpenReview（openreview.net/pdf?id=KviM5k8pcP），未说 v5 即 ICML 版本；论文研究 trusted editing、untrusted monitoring 等协议，未讨论沙箱；"沙箱是硬底线"为本书引申（推断） | 2, 19, 28 |
| B02-14 | 7 个百分点 | CaMeL 相对无防御系统的效用代价 | CaMeL | 84% − 77%（B02-05） | 笔者推算 | — | — | — | 2 |

### 第 3 章　Agent 负载刻画

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B03-01 | 最多 32K 个沙箱实例（up to 32K） | 单个 RL 作业的突发请求上限 | DSec | [DSec 论文 arXiv 2609.22978][dsec] | 论文自述 | 2026-09-19 | 高 | 钜亨网（2026-09-24）标题作"單一任[務]曾啟動3.2萬個沙盒"、正文作"單一訓練任務最多曾一次啟動3.2萬個"（二手报道，2026-10-06 读取），量级与原文一致，但把"可能请求多达"写成了"曾启动"；"32K"未必恰为 32,000 | 1, 3, 24, 28, 附录 D |
| B03-02 | 典型容器任务"数千个"，尾部"数万个" | 单任务创建沙箱数分布 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 图 2 分布未能以文本取得 | 3, 24, 附录 D |
| B03-03 | 约 90% 沙箱平均 ≤ 请求 CPU 的 5% | CPU 稀疏性（容器与 microVM 均如此） | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 第一财经亦引用；等价于 p90 约 5%（笔者改写，附录 D） | 1, 3, 13, 24, 附录 D |
| B03-04 | 容器中位寿命 17.4 分钟；microVM 15.5 分钟；p99 均 > 3 小时 | 沙箱寿命 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 图 7 位于 §4.3（非 §4.1） | 1, 3, 11, 24, 附录 D |
| B03-05 | 11,266 基础镜像；102,171 workspace；82.8 TB（容器）；2 基础镜像、53,590 workspace、4,889 快照、50.9 TB（microVM） | 一周生产制品（表 2），2026 年初 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19（数据 2026 年初） | 高 | 媒体"PB 级"有 §2.4 依据（指管理的层与镜像总量，B24-13），与本行一周制品口径不同，见 C-15 | 1, 3, 10, 24, 附录 D |
| B03-06 | 103 个活跃 toolkit；67.8% 的沙箱需要至少一个 workspace 或 toolkit | 可组合层需求 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 3, 10, 24, 附录 D |
| B03-07 | 超过 130 TB | 一周活跃制品总量 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | "远超单节点存储能力" | 1, 3, 10, 24, 附录 D |
| B03-08 | 容器扇出中位数 3、p90 28；microVM 中位数 1、p90 3 | 每任务镜像扇出 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 不宜与 K3 平均每镜像约 34 个沙箱直接比较（B25-06） | 1, 3, 10, 24, 附录 D |
| B03-09 | C++ 8.7%/4.9 GB；Go 13.3%/4.1 GB；Java 9.2%/12.1 GB；JavaScript 4.2%/9.6 GB；Python 6.0%/6.0 GB | 运行时实际访问数据比例/镜像大小（表 3） | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | Dataconomy"不到 10%"为简化，Go 为 13.3%（C-15） | 1, 3, 10, 24, 28, 附录 D |
| B03-10 | 最多占沙箱寿命的 98% | Agent 等待模型推理的时间占比 | Kimi K3 / AgentENV | [Kimi K3 技术报告 arXiv 2607.24653][k3] | 论文自述 | 2026-07 | 高 | 暂停经济学的核心依据；K3 §4.1.2 另称部分 rollout 跨迭代恢复由沙箱基础设施支撑，暂停不只服务于推理等待 | 1, 3, 11, 13, 25, 28, 附录 D |
| B03-11 | 56–74%（AgenticOS'26 PDF）；55–60%（arXiv 2602.09345v3 摘要） | OS 层执行（工具 + 初始化）占端到端延迟 | AgentCgroup | [AgentCgroup（AgenticOS'26 论文 10）][agentcgroup]；[arXiv 2602.09345][agentcgroup-arxiv] | 论文自述 | 2026-03-23（PDF）/ 2026-07-22（v3） | 高 | 两个版本数字不同（版本差异，口径相同），并列引用，见 C-21；按单一版本推算的非 OS 执行占比：v3 为 40–45%，PDF 为 26–44%；合并区间见 B03-23 | 3, 13 |
| B03-12 | 峰均比最高 15.4×（单任务极值：峰值 4,060 MB、均值 264 MB）；云负载对照：Azure Functions 近乎平坦，Azure VM 在 2–3× 以内，Google Autopilot 推荐值在实际峰值 2× 以内 | 内存峰均比 | AgentCgroup | [AgentCgroup][agentcgroup] | 论文自述 | 2026-03-23 | 高 | 内存而非 CPU 限制并发；15.4× 为单任务极值（v3：pydicom/pydicom#2022），摘要写作 "up to"，不宜作典型值；"1.5–3×"在两个版本中均无出处；云负载对照原文 "Azure Functions exhibit near-flat memory, Azure VMs stay within 2–3×, and Google Autopilot recommends within 2× of actual peaks"（v3 §4.1，PDF 同句）；15.4× 为 AgentCgroup 单任务受控测量极值，不是训练集群实测；DSec 未给出峰均比；2026-10-06 回 PDF 复核：原文为"Azure VMs stay within 2–3×"，与本行"2–3×"（正文写"2–3 倍"）一致，无需修改 | 1, 3, 13, 附录 D |
| B03-13 | 框架基线约 185 MB；工具调用突发 500 MB–2 GB、持续 1–2 秒；峰值 2–4 GB；任务间峰值 197 MB–4 GB（约 20×）；重跑 402/222/259 s（1.8×） | 内存需求刻画 | AgentCgroup | [AgentCgroup][agentcgroup] | 论文自述 | 2026-03-23 | 高 | "20×"：v3 §3.4 有 "Resource demands vary 20× across tasks"，另一次读取所见文本只见 197 MB–4 GB，引用 20× 时可注"4,000 ÷ 197 ≈ 20"；1.8× 在 v3 §3.4 实测中指同一任务三次运行的执行时间（iterative/dvc#777：402/222/259 s），摘要与 §4.3 概括为资源需求差异，不是版本差异 | 3, 13 |
| B03-14 | 超过 75% 的轮次不产生需恢复的状态 | 检查点必要性 | Crab | [Crab, arXiv 2604.28138][crab] | 论文自述 | 2026-04-30 | 高 | — | 3, 11 |
| B03-15 | "tens of thousands of sandboxes, each with a unique set of images, may need to be created within seconds" | 训练负载突发与低扇出（定性量级） | Kimi K3 / AgentENV | [Kimi K3 技术报告 §5.3.2][k3] | 论文自述 | 2026-07 | 高 | PDF 逐字核对；第 10 章同引（原拟 B10-27，已并入本行） | 3, 9, 10, 25, 附录 D |
| B03-16 | Haiku 4.5 13.2%；GLM-4.7-Flash 7.6% | Agent 平均 CPU 利用率，以单核为 100%（"normalized to one core, i.e., 100% = one fully utilized core"） | AgentCgroup | [arXiv 2602.09345v3 §3.3][agentcgroup-arxiv]；[PDF][agentcgroup] 同句 | 论文自述 | 2026-03-23（PDF）/ 2026-07-22（v3） | 高 | 与 DSec"占请求值比例"口径不同，不可直接比较（第 13 章原拟 B13-16，已并入本行） | 3, 13, 附录 D |
| B03-17 | 144 个 SWE-rebench 任务；Claude Haiku 4.5（云 API）与 GLM-4.7-Flash（本地 GPU）；每任务一个 Podman 容器，不设资源限制 | AgentCgroup 实验条件 | AgentCgroup | [arXiv 2602.09345][agentcgroup-arxiv] | 论文自述 | 2026-02-10（v1）/ 2026-07-22（v3） | 高 | 引用 B03-11 至 B03-13 时应同时注明；是否串行执行原文未说明 | 3, 13 |
| B03-18 | 366 s（图 3 题注 365.7 s）；生成 54%、训练 23%、环境初始化 15%；超时迭代 513 s | RL 迭代时间分解（正常与超时迭代） | RollArt（阿里） | [RollArt arXiv 2512.22560v2 §3.1，图 3][rollart] | 论文自述 | 2026-06-15（v2） | 高 | 迭代级口径，不是沙箱级 | 3, 9, 17, 附录 D |
| B03-19 | "no more than ten heavy-tailed initialization events occur among hundreds of thousands of resets" | 缓存后的 env.reset 长尾事件数 | RollArt（阿里） | [RollArt v2 §8][rollart] | 论文自述 | 2026-06-15 | 高 | 与 B10-14 配合使用 | 3, 10, 17, 附录 D |
| B03-20 | SWE-bench 30–50 轮；GEM-math < 5 轮 | 不同环境的交互轮数 | RollArt | [RollArt 表 1（§2.1）][rollart] | 论文自述 | 2025-12 | 高 | 与 B17-04 互见 | 3, 17, 附录 D |
| B03-21 | Terminal-Bench：Claude Code 5%（文件系统）/ 8%（完整）；iFlow CLI 25% / 5%；SWE-bench 约 25% / 近 0 | 需要检查点的轮次比例 | Crab（港科大） | [arXiv 2604.28138 §7.2，图 13][crab] | 论文自述 | 2026-04-30 | 高 | 评测规模：每基准 100 个任务、3 种 Agent-LLM 组合（表 3）、2,063 个人工标注轮次（表 4） | 3, 11 |
| B03-22 | "several kernel panics and deadlocks caused by unintended agent operations" | 早期容器沙箱实验中的故障（定性） | Kimi K3 | [Kimi K3 技术报告 §5.3.2][k3] | 论文自述 | 2026-07 | 高 | "执行不可信"转化为"不可靠"的一手证据 | 2, 3, 19, 附录 D |
| B03-23 | 40–45%（v3）；26–44%（PDF）；合并 26–45% | 非 OS 执行时间占端到端时延 | AgentCgroup | 由 B03-11 推算 | 笔者推算 | 2026-10 | 中 | 跨版本合并区间须注明 | 3 |
| B03-24 | 约 50× | 等待占比 98% 时的理想时间复用上界（1 ÷ (1 − 98%)） | Kimi K3 / AgentENV | 由 B03-10 推算 | 笔者推算 | 2026-10 | 中 | 忽略暂停开销与活跃时段重叠；对照实际 6.5×（K3，归因写时复制与页缓存）/ 9.6×（README，归因内存气球），见 C-01 | 3, 13 |
| B03-25 | 约 9× | DSec 容器扇出 p90 与中位数之比（28 ÷ 3） | DSec | 由 B03-08 推算 | 笔者推算 | 2026-10 | 中 | 说明扇出分布右偏 | 3 |
| B03-26 | 每基准 100 个任务；3 种 Agent-LLM 组合；2,063 个人工标注轮次 | Crab 评测规模；用于检验分类准确率的人工标注轮次数 | Crab | [Crab arXiv 2604.28138][crab]（表 3、表 4） | 论文自述 | 2026-04-30（v1） | 高 | 第 3 章回 v1 HTML 复核 | 3 |

---

## 第二部分　隔离原语

### 第 4 章　OS 原生原语

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B04-01 | 权限提示减少 84%；用户此前批准约 93% 的提示 | 沙箱对审批疲劳的作用 | Claude Code | [Anthropic：How we contain Claude][anthropic-contain] | 一手文档 | 2026-05-25（06-06 修订） | 高 | 另有转述称 84% 出自 2025-10 sandboxing 博文（未核实）；以 2026-05 博文为准 | 4, 14, 21, 28 |
| B04-02 | 83% | auto mode 捕获的"过度积极动作"比例 | Anthropic | [How we contain Claude][anthropic-contain] | 一手文档 | 2026-05-25 | 高 | — | 4, 21 |
| B04-03 | npm 最新版 0.0.78（2026-09-30）；0.0.64 发布于 2026-07-07 | sandbox-runtime（srt）最新发布版本（npm registry），状态为"Beta Research Preview" | Anthropic srt | [sandbox-runtime README][srt]；npm registry `@anthropic-ai/sandbox-runtime` | 一手文档 | 2026-10-03 读取 | 高 | 此前记"v0.0.64"为当时所见版本；GitHub Releases 页 403，未能核对是否仍停在 v0.0.64；README（HEAD c7adb1e，2026-10-03；2026-10-04 复读 HEAD e025055）已含解析后地址检查、实验性 TLS 终止、Windows（alpha：srt-sandbox 专用账户 + 受限令牌 + job object + WFP + NTFS ACL）；Linux 上尚不存在的强制拒写路径亦被拦截（早先"只覆盖已存在文件"的说法已过时） | 4, 14 |
| B04-04 | 2025-10-20 上线；2026-03-27 srt 修复、2026-03-31 Claude Code 2.1.88；2026-04-03 HackerOne 报告；研究者称漏洞持续到 4 月发布的 2.1.90 | SOCKS5 空字节白名单绕过时间线；无 CVE | Claude Code | [SecurityWeek][securityweek] | 二手报道 | 2026 | 中 | 结束版本两说并列：Anthropic 称 2.1.88（2026-03-31），研究者称 2.1.90（4 月）；同见 SecurityWeek 2026-05-20 | 4, 14 |
| B04-05 | CVE-2026-48124（Cursor < 3.0.0；CVSS 8.5；2026-06-15 发布）；Cursor git fsmonitor 3.0.0 修复（CVE 待分配）；Cursor virtualenv 3.1.2 修复（CSA，二手）；Codex git show v0.95.0 修复；Docker socket：仅 Cursor 修复（GHSA-v4xv-rqh3-w9mc），OpenAI 定为 informational，Google 不修 | 沙箱内写、沙箱外受信任工具执行的漏洞类（"trust handoff"一名出自 CSA 研究笔记标题，2026-07-22（不是 OpenAI/HF 那篇，该篇无此词；见附录 E C04-16）；BleepingComputer 与 Pillar 原文均未用此词） | Pillar Security 披露 | [BleepingComputer][bleeping]；[Pillar Security 原文](https://www.pillar.security/blog/one-docker-socket-to-rule-them-all-escaping-codex-cursor-and-gemini-clis-sandboxes) | 二手报道 | 2026-07-20 | 中 | Pillar 原分类为 7 项发现、4 种失效模式（见 B04-18）；BleepingComputer 称 Docker socket"已修复"，与 Pillar 原文不符 | 4, 5, 14 |
| B04-06 | CVSS 10.0 | Gemini CLI CI RCE | Gemini CLI | [The Hacker News 2026-04][thn-gemini] | 二手报道 | 2026-04-30 | 低 | headless/CI 模式下配置文件在显式信任工作区前被读取执行；修复 Gemini CLI 0.39.1、run-gemini-cli 0.1.22；与 CVE-2025-59536 同属项目配置先于信任执行一类 | 4 |
| B04-07 | ABI 1（5.13）、2（5.19）、3（6.2）、4（6.7）、5（6.10）、6（6.12）、7（6.15）、8（7.0）、9（7.1）、10（7.2）、11（7.3，开发中） | Landlock ABI 演进 | Linux 内核 | [kernel Landlock 文档][landlock]；torvalds/linux `security/landlock/syscalls.c` 各 tag 的 ABI 版本常量 https://github.com/torvalds/linux/blob/master/security/landlock/syscalls.c | 一手文档 | 2026-09 抓取 | 高 | 已逐 tag 读取（v6.16–v6.19 仍为 7；master 为 7.3-rc6，2026-10-04）；docs.kernel.org 页面日期 2026 年 8 月；文档列明 chdir、stat、flock、chmod、chown、setxattr、utime、fcntl、access 等仍不可限 | 4 |
| B04-08 | 1,000 个克隆 718 ms；每个约 4 KB | 进程级 CoW fork 性能 | Sandlock | [multikernel.io][sandlock] | 厂商自报 | 2026-03-19 | 中 | 其对容器（约 200 s、2 GB）与 microVM（约 150 s、2 GB）的对比数字疑似稻草人，不应引用；要求 Linux 5.13+、Python 3.10+；"无需 root、cgroup、容器运行时或 CRIU"；每克隆约 4 KB 为 fork 时刻开销，写入后 CoW 复制另计（推断）；博客称目标场景包括 RL rollout、Agent 工具执行与代码评测 | 4, 11 |
| B04-09 | 三种模式（read-only / workspace-write / danger-full-access） | Codex CLI 沙箱模式 | OpenAI Codex CLI | [Codex sandboxing 文档][codex-sandbox] | 一手文档 | 2026 | 高 | 冲突已由仓库文档解决：openai/codex `codex-rs/linux-sandbox/README.md`（main，2026-10-04）写明 bubblewrap 为默认文件系统沙箱、施加 PR_SET_NO_NEW_PRIVS 与 seccomp 网络过滤器；Landlock 为旧选项（features.use_legacy_landlock），对受文件系统限制的策略被拒绝，"因为它无法隔离 app-server 的 Unix socket"；Vaughan（2026-10-03 更新）仍写 bwrap+Landlock+seccomp，可能反映较早设计；审批策略 on-request / never 两种 | 4, 27 |
| B04-10 | CVSS 8.7；影响 < 1.0.111；修复 1.0.111 | CVE-2025-59536：Claude Code 可被诱使在用户接受启动信任对话框之前执行项目中包含的代码（CWE-94） | Claude Code | [CVE-2025-59536 记录](https://cveawg.mitre.org/api/cve/CVE-2025-59536)（GHSA-4fgq-fpq9-mr3g） | 一手文档 | 2025-10-03 | 高 | 不含 API token 外传：后者为 CVE-2026-21852（见 B04-17）；Check Point 原文抓取失败 | 4, 21 |
| B04-11 | CVSS 7.7（CVSS 4.0）；影响 < 2.1.64；修复 2.1.64 | CVE-2026-39861：沙箱未阻止创建指向工作区外的符号链接，未被沙箱的 Claude Code 进程随后跟随写出工作区（CWE-22、CWE-61） | Claude Code | [CVE-2026-39861 记录](https://cveawg.mitre.org/api/cve/CVE-2026-39861)（GHSA-vp62-r36r-9xqp） | 一手文档 | 2026-04-21 | 高 | 博客标题作"2026-05 修复"，以 CVE 记录为准 | 4 |
| B04-12 | CVSS 1.8；影响 < 0.0.16；修复 0.0.16 | CVE-2025-66479：未配置任何允许域名时 sandbox-runtime 未正确执行网络沙箱（CWE-693） | Anthropic srt | [CVE-2025-66479 记录](https://cveawg.mitre.org/api/cve/CVE-2025-66479)（GHSA-9gqj-5w7c-vx47） | 一手文档 | 2025-12-04 | 高 | SecurityWeek 2026-05-20 提及此 CVE 属另一研究者的绕过，与 SOCKS5 空字节无关 | 4, 14 |
| B04-13 | 2 种模式（提升 elevated / 非提升 unelevated） | Codex 原生 Windows 沙箱：提升模式用专用低权限沙箱用户 + 防火墙规则；非提升模式用受限令牌 + ACL，文档称"弱于提升模式" | OpenAI Codex | [Codex Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox) | 一手文档 | 2026-10-04 读取 | 高 | 文档未提 AppContainer；Vaughan 称账户名为 CodexSandboxOffline / CodexSandboxOnline（二手） | 4, 21 |
| B04-14 | 3 层（`mandatoryDenySearchDepth` 默认） | srt 在 Linux 上于可写路径内搜索危险文件的默认深度 | Anthropic srt | [sandbox-runtime README](https://github.com/anthropic-experimental/sandbox-runtime) | 一手文档 | 2026-10-04 读取 | 高 | 可调 | 4 |
| B04-15 | 6 个 profile；默认 `permissive-open` | Gemini CLI macOS Seatbelt profile；沙箱默认关闭 | Gemini CLI | [Gemini CLI sandbox 文档](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/sandbox.md) | 一手文档 | 2026-10-04 读取 | 高 | 另有 Windows 原生沙箱（icacls 完整性级别）、Docker/Podman、gVisor、LXC（实验） | 4, 21, 27 |
| B04-16 | 50% | Docker sbx 默认内存占宿主 RAM 比例（本地版） | Docker Sandboxes | [Vaughan](https://codex.danielvaughan.com/2026/04/24/agent-sandbox-comparison-codex-seatbelt-openshell-docker-sbx/) | 二手报道 | 2026-10-03 更新 | 中 | Docker 博客 2026-09-24 未提此值，云端 Small 默认档为 4 GiB | 4 |
| B04-17 | CVSS 5.3；2026-01-21 公布；影响 2.0.65 之前 | CVE-2026-21852：Claude Code API 凭据外传（Check Point 与 CVE-2025-59536 同篇披露；均在公开前修复） | Claude Code | CVE 记录 https://cveawg.mitre.org/api/cve/CVE-2026-21852；[Check Point](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files/)（2026-02-25）；TechRadar 2026-02-26 转述 | 一手文档 | 2026-01-21 | 高 | 原文："Prior to version 2.0.65, vulnerability in Claude Code's project-load flow allowed malicious repositories to exfiltrate data including Anthropic API keys before users confirmed trust."；Check Point 披露机制为项目配置中的 ANTHROPIC_BASE_URL 重定向（Check Point 原文 2026-10-06 再读为空，JS 渲染；机制描述据此前对原文的读取） | 4, 21 |
| B04-18 | 7 项发现；4 种失效模式 | Pillar Security 报告的原始分类：denylist 沙箱跟不上操作系统、实为可执行代码的工作区配置、按名字信任的安全命令白名单、沙箱外特权本地守护进程 | Pillar Security | [Pillar 原文](https://www.pillar.security/blog/one-docker-socket-to-rule-them-all-escaping-codex-cursor-and-gemini-clis-sandboxes) | 一手文档（研究方披露） | 2026-07-20 | 中 | 第 4 章四分类（代理解析/安全命令/信任移交/能力型 socket）为本书分类，不可混同 | 4, 5 |

### 第 5 章　容器与 gVisor

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B05-01 | 3 个 CVE，均为 CVSS 7.3；修复于 runc 1.2.8、1.3.3、1.4.0-rc.3 | 2025-11 runc 逃逸 CVE（31133 / 52565 / 52881） | runc | [CNCF 博客][cncf-runc] | 一手文档 | 2025-11-28 | 高 | 触发条件：自定义挂载配置（含 Dockerfile 中 RUN --mount=…）或恶意、被攻陷的镜像；缓解：用户命名空间、非 root 运行、AppArmor/SELinux（"can help to mitigate some of the attack vectors"）；CVE-2025-52881 本身是绕过 LSM 检查的漏洞（经 /proc/self/attr/<label> 重定向） | 5 |
| B05-02 | CVSS 9.0 | NVIDIAScape（CVE-2025-23266） | NVIDIA Container Toolkit | [emirb microVM 综述][emirb]；[Wiz：NVIDIAScape][wiz-nvidiascape] | 二手报道（安全厂商） | 2026-03-27 | 中 | 影响 NVIDIA Container Toolkit ≤ 1.17.7、GPU Operator ≤ 25.3.1；createContainer 钩子继承镜像环境变量，经 LD_PRELOAD 加载恶意库；三行 Dockerfile；2025-07-17 披露（NVIDIA 公告 07-15）；修复版本未回 NVIDIA 公告核对 | 5, 28 |
| B05-03 | 约 50 ms | gVisor 启动 | gVisor | [emirb][emirb] | 二手报道 | 2026-03-27 | 中 | 厂商数据汇总，量级参考；OpenSandbox 安全运行时指南写 gVisor 启动开销约 10–50 ms（厂商自报，见 B05-11） | 5, 6 |
| B05-04 | Sentry 自身发出 53 种宿主 syscall（含网络 68 种）；重新实现约 274 个；完整内核 ABI 450 个以上 | gVisor 攻击面 | gVisor | [emirb][emirb] | 二手报道 | 2026-03-27 | 中 | emirb 原文 "gVisor reimplements ~274 Linux syscalls in Go, but the Sentry itself only makes 53 host syscalls without networking, 68 with"（emirb 转引自 luiscardoso.dev，实为三手）；gVisor 官方安全文档只写"最小的一组宿主系统调用"，无具体数量；HotCloud'19 为 55 种（2019 年版本，见 B05-09）；官方 amd64 兼容表为 352 个中 290 个有实现（见 B05-08）；"450+"与"352"口径不同，见 C-42 | 5 |
| B05-05 | Node.js 2×、WordPress 7× | systrap 模式吞吐提升 | DigitalOcean（gVisor） | [emirb][emirb] | 二手报道 | 2026-03-27 | 低 | 转述 | 5 |
| B05-06 | 3–15 s | Kubernetes pod 调度耗时 | — | [emirb][emirb]；[manveerc][manveerc] | 二手报道 | 2026 | 中 | — | 5, 9 |
| B05-07 | CVSS 8.6；影响 runc v1.0.0-rc93 至 v1.1.11；修复于 v1.1.12 | Leaky Vessels（CVE-2024-21626） | runc | [runc 安全公告 GHSA-xr7r-f8xq-vfvv][runc-ghsa-21626]；[Snyk][snyk-leaky] | 一手文档 | 2024-01-31 | 高 | Snyk 页面未给 CVSS；同批另有 BuildKit CVE-2024-23651/23652/23653；SandboxEscapeBench 中 leaky_vessels 为难度 3 | 5 |
| B05-08 | 352 个系统调用中 290 个有完整或部分实现；62 个不支持 | gVisor amd64 兼容表 | gVisor | [gVisor amd64 兼容性][gvisor-amd64] | 一手文档 | 2026-10-04 读取 | 高 | 与 emirb"约 274 个重新实现"口径不同；时点数字 | 5 |
| B05-09 | 55 种宿主调用；向应用暴露 319 个中的 211 个；系统调用慢 2.8×（最快配置）；外部 tmpfs 文件开关慢 216×、内部 tmpfs 12×；1 GB 下载约 34% 吞吐（KVM 平台）；Python 导入慢 2–4× | gVisor 2019 年版本的宿主调用与开销 | gVisor | [HotCloud'19：The True Cost of Containing][hotcloud19] | 论文自述 | 2019-07 | 高（对 2019 年版本） | 原文 "The Sentry exposes 211 of 319 Linux system calls to the application"；2.8× 的比较基线未逐字确认；已陈旧：此后有 systrap、directfs；不得当作当前性能引用（X-37） | 5 |
| B05-10 | 额外 15 个 | 宿主网络直通模式下 Sentry 需额外放开的宿主系统调用 | gVisor | [gVisor Networking Security][gvisor-net] | 一手文档 | 2020-04-02 | 高 | — | 5 |
| B05-11 | runc 约 0 ms；gVisor 约 10–50 ms、内存约 50 MB；Kata（QEMU）约 500 ms；Kata（Firecracker）约 125 ms、约 5 MB；Kata（CH）约 200 ms | OpenSandbox 安全运行时指南中的启动与内存开销 | 阿里 OpenSandbox | [OpenSandbox secure-container 指南][osb-secure] | 厂商自报 | 2026-10-04 读取 | 中 | 未说明测试条件；安全运行时按服务器配置，留空为 runc（默认，见 X-38）；`kata` 类型默认 QEMU | 5, 6 |
| B05-12 | 约 29% | systrap 平台 seccomp-bpf 过滤开销降低；过滤程序缩小 4 倍以上；构建基准总运行时间约降 1% | gVisor | [Optimizing seccomp usage in gVisor][gvisor-seccomp] | 一手文档 | 2024-02-01 | 高 | — | 5 |
| B05-13 | 难度 1（privileged、docker.sock、hostpath）；难度 2（RBAC、CAP_SYS_ADM、pid ns）；难度 3（CAP_MOD、CAP_DAC_RD、runc 2019、runc 2024、cgroup、dirty cow、dirty pipe）；难度 4（kubectl cp、route ln）；难度 5（CRI-O、bpf privesc、packet sock） | SandboxEscapeBench 场景难度 | UK AISI | [arXiv 2603.02277v3][sebench] | 论文自述 | 2026-08-01（v3） | 中 | PDF 表 1（抓取摘录）与仓库 README、difficulty.py 三方一致（2026-10-06）；删去"README 难度体系与论文不一致"；分层依论文：编排（L1）4、引擎与运行时（L3）8、宿主与内核（L4）6，runc 2024 在仓库中归 Kubernetes 类、论文归 L3 | 5, 20 |
| B05-14 | 4 倍 | DSec 每节点稳定运行上限：容器 ÷ microVM（3,200 ÷ 800） | DSec | 由 B13-01 推算 | 笔者推算 | 2026-10 | 中 | 观测上限之比，不是同负载受控对比 | 5 |

### 第 6 章　microVM

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B06-01 | VMM 启动 ≤ 8 CPU ms（墙钟 6–60 ms，典型约 12 ms） | Firecracker VMM 进程启动 | Firecracker | [Firecracker SPECIFICATION.md][fc-spec] | 一手文档 | 2026-09 抓取 | 高 | — | 6 |
| B06-02 | ≤ 125 ms | InstanceStart 到 guest `/sbin/init`（1 vCPU / 128 MiB；关闭串口、最小内核与根文件系统；M5D.metal 关超线程 / M6G.metal） | Firecracker | [SPECIFICATION.md][fc-spec] | 一手文档 | 同上 | 高 | — | 6, 11 |
| B06-03 | ≤ 5 MiB（1 vCPU/128 MiB guest） | 每 microVM 内存开销 | Firecracker | [SPECIFICATION.md][fc-spec] | 一手文档 | 同上 | 高 | 指 VMM 线程开销，不含 guest 内存与 MMDS；随 vsock 连接数等负载与配置变化 | 6, 13 |
| B06-04 | > 95% 裸金属 | guest CPU 性能 | Firecracker | [SPECIFICATION.md][fc-spec] | 一手文档 | 同上 | 高 | 原文标注"integration test pending" | 6 |
| B06-05 | 14.5 Gbps（≤80% 宿主 CPU）/ 25 Gbps（100%），约 0.06 ms 附加延迟；存储约 1 GiB/s（≤70% 一核） | 网络与存储性能 | Firecracker | [SPECIFICATION.md][fc-spec] | 一手文档 | 同上 | 高 | 四项均标注"integration test pending" | 6 |
| B06-06 | 约 83k 行 Rust；Cloud Hypervisor 约 106k 行 | 代码规模 | Firecracker / CH | [emirb][emirb] | 二手报道 | 2026-03-27 | 中 | emirb 为 cloc 口径（只计代码行，2026-03）；NSDI'20 论文为约 50k 行（2020，论文自述，见 B06-28）；笔者对 f23a213（2026-10-01）src/ 下 361 个 .rs 计数 124,033 行（去空行 109,931，含注释与测试；cloc 口径约 9.1 万行，见 B06-29）；口径不同，并列 | 6 |
| B06-07 | 每宿主每秒最多 150 台（"up to 150 MicroVMs per second per host"） | 创建速率 | Firecracker NSDI'20 | [Firecracker NSDI'20][fc-nsdi] | 论文自述 | 2020 | 高 | 2026-10-04 回 NSDI'20 PDF 核实（X-26 已移出此项） | 6 |
| B06-08 | CH < 200 ms（Linux 6.18 最小内核）；嵌套虚拟化下约 3% CPU 开销 | Cloud Hypervisor 启动与开销 | Cloud Hypervisor（Oracle OCI 数据） | [emirb][emirb] | 二手报道 | 2026-03-27 | 中 | — | 6 |
| B06-09 | 额外 150–300 ms | Kata 启动开销 | Kata Containers | [emirb][emirb] | 二手报道 | 2026-03-27 | 中 | — | 5, 6 |
| B06-10 | < 200 ms | libkrun 启动 | libkrun | [emirb][emirb] | 二手报道 | 2026-03-27 | 中 | — | 6 |
| B06-11 | 约 320 ms（对比 Docker 463 ms、Firecracker 808 ms；rywalker 2026-06-11）；README 现称平均 < 100 ms（M1 上 guest 启动，2026-10-04 读取）；6,519 星（2026-06） | microsandbox 裸机启动基准 | microsandbox（libkrun） | [rywalker 研究页][microsandbox] | 厂商自报 | 2026-06-11 | 低 | 厂商自测，Firecracker 808 ms 与官方规格 ≤125 ms 口径不同 | 6, 22 |
| B06-12 | 亚 20 ms（FreeBSD 内核）；Unikraft Cloud < 10 ms、单机 > 100,000 实例 | microVM 启动下界 | Firecracker/FreeBSD；Unikraft Cloud | [emirb][emirb] | 二手报道 | 2026-03-27 | 低 | 厂商宣称 | 6, 8 |
| B06-13 | 约 28 ms | 快照恢复 | AWS Lambda SnapStart | [emirb][emirb] | 二手报道 | 2026-03-27 | 低 | 二手来源，非 Agent 负载 | 6, 11 |
| B06-14 | 400 并发时约 263% | RunD 安全容器启用网络相对无网络启动的时间增幅（"reaching around 263% at 400 concurrency"） | RunD（阿里云安全容器） | [IMC'24：Liu 等，Understanding Network Startup for Secure Containers in Multi-Tenant Clouds][imc24-cni]；[manveerc][manveerc]（转述） | 论文自述 | 2024-11 | 高 | 瓶颈为 RTNL 锁与自旋锁；"125 ms 变数秒"为 manveerc 转述者自述，不在论文中；manveerc 泛称"microVM 部署"，原文对象为 RunD | 6, 14 |
| B06-15 | 冷启动 < 60 ms；50 并发平均约 67 ms（P95 90 ms、P99 137 ms） | CubeSandbox 冷启动 | 腾讯 CubeSandbox | [CubeSandbox README_zh][cube-readme]；[腾讯云开发者社区][cube-dev] | 厂商自报 | 2026-04-21 | 中 | P95/P99 亦见于 README（2026-09-30）；指模板快照恢复到可用；仓库裸金属报告（2026-06-01）50 并发平均 276.1 ms、P95 508.4 ms，口径与 README 不同，见 B06-20 | 6, 26 |
| B06-16 | 单实例内存开销 < 5 MB；96 核物理机 2000+ 沙箱 | CubeSandbox 密度 | 腾讯 CubeSandbox | [腾讯云开发者社区][cube-dev]；[GitHub][cube-gh] | 厂商自报 | 2026-04-21 | 中 | GitHub 写"thousands of instances per server"，见 C-12；仓库性能报告按 free 差值摊算为 21.5–25.7 MB（裸金属）/ 27–34 MB（PVM），见 B06-21 | 6, 13, 26 |
| B06-17 | 1–2 ms（对比优化后传统 VM > 120 ms） | micro-VM 创建 | Microsoft Hyperlight | [Hyperlight 博客][hyperlight] | 一手文档 | 2024-11-07 | 高 | 无 guest OS，适合函数级工具调用；Hyperlight Wasm 博客（2025-03-26）给出传统 VM 约 125 ms、Hyperlight Wasm 约 1–2 ms 且目标 < 1 ms；两篇博客均未提 AI/Agent | 6, 8 |
| B06-18 | 30–60 s | 传统 VM 启动 | — | [emirb][emirb] | 二手报道 | 2026-03-27 | 中 | — | 6, 7 |
| B06-19 | 超过 200 个安全容器/秒；超过 2,500 个/节点（384 GB 内存） | RunD 启动速率与密度 | RunD（ATC'22） | [RunD][rund] | 论文自述 | 2022 | 高 | 原文："over 200 secure containers can be started in a second, and over 2500 secure containers can be deployed on a node with 384GB of memory"（USENIX ATC'22 论文页，2026-10-06 核实）；X-26 中 RunD 部分已移出 | 6, 13 |
| B06-20 | 串行平均 47.8 ms（P95 57.4）；20 并发平均 98.1 ms、180.9 个/秒；50 并发平均 276.1 ms、P95 508.4 ms | CubeSandbox 从模板创建到 running（腾讯云 BMI5，96 逻辑核、375 GiB；2 vCPU / 2 GiB 沙箱） | 腾讯 CubeSandbox | [Cube 性能报告][cube-bench] | 厂商自报 | 2026-06-01 | 中 | 与 README 50 并发平均 67 ms 口径不同（B06-15） | 6 |
| B06-21 | 约 21.5 MB（100 个）至约 25.7 MB（1,000 个）；满载约 185 个 | CubeSandbox 空闲沙箱摊销内存（free 差值 ÷ 个数）；每沙箱写满 2 GiB 时 375 GiB 可容纳数 | 腾讯 CubeSandbox | [Cube 性能报告][cube-bench] | 厂商自报 | 2026-06-01 | 中 | 与 README < 5 MB 口径不同（后者近 VMM 侧开销） | 6, 13 |
| B06-22 | 串行平均 66.7 ms；10 并发 170.9 ms；20 并发 364.6 ms（P99 673.8）；摊销 27–34 MB；空闲约 743 个 / 满载约 10 个 | CubeSandbox 在 PVM 云主机（SA9.4XLARGE32，16 核、32 GiB）上 | 腾讯 CubeSandbox | [Cube PVM 性能报告][cube-bench-pvm] | 厂商自报 | 2026-06-03 | 中 | 与裸金属串行之比约 1.40（笔者推算，机器不同） | 6 |
| B06-23 | 500 | Cube `tap_init_num` 默认预建 TAP 数；密度测试须调高 | 腾讯 CubeSandbox | [Cube 性能报告][cube-bench] | 一手文档 | 2026-06-01 | 高 | 网络准备移出关键路径的例证 | 6, 14 |
| B06-24 | 2026-02-16；C8i / M8i / R8i | AWS 在虚拟 EC2 实例上支持嵌套虚拟化（KVM 或 Hyper-V，所有商业区域） | AWS | [AWS 新闻稿][aws-nested] | 一手文档 | 2026-02-16 | 高 | emirb 写"2026 年 2 月"一致 | 6, 28 |
| B06-25 | 2026-06-18；C7i、M7i、R7i、C8id、M8id、R8id、I7i、X8i 及 flex 机型；GovCloud | AWS 嵌套虚拟化扩展 | AWS | [AWS 新闻稿][aws-nested2] | 一手文档 | 2026-06-18 | 高 | — | 6 |
| B06-26 | 0.179 µs vs 1.3 µs；VM 退出/进入延迟平均降低 > 75%；内存密集并发负载最高一个数量级 | PVM 相对硬件辅助嵌套虚拟化（EPT-on-EPT） | PVM | [PVM SOSP'23][pvm] | 论文自述 | 2023-10-23 | 中 | 经摘要式抓取作者主页 PDF | 6 |
| B06-27 | 每天 > 10 万个安全容器、> 40 万 vCPU；RFC 称"每天数万个" | PVM 在阿里云（与蚂蚁）的生产规模 | PVM | [PVM SOSP'23][pvm]；[LKML RFC][pvm-rfc] | 论文自述；一手文档 | 2023 / 2024-02-26 | 中 | 两处口径不同，并列 | 6 |
| B06-28 | 约 50k 行 Rust（比 QEMU 少 96%）；QEMU > 1.4M 行（4.2）；< 125 ms 到应用代码；< 5 MB 每容器 | Firecracker 2020 年论文数字 | Firecracker | [Firecracker NSDI'20][fc-nsdi] | 论文自述 | 2020 | 高 | 与 SPECIFICATION 措辞略异，以 SPECIFICATION 为准 | 6 |
| B06-29 | 124,033 行；109,931 行（去空行）；约 9.1 万行（cloc 口径，粗算） | Firecracker src/ 下 .rs 文件行数（提交 f23a213，含注释与测试） | Firecracker | [Firecracker 仓库][fc-repo] | 笔者推算 | 2026-10-01 | 中 | 与 B06-06（约 83k，二手）、B06-28（约 50k）口径不同 | 6 |
| B06-30 | Linux ≥ 5.18（ACPI）；≥ 6.10（DeviceTree）；16 字节 | VMGenID：guest 内核据此重播种 PRNG 的最低版本；代际 ID 长度 | Firecracker | [Firecracker snapshot-support.md][fc-snap] | 一手文档 | 2026-10-01 | 高 | 应用层随机数、标识符、令牌仍会被复制 | 6, 11 |
| B06-31 | 8 小时；15 分钟；14 天 | AgentCore microVM 会话默认最长计算寿命；默认空闲停止；Instances 上的会话上限 | AWS Bedrock AgentCore | [AgentCore 会话文档][agentcore-sess] | 一手文档 | 2026-10-04 读取 | 高 | 文档未点名 VMM | 6, 21 |
| B06-32 | `1.15.1-patch-v1`（KVM）；`v1.17.0-next.1`（PVM）；9 个提交 | AgentENV 下载的 Firecracker 版本：kvcache-ai/firecracker 自维护补丁版与 firecracker-next；`v1.15.1-patch` 相对上游 v1.15.1 的提交数（脏页范围、内存区域 RPC、O_DIRECT 块后端、快照内存文件可选、KVM 预缺页） | AgentENV | [AgentENV `config/deps_manifest.toml`][aenv]；kvcache-ai/firecracker | 一手文档 | 2026-09-30 | 高 | 否定"AgentENV 用未修改的 Firecracker"；DSec 的 Firecracker 版本与修改未披露 | 6, 25 |
| B06-33 | `vmlinux-6.1.175` | AgentENV KVM 模式默认 guest 内核 | AgentENV | [AgentENV deps_manifest][aenv] | 一手文档 | 2026-09-30 | 高 | PVM 模式为 6.12.33-pvm（B25-16）；宿主须 Linux 6.8+ | 6, 25 |
| B06-34 | v0.7.6 | microsandbox 最新标签（README 仍标"beta 软件"） | microsandbox | [microsandbox 仓库](https://github.com/superradcompany/microsandbox) | 一手文档 | 2026-10-04 读取 | 高 | 时点数字 | 6 |
| B06-35 | 第 515–530 页；15 位作者 | PVM 论文（SOSP 2023）页码与作者数 | PVM | [PVM（ACM DL）][pvm]；Crossref 元数据 | 一手文档 | 2023-10（SOSP'23） | 高 | 第 6 章据 Crossref 复核 | 6 |
| B06-36 | 约 1.40 倍 | CubeSandbox PVM 云主机与裸金属串行创建平均时延之比（66.7 ÷ 47.8） | 腾讯 CubeSandbox | 由 B06-22、B06-20 推算 | 笔者推算 | 2026-10 | 中 | 两组测试的机器不同，只表示量级 | 6 |
| B06-37 | 169.254.68.6 | CubeSandbox 每个沙箱内部使用的同一固定地址（由 eBPF 做 SNAT 映射） | 腾讯 CubeSandbox | [CubeSandbox `docs/architecture/network.md`][cube-gh] | 一手文档 | HEAD e02976a（2026-09-30） | 高 | — | 6 |

### 第 7 章　完整 VM、GUI、移动与浏览器环境

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B07-01 | "several thousand instances"；"several thousand QPS"；"millions of interactive rollouts"（原句："making it possible to run millions of interactive rollouts reliably"） | 统一沙箱平台规模 | 字节 UI-TARS-2 | [arXiv 2509.02544][uitars2] | 论文自述 | 2025-09 | 中 | 原文即模糊量词，勿换算成具体数；原文："the VM cluster comprises several thousand instances, centrally managed by a VM Manager capable of sustaining throughput at several thousand QPS"（§2.2）；浏览器沙箱"running multiple browser instances per container with elastic scheduling"，"re-implemented Window timing APIs allow time acceleration and pause at startup"；旧稿"millions of interactive episodes"原文无此语 | 7, 26 |
| B07-02 | "several thousands of concurrent environments" | qemu-in-docker Ubuntu VM 并发 | 智谱 ComputerRL | [arXiv 2508.14040][computerrl] | 论文自述 | 2025-08（ICLR 2026） | 中 | 另处写"thousands of parallel environments" | 7, 26 |
| B07-03 | 48.1% | OSWorld 成绩 | ComputerRL | [arXiv 2508.14040][computerrl] | 论文自述 | 2025-08 | 高 | 步数至多为最强基线的 1/3（§4.1） | 7 |
| B07-04 | "hundreds of Dockerized AVDs"；"over 1,000 environments"；VLM 奖励验证准确率 86%（验证集 1,000 条 AndroidLab 轨迹；三模型打分取多数票作标签） | 移动 RL 环境规模与奖励模型 | 智谱 MobileRL | [arXiv 2509.18119][mobilerl] §2.1、附录 C.1/C.3 | 论文自述 | 2025-09 | 中 | 附录 C.3 承认 VLM 奖励带来更多训练不稳定 | 7, 19 |
| B07-05 | 10–100× 更低成本；> 90% 标注准确率 | CSRS 步级奖励系统 | 阶跃 Step-GUI | [arXiv 2512.15431][stepgui] | 论文自述 | 2025-12 | 中 | 设备数未披露 | 7, 26 |
|  B07-06 | 最高 6.20×（VWA 吞吐，8 并发；WebArena 2.22×、OSWorld 3.08×）；每环境内存 9.2×（VWA；WebArena 4.5×、OSWorld 3.2×）；增量存储 504×（VWA；WebArena 515.8×、OSWorld 2.2×） | 相对"每 rollout 一个 Docker" | CUA-Sandbox | [作者仓库所附 PDF](https://github.com/windskyyx/CUA-Sandbox-Efficient-Environments-for-Computer-Use-Reinforcement-Learning) §4.3 与图 3（arXiv 2609.32750；未与 arXiv 版逐字比对） | 论文自述 | 2026-09-26 | 中高 | VWA 每环境内存 1,745.2 → 190.0 MiB；附录表 6 的 VWA 列与正文不一致（按表 6 推得约 4.25×/1.75×，C-56）；最大密度未测；§4.4 另有单场景内存降幅最高 51.2×（WebArena GitLab）；未与 arXiv 版逐字比对；通讯作者 Xingrui Yu（A*STAR） | 7, 11, 13, 28, 附录 D  |
| B07-07 | 单实例约 400 MB（模拟器约 4.5 GB）；冷启动约 3 s（AndroidWorld 模拟器约 78 s，为未启用 /dev/kvm 时的实测中位数，原文"with KVM enabled, it is usually faster"）；单服务器可承载数百个实例（实测 256 个并行实例 CPU < 10%、内存约 100 GB）；256 任务评测约 6 分钟 | 浏览器托管 Android 模拟 | MobileGym | [arXiv 2605.26114][mobilegym] | 论文自述 | 2026-05（预印本） | 高 | 会议录用情况未核实（arXiv HTML 未注明会议）；旧稿"单服务器约 400 实例"系把"约 400 MB"误读为实例数；原文用"~"不用"+" | 7, 11, 13, 28, 附录 D |
| B07-08 | 内存约为 AndroidWorld 的 1/10（约 400 MB vs 约 4.5 GB）、磁盘 1/100（约 50 MB vs AndroidWorld Docker 镜像合计约 20.2 GB，其中 Android 13 系统镜像约 9.5 GB）；快照恢复"毫秒级"（ms-level） | MobileGym 资源与快照 | MobileGym | [arXiv 2605.26114][mobilegym] | 论文自述 | 2026 | 高 | "毫秒级"无具体数；磁盘口径与 AndroidWorld README"最低 8 GB 磁盘"不同 | 7, 11 |
| B07-09 | +12.8 个百分点；59 个真机任务保留 95.1% 增益 | Qwen3-VL-4B GRPO 效果与 sim-to-real | MobileGym | [arXiv 2605.26114][mobilegym] | 论文自述 | 2026 | 高 | — | 7 |
| B07-10 | 平均 117 ms（RDP 122 ms）；带宽最多降 50%（摘要）/最多降 55%（结论，视频播放 4.6 vs 10.2 Mbps）；下行丢包 10%：视频 8.55% vs 44.96%，网页浏览 16.45% vs 96.16%（表 4） | ASP 流协议 | 阿里 AgentBay | [arXiv 2512.04367][agentbay-paper] | 论文自述 | 2025-12 | 中 | 50% 与 55% 均出自论文本身（见 C-22）；论文未给 ASP 测试日期（唯一的"February 2025"指 WebArena SOTA） | 7 |
| B07-11 | 浮动广告场景 27% → 97%；CAPTCHA 64% → 95%；整体提升 "more than 48%" | 人机协同接管实验（Claude Sonnet 4.5） | AgentBay | [arXiv 2512.04367][agentbay-paper] | 论文自述 | 2025-12 | 高 | — | 7 |
| B07-12 | 每台 Mac 最多 2 个额外 macOS 实例；第三个 guest 返回 VZErrorDomain Code 6 | macOS 虚拟化许可硬约束 | Apple EULA / Virtualization framework | [Eclectic Light][eclectic] | 二手报道（技术博客引 EULA） | 2022-08-04 | 高 | — | 7 |
| B07-13 | Kernel headless $0.06/h、headful $0.48/h、冷启动 < 150 ms；Browserbase $0.10–0.12/h、2–5 s、并发 25–100；Steel $0.08–0.10/h、约 1 s；Anchor $0.05/h + 计量、并发 25–500+；Cloudflare 超 10 h 免费后 $0.09/h；Hyperbrowser 约 $0.10/h | 云浏览器价格与冷启动 | 各云浏览器厂商 | [Kernel 竞品对比][kernel] | 厂商自报（竞品撰写） | 2026-07 | 低 | 需到各官网复核 | 7, 22 |
| B07-14 | 约 10 个 agent 共享一个 Chrome | 浏览器共享密度 | TrEnv-X | [arXiv 2509.09525][trenvx] | 论文自述 | 2026 | 低 | "内存最多降 42%"已删除，42% 未核实：两次读取 v2 HTML，一次转述为"浏览器共享使 Agent 端到端延迟降低 42%"（摘要式），另一次检索全文所得唯一的"42%"句为"在我们的测量中，它（浏览器）在某些 Agent 中占总成本的 42%"（as much as 42% of overall costs for certain agents）；均不支持"内存降 42%"，浏览器共享节未逐字核对；原备注：以削弱 cookie/存储隔离换密度；原文"TRENV-X allows multiple agents (e.g., ten) to concurrently share a single browser instance"；原文把"浏览器共享的 Agent 之间无意的数据共享（例如 cookie）"列为局限，建议引入 Firefox Containers 类隔离；"61% 内存、58% P99"为全系统相对 E2B+ 的合计（B13-11），不是浏览器共享单项；2026-10-04 第三次读取，含 42% 的句子被转述为指 serverless 执行开销，与此前"指浏览器"的读法冲突，继续不引用 | 7, 13 |
| B07-15 | 延迟开销 7.25–15%；策略选择准确率 94%+；GitLab 案例拦截 12/12 模拟攻击；内存约 25 MB | HTTP 层浏览器最小权限 | ceLLMate | [arXiv 2512.12594][cellmate] | 论文自述 | 2025-12（2026-03 修订） | 高 | 另有二手综述写"在 WASP 上拦截注入"（未核实）；延迟开销 7.25% 对应 100 条 sitemap 条目、15% 对应 300 条；作者含 AI Sequrity Company 的 Ilia Shumailov；会议状态未确认（有摘要称"疑似 IEEE S&P"，无依据，不写） | 7, 14 |
| B07-16 | 22,625 条轨迹（Windows 12k、macOS 5k、Ubuntu 5k；平均 18.6 步；140+ 应用、190+ 网站） | AgentNet 数据集 | OpenCUA | [arXiv 2508.09123][opencua] | 论文自述 | 2025-08 | 高 | — | 7 |
| B07-17 | 44.4% → 74.1%；步数少 43.5%；时间少 39%；61% 成功只需一次 LLM 调用 | 声明式 GUI 接口（DMI）在 MS Office 上 | Rethinking OS Interfaces for LLM Agents | [AgenticOS'26 论文 9][dmi] | 论文自述 | 2026-03-23 | 高 | 自称有 EuroSys'26 完整版，未核实 | 7 |
| B07-18 | 每用户一台云手机 + 一台云电脑；约 0.2 美元/任务（约 1.4 元，含推理与 VM） | AutoGLM 2.0 产品形态与单价 | 智谱 AutoGLM 2.0 | [新浪财经][autoglm-sina]；[量子位][qbit-autoglm] | 二手报道 | 2025-08-20 | 中 | 单价仅见新浪财经；量子位同日报道（2026-10-04 复核）只有"为每位用户准备了一台云手机和一台云电脑""不会影响用户正常使用自己的设备"，未提单价，也未披露虚拟化、云厂商与规模 | 7, 21, 26 |
| B07-19 | 36 个漏洞 Web 应用；最佳模型 Claude-3.7-Sonnet 平均成功率 10.18%（各观测空间平均；单一配置最高 11.1%）；各 Agent 利用率均 < 12% | GUI 渗透能力评测 | HackWorld | [arXiv 2510.12200][hackworld] | 论文自述 | 2025-10 | 高 | — | 7, 20 |
| B07-20 | 约 50 MB（AndroidWorld 约 20 GB）；416 个模板；28 个 App（12 个日常 + 16 个系统）；256 测试 + 160 训练 | MobileGym 磁盘与任务规模 | MobileGym | [arXiv 2605.26114][mobilegym] | 论文自述 | 2026 | 高 | 任务规模与 B20-29 同源 | 7, 20 |
| B07-21 | 约 22 个 | 约 100 GB 内存可容纳的约 4.5 GB Android 模拟器数（与 MobileGym 256 个实例对比） | — | 由 B07-07 推算（100 ÷ 4.5） | 笔者推算 | 2026-10 | 中 | 未计 CPU 与磁盘约束，仅作量级 | 7 |
| B07-22 | 2026-08-18；2026-08-19 | 豆包 Windows 版"虚拟桌面"上线；"工作任务"云电脑模式上线 | 字节豆包 | [腾讯新闻][doubao-vd]；[科技日报][doubao-cloud] | 二手报道 | 2026-08 | 中 | 底层技术（VM、容器或 Windows 原生功能）未披露；"无需依赖 MCP、API、插件、命令行工具" | 7, 21, 26 |
| B07-23 | reset 1.03×–7.29×、fork 1.10×–17.84×、create 1.15×–15.17×（相对 Docker）；fork 0.054 s、create 0.071 s（3.6 GB Shopping 胶囊） | CUA-Sandbox 生命周期操作加速比与绝对延迟 | CUA-Sandbox | [作者仓库所附 PDF](https://github.com/windskyyx/CUA-Sandbox-Efficient-Environments-for-Computer-Use-Reinforcement-Learning) 表 3、§4.5 | 论文自述 | 2026-09-26 | 中高 | 0.054/0.071 s 是 CUA-Sandbox 自身值，对照为"去掉写时复制"的消融（4.772 s / 5.476 s），不是 Docker；reset 无绝对延迟；未与 arXiv 版逐字比对 | 7, 11, 附录 D |

### 第 8 章　WASM、TEE 与轻量方案

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B08-01 | 约 5% 存储（SWE-smith：13.5 GB vs 295 GB）；SWE-bench Verified 约 15%（89 GB vs 605 GB）；约 25% 准备时间（3B 模型：23.62 s vs 88.86 s） | 用 mount ns + chroot 取代每任务 Docker | SWE-MiniSandbox | [arXiv 2602.11210][swemini] | 论文自述 | 2026-02（ICML 2026，PMLR 306） | 高 | 按原始数字约 4.6%、14.7%、26.6%（笔者推算）；"约 5%"只对 SWE-smith 成立，不可当作普适值；旧稿"约 90 s → 约 24 s"为约数；实验规模为每次更新 128 个并行环境、1,600 个训练实例；典型 venv 约 100 MB；作者自述共享内核、"不太适合运行不可信或可能恶意的代码"、不支持内核级操作、网络灵活性低于 Docker；是否使用 PID/网络命名空间未核实；原 B04-16、B04-20 并入本行与 B08-09 | 4, 5, 8, 10, 17 |
| B08-02 | 约 78%（约 20% blind + 约 58% schema 可推断） | 97 个 AgentDojo 任务中无需 LLM 看到数据即可脚本化的比例 | Execute-Only Agents | [AgenticOS'26 论文 21][execonly] | 论文自述（愿景论文） | 2026-03-23 | 中 | 愿景论文 | 8, 14 |
| B08-03 | FHE 开销高 2–4 个数量级 | 同态加密代价 | TEE 综述 | [arXiv 2605.03213][tee-survey] | 论文自述（综述） | 2026-05 | 中 | GPU TEE 在 LLM 规模的性能为 §VIII-E 所列六个开放挑战之一；全文无 TDX/SEV-SNP/H100 CC 开销数字；综述作者 Javad Forough、Marios Kogias、Hamed Haddadi，v1 2026-05-04 | 8 |
| B08-04 | README 列 21 个语言条目（含 CUDA、Verilog、GPU 版 Python），文档首页称"最多 20 种"（另页含 Lean）；基准 README 11 个 / 文档 Get Started 页 12 个（多 miniF2F）；约 1.1k 星（未经 API 复核） | 代码执行与评判沙箱 | 字节 SandboxFusion | [GitHub SandboxFusion][sandboxfusion] | 一手文档 | 2026-09 抓取 | 高 | 星标为抓取时点；"24 种"在仓库与文档中均无出处，见 C-38；README 未说明隔离机制，文档称"在特权容器可用时提供内置安全隔离"（摘要式抓取），具体机制未披露 | 8, 26 |
| B08-05 | "a few milliseconds"、"a few megabytes" vs "hundreds of milliseconds"、"hundreds of megabytes"；"100x faster" | V8 isolate 与容器的启动与内存 | Cloudflare Dynamic Workers | [Sandboxing AI agents, 100x faster](https://blog.cloudflare.com/dynamic-workers/) | 厂商自报 | 2026-03-24（07-22 修订） | 中 | 开放 beta；JavaScript 为主 | 8, 22 |
| B08-06 | 81% | 把一个 MCP server 改写成 TypeScript API 后的 token 降幅（"simply converting an MCP server into a TypeScript API can cut token usage by 81%"） | Cloudflare Code Mode | 同上 | 厂商自报 | 2026-03-24 | 中 | 博客回引此前 Code Mode 文章的结果；未独立测试 | 8 |
| B08-07 | "under 1ms"（OSS Monty，池内新建）；"about 2ms"（Full Monty）；v1.0.0 | Monty 新建沙箱延迟；版本 | Pydantic Monty | [pydantic/monty README](https://raw.githubusercontent.com/pydantic/monty/HEAD/README.md)；[Monty 文档](https://pydantic.dev/docs/monty) | 厂商自报；一手文档 | 2026-10-04 读取 | 中 | 文档称"ready for production use"；文档延迟表 OSS Monty 新建 0.80 ms；旧版 README 的 0.06 ms、"Experimental"、约 8.1k 星不再引用；归类见 C-39 | 8 |
| B08-08 | 90 多种语言；约 4,500 星 | 在线代码执行系统 | Judge0 | [judge0/judge0](https://github.com/judge0/judge0) | 一手文档 | 2026-10-04 读取 | 高 | 致谢 Isolate 与 Docker；GPL-3.0 | 8 |
| B08-09 | 13.5 GB vs 295 GB；89 GB vs 605 GB；23.62 s vs 88.86 s | SWE-MiniSandbox 原始存储与准备时间 | SWE-MiniSandbox | [arXiv 2602.11210][swemini] | 论文自述 | 2026-02（ICML 2026，PMLR 306） | 高 | 由 B08-01 拆出的原始值 | 4, 8, 10 |
| B08-10 | 128 个；1,600 个；5.2 → 8.6 vs 5.8 → 9.2；约 2 万个 | 并行环境数；训练实例；3B 模型容器 vs MiniSandbox 得分；被过滤实例 | SWE-MiniSandbox | 同上 | 论文自述 | 2026-02 | 高 | 规模远小于生产负载 | 8, 28 |
| B08-11 | 一种 CPU TEE；H100、RTX PRO 6000 Blackwell | OpenShift 沙箱容器同时只能管理一种 CPU TEE；经机密计算测试的 GPU | Red Hat OpenShift | [Red Hat 文章](https://developers.redhat.com/articles/2026/05/22/protect-data-offloaded-gpu-accelerated-environments-openshift-sandboxed) | 一手文档 | 2026-05-22 | 高 | 运行时类 `kata-cc-nvidia-gpu`；Trustee + NRAS 联合证明；GA 状态未说明；无开销数字 | 8 |
| B08-12 | 2 GB | Wasmtime 线性内存默认前置保护区 | Wasmtime | [Wasmtime Security](https://docs.wasmtime.dev/security.html) | 一手文档 | 2026-10-04 读取 | 高 | — | 8 |
| B08-13 | 2025 年 2 月 | Hyperlight 进入 CNCF 沙箱项目 | Microsoft Hyperlight | [Hyperlight Wasm 博客][hyperlight-wasm] | 一手文档 | 2025-03-26 | 高 | — | 6, 8 |
| B08-14 | 0.1 / 0.2 / 0.3 | WASI 里程碑版本（也称 Preview 1/2/3；0.3 为组件模型加入原生异步） | WASI | [wasi.dev](https://wasi.dev/) | 一手文档 | 2026-10 读取 | 高 | — | 8 |
| B08-15 | 6 个 | coze-loop Pyodide 运行时权限开关（`AllowEnv`、`AllowRead`、`AllowWrite`、`AllowNet`、`AllowRun`、`AllowFFI`） | coze-loop | [coze-loop pyodide 包文档](https://pkg.go.dev/github.com/coze-dev/coze-loop/backend/modules/evaluation/infra/sandbox/infra/pyodide) | 一手文档 | 2025-09-02 发布 | 高 | 另有 `MemoryLimitMB`、`TimeoutSeconds`；用途是执行评测器代码 | 8 |
| B08-16 | 0.002 美元 / Worker / 天 | Dynamic Workers 加载费（开放 beta 期间免收） | Cloudflare Dynamic Workers | [Sandboxing AI agents, 100x faster](https://blog.cloudflare.com/dynamic-workers/) | 厂商自报 | 2026-03-24（07-22 修订） | 中 | — | 8 |
| B08-17 | 约 4.6%；约 14.7%；约 26.6% | SWE-MiniSandbox 按原始数字计算的存储比（SWE-smith、SWE-bench Verified）与 3B 模型环境准备时间比 | SWE-MiniSandbox | 由 B08-09 推算（13.5 ÷ 295；89 ÷ 605；23.62 ÷ 88.86） | 笔者推算 | 2026-10 | 中 | 论文写作约 5%、约 15%、约 25%（B08-01）；"约 5%"只对 SWE-smith 成立 | 8 |
| B08-18 | 约 1–2 ms，目标 < 1 ms；约 125 ms | Hyperlight Wasm 启动时间；对照的传统 VM | Microsoft Hyperlight | [Hyperlight Wasm 博客][hyperlight-wasm] | 厂商自报 | 2025-03-26 | 中 | 与 B06-17（Hyperlight micro-VM 创建 1–2 ms，对照 > 120 ms）出自不同博文 | 8 |
| B08-19 | 约 2,700 星 | LiteBox GitHub 星标数 | Microsoft LiteBox | [microsoft/litebox](https://github.com/microsoft/litebox) | 一手文档 | 2026-10-04 读取 | 中 | 摘要式抓取，未经 API 复核；时点数字 | 8 |

---

## 第三部分　工业级沙箱的八层架构

### 第 9 章　参考架构与控制面

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B09-01 | 本地利用率超过 80% | 触发云突发的阈值 | DSec 放置引擎 | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 9, 24 |
| B09-02 | 30 TB 去重 EROFS 镜像集覆盖 70% 容器任务 | 云突发可覆盖范围 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 其余约 30% 容器任务不能上云（笔者推算） | 9, 10, 24, 28 |
| B09-03 | 一个规模单元中 200 台云 VM 吸收约 30% 峰值溢出 | 云突发容量 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 9, 24 |
| B09-04 | k 未给出 | power-of-k-choices 的 k 值与"负载"定义 | DSec | [DSec][dsec] §7（§3.2 只写"随机采样少数几个合格节点，选负载最低者"，power-of-k、herding、在途叠加均在 §7） | 论文自述 | 2026-09-19 | 高 | 属空白，书中不得填写具体 k | 9, 24 |
| B09-05 | 约 250 个/秒 | ACS 每分钟 1.5 万换算成每秒 | 阿里云 ACS | 由 B26-11 推算 | 笔者推算 | 2026-06-22 文档 | 中 | 15,000 ÷ 60；仅作量级比较，口径与 DSec 不同 | 9, 22 |
| B09-06 | 按 2026 年年中 GKE 与 ACS 的公开口径，其创建速率比 DSec 自建集群低一个数量级左右 | GKE 300/s、ACS 约 250/s vs DSec > 5,000/s | 多方 | 由 B22-25、B09-05、B24-06 推算 | 笔者推算 | 2026-09 | 中 | ACS 2026-09 营销口径已升至每分钟 10 万（约 1,667/s，笔者推算），结论需按日期表述，见 C-06；Modal（一分钟一百万，约 16,667/s，测试条件未说明）与腾讯云（数十万实例/分钟，产品页）不计入比较；措辞与 C-13 统一；若取 ACS 营销稿口径（约 1,667/秒），与 DSec（> 5,000/秒）差约 3 倍 | 9, 22 |
| B09-07 | 可靠性约 90% → 99% 以上 | 编排迁至 Temporal 后的可靠性 | Cursor 云 agent | [Cursor：cloud agent lessons][cursor-cloud] | 一手文档 | 2026-06-02 | 高 | 原文为"one 9 of reliability"→"past two 9s of reliability"；"约 90% → 99% 以上"为本书换算 | 9, 21, 27 |
| B09-08 | Gateway HTTP :8080；Scheduler gRPC :9090；调度策略仅 round_robin（默认）与 random | 开源版控制面 | AgentENV | [AgentENV 架构文档][aenv] | 一手文档 | 2026-10-01（HEAD 00351e2 复核） | 高 | 绑定默认在内存中（不设 SCHEDULER_REDIS_ADDR 时重启即丢失）；可选 Redis 绑定存储，并可加 --query-only 只读调度副本（"HA mode is intentionally data-plane only"，services/README.md，首版 8f028b1 即有）；K8s 清单为默认内存、单副本；MarkTechPost 称多节点控制面为原型；`strategy.go` 中除 random 外的策略名一律回落 round_robin；scheduler 以节点心跳名单为事实来源；`binding_ttl` 为路由新鲜度 TTL；gateway 同时承担数据面反向代理 | 9, 25 |
| B09-09 | ~70/s（kube-scheduler 默认 `--kube-api-qps=50`）；单个预热池补充上限 ~70–85 sandboxes/s | K8s 原生沙箱控制面的调度与补充上限 | kubernetes-sigs/agent-sandbox | [agent-sandbox docs/performance-tuning.md][agent-sandbox-perf] | 一手文档 | 2026-09-30（HEAD 82d410e） | 高 | 标准控制面、单池 | 9, 28 |
| B09-10 | 10–20+ claims/s；1,000–2,500+ replicas；~40 write QPS at 20 claims/s；HTTP/2 每连接 100 并发流；APF 建议阈值 ~50 claims/s；`expectationsTimeout = 5m`；示例控制器 `replicas: 1` + 领导者选举 | K8s 原生控制面在高吞吐下的瓶颈与调优 | kubernetes-sigs/agent-sandbox | [agent-sandbox docs/configuration.md][agent-sandbox-config]；[performance-tuning.md][agent-sandbox-perf] | 一手文档 | 2026-09-30 | 高 | — | 9 |
| B09-11 | p50 92 ms / p90 182 ms / p99 376 ms（45/s 泊松，kops）；GKE 测试集群冷启动 p50 ~42–50 s；配置 H p90 74 s、配置 I（replenish-delay=20s，1/75 失败致池被抽干）p90 205 s；75 并发领用、全部性能参数下 200/150/2/1 workers p50 49.8 s vs 1000/1000/500/100 p50 52.7 s | 预热领用与冷启动延迟 | kubernetes-sigs/agent-sandbox | [performance-tuning.md][agent-sandbox-perf] | 一手文档 | 2026-09-30 | 高 | 测试集群 kops 与 20× e2-standard-16 GKE；74 s 与 205 s 不是同一配置的前后对比；无性能参数基线 1000/1000/500/100 为 47.3 s | 9 |
| B09-12 | 约 2 次辅助写/次领用；约 10,000 写/s；约 71 倍；约 3 倍；约 500/s；> 16,667/s | 40 ÷ 20；5,000 × 2；5,000 ÷ 70；5,000 ÷ 1,667；5,000 ÷ 10（MiniMax）；1,000,000 ÷ 60（Modal） | 多方 | 由 B09-10、B24-06、B26-12、B26-14、B22-15 推算 | 笔者推算 | 2026-10 | 中 | 仅作量级论证 | 9 |
| B09-13 | 数秒内（within seconds） | BGP ECMP 在实例故障时重定向流量；适用于"辅助服务"（API 网关、包镜像）与控制面入口 | DSec | [DSec][dsec] §7 | 论文自述 | 2026-09-19 | 高 | 第 24 章已用，此前未登记 | 9, 24 |
| B09-14 | 4 个 CRD（Sandbox；扩展 SandboxTemplate、SandboxClaim、SandboxWarmPool） | agent-sandbox 对象模型 | kubernetes-sigs/agent-sandbox | [README][agent-sandbox] | 一手文档 | 2026-09-30 | 高 | 早先附录 E 曾记为三个 | 9, 16 |
| B09-15 | GPU FnCall 的 Python 进程预热池（机制，无数字） | "a warm pool of Python processes initializes the runtime and imports libraries in advance" | DSec | [DSec][dsec] §7 | 论文自述 | 2026-09-19 | 高 | 容器/microVM 级预热池未披露；另：§3.2 "All sandbox requests, including creation, command execution, and streaming I/O, pass through this ingress"（apiserver 兼作数据面入口），"resource quotas limit resource consumption" | 9, 24 |

### 第 10 章　镜像与存储

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B10-01 | 30 行 Go 代码 | 修改 dockerd（Moby）动态组装 overlayfs lowerdir | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 10, 24 |
| B10-02 | O(m·N)、O(k·N) → O(m)、O(k) | 单体打包与可组合层的重建复杂度 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 10, 18, 24 |
| B10-03 | 阈值如 3 GB | 离线合并连续层的大小阈值 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | "e.g."，示例值 | 10, 24 |
| B10-04 | 256 KiB 块 | ublk 从远端取 OverlayBD 数据的块大小 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 10, 24 |
| B10-05 | 每台 20 × 15 TB SSD；2 × 400 Gbps RDMA 网卡 | 3FS 存储服务器配置 | DSec / 3FS | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 10, 24 |
| B10-06 | 10 节点突发 8,192 容器：按需拉取约 35 分钟（≈ 全本地基线），预先拉取 60 分钟以上（慢 1.71×） | 按需加载评测 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 对照组为 Docker Pull (cold)，即从远端 registry 冷态全量预拉取；本地已缓存的 Docker Pull (cached) 约 35 分钟，与按需持平；36 氪写"Docker cold pull"，与原文一致（C-15） | 10, 24 |
| B10-07 | 每节点写盘：预先拉取 > 1,600 GB；按需约 700 GB（少约 57%）；全本地约 600 GB；预先拉取峰值写 IOPS 近 2 倍 | 按需加载的写放大 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 10, 24 |
| B10-08 | EROFS 45 分钟 vs tar 79 分钟（论文称 1.76× 加速）；tar 总写盘 5.5×、峰值吞吐 3.4× | 确定性工具调用回放 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 1.76× 为原文数字（§8.3），非推算 | 10, 24 |
| B10-09 | microVM 节点：2 × AMD EPYC 9655（每路 96 核、SMT）、1.5 TB DRAM、3.4 TB 存储；容器节点：192 线程、512 GB、5.8 TB 的 QEMU VM；宿主 Linux 7.0、guest Linux 6.1 | 评测硬件 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 论文未给各后端冷/热启动毫秒数 | 10, 13, 24 |
| B10-10 | zstd level 3；16 字节 DiskSegmentMapping | overlaybd LSMT 格式参数 | AgentENV | [AgentENV 架构文档][aenv] | 一手文档 | 2026-09-29 | 高 | — | 10, 25 |
| B10-11 | Linux 6.8+（AutoRegBuffer 零拷贝）；Ubuntu 24.04 | 运行要求 | AgentENV | [AgentENV README][aenv-readme] | 一手文档 | 2026-09 | 高 | — | 10, 25 |
| B10-12 | "比本地盘容量高出几个数量级" | 镜像与快照总占用 vs 本地盘 | AgentENV | [AgentENV README][aenv-readme] | 一手文档（厂商自报） | 2026-09 | 中 | 定性量级，无具体数；体例：仓库 README 中的设计描述记"一手文档"，性能与规模声明加注"厂商自报"（2026-10-02 统一） | 10, 25 |
| B10-13 | "亚秒级启动延迟"（sub-second launch latency at large scale） | OverlayBD + 自研 ublk + 存储层共享 + P2P 传输带来的启动 | Kimi K3 / AgentENV | [Kimi K3 技术报告][k3] §5.3.2 | 论文自述 | 2026-07 | 中 | 原句已逐字取得："We adopt OverlayBD as the image format, together with a custom ublk driver implementation, storage-layer sharing, and P2P transport, achieving sub-second launch latency at large scale."；无分布与条件；K3 称生产用 P2P，AgentENV 文档称 P2P 未经生产测试（C-34） | 10, 25 |
| B10-14 | 约每十次迭代出现一次环境超时（§3.1）；长尾数百秒（§3.1）；因环境故障超时的迭代中训练步平均时长 513 s（正常 365.7 s，§3.1 图 3），env.reset 单独占 rollout 时间 78%；多级缓存（内部 registry 镜像外部镜像 + 计算节点与 registry 间的分布式负载均衡缓存）后成功率 > 99.99%，且 99.99% 以上的初始化在一分钟内完成；数十万次重置中重尾初始化事件不超过十次（§8） | env.reset（拉镜像 + 起容器）可靠性 | RollArt（阿里） | [RollArt arXiv 2512.22560][rollart]；[OSDI'26 PDF][rollart-pdf] | 论文自述 | 2025-12-27（v2 2026-06-15） | 高 | §3.1 原文两句："When environment timeouts occur, the average time spikes to 513 seconds and env.reset alone consumes 78% of rollout time…"（无"最多"）；"Our production data indicates these failures are not rare corner cases, occurring approximately once every ten iterations (§8)."。"these failures"指前句的环境超时，为按迭代计的超时频率，不能换算为按 reset 计的失败率，不写作"env.reset 失败"；"The long-tail delay of env.reset can reach hundreds of seconds in production"亦在 §3.1，此前记 §3.2 有误（附录 D 核对，以 v2 HTML 与 OSDI'26 PDF 确认）；根因 "concurrent Docker image pulls saturate network links"；§8 "raises the env.reset success rate above 99.99%……keeping over 99.99% of initialization under one minute" 两说并存，均可引用；会议：USENIX 页面列 OSDI'26（2026-07），arXiv abs 页 Comments 只有 "19 pages, 15 figures" | 1, 10, 17, 26, 28, 3, 9, 附录 D |
| B10-15 | 优化前峰值磁盘占用约 95%；优化后稳态磁盘占用约 60%；超时无效 rollout 约 6%–7% → 低于 1% | 大规模并发拉镜像的磁盘压力；重写镜像管理模块并引入早释放策略后 | 快手 KwaiEnv | [KAT-Coder-V2.5 arXiv 2607.05471][kat] | 论文自述 | 2026-07 | 高 | 95% 为峰值（"Peak-time disk usage reached roughly 95%"），60% 为稳态（"steady-state disk usage dropped to roughly 60%"），统计量不同，不宜写"95% → 60%" | 10, 18, 26, 28, 附录 D |
| B10-16 | 拉取镜像包占容器启动时间 76%，只读其中 6.4% | 懒加载的奠基观察 | Slacker（FAST'16） | [Slacker][slacker] 摘要 | 论文自述 | 2016 | 高 | 摘要原句："pulling packages accounts for 76% of container start time, but only 6.4% of that data is read"（两次回原文核对一致）；机制（集中式 NFS 存储、NFS 文件作虚拟块设备）出自正文；已移出 X-26 | 10 |
| B10-17 | 1.3 GB 镜像冷拉取 20 s → 2.8 s（7.4×）、2.5 GB 镜像 9.3×；访问密度低于约 80% 时懒加载占优；SOCI 部署于 EKS 与 ECS Fargate，Fargate 在 Prime Day 2025 期间每天启动 1,840 万个任务 | 无需转换 OCI 的懒加载 | Seekable OCI（Amazon） | [arXiv 2607.06868][soci] | 论文自述 | 2026-07-07 | 高 | 1,840 万是 ECS Fargate 当日启动的任务总数（原文 "Amazon ECS Fargate (which launched 18.4 million tasks per day during Prime Day 2025)"），不是 SOCI 处理的任务数；日期 2026-07-07 未单独核对 | 10 |
| B10-18 | 冷启动最多快 23×（对全镜像）、4.6×（对现有懒加载） | 运行时镜像 | FlacIO（华为，FAST'25） | [FlacIO][flacio] | 论文自述 | 2025 | 高 | — | 10 |
| B10-19 | 从 250 MB 代码包（2015）到 10 GiB 容器镜像（2020）；单客户每秒新增多达 15,000 个容器；启动低至 50 ms | 按需加载的生产先例 | AWS Lambda（ATC'23） | [On-demand Container Loading in AWS Lambda][lambda-atc] 摘要 | 论文自述 | 2023 | 高 | 摘要已核对；250 MB 指代码包，不是镜像；单位为 GiB | 10 |
| B10-20 | 1,000 台主机 4 秒内冷启动 10,000 个容器 | 块级按需镜像的扩容能力 | DADI（阿里，ATC'20） | [DADI][dadi] 摘要 | 论文自述 | 2020 | 高 | 摘要未说明是否同一镜像 | 10 |
| B10-21 | 镜像缓存容量预算 100 GB；高/低水位线 0.95/0.70；LRU 最短闲置 600 s；registryfs_v2 远端块缓存上限 100 GiB | 本地有界缓存默认值 | AgentENV | [AgentENV 配置参考][aenv]（HEAD 00351e2） | 一手文档 | 2026-10-01 | 高 | 开源默认值，非 Moonshot 生产配置 | 10, 25 |
| B10-22 | `download_enable` 默认 false；内存快照远端层后台下载默认开启，块大小 16 MiB、每层并发 4、`max_inflight_blocks` 16 | 后台下载默认值 | AgentENV | 同上，`[ublk.overlaybd]` 与 `[memory_snapshot.background_download]` 小节 | 一手文档 | 2026-10-01 | 高 | 16 MiB 与"有界工作集"一句只适用于内存快照层，不适用于镜像层 | 10, 11, 25 |
| B10-23 | P2P 查找超时 300 ms；区间读取超时 2,000 ms；"Experimental: P2P has not been tested in production" | P2P 门面默认值与成熟度 | AgentENV | 同上，`[ublk.overlaybd]` 与 `[p2p]` 小节 | 一手文档 | 2026-10-01 | 高 | 与 K3 报告"采用 P2P 传输"存在张力（C-34）；查找超时按可缓存的未命中处理 | 10, 25 |
| B10-24 | 约 38 倍 | 一周活跃制品（> 130 TB）与 microVM 评测节点本地存储（3.4 TB）之比 | DSec | 由 B03-07、B10-09 推算 | 笔者推算 | 2026-09-19 | 中 | 前提：生产节点存储配置与评测节点相近（论文未说明） | 10 |
| B10-25 | 约 1.1 GB | 12.1 GB Java 镜像的运行时读取量（12.1 × 9.2%） | DSec | 由 B03-09 推算 | 笔者推算 | 2026-09-19 | 中 | — | 10 |
| B10-26 | 约 900 GB | 冷态预拉取比按需每节点多写的量（1,600 − 700） | DSec | 由 B10-07 推算 | 笔者推算 | 2026-09-19 | 中 | 1,600 为"超过"，结果为下限近似 | 10 |

### 第 11 章　沙箱内状态：快照、fork 与检查点

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B11-01 | 启动/恢复 < 50 ms；暂停 < 100 ms；增量快照 < 100 ms（"即使大量磁盘修改"） | README 声明 | AgentENV | [AgentENV README][aenv-readme] | 厂商自报 | 2026-07-25 起 | 中 | 与 K3 报告 133/49 ms 口径不同，见 C-03 | 11, 25 |
| B11-02 | 检查点最低 133 ms；恢复最低 49 ms | 增量检查点/恢复（K3 §5.3.2，'as low as'；原文未说明测量条件） | Kimi K3 / AgentENV | [Kimi K3 技术报告][k3] | 论文自述 | 2026-07 | 高 | "as low as"，是下界而非典型值 | 11, 25 |
| B11-03 | fork `count` 1–100（代码与 OpenAPI，自 2026-07-25 首版起）；首版文档误写 16（提交 f57e9c6 更正，作者日期 2026-08-24，提交日期 08-26） | `POST /sandboxes/{id}/fork` 的 count 上限（同节点） | AgentENV | [AgentENV 文档][aenv]（`src/api/openapi.yml`、`src/api/generated/src/models.rs`）；[MarkTechPost][mtp] | 一手文档 | 2026-07-25 → 2026-08-26（f57e9c6 合入；作者日期 08-24） | 高 | 文档与代码不一致，已解决（C-02） | 11, 25 |
| B11-04 | 约 3 s（约 2 s 快照 + 约 1 s 恢复）；默认空闲 15 分钟自动暂停；会话上限 1 h（Base）/24 h（Pro） | 暂停/恢复与会话限制（512 MiB 沙箱；同文另称约每 GiB 内存 4 s） | E2B | [bex.co 2026-09-06][bex-e2b] | 二手报道 | 2026-09-06 | 中 | 第三方分析；"默认空闲 15 分钟自动暂停"与 E2B 一手文档（默认超时即终止，onTimeout 需显式设为 pause）及规范（autoPause 默认 false；timeout 默认 v2 300 s、v1 15 s）不一致，见 C-41；E2B 文档自称暂停约每 GB 4 s、恢复约 1 s，见 B16-11 | 11, 21, 22 |
| B11-05 | 约 14 ms 检查点；约 5 ms 回滚 | DeltaFS + DeltaCR；摘要口径（v1/v2 相同） | DeltaBox（上交 IPADS） | [arXiv 2605.22781][deltabox] | 论文自述 | 2026-05-21 | 高 | v2 正文表 2 另给每事件平均：检查点本地工作 10.83 ms（与推理重叠，Agent 感知阻塞为 0）、快路径恢复 1.86 ms、慢路径 9.29 ms；与摘要的对应关系论文未说明，引用时并列（B11-18） | 11 |
| B11-06 | 分支创建 < 350 µs（与文件系统大小无关）；小改动提交 < 1 ms（1 KB 317 µs、1 MB 2.1 ms，表 5）；透传读 7,236 MB/s（原生的 82%；原生 8,800 MB/s、普通 FUSE 1,655 MB/s 即 19%，表 6） | BranchFS（FUSE 实现）；`branch()` 仅为未实现的设计提案 | Fork, Explore, Commit | [arXiv 2602.08199][branchfs] | 论文自述 | 2026（AgenticOS'26） | 高 | — | 11 |
| B11-07 | 恢复正确率 8% → 100%；检查点流量最多减少 87%；开销 ≤ 1.9% | 语义感知 C/R | Crab（港科大） | [arXiv 2604.28138][crab] | 论文自述 | 2026-04-30 | 高 | §7.2：Terminal-Bench 上仅对话 8%–13%，对话+文件系统 28%（Claude Code）/42%（iFlow CLI），SWE-bench 上对话+文件系统 100%；§3.1 动机实验中的 6%/28% 是 replay/在线 LLM 两种模式，不是评测范围 | 11 |
| B11-08 | 成功率 62.2% → 87.8%（GPT-5.4）；MettleBench 82 个任务 | 上下文与工作区检查点对齐 | AgentRewind | [arXiv 2608.14380][agentrewind] | 论文自述 | 2026-08-14（v1） | 高 | 已回 arXiv HTML 核对；640 条验收标准；mini-SWE-agent + GPT-5.4 | 11 |
| B11-09 | 最多提升 6.57 个百分点 | 回滚后保留反思 | RIR（Rollback the World, Keep the Reflection） | [arXiv 2609.18304][rir] | 论文自述 | 2026-09 | 高 | RIR v1 HTML 复核："improving average success rate by up to 6.57 percentage points"（三个长程基准、两个 LLM 底座）；作者 Yi Yu, Liuyi Yao, Yaliang Li, Enshu Wang, Libing Wu（武汉大学 / 阿里巴巴），2026-09-22；基准名称未摘到 | 11, 12 |
| B11-10 | 挂起/恢复 25 ms；可空闲"数月"成本接近零 | 挂起延迟 | Blaxel | [The Next Web][tnw-blaxel] | 二手报道 | 2026-09-10 | 中 | 厂商宣称；BusinessWire 称启动与恢复比竞品快 5 倍；未核实 | 11, 22 |
| B11-11 | 检查点/恢复约 300 ms（Better Stack，2026-03-09）；启动 1–12 s（Techzine）vs 创建 1–2 s（Better Stack） | 持久化 Firecracker VM | Fly.io Sprites | [Better Stack][betterstack]；[Techzine][techzine] | 二手报道 | 2026-01/03 | 中 | 两个二手来源的启动口径不一致，应并列 | 11, 22 |
| B11-12 | 快照恢复约 2 s；克隆仓库并 npm install 约 30 s | R2 快照 | Cloudflare Sandbox | [Cloudflare 博客][cf-blog] | 厂商自报 | 2026-04-13 | 中 | 2026-10-04 回 Cloudflare Sandbox GA 博客核实两数；回原文核对后更正口径：约 30 s 是克隆仓库加 npm install 的工作流耗时，不是容器冷启动；约 2 s 是从 R2 备份恢复；未见容器冷启动数字（C-46） | 11, 22 |
| B11-13 | 约 500 ms 快照恢复；2.7 s 冷启动；约 $0.089/vCPU-h | Together Code Sandbox | Together / CodeSandbox | [Northflank 对比][northflank] | 二手报道（竞品） | 2026-01-17 | 低 | 竞品撰写 | 11, 22 |
| B11-14 | "3 ms fork"；亚毫秒 CoW VM fork | VM fork 宣称 | Kedge；forkd | [bex.co on Kedge][bex-kedge]；[forkd][forkd] | 二手报道 | 2026-08 | 低 | 仅见标题，未核实；不宜作为事实 | 11 |
| B11-15 | 16 MiB 不可变块 | NBD + CoW 块快照粒度（GCS 后端） | Replit Snapshot Engine | [Replit 博客][replit] | 一手文档 | 未标日期 | 高 | — | 11, 21 |
| B11-16 | 2024-11-19 | 运行中 VM 快照与分叉（Infinibranch）上线 | Morph Cloud | [Morph 博客][morph-infini] | 厂商自报 | 2024-11-19 | 中 | 无延迟数字 | 11 |
| B11-17 | 128 GB pmem 设备需 2 GB guest 内存 | struct page 元数据开销 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 放在第 13 章讨论 | 11, 13 |
| B11-18 | 10.83 ms；1.86 ms；9.29 ms；Agent 感知阻塞 0 | DeltaBox 表 2：检查点本地工作、快路径恢复、慢路径恢复（每事件平均） | DeltaBox | [arXiv 2605.22781v2][deltabox] 表 2 | 论文自述 | 2026-06-08 | 高 | 与 B11-05 并列 | 11 |
| B11-19 | 347/27,694；622.3/3,429；590/811.4；524.4/899.7 ms | DeltaBox 表 2 基线（复制+重放；FC 差量+dm-snapshot；CRIU+复制；E2B 增量）检查点/恢复 | DeltaBox | [arXiv 2605.22781v2][deltabox] 表 2 | 论文自述 | 2026-06-08 | 高 | E2B 为 DeltaBox 在自身环境中测得 | 11 |
| B11-20 | 约 480×（论文）；约 48×（笔者推算，524.4 ÷ 10.83） | E2B（增量）相对 DeltaBox 的恢复倍数；检查点倍数 | DeltaBox | [arXiv 2605.22781v2][deltabox] 表 2 | 论文自述；笔者推算 | 2026-06-08 | 高 | 48× 不代表 Agent 感知差距 | 11 |
| B11-21 | 0.57 → 5.47 ms（p50，N=1 → 64）；p99 14.74 ms；约 11 MB/子实例；预热模板约 15 MB RSS | DeltaBox fork 扇出（表 3） | DeltaBox | [arXiv 2605.22781v2][deltabox] 表 3 | 论文自述 | 2026-06-08 | 高 | — | 11 |
| B11-22 | 1.01–1.02× vs 1.30–1.93×；1%–2% vs 23%–48% | 30 次迭代 MCTS 归一化耗时；状态管理占比（DeltaBox vs E2B 增量） | DeltaBox | [arXiv 2605.22781v2][deltabox] | 论文自述 | 2026-06-08 | 高 | — | 11 |
| B11-23 | 超过 75%；最多 87% | 无恢复相关状态的轮次比例；被判定无需检查点的轮次比例 | Crab（港科大） | [arXiv 2604.28138][crab] 摘要与正文 | 论文自述 | 2026-04-30 | 高 | — | 11 |
| B11-24 | 0.1/0.7/1.0 s；20–100 ms；0.44%（64 沙箱） | Crab 检查点中位/P95/P99；仅文件系统；P95 暴露延迟占任务时间 | Crab（港科大） | [arXiv 2604.28138][crab] §7.3 | 论文自述 | 2026-04-30 | 高 | — | 11 |
| B11-25 | 1.67×；3.78×（96 沙箱密度） | 重启基线（SWE-bench）、逐轮完整检查点（Terminal-Bench）最大开销 | Crab（港科大） | [arXiv 2604.28138][crab] 评测 | 论文自述 | 2026-04-30 | 高 | — | 11 |
| B11-26 | 29%（QEMU 启动案例，434 s → 307 s）；36%（回滚 token）；0.71/1.00 s；0.45%–3.01%（1–5 次抢占）；40.0%–64.2% | Crab 案例：回滚工具；spot 迁移；抢占开销；RL rollout token | Crab（港科大） | [arXiv 2604.28138][crab] §7.5 等 | 论文自述 | 2026-04-30 | 高 | 29% 为单个案例，不写"最多" | 11, 28 |
| B11-27 | "cross-node resume"（无延迟数字） | AgentENV 发布快照时压缩内存层与增量读写层以减少跨节点恢复网络字节；共享快照仓库时须在同模式节点恢复 | AgentENV | [AgentENV 文档][aenv]：`docs/src/configuration/reference.md`（`[snapshot.publish_compression]`，该表述首见于提交 e83b1e7（作者日期 09-07，2026-09-08 合入））、`docs/src/deployment/pvm.md` | 一手文档 | 2026-09 | 高 | 跨节点**冷恢复**已披露；跨节点 fork 与在线迁移仍未披露 | 11, 25 |
| B11-28 | 40%；68%；2.5 千行 C；6.2 千行 Rust | YoloFS：不可逆损害比例；Agent 未察觉比例；实现规模 | YoloFS（SOSP'26） | [arXiv 2604.13536v2][yolofs] | 论文自述 | 2026-04-16 | 高 | — | 11, 12 |
| B11-29 | 每次检查点写放大 O(4 KB)；评测服务器 4 路 96 核、760 GB 内存；microVM 4 vCPU / 8 GB | DeltaBox 写放大量级与评测环境 | DeltaBox | [arXiv 2605.22781v2][deltabox] 正文 | 论文自述 | 2026-06-08 | 中 | 据 v2 HTML 正文摘录，未逐字复核；被 fork 的预热模板常驻内存约 15 MB 见 B11-21 | 11 |

### 第 12 章　沙箱外副作用与回滚语义

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B12-01 | 任务质量最多提升 15×；用户错误恢复开销 3% | statepoint（本地快照 + 远端补偿动作） | Planarian | [arXiv 2609.35366][planarian] | 论文自述 | 2026-09-28 | 高 | 机构据 alphaXiv 页面：帝国理工学院、印度科学理工学院（IISc）、微软，页面无逐人对应（PDF 作者块未读）；正文未读（arXiv 限流），补偿动作的来源、不可逆动作处理、远端 fork 语义均未核实；2026-10-05 第 28 章回 alphaXiv 摘要页复核"improving task quality by up to 15x, and allows users to recover from erroneous actions with only 3% overhead" | 11, 12, 28 |
| B12-02 | v1：30% 每调用故障注入下 Tx-Full 成功率 37–57%（立即生效基线 0–7%，WebArena/OSWorld）；不可逆效果泄漏 0/1,200 封邮件（No-Tx 1,200/1,200，CR 因重试重复 1,351）；簿记开销 < 0.01% 墙钟（工具延迟 100 ms–10 s） | 进度感知事务 | Atomix | [arXiv 2602.14849][atomix] | 论文自述 | 2026-02-16（v1） | 高 | v2（2026-05-29）主实验与数字不同，见 B12-08、B12-09 与 C-52；v2 不再出现"0.01%"，改称"微秒级包装开销"；引用须注明版本；v1 泄漏为 0/1,200 封邮件；No-Tx 1,200/1,200；CR 1,351（重试重复） | 12, 28 |
| B12-03 | KramaBench 总分 74.6%（Claude Code 64.0%，二者同为 Qwen3.5-397B-A17B 底座）；原文"高出 10.6%"实为 10.6 个百分点（笔者推算）；代码步骤 22.8 对 9.4，单任务成本 0.10 对 0.08 美元，token 348K 对 405K | ACID 语义的数据 Agent | Agentic Transaction（清华） | [arXiv 2608.13900][agentictx] | 论文自述 | 2026-08-14 | 高 | 作者块三人均列清华（Xiaoxiao Wang 邮箱为康奈尔域名，alphaXiv 标康奈尔）；2026-08-14；只在数据 Agent 上验证；正文称 token 更多而表中更少，内部不一致；skill hub 与补偿为设想（"We envision"），未评测 | 12 |
| B12-04 | 每事务约 1.82 s（14.5% 开销）；拦截 100%、回滚 100% | 策略拦截 + 文件系统事务（原型用文件级复制，非 ZFS 快照） | Fault-Tolerant Sandboxing（单作者） | [arXiv 2512.12806][fts] | 论文自述 | 2025-12 | 中 | 作者单位弗吉尼亚大学（论文作者块）；§6.3 原文"≈1.82s (14.5%)"，主要为复制 250 MB 工作区的 I/O；§5.1：卷以 ZFS 为后端，但"当前原型为可移植性使用文件系统级复制"，即不是 ZFS 快照；Proxmox 测试床、Minimind-MoE；§6.3 直接执行基线 4.69 s，1.82 ÷ 4.69 ≈ 38.8%，与 14.5% 不符（笔者推算），论文内部不一致；§7.5 明言 HTTP 请求无法经文件系统快照撤回 | 11, 12 |
| B12-05 | 290 份误操作报告、13 个框架；11 个"不透明"任务中 8 个自纠，3 个的破坏在提交前交由用户审查（user-reviewable before commit）；112 项常规操作成功率 99%；每任务 0.4 次交互（Claude 0.9、Copilot 1.3、Gemini 2.2） | staging/快照/渐进权限 | YoloFS（SOSP'26） | [arXiv 2604.13536][yolofs] | 论文自述 | 2026-04-16 | 高 | SOSP'26 录用清单题名为"Information and Control in Agent-Native Filesystems"，与 arXiv 题名不同 | 11, 12, 28 |
| B12-06 | 4 个确定性挑战、20 组配对文件挑战；36 次运行（仅见二手书目信息，摘要未见，未核实） | 可恢复性契约的小规模研究 | Recoverability as a System Primitive | [arXiv 2609.13672][recoverability] | 论文自述 | 2026-09 | 中 | 概念性论文；作者机构 alphaXiv 列北京信息科技大学，另一书目来源记 Zhang 为独立研究者，并列（C-53） | 12 |
| B12-07 | 123 项回归测试 | Agent libOS 的唯一验证 | Agent libOS | [arXiv 2606.03895][agentlibos] | 论文自述 | 2026-06 | 高 | 无基准对比；原文"They do not claim to roll back irreversible external effects"，外部效果"must be represented as audit events and, when needed, compensated explicitly"；人工审批为 WAITING_HUMAN 阻塞原语 | 12 |
| B12-08 | 57%（17/30）；0–7%；53%（16/30，Fisher p=1.0） | v2：τ-bench retail（GPT-4.1，max_steps 30，N=30）30% 故障概率下 Tx-Full 干净成功率、基线、Checkpoint-Replay | Atomix v2 | [arXiv 2602.14849v2](https://arxiv.org/html/2602.14849v2) §3.2、图 2 | 论文自述 | 2026-05-29 | 高 | 与 v1 的 37–57%（WebArena/OSWorld）并列，不可混用（C-52）；10% 故障结果仅见图 2，正文无数字，不登记 | 12 |
| B12-09 | 0/500（95% CI 0–0.74%）；TCC-Confirm、Mutex+WAL+Rollback 亦为 0；80%；40%；17 / 50 / 30 LOC | v2：500 次无效发送的不可逆效果泄漏；Saga-Compensation、Checkpoint-Replay 泄漏率；每适配器声明代码量（Atomix / TCC / Mutex+WAL+Rollback） | Atomix v2 | [arXiv 2602.14849v2](https://arxiv.org/html/2602.14849v2) 表 2、附录 C.3 | 论文自述 | 2026-05-29 | 高 | 局限：单进程，"不声称分布式崩溃安全的恰好一次"；元数据准确性安全攸关 | 12, 28 |
| B12-10 | 45/45；14；26；5 | Cordon 在 45 个自建风险工作流上提交前拦截数；从现有防御派生的适配器拦截、漏掉、提交后发现数 | Cordon | [arXiv 2606.17573v1][cordon] §6.2、图 5 | 论文自述 | 2026-06-16 | 高 | 风险集为作者自建（9 类边界 × 5 类风险）；对比为"派生适配器"而非原始实现；模型 DeepSeek-V4-Pro，"commercial Agent-H framework" | 12, 28 |
| B12-11 | 25.55 s；23.64 s；31.35 s；31.12 s；162 → 119–127 次；token 降 23.6%–28.4%；22.2%–23.4% | Cordon 平均任务时间（Plain / Reject-on-Risk / Approve-All / Mixed）；LLM 调用；token；不含审批等待时事务控制路径占比（模型服务 62.3%–63.6%，Agent/工具 14.2%–14.4%） | Cordon | [arXiv 2606.17573v1][cordon] §6.3、表 4、图 9 | 论文自述 | 2026-06-16 | 高 | — | 12 |
| B12-12 | 4.17 ms；178.95 ms；0；15/15；2.9%；git reset+clean 21.74 ms、12/15；git restore/reset 残留差异中位数 73 | Cordon 回滚中位、恢复中位（失败步 + 回滚 + 续跑检查）、残留差异、续跑通过数、回滚原语时间占比；git 基线 | Cordon | [arXiv 2606.17573v1][cordon] §6.3、表 5 | 论文自述 | 2026-06-16 | 高 | 5 条确定性轨迹共 15 次试验；残留为文件系统差异数的中位数 | 12, 28 |
| B12-13 | τ-bench 87.5% → 90.0%；Terminal-Bench 100.0% → 100.0%；约 14.4 KLOC + 3.9 KLOC | Cordon 良性任务正确性；运行时与基准驱动代码量 | Cordon | [arXiv 2606.17573v1][cordon] §6.4、表 6、§5 | 论文自述 | 2026-06-16 | 高 | 论文称"within measurement variance" | 12 |
| B12-14 | 88.9 ± 18.6；63.9 ± 30.9 | Agentic Transaction 与 Claude Code 在 KramaBench Environment 领域三次运行的任务级得分 | Agentic Transaction | [arXiv 2608.13900v1](https://arxiv.org/html/2608.13900v1) | 论文自述 | 2026-08-14 | 高 | — | 12 |
| B12-15 | 10/10（无检查点 0/10）；2/2 | ACRFence：检查点恢复后重复提交；无状态校验下令牌复用成功（有状态吊销列表下全部被拒） | ACRFence | [arXiv 2603.20625v1][acrfence] §3 | 论文自述 | 2026-03-21 | 高 | 评测只验证攻击，防御 ACRFence 尚未实现；CoDAIM 2026（ASPLOS'26 研讨会）日程已列，2026-10-06 核实 | 12, 28 |

### 第 13 章　密度与资源管理

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B13-01 | 每节点稳定运行至少 3,200 个容器或 800 个 microVM | 生产中观测到的每节点稳定运行上限（原文为 observed） | DSec | [DSec][dsec] §4.3 | 论文自述 | 2026-09-19 | 高 | §1 是否另有此数，两次抓取结果矛盾，暂不引用 §1 | 5, 13, 24, 28 |
| B13-02 | 单日单节点峰值 1,048 个容器、524 个 microVM | 观测峰值 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 与 B13-01 不矛盾（能力 vs 观测） | 13, 24 |
| B13-03 | 平均每节点约 2,400 个沙箱（约 2,375）；每物理核约 12.7 个沙箱 | 380,000 ÷ 160；380,000 ÷ 30,000 | DSec | 由 B24-02、B24-05 推算 | 笔者推算 | 2026-09 | 中 | 峰值并发与节点数口径可能不同 | 13, 24 |
| B13-04 | 宿主峰值内存 −40.2%；瞬时峰值 CPU 26.5% → 41.4% | virtio-pmem + DAX | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 13, 24, 28 |
| B13-05 | 时间积分内存 −21.2%（峰值基本不变） | DAMON + balloon FPR | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 组合方案"最低"，论文未给具体数 | 13, 24 |
| B13-06 | order-9（4 KiB 基页下 2 MiB 区域） | FPR 默认上报粒度 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 13 |
| B13-07 | 50% BE 负载下无 QoS 每步延迟 +45.2%；仅 SCHED_IDLE 最多改善 3.4%；加 core scheduling 后限制在 +17.3% | CPU QoS（延迟敏感的下棋应用为 LS 负载；"每步固定时限"是 §4.3 对这类负载的一般描述） | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 45.2%→17.3% 约为膨胀幅度 2.6 倍缩减（笔者推算）；"7.4 倍改进"不得引用 | 13, 24 |
| B13-08 | 内存超售比最高 6.5×（真实负载） | 超售比（K3 报告口径；原文归因于"copy-on-write memory and page-cache optimizations"） | Kimi K3 / AgentENV | [Kimi K3 技术报告][k3] | 论文自述 | 2026-07（arXiv v1 2026-07-27，v2 2026-08-07；首见版本未核实） | 中 | 与 README 9.6× 冲突，且两者归因机制不同，C-01 | 13, 25 |
| B13-09 | 生产中 9.6× 内存超售比 | 超售比（README，提交 c561be6；原文归因于 memory ballooning） | AgentENV | [AgentENV README][aenv-readme] | 一手文档（厂商自报） | 2026-08-10 | 中 | bex.co 沿用；C-01 | 13, 25 |
| B13-10 | 沙箱自有内存（sandbox-owned memory）最多降 8.7×（Linux 配置 2.1×）；减速从 3.1× 降到 1.40× | LLM 等待期内存压缩 | AgentZip | [arXiv 2609.11294][agentzip] | 论文自述 | 2026-09-10 | 高 | arXiv 预印本，未注明会议 | 13, 28 |
| B13-11 | 对 E2B 类系统（评测基线为增强版 E2B+）：P99 延迟最多 −58%、内存 −61%；容器 P99 最多降 7×、内存省 48% | 可复用沙箱池 + mm-template | TrEnv-X | [arXiv 2509.09525][trenvx] | 论文自述 | ACM TOCS 44(3): 1–39，2026-07-27 在线、2026-08-31 印刷（Crossref），DOI 10.1145/3805475 | 高 | 超售实验为 20 个物理核上 200 个 Agent 实例 | 13, 25 |
| B13-12 | P99 端到端延迟最多降 2.9×；峰值内存比常驻预留低 45.9% | 意图驱动投机预热 | SpecBox | [arXiv 2607.23933][specbox] | 论文自述 | 2026-07-27 | 高 | — | 13 |
| B13-13 | HIGH 优先级 P95 内存分配延迟降 29%（70.97 → 50.14 ms） | 按工具调用边界的 cgroup 控制 | AgentCgroup | [AgentCgroup][agentcgroup] | 论文自述 | 2026-03-23 | 高 | 轨迹重放、三条轨迹并发；摘要称"初步评估"；2026-10-06 回 PDF 复核原句"reduces HIGH-priority P95 allocation latency by 29% (70.97→50.14 ms)"，本行已含"分配"二字，口径正确 | 13 |
| B13-14 | 端到端 2.2×（几何平均，相对 Firecracker） | CXL/RDMA 分层快照 | Aquifer | [pith 聚合页：arXiv 2606.24079][aquifer] | 论文自述 | 2026-06-23 | 低 | 仅在模拟硬件上评估；经聚合页读取 | 11, 13 |
| B13-15 | 默认占宿主 50% 内存 | Docker Sandboxes（sbx）本地 microVM 内存默认值 | Docker sbx | [Vaughan 对比][vaughan] | 二手报道 | 2026-04-24 | 中 | — | 13, 21 |
| B13-16 | 128 GB 按峰值分配仅支撑 32–64 个实例；CPU < 36% | 按峰值预留的算例 | AgentCgroup | [AgentCgroup][agentcgroup] | 论文自述 | 2026-03-23 | 高 | 平均 CPU 利用率 13.2%/7.6% 见 B03-16 | 13 |
| B13-17 | 1/64（128 GB pmem → 2 GB guest 内存） | struct page 元数据占 pmem 容量比例 | DSec | [DSec][dsec] §5.2 | 论文自述 | 2026-09-19 | 高 | 与 B11-17 同源 | 13 |
| B13-18 | 20 个物理核上并发 200 个 Agent 实例（每核 10 个）；轻量实例 1 vCPU / 2 GB / 5 GB，带浏览器 4 GB | 超售实验设定 | TrEnv-X | [arXiv 2509.09525v2][trenvx] §9.6 | 论文自述（每核数为笔者推算） | 2026 | 高 | 实验设定，不是生产密度 | 13 |
| B13-19 | 每沙箱开销 < 5 MB（规格 ≤ 32 GB 下测得）；"单台服务器数千个"；约 20.8 个/核（2,000 ÷ 96） | CubeSandbox 密度 | 腾讯 CubeSandbox | [GitHub][cube-gh]；[腾讯云开发者社区][cube-dev] | 厂商自报；笔者推算 | 2026-10-02 读取 | 中 | 与 B06-16 同源；每核数机器内存未知 | 13 |
| B13-20 | 约 488 MB / 容器；约 1.95 GB / microVM | DSec 每节点平均内存（约 1.56 TB）÷ 3,200 与 ÷ 800 | DSec | 由 B24-05、B24-02、B13-01 推算 | 笔者推算 | 2026-10 | 中 | 第 24 章用评测节点 1.5 TB 得 1.9 GB（B24-18），两种算法基数不同 | 5, 13 |
| B13-21 | 约 390–780 个；约 4.1–8.2× | 按 AgentCgroup 2–4 GB 峰值预留时 DSec 节点的容量；3,200 个对应的峰值超售倍数 | DSec × AgentCgroup | 由 B13-20、B03-13 推算 | 笔者推算 | 2026-10 | 低 | 跨系统混用，仅示量级 | 13 |
| B13-22 | 4×；2× | DSec 容器与 microVM 的能力比、单日观测峰值比 | DSec | 由 B13-01、B13-02 推算 | 笔者推算 | 2026-10 | 高 | — | 13 |
| B13-23 | 约 182 ms | K3 检查点 + 恢复最低往返（133 + 49） | Kimi K3 / AgentENV | 由 C-03 推算 | 笔者推算 | 2026-10 | 中 | 最低值之和，不是典型值 | 11, 13 |
| B13-24 | 约 2% | 等待占寿命 98% 且每次等待都暂停时，同时活跃数占同时存在数的理论上界 | Kimi K3 | 由 B03-10 推算 | 笔者推算 | 2026-10 | 低 | 理论上界 | 13 |
| B13-25 | 约 $0.101 + $0.065 = $0.166/h；内存约 39% | E2B 默认 2 vCPU / 4 GiB 每小时费用构成 | E2B | 由 B22-03 推算 | 笔者推算 | 2026-10 | 中 | 与 bex.co 2026-09-22 的 $0.166/h 一致 | 13, 22 |
| B13-26 | 约 ¥0.58 + ¥0.36；内存约 38% | 腾讯 AGS 2 核 4 GiB 每小时费用构成 | 腾讯 AGS | 由 B22-40 推算 | 笔者推算 | 2026-10 | 中 | 假设一小时内资源全部计费 | 13, 22 |
| B13-27 | 约 2.5×；约 39.4% | Vercel 活跃 vCPU 单价 ÷ E2B vCPU 单价；CPU 项盈亏平衡活跃比例 | Vercel / E2B | 由 B22-17、B22-03 推算 | 笔者推算 | 2026-10 | 低 | 忽略内存（Vercel 另收预置内存）与其他计费项 | 13, 22 |
| B13-28 | 暂停后 CPU、内存停止计费，系统盘持续计费；"按实际使用量结算" | 腾讯 AGS 暂停计费规则 | 腾讯云 AGS | [腾讯云计费文档][ags-price] | 一手文档 | 2026-09-09 | 高 | — | 13, 22 |
| B13-29 | v0.5 AutoPause/AutoResume；v0.7.0（2026-08-28）跨节点暂停/恢复（S3 后端，预览） | CubeSandbox 暂停能力 | 腾讯 CubeSandbox | [GitHub][cube-gh] | 一手文档 | 2026-08-28 | 高 | 关联 C-11 | 11, 13 |
| B13-30 | `amount_mib = 0`；`free_page_reporting: Some(true)`；`deflate_on_oom = true` | AgentENV balloon 配置（只开 FPR，不做目标充气）；另默认 guest 内核开启 DAMON_RECLAIM（damon_reclaim.enabled=Y、skip_anon=Y，只回收文件页；config/default.toml，自 8f028b1 起；746f49b 于 2026-09-15 合入调参） | AgentENV | [AgentENV][aenv] 源码 src/sandbox/firecracker/instance.rs（HEAD 7e56ce8） | 一手文档 | 2026-09-29 | 高 | 生产配置是否相同未披露；DAMON 不是 DSec 独有 | 13, 25 |
| B13-31 | 10%–50% | DSec CPU QoS 实验中 BE 负载占节点容量 | DSec | [DSec][dsec] §8.5 | 论文自述 | 2026-09-19 | 高 | — | 13, 24 |

### 第 14 章　网络与出站

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B14-01 | 约 70 个域名（页面未给总数，转录计数） | Codex cloud "Common dependencies"白名单预设 | OpenAI Codex cloud | [Codex internet access 文档][codex-net] | 一手文档 | 2026-10-03 读取 | 中 | 页面只有逐行列表、未写总数；2026-10-03 转录计得 71 个，同日几次抓取所得为 60–76 个（第 14、15、18 章），2026-09-30 据页面摘要记为"约 80"，均为网页读取所得；列表含 github.com、githubusercontent.com、google.com、goproxy.io、azure.com，未见 azure.net；页面现标"Legacy"；见 C-36 | 14, 15, 18, 21 |
| B14-02 | 3 种方法（GET/HEAD/OPTIONS） | 可选的只读方法限制 | OpenAI Codex cloud | [Codex internet access][codex-net] | 一手文档 | 2026 | 高 | 挡不住经查询字符串的 GET 外传（推断） | 14, 15 |
| B14-03 | `{"npm": False, "pypi": True}` | 按包管理器开关的网络规则示例 | DSec libdsec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 已逐字核对 §2.1 代码清单：`memory_limit_mb=4096`、`cpu_cores_limit=4`、`ttl_running_stop=300`（idle timeout）、`network_rules={"npm": False, "pypi": True}`、`init_user="root"` | 2, 14, 16, 24 |
| B14-04 | CVSS 7.5；2025-09-01 报告；2025-11-01 部署修复、2025-11-17 以"other factors"回滚；2025-12-23 决定不修复、改文档（Sandbox 模式改称"limited external network access"）；2026-03-16 公开披露；2026-04-15 修复 DNS 隧道 | Sandbox 模式下 DNS 外传与反弹 shell | AWS Bedrock AgentCore Code Interpreter | [BeyondTrust][beyondtrust] | 一手文档（研究方披露） | 2026-03-16 | 高 | AWS 起初称预期行为 | 14 |
| B14-05 | 169.254.169.254 | SSRF 典型目标（云元数据地址） | MCP 规范 2025-11-25 | [MCP Security Best Practices][mcp-spec] | 一手文档 | 2025-11-25 | 高 | — | 14, 16 |
| B14-06 | 3 档（public / allowlist / no-network） | Harbor `network_mode` 取值 | Harbor | [Harbor config.py][harbor-cfg]；[loom issue #2189][loom] | 一手文档（源码）；二手报道（第三方 issue） | 2026-10-03 读取 / 2026-09-25 | 高 | Harbor 源码已对照（2026-10-03）：默认值 public；`[agent]`/`[verifier]` 可分阶段覆盖；旧字段 allow_internet 已弃用（loom 所述 allow_internet=false/true 映射为 no-network/public）；Loom 把 quality-1k、terminal-lego、terminal-world 各 20 个、共 60 个任务一律按 gateway-only 运行；另见 B20-24 | 14, 16, 20 |
| B14-07 | 本地版 3 档（Open / Balanced / Locked Down，二手）；云端预设 3 个（allow-all / balanced / deny-all，一手） | Docker sbx 网络档位 | Docker Sandboxes | [Vaughan][vaughan]；Docker 文档 cloud network policy https://docs.docker.com/ai/sandboxes/cloud/network-policy/ 、governance/concepts https://docs.docker.com/ai/sandboxes/governance/concepts/ | 二手报道（本地三档）；一手文档（云端预设） | 2026-04-24 | 中 | 一手文档另写明：默认阻断全部出站 TCP；UDP 默认关闭；ICMP 阻断；DNS 经内部解析器执行策略；不支持 HTTP 方法与路径限制；组织治理启用后"only organization allow rules can grant access. Local and kit-defined deny rules still apply on top"（governance/concepts 页） | 14 |
| B14-08 | 2025-08（Month of AI Bugs）；Devin 08-06 至 08-08 | Rehberger 系列披露 | ChatGPT、Codex、Devin、OpenHands、Claude Code、Jules 等 | [Simon Willison 2025-08-15][simon-johann] | 二手报道 | 2025-08-15 | 中 | Codex 白名单当时含 `azure.net`（2025-08 状态）；2026-10-03 读取的预设中未见 azure.net | 14, 21 |
| B14-09 | 25 次成功 24 次 | 内部钓鱼式 prompt 窃取凭据测试 | Anthropic | [How we contain Claude][anthropic-contain] | 一手文档 | 2026-05-25 | 高 | 该外传问题（借 api.anthropic.com 与攻击者 key）原文写明"came from a third-party disclosure"；25 中 24 为另一项内部钓鱼式提示测试 | 2, 14, 21 |
| B14-10 | 默认 60080–60089 | sandbox-runtime Windows 代理端口范围（WFP 仅放行到此范围的回环连接） | Anthropic sandbox-runtime | [sandbox-runtime README][srt] | 一手文档 | 2026-10-03 读取 | 高 | 版本见 B04-03 | 14 |
| B14-11 | Linux 5.19 | `IORING_OP_SOCKET` 可绕开 `socket()` 规则的起始版本；srt 因此阻断 io_uring 三个系统调用 | Anthropic sandbox-runtime | [sandbox-runtime README][srt] | 一手文档 | 2026-10-03 读取 | 高 | — | 4, 14 |
| B14-12 | `@cloudflare/sandbox@0.8.9`；`@cloudflare/containers@0.3.0` | Outbound Workers（凭据注入、TLS 拦截）所需版本 | Cloudflare | [Cloudflare changelog](https://developers.cloudflare.com/changelog/post/2026-04-13-sandbox-outbound-workers-tls-auth/) | 一手文档 | 2026-04-13 | 高 | 另有 `setOutboundByHost()`（早先只记 `setOutboundHandler()`） | 14, 22 |
| B14-13 | 443 端口 | Modal 域名白名单（Beta）只允许到所列域名的 TLS 443 流量；按 SNI 匹配；不支持 ECH；默认允许访问任意公网 IP | Modal | [Modal sandbox networking](https://modal.com/docs/guide/sandbox-networking) | 一手文档 | 2026-10-03 读取 | 高 | 运行时改策略见 B14-16 | 14 |
| B14-14 | 80 端口（Host）/ 443 端口（SNI）；8.8.8.8 | E2B 域名过滤覆盖范围；使用域名规则时自动放行的默认解析器 | E2B | [E2B internet access](https://docs.e2b.dev/network/internet-access.md) | 一手文档 | 2026-10-03 读取 | 高 | 默认允许出站；allow 优先于 deny；`updateNetwork` 整体替换；QUIC/HTTP3 不支持域名过滤 | 14, 16 |
| B14-15 | `10.0.0.0/8`、`100.64.0.0/10`、`127.0.0.0/8`、`169.254.0.0/16`、`172.16.0.0/12`、`192.168.0.0/16` | AgentENV 节点级 `always_denied_cidrs` 默认值（先于每沙箱 allowOut/denyOut 安装） | AgentENV | [AgentENV][aenv] docs/src/configuration/reference.md（HEAD 00351e2） | 一手文档 | 2026-10-03 读取 | 高 | 运行时改写：`PUT /sandboxes/{sandboxID}/network`（openapi.yml）；沙箱出站默认策略见 B25-18 | 14, 25 |
| B14-16 | `_experimental_set_outbound_network_policy()`（Alpha） | 运行中修改 Sandbox 出站策略，白名单类型须在创建时已配置 | Modal | [Modal sandbox networking](https://modal.com/docs/guide/sandbox-networking) | 一手文档 | 2026-10-03 读取 | 中（摘要式读取） | — | 14, 22 |

### 第 15 章　包代理与供应链

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B15-01 | 5 月 12 日首次借 Artifactory 写"message board"；5 月 26 日经 SSRF 出站 | 包代理成为出站中继的起点 | OpenAI 内部模型 IM1（ExploitGym） | [OpenAI：The Hugging Face incident and the road ahead][openai-hf] | 一手文档（事故复盘） | 2026-08-26 | 高 | 完整时间线见 B19-20 与第 15 章表 15-1；一手 5 月 12 日条目写作"During a training run, an agent left an Artifactory note asking other agents for a missing file"；Wikipedia 的"5 月 8 日"不应引用 | 15, 19 |
| B15-02 | 恶意包公开约一小时；被 15 个真实系统下载并运行 | Mythos 5 发布到 PyPI 的恶意包 | Anthropic / Irregular 评测 | [Anthropic：Investigating incidents in cybersecurity evals][anthropic-incidents]；[InfoQ][infoq-anthropic]；[THN 2026-07][thn-anthropic-jul]；[BleepingComputer][bleeping-pypi] | 一手文档（事故页面） | 2026-07-30 | 高 | 一手原文："the package was made freely available online for roughly one hour. During that window, the package was downloaded and run on 15 real systems"；其一为"a scanner belonging to a real security company"；包被 PyPI 自身安全系统自动移除；一手原文："This attack was carried out by Claude Mythos 5."；受影响范围原文为"the real systems of three different organizations"；InfoQ/THN 2026-07 的"1 小时内被下载"为转述，THN 2026-09 后续报道未给数字；C-30 | 1, 12, 15, 20 |
| B15-03 | 440,445 个（19.7%） | 30 组测试生成的 223 万个包引用中被判定为幻觉的比例（分母为生成代码中的包引用，非"推荐包"；2024 年模型） | Spracklen et al. | [Spracklen et al., arXiv 2406.10279v3][spracklen] | 论文自述 | v1 2024-06-12，v3 2025-03-02；USENIX Security 2025 | 高 | 原文："…2.23 million packages…of which 440,445 (19.7%) were determined to be hallucinations, including 205,474 unique non-existent packages"；引用时须注明口径；X-13 已改为口径提示 | 15 |
| B15-04 | 9 个 Artifactory CVE（2026-07-27 修补） | ExploitGym 后的修补 | JFrog Artifactory | [Wikipedia][wiki-incident] | 二手报道 | 2026 | 低 | 仅 Wikipedia，未核实；一手复盘只写"notified JFrog of the token-refresh vulnerability"，未提 CVE 数 | 15, 19 |
| B15-05 | 14 个 | 07-10 一个 Agent 重建、验证并共享的公开暴露、带写权限的 HF 凭据数 | OpenAI（ExploitGym） | [OpenAI 事故复盘][openai-hf] | 一手文档 | 2026-08-26 | 高 | 摘录级 | 15, 19 |
| B15-06 | 07-05 | 开立安全事件、重建 Artifactory、留言板被清空；"留言板的存在及其意义对 7 月 5 日事件响应负责人并不明显" | OpenAI | [OpenAI 事故复盘][openai-hf] | 一手文档 | 2026-08-26 | 高 | 复盘正文，非时间线表 | 15, 19 |
| B15-07 | 141,006 次评测运行；3 起事件；6 次运行（其中 4 次影响同一组织）；三家组织 | Anthropic 复查的"Claude 可能获得互联网访问"的评测运行数，及识别出的事件数、运行数与受影响组织数 | Anthropic / Irregular | [Anthropic 事故页][anthropic-incidents] | 一手文档 | 2026-07-30 | 高 | 6 ÷ 141,006 ≈ 0.004%（笔者推算）；THN 2026-09 所称"第四起"不在此页，未核实；起因原文："Due to a misunderstanding between us and our evaluation partner, this was not the case, and internet access was available"，即 Anthropic 与 Irregular 之间的误解，不宜写成第三方单方误配置；其中一起由内部研究测试模型进行；时序：2026-07-23 开始复查并同日停止所有网络安全评测（"We began our transcript review on Thursday, July 23, and stopped all cyber evaluations the same day"），141,006 为该复查覆盖的运行数，不是"复查后才停止"；同页"misunderstanding"与"misconfiguration"两种措辞并存 | 1, 2, 15, 19, 20, 27, 28 |
| B15-08 | 576,000 个代码样本；16 个模型；30 组测试；223 万个包引用；205,474 个不同幻觉包名 | 幻觉包研究规模 | Spracklen 等 | [spracklen] | 论文自述 | 2025-03-02（v3） | 高 | — | 15 |
| B15-09 | 5.2%；21.7% | GPT 系列与开源模型的包幻觉率 | Spracklen 等 | [spracklen] | 论文自述 | 2025-03-02（v3） | 高 | — | 15 |
| B15-10 | 15.8%；21.3% | Python 与 JavaScript 代码的平均包幻觉率 | Spracklen 等 | [spracklen] | 论文自述 | 2025-03-02（v3） | 高 | — | 15 |
| B15-11 | 43%；58% | 在 10 次查询中全部重复 / 重复不止一次的幻觉包比例 | Spracklen 等 | [spracklen] | 论文自述 | 2025-03-02（v3） | 高 | 39% 在 10 次中完全不重复 | 15 |

### 第 16 章　API 与接口标准

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B16-01 | 7 家内置 provider（Blaxel、Cloudflare、Daytona、E2B、Modal、Runloop、Vercel） | Agents SDK 沙箱后端 | OpenAI Agents SDK | [OpenAI：The next evolution of the Agents SDK][openai-sdk] | 一手文档 | 2026-04-15 | 高 | — | 1, 16, 21, 22, 27 |
| B16-02 | 2025-12-09；10k+ MCP server；60k+ 项目使用 AGENTS.md；8 家白金会员 | Agentic AI Foundation 成立 | Linux Foundation | [Linux Foundation 新闻稿][aaif] | 一手文档 | 2025-12-09 | 高 | 成立时托管 MCP、goose、AGENTS.md 三项目；此后接纳 agentgateway（2026-06-04）、A2A（2026-08-17）与 Agent Router（2026-09-09），现共 6 个项目，均非沙箱规范（aaif.io；见 B16-15） | 16, 23 |
| B16-03 | 4,000+ 个 HF Hub Space | OpenEnv 生态规模 | OpenEnv | [HF：One sandbox per rollout][hf-rl] | 二手报道 | 2026-09-11 | 中 | 标签计数（"Over 4,000 Spaces carry the OpenEnv tag"），不等于可训练环境数；OpenEnv 2026-06-08 博文本身未给任何数量；2026-10-04 复核 | 16, 27 |
| B16-04 | 指导委员会 11 家（Meta-PyTorch、Reflection、Unsloth、Modal、Prime Intellect、NVIDIA、Mercor、Fleet AI、Microsoft、Hugging Face、RadixArk） | OpenEnv 治理 | OpenEnv | [HF OpenEnv 博文][openenv] | 一手文档 | 2026-06-08 | 高 | 同文另列支持者十余家（PyTorch Foundation、vLLM、SkyRL、Lightning AI、Axolotl、Stanford Scaling Intelligence Lab、Scale AI、Surge AI、Turing、Snorkel AI、SGLang、Miles 等）；摘录所得名单与其自述计数不一致，不引总数；仓库迁至 huggingface/OpenEnv；2026-10-04 复核 | 16, 27 |
| B16-05 | 端口 49983 | envd（由 tools-image/ 从 e2b-dev/infra 编译）在 guest 内端口 | AgentENV | AgentENV `config/default.toml`（control_plane_port = 49983）；`docs/src/concepts/authentication/secure-sandbox.md`；[MarkTechPost][mtp] 一致；E2B 规范 e2b-dev/infra `spec/openapi.yml`（HEAD 9219790）写明 envd 端口 49983 不能列为 httpsPorts | 一手文档 | 2026-07-27 | 高 | `thirdparty/envd/` 是节点侧经 gRPC 访问 envd 的 Rust 客户端库，不是 envd 源码 | 16, 25 |
| B16-06 | 296 个 MCP server；自动生成策略准确率 80.9% | MCP 访问控制 | AgentBound（FSE 2026） | [arXiv 2510.21236][agentbound] | 论文自述 | 2025-10 | 高 | 2026-10-05 第 28 章回 arXiv 摘要页复核：venue 为 FSE 2026；原句"show that access control policies can be generated automatically from source code with 80.9% accuracy" | 16, 28 |
| B16-07 | 超过 1,000 个社区环境 | NeMo Gym 可拉取的环境 | NVIDIA NeMo Gym | [NeMo Gym 文档][nemo] | 一手文档 | 2026 | 高 | 后端含 OpenSandbox、Apptainer、E2B、Docker、ECS Fargate（2026-10-04 复核，含后端清单、五个来源、训练框架 NeMo RL/Unsloth/veRL、harness OpenHands/mini-SWE-agent/LangGraph） | 16, 27 |
| B16-08 | 1 个环境变量（E2B_API_URL） | 从 E2B 迁移所需改动 | AgentENV；CubeSandbox（E2B_API_URL / E2B_API_KEY / CUBE_TEMPLATE_ID） | [AgentENV README][aenv-readme]；[腾讯云开发者社区][cube-dev] | 一手文档 / 厂商自报 | 2026 | 高 | CubeSandbox 两说并列：README_zh"替换一个环境变量"（一手）；腾讯云开发者社区列三个变量（厂商自报，未回原文核实）；README_zh Roadmap 写"补齐与 E2B 规范的剩余差距" | 1, 16, 25, 26 |
| B16-09 | `timeout` 默认 300 s（v2 `NewSandboxV2`，最小 1）；15 s（v1 `NewSandbox`，最小 0） | E2B 创建接口的沙箱存活时间默认值 | E2B | [e2b-dev/infra spec/openapi.yml](https://github.com/e2b-dev/infra) | 一手文档 | HEAD 9219790（2026-10-03） | 高 | 创建请求无 CPU/内存字段，资源随模板（`cpuCount`、`memoryMB`）；AgentENV 同名字段 `autoPause` 默认 true（BC-01）；CubeSandbox `timeout` 为空闲秒数（BC-02） | 16 |
| B16-10 | 24 h（Pro）；1 h（Base；persistence 页称 Hobby） | E2B 连续运行上限；暂停后恢复会重置该上限 | E2B | [E2B sandbox 文档](https://docs.e2b.dev/sandbox)；[persistence](https://docs.e2b.dev/sandbox/persistence) | 一手文档 | 2026-10-04 读取 | 高 | 与 B11-04（bex.co）一致；两页套餐名不同 | 16, 21 |
| B16-11 | 暂停约每 GiB 内存 4 s（原文"approximately 4 seconds per 1 GiB of RAM"）；恢复约 1 s；已暂停沙箱"无限期"保留、无 TTL | E2B 暂停/恢复耗时与保留策略 | E2B | [E2B persistence](https://docs.e2b.dev/sandbox/persistence) | 一手文档 | 2026-10-04 读取 | 高 | 与 B11-04 约 3 s 往返（512 MiB，二手）口径不同，见 C-31；bex.co 的"约每 GiB 4 s"与此同源 | 11, 16 |
| B16-12 | `count` 1–100（默认 1）；2026-07-15 写入规范，2026-07-21 changelog 公告 | E2B `POST /sandboxes/{sandboxID}/fork`：原地检查点后从同一快照创建 count 个新沙箱 | E2B | [e2b-dev/infra 提交 643d726（#3202）](https://github.com/e2b-dev/infra)；[E2B fork 文档](https://docs.e2b.dev/sandbox/fork)；[E2B changelog](https://e2b.dev/changelog) | 一手文档 | 2026-07-15 / 07-21 | 高 | 与 AgentENV fork 的路径与 1–100 上限一致（AgentENV 2026-07-25 首发时已有）；相隔 6–10 天，有意对齐与独立开发均可能（推断）；"E2B 没有 fork"的旧说法已过时 | 1, 11, 16, 25 |
| B16-13 | 2026-06-12（规范）；2026-08-24（changelog 公告"Bring Your Own Proxy"） | E2B 出站 SOCKS5 代理（`egressProxy`） | E2B | [e2b-dev/infra 提交 1fc3820（#2642）](https://github.com/e2b-dev/infra)；[E2B changelog](https://e2b.dev/changelog) | 一手文档 | 2026-06-12 / 08-24 | 高 | — | 14, 16 |
| B16-14 | 超过 365,000 个 | Prime Sandboxes 可访问的预构建环境 | Prime Intellect | [Prime Sandboxes](https://www.primeintellect.ai/blog/sandboxes) | 厂商自报 | 2026-09-23 | 中 | 每沙箱为完整 Linux VM；博文（2026-09-23）称保存、恢复、fork 在路线图中；2026-10-05 核对 prime-sandboxes SDK（HEAD 32098eb）：已有文件系统检查点（`checkpoint`、`checkpoint_id` 恢复）与 `set_network`，fork、暂停未见（BC-05）；转向 VM 的理由为保真度（厂商自报）："gVisor needs complex setup and even then, does not offer the full list of features"（Docker Compose 类任务）；"Silent differences from production can be more dangerous than hard failures because they can reward behaviors that do not transfer into reality"；"A full Linux VM provides both by giving each sandbox its own kernel while keeping the isolation boundary outside the workload" | 16, 22 |
| B16-15 | 2026-06-04（agentgateway 加入）；2026-08-17（A2A 加入，时为 5 个项目）；2026-09-09（Agent Router 加入，现 6 个项目） | agentgateway、A2A、Agent Router 加入 AAIF 的公告日期；AAIF 托管项目（MCP、goose、AGENTS.md、agentgateway、A2A、Agent Router） | AAIF | [aaif.io A2A joins AAIF](https://aaif.io/blog/a2a-joins-aaif)；[Agent Router joins AAIF](https://aaif.io/blog/agent-router-joins-aaif)；[agentgateway joins AAIF](https://aaif.io/blog/agentgateway-joins-aaif-as-an-open-gateway-for-agentic-ai-infrastructure) | 一手文档 | 2026-06-04 / 08-17 / 09-09 | 高 | — | 16, 23 |
| B16-16 | 网络配置"可调用但效果受限"；卷与访问令牌"暂不兼容"；快照、暂停/恢复需白名单 | 阿里云 FC 对 E2B SDK/CLI 的逐项兼容范围 | 阿里云函数计算 FC | [FC E2B Compatibility](https://help.aliyun.com/en/functioncompute/e2b-compatibility-description) | 一手文档 | 2026-10-04 读取 | 高 | 命令、进程、PTY 支持；文件系统部分支持（无自定义元数据） | 16, 26 |
| B16-17 | 7 家（Daytona、Modal、LangSmith、Blaxel、Novita Sandbox、Tensorlake、Runta） | Harbor README 列出的云沙箱后端 | Harbor | [harbor-framework/harbor](https://github.com/harbor-framework/harbor) | 一手文档 | 2026-10-04 读取 | 高 | README 写"providers like"，非穷举；文献库 C16-04 原记 6 家（无 Runta），已补 | 16, 20 |
| B16-18 | 3 个轴（工具、宿主、网络）；2025-08-07 | Inspect Sandboxing Toolkit 的隔离分类；博文日期 | UK AISI | [AISI 博文](https://www.aisi.gov.uk/blog/the-inspect-sandboxing-toolkit-scalable-and-secure-ai-agent-evaluations) | 一手文档 | 2025-08-07 | 高 | 文献库 C20-03；Inspect 内置 docker、local，扩展含 k8s、daytona、modal、ec2、proxmox、vagrant、openshell | 16, 20 |

---

## 第四部分　沙箱与 Agent RL

### 第 17 章　Rollout 架构与 RL 框架集成

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B17-01 | 自 DeepSeek-V4.1 起 | rollout 执行移到 DSec（agent sandbox + worker container） | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | V4.1 之前 GPU 作业被抢占时 Agent 循环丢失；原文 "Starting with DeepSeek-V4.1, we instead move rollout execution onto DSec……"（DSec §6.2）；抢占暂停见 §6.3 | 17, 24, 28 |
| B17-02 | RLVR 最高 2.24×、Agent 任务 2.72×；环境级异步（同步训练下）：SWE 10.22 h → 8.32 h（1.23×）、ALFWorld 13.37 h → 8.44 h（1.58×）；冗余环境 rollout：同步 SWE 8.32 → 7.66 h（−7.9%）、ALFWorld 8.44 → 7.85 h（−7.0%），异步 SWE 6.09 → 5.65 h（−7.2%）、ALFWorld 5.87 → 4.91 h（−16.4%），即额外吞吐 7%–16% | 环境级异步 rollout 与冗余环境 rollout（两步分别报告，不可首尾相连） | ROLL Flash（阿里/上交/港科大） | [arXiv 2510.11345][rollflash] | 论文自述 | 2025-10 | 高 | 旧值"SWE 8.32 h → 5.65 h；ALFWorld 8.44 h → 4.91 h"把 §5.2.1（环境级异步）与 §5.2.2（冗余）不同配置的端点拼接，不应再用；原文 §5.2.1 "from 10.22h to 8.32h on SWE (1.23×) and from 13.37h to 8.44h on ALFWorld (1.58×)" | 17, 26 |
| B17-03 | 超过 3,000 张 GPU；训练时间缩短 1.31–2.05× | 解耦多任务 Agentic RL | RollArt（OSDI'26） | [arXiv 2512.22560][rollart]；[USENIX OSDI'26][rollart-osdi] | 论文自述 | 2025-12-27 / OSDI'26 | 高 | 会议状态：曾一度记为"未核实"，后经 USENIX 演讲页核实属 OSDI'26（C-20）；2026-10-05 再次回 USENIX 演讲页复核（"20th USENIX Symposium on Operating Systems Design and Implementation (OSDI 26)"） | 17, 26, 附录 D |
| B17-04 | SWE-bench 30–50 轮 | RollArt 负载 | RollArt | [arXiv 2512.22560][rollart] | 论文自述 | 2025-12 | 高 | — | 17 |
| B17-05 | 10× 吞吐提升 | 异步调度 + Prefix/KV 复用 + 冗余环境执行 | 阿里云 Qwen-Coder-Qoder | [Alibaba Cloud 博客][qoder-blog] | 厂商自报 | 2026-07-17 | 中 | — | 17, 26 |
| B17-06 | 开源基准：端到端吞吐最高 2.12×（128 张 GPU，34,135 tokens/s）、rollout 阶段 8.2×（64 张 GPU，14.9 → 1.8 分钟）；生产：4,096 张加速卡、约 5,000 亿参数 MoE（LongCat-Flash-Thinking）、最长 64K token 响应，相对生产调优同步基线，数学与工具推理 rollout 加速 3.6×，Agent 训练（Tau2-bench、Vita）最高 6.2× | 异步 RL 系统 | 美团 DORA | [arXiv 2604.26256][dora] | 论文自述 | 2026-04 | 高 | 开源基准为 16 节点 × 8 张 H800；摘要另写 "8.2× rollout-stage acceleration"；6.2× 仅对 Agent 负载，基线为生产同步训练（原文："running all baselines at this scale is prohibitive"）；摘要写"thousands of accelerators"，正文写"4,096 accelerators"；C-37 | 17, 26 |
| B17-07 | 请求负载比约 63%；比同步训练快 2–4× | DORA 在 LongCat 训练中 | 美团 LongCat | [arXiv 2601.16725][longcat] | 论文自述 | 2026-01 | 中 | — | 17, 26 |
| B17-08 | 超过 100 步的陈旧轨迹被丢弃；最多 128 轮、131k 上下文 | 全异步 RL 与 Agent 化 SWE | Meta CWM（32B） | [arXiv 2510.02387][cwm] | 论文自述 | 2025-09/10 | 高 | — | 17, 19, 27 |
| B17-09 | 4,500 个 R2E-Gym 任务；每次迭代 512 个 Docker 容器（BS=64, 8 passes）；> 1,000 个 CPU 核；64 × H100 训练 6 天；SWE-bench Verified pass@1 42.2%（TTS 后 59%） | 纯 RL 训练 Qwen3-32B | DeepSWE / rLLM（Agentica + Together） | [Together AI 博客][deepswe] | 一手文档 | 2025-07-02 | 高 | 把 Docker daemon 换成 Kubernetes；数千个容器使 Docker API 过载、dockerd 崩溃后改用 K8s（第 5 章复核） | 5, 17, 27 |
| B17-10 | 约 200 轮时重新分词漂移曾影响约 40% 样本 | token 一致性问题 | 快手 KAT-Coder-V2.5 | [arXiv 2607.05471][kat] | 论文自述 | 2026-07 | 高 | 由 Gateway Server 处理 | 17, 26, 28 |
| B17-11 | 最多 100,000 个并发 agent 任务（concurrent agent tasks） | Rollout Manager 编排的协程任务数 | Kimi K2.5 | [Kimi K2.5 报告 arXiv 2602.02276][k25] | 论文自述 | 2026-02 | 高（按原单位） | **不是 10 万个并发沙箱**，C-09 | 17, 26 |
| B17-12 | 超过 1k 个并发 rollout | Multi-Task Rollout Orchestrator | 智谱 GLM-5 | [GLM-5 报告 arXiv 2602.15763][glm5] | 论文自述 | 2026-02 | 高 | 原文："this orchestrator supports over 1k concurrent rollouts and enables automated, dynamic adjustment of task sampling ratios"；单位为 rollout，非沙箱；§4.1.1（"Server-based multi-task training design"段，下一标题为 4.1.2）；v1、v2 PDF 结构经网页读取一致（2026-10-06，未取得本地 PDF）；此前"§3.6.1"一说为抓取错位，3.6.1 下的段首是"Highly customizable rollouts""Server-based rollouts via HTTP APIs"；引文一致："Serving as the backbone of the GLM-5 training infrastructure, this orchestrator supports over 1k concurrent rollouts" | 17, 26 |
| B17-13 | 冷启动差距最高 110×；100 万条 150 步轨迹的预计工时差 1.8× | 四种执行底座对比 | The Rollout Infrastructure Tax（Daytona 作者） | [arXiv 2607.01415][tax] | 论文自述 | 2026-07-01 | 中 | 作者来自沙箱厂商；SoCC'26 投稿预印本；五位作者 Daniel Thi Graviet、Lovre Pešut、Ivan Dagelić、Vedran Jukic、Ivan Burazin 的署名单位均为 Daytona, United States；"Preprint submitted to ACM SoCC 2026" | 17, 22 |
| B17-14 | 数十万个任务；可运行"many hours"的 rollout；数万张 GB300 | Grok 4.5 RL | xAI | [xAI Grok 4.5][xai-grok45] | 一手文档 | 2026-07-16 | 高 | 无沙箱技术与并发披露；2026-10-05 第 27 章复核原句；Grok 4.6 模型卡（2026-08-12，08-17 修订）亦无沙箱技术披露，仅称 KernelBench 在"sandboxed GPU environment"中运行 | 17, 27 |
| B17-15 | 200,000 GPU 的 Colossus；训练算力效率 6× | Grok 4 RL | xAI | [xAI Grok 4][xai-grok4] | 一手文档 | 2025-07-09 | 高 | — | 27 |
| B17-16 | 超过十万个真实 scaffold 与环境；数百种 scaffold、数千种工具调用格式；上下文 200k；每日数百万样本 | Agent 无关的 RL 中间件 | MiniMax Forge（M2.5） | [MiniMax Forge][forge] | 厂商自报 | 2026-02-13 | 中 | 无沙箱并发或延迟数字 | 17, 18, 26 |
| B17-17 | "数十万个并发的沙箱化编码环境" | Composer RL | Cursor | [Cursor：Composer](https://cursor.com/blog/composer) | 一手文档 | 2025-10-29 | 高 | 原文"running hundreds of thousands of concurrent sandboxed coding environments"；同文"rewriting our virtual machine scheduler"，复用 Background Agents 基础设施（2026-10-05 第 27 章复核）；原经 [HF：One sandbox per rollout][hf-rl] 转述；第 1 章 1.1.2、1.4.3 节引用（2026-10-05 复核）："running hundreds of thousands of concurrent sandboxed coding environments in the cloud"；"rewriting our virtual machine scheduler to support the bursty nature and scale of training runs"；"This enabled seamless unification of RL environments with production environments." | 1, 17, 27 |
| B17-18 | "routinely preempted" | GPU 训练作业被例行抢占以提高利用率；抢占时 RL 框架主动向相关沙箱发送暂停请求，后续请求透明恢复 | DSec | [DSec §6.2–§6.3][dsec] | 论文自述 | 2026-09-19 | 高 | 无暂停延迟与暂停数量；"唯一事实来源"（single source of truth）在 §6.2，RL 框架主动暂停在 §6.3，引用时分别注明 | 17, 24 |
| B17-19 | up to 2.77× | 相对同步系统的训练加速（完全异步、陈旧度增强 PPO） | AReaL（蚂蚁） | [arXiv 2505.24298](https://arxiv.org/abs/2505.24298) | 论文自述 | 2025-05-30（现行版本 2026-03-02） | 高 | 数学与代码推理基准，非 Agent 负载 | 17, 26 |
| B17-20 | up to 2.04×；72–94% | 端到端 rollout 吞吐提升；长尾延迟降低 | Seer | [arXiv 2511.14617](https://arxiv.org/abs/2511.14617) | 论文自述 | 2025-11-18（修订 2026-04-03） | 高 | 同步 RL；GPU 侧优化 | 17 |
| B17-21 | 1.55×；24.4% → 39.4% Pass@1；> 2× 成本降低 | 异步流水线调度器相对朴素异步批处理的加速；SA-SWE-32B 在 SWE-Bench Verified 上的结果 | SkyRL-Agent（UC Berkeley） | [arXiv 2511.16108](https://arxiv.org/abs/2511.16108) | 论文自述 | 2025-11-20 | 高 | — | 17, 27 |
| B17-22 | 约 16% → < 2%；超时无效 rollout 约 6%–7% → < 1%；验证器输出损坏约 6%–7% → < 1% | 沙箱反馈错误率及两项细分 | 快手 KAT-Coder-V2.5 | [arXiv 2607.05471][kat] | 论文自述 | 2026-07 | 高 | 与 B18-02 互见；细分为新增 | 3, 17, 26 |
| B17-23 | 心跳（无数字） | slime 心跳容错的对象为 rollout 服务器（推理侧），不健康者被终止并从推理路由器注销 | 智谱 GLM-5 / slime | [GLM-5 §3.6.3][glm5] | 论文自述 | 2026-02 | 高 | 不应写成"沙箱心跳"，X-32 | 17, 26 |
| B17-24 | r/(1+r) | 冗余比例为 r 时被作废沙箱时间的上界 | — | 由冗余定义推算 | 笔者推算 | 2026-10 | 中 | 假设冗余轨迹与正常轨迹寿命相同 | 17 |

### 第 18 章　环境构建与规模化

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B18-01 | 超过 10 万个可验证环境；12 种语言；构建成功率 16.5% → 57.2% | AutoBuilder 流水线 | 快手 KAT-Coder-V2.5 | [arXiv 2607.05471][kat] | 论文自述 | 2026-07 | 高 | 原文称 environment-construction success rate，未写明分母；接受门槛为预期测试被收集超过 90% 且多次运行可复现；提升手段为预配置基础环境、按语言/构建系统的模板、可检索的成功配置库（§2.1） | 18, 26, 28 |
| B18-02 | 约 16% 的轨迹含至少一次沙箱可归因故障（超时 6–7% 的 rollout、环境变量损坏 6–7% 的样本）→ 总体 2% 以下，两分项各 1% 以下 | 沙箱故障学 | 快手 KwaiEnv | [arXiv 2607.05471][kat] | 论文自述 | 2026-07 | 高 | 三项分母不同：trajectories、all rollouts、samples（§4.2.2） | 18, 26, 28, 附录 D |
| B18-03 | 807,693 个真实 PR 实例（52,960 个仓库）+ 851,898 个合成 bug 实例；九种以上语言（spanning over nine programming languages）；表 10 为 Python、JS/TS、Go、Java、Rust、C/C++、C# 七类具名语言加 Others，Python 202,302 个 | SWE 任务规模 | Qwen3-Coder-Next / MegaFlow | [arXiv 2603.00729][qcn] | 论文自述 | 2026-02-28（提交） | 高 | 合计约 166 万（笔者推算，精确值见 B18-21）；未给并发数；正文未给构建成功率；§4.2.4 记录删除 remote/分支/tag 后模型改用 git remote add、git clone、curl 取回历史，团队以"仓库链接 + 网络关键字"的工具调用拦截规则应对，经人工检查"有效消除" | 18, 26 |
| B18-04 | 20,000 个独立环境并行 | RL 环境规模 | Qwen3-Coder | [Qwen3-Coder 博客][qwen3coder] | 一手文档 | 2025-07-22 | 高 | — | 18, 26 |
| B18-05 | 超过 35,000 个可执行仓库 Docker 镜像；ForagerAgent 从 10,200 个镜像/3,150 个仓库生成 300 万条轨迹；每秒"数万个代码片段" | 环境构建与执行服务 | Meta CWM | [arXiv 2510.02387][cwm] | 论文自述 | 2025-09-29 | 高 | RepoAgent 依据仓库文档构建；Activ 借 act 本地运行 GitHub Actions；对 SWE-bench Verified 做仓库级去污染，ForagerAgent 生成时排除 SWE-bench 所用仓库及其 fork（§2.3、§15） | 18, 27 |
| B18-06 | 约 45 万个关联 issue 的 PR → 约 153,400 个候选 → 21,336 个可验证任务（3,468 个仓库，仅 Python） | 任务生成 | SWE-rebench | [SWE-rebench arXiv 2505.20411](https://arxiv.org/abs/2505.20411)；[SemiAnalysis][semianalysis]（转述） | 论文自述 | 2025-05-26 | 高 | 已回论文原文核对 | 18 |
| B18-07 | 5 万个经验证环境；1.5 万以上仓库；20 多种语言；"数千并发"；环境构建成功率 40% | SWE 环境与并发 | 阶跃 Step 3.5 Flash | [arXiv 2602.10604][step35] | 论文自述 | 2026-02 | 高 | — | 18, 26 |
| B18-08 | 超过 1 万个可验证环境（9 种语言）；数千个合成终端环境（Docker 构建准确率 > 90%） | 环境规模 | 智谱 GLM-5 | [GLM-5 报告][glm5] | 论文自述 | 2026-02 | 高 | 此前"1 万+ 未核实"已撤销，C-24；SWE 环境基于 RepoLaunch 框架；终端任务由构建 Agent 实例化为 Harbor 格式，refine Agent 按人工 rubric 修订；> 90% 是合成终端任务的 Docker 构建准确率，与真实仓库构建成功率口径不同；原列于此的"约 1,000 万个 issue–PR 对"出自 §2.3 中期训练语料，移至 B18-22 | 18, 26, 27, 28 |
| B18-09 | 10 多种语言 | Agent 合成的多语言 Docker 环境 | MiniMax-M2 系列 | [arXiv 2605.26494][m2] | 论文自述 | 2026-05 | 高 | 无并发数，亦无环境数与构建成功率；Terminal-Gym 以完整 Stack Overflow 为原料，丢弃无采纳答案、低分、过长的帖子，Agent 生成 Dockerfile 与测试脚本，失败则反馈修复至通过或达重试上限（§4.1.3） | 18, 26 |
| B18-10 | 代码 Agent 9 万真实 + 3 万合成；搜索 Agent 15 万；通用 Agent 5 万 | Agentic RL 任务数 | 小米 MiMo-V2-Flash | [arXiv 2601.02780][mimo] | 论文自述 | 2026-01 | 高 | PDF §4.3.2 另有"a large-scale Kubernetes cluster running over 10,000 concurrent pods"与环境搭建成功率 70%（8 种语言），见 B26-22；附录 B 记录 SWE-Bench 镜像残留真值提交被 git log --all 利用，以关键词计数量化，图 8 给出尝试次数随训练步变化（无比率） | 18, 26 |
| B18-11 | 超过 365,000 个预构建环境 | Prime Sandboxes 背后的环境注册表中的预构建环境（"registry of more than 365,000 prebuilt environments"；原文未说是 Environments Hub） | Prime Intellect | [Prime Sandboxes 博客][prime-sandboxes] | 厂商自报 | 2026-09-23 | 中 | Hub 2025-08-27 上线，私测期 > 30 名贡献者 | 18, 22, 27 |
| B18-12 | 3000+ 真实 MCP 工具；超过 20,000 个合成工具 | 工具生态规模 | Kimi K2 | [Kimi K2 报告][k2] | 论文自述 | 2025-07 | 高 | — | 16, 18, 26 |
| B18-13 | 20 多个领域、每领域 60+ 工具；"数万个环境" | 环境覆盖 | 美团 LongCat-Flash-Thinking-2601 | [arXiv 2601.16725][longcat] | 论文自述 | 2026-01 | 高 | — | 18, 26 |
| B18-14 | 118,000+ 个 skill；token 最多少 40%；并行最多 3.2×；固化后延迟降 19–50×（8 个 LLM） | Skill 编译与环境绑定 | SkVM（SOSP'26） | [arXiv 2604.03088][skvm] | 论文自述 | 2026-04 | 高 | — | 18 |
| B18-15 | 约 10 万个 skill；45% 依赖 shell 工具；约 70% 含半确定性代码块 | Skill 研究 | Skill OS | [AgenticOS'26 论文 13][skillos] | 论文自述 | 2026-03-23 | 高 | 缺依赖每次执行多耗"数万" token | 18 |
| B18-16 | 延迟降 13×；输入 token 少 88%；成本降 66% | 在 FaaS 上部署 MCP 工作流 | FAME | [arXiv 2601.14735][fame] | 论文自述 | 2026-01 | 高 | — | 18 |
| B18-17 | 40% | 环境构建成功率（分母与判据未写明） | 阶跃 Step 3.5 Flash | [arXiv 2602.10604][step35] §5.3.3 | 论文自述 | 2026-02 | 高 | 流水线由 SWE-factory 演化，含跨任务记忆池与循环检测；国内构建成功率对照见第 26 章表 26-3（KAT 57.2%、MiMo 70%、GLM-5 >90%，口径不同不可排序） | 18, 26, 28 |
| B18-18 | 超过 90% | KAT AutoBuilder 接受环境的预期测试收集率门槛；另要求多次运行可复现 | 快手 KAT-Coder-V2.5 | [arXiv 2607.05471][kat] §2.1 | 论文自述 | 2026-07 | 高 | 不依赖退出码，解析结构化测试输出 | 18 |
| B18-19 | 最多 92% | WebArena-Verified 镜像较原版缩小幅度 | ServiceNow WebArena-Verified | [GitHub][webarena-v] | 一手文档 | 2026-10-03 读取 | 高 | 另：去除 LLM-as-judge 与子串匹配，全部任务、参考答案与评估器人工审查；与 B20-17 同源 | 18, 20 |
| B18-20 | 约 0.75–1.5 个 | 每得到一个可验证环境伴随的失败构建尝试 | 快手、阶跃 | 由 B18-01、B18-17 推算：1/0.572 − 1 ≈ 0.75；1/0.4 − 1 = 1.5 | 笔者推算 | 2026-10 | 中 | 假设成功率按尝试计；两家分母均未披露，仅作量级 | 18 |
| B18-21 | 1,659,591 | Qwen3-Coder-Next 两类实例合计 | Qwen3-Coder-Next | 807,693 + 851,898 | 笔者推算 | 2026-10 | 高 | 原 B18-03 备注"约 166 万"的精确值 | 18 |
| B18-22 | 约 1,000 万个 issue–PR 对 | GLM-5 中期训练语料（放宽仓库级过滤后） | 智谱 GLM-5 | [GLM-5][glm5] §2.3 | 论文自述 | 2026-02-17 | 高 | 不是 SWE 环境原料数；二者是否同源报告未说明 | 18, 26 |
| B18-23 | 2,438 个；超过 8.7K 个；50k 个（128 个仓库） | SWE-Gym、R2E-Gym、SWE-smith 任务规模 | SWE-Gym / R2E-Gym / SWE-smith | arXiv 2412.21139；arXiv 2504.07164；SWE-smith 论文 | 论文自述 | 2024-12-30 / 2025-04-09 / 2025-04-30 | 高 | 已回原文核对 | 18 |

### 第 19 章　训练期 reward hacking 与遏制

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B19-01 | 63% 取回而非推导（以成功解为分母）；被审计的 731 条轨迹中 57% 查上游、9% 挖 .git 历史 | SWE-bench Pro 上 Opus 4.8 Max 解的来源 | Cursor | [Cursor：reward hacking on coding benchmarks][cursor-rh] | 一手文档 | 2026-06-25 | 高 | 63% 以成功解为分母，57% 与 9% 原文写作"轨迹"（In 57% of the trajectories / In 9% of trajectories）；审计对象为 731 条 Opus 4.8 Max 轨迹；57% 的分母为被审计的全部 731 条轨迹，不是"成功轨迹"（第 14、19 章口径统一） | 1, 2, 14, 19, 20, 27, 28 |
| B19-02 | Opus 4.8 Max 87.1% → 73.0%（−14.1）；Composer 2.5 74.7% → 54.0%（−20.7）；Opus 4.6 不到 1 分 | 标准 vs 严格 harness（去 .git + registry 出站代理） | Cursor | [Cursor][cursor-rh] | 一手文档 | 2026-06-25 | 高 | 同时改了两个变量；原文：On SWE-bench Pro, it was under 1 point for Opus 4.6, 14.1 points for Opus 4.8 Max and 20.7 points for Composer 2.5；Pro 逐模型表由客户端渲染，静态抓取不可得 | 1, 2, 14, 19, 20, 28 |
| B19-03 | Multilingual 表：Opus 4.8 (max) 91.16% → 82.03%（−9.1）；Composer 2.5 79.15% → 71.60%（−7.5）；Opus 4.6 (max) 76.33% → 76.06%（−0.3）；Opus 4.6 (high) 76.11% → 75.22%（−0.9） | SWE-bench Multilingual 掉分 | Cursor | [Cursor][cursor-rh] | 一手文档 | 2026-06-25 | 高 | — | 19, 20 |
| B19-04 | RE-Bench 30.4%（39/128）；Optimize a Kernel 25.0%（6/24）；Rust CodeContests 42.9%（12/28）；LLM Foundry 100%（21/21）；HCAST 0.7%（8/1087） | o3 reward hacking 率 | METR | [METR：Recent frontier models are reward hacking][metr] | 一手文档 | 2025-06-05 | 高 | — | 19 |
| B19-05 | 原始 80%；"intended methods" 95%；"don't cheat" 80%；"don't reward hack" 70%；高风险框架 70% | 反作弊提示下仍作弊的比例 | METR（o3） | [METR][metr] | 一手文档 | 2025-06-05 | 高 | 在 Optimize LLM Foundry 任务上、每种提示运行 20 次 | 19 |
| B19-06 | Conflicting-SWEbench：GPT-5 54%、o3 约 49%、Opus 4.1 约 50%；Impossible-LiveCodeBench（最小脚手架）GPT-5 2.9%；One-off-SWEbench：GPT-5 76% | 不可能任务上的作弊率 | ImpossibleBench（ICLR 2026） | [arXiv 2510.20270][impossible] | 论文自述 | 2025-10 | 高 | 二手转述写"约 49–54%" | 19, 28 |
| B19-07 | Claude、Qwen 作弊 > 79% 为改测试 | 作弊策略分布 | ImpossibleBench | [arXiv 2510.20270][impossible] | 论文自述 | 2025-10 | 高 | — | 19 |
| B19-08 | 严格提示 GPT-5 92% → 1%（Conflicting-LiveCodeBench）；abort 选项 GPT-5 54% → 9%、o3 49% → 12%（Conflicting-SWEbench）；多次提交使平均作弊率 33% → 38% | 缓解措施效果 | ImpossibleBench | [arXiv 2510.20270][impossible] | 论文自述 | 2025-10 | 高 | 只读测试只消除改测试一类 | 19 |
| B19-09 | 13 个前沿模型；Sonnet 4.5 0%、R1-Zero 13.9%、V3 0.6% | 环境利用率 | Reward Hacking Benchmark（arXiv 摘要页注明 Accepted to ICML 2026） | [arXiv 2605.02964][rhb] | 论文自述 | 2026-05-03 | 高 | RL 后训练与更高利用率相关（相关性）；原文："A controlled sibling comparison (DeepSeek-V3 vs. DeepSeek-R1-Zero) shows RL post-training is associated with substantially higher reward hacking (0.6% vs. 13.9%), with consistent gaps across all four task families" | 2, 19 |
| B19-10 | −5.7 个百分点（相对 87.7%），不损失任务成功率 | 简单环境加固效果 | Reward Hacking Benchmark | [arXiv 2605.02964][rhb] | 论文自述 | 2026-05-03 | 高 | — | 2, 19 |
| B19-11 | Claude Opus 6 条可疑成功轨迹（约 1.2 个百分点）；Claude 4 Sonnet 8 条；另一贡献者估计初步搜索为 5/10000 | `git log --all` 看到未来提交 | SWE-bench issue #465 | [SWE-bench #465][swebench465] | 一手文档（GitHub issue） | 2025-09-03（issue 开启；2026-03-24 关闭） | 中 | 4.1.0（PR #471）删除未来历史、保留基准提交前的 tag；#578（2026-05-08）Multilingual 镜像泄漏 116 个 git tag、515 个可达提交，属 .git 复发；#669（2026-09-25）为题面（problem_statement）泄漏答案，**不是** .git 复发 | 19, 20 |
| B19-12 | 216 条轨迹（每个模型 108 个任务，GPT-5.5 与 Claude Opus 4.7）中，约 33% 的任务绕开用户可见界面，约 14% 的任务提取隐藏应用状态；11.53% 总分依赖模型评判，无任务超过 50% | GUI 场景的 reward hacking | OSWorld 2.0 | [arXiv 2606.29537][osworld2] | 论文自述 | 2026-06-28 | 高 | 两者原文均为 of tasks；原文未说明分母是否合并两个模型；"绕开界面"不必然等于获得不当分数；第 28 章初稿曾误写为"约 33% 的轨迹"，已更正；他章引用时两比例均按"任务"计 | 7, 19, 20, 28 |
| B19-13 | 无比率 | DSec §6.4 训练期作弊清单（伪造 chronus RPC、覆盖 /bin/bash、XFS_IOC_SWAPEXT、扫端口、借 Go proxy、读 /proc/kpagecgroup 崩内核） | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 书中不得给 DSec 配比率 | 2, 19, 24, 28, 附录 D |
| B19-14 | 数十 GB | 无界输出（`yes` 命令）在存储上堆积的数据 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 19, 24 |
| B19-15 | 目标最低通过率 2–3%（64–128 次 rollout 约 1 次成功） | 外购环境的难度规格 | Epoch AI 访谈 | [Epoch：State of RL environments][epoch] | 二手报道（访谈综述） | 2026-01-12 | 中 | reward hacking 是买方最关心的质量问题；原文为"Multiple interviewees mentioned"，不是共识 | 18, 19, 22 |
| B19-16 | 898 个真实漏洞（用户态、V8、Linux 内核） | ExploitGym 规模 | ExploitGym（UC Berkeley RDI） | [Substack 摘要][substack-exploitgym] | 二手报道 | 2026 | 中 | 与一手复盘"898 个任务"一致 | 19, 20 |
| B19-17 | 898 个任务中 198 个"none of our models had ever produced a correct answer" | "没有安全退出路径"的根因 | OpenAI（IM1） | [OpenAI 事故复盘][openai-hf] | 一手文档 | 2026-08-26 | 高 | — | 2, 19, 20, 27 |
| B19-18 | 约 17,600 次动作 / "超过 17,000 次记录动作"（一个周末） | ExploitGym 事件动作数 | OpenAI 模型 | [Substack][substack-exploitgym]；[CSA 研究笔记][csa-openai] | 二手报道 | 2026-07 | 低 | 两个二手数字接近但不同，一手复盘未给；C-10；第 19 章正文不列出该数字；CSA 原句："executed more than 17,000 recorded actions"（2026-10-06 逐字复核；CSA 亦为转述） | 19 |
| B19-19 | 30 分钟 | 暂停前告警的误报阈值（paging alerts） | OpenAI 事后对策 | [OpenAI 事故复盘][openai-hf] | 一手文档 | 2026-08-26 | 高 | — | 19, 28 |
| B19-20 | 05-12 首次借 Artifactory 写留言板；05-26 经 SSRF 出站；06-26 token 刷新漏洞提权；07-04 Artifactory 宕机；07-05 开立安全事件、封堵已知提权路径、移除暴露凭据，之后重建 Artifactory，留言板被顺带清空；07-08 重建后 Agent 经 remote-repository 重获互联网访问、留言板重建，另有 Agent 以未经认证的 WebDAV 请求在 Artifactory 建消息目录；07-10 重建、验证并共享 14 个公开暴露、带写权限的 HF 凭据；07-11 HDF5 零日暴露 HF worker 机密、"RefJinja"模板注入零日执行代码；**07-12 扩大 HF 集群访问、生产凭据失陷**；07-13 经 Artifactory 的 RubyGems 处理逻辑取得签名密钥并伪造管理员凭据；07-19 检测到可疑活动，另有 Agent 取得 OpenAI Kubernetes 集群管理员访问并触及云端机密；**07-20 调查将活动与 HF 事件关联**；07-21 披露 | ExploitGym 一手时间线（2026 年） | OpenAI / Hugging Face | [OpenAI 事故复盘][openai-hf] | 一手文档 | 2026-08-26 | 高 | 替代此前 Wikipedia/二手时间线，C-10；第 19 章只引 05-12、07-19、07-21 三个节点，逐日见第 15 章表 15-1 | 15, 19 |
| B19-21 | GPT-5.6 Sol 能力及以上（models with GPT‑5.6 Sol capability or higher）的所有工具型 RL 训练与评测；Astra 级模型另覆盖所有启用工具的推理负载 | 所有工具型 RL 训练与评测启用 CoT 监控的模型范围 | OpenAI 对策 | [OpenAI 事故复盘][openai-hf] | 一手文档 | 2026-08-26 | 高 | 另：对拟部署的最新模型暂停 RL 训练；"Our largest planned frontier RL run remains on hold" | 2, 19 |
| B19-27 | 731 条 | Cursor 审计的 Opus 4.8 Max 轨迹数 | Cursor | [Cursor][cursor-rh] | 一手文档 | 2026-06-25 | 高 | 63%/57%/9% 的样本 | 2, 19, 20 |
| B19-28 | 93% | Artifactory 留言板上讨论的任务中来自 198 个无解任务的比例 | OpenAI（IM1） | [OpenAI 事故复盘][openai-hf] | 一手文档 | 2026-08-26 | 高 | 无解任务是 hacking 放大器 | 2, 18, 19, 20, 27 |
| B19-29 | "over 100x" | 使用生产 ChatGPT harness 与系统提示时，破坏基础设施倾向的下降倍数 | OpenAI | [OpenAI 事故复盘][openai-hf] | 一手文档 | 2026-08-26 | 中 | 测量口径未披露 | 2, 19, 20 |
| B19-30 | "dozens of" 服务器；一台 root | Agent 在 HF 上执行代码的服务器数与取得 root 的服务器数 | OpenAI / Hugging Face | [OpenAI 事故复盘][openai-hf] | 一手文档 | 2026-08-26 | 高 | 替代二手"约三分之一基础设施重建"等说法 | 15, 19 |
| B19-31 | 5/10000 | SWE-bench #465 中一位贡献者初步搜索 `git log --all` 的匹配比例 | SWE-bench | [SWE-bench #465][swebench465] | 一手文档（GitHub issue） | 2025-09-03（issue 开启） | 中 | 个人估计 | 19, 20 |
| B19-32 | 116 个 tag；515 个可达提交 | SWE-bench Multilingual 镜像的 git tag 泄漏 | SWE-bench #578 | [SWE-bench #578][swebench578] | 一手文档 | 2026-05-08 | 高 | .git 通道复发 | 19, 20 |
| B19-33 | 9 个实例（1 个题面含 diff、8 个链接 PR） | SWE-bench Verified 题面泄漏答案 | SWE-bench #669 | [SWE-bench #669][swebench669] | 一手文档 | 2026-09-25 | 高 | 与 .git 无关 | 19, 20 |
| B19-34 | 二十倍以上 | SWE-bench Pro 上 Composer 2.5 与 Opus 4.6 掉分之比 | Cursor | 20.7 对"不到 1" | 笔者推算 | — | — | 取代初稿"近 70 倍"（误用 Multilingual 的 0.3） | 2, 19 |
| B19-35 | 领先约 2.8 分 → 落后约 4.5 分 | Multilingual 上 Composer 2.5 相对 Opus 4.6 (max) 的差距（标准 → 严格） | Cursor | 79.15 − 76.33；76.06 − 71.60 | 笔者推算 | — | — | 隔离设置使先后次序翻转的实例 | 2, 19, 20 |
| B19-22 | 约 9,000 个目标 | 模型扫描的目标数（一手为"targets"） | Anthropic / Irregular 事件 3 | [Anthropic 事故页][anthropic-incidents]；[InfoQ][infoq-anthropic]；[THN 2026-07][thn-anthropic-jul] | 一手文档 | 2026-07-30 | 高 | 一手摘录为"scanning roughly 9,000 targets"（第 15、20 章两次抓取一致），未写"公网 IP"；所属事件与模型的逐字措辞未核实 | 15, 20 |
| B19-23 | 数百行生产数据 | Opus 4.7 在真实组织取得的数据量 | Anthropic 事件 1 | [Anthropic 事故页][anthropic-incidents]；[THN 2026-07][thn-anthropic-jul] | 一手文档 | 2026-07-30 | 中 | 一手页面摘录为"several hundred rows of production data"（摘要式转述，未逐字核对） | 19 |
| B19-24 | 2026-07-23 | 开始复查 transcript，并于同日停止所有网络安全评测；7-24 识别事件；7-27 通知受影响组织 | Anthropic | [Anthropic 事故页][anthropic-incidents]；[InfoQ][infoq-anthropic] | 一手文档 | 2026-07-30 | 高 | 一手原文："We began our transcript review on Thursday, July 23, and stopped all cyber evaluations the same day…"；二手"进攻性"一词一手未见；7-24、7-27 为摘要式转述（可信度中） | 2, 19, 20 |
| B19-25 | 事件发生于 2026-01、2026-08 发现；扫描约 4.81 亿条 transcript 未发现同类 | 第四起事件（早期 Opus 4.6） | Anthropic | [THN 2026-09][thn-anthropic-sep] | 二手报道 | 2026-09 | 低 | 委托 METR 独立调查 | 2, 19 |
| B19-26 | 2026-04 | Mythos Preview 系统卡：早期内部版本在行为测试中被模拟用户指示逃出"安全容器"并联系研究者；"未经要求"公开发布利用细节 | Anthropic Claude Mythos Preview | [Mythos Preview 系统卡 §4.1.1（第 54 页起）](https://www-cdn.anthropic.com/08ab9158070959f88f296514c21b7facce6f52bc.pdf)；[GreaterWrong 全文转载](https://www.greaterwrong.com/posts/xtnSzhA3TvExN4ZhG/claude-mythos-preview-system-card)（逐字比对） | 一手文档 | 2026-04 | 高 | 原文："The simulated user instructed it to try to escape that secure container and find a way to send a message to the researcher running the evaluation."；"secured 'sandbox' computer"一语经 GreaterWrong 转载逐字核实；该段在 §4.1.1 内的具体页码未核；Futurism、TNW 为二手；C-27 已据原文裁决 | 2, 19, 20 |

### 第 20 章　评测沙箱

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B20-01 | 18 个场景（编排层 4、运行时层 8、内核层 6） | 容器逃逸基准结构 | SandboxEscapeBench（UK AISI） | [arXiv 2603.02277][sebench] | 论文自述 | 2026-03（ICML 2026 Oral） | 高 | ICML 2026 Oral 已于 2026-10-05 回 icml.cc 演讲页复核（Oral，2026-07-08） | 2, 5, 20 |
| B20-02 | 难度 1–2 "high success rates"（≥ 80% 为图读，未核实）；难度 3 约 40%（0.40 [0.26, 0.56]）；难度 4–5 为 0%（以上均为原始每样本 250 万 token 预算，§5.1） | 前沿模型逃逸成功率 | SandboxEscapeBench | [arXiv 2603.02277][sebench] | 论文自述 | 2026-03（v3 2026-08-01） | 高 | 未评测 gVisor/Firecracker/Kata/WASM；Level 3 约 40% 为 GPT-5 与 Opus 4.5；所有成功逃逸依赖已公开的错误配置或 CVE；作者建议"treat plain Docker isolation as insufficient by default"；难度 1 为直接错误配置（专家 < 10 分钟），难度 5 为复杂内核利用（1–2 小时）；论文局限一节未把 gVisor/Firecracker 列为未覆盖项，二者只在背景中提及（"hyperscale inference providers typically rely on … Firecracker … gVisor"）；"难度 4–5 为 0"只适用于原始预算，v3 在每样本 1 亿 token 下已被 Mythos Preview 饱和，见 B20-22 | 2, 5, 20, 28 |
| B20-03 | Claude Opus 4.5 49% [39–59%]、Claude Haiku 4.5 18% [11–27%]；GPT-5 50% [40–60%]、GPT-5.2 27% [19–37%]；GPT-OSS-120B 16% [9–24%] | 按模型总体成功率 | SandboxEscapeBench | [arXiv 2603.02277][sebench] | 论文自述 | 2026-03（v3 2026-08-01） | 高 | 方括号为置信区间；每模型–任务 5 次试验、每次 250 万 token 预算（原始设置） | 2, 5, 20 |
| B20-04 | 4 条非预期捷径（附录 C.1–C.4：Default Credential、Insecure Key、eBPF Kernel Exploit、Dirty COW Bypass）；任务限定为已公开漏洞集合（设计如此，"fixed, bounded vulnerability set"）；成功率随推理算力近似对数线性增长（原始预算）；许多运行约 $1/样本 | 其他发现 | SandboxEscapeBench | [arXiv 2603.02277][sebench]；[AISI 博客][aisi-blog] | 论文自述 | 2026-03-23 | 高 | — | 20, 28 |
| B20-05 | 97 个任务；629 个安全测试用例 | AgentDojo 规模 | AgentDojo（NeurIPS 2024 D&B） | [arXiv 2406.13352][agentdojo] | 论文自述 | 2024-06 | 中 | [K]，未重新抓取 | 2, 20 |
| B20-06 | 1,054 个用例；GPT-4 约 24% 易受攻击 | InjecAgent | InjecAgent | [arXiv 2403.02691][injecagent] | 论文自述 | 2024 | 中 | 原文："1,054 test cases spanning 17 user tools and 62 attacker tools"；"ReAct-prompted GPT-4 vulnerable to attacks 24% of the time"；加强攻击后约 47%（alphaXiv 摘要，2026-10-06）；X-27 中 InjecAgent 部分已移出 | 20 |
| B20-07 | 最高平均 ASR 84.30% | Agent Security Bench | ASB（ICLR 2025） | [arXiv 2410.02644][asb] | 论文自述 | 2024-10 | 中 | 原文："the highest average attack success rate of 84.30%"；10 个场景、400 多个工具、27 种攻防方法、13 个 LLM 骨干（alphaXiv 摘要，2026-10-06）；X-27 中 ASB 部分已移出 | 20 |
| B20-08 | RedCode-Exec 4,050 个风险用例（25 类漏洞、8 个领域）；RedCode-Gen 160 个；19 个 LLM | 风险代码执行基准 | RedCode（NeurIPS 2024 D&B） | [RedCode][redcode] | 论文自述 | 2024-11 | 高 | 另有二手转述写"4,000+"（C-26，非实质冲突） | 20 |
| B20-09 | 150 个任务 | 基于 OSWorld 的 computer-use 伤害评测 | OS-Harm | [arXiv 2506.14866][osharm] | 论文自述 | 2025-06 | 中 | [K] | 7, 20 |
| B20-10 | 零日约 13%、一日约 25% | 真实 Web CVE 利用率 | CVE-Bench | [arXiv 2503.17332][cvebench] | 论文自述 | 2025 | 低 | [K] 未核实 | 20 |
| B20-11 | 36 个工具包、144 个测试用例 | LM 模拟沙箱 | ToolEmu（ICLR 2024） | [arXiv 2309.15817][toolemu] | 论文自述 | 2023-09 | 低 | [K] | 20 |
| B20-12 | AWS 上最多 50 个环境并发，评测时间缩短到"数分钟"（"shorten evaluation time to minutes"，原文未给具体数）；此前每台服务器 8–16 个；约 10 人团队约两个月处理 "300+ pieces of feedback" | 评测并行化与维护 | OSWorld-Verified | [XLANG 博客][osworld-v] | 一手文档 | 2025-07-28 | 高 | 转向 Docker/AWS 的原因之一是 Broadcom 收购后 VMware 分发问题；"10+ hours to just 20 minutes" 为博客对 WAA 的描述（"Later, WindowsAgentArena … compressing evaluation time from 10+ hours to just 20 minutes"），不得归于 OSWorld-Verified；问题清单第一项为 "Anti-crawling mechanisms and CAPTCHAs" | 1, 7, 20 |
| B20-13 | Claude Opus 4.8 约 $72.40、Opus 4.7 约 $33.60、GPT-5.5 约 $25.50、小模型 $2.40–6.60 | 单任务评测成本（推理 token 的 API 费用；Opus 4.8 为 max thinking + 批量工具调用） | OSWorld 2.0 | [arXiv 2606.29537][osworld2] | 论文自述 | 2026-06-28 | 高 | 小模型 $2.4（MiniMax M3）、$6.6（Kimi 2.6）为单动作设置，已核实（表 3）；$33.6 为 Opus 4.7 批量设置，单动作设置为约 $35.8；全量 108 个任务，全量成本见 B20-26 | 1, 20, 22 |
| B20-14 | Claude Opus 4.7（单动作设置）平均 318.4 步（原文 steps；单动作下每步一次调用，与"工具调用"数值等价；1.0 版约 30）；每任务平均 27.25 个检查点；AWS us-east-1，默认 t3.2xlarge；108 个任务；自托管 31 个面向任务的 Web 服务 | 任务长度与评测设置 | OSWorld 2.0 | [arXiv 2606.29537][osworld2] | 论文自述 | 2026-06-28 | 高 | 全部 Web 流量走住宅代理；318.4 步为 Claude Opus 4.7 的数值，步数随模型而变，引用时须写主语 | 1, 7, 20 |
| B20-15 | 30 GB golden image；默认 8 GB RAM/8 核；90 天评估版许可；Azure 40 台 VM；约 30–35 分钟；Azure VM 约 $8（$0.38/h × 40 × 0.5 h，仅 VM）；模型费用 GPT-4V $100、GPT-4o $100、GPT-4o-mini $15 | Windows 评测环境 | Windows Agent Arena | [GitHub WAA][waa] | 一手文档 | 2024–2026 | 高 | GPT-4V 约 35 分钟、GPT-4o-mini 约 30 分钟；更正：README"What are approximate running times and costs"表中 $8 只是 VM 费用；约 30–35 分钟是 40 台 Azure VM 并行跑完全量基准的墙钟时间，不是单任务或单个沙箱的寿命，勿作"状态寿命"引用（见 X-47） | 1, 7, 20, 27 |
| B20-16 | 116 个任务/20 个应用；Pixel 6 AVD API 33；最低 2 GB 内存、8 GB 磁盘；2025-06 起实验性 Docker | Android 评测环境 | AndroidWorld | [GitHub AndroidWorld][androidworld] | 一手文档 | 2025–2026 | 高 | — | 7, 20 |
| B20-17 | 812 个复核任务 + 258 个 Hard 子集；镜像最多缩小 92%；地图服务 5 个容器 → 1 个 | 确定性评分的 Web 评测 | WebArena-Verified（ServiceNow） | [GitHub webarena-verified][webarena-v] | 一手文档 | 2025-12-04 / 2026-02-02 | 高 | — | 20 |
| B20-18 | 241 个任务 | 综述表 4 所称"Terminal-Bench 2.1"的任务数 | Terminal Agents 综述 | [arXiv 2608.20485][termsurvey] | 论文自述（综述） | 2026-08 | 低 | tbench.ai 2.1 页原文"fix issues in 28 of the 89 tasks in Terminal-Bench 2.0"（2.1 为同一批 89 个任务的修订，强推断），241 来源不明，C-14 | 20 |
| B20-19 | 640 个任务；SetupBench 93 个任务 | BashArena / SetupBench 规模 | Terminal Agents 综述转述 | [arXiv 2608.20485][termsurvey] | 论文自述（综述） | 2026-08 | 中 | — | 20 |
| B20-20 | 369 个任务（OSWorld） | Step-GUI 评测口径 | 阶跃 Step-GUI | [arXiv 2512.15431][stepgui] | 论文自述 | 2025-12 | 中 | — | 20 |
| B20-21 | 5 次试验；250 万 token；约 $1/样本；难度 1 < 10 分钟、难度 5 为 1–2 小时 | SandboxEscapeBench 原始评测设置与成本 | UK AISI | [arXiv 2603.02277v3][sebench] | 论文自述 | 2026-03 / 2026-08-01（v3） | 高 | 原始预算；v3 更新见 B20-22 | 2, 5, 20, 28 |
| B20-22 | 每样本 1 亿 token；Mythos Preview 100% 样本至少成功一次 | SandboxEscapeBench v3 更新：在原始配置下重测 Claude Mythos Preview、Opus 4.6、GPT-5.4 Pro、GPT-5.5 | UK AISI | [arXiv 2603.02277v3][sebench] | 论文自述 | 2026-08-01 | 高 | 原文："We found that Claude Mythos Preview saturates this public benchmark"；"succeeded at least once on 100% of samples"；其他模型在新预算下的比例（如 Opus 4.6 约 80%）仅见摘要式抓取，未核实；对数线性原句（v3 HTML 摘录）："an approximately log-linear relationship between compute budget and success rate"；建议句前半"treat 'plain Docker isolation' as insufficient by default and use SandboxEscapeBench to stress-test configurations"已两次抓取一致，后半"while motivating stronger isolation primitives"仅见于一次摘要式读取、回原文未取到（未核实）；abs 页 2026-10-05 抓取均无可读文本 | 1, 2, 5, 20, 28 |
| B20-23 | 89 个任务（一手：tbench.ai 2.1 页）；2.1 修复 28 个；9 个任务外部依赖变化；8 个任务资源预算不足；Claude Code + Opus 4.6 提升 12.1% | Terminal-Bench 2.0/2.1 版本差异 | Terminal-Bench / Harbor | [VentureBeat][tb2-vb]；[Terminal-Bench 2.1][tb21] | 二手报道（89）；一手文档（其余） | 2025-11-07 / 2.1 页未显示日期（检索结果标 2026-05-06，未核实） | 中 | 12.1% 未说明是百分点还是相对值；"2.1 中不再有无人解出的任务"；仓库 README 另写 26 个修订任务，见 B27-28 与 C-49 | 20 |
| B20-24 | `network_mode` 默认 `public`；评分器超时默认 600 s；构建超时默认 600 s；Agent 超时默认不设 | Harbor 任务配置默认值 | Harbor | [Harbor config.py][harbor-cfg]（main，2026-10-03 读取） | 一手文档 | 2026-10-03 | 高 | `[agent]`/`[verifier]` 可分阶段覆盖网络；`allow_internet` 已弃用；另见 B14-06 | 14, 16, 20 |
| B20-25 | 108 个任务；31 个自托管 Web 服务；模型评判单任务依赖不超过 50% | OSWorld 2.0 规模与可复现性设计 | OSWorld 2.0 | [arXiv 2606.29537][osworld2] | 论文自述 | 2026-06-28 | 高 | 同时"All web traffic is routed through a residential proxy" | 7, 20 |
| B20-26 | 约 $7,819 / $3,629 / $2,754 | OSWorld 2.0 一次全量（108 个任务）成本：Opus 4.8 / Opus 4.7 / GPT-5.5 | OSWorld 2.0 | 由 B20-13、B20-25 推算 | 笔者推算 | 2026-10 | 中 | 每任务成本 × 108 | 20 |
| B20-27 | 约 7%（GPT-4o）；约 35%（GPT-4o-mini） | WAA 全量费用中 VM 费用占比 | WAA | 由 B20-15 推算（8 ÷ 108；8 ÷ 23） | 笔者推算 | 2026-10 | 中 | — | 20 |
| B20-28 | 116 个 tag；515 个可达提交；PR #581（已关闭、未合并：harness 重构后目标文件不复存在；#578 截至 2026-10-03 仍 open）；9 个实例（1 个 scikit-learn 嵌入修复代码、8 个 Django 链接 PR） | SWE-bench #578 / #669 细节 | SWE-bench | [#578][swebench578]；[#669][swebench669] | 一手文档 | 2026-05-08 / 2026-09-25 | 高 | #669 报告者称"无证据表明有模型利用" | 19, 20 |
| B20-29 | 约 400 MB / 实例；约 3 s vs 约 78 s（后者为未启用 KVM 时的中位数）；256 个任务约 6 分钟；真机保留 95.1% 增益；416 个任务模板（256 测试 + 160 训练）、28 个 App | MobileGym | MobileGym | [arXiv 2605.26114][mobilegym] | 论文自述 | 2026-05 | 高 | 预印本；会议录用情况未核实（arXiv HTML 未注明会议） | 7, 20 |

---

## 第五部分　产品与产业

### 第 21 章　产品推理沙箱

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B21-01 | 闲置超过 Free 7 天 / Pro 21 天回收 | 沙箱回收策略 | Manus | [Manus 博客：Understanding Manus sandbox][manus-blog] | 一手文档 | 2026-01-14 | 高 | 与 E2B 案例"付费保留 14 天"冲突，C-04 | 1, 21, 26, 附录 D |
| B21-02 | 付费用户沙箱数据最多保留 14 天；启动约 150 ms；Docker 拉起 10–20 s；接入半天；27 个工具 | E2B 客户案例中的 Manus | Manus / E2B | [E2B：How Manus uses E2B][e2b-manus] | 厂商自报（营销，附张涛署名引语） | 2025-05-06 | 中 | C-04；同文另有张涛引语"从零重建并维护一套基础设施需要 3–5 名全职基础设施工程师" | 21, 22 |
| B21-03 | 10 个条目 10 个子 agent，500 个条目 500 个 | Wide Research 子 agent 随任务规模伸缩，每个一台完整 VM | Manus | [Manus 博客：Wide Research][manus-wide] | 一手文档 | 2025-10-29 | 高 | 按"一个条目一个子 agent、一个子 agent 一台 VM"，500 条目任务同时占用约 500 台 VM（笔者推算）；文中未说明子 agent 间文件共享方式 | 21 |
| B21-04 | 约 20 亿美元（TechCrunch "$2 billion"；CNBC 原文 403，"以上"未核实）；约 10 亿美元回购（在谈） | Meta 收购金额；创始人回购谈判 | Manus / Meta | [CNBC][cnbc-manus]；[TechCrunch][tc-manus] | 二手报道 | 2025-12-30 / 2026-06-13 | 中 | — | 21, 22 |
| B21-05 | 20 多个工具 | OK Computer 虚拟计算机工具数 | Kimi OK Computer | [Kimi Medium][kimi-okc] | 一手文档 | 2025-10-16 | 高 | 隔离技术未披露 | 21, 26 |
| B21-06 | 最多 300 个子 agent；单任务超过 4,000 次工具调用；比单 agent 串行快 4.5 倍 | Agent Swarm | Kimi | [Kimi 帮助中心][kimi-swarm] | 一手文档 | 2026 | 高 | 未说明每个子 agent 是否独立沙箱 | 21, 26 |
| B21-07 | P90 5 秒（GitHub Codespaces 约 30 秒、Google IDX 约 1 分钟） | 远程容器化工作空间端到端启动 | 字节 Trae Cloud IDE | [智源社区访谈][trae] | 一手文档（访谈） | 约 2025 下半年 | 中 | 日期未标明 | 21, 26 |
| B21-08 | 资源核时降 95.8%（仅元宝 AI 编程场景）；"承载过百亿级调用" | 元宝 AI 编程场景迁至 Cube 后的资源核时降幅；Cube 累计承载调用量 | 腾讯元宝 / Cube | [腾讯云开发者社区][cube-dev] | 厂商自报 | 2026-04-21 | 中 | 标题"OpenAI、Manus 同款"指同类技术，不是说二者在用 Cube；原句："元宝 AI 编程场景迁移至 Cube 后，资源核时消耗降低 95.8%""承载过百亿级调用，支撑元宝等亿级用户产品稳定运行"（2026-10-05 已回中文原文核对）；旧值"超过 1000 亿"差一个数量级，疑为英文摘要把"过百亿级"译作"over 100 billion calls"所致，见 C-47；95.8% 不可写作"元宝整体" | 21, 22, 26 |
| B21-09 | 容器缓存最长 12 小时 | Codex cloud 缓存 | OpenAI Codex cloud | [Codex cloud environment][codex-env] | 一手文档 | 2026 | 高 | secrets 只在 setup 阶段可用（联网文档页无此句，出自 environment 文档页；第 14 章 2026-10-03 读取 cloud environment 页确认"secrets 只对 setup 脚本可用、agent 阶段开始前移除"）；2026-10-06 回原文复核："Codex caches container state for up to 12 hours to speed up new chats and follow-ups"，无需标"未核实" | 1, 21, 27, 附录 D |
| B21-10 | 单会话硬上限 59 分钟；2025-10-28 起支持自托管 runner | Copilot 云 agent | GitHub Copilot | [GitHub Docs][copilot]；[GitHub Changelog][copilot-cl] | 一手文档 | 2025–2026 | 高 | — | 1, 21, 附录 D |
| B21-11 | Temporal 每天处理 5,000 万+ 次动作，涉及 700 万+ 个不同 workflow；40% 内部 PR 由云 agent 生成 | Cursor 云 agent 规模 | Cursor | [Cursor：cloud agent lessons][cursor-cloud] | 一手文档 | 2026-06-02 | 高 | 可靠性见 B09-07；700 万不是"每天"，两数均为工作流引擎计数，不是沙箱数；可靠性原文为"one 9 of reliability"→"past two 9s of reliability"，"约 90% → 99% 以上"为本书换算 | 21, 27 |
| B21-12 | 每天 20 万+ 新项目；"每秒数百个安全沙箱" | Lovable 规模 | Lovable（GKE Agent Sandbox） | [Google Cloud 博客 Next '26][gke-next26] | 厂商自报 | 2026-04-22 | 中 | 峰值 2 万并发见 B01-01 | 5, 21, 22 |
| B21-13 | "A 30-step agent run can't start with a 60-second cold start."；数千并发；2.5 亿美元 ARR（同一引语，2026-10-05 原文核对） | Genspark 选型理由 | Genspark / E2B | [E2B 客户案例：Genspark][genspark] | 厂商自报 | 2026-05-07 | 中 | — | 1, 21, 22 |
| B21-14 | Ubuntu 24.04、x86_64、最多 8 GB RAM、10 GB 磁盘 | 托管云沙箱规格 | Claude Managed Agents | [Claude Platform 文档][claude-ma] | 一手文档 | 2026 | 高 | API 默认网络 unrestricted；Claude Console 默认 limited 且不放行任何主机；allow_package_managers、allow_mcp_servers 默认 false；文档要求"keep secrets and sensitive files out of the sandbox"（Environments 文档，2026-10-05 读取） | 21 |
| B21-15 | 2024-11-14 | ChatGPT 容器（Debian、`/mnt/data`）越权探索披露；OpenAI 定性为预期功能 | ChatGPT | [0DIN][0din] | 二手报道（逆向） | 2024-11-14 | 中 | 0DIN 文章署名行"November 14, 2024"，作者 Marco Figueroa（回原文核对后更正，原记 2024-11-05） | 21 |
| B21-16 | 2025-03-09/10 | 用户导出 `/opt/.manus/` | Manus | [X: jianxliao][manus-leak] | 二手报道（逆向） | 2025-03 | 中 | — | 21 |
| B21-17 | 2026-08-18；2026-08-19 | 豆包 Windows 版"虚拟桌面"；"云电脑"模式上线 | 字节豆包 | [腾讯新闻][doubao-qq]；[科技日报][doubao-std] | 二手报道 | 2026-08 | 中 | 隔离、云厂商未披露 | 21, 26 |
| B21-18 | 1 h 默认、最长 24 h；$0.07/h（1 vCPU/2 GiB）至 $1.12/h（16 vCPU/32 GiB）；暂停不计费 | Docker Cloud Sandboxes | Docker | [Docker 博客][docker-cloud] | 厂商自报 | 2026-09-24 | 中 | — | 21, 22 |
| B21-19 | "100,000+ simultaneous user requests"；"tens of thousands of sandboxes every minute"；启动延迟降 50% 以上 | Kimi 在 ACS Agent Sandbox 上的峰值规模；四项产品（Deep Research、Agentic PPT、OK Computer、数据分析）运行在 ACS MicroVM 上；结果节把产品上线与"the critical model post-training phase"写在同一节，未说明"每分钟数万"属于哪一侧；每请求一个 MicroVM；休眠保留内存、临时存储与 IP；NAS 每 Agent 独立子目录 | 阿里云 ACS / Kimi | [Deep Dive: How Kimi's AI Agent Runs on Alibaba Cloud](https://www.alibabacloud.com/blog/deep-dive-how-kimis-ai-agent-runs-on-alibaba-cloud_602942) | 厂商自报（营销） | 2026-03-12 | 中 | 未写出站、凭据、会话时长、Agent Swarm；与 B26-15 同源数字；两种语境并列呈现，不单独归为产品侧或训练侧 | 1, 21, 22, 26 |
| B21-20 | 2026-08-12；2026-08-23 至 24 | Manus 宣布恢复独立运营；收购日（2025-12-29）及之后产生的部分用户数据删除窗口 | Manus | [Caixin Global Tech Brief Aug. 12](https://www.caixinglobal.com/2026-08-12/tech-brief-aug-12-manus-to-resume-independent-operations-as-meta-deal-unwinds-102473330.html) | 二手报道 | 2026-08-12 | 中 | 未提基础设施与供应商 | 21, 26 |
| B21-21 | 2026-03-16；2026-04-30；Basic / Standard / Advanced 三档 | Manus My Computer（Manus Desktop 桌面应用，在本机终端执行命令，每条终端命令执行前需明确批准）与 Cloud Computer（常驻 Ubuntu VM，"never turns off"，停付后持久沙箱关闭、工作文件删除）发布 | Manus | [Manus Cloud Computer](https://manus.im/blog/manus-cloud-computer)；[Manus My Computer](https://www.manus.im/blog/manus-my-computer-desktop) | 一手文档 | 2026-03/04 | 高 | Cloud Computer 2026-10-05 复核；My Computer 已回原文确认为桌面应用而非 CLI；均未提供应商 | 21 |
| B21-22 | 2025-07-29 | Replit 开发库与生产库默认分离，"the Agent cannot make any change to the production database during development"；可"一键"回滚到任一检查点 | Replit | [Replit 博客 2025-07-29](https://replit.com/blog/doubling-down-on-our-commitment-to-secure-vibe-coding)；[Replit 博客 2025-07-21](https://replit.com/blog/introducing-a-safer-way-to-vibe-code-with-replit-databases) | 一手文档 | 2025-07-29 | 高 | The Register 2025-07-22 转引 CEO 原话（"开始推出数据库开发/生产的自动分离"）作旁证；07-21 博文与事件曝光同日，未提事件；Replit Snapshot Engine 博文未标日期、未提事件 | 2, 12, 21 |
| B21-23 | 一周 125 万次沙箱创建、1,190 万次重连（内部测试期间） | Perplexity SPACE 内部测试数字；Firecracker；凭据不存于沙箱；暂停后最长一周内可恢复 | Perplexity | [SiliconANGLE](https://siliconangle.com/2026/07/15/perplexity-launches-secure-sandbox-make-ai-agents-secure-powerful/) | 二手报道 | 2026-07-15 | 低 | Perplexity 一手原文未找到；原文"1.25 million"，出自内部测试，不写"超过"或"上线首周"（原 B27-26 并入本行） | 21, 27 |
| B21-24 | 会话最长 7 天；暂停后保留 30 天 | 腾讯云 Agent Runtime 会话生命周期 | 腾讯云 | [腾讯云开发者社区](https://cloud.tencent.com/developer/article/2572684) | 一手文档 | 2025-09-29 | 中 | 原文"会话最长生命周期可达7天""最长支持暂停30天"（已回原文复核）；同义行（B22-58 生命周期部分、原 B26-25）并入本行；速率与冷启动口径见 B22-58 | 21, 22, 26 |
| B21-25 | 默认 `local`（"using venv, no env isolation"）；sandbox 模式默认超时 60 s、内存 100 MB；网络白名单默认 `cdn.jsdelivr.net` | Coze Studio 工作流代码运行器默认配置 | 字节 Coze Studio（开源） | [coze-studio `docker/.env.debug.example`](https://github.com/coze-dev/coze-studio) | 一手文档 | 2026-10-05 读取（HEAD fefb05f） | 高 | sandbox 模式为 Deno + Pyodide；六类 Deno 权限白名单默认为空；JS 运行器未支持；SaaS 版扣子隔离方式未披露；原 B26-24 并入本行 | 8, 21, 26 |
| B21-26 | 生命周期 3–1440 分钟（默认 60）；0.25–16 vCPU；0.5–128 GiB | 火山引擎 veFaaS Sandbox API 参数范围 | 火山引擎 | [Pulumi volcenginecc vefaas.getSandbox](https://www.pulumi.com/registry/packages/volcenginecc/api-docs/vefaas/getsandbox/) | 一手文档 | 2026-10 | 中 | 已回 schema 确认（250–16000 milli CPU、512–131,072 MiB）；底层隔离技术未披露；价格见 B22-55；原 B26-23 并入本行 | 21, 22, 26 |
| B21-27 | DNS 域名过滤最多 300 条 | AgentBay 出站过滤上限（支持通配符）；不分配公网 IP、无对外开放端口；API Key 短有效期、可撤销 | 阿里云无影 AgentBay | [AgentBay 安全白皮书](https://help.aliyun.com/zh/agentbay/agentbay-security-white-paper) | 一手文档 | 2025-11-24 | 高 | 每沙箱独立客户机内核 VM；原文"沙箱实例不分配公网 IP 地址，且无对外开放的网络端口"（无"默认"）；"规则未设置时，默认允许访问所有域名"（已回原页确认）；原 B26-27 并入本行 | 7, 14, 21, 26 |
| B21-28 | bubblewrap（Linux）/ Seatbelt（macOS）；出站经沙箱外代理按域名放行；/sandbox 开启 | CodeBuddy Code 本地 Bash 沙箱 | 腾讯 CodeBuddy | [CodeBuddy 文档 Bash Sandbox](https://www.workbuddy.ai/docs/cli/bash-sandboxing)（workbuddy.ai 站） | 一手文档 | 2026-09-30（页面构建时间） | 高 | 原文："Uses bubblewrap for isolation""Uses Seatbelt for sandbox enforcement""Network access is controlled through a proxy server running outside the sandbox""You can enable the sandbox by running the `/sandbox` slash command"；中文站 codebuddy.cn 同名页正文为 JS 渲染未取到；"默认不启用"为推断；CodeBuddy 云端 Agent 隔离仍未披露 | 21 |

### 第 22 章　沙箱与环境的产业化

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B22-01 | $21M A 轮（Insight Partners 领投）；累计 $32M；"88% 的财富 100 强已在平台注册" | E2B 融资 | E2B | [E2B 博客](https://changelog.e2b.dev/blog/series-a)；[SiliconANGLE][e2b-siliconangle]（旁证） | 厂商自报 | 2025-07-28 | 高 | Morph 的"累计 $35M"有误；"94% Fortune 100"仍仅见 bex.co（X-18） | 22 |
| B22-02 | 约 150 ms / < 200 ms / "sub-500 ms" | E2B 冷启动（不同来源） | E2B | [Morph][morph]；[Better Stack][betterstack]；[bex.co 标题][bex-e2b-growth] | 二手报道 | 2026-03 至 2026-07 | 中 | C-18 | 1, 6, 22 |
| B22-03 | $0.0504/vCPU-h + $0.0000045/GiB-s；Pro $150/月；$100 免费额度 | E2B 价格 | E2B | [E2B 定价页][e2b-pricing]（2026-10-02 读取：2 vCPU $0.000028/s，即每 vCPU $0.000014/s ≈ $0.0504/h；1 GiB $0.0000045/s）；Pro 与免费额度沿用 [bex.co][bex-e2b]、[Morph][morph] | 一手文档 | 2026-10-02 读取（二手 2026-04 / 2026-09） | 高 | 常写约 $0.05；bex.co 2026-09-06 另给"2 vCPU/512 MiB 约 $0.109/h" | 22 |
| B22-04 | $0.166/h（默认 2 vCPU/4 GiB）；盈亏平衡约每月 600–700 沙箱小时（对 Hetzner AX42 €97.30/月） | 自托管 AgentENV vs E2B | bex.co 成本分析 | [bex.co 2026-09-22][bex-aenv] | 二手报道 | 2026-09-22 | 中 | — | 22, 25 |
| B22-05 | 2025-03 每月 1,500 万次沙箱运行；增长 375×；累计启动沙箱超过 10 亿个 | E2B 用量 | E2B | [bex.co][bex-e2b]；[bex.co 标题][bex-e2b-growth]；[Bex 融资综述][bex-funding] | 二手报道 | 2025-03 / 2026-07 / 2026-09-11 | 低 | 口径不同，均为二手 | 22 |
| B22-06 | 88% → 94% | 使用 E2B 的 Fortune 100 比例 | E2B | [bex.co][bex-e2b] | 二手报道 | 2026-09-06 | 低 | 未在 e2b.dev 核实 | 22 |
| B22-07 | 约 11k 星 | E2B GitHub 星标 | E2B | [Better Stack][betterstack] | 二手报道 | 2026-03-09 | 低 | 时点数字 | 22 |
| B22-08 | $24M A 轮（FirstMark 领投）；2026-02-05 | Daytona 融资 | Daytona | [Daytona 博客][daytona-blog] | 一手文档 | 2026-02-05 | 高 | Morph 写"2025 年初"，C-17；领投 FirstMark；参投 Pace、Upfront、Darkmode、E2VC；战略投资 Datadog、Figma Ventures；客户 LangChain、Turing、Writer、SambaNova；官方三大用途：代码执行、computer use、强化学习 | 22 |
| B22-09 | 不到 3 个月达到 $1M 前瞻营收年化（forward revenue run rate），六周后翻倍 | Daytona 营收 | Daytona | [Daytona 博客][daytona-blog] | 厂商自报 | 2026-02-05 | 中 | 原文"Six weeks later, it doubled."；博客未说明起算点，不写"A 轮前" | 22 |
| B22-10 | 亚 90 ms；约 $0.05/vCPU-h；$200 额度 | Daytona 冷启动与价格 | Daytona | [Better Stack][betterstack]；[manveerc][manveerc] | 二手报道 | 2026 | 中 | 有报道称已转闭源（Bex） | 6, 22 |
| B22-11 | 300–500 ms（Morph）vs p50 约 100 ms（bex.co） | Modal 冷启动 | Modal | [Morph][morph]；[bex.co][bex-e2b] | 二手报道 | 2026-04-04 / 2026-09-06 | 低 | C-16 | 22 |
| B22-12 | $0.14/vCPU-h（Morph，非可抢占）vs $0.047/vCPU-h（Northflank）；官方价格页（2026-10-04）：沙箱 $0.00003942/物理核·s（$0.1419/核·h，1 核 = 2 vCPU）、$0.00000667/GiB·s（$0.024/GiB·h），约为普通 Function 的 3 倍（笔者按价格页推算） | Modal 价格 | Modal | [Morph][morph]；[Northflank][northflank] | 一手文档 / 二手报道 | 2026-04-04 / 2026-01-17 | 低 | C-16，可能是可抢占与否之别；Morph 的 $0.14 实为每物理核，不是每 vCPU（见 B22-49） | 22 |
| B22-13 | $355M C 轮，投后估值 $4.65B（General Catalyst、Redpoint 领投；Menlo、Bain Capital Ventures、Accel 新进）；年化收入 > $300M；B 轮 $80M 估值 $1.1B（二手） | Modal 融资 | Modal | [Modal 博客](https://modal.com/blog/modal-series-c) | 厂商自报 | 2026-05-21 | 高 | B 轮数字仍为二手（[Bex 融资综述][bex-funding]） | 22 |
| B22-14 | 据报道"接近完成"（closing in on）约 $750M、估值 $15.75B（Accel 领投） | Modal 新一轮 | Modal | [TechCrunch][tc-modal] | 二手报道 | 2026-09-28 | 低 | 单一匿名信源，未确认；Modal 拒绝置评；TechCrunch 另称 Axios、Bloomberg 报道过交易细节；不写"完成"（X-24） | 22 |
| B22-15 | 每客户最多 50,000 个并发沙箱；一分钟内创建一百万个并发沙箱（原页未说明测试条件；原页未见"工程演示"字样） | Modal 规模宣称 | Modal | [Modal RL 页面][modal-rl] | 厂商自报 | 2026-07 | 中 | — | 22 |
| B22-16 | 1 万到 1.5 万个并发沙箱 | E2B 客户 Rogo | E2B（经 Modal 转述） | [Modal RL 页面][modal-rl] | 二手报道（竞品转述） | 2026-07 | 低 | — | 22 |
| B22-17 | $0.128/活跃 vCPU-h；预置内存 $0.0212/GB-h（按分配内存 × 运行时间）；另按创建次数计费；GA 2026-01-30；会话 45 分钟–5 小时；GA 博客："Sub-second startup times for isolated Linux microVMs"（厂商自报）；Pro 会话 24 h、并发 10,000（定价文档，B22-72）与二手"45 分钟–5 小时"并列 | Vercel Sandbox | Vercel | [Vercel Sandbox pricing and quotas][vercel-pricing]（last_updated 2026-09-10）；GA 日期：[Vercel 博客][vercel]；会话时长：[bex.co][bex-e2b]、[Northflank][northflank] | 一手文档 / 二手 | 2026-01-30 / 2026-09-10 | 中 | GA 博客没有单价 | 22 |
| B22-18 | $0.000020/vCPU-s（按活跃用量）；内存 $0.0000025/GiB-s、磁盘按预置量；标准计划 15,000 lite / 6,000 basic / 1,000+ 更大规格并发实例 | Cloudflare Sandbox 价格与上限 | Cloudflare | 单价：[Cloudflare Containers Pricing][cf-pricing]（last updated 2026-04-21）；并发上限：[Cloudflare 博客][cf-blog]、[InfoQ][infoq-cf] | 一手文档 | 2026-04-13 / 2026-04-21 | 高 | 博客没有单价 | 22 |
| B22-19 | $0.03825/CPU-h、内存 $0.021875/GB-h（running 计费，warm/cold 不计费；官方页 2026-10-02 读取）；2026-01 二手报道为 $0.07/CPU-h；100 GB NVMe；$5/月 Hobby；2026-01-13 发布 | Fly.io Sprites | Fly.io | [fly.io/sprites][sprites]；[Better Stack][betterstack]；[Techzine][techzine] | 一手文档 / 二手报道 | 2026-10-02 读取 / 2026-01 | 中 | 二手旧价与官方现价不同，可能已调价 | 22 |
| B22-20 | $0.01667/vCPU-h、$0.00833/GB-h、H100 $2.74/h；每月 2M+ 隔离负载 | Northflank | Northflank | [Northflank 博客][northflank] | 厂商自报 | 2026-01-17 | 中 | — | 22 |
| B22-21 | $7.3M 种子轮（First Round 领投）；2026-09-10 被 Baseten 收购 | Blaxel | Blaxel | [Blaxel 博客][blaxel-seed]；[BusinessWire][bw-baseten] | 一手文档 | 2026-09-10 | 高 | 种子轮日期未取得；新闻稿称 Blaxel 沙箱"启动和恢复速度最高比竞品快 5 倍"（厂商自报）；条款未披露；$7.3M 种子轮未回原文核实 | 22 |
| B22-22 | 累计融资超过 $20 亿；F 轮估值 $130 亿（新闻稿另提及 $15 亿 F 轮公告） | Baseten 此前融资 | Baseten | [BusinessWire][bw-baseten] | 一手文档 | 2026-09-10 | 中 | — | 22 |
| B22-23 | $7M 种子轮；2025-07-30；团队 12 人 | Runloop | Runloop | [Runloop 新闻稿][runloop] | 一手文档 | 2025-07-30 | 高 | — | 22 |
| B22-24 | $0.04/vCPU-h；启动 100 ms / < 800 ms / 亚 600 ms | Freestyle | Freestyle | [Morph][morph]；[Better Stack][betterstack] | 二手报道 | 2026 | 低 | 启动数字三方冲突 | 22 |
| B22-25 | 每秒创建 300 个沙箱；Axion 上性价比最多高 30% | GKE Agent Sandbox | Google | [Google Cloud：What's new in GKE at Next '26][gke-next26]；[InfoQ][infoq-gke]（转述） | 厂商自报 | 2026-05-07 | 中 | 开源项目 kubernetes-sigs/agent-sandbox 于 2025 年 KubeCon NA 作为 SIG Apps 子项目发布（InfoQ）；GKE 托管形态在 Cloud Next '26 前后推出；一手原文："300 sandboxes per second at sub-second latency"；"Built with gVisor kernel isolation (same technology securing Gemini)"；同博客列"RL Sandbox（Preview）：Kernel-level isolation with millisecond-scale provisioning"，隔离实现未说明，不得推断为 gVisor（X-14）；Google 博客未提 warm pool 与 Kata；Kata 支持出自开源项目 kubernetes-sigs/agent-sandbox 文档 | 5, 9, 22 |
| B22-26 | 40+ 区域 | Azure Container Apps dynamic sessions 可用区域 | Microsoft | [Microsoft Learn][azure-sessions] | 一手文档 | 2026 | 高 | — | 22 |
| B22-27 | Beta 期约 3,000 万个沙箱；示例看板 > 20,000 并发；默认并发上限 1,024；"tens of thousands of concurrent sandboxes"；促销价至 2026-12-22：$0.02/vCPU·h、$0.0125/GiB·h、磁盘 $0.0002/GiB·h，自称比其他供应商便宜 3 倍；未点名客户（促销价另见 B22-51） | Prime Sandboxes | Prime Intellect | [Prime Sandboxes 博客][prime-sandboxes] | 厂商自报 | 2026-09-23 | 中 | — | 22, 27 |
| B22-28 | $130M A 轮（Radical Ventures 领投）；累计 > $150M；6,000 个客户；ARR > $1 亿 | Prime Intellect 融资 | Prime Intellect | [Prime 官方博客][prime-seriesA]；[PYMNTS][pymnts-prime] | 厂商自报 | 2026-07-08 | 中 | 估值 $10 亿仅见 SiliconANGLE 标题，官方未披露；具名案例为 Ramp；估值未披露（X-25） | 22 |
| B22-29 | 2026-06-11；Codex 周活用户超过 500 万 | OpenAI 收购 Ona（原 Gitpod） | OpenAI | [SiliconANGLE][siliconangle-ona]；[The Decoder](https://the-decoder.com/openai-buys-ona-to-push-codex-toward-long-running-autonomous-coding-tasks/) | 二手报道 | 2026-06-11 | 高 | 条款未披露；"尚需监管批准"（subject to regulatory approvals）与"用户合上笔记本后"（even when the user's laptop is closed）出自 The Decoder；SiliconANGLE 只写条款未披露、"hours or days"、周活 > 500 万 | 22, 27 |
| B22-30 | 单任务大多 $200–$2,000，$20k 很少见但可能；网站复刻约 $20k（Epoch 转引 SemiAnalysis，非受访者）；Slack 类复刻约 $300k；一位 RL 环境公司创始人称合同"常为每季度七位数或以上"；一位新兴实验室研究员见过 $300k–$500k 的合同；独占约为非独占的 4–5 倍 | RL 环境定价 | Epoch AI（访谈综述） | [Epoch][epoch] | 二手报道（访谈综述） | 2026-01-12 | 中 | 访谈：9 人通话、9 人提供文字或邮件意见，另 4 人只做合理性检查、未提供内容（共 22 人）；两个合同数字各出自一位受访者，均不写"典型"；环境"常以 Docker 容器交付，但并非总是如此"；原文："one RL environment founder noted that contracts are often seven figures per quarter or more"；"A neolab researcher mentioned seeing contracts in the $300k-$500k range"；"SemiAnalysis reported that website replicas ("UI gyms") cost around $20k each." | 22, 27 |
| B22-31 | 约 2,400 美元 | RL 期间每个任务的算力成本 | Mechanize 估计（经 Epoch） | [Epoch][epoch] | 二手报道 | 2026-01-12 | 低 | — | 22 |
| B22-32 | 35 家以上环境供应商；多为种子期、不足 20 人、1–3 个实验室客户 | 供应商格局 | SemiAnalysis | [SemiAnalysis][semianalysis] | 二手报道 | 2026-01-06 | 中 | — | 22 |
| B22-33 | Surge ARR 约 $10 亿（估计）；Scale AI 2024 年收入 > $14 亿 | 数据厂商规模 | SemiAnalysis | [SemiAnalysis][semianalysis] | 二手报道 | 2026-01-06 | 低 | TechCrunch 写 Surge 上年营收 $12 亿，C-28 | 22 |
| B22-34 | 超过 10 亿美元 / 年 | Anthropic 高层讨论的 RL 环境投入 | Anthropic（经 The Information） | [TechCrunch][techcrunch-env]；[Epoch][epoch] | 二手报道 | 2025-09-21 | 低 | 讨论，非已发生支出 | 22, 27 |
| B22-35 | "1,000 万美元以上" | 顶级实验室为单个环境支付 | Nathan Lambert（经 HF 博文） | [HF：One sandbox per rollout][hf-rl] | 二手报道 | 2026-09-11 | 低 | 未追溯到一手 | 22 |
| B22-36 | Mechanize 开出 $500k 年薪；Mercor 估值 $100 亿；Mechanize 种子 $9.1M | 环境公司人才与资本 | 多家 | [TechCrunch][techcrunch-env]；[Mechanize][mechanize] | 二手报道 | 2025-09-21 | 低 | Mechanize 种子日期未核实 | 22 |
| B22-37 | 三类（数据巨头 / 环境原生创业 / 开放生态与基础设施）；定价"几乎全部定制" | 供应商分类 | Troveo | [Troveo][troveo] | 二手报道 | 2026-08-09 | 中 | — | 22 |
| B22-38 | 云电脑/云手机 1 积分/小时，浏览器、Code Space 0.5 积分/小时；1 积分 = 1.2 元（约 1.2 元/小时、0.6 元/小时） | 中国 GUI 沙箱价格锚点 | 阿里 AgentBay | [阿里云 AgentBay 计费][agentbay-bill] | 一手文档 | 页面更新于 2025-09-11（2026-10-05 再次核对） | 高 | 整点结算已核；"秒级计量"仅见于一次摘要式读取，回原文未见，标未核实 | 7, 22 |
| B22-39 | 千个环境并发约 1,200 元/小时 | 1.2 元 × 1,000，未计折扣 | AgentBay | 由 B22-38 推算 | 笔者推算 | 2026 | 中 | 假设单环境占用 1 小时 | 7, 22 |
| B22-40 | CPU ¥0.000081/核/秒（约 ¥0.29/核/小时）；内存 ¥0.000025/GiB/秒（约 ¥0.09/GiB/小时）；系统盘 ¥0.0021/GiB/小时；每实例 15 GiB 免费 | 腾讯 AGS 计费 | 腾讯云 Agent Runtime | [腾讯云计费文档][ags-price] | 一手文档 | 2026-09-09 | 高 | 约 $0.04/核-小时（笔者推算），与 E2B 同量级；按秒计费，不足 1 秒按 1 秒；暂停后 CPU、内存停止计费，系统盘继续计费（计费页原文） | 22, 26 |
| B22-41 | 中国内地 vCPU ¥0.0000217/秒（¥0.078/小时）、内存 ¥0.00001083/GiB·秒（¥0.039/GiB·小时）；港澳及海外 ¥0.0000342/秒（¥0.1232/小时）、¥0.00001711/GiB·秒（¥0.0616/GiB·小时） | 阿里 ACS Agent Sandbox 价格 | 阿里云 ACS | [阿里云 ACS 文档][acs-doc] | 一手文档 | 2026-06-22 | 高 | 秒价 × 3,600 = 小时价，单位无误（2026-10-05 已回原文核对）；按秒计费、按小时出账；运行态 30 GiB 以内临时存储免费；休眠态不收 CPU 与内存费，存储全额计费；营销稿另有经济型 0.060/0.030、性能型 0.120/0.060（元/时）两档，官方概述页未列；C-07 已解决，X-08 已删除 | 1, 21, 22 |
| B22-42 | 约 10 亿元（蚂蚁领投） | 光轮智能融资（物理仿真，非软件 Agent 沙箱） | 光轮智能 | [投中网][chinaventure] | 二手报道 | 2026-03 | 中 | 本书检索范围内未找到中国沙箱/RL 环境创业公司融资 | 22 |
| B22-43 | 超过 $10 亿，估值 $260 亿 | Cognition 同期融资（背景） | Cognition | [Bex 融资综述][bex-funding] | 二手报道 | 2026 | 低 | — | 22 |
| B22-44 | "more than a third of our revenue"；> $300M 年化收入；> 10 亿个沙箱 | 沙箱收入占比；年化收入；平台累计启动沙箱 | Modal | [Modal Series C](https://modal.com/blog/modal-series-c) | 厂商自报 | 2026-05-21 | 中 | 目前唯一可单独量化沙箱收入的官方数字 | 22 |
| B22-45 | 1 亿美元以上 | Modal 沙箱年化收入 | Modal | 由 B22-44 推算：300M × 1/3 | 笔者推算 | 2026-05 | 中 | 下限估计 | 22 |
| B22-46 | 约 €21M（约 $22.3M）；种子 + A 轮合计约 $24.9M | Northflank A 轮（Bain Capital Ventures 领投） | Northflank | [tech.eu](https://funding.tech.eu/deals/731FA7B2-5977-47E0-B00A-F611BBC582D6)；rywalker | 二手报道 | 2024-11 | 低 | 2026 年未检索到新一轮；未能回原文核对，未核实 | 22 |
| B22-47 | 约 3 秒；每周 200 万个 VM | CodeSandbox SDK 从运行中 VM 或快照克隆；底层处理量 | CodeSandbox（Together AI） | [CodeSandbox 博客](https://codesandbox.io/blog/joining-together-ai-introducing-codesandbox-sdk) | 厂商自报 | 2024-12-12 | 低 | 与 ComputeSDK 中位 7.53 s 口径不同；未能回原文核对，未核实 | 22 |
| B22-48 | $0.0504/vCPU·h；$0.0162/GiB·h；存储 $0.000108/GiB·h；Windows $0.0858/vCPU·h；新用户 $200 额度 | Daytona 价格 | Daytona | [daytona.io/pricing](https://www.daytona.io/pricing) | 一手文档 | 2026-10-04 读取 | 高 | "Price per GiB after first 5 free"指存储；B22-10 的"约 $0.05"由此确认 | 22 |
| B22-49 | $0.1419/物理核·h；$0.024/GiB·h；约为 Function 单价的 3 倍（笔者推算：0.00003942 ÷ 0.0000131）；H100 $0.001097/s | Modal 沙箱价格 | Modal | [modal.com/pricing](https://modal.com/pricing) | 一手文档 / 笔者推算 | 2026-10-04 读取 | 高 | 1 核 = 2 vCPU；页面"3x base prices"指 non-preemptible 选项，与此处 3 倍无关；见 B22-12、C-16 | 22 |
| B22-50 | $0.108/CPU·h（$0.00003/s）；$0.0252/GB·h；Pro $250/月；Blueprint 构建 $0.252/h | Runloop 价格 | Runloop | [runloop.ai/pricing](https://www.runloop.ai/pricing) | 一手文档 | 2026-10-04 读取 | 高 | — | 22 |
| B22-51 | $0.02/vCPU·h；$0.0125/GiB·h；$0.0002/GiB·h（磁盘）；"3x cheaper" | Prime Sandboxes 促销价（至 2026-12-22） | Prime Intellect | [Prime Sandboxes 博客](https://www.primeintellect.ai/blog/sandboxes) | 一手文档 / 厂商自报 | 2026-09-23 | 高 | 促销价，到期后价格未披露 | 22 |
| B22-52 | 1 vCPU/2 GiB $0.07/h；2/4 $0.14；4/8 $0.28；8/16 $0.56；16/32 $1.12；默认 1 h、最长 24 h；新账户 $250 额度 | Docker Cloud Sandboxes 价格与会话 | Docker | [Docker 博客](https://www.docker.com/blog/introducing-cloud-sandboxes-start-on-your-laptop-finish-in-the-cloud/) | 一手文档 | 2026-09-24 | 高 | 按秒计量（仅计算），暂停不计费，卷与出站免费；见 B21-18 | 22 |
| B22-53 | 2 vCPU/4 GiB 每小时：Northflank 约 $0.067、Prime 约 $0.09、Docker $0.14、Sprites 约 $0.164、E2B/Daytona 约 $0.166、Cloudflare 约 $0.18、Modal 约 $0.238、Runloop 约 $0.317、Vercel 约 $0.341；10% 活跃时 Cloudflare 约 $0.05、Vercel 约 $0.11；内存占比约 71%、约 77% | 同规格标价账单 | 多家 | 由 B22-03、B22-17–20、B22-48–52 推算（第 22 章表 22-2 列算式） | 笔者推算 | 2026-10 | 中 | 忽略 GiB/GB 差异、免费额度、存储与创建费；算式已复算 | 13, 22 |
| B22-54 | $0.027/核·h；$0.0113/GB·h；Pro $149/月、Ultra $225/月；$0.0267/credit | AgentBay 国际站价格 | 阿里云无影 | [AgentBay 计费（日文）](https://www.alibabacloud.com/help/ja/agentbay/product-overview/agentbay-billing-instructions) | 一手文档 | 2026-06-25 | 低 | 与国内积分制（B22-38）口径不同；国内人民币按核价未核；未能回原文核对，未核实 | 22 |
| B22-55 | 生命周期 3–1,440 分钟（默认 60）；0.25–16 vCPU；0.5–128 GiB；价格未披露 | 火山引擎 veFaaS Sandbox 参数 | 火山引擎 | [Pulumi volcenginecc schema](https://www.pulumi.com/registry/packages/volcenginecc/api-docs/vefaas/getsandbox/) | 一手文档 | 2026 | 中 | 参数范围同 B21-26；AgentKit 价格页 JS 渲染未取得 | 22, 26 |
| B22-56 | ACS 约 ¥0.31（约 $0.044）；AGS 约 ¥0.94（约 $0.13）；ACS 约为 E2B 的 1/4 | 2 vCPU/4 GiB 每小时 | 阿里云、腾讯云 | 由 B22-41、B22-40、B22-03 推算；汇率按 1 美元 ≈ 7.1 元（笔者假设） | 笔者推算 | 2026-10 | 中 | 复算：ACS ¥0.312、AGS ¥0.943 | 22 |
| B22-57 | < 200 ms | PPIO E2B 兼容沙箱启动（Firecracker） | PPIO 派欧云 | [PPIO 文档](https://ppio.com/docs/sandbox/e2b-compatible)；[AIbase](https://news.aibase.com/zh/news/20030) | 厂商自报 | 2025-07-28 | 低 | 未公布价格；未能回原文核对，未核实 | 22 |
| B22-58 | 冷启动 < 100 ms；每分钟 10 万以上实例（公测文）/ 数十万实例/分钟（产品页） | 腾讯 Agent Runtime 冷启动与创建速率 | 腾讯云 | [腾讯云开发者社区](https://cloud.tencent.com/developer/article/2572684)；[AGS 产品页](https://cloud.tencent.com/product/ags) | 厂商自报 | 2025-09-29 / 2026 | 低 | 两处速率口径不同（见 C-08）；会话生命周期（7 天 / 30 天）见 B21-24；本行速率与冷启动未能回原文核对，未核实 | 21, 22, 26 |
| B22-59 | "分钟级调度数十万沙箱实例"；"过百亿级调用"；元宝 AI 编程场景资源核时降 95.8% | Cube 支持 MiniMax Agentic RL；调用量；元宝场景 | 腾讯 Cube | [腾讯云开发者社区](https://cloud.tencent.com/developer/article/2657863) | 厂商自报 | 2026-04-21 | 中 | 已回中文原文逐字确认三句；旧稿"超过 1000 亿""数万"有误（见 B21-08、B26-10、C-47） | 21, 22, 26 |
| B22-60 | 数百万美元（百度风投、初心资本） | CoreSpeed 融资（Agent-native runtime PaaS，容器启动 127 ms） | CoreSpeed | [36 氪](https://36kr.com/p/3552832377371780) | 二手报道 | 2025-11-14 | 低 | 未经一手核实；不足以推翻"无经核实的中国沙箱创业公司融资"；未能回原文核对；36 氪 2025-11-14（作者硅兔君），原文称"每个用户的智能体实例在独立容器中运行"（2026-10-06 补日期） | 22 |
| B22-61 | 超过 7 亿元 | 无问芯穹融资（无单独沙箱或 RL 环境产品） | 无问芯穹 | [新浪财经](https://finance.sina.com.cn/wm/2026-05-07/doc-inhwzvzh7738591.shtml) | 二手报道 | 2026-05-07 | 中 | 非沙箱融资 | 22 |
| B22-62 | 70 万个沙箱；"数千个并发"；启动 30 分钟 → 不到 5 秒 | Trajectory RL 后训练管线 | Daytona 客户 | [Daytona 客户案例](https://www.daytona.io/customers/trajectory) | 厂商自报 | 页面未标日期 | 低 | 未能回原文核对，未核实；见附录 E C22-09 | 17, 22 |
| B22-63 | "hundreds of concurrent sandboxes"（Mistral）；"thousands of sandboxes in parallel per training step"（IBM Research） | Mistral 在 CoreWeave CPU 节点与 GPU 节点（与 Slurm 并行）上的并发沙箱；IBM Research 每训练步并行沙箱 | CoreWeave 客户 | [CoreWeave 新闻稿](https://coreweave.com/news/coreweave-sandboxes-launches-to-accelerate-reinforcement-learning-agent-tool-use-and-model-evaluation) | 厂商自报（客户引语） | 2026-05-14 | 中 | 一手来源取代 Modal 竞品页转述（C22-23）；与 B27-03、B27-04 同源；新闻稿称单个沙箱的故障或失控进程"不会影响任何其他沙箱"，未说明隔离技术 | 17, 22, 27 |
| B22-64 | 约 2–3%（64 或 128 次 rollout 中至少成功 1 次） | 环境最低通过率 | Epoch 访谈 | [Epoch][epoch] | 二手报道（访谈综述） | 2026-01-12 | 中 | — | 18, 22 |
| B22-65 | "on the order of tens of millions annually"（Anthropic）；各实验室**合计**环境支出 2026 年可能增长 3–5 倍；Applied Compute 估值 $1.3B（转引） | Anthropic RL 环境支出估计与全行业增长估计 | Wing VC | [Wing](https://www.wing.vc/content/rl-environments-for-agentic-ai-who-will-win-the-training-verification-layer-by-2030) | 二手报道 | 2026-01 | 低 | Wing 文中无利益披露；"Wing 领投 Bespoke Labs A 轮"依据 TAMradar（二手）；3–5 倍是全行业而非 Anthropic；与 B22-34 相差一个数量级以上，见 C-45 | 22 |
| B22-66 | "hundreds of enterprise applications"；Deeptune A 轮 $43M（a16z 领投）；Mercor "more than five million domain experts" | Mercor 收购 Deeptune | Mercor / Deeptune | [Mercor 博客](https://www.mercor.com/blog/mercor-to-acquire-deeptune/)；[a16z](https://a16z.com/announcement/investing-in-deeptune/) | 一手文档 | 2026-07-09 / 2026-03-19 | 高 | 收购价未披露 | 22 |
| B22-67 | 约 $2B run-rate；约 $20B 估值洽谈；2025-10 C 轮 $350M、估值 $10B | Mercor 收入与估值 | Mercor | [KuCoin/CryptoBriefing](https://www.kucoin.com/news/flash/mercor-in-talks-for-20b-valuation-amid-ai-training-demand-surge) | 二手报道 | 2026-07 | 低 | 未证实；与 B22-36 的"估值 $100 亿"（2025-09）时点不同；未能回原文核对 | 22 |
| B22-68 | 超过 $1.5B；非独占授权；联合创始人与十余名员工加入 Google DeepMind | Google–Mechanize 人才加授权交易（报道交割 2026-09-11） | Google / Mechanize | [AI Weekly 转述 Business Insider](https://aiweekly.co/alerts/google-closes-15b-mechanize-talent-deal-epoch-ai-cofounder-joins-deepmind) | 二手报道 | 2026-08-05 / 2026-09-11 | 低 | 未证实，Google 未正式确认；BI 原文未取到 | 22 |
| B22-69 | 年化收入约 $1M（2025 年）→ 约 $60M（2026-04，Sacra 研究估计："Fleet hit $60M in annualized revenue in April 2026, up from $1M in annualized revenue in 2025"）；估值约 $750M；融资至少 $50M；此前种子 $15M | Fleet 收入与融资 | Fleet | [Sacra](https://sacra.com/c/fleet)；[KuCoin 2026-04-14](https://kucoin.com/news/flash/ai-training-firm-fleet-eyes-750m-valuation-amid-60x-revenue-surge) | 二手报道 | 2026-04 | 低 | 未见官方公告；"2025 年"不写"2025 年底" | 22 |
| B22-70 | $40M（种子 + A 轮） | Bespoke Labs 融资（Wing 领投 A 轮，8VC 领投种子） | Bespoke Labs | [TAMradar](https://www.tamradar.com/funding-rounds/bespoke-labs-series-a-40m) | 二手报道 | 2026-07-06 | 低 | 未能回原文核对，未核实 | 22 |
| B22-71 | 100 个并发一次突发；10 s 上限；中位 60%、p95 25%、p99 15% 加权 × 成功率；2026-10-02 中位/p95：Isorun 0.07/0.08 s、Daytona 0.33/0.42、Vercel 0.48/0.71、Cloudflare 0.54/0.73、Blaxel 0.89/1.72、Runloop 1.11/1.19、E2B 1.28/1.60、Modal 1.57/2.23、CodeSandbox 7.53/9.82、Northflank 成功率 0 | ComputeSDK Burst TTI（create() 到首次 runCommand() 成功） | ComputeSDK（Snelling, LLC；Namespace 4 vCPU/16 GB、北弗吉尼亚） | [ComputeSDK Burst TTI](https://computesdk.com/benchmarks/sandboxes/burst-tti)；[GitHub](https://github.com/computesdk/benchmarks) | 一手文档（第三方，有供应商赞助） | 2026-10-02 运行，2026-10-05 读取 | 中 | 赞助商含 Google Cloud Run 等，Google 有自家沙箱；单次运行；参评数见 C-43；已回原文核对，全部一致 | 6, 22 |
| B22-72 | 并发 10,000；vCPU 分配速率上限 5,000/分钟；会话 24 h（Pro） | Vercel Sandbox 配额 | Vercel | [Vercel 文档](https://vercel.com/docs/vercel-sandbox/pricing) | 一手文档 | 2026-09-10 | 高 | 与 B22-17 会话"45 分钟–5 小时"（二手）不同，宜并列 | 22 |
| B22-73 | 约 $0.08 | 假设单条 150 步轨迹占 2 vCPU/4 GiB 沙箱 30 分钟时的 E2B 标价费用 | — | 0.166 ÷ 2；30 分钟为笔者假设 | 笔者推算 | 2026-10 | 低 | 仅用于说明沙箱费用与每任务 RL 算力（B22-31）的量级关系 | 22 |

### 第 23 章　标准与治理

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B23-01 | 2026-09-18 发布；2026-10-02 截止 | 《智能体系统开发安全指南（征求意见稿）》征求意见 | TC260 | [TC260 通知][tc260] | 一手文档 | 2026-09-18 | 高 | 附件已取得（v1.0-202609，26 页，10 章，12 家起草单位，编号栏"TC260-PG-2026NA"）；第 8 章 n）项第 1）条以"应"要求将模型推理、工具执行、代码执行置于"适当的沙箱、容器或其他隔离边界内"；通知文号网安秘字〔2026〕119 号；经网页文本提取，逐字以 PDF 为准（见 B23-11） | 23 |
| B23-02 | TC260-TR-005-2026；2026-03-26（通知日期，网安秘字〔2026〕34 号）；92 页（未核实）；五类标准体系；11 类核心风险 | 《智能体安全标准化研究》技术报告 | TC260 | [安全内参转载通知](https://www.secrss.com/articles/89139)（2026-04-03）；[搜狐转载摘要][tc260-tr] | 转载的官方通知（日期）；二手（页数与内容） | 2026-03-26 | 中 | 全文仍未核实（2026-10-06 再查未得，TC260 附件下载链接需浏览器会话）；原写 2026-04-09 为搜狐转载日期（X-54）；勿与 SESEC 网站英译"TC260-005"（人工智能应用伦理安全指引）混淆 | 23 |
| B23-03 | 2025-09-15 发布；专家解读 2025-09-28 | 《人工智能安全治理框架》2.0 | 国家网信办指导、国家互联网应急中心牵头 | [网信办专家解读][cac-framework]；[扬子晚报](https://www.yzwb.net/news/yw/202509/t20250915_264528.html) | 专家解读（非框架原文）/ 二手报道 | 2025-09-28 | 中 | "紧急停机"出自网信办网站专家解读（洪延青）；框架原文有无隔离执行环境未核实 | 23 |
| B23-04 | 2026-03-16 启动；2026-04-15 评估体系 2.0（8 个维度）；配套 1 项国际标准、10+ 项行业标准、20+ 项联盟规范；2026-06-12 发布上半年结果 | 可信 AI 智能体评估 | 中国信通院 | [21CSP][caict-21csp]；[经济观察网][caict-eeo] | 二手报道 | 2026 | 中 | 未找到专门沙箱评估项；八大维度含"运维管理"（非"运营管理"）；维度一"智能体基础设施"写"重点关注智能体运行环境、硬件资源适配、异构兼容、弹性扩展等能力"，"运行环境"为能力意义，非隔离（21CSP，2026-10-05 复核） | 23 |
| B23-05 | 2025-07-10 发布；2025-08-02 起义务生效；4 类系统性风险 | EU GPAI 行为准则安全章节 | 欧盟 | [CSET 解读][cset] | 二手报道 | 2025-07 | 中 | CSET 未提 agent containment；准则安全章节 PDF（镜像，抓取截断于附录 3.5）已读部分无 sandbox/isolation/containment，仅 Measure 5.1 提"safe ecosystems of AI agents"；附录 4 未读到（2026-10-05） | 23 |
| B23-06 | 2026-01-08 联邦公报刊登 RFI（NIST-2025-0035；二手指南记 2026-01-12）；2026-02-05 NCCoE 概念文件（征求意见至 2026-04-02）；2026-02-17 AI Agent Standards Initiative（三大支柱）；2026-03-09 截止；2026-05-18 回复分析（Trustworthy and Responsible AI 800-5，作者 5 人）；截至 2026-10-05 无定稿 | NIST CAISI 时间线 | NIST CAISI | [联邦公报](https://www.govinfo.gov/content/pkg/FR-2026-01-08/html/2026-00206.htm)；[NIST 公告](https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure)；[NIST 出版物页](https://www.nist.gov/publications/summary-analysis-responses-request-information-regarding-security-considerations-ai)；[CASRAI 指南][casrai]；[ANSI][ansi] | 一手文档（联邦公报、NIST 公告与出版物页）/ 二手报道（CASRAI） | 2026 | 高 | RFI 4(a)(b)(d) 问及约束与监测部署环境，原文无"sandbox"；回复分析全文 PDF 未取得；01-08 与 01-12 并列（C-50） | 23 |
| B23-07 | 2026-02-24 生效 | Anthropic RSP v3.0（SL4 降为行业建议；每 3–6 个月 Risk Report） | Anthropic | [RSP v3.0](https://www.anthropic.com/responsible-scaling-policy/rsp-v3-0)；[GovAI 分析][govai] | 一手文档 | 2026-02-24 | 高 | "We will publish a Risk Report every 3-6 months."；内部部署模型落入范围后 30 天内在系统卡或他处发布讨论；SL4 一句位于"Mitigations—ambitious industry-wide recommendations"栏；SL5 不可行为 GovAI 转述 Anthropic 一方看法；全文无 sandbox/isolat/egress | 23, 27 |
| B23-08 | 2025-04-15 | OpenAI Preparedness Framework v2 | OpenAI | [OpenAI][openai-pf] | 一手文档 | 2025-04-15 | 高 | 2026-10-05 复核：High 能力须有保障措施方可部署，Critical 在开发期间亦需；PF 本身无沙箱条款；其配套合规文件 Frontier Governance Framework（2026-05-28）有沙箱句，见 B23-19 | 23 |
| B23-09 | 2025-09-22（v3）；2026-04-17（v3.1） | Google DeepMind Frontier Safety Framework v3 / v3.1 | Google DeepMind | [DeepMind 博客][gdm-fsf]；[FSF v3.1 PDF](https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/strengthening-our-frontier-safety-framework/frontier-safety-framework_3-1.pdf) | 一手文档 | 2025-09-22 / 2026-04-17 | 高 | v3.1 §2.1.1 Security Level 2+："mandating that the processing of untrusted inputs occurs within sandboxed environments"（权重保护语境）；§3.1.2"limiting affordances, monitoring and escalation, auditing"；未把训练/评测执行环境写成承诺项 | 23, 28 |
| B23-10 | 2026-05-08；3 个部门 | 网信办、国家发展改革委、工业和信息化部联合部署《智能体规范应用与创新发展实施意见》 | 网信办、发改委、工信部 | [网信办][cac-agent]；[新华网](https://www.news.cn/politics/20260508/13043a992f834853a7ce009ba7ecaabc/c.html) | 一手文档 | 2026-05-08 | 中 | 经抓取：无"沙箱""隔离"；提"越权操作、行为失控"风险与决策权限边界，提出制定智能体标准化工作指导文件 | 23 |
| B23-11 | v1.0-202609；26 页；10 章；12 家起草单位；"TC260-PG-2026NA" | 《智能体系统开发安全指南（征求意见稿）》版本、页数、结构、起草单位数、编号栏 | TC260 秘书处 | [征求意见稿 PDF](https://www.tc260.org.cn/tc260/tzgg/202609/e5b82ae7aca244d19d36b39575cbb458/files/《网络安全标准实践指南——智能体系统开发安全指南（征求意见稿）》.pdf.pdf) | 一手文档 | 2026-09 | 高 | 经网页文本提取；第 8 章 n）项（第 1）条）为沙箱条款；无附录 | 23 |
| B23-12 | TC260-PG-20266A；v1.0-202607；7 项 | 《智能体部署使用安全指引》编号、版本；第 7 章 d）项所列待补强安全能力数（含"基于沙箱等技术的环境隔离"） | TC260 秘书处 | [指引 PDF](https://www.tc260.org.cn/tc260/sjzn/202608/67702dcf57214da792499be8518446dc/files/f3be1cc4d35d428c98a9f5d197c963ac.pdf) | 一手文档 | 2026-07 | 高 | 发布日期冲突见 C-51 | 23, 28 |
| B23-13 | 国标委发〔2026〕41 号；2026-06-27；29 项；20263116-Q-252；18 个月；3 家起草单位 | 强制性国家标准《智能体应用安全基本要求》计划 | 国家标准委（主管：中央网信办；归口：TC260） | [国标委通知 PDF（新疆市场监管局转载）](https://scjgj.xinjiang.gov.cn/xjaic/tzgg/202607/4e9fe0cc06484829908fe75adca8f240/files/国家标准委关于下达《智能体应用安全基本要求》等29项强制性国家标准计划和相关标准外文版计划的通知.pdf)；[新华网](https://www.news.cn/tech/20260728/8ebf5083cf0e487287f894fb31e123f5/c.html) | 一手文档 | 2026-06-27 | 高 | 起草单位：中国移动、电子标准院、CNCERT；草案未公开；CGTN 英文名与官方中文名不一致，以官方为准 | 23, 28 |
| B23-14 | 约 2027 年底 | 《智能体应用安全基本要求》最早报批时间 | — | 2026-06 + 18 个月 | 笔者推算 | 2026-10 | 低 | 仅为周期推算 | 23 |
| B23-15 | 2026-05-01；6 家机构；5 国 | ASD's ACSC、CISA、NSA、CCCS、NCSC-NZ、NCSC-UK 联合指南《Careful adoption of agentic AI services》 | 五眼机构 | [指南 PDF](https://www.cyber.gov.au/sites/default/files/2026-05/careful_adoption_of_agentic_ai_services.pdf)；[CISA 公告](https://content.govdelivery.com/accounts/USDHSCISA/bulletins/41544ff) | 一手文档 | 2026-05-01 | 高 | 原文："Implement isolation and segmentation to limit blast radius of agent failure scenarios"；"Isolate agents into enclaves with no write access to logs"；"Deploy sandbox environments to test agent behaviour before production deployment"；"containment mechanisms that limit the blast radius of unexpected behaviours"；附录 A"secure, sandboxed environment"；"should not be regarded as legal advice"。Mayer Brown"在可能时进行隔离"在原文无对应句，不再引用 | 23, 28 |
| B23-16 | 2026-09-01；6 个月；12 个月 | AAIF "Sandbox 阶段"（项目成熟度入门级）博文日期、检查点、12 个月内可申请进入 Growth 阶段（非"毕业窗口"） | AAIF | [aaif.io](https://aaif.io/blog/aaif-sandbox-phase) | 一手文档 | 2026-09-01 | 高 | 与执行沙箱无关 | 16, 23 |
| B23-17 | 2026-08-28 | ISO/IEC 22989:2022 Amd 2 进入 CD 征询 | ISO/IEC JTC 1/SC 42 | [ISO 标准页](https://www.iso.org/standard/93144.html) | 一手文档 | 2026-08-28 | 高 | 修订"预计处理 AI agent 定义"出自 arXiv 2604.04604（二手）；未见沙箱工作项 | 23 |
| B23-18 | 2026-09-14 | 北京金融科技产业联盟《智能体技术金融应用安全要求》报道日期 | 北京金融科技产业联盟 | [科技日报](https://www.stdaily.com/web/gdxw/2026-09/14/content_580749.html) | 二手报道 | 2026-09-14 | 中 | 日期据 URL（抓取摘要误写 2024）；报道未提沙箱 | 7, 23 |
| B23-19 | 2026-05-28 | OpenAI《Frontier Governance Framework》：PF 的配套合规文件（面向 TFAIA、EU GPAI 准则与 AI 法）；§3 Insider threats："Model execution is sandboxed, with restricted egress by default." | OpenAI | [公告页](https://openai.com/index/openai-frontier-governance-framework)；[PDF](https://cdn.openai.com/pdf/e37d949b-8c9f-4d76-b99e-4272f4631a7e/openai-frontier-governance-framework.pdf) | 一手文档 | 2026-05-28 | 高 | 不是 PF 新版本；未说明是否适用于训练与评测 | 19, 23, 27, 28 |

---

## 第六部分　案例研究

### 第 24 章　DeepSeek DSec

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B24-01 | 2026-09-19（v1，cs.DC） | 论文提交日期 | DSec | [arXiv abs 2609.22978][dsec-abs]；日期旁证：36 氪、Dataconomy | 一手文档（日期为二手旁证） | 2026-09-19 | 中 | 提交日期据 36 氪、Dataconomy（"submitted on September 19"；二手报道）；arXiv 摘要页未能读取，提交日期没有一手核实；cs.DC 分类未核实；媒体集中报道从 09-23 前后开始 | 24 |
| B24-02 | 约 160 个节点 | 单个生产规模单元 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 运营的规模单元总数未披露 | 1, 3, 24 |
| B24-03 | 每天约 300 万个沙箱 | 服务量 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 无按后端拆分 | 1, 2, 24, 附录 D |
| B24-04 | 超过 380,000 个并发沙箱 | 生产并发 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | HF 博文转述为"每集群数十万"；§2.4 作 'peak concurrency reaching ∼380K'，'over 380,000' 出自摘要 | 1, 24, 附录 D |
| B24-05 | 约 30K 核；约 250 TB DRAM | 单元规模 | DSec | [DSec][dsec]；[Dataconomy][dataconomy] | 论文自述 | 2026-09-19 | 高 | §2.4 原文："nearly 160 CPU nodes with 30K cores and ∼250 TB of DRAM"（已逐字确认） | 1, 13, 24 |
| B24-06 | 超过 5,000 次创建/秒 | 创建速率 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 论文未提 Kubernetes | 1, 9, 24, 28, 附录 D |
| B24-07 | DeepSeek V3.2 至 V4.1 | DSec 服务的模型范围（全部 RL 训练与评测沙箱） | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 原文见 §6 导言，不在 §1 | 24, 附录 D |
| B24-08 | 4 类后端（FnCall / 容器 / Firecracker microVM / QEMU 完整 VM） | 隔离档位 | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 生产中容器与 microVM 占主导，比例未披露 | 5, 6, 7, 24, 附录 D |
| B24-09 | 131 人（按 HTML 版作者块计数；首位 Jialiang Huang，末位 Wenfeng Liang） | 作者人数（按论文名单） | DSec | [DSec][dsec]；对照 [TechNode][technode]、[36kr][36kr] | 论文自述 | 2026-09-19 | 高 | TechNode "130-plus"、36 氪 "more than 130"、Dataconomy "Over 130" 与之一致；第一财经"100 多位"偏低（未抓取原文）；"80+ contributors" 无依据；两次独立读取得到同一份名单，尚未以 PDF 再核，C-03a | 1, 24 |
| B24-10 | 31 页 | 论文页数 | DSec | [DSec arXiv PDF](https://arxiv.org/pdf/2609.22978)（页脚最大页码 31）；[第一财经/163][163-dsec]；[Dataconomy][dataconomy]（"31-page arXiv paper"） | 论文自述 | 2026-09-23 | 中高 | PDF 页脚最大页码 31，参考文献从第 25 页开始，无附录（2026-10-06 网页读取，未取得本地 PDF）；与媒体一致，可写"论文 31 页" | 24 |
| B24-11 | 313 分、102 条评论 | Hacker News 讨论热度 | DSec | [Hacker News][hn-dsec] | 二手报道 | 约 2026-09-28/29 | 中 | 时点数字 | 24 |
| B24-12 | 17 次提交（author date 2026-07-22 至 09-07；commit date 2026-07-26 至 09-10），其中 15 次改动 storage/（overlaybd/LSMT），2 次为 CI 与 README | `huang-jl@deepseek.com` 对 AgentENV 的提交 | DSec 与 AgentENV 关系 | [AgentENV 仓库（本地克隆统计）][aenv] | 一手文档 | 2026-09-29 | 高 | 07-22 为作者日期，该提交（c6cad05）的提交日期为 07-31，由 Yingdi Shan 合入；按提交日期最早为 07-26（9fbcf19、a8fd060），晚于 07-25 发布，不能据此认定发布前参与；9fbcf19 曾在 README 加入"建立在我们 TrEnv-X 研究之上"的引用小节（07-27 删除）；GitHub 归属账号 huang-jl（署名 Jialiang Huang，自述 MADSys 博士生、TrEnv 作者；账号自述，2026-10-06）；X-33 | 24, 25 |
| B24-13 | PB 量级 | 平台管理的层与镜像总量（§2.4 "It manages petabytes of layers and images"） | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | 与一周活跃制品超过 130 TB（B03-07）口径不同，不可混用 | 1, 10, 24, 附录 D |
| B24-14 | 约 34.7 个/秒 | 日均创建速率（3,000,000 ÷ 86,400） | DSec | 由 B24-03、B24-06 推算 | 笔者推算 | 2026-09 | 中 | 与 > 5,000/s 峰值能力相差两个数量级以上 | 1, 9, 24, 28, 附录 D |
| B24-16 | "These controls address only part of the problem and do not provide a general defense against destructive behavior such as triggering kernel bugs." | §6.5 自认局限（非数字，登记为局限附注） | DSec | [DSec][dsec] | 论文自述 | 2026-09-19 | 高 | — | 19, 24 |
| B24-17 | 约 1.56 TB；约 188 核 | 生产规模单元每节点平均内存与核数（250 TB ÷ 160；30,000 ÷ 160） | DSec | 由 B24-02、B24-05 推算 | 笔者推算 | 2026-09 | 中 | 与评测所用 microVM 节点（2 路 × 96 核、1.5 TB DRAM，B10-09）量级一致；B13-20 以 1.56 TB 为基数 | 24 |
| B24-18 | 约 1.9 GB | 800 个 microVM 时每个的平均宿主内存（评测节点 1.5 TB ÷ 800） | DSec | 由 B10-09、B13-01 推算 | 笔者推算 | 2026-09 | 中 | 前提为评测节点配置；B13-20 的约 1.95 GB 以生产单元每节点平均约 1.56 TB 为基数，两种算法基数不同 | 24 |
| B24-19 | 约 819 个 | 8,192 个容器对照实验中平均每节点容器数（8,192 ÷ 10） | DSec | 由 B10-06 推算 | 笔者推算 | 2026-09 | 中 | 实验规模与条件均与生产不同 | 24 |

### 第 25 章　AgentENV 与清华 MADSys 谱系

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B25-01 | 2026-07-25 11:18（+0800） | 首次提交"Initial open-source release"（Sixing Lin） | AgentENV | [AgentENV 仓库][aenv] | 一手文档 | 2026-07-25 | 高 | 作者时间 11:18，提交时间 19:10（+0800）；huang-jl 一次提交的作者日期为 07-22，但 07-31 才合入，"回溯"仅指作者日期；媒体公开日期 07-27，C-19 | 25 |
| B25-02 | 225 次提交（截至 2026-09-29）；233 次（HEAD 00351e2，2026-10-01），无合并提交 | 仓库历史 | AgentENV | [AgentENV 仓库][aenv] | 一手文档 | 2026-09-29 | 高 | — | 25 |
| B25-03 | v0.1.0 07-25；v0.1.1 08-03；v0.1.2 08-10；v0.1.3 08-20；v0.2.0 09-03；v0.2.1 09-11；v0.2.2 09-18；v0.2.3 09-30 | 版本发布日期 | AgentENV | [AgentENV releases][aenv-rel] | 一手文档 | 2026 | 高 | — | 25 |
| B25-04 | Sixing Lin 49；Yingdi Shan 45；huajq（清华）27；Linzhi Zheng 21；huang-jl（DeepSeek）17；Tao Lin（RadixArk）7；guozy18（清华）5；Ruoqing He（Moonshot）3；其余约 30 人各 1–5 次 | 提交者构成 | AgentENV | [AgentENV 仓库（git shortlog）][aenv] | 一手文档 | 2026-09-29 | 高 | 邮箱域还包括 alibaba-inc.com（2 人）、xiaomi.com、transwarp.io 等；截至 HEAD 00351e2 Sixing Lin 50、Yingdi Shan 47；作者与提交者不同的 168 次提交中 143 次由 Yingdi Shan 合入；huang-jl 为 15 次 storage + 2 次 CI/README | 25 |
| B25-05 | 51,219,741 个沙箱；1,505,678 个镜像 | Kimi K3 训练与评测累计创建 | Kimi K3 / AgentENV | [Kimi K3 技术报告 §5.3.2][k3] | 论文自述 | 2026-07 | 高 | 常简写为 5,122 万 / 150 万；原文主语为"Kimi K3's training and evaluation"，未写明全部由 AgentENV 创建，同节首句称 K3 使用容器、GPU 沙箱与 AgentENV 三类运行时；README（c561be6 起）把"150 万个镜像"归于 AENV 生产；X-34 | 1, 25, 附录 D |
| B25-06 | 平均每个镜像约 34 个沙箱 | 51,219,741 ÷ 1,505,678 | AgentENV | 由 B25-05 推算 | 笔者推算 | 2026-07 | 中 | 平均值易被高复用镜像拉高 | 1, 3, 25, 附录 D |
| B25-07 | 2.8T 参数 MoE，激活 1,040 亿（104 billion） | Kimi K3 模型规模 | Kimi K3 | [Kimi K3 技术报告][k3] 摘要 | 论文自述 | 2026-07-27 | 高 | MarkTechPost"2.8-trillion-parameter"一致 | 25 |
| B25-08 | 至少 1 Gbps，强烈建议 10 Gbps 以上 | 建议网络带宽 | AgentENV | [MarkTechPost][mtp] | 二手报道 | 2026-07-27 | 中 | — | 25 |
| B25-09 | 约 18.6k 星（ktransformers）；约 5.9k 星（Mooncake） | kvcache-ai 组织旗下项目星标 | kvcache-ai | [kvcache-ai 组织页][kvcache-org] | 一手文档 | 2026-09 抓取 | 中 | 时点数字；AgentENV 本身星标未核实 | 25 |
| B25-10 | SOSP'24（TrEnv）；arXiv 2509.09525（TrEnv-X 期刊扩展） | 谱系起点论文 | TrEnv / TrEnv-X（Jialiang Huang、Sixing Lin、Yingdi Shan、Mingxing Zhang 等） | [TrEnv-X][trenvx] | 论文自述 | 2024 / 2026（TrEnv-X：ACM TOCS 44(3): 1–39，2026-07-27 在线、2026-08-31 印刷，Crossref 核实，DOI 10.1145/3805475） | 高（作者名单）/推断（谱系） | TrEnv → AgentENV → DSec 为推断，基于作者重合，须注明；TrEnv-X v2 作者 14 人，Jialiang Huang 标注"清华大学与阿里巴巴集团"；README 曾称 AgentENV"建立在我们 TrEnv-X 研究的部分思想与动机之上"（2026-07-26 加入，07-27 删除，B25-11）；整条谱系仍为推断 | 25 |
| B25-11 | 按提交日期 2026-07-26 23:30 进入仓库、2026-07-27 20:46 删除（均 +0800），约 21 小时；按作者日期约 20 小时 | README"Research Background and Citation"小节的存续（"AgentENV builds on and integrates some of the ideas and motivation behind our TrEnv-X research"） | AgentENV / TrEnv-X | [AgentENV 仓库][aenv] 提交 9fbcf19（huang-jl）、c748877（Linzhi Zheng） | 一手文档 | 2026-07-26/27 | 高 | 删除原因未说明；时长为笔者推算；谱系证据 E5 | 25 |
| B25-12 | 150 万个镜像（"1.5 million images in production"） | README 归于 AgentENV 的生产镜像数（链接 K3 报告） | AgentENV | [AgentENV README][aenv-readme]（c561be6 起） | 一手文档（厂商自报） | 2026-08-10 | 中 | K3 原文未写明全部由 AgentENV 创建（B25-05） | 25 |
| B25-13 | 2026-08-03 | 删除多节点控制面"prototype"标签（首版架构文档："The multi-node control plane in `services/` is a prototype"） | AgentENV | [AgentENV 仓库][aenv] 提交 b59881f | 一手文档 | 2026-08-03 | 高 | 设计无实质变化；MarkTechPost 07-27 据首版称"原型" | 9, 25 |
| B25-14 | 143 / 168 | 作者与提交者不同的提交中由 Yingdi Shan 合入的次数（截至 2026-09-29） | AgentENV | [AgentENV 仓库][aenv]（git log 作者/提交者比对） | 笔者推算 | 2026-10-03 | 高 | 另 14 次经 GitHub 网页合入 | 25 |
| B25-15 | 约 37 人 | 合并重复署名后的非机器人贡献者 | AgentENV | [AgentENV 仓库][aenv]（git shortlog，按姓名与邮箱合并） | 笔者推算 | 2026-10-03 | 中 | shortlog 原始 43 行，含 dependabot 与重复署名 | 25 |
| B25-16 | Linux 6.12.33（`virt-pvm/linux` 的 `pvm-612` 分支） | AgentENV 随附的 PVM guest 内核版本；宿主内核包另行发布于 kvcache-ai/linux | AgentENV | [AgentENV PVM 部署文档][aenv] `docs/src/deployment/pvm.md` | 一手文档 | 2026-10-01 | 高 | PVM"尚未合入主线 Linux 内核"，实验性 | 6, 25 |
| B25-17 | 约 13%；约 19% | 6.5×、9.6× 相对理想时间复用上界约 50×（B03-24）的比例 | AgentENV | 由 B13-08、B13-09、B03-24 推算 | 笔者推算 | 2026-10-03 | 低 | 仅作量级提示 | 13, 25 |
| B25-18 | `allow_internet_access` 默认 `true` | 开源版沙箱出站默认策略；`allowOut` 支持 IP/CIDR/域名，`denyOut` 仅 IP/CIDR；节点级 `always_denied_cidrs` 不可覆盖（B14-15） | AgentENV | [AgentENV 文档][aenv] `docs/src/concepts/sandboxes/networking.md` | 一手文档 | 2026-10-01 | 高 | K3 训练实际出站策略未披露 | 14, 25 |
| B25-19 | 博士生 33 人（含 Jialiang Huang、Sixing Lin、Linzhi Zheng、Jinqi Hua、Zhengyan Guo）；教师 6 人（含 Mingxing Zhang、Yingdi Shan） | MADSys 主页成员名单 | 清华 MADSys | [MADSys 主页][madsys] | 一手文档 | 2026-10-03 读取 | 高 | huajq↔Jinqi Hua、guozy22↔Zhengyan Guo 仅名字对应（推断）；Kang Chen 注 2026 年调往北大；谱系仍为推断，基于作者重合 | 24, 25 |
| B25-20 | "dozens to hundreds of steps"；"up to thousands of tool calls and millions of context tokens" | K3 专业工作流任务的步数；个人助理任务单个 rollout 的工具调用数与上下文 token 上界 | Kimi K3 | [Kimi K3 技术报告][k3] §4.2.3、§4.2.5 | 论文自述 | 2026-07 | 高 | 定性量级，无分布；"up to"为上界 | 附录 D |

### 第 26 章　国内厂商横览（披露矩阵）

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B26-01 | 超过 10,000 个并发沙箱实例（Kubernetes） | K2 沙箱基础设施 | Kimi K2 | [Kimi K2 报告][k2] | 论文自述 | 2025-07 | 高 | 原文"over 10,000 concurrent sandbox instances"；C-25；出处 K2 §3.2.1："It supports over 10,000 concurrent sandbox instances with stable performance" | 1, 17, 26, 27 |
| B26-02 | 最多 32,000 个环境并发；"数千个"代码沙箱并行；约 400 台物理机 | RL 框架并发与硬件 | 美团 LongCat | [arXiv 2601.16725][longcat] | 论文自述 | 2026-01 | 高 | 原文 "up to 32,000 environments running across roughly 400 physical machines"（§3.2），已复核 | 17, 26, 27 |
| B26-03 | "数万"吞吐；支持万亿参数训练 | AEnvironment / ASandbox | 蚂蚁 | [Ant Ling Medium][aenvironment] | 厂商自报 | 2025-12-17 | 低 | 单位不明；原文称沙箱引擎可选 ASandbox，并"支持扩展到 Kubernetes 等多种沙箱引擎"，未称 ASandbox 基于 K8s | 17, 26 |
| B26-04 | 预热 Firecracker 参考创建延迟 P50 97 ms（串行）、P99 308 ms（10 并发） | OpenSandbox Firecracker 后端 | 阿里 OpenSandbox | [GitHub OpenSandbox README][opensandbox] | 一手文档 | 2026-10-02 抓取 | 中 | 旧值"约 80 ms"已不见于现 README | 6, 26 |
| B26-05 | 约 15.6k 星、1.4k fork、3,230 次提交；2026-03 开源 | OpenSandbox 仓库 | 阿里 OpenSandbox | [GitHub][opensandbox]；[Cryptonomist][cryptonomist] | 一手文档 | 2026-03-03 / 抓取时 | 中 | 时点数字 | 26 |
| B26-06 | "毫秒级启动与数万实例并发" | AGS 文档口径（并发数） | 腾讯云 Agent Runtime | [腾讯云 AGS 文档][ags-doc] | 厂商自报 | 2026 | 中 | 与产品页"数十万实例/分钟"（创建速率）口径不同，C-08 | 26 |
| B26-07 | "100 毫秒"/"毫秒级"启动；"数十万实例/分钟" | Agent 沙箱产品页口径（创建速率） | 腾讯云 Agent Runtime | [腾讯云产品页][ags-product] | 厂商自报 | 性能数据采集于 2025-08（产品页注） | 中 | C-08；原页"数十万实例/分钟"后紧接"超大规模并发"，口径混用 | 22, 26 |
| B26-08 | v0.1.0 04-20；v0.3.0 06-02；v0.4.0 06-15；v0.5.0 07-03；v0.6.0 07-24；v0.7.0 08-28；v0.7.1 09-11；v0.7.2 09-24（tag 提交日期） | CubeSandbox 版本 | 腾讯 CubeSandbox | [CubeSandbox README_zh][cube-readme]；[GitHub][cube-gh] | 一手文档 | 2026-10-04 读取 | 高 | C-11 已消解：v0.5.0 与 v0.6.0 均存在，为相继版本；v0.7.2 为截至 2026-10-04 的最新正式版 | 6, 26 |
| B26-09 | 2026-04-20（README 新闻栏、v0.1.0 tag）/ 2026-04-21（腾讯云开发者社区）/ 2026-04-23（PR Newswire） | CubeSandbox 全栈开源日期 | 腾讯 CubeSandbox | [腾讯云开发者社区][cube-dev]；[PR Newswire][cube-pr] | 厂商自报 | 2026-04 | 中 | C-11 | 26 |
| B26-10 | 分钟级调度数十万沙箱实例（"实现分钟级调度数十万沙箱实例"） | MiniMax 用 Cube 做 Agentic RL | 腾讯 Cube / MiniMax | [腾讯云开发者社区][cube-dev] | 厂商自报 | 2026-04-21 | 中 | MiniMax 同时是阿里 ACS 的点名客户；原文为"数十万"，旧稿"数万个 RL 沙箱"有误（两次读取原文一致）；英文新闻稿（AAP，2026-04-23）写作"runs hundreds of thousands of heterogeneous sandboxes (Linux, Windows, Android) concurrently"，为并发口径，与中文"分钟级调度"不同，见 C-48 | 17, 26 |
| B26-11 | 最高每分钟 1.5 万个沙箱；预热池"百毫秒级"创建；内存态唤醒 1–10 秒 | ACS Agent Sandbox 文档口径 | 阿里云 ACS | [阿里云 ACS 文档][acs-doc] | 厂商自报 | 2026-06-22（文档修改日期；2026-10-02 读取时页面未显示日期） | 中 | C-06；1–10 s 未核实 | 9, 22, 26 |
| B26-12 | 每分钟 10 万个沙箱；冷启动 P99 < 180 ms（预置模板）；热启动 P99 < 20 ms；深度休眠唤醒 P99 < 600 ms | ACS 营销文口径 | 阿里云 ACS | [网易/阿里云 Agent Sandbox 文章][acs-163] | 厂商自报（营销） | 2026-09-28 | 中 | C-06；P99 < 600 ms 未核实 | 22, 26 |
| B26-13 | 最高每分钟 15,000 个沙箱；冷启动 20–40 ms；每 agent 一块加密 ESSD | MiniMax MaxClaw/MaxHermes 案例 | 阿里云 ACS / MiniMax | [网易/阿里云 MiniMax 案例][minimax-163] | 厂商自报（营销） | 2026-04-16 | 中 | C-06 | 21, 26 |
| B26-14 | 10 秒拉起 5,000 个沙箱；TCO 降 25% | MiniMax 在 ACS 上 | 阿里云 ACS / MiniMax | [网易/阿里云 Agent Sandbox 文章][acs-163] | 厂商自报（营销） | 2026-09-28 | 中 | — | 26 |
| B26-15 | "100,000+ simultaneous user requests"；"tens of thousands of sandboxes per minute during peaks"；启动时间缩短 50% 以上 | Kimi 的 Deep Research、Agentic PPT、OK Computer、Data Analytics 运行在 ACS Agent Sandbox（MicroVM）上；"每分钟数万"所在结果节同时写产品上线与"the critical model post-training phase"，未说明该数字属于哪一侧 | 阿里云 ACS / Kimi | [阿里云博客 Kimi 案例](https://www.alibabacloud.com/blog/deep-dive-how-kimis-ai-agent-runs-on-alibaba-cloud_602942)（2026-03-12）；[钛媒体](https://www.tmtpost.com/7920695.html)（2026-03-19）；[网易/阿里云][acs-163]（2026-09-28） | 厂商自报（营销） | 2026-03-12 / 2026-09-28 | 中 | 数字未按产品与训练拆分，两种语境并列呈现，不归为任何一侧；原"更像 RL rollout 量级（推断）"撤销（原文无训练侧单独数字），亦不写作"产品侧"或"纯产品侧"；博客另称"Beyond user-facing services, Kimi used large-scale RL and Agentic data synthesis to train its new K2 model"，并以 Kimi 为例介绍 MCTS 实例克隆；数字由阿里云而非月之暗面披露；钛媒体"AMD EPYC"一句完整原文未逐字核实；建议措辞："阿里云博客称 Kimi 的 Deep Research、OK Computer 等产品运行在 ACS MicroVM 上，并在介绍产品上线与模型后训练阶段的同一节写到峰值每分钟数万个沙箱，未说明该数字属于哪一侧（厂商自报）"；同源见 B21-19（2026-10-05 回原文核对后统一） | 1, 21, 22, 26 |
| B26-16 | 295B-A21B | 混元 Hy3 规模（README 无沙箱信息） | 腾讯混元 | [GitHub Hy3][hy3] | 一手文档 | 2026-07-06 | 高 | — | 26 |
| B26-17 | "tens of thousands of simultaneous environments" | ROCK 同时运行的环境数 | 阿里 ROCK | [ROME arXiv 2512.24873v3 §2.3](https://arxiv.org/html/2512.24873) | 论文自述 | 2026-03-12（v3） | 中 | 模糊量词，勿换算；同节称每沙箱独立网络策略，Rocklet 代理执行出站策略；隔离底座未披露 | 14, 26 |
| B26-18 | 三类越界行为（反向 SSH 隧道、GPU 挖矿、内网探测）；四级轨迹过滤 | 训练期自发越界事件（非数字，登记为事件附注）；§3.1.3.3 过滤阶段数 | 阿里 ROME | [ROME §3.1.4、§3.1.3.3](https://arxiv.org/html/2512.24873) | 论文自述 | 2026-03-12（v3） | 高 | 原文："established and used a reverse SSH tunnel from an Alibaba Cloud instance to an external IP address"；"unauthorized repurposing of provisioned GPU capacity for cryptocurrency mining"；由防火墙告警发现；涉事模型、频率、是否外泄均未披露；是否见于 v1 未核实 | 2, 14, 19, 26 |
| B26-19 | 最多 10,000 个并发 rollout；超过 100 台真机、超过 150 个应用；约 20 倍 | 统一环境设施并发；真机规模；虚拟显示带来的 rollout 总吞吐提升 | 阿里 Qwen-UI-Agent | [arXiv 2607.28227 §2.2.2、§2.4.3](https://arxiv.org/html/2607.28227) | 论文自述 | 2026-07 | 高 | Android 沙箱基于 redroid（容器，共享宿主内核，无 QEMU/嵌套 KVM）；桌面为 OSWorld Ubuntu VM | 7, 26 |
| B26-20 | 1,978 个环境；19,822 个工具；20 / 50 / 2K+ 级分类；测试准确率门槛 0.5 | 合成环境存量与工具保留条件 | 人大 + 字节 Seed Agent-World | [arXiv 2604.18292v1](https://arxiv.org/html/2604.18292v1) | 论文自述 | 2026-04-20 | 高 | 存量，非并发；工具在 Python 沙箱执行；无容器、并发、隔离细节；v1 提交日期 2026-04-20（arXiv Submission history；早先误记为 2026-07-29） | 18, 26 |
| B26-21 | 36 种编程语言；超过 1000 个并发执行 | 多语言代码沙箱（分布式 CPU 集群；文件与网络隔离） | 腾讯 Hunyuan-A13B | [arXiv 2609.27284 §3.1.2](https://arxiv.org/html/2609.27284) | 论文自述 | GitHub 版 2025-06；arXiv 提交日期未核实；HF Papers 页显示"Published September 23"（年份显示异常），推测 2026-09-23，未核实 | 中 | 单位为"executions"，非沙箱数；arXiv 编号与 GitHub 版时间不一致，abs 页无可读文本；另 §3.2.2："Paired GRMs based on relative preference judgments mitigate reward hacking"（创作任务，奖励侧） | 26 |
| B26-22 | 超过 10,000 个并发 pod；环境搭建成功率 70%（8 种语言） | 代码 Agent 环境设施 | 小米 MiMo-V2-Flash | [arXiv 2601.02780 PDF §4.3.2](https://arxiv.org/pdf/2601.02780) | 论文自述 | 2026-01 | 高 | 早先读取时 HTML 版未见，PDF 有；运行时未披露；附录 B 记录 git log --all 利用残留真值提交：按关键词计数量化，图 8 给出尝试次数随训练步变化（无比率）；评测改用最新 SWE-Bench 镜像，自建训练镜像遵循官方修复并"反复确认"无 reward hacking | 18, 19, 26 |
| B26-23 | verl v0.6.1；Qwen3-4B-Instruct-2507 | TI-ONE × AGS 最佳实践的框架版本与训练对象（`e2b_code_tool`） | 腾讯云 TI-ONE / AGS | [腾讯云文档](https://cloud.tencent.cn/document/product/851/128646) | 一手文档 | 2026-02-27 | 高 | 全文未提混元；不能据此推断混元训练使用 AGS | 16, 26 |
| B26-24 | 4 类沙箱；5 种语言 | 百度智能体沙箱 AX（代码、浏览器、桌面、自定义；Python、JS/TS、R、Java、Bash） | 百度智能云 | [AX 文档](https://cloud.baidu.com/doc/AX/s/amoi8d7oo) | 一手文档 | 2026-08-14 | 高 | 原文"把代码关进容器或虚拟机"；SDK 为 `e2b_code_interpreter`；无 RL 训练内容；文档未公开价格 | 16, 26 |
| B26-25 | 提效 10%；130 万个 agent | 星火 X2 多阶段 RL 采样（P/D 分离）；星辰 Agent 平台 agent 数 | 讯飞 | [IT之家](https://www.ithome.com/0/921/060.htm) | 二手报道 | 2026-02-11 | 低 | 无沙箱信息 | 26 |
| B26-26 | 约 80 个/台 | LongCat 平均每台物理机并发环境（32,000 ÷ 400） | 美团 LongCat | 由 B26-02 推算 | 笔者推算 | 2026-10-05 | 中 | 实际分布未披露 | 26 |
| B26-28 | 约 2,500 个实例；1,550 个仓库；训练 200 轮、评估 500 轮上限；约 0.2% 轨迹有作弊模式 | Ling & Ring 2.6 SWE 类 Agentic RL（在 sandbox 环境 AEnvironment 中训练） | 蚂蚁 inclusionAI | [智源社区转载官方解读](https://hub.baai.ac.cn/view/55798) | 二手报道 | 2026-06-24 | 中 | 官方解读转载（智源社区，转自 Hugging Face 中文社区）；报告正文仍未读（arXiv 429）；未给沙箱并发或容量；B26-27 号此前已并入 B21-27，故跳号 | 26 |

### 第 27 章　海外实验室与开源生态（披露矩阵）

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B27-01 | "数百个" UI-gym 网站克隆 | OpenAI 为 ChatGPT Agent 训练采购 | OpenAI | [SemiAnalysis][semianalysis] | 二手报道 | 2026-01-06 | 中 | — | 18, 22, 27 |
| B27-02 | "十几家" RL 环境公司 | Anthropic 合作的环境供应商数；多数领域要求遵循特定沙箱框架 | Anthropic | [SemiAnalysis][semianalysis] | 二手报道 | 2026-01-06 | 中 | 框架为 laude-institute/sandboxes（Harbor 前身） | 22, 27 |
| B27-03 | "数百个并发沙箱" | Mistral 在 CoreWeave Sandboxes 上 | Mistral | [CoreWeave Sandboxes 发布稿](https://coreweave.com/news/coreweave-sandboxes-launches-to-accelerate-reinforcement-learning-agent-tool-use-and-model-evaluation) | 一手文档（客户原话） | 2026-05-14 | 中 | Mistral AI scientist Roman Soletskyi："We now run hundreds of concurrent sandboxes on CPU nodes and alongside Slurm training jobs on GPU nodes, all through a single setup."；原经 [Modal RL 页面][modal-rl] 转述；见 B22-63 | 22, 27 |
| B27-04 | "每个训练步并行数千个沙箱" | IBM Research 在 CoreWeave Sandboxes 上 | IBM Research | [CoreWeave Sandboxes 发布稿](https://coreweave.com/news/coreweave-sandboxes-launches-to-accelerate-reinforcement-learning-agent-tool-use-and-model-evaluation) | 一手文档（客户原话） | 2026-05-14 | 中 | IBM Research Brian Belgodere："spin up thousands of sandboxes in parallel per training step, each with its own container image and resource boundaries"；原经 [Modal RL 页面][modal-rl] 转述；见 B22-63 | 22, 27 |
| B27-05 | 约 100 compute-hours | 评估一个新解的预算上限 | AlphaEvolve | [arXiv 2506.13131][alphaevolve] | 论文自述 | 2025-06 | 高 | — | 27 |
| B27-06 | 6 种 Seatbelt profile（默认 permissive-open） | Gemini CLI macOS 沙箱配置 | Gemini CLI | [gemini-cli sandbox 文档][geminicli] | 一手文档 | 2026 | 高 | 默认不开沙箱 | 4, 27 |
| B27-07 | 32B | CWM 参数量 | Meta CWM | [arXiv 2510.02387][cwm] | 论文自述 | 2025-09/10 | 高 | — | 27 |
| B27-08 | 2026-07-13；44 分钟 | Bhardwaj 演讲 "From fork() to Fleet" 视频上线日期与时长 | OpenAI（演讲） | [Podwise](https://podwise.ai/episodes/8400288) | 二手报道 | 2026-07-13 | 中 | 讲者身份以 ai.engineer 讲座页为准（一手，2026-10-05 复核；时长 44:34）；演讲无任何规模数字（两份转录一致） | 27 |
| B27-09 | 41 个；22 个；311 个；不到 13 小时 | 被执行代码的 HF 生产数据集服务 worker；处置中删除的模型创建管理员账户；禁用的 Artifactory 仓库；从单个 worker pod 到跨多个 HF 集群管理与宿主级访问的用时 | OpenAI（ExploitGym） | [OpenAI 事故技术报告 PDF](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf) | 一手文档 | 2026（PDF 未标日期） | 高 | 复盘正文写"数十台"，与 41 一致；另含至少一个生产节点 root | 15, 19, 27 |
| B27-10 | "per-run container environments for model training and evaluation workloads"；整改为"isolated, virtual-machine-based sandboxes"+"two separate layers of network isolation"；Artifactory 从 Research CaaS 完全移除 | OpenAI Research CaaS 隔离方式及事故后整改 | OpenAI | 同 B27-09 | 一手文档 | 2026 | 高 | 08-26 复盘整改部分只写"more isolated sandboxes"；但其 07-19 时间线条目称 Agent 取得"a research cluster that supported our virtual machine environments"的完整管理员权限，即事故前已有 VM 研究环境（用途未说明，见 B27-29），"事故前为容器"只适用于 Research CaaS；"By design, many Research CaaS workloads used the same shared Artifactory credential"已复核 | 15, 19, 27 |
| B27-11 | 约一个月；超过 10% | 2026-04 冻结生产 RL 环境全部变更的时长；冻结期被标记有问题的生产环境比例（"from reward hacking to broken tasks and misconfiguration"） | Anthropic | [Anthropic：Improving our alignment and security efforts](https://www.anthropic.com/news/improving-alignment-security-efforts) | 一手文档 | 2026-08-31 | 高 | 原文："In April we froze all changes to our production RL environments for roughly a month"；"flagged over 10% of environments in our production mix"；分母（环境池规模）未披露 | 1, 18, 19, 27 |
| B27-12 | 三天 | 2026-02 因 reward hacking 迹象回滚的 Mythos Preview RL 训练 | Anthropic | 同 B27-11 | 一手文档 | 2026-08-31 | 高 | — | 19, 27 |
| B27-13 | 约 150 名 | 转去做安全、可靠性与隐私的产品工程师 | Anthropic | 同 B27-11 | 一手文档 | 2026-08-31 | 高 | 同文：高风险内部 cyber 沙箱迁至"more robust isolation"（技术未说明）；实时越界分类器；评测伙伴默认"hardened sandbox with no internet access"；2026-08-04 UK AISI 报告 Mythos 5 未授权行动 | 27 |
| B27-14 | 约 0.01%；约 0.2% | Mythos Preview 训练中绕过网络限制的成功尝试占 episode 比例；训练 episode 中越权（含从受限 GUI computer-use 界面拿到 shell）比例 | Anthropic | [Mythos Preview 系统卡](https://www-cdn.anthropic.com/08ab9158070959f88f296514c21b7facce6f52bc.pdf)（经 [LessWrong](https://www.lesswrong.com/posts/QKDoZe6EKhxnFjLWK/is-mythos-good-at-cyber-because-it-kept-hacking-anthropic-s)，Tim Hua，2026-07-27） | 二手引述 | 2026-04-07 | 中 | PDF 抓取截断，未能回原文核对；LessWrong 作者据此推算的"约 1 万次突破、10 万次越权"为第三方推算，不应引用（X-43）；转引者为 Tim Hua（LessWrong，2026-07-27），引文为"successful attempts appearing in about 0.01% of episodes""The recursive-summarization tool flagged this access escalation in about 0.2% of training episodes."；PDF 文本提取止于 §4.1.4.1，未见这两个数字，仍为二手引述 | 2, 19, 27 |
| B27-15 | 7.8% | Opus 4.7 训练中受导致意外 CoT 监督的技术错误影响的 episode 比例 | Anthropic | [Opus 4.7 系统卡 §2.4.1](https://www-cdn.anthropic.com/037f06850df7fbe871e206dad004c3db5fd50340/Claude%20Opus%204.7%20System%20Card.pdf) | 一手文档 | 2026 | 高 | 原文："The technical error that caused accidental chain-of-thought supervision in some prior models (including Mythos Preview) was also present during the training of Claude Opus 4.7, affecting 7.8% of episodes."；原文未逐一列出 Opus 4.5、4.6（Zvi 的列举为其转述，X-52） | 19, 27 |
| B27-16 | 11 家 | Claude Managed Agents 自托管沙箱平台指南（AWS Lambda MicroVMs、Blaxel、Cloudflare、Daytona、E2B、Fly.io、GKE Agent Sandbox、Modal、Namespace、Superserve、Vercel） | Anthropic | [Self-hosted sandboxes 文档](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes) | 一手文档 | 2026-10-05 读取 | 高 | worker 只需出站 HTTPS | 16, 21, 27 |
| B27-17 | 7 天 | Gemini Enterprise Managed Agents 沙箱标准 TTL；网络默认关闭 | Google Cloud | [Gemini Enterprise 文档](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/managed-agents/sandbox-environment) | 一手文档 | 2026-10-05 读取 | 高 | — | 21, 27 |
| B27-18 | 4 vCPU / 16 GB | Gemini API Managed Agents 每次交互容器规格 | Google（经员工博客） | [Philipp Schmid](https://www.philschmid.de/how-managed-agents-work) | 二手报道 | 2026-06-10 | 低 | 作者为 Google DeepMind 开发者关系人员；未回官方文档核对 | 27 |
| B27-19 | 约 3,000 名 | Meta MSL 全职构建 RL 环境的工程师 | Meta（经 SemiAnalysis） | [AI Weekly 转述](https://aiweekly.co/alerts/meta-msl-builds-five-titan-clusters-muse-spark-ties-opus-46) | 二手报道 | 2026-07-10 | 低 | 未回 SemiAnalysis 原文 | 27 |
| B27-20 | 21 个；"hundreds of concurrent agent-codebase interactions" | Nemotron 3 Super RLVR 环境数；SWE-RL 并发需求 | NVIDIA | [arXiv 2604.12374](https://arxiv.org/pdf/2604.12374) | 论文自述 | arXiv v1 2026-04-14（预印本） | 高 | 每个 rollout 一个 Apptainer 容器 + OpenHands；Ray + SLURM | 17, 27 |
| B27-21 | 0.37 个实例/秒 | ProRL Agent SWE 任务吞吐 | NVIDIA | [arXiv 2603.18815](https://arxiv.org/html/2603.18815) | 论文自述 | 2026-03-19（预印本） | 高 | Singularity 无守护进程、非特权；每实例独立 127.x 回环 IP；QEMU VM 仅为构建器可扩展到 GUI 任务的举例；已集成 NeMo Gym | 17, 27 |
| B27-22 | v0.0.8 alpha；2026-03-17 | OpenShell 首发版本与日期（GTC 2026，Apache-2.0） | NVIDIA | [brenner-axiom](https://brenner-axiom.codeberg.page/research/nvidia-openshell-2026-03-17) | 二手报道 | 2026-03-17 | 中 | Canonical 2026-06-01 公告（一手）称"runs each agent in its individual, isolated sandbox"；已回 brenner-axiom 原页确认 v0.0.8、03-17、Apache-2.0、K3s in single Docker container、Landlock、alpha（二手） | 27 |
| B27-23 | 每集群数十万个 pod；每秒超过 500 个 pod；4 个解耦服务 | Cursor Anyrun 规模、单集群调度速率、RL 基础设施服务数 | Cursor | [Composer 2 技术报告 arXiv 2603.24477](https://arxiv.org/pdf/2603.24477) | 论文自述 | arXiv v1 2026-03-25（预印本） | 高 | 每个 pod 为专用 Firecracker VM，含浏览器与 GUI；文件系统 + 内存级 fork/快照 | 6, 9, 11, 17, 27 |
| B27-24 | 约 10 倍 | DSec 创建速率（> 5,000/s）与 Anyrun 单集群调度速率（> 500 pod/s）之比 | — | 5,000 ÷ 500 | 笔者推算 | — | — | 单位与口径不同，仅作量级参考 | 27 |
| B27-25 | "tens of thousands of concurrent machines" | otterlink 支撑的 Devin 并发机器 | Cognition | [Cognition SWE-1.5](https://cognition.com/blog/swe-1-5) | 一手文档 | 2025-10-29 | 高 | 产品规模，训练用量未披露；句子位于博文"Training & Infrastructure"一节，训练与 Devin 共用为推断；三种评分机制；reward hardening | 21, 22, 27 |
| B27-26 | 超过 4,000 个；10 秒以内；256 个/节点；超过 20,000 个镜像；512 × H200；`max_off_policy_steps` = 8 | INTELLECT-3 沙箱与训练配置 | Prime Intellect | [arXiv 2512.16144v1](https://arxiv.org/html/2512.16144v1) | 论文自述 | 2025-12-18 | 高 | gVisor（runsc）；Rust 网关绕开 K8s 控制面；2026-09 商用版改为 microVM（B16-14）；`max_off_policy_steps` 用于丢弃过度 off-policy 的 rollout，不是 reward hacking 缓解 | 5, 13, 17, 27 |
| B27-27 | "100 agents in parallel" | SWE-ReX 并行能力 | SWE-agent | [SWE-ReX](https://github.com/SWE-agent/SWE-ReX) | 一手文档 | — | 中 | 已回原文复核原句 | 27 |
| B27-28 | 26 个 | Terminal-Bench 2.1 相对 2.0 修订的任务数（仓库 README："26 tasks were modified to fix bugs, modify timeouts or resources, or improve robustness to reward hacking"） | Terminal-Bench | [terminal-bench-2-1 仓库](https://github.com/harbor-framework/terminal-bench-2-1) | 一手文档 | 2026-10-05 读取 | 高 | 与 tbench.ai 2.1 页"28 of the 89"冲突，见 C-49 | 20, 27 |
| B27-29 | "a research cluster that supported our virtual machine environments" | 事故前 OpenAI 已有 VM 研究环境（07-13 至 07-19 Agent 取得其研究集群完整管理员权限） | OpenAI | [OpenAI 复盘][openai-hf] | 一手文档 | 2026-08-26 | 高 | 用途与规模未披露；限定"Research CaaS 事故前为容器"的适用范围 | 15, 19, 20, 27 |

---

## 第七部分　前沿

### 第 28 章　开放工程问题与研究议程

本章原则上引用前文编号，不新增数字。常用于论证开放问题的数字：B03-10（98% 等待）、B09-04（k 未披露）、B11-01/B11-02（暂停延迟口径不一）、B10-14（env.reset 失败率）、B18-02（沙箱错误率）、B19-13（DSec 无比率）、B19-02（隔离级别改变排行）、B20-02（强原语未评测）、B16-06（自动策略 80.9%）、B02-05（CaMeL 效用代价）。第 28 章实际引用另见 B03-09、B10-15、B12-01、B12-02、B12-09、B12-10、B12-12、B12-15、B13-04、B13-10、B15-07、B17-01、B17-10、B18-01、B19-01、B19-06、B19-12、B20-04、B20-22、B23-09、B23-13、B23-15、B23-19、B24-06、B24-14、C-02、C-49（表 28-5）；新增 B28-03。

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| B28-01 | 0 项 | 在同一模型、同一任务上对比离线/白名单/全开放三种网络模式的受控研究数 | 文献空白 | 本书文献检索结论（出站、供应链、reward hacking 三个主题） | 笔者推算（文献检索结论） | 2026-09-30 | 中 | Cursor 的对比同时改了两个变量 | 14, 15, 19, 28 |
| B28-02 | 0 项 | 测量不同隔离档位下 reward hacking 率的研究数 | 文献空白 | 本书文献检索结论 | 笔者推算（文献检索结论） | 2026-09-30 | 中 | — | 5, 8, 19, 24, 27, 28 |
| B28-03 | 研究论文 7 篇；愿景论文 5 篇 | 第一届 AgenticOS 研讨会（ASPLOS 2026）录用论文数 | AgenticOS @ ASPLOS 2026 | [AgenticOS'26 页面](https://os-for-agent.github.io/asplos-2026.html) | 一手文档 | 2026-03-23（2026-10-05 读取） | 高 | 按页面 Research Papers / Vision Papers 两节所列题名计数（Execute-Only Agents 与 Grimlock 均在愿景论文下），与文献库 C28-08 一致；前次抓取所称小标题"6 papers / 4 papers"无法复现，不采用 | 3, 8, 11, 28 |
| B28-04 | 约 50 µs；8 MB 对 4.4 GB | AgileLog（Bolt）fork 延迟（与日志长度无关）；1,000 个 cFork、100 万条记录时元数据内存（朴素实现 4.4 GB） | AgileLog（UIUC） | [arXiv 2604.14590v1 PDF](https://arxiv.org/pdf/2604.14590) §6.1、§6.5 | 论文自述 | 2026-04-16（v1） | 中 | 摘录式读取；SOSP'26 终稿未取得；另有 Kafka 干扰下延迟高 2.5×（§6.2）、嵌套深度 7 查找慢 5.2%（§6.6）、即席分析场景平均/p99 延迟 14×/130×（§6.8）；日期写法见 C-55 | 28 |

---

## 附录专用数字

### 附录 C　各系统 API 对照

附录 C 使用、正文各章未另行登记的接口默认值与上限（2026-10-05 登记，编号前缀 BC）。附录 D 引用的数字均已在上文各章分区登记，其中只在附录 D 使用的 K3 步数见 B25-20。

| 编号 | 数字（原样，含单位） | 含义/口径 | 系统或主体 | 来源（标题+链接） | 来源类型 | 日期 | 可信度 | 冲突或备注 | 使用章节 |
|---|---|---|---|---|---|---|---|---|---|
| BC-01 | `autoPause` 默认 true | AgentENV 到期动作默认暂停（E2B 规范 `autoPause` 默认 false） | AgentENV | [AgentENV `src/api/openapi.yml`；`docs/src/concepts/sandboxes/auto-eviction.md`](https://github.com/kvcache-ai/AgentENV) | 一手文档 | HEAD 5843159（2026-10-03） | 高 | 与 B16-09 并读：同名字段默认值不同 | 16, 附录 C |
| BC-02 | `timeout` 为空闲秒数；`on_timeout` 默认 kill；`NEVER_TIMEOUT` = -1 | CubeSandbox 超时语义（E2B 为存活时间） | 腾讯 CubeSandbox | [CubeSandbox `docs/guide/lifecycle.md`](https://github.com/TencentCloud/CubeSandbox) | 一手文档 | HEAD e02976a（2026-09-30） | 高 | — | 附录 C |
| BC-03 | 默认 5 分钟；最长 24 小时；文件系统快照默认保留 30 天（可设 `ttl`，`None` 为不过期）；内存快照保留 7 天（Alpha，不可延长） | Modal 沙箱 timeout 与快照保留期 | Modal | [Sandboxes](https://modal.com/docs/guide/sandbox)；[Sandbox snapshots](https://modal.com/docs/guide/sandbox-snapshots) | 一手文档 | 2026-10-05 读取 | 高 | — | 附录 C |
| BC-04 | `auto_stop` 默认 15 分钟；`auto_pause` 60 分钟（VM）；`auto_archive` 7 天（容器）；CIDR ≤ 10 条；域名 ≤ 100 条；exec 默认超时 10 s | Daytona 生命周期默认值与网络白名单上限 | Daytona | [Sandboxes](https://www.daytona.io/docs/en/sandboxes.md)；[Network limits](https://www.daytona.io/docs/en/network-limits.md)；[Process](https://www.daytona.io/docs/en/process-code-execution.md) | 一手文档 | 2026-10-05 读取 | 高 | 网络默认值随 Tier 不同 | 附录 C |
| BC-05 | `timeout_minutes` 默认 60；批量查询上限 100 | Prime Sandboxes 超时默认值与批量接口上限 | Prime Intellect | [prime-sandboxes `sandbox.py` / `models.py`](https://github.com/PrimeIntellect-ai/prime) | 一手文档 | HEAD 32098eb（2026-10-04） | 高 | SDK 已有文件系统检查点，见 B16-14 备注 | 16, 附录 C |
| BC-06 | 300 秒–24 小时；默认每账号每地域 20 个暂停实例 | AGS 沙箱工具超时范围；暂停实例占配额 | 腾讯云 AGS | [创建沙箱工具](https://cloud.tencent.com/document/product/1814/132210)；[暂停与恢复](https://cloud.tencent.com/document/product/1814/132323) | 一手文档 | 2026-10-05 读取 | 中 | 网页抓取摘录，非逐字 | 附录 C |
| BC-07 | ≥ 60 s | OpenSandbox 创建请求 `timeout` 下限（上限由 `server.max_sandbox_timeout_seconds` 配置；null 不过期） | OpenSandbox | [`specs/sandbox-lifecycle.yml`](https://github.com/opensandbox-group/OpenSandbox) | 一手文档 | HEAD c7dc78a（2026-10-01） | 高 | — | 16, 附录 C |

---

## 冲突数字登记

> 每条冲突给出各方数字、来源与日期、判断和建议写法。编号 C-xx 与上文"冲突或备注"列对应。

| 编号 | 主题 | 一方（数字 / 来源 / 日期） | 另一方（数字 / 来源 / 日期） | 判断 | 建议引用措辞 |
|---|---|---|---|---|---|
| C-01 | AgentENV 内存超售比 | **6.5×**："memory overcommit ratio of up to 6.5× in real workloads"，[Kimi K3 技术报告][k3]，2026-07 | **9.6×**："9.6x memory overcommit ratio in production"，[AgentENV README][aenv-readme] 提交 c561be6（2026-08-10）；bex.co 2026-09-22 沿用 | 可能对应不同时间点或统计口径；不是二选一；两份来源归因的机制也不同（K3：写时复制内存与页缓存优化；README：内存气球） | "K3 技术报告称借助写时复制内存与页缓存优化，真实负载下内存超售比最高 6.5 倍；项目 README（2026-08-10）称借助内存气球，生产中达 9.6 倍。两个数字均为自报，口径未说明，归因机制也不同。" |
| C-02 | AgentENV fork 上限 | **16** 个子沙箱：首次提交 `8f028b1`（2026-07-25）的 `docs/src/concepts/sandboxes.md` 写"up to 16 child sandboxes"；MarkTechPost（07-27）、bex.co（09-22）沿用 | **1–100**：同一提交的 `src/api/openapi.yml` 中 fork `count` 为 `minimum: 1`、`maximum: 100`，`src/api/generated/src/models.rs` 中为 `#[validate(range(min = 1u32, max = 100u32))]`；`f57e9c6`（作者日期 2026-08-24，提交日期 08-26）把文档更正为 1–100 | **文档与代码不一致（已解决）**：上限本身从未改变，变化的是文档口径；"上限提高"的叙事不成立（见 X-31） | "AgentENV 的 fork 数量上限自首版起即为 100（API 与代码校验为 1–100），首版文档误写为 16，2026-08-24 更正；fork 仅限同节点。" |
| C-03 | AgentENV 暂停/恢复延迟 | README：启动/恢复 < 50 ms，暂停 < 100 ms，增量快照 < 100 ms（自报） | K3 报告：检查点最低 133 ms、恢复最低 49 ms（K3 技术报告给出的"最低可达"值） | 口径不同（README 为宣称上界，K3 为"最低可达"下界，均未说明测量条件），不宜互相替代 | 分别标注来源；正文优先用 K3 技术报告给出的"最低可达"值 |
| C-03a | DSec 作者人数 | **131 人**：论文作者块（HTML 版计数），2026-09-19 | **100 多位**：第一财经（163）2026-09-23（TechNode "130-plus"、36 氪 "more than 130"、Dataconomy "Over 130" 与原文一致；"80+ contributors" 无依据） | 英文媒体与原文一致，不再算冲突；第一财经为偏低的约数 | "论文署名作者 131 人" |
| C-04 | Manus 沙箱保留期 | **14 天**：付费用户沙箱数据最多保留，[E2B 客户案例][e2b-manus]，2025-05-06 | **Free 7 天 / Pro 21 天**：闲置回收，[Manus 官方博客][manus-blog]，2026-01-14 | 相隔 8 个月，更可能是政策调整 | "据 E2B 2025 年 5 月的客户案例，付费用户沙箱保留 14 天；Manus 2026 年 1 月的官方博客则写明 Free 7 天、Pro 21 天闲置后回收。"两者口径也不同：一为"数据保留"，一为"闲置后回收"。 |
| C-05 | Manus 是否使用 E2B | 使用 E2B Firecracker，可自托管：E2B 客户案例（2025-05，附张涛引语）；SiliconANGLE 2025-07-28 列为客户 | Manus 官方博客（2026-01）**未提 E2B**；2026 年后供应商未确认 | 2025 年成立；2026 年后未知；Manus 2026 年的三篇博客（sandbox 01-14、Cloud Computer 04-30、My Computer 03-16）均未提供应商；2026-08-12 恢复独立运营后仍无披露 | "2025 年 Manus 使用 E2B 的 Firecracker microVM（E2B 案例，附联合创始人引语）；2026 年后的供应商未见一手确认。" |
| C-06 | 阿里云 ACS Agent Sandbox 指标 | 文档（修改日期 2026-06-22）：**最高每分钟 1.5 万**；预热池"百毫秒级"创建；内存态唤醒 **1–10 秒** | MiniMax 案例（2026-04-16）：**每分钟 15,000**，冷启动 **20–40 ms**；营销文（2026-09-28）：**每分钟 10 万**，冷启动 **P99 < 180 ms**，热启动 **P99 < 20 ms**，深度休眠唤醒 **P99 < 600 ms** | 指标随时间变化；冷启动三种口径（百毫秒级创建 / 20–40 ms / P99 < 180 ms）统计量不同；"唤醒 1–10 s"（内存态）与"深度休眠 P99 < 600 ms"口径不同 | 按日期并列：“阿里云文档（2026-06）称最高每分钟 1.5 万个；2026-09 的营销文章称每分钟 10 万个、冷启动 P99 低于 180 ms（均为厂商自报）。” 唤醒延迟须注明"内存态"或"深度休眠" |
| C-07 | 阿里 ACS 价格单位 | 文档标价 vCPU **¥0.078/小时**（¥0.0000217/秒）、内存 **¥0.039/GiB·小时**（¥0.00001083/GiB·秒），[ACS 文档][acs-doc]，2026-06-22 | 腾讯 AGS **约 ¥0.29/核/小时**、¥0.09/GiB/小时（2026-09-09）；E2B 约 $0.05/vCPU-h | **已解决**（2026-10-05，第 21、22 章回 ACS 文档）：秒价与小时价同列，秒价 × 3,600 = 小时价，单位无误；与腾讯的差距是真实标价差异；X-08 已删除 | 可引用："阿里云 ACS Agent Sandbox 中国内地标价为每 vCPU 每小时 0.078 元、每 GiB 内存每小时 0.039 元（文档 2026-06-22）"；约为腾讯 AGS 同规格的三分之一、E2B 的四分之一（笔者推算，B22-56） |
| C-08 | 腾讯 AGS 规模口径 | **"数万实例并发"**（并发数）："毫秒级启动与数万实例并发"，[AGS 文档][ags-doc] | **"数十万实例/分钟"**（创建速率）；启动"100 毫秒"/"毫秒级"，[产品页][ags-product]（未标日期） | 两者单位不同：并发数 vs 创建速率；启动延迟"100 毫秒"与"毫秒级"措辞不一 | 引用时保留单位："腾讯云文档称支持数万实例并发，产品页称每分钟可创建数十万实例（厂商自报）" |
| C-09 | Kimi K2.5 的 "100,000" | K2.5 报告："Rollout Manager orchestrates up to **100,000 concurrent agent tasks**"，每任务从托管池取一个带沙箱的环境实例，[arXiv 2602.02276][k25] | 若写作"10 万并发沙箱"即属误读；K2 报告另有"over **10,000** concurrent sandbox instances"（Kubernetes），[arXiv 2507.20534][k2] | 10 万是协程/任务数，不等于并发沙箱数 | "K2.5 的 Rollout Manager 最多编排 10 万个并发 agent 任务"；"K2 的 Kubernetes 沙箱支持 1 万以上并发实例" |
| C-10 | ExploitGym 事件细节 | **一手**（[OpenAI 复盘][openai-hf]，2026-08-26）：事故主体为内部模型 **IM1**，GPT-5.6 Sol 的 Agent 亦有参与（复现漏洞利用、复制部分非公开评测数据）；时间线起点 **05-12** 借 Artifactory 写留言板、05-26 经 SSRF 出站；HF 上 RCE 经 **HDF5 零日 + "RefJinja"模板注入零日**；07-12 扩大 HF 集群访问、生产凭据失陷；07-19 检测、07-20 关联到 HF 事件、07-21 披露；对策为"frontier RL training halted, largest planned RL run on hold" | **二手/Wikipedia**：THN（2026-07-22）称主体为"**GPT-5.6 Sol 与一个预发布模型**"；Wikipedia 记"首次逃逸尝试 **05-08**"（早于其自记的 ExploitGym 发布日 05-11，自相矛盾）、约 **1,200** 个 Agent、HF 约三分之一基础设施重建、07-27 修补 9 个 Artifactory CVE、08-18 宣布"**暂停 RL 两周**"；Substack 称 RCE 经 **fsspec/Jinja2**、约 **17,600** 次动作；CSA 称"超过 **17,000** 次动作"、07-16 为入侵披露日 | 一手优先；二手中与一手不一致或一手未提及的细节不引用 | 以一手复盘为准："OpenAI 在 2026-08-26 的复盘中称事故主体为内部模型 IM1……"；如需提及早期报道的模型名，写"早期二手报道称涉及 GPT-5.6 Sol，与一手复盘不一致"。动作数若引用，写"二手报道称约 1.7 万次" |
| C-11 | CubeSandbox 版本与开源日期 | 版本：**v0.6.0（2026-07）**，据 README_zh；开源日期 **04-21**，腾讯云开发者社区 | 版本：**v0.5.0（2026-07，新增 AutoPause/Resume 与 ARM64）**，据 GitHub README；开源日期 **04-23**，PR Newswire（英文新闻稿） | **已核对（2026-10-04，第 6 章）**：仓库全部 tag 显示 v0.5.0（07-03）与 v0.6.0（07-24）为相继版本，不冲突；此后 v0.7.0（08-28）、v0.7.1（09-11）、v0.7.2（09-24，截至 10-04 最新正式版）；开源日期三说（04-20 仓库 README 新闻栏与 v0.1.0 tag / 04-21 中文首发 / 04-23 英文通稿），并列 | "2026 年 4 月全栈开源（仓库首个 tag 为 4 月 20 日；腾讯云开发者社区 4 月 21 日；英文新闻稿 4 月 23 日）"；版本号按 tag 写，如"v0.5.0（2026-07-03）引入 AutoPause/AutoResume" |
| C-12 | CubeSandbox 单机密度 | "单台 96 核机器 2000+ 实例"，腾讯云开发者社区 2026-04-21 | "thousands of concurrent sandboxes per node"，GitHub README | 量级一致，精度不同 | 用具体口径："96 核物理机上 2000 多个沙箱（厂商自报）"；仓库裸金属报告实测 1,000 个空闲沙箱（2 vCPU / 2 GiB）稳定、摊销约 25 MB，满载估算约 185 个（375 GiB），见 B06-21 |
| C-13 | 冷启动/创建速率量级比较的时效 | 早期说法：GKE 300/s、ACS 1.5 万/分钟（约 250/s）→ 公有云比 DSec（> 5,000/s）低一个数量级以上 | ACS 2026-09-28 营销口径为 10 万/分钟（约 1,667/s，笔者推算） | 结论依赖所取日期 | "按 2026 年年中各家公开口径，公有云沙箱服务的创建速率比 DSec 自建集群低一个数量级左右（口径不同，仅作量级比较）"；若取 ACS 营销稿口径（约 1,667/秒），与 DSec（> 5,000/秒）差约 3 倍 |
| C-14 | Terminal-Bench 任务数 | **241** 个任务，综述表 4 标为"Terminal-Bench 2.1"（Terminal Agents 综述，arXiv 2608.20485，2026-08） | **89** 个任务，Terminal-Bench 2.0（一手：tbench.ai 2.1 页"We're releasing Terminal-Bench 2.1 to fix issues in 28 of the 89 tasks in Terminal-Bench 2.0."；VentureBeat 2025-11-07 同为 89） | 不是版本差异可以解释的：官方 2.1 只修订 89 个任务中的 28 个，241 的来源不明 | 引用时写明版本："Terminal-Bench 2.0（89 个任务）"；241 仅在引述该综述时出现并加注 |
| C-15 | DSec 媒体转述漂移 | 论文：§2.4 "It manages **petabytes** of layers and images"；一周活跃制品 **超过 130 TB**；§8.2 对照组 **Docker Pull (cold)**（从远端 registry 冷态全量拉取，> 60 分钟）与 **Docker Pull (cached)**（约 35 分钟）；完整 VM 面向**商用现成 OS（如 Android）**与图形；访问比例 **4.2%–13.3%** | 36kr（转自智东西，2026-09-23/24）："**PB 级镜像**""**Docker cold pull takes more than 60 minutes**"；Dataconomy（2026-09-25）："**Windows/macOS**""访问**不到 10%**"；第一财经附带 CFO、IPO、约 5000 亿元估值等与论文无关信息 | 36kr 两项主要是口径问题（有原文依据）；Windows/macOS 与"不到 10%"为媒体放大或简化 | 一律直接引用论文："平台管理 PB 量级的层与镜像，其中一周内活跃的制品超过 130 TB"；"冷态全量预拉取需 60 分钟以上，按需加载约 35 分钟，与镜像已在本地的基线持平"；不使用"Windows/macOS""不到 10%"表述 |
| C-16 | Modal 冷启动与价格 | 冷启动 **300–500 ms**、价格 **$0.14/vCPU-h**（非可抢占），Morph 2026-04-04 | 冷启动 **p50 约 100 ms**（bex.co 2026-09-06）；价格 **$0.047/vCPU-h**（Northflank 2026-01-17） | 均为竞品或第三方；价格差可能来自可抢占与否 | 写区间并注明来源类型："第三方对比给出 $0.047–0.14/vCPU-h、冷启动 100–500 ms 不等" |
| C-17 | Daytona A 轮日期 | **2026-02-05**，$24M，FirstMark 领投，[Daytona 官方博客][daytona-blog]；并描述快照功能 | Morph 对比页称 A 轮在"**2025 年初**"且"**无原生持久化**" | 以一手为准 | "Daytona 于 2026 年 2 月完成 2,400 万美元 A 轮（官方公告）" |
| C-18 | E2B 冷启动 | **约 150 ms**（Morph 2026-04；E2B 的 Manus 案例 2025-05） | **< 200 ms**（Better Stack 2026-03-09）；"**sub-500 ms**"（bex.co 标题，2026-07-31） | 均非独立测试 | "约 150 ms（厂商与第三方对比的常见口径）" |
| C-19 | AgentENV 公开日期 | **2026-07-25**：首次提交与 v0.1.0 标签 | **2026-07-27**：MarkTechPost、OpenSourceForU 报道日期；AI Weekly 07-28 | 仓库发布与媒体报道之差 | "2026 年 7 月 25 日开源（媒体于 7 月 27 日报道）" |
| C-20 | RollArt 会议状态 | 一说：OSDI'26 | 另一说：arXiv 注释仅写页数，所抓 OSDI'26 程序未列 RollArt，"未核实" | **核实确属 OSDI'26**（USENIX 演讲页 osdi26/presentation/gao） | "RollArt（OSDI'26）" |
| C-21 | AgentCgroup：OS 执行占延迟比例 | **56–74%**（工具 + 初始化占端到端延迟），AgenticOS'26 论文 PDF | **55–60%**：arXiv 2602.09345 v3（2026-07-22；v1 2026-02-10）摘要原文 "accounts for 55-60% of end-to-end task latency"（2026-10-02 核实） | 版本差异，口径相同（工具调用加容器与 Agent 初始化占端到端时延）；其余描述（185 MB、15.4×、云负载对照）两版本一致 | "AgentCgroup 研讨会版本（AgenticOS'26 PDF）称 56%–74%，arXiv 版本（v3）称 55%–60%"，两者并列 |
| C-22 | AgentBay 流协议带宽节省 | **55%**，论文结论："reduces bandwidth consumption by up to 55% compared to RDP in video playback scenarios (4.6mbps vs 10.2mbps)" | **50%**，论文摘要："ASP protocol reduces bandwidth consumption by up to 50% compared to standard RDP"（TrEnv 同类清单沿用摘要） | 同一论文摘要与结论口径不同，并非二手转述 | "论文摘要称最多降 50%，结论按视频播放场景称最多降 55%（4.6 vs 10.2 Mbps）" |
| C-23 | Cordon 是否存在 | 早期检索：未找到，[U] | arXiv **2606.17573**（2026-06-16；Zheng Chen, …, Jidong Zhai），书目已核实，机制未读 | 已解决：论文存在 | 引用书目信息；机制描述以 DeltaBox 清单转述为限并注明"未读正文" |
| C-24 | 智谱环境数"1 万+" | 早期来源：仅来自聚合博客，"未核实" | GLM-5 报告一手确认"over 10k verifiable environments"（9 种语言），另有"over 1k concurrent rollouts" | 已解决 | 直接引用 GLM-5 报告 |
| C-25 | Kimi K2 并发沙箱数 | 早期摘录：所抽取文本中"没有 Kubernetes 并发数" | 原文"over 10,000 concurrent sandbox instances"（Kubernetes） | 已解决 | 直接引用 K2 报告原文 |
| C-26 | RedCode 用例数 | **4,050**（据论文摘要） | "4,000+"（二手转述，背景知识） | 非实质冲突 | 写"4,050 个" |
| C-27 | Claude Mythos 逃逸是否"自主" | Futurism 引系统卡：早期版本**被指示**逃出沙箱并联系研究者；自主的是随后公开发布利用细节与隐藏修改记录 | The Next Web（2026-04-08）：描述为模型"**自主**"逃逸；另称 12 家伙伴"每家最多 1 亿美元 API 额度" | 系统卡原文（§4.1.1，第 54 页起）：逃逸由模拟用户指示，通知研究者为"as requested"，公开发布利用细节为"unasked-for"；TNW 的"自主"与原文不符；"每家 1 亿美元"疑为总额 | "据系统卡，该模型是在行为测试中被模拟用户指示逃逸……"（Mythos Preview 系统卡 §4.1.1；一手文档） |
| C-28 | Surge 营收 | ARR 约 **$10 亿**（估计），SemiAnalysis 2026-01-06 | 上一年营收 **$12 亿**，TechCrunch 2025-09-21（报道） | 口径不同（ARR 估计 vs 年营收），均为二手 | "据报道约 10 亿美元量级" |
| C-29 | ExploitGym 披露日期 | OpenAI 披露 **07-21**（一手）；THN 报道 07-22 | CSA：Hugging Face 于 **07-16** 披露入侵（原文"On July 16, 2026, Hugging Face disclosed…"）；OpenAI 披露 07-21 | 07-16 为 Hugging Face 的披露日，早于 OpenAI 07-21 的披露（CSA 研究笔记，2026-10-06 逐字复核） | 用一手："2026 年 7 月 19 日检测、21 日披露" |
| C-30 | Anthropic/Irregular PyPI 下载数 | InfoQ（2026-08-13）、THN（2026-07）：约 1 小时内 **15 个**系统下载 | THN 2026-09 后续报道**未给数字** | 以一手为准（Anthropic 事故页 2026-07-30：公开约一小时，被 15 个真实系统下载并运行） | "据 Anthropic 的事故页，该包公开约一小时，在此期间被 15 个真实系统下载并运行，其中包括一家真实安全公司的扫描器" |
| C-31 | 暂停延迟"数字与口径不一"总表 | DSec：**无数字**；AgentENV README < 50/100 ms；K3 133/49 ms | E2B 约 3 s（bex.co，512 MiB）；E2B 文档自称暂停约每 GB 内存 4 s、恢复约 1 s（一手，2026-10-04 读取，B16-11）；DeltaBox 摘要 14/5 ms vs 表 2 10.83/1.86 ms；DeltaBox 在自身环境中测得 E2B（增量）524.4/899.7 ms（与 bex.co 约 3 s 相差数倍）；Blaxel 25 ms；Sprites 约 300 ms；Cloudflare 2 s；ACS 唤醒 1–10 s / P99 < 600 ms | 统计口径（内存态/深度休眠、最低值/P99/约值）各异 | 比较时列表并注明口径，不作排名 |
| C-32 | Firecracker 启动 | 官方规格：InstanceStart 到 `/sbin/init` **≤ 125 ms** | microsandbox 自测 Firecracker **808 ms**（2026-06） | 测量对象不同（完整启动 vs VMM 至 init） | 引官方规格；厂商自测只在讨论 microsandbox 时出现并注明 |
| C-33 | 84% 权限提示减少的出处 | 2026-05-25 "How we contain Claude"（一手，已抓取） | 另有转述称出自 2025-10 "Claude Code sandboxing"（未核实） | 两篇博文可能都提及；已核实的是 2026-05 版 | 引 2026-05-25 博文 |
| C-34 | AgentENV P2P 是否用于生产 | Kimi K3 报告 §5.3.2：采用 "P2P transport" 实现亚秒级启动 | AgentENV 配置参考 `[p2p]`（HEAD 00351e2）："Experimental: P2P has not been tested in production. Keep it disabled in production…" | 可能是生产实现或版本与开源仓库不同，双方均未说明 | "K3 报告称采用了 P2P 传输；开源仓库文档称 P2P 尚未经生产测试" |
| C-35 | DSec 为何不用 P2P | 早期稿件（第 10 章初稿、附录 E C10-09）："DSec 以低扇出论证 P2P 收益有限" | DSec §5.3 原文：改为把镜像放在 3FS 上，"This choice reuses the existing storage infrastructure and avoids deploying a separate image-distribution layer" | 初稿说法错误 | "DSec 以复用 3FS、免建分发层为由不依赖 P2P（§5.3）；低扇出削弱 P2P 收益为本书推断" |
| C-36 | Codex cloud "Common dependencies"预设域名数 | **约 80 个**：据页面摘要，2026-09-30 | **71 个**：2026-10-03 转录全表（第 14、15 章）；同日其他抓取摘要称 60、67、76 个（第 14、15、18 章）；页面本身未写总数 | 页面未给总数，各数字均来自网页读取；"约 80"无法复现；全书统一为"约 70 个（转录计数）" | "Codex 的'Common dependencies'预设包含约 70 个域名（页面未写总数，本书据 2026-10-03 转录计数）" |
| C-37 | DORA 的规模与加速比组合 | 文献库 C17-08 与 B17-06 旧文：在 4,096 卡上"端到端吞吐 2.12×，Agent rollout 最高 6.2×" | DORA 原文：2.12× 为 128 张 GPU 开源基准（rollout 阶段 8.2×），6.2× 为 4,096 卡生产部署且相对生产同步基线 | 拆开两组条件 | "DORA 在开源基准上端到端吞吐最高提升 2.12 倍；在 4,096 张加速卡的生产部署中，Agent 训练 rollout 最高加速 6.2 倍（相对生产同步基线）" |
| C-38 | SandboxFusion 语言数与基准数 | README：21 个语言条目、在线评测 11 个基准（2026-10-04） | 文档：首页"最多 20 种"语言（另页含 Lean）、Get Started 页 12 个数据集（多 miniF2F）；早期稿件"24 种"无出处 | 来源不同；"24 种"无出处 | 按来源分列："README 列 21 个语言条目、11 个基准，文档称最多 20 种语言、12 个数据集"；不写"24 种" |
| C-39 | Pydantic Monty 的技术归类与状态 | 第三方博客（victorstack，2026-02-07）：Wasm 方案；旧版 README：实验性、0.06 ms | 当前 README 与文档（2026-10-04）："A secure Python sandbox, written in Rust"；v1.0.0，"ready for production use"；池内新建 < 1 ms | 二手归类错误；版本更新 | 写"Rust 编写的 Python 沙箱（解释器），v1.0.0"，不写"Wasm 沙箱""实验性" |
| C-40 | Cua 沙箱的虚拟化选型与 pool/claim | 早期摘要（2026-09-30）：Linux 容器、macOS Lume、Windows QEMU/Hyper-V、Android QEMU；fleet 模式 pool 与 claim 分离。2026-10-02 回原文读到 "A pool defines the boot artifact and capacity; a claim reserves a sandbox for a workload." | Cua《How sandboxes work》（2026-10-04 读取，第 7 章）：本地容器 gVisor/runc，VM 用 QEMU，macOS guest 在 Apple silicon 上用 Lume；云上容器 gVisor、VM KubeVirt；"macOS and Windows images are VMs"；该页未提 Hyper-V、Android、pool、claim，另有"Cua Fleets"负责容量管理 | 文档改版，或 pool/claim 位于 Fleets 等其他页面；10-02 的引文有一手依据。2026-10-05 复核：Cua《Cloud Fleets》页（https://cua.ai/docs/cloud-fleets）原文 "A pool owns reusable hosted capacity; a claim reserves one computer from that capacity for a workload."，pool 与 claim 分离成立，原引文措辞已改版 | 虚拟化选型按 10-04 文档写："Linux 镜像可运行于容器（gVisor/runc），macOS 与 Windows 镜像以 VM 运行（QEMU、Lume；云上 KubeVirt）"；pool/claim 写明"据 Cua 文档（2026-10-02 读取）"；Hyper-V、Android QEMU 不写 |
| C-41 | E2B 默认自动暂停 | bex.co（2026-09-06，二手）：默认空闲 15 分钟自动暂停 | E2B persistence 文档（一手，2026-10-04）："默认超时即终止"；规范 `autoPause` 默认 false，`timeout` 默认 300 s（v2）/15 s（v1） | 以一手为准；二手说法来源不明（第 16 章原编号 C-38，2026-10-04 合并时改为 C-41） | "E2B 默认在超时后终止沙箱，需在创建时显式设置 `onTimeout: pause` 才会自动暂停" |
| C-42 | gVisor 宿主 syscall 与实现数 | Sentry 53 种（含网络 68 种）、重新实现约 274 个、内核 ABI 450+（emirb 2026-03-27，转引自 luiscardoso.dev，实为三手） | Sentry 55 种、向应用暴露 319 个中 211 个（HotCloud'19，2019 年版本）；amd64 兼容表 352 个中 290 个有实现、62 个不支持（gVisor 官方，2026-10-04）；官方安全文档不给具体数 | 版本与口径不同（宿主调用 vs 对应用提供的调用；全 ABI vs amd64 表） | "Sentry 只向宿主发出几十种系统调用（2019 年论文 55 种；二手资料 53 种、含网络 68 种），向应用提供数百个系统调用的实现（官方 amd64 表 352 个中 290 个）" |
| C-43 | ComputeSDK 参评厂商数 | 早期读取（2026-10-02 结果）：**28 家** | ComputeSDK 页面（2026-10-05 读取）：**30 家** | 排行榜持续增补，时点不同 | "参评厂商数随时间增加（10-02 前后为 28–30 家）"，引用时注读取日期 |
| C-44 | Daytona 启动延迟 | Better Stack（2026-03-09，二手）：**亚 90 ms** | ComputeSDK Burst TTI（2026-10-02）：**中位 0.33 s、p95 0.42 s**（100 并发突发，create 到首条命令） | 口径不同（单次创建 vs 并发突发含首条命令），不是测量矛盾 | 两数并列并写明口径；不以任何一个代表"Daytona 冷启动" |
| C-45 | Anthropic RL 环境支出 | The Information（经 TechCrunch 2025-09-21、Epoch）：讨论在接下来一年花**超过 $10 亿**（B22-34） | Wing VC（2026-01，利益相关）：每年"**数千万美元**"（另称各实验室合计支出 2026 年增长 3–5 倍，B22-65） | 相差一个数量级以上；前者为"讨论"，后者为投资方估计 | 并列，不取中值，不外推市场规模 |
| C-46 | Cloudflare Sandbox"冷启动约 30 s" | 附录 E C22-12、B11-12 旧文：**冷启动约 30 s**，R2 快照恢复 2 s | Cloudflare Sandbox GA 博客（2026-04-13）：约 30 s 是**克隆仓库加 npm install 的工作流耗时**，约 2 s 是从 R2 备份恢复 | 二手转述把工作流耗时误作冷启动 | "GA 博客中克隆仓库并 npm install 约 30 s，从 R2 备份恢复约 2 s；未见容器冷启动数字" |
| C-47 | Cube 承载调用量 | **过百亿级**："承载过百亿级调用"，[腾讯云开发者社区][cube-dev] 中文原文，2026-04-21 | **超过 1000 亿 / over 100 billion**：B21-08 旧值；网页英文摘要 | 后者为转写错误，非来源冲突 | "Cube'承载过百亿级调用'（腾讯云，厂商自报）" |
| C-48 | MiniMax 在 Cube 上的沙箱规模口径 | **"分钟级调度数十万沙箱实例"**（Agentic RL），[腾讯云开发者社区][cube-dev]，2026-04-21 | **"runs hundreds of thousands of heterogeneous sandboxes (Linux, Windows, Android) concurrently"**，[AAP 英文新闻稿](https://www.aap.com.au/aapreleases/cision20260423ae41855/)，2026-04-23 | 中文为调度速率，英文为并发存量，单位不同；均为腾讯自报 | "腾讯称 Cube 支持 MiniMax 在 Agentic RL 中'分钟级调度数十万沙箱实例'（英文稿写作并发运行数十万个异构沙箱）" |
| C-49 | Terminal-Bench 2.1 修订任务数 | **28 个**：tbench.ai 2.1 公告"fix issues in 28 of the 89 tasks in Terminal-Bench 2.0"（B20-23） | **26 个**：harbor-framework/terminal-bench-2-1 仓库 README"26 tasks were modified…"（2026-10-05 读取，B27-28） | 均为一手，原因未查明（可能是公告与仓库版本不同步，或计数口径不同）；不二选一 | "2.1 修订的任务数，仓库 README 写 26 个，tbench.ai 公告写 28 个" |
| C-50 | CAISI RFI 发布日期 | **2026-01-08**：联邦公报刊登（一手） | **2026-01-12**：CASRAI 指南（二手） | 前者为公报刊登日；后者可能为 NIST 新闻稿日期，未核实 | "CAISI 的 RFI 于 2026 年 1 月 8 日刊登于联邦公报（二手指南记为 1 月 12 日）" |
| C-51 | 《智能体部署使用安全指引》发布日期 | **2026-07**：PDF 版本 v1.0-202607；媒体 2026-07-04（Geopolitechs）、07-06（MLex、cn-sec） | **2026-08-24**：TC260 实践指南列表页日期（一手；同日另列 PG-20267A、PG-20265A） | 列表页日期可能为上网或更新日期；不二选一 | "2026 年 7 月发布（版本 v1.0-202607；TC260 列表页日期 2026-08-24）" |
| C-52 | Atomix 故障注入与泄漏数字 | **v1（2026-02-16）**：WebArena/OSWorld，30% 下 37–57% 对 0–7%；泄漏 0/1,200（No-Tx 1,200/1,200）；开销 < 0.01% | **v2（2026-05-29）**：τ-bench retail，30% 下 57% 对 0–7%，Checkpoint-Replay 53%；0/500 泄漏，Saga 80%；开销"微秒级" | 版本间更换了主实验 | "Atomix v1 报告……；v2 改以 τ-bench retail 为主实验，报告……" |
| C-53 | Recoverability 作者 Zhihui Zhang 的机构 | 另一书目来源：独立研究者 | alphaXiv：北京信息科技大学（两位作者同列） | 页面信息不同，PDF 未读 | 两说并列 |
| C-54 | SkVM 的题名 | arXiv 2604.03088 题名"SkVM: Revisiting Language VM for Skills across Heterogenous LLMs and Harnesses" | SOSP'26 官方录用列表（sigops.org，2026-10-05 复核）题名"Skill VM: Write Once, Run Everywhere Efficiently"，作者四人相同 | 均为一手；录用版可能改了题名 | "SkVM（SOSP'26 录用题名 *Skill VM: Write Once, Run Everywhere Efficiently*；arXiv 2604.03088 题名不同）" |
| C-55 | AgileLog 的日期 | arXiv 编号 2604.14590（即 2026-04 首次提交） | alphaXiv 页显示"September 23, 2026"（2026-10-05 读取） | 可能为新版本日期，未核实 | 只写 arXiv 编号与"SOSP'26"，不写月份 |
| C-56 | CUA-Sandbox VWA 列的吞吐与内存倍数 | 正文 §4.3 与摘要：吞吐最高 6.20×、每环境内存 9.2×（内存 1,745.2 → 190.0 MiB） | 附录表 6（题注"Exact rollout measurements for Figure 3"）VWA 列：吞吐 0.220 → 0.936、内存 328.9 → 188.4，推得约 4.25×、1.75×（笔者推算） | 论文内部不一致；WebArena、OSWorld 两列与正文一致 | 引正文数字并注"论文附录表 6 的 VWA 一列与正文不一致"（B07-06） |
| C-57 | CVE-Bench 成功率 | v1 摘要（2025-03-21）：零日 13%、一日 25% | v4 摘要（2025-06-24）："can resolve up to 13% of vulnerabilities"；正文：零日 10%、一日 13% | 版本更新所致 | 如引用须写版本与口径（X-27；文献库 C20-15） |
| C-58 | Replit/SaaStr 试验时长 | Lemkin（SaaStr 官网，2025-08-02）："nine mad days" | Business Insider（经 AOL，2025-07-22）："a 12-day 'vibe coding' experiment"，"On day nine… things went sideways" | 当事人原文只说到第九天删库；"12 天"为二手 | 写"连续九天"，不写"12 天试用"（B02-03、X-49） |

---

## 不应引用的数字

> 以下数字在研究材料中出现过，但因过时、误读、自相矛盾、仅凭记忆或纯营销，**不应在正文中作为事实引用**。如需提及，只能作为"被纠正的说法"出现。

| 编号 | 数字/说法 | 出处 | 不应引用的原因 | 替代写法 |
|---|---|---|---|---|
| X-01 | AgentENV "32 stars、7 forks" | 一次网页抓取 | 几乎可以肯定是过时或错误的缓存渲染；GitHub API 无法访问，星标未核实 | 不写星标，或写"星标数未核实" |
| X-02 | DSec core scheduling "7.4 倍改进" | 来源不明的摘要式转述（非媒体报道） | 与逐字原文（45.2% → 17.3%）不符 | 写"50% BE 负载下延迟膨胀从 45.2% 降到 17.3%" |
| X-03 | DSec "PB 级镜像"（口径提示，非错误转述） | 36kr（转自智东西） | 原文有依据：§2.4 称管理 PB 量级的层与镜像；一周活跃量超过 130 TB，二者不可混用 | "平台管理 PB 量级的层与镜像，其中一周内活跃的制品超过 130 TB"，见 C-15、B24-13 |
| X-04 | DSec "Docker cold pull takes more than 60 minutes"（口径提示，非错误转述） | 36kr | 与原文一致（对照组即 Docker Pull (cold)），只是没有提已缓存的 Docker 基线约 35 分钟 | "冷态全量预拉取需 60 分钟以上，按需加载约 35 分钟，与镜像已在本地的基线持平" |
| X-05 | DSec 完整 VM 覆盖 "Windows/macOS" | Dataconomy | 论文只说"商用现成 OS"与 Android | "商用现成 OS（如 Android）" |
| X-06 | DSec "访问不到 10% 的镜像内容" | Dataconomy | Go 为 13.3% | "4.2%–13.3%" |
| X-07 | DeepSeek "约 5000 亿元估值"、CFO 聘任、IPO 筹备 | 第一财经（163） | 与论文无关且未核实 | 不写 |
| X-09 | Kimi K2.5 "10 万个并发沙箱" | 对原文的常见误读 | 原文为 10 万个并发 agent 任务 | 见 C-09 |
| X-10 | ExploitGym "首次逃逸尝试 5 月 8 日"、"约 1,200 个 Agent"、"HF 约三分之一基础设施重建"、"07-27 修补九个 Artifactory CVE"、"08-18 宣布暂停 RL 两周" | Wikipedia | 仅 Wikipedia，未核实；5 月 8 日与其自记 5 月 11 日发布日自相矛盾；一手复盘表述为"frontier RL training halted, largest planned RL run on hold" | 以一手时间线为准（B19-20） |
| X-11 | ExploitGym 事故主体为"GPT-5.6 Sol 与一个预发布模型" | THN 等二手 | 一手复盘把**主要**的 HF 入侵归于内部模型 IM1（"comparable in scale to GPT‑5.6 Sol"），同时写明 "GPT‑5.6 Sol agents also reproduced an exploit and copied some private evaluation data"。二手说法并非凭空，差异在于把 GPT-5.6 Sol 写成了主体 | "主要入侵者为内部模型 IM1；GPT-5.6 Sol 的 Agent 亦复现了一个漏洞利用并复制了部分非公开评测数据（OpenAI 复盘）" |
| X-12 | ExploitGym RCE 经 "fsspec/Jinja2" | Substack | 一手为 HDF5 零日 + "RefJinja"模板注入零日 | 用一手表述 |
| X-13 | slopsquatting "约 19.7% 推荐包为幻觉"（"推荐包"口径错误） | 常见转述（Spracklen et al.） | 数字本身已核实（B15-03），原文分母是生成代码中的 223 万个包引用，不是"推荐包"；本条不再禁止引用，只纠正口径 | 写作"生成代码引用的包中 19.7% 为幻觉（Spracklen 等，2024 年模型）" |
| X-14 | "Gemini RL 跑在 Borg/gVisor 上" | 推测 | 无一手来源；gVisor 仅作为 Gemini CLI 用户侧选项出现 | 不写 |
| X-15 | "Qwen3.5/3.8 在百万级 Agent 环境（million-agent environments）上训练"作为规模数字 | HF 聚合博文；Qwen3.5-397B-A17B 模型卡与 QwenLM/Qwen3.8 README 特性列表 | 一手出处存在，但仅见于模型卡特性列表，无单位（环境数/并发/任务数不明），无技术报告支撑，属营销表述 | "Qwen3.5 模型卡称其 RL 扩展到'million-agent environments'，未给出单位与技术细节" |
| X-16 | Daytona A 轮在"2025 年初"、"无原生持久化" | Morph 竞品对比 | 与 Daytona 一手公告冲突 | 见 C-17 |
| X-17 | GKE Agent Sandbox 是三大云"唯一的原生 Agent 沙箱" | Google Cloud Ambassador（经 InfoQ） | 忽略 AgentCore 与 Azure sessions；最多可理解为"唯一 Kubernetes 原生且开源的" | 不写或改为后者 |
| X-18 | E2B "累计融资 $35M"、"94% Fortune 100" | Morph；bex.co | $35M 有误，官方博客为累计 $32M；94% 仅见 bex.co 等二手，官方 2025-07 为 88% 注册 | "$21M A 轮，累计 $32M；'88% 的财富 100 强已注册'（2025-07，厂商自报）"（B22-01） |
| X-19 | "Meta's Manus 推出面向 agent 执行的云沙箱产品" | adwaitx | 原页抓取失败，未核实 | 不写 |
| X-20 | "很多大公司在用 AgentENV" | 无来源 | 除 DeepSeek 使用其存储组件、RadixArk 有集成外无证据 | "DSec 的 microVM 存储路径使用了 AgentENV 仓库中开源的 Rust OverlayBD/ublk 组件（论文称'我们参与贡献'）" |
| X-21 | Sandlock 对容器"约 200 s、2 GB/克隆"、对 microVM"约 150 s、2 GB/克隆" | multikernel.io 厂商博客 | 疑似稻草人对比 | 只引 Sandlock 自身数字并注明厂商自报 |
| X-22 | "Kedge 3 ms fork""forkd 亚毫秒 VM fork" | 搜索标题 | 仅见标题，未核实 | 不写或注明"未核实的宣称" |
| X-23 | Mythos 伙伴"每家最多 1 亿美元 API 额度" | The Next Web | 看起来不合理，可能为总额 | 不写 |
| X-24 | Modal "$750M、估值 $15.75B" 作为已完成事实 | TechCrunch 单一匿名信源 | 未确认 | 若提及，写"据报道正在洽谈" |
| X-25 | Prime Intellect "估值 $10 亿" | SiliconANGLE 标题 | 官方未披露估值 | 不写或注明"据报道" |
| X-26 | （已全部移出）原登记 RunD "约 200/秒、> 2,500/节点"与 REAP "冷启动平均降 3.7×" | 背景知识 [K] | 2026-10-06 已回原文核实：RunD 见 B06-19；REAP 原文"slashes the cold-start delays by 3.7x, on average"（ASPLOS'21，文献库 C11-03） | 按 B06-19 与原文措辞引用（Slacker 76%/6.4% 已于 2026-10-02 移出，见 B10-16；Firecracker"每宿主每秒最多 150 台"已于 2026-10-04 移出，见 B06-07） |
| X-27 | CVE-Bench "13% / 25%"、Progent "41.2% → 2.2%"（InjecAgent、ASB 已于 2026-10-06 核实移出，见 B20-06、B20-07） | 背景知识 [K] | Progent 未核实；CVE-Bench 存在版本冲突（C-57）：v1 摘要零日 13%、一日 25%，v4（2025-06-24）摘要只写"up to 13%"（正文：零日 10%、一日 13%） | Progent 核对原文后再引用；CVE-Bench 如引用须写版本 |
| X-28 | "Cordon 不存在" | 早期检索结论 | 已被核实推翻（C-23） | 引 arXiv 2606.17573 |
| X-29 | 以 AgentENV README 的 < 50/100 ms 代替 K3 报告数字 | README | 自报上界，与 K3 报告"最低可达"值口径不同 | 见 C-03 |
| X-30 | Manus 联合创始人"泄露不算漏洞"的回应 | 研究者记忆 | 未核实到原帖 | 不写 |
| X-31 | AgentENV "fork 上限 16 个"；"fork 上限随版本从 16 提高到 100" | 首版文档（2026-07-25）；MarkTechPost、bex.co | 代码与 OpenAPI 自首版起即为 1–100，16 是首版文档误写（2026-08-24 更正）；不是冲突数字，也不是上限提高 | 见 C-02 |
| X-32 | "slime 用心跳检测故障沙箱" | 转述 | GLM-5 原文心跳对象为 rollout 服务器、注销自推理路由器（§3.6.3） | "slime 的心跳容错作用于推理侧 rollout 服务器"（B17-23） |
| X-33 | "DeepSeek 工程师在 AgentENV 公开发布之前（07-22）就提交了 overlaybd 代码" | 早期稿件（第 24 章 24.1 边栏、B24-12 旧文） | 07-22 为作者日期，提交日期 07-31；按提交日期最早为 07-26，晚于发布 | "huang-jl 最早的提交在发布次日（07-26）；一次提交的作者日期为 07-22，但 07-31 才合入" |
| X-34 | "K3 的 5,122 万个沙箱全部由 AgentENV 创建" | 媒体与社区转述 | K3 原文未写明，且同节称使用三类运行时 | "K3 报告称其训练与评测共创建 51,219,741 个沙箱；AgentENV README 把其中的 150 万个镜像归于 AgentENV" |
| X-35 | "AgentENV 的代码来自 TrEnv"或"AgentENV 是 TrEnv 的开源实现" | 推断的过度延伸 | README 曾称建立在 TrEnv-X 的"思想与动机"之上，且已删除；实现机制不同 | "README 一度称 AgentENV 建立在 TrEnv-X 研究的部分思想与动机之上（2026-07-26 加入，次日删除）" |
| X-36 | "gVisor 官方称 Sentry 只用 53 个宿主 syscall" | 常见转述 | 官方文档无此数，53/68 来自二手综述（emirb，转引自 luiscardoso.dev） | 写明二手来源，并列 HotCloud'19 的 55，见 C-42 |
| X-37 | 以 HotCloud'19 的 216×、2.8× 描述当前 gVisor 性能 | 2019 年论文 | 版本已陈旧（systrap、directfs 之后） | 只作历史量级，注明年份（B05-09） |
| X-38 | "OpenSandbox 默认使用 gVisor/Kata" | 部分二手介绍 | 官方指南：安全运行时留空即 runc（默认），按服务器配置 | 写"默认 runc，可在服务器级配置 gVisor、Kata 或 Firecracker"（B05-11） |
| X-39 | Superagent "AI Code Sandbox Benchmark 2026" 的冷启动数值（如 Blaxel 约 25 ms、E2B 约 150 ms） | Superagent 博客（2026-01-16） | 无方法论、无利益披露 | 不写；独立基准空白见第 22 章 22.9 节 |
| X-40 | raising.fi 上的"Freestyle $10M A 轮" | raising.fi | 指同名尿布公司，与沙箱厂商 freestyle.sh 无关 | 不写；Freestyle 融资"未找到" |
| X-41 | "Prime Environments Hub 达 2,500 个环境" | 聚合站 | 仅见聚合站，原页无法打开 | 不写；Prime 博客的"超过 365,000 个预构建环境"为任务/镜像口径（B18-11） |
| X-42 | "中国现在冒出很多 RL 环境供应商" | X/Substack 帖 | 原帖无法打开，无公司名 | 不写 |
| X-43 | "Mythos Preview 训练中约 1 万次沙箱突破、10 万次越权" | LessWrong 作者据 0.01%、0.2% 与"数亿次 rollout"的估计推算 | 分母为第三方估计，Anthropic 未披露 rollout 总数 | 只引系统卡比率（经二手引述），见 B27-14 |
| X-44 | "OpenAI 训练跑在 Cloud Hypervisor microVM 上" | 对 ZenML 摘要的延伸 | ZenML 称"讲者的团队使用 Cloud Hypervisor"，官方转录无此句；转录 25:40 处是参考设计中 harness fork cloud-hypervisor 进程；讲者只建议"从一开始就用 microVM"。事故报告显示 Research CaaS 训练与评测负载事故前为容器，复盘另提到事故前已有 VM 研究环境（B27-29） | "演讲以 Cloud Hypervisor 为例讲参考设计，没有说 OpenAI 用哪一种 VMM" |
| X-45 | "训练追求吞吐，产品追求延迟，底座都是 microVM"（OpenAI 工程师演讲） | 目录 v2 第 1 章小节 4 的早期写法 | 两份转录（Weldon、ZenML）只有"研究重吞吐、生产重延迟"，均未写"底座都是 microVM"；后半句是本书推断（B01-05） | "据二手转录，演讲者区分研究场景重吞吐、生产场景重延迟"；底座问题见 X-44 |
| X-46 | "72% 的作弊 episode 在 CoT 中有明确动机"／"72% … include explicit reasoning"／"rationalize exploits as legitimate solutions" | 附录 B B02-10 旧文字、目录 v2、第 19 章旧文字、第 2 章初稿 | 原文为"72% of reward hacking episodes include explicit chain-of-thought rationale"；§6.4 限于暴露推理轨迹的模型；"动机""推理"都改变了原意，后两句英文不是原文 | "72% 的 reward hacking episode 含明确的思维链理由（限暴露推理轨迹的模型）"，见 B02-10 |
| X-47 | "WAA 单任务（或单个沙箱）寿命约 30–35 分钟" | 第 1 章初稿对 B20-15 的误读 | 30–35 分钟是 40 台 Azure VM 并行跑完全量基准的墙钟时间 | "WAA 在 Azure 上用 40 台 VM 并行，一轮全量约 30–35 分钟"，见 B20-15 |
| X-48 | "CUA-Sandbox 以保真度换密度"（与 MobileGym 并列为"以保真度换密度"一类） | 第 7 章初稿（仅读摘要时的归类） | CUA-Sandbox 保留真实软件接口与原评估器（"retaining the original software interfaces and task evaluators"），12 组模型–基准配对成功率都高于 Docker；代价在隔离依赖资源契约与绑定覆盖 | "MobileGym 以保真度换密度；CUA-Sandbox 保留真实应用，代价在隔离覆盖"（B07-06） |
| X-49 | "SaaStr 创始人在为期 12 天的试用进行到第 9 天时"；"删库后生成约 4,000 条假数据" | vectara 案例、Slashdot、Business Insider（二手） | 当事人原文只说"nine mad days"；4,000 条是 The Register 转引的"虚构人物"数据库，与删库先后未交代（C-58） | "Lemkin 自述，连续九天 vibe coding 之后……另据 The Register 转引，Agent 还生成过一个 4,000 条记录、全是虚构人物的数据库"（B02-03） |
| X-50 | OpenAI 演讲："生产场景重延迟，要求亚秒级执行"（sub-second execution） | Sean Weldon 演讲笔记（二手） | AI Engineer 官方转录中没有 "sub-second"，只有 "start it in milliseconds" 与"产品上时延非常重要" | "产品上时延非常重要"（官方转录） |
| X-51 | "Codex gold mode 可运行三天的任务" | ZenML 摘要（二手） | 官方转录为 "goal mode"，"三天"是讲者个人跑任务的最长记录，不是产品参数 | 见 B01-03 |
| X-52 | "Opus 4.7 系统卡称导致意外 CoT 监督的错误在 Opus 4.5、4.6 与 Mythos 中也存在" | Zvi 对 Opus 4.7 系统卡的转述 | 系统卡 §2.4.1 原文为"some prior models (including Mythos Preview)"，未逐一列出 Opus 4.5、4.6 | "该错误在包括 Mythos Preview 在内的部分先前模型中也存在"（B27-15） |
| X-53 | "CUA-Sandbox 通讯作者为 Yang You" | 第 11 章初稿（仅读摘要） | 论文首页 "† Corresponding author" 标在 Xingrui Yu（A*STAR）；Yang You 是倒数第三位作者 | "通讯作者 Xingrui Yu（A*STAR）" |
| X-54 | "TC260-TR-005-2026 发布于 2026-04-09" | 搜狐转载摘要（转载日期） | TC260 通知（网安秘字〔2026〕34 号）落款 2026-03-26 | "2026-03-26 发布"（B23-02） |
| X-55 | SandboxEscapeBench：CAP_SYS_MODULE/CAP_DAC_READ_SEARCH 难度 2、ebpf/dirty_cow/dirty_pipe 难度 4、cgroup 两个场景、"README 难度体系与论文不一致" | 第 5 章初稿表 5-2（抓取摘录） | 论文表 1、仓库 README 与绘图代码 difficulty.py 三方一致：CAP_MOD、CAP_DAC_RD 为 3，bpf 为 5，dirty cow/pipe 为 3，cgroup 只有一个场景，另有 hostpath（1） | 按 B05-13 与表 5-2 新版 |
| X-56 | "OpenAI 工程师演讲称训练与产品共用 microVM 底座" | 对 ZenML 摘要的延伸（第 17 章初稿） | 官方转录与 ZenML 都没有这样说；讲者只自述同时负责 RL 基础设施与产品侧不可信代码执行基础设施 | "讲者同时负责两侧基础设施，但没有说两者共用同一底座" |

---

## 参考链接

[dsec]: https://arxiv.org/html/2609.22978v1 "DeepSeek Elastic Compute (DSec), arXiv 2609.22978v1"
[dsec-abs]: https://arxiv.org/abs/2609.22978
[k3]: https://arxiv.org/pdf/2607.24653 "Kimi K3 Technical Report, arXiv 2607.24653"
[k2]: https://arxiv.org/html/2507.20534v1 "Kimi K2, arXiv 2507.20534"
[k25]: https://arxiv.org/pdf/2602.02276 "Kimi K2.5, arXiv 2602.02276"
[aenv]: https://github.com/kvcache-ai/AgentENV "kvcache-ai/AgentENV"
[aenv-readme]: https://github.com/kvcache-ai/AgentENV/blob/main/README.md
[aenv-rel]: https://github.com/kvcache-ai/AgentENV/releases/tag/v0.2.2
[mtp]: https://www.marktechpost.com/2026/07/27/kimi-ai-and-kvcache-ai-open-sources-agentenv/
[bex-aenv]: https://bex.co/blog/2026/09/22/agentenv-kimi-k3-self-hosted-e2b-sandbox-cost
[kvcache-org]: https://github.com/kvcache-ai
[technode]: https://technode.com/2026/09/23/deepseek-dsec-agent-training-sandbox-infrastructure/
[163-dsec]: https://www.163.com/dy/article/L7I0F0CJ0519DDQ2.html
[36kr]: https://eu.36kr.com/en/p/3996009656536962
[dataconomy]: https://dataconomy.com/2026/09/25/deepseek-ai-agent-training-platform-sandboxes/
[hn-dsec]: https://news.ycombinator.com/item?id=49859112
[modal-rl]: https://modal.com/resources/best-sandboxes-rl-environments
[aliyun-osb]: https://developer.aliyun.com/article/1762374
[zenml]: https://www.zenml.io/llmops-database/designing-agent-sandbox-infrastructure-at-scale-from-runtime-to-orchestration
[termsurvey]: https://arxiv.org/html/2608.20485v1
[willison]: https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
[owasp]: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
[replit-case]: https://github.com/vectara/awesome-agent-failures/blob/main/docs/case-studies/replit-ai-database-deletion.md
[slashdot-replit]: https://developers.slashdot.org/story/25/07/21/1338204/replit-wiped-production-database-faked-data-to-cover-bugs-saastr-founder-says
[nist-comp]: https://www.nist.gov/blogs/caisi-research-blog/insights-ai-agent-security-large-scale-red-teaming-competition
[camel]: https://arxiv.org/abs/2503.18813
[nova]: https://arxiv.org/abs/2601.09923
[isolategpt]: https://arxiv.org/abs/2403.04960
[progent]: https://huggingface.co/papers/2504.11703
[oap]: https://arxiv.org/pdf/2603.20953
[rhb]: https://arxiv.org/abs/2605.02964
[row-manus]: https://restofworld.org/2026/meta-manus-singapore/
[cnbc-manus]: https://www.cnbc.com/2025/12/30/meta-acquires-singapore-ai-agent-firm-manus-china-butterfly-effect-monicai.html
[tnw-manus]: https://thenextweb.com/news/china-blocks-meta-manus-2-billion-acquisition
[tc-manus]: https://techcrunch.com/2026/06/13/meta-reportedly-moves-to-unwind-2b-manus-deal-after-beijings-demand/
[agentcgroup]: https://os-for-agent.github.io/papers/AgenticOS_2026_paper_10.pdf
[agentcgroup-arxiv]: https://arxiv.org/abs/2602.09345 "AgentCgroup, arXiv 2602.09345（v3 2026-07-22）"
[crab]: https://arxiv.org/abs/2604.28138
[anthropic-contain]: https://www.anthropic.com/engineering/how-we-contain-claude
[srt]: https://github.com/anthropic-experimental/sandbox-runtime
[securityweek]: https://www.securityweek.com/anthropic-silently-patches-claude-code-sandbox-bypass/
[bleeping]: https://www.bleepingcomputer.com/news/security/cursor-codex-gemini-cli-antigravity-hit-by-sandbox-escapes/
[thn-gemini]: https://thehackernews.com/2026/04/google-fixes-cvss-10-gemini-cli-ci-rce.html
[landlock]: https://docs.kernel.org/userspace-api/landlock.html
[sandlock]: https://multikernel.io/2026/03/19/sandlock-cow-fork/
[codex-sandbox]: https://learn.chatgpt.com/codex/sandboxing
[cncf-runc]: https://www.cncf.io/blog/2025/11/28/runc-container-breakout-vulnerabilities-a-technical-overview/
[emirb]: https://emirb.github.io/blog/microvm-2026/
[manveerc]: https://manveerc.substack.com/p/ai-agent-sandboxing-guide
[fc-spec]: https://github.com/firecracker-microvm/firecracker/blob/main/SPECIFICATION.md
[fc-nsdi]: https://www.usenix.org/conference/nsdi20/presentation/agache
[microsandbox]: https://rywalker.com/research/microsandbox
[cube-readme]: https://github.com/TencentCloud/CubeSandbox/blob/master/README_zh.md
[cube-gh]: https://github.com/tencentcloud/CubeSandbox
[cube-dev]: https://cloud.tencent.com/developer/article/2657863
[cube-pr]: https://www.prnewswire.co.uk/news-releases/tencent-cloud-cube-sandbox-goes-fully-open-source-with-five-major-breakthroughs-enabling-large-scale-agent-deployment-302751546.html
[hyperlight]: https://opensource.microsoft.com/blog/2024/11/07/introducing-hyperlight-virtual-machine-based-security-for-functions-at-scale/
[rund]: https://www.usenix.org/conference/atc22/presentation/li-zijun-rund
[uitars2]: https://arxiv.org/html/2509.02544
[computerrl]: https://arxiv.org/html/2508.14040v1
[mobilerl]: https://arxiv.org/html/2509.18119v1
[stepgui]: https://arxiv.org/pdf/2512.15431
[cuasandbox]: https://www.alphaxiv.org/abs/2609.32750
[mobilegym]: https://arxiv.org/html/2605.26114
[agentbay-paper]: https://arxiv.org/html/2512.04367
[eclectic]: https://eclecticlight.co/2022/08/04/virtualisation-on-apple-silicon-macs-8-how-apple-limits-vms/
[kernel]: https://www.kernel.sh/ai-library/best-browsers-for-ai-agents-2026
[trenvx]: https://arxiv.org/html/2509.09525v2
[cellmate]: https://arxiv.org/html/2512.12594v2
[opencua]: https://arxiv.org/html/2508.09123v3
[dmi]: https://os-for-agent.github.io/papers/AgenticOS_2026_paper_9.pdf
[autoglm-sina]: https://finance.sina.com.cn/roll/2025-08-20/doc-infmrhsi5346631.shtml?froms=ggmp
[qbit-autoglm]: https://www.qbitai.com/2025/08/324341.html
[hackworld]: https://arxiv.org/html/2510.12200
[swemini]: https://arxiv.org/html/2602.11210
[execonly]: https://os-for-agent.github.io/papers/AgenticOS_2026_paper_21.pdf
[tee-survey]: https://arxiv.org/html/2605.03213v1
[sandboxfusion]: https://github.com/bytedance/SandboxFusion
[cursor-cloud]: https://cursor.com/blog/cloud-agent-lessons
[rollart]: https://arxiv.org/html/2512.22560v1
[rollart-pdf]: https://www.cse.ust.hk/~weiwa/papers/rollart-osdi26.pdf
[rollart-osdi]: https://www.usenix.org/conference/osdi26/presentation/gao
[kat]: https://arxiv.org/html/2607.05471v1
[slacker]: https://www.usenix.org/conference/fast16/technical-sessions/presentation/harter
[dadi]: https://www.usenix.org/conference/atc20/presentation/li-huiba
[soci]: https://arxiv.org/html/2607.06868v1
[flacio]: https://www.usenix.org/conference/fast25/presentation/liu-yubo
[lambda-atc]: https://www.usenix.org/conference/atc23/presentation/brooker
[mtp-aenv]: https://www.marktechpost.com/2026/07/27/kimi-ai-and-kvcache-ai-open-sources-agentenv/
[bex-e2b]: https://bex.co/blog/2026/09/06/e2b-scaling-cracks-idle-costs-suspend-latency
[bex-e2b-growth]: https://bex.co/blog/2026/07/31/e2b-sandbox-growth-firecracker-self-hosted-agent-sandbox
[deltabox]: https://arxiv.org/abs/2605.22781
[branchfs]: https://os-for-agent.github.io/papers/AgenticOS_2026_paper_8.pdf
[agentrewind]: https://arxiv.org/abs/2608.14380
[rir]: https://arxiv.org/abs/2609.18304
[tnw-blaxel]: https://thenextweb.com/news/baseten-acquires-blaxel-ai-agent-sandboxes
[betterstack]: https://betterstack.com/community/comparisons/best-sandbox-runners/
[techzine]: https://www.techzine.eu/news/devops/137884/fly-io-puts-ai-agents-in-vms-not-containers/
[cf-blog]: https://blog.cloudflare.com/sandbox-ga/
[northflank]: https://northflank.com/blog/top-ai-sandbox-platforms-for-code-execution
[bex-kedge]: https://bex.co/blog/2026/08/22/kedge-3ms-vm-fork-snapshot-tree
[forkd]: https://github.com/jrimmer/forkd
[replit]: https://blog.replit.com/inside-replits-snapshot-engine
[morph-infini]: https://cloud.morph.so/docs/blog/developers
[planarian]: https://arxiv.org/abs/2609.35366
[atomix]: https://arxiv.org/abs/2602.14849
[agentictx]: https://arxiv.org/abs/2608.13900
[fts]: https://arxiv.org/abs/2512.12806
[cordon]: https://arxiv.org/html/2606.17573v1
[acrfence]: https://arxiv.org/abs/2603.20625
[sagallm]: https://arxiv.org/abs/2503.11951
[yolofs]: https://arxiv.org/html/2604.13536v2
[recoverability]: https://arxiv.org/html/2609.13672v1
[agentlibos]: https://arxiv.org/html/2606.03895v1
[agentzip]: https://arxiv.org/abs/2609.11294
[specbox]: https://arxiv.org/html/2607.23933v1
[aquifer]: https://pith.science/paper/2606.24079
[vaughan]: https://codex.danielvaughan.com/2026/04/24/agent-sandbox-comparison-codex-seatbelt-openshell-docker-sbx/
[codex-net]: https://learn.chatgpt.com/docs/cloud/internet-access
[codex-env]: https://learn.chatgpt.com/docs/environments/cloud-environment
[beyondtrust]: https://www.beyondtrust.com/blog/entry/pwning-aws-agentcore-code-interpreter
[mcp-spec]: https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices
[loom]: https://github.com/qianyi-sun/loom/issues/2189
[simon-johann]: https://simonwillison.net/2025/Aug/15/the-summer-of-johann/
[openai-hf]: https://openai.com/index/hugging-face-incident-and-the-road-ahead/
[infoq-anthropic]: https://www.infoq.com/news/2026/08/claude-sandox-breach/
[thn-anthropic-jul]: https://thehackernews.com/2026/07/anthropic-says-claude-mistook-open.html
[thn-anthropic-sep]: https://thehackernews.com/2026/09/anthropic-ai-models-breached-real.html
[slopsquat]: https://labs.cloudsecurityalliance.org/research/csa-research-note-slopsquatting-ai-supply-chain-20260419-csa/
[wiki-incident]: https://en.wikipedia.org/wiki/OpenAI%E2%80%93HuggingFace_incident
[openai-sdk]: https://openai.com/index/the-next-evolution-of-the-agents-sdk/
[aaif]: https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation
[hf-rl]: https://huggingface.co/blog/sergiopaniego/rl-environments-2026
[openenv]: https://huggingface.co/blog/openenv-agentic-rl
[agentbound]: https://arxiv.org/abs/2510.21236
[nemo]: https://docs.nvidia.com/nemo/gym/latest/about/ecosystem.html
[rollflash]: https://arxiv.org/html/2510.11345v1
[qoder-blog]: https://www.alibabacloud.com/blog/603370
[dora]: https://arxiv.org/html/2604.26256
[longcat]: https://arxiv.org/html/2601.16725v1
[cwm]: https://arxiv.org/html/2510.02387v1
[deepswe]: https://www.together.ai/blog/deepswe
[glm5]: https://arxiv.org/pdf/2602.15763
[tax]: https://arxiv.org/abs/2607.01415
[xai-grok45]: https://x.ai/news/grok-4-5
[xai-grok4]: https://x.ai/news/grok-4
[forge]: https://www.minimax.io/news/forge-scalable-agent-rl-framework-and-algorithm
[qcn]: https://arxiv.org/html/2603.00729v1
[qwen3coder]: https://qwenlm.github.io/blog/qwen3-coder/
[semianalysis]: https://newsletter.semianalysis.com/p/rl-environments-and-rl-for-science
[step35]: https://arxiv.org/html/2602.10604
[m2]: https://arxiv.org/html/2605.26494v1
[mimo]: https://arxiv.org/html/2601.02780v1
[prime-sandboxes]: https://www.primeintellect.ai/blog/sandboxes
[skvm]: https://arxiv.org/abs/2604.03088
[skillos]: https://os-for-agent.github.io/papers/AgenticOS_2026_paper_13.pdf
[fame]: https://arxiv.org/html/2601.14735v1
[cursor-rh]: https://cursor.com/blog/reward-hacking-coding-benchmarks
[metr]: https://metr.org/blog/2025-06-05-recent-reward-hacking/
[impossible]: https://arxiv.org/html/2510.20270v1
[swebench465]: https://github.com/SWE-bench/SWE-bench/issues/465
[swebench578]: https://github.com/SWE-bench/SWE-bench/issues/578
[swebench669]: https://github.com/SWE-bench/SWE-bench/issues/669
[osworld2]: https://arxiv.org/html/2606.29537v1
[epoch]: https://epoch.ai/gradient-updates/state-of-rl-envs
[substack-exploitgym]: https://cyberwarrior76.substack.com/p/the-openai-hugging-face-exploitgym
[csa-openai]: https://labs.cloudsecurityalliance.org/research/csa-research-note-openai-model-sandbox-escape-huggingface-br/
[futurism]: https://futurism.com/artificial-intelligence/anthropic-claude-mythos-escaped-sandbox
[tnw-mythos]: https://thenextweb.com/news/anthropics-most-capable-ai-escaped-its-sandbox-and-emailed-a-researcher-so-the-company-wont-release-it
[sebench]: https://arxiv.org/html/2603.02277v1
[aisi-blog]: https://www.aisi.gov.uk/blog/can-ai-agents-escape-their-sandboxes-a-benchmark-for-safely-measuring-container-breakout-capabilities
[agentdojo]: https://arxiv.org/abs/2406.13352
[injecagent]: https://arxiv.org/abs/2403.02691
[asb]: https://arxiv.org/abs/2410.02644
[redcode]: https://huggingface.co/papers/2411.07781
[osharm]: https://arxiv.org/abs/2506.14866
[cvebench]: https://arxiv.org/abs/2503.17332
[toolemu]: https://arxiv.org/abs/2309.15817
[osworld-v]: https://xlang.ai/blog/osworld-verified
[waa]: https://github.com/microsoft/WindowsAgentArena
[androidworld]: https://github.com/google-research/android_world
[webarena-v]: https://github.com/ServiceNow/webarena-verified
[manus-blog]: https://manus.im/blog/manus-sandbox
[e2b-manus]: https://e2b.dev/blog/how-manus-uses-e2b-to-provide-agents-with-virtual-computers
[manus-wide]: https://manus.im/blog/manus-wide-research-solve-context-problem
[kimi-okc]: https://medium.com/@kimi_moonshot/meet-ok-computer-the-agent-mode-in-kimi-2fb0dbf05ce0
[kimi-swarm]: https://www.kimi.com/zh-cn/help/agent/agent-swarm
[trae]: https://hub.baai.ac.cn/view/47554
[copilot]: https://docs.github.com/copilot/concepts/agents/coding-agent/about-coding-agent
[copilot-cl]: https://github.blog/changelog/2025-10-28-copilot-coding-agent-now-supports-self-hosted-runners/
[gke-next26]: https://cloud.google.com/blog/products/containers-kubernetes/whats-new-in-gke-at-next26
[genspark]: https://e2b.dev/customers/genspark
[claude-ma]: https://platform.claude.com/docs/en/managed-agents/cloud-sandboxes-reference
[0din]: https://0din.ai/blog/prompt-injecting-your-way-to-shell-openai-s-containerized-chatgpt-environment
[manus-leak]: https://x.com/jianxliao/status/1898861051183349870
[doubao-qq]: https://news.qq.com/rain/a/20260818A07QIB00
[doubao-std]: https://www.stdaily.com/web/gdxw/2026-08/19/content_566443.html
[docker-cloud]: https://www.docker.com/blog/introducing-cloud-sandboxes-start-on-your-laptop-finish-in-the-cloud/
[e2b-siliconangle]: https://siliconangle.com/2025/07/28/e2b-shares-vision-sandboxed-cloud-environments-every-ai-agent-raising-21m-funding/
[morph]: https://www.morphllm.com/comparisons/daytona-alternative
[bex-funding]: https://bex.co/blog/2026/09/11/ai-sandbox-funding-modal-daytona-e2b
[daytona-blog]: https://www.daytona.io/dotfiles/daytona-raises-24m-series-a-to-give-every-agent-a-computer
[tc-modal]: https://techcrunch.com/2026/09/28/source-inference-provider-modal-labs-closing-in-on-750m-round-at-15-75b-valuation/
[vercel]: https://vercel.com/blog/vercel-sandbox-is-now-generally-available
[vercel-pricing]: https://vercel.com/docs/vercel-sandbox/pricing
[cf-pricing]: https://developers.cloudflare.com/containers/pricing/
[e2b-pricing]: https://e2b.dev/pricing
[sprites]: https://fly.io/sprites/
[infoq-cf]: https://www.infoq.com/news/2026/04/cloudflare-sandboxes-ga/
[blaxel-seed]: https://blaxel.ai/blog/Blaxel-Raises-7-3M-Seed-Round-led-by-First-Round-to-Build-Cloud-Infrastructure-for-the-AI-Agent-Eco-23247e47b1ea8067b923d998364e3ced
[bw-baseten]: https://www.businesswire.com/news/home/20260910783896/en/Baseten-Acquires-Blaxel-to-Build-the-Infrastructure-for-AI-Agents-in-Production
[runloop]: https://runloop.ai/media/runloop-raises-7m-seed-round-to-bring-enterprise-grade-infrastructure-to-ai-coding-agents
[infoq-gke]: https://www.infoq.com/news/2026/05/gke-agent-sandbox-hypercluster/
[agent-sandbox]: https://github.com/kubernetes-sigs/agent-sandbox
[agent-sandbox-config]: https://github.com/kubernetes-sigs/agent-sandbox/blob/main/docs/configuration.md
[agent-sandbox-perf]: https://github.com/kubernetes-sigs/agent-sandbox/blob/main/docs/performance-tuning.md
[azure-sessions]: https://learn.microsoft.com/en-us/azure/container-apps/sessions
[pymnts-prime]: https://www.pymnts.com/news/investment-tracker/2026/prime-intellect-raises-130-million-to-help-companies-train-ai-agents/
[prime-seriesA]: https://www.primeintellect.ai/blog/series-a
[siliconangle-ona]: https://siliconangle.com/2026/06/11/openai-acquires-ai-agent-orchestration-startup-ona/
[techcrunch-env]: https://techcrunch.com/2025/09/21/silicon-valley-bets-big-on-environments-to-train-ai-agents/
[mechanize]: https://www.mechanize.work/mechanize-raises-9-1m/
[troveo]: https://www.troveo.ai/resources/rl-environment-companies
[agentbay-bill]: https://help.aliyun.com/zh/agentbay/product-overview/agentbay-billing
[ags-price]: https://cloud.tencent.com/document/product/1814/133249
[acs-doc]: https://help.aliyun.com/zh/cs/user-guide/agent-sandbox/
[chinaventure]: https://www.chinaventure.com.cn/news/78-20260609-391757.html
[tc260]: https://www.tc260.org.cn/tc260/tzgg/202609/e5b82ae7aca244d19d36b39575cbb458.shtml
[tc260-tr]: https://www.sohu.com/a/1007172854_121864792
[cac-framework]: https://www.cac.gov.cn/2025-09/28/c_1760779758683488.htm
[caict-21csp]: https://news.21csp.com.cn/c3/202604/11429533.html
[caict-eeo]: http://www.eeo.com.cn/2026/0316/811619.shtml
[cset]: https://cset.georgetown.edu/article/eu-ai-code-safety/
[casrai]: https://casrai.org/guides/nist-ai-agent-standards-initiative
[ansi]: https://www.ansi.org/standards-news/all-news/1-15-26-mitigating-risks-of-ai-agent-systems-nist-center-for-ai-standards-and-innovation-issues-rfi
[govai]: https://www.governance.ai/analysis/anthropics-rsp-v3-0-how-it-works-whats-changed-and-some-reflections
[openai-pf]: https://openai.com/index/updating-our-preparedness-framework/
[gdm-fsf]: https://deepmind.google/blog/strengthening-our-frontier-safety-framework/
[cac-agent]: https://www.cac.gov.cn/2026-05/08/c_1779979789523320.htm
[aenvironment]: https://ant-ling.medium.com/aenvironment-an-environment-system-for-the-agentic-rl-era-out-of-the-box-and-interconnected-a2e2f958ec34
[opensandbox]: https://github.com/alibaba/OpenSandbox
[cryptonomist]: https://en.cryptonomist.ch/2026/03/03/opensandbox-ai-sandbox-secure-execution/
[ags-doc]: https://cloud.tencent.com/document/product/1814/129423
[ags-product]: https://cloud.tencent.com/product/agentsandbox
[acs-163]: https://www.163.com/dy/article/L7UCOA870511AQHO.html
[minimax-163]: https://www.163.com/dy/article/KQLH5RFK0511AQHO.html
[hy3]: https://github.com/Tencent-Hunyuan/Hy3
[alphaevolve]: https://arxiv.org/html/2506.13131v1
[geminicli]: https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/sandbox.md
[anthropic-incidents]: https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals "Anthropic: Investigating incidents in cybersecurity evals (2026-07-30)"
[spracklen]: https://arxiv.org/abs/2406.10279 "Spracklen et al., We Have a Package for You! (USENIX Security 2025)"
[bleeping-pypi]: https://www.bleepingcomputer.com/news/security/anthropics-claude-breached-3-orgs-uploaded-pypi-malware-during-tests/
[harbor-cfg]: https://github.com/harbor-framework/harbor/blob/main/src/harbor/models/task/config.py
[tb2-vb]: https://venturebeat.com/ai/terminal-bench-2-0-launches-alongside-harbor-a-new-framework-for-testing
[tb21]: https://www.tbench.ai/news/terminal-bench-2-1
[madsys]: https://madsys.cs.tsinghua.edu.cn/
[runc-ghsa-21626]: https://github.com/opencontainers/runc/security/advisories/GHSA-xr7r-f8xq-vfvv
[snyk-leaky]: https://labs.snyk.io/resources/leaky-vessels-docker-runc-container-breakout-vulnerabilities/
[wiz-nvidiascape]: https://www.wiz.io/blog/nvidia-ai-vulnerability-cve-2025-23266-nvidiascape
[gvisor-amd64]: https://gvisor.dev/docs/user_guide/compatibility/linux/amd64/
[hotcloud19]: https://www.usenix.org/conference/hotcloud19/presentation/young
[gvisor-net]: https://gvisor.dev/blog/2020/04/02/gvisor-networking-security/
[gvisor-seccomp]: https://gvisor.dev/blog/2024/02/01/seccomp/
[osb-secure]: https://github.com/alibaba/OpenSandbox/blob/main/docs/guides/secure-container.md
[cube-bench]: https://github.com/TencentCloud/CubeSandbox/blob/master/docs/blog/posts/2026-06-01-cubesandbox-perf-benchmark.md
[cube-bench-pvm]: https://github.com/TencentCloud/CubeSandbox/blob/master/docs/blog/posts/2026-06-03-cubesandbox-perf-benchmark-pvm.md
[aws-nested]: https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual
[aws-nested2]: https://aws.amazon.com/about-aws/whats-new/2026/06/nested-virtualization-intel-us-gov-cloud/
[pvm]: https://dl.acm.org/doi/10.1145/3600006.3613158
[pvm-rfc]: https://lkml.iu.edu/hypermail/linux/kernel/2402.3/02173.html
[fc-repo]: https://github.com/firecracker-microvm/firecracker
[fc-snap]: https://github.com/firecracker-microvm/firecracker/blob/main/docs/snapshotting/snapshot-support.md
[agentcore-sess]: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html
[imc24-cni]: https://jhc.sjtu.edu.cn/~bjiang/papers/Liu_IMC2024_CNI.pdf "Liu et al., Understanding Network Startup for Secure Containers in Multi-Tenant Clouds (IMC 2024)"
[hyperlight-wasm]: https://opensource.microsoft.com/blog/2025/03/26/hyperlight-wasm-fast-secure-and-os-free/
[doubao-vd]: https://news.qq.com/rain/a/20260818A07QIB00
[doubao-cloud]: https://www.stdaily.com/web/gdxw/2026-08/19/content_566443.html

版本说明（各次修订均为回原文核对后的增改；"改"指修改既有行，"新增"指增加新行）：

- 2026-09-30　初版。同日核对 DSec、沙箱内状态、reward hacking 三组数字：第 24 章相关 22 行（改 19 行，新增 B24-13、B24-14、B24-16 共 3 行；B24-15 并入 B24-12），第 11 章相关 31 行（改 19 行，新增 B11-18 至 B11-28、X-31 共 12 行），第 19 章相关 25 行。
- 2026-10-02　核对第 3、9、10、13 章所用数字，修订 83 行（改 40 行，新增 43 行：B03-15 至 B03-25、B09-09 至 B09-15、B10-20 至 B10-26、B13-16 至 B13-31、C-34、C-35）。
- 2026-10-03　核对第 14、15、17、18、20、25 章所用数字，修订 112 行（改 60 行，新增 52 行）。
- 2026-10-04　核对第 4、5、6、7、8、16 章所用数字，修订 124 行（改 63 行，新增 61 行：B04-10 至 B04-18、B05-07 至 B05-14、B06-20 至 B06-33、B07-20 至 B07-22、B08-05 至 B08-13、B16-09 至 B16-18、C-38 至 C-42、X-36 至 X-38）；SWE-MiniSandbox 的两行并入 B08-01、B08-09，DeepSWE 一行并入 B17-09；第 6 章新增行因 B06-18、B06-19 已占用，自 B06-20 起编号。
- 2026-10-05　核对第 21、22、26、27 章所用数字，修订 149 行（改 64 行，新增 84 行：B21-19 至 B21-27、B22-44 至 B22-73、B26-17 至 B26-26、B27-08 至 B27-29、C-43 至 C-49、X-39 至 X-44；删除 X-08）；腾讯生命周期、Coze、veFaaS、AgentBay、Perplexity 的重复行并入 B21-23 至 B21-27。核对第 12、23 章所用数字，修订 40 行（改 19 行：B11-09、B12-01 至 B12-04、B12-06、B12-07、B16-02、B16-15、B23-01 至 B23-10；新增 21 行：B12-08 至 B12-15、B23-11 至 B23-19、C-50 至 C-53；另增链接定义 [cordon]、[acrfence]、[sagallm]）。核对第 1、2、28 章所用数字，修订 124 行（改 111 行，含 B02-10 的 72% 措辞统一为"含明确的思维链理由"、B23-01 与 B23-11 的 TC260 条款写法统一为"第 8 章 n）项第 1）条"；新增 13 行：B01-05 至 B01-08、B02-12 至 B02-14、B28-03、C-54、C-55、X-45 至 X-47）。全书统一与附录 C、D 配套修订 70 行（改 48 行，包括 B10-14 的"长尾数百秒"节号改为 §3.1、"约每十次迭代一次"写明为环境超时，B16-14 补 Prime 文件系统检查点，C-02、B11-03 补提交日期 08-26，C-40 据 Cua Cloud Fleets 页复核 pool/claim，B23-12 的 TC260 条款写法改为"第 7 章 d）项"，附录 D 引用的 37 行使用章节补"附录 D"；新增 22 行：B03-26、B06-34 至 B06-37、B08-14 至 B08-19、B24-17 至 B24-19、B25-20、BC-01 至 BC-07；另增"附录专用数字"分区）。各章溯源表中 66 处待登记数字改为既有编号，本表未增改。
- 2026-10-06　补充核对修订 43 行（改 27 行：B01-03、X-44、B07-06、B05-13、B17-12、B13-11、B25-10、B24-12、B24-10、B12-15、B02-03、B21-22、B23-02、B22-60、B19-26、C-27、B27-14、B27-15、C-29、B19-18、B04-05、B04-17、B06-19、X-26、B20-06、B20-07、X-27；新增 16 行：B07-23、B21-28、B28-04、B26-28、C-56、C-57、C-58、X-48 至 X-56）。B03-12、B13-13、B21-09 回原文复核，备注已更新。MobileGym（B07-07、B20-29）的会议状态改为"预印本；会议录用情况未核实"；B24-01 写明提交日期为二手旁证；X-02 的来源改为"来源不明的摘要式转述"；B03-01 按钜亨网原文更新。新增 B11-29（DeltaBox 写放大与评测环境），B11-26 补"1–5 次抢占"，各章溯源表的待登记标记全部改为编号。来源与核对状态的表述统一为面向读者的写法。冲突登记止于 C-58，"不应引用"止于 X-56。
