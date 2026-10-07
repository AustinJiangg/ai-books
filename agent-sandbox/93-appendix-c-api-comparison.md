# 附录 C　各系统 API 对照

## 附录导读

第 16 章用表 16-3 并列了七个系统的主要操作，并说明字段级对照放在本附录。这里把范围扩到 15 个系统，按"一个系统一行、一类操作一列"排成三张表：表 C-1 是生命周期与状态，表 C-2 是网络、凭据、I/O 与集成，表 C-3 把每一行对到第 16 章表 16-2 的七个"训练场景缺失概念"。

**怎么读。** 每个格子写的是本书在一手材料里读到的**接口名**（SDK 方法、REST 路径、CRD 字段或 CLI 子命令），后附一句必要的语义说明。接口名一律用行内代码格式，原样照抄，不做翻译或统一。同一能力在不同系统中名字不同（例如暂停在 E2B 叫 `pause()`，在 ACS 的 E2B 接入页叫 `beta_pause`，在 agent-sandbox 是把 `operatingMode` 设为 `Suspended`），读者应按语义而不是按名字比较。

**口径。** 第一，只记"公开文档或代码中出现过"的接口，不记厂商宣传中的能力描述；少数只有概述页文字、没有接口名的能力（如 ACS 的 Checkpoint/Restore、AGS 的"进程级快照"），照录原文并注明"接口名文档未见"。第二，"文档未见（10-05）"表示截至 2026-10-05，本书读过的该系统一手材料中没有相关接口或说明；它**不等于**该系统不具备这项能力，只说明公开材料无法证实。第三，DSec 只有论文，没有公开 SDK 文档，凡论文未写明调用形式的，一律写"文档未见"，与第 24 章 24.7 节的空白清单一致。第四，同一系统的开源仓库与托管服务可能不同（如 OpenSandbox 的服务器级运行时配置、Daytona 的分级网络默认值），本表以所读材料为准，并在格内注明适用条件。第五，"兼容 E2B"的系统，凡其文档或代码明确写出与 E2B 不同的默认值或语义，单独标出；未写明的，不推定为相同。

**局限。** 本附录是 2026 年 10 月初的一个切片。表 16-3 写作时（2026-10-04）标为"未见"的若干格，到本附录核对时已经有了接口（见 C.4 节第一条），说明这一层的接口变化以周计；引用时请以出处清单中的提交号和日期为准。托管产品（ACS、AGS、Modal、Daytona）只能读到公开文档，无法看到实现；开源项目读的是默认分支的单一提交，未覆盖发布版本之间的差异。本附录不做任何功能测试，格子里的接口能否按文档工作，需要读者自己验证（第 16 章 16.2.3 节阿里云 FC "可调用但效果受限"一例说明了这一点）。

## C.1　生命周期与状态

**表 C-1　生命周期与状态**

