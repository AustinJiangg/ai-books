"""《E2B 沙箱快照回滚从零讲透》第 1～4 篇的配图。用法: python3 tools/figures/rb_p1.py"""
from rb_common import *  # noqa: F401,F403
from rb_common import W, M


# ------------------------------------------------------------------ 第 1 篇
def fig_01_flow():
    s = Svg()
    y0 = s.header("存档、失败、读档、再试：任务可以回到准备完成的那一刻",
                  "准备环境要好几分钟。在准备完成时存档 S；方案 A 失败后读档回 S，依赖、配置、进程和已加载的数据一起回来；"
                  "再试方案 B。读档不删除更新的存档，所以 A1 仍然可以回去。")
    T = y0 + 40
    # 主线
    prep = (M, T, 260, 90)
    box(s, *prep, KEY, "准备环境", "拉代码、装依赖、导数据、起服务\n几分钟", 16, 12.5)
    S = (M + 330, T + 15, 110, 60)
    box(s, *S, OK, "存档 S", None, 16)
    arrow(s, [(prep[0] + prep[2] + 4, T + 45), (S[0] - 4, T + 45)], INK, 1.6)
    A = (M + 520, T, 300, 90)
    box(s, *A, WHITE, "方案 A：升级组件、改配置、跑测试", None, 15)
    arrow(s, [(S[0] + S[2] + 4, T + 45), (A[0] - 4, T + 45)], INK, 1.6)
    A1 = (M + 560, T + 120, 110, 50)
    box(s, *A1, OK, "存档 A1", None, 14)
    arrow(s, [(A1[0] + 55, A[1] + A[3] + 4), (A1[0] + 55, A1[1] - 4)], MUTED, 1.3, dash="4 4")
    fail = (M + 900, T, 220, 90)
    box(s, *fail, RISK, "测试失败", "配置被覆盖、服务退出", 16, 12.5)
    arrow(s, [(A[0] + A[2] + 4, T + 45), (fail[0] - 4, T + 45)], INK, 1.6)
    # 读档回 S
    yb = T + 230
    arrow(s, [(fail[0] + 110, fail[1] + fail[3] + 4), (fail[0] + 110, yb), (S[0] + 30, yb), (S[0] + 30, S[1] + S[3] + 4)],
          RISK[1], 2)
    s.text((fail[0] + 110 + S[0] + 30) / 2 + 60, yb + 24, "读档回 S：几十毫秒，同一台沙箱", 13.5, RISK[2], 600, "middle")
    B = (M + 520, T + 300, 300, 90)
    box(s, *B, WHITE, "方案 B", "从 S 的现场出发", 15, 12.5)
    arrow(s, [(S[0] + 85, S[1] + S[3] + 4), (S[0] + 85, B[1] + 45), (B[0] - 4, B[1] + 45)], INK, 1.6)
    ok = (M + 900, T + 300, 220, 90)
    box(s, *ok, OK, "成功", "继续推进", 16, 12.5)
    arrow(s, [(B[0] + B[2] + 4, B[1] + 45), (ok[0] - 4, B[1] + 45)], INK, 1.6)
    # 右侧说明
    nx = M + 1180
    band(s, nx, T, W - M - nx, 390, KEY, "读档后回来的是")
    bullets(s, nx + 24, T + 90, ["依赖、配置文件", "后台服务进程（原来的 PID）", "进程里已加载的数据", "保存后被杀的进程复活",
                                  "保存后才起的进程消失"], 13.5, 46, maxw=W - M - nx - 50)
    yy = s.footer(T + 420, "注：读档要求承载沙箱的那台虚拟机还活着。宿主宕机、沙箱已被销毁之后的恢复，是原生快照的事（第 15 篇）。")
    save(s, "01-1-任务流.svg", yy + 20)


