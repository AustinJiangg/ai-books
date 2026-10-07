# 续写交接（AgentENV 手册）

本文件记录这本书写到哪里、怎么接着写。下次继续时先读它，再读 `agentenv/OUTLINE.md` 第四节（编写流程）。

## 当前状态（2026-10-07）

| 项 | 状态 |
|---|---|
| 脚手架 | 完成：`agentenv/{README,OUTLINE,STYLE,FIGURE-GUIDE}.md`、`tools/briefs/agentenv/{WRITER-BRIEF,REVIEWER-BRIEF,review-notes}.md`、调研笔记 `survey/` |
| 编写环境 | 完成：`tools/fetch-sources.sh`（代码基线拉到不入库的 `.src/`）、`tools/package.json`（mermaid / jsdom / playwright-chromium） |
| 正文 | **1 / 74**：只有第 19 篇（状态机与并发控制，约 4300 字，初稿 `●`） |
| 已知待修 | 第 19 篇第 2 张图 figcheck WARN（边标签重叠 4 处），审校时按 FIGURE-GUIDE 改成编号边 + 图下表 |
| 审校 / 打包 / 发布 | 未开始 |

第一波（08–39，10 个代理并行）在启动后不久因额度原因全部中止，除第 19 篇外没有产出；
那一波主要成本花在读代码上，因此下次每个代理的篇数宜少（2 篇），一次派的代理数也宜少。

## 恢复环境（新容器里每次都要做）

```bash
cd "$(git rev-parse --show-toplevel)"
tools/fetch-sources.sh                                   # 拉 .src/agentenv、.src/fc-aenv、.src/e2b-infra、.src/overlaybd-upstream
(cd tools && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install --no-audit --no-fund)
tools/figcheck.sh agentenv/19-state-machine-and-concurrency.md   # 验证图检查可用
```

打包需要 `pip install markdown-it-py`（或在 venv 里装），命令见根目录 `README.md`。

## 剩余篇目与建议批次

建议每批 3–4 个代理、每个代理 2 篇相邻篇目；每批交回后：汇总交付说明里给其它篇的建议到 `review-notes.md` →
把 OUTLINE 状态列改为 `●` → 提交并推送。顺序沿用 OUTLINE 第四节：第二至九部分 → 第一部分 → 第十部分（68 最后）→ 附录 → 00。

| 批 | 篇目 |
|---|---|
| 1 | 08–09、10–11、12–13、14–15 |
| 2 | 16–17、18 + 20、21–22、23–24 |
| 3 | 25–26、27–28、29–30、31–32 |
| 4 | 33 + 34、35–36、37–38、39–40 |
| 5 | 41–42、43–44、45–46、47–48 |
| 6 | 49–50、51–52、53–54、55–56 |
| 7 | 57–58、59–60、61–62、63–64 |
| 8 | 02–03、04–05、06–07、65–66 |
| 9 | 67 + 68、69–70、71–73、00–01 |

然后审校（每 8–10 篇一个审校代理，用 `REVIEWER-BRIEF.md`）、图返工（`tools/briefs/FIGURE-FIXER-BRIEF.md`）、
`tools/mdlinks.py agentenv` 与 `tools/figcheck.sh agentenv` 全过、生成 `html/agentenv.html`，
并在根目录 `README.md` 与 `index.html` 的书目里加上网页版链接。

## 派编写代理用的提示词模板

```text
你是《AgentENV 技术手册》的章节编写者。先 cd 到仓库根目录。
先完整阅读 tools/briefs/agentenv/WRITER-BRIEF.md，并严格按它执行（它会指引你读 STYLE.md、OUTLINE.md、FIGURE-GUIDE.md、调研笔记与 review-notes）。

你负责的篇目（按 agentenv/OUTLINE.md 中的要点写，文件名以 OUTLINE 为准）：
- NN-xxx.md
- NN-yyy.md

代码基线在 .src/（不存在就先运行 tools/fetch-sources.sh）；只写这几个文件，不改其它文件，不 git commit。
每篇写完都要跑 mdlinks / mdmermaid / figcheck（用 --png .src/figs/<篇号>）并看 PNG，直到图全部 PASS。
写完一篇就先落盘再写下一篇（中途被打断时已完成的篇目不会丢）。
最终回复给出每篇的交付说明（按 WRITER-BRIEF「交付」第 4 条）。
```

## 约定回顾

- 书里与简报里不出现任何本机路径；代码基线只在 `.src/`，正文引用路径相对于各自仓库根。
- 调研笔记（`survey/`）入库，是起点不是依据。
- 不给性能数字，README 的宣称也不引用。
- 另外两本书（`e2b-infra/`、`firecracker/`）的旧简报里仍有本机路径，未改。
