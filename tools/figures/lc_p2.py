"""《E2B 模板构建、沙箱启动与暂停恢复从零讲透》第 5～9 篇的配图。用法: python3 tools/figures/lc_p2.py"""
from lc_common import *  # noqa: F401,F403
from lc_common import W, M


# ------------------------------------------------------------------ 第 5 篇
def fig_05_image_vs_template():
    s = Svg()
    y0 = s.header("镜像与模板：一堆文件 vs 一台开到一半就冻住的机器",
                  "镜像只是文件层；虚拟机要从开机走到 envd 就绪，要几秒甚至更久。模板把这几秒提前做掉，在就绪那一刻存成快照。")
    T = y0 + 40
    lw = (W - 2 * M - 100) / 2
    band(s, M, T, lw, 330, KEY, "Docker 镜像")
    for i, t in enumerate(["第 3 层：pip install pandas", "第 2 层：apt-get install python3", "第 1 层：ubuntu:22.04"]):
        box(s, M + 30, T + 70 + i * 70, lw - 60, 56, WHITE, None, t, 14, 13.5)
    s.text(M + 30, T + 310, "只是文件；容器启动 = 起一个进程", 13.5, SUB)
    rx = M + lw + 100
    band(s, rx, T, lw, 330, GST, "E2B 模板")
    box(s, rx + 30, T + 70, lw - 60, 56, white(GST), None, "内核已启动 · systemd 已拉起服务", 14, 13.5)
    box(s, rx + 30, T + 140, lw - 60, 56, white(GST), None, "envd 已在运行 · 用户服务已启动", 14, 13.5)
    box(s, rx + 30, T + 210, lw - 60, 56, white(STO), None, "内存 + 磁盘 + CPU 状态，存成快照", 14, 13.5)
    s.text(rx + 30, T + 310, "一台冻住的机器；启动 = 从这一刻接着跑", 13.5, GST[2], 600)
    arrow(s, [(M + lw + 8, T + 165), (rx - 8, T + 165)], INK, 2, label="构建", ldy=-10)
    T2 = T + 370
    table(s, M, T2, [360, 600, 540], [["开机、内核初始化", "要", "构建时做掉"], ["systemd 拉起几十个服务", "要", "构建时做掉"],
                                      ["envd 与用户服务启动", "要", "构建时做掉"]],
          header=["启动一台沙箱时", "如果每次从镜像开机", "用模板快照"])
    f = s.footer(T2 + 190, "这就是 Sandbox.create 能在一百多毫秒内可用的根本原因。")
    save(s, "05-1-镜像与模板.svg", f + 20)


def fig_05_pipeline():
    s = Svg()
    y0 = s.header("构建流水线：五个阶段",
                  "顺序固定。每个阶段先算 hash 查层缓存，命中就整段跳过；没命中才起虚拟机干活。finalize 产出模板本身，optimize 只改元数据。")
    T = y0 + 40
    items = [(CTL, "base", "镜像 → ext4；busybox 装系统；systemd 开机"),
             (CTL, "默认用户", "建 user，加 sudo 权限"),
             (CTL, "steps", "每条指令一层"),
             (OK, "finalize", "配置、启动命令、等就绪、拍快照"),
             (KEY, "optimize", "恢复两次，记预取表")]
    bx = flow_h(s, M, T, W - 2 * M, items, h=120, gap=36, ts=17, ss=13)
    outs = ["第一层快照", "一层快照", "每条一层", "最终快照 = 模板", "不产新层"]
    for (x, y, w, h), o in zip(bx, outs):
        s.pill(x + w / 2, y + h + 34, o, STO, 13)
    T2 = T + 220
    table(s, M, T2, [260, 500, 740],
          [["base", "镜像名、磁盘大小、provision 版本", "最贵、最易错；基础镜像不变就整段跳过"],
           ["steps", "上一层 hash + 指令文本 + 上传文件的 hash", "改了第 N 条，从第 N 条起重做"],
           ["finalize / optimize", "—", "从不查缓存，每次都重做"]],
          header=["阶段", "hash 由什么决定", "缓存效果"])
    f = s.footer(T2 + 200, "每个阶段的时限：provision 5 分钟、base 层 10 分钟、每条指令 1 小时、等就绪 10 分钟。")
    save(s, "05-2-构建流水线.svg", f + 20)


