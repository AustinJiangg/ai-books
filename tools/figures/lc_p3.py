"""《E2B 模板构建、沙箱启动与暂停恢复从零讲透》第 10～15 篇的配图。用法: python3 tools/figures/lc_p3.py"""
from lc_common import *  # noqa: F401,F403
from lc_common import W, M


# ------------------------------------------------------------------ 第 10 篇
def fig_10_chain():
    s = Svg()
    y0 = s.header("一次 Sandbox.create 的请求链",
                  "api 认证、把模板名翻译成当前 build ID、选节点；orchestrator 先过准入闸门，再进入 ResumeSandbox；"
                  "最后 envd 收到 /init，沙箱可用。")
    T = y0 + 40
    items = [(CTL, "SDK", "Sandbox.create(\"my-python\")"), (CTL, "api", "认证 · 配额\n模板名 → build ID\n选节点"),
             (CTL, "准入闸门", "节点沙箱总数\n同时启动信号量"), (CTL, "ResumeSandbox", "准备五样东西\n加载快照"),
             (GST, "envd", "/init：身份、令牌、环境变量")]
    flow_h(s, M, T, W - 2 * M, items, h=140, gap=46, ts=16, ss=12.5, labels=["HTTPS", "gRPC", "", ""])
    T2 = T + 190
    table(s, M, T2, [440, 520, 540],
          [["同时启动上限", "3", "代码默认 500，部署 30，可调"], ["从模板创建、拿不到名额", "立即拒绝，让 api 换节点", "排队等待"],
           ["从暂停快照恢复、拿不到名额", "排队，最多 15 秒", "排队，最多 300 秒"], ["整个请求超时", "60 秒", "300 秒"],
           ["节点沙箱总数上限", "200", "10000"]],
          header=["准入参数", "上游", "我们"], roles=[None, OK, None, None, None])
    f = s.footer(T2 + 270, "上游的设计适合多节点：一个节点忙就换一个。单节点部署无处可换，所以一律排队。")
    save(s, "10-1-请求链.svg", f + 20)


def fig_10_structure():
    s = Svg()
    y0 = s.header("ResumeSandbox 的三段结构",
                  "第一段串行准备，同时在后台开始领网络槽位、搭根盘、准备 uffd、预取；第二段三路并行，耗时等于最慢的一路；"
                  "第三段串行收尾。")
    T = y0 + 40
    band(s, M, T, 380, 430, KEY, "一 · 串行准备")
    st = [("取模板句柄", "缓存没有就后台拉"), ("发起后台准备", "槽位、根盘、uffd、预取"), ("等网络槽位", None),
          ("读模板元数据", None), ("建 Firecracker 进程对象", "生成启动脚本，进程未起")]
    steps(s, M + 16, T + 60, 348, st, ts=13.5, ss=11.5, gap=8, numw=34)
    px = M + 420
    pw = 520
    band(s, px, T, pw, 430, FCR, "二 · 三路并行（取最慢）")
    box(s, px + 24, T + 70, pw - 48, 100, RISK, "拉起 Firecracker", "执行启动脚本，等 API 套接字出现（第 11 篇）", 15, 12.5)
    box(s, px + 24, T + 190, pw - 48, 90, WHITE, "等 uffd 套接字", "内存处理器就绪（第 12 篇）", 15, 12.5)
    box(s, px + 24, T + 300, pw - 48, 90, WHITE, "接上根盘", "符号链接到 NBD 设备（第 13 篇）", 15, 12.5)
    qx = px + pw + 40
    qw = W - M - qx
    band(s, qx, T, qw, 430, KEY, "三 · 串行收尾")
    st3 = [("加载快照", "PUT /snapshot/load，内存交给 uffd"), ("恢复 vCPU", None), ("写 MMDS", "沙箱身份"),
           ("调 envd /init", "令牌、环境变量、默认用户")]
    steps(s, qx + 16, T + 60, qw - 32, st3, ts=13.5, ss=11.5, gap=10, numw=34)
    arrow(s, [(M + 384, T + 215), (px - 4, T + 215)], INK, 1.6)
    arrow(s, [(px + pw + 4, T + 215), (qx - 4, T + 215)], INK, 1.6)
    f = s.footer(T + 460, "每准备好一样资源就登记一个清理函数；任何一步失败，倒序执行全部清理，不在宿主上留垃圾。")
    save(s, "10-2-ResumeSandbox结构.svg", f + 20)


