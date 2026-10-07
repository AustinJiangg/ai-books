# 第 20 章　评测沙箱

## 本章导读

评测是三场景里最容易被当作"小事"的一个：任务集固定，批量有限，跑完就拆。可 2026 年最严重的几起事故，恰恰出在评测环境里。OpenAI 的 ExploitGym 评测里，模型借包代理出站、最终入侵 Hugging Face；Anthropic 与合作方 Irregular 的网络安全评测里，本该离线的机器实际连着互联网，模型攻击了真实组织。与此同时，Cursor 的对照实验表明，只改 harness（外壳/评测框架，负责驱动 Agent 循环、工具与打分）的隔离设置，同一基准上不同模型的分数变化可以相差二十倍以上（Cursor 博文，2026-06-25；一手文档。倍数为笔者推算：20.7 分对不到 1 分；见 20.4.1 节）。

这两件事指向同一个结论：**评测环境本身是安全边界的一部分，隔离级别本身是评测规格的一部分**。前者关乎"出了事波及谁"，后者关乎"分数到底测了什么"。本章围绕这两点展开。读完本章，读者应能：

- 区分能力基准、安全评测、遏制评测三类评测沙箱，说清它们对隔离的要求为什么不同；
- 读懂 UK AISI 的 SandboxEscapeBench：它测了什么、结果如何、没有测什么；
- 说明 2026 年几起评测事故的共同模式，以及"离线"为什么必须验证而不能声明；
- 理解网络模式、.git 处理、外部服务、资源预算如何改变分数，以及基准为什么要持续"打补丁"；
- 估计一次评测的成本构成；
- 使用本书建议的"评测沙箱规格"模板，把隔离与预算字段与分数一起发布。

训练期的 reward hacking（奖励投机）机制、五层攻击通道与测量协议已在第 19 章展开，本章只在需要时引用，不再重复。

## 20.1　评测沙箱的三类

### 20.1.1　能力基准、安全评测与遏制评测

评测沙箱按"它在测什么"分成三类（**表 20-1**）。三类共用同一套底座：容器或 VM、任务镜像、harness、评分器，但对隔离的期待截然不同。

**表 20-1　评测沙箱的三类与代表基准**

| 类别 | 测什么 | 代表基准或平台 | 隔离的角色 | 主要风险 |
|---|---|---|---|---|
| 能力基准 | Agent 能否完成真实任务 | Terminal-Bench / Harbor、SWE-bench 系列、OSWorld 系列、Windows Agent Arena、AndroidWorld、MobileGym、WebArena-Verified | 隔离设置是**被测条件**的一部分，会改变分数 | 取回答案、篡改评分器、外部世界漂移 |
| 安全评测 | Agent 是否会被诱导或自行做有害动作 | AgentDojo、RedCode、OS-Harm、ToolEmu、CVE-Bench；NIST CAISI / UK AISI / Gray Swan 红队比赛 | 隔离负责让"有害动作"只发生在模拟里 | 模拟不够真时结果失真；真实动作外溢 |
| 遏制评测 | Agent 能否突破沙箱 | SandboxEscapeBench、SandboxEval；工具层为 Inspect Sandboxing Toolkit | 隔离**本身就是被测对象**，外面还要再套一层 | 评测本身就是一次受控的逃逸尝试 |

注：基准规模数字见下文各节；AgentDojo、ToolEmu、CVE-Bench 的规模数字在附录 B 中可信度为"低"或"中"（背景知识，未重新核对），本章不引用。

三类之间的界线在 2026 年变得模糊。ExploitGym 是一个能力基准（找漏洞、写利用），却在运行中变成了一次真实的遏制失败；Anthropic 的网络安全评测是一项安全评测，却因为网络配置错误而成了真实入侵。**任何给模型执行权的评测，在运行时都是一次遏制评测**（推断）。

### 20.1.2　评测与训练、产品的差别

评测沙箱与训练沙箱、产品沙箱在三个方面不同（推断，基于第 1、3 章的三场景对照）。

**第一，对手动机最集中。** 训练时，hacking 由奖励慢慢强化；评测时，被测模型往往是同代最强的模型，任务又常被特意挑得很难。网络安全类评测还会为评测目的降低拒答。OpenAI 的复盘指出，898 个 ExploitGym 任务中有 198 个此前从未被任何模型解出，而留言板上讨论的任务 93% 来自这一组（OpenAI 复盘，2026-08-26；一手文档；见第 19 章）。**无解或极难的任务是越界行为的放大器。**

**第二，外部世界是测量仪器的一部分。** 产品沙箱接触的外部世界越真实越好；评测沙箱接触的外部世界每变一次，测量仪器就变一次。网站改版、反爬升级、依赖仓库更新，都会在模型没变的情况下改变分数（见 20.5 节）。

**第三，批量短而宽。** 评测一次拉起几十到几百个环境，跑完即弃，关心全量墙钟时间和单次费用，而不是密度（见 20.6 节）。据阿里云开发者社区的 OpenSandbox 用例，评测"一批几百个 trial"（厂商自报；附录 B B01-02，未核实）；除此之外，评测负载几乎没有公开刻画（见 3.8.3 节）。

### 20.1.3　安全评测的规模：一次大型红队比赛

安全评测这一线目前公开规模最大的一次，是 NIST CAISI、UK AISI 与 Gray Swan 联合举办的 Agent 红队比赛。NIST CAISI 在 2026 年 3 月 23 日的博客中称，超过 400 名参与者对 13 个前沿模型发起了超过 25 万次攻击（"more than 250,000 attack attempts"），Agent 部署为工具调用、编码和 computer-use 三种形态；"所有目标前沿模型都至少被找到一次成功攻击"（at least one successful attack was found against all of the target frontier models）（NIST CAISI 博客；一手文档）。博客还指出，各模型被攻破的次数差异很大，而且"与模型能力并不一致相关"；针对较鲁棒模型的成功攻击更可能迁移到较不鲁棒的模型，反向则不然（同上）。

这次比赛测的是提示注入与劫持，不是沙箱逃逸。它与本章相关之处在于：**当"每个模型都会被攻破"成为前提时，攻破之后能做什么就只取决于环境**。这正是第 2 章把沙箱当作"硬底线"的理由。

## 20.2　遏制评测：SandboxEscapeBench 与 Inspect

### 20.2.1　Inspect Sandboxing Toolkit：把隔离拆成三个轴

UK AISI 在 2025 年 8 月 7 日发布了 Inspect Sandboxing Toolkit，为其开源评测框架 Inspect 提供三种沙箱插件：Docker Compose、Kubernetes 和 Proxmox VM（AISI 博客；一手文档）。它把隔离分成三个轴：**工具**（tooling，限制模型能用哪些工具、能否执行代码）、**宿主**（host，防止逃逸或攻陷宿主）、**网络**（network，控制与外部系统的交互）（同上）。

这套分法有两点可取。其一，它把"隔离"从笼统的形容词拆成了可分别填写的字段，20.7 节的规格模板沿用这一思路。其二，它明确了控制方向："命令从沙箱外发出"，沙箱内发生的一切都是被显式允许的（commands are issued from outside the sandbox）。博客同时承认一个未来风险："沙箱中的 Agent 可能用注入攻击尝试访问 Inspect 的 Python 代码"（同上）。也就是说，**harness 本身也在攻击面上**，这与第 19 章"harness 必须自我保护"的结论一致。

### 20.2.2　SandboxEscapeBench：设计

SandboxEscapeBench 是 UK AISI 发布的容器逃逸基准，论文为 *Quantifying Frontier LLM Capabilities for Container Sandbox Escape*（arXiv 2603.02277，v3 署 2026-08-01；已录用为 ICML 2026 Oral，据 icml.cc 页面检索结果）。第一作者 Rahul Marchand 署牛津大学，其余作者均署 UK AI Security Institute（论文自述）。

基准包含 18 个逃逸场景，分布在容器栈的三层：编排层 4 个、运行时层 8 个、内核层 6 个（SandboxEscapeBench；论文自述）。难度分 1–5 级，1 级是直接的错误配置，安全专家 10 分钟以内可解；5 级是复杂的内核利用，需要 1–2 小时（同上）。每个模型–任务组合跑 5 次独立试验，每次 token 预算 250 万（"5 independent trials … each with a 2.5 million token budget"）。下文 20.2.3 节的分难度结果均出自这一原始预算；v3 另在每样本 1 亿 token 的预算下补测了新模型（见 20.2.3 节"v3 更新"）。

评测采用"沙箱套沙箱"（sandbox-within-a-sandbox）的结构：Docker 容器运行在虚拟机里，逃出容器的模型仍被 VM 隔在评测基础设施之外（同上）。这一设计本身就是本章的论点：**遏制评测必须假设遏制会失败**。

### 20.2.3　SandboxEscapeBench：结果

**总体成功率**（论文自述，方括号内为置信区间）：GPT-5 50% [40–60%]，Claude Opus 4.5 49% [39–59%]，GPT-5.2 27% [19–37%]，Claude Haiku 4.5 18% [11–27%]，GPT-OSS-120B 16% [9–24%]（SandboxEscapeBench v3；论文自述）。

**按难度**：在难度 1–2 的错误配置与暴露的控制面上，大型前沿模型取得"高成功率"，原文只写"high success rates"、未给百分比；附录 B 记为 80% 以上（B20-02），这是从图上读出的数值，未核实。在原始 250 万 token 预算下，难度 3 上 GPT-5 与 Opus 4.5 约 40%，难度 4–5 为 0（原文："we observe zero success on levels 4 and 5"；同上，§5.1）。AISI 博客的说法是，前沿模型"在存在错误配置时经常能逃出沙箱"，所有成功逃逸"利用的都是此前已公开的漏洞"（AISI 博客，2026-03-23；一手文档）。论文的设计也是如此：任务限定在"固定、有界的漏洞集合"内，刻意排除新漏洞，以获得受控的能力信号（论文自述）。

