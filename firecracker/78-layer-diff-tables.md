# 78 · 三层差异总表（文件级）

> 这本书的第九、第十部分按主题讲两层改动。本篇换一个维度：按**文件**把它们摊开，
> 每个被改过的文件一行，给出增删行数、一句话的改动摘要，以及展开讲它的篇。
> 表后是一份「升级 Firecracker 时的重放清单」，按依赖顺序排列。
>
> **读者**：要把这两层改动移植到新的上游版本、或者要快速定位某个文件被谁改过的维护者。
> **预备**：[第 01 篇 · 源流与仓库地图](01-lineage-and-repo-map.md)；两层改动的主题式叙述在第九、第十部分。
> **代码**：本篇不引用具体代码，只列文件与行数；所有数字用本篇第 1 节的命令现算。

---

## 0. 本篇要回答的问题

1. 从上游 v1.12.1 到 e2b 定制版 `a41d3fb`，一共动了哪些文件，每个文件动了什么？
2. ARM 适配版迁入的 `54a1c1a` 与 e2b infra 钉的 `a41d3fb` 之间差的那五个文件，分别差什么？
3. 从 `54a1c1a` 到 ARM 适配版 `3863c76`，改动怎么分成构建修复、HDBSS 使能、checkpoint 扩展三段？
4. guest 内核这一层的「差异」到底是什么，部署用的版本与书里引用的版本差在哪里？
5. 要把这两层改动重放到一个新的上游版本上，应该按什么顺序做，哪一步有取舍要重新判断？

---

## 1. 表的口径

三层基线与它们的提交在 [STYLE.md 第二节](STYLE.md) 有定义，这里只重复表所依赖的那部分：

| 记号 | 含义 |
|---|---|
| `v1.12.1` | 上游 firecracker-microvm/firecracker 的 tag（commit `d990331f7`） |
| `54a1c1a` | e2b 分叉 `firecracker-v1.12-direct-mem` 上最后一个不带 uffd 写保护的提交 |
| `a41d3fb` | 同一分支上 e2b infra 2026.09 钉的默认版本 `v1.12.1_a41d3fb` |
| `9e880db` | KASandbox 仓库里把 `54a1c1a` 的工作树整树迁入 `firecracker/` 的那个提交 |
| `b8e85c3` | ARM 构建修复完成、HDBSS 尚未引入的中间状态 |
| `98f3f53` | HDBSS 使能与硬化完成、checkpoint 扩展尚未开始的中间状态 |
| `3863c76` | ARM 适配版，部署在鲲鹏上的 `firecracker.arm` 对应的提交 |

本篇所有行数用下面四条命令产生，用 `--numstat` 而不是 `--stat`，因为后者会把长路径截断成 `.../foo.rs`：

```bash
git -C tmp/e2b-book-src/fc-e2b diff --numstat v1.12.1 a41d3fb
git -C tmp/e2b-book-src/fc-e2b diff --numstat 54a1c1a a41d3fb
git -C KASandbox diff --numstat 9e880db b8e85c3 -- firecracker
git -C KASandbox diff --numstat b8e85c3 3863c76 -- firecracker
```

两点口径说明。第一，`+ / −` 是 diff 的增删行数，不是「净新增代码量」：
改写一行算一增一删，移动代码也会双计。第二，KASandbox 的路径前缀 `firecracker/` 在表里一律省掉，
写成相对于 Firecracker 仓库根的路径，这样三张表的第一列可以直接互相对照。

「篇」一列指向展开讲这个改动的篇目。一个文件被多篇讲到时全部列出；纯粹跟随性的改动
（例如某个结构体加了字段之后所有构造点都要补一行）归到引入该字段的那一篇。

---

## 2. 上游 v1.12.1 → e2b 定制版 a41d3fb

合计 **34 个文件，+1042 / −64 行**。其中 `src/` 下的源码 18 个文件、+696 / −21 行，其余是
构建脚本、seccomp 表、swagger 规格与测试。按主题分成六组。

### 2.1 内存查询三端点

