"""《E2B 模板构建、沙箱启动与暂停恢复从零讲透》第 16～20 篇的配图。用法: python3 tools/figures/lc_p4.py"""
from lc_common import *  # noqa: F401,F403
from lc_common import W, M


def hbars(s, x, y, label_w, scale, rows, bh=28, gap=14, unit="ms"):
    """横向条形：rows=[(标签, 数值, role, 备注)]，返回结束 y。"""
    for t, v, role, note in rows:
        s.text(x, y + bh * 0.7, t, 14, INK, 600)
        w = max(v * scale, 3)
        s.rect(x + label_w, y, w, bh, role[0], role[1], 1.2, rx=5)
        s.text(x + label_w + w + 10, y + bh * 0.7, f"{v:g} {unit}" + (f"  {note}" if note else ""), 13.5, INK, 600)
        y += bh + gap
    return y


# ------------------------------------------------------------------ 第 16 篇
def fig_16_two_rpcs():
    s = Svg()
    y0 = s.header("Pause 与原生 Checkpoint：同一段存盘，后面是否再拉起一台",
                  "两者都先存盘、停掉旧沙箱。Pause 到此为止，沙箱离场；原生 Checkpoint 再从刚存的快照拉起一台新的。"
                  "这个原生 Checkpoint 和我们的快照回滚不是一回事。")
    T = y0 + 40
    s.text(M, T + 10, "Pause（sbx.pause()）", 17, CTL[2], 600)
    flow_h(s, M, T + 26, W - 2 * M, [(CTL, "存盘", "snapfile + 内存增量 + 磁盘增量"), (RISK, "停掉沙箱", None),
                                     (STO, "上传", "等上传完才返回"), (KEY, "离场", "以后 Sandbox.connect 恢复")], h=90, gap=50)
    T2 = T + 170
    s.text(M, T2 + 10, "原生 Checkpoint（sbx.create_snapshot()）", 17, CTL[2], 600)
    flow_h(s, M, T2 + 26, W - 2 * M, [(CTL, "存盘", "同上"), (RISK, "停掉旧沙箱", None), (STO, "上传", None),
                                      (OK, "从新快照拉起一台", "新的 Firecracker 进程")], h=90, gap=50)
    T3 = T2 + 170
    box(s, M, T3, W - 2 * M, 70, KEY, "对比：我们的快照回滚", "在同一个活着的 Firecracker 进程里原地存档读档，沙箱一刻都不停（另一本书）", 15, 12.5)
    f = s.footer(T3 + 100, "原生 Checkpoint 看起来沙箱一直在，底下其实是一次销毁加一次重建。")
    save(s, "16-1-Pause与Checkpoint.svg", f + 20)


def fig_16_six():
    s = Svg()
    y0 = s.header("暂停的六步：第 ② 步之后再也没有恢复运行",
                  "前五步把状态存下来；第 ⑥ 步导出磁盘增量时把写层摘下、关掉沙箱。导出磁盘的那个函数，参数之一就是“关掉沙箱”的回调。")
    T = y0 + 36
    st = [("停掉健康检查", "沙箱接下来会停止响应，别让健康检查误报"), ("暂停 vCPU", "guest 不再产生新状态"),
          ("让 Firecracker 写 snapfile", "CPU、中断控制器、设备状态；不含内存"), ("取脏页集合", "问内存处理器：这一代哪些页改过"),
          ("导出内存增量", "process_vm_readv 从 Firecracker 进程读出，写成紧凑文件"),
          ("导出磁盘增量", "摘下写层 → 关掉沙箱 → 等 NBD 释放 → 逐块导出")]
    y = steps(s, M, T, 980, st, ts=15, ss=12.5)
    rx = M + 1030
    box(s, rx, T, W - M - rx, 300, RISK, "为什么必须停", "摘下写层后，guest 再写磁盘无处可去\n\n遍历写层时不能有并发写，否则导出“一半新一半旧”\n\nNBD 设备释放后写层文件才能关闭", 16, 13)
    box(s, rx, T + 320, W - M - rx, 90, STO, "最后", "写元数据 → 上传 → 等上传完才返回", 15, 12.5)
    f = s.footer(max(y, T + 430) + 6, "对“沙箱离场”合理；对高频存档读档不可接受，这是另做快照回滚的直接原因。")
    save(s, "16-2-暂停六步.svg", f + 20)


