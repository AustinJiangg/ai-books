"""《E2B 部署从零讲透》第 1～5 篇的配图。用法: python3 tools/figures/dp_p1.py"""
from dp_common import *  # noqa: F401,F403
from dp_common import W, M


# ------------------------------------------------------------------ 第 1 篇
def fig_01_map():
    s = Svg()
    y0 = s.header("部署完成后，这台机器上有四层东西",
                  "从下往上：机器层是配置，没有进程；宿主服务层由 systemd 或 docker 直接管；业务层是 Nomad 管的 4 个 job；"
                  "沙箱层是部署完成后每次 Sandbox.create() 新开的虚拟机。SDK 从左边进来：控制面找 api，数据面经 80 端口到 client-proxy。")
    T = y0 + 30
    LX, LW = M, 220
    BX = M + LW + 130
    BW = W - M - BX
    layers = [
        (SBX, "沙箱层", "部署后按需创建", [("Firecracker 虚拟机 × N", "每个沙箱一个进程"), ("envd :49983", "虚拟机里的代理"),
                                     ("模板", "/tmp/templates")]),
        (JOB, "业务层", "Nomad 管的 4 个 job", [("api", ":3000 REST  :5009 gRPC"), ("client-proxy", ":3002 沙箱流量"),
                                          ("redis", ":6379 沙箱目录"), ("template-manager-system", "= orchestrator :5008 :5007")]),
        (SVC, "宿主服务层", "systemd / docker 直接管", [("Nomad", ":4646"), ("Consul", ":8500 :8600"), ("dnsmasq", ":53"),
                                                 ("Nginx", ":443 → Harbor"), ("Harbor", ":2900"), ("PostgreSQL", ":5432"),
                                                 ("MinIO", ":9000（未用上）")]),
        (MACH, "机器层", "只有配置，没有进程", [("nbd 模块", "512 块虚拟硬盘"), ("大页", "静态池 + 超分配"), ("IP 转发", "ip_forward = 1"),
                                        ("目录", "/orchestrator /fc-*"), ("DNS", "*.e2b.app → 本机"), ("iptables", "80 → 3002")]),
    ]
    LH, G = 138, 18
    y = T
    ys = {}
    for role, t, sub, chips in layers:
        band(s, BX, y, BW, LH, role, t, sub)
        n = len(chips)
        cx0 = BX + 200
        cw = (BX + BW - 20 - cx0 - (n - 1) * 12) / n
        for i, (a, b) in enumerate(chips):
            box(s, cx0 + i * (cw + 12), y + 24, cw, LH - 48, white(role), a, b, 14, 11.5)
        ys[t] = y
        y += LH + G
    # SDK 入口
    sy = ys["业务层"]
    box(s, LX, sy + 4, LW, 60, KEY, "SDK：Sandbox.create()", "控制面", 14, 12)
    box(s, LX, sy + 76, LW, 60, KEY, "SDK：commands.run()", "数据面", 14, 12)
    arrow(s, [(LX + LW + 4, sy + 34), (BX - 4, sy + 34)], INK, 1.6, label="HTTP :3000", ldy=-8, lsize=11.5)
    arrow(s, [(LX + LW + 4, sy + 106), (BX - 4, sy + 106)], INK, 1.6, label="*.e2b.app :80", ldy=-8, lsize=11.5)
    yy = s.footer(y + 6, "注：沙箱层能不能开起来，取决于下面三层是否都准备好了；它是检验部署是否成功的唯一标准。")
    save(s, "01-1-全书地图.svg", yy + 20)


