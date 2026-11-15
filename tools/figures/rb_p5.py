"""《E2B 沙箱快照回滚从零讲透》第 17～20 篇的配图。用法: python3 tools/figures/rb_p5.py"""
from rb_common import *  # noqa: F401,F403
from rb_common import W, M


def axes(s, x0, y0, w, h, ymax, step, unit="", xlabel=None):
    """y0 是底边。画水平网格与刻度。"""
    g = 0
    while g <= ymax + 1e-9:
        yy = y0 - g / ymax * h
        s.line(x0, yy, x0 + w, yy, HAIR, 1)
        s.text(x0 - 8, yy + 4, f"{g:g}{unit}", 11.5, MUTED, 400, "end")
        g += step
    if xlabel:
        s.text(x0 + w, y0 + 40, xlabel, 12.5, SUB, 400, "end")


def polyline(s, pts, role, sw=2.4, dash=None, dots=True):
    s.path("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts), role[1], sw, dash)
    if dots:
        for x, y in pts:
            s.circle(x, y, 4, "#FFFFFF", role[1], 2)


# ------------------------------------------------------------------ 第 17 篇
def fig_17_tiers():
    s = Svg()
    y0 = s.header("950 混合负载各档：存档、读档的客户端耗时中位数",
                  "2 GiB 沙箱、HDBSS、ext4；内存 : 文件 = 3 : 1。128 MiB 以内两项都在参考线内；256 MiB 读档 105.6 ms，开始超线；"
                  "512 MiB 极限档两项都超。折线只连接已测档位，看趋势用，不是连续区间的保证。")
    T = y0 + 50
    tiers = [0, 4, 8, 16, 32, 64, 128, 256, 512]
    ck = [17.2, 19.3, 20.8, 23.8, 30.5, 41.4, 73.0, 125.5, 235.2]
    rs = [22.4, 25.5, 28.1, 30.4, 36.4, 46.0, 67.8, 105.6, 196.2]
    x0, w, h = M + 60, W - 2 * M - 120, 400
    yb = T + h
    ymax = 250
    axes(s, x0, yb, w, h, ymax, 50, xlabel="名义改动量（MiB），横轴按档位等距")
    xs = [x0 + 30 + i * (w - 60) / (len(tiers) - 1) for i in range(len(tiers))]
    for x, t in zip(xs, tiers):
        s.text(x, yb + 22, str(t), 12.5, SUB, 400, "middle")
    for v, role, lab in ((200, CTL, "存档参考线 200 ms"), (100, OK, "读档参考线 100 ms")):
        yy = yb - v / ymax * h
        s.line(x0, yy, x0 + w, yy, role[1], 1.4, dash="6 5")
        s.text(x0 + 8, yy - 8, lab, 12.5, role[2], 600)
    pc = [(x, yb - v / ymax * h) for x, v in zip(xs, ck)]
    pr = [(x, yb - v / ymax * h) for x, v in zip(xs, rs)]
    polyline(s, pc, CTL)
    polyline(s, pr, OK)
    for (x, yc), (_, yr), vc, vr in zip(pc, pr, ck, rs):
        cu = vc >= vr
        s.text(x, (yc - 12) if cu else (yc + 22), f"{vc:g}", 11.5, CTL[2], 600, "middle")
        s.text(x, (yr + 22) if cu else (yr - 12), f"{vr:g}", 11.5, OK[2], 600, "middle")
    legend(s, yb + 66, [(CTL, "增量存档 p50（ms）"), (OK, "读档 p50（ms）")], x=x0)
    yy = s.footer(yb + 90, "注：每档 10～30 个样本，p99 就是最大值，不能推断长期尾延迟；首次全量 0.47～0.50 s 单列，不在图中。")
    save(s, "17-1-分档耗时.svg", yy + 20)


def fig_17_phases():
    s = Svg()
    y0 = s.header("时间花在哪：128 / 256 / 512 MiB 三档的分阶段中位数",
                  "存档的增长主要在“写快照”，封存也略增但小得多；读档的增长在“物化”和 Firecracker“写回内存”，两者都随回滚量增长。"
                  "取位图约 1.6 ms、窗口外装配视图约 0.2 ms、等 envd 约 1.5 ms，基本不随档位变。")
    T = y0 + 40
    tiers = ["128 MiB", "256 MiB", "512 MiB"]
    ck = [("写快照", [62.3, 109.9, 209.8], CTL), ("封存", [7.1, 12.4, 21.9], STO)]
    rs = [("物化", [34.1, 52.9, 104.2], CTL), ("写回内存", [19.4, 33.9, 68.5], FCR), ("取位图", [1.65, 1.65, 1.65], STO)]
    hw = (W - 2 * M - 80) / 2
    for p, (title, segs) in enumerate((("存档", ck), ("读档", rs))):
        x0 = M + p * (hw + 80) + 110
        cw = hw - 160
        s.text(x0 - 110, T + 10, title + "（ms，各段中位数）", 15, INK, 600)
        sc = cw / 240
        for i, t in enumerate(tiers):
            y = T + 40 + i * 110
            s.text(x0 - 14, y + 30, t, 13.5, INK, 600, "end")
            for k, (name, vals, role) in enumerate(segs):
                v = vals[i]
                yy = y + k * 26
                s.rect(x0, yy, max(v * sc, 2), 22, role[0], role[1], 1, rx=3)
                s.text(x0 + v * sc + 8, yy + 16, f"{name} {v:g}", 12, role[2], 600)
        legend(s, T + 390, [(r, n) for n, _, r in segs], x=x0)
    yy = s.footer(T + 420, "注：各段中位数不一定出自同一次操作，后台工作也可能和关键路径重叠，所以不能直接相加。")
    save(s, "17-2-分段构成.svg", yy + 20)


def fig_17_size():
    s = Svg()
    y0 = s.header("名义改动量与实际产物大小",
                  "0 档也有约 21 MiB 的内存差分本底；文件写入先进客户机的文件缓存，所以也出现在内存差分里：纯文件 16 MiB 的内存差分约 40 MiB。"
                  "扣掉本底，内存差分约是名义总改动的 1.03～1.04 倍；磁盘层约等于名义文件写入量。")
    T = y0 + 40
    rows = [("混合 0", 0, 21.28, 0.49), ("混合 128", 128, 154.72, 32.65), ("混合 256", 256, 285.28, 64.76), ("混合 512", 512, 550.30, 128.75),
            ("纯内存 16", 16, 40.05, 0.59), ("纯文件 16", 16, 39.88, 16.65), ("只读 192", 0, 24.70, 0.50)]
    x0 = M + 170
    sc = (W - M - x0 - 160) / 560
    bh = 18
    y = T + 10
    for lab, nom, mem, disk in rows:
        s.text(x0 - 14, y + 30, lab, 13.5, INK, 600, "end")
        for k, (v, role, nm) in enumerate(((nom, KEY, "名义"), (mem, GST, "内存差分"), (disk, STO, "磁盘层"))):
            yy = y + k * (bh + 3)
            s.rect(x0, yy, max(v * sc, 2), bh, role[0], role[1], 1, rx=3)
            s.text(x0 + v * sc + 8, yy + 14, f"{v:g} MiB", 11.5, role[2], 600)
        y += 3 * (bh + 3) + 14
    legend(s, y + 16, [(KEY, "名义总改动"), (GST, "内存差分实占（st_blocks）"), (STO, "磁盘层实占")], x=x0)
    yy = s.footer(y + 44, "注：只读触碰 192 MiB 的产物和 0 档几乎一样，说明读不算脏；它比 0 档多出的约 3 MiB 混有后台写和命令执行，不能据此说 HDBSS 把读页判脏。")
    save(s, "17-3-产物大小.svg", yy + 20)


# ------------------------------------------------------------------ 第 18 篇
def fig_18_groups():
    s = Svg()
    y0 = s.header("五组优化，各作用在哪一段",
                  "单沙箱达标之后，多台沙箱同时做、反复做几个小时，暴露出的问题分散在存档和读档的各个环节，也有节点级的、和单次操作无关的长尾。")
    T = y0 + 40
    lanes = [("窗口外准备", 280), ("冻结窗口", 560), ("窗口外收尾", 280), ("节点级", W - 2 * M - 1120 - 60)]
    x = M
    xs = {}
    for name, w in lanes:
        role = FROZEN if name == "冻结窗口" else (RISK if name == "节点级" else KEY)
        s.rect(x, T, w, 470, role[0], role[1], 1.2, rx=12, dash="6 4" if name == "冻结窗口" else None)
        s.text(x + 16, T + 28, name, 14.5, role[2], 600)
        xs[name] = (x, w)
        x += w + 20
    items = [
        ("窗口外收尾", 0, CTL, "1. 跨沙箱等待", "锁里只算；锁外读写、删文件；不再整份重写 index.json"),
        ("冻结窗口", 0, FCR, "2. 缩短冻结窗口", "不 fsync；位图按字跳零；连续页合批读"),
        ("窗口外准备", 0, FCR, "2. 装配视图前移", "读不可变的封存层，挪出窗口"),
        ("窗口外收尾", 1, FCR, "2. 层文件移动后移", "跨文件系统是拷贝，放到恢复之后"),
        ("冻结窗口", 1, NAT, "3. 网络清理", "与回滚并行；攒批一次整表扫描；按实测选路"),
        ("窗口外准备", 1, NAT, "3. 代理全双工", "修复流式命令偶发截断"),
        ("冻结窗口", 2, OK, "4. 历史增长", "位图批量装配视图；块归属索引"),
        ("窗口外收尾", 2, OK, "4. 回收与合并", "层引用计数回收；隐藏条目合并"),
        ("节点级", 0, RISK, "5. GC 长尾", "MADV_POPULATE 把缺页挪进系统调用"),
        ("节点级", 1, KEY, "指标纠偏", "读盘量改为本沙箱自计"),
    ]
    for lane, k, role, t, sub in items:
        x, w = xs[lane]
        box(s, x + 16, T + 50 + k * 135, w - 32, 115, role, t, sub, 14.5, 12.5)
    yy = s.footer(T + 500, "注：每组按“现象 → 根因 → 改法 → 验证”展开见正文；最终长测里 GC 停顿最长 2.8 ms，冻结窗口里等连接跟踪清理的中位数 2.2 ms。")
    save(s, "18-1-五组优化.svg", yy + 20)


def fig_18_gc():
    s = Svg()
    y0 = s.header("GC 长停顿怎么跨沙箱传染，MADV_POPULATE 怎么切断",
                  "Go 垃圾回收要短暂“停住整个世界”，必须等所有处理器停下。某个线程在文件映射上拷贝时缺页，分配页、计入内存控制组、触发回收，"
                  "睡在内核里，它的处理器一直是“运行中”，抢占够不着，STW 只能干等，别的沙箱的冻结窗口随之被拉长。")
    T = y0 + 40
    chain = [(STO, "拷贝层数据", "在 MAP_SHARED 映射上"), (STO, "缺页（用户态）", "分配页"), (NAT, "计入内存控制组", "256 GiB 早已被页缓存填满"),
             (RISK, "在回收里睡着", "86% 睡在回收限流上"), (RISK, "STW 等不到它", "长停顿 100% 花在等处理器停下")]
    flow_h(s, M, T, W - 2 * M, chain, h=90, gap=30, ts=14.5, ss=12)
    box(s, M, T + 120, W - 2 * M, 60, OK, "改法：拷贝前对范围调用 madvise(MADV_POPULATE_READ / WRITE)：缺页、计入、回收都发生在系统调用里，STW 不用等处于系统调用中的线程",
        None, 14.5)
    T2 = T + 220
    s.text(M, T2, "STW 停顿 p99（ms），各轮长跑", 15, INK, 600)
    data = [("long1", 205.6), ("long2", 226.3), ("long3 减垃圾", 268.5), ("long4", 277.0), ("long5 +MADV", 97.6), ("long6 上限 60", 1.2),
            ("long7 +合并", 1.3), ("最终长测", 1.1)]
    x0, w, h = M + 60, W - 2 * M - 80, 240
    yb = T2 + 30 + h
    axes(s, x0, yb, w, h, 300, 100)
    gw = w / len(data)
    for i, (lab, v) in enumerate(data):
        role = RISK if v > 50 else OK
        bx = x0 + i * gw + gw * 0.25
        bh = v / 300 * h
        s.rect(bx, yb - bh, gw * 0.5, max(bh, 2), role[0], role[1], 1.1, rx=3)
        s.text(bx + gw * 0.25, yb - bh - 8, f"{v:g}", 12, role[2], 600, "middle")
        s.text(bx + gw * 0.25, yb + 20, lab, 12, SUB, 400, "middle")
    yy = s.footer(yb + 46, "注：“减垃圾”之后次数减半，长停顿却没少，证明不是垃圾太多；最后的改善是 MADV_POPULATE、层回收、合并叠加的结果，不能全归功于一处改动。")
    save(s, "18-2-GC长停顿.svg", yy + 20)


def fig_18_growth():
    s = Svg()
    y0 = s.header("长跑中的增长：修复前后对比",
                  "左：每台沙箱最多 60 个可见存档，30 分钟长跑的存档盘增长峰值。修复前隐藏存档无限积累、层文件从不回收；"
                  "加上层回收和合并后，目录稳定在约 1240，峰值从 340.6 GiB 降到约 90 GiB。右：只留最近 10 个，读档中位数随时间的变化，"
                  "视图装配改成位图批量处理后不再跟着块数涨。")
    T = y0 + 40
    hw = (W - 2 * M - 80) / 2
    s.text(M, T + 10, "存档盘增长峰值（GiB）", 15, INK, 600)
    bars = [("修复前", 340.6, RISK), ("层回收 + 合并", 90.5, OK)]
    x0, h = M + 60, 300
    yb = T + 40 + h
    axes(s, x0, yb, hw - 80, h, 400, 100)
    for i, (lab, v, role) in enumerate(bars):
        bx = x0 + 60 + i * 220
        bh = v / 400 * h
        s.rect(bx, yb - bh, 120, bh, role[0], role[1], 1.2, rx=4)
        s.text(bx + 60, yb - bh - 8, f"{v:g}", 13, role[2], 600, "middle")
        s.text(bx + 60, yb + 22, lab, 13, SUB, 400, "middle")
    x2 = M + hw + 80
    s.text(x2, T + 10, "读档 p50（ms），每 10 分钟一段", 15, INK, 600)
    a = [90.9, 109.2, 123.9, 133.6, 138.2, 141.9]
    b = [71.0, 78.6, 81.7, 82.1, 83.2, 84.1]
    cx0 = x2 + 60
    cw = hw - 100
    axes(s, cx0, yb, cw, h, 160, 40)
    xs = [cx0 + 30 + i * (cw - 60) / 5 for i in range(6)]
    for x, lab in zip(xs, ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60"]):
        s.text(x, yb + 22, lab, 12, SUB, 400, "middle")
    pa = [(x, yb - v / 160 * h) for x, v in zip(xs, a)]
    pb = [(x, yb - v / 160 * h) for x, v in zip(xs, b)]
    polyline(s, pa, RISK)
    polyline(s, pb, OK)
    s.text(pa[-1][0], pa[-1][1] - 14, "141.9", 12, RISK[2], 600, "middle")
    s.text(pb[-1][0], pb[-1][1] + 24, "84.1", 12, OK[2], 600, "middle")
    legend(s, yb + 56, [(RISK, "逐块哈希表装配"), (OK, "位图 + 区间批量装配")], x=cx0)
    s.text(x0, yb + 56, "单位 GiB；对照组同为上限 60", 12.5, SUB)
    yy = s.footer(yb + 84, "注：修复后块数比修复前同期还略多，读档却更快；剩下的缓慢增长来自客户机后台持续写内存让回滚集真实变大，是真实工作量。")
    save(s, "18-3-长跑增长.svg", yy + 20)


# ------------------------------------------------------------------ 第 19 篇
def fig_19_layers():
    s = Svg()
    y0 = s.header("三层测试，各证什么",
                  "单元测试与属性测试守部件和不变量；整机验收在目标机上证明整体正确、量耗时、跑并发和长跑；补充用例覆盖盲区、边界和故障注入。"
                  "上机的一站式入口是 run.sh 的 smoke / func / perf / long / hdbss 几档。")
    T = y0 + 40
    lv = [(CTL, "单元测试与属性测试", "代码仓库里，和被测代码放在一起", "部件与不变量；随机操作序列对照参照模型；故意注入错误，确认测试会失败"),
          (OK, "整机验收", "五个单文件脚本，拷到目标机就能跑", "59 项正确性检查、分档性能、并发、长跑；故意不抽公共模块"),
          (NAT, "补充用例与开发工具", "20 个用例 + 诊断工具箱", "生命周期竞争、文件系统边界、时间与 CPU、串口、故障注入、提交点后失败、和原生快照的组合")]
    y = T
    for i, (role, t, where, what) in enumerate(lv):
        pad = (2 - i) * 120
        box(s, M + pad, y, W - 2 * M - 2 * pad, 110, role, t, where + "\n" + what, 16, 12.5)
        y += 126
    s.text(M, y + 20, "几条约定：打 RPM 包时不跑单元测试；正确性和性能分开跑；都在宿主上以 root 跑。", 14, INK)
    yy = s.footer(y + 50, "注：正确性可以远程验，性能必须在宿主上测，因为条件标签只能在宿主上读到（第 16 篇）。")
    save(s, "19-1-三层测试.svg", yy + 20)


def fig_19_59():
    s = Svg()
    y0 = s.header("59 项检查：一条三代直链，覆盖现场的每一部分",
                  "三代 A → B → C，每代换掉全部观测点；读档前先断言 9 项现场三代各不相同、心跳的 PID 和启动时刻三代相同，"
                  "证明“全部一致”这句话真的有区分度。最硬的一项：kill -9 掉的心跳进程，读档后带着原 PID 活回来。")
    T = y0 + 40
    obs = [(GST, "内存标记", "/dev/shm 小文件：证明内存被搬回来"), (GST, "内存大块", "/dev/shm 128 MB 随机数据的 MD5：抓局部漏页"),
           (STO, "磁盘标记和大文件", "根文件系统，不写 /home/user"), (STO, "被删的文件", "A 建、B 删：回到 A 必须复活"),
           (STO, "权限位", "600 / 640 / 755"), (OK, "进程", "kill -9 后复活，PID 和启动时刻不变")]
    cw = (W - 2 * M - 5 * 16) / 6
    for i, (role, t, sub) in enumerate(obs):
        box(s, M + i * (cw + 16), T, cw, 110, role, t, sub, 15, 12)
    T2 = T + 150
    rows = [["1. 建三代现场", "3 次“还能干活”（每次 5 项）+ mem_mode 2 项 + 区分度 2 项", "19"],
            ["2. 逐级回退 C → B → A", "1 次“还能干活” + 2 次“现场一致”（每次 2 项）", "9"],
            ["3. 跨两代前滚 A → C", "1 次“还能干活” + 1 次“现场一致”", "7"],
            ["4. A、C 交替 3 轮", "1 次“还能干活” + 6 次“现场一致”", "17"],
            ["5. kill -9 心跳后回滚到 A", "1 次“还能干活” + 1 次“现场一致”", "7"]]
    table(s, M, T2, [360, W - 2 * M - 480, 120], rows, header=["部分", "检查", "项数"], ts=14)
    s.text(W - M - 110, T2 + 300, "合计 59", 17, OK[2], 600)
    yy = s.footer(T2 + 330, "注：“还能干活”5 项：能执行命令、根文件系统能写能读回、能起新进程、新进程算对、后台进程仍在推进（只看计数器，不看时间）。")
    save(s, "19-2-59项检查.svg", yy + 20)


def fig_19_matrix():
    s = Svg()
    y0 = s.header("测试矩阵：950 上已证的、待证的",
                  "默认功能回归通过，不代表没跑的专项也通过；几分钟的混合操作，不能替代小时级的稳定性。缺口都列出来，留在第 20 篇的待办里。")
    T = y0 + 30
    rows = [("存档读档后照常干活，现场回到那一刻（59 项）", "已证", "10 次读档全部一致"), ("部署前提与二进制配套", "已证", "预检五项通过"),
            ("补充用例（默认 16 个）", "已证", "重启 / 注入 / 配额 / 提交点后失败 4 个跳过"), ("存档后原生 pause、干净沙箱原生 pause", "已证", ""),
            ("短时并发：16 台突发", "已证", "93 次读档全部一致"), ("读档后立刻请求", "已证", "200 次读档、400 条命令全成功"),
            ("HDBSS 三级证据", "已证", "仅默认缓冲区大小"), ("分档性能、串行长尾", "已证", "第 17 篇"),
            ("树形语义脚本", "待证", "950 上还没有结果"), ("小时级长跑、滚动保留资源收敛", "待证", ""), ("重启、故障注入、配额专项", "待证", ""),
            ("跨树读档端到端", "待证", "只有单元测试"), ("HDBSS 启用顺序断言", "待证", "只靠代码位置保证"), ("不同 HDBSS 缓冲区大小比较", "待证", "")]
    y = T
    for t, st, note in rows:
        role = OK if st == "已证" else NAT
        box(s, M, y, 760, 34, WHITE, None, t, 13.5, 13.5, align="start")
        s.pill(M + 820, y + 17, st, role, 13)
        if note:
            s.text(M + 880, y + 22, note, 13, SUB)
        y += 40
    yy = s.footer(y + 6, "注：两种脏页后端给上层的是同一种位图，正确性论证可以沿用；性能数字不能跨机器搬。")
    save(s, "19-3-测试矩阵.svg", yy + 20)


# ------------------------------------------------------------------ 第 20 篇
def fig_20_big():
    s = Svg()
    y0 = s.header("全景：一次存档与一次读档经过的所有部件",
                  "上半是存档，下半是读档；中间的浅蓝虚线框是冻结窗口。左右两侧是窗口外的工作。"
                  "三件事：回得对（同一窗口、不变量、拿不准就报错）、回得快（只存改动、只改名、原地写回）、讲得清（mem_mode、分级、计时）。")
    T = y0 + 30

    def row(y, title, pre, frozen, post):
        s.text(M, y + 4, title, 16, INK, 600)
        x = M
        pw = 300
        for i, (r, t) in enumerate(pre):
            box(s, x, y + 20 + i * 52, pw, 44, r, None, t, 13.5, 13)
        fx = M + pw + 40
        fw = 700
        s.rect(fx, y + 14, fw, len(frozen) * 46 + 50, FROZEN[0], FROZEN[1], 1.3, rx=12, dash="6 4")
        s.text(fx + 14, y + 38, "冻结窗口", 13.5, FROZEN[2], 600)
        for i, (r, t) in enumerate(frozen):
            box(s, fx + 16, y + 50 + i * 46, fw - 32, 38, r, None, t, 13.5, 13)
        px = fx + fw + 40
        for i, (r, t) in enumerate(post):
            box(s, px, y + 20 + i * 52, W - M - px, 44, r, None, t, 13.5, 13)
        arrow(s, [(M + pw + 4, y + 60), (fx - 4, y + 60)], INK, 1.4)
        arrow(s, [(fx + fw + 4, y + 60), (px - 4, y + 60)], INK, 1.4)
        return y + max(len(pre), len(post)) * 52 + 30, y + len(frozen) * 46 + 80

    e1, e2 = row(T, "存档", [(CTL, "代理截下 49984"), (CTL, "鉴权 · 取锁 · 再确认"), (CTL, "全量 / 增量决策"), (CTL, "Prepare")],
                 [(STO, "暂停"), (FCR, "写快照 + 位图（纪元前进）"), (STO, "封存写层：只换指针"), (STO, "恢复")],
                 [(STO, "层文件改名进存档目录"), (CTL, "登记磁盘账本"), (CTL, "提交 · 基准 ← 新存档"), (CTL, "返回 mem_mode")])
    T2 = max(e1, e2) + 20
    row(T2, "读档", [(CTL, "代理截下 · 鉴权 · 取锁"), (CTL, "取目标"), (CTL, "装配目标视图"), (CTL, "丢连接池 · 拒绝其他请求")],
        [(STO, "暂停 ∥ 后台清连接跟踪"), (FCR, "导出活跃脏页"), (CTL, "物化：回滚集 + 祖先链找内容"), (FCR, "原地回滚九阶段（提交点）"),
         (STO, "换磁盘视图 · 等清理 · 恢复")],
        [(CTL, "基准 ← 目标"), (CTL, "磁盘账本 ← 目标描述"), (GST, "等 envd · 校正墙钟"), (CTL, "失败按四档分级")])
    yy = s.footer(T2 + 5 * 46 + 100, "注：颜色：蓝是控制面（orchestrator 里的编排与账本），橙是 Firecracker，灰是宿主与存储，紫是客户机。")
    save(s, "20-1-全景.svg", yy + 20)


def fig_20_triage():
    s = Svg()
    y0 = s.header("按症状排障：先看 mem_mode 和能力行，再看 reason，再看分阶段计时",
                  "大多数问题能在三步之内定位：是没在跟踪脏页、是某一类明确的失败，还是某一段在变慢。")
    T = y0 + 40
    cols = [
        (NAT, "1. 慢，或每次都像全量", [("mem_mode 除第一次外是 full", "没开跟踪 / 开关值写错 / 链断后的新树根"), ("增量但比预期慢", "HDBSS 启用失败，退回软件写保护")]),
        (RISK, "2. 明确报错", [("507 / 429", "存档盘快满 / 个数或字节上限"), ("torn", "提交点后失败或超时：重建"), ("chain_broken", "先存一个新档"),
                           ("rootfs_poisoned", "读档到任意已有存档"), ("不支持原地回滚", "Firecracker 没配对")]),
        (CTL, "3. 随时间或负载变慢", [("连接挂死、流截断", "跨越读档的连接本就作废"), ("读档随运行时间变慢", "块数增长 / 回滚量真实变大"),
                                ("随宿主其他流量变慢", "连接跟踪清理要扫整张宿主表"), ("收包卡死", "看逐设备诊断日志的队列位置")]),
    ]
    cw = (W - 2 * M - 40) / 3
    for i, (role, t, items) in enumerate(cols):
        x = M + i * (cw + 20)
        band(s, x, T, cw, 470, role, t)
        y = T + 60
        for a, b in items:
            box(s, x + 18, y, cw - 36, 70, WHITE, a, b, 14, 12.5)
            y += 80
    yy = s.footer(T + 500, "注：每一条都能在正文找到原理：脏页跟踪第 8 篇，失败分级第 13 篇，网络与时间第 12 篇，优化与长尾第 18 篇。")
    save(s, "20-2-排障决策.svg", yy + 20)


def fig_20_next():
    s = Svg()
    y0 = s.header("后续方向地图：按收益和难度摆放",
                  "大多数候选方向难度在“中”，差别在收益和前提。左下是验证缺口，成本低、应尽快补；右上是改变能力边界的大项，"
                  "比如可导出的存档、账本跨重启，要先想清楚调用约定和失败语义。")
    T = y0 + 40
    x0, y0b = M + 80, T + 440
    w, h = W - 2 * M - 120, 420
    s.line(x0, y0b, x0 + w, y0b, SUB, 1.5, end=True)
    s.line(x0, y0b, x0, y0b - h, SUB, 1.5, end=True)
    s.text(x0 + w, y0b + 28, "难度 →", 13, SUB, 600, "end")
    s.text(x0 - 10, y0b - h - 10, "收益 ↑", 13, SUB, 600)
    pts = [(0.12, 0.25, OK, "跨树读档端到端测试"), (0.12, 0.12, OK, "HDBSS 启用顺序断言"), (0.45, 0.55, CTL, "后台异步合并"),
           (0.5, 0.72, CTL, "连接跟踪按标记过滤"), (0.55, 0.35, CTL, "层块清单区间编码"), (0.55, 0.47, CTL, "按沙箱按需开跟踪"),
           (0.55, 0.22, KEY, "全零块回收"), (0.58, 0.10, KEY, "视图层列表引用父代"), (0.82, 0.82, NAT, "可导出的存档"), (0.88, 0.62, NAT, "账本跨重启加载")]
    for fx, fy, role, t in pts:
        cx, cy = x0 + fx * w, y0b - fy * h
        s.circle(cx, cy, 7, role[1])
        s.text(cx + 14, cy + 5, t, 13.5, role[2], 600)
    legend(s, y0b + 56, [(OK, "验证缺口"), (CTL, "性能与空间"), (KEY, "空间小优化"), (NAT, "能力边界")], x=x0)
    yy = s.footer(y0b + 84, "注：示意位置，不是量化评分；实施任何一项之前，先对照纪元不变量和八条顺序约束，并按“先量、再改、写回结论”的方法验证收益。")
    save(s, "20-3-后续方向.svg", yy + 20)


if __name__ == "__main__":
    fig_17_tiers()
    fig_17_phases()
    fig_17_size()
    fig_18_groups()
    fig_18_gc()
    fig_18_growth()
    fig_19_layers()
    fig_19_59()
    fig_19_matrix()
    fig_20_big()
    fig_20_triage()
    fig_20_next()
