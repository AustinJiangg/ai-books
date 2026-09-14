# 77 · 配置项、命令行参数、环境变量与 metrics 总表

> 一台 microVM 的行为由四组输入决定：进程的命令行参数、API 或配置文件里的配置项、少数环境变量，
> 以及一组常量。进程的输出除了 guest 本身，还有 metrics 树与退出码。
> 本篇把这四组输入与两组输出收成可查的表，标出三层基线各自加了什么。
>
> **读者**：部署与运维、写调用方的后端工程师、排查进程异常退出的人。
> **预备**：[第 06 篇 · 构建、运行与调试](06-build-run-debug.md)、[第 44 篇 · 日志与 metrics](44-logging-and-metrics.md)。
> **代码**：`src/firecracker/src/main.rs`、`src/jailer/src/main.rs`、`src/vmm/src/vmm_config/`、
> `src/vmm/src/logger/metrics.rs`、`src/vmm/src/lib.rs`、`src/vmm/src/vstate/vm.rs`

---

## 0. 本篇要回答的问题

1. `firecracker` 二进制接受哪些命令行参数，哪些有默认值，哪些互斥或互相要求？
2. `machine-config` 与各设备的配置项完整取值范围是什么，哪些组合会被拒绝？
3. 哪些行为由环境变量控制，为什么会用环境变量而不是 API？
4. `latencies_us` 的十项分别度量哪一段，哪些项在后续层被复用成了别的语义？
5. 进程非正常结束时退出码怎么读，为什么 152 / 153 夹在信号码中间？

---

## 1. 命令行参数

### 1.1 `firecracker`

参数在 `src/firecracker/src/main.rs` 的 `main_exec()` 里一次性注册。参数解析器自带 `--help`；
所有参数都是长选项，没有短选项。「值」列写 `—` 表示这是一个不带值的开关。

| 参数 | 值 | 默认 | 作用 |
|---|---|---|---|
| `--api-sock` | 路径 | `/run/firecracker.socket` | API 监听的 Unix 域套接字 |
| `--id` | 字符串 | `anonymous-instance` | microVM 标识，进入 `InstanceInfo.id` 与日志前缀 |
| `--config-file` | 路径 | 无 | 单文件 JSON 配置，键名 kebab-case |
| `--no-api` | — | 关 | 不起 API server；要求同时给 `--config-file` |
| `--metadata` | 路径 | 无 | 启动时灌入 MMDS 的 JSON 文件 |
| `--seccomp-filter` | 路径 | 无 | 自定义 BPF 过滤器；与 `--no-seccomp` 互斥 |
| `--no-seccomp` | — | 关 | 完全不装过滤器；与 `--seccomp-filter` 互斥 |
| `--log-path` | 路径 | 无 | 日志的 FIFO 或文件 |
| `--level` | 字符串 | 无 | 日志级别 |
| `--module` | 字符串 | 无 | 只输出该模块前缀的日志 |
| `--show-level` | — | 关 | 日志行里带级别 |
| `--show-log-origin` | — | 关 | 日志行里带文件名与行号 |
| `--metrics-path` | 路径 | 无 | metrics 的 FIFO 或文件 |
| `--boot-timer` | — | 关 | 挂上 boot timer 设备 |
| `--http-api-max-payload-size` | 字节数 | `51200` | API 与 MMDS 请求体上限 |
| `--mmds-size-limit` | 字节数 | 无（回落到上一项） | MMDS 数据存储上限 |
| `--start-time-us` | 微秒 | 无 | 父进程传入的启动墙钟时刻，用于 `process_startup_time_us` |
| `--start-time-cpu-us` | 微秒 | 无 | 同上，CPU 时间 |
| `--parent-cpu-time-us` | 微秒 | 无 | 父进程 CPU 时间，从上一项里扣除 |
| `--version` | — | — | 打印版本后退出 |
| `--snapshot-version` | — | — | 打印支持的快照数据格式版本后退出 |
| `--describe-snapshot` | 路径 | — | 打印给定 vmstate 文件的数据格式版本后退出 |

