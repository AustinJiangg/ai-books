# 76 · API 端点总表

> 本篇把三层代码基线的全部 HTTP 端点收成一张可查的表：方法、路径、在 microVM 生命周期的哪一段被接受、
> 落到哪个 `VmmAction`、由哪一篇展开，以及请求与响应的 JSON 骨架。
> 表的依据是 `parsed_request.rs`、`api_server/request/*.rs` 与 `rpc_interface.rs` 三处代码，不是 swagger；
> swagger 与代码不一致的地方在最后一节逐条列出。
>
> **读者**：写调用方的后端工程师、需要核对接口契约的系统工程师。
> **预备**：[第 08 篇 · API server](08-api-server.md)、[第 09 篇 · rpc_interface](09-rpc-interface.md)。
> **代码**：`src/firecracker/src/api_server/parsed_request.rs`、`src/firecracker/src/api_server/request/`、
> `src/vmm/src/rpc_interface.rs`、`src/vmm/src/vmm_config/`、`src/firecracker/swagger/firecracker.yaml`

---

## 0. 本篇要回答的问题

1. 上游 v1.12.1 一共有多少个端点，每个端点在 preboot 段和 runtime 段分别是被执行还是被拒绝？
2. 一个路径怎么变成一个 `VmmAction`，路径里的第二段（`/balloon/statistics`、`/mmds/config`、`/snapshot/create`）在哪里被分流？
3. 每个端点的请求体与响应体有哪些字段，哪些字段有默认值，哪些字段拒绝未知键？
4. e2b 定制版加的三个 GET 与 ARM 适配版加的两个 PUT 在这张表里处在什么位置，它们的前置条件是什么？
5. API 实际会返回哪些 HTTP 状态码？
6. 仓库里的 swagger 有哪几处与代码对不上，调用方应当以哪一边为准？

---

## 1. 怎么读这张表

### 1.1 路径到动作的两级分派

所有请求先进 `parsed_request.rs` 的 `impl TryFrom<&Request> for ParsedRequest`。它把 URI 去掉开头的 `/` 之后按 `/` 切开，
只用**第一段**加上 HTTP 方法加上「有没有 body」做匹配；第二段（如果有）作为 `Option<&str>` 传给该资源的解析函数，
由解析函数自己决定接受什么。所以 `/balloon/statistics`、`/mmds/config`、`/snapshot/create`、`/drives/{drive_id}`
这四类「二级路径」的合法值不在总的 match 里，而在 `request/balloon.rs`、`request/mmds.rs`、`request/snapshot.rs`、
`request/drive.rs` 各自的函数里。第二段取到不认识的值时返回 400，不是 404。

第二级是 `rpc_interface.rs`。同一个 `VmmAction` 被送到两个控制器之一：microVM 启动之前是
`PrebootApiController::handle_preboot_request()`，启动之后是 `RuntimeApiController::handle_request()`。
两个函数各自有一个「不支持」的分支，分别返回 `VmmActionError::OperationNotSupportedPreBoot` 与
`OperationNotSupportedPostBoot`。下表的「Preboot」「Runtime」两列写的就是这两个 match 的结果：
● 表示该段执行，○ 表示该段返回上述错误（HTTP 400）。

### 1.2 状态码

响应只在两个地方生成。`ParsedRequest::convert_to_response()` 把成功结果映射成 200（有 body）或 204（`VmmData::Empty`），
把错误映射成 400，唯一的例外是 `VmmActionError::MmdsLimitExceeded`，它映射成 413。解析阶段的
`RequestError` 一律走 400（`RequestError::Generic` 携带的状态码在 v1.12.1 里也只被用作 400）。
因此 Firecracker 自身产生的状态码集合是 `{200, 204, 400, 413}`；再加上 `micro_http` 在 HTTP 层面产生的
100（`Expect: 100-continue`）与 500（连接层内部错误），没有 404，也没有 405。
路径不认识、方法不认识、二级路径不认识，全部是 400。

