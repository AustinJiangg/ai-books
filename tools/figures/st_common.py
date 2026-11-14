"""《E2B 沙箱存储从零讲透》配图的公共部分：输出目录、颜色角色、几个常用部件。

颜色角色（全书统一，一种颜色只表示一种东西）：
- GUEST 紫：客户机、Firecracker 进程里的东西
- ORCH  蓝：orchestrator（template-manager 进程）和它的数据结构
- HOST  灰：宿主机内核、普通目录、部署脚本
- STORE 橙：存储里的文件（模板、build 的数据和 header）
- MINE  绿：改动、沙箱私有的数据（COW、diff、脏页）
- RISK  红：问题、风险、吃内存的地方
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from figkit import *  # noqa: E402,F401,F403
from figkit import W, M, VM, NS, HOST, NAT, BAD, GOOD, KEY, WHITE  # noqa: E402,F401

OUT = os.path.join(HERE, "..", "..", "e2b-storage", "img")

GUEST, ORCH, STORE, MINE, RISK = VM, NS, NAT, GOOD, BAD


def save(s, name, h):
    s.save(os.path.join(OUT, name), h)


def white(role):
    """同色系的白底版本：白底、该角色的边框和字色。"""
    return ("#FFFFFF", role[1], role[2])


def band(s, y, h, role, title, sub=None, x=None, w=None):
    """横向分区：浅底大框，左上角标题。"""
    x = M if x is None else x
    w = W - 2 * M if w is None else w
    s.rect(x, y, w, h, role[0], role[1], 1.3, rx=14)
    s.text(x + 20, y + 30, title, 15, role[2], 600)
    if sub:
        s.text(x + 20, y + 52, sub, 12.5, SUB)


def legend(s, y, items, x=None):
    """一行图例：[(角色, 文字)]，返回宽度结束 x。"""
    x = M if x is None else x
    for role, t in items:
        s.rect(x, y - 11, 16, 16, role[0], role[1], 1.2, rx=4)
        s.text(x + 24, y + 2, t, 13, SUB)
        x += 24 + text_w(t, 13) + 28
    return x


def cells(s, x, y, cw, ch, marks, role_on, role_off=WHITE, labels=None, lsize=11.5):
    """一排小格子（位图 / 块）：marks 里每项为 True/False 或角色。labels 是格子下方的小字。"""
    for i, m in enumerate(marks):
        role = m if isinstance(m, tuple) else (role_on if m else role_off)
        s.rect(x + i * cw, y, cw - 4, ch, role[0], role[1], 1.1, rx=4)
        if labels and i < len(labels) and labels[i]:
            s.text(x + i * cw + (cw - 4) / 2, y + ch + 16, labels[i], lsize, MUTED, 400, "middle")
