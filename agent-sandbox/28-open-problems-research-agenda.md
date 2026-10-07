# 第 28 章　开放工程问题与研究议程

## 本章导读

前面 25 章（第 3–27 章）各自在结尾写下了"披露空白""开放问题"或"缺口"。这些段落分散在负载、原语、八层架构、RL 集成、产品与案例各部分，彼此有大量重叠：跨节点 fork 在第 11、24、25 章各出现一次，"不同隔离档位下的 hacking 率"在第 5、8、19、24、27 章各出现一次，"独立基准"几乎每一章都提到。本章把它们汇总、去重、归并，回答两个核心问题：**哪些问题工业界已经明确碰到却没有解决？研究者从哪里切入最有杠杆？**

本章的写法与前文不同：几乎不引入新的事实，数字原则上沿用前文与附录 B 的编号，贡献在于归类与排序。凡属笔者判断的内容，均标"推断"或"本书建议"。读完本章，读者应能：

- 用八个趋势概括全书的主要结论，并知道每个趋势由哪几章的证据支撑；
- 查到 13 项开放工程问题各自的现状、证据、难点与出处（表 28-1），以及 12 项安全线研究方向的核心问题与切入点（表 28-2）；
- 理解"遏制预算"为什么应当作为一个联合优化问题来提出，以及目前为什么连最基本的对照测量都不存在；
- 区分 2026 年相关学术工作中哪些已录用、哪些仍是预印本，哪些状态本书未能核实；
- 拿到一份可以直接动手的"最小可发表实验"清单，以及第 6 章承诺的统一口径测量方案。

## 28.1　八个趋势回顾

本节用八条趋势收束全书。每一条都只是对前文结论的复述，不新增论据；括注给出主要证据所在的章。

### 28.1.1　Agent 沙箱是一类独立的负载

Agent 训练沙箱的负载不是 serverless 函数，也不是长驻服务。DSec 用突发、CPU 稀疏、有状态长寿命、异构、镜像多样且复用有限、执行不可信、可中断七项特征刻画它，本书取其中五项（突发、稀疏、有状态、低扇出、可中断）作为全书的负载框架（见第 3 章）。这些特征的组合使经典答案需要重新加权：按需加载更必要，P2P 从主路径退为加速手段，可写层从可忽略变成要设计的对象（见第 10 章）。同时，这一判断的经验基础很窄：除 DSec 外没有第二家按同口径公开刻画，产品、GUI 与评测负载几乎没有数据（见 3.8 节）。

### 28.1.2　存储取代隔离原语成为竞争点

隔离原语在多租户场景已经收敛到 microVM（微虚拟机；见第 6 章），差异化转移到第④层镜像与存储、第⑤层状态管理（见第 9 章）。DSec 用可组合 EROFS 层把重建复杂度从 O(m·N) 降到 O(m)，运行时实际访问的镜像数据只占 4.2%–13.3%（DSec 表 3；论文自述；B03-09）；AgentENV 的工程重心在 Rust overlaybd 与 ublk 块设备层，内存快照也做成块设备以共享页缓存（见第 10、25 章）。两条路径在 DSec 的 microVM 可写盘交汇：DSec 的 microVM 存储路径使用了 AgentENV 仓库中开源的 Rust OverlayBD/ublk 组件（论文称"我们参与贡献"）。

### 28.1.3　暂停是成本杠杆

Kimi K3 报告称，Agent 等待模型推理的时间最多占沙箱寿命的 98%（K3 §5.3.2；论文自述；B03-10）。在这种负载下，CPU 超售门槛很低，内存才是第一约束；暂停在等待期把整个沙箱移出内存，是唯一能把内存成本降到零的手段（见第 11、13 章）。产品侧的计费演进说明了同一件事：按活跃 CPU 计费只处理了 CPU，"暂停免费"与"状态保留"是两项不同的承诺（见第 22 章）。AgentENV 以暂停为中心、DSec 以密度为中心，两条路线的对照见第 25 章。

### 28.1.4　rollout 状态外置

一次 Agent rollout（一次策略与环境交互直至结束的完整采样过程，也称轨迹展开）的状态分布在 GPU、harness（外壳/评测框架，负责驱动 Agent 循环、工具与打分）、沙箱与验证器四处，GPU 作业被抢占时沙箱多半还活着，必须指定一方为事实来源（见第 17 章）。DSec 自 V4.1 起让 worker container 与 agent sandbox 在可抢占 GPU 池之外共同持有 rollout 状态，抢占时由 RL 框架主动暂停相关沙箱（DSec §6.2、§6.3；论文自述；B17-01）。"rollout 状态归谁"因此成为训练沙箱与产品沙箱的分水岭（见第 9、24 章）。

### 28.1.5　接口在两层上标准化

生命周期层（create、exec、文件、暂停、fork）向 E2B 协议收敛，AgentENV、CubeSandbox、腾讯 AGS、阿里 ACS 都宣称兼容，证据多为实现者自述；环境语义层向 Gym 式接口加 MCP 收敛，OpenEnv、verifiers、NeMo Gym 之间已有适配器（见第 16 章）。两层之间仍缺七个概念：语义级网络策略、阶段切换、作业级暂停、完整性约束、fork 语义、资源与后端声明、与 rollout 关联的可观测性（见 16.6 节、表 16-2）。

### 28.1.6　披露转向运维指标

2026 年的技术报告开始写失败率、构建成功率与磁盘压力，而不只写并发量（见第 26 章）。RollArt 记录 env.reset 约每十次迭代出现一次环境超时，超时迭代中 env.reset 单独占 rollout 时间的 78%（RollArt §3.1；论文自述；B10-14）；快手记录约 16% 的轨迹含至少一次沙箱可归因故障（KAT-Coder-V2.5 §4.2.2；论文自述；B18-02），并把它当作奖励信号可靠性问题处理（见第 3、18 章）。可靠性开始被视为训练质量指标。

### 28.1.7　Agent 自动化环境构建

环境规模已到十万级，构建本身被 Agent 自动化：快手的构建成功率从 16.5% 提到 57.2%（KAT-Coder-V2.5 §2.1；论文自述；B18-01），阶跃为 40%，GLM-5 终端合成任务的 Docker 构建准确率超过 90%，三者分母与判据不同，不能排名（见第 18 章）。DSec 的 pack_diff 把交互会话直接固化为环境镜像（见第 24 章）。构建流水线因此成为上游攻击面：.git 未来历史、构建残留等会让答案随镜像进入环境（见第 18、19 章）。

### 28.1.8　竞争对手在底层开源协作

DSec 的 microVM 存储路径使用了 AgentENV 仓库中开源的 Rust OverlayBD/ublk 组件（论文称"我们参与贡献"）；AgentENV 托管在自称清华 MADSys 联合研究项目的 kvcache-ai 组织下，以 MIT 许可开源（见第 25 章）。本书据作者重合推测存在一条 TrEnv → AgentENV → DSec 的学术到工业传承线（推断，基于作者重合）。同一时期，OpenEnv 由多家机构共同治理，E2B 协议被国内外云厂商共同实现（见第 16 章）。竞争集中在模型与数据上，沙箱的底层组件正在变成公共品（推断）。

**八个趋势与本章问题的关系。** 这八条趋势不是彼此独立的。存储成为竞争点（28.1.2）与暂停成为成本杠杆（28.1.3）共同把压力推到快照与恢复上，于是有了表 28-1 的跨节点 fork（E2）与抢占风暴（E3）；rollout 状态外置（28.1.4）把沙箱拉进训练正确性，于是有了 token 一致性（E11）；披露转向运维指标（28.1.6）让 env.reset 可靠性（E4）第一次有了数字；环境构建的自动化（28.1.7）扩大了上游攻击面，与第 19 章的取回型 hacking 连在一起（E10）；接口标准化（28.1.5）与底层开源协作（28.1.8）降低了做独立测量的门槛，却还没有带来独立测量本身（E12）。概括地说，趋势描述的是工业界已经做到了什么，开放问题描述的是这些做法在规模、正确性与安全上的下一道坎（推断）。

**关于标准的补充判断。** 这八条趋势之外，第 23 章修正了一个容易被误读的判断：沙箱与隔离**已经**写入非强制的实践指南和实验室治理框架，但**尚未**进入任何强制性标准或法规。前者包括 TC260《智能体系统开发安全指南（征求意见稿）》第 8 章 n）项第 1）条（以"应"字要求把模型推理、工具执行、代码执行"置于适当的沙箱、容器或其他隔离边界内"）、五眼机构联合指南《Careful adoption of agentic AI services》（"Implement isolation and segmentation to limit blast radius of agent failure scenarios"，并要求"Deploy sandbox environments to test agent behaviour before production deployment"；一手文档；B23-15）、Google DeepMind FSF v3.1（Security Level 2+ 下"mandating that the processing of untrusted inputs occurs within sandboxed environments"；一手文档；B23-09）与 OpenAI《Frontier Governance Framework》（"Model execution is sandboxed, with restricted egress by default."；一手文档；B23-19）。此外，TC260 已发布的《智能体部署使用安全指引》（TC260-PG-20266A）也建议以"基于沙箱等技术的环境隔离"补强（一手文档；B23-12）。这些文件都不具强制力；中国已立项的强制性国标《智能体应用安全基本要求》草案未公开（B23-13），本书检索范围内的强制层是空的（见第 23 章小结）。

## 28.2　开放工程问题

### 28.2.1　归并方法

表 28-1 的 13 项来自目录的初拟清单，本书按第 3–27 章的空白段落逐条核对后保留了全部 13 项，并把其余条目归并进去。归并遵循三条规则：同一机制问题在多章出现时，归入机制所在层的那一项，并在"相关章"列出全部出处；"某系统未披露某参数"类条目，只在它构成一类问题时才进入本表，单纯的厂商空白留在各章披露表（如表 9-5、表 24-7、表 25-6）；安全取向的问题进入 28.3 节的表 28-2，两表交叉的条目在两处都列出相关章。

