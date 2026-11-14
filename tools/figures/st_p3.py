"""《E2B 沙箱存储从零讲透》第 11～13 篇的配图。

用法: python3 tools/figures/st_p3.py
"""
from st_common import *  # noqa: F401,F403
from st_common import W, M


# ------------------------------------------------------------------ 第 11 篇
def fig_11_tables():
    s = Svg()
    y0 = s.header("两张缓存表：模板表按 build 记，数据表按“build/文件”记",
                  "模板 C 的 header 引用 A、B、C 三代数据，所以模板表里只有 C 一项，数据表里却有三项 rootfs；"
                  "另一个模板 D 也引用 A，就和 C 共享 A 那一项。两张表的项都是最后一次访问后 25 小时过期。")
    T = y0 + 40
    lw = 520
    band(s, T, 330, ORCH, "模板表（按 buildID）", x=M, w=lw)
    for i, (n, refs) in enumerate([("C", "header 引用 A、B、C"), ("D", "header 引用 A、D")]):
        box(s, M + 24, T + 60 + i * 130, lw - 48, 100, white(ORCH), f"build {n}",
            f"两个 header（在内存里）\nsnapfile、metadata.json → /orchestrator/template/{n}/cache/<随机>/\n{refs}", 15, 12)
    DX = M + lw + 160
    band(s, T, 330, STORE, "数据表（按 buildID/文件类型）", x=DX, w=W - M - DX)
    rows = [("A/rootfs.ext4", T + 60), ("B/rootfs.ext4", T + 120), ("C/rootfs.ext4", T + 180), ("D/rootfs.ext4", T + 240)]
    for n, y in rows:
        box(s, DX + 24, y, W - M - DX - 48, 46, white(STORE), None, None)
        s.text(DX + 44, y + 29, n, 14, STORE[2], 600, mono=True)
        s.text(DX + 260, y + 29, "→ /orchestrator/build/" + n.replace("/", "-") + "-<随机>（稀疏，按 4 MiB 拉）", 12.5, SUB)
    for ty in (T + 83, T + 143, T + 203):
        arrow(s, [(M + lw - 24 + 6, T + 110), (DX + 18, ty)], SUB, 1.2)
    for ty in (T + 83, T + 263):
        arrow(s, [(M + lw - 24 + 6, T + 240), (DX + 18, ty)], SUB, 1.2, dash="5 4")
    T2 = T + 370
    cw = (W - 2 * M - 24) / 2
    box(s, M, T2, cw, 86, WHITE, "磁盘淘汰", "每秒查一次 /orchestrator/build 所在磁盘\n占用超过 85%（默认）就淘汰最老的一项", 15, 12.5)
    box(s, M + cw + 24, T2, cw, 86, RISK, "启动时清空", "模板表初始化时 cleanDir(/orchestrator/build)\n这里是缓存，不是模板的家", 15, 12.5)
    yy = s.footer(T2 + 122, "注：文件名里的随机 ID 防止旧缓存项关闭时删掉新缓存项的文件。内存这边一样，只是换成 memfile。")
    save(s, "11-1-两张缓存表.svg", yy + 20)


def fig_11_read():
    s = Svg()
    y0 = s.header("沙箱读一块数据的完整路径",
                  "先看沙箱自己写过没有；没有就查当前 build 的 header，找到数据在哪一代；去数据表取那一代的本地副本，"
                  "本地没有就从存储后端拉整个 4 MiB。内存的路径完全一样，只是起点换成 UFFD 缺页。")
    T = y0 + 40
    steps = [("客户机读 /dev/vda 第 N 块", "virtio-blk → /dev/nbdX → NBD 服务", GUEST),
             ("沙箱自己写过第 N 块吗？", "是 → 从 /orchestrator/sandbox/…cow 读，结束", MINE),
             ("查 rootfs.ext4.header（内存中）", "得到：在 build B 的数据文件里，偏移 M\nuuid.Nil → 直接给零", STORE),
             ("去数据表取 “B/rootfs.ext4”", "没有就新建：建稀疏文件、mmap、建 chunker", ORCH),
             ("chunker.Slice(M, 4 KiB)", "本地有：直接返回 mmap 里那一段\n本地没有：从 /tmp/templates/B/rootfs.ext4 拉整个 4 MiB 块", ORCH),
             ("交回 NBD 服务 → 内核 → 客户机", None, GUEST)]
    bh = 74
    for i, (t, d, r) in enumerate(steps):
        y = T + i * (bh + 22)
        box(s, M + 180, y, W - 2 * M - 360, bh, r, t, d, 15, 12.5)
        num(s, M + 150, y + bh / 2, i + 1)
        if i < len(steps) - 1:
            arrow(s, [(W / 2, y + bh + 2), (W / 2, y + bh + 20)], INK, 1.4)
    yy = s.footer(T + 6 * (bh + 22) + 10, "注：同一块同时只拉一次（fetchers.Wait），两个沙箱同时读同一块，一个去拉，另一个等。"
                                          "本机刚打的快照数据本来就在本地，数据表里存的是“本地 diff”，不用拉。")
    save(s, "11-2-读一块数据.svg", yy + 20)


