"""《E2B 模板构建、沙箱启动与暂停恢复从零讲透》第 1～4 篇的配图。用法: python3 tools/figures/lc_p1.py"""
from lc_common import *  # noqa: F401,F403
from lc_common import W, M


# ------------------------------------------------------------------ 第 1 篇
def fig_01_life():
    s = Svg()
    y0 = s.header("一个沙箱的一生",
                  "模板只构建一次；之后每台沙箱都从它启动。运行中可以暂停离场，以后再恢复；最后销毁。"
                  "本书详讲其中三个操作：构建模板、启动沙箱、暂停与恢复。")
    T = y0 + 40
    items = [
        (CTL, "1. 构建模板", "Template.build\n只做一次"),
        (OK, "2. 启动沙箱", "Sandbox.create\n一百多毫秒"),
        (WHITE, "3. 运行", "commands.run\n读写文件"),
        (CTL, "4. 暂停", "pause()\n存盘并离场"),
        (OK, "5. 恢复", "Sandbox.connect\n读盘重建"),
        (WHITE, "6. 销毁", "kill()"),
    ]
    boxes = flow_h(s, M, T, W - 2 * M, items, h=110, gap=40, ts=16, ss=13)
    # 回环：恢复后又能运行
    x5 = boxes[4][0] + boxes[4][2] / 2
    x3 = boxes[2][0] + boxes[2][2] / 2
    yb = T + 110 + 50
    arrow(s, [(x5, T + 114), (x5, yb), (x3, yb), (x3, T + 114)], MUTED, 1.4, dash="5 4")
    s.text((x3 + x5) / 2, yb + 24, "恢复后接着运行，可以再次暂停", 13, SUB, 400, "middle")
    # 标注本书范围
    yy = yb + 70
    for i in (0, 1, 3, 4):
        bx, by, bw, bh = boxes[i]
        s.pill(bx + bw / 2, yy, "本书详讲", OK, 12.5)
    s.text(boxes[2][0] + boxes[2][2] / 2, yy + 4, "按需提到", 12.5, MUTED, 400, "middle")
    s.text(boxes[5][0] + boxes[5][2] / 2, yy + 4, "按需提到", 12.5, MUTED, 400, "middle")
    f = s.footer(yy + 40, "类比：构建 = 做模具；启动 = 用模具铸一个零件；暂停与恢复 = 存盘离场、改天读盘。")
    save(s, "01-1-一生.svg", f + 20)


def fig_01_cycle():
    s = Svg()
    y0 = s.header("一切皆快照：三个操作首尾相接",
                  "构建的终点是拍一张快照；启动从这张快照恢复；暂停在当前状态上再拍一张；恢复又从那一张恢复。"
                  "构建本身也在这个圈里反复转：每条指令都是“恢复—执行—暂停”。")
    T = y0 + 40
    cx, cy = W / 2, T + 230
    snap = (cx - 150, cy - 55, 300, 110)
    box(s, *snap, STO, "快照", "snapfile + memfile + rootfs\n+ 映射表", 18, 13)
    pos = {
        "build": (cx - 640, cy - 190, 360, 100),
        "start": (cx + 280, cy - 190, 360, 100),
        "pause": (cx + 280, cy + 90, 360, 100),
        "resume": (cx - 640, cy + 90, 360, 100),
    }
    box(s, *pos["build"], CTL, "构建模板", "开机、装软件、跑启动命令，就绪那一刻拍快照", 16, 12.5)
    box(s, *pos["start"], OK, "启动沙箱", "把模板快照加载进新的 Firecracker", 16, 12.5)
    box(s, *pos["pause"], CTL, "暂停", "只存改过的部分，长出新的一代", 16, 12.5)
    box(s, *pos["resume"], OK, "恢复", "从暂停那一代加载，和启动同一条路", 16, 12.5)
    b, st, p, r = pos["build"], pos["start"], pos["pause"], pos["resume"]
    arrow(s, [(b[0] + b[2] + 4, b[1] + 50), (snap[0] + 40, b[1] + 50), (snap[0] + 40, snap[1] - 4)], INK, 1.6, label="拍下", ldx=-30)
    arrow(s, [(snap[0] + snap[2] - 40, snap[1] - 4), (snap[0] + snap[2] - 40, st[1] + 50), (st[0] - 4, st[1] + 50)], INK, 1.6)
    s.text(snap[0] + snap[2] + 10, st[1] + 40, "读", 13, SUB, 600)
    arrow(s, [(st[0] + 180, st[1] + st[3] + 4), (p[0] + 180, p[1] - 4)], INK, 1.6, label="运行一段时间", ldx=70, ldy=4)
    arrow(s, [(p[0] - 4, p[1] + 50), (snap[0] + snap[2] - 40, p[1] + 50), (snap[0] + snap[2] - 40, snap[1] + snap[3] + 4)], INK, 1.6)
    s.text(snap[0] + snap[2] + 10, p[1] + 72, "拍下新一代", 13, SUB, 600)
    arrow(s, [(snap[0] + 40, snap[1] + snap[3] + 4), (snap[0] + 40, r[1] + 50), (r[0] + r[2] + 4, r[1] + 50)], INK, 1.6)
    s.text(snap[0] - 10, r[1] + 72, "读", 13, SUB, 600, "end")
    # 构建内部小循环
    yy = cy + 230
    band(s, M, yy, W - 2 * M, 110, KEY, "构建内部也在转圈")
    flow_h(s, M + 300, yy + 26, W - 2 * M - 330, [(WHITE, "从上一层恢复", None), (WHITE, "执行一条指令", None),
                                                  (WHITE, "暂停成新一层", None)], h=56, gap=60, ts=14.5)
    f = s.footer(yy + 140, "三个操作共用同一套部件：Firecracker、内存懒加载、磁盘写层、映射表。")
    save(s, "01-2-一切皆快照.svg", f + 20)