---

## 2. 上游 v1.12.1 端点总表

「篇」列指向展开讲这个端点背后机制的篇目。

| 方法 · 路径 | Preboot | Runtime | `VmmAction` | 篇 |
|---|:--:|:--:|---|---|
| `GET /` | ● | ● | `GetVmInstanceInfo` | [09](09-rpc-interface.md) |
| `GET /version` | ● | ● | `GetVmmVersion` | [08](08-api-server.md) |
| `GET /vm/config` | ● | ● | `GetFullVmConfig` | [10](10-vm-resources-and-config.md) |
| `GET /machine-config` | ● | ● | `GetVmMachineConfig` | [10](10-vm-resources-and-config.md) |
| `GET /balloon` | ● | ● | `GetBalloonConfig` | [34](34-balloon.md) |
| `GET /balloon/statistics` | ○ | ● | `GetBalloonStats` | [34](34-balloon.md) |
| `GET /mmds` | ● | ● | `GetMMDS` | [32](32-mmds.md) |
| `PUT /actions` `InstanceStart` | ● | ○ | `StartMicroVm` | [11](11-builder.md) |
| `PUT /actions` `FlushMetrics` | ○ | ● | `FlushMetrics` | [44](44-logging-and-metrics.md) |
| `PUT /actions` `SendCtrlAltDel` | ○ | ● | `SendCtrlAltDel`（仅 x86_64） | [24](24-legacy-devices.md) |
| `PUT /boot-source` | ● | ○ | `ConfigureBootSource` | [10](10-vm-resources-and-config.md) |
| `PUT /machine-config` | ● | ○ | `UpdateMachineConfiguration` | [10](10-vm-resources-and-config.md) |
| `PATCH /machine-config` | ● | ○ | `UpdateMachineConfiguration` | [10](10-vm-resources-and-config.md) |
| `PUT /cpu-config` | ● | ○ | `PutCpuConfiguration` | [20](20-cpu-templates.md) |
| `PUT /drives/{drive_id}` | ● | ○ | `InsertBlockDevice` | [27](27-virtio-block.md) |
| `PATCH /drives/{drive_id}` | ○ | ● | `UpdateBlockDevice` | [27](27-virtio-block.md) |
| `PUT /network-interfaces/{iface_id}` | ● | ○ | `InsertNetworkDevice` | [30](30-virtio-net.md) |
| `PATCH /network-interfaces/{iface_id}` | ○ | ● | `UpdateNetworkInterface` | [30](30-virtio-net.md) |
| `PUT /vsock` | ● | ○ | `SetVsockDevice` | [33](33-vsock.md) |
| `PUT /entropy` | ● | ○ | `SetEntropyDevice` | [35](35-entropy-vmgenid-rate-limiter.md) |
| `PUT /balloon` | ● | ○ | `SetBalloonDevice` | [34](34-balloon.md) |
| `PATCH /balloon` | ○ | ● | `UpdateBalloon` | [34](34-balloon.md) |
| `PATCH /balloon/statistics` | ○ | ● | `UpdateBalloonStatistics` | [34](34-balloon.md) |
| `PUT /mmds` | ● | ● | `PutMMDS` | [32](32-mmds.md) |
| `PATCH /mmds` | ● | ● | `PatchMMDS` | [32](32-mmds.md) |
| `PUT /mmds/config` | ● | ○ | `SetMmdsConfiguration` | [32](32-mmds.md) |
| `PUT /logger` | ● | ○ | `ConfigureLogger` | [44](44-logging-and-metrics.md) |
| `PUT /metrics` | ● | ○ | `ConfigureMetrics` | [44](44-logging-and-metrics.md) |
| `PUT /snapshot/create` | ○ | ● | `CreateSnapshot` | [37](37-snapshot-create.md) |
| `PUT /snapshot/load` | ● | ○ | `LoadSnapshot` | [38](38-snapshot-load.md) |
| `PATCH /vm` `Paused` | ○ | ● | `Pause` | [15](15-vcpu-threads-and-state-machine.md) |
| `PATCH /vm` `Resumed` | ○ | ● | `Resume` | [15](15-vcpu-threads-and-state-machine.md) |

