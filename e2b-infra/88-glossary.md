# 88 · 术语表

> 全书用到的固定译法与反复出现的概念，按中文拼音与英文字母各列一表，
> 每条给出英文写法、两到四句定义，以及讲得最细的篇目。
>
> **读者**：读到某个词想不起它在哪一篇讲过的人　**预备**：无　**代码**：无（定义均取自各篇正文）

---

## 0. 怎么用这张表

本篇是查阅用的附录，不是可以顺读的一章。它的口径来自两处：一处是
[写作规约](STYLE.md)第三节的固定译法表，那张表规定了中文正文里该怎么称呼每个部件，
本篇把它全部收录并补上定义；另一处是已经写成的各篇正文里反复出现的标识符与概念，
例如 `LifecycleID`、`cacheScope`、`team_limits`、hyperloop、HDBSS，
它们在代码里是一个名字，在书里散落在若干篇，需要一个集中的落点。

用法有三条。第一，每条定义只说「它是什么」，不讲机制的取舍与实现细节，
那些留在「主要篇目」列指向的正文里；一条术语若在两三篇里都占大段篇幅，
主要篇目列会列出全部，排在前面的是讲得最细的一篇。
第二，同一个概念的中英两种写法只立一个词条：有固定中文译法的进第一张表，
按拼音排序，英文写在括号里；不翻译的专有名词与代码里的标识符进第二张表，按字母排序。
第三，版本称谓只有三个 —— 上游 2026.09、ARM 适配版、单机离线版 ——
它们本身也是词条，含义见第一张表；正文里凡不加说明的地方讲的都是上游 2026.09。

---

## 1. 中文词条（按拼音）

### 1.1 速查表

| 中文 | 英文 | 主要篇目 |
|---|---|---|
| 编排器 | orchestrator | [第 25 篇](25-orchestrator-process.md)、[第 10 篇](10-system-architecture.md) |
| 边缘代理 | client-proxy（edge） | [第 53 篇](53-client-proxy-edge.md)、[第 56 篇](56-edge-api.md) |
| 层 | layer | [第 45 篇](45-layers-and-build-cache.md)、[第 42 篇](42-build-phases.md) |
| 差分 | diff | [第 29 篇](29-template-artifact-format.md)、[第 37 篇](37-pause-and-snapshot.md) |
| 大页 | huge pages | [第 32 篇](32-memory-prefetch-and-hugepages.md)、[第 04 篇](04-kvm-and-memory-virtualization.md) |
| 单机离线版 | single-node offline deployment | [第 80 篇](80-single-node-rpm.md)、[第 81 篇](81-single-node-traffic.md) |
| 档位 | tier | [第 16 篇](16-auth-and-multitenancy.md)、[第 58 篇](58-postgres-schema-and-migrations.md) |
| 对象存储 | object storage | [第 13 篇](13-storage-landscape.md)、[第 75 篇](75-minio-storage.md) |
| 多租户 | multitenancy | [第 16 篇](16-auth-and-multitenancy.md)、[第 02 篇](02-why-sandbox.md) |
| 放置 | placement | [第 19 篇](19-node-management-and-placement.md) |
| 分片 | chunk | [第 30 篇](30-block-layer.md)、[第 34 篇](34-template-cache-and-local-storage.md) |
| 根文件系统 | rootfs | [第 33 篇](33-nbd-and-rootfs.md)、[第 43 篇](43-rootfs-construction.md) |
| 构建 | build | [第 41 篇](41-template-build-overview.md)、[第 11 篇](11-object-model.md) |
| 集群 | cluster | [第 21 篇](21-clusters-and-discovery.md) |
| 节点 | node | [第 19 篇](19-node-management-and-placement.md)、[第 25 篇](25-orchestrator-process.md) |
| 节点池 | node pool | [第 63 篇](63-gcp-terraform.md)、[第 64 篇](64-nomad-jobs.md) |
| 块 | block | [第 29 篇](29-template-artifact-format.md)、[第 30 篇](30-block-layer.md) |
| 快照 | snapshot | [第 37 篇](37-pause-and-snapshot.md)、[第 29 篇](29-template-artifact-format.md) |
| 模板 | template | [第 11 篇](11-object-model.md)、[第 22 篇](22-template-api.md) |
| 模板管理器 | template-manager | [第 46 篇](46-template-manager-service.md)、[第 23 篇](23-template-manager-client.md) |
| 内存文件 | memfile | [第 29 篇](29-template-artifact-format.md)、[第 31 篇](31-uffd-memory-backend.md) |
| 缺页 | page fault | [第 05 篇](05-userfaultfd.md)、[第 31 篇](31-uffd-memory-backend.md) |
| 沙箱 | sandbox | [第 26 篇](26-sandbox-object.md)、[第 12 篇](12-sandbox-lifecycle-walkthrough.md) |
| 沙箱目录 | sandbox catalog | [第 55 篇](55-sandbox-catalog-and-routing.md)、[第 20 篇](20-sandbox-state-storage.md) |
| 上游 2026.09 | upstream 2026.09 | [写作规约 §2](STYLE.md)、[第 01 篇](01-e2b-ecosystem.md) |
| ARM 适配版 | ARM port | [第 67 篇](67-arm-port-overview.md)、[第 68 篇](68-aarch64-virtualization-differences.md) |
| 特性开关 | feature flag | [第 14 篇](14-config-flags-versions.md)、[第 77 篇](77-api-and-flags-on-arm.md) |
| 团队 | team | [第 16 篇](16-auth-and-multitenancy.md)、[第 11 篇](11-object-model.md) |
| 网络槽位 | slot | [第 35 篇](35-sandbox-networking.md)、[第 07 篇](07-linux-networking-for-sandboxes.md) |
| 写保护 | write protect（WP） | [第 05 篇](05-userfaultfd.md)、[第 72 篇](72-uffd-on-arm.md) |
| 写时复制 | copy-on-write（COW） | [第 06 篇](06-block-devices-nbd-cow.md)、[第 30 篇](30-block-layer.md) |
| 映射表 | header | [第 29 篇](29-template-artifact-format.md) |
| 预取 | prefetch | [第 32 篇](32-memory-prefetch-and-hugepages.md) |
| 脏页 | dirty page | [第 37 篇](37-pause-and-snapshot.md)、[第 72 篇](72-uffd-on-arm.md) |
| 暂停 / 恢复 | pause / resume | [第 37 篇](37-pause-and-snapshot.md)、[第 27 篇](27-resume-sandbox.md) |

