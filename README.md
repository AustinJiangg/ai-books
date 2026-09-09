# e2b-book —— e2b 服务端基础设施技术手册

一本关于 **e2b 服务端基础设施**（[e2b-dev/infra](https://github.com/e2b-dev/infra)，tag `2026.09`）
及其 **aarch64（鲲鹏 / openEuler）适配版**的教材式技术手册。

| 路径 | 内容 |
|---|---|
| [`docs/`](docs/) | 正文，九十余篇；入口是 [`docs/README.md`](docs/README.md) |
| [`docs/OUTLINE.md`](docs/OUTLINE.md) | 编写计划：篇目、每篇要点、代码基线、编写流程 |
| [`docs/STYLE.md`](docs/STYLE.md) | 写作规约：口径、术语、体例、自检清单 |
| [`docs/FIGURE-GUIDE.md`](docs/FIGURE-GUIDE.md) | 图的规约：尺寸阈值、各类图的画法、检查与验收 |
| [`tools/`](tools/) | 链接 / 锚点检查（`mdlinks.py`）、mermaid 语法检查（`mdmermaid.mjs`）、图的渲染检查（`figcheck.sh`，真实 chromium）、单文件 HTML 打包（`build_docs_html.py`）、mermaid 主题（`mermaid-config.json` / `mermaid.css`）、编写 / 审校 / 图修订简报 |
| `dist/`（不入库） | 打包产物 `e2b-book.html`：单文件、离线可读、mermaid 内联渲染、图可点击放大、按部分折叠的目录、跨篇链接改写为页内锚点 |

与本仓库其它文档的关系：

- checkpoint / restore（高频快速回滚）有独立的手册：[`../e2b-infra-docs/rollback/docs/`](../e2b-infra-docs/rollback/docs/)。
  本书第 87 篇给概览与入口，不重复。
- 单机离线部署的**操作手册**是 [`../e2b-infra/single-node-offline-deploy.md`](../e2b-infra/single-node-offline-deploy.md)，
  **逐脚本讲解**在 [`../e2b-infra/deploy-docs/`](../e2b-infra/deploy-docs/)。本书第 80–82 篇讲原理，操作步骤链接过去。

重新生成打包件（需要 `markdown-it-py` 与 rollback 手册 `slides/node_modules` 里的 mermaid）；改过图之后先跑 `tools/figcheck.sh docs` 确认全部 PASS：

```bash
python3 tools/build_docs_html.py docs ../e2b-infra-docs/rollback/slides/node_modules/mermaid/dist/mermaid.min.js dist/e2b-book.html
```

当前版本、日期与修订记录见 [`docs/README.md`](docs/README.md) 顶部与「版本」节；打包脚本从那里读取版本号。
