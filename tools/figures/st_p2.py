"""《E2B 沙箱存储从零讲透》第 7～10 篇的配图。

用法: python3 tools/figures/st_p2.py
"""
from st_common import *  # noqa: F401,F403
from st_common import W, M


# ------------------------------------------------------------------ 第 7 篇
def fig_07_header():
    s = Svg()
    y0 = s.header("header 的结构：64 字节元数据，加若干条 40 字节的映射",
                  "两个结构体按小端序原样写成二进制，没有压缩。映射按 Offset 从小到大排列，首尾相接，"
                  "不重不漏地覆盖从 0 到 Size 的整个范围。")
    T = y0 + 40
    # 元数据
    s.text(M, T + 6, "元数据 Metadata（64 字节）", 15, INK, 600)
    fields = [("Version", "8", "版本，当前 3"), ("BlockSize", "8", "4 KiB 或 2 MiB"), ("Size", "8", "完整内存 / 磁盘多大"),
              ("Generation", "8", "代数，构建出来是 0"), ("BuildId", "16", "这一代自己"), ("BaseBuildId", "16", "第 0 代")]
    x = M
    unit = (W - 2 * M) / 64
    for n, b, d in fields:
        w = int(b) * unit
        s.rect(x, T + 20, w - 4, 70, STORE[0], STORE[1], 1.2, rx=6)
        s.text(x + (w - 4) / 2, T + 48, n, 14, STORE[2], 600, "middle", mono=True)
        s.text(x + (w - 4) / 2, T + 72, d, 12, SUB, 400, "middle")
        s.text(x + (w - 4) / 2, T + 108, b + " 字节", 11.5, MUTED, 400, "middle")
        x += w
    # 映射
    T2 = T + 150
    s.text(M, T2 + 6, "映射 BuildMap（每条 40 字节，一条接一条）", 15, INK, 600)
    fields = [("Offset", "8", "在完整内存 / 磁盘里从哪开始"), ("Length", "8", "这一段多长"),
              ("BuildId", "16", "数据实际在哪个 build"), ("BuildStorageOffset", "8", "在那个 build 的数据文件里从哪开始")]
    unit2 = (W - 2 * M) / 40
    for k in range(3):
        x = M
        y = T2 + 20 + k * 62
        for n, b, d in fields:
            w = int(b) * unit2
            role = MINE if (k == 1 and n == "BuildId") else WHITE
            s.rect(x, y, w - 4, 52, role[0], role[1] if role != WHITE else STORE[1], 1.2, rx=6)
            if k == 0:
                s.text(x + (w - 4) / 2, y + 22, n, 13.5, STORE[2], 600, "middle", mono=True)
                s.text(x + (w - 4) / 2, y + 42, d, 12, SUB, 400, "middle")
            else:
                ex = {("Offset", 1): "1000 块", ("Length", 1): "2 块", ("BuildId", 1): "C", ("BuildStorageOffset", 1): "0",
                      ("Offset", 2): "1002 块", ("Length", 2): "3998 块", ("BuildId", 2): "A",
                      ("BuildStorageOffset", 2): "1002 块"}[(n, k)]
                s.text(x + (w - 4) / 2, y + 32, ex, 13.5, INK, 400, "middle", mono=True)
            x += w
    T3 = T2 + 230
    box(s, M, T3, W - 2 * M, 64, WHITE, "BuildId 是 00000000-0000-…（uuid.Nil）的映射：这一段全是零，不在任何文件里，读的时候直接给零",
        None, 14.5)
    yy = s.footer(T3 + 100, "注：所以 header 很小。代码里给一个偏移查映射的函数叫 GetShiftedMapping："
                            "返回去哪个 build、那个文件里的哪个偏移、从这里开始还能连续读多长。")
    save(s, "07-1-header结构.svg", yy + 20)


_KEYS = [0, 1000, 1002, 5000, 5100, 6000]
_FRAC = [0, 0.20, 0.32, 0.70, 0.82, 1.0]


