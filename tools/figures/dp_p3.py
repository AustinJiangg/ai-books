"""《E2B 部署从零讲透》第 10～16 篇的配图。用法: python3 tools/figures/dp_p3.py"""
from dp_common import *  # noqa: F401,F403
from dp_common import W, M


# ------------------------------------------------------------------ 第 10 篇
def fig_10_deps():
    s = Svg()
    y0 = s.header("build.sh -i 装出来的周边依赖",
                  "四样东西都不属于 E2B，但 E2B 离不开。PostgreSQL 每次 -i 都重建；MinIO 装了没用上；Harbor 分两段装；Nginx 只为给 Harbor 套一层 HTTPS。")
    T = y0 + 34
    rows = [
        ["PostgreSQL", "docker，--restart=always", "5432", "容器可写层（没挂卷）", "postgres / local，库 mydatabase", "每次 -i 删容器重建，数据清空；表由 api 的 db-migrator 建"],
        ["MinIO", "systemd", "9000、9001", "/root/data/minio", "minioadmin / minioadmin", "健康检查过了，但没人往里写：STORAGE_PROVIDER 写死 Local"],
        ["Harbor", "docker compose（十来个容器）", "2900", "/opt/e2b-infra/harbor/", "admin / Harbor12345", "-i 只解压、改 harbor.yml（关 HTTPS、hostname、端口）；-s 才启动"],
        ["Nginx", "systemd", "443", "/etc/nginx", "—", "server_name harbor，反代到 2900；自签证书 CN=harbor，一年有效"],
    ]
    y = table(s, M, T, [150, 250, 120, 250, 280, 454], rows, header=["组件", "跑法", "端口", "数据", "账号", "要注意的"],
              ts=13.5, roles=[SVC, None, SVC, None])
    yy = s.footer(y + 14, "注：-u 卸载时 MinIO 那一行被注释了，它和数据目录会一直留在机器上；Docker 是自备的，-u 也不动。")
    save(s, "10-1-周边依赖.svg", yy + 20)


def fig_10_harbor443():
    s = Svg()
    y0 = s.header("harbor:443 这条路：建模板拉基础镜像时经过谁",
                  "template-manager 用 go-containerregistry 拉镜像，对非 localhost 地址默认走 HTTPS、不认 insecure-registries。"
                  "于是给 Harbor 套一层 Nginx + 自签证书，名字必须是 harbor。")
    T = y0 + 40
    items = [(JOB, "template-manager", "FROM harbor:443/e2b-orchestration/\nubuntu:22.04-custom"),
             (MACH, "dnsmasq", "查 /etc/hosts\nharbor → 192.168.10.23"),
             (SVC, "Nginx :443", "出示证书 CN=harbor\n转给 127.0.0.1:2900"),
             (SVC, "Harbor :2900", "返回镜像")]
    flow_h(s, M, T, W - 2 * M, items, h=110, gap=96, labels=["DNS", "HTTPS", "HTTP"])
    T2 = T + 160
    s.text(M, T2, "同一张证书 /etc/nginx/ssl/harbor.crt 装进三处", 14, SUB, 600)
    tw = (W - 2 * M - 2 * 20) / 3
    for i, (t, sub) in enumerate([("系统信任库", "/etc/pki/ca-trust/source/anchors/harbor-ca.crt\n→ update-ca-trust extract；多数程序读这里"),
                                  ("docker 信任目录", "/etc/docker/certs.d/harbor:443/ca.crt\n→ docker daemon 读这里"),
                                  ("SSL_CERT_FILE", "template-manager.hcl 的 env\n→ 进程一定信任这张证书")]):
        box(s, M + i * (tw + 20), T2 + 16, tw, 96, OK, t, sub, 15, 12, style="outline")
    T3 = T2 + 150
    rows = [["/etc/hosts 没有 harbor（-s 写入）", "lookup harbor on 127.0.0.1:53: server misbehaving"],
            ["证书没被信任", "x509: certificate signed by unknown authority"],
            ["证书过期（365 天）", "x509: certificate has expired"],
            ["Nginx 没起来", "connection refused"],
            ["Harbor 里没有基础镜像（-s 推送）", "manifest unknown"]]
    y = table(s, M, T3, [620, 884], rows, header=["缺了哪一环", "建模板时的报错"], ts=13.5)
    yy = s.footer(y + 14, "注：推送镜像走 IP:2900（明文），拉取走 harbor:443（HTTPS），两者是同一个仓库。")
    save(s, "10-2-harbor443路径.svg", yy + 20)


