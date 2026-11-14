# E2B 部署从零讲透

一本写给计算机新手的 E2B 部署教程，讲的是一套实际在用的部署：

- **源码**：上游 [e2b-dev/infra](https://github.com/e2b-dev/infra) tag `2026.09`，加 ARM 适配补丁（[AustinJiangg/e2b-infra](https://github.com/AustinJiangg/e2b-infra) 里的 `0001-adapted-for-arm-architecture.patch`）。
- **机器**：单机鲲鹏服务器，openEuler。
- **部署**：三步。下载仓库；按 `e2b-infra.spec` 打成 RPM，装到 `/opt/e2b-infra`；依次执行 `build.sh -d`、`-i`、`-s`。

全书围绕三个问题展开：**跑什么**（可执行的东西从哪来）、**在哪跑、谁管它**（systemd、docker、Nomad、Consul）、**机器要准备成什么样**（内核模块、大页、IP 转发、DNS、防火墙入口）。

前 5 篇打地基：部署完成后机器上有哪四层东西；E2B 由哪些部件组成，一次 `Sandbox.create()` 经过谁；服务在 Linux 上怎么跑起来，容器、镜像仓库和自签证书；Nomad 和 Consul；原版 E2B 怎么在云上部署，这套环境把每样云服务换成了什么。

之后顺着三步往下讲：

1. 仓库里有什么，RPM 怎么打，装好的 `/opt/e2b-infra` 里每个文件从哪来，“RPM 底座 + `dep/` 覆盖”两层结构，以及动手前机器要自己备好的东西。
2. `build.sh` 逐段拆开：`-i` 装的数据库、对象存储、镜像仓库、Nginx 与证书、SDK 的三层改造；`-s` 拉起 Harbor、Consul、Nomad，调好宿主机，现场构建镜像，用 `envsubst` 渲染并提交四个 job，造出第一个团队；四个 job 逐个读；所有配置从哪来、到哪去。
3. 部署之后：怎么验证、开第一台沙箱；`-d` 怎么停干净；改了东西怎么生效；排障速查与风险。

约 5 万汉字，20 篇，42 张图。

本书只读不练，没有需要动手的实验；文中的代码和命令都是帮助理解的示例片段，不追求完整可运行。网络、存储的细节只讲到部署要用的程度，详见《E2B 沙箱网络从零讲透》《E2B 沙箱存储从零讲透》。

## 目录

### 第一部分　打地基：部署要懂的几样东西

- [第 1 篇　从三条命令说起：把一台裸机变成沙箱平台](01-three-commands.md)
- [第 2 篇　E2B 由哪些部件组成：一次 `Sandbox.create()` 经过谁](02-components.md)
- [第 3 篇　部署基础（一）：一个服务在 Linux 上怎么“跑起来”](03-how-a-service-runs.md)
- [第 4 篇　部署基础（二）：调度与服务发现——Nomad 和 Consul](04-nomad-and-consul.md)
- [第 5 篇　原版 E2B 是怎么部署的：从云上集群到一台机器](05-upstream-deployment.md)

### 第二部分　第一、二步：从仓库到装好的 RPM

- [第 6 篇　仓库里有什么：补丁、原料与配方](06-repo-map.md)
- [第 7 篇　RPM 与 spec：一个包是怎么打出来的](07-rpm-and-spec.md)
- [第 8 篇　装好之后的 `/opt/e2b-infra`，以及动手前机器要备好什么](08-opt-layout-and-prerequisites.md)

### 第三部分　第三步：build.sh 一步一步

- [第 9 篇　`build.sh` 总览：一个脚本，几种模式](09-build-sh-overview.md)
- [第 10 篇　`build.sh -i`（一）：周边依赖——数据库、对象存储、镜像仓库](10-install-dependencies.md)
- [第 11 篇　`build.sh -i`（二）：E2B 本体与 SDK](11-install-e2b-and-sdk.md)
- [第 12 篇　`build.sh -s`（一）：拉起 Harbor、Consul 与 Nomad](12-start-harbor-consul-nomad.md)
- [第 13 篇　`build.sh -s`（二）：把宿主机调成能跑沙箱的样子](13-host-preparation.md)
- [第 14 篇　`build.sh -s`（三）：镜像入库、渲染 job、提交上线](14-deploy-sh.md)
- [第 15 篇　四个 job 逐个读：谁先起、谁等谁](15-four-jobs.md)
- [第 16 篇　配置全景：一个参数从哪来、到哪去](16-configuration.md)

### 第四部分　部署之后

- [第 17 篇　部署好了没有：验证与第一台沙箱](17-verify-and-first-sandbox.md)
- [第 18 篇　`build.sh -d`：怎么停干净](18-stop-cleanly.md)
- [第 19 篇　改了东西之后，怎么让它生效](19-apply-changes.md)
- [第 20 篇　全景、排障与风险](20-big-picture-troubleshooting.md)

编写用文件：[`OUTLINE.md`](OUTLINE.md)（各篇要点）。

## 阅读建议

- **完全的新手**：从头顺着读。第 3、4 篇是概念基础，后面大量用到。
- **熟悉 Linux 服务和容器**：可以跳过第 3 篇；第 4 篇的 Nomad 部分建议看，这套环境用 Nomad 的方式有些特别。
- **第 1、8、9 篇是三张地图**：全景图、`/opt/e2b-infra` 的两层结构、`build.sh` 的调用树。迷路时回到这三篇。
- **只想抓主线**：读第 1、2、8、9、14、15、19 篇。
- **只想解决眼前的问题**：直接翻第 20 篇的速查表，按表里的指引回到对应篇章。
- **第 16、19、20 篇可以当手册用**：配置总表、五种改动场景、排障速查。
- 每篇末尾有“本篇小结”表格，复习时过一遍小结即可。

## 几个容易出乎意料的事实

| 事实 | 篇 |
|---|---|
| 仓库里没有 E2B 的源码目录，源码装在一个走 git-lfs 的压缩包里，不能用 GitHub 的标签归档代替 | 6 |
| 同一个脚本装了两份：RPM 装上游版，`-i` 用 `dep/` 里的单机版盖上去；升级 RPM 后要重放 | 8、19 |
| orchestrator 和 template-manager 是同一个二进制、同一个进程，名字叫 `/usr/bin/template-manager` | 2、12、15 |
| 一个 Nomad 进程同时当 server 和 client，三个节点池全指向 `api` | 4、12 |
| `.env` 写的是 MinIO，hcl 里写死了 `Local`，MinIO 装了却没用上 | 10、16 |
| openEuler 自带的 `/etc/sysctl.conf` 写死了 `ip_forward=0`，不改的话建模板会在等 envd 时超时 | 8、13 |
| SDK 要经过三层改造才能连上这套环境，顺序不能反 | 11 |
| dnsmasq 少一行 `local=/e2b.app/`，每台沙箱的第一条命令就慢 15 秒 | 11 |
| api 一直 503，原因几乎总在 template-manager | 15 |
| 只换了二进制、hcl 没变时，`nomad job run` 什么都不做 | 4、19 |
| 每次 `-i` 都会重建 PostgreSQL，API key 全部换新；明文 key 只在 `/root/.e2b/config.json` 里写一次 | 10、14、17 |
| 机器重启后不会自动恢复：大页、挂载、iptables 入口、模板都没了 | 9、20 |
