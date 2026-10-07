# ai-books —— AI 写的书

这里放用 AI Agent 编写的书。每本书一个目录，正文是一篇篇 Markdown，在 GitHub 上点开就能读；
每本书另有一个打包好的单文件 HTML，下载后双击即可离线阅读。

## 书目

| 书 | 版本 | 讲什么 | 在线读 | 离线版 |
|---|---|---|---|---|
| e2b 服务端基础设施技术手册 | v0.1.6 · 2026-09-12 | [e2b-dev/infra](https://github.com/e2b-dev/infra) tag `2026.09` 及其 aarch64（鲲鹏 / openEuler）适配版 | [目录](e2b-infra/README.md) | [e2b-infra.html](html/e2b-infra.html) |
| Firecracker 技术手册 | v0.1.0 · 2026-09-15 | 上游 Firecracker v1.12.1、e2b 定制版、ARM 适配版与 checkpoint / restore 扩展四层的代码讲解 | [目录](firecracker/README.md) | [firecracker.html](html/firecracker.html) |
| AI Agent 沙箱 | v0.1.0 · 2026-10-07 | Agent 沙箱作为 RL 训练、评测与产品推理的基础设施：隔离原语、八层参考架构、DSec / AgentENV 等案例、国内外披露矩阵与研究议程 | [目录](agent-sandbox/README.md) | [agent-sandbox.html](html/agent-sandbox.html) |
| C++ 期末笔试突击手册 | v0.1.0 · 2026-10-07 | 按 Stroustrup《C++程序设计语言》（第 4 版，C++11）讲大学 C++ 期末笔试考点 | [目录](cpp-exam/README.md) | [cpp-exam.html](html/cpp-exam.html) |

**怎么读**

- **在线读**：点「目录」进入该书的 `README.md`，从目录点进各篇。图（mermaid）由 GitHub 直接渲染。
- **离线版**：点 `.html` 链接，在打开的页面右上角点 **Download raw file**（下载图标）保存，双击用浏览器打开。
  单文件、不联网也能看：图内联渲染、可点击放大，目录按部分折叠，跨篇链接都改成了页内跳转。

## 仓库结构

| 路径 | 内容 |
|---|---|
| `<书>/` | 一本书。`README.md` 是导读、目录与版本；正文是 `NN-xxx.md`；另有三个编写用文件：`OUTLINE.md`（编写计划与每篇要点）、`STYLE.md`（写作规约）、`FIGURE-GUIDE.md`（图的规约） |
| [`html/`](html/) | 每本书的单文件 HTML，文件名与书的目录同名 |
| [`tools/`](tools/) | 共用工具：链接 / 锚点检查（`mdlinks.py`）、mermaid 语法检查（`mdmermaid.mjs`）、图的渲染检查（`figcheck.sh`）、单文件 HTML 生成（`build_docs_html.py`）、mermaid 主题 |
| [`tools/briefs/`](tools/briefs/) | 给编写 / 审校 / 图修订子任务的简报，按书分目录 |

书名、版本、日期与修订记录都在各书 `README.md` 顶部与「版本」节。

与本仓库之外其它文档的关系：

- checkpoint / restore（高频快速回滚）在 orchestrator 一侧的设计与测试有独立的手册：
  [`../e2b-infra-docs/rollback/docs/`](../e2b-infra-docs/rollback/docs/)。e2b 手册第 87 篇给概览与入口；
  Firecracker 手册第十一部分讲 Firecracker 一侧的实现，与那本手册分工不重复。
- 单机离线部署的**操作手册**是 [`../e2b-infra/single-node-offline-deploy.md`](../e2b-infra/single-node-offline-deploy.md)，
  **逐脚本讲解**在 [`../e2b-infra/deploy-docs/`](../e2b-infra/deploy-docs/)。
