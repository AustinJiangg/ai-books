# 第 18 篇｜部署里的存储配置：RPM、`build.sh -d`、`-i`、`-s`

> **本篇目标**：前面各篇讲的目录、设备、大页、配置项，都是由部署流程准备好的。本篇顺着这套环境的实际部署步骤走一遍：RPM 往 `/opt/e2b-infra` 放了哪些和存储有关的东西；`build.sh -i`、`-s`、`-d` 各为存储做了什么、没做什么；nbd 模块这个“部署前提”要怎么准备；template-manager 那 32 GiB 的内存上限到底管什么；最后给出全书涉及的存储配置项总表，以及改配置时的注意事项。

---

## 一、全流程一览

```
 ① 下载仓库 AustinJiangg/e2b-infra
 ② rpmbuild：上游源码 + ARM 补丁 + 内核 + 定制 Firecracker + 部署包 → RPM
    安装 RPM → /opt/e2b-infra
 ③ 部署前一次性准备：自编译 nbd 模块（nbds_max=512）固化到系统
 ④ build.sh -d   停止并清理
 ⑤ build.sh -i   安装依赖组件：PostgreSQL、MinIO、Harbor、nginx、SDK……
 ⑥ build.sh -s   启动部署：Harbor、Nomad/Consul、宿主初始化、提交 job
```

下面按这个顺序讲和存储相关的部分。

---

## 二、RPM 阶段

### 2.1 构建时

`e2b-infra.spec` 的 `%prep` 阶段：

- 解开上游 `2026.09` 的源码包，打上 `0001-adapted-for-arm-architecture.patch`；
- 把 `busybox_1.35_arm64` 拷进 `packages/orchestrator/internal/template/build/core/systeminit/`，编译时被嵌进 orchestrator 二进制，用作模板构建第一次开机的 init（第 9 篇）；
- 把仓库里的 `e2b-deploy/` 整个拷过来作为部署包，再把 `ubuntu-22.04-custom.tar.gz`（模板基础镜像，第 8 篇）放进 `dep/`。

`%build` 阶段编译 api、client-proxy、envd、db、orchestrator 等。

### 2.2 安装到 `/opt/e2b-infra` 的存储相关文件

| 文件 | 用途 | 去向 |
|---|---|---|
| `bin/orchestrator` | orchestrator 和 template-manager 共用的二进制 | `-s` 时拷成 `/usr/bin/orchestrator` 和 `/usr/bin/template-manager` |
| `bin/envd` | 沙箱里的守护进程 | `-s` 时拷到 `/fc-envd/envd`，构建模板时注入根盘 |
| `bin/vmlinux.bin` | 客户机内核 | `-s` 时拷到 `/fc-kernels/vmlinux-6.1.158/`、`/fc-kernels/vmlinux-6.1.102/` |
| `bin/vmlinux.bin.openeuler` | openEuler 客户机内核 | `/fc-kernels/vmlinux-6.6.0-132.0.0/` |
| `bin/firecracker` | 定制版 Firecracker（只在 aarch64 包里） | `/fc-versions/v1.13.1/firecracker` |
| `nomad/*.hcl` | 上游的 Nomad job 模板 | 其中 `template-manager.hcl` 会被 `-i` 覆盖 |
| `dep/.env` | 全部环境变量 | `-i` 拷到 `/opt/e2b-infra/.env` |
| `dep/template-manager.hcl` | 实际生效的 job 定义 | `-i` 覆盖 `nomad/template-manager.hcl` |
| `dep/init-client.sh`、`dep/start-client.sh` | 宿主初始化脚本 | `-i` 覆盖到 `/opt/e2b-infra/` |
| `dep/minio`、`minio.yml`、`minio.service` | MinIO | `-i` 安装 |
| `dep/harbor-offline-installer-aarch64-v2.13.0.tgz`、`harbor.cnf`、`nginx.conf` | Harbor 和 nginx | `-i` 解压配置，`-s` 启动 |
| `dep/ubuntu-22.04-custom.tar.gz` | 模板基础镜像 | `-s` 推进 Harbor |

注意“覆盖”这件事：RPM 里同时有上游版本和部署包版本的同名文件，`-i` 用部署包版本覆盖上游版本。**实际生效的是 `dep/` 下的那一份。**第 10 篇的 `STORAGE_PROVIDER = "Local"` 就是这么来的。

---

## 三、部署前提：nbd 模块

这是一个**部署脚本不管、必须手工做一次**的步骤（第 3 篇）。部署文档要求把自编译的 nbd 模块固化到系统模块目录：

