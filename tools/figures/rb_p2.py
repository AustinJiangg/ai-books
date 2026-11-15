"""《E2B 沙箱快照回滚从零讲透》第 5～8 篇的配图。用法: python3 tools/figures/rb_p2.py"""
from rb_common import *  # noqa: F401,F403
from rb_common import W, M


def frozen_band(s, x, y, w, h, label="冻结窗口：虚机暂停"):
    s.rect(x, y, w, h, FROZEN[0], FROZEN[1], 1.3, rx=12, dash="6 4")
    s.text(x + 16, y + 26, label, 14, FROZEN[2], 600)


# ------------------------------------------------------------------ 第 5 篇
def fig_05_path():
    s = Svg()
    y0 = s.header("请求发往沙箱，却由宿主应答",
                  "SDK 把存档请求发到沙箱的 49984 端口，和普通请求走同一条路。orchestrator 的代理解出（沙箱 ID, 端口）后多看一眼："
                  "命中 49984 且是 checkpoint 路径，就不转发，交给 Checkpoint Service；读档进行中，别的请求直接回答 409；其余照常进沙箱。")
    T = y0 + 40
    sdk = (M, T + 110, 200, 90)
    box(s, *sdk, CTL, "SDK", "沙箱地址 :49984\n/checkpoint.Checkpoint/…", 16, 12)
    px = M + 280
    proxy = (px, T + 90, 300, 130)
    box(s, *proxy, CTL, "orchestrator 代理", "解出（沙箱 ID, 端口）\n复用已有的寻址机制", 16, 12.5)
    arrow(s, [(sdk[0] + sdk[2] + 4, T + 155), (px - 4, T + 155)], INK, 1.6)
    ox = px + 300 + 220
    ow = W - M - ox
    outs = [
        (CTL, "Checkpoint Service", "命中 49984 + checkpoint 路径 / health\n先查沙箱，再自己验一次令牌", "存档请求"),
        (RISK, "直接回答 409", "这台沙箱正在读档：不放进去\nSDK 抛 CheckpointInterruptedException", "读档期间的其他请求"),
        (GST, "照常转发进沙箱 → envd", "其他一切请求，行为不变", "普通请求"),
    ]
    for i, (role, t, sub, lab) in enumerate(outs):
        y = T + i * 120
        box(s, ox, y, ow, 96, role, t, sub, 15, 12.5)
        arrow(s, [(px + 304, T + 155), (ox - 180, T + 155), (ox - 180, y + 48), (ox - 4, y + 48)], INK if i != 1 else RISK[1], 1.5)
        s.text(ox - 92, y + 38, lab, 12.5, SUB, 400, "middle")
    T2 = T + 380
    box(s, M, T2, W - 2 * M, 70, KEY, "沙箱里没有任何程序监听 49984",
        "SDK 的 is_available() 打的也是这里的 /health，探的是宿主侧服务活不活着；客户机完全不知道自己被存过档（VMGenID 那一次通知除外）", 15, 12.5,
        style="outline")
    yy = s.footer(T2 + 100, "注：代理原本的令牌检查在拦截点之后，被截走的请求绕过了它，所以 Service 必须自己补上：新加旁路时，原来路上的检查要跟着补。")
    save(s, "05-1-请求路径.svg", yy + 20)


