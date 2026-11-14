"""《E2B 部署从零讲透》配图的公共部分：输出目录、颜色角色、几个常用部件。

颜色角色（全书统一，一种颜色只表示一种东西）：
- MACH 灰：机器层（内核、目录、系统配置文件、脚本）
- SVC  橙：宿主服务层（systemd / docker 直接管的服务）
- JOB  蓝：业务层（Nomad 管的 E2B 服务、Nomad / Consul 本身的调度概念）
- SBX  紫：沙箱层（Firecracker、envd、客户机）
- OK   绿：成功、持久、推荐做法
- RISK 红：问题、风险、重启后丢失
- KEY  中性深色：强调但不表达含义；WHITE 白底
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from figkit import *  # noqa: E402,F401,F403
from figkit import W, M, VM, NS, HOST, NAT, BAD, GOOD, KEY, WHITE, INK, SUB, MUTED, HAIR  # noqa: E402,F401

OUT = os.path.join(HERE, "..", "..", "e2b-deploy", "img")

MACH, SVC, JOB, SBX, OK, RISK = HOST, NAT, NS, VM, GOOD, BAD


def save(s, name, h):
    s.save(os.path.join(OUT, name), h)


def white(role):
    return ("#FFFFFF", role[1], role[2])


def band(s, x, y, w, h, role, title, sub=None, ts=15):
    """浅底大框，左上角标题。"""
    s.rect(x, y, w, h, role[0], role[1], 1.3, rx=14)
    s.text(x + 20, y + 30, title, ts, role[2], 600)
    if sub:
        s.text(x + 20, y + 52, sub, 12.5, SUB)


def legend(s, y, items, x=None):
    x = M if x is None else x
    for role, t in items:
        s.rect(x, y - 11, 16, 16, role[0], role[1], 1.2, rx=4)
        s.text(x + 24, y + 2, t, 13, SUB)
        x += 24 + text_w(t, 13) + 28
    return x


def flow_h(s, x, y, w, items, h=None, gap=44, ts=15, ss=12.5, labels=None, color=INK):
    """横向流程：items=[(role, title, sub)]，等宽排开，之间画箭头。返回每个框的 (x, y, w, h)。"""
    n = len(items)
    bw = (w - gap * (n - 1)) / n
    if h is None:
        h = max(need_h(bw, t, sub, ts, ss) for _, t, sub in items)
    out = []
    for i, (role, t, sub) in enumerate(items):
        bx = x + i * (bw + gap)
        box(s, bx, y, bw, h, role, t, sub, ts, ss)
        out.append((bx, y, bw, h))
        if i < n - 1:
            arrow(s, [(bx + bw + 4, y + h / 2), (bx + bw + gap - 4, y + h / 2)], color, 1.6,
                  label=(labels[i] if labels and i < len(labels) else None), ldy=-8, lsize=11.5)
    return out


def steps(s, x, y, w, items, role=WHITE, ts=14.5, ss=12.5, gap=12, numw=40, note_w=0, note_role=None):
    """竖向编号步骤：items=[(title, sub)] 或 [(title, sub, note)]。note 画在右侧小框里。返回结束 y。"""
    for i, it in enumerate(items):
        t, sub = it[0], it[1]
        note = it[2] if len(it) > 2 else None
        bw = w - numw - (note_w + 16 if note_w else 0)
        h = need_h(bw, t, sub, ts, ss, extra=20)
        if note and note_w:
            h = max(h, need_h(note_w, None, note, ts, 12, extra=20))
        num(s, x + 14, y + h / 2, i + 1)
        box(s, x + numw, y, bw, h, role, t, sub, ts, ss, align="start")
        if note and note_w:
            box(s, x + numw + bw + 16, y, note_w, h, note_role or KEY, None, note, ts, 12, style="outline")
        y += h + gap
    return y


def table(s, x, y, widths, rows, header=None, ts=13.5, hs=13.5, pad=10, roles=None, head_role=KEY, line=1.5):
    """表格：widths 列宽，rows 每行若干字符串；header 表头。roles[i] 给第 i 行整行底色（可为 None）。返回结束 y。"""
    def row_h(cells, size):
        return max(len(wrap(c, w - 2 * pad, size) or [""]) for c, w in zip(cells, widths)) * size * line + 2 * pad - 2

    total = sum(widths)
    if header:
        h = row_h(header, hs)
        s.rect(x, y, total, h, head_role[0], head_role[1], 1.1, rx=6)
        cx = x
        for c, w in zip(header, widths):
            for k, ln in enumerate(wrap(c, w - 2 * pad, hs)):
                s.text(cx + pad, y + pad + hs * 0.95 + k * hs * line, ln, hs, head_role[2], 600)
            cx += w
        y += h + 4
    for i, r in enumerate(rows):
        h = row_h(r, ts)
        role = roles[i] if roles and i < len(roles) and roles[i] else None
        if role:
            s.rect(x, y, total, h, role[0], role[1], 1, rx=6)
        else:
            s.line(x, y + h + 2, x + total, y + h + 2, HAIR, 1)
        cx = x
        for j, (c, w) in enumerate(zip(r, widths)):
            for k, ln in enumerate(wrap(c, w - 2 * pad, ts)):
                s.text(cx + pad, y + pad + ts * 0.95 + k * ts * line, ln, ts,
                       (role[2] if role else INK) if j == 0 else (INK if not role else role[2]), 600 if j == 0 else 400)
            cx += w
        y += h + 4
    return y


def tree(s, x, y, nodes, indent=34, gap=34, size=14, mono_first=True):
    """调用树：nodes=[(depth, text, note, role)]；role 决定左侧小方块颜色。返回结束 y。"""
    last_at_depth = {}
    for depth, text, note, role in nodes:
        nx = x + depth * indent
        if depth > 0 and (depth - 1) in last_at_depth:
            px, py = last_at_depth[depth - 1]
            s.path(f"M{px + 8:.1f} {py + 19:.1f} L{px + 8:.1f} {y - 5:.1f} L{nx - 4:.1f} {y - 5:.1f}", HAIR, 1.4)
        s.rect(nx, y - 13, 16, 16, role[0], role[1], 1.2, rx=4)
        s.text(nx + 26, y, text, size, INK, 600, mono=mono_first)
        tw = text_w(text, size) * 1.05 if (not mono_first or any(ord(c) > 127 for c in text)) else len(text) * size * 0.61
        if note:
            s.text(nx + 26 + tw + 18, y, note, 12.5, SUB)
        last_at_depth[depth] = (nx, y - 13)
        for d in list(last_at_depth):
            if d > depth:
                del last_at_depth[d]
        y += gap
    return y


def pill_row(s, x, y, items, role, size=13, gap=10, mono=True):
    """一行胶囊标签，返回结束 x。"""
    for t in items:
        w = (len(t) * size * 0.61 if mono else text_w(t, size)) + 22
        s.pill(x + w / 2, y, t, role, size, mono=mono)
        x += w + gap
    return x
