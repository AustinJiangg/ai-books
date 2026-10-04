# 图修订者简报

你负责一组篇目里 **所有 mermaid 图** 的返工。目标：每张图在 `tools/figcheck.sh` 下 PASS，并且肉眼看着清楚、匀称、好看。
正文文字原则上不动；只有把长链图改成列表 / 表格、或给编号边补一张说明表时才动图附近的正文。

## 先读

1. `/home/austin/projects/e2b-repo/e2b-book/<书目录>/FIGURE-GUIDE.md`（<书目录> 是 e2b-infra、firecracker 或 agentenv，由任务指定）（全文，逐条遵守）
2. `/home/austin/projects/e2b-repo/e2b-book/<书目录>/STYLE.md` 4.4 节（图的体例）

## 做法

对你负责的每个文件：

1. 运行 `tools/figcheck.sh --png <你的临时目录>  <书目录>/<文件>`，读输出与 PNG（用 Read 工具打开 PNG 看图）。
2. 对每张 WARN 的图，按 FIGURE-GUIDE 第 3 节对应类型的规则改源码。常见改法：
   - 太宽 / 太扁：`LR` 改 `TB`，或用 `subgraph` 折成两列 / 两行；
   - 太高 / 太窄：长链拆成 2～3 列的子图，或降级为有序列表 + 阶段图；
   - 边标签重叠：缩短标签、给边编号 + 图下表格、把状态图改成 flowchart；
   - 时序图太高：拆两张，或删掉不承载信息的消息，缩短文字；
   - 文字被裁、节点文字换行难看：用 `<br/>` 自己断行。
   - PASS 但看着别扭的（边绕远、重心偏、留白不均）也要改。
3. 改完重跑 figcheck，直到该文件所有图 PASS；再打开最终 PNG 看一遍。
4. 跑 `node tools/mdmermaid.mjs  <书目录>/<文件>` 与 `python3 tools/mdlinks.py  <书目录>/<文件>`，都不能有错。
5. 图的信息不能丢：改画法不是删内容。若把一张图降级为列表，该篇仍要至少保留一张图。
6. 不要改别的篇目，不要改 tools/ 与 STYLE / OUTLINE / FIGURE-GUIDE。
7. 汉字数变化控制在 ±300 以内（统计命令见 `tools/WRITER-BRIEF.md` 交付节）。

## 交付

最终回复（≤ 300 字）：每篇每张图做了什么改动（一行一张）、仍 WARN 的图及原因（应当没有）、是否动了正文。