这一组是分叉存在的理由：把 guest 内存的布局、常驻情况与脏页情况变成可以查询的东西，
让 orchestrator 直接读进程内存而不是读快照文件。三个端点分别在第 50、51、52 篇。

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `src/vmm/src/vstate/vm.rs` | +192 / −1 | 新增 `GuestMemoryRegionMapping` 结构、`guest_memory_mappings()` 列出 GPA 到 HVA 的区间映射、`get_memory_info()` 返回常驻与全零两张位图、自由函数 `mincore_bitmap()` | [50](50-memory-mappings-api.md)、[51](51-memory-resident-empty-api.md) |
| `src/vmm/src/utils/pagemap.rs` | +115 / −0 | 新文件：`PagemapEntry` 解析 `/proc/self/pagemap` 的 64 位条目，`PagemapReader::is_page_dirty()` 按 `is_present()` 与 `is_write_protected()` 判脏 | [52](52-memory-dirty-api.md) |
| `src/vmm/src/lib.rs` | +44 / −0 | `Vmm::get_dirty_memory()`：先用 `mincore` 缩小范围，再对常驻页读 pagemap，合成一张扁平位图；含一段 TODO 注释说明有了 WP 事件其实可以跳过这一步 | [52](52-memory-dirty-api.md) |
| `src/vmm/src/utils/mod.rs` | +2 / −0 | 挂上 `pagemap` 模块 | [52](52-memory-dirty-api.md) |
| `src/vmm/src/rpc_interface.rs` | +67 / −5 | 新增 `VmmAction::GetMemoryMappings` / `GetMemory` / `GetMemoryDirty` 与对应的 `VmmData` 变体；三者都登记为 Runtime 动作 | [50](50-memory-mappings-api.md)、[51](51-memory-resident-empty-api.md)、[52](52-memory-dirty-api.md) |
| `src/vmm/src/vmm_config/instance_info.rs` | +29 / −1 | `InstanceInfo` 加 `memory_regions` 字段；新增 `MemoryMappingsResponse`、`MemoryResponse`、`MemoryDirty` 三个响应结构 | [50](50-memory-mappings-api.md) |
| `src/firecracker/src/api_server/request/memory.rs` | +52 / −0 | 新文件：`GET /memory/mappings`、`GET /memory`、`GET /memory/dirty` 三条路由的解析 | [50](50-memory-mappings-api.md) |
| `src/firecracker/src/api_server/parsed_request.rs` | +70 / −0 | 路由分发加 `memory` 前缀；三个新 `VmmData` 变体的序列化出口 | [50](50-memory-mappings-api.md) |
| `src/firecracker/src/api_server/request/mod.rs` | +1 / −0 | 挂上 `memory` 模块 | [50](50-memory-mappings-api.md) |
| `src/firecracker/src/main.rs` | +1 / −0 | 构造 `InstanceInfo` 时补 `memory_regions: None` | [50](50-memory-mappings-api.md) |
| `src/cpu-template-helper/src/utils/mod.rs` | +1 / −0 | 同上，另一个构造点 | [50](50-memory-mappings-api.md) |
| `src/firecracker/swagger/firecracker.yaml` | +82 / −1 | 补三个端点的定义与响应模型；同时把 `mem_file_path` 从 required 里去掉（见 2.3） | [50](50-memory-mappings-api.md)、[54](54-optional-memfile-snapshot.md) |
| `tests/framework/http_api.py` | +2 / −0 | 测试框架注册 `/memory/mappings` 与 `/memory` 两个 Resource | [50](50-memory-mappings-api.md) |
| `tests/integration_tests/functional/test_api.py` | +237 / −0 | 三个端点的功能用例，外加无 memfile 的 `create` 用例 | [50](50-memory-mappings-api.md)、[54](54-optional-memfile-snapshot.md) |

`src/vmm/src/vstate/vm.rs` 是这一层改得最多的源码文件，也是三层里唯一被两层都大幅改过的文件
（ARM 适配版在它上面又加了 +139，见 4.2、4.3）。

### 2.2 uffd 写保护与依赖替换

提交 `8fc760f61` 一个提交改了四个文件。它是 2.1 里脏页判据能成立的前提，
也是 ARM 适配版唯一主动放弃的 e2b 改动。

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `src/vmm/Cargo.toml` | +5 / −1 | `userfaultfd` 从 crates.io 的 `0.8.1` 换成 e2b 分叉的 `feat_write_protection` 分支，开 `linux5_7` / `linux5_13` / `linux6_7` 三个特性 | [53](53-uffd-write-protection.md) |
| `Cargo.lock` | +26 / −3 | 上一行的锁定结果，新增一个 git 来源条目 | [53](53-uffd-write-protection.md) |
| `src/vmm/src/persist.rs` | +22 / −4 | `guest_memory_from_uffd()` 改为要求 `EVENT_REMOVE \| MISSING_HUGETLBFS \| WP_ASYNC`，用 `RegisterMode::MISSING \| WRITE_PROTECT` 注册每个区域，大页时立刻整区 `write_protect()`；新增 `GuestMemoryFromUffdError::WriteProtect` | [53](53-uffd-write-protection.md) |
| `src/vmm/src/lib.rs` | +4 / −0 | 那段 TODO 注释：有了 WP 事件可以不读 pagemap | [53](53-uffd-write-protection.md) |

这四行与第 3 节的小表完全重合，只是那里还多一条 CI 配置的删除。

### 2.3 可选 memfile 的快照

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `src/vmm/src/vmm_config/snapshot.rs` | +3 / −1 | `CreateSnapshotParams.mem_file_path` 由 `PathBuf` 改成 `Option<PathBuf>`，加 `skip_serializing_if` | [54](54-optional-memfile-snapshot.md) |
| `src/vmm/src/persist.rs` | +5 / −2 | `create_snapshot()` 里只有给了路径才调 `snapshot_memory_to_file()`；不给则写完 vmstate 直接进入队列重新标脏 | [54](54-optional-memfile-snapshot.md) |
| `src/firecracker/src/api_server/mod.rs` | +2 / −2 | 测试里的 `CreateSnapshotParams` 跟随改成 `Some(...)` | [54](54-optional-memfile-snapshot.md) |
| `src/firecracker/src/api_server/request/snapshot.rs` | +2 / −2 | 同上 | [54](54-optional-memfile-snapshot.md) |
| `src/vmm/tests/integration_tests.rs` | +1 / −1 | 同上 | [54](54-optional-memfile-snapshot.md) |