def fig_05_layers():
    s = Svg()
    y0 = s.header("分层与边界：谁知道“树”，谁只做机械动作",
                  "语义只在一处：存档树、回滚集只有账本懂；“怎么把一页写进活着的客户机内存”只有 Firecracker 懂。"
                  "两侧按约定的接口说话，任何一侧改动，只要接口不变，另一侧就不受影响。")
    T = y0 + 30
    rows = [
        (CTL, "SDK", "把四个调用发到沙箱地址", "不知道请求没进沙箱"),
        (CTL, "代理", "认出存档请求并改道", "不懂存档的含义"),
        (CTL, "Checkpoint Service", "编排、排队、全量/增量决策、失败分级、计时", "不碰客户机内存，不算回滚集"),
        (CTL, "账本 Store", "存档树、回滚集、按页找内容、磁盘层清单、合并", "不和 Firecracker 说话"),
        (STO, "Sandbox 对象", "暂停/恢复、封存写层、换磁盘视图、清连接跟踪", "不知道存档树"),
        (FCR, "Firecracker（分叉）", "写快照、导出脏页、原地回滚", "不知道有“树”这回事"),
        (FCR, "KVM / CPU", "记录脏页", "——"),
    ]
    widths = [320, 640, W - 2 * M - 960]
    y = T
    s.text(M + 10, y + 4, "层", 13.5, SUB, 600)
    s.text(M + widths[0] + 10, y + 4, "负责", 13.5, OK[2], 600)
    s.text(M + widths[0] + widths[1] + 10, y + 4, "不负责", 13.5, RISK[2], 600)
    y += 20
    for role, a, b, c in rows:
        box(s, M, y, widths[0] - 10, 50, role, a, None, 15)
        box(s, M + widths[0], y, widths[1] - 10, 50, WHITE, None, b, 15, 13.5)
        box(s, M + widths[0] + widths[1], y, widths[2], 50, WHITE, None, c, 15, 13.5)
        y += 60
        if a == "Sandbox 对象":
            s.line(M - 6, y + 2, W - M + 6, y + 2, FCR[1], 1.6, dash="6 4")
            s.text(W - M, y + 24, "约定的接口：位图文件 + 内容文件 + 三处扩展", 12.5, FCR[2], 600, "end")
            y += 36
    yy = s.footer(y + 10, "注：Firecracker 只加了三处，没有改动任何已有行为；orchestrator 与 Firecracker 必须成对交付，未打补丁的版本在 rollback 接口上返回 404。")
    save(s, "05-2-分层与边界.svg", yy + 20)


def fig_05_dir():
    s = Svg()
    y0 = s.header("存档目录：每个文件谁写、谁读、什么时候消失",
                  "根目录在 orchestrator 启动时整个清空，账本从不读盘。文件先写临时名、再改名到位（不 fsync）："
                  "prepared 的条目不在账本里，只有 committed 的才能被列出、被读档。")
    T = y0 + 34
    nodes = [
        (0, "/orchestrator/build/checkpoints/", "启动时清空", STO),
        (1, "{沙箱 ID}/", "沙箱移除时整棵改名进回收目录再删", STO),
        (2, "ckpt_{时间戳}/", "一个存档", CTL),
        (3, "snapfile", "Firecracker 写 / 读档时 Firecracker 读；隐藏时删", FCR),
        (3, "mem_diff", "Firecracker 写 / orchestrator 找内容；隐藏时保留", FCR),
        (3, "mem_bitmap", "Firecracker 写 / 算回滚集、找内容；隐藏时保留", FCR),
        (3, "rootfs.header", "orchestrator 写 / 读档后重置磁盘账本", CTL),
        (3, "manifest.json", "只给人看，程序从不读", STO),
        (3, "timings.json", "这次存档各阶段耗时", STO),
        (2, "layers/", "多代共享", STO),
        (3, "layer-{uuid}", "客户机自己写出的写层文件，改名而来；引用计数归零才删", GST),
        (3, "layer-{uuid}.meta", "这一层有哪些块", CTL),
        (2, "last-restore-timings.json", "最近一次读档各阶段耗时", STO),
    ]
    tree(s, M, T, [(d, t, n, r) for d, t, n, r in nodes], indent=40, gap=36, size=14)
    rx = M + 1080
    band(s, rx, T - 20, W - M - rx, 330, OK, "原子提交")
    bullets(s, rx + 22, T + 50, ["先写 xxx.tmp", "全部写完再改名到正式名字", "manifest 改成 committed", "锁内发布进账本",
                                  "半写完的存档永远不会成为读档目标"], 13.5, 44, dot=OK[1], maxw=W - M - rx - 50)
    yy = s.footer(T + 13 * 36 + 6, "注：不 fsync 的理由：存档本来就不承诺活过 orchestrator 进程，原子性来自改名；颜色表示谁写这个文件。")
    save(s, "05-3-产物目录.svg", yy + 20)