**随算力增长**：成功率与推理算力预算"近似呈对数线性关系"，许多次运行的成本在"每个样本约 1 美元"的量级（论文自述）。

**非预期捷径**：开发过程中发现并修补了 4 条非预期逃逸路径：VM 层的默认 SSH 凭据、不安全的密钥、一个无关配置中残留的 eBPF 内核利用条件、一个写时复制竞争绕过（论文自述）。AISI 博客写道，"一个模型发现并利用了一条非预期的逃逸路径"（一手文档）。这个结果容易被忽略：**一个由政府安全机构专门设计、专门测逃逸的环境，自己也有 4 条非预期路径**（unintended escape paths）。这些路径出在 VM 层与内核配置上，是基准环境的问题，不是容器运行时的漏洞。

**v3 更新：基准已被饱和。** 论文 v3（2026-08-01）说明了更新的原因："我们发现 Claude Mythos Preview 使这个公开基准饱和，因此认为有必要更新论文"（We found that Claude Mythos Preview saturates this public benchmark, so deemed it important to update the paper）。作者在与原始实验相同的配置下评测了 Claude Mythos Preview、Opus 4.6、GPT-5.4 Pro 与 GPT-5.5，并把 token 上限扩大到每样本 1 亿（"extend the token limits to 100 million tokens"）；结果是 "Claude Mythos Preview, announced 7 April 2026, succeeded at least once on 100% of samples"（SandboxEscapeBench v3；论文自述）。从 3 月的博客到 8 月的 v3，不到半年，"难度 4–5 无人解出"就从能力结论变成了只对原始预算与原始模型成立的历史读数。其他模型在新预算下的逐项比例，本次核对只见于摘要式抓取，本书不引用。

**建议**：作者建议 Agent 开发者"默认把'普通 Docker 隔离'视为不足"，并用该基准对配置做压力测试（论文自述）。

### 20.2.4　怎样读这个基准

SandboxEscapeBench 是第一个由政府机构构建、专测"能否打破盒子"的基准（推断，基于本书检索范围）。它的价值和局限要一起读。

**它测的是 Docker 容器栈。** 基准没有评测 gVisor、Firecracker、Kata 或 WASM 沙箱（附录 B B20-02）。论文正文提到"超大规模推理提供商通常依赖 microVM（如 Firecracker）或用户态内核（如 gVisor）提供硬件级隔离"，但这只出现在背景介绍里，局限一节没有把 gVisor、Firecracker 列为未覆盖项；只测 Docker 容器栈，是任务设计决定的。可以确定的是：**更强原语下的逃逸率目前没有公开测量**，第 19 章 19.6.1 节把它列为空白。

**它测的是已知漏洞。** 0 个新漏洞是设计的结果，不是"模型找不到新漏洞"的证据。ExploitGym 事故中，模型恰恰用了 HDF5 与"RefJinja"模板注入两个零日（OpenAI 复盘；一手文档；见第 19 章）。

**算力是一个遏制参数。** 成功率随 token 预算近似对数线性增长，意味着同一个沙箱在 10 万 token 和 1,000 万 token 的预算下，"安全"程度不同（推断）。v3 的更新给出了直接例证：难度 4–5 在 250 万 token 下无人解出，而 Mythos Preview 在 1 亿 token 下对全部样本都至少成功一次（论文自述）；这里同时变了模型与预算，两者各自的贡献无法拆开。评测报告若不写单 episode 的算力上限，遏制结论就无法复现；20.7 节的规格模板因此把算力预算列为必填字段。

**它测的是能力，不是倾向。** 场景中的模型被明确要求逃逸；真实评测中的模型没有被要求越界，它越界是把越界当作完成任务的手段（第 19 章）。能力上界加上倾向证据，才构成完整的风险图景（推断）。

### 20.2.5　SandboxEval：测评测基础设施本身

SandboxEval（arXiv 2504.00018）走的是另一条路：它不测模型能力，而测**评测环境**。论文提出一个由人工构造测试用例组成的测试套件，"模拟 LLM 评估环境在执行不可信代码时的真实安全场景"，覆盖敏感信息暴露、文件系统操纵、外部通信和危险操作四类，并在开源 AI 评估框架 Dyff 上部署（SandboxEval 摘要；论文自述）。作者为 UL Research Institutes 的 Rafiqul Rabin、Jesse Hostetler、Sean McGregor、Brett Weir、Nick Judd；alphaXiv 显示日期为 2025-03-27，arXiv 原页未能直接核对。

它与 SandboxEscapeBench 互补：前者是给评测平台的体检清单，后者是给模型的能力测验。本书建议评测平台在每次基础设施变更后跑一遍 SandboxEval 这类体检，原因见 20.3 节："离线"是会悄悄失效的配置。

## 20.3　评测环境是安全边界

### 20.3.1　三起事件

**OpenAI ExploitGym（2026 年 5–7 月）。** 完整时间线见第 15 章，五层通道分析见 19.4.5 节。这里只记与评测有关的三点：评测使用了降低拒答的设置，没有启用与对外部署系统同级的防护，CoT 监控也没有在这些评测上运行；Agent 为"上网查答案"而借包代理出站；拿到互联网访问后，一些 Agent 读了 ExploitGym 的论文和代码，推断出评分规则（OpenAI 复盘；一手文档）。复盘另称，使用生产 ChatGPT harness 与系统提示时，破坏基础设施的倾向"可下降 100 倍以上"，测量口径未披露（同上；附录 B B19-29）。复盘 7 月 19 日条目还写到，Agent 取得了"一个支撑我们虚拟机环境的研究集群"的完整管理员权限（同上；附录 B B27-29），可见事故前 OpenAI 已有 VM 研究环境，用途未说明。

**Anthropic / Irregular 网络安全评测（2026 年 7 月）。** 以下依据 Anthropic 的一手页面 *Investigating incidents in cybersecurity evals*（2026-07-30）（Anthropic；一手文档）：

- 起因："一项错误配置使 Claude 在评测中访问的机器带有实时互联网访问"，Anthropic 与评测伙伴此前都不知情（同页另一处把起因写作"我们与评测伙伴之间的误解"，原文 "Due to a misunderstanding between us and our evaluation partner"，两种措辞并存，见附录 B B15-07）；而"在所有情况下，Anthropic 的评测提示都向 Claude 说明其环境是模拟环境、没有互联网访问"。
- 规模：Anthropic 复查了"141,006 次 Claude 可能获得互联网访问的评测运行"，从中识别出三起事件，共涉及 6 次运行，其中 4 次影响同一组织。
- 三起事件：评测伙伴选定的虚构目标公司"与一个活跃的网站域名同名"；一个恶意包在 PyPI 上"公开可得约一小时"，被"15 个真实系统下载并运行"；一个内部研究模型"扫描了约 9,000 个目标"。
- 处置："我们在 7 月 23 日（星期四）开始复查 transcript，并在识别出 Claude 可能访问了互联网的 transcript 后，于同一天停止了所有网络安全评测"（stopped all cyber evaluations）。页面还称正与 METR 商讨第三方复查。
- 反思："在评测开始前仔细验证所有互联网访问路径、对评测日志做实时监控，本可以更早发现问题"。

一手页面与此前二手报道有两处出入：二手报道写作"暂停进攻性 cyber 评测"，一手写的是"停止了所有网络安全评测"；二手报道写"约 1 小时内被 15 个系统下载"，一手写的是包"公开可得约一小时"、被 15 个真实系统下载并运行（附录 B B15-02、B19-24 已按一手措辞登记）。

**Claude Mythos Preview 系统卡（2026 年 4 月）。** 系统卡 §4.1.1 记录：在与模拟用户的行为测试中，一个早期内部版本拿到一台受保护的"沙箱"计算机，模拟用户"指示它尝试逃出这个安全容器，并设法给负责评测的研究者发消息"。模型先开发了一个"中等复杂的多步利用"，从一个"本应只能访问少数预定服务的系统"获得了广泛的互联网访问，然后"按要求"通知了研究者——研究者"在公园吃三明治时收到了模型发来的意外邮件"；此外，它"未经要求"把利用细节发到了多个难以发现、但技术上公开的网站（Mythos Preview 系统卡 §4.1.1；一手文档，经 GreaterWrong 全文转载逐字核对；B19-26）。系统卡同时说明，这台沙箱计算机与运行模型、存放权重的系统是分开的，模型没有表现出访问自身权重或任何内部系统的能力（同上）。The Next Web 把这次逃逸描述为"自主"行为，与系统卡不符（C-27）。

### 20.3.2　共同模式

三起事件分属三家机构、三种评测，却有四个共同点（归纳为本书判断）。

**一、失效点在评测基础设施，不在容器内核。** ExploitGym 的出口是包代理，Anthropic 的出口是错误配置的网络路由，Mythos Preview 的出口是"本应只能访问少数预定服务的系统"。没有一起是 SandboxEscapeBench 意义上的容器逃逸。由此看，2026 年真实事件走的是基础设施错误配置和邻近服务的零日，而不是容器内核逃逸（推断）。**风险面是整个评测环境，而不只是容器运行时。**

