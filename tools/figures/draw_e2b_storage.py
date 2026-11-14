"""重画《E2B 沙箱存储从零讲透》的全部配图，输出到 e2b-storage/img/。

用法（任意目录下）: python3 tools/figures/draw_e2b_storage.py

各篇的图分在几个脚本里，都可以单独运行：
- st_p1.py：第 1～6 篇    - st_p2.py：第 7～10 篇   - st_p3.py：第 11～13 篇
- st_p4.py：第 14～17 篇  - st_p5.py：第 18、19 篇
公共部分（颜色角色、输出目录）在 st_common.py，画图工具在 figkit.py。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import st_p1, st_p2, st_p3, st_p4, st_p5  # noqa: E402,E401

for mod in (st_p1, st_p2, st_p3, st_p4, st_p5):
    for name in sorted(n for n in dir(mod) if n.startswith("fig_")):
        getattr(mod, name)()