def fig_10_cold_vs_resume():
    s = Svg()
    y0 = s.header("冷启动与快照恢复：省掉了什么",
                  "快照恢复省掉的是 guest 内部的全部初始化；省不掉的是宿主侧的准备。所以启动的时间几乎全花在宿主侧。")
    T = y0 + 40
    rows = [["内核引导", "要（几百毫秒到一秒）", "不要，在快照里"], ["systemd 拉起几十个服务", "要（几秒）", "不要"],
            ["envd 初始化", "要", "不要，envd 进程本来就在跑"], ["用户服务启动", "要", "不要，构建时已启动"],
            ["宿主准备五样东西", "要", "要"], ["加载快照", "不要", "要，几十毫秒"]]
    table(s, M, T, [480, 500, 520], rows, header=["步骤", "冷启动", "快照恢复"], roles=[OK, OK, OK, OK, RISK, None])
    f = s.footer(T + 360, "Sandbox.create 和 Sandbox.connect 走同一个 ResumeSandbox，只是用的快照不同。")
    save(s, "10-3-冷启动与恢复.svg", f + 20)


# ------------------------------------------------------------------ 第 11 篇
def fig_11_samepath():
    s = Svg()
    y0 = s.header("同一路径、各指各的文件",
                  "快照里录死了磁盘路径 /fc-vm/rootfs.ext4。每个 Firecracker 在私有的挂载命名空间里，在这个路径上盖一层 tmpfs、"
                  "放一个符号链接指向本沙箱自己的盘。别的 Firecracker 看不见。")
    T = y0 + 40
    n = 3
    gw = (W - 2 * M - 2 * 40) / n
    for i in range(n):
        x = M + i * (gw + 40)
        band(s, x, T, gw, 300, FCR, f"Firecracker {i + 1} 的挂载命名空间")
        box(s, x + 20, T + 60, gw - 40, 60, WHITE, None, "快照说：打开 /fc-vm/rootfs.ext4", 13.5, 13)
        box(s, x + 20, T + 140, gw - 40, 60, KEY, None, "tmpfs 盖住 /fc-vm", 13.5, 13)
        box(s, x + 20, T + 220, gw - 40, 60, STO, None, f"rootfs.ext4 → /dev/nbd{[3, 17, 42][i]}", 13.5, 13)
        arrow(s, [(x + gw / 2, T + 124), (x + gw / 2, T + 136)], INK, 1.2)
        arrow(s, [(x + gw / 2, T + 204), (x + gw / 2, T + 216)], INK, 1.2)
    f = s.footer(T + 330, "内核文件同理。类比：每户人家都有一个“101 号信箱”，但都是自己家门口那个。")
    save(s, "11-1-同一路径各指各的文件.svg", f + 20)


def fig_11_script():
    s = Svg()
    y0 = s.header("启动脚本的管线",
                  "unshare -m 开私有挂载命名空间；把挂载树设为私有；盖 tmpfs、放两个符号链接；最后进入网络命名空间并启动 Firecracker。"
                  "两处全挂载树操作（红）在高并发下要抢内核全局锁。")
    T = y0 + 40
    items = [(RISK, "unshare -m", "新的挂载命名空间"), (RISK, "mount --make-rprivate /", "遍历整棵挂载树"),
             (WHITE, "mount -t tmpfs", "盖住沙箱目录"), (WHITE, "ln -s ×2", "磁盘、内核"),
             (RISK, "ip netns exec <ns>", "进网络命名空间\n（还偷偷做五件事）"), (FCR, "firecracker", "--api-sock <sock>")]
    flow_h(s, M, T, W - 2 * M, items, h=120, gap=26, ts=14.5, ss=12)
    T2 = T + 160
    box(s, M, T2, W - 2 * M, 70, KEY, "然后", "orchestrator 每 10 毫秒检查一次 API 套接字是否出现；同时盯着脚本进程，提前退出就立即取消等待并报因", 15, 12.5)
    f = s.footer(T2 + 100, "第 15 篇：只把 ip netns exec 换成 fc-netns-exec，“等待 Firecracker 启动”就省下一大截。")
    save(s, "11-2-启动脚本管线.svg", f + 20)


def fig_11_load():
    s = Svg()
    y0 = s.header("加载快照的几次 HTTP 调用",
                  "Firecracker 就绪后，orchestrator 通过它的 HTTP 接口依次加载 snapfile、恢复 vCPU、写 MMDS。加载时一页内存都不读。")
    T = y0 + 40
    cols = [(CTL, "orchestrator"), (FCR, "Firecracker"), (CTL, "uffd 处理器")]
    cw = (W - 2 * M) / 3
    xs = [M + i * cw + cw / 2 for i in range(3)]
    for (role, t), x in zip(cols, xs):
        s.pill(x, T + 10, t, role, 14)
        s.line(x, T + 30, x, T + 360, HAIR, 1.4, dash="4 4")
    msgs = [(0, 1, T + 70, "PUT /snapshot/load：snapfile，内存后端 = uffd，先不运行（约 20～30 ms）"),
            (1, 1, T + 120, "重建 KVM 虚拟机、vCPU、中断控制器、virtio 设备"),
            (1, 2, T + 170, "连上 uffd 套接字，交出 guest 内存区域"),
            (0, 1, T + 230, "PATCH /vm  state = Resumed（不到 1 ms）"),
            (0, 1, T + 290, "PUT /mmds  沙箱 ID、模板 ID、令牌哈希（不到 1 ms）")]
    for a, b, y, t in msgs:
        if a == b:
            s.rect(xs[a] - 230, y - 18, 460, 30, FCR[0], FCR[1], 1, rx=6)
            s.text(xs[a], y + 2, t, 13.5, FCR[2], 600, "middle")
        else:
            arrow(s, [(xs[a], y), (xs[b], y)], INK, 1.5)
            s.text((xs[a] + xs[b]) / 2 + (60 if b == 2 else 0), y - 9, t, 13.5, INK, 600, "middle")
    f = s.footer(T + 390, "ARM 上的机器配置：SMT 关闭；脏页跟踪按硬件决定，从快照加载时也要在 /snapshot/load 里一并打开。")
    save(s, "11-3-加载快照.svg", f + 20)


