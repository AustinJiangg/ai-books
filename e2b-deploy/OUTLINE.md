# 大纲

**书名**：《E2B 部署从零讲透》

**读者**：会一点编程、用过命令行，但没自己部署过一套分布式系统的新手。不要求懂 RPM、systemd、Docker、Nomad、Consul，用到时从头讲。

**目的**：花几个小时读完，能把一台 ARM 服务器从“只装了操作系统”到“能用 SDK 开沙箱”之间发生的每一件事说清楚：
- 装了哪些组件，各自是什么、为什么需要；
- 每一步脚本改了系统的哪里；
- 每个参数从哪里来、到哪里去、改了影响什么；
- 出了问题去哪里看。

概念讲透，只读不练，不安排动手实验。

**写法**：从现实问题出发，先讲“为什么需要”，再讲“是什么”，最后讲“这套环境怎么做、坑在哪”。多用生活类比和图，每篇末尾有“本篇小结”表格。

**代码**：只放简短的示例片段，帮助理解，不追求完整可运行。片段包括：
- `build.sh`、`deploy.sh`、`init-client.sh` 等脚本里的相关几行；
- `e2b-infra.spec` 的段落；
- nomad job（`.hcl`）和 `.env` 的配置项；
- `rpm`、`systemctl`、`nomad`、`consul`、`docker` 等命令和示例输出。

