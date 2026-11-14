"""《E2B 沙箱存储从零讲透》第 14～17 篇的配图。

用法: python3 tools/figures/st_p4.py
"""
from st_common import *  # noqa: F401,F403
from st_common import W, M


# ------------------------------------------------------------------ 第 14 篇
def fig_14_steps():
    s = Svg()
    y0 = s.header("一次暂停：先停下，再分两路导出内存和磁盘，最后放进缓存、后台上传",
                  "Firecracker 只负责“停下来、写机器状态、报告哪些页脏了、报告它们在哪个地址”；"
                  "真正搬数据的是 orchestrator：内存用 process_vm_readv 直接从 Firecracker 进程里拷，磁盘把 COW 文件弹出来导出。")
    T = y0 + 40
    box(s, M, T, 300, 60, WHITE, "① 停健康检查  ② 暂停 VM", None, 15)
    box(s, M + 340, T, 420, 60, GUEST, "③ PUT /snapshot/create（不传 mem_file_path）", "只写 snapfile，刷磁盘缓冲", 14, 12)
    arrow(s, [(M + 306, T + 30), (M + 334, T + 30)], INK, 1.6)
    # 两路
    LX, RX = M, M + 800
    lw = 740
    band(s, T + 100, 330, GUEST, "内存", x=LX, w=lw)
    band(s, T + 100, 330, MINE, "磁盘", x=RX, w=W - M - RX)
    arrow(s, [(M + 550, T + 66), (M + 550, T + 94)], INK, 1.6)
    arrow(s, [(M + 760 + 6, T + 30), (RX + 200, T + 30), (RX + 200, T + 94)], INK, 1.6)
    mem = [("④ 问哪些页要导出", "写跟踪位图 ∪ 累积；或常驻页判据；或常驻 + 全零（第 15 篇）"),
           ("⑤ GET /memory/mappings → process_vm_readv", "把这些页拷进 /orchestrator/build/<新ID>-memfile-<随机>"),
           ("合成新 memfile.header", "位图变映射，盖在父 header 上，代数 +1")]
    for i, (t, d) in enumerate(mem):
        box(s, LX + 24, T + 150 + i * 88, lw - 48, 70, white(GUEST), t, d, 14.5, 12)
    disk = [("⑥ 弹出 COW 文件，后台停掉沙箱", "Firecracker 退出、NBD 断开、设备归还"),
            ("等 NBD 请求处理完，按位图导出", "→ /orchestrator/build/<新ID>-rootfs.ext4-<随机>"),
            ("合成新 rootfs.ext4.header", "COW 里有的块一定写过：永远精确")]
    for i, (t, d) in enumerate(disk):
        box(s, RX + 24, T + 150 + i * 88, W - M - RX - 48, 70, white(MINE), t, d, 14.5, 12)
    T2 = T + 470
    box(s, M, T2, 660, 74, ORCH, "⑦ 写 metadata.json  ⑧ 返回六样东西", "先放进本机模板缓存表：马上恢复不用等上传", 15, 12.5)
    box(s, M + 720, T2, W - 2 * M - 720, 74, RISK, "后台“上传”：Local 后端 = 拷贝到 /tmp/templates/<新ID>/",
        "暂停接口返回时可能还没拷完；同一份 diff 在硬盘缓存和 tmpfs 里各一份", 15, 12.5)
    arrow(s, [(M + 666, T2 + 37), (M + 714, T2 + 37)], INK, 1.6)
    arrow(s, [(LX + lw / 2, T + 436), (LX + lw / 2, T2 - 6)], INK, 1.4)
    arrow(s, [(RX + (W - M - RX) / 2, T + 436), (RX + (W - M - RX) / 2, T2 - 6)], INK, 1.4)
    yy = s.footer(T2 + 110, "注：新 buildID 由 api 分配，随暂停请求带过来。恢复就是“用这个 build 创建沙箱”：沙箱 ID 不变，Firecracker、NBD、COW、UFFD 全是新的。")
    save(s, "14-1-暂停八步.svg", yy + 20)