`--level` 的取值在 `LevelFilter::from_str()` 里大小写不敏感地匹配 `off`、`trace`、`debug`、`info`、
`warn`（也接受 `warning`）、`error`；其它值让进程以 `BadConfiguration` 退出。

`--seccomp-filter` 与 `--no-seccomp` 通过 `forbids()` 声明互斥，`--no-api` 通过 `requires("config-file")`
声明依赖，违反任一条都在参数解析阶段失败，退出码 `ArgParsing`。

e2b 定制版与 ARM 适配版都没有增删命令行参数。ARM 适配版部署时不用 jailer，命令行里也没有
`--seccomp-filter` / `--no-seccomp`，因此编译进二进制的默认过滤器生效（[第 62 篇](62-aarch64-seccomp-filter.md)、
[第 63 篇](63-integration-with-e2b-infra.md)）。

### 1.2 `jailer`

`src/jailer/src/main.rs` 的 `build_arg_parser()`。前四个参数必填。

| 参数 | 值 | 默认 | 作用 |
|---|---|---|---|
| `--id` | 字符串 | 必填 | jail 标识，决定 chroot 路径 |
| `--exec-file` | 路径 | 必填 | 要 exec 的二进制 |
| `--uid` / `--gid` | 数字 | 必填 | exec 之后切换到的用户与组 |
| `--chroot-base-dir` | 路径 | `/srv/jailer` | chroot 根的基目录 |
| `--netns` | 路径 | 无 | 要加入的网络 namespace |
| `--daemonize` | — | 关 | `setsid()` 并把标准 I/O 重定向到 `/dev/null` |
| `--new-pid-ns` | — | 关 | 进入新的 PID namespace |
| `--cgroup` | `文件=值` | 无 | 可重复，设置一项 cgroup |
| `--cgroup-version` | `1` 或 `2` | `1` | cgroup 版本 |
| `--parent-cgroup` | 路径 | 无 | 本 microVM cgroup 的父节点 |
| `--resource-limit` | `资源=值` | 无 | 可重复，取 `fsize` 或 `no-file` |
| `--version` | — | — | 打印版本后退出 |

jailer 在 exec 之前调用 `clean_env_vars()` 清空**全部**环境变量。因此凡是靠环境变量传的开关，
经 jailer 启动时都不会到达 Firecracker 进程（[第 43 篇](43-jailer.md)）。

---

## 2. 配置项

配置项有两条等价的入口：API 端点（[第 76 篇](76-api-reference.md)）与 `--config-file` 的单文件 JSON。
后者反序列化成 `VmResources`，字段名是 kebab-case 的顶层键：`boot-source`、`machine-config`、`drives`、
`network-interfaces`、`vsock`、`balloon`、`entropy`、`mmds-config`、`cpu-config`、`logger`、`metrics`。

### 2.1 `machine-config`

`src/vmm/src/vmm_config/machine_config.rs` 的 `MachineConfig`。

| 字段 | 类型 | 默认 | 约束 |
|---|---|---|---|
| `vcpu_count` | u8 | 无默认，必给 | `1..=32`（`MAX_SUPPORTED_VCPUS`）；`smt` 开启时只能是 1 或偶数 |
| `mem_size_mib` | usize | 无默认，必给 | 非 0；`huge_pages` 为 `2M` 时必须是 2 的倍数 |
| `smt` | bool | `false` | aarch64 上置 true 直接报 `SmtNotSupported` |
| `cpu_template` | 字符串 | 无 | 静态模板名；`"None"` 等价于不设 |
| `track_dirty_pages` | bool | `false` | 开启才允许 Diff 快照 |
| `huge_pages` | 字符串 | `"None"` | `"None"` 或 `"2M"` |
| `gdb_socket_path` | 字符串 | 无 | 仅 `gdb` 编译特性下存在 |

`PATCH /machine-config` 的 body 是 `MachineConfigUpdate`：同样的字段全部包一层 `Option`，
只更新给出的字段，随后整体走一次 `MachineConfig::update()` 的校验。校验顺序是
vCPU 数 → SMT 与奇偶 → 内存大小与页大小整除 → CPU 模板，任一条不过就是 400。