def fig_16_ids():
    s = Svg()
    y0 = s.header("三个 ID 在一次原生 Checkpoint 前后",
                  "沙箱 ID 和执行 ID 不变；生命周期 ID（一个 Firecracker 进程实例）换新。旧沙箱的清理协程用自己的生命周期 ID 删表项，"
                  "新沙箱沿用同一个 ID 就会被误删。")
    T = y0 + 40
    rows = [["沙箱 ID", "用户看到的沙箱标识", "sbx-123", "sbx-123", "不变"],
            ["执行 ID", "一次“执行”，api、路由、统计用", "exec-9", "exec-9", "不变"],
            ["生命周期 ID", "一个 Firecracker 进程实例", "life-A", "life-B", "换新"]]
    table(s, M, T, [240, 480, 260, 260, 260], rows, header=["ID", "含义", "之前", "之后", ""], roles=[None, None, RISK])
    f = s.footer(T + 220, "推论：原生快照每一次“存盘后继续”都是一次销毁加一次重建，这是它成本模型的根源。")
    save(s, "16-3-三个ID.svg", f + 20)


# ------------------------------------------------------------------ 第 17 篇
def fig_17_criterion():
    s = Svg()
    y0 = s.header("x86 上的脏页判据：读进来的页保持写保护，写过的页保护被清",
                  "uffd 处理器填页时看缺页原因：读缺页带写保护填入；写缺页不带。读进来的页之后被写，会再触发一次写保护缺页，处理器解除保护。")
    T = y0 + 40
    cw = (W - 2 * M - 2 * 40) / 3
    cases = [("只读过的页", "读缺页 → 带写保护填入", "在内存里 · 有写保护", "不算脏", OK),
             ("直接写的页", "写缺页 → 不带写保护", "在内存里 · 无写保护", "脏", RISK),
             ("先读后写的页", "读缺页带写保护 → 写时再缺页 → 解除保护", "在内存里 · 无写保护", "脏", RISK)]
    for i, (t, how, state, verdict, role) in enumerate(cases):
        x = M + i * (cw + 40)
        box(s, x, T, cw, 60, KEY, t, None, 16)
        box(s, x, T + 80, cw, 70, WHITE, None, how, 14, 13)
        box(s, x, T + 170, cw, 60, STO, None, state, 14, 13)
        s.pill(x + cw / 2, T + 265, verdict, role, 15)
        for yy in (T + 64, T + 154):
            arrow(s, [(x + cw / 2, yy), (x + cw / 2, yy + 12)], INK, 1.2)
    box(s, M, T + 310, W - 2 * M, 60, KEY, None, "脏 ⟺ 在内存里（pagemap 第 63 位 = 1）且 没有写保护（第 57 位 = 0）　·　Firecracker 的 GET /memory/dirty 按此给位图", 15, 14)
    f = s.footer(T + 400, "代价：先读后写的页多一次缺页。收益：判据精确，只读不写的页不导出。第 19 篇：ARM 上这条判据失灵了。")
    save(s, "17-1-脏页判据.svg", f + 20)


def fig_17_memexport():
    s = Svg()
    y0 = s.header("内存导出：从 Firecracker 进程地址空间直接读出脏页",
                  "orchestrator 把脏页对应的地址区间组织成一批读取请求，用 process_vm_readv 分批读，依次写进一个紧凑文件；再生成新一代的映射表。")
    T = y0 + 40
    s.text(M, T, "Firecracker 进程里的 guest 内存", 14.5, SUB)
    n = 16
    cw = (W - 2 * M) / n
    dirty = {2, 3, 7, 11}
    for i in range(n):
        role = RISK if i in dirty else WHITE
        s.rect(M + i * cw, T + 12, cw - 4, 46, role[0], role[1], 1.2, rx=4)
        s.text(M + i * cw + cw / 2 - 2, T + 41, str(i), 13, role[2], 600, "middle")
    T2 = T + 150
    s.text(M, T2, "本代的紧凑差分文件（只有脏块，首尾相接）", 14.5, SUB)
    for k, i in enumerate(sorted(dirty)):
        s.rect(M + k * cw, T2 + 12, cw - 4, 46, RISK[0], RISK[1], 1.2, rx=4)
        s.text(M + k * cw + cw / 2 - 2, T2 + 41, str(i), 13, RISK[2], 600, "middle")
        arrow(s, [(M + i * cw + cw / 2 - 2, T + 62), (M + k * cw + cw / 2 - 2, T2 + 8)], MUTED, 1.2)
    s.text(M + 4 * cw + 20, T2 + 41, "process_vm_readv 批量读取（按系统允许的单次上限分批）", 13.5, INK, 600)
    T3 = T2 + 100
    table(s, M, T3, [700, 800], [["本代写过的块（2、3、7、11）", "指向本代差分文件"], ["没写过的块", "沿用上一代映射表里的指向（可能更早）"]],
          header=["新一代的映射表", ""])
    f = s.footer(T3 + 130, "这是一次真实的数据搬运：改了多少就拷多少。")
    save(s, "17-2-内存导出.svg", f + 20)


