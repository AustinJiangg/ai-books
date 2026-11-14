# 第 8 篇｜存数据的数据：Harbor、PostgreSQL 与 Redis

> **本篇目标**：前一篇讲了模板的六个文件。可光有文件还不够：哪个模板现在用的是哪个 build？暂停中的沙箱对应哪个快照？正在运行的沙箱在哪台机器上？做模板的原料镜像放在哪？这些“关于数据的数据”分别存在三个组件里：Harbor、PostgreSQL、Redis。本篇讲清楚它们各存什么、在这套环境里怎么装、数据落在哪、谁来读写，以及它们和 `/tmp/templates` 里的文件对不上时会出什么问题。

---

## 一、文件之外，还要记什么

设想 SDK 发来一个请求：“用模板 `base` 创建一个沙箱”。orchestrator 能干活之前，有好几个问题要先回答：

| 问题 | 谁来回答 |
|---|---|
| `base` 是哪个模板？它现在的标签 `default` 指向哪个 buildID？ | PostgreSQL |
| 这个 team 还能不能再开沙箱？配额多少？ | PostgreSQL |
| 新沙箱开在哪台机器上？开好以后，访问它的请求该转给谁？ | Redis |
| 这个模板最初是用哪个镜像做的？api、client-proxy 这些服务本身的镜像从哪拉？ | Harbor |

这三个组件存的都不是沙箱的磁盘或内存，而是**指向**这些数据的记录和原料。本书叫它们“存数据的数据”。

![三个存数据的数据的组件](img/08-1-三个组件.svg)

下面这张表先给个全貌，后面逐个展开：

| 组件 | 存什么 | 这套环境怎么跑 | 数据在哪 | 谁读写 |
|---|---|---|---|---|
| Harbor | 做模板的原料镜像；api、client-proxy、db-migrator、redis 的服务镜像 | 一组 docker compose 容器，`-s` 启动 | 宿主 `/data` | 建模板时 template-manager 拉；Nomad 起服务时拉 |
| PostgreSQL | 团队、配额、模板、别名、build、快照的记录 | 一个 `docker run` 起的容器，端口 5432 | 容器的匿名数据卷 | api |
| Redis | 正在运行的沙箱的状态、它在哪台机器上 | Nomad 的 `redis` job，端口 6379 | 容器内存，没有持久卷 | api、client-proxy |

注意 orchestrator 一个都不直接读写 PostgreSQL 和 Redis。它只认 api 发来的 buildID，然后去存储后端找文件（第 10 篇）。

---

## 二、Harbor：镜像仓库

### 2.1 镜像仓库存什么

**镜像仓库**（registry）是一个按“名字:标签”存取容器镜像的 HTTP 服务。一个镜像的完整名字是：

```
harbor:443 / e2b-orchestration / ubuntu : 22.04-custom
└──┬────┘    └──────┬───────┘   └─┬──┘   └────┬─────┘
 仓库地址          项目          仓库名        标签
```

一个镜像在仓库里由三类东西组成，都按内容的 sha256 命名：

| 组成部分 | 是什么 |
|---|---|
| **清单**（manifest） | 一个小 JSON，列出这个镜像由哪个配置、哪几层组成 |
| **配置**（config） | 平台（`linux/arm64`）、环境变量、工作目录、默认启动命令 |
| **层**（layer） | 一个个 `tar.gz`，每层记录相对下层的文件改动（第 5 篇） |

按内容命名的好处是**去重**：两个镜像共享同一个 ubuntu 基础层，仓库里只存一份。标签只是一个指向某份清单的可变指针。

![镜像在仓库里怎么存](img/08-2-镜像在仓库里.svg)

同一个名字可以对应多个平台的镜像。ARM 补丁把 template-manager 拉镜像时的平台**固定为 `linux/arm64`**，拉下来还会检查一遍。往 Harbor 推了一个 x86 镜像，用它建模板会直接报平台不匹配。

