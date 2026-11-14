"""《E2B 沙箱存储从零讲透》第 1～6 篇的配图。

用法: python3 tools/figures/st_p1.py
"""
from st_common import *  # noqa: F401,F403
from st_common import W, M


# ------------------------------------------------------------------ 第 1 篇
def fig_01_map():
    s = Svg()
    y0 = s.header("全景图：这套环境里和存储有关的东西都在哪",
                  "一台鲲鹏服务器，一个 template-manager 进程同时当 orchestrator 和模板构建器。"
                  "颜色表示角色：橙色是模板文件的家，蓝色是 orchestrator 的本地缓存，紫色是给虚拟机用的，红色是其实在吃内存的地方。")
    T = y0 + 30
    # 左：原料
    box(s, M, T + 40, 260, 120, HOST, "Harbor 镜像仓库", "做模板的原料\nnginx harbor:443 → 2900\n数据在 /data", 15, 12.5)
    s.text(M, T + 20, "原料", 14, MUTED, 600)
    # 中：进程
    PX, PW = 420, 520
    box(s, PX, T + 40, PW, 120, ORCH, "/usr/bin/template-manager",
        "一个进程 = orchestrator + 模板构建（第 1、18 篇）\n读写模板、管理本地缓存、回答 NBD 和 UFFD", 16, 12.5)
    s.text(PX, T + 20, "进程", 14, MUTED, 600)
    arrow(s, [(M + 266, T + 100), (PX - 6, T + 100)], SUB, 1.6, label="拉镜像", ldy=-10)
    s.text((M + 266 + PX) / 2, T + 124, "第 8 篇", 12, MUTED, 400, "middle")
    # 右：模板的家
    RX = 1060
    box(s, RX, T + 40, W - M - RX, 120, RISK, "/tmp/templates/<buildID>/",
        "模板和快照的六个文件（Local 后端）\n/tmp 是 tmpfs：占内存、重启即丢（第 10 篇）", 15, 12.5)
    s.text(RX, T + 20, "模板的家", 14, MUTED, 600)
    arrow(s, [(PX + PW + 6, T + 85), (RX - 6, T + 85)], STORE[1], 1.6, label="上传", ldy=-8)
    arrow(s, [(RX - 6, T + 125), (PX + PW + 6, T + 125)], STORE[1], 1.6, label="按需读", ldy=18)
    # 第二行：本地缓存
    y2 = T + 220
    s.text(M, y2 - 14, "本地缓存（第 11 篇）", 14, MUTED, 600)
    cw = (W - 2 * M - 3 * 24) / 4
    items = [("/orchestrator/template", "snapfile、metadata.json"),
             ("/orchestrator/build", "memfile、rootfs 的稀疏副本\n启动时清空；检查点也在这"),
             ("/orchestrator/sandbox", "每个沙箱的 COW 文件\n和指向 NBD 的 .link"),
             ("/mnt/snapshot-cache", "tmpfs 65G\n本版代码不写")]
    for i, (t, sub) in enumerate(items):
        role = ORCH if i < 3 else WHITE
        box(s, M + i * (cw + 24), y2, cw, 96, role, t, sub, 14, 12)
    # 第三行：给虚拟机用的
    y3 = y2 + 150
    s.text(M, y3 - 14, "给虚拟机用的", 14, MUTED, 600)
    items = [("/dev/nbd0 … nbd511", "沙箱的“硬盘”，自编译模块 512 台（第 3、12 篇）", GUEST),
             ("/mnt/hugepages", "沙箱“内存”背后的 2 MiB 大页池（第 13 篇）", RISK),
             ("/fc-kernels  /fc-versions  /fc-envd", "内核、定制 Firecracker、envd（第 6 篇）", GUEST)]
    cw3 = (W - 2 * M - 2 * 24) / 3
    for i, (t, sub, role) in enumerate(items):
        box(s, M + i * (cw3 + 24), y3, cw3, 84, role, t, sub, 14, 12)
    # 第四行：其他
    y4 = y3 + 138
    s.text(M, y4 - 14, "其他；PostgreSQL、Redis 和 Harbor 合称“存数据的数据”（第 8 篇）", 14, MUTED, 600)
    items = [("MinIO  /root/data/minio", "装了、健康检查通过，但没建桶、没人写（第 10 篇）"),
             ("PostgreSQL", "模板、build、快照的记录（docker 容器）"),
             ("Redis", "运行中的沙箱在哪（Nomad job，无持久卷）")]
    ws = [620, 420, W - 2 * M - 620 - 420 - 48]
    x = M
    for (t, sub), w in zip(items, ws):
        box(s, x, y4, w, 70, WHITE, t, sub, 14, 12)
        x += w + 24
    yy = legend(s, y4 + 110, [(STORE, "模板文件"), (ORCH, "orchestrator 与本地缓存"), (GUEST, "给虚拟机用的"),
                              (RISK, "其实在吃内存")])
    yy = s.footer(y4 + 136, "注：镜像（Harbor）、模板（/tmp/templates）、MinIO 是三处互不相干的存储。"
                            "镜像变成模板以后，沙箱就不再用到 Harbor 里的镜像了。")
    save(s, "01-1-全景图.svg", yy + 20)