def fig_01_map():
    s = Svg()
    y0 = s.header("全书地图：五个部分与三类修改",
                  "左边是五个部分；右边是我们对上游 E2B 的三类修改，标出它们主要落在哪几篇。")
    T = y0 + 36
    parts = [
        ("一、先打底", "第 1～4 篇", "沙箱组成 · 页、缺页、块设备、命名空间 · 快照三件套与映射表"),
        ("二、构建模板", "第 5～9 篇", "流水线五阶段 · base · 指令与缓存 · finalize 与 optimize · 搬到 ARM"),
        ("三、启动沙箱", "第 10～15 篇", "启动就是恢复 · 拉起 Firecracker · 内存 · 磁盘网络 envd · 测量 · 优化"),
        ("四、暂停与恢复", "第 16～20 篇", "暂停六步 · 增量与成本 · 恢复 · ARM 上读即脏 · 精确增量"),
        ("五、和快照回滚共存", "第 21～23 篇", "共用部件 · 三处被撞坏 · 全景与修改清单"),
    ]
    LW = 960
    y = T
    for t, ref, sub in parts:
        box(s, M, y, LW, 74, WHITE, None, None)
        s.text(M + 20, y + 32, t, 17, INK, 600)
        tag(s, M + 20, y + 44, ref)
        s.text(M + 250, y + 44, sub, 13.5, SUB)
        y += 88
    rx = M + LW + 50
    rw = W - M - rx
    mods = [
        (FCR, "搬到 ARM", "镜像架构、busybox、发行版脚本、cgroup、内核参数、uffd 写保护", "第 9、11、19 篇"),
        (OK, "更快、更稳", "netns-exec、并发参数、超时、网络池、精确增量、埋点", "第 14、15、20 篇"),
        (CTL, "和快照回滚共存", "跟踪开关、压平层导出、累积位图、路由头、兼容矩阵", "第 21、22 篇"),
    ]
    yy = T
    for role, t, sub, ref in mods:
        box(s, rx, yy, rw, 132, role, t, sub, 16, 13)
        tag(s, rx + rw - 14, yy + 10, ref, "end")
        yy += 146
    f = s.footer(max(y, yy) + 10, "每处修改都按同一顺序讲：原来怎样 → 出了什么问题 → 改成了什么 → 改对了的证据。")
    save(s, "01-3-全书地图.svg", f + 20)