def fig_05_loop():
    s = Svg()
    y0 = s.header("构建就是反复“启动—干活—暂停”",
                  "每一层都是同一个动作：从上一层快照恢复一台虚拟机，在里面干活，再暂停成新一层。用的是和用户沙箱同一套 ResumeSandbox 和 Pause。")
    T = y0 + 40
    layers = ["base", "指令 1", "指令 2", "指令 3", "finalize"]
    n = len(layers)
    cw = (W - 2 * M - (n - 1) * 24) / n
    for i, t in enumerate(layers):
        x = M + i * (cw + 24)
        box(s, x, T, cw, 60, STO, f"快照：{t}", None, 14.5)
        if i < n - 1:
            xx = x + cw / 2
            box(s, xx + 10, T + 90, cw + 4, 46, OK, "恢复", None, 13.5)
            box(s, xx + 10, T + 146, cw + 4, 46, WHITE, "执行指令", None, 13.5)
            box(s, xx + 10, T + 202, cw + 4, 46, CTL, "暂停", None, 13.5)
            arrow(s, [(xx, T + 64), (xx, T + 113), (xx + 6, T + 113)], MUTED, 1.3)
            arrow(s, [(xx + cw + 18, T + 225), (x + cw + 24 + cw / 2, T + 225), (x + cw + 24 + cw / 2, T + 64)], MUTED, 1.3)
    T2 = T + 290
    table(s, M, T2, [360, 560, 580],
          [["谁发起", "template-manager", "用户的 SDK"], ["能不能上网", "base 装包时可以", "按用户配置"],
           ["暂停之后", "立刻拿新一层接着构建", "沙箱离场，等用户恢复"], ["转几圈", "指令有几条转几圈，外加 base、finalize", "一圈"]],
          header=["", "构建时", "用户使用时"])
    f = s.footer(T2 + 240, "推论：暂停的所有特性和问题都会在构建的每一层重演，例如 ARM 上的“读即脏”（第 19 篇）。")
    save(s, "05-3-构建即启动暂停.svg", f + 20)


# ------------------------------------------------------------------ 第 6 篇
def fig_06_unpack():
    s = Svg()
    y0 = s.header("镜像解包成 ext4",
                  "按最大尺寸造一块空 ext4；挂载后把各层并行解包到各自目录，用 overlayfs 叠成一个只读视图，rsync 进磁盘；"
                  "最后检查、收缩、再检查。")
    T = y0 + 40
    items = [(CTL, "拉镜像", "指定平台；拉下来再查一次架构"),
             (STO, "造空 ext4", "约 24 GiB 上限；每 4 KiB 一个 inode；不留 root 预留"),
             (STO, "各层并行解包", "layer-0、layer-1……"),
             (STO, "overlayfs 叠起来", "删除与覆盖交给内核处理"),
             (STO, "rsync 进磁盘", "保留权限、符号链接、硬链接"),
             (OK, "查 → 缩 → 查", "收缩到刚好装下")]
    flow_h(s, M, T, W - 2 * M, items, h=130, gap=30, ts=15, ss=12.5)
    f = s.footer(T + 170, "上游把平台写死成 amd64，这是搬到 ARM 要改的第一处（第 9 篇）。")
    save(s, "06-1-镜像解包.svg", f + 20)


