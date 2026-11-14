"""《E2B 沙箱网络从零讲透》第 1～4 篇的配图。用法: python3 tools/figures/e2b_p1a.py"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from figkit import *  # noqa: E402,F401,F403
from figkit import W, M  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "e2b-network", "img")


def save(s, name, h):
    s.save(os.path.join(OUT, name), h)


# ------------------------------------------------------------------ 第 1 篇：全景图
def fig_01_map():
    s = Svg()
    y0 = s.header("全书地图：一个沙箱的网络，和进出它的四类流量",
                  "以单机部署、槽位 5 为例。每个部件下方的灰色标签是详细讲它的篇目；带圈数字是四类流量："
                  "① 出站（沙箱访问外部） ② 入站（SDK、浏览器访问沙箱） ③ 控制（orchestrator 直接调用 envd） ④ 内部服务（沙箱访问宿主机上的服务）。")
    T = y0 + 26
    # 宿主机外：SDK 与互联网
    box(s, M, T, 250, 56, WHITE, "SDK / 浏览器", None, 15, style="outline")
    box(s, W - M - 250, T, 250, 56, WHITE, "互联网 · pypi.org", None, 15, style="outline")
    HT = T + 96
    HB = HT + 58 + 76 + 70 + 300 + 30
    s.rect(M, HT, W - 2 * M, HB - HT, HOST[0], HOST[1], 1.4, rx=16)
    s.text(M + 20, HT + 30, "宿主机", 16, HOST[2], 600)

    # 入口一侧
    ey = HT + 58
    eh = 76
    EX = 1040                                  # e2bv-5 与 Host IP 竖线的 x
    box(s, 84, ey, 300, eh, WHITE, "宿主机入口", "dnsmasq：*.e2b.app → 127.0.0.1\niptables：80 → 3002", 14.5, 12.5,
        style="outline")
    tag(s, 234, ey + eh + 8, "第 17 篇", "middle")
    box(s, 460, ey, 220, eh, WHITE, "client-proxy", ":3002　按沙箱 ID 转发", 14.5, 12.5, style="outline")
    tag(s, 570, ey + eh + 8, "第 18 篇", "middle")
    box(s, 756, ey, 360, eh, WHITE, "orchestrator", "代理 :5007；也负责建网、运行防火墙代理", 14.5, 12.5, style="outline")
    tag(s, 936, ey + eh + 8, "第 12、18 篇", "middle")
    arrow(s, [(M + 125, T + 56), (M + 125, ey)], INK, 1.8)
    num(s, M + 146, (T + 56 + ey) / 2 + 2, 2)
    arrow(s, [(384, ey + eh / 2), (456, ey + eh / 2)], INK, 1.8)
    arrow(s, [(680, ey + eh / 2), (752, ey + eh / 2)], INK, 1.8)

    # 沙箱一侧
    sy = ey + eh + 70
    NS0, NS1 = 84, 934
    nsh = 300
    LY = sy + 210
    s.rect(NS0, sy, NS1 - NS0, nsh, NS[0], NS[1], 1.4, rx=14)
    s.text(NS0 + 18, sy + 28, "网络命名空间 ns-5", 15, NS[2], 600)
    tag(s, NS0 + 170, sy + 13, "第 10、11 篇")
    VX0, VX1 = 108, 336
    s.rect(VX0, sy + 52, VX1 - VX0, nsh - 76, VM[0], VM[1], 1.4, rx=12)
    s.text(VX0 + 16, sy + 78, "Firecracker 虚拟机", 14, VM[2], 600)
    tag(s, VX0 + 16, sy + 88, "第 9 篇")
    chip(s, 200, sy + 148, 150, 48, VM, "envd", ":49983", 13.5, 12.5)
    chip(s, 270, LY, 100, 48, VM, "eth0", "169.254.0.21", 13, 12)
    chip(s, 400, LY, 96, 48, NS, "tap0", "169.254.0.22", 13, 12)
    box(s, 490, LY - 34, 120, 68, ("#FFFFFF", NS[1], NS[2]), "nftables", "出站过滤", 14, 12.5)
    tag(s, 550, LY + 42, "第 8、15 篇", "middle")
    box(s, 650, LY - 34, 120, 68, NAT, "NAT", "SNAT / DNAT", 14, 12.5)
    tag(s, 710, LY + 42, "第 7、13 篇", "middle")
    chip(s, 860, LY, 100, 48, NS, "eth0", "vpeer", 13, 12)
    for a, b in [(320, 352), (448, 490), (610, 650), (770, 810)]:
        s.line(a + 4, LY, b - 4, LY, INK, 1.6, start=True, end=True)
    # veth 与宿主机一侧
    chip(s, EX, LY, 110, 48, HOST, "e2bv-5", "10.14.0.10", 13, 12)
    s.line(914, LY, EX - 59, LY, INK, 2.4, start=True, end=True)
    s.text((NS1 + EX - 55) / 2 + 2, LY - 14, "veth", 12.5, SUB, 600, "middle")
    tag(s, (NS1 + EX - 55) / 2 + 2, LY + 12, "第 6 篇", "middle")
    # orchestrator → Host IP → e2bv-5
    arrow(s, [(EX, ey + eh), (EX, LY - 28)], INK, 1.8)
    s.text(EX + 14, ey + eh + 56, "Host IP 10.13.0.5:49983", 13, NAT[2], 700, mono=True)
    s.text(EX + 14, ey + eh + 76, "按 /32 路由交给 e2bv-5", 12.5, SUB)
    num(s, EX - 20, ey + eh + 52, 2)
    num(s, EX - 20, ey + eh + 80, 3)
    # 三个去处
    DX0, DX1 = 1150, 1350
    dest = [(sy + 30, "防火墙代理", ":5016–5018　TCP 按域名判定", "第 16 篇", GOOD),
            (sy + 128, "转发 + MASQUERADE", "UDP、ICMP 等", "第 12、13 篇", WHITE),
            (sy + 226, "宿主服务 192.0.2.1", "hyperloop · NFS · portmap", "第 19 篇", WHITE)]
    for k, (dy, t, sub, tg, role) in enumerate(dest):
        box(s, DX0, dy, DX1 - DX0, 70, role, t, sub, 14, 12, style="fill" if role is GOOD else "outline")
        tag(s, DX1 - 6, dy + 74, tg, "end")
        arrow(s, [(EX + 55, LY), (EX + 78, LY), (EX + 78, dy + 35), (DX0 - 4, dy + 35)], INK, 1.6)
    num(s, DX0 - 22, sy + 226 + 12, 4)
    # 物理网卡：防火墙代理和转发两条路在这里出宿主机
    NX = 1462
    NY = sy + 65
    chip(s, NX, NY, 140, 52, HOST, "enp125s0f0", "192.168.10.23", 13, 12)
    arrow(s, [(DX1, NY), (NX - 74, NY)], INK, 1.6)
    arrow(s, [(DX1, sy + 163), (NX, sy + 163), (NX, NY + 30)], INK, 1.6)
    tag(s, NX + 74, sy + 172, "第 13 篇", "end")
    arrow(s, [(NX, NY - 26), (NX, T + 60)], INK, 1.8)
    num(s, NX + 20, (NY - 26 + T + 60) / 2, 1)
    yy = s.footer(HB + 34, "注：沙箱里看到的永远是 169.254.0.21；宿主机只认 Host IP 10.13.0.5。两者在 ns-5 的 NAT 处互换（第 10 篇）。"
                           "TCP 出站全部经过防火墙代理，代理另开连接从物理网卡出去。")
    save(s, "01-1-全书地图.svg", yy + 20)


# ------------------------------------------------------------------ 第 2 篇：CIDR
def bits_of(ip):
    return "".join(f"{int(p):08b}" for p in ip.split("."))


def fig_02_cidr():
    s = Svg()
    y0 = s.header("斜杠后面的数字：前多少位是网络号",
                  "IPv4 地址是 32 个比特。/n 表示前 n 位是网络号（蓝），剩下 32−n 位是主机号（白），子网里一共 2^(32−n) 个地址。"
                  "下面四行是本书用到的四种长度，每行都是一个真实的 E2B 地址。")
    CX0, CWD, GAP = 250, 21, 12           # 比特格子
    rows = [("/16", "10.13.0.0", 16, "65536 个地址", ["Host 池 10.13.0.0/16", "VRT 池 10.14.0.0/16，都是 /16"]),
            ("/30", "169.254.0.20", 30, "4 个地址", ["客户机与 tap0 之间的小网段：", ".20 网络地址 · .21 客户机 · .22 tap0 · .23 广播"]),
            ("/31", "10.14.0.10", 31, "2 个地址", ["每个槽位的一对 veth：.10 宿主机侧 · .11 命名空间侧", "点对点链路不需要广播，两个都能用"]),
            ("/32", "10.13.0.5", 32, "1 个地址", ["单个地址：沙箱的 Host IP", "用在路由表和防火墙规则里精确指定一个地址"])]
    y = y0 + 40
    for name, ip, n, cnt, info in rows:
        b = bits_of(ip)
        s.text(M, y + 52, name, 34, INK, 600, mono=True)
        s.text(M + 96, y + 44, ip, 15, INK, 600, mono=True)
        s.text(M + 96, y + 66, cnt, 13, SUB)
        xs = []
        for i, ch in enumerate(b):
            x = CX0 + i * CWD + (i // 8) * GAP
            xs.append(x)
            net = i < n
            s.rect(x, y + 26, CWD - 3, 34, NS[0] if net else "#FFFFFF", NS[1] if net else HAIR, 1, rx=4)
            s.text(x + (CWD - 3) / 2, y + 48, ch, 13, NS[2] if net else MUTED, 600 if net else 400, "middle", mono=True)
        for g in range(4):
            gx = CX0 + g * (8 * CWD + GAP) + 4 * CWD - 1.5
            s.text(gx, y + 82, ip.split(".")[g], 12.5, SUB, 400, "middle", mono=True)
        # 网络号 / 主机号括号
        xe = xs[n - 1] + CWD - 3
        s.path(f"M{CX0} {y + 18} v-6 H{xe} v6", NS[1], 1.2)
        s.text((CX0 + xe) / 2, y + 6, f"网络号 {n} 位", 12, NS[2], 600, "middle")
        if n < 32:
            xh0, xh1 = xs[n], xs[-1] + CWD - 3
            s.path(f"M{xh0} {y + 18} v-6 H{xh1} v6", MUTED, 1.2)
            if xh1 - xh0 > 60:
                s.text((xh0 + xh1) / 2, y + 6, f"主机号 {32 - n} 位", 12, SUB, 600, "middle")
            else:
                s.text(xh1 + 8, y + 6, f"主机号 {32 - n} 位", 12, SUB, 600)
        ix = 1010
        s.text(ix, y + 40, info[0], 14, INK, 600)
        s.text(ix, y + 63, info[1], 13, SUB)
        y += 116
    yy = s.footer(y + 8, "注：普通子网的第一个地址（主机号全 0）是网络地址，最后一个（主机号全 1）是广播地址，都不分给设备；/31 是例外（RFC 3021）。")
    save(s, "02-1-CIDR前缀.svg", yy + 20)


def fig_02_nth():
    s = Svg()
    y0 = s.header("从地址池算出第 N 个地址：起点当整数，加上偏移",
                  "槽位编号 N 决定它的两段地址：VRT 池切成一块块 /31，第 N 块从第 2N 个地址开始；Host 池直接取第 N 个地址。以 N = 5 为例。")
    CW_, CH_ = 74, 48
    # VRT 池
    y = y0 + 50
    s.text(M, y, "VRT 池 10.14.0.0/16，切成 /31", 17, INK, 600)
    y += 26
    x0 = M + 10
    for k in range(14):
        blk = k // 2
        x = x0 + k * (CW_ + 4) + blk * 14
        hit = blk == 5
        s.rect(x, y, CW_, CH_, NAT[0] if hit else "#FFFFFF", NAT[1] if hit else HAIR, 1.4 if hit else 1, rx=6)
        s.text(x + CW_ / 2, y + 30, f".{k}", 15, NAT[2] if hit else INK, 600 if hit else 400, "middle", mono=True)
        if k % 2 == 0:
            bx0, bx1 = x, x + 2 * CW_ + 4
            s.path(f"M{bx0} {y + CH_ + 8} v6 H{bx1} v-6", NAT[1] if hit else MUTED, 1.2)
            s.text((bx0 + bx1) / 2, y + CH_ + 32, f"块 {blk}", 13, NAT[2] if hit else SUB, 600 if hit else 400, "middle")
    xe = x0 + 14 * (CW_ + 4) + 6 * 14
    s.text(xe + 8, y + 30, "…", 18, MUTED)
    y += CH_ + 64
    s.rich(M + 10, y, [("第 5 块的起点 = 10.14.0.0 + 5 × 2 = ", SUB, 400), ("10.14.0.10", NAT[2], 700),
                       ("（宿主机侧 e2bv-5），下一个 ", SUB, 400), ("10.14.0.11", NAT[2], 700), ("（命名空间侧 vpeer）", SUB, 400)], 15)
    # Host 池
    y += 64
    s.text(M, y, "Host 池 10.13.0.0/16，每个槽位一个地址", 17, INK, 600)
    y += 26
    for k in range(8):
        x = x0 + k * (CW_ + 18)
        hit = k == 5
        s.rect(x, y, CW_, CH_, NAT[0] if hit else "#FFFFFF", NAT[1] if hit else HAIR, 1.4 if hit else 1, rx=6)
        s.text(x + CW_ / 2, y + 30, f".{k}", 15, NAT[2] if hit else INK, 600 if hit else 400, "middle", mono=True)
        s.text(x + CW_ / 2, y + CH_ + 22, f"第 {k} 个", 12.5, NAT[2] if hit else SUB, 600 if hit else 400, "middle")
    s.text(x0 + 8 * (CW_ + 18), y + 30, "…", 18, MUTED)
    y += CH_ + 60
    s.rich(M + 10, y, [("第 5 个 = 10.13.0.0 + 5 = ", SUB, 400), ("10.13.0.5", NAT[2], 700), ("，这就是槽位 5 的 Host IP", SUB, 400)], 15)
    # 进位
    y += 62
    box(s, M, y, W - 2 * M, 74, ("#F7F8FA", HAIR, INK), None, None)
    s.text(M + 22, y + 30, "数字大了会进位，和十进制一样，只是每段满 256 进 1", 14.5, INK, 600)
    s.rich(M + 22, y + 56, [("槽位 300：Host IP = 10.13.0.0 + 300，300 = 1 × 256 + 44 → ", SUB, 400), ("10.13.1.44", NAT[2], 700),
                            ("；veth = 10.14.0.0 + 600，600 = 2 × 256 + 88 → ", SUB, 400), ("10.14.2.88", NAT[2], 700),
                            (" / ", SUB, 400), ("10.14.2.89", NAT[2], 700)], 14)
    yy = s.footer(y + 74 + 34, "注：反过来也成立，看到 10.13.1.44 就知道是槽位 300，去 ns-300 排查（第 11 篇）。")
    save(s, "02-2-第N个地址.svg", yy + 20)


# ------------------------------------------------------------------ 第 3 篇
L2 = ("#F1F0EC", "#A8A69D", "#3D3C38")
L3 = NS
L4 = VM


def fig_03_frame():
    s = Svg()
    y0 = s.header("帧套包：每过一站换外层的 MAC，里面的 IP 不变",
                  "网线上传的是以太网帧。帧头写着这一段的 MAC 地址，里面装着 IP 包，IP 包里装着 TCP 或 UDP。"
                  "路由器每转发一次，拆掉旧帧头、换上下一段的 MAC；IP 包里的地址原样往下传（NAT 是例外）。")
    # 上：嵌套结构
    y = y0 + 40
    X0, X1 = M, W - M
    H = 132
    s.rect(X0, y, X1 - X0, H, L2[0], L2[1], 1.3, rx=12)
    s.text(X0 + 16, y + 24, "以太网帧（第二层）", 13.5, L2[2], 600)
    fx = X0 + 16
    for t, w in [("目的 MAC", 150), ("源 MAC", 150), ("类型 0x0800", 140)]:
        box(s, fx, y + 38, w, 78, ("#FFFFFF", L2[1], L2[2]), t, None, 14)
        fx += w + 10
    ix0 = fx + 6
    s.rect(ix0, y + 30, X1 - 16 - ix0, H - 44, L3[0], L3[1], 1.3, rx=10)
    s.text(ix0 + 14, y + 50, "IP 包（第三层）", 13, L3[2], 600)
    fx = ix0 + 14
    for t, w in [("源 IP", 120), ("目的 IP", 120), ("协议", 80)]:
        box(s, fx, y + 60, w, 50, ("#FFFFFF", L3[1], L3[2]), t, None, 14)
        fx += w + 8
    tx0 = fx + 6
    s.rect(tx0, y + 56, X1 - 30 - tx0, 60, L4[0], L4[1], 1.3, rx=8)
    s.text(tx0 + 12, y + 74, "TCP / UDP（第四层）", 12.5, L4[2], 600)
    fx = tx0 + 12
    for t, w in [("源端口", 92), ("目的端口", 92)]:
        box(s, fx, y + 82, w, 28, ("#FFFFFF", L4[1], L4[2]), t, None, 12.5)
        fx += w + 6
    box(s, fx, y + 82, X1 - 42 - fx, 28, ("#FFFFFF", HAIR, INK), "数据", None, 12.5)

    # 下：一次转发前后
    y += H + 64
    s.text(M, y, "例子：主机 A 经过路由器 R 发给主机 B", 18, INK, 600)
    s.text(M + text_w("例子：主机 A 经过路由器 R 发给主机 B", 18) + 16, y, "两段网线，两张帧头，同一个 IP 包", 14, MUTED)
    y += 40
    hy = y + 150
    hosts = [(170, "主机 A", "IP 192.168.1.10", "MAC aa:aa"), (800, "路由器 R", "左口 MAC r1:r1 · 右口 MAC r2:r2", ""),
             (1430, "主机 B", "IP 10.0.0.20", "MAC bb:bb")]
    for cx, t, a, b in hosts:
        box(s, cx - 120 if cx != 800 else cx - 150, hy - 40, 240 if cx != 800 else 300, 80, WHITE, t,
            a + ("\n" + b if b else ""), 15, 12.5, style="outline")
    s.line(290, hy, 650, hy, SUB, 2)
    s.line(950, hy, 1310, hy, SUB, 2)
    s.text(470, hy + 26, "第一段网线", 12.5, MUTED, 400, "middle")
    s.text(1130, hy + 26, "第二段网线", 12.5, MUTED, 400, "middle")

    def frame(cx, top, dmac, smac):
        w = 400
        x = cx - w / 2
        s.rect(x, top, w, 74, "#FFFFFF", "#AEB6BE", 1.2, rx=9)
        s.rect(x + 8, top + 8, 160, 58, NAT[0], NAT[1], 1, rx=6)
        s.text(x + 18, top + 31, f"目的 MAC {dmac}", 12.5, NAT[2], 600, mono=True)
        s.text(x + 18, top + 53, f"源 MAC {smac}", 12.5, NAT[2], 600, mono=True)
        s.rect(x + 176, top + 8, w - 184, 58, L3[0], L3[1], 1, rx=6)
        s.text(x + 190, top + 31, "源 IP 192.168.1.10", 12.5, L3[2], 600, mono=True)
        s.text(x + 190, top + 53, "目的 IP 10.0.0.20", 12.5, L3[2], 600, mono=True)
    frame(470, y - 6, "r1:r1", "aa:aa")
    frame(1130, y - 6, "bb:bb", "r2:r2")
    for cx in (470, 1130):
        s.line(cx, y + 70, cx, hy - 4, MUTED, 1.2, dash="3 3")
        s.circle(cx, hy, 4, MUTED)
    arrow(s, [(690, y + 30), (910, y + 30)], NAT[1], 1.8, label="R 拆掉旧帧头，换上新帧头", ldy=-10, lcolor=NAT[2])
    yy = hy + 86
    s.rich(M, yy, [("琥珀色", NAT[2], 700), ("：每段都会变的 MAC 地址。", SUB, 400), ("  蓝色", L3[2], 700),
                   ("：从头到尾不变的 IP 地址。R 怎么知道下一段该填 bb:bb？查路由表定下一站，再用 ARP 问到它的 MAC。", SUB, 400)], 14)
    yy = s.footer(yy + 34, "注：tap 设备收发的就是这种完整的以太网帧，所以虚拟机的网卡像接了一根真网线（第 6、9 篇）。")
    save(s, "03-1-帧套包.svg", yy + 20)


def fig_03_lpm():
    s = Svg()
    y0 = s.header("最长前缀匹配：去 10.13.0.5 的包选最具体的那条路由",
                  "一个目的地址可能同时匹配好几条路由，内核选前缀最长的一条。下面是宿主机的路由表，逐条检查目的地址 10.13.0.5 落不落在这一段里。")
    y = y0 + 40
    s.pill(M + 120, y + 16, "目的 IP 10.13.0.5", NAT, 15, mono=True, h=34)
    y += 60
    cols = [M, 520, 820, 1010, 1210]
    heads = ["路由", "这一段的范围", "前缀长度", "包含 10.13.0.5？", "结果"]
    for x, h in zip(cols, heads):
        s.text(x + 14, y, h, 13, MUTED, 600)
    y += 14
    routes = [("default via 192.168.10.1 dev enp125s0f0", "0.0.0.0/0：所有地址", 0, True, "匹配，但只有 0 位"),
              ("192.168.10.0/24 dev enp125s0f0", "192.168.10.0 ～ .255", 24, False, ""),
              ("10.13.0.5 via 10.14.0.11 dev e2bv-5", "只有 10.13.0.5 自己", 32, True, "选中：最长"),
              ("10.14.0.10/31 dev e2bv-5", "10.14.0.10 ～ .11", 31, False, "")]
    for k, (r, rng, n, hit, res) in enumerate(routes):
        ry = y + k * 64
        chosen = n == 32
        s.rect(M, ry, W - 2 * M, 54, NAT[0] if chosen else ("#F7F8FA" if k % 2 == 0 else "#FFFFFF"),
               NAT[1] if chosen else "none", 1.4 if chosen else 0, rx=8)
        s.text(cols[0] + 14, ry + 33, r, 13.5, INK, 600 if chosen else 400, mono=True)
        s.text(cols[1] + 14, ry + 33, rng, 13.5, SUB)
        # 前缀长度条
        bw = 150
        s.rect(cols[2] + 14, ry + 21, bw, 12, "#E6E8EB", "none", 0, rx=6)
        if n:
            s.rect(cols[2] + 14, ry + 21, bw * n / 32, 12, NS[1], "none", 0, rx=6)
        s.text(cols[2] + 14 + bw + 10, ry + 32, f"/{n}", 13, INK, 600, mono=True)
        s.text(cols[3] + 14, ry + 33, "是" if hit else "否", 14, GOOD[2] if hit else MUTED, 600 if hit else 400)
        if res:
            s.text(cols[4] + 14, ry + 33, res, 14, NAT[2] if chosen else SUB, 600 if chosen else 400)
    y += 4 * 64 + 30
    box(s, M, y, W - 2 * M, 84, ("#FFFFFF", NAT[1], INK), None, None, style="outline")
    s.text(M + 22, y + 32, "结果：从 e2bv-5 发出，下一跳 10.14.0.11", 16, INK, 600)
    s.text(M + 22, y + 60, "“via” 只决定把帧交给谁：内核用 ARP 查到 10.14.0.11 的 MAC 填进帧头；包里的目的 IP 仍然是 10.13.0.5。", 14, SUB)
    yy = s.footer(y + 84 + 34, "注：一条默认路由兜底，再用更具体的路由处理特殊目的地。E2B 每建一个槽位，就在宿主机上加一条这样的 /32 路由（第 12 篇）。")
    save(s, "03-2-最长前缀匹配.svg", yy + 20)


# ------------------------------------------------------------------ 第 4 篇
def fig_04_tcp():
    s = Svg()
    y0 = s.header("一条 TCP 连接的一生：两端各记一份状态",
                  "以沙箱里的 pip 连接 pypi.org 为例。中间是来回的包，两侧是两端各自记下的连接状态。"
                  "连接不是一根线，而是两端内存里对得上的两份记录：对方的地址和端口、序列号、确认号、所处阶段。")
    CX, SX = 560, 1040                 # 两条生命线
    y = y0 + 40
    box(s, CX - 130, y, 260, 58, NS, "客户端", "169.254.0.21:51234", 15, 12.5, mono_sub=True)
    box(s, SX - 130, y, 260, 58, WHITE, "服务端", "151.101.0.223:443", 15, 12.5, style="outline", mono_sub=True)
    top = y + 58
    msgs = [("hs", "→", "SYN  seq=x", "我想连你，我的起始编号是 x"),
            ("hs", "←", "SYN+ACK  seq=y ack=x+1", "好，我的起始编号是 y"),
            ("hs", "→", "ACK  ack=y+1", None),
            ("data", "→", "数据  seq=x+1", "带上这段数据的编号"),
            ("data", "←", "ACK  ack=x+1+长度", "收到这里之前的全部数据"),
            ("fin", "→", "FIN", "我说完了"),
            ("fin", "←", "ACK", None),
            ("fin", "←", "FIN", "我也说完了"),
            ("fin", "→", "ACK", None)]
    step = 72
    y = top + 50
    ys = []
    for i, (ph, d, lab, note) in enumerate(msgs):
        if i in (3, 5):
            y += 26
        ys.append(y)
        x1, x2 = (CX, SX) if d == "→" else (SX, CX)
        arrow(s, [(x1 + (4 if d == "→" else -4), y), (x2 + (-6 if d == "→" else 6), y + 18)], INK, 1.6)
        s.text((CX + SX) / 2, y - 2, lab, 13.5, INK, 600, "middle", mono=True)
        if note:
            s.text((CX + SX) / 2, y + 34, note, 12, MUTED, 400, "middle")
        y += step
    bottom = y + 10
    s.line(CX, top, CX, bottom, "#AEB6BE", 1.4, dash="4 4")
    s.line(SX, top, SX, bottom, "#AEB6BE", 1.4, dash="4 4")

    def state(x, yy, t):
        s.pill(x, yy, t, GOOD if t == "ESTABLISHED" else KEY, 12, mono=True, h=24)
    # 状态在「发出」或「收到」那一刻变化：发出看箭头起点 ys[i]，收到看箭头终点 ys[i] + 18
    client = [(top + 22, "CLOSED"), (ys[0], "SYN_SENT"), (ys[1] + 18, "ESTABLISHED"), (ys[5], "FIN_WAIT_1"),
              (ys[6] + 18, "FIN_WAIT_2"), (ys[7] + 18, "TIME_WAIT")]
    server = [(top + 22, "LISTEN"), (ys[1], "SYN_RCVD"), (ys[2] + 18, "ESTABLISHED"), (ys[5] + 18, "CLOSE_WAIT"),
              (ys[7], "LAST_ACK"), (ys[8] + 18, "CLOSED")]
    for yy, t in client:
        w = len(t) * 12 * 0.61 + 22
        state(CX - 120, yy, t)
        s.line(CX - 120 + w / 2 + 4, yy, CX - 4, yy, "#C9D1D9", 1, dash="2 3")
    for yy, t in server:
        w = len(t) * 12 * 0.61 + 22
        state(SX + 120, yy, t)
        s.line(SX + 4, yy, SX + 120 - w / 2 - 4, yy, "#C9D1D9", 1, dash="2 3")
    # 左侧阶段括号
    for (a, b, t) in [(0, 2, "三次握手"), (3, 4, "传数据"), (5, 8, "四次挥手")]:
        ya, yb = ys[a] - 12, ys[b] + 32
        s.path(f"M{M + 150} {ya} h-10 V{yb} h10", MUTED, 1.2)
        s.text(M + 128, (ya + yb) / 2 + 5, t, 14.5, INK, 600, "end")
    # 右侧说明
    nx = SX + 230
    box(s, nx, top + 120, W - M - nx, 280, ("#FFFFFF", NAT[1], INK), None, None, style="outline")
    s.text(nx + 18, top + 150, "每一端记着的东西", 14.5, NAT[2], 600)
    bullets(s, nx + 18, top + 182, ["对方的 IP 和端口", "我发到哪个编号了", "对方确认到哪了", "连接处于哪个阶段"], 13.5, 28)
    for k, t in enumerate(wrap("两份记录对不上，比如一端被快照回滚到几秒前，包就会被当成无效包，连接卡死（第 20 篇）。",
                               W - M - nx - 36, 13)):
        s.text(nx + 18, top + 312 + 20 * k, t, 13, SUB)
    yy = s.footer(bottom + 30, "注：x、y 是两端各自随机选的起始序列号。TIME_WAIT 会再等一段时间才彻底关闭，防止迟到的包被误认成新连接的。")
    save(s, "04-1-TCP连接的一生.svg", yy + 20)


def fig_04_sni():
    s = Svg()
    y0 = s.header("不解密也能知道域名：HTTP 的 Host 头、TLS 的 SNI 都是明文",
                  "一个 IP 上常常托管着很多网站，只看目的地址 151.101.0.223:443 分不清要访问哪一个。"
                  "客户端会在连接一开始就把域名说出来；防火墙代理读的就是这一行（第 16 篇）。")
    y = y0 + 40
    # 上：一个 IP 多个网站
    s.pill(M + 150, y + 30, "151.101.0.223:443", WHITE, 15, mono=True, h=36)
    s.line(M + 260, y + 30, 1220, y + 30, HAIR, 1.2)
    s.text(M + 290, y + 20, "同一个 IP 上托管着", 12.5, MUTED)
    for k, t in enumerate(["pypi.org", "files.pythonhosted.org", "同一 IP 上的其他网站 …"]):
        cx = 560 + k * 330
        s.pill(cx, y + 30, t, KEY if k < 2 else ("#FFFFFF", HAIR, MUTED), 14, h=32)
    y += 90
    colw = (W - 2 * M - 40) / 2

    def panel(x, title, sub, lines):
        h = 296
        s.rect(x, y, colw, h, "#FCFBFA", HAIR, 1, rx=14)
        s.text(x + 22, y + 34, title, 17, INK, 600)
        s.text(x + 22, y + 58, sub, 13, SUB)
        yy = y + 90
        for t, kind in lines:
            if kind == "hit":
                s.rect(x + 18, yy - 20, colw - 36, 32, NAT[0], NAT[1], 1.2, rx=6)
                s.text(x + 30, yy + 1, t, 14.5, NAT[2], 700, mono=True)
            elif kind == "enc":
                s.rect(x + 18, yy - 20, colw - 36, 32, "#EEF0F2", "none", 0, rx=6)
                s.text(x + 30, yy + 1, t, 14, MUTED, 400, mono=True)
            else:
                s.text(x + 30, yy + 1, t, 14, INK, 400, mono=True)
            yy += 38
    panel(M, "HTTP（端口 80）", "整个请求都是明文，第一部分就有 Host 头",
          [("GET /simple/pandas/ HTTP/1.1", None), ("Host: pypi.org", "hit"), ("User-Agent: pip/24.0", None), ("…", None)])
    panel(M + colw + 40, "HTTPS（端口 443）", "加密之前先握手；第一条握手消息 ClientHello 是明文",
          [("ClientHello", None), ("  支持的加密算法: …", None), ("  SNI: pypi.org", "hit"), ("— 握手完成，之后全部加密 —", None),
           ("GET /simple/pandas/ …（看不到）", "enc")])
    yy = s.footer(y + 296 + 34, "注：SNI 必须是明文，因为服务器要先知道客户想访问哪个网站，才能拿出那个网站的证书完成握手。")
    save(s, "04-2-Host与SNI.svg", yy + 20)


if __name__ == "__main__":
    fig_01_map()
    fig_02_cidr()
    fig_02_nth()
    fig_03_frame()
    fig_03_lpm()
    fig_04_tcp()
    fig_04_sni()
