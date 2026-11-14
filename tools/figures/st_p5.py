"""《E2B 沙箱存储从零讲透》第 18、19 篇的配图。

用法: python3 tools/figures/st_p5.py
"""
from st_common import *  # noqa: F401,F403
from st_common import W, M


# ------------------------------------------------------------------ 第 18 篇
def fig_18_deploy():
    s = Svg()
    y0 = s.header("部署流程里，存储相关的东西是哪一步放上去的",
                  "RPM 把二进制、内核、定制 Firecracker 和部署包装到 /opt/e2b-infra；-i 装 MinIO、Harbor、nginx 并用 dep/ 覆盖上游文件；"
                  "-s 才真正建目录、挂 tmpfs、预留大页、放运行环境文件、启动 Harbor 和提交 job。")
    T = y0 + 40
    cols = [("RPM 安装", HOST, ["bin/orchestrator  envd", "bin/vmlinux.bin（.openeuler）", "bin/firecracker（定制，aarch64）",
                               "nomad/*.hcl（上游版）", "dep/：.env、template-manager.hcl、\ninit-client.sh、Harbor/MinIO 包、\nubuntu-22.04-custom.tar.gz"]),
            ("部署前（手工一次）", RISK, ["自编译 nbd.ko 固化到系统", "modules-load.d：开机加载", "modprobe.d：nbds_max=512",
                                     "升级内核后要重做"]),
            ("build.sh -i", ORCH, ["MinIO → /root/data/minio", "Harbor 解压、改 harbor.yml", "nginx：harbor:443 + 自签证书",
                                  "dep/ 覆盖 /opt/e2b-infra 同名文件\n（STORAGE_PROVIDER=\"Local\" 由此生效）", "SDK 补丁、检查点 SDK"]),
            ("build.sh -s", GOOD, ["启动 Harbor，建项目，推基础镜像", "/orchestrator/{sandbox,template,build}",
                                  "/swapfile 1G；/mnt/snapshot-cache tmpfs", "nbd udev 规则；/fc-vm；大页预留",
                                  "/fc-envd /fc-kernels /fc-versions", "提交 redis、template-manager、edge、api"])]
    cw = (W - 2 * M - 3 * 30) / 4
    for i, (t, role, items) in enumerate(cols):
        x = M + i * (cw + 30)
        box(s, x, T, cw, 54, role, t, None, 16)
        y = T + 74
        for it in items:
            h = need_h(cw - 20, it, None, 13, extra=18) if "\n" not in it else 18 + 22 * (it.count("\n") + 1)
            box(s, x + 10, y, cw - 20, h, WHITE, it, None, 13)
            y += h + 10
        if i < 3:
            arrow(s, [(x + cw + 4, T + 27), (x + cw + 26, T + 27)], INK, 1.5)
    T2 = T + 400
    box(s, M, T2, W - 2 * M, 80, KEY, "build.sh -d：停进程、杀残留 Firecracker；不动 /tmp/templates、/orchestrator 下的缓存、大页池、MinIO 和 Harbor 的数据",
        "大页要 build.sh --purge-hugepages；被强杀的沙箱留在 /orchestrator/sandbox 的 COW 文件不会被自动清理", 15, 12.5)
    yy = s.footer(T2 + 116, "注：改任何配置都要改源头 e2b-deploy/dep/…，再 build.sh -r template-manager 只重跑这一个 job；"
                            "重跑会结束所有运行中的沙箱、作废检查点、清空 /orchestrator/build。")
    save(s, "18-1-部署流程.svg", yy + 20)