# ------------------------------------------------------------------ 第 11 篇
def fig_11_sdk():
    s = Svg()
    y0 = s.header("SDK 的三层改造：先整文件覆盖，最后做文本替换",
                  "装好 e2b==2.20.0、e2b_code_interpreter==2.4.1 之后，install_e2b 依次做三层。connection_config.py 三层都动过：最终起作用的是第二层那份，再被第三层改成 http。")
    T = y0 + 34
    LW = 1000
    layers = [
        (SVC, "第一层：替换 5 个文件（cp）", "connection_config.py：api、沙箱地址改 http\ndockerfile_parser.py：保留 Dockerfile 的 USER、WORKDIR\n"
                                         "template_sync/build_api.py、main.py：建模板走老接口 POST /templates，access token + API key 双客户端\n"
                                         "code_interpreter_sync.py：与原版相同"),
        (JOB, "第二层：checkpoint 覆盖层（install.py）", "21 个文件：12 个新增，9 个覆盖（留 .orig）\n加 sandbox.checkpoint.create() / restore()\n版本不是 2.20.0 就停；装完自检"),
        (OK, "第三层：patch_e2b.py（文本替换）", "connection_config.py 全文 https → http\ncode_interpreter（同步、异步）的 Jupyter 地址\nvolume、MCP 地址（可选）；留 .backup，清 __pycache__"),
    ]
    y = T
    for i, (role, t, sub) in enumerate(layers):
        h = need_h(LW - 80, t, sub, 16, 12.5, extra=30)
        num(s, M + 14, y + h / 2, i + 1)
        box(s, M + 40, y, LW - 40, h, role, t, sub, 16, 12.5, align="start")
        if i < 2:
            arrow(s, [(M + 14, y + h / 2 + 14), (M + 14, y + h + 20)], INK, 1.4)
        y += h + 26
    RX = M + LW + 40
    RW = W - M - RX
    box(s, RX, T, RW, 150, RISK, "顺序反了会怎样", "patch_e2b.py 先把 https 改成 http\n→ checkpoint 覆盖层整文件盖回自带版本\n→ 又是 https，连不上", 15, 12.5, style="outline")
    box(s, RX, T + 170, RW, 150, KEY, "在别的机器上用 SDK", "装同样版本；至少跑 patch_e2b.py\n要建模板还得替换那 5 个文件\n自己把 *.e2b.app 解析到服务器", 15, 12.5, style="outline")
    yy = s.footer(max(y, T + 330) + 4, "注：所以用户的 .env 里既要 E2B_API_KEY，又要 E2B_ACCESS_TOKEN：建模板时两个都要用。")
    save(s, "11-1-SDK三层改造.svg", yy + 20)


# ------------------------------------------------------------------ 第 12 篇
def fig_12_flow():
    s = Svg()
    y0 = s.header("build.sh -s 的完整顺序",
                  "先起服务（Harbor、Consul、Nomad），再准备宿主机，然后等 Nomad 就绪、把镜像和 job 交给它，最后打开 80 端口的入口。右侧是讲它的篇目。")
    T = y0 + 30
    items = [("启动 Harbor", "harbor/install.sh；修属主 10000:10000；重启 registry、proxy", "第 12 篇"),
             ("start-server.sh", "装 Consul、Nomad；以 server 启动；ACL bootstrap；建节点池", "第 12 篇"),
             ("append_nomad_client_config + 重启 Nomad", "同一个 Nomad 也当 client：api 池、raw_exec、network_speed", "第 12 篇"),
             ("start-client.sh", "orchestrator → /usr/bin/template-manager；目录、swap、tmpfs、DNS", "第 12 篇"),
             ("init-client.sh", "IP 转发、sysctl、NBD、envd、内核、Firecracker、大页", "第 13 篇"),
             ("wait_for_port 4646", "永不超时；卡住看 journalctl -u nomad", "第 12 篇"),
             ("Harbor 收尾", "登录、建项目、/etc/hosts 写 harbor、推送 ubuntu:22.04-custom", "第 14 篇"),
             ("deploy.sh", "构建推送镜像 → envsubst → nomad job run ×4 → seed-db、放开配额", "第 14、15 篇"),
             ("iptables 80 → 3002", "PREROUTING（外机）+ OUTPUT（本机）", "第 14 篇")]
    y = steps(s, M, T, W - 2 * M, items, role=WHITE, ts=14.5, ss=12.5, gap=10, note_w=150, note_role=KEY)
    yy = s.footer(y + 6, "注：第 5 步 init-client.sh 必须在第 8 步之前：orchestrator 一启动就建几百个网络槽位，ip_forward 要在那之前就是 1。")
    save(s, "12-1-s全流程.svg", yy + 20)