```bash
# 备份原版，放入自编译版
cp /lib/modules/$(uname -r)/kernel/drivers/block/nbd.ko{,.orig}
cp nbd.ko /lib/modules/$(uname -r)/kernel/drivers/block/nbd.ko

# 开机自动加载，并带上参数
echo nbd > /etc/modules-load.d/nbd.conf
echo "options nbd nbds_max=512" > /etc/modprobe.d/nbd.conf
```

验证：

```bash
cat /sys/module/nbd/parameters/nbds_max     # 512
ls /dev/nbd* | wc -l                        # 512
```

部署脚本里原本有 `rmmod` + `insmod` 的步骤，被去掉了：模块只需要加载一次，重复加载会报 `File exists`。

两个坑：

- **没做**：orchestrator 启动时读不到 `nbds_max`，报 `NBD module not loaded`，起不来；
- **升级内核后**：新内核目录里是发行版原版的 `nbd.ko`，开机照样加载，参数文件照样生效，设备数照样是 512，看不出任何异常，但用的已经不是自编译版了。要重新放一次，并且要在**目标内核**上重新编译。

---

## 四、`build.sh -i`：安装

`-i` 依次执行：检查 `SERVER_IP` 是否是本机地址 → 装系统包 → PostgreSQL → **MinIO** → **Harbor** → **nginx** → **e2b**。和存储相关的：

### 4.1 MinIO

```
/usr/local/bin/minio                 二进制
/etc/default/minio.yml               账号 minioadmin/minioadmin，数据目录 /root/data/minio
/etc/systemd/system/minio.service    systemd 服务，开机自启
```

启动后反复探测 `http://127.0.0.1:9000/minio/health/ready`，等到返回 200。它装好了、跑着，但不存模板（第 10 篇）。

### 4.2 Harbor 和 nginx

解压 Harbor 离线包，改 `harbor.yml`（关 https、主机名改成本机 IP、端口改成 2900）；装 nginx 做 `harbor:443` 的 https 反代，生成自签证书并装进系统信任库和 docker 信任目录（第 8 篇）。此时 Harbor **还没启动**，要等 `-s`。

### 4.3 e2b

- `pip install` 指定版本的 e2b SDK 和 code interpreter SDK；
- 用 `dep/` 下的文件覆盖 `/opt/e2b-infra/` 下的 `.env`、`template-manager.hcl`、`start-client.sh`、`init-client.sh`、`deploy.sh` 等；
- 给 SDK 打补丁：模板构建相关的 `dockerfile_parser.py`、`build_api.py`、`main.py`，以及检查点 SDK 扩展（第 16 篇），最后 `patch_e2b.py` 把 SDK 里的 https 改成 http。

---

## 五、`build.sh -s`：启动部署

`-s` 的顺序（只列存储相关的）：

```
 1. 启动 Harbor（install.sh），修正配置目录属主，重启仓库和入口容器
 2. 启动 Nomad 服务端
 3. start-client.sh       宿主初始化（一）
 4. init-client.sh        宿主初始化（二）
 5. 等 Nomad 端口
 6. 登录 Harbor，建项目 e2b-orchestration，写 /etc/hosts 的 harbor，推基础镜像
 7. deploy.sh             渲染并提交 job：redis、template-manager、edge、api
```

### 5.1 `start-client.sh`

```bash
cp bin/orchestrator /usr/bin/orchestrator
cp bin/orchestrator /usr/bin/template-manager          # 同一个二进制两份

mkdir -p /orchestrator/sandbox /orchestrator/template /orchestrator/build   # 第 11 篇

# 1 GiB 的交换文件 /swapfile，并写进 /etc/fstab
fallocate -l 1G /swapfile && mkswap /swapfile && swapon /swapfile

mkdir -p /mnt/snapshot-cache
mountpoint -q /mnt/snapshot-cache || mount -t tmpfs -o size=65G tmpfs /mnt/snapshot-cache   # 第 11 篇：本版不用

# nbd 的 udev 规则，只对 nbd 触发（第 3 篇）
echo 'ACTION=="add|change", KERNEL=="nbd*", OPTIONS:="nowatch"' > /etc/udev/rules.d/97-nbd-device.rules
udevadm trigger --action=change --subsystem-match=block --sysname-match='nbd*'

mkdir -p /fc-vm                                          # 第 6 篇：每个 FC 的私有 tmpfs 挂在这

mkdir -p /fuse/cache && 写 /fuse/config.yaml             # 上游给 gcsfuse 用的，本环境没用到

# 大页预留（第 13 篇）
```