def fig_01_life():
    s = Svg()
    y0 = s.header("一个沙箱的存储一生：五个阶段对应全书五个部分",
                  "模板构建出六个文件；沙箱从模板按需取盘和内存；暂停产生新的 build，恢复又回到运行；"
                  "运行中还可以打检查点、原地回滚。")
    T = y0 + 40
    bh, gap = 150, 52
    bw = (W - 2 * M - 3 * gap) / 4
    xs = [M + i * (bw + gap) for i in range(4)]
    steps = [("① 模板构建", "第 8、9 篇", "Dockerfile + Harbor 镜像\n→ rootfs.ext4 + 内存快照", STORE),
             ("② 模板存放", "第 7、10 篇", "六个文件 + header 映射表\n→ /tmp/templates", STORE),
             ("③ 沙箱运行", "第 11～13 篇", "硬盘 = NBD + 写时复制\n内存 = UFFD 按需供页 + 大页", ORCH),
             ("④ 暂停与恢复", "第 14、15 篇", "只存改动的增量快照\n恢复 = 用新 build 回到 ③", MINE)]
    for x, (t, tg, sub, role) in zip(xs, steps):
        box(s, x, T, bw, bh, role, t, sub, 17, 13)
        tag(s, x + bw / 2, T + bh + 10, tg, "middle")
    for i in range(3):
        arrow(s, [(xs[i] + bw + 6, T + bh / 2), (xs[i + 1] - 6, T + bh / 2)], INK, 1.8)
    # 恢复回到运行
    arrow(s, [(xs[3] + bw / 2, T - 6), (xs[3] + bw / 2, T - 30), (xs[2] + bw / 2, T - 30), (xs[2] + bw / 2, T - 6)],
          MINE[1], 1.7)
    s.text((xs[2] + xs[3]) / 2 + bw / 2, T - 38, "恢复", 13, MINE[2], 600, "middle")
    # 检查点
    cy = T + bh + 80
    box(s, xs[2] - 40, cy, bw + 80, 110, GUEST, "⑤ 检查点回滚", "本机、随 Firecracker 进程存活\n原地把内存和磁盘倒回去（第 16、17 篇）", 17, 13)
    arrow(s, [(xs[2] + bw / 2 - 40, T + bh + 44), (xs[2] + bw / 2 - 40, cy - 6)], GUEST[1], 1.7, label="打检查点",
          ldx=-10, lanchor="end", lpos=0.5, ldy=4)
    arrow(s, [(xs[2] + bw / 2 + 40, cy - 6), (xs[2] + bw / 2 + 40, T + bh + 44)], GUEST[1], 1.7, label="回滚",
          ldx=10, lanchor="start", lpos=0.5, ldy=4)
    box(s, xs[0], cy, 2 * bw + gap, 110, WHITE, "第一部分（第 1～6 篇）：打地基",
        "块与页、文件系统、NBD、虚拟内存与 userfaultfd、写时复制、Firecracker 的存储", 15, 13)
    box(s, xs[3], cy, bw, 110, WHITE, "第五部分（第 18、19 篇）", "部署配置、容量规划与排障", 15, 13)
    yy = s.footer(cy + 150, "注：①② 产生的文件在存储后端；③ 的数据在本地缓存和 NBD、UFFD 里；"
                            "④ 产生新的 build，回到存储后端；⑤ 的文件只在本机 /orchestrator/build/checkpoints 下。")
    save(s, "01-2-存储一生.svg", yy + 20)


