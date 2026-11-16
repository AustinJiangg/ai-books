# 附录 A｜Firecracker 改动地图

> **本附录的用途**：正文按“做什么、为什么”讲 Firecracker 这一侧，本附录按“改了哪些文件”列一遍，方便对照源码。路径以 Firecracker 源码目录为根。e2b-infra 里只有编译好的 `firecracker.arm`，这份源码没有随它发布，所以这里只给路径和函数名。

---

## 一、基线

本方案的 Firecracker 不是直接从上游改的，而是在 E2B 自己的 Firecracker 分支 `firecracker-v1.12-direct-mem` 上改的，Cargo 里的版本号是 `1.12.1`。`firecracker --version` 报的就是这个号，它说明不了二进制里有没有下面这些改动。

E2B 分支在上游之上已经加过一些东西，它们**不属于本方案**，但正文和其他几本书会用到：

| E2B 分支已有的 | 在哪 | 用途 |
|---|---|---|
| 打快照时 `mem_file_path` 可选 | `src/vmm/src/vmm_config/snapshot.rs` | 不传就只写 snapfile，内存由 orchestrator 自己导出 |
| `GET /memory/mappings` | `src/vmm/src/rpc_interface.rs` | 客户机内存每一段在 Firecracker 进程里的地址 |
| `GET /memory/dirty` | `src/vmm/src/lib.rs` 的 `get_dirty_memory`、`src/vmm/src/utils/pagemap.rs` | 原生 pause 的脏页判据：在内存里且没有 uffd 写保护（第 8 篇第六节） |
| `GET /memory` | `src/vmm/src/rpc_interface.rs` | 哪些页在内存里、哪些全是零 |

## 二、本方案的改动

相对 E2B 分支，改动涉及 44 个文件，新增约 4900 行（含单元测试），其中新文件 `src/vmm/src/rollback.rs` 占 1676 行。按功能分组：

### 1. 写快照时顺带写位图（扩展一）

| 文件 | 改了什么 |
|---|---|
| `src/vmm/src/vmm_config/snapshot.rs` | `CreateSnapshotParams` 加可选字段 `dirty_bitmap_path` |
| `src/vmm/src/vstate/vm.rs` | `snapshot_memory_to_file` 多一个位图路径参数；差分取 `dump_dirty` 的返回值，全量构造全 1；写完内存文件再写位图；只 `flush`，不 `sync_all` |
| `src/vmm/src/vstate/memory.rs` | `dump_dirty` 在写的同时记下写了哪些页并返回；新增 FCDB 格式 `serialize_dirty_bitmap` / `deserialize_dirty_bitmap` |
| `src/vmm/src/persist.rs` | 有位图没内存文件就拒绝（`DirtyBitmapWithoutMemFile`）；`snapfile_must_be_durable`：带内存文件的不 fsync snapfile，原生 pause 照旧 fsync |

### 2. 导出活跃脏页位图（扩展二）

| 文件 | 改了什么 |
|---|---|
| `src/vmm/src/rollback.rs` | `save_dirty_bitmap`：取 KVM 位图、并进备份位图、写 FCDB 文件 |
| `src/vmm/src/vmm_config/snapshot.rs` | `SaveDirtyBitmapParams`（只有一个 `path`） |

### 3. 原地回滚（扩展三）

| 文件 | 改了什么 |
|---|---|
| `src/vmm/src/rollback.rs` | 九个阶段 `rollback_snapshot_inner`；设备组成校验 `validate_topology`；静默 `quiesce_devices`；覆盖校验 `validate_mem_file_coverage`；设备写回 `apply_device_states`、`apply_net_rx_cache`、`apply_net_tap_offload`；串口中断线 `clear_serial_gic_line`；队列诊断 `log_queue_diagnostics`；错误分级 `RollbackError::faults_vm` |
| `src/vmm/src/vstate/memory.rs` | `restore_dirty`（合批 `pread` 写回）；按字遍历位图的 `for_each_set_bit`、`or_bits_into` |
| `src/vmm/src/lib.rs` | `restore_vcpu_states_in_place`（把恢复派给各 vCPU 线程）；`reset_serial_for_rollback`；暂停、恢复前检查 `Faulted` |
| `src/vmm/src/vstate/vcpu.rs` | 新的 vCPU 事件“原地恢复状态”；vCPU 停下之前先收尾挂起的设备访问 |
| `src/vmm/src/arch/aarch64/vcpu.rs` | `restore_state_in_place`、`drain_pending_exit`、`verify_restored_core_regs` |
| `src/vmm/src/arch/aarch64/gic/` 下几个文件 | `restore_state_absolute`：使能、等待、正在处理三类寄存器绝对写回（分发器和重分发器）；清串口那条中断线的“正在处理 / 等待”位。GICv2 退回普通恢复，因为回滚路径从没在 GICv2 上跑过 |
| `src/vmm/src/devices/legacy/serial.rs` | `reset_for_rollback`：清 IIR、打开两类中断、写一个字节触发一次中断，处理 DLAB |
| `src/vmm/src/devices/virtio/net/device.rs` | `rollback_rx_buffers`：原地清空并重建接收缓存 |
| `src/vmm/src/devices/virtio/` 下的 `persist.rs` 等 | 让回滚能取到快照里的 virtio 通用状态、网卡接收缓存计数；把传输层寄存器写回活着的对象（`MmioTransport::apply_state`）；vhost-user 磁盘明确不支持 |
| `src/vmm/src/devices/acpi/vmgenid.rs` | `refresh_generation`：写新代号并通知客户机 |
| `src/vmm/src/vmm_config/instance_info.rs` | 新状态 `Faulted` |
| `src/vmm/src/arch/x86_64/vcpu.rs` | x86 上的 `restore_state_in_place` 直接复用普通恢复。x86 只保证能编译，回滚没有在 x86 上验证过 |