def fig_17_diskexport():
    s = Svg()
    y0 = s.header("磁盘导出：写层里的块 → 紧凑差分 + 映射表",
                  "写层只记写入，所以写层里有的块就是写过的块，磁盘增量天然精确，在 ARM 上也一样。全零块只记一个“空”标记，不写数据。")
    T = y0 + 40
    flow_h(s, M, T, W - 2 * M, [(CTL, "摘下写层", "根盘就此作废"), (RISK, "停沙箱", "另起协程关沙箱，等 NBD 释放"),
                                (STO, "逐块导出", "非零块追加进文件；全零块只记标记"), (STO, "关闭写层文件", None)], h=100, gap=50)
    T2 = T + 150
    s.text(M, T2, "写层里写过的块", 14.5, SUB)
    blocks = [(5, False), (6, False), (9, True), (14, False), (20, True), (21, False)]
    bw = 90
    for i, (b, z) in enumerate(blocks):
        role = KEY if z else OK
        s.rect(M + i * (bw + 10), T2 + 12, bw, 46, role[0], role[1], 1.2, rx=4)
        s.text(M + i * (bw + 10) + bw / 2, T2 + 41, f"块 {b}" + ("（全零）" if z else ""), 12.5, role[2], 600, "middle")
    T3 = T2 + 100
    s.text(M, T3, "差分文件（紧凑）", 14.5, SUB)
    k = 0
    for b, z in blocks:
        if z:
            continue
        s.rect(M + k * (bw + 10), T3 + 12, bw, 46, OK[0], OK[1], 1.2, rx=4)
        s.text(M + k * (bw + 10) + bw / 2, T3 + 41, f"块 {b}", 12.5, OK[2], 600, "middle")
        k += 1
    s.text(M + 700, T3 + 41, "块 9、20 只在映射表里记“空”", 13.5, SUB)
    f = s.footer(T3 + 90, "存储偏移 ≠ 设备偏移，要靠映射表换算。做过快照回滚的沙箱写层是一叠，导出要先压平（第 22 篇）。")
    save(s, "17-3-磁盘导出.svg", f + 20)


def fig_17_pausetime():
    s = Svg()
    y0 = s.header("一次 0 MiB 暂停的时间账（920B 逐段跟踪，总 234.9 ms）",
                  "真正保存内存状态的只有前约 10 ms；其余约 225 ms 在销毁虚拟机环境并等它结束。950 上拟合：暂停 ≈ 246 ms 固定 + 每 MiB 导出量 0.52 ms。")
    T = y0 + 50
    lx = M
    tw = W - 2 * M
    scale = tw / 240
    segs = [(0, 10, OK, ""), (10, 12, KEY, ""), (12, 169, RISK, "Firecracker 收到终止信号到退出（约 157 ms）"),
            (169, 232, FCR, "收尾、断 NBD、导出磁盘（约 63）"), (232, 235, STO, "")]
    for a, b, role, t in segs:
        s.rect(lx + a * scale, T, (b - a) * scale - 2, 50, role[0], role[1], 1.2, rx=4)
        if t:
            s.text(lx + (a + b) / 2 * scale, T + 31, t, 13, role[2], 600, "middle")
    for v in (0, 10, 169, 235):
        s.text(lx + v * scale, T + 72, str(v), 12, SUB, 400, "middle")
    s.text(lx + 5 * scale, T - 12, "存状态约 10 ms", 13, OK[2], 600, "start")
    T2 = T + 120
    s.text(M, T2, "Firecracker 退出过程的内核栈采样（采样拖慢了退出，时间点仅供参考）", 15, INK, 600)
    table(s, M, T2 + 16, [260, 1240],
          [["约 9～123 ms", "主线程在运行，调用栈读不到：约 114 ms 未归因，最长的一段"], ["123 ms", "释放挂载命名空间，等 RCU 宽限期"],
           ["137 ms", "卸载挂载点"], ["140 ms", "关闭 KVM 虚拟机，等中断相关清理"], ["149 ms", "销毁 KVM 虚拟机，等 RCU 宽限期"]],
          roles=[RISK, None, None, None, None])
    T3 = T2 + 270
    table(s, M, T3, [700, 260, 260, 280],
          [["开始停沙箱之前（含内存差分导出）", "12.4 ms", "88.8 ms", "约 +76 ms"], ["开始停沙箱到 Firecracker 退出", "约 156 ms", "约 191 ms", "约 +35 ms"],
           ["退出到磁盘差分导出完成", "约 63 ms", "约 160 ms", "约 +97 ms"]],
          header=["阶段", "0 MiB 档", "256 MiB 档", "增长"])
    f = s.footer(T3 + 190, "成本模型：原生暂停的主要代价来自拆机，改动量只决定上面那层增量。")
    save(s, "17-4-暂停时间账.svg", f + 20)


