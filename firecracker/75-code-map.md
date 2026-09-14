# 75 · 代码地图：crate、模块与篇目

> 这是一张查找表，不是一篇叙述。它把上游 v1.12.1 源码树里的每一个目录与主要文件，
> 对上「它做什么」「本书哪一篇讲它」「e2b 定制版与 ARM 适配版有没有动过它」。
> 读代码时遇到一个陌生文件，从这里能一步找到对应的篇目；准备改一处代码时，从这里能一眼看出这处是不是已经被两层改动占用。
>
> **读者**：所有读者。　**预备**：[第 01 篇 · 三层版本谱系与仓库地图](01-lineage-and-repo-map.md)、
> [第 46 篇 · 代码组织、依赖与构建](46-code-organization-and-build.md)。
> **代码**：整棵源码树，基线为 `tmp/e2b-book-src/fc-upstream/`（`v1.12.1`，commit `d990331f7`）

---

## 0. 本篇要回答的问题

1. 上游 v1.12.1 的源码树由哪些 crate 组成，每个多大、产出什么？
2. `vmm` crate 内部的目录与文件怎么按控制面、状态面、机器面、数据面归位？
3. 给定一个文件路径，本书哪一篇（或哪几篇）讲它？
4. 哪些文件被 e2b 定制版动过，哪些又被 ARM 适配版动过？两层各新增了哪些文件？
5. 源码之外的 `resources/`、`tests/`、`tools/`、`docs/` 各存放什么，谁在用？

---

## 1. 这张表怎么读

全书的四种坐标在这一篇里合并成一行。

**路径**一律是仓库相对路径，基准是 firecracker 仓库根。在 ARM 适配版里，
这个根对应 KASandbox 仓库的 `firecracker/` 目录，所以本篇写 `src/vmm/src/rollback.rs`，
在那个仓库里的完整路径是 `firecracker/src/vmm/src/rollback.rs`。

**行数**是 `wc -l` 的原始行数，包含注释、空行与文件内的 `#[cfg(test)]` 单元测试块。
Firecracker 的单元测试与被测代码同文件，很多文件里测试占一半以上（`src/vmm/src/devices/virtio/queue.rs`
的 1721 行里有一大段是 `mod tests`），所以行数只适合用来判断「这个文件是大是小」，
不适合当作实现复杂度的度量。

**篇目**列给出题注里把该文件列为主要代码的篇。一个文件常被多篇引用，这里只列把它当作主题的那几篇；
只是顺带提到的不列。空着的「—」表示本书没有专门讲它，通常是生成代码、单元测试辅助或本书范围之外的内容。

**e2b 列与 ARM 列**的含义不对称，这一点要先说清楚，否则会读错：

| 列 | 打勾的含义 | 比较的两个版本 |
|---|---|---|
| e2b | e2b 定制版相对上游 v1.12.1 修改或新增了这个文件 | `v1.12.1` → `a41d3fb` |
| ARM | ARM 适配版在它迁入的 e2b 提交之上又修改或新增了这个文件 | `54a1c1a` → `b8e85c3` → `3863c76` |

也就是说，ARM 列**不重复**继承自 e2b 定制版的那些改动。`src/vmm/src/utils/pagemap.rs`
是 e2b 新增的文件，ARM 适配版里它照样存在、照样被编译，但 ARM 适配版没有再改它，
所以那一行只有 e2b 列打勾。两列都打勾的行是需要特别小心的：这些文件被两层先后改过，
升级上游时要按顺序重放两次（重放清单见[第 78 篇 · 三层差异总表](78-layer-diff-tables.md)）。

还有一处不对称要记住：ARM 适配版迁入的是 `54a1c1a`，比 e2b 定制版钉的 `a41d3fb`
少一个提交，差别落在 `src/vmm/Cargo.toml`、`src/vmm/src/lib.rs`、`src/vmm/src/persist.rs`
与 `Cargo.lock` 这四个文件上，内容是 uffd 写保护。理由与后果见
[第 57 篇 · 迁入的版本与被放弃的写保护](57-which-fork-commit-and-uffd-wp.md)。

---

## 2. 仓库顶层

上游 v1.12.1 的仓库根下有 697 个受版本控制的文件，分成五类。

```text
firecracker/
├── Cargo.toml            workspace 定义：十二个成员 crate 与公共依赖
├── Cargo.lock            锁定的依赖版本；CI 强制它与 Cargo.toml 一致
├── rust-toolchain.toml   工具链版本，构建时由 rustup 读取
├── deny.toml             cargo-deny 的许可证与漏洞策略
├── src/                  十二个 crate（下面第 3 节起逐个展开）
├── resources/            随二进制一起发布或在构建期消费的数据
│   ├── seccomp/          两份架构相关的 BPF 白名单 JSON，构建时编译进二进制
│   ├── guest_configs/    CI 用的 guest 内核 config
│   ├── overlay/          测试 rootfs 里的 init 与网络脚本
│   ├── chroot.sh         jailer 场景下的 chroot 辅助脚本
│   └── rebuild.sh        重建 CI 内核与 rootfs 产物
├── tests/                pytest 集成测试（框架 + 五类测试 + 数据）
├── tools/                devtool、构建容器、发布脚本、bindgen 包装
├── docs/                 上游文档；本书以代码为准，只把它当参考
└── .buildkite/           CI 流水线定义（Python 生成 YAML）
```

`src/` 之外的四个目录里，只有 `resources/seccomp/` 的内容会进入 `firecracker` 二进制
——`src/firecracker/build.rs` 在编译期把 JSON 编成 BPF 字节码嵌进去
（[第 42 篇 · seccomp](42-seccomp.md)）。其余都是开发期或测试期的资产。

---

## 3. 十二个 crate

`src/` 下是一个 cargo workspace 的十二个成员。六个产出可执行文件，六个是库。

| crate | 产物 | `.rs` 文件 / 行数 | 做什么 | 篇目 |
|---|---|---|---|---|
| `vmm` | 库 | 235 / 78 704 | VMM 的全部实现：KVM 抽象、设备、快照、配置 | 第 7–41 篇 |
| `firecracker` | 可执行 | 35 / 5 737 | 主二进制：参数解析、API server、seccomp 安装 | [第 07 篇](07-process-startup.md)、[第 08 篇](08-api-server.md) |
| `jailer` | 可执行 | 5 / 3 133 | chroot、cgroup、namespace 与降权 | [第 43 篇](43-jailer.md) |
| `cpu-template-helper` | 可执行 | 18 / 2 739 | 采集 CPU 指纹、生成与裁剪 CPU 模板 | [第 22 篇](22-aarch64-templates-and-helper.md) |
| `snapshot-editor` | 可执行 | 5 / 650 | 离线编辑 vmstate 与内存文件 | [第 41 篇](41-snapshot-tools-and-compat.md) |
| `rebase-snap` | 可执行 | 1 / 329 | 把 Diff 内存文件合进基线内存文件 | [第 41 篇](41-snapshot-tools-and-compat.md) |
| `seccompiler` | 库 + 可执行 | 5 / 606 | 把 JSON 过滤器编成 BPF 程序 | [第 42 篇](42-seccomp.md) |
| `acpi-tables` | 库 | 7 / 2 704 | 构造 RSDP / XSDT / FADT / MADT / DSDT 与 AML | [第 17 篇](17-x86-64-platform.md) |
| `utils` | 库 | 4 / 1 411 | 参数解析、时间、字符串校验 | [第 06 篇](06-build-run-debug.md) |
| `clippy-tracing` | 可执行 | 2 / 934 | 批量增删 `#[instrument]` 属性的源码改写工具 | [第 45 篇](45-gdb-tracing-and-kani.md) |
| `log-instrument` | 库 | 7 / 216 | `instrument` 过程宏的运行时支撑 | [第 45 篇](45-gdb-tracing-and-kani.md) |
| `log-instrument-macros` | 库 | 1 / 38 | 上面那个宏的实现 | [第 45 篇](45-gdb-tracing-and-kani.md) |

