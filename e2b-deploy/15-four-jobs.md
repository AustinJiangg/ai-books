# 第 15 篇｜四个 job 逐个读：谁先起、谁等谁

> **本篇目标**：打开 `/opt/e2b-infra/rendered/` 下提交给 Nomad 的四个 job 文件，逐个读懂。先给一个读 job 文件的顺序，然后依次看 redis、template-manager、client-proxy、api。重点是 template-manager：它的驱动、停止超时、内存配额和环境变量都有讲究。最后把四个 job 串成一条启动依赖链，解释为什么链上任何一环断了，最后都表现为“api 一直 503、部署卡 10 分钟后超时”。末尾附一张全书用到的端口总表。

---

## 一、怎么读一个 job 文件

一个 job 文件几十到上百行，按这个顺序看，很快就能抓住要点：

1. **job 头部**：`type`（service 还是 system）、`node_pool`（去哪个池）、`priority`（优先级）；
2. **task 的 `driver`**：docker 还是 raw_exec；
3. **`network`**：占哪些端口；
4. **`resources`**：要多少 CPU 和内存；
5. **`env`**：给进程的环境变量，也就是它的配置；
6. **`config`**：具体怎么启动（镜像名或命令行）；
7. **`service` 和 `check`**：注册成什么服务、怎么判断健康；
8. **`restart`、`lifecycle`、`kill_timeout`** 这类控制行为的配置。

下面按这个顺序读四个 job。读的是 `rendered/` 下已经填好值的版本。

---

## 二、redis

```hcl
job "redis" {
  datacenters = ["dc1"]
  node_pool   = "api"
  type        = "service"
  priority    = 95

  group "redis" {
    restart {
      interval = "5s"
      attempts = 1
      delay    = "5s"
      mode     = "delay"
    }

    network {
      port "redis" { static = "6379" }
    }

    service {
      name = "redis"
      port = "redis"
      check {
        type     = "tcp"
        interval = "10s"
        timeout  = "2s"
        port     = "6379"
      }
    }

    task "start" {
      driver = "docker"
      resources {
        memory_max = 4096
        memory     = 2048
        cpu        = 1000
      }
      config {
        network_mode   = "host"
        image          = "192.168.10.23:2900/e2b-orchestration/redis:7.4.4-alpine"
        auth_soft_fail = true
        args = ["redis-server", "--port", "6379"]
      }
    }
  }
}
```

逐项看：

| 项 | 值 | 含义 |
|---|---|---|
| 类型 | service | 普通的长期服务 |
| 驱动 | docker | 跑容器 |
| 端口 | 6379 | 固定端口（`static`） |
| 内存 | 2048 MiB，最多 4096 MiB | `memory` 用于调度预留，`memory_max` 是实际可用的上限 |
| 镜像 | 从 Harbor 拉 | 第 14 篇推进去的 |
| 网络模式 | `host` | 容器直接用宿主机的网络，不做端口映射 |
| 健康检查 | 每 10 秒连一下 6379 | |
| 重启 | `mode = "delay"` | 无限重试，每次间隔 5 秒 |

两个值得解释的配置：

**`network_mode = "host"`**：四个 job 里的 docker 容器全都用宿主机网络。好处是简单：容器里监听 6379，宿主机上就是 6379；容器里的 `127.0.0.1` 就是宿主机的 `127.0.0.1`，能直接用本机的 dnsmasq、Consul。代价是容器之间没有网络隔离。单机部署里这不是问题。

**`auth_soft_fail = true`**：拉镜像时如果认证失败，不要直接报错，继续尝试匿名拉取。因为 `e2b-orchestration` 是公开项目，匿名就能拉。旁边的注释写着“合入时需删除”，是一个临时的兼容写法。

**它注册成 Consul 服务 `redis`**，api 和 client-proxy 通过 `redis.service.consul:6379` 找到它（第 4 篇）。

**它存的是什么**：运行中沙箱的目录，即“沙箱 ID → 在哪个节点”。`.env` 里的 `SANDBOX_STORAGE_BACKEND=redis` 就是让 api 用它。Redis 没有配置持久化，重启就清空，但运行中的沙箱本来也会随之失效，所以影响不大。