# ------------------------------------------------------------------ 第 18 篇
def fig_18_structure():
    s = Svg()
    y0 = s.header("恢复和启动是同一条路，只是映射链更长",
                  "Sandbox.connect 走同一个 ResumeSandbox。宿主上的五样东西全部从零重建；根盘 = 所有代 + 新的空写层；内存靠缺页回来。")
    T = y0 + 40
    lw = (W - 2 * M - 60) / 2
    band(s, M, T, lw, 260, OK, "启动（create）")
    gens = ["base", "指令…", "finalize"]
    for i, g in enumerate(gens):
        box(s, M + 24 + i * 150, T + 70, 136, 50, CTL, g, None, 13.5)
    s.text(M + 24, T + 160, "快照：模板最终那一代", 14, INK, 600)
    s.text(M + 24, T + 190, "节点：任意", 13.5, SUB)
    rx = M + lw + 60
    band(s, rx, T, lw, 260, OK, "恢复（connect）")
    gens2 = ["base", "指令…", "finalize", "暂停 1", "暂停 2"]
    for i, g in enumerate(gens2):
        box(s, rx + 24 + i * 138, T + 70, 126, 50, CTL if i < 3 else OK, g, None, 13.5)
    s.text(rx + 24, T + 160, "快照：最近一次暂停那一代", 14, INK, 600)
    s.text(rx + 24, T + 190, "节点：优先原节点（有本地缓存）；单节点部署都改成排队", 13.5, SUB)
    T2 = T + 300
    st = ["新建 Firecracker 进程 · KVM 虚拟机 · vCPU · 设备", "领网络槽位（可能和暂停前不同）", "新 uffd 处理器接管内存",
          "NBD + 根盘：所有代 + 新空写层", "加载 snapfile，恢复运行，缺页按需回来"]
    flow_h(s, M, T2, W - 2 * M, [(FCR, None, t) if i == 0 else (STO, None, t) for i, t in enumerate(st)], h=80, gap=26, ss=13)
    f = s.footer(T2 + 110, "第三部分讲的所有内容在恢复时原样发生；启动优化对恢复同样有效。")
    save(s, "18-1-恢复的结构.svg", f + 20)