def fig_06_two_vms():
    s = Svg()
    y0 = s.header("base 阶段的两台虚拟机",
                  "基础镜像里通常没有 systemd，要装它又得先有一个在运行的系统。解法是开两次机：第一次 busybox 当 1 号进程装好 systemd，"
                  "第二次 systemd 正式开机，等 envd 就绪后暂停成第一层。两台共用同一个磁盘文件。")
    T = y0 + 40
    lw = (W - 2 * M - 80) / 2
    band(s, M, T, lw, 430, KEY, "第一台：busybox 当 1 号进程")
    st = [("挂载 /proc /sys /dev /tmp /run", None), ("运行 provision.sh", "输出加 [external] 前缀，宿主过滤后转成构建日志"),
          ("sync，冻结根文件系统", None), ("打印 E2B_PROVISIONING_EXIT:<码>", "没有 envd，只能靠一行文本回报"),
          ("sleep infinity，等宿主关机", None)]
    steps(s, M + 20, T + 60, lw - 40, st, ts=14, ss=12)
    s.text(M + 20, T + 415, "唯一允许上网；限时 5 分钟", 13, KEY[2], 600)
    rx = M + lw + 80
    band(s, rx, T, lw, 430, GST, "第二台：systemd 正式开机")
    st2 = [("检查磁盘完整性，扩到要求的空闲空间", None), ("systemd 当 1 号进程开机", None), ("拉起 envd 等服务", None),
           ("等 envd 能应答，刷盘", None), ("暂停 → 第一层快照", None)]
    steps(s, rx + 20, T + 60, lw - 40, st2, ts=14, ss=12)
    arrow(s, [(M + lw + 6, T + 215), (rx - 6, T + 215)], INK, 1.8, label="关机", ldy=-10)
    box(s, M, T + 460, W - 2 * M, 56, STO, None, "两台虚拟机用宿主上同一个磁盘文件：第一台装好的软件，第二台开机时就在", 14, 13.5)
    f = s.footer(T + 540, "模板若从另一个模板派生，base 阶段整段不跑，直接拿那个模板的最后一层当起点。")
    save(s, "06-2-两台沙箱.svg", f + 20)


def fig_06_inject():
    s = Svg()
    y0 = s.header("注入清单：E2B 往镜像顶上追加的两层文件",
                  "用户镜像里没有 E2B 的东西。解包之前，追加一层文件和一层符号链接。")
    T = y0 + 40
    rows = [["/usr/bin/envd", "沙箱里的管家"], ["/usr/local/bin/provision.sh", "第一次开机时运行的装机脚本"],
            ["/usr/bin/busybox、/usr/bin/init", "第一次开机的 1 号进程与工具箱"],
            ["/etc/inittab、/etc/init.d/rcS", "busybox 当 init 时的剧本"],
            ["/etc/systemd/system/envd.service", "让 systemd 拉起 envd（ARM 版去掉了 cgroup 指令）"],
            ["/etc/hostname、hosts、resolv.conf", "主机名与 DNS"],
            ["journald、networkd 的 watchdog 覆盖", "关掉看门狗：快照恢复会让时钟跳变，看门狗会误判服务卡死"],
            ["串口免登录", "调试时从串口直接进系统"],
            ["multi-user.target.wants/ 下两条链接", "启用 envd 与 chrony，等同 systemctl enable"]]
    table(s, M, T, [560, 940], rows, header=["文件", "用途"], roles=[None] * 6 + [RISK, None, None])
    f = s.footer(T + 470, "关看门狗这一行是“一切皆快照”的副作用：系统软件默认假设时间连续流逝，快照打破了这个假设。")
    save(s, "06-3-注入清单.svg", f + 20)


