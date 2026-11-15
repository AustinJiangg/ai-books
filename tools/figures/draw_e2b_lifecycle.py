"""一次画出《E2B 模板构建、沙箱启动与暂停恢复从零讲透》的全部配图。用法: python3 tools/figures/draw_e2b_lifecycle.py"""
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
for name in ("lc_p1", "lc_p2", "lc_p3", "lc_p4", "lc_p5"):
    runpy.run_path(os.path.join(HERE, name + ".py"), run_name="__main__")