def fig_14_criteria():
    s = Svg()
    y0 = s.header("哪些内存页要导出：orchestrator 按顺序选判据",
                  "要导出的是“和父 build 不一样的页”。写跟踪位图只记客户机写过的页，最精确；"
                  "任何一步不可信，就退回常驻页判据：宁可多导出，绝不少导出。")
    T = y0 + 40
    X = M + 60
    bw = 480
    box(s, X, T, bw, 60, NAT and KEY, "这个沙箱是从快照恢复的吗？", None, 15)
    box(s, X + bw + 120, T, W - M - X - bw - 120, 60, WHITE, "否（模板构建的第一次开机，NoopMemory）",
        "GET /memory：常驻页，剔除全零页（映射到 uuid.Nil）", 14, 12)
    arrow(s, [(X + bw + 6, T + 30), (X + bw + 114, T + 30)], SUB, 1.5, label="否", ldy=-8)
    arrow(s, [(X + bw / 2, T + 66), (X + bw / 2, T + 104)], INK, 1.5, label="是", ldx=10, lanchor="start", ldy=4)
    box(s, X, T + 110, bw, 60, KEY, "这台机器开了写跟踪吗？", "有 HDBSS 默认开；FC_TRACK_DIRTY_PAGES 可强制", 15, 12)
    arrow(s, [(X + bw / 2, T + 176), (X + bw / 2, T + 214)], INK, 1.5, label="开了", ldx=10, lanchor="start", ldy=4)
    box(s, X, T + 220, bw, 60, KEY, "检查点累积的 DirtySinceBoot 可信吗？", None, 15)
    arrow(s, [(X + bw / 2, T + 286), (X + bw / 2, T + 324)], INK, 1.5, label="可信", ldx=10, lanchor="start", ldy=4)
    box(s, X, T + 330, bw, 76, GOOD, "写跟踪位图 ∪ DirtySinceBoot", "Firecracker 写出 FCDB 位图，4 KiB 一页\n日志 source=tracked / tracked+accumulated", 15, 12)
    RX = X + bw + 120
    box(s, RX, T + 160, W - M - RX, 120, RISK, "常驻页判据 GET /memory/dirty",
        "pagemap：在内存里、且没有写保护封条\nx86：精确（只读页有封条）\nARM 补丁：换入过的都算，读也算\n日志 source=resident", 15, 12.5)
    arrow(s, [(X + bw + 6, T + 140), (RX + 80, T + 140), (RX + 80, T + 154)], RISK[1], 1.5, label="没开", ldy=-8, lpos=0.3)
    arrow(s, [(X + bw + 6, T + 250), (RX - 6, T + 250)], RISK[1], 1.5, label="不可信", ldy=-8)
    yy = s.footer(T + 446, "注：写跟踪位图本身也可能取不到（Firecracker 没有这个接口），同样退回常驻页判据。磁盘那一路没有判据之争，COW 文件里有的就是写过的。")
    save(s, "14-2-脏页判据.svg", yy + 20)


# ------------------------------------------------------------------ 第 15 篇
def fig_15_chain():
    s = Svg()
    y0 = s.header("注释掉的三行，引出一条因果链",
                  "ARM 补丁把读缺页时的 UFFDIO_COPY_MODE_WP 注释掉了。填进去的页都不带封条，"
                  "于是“在内存里、且没封条”对每一个换入过的页都成立，常驻页判据从“写过的页”变成了“碰过的页”。")
    T = y0 + 40
    cw = (W - 2 * M - 60) / 2
    for k, (title, role, steps) in enumerate([
        ("x86（上游）", GOOD, ["读缺页：填页并贴封条", "之后只读：封条还在", "被写：封条被撕", "暂停：在且无封条 = 写过的页",
                             "内存增量 ≈ 真正写过的页"]),
        ("这套 ARM 环境（写跟踪没开时）", RISK, ["读缺页：填页，不贴封条", "之后只读：本来就没封条", "预取填的页：也没封条",
                                        "暂停：在且无封条 = 换入过的所有页", "内存增量 = 读过 + 写过（超集），下限 ≈ 工作集"])]):
        x = M + k * (cw + 60)
        box(s, x, T, cw, 54, role, title, None, 16)
        for i, t in enumerate(steps):
            y = T + 78 + i * 72
            last = i == len(steps) - 1
            box(s, x + 30, y, cw - 60, 54, role if last else WHITE, t, None, 14.5)
            if i:
                arrow(s, [(x + cw / 2, y - 16), (x + cw / 2, y - 4)], SUB, 1.3)
    T2 = T + 78 + 5 * 72 + 10
    cw3 = (W - 2 * M - 2 * 24) / 3
    for i, (t, d, r) in enumerate([("磁盘不受影响", "来自 COW 文件，只记写入，依然精确", GOOD),
                                   ("正确性不受影响", "多导出的页内容和父 build 一样", GOOD),
                                   ("代价", "空间和时间：每次暂停多出一个工作集", RISK)]):
        box(s, M + i * (cw3 + 24), T2, cw3, 70, r, t, d, 15, 12.5)
    yy = s.footer(T2 + 106, "注：补丁没写明为什么注释掉；可能是当时 arm64 的内核或 Firecracker 对 UFFD 写保护的支持不完整。有 HDBSS 的机器写跟踪默认打开，暂停不走这条判据。")
    save(s, "15-1-因果链.svg", yy + 20)