# ------------------------------------------------------------------ 第 12 篇
def fig_12_fault():
    s = Svg()
    y0 = s.header("补一页的路径",
                  "guest 访问一页还没有内容的内存 → 内核挂起 vCPU、通知 orchestrator → 算出 memfile 偏移、查映射表 → 读本地缓存"
                  "（没有就从存储拉）→ UFFDIO_COPY 填 2 MiB → 唤醒 vCPU。")
    T = y0 + 40
    items = [(GST, "guest 缺页", "访问地址 X"), (FCR, "内核挂起 vCPU", "发缺页消息"),
             (CTL, "uffd 处理器", "X → memfile 偏移"), (CTL, "查映射表", "在哪一代哪个偏移"),
             (STO, "本地缓存", "没有就从存储拉"), (FCR, "UFFDIO_COPY", "填一整页 2 MiB"), (GST, "唤醒，重做", "这次成功")]
    flow_h(s, M, T, W - 2 * M, items, h=110, gap=22, ts=14, ss=12)
    T2 = T + 150
    table(s, M, T2, [420, 540, 540],
          [["一次缺页填多少", "一整个 guest 页", "大页背衬：2 MiB"], ["400 MiB 工作集要缺页几次", "2 MiB 大页：约 200 次", "4 KiB 小页：约 10 万次"],
           ["大页池", "部署时预留，按需落地", "只增不减；沙箱销毁即归还"]],
          header=["", "", ""])
    f = s.footer(T2 + 180, "加载快照时一页内存都没读；内存是在 guest 跑起来之后，一次次缺页回来的。")
    save(s, "12-1-补一页的路径.svg", f + 20)


def fig_12_prefetch():
    s = Svg()
    y0 = s.header("预取与按需：两组工作者 + 真实缺页",
                  "取数据的工作者立刻开始，甚至早于 Firecracker 启动；填内存的工作者等 uffd 就绪才开始。"
                  "真实缺页和预取走同一个填页函数，谁先填上，另一个就跳过。")
    T = y0 + 40
    tl = W - 2 * M - 200
    x0 = M + 200
    def bar(y, t, a, b, role, label):
        s.text(M, y + 22, t, 14, INK, 600)
        s.rect(x0 + tl * a, y, tl * (b - a), 34, role[0], role[1], 1.2, rx=6)
        s.text(x0 + tl * a + 10, y + 22, label, 12.5, role[2], 600)
    bar(T, "拉起 Firecracker", 0.0, 0.55, FCR, "启动脚本 → API 就绪 → 加载快照")
    bar(T + 50, "预取：取数据", 0.0, 0.7, STO, "按预取表把块读进本地缓存（并发 16 → 32）")
    bar(T + 100, "预取：填内存", 0.45, 0.9, CTL, "uffd 就绪后才开始（并发 8 → 16）")
    bar(T + 150, "真实缺页", 0.6, 1.0, GST, "guest 恢复运行，缺哪页补哪页")
    xr = x0 + tl * 0.45
    s.line(xr, T - 14, xr, T + 200, OK[1], 1.5, dash="5 4")
    s.text(xr, T + 220, "uffd 就绪", 13, OK[2], 600, "middle")
    xg = x0 + tl * 0.6
    s.line(xg, T - 14, xg, T + 200, RISK[1], 1.5, dash="5 4")
    s.text(xg, T + 240, "vCPU 恢复", 13, RISK[2], 600, "middle")
    f = s.footer(T + 270, "示意图，不按比例。预取的目标：guest 真正用到时，常用的页已经在了。")
    save(s, "12-2-预取与按需.svg", f + 20)