| 系统 | create | exec | 文件 | pause / resume | snapshot | fork | TTL | 后端选择 |
|---|---|---|---|---|---|---|---|---|
| E2B | `Sandbox.create`（模板 ID 或快照 ID）；`POST /v2/sandboxes`（`POST /sandboxes` 已标 deprecated） | `commands.run`；envd `Process.Start`（流式） | `files.read` / `files.write`；envd Filesystem 服务与 `/files` | `pause()`（SDK `keepMemory` / `keep_memory` 可设 false，只留文件系统；REST 字段为 `memory`）/ `connect()`；`POST .../pause`；`POST .../resume` 已标 deprecated；`autoResume` | `createSnapshot()`、`listSnapshots()`、`deleteSnapshot()`；`POST /sandboxes/{id}/snapshots`（原沙箱继续运行） | `sandbox.fork()`；`POST /sandboxes/{id}/fork`，`count` 1–100 | `timeout` 为存活时间（v2 默认 300 s，v1 15 s）；`POST .../timeout` 覆盖；`lifecycle.onTimeout`：`kill`（默认）或 `pause`；已暂停沙箱无 TTL | 单一形态；资源随模板（`cpuCount`、`memoryMB`），创建请求无资源字段 |
| AgentENV（`aenv` 与 HTTP） | E2B SDK `Sandbox.create`；`POST /sandboxes`、`/v2/sandboxes`；`POST /sandboxes-cold`（直接用 OCI 镜像冷启动）；`aenv start` | guest 内 envd（由 e2b-dev/infra 编译），E2B SDK `commands.run`；`aenv exec` | 经 envd，E2B SDK `files.*`；E2B SDK 的卷内容直读 API 不支持 | `POST .../pause`、`.../resume`、`connect`；`aenv pause` / `aenv resume` | `POST /sandboxes/{id}/snapshots`；`GET`/`DELETE /snapshots/{id}`；可持久化到共享 POSIX 文件系统（`posix_fs`）或 OSS（经 S3 兼容客户端） | `POST /sandboxes/{id}/fork`，`count` 1–100，限同一节点（`src/orchestrator/service.rs`） | `timeout`（v1 默认 15 s，v2 300 s）；到期动作 `autoPause` **默认 true**（暂停），false 为删除；`aenv timeout` | 仅 Firecracker microVM；`customExtensionParams` 交外部扩展处理（VPN、防火墙、挂载） |
| CubeSandbox | `Sandbox.create(template=...)`（`cubesandbox` SDK，Python/Node/Go，自称可替换 e2b SDK）；CubeAPI `POST /sandboxes` | `commands.run`、`run_code` | `files.read` / `files.write`（经 envd `/files`；issue #498 记录部分部署返回 502） | `POST .../pause`、`.../resume`；`connect` | `sb.create_snapshot()`；`POST /sandboxes/{id}/snapshots`；`sb.rollback(snap_id)` 原地回滚（`POST .../rollback`）；跨节点快照（S3 后端） | `sb.clone(n=N, concurrency=C)`，SDK 层先快照再批量创建，内部快照自动清理；上限文档未见（10-05） | `timeout` 为**空闲**秒数；`on_timeout`：`kill`（默认）或 `pause`；`NEVER_TIMEOUT`（-1） | KVM microVM（CubeHypervisor）；PVM 为部署形态（普通云主机），不是每沙箱选项 |
| 阿里云 ACS Agent Sandbox | E2B SDK `Sandbox.create`（需 `E2B_DOMAIN`、`E2B_API_KEY`；私有协议需 `kruise-agents` 的 `patch_e2b()`）；或 Sandbox CR：`SandboxSet`、`SandboxClaim`、`Sandbox`（`agents.kruise.io/v1alpha1`） | `commands.run`、`run_code` | `files.read` / `files.write`；`upload_url` / `download_url` 不支持 | `beta_pause` / `connect`；概述页称"内存状态保持"，"1s~10s"唤醒（厂商自报） | 概述页称支持对内存状态"Checkpoint 和 Restore"（厂商自报）；接口名文档未见（10-05） | 文档未见（10-05） | `set_timeout`；CR 侧 `ttlAfterCompleted`、`claimTimeout` | MicroVM（概述页；厂商自报）；`alibabacloud.com/compute-class: agent-sandbox` 标签指定实例类型；`spec.runtimes` 是附加能力（`csi` 挂载、`agent-runtime` 注入 envd），不是后端选项 |
| 腾讯云 AGS（Agent Runtime） | 云 API `StartSandboxInstance`（从"沙箱工具"启动实例）；CLI `agr`；Python/Go SDK；E2B SDK `Sandbox.create(template=..., timeout=...)`（快速入门页） | E2B SDK `run_code`（`e2b_code_interpreter`，快速入门页） | 概述页："创建、读取、编辑、搜索"，支持 COS/CFS 外挂存储；接口名文档未见（10-05） | `PauseSandboxInstance` / `ResumeSandboxInstance`；`agr instance pause` / `resume`；E2B SDK `pause()` / `Sandbox.connect()`；暂停实例占配额（默认每账号每地域 20 个） | 概述页："进程级快照技术，完整保留运行上下文"；接口名文档未见（10-05） | 文档未见（10-05） | 沙箱工具级超时，duration 字符串（如 `"5m"`），范围 300 秒至 24 小时；返回 `TimeoutSeconds`（启动实例页） | 按工具类型：`code-interpreter`、`browser`、`mobile`、`osworld`、`custom`；自定义工具声明镜像与 K8s 格式资源 |
| OpenSandbox | `POST /sandboxes`（`image`、`snapshotId`、`templateId` 三选一）；多语言 SDK；`osb` CLI | execd `POST /command`（SSE）、`/code`、`/session/{id}/run` | execd `/files/upload`、`/files/download`、`/files/search`、`/files/replace` 等 | `POST /sandboxes/{id}/pause`、`/resume`（202 异步）；README：Firecracker 运行时保留内存与磁盘 | `POST /sandboxes/{id}/snapshots`（可能短暂暂停源沙箱）；`GET`/`DELETE /snapshots/{id}`；以 `snapshotId` 创建 | 文档未见（10-05） | `timeout`（≥60 s，上限由 `server.max_sandbox_timeout_seconds` 决定；null 为不过期）；`POST .../renew-expiration` | 运行时为服务器级配置 `[secure_runtime]`（默认 runc，可配 `gvisor`、`kata`、`firecracker`，后者仅限 Kubernetes；`server/configuration.md`）；请求可带 `platform` 约束、`resourceLimits` / `resourceRequests` |
| DSec（libdsec） | `DSecClient().run_container(DSecContainerRunArgs(...))`；按后端分参数类型与方法 | `sandbox.run_shell` | 沙箱内 chronus 提供"文件系统操作"（§3.3）；SDK 方法名文档未见（10-05） | GPU 作业抢占时由 RL 框架触发暂停（§6.3）；SDK 调用形式文档未见（10-05） | pack_diff 增量磁盘快照，"之后可以作为一个新沙箱恢复"（§6.1）；SDK 调用形式文档未见（10-05） | 文档未见（10-05） | `ttl_running_stop`（空闲超时；示例 300 s） | FnCall、容器、microVM、完整 VM 四档，由参数类型与方法选定；`memory_limit_mb`、`cpu_cores_limit` 按沙箱声明 |
| agent-sandbox（kubernetes-sigs） | CR `Sandbox`（`spec.podTemplate`）；`SandboxClaim`（`warmPoolRef`）；Python `create_sandbox` | Python `sandbox.commands.run(command, timeout=60)` | Python `files` 的 `write` / `read` / `read_to` | `spec.operatingMode: Suspended`（终止 Pod，保留对象与卷）/ `Running`；GKE 扩展 `suspend(snapshot_before_suspend=True)` / `resume()` | GKE 扩展（基于 GKE PodSnapshot）：`snapshots.create`、`restore(snapshot_uid)`；核心 CRD 文档未见（10-05） | 文档未见（10-05） | `shutdownTime`（绝对时间）+ `shutdownPolicy`（`Retain` 默认、`Delete`）；`SandboxClaim.ttlSecondsAfterFinished` | `corev1.PodSpec`（含 `runtimeClassName`；README 称隔离委托给 gVisor 或 Kata）；`SandboxWarmPool` |
| Modal | `modal.Sandbox.create(...)` | `sb.exec(...)` | `sb.filesystem.read_text` / `write_text` / `copy_from_local` / `copy_to_local` 等 | 文档未见（10-05） | `snapshot_filesystem()`（默认保留 30 天，可设 `ttl`，`None` 为不过期）；`snapshot_directory(path)`；`_experimental_snapshot()` 内存快照（Alpha，保留 7 天） | 文件系统快照可"从同一快照创建多个沙箱"；专门 fork 接口文档未见（10-05） | `timeout`（默认 5 分钟，最长 24 小时）；`idle_timeout` | `runtime="gvisor"`（默认）或 `"vm"`；资源参数同 Function |
| Daytona | `daytona.create(CreateSandboxFromSnapshotParams(...))` 或 `CreateSandboxFromImageParams(...)` | `process.exec()`（默认超时 10 s）、`process.code_run()`、会话 | `fs.upload_file` / `fs.download_file` / `fs.list_files` 等 | `sandbox.pause()`（仅 VM/Windows，"文件系统与内存状态被保留"）；`stop()` / `start()`；`archive()`（仅容器） | `daytona.snapshot.create()`（从镜像建模板）；`sandbox._experimental_create_snapshot()`（容器只含文件系统，VM 含内存） | `sandbox.fork(name=...)`（仅 VM/Windows；"不支持容器沙箱"） | `auto_stop_interval`（默认 15 分钟）、`auto_pause_interval`（VM，60 分钟）、`auto_archive_interval`（容器，7 天）、`auto_delete_interval`、`ephemeral` | 由 `snapshot` 选类：`daytona-small` 等为容器，`daytona-vm-*` 为 Linux VM，`windows-*`，`daytona-gpu`；自建快照用 `sandbox_class` |
| Prime Sandboxes | `SandboxClient.create(CreateSandboxRequest(...))`；CLI `prime sandbox create` | `execute_command`；`start_background_job` | `upload_file` / `download_file` | 文档未见（10-05） | `checkpoint(sandbox_id)`（文件系统检查点）、`wait_for_checkpoint`；`CreateSandboxRequest(checkpoint_id=...)` 恢复 | 文档未见（10-05；博文 2026-09-23 列入路线图） | `timeout_minutes`（默认 60）、`idle_timeout_minutes` | 单一形态（README："VM-backed sandbox"）；`cpu_cores`、`memory_gb`、`gpu_count`、`disk_size_gb` |
| OpenEnv | `EnvClient.from_docker_image(...)` / `from_env(...)`；provider `start_container(image, port, env_vars)` | `reset()` / `step(action)` / `state()`（环境语义，不是 shell） | 文档未见（10-05） | 文档未见（10-05） | 文档未见（10-05） | 文档未见（10-05） | 文档未见（10-05） | `LocalDockerProvider`、`DockerSwarmProvider`、`DaytonaProvider`、`ACASandboxProvider`、`ModalProvider`、`HFSandboxProvider`、`NovitaSandboxProvider`、`UVProvider`；`KubernetesProvider` 为占位 |
| Harbor | `BaseEnvironment.start(force_build)`；环境类型由 factory 选择 | `exec()` | `upload_file` / `upload_dir` / `download_file` / `download_dir` | 文档未见（10-05） | 文档未见（10-05） | 文档未见（10-05） | 任务级 `timeout_sec`（Agent、验证等阶段），不是沙箱存活期 | `src/harbor/environments/` 下数十种实现（docker、daytona、modal、e2b、gke、kata、opensandbox、prime、runloop、vercel 等）；`EnvironmentCapabilities` 声明能力；任务声明 `cpus`、`memory_mb`、`gpus` |
| Inspect Sandboxing | 框架在 `task_init` / `sample_init` 中创建；任务或样本以 `sandbox=("docker", "compose.yaml")` 指定 | `exec()`、`exec_remote()` | `write_file()`、`read_file()` | 文档未见（10-05） | 文档未见（10-05） | 文档未见（10-05） | 文档未见（10-05） | 内置 `docker`、`local`；扩展 k8s、daytona、modal、ec2、proxmox、vagrant、openshell（见第 16 章） |
| OpenAI Agents SDK（Manifest / 沙箱接口） | `SandboxClient.create(snapshot=..., manifest=Manifest(...), options=...)`；`SandboxAgent` | `SandboxSession.exec()`；`pty_exec_start()` | `read()`、`write()`、`ls()`、`rm()`、`mv()`、`apply_patch()`；Manifest `entries` 描述工作区 | 核心接口为 `SandboxClient.resume(...)`（恢复会话）；E2B provider `pause()`，其 `on_timeout` 默认 `"pause"` | `SnapshotBase.persist()` / `restore()`；`persist_workspace()` / `hydrate_workspace()`（工作区归档，用于"再水化"） | 文档未见（10-05） | 核心接口文档未见（10-05）；由 provider 选项决定（如 E2B provider 的 `timeout`） | 由 client 选 provider：内置 `docker`、`unix_local`；扩展 blaxel、cloudflare、daytona、e2b、modal、runloop、vercel |