### 1.2 释义

**编排器**（orchestrator）—— 运行在每台节点上的 Go 进程，直接管理这台机器上的全部沙箱：
拉起与回收 Firecracker、挂上内存与磁盘后端、取还网络槽位、代理进出沙箱的流量。
它对外只暴露 gRPC，调用方是 api 服务与 edge。按写作规约，首次出现之后一律写英文 `orchestrator`。

**边缘代理**（client-proxy，edge）—— 同一个进程的两个名字：二进制与包目录叫 `client-proxy`，
它在拓扑里的位置叫 edge。它是外部流量的入口，从形如 `<端口>-<沙箱ID>.<域名>` 的主机名里
解出沙箱与端口，查沙箱目录得到承载节点，再把连接转给那台机器上的 orchestrator。
本书用 client-proxy 指进程，用 edge 指位置。

**层**（layer）—— 模板构建里的缓存单位。一条构建指令对应一层，每层的产物是一对 memfile
与 rootfs 差分加一份元数据，能不能跳过某一层由该层的哈希决定。层是构建期的概念，
沙箱运行期看不到层，只看到最后一层压平出来的那次构建。

**差分**（diff）—— 只含改动块的产物文件。一次 pause 或者构建的一层不重写整份内存文件与
根文件系统，只把被写过的块顺序写成一个 diff，再配一张映射表说明哪个块该到哪一代去取。
好处是产物体积与写入量正比于改动量，代价是读的时候多一次查表。

**大页**（huge pages）—— 这里特指 2 MiB 的 HugeTLB 页，用于 guest 内存的宿主侧映射。
相对 4 KiB 页，页表项数、缺页次数与 uffd 事件数各降 512 倍。
代价是宿主必须提前预留，运行期凑不出来，而且填页要按 2 MiB 对齐，不能按 4 KiB 填一角。

**单机离线版** —— 把 ARM 适配版打成 RPM、在一台 openEuler/aarch64 服务器上无外网部署的形态。
它保留 Nomad 与 Consul 但只有一个节点，对象存储换成本机 MinIO，
镜像仓库换成本地 Harbor 或直连，特性开关换成离线取值。

**档位**（tier）—— 团队的资源配额等级，规定并发沙箱数、单个沙箱的最长存活时间与 CPU
内存上限。运行期读到的配额不是 `tiers` 表本身，而是把档位基线加上当前生效增量的
`team_limits` 视图，所以给某个团队临时加并发不需要新建档位。

**对象存储**（object storage）—— GCS、S3、MinIO 的统称。模板产物、构建缓存与 pause
快照都放在这里，节点本地只留分片缓存。存储 provider 在编译期由构建标签选定，不是运行期判断。

**多租户**（multitenancy）—— 一套集群同时服务多个互不信任的团队。隔离分三层：
API key 与 access token 的鉴权、按团队划分的配额与对象存储命名空间、
microVM 与网络命名空间提供的运行时隔离。第三层是 e2b 存在的理由。