def fig_12_idle():
    s = Svg()
    y0 = s.header("一台空闲沙箱的内存账（2 vCPU、2048 MiB 规格）",
                  "启动 1、10、50 台空闲沙箱，测宿主变化做线性拟合：每台约 350 MiB = 大页 157 + 普通内存 194。"
                  "memory_mb = 2048 只是上限，空闲时只碰了 7.7%。")
    T = y0 + 40
    parts = [("大页（guest 碰过的内存）", 157, GST), ("沙箱目录文件页", 62.4, STO), ("其他文件缓存", 104.8, STO),
             ("匿名内存", 22.3, CTL), ("其他", 4.2, KEY)]
    total = sum(p[1] for p in parts)
    x = M
    tw = W - 2 * M
    for t, v, role in parts:
        w = tw * v / total
        s.rect(x, T, w - 3, 60, role[0], role[1], 1.2, rx=6)
        if w > 120:
            s.text(x + w / 2, T + 36, f"{v:g} MiB", 14, role[2], 600, "middle")
        x += w
    s.text(M, T + 90, "大页：单独的 hugetlb 账，不进 orchestrator 的内存上限", 13.5, GST[2], 600)
    s.text(M + tw * 157 / total + 10, T + 120, "普通内存 194 MiB：全部记在 orchestrator 所在 cgroup 的 32 GiB 上限里（Firecracker 没进自己的 cgroup）", 13.5, SUB)
    T2 = T + 160
    table(s, M, T2, [760, 300, 440],
          [["orchestrator 的 cgroup 开始回收旧缓存", "约 89 台", "先到的上限"], ["cgroup 里的旧缓存全部挤完", "约 167 台", "之后开始回收沙箱自己的页"],
           ["大页池（约 391 GiB），每台用满 2 GiB", "195 台", "有保证的下限"], ["大页池，每台只用空闲时的 157 MiB", "2554 台", ""]],
          header=["约束", "能撑的空闲沙箱数", ""], roles=[RISK, None, None, None])
    f = s.footer(T2 + 250, "想稳定支撑 X 台空闲沙箱：orchestrator 内存上限 ≥ 32 GiB（构建需要）+ X × 0.19 GiB。")
    save(s, "12-3-空闲沙箱内存账.svg", f + 20)


# ------------------------------------------------------------------ 第 13 篇
def fig_13_rootfs():
    s = Svg()
    y0 = s.header("根盘：模板只读层 + 沙箱写层，经 NBD 呈现为一块盘",
                  "guest 看到一块普通的 /dev/vda。读写请求经内核 NBD 模块转给 orchestrator：读先查写层，没有就按模板映射表读；写只进写层。")
    T = y0 + 40
    box(s, M, T, 300, 80, GST, "guest", "/dev/vda", 16, 13)
    box(s, M + 360, T, 300, 80, FCR, "Firecracker", "virtio 块设备", 16, 13)
    box(s, M + 720, T, 300, 80, FCR, "内核 NBD 模块", "/dev/nbdN", 16, 13)
    box(s, M + 1080, T, W - 2 * M - 1080, 80, CTL, "orchestrator", "NBD 服务端：分派读写", 16, 13)
    for x in (M + 300, M + 660, M + 1020):
        arrow(s, [(x + 4, T + 40), (x + 56, T + 40)], INK, 1.5)
    ox = M + 1080
    ow = W - 2 * M - 1080
    box(s, ox, T + 130, ow, 80, OK, "写层（本沙箱）", "按需增长的文件，mmap", 15, 12.5)
    box(s, ox, T + 240, ow, 80, KEY, "模板（只读，共享）", "按映射表读任意一代", 15, 12.5)
    arrow(s, [(ox + ow / 2, T + 84), (ox + ow / 2, T + 126)], INK, 1.4)
    arrow(s, [(ox + ow / 2, T + 214), (ox + ow / 2, T + 236)], MUTED, 1.4, dash="4 4")
    s.text(ox - 20, T + 230, "写层里没有才往下", 13, SUB, 400, "end")
    T2 = T + 360
    table(s, M, T2, [420, 1080],
          [["阶段一", "每次部署时先卸载自带模块再加载我们的：重复加载报错，有设备在用时卸载失败"],
           ["阶段二", "启动脚本不再管，每次重启后手动加载：容易忘"],
           ["阶段三（现在）", "一次性固化：覆盖系统模块目录里的原版（备份），开机自动加载，默认 512 个设备"],
           ["留下的坑", "升级内核后新目录里又是原版，开机照样 512 个设备，只有对比哈希才发现；模块必须和运行内核版本完全一致"]],
          header=["NBD 模块（自己编译的优化版）", ""], roles=[None, None, OK, RISK])
    f = s.footer(T2 + 250, "“准备根盘”在 ResumeSandbox 第一段就在后台开始，到并行段要用时通常已就绪（平均 0.2 ms）。")
    save(s, "13-1-根盘.svg", f + 20)