三点需要注意。

第一，`PUT /actions` 与 `PATCH /vm` 是「一个路径多个动作」：路径本身不区分语义，body 里的 `action_type` 或 `state`
决定生成哪个 `VmmAction`（`request/actions.rs` 的 `parse_put_actions()`、`request/snapshot.rs` 的 `parse_patch_vm_state()`）。
表里按动作分行，因为它们的允许段不同。

第二，`SendCtrlAltDel` 在 aarch64 上根本不进入 `VmmAction`：`parse_put_actions()` 里有 `#[cfg(target_arch = "aarch64")]`
分支直接返回 400，错误文本是 `SendCtrlAltDel does not supported on aarch64.`。`VmmAction::SendCtrlAltDel`
这个变体本身也带 `#[cfg(target_arch = "x86_64")]`。

第三，`ConfigureLogger` 与 `ConfigureMetrics` 只在 preboot 段允许。启动之后想换日志文件或 metrics 文件是做不到的；
runtime 段唯一与这两者相关的动作是 `FlushMetrics`。

### 2.1 `GET /vm` 不是端点

总 match 里 `vm` 这一项写成 `(Method::Get, "vm", None) if path_tokens.next() == Some("config")`。
guard 不成立时这条 arm 不匹配，请求落到最后的兜底 arm，返回 `RequestError::InvalidPathMethod`，
也就是 400。所以只有 `GET /vm/config` 存在，`GET /vm` 不存在。`PATCH /vm` 则是独立的一条 arm，与 `/vm/config` 无关。

---

## 3. 请求与响应的 JSON 骨架（上游 v1.12.1）

字段名与可选性以 `src/vmm/src/vmm_config/` 下的结构体为准。标注 `deny_unknown_fields` 的结构体，
请求里带一个多余的键就是 400。

### 3.1 只读端点

`GET /`（`InstanceInfo`，全部字段必出）：

```json
{
  "id": "anonymous-instance",
  "state": "Not started",
  "vmm_version": "1.12.1",
  "app_name": "Firecracker"
}
```

`state` 是 `VmState` 的 `Display` 输出，三个取值：`"Not started"`、`"Running"`、`"Paused"`。

`GET /version`：响应不是一个结构体，而是 `convert_to_response()` 现场拼的对象：

```json
{ "firecracker_version": "1.12.1" }
```

`GET /machine-config` 返回 `MachineConfig`（字段见[第 77 篇](77-config-cli-env-metrics-reference.md)）。
`GET /vm/config` 返回 `VmmConfig`，键名是 kebab-case（`boot-source`、`machine-config`、`network-interfaces`、
`mmds-config`、`cpu-config`、`drives`、`balloon`、`vsock`、`entropy`、`logger`、`metrics`），
与 `--config-file` 接受的单文件格式同构。

`GET /balloon` 返回 `BalloonDeviceConfig`；`GET /balloon/statistics` 返回 `BalloonStats`。
`GET /mmds` 返回数据存储的当前内容，`Value::Null` 被特判成 `{}`。

### 3.2 设备与机器配置

`PUT /boot-source`（`BootSourceConfig`）：

```json
{
  "kernel_image_path": "/path/vmlinux",
  "initrd_path": null,
  "boot_args": "console=ttyS0 reboot=k panic=1"
}
```

`PUT /machine-config`（`MachineConfig`）与 `PATCH /machine-config`（`MachineConfigUpdate`，全字段 `Option`）：

```json
{
  "vcpu_count": 2,
  "mem_size_mib": 1024,
  "smt": false,
  "cpu_template": "None",
  "track_dirty_pages": false,
  "huge_pages": "None"
}
```

`PUT /drives/{drive_id}`（`BlockDeviceConfig`）。路径里的 `drive_id` 必须与 body 里的 `drive_id` 相等，
否则 400（`parse_put_drive()` 显式比较）：