**放置**（placement）—— 给一个新沙箱挑一台节点。算法是 best-of-K：
无放回随机抽样直到攒够 K 个通过过滤的候选，再取「放置之后过量分配率最小」的那台。
它不维护全局最优，只保证坏选择的概率随 K 快速下降。

**分片**（chunk）—— 从对象存储按范围拉取的单位，比块大。
block 层的 chunker 负责把 guest 的一次小读放大成整分片的 range 请求，
把整片填进本地缓存，后续落在同一片里的读就不再出网。

**根文件系统**（rootfs）—— 快照中的磁盘产物 `rootfs.ext4`，一个 ext4 镜像。
运行期它不被宿主挂载，而是经 block 层与 NBD 暴露成 `/dev/nbdX` 交给 Firecracker，
guest 里才挂成根盘。

**构建**（build）—— 模板的一次具体产物，由一个 UUID 形式的 build ID 标识，
这个 ID 同时是对象存储里产物的目录名。一个模板可以有多次构建；
pause 产生的快照在存储上也是一次构建，只是没有对应的构建指令。

**集群**（cluster）—— 一组节点加一组 edge。集群的地址与身份记在数据库里，
api 据此把请求路由到正确的 edge，再由 edge 转给节点。单机离线版里集群只有一个成员。

**节点**（node）—— 运行 orchestrator 的宿主机。api 侧维护每个节点的健康状态、
已用与可用容量、以及排空标记；放置只在状态正常且容量够的节点里挑。

**节点池**（node pool）—— Nomad 的调度分组。同一个镜像家族按职责分成若干池，
差别在机器规格、磁盘、启动脚本与大页比例：跑沙箱的是 client 池，跑模板构建的是 build 池，
跑控制面的是 api 池。job 用 node pool 与 constraint 决定自己落在哪一类机器上。

**块**（block）—— 映射表里的映射单位，也是 block 层缓存位图的粒度。
内存文件的块大小要与宿主页大小一致，用大页时就是 2 MiB；
根文件系统的块大小与文件系统块对齐。块选大了放大写入，选小了放大表的体积。

**快照**（snapshot）—— 一个沙箱在某一刻的完整可恢复状态：内存文件与根文件系统的差分、
各自的映射表、Firecracker 的 VM 状态文件与一份元数据。
它是通用概念，在 e2b 里 pause 产出的快照同时也是一次 build。

**模板**（template）—— 沙箱的「镜像」：规定 guest 的根文件系统内容、内核版本、
启动命令与资源规格。一个模板有多次构建，创建沙箱时用的是其中某一次构建的产物，
所以「模板」是长期标识，「构建」才是可以拿来启动的东西。

**模板管理器**（template-manager）—— 负责模板构建的服务。
它与 orchestrator 是同一个二进制的两种角色，靠环境变量 `ORCHESTRATOR_SERVICES` 决定
本进程启用哪些 gRPC 服务，因此两者可以合并部署，也可以分在不同节点池上。

**内存文件**（memfile）—— 快照中的 guest 内存产物。恢复时它不被整份读进内存，
而是由 uffd 后端按缺页按需拉取，读到的数据经 block 层从本地缓存或对象存储取回。
它通常是快照里最大的一份，也是恢复延迟的主要来源。

**缺页**（page fault）—— guest 访问尚未填充的内存页时触发的异常。
在恢复路径上，这些缺页被 userfaultfd 转成用户态事件交给 orchestrator，
由它取到数据再填回去；因此一次「内存访问」在 e2b 里可能等价于一次对象存储读。

**沙箱**（sandbox）—— 一台运行中的 microVM 及其宿主侧资源：Firecracker 进程、
内存与磁盘后端、网络槽位、cgroup 记账与代理连接。
沙箱有自己的生命周期与身份，宿主侧的 sandbox 对象是这些资源的持有者与回收者。

**沙箱目录**（sandbox catalog）—— 一张只回答「某个沙箱现在在哪台节点上」的路由表，
存在 Redis 的 `sandbox:catalog:<沙箱ID>` 键上，靠 TTL 过期，
edge 侧还有一层 500 ms 的进程内缓存。它为读优化，允许短暂陈旧，
不承担配额、状态机之类的其它职责。

**上游 2026.09** —— e2b-dev/infra 在 tag `2026.09` 的代码。
全书凡不特别说明的地方讲的都是它；引用代码时写仓库相对路径，不写行号。

**ARM 适配版** —— 在上游 2026.09 之上的 aarch64 移植：infra 的适配补丁、
分叉 Firecracker 的 ARM 修复、以及 fc-kernels 的 arm64 内核配置。
它的差异集中在第十部分，上游各篇只在末尾用一节点到为止。

**特性开关**（feature flag）—— 不重启进程就能改的运行期取值，上游用 LaunchDarkly 驱动。
它的适用范围有限：只有在每次使用时都重新读取的地方才真正可热改，
像 chunker 的构造参数那种只在初始化时读一次的，改了也要重启才生效。

