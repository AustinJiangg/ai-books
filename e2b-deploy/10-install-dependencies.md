# 第 10 篇｜`build.sh -i`（一）：周边依赖——数据库、对象存储、镜像仓库

> **本篇目标**：拆开 `build.sh -i` 的前半段。它按顺序装了几样“不属于 E2B、但 E2B 离不开”的东西：PostgreSQL、MinIO、Harbor、Nginx。每一样讲清楚四件事：为什么需要它、怎么装的、装完在系统里留下了什么、有什么要注意的。重点是最后一样：为什么镜像仓库要套一层 Nginx、一张自签证书要装进三个地方。

---

## 一、`install()` 的顺序

```bash
function install() {
    check_host_ip       # 1. SERVER_IP 必须是本机地址
    yum_install         # 2. 装基础工具和 dnsmasq
    setenforce 0        # 3. SELinux 临时 permissive
    install_postgre     # 4. PostgreSQL
    install_minio       # 5. MinIO
    install_harbor      # 6. Harbor（只解压、改配置）
    install_nginx       # 7. Nginx + 证书
    install_e2b         # 8. SDK、dep 覆盖、dnsmasq（第 11 篇）
}
```

![-i 装出来的周边依赖](img/10-1-周边依赖.svg)

前三步在前面几篇已经讲过：

- `check_host_ip`：第 8、9 篇；
- `yum_install`：装 `curl unzip jq tar rsync` 和 `dnsmasq`，要能访问 yum 源；
- `setenforce 0`：本次开机内有效，持久化见第 8 篇。

下面从第 4 步开始。

---

## 二、PostgreSQL：E2B 的“账本”

### 2.1 为什么需要

第 2 篇说过，api 把团队、API key、模板、构建记录、配额都存在 PostgreSQL 里。没有它，api 一启动就退出。

上游用的是 Supabase 托管的 PostgreSQL。本环境在本机用 docker 跑一个。

### 2.2 怎么装的

```bash
function install_postgre() {
    # 镜像必须提前 docker load 好
    docker image inspect postgres:latest >/dev/null 2>&1 \
        || error "docker 镜像 postgres:latest 不存在，请先 docker load 离线镜像"

    # 已有同名容器，先删掉
    if docker ps -a --format "{{.Names}}" | grep -q "^postgres$"; then
        docker stop postgres; docker rm postgres
    fi

    docker run -d --name postgres \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=local \
        -e POSTGRES_DB=mydatabase \
        -p 5432:5432 \
        --restart=always \
        --health-cmd="pg_isready -U postgres" \
        --health-interval=5s --health-timeout=2s --health-retries=5 \
        postgres:latest

    # 最多等 20 秒，直到健康检查通过
    for ((i=0; i<10; i++)); do
        docker inspect --format '{{.State.Health.Status}}' postgres | grep -q healthy && return 0
        sleep 2
    done
    error "PostgreSQL 健康检查超时！"
}
```

装完的结果：

| 项 | 值 |
|---|---|
| 容器名 | `postgres` |
| 端口 | 5432，映射到宿主机 |
| 账号 / 密码 | `postgres` / `local` |
| 数据库名 | `mydatabase` |
| 连接串 | `postgresql://postgres:local@localhost:5432/mydatabase?sslmode=disable` |
| 健康检查 | 每 5 秒 `pg_isready` |

`.env` 里的 `POSTGRES_CONNECTION_STRING` 就是上面这个连接串。两边的账号、密码、库名必须一致，但它们一个写死在 `build.sh` 里，一个写在 `.env` 里，改的时候要两边一起改。

### 2.3 要注意的

**每次 `-i` 都会删掉旧容器、重建一个新的。** 而这个容器启动时没有挂载数据卷（没有 `-v`），数据存在容器自己的可写层里。容器一删，数据就没了：

- 团队、API key 全部重新生成（`-s` 末尾的 seed-db 会重新造，第 14 篇）；
- 模板记录全部消失，之前建的模板在数据库里查不到了。

这对“推倒重来”的部署流程是合适的。但如果你只想重装 SDK，**不要随手跑 `-i`**。

**表不是这里建的。** 这一步只是启动了一个空数据库。建表由 api 的前置任务 db-migrator 在 `-s` 阶段完成（第 15 篇）。

**看它的状态：**