def fig_11_twice():
    s = Svg()
    y0 = s.header("同一份数据，在内存里出现不止一次",
                  "这套环境的“存储后端”在 tmpfs 上，本身就占内存；本地缓存文件在硬盘上，但刚读写过的内容留在页缓存里；"
                  "最后每个用到这一页的沙箱，客户机内存里还各有一份。")
    T = y0 + 50
    items = [("/tmp/templates/<B>/memfile", "存储后端，在 tmpfs 上\n= 宿主普通内存", RISK),
             ("/orchestrator/build/<B>-memfile-<随机>", "本地缓存，在硬盘上\n读写过的部分在页缓存里\n记在 template-manager 的 cgroup 账上", ORCH),
             ("Firecracker 进程里的客户机内存", "2 MiB 大页，每个沙箱各一份\n不记 memory 控制器的账", GUEST)]
    bw = (W - 2 * M - 2 * 110) / 3
    for i, (t, d, r) in enumerate(items):
        x = M + i * (bw + 110)
        box(s, x, T, bw, 150, r, t, d, 15, 13)
        if i < 2:
            arrow(s, [(x + bw + 8, T + 75), (x + bw + 102, T + 75)], INK, 1.7,
                  label=["拉取 4 MiB", "UFFDIO_COPY"][i], ldy=-10)
    T2 = T + 200
    box(s, M, T2, W - 2 * M, 80, WHITE, "第 1 份是把模板放在 /tmp 造成的；第 2 份是缓存层的正常行为，内存紧张时内核会回收；第 3 份是沙箱真正在用的",
        "第 19 篇把这几份加起来算容量账", 15, 13)
    yy = s.footer(T2 + 116, "注：/mnt/snapshot-cache 也是 tmpfs，但这个版本的代码只在启动时建一下目录，从不往里写，不占内存。")
    save(s, "11-3-内存里两份.svg", yy + 20)


# ------------------------------------------------------------------ 第 12 篇
def fig_12_overlay():
    s = Svg()
    y0 = s.header("沙箱的硬盘：两层拼成一块",
                  "下层是所有同模板沙箱共享的只读模板，上层是每个沙箱自己的 COW 文件。写一律写上层并在位图里登记；"
                  "读先看上层，没有再看下层。")
    T = y0 + 40
    box(s, M + 300, T, W - 2 * M - 600, 60, GUEST, "客户机看到的 /dev/vda（5 GiB）", "→ /dev/nbdN → NBD 服务", 16, 12.5)
    box(s, M + 300, T + 100, W - 2 * M - 600, 60, ORCH, "overlay", "写：上层；读：先上后下", 16, 12.5)
    arrow(s, [(W / 2, T + 66), (W / 2, T + 94)], INK, 1.6, start=True)
    L = M + 80
    R = W - M - 80
    n = 24
    cw = (R - L) / n
    up = {2, 3, 9, 15, 16, 17}
    y1 = T + 230
    s.text(L - 14, y1 + 26, "上层", 15, MINE[2], 600, "end")
    for i in range(n):
        if i in up:
            s.rect(L + i * cw, y1, cw - 4, 40, MINE[0], MINE[1], 1.2, rx=4)
        else:
            s.rect(L + i * cw, y1, cw - 4, 40, "#FFFFFF", HAIR, 1, rx=4, dash="3 3")
    s.text(R, y1 + 64, "/orchestrator/sandbox/rootfs-<ID>-<随机>.cow：稀疏，只有写过的块；旁边一张位图记“哪些块在上层”", 13, MINE[2], 600, "end")
    y2 = y1 + 120
    s.text(L - 14, y2 + 26, "下层", 15, STORE[2], 600, "end")
    for i in range(n):
        s.rect(L + i * cw, y2, cw - 4, 40, STORE[0], STORE[1], 1.2, rx=4)
    s.text(L, y2 + 64, "模板根盘：header 查表 → 本地缓存 → /tmp/templates；只读、共享", 13, STORE[2], 600)
    for i in (5, 9):
        x = L + i * cw + cw / 2 - 2
        role = MINE if i in up else STORE
        tgt = y1 + 40 if i in up else y2
        arrow(s, [(x, T + 166), (x, tgt - 6)], role[1], 1.5)
    s.text(L + 5 * cw + cw / 2 - 8, T + 200, "读第 5 块：上层没有 → 下层", 12.5, STORE[2], 600, "end")
    s.text(L + 9 * cw + cw / 2 + 8, T + 200, "读第 9 块：上层有", 12.5, MINE[2], 600)
    yy = s.footer(y2 + 100, "注：ext4 改一个文件，不止写内容，还要写 inode、目录、日志等元数据块；这些块被写一次后也“搬”到了上层。")
    save(s, "12-1-两层根盘.svg", yy + 20)