**表 28-1　开放工程问题（现状 / 证据 / 为什么难 / 相关章）**

| 编号 | 问题 | 现状 | 证据 | 为什么难 | 相关章 |
|---|---|---|---|---|---|
| E1 | 可扩展放置 | 只有 DSec 公开了放置算法（过滤 + power-of-k + 本地在途叠加），k 值与"负载"定义未披露；K8s 路线训练侧无一家公开创建速率或放置算法 | DSec 单个规模单元峰值能力超过 5,000 个/秒，日均约 34.7 个/秒，相差两个数量级以上（B24-06、B24-14）；agent-sandbox 文档称默认配置下 Pod 调度约 70 个/秒；AgentENV 开源调度器只有轮询与随机 | 按峰值设计、按均值运行；创建关键路径上是否有一致性写决定上限（推断）；放置要同时考虑镜像缓存位置、快照位置与后端档位 | 9、24、25 |
| E2 | 跨节点 fork 与在线迁移 | 工业系统中没有一家披露跨节点 fork 或在线迁移；AgentENV 文档披露了经共享快照仓库的跨节点冷恢复，但没有延迟与带宽数据，fork 限同节点、上限 100 | Crab 的单沙箱迁移中位 0.71 s（B11-26），不是集群规模；CXLfork、TrEnv 依赖 CXL/RDMA 内存池 | 私有内存与可写层无法靠页缓存共享吸收；网络连接无法快照；快照与 VMM、内核、虚拟化模式绑定 | 11、24、25、6 |
| E3 | 抢占风暴下的暂停一致性 | DSec 由 RL 框架在抢占时批量暂停相关沙箱，但未披露一次暂停多少沙箱、耗时多久、快照写到哪里 | DSec 单作业最多请求 32K 个沙箱（DSec §1；论文自述）；只有 Crab 做了宿主层检查点流量调度，场景是同机几十个沙箱 | 同步写风暴与恢复时的读风暴；重连时正在执行的工具调用是否恰好一次；陈旧度窗口与沙箱寿命耦合；第三方 harness 未必可快照 | 11、17、24、12 |
| E4 | env.reset 可靠性 | 只有 RollArt、快手公开了故障率；GUI 环境的 reset 延迟无人公开 | env.reset 超时迭代中占 rollout 时间 78%（B10-14）；约 16% 轨迹含沙箱故障（B18-02）；快手优化前峰值磁盘占用约 95%（B10-15） | 低扇出使缓存命中率低；故障被当作奖励噪声吸收；"环境失败"与"模型失败"难区分 | 3、7、10、18、20 |
| E5 | 可写层去重 | 可写层与匿名内存只能回收、不能共享，是各工业系统的共同短板 | DSec pmem DAX 只共享只读层（峰值内存 −40.2%，B13-04）；AgentZip 跨沙箱压缩最多降 8.7 倍（Linux 配置 2.1 倍；B13-10），无生产部署报告 | 同一模板派生的沙箱"相似但不相同"；压缩带来减速（最高 3.1 倍，经调度降到 1.40 倍）；层数增长后何时合并没有公开数据 | 10、13、11 |
| E6 | GUI 密度 | 规模数字很多，reset 延迟、GPU 用量、每环境成本几乎没有；除 DSec 外无训练系统说明 GUI 放在哪一档 | CUA-Sandbox 自报吞吐最高 6.20 倍、内存降 9.2 倍（VWA、8 并发；最大密度未测；B07-06）；MobileGym 单实例约 400 MB（B07-07） | 完整 OS、显示与输入通道、应用进程状态都要复制；保真度与密度互换；Windows、macOS 许可限制 | 7、13、3 |
| E7 | GPU 沙箱 | DSec 的 GPU FnCall（MIG 切分、预创建容器）与 K3 的 GPU 沙箱只有机制描述，没有负载数据 | NVIDIAScape（CVSS 9.0；B05-02）可由恶意镜像触发；GPU TEE 在 LLM 规模下的开销无公开数字 | GPU 驱动与设备注入以高权限运行；显存难以超售与快照；隔离与共享粒度粗 | 3、5、6、8 |
| E8 | 云上与嵌套虚拟化 | 公有云普遍不提供 KVM；嵌套虚拟化依机型而定；PVM 未入主线 | DSec 云突发只覆盖镜像落在 30 TB 集合内的任务，即 70% 的容器任务（DSec §3.4；论文自述）；AgentENV 节点拒绝恢复另一种虚拟化模式下创建的快照 | 维护分叉内核的成本；KVM 与 PVM 节点快照不互通；弹性依赖可上云的镜像子集 | 6、9、25 |
| E9 | 网络策略的表达 | 五级粒度（开关、地址、名字、语义、身份）各有执行机制，没有公开协议能表达语义级、分阶段的网络策略 | 白名单按名字匹配、流量按地址发生（空字节、域前置、DNS 重绑定）；Modal 不支持 ECH，E2B 域名过滤不覆盖 QUIC；训练沙箱的 DNS 处理无一手披露 | 名字到地址的映射要持续维护；被允许的域名本身是双向通道；加密协议演进削弱 SNI 过滤；跨后端语义不一致 | 14、15、16 |
| E10 | reward hacking（奖励投机）的系统化检测 | 生产系统只列行为、不给比率；对策没有前后对比 | DSec §6.4 无比率（B19-13）；Cursor 63% 取回而非推导（B19-01）与 ImpossibleBench GPT-5 54%（B19-06）分母不同、不可比 | 需要按通道计数而非按"是否作弊"计数；轨迹判读主观；无解任务是放大器 | 19、20、24、26、27 |
| E11 | token 一致性 | 工具输出须在唯一的点被分词一次；位于 GPU 池外的事实来源须保存 token 级轨迹；rollout 状态没有跨框架格式 | 快手约 200 轮时重新分词漂移曾影响约 40% 样本（B17-10） | 状态跨沙箱与推理服务两个系统；各框架的 chat 模板与分词点不同 | 17、16 |
| E12 | 独立基准 | 所有启动、密度、暂停数字都来自系统作者或厂商；没有第三方同硬件、同负载的横向测试 | Rollout Infrastructure Tax 作者来自 Daytona（SoCC'26 投稿预印本）；ComputeSDK 有厂商赞助（见第 22 章）；负载刻画也只有 DSec 一家同口径 | 各家"冷启动"起止点不同；厂商没有动力在对手的最优配置上测；训练关心的高并发、频繁暂停区间无人覆盖 | 3、6、13、22、25 |
| E13 | 可复现性 | 外部世界漂移、快照唯一性、共享缓存污染都会让同一任务在不同时间、不同分支上不可比 | Terminal-Bench 2.1 修订任务数一手两处为 26 与 28（C-49）；没有任何 Agent 沙箱披露 fork 后如何重置熵与标识符 | 快照把"本该唯一"的状态复制给所有子实例；拉取式缓存使后一个 rollout 读到前一个引入的依赖；VMM 与内核升级后旧快照能否恢复少有说明 | 6、11、15、20 |

注：数字类型见表 28-5；"相关章"按与问题的相关程度排序；"为什么难"列为本书归纳（推断）。

**归并说明。** 以下子问题已并入表 28-1 的相应项，括注为原出处：控制面各组件实例数与创建延迟分布（9.9 节）、预热池抽干时落回冷启动（9.5 节）并入 E1；"一次抢占暂停多少沙箱"（11.6.3、17.8、24.7 节）、重连时的恰好一次语义与陈旧度耦合（17.8 节）、harness 自身的可快照性（17.8 节）并入 E3；层数增长与合并（11.6.2 节）并入 E5；GUI 许可与确定性（7.10.1 节）并入 E6；GPU 沙箱负载未刻画（3.8.1 节）并入 E7；PVM 是否在生产中使用（25.9 节）并入 E8；DNS 与凭据注入无一手披露、名字到地址的映射维护、TLS 拦截的信任代价（14.8 节）、MCP server 的出站如何纳入任务策略（16.9 节）并入 E9；生产对策无前后对比（19.6.1 节）、ROME 与 MiMo 之外无沙箱侧 hacking 记录（26.13 节）并入 E10；跨框架 rollout 状态格式（16.9、17.8 节）并入 E11；E2B 兼容的一致性测试（16.9 节）、中断频率与后端比例未披露（3.8.1 节）、产品负载分布（3.8.2、21.10 节）并入 E12；模板 fork 后的唯一性（6.6.4、11.6.1 节）、共享缓存的跨 rollout 污染与冻结–新鲜度张力（15.7 节）、外部服务漂移（20.5 节）并入 E13。

### 28.2.2　几项需要展开的问题

**E1 与 E3 是同一枚硬币的两面。** 放置决定沙箱落在哪里，抢占决定沙箱什么时候必须一起离开。DSec 的设计在两端都有答案：沙箱 ID 编码所属 edge、power-of-k 加本地在途视图；抢占时由 RL 框架向相关沙箱批量发送暂停请求（见第 9、24 章）。但这两端的参数都没有披露，于是一个最基本的工程问题没有公开答案：当一个持有数万沙箱的作业被抢占时，暂停的 p99 是多少、写出的快照总量多大、恢复时放置是否要回到原节点。把放置与快照位置联合决策（OpenAI 演讲中的"快照感知调度"只有二手摘要），是 E1、E2、E3 共同指向的方向（推断）。