---

## 三、template-manager-system

这是四个 job 里最重要、也最特别的一个。它就是 orchestrator。文件来自 `dep/template-manager.hcl`（单机版）。

```hcl
job "template-manager-system" {
  datacenters = ["dc1"]
  type        = "system"
  node_pool   = "api"
  priority    = 70

  group "template-manager" {
    network {
      port "template-manager" { static = "5008" }
    }

    service {
      name = "template-manager"
      port = "5008"
      check {
        type         = "grpc"
        interval     = "20s"
        timeout      = "5s"
        grpc_use_tls = false
      }
    }

    task "start" {
      driver       = "raw_exec"
      kill_signal  = "SIGTERM"
      kill_timeout = "30s"

      resources {
        memory = 32768
        cpu    = 2048
      }

      env { ... }

      config {
        command = "/bin/bash"
        args    = ["-c", " chmod +x /usr/bin/template-manager && /usr/bin/template-manager --port 5008"]
      }
    }
  }
}
```

### 3.1 类型和驱动

- **`type = "system"`**：每个符合条件的节点跑一份（第 4 篇）。单机就是一份。
- **`driver = "raw_exec"`**：直接在宿主机上以 root 运行 `/usr/bin/template-manager`，不进容器。它要建网络、写 iptables、开 NBD、用大页、起 Firecracker，这些都需要宿主机的完整权限。

启动命令就是第 12 篇 `start-client.sh` 拷过去的那个二进制，参数 `--port 5008`。

### 3.2 健康检查

用 gRPC 协议的标准健康检查接口，每 20 秒问一次 5008 端口。检查通过后，Consul 里才会有一个健康的 `template-manager` 服务。

### 3.3 `kill_timeout = "30s"`：停服时的 30 秒

停止这个 job 时，Nomad 先发 SIGTERM，等 30 秒，还没退就发 SIGKILL 强杀。

这 30 秒对 orchestrator 很关键。它收到 SIGTERM 后要拆掉“网络槽位暖池”：

- orchestrator 为了开沙箱更快，会预先建好一批网络槽位；
- 本仓库把池子从上游的 32 个新建 + 100 个回收调大到了 300 + 1000；
- 每个槽位在宿主机上有一个网络命名空间、一对虚拟网卡、9 条 iptables 规则；
- 逐个拆，十几秒到几十秒。

30 秒不够时，它会被强杀，没拆完的槽位就永久留在宿主机上。为什么不调大？因为 30 秒是 Nomad client 允许的默认上限，上游原本有一行把上限放宽到 24 小时的配置，被补丁删掉了。所以只能靠事后清理（`build.sh -d` 和 `--recycle-netns`，第 18 篇）。

### 3.4 `resources { memory = 32768 }`：32 GiB 管的是什么

这是最容易误解的一个数字。它**不是**“所有沙箱加起来的内存预算”。

![32 GiB 管什么](img/15-1-内存配额.svg)

Nomad 会把这个 job 的进程放进一个 cgroup，`memory = 32768` 成为这个 cgroup 的内存上限。cgroup 里有：

- orchestrator 进程本身；
- 它启动的每个 Firecracker 进程（子进程默认继承父进程的 cgroup；上游会把它们挪到独立的 cgroup，ARM 补丁把这几行注释掉了）。

但沙箱的客户机内存是**大页**，大页由另一个独立的记账机制（hugetlb 控制器）管理，**不计入这 32 GiB**。所以几百个沙箱的内存再大，也不会撑爆它。

真正计入这 32 GiB 的是：

| 内容 | 什么时候大 |
|---|---|
| orchestrator 自己的堆内存 | 一般几十 MB 到几 GB |
| Firecracker 进程客户机以外的内存 | 每个几十 MB |
| **页缓存** | 建模板时：解压镜像层、写磁盘镜像、写内存快照，一次就是几百 MB 到几 GB |

页缓存是“读写文件时内核顺手缓存的内容”，名义上可以回收，但写出去的脏页要先落盘才能回收。建模板时一口气写几个 GB，落盘跟不上，就可能把这 32 GiB 撑满。

