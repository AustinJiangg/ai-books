"""《E2B 沙箱快照回滚从零讲透》第 9～12 篇的配图。用法: python3 tools/figures/rb_p3.py"""
from rb_common import *  # noqa: F401,F403
from rb_common import W, M


def frozen_band(s, x, y, w, h, label="冻结窗口：虚机暂停"):
    s.rect(x, y, w, h, FROZEN[0], FROZEN[1], 1.3, rx=12, dash="6 4")
    s.text(x + 16, y + 26, label, 14, FROZEN[2], 600)


TREE = {"ck1": (0, 1), "ck2": (1, 0), "ck3": (2, 0), "ck4": (1, 2), "ck5": (2, 2)}
BITS = {"ck1": "全 1（全量根）", "ck2": "{1, 5, 9}", "ck3": "{5, 7}", "ck4": "{2, 5}", "ck5": "{9, 11}"}


def draw_tree(s, x0, y0, dx, dy, roles, bw=200, bh=70, show_bits=True):
    pos = {}
    for k, (c, r) in TREE.items():
        pos[k] = (x0 + c * dx, y0 + r * dy)
    for a, b in (("ck1", "ck2"), ("ck2", "ck3"), ("ck1", "ck4"), ("ck4", "ck5")):
        (ax, ay), (bx, by) = pos[a], pos[b]
        if ay == by:
            arrow(s, [(ax + bw + 4, ay + bh / 2), (bx - 4, by + bh / 2)], SUB, 1.6)
        else:
            arrow(s, [(ax + bw + 4, ay + bh / 2), (ax + bw + 40, ay + bh / 2), (ax + bw + 40, by + bh / 2), (bx - 4, by + bh / 2)], SUB, 1.6)
    for k, (x, y) in pos.items():
        role = roles.get(k, WHITE)
        box(s, x, y, bw, bh, role, k, BITS[k] if show_bits else None, 16, 12.5)
    return pos


# ------------------------------------------------------------------ 第 9 篇
def fig_09_three():
    s = Svg()
    y0 = s.header("三种存法：2 GiB 内存、20 个存档、每次改 40 MiB",
                  "每代全量不可行；每代自足最简单，但“复制上一代”在 ext4 上是真拷 2 GiB；每代只存差分不依赖任何文件系统特性，"
                  "代价是找一页内容时要沿祖先往上找。存档盘是 ext4，所以选第三种。")
    T = y0 + 30
    rows = [["每代全量", "2 GiB", "2 GiB", "40 GiB", "无"],
            ["每代自足（复制上一代 + 覆盖脏页）", "元数据 + 40 MiB；ext4 上 2 GiB", "只写需要的页", "约 2 GiB + 20 × 40 MiB", "reflink"],
            ["每代只存差分（本方案）", "40 MiB", "只写需要的页", "约 2 GiB + 20 × 40 MiB", "无"]]
    table(s, M, T, [400, 340, 240, 300, W - 2 * M - 1280], rows, header=["存法", "每次存档写多少", "读档写回多少", "20 代共占", "依赖"],
          ts=14.5, roles=[RISK, NAT, OK])
    T2 = T + 230
    s.text(M, T2, "差分存法下，第 n 代某一页的内容去哪找", 15, INK, 600)
    gens = ["ck1 全量", "ck2", "ck3", "ck4（目标）"]
    gw = 260
    for i, g in enumerate(gens):
        x = M + i * (gw + 60)
        box(s, x, T2 + 24, gw, 70, OK if i == 0 else WHITE, g, "位图全 1" if i == 0 else "只有本代脏页", 15, 12.5)
        if i > 0:
            arrow(s, [(x - 4, T2 + 59), (x - 56, T2 + 59)], CTL[1], 1.6)
    s.text(M + 3 * (gw + 60) + gw + 20, T2 + 64, "沿祖先往上，第一个位图里有它的那一代", 13.5, CTL[2], 600)
    yy = s.footer(T2 + 130, "注：读档的代价与历史多长无关：找内容是按 64 页一个字做位运算，真正读文件只发生在命中的那一代（第 9 篇第七节）。")
    save(s, "09-1-三种存法.svg", yy + 20)