# ------------------------------------------------------------------ 第 2 篇
def fig_02_parts():
    s = Svg()
    y0 = s.header("一台沙箱的组成：虚拟机里四样，宿主上五样",
                  "虚拟机里是内核、根文件系统、systemd 和 envd；宿主为它准备 Firecracker 进程和四样家当。"
                  "启动就是把这五样准备好再加载快照，暂停反过来把它们拆掉。")
    T = y0 + 36
    fw = 620
    band(s, M, T, fw, 420, FCR, "Firecracker 进程")
    band(s, M + 24, T + 70, fw - 48, 330, GST, "虚拟机（guest）")
    gi = [("Linux 内核", "E2B 编译的精简内核"), ("根文件系统 rootfs", "ext4：发行版 + 用户软件"),
          ("systemd", "1 号进程"), ("envd（49983）", "唯一的管家：跑命令、读写文件")]
    y = T + 130
    for t, sub in gi:
        box(s, M + 48, y, fw - 96, 58, white(GST), t, sub, 14.5, 12.5)
        y += 66
    rx = M + fw + 80
    rw = W - M - rx
    band(s, rx, T, rw, 420, STO, "宿主为它准备的四样家当")
    hh = [("网络槽位", "网络命名空间 + tap + veth + iptables", "第 13 篇"),
          ("根盘", "NBD 设备：模板只读层 + 本沙箱写层", "第 13 篇"),
          ("内存处理器", "userfaultfd：用到哪页补哪页", "第 12 篇"),
          ("cgroup", "资源统计与限制", "第 12、15 篇")]
    y = T + 70
    for t, sub, ref in hh:
        box(s, rx + 24, y, rw - 48, 74, WHITE, t, sub, 15, 12.5)
        tag(s, rx + rw - 36, y + 8, ref, "end")
        y += 84
    for yy in (T + 105, T + 190, T + 275):
        arrow(s, [(rx - 4, yy + 40), (M + fw + 4, yy + 40)], MUTED, 1.3, dash="4 4")
    f = s.footer(T + 450, "合计五样：Firecracker 进程 + 网络槽位、根盘、内存处理器、cgroup。")
    save(s, "02-1-沙箱组成.svg", f + 20)


def fig_02_services():
    s = Svg()
    y0 = s.header("宿主侧服务全景（单节点部署）",
                  "api 接请求、记账、选节点；orchestrator 真正管沙箱；template-manager 构建模板，单节点部署里它和 orchestrator 是同一个进程；"
                  "client-proxy 转发用户访问沙箱的流量。")
    T = y0 + 36
    box(s, M, T + 120, 200, 80, CTL, "SDK", "用户代码", 16, 12.5)
    box(s, M + 270, T + 40, 260, 90, CTL, "api", "认证、记账、模板版本、选节点", 16, 12.5)
    box(s, M + 270, T + 200, 260, 90, CTL, "client-proxy", "按沙箱 ID 转发", 16, 12.5)
    ox = M + 610
    ow = 560
    band(s, ox, T, ow, 380, CTL, "一个进程（单节点部署）")
    box(s, ox + 24, T + 60, ow - 48, 70, white(CTL), "orchestrator", "启动、暂停、恢复、销毁沙箱 · 内置代理 5007", 15, 12.5)
    box(s, ox + 24, T + 145, ow - 48, 70, white(CTL), "template-manager", "构建模板：开构建虚拟机、执行指令、打快照", 15, 12.5)
    box(s, ox + 24, T + 230, ow - 48, 120, STO, "共享", "同一套 Firecracker、网络槽位池、本地缓存、内存上限", 15, 12.5)
    sx = ox + ow + 60
    sw = W - M - sx
    box(s, sx, T, sw, 110, FCR, "沙箱们", "每台一个 Firecracker 进程", 15, 12.5)
    box(s, sx, T + 135, sw, 110, STO, "存储", "本地目录或 MinIO：模板与快照", 15, 12.5)
    box(s, sx, T + 270, sw, 110, STO, "数据库 · Redis", "模板版本、沙箱记录、路由表", 15, 12.5)
    arrow(s, [(M + 204, T + 150), (M + 266, T + 90)], INK, 1.5)
    arrow(s, [(M + 204, T + 170), (M + 266, T + 240)], INK, 1.5)
    arrow(s, [(M + 534, T + 85), (ox - 4, T + 85)], INK, 1.5, label="gRPC 5008", ldy=-10)
    arrow(s, [(M + 534, T + 245), (ox - 4, T + 245)], INK, 1.5, label="HTTP 5007", ldy=-10)
    arrow(s, [(ox + ow + 4, T + 95), (sx - 4, T + 55)], INK, 1.5)
    arrow(s, [(ox + ow + 4, T + 180), (sx - 4, T + 190)], MUTED, 1.4)
    f = s.footer(T + 410, "官方的大规模部署把这些服务分到不同机器池；我们的部署全部在一台机器上。")
    save(s, "02-2-服务全景.svg", f + 20)