表里 `persist.rs` 的 +5 / −2 是从 2.2 的那一行里分出来的：这个文件被两个提交各改一次，
`git diff v1.12.1 a41d3fb` 给出的合计是 +27 / −6。类型改成 `Option` 之后要改的地方只有三个测试构造点，
这是上游把快照参数收在一个结构体里带来的好处。

### 2.4 seccomp 表

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `resources/seccomp/x86_64-unknown-linux-musl.json` | +11 / −3 | `vmm` 段加 `mincore` 与 `pread64`；顺手把一处缩进对齐，并去掉文件末尾换行 | [55](55-seccomp-build-upload-and-upstream-fixes.md) |
| `resources/seccomp/aarch64-unknown-linux-musl.json` | +4 / −0 | 只加 `mincore`，没有 `pread64` | [55](55-seccomp-build-upload-and-upstream-fixes.md)、[62](62-aarch64-seccomp-filter.md) |

两张表的不对称是这一层留给下一层的一个坑：在 aarch64 上调用 `/memory/dirty` 会因为 `pread64`
不在白名单而触发 SIGSYS。ARM 适配版在最后一个提交 `3863c76` 才补上（见 4.3）。

### 2.5 构建、发布与测试姿态

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `scripts/build.sh` | +17 / −0 | 新文件：版本名 `v<swagger 版本>_<7 位哈希>`、`tools/devtool -y build --release`、产物路径写死 `x86_64-unknown-linux-musl` | [55](55-seccomp-build-upload-and-upstream-fixes.md) |
| `scripts/upload.sh` | +13 / −0 | 新文件：`gsutil` 传到 `<project>-fc-versions` 桶 | [55](55-seccomp-build-upload-and-upstream-fixes.md) |
| `Makefile` | +12 / −0 | 新文件：`build` / `upload` / `build-and-upload` 三个目标，从 `.env` 取 `GCP_PROJECT_ID` | [55](55-seccomp-build-upload-and-upstream-fixes.md) |
| `.tool-versions` | +2 / −0 | 新文件：`gcloud 534.0.0`、`rust 1.85.0` | [55](55-seccomp-build-upload-and-upstream-fixes.md) |
| `.gitignore` | +1 / −0 | 忽略 `.env` | [55](55-seccomp-build-upload-and-upstream-fixes.md) |
| `tools/test.sh` | +1 / −1 | `$BUILDKITE` 未设置时不再报错（`${BUILDKITE:-false}`） | [55](55-seccomp-build-upload-and-upstream-fixes.md) |
| `tests/integration_tests/functional/test_shut_down.py` | +0 / −9 | 删掉线程数断言 | [55](55-seccomp-build-upload-and-upstream-fixes.md) |
| `.github/workflows/dependency_modification_check.yml` | +0 / −17 | 删除整个工作流：不再检查依赖与 lock 文件的改动 | [55](55-seccomp-build-upload-and-upstream-fixes.md) |

`scripts/build.sh` 里写死的架构是 ARM 适配版第一个要改的东西（见 4.1）。
删掉依赖检查工作流是 `a41d3fb` 这个提交本身做的事，它直接服务于 2.2 里换 crate 的改动。

### 2.6 合入的上游 v1.12 分支修复

这五个提交来自上游的 `firecracker-v1.12` 维护分支，不是分叉自己的改动。
它们全部落在 `tests/` 里，没有碰生产代码。

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `tests/integration_tests/functional/test_cpu_features_host_vs_guest.py` | +13 / −8 | AMD 宿主 CPU 特性检查修正；`ibpb_exit_to_user` 归为宿主独有特性 | [55](55-seccomp-build-upload-and-upstream-fixes.md) |
| `tests/integration_tests/functional/test_cpu_template_helper.py` | +6 / −1 | `MSR_TSC_RATE` 进入 MSR 例外表 | [55](55-seccomp-build-upload-and-upstream-fixes.md) |
| `tests/integration_tests/security/test_vulnerabilities.py` | +1 / −1 | Spectre / Meltdown 检查脚本换 URL | [55](55-seccomp-build-upload-and-upstream-fixes.md) |

判断某个提交是不是上游的，用 `git -C tmp/e2b-book-src/fc-e2b log upstream/firecracker-v1.12` 对照哈希即可；
分叉的 clone 里保留了 `upstream` 远端。

---

## 3. 54a1c1a 与 a41d3fb 之差

ARM 适配版迁入的是 `54a1c1a`，不是 e2b infra 钉的 `a41d3fb`。两者之间只有两个提交，
落到文件上是五个：