# ------------------------------------------------------------------ 第 2 篇
def fig_02_sizes():
    s = Svg()
    y0 = s.header("本书的四个尺寸：4 KiB、4 KiB、2 MiB、4 MiB",
                  "硬盘按块读写，内存按页管理，大页一次管 512 个普通页；E2B 从存储里拉数据时，又按 4 MiB 一块来拉。"
                  "下面按真实比例画出 4 MiB 里能放下多少个它们。")
    T = y0 + 40
    L = 330
    span = W - M - L - 40
    rows = [("块 block", "4 KiB", "根盘读写、COW 位图的粒度", 4, STORE),
            ("普通页 page", "4 KiB", "进程内存、检查点脏页的粒度", 4, ORCH),
            ("大页 huge page", "2 MiB", "客户机内存；memfile 的块", 2048, GUEST),
            ("分块 chunk", "4 MiB", "本地缓存从存储后端拉取的粒度", 4096, MINE)]
    y = T
    for name, sz, use, kib, role in rows:
        s.text(M, y + 22, name, 16, INK, 600)
        s.text(M, y + 44, sz + " · " + use, 12.5, SUB)
        w = max(span * kib / 4096, 3)
        s.rect(L + 40, y + 6, span, 40, "#FAFBFC", HAIR, 1, rx=6)
        s.rect(L + 40, y + 6, w, 40, role[0], role[1], 1.4, rx=4 if w > 8 else 1)
        if kib >= 2048:
            s.text(L + 40 + w / 2, y + 32, f"{kib // 1024} MiB = {kib // 4} 个 4 KiB", 13, role[2], 600, "middle")
        else:
            s.text(L + 52, y + 32, "← 细到几乎看不见：4 MiB 里有 1024 个", 13, role[2], 600)
        y += 86
    yy = s.footer(y + 6, "注：有的 ARM 内核普通页是 64 KiB，那时默认大页是 512 MiB；部署脚本因此从 /proc/meminfo 读大页大小，不写死。"
                         "本书的鲲鹏 + openEuler 环境是 4 KiB / 2 MiB。")
    save(s, "02-1-四个尺寸.svg", yy + 20)


def fig_02_nested():
    s = Svg()
    y0 = s.header("盘里套盘：rootfs.ext4 在宿主是一个文件，在客户机是一整块硬盘",
                  "宿主机的文件系统里有一个 5 GiB 的文件；它的内容本身又是一个完整的 ext4 文件系统。"
                  "orchestrator 只把它当一串 4 KiB 的块来读写，不需要懂里面装了什么。")
    T = y0 + 40
    # 外层
    s.rect(M, T, 700, 330, HOST[0], HOST[1], 1.3, rx=14)
    s.text(M + 20, T + 32, "宿主机的文件系统（外层）", 16, HOST[2], 600)
    for i, (n, sz) in enumerate([("/etc/…", ""), ("/usr/…", ""), ("/tmp/templates/<id>/rootfs.ext4", "5 GiB 的普通文件")]):
        role = STORE if i == 2 else WHITE
        box(s, M + 30, T + 60 + i * 84, 640, 64, role, n, sz or None, 15, 12.5, align="start")
    # 块条
    bx, by = M + 30, T + 60 + 2 * 84 + 64 + 12
    for i in range(16):
        s.rect(bx + i * 40, by, 36, 22, STORE[0], STORE[1], 1, rx=3)
    s.text(bx + 644, by + 16, "…", 14, MUTED)
    # 内层
    IX = 900
    s.rect(IX, T, W - M - IX, 330, GUEST[0], GUEST[1], 1.3, rx=14)
    s.text(IX + 20, T + 32, "客户机看到的 /dev/vda（内层 ext4）", 16, GUEST[2], 600)
    items = ["超级块：块大小 4096，共 1310720 块", "inode 表：每个文件一张“索引卡”", "/bin  /etc  /home  /usr  …  成千上万个文件"]
    for i, t in enumerate(items):
        box(s, IX + 30, T + 60 + i * 84, W - M - IX - 60, 64, white(GUEST), t, None, 14, align="start")
    arrow(s, [(M + 700 + 6, T + 236), (IX - 6, T + 236)], INK, 1.8, label="交给虚拟机当硬盘", ldy=-10)
    yy = s.footer(T + 370, "注：E2B 能按块做写时复制、按块做增量快照，前提就在这里：它只管外层的块，不用理解内层的文件。")
    save(s, "02-2-盘里套盘.svg", yy + 20)