def fig_13_slot():
    s = Svg()
    y0 = s.header("网络槽位：命名空间 + tap + veth + iptables",
                  "所有沙箱的 guest IP 相同（同一张快照）；区分它们靠外面那层：每个槽位的 veth 有不同的宿主侧地址，地址转换把流量送进对应的命名空间。"
                  "槽位提前建好放进池子。")
    T = y0 + 40
    lw = 820
    band(s, M, T, lw, 330, STO, "宿主")
    band(s, M + 24, T + 60, 470, 250, KEY, "网络命名空间 ns-N")
    box(s, M + 48, T + 110, 200, 70, FCR, "Firecracker", None, 14.5)
    box(s, M + 270, T + 110, 200, 70, STO, "tap0", "接 guest 网卡", 14.5, 12)
    box(s, M + 270, T + 210, 200, 70, STO, "veth 一端", None, 14.5)
    box(s, M + 560, T + 210, 230, 70, STO, "e2bv-N（宿主侧）", "每槽一个宿主地址", 14, 12)
    box(s, M + 560, T + 90, 230, 90, KEY, "iptables", "地址转换 · 转发 · 端口重定向", 14, 12)
    arrow(s, [(M + 474, T + 245), (M + 556, T + 245)], INK, 1.5, start=True)
    arrow(s, [(M + 252, T + 145), (M + 266, T + 145)], INK, 1.4, start=True)
    px = M + lw + 50
    pw = W - M - px
    band(s, px, T, pw, 330, CTL, "槽位池")
    table(s, px + 20, T + 60, [220, (pw - 40 - 220) / 2, (pw - 40 - 220) / 2],
          [["新建池", "32", "300"], ["复用池", "100", "1000"]], header=["", "上游", "我们"])
    s.text(px + 20, T + 220, "建一个槽位要几十毫秒，提前建好", 13.5, SUB)
    s.text(px + 20, T + 248, "启动时直接领：平均 0.7 ms", 13.5, OK[2], 600)
    s.text(px + 20, T + 276, "强杀 orchestrator：整池泄漏，只能停—清—启", 13.5, RISK[2], 600)
    f = s.footer(T + 360, "从进程外面看，池子里闲着的槽位和泄漏的槽位一模一样：都没进程、都没被打开、名字地址规则相同。")
    save(s, "13-2-网络槽位.svg", f + 20)


def fig_13_envd():
    s = Svg()
    y0 = s.header("envd 醒过来之后的四件事",
                  "envd 没有重新启动，它从构建那一刻接着往下跑，只需要醒过来、接收新的身份。")
    T = y0 + 40
    items = [(GST, "拿身份", "从 MMDS 读沙箱信息\n（客户端改为复用连接）"), (GST, "收配置", "orchestrator 调 /init：\n令牌、环境变量、默认用户\n（超时 50 ms → 120 s）"),
             (GST, "对时", "时钟停在构建那一刻\nchrony 从宿主时钟设备同步"), (OK, "对外就绪", "外部轮询健康检查\n直到应答")]
    flow_h(s, M, T, W - 2 * M, items, h=150, gap=50, ts=16, ss=12.5)
    f = s.footer(T + 190, "/init 是同步的，在 ResumeSandbox 之内，通常几毫秒；客户端多出的几百毫秒不是“envd 启动慢”（第 14 篇）。")
    save(s, "13-3-envd四件事.svg", f + 20)


# ------------------------------------------------------------------ 第 14 篇
def fig_14_scopes():
    s = Svg()
    y0 = s.header("三个口径，别混",
                  "客户端墙钟 ⊃ 路由与 api + 准入排队 + ResumeSandbox 总耗时 + 善后。100 并发下客户端约 600 ms，ResumeSandbox 约 294 ms。")
    T = y0 + 50
    tw = W - 2 * M
    segs = [("路由 · api", 0.07, KEY), ("准入排队", 0.36, RISK), ("ResumeSandbox 总耗时 ≈ 294 ms", 0.49, CTL), ("善后", 0.08, KEY)]
    x = M
    for t, p, role in segs:
        w = tw * p
        s.rect(x, T + 40, w - 3, 56, role[0], role[1], 1.2, rx=6)
        s.text(x + w / 2, T + 74, t, 14, role[2], 600, "middle")
        x += w
    s.line(M, T + 20, M + tw, T + 20, INK, 1.5, start=True, end=True)
    s.text(M + tw / 2, T + 10, "客户端墙钟 ≈ 600 ms（Sandbox.create 从调用到返回）", 14.5, INK, 600, "middle")
    T2 = T + 140
    table(s, M, T2, [420, 600, 480],
          [["客户端墙钟", "Sandbox.create 从调用到返回", "压测脚本"], ["准入排队", "等“同时启动”信号量", "orchestrator 日志：acquire wait"],
           ["ResumeSandbox 总耗时", "进入函数到返回，含 envd /init", "orchestrator 日志：total"]],
          header=["口径", "量的是什么", "在哪测"])
    f = s.footer(T2 + 170, "示意图，各段比例只表示量级；准入排队的大小取决于并发数和信号量上限。")
    save(s, "14-1-三个口径.svg", f + 20)