`huge_pages` 为 `"2M"` 时 `mmap` 加 `MAP_HUGETLB | MAP_HUGE_2MB`；为 `"None"` 时页大小在代码里写死 4096，
不查 `sysconf`（[第 49 篇](49-why-e2b-forked.md)、[第 52 篇](52-memory-dirty-api.md)）。

### 2.2 设备配置项

| 资源 | 字段 | 默认 | 取值 |
|---|---|---|---|
| `boot-source` | `kernel_image_path` | 必给 | 路径 |
| | `initrd_path` / `boot_args` | 无 | 路径 / 字符串 |
| `drives[]` | `drive_id` | 必给 | 字母数字与 `_` |
| | `is_root_device` | 必给 | bool |
| | `path_on_host` | 无 | 与 `socket` 二选一 |
| | `socket` | 无 | 给出即 vhost-user 块设备 |
| | `is_read_only` | 无 | bool |
| | `partuuid` | 无 | 仅在 `is_root_device` 为 true 时使用 |
| | `cache_type` | `Unsafe` | `Unsafe` / `Writeback` |
| | `io_engine` | `Sync` | `Sync` / `Async` |
| | `rate_limiter` | 无 | 见下 |
| `network-interfaces[]` | `iface_id`、`host_dev_name` | 必给 | 字符串 |
| | `guest_mac` | 无 | `AA:BB:CC:DD:EE:FF` |
| | `rx_rate_limiter` / `tx_rate_limiter` | 无 | 见下 |
| `vsock` | `guest_cid`、`uds_path` | 必给 | u32 / 路径 |
| | `vsock_id` | 无 | 已废弃，出现时计 deprecation |
| `balloon` | `amount_mib` | 必给 | u32 |
| | `deflate_on_oom` | 必给 | bool |
| | `stats_polling_interval_s` | `0` | u16，0 表示关闭统计 |
| `entropy` | `rate_limiter` | 无 | 见下 |
| `mmds-config` | `version` | `V1` | `V1` / `V2` |
| | `network_interfaces` | 必给 | 允许转发到 MMDS 的接口 id 列表 |
| | `ipv4_address` | 无 | 默认由 MMDS 侧决定 |
| `logger` | `log_path` / `level` / `show_level` / `show_log_origin` / `module` | 均无 | 与同名命令行参数一致 |
| `metrics` | `metrics_path` | 必给 | 路径 |

速率限制器（`RateLimiterConfig`）有 `bandwidth` 与 `ops` 两个桶，每个桶三个字段：
`size`（令牌总量）、`refill_time`（毫秒）、`one_time_burst`（可选的一次性额度）。两个桶都可以省略。

### 2.3 后续各层新增的配置项

| 配置项 | 层 | 位置 | 说明 |
|---|---|---|---|
| `CreateSnapshotParams.mem_file_path` 变为可选 | e2b 定制版 | `vmm_config/snapshot.rs` | 不给就不写内存文件（[第 54 篇](54-optional-memfile-snapshot.md)） |
| `CreateSnapshotParams.dirty_bitmap_path` | ARM 适配版 | 同上 | 写出本次快照的页位图 sidecar，需与 `mem_file_path` 同给（[第 67 篇](67-dirty-bitmap-sidecar.md)） |
| `RollbackSnapshotParams`（4 字段） | ARM 适配版 | 同上 | 见[第 69 篇](69-rollback-api-and-phases.md) |
| `SaveDirtyBitmapParams.path` | ARM 适配版 | 同上 | 见[第 68 篇](68-save-dirty-bitmap-api.md) |

---

## 3. 环境变量

上游 v1.12.1 的 Firecracker 进程不读任何自定义环境变量。`std::env::var` 在 `src/` 下的出现全部在
`build.rs`（`TARGET`、`DEBUG`、`OUT_DIR`、`CARGO_CFG_TARGET_ARCH`，构建期）与测试里。
运行期真正起作用的只有 Rust 运行时自己认的那些。

