"""画书中配图用的小工具：输出 SVG，纯标准库。

- 文字测量与换行：text_w、wrap（中文逐字断行，英文按词断行，标点不出现在行首）
- Svg：文字、混排文字、矩形、线、箭头、胶囊标签、标题、页脚
- 常用部件：chip（标题 + 等宽地址的小卡片）

颜色按角色定义（浅底、边框、深色字），同一本书的图里每种颜色只表示一种东西。
各书的绘图脚本 import 本模块，OUT 目录由脚本自己设置后传给 Svg.save。
"""
import os
from xml.sax.saxutils import escape

W, M = 1600, 48


# ------------------------------------------------------------------ 文字测量与换行
def _wide(ch):
    o = ord(ch)
    return o >= 0x2E80 or 0x2460 <= o <= 0x24FF or ch in "“”‘’…—→←↻×"


def _cw(ch, fs):
    if _wide(ch):
        return fs
    if ch == " ":
        return fs * 0.30
    if ch.isupper():
        return fs * 0.66
    if ch.isdigit():
        return fs * 0.57
    if ch.islower():
        return fs * 0.55
    if ch in "−_=+<>#%&@~^":
        return fs * 0.62
    return fs * 0.38


def text_w(s, fs):
    return sum(_cw(c, fs) if _wide(c) else _cw(c, fs) * 1.05 for c in s)


def _tokens(s):
    toks, cur = [], ""
    for ch in s:
        if ch == " " or _wide(ch):
            if cur:
                toks.append(cur)
                cur = ""
            toks.append(ch)
        else:
            cur += ch
    if cur:
        toks.append(cur)
    return toks


_CLOSE = set("，。、：；！？）」』”】》,.;:!?)")


def wrap(s, maxw, fs):
    """按宽度换行：中文逐字断行，英文按词断行；标点不出现在行首；避免最后一行只剩一两个字。"""
    if not s:
        return []
    lines, cur = [], []

    def w(tl):
        return text_w("".join(tl), fs)

    for t in _tokens(s):
        if not cur or w(cur + [t]) <= maxw:
            if not cur and w([t]) > maxw:
                piece = ""
                for ch in t:
                    if text_w(piece + ch, fs) > maxw and piece:
                        lines.append([piece])
                        piece = ""
                    piece += ch
                cur = [piece]
            else:
                cur.append(t)
            continue
        if t == " ":
            lines.append(cur)
            cur = []
        elif t in _CLOSE and len(cur) == 1:
            cur.append(t)
        elif t in _CLOSE:
            moved = cur.pop()
            lines.append(cur)
            cur = [moved, t]
        else:
            lines.append(cur)
            cur = [t]
    if cur:
        lines.append(cur)
    if len(lines) >= 2 and w(lines[-1]) < 2.2 * fs and len(lines[-2]) >= 3:
        lines[-1].insert(0, lines[-2].pop())
    return ["".join(tl).strip() for tl in lines]


SANS = ("'PingFang SC','Hiragino Sans GB','Microsoft YaHei','Noto Sans CJK SC','Noto Sans SC',"
        "'Source Han Sans SC',sans-serif")
MONO = "'JetBrains Mono','SF Mono',Menlo,Consolas,'Noto Sans Mono CJK SC','DejaVu Sans Mono',monospace"

INK, SUB, MUTED, HAIR = "#1F2328", "#57606A", "#8C959F", "#D8DEE4"
# 每种角色：浅底、边框、深色字
VM = ("#F3F0FF", "#8B7FE0", "#4B3FA8")
NS = ("#EDF4FD", "#5B9BE6", "#1D4F91")
HOST = ("#F6F6F3", "#B7B5AC", "#3D3C38")
NAT = ("#FDF0D9", "#D9922B", "#8A5300")
BAD = ("#FCEDE8", "#D6603D", "#9A3215")
GOOD = ("#E3F5EE", "#1F9E77", "#0E6B4F")