def fig_09_fork():
    s = Svg()
    y0 = s.header("读档后分叉：存档之间是一棵树，不是一条链",
                  "依次存 ck1、ck2、ck3；读档回 ck1（ck2、ck3 保留）；从 ck1 继续存 ck4、ck5，它们的父亲是 ck1。"
                  "创建时间的先后不等于依赖关系；“当前基准”记录沙箱现在从哪个存档继续变化。")
    T = y0 + 50
    pos = draw_tree(s, M + 40, T, 330, 170, {"ck1": OK, "ck5": NAT}, bw=220, bh=72)
    (x3, y3), (x1, y1) = pos["ck3"], pos["ck1"]
    arrow(s, [(x3 + 110, y3 - 4), (x3 + 110, y3 - 34), (x1 + 110, y3 - 34), (x1 + 110, y1 - 4)], RISK[1], 1.6, dash="5 4")
    s.text((x3 + x1) / 2 + 110, y3 - 42, "1. 曾经读档回 ck1，ck2、ck3 保留", 13, RISK[2], 600, "middle")
    s.pill(pos["ck5"][0] + 220 + 60, pos["ck5"][1] + 36, "当前基准", NAT, 13, solid=True)
    rx = M + 40 + 2 * 330 + 300
    rows = [["操作", "当前基准", "新条目的父亲"], ["存 ck1（全量）", "ck1", "无（树根）"], ["存 ck2", "ck2", "ck1"], ["存 ck3", "ck3", "ck2"],
            ["读档回 ck1", "ck1", "不建条目"], ["存 ck4", "ck4", "ck1"], ["存 ck5", "ck5", "ck4"]]
    table(s, rx, T - 10, [190, 130, W - M - rx - 320], rows[1:], header=rows[0], ts=13.5)
    yy = s.footer(T + 450, "注：条目的父亲写好就不变；沙箱的当前基准在存档成功时变成新存档，在读档成功时变成目标。读档不删除更新的存档，所以能前滚、能跨分支跳。")
    save(s, "09-2-回滚后分叉.svg", yy + 20)


def fig_09_revert():
    s = Svg()
    y0 = s.header("回滚集图解：从 ck5 读档到 ck3",
                  "最近公共祖先 A = ck1。从基准 ck5 爬到 A 经过 ck5、ck4；从 A 走到目标 ck3 经过 ck2、ck3；两段不含 A 本身。"
                  "沿途四张位图求并，再并上活跃脏页 L = {3}，得到 7 页。16 页里其余 9 页两个时刻内容相同，不用写。")
    T = y0 + 50
    roles = {"ck1": WHITE, "ck2": CTL, "ck3": CTL, "ck4": NAT, "ck5": NAT}
    pos = draw_tree(s, M + 20, T, 300, 160, roles, bw=210, bh=70)
    s.pill(pos["ck1"][0] + 105, pos["ck1"][1] + 92, "公共祖先 A（不参与）", KEY, 12.5)
    s.pill(pos["ck5"][0] + 210 + 50, pos["ck5"][1] + 35, "基准 b", NAT, 12.5, solid=True)
    s.pill(pos["ck3"][0] + 210 + 50, pos["ck3"][1] + 35, "目标 t", CTL, 12.5, solid=True)
    rx = M + 20 + 2 * 300 + 340
    rw = W - M - rx
    band(s, rx, T - 10, rw, 400, KEY, "求并")
    parts = [(NAT, "b → A 段：ck5 {9,11} ∪ ck4 {2,5}"), (CTL, "A → t 段：ck3 {5,7} ∪ ck2 {1,5,9}"), (GST, "活跃脏页 L：{3}")]
    yy = T + 50
    for role, t in parts:
        box(s, rx + 20, yy, rw - 40, 48, role, None, t, 14, 13.5)
        yy += 58
    s.text(rx + 20, yy + 26, "回滚集 = {1, 2, 3, 5, 7, 9, 11}", 17, INK, 600)
    for i in range(16):
        on = i in (1, 2, 3, 5, 7, 9, 11)
        x = rx + 20 + i * ((rw - 40) / 16)
        s.rect(x + 1, yy + 50, (rw - 40) / 16 - 2, 34, RISK[0] if on else "#FFFFFF", RISK[1] if on else HAIR, 1, rx=3)
        s.text(x + (rw - 40) / 32, yy + 72, str(i), 11, RISK[2] if on else MUTED, 600 if on else 400, "middle")
    yy2 = s.footer(T + 420, "注：为什么够：不在回滚集里的页，当前 = b 时刻 = A 时刻 = t 时刻。两段路径和 L 缺一不可，少一个就会漏页（第 9 篇第四节）。")
    save(s, "09-3-回滚集图解.svg", yy2 + 20)