| 变量 | 层 | 读取位置 | 取值与默认 | 作用 |
|---|---|---|---|---|
| `FC_HDBSS_ORDER` | ARM 适配版 | `vstate/vm.rs` 的 `setup_dirty_tracking()` | 整数，默认 `1` | HDBSS 缓冲区的阶：1 表示每个 vCPU 两页共 8 KiB，与内核默认一致；写密集负载调大以减少缓冲区溢出（[第 66 篇](66-hdbss.md)） |
| `FC_HDBSS_REQUIRED` | ARM 适配版 | 同上 | `true` 或 `1` 视为真，默认假 | 为真时 HDBSS 启用失败直接返回 `VmError::HdbssRequired`；为假时静默回落到 KVM 写保护跟踪 |
| `RUST_BACKTRACE` | Rust 运行时 | 标准库 | `0` / `1` / `full` | panic 时是否打印回溯。Firecracker 代码不读它 |

两点值得注意。

第一，`FC_HDBSS_ORDER` 与 `FC_HDBSS_REQUIRED` 都只在 `#[cfg(target_arch = "aarch64")]` 的分支里被读，
在 x86_64 上设置无效果，后者直接把跟踪后端置为 KVM 写保护。

第二，用环境变量而不是 API 字段做开关，代价是这两个值不进 `GET /vm/config`，
也不进快照，从外部看不出一个进程是用什么阶启动的；唯一的线索是启动日志里的
`HDBSS enabled (buffer order N)` 一行，以及 `GET /` 响应里的 `dirty_tracking`
（[第 65 篇](65-dirty-tracking-backend.md)）。经 jailer 启动时这两个变量会被
`clean_env_vars()` 清掉，等价于全部取默认值。

---

## 4. metrics

`METRICS` 是一个进程级静态树，序列化成一行 JSON 写进 `--metrics-path` 指向的文件或 FIFO，
每 60000 ms 一次（`src/firecracker/src/metrics.rs` 的 `WRITE_METRICS_PERIOD_MS`），
`PUT /actions` 的 `FlushMetrics` 可以手动触发一次。microVM 暂停期间定时刷写冻结
（[第 12 篇](12-vmm-event-loop-and-exit.md)、[第 44 篇](44-logging-and-metrics.md)）。

### 4.1 顶层分组

| JSON 键 | 结构体 | 内容 |
|---|---|---|
| `utc_timestamp_ms` | — | 序列化时刻 |
| `api_server` | `ApiServerMetrics` | 启动耗时两项、API 内部失败、与 VMM 通信超时 |
| `get_api_requests` / `put_api_requests` / `patch_api_requests` | `*RequestsMetrics` | 按资源分的调用数与失败数 |
| `deprecated_api` | `DeprecatedApiMetrics` | 废弃 HTTP 字段与废弃命令行参数各一个计数 |
| `latencies_us` | `PerformanceMetrics` | 见 4.2 |
| `logger` | `LoggerSystemMetrics` | 日志与 metrics 自身的丢失与失败计数 |
| `mmds` | `MmdsMetrics` | MMDS 收发包与解析错误 |
| `seccomp` | `SeccompMetrics` | `num_faults`，被过滤器拦下的次数 |
| `signals` | `SignalMetrics` | 七个信号各一个计数 |
| `vcpu` | `VcpuMetrics` | KVM 退出按类型计数与四组 min/max/sum 聚合 |
| `vmm` | `VmmMetrics` | `device_events`、`panic_count` |
| `block` / `net` / `vsock` / `balloon` / `entropy` / `vhost_user` / 串口等 | 各设备 metrics | 以 `#[serde(flatten)]` 摊平到顶层 |

### 4.2 `latencies_us` 十项

每项都是一个「存最后一次」的计量，单位微秒。五个名字成对出现，不带前缀的从 API 层计时（包含拿锁与排队），
带 `vmm_` 前缀的从 VMM 动作真正开始处计时。

