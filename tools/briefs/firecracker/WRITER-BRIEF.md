# 编写者简报（Firecracker 手册，每位章节编写者必读）

你是一本教材式技术手册的**一篇**的作者。这本书讲 Firecracker（上游 v1.12.1）及其上的两层改动：
e2b 定制版、ARM 适配版（含 checkpoint / restore 扩展）。读者是美国顶级大学计算机专业本科高年级与研究生：
懂操作系统、体系结构、系统编程的基本概念，但不一定接触过 KVM、virtio、Rust、Firecracker。主语言中文，技术名词按需用英文。

## 你必须先读的三份文件

1. `/home/austin/projects/e2b-repo/e2b-book/firecracker/STYLE.md` —— 体例、术语、三层版本称谓、自检清单。**逐条遵守。**
2. `/home/austin/projects/e2b-repo/e2b-book/firecracker/OUTLINE.md` —— 找到你这一篇的要点（讲什么 / 代码 / 图表），
   并读一遍**前后相邻篇目**的要点，避免重复、便于交叉引用。要点里标「确认」的地方必须到代码里核实。
3. 风格样例：`/home/austin/projects/e2b-repo/e2b-book/e2b-infra/37-pause-and-snapshot.md`
   （另一本手册的一篇；读它的写法与图的用法，不要引用它的内容，除非你的篇目要点明确要求）。

## 代码基线（读代码时只用这些路径）

| 基线 | 路径 |
|---|---|
| 上游 v1.12.1 | `/home/austin/projects/e2b-repo/tmp/e2b-book-src/fc-upstream/` |
| e2b 定制版 | `/home/austin/projects/e2b-repo/tmp/e2b-book-src/fc-e2b/`（a41d3fb）；差异：`git -C /home/austin/projects/e2b-repo/tmp/e2b-book-src/fc-e2b diff v1.12.1 a41d3fb -- <path>`；提交：`git -C … log --stat v1.12.1..a41d3fb`；该 clone 有 `upstream` 远端与上游 tag、e2b 的全部分支 |
| e2b 定制版（guest 内核） | GitHub e2b-dev/fc-kernels release `v0.0.8`（commit b8cea06）：`gh api repos/e2b-dev/fc-kernels/contents/<path>?ref=b8cea06`，或 `git clone https://github.com/e2b-dev/fc-kernels /home/austin/projects/e2b-repo/tmp/e2b-book-src/fc-kernels && git -C … checkout b8cea06`（已存在就直接用） |
| ARM 适配版 | `/home/austin/projects/e2b-repo/tmp/e2b-book-src/kasandbox-jll/firecracker/`（jll 3863c76，含 checkpoint 扩展）；checkpoint 扩展之前：`/home/austin/projects/e2b-repo/tmp/e2b-book-src/kasandbox-arm/firecracker/`（b8e85c3）；差异：`git -C /home/austin/projects/e2b-repo/KASandbox diff 9e880db b8e85c3 -- firecracker`（ARM 构建修复）、`git -C /home/austin/projects/e2b-repo/KASandbox diff b8e85c3 3863c76 -- firecracker`（HDBSS + checkpoint 扩展）；54a1c1a 与 a41d3fb 之差：`git -C /home/austin/projects/e2b-repo/tmp/e2b-book-src/fc-e2b diff 54a1c1a a41d3fb` |
| 单机离线版（部署布局） | `/home/austin/projects/e2b-repo/e2b-infra/`：`e2b-infra.spec`、`e2b-deploy/dep/init-client.sh` |
| e2b infra（调用方，只在要点让你看时看） | `/home/austin/projects/e2b-repo/tmp/e2b-book-src/upstream/packages/orchestrator/internal/sandbox/fc/`（ARM 版在 `tmp/e2b-book-src/arm/`）|
| 上游文档 | `/home/austin/projects/e2b-repo/tmp/e2b-book-src/fc-upstream/docs/` —— 参考，不是依据；以代码为准 |