def fig_18_cgroup():
    s = Svg()
    y0 = s.header("template-manager 的 32 GiB 上限记的是什么",
                  "Firecracker 进程和 orchestrator 在同一个 Nomad 任务 cgroup 里（ARM 补丁注释掉了把它挪进独立 cgroup 的几行），"
                  "但客户机内存是 hugetlb 映射，只记 hugetlb 控制器，不进 memory.max 的账。")
    T = y0 + 40
    s.rect(M, T, 900, 360, ORCH[0], ORCH[1], 1.4, rx=14)
    s.text(M + 20, T + 32, "nomad.slice/…/<allocID>.start.scope   memory.max = 32 GiB", 15, ORCH[2], 600)
    box(s, M + 30, T + 60, 400, 120, white(ORCH), "/usr/bin/template-manager", "堆：几十 MB 到几 GB\n构建、快照读写文件的页缓存", 15, 12.5)
    box(s, M + 470, T + 60, 400, 120, white(GUEST), "每个沙箱的 Firecracker", "进程本身的少量内存\n读写 /dev/nbdN 产生的页缓存", 15, 12.5)
    box(s, M + 30, T + 210, 840, 120, RISK, "撑满它的通常是页缓存",
        "解包镜像、写 rootfs、写 memfile diff、读写 /orchestrator/build 缓存文件\n事故：建 200 MB 基础镜像时被 OOM 杀（Exit 137），现场堆只有几十 MB", 15, 12.5)
    RX = M + 960
    box(s, RX, T, W - M - RX, 170, GUEST, "客户机内存（2 MiB 大页）", "MAP_HUGETLB，只记 hugetlb 控制器\n几百个沙箱也不占这 32 GiB", 16, 13)
    box(s, RX, T + 200, W - M - RX, 160, WHITE, "设多大", "太小：OOM（Exit 137），api 一直 503\n太大：超过节点可分配内存，调度不上\n（Dimension \"memory\" exhausted），同样 api 503\n历史：8192 → 32768 → 262144 → 32768 MiB", 15, 12.5)
    yy = s.footer(T + 396, "注：/sys/fs/cgroup/e2b/sbx-<id> 目录仍会被建出来，但里面没有进程。")
    save(s, "18-2-内存上限.svg", yy + 20)


# ------------------------------------------------------------------ 第 19 篇
def fig_19_memory():
    s = Svg()
    y0 = s.header("容量账：模板和快照吃的是宿主的普通内存，不是大页，也不是硬盘",
                  "/tmp/templates 在 tmpfs 上，挤在“给宿主留的普通内存”里（总内存 16%，最多 42 GiB），"
                  "和操作系统、各服务、template-manager 的页缓存抢地方；大页那一大块是给客户机用的。")
    T = y0 + 40
    L, R = M, W - M
    s.rect(L, T, (R - L) * 0.10, 300, HOST[0], HOST[1], 1.4, rx=10)
    s.rect(L + (R - L) * 0.10 + 6, T, (R - L) * 0.90 - 6, 300, GUEST[0], GUEST[1], 1.4, rx=10)
    s.text(L + (R - L) * 0.10 + 26, T + 32, "可做大页的内存：静态池 20%（≤64 GiB）+ 超分配 80%", 15, GUEST[2], 600)
    s.text(L + (R - L) * 0.10 + 26, T + 56, "客户机内存走这里；静态池开机就划出，不管有没有沙箱", 13, SUB)
    xs = L + (R - L) * 0.10 + 26
    for i in range(10):
        s.rect(xs + i * 128, T + 90, 116, 180, "#FFFFFF", GUEST[1], 1.1, rx=8)
        s.text(xs + i * 128 + 58, T + 186, f"沙箱 {i + 1}", 13, GUEST[2], 600, "middle")
    s.text(L + 8, T + 26, "宿主普通内存", 12.5, HOST[2], 600)
    s.text(L + 8, T + 44, "≤ 42 GiB", 12.5, HOST[2], 400)
    # 放大
    ZX = M
    ZY = T + 340
    s.line(L, T + 300, ZX, ZY, HAIR, 1.2, dash="4 4")
    s.line(L + (R - L) * 0.10, T + 300, R, ZY, HAIR, 1.2, dash="4 4")
    parts = [("操作系统", "Nomad、Consul", 0.10, HOST), ("其他服务", "api、client-proxy、Redis、\nPostgreSQL、Harbor 容器", 0.18, HOST),
             ("template-manager", "堆 + 页缓存（≤32 GiB）", 0.27, ORCH), ("/tmp/templates（tmpfs）", "模板、每层、每次暂停的快照\n删除不回收，只增不减", 0.45, RISK)]
    x = ZX
    for t, d, f, role in parts:
        w = (R - ZX) * f
        box(s, x, ZY, w - 8, 120, role, t, d, 14, 12.5)
        x += w
    s.text(ZX, ZY + 150, "放大“宿主普通内存”这一小块：四样东西抢这 ≤42 GiB", 13.5, INK, 600)
    T2 = ZY + 180
    cw = (W - 2 * M - 2 * 24) / 3
    rows = [("估一下 /tmp/templates", "10 个模板 ≈ 28 GiB；再 1000 次暂停，没开写跟踪时每次约 100 MiB 起，近 100 GiB", RISK),
            ("其他上限", "同时运行 512 个沙箱（nbd）；大页超分配看碎片；/orchestrator 缓存 85% 开始淘汰", WHITE),
            ("放开这个限制", "把模板存储搬到硬盘（第 10 篇），定期清理不再被引用的 build", GOOD)]
    for i, (t, d, r) in enumerate(rows):
        box(s, M + i * (cw + 24), T2, cw, 90, r, t, d, 15, 12.5)
    yy = s.footer(T2 + 126, "注：示意比例。/orchestrator 下的缓存、COW、检查点在硬盘上，但刚读写过的部分会进页缓存，记在 template-manager 的 32 GiB 账上。")
    save(s, "19-1-内存账.svg", yy + 20)


