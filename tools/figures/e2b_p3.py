"""《E2B 沙箱网络从零讲透》第 15～19 篇的配图。用法: python3 tools/figures/e2b_p3.py"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from figkit import *  # noqa: E402,F401,F403
from figkit import W, M  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "e2b-network", "img")


def save(s, name, h):
    s.save(os.path.join(OUT, name), h)


def diamond(s, cx, cy, w, h, lines, size=13.5):
    s.o.append(f'<path d="M{cx} {cy - h / 2} L{cx + w / 2} {cy} L{cx} {cy + h / 2} L{cx - w / 2} {cy} Z" '
               f'fill="#FFFFFF" stroke="{SUB}" stroke-width="1.4"/>')
    for k, t in enumerate(lines):
        s.text(cx, cy + 5 + (k - (len(lines) - 1) / 2) * 19, t, size, INK, 600, "middle")


def outcome(s, x, cy, t, kind, w=150):
    role = {"ok": GOOD, "drop": BAD, "tcp": KEY}[kind]
    s.rect(x, cy - 18, w, 36, role[0], role[1], 1.3, rx=18)
    s.text(x + w / 2, cy + 5, t, 14, role[2], 600, "middle")


# ------------------------------------------------------------------ 第 15 篇
def fig_15_rules():
    s = Svg()
    y0 = s.header("命名空间防火墙的五条规则：从上往下，命中即停",
                  "每个从 tap0 进来的包（沙箱发出的包）依次回答下面几个问题。前三条对所有协议生效；用户的放行、拦截只管非 TCP，"
                  "TCP 在这一层放过去，到宿主机交给防火墙代理再判一次。")
    T = y0 + 30
    QX0, QX1 = 300, 940
    OX = 990
    box(s, QX0, T, QX1 - QX0, 50, WHITE, "从 tap0 进入 ns-5 的包", None, 15, style="outline")
    rows = [("规则 1", "属于已建立的连接？", "ct state established,related", ("放行", "ok")),
            ("规则 2", "目的在预置放行集合里？", "只有 192.0.2.1", ("放行", "ok")),
            ("规则 3", "目的在预置拦截集合里？", "10/8 · 172.16/12 · 192.168/16 · 127/8 · 169.254/16", ("丢弃", "drop")),
            ("", "是 TCP 吗？", "", ("交给 TCP 代理", "tcp")),
            ("规则 4", "目的在用户放行集合里？", "allowOut 的 IP/CIDR（+ 8.8.8.8）", ("放行", "ok")),
            ("规则 5", "目的在用户拦截集合里？", "denyOut，或断网时的 0.0.0.0/0", ("丢弃", "drop"))]
    rh, rg = 64, 26
    y = T + 50 + rg
    ys = []
    for k, (rn, q, sub, (res, kind)) in enumerate(rows):
        cy = y + rh / 2
        ys.append(cy)
        tcpq = rn == ""
        if tcpq:
            diamond(s, (QX0 + QX1) / 2, cy, 300, rh, [q])
        else:
            s.rect(QX0, y, QX1 - QX0, rh, "#FFFFFF", "#AEB6BE", 1.2, rx=10)
            s.text(QX0 + 20, cy - 5, rn, 13, MUTED, 600)
            s.text(QX0 + 90, cy - 5, q, 15, INK, 600)
            s.text(QX0 + 90, cy + 17, sub, 12.5, SUB, 400, mono=True)
        xr = (QX0 + QX1) / 2 + 150 if tcpq else QX1
        arrow(s, [(xr + 2, cy), (OX - 4, cy)], GOOD[1] if kind == "ok" else BAD[1] if kind == "drop" else SUB, 1.6,
              label="是", ldy=-8)
        outcome(s, OX, cy, res, kind, 170 if kind == "tcp" else 120)
        ytop = y - rg
        arrow(s, [((QX0 + QX1) / 2, ytop + (0 if k else 0)), ((QX0 + QX1) / 2, y - 3 if not tcpq else cy - rh / 2 - 3)],
              INK, 1.5)
        if k:
            s.text((QX0 + QX1) / 2 + 10, ytop + 17, "否", 12.5, MUTED, 600)
        y += rh + rg
    # 默认
    arrow(s, [((QX0 + QX1) / 2, y - rg), ((QX0 + QX1) / 2, y - 3)], INK, 1.5)
    s.text((QX0 + QX1) / 2 + 10, y - rg + 17, "否", 12.5, MUTED, 600)
    box(s, QX0 + 120, y, QX1 - QX0 - 240, 48, GOOD, "链的默认策略：放行", None, 15)
    # 左侧分组括号
    def brk(a, b, t1, t2):
        ya, yb = ys[a] - rh / 2, ys[b] + rh / 2
        s.path(f"M{QX0 - 14} {ya} h-10 V{yb} h10", MUTED, 1.3)
        s.text(QX0 - 34, (ya + yb) / 2 - 4, t1, 14.5, INK, 600, "end")
        s.text(QX0 - 34, (ya + yb) / 2 + 18, t2, 12.5, SUB, 400, "end")
    brk(0, 2, "预置规则", "所有协议")
    brk(4, 5, "用户规则", "只管非 TCP")
    # 右侧要点
    NX = 1190
    notes = [("规则 3 在规则 4 前面", "allowOut 写了 10.0.0.5 也没用：包先撞上规则 3 被丢弃。私有地址永远放不出去，这是刻意的。", BAD),
             ("规则 4 在规则 5 前面", "允许优先：denyOut 0.0.0.0/0 + allowOut 1.1.1.1，就是“拒绝一切，只开一个口子”。", GOOD),
             ("规则 1 排第一", "宿主机先发起的连接（比如连 envd），沙箱的回包目的是 10.14.0.10，也在拦截范围内，靠它放行。", NS)]
    ny = T + 76
    for t, sub, role in notes:
        h = need_h(W - M - NX, t, sub, 14.5, 13, 18, 30)
        s.rect(NX, ny, W - M - NX, h, "#FFFFFF", role[1], 1.2, rx=10)
        s.rect(NX, ny, 5, h, role[1], role[1], 0, rx=2)
        box(s, NX + 4, ny, W - M - NX - 4, h, ("#FFFFFF", "none", role[2]), t, sub, 14.5, 13, align="start", pad=18, sw=0)
        ny += h + 18
    yy = s.footer(y + 48 + 34, "注：每条规则都以 iifname \"tap0\" 开头，只检查沙箱发出的包；外面进来的包和回包不受约束。"
                               "这张表挂在 PREROUTING，优先级 -150，比 NAT 早，看到的是沙箱原本想访问的地址。")
    save(s, "15-1-五条规则.svg", yy + 20)


def fig_15_config():
    s = Svg()
    y0 = s.header("用户的出站配置怎么变成集合里的元素",
                  "创建沙箱时的三个参数，先在 api 里校验、拆分、补 DNS，再交给 orchestrator 变成三个列表。IP 和网段装进 nftables 的用户集合，"
                  "域名只留给 TCP 防火墙代理。规则在沙箱拿到槽位时设置一次，归还时清空。")
    T = y0 + 36
    cols = [(M, 300, "用户参数"), (400, 760, "api：校验与转换"), (860, 1150, "交给 orchestrator 的三个列表"), (1250, W - M, "最后装到哪")]
    for x0, x1, t in cols:
        s.text(x0, T, t, 16, INK, 600)
    y = T + 22
    params = [("allow_internet_access", "true / false"), ("network.allowOut", "IP、CIDR、域名（可用 *.example.com）"),
              ("network.denyOut", "只能是 IP 或 CIDR")]
    for k, (a, b) in enumerate(params):
        ry = y + k * 112
        box(s, M, ry, 252, 88, WHITE, a, b, 14, 12.5, style="outline")
    steps = [("校验", "denyOut 只能是 IP/CIDR；allowOut 有域名时，denyOut 必须含 0.0.0.0/0"),
             ("拆分", "allowOut 拆成 IP/CIDR 和域名两部分"),
             ("补 DNS", "有域名就把 8.8.8.8 加进放行的 IP"),
             ("断网", "allow_internet_access=false：拦截列表整个换成 0.0.0.0/0")]
    for k, (a, b) in enumerate(steps):
        ry = y + k * 84
        box(s, 400, ry, 360, 70, KEY, a, b, 14, 12.5, align="start", pad=18)
    for k in range(3):
        arrow(s, [(M + 254, y + k * 112 + 44), (396, y + k * 112 + 44)], SUB, 1.4)
    lists = [("AllowedCidrs", "allowOut 的 IP/CIDR（+ 8.8.8.8）", NS),
             ("AllowedDomains", "allowOut 的域名", GOOD),
             ("DeniedCidrs", "denyOut，或 0.0.0.0/0", BAD)]
    for k, (a, b, role) in enumerate(lists):
        ry = y + k * 112
        box(s, 860, ry, 290, 88, role, a, b, 15, 12.5)
        arrow(s, [(764, y + 150), (812, y + 150), (812, ry + 44), (856, ry + 44)], SUB, 1.4)
    s.text(860, y + 3 * 112 + 8, "请求里没带 allow_internet_access 时，", 12.5, SUB)
    s.text(860, y + 3 * 112 + 28, "用节点开关 ALLOW_SANDBOX_INTERNET", 12.5, SUB)
    dests = [("nftables 用户放行集合", "filtered_allowlist：管非 TCP", NS, [0]),
             ("TCP 防火墙代理", "按域名 + IP 判定 TCP（第 16 篇）", GOOD, [0, 1, 2]),
             ("nftables 用户拦截集合", "filtered_denylist：管非 TCP", BAD, [2])]
    dy = [y, y + 112, y + 224]
    for k, (a, b, role, srcs) in enumerate(dests):
        box(s, 1250, dy[k], W - M - 1250, 88, ("#FFFFFF", role[1], role[2]), a, b, 15, 12.5)
        for sidx in srcs:
            sy = y + sidx * 112 + 44
            xv = 1180 + sidx * 20
            arrow(s, [(1154, sy), (xv, sy), (xv, dy[k] + 44 + (sidx - 1) * 10), (1246, dy[k] + 44 + (sidx - 1) * 10)],
                  {0: NS[1], 1: GOOD[1], 2: BAD[1]}[sidx], 1.4)
    # 生命周期
    ly = y + 3 * 112 + 70
    s.text(M, ly, "这些规则的一生", 16, INK, 600)
    stages = [("取槽位时", "ConfigureInternet：三个列表都空就什么也不做；否则进命名空间往集合里加元素", NS),
              ("运行中", "没有接口可以修改；要换规则只能暂停再恢复，或重建沙箱", KEY),
              ("归还槽位时", "ResetInternet：清空两个用户集合，重填两个预置集合，防止规则留给下一个沙箱", NAT)]
    sw = (W - 2 * M - 2 * 40) / 3
    for k, (a, b, role) in enumerate(stages):
        x = M + k * (sw + 40)
        box(s, x, ly + 18, sw, 92, role, a, b, 15, 12.5, align="start", pad=18)
        if k < 2:
            arrow(s, [(x + sw + 4, ly + 64), (x + sw + 36, ly + 64)], INK, 1.6)
    yy = s.footer(ly + 18 + 92 + 34, "注：0.0.0.0/0 在 Go 的地址库里不算合法网段，代码直接往集合里写入 0.0.0.0～255.255.255.255 这个区间。")
    save(s, "15-2-用户配置到集合.svg", yy + 20)


# ------------------------------------------------------------------ 第 16 篇
def fig_16_proxy():
    s = Svg()
    y0 = s.header("TCP 防火墙代理接到一个连接后：认人、查限额、问原址、读域名、判定、替它去连",
                  "沙箱发出的 TCP 连接通过 nftables 后，在宿主机按目的端口分三路 REDIRECT 到代理。代理按下面的顺序处理；"
                  "拒绝时直接关闭沙箱这边的连接，所以沙箱看到的是“连上了又被关掉”，不是超时。")
    T = y0 + 36
    # 左：三个端口
    s.text(M, T, "按目的端口分三路", 15, INK, 600)
    ports = [("80 → 5016", "读 HTTP Host 头"), ("443 → 5017", "读 TLS SNI"), ("其他 → 5018", "不读内容，只看 IP")]
    for k, (a, b) in enumerate(ports):
        ry = T + 20 + k * 86
        box(s, M, ry, 250, 70, WHITE, a, b, 15, 12.5, style="outline")
        arrow(s, [(M + 252, ry + 35), (M + 300, ry + 35), (M + 300, T + 150), (M + 340, T + 150)], SUB, 1.4)
    s.text(M, T + 300, "分开端口，是为了不卡住 SSH", 12.5, SUB)
    s.text(M, T + 320, "这类服务器先说话的协议", 12.5, SUB)
    # 中：五步
    PX0, PX1 = M + 344, 860
    steps = [("① 这是哪个沙箱", "用源地址 Host IP（如 10.13.0.5）查运行中的沙箱；找不到就关闭"),
             ("② 连接数限额", "每个沙箱的并发连接有上限，超了就关闭"),
             ("③ 原本要去哪", "SO_ORIGINAL_DST 从 conntrack 取回，如 151.101.0.223:443"),
             ("④ 读域名", "5016 读 Host，5017 读 SNI；只偷看不消费，之后原样转发"),
             ("⑤ 判定", "isEgressAllowed，顺序见右边")]
    for k, (a, b) in enumerate(steps):
        ry = T + 20 + k * 74
        box(s, PX0, ry, PX1 - PX0, 62, GOOD if k == 4 else KEY, a, b, 14.5, 12.5, align="start", pad=18)
        if k < 4:
            arrow(s, [((PX0 + PX1) / 2, ry + 62), ((PX0 + PX1) / 2, ry + 72)], INK, 1.3)
    # 右：判定顺序
    RX0 = 920
    s.text(RX0, T, "判定顺序（允许优先，默认放行）", 15, INK, 600)
    rules = [("沙箱没有任何网络配置", "放行", "ok"), ("有域名，且匹配 AllowedDomains", "放行（按域名）", "ok"),
             ("目的 IP 在 AllowedCidrs", "放行（按 IP）", "ok"), ("目的 IP 在 DeniedCidrs", "拒绝", "drop"), ("以上都不是", "放行", "ok")]
    for k, (a, res, kind) in enumerate(rules):
        ry = T + 20 + k * 64
        s.rect(RX0, ry, W - M - RX0, 52, "#FFFFFF" if k % 2 else "#F7F8FA", "none", 0, rx=8)
        num(s, RX0 + 22, ry + 26, k + 1, INK, 11, 12)
        s.text(RX0 + 44, ry + 31, a, 14, INK)
        role = GOOD if kind == "ok" else BAD
        s.text(W - M - 16, ry + 31, res, 14, role[2], 600, "end")
    s.text(RX0, T + 20 + 5 * 64 + 4, "域名匹配：pypi.org 不含 www.pypi.org；*.example.com 不含 example.com 本身", 12.5, SUB)
    # 下：⑥ 替它去连
    by = T + 20 + 5 * 74 + 30
    s.text(M, by, "⑥ 放行后，代理以宿主机身份新开一条连接，然后双向搬运数据", 16, INK, 600)
    bw = (W - 2 * M - 40) / 2
    for i, (t, sub, role) in enumerate([
            ("按域名放行", "不用沙箱给的 IP：在宿主机上重新解析域名，解析结果在预置拦截段里就拒绝（连 SYN 都不发），否则连解析出的地址", GOOD),
            ("按 IP 放行，或默认放行", "连 SO_ORIGINAL_DST 拿到的那个 IP 和端口，也就是沙箱原本想去的地方", KEY)]):
        x = M + i * (bw + 40)
        box(s, x, by + 18, bw, 96, role, t, sub, 15.5, 13, align="start", pad=20)
    yy = s.footer(by + 18 + 96 + 34, "注：所有沙箱的所有出站 TCP 都经过这个代理，它运行在 orchestrator 进程里；orchestrator 挂了，"
                                     "REDIRECT 规则还在但 5016～5018 没人监听，沙箱的出站 TCP 全部失败。")
    save(s, "16-1-防火墙代理.svg", yy + 20)


def fig_16_bypass():
    s = Svg()
    y0 = s.header("防绕过：按域名放行时，代理自己重新解析域名",
                  "用户只允许 pypi.org。沙箱里的恶意代码在 /etc/hosts 写一行 203.0.113.66 pypi.org，再去连 pypi.org:443："
                  "SNI 写的是 pypi.org，实际目的 IP 却是攻击者的服务器。代理连哪个地址，决定了这条规则还算不算数。")
    T = y0 + 36
    # 上：共同部分
    box(s, M, T, W - 2 * M, 76, ("#FCFBFA", HAIR, INK), None, None)
    parts = [("沙箱 /etc/hosts", "203.0.113.66 pypi.org"), ("连接的原始目的", "203.0.113.66:443"), ("TLS 里的 SNI", "pypi.org"),
             ("用户配置", "allowOut: pypi.org")]
    cw = (W - 2 * M) / 4
    for k, (a, b) in enumerate(parts):
        x = M + k * cw + 24
        s.text(x, T + 30, a, 13, MUTED)
        s.text(x, T + 56, b, 15, BAD[2] if k < 2 else INK, 600, mono=True)
    y = T + 110
    pw = (W - 2 * M - 40) / 2
    panels = [("如果代理连沙箱给的 IP", BAD, [("SNI pypi.org 在放行名单里", "判定：放行", KEY), ("连 203.0.113.66:443", "就是 /etc/hosts 里写的那个", BAD)],
               ("数据送到了攻击者的服务器", "“只允许 pypi.org”形同虚设")),
              ("E2B：按域名放行时连域名", GOOD, [("SNI pypi.org 在放行名单里", "判定：放行（按域名）", KEY),
                                           ("宿主机重新解析 pypi.org", "问宿主机的 DNS，得到 151.101.0.223", GOOD)],
               ("连到真正的 PyPI", "沙箱的 /etc/hosts、DNS 都影响不了目标"))]
    for i, (t, role, steps, (r1, r2)) in enumerate(panels):
        x = M + i * (pw + 40)
        s.rect(x, y, pw, 360, "#FCFBFA", HAIR, 1, rx=16)
        s.pill(x + 30 + (text_w(t, 15) + 22) / 2, y + 34, t, role, 15, solid=True, h=32)
        yy = y + 70
        for a, b, r in steps:
            box(s, x + 30, yy, pw - 60, 72, r, a, b, 15, 13)
            arrow(s, [(x + pw / 2, yy + 72), (x + pw / 2, yy + 92)], INK, 1.5)
            yy += 92
        box(s, x + 30, yy, pw - 60, 80, role, r1, r2, 16, 13)
    # 再防一层
    by = y + 390
    box(s, M, by, W - 2 * M, 82, ("#FFFFFF", NAT[1], INK), None, None, style="outline")
    s.text(M + 22, by + 32, "再防一层：解析结果不能是内网（防 DNS 重绑定）", 15.5, NAT[2], 600)
    s.text(M + 22, by + 60, "放行的域名如果被解析成 10.x、192.168.x、127.x、169.254.x 等预置拦截段的地址，代理在发起 TCP 连接之前就拒绝，"
                            "并记一条告警日志，连一个 SYN 都不会发往内网。", 13.5, SUB)
    yy = s.footer(by + 82 + 34, "注：按域名放行用的是宿主机的 DNS（本机 dnsmasq → 上游）。沙箱自己能解析、宿主机解析不了时，按域名放行的连接会失败，排障要两边都看。")
    save(s, "16-2-防绕过.svg", yy + 20)


# ------------------------------------------------------------------ 第 17 篇
def fig_17_entry():
    s = Svg()
    y0 = s.header("宿主机的入口：一个公网上不存在的域名，怎么落到本机 3002 端口",
                  "SDK 发出的请求分两类：控制请求直连 api 的 3000 端口；沙箱请求访问 http://49983-<沙箱ID>.e2b.app。"
                  "后者先由 dnsmasq 解析成 127.0.0.1，再由 iptables 把 80 端口改到 3002，交给 client-proxy。")
    T = y0 + 40
    SX1 = M + 210
    box(s, M, T, 210, 330, WHITE, "SDK", "跑在本机\n.env 里\nE2B_DOMAIN=e2b.app", 16, 12, style="outline")
    # 控制请求：最上面一行直连 api
    cy0 = T + 40
    arrow(s, [(SX1 + 2, cy0), (1010, cy0)], SUB, 1.6)
    s.text((SX1 + 1010) / 2, cy0 - 10, "控制请求：创建、销毁、暂停沙箱，构建模板", 13, SUB, 600, "middle")
    box(s, 1014, cy0 - 30, W - M - 1014, 60, KEY, "api :3000", None, 15)
    # 沙箱请求 ①：解析
    DX0, DX1 = 370, 860
    rb = T + 90
    s.rect(DX0, rb, DX1 - DX0, 150, "#FCFBFA", "#AEB6BE", 1.2, rx=12)
    s.text(DX0 + 18, rb + 28, "/etc/resolv.conf 第一行 nameserver 127.0.0.1 → dnsmasq", 13.5, INK, 600)
    for k, (a_, b_, role) in enumerate([("address=/.e2b.app/127.0.0.1", "A 记录：回答 127.0.0.1", NAT),
                                        ("local=/e2b.app/", "AAAA 等：立刻回答“没有”", NAT),
                                        ("server=/consul/127.0.0.1#8600", "*.consul 转给 Consul", KEY)]):
        yy = rb + 52 + k * 32
        s.text(DX0 + 18, yy + 14, a_, 12.5, role[2], 600, mono=True)
        s.text(DX0 + 290, yy + 14, b_, 12.5, SUB)
    arrow(s, [(SX1 + 2, rb + 75), (DX0 - 4, rb + 75)], INK, 1.6)
    s.text((SX1 + DX0) / 2, rb + 65, "① 解析域名", 12.5, INK, 600, "middle")
    # ② 连接 127.0.0.1:80
    cy = T + 300
    arrow(s, [(SX1 + 2, cy), (DX0 - 4, cy)], INK, 1.6)
    s.text((SX1 + DX0) / 2, cy - 10, "② 连 127.0.0.1:80", 12.5, INK, 600, "middle")
    box(s, DX0, cy - 34, DX1 - DX0, 68, NAT, "iptables nat OUTPUT", "-p tcp -o lo --dport 80 → REDIRECT 3002", 14.5, 12.5)
    arrow(s, [(DX1 + 4, cy), (1010, cy)], INK, 1.8)
    box(s, 1014, cy - 44, W - M - 1014, 88, GOOD, "client-proxy :3002", "按 Host 头找沙箱（第 18 篇）", 16, 13)
    # 外部机器
    ey = cy + 120
    box(s, M, ey - 52, 210, 104, WHITE, "别的机器上的 SDK", "自己把 *.e2b.app 解析到\n192.168.10.23，\n经物理网卡访问它的 80 端口", 15, 12, style="outline")
    arrow(s, [(SX1 + 2, ey), (DX0 - 4, ey)], INK, 1.6)
    box(s, DX0, ey - 34, DX1 - DX0, 68, NAT, "iptables nat PREROUTING", "-p tcp --dport 80 --dst-type LOCAL → REDIRECT 3002", 14.5, 12.5)
    arrow(s, [(DX1 + 4, ey), (940, ey), (940, cy + 22), (1010, cy + 22)], INK, 1.6)
    s.text(1014, ey + 6, "本机发出的包不经过 PREROUTING，所以两条规则都要有", 13, SUB)
    yy = s.footer(ey + 82, "注：DNS 只能给地址，不能给端口，所以要 iptables 改端口。这两条规则只在内存里，机器重启后要重新执行 build.sh -s。"
                           "SDK 默认用 https，build.sh -i 运行 patch_e2b.py 把它改成 http。别的机器上的 SDK 发控制请求时，同样直连 api 的 3000 端口，只是包从物理网卡进来（本篇 5.1 节）。")
    save(s, "17-1-宿主机入口.svg", yy + 20)


def fig_17_local():
    s = Svg()
    y0 = s.header("--dst-type LOCAL：只改道发给本机的 80 端口流量",
                  "最早的入口规则没有限制目的地址：任何从网卡进来、去往 80 端口的 TCP 都被改到 3002。它在部署时就加上，"
                  "排在所有槽位规则前面，于是截走了别人的流量，也截走了 E2B 沙箱访问 hyperloop 的请求。")
    T = y0 + 40
    LW = 420
    cw = (W - 2 * M - LW - 30) / 2
    cx = [M + LW, M + LW + cw + 30]
    heads = [("旧规则", "-p tcp --dport 80 -j REDIRECT --to-port 3002", BAD), ("新规则", "… --dport 80 -m addrtype --dst-type LOCAL …", GOOD)]
    for x, (t, sub, role) in zip(cx, heads):
        s.rect(x, T, cw, 64, role[0], role[1], 1.4, rx=10)
        s.text(x + cw / 2, T + 28, t, 17, role[2], 600, "middle")
        s.text(x + cw / 2, T + 50, sub, 12, SUB, 400, "middle", mono=True)
    rows = [("别的机器访问本机 IP 的 80 端口", "目的是本机", [("改到 3002", "ok", "本来就该这样"), ("改到 3002", "ok", "目的是本机，照常改道")]),
            ("AgentENV、Docker 容器访问外网 http 网站", "路过宿主机，被转发", [("被截到 client-proxy", "bad", "别人的流量出不去"),
                                                            ("不改道", "ok", "目的不是本机，正常转发")]),
            ("E2B 沙箱访问 192.0.2.1:80（hyperloop）", "槽位规则加在链尾，排在后面",
             [("被截到 client-proxy", "bad", "invalid host 日志：16 个沙箱两小时约 9 GB"),
              ("不改道", "ok", "192.0.2.1 不是本机地址，留给后面的槽位规则 → 5010")])]
    y = T + 84
    for k, (a, b, cells) in enumerate(rows):
        rh = 96
        if k % 2 == 0:
            s.rect(M, y, W - 2 * M, rh, "#F7F8FA", "none", 0, rx=10)
        s.text(M + 18, y + 40, a, 15, INK, 600)
        s.text(M + 18, y + 64, b, 13, SUB)
        for x, (res, kind, note) in zip(cx, cells):
            role = GOOD if kind == "ok" else BAD
            s.rect(x + 16, y + 16, cw - 32, rh - 32, "#FFFFFF", role[1], 1.2, rx=9)
            s.text(x + 34, y + 44, res, 15, role[2], 600)
            s.text(x + 34, y + 66, note, 12.5, SUB)
        y += rh + 8
    yy = s.footer(y + 26, "注：部署脚本会先把不带 --dst-type LOCAL 的老规则循环删干净，再加新规则，避免升级后新旧并存。"
                          "本机程序访问 127.0.0.1:80 由另一条 OUTPUT -o lo 规则处理。")
    save(s, "17-2-dst-type-LOCAL.svg", yy + 20)


# ------------------------------------------------------------------ 第 18 篇
def fig_18_path():
    s = Svg()
    y0 = s.header("从 SDK 到 envd：一次沙箱请求的八跳",
                  "SDK 执行 sbx.commands.run(\"whoami\")。前三跳把请求送到本机 3002（第 17 篇）；中间两层代理先找节点、再找 Host IP；"
                  "最后三跳和第 13 篇的“宿主机连沙箱”一样。响应沿原路返回。")
    T = y0 + 40
    n = 4
    gap = 40
    bw = (W - 2 * M - (n - 1) * gap) / n
    row1 = [("① SDK", "http://49983-<ID>.e2b.app/…", WHITE), ("② dnsmasq", "*.e2b.app → 127.0.0.1", WHITE),
            ("③ iptables OUTPUT", "127.0.0.1:80 → :3002", NAT), ("④ client-proxy :3002", "从 Host 头取端口和沙箱 ID；查目录得到节点 IP", GOOD)]
    row2 = [("⑤ orchestrator 代理 :5007", "再解析一次 Host；在内存里找到沙箱的 Host IP；校验流量令牌；失败最多重试 5 次", GOOD),
            ("⑥ 宿主机路由", "10.13.0.5 via 10.14.0.11 dev e2bv-5", HOST), ("⑦ ns-5 DNAT", "10.13.0.5 → 169.254.0.21", NAT),
            ("⑧ envd :49983", "tap0 → Firecracker → 客户机；envd 用 MMDS 里的哈希校验令牌", VM)]
    h = 108
    for k, (t, sub, role) in enumerate(row1):
        x = M + k * (bw + gap)
        box(s, x, T, bw, h, role, t, sub, 15, 12.5, style="outline" if role is WHITE else "fill")
        if k < n - 1:
            arrow(s, [(x + bw + 4, T + h / 2), (x + bw + gap - 4, T + h / 2)], INK, 1.7)
    y2 = T + h + 70
    for k, (t, sub, role) in enumerate(row2):
        x = M + (n - 1 - k) * (bw + gap)
        box(s, x, y2, bw, h, role, t, sub, 15, 12.5)
        if k < n - 1:
            arrow(s, [(x - 4, y2 + h / 2), (x - gap + 4, y2 + h / 2)], INK, 1.7)
    xr = M + (n - 1) * (bw + gap) + bw / 2
    arrow(s, [(xr, T + h + 2), (xr, y2 - 4)], INK, 1.7, label="转发到节点 IP:5007，Host 头不变", ldx=-12, lanchor="end", ldy=4)
    # Host 头解析
    py = y2 + h + 50
    s.text(M, py, "两层代理都这样解析 Host 头", 16, INK, 600)
    hx = M
    hy = py + 24
    s.rect(hx, hy, W - 2 * M, 96, "#FCFBFA", HAIR, 1, rx=12)
    s.text(hx + 24, hy + 40, "Host:", 16, MUTED, 400, mono=True)
    x = hx + 100
    for t, role in [("49983", NAT), ("-", None), ("i2k5fx3h0qa9z1m7", NS), (".e2b.app", None)]:
        w = len(t) * 16 * 0.61
        if role:
            s.rect(x - 4, hy + 18, w + 8, 32, role[0], role[1], 1.2, rx=6)
        s.text(x, hy + 40, t, 16, role[2] if role else INK, 700 if role else 400, mono=True)
        if role:
            s.text(x + w / 2, hy + 76, "端口" if role is NAT else "沙箱 ID", 13, role[2], 600, "middle")
        x += w + (8 if role else 2)
    s.text(x + 60, hy + 40, "取第一个点之前的部分，按 - 切开", 14, SUB)
    s.text(x + 60, hy + 66, "也可以用请求头 E2b-Sandbox-Id / E2b-Sandbox-Port 指定", 13, MUTED)
    yy = s.footer(hy + 96 + 34, "注：两层代理是为多节点设计的：client-proxy 是集群入口，只负责找到沙箱在哪个节点（Redis 里的沙箱目录）；"
                                "orchestrator 代理是节点入口，只有它知道本机沙箱的 Host IP。单机部署时两层在同一台机器上。")
    save(s, "18-1-SDK到envd.svg", yy + 20)


def fig_18_pool():
    s = Svg()
    y0 = s.header("连接池为什么按生命周期 ID 分组：Host IP 会换主人",
                  "槽位 5 先给沙箱 A 用，A 结束后给了沙箱 B，Host IP 都是 10.13.0.5。连接池如果按目标地址分组，"
                  "发给 B 的请求可能拿到当初连 A 的旧连接。")
    T = y0 + 40
    X0, X1 = 300, W - M
    # 时间轴：槽位 5 的主人
    s.text(M, T + 30, "槽位 5", 15, INK, 600)
    s.text(M, T + 50, "Host IP 10.13.0.5", 12.5, SUB, 400, mono=True)
    mid = (X0 + X1) / 2
    s.rect(X0, T + 14, mid - X0 - 30, 40, VM[0], VM[1], 1.2, rx=8)
    s.text((X0 + mid - 30) / 2, T + 40, "沙箱 A（LifecycleID = a1）", 14, VM[2], 600, "middle")
    s.rect(mid + 30, T + 14, X1 - mid - 30, 40, NS[0], NS[1], 1.2, rx=8)
    s.text((mid + 30 + X1) / 2, T + 40, "沙箱 B（LifecycleID = b7）", 14, NS[2], 600, "middle")
    s.line(mid, T + 4, mid, T + 400, MUTED, 1.2, dash="4 4")
    s.text(mid, T + 420, "A 结束，槽位 5 归还后分给 B", 13, MUTED, 400, "middle")
    rows = [("按目标地址分组", "键：10.13.0.5:49983", BAD,
             ("建连接 c1，用完放回池子", "键 10.13.0.5:49983"), ("从池子里取到 c1", "两端状态对不上：请求失败，甚至被错误的对象处理")),
            ("按生命周期 ID 分组（E2B）", "键：沙箱实例的 LifecycleID", GOOD,
             ("建连接 c1，键 a1", "只给沙箱 A 用"), ("键 b7 下没有连接，新建 c2", "A 的连接绝不会被 B 拿到"))]
    y = T + 90
    for t, sub, role, (a1, a2), (b1, b2) in rows:
        s.text(M, y + 40, t, 15, role[2], 600)
        s.text(M, y + 62, sub, 12.5, SUB)
        box(s, X0, y, mid - X0 - 30, 96, WHITE, a1, a2, 14.5, 12.5, style="outline")
        box(s, mid + 30, y, X1 - mid - 30, 96, role, b1, b2, 14.5, 12.5)
        y += 136
    yy = s.footer(T + 446, "注：也不用沙箱 ID 分组：沙箱暂停再恢复后 ID 不变，但已是新实例，可能落在别的槽位。"
                           "此外 orchestrator 代理到沙箱的连接关闭了 keep-alive：沙箱里的服务随时可能重启，同机新建连接的开销又很小。")
    save(s, "18-2-连接池.svg", yy + 20)


# ------------------------------------------------------------------ 第 19 篇
def fig_19_chain():
    s = Svg()
    y0 = s.header("宿主机的 nat PREROUTING 链：从上往下，命中即停",
                  "槽位 5 的六条 REDIRECT 加在链尾，前面还有一条全局入口规则。三个沙箱发出的 TCP 包依次往下比，"
                  "命中第一条就停。宿主服务的三条排在防火墙代理的三条前面，所以 192.0.2.1:80 不会被 5016 截走。")
    T = y0 + 36
    RW = 640
    cw = (W - 2 * M - RW - 3 * 16) / 3
    cx = [M + RW + 16 + i * (cw + 16) for i in range(3)]
    pk = [("192.0.2.1:80", "events.e2b.local/me"), ("151.101.0.223:443", "pip 连 pypi.org"), ("203.0.113.9:22", "ssh 到外部主机")]
    for x, (a, b) in zip(cx, pk):
        s.rect(x, T, cw, 60, "#FCFBFA", "#AEB6BE", 1.2, rx=10)
        s.text(x + cw / 2, T + 26, a, 14.5, INK, 700, "middle", mono=True)
        s.text(x + cw / 2, T + 46, b, 12.5, SUB, 400, "middle")
    s.text(M, T + 26, "沙箱发出的 TCP 包，目的是", 14, SUB)
    rules = [("全局", "--dport 80 --dst-type LOCAL", "3002", "入口"),
             ("槽位 5", "-d 192.0.2.1 --dport 80", "5010", "hyperloop"),
             ("槽位 5", "-d 192.0.2.1 --dport 111", "5012", "portmap"),
             ("槽位 5", "-d 192.0.2.1 --dport 2049", "5011", "NFS 代理"),
             ("槽位 5", "--dport 80", "5016", "防火墙代理 HTTP"),
             ("槽位 5", "--dport 443", "5017", "防火墙代理 TLS"),
             ("槽位 5", "（其他 TCP）", "5018", "防火墙代理 其他")]
    hit = [1, 5, 6]
    notes = {(0, 0): "192.0.2.1 不是本机地址", (0, 1): "目的不是本机", (0, 2): "目的不是本机"}
    y = T + 76
    rh = 52
    for k, (scope, m, port, svc) in enumerate(rules):
        if k % 2 == 0:
            s.rect(M, y, W - 2 * M, rh, "#F7F8FA", "none", 0, rx=8)
        s.text(M + 14, y + 22, scope, 12, MUTED, 600)
        s.text(M + 14, y + 42, ("-i e2bv-5 " if scope != "全局" else "") + "-p tcp", 12, SUB, 400, mono=True)
        s.text(M + 190, y + 32, m, 13.5, INK, 600, mono=True)
        s.text(M + 450, y + 32, f"→ {port}", 13.5, NAT[2], 700, mono=True)
        s.text(M + 520, y + 32, svc, 13, SUB)
        for i in range(3):
            x = cx[i]
            if k < hit[i]:
                s.text(x + cw / 2, y + 32, notes.get((k, i), "不匹配"), 12.5, MUTED, 400, "middle")
            elif k == hit[i]:
                s.rect(x + 8, y + 8, cw - 16, rh - 16, NAT[0], NAT[1], 1.4, rx=8)
                s.text(x + cw / 2, y + 32, f"命中 → {svc}", 13.5, NAT[2], 700, "middle")
            else:
                s.text(x + cw / 2, y + 32, "—", 13, "#C9D1D9", 400, "middle")
        y += rh + 4
    by = y + 20
    box(s, M, by, W - 2 * M, 82, ("#FFFFFF", NS[1], INK), None, None, style="outline")
    s.text(M + 22, by + 32, "第一个包能走到这里，前面还有两关", 15, NS[2], 600)
    s.text(M + 22, by + 60, "ns-5 里 nftables 规则 2 放行 192.0.2.1（发往私有地址的包在规则 3 就被丢了），再 SNAT 成 10.13.0.5；"
                            "宿主服务据此认出是哪个沙箱。只有这三个 TCP 端口有改道，访问 192.0.2.1 的其他端口或 UDP 都无果。", 13.5, SUB)
    yy = s.footer(by + 82 + 34, "注：真实链里每个槽位各有六条，全都加在链尾；全局入口规则在部署时就加上，排在最前。"
                               "它要是没有 --dst-type LOCAL，第一列的包就会在第一行被截到 3002（第 17 篇）。")
    save(s, "19-1-PREROUTING链.svg", yy + 20)


if __name__ == "__main__":
    fig_15_rules()
    fig_15_config()
    fig_16_proxy()
    fig_16_bypass()
    fig_17_entry()
    fig_17_local()
    fig_18_path()
    fig_18_pool()
    fig_19_chain()