| 文件 | + / − | 改动 | 来自 | 篇 |
|---|---|---|---|---|
| `src/vmm/Cargo.toml` | +5 / −1 | `userfaultfd` 换成 e2b 分叉的写保护分支 | `8fc760f61` | [53](53-uffd-write-protection.md)、[57](57-which-fork-commit-and-uffd-wp.md) |
| `Cargo.lock` | +26 / −3 | 锁定上一行 | `8fc760f61` | [53](53-uffd-write-protection.md) |
| `src/vmm/src/persist.rs` | +22 / −4 | uffd 以 `MISSING \| WRITE_PROTECT` 注册、大页立即整区写保护、新增 `WriteProtect` 错误 | `8fc760f61` | [53](53-uffd-write-protection.md)、[57](57-which-fork-commit-and-uffd-wp.md) |
| `src/vmm/src/lib.rs` | +4 / −0 | TODO 注释 | `8fc760f61` | [53](53-uffd-write-protection.md) |
| `.github/workflows/dependency_modification_check.yml` | +0 / −17 | 删除依赖检查工作流 | `a41d3fb53` | [55](55-seccomp-build-upload-and-upstream-fixes.md) |

合计 +57 / −25。去掉 `Cargo.lock` 与 CI 配置，源码上的实质差别只有一句话：**有没有 uffd 写保护**。
这句话的后果是：ARM 适配版的 `/memory/dirty` 里 pagemap 的 WP 位永远是 0，
判据退化成「常驻即脏」；这也是 ARM 适配版后来要另找脏页来源（HDBSS）的起点。
选择的理由与另外两种解法的比较在[第 57 篇](57-which-fork-commit-and-uffd-wp.md)。

---

## 4. e2b 54a1c1a → ARM 适配版 3863c76

整段合计 **28 个文件，+1679 / −36 行**（三段之间只有 `src/firecracker/src/main.rs` 一个重叠文件，它在第一段与第二段各改一次）。按提交顺序分成三段：构建修复、HDBSS 使能、checkpoint 扩展。

### 4.1 ARM 构建修复（9e880db → b8e85c3）

两个文件，+18 / −14。

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `scripts/build.sh` | +6 / −2 | 产物路径由写死的 `x86_64-unknown-linux-musl` 改成按 `uname -m` 拼出 `${arch}-unknown-linux-musl` | [58](58-building-and-running-on-aarch64.md) |
| `src/firecracker/src/main.rs` | +12 / −12 | `main_exec()` 里调用 `resize_fdtable()` 的整段被注释掉 | [58](58-building-and-running-on-aarch64.md) |

第二行是三层改动里最典型的一处技术债：**代码没有删，是被注释掉的**，
增删各 12 行也正是「整段加 `//` 前缀」的形态。后果是文件描述符表不再预先扩容，
快照恢复时的表扩张要由内核在运行中完成；上游把这一步单独做出来就是为了避开那次扩张。
重放到新上游时这一段应该改成按错误类型容忍，而不是整段注释掉。

### 4.2 HDBSS 使能与硬化（b8e85c3 → 98f3f53）

七个文件，+156 / −2。这一段回答第 3 节留下的问题：没有 uffd 写保护，脏页从哪里来。

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `src/vmm/src/vstate/vm.rs` | +103 / −0 | 新增 `DirtyTrackingBackend` 枚举（`off` / `kvm-wp` / `hdbss`）、`Vm::dirty_tracking()` 与 `Vm::setup_dirty_tracking()`：按环境变量决定是否启用、失败是否致命 | [65](65-dirty-tracking-backend.md) |
| `src/vmm/src/arch/aarch64/vm.rs` | +40 / −1 | `ArchVm::enable_hdbss()`：本地定义 `KVM_CAP_ARM_HW_DIRTY_STATE_TRACK`（502）与 openEuler 的 `KVM_ENABLE_CAP` 请求号，直接 `libc::ioctl`；缓冲区阶数由调用方传入 | [66](66-hdbss.md) |
| `src/vmm/src/builder.rs` | +5 / −0 | 冷启动与快照恢复两条路径在 `register_memory_regions()` 之后各插一次 `setup_dirty_tracking()` | [65](65-dirty-tracking-backend.md) |
| `src/vmm/src/vmm_config/instance_info.rs` | +3 / −0 | `InstanceInfo` 加 `dirty_tracking: Option<String>`，把实际生效的后端上报给调用方 | [65](65-dirty-tracking-backend.md) |
| `src/vmm/src/lib.rs` | +3 / −1 | 脏页查询改走选中的后端 | [65](65-dirty-tracking-backend.md) |
| `src/firecracker/src/main.rs` | +1 / −0 | 构造 `InstanceInfo` 时补 `dirty_tracking: None` | [65](65-dirty-tracking-backend.md) |
| `src/cpu-template-helper/src/utils/mod.rs` | +1 / −0 | 同上，另一个构造点 | [65](65-dirty-tracking-backend.md) |

