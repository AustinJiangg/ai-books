"""《E2B 部署从零讲透》第 6～9 篇的配图。用法: python3 tools/figures/dp_p2.py"""
from dp_common import *  # noqa: F401,F403
from dp_common import W, M


# ------------------------------------------------------------------ 第 6 篇
def fig_06_repo():
    s = Svg()
    y0 = s.header("仓库里有什么：原料、改良、配方、摆盘",
                  "这是一个“打包仓库”：没有 packages/api 这类源码目录，E2B 的源码整个装在一个走 git-lfs 的压缩包里；"
                  "对源码的全部修改集中在一个补丁里；spec 把它们变成 RPM；e2b-deploy/ 决定装好后怎么部署。")
    T = y0 + 34
    cw = (W - 2 * M - 3 * 20) / 4
    cols = [
        (SVC, "原料", "拿来就用，不改内容", [("e2b-infra-2026.09.tar.gz", "上游源码 + vendor/，约 140 MB，git-lfs"),
                                      ("tools-arm64.tar.gz", "离线 Go 工具链 go1.25.4"),
                                      ("firecracker.arm", "定制 Firecracker"),
                                      ("vmlinux.bin.arm (.openeuler)", "客户机内核"),
                                      ("busybox_1.35_arm64、goose", "模板 init、数据库迁移"),
                                      ("ubuntu-22.04-custom.tar.gz", "模板基础镜像，约 70 MB")]),
        (RISK, "改良", "对上游的唯一修改", [("0001-adapted-for-arm-architecture.patch", "约 900 KB、170 多个文件"),
                                      ("功能改动", "ARM 适配、去 GCP、MinIO/Local、快照回滚、FC 启动优化"),
                                      ("部署改动", "job 文件、Dockerfile、Makefile、初始化脚本、Helm")]),
        (JOB, "配方", "rpmbuild 读它", [("e2b-infra.spec", "Source0～9 + Patch1"),
                                     ("%prep / %build", "解压、打补丁、离线编译"),
                                     ("%install / %files", "摆进 /opt/e2b-infra")]),
        (OK, "摆盘", "装好后怎么部署", [("e2b-deploy/build.sh", "单机部署总开关"),
                                     ("e2b-deploy/dep/", ".env、单机版脚本与 hcl、SDK 替换文件、MinIO/Nginx 配置"),
                                     ("patch_e2b.py", "SDK 的 https → http")]),
    ]
    yend = T
    for i, (role, t, sub, items) in enumerate(cols):
        x = M + i * (cw + 20)
        box(s, x, T, cw, 70, role, t, sub, 17, 12.5)
        y = T + 86
        for a, b in items:
            h = need_h(cw - 16, a, b, 13.5, 12, extra=18)
            box(s, x + 8, y, cw - 16, h, white(role), a, b, 13.5, 12)
            y += h + 8
        yend = max(yend, y)
    y = yend + 10
    box(s, M, y, W - 2 * M, 64, KEY, "说明书：single-node-offline-deploy.md（怎么做）· deploy-docs/（为什么）· docs/zh/（多节点、k8s）· benchmark/ rollback/ gsd/",
        None, 13.5, style="outline")
    yy = s.footer(y + 92, "注：clone 之后要 git lfs pull，否则源码包只是 134 字节的指针；不能拿 GitHub 的标签归档代替（没有 vendor/，补丁打不上）。")
    save(s, "06-1-仓库文件地图.svg", yy + 20)