class Svg:
    def __init__(self, w=W):
        self.w, self.o, self.markers = w, [], set()

    def text(self, x, y, s, size=15, color=INK, weight=400, anchor="start", mono=False):
        fam = f' font-family="{MONO}"' if mono else ""
        fw = f' font-weight="{weight}"' if weight != 400 else ""
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}"{fw}{fam} '
                      f'text-anchor="{anchor}">{escape(s)}</text>')

    def rich(self, x, y, parts, size=15, anchor="start", mono=False):
        """一行里混排几段颜色 / 粗细不同的文字。parts: [(文字, 颜色, 字重)]。"""
        fam = f' font-family="{MONO}"' if mono else ""
        spans = "".join(f'<tspan fill="{c}"{"" if w == 400 else f" font-weight={chr(34)}{w}{chr(34)}"}>'
                        f'{escape(s)}</tspan>' for s, c, w in parts)
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}"{fam} text-anchor="{anchor}" '
                      f'xml:space="preserve">{spans}</text>')

    def rect(self, x, y, w, h, fill="#FFFFFF", stroke=HAIR, sw=1.2, rx=10, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
                      f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def line(self, x1, y1, x2, y2, color=SUB, sw=1.5, dash=None, start=False, end=False):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ""
        if start or end:
            self.markers.add(color)
            mid = f'url(#m{color[1:]})'
            m = (f' marker-start="{mid}"' if start else "") + (f' marker-end="{mid}"' if end else "")
        self.o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
                      f'stroke-width="{sw}" stroke-linecap="round"{d}{m}/>')

    def path(self, d, color=SUB, sw=1.5, dash=None, end=False):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        m = ""
        if end:
            self.markers.add(color)
            m = f' marker-end="url(#m{color[1:]})"'
        self.o.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
                      f'stroke-linejoin="round"{da}{m}/>')

    def circle(self, cx, cy, r, fill, stroke="none", sw=1):
        self.o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def pill(self, cx, cy, s, role, size=13, solid=False, mono=False, h=None):
        """以 (cx, cy) 为中心的胶囊标签，返回宽度。"""
        f, st, tc = role
        h = h or size + 13
        w = (len(s) * size * 0.61 if mono else text_w(s, size)) + 22
        self.rect(cx - w / 2, cy - h / 2, w, h, st if solid else f, st, 1, rx=h / 2)
        self.text(cx, cy + size * 0.36, s, size, "#FFFFFF" if solid else tc, 600, "middle", mono)
        return w

    def header(self, title, sub):
        self.text(M, 58, title, 28, INK, 600)
        y = 92
        for s in wrap(sub, self.w - 2 * M, 15):
            self.text(M, y, s, 15, SUB)
            y += 24
        return y

    def footer(self, y, s):
        self.line(M, y, self.w - M, y, HAIR, 1)
        y += 26
        for t in wrap(s, self.w - 2 * M, 13):
            self.text(M, y, t, 13, MUTED)
            y += 20
        return y

    def save(self, path, h):
        defs = "".join(
            f'<marker id="m{c[1:]}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M1 1.2L8.6 5L1 8.8" fill="none" stroke="{c}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round"/></marker>' for c in sorted(self.markers))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{int(h)}" '
               f'viewBox="0 0 {self.w} {int(h)}" font-family="{SANS}"><defs>{defs}</defs>'
               f'<rect width="{self.w}" height="{int(h)}" fill="#FFFFFF"/>' + "\n".join(self.o) + "</svg>")
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        open(path, "w", encoding="utf-8").write(svg)
        print("SVG:", os.path.normpath(path), f"{self.w}x{int(h)}")


def chip(s, cx, cy, w, h, role, title, value=None, tsize=14, vsize=14):
    """小卡片：上一行标题（无衬线），下一行等宽的地址。"""
    f, st, tc = role
    s.rect(cx - w / 2, cy - h / 2, w, h, f, st, 1.3, rx=9)
    if value:
        s.text(cx, cy - 4, title, tsize, tc, 600, "middle")
        s.text(cx, cy + vsize + 2, value, vsize, tc, 400, "middle", mono=True)
    else:
        s.text(cx, cy + tsize * 0.36, title, tsize, tc, 600, "middle")




# ------------------------------------------------------------------ 通用部件
KEY = ("#F4F5F7", "#57606A", "#1F2328")      # 中性深色：强调但不表达含义
WHITE = ("#FFFFFF", "#AEB6BE", INK)