# ------------------------------------------------------------------ 第 7 篇
def fig_07_layer_per_step():
    s = Svg()
    y0 = s.header("一条指令一层：恢复 → 执行 → 暂停",
                  "层是缓存的单位。每一层都是一个 build ID，只存这条指令改动的内存页和磁盘块。")
    T = y0 + 40
    ins = [("FROM ubuntu:22.04", "base 层"), ("RUN apt-get install python3", "层 1"), ("RUN pip install pandas", "层 2"),
           ("WORKDIR /home/user", "层 3")]
    y = T
    for i, (cmd, lay) in enumerate(ins):
        s.text(M, y + 34, cmd, 15, INK, 600, mono=True)
        if i > 0:
            flow_h(s, M + 470, y, 700, [(OK, "从上一层恢复", None), (WHITE, "通过 envd 执行", None), (CTL, "暂停", None)], h=52, gap=40, ts=13.5)
        else:
            box(s, M + 470, y, 700, 52, KEY, None, "第 6 篇：两次开机后暂停", 13.5, 13)
        box(s, M + 1220, y, W - 2 * M - 1220, 52, STO, lay, None, 14.5)
        y += 76
    f = s.footer(y + 10, "一条一层的好处：改了最后一条，只从倒数第二层接着做，不用把装 Python、装 pandas 重来一遍。")
    save(s, "07-1-一条指令一层.svg", f + 20)


def fig_07_hash():
    s = Svg()
    y0 = s.header("层 hash 链：任何一环变了，之后全部重做",
                  "本层 hash = SHA-256(上一层 hash ; 指令类型 ; 参数 ; 上传文件的 hash)。hash 只看文本，不看结果：软件源更新了，文本没变，仍然命中。")
    T = y0 + 40
    labels = ["base", "默认用户", "指令 1", "指令 2", "指令 3", "finalize"]
    n = len(labels)
    gap = 34
    bw = (W - 2 * M - gap * (n - 1)) / n
    for row, (title, changed) in enumerate([("第一次构建", -1), ("改了指令 2 之后", 3)]):
        y = T + row * 170
        s.text(M, y, title, 15, INK, 600)
        for i, t in enumerate(labels):
            x = M + i * (bw + gap)
            if changed < 0:
                role, sub = WHITE, "构建"
            elif i == n - 1:
                role, sub = RISK, "从不查缓存"
            elif i < changed:
                role, sub = OK, "命中，跳过"
            else:
                role, sub = RISK, "hash 变了，重做"
            box(s, x, y + 16, bw, 76, role, t, sub, 15, 12.5)
            if i < n - 1:
                arrow(s, [(x + bw + 3, y + 54), (x + bw + gap - 3, y + 54)], INK, 1.4)
    f = s.footer(T + 330, "想强制重做可以跳过缓存构建。E2B 的“层”是整台虚拟机的快照，包含内存，这一点和 Docker 的层不同。")
    save(s, "07-2-层hash链.svg", f + 20)


def fig_07_run():
    s = Svg()
    y0 = s.header("一条 RUN 的路径",
                  "template-manager 从上一层恢复构建虚拟机，通过 orchestrator 内置代理连到 envd 的进程服务；envd 以当前用户、目录和环境变量"
                  "启动 bash -l -c；输出流回构建日志。走的是数据面，和用户的 commands.run 同一条路。")
    T = y0 + 40
    flow_h(s, M, T, W - 2 * M, [(CTL, "template-manager", "恢复上一层的虚拟机"), (CTL, "orchestrator 代理", "送进沙箱网络"),
                                (GST, "envd 进程服务", "以当前用户、目录、环境变量"), (GST, "bash -l -c", "pip install pandas")],
           h=100, gap=60)
    T2 = T + 140
    box(s, M, T2, 700, 70, KEY, "输出", "stdout / stderr 流式传回 → 加步骤编号 → 构建日志 → SDK 轮询看到", 15, 12.5)
    box(s, M + 740, T2, W - 2 * M - 740, 70, KEY, "结束", "退出码非零：构建失败；为零：刷盘 → 暂停成新一层", 15, 12.5)
    T3 = T2 + 110
    table(s, M, T3, [300, 600, 600],
          [["RUN", "不改", "每条是独立的 shell，export 和 cd 不会带到下一条"], ["ENV / ARG", "改环境变量", "值送进虚拟机求值一次，$PATH 能展开"],
           ["WORKDIR", "改工作目录", ""], ["USER", "改用户", "openEuler 上用 useradd、wheel 组（第 9 篇）"],
           ["COPY / ADD", "不改", "文件先上传到存储，再通过 envd 的文件服务写进去"]],
          header=["指令", "当前状态（用户、目录、环境变量）", "备注"])
    f = s.footer(T3 + 290, "最终的当前状态写进模板元数据，启动沙箱时交给 envd 当默认用户和目录。")
    save(s, "07-3-RUN的路径.svg", f + 20)