写第一至八部分（上游）时只读 `fc-upstream/`；写第九部分读 `fc-e2b/` 与 diff；第十部分读 `kasandbox-jll/`、`kasandbox-arm/` 与 diff。
上游篇目末尾的「后续各层的差异」小节要靠上面的 diff 命令判断你涉及的文件有没有被改。

**不要**读 `KASandbox/`、`KASandbox_0904/`、`infra-arm/` 的工作树，不要读 `fc-kernels-arm/`（另一套方案的内核仓库，与本书无关），
不要读 `/home/austin/projects/firecracker-1.12.1/`、`/home/austin/projects/kvcache-ai/`。

## 写作要求（STYLE.md 的浓缩，冲突时以 STYLE.md 为准）

- 结构：`# NN · 标题` → 题注引用块（一到三句 + 读者 / 预备 / 代码）→ `## 0. 本篇要回答的问题` →
  正文各节 `## 1.` … → `## N. 小结` → `## 延伸阅读 / 下一篇`。
- 正文 3000–5000 汉字（不含代码块与表格）。
- **每个行为论断都要读过代码**，给出仓库相对路径 + 函数名（`src/vmm/src/vstate/vm.rs` 的 `get_dirty_bitmap()`）；
  读不到、拿不准的标「推论：」。不要凭对 Firecracker 的印象写；版本间差异大，以 v1.12.1 的代码为准。
- 先讲问题再讲方案；代价与收益成对；不写宣传腔；不用「显然」；不用 emoji 与感叹号。不给性能数字。
- 图：mermaid 内嵌，1–3 张，节点 ≤ 20，标签用 `A["..."]` 形式，标签里不要有未转义的括号 / 引号 / 竖线；
  目录、字节布局、寄存器布局用 ```text。**图必须在 `tools/figcheck.sh` 下 PASS**，画法与阈值见 `firecracker/FIGURE-GUIDE.md`
  （尤其：直线长链拆列、状态机改 flowchart + 编号表、时序图 ≤ 6 参与者 ≤ 14 消息）。
- 交叉引用只链接 OUTLINE 里存在的文件名：`[第 37 篇 · 创建快照](37-snapshot-create.md)`。
  目标篇已经存在于 `firecracker/` 时可以加小节锚点（先读它的标题确认锚点）；不存在时只链文件。
  另外两本手册只在「延伸阅读」里链接（写法见 STYLE.md 第二节）。
- 上游篇目：若该机制在后面某层有变化，在小结之前加 `## N. 后续各层的差异`，两三句 + 链接到对应篇目。没有变化就不加。
- 术语按 STYLE.md 第三节；版本称谓只用「上游 v1.12.1」「e2b 定制版」「ARM 适配版」。
- 不写内部代号（M1、v3、jll、jll-xfs、deltabox、路线 A）、不写过程叙事、不写「我们决定」。代码注释里出现的这类字眼要翻译成设计取舍。

## 交付

1. 把文档写到 `/home/austin/projects/e2b-repo/e2b-book/firecracker/<你的文件名>`。只写分配给你的文件，不改别的文件。
2. 写完后自检：
   ```bash
   cd /home/austin/projects/e2b-repo/e2b-book
   python3 tools/mdlinks.py firecracker/<你的文件名>
   node tools/mdmermaid.mjs firecracker/<你的文件名>
   tools/figcheck.sh --png /tmp/claude-1000/figs-<你的篇号> firecracker/<你的文件名>
   ```
   MISSING-FILE 对尚未写的篇目是正常的；其它问题要修掉。figcheck 每张图必须 PASS；WARN 就改图（拆列、缩短标签、减少节点）。
3. 统计汉字数：`python3 -c "import re,sys;t=open(sys.argv[1],encoding='utf-8').read();t=re.sub(r'\x60\x60\x60.*?\x60\x60\x60','',t,flags=re.S);t=re.sub(r'^\|.*$','',t,flags=re.M);print(len(re.findall(r'[一-鿿]',t)))" firecracker/<你的文件名>`
4. 在最终回复里给出**交付说明**（每篇不超过 200 字）：核心论断清单、标为推论的地方、发现的与大纲不符之处、
   建议其它篇目补充或修改之处、汉字数、figcheck 结果。