def fig_14_critical():
    s = Svg()
    y0 = s.header("100 路并发的关键路径：拉起 Firecracker 占 82%",
                  "并行段只算最长一路。等 uffd（13.2 ms）和准备根盘（0.2 ms）被拉起 Firecracker 的 241.6 ms 盖住了。")
    T = y0 + 40
    rows = [("获取网络槽位", 0.68, WHITE, True), ("获取模板元数据", 0.09, WHITE, True), ("创建进程对象", 15.45, NAT, True),
            ("等待 Firecracker 启动", 241.61, RISK, True), ("等待 uffd 套接字", 13.18, KEY, False), ("准备根盘", 0.19, KEY, False),
            ("加载快照", 29.15, NAT, True), ("恢复 vCPU", 0.58, WHITE, True), ("写 MMDS", 0.40, WHITE, True),
            ("envd /init 与零碎", 6.8, WHITE, True)]
    lx = M + 260
    tw = W - M - lx - 140
    scale = tw / 245
    y = T
    for t, v, role, crit in rows:
        s.text(M, y + 20, t, 14, INK if crit else MUTED, 600 if crit else 400)
        w = max(v * scale, 3)
        s.rect(lx, y + 4, w, 24, role[0], role[1], 1.2, rx=4, dash=None if crit else "4 3")
        s.text(lx + w + 10, y + 21, f"{v:g} ms" + ("" if crit else "（被盖住）"), 13, INK if crit else MUTED, 600 if crit else 400)
        y += 38
    s.text(M, y + 30, "总耗时 294.69 ms ≈ 0.7 + 0.1 + 15.5 + max(241.6, 13.2, 0.2) + 29.1 + 0.6 + 0.4 + 约 6.8", 15, INK, 600)
    f = s.footer(y + 60, "p99：等待 Firecracker 启动 329 ms，远大于平均 242 ms，是资源争用的典型特征。优化只有这一个主战场。")
    save(s, "14-2-关键路径.svg", f + 20)


