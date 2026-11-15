"""《E2B 沙箱快照回滚从零讲透》第 13～16 篇的配图。用法: python3 tools/figures/rb_p4.py"""
from rb_common import *  # noqa: F401,F403
from rb_common import W, M


# ------------------------------------------------------------------ 第 13 篇
def fig_13_restore_fail():
    s = Svg()
    y0 = s.header("读档的四档失败：按失败发生在哪里分级",
                  "提交点把失败切成两半：之前没动客户机，沙箱原样可用；之后动了，就是撕裂。再加上树解析不了的情形和客户机不应答的情形，"
                  "一共四档，每一档调用方的应对都不同。")
    T = y0 + 40
    start = (M, T + 15, 220, 70)
    box(s, *start, KEY, "读档失败了", None, 16)
    cols = [
        (CTL, "存档树解析不了", "没有磁盘描述、祖先缺失、丢过纪元", "chain_broken", OK, "原样，继续可用", "不要原样重试：先存一个新档，再读档"),
        (CTL, "提交点之前的其他失败", "装配视图、物化、Firecracker 校验不过", "internal", OK, "虚机原样恢复运行", "换目标重试，或先存一个新档"),
        (RISK, "提交点之后失败，或回滚调用超时", "客户机一部分在目标、一部分在现在", "torn", RISK, "撕裂：虚机保持暂停留作分析", "只能销毁重建"),
        (FCR, "回滚完成，envd 45 秒内不应答", "宿主侧已完成，虚机在目标时刻", "guest_unresponsive", NAT, "不是撕裂", "按业务决定：稍后重试命令，或重建"),
    ]
    x0 = M + 300
    cw = (W - M - x0 - 3 * 20) / 4
    for i, (r1, t, sub, reason, r2, state, todo) in enumerate(cols):
        x = x0 + i * (cw + 20)
        box(s, x, T, cw, 100, r1, t, sub, 14.5, 12)
        s.pill(x + cw / 2, T + 130, reason, KEY, 13, mono=True)
        box(s, x, T + 160, cw, 64, r2, state, None, 14)
        box(s, x, T + 240, cw, 90, WHITE, None, todo, 14, 13.5, style="outline")
        arrow(s, [(x + cw / 2, T - 24), (x + cw / 2, T - 4)], MUTED, 1.3)
    s.path(f"M{start[0] + start[2] + 4:.1f} {start[1] + 35:.1f} L{x0 - 30:.1f} {start[1] + 35:.1f} L{x0 - 30:.1f} {T - 24:.1f} "
           f"L{x0 + 3 * (cw + 20) + cw / 2:.1f} {T - 24:.1f}", MUTED, 1.3)
    s.text(M, T + 198, "沙箱状态", 14, SUB, 600)
    s.text(M, T + 290, "调用方该怎么做", 14, SUB, 600)
    yy = s.footer(T + 360, "注：45 秒刻意低于 SDK 默认的 60 秒超时，让服务端先说清发生了什么；撕裂按 Firecracker 进程这一代记，不按沙箱 ID 记。")
    save(s, "13-1-restore失败决策.svg", yy + 20)


def fig_13_degrade():
    s = Svg()
    y0 = s.header("存档的三层降级：宁可留下垃圾，也不留下坏链",
                  "写快照之前的失败删目录即可。写快照之后，差分是那段脏页的唯一记录：能正常提交就提交；不能就以隐藏条目提交，"
                  "保住纪元；连隐藏都提交不了，就标记链断，拒绝读档，直到下一次全量存档起一棵新树。")
    T = y0 + 40
    lv = [(OK, "正常提交", "条目可见、可读档；当前基准 ← 新存档"), (NAT, "隐藏提交", "列表里看不见、不能作为读档目标；位图和差分留在树里，回滚集计算照常用它"),
          (RISK, "标记链断", "拒绝一切读档（回 chain_broken）；下一次存档强制全量，起新树")]
    y = T
    for i, (role, t, sub) in enumerate(lv):
        box(s, M + i * 120, y, 760, 84, role, t, sub, 16, 13)
        if i < 2:
            arrow(s, [(M + i * 120 + 60, y + 88), (M + i * 120 + 60, y + 108), (M + (i + 1) * 120 + 20, y + 108),
                      (M + (i + 1) * 120 + 20, y + 116)], role[1], 1.6)
            s.text(M + i * 120 + 80, y + 104, "失败", 12.5, RISK[2], 600)
        y += 120
    rx = M + 1060
    band(s, rx, T, W - M - rx, 340, KEY, "三种保护状态")
    rows = [("隐藏条目", "在树里，不在接口里"), ("链断", "拒绝读档；全量根当全 1，跨树读档自动正确"), ("账本污染", "层栈已变而账本没跟上；拒绝存档，读档后恢复")]
    yy = T + 70
    for t, sub in rows:
        box(s, rx + 20, yy, W - M - rx - 40, 76, WHITE, t, sub, 15, 12.5)
        yy += 88
    yy2 = s.footer(T + 370, "注：封存已经把新写层换上、旧层还没登记进账本时，还要额外把磁盘账本标记为“已污染”（rootfs_poisoned）。")
    save(s, "13-2-三层降级.svg", yy2 + 20)