def fig_18_time():
    s = Svg()
    y0 = s.header("恢复的时间账（920B 单次，92.6 ms 返回）",
                  "恢复不搬运任何数据：内存按缺页回来，根盘按需读差分。所以 950 上 0 MiB 档 109.3 ms、256 MiB 档 120.7 ms，几乎不随改动量变化。")
    T = y0 + 50
    tw = W - 2 * M
    scale = tw / 100
    segs = [(0, 35, FCR, "到节点、建资源、起 Firecracker（28 ms 时 API 就绪）"), (35, 57, GST, "加载 snapfile 21"),
            (57, 58, KEY, ""), (58, 93, OK, "等 envd 就绪、api 返回"), (93, 98, WHITE, "命令")]
    for a, b, role, t in segs:
        s.rect(M + a * scale, T, (b - a) * scale - 2, 50, role[0], role[1], 1.2, rx=4)
        if t:
            s.text(M + (a + b) / 2 * scale, T + 31, t, 13, role[2], 600, "middle")
    for v in (0, 35, 57, 58, 93, 98):
        s.text(M + v * scale, T + 72, str(v), 12, SUB, 400, "middle")
    T2 = T + 120
    table(s, M, T2, [500, 500, 500], [["0 MiB", "251.9 ms", "109.3 ms"], ["256 MiB", "429.9 ms", "120.7 ms"]],
          header=["950 · 改动量", "暂停（p50）", "恢复（p50）"])
    f = s.footer(T2 + 130, "单台、无并发时拉起 Firecracker 只要约 28 ms；对比 100 并发下的 240 ms，那里几乎全是争用。")
    save(s, "18-2-恢复的时间账.svg", f + 20)


def fig_18_deferred():
    s = Svg()
    y0 = s.header("成本被推迟：恢复很快，第一次访问工作集才慢",
                  "950 上：快照前第一次读 192 MiB 负载 590.9 ms；暂停、恢复之后第一次读同一份负载 702.6 ms，多出约 112 ms，"
                  "由 guest 里第一个访问这些页的程序承担。")
    T = y0 + 50
    scale = (W - 2 * M - 300) / 1000
    y = hbars(s, M, T, 300, scale, [("快照前首次读 192 MiB", 590.9, KEY, ""), ("恢复后首次读 192 MiB", 702.6, RISK, "多约 112 ms")], bh=40, gap=24)
    f = s.footer(y + 20, "所以评价恢复不能只看 connect() 多久返回；第 20 篇用“恢复后首次读一遍负载”的时间衡量改动有没有让恢复变慢。")
    save(s, "18-3-成本被推迟.svg", f + 20)


def fig_18_fit():
    s = Svg()
    y0 = s.header("原生快照的适用场景",
                  "成本模型和场景匹配就合适：产物自足、能搬走、不依赖活着的进程。不擅长的是高频、低延迟、沙箱不能中断，那是快照回滚的场景。")
    T = y0 + 40
    lw = (W - 2 * M - 60) / 2
    band(s, M, T, lw, 330, OK, "擅长")
    bullets(s, M + 24, T + 80, ["跨节点迁移：产物进对象存储，任何节点都能加载", "长期保存：不依赖任何活着的资源", "进程崩溃后恢复：本来就是新建进程",
                                 "沙箱离场再回来：停掉本来就是场景的一部分", "低频：几百毫秒的固定开销摊得开"], 14.5, 46, maxw=lw - 60)
    rx = M + lw + 60
    band(s, rx, T, lw, 330, RISK, "不擅长")
    bullets(s, rx + 24, T + 80, ["高频回退：每存一次停一次、拆一次", "低延迟：暂停 250 ms 起，恢复 100 ms 起，再加缺页", "沙箱不能中断：暂停一定会停掉沙箱"],
            14.5, 46, maxw=lw - 60)
    box(s, rx + 24, T + 230, lw - 48, 76, white(CTL), "快照回滚", "同一进程原地存档读档：950 上 0 MiB 档约 17 / 22 ms", 15, 12.5)
    f = s.footer(T + 360, "不是“原生实现得慢”，而是成本模型和场景不匹配。")
    save(s, "18-4-适用场景.svg", f + 20)


# ------------------------------------------------------------------ 第 19 篇
def fig_19_collapse():
    s = Svg()
    y0 = s.header("判据塌缩：没有任何页带写保护，“脏”变成了“在内存里”",
                  "arm64 的 6.6 内核没有 uffd 写保护；ARM 移植时把填页时带写保护的三行注释掉。从此每次填页都不带写保护，判据第二项恒真。")
    T = y0 + 40
    lw = (W - 2 * M - 80) / 2
    band(s, M, T, lw, 280, OK, "x86（上游）")
    s.text(M + 24, T + 80, "if 读缺页 { 带写保护填入 }", 15, INK, 600, mono=True)
    s.text(M + 24, T + 130, "脏 ⟺ 在内存里 且 没有写保护", 16, OK[2], 600)
    s.text(M + 24, T + 170, "只读过的页：有写保护 → 不算脏", 14, SUB)
    s.text(M + 24, T + 200, "写过的页：无写保护 → 脏", 14, SUB)
    rx = M + lw + 80
    band(s, rx, T, lw, 280, RISK, "ARM 适配版（修复前）")
    s.text(rx + 24, T + 80, "// if 读缺页 { 带写保护填入 }", 15, MUTED, 600, mono=True)
    s.text(rx + 24, T + 130, "脏 ⟺ 在内存里", 16, RISK[2], 600)
    s.text(rx + 24, T + 170, "只读过的页：被换入过 → 也算脏", 14, SUB)
    s.text(rx + 24, T + 200, "预取填进来的页 → 也算脏", 14, SUB)
    arrow(s, [(M + lw + 6, T + 140), (rx - 6, T + 140)], INK, 1.8)
    f = s.footer(T + 310, "这个改动在当时是必要的，对运行没有影响；它只影响暂停，而当时没人注意到。")
    save(s, "19-1-判据塌缩.svg", f + 20)