def fig_12_acl():
    s = Svg()
    y0 = s.header("ACL 令牌：只给一次，所以要存在集群数据旁边",
                  "Consul 先以 allow 启动、bootstrap 后改 deny 重启；Nomad 只在全新集群时 bootstrap，否则从 /data/nomad/acl.token 找回。两者都写回 .env。")
    T = y0 + 44
    s.text(M, T, "Consul（run-consul.sh --server）", 15, SVC[2], 600)
    flow_h(s, M, T + 18, W - 2 * M, [(SVC, "default_policy = allow 启动", "没有令牌也能访问"), (SVC, "等 leader", "/v1/status/leader"),
                                      (SVC, "consul acl bootstrap", "拿到管理令牌"), (OK, "存令牌", "/opt/consul/acl.token\n.env 的 CONSUL_ACL_TOKEN"),
                                      (SVC, "改 deny、带令牌重启", "从此无令牌一律拒绝")], h=96, gap=30, ts=14, ss=12)
    T2 = T + 170
    s.text(M, T2, "Nomad（run-nomad.sh --server）", 15, JOB[2], 600)
    box(s, M, T2 + 18, 300, 96, JOB, "已有 server 在跑？", "问 SERVER_IPS 的 :4646 leader", 14.5, 12)
    box(s, M + 380, T2 - 10, 520, 70, OK, "没有：nomad acl bootstrap", "建节点池 api、build；令牌存 /data/nomad/acl.token", 14, 12)
    box(s, M + 380, T2 + 82, 520, 70, KEY, "有：不再 bootstrap", "从 /data/nomad/acl.token 读回令牌", 14, 12)
    arrow(s, [(M + 304, T2 + 50), (M + 376, T2 + 25)], INK, 1.4)
    arrow(s, [(M + 304, T2 + 80), (M + 376, T2 + 117)], INK, 1.4)
    box(s, M + 980, T2 + 18, W - 2 * M - 980, 96, OK, "写回 .env 的 NOMAD_ACL_TOKEN", "deploy.sh 提交 job 用它", 14.5, 12)
    arrow(s, [(M + 904, T2 + 25), (M + 976, T2 + 55)], INK, 1.4)
    arrow(s, [(M + 904, T2 + 117), (M + 976, T2 + 80)], INK, 1.4)
    T3 = T2 + 190
    box(s, M, T3, W - 2 * M, 70, RISK, "为什么不能只存在 .env 里",
        "-i 会用 dep/.env 覆盖根目录 .env；重装 RPM 会把 dep/.env 打回占位值。令牌跟集群数据放一起：集群在令牌就在，-d 删集群时一起删。", 14.5, 12.5, style="outline")
    yy = s.footer(T3 + 98, "注：.env 里的令牌和集群对不上，deploy.sh 提交 job 就报 403 (Permission denied)。")
    save(s, "12-2-consul-acl.svg", yy + 20)


