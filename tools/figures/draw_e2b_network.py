"""重画《E2B 沙箱网络从零讲透》的全部配图，输出到 e2b-network/img/。

用法（任意目录下）: python3 tools/figures/draw_e2b_network.py

各篇的图分在几个脚本里，都可以单独运行：
- e2b_p1a.py：第 1～4 篇        - e2b_p1b.py：第 5～8 篇
- e2b_p2.py ：第 9、10、12、14 篇 - e2b_core.py：第 10-1、11-1、13-1
- e2b_p3.py ：第 15～19 篇       - e2b_p5.py ：第 20～22 篇
画图用的工具在 figkit.py。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import e2b_core, e2b_p1a, e2b_p1b, e2b_p2, e2b_p3, e2b_p5  # noqa: E402,E401

for mod in (e2b_p1a, e2b_p1b, e2b_p2, e2b_core, e2b_p3, e2b_p5):
    for name in sorted(n for n in dir(mod) if n.startswith("fig_")):
        getattr(mod, name)()