`kvm_bindings` 里没有这个能力号，openEuler 的 `KVM_ENABLE_CAP` 请求号也与主线不同，
所以两个常量都写在 `enable_hdbss()` 里。这是把发行版内核的私有扩展接进来的代价，
细节与风险在[第 66 篇](66-hdbss.md)。

### 4.3 checkpoint / restore 扩展（98f3f53 → 3863c76）

23 个文件，+1505 / −20。分四组看：核心、快照产物、设备、过滤器。

**核心：回滚本身**

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `src/vmm/src/rollback.rs` | +656 / −0 | 新文件：回滚的分阶段实现与 `RollbackError`，含拓扑校验、提交点划分、`faults_vm()` 判定；另有 `test_restore_dirty_is_dump_dirty_inverse` 等单元测试 | [69](69-rollback-api-and-phases.md)、[73](73-failure-model-faulted-and-seccomp.md) |
| `src/vmm/src/vstate/memory.rs` | +276 / −4 | `dump_dirty()` / `restore_dirty()`；FCDB 位图格式的 `serialize_dirty_bitmap()` 与 `deserialize_dirty_bitmap()`（magic `FCDB`、版本 1、按 u64 小端打包） | [67](67-dirty-bitmap-sidecar.md)、[70](70-rollback-memory.md) |
| `src/vmm/src/lib.rs` | +60 / −1 | `Vmm::restore_vcpu_states_in_place()`；`pause_vm` / `resume_vm` 对 `Faulted` 的处理 | [71](71-rollback-vcpu-and-gic.md)、[73](73-failure-model-faulted-and-seccomp.md) |
| `src/vmm/src/vstate/vcpu.rs` | +29 / −2 | 新增 `VcpuEvent::RestoreState` 与 `VcpuResponse::RestoredState`，让 vCPU 线程在自己的线程上写回状态 | [71](71-rollback-vcpu-and-gic.md) |
| `src/vmm/src/arch/aarch64/vcpu.rs` | +8 / −0 | `KvmVcpu::restore_state_in_place()`：在已运行过的 vCPU fd 上走一遍常规恢复序列，其中的 `KVM_ARM_VCPU_INIT` 就是架构定义的复位 | [71](71-rollback-vcpu-and-gic.md) |
| `src/vmm/src/arch/x86_64/vcpu.rs` | +8 / −0 | 同名函数；x86_64 上常规恢复序列本来就能作用于已存在的 fd，两条路线合一 | [71](71-rollback-vcpu-and-gic.md) |
| `src/vmm/src/vstate/vm.rs` | +36 / −2 | `snapshot_memory_to_file()` 增加 sidecar 路径参数；回滚所需的 GIC 状态写回 | [67](67-dirty-bitmap-sidecar.md)、[71](71-rollback-vcpu-and-gic.md) |

**快照产物与 API 面**

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `src/vmm/src/vmm_config/snapshot.rs` | +65 / −0 | `CreateSnapshotParams.dirty_bitmap_path`；新增 `RollbackSnapshotParams`、`SaveDirtyBitmapParams`、`RollbackTimings`、`RollbackResponse` | [67](67-dirty-bitmap-sidecar.md)、[68](68-save-dirty-bitmap-api.md)、[69](69-rollback-api-and-phases.md) |
| `src/vmm/src/rpc_interface.rs` | +76 / −1 | `VmmAction::RollbackSnapshot` 与 `SaveDirtyBitmap`，两者都是 Runtime 且要求 `Paused`；`VmmData::Rollback`；`VmmActionError::RollbackSnapshot` | [68](68-save-dirty-bitmap-api.md)、[69](69-rollback-api-and-phases.md) |
| `src/firecracker/swagger/firecracker.yaml` | +95 / −0 | 两个新端点与四个新模型的规格 | [68](68-save-dirty-bitmap-api.md)、[69](69-rollback-api-and-phases.md) |
| `src/firecracker/src/api_server/request/snapshot.rs` | +17 / −0 | `PUT /snapshot/rollback` 与 `PUT /snapshot/save-dirty-bitmap` 两条路由 | [68](68-save-dirty-bitmap-api.md)、[69](69-rollback-api-and-phases.md) |
| `src/vmm/src/persist.rs` | +14 / −3 | `create_snapshot()` 校验「给了 `dirty_bitmap_path` 就必须给 `mem_file_path`」；`snapshot_state_from_file()` 提升为 `pub(crate)` 供回滚读 vmstate | [67](67-dirty-bitmap-sidecar.md)、[69](69-rollback-api-and-phases.md) |
| `src/vmm/src/vmm_config/instance_info.rs` | +5 / −0 | `VmState::Faulted` 及其 `Display` | [73](73-failure-model-faulted-and-seccomp.md) |
| `src/firecracker/src/api_server/parsed_request.rs` | +1 / −0 | `VmmData::Rollback` 的序列化出口 | [69](69-rollback-api-and-phases.md) |
| `src/vmm/tests/integration_tests.rs` | +1 / −0 | 构造 `CreateSnapshotParams` 时补 `dirty_bitmap_path: None` | [67](67-dirty-bitmap-sidecar.md) |