# ------------------------------------------------------------------ 第 7 篇
def fig_07_rpmbuild():
    s = Svg()
    y0 = s.header("rpmbuild 流水线：一份 spec，五个阶段",
                  "rpmbuild -bb e2b-infra.spec --define \"_sourcedir $PWD\"：原料直接从仓库根目录取；编译全程不联网（GOFLAGS=-mod=vendor）。")
    T = y0 + 34
    s.text(M, T, "输入（_sourcedir = 仓库根目录）", 13.5, SUB, 600)
    pill_row(s, M, T + 26, ["Source0 源码包", "Patch1 补丁", "Source1 busybox", "Source2/3 goose", "Source4/6 内核",
                             "Source8 firecracker", "Source9 ubuntu 镜像", "tools-arm64.tar.gz", "e2b-deploy/"], SVC, 12, 8)
    T2 = T + 70
    items = [(JOB, "%prep", "解压源码、打补丁\n拷 busybox、解 Go 工具链\n复制 e2b-deploy/"),
             (JOB, "%build", "GOROOT=自带工具链\nGOFLAGS=-mod=vendor\n5 个模块 make build + seed-db"),
             (JOB, "%install", "产物摆进 BUILDROOT\n/opt/e2b-infra/bin、nomad/\n根目录脚本、dep/"),
             (JOB, "%files", "声明包拥有的文件\n升级时替换，没列的不碰"),
             (OK, ".rpm", "e2b-infra-2026.09-3\n.aarch64.rpm")]
    flow_h(s, M, T2, W - 2 * M, items, h=130, gap=36, ts=17, ss=12.5)
    T3 = T2 + 170
    s.text(M, T3, "%build 的产物", 13.5, SUB, 600)
    rows = [["packages/api", "bin/api", "CGO 关"], ["packages/client-proxy", "bin/client-proxy", "CGO 关"],
            ["packages/envd", "bin/envd", "CGO 关"], ["packages/db", "bin/migrator", "db-migrator 镜像里的程序"],
            ["packages/orchestrator", "bin/orchestrator、fc-netns-exec、clean-nfs-cache", "CGO 开 → 需要 gcc"],
            ["packages/db/scripts/seed/postgres", "seed-db", "单独 go build"]]
    y = table(s, M, T3 + 14, [440, 640, 424], rows, header=["模块", "产物", "备注"], ts=13)
    yy = s.footer(y + 14, "注：%ifarch 让同一份 spec 能出 aarch64 和 x86_64 两种包；定制 Firecracker 只打进 aarch64 包。")
    save(s, "07-1-rpmbuild流水线.svg", yy + 20)


# ------------------------------------------------------------------ 第 8 篇
def fig_08_opt():
    s = Svg()
    y0 = s.header("装好的 /opt/e2b-infra：每一块从哪来",
                  "左边是来源，右边是装好后的位置。注意 nomad/ 下十来个 job 模板只用 4 个，bin/orchestrator.Dockerfile 会在 -s 时被删掉。")
    T = y0 + 34
    LW = 520
    RX = M + LW + 160
    RW = W - M - RX
    src = [(JOB, "上游源码 + 补丁，%build 编译", "api、client-proxy、envd、orchestrator、migrator、seed-db、fc-netns-exec"),
           (JOB, "上游源码 + 补丁，直接拷贝", "各模块 Dockerfile、db/migrations、iac/.../jobs/*.hcl、helm/"),
           (MACH, "上游源码 + 补丁里的运维脚本", "iac/provider-gcp/... 和 .github/actions/host-init/ 下的\nstart-*.sh、init-client.sh、deploy.sh、run-*.sh"),
           (SVC, "仓库根目录的预编译文件", "firecracker.arm、vmlinux.bin.*、goose、patch_e2b.py"),
           (OK, "仓库的 e2b-deploy/", "build.sh、dep/（单机版脚本、.env、hcl、SDK 文件）+ ubuntu 镜像")]
    dst = [("bin/", "二进制、*.Dockerfile、migrations/"), ("nomad/ 、 helm/", "job 模板（只用 4 个）、Kubernetes 用"),
           ("根目录脚本", "deploy.sh、start-*.sh、init-client.sh …（上游版）"),
           ("bin/firecracker、vmlinux.bin*、goose；patch_e2b.py", ""), ("build.sh 、 dep/", "单机部署入口与覆盖源")]
    h = 92
    for i, ((role, t, sub), (dt, dsub)) in enumerate(zip(src, dst)):
        y = T + i * (h + 16)
        box(s, M, y, LW, h, role, t, sub, 14.5, 12)
        box(s, RX, y, RW, h, white(role), "/opt/e2b-infra/" + dt, dsub or None, 14.5, 12)
        arrow(s, [(M + LW + 4, y + h / 2), (RX - 4, y + h / 2)], INK, 1.5)
    yy = s.footer(T + 5 * (h + 16) + 10, "注：根目录脚本和 dep/ 下有同名文件，两份内容不同；-i 用 dep/ 版覆盖根目录版（下一张图）。")
    save(s, "08-1-opt目录来源.svg", yy + 20)