def fig_13_reasons():
    s = Svg()
    y0 = s.header("错误 reason 速查：能重试、换个做法、还是销毁重建",
                  "四个调用都不自动重发，服务端也不因客户端放弃而取消。拿到错误先看 reason：有的等一会就能重试，有的要先做别的事，"
                  "有的只能重建沙箱。")
    T = y0 + 40
    groups = [
        (OK, "可以重试", [("busy", "同沙箱另一个操作没结束，排队超时；等 Retry-After 秒"), ("sandbox_restored", "别的调用撞上了读档；重连重试"),
                        ("internal", "稍后重试或换目标；持续出现就上报")]),
        (NAT, "先做别的事", [("chain_broken", "先存一个新档，再读档"), ("rootfs_poisoned", "读档到任意已有存档，账本随之重建"),
                          ("too_many_checkpoints", "删掉不需要的，再存"), ("checkpoint_bytes_limit", "删最旧的，删当前基准几乎没用"),
                          ("disk_full", "请运维清理存档盘（整个节点的问题）")]),
        (RISK, "只能重建或按业务决定", [("torn", "撕裂，销毁重建"), ("guest_unresponsive", "已在目标时刻，客户机暂不响应；按业务决定")]),
    ]
    cw = (W - 2 * M - 40) / 3
    for i, (role, t, items) in enumerate(groups):
        x = M + i * (cw + 20)
        band(s, x, T, cw, 450, role, t)
        y = T + 64
        for r, d in items:
            s.pill(x + 24 + (len(r) * 13 * 0.61 + 22) / 2, y + 14, r, role, 13, mono=True)
            for k, ln in enumerate(wrap(d, cw - 48, 13)):
                s.text(x + 24, y + 48 + k * 20, ln, 13, INK)
            y += 78
    yy = s.footer(T + 480, "注：删除按实际发生了什么作答：不存在回 404；已生效只是清理文件失败按成功返回；账本还没改就失败回 500。")
    save(s, "13-3-错误速查.svg", yy + 20)


# ------------------------------------------------------------------ 第 14 篇
def fig_14_locks():
    s = Svg()
    y0 = s.header("两把锁：按沙箱的操作锁持有整个操作，全局账本锁只持一瞬间",
                  "同一台沙箱的存档、读档、删除串行，不同沙箱完全并行。全局锁里只算、只摘账，不读写文件、不调 Firecracker；"
                  "否则一台沙箱慢一点的磁盘操作，会让整台宿主的账本操作排队。先拿操作锁，再短暂拿全局锁，只有这一个方向，不会死锁。")
    T = y0 + 40
    sbx = ["沙箱 A", "沙箱 B", "沙箱 C"]
    lw = 320
    for i, n in enumerate(sbx):
        y = T + i * 120
        box(s, M, y, 160, 90, GST, n, None, 15)
        box(s, M + 190, y, lw, 90, CTL, "操作锁", "存档 / 读档 / 删除 全程持有\n排队超过 60 s 回 busy", 14.5, 12)
        arrow(s, [(M + 164, y + 45), (M + 186, y + 45)], INK, 1.4)
    gx = M + 190 + lw + 120
    gw = 360
    box(s, gx, T + 100, gw, 160, NAT, "全局账本锁", "持有极短：只在读写表的那一下\n锁里只算、只摘账\n不读写文件、不调 Firecracker", 16, 13)
    for i in range(3):
        y = T + i * 120 + 45
        arrow(s, [(M + 190 + lw + 4, y), (gx - 4, T + 180)], MUTED, 1.3, dash="4 4")
    rx = gx + gw + 60
    band(s, rx, T, W - M - rx, 330, OK, "全局锁里的规矩")
    bullets(s, rx + 22, T + 74, ["锁里算路径，锁外读位图、写文件", "锁里摘账收进待删列表，放锁后删", "整棵沙箱目录先改名，锁外再删",
                                  "孩子计数代替扫描", "提交是常数时间"], 13.5, 46, dot=OK[1], maxw=W - M - rx - 50)
    yy = s.footer(T + 360, "注：这些规矩是在并发长跑里一条条暴露出来的，修完后三处锁等待的 p99 从 8～22 ms 降到 0.1 ms 以下（第 18 篇）。")
    save(s, "14-1-两级锁.svg", yy + 20)