# ------------------------------------------------------------------ 第 13 篇
def fig_13_prep():
    s = Svg()
    y0 = s.header("init-client.sh：把宿主机调成能跑沙箱的样子",
                  "每一项都对应一个“不做会怎样”。和 start-client.sh 重复的几项（目录、swap、tmpfs、udev、大页）两边都写成了幂等，重复执行没有问题。")
    T = y0 + 30
    rows = [["连接数 sysctl", "somaxconn、netdev_max_backlog、tcp_max_syn_backlog、max_map_count", "高并发时连接被拒", "是"],
            ["ip_forward = 1", "改 /etc/sysctl.conf 那一行（openEuler 写死了 0），再 sysctl -w", "建模板等 envd 60 秒超时；必须在 orchestrator 启动前", "是"],
            ["NBD nowatch", "udev 规则；只对 nbd* 触发", "全机触发：udevd 忙几分钟，脚本超时退出", "是"],
            ["/fc-envd/envd", "从 bin/envd 拷", "建模板失败；换 envd 要重建模板", "是"],
            ["/fc-kernels/<版本>/", "vmlinux-6.1.158、6.1.102（同一个文件）、6.6.0-132.0.0", "Provisioning sandbox template 失败", "是"],
            ["/fc-versions/v1.13.1/", "定制 Firecracker；先 rm 再 cp", "沙箱起不来；Text file busy", "是"],
            ["/mnt/hugepages", "mount -t hugetlbfs", "客户机内存没有大页", "否"],
            ["大页池", "保留 4～42 GiB 普通内存；剩余 20%（≤64 GiB）静态 + 80% 超分配", "沙箱分配不到内存", "否"]]
    y = table(s, M, T, [230, 620, 520, 134], rows, header=["准备项", "怎么做", "不做会怎样", "持久"], ts=13.5,
              roles=[None, RISK, None, None, None, None, None, None])
    yy = s.footer(y + 14, "注：脚本以 set -euo pipefail、set -x 运行，屏幕上会刷出大量带时间戳的命令，便于出错时定位到具体哪一行。")
    save(s, "13-1-宿主机准备.svg", yy + 20)


def fig_13_runtime():
    s = Svg()
    y0 = s.header("运行时文件：从 /opt/e2b-infra/bin 拷到 orchestrator 找的位置",
                  "上游从存储桶下载这些文件，本环境直接从 RPM 拷。目录名只是寻址用的标签：内核按模板请求里的版本号找，Firecracker 按代码里的版本号找。")
    T = y0 + 34
    LW, RX = 380, M + 520
    RW = W - M - RX - 330
    pairs = [("bin/envd", ["/fc-envd/envd"], "建模板时放进模板的磁盘"),
             ("bin/vmlinux.bin", ["/fc-kernels/vmlinux-6.1.158/vmlinux.bin", "/fc-kernels/vmlinux-6.1.102/vmlinux.bin"], "默认版本 6.1.158（api 编译进去的）"),
             ("bin/vmlinux.bin.openeuler", ["/fc-kernels/vmlinux-6.6.0-132.0.0/vmlinux.bin"], "指定该版本的模板用"),
             ("bin/firecracker", ["/fc-versions/v1.13.1/firecracker"], "定制版（基于 v1.12.1）；先删后拷")]
    y = T
    for src, dsts, note in pairs:
        h = 46 * len(dsts) + 10 * (len(dsts) - 1)
        box(s, M, y, LW, h, MACH, "/opt/e2b-infra/" + src, None, 14)
        for k, d in enumerate(dsts):
            dy = y + k * 56
            box(s, RX, dy, RW, 46, SBX, d, None, 13.5)
            arrow(s, [(M + LW + 4, y + h / 2), (RX - 4, dy + 23)], INK, 1.4)
        s.text(RX + RW + 20, y + h / 2 + 5, note, 13, SUB)
        y += h + 26
    yy = s.footer(y + 4, "注：/usr/bin/template-manager 是另一条路：start-client.sh 从 bin/orchestrator 拷过去（第 12 篇）。三者都不归 RPM 管，升级后要重新拷。")
    save(s, "13-2-运行时文件.svg", yy + 20)