def fig_19_layers():
    s = Svg()
    y0 = s.header("存储问题按五层排查：从远到近，逐层排除",
                  "数据从存储后端一路流到客户机。出问题时沿着这条路一层层看，每层都有一两个最能说明问题的地方。")
    T = y0 + 40
    rows = [("① 存储后端", "模板文件在不在？后端到底是什么？", "ls /tmp/templates/<buildID>；findmnt /tmp；\n/proc/<PID>/environ 里的 STORAGE_PROVIDER", STORE),
            ("② 本地缓存", "拉得下来吗？磁盘满了没？", "/orchestrator/build、/orchestrator/template；\ndf -h /orchestrator；du 对比 ls -l", ORCH),
            ("③ 磁盘栈", "有 NBD 设备吗？COW 写得进吗？", "/sys/module/nbd/parameters/nbds_max；\n/sys/block/nbdN/{size,pid}；…/rootfs-<ID>-*.link", MINE),
            ("④ 内存栈", "UFFD 握手了吗？大页够吗？", "ls /tmp/uffd-*.sock；\ngrep HugePages_ /proc/meminfo", GUEST),
            ("⑤ 快照与检查点", "导出、上传、回滚成功了吗？", "日志 source=resident|tracked；\n/orchestrator/build/checkpoint-capabilities.json", RISK)]
    for i, (t, q, where, role) in enumerate(rows):
        y = T + i * 104
        box(s, M, y, 300, 86, role, t, None, 17)
        box(s, M + 320, y, 480, 86, WHITE, q, None, 15)
        box(s, M + 820, y, W - 2 * M - 820, 86, WHITE, None, where, 13, 13, mono_sub=True)
        if i < 4:
            arrow(s, [(M + 150, y + 90), (M + 150, y + 102)], SUB, 1.3)
    yy = s.footer(T + 5 * 104 + 10, "注：常见问题和对应的篇目见第 19 篇的速查表。大多数“模板突然没了”的问题，答案都在第 ① 层：/tmp 是 tmpfs。")
    save(s, "19-2-排障五层.svg", yy + 20)


if __name__ == "__main__":
    for name in sorted(n for n in dir() if n.startswith("fig_")):
        globals()[name]()