**Harbor** 在标准仓库服务外面加了项目、用户权限和网页界面，自己由一组容器组成（核心服务、仓库服务、自带的数据库和 Redis、入口 nginx 等）。它自带的数据库和 Redis 只给 Harbor 自己用，和下面讲的 E2B 的 PostgreSQL、Redis 毫无关系。

### 2.2 这套环境里 Harbor 存了两类镜像

| 镜像 | 谁推进去 | 谁拉 |
|---|---|---|
| 模板原料 `e2b-orchestration/ubuntu:22.04-custom` | `build.sh -s` 的 `push_base_image`：`docker load` RPM 里带的 `ubuntu-22.04-custom.tar.gz` 再推送 | 建模板时 template-manager |
| 服务镜像 `api`、`client-proxy`、`db-migrator`、`redis:7.4.4-alpine` | `deploy.sh`：在 `/opt/e2b-infra/bin` 下按各 Dockerfile 构建，再 `docker push` 到 `<本机IP>:2900/e2b-orchestration/` | Nomad 启动 api、edge、redis 这几个 job 时 |

第二类很容易被忽略：**Harbor 不只是建模板用的**。如果 Harbor 没起来，Nomad 重新调度 api、edge、redis 这几个 job 时就拉不到镜像。

### 2.3 怎么装

安装分散在 `build.sh -i` 和 `-s` 两步：

- **`-i`**：解压社区构建的 aarch64 离线包 `harbor-offline-installer-aarch64-v2.13.0.tgz`（官方没有 aarch64 离线包），改 `harbor.yml`：关掉 https、主机名改成本机 IP、HTTP 端口改成 2900。数据目录用默认的 `/data`。再装一个 nginx，`server_name harbor`、`listen 443 ssl`，反代到 `127.0.0.1:2900`；生成自签证书，装进系统信任库和 `/etc/docker/certs.d/harbor:443/`。
- **`-s`**：执行 Harbor 的 `install.sh` 拉起容器，修正配置目录属主（容器里的进程以 UID 10000 运行），`docker login`，用 REST API 建一个**公开**项目 `e2b-orchestration`（拉取不用登录），往 `/etc/hosts` 写 `<本机IP> harbor` 并重启 dnsmasq，最后推基础镜像。

### 2.4 同一个仓库，两个门

推送和拉取用的不是同一个地址：

![推送和拉取的两个地址](img/08-3-两个地址.svg)

- **推送走 `<本机IP>:2900`（HTTP）**：docker daemon 要用 http 必须把地址加进 `daemon.json` 的 `insecure-registries`。不用 `harbor:443` 推，是因为 docker daemon 配了代理时，它的 `NO_PROXY` 一般不认识只写在本机 `/etc/hosts` 里的 `harbor`，请求被转给代理，返回 504。
- **拉取走 `harbor:443`（HTTPS）**：template-manager 不经过 docker daemon，而是用 Go 的 go-containerregistry 库直接按 registry 协议拉，要求 HTTPS 且证书名对得上。名字 `harbor` 靠 dnsmasq 读 `/etc/hosts` 解析，证书靠系统信任库和 `dep/template-manager.hcl` 里的 `SSL_CERT_FILE`。

所以 docker daemon 的代理、`insecure-registries` 设置，对 template-manager 都不起作用。

### 2.5 `ARTIFACTS_REGISTRY_PROVIDER=Local`

`.env` 里还有这一行。它对应 E2B 的另一种取镜像方式：按“模板 ID:buildID”去本机 docker daemon 里找镜像，给官方云部署那种“先在别处把 Dockerfile 构建成镜像”的流程用。这套环境建模板走的是 `FROM` 指定镜像那条路，不走这里。

---

## 三、PostgreSQL：模板和 build 的账本

### 3.1 怎么装、数据在哪

`build.sh -i` 的 `install_postgre` 是一条 `docker run`：

```bash
docker run -d --name postgres \
    -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=local -e POSTGRES_DB=mydatabase \
    -p 5432:5432 --restart=always \
    --health-cmd="pg_isready -U postgres" \
    postgres:latest
```

api 用 `.env` 里的连接串访问它：