def box(s, x, y, w, h, role, title=None, sub=None, ts=15, ss=13, style="fill", align="middle", mono_sub=False,
        pad=14, rx=10, sw=1.3):
    """矩形框，标题和副标题自动换行、整体垂直居中。style: fill 实心浅底 / outline 白底 / dashed 白底虚线。"""
    f, st, tc = role
    s.rect(x, y, w, h, f if style == "fill" else "#FFFFFF", st, sw, rx=rx, dash="5 4" if style == "dashed" else None)
    tl = wrap(title, w - 2 * pad, ts) if title else []
    if sub and mono_sub:
        sl = sub.split("\n")
    else:
        sl = [ln for part in (sub or "").split("\n") for ln in wrap(part, w - 2 * pad, ss)] if sub else []
    th = len(tl) * ts * 1.32 + (7 if tl and sl else 0) + len(sl) * ss * 1.5
    yy = y + (h - th) / 2 + ts * 0.98 if tl else y + (h - th) / 2 + ss * 1.05
    tx = x + w / 2 if align == "middle" else x + pad
    anc = "middle" if align == "middle" else "start"
    for t in tl:
        s.text(tx, yy, t, ts, tc, 600, anc)
        yy += ts * 1.32
    if tl and sl:
        yy += 7 - ts * 1.32 + ss * 1.5 - ss * 0.2
    for t in sl:
        s.text(tx, yy, t, ss, tc if mono_sub else SUB, 400, anc, mono=mono_sub)
        yy += ss * 1.5


def need_h(w, title=None, sub=None, ts=15, ss=13, pad=14, extra=24):
    tl = wrap(title, w - 2 * pad, ts) if title else []
    sl = [ln for part in (sub or "").split("\n") for ln in wrap(part, w - 2 * pad, ss)] if sub else []
    return len(tl) * ts * 1.32 + (7 if tl and sl else 0) + len(sl) * ss * 1.5 + extra


def arrow(s, pts, color=SUB, sw=1.7, dash=None, label=None, lpos=0.5, ldx=0, ldy=-9, lsize=12.5, lcolor=None,
          lanchor="middle", start=False, lweight=600):
    """折线箭头，pts: [(x, y), ...]，终点带箭头；label 放在第一段上（lpos 为位置比例）。"""
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    if start:
        s.markers.add(color)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        s.o.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
                   f'stroke-linejoin="round"{da} marker-start="url(#m{color[1:]})" marker-end="url(#m{color[1:]})"/>')
    else:
        s.path(d, color, sw, dash, end=True)
    if label:
        (x1, y1), (x2, y2) = pts[0], pts[1]
        s.text(x1 + (x2 - x1) * lpos + ldx, y1 + (y2 - y1) * lpos + ldy, label, lsize, lcolor or color, lweight,
               lanchor)


def num(s, cx, cy, n, fill=INK, r=11, size=12.5):
    s.circle(cx, cy, r, fill)
    s.text(cx, cy + size * 0.36, str(n), size, "#FFFFFF", 600, "middle")


def tag(s, x, y, text, anchor="start", size=11.5):
    """灰色小标签（如「第 12 篇」），(x, y) 是标签左上角（anchor=start）或上沿中点（middle）。返回宽度。"""
    w = text_w(text, size) + 14
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    s.rect(x, y, w, size + 9, "#EEF0F2", "none", 0, rx=(size + 9) / 2)
    s.text(x + w / 2, y + size + 2.5, text, size, SUB, 500 if False else 400, "middle")
    return w


def bullets(s, x, y, items, size=14, gap=30, color=INK, dot=None, maxw=None):
    """圆点列表：items 是文字，或 [(文字, 颜色, 字重)] 的混排。返回结束 y。"""
    for it in items:
        s.circle(x + 4, y - size * 0.34, 3.6, dot or SUB)
        if isinstance(it, str):
            lines = wrap(it, maxw, size) if maxw else [it]
            for k, ln in enumerate(lines):
                s.text(x + 16, y + k * size * 1.5, ln, size, color)
            y += gap + (len(lines) - 1) * size * 1.5
        else:
            s.rich(x + 16, y, it, size)
            y += gap
    return y


def title_num(s, x, y, n, text, note=None, size=18):
    """分段标题：黑色序号圆 + 粗体标题 + 灰色备注。"""
    num(s, x + 13, y - size * 0.36, n, INK, 13, 13.5)
    s.text(x + 36, y, text, size, INK, 600)
    if note:
        s.text(x + 36 + text_w(text, size) + 16, y, note, 14, MUTED)