**团队**（team）—— 租户单位。API key 属于团队，配额按团队计，
构建缓存的命名空间 `cacheScope` 默认也取团队 ID，
所以同一团队的两个模板可以复用彼此的层，跨团队则不会。

**网络槽位**（slot）—— 一套预先建好、循环使用的网络资源：一个网络命名空间、
一对 veth、一个 tap 设备和一段固定的 IP。沙箱启动时取一个槽位，
结束后异步归还并清理，避免每次创建都去配一遍网络。

**写保护**（write protect，WP）—— userfaultfd 的一种模式：页已经填充之后，
对它的写仍然可以被拦截成事件。e2b 用它来判定「这一页在上次快照之后被写过没有」，
判据是 `/proc/<pid>/pagemap` 里的 uffd-wp 位。

**写时复制**（copy-on-write，COW）—— 读走共享的只读基底、写落到私有层的模式。
block 层的 Overlay 就是这个结构：一个只读设备加一个可写的本地缓存文件，
写只进缓存，读先问缓存位图、未命中再问基底。

**映射表**（header）—— `memfile.header` 与 `rootfs.ext4.header`，
记录每个块该到哪一代 diff 的哪个偏移去取。它让差分链可以只查一张表就定位，
pause 时新表直接写祖先的 build ID，把链压平。

**预取**（prefetch）—— 在缺页真正发生之前，主动把可能要用的页读进来。
它拿网络与磁盘带宽换缺页延迟，猜错时浪费的是带宽，猜对时省下的是一次同步等待。

**脏页**（dirty page）—— 上一次快照之后被 guest 写过的内存页。
把脏页找出来是增量快照的前提：只有脏页需要写进新的 diff。
判定手段有 KVM 的脏页日志、userfaultfd 写保护、以及硬件标脏三条路。

**暂停 / 恢复**（pause / resume）—— e2b 的原生快照与从快照拉起。
pause 把运行中的沙箱变成一次 build 并释放宿主资源，resume 反过来。
两者不是对称的：pause 的成本正比于脏页量，resume 的成本正比于恢复后实际访问到的页量。

---

## 2. 英文词条（按字母）

### 2.1 速查表