```json
{
  "drive_id": "rootfs",
  "path_on_host": "/path/rootfs.ext4",
  "is_root_device": true,
  "is_read_only": false,
  "partuuid": null,
  "cache_type": "Unsafe",
  "io_engine": "Sync",
  "rate_limiter": null,
  "socket": null
}
```

`path_on_host` 与 `socket` 二选一：给 `socket` 就是 vhost-user 块设备（[第 29 篇](29-vhost-user-block.md)）。
`cache_type` 取 `Unsafe`（默认）或 `Writeback`；`io_engine` 取 `Sync`（默认）或 `Async`（[第 28 篇](28-io-uring-engine.md)）。

`PATCH /drives/{drive_id}`（`BlockDeviceUpdateConfig`，`deny_unknown_fields`）只有三个字段：
`drive_id`、`path_on_host`、`rate_limiter`。

`PUT /network-interfaces/{iface_id}`（`NetworkInterfaceConfig`）：

```json
{
  "iface_id": "eth0",
  "host_dev_name": "tap0",
  "guest_mac": "AA:FC:00:00:00:01",
  "rx_rate_limiter": null,
  "tx_rate_limiter": null
}
```

`PATCH /network-interfaces/{iface_id}`（`NetworkInterfaceUpdateConfig`）只接受 `iface_id`、`rx_rate_limiter`、`tx_rate_limiter`。

速率限制器（`RateLimiterConfig`，[第 35 篇](35-entropy-vmgenid-rate-limiter.md)）在块设备、网络设备、entropy 设备上是同一个形状：

```json
{
  "bandwidth": { "size": 0, "one_time_burst": null, "refill_time": 0 },
  "ops":       { "size": 0, "one_time_burst": null, "refill_time": 0 }
}
```

`PUT /vsock`（`VsockDeviceConfig`）：`{"guest_cid": 3, "uds_path": "/path/v.sock"}`；
`vsock_id` 字段仍被接受但已废弃，出现时响应带 deprecation 提示并计一次 `deprecated_api.deprecated_http_api_calls`。

`PUT /entropy`（`EntropyDeviceConfig`）：`{"rate_limiter": null}`，空对象 `{}` 合法。

`PUT /balloon`（`BalloonDeviceConfig`）：`{"amount_mib": 0, "deflate_on_oom": false, "stats_polling_interval_s": 0}`；
`PATCH /balloon` 只有 `amount_mib`，`PATCH /balloon/statistics` 只有 `stats_polling_interval_s`。

`PUT /cpu-config` 的 body 是一份自定义 CPU 模板，形状按架构分（x86_64 的 `cpuid_modifiers` / `msr_modifiers`，
aarch64 的 `reg_modifiers`），见[第 20 篇](20-cpu-templates.md)、[第 21 篇](21-x86-64-cpuid-msr-normalization.md)、
[第 22 篇](22-aarch64-templates-and-helper.md)。

### 3.3 控制面与 MMDS

`PUT /actions`（`ActionBody`，`deny_unknown_fields`）：`{"action_type": "InstanceStart"}`，
另外两个取值是 `FlushMetrics`、`SendCtrlAltDel`。

`PATCH /vm`（`Vm`，`deny_unknown_fields`）：`{"state": "Paused"}` 或 `{"state": "Resumed"}`。

`PUT /logger`（`LoggerConfig`，全字段 `Option`）：

```json
{ "log_path": "/path/fc.log", "level": "Info", "show_level": false,
  "show_log_origin": false, "module": null }
```

`PUT /metrics`（`MetricsConfig`）：`{"metrics_path": "/path/fc-metrics"}`。

`PUT /mmds/config`（`MmdsConfig`）：

```json
{ "version": "V1", "network_interfaces": ["eth0"], "ipv4_address": "169.254.169.254" }
```