def fig_02_planes():
    s = Svg()
    y0 = s.header("控制面与数据面：两条不同的路",
                  "创建、暂停、恢复、销毁走控制面，要认证、要记账；跑命令、读写文件走数据面，只做转发，要求延迟低。"
                  "本书的三个操作都走控制面。")
    T = y0 + 40
    s.text(M, T + 10, "控制面", 18, CTL[2], 600)
    flow_h(s, M, T + 30, W - 2 * M, [(CTL, "SDK", "Sandbox.create / pause / connect"), (CTL, "api", "认证 · 记账 · 选节点"),
                                     (CTL, "orchestrator", "Create / Pause RPC"), (FCR, "Firecracker", "HTTP 接口（Unix 套接字）")],
           h=90, gap=60, labels=["HTTPS", "gRPC", "HTTP"])
    T2 = T + 180
    s.text(M, T2 + 10, "数据面", 18, OK[2], 600)
    flow_h(s, M, T2 + 30, W - 2 * M, [(CTL, "SDK", "commands.run / files.read"), (CTL, "client-proxy", "按地址里的沙箱 ID 查路由"),
                                      (CTL, "orchestrator 代理", "送进沙箱网络"), (GST, "envd", "49983 端口")],
           h=90, gap=60, labels=["HTTPS", "", ""])
    s.text(M, T2 + 160, "地址形如 49983-<沙箱ID>.<域名>：沙箱 ID 就在地址里，不需要额外的请求头。", 13.5, SUB)
    f = s.footer(T2 + 190, "两处交叉：启动的最后要确认 envd 能应答；恢复后的沙箱少带两个路由头，数据面上按请求头路由的服务不通（第 18 篇）。")
    save(s, "02-3-控制面与数据面.svg", f + 20)


# ------------------------------------------------------------------ 第 3 篇
def fig_03_pages():
    s = Svg()
    y0 = s.header("页、大页与页表",
                  "同样 2 MiB 的数据：4 KiB 小页要 512 个页表项，2 MiB 大页只要 1 个。TLB 只能缓存有限的表项，大页让它覆盖的范围扩大 512 倍。"
                  "代价是一次读、补、存都至少 2 MiB。")
    T = y0 + 40
    lw = (W - 2 * M - 80) / 2
    band(s, M, T, lw, 300, KEY, "4 KiB 小页")
    n = 32
    cw = (lw - 48) / n
    for i in range(n):
        s.rect(M + 24 + i * cw, T + 80, cw - 2, 60, GST[0], GST[1], 1, rx=2)
    s.text(M + 24, T + 170, "2 MiB = 512 页（图中只画 32 格示意）", 13.5, SUB)
    s.text(M + 24, T + 205, "页表项：512 个", 15, INK, 600)
    s.text(M + 24, T + 235, "TLB 很快装不下，查表变多", 13.5, RISK[2])
    s.text(M + 24, T + 265, "缺页时一次补 4 KiB", 13.5, SUB)
    rx = M + lw + 80
    band(s, rx, T, lw, 300, KEY, "2 MiB 大页")
    s.rect(rx + 24, T + 80, lw - 48, 60, GST[0], GST[1], 1.2, rx=4)
    s.text(rx + lw / 2, T + 116, "一整页 2 MiB", 15, GST[2], 600, "middle")
    s.text(rx + 24, T + 205, "页表项：1 个", 15, INK, 600)
    s.text(rx + 24, T + 235, "TLB 覆盖范围大 512 倍，运行更快", 13.5, OK[2])
    s.text(rx + 24, T + 265, "缺页时一次补 2 MiB：读、补、存都按 2 MiB", 13.5, RISK[2])
    f = s.footer(T + 330, "E2B 沙箱的内存默认由 2 MiB 大页背衬（hugetlbfs），大页池在宿主上提前预留。")
    save(s, "03-1-页与大页.svg", f + 20)