def fig_01_map():
    s = Svg()
    y0 = s.header("全书地图：一次存档或读档经过的五层",
                  "从上到下：SDK 把请求发到沙箱地址，orchestrator 里的代理截下交给 Checkpoint Service，账本记着存档树和磁盘层，"
                  "分叉版 Firecracker 做机械动作，KVM 和硬件记录脏页。右边是宿主本地的存档盘。")
    T = y0 + 30
    LW = 1050
    rows = [
        (CTL, "SDK", "sandbox.checkpoint.create / restore / list / delete", "第 1、5 篇"),
        (CTL, "代理 + Checkpoint Service（orchestrator 进程内）", "拦截 49984 · 鉴权 · 按沙箱排队 · 全量/增量决策 · 失败分级 · 计时", "第 5～7、13、14 篇"),
        (CTL, "账本（只在内存里）", "内存差分树 · 回滚集 · 磁盘层清单 · 引用计数 · 合并", "第 9、10、14 篇"),
        (FCR, "Firecracker（同一个进程，全程不重建）", "写快照 + 位图 · 导出脏页 · 原地回滚九阶段 · 设备与时间", "第 11、12 篇"),
        (FCR, "KVM / CPU", "脏页跟踪：HDBSS 硬件 / KVM 写保护 / 关闭", "第 8 篇"),
    ]
    y = T
    h = 86
    for i, (role, t, sub, ref) in enumerate(rows):
        box(s, M, y, LW, h, role, t, sub, 16, 13)
        tag(s, M + LW - 14, y + 10, ref, "end")
        if i < len(rows) - 1:
            arrow(s, [(M + 160, y + h + 3), (M + 160, y + h + 21)], INK, 1.5)
        y += h + 24
    sx = M + LW + 70
    band(s, sx, T, W - M - sx, y - 24 - T, STO, "宿主本地存档盘", "/orchestrator/build/checkpoints")
    items = ["snapfile：CPU、中断控制器、设备", "mem_diff：稀疏内存差分", "mem_bitmap：这一代的脏页位图", "rootfs.header：磁盘视图",
             "layers/：封存的磁盘层", "manifest.json：给人看"]
    yy = T + 90
    for it in items:
        box(s, sx + 18, yy, W - M - sx - 36, 50, WHITE, None, it, 13, 12.5)
        yy += 62
    for i in (1, 3):
        ry = T + i * (h + 24) + h / 2
        arrow(s, [(M + LW + 4, ry), (sx - 4, ry)], MUTED, 1.3, dash="4 4")
    yy2 = s.footer(y + 6, "注：沙箱里没有任何代理程序；四条设计原则见第 4 篇，八条顺序约束见第 7 篇，不变量清单见第 13 篇。")
    save(s, "01-2-全书地图.svg", yy2 + 20)


# ------------------------------------------------------------------ 第 2 篇
def fig_02_host():
    s = Svg()
    y0 = s.header("宿主上的一台沙箱长什么样",
                  "orchestrator 为每台沙箱持有四样东西：Firecracker 进程的接口、内存缺页处理程序、磁盘的 Overlay 与 NBD 设备、网络槽位。"
                  "读档要在不重建其中任何一样的前提下，把客户机变回过去。")
    T = y0 + 34
    OW = 900
    band(s, M, T, OW, 470, STO, "orchestrator 进程（宿主）")
    box(s, M + 24, T + 60, 250, 70, CTL, "代理（端口路由）", ":5007", 15, 12.5)
    box(s, M + 300, T + 60, 280, 70, CTL, "Checkpoint Service", "本方案加的部件", 15, 12.5)
    box(s, M + 606, T + 60, 270, 70, CTL, "沙箱表", None, 15)
    band(s, M + 24, T + 160, OW - 48, 290, STO, "Sandbox 对象（每台沙箱一个）")
    parts = [("process", "→ Firecracker 接口"), ("内存缺页处理（uffd）", "按需从模板拉页"), ("Overlay + NBD", "只读层 + 写层"), ("网络槽位", "netns · tap · IP")]
    pw = (OW - 48 - 40 - 3 * 14) / 4
    for i, (t, sub) in enumerate(parts):
        box(s, M + 44 + i * (pw + 14), T + 230, pw, 90, WHITE, t, sub, 14, 12.5)
    s.text(M + 44, T + 360, "读档时一个都不重建：进程、KVM 对象、tap、NBD 设备、内存映射，以及已在内存里的工作集。", 13.5, OK[2], 600)
    # 右侧进程
    rx = M + OW + 70
    rw = W - M - rx
    fc = (rx, T, rw, 200)
    band(s, *fc, FCR, "Firecracker 进程")
    box(s, rx + 20, T + 60, rw - 40, 120, white(GST), "客户机（microVM）", "内存 · vCPU · GIC · virtio 设备\nenvd 在里面执行命令", 15, 12.5)
    box(s, rx, T + 230, rw, 70, FCR, "KVM（/dev/kvm）", "客户机代码直接在 CPU 上跑", 15, 12.5)
    box(s, rx, T + 320, (rw - 14) / 2, 70, STO, "/dev/nbdX", "磁盘后端", 14, 12.5)
    box(s, rx + (rw + 14) / 2, T + 320, (rw - 14) / 2, 70, STO, "tap + netns", "网络", 14, 12.5)
    box(s, rx, T + 410, rw, 60, STO, "模板 memfile / rootfs", "在对象存储，按需拉取", 14, 12)
    arrow(s, [(M + OW + 4, T + 275), (rx - 4, T + 100)], INK, 1.5)
    arrow(s, [(rx + rw / 2, T + 204), (rx + rw / 2, T + 226)], INK, 1.4)
    yy = s.footer(T + 500, "注：用户沙箱都是从模板快照“恢复”出来的，不是从头开机；内存缺页时才从模板取，磁盘是只读底座加每台沙箱自己的写层（第 2 篇）。")
    save(s, "02-1-宿主上的一台沙箱.svg", yy + 20)