def fig_19_amplify():
    s = Svg()
    y0 = s.header("两个放大叠在一起：每一代的下限约等于工作集",
                  "每一代都是新的 Firecracker 进程，guest 一跑就要把工作集重新缺页换入；而换入即被判脏。两者一乘，改了多少都至少导出一个工作集。")
    T = y0 + 40
    flow_h(s, M, T, W - 2 * M, [(FCR, "放大一：每代新进程", "恢复、原生 Checkpoint 都新建进程\nguest 内存一开始是空的"),
                                (GST, "工作集重新换入", "内核、systemd、envd、后台进程碰过的页"),
                                (RISK, "放大二：换入即判脏", "在内存里 = 脏"),
                                (RISK, "每代导出 ≥ 工作集", "与改了多少无关")], h=130, gap=50, ts=15.5, ss=12.5)
    T2 = T + 180
    table(s, M, T2, [300, 500, 300, 400],
          [["#1", "沙箱刚起来", "112 MiB", "0"], ["#2", "中间什么都没做", "112 MiB", "0"], ["#3", "写了 200 MiB 随机数据", "338 MiB", "201 MiB"]],
          header=["连拍三次（1 vCPU / 1 GiB 模板）", "场景", "内存差分", "磁盘差分"], roles=[None, RISK, None])
    f = s.footer(T2 + 210, "磁盘那一列是精确的：写层只记写入。x86 上换进来的是带写保护的干净页，不算脏，没有这个问题。")
    save(s, "19-2-两个放大.svg", f + 20)


def fig_19_three():
    s = Svg()
    y0 = s.header("三列对比（950，修复前）：正确的位图其实就在旁边",
                  "每一步之间沙箱经历一次暂停加恢复。左列是原生暂停的判据，中列是 Firecracker 的写跟踪位图，右列是实际导出量。左列等于右列；中列才是真实写入。")
    T = y0 + 40
    rows = [("刚建好", 118.0, 4.6), ("只读 192 MiB，一字节没改", 324.0, 15.0), ("只改 12 MiB", 148.0, 19.7)]
    lx = M + 330
    scale = (W - M - lx - 200) / 330
    y = T
    for t, a, b in rows:
        s.text(M, y + 30, t, 15, INK, 600)
        s.rect(lx, y + 4, a * scale, 26, RISK[0], RISK[1], 1.2, rx=4)
        s.text(lx + a * scale + 10, y + 23, f"{a:g} MiB  原判据 = 实际导出", 13.5, RISK[2], 600)
        s.rect(lx, y + 36, max(b * scale, 3), 26, OK[0], OK[1], 1.2, rx=4)
        s.text(lx + b * scale + 10, y + 55, f"{b:g} MiB  写跟踪位图", 13.5, OK[2], 600)
        y += 96
    legend(s, y + 10, [(RISK, "原判据 GET /memory/dirty（= 实际导出）"), (OK, "写跟踪位图（真实写入 + 几 MiB 本底）")])
    f = s.footer(y + 40, "920B 上形状完全一样，只是本底大几十 MiB。修复前的方向是安全的：在内存里是写过的超集，只会多导，不会少导。")
    save(s, "19-3-三列对比.svg", f + 20)