def fig_14_gen():
    s = Svg()
    y0 = s.header("代际边界：一个 Firecracker 进程就是一代，换代后旧存档全部失效",
                  "账本按代记账，不按沙箱 ID。同一个 ID 经原生 pause / resume 换了新进程，新一代从零开始，旧存档 ID 返回 not_found；"
                  "迟到的“沙箱被移除”通知发现 ID 已被活着的新一代持有，就什么也不做。")
    T = y0 + 60
    s.line(M, T + 60, W - M, T + 60, SUB, 2, end=True)
    g1 = (M + 20, T + 20, 640, 80)
    box(s, *g1, OK, "第 1 代：Firecracker 进程 #1", "ck1 · ck2 · ck3 …… 都有效", 15, 12.5)
    cut = M + 720
    s.line(cut, T, cut, T + 120, RISK[1], 3, dash="6 4")
    s.text(cut, T - 10, "换代", 15, RISK[2], 600, "middle")
    g2 = (cut + 60, T + 20, W - M - cut - 80, 80)
    box(s, *g2, CTL, "第 2 代：Firecracker 进程 #2（同一个沙箱 ID）", "看不到 ck1～ck3；第一次存档是新的全量根", 15, 12.5)
    T2 = T + 170
    rows = [["沙箱被销毁", "存档随之删除"], ["原生 pause / resume", "同一个 ID、新的进程，旧存档全部失效"], ["Firecracker 或 orchestrator 重启", "全部失效（账本启动时清空）"],
            ["宿主重启、迁移到别的机器", "全部失效"], ["沙箱里的普通程序退出、重启", "不算换代，存档照常有效"]]
    table(s, M, T2, [520, W - 2 * M - 520], rows, header=["事件", "结果"], ts=14, roles=[None, None, None, None, OK])
    yy = s.footer(T2 + 290, "注：为什么必须这样：读档是原地回滚，上一代的存档没有可以写回去的活进程；撕裂标记也按代记。")
    save(s, "14-2-代际边界.svg", yy + 20)


def fig_14_copy():
    s = Svg()
    y0 = s.header("思想实验：把存档目录完整拷走，为什么还是恢复不了",
                  "四层依赖缺一不可：恢复机制要求活着的虚机；磁盘存档只是相对模板的增量；账本不从磁盘加载；网络、块设备、内存映射都绑在原来的进程上。"
                  "有意思的是内存那一半其实已经自足：树根是全量的。")
    T = y0 + 40
    deps = [(RISK, "1. 恢复机制要求活体", "读档是往活着的 Firecracker 进程里写；原来的进程已经没了"),
            (RISK, "2. 磁盘存档不自足", "封存层只是相对模板的改动，不含模板数据，要配同一份模板和块清单"),
            (RISK, "3. 账本不从磁盘加载", "orchestrator 启动时清空目录、不读 manifest；拷回去也看不见"),
            (RISK, "4. 缺运行环境", "网络槽位、NBD 设备、页缓存状态、设备组成都要一致"),
            (OK, "内存那一半已经自足", "树根是全量，只读本地文件就能解析出任意一代的完整内存")]
    y = T
    for role, t, sub in deps:
        box(s, M, y, 900, 70, role, t, sub, 15, 12.5, align="start")
        y += 82
    rx = M + 960
    band(s, rx, T, W - M - rx, 400, KEY, "要让存档“带得走”，需要")
    bullets(s, rx + 22, T + 74, ["把磁盘层栈压平，连模板底座一起装进去", "提供单独的导出接口", "账本按事务顺序刷盘、启动时读回",
                                  "回收陈旧条目、处理格式升级", "即便如此，也恢复不了已消失的虚机：需要长期保存时用原生快照"], 13.5, 56,
            maxw=W - M - rx - 50)
    yy = s.footer(T + 430, "注：这是取舍，不是缺陷：用“绑定沙箱生命周期”换来零拷贝封存、原地回滚、只随回退跨度增长的成本（第 4 篇）。")
    save(s, "14-3-拷走目录.svg", yy + 20)