这个数字两个方向都不能错：

| 设置 | 后果 | 现象 |
|---|---|---|
| 太小 | 建模板时 orchestrator 被 OOM 杀掉（退出码 137），Nomad 重试几次后放弃 | api 一直 503 |
| 太大 | 超过节点可分配内存，Nomad 根本调度不上 | `nomad job status` 显示 `Dimension "memory" exhausted`；api 一直 503 |

两种错误最后表现一样，都在 api 上，根因却在这里。32 GiB 是实测能扛住一次完整基础镜像构建、又能在 128 GiB 机器上调度上的值。它曾经被改成 256 GiB，在 128 GiB 的机器上就调度不上了，又改了回来。

`cpu = 2048` 的单位是 MHz，用于调度预留和计算 CPU 权重，不是“绑定 2 个核”。

### 3.5 环境变量

`env` 块是 orchestrator 的全部配置。按用途分组：

| 变量 | 值 | 作用 |
|---|---|---|
| `ORCHESTRATOR_SERVICES` | `orchestrator,template-manager` | 一个进程同时担任两个角色（第 2 篇） |
| `NODE_ID` | `$${node.unique.name}`（Nomad 运行时填） | 节点名 |
| `STORAGE_PROVIDER` | **`Local`**（写死） | 模板存本地目录 |
| `ARTIFACTS_REGISTRY_PROVIDER` | `Local` | 拉基础镜像的方式 |
| `GCP_DOCKER_REPOSITORY_NAME` | `192.168.10.23:2900` | 镜像仓库地址（名字是上游遗留） |
| `SSL_CERT_FILE` | `/etc/docker/certs.d/harbor:443/ca.crt` | 信任 Harbor 的自签证书（第 10 篇） |
| `SANDBOXES_HOST_NETWORK_CIDR` | `10.13.0.0/16` | 沙箱网络地址池，避开同机 AgentENV |
| `SANDBOXES_VRT_NETWORK_CIDR` | `10.14.0.0/16` | 同上 |
| `ALLOW_SANDBOX_INTERNET` | `true` | 沙箱能否访问外网 |
| `E2B_FC_NETNS_EXEC_HELPER` | `/opt/e2b-infra/bin/fc-netns-exec` | Firecracker 启动加速辅助程序 |
| `MAX_STARTING_INSTANCES_PER_NODE` | `30` | 同时处于“启动中”的沙箱最多几个，防止并发启动时互相拖慢 |
| `ENVD_TIMEOUT` | `60s` | 等沙箱里 envd 就绪的超时 |
| `CONSUL_TOKEN` | Consul 令牌 | |
| `MINIO_*` | MinIO 地址和账号 | 因为 `STORAGE_PROVIDER` 是 `Local`，实际不用 |
| `CLICKHOUSE_*`、`OTEL_*`、`LOGS_*` | | 对应组件没部署，不起作用 |

`STORAGE_PROVIDER = "Local"` 是写死在 hcl 里的，不是 `${STORAGE_PROVIDER}`。所以 `.env` 里的 `STORAGE_PROVIDER=MinioBucket` 对它没有任何影响。第 16 篇会以它为例讲配置的优先级。

### 3.6 重启策略

这个 job 没有写 `restart` 块，用的是 Nomad 的默认值：30 分钟内最多重启 2 次，用完就把 alloc 标为失败、不再尝试。所以 orchestrator 如果因为端口被占（上一轮没停干净）或配额太小而连续崩溃，很快就会彻底停下来。

---

## 四、client-proxy（`edge.hcl`）