### 4. HDBSS 脏页跟踪

| 文件 | 改了什么 |
|---|---|
| `src/vmm/src/vstate/vm.rs` | `setup_dirty_tracking`：决定后端（`hdbss` / `kvm-wp` / `off`），读 `FC_HDBSS_ORDER`、`FC_HDBSS_REQUIRED` |
| `src/vmm/src/arch/aarch64/vm.rs` | `enable_hdbss`：`KVM_ENABLE_CAP`，能力号 502 |
| `src/vmm/src/builder.rs` | 冷启动和加载快照两条路径都在注册内存之后调 `setup_dirty_tracking` |
| `src/vmm/src/vmm_config/instance_info.rs`、`src/vmm/src/lib.rs` | 实例信息里的 `dirty_tracking` 字段 |

### 5. HTTP 接口

| 文件 | 改了什么 |
|---|---|
| `src/firecracker/src/api_server/request/snapshot.rs`、`parsed_request.rs` | 路由 `PUT /snapshot/rollback`、`PUT /snapshot/save-dirty-bitmap`；回滚失败按 `faults_vm` 分 400 / 500，500 的响应体带 `"fault": true` |
| `src/vmm/src/rpc_interface.rs` | 两个新动作；`allowed_while_faulted`：虚机 `Faulted` 后只放行查询类请求 |
| `src/firecracker/swagger/firecracker.yaml` | 接口文档 |

### 6. 系统调用白名单

`resources/seccomp/aarch64-unknown-linux-musl.json`（x86 的那份也同步改了）：

| 线程 | 新放行 | 为什么 |
|---|---|---|
| vCPU 线程 | `KVM_SET_ONE_REG`、`KVM_SET_MP_STATE`、`KVM_ARM_VCPU_INIT`、`KVM_ARM_VCPU_FINALIZE` | 回滚时在 vCPU 线程上复位、写寄存器 |
| 主线程 | `TUNSETOFFLOAD` | 回滚后按写回的网卡特性重设 tap 的 offload |
| 主线程 | `pread64` | `GET /memory/dirty` 按位置读 `/proc/self/pagemap`，缺了它这个接口会触发白名单、虚机被关掉 |

### 7. 观测

| 文件 | 改了什么 |
|---|---|
| `src/vmm/src/logger/metrics.rs` | 回滚、导出位图的耗时；暂停和回滚时收尾了几次挂起的设备访问、收尾失败几次、读回核对不一致几次 |
| `src/vmm/src/vmm_config/snapshot.rs` | 回滚的返回值：`restored_pages`、`restored_bytes`、`timings_us`、`vcpu_counters` |

### 8. 测试与构建

| 文件 | 改了什么 |
|---|---|
| `src/vmm/Cargo.toml`、`src/firecracker/Cargo.toml` | 测试专用特性 `rollback-fault-inject`，交付的二进制不带 |
| 各文件的 `mod tests` | 位图格式、按字遍历、覆盖校验、错误分级与 HTTP 状态码、GIC 绝对写回、串口复位、fsync 判定等单元测试 |
| `src/firecracker/src/main.rs` | 启动时扩容文件描述符表的那一段被注释掉了（openEuler 24.03 上会崩溃），与回滚无关，属于 ARM 部署适配 |

## 三、正文里在哪讲

| 改动 | 正文 |
|---|---|
| 三处扩展、九个阶段、FCDB、设备组成校验 | 第 11 篇 |
| HDBSS 启用、两份位图、`GET /memory/dirty` 的判据 | 第 8 篇 |
| 网卡接收缓存、队列诊断日志 | 第 12 篇 |
| 撕裂与 `Faulted` | 第 11、13 篇 |
| 原生 pause 用 `save-dirty-bitmap` 做精确增量 | 第 15 篇 |
| 不 fsync、按字跳零、合批 `pread` | 第 11、18 篇 |
