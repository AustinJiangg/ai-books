"""《E2B 部署从零讲透》第 17～20 篇的配图。用法: python3 tools/figures/dp_p4.py"""
from dp_common import *  # noqa: F401,F403
from dp_common import W, M


# ------------------------------------------------------------------ 第 17 篇
def fig_17_layers():
    s = Svg()
    y0 = s.header("自下而上验证：下层不通，别查上层",
                  "部署是从下往上搭的，验证也从下往上查。每层一两条命令，和“正常时”对不上，就在那一层找原因。")
    T = y0 + 30
    rows = [
        ["5 沙箱层", "建 base 模板；Sandbox.create(\"base\") + commands.run(\"uname -m\")", "秒级返回 aarch64"],
        ["4 业务层", "curl :3000/health；curl :3003/health", "都是 200（api 已发现 orchestrator）"],
        ["3 调度层", "nomad node status；nomad job status；consul catalog services", "1 个节点 ready；4 个 job running；服务齐全"],
        ["2 宿主服务层", "systemctl is-active nomad consul dnsmasq nginx minio docker；curl https://harbor/v2/ --cacert …", "全部 active；harbor 返回 401"],
        ["1 机器层", "nbds_max；HugePages_Total；ip_forward；getent hosts x.e2b.app harbor；iptables -t nat -S | grep 3002", "512；与 init-client 一致；1；127.0.0.1 / 本机 IP；两条"],
    ]
    y = table(s, M, T, [190, 830, 484], rows, header=["层", "命令", "正常时"], ts=13.5, roles=[SBX, JOB, JOB, SVC, MACH])
    yy = s.footer(y + 14, "注：harbor 返回 401 是好事：请求到达了 Harbor，只是没带账号，说明 DNS、Nginx、证书、Harbor 整条路都是通的。")
    save(s, "17-1-五层验证.svg", yy + 20)


def fig_17_template():
    s = Svg()
    y0 = s.header("建第一个模板，用到了前面几乎每一篇的成果",
                  "Template.build(from_dockerfile('FROM harbor:443/e2b-orchestration/ubuntu:22.04-custom'), alias=\"base\")。右侧是这一步依赖的部署成果。")
    T = y0 + 30
    items = [("SDK 发请求到 :3000", "带 access token 和 API key", "SDK 三层改造（第 11 篇）"),
             ("api 记录构建", "验证 token；写 PostgreSQL", "PostgreSQL、db-migrator、seed-db（第 10、14、15 篇）"),
             ("交给 template-manager", "同一个进程，5008", "api 已发现 orchestrator（第 15 篇）"),
             ("拉 harbor:443/…/ubuntu:22.04-custom", "", "hosts、dnsmasq、Nginx、证书、SSL_CERT_FILE、基础镜像（第 10、14 篇）"),
             ("做成磁盘，注入 envd 和 busybox", "", "/fc-envd/envd；编进二进制的 busybox（第 7、13 篇）"),
             ("启动构建用的虚拟机", "", "/fc-kernels、/fc-versions、NBD、大页、网络槽位（第 8、13 篇）"),
             ("等虚拟机里的 envd 就绪", "最多 60 秒", "IP 转发 = 1（第 13 篇）"),
             ("打内存快照，存成模板", "", "/orchestrator/build、/tmp/templates（第 12 篇）")]
    y = steps(s, M, T, W - 2 * M, items, role=WHITE, ts=14.5, ss=12, gap=8, note_w=640, note_role=OK)
    yy = s.footer(y + 6, "注：上一次构建失败后重试报 Alias 'base' already used，要先用 API 删掉失败的模板（第 20 篇）。")
    save(s, "17-2-建模板路径.svg", yy + 20)