def fig_15_measure():
    s = Svg()
    y0 = s.header("实测：两次快照之间什么都不做，内存增量也有 112 MiB",
                  "同一个沙箱连打三次快照（每次打完用新 build 原地恢复）：#1 基线，#2 什么都不做，#3 写 200 MiB 随机数据。"
                  "数据来自 deploy-docs/09，写跟踪没开的 ARM 环境。")
    T = y0 + 50
    rows = [("#1 基线", 112, 0, "0.42 秒"), ("#2 什么都不做", 112, 0, "0.41 秒"), ("#3 写了 200 MiB", 338, 201, "1.10 秒")]
    L = M + 220
    span = W - M - L - 160
    scale = span / 360.0
    for i, (n, mem, disk, tm) in enumerate(rows):
        y = T + i * 120
        s.text(M, y + 34, n, 16, INK, 600)
        s.text(M, y + 58, "耗时 " + tm, 13, SUB)
        s.rect(L, y + 6, mem * scale, 34, GUEST[0], GUEST[1], 1.3, rx=4)
        s.text(L + mem * scale + 10, y + 29, f"memfile {mem} MiB", 13.5, GUEST[2], 600)
        if disk:
            s.rect(L, y + 48, disk * scale, 34, MINE[0], MINE[1], 1.3, rx=4)
            s.text(L + disk * scale + 10, y + 71, f"rootfs {disk} MiB", 13.5, MINE[2], 600)
        else:
            s.rect(L, y + 48, 3, 34, MINE[1], MINE[1], 1, rx=1)
            s.text(L + 14, y + 71, "rootfs 0：沙箱读了大量磁盘，但磁盘增量只记写入", 13.5, MINE[2], 600)
    s.line(L, T - 6, L, T + 3 * 120 - 20, HAIR, 1.2)
    T2 = T + 370
    cw = (W - 2 * M - 2 * 24) / 3
    for i, (t, d) in enumerate([("#2 的 112 MiB", "新 UFFD 下系统重新换入自己的工作集；x86 上不算，这里全算"),
                                ("#3 的 338 ≈ 112 + 200 + 26", "dd 经过客户机页缓存，这 200 MiB 同时进了内存和磁盘两份增量"),
                                ("0.7 秒多出来的", "多导出约 427 MiB，约 600 MB/s，和 process_vm_readv 加写文件相符")]):
        box(s, M + i * (cw + 24), T2, cw, 86, WHITE, t, d, 15, 12.5)
    yy = s.footer(T2 + 122, "注：112 MiB 约为模板内存的一成，就是这个沙箱的常驻工作集。连续暂停 N 次，这套环境约多存 N 个工作集；而 /tmp/templates 在 tmpfs 上，删除也不回收。")
    save(s, "15-2-实测.svg", yy + 20)


