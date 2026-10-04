# 审校者简报（AgentENV 手册）

你是这本书的一位审校者，负责一组已写完的篇目。目标：让它们达到 `agentenv/STYLE.md` 的标准，并与相邻篇目一致。
你可以**直接修改**分配给你的篇目；不要改别的篇目、不要改 OUTLINE.md / STYLE.md / README.md。

本简报里的路径都相对于本仓库根（`git rev-parse --show-toplevel`）；代码基线在 `.src/`（见 WRITER-BRIEF）。不要 git commit。

## 先读

1. `agentenv/STYLE.md`（全文，尤其第二节称谓与第五节自检清单）
2. `tools/briefs/agentenv/WRITER-BRIEF.md`（代码基线路径与 diff 命令）
3. `agentenv/OUTLINE.md` 中你负责篇目的要点
4. `tools/briefs/agentenv/review-notes.md` 中与你负责篇目有关的条目

## 逐篇做的事

1. **结构与体例**：标题格式 `# NN · 标题`、题注块、`## 0.`、`## N. 小结`、`## 延伸阅读 / 下一篇` 齐全；
   二级标题带数字；无四级标题；无 emoji、感叹号、「显然」、宣传腔；无过程叙事；**无性能数字**。
2. **篇幅**：汉字 3000–5000（用 WRITER-BRIEF 里的统计命令）。过短就补（读代码补内容，不注水）；过长就删冗余。
3. **代码论断抽查**：随机抽 8 条涉及行为的论断，到对应基线里核实。错的改掉；核实不了的改成「推论：」。
   特别留意：函数名、类型名、文件路径是否真实存在（用 grep 查）；把 AENV 补丁版 Firecracker 的端点写成上游就有；
   把 AgentENV 扩展的 overlaybd 格式写成与上游兼容；把文档（`docs/src/**`）的说法当成代码事实；
   把 POSIX 仓库与对象存储仓库的一致性保证混为一谈。
4. **术语与称谓**：对照 STYLE.md 第二、三节统一。
5. **交叉链接**：运行 `python3 tools/mdlinks.py agentenv/<file>`；对已存在的目标篇补上小节锚点（先读目标篇的标题）；
   修掉指向不存在文件的链接（只允许 OUTLINE 里的文件名）。另外两本手册的链接只允许出现在「延伸阅读」。
6. **图**：运行 `node tools/mdmermaid.mjs agentenv/<file>` 与 `tools/figcheck.sh --png .src/figs/<篇号> agentenv/<file>`，
   修掉 FAIL 与 WARN（画法见 `agentenv/FIGURE-GUIDE.md`）；打开 PNG 看图是否真的帮助理解。
7. **「本篇要回答的问题」**：每个问题正文都要有明确回答；没有的补上或删掉问题。
8. **「与 e2b infra 的对照」小节**：若有，不超过四句、不评优劣、e2b 侧论断与 e2b 手册一致；没有明显差异的篇目不该有。
9. **与相邻篇目的重复**：读相邻篇目，若大段重复，保留一处、另一处改为「回顾 + 链接」。
   已知容易重复的组合：27 / 42（暂停与恢复）、26 / 41（块设备）、31 / 51（卷与 fork）、43 / 49（startup pack）、17 / 13（代理鉴权）、55 / 17（两层反向代理）。

## 交付

在最终回复里列出：每篇改了什么（3–5 条）、发现但没改的问题（需要别的篇目配合的）、最终汉字数与 figcheck 结果。