def fig_13_huge():
    s = Svg()
    y0 = s.header("大页怎么切：三刀",
                  "第一刀给系统留普通内存 max(4 GiB, 16%)，最多 42 GiB；剩下的都算大页内存。第三刀：20% 立即划走做静态池（上限 HUGEPAGES_BASE_MAX_MIB，默认 64 GiB），80% 做超分配上限。")
    T = y0 + 40
    L, R = M, W - M
    TW = R - L

    def bar(y, label, total, parts):
        s.text(L, y - 12, label, 15, INK, 600)
        x = L
        for size, role, t, sub in parts:
            w = TW * size / total
            s.rect(x, y, w - 2, 70, role[0], role[1], 1.3, rx=6)
            if w > 120:
                s.text(x + 12, y + 30, t, 14, role[2], 600)
                s.text(x + 12, y + 52, sub, 12.5, SUB)
            x += w
        return x

    bar(T + 20, "例一：总内存 256 GiB", 256, [(41, MACH, "保留 41 GiB", "16%"), (43, SBX, "静态池 43 GiB", "20%，未到上限"),
                                          (172, white(SBX), "超分配池 172 GiB", "80%，用到才分配")])
    bar(T + 150, "例二：总内存 1.5 TiB（1536 GiB）", 1536, [(42, MACH, "", ""), (64, SBX, "静态 64G", "上限"),
                                                     (1195, white(SBX), "超分配池约 1195 GiB", "80% × 764928 页"),
                                                     (235, RISK, "约 235 GiB", "被上限截掉，留作普通内存")])
    s.text(L, T + 248, "左边两小段：保留 42 GiB（16% 超过了 42 GiB 上限）· 静态池 64 GiB（20% 约 299 GiB，被上限截到 64 GiB）", 12.5, SUB)
    T2 = T + 290
    rows = [["静态池", "/proc/sys/vm/nr_hugepages", "开机就划走、一直占着，不管有没有沙箱；保证一定拿得到"],
            ["超分配池", "/proc/sys/vm/nr_overcommit_hugepages", "只是上限；用到时才分配，用完归还"],
            ["生命周期", "写在 /proc，不持久", "重启归零；-d 故意不释放（避免内存碎片）；--purge-hugepages 才释放"]]
    y = table(s, M, T2, [180, 460, 864], rows, header=["", "写到哪", "特点"], ts=13.5)
    yy = s.footer(y + 14, "注：脚本按字段名精确读 /proc/meminfo（鲲鹏上有 RemoteMemTotal 这一行），大页大小也不写死（64K 基页内核上是 512 MiB）。")
    save(s, "13-3-大页切分.svg", yy + 20)


# ------------------------------------------------------------------ 第 14 篇
def fig_14_deploy():
    s = Svg()
    y0 = s.header("deploy.sh 的三段",
                  "先 source .env（set -a 导出）。--only <job> 时跳过第一段和第三段，只渲染并提交那一个 job，这就是 build.sh -r。")
    T = y0 + 34
    cw = (W - 2 * M - 2 * 40) / 3
    cols = [(SVC, "① 构建并推送镜像", ["bin/*.Dockerfile 逐个 docker build", "api、client-proxy、db-migrator", "（orchestrator.Dockerfile 已被删）",
                                     "redis:7.4.4-alpine 打标签推送", "DOCKER_BUILDKIT=0", "需要本机已有 debian:bookworm-slim"]),
            (JOB, "② 渲染并提交 job", ["envsubst '<约 100 个变量的白名单>'", "nomad/*.hcl → rendered/*.hcl", "$${NOMAD_PORT_proxy} 之类原样保留",
                                    "nomad job run --token ... 依次：", "redis → template-manager → edge → api"]),
            (OK, "③ 初始化数据", ["teams 里没有 E2B 才执行", "echo admin@e2b.dev | seed-db", "摘出 Team ID、Access Token、Team API Key",
                                "写 /root/.e2b/config.json", "UPDATE tiers … base_v1 → 10000"])]
    yend = T
    for i, (role, t, items) in enumerate(cols):
        x = M + i * (cw + 40)
        box(s, x, T, cw, 54, role, t, None, 16.5)
        y = T + 70
        for it in items:
            box(s, x, y, cw, 46, white(role), None, it, 13, 13)
            y += 54
        yend = max(yend, y)
        if i < 2:
            arrow(s, [(x + cw + 4, T + 27), (x + cw + 36, T + 27)], INK, 1.5)
    yy = s.footer(yend + 6, "注：文件名和 job 名不一定一样：edge.hcl 里的 job 叫 client-proxy，template-manager.hcl 里的叫 template-manager-system。")
    save(s, "14-1-deploy三段.svg", yy + 20)