# ------------------------------------------------------------------ 第 8 篇
def fig_08_finalize():
    s = Svg()
    y0 = s.header("finalize 的时序：最后一次开机",
                  "总是重新开一台虚拟机（最终层的磁盘路径要指向最终 build ID）。跑配置脚本，启动用户服务，每 2 秒检查一次就绪，"
                  "确认服务没崩，刷盘，拍快照。")
    T = y0 + 40
    items = [(OK, "重新开机", None), (WHITE, "configure.sh", "确保用户、复制默认文件、权限、swap\n5 分钟"),
             (WHITE, "start 命令", "后台一直跑"), (WHITE, "ready 命令", "每 2 秒一次\n最多 10 分钟"),
             (WHITE, "确认 start 仍在跑", None), (STO, "刷盘", "缓存落到磁盘"), (CTL, "拍快照", "= 模板")]
    flow_h(s, M, T, W - 2 * M, items, h=130, gap=22, ts=14.5, ss=12)
    T2 = T + 170
    table(s, M, T2, [460, 1040],
          [["没有 start 也没有 ready", "跑完配置脚本就拍快照：冻住的那一刻是“系统刚配好”"],
           ["有 start 没写 ready", "默认 sleep 20：固定等 20 秒，可能等不够也可能等太久"],
           ["都有", "ready 成功、start 仍在运行，才拍快照"]],
          header=["情况", "行为"])
    f = s.footer(T2 + 170, "刷盘不能省：内存和磁盘必须一致；文件缓存里没落盘的写，在磁盘上就是缺的。")
    save(s, "08-1-finalize时序.svg", f + 20)


def fig_08_at_ready():
    s = Svg()
    y0 = s.header("快照拍在就绪那一刻",
                  "快照记下的是那一刻的全部状态；以后每次恢复都从同一刻接着跑。拍得越晚，每次恢复省下的越多，只花一次。")
    T = y0 + 50
    tl = W - 2 * M
    s.line(M, T + 60, M + tl, T + 60, INK, 2, end=True)
    marks = [(0.03, "开机"), (0.22, "内核就绪"), (0.42, "systemd 拉起服务"), (0.62, "envd 就绪"), (0.82, "用户服务就绪")]
    for p, t in marks:
        x = M + tl * p
        s.circle(x, T + 60, 6, INK)
        s.text(x, T + 40, t, 14, INK, 600, "middle")
    xs = M + tl * 0.86
    s.line(xs, T + 20, xs, T + 100, RISK[1], 2.5)
    s.pill(xs, T + 120, "拍快照", RISK, 14)
    T2 = T + 170
    table(s, M, T2, [460, 520, 520],
          [["开机前", "每次恢复都要从头开机", "几秒"], ["envd 就绪", "恢复出来 envd 就能接命令", "省掉开机与服务启动"],
           ["用户服务就绪（E2B 的做法）", "恢复出来 Jupyter 等服务已经可用", "连用户服务的启动也省了"]],
          header=["快照拍在", "每次恢复后", "效果"], roles=[None, None, OK])
    T3 = T2 + 210
    table(s, M, T3, [460, 520, 520],
          [["所有沙箱内存一模一样", "从同一张快照恢复", "/init 注入不同身份、令牌、环境变量"],
           ["时钟停在构建那一刻", "快照冻结了时间", "恢复后校时"], ["看门狗误判服务卡死", "时钟跳变", "构建时就关掉看门狗"]],
          header=["副作用", "原因", "处理"])
    f = s.footer(T3 + 200, "构建比启动贵几个数量级，但对一个模板只做一次；之后成千上万次启动都直接享用成果。")
    save(s, "08-2-拍在就绪.svg", f + 20)


