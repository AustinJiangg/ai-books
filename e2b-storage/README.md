# E2B 沙箱存储从零讲透

一本写给计算机新手的 E2B 沙箱存储教程，讲的是一套实际在用的部署：

- **源码**：上游 [e2b-dev/infra](https://github.com/e2b-dev/infra) tag `2026.09`，加 ARM 适配补丁（[AustinJiangg/e2b-infra](https://github.com/AustinJiangg/e2b-infra) 里的 `0001-adapted-for-arm-architecture.patch`）。
- **机器**：单机鲲鹏服务器，openEuler。
- **部署**：RPM 安装到 `/opt/e2b-infra`，依次执行 `build.sh -d/-i/-s`。

前 6 篇是够用的存储基础：块与页、文件系统、稀疏文件、tmpfs、块设备与 NBD、虚拟内存与 mmap、大页、userfaultfd、写时复制与分层，以及 Firecracker 眼中的磁盘和内存。

之后顺着一个沙箱的存储一生往下讲：

1. 模板：一个 buildID 目录里的六个文件和“拍平的映射表” header；模板的原料仓库 Harbor；从 Dockerfile 到 `rootfs.ext4` 的构建流水线；存储后端，以及为什么 `.env` 写了 MinIO、模板却落在 tmpfs 上的 `/tmp/templates`。
2. 一个沙箱的存储栈：`/orchestrator` 下的本地缓存与 4 MiB 分块拉取；NBD 加写时复制的根盘；UFFD 按需供页与大页预留。
3. 快照：暂停与恢复怎么产生一个增量 build；ARM 上内存增量为什么偏大、写跟踪位图怎么补回来；补丁新增的检查点回滚，包括检查点树、内存还原、磁盘封存层、压实与配额。

最后讲部署脚本为存储做了什么、全部配置项，以及容量规划与排障。

约 5.3 万汉字，19 篇。

本书只读不练，没有需要动手的实验；文中的代码和命令都是帮助理解的示例片段，不追求完整可运行。网络相关的内容只在用到时一句带过，详见《E2B 沙箱网络从零讲透》。

## 目录

### 第一部分　打地基：够用的存储知识

- [第 1 篇　从“毫秒开一台虚拟机”说起：E2B 的存储要解决什么问题](01-what-storage-solves.md)
- [第 2 篇　存储基础（一）：字节、块、页与文件系统](02-bytes-blocks-pages-filesystems.md)
- [第 3 篇　存储基础（二）：块设备与 NBD](03-block-devices-and-nbd.md)
- [第 4 篇　存储基础（三）：虚拟内存、mmap、缺页与 userfaultfd](04-virtual-memory-mmap-uffd.md)
- [第 5 篇　写时复制与分层：只存改动的思想](05-cow-and-layers.md)
- [第 6 篇　虚拟机的“盘”和“内存条”：Firecracker 眼中的存储](06-firecracker-disk-and-memory.md)

### 第二部分　模板：沙箱的“出生证”

- [第 7 篇　模板长什么样：一个 buildID 目录里的六个文件](07-template-six-files.md)
- [第 8 篇　模板的原料仓库：Harbor 与镜像的存放](08-harbor-image-registry.md)
- [第 9 篇　从 Dockerfile 到 rootfs.ext4：模板构建流水线](09-template-build-pipeline.md)
- [第 10 篇　模板存到哪：存储后端、Local 与“装了没用”的 MinIO](10-storage-backends.md)

### 第三部分　一个沙箱的存储栈

- [第 11 篇　节点本地缓存：`/orchestrator` 目录里都是什么](11-node-local-cache.md)
- [第 12 篇　沙箱的硬盘：NBD 加写时复制](12-sandbox-disk-nbd-cow.md)
- [第 13 篇　沙箱的内存：UFFD 按需供页与大页](13-sandbox-memory-uffd-hugepages.md)

### 第四部分　快照：暂停、恢复与回滚

- [第 14 篇　暂停与恢复：一次增量快照是怎么做出来的](14-pause-and-resume.md)
- [第 15 篇　ARM 上的增量为什么“偏大”：脏页判据与实测](15-arm-incremental-snapshot.md)
- [第 16 篇　快照回滚（一）：检查点树与内存](16-rollback-checkpoint-tree.md)
- [第 17 篇　快照回滚（二）：磁盘层、压实与配额](17-rollback-disk-compaction-quota.md)

### 第五部分　部署、容量与排障

- [第 18 篇　部署里的存储配置：RPM、`build.sh -d`、`-i`、`-s`](18-deploy-storage-config.md)
- [第 19 篇　全景、容量规划与排障](19-big-picture-capacity-troubleshooting.md)

编写用文件：[`OUTLINE.md`](OUTLINE.md)（各篇要点）。

## 怎么读

- **第 1 篇的全景图是全书的地图**：后面每一篇都在放大它的某一块，读到迷糊时回去看一眼。
- **第 2～6 篇是通用基础**：只讲后面要用到的操作系统知识，不涉及 E2B 的代码。有基础的读者可以只看每篇的小结表。
- **第 7 篇是钥匙**：模板、暂停、恢复、回滚都绕不开那张“拍平的映射表”。只想抓主线，读第 1、7、11、12、13、14 篇即可。
- **只想知道“模板存在哪、为什么重启会丢、为什么删了不变小”**：读第 10、14 篇。
- **第 15～17 篇讲这套环境特有的东西**：ARM 补丁带来的增量差异，以及补丁新增的检查点回滚。
- **第 18、19 篇最贴近运维**：配置项总表、容量账、排障速查表和术语表，可以当手册用。
- 每篇末尾有“本篇小结”表格，复习时过一遍小结即可。

## 几个容易出乎意料的事实

| 事实 | 篇 |
|---|---|
| orchestrator 和 template-manager 是同一个进程 | 1、18 |
| `.env` 写的是 MinIO，实际生效的是 `Local`，模板在 `/tmp/templates` | 10 |
| openEuler 的 `/tmp` 是 tmpfs：模板占内存、重启就丢、10 天不用会被清 | 10、19 |
| 通过 API 删模板、删快照只删数据库记录，存储里的文件故意不删 | 14 |
| 每个运行中的沙箱占一台 NBD 设备，自编译模块最多 512 台 | 3、12 |
| 客户机内存走 2 MiB 大页，不算在 template-manager 的 32 GiB 上限里 | 13、18 |
| 没有硬件脏页跟踪的 ARM 机器上，每次暂停的内存增量至少是一个工作集 | 15 |
| `/mnt/snapshot-cache` 挂了 65G tmpfs，但这个版本的代码不写它 | 11 |
