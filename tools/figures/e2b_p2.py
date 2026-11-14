"""《E2B 沙箱网络从零讲透》第 9、10、12、14 篇的配图（第 10-1、11-1、13-1 见 e2b_core.py）。

用法: python3 tools/figures/e2b_p2.py
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


def band(s, y, h, role, title, sub=None):
    s.rect(M, y, W - 2 * M, h, role[0], role[1], 1.3, rx=14)
    s.text(M + 20, y + 30, title, 15, role[2], 600)
    if sub:
        s.text(M + 20, y + 52, sub, 12.5, SUB)


# ------------------------------------------------------------------ 第 9 篇
def fig_09_frame():
    s = Svg()
    y0 = s.header("一个帧从客户机走到 tap0：中间隔着一个普通程序 Firecracker",
                  "客户机的 virtio-net 驱动把帧放进和 Firecracker 共享的内存队列；Firecracker 取出来，写进 tap0 的文件描述符，"
                  "帧就进了 ns-5 的网络栈。发往 169.254.169.254 的 MMDS 请求在 Firecracker 这里就被截下回答，不会出现在 tap0 上。")
    T = y0 + 34
    BH = 136
    B1, B2, B3 = T, T + BH + 30, T + 2 * (BH + 30)
    band(s, B1, BH, VM, "客户机", "虚拟机内部")
    band(s, B2, BH, KEY, "Firecracker 进程", "用户态，运行在 ns-5 里")
    band(s, B3, BH, NS, "宿主机内核", "ns-5 的网络栈")
    by = B1 + 40
    xs = [(300, "程序", "例如 pip"), (530, "客户机内核", "查路由，交给网关"), (760, "virtio-net 驱动", "知道自己在虚拟机里")]
    for cx, t, sub in xs:
        box(s, cx - 90, by, 180, 64, ("#FFFFFF", VM[1], VM[2]), t, sub, 14, 12)
    arrow(s, [(390, by + 32), (436, by + 32)], INK, 1.6)
    arrow(s, [(620, by + 32), (666, by + 32)], INK, 1.6)
    # 共享内存队列：跨在客户机和 Firecracker 之间
    QX0, QX1 = 1000, 1180
    qy0, qy1 = B1 + 70, B2 + 66
    s.rect(QX0, qy0, QX1 - QX0, qy1 - qy0, "#FFFFFF", NAT[1], 1.5, rx=10, dash="5 4")
    s.text((QX0 + QX1) / 2, qy0 + 26, "共享内存", 14, NAT[2], 600, "middle")
    for k, t in enumerate(["发送队列", "接收队列"]):
        s.rect(QX0 + 20, qy0 + 40 + k * 46, QX1 - QX0 - 40, 34, NAT[0], NAT[1], 1, rx=6)
        s.text((QX0 + QX1) / 2, qy0 + 62 + k * 46, t, 13, NAT[2], 600, "middle")
    arrow(s, [(850, by + 32), (QX0 - 6, by + 32), ], INK, 1.6)
    s.text(925, by + 22, "放进发送队列", 12.5, INK, 600, "middle")
    s.text(925, by + 54, "敲门铃通知", 12, SUB, 400, "middle")
    # Firecracker：取帧 → 判断（这一行从右往左走）
    fy = B2 + 70
    DX = 780
    d = 34
    arrow(s, [(QX0 - 4, fy + 4), (DX + d * 2.6 + 6, fy + 4)], INK, 1.6, label="取出帧", ldy=-10)
    s.o.append(f'<path d="M{DX} {fy + 4 - d} L{DX + d * 2.6} {fy + 4} L{DX} {fy + 4 + d} L{DX - d * 2.6} {fy + 4} Z" '
               f'fill="#FFFFFF" stroke="{SUB}" stroke-width="1.4"/>')
    s.text(DX, fy, "目的是", 12.5, INK, 600, "middle")
    s.text(DX, fy + 18, "169.254.169.254？", 12.5, INK, 600, "middle", mono=True)
    # 是：MMDS
    mx1 = 560
    arrow(s, [(DX - d * 2.6, fy + 4), (mx1 + 4, fy + 4)], GOOD[1], 1.6, label="是", ldy=-8)
    box(s, 300, fy - 32, mx1 - 300, 72, GOOD, "MMDS", "Firecracker 自己回答，放进接收队列", 14, 12)
    # 否：写进 tap0
    ty = B3 + 46
    arrow(s, [(DX, fy + 4 + d), (DX, ty - 4)], INK, 1.6, label="否：write(tap fd, 帧)", lpos=0.45, ldx=12, ldy=4,
          lanchor="start")
    box(s, DX - 100, ty, 200, 64, ("#FFFFFF", NS[1], NS[2]), "tap0", "“收到”一个以太网帧", 14, 12)
    box(s, 300, ty, 260, 64, ("#FFFFFF", NS[1], NS[2]), "ns-5 的网络栈", "PREROUTING …（第 13 篇接着讲）", 14, 12)
    arrow(s, [(DX - 104, ty + 32), (564, ty + 32)], INK, 1.6)
    yy = s.footer(B3 + BH + 34, "注：反方向一样：ns-5 把发给客户机的帧从 tap0 发出，Firecracker read 到它，放进接收队列，再用中断通知客户机。"
                                "对宿主机内核来说，tap0 就像一根网线，另一头接着一台 169.254.0.21。")
    save(s, "09-1-帧到tap0.svg", yy + 20)


def fig_09_netns_exec():
    s = Svg()
    y0 = s.header("让 Firecracker 进入 ns-5：ip netns exec 做了太多事，fc-netns-exec 只做两件",
                  "Firecracker 只需要身在 ns-5，才能按名字打开 ns-5 的 tap0。ip netns exec 还要处理挂载、/sys、/etc，"
                  "其中几步要拿内核里的一把全局锁，高并发创建沙箱时排队；补丁里的 fc-netns-exec 只做 setns 和 exec。")
    T = y0 + 40
    PW = (W - 2 * M - 40) / 2
    H = 470
    heads = [("上游：ip netns exec", "ip netns exec ns-5 firecracker …", WHITE),
             ("这套环境：fc-netns-exec", "fc-netns-exec ns-5 firecracker …", GOOD)]
    for i, (t, cmd, role) in enumerate(heads):
        x = M + i * (PW + 40)
        s.rect(x, T, PW, H, "#FCFBFA", HAIR, 1, rx=16)
        s.text(x + 24, T + 36, t, 18, role[2] if role is GOOD else INK, 600)
        s.text(x + 24, T + 62, cmd, 13, SUB, 400, mono=True)
    left = [("新开一个挂载命名空间", True), ("遍历整棵挂载树，改传播属性", True), ("卸载并重新挂载 /sys", True),
            ("把 /etc/netns/ns-5/ 下的文件覆盖到 /etc", True), ("setns：进入网络命名空间 ns-5", False), ("exec：变成 Firecracker", False)]
    right = [("打开 /run/netns/ns-5，setns 进入", False), ("exec：变成 Firecracker", False)]
    sh, sg = 44, 12
    for i, steps in enumerate([left, right]):
        x = M + i * (PW + 40)
        for k, (t, mount) in enumerate(steps):
            ry = T + 90 + k * (sh + sg)
            role = BAD if mount else ("#FFFFFF", "#AEB6BE", INK)
            s.rect(x + 60, ry, PW - 100, sh, role[0], role[1], 1.2, rx=8)
            num(s, x + 38, ry + sh / 2, k + 1, BAD[1] if mount else INK, 12, 12.5)
            s.text(x + 80, ry + 28, t, 14, role[2], 600 if not mount else 400)
        if i == 0:
            ya, yb = T + 90, T + 90 + 4 * (sh + sg) - sg
            s.path(f"M{x + PW - 30} {ya} h10 V{yb} h-10", BAD[1], 1.3)
            ly = T + 90 + 6 * (sh + sg) + 14
            s.rich(x + 30, ly, [("1～4 是挂载相关的操作：", BAD[2], 700), ("Firecracker 用不上，其中几步要拿全局锁，并发时排队", SUB, 400)], 13.5)
    # 右侧补充
    x = M + PW + 40
    bullets(s, x + 30, T + 230, [[("开关：", INK, 600), ("orchestrator 的环境变量 E2B_FC_NETNS_EXEC_HELPER", SUB, 400)],
                                 [("设成空、disabled、ip-netns-exec：", INK, 600), ("退回上游做法", SUB, 400)],
                                 [("构建模板时：", INK, 600), ("仍用 ip netns exec；只有恢复沙箱时用新工具", SUB, 400)]],
            13.5, 30, dot=GOOD[1])
    by = T + H + 30
    box(s, M, by, W - 2 * M, 70, ("#FFFFFF", NS[1], INK), None, None, style="outline")
    s.rich(M + 22, by + 42, [("网络上的结果完全一样：", NS[2], 700), ("Firecracker 进程运行在 ns-5 里，打开的是 ns-5 的 tap0。"
                              "压测记录里，“拉起 Firecracker 并等它就绪”占沙箱启动总耗时的八成以上。", SUB, 400)], 14)
    yy = s.footer(by + 70 + 34, "注：fc-netns-exec 是 openEuler 社区的优化，只有几十行 Go：open + setns(CLONE_NEWNET) + exec。")
    save(s, "09-2-进入命名空间.svg", yy + 20)


# ------------------------------------------------------------------ 第 10 篇
def fig_10_snapshot():
    s = Svg()
    y0 = s.header("模板只开机一次，沙箱都从同一张快照恢复：网卡配置原样醒来",
                  "构建模板时，虚拟机真正启动一次，内核按 ip= 参数配好网卡，然后连同内存和设备状态拍成快照。"
                  "之后每个沙箱都加载这张快照，从拍照那一刻接着运行，所以 IP、MAC、网关全都一样。")
    T = y0 + 40
    # 左：构建模板
    LX0, LX1 = M, 560
    s.rect(LX0, T, LX1 - LX0, 470, "#FCFBFA", HAIR, 1, rx=16)
    s.text(LX0 + 22, T + 36, "构建模板：只做一次", 18, INK, 600)
    steps = [("准备根文件系统", "装好系统、软件、envd"), ("真正启动一次虚拟机", "内核按 ip= 配好 eth0：169.254.0.21/30"),
             ("envd 启动", "监听 49983；用户的启动命令也跑起来"), ("拍快照", "内存和设备状态原样存成文件")]
    for k, (t, sub) in enumerate(steps):
        ry = T + 64 + k * 98
        box(s, LX0 + 60, ry, LX1 - LX0 - 90, 74, NAT if k == 3 else WHITE, t, sub, 15, 12.5,
            style="fill" if k == 3 else "outline")
        num(s, LX0 + 34, ry + 37, k + 1, NAT[1] if k == 3 else INK)
        if k < 3:
            arrow(s, [(LX0 + 60 + (LX1 - LX0 - 90) / 2, ry + 76), (LX0 + 60 + (LX1 - LX0 - 90) / 2, ry + 96)], INK, 1.5)
    # 中：快照文件
    cx = 690
    cy = T + 235
    box(s, cx - 90, cy - 60, 180, 120, NAT, "快照", "一张，供所有沙箱加载", 17, 12.5)
    arrow(s, [(LX1 + 4, T + 64 + 3 * 98 + 37), (cx - 90 - 30, T + 64 + 3 * 98 + 37), (cx - 90 - 30, cy), (cx - 94, cy)],
          NAT[1], 1.6)
    # 右：恢复出的沙箱
    RX0 = 860
    rows = [T + 10 + k * 158 for k in range(3)]
    ident = [("IP", "169.254.0.21/30"), ("网关", "169.254.0.22"), ("MAC", "02:FC:00:00:00:05"), ("tap", "tap0")]
    for k, ry in enumerate(rows):
        s.rect(RX0, ry, W - M - RX0, 140, VM[0], VM[1], 1.3, rx=12)
        s.text(RX0 + 20, ry + 30, f"沙箱 {'ABC'[k]}", 15, VM[2], 600)
        s.text(RX0 + 20, ry + 52, "加载快照，接着运行", 12.5, SUB)
        for j, (a, b) in enumerate(ident):
            gx = RX0 + 200 + (j % 2) * 230
            gy = ry + 40 + (j // 2) * 50
            s.text(gx, gy, a, 12.5, MUTED)
            s.text(gx, gy + 22, b, 14.5, INK, 600, mono=True)
        arrow(s, [(cx + 94, cy), (RX0 - 40, cy), (RX0 - 40, ry + 70), (RX0 - 4, ry + 70)], VM[1], 1.6)
    s.text(cx, cy + 86, "恢复：几十到几百毫秒", 13, VM[2], 600, "middle")
    by = T + 500
    box(s, M, by, W - 2 * M, 70, ("#FFFFFF", BAD[1], INK), None, None, style="outline")
    s.rich(M + 22, by + 42, [("后果：", BAD[2], 700), ("一台宿主机上，所有沙箱的网络身份完全相同；而且所有模板用的是同一组常量，换个模板也一样。"
                              "客户机不知道自己是第几个副本。", SUB, 400)], 14)
    yy = s.footer(by + 70 + 34, "注：网卡配置真正读进客户机，只发生在构建模板时那一次开机；恢复沙箱不会重新开机，也不会重新配置（第 9 篇）。")
    save(s, "10-2-快照恢复出相同副本.svg", yy + 20)


# ------------------------------------------------------------------ 第 12 篇
def fig_12_steps():
    s = Svg()
    y0 = s.header("建网十一步：线程在宿主机和 ns-5 之间来回切换",
                  "“当前在哪个网络命名空间”是线程的属性。CreateNetwork 先把协程钉在一个线程上，再用 setns 在两个命名空间之间来回切，"
                  "每一步建的东西就落在线程当时所在的命名空间里。左列是宿主机，右列是 ns-5，粗线是线程的位置。")
    T = y0 + 40
    HX0, HX1 = 120, 690
    NX0, NX1 = 930, W - M
    s.rect(HX0 - 12, T, HX1 - HX0 + 24, 40, HOST[0], HOST[1], 1.2, rx=10)
    s.text((HX0 + HX1) / 2, T + 26, "宿主机命名空间", 15, HOST[2], 600, "middle")
    s.rect(NX0 - 12, T, NX1 - NX0 + 12, 40, NS[0], NS[1], 1.2, rx=10)
    s.text((NX0 + NX1) / 2, T + 26, "ns-5", 15, NS[2], 600, "middle")
    steps = [("h", "", "锁线程，记下宿主机命名空间", "LockOSThread；hostNS := netns.Get()", None),
             ("n", "1", "创建 ns-5，线程随即进入", "ip netns add ns-5", None),
             ("n", "2", "建 veth 对，配 vpeer", "eth0 = 10.14.0.11/31；e2bv-5 这头送回宿主机", None),
             ("h", "3", "配宿主机这一头", "e2bv-5 = 10.14.0.10/31", None),
             ("n", "4", "建 tap0，启用 lo", "tap0 = 169.254.0.22/30", None),
             ("n", "5", "默认路由", "default via 10.14.0.10", None),
             ("n", "6", "两条 NAT", "SNAT 169.254.0.21 → 10.13.0.5；DNAT 反过来", NAT),
             ("n", "7", "nftables 防火墙", "表 slot-firewall：4 个集合、5 条规则", None),
             ("h", "8", "到 Host IP 的路由", "10.13.0.5/32 via 10.14.0.11", NAT),
             ("h", "9", "转发放行 + MASQUERADE", "FORWARD × 2；-s 10.13.0.5/32 -j MASQUERADE", None),
             ("h", "10", "六条 REDIRECT", "192.0.2.1 的 3 条 + 防火墙代理 3 条", None),
             ("b", "11", "为 ns-5 打开一个 conntrack 句柄（补丁新增）", "netlink 套接字，为第 20 篇的回滚清理做准备；打开失败也不影响使用", None),
             ("h", "", "defer：回到宿主机", "无论成败，最后都切回宿主机", None)]
    rh, rg = 50, 10
    y = T + 60
    pts = []
    for k, (side, n, t, sub, role) in enumerate(steps):
        ry = y + k * (rh + rg)
        x0, x1 = {"h": (HX0, HX1), "n": (NX0, NX1 - 12), "b": (HX0, NX1 - 12)}[side]
        r = role or (HOST if side in "hb" else NS)
        s.rect(x0, ry, x1 - x0, rh, r[0] if role else "#FFFFFF", r[1], 1.2, rx=8, dash="5 4" if side == "b" else None)
        if n:
            num(s, x0 - 0 + 22, ry + rh / 2, n, r[1] if role else (HOST[2] if side == "h" else NS[2]), 12, 11.5)
        s.text(x0 + 44, ry + 21, t, 14, r[2] if role else INK, 600)
        s.text(x0 + 44, ry + 40, sub, 12, SUB, 400, mono=True)
        if side != "b":
            pts.append(((HX1 + 2) if side == "h" else (NX0 - 2), ry + rh / 2, side))
    # 线程的位置：在两列之间的竖条上画折线
    LH, LN = HX1 + 34, NX0 - 34
    d = ""
    for k, (x, yy, side) in enumerate(pts):
        lx = LH if side == "h" else LN
        d += (f"M{lx} {yy}" if k == 0 else f" L{lx} {yy}")
    s.path(d, INK, 3)
    for k, (x, yy, side) in enumerate(pts):
        lx = LH if side == "h" else LN
        s.circle(lx, yy, 5, INK)
        s.line(lx + (-5 if side == "n" else 5), yy, x, yy, "#C9D1D9", 1)
    for k in range(1, len(pts)):
        if pts[k][2] != pts[k - 1][2]:
            mx, my = (LH + LN) / 2, (pts[k][1] + pts[k - 1][1]) / 2
            s.rect(mx - 26, my - 11, 52, 20, "#FFFFFF", "#C9D1D9", 1, rx=10)
            s.text(mx, my + 4, "setns", 11.5, SUB, 600, "middle", mono=True)
    yb = y + len(steps) * (rh + rg)
    yy = s.footer(yb + 26, "注：步骤 1 的 netns.NewNamed 建好命名空间后会让当前线程进入它；步骤 2 建的 veth 两头起初都在 ns-5，"
                           "所以要把 e2bv-5 这头送回宿主机。如果不锁线程，Go 调度器把协程挪到别的线程上，后面的规则就会落到错误的命名空间。")
    save(s, "12-1-建网十一步.svg", yy + 20)


def fig_12_teardown():
    s = Svg()
    y0 = s.header("拆网：命名空间里的东西随它一起消失，宿主机上的要逐条删",
                  "删除 ns-5，里面的网卡、路由、NAT 规则、nftables 表都会一起消失。宿主机上的网卡、路由和 9 条 iptables 规则不会，"
                  "必须由 RemoveNetwork 逐条删掉。orchestrator 被强杀、断电或中途出错，宿主机这一侧就会留下残骸。")
    T = y0 + 40
    PW = (W - 2 * M - 40) / 2
    H = 420
    cols = [("ns-5 里", "删除命名空间时自动消失", NS,
             [("网卡", "lo、eth0（vpeer）、tap0"), ("路由", "default via 10.14.0.10"), ("iptables nat", "SNAT、DNAT 共 2 条"),
              ("nftables", "表 slot-firewall")]),
            ("宿主机上", "必须逐条删", HOST,
             [("网卡", "e2bv-5（显式删，避免和下一个同名网卡撞上）"), ("路由", "10.13.0.5/32 via 10.14.0.11"),
              ("iptables filter", "FORWARD 2 条"), ("iptables nat", "MASQUERADE 1 条 + REDIRECT 6 条")])]
    for i, (t, sub, role, items) in enumerate(cols):
        x = M + i * (PW + 40)
        s.rect(x, T, PW, H, role[0], role[1], 1.4, rx=16)
        s.text(x + 24, T + 36, t, 18, role[2], 600)
        s.text(x + 24 + text_w(t, 18) + 16, T + 36, sub, 14, SUB)
        for k, (a, b) in enumerate(items):
            ry = T + 64 + k * 74
            s.rect(x + 24, ry, PW - 48, 60, "#FFFFFF", role[1], 1, rx=9)
            s.text(x + 44, ry + 25, a, 13.5, role[2], 600)
            s.text(x + 44, ry + 46, b, 13.5, INK)
        if i == 1:
            s.rich(x + 24, T + H - 26, [("每个槽位 9 条 iptables 规则；", BAD[2], 700), ("300 个槽位就是 2700 条", SUB, 400)], 14)
        else:
            s.text(x + 24, T + H - 26, "命名空间的一大好处：里面的东西不用逐条删", 14, SUB)
    by = T + H + 30
    s.text(M, by + 6, "异常退出时留下的两种残骸", 17, INK, 600)
    cw = (W - 2 * M - 30) / 2
    for i, (t, sub) in enumerate([("残留的命名空间和 veth", "/var/run/netns/ns-N、e2bv-N 还在。orchestrator 启动时把已存在的 ns-N 当成别人的，这个编号不再用，可用编号越来越少。"),
                                  ("残留的 iptables 规则", "网卡删了，规则不会跟着消失，只是永远不会命中。攒到几万条后，每次改 iptables 都要读写整张表，建网和部署都变慢。")]):
        x = M + i * (cw + 30)
        box(s, x, by + 24, cw, 96, BAD, t, sub, 15, 13, align="start", pad=20)
    yy = s.footer(by + 24 + 96 + 34, "注：部署脚本停服务时会区分在用和残留的槽位，只清理残留的命名空间、veth 和 iptables 规则，并批量删除上万条规则（第 21 篇）。")
    save(s, "12-2-拆网.svg", yy + 20)


# ------------------------------------------------------------------ 第 14 篇
ZX = [M, 330, 790, 1310, W - M]


def fig_14_dns():
    s = Svg()
    y0 = s.header("沙箱为什么用不了宿主机的 dnsmasq：每条路都在半路被挡",
                  "把沙箱 /etc/resolv.conf 里的 nameserver 换成几个候选地址，看看 DNS 查询（UDP 53）各自走到哪里为止。"
                  "只有公网地址 8.8.8.8 走得通，而且要宿主机自己能直接访问到它。")
    T = y0 + 30
    H = 520
    roles = [VM, NS, HOST, ("#FFFFFF", HAIR, SUB)]
    names = ["沙箱", "ns-5（nftables）", "宿主机", "公网"]
    for i in range(4):
        f, st, tc = roles[i]
        s.rect(ZX[i], T, ZX[i + 1] - ZX[i], H, f, "none", 0, rx=0)
        s.text((ZX[i] + ZX[i + 1]) / 2, T + 28, names[i], 15, tc, 600, "middle")
    s.rect(ZX[0], T, ZX[4] - ZX[0], H, "none", HAIR, 1, rx=14)
    for i in (1, 2, 3):
        s.line(ZX[i], T + 40, ZX[i], T + H - 8, "#C9D1D9", 1, dash="4 4")
    rows = [("127.0.0.1", 200, "沙箱里的 127.0.0.1 是沙箱自己，里面没有 DNS 服务", "bad"),
            ("10.14.0.10（宿主机侧 veth）", ZX[1] + 140, "在 10.0.0.0/8 里，预置拦截集合，丢弃", "bad"),
            ("192.168.10.23（宿主机网卡）", ZX[1] + 140, "在 192.168.0.0/16 里，同样丢弃", "bad"),
            ("192.0.2.1（orchestrator 暗号）", ZX[2] + 200, "防火墙放行，但宿主机只为它的 TCP 80/111/2049 准备了改道，没有 DNS", "bad"),
            ("8.8.8.8", ZX[4] - 70, "放行 → SNAT → 宿主机转发、MASQUERADE → 物理网卡出去", "good")]
    for k, (ns_, stop, why, kind) in enumerate(rows):
        ry = T + 80 + k * 88
        s.text(ZX[0] + 18, ry + 5, "nameserver", 12, MUTED, 400, mono=True)
        s.text(ZX[0] + 18, ry + 26, ns_, 13.5, INK, 600, mono=True)
        x0 = ZX[1] - 30
        col = GOOD[1] if kind == "good" else BAD[1]
        if stop > x0:
            s.line(x0, ry + 10, stop, ry + 10, col, 2.2)
        if kind == "bad":
            cx = stop if stop > x0 else ZX[0] + 270
            s.circle(cx, ry + 10, 11, BAD[1])
            s.line(cx - 4.5, ry + 5.5, cx + 4.5, ry + 14.5, "#FFFFFF", 2)
            s.line(cx + 4.5, ry + 5.5, cx - 4.5, ry + 14.5, "#FFFFFF", 2)
            tx = cx + 22
        else:
            arrow(s, [(stop - 10, ry + 10), (stop + 4, ry + 10)], col, 2.2)
            s.pill(ZX[4] - 54, ry + 10, "8.8.8.8", GOOD, 12.5, mono=True)
            tx = ZX[1] + 10
        lines = wrap(why, (ZX[4] - 30 - tx) if kind == "bad" else 900, 13)
        for j, ln in enumerate(lines):
            s.text(tx, ry + 38 + 18 * j, ln, 13, BAD[2] if kind == "bad" else GOOD[2], 600 if j == 0 else 400)
    by = T + H + 26
    box(s, M, by, W - 2 * M, 70, ("#FFFFFF", NS[1], INK), None, None, style="outline")
    s.rich(M + 22, by + 42, [("即使连得上也不该用：", NS[2], 700), ("宿主机的 dnsmasq 把 *.e2b.app 答成 127.0.0.1、把 *.consul 转给内部 Consul，"
                              "这些内部答案不应该给不可信的沙箱看。所以两套 DNS 被刻意分开。", SUB, 400)], 14)
    yy = s.footer(by + 70 + 34, "注：也不能换成内网 DNS（私有地址）：nftables 的预置拦截规则排在用户放行规则前面，allowOut 也救不了（第 15 篇）。")
    save(s, "14-1-沙箱DNS的出路.svg", yy + 20)


if __name__ == "__main__":
    fig_09_frame()
    fig_09_netns_exec()
    fig_10_snapshot()
    fig_12_steps()
    fig_12_teardown()
    fig_14_dns()