def fig_09_resolve():
    s = Svg()
    y0 = s.header("找内容：沿目标的祖先链往上，第一个位图里有它的那一代",
                  "目标是 ck3，祖先链是 ck3 → ck2 → ck1。“为什么要写回”用路径上的位图，“内容从哪来”用目标祖先链上的位图，是两个独立的问题。"
                  "第 3 页进回滚集是因为它现在脏，内容却要一路找到全量根。")
    T = y0 + 40
    cols = [("页", 100), ("ck3 {5,7}", 220), ("ck2 {1,5,9}", 220), ("ck1 全 1", 220), ("内容取自", 260)]
    x = M
    xs = []
    for t, w in cols:
        xs.append(x)
        s.text(x + 12, T, t, 14, SUB, 600)
        x += w
    data = [(1, "ck2"), (2, "ck1"), (3, "ck1"), (5, "ck3"), (7, "ck3"), (9, "ck2"), (11, "ck1")]
    order = ["ck3", "ck2", "ck1"]
    y = T + 16
    for p, src in data:
        s.text(xs[0] + 12, y + 30, str(p), 15, INK, 600)
        hit = order.index(src)
        for k in range(3):
            if k < hit:
                box(s, xs[k + 1] + 6, y + 6, cols[k + 1][1] - 20, 38, WHITE, None, "没有", 13, 12.5)
            elif k == hit:
                box(s, xs[k + 1] + 6, y + 6, cols[k + 1][1] - 20, 38, OK, "命中", None, 13.5)
        s.text(xs[4] + 12, y + 30, src + " 的 mem_diff", 14, OK[2], 600)
        y += 52
    rx = M + 1100
    band(s, rx, T - 20, W - M - rx, 400, KEY, "合并成批")
    bullets(s, rx + 22, T + 50, ["按页号从小到大扫", "连续且同源的页合成一次读", "2、3 页同来自 ck1 → 一批", "5、7 页同源但不连续 → 两批",
                                  "每批最多 1024 页"], 13.5, 46, maxw=W - M - rx - 50)
    yy = s.footer(y + 16, "注：树根默认存全量、位图全 1，所以一定找得到，读档只读本地文件；缺位图、读短了都直接报错，不悄悄全量回滚或填 0。")
    save(s, "09-4-内容解析.svg", yy + 20)


# ------------------------------------------------------------------ 第 10 篇
def fig_10_path():
    s = Svg()
    y0 = s.header("一次磁盘读写的路径：从客户机到层文件",
                  "/dev/vda 和 /dev/nbdX 属于两个操作系统：前者是客户机里的虚拟磁盘，后者是宿主上的数据后端。"
                  "封存和换视图都发生在 Overlay 内部，设备本身不换，这就是“不重建宿主资源”在磁盘一侧的样子。")
    T = y0 + 34
    band(s, M, T, 380, 330, GST, "客户机内部")
    box(s, M + 24, T + 70, 332, 70, white(GST), "ext4 文件系统", "文件读写 → 块读写", 15, 12.5)
    box(s, M + 24, T + 170, 332, 70, white(GST), "virtio 块驱动：/dev/vda", "经 virtio 队列提交请求", 15, 12.5)
    arrow(s, [(M + 190, T + 144), (M + 190, T + 166)], INK, 1.4)
    fx = M + 440
    box(s, fx, T + 170, 260, 70, FCR, "Firecracker", "模拟 virtio 磁盘", 15, 12.5)
    arrow(s, [(M + 360, T + 205), (fx - 4, T + 205)], INK, 1.5)
    nx = fx + 320
    box(s, nx, T + 170, 220, 70, STO, "/dev/nbdX", "宿主内核 NBD 设备", 15, 12.5)
    arrow(s, [(fx + 264, T + 205), (nx - 4, T + 205)], INK, 1.5)
    ox = nx + 280
    ow = W - M - ox
    band(s, ox, T, ow, 330, CTL, "orchestrator：NBD 分发 → Overlay")
    box(s, ox + 20, T + 70, ow - 40, 64, white(GST), "活写层", "稀疏文件 + “本层有哪些块”位图；写只落这里", 14.5, 12.5)
    box(s, ox + 20, T + 150, ow - 40, 64, WHITE, "封存层栈（存过档才有）", "按块的归属索引：直接定位", 14.5, 12.5)
    box(s, ox + 20, T + 230, ow - 40, 64, WHITE, "模板 rootfs", "按需拉取并缓存", 14.5, 12.5)
    arrow(s, [(nx + 224, T + 205), (ox - 4, T + 205)], INK, 1.5)
    yy = s.footer(T + 360, "注：归属位图回答“这一块是不是本层的”，不是内容：客户机可能真的写了一块全 0，只看内容分不清（第 10 篇第一节）。")
    save(s, "10-1-块读写路径.svg", yy + 20)