def fig_02_state():
    s = Svg()
    y0 = s.header("现场七项：沙箱里的回得去，沙箱外的回不去",
                  "前五项是机器里的东西，读档后都回到存档那一刻；时间要特殊处理：单调时钟倒退，墙钟被校回现在；"
                  "外部世界对沙箱的记忆回不去，要业务自己处理。")
    T = y0 + 34
    IW = 1000
    band(s, M, T, IW, 490, GST, "沙箱边界之内")
    items = [("内存", "GB 级 · 进程数据、内核结构、文件缓存"), ("vCPU 寄存器", "执行到哪条指令"), ("中断控制器 GIC", "哪些中断在等、被屏蔽"),
             ("设备状态", "virtio 队列位置、协商特性"), ("磁盘", "GB 级 · 根文件系统")]
    y = T + 60
    for t, sub in items:
        box(s, M + 24, y, 560, 54, white(GST), t, sub, 14.5, 12.5, align="start")
        s.pill(M + 700, y + 27, "回到那一刻", OK, 13)
        y += 64
    box(s, M + 24, T + 400, IW - 48, 64, FROZEN, "一致性：这五项必须在同一次暂停里一起处理", "否则内存和磁盘属于两个时刻（第 2 篇第四节）", 15, 12.5, style="dashed")
    tx = M + IW + 50
    tw = W - M - tx
    box(s, tx, T, tw, 160, NAT, "时间", "单调时钟：随 vCPU 寄存器倒退\n墙钟：读档返回前由 envd 校回现在\n用户态随机数状态：回退", 15, 12.5)
    band(s, tx, T + 190, tw, 300, RISK, "沙箱边界之外：回不去")
    bullets(s, tx + 20, T + 260, ["宿主连接跟踪表（本方案清理）", "TCP 对端、代理连接池（本方案断开）", "外部数据库、已发出的请求"], 13.5, 40,
            maxw=tw - 40)
    yy = s.footer(T + 520, "注：连接跟踪、连接池和时间由第 12 篇处理；外部副作用是任何快照方案的边界，业务需幂等、去重或补偿。")
    save(s, "02-2-七项状态与回滚边界.svg", yy + 20)


