# 71 · 配置项、环境变量与端口总表

> 本附录把散在全书的配置面集中成几张表：节点配置文件 `config/default.toml` 的全部节与键（代码默认与默认文件两列并列，不一致处标出）、
> ublk-daemon 自己再读的那几个键、gateway 与 scheduler 的 JSON 配置与环境变量覆盖、所有被代码或部署脚本读取的环境变量，以及每个监听端口的来源。
> 每一行都链到详细讲解的篇目与小节。
>
> **读者**：部署、调参、排查「改了配置为什么没生效」的读者。　**预备**：[第 11 篇 · 配置体系](11-configuration.md)、[第 60 篇 · 部署形态](60-deployment.md)。
> **代码**：`src/cfg.rs`、`src/cfg/image.rs`、`src/cfg/network.rs`、`config/default.toml`、`storage/ublk-daemon/src/main.rs`、`storage/ublk-daemon/src/client.rs`、
> `services/shared/config/config.go`、`services/gateway/cmd/main.go`、`services/scheduler/cmd/main.go`、`src/bin/server.rs`、`deploy/`

---

## 0. 本篇要回答的问题

1. `config/default.toml` 有哪些节与键？每个键在代码里的默认值是什么，与默认文件里写的值是否一致？
2. 哪些键可以用环境变量覆盖？哪些环境变量根本不经过 confique，由谁在什么时候读？
3. ublk-daemon 从同一份 TOML 里读哪几个键，默认值与 `server` 有什么不同？
4. gateway 与 scheduler 的 JSON 配置有哪些键，代码默认、仓库附带的三份配置与环境变量覆盖各是什么？
5. 一个节点、一套集群各监听哪些端口？每个端口在代码或部署清单的哪一处定义？
6. 代码、默认文件、文档与部署清单之间有哪些不一致，后果是什么？

---

## 1. 怎样读这些表

