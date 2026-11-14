# 第 16 篇｜配置全景：一个参数从哪来、到哪去

> **本篇目标**：把散落在各处的配置收拢到一起。先列出配置存在的六个地方，再完整追踪一个变量从 `.env` 到进程的旅程，讲清楚三种“改了没用”的典型原因（以 MinIO 为例）。然后把 `.env` 分类讲一遍，每类说明本环境的值、作用、改了影响什么；再列出不在 `.env` 里、但同样重要的参数。最后给一张“要改 X，动哪几处”的速查表。这一篇适合当手册查。

---

## 一、配置在哪：六个地方

![配置的六个来源](img/16-1-配置来源.svg)

| # | 地方 | 例子 | 谁读它 |
|---|---|---|---|
| 1 | `.env`（`dep/.env` 和根目录 `.env`） | `API_PORT=3000`、`SANDBOXES_HOST_NETWORK_CIDR` | `build.sh`、`deploy.sh`、`start-*.sh`、`init-client.sh` |
| 2 | job 模板 `nomad/*.hcl` | `static = "${API_PORT}"`、`memory = 32768` | `deploy.sh` 的 `envsubst` |
| 3 | 渲染结果 `rendered/*.hcl` | `static = "3000"` | Nomad |
| 4 | 脚本里写死的值 | `build.sh` 的 `HARBOR_PASSWORD="Harbor12345"` | 脚本自己 |
| 5 | 编译进二进制的默认值 | 默认内核版本 `vmlinux-6.1.158`、槽位池大小 300/1000 | 程序自己 |
| 6 | 系统配置文件 | `/etc/nomad.d/default.hcl`、`/etc/dnsmasq.conf`、`/etc/sysctl.conf` | Nomad、dnsmasq、内核等 |

其中 1、2 有两份：仓库里的（`e2b-deploy/dep/`）和机器上的（`/opt/e2b-infra/`）。机器上的又分 `dep/` 下的原件和根目录的覆盖结果（第 8 篇）。

---

## 二、一个变量的旅程

以沙箱网络地址池 `SANDBOXES_HOST_NETWORK_CIDR` 为例，跟着它走一遍：

![一个变量的旅程](img/16-2-变量旅程.svg)

```
① 仓库：e2b-deploy/dep/.env
     export SANDBOXES_HOST_NETWORK_CIDR=10.13.0.0/16
        │  rpmbuild 打进包
② /opt/e2b-infra/dep/.env
        │  build.sh -i：cp 到根目录
③ /opt/e2b-infra/.env
        │  deploy.sh：source，set -a 导出
④ deploy.sh 进程的环境变量
        │  envsubst（变量必须在白名单里）
⑤ nomad/template-manager.hcl 里的
     SANDBOXES_HOST_NETWORK_CIDR = "${SANDBOXES_HOST_NETWORK_CIDR}"
   变成 rendered/template-manager.hcl 里的
     SANDBOXES_HOST_NETWORK_CIDR = "10.13.0.0/16"
        │  nomad job run
⑥ Nomad 保存的 job 定义
        │  Nomad 启动任务
⑦ /usr/bin/template-manager 进程的环境变量
        │  Go 代码读环境变量
⑧ orchestrator 用 10.13.0.0/16 分配沙箱地址
```

八个环节，任何一个环节断了，你在 ① 改的值都到不了 ⑧。同一个变量还会被 `build.sh -d` 的清理逻辑读（③ 那份），用来判断哪些 iptables 规则是自己的（第 18 篇）。

验证时**从后往前**查最快：

```bash
# ⑦ 进程实际拿到的值（最终真相）
tr '\0' '\n' < /proc/$(pgrep -f '^/usr/bin/template-manager' | head -1)/environ | grep SANDBOXES

# ⑥ Nomad 里的 job 定义
nomad job inspect template-manager-system | grep -A1 SANDBOXES

# ⑤ 渲染结果
grep SANDBOXES /opt/e2b-infra/rendered/template-manager.hcl

# ③ 根目录 .env
grep SANDBOXES /opt/e2b-infra/.env
```

哪一层的值和你预期的不一样，问题就在那一层和它上一层之间。

---

## 三、三种“改了没用”

### 3.1 被写死的值压过了：MinIO 为什么没用上