def fig_08_prefetch():
    s = Svg()
    y0 = s.header("预取表：恢复后会访问哪些内存块、按什么顺序",
                  "optimize 从最终快照恢复两次，记下每次恢复后经缺页进来的块及其顺序，取两次的交集写进 metadata.json。"
                  "启动时按这张表在后台提前搬。")
    T = y0 + 40
    def seq(y, title, blocks, role):
        s.text(M, y + 30, title, 15, INK, 600)
        x = M + 220
        for b in blocks:
            s.rect(x, y + 8, 56, 36, role[0], role[1], 1.2, rx=5)
            s.text(x + 28, y + 32, str(b), 13.5, role[2], 600, "middle")
            x += 66
    seq(T, "第一次恢复", [12, 3, 47, 8, 91, 20, 5, 66], WHITE)
    seq(T + 70, "第二次恢复", [12, 3, 47, 8, 20, 5, 33, 66], WHITE)
    seq(T + 160, "取交集（预取表）", [12, 3, 47, 8, 20, 5, 66], OK)
    s.text(M + 220, T + 240, "91 只在第一次出现、33 只在第二次出现：偶然访问，滤掉", 13.5, SUB)
    rx = M + 820
    box(s, rx, T, W - M - rx, 220, KEY, "为什么取交集", "只留“每次恢复都一定会用到”的块\n代价：可能漏掉只在一次运行里出现、但其实常用的块\n\noptimize 是尽力而为：失败只记警告，模板照常可用", 15, 13)
    f = s.footer(T + 280, "optimize 不产生新层，只修改最终那一层的元数据。")
    save(s, "08-3-预取表.svg", f + 20)


# ------------------------------------------------------------------ 第 9 篇
def fig_09_diff():
    s = Svg()
    y0 = s.header("构建路径上为 ARM 做的修改",
                  "三类：写死了架构的地方、发行版不同的地方、系统环境不同的地方；另加存储后端。")
    T = y0 + 36
    rows = [["架构", "镜像平台写死 amd64", "拉到 x86 版或被架构检查拦下", "改成 arm64"],
            ["架构", "只内嵌一份 x86 busybox", "ARM 虚拟机第一次开机就失败", "内嵌两份按架构选；用 glibc 版"],
            ["发行版", "provision.sh 只认 apt", "openEuler 用 dnf", "读 /etc/os-release 分支"],
            ["发行版", "装 12 个包", "部分包装不上", "精简到 9 个必需的"],
            ["发行版", "adduser 与 sudo 组", "没有 adduser；组叫 wheel", "先探测再分支"],
            ["发行版", "configure.sh 用 bash 语法", "早期 busybox 里没有 bash", "改成纯 sh"],
            ["系统环境", "envd 单元带 cgroup 指令", "guest 环境里不适用", "去掉"],
            ["系统环境", "宿主不是 cgroup v2 就报错", "部分宿主是 v1", "v1 时跳过初始化"],
            ["系统环境", "读 CPU 家族与型号", "ARM 上读不到，报错", "给兜底值"],
            ["存储", "默认 Google 对象存储", "离线环境连不上", "新增 MinIO 并设为默认"]]
    roles = [FCR, FCR, GST, GST, GST, GST, STO, STO, STO, CTL]
    y = T
    widths = [150, 400, 450, 500]
    y = table(s, M, y, widths, rows, header=["类别", "原来", "问题", "改成"])
    f = s.footer(y + 10, "改法的共同点：先探测、再分支，同一份代码既能构建 Ubuntu 模板，也能构建 openEuler 模板。")
    save(s, "09-1-构建差异总表.svg", f + 20)