def fig_01_steps():
    s = Svg()
    y0 = s.header("三步各负责什么：前两步只备料，第三步才真正改机器",
                  "第一步拿到原料，第二步把原料加工成 /opt/e2b-infra 里的成品，机器本身都没变；"
                  "build.sh 的 -d、-i、-s 才动机器的各层。")
    T = y0 + 34
    cols = [
        (KEY, "第一步：下载仓库", "git clone + git lfs pull", ["上游源码包（带 vendor）", "ARM 补丁", "Firecracker、客户机内核", "部署脚本 e2b-deploy/"], "机器不变"),
        (KEY, "第二步：打 RPM、安装", "rpmbuild + rpm -ivh", ["编译 api、client-proxy、orchestrator、envd", "摆进 /opt/e2b-infra", "内核、Firecracker、job 模板就位"], "机器不变"),
        (RISK, "build.sh -d", "停止并清理", ["停 orchestrator，拆网络槽位", "删 Nomad、Consul 集群", "清 netns、veth、iptables 残留"], "清四层的旧东西"),
        (SVC, "build.sh -i", "装依赖", ["PostgreSQL、MinIO、Nginx + 证书", "解压 Harbor", "SDK 三层改造", "dep/ 覆盖、dnsmasq"], "宿主服务层的一半"),
        (JOB, "build.sh -s", "启动部署", ["Harbor、Consul、Nomad", "大页、IP 转发、内核、Firecracker", "构建镜像、提交 4 个 job", "seed-db、iptables 80→3002"], "机器层 + 宿主服务层 + 业务层"),
    ]
    n = len(cols)
    gap = 26
    cw = (W - 2 * M - gap * (n - 1)) / n
    for i, (role, t, sub, items, eff) in enumerate(cols):
        x = M + i * (cw + gap)
        box(s, x, T, cw, 74, role, t, sub, 16, 12.5)
        y = T + 90
        for it in items:
            h = need_h(cw - 16, None, it, 13, 12.5, extra=18)
            box(s, x + 8, y, cw - 16, h, WHITE, None, it, 13, 12.5)
            y += h + 8
        if i < n - 1:
            arrow(s, [(x + cw + 3, T + 37), (x + cw + gap - 3, T + 37)], INK, 1.5)
    yb = T + 330
    for i, (role, t, sub, items, eff) in enumerate(cols):
        x = M + i * (cw + gap)
        r = OK if eff == "机器不变" else role
        box(s, x, yb, cw, 56, r, eff, None, 14.5, style="outline")
    s.text(M, yb - 14, "对机器的影响", 13, SUB, 600)
    yy = s.footer(yb + 84, "注：重头戏在 -s，本书第 12～15 篇讲它。-d 放在最前面，让第一次部署和第 N 次部署走同一条路。")
    save(s, "01-2-三步分工.svg", yy + 20)


# ------------------------------------------------------------------ 第 2 篇
def fig_02_parts():
    s = Svg()
    y0 = s.header("E2B 的部件：谁调谁、走哪个端口",
                  "蓝色是 E2B 自己的服务，橙色是它们依赖的外部组件，紫色在沙箱里。"
                  "api 找 orchestrator 不经过 Consul，而是问 Nomad 有哪些就绪节点，再连每个节点的 5008。")
    T = y0 + 40
    sdk = (M, T + 150, 200, 110)
    box(s, *sdk, KEY, "SDK", "e2b 2.20.0（已打补丁）", 16, 12.5)
    api = (M + 300, T + 40, 300, 110)
    cp = (M + 300, T + 260, 300, 110)
    orch = (M + 760, T + 150, 340, 120)
    env = (M + 1220, T + 150, W - 2 * M - 1220, 120)
    box(s, *api, JOB, "api", ":3000 REST  ·  :5009 gRPC\n管团队、密钥、模板、沙箱", 16, 12.5)
    box(s, *cp, JOB, "client-proxy（edge）", ":3002 沙箱流量  ·  :3003 健康\n按域名里的沙箱 ID 转发", 16, 12.5)
    box(s, *orch, JOB, "orchestrator = template-manager", "同一个进程\n:5008 gRPC  ·  :5007 沙箱代理\n建网、挂盘、起 Firecracker、建模板", 15, 12.5)
    band(s, env[0], env[1] - 30, env[2], env[3] + 60, SBX, "沙箱（Firecracker）")
    box(s, env[0] + 16, env[1] + 30, env[2] - 32, env[3] - 30, white(SBX), "envd :49983", "执行命令、读写文件", 15, 12.5)
    arrow(s, [(sdk[0] + sdk[2] + 4, sdk[1] + 30), (api[0] - 4, api[1] + 55)], INK, 1.6, label=":3000", ldy=-6)
    arrow(s, [(sdk[0] + sdk[2] + 4, sdk[1] + 80), (cp[0] - 4, cp[1] + 55)], INK, 1.6, label=":80 → 3002", ldy=14)
    arrow(s, [(api[0] + api[2] + 4, api[1] + 55), (orch[0] - 4, orch[1] + 40)], INK, 1.6, label="gRPC :5008", ldy=-8)
    arrow(s, [(cp[0] + cp[2] + 4, cp[1] + 55), (orch[0] - 4, orch[1] + 90)], INK, 1.6, label=":5007", ldy=16)
    arrow(s, [(orch[0] + orch[2] + 4, orch[1] + 60), (env[0] + 12, orch[1] + 60)], INK, 1.6)
    # 依赖
    D = T + 470
    deps = [("PostgreSQL :5432", "团队、key、模板、配额", "api"), ("Redis :6379", "沙箱 → 在哪个节点", "api 写，client-proxy 读"),
            ("Harbor :2900", "服务镜像、模板基础镜像", "docker、template-manager"), ("本地目录 /tmp/templates", "模板文件（MinIO 未用上）", "orchestrator"),
            ("/fc-kernels  /fc-versions", "客户机内核、Firecracker", "orchestrator"), ("Nomad :4646", "列出就绪节点", "api")]
    dw = (W - 2 * M - 5 * 16) / 6
    for i, (t, sub, who) in enumerate(deps):
        x = M + i * (dw + 16)
        box(s, x, D, dw, 96, SVC, t, sub + "\n谁用：" + who, 14, 12)
    s.text(M, D - 16, "它们依赖的外部组件", 13.5, SUB, 600)
    yy = s.footer(D + 126, "注：上游还有 otel-collector、loki、clickhouse、docker-reverse-proxy、nomad-autoscaler，本环境都没部署，不在开沙箱的主路径上。")
    save(s, "02-1-部件关系.svg", yy + 20)


