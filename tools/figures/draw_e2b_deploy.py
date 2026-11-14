"""重画《E2B 部署从零讲透》的全部配图，输出到 e2b-deploy/img/。

用法（任意目录下）: python3 tools/figures/draw_e2b_deploy.py

各篇的图分在几个脚本里，都可以单独运行：
- dp_p1.py：第 1～5 篇    - dp_p2.py：第 6～9 篇
- dp_p3.py：第 10～16 篇  - dp_p4.py：第 17～20 篇
公共部分（颜色角色、输出目录、表格/流程/步骤/树等部件）在 dp_common.py，画图工具在 figkit.py。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import dp_p1, dp_p2, dp_p3, dp_p4  # noqa: E402,E401

for mod in (dp_p1, dp_p2, dp_p3, dp_p4):
    for name in sorted(n for n in dir(mod) if n.startswith("fig_")):
        getattr(mod, name)()
