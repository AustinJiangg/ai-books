# 70 · 代码地图：crate、模块与篇目

> 本附录把 AgentENV v0.2.3 的源码按目录与 crate 逐级列到子模块与主要文件：每一行给出行数、一句话职责与详细讲解它的篇目。
> [第 01 篇 §6](01-repo-map-and-versions.md#6-目录地图) 给的是顶层目录地图，本篇比它细一级，数字口径与它一致；生成代码单列在第 7 节。
>
> **读者**：要在仓库里找某个机制的实现、或想从一个文件反查本书讲解位置的读者。　**预备**：[第 01 篇 · 仓库地图、版本与依赖](01-repo-map-and-versions.md)。
> **代码**：整个仓库（tag `v0.2.3`，commit `6cccaa7842bd`）；统计命令见第 1 节。

---

## 0. 本篇要回答的问题

1. 一个顶层目录（如 `src/sandbox`、`storage/overlaybd`）内部分成哪些子模块，各有多大，各管什么？
2. 读到某个文件路径时，本书在哪一篇、哪一节讲它？
3. 哪些行数是测试，哪些代码是生成的、不该当作行为依据？

---

## 1. 口径

行数的统计方法与第 01 篇相同：对 v0.2.3 的 `git ls-files` 所列的普通文件逐个 `wc -l`，含注释、空行与测试，不跟随符号链接（`AGENTS.md` 是指向 `CLAUDE.md` 的链接，只算一次）。
下列五份生成代码整体排除，单列在第 7 节：`src/api/generated/`、`thirdparty/firecracker-client/`、`thirdparty/envd/http-client/`、`src/custom_extension_api/generated/`、`services/api/proto/*.pb.go`。

```bash
git -C <agentenv> ls-files \
  | grep -v -E '^(src/api/generated/|thirdparty/firecracker-client/|thirdparty/envd/http-client/|src/custom_extension_api/generated/)' \
  | grep -v -E '^services/api/proto/.*\.pb\.go$' \
  | while read f; do [ -f "$f" ] && [ ! -L "$f" ] && printf '%s\t%s\n' "$(wc -l < "$f")" "$f"; done
```

按这个口径，手写部分共 631 个文件、227365 行；其中 Rust 169975 行、Go 13364 行（Go 测试 6903 行），另有 `Cargo.lock` 9459 行。
Rust 的单元测试多数以行内 `#[cfg(test)] mod tests` 写在被测文件末尾，本篇不把它们拆出；表里标「测试」的只是**独立的测试文件**。
各目录的合计与第 01 篇 §6 一致（例如 `scripts` 为 7024 行）。

「篇目」一栏链到详细讲解的位置；一个文件被多篇用到时，先列主讲篇。只链文件名的篇目表示该篇整体都在讲它。

---

## 2. 根 crate `agentenv`：`src/`

`src/` 合计 96328 行（不含生成代码），是节点进程 `server` 的全部业务逻辑。

### 2.1 入口、配置与根级文件

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `src/bin/server.rs` | 270 | `server` 进程入口：普通启动、`--setup-only`、`--setup-host` 三种模式，启动与关闭序列 | [第 10 篇 §2](10-node-process-and-object-model.md#2-启动序列)、[§3](10-node-process-and-object-model.md#3-关闭序列)、[第 59 篇 §2](59-host-setup-and-privileges.md#2-三种模式的分工) |
| `src/bin/aenv-snapshot-image.rs` | 110 | 离线把已提交快照的 rootfs 发布成 OCI 镜像的独立工具 | [第 50 篇 §3](50-rootfs-as-oci-image.md#3-离线导出aenv-snapshot-image) |
| `src/lib.rs`、`src/proto.rs` | 25 | 模块声明；`tonic::include_proto!` 引入构建期生成的 gRPC 代码 | [第 08 篇 §3](08-system-architecture.md#3-server-进程内部的子系统)、[第 54 篇 §5.2](54-control-plane-overview.md#52-rust构建期生成只要客户端) |
| `src/cfg.rs` | 2199 | 配置结构体、加载、路径归一化与校验，`ConfigManager` 全局单例 | [第 11 篇](11-configuration.md) |
| `src/cfg/network.rs`、`src/cfg/image.rs` | 443 | `[network]` 与 `[image]` 两节的子配置 | [第 11 篇 §4](11-configuration.md#4-defaulttoml-各节)、[第 29 篇](29-network-slots.md)、[第 45 篇](45-oci-to-overlaybd.md) |
| `src/types/` | 238 | 共享 ID 类型、资源规格、镜像配置的类型定义 | [第 10 篇 §4](10-node-process-and-object-model.md#4-对象模型) |
| `src/volume.rs` | 1279 | `VolumeManager`：卷对象、预留与 owner、本地物化与发布 | [第 31 篇 §6](31-extra-drives-and-volumes.md#6-volumemanager权威在仓库本地是缓存)、[第 16 篇 §7](16-snapshot-and-volume-api.md#7-挂载预留物化与-owner-转移) |
| `src/api_key.rs` | 252 | 部署级 API key 的来源、格式与常数时间比较 | [第 13 篇 §2](13-authentication.md#2-部署级-api-key) |
| `src/managed_secret.rs` | 273 | 托管密钥文件的权限检查与原子创建 | [第 13 篇 §2.2](13-authentication.md#22-托管密钥文件权限与原子创建) |
| `src/privileges.rs` | 333 | 启动前的能力检查与子进程能力委派 | [第 59 篇 §5](59-host-setup-and-privileges.md#5-权限模型)、[第 10 篇 §2.2](10-node-process-and-object-model.md#22-能力检查为什么在最前面) |
| `src/local_store.rs` | 238 | 基于 RocksDB 的本地 KV 存储与写入持久性级别 | [第 22 篇 §3.2](22-persistence-across-restarts.md#32-rocksdb-与持久性) |
| `src/identity.rs` | 117 | 节点身份（`node_id`、集群 id 等）的解析 | [第 12 篇 §6](12-spec-driven-server.md#6-最小的实现health-与-nodes)、[第 57 篇 §2](57-heartbeat-and-cpu-intersection.md#2-节点快照) |
| `src/virtualization.rs` | 52 | `VirtualizationMode`（KVM / PVM） | [第 61 篇 §2.1](61-pvm.md#21-virtualizationmode) |
| `src/digest.rs`、`src/logging.rs` | 307 | 本地文件的 sha256 与大小；日志初始化 | — |
| `src/custom_extension_api/openapi.yml` | 218 | 自定义扩展 hook 的契约（生成客户端的来源） | [第 33 篇 §2](33-custom-extension-hooks.md#2-契约四个-hook) |

### 2.2 `src/api`：HTTP 层（14320）

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `src/api/openapi.yml` | 2966 | API 契约，生成 `agentenv_http_server` 的来源 | [第 12 篇 §2](12-spec-driven-server.md#2-生成管线)、[第 18 篇](18-e2b-compatibility.md) |
| `src/api/server.rs` | 188 | Router 组装、中间件顺序、Host 路由分类器挂载 | [第 12 篇 §4](12-spec-driven-server.md#4-router-组装与中间件顺序) |
| `src/api/proxy.rs` | 3198 | 节点内反向代理：三个入口、解析循环、自动恢复、HTTP / WebSocket 转发 | [第 17 篇](17-reverse-proxy.md) |
| `src/api/impls/mod.rs`、`admin.rs` | 352 | 生成 trait 的实现对象；`/health`、`/nodes` 等管理端点 | [第 12 篇 §6](12-spec-driven-server.md#6-最小的实现health-与-nodes) |
| `src/api/impls/auth.rs` | 164 | `require_auth()`：控制面与数据面的凭据判定 | [第 13 篇 §4](13-authentication.md#4-require_auth-的决策) |
| `src/api/impls/sandbox.rs` | 2404 | 沙箱端点：创建（v1 / v2 / 冷启动）、connect、pause / resume、TTL、列表、fork、snapshot | [第 14 篇](14-sandbox-api.md)、[第 51 篇 §2.1](51-fork.md#21-api-层参数与卷的预处理) |
| `src/api/impls/pagination.rs` | 461 | 列表的游标分页 | [第 14 篇 §8.3](14-sandbox-api.md#83-游标分页) |
| `src/api/impls/attached_drives.rs` | 368 | 附加盘请求的校验与转换 | [第 14 篇](14-sandbox-api.md)、[第 31 篇 §2.1](31-extra-drives-and-volumes.md#21-入口校验) |
| `src/api/impls/template.rs`、`template_helpers.rs` | 1442 | E2B 风格两步模板构建、模板状态与日志端点 | [第 15 篇 §3](15-template-build-api.md#3-e2b-风格的两步构建)、[第 52 篇](52-template-builder.md) |
| `src/api/impls/image_build.rs` | 518 | Dockerfile / BuildKit 路径的受理与会话状态 | [第 15 篇 §4](15-template-build-api.md#4-dockerfile-与-buildkit-路径) |
| `src/api/impls/image_build/` | 1746 | BuildKit 隧道（`transport.rs`）、构建 worker、缓存种子、清理；`tests.rs` 936 为测试 | [第 15 篇 §4.4](15-template-build-api.md#44-隧道get-builder)、[第 53 篇](53-buildkit-in-microvm.md) |
| `src/api/impls/snapshots.rs`、`volumes.rs` | 508 | 快照读取与卷的创建、读取、删除 | [第 16 篇](16-snapshot-and-volume-api.md) |

### 2.3 `src/orchestrator`：状态机（12381）

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `src/orchestrator/types.rs` | 106 | `SandboxState` 八个状态与相关类型 | [第 19 篇 §2](19-state-machine-and-concurrency.md#2-八个状态) |
| `src/orchestrator/service.rs` | 3041 | `Orchestrator`：launch、pause / resume、删除与捕获、fork、快照、驱逐任务、关闭 | [第 19 篇](19-state-machine-and-concurrency.md)–[第 23 篇](23-auto-eviction-and-ttl.md) |
| `src/orchestrator/launch_plan.rs` | 126 | `LaunchPlan`：冷启动与恢复两种计划 | [第 20 篇 §2](20-launch-plan-and-rollback.md#2-launchplan一条流水线两种计划) |
| `src/orchestrator/store/` | 1344 | 元数据存储 trait、`InMemoryMetadataStore`（CAS 与过期索引）、记录类型 | [第 19 篇 §4](19-state-machine-and-concurrency.md#4-cas-原语)、[第 23 篇 §3](23-auto-eviction-and-ttl.md#3-过期索引) |
| `src/orchestrator/persistence/` | 1160 | 持久化器接口与 RocksDB 实现（`file_backed.rs`）、测试替身 | [第 22 篇](22-persistence-across-restarts.md) |
| `src/orchestrator/proxy.rs` | 119 | 运行时路由表的查找结果类型 | [第 17 篇 §3.1](17-reverse-proxy.md#31-运行时路由表) |
| `src/orchestrator/metrics.rs`、`sandbox_metrics.rs` | 560 | 容量快照与 guest 指标采样 | [第 24 篇 §2](24-metrics-and-events.md#2-容量快照现算而不是累加)、[§3](24-metrics-and-events.md#3-guest-指标采样) |
| `src/orchestrator/tests.rs` | 5808 | 测试：状态机、并发、回滚、删除与驱逐 | [第 19 篇 §8](19-state-machine-and-concurrency.md#8-怎样验证这台状态机)、[第 63 篇](63-testing-and-benchmarks.md) |

### 2.4 `src/sandbox`：沙箱运行时（20535）

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `src/sandbox/backend.rs` | 453 | 后端 trait：`SandboxBackend`、`SandboxBackendFactory`、`PausedSandboxState` | [第 25 篇 §2](25-backend-and-firecracker-process.md#2-回顾后端-trait-的约定)、[第 10 篇 §4.3](10-node-process-and-object-model.md#43-两个后端-trait) |
| `src/sandbox/firecracker/sandbox.rs` | 3558 | `FirecrackerSandbox`：冷启动、恢复、暂停、fork、卷槽位、停止 | [第 25 篇 §3](25-backend-and-firecracker-process.md#3-firecrackersandbox一份资源清单)、[第 27 篇](27-start-pause-resume-sequences.md) |
| `src/sandbox/firecracker/instance.rs` | 758 | Firecracker 进程的拉起（`spawn_with_netns()`）与 API 调用 | [第 25 篇 §4](25-backend-and-firecracker-process.md#4-拉起进程spawn_with_netns) |
| `src/sandbox/firecracker/socket.rs`、`connector.rs` | 393 | 手写的 Unix socket HTTP 客户端 | [第 25 篇 §6](25-backend-and-firecracker-process.md#6-和-firecracker-说话手写的-uds-客户端) |
| `src/sandbox/firecracker/config.rs`、`factory.rs` | 1259 | 沙箱配置（含 boot args 默认值）与沙箱工厂 | [第 27 篇 §2](27-start-pause-resume-sequences.md#2-冷启动的准备阶段)、[第 26 篇](26-sandbox-block-devices.md) |
| `src/sandbox/firecracker/overlaybd_snapshot.rs` | 1290 | 内存快照成层、restack 收尾、卷的封存与捕获 | [第 42 篇 §2](42-memory-snapshot-over-ublk.md#2-暂停从脏页到层)、[第 37 篇 §3.4](37-seal-restack-compact.md#34-节点侧的收尾) |
| `src/sandbox/firecracker/process_vm_reader.rs` | 131 | 用 `process_vm_readv` 读 Firecracker 进程内存 | [第 42 篇 §2.5](42-memory-snapshot-over-ublk.md#25-processvmreader-与-compact_to) |
| `src/sandbox/firecracker/startup_pack.rs` | 1433 | startup pack 录制的编排 | [第 43 篇 §2](43-startup-pack-and-prefetch.md#2-录制一台一次性的-vm) |
| `src/sandbox/firecracker/pool.rs` | 429 | 预先拉起的 Firecracker 进程池 | [第 32 篇 §5](32-warm-pools.md#5-firecracker-进程池) |
| `src/sandbox/firecracker/mmds.rs` | 171 | MMDS 元数据的构造 | [第 28 篇 §2](28-mmds-and-envd.md#2-mmds带外的身份) |
| `src/sandbox/network/address_plan.rs` | 100 | 槽位的地址计划 | [第 29 篇 §2.2](29-network-slots.md#22-地址计划) |
| `src/sandbox/network/slot.rs`、`iptables_util.rs` | 1527 | 一个网络槽位的创建与清理、iptables 提交 | [第 29 篇 §4](29-network-slots.md#4-创建一个槽位) |
| `src/sandbox/network/manager.rs` | 1389 | `NetworkManager`：槽位分配、复用、网络槽位池 | [第 29 篇 §5](29-network-slots.md#5-networkmanager分配复用与清理)、[第 32 篇 §3](32-warm-pools.md#3-网络槽位池) |
| `src/sandbox/network/policy.rs` | 820 | `SandboxNetworkPolicy` 与内核判定链 | [第 30 篇 §2](30-egress-policy-and-proxy.md#2-策略对象与-api-映射)、[§3](30-egress-policy-and-proxy.md#3-内核中的判定链) |
| `src/sandbox/network/egress_proxy.rs`、`resolver.rs` | 1377 | 出站透明代理与域名解析 | [第 30 篇 §4](30-egress-policy-and-proxy.md#4-透明代理) |
| `src/sandbox/ublk/device.rs` | 941 | `UblkDeviceManager`：节点侧 ublk 设备客户端与共享设备去重 | [第 26 篇 §3](26-sandbox-block-devices.md#3-ublkdevicemanager节点侧的设备客户端)、[§4](26-sandbox-block-devices.md#4-共享只读设备与两级引用计数) |
| `src/sandbox/ublk/overlaybd.rs` | 372 | 节点侧 overlaybd 镜像配置的生成与可写层模式 | [第 26 篇 §5](26-sandbox-block-devices.md#5-用户-rootfs每台沙箱独占的可写设备) |
| `src/sandbox/extra_drive.rs` | 686 | 附加盘与卷槽位的设备命名与接线 | [第 31 篇 §3](31-extra-drives-and-volumes.md#3-设备命名与槽位) |
| `src/sandbox/manifest.rs` | 340 | 暂停产物的 manifest（不含路径的形状描述） | [第 46 篇 §3](46-snapshot-object-model.md#3-manifest形状进仓库路径留在节点)、[第 27 篇 §5.3](27-start-pause-resume-sequences.md#53-产物两份描述) |
| `src/sandbox/envd.rs`、`envd/user.rs` | 681 | envd 就绪等待、`/init`、默认用户解析 | [第 28 篇 §4](28-mmds-and-envd.md#4-就绪与-init) |
| `src/sandbox/process.rs` | 372 | `Executor`：宿主在 guest 内执行命令 | [第 28 篇 §6](28-mmds-and-envd.md#6-executor宿主在-guest-里的手) |
| `src/sandbox/access.rs` | 422 | 沙箱级 envd token 的无状态派生 | [第 13 篇 §3](13-authentication.md#3-沙箱级-token无状态派生) |
| `src/sandbox/custom_extension/` | 824 | 自定义扩展 hook 客户端与 hook guard | [第 33 篇](33-custom-extension-hooks.md) |
| `src/sandbox/metrics.rs` | 80 | guest 资源样本类型 | [第 24 篇 §3.1](24-metrics-and-events.md#31-样本从哪里来) |
| `src/sandbox/mock.rs`、`mod.rs` | 621 | 进程内 mock 后端（测试用）；模块声明 | [第 63 篇 §4.1](63-testing-and-benchmarks.md#41-trait-替身) |

### 2.5 `src/snapshot`：快照与仓库（18762）

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `src/snapshot/types/` | 1487 | 快照记录、`CommittedSnapshot`、层引用、制品清单常量、兼容版本 | [第 46 篇 §2](46-snapshot-object-model.md#2-记录已提交载荷与可运行快照) |
| `src/snapshot/manager.rs` | 526 | `SnapshotManager`：仓库与运行时缓存之上的门面 | [第 46 篇 §6](46-snapshot-object-model.md#6-snapshotmanager一层薄门面) |
| `src/snapshot/repository/interfaces.rs` 等 | 515 | 仓库 trait、错误类型、构建缓存头指针接口（`build_cache.rs`） | [第 46 篇](46-snapshot-object-model.md)、[第 53 篇 §5.4](53-buildkit-in-microvm.md#54-头指针的条件写) |
| `src/snapshot/repository/backends/mod.rs` | 192 | 按配置选择后端 | [第 47 篇](47-posix-repository.md) |
| `…/backends/posixfs/` | 4621 | POSIX 仓库：目录布局、导入与提交、catalog、按名加锁、`PosixFsRuntimeResolver` | [第 47 篇](47-posix-repository.md)、[第 49 篇 §3](49-resolve-and-artifact-cache.md#3-posix-后端不复制直接指向仓库) |
| `…/backends/oss/` | 3977 | 对象存储仓库：对象布局、七步 publish 与回滚、分片上传、catalog、resolver | [第 48 篇](48-object-storage-repository.md)、[第 49 篇 §4](49-resolve-and-artifact-cache.md#4-对象存储后端只下载小的层留在远端) |
| `…/backends/common/recontainerize.rs` | 417 | 发布时把本地 raw 层重封装为 ZFile | [第 35 篇 §7.1](35-zfile-compression.md#71-本地-raw发布时压缩)、[第 48 篇 §4.2](48-object-storage-repository.md#42-发布压缩digest-描述上传的字节) |
| `…/backends/common/acr/` | 3433 | registry 客户端、overlaybd-native manifest 构造、发布时推回源 registry | [第 50 篇 §4](50-rootfs-as-oci-image.md#4-发布时推回源-registry) |
| `src/snapshot/runtime_support.rs` | 431 | 物化可运行快照的 `image.json` | [第 49 篇 §5](49-resolve-and-artifact-cache.md#5-物化-imagejson每一层落在哪里) |
| `src/snapshot/artifact_cache.rs` | 654 | `LocalArtifactCache`：对象存储后端的本地制品缓存 | [第 49 篇 §6](49-resolve-and-artifact-cache.md#6-localartifactcache) |
| `src/snapshot/startup_pack.rs` | 471 | startup pack 制品常量与记录侧描述 | [第 43 篇](43-startup-pack-and-prefetch.md)、[第 49 篇 §7](49-resolve-and-artifact-cache.md#7-startup-manifest-制品) |
| `src/snapshot/image_export/` | 1313 | `aenv-snapshot-image` 的目标解析、发布流程与 `regctl` 封装 | [第 50 篇 §3](50-rootfs-as-oci-image.md#3-离线导出aenv-snapshot-image) |
| `src/snapshot/p2p.rs` | 431 | 把快照引用的本地层收集为可发布的 P2P 制品 | [第 58 篇 §4](58-p2p-artifact-transport.md#4-三个消费者与-key-空间) |
| `src/snapshot/mock.rs`、`mod.rs` | 176 | 测试替身；模块声明 | [第 63 篇](63-testing-and-benchmarks.md) |

### 2.6 `src/image`：OCI 镜像（10279）

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `src/image/resolver.rs`、`reference.rs` | 1554 | 镜像引用解析、候选 registry、取 manifest 与分类 | [第 45 篇 §2](45-oci-to-overlaybd.md#2-解析一个镜像引用) |
| `src/image/oci_image.rs` | 2475 | OCI 镜像到 overlaybd lower 栈：native 直读与逐层转换；BuildKit content 镜像转换 | [第 45 篇 §3](45-oci-to-overlaybd.md#3-overlaybd-native不下载任何-blob)、[§4](45-oci-to-overlaybd.md#4-标准-oci逐层转换) |
| `src/image/commit_index.rs`、`local_layer.rs`、`metadata.rs` | 652 | 转换结果的提交索引、本地层文件名约定、源镜像配置透传 | [第 45 篇 §4.2](45-oci-to-overlaybd.md#42-三级查找) |
| `src/image/cache/service.rs`、`graph.rs` | 4023 | 节点 image-cache：元数据图、持有者、按源配置的 LRU | [第 45 篇 §5](45-oci-to-overlaybd.md#5-节点本地的-image-cache) |
| `src/image/cache/` 其余 | 704 | 源配置、对外存储端口（镜像引用保护）、GC、mock | [第 45 篇 §5.5](45-oci-to-overlaybd.md#55-宁可不删的-gc)、[第 20 篇 §5](20-launch-plan-and-rollback.md#5-镜像引用保护的交接) |
| `src/image/buildkit.rs`、`buildkit/history.rs` | 705 | 只读访问 BuildKit content store；在 history 里认出本次构建 | [第 53 篇 §4.2](53-buildkit-in-microvm.md#42-在-history-里认出自己)、[§4.3](53-buildkit-in-microvm.md#43-经-content-api-取镜像) |
| `src/image/*.proto`、`mod.rs` | 166 | BuildKit content / history 的 gRPC 定义（构建期生成） | [第 53 篇](53-buildkit-in-microvm.md) |

### 2.7 其余子系统

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `src/template/builder.rs`、`runner.rs` | 1886 | 模板构建器：两个起点、构建 VM、版本探测与捕获、发布 | [第 52 篇](52-template-builder.md) |
| `src/template/step_executor.rs`、`build_spec.rs`、`logs.rs`、`errors.rs` | 1481 | 逐步执行、构建规格、构建日志 | [第 52 篇 §4](52-template-builder.md#4-构建-vm-里的流程)、[§6](52-template-builder.md#6-构建日志) |
| `src/setup/deps.rs` | 1557 | 依赖下载与版本化路径（manifest 编进二进制） | [第 59 篇 §3](59-host-setup-and-privileges.md#3-依赖供给) |
| `src/setup/` 其余 | 1850 | 发行版包、overlaybd 全局配置、KVM / ublk 检查、网络容量 | [第 59 篇 §4](59-host-setup-and-privileges.md#4-宿主准备--setup-host-与-docker-setupsh)、[第 61 篇 §3](61-pvm.md#3-启动时的校验) |
| `src/p2p/iroh/` | 2071 | iroh 后端：endpoint、publish / lookup / fetch、本地 catalog | [第 58 篇 §3](58-p2p-artifact-transport.md#3-iroh-后端) |
| `src/p2p/` 其余 | 1249 | 传输抽象（key、descriptor、provider）、经 scheduler 的发现、mock | [第 58 篇 §2](58-p2p-artifact-transport.md#2-抽象keydescriptorprovider) |
| `src/overlaybd/p2p/` | 1889 | 给 Rust 版 overlaybd 用的 P2P HTTP 门面（`facade.rs` 1450） | [第 58 篇 §5](58-p2p-artifact-transport.md#5-overlaybd-的-http-门面) |
| `src/observability/reporter.rs`、`service.rs` | 699 | 心跳 reporter 与节点快照 | [第 57 篇 §3.1](57-heartbeat-and-cpu-intersection.md#31-节点侧observabilityreporter) |
| `src/observability/` 其余 | 1002 | 主机指标、CPU 型号采集、Prometheus 记录器 | [第 57 篇 §2.2](57-heartbeat-and-cpu-intersection.md#22-主机指标)、[第 24 篇 §5](24-metrics-and-events.md#5-prometheus-指标) |

---

## 3. 存储栈：`storage/`

### 3.1 `storage/overlaybd`：Rust 版 overlaybd（43173）

`src/` 41260 行，另有 `benches/` 778、`examples/` 718、`tests/` 350、`Cargo.toml` 67。

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `src/lsmt/format.rs` | 294 | `HeaderTrailer` 与 `DiskSegmentMapping` 的字节格式 | [第 34 篇 §2](34-lsmt-format-and-index.md#2-头尾与段映射两个固定格式) |
| `src/lsmt/index.rs` | 1276 | 三种索引结构与合并 | [第 34 篇 §4](34-lsmt-format-and-index.md#4-索引三种结构与-tag-约定) |
| `src/lsmt/file/readonly.rs`、`stack.rs`、`types.rs` | 1032 | 只读层、层栈、层文件形态与布局类型 | [第 34 篇 §3](34-lsmt-format-and-index.md#3-四种层文件形态)、[第 36 篇 §2](36-read-write-paths-and-rw-layouts.md#2-层栈装配) |
| `src/lsmt/file/readwrite.rs` | 1370 | 可写层：三种布局的写、seal、discard | [第 36 篇 §4](36-read-write-paths-and-rw-layouts.md#4-写路径三种布局)、[第 37 篇 §2](37-seal-restack-compact.md#2-seal原地封口) |
| `src/lsmt/file/helper.rs` | 1675 | compact、预合并索引缓存 `PMIDX001`、RW 头结构校验 | [第 37 篇 §4](37-seal-restack-compact.md#4-compact按映射重写成单层)、[第 34 篇 §5](34-lsmt-format-and-index.md#5-预合并索引缓存pmidx001) |
| `src/lsmt/file/tests.rs` | 4051 | 测试 | [第 63 篇](63-testing-and-benchmarks.md) |
| `src/compression/zfile.rs` | 3157 | ZFile 格式、jump table、读路径、`ZFileBuilder` 与 `ZFileCompactWriter` | [第 35 篇](35-zfile-compression.md) |
| `src/image/image_file.rs` | 3095 | `ImageFile`：层栈装配、读写入口、`create_snapshot_and_restack()` | [第 36 篇 §2](36-read-write-paths-and-rw-layouts.md#2-层栈装配)、[第 37 篇 §3](37-seal-restack-compact.md#3-restack封存并换上新-upper) |
| `src/image/image_service.rs` | 1387 | 镜像服务：从 `image.json` 打开镜像、装配后端链 | [第 38 篇 §3](38-virtualfile-chain-and-remote-io.md#3-装饰器链) |
| `src/image/helper.rs`、`snapshot.rs` | 374 | 配置路径改写、运行时 upper 准备、把 upper 导出为快照层 | [第 49 篇 §5](49-resolve-and-artifact-cache.md#5-物化-imagejson每一层落在哪里) |
| `src/io/` | 733 | `VirtualFile` trait、策略类型、`RuntimeDispatchFile` | [第 38 篇 §2](38-virtualfile-chain-and-remote-io.md#2-virtualfile-trait)、[§4](38-virtualfile-chain-and-remote-io.md#4-多-runtime-陷阱) |
| `src/backend/local.rs`、`tar.rs`、`switch.rs` | 2615 | 本地文件、tar 包裹适配、`SwitchFile`（ZFile 识别） | [第 38 篇 §3.2](38-virtualfile-chain-and-remote-io.md#32-localfile)、[§3.3](38-virtualfile-chain-and-remote-io.md#33-tar-适配与-switchfile) |
| `src/backend/registryfs_v2.rs` | 2798 | 从 registry 按范围读 blob | [第 38 篇 §3.4](38-virtualfile-chain-and-remote-io.md#34-registryfs_v2) |
| `src/backend/oss.rs` | 721 | 对象存储读后端 | [第 38 篇 §3.5](38-virtualfile-chain-and-remote-io.md#35-oss) |
| `src/backend/cache/full_file_cache/` | 3616 | 节点块缓存：条目、池（容量与驱逐）、数据文件与位图 | [第 39 篇 §2](39-block-cache-and-background-download.md#2-缓存在读链上的位置与条目组织)、[§4](39-block-cache-and-background-download.md#4-容量驱逐与持久化) |
| `src/backend/cache/cached_fs.rs`、`meta.rs`、`mod.rs` | 1007 | 缓存读链入口、`meta.bin` 持久化 | [第 39 篇 §3](39-block-cache-and-background-download.md#3-一次缺块读)、[§4.3](39-block-cache-and-background-download.md#43-metabin-与崩溃语义) |
| `src/backend/cache/bk_download.rs` | 1089 | 后台下载调度器 | [第 39 篇 §5](39-block-cache-and-background-download.md#5-后台下载调度器) |
| `src/backend/cache/startup_pack_task.rs` | 709 | 按 startup manifest 回填块缓存的预取任务 | [第 43 篇 §4.2](43-startup-pack-and-prefetch.md#42-对象存储来源交给-daemon-回填块缓存) |
| `src/backend/cache/tests.rs` | 2759 | 测试 | [第 63 篇](63-testing-and-benchmarks.md) |
| `src/download_gate.rs` | 337 | 前台与后台下载的节点级准入 | [第 39 篇 §6](39-block-cache-and-background-download.md#6-前台与后台的准入) |
| `src/startup_pack.rs`、`startup_manifest.rs`、`pack_planner.rs`、`prefetch.rs` | 2141 | 首触页 trace 编解码、startup manifest、物理块规划、上游兼容 trace prefetch | [第 43 篇 §3](43-startup-pack-and-prefetch.md#3-两种格式trace-与-manifest)、[§5](43-startup-pack-and-prefetch.md#5-上游兼容的-trace-prefetch) |
| `src/config.rs` | 1270 | `image.json` 等配置结构（与上游 overlaybd 配置对应） | [第 36 篇 §2.1](36-read-write-paths-and-rw-layouts.md#21-从-imagejson-到-imagefile)、[第 05 篇](05-overlaybd-and-lazy-loading.md) |
| `src/tools/oci.rs`、`packaging.rs` | 1106 | 调用 overlaybd 工具做 OCI 层转换；ext4 / raw 打包成层 | [第 45 篇 §4.4](45-oci-to-overlaybd.md#44-一层的转换) |
| `src/sys/` | 1470 | 平台文件系统原语：空间预留与释放、xattr、页缓存丢弃 | [第 39 篇 §3.3](39-block-cache-and-background-download.md#33-预留磁盘把-sigbus-变成-enospc) |
| `src/dense_export.rs`、`layer/`、`ext4_stat.rs`、`metrics.rs`、`lib.rs` | 1103 | 稠密层导出的 digest 跟踪、层文件名约定、ext4 用量探测、指标 | [第 50 篇](50-rootfs-as-oci-image.md)、[第 49 篇](49-resolve-and-artifact-cache.md) |

### 3.2 ublk 与其它存储 crate

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `storage/ublk-daemon/src/main.rs` | 413 | daemon 入口、配置读取、能力 | [第 41 篇 §2](41-ublk-daemon.md#2-进程生命周期) |
| `storage/ublk-daemon/src/protocol.rs` | 819 | RPC 帧与请求 / 响应类型 | [第 41 篇 §3](41-ublk-daemon.md#3-rpc-协议) |
| `storage/ublk-daemon/src/server.rs` | 2148 | RPC 服务：设备表、预热池、restack、内存层、startup pack 录制 | [第 41 篇 §4](41-ublk-daemon.md#4-设备表与预热池)、[第 37 篇 §3](37-seal-restack-compact.md#3-restack封存并换上新-upper) |
| `storage/ublk-daemon/src/runtime.rs` | 1106 | 运行时物化：从 lower 栈准备可写设备、扩容 | [第 41 篇 §5](41-ublk-daemon.md#5-运行时物化) |
| `storage/ublk-daemon/src/client.rs` | 924 | `UblkDaemonClient`（`server` 侧链接使用）与拉起 | [第 26 篇 §3](26-sandbox-block-devices.md#3-ublkdevicemanager节点侧的设备客户端)、[第 41 篇 §2.1](41-ublk-daemon.md#21-拉起与就绪) |
| `storage/ublk-daemon/tests/` 等 | 1333 | 集成测试 1253；`metrics_server.rs`、`lib.rs`、`Cargo.toml` | [第 63 篇](63-testing-and-benchmarks.md) |
| `storage/ublk/src/ctrl.rs`、`dev.rs` | 903 | ublk 控制面：ctrl ring、控制命令、设备生命周期 | [第 40 篇 §2](40-ublk-library.md#2-控制面)、[§3](40-ublk-library.md#3-设备生命周期) |
| `storage/ublk/src/queue.rs`、`io_buffer.rs` | 837 | 数据面 queue 线程、两种缓冲 | [第 40 篇 §4](40-ublk-library.md#4-数据面一个-queue-线程)、[§6](40-ublk-library.md#6-两种缓冲) |
| `storage/ublk/src/impls/overlaybd_target.rs` | 593 | `OverlaybdTarget`：把块请求接到 `ImageFile` | [第 40 篇 §7](40-ublk-library.md#7-overlaybdtarget) |
| `storage/ublk/src/impls/startup_pack_recorder.rs` | 471 | 首触页录制器 | [第 43 篇 §2.3](43-startup-pack-and-prefetch.md#23-startuppackrecorder) |
| `storage/ublk/` 其余 | 1327 | `lib.rs`、特性位常量、调试二进制 `main.rs`；测试 892 | [第 04 篇 §5](04-io-uring-and-ublk.md#5-特性位与内核版本)、[第 40 篇](40-ublk-library.md) |
| `storage/util/src/io_ring/` | 1063 | io_uring 封装、`AsyncIoRing` 与 worker | [第 40 篇 §5](40-ublk-library.md#5-asyncioring-与取消安全) |
| `storage/util/src/` 其余 | 782 | 对齐缓冲区、mmap 区域、稀疏下标分配、compact 写出接口 | [第 40 篇 §5.3](40-ublk-library.md#53-稀疏表的下标分配) |
| `storage/uffd-core/` | 808 | uffd 内存后端的保留实现（不在 workspace） | [第 44 篇 §2](44-uffd-alternative.md#2-uffd-core-的结构) |

---

## 4. 其它 Rust crate 与测试

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `crates/aenv/src/client/` | 1620 | CLI 的控制面 HTTP 客户端（沙箱、模板、快照、卷、文件、BuildKit） | [第 62 篇 §2](62-aenv-cli.md#2-分层) |
| `crates/aenv/src/grpc/` | 537 | 经反向代理访问 envd 的 Connect 客户端 | [第 62 篇 §3](62-aenv-cli.md#3-数据面envd-的-connect-客户端) |
| `crates/aenv/src/commands/connect.rs` | 957 | `aenv connect` 交互终端 | [第 62 篇 §4](62-aenv-cli.md#4-aenv-connect交互终端的鲁棒性) |
| `crates/aenv/src/commands/build.rs` | 476 | `aenv build`：本地 buildctl 对接远端 buildkitd | [第 62 篇 §5](62-aenv-cli.md#5-aenv-build本地-buildctl-与远端-buildkitd)、[第 53 篇](53-buildkit-in-microvm.md) |
| `crates/aenv/src/commands/codex/` | 2952 | `aenv codex`：在沙箱里隔离执行的 Codex 会话 | [第 62 篇 §6](62-aenv-cli.md#6-aenv-codex一个完整的用例) |
| `crates/aenv/src/commands/` 其余 | 3184 | 补全、上传下载、start / pause / resume 等子命令 | [第 62 篇 §7](62-aenv-cli.md#7-补全与其它细节) |
| `crates/aenv/` 其余 | 412 | 入口、凭据保存、进度与输出 | [第 62 篇](62-aenv-cli.md) |
| `crates/warm-pool` | 617 | 水位维持的通用预热池 `WarmPool<T>` | [第 32 篇 §2](32-warm-pools.md#2-通用实现warmpool) |
| `crates/linux-cap` | 231 | Linux 能力的委派 | [第 59 篇 §5.4](59-host-setup-and-privileges.md#54-linux-cap-crate) |
| `crates/object-store-operator` | 680 | 对象存储凭据与客户端 | [第 48 篇 §4.4](48-object-storage-repository.md#44-分片上传与凭证) |
| `crates/observability` | 101 | 节点与控制面共用的指标格式与直方图桶 | [第 57 篇 §6](57-heartbeat-and-cpu-intersection.md#6-共用的直方图桶) |
| `crates/shell-util`、`crates/test-support` | 153 | shell 转义小工具；测试用 MinIO 等支撑 | [第 63 篇](63-testing-and-benchmarks.md) |
| `crates/benchmarks` | 2939 | 四组 criterion 基准（OCI 转换、元数据存储、快照、ublk + overlaybd） | [第 63 篇 §6](63-testing-and-benchmarks.md#6-基准) |
| `crates/e2e-tests` | 813 | 对象存储端到端测试 | [第 63 篇 §2.3](63-testing-and-benchmarks.md#23-对象存储与存储引擎) |
| `tests/` | 3118 | 根 crate 集成测试（Firecracker、快照、附加盘、ublk、进程） | [第 63 篇 §2.2](63-testing-and-benchmarks.md#22-集成测试) |
| `thirdparty/envd`（不含 `http-client/`） | 1002 | host 侧 envd 客户端：Connect-RPC 部分手写，含 proto 与测试 | [第 28 篇 §5](28-mmds-and-envd.md#5-客户端不信任同一个-ip-还是同一台-vm) |
| `adev` | 1197 | 开发者工具：codegen、coverage、mutants、工具安装 | [第 64 篇 §2.3](64-build-codegen-release.md#23-adev开发与-ci-工具) |

---

## 5. Go 控制面：`services/`（13701）

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `services/gateway/internal/server.go` | 1005 | gateway 主体：认证分界、路由判定、转发、写绑定 | [第 55 篇 §2](55-gateway.md#2-认证分界)–[§6](55-gateway.md#6-写绑定) |
| `services/gateway/internal/host_route.go` | 143 | 从 Host 头解析沙箱路由 | [第 55 篇 §3.2](55-gateway.md#32-六种路由来源) |
| `services/gateway/internal/schedule_hint.go` | 154 | 创建请求的调度提示与选节点 | [第 55 篇 §4](55-gateway.md#4-选节点) |
| `services/gateway/internal/cluster_list.go`、`node_list.go`、`sandbox_metrics.go` | 817 | gateway 本地聚合：集群沙箱列表、节点列表、批量指标 | [第 55 篇 §7](55-gateway.md#7-gateway-本地聚合) |
| `services/gateway/internal/metrics.go` | 238 | gateway 的 Prometheus 指标 | [第 55 篇](55-gateway.md) |
| `services/gateway` 其余 | 3751 | `cmd/main.go` 309；测试 3422 | [第 55 篇](55-gateway.md) |
| `services/scheduler/internal/service.go` | 377 | 13 个 gRPC 方法的实现 | [第 56 篇](56-scheduler.md)、[第 54 篇 §3](54-control-plane-overview.md#3-13-个-rpc) |
| `services/scheduler/internal/filter.go`、`strategy.go` | 148 | 资源过滤与放置策略 | [第 56 篇 §2](56-scheduler.md#2-放置) |
| `services/scheduler/internal/node_registry.go` | 448 | 节点注册表与心跳状态 | [第 57 篇 §3.2](57-heartbeat-and-cpu-intersection.md#32-scheduler-侧heartbeat)、[第 56 篇 §2.4](56-scheduler.md#24-不排除-unhealthy-节点) |
| `services/scheduler/internal/store.go`、`redis_store.go` | 628 | 绑定存储接口、内存实现、Redis 实现；P2P 索引 | [第 56 篇 §3](56-scheduler.md#3-绑定)、[第 58 篇 §3.5](58-p2p-artifact-transport.md#35-scheduler-侧的索引) |
| `services/scheduler/internal/kubernetes_discovery.go` | 348 | 基于 EndpointSlice 的节点发现 | [第 56 篇 §4.2](56-scheduler.md#42-kubernetes) |
| `services/scheduler/internal/cpu_template.go` | 301 | CPU 模板求交 | [第 57 篇 §5.3](57-heartbeat-and-cpu-intersection.md#53-scheduler-求交) |
| `services/scheduler` 其余 | 3169 | `cmd/main.go` 263（HA 角色）、`metrics.go`、`types.go`；测试 2713 | [第 56 篇 §6](56-scheduler.md#6-haprimary-与-query-only) |
| `services/shared/` | 1250 | gateway 与 scheduler 共用的配置、日志、指标桶 | [第 54 篇](54-control-plane-overview.md)、[第 57 篇 §6](57-heartbeat-and-cpu-intersection.md#6-共用的直方图桶) |
| `services/api/proto/scheduler.proto` | 271 | 控制面 proto 契约 | [第 54 篇 §3](54-control-plane-overview.md#3-13-个-rpc) |
| `services/` 根级文件 | 653 | `Makefile`、`go.mod` / `go.sum`、`README.md`、配置样例 | [第 54 篇 §5.1](54-control-plane-overview.md#51-go生成后入库) |

---

## 6. 部署、脚本与周边

| 路径 | 行数 | 职责 | 篇目 |
|---|---|---|---|
| `config/default.toml` | 403 | 节点配置的缺省文件 | [第 11 篇 §4](11-configuration.md#4-defaulttoml-各节) |
| `config/deps_manifest.toml`、`buildkit-version` | 63 | 外部依赖版本表；BuildKit 版本 | [第 01 篇 §3](01-repo-map-and-versions.md#3-外部依赖configdeps_manifesttoml)、[第 59 篇 §3.1](59-host-setup-and-privileges.md#31-manifest编进二进制的版本表) |
| `deploy/docker/` | 244 | 三个 Dockerfile 与容器缺省配置 | [第 60 篇 §3](60-deployment.md#3-docker-镜像) |
| `deploy/docker-compose.yml` | 111 | 单机两节点的 Compose 模拟 | [第 60 篇 §4](60-deployment.md#4-compose一台机器上的两节点) |
| `deploy/k8s/` | 723 | kustomize 清单（节点 DaemonSet、gateway、scheduler、RBAC）与 `run.sh` | [第 60 篇 §5](60-deployment.md#5-kubernetes) |
| `scripts/install.sh`、`install-cli.sh` | 614 | 裸机安装与 CLI 安装 | [第 60 篇 §2](60-deployment.md#2-裸机单节点installsh) |
| `scripts/docker-setup.sh` | 80 | 容器宿主的准备 | [第 59 篇 §4.2](59-host-setup-and-privileges.md#42-容器宿主docker-setupsh) |
| `scripts/run-with-capabilities.sh` | 101 | 以委派能力运行测试 | [第 63 篇 §3](63-testing-and-benchmarks.md#3-能力委托run-with-capabilitiessh) |
| `scripts/tests/` | 5317 | HTTP 端到端套件（17 个 suite）、SDK 兼容脚本、安装验证 | [第 63 篇 §2.4](63-testing-and-benchmarks.md#24-http-端到端套件)、[第 18 篇 §6](18-e2b-compatibility.md#6-验证方式) |
| `scripts/` 其余 | 912 | BuildKit 测试夹具与脚本、e2b 基准脚本、发布打包、公共函数 | [第 53 篇](53-buildkit-in-microvm.md)、[第 64 篇 §4](64-build-codegen-release.md#4-发布流水线) |
| `tools-image/` | 671 | tools 盘构建源：从 e2b infra 编译 envd，加 busybox 与 `/init` | [第 64 篇 §5](64-build-codegen-release.md#5-tools-盘镜像)、[第 26 篇 §7](26-sandbox-block-devices.md#7-tools-盘的来源与版本) |
| `containerd-plain-snapshotter/` | 1042 | 独立的 containerd snapshotter 插件，不被其它部分引用 | [第 01 篇 §4.2](01-repo-map-and-versions.md#42-go两个独立-module) |
| `.github/` | 2296 | CI、覆盖率、发布、文档与 tools 盘镜像 workflow | [第 63 篇 §5](63-testing-and-benchmarks.md#5-ci-矩阵)、[第 64 篇 §4](64-build-codegen-release.md#4-发布流水线) |
| `docs/` | 7509 | mdBook 文档站（`docs/src` 7239 为正文源码；参考，不是依据） | [第 64 篇 §6](64-build-codegen-release.md#6-文档站) |
| 根级文件 | 10788 | `Cargo.toml` 152、`Cargo.lock` 9459、`Makefile` 302、`build.rs` 73、`CLAUDE.md`、`README.md` 等 | [第 64 篇 §2](64-build-codegen-release.md#2-构建入口)、[第 01 篇 §4.1](01-repo-map-and-versions.md#41-19-个成员) |

---

## 7. 生成代码

以下五份产物入库但不计入前文行数；讲行为时引用它们的来源。行数为 `git ls-files` 下全部文件之和，括号内为其中 `.rs` / `.go` 的行数。

| 生成产物 | 行数 | 来源 | 主要内容 | 篇目 |
|---|---|---|---|---|
| `src/api/generated/`（crate `agentenv_http_server`） | 20709（Rust 20539） | `src/api/openapi.yml` | `models.rs` 11188、`server/mod.rs` 7012、`apis/*.rs` 按 tag 分的 trait | [第 12 篇 §3](12-spec-driven-server.md#3-生成了什么) |
| `thirdparty/firecracker-client/` | 4953（Rust 2155） | 同目录 `firecracker.yaml`（1939 行，描述 AENV 补丁版 Firecracker 的 API） | 只用其 model 类型；另含 `docs/*.md` | [第 25 篇 §6.1](25-backend-and-firecracker-process.md#61-只生成了数据模型) |
| `thirdparty/envd/http-client/` | 1803（Rust 903） | 同目录 `envd.yaml`（405 行） | envd HTTP 部分的客户端 | [第 28 篇 §5.1](28-mmds-and-envd.md#51-引导-http-客户端) |
| `src/custom_extension_api/generated/` | 987（Rust 621） | `src/custom_extension_api/openapi.yml` | 扩展 hook 客户端 | [第 33 篇 §2](33-custom-extension-hooks.md#2-契约四个-hook) |
| `services/api/proto/*.pb.go` | 3227（Go） | `services/api/proto/scheduler.proto` | `scheduler.pb.go` 2650、`scheduler_grpc.pb.go` 577 | [第 54 篇 §5.1](54-control-plane-overview.md#51-go生成后入库) |

两个来源文件 `firecracker.yaml` 与 `envd.yaml` 位于生成目录之内，所以也随整目录排除在前文合计之外。
Rust 侧的 gRPC 代码（scheduler 客户端、`src/image/*.proto`、`thirdparty/envd/proto/*.proto`）由 `build.rs` 在构建期生成到 `OUT_DIR`，不入库，也不在本表；生成器版本与后处理见[第 64 篇 §3](64-build-codegen-release.md#3-生成代码)。

---

## 8. 按部反查

| 本书部分 | 主要目录 |
|---|---|
| 二、总体架构（08–11） | `src/bin`、`src/lib.rs`、`src/cfg*`、`src/setup/mod.rs` |
| 三、API 层（12–18） | `src/api`、`src/api_key.rs`、`src/managed_secret.rs`、`src/sandbox/access.rs` |
| 四、orchestrator（19–24） | `src/orchestrator`、`src/local_store.rs`、`src/observability` |
| 五、沙箱运行时（25–33） | `src/sandbox`、`src/volume.rs`、`crates/warm-pool` |
| 六、存储（34–44） | `storage/overlaybd`、`storage/ublk`、`storage/ublk-daemon`、`storage/util`、`storage/uffd-core`、`src/sandbox/firecracker/overlaybd_snapshot.rs` |
| 七、镜像、快照与模板（45–53） | `src/image`、`src/snapshot`、`src/template`、`src/api/impls/image_build*` |
| 八、分布式控制面（54–58） | `services/`、`src/p2p`、`src/overlaybd/p2p`、`src/observability` |
| 九、部署与工程（59–64） | `src/setup`、`crates/linux-cap`、`deploy`、`scripts`、`crates/aenv`、`tests`、`crates/benchmarks`、`adev`、`tools-image`、`.github` |

---

## 9. 小结

- 手写代码按第 01 篇口径共 227365 行，Rust 169975 行、Go 13364 行；生成代码 31679 行单列，讲行为时引用它们的 YAML / proto 来源。
- 单个文件最大的是 `src/orchestrator/tests.rs`（5808）与 `storage/overlaybd/src/lsmt/file/tests.rs`（4051）；生产代码中最大的是 `src/sandbox/firecracker/sandbox.rs`（3558）、`src/api/proxy.rs`（3198）、`storage/overlaybd/src/compression/zfile.rs`（3157）、`storage/overlaybd/src/image/image_file.rs`（3095）与 `src/orchestrator/service.rs`（3041）。
- `storage/overlaybd` 的四大块是后端与缓存（`backend/` 15326）、LSMT（`lsmt/` 9723）、镜像装配（`image/` 4863）与 ZFile（3158）。
- `src/sandbox` 的近一半是 `firecracker/`（9449），网络（`network/` 5285）次之；内存快照成层的节点侧代码集中在 `overlaybd_snapshot.rs`。
- `src/snapshot` 的七成是两个仓库后端与共用的发布代码（`repository/backends/` 12758）。
- Go 控制面一半是测试；gateway 的业务集中在 `server.go` 一个文件，scheduler 按职责拆成过滤、策略、注册表、存储、发现、CPU 模板几个小文件。
- Rust 行内测试没有拆出，独立测试文件与 `tests/`、`benches/` 在表中单独标出。
- 各目录合计与第 01 篇 §6 一致，两篇可以交叉核对。

---

## 延伸阅读 / 下一篇

- [第 01 篇 · 仓库地图、版本与依赖](01-repo-map-and-versions.md)：顶层目录地图、workspace 成员与生成代码的再生成命令。
- [第 64 篇 · 构建、代码生成与发布](64-build-codegen-release.md)：生成管线与构建入口。
- [第 69 篇 · 术语表](69-glossary.md)：表中出现的术语的一句话定义。
- [第 71 篇 · 配置项、环境变量与端口总表](71-config-env-ports-reference.md)、[第 72 篇 · 接口总表](72-api-reference.md)、[第 73 篇 · 持久化制品与磁盘格式总表](73-artifacts-and-formats-reference.md)：其余附录。