`.env` 里写着：

```bash
export STORAGE_PROVIDER=MinioBucket
```

但模板实际存在本地目录，MinIO 里空空如也。原因在 ⑤：`dep/template-manager.hcl` 里这一行是**写死的**：

```hcl
STORAGE_PROVIDER = "Local"
```

而不是 `STORAGE_PROVIDER = "${STORAGE_PROVIDER}"`。`envsubst` 没有东西可替换，`.env` 里的值根本没机会进入 job。

这类问题的特征是：**`.env` 改了，`rendered/` 里没变**。

同类的还有：

| hcl 里写死的 | `.env` 里对应的值 | 实际生效 |
|---|---|---|
| `STORAGE_PROVIDER = "Local"` | `MinioBucket` | Local |
| api 的 `ENVIRONMENT = "dev"` | `local` | dev |
| api、redis、template-manager 的 `resources` | （`.env` 里没有对应项） | hcl 里的数字 |
| client-proxy 的 `ENVIRONMENT = "dev"` | `local` | dev |

想让某个值可以从 `.env` 控制，要把 hcl 里的字面值改成 `${变量名}`，并且确认这个变量在 `envsubst` 的白名单里（下一节）。

### 3.2 不在白名单里

第 14 篇讲过，`deploy.sh` 的 `envsubst` 带了一份白名单，只替换列出的变量。如果你：

1. 在 `.env` 里新加了一个变量 `MY_NEW_VAR=abc`；
2. 在 hcl 里写了 `MY_NEW_VAR = "${MY_NEW_VAR}"`；
3. 但忘了在 `deploy.sh` 的白名单里加 `$MY_NEW_VAR`；

那么 `rendered/` 里会**原样保留** `"${MY_NEW_VAR}"`，而不是 `"abc"`。

特征是：**`rendered/` 里还能看到 `${...}`**。查一下：

```bash
grep -n '\${[A-Z_]*}' /opt/e2b-infra/rendered/*.hcl
```

（注意区分 `$${...}`，那是有意留给 Nomad 运行时填的。）

### 3.3 改错了层

几种常见的“改错层”：

| 改了 | 为什么没用 / 被覆盖 |
|---|---|
| `rendered/*.hcl` | 下次 `deploy.sh` 或 `build.sh -r` 重新渲染，被覆盖 |
| 根目录 `/opt/e2b-infra/.env` | 下次 `build.sh -i` 用 `dep/.env` 覆盖 |
| `/opt/e2b-infra/nomad/template-manager.hcl` | 下次 `build.sh -i` 用 `dep/template-manager.hcl` 覆盖；下次 `rpm -Uvh` 换回上游版 |
| `/opt/e2b-infra/dep/.env` | 下次 `rpm -Uvh` 换回仓库里的版本 |
| 只改了文件，没重新提交 job | 文件对了，但 Nomad 里还是旧定义，进程还是旧环境 |

**持久的改法**是改仓库里的源头 `e2b-deploy/dep/...`，重新打包；临时验证可以改机器上的文件，但要知道它会被哪一步覆盖。第 19 篇有完整的流程。

还有一种情况：值改对了、job 也重新提交了，但**进程没有重启**。Nomad 只在 job 定义有差异时才替换 alloc（第 4 篇）。环境变量变了算差异，会自动重启；只换了二进制、hcl 没变，就不算差异（第 19 篇）。

---

## 四、`.env` 分类讲解

`.env` 一百多行，按用途分成几组。“生效吗”一列标明这个值在本环境里有没有实际作用。

### 4.1 本机与基础

| 变量 | 本环境的值 | 作用 | 生效吗 |
|---|---|---|---|
| `SERVER_IP` | 本机 IP | 一切地址的根；`build.sh` 读它 | 是，最关键 |
| `SERVER_IPS` | `$SERVER_IP` | Consul/Nomad server 列表 | 是 |
| `NUM_SERVERS` | 1 | Nomad 等几个 server | 是 |
| `ENVIRONMENT` | `local` | 环境名 | 部分（多处被 hcl 写死成 `dev`） |
| `GCP_ZONE` | `dc1` | Nomad 的数据中心名（名字是上游遗留） | 是 |
| `DOMAIN_NAME` | 写了两次，后者为 `domain_name` | 上游的域名 | 否 |