# ------------------------------------------------------------------ 第 6 篇
def fig_06_ck_timeline():
    s = Svg()
    y0 = s.header("一次存档的时间线：窗口外准备、冻结窗口、窗口外提交",
                  "冻结窗口里只有“写快照”一步与改动量相关；封存写层不搬数据。凡是能在窗口外做的都挪出去：准备在前，"
                  "层文件改名进存档目录在恢复运行之后。")
    T = y0 + 40
    pre = [("进门", "鉴权 · 脱钩请求生命周期\n拒绝已撕裂 · 取沙箱锁"), ("再确认", "沙箱还在、还是同一代 · 水位检查"),
           ("决定全量 / 增量", "无基准 → 全量根\n在跟踪且链没断 → 增量"), ("Prepare", "配额检查 · 建目录 · 条目对外不可见")]
    w = 250
    for i, (t, sub) in enumerate(pre):
        box(s, M, T + 40 + i * 90, w, 78, CTL, t, sub, 14.5, 12)
    s.text(M, T + 22, "窗口外：失败都干净", 13.5, OK[2], 600)
    fx = M + w + 50
    fw = 640
    frozen_band(s, fx, T, fw, 400)
    steps = [("1. 暂停", "常数"), ("2. 仅全量：导出活跃位图", "很小"), ("3. 写快照 + 位图（一次调用）", "本代脏页数 · 纪元前进"),
             ("4. 封存写层", "接近常数，不搬数据"), ("5. 恢复（无论成败）", "常数")]
    yy = T + 50
    for t, c in steps:
        hl = "3. " in t
        box(s, fx + 20, yy, fw - 40, 54, RISK if hl else WHITE, None, None)
        s.text(fx + 36, yy + 33, t, 14.5, RISK[2] if hl else INK, 600)
        s.text(fx + fw - 36, yy + 33, c, 13, RISK[2] if hl else SUB, 600 if hl else 400, "end")
        yy += 68
    px = fx + fw + 50
    pw = W - M - px
    post = [("层文件改名进存档目录", "跨文件系统时是拷贝，所以放在恢复之后"), ("登记磁盘账本", "失败 → 标记“已污染”"),
            ("提交", "改名 · committed · 发布 · 当前基准 ← 新存档"), ("返回", "checkpoint_id + mem_mode")]
    for i, (t, sub) in enumerate(post):
        box(s, px, T + 40 + i * 90, pw, 78, CTL, t, sub, 14.5, 12)
    s.text(px, T + 22, "窗口外：失败走三层降级", 13.5, RISK[2], 600)
    arrow(s, [(M + w + 4, T + 200), (fx - 4, T + 200)], INK, 1.5)
    arrow(s, [(fx + fw + 4, T + 200), (px - 4, T + 200)], INK, 1.5)
    yy2 = s.footer(T + 430, "注：950 上改 128 MiB 时写快照约 62 ms、封存约 7 ms；首次全量写快照约 440 ms（第 17 篇）。")
    save(s, "06-1-checkpoint时间线.svg", yy2 + 20)