def _sc(v):
    """示意比例：把块号映射到 0～1，让很短的段也看得见。"""
    for i in range(len(_KEYS) - 1):
        if _KEYS[i] <= v <= _KEYS[i + 1]:
            return _FRAC[i] + (_FRAC[i + 1] - _FRAC[i]) * (v - _KEYS[i]) / (_KEYS[i + 1] - _KEYS[i])
    return 1.0


def _strip(s, x, y, w, segs, total, label):
    s.text(x - 14, y + 24, label, 14, INK, 600, "end")
    for a, b, bid in segs:
        role = {"A": STORE, "B": MINE, "C": RISK, "0": WHITE}[bid]
        x1 = x + w * _sc(a)
        x2 = x + w * _sc(b)
        s.rect(x1, y, max(x2 - x1 - 2, 3), 38, role[0], role[1], 1.3, rx=4)
        if x2 - x1 > 40:
            s.text((x1 + x2) / 2, y + 24, bid, 14, role[2], 600, "middle")


def fig_07_merge():
    s = Svg()
    y0 = s.header("新一代 header 怎么来：拿上一代的表，用本次改动覆盖",
                  "暂停得到 C 时：C 写过第 1000～1001 块，先把这张位图变成一条映射，再盖到 B 的 header 上；"
                  "被盖住的那段切开，其余照搬，最后把相邻的段合并。代数加 1，BaseBuildId 不变。")
    T = y0 + 50
    L, R = M + 200, W - M
    w = R - L
    total = 6000
    _strip(s, L, T, w, [(0, 5000, "A"), (5000, 5100, "B"), (5100, 6000, "A")], total, "B 的 header")
    _strip(s, L, T + 90, w, [(1000, 1002, "C")], total, "本次改动")
    s.rect(L, T + 90, w, 38, "none", HAIR, 1, rx=4, dash="4 4")
    _strip(s, L, T + 200, w, [(0, 1000, "A"), (1000, 1002, "C"), (1002, 5000, "A"), (5000, 5100, "B"), (5100, 6000, "A")],
           total, "C 的 header")
    for v in (0, 1000, 1002, 5000, 5100):
        s.text(L + w * _sc(v) + (8 if v in (1002, 5100) else 0), T + 262, str(v), 12, MUTED, 400, "middle", mono=True)
    s.text(R, T + 262, "（示意比例，不按真实长度）", 12, MUTED, 400, "end")
    x1000 = L + w * _sc(1000)
    s.line(x1000, T + 128, x1000, T + 200, RISK[1], 1.3, dash="4 3")
    s.text(x1000 + 10, T + 168, "原来的 A 段在这里被切成三段", 13, RISK[2], 600)
    T2 = T + 300
    steps = [("① 位图变映射", "连续的 1 合并成一段，紧凑地编进 C 的数据文件"),
             ("② 覆盖合并", "新映射盖在旧映射上，被盖住的部分切掉"),
             ("③ 规整", "相邻且能接上的段合并，减少条数")]
    cw = (W - 2 * M - 2 * 24) / 3
    for i, (t, d) in enumerate(steps):
        box(s, M + i * (cw + 24), T2, cw, 80, WHITE, t, d, 15, 13)
    yy = legend(s, T2 + 120, [(STORE, "数据在 A（模板）"), (MINE, "数据在 B"), (RISK, "数据在 C（这次的改动）")])
    yy = s.footer(T2 + 146, "注：内存这边一样。ARM 补丁允许本次改动按 4 KiB 记、而上一代 header 是 2 MiB 一块，合成时块大小变细到 4 KiB；"
                            "映射是按字节记的，旧的 2 MiB 段依然有效。")
    save(s, "07-2-合成新header.svg", yy + 20)