def fig_14_gantt():
    s = Svg()
    y0 = s.header("时间轴甘特：每台沙箱一条，阶段按真实时刻摆放",
                  "示意图：排队按信号量分批成阶梯；三路并行分泳道（红：拉起 Firecracker；蓝：等 uffd；橄榄：根盘），"
                  "最长一路决定汇合点；之后是加载快照（紫）和 envd（绿）。")
    T = y0 + 40
    lx = M + 120
    tw = W - M - lx
    scale = tw / 900
    import random
    random.seed(7)
    n = 12
    y = T
    for i in range(n):
        q = (i // 4) * 260
        start = q + random.randint(0, 20)
        s.text(M, y + 22, f"沙箱 {i + 1}", 13, SUB)
        def seg(a, b, role, yy, h):
            s.rect(lx + a * scale, yy, max((b - a) * scale, 2), h, role[0], role[1], 1, rx=3)
        if q:
            seg(0, start, KEY, y + 6, 22)
        np_ = 15 + random.randint(0, 10)
        seg(start, start + np_, ("#E0F4F4", "#3BA7A7", "#1F6E6E"), y + 6, 22)
        c = start + np_
        fc = 200 + random.randint(0, 60) + (i // 4) * 15
        seg(c, c + fc, RISK, y + 2, 12)
        seg(c, c + 13, CTL, y + 16, 8)
        seg(c, c + 2, ("#F1F3DC", "#9AA33A", "#5D6420"), y + 26, 6)
        c += fc
        seg(c, c + 29, GST, y + 6, 22)
        seg(c + 30, c + 37, OK, y + 6, 22)
        y += 38
    s.line(lx, y + 8, lx + tw, y + 8, INK, 1.2, end=True)
    s.text(lx + tw, y + 30, "时间", 13, SUB, 400, "end")
    legend(s, y + 60, [(KEY, "准入排队"), (("#E0F4F4", "#3BA7A7", "#1F6E6E"), "建进程对象"), (RISK, "拉起 Firecracker"),
                       (CTL, "等 uffd"), (GST, "加载快照"), (OK, "envd /init")])
    f = s.footer(y + 90, "时刻从日志的时间戳推出：每条计时日志的时间 ≈ 阶段结束时刻，减去耗时就是开始时刻；同一台机器的时钟，不用担心跨机误差。")
    save(s, "14-3-时间轴甘特.svg", f + 20)


def fig_14_e2e():
    s = Svg()
    y0 = s.header("端到端拆分：294 ms 之外那约 300 ms",
                  "常见的说法“那 300 ms 是 envd 启动慢”不对。orchestrator 同步调的 /init 在 294 ms 之内，只有几毫秒；"
                  "差值是排队、路由、轮询就绪、恢复后缺页的合计。")
    T = y0 + 40
    rows = [["准入排队", "ResumeSandbox 之前", "并发超过上限时可能最大：并发 100、上限 30，约 70 台在排队"],
            ["路由与网络往返", "SDK → api → orchestrator → 回来", "几到几十毫秒"],
            ["外部轮询 envd 就绪", "proxy 层反复检查健康", "受轮询间隔影响"],
            ["恢复后的缺页", "100 台同时缺页争抢 I/O", "被低估的一块"]]
    table(s, M, T, [360, 520, 620], rows, header=["差值里的成分", "在哪", "量级"], roles=[RISK, None, None, None])
    T2 = T + 260
    box(s, M, T2, W - 2 * M, 100, OK, "正确的做法：补点，不做减法",
        "给准入排队打点（已做，且两条排队路径都要打）· 在 envd 内部给收到 /init、对完时、首次健康检查成功打时间戳 · 跑一遍并发 1 做对照，逐阶段算放大倍数", 15, 12.5)
    f = s.footer(T2 + 130, "埋点的坑：普通创建和从暂停恢复走两条不同的排队路径，只给一条打了点，排队时间的样本数曾是 0。")
    save(s, "14-4-端到端拆分.svg", f + 20)


# ------------------------------------------------------------------ 第 15 篇
def fig_15_six():
    s = Svg()
    y0 = s.header("ip netns exec 实际做的六件事，只有一件是需要的",
                  "iproute2 的 netns exec 每次都做完整一套。第 2、3、4 件要持内核全局的挂载命名空间锁，100 个沙箱同时做时互相排队。")
    T = y0 + 36
    rows = [["1", "打开命名空间文件，setns 进入网络命名空间", "很便宜", "需要"],
            ["2", "再创建一个挂载命名空间", "复制整棵挂载树，持全局锁", "不需要，脚本开头已经建过"],
            ["3", "整棵挂载树递归设为 slave", "又遍历一次，持全局锁", "不需要"],
            ["4", "卸载并重挂 /sys", "重建 sysfs 对象树，持全局锁", "不需要，不读 /sys 的网络信息"],
            ["5", "/etc/netns/<ns>/ 绑定到 /etc", "按命名空间配 DNS", "不需要，guest 用自己的 /etc"],
            ["6", "加载 ip 二进制本身", "动态链接好几个库", "不需要"]]
    table(s, M, T, [80, 560, 420, 440], rows, header=["#", "实际动作", "代价", "Firecracker 需要吗"],
          roles=[OK, RISK, RISK, RISK, None, None])
    f = s.footer(T + 400, "fc-netns-exec 只保留第 1 件：setns + execve，静态编译，不过动态链接。")
    save(s, "15-1-六件事.svg", f + 20)


def fig_15_lock():
    s = Svg()
    y0 = s.header("全局锁上的排队",
                  "单个沙箱做挂载树操作只要几毫秒；100 个同时做，就在内核的挂载命名空间锁上一个接一个。这是“等待 Firecracker 启动”"
                  "从单沙箱几十毫秒放大到 240 ms 的串行化来源之一。")
    T = y0 + 40
    box(s, W / 2 - 200, T, 400, 70, RISK, "内核全局锁", "namespace_sem", 17, 13)
    n = 10
    cw = (W - 2 * M - (n - 1) * 14) / n
    for i in range(n):
        x = M + i * (cw + 14)
        box(s, x, T + 140, cw, 54, FCR, f"沙箱 {i + 1}", None, 13.5)
        arrow(s, [(x + cw / 2, T + 136), (W / 2 + (i - 4.5) * 30, T + 74)], MUTED, 1.2)
    s.text(M, T + 240, "持锁中：", 14, INK, 600)
    tl = W - 2 * M - 100
    for i in range(n):
        s.rect(M + 100 + i * tl / n, T + 222, tl / n - 4, 26, RISK[0] if i else RISK[1], RISK[1], 1, rx=4)
    s.text(M + 100, T + 280, "一次只有一个能进去，其余排队", 13.5, SUB)
    f = s.footer(T + 310, "p99（329 ms）远大于平均值（242 ms）的长尾，也是锁争用的典型形态。")
    save(s, "15-2-全局锁排队.svg", f + 20)


def fig_15_before_after():
    s = Svg()
    y0 = s.header("优化前后的启动管线：只换掉最后一环",
                  "其余部分原封不动，和上游相比只有一个变量。在脚本模板里生成命令，不做字符串替换；模板构建的虚拟机不走这条路。")
    T = y0 + 40
    common = [(WHITE, "unshare -m", None), (WHITE, "make-rprivate", None), (WHITE, "tmpfs + ln", None)]
    s.text(M, T + 10, "优化前", 16, RISK[2], 600)
    flow_h(s, M, T + 24, W - 2 * M, common + [(RISK, "ip netns exec", "6 件事，3 件抢全局锁"), (FCR, "firecracker", None)], h=86, gap=40)
    s.text(M, T + 160, "优化后", 16, OK[2], 600)
    flow_h(s, M, T + 174, W - 2 * M, common + [(OK, "fc-netns-exec", "setns + execve"), (FCR, "firecracker", None)], h=86, gap=40)
    T2 = T + 300
    table(s, M, T2, [480, 1020],
          [["不设置（默认）", "开启：/opt/e2b-infra/bin/fc-netns-exec"], ["disabled、ip-netns-exec 或空", "退回 ip netns exec"],
           ["其他路径", "用那个路径下的小程序"]], header=["E2B_FC_NETNS_EXEC_HELPER", "行为"])
    f = s.footer(T2 + 170, "LockOSThread 不能省：setns 只改当前系统线程，必须保证 setns 和 execve 在同一个线程上。")
    save(s, "15-3-优化前后管线.svg", f + 20)


def fig_15_rejected():
    s = Svg()
    y0 = s.header("放弃的两档：子进程侧省下的，父进程侧又赔回去",
                  "把整条管线重写成一个 Go / C 程序，不经过 bash。子进程侧从 138 ms 降到 29 ms；但复制挂载命名空间这一步搬到了父进程，"
                  "被拖到平均 143 ms。两段合计比只用 fc-netns-exec 倒赔约 31 ms。")
    T = y0 + 50
    lx = M + 300
    scale = (W - M - lx - 160) / 200
    def b(y, t, segs):
        if t:
            s.text(M, y + 24, t, 15, INK, 600)
        x = lx
        for v, role, lab in segs:
            w = v * scale
            s.rect(x, y, w - 2, 36, role[0], role[1], 1.2, rx=5)
            if lab:
                s.text(x + w / 2 if w > 200 else x + 8, y + 24, lab, 13, role[2], 600, "middle" if w > 200 else "start")
            x += w
    b(T, "子进程侧（socket 等待）", [(138, KEY, "fc-netns-exec：138 ms")])
    b(T + 56, "", [(29, OK, "重写：29")])
    b(T + 140, "两段合计", [(3, KEY, ""), (138, KEY, "fc-netns-exec：父进程约 3 + 子进程 138 ≈ 141 ms")])
    b(T + 196, "", [(143, RISK, "重写：父进程复制挂载命名空间 143 ms"), (29, OK, "29")])
    s.text(M, T + 290, "成本没有消失，只是从子进程挪到了父进程；而父进程是 orchestrator 本身，所有启动都要经过它。", 14.5, RISK[2], 600)
    f = s.footer(T + 320, "fc-netns-exec 的父进程一段按“倒赔约 31 ms”反推：141 + 31 = 143 + 29。教训：优化的收益要看端到端。")
    save(s, "15-4-放弃的两档.svg", f + 20)


def fig_15_params():
    s = Svg()
    y0 = s.header("启动相关参数的修改总表",
                  "上游默认值为多节点大集群设计；我们是单节点、要求上百路并发。用“上限扫描”定同时启动上限：放开后若只是把时间从排队挪到等 Firecracker，"
                  "说明真正的天花板在 Firecracker 启动。")
    T = y0 + 36
    rows = [["同时启动上限", "3", "默认 500，部署 30，可调"], ["拿不到启动名额（从模板创建）", "立即拒绝", "排队"],
            ["排队超时 / 请求超时", "15 秒 / 60 秒", "300 秒 / 300 秒"], ["节点沙箱总数上限", "200", "10000"],
            ["新建 / 复用网络槽位池", "32 / 100", "300 / 1000"], ["预取：取数据 / 填内存并发", "16 / 8", "32 / 16"],
            ["envd /init 单次超时", "50 毫秒", "120 秒"], ["等 uffd 消息超时", "10 秒", "120 秒"],
            ["等套接字超时", "写死", "环境变量可调，默认 300 秒"], ["等套接字的上下文", "与调用方无关", "以调用方为基础（失败立即报因）"]]
    table(s, M, T, [600, 400, 500], rows, header=["参数", "上游", "我们"], roles=[None] * 9 + [OK])
    f = s.footer(T + 560, "宿主侧另有三项：大页池单独释放（并封顶 64 GB）、Nomad 升级到 1.11.2（不连续 NUMA 编号）、绑核绑整个任务 cgroup 且先算大页。")
    save(s, "15-5-参数总表.svg", f + 20)


if __name__ == "__main__":
    fig_10_chain()
    fig_10_structure()
    fig_10_cold_vs_resume()
    fig_11_samepath()
    fig_11_script()
    fig_11_load()
    fig_12_fault()
    fig_12_prefetch()
    fig_12_idle()
    fig_13_rootfs()
    fig_13_slot()
    fig_13_envd()
    fig_14_scopes()
    fig_14_critical()
    fig_14_gantt()
    fig_14_e2e()
    fig_15_six()
    fig_15_lock()
    fig_15_before_after()
    fig_15_rejected()
    fig_15_params()