注：各行出处（编号见 C.5 节）：E2B [1][2][3]；AgentENV [4]；CubeSandbox [5]；ACS [6][7][8]；AGS [9][10][11]；OpenSandbox [12]；DSec §2.1、§3.3、§6.1、§6.3 [13]；agent-sandbox [14]；Modal [15][16]；Daytona [17]；Prime [18][19]；OpenEnv [20]；Harbor [21]；Inspect [22]；Agents SDK [23][24]。E2B 的 `POST /sandboxes` 与 `POST /sandboxes/{id}/connect` 已标 deprecated，改用 v2 路径；`connect()` 会把已暂停沙箱恢复运行，文档称"超时只延长不缩短"（`/sandboxes/{id}/connect` 说明）。AgentENV `autoPause` 默认值与 E2B 规范相反（E2B 为 false），见 C.4 节第二条。CubeSandbox 文档写"Snapshot、rollback、clone 是 Cube Sandbox 独有能力，e2b SDK 没有对应 API"，该句未随 E2B 2026 年加入快照与 fork 而更新（E2B 情况见第 16 章 16.2.2 节）。ACS 的 `beta_pause` 等方法名出自其 E2B 接入页的兼容表；ACS 概述页另称支持 E2B 兼容 SDK 与 Sandbox CR 两种接入，"Sandbox CR（推荐）"一语在页面中与 SDK 并列。阿里云 ack-sandbox-manager 组件页（ACK 文档）列有"Snapshot（检查点）创建与克隆恢复""网络策略与出站访问控制""凭据注入（API Key、STS Token）"，但没有给出接口名，也未说明与 ACS Agent Sandbox 的部署关系，本表不把它填入 ACS 行（见 C.5 节 [8]）。DSec 的 pack_diff 是"恢复为新沙箱"的磁盘检查点，与 fork 用途不同（第 24 章 24.3.5 节）。Agents SDK 一行的 `SandboxClient`、`SandboxSession` 为仓库中的抽象类名（`src/agents/sandbox/session/`），各 provider 的实际行为以其扩展实现为准。

