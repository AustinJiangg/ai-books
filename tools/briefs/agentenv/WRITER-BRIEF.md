# 编写者简报（AgentENV 手册，每位章节编写者必读）

你是一本教材式技术手册的**一篇**的作者。这本书讲 AgentENV（kvcache-ai/AgentENV，tag v0.2.3）——
一个为 agent 环境设计、E2B 兼容的 Firecracker 沙箱平台，以及它依赖的 AENV 补丁版 Firecracker。
读者是美国顶级大学计算机专业本科高年级与研究生：懂操作系统、存储、网络、分布式系统的基本概念，
但不一定接触过 io_uring、ublk、overlaybd、Firecracker、Rust 异步。主语言中文，技术名词按需用英文。

本简报里的路径都相对于本仓库（e2b-book）根目录。先 `cd "$(git rev-parse --show-toplevel)"`。

## 你必须先读的文件

1. `agentenv/STYLE.md` —— 体例、术语、称谓、自检清单。**逐条遵守。**
2. `agentenv/OUTLINE.md` —— 找到你这一篇的要点（讲什么 / 代码 / 图表），
   并读一遍**前后相邻篇目**的要点，避免重复、便于交叉引用。要点里标「确认」的地方必须到代码里核实。
3. `agentenv/FIGURE-GUIDE.md` —— 图的阈值与画法。
4. 风格样例：`firecracker/12-vmm-event-loop-and-exit.md` 与 `e2b-infra/37-pause-and-snapshot.md`
   （另外两本手册的篇目；读它们的写法与图的用法，不要引用它们的内容，除非你的篇目要点明确要求）。
5. 规划阶段的调研笔记 `tools/briefs/agentenv/survey/`（按区域分五份，索引见其 `README.md`）：读你这一篇对应区域的那一份。
   它给出模块地图、函数名与已知问题，能省下大半摸索时间；但它**不是依据**，正文里的每条论断仍要你自己读代码确认。
6. `tools/briefs/agentenv/review-notes.md` 中与你的篇目有关的条目（多篇口径要一致的事项）。

## 代码基线（读代码时只用这些路径）

| 基线 | 路径 |
|---|---|
| AgentENV v0.2.3 | `.src/agentenv/`（tag `v0.2.3`，commit `6cccaa7842bd`）|
| AENV 补丁版 Firecracker | `.src/fc-aenv/`（tag `aenv-deps`，commit `90288c39`）；差异：`git -C .src/fc-aenv diff v1.15.1 aenv-deps -- <path>`；提交：`git -C .src/fc-aenv log --stat v1.15.1..aenv-deps` |
| 上游 Firecracker v1.15.1 | 同一 clone 的 tag `v1.15.1`：`git -C .src/fc-aenv show v1.15.1:<path>` |
| e2b infra 2026.09（对照） | `.src/e2b-infra/`（tag `2026.09`）；**优先读 e2b 手册** `e2b-infra/` |
| 上游 overlaybd（只为核实格式兼容） | `.src/overlaybd-upstream/` |

`.src/` 不入库。若不存在，运行 `tools/fetch-sources.sh`（已存在的目录不重复拉取）。**不要 checkout 别的版本**，也不要修改 `.src/` 里的任何文件。

写第 65、66 篇与「与 e2b infra 的对照」小节时，e2b 侧的论断以 e2b 手册为依据；手册里没有的才读 `.src/e2b-infra/` 的代码。
写第 03、42、67 篇时读 fc-aenv 的 diff；其它篇目只在要点让你看时看 Firecracker 代码。

不要把 kvcache-ai/firecracker 的 `v1.15.1-patch`（`patch-v2`）、`v1.15.1-patch-nestedvirt`、`v1.16.1-patch` 分支当基线。
`.src/agentenv/docs/src/**` 与 `AGENTS.md` 是参考，不是依据：调研已发现多处与代码不符，以代码为准。

## 写作要求（STYLE.md 的浓缩，冲突时以 STYLE.md 为准）