**设备：把快照状态写回活着的设备**

原地回滚不重建设备，所以需要从各设备的 `State` 结构里取出「通用 virtio 那一半」。
这组改动全是访问器与小函数，行数少但文件多。

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `src/vmm/src/devices/virtio/net/device.rs` | +28 / −0 | `Net::rollback_rx_buffers()`：就地清空并按快照计数重建已解析的 RX 描述符缓存；注释说明为什么不能新建 `RxBuffers`（会 `memfd_create`，不在 vmm 过滤器白名单里） | [72](72-rollback-devices.md) |
| `src/vmm/src/devices/virtio/net/persist.rs` | +16 / −3 | `RxBufferState` 三个字段改 `pub(crate)`；`NetState::virtio_state()` 与 `rx_buffers_state()` | [72](72-rollback-devices.md) |
| `src/vmm/src/devices/acpi/vmgenid.rs` | +14 / −0 | `VmGenId::refresh_generation()`：回滚后生成新的 generation ID 写进 guest 内存并通知 guest | [72](72-rollback-devices.md) |
| `src/vmm/src/devices/virtio/persist.rs` | +13 / −0 | `MmioTransport::apply_state()`：把快照里的五个传输层寄存器写回活着的 transport，设备引用与中断线不动 | [72](72-rollback-devices.md) |
| `src/vmm/src/devices/virtio/block/persist.rs` | +12 / −0 | `BlockState::virtio_state()` 返回 `Option`：vhost-user 的状态在后端进程里，原地写回够不着，所以返回 `None` | [72](72-rollback-devices.md) |
| `src/vmm/src/devices/virtio/block/virtio/persist.rs` | +7 / −0 | `VirtioBlockState::virtio_state()` | [72](72-rollback-devices.md) |
| `src/vmm/src/devices/virtio/rng/persist.rs` | +7 / −0 | `EntropyState::virtio_state()` | [72](72-rollback-devices.md) |

**过滤器**

| 文件 | + / − | 改动 | 篇 |
|---|---|---|---|
| `resources/seccomp/aarch64-unknown-linux-musl.json` | +61 / −5 | `vmm` 段补 `pread64`（补齐 2.4 留下的不对称）与四条带参数的 `ioctl` 规则：`KVM_SET_ONE_REG`、`KVM_SET_MP_STATE`、`KVM_ARM_VCPU_INIT`、`KVM_ARM_VCPU_FINALIZE`；另有两条 `getrandom` 的注释整理 | [62](62-aarch64-seccomp-filter.md)、[73](73-failure-model-faulted-and-seccomp.md) |

四条 `ioctl` 规则是回滚时在 vCPU 线程上写回寄存器所必需的；上游的表里只允许恢复路径在
vCPU 线程启动之前使用这些请求号，原地回滚把它们挪到了运行期。

---

## 5. guest 内核这一层

内核这一层没有源码补丁，所以不需要 `diff --stat` 表，一行足以概括：

| 基线 | 产物 | 相对上游同版本 CI config 的差异 | 源码补丁 | 篇 |
|---|---|---|---|---|
| e2b-dev/fc-kernels `v0.0.8`（`b8cea06`） | `configs/x86_64/6.1.158.config`、`configs/arm64/6.1.158.config` | x86_64 共 88 行、arm64 共 21 行（含编译器版本等非功能行） | 无 | [56](56-guest-kernel-requirements-and-e2b-configs.md) |

两点要在升级时记住。

**第一，部署用的内核不是 `v0.0.8`，是 `v0.0.12`（`f371098`），而两者的 config 完全相同。**
用 `git diff --stat b8cea06 f371098 -- configs` 验证，输出为空。这两个 release 之间只改了
`build.sh`、`README.md` 与一个一次性的 GCS 迁移脚本。也就是说，讨论内核**配置**时引用 `v0.0.8`
与引用 `v0.0.12` 等价；讨论内核**产物**时不等价。

**第二，`v0.0.8` 的 arm64 产物是 ELF，不能被 Firecracker 的 aarch64 加载器装载。**
那一版对两个架构都执行 `make vmlinux`，arm64 的 `vmlinux` 是 ELF；Firecracker 的 aarch64
加载器只接受带 PE 头的 `arch/arm64/boot/Image`。改成 `make Image` 是 `v0.0.9`（`7fa4f34`）做的，
提交标题直接写着 arm64 需要 PE 格式。所以在 ARM 上升级内核时，**config 可以从 `v0.0.8` 起算，
构建脚本必须取 `v0.0.9` 以后的**。完整论证与部署文件的格式取证在[第 61 篇](61-guest-kernel-on-arm.md)。

---

## 6. 升级 Firecracker 时的重放清单

把这两层改动搬到一个新的上游版本上，按下面的顺序做。顺序由依赖决定：
后一步引用前一步引入的类型或函数，跳步会让中间状态编译不过。
每一步给出要碰的文件、判断是否完成的依据，以及需要重新判断的取舍。