def layer_row(s, x, y, w, role, label, blocks, nb=12, h=40, dashed=False):
    bw = w / nb
    s.text(x - 14, y + h / 2 + 5, label, 13.5, role[2], 600, "end")
    for b in range(nb):
        on = b in blocks
        s.rect(x + b * bw + 2, y, bw - 4, h, role[0] if on else "#FFFFFF", role[1] if on else HAIR, 1.1, rx=4,
               dash=None if on and not dashed else "3 3")
        if on and isinstance(blocks, dict) and blocks[b]:
            s.text(x + b * bw + bw / 2, y + h / 2 + 5, blocks[b], 13, role[2], 600, "middle")


def fig_10_seal():
    s = Svg()
    y0 = s.header("存档前后的层栈：旧写层就地变成只读层，新空写层接上",
                  "块 100（图中第 4 格）在模板里是 A，存档前被改成 B，写在 W1 里。存档 c1：刷屏障，新建空写层 W2，W1 叠到只读层栈顶上，换指针。"
                  "c1 时刻的磁盘 = 模板 + W1。之后改成 C，落进 W2。")
    T = y0 + 40
    hw = (W - 2 * M - 100) / 2
    LX = M + 150
    lw = hw - 150
    s.text(M, T, "存档 c1 之前", 16, INK, 600)
    layer_row(s, LX, T + 30, lw, GST, "活写层 W1", {4: "B", 8: "x"})
    layer_row(s, LX, T + 90, lw, STO, "模板", {i: ("A" if i == 4 else "") for i in range(12)})
    x2 = M + hw + 100
    LX2 = x2 + 150
    s.text(x2, T, "存档 c1 之后，再改成 C", 16, INK, 600)
    layer_row(s, LX2, T + 30, lw, GST, "活写层 W2（新）", {4: "C"})
    layer_row(s, LX2, T + 90, lw, STO, "封存层 W1", {4: "B", 8: "x"})
    layer_row(s, LX2, T + 150, lw, STO, "模板", {i: ("A" if i == 4 else "") for i in range(12)})
    arrow(s, [(M + hw + 10, T + 80), (x2 - 10, T + 80)], INK, 2)
    T2 = T + 240
    steps = [("1. 暂停后刷屏障", "内核手里攥着的写全部推进写层"), ("2. 建新空写层 W2", "稀疏文件，几乎不占空间"), ("3. W1 进只读层栈，换指针", "读写锁下一瞬间完成"),
             ("4. 恢复后改名进 layers/", "同一文件系统：inode 不变，映射照样有效")]
    sw = (W - 2 * M - 3 * 20) / 4
    for i, (t, sub) in enumerate(steps):
        box(s, M + i * (sw + 20), T2, sw, 80, CTL if i < 3 else OK, t, sub, 14.5, 12.5)
    yy = s.footer(T2 + 110, "注：没有复制任何一个块；封存层就是客户机自己写出的那个文件。只登记 W1 写过哪些块，950 上改 128 MiB 时封存约 7 ms。")
    save(s, "10-2-封存前后.svg", yy + 20)


def fig_10_view():
    s = Svg()
    y0 = s.header("读档换视图：换上目标的层组合和一个新空写层",
                  "读档回 c1：Overlay 的只读来源换成 c1 的层清单（模板 + W1），活写层换成新的空 W3；W2 是被丢弃时间线上的写，连文件删除。"
                  "目标视图在暂停前就装好，暂停后在独占锁下两个指针一起换。")
    T = y0 + 40
    hw = (W - 2 * M - 100) / 2
    lw = hw - 170
    s.text(M, T, "读档前（当前在 c2 之后）", 16, INK, 600)
    LX = M + 170
    layer_row(s, LX, T + 30, lw, GST, "活写层 W2", {4: "C"})
    layer_row(s, LX, T + 90, lw, STO, "封存层 W1", {4: "B", 8: "x"})
    layer_row(s, LX, T + 150, lw, STO, "模板", {i: ("A" if i == 4 else "") for i in range(12)})
    x2 = M + hw + 100
    LX2 = x2 + 170
    s.text(x2, T, "读档回 c1 之后", 16, INK, 600)
    layer_row(s, LX2, T + 30, lw, GST, "新活写层 W3", {})
    layer_row(s, LX2, T + 90, lw, STO, "封存层 W1", {4: "B", 8: "x"})
    layer_row(s, LX2, T + 150, lw, STO, "模板", {i: ("A" if i == 4 else "") for i in range(12)})
    arrow(s, [(M + hw + 10, T + 110), (x2 - 10, T + 110)], INK, 2)
    s.text(LX2 + 4 * lw / 12 + lw / 24, T + 218, "读块 100 → B", 13, OK[2], 600, "middle")
    T2 = T + 260
    rows = [["只读来源", "模板 + W1", "模板 + W1（c1 的清单）"], ["活写层", "W2，块 100 是 C", "新空 W3"], ["读块 100", "C", "B"],
            ["W2 的去向", "——", "被丢弃的时间线，连文件删除"]]
    table(s, M, T2, [300, 500, W - 2 * M - 800], rows, header=["", "读档前", "读档回 c1 后"], ts=14)
    yy = s.footer(T2 + 230, "注：不是把 B 复制回写层；而且只换磁盘不行，内存里的文件缓存也必须一起回去，所以磁盘、内存、设备在同一个冻结窗口里换。")
    save(s, "10-3-读档换视图.svg", yy + 20)