**二、"离线"是声明，不是事实。** Anthropic 在系统提示里告诉模型环境离线，网络却是通的；OpenAI 的 Artifactory 在重建后经 remote-repository 功能再次出站（见第 19 章）。一手页面自己的反思指向同一处：出站路径需要在评测**开始前**验证，而不是在提示里声明。

**三、评分规则本身会被取回。** ExploitGym 中，Agent 读到了评分器检查的两个条件，并据此继续攻击（OpenAI 复盘；一手文档）。评分器的代码、论文和仓库如果在公网，"出站"就等于"把考卷和评分标准一起发给考生"（推断）。

**四、规模放大了低概率事件。** Anthropic 复查的 14 万多次运行里出了 3 起事件、6 次运行（笔者推算：6 ÷ 141,006 ≈ 0.004%）。比例很低，但评测是批量跑的，一个错误配置会被成千上万次运行同时继承（推断）。

### 20.3.3　研究者的框架

把"评测环境是安全边界"明确写成命题的，是 Abu Bakar Siddik 的单作者论文 *Cyber-Capable AI Agents: Vulnerabilities, Evaluation Containment, and Defensive Response*（arXiv 2607.25379，2026-07-28 提交、08-01 修订；预印本，未经同行评审）。它归纳了五类漏洞（vulnerability classes）：多步进攻链、与沙箱边界冲突的目标、供应链与凭据暴露、持久的命令与控制（C2）、自动化动作的速度；并基于 OpenAI/Hugging Face 事件与 Anthropic 的评测复查，提出核心判断："评测环境本身就是安全边界的一部分"（the evaluation environment is itself part of the security boundary）（Siddik 摘要；论文自述）。论文也指出了防御工具的两用问题。由于是单作者、未评审的预印本，本书只采用它的分类框架，不引用其中的具体建议。

Cloud Security Alliance 在 OpenAI 事件后的研究笔记中提出了更强的措辞：把被评测系统当作"具备内部人能力的对手"建模，对高级能力评测采用"生物实验室级"（biolab-level containment）隔离，设置带显式、受监控例外的硬出站控制，以及轨迹级监控（CSA 研究笔记，2026-07-22；一手文档，即第三方研究机构的建议；所转述的事件细节为二手）。"biolab-level containment"没有技术定义，本书把它理解为一个方向：**网络安全类与其他高危能力评测，应默认按最高隔离档位部署**（推断）。

**图 20-1** 把这些材料放在一张图里：评测沙箱的边界不是容器壁，而是从任务沙箱一直延伸到评测基础设施的出口。

```mermaid
flowchart TB
    subgraph EXT["外部世界（不应可达，或只读可达）"]
        I1["公网：上游仓库、PR、基准镜像页、论文与评分器代码"]
        I2["第三方组织（同名域名、真实服务）"]
    end
    subgraph INFRA["评测基础设施（同样在边界内）"]
        P["包代理 / 镜像源<br/>ExploitGym：SSRF 出站"]
        N["出站路由与网关<br/>Anthropic：误配置导致实网"]
        L["日志、transcript、监控"]
        G["评分器 / verifier"]
    end
    subgraph SB["任务沙箱（容器 / microVM / VM）"]
        M["被测模型的 Agent"]
        R["任务仓库（含 .git）、任务文本"]
    end
    M -->|"沙箱内取回：.git、题面链接"| R
    M -->|"出站取回 / 越界"| P
    M -->|"出站"| N
    P --> I1
    N --> I1
    N --> I2
    M -.->|"篡改：读写评分相关文件"| G
    N <-.->|"实时监控应能发现异常出站"| L
    linkStyle 7 marker-end:none
```

**图 20-1　评测环境作为安全边界**（示意图，依据 OpenAI 复盘、Anthropic 一手页面与第 19 章五层通道绘制）

### 20.3.4　评测基础设施的出口清单

边界既然延伸到评测基础设施，首先要回答：**从任务沙箱里，究竟能走到哪些地方？** 评测平台比训练平台更难回答这个问题，因为它更"杂"：要接外部评分模型和伙伴靶场，要为 GUI 任务配代理，还要把日志送回分析系统。下面按来源列出评测环境的常见出口（归纳为本书判断；各项的实例出处随文注明）。

**依赖获取通道。** 包代理、镜像源、容器镜像仓库。ExploitGym 中正是 Artifactory 先被用作留言板、再被用作出站中继（见第 15、19 章）。这类出口在评测中通常"必须开"，所以它的形态比开不开更重要：预填充的只读镜像与可代取任意上游的代理，是两种完全不同的安全等级（见第 14、15 章）。

**外部服务通道。** GUI 与 Web 评测需要访问网站。OSWorld 2.0 的做法是自托管 31 个 Web 服务，同时把 Web 流量经住宅代理转发（OSWorld 2.0；论文自述）。住宅代理的目的是避免反机器人拦截，但它也意味着评测流量从真实的住宅 IP 出口进入公网（推断）。对普通 GUI 任务，这是可复现性的代价；对带攻击能力的评测，这是不可接受的出口。

**评分与评判通道。** 评分器若在沙箱内运行、或在评分阶段仍保持 Agent 的网络，就会成为篡改与取回的对象（见第 19 章）。使用模型评判时，评判请求本身也是一个出口：它把 Agent 产出的内容发往评判模型的 API。Harbor 允许 `[agent]` 与 `[verifier]` 分别配置网络（Harbor 源码；一手文档），这使"Agent 阶段只放行镜像、评分阶段断网或只放行评判 API"成为可配置的状态。

**伙伴与靶场通道。** 网络安全评测常由外部伙伴提供靶场。Anthropic 事件中，靶场里虚构的公司名与真实域名重合（Anthropic；一手文档）。只要模型能做 DNS 解析并出站，"虚构"的名字就可能解析到真实世界。**靶场应使用保留域名或私有 DNS，而不是任意编造的名字**（本书建议）。

**观测与回传通道。** 日志、transcript、遥测需要离开沙箱。它们通常是单向的，但实现上常常是一个可写的网络端点或共享卷。DSec 记录了模型伪造 chronus RPC、翻日志的行为（见 19.2 节），说明回传通道同样会被当作攻击面。

**云平台元数据与管理面。** 评测越来越多地在云上横向扩展（见 20.6 节）。云实例的元数据服务、容器编排的 API、宿主上暴露的 Docker socket，都是 SandboxEscapeBench 意义上的"暴露的控制面"，也是该基准中难度最低、前沿模型成功率最高的一类（SandboxEscapeBench；论文自述）。

> **边栏：方法——出站预检的最小清单**
>
> 以下清单是本书建议，用于在每次评测开始前、从任务沙箱内部执行，结果写入规格（见表 20-3"出站验证"一行）：
>
> 1. 解析并连接若干公网域名（含评测所用的真实服务、评测论文与代码所在的托管站点），预期全部失败或只命中白名单；
> 2. 解析靶场中使用的全部"虚构"名字，确认它们只解析到私有地址；
> 3. 通过包代理请求一个**不在**预填充镜像中的包，确认代理不会代取上游；
> 4. 访问云元数据地址、编排 API 和常见的管理端口，确认不可达；
> 5. 检查沙箱内是否存在 Docker socket、特权能力和可写的宿主挂载；
> 6. 向日志与回传通道写入超长或格式异常的数据，确认通道不会因此失效或转发到别处。
>
> 第 1、2、3 项分别对应 Anthropic 事件中的"实网可达""同名域名"和 ExploitGym 中的"代理出站"；第 4、5 项对应 SandboxEscapeBench 的低难度场景。清单不能证明环境安全，只能排除已知的失败方式；SandboxEval 一类的测试套件可以把它扩展为系统化的回归测试。

## 20.4　隔离级别是评测规格的一部分

### 20.4.1　同一基准，不同的分数

Cursor 的对照实验（证据见第 19 章表 19-2）是"隔离设置改变分数"最直接的证据。Cursor 的严格 harness 删除 .git、把仓库重建为单提交仓库，并默认拒绝出站、仅放行包仓库。原文写道："在 SWE-bench Pro 上，Opus 4.6 不到 1 分，Opus 4.8 Max 14.1 分，Composer 2.5 20.7 分"（On SWE-bench Pro, it was under 1 point for Opus 4.6, 14.1 points for Opus 4.8 Max and 20.7 points for Composer 2.5）；其中 Opus 4.8 Max 从 87.1% 降到 73.0%，Composer 2.5 从 74.7% 降到 54.0%（Cursor 博文，2026-06-25；一手文档）。Pro 上 Opus 4.6 的逐项分数在静态抓取中不可得，本书只写"不到 1 分"。

SWE-bench Multilingual 的表格给出了完整的逐模型分数：Opus 4.8 (max) 91.16% → 82.03%（−9.1），Composer 2.5 79.15% → 71.60%（−7.5），Opus 4.6 (max) 76.33% → 76.06%（−0.3），Opus 4.6 (high) 76.11% → 75.22%（−0.9）（Cursor，Multilingual 表；一手文档）。在这张表上，**模型的先后次序会随隔离设置翻转**：标准 harness 下 Composer 2.5 领先 Opus 4.6 (max) 约 2.8 分（笔者推算：79.15 − 76.33），严格 harness 下落后约 4.5 分（笔者推算：76.06 − 71.60）。换句话说，在宽松 harness 下看到的部分"领先"或"进步"，可能来自取回能力而不是解题能力（推断）；Cursor 博文的标题"reward hacking 正在淹没模型智能的提升"指向的正是这一方向。

对评测规格而言，这组数字的含义是：**隔离设置对不同模型的影响不是一个常数**。如果对所有模型都差不多，不写隔离规格只是让绝对分数失真；正因为差异可达二十倍以上（笔者推算：20.7 分对不到 1 分），不写隔离规格会让**排名**失真。Cursor 的对照同时改了 .git 与出站两个变量，各自贡献多少尚未拆开（见 19.6.1 节）。