def fig_06_epoch():
    s = Svg()
    y0 = s.header("纪元前进前后：失败处理从“删干净”变成“三层降级”",
                  "写快照成功的那一刻，Firecracker 把脏页记录清零，差分文件成了那段时间脏页的唯一记录。此前的失败删目录就行；"
                  "此后的失败如果删目录，那一段写过哪些页就永远丢了，之后的读档会静默漏页。")
    T = y0 + 50
    s.line(M, T + 40, W - M, T + 40, SUB, 2, end=True)
    mid = M + 560
    s.line(mid, T + 10, mid, T + 70, RISK[1], 3)
    s.text(mid, T, "写快照成功：纪元前进", 15, RISK[2], 600, "middle")
    s.text((M + mid) / 2, T + 70, "检查 · 决策 · Prepare · 暂停", 13.5, SUB, 400, "middle")
    s.text((mid + W - M) / 2, T + 70, "封存 · 改名 · 登记磁盘账本 · 提交", 13.5, SUB, 400, "middle")
    lw = mid - M - 30
    box(s, M, T + 110, lw, 120, OK, "失败是干净的", "删掉刚建的目录\n虚机没被碰过，沙箱照常运行", 16, 13)
    rx = mid + 30
    rw = W - M - rx
    steps = [(OK, "能正常提交", "→ 正常提交"), (NAT, "不能 → 能隐藏提交吗？", "→ 隐藏提交：不出现在列表里、不能读档，但位图和差分留在树里，纪元没丢"),
             (RISK, "也不能", "→ 标记链断：拒绝一切读档，下一次存档强制全量，起一棵新树")]
    yy = T + 110
    for role, t, sub in steps:
        box(s, rx, yy, rw, 70, role, t, sub, 14.5, 12.5)
        yy += 82
    s.text(rx, yy + 18, "另：封存已换上新写层、旧层还没登记时，磁盘账本标记“已污染”。", 13, SUB)
    yy2 = s.footer(yy + 50, "注：三层的思路是一致的：宁可留下一点垃圾，也不能留下一条坏链（第 13 篇）。")
    save(s, "06-2-纪元前进前后.svg", yy2 + 20)


# ------------------------------------------------------------------ 第 7 篇
def fig_07_rs_timeline():
    s = Svg()
    y0 = s.header("一次读档的时间线：准备、冻结窗口、收尾",
                  "目标磁盘视图在暂停之前就装配好；冻结窗口里导出活跃脏页、物化回滚集、交给 Firecracker 原地回滚、整体换磁盘，"
                  "连接跟踪清理在后台并行；回滚完成后先更新账本，再等 envd。")
    T = y0 + 40
    pre = [("进门", "同存档：鉴权、取锁、再确认"), ("取目标", "本代 · 已提交 · 未隐藏"), ("装配目标视图", "读块清单、重开封存层、建索引\n950 上约 0.2 ms"),
           ("打开读档窗口", "丢弃代理连接池\n别的请求回 409")]
    w = 190
    for i, (t, sub) in enumerate(pre):
        box(s, M, T + 40 + i * 96, w + 30, 84, CTL, t, sub, 14, 12)
    s.text(M, T + 22, "窗口外", 13.5, OK[2], 600)
    fx = M + w + 70
    fw = 820
    frozen_band(s, fx, T, fw, 440)
    steps = [("1. 暂停", "常数"), ("2. 导出活跃脏页", "位图扫描，常数极小"), ("3. 物化：算回滚集、沿祖先链找内容", "回滚集大小"),
             ("4. Firecracker 原地回滚（九阶段）", "回滚集大小 + 常数"), ("5. 整体换磁盘视图", "常数"), ("6. 等连接跟踪清理结束", "通常 ≈ 0"),
             ("7. 恢复", "常数")]
    yy = T + 46
    for t, c in steps:
        hl = "3. " in t or "4. " in t
        box(s, fx + 20, yy, fw - 300, 44, FCR if hl else WHITE, None, None)
        s.text(fx + 36, yy + 28, t, 14, FCR[2] if hl else INK, 600)
        s.text(fx + fw - 300, yy + 28, c, 12.5, SUB, 400, "end")
        yy += 54
    bx = fx + fw - 250
    box(s, bx, T + 46, 230, 54 * 5 + 44, NAT, "后台：清连接跟踪表", "暂停后立即开始\n与 2. ～5. 并行\n恢复前等它结束", 14, 12.5, style="dashed")
    px = fx + fw + 30
    pw = W - M - px
    post = [("当前基准 ← 目标", "树从这里长出新分支"), ("磁盘账本 ← 目标描述", "顺带清除“已污染”"), ("等 envd 应答", "最多 45 s · 校正墙钟"),
            ("返回成功", "失败按四档分级")]
    for i, (t, sub) in enumerate(post):
        box(s, px, T + 40 + i * 96, pw, 84, CTL, t, sub, 14, 12)
    s.text(px, T + 22, "窗口外：账本跟着状态走", 13.5, CTL[2], 600)
    yy2 = s.footer(T + 470, "注：和虚机大小相关的只有两次位图扫描（2 GiB 是 8192 个字），其余都只和回滚集有关。")
    save(s, "07-1-restore时间线.svg", yy2 + 20)