`PUT /mmds` 与 `PATCH /mmds` 的 body 是任意 JSON 对象，写进数据存储。超出 `--mmds-size-limit` 时
返回 413，是全 API 里唯一的 413 来源。

### 3.4 快照

`PUT /snapshot/create`（`CreateSnapshotParams`，`deny_unknown_fields`）：

```json
{ "snapshot_type": "Full", "snapshot_path": "/path/vmstate", "mem_file_path": "/path/memfile" }
```

`snapshot_type` 缺省为 `Full`；上游两个路径字段都必填。创建快照要求 microVM 处于 `Paused`；
`Diff` 且 `track_dirty_pages` 为 false 时返回 `VmmActionError::NotSupported`（HTTP 400）。

`PUT /snapshot/load`（`LoadSnapshotConfig`，`deny_unknown_fields`）：

```json
{
  "snapshot_path": "/path/vmstate",
  "mem_backend": { "backend_path": "/path/memfile", "backend_type": "File" },
  "enable_diff_snapshots": false,
  "resume_vm": false,
  "network_overrides": []
}
```

`backend_type` 取 `File` 或 `Uffd`（[第 39 篇](39-uffd-backend.md)）。旧字段 `mem_file_path` 仍被接受，
但与 `mem_backend` 互斥：两个都给返回「too many fields」，两个都不给返回「missing field」，
只给 `mem_file_path` 时内部合成一个 `backend_type: "File"` 的 `MemBackendConfig` 并附 deprecation 提示。
`network_overrides` 的元素是 `{"iface_id": "eth0", "host_dev_name": "tap1"}`。

以上四个快照路径之外的第二段（例如 `/snapshot/foo`）返回 400；`PUT /snapshot` 不带第二段也返回 400，
错误文本是 `Missing snapshot operation type.`。

---

## 4. e2b 定制版新增的三个 GET

e2b 定制版在 `parsed_request.rs` 里加了一条 `(Method::Get, "memory", None)` 的 arm，
第二段由 `request/memory.rs` 分流。三个端点都是 runtime 专属：preboot 控制器把
`GetMemoryMappings | GetMemory | GetMemoryDirty` 一并归入 `OperationNotSupportedPreBoot`。

| 方法 · 路径 | Preboot | Runtime | `VmmAction` | 额外前置条件 | 篇 |
|---|:--:|:--:|---|---|---|
| `GET /memory/mappings` | ○ | ● | `GetMemoryMappings` | 无 | [50](50-memory-mappings-api.md) |
| `GET /memory` | ○ | ● | `GetMemory` | 无 | [51](51-memory-resident-empty-api.md) |
| `GET /memory/dirty` | ○ | ● | `GetMemoryDirty` | 必须 `Paused` | [52](52-memory-dirty-api.md) |

`GET /memory/mappings` 返回 `MemoryMappingsResponse`：

```json
{ "mappings": [
    { "base_host_virt_addr": 140234000000000, "size": 134217728,
      "offset": 0, "page_size": 4096 }
] }
```

`GET /memory` 返回 `MemoryResponse`，两张位图都是 `u64` 数组，`empty` 是 `resident` 的子集：

```json
{ "resident": [18446744073709551615, 0], "empty": [0, 0] }
```

`GET /memory/dirty` 返回 `MemoryDirty`：`{"bitmap": [0, 0]}`。
它在 `RuntimeApiController::get_dirty_memory_info()` 里先检查 `instance_info.state != VmState::Paused`，
不满足就返回新增的 `VmmActionError::OperationNotSupportedWhileRunning`（HTTP 仍是 400）。
另外两个端点没有这个检查。

e2b 定制版还改了两处既有契约：

- `CreateSnapshotParams::mem_file_path` 由 `PathBuf` 变成 `Option<PathBuf>`，不给就不写内存文件
  （[第 54 篇](54-optional-memfile-snapshot.md)）。