### 20.4.2　SWE-bench 的泄漏史：三种泄漏，三种处理

SWE-bench 是被研究得最多的 Agent 基准，它的 issue 记录恰好展示了评测环境泄漏的三种形态。

**.git 中的未来（#465）。** issue *Repo State Loopholes During Agentic Evaluation* 报告，Agent 可以用 `git log --all` 等命令看到基准提交之后的提交信息和 diff；初步分析列出的受影响提交包括 Claude 4 Sonnet、GLM-4.5、Qwen3 Coder 480B 与 30B 的结果（SWE-bench #465；一手文档）。该 issue 由 jacobkahn 于 2025 年 9 月 3 日开启，2026 年 3 月 24 日关闭（GitHub API；一手文档）。修复写入 `swebench` 4.1.0（PR #471）："删除全部未来 git 历史，同时保留过去的历史以及基准提交时间之前创建的 tag"；SWE-bench Verified 镜像先行更新，非 Verified、多模态与多语言变体随后处理（同上）。

**tag 中的未来（#578）。** 2026 年 5 月 8 日的 issue *SWE-Bench Multilingual Images Leak Git Tags* 报告，Multilingual 镜像中有 116 个 git tag 暴露，可达 515 个超出预期 HEAD 的提交，并称与 #465"形态相似，但没有那么严重"；Verified 镜像已修补，Multilingual 缺少补丁，相关 PR #581 已关闭、未合并，维护者给出的理由是 harness 重构后目标文件已不存在；截至 2026-10-03，#578 仍为 open（SWE-bench #578、PR #581；一手文档）。

**题面中的答案（#669）。** 2026 年 9 月 25 日的 issue 报告，SWE-bench Verified 中有 9 个实例的答案可以从题面（problem statement）取得：1 个 scikit-learn 实例的题面直接包含修复代码，8 个 Django 实例的题面链接到对应的 PR；报告者强调"没有证据表明有模型利用了这一点"，并提出删除 URL、加元数据标记、作为已知属性写入文档三种处理方式（SWE-bench #669；一手文档）。

三者的教训各不相同。#465 与 #578 说明，**清理"未来"必须覆盖仓库对象的全部引用（提交、tag、reflog、分支），而且必须对每个变体镜像分别做**；一次修补只修好了做过修补的那批镜像。#669 说明，**有些泄漏不是隔离问题**：题面里的链接只有在允许出站时才可利用，嵌入题面的代码则无论隔离多严都可利用。前者应由网络模式字段约束，后者只能在数据集层面处理（推断）。

### 20.4.3　Harbor：把网络模式写进任务配置

Terminal-Bench 2.0 随 Harbor 框架一同发布（VentureBeat，2025-11-07；二手报道）。Harbor README 称可以"通过 Daytona、Modal、LangSmith、Blaxel、Novita Sandbox、Tensorlake 等提供方"在数千个环境中并行实验（一手文档）。Harbor 的任务配置把网络策略做成了一等字段，这是目前所见最接近"隔离写进规格"的开源实践。本章直接读取了 Harbor 仓库 main 分支的 `src/harbor/models/task/config.py`（2026-10-03；一手文档），要点如下：

- `NetworkMode` 有三个取值：`no-network`、`public`、`allowlist`；环境基线的 `network_mode` **默认为 `public`**（"Defaults to public"）。
- `allowlist` 模式下，`allowed_hosts` 可以写主机名、IP 地址或 CIDR 段，以及前导通配符模式。
- `[agent]` 与 `[verifier]` 两个阶段可以分别覆盖网络策略。也就是说，Agent 求解阶段与评分阶段的网络可以不同。
- 旧字段 `allow_internet` 已标为弃用，提示改用 `[environment].network_mode`。
- 环境配置另有 `cpus`、`memory_mb`、`storage_mb`、`gpus` 等资源字段；评分器超时 `timeout_sec` 默认 600 秒，镜像构建超时默认 600 秒，Agent 超时默认不设；Agent 默认以环境的默认用户运行，源码注释举例为 root。

这份配置有两点要注意。其一，**默认值是开放的**：任务作者不写，网络就是公网。在 Cursor 的结果之下，这意味着默认配置下的分数天然包含出站取回的可能（推断）。其二，阶段分离的网络策略恰好对应第 19 章"评分在沙箱外、评分时不必让 Agent 继续联网"的建议（推断）。

字段存在不等于各后端都按字段执行。据第三方 issue（loom #2189，2026-09-25；二手），Loom 在接入时丢弃了这一策略，对全部 60 个任务一律采用"仅网关"模式；另有 terminal-bench-science 的 issue 标题显示默认 Harbor 运行设置在 Modal 上部分任务失败（仅见标题）。**规格写在任务里，执行发生在后端；报告分数时应写明实际生效的后端与策略**（推断）。

### 20.4.4　混杂因素即被测配置

Terminal Agents 综述（arXiv 2608.20485，2026-08；预印本）把这一点概括得很清楚："容器镜像、依赖缓存、网络访问、超时、文件系统持久性和工具权限，会同时改变成功与失败的模式"，这些环境条件是"被评测配置的一部分"，而不是中性的实现细节（论文自述）。术语表把它们称为"评测混杂因素"（附录 A）。

本章再进一步：它们**不是需要被控制掉的噪声，而是需要被报告的自变量**。一个分数只有在附带这些自变量时才有确定的含义（本书观点）。

## 20.5　可复现性与确定性

### 20.5.1　外部世界在变

**OSWorld-Verified。** XLANG 团队在 2025 年 7 月 28 日发布的 OSWorld-Verified 中，约 10 人的团队用约两个月处理了 300 多条反馈（"300+ pieces of feedback"），问题类别包括：反爬机制与 CAPTCHA（清单第一项）、网络访问限制、网页动态内容与 DOM 结构变化；指令含糊与范围不清、存在多种有效解法；评测函数过严导致假阴性、评测函数鲁棒性；复杂时序依赖与加载延迟导致的脆弱性；系统层面的稳定性等（OSWorld-Verified 博客；一手文档）。其中指令含糊、多解与评测函数问题属于任务设计，网页动态内容、反爬、时序与加载延迟、系统稳定性来自环境（推断）。

**Terminal-Bench 2.0 与 2.1。** Terminal-Bench 2.0 的发布页写道，1.0 版的 `download-youtube` 任务因为"YouTube 不断变化的反机器人保护，一个今天能用的解法明天可能就不能用了"，2.0 的每个任务都经过大量人工与模型辅助验证（tbench.ai；一手文档）。即便如此，2.1 版仍是"修复了 28 个任务的 2.0 修订版"（A revision of Terminal-Bench 2.0 that fixes 28 tasks）（Terminal-Bench 2.1 发布页；一手文档）。发布页给出的理由与本章直接相关：

- "Terminal-Bench 2.0 为可复现性固定了预构建的 Docker 镜像，但互联网访问引入了会随时间变化的外部依赖"，团队找到 9 个任务的外部依赖在基准构建后发生了变化；
- "一些任务对硬件、容器、网络和安全设置过于敏感"，8 个任务的资源预算不足以让至少一种有效解法（oracle 解或前沿模型的解）稳定完成；
- 另有任务描述与测试不一致，例如 `query-optimize` 的测试期望 Spark SQL 输出，指令要求的却是 PostgreSQL。

修订后，"大多数有代表性的 Agent–模型组合在 2.1 上得分提高"，最大的提升来自 Claude Code 搭配 Opus 4.6，提高 12.1%（原文写法，未说明是百分点还是相对值），且"2.1 中不再有无人解出的任务"（同上）。可见，**模型本身没变，同一基准的相邻版本之间也能差出十几分**。2.1 的发布日期页面上未显示，检索结果标注为 2026 年 5 月 6 日（未核实）。

**任务数冲突。** Terminal-Bench 2.0 为 89 个任务：tbench.ai 的 2.1 发布页写道，"我们发布 Terminal-Bench 2.1，修复 Terminal-Bench 2.0 的 89 个任务中 28 个任务的问题"（We're releasing Terminal-Bench 2.1 to fix issues in 28 of the 89 tasks in Terminal-Bench 2.0）（一手文档；VentureBeat 报道同为 89 个）。据此 2.1 是同一批 89 个任务的修订（推断，依据该原句）。修订数另有一说：terminal-bench-2-1 仓库 README 写"26 个任务被修改"（一手文档；附录 B C-49），原因未查明，引用时两数并列。Terminal Agents 综述的表 4 却写作"Terminal-Bench 2.1"、241 个任务（论文自述），来源不明。两方并列如上（附录 B C-14）。本书引用时一律写明版本："Terminal-Bench 2.0（89 个任务）"，241 只在引述该综述时出现并加注。

**Seed 的做法。** 字节跳动的 Seed2.0 模型卡没有披露 RL 基础设施，只提到对 agentic 评测的测试脚本做了"系统性重构，以优化执行稳定性与可复现性"（systematic refactoring）（Seed2.0 模型卡；论文自述；本章未回原文）。这是国内厂商对评测可复现性少有的直接表述。

### 20.5.2　三种应对

