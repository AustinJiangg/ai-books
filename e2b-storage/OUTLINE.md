# 大纲

**读者**：会一点编程、用过命令行，但没系统学过操作系统存储、文件系统和虚拟内存的新手。
**目的**：花几个小时读完，把一套实际在用的 E2B 环境的存储看明白：一个模板由哪些文件组成、存在哪里；一个沙箱运行时它的“硬盘”和“内存”从哪里来；暂停、恢复、回滚时数据怎么存、怎么取；部署脚本为这些准备了什么。概念讲透，只读不练，不安排动手实验。
**写法**：从现实问题出发，先讲“为什么需要”，再讲“是什么”，最后讲“这套环境怎么做、坑在哪”。多用生活类比和文字图，每篇末尾有“本篇小结”表格。
**代码**：只放简短的示例片段，帮助理解，不追求完整可运行，也不需要读者自己核对。片段包括：
- 简化后的 Go 代码；
- `ls`、`du`、`findmnt`、`lsblk` 等命令和示例输出；
- 部署脚本和 nomad job 里的相关几行。

**依据**：以作者实际部署的环境为准，不讲 E2B 官方最新版的新功能。
- 源码：上游 [e2b-dev/infra](https://github.com/e2b-dev/infra) tag `2026.09`，打上 [AustinJiangg/e2b-infra](https://github.com/AustinJiangg/e2b-infra) 里的 ARM 适配补丁 `0001-adapted-for-arm-architecture.patch`。补丁里和存储有关的改动有三类：
  - 新增 MinIO 存储后端，并把默认后端改成 MinIO；
  - 改了 UFFD 换页方式和若干块设备读写细节；
  - 新增整套“快照回滚”（checkpoint / restore）代码，包括 `internal/checkpoint`、`block/layerstack.go`、`fc/rollback.go`、`fc/dirtytracking.go` 等。
- 部署方式：单机鲲鹏 ARM 服务器、openEuler。
  1. 下载仓库。
  2. 按 `e2b-infra.spec` 构建 RPM，安装到 `/opt/e2b-infra`。
  3. 依次执行 `build.sh -d`（停止并清理）、`-i`（安装）、`-s`（启动部署）。

  实际生效的配置是 `e2b-deploy/dep/` 下的 `.env`、`template-manager.hcl`、`init-client.sh`、`start-client.sh`，以及 RPM 装进去的那份二进制。

本书自成一体，不依赖本仓库其他书。网络相关内容只在用到时一句带过，详见《E2B 沙箱网络从零讲透》。

**规模**：19 篇，每篇约 3000～3800 个汉字，合计约 6.5 万汉字（连同代码、命令和英文约 15 万字符）。

**贯穿全书的几个事实**，正文会反复回到这里：

| 事实 | 出处 |
|---|---|
| orchestrator 和 template-manager 是同一个进程（`ORCHESTRATOR_SERVICES=orchestrator,template-manager`），既跑沙箱也建模板 | `dep/template-manager.hcl` |
| 模板的持久化存储实际是 `Local`，落在 `/tmp/templates`；`.env` 里写的 `MinioBucket` 没有生效 | `dep/template-manager.hcl` 写死 `STORAGE_PROVIDER = "Local"` |
| openEuler 的 `/tmp` 是 tmpfs，所以模板实际放在内存里，宿主重启就丢 | 系统自带的 `tmp.mount` |
| MinIO 由 `build.sh -i` 装好并通过了健康检查，但没有建桶，也没有组件往里写 | `build.sh` 的 `install_minio` |
| 每个运行中的沙箱占一个 `/dev/nbdN`，自编译的 nbd 模块 `nbds_max=512`，这就是单机并发上限之一 | `single-node-offline-deploy.md` 0.2 |
| 客户机内存走 2 MiB 大页（hugetlbfs），开机时静态池取 20%（上限 `HUGEPAGES_BASE_MAX_MIB=65536`），其余 80% 按需超分配 | `init-client.sh` |

## 第一部分　打地基：够用的存储知识

### 第 1 篇　从“毫秒开一台虚拟机”说起：E2B 的存储要解决什么问题

- 一个场景：SDK 调用 `Sandbox.create()`，一百多毫秒后拿到一台装好 Python、已经启动完毕的 Linux 虚拟机。
  - 这台机器的“硬盘”有好几个 GB，“内存”有好几百 MB，它们是什么时候准备好的？
  - 答案：不是现装的，而是从“模板”恢复出来的；而且不是整份拷贝，是“用到哪页才取哪页”。
- 一台虚拟机有两样东西要存：
  - 磁盘：根文件系统，一个 ext4 镜像。
  - 内存：客户机的全部 RAM。快照时还要加上 CPU 和设备状态。
- E2B 存储的几个设计目标：
  - 秒级甚至毫秒级启动：不能先下载、解压几个 GB 再开机。
  - 一台机器跑几百个沙箱：同一个模板的数据只存一份，各沙箱只存自己改过的部分。
  - 能暂停、能恢复：暂停时只存改动，不存整机。
  - 能回滚：沙箱里的 AI 搞坏了环境，可以退回到之前的某个检查点。
- 一个沙箱的存储一生，五个阶段，正好对应本书五个部分：
  1. 模板构建：Dockerfile 变成 `rootfs.ext4` 和内存快照。
  2. 模板存放：存储后端。
  3. 沙箱运行：NBD 加写时复制的磁盘，UFFD 按需供页的内存。
  4. 暂停与恢复：增量快照。
  5. 回滚：检查点。
- 本书讲的这套环境里，和存储相关的组件与目录（全景图）：
  - 进程：template-manager 一个进程身兼 orchestrator 和模板构建两个角色。它下面是 Firecracker。
  - 持久化目录：`/tmp/templates`、`/tmp/build-cache`。
  - 本地缓存目录：`/orchestrator/{build,template,sandbox}`。
  - tmpfs：`/mnt/snapshot-cache`（65G）。
  - hugetlbfs：`/mnt/hugepages`。
  - 设备：`/dev/nbd0`～`/dev/nbd511`。
  - 运行环境文件：`/fc-kernels`、`/fc-versions`、`/fc-envd`。
  - 镜像仓库 Harbor：模板的“原料”Docker 镜像存在这里（第 8 篇）。
  - 存“数据的数据”的地方：PostgreSQL 存模板和 build 记录，Redis 存运行中沙箱的目录。这些在第 9 篇和第 18 篇简单提一下。
  - 装了但没用上的 MinIO（第 10 篇解释）。
- 本书路线图：每一部分负责全景图上的哪一块。

### 第 2 篇　存储基础（一）：字节、块、页与文件系统

- 硬盘眼里只有“第几块”：扇区与块，为什么读写总是以 4 KiB 为单位。
- 内存眼里只有“第几页”：4 KiB 的普通页，2 MiB 的大页。
  - 本书会反复用到两个数：块大小 4 KiB（`RootfsBlockSize`），大页 2 MiB（`HugepageSize`）。
- 文件系统做了什么：把一堆“块”组织成有名字、有目录的“文件”，用图书馆的书架和索引卡来类比。
  - ext4 的基本概念：超级块、inode、块组。只讲到能看懂 `tune2fs -l` 和 `e2fsck` 在检查什么。
- 文件就是一串字节；一个文件也可以被当成一块“硬盘”来用。镜像文件 `rootfs.ext4` 就是这样一块装在文件里的盘。
- 稀疏文件：文件“看起来”有 10 GB，实际只占用写过的那部分。`ls -l` 和 `du` 为什么对不上。
  - 后面的 diff 文件、COW 文件、检查点文件都是稀疏文件。
- 页缓存：读过的文件内容会留在内存里，这对“谁占了内存”的判断有什么影响（第 18 篇的 memcg 上限要用）。
- tmpfs：放在内存里的文件系统。`/tmp`、`/mnt/snapshot-cache` 都是它，重启即空。

### 第 3 篇　存储基础（二）：块设备与 NBD

- 什么是块设备：`/dev/sda`、`/dev/nvme0n1`，以及内核里的块设备层。
- 用户态也能“造”一块盘：
  - loop 设备：把文件当盘。
  - NBD（Network Block Device）：盘的每一次读写都变成发给一个程序的请求，程序怎么回答，盘里就是什么内容。
  - 类比：一个“假硬盘”，背后其实是一位接线员在实时查资料作答。
- NBD 协议的骨架：请求包（读、写、刷盘、断开）、应答包、句柄号。
  - 用文字图画出“内核 → socket → 用户态程序 → 应答”的往返。
- 为什么 E2B 要用 NBD，而不是直接把文件交给虚拟机：
  - 磁盘内容并不在一个本地文件里，而是散在好几代 diff 和远端存储里。
  - 需要在“读的那一刻”决定去哪里取数据，在“写的那一刻”把数据记到沙箱自己的地方。
- NBD 设备是有数量上限的内核资源：
  - 模块参数 `nbds_max`。
  - 这套环境自己编译了 nbd 模块，固化为开机加载、`nbds_max=512`。
- udev 与 NBD：为什么部署脚本要给 `nbd*` 加 `OPTIONS:="nowatch"`，以及为什么只对 nbd 设备触发 `udevadm trigger`。
- 读懂几条命令的输出：`lsblk`、`ls /dev/nbd* | wc -l`、`cat /sys/module/nbd/parameters/nbds_max`。

### 第 4 篇　存储基础（三）：虚拟内存、mmap、缺页与 userfaultfd

- 虚拟地址与物理内存：每个进程以为自己独占一大片内存，实际由页表按页映射。
- 缺页：访问一个还没准备好的页时，CPU 停下来让内核补上。这是“按需加载”的基础。
- mmap：把文件“贴”到内存地址上，读内存就是读文件。
  - `MAP_SHARED` 与 `MAP_PRIVATE` 的区别。
  - E2B 的本地缓存文件都是 mmap 出来用的。
- 大页与 hugetlbfs：一次映射 2 MiB，少很多页表项；要预先留出大页池；`nr_hugepages` 和 `nr_overcommit_hugepages`。
- userfaultfd（UFFD）：把缺页交给用户态程序处理。
  - MISSING 事件：页还不存在。
  - `UFFDIO_COPY`：程序把数据填进去。
  - 写保护（WP）：页在，但写它时要通知我。
  - 类比：仓库按订单现取货；货架上加封条，有人动就报告。
- `/proc/<pid>/pagemap`：内核告诉你每一页是否在内存里、是否带写保护位（第 15 篇要用）。
- `process_vm_readv`：直接读另一个进程的内存，不经过文件（第 14 篇要用）。
- 脏页：被写过的页。“记下哪些页脏了”有三种办法，本书都会遇到：
  - UFFD 写保护位；
  - KVM 脏页日志；
  - ARM 的硬件脏状态跟踪（HDBSS）。

### 第 5 篇　写时复制与分层：只存改动的思想

- 问题：一百个沙箱都基于同一个 5 GB 的模板，难道要拷一百份？
- 写时复制（COW）：读时共享，写时才复制到自己那份。用“共享课本，各自在便签上做笔记”来类比。
- 分层：
  - Docker 镜像层（OCI 层）：只读的下层加一个可写的上层。
  - E2B 的 build 链：每次暂停或快照产生一层 diff，只含这一轮改过的块或页。
- 两种组织多层数据的方式：
  - 链表式：逐层往下找，层越多越慢。
  - 拍平的映射表：查一次表就知道这一块在哪一层的哪个偏移。E2B 的 header 就是这种（第 7 篇）。
- 拍平的代价：被引用到的每一层都必须留着；删中间一层会打断后代。
- 压实（compaction）：把层合并起来，免得越叠越多（第 17 篇）。
- 小结：本书后面几乎所有设计，都是“共享不变的部分，只存改过的部分，再用一张表把它们拼起来”。

### 第 6 篇　虚拟机的“盘”和“内存条”：Firecracker 眼中的存储

- Firecracker 给客户机提供的存储设备：
  - virtio-blk 根盘，宿主那头指向一个路径。在 E2B 里这个路径是 `/dev/nbdN`。
  - 客户机内存，由宿主的一块内存区域支撑：普通匿名内存，或者 hugetlbfs 大页。
- 内核和启动参数从哪来：`/fc-kernels/<版本>/vmlinux.bin`、`/fc-versions/<版本>/firecracker`。
  - 本环境 RPM 自带定制版 `firecracker` 和两份内核：通用 arm 内核，以及 openEuler 内核 `vmlinux-6.6.0-132.0.0`。
- 原生快照的三个产物，以及它们的局限：
  - `snapshot_path`：vmstate，CPU 寄存器和设备状态。
  - `mem_file_path`：整份内存。
  - Full 与 Diff 两种快照，Diff 需要 KVM 脏页日志，还得自己合并。
- 原生恢复的两种内存后端：
  - File：整份 mmap。
  - Uffd：Firecracker 把 UFFD 交给外部程序，缺页由外部程序供页。
- E2B 用的定制 Firecracker 多了几样东西：
  - 创建快照时不传 `mem_file_path`，Firecracker 只写 vmstate，不导出内存。
  - `GET /memory/dirty`：脏页位图。
  - `GET /memory/mappings`：客户机页到宿主虚拟地址的映射。
  - 回滚接口（第 16 篇）。
- 一张图：Firecracker 进程、`/dev/nbdN`、UFFD socket、大页内存、orchestrator 之间的关系。后面第 11～13 篇逐块展开。

## 第二部分　模板：沙箱的“出生证”

### 第 7 篇　模板长什么样：一个 buildID 目录里的六个文件

- template、build、buildID：
  - 一个模板可以有很多次 build。
  - 每次暂停或快照也会产生一个新的 build。
  - SDK 返回的快照 ID（`templateID:tag`）不是 buildID。
- 六个文件逐个讲：
  - `snapfile`：Firecracker 的 vmstate。
  - `memfile`：内存数据。可能只是 diff。
  - `memfile.header`：内存的映射表。
  - `rootfs.ext4`：磁盘数据。可能只是 diff。
  - `rootfs.ext4.header`：磁盘的映射表。
  - `metadata.json`：内核版本、Firecracker 版本、envd 版本、启动命令等。
- header 的结构：
  - 元数据：版本、块大小、总大小、代数（generation）、本代 buildID、基底 buildID。
  - 映射数组 `BuildMap`：偏移、长度、数据实际在哪个 build、在那个文件里的偏移。
- 全零块：映射到 `uuid.Nil`，读的时候直接给零，不占存储。
- 举例：一个模板，加两次暂停，得到三代 header 和三个 diff；手工“查表”读出第 N 块。
- 新旧格式：为什么代码里还留着 `oldMemfileHugePageSize`、`oldRootfsBlockSize`。
- 持久化存储里的键名与本地路径一一对应，见第 10 篇。

### 第 8 篇　模板的原料仓库：Harbor 与镜像的存放

- 问题：模板的第一行是 `FROM harbor:443/e2b-orchestration/ubuntu:22.04-custom`。这个镜像存在哪，template-manager 又是怎么拿到它的？
- 镜像仓库（registry）是什么：一个按“仓库名:标签”存取镜像的 HTTP 服务。用“仓库管理员按货号收发货”来类比。
- OCI 镜像在仓库里怎么存：
  - 清单（manifest）：这个镜像由哪几层组成，平台是什么。
  - 配置（config）：环境变量、工作目录、启动命令。
  - 层（layer）：一个个 tar.gz，按内容的 sha256 命名，相同的层只存一份。
  - 多平台镜像的索引：为什么补丁把拉取平台固定为 `linux/arm64`，拉到 x86 镜像会直接报错。
- Harbor 是什么：在 Docker 官方 registry 外面加了项目、用户、网页界面的“仓库管理系统”，自己由一组容器组成。
- 这套环境怎么装 Harbor：
  - `-i`：解压社区构建的 aarch64 离线包 `harbor-offline-installer-aarch64-v2.13.0.tgz`，改 `harbor.yml`：注释掉 https，`hostname` 改成本机 IP，HTTP 端口改成 2900。
  - `-i` 还装了 nginx：`server_name harbor`、`listen 443 ssl`，反代到 `127.0.0.1:2900`；生成自签证书，装进系统信任库和 `/etc/docker/certs.d/harbor:443/`。
  - `-s`：执行 Harbor 的 `install.sh` 拉起容器，修正配置目录属主（容器内 UID 10000），`docker login`，用 REST API 建公开项目 `e2b-orchestration`。
  - `-s`：`ensure_harbor_hostname` 往 `/etc/hosts` 写 `<本机IP> harbor` 并重启 dnsmasq。
  - `-s`：`push_base_image` 把 `dep/ubuntu-22.04-custom.tar.gz` 先 `docker load`，再推成 `e2b-orchestration/ubuntu:22.04-custom`；已有就跳过。
- 为什么有两个地址：
  - 推送走 `<本机IP>:2900`（HTTP，`daemon.json` 的 `insecure-registries`），避开 docker daemon 代理设置对 `harbor` 这个名字的误转发。
  - 拉取走 `harbor:443`（HTTPS，nginx 反代）。
  - 两个地址背后是同一个仓库。
- template-manager 怎么拉镜像：
  - 不经过本机 docker daemon，而是用 Go 的 go-containerregistry 直接按 registry 协议拉（`GetPublicImage`）。
  - 名字 `harbor` 靠 dnsmasq 读 `/etc/hosts` 解析；证书靠系统信任库，以及 hcl 里的 `SSL_CERT_FILE`。
  - 拉下来的层在第 9 篇被解包、转成 ext4。
- `ARTIFACTS_REGISTRY_PROVIDER=Local`：另一条“从 build 记录取镜像”的路径，读的是本机 docker daemon 里的 `templateID:buildID`。本环境建模板走的是 `FROM` 指定的公开路径。
- 镜像本身存在哪：Harbor 的数据目录（安装包默认 `/data`）。和模板文件、MinIO 是三处互不相干的存储。
- 常见问题：
  - `lookup harbor ... server misbehaving`：主机名没解析。
  - 推送 504：请求被转给了代理。
  - `docker-compose` 版本太老，解析不了 Harbor 2.13 的 compose 文件。
  - 拉取报平台不匹配。

### 第 9 篇　从 Dockerfile 到 rootfs.ext4：模板构建流水线

- 入口：
  - 宿主上用 SDK（本环境由 `build.sh -i` 打了补丁：`patch_e2b.py`、`dockerfile_parser.py`、`build_api.py`），或 `benchmark/build_template.py`。
  - 请求到 api，再到 template-manager。
- 镜像从哪来：本机 Harbor（第 8 篇）。
- 九个步骤，围绕“磁盘文件怎么一步步变出来”讲：
  1. 拉镜像。
  2. 注入文件：envd、busybox init、hostname、DNS 配置、`provision.sh`。
  3. 解包并转成 ext4（`oci.ToExt4`）。
  4. 扩容到 `DiskSizeMB`，用 `tune2fs`、`e2fsck` 检查完整性。
  5. 用 BusyBox init 启动一次，只跑 provision 脚本，装 systemd。
  6. 用 systemd 正式启动，等 envd 就绪。
  7. 逐条执行模板步骤（RUN、COPY 等），每一步都可以缓存成层。
  8. 跑 configure 脚本和启动命令。
  9. 打快照，上传。
- 层缓存：
  - 每一步按内容算哈希，命中就直接复用上次的结果。
  - 缓存落在构建缓存存储里。本环境是 `/tmp/build-cache`。
- ARM 补丁在这条流水线上改了什么：
  - 换成 glibc 版 busybox（`busybox_1.35_arm64`，RPM 构建时拷进 `systeminit/`）。
  - `provision.sh`、`configure.sh` 的适配。
  - 构建时启动 Firecracker 仍走原来的 `ip netns exec` 路径（网络书第 9 篇）。
- 构建时的磁盘不走 NBD，而是 Direct 方式：为什么构建和运行要用两种方式（第 12 篇对照）。
- 构建产物的第一份内存快照：不是从模板恢复的，所以内存走 NoopMemory，并做全零页剔除（第 13 篇）。

### 第 10 篇　模板存到哪：存储后端、Local 与“装了没用”的 MinIO

- 存储后端的抽象 `StorageProvider`：
  - 两种对象：整块读写的 Blob（header、snapfile、metadata），可以随机读的 Seekable（memfile、rootfs）。
  - 四个实现：GCP、AWS、Local、MinIO（MinIO 由 ARM 补丁新增，并改成默认）。
- 两个入口，各建一个后端：
  - 模板与快照：`GetTemplateStorageProvider`，桶名 `TEMPLATE_BUCKET_NAME`。
  - 构建层缓存：`GetBuildCacheStorageProvider`，桶名 `BUILD_CACHE_BUCKET_NAME`。
- 键名：`<buildID>/memfile` 等，在所有后端下都一样。
- 本环境真正生效的是什么：一条四步的链路。
  1. RPM 装进去的 `nomad/template-manager.hcl` 写的是 `${STORAGE_PROVIDER}`。
  2. `build.sh -s` 用 `dep/template-manager.hcl` 覆盖它，那份里写死了 `"Local"`。
  3. `deploy.sh` 用 `envsubst` 渲染，字面量原样保留。
  4. 只提交 redis、template-manager、edge、api 四个 job；带 `${STORAGE_PROVIDER}` 的 orchestrator job 从不提交。
- 结果：
  - 模板在 `/tmp/templates/<buildID>/`，构建缓存在 `/tmp/build-cache`。
  - `/tmp` 是 tmpfs，模板占的是内存。
  - 宿主重启后模板全部丢失；不重启时，`systemd-tmpfiles` 也会清掉 10 天没碰过的文件。
- MinIO：
  - `build.sh -i` 装在 `/root/data/minio`，端口 9000 和 9001，健康检查通过。
  - 但没有建桶，也没有组件往里写。Loki 用本地文件系统，ClickHouse 备份桶为空。
  - 补丁实现的两个细节：`useSSL` 写死为 false；不会自动建桶。
- 想让模板“不丢”的两条路（只讲思路和要改的位置，不展开操作）：
  - 把 `LOCAL_TEMPLATE_STORAGE_BASE_PATH` 指到持久盘。
  - 真正切到 MinIO：建桶，改源头的 hcl，迁移数据。
  - 两条路都要改 `dep/` 里的源头文件，否则下次 `-s` 又被覆盖回去。
- api 根本不碰存储：删模板、删快照是 api 让 template-manager 去执行 `DeleteObjectsWithPrefix`。

## 第三部分　一个沙箱的存储栈

### 第 11 篇　节点本地缓存：`/orchestrator` 目录里都是什么

- 为什么持久化存储之外还要一层本地缓存：远端（或者哪怕是本地 tmpfs）的对象不能直接给虚拟机当盘、当内存用，需要一个可以 mmap、可以随机读的本地文件。
- 三个目录与一个 tmpfs：

  | 路径 | 放什么 | 生命周期 |
  |---|---|---|
  | `/orchestrator/template/<buildID>/cache/<uuid>/` | snapfile、metadata.json | 缓存项过期或关闭时删 |
  | `/orchestrator/build/<buildID>-memfile-<rand>`、`<buildID>-rootfs.ext4-<rand>` | memfile、rootfs 的本地副本 | TTL 25 小时加容量驱逐；进程启动时整目录清空 |
  | `/orchestrator/sandbox/` | 运行中沙箱的 COW 文件 | 沙箱销毁即删 |
  | `/mnt/snapshot-cache` | 快照中间产物，tmpfs 65G | 重启即空 |

- 文件名里的随机后缀是干什么的：防止旧缓存项关闭时删掉新缓存项的文件。
- 分块拉取（chunker）：
  - 不是一次把 memfile 拉全，而是按 4 MiB 一块（`MemoryChunkSize`）用到才拉。
  - 拉过的块记在位图里，拉过的数据写进 mmap 的本地缓存文件。
  - 两种拉取器：整块拉取（FullFetch）和流式拉取（Streaming，读到想要的字节就先返回）。
- 一次读的完整路径：
  1. 按偏移查 header，得到 buildID 和偏移。
  2. 找到那个 build 的本地缓存。
  3. 块没拉过就去存储后端拉。
  4. 从 mmap 里切出数据。
- 本环境里“远端”其实就在本机 tmpfs 上，所以拉取很快；但缓存这一层依然存在，同一份数据会在内存里出现两次（第 19 篇算账）。
- `SHARED_CHUNK_CACHE_PATH`（共享的 NFS 块缓存）：本环境为空，所以没有启用。
- 常见误判：在 `/orchestrator/build` 看到大文件，不代表模板存在这里，也不代表泄漏。

### 第 12 篇　沙箱的硬盘：NBD 加写时复制

- 运行中的沙箱，磁盘由两层拼成：
  - 下层：模板的 rootfs，只读，经第 11 篇的缓存按需读取。
  - 上层：沙箱自己的 COW 文件 `/orchestrator/sandbox/rootfs-<沙箱ID>-<rand>.cow`，稀疏文件，只记写过的块。
- overlay 的读写规则：
  - 写一定落到上层，并在位图里记下“这一块是我的”。
  - 读先看上层，没有再去下层。
- 怎么把这两层交给 Firecracker：
  1. 从 NBD 设备池里取一个空闲的 `/dev/nbdN`。
  2. 起一个用户态 NBD 服务，用 socket 接上这台设备。
  3. 把路径交给 Firecracker 当根盘。
  4. 客户机的每次读写变成 NBD 请求，由 orchestrator 里的 dispatch 循环回答。
- NBD 设备池：
  - 怎么判断一台设备空闲。
  - 取不到设备时报什么错。
  - 释放时设备还被占用怎么办。
  - `nbds_max=512`：同时运行的沙箱最多 512 个；模块没加载时 orchestrator 启动就报 `NBD module not loaded`。
- Direct 方式：模板构建时不用 NBD，直接用本地文件当盘，因为构建需要把所有块都标成脏、最后整份导出。
- ARM 补丁对这一层的改动（只讲作用，不读代码）：
  - `LayerStack`：用一个每块一个 `uint16` 的索引数组代替逐层查找，为回滚的多层磁盘做准备（第 17 篇）。
  - `BlockSet`：用原子位图代替 `sync.Map` 记录“哪些块在这一层”。
  - `populate`：拷贝前用 `MADV_POPULATE_READ/WRITE` 先把页面调进来，避免 Go 协程在缺页时长时间占着调度器。
  - 写缓存时加了越界检查和 SIGBUS 兜底。
- 一张文字图：客户机 ext4、virtio-blk、`/dev/nbdN`、NBD socket、overlay、COW 文件和模板缓存，逐层标出。

### 第 13 篇　沙箱的内存：UFFD 按需供页与大页

- 问题：模板的内存有几百 MB 到几 GB，恢复时不可能先全部读进来。
- UFFD 内存后端的工作方式：
  1. Firecracker 恢复快照时，按 Uffd 后端建好 userfaultfd，通过 unix socket 把句柄交给 orchestrator。
  2. 客户机第一次访问某一页，触发缺页，内核通知 orchestrator。
  3. orchestrator 按 memfile header 查到数据在哪，用 `UFFDIO_COPY` 填进去。
  4. 客户机继续运行，完全不知道刚才发生过什么。
- 预取（prefetch）：
  - 模板构建时记下启动过程用到了哪些页（预取映射），恢复时后台先拉取、等 UFFD 就绪后提前填进去。
  - 好处是少等；第 15 篇会看到，在 ARM 上它的副作用是快照变大。
- NoopMemory：没有快照可恢复的时候（模板构建时第一次开机），内存由 Firecracker 自己的文件支撑，不走 UFFD。
- 大页：
  - 客户机内存用 2 MiB 大页，页表更小，缺页次数少 512 倍；代价是每次缺页要拷 2 MiB。
  - 部署脚本怎么预留大页：
    - 先给宿主留够普通内存。
    - 剩下的 20% 做静态池，上限 `HUGEPAGES_BASE_MAX_MIB`（64 GiB），开机就占住、不归还。
    - 另外 80% 做超分配，按需分配，用完归还。
    - 补丁把写入路径改成显式的 `hugepages-2048kB`，因为 ARM 的默认大页大小不一定是 2 MiB。
  - 挂载点 `/mnt/hugepages`；停服后静态池不会自动释放，要用 `build.sh --purge-hugepages`。
  - 为什么客户机内存不计入 Nomad 的内存上限：hugetlb 不记在 memory 控制器里（第 18 篇）。
- ARM 补丁在这一层的改动：
  - 等待 UFFD socket 的超时从 10 秒放宽到 120 秒，因为 ARM 上 Firecracker 起得慢。
  - 去掉了 `UFFDIO_COPY_MODE_WP`（第 15 篇专门讲后果）。
- 小结：沙箱的“内存”其实是一层层的：客户机页，大页池，UFFD 处理程序，memfile 本地缓存，持久化存储。

## 第四部分　快照：暂停、恢复与回滚

### 第 14 篇　暂停与恢复：一次增量快照是怎么做出来的

- 暂停（pause）对用户的意义：沙箱不再占 CPU 和内存，之后可以按同一个 ID 恢复。
- 打快照的八个步骤，每一步回答“为什么这样做”：
  1. 暂停虚拟机。
  2. 创建快照，只写 vmstate，并把磁盘缓冲刷下去。
  3. 取脏页位图（`GET /memory/dirty`）。
  4. 如果是第一次快照（NoopMemory），改取常驻页和全零页位图。
  5. 取地址映射（`GET /memory/mappings`），用 `process_vm_readv` 直接从 Firecracker 进程里把脏页拷进本地 diff 文件。
  6. 磁盘：把 overlay 的 COW 文件“弹出”作为 rootfs diff。
  7. 用“上一代 header 加本次 diff”合成新 header，合并映射并规整。
  8. 上传六个文件：本环境是写进 `/tmp/templates/<新buildID>/`。
- 为什么内存不让 Firecracker 自己写文件：少一跳，而且天然只导出脏页。
- 恢复（resume）：就是“用新 build 创建沙箱”。
  - 沙箱 ID 不变，但 Firecracker 进程、NBD 设备、UFFD 都是新的。
  - 内存和磁盘按新 header 从各代 diff 里按需取。
- 快照链和删除：
  - 删一个快照为什么要走 API。
  - 手工删 `/tmp/templates` 里的目录会打断哪些后代。
- 中间文件在哪：`/orchestrator/build` 和 `/mnt/snapshot-cache` 各放了什么。

### 第 15 篇　ARM 上的增量为什么“偏大”：脏页判据与实测

- 回顾 x86 上的精确增量：
  - 读缺页时带写保护位填页，写缺页时不带。
  - 定制 Firecracker 按 pagemap 判断：页在内存里且写保护位已清，才算脏。
  - 所以只读过的页不算脏。
- ARM 补丁注释掉了 `UFFDIO_COPY_MODE_WP`，后果是一条链：
  1. 换入的页都不带写保护位。
  2. “在内存里且不带写保护位”恒为真。
  3. 这一轮被换入过的页（读过的也算）全部计入脏页。
  4. 内存增量成了真实脏页的超集。
- 几个推论：
  - 只读操作也会产生内存增量。
  - 预取多少页，增量就多多少页。
  - 磁盘增量不受影响，依然精确，因为它来自 COW 文件。
  - 正确性不受影响，只多花空间和时间。
- 实测（引用部署文档 09 的数据，不要求读者复现）：三组对照（空闲、只读、写入），各自的 memfile 和 rootfs diff 大小与耗时，逐条解读。
- 另一条路：硬件或 KVM 记录脏页。
  - 补丁新增的 `dirtytracking.go` 检测 arm64 KVM 的硬件脏状态跟踪能力（HDBSS），由 `FC_TRACK_DIRTY_PAGES` 强制开关。
  - 打开后 Firecracker 维护“写过的页”位图。
  - 这条路主要服务于回滚（第 16 篇）。
- 对使用者的建议：暂停和快照的体积怎么估；为什么 ARM 上不要盲目调大预取。

### 第 16 篇　快照回滚（一）：检查点树与内存

- 问题：AI 在沙箱里跑了十步，第七步把环境搞坏了，想回到第六步之后的状态，而且要快、不换进程、不丢沙箱 ID。
- 暂停与恢复、模板快照、回滚三者的区别：
  - 存在哪：持久化存储，还是本机。
  - 活多久：跨进程，还是随 Firecracker 进程。
  - 恢复方式：新开 Firecracker，还是原地倒回。
- 入口：沙箱内访问检查点端口 49984，由宿主上的 checkpoint 服务应答（网络细节一句带过）。
- 检查点树：
  - 每个沙箱一棵树；回滚到某个点之后再打检查点，就长出一条新分支。
  - 删除还有后代的节点时，只把它隐藏，不打断后代。
- 一个检查点存了什么：
  - 这一段时间（epoch）写过的页：一个稀疏 diff 文件，加一个位图边车文件（FCDB 格式，和定制 Firecracker 共用）。
  - 根检查点：默认（`CHECKPOINT_FULL_ROOT` 不设或为 true）第一次存整份内存；设为 false 时，根落到模板的 memfile。
  - 没有脏页跟踪，或者链断了，就做一次全量，开一棵新的子树。
- 脏页从哪来：
  - Firecracker 的写跟踪位图每次检查点后清零。
  - 补丁用 `DirtySinceBoot` 把每次清零前的位图并起来，避免漏页。代码注释里的原话是：导出多了只是慢，导出少了就是静默的数据损坏。
- 回滚怎么做：
  1. 算出“需要还原的页集合”。
  2. 沿目标检查点的祖先链逐页找到内容。
  3. 让定制 Firecracker 原地回滚内存和 vCPU 状态。
  4. 不在磁盘上重新拼出整份镜像。
- 文件放在哪：`/orchestrator/build/checkpoints/`。
  - 账本只在进程内存里，目录里的 manifest 只给人看。
  - 进程重启就没了。
  - 暂停或恢复会换一个“代”（generation），旧检查点作废。

### 第 17 篇　快照回滚（二）：磁盘层、压实与配额

- 磁盘怎么跟着回滚：
  - 打检查点时把当前写层“封存”（Seal）成只读层文件，换一个新的空写层。
  - 封存要在虚拟机暂停、NBD 刷完之后做，而且要尽量快。
  - 回滚时把磁盘视图（view）换成目标检查点那一摞层（ResetView）。
- LayerStack：
  - 一摞只读层加一个写层。
  - 每块一个 `uint16` 的索引记录“这一块的主人在哪一层”，读的时候一次查数组就到。
  - 代价：每 GiB 根盘、每个视图 512 KiB。
- 层的引用计数：
  - 谁在用一个层：活着的磁盘栈，以及列着它的检查点。
  - 没人用了才删文件。
  - “中毒”（poison）：账本对不上时，拒绝再记录新的视图。
- 压实（compaction）：
  - 隐藏的检查点如果只剩一个孩子，就把它并进孩子。
  - 内存这半：合并稀疏 diff 和位图。
  - 磁盘这半：把相邻两层合成一层，并改写引用它们的 header。
  - 开关 `CHECKPOINT_COMPACT`，每次最多并几个 `CHECKPOINT_COMPACT_MAX_PER_OP`。
- 配额：
  - 每个沙箱最多几个检查点（`CHECKPOINT_MAX_PER_SANDBOX`）。
  - 最多占多少字节（`CHECKPOINT_MAX_BYTES_PER_SANDBOX`）。
  - 磁盘至少留多少空间（`CHECKPOINT_MIN_FREE_BYTES`）。
  - 超了怎么办：删最老的，或者回滚到更早的点。
- 回滚之后，网络连接要配合清 conntrack（一句带过，见网络书第 20 篇）。
- 节点能力自报：启动时把“这台机器的检查点栈能做什么”写进日志和一个文件，排障时先看它。
- 一张对照表：模板快照、暂停与恢复、检查点回滚，在存什么、存哪、多快、活多久上的区别。

## 第五部分　部署、容量与排障

### 第 18 篇　部署里的存储配置：RPM、`build.sh -d`、`-i`、`-s`

- RPM 阶段放了哪些和存储有关的东西，安装到 `/opt/e2b-infra`：
  - `bin/` 下的 orchestrator、envd、`vmlinux.bin`、`vmlinux.bin.openeuler`、`firecracker`。
  - 构建时拷进源码树的 busybox。
  - `dep/` 部署包，含 `.env`、`template-manager.hcl`、`init-client.sh`、`start-client.sh`、MinIO 文件。
- `-i`（安装）对存储做了什么：
  - 安装 MinIO：二进制、`/etc/default/minio.yml`、systemd 服务、数据目录 `/root/data/minio`。
  - 给 SDK 打补丁，用于模板构建。
- `-s`（启动部署）对存储做了什么，按执行顺序：
  1. 把 orchestrator 二进制拷成 `/usr/bin/orchestrator` 和 `/usr/bin/template-manager`（同一个二进制）。
  2. 建 `/orchestrator/{sandbox,template,build}`。
  3. 挂 `/mnt/snapshot-cache`（tmpfs，65G，脚本做了幂等判断）。
  4. 写 nbd 的 udev 规则并只对 nbd 触发。
  5. 建 `/fc-vm`。
  6. 放 envd 到 `/fc-envd`，内核到 `/fc-kernels/<版本>/`，Firecracker 到 `/fc-versions/`。
  7. 预留大页，挂 `/mnt/hugepages`。
  8. 用 `dep/template-manager.hcl` 覆盖 nomad job，渲染并提交。
- 前置条件：nbd 模块要一次性固化到系统模块目录，部署脚本不会替你加载；升级内核会让固化悄悄失效。
- `template-manager.hcl` 里和存储有关的几行：
  - `STORAGE_PROVIDER = "Local"`。
  - 渲染进去但用不上的 `MINIO_*` 和桶名。
  - `SHARED_CHUNK_CACHE_PATH` 为空。
  - 内存上限 32 GiB：记账的是 orchestrator 堆和构建、快照产生的页缓存，不是客户机内存。太小会被 OOM 杀掉（Exit 137），太大会调度不上。
- `-d`（停止）对存储做了什么、没做什么：
  - 停服务。
  - 大页静态池不随服务释放，提示用 `--purge-hugepages`。
  - `/tmp/templates` 不动。
  - `/orchestrator/build` 下次启动时被清空。
- 配置项总表，每项说明默认值、本环境的值、作用、改了影响全景图哪一块：
  - 存储后端：`STORAGE_PROVIDER`、`LOCAL_TEMPLATE_STORAGE_BASE_PATH`、`LOCAL_BUILD_CACHE_STORAGE_BASE_PATH`、`TEMPLATE_BUCKET_NAME`、`BUILD_CACHE_BUCKET_NAME`、`MINIO_*`。
  - 本地目录：`ORCHESTRATOR_BASE_PATH`、`DEFAULT_CACHE_DIR`、`TEMPLATE_CACHE_DIR`、`SANDBOX_CACHE_DIR`、`SNAPSHOT_CACHE_DIR`、`SANDBOX_DIR`、`SHARED_CHUNK_CACHE_PATH`。
  - 运行环境：`HOST_KERNELS_DIR`、`FIRECRACKER_VERSIONS_DIR`、`HOST_ENVD_PATH`。
  - 大页：`HUGEPAGES_BASE_MAX_MIB`。
  - 回滚：`CHECKPOINT_*`、`FC_TRACK_DIRTY_PAGES`。
  - 内核参数：`nbds_max`。
- 改这些配置时的注意事项：要改 `dep/` 里的源头；改完只需 `build.sh -r template-manager`；已经运行的沙箱怎么办。

### 第 19 篇　全景、容量规划与排障

- 一次完整生命周期的复盘，把前 17 篇串起来，每一步写出数据在哪、谁在读写：
  1. 构建模板。
  2. 创建沙箱。
  3. 在沙箱里装包、写文件。
  4. 打两个检查点，回滚一次。
  5. 暂停。
  6. 恢复。
  7. 删除。
- 容量账，这套环境的特点是“很多存储其实是内存”：
  - `/tmp/templates`：tmpfs，占内存。
  - `/mnt/snapshot-cache`：tmpfs，上限 65G。
  - 大页池：静态池加超分配。
  - `/orchestrator/build` 的本地缓存：真盘，但会进页缓存，计入 template-manager 的 32 GiB 上限。
  - 每个沙箱的 COW 文件和检查点文件。
  - 512 个 NBD 设备。
  - 怎么估“这台机器能放多少模板、跑多少沙箱、存多少快照”。
- 排查思路，按层定位：存储后端 → 本地缓存 → NBD 与 overlay → UFFD 与大页 → 快照或检查点。
- 常用工具，只介绍看什么、怎么读输出：
  - `findmnt /tmp`、`df`、`du -sh` 与 `ls -l` 对比稀疏文件。
  - `lsblk`、`/sys/module/nbd/parameters/nbds_max`。
  - `/proc/meminfo` 的 `HugePages_*` 和 `Hugetlb`。
  - 从 `/proc/<pid>/environ` 确认 `STORAGE_PROVIDER`。
  - 检查点的能力文件。
- 常见问题速查表，每条给出现象、原因、看哪里：
  - 宿主重启后模板全没了。
  - 模板放了十几天后突然恢复失败。
  - 报“对象不存在”。
  - orchestrator 起不来：`NBD module not loaded`。
  - 并发到几百个后建不出沙箱：NBD 用尽，或大页不够。
  - template-manager 被 OOM 杀（Exit 137），api 一直 503。
  - 部署时 udev 卡住好几分钟。
  - `/orchestrator/build` 很大，是不是泄漏。
  - ARM 上快照比预期大很多。
  - 停服后内存没回来：大页静态池还占着。
  - 改了 MinIO 配置没效果。
  - 回滚报配额超限或“中毒”。
- 风险与改进方向：
  - 模板放在 tmpfs 上。
  - MinIO 未启用。
  - ARM 上增量偏大。
  - 检查点不跨进程持久化。
- 术语表（中英对照）。