def fig_17_request():
    s = Svg()
    y0 = s.header("第一台沙箱：一次 create 和一次 run 在全景图上怎么走",
                  "上一行是控制面，下一行是数据面。每个框下面是这一步用到的部署成果。")
    T = y0 + 40
    ctl = [(KEY, "① 创建", "SDK → api :3000"), (JOB, "② 派活", "api → orchestrator :5008"), (SBX, "③ 开机", "模板、NBD、大页、建网、Firecracker"),
           (SVC, "④ 登记", "api 写 Redis")]
    data = [(MACH, "⑤ 解析", "49983-<ID>.e2b.app → 127.0.0.1"), (MACH, "⑥ 入口", "127.0.0.1:80 → 3002"),
            (JOB, "⑦ 找沙箱", "client-proxy 查 Redis → :5007"), (SBX, "⑧ 进沙箱", "经网络槽位到 envd :49983")]
    uses1 = ["api job、PostgreSQL、配额已放开", "NOMAD_TOKEN、节点发现", "第 13 篇的全部", "redis job、redis.service.consul"]
    uses2 = ["dnsmasq：address= 与 local=", "iptables OUTPUT 规则", "client-proxy job", "IP 转发、地址池 10.13/10.14"]
    for row, (items, uses) in enumerate([(ctl, uses1), (data, uses2)]):
        y = T + row * 230
        s.text(M, y - 10, "控制面：Sandbox.create(\"base\")" if row == 0 else "数据面：commands.run(\"uname -m\")", 14.5, INK, 600)
        bx = flow_h(s, M, y + 6, W - 2 * M, items, h=90, gap=40)
        for (x, yy, w, h), u in zip(bx, uses):
            box(s, x, yy + h + 12, w, 56, OK, None, u, 13, 12.5, style="outline")
    yy = s.footer(T + 420, "注：create 很快、第一条 run 却慢 15 秒，是 dnsmasq 缺 local=/e2b.app/；每一步怎么走，详见《E2B 沙箱网络从零讲透》第 18 篇。")
    save(s, "17-3-请求路径.svg", yy + 20)


# ------------------------------------------------------------------ 第 18 篇
def fig_18_stop():
    s = Svg()
    y0 = s.header("build.sh -d 的停止顺序：每一步为什么排在这里",
                  "先给 orchestrator 机会自己清理，再按正确的顺序停其他东西，最后把它没清完的残留扫干净。")
    T = y0 + 30
    items = [("nomad job stop template-manager-system", "SIGTERM，最多等 40 秒，让它跑 networkPool.Close() 拆暖池", "必须在停 Nomad 之前，否则只能强杀"),
             ("uninstall-consul.sh、uninstall-nomad.sh", "停服务，删配置、数据、令牌文件", "之后的 -s 是全新集群"),
             ("按命令行杀业务进程", "pgrep -f \"^/usr/bin/template-manager\" 等，先 TERM 后 KILL", "必须写完整路径才匹配得到"),
             ("杀残留的 firecracker", "pgrep -f '/fc-versions/.*/firecracker'", "它们占着大页、NBD、槽位"),
             ("pkill nomad、consul（兜底）", "确保 agent 本身退出", "放最后：先杀会让 orchestrator 变孤儿"),
             ("purge_sandbox_netns / iptables", "只认 ns-<n>、e2bv-<n> 和 10.13.0.0/16；跳过在用槽位；iptables-restore --noflush", "不误伤 AgentENV、docker、k3s"),
             ("check_ports_free", "3000～3003、5007～5010、5016～5018、6379", "没放开，下次部署以 api 503 的样子失败"),
             ("提示大页仍占用", "不释放静态池", "下次 -s 时内存可能已零碎")]
    y = steps(s, M, T, W - 2 * M, items, role=WHITE, ts=14, ss=12, gap=8, note_w=470, note_role=KEY)
    yy = s.footer(y + 6, "注：-d 会结束所有运行中的沙箱；过程中出现 Error querying jobs: 403 是正常的（Nomad 正在被卸载）。")
    save(s, "18-1-停止顺序.svg", yy + 20)