**依据**：以作者实际部署的环境为准，不讲 E2B 官方最新版的新功能。
- 源码：上游 [e2b-dev/infra](https://github.com/e2b-dev/infra) tag `2026.09`，打上 [AustinJiangg/e2b-infra](https://github.com/AustinJiangg/e2b-infra) 里的 ARM 适配补丁 `0001-adapted-for-arm-architecture.patch`。
- 部署方式：单机鲲鹏 ARM 服务器、openEuler，三步：
  1. 下载仓库。
  2. 按 `e2b-infra.spec` 构建 RPM，安装到 `/opt/e2b-infra`。
  3. 依次执行 `build.sh -d`（停止并清理）、`-i`（安装依赖）、`-s`（启动部署）。
- 仓库里已有的部署文档（`single-node-offline-deploy.md`、`deploy-docs/`）是本书的事实来源之一，正文不照搬，按新手的顺序重新组织。

本书自成一体，不依赖本仓库其他书。网络和存储的细节只在用到时讲到够用为止，详见《E2B 沙箱网络从零讲透》《E2B 沙箱存储从零讲透》。

**规模**：20 篇，每篇约 2500～3500 个汉字，合计约 6 万汉字（连同代码、命令和英文约 15 万字符）。

**全书的主线**：部署就是回答三个问题，全书反复回到这三个问题。

| 问题 | 在这套环境里的答案 | 主要在哪几篇 |
|---|---|---|
| 跑什么？可执行的东西从哪来 | 上游源码 + ARM 补丁，离线编译成二进制，连同内核、Firecracker、脚本打进一个 RPM | 第 6～8 篇 |
| 在哪跑、谁管它？ | 周边依赖由 systemd 和 docker 直接管；E2B 自己的四个服务交给 Nomad 管，Consul 负责互相找到 | 第 3、4、10～15 篇 |
| 机器要先准备成什么样？ | 内核模块、大页、转发开关、DNS、目录、iptables 入口 | 第 8、13 篇 |

**贯穿全书的几个事实**，正文会反复回到这里：

| 事实 | 出处 |
|---|---|
| 只有一台机器，它同时是 Nomad 的 server 和 client、Consul 的 server，三个节点池（api / build / default）都落在它身上 | `build.sh` 的 `append_nomad_client_config`、`.env` 的 `*_NODE_POOL` |
| Nomad 上只跑 4 个 job：`redis`、`template-manager-system`、`client-proxy`、`api` | `deploy.sh` 的 `JOBS` |
| orchestrator 和 template-manager 是同一个二进制、同一个进程（`ORCHESTRATOR_SERVICES=orchestrator,template-manager`），以 `raw_exec` 方式直接跑在宿主机上 | `dep/template-manager.hcl`、`start-client.sh` |
| api 和 client-proxy 跑在 docker 容器里，镜像是部署时现场用 `bin/*.Dockerfile` 构建、推到本机 Harbor 的 | `deploy.sh` |
| PostgreSQL、MinIO、Harbor、Nginx、dnsmasq 不归 Nomad 管，由 `build.sh -i` 用 docker 或 systemd 直接装 | `build.sh` 的 `install()` |
| `dep/` 是一层“覆盖”：RPM 先铺上游脚本，`build.sh -i` 再用 `dep/` 里改过的版本盖上去，实际生效的是 `dep/` 那份 | `build.sh` 的 `install_e2b` |
| `.env` 里的值要经过 `deploy.sh` 的 `envsubst` 白名单才能进到 job；hcl 里写死的值会压过 `.env`（例如 `STORAGE_PROVIDER`） | `deploy.sh`、`dep/template-manager.hcl` |
| 基本离线：Go 工具链、vendor 依赖、docker 镜像、Harbor/MinIO/Nomad/Consul 安装包都提前备好；只有 `yum install`（dnsmasq、nginx 等）和 `pip install`（SDK）要一个可用的软件源 | `e2b-infra.spec`、`single-node-offline-deploy.md` §1、§8 |

## 第一部分　打地基：部署要懂的几样东西

### 第 1 篇　从三条命令说起：把一台裸机变成沙箱平台

- 一个场景：一台刚装好 openEuler 的鲲鹏服务器。执行完下面三步后，在另一个终端里 `Sandbox.create()` 就能拿到一台虚拟机。
  1. 下载仓库；
  2. 打出 RPM、装到 `/opt`；
  3. `build.sh -d`、`-i`、`-s`。

  这三步之间，机器上多了什么？
- “部署”到底是什么：把源码变成在某台机器上持续运行、能互相找到、出了问题能自动拉起的一组进程。拆成三个问题：
  - 跑什么；
  - 在哪跑、谁管它；
  - 机器要先准备成什么样。
- 部署完成后的终态全景（全书地图），四层：
  - 机器层：内核模块、大页、目录、网络开关；
  - 宿主服务层：systemd 管的 Nomad、Consul、MinIO、Nginx、dnsmasq；docker 直跑的 PostgreSQL、Harbor；
  - 业务层：Nomad 管的 4 个 job；
  - 沙箱层：Firecracker 虚拟机和里面的 envd。
- 三步各自负责全景图上的哪几块（图）。
- 为什么是 `-d`、`-i`、`-s` 这个顺序，`-d` 为什么放在最前面。
- 本书路线图：每一部分对应全景图的哪一块。
- 配图：全书地图（四层终态）；三步与全景图的对应关系。

### 第 2 篇　E2B 由哪些部件组成：一次 `Sandbox.create()` 经过谁

- 先不谈部署，只看运行时：一台沙箱从请求到开机，经过哪些部件。
- E2B 自己的服务，每个讲清楚“它是什么、监听什么端口、依赖谁”：
  - api：对外的 REST 接口（:3000），管团队、密钥、模板、沙箱的增删查；内部 gRPC（:5009）。
  - client-proxy（又叫 edge）：沙箱流量的入口（:3002），按沙箱 ID 把请求转到对应节点；edge API（:3001）、健康检查（:3003）。
  - orchestrator：每台计算节点上的“沙箱管家”（gRPC :5008、沙箱代理 :5007），负责建网、挂盘、起 Firecracker。
  - template-manager：把 Dockerfile 变成模板（磁盘镜像 + 内存快照）。本环境它和 orchestrator 是同一个进程。
  - envd：跑在每台沙箱里的代理（:49983），执行命令、读写文件。
  - db-migrator 和 seed-db：一次性任务，前者建表，后者造出第一个团队和密钥。
- 它们依赖的外部东西：
  - PostgreSQL：团队、密钥、模板、build 记录；
  - Redis：运行中沙箱的目录；
  - 镜像仓库（Harbor）：服务镜像和建模板用的基础镜像；
  - 对象存储：模板文件（本环境实际用本地目录）；
  - Firecracker、客户机内核、envd 二进制。
- 控制面与数据面：SDK → api（建沙箱）和 SDK → client-proxy（用沙箱）是两条路。
- 可观测性组件（otel-collector、loki、clickhouse、logs-collector）：上游有，本环境全部没部署，为什么可以不要。
- 配图：部件关系图（谁调谁、端口）；控制面与数据面两条路。

### 第 3 篇　部署基础（一）：一个服务在 Linux 上怎么“跑起来”

- 一个程序要长期跑着，需要解决几件事：
  - 开机自己起来；
  - 崩了自己拉起；
  - 日志去哪；
  - 配置从哪读。
- 进程、可执行文件、命令行参数、环境变量：Go 服务几乎全靠环境变量读配置。为什么本书会反复追“这个环境变量是谁设的”。
- 端口：一个服务监听一个端口，两个服务抢同一个端口会怎样（`bind: address already in use`）。`ss -lntp` 怎么看。
- systemd：unit 文件、`systemctl start/enable/status`、`journalctl -u`。
  - 本环境由 systemd 管的服务：nomad、consul、minio、nginx、dnsmasq、docker。
  - 以 `minio.service` 为例读一个 unit 文件。
- 容器：镜像、容器、仓库三个概念。
  - 用“安装包、装好的软件、应用商店”来类比。
  - `docker run` 的几个常用参数：`-d`、`-p`、`--restart=always`、`--health-cmd`。
  - 以 PostgreSQL 容器为例。
  - Dockerfile：本仓库的 api 镜像只有三行，把编译好的二进制拷进 debian 基础镜像。
- 私有镜像仓库：为什么离线环境要自己搭一个（Harbor），`docker tag` / `push` / `pull` 的地址里包含什么。
- HTTPS 与自签证书：只讲到能看懂“为什么要把证书装进系统信任库”。
- 配图：一个服务的“运行要素”（二进制、配置、端口、日志、守护者）；镜像、容器、仓库三者关系。

### 第 4 篇　部署基础（二）：调度与服务发现——Nomad 和 Consul

- 服务多了以后的新问题：
  - 谁来决定服务跑在哪台机器上；
  - 服务挂了谁来重启；
  - 服务换了地址，别人怎么找到它。
- Nomad 的基本概念，用“工厂排班”来类比：
  - server 与 client：排班的人和干活的人。本环境一个进程两样都做。
  - job、group、task：一张排班单、一组必须在一起的活、一件具体的活。
  - driver：`docker`（跑容器）和 `raw_exec`（直接跑宿主机上的程序），本环境两种都用，为什么 orchestrator 必须用 `raw_exec`。
  - job 类型：`service` 与 `system`。template-manager 是 `system`，每个符合条件的节点跑一份。
  - allocation：一次实际的运行实例。`nomad job status`、`nomad alloc logs` 怎么读。
  - node pool：把机器分组，job 声明自己要去哪个池。
  - 资源声明 `resources { cpu, memory }`：既用于调度，也是 cgroup 上限。
  - 健康检查、重启策略、`kill_timeout`、`prestart` 任务。
- Consul 的基本概念：
  - 服务目录：服务注册自己，健康检查不过就摘掉；
  - DNS 接口（:8600）：`redis.service.consul` 这类名字怎么解析出地址；
  - 为什么要让宿主机的 DNS（dnsmasq）把 `.consul` 转给 Consul。
- ACL：Nomad 和 Consul 都开了访问控制，token 是什么，bootstrap 是什么，为什么丢了 token 会报 403。
- 一张图把 Nomad、Consul、dnsmasq、docker 在单机上的关系画清楚。
- 配图：Nomad 概念层级（job → group → task → alloc）；Nomad/Consul/dnsmasq 关系。

### 第 5 篇　原版 E2B 是怎么部署的：从云上集群到一台机器

- 上游的部署形态（GCP）：
  - Terraform 建资源：虚拟机组、负载均衡、存储桶、密钥；
  - Packer 预先做好机器镜像（装好 Nomad、Consul、内核参数）；
  - 多个 Nomad 集群和节点池：api 节点、build 节点、client（沙箱）节点、server 节点；
  - 云服务：GCS 存模板、Artifact Registry 存镜像、Supabase 或云数据库、Memorystore（Redis）、Grafana 监控。
  - 上游的服务是怎么一步步“上线”的：`make` 构建镜像 → 推送 → Terraform 渲染 job 模板 → 提交到 Nomad。
- 为什么改成单机离线：
  - 没有 GCP；
  - 内网不通外网；
  - ARM 架构；
  - 一台大内存鲲鹏服务器就够用。
- 一张对照表：上游用的云服务 → 本环境的替代品。
  - GCS → 本地目录（MinIO 已装但未启用）；
  - Artifact Registry → Harbor；
  - 云数据库 → docker 里的 PostgreSQL；
  - Packer 镜像 → RPM 加 `init-client.sh`；
  - Terraform 的模板变量 → `.env` 加 `envsubst`；
  - 负载均衡和域名 → dnsmasq 加 iptables 80→3002；
  - 监控日志 → 不部署。
- 本仓库其实支持三种形态，本书只讲第三种：
  - 多节点 Nomad（`start-server.sh` / `start-client.sh` 按节点池加入）；
  - Kubernetes（`helm/`、`deploy.sh --type k8s`）；
  - 单机（`build.sh`），本书主角。
  - 三者共用同一套二进制和 job 定义，区别在“谁来调用这些脚本、几台机器”。
- ARM 补丁里和部署有关的改动（只列清单，细节在后面各篇）：
  - job 模板从 Terraform 语法改成 `envsubst` 能填的 `${VAR}`；
  - Dockerfile 从“容器里编译”改成“拷贝现成二进制”；
  - Makefile 支持 arm64、离线 vendor 构建；
  - `init-client.sh`、`run-nomad.sh` 等脚本去掉对 GCP 的依赖。
- 配图：上游 GCP 集群形态；上游组件 → 本环境替代品对照。

## 第二部分　第一、二步：从仓库到装好的 RPM

### 第 6 篇　仓库里有什么：补丁、原料与配方

- 先建立一个心智模型：这个仓库不是“源码仓库”，而是“打包仓库”。用做菜来类比：
  - 原料：上游源码包 `e2b-infra-2026.09.tar.gz`、各种预编译的二进制；
  - 改良：`0001-adapted-for-arm-architecture.patch`；
  - 配方：`e2b-infra.spec`；
  - 上菜后的摆盘：`e2b-deploy/`。
- 逐个过一遍仓库根目录的文件，每个说清楚是什么、谁会用到它：
  - 上游源码包（走 git-lfs，约 140 MB，自带各模块的 `vendor/`）。为什么不能拿 GitHub 的标签归档代替。
  - ARM 补丁（近 900 KB）：改了哪几类文件。
  - `tools-arm64.tar.gz`：离线的 Go 工具链。
  - `firecracker.arm`：定制版 Firecracker。
  - `vmlinux.bin.arm`、`vmlinux.bin.arm.openeuler`、`vmlinux.bin.x86`：客户机内核。
  - `busybox_1.35_arm64`：建模板时注入客户机的工具。
  - `goose_*`：数据库迁移工具。
  - `ubuntu-22.04-custom.tar.gz`：建模板用的离线基础镜像。
  - `patch_e2b.py`：SDK 补丁。
  - `e2b-deploy/`：部署包，`build.sh` 和 `dep/`。
  - 文档和工具目录：`deploy-docs/`、`benchmark/`、`rollback/`、`gsd/`，和部署的关系。
- 为什么用“上游源码 + 一个补丁”而不是直接 fork 改代码：跟进上游版本时的取舍。
- 配图：仓库文件地图（原料、改良、配方、摆盘四类）。

### 第 7 篇　RPM 与 spec：一个包是怎么打出来的

- 为什么用 RPM：
  - openEuler 的原生包格式；
  - 一条命令装、卸、升级；
  - 版本可追踪；
  - 离线可分发。
- RPM 的基本概念：
  - 源码包与二进制包；
  - `rpmbuild` 的目录（`SOURCES`、`BUILD`、`RPMS`）；
  - Name、Version、Release；
  - `rpm -ivh`、`-Uvh --force`、`-e`、`-ql`。
- spec 文件逐段精读：
  - 头部：`Source0`～`Source9`、`Patch1`，每一项对应仓库里哪个文件。
  - `%prep`：解压源码、`%autosetup -p1` 打补丁、把 busybox 放进源码树、解压离线 Go 工具链、复制 `e2b-deploy/`、放入 ubuntu 基础镜像。
  - `%build`：
    - `GOFLAGS=-mod=vendor`：只用源码包自带的依赖，不联网；
    - 对 api、client-proxy、envd、db、orchestrator 逐个 `make build`；
    - 单独编译 `seed-db`。
  - `%install`：把构建产物摆到 `/opt/e2b-infra` 的哪里（第 8 篇详讲）。
  - `%files`：哪些文件归这个包管，卸载时一起删。
  - `%ifarch`：同一份 spec 怎么区分 aarch64 和 x86_64。
  - `%changelog`：从“适配 ARM”到“加入一键部署”的演进。
- 第二步的实际命令：放好源码包、改 `.env` 里的 `SERVER_IP`、`rpmbuild -ba`、`rpm -ivh`。
- 为什么改 `.env` 要在打包之前：spec 把 `e2b-deploy/` 整个拷进包里。
- 常见坑：
  - 源码包拉不到（LFS 服务器在内网）；
  - Release 没递增导致 `already installed`；
  - 通配符把旧包一起匹配进来。
- 配图：rpmbuild 流水线（`%prep` → `%build` → `%install` → `%files` → `.rpm`）。

### 第 8 篇　装好之后的 `/opt/e2b-infra`，以及动手前机器要备好什么

- `/opt/e2b-infra` 的布局，每个文件从哪来（spec 里的哪一行）：
  - `bin/`：
    - 各服务二进制：api、client-proxy、orchestrator、envd、seed-db、goose；
    - 各服务的 Dockerfile；
    - `migrations/`；
    - 内核 `vmlinux.bin*`、`firecracker`。
  - `nomad/*.hcl`：job 模板；
  - 根目录的脚本：start-server/start-client/init-client/deploy/run-nomad/run-consul 等；
  - `dep/`、`build.sh`、`patch_e2b.py`、`helm/`。
- 同一个脚本有两份：RPM 从上游源码装的那份，和 `dep/` 里改过的那份。`build.sh -i` 用后者覆盖前者。
  - 为什么要这样设计。
  - 后果：`rpm -Uvh` 之后必须重放一遍覆盖，否则跑的是上游版。
- “第 0 步”：动手执行 `build.sh` 之前，机器要自己备好的东西（脚本不管）：
  - 硬件与系统：鲲鹏 CPU、BIOS 开虚拟化、`/dev/kvm`、openEuler；
  - Docker 自备，`daemon.json` 里的 `insecure-registries`；
  - 自编译的 nbd 模块（`nbds_max=512`），固化为开机加载；
  - `net.ipv4.ip_forward=1`，以及 openEuler 自带的 `sysctl.conf` 会把它压回 0 的坑；
  - SELinux 设为 permissive；
  - `/etc/resolv.conf` 的几种情况；
  - 离线大件放进 `dep/`：Harbor 离线安装包、MinIO 二进制、Nomad/Consul 的 zip；
  - 离线镜像提前 `docker load`：postgres、redis 等；
  - `.env` 里的 `SERVER_IP` 必须是本机地址（`check_host_ip` 会拦）。
- 机器上还跑着别的沙箱系统（如 AgentENV）时要注意什么，只点到为止。
- 配图：`/opt/e2b-infra` 目录树，标出来源；“RPM 底座 + dep 覆盖”两层示意。

## 第三部分　第三步：`build.sh` 一步一步

### 第 9 篇　`build.sh` 总览：一个脚本，几种模式

- `build.sh` 的定位：单机部署的总开关，把上游分散在多台机器上的步骤串成一条命令。
- 所有参数一览：
  - `-i` 安装依赖；
  - `-s` 启动部署；
  - `-d` 停止清理；
  - `-u` 卸载；
  - `-r <job>` 只重跑一个 job；
  - `-f` 只跑 `deploy.sh`；
  - `--recycle-netns`、`--purge-hugepages`；
  - `-m` 制作自定义镜像。
- 开头的公共部分：`source dep/.env`、`HOST_IP=$SERVER_IP`、几个写死的端口和 Harbor 账号。
- 三个主模式的调用树（图）：每个模式依次调用哪些函数和子脚本。
- 两条设计原则，后面各篇会反复看到：
  - 幂等：反复执行不会叠加（`grep -q` 再追加、`mountpoint -q` 再挂载、`iptables -C` 再添加）；
  - 先拦截后执行：把配错了会导致误导性报错的情况提前检查掉（`check_host_ip`、`check_ports_free`）。
- 哪些改动是持久的（写进文件，重启还在），哪些是临时的（写进 `/proc`，重启就没）。一张表，第 20 篇排障时用。
- 配图：`build.sh` 各模式的调用树；持久与临时改动对照。

### 第 10 篇　`build.sh -i`（一）：周边依赖——数据库、对象存储、镜像仓库

- `install()` 的顺序与每一步的理由：
  1. `check_host_ip`；
  2. 装 dnsmasq 等工具；
  3. `setenforce 0`；
  4. PostgreSQL；
  5. MinIO；
  6. Harbor；
  7. Nginx；
  8. E2B 本身（第 11 篇）。
- PostgreSQL：
  - 以 docker 容器运行，账号、库名、端口、健康检查；
  - 存什么：团队、API key、模板、build、tier（配额）；
  - 表是谁建的：不是这里，是第 15 篇的 db-migrator。
- MinIO：
  - systemd 服务、数据目录、控制台端口；
  - 一个要提前说明的事实：装好了、健康检查也过了，但当前没有组件往里写，原因见第 16 篇。
- Harbor：
  - 为什么需要自己的镜像仓库；
  - `-i` 只解压并改好 `harbor.yml`（关 HTTPS、hostname 改成本机 IP、端口 2900），真正安装在 `-s`；
  - 为什么要拆成两步。
- Nginx 与证书：
  - 为什么模板的 `FROM` 写 `harbor:443/...`，而 Harbor 实际听 2900；
  - Nginx 以 `server_name harbor` 监听 443，反代到 2900；
  - 生成自签证书，并装进两处信任：系统信任库（建模板的程序读这里）和 `/etc/docker/certs.d/harbor:443/`（docker 读这里）。
- 卸载时（`-u`）这几样分别怎么清。
- 配图：`-i` 装出来的周边依赖（端口、运行方式、数据目录）；`harbor:443` 到 Harbor 的一条请求路径。

### 第 11 篇　`build.sh -i`（二）：E2B 本体与 SDK

- `install_e2b` 做的三件事：
  1. 装 SDK；
  2. 把 `dep/` 覆盖到 `/opt/e2b-infra`；
  3. 配 dnsmasq。
- 装 SDK：
  - `e2b==2.20.0`、`e2b_code_interpreter==2.4.1`，为什么锁死版本；
  - 用 `dep/` 里的 5 个文件替换 site-packages 里的同名文件，各解决什么问题（连接地址、模板构建、Dockerfile 解析等）；
  - checkpoint SDK 覆盖层（`e2b-sdk-checkpoint/install.py`）；
  - `patch_e2b.py`：把 SDK 里的 https 全部换成 http；
  - 三者的顺序为什么不能反。
- `dep/` 覆盖：哪几个文件被盖掉、各改了什么（列表，细节散在后面各篇）：
  - `.env`；
  - `template-manager.hcl`；
  - `start-server.sh`、`start-client.sh`、`init-client.sh`；
  - `run-nomad.sh`、`run-consul.sh`、`install-*.sh`、`uninstall-*.sh`；
  - `deploy.sh`。
- Nomad、Consul 安装包放进 `/tmp`：`install-nomad.sh` 发现文件已在就跳过下载，这就是“离线安装”的实现方式。
- Nomad 版本至少 1.11.2：1.10 在 NUMA 节点编号不连续的鲲鹏上一启动就 panic。
- dnsmasq 加两行：
  - `address=/.e2b.app/127.0.0.1`：沙箱域名都指向本机；
  - `local=/e2b.app/`：AAAA 查询立刻答空，避免每个新连接多等 15 秒。
- 配图：SDK 改造的三层（文件替换 → checkpoint 覆盖 → https→http）。

### 第 12 篇　`build.sh -s`（一）：拉起 Harbor、Consul 与 Nomad

- `start()` 的完整顺序（图），本篇讲前半段。
- 安装并启动 Harbor：
  - `install.sh` 用 docker compose 拉起一组容器；
  - 为什么之后要 `chown 10000:10000` 并重启 registry 和 proxy。
- `start-server.sh`：
  - 安装 Consul、Nomad；
  - `run-consul.sh --server`：生成配置、写 systemd unit、启动；
  - `run-nomad.sh --server`：生成 `/etc/nomad.d/default.hcl`；
  - ACL bootstrap：拿到管理 token，存到 `/data/nomad/acl.token`，并同步写回 `.env`。重跑时为什么能“找回”旧 token；
  - 建 api、build 节点池。
- `append_nomad_client_config`：让同一个 Nomad 也当 client。
  - 节点池 `api`。为什么三个节点池在单机上都指向 api（`.env` 的 `*_NODE_POOL`）。
  - 打开 `raw_exec` 插件。
  - `network_interface` 和 `network_speed`：宿主机网卡多到几千块时，Nomad 的指纹探测要走几分钟，4646 迟迟不开。
- `start-client.sh`：
  - 把 `bin/orchestrator` 拷成 `/usr/bin/orchestrator` 和 `/usr/bin/template-manager`（同一个二进制两个名字）；
  - 建 `/orchestrator/{sandbox,template,build}`；
  - 1G swap；
  - `/mnt/snapshot-cache` tmpfs；
  - 几个 sysctl。
- `wait_for_port 4646`：等 Nomad 的 HTTP 接口打开，为什么会卡在这里、卡住时看什么。
- 部署过程中出现、但属于正常的报错：
  - `-s` 时连不上 8500；
  - 日志里的 “skipping download”。
- 配图：`-s` 全流程时间线；单机上 Nomad/Consul 的 server+client 合一。

### 第 13 篇　`build.sh -s`（二）：把宿主机调成能跑沙箱的样子

- `init-client.sh` 是“机器层”的主要准备者。它原本是上游 CI 给测试机用的脚本，被改造成单机部署的一步。
- 逐项讲，每项都说清楚：不做会怎样；在网络或存储书里的哪一篇有详解。
  - `net.ipv4.ip_forward=1`：
    - 为什么必须在 template-manager 启动前生效（新 netns 创建时继承）；
    - openEuler 的 `/etc/sysctl.conf` 写死了 0。
  - 连接数、`max_map_count` 等 sysctl。
  - NBD：
    - udev 规则 `nowatch`；
    - 为什么只对 nbd 设备 `udevadm trigger`，全机触发会让 udevd 忙几分钟。
  - Firecracker 运行环境：
    - `/fc-kernels/<版本>/vmlinux.bin`，目录名就是模板请求里的内核版本号；
    - `/fc-versions/<版本>/firecracker`：定制版，替换时先删后拷，避免 `Text file busy`；
    - `/fc-envd`。
  - 大页：
    - 先给系统留 4～42 GiB 普通内存；
    - 剩下的 20% 做静态池（上限 `HUGEPAGES_BASE_MAX_MIB`），80% 做超分配；
    - 一台 1.5 TB 内存的机器上各算出多少（算例）。
  - DNS：
    - `/etc/resolv.conf` 第一行指向 127.0.0.1；
    - dnsmasq 把 `.consul` 转给 Consul 的 8600。
- 这些准备完成后，宿主机上新增的目录、挂载点、设备、内核参数总表。
- 配图：大页切分示意（普通内存 / 静态池 / 超分配）；宿主机准备清单与“不做会怎样”。

### 第 14 篇　`build.sh -s`（三）：镜像入库、渲染 job、提交上线

- `start()` 的后半段：
  - `docker login` Harbor；
  - 建项目 `e2b-orchestration`；
  - `/etc/hosts` 写入 `harbor`，并重启 dnsmasq；
  - 推送模板基础镜像 `ubuntu:22.04-custom`。为什么推到 `IP:2900` 而模板从 `harbor:443` 拉，两者是同一个仓库。
  - 删掉 `orchestrator.Dockerfile`：orchestrator 不进容器。
- `deploy.sh` 三段：
  1. 构建并推送镜像：
     - 遍历 `bin/*.Dockerfile`，构建 api、client-proxy、db-migrator 的镜像并推进 Harbor；
     - redis 镜像重新打标签后推送；
     - 为什么关掉 BuildKit。
  2. 渲染并提交 job：
     - `envsubst` 把 `nomad/*.hcl` 里的 `${VAR}` 填成 `.env` 的值，写到 `rendered/`；
     - 为什么要列一个变量白名单：不列的话，hcl 里 Nomad 自己的 `$${node.unique.name}` 也会被吃掉；
     - 按 redis → template-manager → edge → api 的顺序 `nomad job run`。
  3. 初始化数据：
     - 用 `seed-db` 造出团队 E2B、access token、team API key，写进 `/root/.e2b/config.json`；
     - 把 `base_v1` 套餐的并发和存活时长放到 10000。
- 最后一步：两条 iptables 规则把 80 端口交给 client-proxy（3002），外机走 PREROUTING、本机走 OUTPUT，为什么要加 `--dst-type LOCAL`。
- 配图：`.env` → `envsubst` → `rendered/*.hcl` → `nomad job run` → 进程环境变量；镜像从 Dockerfile 到 Harbor 再到容器。

### 第 15 篇　四个 job 逐个读：谁先起、谁等谁

- 读 hcl 的方法：先看 `type`、`node_pool`、`driver`，再看 `network`、`resources`、`env`，最后看 `service` 和 `check`。
- `redis`：docker 跑 Redis，注册为 Consul 服务 `redis`，api 用 `redis.service.consul` 找到它。
- `template-manager-system`：
  - `system` 类型、`raw_exec` 驱动、端口 5008 的 gRPC 健康检查；
  - `ORCHESTRATOR_SERVICES` 让一个进程身兼两职；
  - `kill_timeout = 30s` 不够拆完网络槽位暖池的后果；
  - `resources { memory = 32768 }` 管的是什么：orchestrator 自身和页缓存，不是沙箱内存（客户机内存走大页，不记在这里）；
  - env 里几项重要的配置：网络地址池、`STORAGE_PROVIDER = "Local"`、`MAX_STARTING_INSTANCES_PER_NODE`、证书路径、`fc-netns-exec` 辅助程序。
- `client-proxy`（定义在 `edge.hcl`）：docker 跑，三个端口，靠 Redis 里的沙箱目录找到沙箱在哪个节点。
- `api`：
  - docker 跑；
  - `prestart` 任务 db-migrator 用 goose 建表；
  - `/health` 只有在发现至少一个 orchestrator 节点后才返回 200。
- 启动依赖链（图）：
  - postgres 就绪 → db-migrator → api；
  - template-manager 注册到 Consul → api 发现节点 → api 健康；
  - redis → api 和 client-proxy。
  - 一环断了，最后表现都是“api 一直 503，部署卡 10 分钟后超时”。
- 端口总表：每个端口属于谁、谁访问它、是否对外。
- 配图：四个 job 的启动依赖链；端口与组件对照图。

### 第 16 篇　配置全景：一个参数从哪来、到哪去

- 配置散落在六个地方：
  - `.env`；
  - `nomad/*.hcl` 模板；
  - `rendered/*.hcl`；
  - 二进制里编译进去的默认值；
  - `build.sh` 等脚本里写死的值；
  - 系统配置文件（`/etc/nomad.d`、`/etc/dnsmasq.conf`、`/etc/sysctl.conf` 等）。
- 一个值的完整旅程（图），以 `SANDBOXES_HOST_NETWORK_CIDR` 为例：`.env` → `envsubst` → `rendered/template-manager.hcl` → Nomad → 进程环境变量 → orchestrator 代码。
- 三个“改了没用”的经典原因：
  - 变量不在 `envsubst` 白名单里；
  - hcl 里写死了，例如 `STORAGE_PROVIDER = "Local"` 压过 `.env` 的 `MinioBucket`，所以 MinIO 装了没用上；
  - 改的是 `rendered/`，下次渲染被覆盖。
- `.env` 分类讲解，每项给出本环境的值、作用、改了影响什么：
  - 地址与端口；
  - 凭证与 token（`NOMAD_ACL_TOKEN`、`CONSUL_ACL_TOKEN`、`API_ADMIN_TOKEN`、`SANDBOX_ACCESS_TOKEN_HASH_SEED`、`EDGE_API_SECRET`、Harbor/MinIO 账号）；
  - 数据库、Redis、镜像仓库连接；
  - 沙箱网络地址池（为什么从 10.11/10.12 改成 10.13/10.14）；
  - 大页上限；
  - 节点池；
  - 版本号；
  - 存储后端；
  - 留着但没用上的项：ClickHouse、Loki、OTel、Grafana、LaunchDarkly、PostHog。
- 不在 `.env` 里、但同样重要的参数：
  - 写死在 hcl 里的资源配额（api 20 GiB、template-manager 32 GiB）；
  - 写死在 `build.sh` 里的端口和 Harbor 账号；
  - 编译进二进制的默认内核版本；
  - 补丁里调过的槽位池大小。
- “要改 X，动哪几处”速查表。
- 配图：一个变量的旅程；配置来源的六个地方。

## 第四部分　部署之后

### 第 17 篇　部署好了没有：验证与第一台沙箱

- 自下而上的验证顺序，每层给一条命令和正常的输出：
  1. 机器层：`lsmod | grep nbd`、`/proc/meminfo` 的大页、`sysctl net.ipv4.ip_forward`；
  2. 宿主服务层：`systemctl status`、`docker ps`、Harbor 能登录；
  3. 调度层：Nomad UI（:4646）、`nomad job status`、Consul UI（:8500）里的服务都是绿的；
  4. 业务层：`curl :3000/health`、client-proxy 健康检查；
  5. 沙箱层：建模板、开沙箱、跑一条命令。
- 用 SDK 连上来需要什么：
  - `/root/.e2b/config.json` 里的 key；
  - `.env` 里的 `E2B_API_KEY`、`E2B_ACCESS_TOKEN`、`E2B_DOMAIN`、`E2B_API_URL`、`E2B_HTTP_SSL`。
- 建第一个模板：`build_prod.py` 里的 `FROM harbor:443/e2b-orchestration/ubuntu:22.04-custom`，背后依次用到第 10、13、14 篇准备的东西：
  - Harbor 与证书；
  - `/etc/hosts` 里的 harbor；
  - 内核目录；
  - Firecracker；
  - envd；
  - 大页。
- 开第一台沙箱：把一次 `Sandbox.create()` 和 `commands.run()` 在全景图上走一遍，标出每一步用到了部署的哪一部分。
- 从别的机器访问需要补的配置：DNS、防火墙、SDK 补丁。
- checkpoint / restore 是否就绪：能力文件、firecracker 哈希、SDK 自检。
- 配图：五层验证清单；一次请求在全景图上的路径。

### 第 18 篇　`build.sh -d`：怎么停干净

- 为什么“停”比“起”难：
  - 沙箱留下的网络槽位（netns、veth、iptables 规则）；
  - Firecracker 进程；
  - 大页；
  - 端口。
  - 这些不会因为进程退出而自动消失。
- `stop()` 的顺序，以及每一步排在这里的理由：
  1. 先通过 Nomad 优雅停 template-manager，让它自己拆暖池（必须赶在停 Nomad 之前）；
  2. 停 Consul、Nomad；
  3. 按命令行精确匹配杀业务进程（为什么早先写错的匹配模式永远找不到进程）；
  4. 杀残留的 Firecracker，否则下次拷贝时 `Text file busy`；
  5. 最后兜底 `pkill nomad/consul`（为什么不能提前：会连带杀掉 raw_exec 任务的父进程，留下孤儿）；
  6. 清 netns/veth，再用 `iptables-restore --noflush` 批量删规则，跳过仍在运行的槽位；
  7. 检查端口都已释放。
- 故意不做的事：不释放大页静态池。理由：重新凑连续内存更难。需要时用 `--purge-hugepages`。
- 槽位泄漏为什么会越攒越多，攒多了会怎样（Nomad 指纹探测变慢、iptables 变慢），`--recycle-netns` 怎么回收。
- `-u` 卸载和 `-d` 停止的区别：哪些东西 `-u` 也不删（MinIO 数据、docker）。
- 配图：`-d` 的停止顺序与理由；槽位泄漏的成因与回收。

### 第 19 篇　改了东西之后，怎么让它生效

- 先想清楚：一套完整部署 = RPM 铺底 + `dep/` 覆盖 + 运行时生成的东西（ACL token、`rendered/`、`/usr/bin` 里的二进制、`/etc` 下的配置）。改动落在哪一层，决定了要做什么。
- 五种场景，每种给出最小操作和为什么：
  1. 彻底重来：`-d` → `-i` → `-s`；
  2. 改了 Go 源码：
     - 重新生成补丁、重打 RPM、`rpm -Uvh --force`；
     - 重放 `dep/` 覆盖，但不要覆盖 `.env`，否则 token 丢失；
     - 刷新 `/usr/bin` 里的二进制；
     - 涉及 api 或 client-proxy 时重建镜像；
     - 先 stop 再 run：二进制变了但 hcl 没变时，Nomad 认为“没有变更”，不会替换 allocation；
  3. 改一个 job 的环境变量：改 `nomad/<job>.hcl`，`build.sh -r <job>`，值变了 Nomad 会自动替换；
  4. 改了 `.env`：哪些变量只影响 job（重渲染即可），哪些影响 `-i`/`-s` 阶段（要重跑）；
  5. 改 Nomad、Consul 的配置：只改 `/etc/nomad.d`，重启服务。
- 改完怎么确认真的生效了，从源头到进程逐层核对：
  - 模板文件；
  - `rendered/`；
  - Nomad 里的 job 定义；
  - 进程的 `/proc/<pid>/environ`；
  - 二进制特征串。
- 源码开发的日常循环（只讲轮廓）：改代码 → 编译 → 直接替换二进制 → 验证；阶段结束才重生成补丁和出包。
- 配图：部署的三层（RPM / dep / 运行时生成物）与五种场景的对应；“改动是否生效”的逐层核对。

### 第 20 篇　全景、排障与风险

- 回到第 1 篇的全景图，再走一遍三步部署，这次每个方框都能说出：谁装的、配置在哪、日志在哪、怎么重启。
- 排障思路：按层定位，从“机器 → 宿主服务 → 调度 → 业务 → 沙箱”往上查。每层的第一条命令。
- 常见问题速查表，每条给出现象、原因、看哪里、怎么办：
  - `check_host_ip` 报错，或健康检查返回 504（`SERVER_IP` 配错、代理劫持）；
  - `deploy.sh` 报 403：ACL token 和 Nomad 里的不一致；
  - 卡在“等待 4646”：网卡太多、NUMA panic、Nomad 版本；
  - api 一直 503，部署卡 10 分钟后超时：template-manager 没起来（端口被占、OOM、资源调度不上）；
  - `reserved port collision`：旧 allocation 还没退干净；
  - 建模板 60 秒超时、`build was cancelled`：`ip_forward` 为 0；
  - 建模板报 `lookup harbor ... server misbehaving`：`/etc/hosts` 缺 harbor；
  - 建模板失败后别名被占：`Alias 'base' already used`；
  - 沙箱第一条命令慢 15 秒：AAAA 查询；
  - `-s` 中途 udevadm 超时；
  - `Text file busy`：上一轮的 Firecracker 还在；
  - 停服后内存没回来：大页静态池。
- 日志地图：每个组件的日志在哪（journalctl、`docker logs`、`nomad alloc logs`、`/data/nomad/alloc`）。
- 这套部署的风险与改进方向：
  - 安全：明文 HTTP、自签证书、`setenforce 0`、写在 `.env` 和脚本里的默认密码与 token；
  - 可靠性：单点、模板放在 tmpfs（重启即丢）、MinIO 未启用、无监控告警；
  - 可维护性：`dep/` 与上游脚本两份并存、RPM 升级后要重放覆盖。
- 术语表（中英对照）。
- 附录：
  - 端口总表；
  - 路径总表（`/opt/e2b-infra`、`/etc/nomad.d`、`/data/nomad`、`/opt/consul`、`/orchestrator`、`/fc-*`、`/mnt/hugepages`、`/mnt/snapshot-cache`、`/root/.e2b`）；
  - `build.sh` 参数速查。
- 配图：全景图加上“谁装的 / 配置在哪 / 日志在哪”标注；按层排障流程。