def fig_08_layers():
    s = Svg()
    y0 = s.header("完整部署 = RPM 底座 + dep/ 覆盖 + 运行时生成物",
                  "实际生效的是 dep/ 的单机版。rpm -Uvh 会把根目录打回上游版，所以升级后要重放覆盖；而 -i 会顺手覆盖 .env，冲掉真令牌。")
    T = y0 + 34
    LW = 1040
    layers = [
        (SBX, "③ 运行时生成物", "-s、deploy.sh、各脚本写出；RPM 永不触碰",
         ".env 里的真 ACL 令牌 · rendered/*.hcl · /usr/bin/template-manager · /etc/nomad.d、/etc/consul.d、/etc/dnsmasq* · /data/nomad/acl.token · SDK 补丁"),
        (OK, "② dep/ 覆盖", "build.sh -i 从 dep/ 拷到根目录",
         "单机版 deploy.sh（有 --only）· start-*.sh · init-client.sh · run-*.sh · nomad/template-manager.hcl · 根目录 .env"),
        (MACH, "① RPM 底座", "rpm -ivh / -Uvh 整层重铺",
         "bin/* · nomad/*.hcl（上游版）· 根目录 deploy.sh 等（上游版）· dep/*（含 dep/.env）· build.sh"),
    ]
    h = 120
    for i, (role, t, sub, body) in enumerate(layers):
        y = T + i * (h + 24)
        band(s, M, y, LW, h, role, t, sub)
        for k, ln in enumerate(wrap(body, LW - 60, 13)):
            s.text(M + 20, y + 82 + k * 20, ln, 13, INK)
    RX = M + LW + 40
    RW = W - M - RX
    notes = [(OK, "build.sh -i", "重做第②层；但也把 dep/.env 拷到根目录，冲掉第③层的真令牌"),
             (RISK, "rpm -Uvh", "只重铺第①层，却让第②层失效：deploy.sh 丢 --only，template-manager.hcl 变回上游版"),
             (KEY, "-d + -s", "重建第③层：集群从零开始，令牌换新")]
    for i, (role, t, b) in enumerate(notes):
        box(s, RX, T + i * (h + 24), RW, h, role, t, b, 15, 12.5, style="outline")
    yy = s.footer(T + 3 * (h + 24) + 6, "注：升级 RPM 后重放覆盖时，要拷 dep/ 下除 .env 以外的文件（第 19 篇）。")
    save(s, "08-2-两层结构.svg", yy + 20)