def fig_14_var():
    s = Svg()
    y0 = s.header("以 API_PORT=3000 为例：一个值从 .env 走到进程",
                  "envsubst 是中间关键的一步：nomad/ 是模板，rendered/ 是填好值的成品，Nomad 只认 rendered/。")
    T = y0 + 40
    items = [(MACH, "dep/.env", "API_PORT=3000"), (MACH, "/opt/e2b-infra/.env", "-i 拷过来"), (KEY, "deploy.sh", "source + set -a"),
             (KEY, "envsubst", "${API_PORT} → 3000"), (JOB, "rendered/api.hcl", 'static = "3000"'), (JOB, "Nomad", "nomad job run"),
             (SBX, "api 进程", "--port 3000")]
    flow_h(s, M, T, W - 2 * M, items, h=100, gap=26, ts=14, ss=12)
    yy = s.footer(T + 130, "注：这条链上的每一环都可能断（写死、不在白名单、改错层、没重启），第 16 篇专门讲。")
    save(s, "14-2-变量旅程.svg", yy + 20)


def fig_14_entry():
    s = Svg()
    y0 = s.header("80 端口的入口：两条 iptables 规则",
                  "SDK 访问 http://49983-<ID>.e2b.app 默认用 80 端口，client-proxy 监听 3002。外机来的包走 PREROUTING，本机自己发给自己的包走 OUTPUT。")
    T = y0 + 40
    s.text(M, T, "别的机器上的 SDK", 14.5, INK, 600)
    flow_h(s, M, T + 16, W - 2 * M, [(KEY, "外机 SDK", "*.e2b.app → 服务器 IP"), (MACH, "物理网卡", "192.168.10.23:80"),
                                      (MACH, "nat PREROUTING", "-m addrtype --dst-type LOCAL\n-j REDIRECT --to-port 3002"), (JOB, "client-proxy :3002", None)],
           h=96, gap=40)
    T2 = T + 160
    s.text(M, T2, "本机上的 SDK", 14.5, INK, 600)
    flow_h(s, M, T2 + 16, W - 2 * M, [(KEY, "本机 SDK", "dnsmasq：*.e2b.app → 127.0.0.1"), (MACH, "lo 回环", "127.0.0.1:80"),
                                       (MACH, "nat OUTPUT", "-o lo --dport 80\n-j REDIRECT --to-port 3002"), (JOB, "client-proxy :3002", None)],
           h=96, gap=40)
    T3 = T2 + 160
    box(s, M, T3, W - 2 * M, 80, RISK, "为什么要 --dst-type LOCAL",
        "老规则不带它，会把所有经过本机 PREROUTING 的 80 端口流量截走：同机 AgentENV 沙箱、docker 容器、E2B 自己的沙箱访问外网 HTTP 都会被错误地送进 client-proxy。脚本先删老规则再加新的。",
        15, 12.5, style="outline")
    yy = s.footer(T3 + 108, "注：-w 等待 xtables 锁；-C 检查存在再 -A 追加（幂等）；两条规则没有保存，重启后丢失。")
    save(s, "14-3-80入口.svg", yy + 20)


# ------------------------------------------------------------------ 第 15 篇
def fig_15_mem():
    s = Svg()
    y0 = s.header("template-manager 的 32 GiB 管的是什么",
                  "Nomad 把这个 job 放进一个 cgroup，memory = 32768 是它的上限。Firecracker 进程也在里面，但客户机内存是大页，只记 hugetlb 控制器，不进这本账。")
    T = y0 + 34
    LW = 900
    band(s, M, T, LW, 330, JOB, "Nomad 任务的 cgroup：memory.max = 32 GiB", "nomad.slice/…/<allocID>.start.scope")
    bw = (LW - 60) / 2
    box(s, M + 20, T + 74, bw, 110, white(JOB), "/usr/bin/template-manager", "自己的堆：几十 MB 到几 GB", 15, 12.5)
    box(s, M + 40 + bw, T + 74, bw, 110, white(SBX), "每个 Firecracker 进程", "客户机以外的内存：每个几十 MB\n（ARM 补丁没把它挪到独立 cgroup）", 15, 12.5)
    box(s, M + 20, T + 200, LW - 40, 110, RISK, "页缓存：撑满它的通常是这个", "建模板时解压镜像层、写磁盘镜像、写内存快照；脏页要先落盘才能回收", 15, 12.5)
    RX = M + LW + 40
    RW = W - M - RX
    box(s, RX, T, RW, 150, SBX, "客户机内存（2 MiB 大页）", "MAP_HUGETLB，只记 hugetlb 控制器\n几百个沙箱也不占这 32 GiB", 15.5, 12.5)
    box(s, RX, T + 170, RW, 160, KEY, "两个方向都会错", "太小：建模板时 OOM（退出码 137）\n太大：超过节点可分配内存，调度不上\n（Dimension \"memory\" exhausted）\n两种都表现为 api 一直 503", 15, 12.5, style="outline")
    yy = s.footer(T + 360, "注：cpu = 2048 的单位是 MHz，用于调度预留和 CPU 权重，不是绑定 2 个核。")
    save(s, "15-1-内存配额.svg", yy + 20)