```hcl
job "client-proxy" {
  node_pool = "api"
  priority  = 80

  group "client-proxy" {
    restart {
      attempts = 2
      interval = "10m"
      delay    = "10s"
      mode     = "fail"
    }
    reschedule {
      delay          = "30s"
      delay_function = "exponential"
      max_delay      = "10m"
      unlimited      = true
    }

    count = 1
    constraint {
      operator = "distinct_hosts"
      value    = "true"
    }

    network {
      port "proxy"  { static = "3002" }
      port "health" { static = "3003" }
    }

    service {
      name = "client-proxy"
      port = "proxy"
      check {
        type     = "http"
        path     = "/health"
        interval = "3s"
        port     = "health"
      }
    }

    task "start" {
      driver = "docker"
      resources {
        memory_max = 6144
        memory     = 4096
        cpu        = 4000
      }
      env {
        NODE_ID     = "$${node.unique.id}"
        NODE_IP     = "$${attr.unique.network.ip-address}"
        HEALTH_PORT = "$${NOMAD_PORT_health}"
        PROXY_PORT  = "$${NOMAD_PORT_proxy}"
        REDIS_URL   = "redis.service.consul:6379"
        ...
      }
      config {
        network_mode = "host"
        dns_servers  = ["127.0.0.1"]
        image        = "192.168.10.23:2900/e2b-orchestration/client-proxy"
      }
    }
  }
}
```

（`env` 里带 `$${...}` 的几行是 Nomad 运行时变量，渲染后原样保留，等 Nomad 启动任务时再填值，第 14 篇讲过。）

要点：

- **文件叫 `edge.hcl`，job 叫 `client-proxy`**。`build.sh -r edge` 重跑的就是它。
- **端口**：3002 承接沙箱流量，3003 做健康检查。
- **`dns_servers = ["127.0.0.1"]`**：容器里的 DNS 指向宿主机的 dnsmasq，这样才能解析 `redis.service.consul`。
- **`count = 1` 和 `distinct_hosts`**：多机时每台机器最多一个实例。单机就是一个。
- **重启与重新调度**：10 分钟内本机重启 2 次失败后，换一台机器重新调度，无限次、指数退避。单机时“换一台”还是这台。
- **`service` 上还有一串 `traefik.*` 标签**：上游用 Traefik 做入口时的路由配置，本环境没有 Traefik，这些标签不起作用。

它依赖 Redis：启动时要连上 Redis，连不上会反复重启。

---

## 五、api

```hcl
job "api" {
  datacenters = ["dc1"]
  node_pool   = "api"
  priority    = 90

  group "api-service" {
    restart { interval = "5s"  attempts = 1  delay = "5s"  mode = "delay" }

    network {
      port "api"  { static = "3000" }
      port "grpc" { static = "5009" }
    }

    service {
      name = "api"
      port = "3000"
      check { type = "http"  path = "/health"  interval = "3s"  timeout = "3s" }
    }
    service {
      name = "api-grpc"
      port = "grpc"
      check { type = "tcp"  interval = "3s" }
    }

    task "start" {
      driver       = "docker"
      kill_timeout = "30s"
      resources {
        memory_max = 40960
        memory     = 20480
        cpu        = 20000
      }
      env {
        ENVIRONMENT                    = "dev"
        NOMAD_TOKEN                    = "<Nomad 令牌>"
        ORCHESTRATOR_PORT              = "5008"
        ADMIN_TOKEN                    = "dev_admin"
        SANDBOX_ACCESS_TOKEN_HASH_SEED = "..."
        POSTGRES_CONNECTION_STRING     = "postgresql://postgres:local@localhost:5432/mydatabase?sslmode=disable"
        REDIS_URL                      = "redis.service.consul:6379"
        SANDBOX_STORAGE_BACKEND        = "redis"
        TEMPLATE_BUCKET_NAME           = "skip"
        ...
      }
      config {
        network_mode = "host"
        dns_servers  = ["127.0.0.1"]
        image        = "192.168.10.23:2900/e2b-orchestration/api"
        args         = ["--port", "3000"]
      }
    }

    task "db-migrator" {
      driver = "docker"
      env {
        POSTGRES_CONNECTION_STRING = "postgresql://postgres:local@localhost:5432/mydatabase?sslmode=disable"
      }
      config {
        network_mode = "host"
        image        = "192.168.10.23:2900/e2b-orchestration/db-migrator"
      }
      resources { cpu = 250  memory = 128 }
      lifecycle {
        hook    = "prestart"
        sidecar = false
      }
    }
  }
}
```

### 5.1 两个 task