def fig_07_clocks():
    s = Svg()
    y0 = s.header("三个钟：调用方等了多久、业务停了多久、停的时间花在哪",
                  "客户端墙钟包含网络往返和排队，最大，也是使用者唯一能复测的；冻结窗口是业务真正感到的停顿；"
                  "分阶段计时回答时间花在哪。墙钟慢而冻结窗口正常，问题在网络或排队；冻结窗口慢，再看哪一段。")
    T = y0 + 60
    x0, x1 = M + 40, W - M - 40
    s.rect(x0, T, x1 - x0, 60, CTL[0], CTL[1], 1.4, rx=10)
    s.text(x0 + 16, T + 36, "客户端墙钟：SDK 发出调用 → 拿到返回", 15, CTL[2], 600)
    f0, f1 = x0 + 220, x1 - 260
    s.rect(f0, T + 90, f1 - f0, 60, FROZEN[0], FROZEN[1], 1.4, rx=10, dash="6 4")
    s.text(f0 + 16, T + 126, "冻结窗口 frozen：暂停 → 恢复", 15, FROZEN[2], 600)
    segs = [("暂停", 0.1), ("导出位图", 0.15), ("物化", 0.25), ("fc_rollback", 0.25), ("换盘", 0.12), ("恢复", 0.13)]
    x = f0
    tot = f1 - f0
    for name, frac in segs:
        w = tot * frac
        s.rect(x + 2, T + 180, w - 4, 50, FCR[0] if name in ("fc_rollback",) else STO[0], FCR[1] if name == "fc_rollback" else STO[1], 1.2, rx=6)
        s.text(x + w / 2, T + 211, name, 13, INK, 600, "middle")
        x += w
    s.text(f0, T + 260, "分阶段计时（举例：读档）。fc_* 由 Firecracker 自报，其余由 orchestrator 记", 13, SUB)
    s.text(x0, T + 300, "窗口外的段：网络往返、排队、装配视图、等 envd", 13, SUB)
    yy = s.footer(T + 330, "注：包含关系：客户端墙钟 ⊇ 服务端总耗时 ⊇ 冻结窗口；分阶段计时有窗口内也有窗口外的段，只看分布，不做加总（第 16 篇）。")
    save(s, "07-2-三个钟.svg", yy + 20)


def fig_07_order():
    s = Svg()
    y0 = s.header("八条顺序约束：只有一条被违反后能立刻报错",
                  "前五条在 orchestrator 的编排里，后三条在 Firecracker 内部。被违反后能立刻报错的只有第 2 条（靠 Firecracker 的覆盖校验兜底）；"
                  "第 1 条可能以文件系统报错露头；其余全是静默的。")
    T = y0 + 30
    rows = [
        ("1", "存档时内存与磁盘在同一个暂停窗口里", "客户机看到两个时刻的世界", NAT, "部分"),
        ("2", "读档时暂停之后才导出脏页、才物化", "内容文件漏页", OK, "报错"),
        ("3", "清连接跟踪表在恢复运行之前完成", "跨越读档的连接挂死", RISK, "静默"),
        ("4", "账本基准与 Firecracker 脏页记录同时重置", "下一代位图区间错位 → 漏页", RISK, "静默"),
        ("5", "回滚完成后先更新账本、再等 envd", "下次存档差分算错父亲", RISK, "静默"),
        ("6", "Firecracker 里先写内存、再恢复设备", "网卡读到旧时间线的队列，收包卡死", RISK, "静默"),
        ("7", "VMGenID 在内存写回之后", "客户机不知道时间被回拨", RISK, "静默"),
        ("8", "设备队列页在清零后重新标脏", "下一代差分漏掉这些页", RISK, "静默"),
    ]
    y = T
    for n, c, bad, role, lab in rows:
        num(s, M + 14, y + 25, n)
        box(s, M + 40, y, 640, 50, WHITE, None, c, 15, 14, align="start")
        box(s, M + 700, y, 640, 50, WHITE, None, bad, 15, 13.5, align="start")
        s.pill(W - M - 60, y + 25, lab, role, 13)
        y += 60
        if n == "5":
            s.line(M, y + 2, W - M, y + 2, FCR[1], 1.4, dash="6 4")
            s.text(M + 40, y + 24, "以下在 Firecracker 内部", 12.5, FCR[2], 600)
            y += 36
    s.text(M + 40, T - 8, "约束", 13, SUB, 600)
    s.text(M + 700, T - 8, "被违反后", 13, SUB, 600)
    yy = s.footer(y + 6, "注：改代码时，这张表比任何测试都更早发出警告；对应的不变量清单见第 13 篇。")
    save(s, "07-3-八条顺序约束.svg", yy + 20)