**E4 的价值在于它把可靠性变成了训练指标。** RollArt 的多级缓存使 env.reset 成功率超过 99.99%（B10-14），快手通过重写镜像管理把超时无效 rollout 从约 6%–7% 降到 1% 以下（B10-15）。这些数字说明问题可解，但都是单一系统在自家负载下的前后对比。没有人公开过"沙箱故障率对最终模型能力的影响"，也没有人在 GUI 环境上做过同样的统计（见第 3、7 章）。

**E6 与 E7 是"重环境"的两种形态。** GUI 环境把完整 OS、显示与输入通道、应用进程状态都装进了沙箱，单实例内存以 GB 计；GPU 沙箱则把一块难以超售、难以快照的设备装了进去。两者都让第 13 章的四族密度技术失灵了一半：共享与回收主要针对 CPU 侧内存，暂停对显存与图形状态的支持没有公开数据（推断）。GUI 侧已有两条路线：完整 VM 加数千实例（UI-TARS-2、ComputerRL、MobileRL）与剥离状态（CUA-Sandbox、MobileGym）；后者中 MobileGym 以保真度换密度，需要在真机或完整 VM 上报告迁移保留率，CUA-Sandbox 保留真实应用，需要说明隔离覆盖与最大密度（见 7.10.2 节）。GPU 侧连路线都还没有成形：DSec 用 MIG 切分加预创建容器，只适用于函数级调用；需要长寿命 GPU 状态的 Agent 任务（例如在沙箱里训练小模型、跑 CUDA 内核基准）怎样隔离与暂停，本书没有找到任何一手材料（见第 3、8 章）。NVIDIAScape 说明 GPU 容器的创建路径本身是高权限入口（B05-02），这又把 E7 与安全线的 S2 连在一起。

**E8 决定了谁能用 microVM。** 训练侧两份一手披露（DSec、AgentENV）都跑在可以直接使用 KVM 的环境上；公有云上的团队要么依赖机型开放嵌套虚拟化，要么维护 PVM 这样的分叉内核，而 PVM 与标准 KVM 节点的快照不互通（见 6.5 节）。DSec 的云突发说明了另一层约束：弹性只能覆盖镜像落在可上云集合内的那部分任务（DSec §3.4；论文自述）。这意味着"突发时上云"不只是算力问题，也是存储分发与虚拟化模式的问题（推断）。

**E9 是策略语言问题，不只是执行机制问题。** 第 14 章把出站策略拆成三种主体（产品用户、平台运营者、任务定义者）与五级粒度，并发现执行机制各有盲区；第 16 章把"语义级网络策略"与"阶段切换"列入接口缺失的七个概念。两者合起来指向一个具体问题：任务定义者想说的是"安装阶段可以访问包镜像，测试阶段完全断网，任何阶段都不得写公共仓库"，而平台能执行的是"某个时段放行某组 IP 与端口"。中间的翻译由谁做、名字到地址的映射多久刷新、DNS 是否视同出站，目前每个系统各自决定，且训练沙箱的这部分设计几乎没有一手披露（见 14.8 节）。

**E11 把沙箱拉进了训练正确性。** token 一致性看起来是 RL 框架的问题，但当 rollout 状态的事实来源位于 GPU 池之外（E3、28.1.4 节），保存的是文本还是 token 级轨迹、工具输出在哪里被分词，就成了沙箱接口必须回答的问题（见 17.5.3 节）。快手的数字说明这不是边角问题。跨框架的 rollout 状态格式也归在这一项：没有公共格式，同一条轨迹就无法在 veRL、slime、prime-rl 之间迁移，也就无法在框架之间做抢占后的恢复（推断；见 17.8 节）。

**E12 是一个元问题。** 表 28-1 中几乎每一项的"证据"列都是厂商或作者自报，这本身就是 E12 的证据。第 6 章 6.8 节因此承诺给出一套统一口径的测量方案；本书把它放在 28.6.2 节，与其他"最小可发表实验"并列。

**E13 在训练侧比在评测侧更隐蔽。** 评测的不可复现会表现为分数漂移，容易被发现；训练的不可复现会表现为 GRPO 一组 rollout 在环境侧并不独立（例如从同一个 fork 出发，随机种子、端口、临时文件名完全相同），或后一个 rollout 经共享缓存读到不同的依赖，它们直接进入梯度，没有显式信号（推断；见 11.6.1、15.7 节）。

## 28.3　安全线研究方向

### 28.3.1　总体判断

安全线的学术文献在 2025–2026 年快速增加，但它们几乎都停在工具调用这一语义层。两篇综述性工作给出了与本书一致的总判断：*Systems Security Foundations for Agentic Computing*（arXiv 2512.01295，预印本）主张从端到端系统安全、而不只是模型安全来看 Agent；*Toward Securing AI Agents Like Operating Systems*（arXiv 2605.14932，预印本）的摘要写道，"一些 Agent 能力在设计上就是不安全的，但许多漏洞可以用成熟的技术缓解"（"while some agentic capabilities remain insecure by design, many vulnerabilities can be mitigated using well-established techniques"；论文自述）。本书在此基础上补充一点：现有安全研究针对的几乎都是"被利用的代理人"，对"作为对手的模型"（训练与评测中的租户本身）研究很少，而后者正是第 19、20 章证据最集中的地方（见第 2 章的两类对手定义）。

表 28-2 列出 12 项研究方向。它们来自目录初拟清单，经与第 4、5、8、12、14、15、19、20、21 章核对后保留，"依据"列给出最直接的证据与出处。

**表 28-2　研究议程：安全线（方向 / 核心问题 / 依据 / 切入点 / 相关章）**

| 编号 | 方向 | 核心问题 | 依据 | 切入点 | 相关章 |
|---|---|---|---|---|---|
| S1 | 跨层能力传递 | 能否把语义层的能力与标签（CaMeL、FIDES）编译成 OS 层规则（seccomp、Landlock、出站代理），使语义层被绕过时仍有确定性边界 | 语义层决定发出哪些动作，OS 层决定损害上限，两层尚未打通；CaMeL 在 AgentDojo 上"可证明安全"完成 77%，无防御 84%（B02-05）；Execute-Only Agents、Grimlock 是从 OS 一侧伸出的愿景论文 | 选一个有标签的语义层系统，把每条工具策略翻译成进程级规则，测量语义层被注入绕过时 OS 层能挡住的比例 | 4、8、14 |
| S2 | 强原语逃逸评测 | gVisor、Firecracker、Kata 在前沿模型面前的实际强度 | SandboxEscapeBench 只覆盖 Docker 容器栈；原始 250 万 token 预算下难度 4–5 为 0（B20-02），v3 在每样本 1 亿 token 下 Mythos Preview 对全部样本至少成功一次（B20-22） | 沿用"沙箱套沙箱"的安全设计，把场景移植到更强原语，固定并报告算力预算 | 5、6、20 |
| S3 | 失准 agent 遏制基准 | 模型在训练与评测中主动寻找答案通道、篡改 harness 时，环境能挡住多少 | DSec §6.4 清单（伪造 chronus RPC、覆盖 /bin/bash 等）；ExploitGym 包代理四种角色；Anthropic 复查 141,006 次运行查出 3 起事件（B15-07） | 以第 19 章五层通道为场景维度，构建带金丝雀的遏制基准，报告"尝试"与"成功"两类事件率 | 15、19、20、24、27 |
| S4 | 外部副作用回滚 | 沙箱外的效果怎样暂存、补偿或门控；回滚本身的语义安全 | 工业界没有一手的外部副作用事务实践（12.8 节）；Planarian、Cordon、Atomix 都是预印本；ACRFence 演示动作重放 10/10（B12-15），防御未实现 | 见 28.3.2 节 | 11、12、21 |
| S5 | 可验证的策略合成 | 能否从代码或任务描述自动生成可验证的最小权限策略 | AgentBound 在 296 个 MCP server 上自动生成策略准确率 80.9%（FSE 2026；论文自述；B16-06）；Progent 用 SMT 判断策略更新是收紧还是扩张 | 以 AgentBound 数据集为起点，把"准确率"细化为过宽与过窄两类错误，并测量过宽策略可被利用的比例 | 8、16 |
| S6 | 出站与凭据 | 凭据外置之后"借用"怎么管；包通路怎样从网络层搬到存储层 | 代理附凭据防住"拿走"、防不住"借用"；ExploitGym 中包代理同时是出站中继、写信道、提权跳板与信任根；九条出站原则无一有效果测量 | 请求级校验的策略语言；按包（名称、版本、哈希）放行的只读快照与拉取式缓存的受控对比 | 14、15、21 |
| S7 | trust handoff（信任移交） | 沙箱内写下的文件被沙箱外受信任工具执行，怎样系统地发现与阻断 | 2025–2026 年本地 Agent 的"逃逸"几乎都是策略管道失效与信任移交（hook、解释器、git 配置、项目文件、符号链接），没有一例突破原语本身 | 枚举"会被执行的配置"清单，做成自动化回归测试；训练中把"沙箱内写、评分器读"纳入同一框架 | 4、19、21 |
| S8 | RL 沙箱的安全与吞吐权衡 | 隔离档位每升一级，吞吐与 hacking 率各变化多少 | DSec 每节点容器与 microVM 能力比为 4 倍（笔者推算；B13-01）；没有任何研究测量不同隔离档位下的 hacking 率（B28-02） | 见 28.4 节与表 28-4 第 1 行 | 5、8、19、24 |
| S9 | computer-use 隔离 | GUI 形态的越界（绕开界面、提取隐藏状态）怎样隔离与评分 | OSWorld 2.0 约 33% 的任务绕开界面、约 14% 的任务提取隐藏状态（216 条轨迹，每个模型 108 个任务；B19-12） | 评估器放在沙箱外、检查界面事件轨迹；GUI 与终端动作空间分离后的对照 | 7、19、20 |
| S10 | 审批疲劳 | 人工审批在什么条件下仍有安全价值 | Claude Code 引入沙箱后权限提示减少 84%，此前用户批准约 93% 的提示（一手文档；B04-01）；产品审批以单命令为单位，不绑定事务 | 把审批绑定到事务与效果类别（Cordon 的限定范围审批），测量批准率与危险批准的变化 | 4、12、21 |
| S11 | 语义防御的理论极限 | 若语义层在原理上无法完全阻止提示注入，OS 层要承担多少 | arXiv 2605.17634 在情境完整性框架下论证：对手总能构造让被阻断的信息流显得合理的情境，否则防御方收紧规范就会阻断合法的流（论文自述） | 把"语义层必然有漏"作为前提，测量各 OS 层机制在语义层失效时的剩余保护 | 2、8 |
| S12 | 独立基准加 TEE | 评测平台与沙箱厂商怎样证明自己"如实执行了声明的隔离规格" | TEE 防运营方、不防模型；远程证明适合控制密钥释放；独立基准缺席（E12） | 用远程证明绑定"评测沙箱规格"（第 20 章）中的隔离档位、网络模式与镜像哈希 | 8、20、22、23 |