def fig_02_planes():
    s = Svg()
    y0 = s.header("控制面与数据面：SDK 和 E2B 之间的两条路",
                  "管理沙箱的生命周期走控制面（E2B_API_URL）；使用沙箱走数据面（E2B_DOMAIN）。两条路在 Redis 汇合：api 写入沙箱位置，client-proxy 读出来。")
    T = y0 + 50
    s.text(M, T, "控制面：Sandbox.create()、kill()、Template.build()", 15, JOB[2], 600)
    flow_h(s, M, T + 20, W - 2 * M, [(KEY, "SDK", "E2B_API_URL"), (JOB, "api", ":3000"), (JOB, "orchestrator", ":5008 gRPC"),
                                      (SBX, "Firecracker", "新的沙箱")], h=84, labels=["HTTP", "gRPC", "启动"])
    T2 = T + 210
    s.text(M, T2, "数据面：commands.run()、files.read()", 15, JOB[2], 600)
    flow_h(s, M, T2 + 20, W - 2 * M, [(KEY, "SDK", "49983-<ID>.e2b.app"), (MACH, "dnsmasq + iptables", "→ 127.0.0.1:80 → 3002"),
                                       (JOB, "client-proxy", ":3002"), (JOB, "orchestrator 代理", ":5007"), (SBX, "envd", ":49983")],
           h=84, gap=40)
    rx = M + (W - 2 * M - 40 * 4) / 5 * 2 + 80
    box(s, W / 2 - 150, T + 125, 300, 60, SVC, "Redis：沙箱 ID → 节点", None, 14.5)
    arrow(s, [(M + (W - 2 * M - 44 * 3) / 4 * 1.5 + 44, T + 106), (W / 2 - 60, T + 124)], MUTED, 1.3, dash="4 4", label="写入", ldy=-4, lsize=11.5)
    arrow(s, [(W / 2 + 20, T + 186), (rx + 60, T2 + 18)], MUTED, 1.3, dash="4 4", label="查询", lsize=11.5, ldx=26)
    yy = s.footer(T2 + 140, "注：部署完成后要把这两个入口告诉 SDK：E2B_API_URL=http://<本机 IP>:3000，E2B_DOMAIN=e2b.app（第 17 篇）。")
    save(s, "02-2-控制面与数据面.svg", yy + 20)