def fig_10_refs():
    s = Svg()
    y0 = s.header("引用计数与层合并：删存档不等于删层",
                  "每个层被多少个视图（每个存档一个）和当前运行状态列着，就有多少引用；归零才删。层栈不是存档树，按树回收会删掉别人还在读的层。"
                  "永远相邻成对出现的两层可以合成一层，读到的内容不变。")
    T = y0 + 40
    hw = (W - 2 * M - 80) / 2
    band(s, M, T, hw, 360, CTL, "引用计数")
    holders = [("c1 的视图", ["W1"]), ("c2 的视图", ["W1", "W2"]), ("当前运行状态", ["W1", "W2"])]
    y = T + 70
    for h, ls in holders:
        s.text(M + 24, y + 26, h, 14, INK, 600)
        for k, l in enumerate(ls):
            box(s, M + 200 + k * 120, y + 4, 100, 36, WHITE, l, None, 14)
        y += 56
    s.text(M + 24, y + 30, "W1 引用 = 3，W2 引用 = 2", 15, CTL[2], 600)
    s.text(M + 24, y + 60, "删 c1：W1 从 3 减到 2，仍然保留", 14, INK)
    s.text(M + 24, y + 88, "计数归零的层才删（若旧栈还映射着，空间等映射解除）", 13, SUB)
    x2 = M + hw + 80
    band(s, x2, T, hw, 360, OK, "层合并")
    lw = hw - 80
    layer_row(s, x2 + 60, T + 80, lw, STO, "B", {4: "B", 9: "y"}, nb=10)
    layer_row(s, x2 + 60, T + 130, lw, STO, "A", {2: "a", 4: "b"}, nb=10)
    arrow(s, [(x2 + hw / 2, T + 178), (x2 + hw / 2, T + 206)], OK[1], 1.8)
    layer_row(s, x2 + 60, T + 214, lw, OK, "A+B", {2: "a", 4: "B", 9: "y"}, nb=10)
    for k, ln in enumerate(["条件：所有列着 A 的地方，都紧接着在上面列着 B；反之亦然", "B 有的用 B，A 有 B 没有的用 A，偏移不变"]):
        s.text(x2 + 24, T + 300 + k * 26, ln, 13, SUB)
    yy = s.footer(T + 390, "注：“删一个存档就删它封的那层”在没开脏页跟踪或链断过时是错的：全量根的视图也叠在此前的层上（第 10 篇第四节、第 18 篇）。")
    save(s, "10-4-引用计数与层合并.svg", yy + 20)