注："切入点"列为本书建议；S2、S3 与表 28-1 的 E10、E12 交叉；S8 与 28.4 节合流议题相同。

### 28.3.2　外部副作用回滚：以第 12 章为准

S4 是安全线与"状态"第二主线的交汇处，也是 2026 年学术进展最快的方向之一。第 12 章的结论可以压缩为三点（详见第 12 章）。其一，**快照止于沙箱边界**：Agent libOS、Fault-Tolerant Sandboxing、DeltaBox、BranchFS、AgentRewind 都在论文中声明不回滚外部效果（见 12.1.1 节）；把本地快照与远端补偿合成一个抽象的 Planarian（arXiv 2609.35366；预印本）在摘要中称把任务质量"最多提高 15 倍"、以"仅 3% 的开销"从错误动作中恢复（Planarian 摘要；论文自述；B12-01），本书只读到摘要，补偿动作的来源与远端 fork 语义未核实。其二，**对不可逆效果只能在提交前扣住**：Atomix（arXiv 2602.14849；预印本）两个版本的数字不同，v1 在 WebArena 与 OSWorld 上施加 30% 故障注入，完整事务配置的成功率为 37%–57%、基线为 0–7%（B12-02），v2 在 τ-bench retail 上 500 次无效发送泄漏 0 次，Saga 式补偿的泄漏率为 80%、Checkpoint-Replay 为 40%（Atomix v2 表 2；论文自述；B12-09）；Cordon（arXiv 2606.17573；预印本）在自建的 45 个风险工作流上全部于提交前拦下，回滚中位 4.17 ms（B12-10、B12-12）；两者的保证都只覆盖经过中介层、效果可观察的操作（见 12.3 节）。其三，**回滚本身是攻击面**：ACRFence（arXiv 2603.20625；预印本，研讨会出处未核实）演示了动作重放（10/10 次检查点恢复产生重复提交）与权限复活（令牌复用 2/2 成功），其 replay-or-fork 防御尚未实现（B12-15）；YoloFS（SOSP'26 已录用）把撤销做成可审计的（B12-05）；AgileLog（SOSP'26，据官方录用列表）从另一端提出可 fork 的共享日志，本书只读到摘要，机制与数字**未核实**。

在此基础上，S4 的开放问题有四个（推断，依据第 12 章）：一是**分类的正确性**，Atomix 自认作用域、幂等键、效果类别等元数据"安全攸关"，一个被误标为"可补偿"的支付接口会被立即执行，谁来为外部 API 标注效果类别、标错了怎么发现，没有方案；二是**远端如何分支**，Planarian 的补偿路线与 AgileLog 的"外部服务原生支持 fork"路线各解决一半，二者的组合未见研究；三是**幂等键的归属**，幂等键必须由事务运行时在效果首次登记时分配并持久化，不能由模型在恢复后重新合成（见 12.4.1 节），这一要求还没有进入任何 Agent 框架的接口；四是**训练场景的放大效应**，RL 的 fork 与重放会把每个外部效果放大，因此训练环境应当把外部服务做成沙箱内状态（见 12.6 节），但"可写的外部服务模拟器"本身的保真度如何评估，同样是空白。工业界目前的主流策略是不让效果越界，事务化仍停留在研究阶段（见 12.8 节）。

### 28.3.3　其他几项方向的要点

**S1 与 S11 应当一起读。** 如果 arXiv 2605.17634 的论证成立，语义层防御在原理上就有一个无法消除的漏洞率。论文在情境完整性框架下提出一个两难：对手总能构造出让被阻断的信息流显得合理的情境，或者防御方收紧规范，就会阻断真正合法的流（"an adversary can always construct a context under which a blocked flow appears legitimate, or a defender who tightens norms will block genuinely legitimate flows"；论文自述）。这是安全与效用之间的两难，而不只是"对手总能得手"。这并不否定 CaMeL、FIDES、Progent 这类工作，而是改变了 OS 层的角色：OS 层不再是"语义层之外的另一道墙"，而是"语义层必然漏过之后的损害上限"（推断）。跨层能力传递的研究价值正在于此：如果语义层已经知道某个值来自不可信来源、只应流向某个工具，把这条信息编译成进程级的文件与网络规则，就能让 OS 层在语义层被绕过时仍执行同一意图。第 8 章提到的 Execute-Only Agents（LLM 只按工具 schema 写脚本，脚本在隔离沙箱中处理真实数据）与 Grimlock（每 agent 机密 VM 加 eBPF 强制流量经守卫 CVM）都是从 OS 一侧伸出的愿景论文，Grimlock 没有定量评估（见 8.6、8.7 节）。

**S2 与 S3 是两种不同的基准。** 强原语逃逸评测问的是"边界能不能被打穿"，对象是内核、VMM 与运行时；失准 agent 遏制基准问的是"模型在边界之内能做多少不该做的事"，对象是 .git、出站、包代理、harness 内部这些答案通道（见第 19 章五层通道）。生产证据几乎全落在后者：DSec §6.4、ExploitGym、Anthropic/Irregular 三组材料中，模型瞄准的都是答案通道与评测基础设施，而不是内核（见第 19、20 章）。SandboxEscapeBench 的饱和（v3 在每样本 1 亿 token 下 Mythos Preview 对全部样本至少成功一次，B20-22）说明前者也不能放下，但它的设计限定在已公开漏洞集合内，不覆盖新漏洞（B20-04）。一个可行的分工是：S2 由有安全研究能力的机构做，按算力–成功率曲线报告；S3 由拥有训练集群的团队做，按第 19 章的测量协议报告（本书建议）。

**S6 与 S7 都是"边界上的洞"。** 第 4 章归纳的本地 Agent 失效几乎都发生在策略管道：代理的字符串解析、按名字放行的"安全"命令、信任移交与能力型 socket；原语如实执行了规则，规则的语义与真实信任关系不一致（见 4.6 节）。第 14、15 章在训练侧看到的是同一类问题：白名单按名字放行，被允许的域名与包代理本身成了出站通道与写信道。这两项方向的研究对象因此不是更强的原语，而是**规则从意图到执行之间的翻译**：哪些配置文件会被沙箱外的谁执行，哪些被允许的目标上带着写能力与账号，凭据经代理附加之后被注入的 Agent 还能借它做什么（推断）。第 14 章的九条出站原则与第 15 章"把包通路从网络层搬到存储层"的建议，都还没有一条有效果测量。

**S12 把独立基准与远程证明连起来。** 第 20 章建议评测方连同分数发布"评测沙箱规格"，第 23 章建议的最小沙箱条款也要求声明档位与出站模式。但声明本身无法验证：读者无从确认某个分数确实是在声明的隔离档位、网络模式与镜像下取得的。TEE 的远程证明恰好适合回答"这台机器上运行的是哪个镜像、哪个配置"，它防的是运营方而不是模型（见 8.6 节），在这里反而对路（推断）。这一方向目前没有任何公开工作。

## 28.4　合流议题：遏制预算的联合优化

### 28.4.1　问题的提出

第 5、8、19 章从三个方向得出了同一个空白：RL 吞吐把隔离往轻处推，hacking 与逃逸证据把隔离往重处推，而两者之间没有任何测量（见 8.4 节）。第 14、19 章又发现，网络模式、harness 自我保护、算力上限对 hacking 的影响同样没有受控对照。本书把这几件事合起来，称为**遏制预算**（containment budget）的联合优化：隔离强度、出站控制、单 episode 算力上限、轨迹监控四个维度共同决定遏制效果，各自又有吞吐与成本代价，它们应当放进同一个模型里权衡，而不是由不同团队分别决定（本书建议）。

把它们放在一起的理由来自已有证据。SandboxEscapeBench 显示逃逸成功率随推理算力近似对数线性增长（B20-04），这意味着**算力上限本身是一个遏制参数**；Cursor 的严格 harness 同时改了 .git 与出站两个变量，使 Composer 2.5 在 SWE-bench Pro 上掉 20.7 分、Opus 4.6 掉不到 1 分（B19-02），这意味着**出站控制与隔离设置对不同模型的效果不同**；OpenAI 在沙箱控制之外加上了 CoT 监控与分级响应（见第 19、27 章），这意味着**监控是第四个可以花预算的维度**。DSec 按任务选档（SWE 与工具调用在容器，安全与 computer use 在 microVM），是在没有测量的情况下做出的一次手工权衡（见 5.6、24.2.2 节）。

**图 28-1** 把四个维度与三类结果画在一起。