`vmm` 一个 crate 占了全部 Rust 代码的八成，所以后面的篇幅也按这个比例分配：
第 4 至 8 节展开 `vmm`，第 9 节一次性给出其余十一个 crate。
crate 之间的依赖方向、哪几条边被刻意断开，见
[第 46 篇 §3](46-code-organization-and-build.md#3-vmm-内部一条主干与两个例外)，本篇不重复。

---

## 4. `vmm` crate 的目录树

`src/vmm/src/lib.rs` 声明的十七个模块，按[第 46 篇](46-code-organization-and-build.md)
的四组划分排列如下。括号里是该目录下所有 `.rs` 文件的行数合计。

```text
src/vmm/src/                                      77 285 行
│
├─ 控制面：从 API 请求到一台运行中的 microVM
│  ├── rpc_interface.rs                    1 276   VmmAction 与 Preboot / Runtime 两个控制器
│  ├── resources.rs                        1 575   VmResources：启动前累积的配置集合
│  ├── vmm_config/                         2 495   每类资源的配置结构与校验（12 个文件）
│  ├── builder.rs                          1 284   从配置构建 microVM；也含从快照恢复的入口
│  ├── initrd.rs                             140   把 initrd 读进 guest 内存并记录位置
│  ├── lib.rs                                916   Vmm 结构体、事件循环、pause / resume
│  └── signal_handler.rs                     243   SIGBUS / SIGSEGV / SIGSYS 的处理与退出码
│
├─ 状态面：快照、暂停与恢复
│  ├── persist.rs                            762   MicrovmState 的保存与恢复、内存后端选择
│  └── snapshot/                             576   版本化序列化格式（mod.rs / crc.rs / persist.rs）
│
├─ 机器面：KVM 之上的抽象与平台代码
│  ├── vstate/                             2 499   kvm.rs / vm.rs / vcpu.rs / memory.rs
│  ├── arch/                               10 614  x86_64/ 与 aarch64/ 两套平台代码（39 个文件）
│  ├── cpu_config/                          6 318  CPU 模板：静态、自定义与序列化（25 个文件）
│  └── acpi/                                 344   x86_64 的 ACPI 表装配
│
├─ 数据面：设备与 I/O
│  ├── device_manager/                      2 274  总线、MMIO 分配、设备状态的保存与恢复
│  ├── devices/                            29 137  legacy / virtio / pseudo / acpi 四类设备（79 个文件）
│  ├── io_uring/                            2 067  block 的异步 I/O 引擎
│  ├── rate_limiter/                        1 407  令牌桶与它的持久化
│  ├── dumbo/                               6 724  MMDS 专用的 TCP/IP 栈
│  ├── mmds/                                2 720  元数据存储、token 与网络栈接入
│  └── logger/                              1 516  日志与 metrics
│
└─ 其它
   ├── utils/                                 568  字节序、状态机、MAC / IPv4、信号封装
   ├── seccomp.rs                             215  把编译期嵌入的 BPF 装到线程上
   ├── gdb/                                 1 346  cfg(feature = "gdb")，不进发布产物
   └── test_utils/                            269  单元测试与 vmm 内集成测试的夹具
```

`arch/` 的两个子树在行数上并不对称：`x86_64/` 5 441 行，`aarch64/` 5 057 行，
另有 `arch/mod.rs` 116 行。差距的一部分来自 `x86_64/generated/` 的 998 行 ——
那是 bindgen 从内核头文件生成的常量表，不是手写代码。
两边同名文件的差异是[第 59 篇 · aarch64 与 x86_64 运行路径的差异清单](59-aarch64-vs-x86-64-runtime-paths.md)的主题。

---

## 5. 控制面的文件

| 文件 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|
| `rpc_interface.rs` | `VmmAction` 枚举、`PrebootApiController` 与 `RuntimeApiController` | ✓ | ✓ | [第 09 篇](09-rpc-interface.md) |
| `resources.rs` | `VmResources`：启动前累积的全部配置，含 `from_json()` | | | [第 10 篇](10-vm-resources-and-config.md) |
| `builder.rs` | `build_microvm_for_boot()` 与 `build_microvm_from_snapshot()` | | ✓ | [第 11 篇](11-builder.md) |
| `lib.rs` | `Vmm` 结构体、`EventManager` 订阅、pause / resume、退出码 | ✓ | ✓ | [第 12 篇](12-vmm-event-loop-and-exit.md) |
| `initrd.rs` | 读取 initrd 文件，算出它在 guest 物理内存里的落点 | | | [第 11 篇](11-builder.md) |
| `signal_handler.rs` | `SIGSYS` 打印被拦的系统调用号，`SIGBUS` 区分 uffd 场景 | | | [第 42 篇](42-seccomp.md) |
| `seccomp.rs` | `apply_filter()`：把 BPF 程序装到当前线程 | | | [第 42 篇](42-seccomp.md) |
| `utils/sm.rs` | 一个极小的状态机组合子，vCPU 状态机用它 | | | [第 15 篇](15-vcpu-threads-and-state-machine.md) |
| `utils/signal.rs` | `sigrtmin()` 之类的信号号计算 | | | [第 15 篇](15-vcpu-threads-and-state-machine.md) |
| `utils/byte_order.rs` | guest 内存上的小端读写辅助 | | | — |
| `utils/net/mac.rs`、`net/ipv4addr.rs` | MAC 与 IPv4 地址的解析与显示 | | | [第 30 篇](30-virtio-net.md) |
| `utils/pagemap.rs` | **e2b 新增**：读 `/proc/self/pagemap` 判定页的驻留与脏状态 | ✓ | | [第 52 篇](52-memory-dirty-api.md) |
| `utils/mod.rs` | 上述子模块的声明 | ✓ | | — |

`vmm_config/` 十二个文件，每个对应一类资源的配置结构、默认值与校验规则。
它们是 API 请求体反序列化后的落点，也是 `VmResources` 的字段类型。

| 文件 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|
| `vmm_config/machine_config.rs` | vCPU 数、内存大小、SMT、huge pages、`track_dirty_pages` | | | [第 10 篇](10-vm-resources-and-config.md)、[第 20 篇](20-cpu-templates.md) |
| `vmm_config/boot_source.rs` | 内核路径、initrd 路径、内核命令行 | | | [第 10 篇](10-vm-resources-and-config.md) |
| `vmm_config/drive.rs` | 块设备配置：文件路径、只读、缓存策略、I/O 引擎 | | | [第 10 篇](10-vm-resources-and-config.md)、[第 27 篇](27-virtio-block.md) |
| `vmm_config/net.rs` | 网卡配置：tap 名、MAC、速率限制 | | | [第 10 篇](10-vm-resources-and-config.md)、[第 30 篇](30-virtio-net.md) |
| `vmm_config/vsock.rs` | vsock CID 与 Unix socket 路径 | | | [第 33 篇](33-vsock.md) |
| `vmm_config/balloon.rs` | 气球目标大小、是否延迟收缩、统计周期 | | | [第 34 篇](34-balloon.md) |
| `vmm_config/entropy.rs` | entropy 设备的速率限制 | | | [第 35 篇](35-entropy-vmgenid-rate-limiter.md) |
| `vmm_config/mmds.rs` | MMDS 版本、IPv4 地址、允许访问的网卡 | | | [第 32 篇](32-mmds.md) |
| `vmm_config/metrics.rs` | metrics 输出路径 | | | [第 44 篇](44-logging-and-metrics.md) |
| `vmm_config/instance_info.rs` | `InstanceInfo`：实例 id、版本、`VmState` | ✓ | ✓ | [第 09 篇](09-rpc-interface.md)、[第 73 篇](73-failure-model-faulted-and-seccomp.md) |
| `vmm_config/snapshot.rs` | `CreateSnapshotParams`、`LoadSnapshotParams`、内存后端类型 | ✓ | ✓ | [第 36 篇](36-snapshot-overview-and-format.md)、[第 67 篇](67-dirty-bitmap-sidecar.md) |
| `vmm_config/mod.rs` | 速率限制配置的公共类型 `RateLimiterConfig` | | | [第 10 篇](10-vm-resources-and-config.md)、[第 35 篇](35-entropy-vmgenid-rate-limiter.md) |

`instance_info.rs` 与 `snapshot.rs` 是全书唯二被两层都改过的配置文件：
前者被 e2b 加了内存区域字段、被 ARM 适配版加了 `Faulted` 状态；
后者被 e2b 加了可选 memfile、被 ARM 适配版加了 `dirty_bitmap_path`。

---

## 6. 状态面的文件

| 文件 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|
| `persist.rs` | `MicrovmState` 的定义、`create_snapshot()`、`restore_from_snapshot()`、内存后端选择 | ✓ | ✓ | [第 36 篇](36-snapshot-overview-and-format.md)、[第 37 篇](37-snapshot-create.md)、[第 38 篇](38-snapshot-load.md)、[第 39 篇](39-uffd-backend.md) |
| `snapshot/mod.rs` | 快照容器格式：magic、版本、bincode 编解码 | | | [第 36 篇](36-snapshot-overview-and-format.md)、[第 48 篇](48-release-and-compat-policy.md) |
| `snapshot/crc.rs` | 写入与读取时的 CRC64 包装 Reader / Writer | | | [第 36 篇](36-snapshot-overview-and-format.md) |
| `snapshot/persist.rs` | `Persist` trait 的定义（25 行，全书设备恢复的接口原点） | | | [第 40 篇](40-device-persist.md) |
| `rollback.rs` | **ARM 适配版新增**（656 行）：原地回滚的十个阶段与脏位图落盘 | | ✓ | [第 69 篇](69-rollback-api-and-phases.md)、[第 70 篇](70-rollback-memory.md)、[第 71 篇](71-rollback-vcpu-and-gic.md)、[第 72 篇](72-rollback-devices.md) |

`persist.rs` 只有 762 行，却是三层改动重叠最深的一个文件：
e2b 在这里加了可选 memfile 的分支与 uffd 写保护的注册，
ARM 适配版在这里接上了脏位图 sidecar 的写出，并且因为迁入的是 `54a1c1a`，
少掉了 e2b 在 `guest_memory_from_uffd()` 里加的那段写保护注册。

---

## 7. 机器面的文件

### 7.1 `vstate/`：KVM 的四层封装

| 文件 | 行数 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|---|
| `vstate/kvm.rs` | 120 | `/dev/kvm` 的打开与能力检查 | | | [第 03 篇](03-kvm-api-primer.md) |
| `vstate/vm.rs` | 394 | VM fd：memslot 注册、脏页位图、中断控制器 | ✓ | ✓ | [第 13 篇](13-guest-memory.md)、[第 14 篇](14-dirty-page-tracking.md) |
| `vstate/vcpu.rs` | 1 249 | vCPU 线程、状态机、`KVM_RUN` 循环与退出处理 | | ✓ | [第 15 篇](15-vcpu-threads-and-state-machine.md) |
| `vstate/memory.rs` | 725 | `GuestMemoryMmap` 的构建、dump、位图与 uffd 后端 | | ✓ | [第 13 篇](13-guest-memory.md)、[第 39 篇](39-uffd-backend.md) |

`vstate/vm.rs` 是两层改动最集中的一个文件：e2b 在这里加了三个内存查询 API 的实现
（[第 50 篇](50-memory-mappings-api.md)、[第 51 篇](51-memory-resident-empty-api.md)、[第 52 篇](52-memory-dirty-api.md)），
ARM 适配版又在这里加了脏页跟踪后端的抽象（[第 65 篇](65-dirty-tracking-backend.md)）。

### 7.2 `arch/`：两套平台代码

`arch/mod.rs`（116 行）用 `#[cfg(target_arch)]` 把两个子模块之一重导出为 `arch`，
两边必须提供同名的类型与函数；这层对齐是[第 59 篇](59-aarch64-vs-x86-64-runtime-paths.md)的前提。

| 文件 | 行数 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|---|
| `arch/x86_64/mod.rs` | 649 | x86_64 内存布局计算、启动参数与 PVH / bzImage 加载 | | | [第 17 篇](17-x86-64-platform.md) |
| `arch/x86_64/layout.rs` | 79 | 各段 GPA 常量 | | | [第 17 篇](17-x86-64-platform.md) |
| `arch/x86_64/vcpu.rs` | 1 311 | `KvmVcpu`：CPUID / MSR / 寄存器的读写与保存恢复 | | ✓ | [第 16 篇](16-x86-64-vcpu.md) |
| `arch/x86_64/regs.rs` | 491 | 通用、段、控制寄存器与页表的初始设置 | | | [第 16 篇](16-x86-64-vcpu.md) |
| `arch/x86_64/gdt.rs` | 147 | GDT 表项构造 | | | [第 16 篇](16-x86-64-vcpu.md) |
| `arch/x86_64/msr.rs` | 537 | MSR 白名单与批量读写 | | | [第 16 篇](16-x86-64-vcpu.md)、[第 21 篇](21-x86-64-cpuid-msr-normalization.md) |
| `arch/x86_64/xstate.rs` | 136 | XSAVE 区域的保存与恢复 | | | [第 16 篇](16-x86-64-vcpu.md) |
| `arch/x86_64/interrupts.rs` | 153 | LAPIC 的初始配置 | | | [第 16 篇](16-x86-64-vcpu.md) |
| `arch/x86_64/vm.rs` | 314 | x86_64 的 VM 级状态：PIT、irqchip、TSS | | | [第 17 篇](17-x86-64-platform.md) |
| `arch/x86_64/kvm.rs` | 70 | x86_64 必需的 KVM 能力清单 | | | [第 03 篇](03-kvm-api-primer.md) |
| `arch/x86_64/mptable.rs` | 458 | 无 ACPI 时的 MP 表 | | | [第 17 篇](17-x86-64-platform.md) |
| `arch/x86_64/cpu_model.rs` | 98 | 从 CPUID 判定厂商与型号 | | | [第 17 篇](17-x86-64-platform.md) |
| `arch/x86_64/generated/` | 998 | bindgen 生成：MSR 索引、mpspec、hyperv 常量 | | | [第 05 篇](05-rust-and-crates-primer.md) |
| `arch/aarch64/mod.rs` | 284 | aarch64 内存布局与内核镜像加载 | | | [第 19 篇](19-aarch64-platform.md) |
| `arch/aarch64/layout.rs` | 84 | 各段 GPA 常量、MMIO 窗口 | | | [第 19 篇](19-aarch64-platform.md) |
| `arch/aarch64/vcpu.rs` | 781 | `KVM_ARM_VCPU_INIT`、寄存器列表、PSCI 与保存恢复 | | ✓ | [第 18 篇](18-aarch64-vcpu.md) |
| `arch/aarch64/regs.rs` | 748 | 寄存器 id 的编码规则与分类 | | | [第 18 篇](18-aarch64-vcpu.md)、[第 22 篇](22-aarch64-templates-and-helper.md) |
| `arch/aarch64/cache_info.rs` | 579 | 从 sysfs 读取宿主缓存层次，写进 FDT | | | [第 18 篇](18-aarch64-vcpu.md)、[第 60 篇](60-kunpeng-openeuler-host.md) |
| `arch/aarch64/fdt.rs` | 650 | 设备树的构造：内存、CPU、GIC、virtio-mmio 节点 | | | [第 19 篇](19-aarch64-platform.md)、[第 61 篇](61-guest-kernel-on-arm.md) |
| `arch/aarch64/vm.rs` | 101 | aarch64 的 VM 级状态：GIC 的创建与保存恢复 | | ✓ | [第 19 篇](19-aarch64-platform.md)、[第 66 篇](66-hdbss.md) |
| `arch/aarch64/kvm.rs` | 60 | aarch64 必需的 KVM 能力清单 | | | [第 03 篇](03-kvm-api-primer.md)、[第 60 篇](60-kunpeng-openeuler-host.md) |
| `arch/aarch64/gic/mod.rs` | 180 | GIC 版本探测：先试 v3 再退 v2 | | | [第 19 篇](19-aarch64-platform.md) |
| `arch/aarch64/gic/regs.rs` | 166 | GIC 寄存器读写的公共辅助 | | | [第 19 篇](19-aarch64-platform.md) |
| `arch/aarch64/gic/gicv3/` | 851 | GICv3 的分发器、重分发器与 CPU 接口寄存器 | | | [第 19 篇](19-aarch64-platform.md) |
| `arch/aarch64/gic/gicv2/` | 573 | GICv2 的对应实现 | | | [第 19 篇](19-aarch64-platform.md) |
| `arch/aarch64/output_*.dtb` | — | 四个用于 FDT 单元测试的参考设备树二进制 | | | [第 47 篇](47-testing.md) |

### 7.3 `cpu_config/`：CPU 模板

| 文件 | 行数 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|---|
| `cpu_config/templates.rs` | 366 | 模板的通用类型：`CpuTemplateType`、修饰符与掩码 | | | [第 20 篇](20-cpu-templates.md) |
| `cpu_config/templates_serde.rs` | 81 | 十六进制字符串与位掩码之间的 serde 适配 | | | [第 20 篇](20-cpu-templates.md) |
| `cpu_config/x86_64/cpuid/mod.rs` | 784 | `Cpuid` 容器：叶子的查找、插入与遍历 | | | [第 21 篇](21-x86-64-cpuid-msr-normalization.md) |
| `cpu_config/x86_64/cpuid/normalize.rs` | 563 | 与厂商无关的 CPUID 归一化 | | | [第 21 篇](21-x86-64-cpuid-msr-normalization.md) |
| `cpu_config/x86_64/cpuid/intel/normalize.rs` | 568 | Intel 特有的归一化 | | | [第 21 篇](21-x86-64-cpuid-msr-normalization.md) |
| `cpu_config/x86_64/cpuid/amd/normalize.rs` | 439 | AMD 特有的归一化 | | | [第 21 篇](21-x86-64-cpuid-msr-normalization.md) |
| `cpu_config/x86_64/cpuid/common.rs` | 157 | 叶子 / 子叶的类型与厂商字符串 | | | [第 21 篇](21-x86-64-cpuid-msr-normalization.md) |
| `cpu_config/x86_64/custom_cpu_template.rs` | 577 | x86_64 自定义模板的结构与应用 | | | [第 20 篇](20-cpu-templates.md) |
| `cpu_config/x86_64/static_cpu_templates/` | 1 438 | C3、T2、T2A、T2CL、T2S 五个静态模板 | | | [第 21 篇](21-x86-64-cpuid-msr-normalization.md) |
| `cpu_config/aarch64/custom_cpu_template.rs` | 391 | aarch64 自定义模板：按寄存器 id 打补丁 | | | [第 22 篇](22-aarch64-templates-and-helper.md) |
| `cpu_config/aarch64/static_cpu_templates/v1n1.rs` | 102 | 唯一的 aarch64 静态模板 | | | [第 22 篇](22-aarch64-templates-and-helper.md) |

### 7.4 `acpi/`

| 文件 | 行数 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|---|
| `acpi/mod.rs` | 290 | 把 `acpi-tables` 构造的表写进 guest 内存并串起指针链 | | | [第 17 篇](17-x86-64-platform.md) |
| `acpi/x86_64.rs` | 54 | x86_64 的表地址常量 | | | [第 17 篇](17-x86-64-platform.md) |

---

## 8. 数据面的文件

### 8.1 `device_manager/`

这是 `vmm` 十七个模块里唯一声明为 `pub(crate)` 的：设备管理器不对 crate 外暴露。

| 文件 | 行数 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|---|
| `device_manager/mmio.rs` | 854 | MMIO 地址与 IRQ 的分配、virtio 设备的注册与内核命令行拼装 | | | [第 23 篇](23-bus-and-mmio-device-manager.md) |
| `device_manager/legacy.rs` | 269 | 串口、i8042、RTC 的注册（两架构分支不同） | | | [第 24 篇](24-legacy-devices.md) |
| `device_manager/acpi.rs` | 89 | vmgenid 等 ACPI 设备的注册 | | | [第 35 篇](35-entropy-vmgenid-rate-limiter.md) |
| `device_manager/resources.rs` | 145 | MMIO / IRQ 资源分配器 | | | [第 23 篇](23-bus-and-mmio-device-manager.md) |
| `device_manager/persist.rs` | 900 | 全部设备状态的保存与按序恢复；拓扑校验的依据 | | | [第 40 篇](40-device-persist.md) |
| `device_manager/mod.rs` | 17 | 子模块声明与 `DeviceManager` 的组合 | | | [第 23 篇](23-bus-and-mmio-device-manager.md) |

### 8.2 `devices/`：四类设备

`devices/` 是 `vmm` 里最大的一块（29 137 行，79 个文件）。virtio 设备有固定的文件套路：
`device.rs` 放设备本体与队列处理，`event_handler.rs` 把 fd 接进 `EventManager`，
`persist.rs` 实现 `Persist`，`metrics.rs` 放该设备的计数器。认出这个套路就能在任意设备目录里快速定位。

```text
devices/
├── bus.rs                  404   地址区间到设备的路由表
├── legacy/                1 205   i8042、串口、PL031 RTC
├── pseudo/boot_timer.rs      45   一次性的启动打点设备
├── acpi/vmgenid.rs          183   虚拟机世代 id，恢复后通知 guest
└── virtio/               27 300   传输层 + 六种设备
    ├── mmio.rs             987   virtio-mmio 寄存器窗口
    ├── device.rs           314   VirtioDevice trait
    ├── queue.rs          1 721   virtqueue 的描述符环解析
    ├── iovec.rs          1 075   描述符链到 iovec 的转换
    ├── iov_deque.rs        535   环形 iovec 缓冲
    ├── persist.rs          479   队列与传输层状态的保存恢复
    ├── block/            5 587   virtio-block 与 vhost-user-block
    ├── net/              5 006   virtio-net
    ├── vsock/            6 159   vsock 设备与 Unix muxer
    ├── balloon/          2 150   气球
    ├── rng/                946   entropy
    ├── vhost_user.rs       969   vhost-user 协议的客户端实现
    └── generated/          307   bindgen 生成的 virtio 常量
```

| 文件 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|
| `devices/bus.rs` | `Bus`：按地址区间查找设备，MMIO 与 PIO 各一份 | | | [第 23 篇](23-bus-and-mmio-device-manager.md) |
| `devices/legacy/serial.rs` | 16550A 串口，含输出缓冲与写阻塞处理 | | | [第 24 篇](24-legacy-devices.md) |
| `devices/legacy/i8042.rs` | 键盘控制器，只为接收 guest 的复位命令 | | | [第 24 篇](24-legacy-devices.md) |
| `devices/legacy/rtc_pl031.rs` | aarch64 的 PL031 RTC | | | [第 24 篇](24-legacy-devices.md) |
| `devices/pseudo/boot_timer.rs` | guest 写一个字节即记录启动完成时刻 | | | [第 24 篇](24-legacy-devices.md) |
| `devices/acpi/vmgenid.rs` | 恢复快照后更新世代 id 并注入中断 | | ✓ | [第 35 篇](35-entropy-vmgenid-rate-limiter.md)、[第 72 篇](72-rollback-devices.md) |
| `devices/virtio/mmio.rs` | virtio-mmio 寄存器读写、状态位与队列通知 | | | [第 25 篇](25-virtio-device-model-and-transport.md) |
| `devices/virtio/device.rs` | `VirtioDevice` trait 与 `DeviceState` | | | [第 25 篇](25-virtio-device-model-and-transport.md) |
| `devices/virtio/queue.rs` | 描述符环、avail / used 环的解析与校验 | | | [第 26 篇](26-virtqueue-implementation.md) |
| `devices/virtio/iovec.rs` | 描述符链到 `IoVecBuffer` 的转换与脏页标记 | | | [第 26 篇](26-virtqueue-implementation.md) |
| `devices/virtio/iov_deque.rs` | 双映射环形缓冲，让 iovec 连续可见 | | | [第 26 篇](26-virtqueue-implementation.md) |
| `devices/virtio/persist.rs` | 队列与传输层状态的 `Persist` 实现 | | ✓ | [第 40 篇](40-device-persist.md)、[第 72 篇](72-rollback-devices.md) |
| `devices/virtio/block/device.rs` | 块设备的两种实现之间的分发 | | | [第 27 篇](27-virtio-block.md) |
| `devices/virtio/block/persist.rs` | 两种块设备状态的统一封装 | | ✓ | [第 27 篇](27-virtio-block.md)、[第 72 篇](72-rollback-devices.md) |
| `devices/virtio/block/virtio/device.rs` | virtio-block 本体：队列处理与配置空间 | | | [第 27 篇](27-virtio-block.md) |
| `devices/virtio/block/virtio/request.rs` | 请求头解析与描述符链校验 | | | [第 27 篇](27-virtio-block.md) |
| `devices/virtio/block/virtio/io/sync_io.rs` | 同步 I/O 引擎 | | | [第 27 篇](27-virtio-block.md) |
| `devices/virtio/block/virtio/io/async_io.rs` | io_uring 引擎的适配层 | | | [第 28 篇](28-io-uring-engine.md) |
| `devices/virtio/block/virtio/persist.rs` | virtio-block 的状态保存与恢复 | | ✓ | [第 40 篇](40-device-persist.md)、[第 72 篇](72-rollback-devices.md) |
| `devices/virtio/block/vhost_user/device.rs` | vhost-user 块设备：把数据面交给外部进程 | | | [第 29 篇](29-vhost-user-block.md) |
| `devices/virtio/vhost_user.rs` | vhost-user 协议的消息编解码与握手 | | | [第 29 篇](29-vhost-user-block.md) |
| `devices/virtio/net/device.rs` | virtio-net 的收发路径、offload 与 MMDS 分流 | | ✓ | [第 30 篇](30-virtio-net.md)、[第 72 篇](72-rollback-devices.md) |
| `devices/virtio/net/tap.rs` | tap 设备的打开、特性协商与读写 | | | [第 30 篇](30-virtio-net.md) |
| `devices/virtio/net/persist.rs` | 网卡状态保存；恢复时重新打开 tap | | ✓ | [第 40 篇](40-device-persist.md)、[第 72 篇](72-rollback-devices.md) |
| `devices/virtio/vsock/device.rs` | vsock 设备的三条队列 | | | [第 33 篇](33-vsock.md) |
| `devices/virtio/vsock/packet.rs` | vsock 包头的解析与校验 | | | [第 33 篇](33-vsock.md) |
| `devices/virtio/vsock/csm/connection.rs` | 连接状态机 | | | [第 33 篇](33-vsock.md) |
| `devices/virtio/vsock/unix/muxer.rs` | Unix socket 侧的多路复用与端口映射 | | | [第 33 篇](33-vsock.md) |
| `devices/virtio/balloon/device.rs` | 气球设备：inflate / deflate 与统计队列 | | | [第 34 篇](34-balloon.md) |
| `devices/virtio/balloon/util.rs` | `remove_range()`：按 uffd 与否选择归还页的方式 | | | [第 34 篇](34-balloon.md)、[第 39 篇](39-uffd-backend.md) |
| `devices/virtio/rng/device.rs` | entropy 设备与它的速率限制 | | | [第 35 篇](35-entropy-vmgenid-rate-limiter.md) |
| `devices/virtio/rng/persist.rs` | entropy 状态的保存与恢复 | | ✓ | [第 40 篇](40-device-persist.md)、[第 72 篇](72-rollback-devices.md) |

### 8.3 `io_uring/`、`rate_limiter/`、`dumbo/`、`mmds/`、`logger/`

| 文件 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|
| `io_uring/mod.rs` | `IoUring` 的建立、提交与收割 | | | [第 28 篇](28-io-uring-engine.md) |
| `io_uring/queue/submission.rs`、`queue/completion.rs` | 两个环的 mmap 与索引维护 | | | [第 28 篇](28-io-uring-engine.md) |
| `io_uring/probe.rs`、`restriction.rs` | 内核支持的操作探测与操作限制 | | | [第 28 篇](28-io-uring-engine.md) |
| `io_uring/generated.rs` | bindgen 生成的 io_uring 结构与常量 | | | [第 28 篇](28-io-uring-engine.md) |
| `rate_limiter/mod.rs` | 令牌桶：带宽与 ops 两条独立限制 | | | [第 35 篇](35-entropy-vmgenid-rate-limiter.md) |
| `rate_limiter/persist.rs` | 令牌桶状态的保存与恢复 | | | [第 35 篇](35-entropy-vmgenid-rate-limiter.md) |
| `dumbo/pdu/` | 以太网、ARP、IPv4、TCP、UDP 的报文结构 | | | [第 31 篇](31-dumbo-tcpip-stack.md) |
| `dumbo/tcp/connection.rs` | 极简 TCP 连接状态机 | | | [第 31 篇](31-dumbo-tcpip-stack.md) |
| `dumbo/tcp/endpoint.rs`、`tcp/handler.rs` | HTTP 端点与多连接分发 | | | [第 31 篇](31-dumbo-tcpip-stack.md) |
| `mmds/mod.rs` | MMDS 的 HTTP 处理与版本分支 | | | [第 32 篇](32-mmds.md) |
| `mmds/data_store.rs` | 元数据的 JSON 存储与路径查询 | | | [第 32 篇](32-mmds.md) |
| `mmds/ns.rs` | 网络命名空间：把 dumbo 接到 virtio-net 的分流点 | | | [第 32 篇](32-mmds.md) |
| `mmds/token.rs`、`token_headers.rs` | V2 的 token 签发与校验 | | | [第 32 篇](32-mmds.md) |
| `mmds/persist.rs` | MMDS 数据的快照保存 | | | [第 32 篇](32-mmds.md) |
| `logger/logging.rs` | 日志初始化、级别与输出目标 | | | [第 44 篇](44-logging-and-metrics.md) |
| `logger/metrics.rs` | 全局 metrics 结构与序列化 | | | [第 44 篇](44-logging-and-metrics.md) |

### 8.4 `gdb/` 与 `test_utils/`

两者都不进发布产物：`gdb/` 挂在 `#[cfg(feature = "gdb")]` 下，`test_utils/` 只在测试编译时启用。

| 文件 | 行数 | 内容 | 篇目 |
|---|---|---|---|
| `gdb/target.rs` | 636 | gdbstub 的 target 实现：断点、单步、内存读写 | [第 45 篇](45-gdb-tracing-and-kani.md) |
| `gdb/event_loop.rs` | 159 | 调试会话的事件循环 | [第 45 篇](45-gdb-tracing-and-kani.md) |
| `gdb/arch/x86.rs`、`arch/aarch64.rs` | 472 | 两架构的寄存器映射 | [第 45 篇](45-gdb-tracing-and-kani.md) |
| `test_utils/mod.rs` | 160 | 构造一台可用于测试的 microVM | [第 47 篇](47-testing.md) |

---

## 9. 其余十一个 crate

### 9.1 `firecracker`：主二进制

| 文件 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|
| `src/main.rs` | 参数解析、日志与 metrics 初始化、两种启动模式的分叉 | ✓ | ✓ | [第 07 篇](07-process-startup.md) |
| `build.rs` | 编译期调用 seccompiler，把 BPF 字节码嵌进二进制 | | | [第 42 篇](42-seccomp.md) |
| `src/api_server/mod.rs` | Unix socket 上的 HTTP 服务与请求分发 | ✓ | | [第 08 篇](08-api-server.md) |
| `src/api_server/parsed_request.rs` | 路径与方法到 `VmmAction` 的映射表 | ✓ | ✓ | [第 08 篇](08-api-server.md) |
| `src/api_server/request/` | 每类资源一个文件，负责请求体反序列化与校验 | ✓ | ✓ | [第 08 篇](08-api-server.md) |
| `src/api_server/request/memory.rs` | **e2b 新增**：三个内存查询端点的解析 | ✓ | | [第 50 篇](50-memory-mappings-api.md)、[第 52 篇](52-memory-dirty-api.md) |
| `src/api_server/request/snapshot.rs` | 快照四个端点的解析 | ✓ | ✓ | [第 38 篇](38-snapshot-load.md)、[第 68 篇](68-save-dirty-bitmap-api.md) |
| `src/api_server_adapter.rs` | API 线程与 VMM 线程之间的请求 / 响应通道 | | | [第 09 篇](09-rpc-interface.md) |
| `src/seccomp.rs` | 过滤器的选择：内嵌、外部文件或禁用 | | | [第 42 篇](42-seccomp.md) |
| `src/metrics.rs` | 周期性刷新 metrics 的定时器 | | | [第 44 篇](44-logging-and-metrics.md) |
| `src/generated/prctl.rs` | bindgen 生成的 prctl 常量 | | | — |
| `swagger/firecracker.yaml` | API 的 OpenAPI 描述，CI 校验它与代码一致 | ✓ | ✓ | [第 08 篇](08-api-server.md)、[第 76 篇](76-api-reference.md) |
| `examples/uffd/` | 三个 uffd 处理进程示例与它们共用的 `uffd_utils.rs` | | | [第 39 篇](39-uffd-backend.md) |
| `examples/seccomp/` | 四个用于验证过滤器行为的小程序 | | | [第 42 篇](42-seccomp.md) |

### 9.2 其余十个

| crate / 文件 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|
| `jailer/src/main.rs` | 参数解析与 `exec` 到 firecracker | | | [第 43 篇](43-jailer.md) |
| `jailer/src/env.rs` | 隔离环境的搭建顺序：namespace、chroot、降权 | | | [第 43 篇](43-jailer.md) |
| `jailer/src/chroot.rs` | `chroot` 与 `pivot_root` 的封装 | | | [第 43 篇](43-jailer.md) |
| `jailer/src/cgroup.rs` | cgroup v1 / v2 两套写法 | | | [第 43 篇](43-jailer.md) |
| `jailer/src/resource_limits.rs` | `setrlimit` 的封装 | | | [第 43 篇](43-jailer.md) |
| `seccompiler/src/lib.rs` | JSON 规则到 BPF 指令的编译 | | | [第 42 篇](42-seccomp.md) |
| `seccompiler/src/types.rs` | 过滤器 JSON 的结构定义 | | | [第 42 篇](42-seccomp.md) |
| `seccompiler/src/bindings.rs` | seccomp 与 BPF 的内核常量 | | | [第 42 篇](42-seccomp.md) |
| `acpi-tables/src/aml.rs` | AML 字节码的构造器（2 049 行，该 crate 的主体） | | | [第 17 篇](17-x86-64-platform.md) |
| `acpi-tables/src/{rsdp,xsdt,fadt,madt,dsdt}.rs` | 五张表各自的结构与校验和 | | | [第 17 篇](17-x86-64-platform.md) |
| `snapshot-editor/src/edit_vmstate.rs` | vmstate 的字段编辑与版本查看 | | | [第 41 篇](41-snapshot-tools-and-compat.md) |
| `snapshot-editor/src/edit_memory.rs` | 内存文件的 rebase 与格式转换 | | | [第 41 篇](41-snapshot-tools-and-compat.md) |
| `rebase-snap/src/main.rs` | 把 Diff 内存文件按空洞信息合进基线 | | | [第 41 篇](41-snapshot-tools-and-compat.md) |
| `cpu-template-helper/src/main.rs` | 五个子命令的入口 | | | [第 22 篇](22-aarch64-templates-and-helper.md) |
| `cpu-template-helper/src/template/{dump,strip,verify}/` | 模板的采集、裁剪与校验，各有两架构实现 | | | [第 22 篇](22-aarch64-templates-and-helper.md) |
| `cpu-template-helper/src/utils/mod.rs` | `build_microvm_from_config()`：构建一台不启动的 microVM | ✓ | ✓ | [第 22 篇](22-aarch64-templates-and-helper.md)、[第 46 篇](46-code-organization-and-build.md) |
| `utils/src/arg_parser.rs` | 自己实现的命令行解析器（1 086 行） | | | [第 06 篇](06-build-run-debug.md) |
| `utils/src/time.rs` | 单调时钟与时间戳格式 | | | [第 44 篇](44-logging-and-metrics.md) |
| `utils/src/validators.rs` | 实例 id 等字符串的合法性检查 | | | [第 07 篇](07-process-startup.md) |
| `clippy-tracing/src/main.rs` | 批量增删 `#[instrument]` 的源码改写 | | | [第 45 篇](45-gdb-tracing-and-kani.md) |
| `log-instrument/src/lib.rs` | 宏展开后调用的日志函数 | | | [第 45 篇](45-gdb-tracing-and-kani.md) |
| `log-instrument-macros/src/lib.rs` | 过程宏本体（38 行） | | | [第 45 篇](45-gdb-tracing-and-kani.md) |

`cpu-template-helper/src/utils/mod.rs` 两列都打勾，但两次改动的性质相同且都很小：
`InstanceInfo` 加了字段，这个构造点就要补一行。它是「一个大库加若干薄二进制」这种切法的固定开销。

---

## 10. 源码之外

| 路径 | 内容 | e2b | ARM | 篇目 |
|---|---|---|---|---|
| `resources/seccomp/x86_64-unknown-linux-musl.json` | x86_64 的系统调用白名单 | ✓ | | [第 42 篇](42-seccomp.md)、[第 55 篇](55-seccomp-build-upload-and-upstream-fixes.md) |
| `resources/seccomp/aarch64-unknown-linux-musl.json` | aarch64 的系统调用白名单 | ✓ | ✓ | [第 62 篇](62-aarch64-seccomp-filter.md)、[第 73 篇](73-failure-model-faulted-and-seccomp.md) |
| `resources/seccomp/unimplemented.json` | 占位文件，给未支持架构 | | | [第 42 篇](42-seccomp.md) |
| `resources/guest_configs/` | CI 用的 guest 内核 config，五个架构 / 版本组合 | | | [第 56 篇](56-guest-kernel-requirements-and-e2b-configs.md) |
| `resources/overlay/` | 测试 rootfs 的 init 与网络配置脚本 | | | [第 47 篇](47-testing.md) |
| `resources/rebuild.sh` | 重建 CI 内核与 rootfs | | | [第 06 篇](06-build-run-debug.md) |
| `tests/framework/` | pytest 夹具：`Microvm`、`http_api`、jailer 包装 | ✓ | | [第 47 篇](47-testing.md) |
| `tests/integration_tests/functional/` | 功能测试，最大的一组 | ✓ | | [第 47 篇](47-testing.md) |
| `tests/integration_tests/security/` | 安全测试，e2b 定制版改了其中的漏洞基线 | ✓ | | [第 47 篇](47-testing.md) |
| `tests/integration_tests/{performance,build,style}/` | 性能、构建与风格三组 | | | [第 47 篇](47-testing.md) |
| `tests/data/` | CPU 指纹、模板、MSR 列表等基线数据 | | | [第 47 篇](47-testing.md) |
| `tools/devtool` | 开发容器的入口脚本，本书多数命令的前缀 | | | [第 06 篇](06-build-run-debug.md) |
| `tools/devctr/Dockerfile` | 开发容器镜像 | | | [第 06 篇](06-build-run-debug.md) |
| `tools/release.sh`、`release-prepare.sh`、`release-tag.sh`、`bump-version.sh` | 发布流程的四个脚本 | | | [第 48 篇](48-release-and-compat-policy.md) |
| `tools/bindgen.sh`、`test_bindings.py` | 生成并校验内核头文件绑定 | | | [第 05 篇](05-rust-and-crates-primer.md)、[第 46 篇](46-code-organization-and-build.md) |
| `tools/test.sh` | 单元测试与集成测试的统一入口 | ✓ | | [第 47 篇](47-testing.md) |
| `tools/ab_test.py` | A/B 性能与安全比较 | | | [第 47 篇](47-testing.md) |
| `.buildkite/pipeline_*.py` | 五条 CI 流水线的生成脚本 | | | [第 46 篇](46-code-organization-and-build.md) |
| `docs/` | 上游文档，本书只作参考 | | | [第 48 篇](48-release-and-compat-policy.md) |
| `scripts/build.sh` | **e2b 新增**：musl 静态构建与产物打包 | ✓ | ✓ | [第 55 篇](55-seccomp-build-upload-and-upstream-fixes.md)、[第 58 篇](58-building-and-running-on-aarch64.md) |
| `scripts/upload.sh` | **e2b 新增**：产物上传 | ✓ | | [第 55 篇](55-seccomp-build-upload-and-upstream-fixes.md) |
| `Makefile`、`.tool-versions` | **e2b 新增**：构建入口与工具链版本声明 | ✓ | | [第 55 篇](55-seccomp-build-upload-and-upstream-fixes.md) |

---

## 11. 两层改动的文件清单

前面各表的打勾散在各节，这里合并成两份完整清单，便于升级时逐项核对。
每行的「改了什么」只写一句；展开在对应篇目，文件级的增删行数在[第 78 篇](78-layer-diff-tables.md)。

### 11.1 e2b 定制版触及的 34 个文件

新增 6 个（其中源码文件 2 个），删除 1 个，其余为修改。

| 文件 | 改了什么 | 篇目 |
|---|---|---|
| `src/vmm/src/vstate/vm.rs` | 加内存映射、常驻 / 空页、脏页三组查询的实现 | [第 50 篇](50-memory-mappings-api.md)、[第 51 篇](51-memory-resident-empty-api.md)、[第 52 篇](52-memory-dirty-api.md) |
| `src/vmm/src/utils/pagemap.rs` | 新增：pagemap 与 soft-dirty 位的读取 | [第 52 篇](52-memory-dirty-api.md) |
| `src/vmm/src/utils/mod.rs` | 声明上面这个模块 | [第 52 篇](52-memory-dirty-api.md) |
| `src/vmm/src/rpc_interface.rs` | 加三个 `VmmAction` 变体与它们的路由 | [第 50 篇](50-memory-mappings-api.md) |
| `src/vmm/src/lib.rs` | 加对应的 `Vmm` 方法与 uffd 写保护开关 | [第 52 篇](52-memory-dirty-api.md)、[第 53 篇](53-uffd-write-protection.md) |
| `src/vmm/src/persist.rs` | 可选 memfile 的快照分支；uffd 写保护的注册 | [第 53 篇](53-uffd-write-protection.md)、[第 54 篇](54-optional-memfile-snapshot.md) |
| `src/vmm/src/vmm_config/snapshot.rs` | `mem_file_path` 变为可选 | [第 54 篇](54-optional-memfile-snapshot.md) |
| `src/vmm/src/vmm_config/instance_info.rs` | 加内存区域字段 | [第 51 篇](51-memory-resident-empty-api.md) |
| `src/vmm/Cargo.toml` | 换到带写保护支持的 userfaultfd 依赖 | [第 53 篇](53-uffd-write-protection.md) |
| `Cargo.lock` | 随上一行更新 | [第 53 篇](53-uffd-write-protection.md) |
| `src/firecracker/src/api_server/request/memory.rs` | 新增：三个端点的请求解析 | [第 50 篇](50-memory-mappings-api.md) |
| `src/firecracker/src/api_server/request/mod.rs` | 声明上面这个模块 | [第 50 篇](50-memory-mappings-api.md) |
| `src/firecracker/src/api_server/parsed_request.rs` | 把三个路径接进路由表 | [第 50 篇](50-memory-mappings-api.md) |
| `src/firecracker/src/api_server/mod.rs` | 放行 GET 带查询串的请求 | [第 50 篇](50-memory-mappings-api.md) |
| `src/firecracker/src/api_server/request/snapshot.rs` | 适配可选 memfile | [第 54 篇](54-optional-memfile-snapshot.md) |
| `src/firecracker/src/main.rs` | `InstanceInfo` 构造点补字段 | [第 51 篇](51-memory-resident-empty-api.md) |
| `src/firecracker/swagger/firecracker.yaml` | 补三个端点与改动的字段 | [第 76 篇](76-api-reference.md) |
| `src/cpu-template-helper/src/utils/mod.rs` | `InstanceInfo` 构造点补字段 | [第 46 篇](46-code-organization-and-build.md) |
| `resources/seccomp/x86_64-unknown-linux-musl.json` | 放行 pagemap 与写保护需要的系统调用 | [第 55 篇](55-seccomp-build-upload-and-upstream-fixes.md) |
| `resources/seccomp/aarch64-unknown-linux-musl.json` | 同上 | [第 55 篇](55-seccomp-build-upload-and-upstream-fixes.md) |
| `scripts/build.sh`、`scripts/upload.sh`、`Makefile`、`.tool-versions`、`.gitignore` | 新增的构建与发布入口 | [第 55 篇](55-seccomp-build-upload-and-upstream-fixes.md) |
| `tools/test.sh`、`tests/framework/http_api.py`、`tests/integration_tests/` 下 5 个文件、`src/vmm/tests/integration_tests.rs` | 新端点的测试与合入的上游测试修复 | [第 55 篇](55-seccomp-build-upload-and-upstream-fixes.md) |
| `.github/workflows/dependency_modification_check.yml` | 删除：分叉后这条检查不再适用 | [第 55 篇](55-seccomp-build-upload-and-upstream-fixes.md) |

### 11.2 ARM 适配版触及的 28 个文件

分两段：构建与运行部分改了 2 个文件，checkpoint / restore 扩展改了 27 个（其中新增 1 个）。

| 文件 | 改了什么 | 篇目 |
|---|---|---|
| `scripts/build.sh` | aarch64 的目标三元组与工具链 | [第 58 篇](58-building-and-running-on-aarch64.md) |
| `src/firecracker/src/main.rs` | aarch64 构建修复；后又加 HDBSS 相关的启动处理 | [第 58 篇](58-building-and-running-on-aarch64.md)、[第 66 篇](66-hdbss.md) |
| `src/vmm/src/rollback.rs` | 新增 656 行：原地回滚的全部阶段与脏位图落盘 | [第 69 篇](69-rollback-api-and-phases.md) |
| `src/vmm/src/vstate/vm.rs` | 脏页跟踪后端的抽象与 HDBSS 分支 | [第 65 篇](65-dirty-tracking-backend.md) |
| `src/vmm/src/arch/aarch64/vm.rs` | HDBSS 的能力探测与使能 | [第 66 篇](66-hdbss.md) |
| `src/vmm/src/vstate/memory.rs` | 脏位图 sidecar 的读写与回滚时的内存写回 | [第 67 篇](67-dirty-bitmap-sidecar.md)、[第 70 篇](70-rollback-memory.md) |
| `src/vmm/src/vstate/vcpu.rs` | 回滚时 vCPU 的暂停、reinit 与状态重灌 | [第 71 篇](71-rollback-vcpu-and-gic.md) |
| `src/vmm/src/arch/aarch64/vcpu.rs` | aarch64 vCPU 的 reinit 路径 | [第 71 篇](71-rollback-vcpu-and-gic.md) |
| `src/vmm/src/arch/x86_64/vcpu.rs` | 对齐同名接口，使两架构都能编过 | [第 71 篇](71-rollback-vcpu-and-gic.md) |
| `src/vmm/src/builder.rs` | 启动时按环境变量选择脏页跟踪后端 | [第 65 篇](65-dirty-tracking-backend.md) |
| `src/vmm/src/lib.rs` | 回滚入口与 `Faulted` 状态的进入 | [第 69 篇](69-rollback-api-and-phases.md)、[第 73 篇](73-failure-model-faulted-and-seccomp.md) |
| `src/vmm/src/persist.rs` | 创建快照时写出脏位图 sidecar | [第 67 篇](67-dirty-bitmap-sidecar.md) |
| `src/vmm/src/rpc_interface.rs` | 两个新 `VmmAction` 与 `Faulted` 下的请求拒绝 | [第 68 篇](68-save-dirty-bitmap-api.md)、[第 73 篇](73-failure-model-faulted-and-seccomp.md) |
| `src/vmm/src/vmm_config/snapshot.rs` | `dirty_bitmap_path` 与回滚参数 | [第 67 篇](67-dirty-bitmap-sidecar.md)、[第 69 篇](69-rollback-api-and-phases.md) |
| `src/vmm/src/vmm_config/instance_info.rs` | 加 `Faulted` 状态 | [第 73 篇](73-failure-model-faulted-and-seccomp.md) |
| `src/vmm/src/devices/virtio/persist.rs` | 队列状态的回滚 | [第 72 篇](72-rollback-devices.md) |
| `src/vmm/src/devices/virtio/block/persist.rs`、`block/virtio/persist.rs` | 块设备状态的回滚 | [第 72 篇](72-rollback-devices.md) |
| `src/vmm/src/devices/virtio/net/device.rs`、`net/persist.rs` | 网卡状态的回滚与 tap 的处理 | [第 72 篇](72-rollback-devices.md) |
| `src/vmm/src/devices/virtio/rng/persist.rs` | entropy 状态的回滚 | [第 72 篇](72-rollback-devices.md) |
| `src/vmm/src/devices/acpi/vmgenid.rs` | 回滚后更新世代 id | [第 72 篇](72-rollback-devices.md) |
| `src/firecracker/src/api_server/parsed_request.rs`、`request/snapshot.rs` | 两个新端点的路由与解析 | [第 68 篇](68-save-dirty-bitmap-api.md)、[第 69 篇](69-rollback-api-and-phases.md) |
| `src/firecracker/swagger/firecracker.yaml` | 补两个新端点 | [第 76 篇](76-api-reference.md) |
| `src/cpu-template-helper/src/utils/mod.rs` | `InstanceInfo` 构造点补字段 | [第 46 篇](46-code-organization-and-build.md) |
| `resources/seccomp/aarch64-unknown-linux-musl.json` | 放行回滚路径用到的系统调用 | [第 73 篇](73-failure-model-faulted-and-seccomp.md) |
| `src/vmm/tests/integration_tests.rs` | 随接口变化调整 | [第 47 篇](47-testing.md) |

两层都触及的文件共十四个：`src/vmm/src/lib.rs`、`persist.rs`、`rpc_interface.rs`、
`vstate/vm.rs`、`vmm_config/snapshot.rs`、`vmm_config/instance_info.rs`、
`src/firecracker/src/main.rs`、`src/firecracker/src/api_server/parsed_request.rs`、
`src/firecracker/src/api_server/request/snapshot.rs`、`src/firecracker/swagger/firecracker.yaml`、
`src/vmm/tests/integration_tests.rs`，以及 `src/cpu-template-helper/src/utils/mod.rs` 与
`resources/seccomp/aarch64-unknown-linux-musl.json`、`scripts/build.sh`。
升级上游时，这些文件的冲突解决要按「先 e2b 后 ARM」的顺序做，反过来会丢掉第一层的语义。

---

## 12. 小结

- 上游 v1.12.1 的 Rust 代码在十二个 crate 里，`vmm` 一个占八成；其余十一个要么是薄的可执行入口，要么是单一用途的库。
- `vmm` 内部按控制面、状态面、机器面、数据面读最省力：控制面回答「请求怎么变成动作」，
  状态面回答「状态怎么落盘与回来」，机器面回答「KVM 与平台细节在哪」，数据面回答「I/O 怎么走」。
- 文件行数只能用来判断大小，不能当复杂度：单元测试与被测代码同文件，很多文件一半是测试。
- virtio 设备目录有固定的四文件套路（`device.rs` / `event_handler.rs` / `persist.rs` / `metrics.rs`），
  认出它就能在任意设备下快速定位。
- e2b 定制版触及 34 个文件，集中在 `vstate/vm.rs`、`persist.rs`、`rpc_interface.rs` 与 API 解析层；
  新增文件只有 `utils/pagemap.rs` 与 `api_server/request/memory.rs` 两个源码文件。
- ARM 适配版在它迁入的 e2b 提交之上再触及 28 个文件，新增文件只有 `src/vmm/src/rollback.rs` 一个，
  其余是把回滚钩子接进已有的设备与 vCPU 代码。
- 十二个文件被两层先后改过，升级上游时必须按「先 e2b 后 ARM」的顺序重放。

---

## 延伸阅读 / 下一篇

- [第 01 篇 · 三层版本谱系与仓库地图](01-lineage-and-repo-map.md)：本篇的叙述版，讲每层改了多少、为什么。
- [第 46 篇 · 代码组织、依赖与构建](46-code-organization-and-build.md)：crate 之间的依赖方向与构建约束。
- [第 78 篇 · 三层差异总表](78-layer-diff-tables.md)：同样的文件清单，但带增删行数与升级重放清单。
- [第 79 篇 · 阅读上游代码的方法与常见问题](79-reading-upstream-code.md)：从一个 API 路径追到执行代码的具体走法。
- 下一篇：[第 76 篇 · API 端点总表](76-api-reference.md)。