# ------------------------------------------------------------------ 第 11 篇
def fig_11_ext():
    s = Svg()
    y0 = s.header("Firecracker 的三处扩展，各在哪一步被调用",
                  "扩展一是已有快照接口上的一个新字段，写快照时同时写出位图；扩展二在暂停时导出活跃脏页，不清零；"
                  "扩展三是原地回滚。Firecracker 只做机械动作，不知道存档树。")
    T = y0 + 40
    hw = (W - 2 * M - 60) / 2
    band(s, M, T, hw, 330, CTL, "存档")
    flow = [("暂停", None), ("仅全量：导出活跃位图", "扩展二 save-dirty-bitmap"), ("写快照", "扩展一 dirty_bitmap_path"), ("封存写层", None), ("恢复", None)]
    y = T + 60
    for t, ext in flow:
        box(s, M + 24, y, hw - 48, 42, FCR if ext else WHITE, None, t + ("  ←  " + ext if ext else ""), 14, 13.5)
        y += 52
    x2 = M + hw + 60
    band(s, x2, T, hw, 330, CTL, "读档")
    flow2 = [("暂停", None), ("导出活跃脏页", "扩展二 save-dirty-bitmap"), ("物化回滚集", None), ("原地回滚", "扩展三 PUT /snapshot/rollback"),
             ("换磁盘、恢复", None)]
    y = T + 60
    for t, ext in flow2:
        box(s, x2 + 24, y, hw - 48, 42, FCR if ext else WHITE, None, t + ("  ←  " + ext if ext else ""), 14, 13.5)
        y += 52
    T2 = T + 360
    rows = [["dirty_bitmap_path", "写差分快照的同时写出这一代位图", "不能拆成两次调用：写完快照就清零了；先取位图又会让快照拿不到这些页"],
            ["save-dirty-bitmap", "暂停时导出“自上次清零以来”的位图，不清零", "读档要事先知道 Firecracker 会写回哪些页，才能准备好内容"],
            ["rollback", "把位图指定的页从文件写回内存，恢复 CPU、GIC、设备", "orchestrator 总是传“回滚完先别恢复运行”：磁盘还没换"]]
    table(s, M, T2, [300, 560, W - 2 * M - 860], rows, header=["扩展", "做什么", "为什么这样设计"], ts=13.5)
    yy = s.footer(T2 + 190, "注：快照和位图都不 fsync：读它们的只有同机的 orchestrator 和 Firecracker，存档本来就不承诺扛过宿主崩溃。")
    save(s, "11-1-三处扩展.svg", yy + 20)


def fig_11_stages():
    s = Svg()
    y0 = s.header("原地回滚的九个阶段与提交点",
                  "提交点之前只检查、不动客户机，失败了虚机原样恢复运行（HTTP 400）；之后开始改写客户机，失败就是“撕裂”，"
                  "标记 Faulted、拒绝恢复运行，只能销毁重建（HTTP 500，带 \"fault\": true）。")
    T = y0 + 40
    pre = [("1 校验", "已暂停？快照能读？设备组成一致？文件长度、位图几何"), ("2 静默在途 I/O", "磁盘异步操作收尾；丢掉 tap 里发给旧时间线的包"),
           ("3 取活跃脏图 + 覆盖校验", "取出先放进备份位图；内容文件在每页上都有数据")]
    post = [("4 内存", "按位图合批写回"), ("5 vCPU", "收尾挂起的设备访问 → 复位 → 全写 → 读回核对"), ("6 中断控制器", "普通恢复后再按位绝对写回，逐位等于快照"),
            ("7 设备", "队列、特性、中断；串口复位；重建网卡缓存"), ("8 VMGenID", "写入新代号，必须在内存之后"), ("9 重置基线", "清零；队列页重新标脏")]
    lw = 560
    y = T
    for t, sub in pre:
        box(s, M, y, lw, 76, OK, t, sub, 15, 12.5, align="start")
        y += 88
    s.text(M, y + 20, "失败 → 虚机原样恢复，沙箱照常可用", 14, OK[2], 600)
    cx = M + lw + 50
    s.line(cx, T - 10, cx, T + 6 * 76 + 20, RISK[1], 3, dash="8 5")
    s.text(cx, T + 6 * 76 + 46, "提交点", 16, RISK[2], 600, "middle")
    rx = cx + 50
    rw = W - M - rx
    y = T
    for t, sub in post:
        box(s, rx, y, rw, 64, NAT, t, sub, 15, 12.5, align="start")
        y += 72
    s.text(rx, y + 20, "失败 → 撕裂：一部分在目标时刻、一部分在现在，只能重建", 14, RISK[2], 600)
    yy = s.footer(max(y + 50, T + 6 * 76 + 70), "注：能检查的全部放在提交点之前；回滚调用超时也按撕裂处理，因为说不清停在提交点哪一边。orchestrator 只看 fault 字段，不匹配错误文案。")
    save(s, "11-2-九个阶段.svg", yy + 20)