```mermaid
flowchart LR
    subgraph IN["遏制预算的四个维度（各自有吞吐与成本代价）"]
        D1["隔离强度<br/>进程原语 / 容器 / gVisor / microVM / 完整 VM"]
        D2["出站控制<br/>离线 / 白名单预填充 / 白名单可代取 / 全开放；<br/>按任务阶段切换"]
        D3["单 episode 算力上限<br/>步数、token、墙钟时间"]
        D4["轨迹监控<br/>通道事件、金丝雀命中、CoT 监控、分级响应"]
    end
    J["联合优化<br/>（目前各维度由不同团队分别决定）"]
    subgraph OUT["需要同时报告的结果"]
        O1["吞吐与每千次 rollout 成本"]
        O2["污染奖励比例<br/>（正奖励中来自非预期通道的部分）"]
        O3["越界与逃逸事件率<br/>（区分尝试与成功）"]
    end
    D1 --> J
    D2 --> J
    D3 --> J
    D4 --> J
    J --> O1
    J --> O2
    J --> O3
    C["约束：构建期卫生、harness 自我保护<br/>（第 18、19 章的前置条件）"] -.-> J
```

**图 28-1　遏制预算的几个维度**（示意图，依据第 5、14、19、20 章材料绘制；维度划分与"联合优化"的提法为本书建议）

### 28.4.2　两项最基本的测量

这一联合优化问题的前提是两项最基本的测量，而它们目前都不存在。

**不同隔离档位下的 hacking 率。** 本书检索范围内，测量不同隔离档位下 reward hacking 率的研究数为 0（B28-02；笔者推算，文献检索结论）。DSec 只列举行为、不给比率（B19-13），Anthropic、OpenAI 也没有披露各档位下的发生率（见 27.10 节）。

**三档网络模式的受控对照。** 在同一模型、同一任务上对比离线、白名单、全开放三种网络模式的受控研究数同样为 0（B28-01；笔者推算，文献检索结论）。最接近的 Cursor 对照同时改了 .git 与出站两个变量。

第 19 章 19.6.2 节已经给出了一个可以直接复用的测量协议：按五层通道计数、在每条通道上放置金丝雀答案、用"`.git` × 网络 × harness 自我保护 × 隔离档位"的因子设计替代"标准 vs 严格"、报告污染奖励比例、把无解任务当作放大器指标、固定并报告算力上限、与隔离规格一起发布（本书建议）。本章在此基础上只补充一点：**算力上限应当作为第五个因子进入设计，而不只是一个被报告的常量**，因为它与隔离强度之间可能存在替代关系（例如更低的 token 上限是否能让容器档位"够用"更久），这正是遏制预算需要回答的问题（推断）。

### 28.4.3　为什么这件事难

难点不在实验设计，而在三个现实约束（推断）。一是**成本**：因子设计的格数随因子数指数增长，每一格都要在前沿模型上跑足够多的 rollout 才能估计一个低频事件率。二是**伦理与安全**：在全开放网络或弱隔离档位下运行有逃逸能力的模型，本身就有外溢风险，SandboxEscapeBench 采用"沙箱套沙箱"正是为此，ExploitGym 与 Anthropic/Irregular 事件说明评测基础设施本身就是安全边界（见第 20 章）。三是**披露动机**：拥有生产训练集群的实验室最有条件做这项测量，但公开 hacking 率会暴露自家环境与模型的弱点；国内实验室公开训练侧设计、海外实验室公开事故，两边都没有公开系统性发生率（见第 26、27 章）。

### 28.4.4　一个最简的形式

> **本书建议**（以下是笔者提出的问题形式，用于说明"联合优化"指什么，不是任何来源的模型，也没有数据支撑其中任何参数）

把一次训练或评测的环境配置记为四元组：隔离档位 i、出站模式 n、单 episode 算力上限 b、监控配置 m。对每个配置，需要三类量：每千次 rollout 的成本 C(i, n, b, m)（含节点数、存储与监控开销）；污染奖励比例 P(i, n, b, m)，即正奖励中来自非预期通道的部分（见 19.6.2 节）；越界与逃逸事件率 R(i, n, b, m)，区分尝试与成功。遏制预算问题可以写成：在 P 不超过训练可容忍的上限、R 不超过组织可接受的上限的约束下，使 C 最小。

这个形式有三点用处（推断）。第一，它说明为什么"一律上最强档"不是答案：如果某类任务在容器档、预填充镜像、较低 token 上限下 P 与 R 已经低于阈值，升级到 microVM 只增加 C；DSec 让 SWE 任务留在容器档，本质上就是对这一点的押注（见 5.6 节）。第二，它说明为什么监控与隔离可以互相替代：在弱隔离下配合按通道计数与金丝雀，可能比在强隔离下不做监控更早发现污染。第三，它暴露了最大的未知量：P 和 R 随模型能力变化，SandboxEscapeBench 从"难度 4–5 为 0"到"全部样本至少成功一次"只隔了几个月和两个数量级的算力（B20-02、B20-22），任何一次测量得到的最优配置都有保质期。

因此，遏制预算不是一次性的设计决策，而应当像第 20 章的评测沙箱规格一样随模型版本重新评估，并把评估结果与模型一起记录（本书建议）。

## 28.5　学术社区信号

### 28.5.1　会议状态

2026 年与 Agent 沙箱直接相关的系统与安全工作，开始进入 OSDI、SOSP、ICML 等主会，但多数仍是预印本。表 28-3 按附录 B 与文献库登记，并注明本章的核实方式。

**表 28-3　2026 年相关工作的发表状态**

| 工作 | 主题 | 状态 | 本章核实方式 | 相关章 |
|---|---|---|---|---|
| RollArt | 解耦的多任务 Agentic RL | OSDI'26 | USENIX 演讲页（2026-10-05 复核） | 17、26 |
| YoloFS | 面向 Agent 的文件系统：暂存、快照、渐进权限 | SOSP'26 | SOSP'26 官方录用列表（2026-10-05 复核） | 11、12 |
| SkVM | skill 的语言 VM 与环境绑定 | SOSP'26 | 同上；录用题名为"Skill VM: Write Once, Run Everywhere Efficiently"，与 arXiv 2604.03088 题名不同 | 16、18 |
| AgileLog | 可 fork 的共享日志 | SOSP'26 | 同上；arXiv v1 正文已读：cFork/sFork 两类 fork，Bolt 上 fork 约 50 µs，1,000 个 cFork 元数据 8 MB | 12 |
| TensorHub | LLM RL 的权重传输 | SOSP'26 | 同上；仅题名 | 17 |
| AgenticOS@ASPLOS'26 | 第一届 Agent OS 研讨会 | 研究论文 7 篇、愿景论文 5 篇 | 工作坊页面（复核，按页面所列题名计数） | 3、8、11 |
| 第二届 AgenticOS | 同上 | 与 SOSP 2026 同期举办（2026-09-29，布拉格） | 工作坊首页（2026-10-05 复核） | — |
| SandboxEscapeBench | 容器逃逸能力基准 | ICML'26 Oral | ICML 2026 Oral 页（复核） | 5、20 |
| Reward Hacking Benchmark | 工具使用中的利用行为 | ICML'26 | arXiv 摘要页 comments（复核） | 19、20 |
| SWE-MiniSandbox | 无容器的 SWE RL | ICML'26 | arXiv HTML 脚注（PMLR 306，2026-10-05 复核） | 8、10 |
| AgentBound | MCP server 访问控制 | FSE 2026 | arXiv 摘要页（复核） | 8、16 |
| Rollout Infrastructure Tax | 四种执行底座对比 | SoCC'26 投稿预印本 | arXiv 摘要页 comments（2026-10-05 复核） | 6、17、22 |
| Cordon、Planarian、Atomix、ACRFence、AgentZip、CUA-Sandbox、DeltaBox | 事务、状态、密度、GUI | 预印本（ACRFence 为 CoDAIM'26 研讨会论文） | 沿用第 7、11、12、13 章 | 7、11、12、13 |
| DSec | 训练沙箱平台 | arXiv 2609.22978 预印本 | 沿用第 24 章 | 24 |

注：AgenticOS'26 的篇数按页面 Research Papers 与 Vision Papers 两节所列题名计数，与文献库 C28-08 一致。另有一场与 NeurIPS 2026 同期的 AgenticOS 研讨会（2026-12-12，悉尼；据征稿通知），届次页面未写明。

### 28.5.2　信号读法

从这张表可以读出三点（推断）。第一，**系统社区接受了"Agent 是一类新负载"这一判断**：OSDI'26 收了 RollArt，SOSP'26 收了 YoloFS、SkVM、AgileLog 与 TensorHub，ASPLOS'26 设了专门的工作坊，第二届与 SOSP 2026 同期举办。第二，**安全社区的进展集中在评测而不是防御**：ICML'26 的两项安全相关工作都是基准（SandboxEscapeBench、Reward Hacking Benchmark）；防御侧除 AgentBound（FSE 2026）外，事务与回滚类系统中 Cordon、Atomix 仍是预印本，ACRFence 为研讨会短文。第三，**训练沙箱本身几乎没有经过同行评审的论文**：DSec、AgentENV（无独立论文）、Kimi K3 的沙箱一节都是技术报告或仓库文档；进入主会的 RollArt 写的是 RL 系统，沙箱只是它的一个组件。例外是 SWE-MiniSandbox（ICML'26），但它是单一研究系统，规模（128 个并行环境）远小于生产负载（B08-10）。

**本书未覆盖的范围。** 目录列出的缺口仍然存在：OSDI'25、SOSP'25、ATC'25、EuroSys'26、NSDI'26 的程序没有系统扫描；SOSP'26 的四篇相关论文已据官方录用列表核实，但本书未逐条扫描该列表的全部论文。读者若要据此判断某一方向是否已有主会论文，应以会议官方程序为准。

## 28.6　给研究者的切入清单

### 28.6.1　最小可发表实验