`SERVER_IP` 那一行没有 `export`，但 `build.sh` 是用 `source` 读的，同一个 shell 里照样能用。

### 4.2 版本

| 变量 | 值 | 说明 |
|---|---|---|
| `NOMAD_VERSION` | 1.11.2 | 决定 `-i` 拷哪个 zip、`-s` 装哪个版本。至少 1.11.2 |
| `CONSUL_VERSION` | 1.21.4 | 实际不决定版本：`-i` 拷的文件名写死了 1.21.4，`install-consul.sh` 用的是固定路径 `/tmp/consul.zip` |
| `REDIS_VERSION` | 7.4.4-alpine | `deploy.sh` 推哪个 redis 镜像、job 拉哪个 |
| `CLICKHOUSE_VERSION`、`LOKI_VERSION` 等 | | 没部署，不生效 |

### 4.3 凭证与令牌

| 变量 | 值 | 作用 | 要注意 |
|---|---|---|---|
| `NOMAD_ACL_TOKEN` | 占位值，`-s` 后被替换成真令牌 | `deploy.sh` 提交 job、api 查节点 | 和集群不一致就 403 |
| `CONSUL_ACL_TOKEN` | 同上 | Nomad 连 Consul、orchestrator 用 | 同上 |
| `API_ADMIN_TOKEN` | `dev_admin` | api 管理接口 | 默认值，建议改 |
| `SANDBOX_ACCESS_TOKEN_HASH_SEED` | 一个 UUID | 生成沙箱访问令牌 | 建议随机生成 |
| `EDGE_API_SECRET` | 一个 UUID | 传给 orchestrator 作 `API_SECRET` | |
| `HARBOR_USERNAME`、`HARBOR_PASSWORD` | `admin` / `Harbor12345` | | 和 `build.sh` 写死的要一致 |
| `MINIO_ACCESS_KEY`、`MINIO_SECRET_KEY` | `minioadmin` | | 和 `minio.yml` 要一致；当前不生效 |

注意两个 ACL 令牌的特殊性：仓库里的值只是占位，真值是运行时生成的（第 12 篇）。所以**不要把根目录 `.env` 里的真令牌提交回仓库**，也不要用 `dep/.env` 覆盖根目录 `.env`。

### 4.4 数据库、Redis、镜像仓库

| 变量 | 值 | 作用 |
|---|---|---|
| `POSTGRES_CONNECTION_STRING` | `postgresql://postgres:local@localhost:5432/mydatabase?sslmode=disable` | api、db-migrator、seed-db 连数据库；账号密码库名要和 `build.sh` 里启动容器时的一致 |
| `REDIS_URL` | `redis.service.consul` | api、client-proxy 找 Redis，靠 Consul DNS |
| `REDIS_PORT` | 6379 | |
| `SANDBOX_STORAGE_BACKEND` | `redis` | 沙箱目录存 Redis |
| `REGISTRY_URL` | `$SERVER_IP:2900/e2b-orchestration` | 镜像推到哪、job 从哪拉 |
| `HARBOR_HOST` | `$SERVER_IP:2900` | 给 orchestrator 的镜像仓库地址 |

### 4.5 端口

| 变量 | 值 |
|---|---|
| `API_PORT` / `API_GRPC_PORT` | 3000 / 5009 |
| `EDGE_API_PORT` / `EDGE_PROXY_PORT` / `EDGE_HEALTH_PORT` | 3001 / 3002 / 3003 |
| `ORCHESTRATOR_PORT` / `ORCHESTRATOR_PROXY_PORT` | 5008 / 5007 |
| `TEMPLATE_MANAGER_PORT` | 5008（和 orchestrator 同一个进程） |
| `REDIS_PORT` | 6379 |

改端口要小心：

- `EDGE_PROXY_PORT` 改了，`build.sh` 里 iptables 规则写死的 `--to-port 3002` 也要改；
- `API_PORT` 改了，SDK 的 `E2B_API_URL` 也要改；
- `ORCHESTRATOR_PORT` 改了，api 的代码里有一个编译进去的常量也是 5008，要一致。

### 4.6 沙箱网络