def fig_11_fcdb():
    s = Svg()
    y0 = s.header("FCDB：orchestrator 与 Firecracker 之间唯一的二进制格式",
                  "24 字节的头，后面是按 64 位字排列的位图。页号是“内存快照文件里的偏移 ÷ 页大小”，几段客户机内存首尾相接平铺，"
                  "所以 orchestrator 看到的是平坦连续的页号空间，不需要知道客户机的内存布局。")
    T = y0 + 50
    fields = [("FCDB", 4, "标识"), ("1", 4, "版本"), ("4096", 8, "页大小"), ("524288", 8, "页数"), ("字 0", 8, "第 0～63 页"), ("字 1", 8, "第 64～127 页"),
              ("……", 16, ""), ("字 8191", 8, "最后 64 页")]
    unit = (W - 2 * M) / 64
    x = M
    for t, n, lab in fields:
        w = n * unit
        role = CTL if lab in ("标识", "版本", "页大小", "页数") else WHITE
        box(s, x + 1, T, w - 2, 60, role, t, None, 14)
        if lab:
            s.text(x + w / 2, T + 84, lab, 12.5, SUB, 400, "middle")
        s.text(x + 2, T - 8, f"{int((x - M) / unit)}", 11, MUTED)
        x += w
    s.text(M, T + 130, "2 GiB 内存：524288 页 → 8192 个字 → 文件长 24 + 65536 字节", 15, INK, 600)
    T2 = T + 170
    items = [(CTL, "几何校验", "页大小、页数、文件长度必须和当前虚机完全一致；不一致说明属于另一台虚机，直接报错，不猜"),
             (NAT, "尾字掩码", "页数通常不是 64 的倍数，最后一个字里多出来的位必须是 0；两侧造的“全 1 位图”才会是同一个"),
             (OK, "两侧对称", "Rust 和 Go 各有一份读写实现，刻意写成镜像")]
    cw = (W - 2 * M - 40) / 3
    for i, (role, t, sub) in enumerate(items):
        box(s, M + i * (cw + 20), T2, cw, 110, role, t, sub, 15, 12.5)
    yy = s.footer(T2 + 140, "注：全量快照也写一张全 1 的位图；orchestrator 对全量条目更进一步，不读它、直接当全 1 用（第 9、13 篇）。")
    save(s, "11-3-FCDB格式.svg", yy + 20)


# ------------------------------------------------------------------ 第 12 篇
def fig_12_timelines():
    s = Svg()
    y0 = s.header("两条时间线：客户机回到 T0，外面的世界还在 T1",
                  "读档把客户机内部的状态带回存档时刻 T0，可网卡对象里的缓存、宿主的连接跟踪表、代理的连接池、外部的对端都还记得 T1。"
                  "重建路线没有前三项问题，原地路线必须逐个处理；它们的共同特点是表现为挂死而不是报错。")
    T = y0 + 50
    s.line(M + 160, T + 20, W - M, T + 20, SUB, 2, end=True)
    s.text(M, T + 26, "时间", 14, SUB, 600)
    t0, t1 = M + 400, M + 1100
    for x, lab in ((t0, "T0：存档"), (t1, "T1：读档")):
        s.line(x, T + 4, x, T + 36, INK, 2.4)
        s.text(x, T - 4, lab, 14, INK, 600, "middle")
    arrow(s, [(t1 - 10, T + 60), (t0 + 10, T + 60)], OK[1], 2, label="客户机内部：内存、CPU、设备回到 T0", ldy=-8, lsize=13)
    items = [(FCR, "网卡对象里缓存的描述符", "按 T1 的接收队列解析", "清空，按回滚后的队列重新解析"),
             (STO, "宿主连接跟踪表", "记着 T1 的 TCP 序号", "清掉本沙箱的表项，和回滚并行"),
             (CTL, "代理的连接池", "T1 时建立的连接", "读档一开始就丢弃"),
             (RISK, "外部对端、数据库", "和沙箱打过的所有交道", "回不去：业务幂等、去重、补偿")]
    y = T + 110
    for role, t, mem, fix in items:
        box(s, M, y, 420, 64, role, t, None, 15)
        box(s, M + 450, y, 440, 64, WHITE, None, "还记得：" + mem, 15, 13.5)
        box(s, M + 920, y, W - 2 * M - 920, 64, OK if role != RISK else RISK, None, "处理：" + fix, 15, 13.5, style="outline")
        y += 76
    yy = s.footer(y + 10, "注：通用规律：从客户机内存推导出的缓存、宿主上“记得这台客户机”的状态，都要在流量放回来之前处理掉（第 12 篇末尾的检查表）。")
    save(s, "12-1-两条时间线.svg", yy + 20)