同一个 group 里有两个 task：

- **`db-migrator`**：`lifecycle { hook = "prestart", sidecar = false }` 表示它是一个**前置任务**：在主任务启动前运行，跑完就结束（不是常驻的“边车”）。它用 goose 检查 PostgreSQL 的表结构，把缺的迁移逐个执行，最后把版本记在 `_migrations` 表里。
- **`start`**：api 本身。只有 db-migrator 成功退出后才会启动。

这就是第 10 篇说的“表不是 `-i` 建的”：每次 api 启动前，db-migrator 都会把表结构补齐到最新。第一次部署时数据库是空的，它会把所有表建出来；之后再启动，发现已经是最新，什么都不做。

第 14 篇里 `deploy.sh` 查询 `teams` 表之前，api 的 job 已经提交，db-migrator 已经跑过，所以表是存在的。

### 5.2 环境变量

| 变量 | 作用 |
|---|---|
| `NOMAD_TOKEN` | api 用它调 Nomad 的接口，查询“有哪些就绪节点” |
| `ORCHESTRATOR_PORT=5008` | 连每个节点上 orchestrator 的端口 |
| `POSTGRES_CONNECTION_STRING` | 连数据库 |
| `REDIS_URL` + `SANDBOX_STORAGE_BACKEND=redis` | 沙箱目录存 Redis |
| `ADMIN_TOKEN` | 管理接口的令牌 |
| `SANDBOX_ACCESS_TOKEN_HASH_SEED` | 生成沙箱访问令牌用的种子 |
| `TEMPLATE_BUCKET_NAME=skip` | 代码某处要求必须有值，填个占位 |

### 5.3 健康检查：503 的来源

api 的 `/health` 接口有一个特别的逻辑：

```go
// 后台定时检查
if orch.NodeCount() != 0 {
    a.Healthy.Store(true)
}

// /health 接口
if a.Healthy.Load() { 返回 200 } else { 返回 503 "Service is unavailable" }
```

只有发现**至少一个 orchestrator 节点**之后，api 才认为自己健康。发现节点的过程是：

1. 用 `NOMAD_TOKEN` 问 Nomad：现在有哪些状态为 ready 的节点？
2. 对每个节点，连 `<节点地址>:5008`，也就是 orchestrator 的 gRPC 端口；
3. 连上了，节点数加一。

所以 **api 的健康取决于 orchestrator**。orchestrator 没起来，api 的进程本身完全正常，但 `/health` 永远返回 503。

### 5.4 资源

api 声明了 20 GiB 内存、20000 MHz CPU，是四个 job 里最大的。加上其他三个：

| job | memory（调度预留） |
|---|---|
| api | 20480 MiB |
| template-manager | 32768 MiB |
| client-proxy | 4096 MiB |
| redis | 2048 MiB |
| 合计 | 约 58 GiB |

Nomad 按 `memory` 的合计判断能否调度。所以机器的普通内存（不算大页）要留出至少这么多给 Nomad 分配，否则后提交的 job 会调度失败。第 13 篇的大页算法给系统留了 4～42 GiB 普通内存，小内存机器上要注意这两者的关系。

---

## 六、启动依赖链

![启动依赖链](img/15-2-启动依赖链.svg)

把四个 job 和它们依赖的外部组件串起来：

```
PostgreSQL（-i 启动）
   └─► db-migrator 建表 ─► api 启动 ─┐
Redis job 健康 ─► Consul 里有 redis ─┤
                                     ├─► api 发现 orchestrator ─► api /health 200
template-manager 启动，5008 监听 ────┘
Redis ─► client-proxy
```

提交时 api 排在最后，`nomad job run api.hcl` 会等 api 的部署结果：

- api 的健康检查通过，部署成功，`deploy.sh` 继续；
- 一直不通过，Nomad 等满默认的 10 分钟（进度截止时间），把部署标为失败：`Failed due to progress deadline`。

于是，链上**任何一环**断了，最后看到的都是同一个现象：

> api 的 `/health` 一直 503，`deploy.sh` 卡在 api 上，10 分钟后失败。

而真正的原因可能是：