# ------------------------------------------------------------------ 第 16 篇
def fig_16_tree():
    s = Svg()
    y0 = s.header("检查点树：回滚到 c2 再打检查点，就长出一条分支",
                  "回滚不删除任何检查点，比目标新的 c3 作为另一条分支保留，照样能回滚过去；下一个检查点的父亲是回滚的目标。"
                  "每个检查点只存它那段时间（epoch）写过的页，第一个默认存完整内存。")
    T = y0 + 40
    nodes = {"c1": (M + 260, T + 40), "c2": (M + 260, T + 170), "c3": (M + 90, T + 300), "c4": (M + 430, T + 300)}
    for n, (x, y) in nodes.items():
        role = RISK if n == "c1" else GUEST
        box(s, x - 80, y, 160, 70, role, n, "完整内存（根）" if n == "c1" else "这一段写过的页", 17, 12)
    for a, b in [("c1", "c2"), ("c2", "c3"), ("c2", "c4")]:
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        arrow(s, [(x1, y1 + 76), (x2, y2 - 6)], SUB, 1.5)
    s.text(M + 430 + 92, T + 340, "回滚到 c2 之后打的", 12.5, MUTED)
    # 文件
    FX = M + 700
    s.rect(FX, T, W - M - FX, 400, HOST[0], HOST[1], 1.3, rx=14)
    s.text(FX + 20, T + 30, "/orchestrator/build/checkpoints/<沙箱ID>/", 15, HOST[2], 600)
    files = [("<检查点ID>/snapfile", "机器状态（Firecracker 写）"),
             ("<检查点ID>/mem_diff", "稀疏：这一段写过的页，按原位置"),
             ("<检查点ID>/mem_bitmap", "FCDB：魔数、版本、页大小、页数、位图"),
             ("<检查点ID>/rootfs.header", "这一刻的磁盘视图（第 17 篇）"),
             ("<检查点ID>/manifest.json", "给人看的，程序不读"),
             ("layers/", "封存的磁盘写层，按引用计数回收")]
    for i, (n, d) in enumerate(files):
        y = T + 50 + i * 56
        s.rect(FX + 20, y, W - M - FX - 40, 46, "#FFFFFF", HAIR, 1, rx=8)
        s.text(FX + 36, y + 29, n, 13.5, INK, 600, mono=True)
        s.text(FX + 330, y + 29, d, 13, SUB)
    T2 = T + 430
    box(s, M, T2, W - 2 * M, 70, WHITE, "打检查点：PUT /snapshot/create，类型 Diff，这次传 mem_file_path 和 dirty_bitmap_path",
        "Firecracker 按写跟踪写出这一段的页和位图，然后清空自己的位图开始记下一段；耗时和写了多少页成正比", 15, 12.5)
    yy = s.footer(T2 + 106, "注：删除还有孩子的检查点（比如 c2）只把它隐藏，文件留给后代。账本只在 orchestrator 进程内存里；"
                            "orchestrator 重启或沙箱暂停再恢复（换了一代 Firecracker），检查点全部作废。")
    save(s, "16-1-检查点树.svg", yy + 20)


def fig_16_restore():
    s = Svg()
    y0 = s.header("回滚到 c2：只处理“还原集”，每一页沿祖先链往上找内容",
                  "当前在 c3 之后的 epoch。和 c2 那一刻相比可能不同的页 = 当前 epoch 写过的 ∪ c3 写过的；"
                  "这些页的内容沿 c2 → c1 往上找，拼成 revert_mem，交给定制 Firecracker 原地写回。")
    T = y0 + 50
    L = M + 260
    n = 16
    cw = (W - M - L) / n
    rows = [("c1（根，完整）", RISK, set(range(n))), ("c2 写过", GUEST, {2, 3, 9}), ("c3 写过", GUEST, {3, 6, 7}),
            ("当前 epoch 写过", GUEST, {7, 12})]
    for r, (name, role, on) in enumerate(rows):
        y = T + r * 56
        s.text(L - 16, y + 26, name, 14, INK, 600, "end")
        for i in range(n):
            if i in on:
                s.rect(L + i * cw, y, cw - 5, 38, role[0], role[1], 1.2, rx=4)
            else:
                s.rect(L + i * cw, y, cw - 5, 38, "#FFFFFF", HAIR, 1, rx=4, dash="3 3")
    y = T + 4 * 56 + 30
    s.text(L - 16, y + 26, "还原集", 15, RISK[2], 600, "end")
    rv = {3, 6, 7, 12}
    src = {3: "c2", 6: "c1", 7: "c1", 12: "c1"}
    for i in range(n):
        if i in rv:
            s.rect(L + i * cw, y, cw - 5, 38, RISK[0], RISK[1], 1.5, rx=4)
            s.text(L + i * cw + (cw - 5) / 2, y + 24, src[i], 13, RISK[2], 600, "middle")
        else:
            s.rect(L + i * cw, y, cw - 5, 38, "#FFFFFF", HAIR, 1, rx=4)
    s.text(L, y + 64, "格子里写的是这一页的内容从哪来：先看 c2，c2 没有再看 c1。第 2、9 页虽然 c2 写过，但当前和 c2 一样，不用动。", 13, SUB)
    T2 = y + 100
    steps = ["暂停 VM", "导出当前写跟踪位图，定下还原集", "生成 revert_mem、revert_bitmap", "Firecracker 原地写回内存、恢复 vCPU",
             "NBD 下面换磁盘视图（第 17 篇）", "恢复运行，等 envd（最多 45 秒）"]
    bw = (W - 2 * M - 5 * 16) / 6
    for i, t in enumerate(steps):
        x = M + i * (bw + 16)
        role = RISK if i == 3 else WHITE
        box(s, x, T2, bw, 70, role, t, None, 13.5)
        num(s, x + 14, T2 + 14, i + 1, r=10, size=11.5)
    s.text(M + 3 * (bw + 16) + bw / 2, T2 + 92, "提交点：之前失败可继续运行，之后失败只能重建沙箱", 12.5, RISK[2], 600, "middle")
    yy = s.footer(T2 + 122, "注：从不在磁盘上拼出一份完整内存镜像，开销和还原集大小成正比。进程、KVM、tap、网络槽位、NBD 设备都不换。")
    save(s, "16-2-还原集.svg", yy + 20)