```bash
docker ps --filter name=postgres
docker exec -it postgres psql -U postgres -d mydatabase -c '\dt'
```

---

## 三、MinIO：装了但没用上的对象存储

### 3.1 为什么装它

模板文件（磁盘镜像、内存快照）要有地方持久保存。上游用 GCS 存储桶。本仓库在补丁里加了一个 MinIO 存储后端，打算用本机的 MinIO 替代 GCS。

### 3.2 怎么装的

```bash
cp -f "$DEP_DIR/minio"         /usr/local/bin
mkdir -p /root/data/minio
cp -f "$DEP_DIR/minio.yml"     /etc/default/minio.yml
cp -f "$DEP_DIR/minio.service" /etc/systemd/system/minio.service
systemctl daemon-reload
systemctl enable minio
systemctl start minio
# 健康检查：反复访问 http://127.0.0.1:9000/minio/health/ready，等 200
```

`minio.service` 的内容第 3 篇逐行读过。配置文件 `/etc/default/minio.yml`：

```bash
MINIO_DIR=/root/data/minio
MINIO_OPTS="--console-address :9001"
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

| 项 | 值 |
|---|---|
| 程序 | `/usr/local/bin/minio` |
| 数据目录 | `/root/data/minio` |
| 端口 | 9000（S3 接口）、9001（网页控制台） |
| 账号 / 密码 | `minioadmin` / `minioadmin` |

健康检查用的 `curl` 加了 `--noproxy '*'`。原因是：如果你的 shell 里设了 `http_proxy` 环境变量，curl 会把访问 `127.0.0.1` 的请求也交给代理，代理返回 504，健康检查就误判失败了。这个坑在脚本里出现过好几次。

### 3.3 但它没有被用上

MinIO 装好了，健康检查也过了，但**当前没有任何组件往里写数据**：

- 部署脚本没有在 MinIO 里建桶；
- orchestrator 的 job 文件里写死了 `STORAGE_PROVIDER = "Local"`，模板实际存在本地目录 `/tmp/templates` 下。

`.env` 里那句 `export STORAGE_PROVIDER=MinioBucket` 没有生效，原因是 job 文件里写死的值压过了它。这是第 16 篇讲“配置为什么改了没用”的头号例子。

为什么还要装？可以理解为“为将来留的位置”：代码已经支持，想切换时按 `deploy-docs/10-模板与快照存储位置梳理.md` 的步骤改几处配置即可。但在切换之前，它只是一个空转的服务。

`-u` 卸载时，MinIO 那一行被注释掉了，它和它的数据目录会一直留在机器上。

---

## 四、Harbor：本机的镜像仓库

### 4.1 为什么需要

第 3 篇说过两个理由：

- 离线，拉不到 Docker Hub；
- api、client-proxy 的镜像是部署时现场构建的，要有个地方放，Nomad 才能按名字拉到。

还有第三个理由：**建模板时，template-manager 要从镜像仓库拉基础镜像**。模板的 Dockerfile 写的是 `FROM harbor:443/e2b-orchestration/ubuntu:22.04-custom`。

### 4.2 两段式安装

Harbor 的安装分成了两半：

| 阶段 | 做什么 |
|---|---|
| `-i` 的 `install_harbor` | 解压安装包，生成并修改 `harbor.yml` |
| `-s` 的开头 | 执行 Harbor 自带的 `install.sh`，用 docker compose 拉起一组容器 |

`-i` 这一半：

```bash
HARBOR_TAR="$DEP_DIR/harbor-offline-installer-aarch64-v2.13.0.tgz"
tar -xvf "$HARBOR_TAR" -C "$WORK_DIR"          # 解到 /opt/e2b-infra/harbor/
cd "$WORK_DIR/harbor"
cp -f harbor.yml.tmpl harbor.yml