def fig_09_distro():
    s = Svg()
    y0 = s.header("发行版分支：先探测，再走各自的路",
                  "provision.sh 读 /etc/os-release；默认用户、USER 指令和 configure.sh 看有没有 /etc/debian_version、有没有 wheel 组。")
    T = y0 + 40
    box(s, W / 2 - 230, T, 460, 70, KEY, "探测", "/etc/os-release · /etc/debian_version · getent group wheel", 16, 12.5)
    lw = (W - 2 * M - 80) / 2
    band(s, M, T + 120, lw, 290, CTL, "Ubuntu / Debian")
    band(s, M + lw + 80, T + 120, lw, 290, KEY, "openEuler / RHEL 系")
    left = ["查包：dpkg-query", "装包：apt-get install", "建用户：adduser --disabled-password", "sudo 组：sudo"]
    right = ["查包：rpm -q", "装包：dnf install", "建用户：useradd -m -s /bin/bash（家目录已在时用 -M 再复制默认文件）", "sudo 组：wheel"]
    bullets(s, M + 24, T + 185, left, 14.5, 52, maxw=lw - 60)
    bullets(s, M + lw + 104, T + 185, right, 14.5, 52, maxw=lw - 60)
    arrow(s, [(W / 2 - 120, T + 74), (M + lw / 2, T + 116)], INK, 1.5)
    arrow(s, [(W / 2 + 120, T + 74), (M + lw + 80 + lw / 2, T + 116)], INK, 1.5)
    f = s.footer(T + 440, "不认识的发行版直接报错，不猜。")
    save(s, "09-2-发行版分支.svg", f + 20)


def fig_09_oom():
    s = Svg()
    y0 = s.header("一次远离病因的故障链",
                  "症状在 api（503、部署超时），病因在 template-manager 的内存上限，中间隔了 Nomad。终点的报错里没有一个字提到内存。")
    T = y0 + 40
    items = [(RISK, "病因", "200 MB 镜像、跳过缓存构建；解包的页缓存 + tmpfs 页记在 8 GiB 上限里"),
             (RISK, "内核杀进程", "tmpfs 页不能回收，交换分区无余量"),
             (KEY, "Nomad 反复重启", "次数用完，任务标记失败"),
             (KEY, "api 发现 0 个节点", "/health 一直 503"),
             (KEY, "部署脚本", "等 api 健康超时")]
    flow_h(s, M, T, W - 2 * M, items, h=130, gap=36, ts=15, ss=12.5)
    T2 = T + 180
    s.text(M, T2, "修法的来回", 17, INK, 600)
    steps(s, M, T2 + 20, W - 2 * M, [("8 GiB → 32 GiB", "实测能通过一次 200 MB 基础镜像的完整重建"),
                                     ("32 GiB → 256 GiB", "在 1 TB 内存的机器上当作“跑飞了也不拖垮整机”的护栏"),
                                     ("换到 128 GiB 的机器：256 GiB 调度不上", "orchestrator 永远起不来，症状与第一次一模一样"),
                                     ("回到 32 GiB", "配置旁写明：太小会被杀，太大会调度不上")], ts=14.5, ss=12.5)
    f = s.footer(T2 + 330, "这个上限不包括虚拟机内存（大页另记账）；“同时跑几十台沙箱没事”不能说明它够用。")
    save(s, "09-3-远离病因的故障链.svg", f + 20)


if __name__ == "__main__":
    fig_05_image_vs_template()
    fig_05_pipeline()
    fig_05_loop()
    fig_06_unpack()
    fig_06_two_vms()
    fig_06_inject()
    fig_07_layer_per_step()
    fig_07_hash()
    fig_07_run()
    fig_08_finalize()
    fig_08_at_ready()
    fig_08_prefetch()
    fig_09_diff()
    fig_09_distro()
    fig_09_oom()