| 变量 | 值 | 说明 |
|---|---|---|
| `SANDBOXES_HOST_NETWORK_CIDR` | `10.13.0.0/16` | 宿主机访问沙箱用的地址池 |
| `SANDBOXES_VRT_NETWORK_CIDR` | `10.14.0.0/16` | 槽位内虚拟网卡对用的地址池 |
| `ALLOW_SANDBOX_INTERNET` | `true` | 沙箱能否上外网 |

上游默认是 `10.11/10.12`，和同机的 AgentENV 完全一样，会撞地址、撞路由，所以改成了 `10.13/10.14`。两段不能互相重叠，也不能和本机、内网在用的网段重叠。`/16` 能分出约三万多个槽位，决定了单机槽位的理论上限。

改了它，`build.sh -d` 的清理逻辑会按新值判断，原来那个地址段上的残留规则就不会被清理到。要先 `-d` 清干净再改。

### 4.7 大页

| 变量 | 值 | 说明 |
|---|---|---|
| `HUGEPAGES_BASE_MAX_MIB` | 65536 | 静态大页池上限（第 13 篇） |

它不经过 `envsubst`，而是 `build.sh` 读 `dep/.env` 后导出，`init-client.sh` 直接从环境变量读。

### 4.8 节点池

| 变量 | 值 |
|---|---|
| `API_NODE_POOL` | `api` |
| `BUILD_NODE_POOL` | `api` |
| `CLICKHOUSE_NODE_POOL` | `api` |

单机时全部是 `api`（第 4 篇）。

### 4.9 存储

| 变量 | 值 | 生效吗 |
|---|---|---|
| `STORAGE_PROVIDER` | `MinioBucket` | **否**，被 hcl 写死成 `Local` |
| `ARTIFACTS_REGISTRY_PROVIDER` | `Local` | 是 |
| `MINIO_ENDPOINT` 等 | | 否 |
| `TEMPLATE_BUCKET_NAME`、`BUILD_CACHE_BUCKET_NAME` | 上游的桶名 | 传进了 orchestrator，但 Local 模式下基本用不到 |
| `SHARED_CHUNK_CACHE_PATH` | 空 | |

### 4.10 留着但不生效的

这一大组是上游配置的“化石”，对应的组件本环境没有部署，或者功能没启用：

- ClickHouse：`CLICKHOUSE_*`（`CLICKHOUSE_SERVER_COUNT=0`）
- Loki、日志：`LOKI_*`、`LOGS_COLLECTOR_*`
- OTel、Grafana：`OTEL_*`、`GRAFANA_*`
- docker-reverse-proxy：`DOCKER_REVERSE_PROXY_*`
- 第三方服务：`SUPABASE_JWT_SECRETS`、`POSTHOG_API_KEY`、`LAUNCH_DARKLY_API_KEY`、`ANALYTICS_COLLECTOR_*`

改它们不会有任何效果。之所以还留着，是因为 job 模板里引用了它们：删掉后 `envsubst` 会把引用处填成空值，各服务能不能接受空值没有逐一验证过，保守起见别删。

---

## 五、不在 `.env` 里的重要参数

| 参数 | 在哪 | 值 | 改了影响什么 |
|---|---|---|---|
| PostgreSQL 账号、密码、库名、端口 | `build.sh` 的 `install_postgre` | `postgres` / `local` / `mydatabase` / 5432 | 要和 `.env` 的连接串一起改 |
| Harbor 端口、账号 | `build.sh` 开头 | 2900、`admin` / `Harbor12345` | 要和 `.env`、docker 的 `insecure-registries` 一起改 |
| MinIO 端口、账号 | `dep/minio.yml`、`minio.service` | 9000/9001、`minioadmin` | |
| 80 → 3002 | `build.sh` 的 `start()` 末尾 | | 改 client-proxy 端口时要同步 |
| template-manager 内存、CPU | `dep/template-manager.hcl` | 32768 MiB、2048 MHz | 第 15 篇 |
| api 内存、CPU | `nomad/api.hcl`（补丁里） | 20480 MiB、20000 MHz | |
| `kill_timeout` | 各 hcl | 30s | 受 Nomad 上限约束 |
| `MAX_STARTING_INSTANCES_PER_NODE` | `dep/template-manager.hcl` | 30 | 并发启动沙箱的上限 |
| 槽位池大小 | 补丁里的 Go 常量 | 新建 300、回收 1000 | 要改代码 |
| 默认内核版本 | api 代码里的常量 | `vmlinux-6.1.158` | 和 `/fc-kernels` 的目录名对应 |
| Firecracker 版本目录 | `init-client.sh` | `v1.13.1` | 和代码里查找的版本对应 |
| 大页切分比例 | `init-client.sh` | 保留 16%（4～42 GiB），静态 20%，超分配 80% | |
| nbd 设备数 | `/etc/modprobe.d/nbd.conf` | 512 | 单机同时运行沙箱的上限之一 |
| `/mnt/snapshot-cache` 大小 | `start-client.sh` | 65G | |
| swap 大小 | `start-client.sh` | 1G | |
| SDK 版本 | `build.sh` 的 `install_e2b` | 2.20.0 / 2.4.1 | 和服务端、SDK 补丁绑定 |
| 种子邮箱 | `deploy.sh` | `admin@e2b.dev`，可用 `SEED_EMAIL` 覆盖 | |
| 配额 | `deploy.sh` 末尾的 SQL | 10000 / 10000 | |