def fig_12_pool():
    s = Svg()
    y0 = s.header("NBD 设备池：后台预备空闲设备，创建沙箱时直接拿",
                  "启动时读 nbds_max（本环境 512）建一张位图。后台循环不停地找“没人接着、大小为 0”的设备，"
                  "放进容量 64 的就绪队列；创建沙箱从队列取，结束时断开、清位图归还。")
    T = y0 + 40
    # 设备格
    s.text(M, T + 4, "/dev/nbd0 … nbd511", 15, INK, 600)
    cols = 32
    cw = (W - 2 * M) / cols
    used = {0, 1, 2, 5, 6, 7, 9, 12, 13, 20, 21, 22, 23, 31, 33, 40, 41, 42, 47, 50}
    for i in range(64):
        r, c = divmod(i, cols)
        role = GUEST if i in used else (MINE if i in (3, 4, 8, 10, 11) else WHITE)
        s.rect(M + c * cw, T + 20 + r * 40, cw - 5, 32, role[0], role[1], 1.1, rx=4)
    s.text(W - M, T + 120, "…… 共 512 台", 13, MUTED, 400, "end")
    T2 = T + 160
    bw = (W - 2 * M - 2 * 60) / 3
    box(s, M, T2, bw, 140, KEY, "后台循环 Populate", "从 0 号起找位图里没分出去的 N\n/sys/block/nbdN/pid 不存在\n且 /sys/block/nbdN/size 为 0\n找不到：等 50 ms 再找", 15, 12.5)
    box(s, M + bw + 60, T2, bw, 140, MINE, "就绪队列（容量 64）", "预备好的空闲设备\n创建沙箱时直接取，几乎不花时间", 15, 12.5)
    box(s, M + 2 * (bw + 60), T2, bw, 140, GUEST, "沙箱占用中", "4 条 socketpair、netlink 连接\n结束：断开，最多等 30 秒\n可无限重试，每 500 ms 一次", 15, 12.5)
    arrow(s, [(M + bw + 6, T2 + 70), (M + bw + 54, T2 + 70)], INK, 1.6)
    arrow(s, [(M + 2 * bw + 66, T2 + 70), (M + 2 * bw + 114, T2 + 70)], INK, 1.6, label="取", ldy=-8)
    arrow(s, [(M + 2.5 * bw + 120, T2 + 146), (M + 2.5 * bw + 120, T2 + 186), (M + bw / 2, T2 + 186), (M + bw / 2, T2 + 146)],
          SUB, 1.5)
    s.text((M + bw / 2 + M + 2.5 * bw + 120) / 2, T2 + 208, "归还：断开、清位图，之后又能被找到", 12.5, SUB, 600, "middle")
    T3 = T2 + 240
    box(s, M, T3, W - 2 * M, 70, RISK, "512 台都在用：就绪队列空了，后台每 50 ms 找一次、每失败 100 次打一条警告，新建沙箱在取设备这一步等到超时",
        "正在暂停、还没断开 NBD 的沙箱也占名额", 15, 12.5)
    yy = legend(s, T3 + 110, [(GUEST, "沙箱在用"), (MINE, "就绪队列里"), (WHITE, "空闲")])
    yy = s.footer(T3 + 136, "注：orchestrator 启动时读不到 /sys/module/nbd/parameters/nbds_max 就报 NBD module not loaded，起不来；部署脚本不会替你加载模块。")
    save(s, "12-2-NBD设备池.svg", yy + 20)