sed -i '/^https:/ s/^/#/'          harbor.yml   # 关掉 HTTPS
sed -i '/^  port: 443/ s/^/#/'     harbor.yml
sed -i '/^  certificate: / s/^/#/' harbor.yml
sed -i '/^  private_key: / s/^/#/' harbor.yml
sed -i "s/^hostname: .*/hostname: $HOST_IP/" harbor.yml      # 主机名改成本机 IP
sed -i "/^  port: [0-9]\+/ s/[0-9]\+$/2900/" harbor.yml       # HTTP 端口改成 2900
```

改动只有三处：

1. **关掉 Harbor 自己的 HTTPS**：Harbor 只提供明文 HTTP，HTTPS 交给外面的 Nginx；
2. **主机名设为本机 IP**；
3. **端口从 80 改成 2900**：80 端口要留给 E2B 的沙箱流量入口。

为什么拆成两段？因为真正的安装要用 docker compose 启动十来个容器，耗时也容易出问题。放在 `-s` 里，和其他服务的启动放在一起，`-i` 就只做“准备文件”这类轻量、几乎不会失败的事。

`-s` 那一半的细节在第 12 篇。

### 4.3 装完的样子（`-s` 之后）

| 项 | 值 |
|---|---|
| 安装目录 | `/opt/e2b-infra/harbor/` |
| 地址 | `http://192.168.10.23:2900`（有网页界面） |
| 账号 / 密码 | `admin` / `Harbor12345`（Harbor 默认值，`build.sh` 里写死） |
| 项目 | `e2b-orchestration`，公开（`-s` 时创建） |
| 容器 | `harbor-core`、`registry`、`harbor-db`、`nginx`（Harbor 自己的）等十来个 |

---

## 五、Nginx 与证书：为什么是 `harbor:443`

### 5.1 一个看起来多余的问题

Harbor 已经在 2900 端口提供服务了，为什么还要再装一个 Nginx，在 443 端口用 HTTPS 转发给 2900？

原因在建模板这一步。template-manager 拉基础镜像时不经过 docker，而是用 Go 的镜像库 go-containerregistry 直接访问仓库。这个库对 `localhost` 以外的地址**默认走 HTTPS**，也不认 docker 的 `insecure-registries` 配置。于是有两个选择：

1. 改代码，让它允许 HTTP；
2. 给 Harbor 套一层 HTTPS。

这套环境选了第二种，不改代码。

![harbor:443 请求路径](img/10-2-harbor443路径.svg)

### 5.2 Nginx 的配置

`dep/nginx.conf` 里的关键一段：

```nginx
server {
    listen 443 ssl;
    server_name harbor;

    ssl_certificate     /etc/nginx/ssl/harbor.crt;
    ssl_certificate_key /etc/nginx/ssl/harbor.key;

    location / {
        proxy_pass http://127.0.0.1:2900;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        ...
    }
}
```

监听 443，名字叫 `harbor`，收到的请求原样转给本机 2900。`http` 块里还设了 `client_max_body_size 2G`，因为推送的镜像层可能很大。

这份配置文件里还有一个默认的 `listen 80` 站点。但 80 端口的流量会被 `-s` 最后加的 iptables 规则转给 client-proxy，Nginx 实际收不到（第 14 篇）。

### 5.3 生成证书

```bash
yum install -y nginx
mkdir -p /etc/nginx/ssl
cp -f "$DEP_DIR/harbor.cnf" /etc/nginx/ssl/
cp -f "$DEP_DIR/nginx.conf" /etc/nginx/nginx.conf

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/harbor.key \
    -out    /etc/nginx/ssl/harbor.crt \
    -config /etc/nginx/ssl/harbor.cnf \
    -extensions v3_req
```

证书参数来自 `harbor.cnf`：

```ini
[dn]
CN = harbor

[v3_req]
basicConstraints = critical, CA:TRUE
keyUsage = critical, digitalSignature, keyCertSign, cRLSign
subjectAltName = @alt_names

[alt_names]
DNS.1 = harbor
```

几个要点：

- **证书上的名字是 `harbor`**（`CN` 和 `subjectAltName` 都是）。客户端访问 `https://harbor:443` 时，名字对得上，验证才能过。所以访问时必须用 `harbor` 这个名字，不能用 IP。
- **`CA:TRUE`**：这张证书同时充当“签发机构”，所以可以直接把它本身放进信任库。
- **有效期 365 天**：一年后过期，建模板会报证书过期。每次 `-i` 都会重新生成一张。

### 5.4 一张证书，装进三个地方

第 3 篇说过，不同程序读不同的信任库。这张证书被装进了三处：

```bash
# 1. 系统信任库：大多数 Go 程序读这里
cp -f /etc/nginx/ssl/harbor.crt /etc/pki/ca-trust/source/anchors/harbor-ca.crt
update-ca-trust extract

# 2. docker 的信任目录：docker 访问 harbor:443 时读这里
mkdir -p /etc/docker/certs.d/harbor:443
cp -f /etc/nginx/ssl/harbor.crt /etc/docker/certs.d/harbor:443/ca.crt
```

