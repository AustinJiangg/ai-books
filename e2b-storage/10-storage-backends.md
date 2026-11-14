# 第 10 篇｜模板存到哪：存储后端、Local 与“装了没用”的 MinIO

> **本篇目标**：前几篇反复说“上传到模板存储”。本篇讲这个“模板存储”到底是什么：E2B 支持哪几种存储后端、它们对外是什么接口、文件在每种后端下叫什么名字。然后回到这套环境，一步步追查一个让人困惑的现象：`.env` 里明明写着 `STORAGE_PROVIDER=MinioBucket`，模板却落在了本地的 `/tmp/templates`，而 `/tmp` 又是放在内存里的 tmpfs。最后讲这意味着什么、想改的话有哪两条路。

---

## 一、为什么要有“存储后端”这一层

E2B 的官方部署跑在云上，模板存在 Google Cloud Storage 或 AWS S3 这样的**对象存储**里。对象存储的特点是：

- 不是文件系统，没有目录、没有“打开文件”，只有“桶（bucket）+ 键（key）→ 一串字节”；
- 容量几乎无限，多台机器共享，机器坏了数据也不丢；
- 通过 HTTP 读写，支持“只读其中某一段字节”（范围读）。

但 E2B 也要能在一台开发机上跑，那就需要“存在本地目录里”的版本。为了让上层代码不关心数据到底存在哪，E2B 抽象出了一个**存储后端**接口。

---

## 二、StorageProvider：四个实现、一套接口

### 2.1 接口

```go
type StorageProvider interface {
    OpenBlob(ctx, path, 类型) (Blob, error)          // 打开一个“整读整写”的对象
    OpenSeekable(ctx, path, 类型) (Seekable, error)  // 打开一个“可以随机读”的对象
    DeleteObjectsWithPrefix(ctx, prefix) error       // 删除某个前缀下的所有对象
    UploadSignedURL(ctx, path, 有效期) (string, error) // 生成一个让别人直接上传的链接
    GetDetails() string
}
```

两种对象：

| 对象类型 | 能做什么 | 用在哪些文件上 |
|---|---|---|
| **Blob** | 整个读出来、整个写进去、判断存不存在 | `snapfile`、`metadata.json`、两个 `.header`、层缓存的 index |
| **Seekable** | 按偏移读一段、取大小、按范围流式读、从本地文件整个上传 | `memfile`、`rootfs.ext4` |

为什么分两种？因为 header、snapfile 这些小文件每次都是整个用；而 memfile、rootfs 动辄几 GB，必须能**只读其中一段**，按需取（第 11 篇）。

### 2.2 四个实现

| 后端名（`STORAGE_PROVIDER` 的值） | 存在哪 | 由谁加 |
|---|---|---|
| `GCPBucket` | Google Cloud Storage 的桶 | 上游 |
| `AWSBucket` | AWS S3 的桶 | 上游 |
| `Local` | 本地目录 | 上游 |
| `MinioBucket` | MinIO 的桶 | **ARM 补丁新增** |

ARM 补丁做了两件事：新增了 MinIO 实现，并把**默认值**从 `GCPBucket` 改成了 `MinioBucket`：

```go
const (
    GCPStorageProvider     Provider = "GCPBucket"
    AWSStorageProvider     Provider = "AWSBucket"
    LocalStorageProvider   Provider = "Local"
    MINIOStorageProvider   Provider = "MinioBucket"   // 补丁新增
    DefaultStorageProvider Provider = MINIOStorageProvider  // 补丁改了默认值
)
```

### 2.3 两个入口

代码里有两个函数各建一个后端：

```go
// 模板和快照
func GetTemplateStorageProvider(...) {
    provider := 环境变量("STORAGE_PROVIDER", 默认 MinioBucket)
    if provider == "Local" {
        basePath := 环境变量("LOCAL_TEMPLATE_STORAGE_BASE_PATH", 默认 "/tmp/templates")
        return 本地目录(basePath)
    }
    bucket := 必填环境变量("TEMPLATE_BUCKET_NAME")
    switch provider { case AWS: … case GCP: … case MinioBucket: … }
}

// 构建层缓存（第 9 篇的 index 和 COPY 文件）
func GetBuildCacheStorageProvider(...) {
    同上，只是换成 LOCAL_BUILD_CACHE_STORAGE_BASE_PATH（默认 "/tmp/build-cache"）
    和 BUILD_CACHE_BUCKET_NAME
}
```

注意两点：