def fig_02_consistency():
    s = Svg()
    y0 = s.header("为什么必须是同一瞬间：内存 T1 加磁盘 T2 等于损坏",
                  "左边分两次暂停：内存在 T1 存，磁盘在 T2 存，中间客户机还在写。读档后文件系统的内存状态和磁盘块属于两个时刻。"
                  "右边在一次暂停里一起存，客户机没刷盘的数据留在内存镜像里，位置完全正确。")
    T = y0 + 40
    hw = (W - 2 * M - 60) / 2
    band(s, M, T, hw, 380, RISK, "错误：分两次暂停")
    # 时间轴
    ax = T + 110
    s.line(M + 30, ax, M + hw - 30, ax, SUB, 1.5, end=True)
    for x, lab in ((M + 120, "T1：存内存"), (M + hw - 160, "T2：存磁盘")):
        s.line(x, ax - 14, x, ax + 14, RISK[1], 2.4)
        s.text(x, ax - 22, lab, 13.5, RISK[2], 600, "middle")
    s.text((M + 120 + M + hw - 160) / 2, ax + 30, "客户机继续写：日志提交、块分配", 12.5, SUB, 400, "middle")
    bullets(s, M + 30, T + 220, ["日志记着已提交，内存里提交还没发生", "缓存里的块比磁盘上的还旧", "inode 说 10 个块，分配表说 8 个"], 13.5, 34,
            dot=RISK[1])
    s.text(M + 30, T + 340, "→ 报文件系统损坏，或者悄悄读到错数据", 14, RISK[2], 600)
    x2 = M + hw + 60
    band(s, x2, T, hw, 380, OK, "正确：一次暂停里一起存")
    s.rect(x2 + 30, T + 70, hw - 60, 190, FROZEN[0], FROZEN[1], 1.3, rx=10, dash="5 4")
    s.text(x2 + 50, T + 98, "冻结窗口", 15, FROZEN[2], 600)
    for i, t in enumerate(["保存内存", "保存磁盘", "保存 vCPU、GIC、设备状态"]):
        box(s, x2 + 60, T + 112 + i * 46, hw - 120, 38, WHITE, None, t, 14, 13)
    s.text(x2 + 30, T + 300, "没刷盘的数据留在内存镜像里，位置正确；", 13.5, INK)
    s.text(x2 + 30, T + 326, "读档后客户机会像什么都没发生一样把它刷下去。", 13.5, INK)
    yy = s.footer(T + 410, "注：这是全书八条顺序约束的第一条（第 7 篇），存档时由“写快照”和“封存写层”在同一个冻结窗口里完成（第 6 篇）。")
    save(s, "02-3-一致性反例.svg", yy + 20)


# ------------------------------------------------------------------ 第 3 篇
def fig_03_bitmap():
    s = Svg()
    y0 = s.header("同一份 2 GiB 内存的三种表示：页、位图、稀疏文件",
                  "内存按 4 KiB 一页管理，2 GiB 是 524288 页；位图一页一个比特，只有 64 KiB；稀疏文件把每个脏页写在它自己的偏移上，"
                  "逻辑上 2 GiB，实际只占写过的那几页。")
    T = y0 + 40
    n = 32
    cw = (W - 2 * M - 200) / n
    X0 = M + 200
    dirty = {3, 4, 5, 11, 17, 18, 26}
    # 行一：页
    s.text(M, T + 34, "内存的页", 15, INK, 600)
    for i in range(n):
        s.rect(X0 + i * cw + 1, T + 10, cw - 2, 40, "#D9D2FF" if i in dirty else "#FFFFFF", GST[1] if i in dirty else HAIR, 1, rx=3)
    s.text(X0, T + 70, "第 0 页", 12, MUTED)
    s.text(X0 + 3 * cw, T + 70, "脏页（被写过）", 12, GST[2], 600)
    # 行二：位图
    yb = T + 110
    s.text(M, yb + 30, "位图", 15, INK, 600)
    for i in range(n):
        v = "1" if i in dirty else "0"
        s.rect(X0 + i * cw + 1, yb + 10, cw - 2, 32, "#FFFFFF", HAIR, 1, rx=3)
        s.text(X0 + i * cw + cw / 2, yb + 32, v, 13, CTL[2] if v == "1" else MUTED, 600 if v == "1" else 400, "middle", mono=True)
    s.text(X0, yb + 62, "一页 1 比特：2 GiB → 524288 比特 = 64 KiB = 8192 个 64 位字", 12.5, SUB)
    # 行三：稀疏文件
    yc = yb + 110
    s.text(M, yc + 34, "稀疏文件", 15, INK, 600)
    i = 0
    while i < n:
        if i in dirty:
            s.rect(X0 + i * cw + 1, yc + 10, cw - 2, 40, STO[0], STO[1], 1.2, rx=3)
            i += 1
        else:
            j = i
            while j < n and j not in dirty:
                j += 1
            s.rect(X0 + i * cw + 1, yc + 10, (j - i) * cw - 2, 40, "#FFFFFF", HAIR, 1, rx=3, dash="4 3")
            if j - i >= 4:
                s.text(X0 + (i + j) / 2 * cw, yc + 35, "空洞（不占盘，读出来是 0）", 12, MUTED, 400, "middle")
            i = j
    s.text(X0, yc + 72, "偏移 = 页号 × 4096；ls 看到 2 GiB，du 看到的只有脏页那么大（st_blocks）", 12.5, SUB)
    yy = s.footer(yc + 104, "注：空洞读出来是 0，分不清“内容是 0”和“没存在这里”，所以每个差分文件旁边都要放一张位图（第 9 篇）。")
    save(s, "03-1-页位图稀疏文件.svg", yy + 20)