# ------------------------------------------------------------------ 第 8 篇
def fig_08_tracking():
    s = Svg()
    y0 = s.header("三种脏页跟踪：谁抓到这次写、记在哪、要不要陷出",
                  "客户机写内存不经过宿主代码，只有管第二层页表的 KVM 和 CPU 自己看得见。软件写保护每页首次写陷出一次；"
                  "uffd 写保护走用户态故障；HDBSS 由 CPU 顺手写进缓冲区，退出时再汇总。三者给上层的是同一张位图。")
    T = y0 + 40
    cols = [
        (FCR, "KVM 写保护", ["页设成只读", "首次写 → 权限故障 → 陷出", "KVM 在位图里置位、改回可写", "Firecracker 取走位图"], "每页首次写：一次陷出", "任何 KVM"),
        (KEY, "userfaultfd 写保护", ["读缺页填进来：保留写保护", "写缺页填进来：不保留", "之后再写 → 用户态故障", "在内存且没写保护 = 写过"], "一次用户态往返",
         "原生快照在 x86 上用；ARM 适配版这条路被注释掉"),
        (OK, "HDBSS（ARMv9.5，鲲鹏 950）", ["CPU 把脏页地址写进每个 vCPU 的缓冲区", "不写保护，不为记脏页陷出", "任何原因退出时，KVM 汇总进位图",
                                          "暂停本身会让每个 vCPU 退出"], "≈ 0", "需要内核支持、VHE 模式"),
    ]
    cw = (W - 2 * M - 48) / 3
    for i, (role, t, items, cost, cond) in enumerate(cols):
        x = M + i * (cw + 24)
        band(s, x, T, cw, 380, role, t)
        yy = T + 60
        for k, it in enumerate(items):
            box(s, x + 18, yy, cw - 36, 44, WHITE, None, it, 13, 13)
            if k < len(items) - 1:
                arrow(s, [(x + cw / 2, yy + 46), (x + cw / 2, yy + 58)], MUTED, 1.2)
            yy += 60
        s.text(x + 20, yy + 20, "首次写代价：" + cost, 13.5, role[2], 600)
        for k, ln in enumerate(wrap("条件：" + cond, cw - 40, 12.5)):
            s.text(x + 20, yy + 46 + k * 19, ln, 12.5, SUB)
    yy2 = s.footer(T + 410, "注：本方案用第一和第三种：有 HDBSS 用硬件，没有就退回 KVM 写保护。两者对上层是同一个接口，所以降级对上层不可见，必须主动报出来。")
    save(s, "08-1-三种脏页跟踪.svg", yy2 + 20)