- 结构：`# NN · 标题` → 题注引用块（一到三句 + 读者 / 预备 / 代码）→ `## 0. 本篇要回答的问题` →
  正文各节 `## 1.` … →（可选）`## N. 与 e2b infra 的对照` → `## N. 小结` → `## 延伸阅读 / 下一篇`。
- 正文 3000–5000 汉字（不含代码块与表格）。附录篇（69–73）以表格为主，不受下限约束。
- **每个行为论断都要读过代码**，给出仓库相对路径 + 函数名（`src/orchestrator/service.rs` 的 `launch_sandbox()`）；
  读不到、拿不准的标「推论：」。不要凭对 E2B 或 Firecracker 的印象写 AgentENV 的行为。
  正文里的路径相对于 AgentENV（或 firecracker）仓库根，**不出现 `.src/`**，不写行号。
- 称谓：只用「AgentENV v0.2.3」「AENV 补丁版 Firecracker」「上游 Firecracker v1.15.1」「Rust 版 overlaybd」「上游 overlaybd」「overlaybd 工具」「e2b infra」。
  补丁版 Firecracker 的行为不要写成上游就有；AgentENV 扩展的格式（Hybrid RW、`PMIDX001`、`OBCH`、`AENVMF01`）不要写成与上游兼容。
- 先讲问题再讲方案；代价与收益成对；不写宣传腔；不用「显然」；不用 emoji 与感叹号。**不给性能数字**，README 里的宣称也不引用。
- 图：mermaid 内嵌，1–3 张，节点 ≤ 20，标签用 `A["..."]` 形式，标签里不要有未转义的括号 / 引号 / 竖线；
  目录、字节布局、位域用 ```text。**图必须在 `tools/figcheck.sh` 下 PASS**
  （尤其：直线长链拆列、状态机改 flowchart + 编号表、时序图 ≤ 6 参与者 ≤ 14 消息）。
- 交叉引用只链接 OUTLINE 里存在的文件名：`[第 42 篇 · 内存快照](42-memory-snapshot-over-ublk.md)`。
  目标篇已经存在于 `agentenv/` 时可以加小节锚点（先读它的标题确认锚点）；不存在时只链文件。
  另外两本手册只在「延伸阅读」里链接（写法见 STYLE.md 第二节）。
- 不写过程叙事、不写「我们决定」。代码注释里出现的 issue 号、人名、内部称呼不要照搬，翻译成设计取舍。
- 技术债如实写，语气中性；同时把它记进交付说明，供第 68 篇汇总。

## 交付

1. 把文档写到 `agentenv/<你的文件名>`。只写分配给你的文件，不改别的文件（OUTLINE / README / STYLE / review-notes 都不要动）。不要 git commit。
2. 写完后自检：
   ```bash
   python3 tools/mdlinks.py agentenv/<你的文件名>
   node tools/mdmermaid.mjs agentenv/<你的文件名>
   tools/figcheck.sh --png .src/figs/<你的篇号> agentenv/<你的文件名>
   ```
   MISSING-FILE 对尚未写的篇目是正常的；其它问题要修掉。figcheck 每张图必须 PASS；WARN 就改图（拆列、缩短标签、减少节点）。
   用 Read 工具打开 `.src/figs/<你的篇号>/` 下的 PNG 看一遍，figcheck 通过但看着别扭的也要改。
3. 统计汉字数：`python3 -c "import re,sys;t=open(sys.argv[1],encoding='utf-8').read();t=re.sub(r'\x60\x60\x60.*?\x60\x60\x60','',t,flags=re.S);t=re.sub(r'^\|.*$','',t,flags=re.M);print(len(re.findall(r'[一-鿿]',t)))" agentenv/<你的文件名>`
4. 在最终回复里给出**交付说明**（每篇不超过 250 字）：核心论断清单、标为推论的地方、发现的与大纲不符之处、
   发现的技术债 / 文档漂移（给第 68 篇）、建议其它篇目补充或修改之处、汉字数、figcheck 结果。