第三处不在 `build.sh` 里，而在 template-manager 的 job 文件中：

```hcl
env {
  SSL_CERT_FILE = "/etc/docker/certs.d/harbor:443/ca.crt"
}
```

`SSL_CERT_FILE` 是 Go 标准库认的环境变量，直接指定一个证书文件作为信任来源。这是最直接的一道保险：不管系统信任库怎样，template-manager 进程一定信任这张证书。

| 位置 | 谁读 |
|---|---|
| `/etc/pki/ca-trust/...`（系统信任库） | 系统里的大多数程序 |
| `/etc/docker/certs.d/harbor:443/ca.crt` | docker daemon |
| `SSL_CERT_FILE` 指向上面那个文件 | template-manager 进程 |

### 5.5 名字 `harbor` 从哪解析

证书和 Nginx 都准备好了，还差一样：`harbor` 这个名字要能解析到本机。这一步不在 `-i` 里，而在 `-s` 里往 `/etc/hosts` 写 `192.168.10.23 harbor`（第 14 篇）。

把整条路串起来：

```
template-manager 拉 harbor:443/e2b-orchestration/ubuntu:22.04-custom
 → 问 dnsmasq：harbor 在哪？ → dnsmasq 查 /etc/hosts → 192.168.10.23
 → HTTPS 连 192.168.10.23:443 → Nginx 出示证书（CN=harbor），进程信任它
 → Nginx 转给 127.0.0.1:2900 → Harbor 返回镜像
```

任何一环缺了，建模板都会失败，而报错信息分别是：

| 缺了哪一环 | 报错 |
|---|---|
| `/etc/hosts` 没有 harbor | `lookup harbor on 127.0.0.1:53: server misbehaving` |
| 证书没被信任 | `x509: certificate signed by unknown authority` |
| 证书过期 | `x509: certificate has expired` |
| Nginx 没起来 | `connection refused` |
| Harbor 里没有这个镜像 | `manifest unknown` |

### 5.6 Nginx 的启动

```bash
systemctl start nginx
systemctl enable nginx
nginx -t && nginx -s reload
```

`nginx -t` 检查配置语法，通过后重新加载。

---

## 六、`-u` 卸载时这些东西怎么清

| 组件 | `-u` 怎么处理 |
|---|---|
| PostgreSQL | 停容器、删容器、删镜像 |
| MinIO | **不处理**（那一行被注释了） |
| Harbor | `docker-compose down -v`，删 `/opt/e2b-infra/harbor/` |
| Nginx | 停服务，`yum remove nginx`，删 `/etc/nginx`、`/var/log/nginx` |
| Docker | **不处理**（docker 是自备的） |

信任库里的证书文件、`/etc/docker/certs.d/harbor:443/` 不会被删。

---

## 本篇小结

| 组件 | 跑法 | 端口 | 数据 | 要注意的 |
|---|---|---|---|---|
| PostgreSQL | docker，`--restart=always` | 5432 | 容器可写层，没挂卷 | 每次 `-i` 都重建，数据清空；表由 db-migrator 建 |
| MinIO | systemd | 9000、9001 | `/root/data/minio` | 装了但没用上，`STORAGE_PROVIDER` 被写死为 `Local` |
| Harbor | docker compose | 2900 | `/opt/e2b-infra/harbor/` | `-i` 只改配置，`-s` 才启动；账号 `admin/Harbor12345` |
| Nginx | systemd | 443 | `/etc/nginx` | 给 Harbor 套 HTTPS，名字必须是 `harbor` |
| 自签证书 | — | — | `/etc/nginx/ssl/harbor.crt` | CN=harbor，一年有效；装进系统信任库、docker 目录、`SSL_CERT_FILE` |

**下一篇预告**：[《`build.sh -i`（二）：E2B 本体与 SDK》](11-install-e2b-and-sdk.md)。`-i` 的最后一步 `install_e2b`：装 Python SDK 并做三层改造；把 `dep/` 覆盖到位；准备 Consul、Nomad 的离线安装包；给 dnsmasq 加两行配置，让 `*.e2b.app` 指向本机，并避开一个让每条命令多等 15 秒的坑。