## C.2　网络、凭据、I/O 与集成

**表 C-2　网络、凭据、I/O 与集成**

| 系统 | 网络策略：粒度与默认 | 网络策略：运行中修改与分阶段 | 凭据注入 | 流式 I/O | MCP 支持 |
|---|---|---|---|---|---|
| E2B | `allow_internet_access`；`network.allowOut`（CIDR、IP、域名，可通配）与 `denyOut`（仅 CIDR、IP），allow 优先；`egressProxy`（SOCKS5）；默认允许出站 | `PUT /sandboxes/{id}/network`（SDK `updateNetwork`），整体替换，省略字段即清空；无阶段对象 | `network.rules` 按域名对出站 HTTPS 请求注入 header；`/secrets` 管理密文，SDK `Secret.fill('name')` 引用，由出站代理在转发时解析（"The runtime resolves it to a value at sandbox egress"） | envd `Process.Start`、`Connect` 为服务端流；SDK `onStdout` / `onStderr`（Python `on_stdout` / `on_stderr`）；`WatchDir` | 创建参数 `mcp`；MCP gateway 在沙箱内运行，`getMcpUrl()` / `getMcpToken()` |
| AgentENV | `allow_internet_access`（默认 true）；`network.allowOut` / `denyOut`；节点级 `always_denied_cidrs` 先于沙箱策略且不可覆盖 | `PUT /sandboxes/{id}/network`，运行中替换；`PATCH` 扩展参数经 `patch-params` 钩子交给外部扩展 | 规范中无 E2B 的 `rules` / `egressProxy` 字段（以 openapi.yml 为准）；文档未见（10-05） | envd（同 E2B）；`aenv start` / `aenv cn` 交互 shell | 规范保留 `mcp` 字段（`additionalProperties`，无语义说明）；文档未见（10-05） |
| CubeSandbox | `allow_internet_access`、`allowOut`、`denyOut`；L7 `rules`（按 SNI、Host、方法、scheme、路径匹配）；CubeVS eBPF 执行 L3/L4，CubeEgress 透明代理执行 L7 | `PUT /sandboxes/{id}/network`（SDK `update_network` / `updateNetwork`），整体替换；文档警告漏写 `allow_internet_access` 会恢复公网出站 | CubeEgress 按规则追加静态 header（"通常是 `Authorization: Bearer …`，工作负载看不到原始密钥"）；每主机 JSONL 审计日志 | Node SDK `commands.run(..., { onStdout })`；Python `_stream` 模块 | 规范保留 `mcp` 字段（无语义说明）；文档未见（10-05） |
| 阿里云 ACS Agent Sandbox | E2B 接入页兼容表把 network 列为不支持；CR 侧网络字段文档未见（10-05） | 文档未见（10-05） | 文档未见（10-05） | 文档未见（10-05） | 文档未见（10-05） |
| 腾讯云 AGS | 沙箱工具级 `NetworkMode`：`PUBLIC`、`SANDBOX`、`VPC`（`VPC` 需 `VpcConfig.SubnetIds`、`SecurityGroupIds`） | 文档未见（10-05） | `RoleArn` 用于镜像仓库、COS 挂载与日志采集的授权；向沙箱内工作负载注入凭据文档未见（10-05） | E2B SDK `run_code(..., on_stdout=...)`（快速入门页） | 概述页称提供"MCP"接入方式（以 MCP 访问沙箱）；接口文档未见（10-05） |
| OpenSandbox | `networkPolicy`：`defaultAction`（`allow` / `deny`）+ 有序 `egress` 规则（`action`、`target`）；整个 `networkPolicy` 省略或为空对象时以 allow-all 启动（只省略 `defaultAction` 时默认 deny）；创建时不能与 `extensions.poolRef` 同用 | `PATCH /sandboxes/{id}/networkpolicy` **合并**规则（同 target 覆盖，其余保留）；另有 `PUT`、`DELETE` | `credentialProxy.enabled` 打开透明 MITM；egress 侧 `/credential-vault`、`/credential-vault/bindings`；规范称要求 `dns+nft` 执行与网络策略，"强烈建议"默认拒绝 | execd `/command`、`/code`、`/session/{id}/run` 返回 `text/event-stream`；`/command/{id}/logs` | OpenSandbox MCP server（`opensandbox-mcp`），把创建、执行、文本文件操作暴露为 MCP 工具 |
| DSec（libdsec） | `network_rules={"npm": False, "pypi": True}`，按包管理器或镜像服务表达；每沙箱 eBPF 按 IP、端口、协议执行，白名单外拒绝（§2.1、§6.5） | "随着任务进入连通性需求不同的阶段，策略可以动态更新"（§6.5）；由训练框架下发，SDK 调用形式文档未见（10-05） | 文档未见（10-05） | chronus 提供"流式 I/O"（§3.3）；SDK 形式文档未见（10-05） | 文档未见（10-05） |
| agent-sandbox（kubernetes-sigs） | `SandboxTemplate.spec.networkPolicy`（K8s NetworkPolicy 的受限子集，ingress / egress）；`networkPolicyManagement: Managed` 且未给策略时，默认只放行公网出站，阻断 RFC1918 与元数据服务 | 策略按模板共享：修改后由 CNI 作用于该模板的全部现有与将来沙箱；无单沙箱、分阶段接口 | `SandboxClaim.spec.env`，受模板 `envVarsInjectionPolicy`（默认 `Disallowed`）约束；设置 env 的申领不能用预热池；出站凭据注入文档未见（10-05） | 文档未见（10-05） | 文档未见（10-05） |
| Modal | 默认可访问任意公网 IP；`block_network`；`outbound_cidr_allowlist`；`outbound_domain_allowlist`（Beta，仅 443 端口 TLS，按 SNI） | `_experimental_set_outbound_network_policy()`（Alpha；两类白名单须在创建时已配置） | `secrets=[modal.Secret.from_dict(...)]`，以环境变量进入沙箱 | `sb.stdout`；`sb.exec` 返回进程对象 | 文档未见（10-05） |
| Daytona | `networkAllowList`（IPv4 CIDR，最多 10 条）、`domainAllowList`（可通配，最多 100 条）、`networkBlockAll`、`outboundProxyUrl`（仅创建时）；Tier 1–2 受组织级限制，Tier 3–4 默认全通 | Tier 3–4 可在运行中更新，"无需停止或启动"；Tier 1–2 返回错误 | `outboundProxyUrl` 把 HTTP(S) 转给上游代理；注入凭据文档未见（10-05） | `process.get_session_command_logs_async`（stdout / stderr 回调）；`fs.upload_file_stream` / `download_file_stream` | Daytona MCP server，让 Agent 经 MCP 操作沙箱 |
| Prime Sandboxes | `network_allowlist` / `network_denylist`（创建时）；`get_network` | `set_network(allow=... 或 deny=...)`（`PUT /sandbox/{id}/egress-policy`），整体替换，"已建立的连接不会被撤销"；仅 VM 沙箱 | `secrets` 字段（README：值在日志与详情中以 `***` 掩码）；是否以环境变量进入沙箱文档未写明 | `open_process`（异步）；`start_background_job` + `get_background_job` | 文档未见（10-05） |
| OpenEnv | 文档未见（10-05；`DockerSwarmProvider` 的 `overlay_network` 是服务互联网络，不是出站策略） | 文档未见（10-05） | `start_container(..., env_vars=...)`（环境变量） | WebSocket 会话 `/ws` 承载 `reset` / `step` / `state`；进程输出流文档未见（10-05） | 环境服务另设 `/mcp`（`tools/list`、`tools/call`），客户端 `MCPToolClient` |
| Harbor | `network_mode`：`public`（默认）、`allowlist`（配 `allowed_hosts`）、`no-network`；能力位 `disable_internet`、`network_allowlist`、`network_allowlist_hostnames` 等 | `[agent]`、`[verifier]` 可分别覆盖；trial 运行时调用 `set_network_policy(phase_policy)` 切换，后端须声明 `dynamic_network_policy` | `[environment].env`（环境变量）；出站凭据注入文档未见（10-05） | `stream_enabled` / `stream_handle`；能力位 `stream`（SSH 执行与 TCP 转发） | 任务配置 `mcp_servers`（`stdio`、`sse`、`streamable-http`），为 Agent 提供 MCP server |
| Inspect Sandboxing | 自动生成的 compose 设 `network_mode: none`；自定义 compose 会**替换**该设置，文档提醒 Docker Compose 默认可出站 | 文档未见（10-05） | 文档未见（10-05） | `exec_remote(..., stream=True)` 返回 `ExecRemoteProcess` | `mcp_server_sandbox()`：在沙箱内运行 MCP server |
| OpenAI Agents SDK | 核心接口文档未见（10-05）；由 provider 选项决定（如 E2B provider `allow_internet_access`，默认 true） | 文档未见（10-05） | Manifest `environment`；挂载凭据暴露策略只能在可信的 Manifest 实例上设置，拒绝从输入载入；博文主张"让凭据远离执行模型生成代码的环境" | `pty_exec_start()`、`pty_write_stdin()` | `SandboxAgent(mcp_servers=[...])`，MCP server 由 harness 一侧挂载 |