# ------------------------------------------------------------------ 第 20 篇
def fig_20_chain():
    s = Svg()
    y0 = s.header("内存增量的三层，被 2 MiB 大页锁成一根链",
                  "判决定“读算不算脏”；存和填决定“最小能存多细”。只换判，存和填仍把一切归并到 2 MiB。")
    T = y0 + 40
    items = [(GST, "guest 页 = 2 MiB", "hugetlbfs 大页"), (FCR, "填", "一次缺页只能填一整页"),
             (RISK, "填的硬检查", "guest 页大小 = 映射块大小"), (STO, "存", "映射块 2 MiB，逐代继承"),
             (CTL, "判", "位图再细也要归并到 2 MiB")]
    flow_h(s, M, T, W - 2 * M, items, h=110, gap=40, ts=16, ss=12.5)
    T2 = T + 150
    table(s, M, T2, [200, 480, 380, 440],
          [["判", "算出这一代哪些页要导出", "判据给出的位图", "按 2 MiB 给出（GET /memory/dirty）"],
           ["存", "块拷进差分文件，映射表记下位置", "映射表的块大小", "模板 2 MiB，之后每代 2 MiB"],
           ["填", "恢复时缺页，从映射链取内容填入", "guest 页大小", "2 MiB，且要求等于映射块大小"]],
          header=["层", "做什么", "粒度由谁决定", "修复前"])
    f = s.footer(T2 + 190, "所以要分两半治：判换成写跟踪位图；存和填降到 4 KiB 存、2 MiB 拼。")
    save(s, "20-1-三层锁链.svg", f + 20)


def fig_20_floor():
    s = Svg()
    y0 = s.header("只换判据的地板：散写落进几十个 2 MiB 块",
                  "空转时真实写入只有 4.1 MiB（约 1050 个 4 KiB 页），却散落在约 67 个不同的 2 MiB 块里；归并后导出 134 MiB，放大三十多倍。")
    T = y0 + 40
    import random
    random.seed(3)
    cols, rows_ = 64, 8
    cw = (W - 2 * M) / cols
    hit = set(random.sample(range(cols * rows_), 67))
    for r in range(rows_):
        for c in range(cols):
            i = r * cols + c
            role = RISK if i in hit else WHITE
            s.rect(M + c * cw, T + r * 26, cw - 3, 22, role[0], role[1], 0.8, rx=2)
    s.text(M, T + rows_ * 26 + 26, "每格 = 一个 2 MiB 块（共 512 格 ≈ 1 GiB 示意）；红 = 块里至少有一个 4 KiB 页被写过，整块都要导出", 13.5, SUB)
    T2 = T + rows_ * 26 + 60
    table(s, M, T2, [360, 360, 360, 420],
          [["空转", "162 MiB", "134 MiB", "4.1 MiB"], ["只读 192 MiB", "366 MiB", "148 MiB", "14.6 MiB"],
           ["只改 12 MiB", "184 MiB", "156 MiB", "20.5 MiB"], ["写 192 MiB", "382 MiB", "358 MiB", "219.8 MiB"]],
          header=["920B 场景", "修复前导出", "只换判据（2 MiB 归并）", "4 KiB 真实写入"])
    f = s.footer(T2 + 230, "只换判据治好“读算脏”，但每代约 130 MiB 的本底散写归并后永远在，到不了真实写入量。")
    save(s, "20-2-只换判据的地板.svg", f + 20)


def fig_20_routes():
    s = Svg()
    y0 = s.header("两条路线：关大页 vs 4 KiB 存、2 MiB 拼",
                  "两条路线导出量相同，差别全在恢复和运行时。选路线 B：拼接能力已经存在，按映射表读的通用函数本来就能跨越任意多代。")
    T = y0 + 40
    rows = [["做法", "模板关大页，三层全 4 KiB；只换判", "换判；映射块 4 KiB；缺页仍 2 MiB，从 4 KiB 映射拼"],
            ["改动量", "约 40 行 + 模板参数", "约 200 行，5 个包"], ["导出量", "真实写入", "真实写入"],
            ["缺页次数", "乘以 512（400 MiB 工作集约 10 万次）", "不变（约 200 次）"], ["guest 运行时", "失去大页的 TLB 收益", "不变"],
            ["影响面", "所有用这个模板的沙箱", "只有原生快照的导出与恢复"]]
    table(s, M, T, [240, 600, 660], rows, header=["", "路线 A：关大页", "路线 B：保留大页（采用）"],
          roles=[None, None, None, RISK, RISK, None])
    f = s.footer(T + 400, "路线 A 可以当天验证数字，适合当对照开关；路线 B 落进代码。")
    save(s, "20-3-两条路线.svg", f + 20)