| 英文 | 中文 / 展开 | 主要篇目 |
|---|---|---|
| aarch64 | ARM 64 位架构 | [第 68 篇](68-aarch64-virtualization-differences.md)、[第 67 篇](67-arm-port-overview.md) |
| best-of-K | 放置采样算法 | [第 19 篇](19-node-management-and-placement.md) |
| build ID | 构建标识 | [第 29 篇](29-template-artifact-format.md)、[第 42 篇](42-build-phases.md) |
| busybox | 构建期 init | [第 43 篇](43-rootfs-construction.md)、[第 74 篇](74-template-build-on-arm.md) |
| cacheScope | 缓存命名空间 | [第 45 篇](45-layers-and-build-cache.md)、[第 46 篇](46-template-manager-service.md) |
| chunker | 分片读取器 | [第 30 篇](30-block-layer.md) |
| ClickHouse | 指标与日志库 | [第 59 篇](59-clickhouse.md)、[第 24 篇](24-api-metrics-and-analytics.md) |
| client ID | 遗留标识 | [第 52 篇](52-envd-legacy-and-sdk-compat.md)、[第 11 篇](11-object-model.md) |
| client-proxy | 边缘代理进程 | [第 53 篇](53-client-proxy-edge.md) |
| Connect-RPC | RPC 协议 | [第 48 篇](48-envd-overview.md)、[第 08 篇](08-go-service-toolkit.md) |
| Consul / Consul KV | 服务发现与 KV | [第 09 篇](09-nomad-consul-terraform.md)、[第 35 篇](35-sandbox-networking.md) |
| DiffStore | 本地产物缓存 | [第 34 篇](34-template-cache-and-local-storage.md)、[第 30 篇](30-block-layer.md) |
| docker-reverse-proxy | 镜像推送鉴权代理 | [第 57 篇](57-docker-reverse-proxy.md) |
| edge | 边缘位置 | [第 53 篇](53-client-proxy-edge.md)、[第 56 篇](56-edge-api.md) |
| envd | 沙箱内守护进程 | [第 48 篇](48-envd-overview.md)、[第 52 篇](52-envd-legacy-and-sdk-compat.md) |
| ExecutionID | 执行标识 | [第 26 篇](26-sandbox-object.md) |
| Firecracker | microVM 监视器 | [第 03 篇](03-firecracker-primer.md)、[第 28 篇](28-firecracker-process-management.md) |
| gRPC | 内部 RPC | [第 08 篇](08-go-service-toolkit.md)、[第 25 篇](25-orchestrator-process.md) |
| Harbor | 私有镜像仓库 | [第 78 篇](78-helm-k8s-deployment.md)、[第 57 篇](57-docker-reverse-proxy.md) |
| hashingVersion | 层哈希版本 | [第 45 篇](45-layers-and-build-cache.md) |
| HDBSS | 硬件标脏 | [第 72 篇](72-uffd-on-arm.md)、[第 87 篇](87-beyond-checkpoint-restore.md) |
| Helm | k8s 打包 | [第 78 篇](78-helm-k8s-deployment.md)、[第 76 篇](76-k8s-discovery.md) |
| HugeTLB | 大页机制 | [第 32 篇](32-memory-prefetch-and-hugepages.md)、[第 68 篇](68-aarch64-virtualization-differences.md) |
| hyperloop | guest 到宿主的回调 | [第 36 篇](36-orchestrator-proxy-and-envd-client.md)、[第 48 篇](48-envd-overview.md) |
| Kubernetes | 容器编排 | [第 76 篇](76-k8s-discovery.md)、[第 78 篇](78-helm-k8s-deployment.md) |
| Kunpeng（鲲鹏） | 服务器处理器 | [第 67 篇](67-arm-port-overview.md)、[第 72 篇](72-uffd-on-arm.md) |
| KVM | 内核虚拟化 | [第 04 篇](04-kvm-and-memory-virtualization.md)、[第 68 篇](68-aarch64-virtualization-differences.md) |
| LaunchDarkly | 特性开关服务 | [第 14 篇](14-config-flags-versions.md) |
| LifecycleID | 进程代标识 | [第 26 篇](26-sandbox-object.md)、[第 39 篇](39-health-errors-and-teardown.md) |
| Loki | 日志后端 | [第 24 篇](24-api-metrics-and-analytics.md)、[第 60 篇](60-telemetry.md) |
| MinIO | 自建对象存储 | [第 75 篇](75-minio-storage.md) |
| MMDS | guest 元数据服务 | [第 48 篇](48-envd-overview.md)、[第 36 篇](36-orchestrator-proxy-and-envd-client.md) |
| NBD | 网络块设备 | [第 33 篇](33-nbd-and-rootfs.md)、[第 06 篇](06-block-devices-nbd-cow.md) |
| netns | 网络命名空间 | [第 07 篇](07-linux-networking-for-sandboxes.md)、[第 35 篇](35-sandbox-networking.md) |
| Nomad | 调度器 | [第 09 篇](09-nomad-consul-terraform.md)、[第 64 篇](64-nomad-jobs.md) |
| Nomad job | 作业定义 | [第 64 篇](64-nomad-jobs.md) |
| OpenAPI | REST 契约 | [第 08 篇](08-go-service-toolkit.md)、[第 15 篇](15-api-service-structure.md) |
| openEuler | 宿主发行版 | [第 74 篇](74-template-build-on-arm.md)、[第 67 篇](67-arm-port-overview.md) |
| OpenTelemetry | 遥测框架 | [第 60 篇](60-telemetry.md) |
| ORCHESTRATOR_SERVICES | 角色开关 | [第 46 篇](46-template-manager-service.md)、[第 25 篇](25-orchestrator-process.md) |
| overlay | 覆盖层 | [第 30 篇](30-block-layer.md)、[第 06 篇](06-block-devices-nbd-cow.md) |
| Packer | 镜像构建 | [第 63 篇](63-gcp-terraform.md)、[第 09 篇](09-nomad-consul-terraform.md) |
| PostgreSQL | 主数据库 | [第 58 篇](58-postgres-schema-and-migrations.md)、[第 13 篇](13-storage-landscape.md) |
| raw_exec | Nomad driver | [第 09 篇](09-nomad-consul-terraform.md)、[第 64 篇](64-nomad-jobs.md) |
| Redis | 状态与目录存储 | [第 20 篇](20-sandbox-state-storage.md)、[第 55 篇](55-sandbox-catalog-and-routing.md) |
| sandbox ID | 沙箱标识 | [第 17 篇](17-sandbox-create-api.md)、[第 20 篇](20-sandbox-state-storage.md) |
| systemd | guest init | [第 43 篇](43-rootfs-construction.md)、[第 48 篇](48-envd-overview.md) |
| tap | 虚拟网卡 | [第 07 篇](07-linux-networking-for-sandboxes.md)、[第 35 篇](35-sandbox-networking.md) |
| team_limits | 配额视图 | [第 58 篇](58-postgres-schema-and-migrations.md)、[第 16 篇](16-auth-and-multitenancy.md) |
| Terraform | 基础设施描述 | [第 63 篇](63-gcp-terraform.md)、[第 09 篇](09-nomad-consul-terraform.md) |
| uffd / userfaultfd | 用户态缺页 | [第 05 篇](05-userfaultfd.md)、[第 31 篇](31-uffd-memory-backend.md)、[第 72 篇](72-uffd-on-arm.md) |
| veth | 虚拟以太网对 | [第 07 篇](07-linux-networking-for-sandboxes.md)、[第 35 篇](35-sandbox-networking.md) |