# ------------------------------------------------------------------ 第 3 篇
def fig_03_elements():
    s = Svg()
    y0 = s.header("一个服务要长期跑着，要解决五件事",
                  "同样五件事，systemd、docker、Nomad 各有一套答案。本环境三种都在用，各管一批服务。")
    T = y0 + 36
    widths = [200, 450, 450, 404]
    rows = [
        ["可执行文件", "/usr/local/bin/minio", "镜像 postgres:latest", "镜像 .../api 或 /usr/bin/template-manager"],
        ["配置", "EnvironmentFile=/etc/default/minio.yml", "docker run -e POSTGRES_PASSWORD=...", "job 里的 env { } 块"],
        ["端口", "ExecStart 里的 --address :9000", "-p 5432:5432", "network { port ... static }"],
        ["日志", "journalctl -u minio", "docker logs postgres", "nomad alloc logs <id> start"],
        ["守护者", "Restart=always + systemctl enable", "--restart=always（docker 守护）", "restart / reschedule 策略（Nomad 守护）"],
    ]
    y = table(s, M, T, widths, rows, header=["要素", "systemd（例：MinIO）", "docker（例：PostgreSQL）", "Nomad（例：api、orchestrator）"], ts=13.5)
    y += 26
    s.text(M, y, "守护链", 14, SUB, 600)
    y += 18
    items = [(MACH, "systemd", "PID 1"), (SVC, "docker / nomad / consul", "systemd 的服务"), (JOB, "postgres 容器、Harbor", "docker 守护"),
             (JOB, "api、client-proxy、redis、orchestrator", "Nomad 守护")]
    flow_h(s, M, y, W - 2 * M, items, h=70, gap=50)
    yy = s.footer(y + 100, "注：判断一个配置到底生效没有，最终要看进程的环境变量：tr '\\0' '\\n' < /proc/<PID>/environ。")
    save(s, "03-1-服务运行要素.svg", yy + 20)


def fig_03_image():
    s = Svg()
    y0 = s.header("镜像、容器与仓库：安装包、正在运行的软件、应用商店",
                  "api 的镜像是部署时现场构建的：把 RPM 编译好的二进制拷进 debian 精简镜像，推进本机 Harbor；Nomad 再按名字拉下来启动成容器。")
    T = y0 + 40
    flow_h(s, M, T, W - 2 * M, [(MACH, "Dockerfile", "FROM debian:bookworm-slim\nCOPY api /api"), (SVC, "镜像", "只读文件系统 + 启动命令"),
                                 (SVC, "Harbor 仓库", "192.168.10.23:2900"), (JOB, "容器", "Nomad 拉取并启动")],
           h=100, gap=70, labels=["docker build", "docker push", "docker pull"])
    T2 = T + 170
    s.text(M, T2, "镜像的完整名字里包含仓库地址", 14, SUB, 600)
    parts = [("192.168.10.23:2900", "仓库地址", SVC), ("/e2b-orchestration", "项目", KEY), ("/api", "名字", JOB), (":latest", "标签（不写就是 latest）", KEY)]
    x = M
    for t, lab, role in parts:
        w = len(t) * 22 * 0.61 + 28
        s.rect(x, T2 + 20, w, 48, role[0], role[1], 1.2, rx=8)
        s.text(x + w / 2, T2 + 51, t, 22, role[2], 600, "middle", mono=True)
        s.text(x + w / 2, T2 + 92, lab, 13, SUB, 400, "middle")
        x += w + 6
    yy = s.footer(T2 + 130, "注：离线环境拉不到 Docker Hub，所以要自己搭仓库；docker 用明文 HTTP 访问它，靠 daemon.json 的 insecure-registries。")
    save(s, "03-2-镜像容器仓库.svg", yy + 20)


# ------------------------------------------------------------------ 第 4 篇
def fig_04_nomad():
    s = Svg()
    y0 = s.header("Nomad 的层级：job → group → task，放到机器上运行一次叫 allocation",
                  "以 api 为例：一个 group 里两个 task，db-migrator 是前置任务，先跑完；同一个 group 的 task 一定在同一台机器上。")
    T = y0 + 36
    L = W - 2 * M - 460
    band(s, M, T, L, 380, JOB, 'job "api"', "node_pool = \"api\"  ·  type = service  ·  priority = 90")
    band(s, M + 24, T + 72, L - 48, 290, white(JOB), 'group "api-service"', "network：3000、5009  ·  service：api（/health 检查）  ·  restart")
    tw = (L - 48 - 72) / 2
    box(s, M + 48, T + 150, tw, 190, WHITE, 'task "db-migrator"', "driver = docker\nlifecycle { hook = \"prestart\" }\n先跑完、再启动主任务\ngoose 建表", 15, 12.5)
    box(s, M + 72 + tw, T + 150, tw, 190, WHITE, 'task "start"', "driver = docker\nimage = .../api\nresources：20 GiB、20000 MHz\nenv { NOMAD_TOKEN ... }", 15, 12.5)
    arrow(s, [(M + 48 + tw + 2, T + 245), (M + 72 + tw - 2, T + 245)], INK, 1.5)
    RX = M + L + 40
    RW = W - M - RX
    box(s, RX, T, RW, 110, KEY, "allocation 3f1c2a9e", "group 在节点 8a7d6c5b 上的一次运行\nDesired: run   Status: running", 15, 12.5)
    box(s, RX, T + 130, RW, 110, WHITE, "driver 决定怎么跑", "docker：拉镜像起容器\nraw_exec：直接在宿主机上执行命令", 15, 12.5)
    box(s, RX, T + 260, RW, 120, WHITE, "job 类型", "service：跑 count 份\nsystem：每个符合条件的节点一份\n（template-manager-system）", 15, 12.5)
    arrow(s, [(M + L + 4, T + 55), (RX - 4, T + 55)], INK, 1.5, label="调度", ldy=-8)
    yy = s.footer(T + 410, "注：nomad job run 只在 job 定义有差异时才替换 allocation；只换了二进制、hcl 一字未改时，它什么都不做（第 19 篇）。")
    save(s, "04-1-nomad概念层级.svg", yy + 20)