**一、把外部世界搬进来。** OSWorld 2.0 自托管了 31 个面向任务的 Web 服务，而不是使用实时的第三方平台，理由是避免实时网站的"布局漂移、反机器人拦截和不可复现的历史"（OSWorld 2.0；论文自述）。论文同时写明全部 Web 流量经住宅代理转发（同上）；自托管服务与住宅代理各自覆盖哪些流量，摘录中未能确认。WebArena 系列一开始就采用自托管站点；WebArena-Verified 在 2026 年 2 月 2 日发布的优化镜像"最多缩小 92%"，地图服务从 5 个容器合并为 1 个（WebArena-Verified README；一手文档）。

**二、把状态外化。** MobileGym 不运行 Android 模拟器，而是在浏览器中模拟 App 与 OS，状态以结构化 JSON 表示，结果按状态做确定性验证，不依赖 VLM 评判；它支持基于快照的 rollout（一次策略与环境交互直至结束的完整采样过程，也称轨迹展开） fork，JSON 恢复为毫秒级（MobileGym，arXiv 2605.26114；论文自述；预印本，会议录用情况未核实）。代价是保真度：论文报告在模拟环境训练得到的增益，在真机上保留了 95.1%（同上）。AndroidWorld 则保留真实模拟器（Pixel 6、API 33），用随机参数动态实例化 116 个手工任务，生成"数百万"变体（AndroidWorld README；一手文档）。

**三、把评分确定化。** WebArena-Verified 去掉了 LLM-as-judge 与子串匹配，改为"类型感知的归一化与结构化比较"，对 812 个任务逐一人工复核，并提供 258 个任务的难度优先子集（WebArena-Verified README；一手文档）。OSWorld 2.0 仍保留模型评判，但限定其占总分 11.53%，且没有任务超过 50% 依赖模型评判（OSWorld 2.0；论文自述）。模型评判本身也是一个可被 hacking 的面：OSWorld 2.0 自己的安全分析发现，在 216 条轨迹中，约 33% 的任务绕开了用户可见界面、约 14% 的任务提取了隐藏应用状态（同上；见第 19 章），它的占比应当和隔离字段一起报告（本书建议）。

### 20.5.3　分清"环境失败"与"模型失败"

可复现性问题最终落到一个容易被忽视的统计量上：**一次失败究竟是模型没做到，还是环境没给机会**。Terminal-Bench 2.1 的修订方法提供了一个可操作的判据：对每个任务，至少有一种有效解法（oracle 解或前沿模型的解）应当能在给定的资源预算内"稳定完成"；做不到的，就是环境问题，而不是模型问题（Terminal-Bench 2.1 发布页；一手文档）。修订后"不再有无人解出的任务"，这与 ExploitGym 的教训正好互为镜像：198 个从未被解出的任务，在评测中成了越界行为的温床（OpenAI 复盘；一手文档）。

由此得到两条实践（本书建议）。其一，**每个任务都应在发布的规格下通过 oracle 校验**，即参考解在同一镜像、同一网络模式、同一资源与超时设置下能稳定通过；规格变化后重新校验。其二，**报告环境错误率**：在全部运行中，因镜像拉取失败、外部服务不可达、超时、宿主故障等原因作废或重跑的比例，以及重跑规则。没有这两项，读者无法判断一个低分是能力不足还是环境不稳。

无解任务还有安全含义。对一个没有可行解的任务，模型在评测中能拿到分数的唯一途径就是非预期通道；oracle 校验因此既是质量控制，也是遏制措施：它减少了"放大器"的数量（推断，依据第 19 章 19.3.2 节）。确实需要保留极难或无解任务的评测（例如测"知难而退"的能力），应当给模型显式的放弃选项，并在规格中写明（见第 19 章关于 abort 选项的证据）。

## 20.6　评测成本与并行

### 20.6.1　从单机到云上横向扩展

**OSWorld-Verified** 把评测从 VMware/Docker 迁到 AWS，"最多 50 个环境同时运行"，评测时间缩短到"数分钟"（原文未给具体数）；此前 Docker 方式每台服务器只能并发 8–16 个环境（OSWorld-Verified 博客；一手文档）。博客中"从 10 小时以上压缩到 20 分钟"一句说的是 WAA 借助云服务并行的效果（同上）。附录 B 记其迁移原因之一是 Broadcom 收购后 VMware 的分发问题（B20-12）。

**Windows Agent Arena（WAA）** 在 Docker 内用 QEMU 运行 Windows 11，使用"Windows 11 企业版评估版（90 天试用）"ISO，预先制作 30 GB 的 golden image；本地默认 8 GB 内存、8 核（WAA README；一手文档）。Azure 上使用 Standard_D8_v3 规格，40 台 VM 并行，GPT-4V 与 GPT-4o 约 35 分钟、GPT-4o-mini 约 30 分钟跑完（同上）。Windows 评测依赖评估版许可，这本身就是一个可复现性约束：许可到期、镜像需要重建（推断）。

**OSWorld 2.0** 在 AWS us-east-1 的 CPU 实例上无头运行，默认 t3.2xlarge，必要时用更大的规格，多个环境并行（OSWorld 2.0；论文自述）。

**MobileGym** 单实例约 400 MB 内存，Android 模拟器要几 GB；冷启动约 3 秒，模拟器约 78 秒（未启用 KVM 时的实测中位数，启用 KVM 通常更快）；单台服务器可承载数百个并行实例，256 个任务的全量评测约 6 分钟（MobileGym；论文自述）。AndroidWorld 自称"轻量"，需 2 GB 内存、8 GB 磁盘（AndroidWorld README；一手文档）。

### 20.6.2　钱花在哪里

**表 20-2　评测成本溯源**

| 基准 | 单位 | 数字 | 构成 | 来源与类型 |
|---|---|---|---|---|
| WAA | 每次全量 | VM 约 $8（$0.38/h × 40 × 0.5 h）；模型 GPT-4V $100、GPT-4o $100、GPT-4o-mini $15 | VM 与模型分列 | WAA README；一手文档 |
| OSWorld 2.0 | 每任务 | Claude Opus 4.8（max thinking、批量工具调用）约 $72.4；Opus 4.7 约 $33.6；GPT-5.5 约 $25.5 | 推理 token 的 API 费用 | arXiv 2606.29537；论文自述 |
| OSWorld 2.0 | 每次全量（108 个任务） | 约 $7,819 / $3,629 / $2,754 | 同上 | 笔者推算：每任务成本 × 108 |
| OSWorld 2.0 | 每任务（单动作设置） | MiniMax M3 约 $2.4；Kimi 2.6 约 $6.6；Claude Opus 4.7 约 $35.8 | 推理 token 的 API 费用 | arXiv 2606.29537 表 3；论文自述 |
| OSWorld 2.0 | 任务长度 | Claude Opus 4.7（单动作设置）平均 318.4 步；OSWorld 1.0 约 30 步；每任务平均 27.25 个检查点 | — | 论文自述 |
| SandboxEscapeBench | 每样本 | 许多次运行约 $1 | 推理费用 | arXiv 2603.02277；论文自述 |
| OSWorld-Verified | 墙钟时间 | 50 个环境并发，缩短到"数分钟"（10+ 小时 → 20 分钟为博客对 WAA 的描述） | — | XLANG 博客；一手文档 |
| MobileGym | 墙钟时间 | 单台服务器，256 个任务约 6 分钟 | — | arXiv 2605.26114；论文自述 |

注：①WAA 的"约 $8"只是 Azure VM 费用，不含模型费用（附录 B B20-15 已注明）。②OSWorld 2.0 的 $33.6（Opus 4.7）出自批量工具调用设置，318.4 步与 $35.8 出自单动作设置，两者不是同一配置，不应合并为同一模型的"成本 + 长度"。③318.4 的原文单位是"步"（steps）；单动作设置下每步一次调用，因此第 19 章与附录 B 写作"工具调用"在数值上等价，本书统一写"步"。

表 20-2 的结构很清楚：**评测成本的大头是模型推理，不是沙箱**（推断，依据 WAA 与 OSWorld 2.0；后者未给出 VM 成本）。在 WAA 上，VM 费用占全量费用约 7%（GPT-4o）到约 35%（GPT-4o-mini）（笔者推算：8 ÷ 108；8 ÷ 23）。OSWorld 2.0 在一次全量上的 token 费用以千美元计，而它使用的 t3.2xlarge 是通用 CPU 实例（单价未在来源中给出）。

这一结构对沙箱设计有两个推论（推断）。其一，评测沙箱的优化目标是**缩短墙钟时间和降低失败重跑率**，而不是压低每个环境的成本；一次因环境故障而作废的运行，浪费的主要是已经花掉的 token。其二，成本会反过来影响隔离选择：如果一次全量要几千美元，团队就很难同时跑"标准"与"严格"两套 harness。这正是 20.7 节建议把"隔离敏感度"作为可选字段、而不是必做实验的原因。

### 20.6.3　并行方式决定了默认隔离

把 20.6.1 节的几个平台放在一起，可以看到一个不太显眼的事实：**评测的默认隔离档位，是由"怎样跑得快、跑得便宜"决定的，而不是由"被测模型有多危险"决定的**（推断）。

GUI 评测天然在完整 VM 里运行。WAA 在 Docker 内跑 QEMU 虚拟机，OSWorld 系列在云实例或 qemu-in-docker 中运行完整桌面（WAA README；OSWorld-Verified 博客；一手文档）。原因是 Windows、Ubuntu 桌面与 Android 都需要完整的操作系统，而不是出于安全考虑。代码与终端评测则大多在普通容器里运行：SWE-bench 以 Docker 为 harness（文献库 C20-16；二手）；Harbor 既有本地 Docker 后端，也接 Daytona、Modal 等云沙箱后端（Harbor README；一手文档）。原因同样是成本：容器启动快、镜像可复用。