```bash
POSTGRES_CONNECTION_STRING="postgresql://postgres:local@localhost:5432/mydatabase?sslmode=disable"
```

注意命令里**没有 `-v`**，没有把数据目录映射到宿主机。PostgreSQL 官方镜像声明了一个数据卷，docker 会自动建一个**匿名卷**放数据，在 `/var/lib/docker/volumes/<一串哈希>/_data` 下。这带来一个容易踩的坑，第五节讲。

### 3.2 表是谁建的、初始数据是谁写的

- **建表**：api 这个 Nomad job 里有一个 `db-migrator` 任务，作为启动前的钩子（prestart）先跑完。它是一个基于 goose 的小程序，按顺序执行 `packages/db/migrations/` 下的迁移脚本（这一版有 85 个），把表结构升到最新。RPM 也把这些脚本装到了 `/opt/e2b-infra/bin/migrations`。
- **初始数据**：`deploy.sh` 最后查一下有没有名叫 `E2B` 的 team，没有就运行 `seed-db`，建一个 team、一个用户、访问令牌和 API key，并把它们写进 `/root/.e2b/config.json` 给 SDK 用。
- **放开配额**：`deploy.sh` 还会执行一条 SQL，把 `base_v1` 这一档的并发沙箱数和最长存活时间都改成 10000。

### 3.3 和存储有关的几张表

数据库里有十几张表，和本书相关的是这几张：

| 表 | 一行代表什么 | 关键列 |
|---|---|---|
| `envs` | 一个模板（快照在这里也算一种模板） | `id`：模板 ID |
| `env_aliases` | 模板的别名，比如 `base` | `alias` → `env_id` |
| `env_builds` | 一个 build | `id` **就是 buildID**；`status`；`vcpu`、`ram_mb`、磁盘大小；`kernel_version`、`firecracker_version`、`envd_version` |
| `env_build_assignments` | 模板的某个标签指向哪个 build | 模板 ID、`tag`（如 `default`）、buildID |
| `snapshots` | 一个暂停中的沙箱 | `sandbox_id`、对应的快照模板 ID、`base_env_id`（最初的模板） |
| `teams`、`tiers`、`team_api_keys`… | 团队、配额档位、密钥 | 第 3.2 节说的初始数据 |

从一个名字找到文件，走的是这样一条链：

![数据库里的记录怎么指到文件](img/08-4-记录指到文件.svg)


暂停一个沙箱时（第 14 篇），api 在一个事务里写四张表：`envs` 里给这个快照建一个模板，`snapshots` 里记下“这个沙箱 ID 对应这个快照模板”，`env_builds` 里插一条新 build 得到新的 buildID，`env_build_assignments` 里让快照模板的标签指向它。恢复时反过来查，拿到 buildID 交给 orchestrator。

第 7 篇说过的那个误会也在这里解开：SDK 返回的 `l1xjsvf1d8h3umr8d11y:default` 是“模板 ID:标签”，要经过 `env_build_assignments` 才能查到 buildID。

### 3.4 删除只删这里

用户通过 API 删模板、删快照时，api 只删 PostgreSQL 里的这些行（删 `envs` 这一行，数据库会级联删掉它的别名、标签指派等关联行），**不删 `/tmp/templates` 里的文件**。理由是 build 是分层的 diff，可能还被别的 build 的 header 引用（第 14 篇第七节）。

---

## 四、Redis：运行中的沙箱在哪

### 4.1 怎么装

Redis 是 Nomad 提交的四个 job 之一（`dep/deploy.sh` 的 `JOBS` 里排第一个）：

```hcl
job "redis" {
  task "start" {
    driver = "docker"
    config {
      network_mode = "host"
      image        = "<本机IP>:2900/e2b-orchestration/redis:7.4.4-alpine"   # 从 Harbor 拉
      args         = ["redis-server", "--port", "6379"]
    }
  }
}
```

它在 Consul 里注册为 `redis` 服务，api 和 client-proxy 用 `redis.service.consul:6379` 访问它（DNS 见《E2B 沙箱网络从零讲透》第 17 篇）。