def fig_15_chain():
    s = Svg()
    y0 = s.header("启动依赖链：任何一环断了，最后都表现为 api 一直 503",
                  "api 的 /health 要等发现至少一个 orchestrator 节点才返回 200；nomad job run api 会等部署结果，默认 10 分钟没变健康就判失败。")
    T = y0 + 40
    c1, c2, c3, c4 = M, M + 330, M + 700, M + 1110
    bw = 290
    box(s, c1, T, bw, 70, SVC, "PostgreSQL", "-i 启动", 15, 12)
    box(s, c2, T, bw, 70, JOB, "db-migrator", "prestart：goose 建表", 15, 12)
    box(s, c1, T + 120, bw, 70, JOB, "redis job", "注册 redis.service.consul", 15, 12)
    box(s, c1, T + 240, bw, 70, JOB, "template-manager", "bind 5007、5008 …", 15, 12)
    box(s, c2, T + 240, bw, 70, JOB, "api 发现节点", "问 Nomad → 连 <节点>:5008", 15, 12)
    box(s, c3, T + 120, 330, 70, JOB, "api 进程", ":3000", 15, 12)
    box(s, c3, T + 240, 330, 70, OK, "/health 200", "NodeCount() != 0", 15, 12)
    box(s, c4, T + 240, W - M - c4, 70, OK, "deploy.sh 继续", None, 15)
    box(s, c3, T + 360, 330, 70, JOB, "client-proxy", "连 Redis", 15, 12)
    box(s, c4, T + 120, W - M - c4, 70, RISK, "10 分钟不健康", "Failed due to progress deadline", 15, 12)
    arrow(s, [(c1 + bw + 4, T + 35), (c2 - 4, T + 35)], INK, 1.5)
    arrow(s, [(c2 + bw + 4, T + 35), (c3 + 165, T + 35), (c3 + 165, T + 116)], INK, 1.5)
    arrow(s, [(c1 + bw + 4, T + 155), (c3 - 4, T + 155)], INK, 1.5)
    arrow(s, [(c1 + bw + 4, T + 275), (c2 - 4, T + 275)], INK, 1.5)
    arrow(s, [(c2 + bw + 4, T + 275), (c3 - 4, T + 275)], INK, 1.5)
    arrow(s, [(c3 + 334, T + 275), (c4 - 4, T + 275)], OK[1], 1.5)
    arrow(s, [(c3 + 334, T + 155), (c4 - 4, T + 155)], RISK[1], 1.5, dash="5 4")
    arrow(s, [(c1 + bw + 4, T + 175), (c1 + bw + 20, T + 175), (c1 + bw + 20, T + 395), (c3 - 4, T + 395)], INK, 1.5)
    T2 = T + 470
    rows = [["orchestrator 没起来", "5007/5008 被上一轮残留占着", "nomad job status template-manager-system；ss -lntp"],
            ["起来又死了", "内存配额太小被 OOM；NBD 模块没加载", "nomad alloc status；dmesg | grep -i oom"],
            ["调度不上", "内存配额太大", "nomad job status 里的 Placement Failure"],
            ["api 连不上数据库", "容器没起来、连接串不对", "db-migrator 的日志"],
            ["api 拿不到节点列表", "NOMAD_TOKEN 不对", "api 的日志"]]
    y = table(s, M, T2, [300, 520, 684], rows, header=["断在哪", "根因举例", "先看什么"], ts=13.5)
    yy = s.footer(y + 14, "注：遇到“api 一直 503”，第一步去看 template-manager-system，而不是 api 本身。")
    save(s, "15-2-启动依赖链.svg", yy + 20)