def fig_03_layers():
    s = Svg()
    y0 = s.header("写层叠在只读底座上：写只落最上层，读从上往下找",
                  "客户机的所有写都进写层，底座不动；读一个块先看写层，没有再往下找。存档时把写层“封”成只读层，"
                  "再换一个新的空写层，这一代的磁盘改动就整个留在了被封存的那一层里。")
    T = y0 + 40
    LX = M + 220
    LW = 900
    layers = [(GST, "活写层（稀疏文件）", [5, 9]), (STO, "封存层 2（只读）", [2, 9, 12]), (STO, "封存层 1（只读）", [2, 7]),
              (STO, "模板 rootfs（只读底座）", list(range(16)))]
    nb = 16
    bw = LW / nb
    for k, (role, t, blocks) in enumerate(layers):
        y = T + k * 80
        s.text(M, y + 32, t, 14, role[2], 600)
        for b in range(nb):
            on = b in blocks
            s.rect(LX + b * bw + 2, y + 8, bw - 4, 44, role[0] if on else "#FFFFFF", role[1] if on else HAIR, 1, rx=4,
                   dash=None if on else "3 3")
    # 读块 9
    bx = LX + 9 * bw + bw / 2
    arrow(s, [(bx, T - 22), (bx, T + 6)], OK[1], 2, label="读块 9：写层有，直接用", ldx=96, ldy=6, lsize=12.5, lcolor=OK[2])
    bx7 = LX + 7 * bw + bw / 2
    arrow(s, [(bx7, T - 22), (bx7, T + 2 * 80 + 6)], CTL[1], 1.8, dash="5 4")
    s.text(bx7 - 10, T - 30, "读块 7：一路往下，在封存层 1 找到", 12.5, CTL[2], 600, "end")
    rx = LX + LW + 50
    band(s, rx, T, W - M - rx, 300, KEY, "存档时")
    bullets(s, rx + 20, T + 84, ["暂停，刷屏障", "写层封成只读，叠到层栈顶上", "换一个新的空写层", "不复制任何一个块"], 13.5, 44,
            maxw=W - M - rx - 50)
    yy = s.footer(T + 340, "注：层多了，“一层层往下问”会变慢，实际实现用按块的归属索引直接定位（第 10 篇）。")
    save(s, "03-2-写层与只读底.svg", yy + 20)