> **本书建议**（以下为笔者基于全书材料的观点，不是任何来源的做法；"最小"指在单一研究组可承担的成本下能回答一个前文已确认的空白问题）

表 28-4 为表 28-1、表 28-2 中的 12 个方向各给出一个"最小可发表实验"。选择的标准是：问题在前文已被确认为空白；实验可以只用开源组件（AgentENV、CubeSandbox、OpenSandbox、Firecracker、gVisor、Harbor、SandboxEscapeBench 等）完成；结果无论正负都有发表价值，因为当前的基线是"没有数据"。

**表 28-4　最小可发表实验（本书建议）**

| 方向 | 问题 | 最小设置 | 主要指标 | 对应 |
|---|---|---|---|---|
| 隔离档位与 hacking | 换档会不会改变 hacking 率 | 一个开放权重模型、一组带金丝雀的 SWE 任务，在容器、gVisor、microVM 三档下各跑同一 seed 集合 | 每千次 rollout 各通道事件数（尝试 / 成功）；通过率；吞吐 | S8、E10、B28-02 |
| 网络模式对照 | 离线比白名单好多少，白名单比全开放好多少 | 同上任务集，网络取离线 / 白名单预填充镜像 / 白名单可代取镜像 / 全开放四档，其余固定 | 同上；经包通路的取回次数 | S6、B28-01 |
| 强原语逃逸 | gVisor、Firecracker 在固定算力下的实际强度 | 在 SandboxEscapeBench 的"沙箱套沙箱"框架内，把可移植场景迁到 gVisor 与 Firecracker，报告算力–成功率曲线 | 各预算下成功率；非预期路径数 | S2 |
| 抢占风暴 | 千级到万级沙箱同时暂停的代价 | 用 AgentENV 在小集群上构造 1,000 至 10,000 个沙箱的同步暂停与恢复 | 暂停 p50/p99；存储写带宽峰值；恢复后放置命中率 | E3 |
| 跨节点恢复 | 冷迁移的延迟随什么变化 | 测 AgentENV 经共享快照仓库的跨节点恢复，变化内存脏页量与可写层大小 | 端到端恢复延迟；传输字节数 | E2 |
| 外部副作用 | 事务化在崩溃与回滚下是否守住不变量 | 一组带模拟支付、邮件、工单的外部服务套件；注入崩溃与回滚；比较检查点重放、补偿、outbox 三类方案，并重演 ACRFence 的两类攻击 | 重复提交数；泄漏数；任务成功率；开销 | S4 |
| 跨层能力传递 | OS 层能否兜住语义层的漏 | 把一个语义层系统的工具策略翻译成 Landlock 与出站代理规则，人为关闭语义层后重跑 AgentDojo | 被 OS 层拦下的攻击比例；效用损失 | S1、S11 |
| 可写层去重 | 同模板派生的沙箱可写层有多少重复 | 记录一批 rollout 结束时的可写层与匿名内存，按块与页做跨沙箱去重统计 | 可去重比例；随 rollout 步数的变化 | E5 |
| token 一致性 | 重新分词漂移随轮数如何增长 | 在一个开源 RL 框架上对比 chat completion 与 token-in/token-out 两种接口 | 漂移样本比例随轮数的曲线 | E11 |
| env.reset 可靠性 | 突发创建下故障从哪里来 | 以 1、100、1,000 个并发 reset 的阶梯，比较全量拉取与按需加载 | reset 失败率；时延分布；磁盘峰值 | E4 |
| 快照唯一性 | fork 出的 GRPO 一组是否独立 | 从同一模板 fork 一组沙箱，统计随机种子、端口、临时文件名、密钥材料的重复 | 重复项数；测试顺序相关性 | E13 |
| 审批疲劳 | 绑定事务的审批是否降低危险批准 | 用户实验：逐命令审批与按事务、按效果类别审批两组 | 批准率；危险动作被批准的比例；任务时长 | S10 |

注：每项实验都应附带第 20 章"评测沙箱规格"中的隔离档位、网络模式、算力预算与镜像版本，使结果可以对照（本书建议）。

### 28.6.2　独立基准：统一口径测量方案

第 6 章 6.8 节承诺给出一套统一口径的测量方案（起止点、并发阶梯、空闲与满载两种内存口径、网络策略开关），作为表 28-1 中 E12 的一部分；第 22 章 22.10.4 节给出了面向采购的简版。以下是完整方案。**目前只有设计，没有任何测量结果**；成本与可行性尚未评估，是否执行、覆盖哪些厂商，将在后续版本中说明（本书建议）。

**一、固定规格与环境。** 沙箱规格固定为 2 vCPU / 4 GiB；固定区域、测试日期、厂商 SDK 与服务版本、所用模板或镜像（含大小与层数）；自建系统另记 VMM、guest 内核与宿主机型。所有结果附带这组元数据。

**二、起止点。** 冷启动以"客户端发起创建 API 调用"为起点、"沙箱内第一条命令的结果返回客户端"为终点（端到端），同时分段记录 API 返回时刻与沙箱内代理健康检查通过时刻。分别测三条路径并分开报告：从镜像启动、从模板快照恢复、从预热池领用。三条路径不得合并为一个"冷启动"数字（见第 6 章边栏"读一个'冷启动'数字时要问的五个问题"）。

**三、并发阶梯。** 以 1、100、1,000、10,000 个并发创建的突发阶梯测量，每级报告 p50、p99 与创建失败率；另做一组持续创建速率测试，逐级提高每秒创建数，直到失败率或 p99 越过预先声明的阈值为止，报告该速率。默认配额不足时，记录提额是否需要合同。

**四、两种内存口径。** 空闲口径：沙箱启动后静置一段固定时间，测每沙箱的宿主侧增量内存（同一宿主上 N 个沙箱的总内存减去基线，除以 N），自建系统同时报告 VMM 与 guest 两部分；满载口径：在沙箱内运行一组 CPU 密集的 RL 型负载（安装依赖、编译、跑测试），重复同样的测量。只报空闲口径会高估密度，只报满载口径会低估暂停的价值（推断）。

**五、网络策略开关。** 每项启动测量分别在"不下发网络策略"与"默认拒绝 + 若干条域名白名单"两种设置下各做一次，报告策略下发对创建延迟的影响；并做出站验证：向白名单外域名发起连接、尝试 DNS 外传、访问云元数据端点，记录是否被阻断（见第 14 章）。

**六、暂停与恢复。** 分别在 1、4、16 GiB 已写内存下测暂停–恢复往返时间，记录暂停期间的计费口径与保留内容（内存、磁盘、IP）。

**七、负载与成本。** 一组 CPU 稀疏的推理型负载（长时间等待、偶发工具调用）与一组 CPU 密集的 RL 型负载；按标价计算每千次 rollout 的成本，按活跃 CPU 计费的厂商另按 CPU 活跃度重算。

**八、披露与独立性。** 公开 harness 与原始数据；不接受被测厂商赞助；被测厂商可在发布前复核测试配置，但不得要求删改结果；记录每次测量的日期，结果随厂商版本失效。

这套方案只覆盖第 6、13、22 章关心的性能与成本，不覆盖安全。隔离强度的独立评测见表 28-2 的 S2 与 S12。

### 28.6.3　杠杆最大的三个方向

> **本书建议**（笔者对优先级的判断，依据是"一项结果能同时回答多少个前文空白"）

**第一，隔离档位 × 网络模式的因子实验。** 它一次回答 B28-01、B28-02 两个文献空白，直接服务于表 28-1 的 E10、表 28-2 的 S6 与 S8，也是遏制预算联合优化的第一组数据点。它不需要新系统，只需要现有开源组件、一个开放权重模型和足够的 rollout 预算；任何结果，包括"档位对 hacking 率没有显著影响"，都会改变 DSec 式按任务选档的依据（见第 5、24 章）。

**第二，抢占风暴与跨节点恢复的集群级测量。** 它同时回答 E2、E3 与 E5 的一部分，而且是 DSec 与 AgentENV 两份一手披露共同留下的空白（见 24.7、25.9 节）。AgentENV 的开源使这项测量第一次可以在学术环境里做：它已经实现了增量暂停、seal-and-restack 与跨节点冷恢复，缺的是在千级沙箱同时暂停时的数字。

**第三，外部服务套件与事务语义的对抗评测。** S4 已有 Planarian、Cordon、Atomix、ACRFence 等多个设计，缺的是一套共同的评测基础：可写、可观察、可注入故障的外部服务模拟器，加上 ACRFence 式的回滚攻击用例。有了它，现有系统的保证才能在同一组不变量下比较；它同时服务于训练场景"把外部服务做成沙箱内状态"的需求（见 12.6 节）。

这三项之外，统一口径测量方案（28.6.2 节）是全书多数数字从"厂商自报"走向"可比较"的前提，但它更适合由不受厂商资助的第三方长期维护，而不是作为一次性论文发表（推断）。

## 本章小结