# ------------------------------------------------------------------ 第 8 篇
def fig_08_oci():
    s = Svg()
    y0 = s.header("镜像在仓库里怎么存：标签指向清单，清单列出配置和层，一切按 sha256 命名",
                  "标签只是一个可变的指针，摘要（sha256）才是内容的身份。两个镜像共享同一个 ubuntu 基础层，"
                  "那一层在仓库里只存一份。")
    T = y0 + 40
    # 标签
    tags = [("e2b-orchestration/ubuntu:22.04-custom", T), ("e2b-orchestration/myapp:v1", T + 230)]
    for t, y in tags:
        box(s, M, y + 40, 360, 60, KEY, t, "标签（可变指针）", 13.5, 12)
    # 清单
    MX = 470
    for i, (t, y) in enumerate(tags):
        box(s, MX, y + 20, 300, 100, STORE, "清单 manifest", "sha256:" + ("4e1c…" if i == 0 else "b07a…") + "\nconfig + layers 的摘要", 15, 12.5)
        arrow(s, [(M + 366, y + 70), (MX - 6, y + 70)], INK, 1.6)
    # blobs
    BX = 900
    s.rect(BX, T, W - M - BX, 420, HOST[0], HOST[1], 1.3, rx=14)
    s.text(BX + 20, T + 30, "blobs/sha256/（按内容平铺，相同内容只存一份）", 14.5, HOST[2], 600)
    blobs = [("配置 3f1a…", "平台 linux/arm64、环境变量、启动命令", WHITE, T + 50),
             ("层 9c2b…（ubuntu 基础层）", "tar.gz，29 MB", MINE, T + 122),
             ("层 a17e…", "tar.gz，51 MB", WHITE, T + 194),
             ("配置 77d0…", "myapp 的配置", WHITE, T + 266),
             ("层 0d44…", "COPY app.py，1 KB", WHITE, T + 338)]
    for t, d, r, y in blobs:
        box(s, BX + 30, y, W - M - BX - 60, 60, r, t, d, 14, 12)
    for (yy, tgt) in [(T + 70, [T + 80, T + 152, T + 224]), (T + 300, [T + 152, T + 296, T + 368])]:
        for ty in tgt:
            arrow(s, [(MX + 306, yy), (BX + 24, ty)], SUB, 1.2)
    yy = s.footer(T + 460, "注：多平台镜像的标签指向一个索引，再按平台挑清单。ARM 补丁把 template-manager 拉取的平台固定为 linux/arm64，"
                           "拉到 x86 镜像会直接报平台不匹配。")
    save(s, "08-2-镜像在仓库里.svg", yy + 20)


def fig_08_two():
    s = Svg()
    y0 = s.header("同一个 Harbor，两个门：推送走 <本机IP>:2900，拉取走 harbor:443",
                  "docker daemon 推镜像时如果配了代理，不认识只写在 /etc/hosts 里的 harbor，会被转给代理而 504，所以推送用 IP 和 HTTP。"
                  "template-manager 用 Go 库直接拉，要求 HTTPS 且证书名对得上，所以拉取用 harbor:443。")
    T = y0 + 40
    HX = 1180
    box(s, HX, T, W - M - HX, 350, HOST, "Harbor", "HTTP 2900\n项目 e2b-orchestration（公开）\n数据目录 /data", 17, 13)
    # 推
    box(s, M, T, 380, 90, KEY, "build.sh -s：push_base_image",
        "docker load dep/ubuntu-22.04-custom.tar.gz\ndocker push <IP>:2900/…", 14, 12)
    arrow(s, [(M + 386, T + 45), (HX - 6, T + 45)], INK, 1.7, label="HTTP <本机IP>:2900（daemon.json 的 insecure-registries）", ldy=-10)
    # 拉
    box(s, M, T + 260, 380, 90, ORCH, "template-manager 建模板", "FROM harbor:443/e2b-orchestration/…\nGo 库 remote.Image，不经过 docker", 14, 12)
    NX = 640
    box(s, NX, T + 260, 300, 90, WHITE, "nginx  server_name harbor", "listen 443 ssl → 127.0.0.1:2900\n自签证书，CN=harbor", 14, 12)
    arrow(s, [(M + 386, T + 305), (NX - 6, T + 305)], ORCH[1], 1.7, label="HTTPS", ldy=-10)
    arrow(s, [(NX + 306, T + 305), (HX - 6, T + 305)], SUB, 1.7, label="HTTP 127.0.0.1:2900", ldy=-10)
    # 解析与信任
    T2 = T + 400
    items = [("名字 harbor 怎么解析", "/etc/resolv.conf → 127.0.0.1 dnsmasq → /etc/hosts 里的 <本机IP> harbor\n（-s 写入后要重启 dnsmasq）"),
             ("证书怎么被信任", "系统信任库 /etc/pki/ca-trust/…/harbor-ca.crt\nhcl 里 SSL_CERT_FILE=/etc/docker/certs.d/harbor:443/ca.crt")]
    cw = (W - 2 * M - 24) / 2
    for i, (t, d) in enumerate(items):
        box(s, M + i * (cw + 24), T2, cw, 96, WHITE, t, d, 15, 12.5)
    yy = s.footer(T2 + 130, "注：两个门背后是同一个仓库。docker daemon 的代理、insecure-registries 设置对 template-manager 不起作用。")
    save(s, "08-3-两个地址.svg", yy + 20)


