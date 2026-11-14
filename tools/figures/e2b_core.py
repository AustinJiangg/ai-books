"""《E2B 沙箱网络从零讲透》的配图，输出到 e2b-network/img/。

第 10-1、11-1、13-1 三张图。用法: python3 tools/figures/e2b_core.py

几张图共用一套颜色，含义固定：
- 紫：Firecracker 虚拟机（客户机）
- 蓝：网络命名空间 ns-N
- 灰：宿主机
- 琥珀：地址转换（SNAT / DNAT / MASQUERADE / REDIRECT）和被改过的地址
- 珊瑚：行不通的做法
- 青绿：回程、放行
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from figkit import *  # noqa: E402,F401,F403
from figkit import W, M  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "e2b-network", "img")


def save(s, name, h):
    s.save(os.path.join(OUT, name), h)


# ------------------------------------------------------------------ 第 10 篇
def fig_10():
    s = Svg()
    y0 = s.header("每个沙箱都是 169.254.0.21，靠什么不冲突",
                  "所有沙箱从同一张快照恢复，客户机的网卡配置完全相同。E2B 不去改客户机，而是改客户机外面："
                  "给每个沙箱一个网络命名空间，在命名空间的出口把地址换成各自的 Host IP。")
    top = y0 + 40
    RH, RG = 84, 18                                # 每个沙箱一行
    rows = [top + 96 + i * (RH + RG) for i in range(3)]
    bottom_rows = rows[-1] + RH

    # ---- 左：共用一个网络
    LX0, LX1 = M, 540
    s.rect(LX0, top, LX1 - LX0, bottom_rows - top + 150, "#FCFBFA", HAIR, 1, rx=16)
    s.pill(LX0 + 24 + text_w("行不通", 13) / 2 + 11, top + 34, "行不通", BAD, 13, solid=True)
    s.text(LX0 + 24 + text_w("行不通", 13) + 36, top + 39, "接到同一个网桥上", 18, INK, 600)
    bus_x, host_cx = 352, 462
    for i, ry in enumerate(rows):
        cy = ry + RH / 2
        chip(s, LX0 + 140, cy, 200, 58, VM, f"沙箱 {'ABC'[i]}", "169.254.0.21")
        s.line(LX0 + 240, cy, bus_x, cy, SUB, 1.4)
    s.rect(bus_x - 7, rows[0] + 10, 14, bottom_rows - rows[0] - 20, "#E9E8E3", HOST[1], 1, rx=7)
    s.text(bus_x, rows[0] - 4, "网桥", 13, SUB, 600, "middle")
    mid = (rows[0] + bottom_rows) / 2
    s.line(bus_x + 7, mid, host_cx - 52, mid, SUB, 1.4)
    chip(s, host_cx, mid, 104, 46, HOST, "宿主机")
    py = bottom_rows + 40
    for k, (a, b) in enumerate([("ARP：", "问 169.254.0.21 的 MAC，三台同时回答"),
                                ("MAC：", "同一个 MAC 出现在三个端口"),
                                ("回包：", "目的地址都一样，不知道交给谁")]):
        s.circle(LX0 + 30, py + 34 * k - 5, 4, BAD[1])
        s.rich(LX0 + 44, py + 34 * k, [(a, BAD[2], 600), (b, SUB, 400)], 14.5)

    # ---- 右：E2B 的做法
    RX0, RX1 = 580, W - M
    s.rect(RX0, top, RX1 - RX0, bottom_rows - top + 150, "#FCFBFA", HAIR, 1, rx=16)
    s.pill(RX0 + 24 + text_w("E2B 的做法", 13) / 2 + 11, top + 34, "E2B 的做法", GOOD, 13, solid=True)
    s.text(RX0 + 24 + text_w("E2B 的做法", 13) + 36, top + 39, "每个沙箱一个命名空间，出口换地址", 18, INK, 600)
    NSX0, NSX1 = RX0 + 28, 1190                    # 命名空间框；右边框就是「出口」
    HX0 = 1352                                     # 宿主机列
    # 列标题：里面 / 外面
    s.text((NSX0 + NSX1) / 2, rows[0] - 14, "命名空间里面：三个沙箱完全相同", 14, NS[2], 600, "middle")
    s.text((HX0 + RX1 - 24) / 2, rows[0] - 14, "宿主机看到：各不相同", 14, NAT[2], 600, "middle")
    for i, ry in enumerate(rows):
        n = i + 2
        cy = ry + RH / 2
        s.rect(NSX0, ry, NSX1 - NSX0, RH, NS[0], NS[1], 1.3, rx=12)
        s.text(NSX0 + 18, ry + 24, f"ns-{n}", 13, NS[2], 600)
        chip(s, NSX0 + 172, cy + 6, 172, 54, VM, "客户机", "169.254.0.21")
        s.line(NSX0 + 262, cy + 6, NSX0 + 312, cy + 6, SUB, 1.4, start=True, end=True)
        chip(s, NSX0 + 382, cy + 6, 132, 54, HOST, "tap0", "169.254.0.22")
        s.line(NSX0 + 452, cy + 6, NSX1 - 96, cy + 6, SUB, 1.4, start=True, end=True)
        # 出口：骑在命名空间右边框上的转换点
        gw = 180
        s.rect(NSX1 - gw / 2, cy - 30, gw, 60, NAT[0], NAT[1], 1.6, rx=10)
        s.text(NSX1, cy - 7, "SNAT / DNAT", 13, NAT[2], 600, "middle")
        s.rich(NSX1, cy + 15, [(".21", SUB, 400), (" ⇄ ", MUTED, 400), (f"10.13.0.{n}", NAT[2], 600)], 14,
               "middle", mono=True)
        s.line(NSX1 + gw / 2 + 4, cy, HX0 - 6, cy, SUB, 1.4, start=True, end=True)
        s.text((NSX1 + gw / 2 + HX0) / 2, cy - 9, f"e2bv-{n}", 12.5, MUTED, 400, "middle", mono=True)
    s.rect(HX0, rows[0], RX1 - 24 - HX0, bottom_rows - rows[0], HOST[0], HOST[1], 1.3, rx=12)
    for i, ry in enumerate(rows):
        cy = ry + RH / 2
        s.text(HX0 + 22, cy - 2, f"10.13.0.{i + 2}", 19, NAT[2], 600, mono=True)
        s.text(HX0 + 22, cy + 20, f"Host IP · 属于 ns-{i + 2}", 12.5, SUB)
    py = bottom_rows + 40
    for k, (a, b) in enumerate([("命名空间里：", "只有一个 169.254.0.21、一个 169.254.0.22，不冲突"),
                                ("出口：", "出去的包源地址换成 Host IP（SNAT），进来的包目的地址换回 .21（DNAT）"),
                                ("回包：", "宿主机按各不相同的 Host IP，把回包送回对应的命名空间")]):
        s.circle(RX0 + 30, py + 34 * k - 5, 4, GOOD[1])
        s.rich(RX0 + 44, py + 34 * k, [(a, GOOD[2], 600), (b, SUB, 400)], 14.5)
    y = s.footer(bottom_rows + 186, "注：Host IP 来自地址池 10.13.0.0/16，第 N 号槽位用第 N 个地址（第 11 篇）。"
                                    "命名空间和 NAT 规则在沙箱恢复之前就建好，不拖慢恢复（第 20 篇）。")
    save(s, "10-1-相同地址怎么共存.svg", y + 20)


# ------------------------------------------------------------------ 第 11 篇
def card(s, x, y, w, title, lines, role=HOST, size=13.5):
    """说明卡：标题 + 若干行（每行是 rich 的 parts 列表或纯文字）。返回底边 y。"""
    f, st, tc = role
    h = 40 + 23 * len(lines)
    s.rect(x, y, w, h, "#FFFFFF", st, 1.1, rx=9)
    s.rect(x, y, 5, h, st, st, 0, rx=2)
    s.text(x + 18, y + 25, title, 13.5, tc, 600)
    for k, ln in enumerate(lines):
        parts = ln if isinstance(ln, list) else [(ln, SUB, 400)]
        mono = isinstance(ln, list)
        s.rich(x + 18, y + 50 + 23 * k, parts, size if not mono else 13, mono=mono)
    return y + h


def fig_11():
    s = Svg()
    y0 = s.header("一个槽位拆开看：三层嵌套，三段连接",
                  "以槽位 5 为例。虚拟机在命名空间 ns-5 里，ns-5 在宿主机里。中间的粗线是包从客户机到互联网走的路，"
                  "网卡画在这条路上；每条规则标在它起作用的位置。琥珀色是 Host IP 10.13.0.5 出现的地方。")
    T = y0 + 30
    PY = T + 260                                         # 主路径的 y
    HOSTB = (M, T, 1352, 560)                            # x0, y0, x1, 高
    NSB = (M + 30, T + 52, 944, 476)
    VMB = (M + 60, T + 104, 404, 372)
    for (x0, y, x1, h), role, lab in [(HOSTB, HOST, "宿主机"), (NSB, NS, "网络命名空间 ns-5"),
                                      (VMB, VM, "Firecracker 虚拟机")]:
        s.rect(x0, y, x1 - x0, h, role[0], role[1], 1.4, rx=16)
        s.text(x0 + 20, y + 30, lab, 15, role[2], 600)

    # 主路径与网卡
    INET = (1440, W - M)
    s.line(VMB[2] - 76, PY, INET[0] - 6, PY, INK, 3.2, end=True)
    ports = [  # cx, 宽, 名字, 地址, 色
        (VMB[2] - 76, 116, "eth0", "169.254.0.21/30", VM),
        (548, 92, "tap0", "169.254.0.22/30", NS),
        (872, 136, "eth0（vpeer）", "10.14.0.11/31", NS),
        (1030, 104, "e2bv-5", "10.14.0.10/31", HOST),
        (HOSTB[2] - 92, 140, "enp125s0f0", "192.168.10.23", HOST),
    ]
    for cx, w, name, addr, role in ports:
        chip(s, cx, PY, w, 40, role, name)
        aw = len(addr) * 14 * 0.62 + 12
        s.rect(cx - aw / 2, PY - 52, aw, 26, HOST[0] if role is HOST else NS[0] if role is NS else VM[0], "none", 0, rx=5)
        s.text(cx, PY - 34, addr, 14, INK, 600, "middle", mono=True)
    s.rect(INET[0], PY - 26, INET[1] - INET[0], 52, "#FFFFFF", HOST[1], 1.3, rx=26, dash="5 4")
    s.text((INET[0] + INET[1]) / 2, PY + 5, "互联网", 15, HOST[2], 600, "middle")

    # 三段连接：路径下方的括号
    def seg(x0, x1, n, a, b, lx=None):
        yb = PY + 34
        s.path(f"M{x0} {yb} v8 H{x1} v-8", MUTED, 1.2)
        tx, anc = (lx, "start") if lx else ((x0 + x1) / 2, "middle")
        s.text(tx, yb + 30, f"{n} {a}", 13.5, INK, 600, anc)
        s.text(tx, yb + 50, b, 12.5, SUB, 400, anc)
    seg(VMB[2] - 76, 548, "①", "169.254.0.20/30", "Firecracker 搬运帧", lx=VMB[2] + 14)
    seg(872 - 68, 1030 + 52, "②", "veth 对", "10.14.0.10/31", lx=NSB[2] + 14)
    seg(HOSTB[2] - 92, INET[0] + 40, "③", "物理网络", "")

    # 虚拟机里
    vy = PY + 112
    s.text(VMB[0] + 22, vy, "客户机的网络配置", 13.5, VM[2], 600)
    s.rich(VMB[0] + 22, vy + 26, [("网关 ", SUB, 400), ("169.254.0.22", INK, 600)], 13, mono=True)
    s.rich(VMB[0] + 22, vy + 49, [("MAC  ", SUB, 400), ("02:FC:00:00:00:05", INK, 600)], 13, mono=True)
    s.text(VMB[0] + 22, vy + 74, "来自模板快照，每个沙箱都一样", 13, SUB)
    # 命名空间里
    card(s, 500, T + 90, 420, "ns-5 的路由", [
        [("default via 10.14.0.10 dev eth0", INK, 400)],
        [("169.254.0.20/30 dev tap0", INK, 400)]], NS)
    nf_b = card(s, 492, PY + 110, 172, "nftables", ["只查从 tap0", "进来的包"], NS)
    s.line(572, PY + 22, 572, PY + 108, NS[1], 1.2, dash="3 3")
    card(s, 684, PY + 110, 244, "NAT（在 eth0 一侧）", [
        [("出 SNAT 源→", SUB, 400), ("10.13.0.5", NAT[2], 700)],
        [("入 DNAT ", SUB, 400), ("10.13.0.5", NAT[2], 700), ("→.21", SUB, 400)]], NAT)
    s.line(836, PY + 22, 836, PY + 108, NAT[1], 1.2, dash="3 3")
    # 宿主机里
    card(s, 984, T + 66, 352, "宿主机的路由", [
        [("10.13.0.5", NAT[2], 700), (" via 10.14.0.11 dev e2bv-5", INK, 400)],
        [("default via 网关 dev enp125s0f0", INK, 400)]], HOST)
    card(s, 984, PY + 110, 352, "宿主机的 iptables（第 12 篇）", [
        "FORWARD 放行、MASQUERADE：UDP 等",
        "REDIRECT：TCP 交给防火墙代理"], HOST)
    hb = HOSTB[1] + HOSTB[3]
    s.rect(HOSTB[0], hb + 24, HOSTB[2] - HOSTB[0], 50, NAT[0], NAT[1], 1, rx=10, dash="5 4")
    s.rich(HOSTB[0] + 20, hb + 55, [("Host IP 10.13.0.5", NAT[2], 700),
                                    ("  不在任何一块网卡上，只出现在宿主机那条路由和 ns-5 的 NAT 规则里：宿主机按它找到 e2bv-5，"
                                     "ns-5 把它换成 169.254.0.21。", SUB, 400)], 14)
    y = s.footer(hb + 110, "注：客户机里的 eth0 和命名空间里的 eth0（vpeer）只是重名。10.13.0.5、10.14.0.10/11 由槽位编号 5 算出"
                           "（本篇第三节）；169.254.0.21/22 与编号无关，每个槽位都一样。")
    save(s, "11-1-一个槽位的拓扑.svg", y + 20)


# ------------------------------------------------------------------ 第 13 篇
ZX = [M, 330, 790, 1310, W - M]        # 四列的边界：客户机 | ns-5 | 宿主机 | 互联网
CW, CH = 236, 60                       # 地址卡片


def pkt(s, cx, cy, src, dst, changed=(), tag=None):
    """一张地址卡片：包经过某块网卡时的源和目的。changed 里的字段（'src'/'dst'）用琥珀色标出。"""
    x, y = cx - CW / 2, cy - CH / 2
    s.rect(x, y, CW, CH, "#FFFFFF", "#AEB6BE", 1.2, rx=9)
    for k, (lab, val, key) in enumerate([("源", src, "src"), ("目的", dst, "dst")]):
        ly = y + 8 + 22 * k
        if key in changed:
            s.rect(x + 6, ly, CW - 12, 22, NAT[0], NAT[0], 0, rx=5)
        s.text(x + 14, ly + 16, lab, 12, MUTED)
        s.text(x + 50, ly + 16, val, 14, NAT[2] if key in changed else INK, 700 if key in changed else 400,
               mono=True)
    if tag:
        s.pill(cx, y - 13, tag, HOST, 11.5, solid=True, h=20)


def op(s, cx, cy, name, note=None, role=NAT):
    w = s.pill(cx, cy, name, role, 13, h=28)
    if note:
        for k, t in enumerate(note if isinstance(note, list) else [note]):
            s.text(cx, cy + 32 + 18 * k, t, 12.5, SUB, 400, "middle")
    return w


def endpoint(s, cx, cy, title, value=None, role=HOST, w=136):
    chip(s, cx, cy, w, 52 if value else 40, role, title, value, 13.5, 13)


def fig_13():
    s = Svg()
    y0 = s.header("跟着三个包走一遍：地址在哪里被改、被谁改",
                  "槽位 5。每张卡片是包经过那块网卡时的源地址和目的地址，琥珀色是刚被改过的字段。"
                  "去互联网的 UDP 包被改两次；TCP 包在宿主机被交给防火墙代理，代理另开一条连接；宿主机连沙箱时只改目的地址。")
    top = y0 + 34
    hdr_h = 44
    # 列底色和列标题
    roles = [VM, NS, HOST, ("#FFFFFF", HAIR, SUB)]
    names = ["客户机", "命名空间 ns-5", "宿主机", "互联网"]
    tracks_top = top + hdr_h
    H = 760
    for i in range(4):
        f, st, tc = roles[i]
        s.rect(ZX[i], top, ZX[i + 1] - ZX[i], H, f if i < 3 else "#FFFFFF", "none", 0, rx=0)
        s.text((ZX[i] + ZX[i + 1]) / 2, top + 28, names[i], 15, tc, 600, "middle")
    s.rect(ZX[0], top, ZX[4] - ZX[0], H, "none", HAIR, 1, rx=14)
    for i, nm in [(1, "tap0"), (2, "veth：e2bv-5"), (3, "enp125s0f0")]:
        s.line(ZX[i], top + 40, ZX[i], top + H - 8, "#C9D1D9", 1, dash="4 4")
        s.pill(ZX[i], top + hdr_h + 2, nm, ("#FFFFFF", "#AEB6BE", SUB), 11.5, mono=True, h=20)

    def title(y, n, a, b):
        s.circle(M + 26, y - 5, 12, INK)
        s.text(M + 26, y, str(n), 13, "#FFFFFF", 600, "middle")
        s.rich(M + 46, y, [(a, INK, 600), ("   " + b, SUB, 400)], 15.5)

    # ---- 旅程一：UDP
    y = tracks_top + 50
    title(y, 1, "UDP：DNS 查询发往 8.8.8.8:53", "两次地址转换，两张 conntrack 表各记一笔")
    cy = y + 66
    s.line(ZX[0] + 150, cy, 1440 - 4, cy, INK, 2.2, end=True)
    endpoint(s, ZX[0] + 82, cy, "客户机程序", None, VM, 124)
    pkt(s, ZX[1], cy, "169.254.0.21:41234", "8.8.8.8:53")
    op(s, 560, cy, "SNAT", "nftables 先检查：放行")
    pkt(s, ZX[2], cy, "10.13.0.5:41234", "8.8.8.8:53", {"src"})
    op(s, 1050, cy, "MASQUERADE", "先过 FORWARD 放行")
    pkt(s, ZX[3], cy, "192.168.10.23:41234", "8.8.8.8:53", {"src"})
    endpoint(s, 1496, cy, "8.8.8.8", None, ("#FFFFFF", "#AEB6BE", INK), 104)
    ry = cy + 64
    s.line(1420, ry, ZX[0] + 150, ry, GOOD[1], 1.6, dash="6 4", end=True)
    s.rich(ZX[0] + 150, ry + 24, [("回程  ", GOOD[2], 600), ("宿主机的 conntrack 把目的改回 10.13.0.5，"
                                    "ns-5 的 conntrack 再改回 169.254.0.21", SUB, 400)], 13)

    # ---- 旅程二：TCP
    s.line(ZX[0] + 16, ry + 50, ZX[4] - 16, ry + 50, HAIR, 1)
    y = ry + 92
    title(y, 2, "TCP：连接 pypi.org（151.101.0.223:443）", "宿主机把它交给防火墙代理，一条连接变成两条")
    cy = y + 66
    PX0, PX1 = 1046, 1176                       # 代理框
    cy2 = cy + 104
    s.line(ZX[0] + 150, cy, PX0 - 4, cy, INK, 2.2, end=True)
    endpoint(s, ZX[0] + 82, cy, "客户机程序", None, VM, 124)
    pkt(s, ZX[1], cy, "169.254.0.21:51000", "151.101.0.223:443", tag="连接 ①")
    op(s, 560, cy, "SNAT", "和 UDP 相同")
    pkt(s, ZX[2], cy, "10.13.0.5:51000", "151.101.0.223:443", {"src"})
    op(s, 976, cy, "REDIRECT", ["目的改成", "10.14.0.10:5017"])
    s.rect(PX0, cy - 34, PX1 - PX0, cy2 - cy + 68, GOOD[0], GOOD[1], 1.5, rx=10)
    s.text((PX0 + PX1) / 2, cy - 6, "防火墙代理", 14, GOOD[2], 600, "middle")
    s.text((PX0 + PX1) / 2, cy + 14, ":5017", 13, GOOD[2], 400, "middle", mono=True)
    for k, t in enumerate(["读 SNI：", "pypi.org", "判定放行"]):
        s.text((PX0 + PX1) / 2, cy + 46 + 19 * k, t, 12.5, GOOD[2], 600 if k == 1 else 400, "middle")
    s.line(PX1 + 4, cy2, 1440 - 4, cy2, INK, 2.2, end=True)
    pkt(s, ZX[3], cy2, "192.168.10.23:随机", "151.101.0.223:443", {"src"}, tag="连接 ②：代理新开")
    endpoint(s, 1496, cy2, "pypi.org", None, ("#FFFFFF", "#AEB6BE", INK), 104)
    s.text(560, cy2 + 6, "连接 ① 的另一头是代理，客户机以为自己连的是 151.101.0.223:443", 13, SUB, 400, "middle")

    # ---- 旅程三：宿主机连 envd
    yl = cy2 + 56
    s.line(ZX[0] + 16, yl, ZX[4] - 16, yl, HAIR, 1)
    y = yl + 42
    title(y, 3, "反方向：orchestrator 连沙箱里的 envd", "宿主机只认 Host IP，进命名空间时换成 169.254.0.21")
    cy = y + 66
    s.line(1180, cy, ZX[0] + 150, cy, INK, 2.2, end=True)
    endpoint(s, ZX[0] + 82, cy, "envd", ":49983", VM, 124)
    pkt(s, ZX[1], cy, "10.14.0.10:38000", "169.254.0.21:49983", {"dst"})
    op(s, 560, cy, "DNAT", "按 /32 路由进来后改目的")
    pkt(s, ZX[2], cy, "10.14.0.10:38000", "10.13.0.5:49983")
    endpoint(s, 1250, cy, "orchestrator", None, HOST, 132)
    ry = cy + 64
    s.rich(ZX[0] + 150, ry, [("回程  ", GOOD[2], 600), ("envd 回包的目的 10.14.0.10 在 nftables 的拦截集合 10.0.0.0/8 里，"
                              "但第一条规则先放行已建立连接的包，所以回得去；沙箱主动连 10.x 会被拦。", SUB, 400)], 13)
    y = s.footer(top + H + 30, "注：nftables 只检查从 tap0 进来的包。连接 ② 是宿主机本机发出的，不经过 FORWARD 和 MASQUERADE。"
                               "代理的判定规则见第 16 篇，全书地址转换总表见第 19 篇。")
    save(s, "13-1-出站包的两条路.svg", y + 20)


if __name__ == "__main__":
    fig_10()
    fig_11()
    fig_13()