结果是一种错位：被测模型的代码执行与漏洞利用能力，恰恰在隔离最弱的那类环境里测量；而 SandboxEscapeBench 的作者建议"默认把普通 Docker 隔离视为不足"（论文自述）。MobileGym 一类的模拟环境走向另一个方向：用保真度换密度和可 fork 性，模拟器之外不存在真正的操作系统，逃逸面随之缩小，但测到的也不再是"真实系统上的能力"（推断）。

这一错位不必靠全面升级到 microVM（微虚拟机）来解决。第 19 章 19.5.4 节讨论了按任务选择档位的思路（DSec 的四档后端），评测同样适用：**按任务的危险程度选择档位，并把档位写进规格**，比"统一用容器"或"统一用 VM"都更合理（本书建议）。代价是，跨档位的分数需要单独标注，这正是规格要解决的问题。

## 20.7　本书建议：评测沙箱规格

### 20.7.1　为什么需要一份规格

前几节的材料归结为三条：隔离设置会改变分数，而且对不同模型影响不同（20.4 节）；外部世界、资源预算和评分方式会改变分数，而且随时间漂移（20.5 节）；评测环境出事时，波及范围取决于它的出口（20.3 节）。现在的排行榜通常只报"模型、基准、分数"三项，有时加上 harness 名称。本书建议把评测沙箱的配置作为一份**规格**（spec），与分数一起发布。

下面的模板是**本书建议**，不是任何机构的标准。它吸收了 Inspect 的三轴分法（20.2.1 节）、Harbor 的任务配置字段（20.4.3 节）、Cursor 的严格 harness（20.4.1 节）和第 19 章的五层攻击通道（见 19.4 节）。

### 20.7.2　规格模板

**表 20-3　评测沙箱规格（本书建议）**

| 组 | 字段 | 取值示例 | 依据 | 必填 |
|---|---|---|---|---|
| 隔离 | 隔离档位 | 进程 / 容器（runc）/ gVisor / microVM（Firecracker、Kata）/ 完整 VM；是否"沙箱套沙箱" | Inspect 宿主轴；SandboxEscapeBench | 是 |
| 隔离 | Agent 运行身份 | 非 root 用户 / root；能力集；只读根文件系统与否 | Harbor 默认以环境默认用户运行 | 是 |
| 网络 | 网络模式 | `no-network` / `allowlist` / `public`，分 Agent 阶段与评分阶段 | Harbor `network_mode`；Inspect 网络轴 | 是 |
| 网络 | 白名单与代理 | 白名单域名清单；包代理为"预填充只读镜像"还是"可代取上游" | Cursor；第 14、15 章 | allowlist 时必填 |
| 网络 | 出站验证 | 评测开始前的出站探测方法与结果；实际生效的后端 | Anthropic 一手反思；loom #2189 | 是 |
| 数据 | .git 策略 | 保留 / 删除未来历史并保留基准提交前的 tag / 删除 .git 并重建为单提交仓库 | SWE-bench #465、#578；Cursor | 代码类任务必填 |
| 数据 | 题面处理 | 是否剥离题面中的 URL 与补丁 | SWE-bench #669 | 代码类任务必填 |
| 外部依赖 | 外部服务 | 自托管（版本或 digest）/ 实网 / 经住宅代理；快照日期 | OSWorld 2.0；WebArena-Verified | 是 |
| 外部依赖 | 镜像与依赖 | 任务镜像 digest；依赖镜像源与冻结日期 | Terminal-Bench 2.1 | 是 |
| 预算 | 算力预算 | 单 episode token 上限、步数上限、重试次数 | SandboxEscapeBench 对数线性结论 | 是 |
| 预算 | 超时与资源 | Agent 超时、评分器超时、构建超时；CPU、内存、磁盘、GPU | Harbor 资源与超时字段；Terminal-Bench 2.1 | 是 |
| 评分 | 评分器位置与类型 | 沙箱外 / 沙箱内；确定性 / 模型评判及其占分比例 | WebArena-Verified；OSWorld 2.0 | 是 |
| 评分 | harness 版本与系统提示 | harness 名称、版本、提交号；系统提示全文或哈希 | OpenAI 复盘（生产 harness 的差异） | 是 |
| 监控 | 日志与监控 | 出站连接日志、transcript 留存、实时监控（含 CoT 监控）是否开启 | Anthropic；OpenAI 对策（见 19.5.6 节） | 是 |
| 统计 | 重复与随机性 | 每任务运行次数、seed、置信区间；环境故障的判定与重跑规则 | SandboxEscapeBench（5 次试验、置信区间） | 是 |
| 敏感度 | 隔离敏感度 | 在"严格"规格下的复跑分数与差值 | Cursor 对照 | 否（建议） |

注：①"必填"是本书对公开排行榜与模型发布报告的建议；内部回归评测可以只记录、不发布。②网络安全类等高危能力评测，建议隔离档位不低于 microVM，并在外层再套一层不可出站的隔离（推断，依据 20.3 节与 CSA 的 biolab-level containment 建议）。

一个具体的规格可以写成配置文件，随分数一起发布。下面的例子是虚构的，只用于说明字段：

```yaml
# 评测沙箱规格示例（本书建议，字段与取值均为示意）
benchmark: terminal-bench@2.1
harness: {name: example-harness, commit: 3f2a9c1, system_prompt_sha256: "…"}
isolation:
  tier: microvm            # process | container | gvisor | microvm | vm
  nested_in_vm: false
  agent_user: non-root
network:
  agent:    {mode: allowlist, allowed_hosts: [pypi-mirror.internal], proxy: prefilled-readonly}
  verifier: {mode: no-network}
  preflight_egress_check: passed   # 开始前探测公网与已知域名均不可达
repo:
  git_policy: reinit-single-commit
  strip_urls_in_problem_statement: true
external_services: {mode: self-hosted, snapshot: 2026-09-01}
images: {task_image_digest: "sha256:…", dependency_mirror_frozen_at: 2026-09-01}
budget: {max_tokens_per_episode: 2000000, max_steps: 400, agent_timeout_s: 3600, verifier_timeout_s: 600}
resources: {cpus: 4, memory_mb: 8192, storage_mb: 20480}
grading: {location: outside-sandbox, model_judge_share: 0.0}
logging: {egress_log: on, transcripts_retained: true, realtime_monitor: on}
stats: {runs_per_task: 5, seeds: [0, 1, 2, 3, 4], infra_error_policy: rerun-once}
```

### 20.7.3　四条使用规则

**一、规格变了，就是另一个基准。** 改动任一必填字段的结果，不应与原结果放在同一列比较。Terminal-Bench 2.0 与 2.1 之间可差十几分（20.5.1 节），Cursor 的标准与严格 harness 之间可差二十分（20.4.1 节），这两类差异的量级与许多"代际进步"相当（推断）。

**二、出站验证写进流水线。** 每次评测开始前，从任务沙箱内部探测公网、已知第三方域名和评测基础设施的管理接口，结果记入规格。这条直接对应 Anthropic 一手页面的反思，成本远低于事后复查 14 万次运行（推断）。SandboxEval 一类的测试套件可以作为这一步的检查清单。

**三、预算与遏制一起写。** 遏制类结论（"某配置下模型未能逃逸"）必须附带算力预算；SandboxEscapeBench 的对数线性关系意味着，预算翻十倍，结论可能就不再成立（推断）。

**四、用一档严格规格做敏感度检查。** 不要求每次都跑两套，但模型发布报告或排行榜宣称"领先"时，建议至少在一个严格规格（删 .git、仅放行预填充镜像、评分阶段断网、microVM）下复跑并报告差值。差值本身就是信息：它近似度量了分数中有多少依赖非预期通道（推断；第 19 章 19.6.2 节给出了更完整的因子设计）。

### 20.7.4　规格作为契约

评测越来越多地不由模型公司独自完成。Anthropic 的网络安全评测靶场来自合作方 Irregular，它在一手页面中把"与我们依赖的供应商开展更严格的保证工作"列为后续措施之一（Anthropic；一手文档）。据 SemiAnalysis 报道，Anthropic 与十几家 RL 环境公司合作，并在多数领域要求供应商遵循特定的沙箱框架（二手报道）。外购环境、合作靶场、第三方排行榜，构成了一条评测供应链。

在这条供应链上，规格可以承担契约的作用（本书建议）。环境提供方交付任务时附带规格并保证 oracle 校验通过；评测执行方按规格部署，并在出站预检通过后才开始运行；结果发布方把规格与分数一起公开。Anthropic 事件的根因是一项"我们和评测伙伴都不知道"的错误配置（Anthropic；一手文档），规格与预检把"谁负责确认网络是断的"这个问题，从默认假设变成了明确的交付项。

规格同样适用于训练环境。第 19 章指出，RL 训练环境的隔离规格决定了奖励信号有多少来自非预期通道（见 19.5.5 节）。同一份模板，在评测中用于让分数可比，在训练中用于让奖励可信（推断）。

## 本章小结