注：出处同表 C-1。E2B `rules` 的说明原文还提醒，"`*.com` 一类宽泛通配是允许的，可能把变换后的凭据暴露给沙箱访问的每个匹配目的地"（`SandboxNetworkConfig.rules`）。CubeSandbox 的整体替换陷阱原文："任何未重申该字段的更新都会让以 `allow_internet_access=false` 创建的沙箱重新获得公网访问"（`docs/guide/network-policy.md`，意译）。OpenSandbox 的 `PATCH` 合并语义与 E2B、AgentENV、CubeSandbox、Prime 的整体替换不同，调用方从一家迁到另一家时，同样的"只发增量"写法会得到相反的结果（推断）。ACS 的网络一格只依据其 E2B 接入页；阿里云 ack-sandbox-manager 页所列"网络策略与出站访问控制"未给接口，未填入。表 14-1 已列出 E2B、Modal、AgentENV、Harbor 的出站默认值与执行点，本表与之一致，DNS 处理不再重复（见第 14 章）。

## C.3　训练场景缺失概念

表 C-3 按第 16 章表 16-2 的编号，把每个系统已经提供的部分支持与仍未见到的概念分开列出：①网络策略作为一等对象；②任务阶段策略切换；③抢占与作业级暂停语义；④完整性约束；⑤fork/分支的语义；⑥资源与后端声明；⑦可与 rollout 关联的可观测性。判断标准沿用表 16-2：只要有对应接口即记"部分"；厂商概述页明确写出、但无接口名的能力也记"部分"，并在格内注明，"缺"指本书所读材料中没有该概念的接口；表 16-2"仍然缺什么"一列中的子项（如组暂停、子实例身份重置、语义级命名策略）在所有系统中都未见，不逐行重复。

**表 C-3　各系统对表 16-2 七个概念的覆盖（本书归纳）**