def fig_08_epoch():
    s = Svg()
    y0 = s.header("纪元：每次写快照或读档都把脏页记录清零",
                  "KVM 取位图是“破坏性读”：取走的同时清空。所以每个存档的位图恰好是“父亲那一刻到这一刻”之间写过的页，"
                  "这就是纪元。读取前后都要先把信息放稳妥，否则后面一失败，这些页脏过的事实就永远丢了。")
    T = y0 + 60
    x0, x1 = M + 60, W - M - 40
    s.line(x0, T + 60, x1, T + 60, SUB, 2, end=True)
    marks = [(x0 + 60, "ck1 全量根", OK), (x0 + 420, "ck2", CTL), (x0 + 780, "读档回 ck1", RISK), (x0 + 1120, "ck3", CTL)]
    for x, lab, role in marks:
        s.line(x, T + 40, x, T + 80, role[1], 3)
        s.text(x, T + 28, lab, 14, role[2], 600, "middle")
        s.text(x, T + 100, "清零", 12, SUB, 400, "middle")
    spans = [(marks[0][0], marks[1][0], "E(ck2)：随 ck2 落地"), (marks[1][0], marks[2][0], "活跃脏页 L：读档时并进回滚集"),
             (marks[2][0], marks[3][0], "E(ck3)：父亲是 ck1")]
    for a, b, t in spans:
        s.rect(a + 8, T + 120, b - a - 16, 40, GST[0], GST[1], 1.2, rx=8)
        s.text((a + b) / 2, T + 146, t, 13, GST[2], 600, "middle")
    T2 = T + 210
    s.text(M, T2, "取位图的三个场合，都遵守“先放稳妥，再做可能失败的事”", 15, INK, 600)
    rows = [["写差分快照", "写文件失败 → 把取出的位图放回备份位图；写成功才清零"], ["原地回滚", "取出来立刻放进备份位图，再往下走"],
            ["导出脏页位图接口", "取出来先放进备份位图，再写文件；不清零"]]
    table(s, M, T2 + 20, [300, W - 2 * M - 300], rows, ts=14)
    yy = s.footer(T2 + 190, "注：Firecracker 自己写客户机内存（网卡收包、设备队列）不经过 KVM，要自己标进备份位图；写快照取的是两份位图的并集。")
    save(s, "08-2-纪元与破坏性读.svg", yy + 20)


def fig_08_degrade():
    s = Svg()
    y0 = s.header("能力随硬件降级，但每一级都要说出来",
                  "有 HDBSS 用硬件；启用失败退回 KVM 写保护；没开跟踪就每次全量。功能都对，只是代价不同。"
                  "静默降级是最难发现的故障：功能全对、测试全过，只是慢。")
    T = y0 + 40
    levels = [(OK, "hdbss", "硬件标脏，几乎不打扰客户机", "950 默认"), (NAT, "kvm-wp", "每页首次写陷出一次；结果完全一样，只是慢", "HDBSS 启用失败，或没有 HDBSS 但显式打开跟踪"),
              (RISK, "off", "不产生位图 → 每次存档都是全量（mem_mode=full）", "没有 HDBSS 且没打开跟踪")]
    lw = 760
    y = T
    for i, (role, t, sub, when) in enumerate(levels):
        box(s, M, y, lw, 84, role, t, sub, 17, 13)
        s.text(M + lw + 20, y + 36, "什么时候：", 13, SUB, 600)
        for k, ln in enumerate(wrap(when, 300, 13)):
            s.text(M + lw + 20, y + 58 + k * 19, ln, 13, INK)
        if i < 2:
            arrow(s, [(M + 120, y + 88), (M + 120, y + 116)], role[1], 1.8)
        y += 120
    rx = M + lw + 360
    band(s, rx, T, W - M - rx, 324, CTL, "在哪里说出来")
    bullets(s, rx + 22, T + 74, ["启动日志 checkpoint capabilities 一行，带理由", "Firecracker 自报后端 hdbss / kvm-wp / off",
                                  "每次存档回报 mem_mode", "FC_HDBSS_REQUIRED=true：没有 HDBSS 就启动失败"], 13.5, 56, maxw=W - M - rx - 50)
    yy = s.footer(T + 360, "注：HDBSS 必须在所有 vCPU 创建之后启用，顺序错了调用照样成功、一条脏页都记不到；从快照加载的路径上也必须启用一次（第 8 篇）。")
    save(s, "08-3-能力降级.svg", yy + 20)


if __name__ == "__main__":
    fig_05_path()
    fig_05_layers()
    fig_05_dir()
    fig_06_ck_timeline()
    fig_06_epoch()
    fig_07_rs_timeline()
    fig_07_clocks()
    fig_07_order()
    fig_08_tracking()
    fig_08_epoch()
    fig_08_degrade()
