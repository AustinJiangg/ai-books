# ai-books —— AI 写的书

这里放用 AI Agent 编写的书。每本书一个目录，正文是一篇篇 Markdown，在 GitHub 上点开就能读；
每本书另有一个单文件网页版，放在 GitHub Pages 上：<https://austinjiangg.github.io/ai-books/>。

## 书目

| 书 | 版本 | 讲什么 | 网页版 | Markdown |
|---|---|---|---|---|
| e2b 服务端基础设施技术手册 | v0.1.6 · 2026-09-12 | [e2b-dev/infra](https://github.com/e2b-dev/infra) tag `2026.09` 及其 aarch64（鲲鹏 / openEuler）适配版 | [打开](https://austinjiangg.github.io/ai-books/html/e2b-infra.html) | [目录](e2b-infra/README.md) |
| Firecracker 技术手册 | v0.1.0 · 2026-09-15 | 上游 Firecracker v1.12.1、e2b 定制版、ARM 适配版与 checkpoint / restore 扩展四层的代码讲解 | [打开](https://austinjiangg.github.io/ai-books/html/firecracker.html) | [目录](firecracker/README.md) |
| AI Agent 沙箱 | v0.1.0 · 2026-10-07 | Agent 沙箱作为 RL 训练、评测与产品推理的基础设施：隔离原语、八层参考架构、DSec / AgentENV 等案例、国内外披露矩阵与研究议程 | [打开](https://austinjiangg.github.io/ai-books/html/agent-sandbox.html) | [目录](agent-sandbox/README.md) |
| C++ 期末笔试突击手册 | v0.1.0 · 2026-10-07 | 按 Stroustrup《C++程序设计语言》（第 4 版，C++11）讲大学 C++ 期末笔试考点 | [打开](https://austinjiangg.github.io/ai-books/html/cpp-exam.html) | [目录](cpp-exam/README.md) |
| AgentENV 技术手册 | v0.0.1 · 2026-10-04 | [kvcache-ai/AgentENV](https://github.com/kvcache-ai/AgentENV) tag `v0.2.3` 及其依赖的 AENV 补丁版 Firecracker（`aenv-deps`），并与 e2b infra 逐项对照（规划中，正文未写） | — | [目录](agentenv/README.md) |

**怎么读**

- **网页版**（推荐）：点「打开」直接在浏览器里读。图可点击放大，目录按部分折叠，跨篇链接是页内跳转；手机也能看。
  想离线看，在页面上 Ctrl+S（Mac 上 ⌘+S）存成一个 `.html` 文件，以后双击打开，不需要联网。
- **Markdown**：点「目录」进入该书的 `README.md`，从目录点进各篇，图由 GitHub 渲染。

## 仓库结构

| 路径 | 内容 |
|---|---|
| `<书>/` | 一本书。`README.md` 是导读、目录与版本；正文是 `NN-xxx.md`；另有三个编写用文件：`OUTLINE.md`（编写计划与每篇要点）、`STYLE.md`（写作规约）、`FIGURE-GUIDE.md`（图的规约） |
| [`html/`](html/) | 每本书的单文件网页版，文件名与书的目录同名；根目录的 `index.html` 是 Pages 首页（书目），`.nojekyll` 让 Pages 原样发布、不经 Jekyll 处理 |
| [`tools/`](tools/) | 共用工具：链接 / 锚点检查（`mdlinks.py`）、mermaid 语法检查（`mdmermaid.mjs`）、图的渲染检查（`figcheck.sh`）、单文件 HTML 生成（`build_docs_html.py`）、mermaid 主题 |
| [`tools/briefs/`](tools/briefs/) | 给编写 / 审校 / 图修订子任务的简报，按书分目录 |

书名、版本、日期与修订记录都在各书 `README.md` 顶部与「版本」节。

检查与生成网页版需要 Python 的 `markdown-it-py`（`pip install markdown-it-py`）与 `tools/node_modules` 里的 mermaid
（`cd tools && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install`，同时装好 `figcheck` 用的 jsdom 与 playwright-chromium）。
AgentENV 手册的代码基线不入库，用 `tools/fetch-sources.sh` 拉到仓库根下的 `.src/`。

与本仓库之外其它文档的关系：

- checkpoint / restore（高频快速回滚）在 orchestrator 一侧的设计与测试有独立的手册：
  [`../e2b-infra-docs/rollback/docs/`](../e2b-infra-docs/rollback/docs/)。e2b 手册第 87 篇给概览与入口；
  Firecracker 手册第十一部分讲 Firecracker 一侧的实现，与那本手册分工不重复。
- 单机离线部署的**操作手册**是 [`../e2b-infra/single-node-offline-deploy.md`](../e2b-infra/single-node-offline-deploy.md)，
  **逐脚本讲解**在 [`../e2b-infra/deploy-docs/`](../e2b-infra/deploy-docs/)。