def fig_20_three_tier():
    s = Svg()
    y0 = s.header("填：一次 2 MiB 缺页，三级取源",
                  "映射表变成 4 KiB 后，一个 2 MiB guest 页可能由来自不同代的小块拼成。按“能不拷就不拷、要拷就不分配”分三级。")
    T = y0 + 40
    cw = (W - 2 * M - 2 * 40) / 3
    tiers = [("一：块等于页", "映射表块大小就是 2 MiB（模板、从未暂停的沙箱）", "原路：直接取一块", "和修复前一样", OK),
             ("二：整块同代", "一条映射覆盖整个 2 MiB", "零拷贝：把那一代缓存文件里的切片交给 UFFDIO_COPY", "和修复前一样；处理大部分缺页", OK),
             ("三：跨代混合", "2 MiB 里混着不同代的 4 KiB 块", "从缓冲池取 2 MiB 缓冲，沿映射链逐段读满，填完归还", "最多 512 次查表 + 一次 2 MiB 拷贝", NAT)]
    for i, (t, cond, how, cost, role) in enumerate(tiers):
        x = M + i * (cw + 40)
        box(s, x, T, cw, 60, role, t, None, 16)
        box(s, x, T + 76, cw, 80, WHITE, "条件", cond, 14, 12.5)
        box(s, x, T + 172, cw, 90, WHITE, "做法", how, 14, 12.5)
        box(s, x, T + 278, cw, 70, KEY, "代价", cost, 14, 12.5)
    T2 = T + 400
    s.text(M, T2, "跨代拼接的例子（上一代整块指向第 1 代，本代只写了 8 KiB 处一页）", 14.5, INK, 600)
    segs = [(0, 8, "第 1 代", WHITE), (8, 12, "本代", OK), (12, 64, "第 1 代（偏移 12 KiB 起）", WHITE)]
    scale = (W - 2 * M) / 64
    for a, b, t, role in segs:
        s.rect(M + a * scale, T2 + 16, (b - a) * scale - 2, 44, role[0], role[1], 1.2, rx=4)
        s.text(M + (a + b) / 2 * scale, T2 + 44, t, 13, role[2], 600, "middle")
    f = s.footer(T2 + 90, "示意按比例压缩。存：上一代映射一行都不用重写，原来那条 2 MiB 映射被切成三段，差分文件一个字节都不动。")
    save(s, "20-4-三级取源.svg", f + 20)


def fig_20_restore_cost():
    s = Svg()
    y0 = s.header("恢复开销的来回：恢复后首次读负载（920B，6 档平均）",
                  "第一版每次缺页都新分配 2 MiB 缓冲，慢了约 120 ms；加零拷贝快路径收回一半；再加缓冲池回到修复前水平。")
    T = y0 + 50
    scale = (W - 2 * M - 360) / 560
    y = hbars(s, M, T, 360, scale, [("修复前", 243, KEY, ""), ("第一版：每次缺页新分配", 367, RISK, "每档多 100～200 ms"),
                                    ("加零拷贝快路径（第二级）", 316, NAT, ""), ("再加缓冲池（第三级）", 241, OK, "与修复前持平")], bh=36, gap=20)
    T2 = y + 20
    box(s, M, T2, W - 2 * M, 70, KEY, "后来又收紧一次", "取缓冲时先查、只在第一次构造池对象：每次 207 ns、4 次分配 → 83 ns、1 次分配", 15, 12.5)
    f = s.footer(T2 + 100, "原则：懒加载路径上每一次缺页都是热路径，能不拷就不拷，要拷就不分配。")
    save(s, "20-5-恢复开销来回.svg", f + 20)


if __name__ == "__main__":
    fig_16_two_rpcs()
    fig_16_six()
    fig_16_ids()
    fig_17_criterion()
    fig_17_memexport()
    fig_17_diskexport()
    fig_17_pausetime()
    fig_18_structure()
    fig_18_time()
    fig_18_deferred()
    fig_18_fit()
    fig_19_collapse()
    fig_19_amplify()
    fig_19_three()
    fig_20_chain()
    fig_20_floor()
    fig_20_routes()
    fig_20_three_tier()
    fig_20_restore_cost()