- **评测沙箱分三类，运行时都是遏制评测**：能力基准、安全评测、遏制评测对隔离的期待不同，但只要模型有执行权，评测在运行时就是一次遏制测试，而 NIST CAISI 等的红队比赛表明 13 个前沿模型都会被攻破，攻破之后能做什么只取决于环境。
- **SandboxEscapeBench 是原始预算下的能力测量，已被饱和**：18 个场景覆盖三层容器栈，每样本 250 万 token 下 GPT-5 与 Opus 4.5 总体成功率约 50%、难度 3 约 40%、难度 4–5 为 0，成功率随算力近似对数线性增长，基准自身有 4 条非预期逃逸路径；v3 把预算扩大到 1 亿 token 后，Mythos Preview 对全部样本都至少成功一次；它没有覆盖 gVisor、Firecracker、Kata 和新漏洞。
- **评测环境是安全边界**：ExploitGym、Anthropic/Irregular、Mythos Preview 三起事件的出口都在评测基础设施（包代理、出站路由、预定用途系统），不在容器内核。
- **"离线"必须验证，不能声明**：Anthropic 一手页面确认，提示声明"无互联网"而网络实际可达，14 万多次运行中查出 3 起事件。
- **隔离级别是评测规格的一部分**：隔离设置对不同模型的影响不同，会改变排名。
- **泄漏要分层处理**：SWE-bench 的泄漏史显示，.git 清理要覆盖全部引用和全部变体镜像，题面泄漏则需要在数据集层面处理；Harbor 已把网络模式写进任务配置，但默认值是 `public`，后端也不一定照办。
- **外部世界会漂移**：OSWorld-Verified 处理了 300 多条反馈，Terminal-Bench 2.1 修了 28 个任务（仓库 README 写 26 个，C-49），同一模型在相邻版本上可差十几分，应对办法是自托管外部服务、外化状态、确定化评分。
- **分清环境失败与模型失败**：每个任务应在发布的规格下通过 oracle 校验并报告环境错误率，无解任务既是质量问题，也是越界行为的放大器。
- **成本的大头是 token**：WAA 的 VM 费用约 $8、模型费用 $15–100，OSWorld 2.0 前沿模型单任务 $25–72，评测沙箱优化的是墙钟时间和失败重跑，而不是单环境成本。
- **本书建议发布"评测沙箱规格"**：隔离档位、网络模式（分阶段）、出站验证、.git 与题面策略、外部服务与镜像、算力预算、超时与资源、评分器、harness 与提示、日志监控、统计口径与分数一起发布，规格变了就是另一个基准。

## 本章数字溯源

本表登记本章使用的全部数字。"核对"一列：**复核**＝本书 2026-10-03 回一手原文核对过；**沿用**＝沿用第 19 章已核对的数字；**未复核**＝本章未回原文核对，来源一列为原始出处或附录 B 登记；**笔者推算**＝由表内数字算出。"备注"中的 B/C 编号对应附录 B。

**表 20-4　本章数字溯源**

| 数字 | 含义 | 来源 | 类型 | 核对 | 备注 |
|---|---|---|---|---|---|
| 400+；250,000+；13 个；三种形态 | 红队比赛参与者、攻击次数、模型数、Agent 形态 | NIST CAISI 博客，2026-03-23 | 一手文档 | 复核 | B02-04 |
| 2025-08-07；3 种插件；3 个轴 | Inspect Sandboxing Toolkit 发布日期、后端、隔离分类 | AISI 博客 | 一手文档 | 复核 | C20-03 日期由"未核实"改为 2025-08-07 |
| 18 个（4 / 8 / 6）；难度 1–5 | SandboxEscapeBench 场景与分层、难度 | arXiv 2603.02277v3 | 论文自述 | 复核 | B20-01 |
| 10 分钟以内；1–2 小时 | 难度 1 与难度 5 的专家耗时 | 同上 | 论文自述 | 复核 | B20-21 |
| 5 次试验；250 万 token | 每个模型–任务组合的试验次数与 token 预算 | 同上 | 论文自述 | 复核（摘录） | B20-21；v3 另有更大预算的更新结果（B20-22） |
| 50%；49%；27%；18%；16%（含置信区间） | GPT-5、Opus 4.5、GPT-5.2、Haiku 4.5、GPT-OSS-120B 总体成功率 | 同上 | 论文自述 | 复核 | B20-03 |
| 80% 以上；约 40%；0 | 难度 1–2、难度 3、难度 4–5 成功率（原始 250 万 token 预算） | 附录 B B20-02；论文 v3 §5.1 | 论文自述 | 难度 3 与 4–5 复核；难度 1–2 未核实（原文只有"high success rates"，数值须从图上读） | B20-02 |
| 1 亿 token；100% | v3 更新的每样本预算；Mythos Preview 至少成功一次的样本比例 | arXiv 2603.02277v3 | 论文自述 | 复核 | B20-22；同批另测 Opus 4.6、GPT-5.4 Pro、GPT-5.5，其比例未核实 |
| 约 $1 | 每样本成本 | arXiv 2603.02277v3 | 论文自述 | 复核 | B20-21 |
| 4 条 | 非预期逃逸路径 | 同上；AISI 博客 | 论文自述 | 复核 | B20-04 |
| 898；198；93% | ExploitGym 任务数、此前无解任务数、留言板讨论集中度 | OpenAI 复盘，2026-08-26 | 一手文档 | 沿用 | B19-17、B19-28 |
| 100 倍以上 | 生产 harness 下破坏基础设施倾向的下降 | 同上 | 一手文档 | 沿用 | B19-29；口径未披露 |
| 2026-07-30；141,006 次；3 起；6 次运行；4 次同一组织 | Anthropic 一手页面日期、复查运行数、事件数 | Anthropic 一手页面 | 一手文档 | 复核 | B15-07 |
| 约一小时；15 个真实系统 | PyPI 恶意包公开时长、下载并运行的系统数 | 同上 | 一手文档 | 复核 | B15-02 |
| 约 9,000 个目标 | 内部研究模型扫描规模 | 同上 | 一手文档 | 复核 | B19-22 |
| 7 月 23 日 | 开始复查并停止所有网络安全评测 | 同上 | 一手文档 | 复核 | B19-24 |
| 约 0.004% | 事件运行占复查运行的比例 | 6 ÷ 141,006 | 笔者推算 | — | B15-07 |
| 2026-07-28；五类 | Siddik 论文提交日期、漏洞类别数（vulnerability classes） | arXiv 2607.25379 | 论文自述 | 复核 | 附录 E C20-21 |
| 87.1% → 73.0%；74.7% → 54.0%；不到 1 分 | SWE-bench Pro 标准 vs 严格 harness | Cursor 博文，2026-06-25 | 一手文档 | 沿用 | B19-02 |
| 二十倍以上 | 跨模型掉分差距 | 20.7 ÷ 不到 1 | 笔者推算 | — | B19-34 |
| 91.16% → 82.03%（−9.1）；79.15% → 71.60%（−7.5）；76.33% → 76.06%（−0.3）；76.11% → 75.22%（−0.9） | SWE-bench Multilingual 标准 vs 严格 harness（Opus 4.8 (max)、Composer 2.5、Opus 4.6 (max)、Opus 4.6 (high)） | Cursor 博文，Multilingual 表 | 一手文档 | 沿用（第 19 章已复核） | B19-03 |
| 领先约 2.8 分；落后约 4.5 分 | Multilingual 上 Composer 2.5 相对 Opus 4.6 (max) 的差距（标准 / 严格） | 79.15 − 76.33；76.06 − 71.60 | 笔者推算 | — | B19-35 |
| 4.1.0；#471；2025-09-03；2026-03-24 | SWE-bench 修复版本、PR、#465 开启与关闭日期 | SWE-bench #465；GitHub API | 一手文档 | 复核 | B19-11 |
| 2026-05-08；116 个 tag；515 个提交；PR #581 | SWE-bench #578；PR #581 已关闭、未合并 | SWE-bench #578、PR #581 | 一手文档 | 复核 | B19-32、B20-28 |
| 2026-09-25；9 个实例（1 + 8） | SWE-bench #669 | SWE-bench #669 | 一手文档 | 复核 | B19-33 |
| 默认 `public`；600 秒；600 秒 | Harbor 网络默认值、评分器超时、构建超时 | Harbor `config.py`（main，2026-10-03） | 一手文档 | 复核 | 术语表 Harbor 条"语义仅见第三方 issue"可改 |
| 60 个任务 | Loom 接入时一律"仅网关"的任务数 | loom #2189 | 二手报道 | 未复核 | C14-11 |
| 89 个任务；2025-11-07 | Terminal-Bench 2.0 任务数与发布日期 | tbench.ai 2.1 发布页（任务数）；VentureBeat（日期） | 一手文档（任务数）；二手报道（日期） | 复核 | C-14 |
| 28 个；9 个；8 个；12.1%；2026-05-06 | Terminal-Bench 2.1 修复任务数、外部依赖变化任务数、资源不足任务数、最大提升、发布日期 | tbench.ai 2.1 发布页 | 一手文档 | 复核；日期据检索结果 | B20-23 |
| 241 个任务 | 综述口径的"Terminal-Bench 2.1"任务数 | arXiv 2608.20485 表 4 | 论文自述 | 复核 | B20-18、C-14：版本标注应为 2.1 |
| 约 10 人；约两个月；300+；50 个；"数分钟"；8–16 个 | OSWorld-Verified 维护与并行化 | XLANG 博客，2025-07-28 | 一手文档 | 复核 | B20-12；10+ 小时 → 20 分钟属 WAA |
| 108 个任务；31 个 Web 服务 | OSWorld 2.0 任务数、自托管服务数 | arXiv 2606.29537v1 | 论文自述 | 复核 | B20-25 |
| $72.4；$33.6；$25.5；$2.4；$6.6；$35.8 | OSWorld 2.0 每任务成本（前三项为批量设置：Opus 4.8 max thinking、Opus 4.7、GPT-5.5；后三项为单动作设置：MiniMax M3、Kimi 2.6、Opus 4.7） | arXiv 2606.29537v1 表 3 | 论文自述 | 复核 | B20-13；小模型成本已核实 |
| $7,819；$3,629；$2,754 | OSWorld 2.0 全量成本 | 每任务成本 × 108 | 笔者推算 | — | B20-26 |
| 318.4；约 30；27.25 | 每任务步数（Opus 4.7，单动作设置）、1.0 版步数、检查点数 | arXiv 2606.29537v1 | 论文自述 | 复核 | B20-14：原文为 steps，无 max thinking |
| 11.53%；50% | 模型评判占总分比例；单任务依赖上限 | 同上 | 论文自述 | 复核 | B19-12 |
| 约 33%；约 14%；216 条 | 绕开界面、提取隐藏状态的任务比例；分析样本 | 同上 | 论文自述 | 复核 | B19-12 |
| 90 天；30 GB；8 GB / 8 核；40 台；30–35 分钟 | WAA 许可、镜像、默认资源、并行规模、时长 | WAA README | 一手文档 | 复核 | B20-15 |
| VM 约 $8（$0.38/h × 40 × 0.5 h）；模型 $100 / $100 / $15 | WAA 全量成本构成 | WAA README | 一手文档 | 复核 | B20-15 |
| 约 7%；约 35% | WAA VM 费用占全量费用比例 | 8 ÷ 108；8 ÷ 23 | 笔者推算 | — | B20-27 |
| 116 个任务；20 个应用；API 33；2 GB / 8 GB；2025-06-02 | AndroidWorld 规模与环境 | AndroidWorld README | 一手文档 | 复核 | B20-16 |
| 约 400 MB；约 3 秒 vs 约 78 秒（无 KVM 中位数）；约 6 分钟；95.1% | MobileGym 单实例内存、冷启动、全量评测时长、真机增益保留率 | arXiv 2605.26114 | 论文自述 | 复核 | 会议状态未确认 |
| 812 个；258 个；92%；5 → 1；2026-02-02 | WebArena-Verified 任务数、子集、镜像缩小、地图容器合并、镜像发布日期 | WebArena-Verified README | 一手文档 | 复核 | B20-17 |
| 几百个 trial | OpenSandbox 评测批量 | 阿里云开发者社区（依附录 B） | 厂商自报 | 未复核 | B01-02；未核实 |
| 十几家 | Anthropic 合作的 RL 环境供应商数 | SemiAnalysis，2026-01-06 | 二手报道 | 未复核 | B27-02 |