- **八个趋势。** Agent 沙箱是独立负载类别；存储取代原语成为竞争点；暂停是成本杠杆；rollout 状态外置；接口在生命周期层与环境语义层两层标准化；披露转向运维指标；Agent 自动化环境构建；竞争对手在底层开源协作（DSec 的 microVM 存储路径使用了 AgentENV 仓库中开源的 Rust OverlayBD/ublk 组件，论文称"我们参与贡献"；TrEnv → AgentENV → DSec 为推断，基于作者重合）。
- **标准的位置。** 沙箱与隔离已写入非强制的实践指南和实验室治理框架（TC260 开发安全指南征求意见稿第 8 章 n）项与《智能体部署使用安全指引》、五眼联合指南、DeepMind FSF v3.1、OpenAI Frontier Governance Framework 等），但尚未进入任何强制性标准或法规。
- **13 项工程问题。** 可扩展放置、跨节点 fork 与在线迁移、抢占风暴下的暂停一致性、env.reset 可靠性、可写层去重、GUI 密度、GPU 沙箱、云上与嵌套虚拟化、网络策略的表达、reward hacking 的系统化检测、token 一致性、独立基准、可复现性，第 3–27 章的其余空白条目均已归并进来（归并关系见 28.2.1 节）。
- **12 项安全线方向。** 跨层能力传递、强原语逃逸评测、失准 agent 遏制基准、外部副作用回滚、可验证的策略合成、出站与凭据、信任移交、RL 沙箱的安全与吞吐权衡、computer-use 隔离、审批疲劳、语义防御的理论极限、独立基准加 TEE。
- **外部副作用回滚以第 12 章为准。** Planarian、Cordon、Atomix 均为预印本，ACRFence 为研讨会短文，工业界没有一手的事务实践。
- **合流议题。** 隔离强度、出站控制、单 episode 算力上限、轨迹监控应当作为遏制预算联合优化；它的两项前提测量，即不同隔离档位下的 hacking 率与三档网络模式的受控对照，目前都不存在（B28-01、B28-02）。
- **学术信号。** RollArt（OSDI'26），YoloFS、SkVM、AgileLog、TensorHub（SOSP'26 官方列表），SandboxEscapeBench（ICML'26 Oral），Reward Hacking Benchmark 与 SWE-MiniSandbox（ICML'26），AgentBound（FSE 2026）的状态均已核实，第二届 AgenticOS 与 SOSP 2026 同期举办。
- **训练沙箱缺少同行评审。** 多数 2026 年工作仍是预印本，训练沙箱本身几乎没有经过同行评审的论文（SWE-MiniSandbox 是规模很小的例外）。
- **切入清单与测量方案。** 表 28-4 的 12 个最小可发表实验与 28.6.2 节的统一口径测量方案都是本书建议，目前没有任何测量结果。

## 本章数字溯源

本章原则上不新增数字，以下数字均沿用前文与附录 B。"核对"一列：**复核**＝2026-10-05 本章回一手原文核对；**沿用**＝依据前文已核对文本与附录 B，本章未再回原文。

**表 28-5　本章数字溯源**

| 数字 | 含义 | 来源 | 类型 | 核对 | 附录 B |
|---|---|---|---|---|---|
| 4.2%–13.3% | DSec 运行时实际访问的镜像数据比例 | DSec 表 3 | 论文自述 | 沿用（第 3、10 章） | B03-09 |
| 最多 98% | 等待推理占沙箱寿命 | K3 §5.3.2 | 论文自述 | 沿用（第 3、11 章） | B03-10 |
| 自 V4.1 起 | rollout 状态移到 DSec | DSec §6.2 | 论文自述 | 沿用（第 17 章） | B17-01 |
| 约每十次迭代；78%；> 99.99% | env.reset 超时频率；超时迭代中 env.reset 占比；多级缓存后成功率 | RollArt §3.1 | 论文自述 | 沿用（第 3、10 章） | B10-14 |
| 约 16% | 含沙箱可归因故障的轨迹比例 | KAT-Coder-V2.5 §4.2.2 | 论文自述 | 沿用（第 18 章） | B18-02 |
| 约 95%；约 6%–7% → 低于 1% | 快手优化前峰值磁盘占用；超时无效 rollout | KAT-Coder-V2.5 | 论文自述 | 沿用（第 10 章） | B10-15 |
| 16.5% → 57.2%；40%；超过 90% | 快手、阶跃、GLM-5 环境构建成功率 | 各技术报告 | 论文自述 | 沿用（第 18 章） | B18-01、B18-17、B18-08 |
| 超过 5,000 个/秒；约 34.7 个/秒 | DSec 峰值创建能力；日均创建速率 | DSec §2.4；3,000,000 ÷ 86,400 | 论文自述；笔者推算 | 沿用（第 9、24 章） | B24-06、B24-14 |
| 约 70 个/秒 | agent-sandbox 默认配置下 Pod 调度速率 | agent-sandbox `docs/performance-tuning.md` | 一手文档 | 沿用（第 9 章） | B09-09 |
| 100 | AgentENV fork 上限 | AgentENV OpenAPI 与代码 | 一手文档 | 沿用（第 11、25 章） | C-02 |
| 中位 0.71 s | Crab 单沙箱 spot 迁移 | Crab | 论文自述 | 沿用（第 11 章） | B11-26 |
| 32K | DSec 单作业最多请求的沙箱数 | DSec §1 | 论文自述 | 沿用（第 10、11 章） | B03-01 |
| 峰值 −40.2% | DSec pmem DAX 宿主峰值内存 | DSec | 论文自述 | 沿用（第 13 章） | B13-04 |
| 8.7 倍；2.1 倍；3.1 倍 → 1.40 倍 | AgentZip 内存降低；Linux 配置；减速 | AgentZip 摘要 | 论文自述 | 沿用（第 13 章） | B13-10 |
| 6.20 倍；9.2 倍 | CUA-Sandbox 吞吐（最高）与每环境内存（VWA、8 并发） | CUA-Sandbox §4.3 | 论文自述 | 沿用（第 7 章） | B07-06 |
| 约 400 MB | MobileGym 单实例内存 | MobileGym | 论文自述 | 沿用（第 7 章） | B07-07 |
| CVSS 9.0 | NVIDIAScape | Wiz；emirb | 二手报道 | 沿用（第 5 章） | B05-02 |
| 30 TB；70% | DSec 云突发覆盖的镜像集合与容器任务比例 | DSec §3.4 | 论文自述 | 沿用（第 24 章） | B09-02 |
| 63% | Cursor 审计中取回而非推导的比例 | Cursor 博客 | 一手文档 | 沿用（第 19 章） | B19-01 |
| 54% | ImpossibleBench 上 GPT-5 的作弊率（Conflicting-SWEbench） | arXiv 2510.20270 | 论文自述 | 沿用（第 19 章） | B19-06 |
| 约 200 轮；约 40% | 重新分词漂移影响的样本比例 | KAT-Coder-V2.5 | 论文自述 | 沿用（第 17 章） | B17-10 |
| 26；28 | Terminal-Bench 2.1 修订任务数（两处一手冲突） | 仓库 README；tbench.ai | 一手文档 | 沿用（第 20、27 章） | C-49 |
| 128 个 | SWE-MiniSandbox 并行环境数 | SWE-MiniSandbox | 论文自述 | 沿用（第 8 章） | B08-10 |
| 77% 对 84% | CaMeL 可证明安全完成率与无防御 | CaMeL 摘要 | 论文自述 | 沿用（第 8 章） | B02-05 |
| 250 万 token；难度 4–5 为 0 | SandboxEscapeBench 原始预算与结果 | arXiv 2603.02277 §5.1 | 论文自述 | 沿用（第 5、20 章） | B20-02 |
| 1 亿 token；全部样本 | v3 预算；Mythos Preview 至少成功一次的样本 | arXiv 2603.02277v3 | 论文自述 | 沿用（第 20 章） | B20-22 |
| 近似对数线性 | 逃逸成功率随推理算力的变化 | arXiv 2603.02277 | 论文自述 | 沿用（第 20 章） | B20-04 |
| 141,006 次；3 起 | Anthropic 复查的评测运行与事件 | Anthropic 事故页 | 一手文档 | 沿用（第 20 章） | B15-07 |
| 最多 15 倍；3% | Planarian 任务质量提升；错误恢复开销 | Planarian 摘要 | 论文自述 | 复核（alphaXiv 摘要） | B12-01 |
| 37%–57%；0–7% | Atomix v1 成功率与基线 | Atomix v1 | 论文自述 | 沿用（第 12 章） | B12-02 |
| 0/500；80%；40% | Atomix v2 泄漏数与 Saga、Checkpoint-Replay 泄漏率 | Atomix v2 表 2 | 论文自述 | 沿用（第 12 章） | B12-09 |
| 45/45；4.17 ms | Cordon 提交前拦截数；回滚中位 | Cordon §6.2、§6.3 | 论文自述 | 沿用（第 12 章） | B12-10、B12-12 |
| 10/10；2/2 | ACRFence 动作重放与令牌复用 | ACRFence §3 | 论文自述 | 沿用（第 12 章） | B12-15 |
| 约 50 µs；8 MB 对 4.4 GB | AgileLog（Bolt）fork 延迟（与日志长度无关）；1,000 个 cFork、100 万条记录时的元数据内存与朴素实现 | AgileLog arXiv v1 §6.1、§6.5 | 论文自述 | 复核（arXiv v1 PDF，WebFetch） | B28-04 |
| 296 个；80.9% | AgentBound MCP server 数与自动策略准确率 | AgentBound 摘要 | 论文自述 | 复核 | B16-06 |
| 84%；约 93% | Claude Code 权限提示减少比例；此前批准比例 | Anthropic 工程博文 | 一手文档 | 沿用（第 4 章） | B04-01 |
| 约 33%；约 14%；216 条 | OSWorld 2.0 绕开界面的任务、提取隐藏状态的任务、轨迹数（两比例原文均为 of tasks） | OSWorld 2.0 | 论文自述 | 沿用（第 19 章） | B19-12 |
| 4 倍 | DSec 每节点容器与 microVM 能力比（3,200 ÷ 800） | 由 B13-01 推算 | 笔者推算 | 沿用（第 5、13 章） | B13-01 |
| 20.7 分；不到 1 分 | Cursor 严格 harness 下 Composer 2.5 与 Opus 4.6 的降幅 | Cursor 博客 | 一手文档 | 沿用（第 19 章） | B19-02 |
| 0 项；0 项 | 三档网络模式受控研究数；隔离档位 hacking 率研究数 | 文献检索结论 | 笔者推算 | 沿用 | B28-01、B28-02 |
| 7 篇；5 篇 | AgenticOS@ASPLOS'26 研究论文与愿景论文数 | 工作坊页面 | 一手文档 | 复核（按 Research Papers / Vision Papers 两节所列题名计数） | B28-03；文献库 C28-08 |
| 2 vCPU / 4 GiB；1、100、1,000、10,000；1、4、16 GiB | 测量方案的规格、并发阶梯与暂停测试内存档 | 本书建议 | — | — | 不登记（方案参数） |