### 5.2 `init-client.sh`

前半部分和 `start-client.sh` 重复（目录、snapshot-cache、udev、大页），脚本都做了幂等判断，重复执行不会叠加挂载。它独有的是放置运行环境文件：

```bash
cp bin/envd /fc-envd/envd
for kv in vmlinux-6.1.158 vmlinux-6.1.102; do
    cp bin/vmlinux.bin /fc-kernels/$kv/vmlinux.bin
done
cp bin/vmlinux.bin.openeuler /fc-kernels/vmlinux-6.6.0-132.0.0/vmlinux.bin

rm -f /fc-versions/v1.13.1/firecracker                   # 先删再拷
cp bin/firecracker /fc-versions/v1.13.1/firecracker
```

拷 Firecracker 之前**先删**，是为了避开 `Text file busy`：上一轮残留的沙箱进程可能正在执行这个文件，内核不允许以写方式打开正在执行的文件，但允许删除目录项。删掉后，老进程继续用旧的 inode，新文件写到新的 inode，互不影响。

### 5.3 两处“幂等”

`/mnt/snapshot-cache` 和 `/mnt/hugepages` 的挂载都带 `mountpoint -q ... ||` 判断。没有这个判断时，每跑一次 `-s` 就在同一个目录上再叠一层挂载，久了会叠出很多层。

### 5.4 `deploy.sh`

`source .env`，用 `envsubst` 把 `nomad/*.hcl` 渲染到 `rendered/`，然后只提交四个 job：`redis`、`template-manager`、`edge`、`api`。orchestrator 跑在 template-manager 这个 job 里（第 1 篇），上游单独的 orchestrator job 不提交（第 10 篇）。

---

## 六、template-manager 的内存上限

### 6.1 它管什么

`dep/template-manager.hcl` 里：

```hcl
resources {
  memory = 32768    # MiB，即 32 GiB
  cpu    = 2048
}
```

这是 Nomad 给这个任务设的 cgroup `memory.max` 硬上限。这个 cgroup 里有：

- orchestrator 主进程（`/usr/bin/template-manager`）；
- **每个沙箱的 Firecracker 进程**：ARM 补丁注释掉了把 Firecracker 放进独立 cgroup 的那几行，于是它们留在父进程的 cgroup 里。

但客户机内存是 hugetlb 映射，**不记在 memory 控制器上**（第 13 篇）。所以这 32 GiB 记的主要是：

- orchestrator 的堆；
- **构建模板、打快照时读写文件产生的页缓存**：解包镜像、写 rootfs、写 memfile diff、读写 `/orchestrator/build` 里的缓存文件。

部署文档记录过一次事故：构建一个 200 MB 的基础镜像时，orchestrator 被内核以“内存超标”杀掉（退出码 137）。现场的进程堆只有几十 MB，看着像“没吃内存却被杀”，实际是页缓存把 cgroup 撑满了。现象还出在别处：api 一直返回 503，部署卡在 api 那一步 10 分钟超时。

### 6.2 不能太小，也不能太大

| 太小 | 太大 |
|---|---|
| 构建或快照时被 OOM 杀掉（Exit 137），连带 api 503 | 超过节点可分配内存，Nomad 调度不上（`Dimension "memory" exhausted`），同样表现为 api 503 |

这个值的历史是 8192 → 32768 → 262144 → 32768 MiB。32 GiB 能撑住 200 MB 基础镜像的全量重建，128 GiB 的机器也放得下。

要改它，要改源头 `e2b-deploy/dep/template-manager.hcl`，否则下次 `-i` 会覆盖回去。

### 6.3 `kill_timeout = "30s"`

同一个文件里还有一行 `kill_timeout = "30s"`：停服时给进程 30 秒收尾。这主要是为了网络槽位的清理（网络书第 21 篇），和存储关系不大。但要知道：被强杀的 orchestrator 来不及清理任何东西。

---

## 七、`build.sh -d`：停止，以及它不管什么

`-d` 的顺序：

1. 优雅停止 template-manager 这个 job，给它时间自己清理；
2. 停 Consul、Nomad；
3. 逐个结束 redis、client-proxy、api、template-manager、orchestrator 进程，不退出就强杀；
4. **结束所有残留的 Firecracker 进程**（命令行匹配 `/fc-versions/.*/firecracker`），否则下次 `-s` 拷 Firecracker 会遇到 `Text file busy`；
5. 清理网络残留（网络书第 21 篇）；
6. 检查端口是否都释放了；
7. 如果大页静态池还占着，提示用 `--purge-hugepages` 释放。