| 断在哪 | 根因举例 | 先看什么 |
|---|---|---|
| orchestrator 没起来 | 端口 5007/5008 被上一轮残留占着 | `nomad job status template-manager-system`；`ss -lntp \| grep 500` |
| orchestrator 起来又死了 | 内存配额太小被 OOM；NBD 模块没加载 | `nomad alloc status`；`dmesg \| grep -i oom` |
| orchestrator 调度不上 | 内存配额太大 | `nomad job status` 里的 `Placement Failure` |
| api 连不上 PostgreSQL | 容器没起来、连接串不对 | db-migrator 的日志 |
| api 拿不到节点列表 | `NOMAD_TOKEN` 不对 | api 的日志 |

所以遇到“api 一直 503”，**第一步应该去看 template-manager-system**，而不是 api 本身。

---

## 七、端口总表

全书涉及的端口，按组件列出：

| 端口 | 属于 | 谁访问它 | 对外 |
|---|---|---|---|
| 80 | （iptables 改写为 3002） | SDK 访问沙箱 | 是 |
| 3000 | api（REST） | SDK | 是 |
| 3001 | client-proxy 的 edge API | 内部 | 否 |
| 3002 | client-proxy（沙箱流量） | 经 80 转来 | 间接 |
| 3003 | client-proxy（健康检查） | Consul | 否 |
| 5009 | api（gRPC） | 内部 | 否 |
| 5007 | orchestrator（沙箱代理） | client-proxy | 否 |
| 5008 | orchestrator（gRPC） | api、Consul 健康检查 | 否 |
| 5010～5012 | orchestrator（沙箱访问宿主服务） | 沙箱 | 否 |
| 5016～5018 | orchestrator（出站防火墙代理） | 沙箱 | 否 |
| 6379 | redis | api、client-proxy | 否 |
| 4646 / 4647 / 4648 | Nomad：HTTP 与界面 / RPC / 节点间 | 命令行、浏览器、api | 界面可对外 |
| 8500 / 8600 / 8300～8302 | Consul：HTTP 与界面 / DNS / 集群 | Nomad、dnsmasq | 界面可对外 |
| 53 | dnsmasq | 本机所有程序 | 否 |
| 5432 | PostgreSQL | api、db-migrator、seed-db | 否 |
| 9000 / 9001 | MinIO：S3 / 控制台 | （暂无） | 控制台可对外 |
| 2900 | Harbor | docker、Nomad | 是 |
| 443 | Nginx → Harbor | template-manager（`harbor:443`） | 否 |
| 49983 | envd（沙箱内） | orchestrator 代理 | 否 |

`build.sh -d` 末尾的端口检查（第 18 篇）检查的就是其中 E2B 自己的那些：3000、3001、3002、3003、5007、5008、5009、5010、5016、5017、5018、6379。

---

## 本篇小结

| job | 驱动 | 端口 | 内存 | 关键点 |
|---|---|---|---|---|
| redis | docker（host 网络） | 6379 | 2 GiB | 注册为 `redis.service.consul`；存沙箱目录 |
| template-manager-system | raw_exec | 5008（+5007 等） | 32 GiB | system 类型；双角色；`kill_timeout` 30 秒拆不完暖池；32 GiB 管页缓存不管大页；`STORAGE_PROVIDER` 写死 Local |
| client-proxy（edge.hcl） | docker | 3002、3003 | 4 GiB | 文件名和 job 名不同；DNS 指向本机 |
| api | docker | 3000、5009 | 20 GiB | db-migrator 前置建表；发现 orchestrator 之前 `/health` 一直 503 |
| 依赖链 | | | | 任何一环断了都表现为 api 503；先查 template-manager |

**下一篇预告**：[《配置全景：一个参数从哪来、到哪去》](16-configuration.md)。配置散落在六个地方：`.env`、job 模板、渲染结果、脚本里写死的值、编译进二进制的默认值、系统配置文件。本篇追踪一个变量的完整旅程，讲清楚三种“改了没用”的原因，再把 `.env` 分类讲一遍，最后给一张“要改什么、动哪几处”的速查表。