def fig_12_conntrack():
    s = Svg()
    y0 = s.header("连接跟踪清理与回滚并行：暂停后开始，恢复前等它结束",
                  "约束只要求“表项在客户机恢复运行之前清完”，不要求“回滚已经完成”。所以暂停一到就在后台开清，"
                  "和导出、物化、Firecracker 回滚、换盘并行；恢复前等一下，通常早就清完了。")
    T = y0 + 50
    frozen_band(s, M, T, W - 2 * M, 280)
    main = [("暂停", 100), ("导出脏页", 160), ("物化", 260), ("Firecracker 回滚", 300), ("换磁盘", 160), ("等清理", 140), ("恢复", 100)]
    x = M + 30
    for t, w in main:
        role = OK if t == "等清理" else (FCR if t == "Firecracker 回滚" else WHITE)
        box(s, x, T + 60, w - 8, 56, role, t, None, 14)
        x += w
    bx0 = M + 30 + 100
    bw = 160 + 260 + 300 + 160 - 8
    box(s, bx0, T + 150, bw, 56, NAT, "后台：清连接跟踪表", "命名空间表整表清空 ∥ 宿主表只删本沙箱的表项（攒批，一次整表扫描）", 14, 12.5)
    arrow(s, [(bx0 + 4, T + 120), (bx0 + 4, T + 146)], NAT[1], 1.5)
    arrow(s, [(bx0 + bw - 20, T + 210), (bx0 + bw - 20, T + 240), (bx0 + bw + 60, T + 240), (bx0 + bw + 60, T + 120)], NAT[1], 1.5)
    s.text(bx0 + bw + 70, T + 262, "join", 13, NAT[2], 600)
    T2 = T + 330
    rows = [["本批地址数", "1", "2", "≥ 3"], ["让内核过滤更便宜的条件", "宿主表 > 约 7000 条", "宿主表 > 约 43000 条", "永不"]]
    table(s, M, T2, [360, 360, 360, W - 2 * M - 1080], rows[1:], header=rows[0], ts=14)
    yy = s.footer(T2 + 110, "注：清理代价和整张宿主表成正比；长跑中宿主表约 95% 是与沙箱无关的条目（本机 80 端口短连接残留、本机 DNS），所以宿主流量多时读档会变慢（第 18 篇）。")
    save(s, "12-2-conntrack并行.svg", yy + 20)


def fig_12_time():
    s = Svg()
    y0 = s.header("读档之后，各种“时间”去了哪里",
                  "单调时钟来自 vCPU 寄存器，跟着倒退；墙钟在读档返回之前由 envd 按宿主时间校正；VMGenID 让客户机内核重新播种随机数，"
                  "但用户程序自己缓存的随机状态在内存里，被原样带回，要业务自己重新初始化。")
    T = y0 + 40
    items = [(RISK, "单调时钟 CLOCK_MONOTONIC", "倒退到存档时刻", "不要用它量跨越读档的间隔；租约、超时判断要重新校准"),
             (OK, "墙钟 CLOCK_REALTIME", "读档返回前被 envd 校回现在", "调用方读档返回后再发的命令，看到的已是正确时间"),
             (OK, "内核随机数", "VMGenID 通知后重新播种", "新代号写在内存回滚之后"),
             (RISK, "用户态随机状态", "回退到存档时刻", "同一存档出发的两次执行可能得到相同随机序列，读档后自己重新初始化")]
    cw = (W - 2 * M - 60) / 4
    for i, (role, t, what, todo) in enumerate(items):
        x = M + i * (cw + 20)
        box(s, x, T, cw, 70, role, t, None, 15)
        box(s, x, T + 84, cw, 70, WHITE, None, what, 14, 14)
        box(s, x, T + 168, cw, 110, WHITE, None, todo, 14, 13, style="outline")
    T2 = T + 310
    box(s, M, T2, W - 2 * M, 80, CTL, "活性判据：用计数器在增长，不用时间戳在推进",
        "凭直觉用时间判断后台进程是否还在跑，会在一次完全正确的读档上报失败；反过来，PID 和启动时刻在多次存档、读档之间不变，是“回到那一刻”最硬的证据", 15, 12.5)
    yy = s.footer(T2 + 110, "注：如果 envd 一直不应答，墙钟就没有被校正，读档以 guest_unresponsive 报错（第 13 篇）。")
    save(s, "12-3-时间的去向.svg", yy + 20)


if __name__ == "__main__":
    fig_09_three()
    fig_09_fork()
    fig_09_revert()
    fig_09_resolve()
    fig_10_path()
    fig_10_seal()
    fig_10_view()
    fig_10_refs()
    fig_11_ext()
    fig_11_stages()
    fig_11_fcdb()
    fig_12_timelines()
    fig_12_conntrack()
    fig_12_time()