对存储来说，更重要的是 `-d` **不做**什么：

| 东西 | `-d` 之后 | 什么时候变化 |
|---|---|---|
| `/tmp/templates`、`/tmp/build-cache` | 不动 | 宿主重启时清空；tmpfiles 每天清 10 天未访问的文件 |
| `/orchestrator/build` | 不动 | 下次 orchestrator 启动时整个清空 |
| `/orchestrator/template` | 不动 | 缓存项过期时删除；重启不会主动清 |
| `/orchestrator/sandbox` | 不动 | 正常退出的沙箱会删自己的文件；被强杀的沙箱留下的 COW 文件，代码里没有启动时的清理，会一直留着 |
| 检查点 | 随 orchestrator 进程作废 | 文件在 `/orchestrator/build/checkpoints/`，下次启动清空 |
| 大页静态池 | 不动 | `--purge-hugepages` 或重启 |
| MinIO、Harbor 的数据 | 不动 | — |
| `/dev/nbdN` | 进程被杀后内核会断开 | — |

`/orchestrator/sandbox` 那一行值得留意：如果停服时还有沙箱在跑，它们的 COW 文件会成为孤儿。COW 文件是稀疏的，只占写过的部分，但长期反复停服可能攒下不少。可以在确认没有沙箱运行时手工清理这个目录。

---

## 八、配置项总表

按全书出现的顺序，列出和存储相关的配置项。“本环境”一列是这套部署实际生效的值。

### 8.1 存储后端（第 10 篇）

| 配置 | 默认 | 本环境 | 作用 |
|---|---|---|---|
| `STORAGE_PROVIDER` | `MinioBucket`（补丁改的默认） | **`Local`**（hcl 写死） | 模板和构建缓存存在哪 |
| `LOCAL_TEMPLATE_STORAGE_BASE_PATH` | `/tmp/templates` | 未设 | Local 时模板目录 |
| `LOCAL_BUILD_CACHE_STORAGE_BASE_PATH` | `/tmp/build-cache` | 未设 | Local 时构建缓存目录 |
| `TEMPLATE_BUCKET_NAME` | 无（桶模式必填） | `e2b-dev-fc-templates`（用不上） | 桶模式的模板桶 |
| `BUILD_CACHE_BUCKET_NAME` | 无（桶模式必填） | `e2b-dev-fc-cache`（用不上） | 桶模式的缓存桶 |
| `MINIO_ENDPOINT`、`MINIO_ACCESS_KEY`、`MINIO_SECRET_KEY` | — | `<本机IP>:9000`、`minioadmin`（用不上） | MinIO 连接信息 |
| `SHARED_CHUNK_CACHE_PATH` | 空 | 空 | 共享块缓存，未启用 |
| `ARTIFACTS_REGISTRY_PROVIDER` | `GCP_ARTIFACTS` | `Local` | 按 buildID 取镜像的方式（第 8 篇） |

### 8.2 本地目录（第 6、11 篇）

| 配置 | 默认 | 本环境 |
|---|---|---|
| `ORCHESTRATOR_BASE_PATH` | `/orchestrator` | 默认 |
| `DEFAULT_CACHE_DIR` | `${ORCHESTRATOR_BASE_PATH}/build` | 默认 |
| `TEMPLATE_CACHE_DIR` | `${ORCHESTRATOR_BASE_PATH}/template` | 默认 |
| `SANDBOX_CACHE_DIR` | `${ORCHESTRATOR_BASE_PATH}/sandbox` | 默认 |
| `TEMPLATES_DIR` | `${ORCHESTRATOR_BASE_PATH}/build-templates` | 默认 |
| `SNAPSHOT_CACHE_DIR` | `/mnt/snapshot-cache` | 默认（本版不写） |
| `SANDBOX_DIR` | `/fc-vm` | 默认 |
| `HOST_KERNELS_DIR` | `/fc-kernels` | 默认 |
| `FIRECRACKER_VERSIONS_DIR` | `/fc-versions` | 默认 |
| `HOST_ENVD_PATH` | `/fc-envd/envd` | 默认 |

### 8.3 内存与设备（第 3、13 篇）

| 配置 | 默认 | 本环境 |
|---|---|---|
| nbd 模块 `nbds_max` | 发行版 16 | **512**（手工固化） |
| `HUGEPAGES_BASE_MAX_MIB`（`.env`） | 脚本内 65536 | 65536 |
| 静态池比例 / 超分配比例 | 20% / 80% | 同左（脚本写死） |
| template-manager `memory` | — | 32768 MiB |
| 交换文件 | — | `/swapfile` 1 GiB |