---

## 六、速查：要改 X，动哪几处

| 要改 | 持久改法：改仓库里的这些 | 然后 |
|---|---|---|
| 本机 IP | `dep/.env` 的 `SERVER_IP`；docker 的 `insecure-registries` | 重新打包或改 `/opt/e2b-infra/dep/.env`，`-d`、`-i`、`-s` |
| 沙箱地址池 | `dep/.env` 的两个 CIDR | 先 `-d` 清干净，再改，再 `-s` |
| template-manager 内存 | `dep/template-manager.hcl` 的 `resources` | 改机器上 `nomad/template-manager.hcl` 后 `build.sh -r template-manager` |
| template-manager 的某个环境变量 | `dep/template-manager.hcl` 的 `env` | 同上 |
| 存储切到 MinIO | `dep/template-manager.hcl` 的 `STORAGE_PROVIDER`；MinIO 里建桶；搬运已有模板 | 按仓库 `deploy-docs/10` 的步骤 |
| 大页上限 | `dep/.env` 的 `HUGEPAGES_BASE_MAX_MIB` | 下次 `-s` 生效（最好先 `--purge-hugepages`） |
| Nomad 版本 | `dep/.env` 的 `NOMAD_VERSION`；`dep/` 下放对应 zip | `-d`、`-i`、`-s` |
| Harbor 密码 | `build.sh`、`dep/.env`、Harbor 里的账号 | `-d`、`-i`、`-s` |
| api 端口 | `dep/.env` 的 `API_PORT`；SDK 的 `E2B_API_URL` | `build.sh -r api` |
| client-proxy 端口 | `dep/.env` 的 `EDGE_PROXY_PORT`；`build.sh` 的 iptables 规则 | `-s` |
| 新增一个给 job 的变量 | `dep/.env`；hcl 里写 `${变量}`；`deploy.sh` 的白名单 | `build.sh -r <job>` |

这张表里的“然后”，第 19 篇会按场景展开。

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| 六个地方 | `.env`、job 模板、渲染结果、脚本写死、二进制默认值、系统配置 |
| 变量的旅程 | `.env` → source → envsubst → rendered → Nomad → 进程环境变量 → 代码 |
| 从后往前查 | 先看 `/proc/<pid>/environ`，再往上一层层对 |
| 被写死的值压过 | hcl 里写字面值，`.env` 没机会进来；MinIO 没用上就是这样 |
| 不在白名单里 | `rendered/` 里还留着 `${...}` |
| 改错了层 | `rendered/`、根目录 `.env`、根目录脚本都会被覆盖；持久改法是改仓库源头 |
| 两个 ACL 令牌 | 仓库里是占位，真值运行时生成，别覆盖 |
| 化石配置 | ClickHouse、Loki、OTel 等，改了没用，但不能删 |

**下一篇预告**：[《部署好了没有：验证与第一台沙箱》](17-verify-and-first-sandbox.md)。进入第四部分。部署脚本说“成功”不等于真能用。本篇给出一套自下而上的验证顺序，再用 SDK 建第一个模板、开第一台沙箱，把一次请求在全景图上走一遍，看它用到了部署的哪些部分。