| 键 | 度量的区间 | 篇 |
|---|---|---|
| `full_create_snapshot` | API 层：`PUT /snapshot/create`，`Full` | [37](37-snapshot-create.md) |
| `diff_create_snapshot` | API 层：`PUT /snapshot/create`，`Diff` | [37](37-snapshot-create.md) |
| `load_snapshot` | API 层：`PUT /snapshot/load` | [38](38-snapshot-load.md) |
| `pause_vm` | API 层：`PATCH /vm` 到 `Paused` | [15](15-vcpu-threads-and-state-machine.md) |
| `resume_vm` | API 层：`PATCH /vm` 到 `Resumed` | [15](15-vcpu-threads-and-state-machine.md) |
| `vmm_full_create_snapshot` | VMM 层：同上 | [37](37-snapshot-create.md) |
| `vmm_diff_create_snapshot` | VMM 层：同上 | [37](37-snapshot-create.md) |
| `vmm_load_snapshot` | VMM 层：同上 | [38](38-snapshot-load.md) |
| `vmm_pause_vm` | VMM 层：`Vmm::pause_vm()` | [15](15-vcpu-threads-and-state-machine.md) |
| `vmm_resume_vm` | VMM 层：`Vmm::resume_vm()` | [15](15-vcpu-threads-and-state-machine.md) |

ARM 适配版没有给 `PerformanceMetrics` 加项。`PUT /snapshot/rollback` 的总耗时写进了
`latencies_us.vmm_pause_vm`，与真正的暂停耗时混用同一个键；回滚自身的阶段计时只出现在
HTTP 响应的 `timings_us` 里，不进 metrics（[第 69 篇](69-rollback-api-and-phases.md)）。

### 4.3 几个容易误读的计数

| 计数 | 含义 | 注意 |
|---|---|---|
| `get_api_requests.instance_info_count` | `GET /` 的调用数 | e2b 定制版起，三个 `/memory*` 端点也计在这里，来源不可分（[第 50 篇](50-memory-mappings-api.md)） |
| `deprecated_api.deprecated_http_api_calls` | 用了废弃字段的请求数 | `PUT /vsock` 的 `vsock_id`、`PUT /snapshot/load` 的 `mem_file_path` 等 |
| `seccomp.num_faults` | SIGSYS 次数 | 记完就以 `BadSyscall` 退出，这个值最多是 1 |
| `logger.missed_metrics_count` | 刷写失败被丢弃的次数 | metrics 自己的丢失也只能从 metrics 里看 |
| `vmm.panic_count` | panic 发生 | 是「存最后一次」的计量，不是累加 |
| `signals.sigpipe` | SIGPIPE 次数 | 七个信号计数里唯一一个累加型，其余是「存最后一次」 |

---

## 5. 退出码

`FcExitCode`（`src/vmm/src/lib.rs`）是进程退出码的唯一来源；`main()` 把它 `as u8` 交给 `ExitCode`。

| 码 | 名称 | 什么时候出现 |
|---|---|---|
| 0 | `Ok` | 正常结束，包括 guest 自己关机与 reboot |
| 1 | `GenericError` | 未归类的失败（`MainError` 的兜底分支、vCPU 循环里的错误） |
| 2 | `UnexpectedError` | 信号处理器拿到的 `siginfo` 与预期不符，或 SIGSYS 的原因不是「非法系统调用」 |
| 148 | `BadSyscall` | SIGSYS：被 seccomp 过滤器拦下 |
| 149 | `SIGBUS` | SIGBUS |
| 150 | `SIGSEGV` | SIGSEGV |
| 151 | `SIGXFSZ` | SIGXFSZ：写出的文件超过 `fsize` 限制 |
| 152 | `BadConfiguration` | 配置本身不合法，例如 `--level` 给了无法解析的值 |
| 153 | `ArgParsing` | 命令行参数解析失败，包括违反互斥与依赖声明 |
| 154 | `SIGXCPU` | SIGXCPU：超过 CPU 时间限制 |
| 155 | `SIGPIPE` | SIGPIPE |
| 156 | `SIGHUP` | SIGHUP |
| 157 | `SIGILL` | SIGILL |