def fig_08_step0():
    s = Svg()
    y0 = s.header("第 0 步：执行 build.sh 之前，机器要自己备好的东西",
                  "这些事脚本不管或只管一半。每张卡片下半截是“不做会怎样”，报错往往离原因很远。")
    T = y0 + 30
    cards = [
        ("硬件与系统", "鲲鹏、BIOS 开虚拟化、/dev/kvm、openEuler", "Firecracker 起不来"),
        ("Docker + Compose v2", "docker ≥ 25.0.3；源里的 docker-compose 1.22 不行", "装 Harbor 报 Unsupported config option"),
        ("insecure-registries", "daemon.json 加 <IP>:2900，合并而非覆盖", "push 镜像失败"),
        ("nbd 模块固化", "自编译 nbd.ko，nbds_max=512，开机加载", "NBD module not loaded；升级内核后悄悄失效"),
        ("SELinux permissive", "写进 /etc/selinux/config", "重启后 Nomad、Consul 报 203/EXEC"),
        ("IP 转发", "openEuler 的 sysctl.conf 写死了 0；新脚本会改", "建模板等 envd 60 秒超时"),
        ("resolv.conf", "NetworkManager 设 dns=none", "网卡重连后 e2b 域名解析失效"),
        ("离线大件放进 dep/", "consul、nomad（≥ 1.11.2）zip、Harbor 包、minio", "-i/-s 找不到文件；旧 Nomad 遇 NUMA panic"),
        ("docker load 三个镜像", "postgres:latest、redis:7.4.4-alpine、debian:bookworm-slim", "-i 报镜像不存在；构建镜像卡住"),
        ("yum 源、pip 源", "dnsmasq、nginx；e2b SDK", "-i 安装失败"),
        ("SERVER_IP", "dep/.env 第一行，取默认路由的源地址", "check_host_ip 拦下；不拦的话 504 误导"),
    ]
    cols = 4
    gap = 18
    cw = (W - 2 * M - gap * (cols - 1)) / cols
    ch = 150
    for i, (t, how, bad) in enumerate(cards):
        r, c = divmod(i, cols)
        x = M + c * (cw + gap)
        y = T + r * (ch + gap)
        s.rect(x, y, cw, ch, "#FFFFFF", MACH[1], 1.3, rx=10)
        s.text(x + 16, y + 30, t, 15, INK, 600)
        for k, ln in enumerate(wrap(how, cw - 32, 12.5)):
            s.text(x + 16, y + 54 + k * 19, ln, 12.5, SUB)
        s.rect(x + 1, y + ch - 52, cw - 2, 51, RISK[0], "none", 0, rx=9)
        for k, ln in enumerate(wrap("不做：" + bad, cw - 32, 12.5)[:2]):
            s.text(x + 16, y + ch - 30 + k * 18, ln, 12.5, RISK[2])
    rows = (len(cards) + cols - 1) // cols
    yy = s.footer(T + rows * (ch + gap) + 4, "注：这些属于“装一次机器做一次”的事，和内核、硬件绑定，所以不放进每次都执行的部署脚本。")
    save(s, "08-3-第0步清单.svg", yy + 20)