- 两个入口读的是**同一个** `STORAGE_PROVIDER`，所以模板和构建缓存总是用同一种后端；
- 选 `Local` 时**根本不读**桶名；选桶类后端时桶名是必填的，没设会直接启动失败。

### 2.4 键名在所有后端下都一样

第 7 篇的六个文件，在存储里的“名字”是：

```
<buildID>/snapfile
<buildID>/memfile
<buildID>/memfile.header
<buildID>/rootfs.ext4
<buildID>/rootfs.ext4.header
<buildID>/metadata.json
```

落到不同后端就是：

| 后端 | 实际位置 |
|---|---|
| `Local` | `/tmp/templates/<buildID>/memfile`（直接按路径建目录、写文件） |
| `MinioBucket` | 桶 `e2b-dev-fc-templates` 里键为 `<buildID>/memfile` 的对象；MinIO 自己在磁盘上存成 `/root/data/minio/e2b-dev-fc-templates/<buildID>/memfile/` 下的若干文件 |

### 2.5 谁会用到存储后端

整个代码里，线上流程只有 orchestrator 进程构造这两个后端：

- 模板后端：恢复沙箱时读，暂停、构建时写，构建失败或被取消时删；
- 构建缓存后端：构建模板时查 index、写 index、存取 COPY 文件。

**api 完全不碰存储**。需要删存储里的文件时（取消一个正在进行的构建），是 api 通过 gRPC 让 template-manager 去执行 `DeleteObjectsWithPrefix(buildID)`。而用户删模板、删快照时，api 只删数据库记录，不删文件（第 14 篇第七节）。所以 api 的配置里设不设 `STORAGE_PROVIDER` 都没有影响。

---

## 三、追查：`.env` 写了 MinIO，为什么没生效

### 3.1 现象

`dep/.env` 里写着：

```bash
export STORAGE_PROVIDER=MinioBucket
export TEMPLATE_BUCKET_NAME=e2b-dev-fc-templates
export BUILD_CACHE_BUCKET_NAME=e2b-dev-fc-cache
export MINIO_ENDPOINT="$SERVER_IP:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
```

`build.sh -i` 也装好了 MinIO，健康检查通过。可是建完模板，去 MinIO 里看，什么都没有；`/tmp/templates` 下却有一堆 buildID 目录。

### 3.2 四步链路

把配置从 RPM 到进程走一遍：

**① RPM 安装**。`e2b-infra.spec` 把源码里 `iac/provider-gcp/nomad/jobs/*.hcl` 装到 `/opt/e2b-infra/nomad/`。其中 `template-manager.hcl` 写的是：

```hcl
STORAGE_PROVIDER = "${STORAGE_PROVIDER}"   # 渲染时会被 .env 的值替换
```

**② `build.sh -i` 覆盖**。`install_e2b` 函数用部署包里的版本覆盖它：

```bash
cp -fv "$DEP_DIR/template-manager.hcl" "$E2B_DIR/nomad/template-manager.hcl"
```

而 `dep/template-manager.hcl` 里这一行是**写死的字面量**：

```hcl
ORCHESTRATOR_SERVICES = "orchestrator,template-manager"
STORAGE_PROVIDER      = "Local"                  # ← 关键
MINIO_ENDPOINT        = "${MINIO_ENDPOINT}"      # 传进去了，但用不上
TEMPLATE_BUCKET_NAME  = "${TEMPLATE_BUCKET_NAME}"
```

**③ `deploy.sh` 渲染**。部署时 `source .env`，然后用 `envsubst` 把 `nomad/*.hcl` 里的 `${变量}` 替换成值，写到 `rendered/` 目录。`envsubst` 只替换 `${...}`，字面量 `"Local"` 原样保留。

**④ 只提交四个 job**。`deploy.sh` 最后提交的 job 只有：

```bash
JOBS=(redis template-manager edge api)
```

上游还有一个 `orchestrator.hcl`，里面写的是 `${STORAGE_PROVIDER}`，会被渲染成 `MinioBucket`。但它**从来没被提交**：这套环境里 orchestrator 是跑在 template-manager 这个 job 里的（第 1 篇）。

结论：

> 唯一会读 `STORAGE_PROVIDER` 的进程，拿到的是写死的 `"Local"`。`.env` 里的 `MinioBucket` 只被渲染进了一个不提交的文件。

### 3.3 于是落到了 `/tmp/templates`

选了 `Local`，又没有设 `LOCAL_TEMPLATE_STORAGE_BASE_PATH`，就用代码默认值：