def fig_12_sigbus():
    s = Svg()
    y0 = s.header("磁盘写满时：补丁让 SIGBUS 只坏一个请求，不崩整个进程",
                  "往稀疏 COW 文件的 mmap 里写一个新块，文件系统要当场分配；磁盘满了分配失败，内核发 SIGBUS。"
                  "Go 默认对 SIGBUS 直接让整个进程崩溃，整台机器的沙箱一起完蛋。")
    T = y0 + 40
    cw = (W - 2 * M - 60) / 2
    for k, (title, role, steps) in enumerate([
        ("上游：整个 orchestrator 崩溃", RISK,
         ["某个客户机写盘，/orchestrator 磁盘已满", "copy 进 COW 的 mmap → 缺页时分配块失败", "内核发 SIGBUS → Go 运行时：致命错误",
          "orchestrator 退出，所有沙箱一起没了"]),
        ("ARM 补丁：只让那一个写请求失败", GOOD,
         ["同样的写，同样的 SIGBUS", "debug.SetPanicOnFault(true)：只在这个 goroutine 上变成 panic",
          "recover → 错误 “mmap fault (disk full?)”", "NBD 回一个失败应答：这个客户机看到 I/O 错误，其他沙箱照常"])]):
        x = M + k * (cw + 60)
        box(s, x, T, cw, 54, role, title, None, 16)
        for i, t in enumerate(steps):
            y = T + 80 + i * 82
            last = i == len(steps) - 1
            box(s, x + 30, y, cw - 60, 60, role if last else WHITE, t, None, 14)
            if i:
                arrow(s, [(x + cw / 2, y - 20), (x + cw / 2, y - 6)], SUB, 1.4)
    T2 = T + 420
    box(s, M, T2, W - 2 * M, 76, white(ORCH), "另一处加固：拷贝前先 madvise(MADV_POPULATE_READ/WRITE)",
        "在系统调用里完成缺页、记账和内存回收，避免 goroutine 在用户态缺页里睡着、拖住 Go 的“全体暂停”，造成很长的 GC 停顿", 15, 12.5)
    yy = s.footer(T2 + 112, "注：设置只对这一次调用所在的 goroutine 生效，出来就恢复，别的代码仍按进程默认处理。")
    save(s, "12-3-SIGBUS保护.svg", yy + 20)


# ------------------------------------------------------------------ 第 13 篇
def fig_13_handshake():
    s = Svg()
    y0 = s.header("UFFD 的交接：Firecracker 把句柄从 unix socket 递过来",
                  "orchestrator 先开好 socket；Firecracker 加载快照、申请客户机内存（不填内容）、建 UFFD 并登记，"
                  "然后连上 socket，一条消息里带上内存布局 JSON 和 UFFD 文件描述符。")
    T = y0 + 40
    lw = (W - 2 * M - 80) / 2
    LX, RX = M, M + lw + 80
    box(s, LX, T, lw, 56, ORCH, "orchestrator", None, 16)
    box(s, RX, T, lw, 56, GUEST, "新的 Firecracker 进程", None, 16)
    for x in (LX + lw / 2, RX + lw / 2):
        s.line(x, T + 60, x, T + 520, HAIR, 1.5, dash="4 4")
    rows = [(0, "开 /tmp/uffd-<ID>-<随机>.sock，等 accept（最多 120 秒）", None),
            (2, "PUT /snapshot/load：backend_type=Uffd，backend_path=那个 socket", "→"),
            (1, "按 snapfile 申请客户机内存（大页），不填内容", None),
            (1, "userfaultfd() 建 UFFD，登记这段内存，只收 MISSING 事件", None),
            (3, "连上 socket，sendmsg：内存布局 JSON + SCM_RIGHTS 带上 UFFD", "←"),
            (0, "建地址映射：FC 进程地址 → 客户机偏移；数据来源 = memfile header", None),
            (2, "uffd 就绪 → resumeVM", "→")]
    for i, (side, t, d) in enumerate(rows):
        y = T + 100 + i * 62
        if d is None:
            x = LX + 20 if side == 0 else RX + 20
            box(s, x, y - 20, lw - 40, 44, WHITE, t, None, 13.5)
        else:
            a, b = (LX + lw / 2 + 6, RX + lw / 2 - 6) if d == "→" else (RX + lw / 2 - 6, LX + lw / 2 + 6)
            arrow(s, [(a, y), (b, y)], INK if d == "→" else GUEST[1], 1.7)
            s.text(W / 2, y - 10, t, 13, INK if d == "→" else GUEST[2], 600, "middle")
    yy = s.footer(T + 550, "注：上游等握手的超时是 10 秒；ARM 机器上 Firecracker 从启动到发来句柄更慢，并发高时不够，补丁放宽到 120 秒。"
                           "预取的“拉取”一路在握手之前就可以开始。")
    save(s, "13-1-UFFD交接.svg", yy + 20)


