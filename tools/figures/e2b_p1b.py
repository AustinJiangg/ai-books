"""《E2B 沙箱网络从零讲透》第 5～8 篇的配图。用法: python3 tools/figures/e2b_p1b.py"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from figkit import *  # noqa: E402,F401,F403
from figkit import W, M  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "e2b-network", "img")


def save(s, name, h):
    s.save(os.path.join(OUT, name), h)


# ------------------------------------------------------------------ 第 5 篇
def fig_05_recursive():
    s = Svg()
    y0 = s.header("一次域名解析：递归解析器替你一层层问下去",
                  "电脑只问一个递归解析器（例如 8.8.8.8），由它依次去问根服务器、.org 服务器、pypi.org 的权威服务器，"
                  "拿到答案后回给电脑并缓存起来。查询走 UDP 53 端口。")
    T = y0 + 40
    CL, RV = (M, 290), (560, 860)            # 电脑列、解析器列的 x 范围
    SV = (1220, W - M)                       # 三台服务器
    rows = [T + 20, T + 170, T + 320]
    servers = [("根服务器", "知道每个顶级域归谁管"), (".org 服务器", "知道 pypi.org 归谁管"),
               ("pypi.org 的权威服务器", "真正知道 IP")]
    for (t, sub), ry in zip(servers, rows):
        box(s, SV[0], ry, SV[1] - SV[0], 92, WHITE, t, sub, 15.5, 13, style="outline")
    rv_top, rv_bot = rows[0], rows[2] + 92
    box(s, RV[0], rv_top, RV[1] - RV[0], rv_bot - rv_top, NS, None, None)
    s.text((RV[0] + RV[1]) / 2, rv_top + 40, "递归解析器", 17, NS[2], 600, "middle")
    s.text((RV[0] + RV[1]) / 2, rv_top + 64, "例如 8.8.8.8", 13.5, NS[2], 400, "middle", mono=True)
    s.rect(RV[0] + 30, rv_bot - 110, RV[1] - RV[0] - 60, 82, "#FFFFFF", NS[1], 1, rx=8, dash="4 3")
    s.text((RV[0] + RV[1]) / 2, rv_bot - 82, "缓存", 14, NS[2], 600, "middle")
    s.text((RV[0] + RV[1]) / 2, rv_bot - 60, "pypi.org → 151.101.0.223", 12.5, INK, 400, "middle", mono=True)
    s.text((RV[0] + RV[1]) / 2, rv_bot - 40, "TTL 到期前直接回答", 12.5, SUB, 400, "middle")
    cy = (rv_top + rv_bot) / 2
    box(s, CL[0], cy - 50, CL[1] - CL[0], 100, WHITE, "你的电脑", "读 /etc/resolv.conf\n知道该问 8.8.8.8", 15.5, 13,
        style="outline")
    # 1 与 8
    arrow(s, [(CL[1] + 4, cy - 18), (RV[0] - 6, cy - 18)], INK, 1.8)
    s.text((CL[1] + RV[0]) / 2, cy - 28, "pypi.org 的 IP？", 13.5, INK, 600, "middle")
    num(s, CL[1] + 26, cy - 46, 1)
    arrow(s, [(RV[0] - 4, cy + 22), (CL[1] + 6, cy + 22)], GOOD[1], 1.8)
    s.text((CL[1] + RV[0]) / 2, cy + 46, "151.101.0.223", 14, GOOD[2], 700, "middle", mono=True)
    num(s, CL[1] + 26, cy + 42, 8, GOOD[1])
    # 2-7
    qs = [("问：pypi.org？", "答：去问 .org 服务器"), ("问：pypi.org？", "答：去问 pypi.org 的权威服务器"),
          ("问：pypi.org？", "答：151.101.0.223")]
    for k, ((q, a), ry) in enumerate(zip(qs, rows)):
        y1, y2 = ry + 30, ry + 64
        arrow(s, [(RV[1] + 4, y1), (SV[0] - 6, y1)], INK, 1.6)
        s.text(RV[1] + 30, y1 - 9, q, 13, INK, 600)
        num(s, RV[1] + 18 - 4, y1 - 14, 2 + 2 * k, INK, 10, 11.5)
        arrow(s, [(SV[0] - 4, y2), (RV[1] + 6, y2)], SUB, 1.6)
        s.text(RV[1] + 30, y2 + 20, a, 13, SUB)
        num(s, RV[1] + 18 - 4, y2 + 15, 3 + 2 * k, SUB, 10, 11.5)
    yy = s.footer(rv_bot + 40, "注：电脑和解析器之间默认用 UDP 53，回答太长时改用 TCP 53。下次有人再问 pypi.org，"
                               "解析器在 TTL 到期前直接从缓存回答，不再跑第 2～7 步。")
    save(s, "05-1-递归解析.svg", yy + 20)


def fig_05_aaaa():
    s = Svg()
    y0 = s.header("同时查 A 和 AAAA：一个不回答，整个查询就白等十几秒",
                  "客户端不知道对方支持 IPv4 还是 IPv6，常常同时发出 A 和 AAAA 两个查询，两个都有结果才开始连接。"
                  "如果 DNS 服务器对 AAAA 一声不吭，客户端要等满超时、重试，按默认的 5 秒超时、共 3 次，就是 15 秒。")
    X0, X1 = 260, W - M - 20
    T = y0 + 50
    sec = (X1 - X0) / 16

    def xt(t):
        return X0 + t * sec
    # 时间轴
    ay = T + 250
    s.line(X0, ay, X1, ay, SUB, 1.4)
    for t in range(0, 17):
        s.line(xt(t), ay, xt(t), ay + (8 if t % 5 == 0 else 4), SUB, 1.2)
        if t % 5 == 0 or t == 16:
            s.text(xt(t), ay + 26, f"{t} 秒", 12.5, SUB, 400, "middle")
    lanes = [("A 查询", T + 30), ("AAAA 查询", T + 110), ("客户端", T + 200)]
    for name, ly in lanes:
        s.text(M, ly + 6, name, 15, INK, 600)
        s.line(X0, ly, X1, ly, "#EEF0F2", 10)
    # A：立刻回答
    ly = lanes[0][1]
    s.circle(xt(0), ly, 6, INK)
    s.circle(xt(0.15), ly, 7, GOOD[1])
    s.text(xt(0.15) + 16, ly + 5, "几毫秒后拿到答案：151.101.0.223", 13.5, GOOD[2], 600)
    # AAAA：三次尝试，每次 5 秒
    ly = lanes[1][1]
    for k in range(3):
        a, b = xt(5 * k), xt(5 * k + 5)
        s.circle(a, ly, 6, INK)
        s.rect(a + 6, ly - 9, b - a - 12, 18, BAD[0], BAD[1], 1, rx=9)
        s.text((a + b) / 2, ly + 5, "第 1 次" if k == 0 else f"重试第 {k} 次", 12.5, BAD[2], 600, "middle")
        s.text((a + b) / 2, ly + 30, "没有回答，等满 5 秒", 12, MUTED, 400, "middle")
    s.text(xt(15) + 12, ly + 5, "放弃", 13, BAD[2], 600)
    # 客户端
    ly = lanes[2][1]
    s.rect(xt(0), ly - 13, xt(15) - xt(0), 26, "#F1F2F4", "#C9D1D9", 1, rx=13)
    s.text((xt(0) + xt(15)) / 2, ly + 5, "手里已有 A 记录，但还在等 AAAA，不能开始连接", 13.5, SUB, 600, "middle")
    arrow(s, [(xt(15), ly), (xt(15.9), ly)], GOOD[1], 2)
    s.text(xt(15.9), ly - 16, "开始连接", 13, GOOD[2], 600, "end")
    # 括号
    s.path(f"M{xt(0)} {ay + 48} v8 H{xt(15)} v-8", BAD[1], 1.4)
    s.text((xt(0) + xt(15)) / 2, ay + 80, "白等约 15 秒", 16, BAD[2], 600, "middle")
    yy = s.footer(ay + 110, "注：这套环境里真实发生过：SDK 每次连沙箱都多等 15 秒。原因是 dnsmasq 把 AAAA 转给了不通的上游；"
                            "加一行 local=/e2b.app/，让 dnsmasq 对 AAAA 立刻回答“没有”，问题就消失了（第 17 篇）。")
    save(s, "05-2-AAAA白等.svg", yy + 20)


def fig_05_dnsmasq():
    s = Svg()
    y0 = s.header("dnsmasq：本机的 DNS 转发器，按域名决定谁来回答",
                  "程序只问 127.0.0.1:53。dnsmasq 按配置逐条看域名：有的自己直接回答，有的转给 Consul，其余转给普通的上游 DNS，"
                  "并把答案缓存起来。这补上了 resolv.conf 的两个短板：不能写端口、不能按域名分流。")
    T = y0 + 40
    PX = (M, 300)
    DX = (430, 990)
    TX = (1130, W - M)
    rows = [("address=/.e2b.app/127.0.0.1", "*.e2b.app", "自己回答 127.0.0.1", "不问任何人", NAT),
            ("server=/consul/127.0.0.1#8600", "*.consul", "Consul DNS", "127.0.0.1:8600，回答服务当前地址", NS),
            ("其他域名", "pypi.org 等", "上游 DNS", "例如 192.168.10.1", WHITE)]
    rh, rg = 96, 26
    top = T + 20
    s.rect(DX[0], T, DX[1] - DX[0], 3 * rh + 2 * rg + 40 + 100, "#FCFBFA", "#AEB6BE", 1.3, rx=14)
    s.text(DX[0] + 20, T + 30, "dnsmasq  127.0.0.1:53", 16, INK, 600)
    for k, (rule, dom, tgt, tsub, role) in enumerate(rows):
        ry = top + 30 + k * (rh + rg)
        box(s, DX[0] + 20, ry, DX[1] - DX[0] - 40, rh, ("#FFFFFF", role[1] if role is not WHITE else HAIR, INK), None, None)
        s.text(DX[0] + 40, ry + 36, dom, 15, INK, 600)
        s.text(DX[0] + 40, ry + 64, rule, 13, SUB, 400, mono=True)
        box(s, TX[0], ry, TX[1] - TX[0], rh, role, tgt, tsub, 15.5, 13,
            style="fill" if role is not WHITE else "outline")
        arrow(s, [(DX[1] - 20, ry + rh / 2), (TX[0] - 6, ry + rh / 2)], INK, 1.6)
    # local=
    ly = top + 30 + 3 * (rh + rg) - 6
    s.rect(DX[0] + 20, ly, DX[1] - DX[0] - 40, 56, NAT[0], NAT[1], 1, rx=8, dash="4 3")
    s.text(DX[0] + 40, ly + 24, "local=/e2b.app/", 13.5, NAT[2], 700, mono=True)
    s.text(DX[0] + 40, ly + 45, "e2b.app 只在本地找；本地没有的记录（如 AAAA）直接回答“没有”", 13, SUB)
    pc = top + 30 + (rh + rg) + rh / 2
    box(s, PX[0], pc - 70, PX[1] - PX[0], 140, WHITE, "本机程序", "SDK、orchestrator、api…\n/etc/resolv.conf：\nnameserver 127.0.0.1",
        15.5, 13, style="outline")
    arrow(s, [(PX[1] + 4, pc), (DX[0] - 6, pc)], INK, 1.8, label="查询", ldy=-10)
    yy = s.footer(T + 3 * rh + 2 * rg + 140 + 36, "注：这是宿主机上的 DNS。沙箱里的程序用的是另一套：resolv.conf 里写的是 8.8.8.8（第 14 篇）。"
                                                  "宿主机这套的完整配置见第 17 篇。")
    save(s, "05-3-dnsmasq分流.svg", yy + 20)


# ------------------------------------------------------------------ 第 6 篇
def fig_06_blocks():
    s = Svg()
    y0 = s.header("三块积木：网络命名空间、veth 对、tap 设备",
                  "E2B 每个沙箱的网络都由这三样搭成：命名空间隔出一整套独立的网络栈；veth 对把两个命名空间连起来；"
                  "tap 让 Firecracker 这个普通程序能收发以太网帧。")
    T = y0 + 40
    PW = (W - 2 * M - 2 * 28) / 3
    H = 470
    xs = [M + i * (PW + 28) for i in range(3)]
    titles = [("网络命名空间", "一整套独立的网络栈"), ("veth 对", "一根两头的虚拟网线"), ("tap 设备", "一头是网卡，一头是程序")]
    for x, (t, sub) in zip(xs, titles):
        s.rect(x, T, PW, H, "#FCFBFA", HAIR, 1, rx=16)
        s.text(x + 22, T + 36, t, 18, INK, 600)
        s.text(x + 22, T + 60, sub, 13.5, SUB)

    # 1 命名空间：两份完整的栈
    x = xs[0]
    items = ["网卡（至少一个 lo）", "路由表", "iptables / nftables 规则", "conntrack 表", "ip_forward 等参数", "端口"]
    cw = (PW - 22 * 2 - 16) / 2
    for k, (name, role) in enumerate([("宿主机（初始命名空间）", HOST), ("ns-5", NS)]):
        cx = x + 22 + k * (cw + 16)
        s.rect(cx, T + 84, cw, 300, role[0], role[1], 1.3, rx=12)
        s.text(cx + cw / 2, T + 110, name, 13.5, role[2], 600, "middle")
        for j, it in enumerate(items):
            s.rect(cx + 10, T + 126 + j * 41, cw - 20, 33, "#FFFFFF", role[1], 0.8, rx=6)
            s.text(cx + cw / 2, T + 148 + j * 41, it, 12, INK, 400, "middle")
    for k, t in enumerate(wrap("各有一份，互相看不见。一块网卡同一时间只属于一个命名空间。", PW - 44, 13.5)):
        s.text(x + 22, T + 414 + 22 * k, t, 13.5, SUB)

    # 2 veth
    x = xs[1]
    hw = PW - 44
    s.rect(x + 22, T + 90, hw, 110, HOST[0], HOST[1], 1.3, rx=12)
    s.text(x + 38, T + 114, "宿主机", 13.5, HOST[2], 600)
    chip(s, x + PW / 2, T + 160, 190, 50, HOST, "e2bv-5", "10.14.0.10/31", 14, 12.5)
    s.rect(x + 22, T + 280, hw, 110, NS[0], NS[1], 1.3, rx=12)
    s.text(x + 38, T + 304, "ns-5", 13.5, NS[2], 600)
    chip(s, x + PW / 2, T + 344, 190, 50, NS, "eth0（vpeer）", "10.14.0.11/31", 14, 12.5)
    s.line(x + PW / 2, T + 188, x + PW / 2, T + 316, INK, 3, start=True, end=True)
    s.text(x + PW / 2 + 14, T + 246, "一头进，", 13.5, INK, 600)
    s.text(x + PW / 2 + 14, T + 266, "另一头出", 13.5, INK, 600)
    for k, t in enumerate(wrap("两头可以放进不同的命名空间；两头地址在同一个 /31 里，是直连的邻居。", PW - 44, 13.5)):
        s.text(x + 22, T + 414 + 22 * k, t, 13.5, SUB)

    # 3 tap
    x = xs[2]
    s.rect(x + 22, T + 90, hw, 120, VM[0], VM[1], 1.3, rx=12)
    s.text(x + 38, T + 114, "用户态", 13.5, VM[2], 600)
    chip(s, x + PW / 2, T + 162, 220, 52, VM, "Firecracker 进程", "持有一个文件描述符", 14, 12)
    s.rect(x + 22, T + 270, hw, 120, NS[0], NS[1], 1.3, rx=12)
    s.text(x + 38, T + 294, "内核（ns-5）", 13.5, NS[2], 600)
    chip(s, x + PW / 2, T + 342, 220, 52, NS, "tap0（网卡）", "169.254.0.22/30", 14, 12)
    arrow(s, [(x + PW / 2 - 50, T + 190), (x + PW / 2 - 50, T + 312)], INK, 1.8)
    s.text(x + PW / 2 - 62, T + 248, "write(帧)", 12.5, INK, 600, "end", mono=True)
    s.text(x + PW / 2 - 62, T + 266, "= tap0 收到", 12, SUB, 400, "end")
    arrow(s, [(x + PW / 2 + 50, T + 314), (x + PW / 2 + 50, T + 192)], INK, 1.8)
    s.text(x + PW / 2 + 62, T + 248, "read(帧)", 12.5, INK, 600, mono=True)
    s.text(x + PW / 2 + 62, T + 266, "= tap0 发出", 12, SUB)
    for k, t in enumerate(wrap("程序只能按名字打开自己所在命名空间里的 tap，所以 Firecracker 要运行在 ns-5 里。", PW - 44, 13.5)):
        s.text(x + 22, T + 414 + 22 * k, t, 13.5, SUB)
    yy = s.footer(T + H + 34, "注：tun 与 tap 的区别只有一点：tun 收发 IP 包，tap 收发带 MAC 的以太网帧。虚拟机的网卡要做 ARP，所以用 tap。")
    save(s, "06-1-三块积木.svg", yy + 20)


def fig_06_bridge():
    s = Svg()
    y0 = s.header("把沙箱接出去的两种方式：网桥，或者路由 + NAT",
                  "网桥把所有沙箱放进同一个二层网络，像接在同一台交换机上；路由 + NAT 给每个沙箱一条自己的点对点链路，"
                  "宿主机按路由表转发。E2B 选后者，根本原因是它的沙箱无法拥有不同的 IP 和 MAC（第 10 篇）。")
    T = y0 + 40
    PW = (W - 2 * M - 40) / 2
    H = 470
    for i, (tg, title, role) in enumerate([("Docker 默认", "网桥（虚拟交换机）", WHITE), ("E2B 的选择", "路由 + NAT（点对点）", GOOD)]):
        x = M + i * (PW + 40)
        s.rect(x, T, PW, H, "#FCFBFA", HAIR, 1, rx=16)
        w = s.pill(x + 24 + (text_w(tg, 13) + 22) / 2, T + 32, tg, role, 13, solid=role is GOOD)
        s.text(x + 24 + w + 14, T + 38, title, 18, INK, 600)
    # 左：网桥
    x = M
    ys = [T + 90 + k * 82 for k in range(3)]
    for k, yy in enumerate(ys):
        chip(s, x + 110, yy + 28, 150, 52, VM, f"沙箱 {k + 1}", f"172.17.0.{k + 2}", 14, 12.5)
        s.line(x + 186, yy + 28, x + 300, ys[1] + 28, SUB, 1.4)
    s.rect(x + 300, ys[0] + 4, 30, ys[2] - ys[0] + 48, "#E9E8E3", HOST[1], 1, rx=8)
    s.text(x + 315, ys[0] - 8, "网桥", 13, SUB, 600, "middle")
    s.line(x + 330, ys[1] + 28, x + 400, ys[1] + 28, SUB, 1.4)
    box(s, x + 400, ys[1] + 2, 130, 52, NAT, "NAT", None, 14)
    s.line(x + 530, ys[1] + 28, x + 570, ys[1] + 28, SUB, 1.4)
    chip(s, x + 640, ys[1] + 28, 130, 52, HOST, "物理网卡", None, 14)
    yb = ys[2] + 90
    bullets(s, x + 24, yb, [[("同一个二层网络：", INK, 600), ("沙箱之间能互发 ARP、互相访问", SUB, 400)],
                            [("要隔离：", INK, 600), ("还得另加规则", SUB, 400)],
                            [("前提：", BAD[2], 600), ("每个沙箱的 IP、MAC 必须各不相同", SUB, 400)]], 14, 30, dot=MUTED)
    # 右：点对点
    x = M + PW + 40
    hx = x + 360
    for k, yy in enumerate(ys):
        chip(s, x + 110, yy + 28, 150, 52, VM, f"沙箱 {k + 1}", "169.254.0.21", 14, 12.5)
        s.line(x + 186, yy + 28, hx - 4, yy + 28, INK, 2.2, start=True, end=True)
        s.text(x + 270, yy + 20, f"veth：e2bv-{k + 2}", 12, SUB, 400, "middle", mono=True)
    s.rect(hx, ys[0], 170, ys[2] - ys[0] + 56, HOST[0], HOST[1], 1.3, rx=10)
    s.text(hx + 85, ys[0] + 26, "宿主机", 14, HOST[2], 600, "middle")
    s.text(hx + 85, ys[1] + 24, "路由表", 13.5, INK, 600, "middle")
    s.text(hx + 85, ys[1] + 44, "按 Host IP 转发", 12, SUB, 400, "middle")
    s.text(hx + 85, ys[2] + 28, "+ NAT", 13.5, INK, 600, "middle")
    s.line(hx + 170, ys[1] + 28, hx + 210, ys[1] + 28, SUB, 1.4)
    chip(s, hx + 270, ys[1] + 28, 110, 52, HOST, "物理网卡", None, 14)
    bullets(s, x + 24, yb, [[("每条链路独立：", INK, 600), ("沙箱之间没有二层通路，看不见对方的 ARP", SUB, 400)],
                            [("沙箱互访：", INK, 600), ("包只能先到宿主机，由宿主机决定转不转", SUB, 400)],
                            [("不要求：", GOOD[2], 600), ("沙箱的 IP、MAC 各不相同", SUB, 400)]], 14, 30, dot=GOOD[1])
    yy = s.footer(T + H + 34, "注：右边每个沙箱的地址都是 169.254.0.21，靠的是各自的命名空间和出口的 NAT（第 10、11 篇）。")
    save(s, "06-2-网桥与点对点.svg", yy + 20)


# ------------------------------------------------------------------ 第 7 篇
def fig_07_hooks():
    s = Svg()
    y0 = s.header("五个钩子，三条路：先看包是哪一种",
                  "包在内核里经过五个固定位置，每个位置都能挂规则。走哪几个钩子取决于包的种类：给本机的、本机发出的、路过的。"
                  "分析 E2B 的每条规则，都先问这个包走的是哪条路。")
    T = y0 + 40
    RY = T + 70                       # 主干一行
    nodes = {"in": (M + 60, "网卡（进）"), "pre": (330, "PREROUTING"), "rt": (560, "路由判断"), "fwd": (800, "FORWARD"),
             "post": (1050, "POSTROUTING"), "out": (1300, "网卡（出）")}
    IY, PY = RY + 150, RY + 290        # INPUT/OUTPUT 一行、本机程序一行
    FWD, IN, OUT = (NS[1], NS[2]), ("#1F9E77", "#0E6B4F"), (VM[1], VM[2])
    # 路径（先画，在节点下面）
    off = 7
    s.path(f"M{M + 120} {RY - off} H{1240}", FWD[0], 3, end=True)                              # 转发
    s.path(f"M{M + 120} {RY + off} H{560 + off} V{PY - 30}", IN[0], 3, end=True)                # 给本机
    s.path(f"M{860} {PY - 30} V{IY} H{1050 + off} V{RY + off} H{1240}", OUT[0], 3, end=True)   # 本机发出
    for key, (cx, t) in nodes.items():
        if key in ("in", "out"):
            chip(s, cx if key == "in" else cx, RY, 120, 46, WHITE, t, None, 13.5)
        elif key == "rt":
            d = 46
            s.o.append(f'<path d="M{cx} {RY - d} L{cx + d * 1.6} {RY} L{cx} {RY + d} L{cx - d * 1.6} {RY} Z" '
                       f'fill="#FFFFFF" stroke="{SUB}" stroke-width="1.4"/>')
            s.text(cx, RY + 5, t, 14, INK, 600, "middle")
        else:
            box(s, cx - 90, RY - 26, 180, 52, KEY, t, None, 14.5)
    box(s, 470, IY - 26, 180, 52, KEY, "INPUT", None, 14.5)
    box(s, 770, IY - 26, 180, 52, KEY, "OUTPUT", None, 14.5)
    box(s, 470, PY - 30, 480, 60, WHITE, "本机程序", None, 15, style="outline")
    # 图例与例子
    LX = 1390
    items = [(FWD, "路过（转发）", "PREROUTING → FORWARD → POSTROUTING", "沙箱的 UDP 包经过宿主机"),
             (IN, "给本机", "PREROUTING → INPUT", "被 REDIRECT 给防火墙代理的 TCP"),
             (OUT, "本机发出", "OUTPUT → POSTROUTING", "orchestrator 连沙箱里的 envd")]
    ly = PY + 80
    for (c, tc), t, path_, ex in items:
        s.line(M, ly, M + 40, ly, c, 3)
        s.text(M + 52, ly + 5, t, 14.5, tc, 600)
        s.text(M + 190, ly + 5, path_, 13.5, INK, 400, mono=True)
        s.text(M + 560, ly + 5, "例：" + ex, 13.5, SUB)
        ly += 32
    # 关键细节
    by = ly + 10
    box(s, M, by, W - 2 * M, 78, ("#FFFFFF", NAT[1], INK), None, None, style="outline")
    s.text(M + 22, by + 32, "PREROUTING 在路由判断之前", 15.5, NAT[2], 600)
    s.text(M + 22, by + 58, "在这里改了目的地址（DNAT、REDIRECT），路由判断就按新地址走。"
                            "REDIRECT 把一个本来要转发的包变成给本机的包，靠的就是这一点。", 13.5, SUB)
    yy = s.footer(by + 78 + 34, "注：iptables、nftables 都只是给这五个钩子写规则的前端，真正干活的是内核里的 Netfilter。")
    save(s, "07-1-五个钩子.svg", yy + 20)


def fig_07_nat():
    s = Svg()
    y0 = s.header("四种地址转换：改源还是改目的，换成写死的地址还是自动选",
                  "按两件事把 NAT 分成四格：改的是源地址还是目的地址（决定挂在哪个钩子上），新地址是写死的还是自动选的。"
                  "每格都是 E2B 里真实用到的一条规则。")
    T = y0 + 40
    LW = 150
    CW_ = (W - 2 * M - LW - 24) / 2
    cx = [M + LW, M + LW + CW_ + 24]
    heads = [("改源地址", "在 POSTROUTING 做：要先知道从哪块网卡出去"),
             ("改目的地址", "在 PREROUTING 做：要赶在路由判断之前")]
    for x, (t, sub) in zip(cx, heads):
        s.text(x + CW_ / 2, T + 20, t, 18, INK, 600, "middle")
        s.text(x + CW_ / 2, T + 44, sub, 13, SUB, 400, "middle")
    rows = [("写死新地址", T + 70), ("自动选地址", T + 330)]
    cells = [[("SNAT", "ns-5 出口", "-o eth0 -s 169.254.0.21 -j SNAT --to 10.13.0.5",
               ("源", "169.254.0.21", "10.13.0.5"), "沙箱的地址换成它的 Host IP"),
              ("DNAT", "ns-5 入口", "-i eth0 -d 10.13.0.5 -j DNAT --to 169.254.0.21",
               ("目的", "10.13.0.5", "169.254.0.21"), "发给 Host IP 的包换回客户机地址")],
             [("MASQUERADE", "宿主机出口", "-s 10.13.0.5/32 -o enp125s0f0 -j MASQUERADE",
               ("源", "10.13.0.5", "192.168.10.23"), "自动用出口网卡当前的地址"),
              ("REDIRECT", "宿主机，从 e2bv-5 进来的 TCP", "-i e2bv-5 -p tcp --dport 443 -j REDIRECT --to-port 5017",
               ("目的", "151.101.0.223:443", "10.14.0.10:5017"), "改成本机（进来那块网卡的地址），交给本机程序")]]
    for r, (rname, ry) in enumerate(rows):
        s.text(M, ry + 120, rname, 16, INK, 600)
        for c in range(2):
            name, where, rule, (fld, a, b), note = cells[r][c]
            x = cx[c]
            s.rect(x, ry, CW_, 236, "#FFFFFF", "#AEB6BE", 1.2, rx=14)
            s.text(x + 22, ry + 36, name, 20, INK, 700)
            s.text(x + 22 + text_w(name, 20) * 1.04 + 14, ry + 36, where, 13.5, SUB)
            # 改写前后
            yy = ry + 74
            s.text(x + 22, yy + 24, fld, 13.5, MUTED)
            s.rect(x + 66, yy, 220, 38, "#F4F5F7", "none", 0, rx=8)
            s.text(x + 176, yy + 25, a, 14.5, INK, 400, "middle", mono=True)
            arrow(s, [(x + 296, yy + 19), (x + 346, yy + 19)], NAT[1], 2)
            s.rect(x + 356, yy, 220, 38, NAT[0], NAT[1], 1.2, rx=8)
            s.text(x + 466, yy + 25, b, 14.5, NAT[2], 700, "middle", mono=True)
            s.text(x + 22, yy + 72, note, 13.5, INK)
            s.rect(x + 16, yy + 92, CW_ - 32, 46, "#F7F8FA", "none", 0, rx=8)
            for k, ln in enumerate(wrap(rule, CW_ - 60, 12)):
                s.text(x + 28, yy + 112 + 18 * k, ln, 12, SUB, 400, mono=True)
    yy = s.footer(T + 330 + 236 + 34, "注：这些规则只描述新连接的第一个包怎么改；同一条连接的后续包和回包，由 conntrack 按记录处理（见下一节）。"
                                     "被 REDIRECT 的程序用 SO_ORIGINAL_DST 向内核要回原始目的地址。")
    save(s, "07-2-四种NAT.svg", yy + 20)


def fig_07_conntrack():
    s = Svg()
    y0 = s.header("conntrack：只有第一个包查 NAT 规则，之后全按记录改",
                  "以宿主机上的 MASQUERADE 为例：沙箱经 Host IP 10.13.0.5 向 8.8.8.8 发 DNS 查询。"
                  "第一个包查 nat 表、改地址，内核把结果记成一条连接；后续的包和回包都直接按这条记录改，不再查规则。")
    T = y0 + 40
    rows = [("第一个包（NEW）", "10.13.0.5:41234 → 8.8.8.8:53", "查 nat 表，命中 MASQUERADE", "源改成 192.168.10.23，并写下记录"),
            ("同一连接的后续包", "10.13.0.5:41234 → 8.8.8.8:53", "不查 nat 表", "按记录把源改成 192.168.10.23"),
            ("回包", "8.8.8.8:53 → 192.168.10.23:41234", "不查 nat 表；规则里也没写回包", "按记录把目的改回 10.13.0.5")]
    LX, MX, RX = M, 520, 1090
    rh = 92
    tb_top = T + 20
    ys = [tb_top + k * (rh + 22) for k in range(3)]
    for k, (t, pkt, how, res) in enumerate(rows):
        y = ys[k]
        box(s, LX, y, 400, rh, WHITE if k else NS, t, pkt, 15, 13, mono_sub=True, style="outline" if k else "fill")
        res_role = NAT
        box(s, RX, y, W - M - RX, rh, res_role, res, how, 14.5, 12.5)
    # 中间：conntrack 表
    ch = 3 * rh + 44
    s.rect(MX, tb_top, 480, ch, "#FCFBFA", "#AEB6BE", 1.3, rx=14)
    s.text(MX + 20, tb_top + 30, "宿主机的 conntrack 表（一条记录）", 14.5, INK, 600)
    s.rect(MX + 18, tb_top + 50, 444, 74, "#FFFFFF", NS[1], 1.1, rx=8)
    s.text(MX + 32, tb_top + 72, "原始方向", 12.5, NS[2], 600)
    s.text(MX + 32, tb_top + 96, "src=10.13.0.5 dst=8.8.8.8", 13, INK, 400, mono=True)
    s.text(MX + 32, tb_top + 114, "sport=41234 dport=53", 13, INK, 400, mono=True)
    s.rect(MX + 18, tb_top + 140, 444, 74, "#FFFFFF", NAT[1], 1.1, rx=8)
    s.text(MX + 32, tb_top + 162, "回复方向（预期的回包）", 12.5, NAT[2], 600)
    s.text(MX + 32, tb_top + 186, "src=8.8.8.8 dst=192.168.10.23", 13, INK, 400, mono=True)
    s.text(MX + 32, tb_top + 204, "sport=53 dport=41234", 13, INK, 400, mono=True)
    s.text(MX + 20, tb_top + 250, "状态：NEW → ESTABLISHED", 13.5, SUB)
    s.text(MX + 20, tb_top + 274, "每个命名空间各有一张这样的表", 13.5, SUB)
    for k, y in enumerate(ys):
        arrow(s, [(LX + 404, y + rh / 2), (MX - 6, y + rh / 2)], INK if k == 0 else SUB, 1.6,
              label="写入" if k == 0 else "查记录", ldy=-8)
        arrow(s, [(MX + 484, y + rh / 2), (RX - 6, y + rh / 2)], NAT[1], 1.6)
    by = ys[2] + rh + 36
    box(s, M, by, W - 2 * M, 82, ("#FFFFFF", HAIR, INK), None, None, style="outline")
    s.text(M + 22, by + 32, "沙箱访问外网一次，两张表各留一条记录", 15, INK, 600)
    s.text(M + 22, by + 58, "ns-5 的表：169.254.0.21 ⇄ 10.13.0.5（SNAT）。宿主机的表：10.13.0.5 ⇄ 192.168.10.23（MASQUERADE）。"
                            "快照回滚时两张表里的旧记录都要清掉（第 20 篇）。", 13.5, SUB)
    yy = s.footer(by + 82 + 34, "注：conntrack 给每个包标一个状态：NEW、ESTABLISHED、RELATED、INVALID。防火墙常用的第一条规则就是放行 ESTABLISHED 和 RELATED。")
    save(s, "07-3-conntrack.svg", yy + 20)


# ------------------------------------------------------------------ 第 8 篇
def fig_08_priority():
    s = Svg()
    y0 = s.header("同一个钩子上谁先谁后：E2B 的防火墙排在 NAT 前面",
                  "同一个钩子上可以挂好几条链，按优先级数字从小到大执行。沙箱发出的包进入 ns-5 后，先过 -150 的 nftables 防火墙，"
                  "再过 -100 的 iptables nat，最后在 POSTROUTING 做 SNAT。所以防火墙判断的永远是沙箱原本想访问的地址。")
    T = y0 + 40
    # 上：PREROUTING 上的优先级刻度
    X0, X1 = 260, W - M - 160

    def px(p):
        return X0 + (p + 330) / 350 * (X1 - X0)
    ay = T + 170
    s.text(M, ay + 5, "PREROUTING 上的链", 15, INK, 600)
    s.line(X0, ay, X1, ay, SUB, 1.6)
    s.text(X1 + 8, ay + 5, "数字小的先执行 →", 12.5, MUTED)
    marks = [(-300, "raw", "最早", KEY, False), (-150, "E2B：slot-firewall", "nftables，放行或丢弃", GOOD, True),
             (-100, "nat PREROUTING", "iptables：DNAT、REDIRECT", NAT, False), (0, "filter", "", KEY, False)]
    for p, t, sub, role, hit in marks:
        x = px(p)
        lift = 64 if p == -100 else 0
        s.circle(x, ay, 7 if hit else 5, role[1])
        s.text(x, ay + 30, str(p), 13, INK, 600, "middle", mono=True)
        w = max(text_w(t, 14), text_w(sub, 12)) + 30
        s.rect(x - w / 2, ay - 82 - lift, w, sub and 58 or 40, role[0], role[1], 1.4 if hit else 1, rx=9)
        s.text(x, ay - 58 - lift, t, 14, role[2], 600, "middle")
        if sub:
            s.text(x, ay - 38 - lift, sub, 12, SUB, 400, "middle")
        s.line(x, (ay - 24 if sub else ay - 42) - lift, x, ay - 8, role[1], 1.2)
    # 下：一个包在 ns-5 里的顺序
    y = ay + 90
    s.text(M, y, "沙箱发出的一个包，在 ns-5 里依次经过", 17, INK, 600)
    y += 30
    steps = [("从 tap0 进入", "目的 151.101.0.223", WHITE),
             ("nftables 防火墙", "优先级 -150：看的是原始目的地址", GOOD),
             ("iptables nat PREROUTING", "-100：这个方向没有匹配的规则", KEY),
             ("路由 → FORWARD", "转发给 eth0（vpeer）", KEY),
             ("nat POSTROUTING：SNAT", "源 169.254.0.21 → 10.13.0.5", NAT),
             ("从 eth0 离开", "进入宿主机", WHITE)]
    n = len(steps)
    gap = 26
    bw = (W - 2 * M - (n - 1) * gap) / n
    for k, (t, sub, role) in enumerate(steps):
        x = M + k * (bw + gap)
        box(s, x, y, bw, 96, role, t, sub, 14, 12.5, style="outline" if role is WHITE else "fill")
        if k < n - 1:
            arrow(s, [(x + bw + 3, y + 48), (x + bw + gap - 4, y + 48)], INK, 1.6)
    yy = s.footer(y + 96 + 40, "注：iptables 和 nftables 挂在同一个 Netfilter 上，可以同时使用。E2B 的分工：出站过滤用 nftables，地址转换和各种改道用 iptables。")
    save(s, "08-1-优先级.svg", yy + 20)


def fig_08_sets():
    s = Svg()
    y0 = s.header("集合：一条规则判断“在不在集合里”，元素可以单独增删",
                  "要拦五个网段，iptables 得写五条规则，包要逐条比较；nftables 把网段放进一个集合，一条规则查一次。"
                  "集合内容可以单独修改，规则不动；一批修改还能一次原子提交。")
    T = y0 + 40
    PW = (W - 2 * M - 40) / 2
    H = 446
    nets = ["10.0.0.0/8", "127.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12", "192.168.0.0/16"]
    for i, (t, sub) in enumerate([("iptables：五条规则", "一条规则只能匹配一个地址段"),
                                  ("nftables：一条规则 + 一个集合", "集合用区间存储，元素再多查一次也很快")]):
        x = M + i * (PW + 40)
        s.rect(x, T, PW, H, "#FCFBFA", HAIR, 1, rx=16)
        s.text(x + 24, T + 36, t, 18, INK, 600)
        s.text(x + 24, T + 60, sub, 13.5, SUB)
    # 左
    x = M
    s.pill(x + 120, T + 104, "目的 192.168.1.9", NAT, 13.5, mono=True, h=30)
    for k, n_ in enumerate(nets):
        ry = T + 132 + k * 50
        hit = k == 4
        s.rect(x + 60, ry, PW - 120, 40, NAT[0] if hit else "#FFFFFF", NAT[1] if hit else HAIR, 1.2, rx=8)
        s.text(x + 80, ry + 26, f"iptables … -d {n_} -j DROP", 13, NAT[2] if hit else INK, 600 if hit else 400, mono=True)
        s.text(x + PW - 76, ry + 26, "命中，丢弃" if hit else "不匹配，下一条", 12.5, NAT[2] if hit else MUTED, 600 if hit else 400,
               "end")
    s.line(x + 40, T + 120, x + 40, T + 132 + 4 * 50 + 20, MUTED, 1.4, end=True)
    s.text(x + 24, T + H - 30, "比较了 5 次。规则越多，比得越多；改一条规则还要整表重写。", 13.5, SUB)
    # 右
    x = M + PW + 40
    s.pill(x + 120, T + 104, "目的 192.168.1.9", NAT, 13.5, mono=True, h=30)
    s.rect(x + 40, T + 132, PW - 80, 46, NAT[0], NAT[1], 1.2, rx=8)
    s.text(x + 58, T + 161, 'iifname "tap0" ip daddr @filtered_always_denylist drop', 12.5, NAT[2], 600, mono=True)
    s.rect(x + 40, T + 200, PW - 80, 150, "#FFFFFF", NS[1], 1.3, rx=10)
    s.text(x + 58, T + 226, "集合 filtered_always_denylist（type ipv4_addr; flags interval）", 12.5, NS[2], 600, mono=True)
    for k, n_ in enumerate(nets):
        cx = x + 58 + (k % 3) * 210
        cy = T + 248 + (k // 3) * 46
        hit = k == 4
        s.rect(cx, cy, 190, 34, NAT[0] if hit else NS[0], NAT[1] if hit else NS[1], 1, rx=17)
        s.text(cx + 95, cy + 22, n_, 13, NAT[2] if hit else NS[2], 600 if hit else 400, "middle", mono=True)
    s.line(x + PW / 2, T + 178, x + PW / 2, T + 198, NAT[1], 1.4, end=True)
    s.text(x + 24, T + H - 30, "查一次集合就知道。用户的 allowOut/denyOut 只往用户集合里填元素。", 13.5, SUB)
    # 原子提交
    by = T + H + 30
    box(s, M, by, W - 2 * M, 82, ("#FFFFFF", GOOD[1], INK), None, None, style="outline")
    s.text(M + 22, by + 32, "原子提交：没有“改了一半”的窗口", 15, GOOD[2], 600)
    s.text(M + 22, by + 58, "E2B 先在内存里攒好建表、建链、建集合、加规则、填元素这一批操作，最后调用一次 Flush 提交；"
                            "内核要么全部生效，要么全部不生效。", 13.5, SUB)
    yy = s.footer(by + 82 + 34, "注：图中的集合是“预置拦截”集合，内容固定；另有预置放行和两个用户集合，第 15 篇逐条讲。")
    save(s, "08-2-集合.svg", yy + 20)


if __name__ == "__main__":
    fig_05_recursive()
    fig_05_aaaa()
    fig_05_dnsmasq()
    fig_06_blocks()
    fig_06_bridge()
    fig_07_hooks()
    fig_07_nat()
    fig_07_conntrack()
    fig_08_priority()
    fig_08_sets()