**没有挂任何持久卷**。Redis 的数据在这个容器里；Nomad 重新调度这个 job（重启、`build.sh -d` 后再 `-s`、宿主重启）时，新容器从空的开始。

### 4.2 api 用它记沙箱状态

`.env` 里有一行：

```bash
export SANDBOX_STORAGE_BACKEND=redis
```

它决定 api 把“正在运行的沙箱”记在哪：

| 取值 | 含义 |
|---|---|
| `memory` | 主存储在 api 进程内存里，同时写一份到 Redis |
| `redis`（本环境） | **Redis 就是主存储**，预留沙箱名额的记录也放在 Redis |

api 在 Redis 里用 `sandbox:storage:…` 开头的一组键记每个沙箱：属于哪个 team、什么时候过期、当前处于什么状态（运行、暂停中……），状态切换时还会写 `transition:…` 键，防止两个操作同时改同一个沙箱。

### 4.3 client-proxy 用它找沙箱

SDK 访问 `49983-<沙箱ID>.e2b.app` 时，入口的 client-proxy 要知道这个沙箱在哪台机器的 orchestrator 上（网络书第 18 篇）。它查的就是 Redis 里的**沙箱目录**：

```
键：  sandbox:catalog:<沙箱ID>
值：  {"orchestrator_id": "…", "orchestrator_ip": "…", "execution_id": "…",
       "sandbox_started_at": "…", "sandbox_max_length_in_hours": …}
```

client-proxy 在本地缓存查到的结果 500 毫秒，每次查 Redis 最多等 1 秒。单机部署里答案永远是本机，但这一步照样要走。

### 4.4 orchestrator 不碰 Redis

`dep/template-manager.hcl` 里没有 `REDIS_URL`。orchestrator 自己在进程内存里知道本机跑着哪些沙箱，不依赖 Redis。所以 Redis 数据丢了，沙箱进程本身照样在跑，但 api 和 client-proxy 不再知道它们，SDK 也就找不到它们了。

---

## 五、记录和文件对不上的时候

三个组件和 `/tmp/templates` 里的文件，生命周期各不相同。下面这些事件发生时，它们会“对不上”：

| 事件 | 文件（`/tmp/templates`） | PostgreSQL | Redis | 表现 |
|---|---|---|---|---|
| 宿主重启 | **全丢**（tmpfs） | 还在（容器 `--restart=always` 自动起来，数据卷还在） | 丢（容器重建） | 模板和别名还在数据库里，但文件没了：用它建沙箱报“对象不存在”；重建模板报别名已被占用，要先删掉旧记录 |
| 重跑 `build.sh -i` | 还在 | **清空**：`install_postgre` 先 `docker rm` 旧容器再新建，新容器配一个新的匿名卷 | 不受影响 | 文件都在，但数据库不认识它们了：所有模板、快照记录消失，要重新 seed、重新建模板；旧文件成了没人引用的孤儿 |
| 通过 API 删模板或快照 | 还在 | 删除相关行 | — | 设计如此，`/tmp/templates` 只增不减 |
| Redis job 重新调度 | — | — | 清空 | 正在运行的沙箱从 api 和 client-proxy 眼里消失，但进程还在跑 |
| Harbor 没起来 | — | — | — | 建模板拉不到原料；Nomad 重新调度 api、edge、redis 时拉不到服务镜像 |

第二行值得特别留意：`build.sh -i` 不是“只装缺的东西”，它会**重建** PostgreSQL 容器。旧的匿名卷不会被删，还留在 `/var/lib/docker/volumes/` 下，但新容器不会用它。

---

## 六、看一眼