- `InstanceInfo` 多了一个 `memory_regions: Option<Vec<GuestMemoryRegionMapping>>` 字段，于是
  `GET /` 的响应多出一个键。三处构造点都填 `None`，序列化出来就是 `"memory_regions": null`
  （[第 50 篇](50-memory-mappings-api.md)）。

三个端点共用 `METRICS.get_api_requests.instance_info_count` 这一个计数器，与 `GET /` 混在一起，
从 metrics 分不出调用来源（[第 44 篇](44-logging-and-metrics.md)）。

---

## 5. ARM 适配版新增的两个 PUT

ARM 适配版在 `request/snapshot.rs` 的 `parse_put_snapshot()` 里加了 `rollback` 与 `save-dirty-bitmap`
两个第二段，两者都只在 runtime 段允许。

| 方法 · 路径 | Preboot | Runtime | `VmmAction` | 额外前置条件 | 篇 |
|---|:--:|:--:|---|---|---|
| `PUT /snapshot/rollback` | ○ | ● | `RollbackSnapshot` | `Paused`；拒绝 `Faulted` | [69](69-rollback-api-and-phases.md) |
| `PUT /snapshot/save-dirty-bitmap` | ○ | ● | `SaveDirtyBitmap` | 见[第 68 篇](68-save-dirty-bitmap-api.md) | [68](68-save-dirty-bitmap-api.md) |

`PUT /snapshot/rollback`（`RollbackSnapshotParams`，`deny_unknown_fields`）：

```json
{
  "snapshot_path": "/path/vmstate",
  "mem_file_path": "/path/memfile",
  "revert_bitmap_path": "/path/cumulative.fcdb",
  "resume_vm": false
}
```

`snapshot_path` 与 `mem_file_path` 必填，另两个字段有 `#[serde(default)]`。成功返回 200 与 `RollbackResponse`：

```json
{
  "restored_pages": 12345,
  "restored_bytes": 50565120,
  "timings_us": { "validate": 0, "quiesce": 0, "memory": 0,
                  "vcpus": 0, "gic": 0, "devices": 0, "total": 0 }
}
```

回滚的所有错误都是 HTTP 400（`VmmActionError::RollbackSnapshot`）。越过提交点的失败会把
`instance_info.state` 置为新增的 `VmState::Faulted`，此后 `GET /` 的 `state` 显示 `"Faulted"`，
pause / resume / create 被拒（[第 73 篇](73-failure-model-faulted-and-seccomp.md)）。

`PUT /snapshot/save-dirty-bitmap`（`SaveDirtyBitmapParams`，`deny_unknown_fields`）只有一个字段，
成功返回 204：

```json
{ "path": "/path/epoch.fcdb" }
```

ARM 适配版对既有契约的两处扩展：

- `CreateSnapshotParams` 多了 `dirty_bitmap_path: Option<PathBuf>`，要求与 `mem_file_path` 同时给出，
  作用是把本次快照写入内存文件的页记成一个 sidecar 位图（[第 67 篇](67-dirty-bitmap-sidecar.md)）。
- `InstanceInfo` 在 e2b 的 `memory_regions` 之外再多一个 `dirty_tracking: Option<String>`，
  取值 `"hdbss"`、`"kvm-wp"`、`"off"`，带 `skip_serializing_if`，为 `None` 时不出现在响应里
  （[第 65 篇](65-dirty-tracking-backend.md)、[第 66 篇](66-hdbss.md)）。

因此 ARM 适配版上 `GET /` 的完整响应是：

```json
{
  "id": "sandbox-1",
  "state": "Paused",
  "vmm_version": "1.12.1",
  "app_name": "Firecracker",
  "memory_regions": null,
  "dirty_tracking": "hdbss"
}
```

ARM 适配版也带着 e2b 的三个 `/memory*` GET，端点总数因此是上游 32 条（按动作拆行）加 3 加 2。

---

## 6. swagger 与代码不一致的地方

`src/firecracker/swagger/firecracker.yaml` 在三层里都存在，但没有任何构建或测试步骤校验它与代码一致。
以下六处以代码为准。