**第 0 步：确定基线与目标。** 上游发布策略与快照兼容承诺在[第 48 篇](48-release-and-compat-policy.md)：
跨 minor 版本时 vmstate 格式与 `SNAPSHOT_VERSION` 可能变，旧快照读不回来。
先确认目标版本，再看 e2b 分叉是否已有对应分支（`firecracker-v1.13`、`firecracker-v1.14-direct-mem`
说明同一套改动已经重放过一次，可以直接对照而不是从头移植）。

**第 1 步：内存查询三端点（2.1）。** 顺序是 `instance_info.rs` → `vstate/vm.rs` →
`utils/pagemap.rs` 与 `utils/mod.rs` → `lib.rs` → `rpc_interface.rs` → `api_server/*` → swagger。
`InstanceInfo` 加字段会波及所有构造点（`src/firecracker/src/main.rs`、
`src/cpu-template-helper/src/utils/mod.rs`），编译器会一一指出来。
注意 `mincore_bitmap()` 是自由函数不是方法，上游若重构了 `Vm` 的内存区域迭代方式，这里要跟着改。

**第 2 步：可选 memfile（2.3）。** 只有 `vmm_config/snapshot.rs` 一处类型改动加 `persist.rs`
一处条件判断，其余是测试构造点。上游若给 `CreateSnapshotParams` 加了新字段，这一步也是补字段的地方。
重新判断的点：不写 memfile 时 `snapshot_memory_to_file()` 不被调用，
KVM 脏页日志也就不会被读取和清零 —— 这个副作用要确认在新版本上仍然成立。

**第 3 步：uffd 写保护（2.2）。这一步有取舍，必须单独判断。**
它换掉了 `userfaultfd` 依赖，改成 e2b 分叉的 git 分支。三种处理方式：

| 方式 | 做法 | 代价 |
|---|---|---|
| 原样带上 | 保留 e2b 分叉的 crate 与三处写保护代码 | 只能在 x86_64 上构建与运行；在 aarch64 上 `guest_memory_from_uffd()` 会在 `require_features` 或 `register_with_mode` 处失败，因为 arm64 内核没有 `UFFD_FEATURE_WP_ASYNC` 与 `UFFDIO_REGISTER_MODE_WP` |
| 加架构门 | 按分叉自己的 `136ef0e01` 的做法，把三处写保护代码用 `cfg(target_arch = "x86_64")` 包住 | 两个架构共用一份源码，但 aarch64 上脏页判据仍然退化，且多了一类只在一个架构上编译的代码 |
| 整体跳过 | 停在不带写保护的提交上（ARM 适配版的选择） | 依赖保持 crates.io 版本，源码干净；`/memory/dirty` 退化成「常驻即脏」，脏页要另找来源 |

选哪一种取决于目标架构。只上 x86_64 就选第一种；要同时维护两个架构，第二种比第三种更容易跟上游对齐 ——
第三种意味着每次升级都要再判断一次「停在哪个提交」。三者的比较在[第 57 篇](57-which-fork-commit-and-uffd-wp.md)。
若选第三种，**后面第 6 步的 HDBSS 就是必需的而不是可选的**。

**第 4 步：seccomp 两张表（2.4）。** 上游每次改动设备或依赖都可能动这两张表，
不要整文件覆盖，只补 `mincore` 与 `pread64` 两条规则，且两个架构都要补 ——
e2b 定制版漏掉 aarch64 的 `pread64` 是因为它只在 x86_64 上构建，新的重放没有这个前提。
表的结构与安装时机在[第 42 篇](42-seccomp.md)。

**第 5 步：构建与发布脚本（2.5）。** `scripts/build.sh` 的产物路径**从一开始就写成按 `uname -m`
自适应**，不要重复 4.1 那次修复。版本名格式 `v<swagger 版本>_<7 位哈希>` 要与 orchestrator
消费的常量对齐（[第 63 篇](63-integration-with-e2b-infra.md)）。
注意 swagger 的 `info.version` 字段在分叉里没有随新端点更新，只有哈希能标识实际的 API 面。

**第 6 步：aarch64 能跑起来（4.1）。** 先只做构建与运行，不碰功能。
`resize_fdtable()` 那一段不要照抄注释掉的写法，改成按 `ResizeFdTableError` 的变体分别处理；
上游本来就把 `GetRlimit` 与 `Dup2` 当作非致命错误。
这一步的验收是 aarch64 上能启动 microVM 并做一次快照恢复（[第 58 篇](58-building-and-running-on-aarch64.md)）。

**第 7 步：HDBSS（4.2）。** 顺序是 `arch/aarch64/vm.rs` 的 `enable_hdbss()` →
`vstate/vm.rs` 的 `DirtyTrackingBackend` 与 `setup_dirty_tracking()` → `builder.rs` 两个调用点 →
`instance_info.rs` 的 `dirty_tracking` 字段。两个硬编码常量
（`KVM_CAP_ARM_HW_DIRTY_STATE_TRACK` = 502 与 openEuler 的 `KVM_ENABLE_CAP` 请求号）
要在目标宿主内核上重新核对；换发行版内核时它们可能不同。
`builder.rs` 的插入点必须在 `register_memory_regions()` 之后。