def fig_02_sparse():
    s = Svg()
    y0 = s.header("稀疏文件：ls -l 说 10 GB，du 说 4 KiB",
                  "没写过的部分叫“洞”，文件系统不给它分配磁盘块，读的时候直接返回全零。"
                  "E2B 的 COW 文件、本地缓存文件、检查点 diff 都是这样的文件，查占用要用 du。")
    T = y0 + 50
    L, R = M + 160, W - M
    s.text(M, T + 26, "逻辑上", 15, INK, 600)
    s.rect(L, T, R - L, 44, "#FFFFFF", HAIR, 1.2, rx=6, dash="5 4")
    mid = L + (R - L) * 0.5
    s.rect(mid, T, 22, 44, MINE[0], MINE[1], 1.5, rx=3)
    s.text(L + (mid - L) / 2, T + 28, "洞（从没写过）", 14, MUTED, 400, "middle")
    s.text(mid + 22 + (R - mid - 22) / 2, T + 28, "洞", 14, MUTED, 400, "middle")
    s.text(L, T + 70, "0", 13, SUB, 400, "middle", mono=True)
    s.text(mid, T + 70, "5 GB", 13, SUB, 400, "middle", mono=True)
    s.text(R, T + 70, "10 GB", 13, SUB, 400, "end", mono=True)
    s.text(mid + 30, T - 10, "写了 4 KiB", 13, MINE[2], 600)
    T2 = T + 120
    s.text(M, T2 + 26, "磁盘上", 15, INK, 600)
    s.rect(L, T2, 22, 44, MINE[0], MINE[1], 1.5, rx=3)
    s.text(L + 40, T2 + 28, "只占这一块", 14, MINE[2], 600)
    T3 = T2 + 90
    box(s, M, T3, 700, 92, HOST, "$ ls -lh big.img   →   10G", "显示逻辑大小：从开头到结尾一共多少字节", 15, 13, mono_sub=False)
    box(s, M + 740, T3, W - 2 * M - 740, 92, MINE, "$ du -h big.img   →   4.0K", "显示实际占用的磁盘块", 15, 13)
    yy = s.footer(T3 + 130, "注：在 /orchestrator/build 里看到一个“8 GB”的文件不必惊慌，先 du 一下，往往只有几十 MB。")
    save(s, "02-3-稀疏文件.svg", yy + 20)


# ------------------------------------------------------------------ 第 3 篇
def fig_03_nbd():
    s = Svg()
    y0 = s.header("NBD 的一次读：内核把块请求交给一个程序回答",
                  "/dev/nbdN 背后没有硬盘，只有一对本机 socket。E2B 里回答请求的“接线员”就是 orchestrator，"
                  "它可以去任何地方找数据：COW 文件、本地缓存、存储后端。")
    T = y0 + 40
    lanes = [("客户机里的程序 / Firecracker", GUEST), ("内核 NBD 驱动", HOST), ("socketpair（本机，不走网络）", WHITE),
             ("orchestrator（接线员）", ORCH)]
    lw = (W - 2 * M - 3 * 30) / 4
    xs = [M + i * (lw + 30) for i in range(4)]
    for x, (t, r) in zip(xs, lanes):
        box(s, x, T, lw, 56, r, t, None, 14)
        s.line(x + lw / 2, T + 60, x + lw / 2, T + 470, HAIR, 1.5, dash="4 4")
    cx = [x + lw / 2 for x in xs]
    rows = [(0, 1, "读 /dev/nbd7 第 100 块", INK, 110),
            (1, 3, "请求{读, 编号=7, From=409600, Length=4096}", ORCH[1], 180),
            (3, 3, "查 COW → 查 header → 取缓存 / 拉存储", None, 250),
            (3, 1, "应答{成功, 编号=7} + 4096 字节", MINE[1], 330),
            (1, 0, "把数据交给读的人", INK, 400)]
    for a, b, t, c, y in rows:
        if a == b:
            box(s, xs[3], T + y - 22, lw, 46, white(ORCH), t, None, 13)
            continue
        x1, x2 = cx[a], cx[b]
        x1 += 6 if x2 > x1 else -6
        arrow(s, [(x1, T + y), (x2 + (-6 if x2 > x1 else 6), T + y)], c, 1.7)
        s.text((cx[a] + cx[b]) / 2, T + y - 10, t, 13, c, 600, "middle", mono="{" in t)
    yy = s.footer(T + 500, "注：内核可以同时发出很多请求，不必等前一个回来；程序可以乱序应答，靠编号对上号。"
                           "E2B 每台 NBD 设备接 4 条这样的连接。")
    save(s, "03-1-NBD一次读.svg", yy + 20)