### 8.4 快照与回滚（第 15、16、17 篇）

| 配置 | 默认 | 本环境 |
|---|---|---|
| `FC_TRACK_DIRTY_PAGES` | 看硬件：有 HDBSS 开，否则关 | 未设 |
| `CHECKPOINT_FULL_ROOT` | true | 未设 |
| `CHECKPOINT_MIN_FREE_BYTES` | max(4 GiB, 2×客户机内存) | 未设 |
| `CHECKPOINT_MAX_PER_SANDBOX` | 0（不限） | 未设 |
| `CHECKPOINT_MAX_BYTES_PER_SANDBOX` | 0（不限） | 未设 |
| `CHECKPOINT_COMPACT` | 开 | 未设 |
| `CHECKPOINT_COMPACT_MAX_PER_OP` | 8 | 未设 |
| `CHECKPOINT_LOCK_WAIT_TIMEOUT` | 60s | 未设 |
| `CHECKPOINT_DEBUG_INDEX` | 关 | 未设 |

### 8.5 特性开关

`.env` 里 `LAUNCH_DARKLY_API_KEY` 为空，所有特性开关取代码默认值（第 11 篇）。和存储相关的几个：

| 开关 | 默认 |
|---|---|
| `chunker-config` | 整块拉取，`minReadBatchSizeKB=16` |
| `build-cache-max-usage-percentage` | 85 |
| `nbd-connections-per-device` | 4 |
| `memory-prefetch-max-fetch-workers` / `copy-workers` | 32 / 16 |
| `build-base-rootfs-size-limit-mb` | 25000 |

---

## 九、改配置时注意

1. **改源头**。实际生效的是 `dep/` 下的文件，`-i` 每次都会用它覆盖 `/opt/e2b-infra/` 下的同名文件。要么改仓库里的 `e2b-deploy/dep/...` 再重新出 RPM，要么记得每次 `-i` 之后再改一次。
2. **只重启一个 job**。改了 template-manager 的环境变量，不必整套 `-s`：

   ```bash
   build.sh -r template-manager      # 只渲染并重跑这一个 job
   ```

3. **确认生效**。看进程实际的环境变量，或者看检查点能力文件：

   ```bash
   tr '\0' '\n' < /proc/$(pgrep -f '^/usr/bin/template-manager' | head -1)/environ | grep -E 'STORAGE|CHECKPOINT|FC_TRACK'
   cat /orchestrator/build/checkpoint-capabilities.json
   ```

4. **运行中的沙箱**。重启 template-manager 会让所有运行中的沙箱随之结束，检查点全部作废，`/orchestrator/build` 被清空。挑没有业务的时候做。
5. **换存储目录要搬数据**。改 `LOCAL_TEMPLATE_STORAGE_BASE_PATH` 或切到 MinIO，都要把旧数据按 `<buildID>/<文件名>` 的结构原样搬过去（第 10 篇），否则旧模板和暂停中的沙箱全部无法恢复。

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| RPM | 源码+补丁+内核+定制 FC+部署包，装到 `/opt/e2b-infra` |
| `dep/` 覆盖 | `-i` 用部署包版本覆盖上游版本，实际生效的是 `dep/` |
| nbd 前提 | 手工固化自编译模块，`nbds_max=512`；升级内核要重做 |
| `-i` | 装 MinIO、Harbor、nginx、SDK 和补丁 |
| `-s` | 起 Harbor；建目录、交换文件、tmpfs、udev 规则、大页；放内核、FC、envd；提交四个 job |
| 先删再拷 | 避开 `Text file busy` |
| 32 GiB 上限 | 记 orchestrator 堆和页缓存，不记客户机大页 |
| `-d` | 停进程、杀 Firecracker；不动模板、缓存、大页 |
| 孤儿 COW | 被强杀的沙箱留在 `/orchestrator/sandbox` 的文件不会被自动清理 |
| 特性开关 | 本环境全用代码默认值 |
| 改配置 | 改源头、`-r` 重跑单个 job、看进程环境变量确认 |

**下一篇预告**：[《全景、容量规划与排障》](19-big-picture-capacity-troubleshooting.md)。全书最后一篇。把一个沙箱从模板构建到删除的完整一生复盘一遍，看每一步数据在哪、谁在读写；然后算一笔这套环境的容量账，特别是“哪些存储其实在吃内存”；最后给出按层排查的思路、常用工具和常见问题速查表。