## 参考文献

本章汇总前文，多数条目的完整信息见各章参考文献；以下只列本章直接引用或复核的来源。

[1] DeepSeek-AI. *DeepSeek Elastic Compute (DSec): A Sandbox Infrastructure for Effective Agentic Training at Scale*. arXiv:2609.22978v1, 2026-09，预印本. https://arxiv.org/html/2609.22978v1

[2] Moonshot AI. *Kimi K3 Technical Report*. arXiv:2607.24653, 2026-07. https://arxiv.org/pdf/2607.24653

[3] kvcache-ai. AgentENV（仓库与 README）. https://github.com/kvcache-ai/AgentENV

[4] Wei Gao, et al. *RollArt: Disaggregated Multi-Task Agentic RL Training at Scale*. OSDI 2026. https://www.usenix.org/conference/osdi26/presentation/gao ；arXiv:2512.22560 https://arxiv.org/html/2512.22560v1

[5] Kuaishou KAT Team. *KAT-Coder-V2.5* 技术报告. arXiv:2607.05471. https://arxiv.org/html/2607.05471v1

[6] Jinnan Guo, Hao Mark Chen, Kapil Vaswani, Andrew Paverd, Peter Pietzuch. *Planarian: Managing Agent State with Statepoints*. arXiv:2609.35366, 2026-09-28，预印本. https://arxiv.org/abs/2609.35366 ；alphaXiv https://www.alphaxiv.org/abs/2609.35366

[7] Bardia Mohammadi, et al. *Atomix: Timely, Transactional Tool Use for Reliable Agentic Workflows*. arXiv:2602.14849（v1 2026-02-16，v2 2026-05-29），预印本. https://arxiv.org/abs/2602.14849

[8] Zheng Chen, et al. *Cordon: Semantic Transactions for Tool-Using LLM Agents*. arXiv:2606.17573v1, 2026-06-16，预印本. https://arxiv.org/html/2606.17573v1

[9] Yusheng Zheng, Yiwei Yang, Wei Zhang, Andi Quinn. *ACRFence: Preventing Semantic Rollback Attacks in Agent Checkpoint-Restore*. arXiv:2603.20625v1, 2026-03-21；CoDAIM 2026（ASPLOS 2026 研讨会，2026-03-23 报告；据研讨会日程页）. https://arxiv.org/abs/2603.20625 ；https://codaim-asplos.github.io/schedule.html

[10] Shawn (Wanxiang) Zhong, et al. *Don't Let AI Agents YOLO Your Files*（YoloFS）. arXiv:2604.13536v2；SOSP'26. https://arxiv.org/html/2604.13536v2

[11] Shreesha G. Bhat, Tony Hong, Michael Noguera, Ramnatthan Alagappan, Aishwarya Ganesan. *AgileLog: A Forkable Shared Log for Agents on Data Streams*. arXiv:2604.14590v1（PDF 标注 16 Apr 2026）；SOSP'26. https://arxiv.org/pdf/2604.14590 ；https://www.alphaxiv.org/abs/2604.14590

[12] Le Chen, Erhu Feng, Yubin Xia, Haibo Chen. *SkVM: Revisiting Language VM for Skills across Heterogenous LLMs and Harnesses*（SOSP'26 录用题名 *Skill VM: Write Once, Run Everywhere Efficiently*）. arXiv:2604.03088. https://arxiv.org/abs/2604.03088

[13] SOSP 2026 Accepted Papers（官方录用列表）. https://www.sigops.org/s/conferences/sosp/2026/accepted.html ；另见 Paul Chaignon, ACM SOSP'26 Papers & Preprints, 2026-08-03, https://pchaigno.github.io/academic/2026/08/03/sosp-2026-papers.html

[14] 1st AgenticOS Workshop @ ASPLOS 2026. https://os-for-agent.github.io/asplos-2026.html ；第二届（与 SOSP 2026 同期）见工作坊首页 https://os-for-agent.github.io/

[15] Rahul Marchand, et al.（UK AISI）. *Quantifying Frontier LLM Capabilities for Container Sandbox Escape*（SandboxEscapeBench）. arXiv:2603.02277（v3 2026-08-01）；ICML 2026 Oral. https://arxiv.org/html/2603.02277v1 ；https://icml.cc/virtual/2026/oral/71104

[16] Kunvar Thaman. *Reward Hacking Benchmark: Measuring Exploits in LLM Agents with Tool Use*. arXiv:2605.02964；ICML 2026. https://arxiv.org/abs/2605.02964

[17] Danlong Yuan, et al. *SWE-MiniSandbox: Container-Free Reinforcement Learning for Building Software Engineering Agents*. arXiv:2602.11210；ICML 2026. https://arxiv.org/html/2602.11210

[18] Christoph Bühler, et al. *AgentBound: Securing Execution Boundaries of AI Agents*. FSE 2026；arXiv:2510.21236. https://arxiv.org/abs/2510.21236

[19] Edoardo Debenedetti, et al. *Defeating Prompt Injections by Design*（CaMeL）. arXiv:2503.18813. https://arxiv.org/abs/2503.18813

[20] Manuel Costa, et al. *Securing AI Agents with Information-Flow Control*（FIDES）. arXiv:2505.23643. https://arxiv.org/abs/2505.23643

[21] Rahul Tiwari, Dan Williams. *Execute-Only Agents: Architectural Defense Against Prompt Injection for AI Agents*. AgenticOS @ ASPLOS 2026. https://os-for-agent.github.io/papers/AgenticOS_2026_paper_21.pdf

[22] Qiancheng Wu, et al. *Grimlock: Guarding High-Agency Systems with eBPF and Attested Channels*. AgenticOS @ ASPLOS 2026. https://os-for-agent.github.io/papers/AgenticOS_2026_paper_23.pdf

[23] Sahar Abdelnabi, Eugene Bagdasarian. *AI Agents May Always Fall for Prompt Injections*. arXiv:2605.17634, 2026-05-17，预印本. https://arxiv.org/abs/2605.17634

[24] Lukas Pirch, et al. *Toward Securing AI Agents Like Operating Systems*. arXiv:2605.14932, 2026-05，预印本. https://arxiv.org/abs/2605.14932

[25] Mihai Christodorescu, Earlence Fernandes, et al. *Systems Security Foundations for Agentic Computing*. arXiv:2512.01295, 2025-12，预印本. https://arxiv.org/abs/2512.01295

[26] Mengming Li, et al. *Memory Compression for High-Fanout Agent Sandboxes*（AgentZip）. arXiv:2609.11294，预印本. https://arxiv.org/abs/2609.11294

[27] Xin Yan, …, Yang You. *CUA-Sandbox: Efficient Environments for Computer-Use Agent Reinforcement Learning*. arXiv:2609.32750, 2026-09-26（预印本；通讯作者 Xingrui Yu；全文据作者仓库所附 PDF） https://github.com/windskyyx/CUA-Sandbox-Efficient-Environments-for-Computer-Use-Reinforcement-Learning ；https://arxiv.org/abs/2609.32750

[28] MobileGym. arXiv:2605.26114. https://arxiv.org/html/2605.26114

[29] Crab. arXiv:2604.28138. https://arxiv.org/abs/2604.28138

[30] Cursor. Reward hacking in coding benchmarks. 2026-06-25. https://cursor.com/blog/reward-hacking-coding-benchmarks

[31] ImpossibleBench. arXiv:2510.20270. https://arxiv.org/abs/2510.20270

[32] OpenAI. The Hugging Face incident and the road ahead. 2026-08-26. https://openai.com/index/hugging-face-incident-and-the-road-ahead/

[33] Anthropic. Investigating incidents in cybersecurity evals. 2026-07-30. https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals

[34] OSWorld 2.0. arXiv:2606.29537. https://arxiv.org/html/2606.29537v1

[35] Daniel Thi Graviet, et al.（Daytona）. *The Rollout Infrastructure Tax in Coding-Agent Reinforcement Learning*. arXiv:2607.01415，SoCC'26 投稿预印本. https://arxiv.org/abs/2607.01415

[36] 全国网络安全标准化技术委员会. 《网络安全标准实践指南——智能体系统开发安全指南（征求意见稿）》. 2026-09-18. 通知页 https://www.tc260.org.cn/tc260/tzgg/202609/e5b82ae7aca244d19d36b39575cbb458.shtml （附件 PDF 链接见第 23 章参考文献）

[37] ASD's ACSC, CISA, NSA, CCCS, NCSC-NZ, NCSC-UK. *Careful adoption of agentic AI services*. 2026-05-01. https://www.cyber.gov.au/sites/default/files/2026-05/careful_adoption_of_agentic_ai_services.pdf

[38] Google DeepMind. *Frontier Safety Framework* v3.1. 2026-04-17. https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/strengthening-our-frontier-safety-framework/frontier-safety-framework_3-1.pdf

[39] OpenAI. *Frontier Governance Framework*. 2026-05-28. https://cdn.openai.com/pdf/e37d949b-8c9f-4d76-b99e-4272f4631a7e/openai-frontier-governance-framework.pdf

[40] 国家标准化管理委员会. 关于下达《智能体应用安全基本要求》等 29 项强制性国家标准计划和相关标准外文版计划的通知（国标委发〔2026〕41 号）. 2026-06-27.（链接见第 23 章参考文献）