def fig_04_single():
    s = Svg()
    y0 = s.header("单机上的 Nomad、Consul、dnsmasq 与 docker",
                  "systemd 守护四个基础服务；Nomad 一个进程兼任 server 和 client，用 docker 跑 3 个 job、用 raw_exec 跑 orchestrator；"
                  "Consul 记录服务，dnsmasq 让普通程序也能查到 .consul 名字。")
    T = y0 + 34
    band(s, M, T, W - 2 * M, 140, MACH, "systemd")
    sv = [("nomad", "server + client\n:4646 界面"), ("consul", ":8500 HTTP · :8600 DNS"), ("dnsmasq", ":53 所有程序的 DNS 入口"), ("docker", "跑容器")]
    sw = (W - 2 * M - 40 - 3 * 20) / 4
    for i, (t, sub) in enumerate(sv):
        box(s, M + 20 + i * (sw + 20), T + 44, sw, 80, SVC, t, sub, 15, 12)
    T2 = T + 190
    jobs = [("redis", "docker"), ("client-proxy", "docker"), ("api", "docker"), ("template-manager-system", "raw_exec：/usr/bin/template-manager")]
    jw = (W - 2 * M - 3 * 20) / 4
    bus = T2 - 26
    s.line(M + 20 + sw / 2, T + 124, M + 20 + sw / 2, bus, JOB[1], 1.4)
    s.line(M + jw / 2, bus, M + 3 * (jw + 20) + jw / 2, bus, JOB[1], 1.4)
    s.text(M + 20 + sw / 2 + 10, T + 154, "Nomad 管理", 12, JOB[2], 600)
    for i, (t, d) in enumerate(jobs):
        box(s, M + i * (jw + 20), T2, jw, 76, JOB, t, d, 15, 12)
        arrow(s, [(M + i * (jw + 20) + jw / 2, bus), (M + i * (jw + 20) + jw / 2, T2 - 4)], JOB[1], 1.4)
    T3 = T2 + 130
    box(s, M, T3, 700, 140, WHITE, "Consul 服务目录", "redis · template-manager · client-proxy · api · api-grpc\nNomad 启动 alloc 时自动注册，健康检查不过就摘掉", 15, 12.5, align="start")
    box(s, M + 740, T3, W - 2 * M - 740, 140, WHITE, "dnsmasq 的三类名字",
        "*.consul → 转给 127.0.0.1:8600（Consul）\n*.e2b.app → 127.0.0.1\nharbor → /etc/hosts 里的本机 IP\n其他 → 上游 DNS", 15, 12.5, align="start")
    yy = s.footer(T3 + 170, "注：api 找 orchestrator 不走 Consul，而是用 NOMAD_TOKEN 问 Nomad 哪些节点就绪，再连 <节点>:5008。")
    save(s, "04-2-单机调度关系.svg", yy + 20)