def fig_13_prefetch():
    s = Svg()
    y0 = s.header("预取：照着构建时录下的清单，在客户机开口之前准备好",
                  "metadata.json 里的 prefetch.memory 记着恢复时通常会碰哪些块、按什么顺序。拉取和填页两路并行：拉到一块，就可以填一块；"
                  "客户机抢先碰到的页由缺页处理先填，预取再填时得到 EEXIST，忽略。")
    T = y0 + 40
    box(s, M, T, 360, 120, STORE, "metadata.json", "prefetch.memory\nindices: [0, 1, 37, 38, 512, …]\naccess_types: [r, w, r, r, p, …]", 15, 12.5)
    bw = 460
    X1 = M + 440
    box(s, X1, T, bw, 120, ORCH, "拉取阶段（最多 32 个并发）", "按清单顺序把块从存储后端\n拉进本地缓存（第 11 篇）\nUFFD 握手之前就能开始", 15, 12.5)
    X2 = X1 + bw + 80
    box(s, X2, T, W - M - X2, 120, ORCH, "填页阶段（最多 16 个并发）", "等 UFFD 就绪后，按清单顺序\nUFFDIO_COPY 进客户机内存\n访问类型记为“预取”", 15, 12.5)
    arrow(s, [(M + 366, T + 60), (X1 - 6, T + 60)], INK, 1.6)
    arrow(s, [(X1 + bw + 6, T + 60), (X2 - 6, T + 60)], INK, 1.6, label="拉到一块", ldy=-10)
    T2 = T + 170
    box(s, M, T2, W - 2 * M, 80, RISK, "副作用：预取填进去的页和读缺页一样不带写保护封条",
        "在 ARM 补丁下，如果暂停走“常驻页”判据，预取了多少页，下次暂停的内存增量就至少有多少页（第 15 篇）", 15, 13)
    yy = s.footer(T2 + 116, "注：清单是 optimize 阶段（第 9 篇）把模板恢复几次、只保留每次都出现的块录下来的；预取失败不影响正确性。")
    save(s, "13-2-预取.svg", yy + 20)


def fig_13_hugepages():
    s = Svg()
    y0 = s.header("大页怎么预留：以一台 512 GiB 的机器为例",
                  "init-client.sh 每次 build.sh -s 时计算：先给宿主留普通内存 max(4 GiB, 16%)，最多 42 GiB；"
                  "剩下的做大页，其中 20% 立刻划成静态池（上限 HUGEPAGES_BASE_MAX_MIB=64 GiB），80% 作为可临时要的超分配额度。")
    T = y0 + 60
    L, R = M, W - M
    total = 512.0
    segs = [(42, "给宿主留 42 GiB", HOST), (64, "静态池 64 GiB", RISK), (376, "超分配额度 376 GiB（用到才分配，用完归还）", GUEST),
            (30, "", WHITE)]
    x = L
    for gb, t, role in segs:
        w = (R - L) * gb / total
        s.rect(x, T, w - 3, 64, role[0], role[1], 1.3, rx=6)
        if t:
            s.text(x + w / 2, T + 38, t, 14, role[2], 600, "middle")
        x += w
    s.text(L, T - 14, "0", 12, MUTED, 400, "middle", mono=True)
    s.text(R, T - 14, "512 GiB", 12, MUTED, 400, "end", mono=True)
    s.text(R - (R - L) * 30 / total / 2, T + 92, "470×20%=94，被上限截到 64，差额不划", 12, MUTED, 400, "end")
    T2 = T + 140
    rows = [("给宿主留的普通内存", "操作系统、Nomad、api、PostgreSQL、Harbor……\ntemplate-manager 的堆和页缓存（上限 32 GiB）\n/tmp 的 tmpfs：模板和快照！", HOST),
            ("静态池 nr_hugepages", "开机就划出、一直占着，不管有没有沙箱\n停服不释放：build.sh --purge-hugepages\n重启归零，下次 -s 重新预留", RISK),
            ("超分配 nr_overcommit_hugepages", "静态池不够时临时向系统要\n要不要得到取决于那时有没有连续的 2 MiB\n客户机内存走这里，不记 memory 控制器", GUEST)]
    cw = (W - 2 * M - 2 * 24) / 3
    for i, (t, d, r) in enumerate(rows):
        box(s, M + i * (cw + 24), T2, cw, 130, r, t, d, 15, 12.5)
    yy = s.footer(T2 + 166, "注：挂载点 /mnt/hugepages（hugetlbfs），脚本做了幂等判断。上游是固定 20% 不设上限，大内存机器开机就锁死近百 GiB。")
    save(s, "13-3-大页预留.svg", yy + 20)


if __name__ == "__main__":
    for name in sorted(n for n in dir() if n.startswith("fig_")):
        globals()[name]()
