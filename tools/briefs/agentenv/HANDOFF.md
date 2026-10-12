# 续写交接（AgentENV 手册）

本文件记录这本书写到哪里、怎么接着写。下次继续时先读它，再读 `agentenv/OUTLINE.md` 第四节（编写流程）。

## 当前状态（2026-10-12）

| 项 | 状态 |
|---|---|
| 正文 | **74 / 74**，全部审校完成（OUTLINE 状态 `◎`）；约 30 万汉字（不含代码块与表格）、129 张图 |
| 检查 | `tools/figcheck.sh agentenv` 129 张全部 PASS；`tools/mdlinks.py agentenv` 0 错误；正文篇（00–68）汉字数都在 3000–5000 |
| 网页版 | `html/agentenv.html`，已加进根目录 `README.md` 与 `index.html` 的书目；正文改动后按「恢复环境」一节的命令重新生成 |
| 已知待办 | 基线升级（见下文「基线升级待办」）；`tools/figcheck.mjs` 对左右并排 subgraph 的「标签压线」检查可能误报（65、66 审校时靠减少边标签绕过）；01 / 70 的代码行数统计口径未与 `git ls-files` 实测统一（`src/api`、`thirdparty/envd` 两行） |

下文的批次表与提示词模板保留，供基线升级后重写受影响篇目时复用。

## 恢复环境（新容器里每次都要做）

```bash
cd "$(git rev-parse --show-toplevel)"
tools/fetch-sources.sh                                   # 拉 .src/agentenv、.src/fc-aenv、.src/e2b-infra、.src/overlaybd-upstream
(cd tools && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install --no-audit --no-fund)
tools/figcheck.sh agentenv/19-state-machine-and-concurrency.md   # 验证图检查可用
```

生成网页版需要 `pip install markdown-it-py`（或在 venv 里装）：

```bash
python3 tools/build_docs_html.py agentenv tools/node_modules/mermaid/dist/mermaid.min.js html/agentenv.html
```

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

## 基线升级待办

决定（2026-10-11）：全书继续以 AgentENV `v0.2.3` 为基线，不写 main 上未发版的改动；上游发布下一个 release 后再统一升级。
升级时：`git -C .src/agentenv fetch --tags && git -C .src/agentenv diff --stat v0.2.3 <新tag>`，逐项更新受影响篇目，
同时更新 STYLE.md 第二节、OUTLINE.md 第二节、WRITER-BRIEF 与 `tools/fetch-sources.sh` 里的 tag 与 commit，并检查 `config/deps_manifest.toml` 的 Firecracker 版本是否变化。

截至 2026-10-10，main 在 v0.2.3 之后已有 11 个提交（44 文件，+2657 −174），预计进入下一版：

| 改动 | 提交 | 受影响篇目 |
|---|---|---|
| 新增沙箱日志 API（`src/sandbox/logs.rs`、`openapi.yml`、`envd.rs`） | `34cdc80` | 14、18、28、72 |
| overlaybd 块缓存：回收被打开条目占住的容量 | `3bc6329` | 39 |
| ublk 块设备默认 I/O 调度器设为 none | `c0c4ad0` | 41、59 |
| ublk-daemon 关闭时并发停止设备 | `e006de0` | 41 |
| 心跳连接超时与失败原因日志 | `854cb14`、`5843159` | 57 |
| aenv CLI 断线恢复时保留排队输入 | `5d30259`、`3d9989b` | 62 |
| clippy、grpc 依赖、CI | `00351e2`、`39b1c90`、`e668fdb` | 无 |

## 约定回顾

- 书里与简报里不出现任何本机路径；代码基线只在 `.src/`，正文引用路径相对于各自仓库根。
- 调研笔记（`survey/`）入库，是起点不是依据。
- 不给性能数字，README 的宣称也不引用。
- 另外两本书（`e2b-infra/`、`firecracker/`）的旧简报里仍有本机路径，未改。