def fig_03_decide():
    s = Svg()
    y0 = s.header("为什么一定要 NBD：第 N 块的内容要在“读的那一刻”去查",
                  "沙箱根盘的一块数据，可能在沙箱自己的 COW 文件里，也可能在模板的某一代 diff 里，"
                  "那一代还不一定拉到了本地。loop 设备只会照着一个文件读写，做不到这些。")
    T = y0 + 40
    X = M + 40
    bw = 420
    box(s, X, T, bw, 56, GUEST, "读第 N 块", None, 15)
    arrow(s, [(X + bw / 2, T + 62), (X + bw / 2, T + 92)], INK, 1.6)
    box(s, X, T + 98, bw, 60, WHITE, "沙箱自己写过第 N 块吗？", None, 15)
    box(s, X + bw + 140, T + 98, 520, 60, MINE, "从沙箱的 COW 文件读", "/orchestrator/sandbox/rootfs-…cow", 15, 12.5)
    arrow(s, [(X + bw + 6, T + 128), (X + bw + 134, T + 128)], MINE[1], 1.6, label="是", ldy=-8)
    arrow(s, [(X + bw / 2, T + 164), (X + bw / 2, T + 194)], INK, 1.6, label="否", ldx=10, lanchor="start", ldy=4)
    box(s, X, T + 200, bw, 60, STORE, "查 header：在哪一代、哪个偏移？", None, 15)
    arrow(s, [(X + bw / 2, T + 266), (X + bw / 2, T + 296)], INK, 1.6)
    box(s, X, T + 302, bw, 60, WHITE, "那一段拉到本地了吗？", None, 15)
    box(s, X + bw + 140, T + 302, 520, 60, STORE, "先从存储后端拉 4 MiB 到本地", "/tmp/templates → /orchestrator/build", 15, 12.5)
    arrow(s, [(X + bw + 6, T + 332), (X + bw + 134, T + 332)], STORE[1], 1.6, label="否", ldy=-8)
    arrow(s, [(X + bw / 2, T + 368), (X + bw / 2, T + 398)], INK, 1.6, label="是", ldx=10, lanchor="start", ldy=4)
    box(s, X, T + 404, bw, 60, ORCH, "从本地缓存读出来", None, 15)
    arrow(s, [(X + bw + 140 + 260, T + 368), (X + bw + 140 + 260, T + 434), (X + bw + 6, T + 434)], STORE[1], 1.6)
    yy = s.footer(T + 500, "注：写的时候一律写进沙箱自己的 COW 文件，不动模板。这套逻辑写在 orchestrator 里，NBD 把它接到内核的块设备上（第 12 篇）。")
    save(s, "03-2-读第N块.svg", yy + 20)


