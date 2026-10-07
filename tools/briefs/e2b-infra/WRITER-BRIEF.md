# 编写者简报（每位章节编写者必读）

你是一本教材式技术手册的**一篇**的作者。这本书讲 e2b 服务端基础设施（e2b-dev/infra，tag 2026.09）
及其 aarch64 适配版。读者是美国顶级大学计算机专业本科高年级与研究生：懂操作系统、网络、分布式系统的
基本概念，但不一定接触过 KVM、userfaultfd、Firecracker、Nomad。主语言中文，技术名词按需用英文。

## 你必须先读的三份文件

1. `/home/austin/projects/e2b-repo/e2b-book/e2b-infra/STYLE.md` —— 体例、术语、口径、自检清单。**逐条遵守。**
2. `/home/austin/projects/e2b-repo/e2b-book/e2b-infra/OUTLINE.md` —— 找到你这一篇的要点（讲什么 / 代码 / 图表），
   并读一遍**前后相邻篇目**的要点，避免重复、便于交叉引用。
3. 风格样例：`/home/austin/projects/e2b-repo/e2b-infra-docs/rollback/docs/07-dirty-page-tracking.md`
   （另一本手册的一篇；读它的写法，不要引用它的内容，除非你的篇目要点明确要求）。

## 代码基线（读代码时只用这些路径）

| 基线 | 路径 |
|---|---|
| 上游 2026.09 | `/home/austin/projects/e2b-repo/tmp/e2b-book-src/upstream/` |
| ARM 适配版（infra 补丁后） | `/home/austin/projects/e2b-repo/tmp/e2b-book-src/arm/` |
| ARM 补丁本身（diff） | `git -C /home/austin/projects/e2b-repo/infra-arm diff f8c2f0cde fbee6fcd1 -- <path>` |
| 分叉 Firecracker（ARM） | `/home/austin/projects/e2b-repo/tmp/e2b-book-src/kasandbox-arm/firecracker/` |
| 内核配置 | `/home/austin/projects/e2b-repo/fc-kernels-arm/` |
| 单机离线版 | `/home/austin/projects/e2b-repo/e2b-infra/`（spec、`e2b-deploy/`、`deploy-docs/`、`benchmark/`、`single-node-offline-deploy.md`） |
| SDK | `/home/austin/projects/e2b-repo/e2b-arm/` |

**不要**读 `infra-arm/`、`KASandbox/` 的工作树（它们含有后续 checkpoint / restore 的开发，超出本书范围），
除非要点明确让你去看。

## 写作要求（STYLE.md 的浓缩，冲突时以 STYLE.md 为准）

- 结构：`# NN · 标题` → 题注引用块（一到三句 + 读者 / 预备 / 代码）→ `## 0. 本篇要回答的问题` →
  正文各节 `## 1.` … → `## N. 小结` → `## 延伸阅读 / 下一篇`。
- 正文 3000–5000 汉字（不含代码块与表格）。
- **每个行为论断都要读过代码**，给出仓库相对路径 + 函数名；读不到、拿不准的标「推论：」。
  不要凭对 e2b 的印象写；上游代码在演进，以 2026.09 的代码为准。
- 先讲问题再讲方案；代价与收益成对；不写宣传腔；不用「显然」；不用 emoji 与感叹号。
- 图：mermaid 内嵌，1–3 张，节点 ≤ 25，标签用 `A["..."]` 形式，标签里不要有未转义的括号 / 引号 / 竖线；
  目录与字节布局用 ```text。
- 交叉引用只链接 OUTLINE 里存在的文件名：`[第 27 篇 · ResumeSandbox](27-resume-sandbox.md)`。
  目标篇已经存在于 `e2b-infra/` 时可以加小节锚点（先读它的标题确认锚点）；不存在时只链文件。
- 上游篇目：若该机制在 ARM 适配版有变化，在小结之前加 `## N. ARM 适配版的差异`，两三句 + 链接到第十部分对应篇目。
  判断依据是 ARM 补丁的 diff（用上面的 git diff 命令查你涉及的文件）。
- 术语按 STYLE.md 第三节；版本称谓只用「上游 2026.09」「ARM 适配版」「单机离线版」。
- 不写内部代号（M1、v3、jll、分支名）、不写过程叙事、不写「我们决定」。

## 交付

1. 把文档写到 `/home/austin/projects/e2b-repo/e2b-book/e2b-infra/<你的文件名>`。只写这一个文件，不改别的文件。
2. 写完后自检：
   ```bash
   cd /home/austin/projects/e2b-repo/e2b-book/tools
   python3 mdlinks.py ../e2b-infra/<你的文件名>
   node mdmermaid.mjs ../e2b-infra/<你的文件名>
   ```
   MISSING-FILE 对尚未写的篇目是正常的；其它问题要修掉。
3. 统计汉字数：`python3 -c "import re,sys;t=open(sys.argv[1],encoding='utf-8').read();t=re.sub(r'\x60\x60\x60.*?\x60\x60\x60','',t,flags=re.S);t=re.sub(r'^\|.*$','',t,flags=re.M);print(len(re.findall(r'[一-鿿]',t)))" ../e2b-infra/<你的文件名>`
4. 在最终回复里给出**交付说明**（不超过 300 字）：核心论断清单、标为推论的地方、发现的与大纲不符之处、
   建议其它篇目补充或修改之处、汉字数。