| 用途 | 目录 |
|---|---|
| 模板和快照 | `/tmp/templates` |
| 构建层缓存 | `/tmp/build-cache` |

### 3.4 怎么亲眼确认

最权威的是看进程**实际的环境变量**：

```bash
# orchestrator 跑在 /usr/bin/template-manager 进程里
pid=$(pgrep -f '^/usr/bin/template-manager' | head -1)
tr '\0' '\n' < /proc/$pid/environ | grep -E 'STORAGE_PROVIDER|LOCAL_.*_BASE_PATH'
```

期望看到 `STORAGE_PROVIDER=Local`，而且**没有** `LOCAL_*_BASE_PATH` 这两行。

再看两边的数据：

```bash
ls /tmp/templates | wc -l            # 有很多 buildID 目录
find /root/data/minio -mindepth 1 -maxdepth 1
# 只有 /root/data/minio/.minio.sys，没有任何桶
```

还有一个常见的误判要排除：`/orchestrator/build` 下面也有 memfile、rootfs 这样的文件，但它们是**本地缓存**，任何后端下都有（第 11 篇），不能用来判断后端是什么。

---

## 四、模板放在 tmpfs 上意味着什么

### 4.1 `/tmp` 是 tmpfs

openEuler 默认启用了系统自带的 `tmp.mount`，把 `/tmp` 挂成 tmpfs：

```
$ findmnt /tmp
TARGET SOURCE FSTYPE OPTIONS
/tmp   tmpfs  tmpfs  rw,nosuid,nodev,...
```

这不是部署脚本加的，是操作系统的默认行为。

### 4.2 三个后果

1. **模板占的是内存**。一个模板的完整根盘几 GB、内存快照几百 MB 到几 GB，再加上每一层、每次暂停产生的 diff，都算在内存里。第 19 篇算容量账时会再说。
2. **宿主机重启，模板全部丢失**。连同暂停中的沙箱的快照一起丢。重启后要重新构建模板。如果 api 的数据库里还记着旧模板的别名，重建时可能报“别名已被占用”，要先删掉旧记录。
3. **不重启也会被清**。系统自带的 `/usr/lib/tmpfiles.d/tmp.conf` 里有一行：

   ```
   q /tmp 1777 root root 10d
   ```

   `systemd-tmpfiles-clean.timer` 每天运行一次，删掉 `/tmp` 下 10 天内既没被访问也没被修改的文件。一个十几天没人用的模板，某一天就会恢复失败。

### 4.3 构建缓存同样在 `/tmp`

`/tmp/build-cache` 也会一起丢。如果只丢了一边（比如某个层的数据被 tmpfiles 清掉了，但 index 还在），会出现“命中了缓存，却找不到那一层”的错误。

---

## 五、MinIO：装了、配了、没用上

### 5.1 MinIO 是什么

**MinIO** 是一个开源的、和 S3 接口兼容的对象存储服务。可以把它理解成“自己搭的一个小 S3”：在本机跑一个进程，把数据存在一个本地目录里，对外提供 S3 风格的 HTTP 接口。

### 5.2 这套环境怎么装的

`build.sh -i` 的 `install_minio` 函数：

```bash
cp dep/minio /usr/local/bin/                    # 二进制
mkdir -p /root/data/minio                       # 数据目录
cp dep/minio.yml /etc/default/minio.yml         # 配置：账号 minioadmin/minioadmin
cp dep/minio.service /etc/systemd/system/       # systemd 服务
systemctl enable --now minio
# 健康检查：curl http://127.0.0.1:9000/minio/health/ready，等到 200
```

服务端口 9000，网页控制台 9001。

### 5.3 谁在用它

| 可能的用户 | 实际情况 |
|---|---|
| 模板和快照 | 不用，后端是 Local（本篇第三节） |
| 构建缓存 | 不用，同上 |
| Loki（日志） | 用的是本地文件系统存储 |
| ClickHouse 备份 | 备份桶名为空，没启用 |

所以在这套 Nomad 单机部署里，MinIO 是“装了、跑着、没人写”。也没有任何地方建过 `e2b-dev-fc-templates` 和 `e2b-dev-fc-cache` 这两个桶。

> 补丁里还有一套 Kubernetes（helm）部署文件，那条路上 `STORAGE_PROVIDER` 是从 `.env` 正常渲染的，MinIO 会真正生效。`.env` 里那一行是为那条路和“本来的设计”准备的。

### 5.4 补丁里 MinIO 实现的两个细节

如果将来真要用它，要知道：