# ------------------------------------------------------------------ 第 9 篇
def fig_09_tree():
    s = Svg()
    y0 = s.header("build.sh 三个主模式的调用树",
                  "-i 装依赖，-s 几乎包揽了机器层、宿主服务层和业务层的全部启动工作，-d 先让 orchestrator 自己清理、再按顺序停、最后扫残留。")
    T = y0 + 40
    cw = (W - 2 * M - 2 * 30) / 3
    trees = [
        ("build.sh -i", SVC, [(0, "install()", None, KEY), (1, "check_host_ip", None, OK), (1, "yum_install", "dnsmasq 等", MACH),
                              (1, "setenforce 0", None, MACH), (1, "install_postgre", "docker", SVC), (1, "install_minio", "systemd", SVC),
                              (1, "install_harbor", "只解压改配置", SVC), (1, "install_nginx", "证书 ×3 处", SVC), (1, "install_e2b", None, JOB),
                              (2, "pip install", "SDK", JOB), (2, "dep/ 覆盖", None, JOB), (2, "zip → /tmp", None, JOB),
                              (2, "SDK 三层改造", None, JOB), (2, "dnsmasq", "*.e2b.app", MACH)]),
        ("build.sh -s", JOB, [(0, "start()", None, KEY), (1, "harbor/install.sh", None, SVC), (1, "start-server.sh", None, SVC),
                              (2, "run-consul.sh", "ACL", SVC), (2, "run-nomad.sh", "ACL、节点池", SVC),
                              (1, "append_nomad_client_config", None, SVC), (1, "start-client.sh", None, MACH),
                              (1, "init-client.sh", None, MACH), (1, "wait_for_port 4646", None, KEY),
                              (1, "Harbor：项目、hosts、镜像", None, SVC), (1, "deploy.sh", None, JOB), (2, "构建 / 推送镜像", None, JOB),
                              (2, "envsubst → job run ×4", None, JOB), (2, "seed-db、配额", None, JOB), (1, "iptables 80→3002", None, MACH)]),
        ("build.sh -d", RISK, [(0, "stop()", None, KEY), (1, "graceful_stop_template_manager", None, OK),
                               (1, "uninstall-consul.sh", "删集群", RISK), (1, "uninstall-nomad.sh", "删集群", RISK),
                               (1, "kill 业务进程", "按命令行", KEY), (1, "kill firecracker", None, KEY), (1, "pkill nomad、consul", "兜底", KEY),
                               (1, "purge_sandbox_netns", None, MACH), (1, "purge_sandbox_iptables", None, MACH),
                               (1, "check_ports_free", None, OK), (1, "提示大页仍占用", "不释放", KEY)]),
    ]
    yend = T
    for i, (t, role, nodes) in enumerate(trees):
        x = M + i * (cw + 30)
        box(s, x, T, cw, 48, role, t, None, 17)
        y = tree(s, x + 12, T + 86, nodes, indent=26, gap=33, size=13)
        yend = max(yend, y)
    yy = s.footer(yend + 4, "注：-d 里的 uninstall-*.sh 不只是停，还删掉 Nomad、Consul 的配置、数据和令牌文件；之后的 -s 是一个全新集群。")
    save(s, "09-1-调用树.svg", yy + 20)


def fig_09_persist():
    s = Svg()
    y0 = s.header("build.sh 的改动：哪些重启后还在，哪些会丢",
                  "这台机器重启后不会自动恢复成可用状态。最省事的恢复是 -d、-s，再重建模板；-i 装的东西大多是持久的。")
    T = y0 + 34
    cw = (W - 2 * M - 30) / 2
    keep = ["PostgreSQL 容器（--restart=always）", "Nomad、Consul、MinIO、Nginx、dnsmasq（systemd enable）", "证书与系统信任库",
            "/etc/dnsmasq.conf、/etc/dnsmasq.d/consul.conf、/etc/hosts", "/etc/sysctl.conf：IP 转发、连接数",
            "/swapfile + /etc/fstab", "nbd 的 udev 规则", "/usr/bin/template-manager", "/fc-kernels、/fc-versions、/fc-envd",
            "/etc/resolv.conf 第一行（NetworkManager 可能改）"]
    lose = ["setenforce 0（除非按第 8 篇持久化）", "大页池 nr_hugepages、nr_overcommit_hugepages", "/mnt/hugepages、/mnt/snapshot-cache 挂载",
            "iptables 80 → 3002 两条规则", "sysctl -w 设的 swappiness 等", "/tmp/templates 里的模板（/tmp 是 tmpfs）",
            "/tmp 里的 Nomad、Consul 安装包", "沙箱的网络命名空间、虚拟网卡（这是好事）"]
    for i, (role, t, items) in enumerate([(OK, "重启后还在：写进了文件", keep), (RISK, "重启后丢失：只在内存里", lose)]):
        x = M + i * (cw + 30)
        box(s, x, T, cw, 52, role, t, None, 16)
        y = T + 76
        for it in items:
            s.rect(x, y, cw, 40, role[0] if i else "#FFFFFF", role[1], 1, rx=8)
            s.text(x + 16, y + 26, it, 13.5, INK)
            y += 48
    yy = s.footer(T + 76 + 10 * 48 + 6, "注：模板丢失是最容易忽略的一项：本环境的模板实际存在 /tmp/templates，重启后要重新构建。")
    save(s, "09-2-持久与临时.svg", yy + 20)


if __name__ == "__main__":
    for name in sorted(n for n in dir() if n.startswith("fig_")):
        globals()[name]()