### 2.2 释义

**aarch64** —— ARM 的 64 位指令集架构，也写作 arm64。
本书第十部分讲的移植就是把原本只在 x86_64 上验证过的一套系统搬到 aarch64 上，
差异集中在虚拟化扩展、页大小与内存序三处。

**best-of-K** —— 放置用的采样算法：从候选节点里无放回地随机抽，
抽到够 K 个通过过滤的为止，再在这 K 个里取「放置之后过量分配率」最小的一台。
它的理论出处是随机负载均衡里的 power of two choices，
好处是不需要全局排序，坏处是不保证最优。

**build ID** —— 一次构建的 UUID，也是对象存储里这次构建产物的目录名。
映射表里指向祖先的引用写的就是 build ID，因此差分链是靠这个 ID 串起来的。
它与模板 ID 不同：模板 ID 长期不变，build ID 每构建一次换一个。

**busybox** —— 静态链接的小型工具集，在模板构建的 provision 阶段当 PID 1。
原因是基础镜像里通常还没有 systemd，需要一台「能跑但还没有 init」的沙箱去装 systemd。
成品沙箱的 PID 1 是 systemd，不是 busybox。

**cacheScope** —— 层缓存与文件缓存在对象存储里的命名空间前缀，
由 api 侧填成 team ID，缺省时退回模板 ID 顶上。
它决定了缓存的共享边界：同一个 scope 下的构建互相能命中，换了 scope 相当于整个命名空间作废。

**chunker** —— block 层里负责从对象存储按分片拉取的组件，实现在 `block/chunk.go`
与 `block/streaming_chunk.go`。它把一次小读放大成整分片请求并回填本地缓存，
是缓存的两个写入者之一（另一个是 guest 自己的写）。

**ClickHouse** —— 列式数据库，装沙箱与构建的指标、以及部分日志。
它承担的是「按时间与维度聚合」的查询，与 PostgreSQL 的事务型职责分开。

**client ID** —— 早期用来定位承载节点的标识，在上游 2026.09 已经退化为常量 `6532622b`，
只为兼容旧 SDK 与旧域名保留，不再含任何路由信息。真正的定位改由沙箱目录承担。

**client-proxy** —— 边缘代理的二进制名与包目录名，见中文词条「边缘代理」。
本书用它指进程本身，用 edge 指这个进程在拓扑里的位置。

**Connect-RPC** —— 与 gRPC 语义兼容、但可以直接跑在 HTTP/1.1 上的 RPC 协议。
envd 的进程与文件系统服务用它，好处是同一个端口既能服务浏览器也能服务 SDK，
不需要 guest 里另起一套 HTTP/2 栈。

**Consul / Consul KV** —— 服务发现与分布式 KV。上游用 Consul 做服务注册与 DNS，
并把网络槽位表示成 KV 里的一个 `<节点ID>/<槽位号>` 键做乐观分配。
单机离线版不需要跨节点协调，槽位分配改走本机目录，因此可以完全不用 Consul KV。

**DiffStore** —— orchestrator 本地的构建产物缓存，实现在
`internal/sandbox/build/cache.go`。缓存键是 `<build-id>/<memfile|rootfs.ext4>`，
按磁盘水位（默认 85%）加 TTL 驱逐。它是「对象存储」与「block 层」之间的那一层本地盘缓存。

**docker-reverse-proxy** —— 模板镜像推送时的鉴权代理，独立进程，
挂在 `docker.<域名>` 后面。客户端用 e2b 的凭据推镜像，由它换成镜像仓库的凭据再转发，
从而不必把仓库凭据发给用户。

**edge** —— client-proxy 在拓扑里的位置名，也是它对外那套控制 API 的名字
（`spec/openapi-edge.yml`）。同一个进程既转发沙箱流量，也提供集群内部的服务发现接口。

**envd** —— 沙箱内唯一常驻的守护进程，不翻译。它提供进程执行、文件读写、
端口探测与指标采集，并用一个 access token 做鉴权。
token 设置之前 envd 是完全开放的，那段窗口靠网络隔离与代理的端口过滤兜底。

**ExecutionID** —— 一次执行的 UUID，从 start 或 resume 到 stop 或 pause 之间不变。
它的用途是删除时的归属校验：按 ID 无条件删除会误删「同名沙箱的新一次执行」，
带上 ExecutionID 做条件删除就不会。