def fig_14_rolling():
    s = Svg()
    y0 = s.header("“只留最近 N 个”：合并开启时条目数收敛，关掉就无限增长",
                  "每次删最旧的，它总是下一个存档的父亲，只能隐藏；它只有一个孩子，随即被合并进去。所以可见存档稳定在 N 个，"
                  "条目总数不超过 2N + 1。关掉合并，或宿主没开脏页跟踪（每个存档都是全量根，不会合并），隐藏条目就越积越多。")
    T = y0 + 40
    cx0, cy0, cw, ch = M + 80, T + 20, 900, 340
    s.line(cx0, cy0 + ch, cx0 + cw, cy0 + ch, SUB, 1.5, end=True)
    s.line(cx0, cy0 + ch, cx0, cy0, SUB, 1.5, end=True)
    s.text(cx0 + cw, cy0 + ch + 28, "时间 / 存档次数", 13, SUB, 400, "end")
    s.text(cx0 - 12, cy0 - 8, "条目数", 13, SUB, 400, "start")
    n = 20
    pts_on = []
    pts_off = []
    for i in range(n + 1):
        x = cx0 + i * cw / n
        k = min(i, 10)
        on = 2 * k + (1 if i > 0 else 0)
        off = i + (i - 10 if i > 10 else 0) * 0 + i
        pts_on.append((x, cy0 + ch - min(on, 21) * ch / 42))
        pts_off.append((x, cy0 + ch - min(off, 40) * ch / 42))
    s.path("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts_off), RISK[1], 2.4)
    s.path("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts_on), OK[1], 2.4)
    yl = cy0 + ch - 21 * ch / 42
    s.line(cx0, yl, cx0 + cw, yl, OK[1], 1, dash="5 4")
    s.text(cx0 + cw - 8, yl - 10, "上界 2N + 1", 13, OK[2], 600, "end")
    s.text(pts_off[-6][0] - 10, pts_off[-6][1] - 14, "关掉合并：线性增长", 13.5, RISK[2], 600, "end")
    s.text(pts_on[14][0], pts_on[14][1] + 26, "合并开启：稳定", 13.5, OK[2], 600, "middle")
    rx = cx0 + cw + 80
    band(s, rx, T, W - M - rx, 360, KEY, "在字节上限下删哪个")
    rows = [(RISK, "删当前基准", "几乎腾不出：只能隐藏"), (NAT, "删最旧的", "并进下一个，释放两者重叠的页"), (OK, "读档到较早的存档，再删之后那一支", "释放最彻底")]
    yy = T + 70
    for role, t, sub in rows:
        box(s, rx + 20, yy, W - M - rx - 40, 80, role, t, sub, 14.5, 12.5)
        yy += 92
    yy2 = s.footer(T + 400, "注：示意图，非实测曲线。实测对照见第 18 篇：只留最近 10 个，关合并 10 分钟就把链深推到上千、写掉半个多 TiB，开合并则一切平稳。")
    save(s, "14-4-滚动保留收敛.svg", yy2 + 20)


# ------------------------------------------------------------------ 第 15 篇
def fig_15_roles():
    s = Svg()
    y0 = s.header("两种快照的分工与叠加：先快速试错，再固化离场",
                  "本方案管活沙箱里的高频回退：几十毫秒、同一个进程、只随改动增长。原生快照管离场：自足、可上传、能跨机器、进程死了也能恢复。"
                  "两者叠加：用 checkpoint 选定满意的状态，再用原生 pause 把它固化下来。")
    T = y0 + 40
    hw = (W - 2 * M - 60) / 2
    box(s, M, T, hw, 110, OK, "checkpoint / restore：活体原地", "高频小回退 · 几十毫秒 · 什么都不重建\n离不开活沙箱，不跨重启、不跨机器", 16, 13)
    box(s, M + hw + 60, T, hw, 110, CTL, "原生 pause / resume：自足重建", "离场、长期保存、跨机器、崩溃后恢复\n每次都停沙箱、建新进程", 16, 13)
    T2 = T + 160
    s.text(M, T2, "一个 Agent 工作流，以及底下发生了什么", 15, INK, 600)
    flow = [(KEY, "起沙箱、准备环境", None), (OK, "checkpoint S", "全量根 ≈ 0.5 s"), (WHITE, "试 A → 失败", None), (OK, "restore S", "几十 ms"),
            (WHITE, "试 B → 部分成功", None), (OK, "checkpoint B1", "增量"), (CTL, "原生 pause", "导出“开机以来写过的页”"), (CTL, "以后 resume", "新一代，从零存档")]
    flow_h(s, M, T2 + 20, W - 2 * M, flow, h=96, gap=22, ts=13.5, ss=12)
    s.text(M, T2 + 160, "原生 pause 之后本方案的存档全部失效；反方向不成立。", 13.5, RISK[2], 600)
    yy = s.footer(T2 + 190, "注：原生快照的 header 块大小从 2 MiB 变成了 4 KiB，兼容是单向的：新 orchestrator 读得了旧快照，旧 orchestrator 读新快照会拒绝启动。")
    save(s, "15-1-两种快照的分工.svg", yy + 20)


def fig_15_layers():
    s = Svg()
    y0 = s.header("原生内存增量的三层：判、存、填，修复前后",
                  "三层的粒度被锁在一起：客户机页 2 MiB → 缺页只能按 2 MiB 填 → 要求 header 块也是 2 MiB → 判据再细也要归并到 2 MiB。"
                  "只换判据，空转时仍有约 130 MiB 的“本底散写”地板；三层一起改，导出量才降到真实写入量。")
    T = y0 + 30
    rows = [["判：这一代导出哪些页", "“在内存里就算脏”（ARM 上写保护被注释掉）", "Firecracker 的写跟踪位图（4 KiB）"],
            ["存：header 记每块在哪一代", "块大小 2 MiB，逐代继承", "降到 4 KiB；父代 2 MiB 的映射原样保留（= 512 个连续 4 KiB 映射）"],
            ["填：恢复时缺页", "一次 2 MiB，要求等于 header 块", "仍一次 2 MiB：整块同代直接交出；跨代按 4 KiB 拼满，拼不满就报错"]]
    table(s, M, T, [380, 460, W - 2 * M - 840], rows, header=["层", "修复前", "修复后"], ts=14, roles=[None, None, None])
    T2 = T + 200
    s.text(M, T2, "只换判据够不够（920B 测算）", 15, INK, 600)
    data = [("空转", 162, 134, 4.1), ("只读 192 MiB", 366, 148, 14.6), ("只改 12 MiB", 184, 156, 20.5), ("写 192 MiB", 382, 358, 219.8)]
    cx0 = M + 160
    bh = 18
    sc = (W - M - cx0 - 120) / 400
    y = T2 + 30
    for lab, a, b, c in data:
        s.text(cx0 - 14, y + 30, lab, 13.5, INK, 600, "end")
        for k, (v, role, nm) in enumerate(((a, RISK, "修复前"), (b, NAT, "只换判据"), (c, OK, "4 KiB 真值"))):
            s.rect(cx0, y + k * (bh + 3), max(v * sc, 2), bh, role[0], role[1], 1, rx=3)
            s.text(cx0 + v * sc + 8, y + k * (bh + 3) + 14, f"{v:g} MiB", 12, role[2], 600)
        y += 3 * (bh + 3) + 18
    legend(s, y + 14, [(RISK, "修复前导出"), (NAT, "只换判据（按 2 MiB 归并）"), (OK, "4 KiB 真实写入量")], x=cx0)
    yy = s.footer(y + 40, "注：x86 上原生增量本来就精确，这是把 ARM 补回到 x86 的水平；关大页也能精确，但缺页次数 × 512、所有沙箱失去大页，不选。")
    save(s, "15-2-原生增量三层.svg", yy + 20)


def fig_15_sinceboot():
    s = Svg()
    y0 = s.header("累积位图：在脏页记录被清零之前，把它收进“开机以来写过的页”",
                  "Firecracker 的写跟踪位图只记“上一次快照或回滚以来”。存过档、读过档的沙箱再做原生 pause，只看它就会漏导之前写过的页，"
                  "而 pause 照样报成功。所以 orchestrator 为每台虚机维护一个累积集合，任何一次没能并进去，就整体标为不可信、退回驻留判据。")
    T = y0 + 60
    s.line(M + 40, T + 40, W - M - 300, T + 40, SUB, 2, end=True)
    evs = [(M + 140, "全量存档", "先导出活跃位图"), (M + 420, "增量存档", "这一代的位图"), (M + 700, "读档", "活跃脏页 + 回滚集"), (M + 980, "增量存档", "这一代的位图")]
    for x, t, what in evs:
        s.line(x, T + 20, x, T + 60, FCR[1], 3)
        s.text(x, T + 10, t + "：清零", 13.5, FCR[2], 600, "middle")
        box(s, x - 110, T + 110, 220, 56, WHITE, None, what, 13.5, 13)
        arrow(s, [(x, T + 64), (x, T + 106)], MUTED, 1.2)
        arrow(s, [(x, T + 170), (x, T + 214)], GST[1], 1.5)
    box(s, M + 20, T + 220, 1100, 70, GST, "“开机以来写过的页”集合（每台虚机一个）", None, 16)
    px = W - M - 260
    box(s, px, T + 120, 260, 170, CTL, "原生 pause", "集合 ∪ 当前写跟踪位图\n→ 按并集导出", 16, 13)
    arrow(s, [(M + 1124, T + 255), (px - 4, T + 255)], GST[1], 1.8)
    T2 = T + 330
    box(s, M, T2, (W - 2 * M - 40) / 2, 90, RISK, "任何一次没并进去", "整体标“不完整”，pause 退回“在内存里就算脏”：导多了只费时间，不会错", 15, 12.5)
    box(s, M + (W - 2 * M + 40) / 2, T2, (W - 2 * M - 40) / 2, 90, OK, "从不存档的沙箱", "集合一直是空的，判据照常用 Firecracker 自己的位图", 15, 12.5)
    yy = s.footer(T2 + 120, "注：磁盘那一半：原生 pause 导出时交出所有封存层和当前写层，按“最上层有就取最上层”压平导出，和沙箱自己读到的一致。")
    save(s, "15-3-累积位图.svg", yy + 20)


def fig_15_compare():
    s = Svg()
    y0 = s.header("950 同档位：本方案与原生 pause / resume 的客户端耗时中位数",
                  "改动越小，本方案的优势越大：0 MiB 时存档 17.2 ms 对 pause 251.9 ms。两组测试的负载构造和宿主条件不同，只能看量级，不是精确倍数。"
                  "256 MiB 时读档和 resume 数字接近，但 resume 返回时内存还没加载，之后还要再付约 112 ms。")
    T = y0 + 40
    tiers = [0, 16, 32, 64, 128, 256]
    ck = [17.2, 23.8, 30.5, 41.4, 73.0, 125.5]
    pz = [251.9, 262.7, 284.6, 308.8, 346.8, 429.9]
    rs = [22.4, 30.4, 36.4, 46.0, 67.8, 105.6]
    rm = [109.3, 107.2, 108.8, 106.1, 108.9, 120.7]
    hw = (W - 2 * M - 80) / 2
    for p, (title, a, b, la, lb, ymax) in enumerate((("存档 vs pause", ck, pz, "checkpoint", "pause", 450),
                                                     ("读档 vs resume", rs, rm, "restore", "resume", 150))):
        x0 = M + p * (hw + 80) + 50
        cw = hw - 60
        ch = 300
        y0b = T + 30 + ch
        s.text(x0 - 50, T + 10, title + "（ms）", 15, INK, 600)
        for g in range(0, ymax + 1, ymax // 3):
            yy = y0b - g / ymax * ch
            s.line(x0, yy, x0 + cw, yy, HAIR, 1)
            s.text(x0 - 8, yy + 4, str(g), 11.5, MUTED, 400, "end")
        gw = cw / len(tiers)
        bw = gw * 0.32
        for i, t in enumerate(tiers):
            gx = x0 + i * gw + gw / 2
            for k, (v, role) in enumerate(((a[i], OK), (b[i], CTL))):
                h = v / ymax * ch
                bx = gx - bw - 2 if k == 0 else gx + 2
                s.rect(bx, y0b - h, bw, h, role[0], role[1], 1.1, rx=3)
                s.text(bx + bw / 2, y0b - h - 6, f"{v:g}", 11, role[2], 600, "middle")
            s.text(gx, y0b + 20, f"{t} MiB", 12, SUB, 400, "middle")
        legend(s, y0b + 52, [(OK, la), (CTL, lb)], x=x0)
    yy = s.footer(T + 420, "注：原生 pause 约 245 ms 固定开销 + 每 MiB 0.52 ms（六档拟合，只是趋势）；本方案数据来自第 17 篇的十二档测试。")
    save(s, "15-4-耗时并列.svg", yy + 20)


# ------------------------------------------------------------------ 第 16 篇
def fig_16_clocks():
    s = Svg()
    y0 = s.header("判定口径：六件事钉死在对自己不利的一侧",
                  "三个钟里只用最大、最保守、使用者唯一能复测的客户端墙钟判定；只判增量存档和原地读档；看中位数，p99 并列；"
                  "按改动量分档；全量单列；出现一个 full 整轮作废。冻结窗口只作解释，用它判定等于放水。")
    T = y0 + 40
    rows = [["量什么钟", "客户端墙钟", "最大、最保守、可复测"], ["哪类存档", "增量（mem_mode=incremental）", "高频回退里的每一次"],
            ["哪类读档", "原地（沙箱 ID 和进程不变）", "另起一台是原生的路径"], ["统计量", "p50 判定，p99 并列", "单次会抖；样本少时 p99 = 最大值"],
            ["分档变量", "名义改动量，内存:文件 = 3:1", "成本只看改了多少，不看内存多大"], ["全量", "单列，不参与判定", "一次性成本，作增量的分母"],
            ["判定前提", "出现 full 整轮作废", "防止悄悄退化成全量"]]
    table(s, M, T, [240, 460, 480], rows, header=["维度", "本书取法", "为什么"], ts=14)
    rx = M + 1240
    band(s, rx, T, W - M - rx, 420, KEY, "三个钟的包含关系")
    nest = [(CTL, "客户端墙钟"), (NAT, "服务端总耗时"), (FROZEN, "冻结窗口")]
    for k, (role, t) in enumerate(nest):
        pad = 20 + k * 24
        s.rect(rx + pad, T + 60 + k * 50, W - M - rx - 2 * pad, 290 - k * 100, role[0], role[1], 1.3, rx=10)
        s.text(rx + pad + 14, T + 86 + k * 50, t, 14, role[2], 600)
    s.text(rx + 20, T + 376, "墙钟达标 ⇒ 冻结窗口必然达标", 13, SUB)
    s.text(rx + 20, T + 398, "反之不成立", 13, SUB)
    yy = s.footer(T + 450, "注：判定线没有限定改动量，所以结论必然是“改动量在多少以内达标”，而不是一句笼统的“达标”。")
    save(s, "16-1-三个钟与口径.svg", yy + 20)


def fig_16_distort():
    s = Svg()
    y0 = s.header("负载构造的三种失真，以及“预热 + 原地覆写”",
                  "判定表第一列“改动 N MiB”成立的前提是：标签上的 N 等于服务端实际处理的量。分配成本混进档位、写放大、负载放错层，"
                  "都会让这个前提失效。解法是先一次撑到最大档，之后每档用 conv=notrunc 只覆写前 N MiB，数据用随机源。")
    T = y0 + 40
    cols = [(RISK, "失真一：分配成本混进档位", "第一次写新内存要清零、建页表，第一次写新文件要分配块；每档重新分配，档位越大混进越多，斜率被抬高"),
            (RISK, "失真二：写放大", "用 shell 拼接造内存负载：缓冲区复制、扩容中间态、释放后再缺页；实测差分是名义量的好几倍"),
            (RISK, "失真三：负载放错层", "快照只带回覆盖范围内的东西；放在范围外，测出来既是零成本，也是假通过")]
    cw = (W - 2 * M - 40) / 3
    for i, (role, t, sub) in enumerate(cols):
        box(s, M + i * (cw + 20), T, cw, 140, role, t, sub, 15, 12.5)
    T2 = T + 180
    s.text(M, T2, "解法", 16, OK[2], 600)
    steps = [(OK, "1. 预热", "内存文件、磁盘文件一次撑到最大档位；这一次承担全部分配成本，不计入任何档位"),
             (OK, "2. 原地覆写", "每档 dd ... conv=notrunc 只覆写前 N MiB；没有 notrunc 会先截成空，失真一回来"),
             (OK, "3. 随机数据", "全零页会被稀疏、去重、压缩特殊对待；随机数据量到的才是最坏也最诚实的情况")]
    for i, (role, t, sub) in enumerate(steps):
        box(s, M + i * (cw + 20), T2 + 20, cw, 110, role, t, sub, 15, 12.5)
    T3 = T2 + 170
    hw = (W - 2 * M - 40) / 2
    box(s, M, T3, hw, 80, GST, "/dev/shm（内存文件系统）", "只弄脏内存页，不落磁盘", 15, 12.5)
    box(s, M + hw + 40, T3, hw, 80, STO, "根文件系统上的普通文件（走缓存写 + sync）", "进磁盘层，同时在内存里留一份文件缓存", 15, 12.5)
    yy = s.footer(T3 + 110, "注：读表的固定预期：实测内存差分 ≈ 名义内存 + 名义文件；实测磁盘层 ≈ 名义文件。偏离这个关系，先查负载，再看时间。")
    save(s, "16-2-三种失真.svg", yy + 20)


def fig_16_iter():
    s = Svg()
    y0 = s.header("一次分档迭代：改、存、读档回去、校验、删",
                  "cpB 每次都挂在基点 cpA 下面、用完就删，链深不会随迭代变深；从 cpB 读档回 cpA 的回滚集正好是本档造的改动，"
                  "所以读档那一列也能按档位读；每次都校验现场，耗时只有在“回对了”的前提下才有意义。")
    T = y0 + 50
    steps = [(GST, "处在基点 cpA", None), (GST, "造本档改动", "内存 3 : 文件 1"), (CTL, "增量存档 → cpB", "记墙钟、分段、产物"),
             (CTL, "读档回 cpA", "撤销本档改动"), (OK, "校验现场", "落错记异常"), (STO, "删除 cpB", "链深配平")]
    flow_h(s, M, T, W - 2 * M, steps, h=100, gap=34, ts=15, ss=12.5)
    arrow(s, [(W - M - 100, T + 104), (W - M - 100, T + 150), (M + 100, T + 150), (M + 100, T + 104)], MUTED, 1.5, dash="5 4")
    s.text(W / 2, T + 172, "下一次迭代", 13, SUB, 400, "middle")
    T2 = T + 220
    cols = [(OK, "判失败", "mem_mode 出现 full\n读档后现场不一致"), (NAT, "不判失败", "超过 200 / 100 ms 目标线：那是结论，不是故障"),
            (KEY, "每轮", "新沙箱跑几遍，遍与遍之间查漂移；小档样本多给")]
    cw = (W - 2 * M - 40) / 3
    for i, (role, t, sub) in enumerate(cols):
        box(s, M + i * (cw + 20), T2, cw, 100, role, t, sub, 15, 12.5)
    yy = s.footer(T2 + 130, "注：正确性可以远程验，性能必须在宿主上测：脏页后端、存档盘文件系统、产物实际大小、服务端分段计时都只能在宿主上读到。")
    save(s, "16-3-分档迭代.svg", yy + 20)


if __name__ == "__main__":
    fig_13_restore_fail()
    fig_13_degrade()
    fig_13_reasons()
    fig_14_locks()
    fig_14_gen()
    fig_14_copy()
    fig_14_rolling()
    fig_15_roles()
    fig_15_layers()
    fig_15_sinceboot()
    fig_15_compare()
    fig_16_clocks()
    fig_16_distort()
    fig_16_iter()