| # | 位置 | swagger 怎么说 | 代码怎么做 |
|---|---|---|---|
| 1 | 全部端点的 `responses` | 各路径列出 `204` / `400` / `default: 内部服务器错误` | 进程只产生 `{200, 204, 400, 413}`，`default` 对应的 500 来自 `micro_http` 连接层，不来自动作处理 |
| 2 | e2b 定制版（a41d3fb）的 paths | 没有 `/memory/dirty` | `parse_get_memory_dirty()` 存在且可用；swagger 在后续提交 827b783 才补上 |
| 3 | ARM 适配版的 paths | 没有 `/snapshot/save-dirty-bitmap` | `parse_put_snapshot()` 接受 `save-dirty-bitmap` |
| 4 | ARM 适配版 `SnapshotRollbackParams` | 列了 `vcpu_route`，枚举 `reinit` / `registers` | `RollbackSnapshotParams` 没有这个字段且带 `deny_unknown_fields`，带上它是 400 |
| 5 | e2b 与 ARM 的 `InstanceInfo` | 只有 `app_name` / `id` / `state` / `vmm_version` | 实际多出 `memory_regions`（e2b 起）与 `dirty_tracking`（ARM 起） |
| 6 | ARM 适配版 `InstanceInfo.state` 的 `enum` | `Not started` / `Running` / `Paused` | 多一个 `Faulted` |

第 4 条是文档债的典型形态：`vcpu_route` 记录的是回滚里 vCPU 状态写回的两种做法，实现最终收敛到其中一种，
参数被删掉而 swagger 没跟上（[第 71 篇](71-rollback-vcpu-and-gic.md)）。
第 5、6 条的后果不对称：多出来的**响应**字段对宽容的客户端无害，
而第 4 条是多出来的**请求**字段，在 `deny_unknown_fields` 下是硬失败。

另有两处差异不算错，只是版本推进的结果：上游 swagger 的 `SnapshotCreateParams` 把 `mem_file_path` 列为必填，
e2b 定制版与 ARM 适配版的 swagger 都已把它移出 `required`，与代码里的 `Option<PathBuf>` 一致。

---

## 7. 小结

- 路径分派只看 URI 的第一段，第二段由各资源的解析函数处理；不认识的路径、方法与第二段一律 400。
- 允许与否由 `rpc_interface.rs` 的两个 match 决定，不由路径决定；同一个动作在另一段返回
  `OperationNotSupportedPreBoot` / `OperationNotSupportedPostBoot`。
- 上游 v1.12.1 的端点集合是固定的 20 条路径、32 个「路径 + 动作」组合；`GET /vm` 不存在。
- 进程产生的状态码只有 200、204、400、413；`micro_http` 另外可能产生 100 与 500。
- e2b 定制版加三个 runtime 专属的 GET，只有 `/memory/dirty` 额外要求 `Paused`；
  三者共用 `instance_info_count` 计数器。
- ARM 适配版加两个 runtime 专属的 PUT，回滚成功返回 200 与阶段计时，失败一律 400，
  越过提交点后 microVM 进入 `Faulted`。
- swagger 不受任何检查约束，已知六处与代码不符；写调用方时以 `vmm_config` 下的结构体定义为准。

## 延伸阅读 / 下一篇

- [第 08 篇 · API server](08-api-server.md)：HTTP 层怎么实现，为什么是串行的。
- [第 09 篇 · rpc_interface](09-rpc-interface.md)：两个控制器的划分与动作分派。
- [第 77 篇 · 配置项、命令行参数、环境变量与 metrics 总表](77-config-cli-env-metrics-reference.md)：
  本篇里出现的配置项字段在那里有完整取值范围。
- [第 73 篇 · 失败模型](73-failure-model-faulted-and-seccomp.md)：`Faulted` 状态下哪些端点还能用。
- [e2b 手册第 37 篇](../e2b-infra/37-pause-and-snapshot.md)：orchestrator 侧怎么按顺序调用这些端点。