**两列默认值。** 节点配置由 confique 分层加载，优先级是**环境变量 > 文件 > 代码默认**（[第 11 篇 §2](11-configuration.md#2-加载与归一化)）。
表里「代码默认」一列取自 `src/cfg.rs` 与 `src/cfg/*.rs` 字段上的 `#[config(default = …)]`；字段没有 default 而类型是 `Option` 的写「未设置」，并在作用栏说明未设置时代码怎样回退。
「default.toml」一列取自仓库的 `config/default.toml`：写了值的照抄，整行被注释掉的写「（注释）」，即文件不提供、取代码默认。
两列不同时，default.toml 一列的值加粗并标「≠」；它只在**有配置文件**时生效，没有配置文件时节点静默地按代码默认运行（[第 11 篇 §6.3](11-configuration.md#63-没有配置文件时)）。

**路径展开。** 带 `$AENV_HOME` 的值在加载后由 `AppConfig::normalize()` 展开为归一化后的 `home_path`；`$AENV_RUNTIME` 只在 `[ublk].daemon_socket_path` 上展开；
其它相对路径以配置文件所在目录为基准（[第 11 篇 §2.2](11-configuration.md#22-路径归一化)）。表里照写未展开的形式。

**环境变量。** 作用栏里出现 `env: NAME` 的键可被同名环境变量覆盖；全部这样的变量在 §5.1 汇总。没有标注的键只能写在文件里。

**篇目。** 「篇目」一栏写成「篇号 §小节」并链接；同一键在多篇出现时只列详讲的一两处。

---

## 2. 节点配置：`config/default.toml`

### 2.1 顶层键

| 键 | 代码默认 | default.toml | 作用 | 篇目 |
|---|---|---|---|---|
| `home_path` | `/var/lib/aenv` | `/var/lib/aenv` | 持久状态、缓存、日志与生成文件的根；相对路径以配置文件目录为基准。env: `AENV_HOME_PATH` | [10 §5](10-node-process-and-object-model.md#5-节点磁盘布局)、[11 §2.2](11-configuration.md#22-路径归一化) |
| `runtime_path` | `/run/aenv` | （注释） | socket 与 netns 等临时状态。env: `AENV_RUNTIME_PATH` | [10 §5](10-node-process-and-object-model.md#5-节点磁盘布局) |
| `deps_path` | `$AENV_HOME/deps` | （注释） | 下载的运行期依赖（Firecracker、内核、tools 盘、overlaybd 工具、regctl）。env: `AENV_DEPS_PATH`。ublk-daemon 对它的缺省不同，见 §3 | [59 §3.2](59-host-setup-and-privileges.md#32-版本化路径与存在即已安装) |
| `virtualization_mode` | `kvm` | `kvm` | 节点级虚拟化后端 `kvm` / `pvm`；`pvm` 时归一化强制关闭脏页跟踪。env: `AENV_VIRTUALIZATION_MODE` | [61 §2.1](61-pvm.md#21-virtualizationmode)、[11 §2.3](11-configuration.md#23-改写与清洗) |

### 2.2 依赖与 guest 启动：`[firecracker]` `[kernel]` `[tools]` `[overlaybd]`

| 键 | 代码默认 | default.toml | 作用 | 篇目 |
|---|---|---|---|---|
| `[firecracker].binary_path` | 未设置 | （注释） | 指定现成的 Firecracker 可执行文件，替代按 manifest 下载 | [59 §3.2](59-host-setup-and-privileges.md#32-版本化路径与存在即已安装) |
| `[firecracker].version` / `url` | 未设置 | 无此行 | 覆盖 `config/deps_manifest.toml` 编进二进制的版本与下载地址 | [59 §3.1](59-host-setup-and-privileges.md#31-manifest编进二进制的版本表) |
| `[firecracker].boot_args` | 未设置，退回常量 `DEFAULT_BOOT_ARGS` | **完整内核命令行（≠）** | 整条 guest 内核命令行，改它是替换不是追加；文件值比代码常量多 `mitigations=off`、`init=/init`、`page_reporting.page_reporting_order=6` | [11 §6.1](11-configuration.md#61-内核命令行的两份默认) |
| `[firecracker].allowed_extra_boot_args_prefixes` | 未设置 | （注释） | 冷启动请求 `extraBootArgs` 的前缀白名单；未设置即一概不允许 | [14 §3.4](14-sandbox-api.md#34-冷启动-sandboxes-cold) |
| `[firecracker].socket_timeout_secs` | `3` | `3` | 等 Firecracker API socket 出现的上限 | [25 §4.3](25-backend-and-firecracker-process.md#43-等-socket-出现) |
| `[firecracker].socket_poll_ms` | `1` | `1` | 等 socket 的轮询间隔 | [25 §4.3](25-backend-and-firecracker-process.md#43-等-socket-出现) |
| `[firecracker].work_dir` | 未设置，归一化为 `$AENV_HOME/firecracker-work` | （注释） | 每沙箱工作目录（socket、本地日志、可写层）。env: `AENV_FIRECRACKER_WORK_DIR` | [26 §5.4](26-sandbox-block-devices.md#54-可写层住在工作目录里) |
| `[firecracker].serial_dir` | 未设置，归一化为 `$AENV_HOME/logs/serial` | （注释） | 持久串口日志目录，按沙箱 ID 分组；只设它不会打开日志。env: `AENV_FIRECRACKER_SERIAL_DIR` | [11 §2.2](11-configuration.md#22-路径归一化) |
| `[firecracker].log_level` | 未设置 | （注释） | 非空时打开 stdout / stderr 捕获与 `firecracker.log`；未设置或空串全部关闭 | [25](25-backend-and-firecracker-process.md) |
| `[kernel].image_path` | 未设置 | （注释） | 指定现成的未压缩内核镜像 | [59 §3.2](59-host-setup-and-privileges.md#32-版本化路径与存在即已安装) |
| `[kernel].version` / `url` | 未设置 | 无此行 | 覆盖 manifest 里的内核版本与地址 | [59 §3.1](59-host-setup-and-privileges.md#31-manifest编进二进制的版本表) |
| `[tools].drive_path` | 未设置 | （注释） | 导入本地 ext4 tools 盘，须同时给 `version` | [26 §7](26-sandbox-block-devices.md#7-tools-盘的来源与版本) |
| `[tools].version` / `url` | 未设置 | `version`（注释）；`url` 无此行 | tools 盘版本与镜像地址模板，覆盖 manifest | [26 §7](26-sandbox-block-devices.md#7-tools-盘的来源与版本) |
| `[tools].control_plane_port` | `49983` | `49983` | 宿主连接 guest 内 envd 的端口；随快照记录（见 §6.1 的约束） | [28 §3.2](28-mmds-and-envd.md#32-地址) |
| `[overlaybd].version` / `url` / `package_url` | 整节未设置 | 无此节 | 覆盖 overlaybd 工具的版本与下载地址；节存在时 `version` 必填 | [59 §3.1](59-host-setup-and-privileges.md#31-manifest编进二进制的版本表) |

### 2.3 镜像：`[image.resolver]` `[image.cache.*]`

| 键 | 代码默认 | default.toml | 作用 | 篇目 |
|---|---|---|---|---|
| `[image.resolver].default_image` | `ubuntu:24.04` | `ubuntu:24.04` | 模板构建省略 `fromImage` 时的 rootfs 镜像 | [52 §2.1](52-template-builder.md#21-镜像-base冷启动) |
| `[image.resolver].search_registries` | `["docker.io", "ghcr.io"]` | 同左 | 短名依次尝试的 registry | [45 §2.1](45-oci-to-overlaybd.md#21-候选-registry) |
| `[image.resolver].convert_standard_oci` | `true` | `true` | 是否把标准 OCI tar 层转换成本地 overlaybd 提交；`false` 时只接受 overlaybd-native | [45 §4](45-oci-to-overlaybd.md#4-标准-oci逐层转换) |
| `[image.resolver].allowed_registries` | 未设置 | （注释） | registry 白名单；未设置全部允许，显式空列表全部拒绝，被拒返回 4xx | [45 §2.1](45-oci-to-overlaybd.md#21-候选-registry) |
| `[image.resolver].try_referrers_overlaybd_prefixes` | `[]` | `[]` | 哪些镜像引用前缀去查 OCI referrers 加速层（`starts_with` 匹配） | [45 §2.4](45-oci-to-overlaybd.md#24-referrers给标准镜像找加速层) |
| `[image.cache].root_dir` | `$AENV_HOME/image-cache` | （注释） | 转换提交、解析索引、配置与远端块缓存的根 | [45 §5.1](45-oci-to-overlaybd.md#51-目录) |
| `[image.cache].capacity_gb` | 未设置，不做容量驱逐 | **`100`（≠）** | 本地提交预算；只在 GC 打开时驱逐 | [45 §5.4](45-oci-to-overlaybd.md#54-容量驱逐按源配置的-lru) |
| `[image.cache.remote_blocks].max_size_gb` | `10` | **`100`（≠）** | registry 远端块缓存上限，写入生成的 overlaybd 配置 | [39 §2.4](39-block-cache-and-background-download.md#24-一个节点上的四个缓存目录)、[39 §4.1](39-block-cache-and-background-download.md#41-记账与两条水位) |
| `[image.cache.gc].enabled` | `true` | `true` | 后台对账并删除无引用的硬提交 | [45 §5.5](45-oci-to-overlaybd.md#55-宁可不删的-gc) |
| `[image.cache.gc].interval_secs` | `1800` | `1800` | GC 周期 | [45 §5.5](45-oci-to-overlaybd.md#55-宁可不删的-gc) |
| `[image.cache.gc].min_age_secs` | `600` | `600` | 容量驱逐前的最小空闲时长 | [45 §5.4](45-oci-to-overlaybd.md#54-容量驱逐按源配置的-lru) |
| `[image.cache.gc].high_watermark_ratio` | `0.95` | `0.95` | 达到 `capacity_gb` 的这一比例开始驱逐；须在 (0, 1] | [45 §5.4](45-oci-to-overlaybd.md#54-容量驱逐按源配置的-lru) |
| `[image.cache.gc].low_watermark_ratio` | `0.70` | `0.70` | 驱逐到这一比例为止；不得高于高水位 | [45 §5.4](45-oci-to-overlaybd.md#54-容量驱逐按源配置的-lru) |

### 2.4 集群与扩展：`[p2p]` `[custom_extension]` `[cluster]` `[sandbox_proxy]`

| 键 | 代码默认 | default.toml | 作用 | 篇目 |
|---|---|---|---|---|
| `[p2p].enabled` | `false` | `false` | P2P 制品传输总开关（文件注释标为实验性） | [58 §3.1](58-p2p-artifact-transport.md#31-一个节点上起了什么) |
| `[p2p].transport` | `iroh` | `iroh` | 传输实现 `iroh` / `disabled` | [58 §3](58-p2p-artifact-transport.md#3-iroh-后端) |
| `[p2p].store_dir` | `$AENV_HOME/p2p/store` | （注释） | 传输层的本地内容存储 | [58 §3.1](58-p2p-artifact-transport.md#31-一个节点上起了什么) |
| `[p2p].listen_addr` | `0.0.0.0:0` | `0.0.0.0:0` | iroh 端点地址；端口 0 由内核选 | [58 §3.1](58-p2p-artifact-transport.md#31-一个节点上起了什么) |
| `[p2p].lookup_timeout_ms` | `5000` | `5000` | 向 peer 目录查询的超时 | [58 §3.3](58-p2p-artifact-transport.md#33-lookup三级) |
| `[p2p].fetch_timeout_ms` | `30000` | `30000` | 从 peer 取制品的超时 | [58 §3.4](58-p2p-artifact-transport.md#34-fetch校验与-gc) |
| `[p2p].peer_discovery_refresh_interval_secs` | `5` | `5` | 向 scheduler 刷新 peer 列表的间隔，小于 1 按 1 | [58 §3.5](58-p2p-artifact-transport.md#35-scheduler-侧的索引) |
| `[custom_extension].url` | 未设置，即关闭 | （注释） | lifecycle hook 服务地址；关闭时非空 `customExtensionParams` 被拒。env: `AENV_CUSTOM_EXTENSION_URL` | [33 §2](33-custom-extension-hooks.md#2-契约四个-hook) |
| `[custom_extension].timeout_ms` | `5000` | （注释） | hook 调用超时；文件注释称不管 stop，第 33 篇核实 stop 同样受限 | [33 §6](33-custom-extension-hooks.md#6-代价与边界) |
| `[cluster].scheduler_endpoint` | 未设置 | （注释） | scheduler gRPC 地址，供心跳上报与 P2P peer 发现；去空白、空串视为未设置。env: `AENV_OBSERVABILITY_SCHEDULER_ENDPOINT` | [57 §3.1](57-heartbeat-and-cpu-intersection.md#31-节点侧observabilityreporter) |
| `[sandbox_proxy].domains` | `[]` | `[]` | Host 路由 `{port}-{sandboxID}.{domain}` 接受的域名后缀，第一个对外通告。env: `AENV_SANDBOX_PROXY_DOMAINS`（逗号分隔） | [17 §2](17-reverse-proxy.md#2-三个入口) |

### 2.5 网络与机器规格：`[network.*]` `[machine.*]`

| 键 | 代码默认 | default.toml | 作用 | 篇目 |
|---|---|---|---|---|
| `[network.egress].always_denied_cidrs` | 六段私有与保留网段 | 同左 | 在每沙箱 `allowOut` / `denyOut` 之前生效的节点级拒绝表 | [30 §3.1](30-egress-policy-and-proxy.md#31-链的结构) |
| `[network.internal].host_interaction_cidr` | `10.11.0.0/16` | `10.11.0.0/16` | 每槽位宿主交互地址池，至少 32768 个地址 | [29 §2.2](29-network-slots.md#22-地址计划) |
| `[network.internal].veth_cidr` | `10.12.0.0/16` | `10.12.0.0/16` | 每槽位 veth 对地址池，至少 65536 个地址；两池与固定的 `169.254.0.20/30` 不得重叠 | [29 §2.2](29-network-slots.md#22-地址计划) |
| `[machine].mem_size_mib` | `1024` | `1024` | 请求未给时的 guest 内存 | [14 §3.1](14-sandbox-api.md#31-sandboxes_post-的步骤) |
| `[machine].vcpu_count` | `2` | `2` | 请求未给时的 vCPU 数 | [14 §3.1](14-sandbox-api.md#31-sandboxes_post-的步骤) |
| `[machine.disk_rate_limit].enabled` | `false` | （注释） | 每沙箱 virtio-blk 限流开关；关闭时下面四项不校验 | [11 §2.4](11-configuration.md#24-校验) |
| `[machine.disk_rate_limit].bandwidth_bytes_per_sec` / `bandwidth_burst_bytes` | `0` / `0` | （注释） | 持续带宽与一次性突发；0 表示不限，有突发须有持续值 | [11 §2.4](11-configuration.md#24-校验) |
| `[machine.disk_rate_limit].iops` / `iops_burst` | `0` / `0` | （注释） | 持续 IOPS 与一次性突发，规则同上 | [11 §2.4](11-configuration.md#24-校验) |

### 2.6 沙箱与 orchestrator：`[envd]` `[sandbox]` `[volume]` `[orchestrator]`

| 键 | 代码默认 | default.toml | 作用 | 篇目 |
|---|---|---|---|---|
| `[envd].version` | `0.5.15` | `0.5.15` | tools 盘里 envd 应有的版本，运行时不核对 | [28 §3.1](28-mmds-and-envd.md#31-来源与拉起) |
| `[envd].init_timeout_secs` | `60` | `60` | 等 envd 就绪与 `/init` 的上限 | [28 §4.1](28-mmds-and-envd.md#41-wait_for_ready-的顺序) |
| `[envd].poll_ms` | `3` | `3` | envd 就绪轮询间隔 | [28 §4.1](28-mmds-and-envd.md#41-wait_for_ready-的顺序) |
| `[sandbox].access_token_hash_seed` | 未设置，用 `$AENV_HOME/secrets` 下的节点本地种子 | （注释） | 派生 envd 与流量 token 的 HMAC 种子；跨节点恢复要求各节点一致。env: `AENV_SANDBOX_ACCESS_TOKEN_HASH_SEED` | [13 §3.1](13-authentication.md#31-派生) |
| `[volume].max_size_mb` | `262144` | `262144` | 单个持久卷上限 | [31 §2.1](31-extra-drives-and-volumes.md#21-入口校验) |
| `[volume].max_volume_count` | `4` | `4` | 单沙箱可挂卷数，须在 1 到 `MAX_VOLUME_MOUNTS`（24）之间 | [31 §2.1](31-extra-drives-and-volumes.md#21-入口校验) |
| `[orchestrator].metrics_interval_secs` | `15` | `15` | guest 指标采样间隔，0 关闭 | [24 §3.2](24-metrics-and-events.md#32-采样任务) |
| `[orchestrator].metrics_retention_secs` | `3600` | `3600` | guest 指标内存保留时长 | [24 §3.5](24-metrics-and-events.md#35-存储与查询) |
| `[orchestrator].auto_evict_interval_ms` | `1000` | `1000` | 过期回收任务的节拍 | [23 §4.1](23-auto-eviction-and-ttl.md#41-节拍与退出) |
| `[orchestrator].default_sandbox_timeout_secs` | `15` | `15` | v1 创建与 resume 未带 TTL 时的缺省（v2 另有 300 s） | [14 §4](14-sandbox-api.md#4-四个改-ttl-的入口) |
| `[orchestrator].auto_resume_min_sandbox_timeout_secs` | `300` | `300` | 代理触发自动恢复时 TTL 的下限 | [23 §7](23-auto-eviction-and-ttl.md#7-与代理自动恢复的联动) |
| `[orchestrator].persisted_sandbox_store_path` | `$AENV_HOME/persisted-sandboxes` | （注释） | 暂停沙箱的持久记录与产物，重启后由 `load_all()` 恢复。env: `AENV_PERSISTED_SANDBOX_STORE_PATH` | [22 §3](22-persistence-across-restarts.md#3-记录与目录) |

### 2.7 快照仓库：`[snapshot.*]` `[backend.*]`

| 键 | 代码默认 | default.toml | 作用 | 篇目 |
|---|---|---|---|---|
| `[snapshot].local_cache_path` | `$AENV_HOME/snapshot-local-cache` | （注释） | 节点本地快照制品缓存。env: `AENV_SNAPSHOT_LOCAL_CACHE_PATH` | [49 §6](49-resolve-and-artifact-cache.md#6-localartifactcache) |
| `[snapshot].repository_backend` | `posix_fs` | `posix_fs` | 持久仓库后端 `posix_fs` / `oss` | [47 §2](47-posix-repository.md#2-目录布局)、[48 §2](48-object-storage-repository.md#2-对象布局) |
| `[snapshot].p2p_enabled` | `true` | `true` | 提交后把制品发布到 P2P、对象存储解析时先试 P2P；须 `[p2p].enabled` 同时为真 | [58 §4](58-p2p-artifact-transport.md#4-三个消费者与-key-空间) |
| `[snapshot.image_publish].enabled` | `false` | （注释） | 仅对象存储：把兼容的 rootfs 以 `agentenv-snapshot-{id}` 回推源 registry | [50](50-rootfs-as-oci-image.md) |
| `[snapshot.publish_compression].enabled` | `true` | `true` | 上传对象存储时压缩内存层与增量可写层；本地层恒为 raw | [35 §7.1](35-zfile-compression.md#71-本地-raw发布时压缩)、[48 §4.2](48-object-storage-repository.md#42-发布压缩digest-描述上传的字节) |
| `[snapshot.publish_compression].algorithm` | `lz4` | `lz4` | `lz4` / `zstd` | [35 §7.1](35-zfile-compression.md#71-本地-raw发布时压缩) |
| `[snapshot.publish_compression].workers` | `1` | `1` | 压缩 4 KiB 块的工作线程数，不改变输出布局 | [35 §7.1](35-zfile-compression.md#71-本地-raw发布时压缩) |
| `[snapshot.memory_startup_pack].enabled` | `false` | （注释） | 发布时录制启动首触页并生成 startup manifest | [43 §2.1](43-startup-pack-and-prefetch.md#21-何时录谁来等) |
| `[snapshot.memory_startup_pack].record_min_window_ms` / `record_quiet_ms` / `record_max_window_ms` | `200` / `300` / `2000` | （注释） | 录制窗口的最短、静默判停与硬上限 | [43 §2.4](43-startup-pack-and-prefetch.md#24-录制窗口) |
| `[snapshot.memory_startup_pack].record_budget_secs` | `10` | （注释） | 准备、录制与打包的总预算，超出放弃 pack 不放弃发布 | [43 §2.5](43-startup-pack-and-prefetch.md#25-节点侧的等待与收尾) |
| `[snapshot.memory_startup_pack].max_pack_bytes` | `1073741824` | （注释） | 单个 pack 页数据上限 | [43 §3.1](43-startup-pack-and-prefetch.md#31-字节布局) |
| `[snapshot.memory_startup_pack].consume_enabled` | `false` | （注释） | resume 时是否消费 manifest，与录制独立 | [43 §4.1](43-startup-pack-and-prefetch.md#41-开关与解析) |
| `[snapshot.memory_startup_pack].consume_timeout_secs` | `30` | （注释） | 一个 manifest 排队加读取的上限，超时退回按需读 | [43 §4.1](43-startup-pack-and-prefetch.md#41-开关与解析) |
| `[backend.posix_fs].snapshot_store` | `posix_fs` 而无此节时补成 `$AENV_HOME/snapshot-store` | （注释） | POSIX 仓库根；多节点须指向共享文件系统。代码声明了 env `AENV_SNAPSHOT_STORE`，推论：不生效，见 §7 | [47 §2](47-posix-repository.md#2-目录布局) |
| `[backend.oss].endpoint` / `bucket` / `region` / `prefix` | 整节未设置 | （注释） | 对象存储位置；节存在时 `endpoint` 与 `bucket` 必填 | [48 §2](48-object-storage-repository.md#2-对象布局) |
| `[backend.oss].addressing_style` | 未设置，按 endpoint 自动判断 | （注释） | `virtual` / `path` | [48 §2](48-object-storage-repository.md#2-对象布局) |
| `[backend.oss].credential_process` / `access_key_id` / `access_key_secret` / `security_token` | 未设置 | （注释） | 两种凭证来源；文件注释称前者优先，代码两者同配直接报错 | [48 §4.4](48-object-storage-repository.md#44-分片上传与凭证) |
| `[backend.oss].cache_max_size_gb` | 未设置，回退 10 GiB（`DEFAULT_MAX_SIZE_BYTES`） | （注释，示例 10） | 对象存储制品的节点本地缓存上限 | [49 §6](49-resolve-and-artifact-cache.md#6-localartifactcache) |

### 2.8 块设备：`[ublk]` `[ublk.overlaybd]`

| 键 | 代码默认 | default.toml | 作用 | 篇目 |
|---|---|---|---|---|
| `[ublk].daemon_binary_path` | 未设置，归一化为 `$AENV_HOME/ublk/uvm-ublk-daemon` | （注释） | ublk-daemon 可执行文件。env: `AENV_UBLK_DAEMON_BINARY_PATH` | [41 §2.1](41-ublk-daemon.md#21-拉起与就绪) |
| `[ublk].daemon_socket_path` | `$AENV_RUNTIME/ublk-daemon.sock` | （注释） | daemon 控制 socket，经 `--socket-path` 传给 daemon | [41 §3.1](41-ublk-daemon.md#31-帧与连接) |
| `[ublk].daemon_log_path` | 未设置，归一化为 `$AENV_HOME/logs/ublk-daemon.log` | （注释） | daemon 日志，经 `--log-file` 传入 | [41 §2.1](41-ublk-daemon.md#21-拉起与就绪) |
| `[ublk].daemon_metrics_listen_addr` | `0.0.0.0:9103` | `0.0.0.0:9103` | daemon 的 Prometheus 端点，空串关闭；经 `--metrics-listen-addr` 传入。env: `AENV_UBLK_DAEMON_METRICS_LISTEN_ADDR` | [24 §5.1](24-metrics-and-events.md#51-记录器与暴露位置) |
| `[ublk.overlaybd].global_config_path` | `$AENV_HOME/overlaybd/overlaybd-global.json` | （注释） | `server` 每次启动重写的 rootfs 用 overlaybd 全局配置；与其它三份生成配置不得重名 | [59 §3.4](59-host-setup-and-privileges.md#34-tools-盘与-overlaybd-全局配置)、[11 §2.4](11-configuration.md#24-校验) |
| `[ublk.overlaybd].read_only` | `false` | `false` | rootfs 设备不带可写层 | [26 §5.1](26-sandbox-block-devices.md#51-运行时物化) |
| `[ublk.overlaybd].runtime_upper_mode` | `hybridLogStructured` | `hybridLogStructured` | 新物化可写层的格式 `logStructured` / `hybridLogStructured` / `sparse`；已有可写层保持原格式 | [36 §4.4](36-read-write-paths-and-rw-layouts.md#44-agentenv-用哪一种) |
| `[ublk.overlaybd].allow_shrink` | `false` | `false` | 冷启动是否允许缩小 rootfs；扩大恒允许，resume 从不改大小 | [26 §5.3](26-sandbox-block-devices.md#53-大小只在冷启动时改变) |
| `[ublk.overlaybd].resize_timeout_secs` | `120` | `120` | 冷启动扩容工具超时，须为正；daemon 另读一次，见 §3 | [41 §5.2](41-ublk-daemon.md#52-为什么扩容要调-c-工具) |
| `[ublk.overlaybd].remote_io_workers` | `4` | `4` | Rust 版 overlaybd 远端 I/O 专用 runtime 的线程数，写入生成配置的 `remoteIoWorkers`；须为正 | [38 §4.3](38-virtualfile-chain-and-remote-io.md#43-runtimedispatchfile) |
| `[ublk.overlaybd].download_enable` | `false` | `false` | rootfs 远端层的层级后台下载 | [39 §5.1](39-block-cache-and-background-download.md#51-谁会被后台下载) |
| `[ublk.overlaybd].p2p_lookup_timeout_ms` | `300` | `300` | overlaybd 经 P2P 查描述符的超时，超时按可缓存的未命中处理 | [58 §5.2](58-p2p-artifact-transport.md#52-一次范围读) |
| `[ublk.overlaybd].p2p_fetch_range_timeout_ms` | `2000` | `2000` | 前台范围读走 P2P 的超时，超时回源 | [58 §5.3](58-p2p-artifact-transport.md#53-中途出错为什么不回退) |

### 2.9 预热池：`[pool.*]`

| 键 | 代码默认 | default.toml | 作用 | 篇目 |
|---|---|---|---|---|
| `[pool].low_watermark` | `2` | `2` | 三个池共用的起始补充目标；不得高于高水位 | [32 §2.1](32-warm-pools.md#21-补多少排多少) |
| `[pool].high_watermark` | `64` | `64` | 取用把池抽空时补充目标增长的上限 | [32 §2.1](32-warm-pools.md#21-补多少排多少) |
| `[pool.network].enabled` | `true` | 无此行 | 与 `maintenance_enabled` 相与后决定后台补充 | [32 §3](32-warm-pools.md#3-网络槽位池) |
| `[pool.network].maintenance_enabled` | `true` | `true` | 网络槽位池后台补充 | [32 §3](32-warm-pools.md#3-网络槽位池) |
| `[pool.network].startup_prewarm` | `true` | 无此行 | 启动时预热网络槽位 | [32 §3](32-warm-pools.md#3-网络槽位池) |
| `[pool.block].enabled` | `true` | `true` | 可复用的 overlaybd ublk 设备池；daemon 侧缺省不同，见 §3 | [32 §4](32-warm-pools.md#4-块设备池) |
| `[pool.block].maintenance_enabled` | `true` | 无此行 | 块设备池恒按请求补充，`block_pool_config()` 写死 `false`，此键不起作用 | [32 §4](32-warm-pools.md#4-块设备池) |
| `[pool.block].startup_prewarm` | `true` | （注释） | 文件注释描述的是 daemon 语义：省略则按内核 `UBLK_F_UPDATE_SIZE` 决定，见 §3 | [11 §5](11-configuration.md#5-同一个文件的第二个读者) |
| `[pool.firecracker].enabled` | `true` | `true` | 为 resume 预先拉起的 Firecracker 进程池 | [32 §5](32-warm-pools.md#5-firecracker-进程池) |
| `[pool.firecracker].maintenance_enabled` | `true` | 无此行 | 进程池后台补充 | [32 §5.1](32-warm-pools.md#51-填充) |
| `[pool.firecracker].startup_prewarm` | `true` | `true` | `server` 启动时填充进程池 | [32 §5.1](32-warm-pools.md#51-填充) |
| `[pool.firecracker].fill_concurrency` | `4` | `4` | 一批补充里并发创建的进程数，不得为 0 | [32 §5.1](32-warm-pools.md#51-填充) |

### 2.10 内存快照：`[memory_snapshot.*]`

| 键 | 代码默认 | default.toml | 作用 | 篇目 |
|---|---|---|---|---|
| `[memory_snapshot].overlaybd_global_config_path` | `$AENV_HOME/overlaybd/mem-overlaybd-global.json` | （注释） | 内存快照设备专用的生成配置，有独立的块缓存目录 | [42 §4.1](42-memory-snapshot-over-ublk.md#41-取设备) |
| `[memory_snapshot].track_dirty_pages` | `true` | `true` | 用 AENV 补丁版 Firecracker 的脏页区间代替 mincore；PVM 下强制关闭。env: `AGENTENV_MEMORY_SNAPSHOT_TRACK_DIRTY_PAGES` | [42 §5](42-memory-snapshot-over-ublk.md#5-关闭脏页跟踪时)、[61 §4.1](61-pvm.md#41-两道关卡) |
| `[memory_snapshot.background_download].enable` | `true` | `true` | 内存层远端缺块的后台下载，不早于 envd 就绪 | [39 §5](39-block-cache-and-background-download.md#5-后台下载调度器)、[39 §6.2](39-block-cache-and-background-download.md#62-envd-就绪信号) |
| `[memory_snapshot.background_download].delay` / `delay_extra` | `0` / `1` | `0` / `1` | 基础延迟与随机附加延迟的开区间上界（1 即无抖动） | [39 §5.2](39-block-cache-and-background-download.md#52-任务的三段生命) |
| `[memory_snapshot.background_download].try_cnt` | `5` | `5` | 每个后台任务的重试次数 | [39 §5.4](39-block-cache-and-background-download.md#54-超时重发与任务重试) |
| `[memory_snapshot.background_download].block_size` | `16777216` | `16777216` | 每次源请求的字节数，上限 64 MiB | [39 §5.3](39-block-cache-and-background-download.md#53-chunk-与块两种粒度共用一张位图) |
| `[memory_snapshot.background_download].concurrency` | `4` | `4` | 每层并发源读 1–16；与 `block_size` 之积不超过 256 MiB | [39 §5.2](39-block-cache-and-background-download.md#52-任务的三段生命) |
| `[memory_snapshot.background_download].max_inflight_blocks` | `16` | `16` | 后端全局 chunk 上限 1–128；与 `block_size` 之积不超过 2 GiB | [39 §5.2](39-block-cache-and-background-download.md#52-任务的三段生命) |

### 2.11 构建、观测与身份：`[template_build]` `[observability.*]` `[node_identity]`

| 键 | 代码默认 | default.toml | 作用 | 篇目 |
|---|---|---|---|---|
| `[template_build].max_concurrent_builds` | `4` | `4` | 每节点并发 BuildKit 会话上限（占用到发布与清理结束），超出返回 429；步骤构建路径不受它约束，与文件注释「每节点上限」不符 | [15 §4.2](15-template-build-api.md#42-受理put-builder)、[15 §3.3](15-template-build-api.md#33-这条路径没有会话) |
| `[template_build].builder_image` | `docker.io/moby/buildkit:v0.33.0` | 同左 | Dockerfile 构建用的 builder 镜像 | [53 §3](53-buildkit-in-microvm.md#3-builder-模板) |
| `[template_build].builder_cpu_count` | `16` | `16` | builder VM vCPU，1–255 | [53 §3](53-buildkit-in-microvm.md#3-builder-模板) |
| `[template_build].builder_memory_mb` | `32768` | `32768` | builder VM 内存，不少于 256 MiB | [53 §3](53-buildkit-in-microvm.md#3-builder-模板) |
| `[template_build].cache_size_mb` | `65536` | `65536` | `/var/lib/buildkit` 持久盘大小，不少于 1024 MiB，只影响新缓存 | [53 §5](53-buildkit-in-microvm.md#5-缓存种子) |
| `[observability].enabled` | `true` | `true` | 暴露节点身份、主机指标与 orchestrator 运行指标 | [24 §5](24-metrics-and-events.md#5-prometheus-指标) |
| `[observability.scheduler_report].enabled` | `false` | `false` | 向 scheduler 发心跳与生命周期事件，需要 `[cluster].scheduler_endpoint`。env: `AENV_OBSERVABILITY_SCHEDULER_REPORT_ENABLED` | [57 §3.1](57-heartbeat-and-cpu-intersection.md#31-节点侧observabilityreporter) |
| `[observability.scheduler_report].interval_secs` | `5` | `5` | 心跳间隔。env: `AENV_OBSERVABILITY_REPORT_INTERVAL_SECS` | [57 §3.1](57-heartbeat-and-cpu-intersection.md#31-节点侧observabilityreporter) |
| `[node_identity].node_id` | 未设置，退回 `HOSTNAME`、`/proc/sys/kernel/hostname`、`/etc/hostname` | **`node-a`（≠）** | 节点 API 与心跳里的节点 ID。env: `AENV_NODE_ID` | [57 §3.2](57-heartbeat-and-cpu-intersection.md#32-scheduler-侧heartbeat) |
| `[node_identity].cluster_id` | 未设置，nil UUID | 全零 UUID | 逻辑集群 UUID；解析失败也降级为 nil UUID（打 warn）。env: `AENV_CLUSTER_ID` | [12](12-spec-driven-server.md) |
| `[node_identity].service_instance_id` | 未设置，每次启动生成 UUIDv7 | **`service-instance-a`（≠）** | 进程实例 ID，`UnregisterNode` 用它防误注销。env: `AENV_SERVICE_INSTANCE_ID` | [57 §4.1](57-heartbeat-and-cpu-intersection.md#41-unregisternode) |

### 2.12 两列不一致汇总

| 键 | 代码默认 | default.toml | 后果 |
|---|---|---|---|
| `[firecracker].boot_args` | `DEFAULT_BOOT_ARGS` | 含 `init=/init` 等的完整命令行 | 无配置文件时 guest 内核命令行不同；推论：没有 `init=/init` 时能否起来取决于 tools 盘布局 |
| `[image.cache].capacity_gb` | 未设置 | `100` | 无配置文件时 image-cache 不做容量驱逐 |
| `[image.cache.remote_blocks].max_size_gb` | `10` | `100` | 远端块缓存上限差十倍；文档 `reference.md` 写 100 |
| `[node_identity].node_id` | 主机名 | `node-a` | 多节点共用默认文件又不设 `AENV_NODE_ID` 时同名注册 |
| `[node_identity].service_instance_id` | 每次启动的 UUIDv7 | `service-instance-a` | 所有节点、每次重启都是同一个值，Compose 与 DaemonSet 都不覆盖，`UnregisterNode` 的实例校验失效 |
| `[pool.block].startup_prewarm` | `true` | 注释写的是 daemon 语义 | 读 `src/cfg.rs` 与读注释得出相反结论；实际生效的通常是 daemon 语义 |

---

## 3. ublk-daemon 读的键

`server` 拉起 daemon 时把 `ConfigManager::config_path()` 作为 `--config` 传入（`src/sandbox/ublk/device.rs` 的 `UblkDaemonConfig::from_app_config()`），
daemon 在 `storage/ublk-daemon/src/main.rs` 里用 serde 结构 `DaemonTomlConfig` 再解析同一个文件，不经 confique，也不做 `server` 那样的归一化与校验（[第 11 篇 §5](11-configuration.md#5-同一个文件的第二个读者)）。
daemon 进程继承 `server` 的环境（`UblkDaemonClient` 的 `Command` 没有清空环境），但只主动读 `AENV_HOME_PATH` 与 `AENV_DEPS_PATH` 两个变量。

| 键 | daemon 缺省 | `server` 侧代码默认 | 用途 | 差异 |
|---|---|---|---|---|
| `home_path` | `/var/lib/aenv`（`DEFAULT_HOME_PATH`）；先看 `AENV_HOME_PATH` | `/var/lib/aenv` | 展开 `deps_path` 里的 `$AENV_HOME` | 一致 |
| `deps_path` | `./env`（`DEFAULT_DEPS_PATH`），相对配置文件目录；先看 `AENV_DEPS_PATH` | `$AENV_HOME/deps` | 找 `overlaybd/bin/overlaybd-resize` | **不同**；`default.toml` 注释掉此键，推论：不设 `AENV_DEPS_PATH` 时冷启动扩容找不到工具 |
| `[ublk.overlaybd].resize_timeout_secs` | `120`（`DEFAULT_RESIZE_TIMEOUT_SECS`），须为正 | `120` | 扩容工具超时 | 一致；两边各自校验 |
| `[pool].low_watermark` / `high_watermark` | `2` / `64` | `2` / `64` | 块设备池水位 | 一致 |
| `[pool.block].enabled` | 未写时取命令行 `--enable-pool`，而有配置文件时 `server` 不传该参数，即为 `false` | `true` | 是否启用块设备池 | **不同**；推论：配置文件里省略此键时 `server` 认为池开着，daemon 不开池 |
| `[pool.block].startup_prewarm` | 未写时按内核是否支持 `UBLK_F_UPDATE_SIZE` | `true` | 首次用镜像后是否预热 | **不同** |

daemon 其余参数全部来自命令行。`UblkDaemonClient::new()`（`storage/ublk-daemon/src/client.rs`）组装的参数如下；池参数只在**没有**配置文件路径时才传，有配置文件时由 daemon 自己读上表。

| 参数 | 来源 | daemon 内缺省 | 篇目 |
|---|---|---|---|
| `--socket-path` | `[ublk].daemon_socket_path` | 必填 | [41 §3.1](41-ublk-daemon.md#31-帧与连接) |
| `--global-config` | `[ublk.overlaybd].global_config_path` | 必填 | [59 §3.4](59-host-setup-and-privileges.md#34-tools-盘与-overlaybd-全局配置) |
| `--resize-global-config` | `resolved_overlaybd_resize_global_config_path()` | 必填 | [41 §5.2](41-ublk-daemon.md#52-为什么扩容要调-c-工具) |
| `--config` | `ConfigManager::config_path()` | 未给则不读 TOML、不配置扩容工具 | [11 §5](11-configuration.md#5-同一个文件的第二个读者) |
| `--log-file` / `--log-level` | `[ublk].daemon_log_path` / 不传 | stderr / `info` | [41 §2.1](41-ublk-daemon.md#21-拉起与就绪) |
| `--metrics-listen-addr` | `[ublk].daemon_metrics_listen_addr` | `0.0.0.0:9103` | [24 §5.1](24-metrics-and-events.md#51-记录器与暴露位置) |
| `--enable-pool`、`--pool-low-watermark`、`--pool-high-watermark`、`--pool-startup-prewarm` | `block_pool_config()`，仅无配置文件时 | 不开池 | [32 §4](32-warm-pools.md#4-块设备池) |
| `--p2p-publish-url` | `from_app_config()` 恒为 `None` | 不发布 | [58 §5.1](58-p2p-artifact-transport.md#51-为什么是一个-http-服务) |

---