def fig_03_uffd():
    s = Svg()
    y0 = s.header("缺页与 userfaultfd：让一个普通程序来补页",
                  "登记过 uffd 的内存发生缺页时，内核不自己处理，而是挂起访问它的线程，通知登记的程序；"
                  "程序自己找到内容，用 UFFDIO_COPY 填进去，内核再唤醒线程重做那次访问。")
    T = y0 + 40
    cols = [(GST, "guest 里的程序"), (FCR, "内核 / KVM"), (CTL, "uffd 处理程序（orchestrator）"), (STO, "内容来源")]
    cw = (W - 2 * M) / 4
    for i, (role, t) in enumerate(cols):
        x = M + i * cw + cw / 2
        s.pill(x, T + 10, t, role, 14)
        s.line(x, T + 30, x, T + 420, HAIR, 1.4, dash="4 4")
    xs = [M + i * cw + cw / 2 for i in range(4)]
    msgs = [
        (0, 1, T + 70, "1. 访问地址 X，这一页还没有内容"),
        (1, 1, T + 120, "2. 挂起这个线程"),
        (1, 2, T + 170, "3. 通知：地址 X 缺页了"),
        (2, 3, T + 220, "4. 查映射表，读快照文件"),
        (3, 2, T + 270, "5. 拿到这一页的内容"),
        (2, 1, T + 320, "6. UFFDIO_COPY 填进去"),
        (1, 0, T + 370, "7. 唤醒线程，重做那次访问，成功"),
    ]
    for a, b, y, t in msgs:
        if a == b:
            s.rect(xs[a] - 140, y - 18, 280, 30, FCR[0], FCR[1], 1, rx=6)
            s.text(xs[a], y + 2, t, 13.5, FCR[2], 600, "middle")
        else:
            arrow(s, [(xs[a], y), (xs[b], y)], INK, 1.5)
            s.text((xs[a] + xs[b]) / 2, y - 9, t, 13.5, INK, 600, "middle")
    f = s.footer(T + 450, "可选的“写保护”：填页时保持只读，之后第一次写会再通知一次。上游靠它判断哪些页被写过；ARM 内核上没有这个功能（第 19 篇）。")
    save(s, "03-2-缺页与uffd.svg", f + 20)


def fig_03_cow():
    s = Svg()
    y0 = s.header("写时复制的磁盘：只读底层 + 各自写层",
                  "几百台沙箱共享同一份只读的模板磁盘，每台上面叠一个自己的写层。写只进写层；读先查写层，没有再往下读模板。"
                  "启动不用复制任何磁盘数据。")
    T = y0 + 40
    n = 3
    gw = (W - 2 * M - 2 * 40) / n
    for i in range(n):
        x = M + i * (gw + 40)
        box(s, x, T, gw, 70, GST, f"沙箱 {i + 1} 看到的磁盘", "/dev/vda", 15, 12.5)
        box(s, x, T + 100, gw, 80, STO, f"写层 {i + 1}", ["只有块 3、7", "只有块 12", "空的"][i], 15, 12.5)
        arrow(s, [(x + gw / 2, T + 74), (x + gw / 2, T + 96)], INK, 1.4)
        arrow(s, [(x + gw / 2, T + 184), (x + gw / 2, T + 226)], MUTED, 1.4, dash="4 4", label="写层里没有才往下", ldx=70, ldy=26)
    box(s, M, T + 230, W - 2 * M, 80, KEY, "模板磁盘（只读，所有沙箱共享）", "按映射表可读到任意一块", 16, 13)
    yy = T + 350
    bullets(s, M, yy, ["写：只写进自己的写层", "读：写层里有就用写层的，没有就读模板",
                       "暂停时导出的磁盘增量，就是写层里那些块（第 17 篇）"], 14.5, 32)
    f = s.footer(yy + 100, "E2B 用 NBD 把这套规则呈现成一块普通的块设备，orchestrator 当它背后的服务端（第 13 篇）。")
    save(s, "03-3-写时复制.svg", f + 20)


def fig_03_ns():
    s = Svg()
    y0 = s.header("命名空间：同一台宿主上，每台沙箱看到自己的一套",
                  "网络命名空间隔离网卡、IP、路由；挂载命名空间隔离“路径指向哪里”。"
                  "所以一千台沙箱可以有同名的网卡、相同的内部 IP、同一个路径指向不同的文件。")
    T = y0 + 40
    n = 3
    gw = (W - 2 * M - 2 * 40) / n
    for i in range(n):
        x = M + i * (gw + 40)
        band(s, x, T, gw, 260, CTL, f"沙箱 {i + 1}")
        box(s, x + 20, T + 60, gw - 40, 80, STO, "网络命名空间 ns-" + str(i + 1), "tap0 · 内部 IP 相同", 14.5, 12.5)
        box(s, x + 20, T + 155, gw - 40, 80, STO, "挂载命名空间", "/fc-vm/rootfs.ext4 → 本沙箱的盘", 14.5, 12.5)
    box(s, M, T + 300, W - 2 * M, 70, KEY, "宿主内核：创建、切换命名空间要动全局数据结构", "平时很快；几百个同时做，会在一把全局锁上排队（第 15 篇）", 15, 12.5)
    f = s.footer(T + 400, "第 11 篇讲挂载命名空间怎样解决“快照录死了路径”的问题；第 13 篇讲网络槽位。")
    save(s, "03-4-命名空间.svg", f + 20)


