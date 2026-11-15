"""一次画出《E2B 沙箱快照回滚从零讲透》的全部配图。用法: python3 tools/figures/draw_e2b_rollback.py"""
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
for name in ("rb_p1", "rb_p2", "rb_p3", "rb_p4", "rb_p5"):
    runpy.run_path(os.path.join(HERE, name + ".py"), run_name="__main__")