# ------------------------------------------------------------------ 第 4 篇
def fig_04_fault():
    s = Svg()
    y0 = s.header("虚拟内存与缺页：用到了才准备",
                  "进程看到的是虚拟地址，经页表一页一页地翻译成物理内存。页表项的存在位是 0 时，访问会触发缺页，"
                  "内核这时才分配物理页、填内容、登记页表，然后让进程接着跑。")
    T = y0 + 40
    # 虚拟页
    s.text(M, T + 10, "进程的虚拟地址空间", 15, INK, 600)
    vy = T + 30
    marks = [1, 1, 0, 1, 0, 0, 1, 0]
    for i, m in enumerate(marks):
        role = ORCH if m else WHITE
        s.rect(M, vy + i * 46, 220, 38, role[0], role[1], 1.2, rx=6)
        s.text(M + 110, vy + i * 46 + 24, f"虚拟页 {i}" + ("" if m else "（未准备）"), 13, role[2] if m else MUTED, 600 if m else 400, "middle")
    # 页表
    PX = 420
    s.text(PX, T + 10, "页表", 15, INK, 600)
    for i, m in enumerate(marks):
        s.rect(PX, vy + i * 46, 200, 38, "#FFFFFF", HAIR, 1.2, rx=6)
        s.text(PX + 100, vy + i * 46 + 24, ("存在=1 → 物理页 " + str([7, 2, 0, 9, 0, 0, 4, 0][i])) if m else "存在=0", 13,
               INK if m else BAD[2], 400, "middle")
    # 物理内存
    FX = 820
    s.text(FX, T + 10, "物理内存", 15, INK, 600)
    for i in range(10):
        used = i in (7, 2, 9, 4)
        role = HOST if used else WHITE
        s.rect(FX + (i % 2) * 130, vy + (i // 2) * 72, 120, 60, role[0], role[1], 1.2, rx=6)
        s.text(FX + (i % 2) * 130 + 60, vy + (i // 2) * 72 + 35, f"物理页 {i}", 13, role[2] if used else MUTED, 400, "middle")
    for i, m in enumerate(marks):
        if m:
            arrow(s, [(M + 226, vy + i * 46 + 19), (PX - 6, vy + i * 46 + 19)], SUB, 1.3)
    # 缺页流程
    KX = 1140
    box(s, KX, vy, W - M - KX, 340, RISK, "访问虚拟页 2 → 缺页",
        "① CPU 发现存在位是 0，停下\n② 交给内核\n③ 找一页空闲物理内存\n④ 填内容：新内存填零；\n    文件映射从文件读；\n    登记了 UFFD 的交给用户态程序\n⑤ 登记页表，存在位置 1\n⑥ 进程接着跑", 16, 13.5,
        align="start")
    yy = s.footer(vy + 380, "注：E2B 要让客户机内存也“用到才准备”，但数据散在好几代快照里，内核不知道去哪读，所以要用 userfaultfd 把第 ④ 步交给 orchestrator。")
    save(s, "04-1-页表与缺页.svg", yy + 20)


def fig_04_uffd():
    s = Svg()
    y0 = s.header("userfaultfd：缺页由另一个程序来填",
                  "Firecracker 把客户机内存登记在 UFFD 上。客户机碰到一页还没有的内存，出错的线程被挂起，"
                  "内核往 UFFD 里放一条消息；orchestrator 读到后用 UFFDIO_COPY 把内容原子地填进去。")
    T = y0 + 40
    steps = [("客户机访问第 X 页", "这一页还没准备", GUEST),
             ("Firecracker 进程缺页", "内核发现这段地址登记在 UFFD 上\n出错线程挂起", HOST),
             ("UFFD 里出现一条消息", "{地址 A，读还是写}", HOST),
             ("orchestrator 读出消息", "地址 → 客户机第 X 页\n查映射表，从快照数据取这一页", ORCH),
             ("UFFDIO_COPY", "原子地把内容放到地址 A", ORCH),
             ("内核登记页表，唤醒线程", "客户机继续运行，什么都没察觉", GUEST)]
    bw, bh = 470, 96
    cols = [M, M + bw + 70, M + 2 * (bw + 70)]
    pos = [(cols[0], T), (cols[1], T), (cols[2], T), (cols[2], T + 170), (cols[1], T + 170), (cols[0], T + 170)]
    for i, ((t, sub, r), (x, y)) in enumerate(zip(steps, pos)):
        box(s, x, y, bw, bh, r, t, sub, 15, 13)
        num(s, x + 18, y + 18, i + 1)
    arrow(s, [(cols[0] + bw + 6, T + 48), (cols[1] - 6, T + 48)], INK, 1.6)
    arrow(s, [(cols[1] + bw + 6, T + 48), (cols[2] - 6, T + 48)], INK, 1.6)
    arrow(s, [(cols[2] + bw / 2, T + bh + 6), (cols[2] + bw / 2, T + 164)], INK, 1.6)
    arrow(s, [(cols[2] - 6, T + 218), (cols[1] + bw + 6, T + 218)], INK, 1.6)
    arrow(s, [(cols[1] - 6, T + 218), (cols[0] + bw + 6, T + 218)], INK, 1.6)
    yy = s.footer(T + 310, "注：E2B 只登记 MISSING（缺页）事件。两个 vCPU 同时碰同一页时，第二次 UFFDIO_COPY 返回 EEXIST，忽略即可（第 13 篇）。")
    save(s, "04-2-UFFD缺页.svg", yy + 20)


def fig_04_seal():
    s = Svg()
    y0 = s.header("写保护“封条”：怎么区分读过的页和写过的页",
                  "UFFDIO_COPY 带上 UFFDIO_COPY_MODE_WP，填进去的页就贴着封条；以后被写，内核撕掉封条让写继续。"
                  "到打快照时，读 pagemap：在内存里、且没封条的页，就是写过的页。")
    T = y0 + 40
    cols = [("只读过的页", "读缺页 → 填页并贴封条", "之后只读", "在、有封条", "不算脏", GOOD),
            ("写缺页的页", "写缺页 → 填页不贴封条", "写", "在、无封条", "算脏", RISK),
            ("先读后写的页", "读缺页 → 填页并贴封条", "后来被写，封条被撕", "在、无封条", "算脏", RISK),
            ("没碰过的页", "从未缺页", "—", "不在", "不算脏", WHITE)]
    cw = (W - 2 * M - 3 * 24) / 4
    heads = ["填页时", "之后", "pagemap 看到", "判定"]
    for i, (t, a, b, c, d, role) in enumerate(cols):
        x = M + i * (cw + 24)
        box(s, x, T, cw, 50, KEY, t, None, 15)
        for k, v in enumerate([a, b, c]):
            s.text(x + 12, T + 86 + k * 70, heads[k], 12, MUTED)
            box(s, x, T + 94 + k * 70, cw, 44, WHITE, v, None, 13.5)
        box(s, x, T + 94 + 3 * 70, cw, 50, role, d, None, 16)
    yy = s.footer(T + 370, "注：这是 x86 上精确增量的来源。这套环境的 ARM 补丁填页时不再贴封条，于是“只读过的页”也被判成脏页（第 15 篇）。")
    save(s, "04-3-写保护封条.svg", yy + 20)


# ------------------------------------------------------------------ 第 5 篇
def fig_05_cow():
    s = Svg()
    y0 = s.header("写时复制：一百个沙箱共享一份模板，各自只存改过的块",
                  "所有沙箱读没改过的块时都去读同一份只读模板；写的时候才把那一块记到自己的私有文件里。"
                  "以后读这一块，先看自己有没有。")
    T = y0 + 40
    box(s, M + 300, T, W - 2 * M - 600, 90, STORE, "模板的根盘（5 GiB，只读，一份）", "所有同模板的沙箱共享", 17, 13)
    xs = [M + 120, M + 560, M + 1000]
    sizes = ["30 MB", "12 MB", "80 MB"]
    for i, x in enumerate(xs):
        box(s, x, T + 220, 340, 100, MINE, f"沙箱 {i + 1} 的改动 {sizes[i]}", "稀疏文件 + “哪些块是我的”位图", 15, 12.5)
        cxs = x + 170
        arrow(s, [(cxs, T + 214), (cxs, T + 96)], STORE[1], 1.6, label="读没改过的块", ldx=8, lanchor="start", lpos=0.5, ldy=4)
    yy = s.footer(T + 360, "注：合计 = 模板一份 + 各沙箱的改动（几十 MB 级）。拷一百份要 500 GB，这样只要 5 GB 多一点。")
    save(s, "05-1-写时复制.svg", yy + 20)


def fig_05_flat():
    s = Svg()
    y0 = s.header("两种组织多层数据的方式：逐层往下找，还是查一张拍平的表",
                  "A 是模板，B、C 是之后两次暂停的改动。读第 1000 块：链表式要从 C 往下一层层问；"
                  "E2B 的 header 是拍平的，每一层都带一张完整的表，查一次就知道数据在哪。")
    T = y0 + 40
    half = (W - 2 * M - 60) / 2
    # 左：链表式
    s.text(M, T + 10, "链表式：层数越多越慢", 16, INK, 600)
    for i, (n, sub) in enumerate([("C", "只有块 1000～1001"), ("B", "只有块 5000～5099"), ("A", "完整")]):
        box(s, M + 40, T + 34 + i * 92, half - 200, 64, STORE if n == "A" else MINE, f"build {n}", sub, 15, 12.5)
    for i, (t, c) in enumerate([("C 里有吗？有 → 读 C", MINE[2])]):
        pass
    s.text(M + half - 140, T + 70, "① 问 C", 13.5, INK, 600)
    s.text(M + half - 140, T + 162, "② 问 B", 13.5, INK, 600)
    s.text(M + half - 140, T + 254, "③ 问 A", 13.5, INK, 600)
    arrow(s, [(M + 40 + (half - 200) / 2, T + 100), (M + 40 + (half - 200) / 2, T + 124)], SUB, 1.5)
    arrow(s, [(M + 40 + (half - 200) / 2, T + 192), (M + 40 + (half - 200) / 2, T + 216)], SUB, 1.5)
    # 右：拍平
    RX = M + half + 60
    s.text(RX, T + 10, "拍平的映射表（E2B 的 header）：查一次", 16, INK, 600)
    rows = [("块 0～999", "A", 0), ("块 1000～1001", "C", 0), ("块 1002～4999", "A", 1002), ("块 5000～5099", "B", 0),
            ("块 5100～…", "A", 5100)]
    s.text(RX, T + 46, "C 的 header", 13, MUTED, 600)
    for i, (rg, b, off) in enumerate(rows):
        y = T + 56 + i * 46
        role = STORE if b == "A" else MINE
        hl = i == 1
        s.rect(RX, y, half, 40, "#FFF8E1" if hl else "#FFFFFF", NAT[1] if hl else HAIR, 1.6 if hl else 1, rx=6)
        s.text(RX + 16, y + 26, rg, 13.5, INK, 600 if hl else 400)
        s.pill(RX + half * 0.62, y + 20, "build " + b, role, 12.5)
        s.text(RX + half - 16, y + 26, f"偏移 {off}", 13, SUB, 400, "end", mono=True)
    s.text(RX, T + 56 + 5 * 46 + 22, "读第 1000 块 → 第 2 行 → C 文件第 0 块，结束", 14, NAT[2], 600)
    yy = s.footer(T + 360, "注：拍平的代价是，被任何 header 引用的那一层都必须留着；删掉中间的 B，C 读第 5000 块就会去一个不存在的文件里找。")
    save(s, "05-2-链表与拍平.svg", yy + 20)


# ------------------------------------------------------------------ 第 6 篇
def fig_06_link():
    s = Svg()
    y0 = s.header("同一个路径，不同的盘：每个 Firecracker 都打开 /fc-vm/rootfs.ext4",
                  "快照里记着根盘路径，所有从它恢复的沙箱都去打开同一个路径。orchestrator 用 unshare -m 给每个 Firecracker "
                  "一个独立的 mount 命名空间，在里面把 /fc-vm 挂成私有 tmpfs，再用符号链接接到各自的 NBD 设备。")
    T = y0 + 40
    cw = (W - 2 * M - 40) / 2
    for k, (sid, nbd) in enumerate([("沙箱 A", "/dev/nbd3"), ("沙箱 B", "/dev/nbd7")]):
        x = M + k * (cw + 40)
        s.rect(x, T, cw, 420, GUEST[0], GUEST[1], 1.3, rx=14, dash="6 4")
        s.text(x + 20, T + 30, f"{sid} 的 mount 命名空间", 15, GUEST[2], 600)
        box(s, x + 30, T + 50, cw - 60, 60, white(GUEST), "Firecracker 打开 /fc-vm/rootfs.ext4", "快照里记的固定路径", 14, 12)
        box(s, x + 30, T + 150, cw - 60, 60, WHITE, "/fc-vm 是私有 tmpfs", f"rootfs.ext4 → …/rootfs-{sid[-1]}-<随机>.link", 14, 12)
        box(s, x + 30, T + 250, cw - 60, 60, ORCH, f"/orchestrator/sandbox/rootfs-{sid[-1]}-<随机>.link",
            "orchestrator 改指向的把手；准备好前指向 /dev/null", 13.5, 12)
        box(s, x + 30, T + 350, cw - 60, 52, MINE, nbd, None, 15)
        for a, b in [(T + 116, T + 144), (T + 216, T + 244), (T + 316, T + 344)]:
            arrow(s, [(x + cw / 2, a), (x + cw / 2, b)], INK, 1.5)
    yy = s.footer(T + 460, "注：内核也一样：/fc-vm/<内核版本>/vmlinux.bin 链到 /fc-kernels/<内核版本>/vmlinux.bin。"
                           "文件名里的随机串让同一个沙箱 ID 暂停又恢复时，新旧两套文件不撞名。")
    save(s, "06-1-三跳链接.svg", yy + 20)


def fig_06_around():
    s = Svg()
    y0 = s.header("一个运行中的沙箱：Firecracker 和它周围的存储",
                  "左半边是硬盘：Firecracker 读写 /dev/nbdN，NBD 把请求交给 orchestrator，由写时复制和模板根盘回答。"
                  "右半边是内存：客户机内存在 Firecracker 进程里，缺页通过 UFFD 交给 orchestrator 填。")
    T = y0 + 40
    # orchestrator 带
    band(s, T, 190, ORCH, "orchestrator（template-manager 进程）")
    half = (W - 2 * M - 80) / 2
    LX, RX = M + 30, M + 50 + half + 20
    box(s, LX, T + 50, half - 20, 54, white(ORCH), "NBD 服务（接线员）", "按块回答读写", 14, 12)
    box(s, RX, T + 50, half - 20, 54, white(ORCH), "UFFD 处理程序（仓库管理员）", "按页填内存", 14, 12)
    box(s, LX, T + 120, (half - 30) / 2, 54, MINE, "COW 文件", "沙箱写过的块", 14, 12)
    box(s, LX + (half - 30) / 2 + 10, T + 120, (half - 30) / 2, 54, STORE, "模板根盘", "header + 本地缓存", 14, 12)
    box(s, RX, T + 120, half - 20, 54, STORE, "模板 memfile", "按 memfile.header 取，经本地缓存", 14, 12)
    # 中间设备
    MY = T + 240
    box(s, LX, MY, half - 20, 56, GUEST, "/dev/nbdN", "socketpair × 4，netlink 连接", 15, 12)
    arrow(s, [(LX + (half - 20) / 2, MY - 6), (LX + (half - 20) / 2, T + 196)], INK, 1.6, start=True)
    box(s, RX, MY, half - 20, 56, WHITE, "unix socket /tmp/uffd-<ID>-<随机>.sock", "握手时传一次 UFFD 句柄和内存布局", 14, 12)
    arrow(s, [(RX + (half - 20) / 2, MY - 6), (RX + (half - 20) / 2, T + 196)], INK, 1.6)
    # Firecracker 带
    FY = MY + 100
    band(s, FY, 170, GUEST, "独立 mount 命名空间里的 Firecracker 进程")
    box(s, LX, FY + 50, half - 20, 54, white(GUEST), "/fc-vm/rootfs.ext4 → .link → /dev/nbdN", "virtio-blk：客户机的 /dev/vda", 13.5, 12)
    box(s, RX, FY + 50, half - 20, 54, RISK, "客户机内存（2 MiB 大页）", "缺页 → UFFD → orchestrator", 14, 12)
    box(s, LX, FY + 116, W - 2 * M - 60, 40, white(GUEST), "客户机：/ 挂在 /dev/vda 上；程序读写内存和文件", None, 14)
    arrow(s, [(LX + (half - 20) / 2, FY + 44), (LX + (half - 20) / 2, MY + 62)], INK, 1.6, start=True)
    arrow(s, [(RX + (half - 20) / 2, FY + 44), (RX + (half - 20) / 2, MY + 62)], INK, 1.6)
    yy = s.footer(FY + 210, "注：第 11 篇讲上方的本地缓存，第 12 篇讲左半边，第 13 篇讲右半边。")
    save(s, "06-2-FC周围的存储.svg", yy + 20)


if __name__ == "__main__":
    for name in sorted(n for n in dir() if n.startswith("fig_")):
        globals()[name]()