- **`useSSL` 写死为 `false`**：只能走明文 HTTP；`MINIO_ENDPOINT` 必须写成 `主机:端口`，不能带 `http://`。
- **只建客户端，不建桶**：桶必须事先手工建好，否则读写时报对象不存在。

MinIO 实现支持“生成上传链接”（预签名 URL），而 Local 不支持（第 9 篇第 5.3 节）。换成 MinIO 后，带 COPY 的模板就能正常上传文件了。

---

## 六、想让模板“不丢”：两条路

### 6.1 方案一：Local 换个目录（改动最小）

在 `dep/template-manager.hcl` 的 `env {}` 里加两行，指向真正的硬盘：

```hcl
LOCAL_TEMPLATE_STORAGE_BASE_PATH    = "/data/e2b/templates"     # 示例路径
LOCAL_BUILD_CACHE_STORAGE_BASE_PATH = "/data/e2b/build-cache"
```

然后把 `/tmp/templates`、`/tmp/build-cache` 的内容移过去，重新部署 template-manager 这一个 job（`build.sh -r template-manager`）。

单机场景下这是性价比最高的做法：少一跳网络，少一份拷贝，数据在硬盘上，重启不丢。

### 6.2 方案二：真正切到 MinIO

1. 建桶：用 MinIO 控制台或 `mc mb` 建好 `e2b-dev-fc-templates` 和 `e2b-dev-fc-cache`。
2. 把 `dep/template-manager.hcl` 里的 `STORAGE_PROVIDER = "Local"` 改回 `"${STORAGE_PROVIDER}"`。
3. 确认 `.env` 里的 `MINIO_ENDPOINT` 不带 `http://`，桶名正确。
4. 把 `/tmp/templates` 和 `/tmp/build-cache` 的内容按原样（`<buildID>/<文件名>`）拷进两个桶，否则旧模板会报“对象不存在”。
5. 重新部署 template-manager。

MinIO 的价值在于**多台机器共享模板**和**模板的生命周期独立于节点**。单机部署里，它比方案一多了一层网络和一份存储。

### 6.3 不管哪条路，都要改“源头”

`build.sh -i` 每次都会用 `dep/template-manager.hcl` 覆盖 `/opt/e2b-infra/nomad/template-manager.hcl`。如果只改了后者，下次重新安装就被改回去了。要么改仓库里的 `e2b-deploy/dep/template-manager.hcl` 再重新出 RPM，要么记得每次部署后再改一次。

---

## 七、还有一层：共享块缓存（本环境没开）

代码里还有一个可选的东西：`SHARED_CHUNK_CACHE_PATH`。设置它之后，模板后端外面会再包一层**共享缓存**（`WrapInNFSCache`）：从远端对象存储拉下来的数据块，先存到一个所有机器共享的 NFS 目录里，别的机器再要同一块就直接从 NFS 读。

这是给多节点、对象存储在远端的部署准备的。这套环境的 `.env` 里这一项是空的，所以没有启用。

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| 存储后端 | 把“存在桶里还是存在目录里”藏起来的一层接口 |
| Blob / Seekable | 整读整写的小文件 / 可按偏移随机读的大文件 |
| 四个后端 | GCP、AWS、Local、MinIO（补丁新增并设为默认） |
| 两个入口 | 模板后端和构建缓存后端，读同一个 `STORAGE_PROVIDER` |
| 键名 | `<buildID>/<文件名>`，所有后端一样 |
| 实际生效 | `dep/template-manager.hcl` 写死 `"Local"`，`.env` 的 MinIO 不生效 |
| `/tmp/templates` | Local 的默认目录，模板和快照都在这 |
| tmpfs 的后果 | 占内存、重启丢、10 天不用会被清 |
| MinIO | 装在 `/root/data/minio`，端口 9000/9001，没建桶、没人写 |
| 两条改法 | Local 换到硬盘目录，或切到 MinIO；都要改源头文件 |
| 共享块缓存 | `SHARED_CHUNK_CACHE_PATH`，本环境为空，未启用 |

**下一篇预告**：[《节点本地缓存：`/orchestrator` 目录里都是什么》](11-node-local-cache.md)。模板在存储后端里，但沙箱不能直接拿存储后端里的对象当盘、当内存用。中间还隔着一层本地缓存：`/orchestrator/template`、`/orchestrator/build`、`/orchestrator/sandbox`，以及一块挂着却没人用的 `/mnt/snapshot-cache`。下一篇讲这一层：数据怎么按 4 MiB 一块被拉到本地，读一块数据的完整路径是什么，以及为什么在这里看到大文件不必惊慌。