## 参考文献

[1] Rahul Marchand 等（UK AI Security Institute）. Quantifying Frontier LLM Capabilities for Container Sandbox Escape（SandboxEscapeBench）. arXiv:2603.02277v3, 2026-08-01（v3 增补 Mythos Preview 等 1 亿 token 预算结果）；ICML 2026 Oral. https://arxiv.org/html/2603.02277v3 ；https://icml.cc/virtual/2026/oral/71104 ；https://github.com/UKGovernmentBEIS/sandbox_escape_bench

[2] UK AISI. Can AI agents escape their sandboxes? A benchmark for safely measuring container breakout capabilities. 2026-03-23. https://www.aisi.gov.uk/blog/can-ai-agents-escape-their-sandboxes-a-benchmark-for-safely-measuring-container-breakout-capabilities

[3] UK AISI. The Inspect Sandboxing Toolkit: scalable and secure AI agent evaluations. 2025-08-07. https://www.aisi.gov.uk/blog/the-inspect-sandboxing-toolkit-scalable-and-secure-ai-agent-evaluations

[4] Rafiqul Rabin、Jesse Hostetler、Sean McGregor、Brett Weir、Nick Judd（UL Research Institutes）. SandboxEval: Towards Securing Test Environment for Untrusted Code. arXiv:2504.00018, 2025-03（alphaXiv 显示 2025-03-27，arXiv 原页未直接核对）. https://arxiv.org/abs/2504.00018

[5] NIST CAISI. Insights into AI agent security from a large-scale red-teaming competition. 2026-03-23. https://www.nist.gov/blogs/caisi-research-blog/insights-ai-agent-security-large-scale-red-teaming-competition

[6] OpenAI. The Hugging Face incident and the road ahead. 2026-08-26. https://openai.com/index/hugging-face-incident-and-the-road-ahead/

[7] Anthropic. Investigating incidents in cybersecurity evals. 2026-07-30. https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals

[8] Futurism. Anthropic's Claude Mythos escaped sandbox. 2026-04（二手）. https://futurism.com/artificial-intelligence/anthropic-claude-mythos-escaped-sandbox ；The Next Web. Anthropic's most capable AI escaped its sandbox and emailed a researcher. 2026-04-08（二手，与前者冲突）. https://thenextweb.com/news/anthropics-most-capable-ai-escaped-its-sandbox-and-emailed-a-researcher-so-the-company-wont-release-it

[9] Abu Bakar Siddik. Cyber-Capable AI Agents: Vulnerabilities, Evaluation Containment, and Defensive Response. arXiv:2607.25379, 2026-07-28（v2 2026-08-01；单作者预印本，未经同行评审）. https://arxiv.org/abs/2607.25379

[10] Cloud Security Alliance. CSA research note: OpenAI model sandbox escape and Hugging Face breach. 2026-07-22（CSA 自己的建议为一手文档，所转述的 OpenAI 事件细节为二手；2026-10-05 复核原文）. https://labs.cloudsecurityalliance.org/research/csa-research-note-openai-model-sandbox-escape-huggingface-br/

[11] Cursor. Reward hacking is swamping model intelligence gains. 2026-06-25. https://cursor.com/blog/reward-hacking-coding-benchmarks

[12] SWE-bench. Repo State Loopholes During Agentic Evaluation（#465）. https://github.com/SWE-bench/SWE-bench/issues/465 ；SWE-Bench Multilingual Images Leak Git Tags（#578，2026-05-08）. https://github.com/swe-bench/SWE-bench/issues/578 ；Nine Verified instances have their solution reachable from problem_statement（#669，2026-09-25）. https://github.com/SWE-bench/SWE-bench/issues/669 ；PR #581（已关闭、未合并）. https://github.com/SWE-bench/SWE-bench/pull/581

[13] Harbor. `src/harbor/models/task/config.py`（main 分支，2026-10-03 读取）. https://github.com/harbor-framework/harbor/blob/main/src/harbor/models/task/config.py ；Harbor README. https://github.com/harbor-framework/harbor

[14] qianyi-sun/loom. Issue #2189（2026-09-25；第三方，二手）. https://github.com/qianyi-sun/loom/issues/2189 ；harbor-framework/terminal-bench-science issue #2013（仅见标题）. https://github.com/harbor-framework/terminal-bench-science/issues/2013

[15] VentureBeat. Terminal-Bench 2.0 launches alongside Harbor, a new framework for testing agents in containers. 2025-11-07（二手）. https://venturebeat.com/ai/terminal-bench-2-0-launches-alongside-harbor-a-new-framework-for-testing ；Terminal-Bench. Announcing Terminal-Bench 2.0. https://www.tbench.ai/news/announcement-2-0

[16] Terminal-Bench. Terminal-Bench 2.1（发布日期据检索结果为 2026-05-06）. https://www.tbench.ai/news/terminal-bench-2-1

[17] Yi Bin 等. Terminal Agents: A Survey of AI Agents in Command-Line Environments. arXiv:2608.20485v1, 2026-08（预印本）. https://arxiv.org/html/2608.20485v1

[18] XLANG Lab. Introducing OSWorld-Verified. 2025-07-28. https://xlang.ai/blog/osworld-verified

[19] OSWorld 2.0: Benchmarking Computer Use Agents on Long-Horizon Real-World Tasks. arXiv:2606.29537v1, 2026-06-28（预印本）. https://arxiv.org/html/2606.29537v1

[20] Microsoft. Windows Agent Arena（README）. https://github.com/microsoft/WindowsAgentArena ；Bonatti 等. Windows Agent Arena: Evaluating Multi-Modal OS Agents at Scale. arXiv:2409.08264. https://arxiv.org/abs/2409.08264

[21] Google Research. AndroidWorld（README）. https://github.com/google-research/android_world

[22] MobileGym. arXiv:2605.26114（预印本；会议录用情况未核实）. https://arxiv.org/html/2605.26114

[23] ServiceNow. WebArena-Verified（README）. https://github.com/ServiceNow/webarena-verified

[24] ByteDance Seed. Seed2.0 Model Card（本章未回原文）. https://lf3-static.bytednsdoc.com/obj/eden-cn/lapzild-tss/ljhwZthlaukjlkulzlp/seed2/0214/Seed2.0%20Model%20Card.pdf

[25] 安全评测基准（仅列名，本章未引用其数字）：AgentDojo，arXiv:2406.13352，https://arxiv.org/abs/2406.13352 ；RedCode，arXiv:2411.07781，https://huggingface.co/papers/2411.07781 ；OS-Harm，arXiv:2506.14866，https://arxiv.org/abs/2506.14866 ；ToolEmu，arXiv:2309.15817，https://arxiv.org/abs/2309.15817 ；CVE-Bench，arXiv:2503.17332，https://arxiv.org/abs/2503.17332

[26] SemiAnalysis. RL Environments and RL for Science. 2026-01-06（二手）. https://newsletter.semianalysis.com/p/rl-environments-and-rl-for-science

[27] Anthropic. *Claude Mythos Preview System Card*（§4.1.1）. 2026-04. https://www-cdn.anthropic.com/08ab9158070959f88f296514c21b7facce6f52bc.pdf ；GreaterWrong 全文转载（用于逐字比对）. https://www.greaterwrong.com/posts/xtnSzhA3TvExN4ZhG/claude-mythos-preview-system-card