| 系统 | 部分支持 | 未见 |
|---|---|---|
| E2B | ①（地址与域名级，另有 SOCKS5 代理与出站 header 注入）；②（运行中整体替换，阶段由调用方计时）；③（`pause` 可选是否保留内存；按元数据过滤列表）；⑤（`fork` 1–100）；⑥（资源随模板 `cpuCount`、`memoryMB`；无后端选择）；⑦（指标、日志、事件、webhook） | ④ |
| AgentENV | ①（节点级不可覆盖的 CIDR 拒绝）；②；③（`autoPause` 默认暂停）；⑤（同节点 fork；外部扩展钩子为每个运行实例给出新的 `sandboxInstanceId`）；⑥（资源随模板；仅 microVM，无后端选择）；⑦（`/sandboxes/{id}/metrics`） | ④ |
| CubeSandbox | ①（L3/L4 + L7 规则）；②；③；⑤（`clone` 与原地 `rollback`；跨节点快照）；⑦（日志接口；CubeEgress 审计日志） | ④；⑥（仅 KVM microVM） |
| 阿里云 ACS Agent Sandbox | ③（休眠与唤醒；`SandboxSet` 预热池）；⑤（概述页的 Checkpoint/Restore，无接口名）；⑥（CR 的 Pod 模板资源） | ①②（E2B 接入页列网络为不支持）；④；⑦（E2B 接入页列 logs、metrics 为不支持） |
| 腾讯云 AGS | ①（工具级 `NetworkMode` 三档）；③（`PauseSandboxInstance`）；⑥（工具类型与资源）；⑦（概述页称"全链路轨迹采集观测"，厂商自报，无接口名） | ②；④；⑤ |
| OpenSandbox | ①（`defaultAction` + 有序规则；凭据库）；②（运行中 `PATCH` 合并）；③（pause/resume；资源池与批量创建）；⑤（快照并以 `snapshotId` 创建，无 fork）；⑥（资源声明；运行时为服务器级）；⑦（诊断与 metrics/events 接口） | ④ |
| DSec（libdsec） | ①（语义级 `network_rules`）；②（按阶段动态更新）；③（RL 框架向被抢占作业的沙箱发暂停，SDK 形式未披露）；⑥（四档后端、按沙箱声明资源） | ④（AppArmor 在平台内部，不在 SDK）；⑤（pack_diff 不是 fork）；⑦（watcher 为调度统计，不在 SDK） |
| agent-sandbox（kubernetes-sigs） | ①（模板级 NetworkPolicy，默认阻断内网与元数据）；③（`Suspended` 保留卷；GKE 扩展可先快照再挂起；`SandboxWarmPool`）；⑥（PodSpec 与 `runtimeClassName`）；⑦（K8s conditions） | ②（策略按模板共享，无单沙箱阶段切换）；④；⑤ |
| Modal | ①（CIDR 与域名白名单）；②（Alpha）；⑤（文件系统快照一对多；内存快照 Alpha）；⑥（`runtime` 选 gVisor 或 VM） | ③（无暂停接口）；④；⑦ |
| Daytona | ①（CIDR、域名、全阻断、上游代理）；②（Tier 3–4）；③（VM 暂停保内存；自动停止、暂停、归档）；⑤（VM `fork`，一次一个）；⑥（按快照选容器、VM、Windows、GPU） | ④；⑦ |
| Prime Sandboxes | ①（allow / deny 列表）；②（整体替换，既有连接不撤销）；③（`bulk_delete(labels=...)` 按标签批量删除，无暂停）；⑤（文件系统检查点，可从检查点创建）；⑥（资源声明）；⑦（`get_logs`） | ④ |
| OpenEnv | ⑥（provider 选择） | ①；②；③；④；⑤；⑦（`state()` 返回 episode 元数据，不是沙箱事件） |
| Harbor | ①（三档 `network_mode`）；②（Agent 与验证阶段分别生效，运行时切换）；④（Agent 与验证阶段分离，见第 20 章）；⑥（`EnvironmentCapabilities` 能力声明与资源声明） | ③；⑤；⑦ |
| Inspect Sandboxing | ①（compose `network_mode`，自动生成时默认断网）；④（harness 在沙箱外）；⑥（沙箱类型与 compose 配置）；⑦（评测日志） | ②；③；⑤ |
| OpenAI Agents SDK | ③（会话 `resume` 与快照再水化；provider 级 `pause`）；④（harness 与计算分离；挂载凭据暴露策略）；⑥（provider 选择） | ①②（核心接口未见，交给 provider）；⑤；⑦ |

注：本表是对表 C-1、C-2 的归纳（推断），"部分支持"不评价实现质量。④一栏中 Harbor、Inspect、Agents SDK 的"部分"指架构上把评分或 harness 放在沙箱外，不是以接口声明"Agent 不可读写的路径"；后者在 15 个系统中均未见。

## C.4　读表观察

以下几条只补充第 16 章没有、或需要按本附录核对结果更新的内容；结论本身与第 16 章 16.6 节一致。

**第一，第 16 章初稿表 16-3 的若干"未见"已经过时。** 本附录核对时（2026-10-05）读到：OpenSandbox 规范已有 `POST /sandboxes/{id}/snapshots` 与以 `snapshotId` 创建，网络策略可经 `PATCH .../networkpolicy` 在运行中修改；agent-sandbox 的 `SandboxTemplate` 有 `networkPolicy` 字段，未配置时由控制器施加"只放行公网、阻断内网与元数据服务"的默认策略，另有 GKE 扩展的 `suspend` / `resume` / `restore`；Prime 的 SDK 已提供文件系统检查点与运行中替换出站规则，第 16 章初稿依据 9 月 23 日博文写的"保存、恢复与 fork 在路线图中"应为"检查点已提供，fork 未见"；OpenEnv 的 provider 增加了 Modal、HF Sandbox、Novita。这些更正已同步到第 16 章。

**第二，"兼容 E2B"之下，默认值并不一致。** AgentENV 的 `autoPause` 默认为 true，到期即暂停；E2B 规范默认 false，到期即终止。CubeSandbox 的 `timeout` 是空闲秒数，E2B 的 `timeout` 是存活时间。OpenAI Agents SDK 的 E2B provider 把 `on_timeout` 默认设为 `"pause"`，又与 E2B 自身不同。ACS 的 E2B 接入页把 network、logs、metrics 列为不支持。同一段 `Sandbox.create(..., timeout=300)`，在 E2B、AgentENV、CubeSandbox、经 Agents SDK 的 E2B provider 上分别意味着"5 分钟后终止""5 分钟后暂停""空闲 5 分钟后终止"和"5 分钟后暂停"；若同时传 `network=...`，在 ACS 上不受支持（推断，依据各自文档）。这是第 16 章"接口能共用，后端不能"的一个字段级实例，也是第 16 章 16.8.1 节原则一主张"能力查询接口"的直接理由。