def fig_16_since():
    s = Svg()
    y0 = s.header("DirtySinceBoot：把 Firecracker 每次清空前的位图攒起来",
                  "Firecracker 的写跟踪位图每打一次检查点（或回滚一次）就清空。暂停要导出的却是“自恢复以来写过的所有页”。"
                  "补丁在每次清空前把位图并进一个集合，暂停时再并上当前位图。")
    T = y0 + 50
    L, R = M + 40, W - M - 40
    s.line(L, T + 60, R, T + 60, INK, 2, end=True)
    marks = [(0.03, "恢复"), (0.28, "打 c1"), (0.55, "打 c2"), (0.92, "暂停")]
    for f, t in marks:
        x = L + (R - L) * f
        s.line(x, T + 46, x, T + 74, INK, 2)
        s.text(x, T + 34, t, 14, INK, 600, "middle")
    segs = [(0.03, 0.28, "位图 ①"), (0.28, 0.55, "位图 ②"), (0.55, 0.92, "当前位图 ③")]
    for a, b, t in segs:
        x1, x2 = L + (R - L) * a, L + (R - L) * b
        s.rect(x1 + 4, T + 90, x2 - x1 - 8, 40, GUEST[0], GUEST[1], 1.2, rx=6)
        s.text((x1 + x2) / 2, T + 115, t, 13.5, GUEST[2], 600, "middle")
    for a, t in [(0.28, "清空前并进 ①"), (0.55, "清空前并进 ②")]:
        x = L + (R - L) * a
        arrow(s, [(x, T + 136), (x, T + 186)], MINE[1], 1.5, label=t, ldx=8, lanchor="start", ldy=4)
    box(s, L, T + 192, (R - L) * 0.62, 50, MINE, "DirtySinceBoot = ① ∪ ②", None, 15)
    xp = L + (R - L) * 0.92
    box(s, xp - 300, T + 280, 330, 70, GOOD, "暂停导出 = ① ∪ ② ∪ ③", "日志 source=tracked+accumulated", 15, 12)
    arrow(s, [(xp, T + 136), (xp, T + 274)], GOOD[1], 1.5)
    arrow(s, [(L + (R - L) * 0.62 + 6, T + 217), (xp - 120, T + 217), (xp - 120, T + 274)], GOOD[1], 1.5)
    T2 = T + 390
    cw = (W - 2 * M - 24) / 2
    box(s, M, T2, cw, 90, RISK, "只用当前位图 ③ 会怎样", "恢复出来的客户机由两个不同时刻的内存拼成，\n而暂停本身不报任何错：静默的数据损坏", 15, 12.5)
    box(s, M + cw + 24, T2, cw, 90, WHITE, "第一个检查点是完整捕获",
        "它的位图是“全部页”，不能并进来；改为打快照前先导出一次当前位图（不清空），\n每 GiB 客户机内存 32 KiB", 15, 12.5)
    yy = s.footer(T2 + 126, "注：任何一步出问题，集合被标记为不可信，之后的暂停一律退回常驻页判据。代码注释：导出多了只是慢，导出少了就是静默的数据损坏。")
    save(s, "16-3-DirtySinceBoot.svg", yy + 20)