```bash
# Harbor：基础镜像在不在
curl -s -u admin:Harbor12345 http://127.0.0.1:2900/v2/e2b-orchestration/ubuntu/tags/list
#   {"name":"e2b-orchestration/ubuntu","tags":["22.04-custom"]}

# PostgreSQL：别名 base 现在指向哪个 build
docker exec postgres psql -U postgres -d mydatabase -c "
  SELECT a.alias, b.tag, b.build_id
  FROM env_aliases a JOIN env_build_assignments b ON b.env_id = a.env_id
  WHERE a.alias = 'base';"
ls /tmp/templates/<上面查到的 build_id>/

# PostgreSQL 的数据卷在哪
docker inspect postgres --format '{{range .Mounts}}{{.Source}}{{end}}'

# Redis：现在记着哪些沙箱
redis-cli -h 127.0.0.1 -p 6379 --scan --pattern 'sandbox:catalog:*' | head
```

（`redis-cli` 宿主上不一定装了，可以用 `docker exec` 进 Redis 容器执行。）

---

## 七、常见问题

| 现象 | 原因 | 看哪里 |
|---|---|---|
| 建模板报 `lookup harbor on 127.0.0.1:53: server misbehaving` | `/etc/hosts` 没有 `harbor`，或加了之后没重启 dnsmasq | `getent hosts harbor` |
| `docker push` 报 504 | 推送地址用了 `harbor:443`，被 docker 的代理设置转走 | 改用 `<本机IP>:2900` |
| `-s` 装 Harbor 时报 `Unsupported config option for services` | 系统里是老版 `docker-compose`，看不懂 Harbor 2.13 的 compose 文件 | 装 Docker Compose v2 |
| 建模板报平台不匹配 | Harbor 里那个标签是 x86 镜像 | 推 arm64 镜像 |
| api、edge 起不来，Nomad 报拉镜像失败 | Harbor 没启动或服务镜像没推进去 | Harbor 状态；`deploy.sh` 的构建推送日志 |
| 重启后建沙箱报“对象不存在” | 文件在 tmpfs 里丢了，数据库记录还在 | `ls /tmp/templates`（第 10 篇） |
| 重建模板报别名已被占用 | 数据库里还有旧模板 | 先通过 API 删掉旧模板，或清理记录 |
| 重跑 `-i` 后模板和快照全没了 | PostgreSQL 容器被重建，数据在旧的匿名卷里 | `docker volume ls`；`/tmp/templates` 文件还在 |
| SDK 连不上一个明明还在跑的沙箱 | Redis 重启丢了沙箱目录 | `sandbox:catalog:<ID>` 键在不在 |

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| 存数据的数据 | 不存磁盘和内存数据本身，而是存“它们在哪、属于谁”的记录和原料 |
| Harbor | 镜像仓库，数据在 `/data`；存模板原料和 api、client-proxy、db-migrator、redis 的服务镜像 |
| 两个门 | 推送走 `<本机IP>:2900`（HTTP），拉取走 `harbor:443`（nginx HTTPS，自签证书） |
| template-manager 拉镜像 | 用 Go 库直接拉，平台固定 `linux/arm64`，不经过 docker daemon |
| PostgreSQL | `docker run` 起的容器，数据在匿名卷；db-migrator 建表，seed-db 写初始数据 |
| `env_builds.id` | 就是 buildID，对应 `/tmp/templates/<buildID>/` |
| 名字到文件 | 别名 → 模板 → 标签指派 → buildID → 目录 |
| Redis | Nomad job，没有持久卷；`SANDBOX_STORAGE_BACKEND=redis` 下是运行中沙箱的主存储 |
| `sandbox:catalog:<ID>` | client-proxy 查沙箱在哪台 orchestrator 上 |
| orchestrator | 不直接读写 PostgreSQL 和 Redis，只认 buildID |
| 对不上 | 重启丢文件和 Redis；重跑 `-i` 清空数据库；删除只删记录 |

**下一篇预告**：[《从 Dockerfile 到 rootfs.ext4：模板构建流水线》](09-template-build-pipeline.md)。原料在 Harbor，账本在 PostgreSQL。下一篇看 template-manager 怎么把镜像一步步变成虚拟机的根盘和一份能毫秒恢复的内存快照：解包、转 ext4、扩容、两次开机、逐步执行模板步骤、层缓存，最后打快照、上传。