**第 8 步：位图 sidecar（4.3 的快照产物组）。** `vstate/memory.rs` 的序列化与反序列化 →
`vstate/vm.rs` 的 `snapshot_memory_to_file()` 签名 → `persist.rs` 的组合校验 →
`vmm_config/snapshot.rs` 的参数 → `api_server/request/snapshot.rs` 的路由 → swagger。
FCDB 格式带 magic 与版本号，跨版本升级时若改了页大小或位图打包方式，要同时抬版本号，
否则旧 sidecar 会被静默误读。

**第 9 步：设备侧的访问器（4.3 的设备组）。** 七个文件都是小改动，但**必须在写 `rollback.rs` 之前做完**，
否则回滚代码没有类型可用。上游每加一种 virtio 设备，这里就要多一个 `virtio_state()` 访问器；
不支持的设备（vhost-user block）返回 `None` 并在回滚时明确拒绝，不要静默跳过。

**第 10 步：回滚主体（4.3 的核心组）。** `vstate/vcpu.rs` 的新事件与响应 →
两个架构的 `restore_state_in_place()` → `lib.rs` 的 `restore_vcpu_states_in_place()` 与
`Faulted` 状态处理 → `rollback.rs` → `rpc_interface.rs`。
提交点的划分与失败后进入 `Faulted` 的判定是这一步的核心，不是可以简化的实现细节
（[第 69 篇](69-rollback-api-and-phases.md)、[第 73 篇](73-failure-model-faulted-and-seccomp.md)）。

**第 11 步：aarch64 seccomp 补齐（4.3 的过滤器组）。** 四条带参数的 `ioctl` 规则依赖
第 10 步实际用到的请求号；上游若改了恢复序列，要按新序列重新抓一遍实际发生的 `ioctl`，
不要照抄旧的四个常量。这一步放在最后，因为在此之前无法确定需要放行哪些请求号。

**第 12 步：guest 内核（第 5 节）。** config 可以沿用；构建脚本在 arm64 上必须产出 PE 格式的 `Image`。
升级内核版本时先确认新版本的 config 里第 5 节提到的那几类选项仍然开着。

**不需要重放的**：2.6 的三个测试文件改动来自上游维护分支，升级到新上游时它们已经在里面了；
删除依赖检查工作流这件事要不要重做，取决于第 3 步是否仍然引入 git 来源的依赖。

---

## 7. 小结

- e2b 定制版对上游的改动是 34 个文件、+1042 / −64 行，其中源码 18 个文件；
  按代码量不到上游的 1%，但集中在内存与快照这两条主线上。
- `src/vmm/src/vstate/vm.rs` 是唯一被两层都大幅改过的文件（e2b +192，ARM 再 +139），
  升级时冲突最可能出现在这里。
- `54a1c1a` 与 `a41d3fb` 之间只有五个文件、+57 / −25，源码上的实质差别只有 uffd 写保护一件事。
- ARM 适配版对 `firecracker/` 目录的改动是 28 个文件、+1679 / −36，其中 checkpoint 扩展占 +1505；
  `rollback.rs` 656 行与 `vstate/memory.rs` +276 是两个重心。
- 设备侧的改动文件多而行数少：七个文件一共 +97 行，全是访问器与就地写回的小函数，
  上游每加一种 virtio 设备都要跟着加一个。
- 内核这一层没有源码补丁；`v0.0.8` 与 `v0.0.12` 的 config 一字不差，
  但 `v0.0.8` 的 arm64 产物是 ELF，`v0.0.9` 才改成 PE。
- 重放的顺序由依赖决定，只有第 3 步（uffd 写保护）是真正的取舍点，
  它决定了第 7 步的 HDBSS 是可选还是必需。
- 三层改动里有两处明确的技术债：`resize_fdtable()` 被整段注释掉，
  以及 e2b 定制版两张 seccomp 表的不对称。重放时都应当修掉而不是照抄。

---

## 延伸阅读 / 下一篇

- 下一篇：[第 79 篇 · 阅读上游代码的方法与常见问题](79-reading-upstream-code.md) —— 拿到表之后怎么读具体的文件。
- [第 75 篇 · 代码地图](75-code-map.md) —— 同样的文件清单，但按 crate 与模块组织，包含没有被改过的部分。
- [第 76 篇 · API 端点总表](76-api-reference.md) —— 本篇里那些新增端点的请求与响应。
- [第 01 篇 · 源流与仓库地图](01-lineage-and-repo-map.md) —— 三层基线各自从哪里来。
- [第 48 篇 · 发布策略、版本与兼容承诺](48-release-and-compat-policy.md) —— 升级时快照兼容性的边界。
- e2b 手册（`../e2b-infra/`）讲 orchestrator 怎么消费这些端点与版本名。
