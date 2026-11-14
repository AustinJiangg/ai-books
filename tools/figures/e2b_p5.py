"""《E2B 沙箱网络从零讲透》第 20～22 篇的配图。用法: python3 tools/figures/e2b_p5.py"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from figkit import *  # noqa: E402,F401,F403
from figkit import W, M  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "e2b-network", "img")


def save(s, name, h):
    s.save(os.path.join(OUT, name), h)


def queue(s, x, y, w, h, title, sub, role, n=10, filled=7):
    """一条队列：外框 + 一排格子（实心的是排队中的槽位）。"""
    s.rect(x, y, w, h, role[0], role[1], 1.4, rx=12)
    s.text(x + 18, y + 26, title, 15, role[2], 600)
    s.text(x + 18 + text_w(title, 15) + 12, y + 26, sub, 12.5, SUB)
    cw = (w - 36 - (n - 1) * 6) / n
    for k in range(n):
        cx = x + 18 + k * (cw + 6)
        on = k >= n - filled
        s.rect(cx, y + 40, cw, h - 56, "#FFFFFF" if not on else role[1], role[1], 1, rx=5)
        if on:
            s.text(cx + cw / 2, y + 40 + (h - 56) / 2 + 4, "ns", 11, "#FFFFFF", 600, "middle", mono=True)


# ------------------------------------------------------------------ 第 20 篇
def fig_20_pool():
    s = Svg()
    y0 = s.header("网络槽位池：后台一直补货，取时先拿旧的，还时清理后放回",
                  "建一个槽位要十一步，现场建会拖慢毫秒级的恢复。orchestrator 启动后就在后台预建槽位放进新建队列；"
                  "创建沙箱时优先拿复用队列里的旧槽位；沙箱结束后清空用户规则，放回复用队列，满了就拆掉。")
    T = y0 + 40
    box(s, M, T + 30, 180, 100, KEY, "后台补货协程", "循环建槽位，放进新建队列；满了就等", 15, 12.5)
    QX0, QX1 = 300, 800
    queue(s, QX0, T + 20, QX1 - QX0, 120, "新建队列", "300 个（上游 32）：从没用过", NS)
    queue(s, QX0, T + 230, QX1 - QX0, 120, "复用队列", "1000 个（上游 100）：清理复位后的旧槽位", GOOD, filled=5)
    arrow(s, [(M + 182, T + 80), (QX0 - 4, T + 80)], INK, 1.6, label="放入", ldy=-10)
    # 取
    TX0, TX1 = 880, 1100
    box(s, TX0, T + 125, TX1 - TX0, 120, WHITE, "取一个槽位", "先看复用队列；没有再从新建队列拿（必要时等）", 15.5, 12.5,
        style="outline")
    arrow(s, [(QX1 + 4, T + 290), (840, T + 290), (840, T + 210), (TX0 - 4, T + 210)], GOOD[1], 1.8)
    s.text(850, T + 262, "优先", 13, GOOD[2], 600)
    arrow(s, [(QX1 + 4, T + 80), (840, T + 80), (840, T + 160), (TX0 - 4, T + 160)], NS[1], 1.6)
    s.text(850, T + 112, "复用队列", 12.5, NS[2], 600)
    s.text(850, T + 130, "空时", 12.5, NS[2], 600)
    # 在用
    UX0, UX1 = 1180, W - M
    box(s, UX0, T + 20, UX1 - UX0, 110, VM, "沙箱在用", "ConfigureInternet 装载用户的出站规则；Firecracker 在这个命名空间里运行", 15.5, 12.5)
    arrow(s, [(TX1 + 4, T + 185), (1140, T + 185), (1140, T + 75), (UX0 - 4, T + 75)], INK, 1.6)
    box(s, UX0, T + 200, UX1 - UX0, 110, NAT, "沙箱结束，归还", "ResetInternet：清空两个用户集合，重填预置集合", 15.5, 12.5)
    arrow(s, [((UX0 + UX1) / 2, T + 132), ((UX0 + UX1) / 2, T + 196)], INK, 1.6)
    arrow(s, [(UX0 - 4, T + 290), (1140, T + 290), (1140, T + 380), (QX1 - 60, T + 380), (QX1 - 60, T + 354)], GOOD[1], 1.8,
          )
    s.text(960, T + 372, "放回复用队列", 13, GOOD[2], 600, "middle")
    box(s, UX0, T + 360, UX1 - UX0, 70, BAD, "拆掉：RemoveNetwork", "复用队列已满，或清理失败", 15, 12.5)
    arrow(s, [((UX0 + UX1) / 2, T + 312), ((UX0 + UX1) / 2, T + 356)], BAD[1], 1.6)
    # 复用时没复位的
    by = T + 460
    box(s, M, by, W - 2 * M, 82, ("#FFFFFF", HAIR, INK), None, None, style="outline")
    s.text(M + 22, by + 32, "复用时原样保留的", 15, INK, 600)
    s.text(M + 22, by + 58, "命名空间、网卡、地址、路由、NAT 和 REDIRECT 规则都只和槽位编号有关，不用复位。conntrack 记录不主动清，"
                            "等它们自己超时；这段“槽位换了主人、内核记录还在”的窗口，也是连接池要按生命周期 ID 分组的原因之一。", 13.5, SUB)
    yy = s.footer(by + 82 + 34, "注：orchestrator 正常退出时会把两条队列里的空闲槽位逐个拆掉；被强杀时它们就成了残骸（第 12、21 篇）。")
    save(s, "20-1-槽位池.svg", yy + 20)


def fig_20_rollback():
    s = Svg()
    y0 = s.header("快照回滚后连接为什么卡死：客户机回到了过去，conntrack 没有",
                  "回滚把运行中的沙箱恢复到检查点，复用同一个槽位。客户机的 TCP 状态回到检查点那一刻，"
                  "但 ns-5 和宿主机的 conntrack 表还记着回滚前的最新状态。两边对不上，包被判 INVALID 丢弃。图中的序列号是示意。")
    T = y0 + 40
    X0, X1 = 300, W - M
    t_ck, t_rb0, t_rb1 = X0, 900, 1080

    def axis(y):
        s.line(X0, y, X1, y, "#C9D1D9", 1.2)
        for x, t in [(t_ck, "检查点"), (t_rb0, "停旧 Firecracker"), (t_rb1, "新 Firecracker 恢复")]:
            s.line(x, y - 4, x, y + 4, SUB, 1.2)
            s.text(x, y + 22, t, 12.5, SUB, 400, "middle")

    def lane(y, label, segs):
        s.text(M, y + 22, label, 14, INK, 600)
        for x0, x1, t, role in segs:
            s.rect(x0 + 2, y, x1 - x0 - 4, 36, role[0], role[1], 1.2, rx=8)
            s.text((x0 + x1) / 2, y + 23, t, 13, role[2], 600, "middle")

    rows = [("不清理", BAD, [("客户机的 TCP 状态", [(t_ck, t_rb0, "seq 1000 → 一路推进到 5000", VM), (t_rb1, X1, "回到 seq 1000（快照里的状态）", VM)]),
                            ("conntrack 记录", [(t_ck, t_rb0, "跟着推进到 5000", KEY), (t_rb1, X1, "仍记着 5000", BAD)])],
             "对不上：内核把客户机的包判为 INVALID 丢弃。连接不报错，只是卡住，客户机不停重发直到超时"),
            ("补丁：回滚时清 conntrack", GOOD, [("客户机的 TCP 状态", [(t_ck, t_rb0, "seq 1000 → 一路推进到 5000", VM), (t_rb1, X1, "回到 seq 1000（快照里的状态）", VM)]),
                                         ("conntrack 记录", [(t_ck, t_rb0, "跟着推进到 5000", KEY), (t_rb1, X1, "空：之后的包按新连接处理", GOOD)])],
             "FlushConntrack 在虚拟机停着的窗口里执行，没有流量，不会边清边产生新记录")]
    y = T + 10
    for title, role, lanes, note in rows:
        s.pill(M + (text_w(title, 14) + 22) / 2, y + 2, title, role, 14, solid=True, h=28)
        y += 30
        s.rect(t_rb0, y, t_rb1 - t_rb0, 100, "#F1F2F4", "none", 0, rx=0)
        s.text((t_rb0 + t_rb1) / 2, y + 54, "虚拟机停着", 12.5, MUTED, 400, "middle")
        if role is GOOD:
            s.rect(t_rb0 + 14, y + 66, t_rb1 - t_rb0 - 28, 28, GOOD[0], GOOD[1], 1.2, rx=14)
            s.text((t_rb0 + t_rb1) / 2, y + 85, "FlushConntrack", 12.5, GOOD[2], 700, "middle", mono=True)
        lane(y + 8, lanes[0][0], lanes[0][1])
        lane(y + 56, lanes[1][0], lanes[1][1])
        axis(y + 110)
        s.text(X0, y + 160, note, 13.5, role[2], 600)
        y += 200
    # 两张表怎么清
    by = y
    cw = (W - 2 * M - 30) / 2
    for i, (t, sub) in enumerate([("ns-5 的 conntrack 表：整张清空", "这张表里只有这一个沙箱的连接"),
                                  ("宿主机的 conntrack 表：只删和 10.13.0.5 有关的", "原始方向源地址或目的地址是这个 Host IP 的记录；"
                                   "这张表所有沙箱共用，不能误删")]):
        box(s, M + i * (cw + 30), by, cw, 84, ("#FFFFFF", GOOD[1], INK), t, sub, 15, 13, align="start", pad=20, style="outline")
    yy = s.footer(by + 84 + 34, "注：两张表同时清，互不依赖。代理层也配合：回滚中到达的请求立即返回明确错误；跨越回滚失败的请求返回“沙箱已回滚”（第 18 篇）。")
    save(s, "20-2-回滚与conntrack.svg", yy + 20)


def fig_20_socket():
    s = Svg()
    y0 = s.header("关闭一个 netlink 套接字要 250 毫秒：比回滚本身还慢",
                  "清理 conntrack 要通过 netlink 套接字。最初每次回滚都临时开一个、用完关掉；在鲲鹏 920（内核 6.6）上实测，"
                  "关闭时内核要等 nf_tables 的工作队列清空，而建新槽位时这个队列正忙。")
    T = y0 + 40
    X0, X1 = 360, 1180
    vmax = 500

    def px(v):
        return X0 + v / vmax * (X1 - X0)
    ay = T + 250
    s.line(X0, ay, X1, ay, SUB, 1.2)
    for v in range(0, 501, 100):
        s.line(px(v), ay, px(v), ay + 6, SUB, 1.2)
        s.text(px(v), ay + 24, f"{v}", 12.5, SUB, 400, "middle", mono=True)
    s.text(X1 + 10, ay + 5, "毫秒", 12.5, SUB)
    # 回滚本身
    y = T + 40
    s.text(M, y + 24, "一次回滚本身", 15, INK, 600)
    s.rect(X0, y, px(100) - X0, 36, "#D9DCE1", "none", 0, rx=4)
    s.text(px(100) + 12, y + 24, "约 100", 14, INK, 600)
    # 关闭套接字
    y = T + 120
    s.text(M, y + 24, "关闭一次 netlink 套接字", 15, INK, 600)
    s.rect(X0, y, px(250) - X0, 36, BAD[1], "none", 0, rx=4)
    s.line(px(127), y + 50, px(447), y + 50, BAD[1], 2)
    for v, t in [(127, "最快 127"), (250, "中位 250"), (447, "最慢 447")]:
        s.line(px(v), y + 44, px(v), y + 56, BAD[1], 2)
        s.text(px(v), y + 76, t, 13, BAD[2], 600, "middle")
    s.text(px(250) + 12, y + 24, "250", 14, "#FFFFFF" if False else BAD[2], 700)
    # 右侧
    RX = 1260
    box(s, RX, T + 10, W - M - RX, 110, ("#FFFFFF", BAD[1], INK), "耗时超过 150 毫秒的回滚里",
        "87% 能用“某一次关闭套接字”解释；这一步占整个回滚耗时的 90%", 15, 13, align="start", pad=18, style="outline")
    box(s, RX, T + 140, W - M - RX, 150, GOOD, "补丁：回滚路径上不开也不关套接字",
        "ns-5 这边：建网第 11 步打开，存在槽位里，拆网时交给后台协程关闭。宿主机这边：常驻清扫器持有一个，批量处理所有沙箱", 15, 12.5,
        align="start", pad=18)
    yy = s.footer(ay + 70, "注：某个槽位的套接字坏了，就退回“进命名空间、临时开一个”的老办法，并只打印一次告警。看起来理所当然很快的操作，也要靠实测确认。")
    save(s, "20-3-关闭套接字.svg", yy + 20)


# ------------------------------------------------------------------ 第 21 篇
def fig_21_order():
    s = Svg()
    y0 = s.header("build.sh -s 的顺序：ip_forward 必须先于槽位池，入口规则放最后",
                  "和网络有关的七步按下面的顺序执行。最关键的一条依赖：新命名空间的 ip_forward 在创建那一刻从宿主机继承，"
                  "之后改宿主机的值对已建好的命名空间无效，所以第 4 步必须在第 6 步建槽位池之前。")
    T = y0 + 110
    steps = [("Harbor", "安装并启动镜像仓库", WHITE), ("start-server.sh", "Consul / Nomad 服务端", WHITE),
             ("start-client.sh", "resolv.conf 第一行 127.0.0.1；Consul 转发；连接队列参数", WHITE),
             ("init-client.sh", "ip_forward = 1", NAT), ("/etc/hosts", "加 <本机IP> harbor，重启 dnsmasq", WHITE),
             ("deploy.sh", "启动 template-manager，开始建槽位池", NS), ("入口规则", "80 → 3002，先删老规则", WHITE)]
    n = len(steps)
    gap = 18
    bw = (W - 2 * M - (n - 1) * gap) / n
    xs = [M + k * (bw + gap) for k in range(n)]
    for k, (t, sub, role) in enumerate(steps):
        box(s, xs[k], T, bw, 120, role, t, sub, 14.5, 12, style="outline" if role is WHITE else "fill")
        num(s, xs[k] + bw / 2, T, k + 1, INK, 13, 13)
        if k < n - 1:
            arrow(s, [(xs[k] + bw + 2, T + 60), (xs[k + 1] - 3, T + 60)], INK, 1.5)
    # 依赖弧线
    def arc(a, b, t, role, up=True, h=56):
        xa, xb = xs[a] + bw / 2, xs[b] + bw / 2
        yb = T + 120 if not up else T - 14
        sign = 1 if not up else -1
        s.path(f"M{xa} {yb + sign * 4} C{xa} {yb + sign * h} {xb} {yb + sign * h} {xb} {yb + sign * 6}", role[1], 1.8,
               end=True)
        s.text((xa + xb) / 2, yb + sign * (h * 0.75 + (16 if not up else 4)), t, 13, role[2], 600, "middle")
    arc(3, 5, "必须在前：命名空间创建时继承 ip_forward", NAT, up=False, h=70)
    arc(2, 4, "dnsmasq 只在启动时读 /etc/hosts，所以这里再重启一次", NS, up=True, h=80)
    # 顺序错了会怎样 / openEuler
    by = T + 230
    cw = (W - 2 * M - 30) / 2
    box(s, M, by, cw, 112, BAD, "顺序错了会怎样",
        "整池槽位都转不了包：宿主机连不上客户机里的 envd，构建模板在等 envd 时 60 秒超时，报 build was cancelled。"
        "只能重启 template-manager，让它把整池重建。", 15.5, 13, align="start", pad=20)
    box(s, M + cw + 30, by, cw, 112, ("#FFFFFF", NAT[1], INK), "openEuler 的坑",
        "自带的 /etc/sysctl.conf 写死 ip_forward=0，而 sysctl -p 只读这个文件，会把值压回 0。"
        "脚本：直接改这一行为 1 → sysctl -p → 再 sysctl -w 一次。", 15.5, 13, align="start", pad=20, style="outline")
    yy = s.footer(by + 112 + 34, "注：入口规则放在最后，是因为它们是全局规则，和槽位无关；所有 iptables 命令都带 -w 等 xtables 锁，"
                                "并用 -C … || -A … 写法，重复执行 -s 也安全。")
    save(s, "21-1-部署顺序.svg", yy + 20)


def fig_21_cleanup():
    s = Svg()
    y0 = s.header("build.sh -d 只清自己的残留：认名字、看进程、先停 orchestrator",
                  "宿主机上不只有 E2B 的网络。清理脚本只认 ns-<数字> 和 e2bv-<数字>；命名空间里有进程的是在用的，保留。"
                  "空闲的池中槽位和泄漏的残骸在宿主机上看起来一样，所以必须先停掉 orchestrator，剩下的空闲命名空间才都算残骸。")
    T = y0 + 40
    cw = (W - 2 * M - 2 * 30) / 3
    cols = [("不是 E2B 的：不碰", WHITE, ["veth-4（AgentENV）", "docker0、容器的 veth", "cni0、vethab12（k3s）", "virbr0（libvirt）"]),
            ("E2B 的、在用：保留", GOOD, ["ns-2：里面有 Firecracker 进程", "e2bv-2", "它的 9 条 iptables 规则"]),
            ("E2B 的、空闲：删除", BAD, ["ns-3、ns-7：里面没有进程", "e2bv-3、e2bv-7 等孤儿 veth", "它们的 iptables 规则"])]
    for i, (t, role, items) in enumerate(cols):
        x = M + i * (cw + 30)
        s.rect(x, T, cw, 250, role[0] if role is not WHITE else "#FCFBFA", role[1] if role is not WHITE else HAIR, 1.3, rx=14)
        s.text(x + 22, T + 34, t, 16.5, role[2] if role is not WHITE else INK, 600)
        for k, it in enumerate(items):
            s.rect(x + 22, T + 56 + k * 46, cw - 44, 36, "#FFFFFF", role[1] if role is not WHITE else HAIR, 1, rx=8)
            s.text(x + 38, T + 80 + k * 46, it, 13.5, INK, 400)
    s.text(M + 2 * (cw + 30) + 22, T + 240 - 8, "前提：orchestrator 已停（池子只在它内存里）", 12.5, BAD[2], 600)
    # iptables 批量删
    by = T + 290
    s.text(M, by, "残留的 iptables 规则怎么删", 17, INK, 600)
    hw = (W - 2 * M - 30) / 2
    box(s, M, by + 18, hw, 110, ("#FFFFFF", BAD[1], INK), "逐条 iptables -D",
        "每删一条都要把整张表读出来再写回去；上万条规则要跑几个小时。同机 k3s 的 kube-proxy 还在抢锁。", 15.5, 13,
        align="start", pad=20, style="outline")
    box(s, M + hw + 30, by + 18, hw, 110, GOOD, "iptables-restore --noflush",
        "把所有删除指令拼成一份文件一次提交；--noflush 只执行这些删除、不清空整张表，Docker、k3s 的规则不受影响。例：nat 25000 → 120。", 15.5, 13,
        align="start", pad=20)
    ry = by + 160
    s.text(M, ry, "怎么认出残留规则", 15, INK, 600)
    bullets(s, M, ry + 30, [[("REDIRECT 6 条、FORWARD 2 条：", INK, 600), ("匹配 -i/-o e2bv-<数字>；排除在用槽位时匹配 \"e2bv-5 \"（带尾随空格，免得连 e2bv-50 一起排除）", SUB, 400)],
                            [("MASQUERADE：", INK, 600), ("不带网卡名，按源地址是 Host 池里的某个 /32 识别；在用槽位按“池起点 + 编号”算出 Host IP 来排除", SUB, 400)]],
            13.5, 30, dot=MUTED)
    yy = s.footer(ry + 90, "注：-d 最先用 nomad job stop 优雅停 template-manager（最多等 40 秒），让它自己拆槽位池；直接 kill -9 会把几百个槽位当场变成残骸。"
                           "只想清沙箱网络时用 --recycle-netns：停 template-manager → 清理 → 重新拉起。")
    save(s, "21-2-清理残留.svg", yy + 20)


# ------------------------------------------------------------------ 第 22 篇
def fig_22_layers():
    s = Svg()
    y0 = s.header("分层排障：从外到内一层层排除",
                  "把这套网络分成七层。入站问题（SDK、浏览器访问不了沙箱）从第 1 层往下查到第 6 层；"
                  "出站问题（沙箱访问不了外部）从第 6 层查到第 7 层。右边是每层最先看的命令。")
    T = y0 + 36
    layers = [("DNS", "宿主机能否把域名解析对？", "dig 49983-xxx.e2b.app @127.0.0.1　·　dig pypi.org @127.0.0.1", 17),
              ("入口", "80 端口的流量送到 3002 了吗？", "iptables -t nat -S | grep 3002", 17),
              ("代理", "client-proxy、orchestrator 代理正常？目录里有这个沙箱？", "ss -lntp | grep -E '3002|5007'　·　api、client-proxy 日志", 18),
              ("槽位", "槽位网络完整？宿主机到 Host IP 通不通？", "ip route get 10.13.0.5　·　iptables -t nat -S | grep e2bv-5", 11),
              ("命名空间", "NAT、nftables 正确？", "ip netns exec ns-5 iptables -t nat -S　·　ip netns exec ns-5 nft list ruleset", 15),
              ("客户机", "服务在监听吗？DNS 配置对吗？", "进沙箱看监听端口和 /etc/resolv.conf", 14),
              ("出站", "TCP 代理怎么判的？宿主机能访问目标吗？", "ss -lnt | grep 501[6-8]　·　orchestrator 日志　·　宿主机 curl 目标", 16)]
    LX = 220
    rh, rg = 66, 10
    for k, (name, q, cmd, ch) in enumerate(layers):
        y = T + k * (rh + rg)
        role = [WHITE, NAT, GOOD, HOST, NS, VM, GOOD][k]
        s.rect(LX, y, W - M - LX, rh, "#FFFFFF" if k % 2 else "#F7F8FA", "none", 0, rx=10)
        num(s, LX + 26, y + rh / 2, k + 1, INK, 14, 13.5)
        s.text(LX + 52, y + 28, name, 15.5, INK, 600)
        s.text(LX + 52, y + 50, f"第 {ch} 篇", 12, MUTED)
        s.text(LX + 170, y + 28, q, 14, INK, 600)
        s.text(LX + 170, y + 50, cmd, 12.5, SUB, 400, mono=True)
    # 左侧方向
    ya, yb = T + 6, T + 5 * (rh + rg) + rh - 6
    arrow(s, [(M + 50, ya), (M + 50, yb)], NS[1], 3)
    s.text(M + 64, (ya + yb) / 2 - 10, "入站", 15, NS[2], 600)
    s.text(M + 64, (ya + yb) / 2 + 10, "1 → 6", 13, NS[2], 400, mono=True)
    yc, yd = T + 5 * (rh + rg) + 8, T + 6 * (rh + rg) + rh - 6
    arrow(s, [(M + 130, yc), (M + 130, yd)], GOOD[1], 3)
    s.text(M + 144, (yc + yd) / 2 - 2, "出站", 15, GOOD[2], 600)
    s.text(M + 144, (yc + yd) / 2 + 18, "6 → 7", 13, GOOD[2], 400, mono=True)
    yy = s.footer(T + 7 * (rh + rg) + 24, "注：确定是哪一层之后，再用 tcpdump 在那一层前后的网卡上抓包对比（见下图）。常见问题速查见下表。")
    save(s, "22-1-分层排障.svg", yy + 20)


def fig_22_tcpdump():
    s = Svg()
    y0 = s.header("tcpdump 在哪块网卡抓：同一个包，三处看到三种源地址",
                  "沙箱发往 8.8.8.8 的 DNS 查询，在三块网卡上分别是下面的样子。对比同一个包在几处的样子，"
                  "就能判断它在哪一层被丢了、地址在哪一步被改了。")
    T = y0 + 40
    ZX = [M, 330, 790, 1310, W - M]
    roles = [VM, NS, HOST, ("#FFFFFF", HAIR, SUB)]
    names = ["客户机", "ns-5", "宿主机", "互联网"]
    H = 274
    for i in range(4):
        f, st, tc = roles[i]
        s.rect(ZX[i], T, ZX[i + 1] - ZX[i], H, f, "none", 0, rx=0)
        s.text((ZX[i] + ZX[i + 1]) / 2, T + 30, names[i], 15, tc, 600, "middle")
    s.rect(ZX[0], T, ZX[4] - ZX[0], H, "none", HAIR, 1, rx=14)
    cy = T + 130
    s.line(ZX[0] + 140, cy, 1450, cy, INK, 2.2, end=True)
    chip(s, ZX[0] + 80, cy, 120, 40, VM, "dig pypi.org", None, 13)
    chip(s, 1500, cy, 90, 40, WHITE, "8.8.8.8", None, 13)
    caps = [(ZX[1], "tap0", "ip netns exec ns-5 tcpdump -i tap0", "169.254.0.21:41234", "原始包，还没改地址", False),
            (ZX[2], "e2bv-5", "tcpdump -i e2bv-5", "10.13.0.5:41234", "ns-5 的 SNAT 之后", True),
            (ZX[3], "enp125s0f0", "tcpdump -i enp125s0f0", "192.168.10.23:41234", "宿主机 MASQUERADE 之后", True)]
    for x, nic, cmd, src, note, changed in caps:
        s.line(x, T + 50, x, T + H - 10, "#C9D1D9", 1, dash="4 4")
        w = 250
        s.rect(x - w / 2, cy - 34, w, 68, "#FFFFFF", "#AEB6BE", 1.2, rx=9)
        if changed:
            s.rect(x - w / 2 + 6, cy - 28, w - 12, 26, NAT[0], NAT[0], 0, rx=5)
        s.text(x - w / 2 + 14, cy - 10, "源", 12, MUTED)
        s.text(x - w / 2 + 44, cy - 10, src, 14, NAT[2] if changed else INK, 700 if changed else 400, mono=True)
        s.text(x - w / 2 + 14, cy + 20, "目的", 12, MUTED)
        s.text(x - w / 2 + 44, cy + 20, "8.8.8.8:53", 14, INK, 400, mono=True)
        s.pill(x, T + 62, nic, ("#FFFFFF", "#AEB6BE", SUB), 12, mono=True, h=22)
        s.text(x, cy + 66, note, 13, SUB, 400, "middle")
        s.rect(x - 200, cy + 86, 400, 32, "#1F2328", "none", 0, rx=6)
        s.text(x, cy + 107, cmd, 12.5, "#F6F8FA", 400, "middle", mono=True)
    yy = s.footer(T + H + 34, "注：去 pypi.org 的 TCP 包在 e2bv-5 上还能看到，但不会出现在物理网卡上：它被 REDIRECT 给了防火墙代理，"
                              "物理网卡上看到的是代理另开的那条连接（第 13、16 篇）。")
    save(s, "22-2-抓包位置.svg", yy + 20)


if __name__ == "__main__":
    fig_20_pool()
    fig_20_rollback()
    fig_20_socket()
    fig_21_order()
    fig_21_cleanup()
    fig_22_layers()
    fig_22_tcpdump()