def fig_18_leak():
    s = Svg()
    y0 = s.header("槽位泄漏：怎么攒起来的、有什么害处、怎么回收",
                  "一个槽位在宿主机上是 1 个网络命名空间、1 块 e2bv-<n> 网卡、9 条 iptables 规则。orchestrator 启动时把已存在的 ns-<n> 记成“别人的”永久跳过，编号只增不减。")
    T = y0 + 34
    cyc = [(JOB, "orchestrator 启动", "建暖池：最多 300 新建 + 1000 回收"), (RISK, "停服 30 秒拆不完", "或被 kill -9、OOM"),
           (RISK, "残留留在宿主机", "netns、网卡、规则"), (JOB, "下次启动", "把残留记成别人的，编号继续往上")]
    flow_h(s, M, T, W - 2 * M, cyc, h=90, gap=50)
    arrow(s, [(W - M - 120, T + 94), (W - M - 120, T + 130), (M + 120, T + 130), (M + 120, T + 94)], RISK[1], 1.4, dash="5 4")
    s.text(W / 2, T + 150, "每重启一次攒一批", 12.5, RISK[2], 600, "middle")
    T2 = T + 190
    cw = (W - 2 * M - 30) / 2
    box(s, M, T2, cw, 150, RISK, "害处", "Nomad client 逐块网卡做指纹：几千块时要几分钟，4646 迟迟不开\n"
                                          "iptables 几万条：每次操作都慢，同机 k3s 抢锁时一两分钟\n地址池 /16 理论上限三万多", 15, 12.5, style="outline")
    box(s, M + cw + 30, T2, cw, 150, OK, "回收：build.sh --recycle-netns", "停 template-manager（停不下来就中止，不硬清）\n"
                                                                    "→ purge_sandbox_netns + purge_sandbox_iptables\n→ build.sh -r template-manager 重新拉起", 15, 12.5, style="outline")
    T3 = T2 + 180
    box(s, M, T3, W - 2 * M, 70, KEY, "为什么只能“停 → 清 → 起”",
        "暖池里空闲的槽位和泄漏的残留在宿主机上长得一模一样，只有进程自己的内存知道哪些是它的；“别人的编号”清单也只在启动时生成。", 14.5, 12.5, style="outline")
    yy = s.footer(T3 + 98, "注：只动 template-manager 一个 job，不碰 Nomad、Consul、Redis、api、client-proxy，比 -d + -s 快得多。")
    save(s, "18-2-槽位泄漏.svg", yy + 20)


# ------------------------------------------------------------------ 第 19 篇
def fig_19_scenarios():
    s = Svg()
    y0 = s.header("改动落在哪一层，就只动哪一层",
                  "列是部署的三层，格子是每种场景要动它的方式。能不 -i -s 就不 -i -s：它们会换掉 API key 和令牌、结束所有沙箱。")
    T = y0 + 30
    rows = [["一 彻底重来", "rpm -Uvh（可选）", "-i 重做", "-d 删、-s 重建", "会"],
            ["二 改 Go 源码", "rpm -Uvh --force", "重放（跳过 .env）", "拷 /usr/bin；api/client-proxy 重建镜像；stop 再 run", "会"],
            ["三 hcl 里写死的 env", "—", "改 nomad/<job>.hcl", "build.sh -r <job>（值变了自动替换）", "改 template-manager 时会"],
            ["四 .env 里进 job 的变量", "—", "改根目录 .env", "build.sh -f 或 -r", "视 job 而定"],
            ["五 Nomad、Consul 配置", "—", "—", "改 /etc/nomad.d，systemctl restart nomad", "不会"]]
    y = table(s, M, T, [300, 250, 300, 444, 210], rows, header=["场景", "① RPM 底座", "② dep/ 覆盖", "③ 运行时生成物", "结束沙箱"], ts=13.5,
              roles=[RISK, None, None, None, OK])
    T2 = y + 20
    box(s, M, T2, W - 2 * M, 76, KEY, "rpm -Uvh 之后必做：重放覆盖",
        "for f in deploy.sh start-*.sh init-client.sh run-*.sh install-*.sh uninstall-*.sh template-manager.hcl → 从 dep/ 拷回；唯独不拷 dep/.env", 14.5, 12.5, style="outline")
    yy = s.footer(T2 + 104, "注：持久的改法永远是改仓库里的 e2b-deploy/dep/... 再打包；机器上的改动都会被某一步覆盖。")
    save(s, "19-1-三层与场景.svg", yy + 20)


def fig_19_verify():
    s = Svg()
    y0 = s.header("改完之后，逐层核对是否真的生效",
                  "别凭“命令执行成功了”就认为生效。环境变量类从模板查到进程；二进制类用一个独特的特征串，分别查磁盘上的文件和运行中的进程。")
    T = y0 + 34
    cw = (W - 2 * M - 40) / 2
    s.text(M, T, "环境变量类", 15, INK, 600)
    items = [("① 模板", "grep $V nomad/template-manager.hcl"), ("② 渲染结果", "grep $V rendered/template-manager.hcl"),
             ("③ Nomad 收到的", "nomad job inspect template-manager-system | grep $V"), ("④ 进程（最终裁决）", "tr '\\0' '\\n' < /proc/$pid/environ | grep $V"),
             ("启动时间", "ps -o lstart -p $pid 晚于这次改动")]
    y = T + 16
    for t, cmd in items:
        box(s, M, y, cw, 62, WHITE, t, cmd, 14, 12, align="start")
        y += 72
    RX = M + cw + 40
    s.text(RX, T, "二进制类", 15, INK, 600)
    box(s, RX, T + 16, cw, 98, WHITE, "磁盘上的文件是新的吗", "strings /usr/bin/template-manager | grep -c 特征串  → ≥ 1", 14, 12, align="start")
    box(s, RX, T + 130, cw, 98, WHITE, "运行中的进程是新的吗", "strings /proc/$pid/exe | grep -c 特征串  → ≥ 1", 14, 12, align="start")
    box(s, RX, T + 244, cw, 116, RISK, "第一条 ≥1、第二条 = 0", "文件换了，进程没重启：只 nomad job run 而 hcl 没变，Nomad 认为无变更。\n先 nomad job stop 再 run", 14, 12, style="outline", align="start")
    yy = s.footer(max(y, T + 380) + 4, "注：哪一层和预期不一样，问题就在它和上一层之间。别靠 rpm -q 的版本号判断：日常迭代时 Release 一般不改。")
    save(s, "19-2-逐层核对.svg", yy + 20)