**第三，网络策略的修改语义分成四种。** 整体替换（E2B、AgentENV、CubeSandbox、Prime）；合并补丁（OpenSandbox）；模板级共享、一次改动作用于该模板全部沙箱（agent-sandbox）；由 harness 按阶段切换（Harbor、DSec）。整体替换有一个已被文档承认的陷阱：CubeSandbox 指出，更新时漏写 `allow_internet_access` 会让本该断网的沙箱重新获得公网出站；E2B 的 `PUT .../network` 同样"省略字段即清空"。训练框架在"setup 结束、收紧网络"这一步若只发增量，在替换语义的平台上会适得其反（推断；第 16 章 16.6.3 节第 2 步）。Harbor 是 15 个系统中唯一同时具备"阶段"概念与"后端能力声明"（`dynamic_network_policy`）的，它在后端不支持运行中切换时直接报错，而不是静默降级。

**第四，凭据有两条路，训练场景只该走一条。** 一条是出站时注入：E2B 的 `rules` 与 `Secret.fill`、CubeSandbox 的 CubeEgress、OpenSandbox 的凭据库，真实密钥不进入沙箱。另一条是环境变量：Modal 的 `secrets`、Harbor 的 `env`、OpenEnv 的 `env_vars`、agent-sandbox 的 `SandboxClaim.spec.env`，以及写法上看不出去向的 Prime `secrets`。面对"作为对手的模型"（第 2 章），后一条等于把密钥交给被训练的模型；第 19 章记录的取回型 reward hacking 不需要越狱，只需要 `env`（推断）。

**第五，fork 有了五种形态，子实例语义仍是空白。** E2B 与 AgentENV 是服务端 `fork`（1–100，AgentENV 限同节点）；CubeSandbox 是 SDK 层的 `clone`（先快照再批量创建，无上限说明），另有原地 `rollback`；Daytona 是一次一个、仅限 VM 的 `fork`；Modal 是"从同一文件系统快照创建多个沙箱"；Prime 只有文件系统检查点。没有一家在接口层说明子实例的随机种子、网络身份、已签发令牌是否重置。唯一接近的是 AgentENV 的外部扩展钩子：每个运行实例有新的 `sandboxInstanceId`，宿主侧 IP 在恢复后"可能变化"，但这只是给扩展的通知，不是对 guest 内熵的承诺（见第 11 章 11.6 节）。

**第六，"MCP 支持"指的是三件不同的事。** 一是沙箱**内**运行 MCP server，供 Agent 调用（E2B MCP gateway、Inspect `mcp_server_sandbox()`、Harbor 任务的 `mcp_servers`）；二是把沙箱**本身**包装成 MCP 工具，供外部 Agent 创建和操作（OpenSandbox MCP server、Daytona MCP server，AGS 概述页的"MCP 接入"大概率属于此类，推断）；三是环境以 MCP 暴露工具语义（OpenEnv 的 `/mcp`，与第 16 章 16.4.4 节 AEnvironment 同一思路）。第一类把 MCP server 放进了对手所在的隔离域，第二类把沙箱控制面交给了 Agent，两者的威胁模型不同（见第 16 章 16.5 节），比较各系统"是否支持 MCP"时应先分清是哪一类。

**第七，作业级分组仍然只有零星接口。** 能按组操作的只有 E2B 的元数据过滤列表、Prime 的 `bulk_delete(labels=...)`、OpenSandbox 的资源池与批量创建、agent-sandbox 与 ACS 的预热池；没有一家提供"按组暂停"。表 16-2 第③项的核心缺口未变。

## C.5　出处清单

所有条目的核对日期均为 2026-10-05，另有说明者除外。仓库条目写默认分支被读取时的提交号与提交日期。

[1] E2B. e2b-dev/infra：`spec/openapi.yml`（`NewSandbox`、`NewSandboxV2`、`SandboxNetworkConfig`、`SandboxNetworkUpdateConfig`、`SandboxPauseRequest`、`SandboxForkRequest`、`Secret`、`/sandboxes/{sandboxID}/*` 路径）；`packages/envd/spec/process/process.proto`、`packages/envd/spec/filesystem/filesystem.proto`. GitHub，HEAD 25b1961. https://github.com/e2b-dev/infra

[2] E2B. Documentation：Persistence、Snapshots、Fork、Commands、Streaming、Secrets（Inject）、MCP Gateway 各页. https://docs.e2b.dev/sandbox/persistence.md ；https://docs.e2b.dev/sandbox/snapshots.md ；https://docs.e2b.dev/sandbox/fork.md ；https://docs.e2b.dev/commands.md ；https://docs.e2b.dev/commands/streaming.md ；https://docs.e2b.dev/secrets/inject.md ；https://docs.e2b.dev/mcp-gateway.md

[3] E2B. Internet access（文档；第 14 章 2026-10-03 读取，本附录未重读）. https://docs.e2b.dev/network/internet-access.md

[4] kvcache-ai. AgentENV：`README.md`（`aenv` CLI 参考）；`src/api/openapi.yml`；`docs/src/integration/e2b.md`；`docs/src/concepts/sandboxes/auto-eviction.md`、`networking.md`；`docs/src/concepts/custom-extension/*.md`；`docs/src/configuration/reference.md`（`repository_backend`）；`src/orchestrator/service.rs`（fork 限同节点）. GitHub，HEAD 5843159（2026-10-03）. https://github.com/kvcache-ai/AgentENV

[5] TencentCloud. CubeSandbox：`openapi.yml`（CubeAPI）；`docs/guide/snapshot-rollback-clone.md`、`lifecycle.md`、`network-policy.md`、`security-proxy.md`、`cross-node-snapshot.md`；`sdk/files-api-streaming.md`；`sdk/node/README.md`. GitHub，HEAD e02976a（2026-09-30）. https://github.com/TencentCloud/CubeSandbox