# ------------------------------------------------------------------ 第 4 篇
def fig_04_three():
    s = Svg()
    y0 = s.header("快照三件套：同一时刻的 CPU、内存、磁盘",
                  "先暂停 vCPU，再分别存三样；三样必须是同一时刻的。Firecracker 只写 snapfile，内存和磁盘由 orchestrator 自己导出、自己管。")
    T = y0 + 40
    cw = (W - 2 * M - 2 * 40) / 3
    items = [
        (FCR, "snapfile", "vCPU 寄存器、中断控制器、设备状态", "几十 KB 到几 MB", "Firecracker 写"),
        (GST, "memfile", "内核、进程的代码和数据、文件缓存", "最多等于内存大小，只存用到的", "orchestrator 从进程里读出"),
        (STO, "rootfs.ext4", "根文件系统", "磁盘大小，只存改过的", "orchestrator 从写层导出"),
    ]
    for i, (role, t, sub, size, who) in enumerate(items):
        x = M + i * (cw + 40)
        box(s, x, T, cw, 140, role, t, sub, 20, 13.5)
        s.text(x + 10, T + 175, "大小：" + size, 13.5, SUB)
        s.text(x + 10, T + 205, "谁写：" + who, 13.5, INK, 600)
    box(s, M, T + 240, W - 2 * M, 60, KEY, None, "每一代还有：memfile.header、rootfs.ext4.header（映射表）和 metadata.json（版本、内核、启动命令、预取表）", 15, 13.5)
    f = s.footer(T + 330, "为什么内存和磁盘不交给 Firecracker：要能按需取、要能增量拼链、要能上传搬走。")
    save(s, "04-1-快照三件套.svg", f + 20)


def fig_04_header():
    s = Svg()
    y0 = s.header("映射表：一块数据在哪一代、哪个偏移",
                  "数据文件只是紧凑地首尾相接的块；映射表按设备地址排序、完整覆盖整个设备，每一行说“这一段在第几代的文件里、从哪个偏移开始”。")
    T = y0 + 40
    # 设备条
    segs = [(0, 4, "第 1 代", WHITE), (4, 2, "第 3 代", OK), (6, 4, "第 2 代", CTL), (10, 6, "第 1 代", WHITE)]
    unit = (W - 2 * M) / 16
    s.text(M, T, "设备（内存或磁盘），单位 MiB", 14, SUB)
    for off, ln, t, role in segs:
        box(s, M + off * unit, T + 15, ln * unit - 3, 60, role, t, f"{off}～{off + ln} MiB", 14, 12)
    # 查找 7 MiB
    x7 = M + 7 * unit
    s.line(x7, T + 5, x7, T + 85, RISK[1], 2)
    s.text(x7 + 6, T + 100, "要读 7 MiB", 13.5, RISK[2], 600)
    T2 = T + 140
    table(s, M, T2, [260, 200, 280, 380],
          [["0", "4 MiB", "第 1 代（模板）", "0"], ["4 MiB", "2 MiB", "第 3 代（本代）", "0"],
           ["6 MiB", "4 MiB", "第 2 代", "2 MiB"], ["10 MiB", "……", "第 1 代", "10 MiB"]],
          header=["设备偏移", "长度", "在哪一代", "那一代文件里的偏移"], roles=[None, None, OK, None])
    rx = M + 1180
    box(s, rx, T2, W - M - rx, 220, KEY, "读 7 MiB", "落在 6 MiB 起那一行\n7 − 6 = 1 MiB\n去读第 2 代文件的\n2 + 1 = 3 MiB 处", 16, 14)
    f = s.footer(T2 + 250, "每一代的映射表都是完整的：新一代 = 上一代的表 + 本代写过的块覆盖上去。从没写过的地方标成“空”，读出来是全零。")
    save(s, "04-2-映射表.svg", f + 20)