**Firecracker** —— AWS 开源的 microVM 监视器，e2b 用它跑每一个沙箱。
它只实现最小的一组虚拟设备，启动快、内存开销小，并且原生支持快照与恢复。
ARM 适配版用的是一个带 aarch64 修复的分叉版本。

**gRPC** —— 控制面内部的 RPC 协议：api 到 orchestrator、api 到 template-manager
走的都是它。对外的 REST 契约用 OpenAPI，两者分工固定。

**Harbor** —— 私有镜像仓库。ARM 适配版与单机离线版把上游的 Artifact Registry
换成 Harbor，template-manager 的仓库地址变量直接填 Harbor 地址。

**hashingVersion** —— 层哈希算法的版本号，当前值 `"v2"`，参与每个层的哈希键。
改动哈希算法时把它递增一次，全部旧缓存就自然失效，
表现为一次缓存未命中而不是构建失败。

**HDBSS** —— ARMv9.5 引入的硬件脏页跟踪特性，鲲鹏 950 实现了它。
它让脏页判定不再依赖 userfaultfd 写保护或 KVM 的软件日志，
代价是绑定具体硬件世代。本书只讲它是什么，细节在 checkpoint / restore 手册。

**Helm** —— Kubernetes 上的打包与部署工具。ARM 适配版的 k8s 形态用一套 Helm chart
描述全部组件，变量集中在 `values-template.yaml` 里按组分列。

**HugeTLB** —— Linux 的大页机制，e2b 用它的 2 MiB 页承载 guest 内存。
页必须提前从 `nr_hugepages` 预留，运行期不能从普通页临时凑；
uffd 填页时也要按 2 MiB 粒度对齐。

**hyperloop** —— 方向与 envd 相反的一条通道：服务端在 orchestrator
（`internal/hyperloopserver/`），调用方是沙箱内部，接口只有 `/me` 与 `/logs`。
它让 guest 能主动查自己的身份、往宿主送日志，契约写在 `spec/openapi-hyperloop.yml`。

**Kubernetes** —— 容器编排系统。上游用 Nomad，ARM 适配版另外提供了一套 k8s 形态，
服务发现相应从 Consul 换成 k8s 的 API。两套形态共用同一批二进制。

**Kunpeng（鲲鹏）** —— 华为的 aarch64 服务器处理器系列，ARM 适配版的目标硬件。
不同世代的差异会直接影响可用的虚拟化与脏页跟踪能力。

**KVM** —— Linux 内核的虚拟化接口，Firecracker 通过它创建 vCPU 与内存槽。
在 aarch64 上它依赖 ARM 的虚拟化扩展与 GIC，与 x86 的 VMX 在中断与页表上都不一样。

**LaunchDarkly** —— 上游用的特性开关服务，把开关值从代码搬到外部控制台。
它有本地存储与离线模式，因此自建或离线部署时可以不连外网，
代价是所有开关退回到代码里的默认值。

**LifecycleID** —— 每启动一个新的 Firecracker 进程就换一次的 UUID。
它解决的是「旧进程的清理逻辑误删新进程的记录」这类竞态：
从 map 里摘除时用条件删除，只有 LifecycleID 相等才真的删。

**Loki** —— 日志后端，沙箱日志经 envd 与 logs-collector 汇聚到这里。
它的租户隔离靠 `teamID` 标签，所以每一行沙箱日志都要在 orchestrator 侧补上团队标签。

**MinIO** —— 兼容 S3 接口的自建对象存储。ARM 适配版新增了一个 MinIO 的存储 provider，
并把默认 provider 从 GCS 改成它，离线部署由此不再依赖公有云。

**MMDS** —— microVM Metadata Service，Firecracker 在 guest 网络里模拟出的元数据端点。
orchestrator 用它把本次的沙箱身份与 access token 哈希交给 guest。
恢复时必须在 resume 之后立刻覆盖，否则 guest 读到的是上一次快照里的旧身份。

**NBD** —— 网络块设备。orchestrator 把 block 层包装成一个 NBD 服务端，
在宿主上呈现为 `/dev/nbdX` 供 Firecracker 当磁盘用。
`/dev/nbdX` 是内核模块加载时按 `nbds_max` 一次建好的固定集合，
因此设备号是跨进程的全局资源，必须全机统一记账。

**netns** —— 网络命名空间。每个沙箱一个 netns，是网络槽位的核心组成，
guest 的 tap 设备与出口 veth 都在里面。

**Nomad** —— HashiCorp 的调度器，上游用它跑控制面与 orchestrator。
相对 Kubernetes 它更轻，且原生支持直接在宿主上跑二进制的 driver，
这对需要访问 `/dev/kvm` 与网络命名空间的 orchestrator 是必要的。

**Nomad job** —— 一份作业定义，规定类型（`service` 常驻、`system` 每节点一份、
`batch` 跑完即止）、driver、node pool 与 constraint、以及端口与资源。
orchestrator 是 `system` 类型，因此每个 client 节点上恰好一份。