[6] 阿里云. Agent Sandbox 概述（ACS 用户指南）. https://help.aliyun.com/zh/cs/user-guide/agent-sandbox/

[7] 阿里云. 使用 E2B SDK 接入 Agent Sandbox；在 ACS 集群中创建 Agent Sandbox. https://help.aliyun.com/zh/cs/user-guide/connect-to-agent-sandbox-using-the-e2b-sdk ；https://help.aliyun.com/zh/cs/user-guide/create-an-agent-sandbox

[8] 阿里云. ack-sandbox-manager（ACK 组件说明）. https://help.aliyun.com/zh/cs/user-guide/ack-sandbox-manager （只作表注参考，未填入 ACS 行）

[9] 腾讯云. Agent Runtime 产品文档（概述）. https://cloud.tencent.com/document/product/1814/129423

[10] 腾讯云. Agent Runtime：快速入门（E2B SDK `Sandbox.create`、`run_code(on_stdout=...)`）；启动沙箱实例（`StartSandboxInstance`）；暂停与恢复 Sandbox Instance. https://cloud.tencent.com/document/product/1814/123816 ；https://cloud.tencent.cn/document/product/1814/132322 ；https://cloud.tencent.com/document/product/1814/132323

[11] 腾讯云. Agent Runtime：创建沙箱工具（`NetworkMode`、`RoleArn`、超时）. https://cloud.tencent.com/document/product/1814/132210

[12] OpenSandbox（opensandbox-group）：`specs/sandbox-lifecycle.yml`、`specs/execd-api.yaml`、`specs/egress-api.yaml`；`README.md`（MCP、Firecracker 暂停）；`server/configuration.md`（`[secure_runtime]`）. GitHub，HEAD c7dc78a（2026-10-01）. https://github.com/opensandbox-group/OpenSandbox

[13] DeepSeek-AI. *DeepSeek Elastic Compute (DSec): A Sandbox Infrastructure for Effective Agentic Training at Scale*. arXiv:2609.22978v1（预印本），§2.1 代码清单、§3.3、§6.1、§6.3、§6.5；本附录回原文复核 §2.1 与 §3.3，其余与第 24 章一致. https://arxiv.org/html/2609.22978v1

[14] Kubernetes SIG Apps. agent-sandbox：`api/v1beta1/sandbox_types.go`；`extensions/api/v1beta1/sandboxtemplate_types.go`、`sandboxclaim_types.go`；`clients/python/agentic-sandbox-client/k8s_agent_sandbox/`（含 `gke_extensions/snapshots/`）. GitHub，HEAD fa39d57（2026-10-05）. https://github.com/kubernetes-sigs/agent-sandbox

[15] Modal. Sandboxes；Sandbox file access；Sandbox snapshots（文档）. https://modal.com/docs/guide/sandbox ；https://modal.com/docs/guide/sandbox-files ；https://modal.com/docs/guide/sandbox-snapshots

[16] Modal. Sandbox networking（文档）. https://modal.com/docs/guide/sandbox-networking

[17] Daytona. Sandboxes；Snapshots；Network limits；Process and code execution；Log streaming；File system operations；MCP（文档）. https://www.daytona.io/docs/en/sandboxes.md ；https://www.daytona.io/docs/en/snapshots.md ；https://www.daytona.io/docs/en/network-limits.md ；https://www.daytona.io/docs/en/process-code-execution.md ；https://www.daytona.io/docs/en/log-streaming.md ；https://www.daytona.io/docs/en/file-system-operations.md ；https://www.daytona.io/docs/en/mcp.md 。另：daytonaio/daytona 仓库 README 称"自 2026 年 6 月起核心开发转入私有代码库"，HEAD ec4c21b（2026-06-25），本附录未据仓库填表

[18] Prime Intellect. prime：`packages/prime-sandboxes/src/prime_sandboxes/sandbox.py`、`models.py`；`packages/prime-sandboxes/README.md`. GitHub，HEAD 32098eb（2026-10-04）. https://github.com/PrimeIntellect-ai/prime

[19] Prime Intellect. Prime Sandboxes（博文）. 2026-09-23（第 16 章读取）. https://www.primeintellect.ai/blog/sandboxes

[20] Hugging Face 等. OpenEnv：`src/openenv/core/env_client.py`、`mcp_client.py`、`containers/runtime/*.py`. GitHub，HEAD 436ee3a（2026-10-05）. https://github.com/huggingface/OpenEnv

[21] Harbor Framework. harbor：`src/harbor/environments/base.py`、`capabilities.py`；`src/harbor/models/task/config.py`；`src/harbor/trial/trial.py`. GitHub，HEAD b53b813（2026-10-04）. https://github.com/harbor-framework/harbor

[22] UK AI Security Institute. inspect_ai：`src/inspect_ai/util/_sandbox/environment.py`、`docker/config.py`；`src/inspect_ai/tool/_mcp/server.py`；`docs/sandboxing.qmd`. GitHub，HEAD fbcdd75（2026-10-05）. https://github.com/UKGovernmentBEIS/inspect_ai ；文档 https://inspect.aisi.org.uk/sandboxing.html

[23] OpenAI. openai-agents-python：`src/agents/sandbox/manifest.py`、`snapshot.py`、`session/sandbox_client.py`、`session/base_sandbox_session.py`、`sandbox_agent.py`；`src/agents/extensions/sandbox/`（含 `e2b/sandbox.py`）. GitHub，HEAD d27abe8（2026-10-05）. https://github.com/openai/openai-agents-python

[24] OpenAI. *The next evolution of the Agents SDK*. 2026-04-15（第 16 章读取）. https://openai.com/index/the-next-evolution-of-the-agents-sdk/

---

版本说明：2026-10-05 初稿；同日回原文独立核对后修订 24 处。2026-10-06 修订：核对方式与读表说明改为面向读者的写法。