def fig_08_three():
    s = Svg()
    y0 = s.header("存数据的数据：三个组件各记什么",
                  "它们都不存沙箱的磁盘和内存，而是存“原料在哪、模板现在用哪个 build、运行中的沙箱在哪台机器上”。"
                  "orchestrator 不直接读写 PostgreSQL 和 Redis，只认 api 交给它的 buildID。")
    T = y0 + 40
    cw = (W - 2 * M - 2 * 30) / 3
    comps = [("Harbor", "镜像仓库", HOST,
              ["模板原料 ubuntu:22.04-custom", "服务镜像 api、client-proxy、\ndb-migrator、redis",
               "docker compose 容器组，-s 启动", "数据：宿主 /data"]),
             ("PostgreSQL", "模板和 build 的账本", STORE,
              ["团队、配额、密钥", "模板、别名、build（id 即 buildID）、\n标签指派、快照", "docker run 的容器，端口 5432",
               "数据：容器的匿名卷，重跑 -i 会换新卷"]),
             ("Redis", "运行中的沙箱在哪", RISK,
              ["sandbox:storage:…  沙箱状态与过期时间", "sandbox:catalog:<ID>  在哪台 orchestrator",
               "Nomad 的 redis job，端口 6379", "数据：容器内存，没有持久卷"])]
    for i, (n, d, role, items) in enumerate(comps):
        x = M + i * (cw + 30)
        box(s, x, T, cw, 70, role, n, d, 18, 13)
        y = T + 90
        for it in items:
            h = 52 if "\n" in it else 40
            box(s, x + 14, y, cw - 28, h, WHITE, None, it, 13, 12.5)
            y += h + 10
    T2 = T + 400
    s.text(M, T2 - 16, "谁在用它们", 15, INK, 600)
    who = [("template-manager", "建模板时从 Harbor 拉原料", 0), ("Nomad", "起 api、edge、redis 时从 Harbor 拉服务镜像", 0),
           ("api", "读写 PostgreSQL 和 Redis", 1), ("client-proxy", "查 Redis 的 sandbox:catalog 决定转给谁", 2)]
    bw = (W - 2 * M - 3 * 24) / 4
    for i, (n, d, tgt) in enumerate(who):
        x = M + i * (bw + 24)
        box(s, x, T2, bw, 76, ORCH, n, d, 15, 12.5)
    yy = s.footer(T2 + 112, "注：Harbor 自带的数据库和 Redis 只给 Harbor 自己用，和这里的 PostgreSQL、Redis 无关。")
    save(s, "08-1-三个组件.svg", yy + 20)