# ------------------------------------------------------------------ 第 17 篇
def fig_17_seal():
    s = Svg()
    y0 = s.header("磁盘跟着回滚：打检查点时封存写层，回滚时换视图",
                  "封存只是几个指针的切换：把当前写层冻成只读层，装一个新的空写层，不拷数据、不刷盘。"
                  "每个检查点记下“模板 + 哪几层”作为磁盘视图；回滚就在 NBD 下面换成那个视图。")
    T = y0 + 40
    cols = [("打 c1 之前", ["W1（写层）"], []),
            ("打完 c1", ["W2（写层）", "L1"], ["c1 视图：模板 + L1"]),
            ("打完 c2、c3", ["W4（写层）", "L3", "L2", "L1"], ["c2 视图：模板 + L1 + L2", "c3 视图：模板 + L1 + L2 + L3"]),
            ("回滚到 c1", ["W5（新写层）", "L1"], ["NBD、Firecracker 不变", "L2、L3 还被 c2、c3 引用，保留"])]
    cw = (W - 2 * M - 3 * 30) / 4
    for i, (t, layers, notes) in enumerate(cols):
        x = M + i * (cw + 30)
        s.text(x, T + 10, t, 16, INK, 600)
        yb = T + 300
        box(s, x, yb, cw, 46, STORE, "模板（只读）", None, 14)
        for k, ln in enumerate(reversed(layers)):
            y = yb - (k + 1) * 54
            role = MINE if "写层" in ln else white(GUEST)
            box(s, x, y, cw, 46, role, ln, None, 14)
        for k, n in enumerate(notes):
            s.text(x, yb + 76 + k * 22, n, 12.5, SUB)
        if i < 3:
            arrow(s, [(x + cw + 4, T + 200), (x + cw + 26, T + 200)], INK, 1.5)
    T2 = T + 430
    box(s, M, T2, W - 2 * M, 80, white(ORCH), "LayerStack：每块一个 uint16 记“主人是第几层”（0 = 模板）",
        "读一块查一次数组就到，不管摞了多少层；代价是每 GiB 根盘 512 KiB、每个视图一份", 15, 12.5)
    yy = s.footer(T2 + 116, "注：封存时故意不 msync：之后读它的人都经过同一份页缓存，内容一致；刷盘只换来“宿主崩溃后还在”，而检查点本来就随进程消失。实测刷盘每 MB 脏数据 0.49 ms。")
    save(s, "17-1-封存与视图.svg", yy + 20)


def fig_17_fold():
    s = Svg()
    y0 = s.header("压实：只有一个孩子的隐藏检查点，并进它的孩子",
                  "“只保留最近 N 个、删最老的”这种用法，删的永远是下一个的父亲，隐藏的检查点会无限增长。"
                  "压实把隐藏的 H 并进唯一的孩子 C：位图取并集，C 没有而 H 有的页拷进 C，C 接到 H 的父亲下面。")
    T = y0 + 40
    def chain(x, items):
        for i, (n, role, d) in enumerate(items):
            y = T + 20 + i * 100
            box(s, x, y, 300, 70, role, n, d, 16, 12)
            if i:
                arrow(s, [(x + 150, y - 24), (x + 150, y - 6)], SUB, 1.5)
    s.text(M, T + 6, "压实前", 15, INK, 600)
    chain(M, [("P", WHITE, "H 的父亲"), ("H（已删除、隐藏）", RISK, "页 {1, 4, 5}"), ("C", GUEST, "页 {4, 9}")])
    s.text(M + 560, T + 6, "压实后", 15, INK, 600)
    chain(M + 560, [("P", WHITE, "C 的新父亲"), ("C（合并后）", GUEST, "页 {1, 4, 5, 9}\n4 用 C 自己的版本")])
    arrow(s, [(M + 330, T + 190), (M + 530, T + 190)], INK, 1.8, label="fold", ldy=-10)
    RX = M + 960
    box(s, RX, T + 20, W - M - RX, 120, WHITE, "为什么不改变任何回滚",
        "H 只有 C 一个孩子：凡是经过 H 的路径，\n一定紧挨着经过 C；把两者合成一个，\n还原集和内容查找的结果都不变", 15, 12.5)
    box(s, RX, T + 160, W - M - RX, 110, WHITE, "磁盘这半",
        "列着 H 那层的视图都紧接着列 C 那层时，\n两层合成一层并改写 header；否则 H 那层留在 C 的视图里", 15, 12.5)
    T2 = T + 330
    rows = [("CHECKPOINT_COMPACT", "默认开；false 关闭"), ("CHECKPOINT_COMPACT_MAX_PER_OP", "默认 8：一次删除最多顺带并几个"),
            ("失败重试", "之后的删除里再试，最多 3 次，之后放着不管")]
    cw = (W - 2 * M - 2 * 24) / 3
    for i, (t, d) in enumerate(rows):
        box(s, M + i * (cw + 24), T2, cw, 70, KEY, t, d, 14, 12.5)
    yy = s.footer(T2 + 106, "注：压实后，一棵有 V 个可见检查点的树最多 V+1 个隐藏的、总共不超过 2V+1 个。文件工作都写到新名字下，最后一次性切换。")
    save(s, "17-2-压实.svg", yy + 20)