def fig_04_chain():
    s = Svg()
    y0 = s.header("代际链：每一代只存自己改的部分",
                  "模板构建时每一层是一代，之后每次暂停又长出一代。新一代不改动老一代的任何文件，只在映射表里把一些区间指向自己。")
    T = y0 + 40
    gens = [("base 层", "build A", CTL), ("指令 1 层", "build B", CTL), ("指令 2 层", "build C", CTL),
            ("finalize（模板）", "build D", CTL), ("第 1 次暂停", "build E", OK), ("第 2 次暂停", "build F", OK)]
    n = len(gens)
    gap = 30
    bw = (W - 2 * M - gap * (n - 1)) / n
    for i, (t, b, role) in enumerate(gens):
        x = M + i * (bw + gap)
        box(s, x, T, bw, 80, role, t, b, 15, 12.5)
        # 数据块示意
        k = [10, 3, 2, 4, 2, 1][i]
        for j in range(k):
            s.rect(x + 12 + j * 18, T + 100, 14, 30, role[0], role[1], 1, rx=2)
        if i < n - 1:
            arrow(s, [(x + bw + 3, T + 40), (x + bw + gap - 3, T + 40)], INK, 1.4)
    s.text(M, T + 160, "下面的小方块 = 这一代数据文件里的块：base 层最多，后面每代只有改过的几块。", 13.5, SUB)
    s.pill(M + 3 * (bw + gap) + bw / 2, T + 200, "几百台沙箱共享到这里", KEY, 13)
    s.pill(M + 4.5 * (bw + gap) + bw / 2, T + 200, "某一台沙箱自己的", OK, 13)
    bullets(s, M, T + 250, ["只追加，不修改：同一个模板的沙箱放心共享模板那几代",
                             "改得少，存得少：一代的大小正比于这一代改了多少",
                             "内存“改了多少”要靠脏页判据，判得准不准决定每一代多大（第 17、19、20 篇）"], 14.5, 32)
    f = s.footer(T + 360, "每一代有自己的 build ID；用户启动沙箱时，api 把模板名翻译成模板最后一代的 build ID。")
    save(s, "04-3-代际链.svg", f + 20)


def fig_04_where():
    s = Svg()
    y0 = s.header("快照产物落在哪：三层目录",
                  "持久化存储是“家”；本地缓存是启动、恢复时实际读的副本；沙箱运行态放正在跑的沙箱的写层和临时产物。")
    T = y0 + 40
    rows = [
        (STO, "持久化存储", "/tmp/templates（我们部署实际用的本地目录）或 MinIO 桶",
         "每个 build ID 一个目录：三件套 + 两张映射表 + metadata.json", "直到删除模板或快照"),
        (KEY, "本地缓存", "/orchestrator/build、/orchestrator/template",
         "从持久化存储拉下来的副本", "有过期时间；orchestrator 一重启就清空"),
        (WHITE, "沙箱运行态", "/orchestrator/sandbox、/mnt/snapshot-cache",
         "正在跑的沙箱的写层、暂停时的临时产物", "沙箱销毁即清"),
    ]
    y = T
    for role, t, path, what, life in rows:
        box(s, M, y, 260, 100, role, t, None, 17)
        s.text(M + 290, y + 30, path, 14, INK, 600, mono=False)
        s.text(M + 290, y + 58, what, 13.5, SUB)
        s.text(M + 290, y + 84, "生命周期：" + life, 13.5, SUB)
        y += 120
    box(s, M, y + 10, W - 2 * M, 70, RISK, "注意", "openEuler 上 /tmp 是 tmpfs：宿主一重启，/tmp/templates 里的模板全部丢失，要重新构建", 15, 13)
    f = s.footer(y + 110, "上游支持 Google、AWS 对象存储和本地目录；我们新增 MinIO 后端并设为默认，但单节点部署脚本把 template-manager 写死成了本地目录。")
    save(s, "04-4-产物落在哪.svg", f + 20)


if __name__ == "__main__":
    fig_01_life()
    fig_01_cycle()
    fig_01_map()
    fig_02_parts()
    fig_02_services()
    fig_02_planes()
    fig_03_pages()
    fig_03_uffd()
    fig_03_cow()
    fig_03_ns()
    fig_04_three()
    fig_04_header()
    fig_04_chain()
    fig_04_where()