def fig_08_records():
    s = Svg()
    y0 = s.header("从一个名字找到文件：数据库里的记录怎么指到 /tmp/templates",
                  "别名 → 模板 → 标签指派 → build。env_builds 的主键就是 buildID，也就是 /tmp/templates 下的目录名。"
                  "暂停一个沙箱时，api 在一个事务里往四张表各写一行。")
    T = y0 + 40
    rows = [("env_aliases", "alias = base\nenv_id = 9x2k…", STORE), ("envs", "id = 9x2k…（模板 ID）", STORE),
            ("env_build_assignments", "env_id = 9x2k…  tag = default\nbuild_id = 7c1e9b52-…", STORE),
            ("env_builds", "id = 7c1e9b52-…（= buildID）\nstatus、vcpu、ram_mb、kernel_version…", STORE)]
    bw = (W - 2 * M - 3 * 50 - 300) / 4
    for i, (n, d, role) in enumerate(rows):
        x = M + i * (bw + 50)
        box(s, x, T, bw, 110, role, n, d, 15, 12.5)
        if i < 3:
            arrow(s, [(x + bw + 6, T + 55), (x + bw + 44, T + 55)], INK, 1.6)
    FX = M + 4 * (bw + 50)
    box(s, FX, T, W - M - FX, 110, RISK, "/tmp/templates/7c1e9b52-…/", "六个文件（第 7 篇）", 14, 12.5)
    arrow(s, [(FX - 44, T + 55), (FX - 6, T + 55)], RISK[1], 1.6)
    T2 = T + 170
    s.text(M, T2, "暂停沙箱 i4fok… 时，api 在一个事务里写：", 15, INK, 600)
    writes = [("envs", "给这个快照建一个模板"), ("snapshots", "sandbox_id = i4fok… → 快照模板\nbase_env_id = 最初的模板"),
              ("env_builds", "新 build，得到新 buildID"), ("env_build_assignments", "快照模板的标签指向新 build")]
    cw = (W - 2 * M - 3 * 24) / 4
    for i, (n, d) in enumerate(writes):
        box(s, M + i * (cw + 24), T2 + 20, cw, 86, WHITE, n, d, 14.5, 12.5)
    T3 = T2 + 140
    box(s, M, T3, W - 2 * M, 70, RISK, "删模板、删快照：只删这些行（删 envs 会级联删掉别名、标签指派等），不删 /tmp/templates 里的文件",
        "重跑 build.sh -i 则相反：PostgreSQL 容器被重建，换了新的匿名卷，记录全没了，文件还在", 15, 12.5)
    yy = s.footer(T3 + 106, "注：SDK 返回的 l1xjsvf1d8h3umr8d11y:default 是“模板 ID:标签”，要经过 env_build_assignments 才能查到 buildID。")
    save(s, "08-4-记录指到文件.svg", yy + 20)