信号相关的码从 148 起按 `SIGBUS`、`SIGSEGV`、`SIGXFSZ` 递增到 151，然后**跳过 152 与 153**
接到 154 的 `SIGXCPU`。152 与 153 是后加进来的两个非信号码，插在中间没有重排已有的值 ——
退出码是对外契约，重排会让已经部署的调用方误判。读这段枚举时不要假定信号码是连续的。

`register_signal_handler()` 只为这八个信号装处理器：SIGSYS、SIGBUS、SIGSEGV、SIGXFSZ、SIGXCPU、
SIGPIPE、SIGHUP、SIGILL。SIGTERM 与 SIGINT **不在其中**，保持系统默认行为
（[第 07 篇](07-process-startup.md)）。

ARM 适配版没有新增退出码。回滚失败不让进程退出，而是把 microVM 置为 `Faulted`：
`Vmm::pause_vm()` 与 `resume_vm()` 此后返回 `VmmError::VmFaulted`，进程活着等编排层替换
（[第 73 篇](73-failure-model-faulted-and-seccomp.md)）。

---

## 6. 几个写死的常量

这些值没有配置入口，改它们要改代码重编译。

| 常量 | 值 | 位置 | 含义 |
|---|---|---|---|
| `MAX_SUPPORTED_VCPUS` | 32 | `vmm_config/machine_config.rs` | vCPU 数上限 |
| `HTTP_MAX_PAYLOAD_SIZE` | 51200 | `vmm/src/lib.rs` | 请求体默认上限，可被 `--http-api-max-payload-size` 覆盖 |
| `RECV_TIMEOUT_SEC` | 30 s | `vmm/src/lib.rs` | 等 vCPU 线程应答 pause / resume / save / restore 的超时，用于发现 vCPU 死锁 |
| `WRITE_METRICS_PERIOD_MS` | 60000 | `firecracker/src/metrics.rs` | metrics 定时刷写周期 |
| `DEFAULT_API_SOCK_PATH` | `/run/firecracker.socket` | `firecracker/src/main.rs` | `--api-sock` 默认值 |
| `DEFAULT_INSTANCE_ID` | `anonymous-instance` | `vmm/src/logger/logging.rs` | `--id` 默认值 |

---

## 7. 小结

- 命令行参数只有长选项，互斥与依赖在解析阶段声明并检查，违反即以 153 退出。
- 配置项的两条入口（API 与 `--config-file`）落到同一组 `vmm_config` 结构体，取值范围与校验顺序也同一份。
- `machine-config` 的校验顺序是 vCPU 数、SMT 奇偶、内存与页大小整除、CPU 模板；aarch64 上 `smt` 为真直接拒绝。
- 上游运行期不读任何自定义环境变量；ARM 适配版用 `FC_HDBSS_ORDER` 与 `FC_HDBSS_REQUIRED`
  控制硬件脏页跟踪的缓冲区大小与失败策略，代价是这两个值不进配置查询也不进快照，且经 jailer 启动时会被清掉。
- `latencies_us` 的十项是五对「API 层 / VMM 层」，ARM 适配版的回滚复用 `vmm_pause_vm`，语义混用。
- `FcExitCode` 里 152 与 153 插在信号码序列中间，`SIGXCPU` 是 154 而不是 152；不要按连续假定推算。
- 只装了八个信号处理器，SIGTERM 与 SIGINT 保持默认行为。

## 延伸阅读 / 下一篇

- [第 06 篇 · 构建、运行与调试](06-build-run-debug.md)：这些参数在真实命令行里怎么组合。
- [第 44 篇 · 日志与 metrics](44-logging-and-metrics.md)：metrics 树的结构与丢数据的条件。
- [第 76 篇 · API 端点总表](76-api-reference.md)：配置项对应的端点与 JSON 骨架。
- [第 66 篇 · HDBSS](66-hdbss.md)：两个环境变量背后的硬件机制与回落路径。
- [e2b 手册第 28 篇](../e2b-infra/28-firecracker-process-management.md)：orchestrator 实际拼出的命令行与进程管理。