def fig_03_reflink():
    s = Svg()
    y0 = s.header("有没有 reflink：“每代复制一份完整内存”的代价天差地别",
                  "XFS、Btrfs 的 reflink 让新文件和旧文件共享磁盘块，复制 2 GiB 只改元数据；ext4 没有 reflink，复制就是真读 2 GiB、写 2 GiB。"
                  "存档盘是 ext4，所以本方案只存差分，按页往祖先找。")
    T = y0 + 40
    hw = (W - 2 * M - 60) / 2
    for k, (role, t, sub, cost, note) in enumerate([
        (OK, "XFS / Btrfs：有 reflink", "复制 = 共享块，写时才分裂", "这一代没改：≈ 0", "成本只看改动量"),
        (RISK, "ext4：没有 reflink", "复制 = 真拷贝", "这一代没改：仍要拷 2 GiB", "成本和改动量脱钩，而且完全静默"),
    ]):
        x = M + k * (hw + 60)
        band(s, x, T, hw, 330, role, t, sub)
        ya = T + 90
        box(s, x + 30, ya, 200, 60, WHITE, "第 n-1 代", "2 GiB", 14, 12)
        box(s, x + hw - 230, ya, 200, 60, WHITE, "第 n 代", "复制 + 覆盖脏页", 14, 12)
        if k == 0:
            arrow(s, [(x + 234, ya + 30), (x + hw - 234, ya + 30)], OK[1], 1.6, dash="4 4", label="共享块（元数据）", ldy=-8)
        else:
            arrow(s, [(x + 234, ya + 30), (x + hw - 234, ya + 30)], RISK[1], 2.4, label="读 2 GiB + 写 2 GiB", ldy=-8)
        box(s, x + 30, T + 190, hw - 60, 54, role, cost, None, 15)
        s.text(x + 30, T + 290, note, 14, role[2], 600)
    yy = s.footer(T + 360, "注：磁盘那一半不受影响：封存写层只是改名，本来就不需要复制（第 10 篇）。")
    save(s, "03-3-reflink对比.svg", yy + 20)


# ------------------------------------------------------------------ 第 4 篇
def fig_04_compare():
    s = Svg()
    y0 = s.header("原生 pause / resume 与本方案：离场重建，还是原地回写",
                  "原生 pause 导出磁盘差分时必须关掉沙箱，resume 要新起进程、缺页把工作集拉回来；本方案存档只暂停一下就继续跑，"
                  "读档在同一个进程里只写回需要的页。950 上 0 MiB 档：pause 251.9 ms、resume 109.3 ms；存档 17.2 ms、读档 22.4 ms。")
    T = y0 + 40
    s.text(M, T, "原生 pause / resume", 16, RISK[2], 600)
    flow_h(s, M, T + 16, W - 2 * M, [(STO, "暂停", None), (FCR, "写 snapfile", "几 ms"), (STO, "导出内存差分", None),
                                      (RISK, "关掉沙箱", "进程退出、KVM 销毁、NBD 断开"), (STO, "导出磁盘差分", "上传"),
                                      (FCR, "resume：新进程", "建 VM、设备、网络"), (GST, "缺页拉回工作集", "成本推迟到之后")],
           h=96, gap=26, ts=14, ss=12)
    T2 = T + 180
    s.text(M, T2, "本方案 checkpoint / restore", 16, OK[2], 600)
    flow_h(s, M, T2 + 16, W - 2 * M, [(STO, "暂停", None), (FCR, "写快照 + 位图", "只写脏页"), (STO, "封存写层", "改名，不搬数据"),
                                       (OK, "恢复运行", "同一个进程"), (STO, "读档：暂停", None), (FCR, "原地写回回滚集", "CPU、设备状态"),
                                       (OK, "恢复运行", "立刻满速")], h=96, gap=26, ts=14, ss=12)
    rows = [["", "原生", "本方案"], ["成本和什么有关", "虚机大小（销毁、重建、换回工作集）", "改了多少、回退多远"],
            ["沙箱中断吗", "要关掉、要新进程", "只暂停几十毫秒"], ["进程死了还能恢复吗", "能", "不能"], ["能跨机器吗", "能", "不能"]]
    table(s, M, T2 + 170, [300, 560, W - 2 * M - 860], rows[1:], header=rows[0], ts=14)
    yy = s.footer(T2 + 400, "注：两者不是替代关系：原生管离场、长期保存、跨机器，本方案管活沙箱里的高频回退（第 15 篇）。")
    save(s, "04-1-原生与本方案对比.svg", yy + 20)