def fig_19_dev():
    s = Svg()
    y0 = s.header("两条开发线：日常不打包，阶段收尾才出补丁和 RPM",
                  "补丁文件不能手改，所以要有一棵“已经打好补丁的源码树”：在里面正常写代码，最后用 git diff 生成新补丁。RPM 的价值在于可重复地装到另一台机器上。")
    T = y0 + 34
    cw = (W - 2 * M - 40) / 2
    box(s, M, T, cw, 110, KEY, "交付仓库（本书讲的这个）", "补丁、spec、原料、e2b-deploy/；没有展开的源码\n推到远端", 16, 12.5)
    box(s, M + cw + 40, T, cw, 110, JOB, "源码工作树（纯本地）", "源码包解开 + git 基线 + 打上补丁\n不推到任何地方；唯一产物是新补丁", 16, 12.5)
    T2 = T + 150
    s.text(M, T2, "日常循环（一轮几分钟）", 15, INK, 600)
    flow_h(s, M, T2 + 16, W - 2 * M, [(JOB, "改代码", "在源码工作树"), (JOB, "make build", "只编改动的模块"),
                                       (SVC, "拷到运行位置", "orchestrator → /usr/bin（先删后拷）\nenvd → /fc-envd"),
                                       (SVC, "让它重新跑", "-r 或 stop + run\napi 重建镜像；envd 重建模板"), (OK, "验证", "特征串")],
           h=104, gap=34, ts=14.5, ss=12)
    arrow(s, [(W - M - 100, T2 + 124), (W - M - 100, T2 + 150), (M + 100, T2 + 150), (M + 100, T2 + 124)], JOB[1], 1.3, dash="5 4")
    T3 = T2 + 200
    s.text(M, T3, "阶段收尾（一个功能做完才做一次）", 15, INK, 600)
    flow_h(s, M, T3 + 16, W - 2 * M, [(KEY, "git commit", "源码工作树"), (KEY, "git diff 基线 HEAD", "→ 0001-…patch"),
                                       (KEY, "patch --dry-run", "在干净源码上验证"), (KEY, "rpmbuild + rpm -Uvh", "再重放覆盖"),
                                       (OK, "提交交付仓库", None)], h=90, gap=34, ts=14.5, ss=12)
    yy = s.footer(T3 + 140, "注：详细流程见仓库的 deploy-docs/08-源码开发与出包流程.md。")
    save(s, "19-3-两条开发线.svg", yy + 20)


