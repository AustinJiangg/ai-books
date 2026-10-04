# e2b-book —— e2b 相关技术手册

这个仓库放 **e2b 相关的教材式技术手册**，每本书一个目录，各自独立编号、独立版本、独立打包件。
工具链（检查、打包、mermaid 主题）共用，在 `tools/`。

| 书 | 目录 | 讲什么 | 打包件 |
|---|---|---|---|
| e2b 服务端基础设施技术手册 | [`e2b-infra/`](e2b-infra/) | [e2b-dev/infra](https://github.com/e2b-dev/infra) tag `2026.09` 及其 aarch64（鲲鹏 / openEuler）适配版；入口 [`e2b-infra/README.md`](e2b-infra/README.md) | `dist/e2b-infra.html` |
| Firecracker 技术手册 | [`firecracker/`](firecracker/) | 上游 Firecracker v1.12.1、e2b 定制版、ARM 适配版与 checkpoint / restore 扩展四层的代码讲解；入口 [`firecracker/README.md`](firecracker/README.md) | `dist/firecracker.html` |
| AgentENV 技术手册 | [`agentenv/`](agentenv/) | [kvcache-ai/AgentENV](https://github.com/kvcache-ai/AgentENV) tag `v0.2.3` 及其依赖的 AENV 补丁版 Firecracker（`aenv-deps`），并与 e2b infra 逐项对照；入口 [`agentenv/README.md`](agentenv/README.md)（规划中，正文未写） | `dist/agentenv.html` |

每本书的目录里固定有四个编写用文件：`README.md`（导读、目录、版本）、`OUTLINE.md`（编写计划与每篇要点）、
`STYLE.md`（写作规约）、`FIGURE-GUIDE.md`（图的规约）。正文是 `NN-xxx.md`。

| 路径 | 内容 |
|---|---|
| [`tools/`](tools/) | 链接 / 锚点检查（`mdlinks.py`）、mermaid 语法检查（`mdmermaid.mjs`）、图的渲染检查（`figcheck.sh`，真实 chromium）、单文件 HTML 打包（`build_docs_html.py`）、mermaid 主题（`mermaid-config.json` / `mermaid.css`） |
| [`tools/briefs/`](tools/briefs/) | 给编写 / 审校 / 图修订子任务的简报，按书分目录；`FIGURE-FIXER-BRIEF.md` 各书共用 |
| `dist/`（不入库） | 打包产物：单文件、离线可读、mermaid 内联渲染、图可点击放大、按部分折叠的目录、跨篇链接改写为页内锚点 |

与本仓库之外其它文档的关系：

- checkpoint / restore（高频快速回滚）在 orchestrator 一侧的设计与测试有独立的手册：
  [`../e2b-infra-docs/rollback/docs/`](../e2b-infra-docs/rollback/docs/)。e2b 手册第 87 篇给概览与入口；
  Firecracker 手册第十一部分讲 Firecracker 一侧的实现，与那本手册分工不重复。
- 单机离线部署的**操作手册**是 [`../e2b-infra/single-node-offline-deploy.md`](../e2b-infra/single-node-offline-deploy.md)，
  **逐脚本讲解**在 [`../e2b-infra/deploy-docs/`](../e2b-infra/deploy-docs/)。

## 打包

需要 Python 的 `markdown-it-py`（`pip install markdown-it-py`）与 `tools/node_modules` 里的 mermaid
（`cd tools && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install`，同时装好 `figcheck` 用的 jsdom 与 playwright-chromium）。
改过图之后先跑 `tools/figcheck.sh <书目录>` 确认全部 PASS：

```bash
M=tools/node_modules/mermaid/dist/mermaid.min.js
python3 tools/build_docs_html.py e2b-infra   $M dist/e2b-infra.html
python3 tools/build_docs_html.py firecracker $M dist/firecracker.html
python3 tools/build_docs_html.py agentenv    $M dist/agentenv.html
```

AgentENV 手册的代码基线不入库，用 `tools/fetch-sources.sh` 拉到仓库根下的 `.src/`。

书名、版本、日期与修订记录都在各书 `README.md` 顶部与「版本」节；打包脚本从那里读取。

## 发布

交付件不入库，放在 GitHub Releases。每本书独立发布：tag 与 Release 名带书的前缀，把该书的打包件作为附件上传：

```bash
git tag -a e2b-infra-vX.Y.Z -m "e2b 服务端基础设施技术手册 vX.Y.Z" && git push origin e2b-infra-vX.Y.Z
gh release create e2b-infra-vX.Y.Z dist/e2b-infra.html --title "e2b-infra vX.Y.Z · YYYY-MM-DD" --notes "改动摘要"
```

```bash
git tag -a firecracker-vX.Y.Z -m "Firecracker 技术手册 vX.Y.Z" && git push origin firecracker-vX.Y.Z
gh release create firecracker-vX.Y.Z dist/firecracker.html --title "firecracker vX.Y.Z · YYYY-MM-DD" --notes "改动摘要"
```

```bash
git tag -a agentenv-vX.Y.Z -m "AgentENV 技术手册 vX.Y.Z" && git push origin agentenv-vX.Y.Z
gh release create agentenv-vX.Y.Z dist/agentenv.html --title "agentenv vX.Y.Z · YYYY-MM-DD" --notes "改动摘要"
```

早期的 `v0.1.5` 及之前的 tag / Release 属于 e2b 手册（当时仓库只有这一本书）。