# ------------------------------------------------------------------ 第 9 篇
def fig_09_phases():
    s = Svg()
    y0 = s.header("模板构建的五个阶段：每一步都是一次快照，都是一个 build",
                  "base 把镜像变成第一层完整的盘和内存；之后每一步都“从上一层恢复 → 执行 → 暂停 → 上传”，只存这一步的改动。"
                  "最后一层就是模板；optimize 只往它的 metadata.json 里加预取清单。")
    T = y0 + 40
    phases = [("base", "镜像 → ext4 → 两次开机\n根盘完整，内存去全零页", STORE),
              ("user", "建默认用户\n（新版模板）", MINE),
              ("steps", "每条 RUN / COPY 一层\n只含这一步的改动", MINE),
              ("finalize", "configure.sh、启动命令\n等就绪；这就是模板", MINE),
              ("optimize", "恢复几次，录预取清单\n不产生新层", WHITE)]
    bw = (W - 2 * M - 4 * 40) / 5
    for i, (t, d, r) in enumerate(phases):
        x = M + i * (bw + 40)
        box(s, x, T, bw, 110, r, t, d, 17, 12.5)
        if i < 4:
            arrow(s, [(x + bw + 6, T + 55), (x + bw + 34, T + 55)], INK, 1.6)
    # 层堆叠
    T2 = T + 170
    s.text(M, T2, "构建完，/tmp/templates 下有好几个 build 目录", 15, INK, 600)
    layers = [("base 层 buildID", "六个文件；rootfs 完整", STORE), ("user 层", "六个文件；只含改动", MINE),
              ("step1 层", "六个文件；只含改动", MINE), ("step2 层", "六个文件；只含改动", MINE),
              ("finalize 层 = 模板", "header 引用上面所有层；metadata.json 含预取清单", RISK)]
    for i, (t, d, r) in enumerate(layers):
        y = T2 + 20 + (4 - i) * 56
        box(s, M + 40, y, 760, 46, r, None, None)
        s.text(M + 60, y + 29, t, 14, r[2], 600)
        s.text(M + 300, y + 29, d, 13, SUB)
    s.text(M + 830, T2 + 20 + 24, "↑ 最新", 13, MUTED)
    IX = M + 920
    box(s, IX, T2 + 20, W - M - IX, 130, KEY, "/tmp/build-cache/<范围>/index/<哈希>", "每层一条：哈希 → 这一层的 buildID\n下次构建前几步没变，直接命中", 14, 12.5)
    box(s, IX, T2 + 170, W - M - IX, 106, RISK, "构建失败", "删掉这次 buildID 前缀下的文件\n已成功的前几层保留，下次还能命中", 14, 12.5)
    yy = s.footer(T2 + 320, "注：一个有 2 步命令的模板，构建完至少 5 个 build 目录。上传异步进行，但写 index 要等前面所有层都上传完，防止别的构建命中一个数据还没到的层。")
    save(s, "09-1-五个阶段.svg", yy + 20)


def fig_09_ext4():
    s = Svg()
    y0 = s.header("base 阶段：镜像怎么变成一块能开机的 ext4 根盘",
                  "先按上限做一个空 ext4，用 loop 挂上把镜像层解进去，再缩到刚好；第一次用 busybox 开机只为装 systemd，"
                  "然后扩到要求的大小；第二次用 systemd 正式开机，打第一份快照。")
    T = y0 + 40
    steps = [("追加系统层", "envd、busybox、provision.sh、\nhostname、resolv.conf", HOST),
             ("mkfs.ext4", "-b 4096，按上限大小\n/orchestrator/build-templates/<id>/", HOST),
             ("loop 挂载、解包", "这时才从 Harbor\n一层层拉 tar.gz", HOST),
             ("e2fsck → 缩小 → e2fsck", "resize2fs -M\n刚好装下镜像内容", HOST),
             ("第一次开机（busybox）", "只跑 provision.sh\n装 systemd 等，不打快照", GUEST),
             ("e2fsck → 扩容", "resize2fs 到 disk_size_mb\n扩出的部分是稀疏的", HOST),
             ("第二次开机（systemd）", "Direct 方式根盘\n等 envd，sync", GUEST),
             ("暂停、打快照", "第 1 层：根盘完整\n内存去掉全零页", STORE)]
    bw, bh = (W - 2 * M - 3 * 40) / 4, 104
    for i, (t, d, r) in enumerate(steps):
        row, col = divmod(i, 4)
        if row == 1:
            col = 3 - col
        x = M + col * (bw + 40)
        y = T + row * (bh + 70)
        box(s, x, y, bw, bh, r, t, d, 15, 12.5)
        num(s, x + 18, y + 18, i + 1)
        if i in (0, 1, 2):
            arrow(s, [(x + bw + 6, y + bh / 2), (x + bw + 34, y + bh / 2)], INK, 1.6)
        if i in (4, 5, 6):
            arrow(s, [(x - 6, y + bh / 2), (x - 34, y + bh / 2)], INK, 1.6)
    xr = M + 3 * (bw + 40) + bw / 2
    arrow(s, [(xr, T + bh + 6), (xr, T + bh + 64)], INK, 1.6)
    T2 = T + 2 * bh + 110
    box(s, M, T2, W - 2 * M, 70, white(GUEST), "ARM 补丁在这里改了什么",
        "glibc 版 arm64 busybox（RPM 构建时拷进源码、编进二进制）；provision.sh 识别 openEuler 用 dnf；configure.sh 改成 POSIX sh", 15, 13)
    yy = s.footer(T2 + 106, "注：两次开机都是 Direct 方式（第 12 篇），根盘直接是这个文件，没有 NBD；第一次开机的内存是 NoopMemory，"
                            "打快照时按“常驻且不全零”导出（第 13、14 篇）。")
    save(s, "09-2-镜像变ext4.svg", yy + 20)