def fig_04_principles():
    s = Svg()
    y0 = s.header("四条设计原则，以及它们各落在哪些机制上",
                  "原则来自三条硬要求（高频、低延迟、不能中断）和五条约束（ARM、ext4、纯加法、不装代理、版本成对）。"
                  "全书第二部分的每一篇，都在实现其中一两条。")
    T = y0 + 40
    cols = [
        (CTL, "1. 成本只与改动量挂钩", ["内存只存本代脏页（第 9 篇）", "封存写层只改名（第 10 篇）", "不等数据刷盘（第 10 篇）",
                                   "只写回回滚集（第 9、11 篇）", "唯一固定开销：全量根"]),
        (FCR, "2. 不重建任何宿主资源", ["同一个 Firecracker 进程", "KVM 对象、中断注册不动", "tap、网络槽位、NBD 设备不动",
                                    "内存映射与工作集保留", "代价：离不开活沙箱（第 14 篇）"]),
        (RISK, "3. 宁可报错，不可静默损坏", ["缺位图就报错，不悄悄全量回滚", "链断了拒绝读档", "账本对不上就标记污染",
                                        "设备组成不一致就拒绝", "提交点前查完能查的（第 11、13 篇）"]),
        (OK, "4. 降级要说出来", ["启动日志报能力和理由", "每次存档回报 mem_mode", "Firecracker 自报后端",
                              "可设“没有 HDBSS 就启动失败”", "（第 8 篇）"]),
    ]
    n = len(cols)
    gap = 24
    cw = (W - 2 * M - gap * (n - 1)) / n
    for i, (role, t, items) in enumerate(cols):
        x = M + i * (cw + gap)
        box(s, x, T, cw, 70, role, t, None, 16)
        y = T + 86
        for it in items:
            box(s, x, y, cw, 52, WHITE, None, it, 13, 13)
            y += 62
    yy = s.footer(T + 410, "注：原则二和“只能在活沙箱上回滚”是同一件事的两面；原则三因为没有兜底重建路线，从好习惯变成了硬要求。")
    save(s, "04-2-四条原则.svg", yy + 20)


def fig_04_alternatives():
    s = Svg()
    y0 = s.header("三条被否决的路线，以及最终的分工",
                  "在客户机里装代理恢复不了内核态和磁盘；单独的快照服务进程碰不到 orchestrator 私有的活对象；全部塞进 Firecracker "
                  "又够不着磁盘、还要开大安全口子。最终：语义在 orchestrator，机械动作在 Firecracker。")
    T = y0 + 40
    alts = [("在客户机里跑代理（CRIU 式）", ["恢复不了内核态：文件缓存、协议栈", "代理自己怎么存档？", "要分发、升级、权限", "解决不了磁盘"]),
            ("宿主上单独的快照服务", ["每一步都要碰 orchestrator 私有对象", "Overlay 指针、NBD、网络槽位", "要么复制生命周期管理", "要么设计跨进程所有权协议"]),
            ("全部放进 Firecracker", ["磁盘根本不在 Firecracker 里", "分叉膨胀成存储子系统", "跟上游同步变难", "seccomp 要开很多口子"])]
    aw = (W - 2 * M - 48) / 3
    for i, (t, items) in enumerate(alts):
        x = M + i * (aw + 24)
        band(s, x, T, aw, 250, RISK, "✗ " + t)
        bullets(s, x + 22, T + 80, items, 13.5, 40, dot=RISK[1], maxw=aw - 50)
    T2 = T + 300
    s.text(M, T2, "最终分工", 16, INK, 600)
    lw = (W - 2 * M - 80) / 2
    box(s, M, T2 + 20, lw, 150, CTL, "orchestrator：语义", "存档树、回滚集、按页找内容\n磁盘层、引用计数、合并、失败分级", 16, 13)
    box(s, M + lw + 80, T2 + 20, lw, 150, FCR, "Firecracker：机械动作", "“把这张位图指定的页，从这个文件写进客户机内存”\n恢复 CPU、中断控制器、设备；不知道树是什么", 16, 13)
    arrow(s, [(M + lw + 4, T2 + 95), (M + lw + 76, T2 + 95)], INK, 1.6, start=True)
    yy = s.footer(T2 + 200, "注：Firecracker 只加了三处：快照请求多一个 dirty_bitmap_path 字段，新增 save-dirty-bitmap 和 rollback 两个接口（第 11 篇）。")
    save(s, "04-3-备选路线与最终分工.svg", yy + 20)


if __name__ == "__main__":
    fig_01_flow()
    fig_01_map()
    fig_02_host()
    fig_02_state()
    fig_02_consistency()
    fig_03_bitmap()
    fig_03_layers()
    fig_03_reflink()
    fig_04_compare()
    fig_04_principles()
    fig_04_alternatives()