def fig_17_quota():
    s = Svg()
    y0 = s.header("检查点配额：三道闸，加一块拿不走的“地板”",
                  "沙箱还在运行，就至少要留下一个完整的根：约一份客户机内存 M，加磁盘层和 header 的开销 ε（实测约 61 MiB，按 256 MiB 留余量）。"
                  "字节上限低于 M+ε 没有意义。")
    T = y0 + 50
    L, R = M + 40, W - M - 40
    gib = 6.0
    def X(v):
        return L + (R - L) * v / gib
    s.text(L, T + 6, "以 M = 2 GiB 的沙箱为例，CHECKPOINT_MAX_BYTES_PER_SANDBOX 设在哪个区间：", 14, INK, 600)
    s.line(L, T + 80, R, T + 80, INK, 1.6, end=True)
    for v in range(0, 7):
        s.line(X(v), T + 74, X(v), T + 86, INK, 1.2)
        s.text(X(v), T + 106, f"{v} GiB", 12, MUTED, 400, "middle", mono=True)
    s.rect(L, T + 20, X(2.25) - L, 44, RISK[0], RISK[1], 1.3, rx=6)
    s.text((L + X(2.25)) / 2, T + 48, "上限低于地板 M+ε ≈ 2.25 GiB：没意义", 13.5, RISK[2], 600, "middle")
    s.rect(X(2.25), T + 20, X(4.25) - X(2.25), 44, WHITE[0], GUEST[1], 1.3, rx=6, dash="5 4")
    s.text((X(2.25) + X(4.25)) / 2, T + 48, "高于 M+ε：不会卡死", 13.5, GUEST[2], 600, "middle")
    s.rect(X(4.25), T + 20, R - X(4.25), 44, GOOD[0], GOOD[1], 1.3, rx=6)
    s.text((X(4.25) + R) / 2, T + 48, "高于 2M+ε：最坏情况也能留一个回滚点", 13.5, GOOD[2], 600, "middle")
    T2 = T + 150
    rows = [("CHECKPOINT_MIN_FREE_BYTES", "打之前检查剩余空间", "默认 max(4 GiB, 2×客户机内存)；0 关闭"),
            ("CHECKPOINT_MAX_PER_SANDBOX", "可见检查点个数", "默认 0：不限"),
            ("CHECKPOINT_MAX_BYTES_PER_SANDBOX", "按实际分配块计的总字节", "默认 0：不限；超了回 429 checkpoint_bytes_limit")]
    cw = (W - 2 * M - 2 * 24) / 3
    for i, (t, a, d) in enumerate(rows):
        box(s, M + i * (cw + 24), T2, cw, 100, KEY, t, a + "\n" + d, 14, 12.5)
    T3 = T2 + 130
    cw2 = (W - 2 * M - 24) / 2
    box(s, M, T3, cw2, 84, WHITE, "超了字节上限，删哪个能腾出空间", "删更老的：被并进唯一的孩子，省下孩子覆盖掉的页\n删当前基础或分叉点：只能隐藏，只省几十 KB", 15, 12.5)
    box(s, M + cw2 + 24, T3, cw2, 84, WHITE, "本环境", "三个变量都没设：剩余空间按默认阈值检查，数量和字节不限\n回滚本身从不受配额限制", 15, 12.5)
    yy = s.footer(T3 + 120, "注：能力文件 /orchestrator/build/checkpoint-capabilities.json 列出每个值，并标明来自环境变量还是默认值。")
    save(s, "17-3-配额与地板.svg", yy + 20)


if __name__ == "__main__":
    for name in sorted(n for n in dir() if n.startswith("fig_")):
        globals()[name]()