# ------------------------------------------------------------------ 第 20 篇
def fig_20_panorama():
    s = Svg()
    y0 = s.header("全景：每个组件谁装的、配置在哪、日志在哪",
                  "回到第 1 篇的四层图，这次每张卡片都能说出来历。卡片里三行依次是：谁装的 / 配置 / 日志。")
    T = y0 + 30
    layers = [
        (JOB, "业务层（Nomad）", [("api", "deploy.sh", "rendered/api.hcl", "nomad alloc logs"), ("client-proxy", "deploy.sh", "rendered/edge.hcl", "nomad alloc logs"),
                               ("redis", "deploy.sh", "rendered/redis.hcl", "nomad alloc logs"),
                               ("template-manager", "deploy.sh", "rendered/template-manager.hcl", "/data/nomad/alloc/<id>/alloc/logs")]),
        (SVC, "宿主服务层", [("Nomad", "-s", "/etc/nomad.d/default.hcl", "journalctl -u nomad"), ("Consul", "-s", "/etc/consul.d/default.json", "journalctl -u consul"),
                          ("dnsmasq", "-i、-s", "/etc/dnsmasq.conf、dnsmasq.d/", "journalctl -u dnsmasq"), ("Nginx", "-i", "/etc/nginx/", "/var/log/nginx/"),
                          ("Harbor", "-i、-s", "harbor/harbor.yml", "docker logs"), ("PostgreSQL", "-i", "build.sh 的 docker run", "docker logs postgres")]),
        (MACH, "机器层", [("nbd", "第 0 步", "/etc/modprobe.d/nbd.conf", "lsmod"), ("sysctl", "init-client", "/etc/sysctl.conf", "sysctl -a"),
                       ("大页", "init-client", "/proc/sys/vm/*（不持久）", "/proc/meminfo"), ("运行时文件", "init-client", "/fc-kernels、/fc-versions", "—"),
                       ("iptables 入口", "-s 末尾", "nat 表（不持久）", "iptables -t nat -S")]),
    ]
    y = T
    for role, t, cards in layers:
        n = len(cards)
        cw = (W - 2 * M - 40 - (n - 1) * 12) / n
        band(s, M, y, W - 2 * M, 176, role, t)
        for i, (name, who, cfg, log) in enumerate(cards):
            x = M + 20 + i * (cw + 12)
            s.rect(x, y + 44, cw, 116, "#FFFFFF", role[1], 1.2, rx=9)
            s.text(x + 12, y + 70, name, 14.5, role[2], 600)
            for k, (lab, val) in enumerate([("装", who), ("配", cfg), ("志", log)]):
                txt = wrap(val, cw - 52, 12)[0] if wrap(val, cw - 52, 12) else val
                s.text(x + 12, y + 96 + k * 21, lab, 12, MUTED, 600)
                s.text(x + 34, y + 96 + k * 21, txt, 12, INK)
        y += 192
    yy = s.footer(y + 4, "注：“装”是谁装的，“配”是配置在哪，“志”是日志在哪。业务层改配置用 build.sh -r <文件名>；只想重启用 nomad job stop + run。")
    save(s, "20-1-全景标注.svg", yy + 20)


def fig_20_triage():
    s = Svg()
    y0 = s.header("按层排障：从下往上，报错在哪层，原因多在下一层",
                  "每一层先跑一条命令；通过就往上走，不通过就在这一层找。最典型的例子：api 一直 503，原因几乎总在 template-manager。")
    T = y0 + 30
    rows = [("机器", "nbds_max；ip_forward；HugePages_*", "512；1；有大页", MACH),
            ("宿主服务", "systemctl --failed；docker ps -a", "没有失败的服务、退出的容器", SVC),
            ("调度", "nomad job status；nomad node status", "4 个 running；1 个 ready", JOB),
            ("业务", "curl :3000/health；curl :3003/health", "200", JOB),
            ("沙箱", "建模板、开沙箱", "看报错，回第 20 篇速查表", SBX)]
    LW = 1000
    y = T + 5 * 96 - 96
    pos = []
    for i, (lay, cmd, ok, role) in enumerate(rows):
        yy = T + (4 - i) * 96
        box(s, M, yy, 170, 76, role, lay, None, 16)
        box(s, M + 190, yy, LW - 190, 76, WHITE, cmd, "正常：" + ok, 14, 12.5, align="start")
        pos.append(yy)
        if i < 4:
            arrow(s, [(M + 85, yy - 2), (M + 85, yy - 18)], OK[1], 1.6)
    RX = M + LW + 40
    RW = W - M - RX
    box(s, RX, T, RW, 200, RISK, "两条经验", "报错在哪一层，原因往往在更下面一层\n\n看日志时确认是当前这次的：/data/nomad/alloc 下有旧 alloc；能力文件要核对 PID",
        15, 12.5, style="outline")
    box(s, RX, T + 220, RW, 240, KEY, "日志在哪", "journalctl -u nomad / consul / dnsmasq\ndocker logs postgres、Harbor 各容器\nnomad alloc logs <id> start\n/data/nomad/alloc/<id>/alloc/logs/\n/var/log/nginx/",
        15, 12.5, style="outline", align="start")
    s.text(M + 96, T + 4 * 96 - 6, "通过就往上", 12, OK[2], 600)
    yy = s.footer(T + 5 * 96 + 4, "注：完整的常见问题表按“部署 / 建模板 / 用沙箱 / 运维”四类列在第 20 篇第三节，每条指向讲原理的那一篇。")
    save(s, "20-2-按层排障.svg", yy + 20)


if __name__ == "__main__":
    for name in sorted(n for n in dir() if n.startswith("fig_")):
        globals()[name]()