**OpenAPI** —— 对外 REST 接口的契约格式。仓库里有四份规格：
面向用户的 `openapi.yml`、边缘控制的 `openapi-edge.yml`、
guest 回调的 `openapi-hyperloop.yml` 与控制台的 `openapi-dashboard.yml`，
服务端与客户端代码都由它们生成。

**openEuler** —— ARM 适配版与单机离线版使用的宿主发行版。
它的内核版本决定了 userfaultfd、HugeTLB 与 NBD 的可用能力，
也决定了构建期能装进 guest 的包。

**OpenTelemetry** —— 遥测框架，全书的 trace 与 metric 都经它导出。
它统一了「一次请求跨多个进程」的上下文传播，是排查跨节点问题的主要手段。

**ORCHESTRATOR_SERVICES** —— 环境变量，取值是 `orchestrator` 与 `template-manager`
的组合（逗号分隔），决定同一个二进制这次启动要暴露哪些 gRPC 服务。
代码里的默认值只有 `orchestrator`（`orchestrator/internal/cfg/model.go`）；
写成两个的部署才让一台机器既跑沙箱又跑构建。

**overlay** —— 两个不同层面上的同名概念：block 层的 `Overlay`
是「只读基底 + 可写缓存」的组合，写只进缓存、读先查缓存位图；
guest 内核里的 overlayfs 则是文件系统级的联合挂载。本书按上下文区分，不混用。

**Packer** —— 构建虚拟机镜像的工具，用来把 orchestrator 节点需要的内核、
Firecracker 二进制与依赖打进一个镜像家族，节点开机即可用。

**PostgreSQL** —— 主数据库，装团队、API key、模板、构建、集群这些需要事务的实体。
与之相对，沙箱的运行期状态放 Redis，指标放 ClickHouse。

**raw_exec** —— Nomad 的一种 driver，直接在宿主上跑二进制，不加容器隔离。
orchestrator、template-manager 与几个清理作业都用它，
因为它们需要 `/dev/kvm`、网络命名空间与宿主目录这些容器里拿不到的东西。

**Redis** —— 沙箱运行期状态与沙箱目录的存储。它承担的是高频读写、
可以容忍短暂陈旧的那一类数据：目录键、团队索引、并发占位。
持久实体不放这里。

**sandbox ID** —— 沙箱的对外标识，也是节点上 sandbox map 的键、
Redis 里各种索引的成员、以及访问域名里的那一段。
它与 ExecutionID、LifecycleID 的区别是：sandbox ID 跨 pause 与 resume 保持不变。

**systemd** —— 成品沙箱里的 PID 1，负责拉起 envd 与用户配置的服务。
构建期的 provision 阶段还没有它，那一步用 busybox 顶替。

**tap** —— 宿主侧的虚拟网卡，Firecracker 把 guest 的网卡后端接在它上面。
每个网络槽位有一个 tap，位于该槽位的 netns 里。

**team_limits** —— PostgreSQL 里的一个视图，用横向连接把团队的档位基线
与当前生效的 addon 增量相加，得到实际配额。
认证时一次 join 就把团队与配额一起取回，所以配额是鉴权的副产品，不是单独一次查询。

**Terraform** —— 描述云上基础设施的工具，上游用它建网络、节点池、
数据库与 Nomad 集群本身。它与 Packer 的分工是：Packer 造镜像，Terraform 用镜像造机器。

**uffd / userfaultfd** —— Linux 的用户态缺页机制：把某段虚拟内存的缺页
交给一个用户态进程处理。e2b 用它做按需恢复，
让 guest 内存不必在 resume 时整份读入；写保护模式还用来做脏页判定。
`uffd` 在书中既指这个机制，也指 orchestrator 里那个内存后端。

**veth** —— 成对出现的虚拟以太网设备，一端在沙箱的 netns 里，
一端在宿主的默认命名空间里，是沙箱出网的那一跳。

---

## 延伸阅读

- [写作规约](STYLE.md)：第二节的版本称谓口径、第三节的固定译法表，本篇的中文词条即由它扩写而来。
- [编写计划](OUTLINE.md)：全部篇目的清单与要点，用来确认某个术语该去哪一篇找。
- [第 89 篇 · 代码地图 §1](89-code-map.md#1-上游-202609-的目录)：从术语落到目录与文件。
- [第 90 篇 · 环境变量与配置项总表 §2](90-config-reference.md#2-环境变量)：`ORCHESTRATOR_SERVICES`、
  `cacheScope` 之类配置项的默认值与读取位置。
- [第 91 篇 · 端口、路径与存储键总表](91-ports-paths-keys.md)：hyperloop 端口、
  `sandbox:catalog:` 键、对象存储路径的完整清单。