# ------------------------------------------------------------------ 第 5 篇
def fig_05_upstream():
    s = Svg()
    y0 = s.header("上游的部署形态：GCP 上的多组机器加一圈云服务",
                  "Terraform 建出几组虚拟机（每组一个 Nomad 节点池），Packer 预做机器镜像；模板、内核、二进制放存储桶，镜像放 Artifact Registry，"
                  "数据库用 Supabase，入口是负载均衡加 Cloudflare 域名。")
    T = y0 + 34
    box(s, M, T, 260, 120, KEY, "Cloudflare 域名\n+ GCP 负载均衡", "*.e2b.app、证书", 15, 12.5)
    GX = M + 300
    GW = W - M - GX
    band(s, GX, T, GW, 380, MACH, "GCP 项目（Terraform 建、Packer 镜像）")
    groups = [("control server", "Nomad / Consul server × 3"), ("api 节点池", "api、client-proxy、redis\ndocker-reverse-proxy"),
              ("build 节点池", "template-manager"), ("client 节点池", "orchestrator × N\n自动扩缩"), ("clickhouse、loki", "用量统计、日志")]
    gw = (GW - 40 - 4 * 16) / 5
    for i, (t, sub) in enumerate(groups):
        box(s, GX + 20 + i * (gw + 16), T + 60, gw, 120, JOB if i else SVC, t, sub, 14.5, 12)
    cloud = [("GCS 存储桶", "fc-templates、fc-kernels\nfc-versions、fc-build-cache…"), ("Artifact Registry", "服务镜像"), ("Secret Manager", "数据库连接串等"),
             ("Filestore", "共享缓存（NFS）")]
    cw = (GW - 40 - 3 * 16) / 4
    for i, (t, sub) in enumerate(cloud):
        box(s, GX + 20 + i * (cw + 16), T + 220, cw, 130, SVC, t, sub, 14.5, 12)
    arrow(s, [(M + 264, T + 60), (GX - 4, T + 60)], INK, 1.5, label="入口", ldy=-8)
    box(s, M, T + 260, 260, 120, SVC, "Supabase", "托管 PostgreSQL", 15, 12.5)
    box(s, M, T + 410, 260, 90, SVC, "Grafana Cloud", "监控", 15, 12.5)
    steps_y = T + 420
    s.text(GX, steps_y + 6, "上线方式", 14, SUB, 600)
    flow_h(s, GX, steps_y + 20, GW, [(KEY, "make build-and-upload", "镜像、二进制、Packer 镜像"), (KEY, "make copy-public-builds", "内核、Firecracker 进桶"),
                                      (KEY, "terraform apply", "templatefile() 渲染 job 并提交"), (KEY, "make prep-cluster", "初始用户、团队、模板")],
           h=76, gap=30, ts=13.5, ss=11.5)
    yy = s.footer(steps_y + 126, "注：job 文件是 Terraform 模板（${port_number}、%{ if ... }）；orchestrator 用 Nomad 的 artifact 从存储桶下载。每一步都离不开 GCP。")
    save(s, "05-1-上游集群形态.svg", yy + 20)


def fig_05_replace():
    s = Svg()
    y0 = s.header("从云上集群搬到一台离线 ARM 服务器：每样云服务换成了什么",
                  "只换掉和云强绑定的部分；Nomad、Consul、端口、协议、节点池概念都保留。右列是本书讲它的篇目。")
    T = y0 + 30
    rows = [
        ["Terraform 建资源", "不需要：资源就是这台机器", "—"],
        ["Terraform 模板变量 ${port_number}", ".env + envsubst 替换 ${API_PORT}", "14、16"],
        ["Packer 机器镜像", "RPM 包 + init-client.sh", "7、13"],
        ["多台机器、多个节点池", "一台机器，所有 job 去 api 池", "4、12"],
        ["3 台 Nomad / Consul server", "一个 Nomad 进程兼任 server + client", "12"],
        ["GCS 存模板", "本地目录 /tmp/templates（MinIO 装了未用）", "10、16"],
        ["GCS 存内核、Firecracker；artifact 下载程序", "RPM 自带，拷到 /fc-*、/usr/bin", "12、13"],
        ["Artifact Registry", "本机 Harbor :2900", "10、14"],
        ["Supabase", "docker 里的 PostgreSQL", "10"],
        ["负载均衡 + Cloudflare 域名", "dnsmasq（*.e2b.app）+ iptables 80→3002", "11、14"],
        ["HTTPS 证书", "不用 HTTPS，SDK 打补丁走 http", "11"],
        ["Secret Manager", "写在 .env 里", "16"],
        ["make prep-cluster", "deploy.sh 末尾的 seed-db", "14"],
        ["Grafana、Loki、ClickHouse、自动扩缩", "不部署", "2"],
    ]
    y = table(s, M, T, [560, 760, 184], rows, header=["上游（GCP）", "本环境（单机离线 ARM）", "篇"], ts=13.5)
    yy = s.footer(y + 14, "注：本仓库还支持多节点 Nomad 和 Kubernetes 两种形态，三者共用同一个 RPM；单机形态就是把多节点的几个脚本串在一台机器上执行。")
    save(s, "05-2-替代品对照.svg", yy + 20)


if __name__ == "__main__":
    for name in sorted(n for n in dir() if n.startswith("fig_")):
        globals()[name]()