def fig_09_hash():
    s = Svg()
    y0 = s.header("层缓存：哈希里包着上一层的哈希，前面一变，后面全变",
                  "每层的哈希 = hash(上一层的哈希, 这一步的内容, 相关参数)。构建前先查 index，命中就直接拿那个 buildID，"
                  "跳过“恢复—执行—快照—上传”。")
    T = y0 + 40
    names = ["base：FROM ubuntu", "step1：RUN apt-get …", "step2：RUN pip install numpy", "step3：COPY app.py"]
    cw = (W - 2 * M - 3 * 40) / 4
    for row, (title, hit) in enumerate([("第一次构建", [False] * 4), ("只改了 step3，再构建", [True, True, True, False])]):
        y = T + row * 200
        s.text(M, y + 4, title, 15, INK, 600)
        for i, n in enumerate(names):
            x = M + i * (cw + 40)
            role = GOOD if hit[i] else (RISK if row == 1 else WHITE)
            box(s, x, y + 20, cw, 60, role, n, None, 14)
            hs = f"h{i + 1}" + ("′" if (row == 1 and i == 3) else "")
            box(s, x + 20, y + 98, cw - 40, 54, WHITE, f"哈希 {hs}", "命中 index，跳过" if hit[i] else ("没命中，真的去做" if row == 1 else "做完写 index"), 13, 11.5)
            arrow(s, [(x + cw / 2, y + 86), (x + cw / 2, y + 94)], SUB, 1.2)
            if i < 3:
                arrow(s, [(x + cw - 14, y + 125), (x + cw + 54, y + 125)], SUB, 1.3)
    yy = s.footer(T + 420, "注：COPY 的文件按内容算哈希，存在构建缓存的 files/<哈希>.tar。这套环境两个后端都是 Local，"
                           "而 Local 不支持生成上传链接，所以带本地文件 COPY 的模板在上传这一步会出问题。")
    save(s, "09-3-层缓存.svg", yy + 20)


# ------------------------------------------------------------------ 第 10 篇
def fig_10_chain():
    s = Svg()
    y0 = s.header("为什么 .env 写了 MinioBucket，实际却是 Local：四步链路",
                  "唯一会读 STORAGE_PROVIDER 的进程是 template-manager，它的 job 定义被部署包里写死 \"Local\" 的那份覆盖了；"
                  "写着 ${STORAGE_PROVIDER} 的 orchestrator job 从来没被提交。")
    T = y0 + 40
    steps = [("① RPM 安装", "nomad/template-manager.hcl\nSTORAGE_PROVIDER = \"${STORAGE_PROVIDER}\"", HOST),
             ("② build.sh -i 覆盖", "cp dep/template-manager.hcl → nomad/\nSTORAGE_PROVIDER = \"Local\"（写死）", RISK),
             ("③ deploy.sh 渲染", "source .env（MinioBucket）\nenvsubst 只换 ${…}，\"Local\" 原样保留", HOST),
             ("④ 只提交四个 job", "redis  template-manager  edge  api\norchestrator.hcl 渲染了但不提交", HOST)]
    bw = (W - 2 * M - 3 * 40) / 4
    for i, (t, d, r) in enumerate(steps):
        x = M + i * (bw + 40)
        box(s, x, T, bw, 120, r, t, d, 16, 12.5)
        if i < 3:
            arrow(s, [(x + bw + 6, T + 60), (x + bw + 34, T + 60)], INK, 1.6)
    T2 = T + 180
    box(s, M, T2, 700, 120, ORCH, "/usr/bin/template-manager 的环境变量",
        "STORAGE_PROVIDER=Local\n没有 LOCAL_TEMPLATE_STORAGE_BASE_PATH → 用默认值", 16, 13)
    arrow(s, [(M + 700 + 6, T2 + 60), (M + 780 - 6, T2 + 60)], INK, 1.6)
    box(s, M + 780, T2, W - 2 * M - 780, 120, RISK, "/tmp/templates  /tmp/build-cache",
        "/tmp 是 tmpfs：占内存、宿主重启全丢、10 天没访问会被 systemd-tmpfiles 清掉", 16, 13)
    T3 = T2 + 160
    box(s, M, T3, W - 2 * M, 70, WHITE, "MinIO：build.sh -i 装好、健康检查通过，但没建桶，也没有任何组件往里写",
        "/root/data/minio 下只有 .minio.sys；helm（k8s）那条部署路上 MinIO 才会真正生效", 15, 12.5)
    yy = s.footer(T3 + 106, "注：确认方法是看进程实际的环境变量：tr '\\0' '\\n' < /proc/<template-manager 的 PID>/environ | grep STORAGE。"
                            "/orchestrator/build 里有 memfile 不能说明什么，那是任何后端下都有的本地缓存。")
    save(s, "10-1-四步链路.svg", yy + 20)