# ------------------------------------------------------------------ 第 16 篇
def fig_16_sources():
    s = Svg()
    y0 = s.header("配置在哪：六个地方",
                  "前三个是一条链（.env → 模板 → 渲染结果 → Nomad → 进程），后三个各自独立。判断一个值生效没有，最终看进程的环境变量。")
    T = y0 + 34
    items = [(MACH, ".env", "dep/.env 与根目录 .env\nAPI_PORT、地址池、令牌"), (MACH, "nomad/*.hcl", "job 模板\n${API_PORT}、写死的 memory"),
             (JOB, "rendered/*.hcl", "envsubst 的成品\nNomad 认的是它")]
    flow_h(s, M, T, 1000, items, h=110, gap=50, labels=["envsubst", ""])
    box(s, M + 1100, T, W - 2 * M - 1100, 110, SBX, "进程", "/proc/<PID>/environ\n最终真相", 16, 12.5)
    arrow(s, [(M + 1004, T + 55), (M + 1096, T + 55)], INK, 1.6, label="nomad job run", ldy=-8, lsize=11.5)
    T2 = T + 170
    s.text(M, T2, "另外三个地方", 14, SUB, 600)
    cw = (W - 2 * M - 2 * 30) / 3
    for i, (t, sub) in enumerate([("脚本里写死", "build.sh：Harbor 账号、端口 2900、\nPostgreSQL 密码、80→3002"),
                                  ("编译进二进制", "默认内核 vmlinux-6.1.158\n槽位池 300 / 1000、OrchestratorAPIPort 5008"),
                                  ("系统配置文件", "/etc/nomad.d、/etc/consul.d、/etc/dnsmasq.conf\n/etc/sysctl.conf、/etc/hosts、daemon.json")]):
        box(s, M + i * (cw + 30), T2 + 16, cw, 110, KEY, t, sub, 15, 12.5, style="outline")
    yy = s.footer(T2 + 156, "注：.env 和 nomad/*.hcl 各有仓库里的一份和机器上的一份；机器上的又分 dep/ 原件和根目录覆盖结果（第 8 篇）。")
    save(s, "16-1-配置来源.svg", yy + 20)


def fig_16_journey():
    s = Svg()
    y0 = s.header("SANDBOXES_HOST_NETWORK_CIDR 的旅程，以及它会在哪里断",
                  "左边八个环节依次传递，右边是四种“改了没用”的情况。验证时从下往上查最快。")
    T = y0 + 30
    items = [("仓库 e2b-deploy/dep/.env", "export SANDBOXES_HOST_NETWORK_CIDR=10.13.0.0/16"),
             ("/opt/e2b-infra/dep/.env", "rpmbuild 打进包"),
             ("/opt/e2b-infra/.env", "build.sh -i 拷到根目录"),
             ("deploy.sh 的环境变量", "source + set -a"),
             ("rendered/template-manager.hcl", "envsubst（变量要在白名单里）"),
             ("Nomad 里的 job 定义", "nomad job run；nomad job inspect 可看"),
             ("template-manager 进程的环境变量", "Nomad 启动任务；/proc/<PID>/environ"),
             ("orchestrator 用 10.13.0.0/16 分配地址", "Go 代码读环境变量")]
    LW = 900
    y = steps(s, M, T, LW, items, role=WHITE, ts=14, ss=12, gap=8)
    RX = M + LW + 40
    RW = W - M - RX
    notes = [(RISK, "被写死的值压过", "hcl 里写字面值 STORAGE_PROVIDER = \"Local\"，.env 的 MinioBucket 没机会进来。特征：.env 改了，rendered/ 没变", 4),
             (RISK, "不在白名单里", "rendered/ 里还留着 ${XXX}。查：grep '\\${[A-Z_]*}' rendered/*.hcl", 4),
             (RISK, "改错了层", "改了 rendered/、根目录 .env 或脚本，下次渲染、-i、rpm -Uvh 时被覆盖", 2),
             (RISK, "没有重启", "值对了，但 job 定义没变化，进程还是旧的", 6)]
    for i, (role, t, b, _) in enumerate(notes):
        box(s, RX, T + i * 128, RW, 116, role, t, b, 15, 12.5, style="outline")
    yy = s.footer(max(y, T + 4 * 128) + 4, "注：同一个变量还会被 build.sh -d 读（根目录 .env 那份），用来判断哪些 iptables 规则是自己的。")
    save(s, "16-2-变量旅程.svg", yy + 20)


if __name__ == "__main__":
    for name in sorted(n for n in dir() if n.startswith("fig_")):
        globals()[name]()