def fig_10_where():
    s = Svg()
    y0 = s.header("同一个键，在两种后端下落在哪：Local 和 MinIO",
                  "六个文件在存储里的“名字”在所有后端下都一样，都以 buildID 为前缀。Local 直接按路径建目录写文件；"
                  "MinIO 把它当作桶里的对象，自己再在磁盘上摊开存。")
    T = y0 + 40
    box(s, M, T, 420, 260, STORE, "键名（所有后端相同）",
        "<buildID>/snapfile\n<buildID>/memfile\n<buildID>/memfile.header\n<buildID>/rootfs.ext4\n<buildID>/rootfs.ext4.header\n<buildID>/metadata.json",
        16, 13.5, mono_sub=True)
    RX = M + 520
    box(s, RX, T, W - M - RX, 120, RISK, "Local（本环境实际生效）",
        "/tmp/templates/<buildID>/memfile\n上传 = 拷贝文件；不支持生成上传链接", 16, 13)
    box(s, RX, T + 140, W - M - RX, 120, WHITE, "MinioBucket（.env 的本意）",
        "桶 e2b-dev-fc-templates 里的对象 <buildID>/memfile\n磁盘上：/root/data/minio/e2b-dev-fc-templates/<buildID>/memfile/…\n"
        "useSSL 写死 false；不会自动建桶；支持预签名上传链接", 16, 12.5)
    arrow(s, [(M + 426, T + 100), (RX - 6, T + 60)], INK, 1.6)
    arrow(s, [(M + 426, T + 160), (RX - 6, T + 200)], SUB, 1.6, dash="5 4")
    T2 = T + 300
    cw = (W - 2 * M - 24) / 2
    box(s, M, T2, cw, 100, GOOD, "想不丢：方案一（改动最小）", "dep/template-manager.hcl 的 env 里加\nLOCAL_TEMPLATE_STORAGE_BASE_PATH 指到硬盘，搬数据", 15, 12.5)
    box(s, M + cw + 24, T2, cw, 100, GOOD, "想不丢：方案二", "建两个桶，把写死的 \"Local\" 改回 ${STORAGE_PROVIDER}\n按 <buildID>/<文件名> 原样把数据拷进桶", 15, 12.5)
    yy = s.footer(T2 + 136, "注：两条路都要改源头 e2b-deploy/dep/template-manager.hcl，否则下次 build.sh -i 又覆盖回去。")
    save(s, "10-2-键名与落点.svg", yy + 20)


if __name__ == "__main__":
    for name in sorted(n for n in dir() if n.startswith("fig_")):
        globals()[name]()
