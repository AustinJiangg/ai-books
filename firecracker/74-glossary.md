# 74 · 术语表

> 这本书里的名词来自四个互不相同的来源：KVM 的接口、virtio 规范、Firecracker 自己的类型名，
> 以及两层定制加进来的概念。同一个词在不同来源下往往指不同的东西 —— 「脏页位图」既可能指 KVM 日志，
> 也可能指用户态位图，还可能指写进磁盘的 FCDB 文件。本篇把全书用到的术语按主题列成八张表，
> 每条给出中文、英文、一句话定义与首次系统介绍它的篇目。
>
> **读者**：查阅者，以及读到某个词想不起它属于哪一层的读者。
> **预备**：无。　**代码**：本篇不引用代码，代码位置见各条目指向的篇目。

---

## 0. 本篇要回答的问题

1. 某个术语的固定中文译法是什么，全书哪一篇负责讲它？
2. 一个名词属于哪一层 —— KVM 的、virtio 规范的、Firecracker 的、还是两层定制新造的？
3. 几组容易混淆的词（脏页位图 / 位图 sidecar、内存文件 / 状态文件、快照恢复 / 原地回滚、
   写保护式跟踪 / 硬件脏页跟踪）各自指什么，边界在哪？
4. 三层版本称谓分别指哪一份代码？

### 0.1 怎么用这张表

- **分组**：八张表按主题分 —— 虚拟化与 KVM、进程结构与控制面、guest 内存与脏页、设备与 virtio、
  快照与回滚、安全与构建、架构相关、版本与部署。同一个词只在最贴近它来源的那张表里出现一次。
- **排序**：每张表内按英文名的字母序排列，忽略大小写与下划线；以 `/` 开头的 API 路径按去掉斜杠后的首字母排。
- **「首次出现」列**：指**实质引入该术语并给出定义**的篇目，不是全书第一次出现这个字符串的地方。
  第 01 篇的仓库地图、第 02 篇的取舍清单与各篇题注里的代码文件列表会提前点到很多名字，
  那些地方不计入本列。
- **固定译法**：[`STYLE.md`](STYLE.md) 第三节列出的术语，本表沿用同一套中文写法；本表是它的超集。
- 标识符（类型名、函数名、字段名、文件名、API 路径）在全书一律保持英文原样，本表给出的中文只是读法，
  不用于替换代码里的名字。

---

## 1. 虚拟化与 KVM

| 中文 | 英文 | 一句话定义 | 首次出现 |
|---|---|---|---|
| 客户机物理地址 | GPA（guest physical address） | guest 眼中的物理地址，由 memslot 映射到宿主虚拟地址 | [第 03 篇](03-kvm-api-primer.md) |
| 客户机 | guest | 跑在 microVM 里的操作系统与其上的负载，对 VMM 而言完全不可信 | [第 02 篇](02-microvm-design-tradeoffs.md) |
| 宿主机 | host | 运行 Firecracker 进程的那台机器与它的内核 | [第 02 篇](02-microvm-design-tradeoffs.md) |
| 宿主虚拟地址 | HVA（host virtual address） | guest 内存在 Firecracker 进程地址空间里的地址，`mmap` 的返回值 | [第 03 篇](03-kvm-api-primer.md) |
| I/O 事件描述符 | ioeventfd | 把 guest 对某个地址的写变成一次 eventfd 通知，在 KVM 内部结束，不退出到用户态 | [第 03 篇](03-kvm-api-primer.md) |
| 中断控制器对象 | irqchip | x86_64 上由 `KVM_CREATE_IRQCHIP` 在内核里建立的 PIC 与 IOAPIC | [第 03 篇](03-kvm-api-primer.md) |
| 中断注入描述符 | irqfd | 写一次 eventfd 即向 guest 注入一条中断，不经过 ioctl | [第 03 篇](03-kvm-api-primer.md) |
| 内核虚拟机 | KVM | Linux 内核里的虚拟化子系统，Firecracker 全部虚拟化能力的来源 | [第 03 篇](03-kvm-api-primer.md) |
| KVM 能力 | KVM capability（`KVM_CAP_*`） | 一项可查询的内核虚拟化特性；Firecracker 启动时检查一张固定清单，缺一项即拒绝启动 | [第 03 篇](03-kvm-api-primer.md) |
| KVM 内核绑定 | kvm-bindings | 由 bindgen 从内核头文件生成的 Rust 结构体与常量 crate | [第 05 篇](05-rust-and-crates-primer.md) |
| KVM ioctl 封装 | kvm-ioctls | 把 KVM 的 ioctl 包成类型安全 Rust 方法的 crate | [第 05 篇](05-rust-and-crates-primer.md) |
| 取脏页日志 | `KVM_GET_DIRTY_LOG` | 取走一个 memslot 的脏页位图并同时清零，没有单独的清零接口 | [第 03 篇](03-kvm-api-primer.md) |
| 运行 vCPU | `KVM_RUN` | 让一个 vCPU 开始执行 guest 代码的 ioctl，guest 运行期间不返回 | [第 03 篇](03-kvm-api-primer.md) |
| 内存槽位 | memslot（KVM memory slot） | 一条「GPA 区间 → HVA」的登记；槽位号等于内存区域序号 | [第 03 篇](03-kvm-api-primer.md) |
| 微型虚拟机 | microVM | 只有极少数设备、没有固件、专为快启动与高密度设计的虚拟机 | [第 02 篇](02-microvm-design-tradeoffs.md) |
| 内存映射 I/O | MMIO（memory-mapped I/O） | 设备寄存器落在物理地址空间里，guest 用普通访存指令访问 | [第 02 篇](02-microvm-design-tradeoffs.md) |
| 端口 I/O | PIO（port I/O） | x86 专有的独立 I/O 地址空间，Firecracker 只用于串口与 i8042 | [第 15 篇](15-vcpu-threads-and-state-machine.md) |
| 二阶段页表 | stage-2 translation | ARM 的 GPA 到宿主物理地址的硬件翻译层，写保护式脏页跟踪与 HDBSS 都作用在这里 | [第 66 篇](66-hdbss.md) |
| vCPU | vCPU | 一个被虚拟化的处理器；在 Firecracker 里对应一个 fd 加一个 OS 线程 | [第 03 篇](03-kvm-api-primer.md) |
| 虚拟化宿主扩展 | VHE（virtualization host extensions） | ARM 的宿主模式扩展，鲲鹏上启用硬件脏页跟踪的前提之一 | [第 60 篇](60-kunpeng-openeuler-host.md) |
| 虚拟机退出 | VM exit | guest 因某个原因把控制权交回 KVM 或用户态；`KVM_RUN` 由此返回 | [第 15 篇](15-vcpu-threads-and-state-machine.md) |
| VM 文件描述符 | VM fd | KVM 三级 fd 的中间一级，管内存注册、中断与建 vCPU | [第 03 篇](03-kvm-api-primer.md) |
| 虚拟机监控器 | VMM（virtual machine monitor） | 用户态里负责建机、模拟设备与管理生命周期的进程，本书里就是 Firecracker | [第 02 篇](02-microvm-design-tradeoffs.md) |

---

## 2. 进程结构与控制面

| 中文 | 英文 | 一句话定义 | 首次出现 |
|---|---|---|---|
| API 服务器 | API server | 跑在 Unix socket 上的 HTTP/1.1 子集，把请求翻译成一个 `VmmAction` | [第 08 篇](08-api-server.md) |
| 建机函数 | builder | `builder.rs` 里把 `VmResources` 变成一台运行中 microVM 的那条流水线 | [第 11 篇](11-builder.md) |
| 控制面 | control plane | API server 加 `rpc_interface`，负责配置与生命周期动作 | [第 08 篇](08-api-server.md) |
| 数据面 | data plane | 设备的 I/O 路径：virtqueue、事件处理器与后端 | [第 25 篇](25-virtio-device-model-and-transport.md) |
| 事件管理器 | EventManager | 封装 epoll 的分发器；`run()` 做一次 `epoll_wait` 加一轮分发 | [第 12 篇](12-vmm-event-loop-and-exit.md) |
| 事件循环 | event loop | VMM 线程上那个反复调用 `EventManager::run()` 的循环 | [第 12 篇](12-vmm-event-loop-and-exit.md) |
| 错误消息字段 | `fault_message` | HTTP 错误响应体里的说明字符串，由错误枚举的文档注释生成 | [第 08 篇](08-api-server.md) |
| 故障状态 | `Faulted` | ARM 适配版新增的 microVM 状态：回滚越过提交点后失败，机器不可信也不可恢复 | [第 73 篇](73-failure-model-faulted-and-seccomp.md) |
| 退出码 | `FcExitCode` | 进程退出码的枚举，例如 seccomp 违规是 148 | [第 07 篇](07-process-startup.md) |
| 实例信息 | `InstanceInfo` | `GET /` 返回的实例 id、状态与版本；ARM 适配版在其中加了 `dirty_tracking` | [第 09 篇](09-rpc-interface.md) |
| 内置 HTTP 库 | micro_http | 项目自己维护的最小 HTTP 实现，用来压缩依赖与系统调用面 | [第 08 篇](08-api-server.md) |
| 事件订阅者 | `MutEventSubscriber` | 向事件管理器注册 fd 并在事件到来时被回调的对象 | [第 12 篇](12-vmm-event-loop-and-exit.md) |
| 无 API 模式 | `--no-api` | 不起 API 线程的单线程形态，代价是没有暂停与快照 | [第 06 篇](06-build-run-debug.md) |
| panic 钩子 | panic hook | `panic = "abort"` 下崩溃前最后执行的代码，负责恢复终端并刷出 metrics | [第 07 篇](07-process-startup.md) |
| 启动前阶段 | Preboot | microVM 尚未建起的阶段，动作作用在 `VmResources` 上 | [第 09 篇](09-rpc-interface.md) |
| 运行期阶段 | Runtime | microVM 已建起之后的阶段，动作作用在 `Arc<Mutex<Vmm>>` 上 | [第 09 篇](09-rpc-interface.md) |
| 动作分派层 | `rpc_interface` | 判断某个动作在当前阶段是否允许、该交给谁执行的唯一落点 | [第 09 篇](09-rpc-interface.md) |
| 接口规格文件 | swagger | `firecracker.yaml`，对外的 API 契约；由发布流程校验，但不参与编译 | [第 08 篇](08-api-server.md) |
| 暂停 / 恢复 | pause / resume | `PATCH /vm` 的两个动作：停住全部 vCPU，或放它们继续跑 | [第 09 篇](09-rpc-interface.md) |
| VMM 结构 | `Vmm` | 运行期的句柄清单：KVM 对象、vCPU 句柄、设备管理器、guest 内存与 uffd | [第 12 篇](12-vmm-event-loop-and-exit.md) |
| 动作枚举 | `VmmAction` | VMM 的全部对外语义，API 线程与 VMM 线程之间传的就是它 | [第 09 篇](09-rpc-interface.md) |
| 返回数据枚举 | `VmmData` | 动作成功时回给 API 线程的数据，例如机器配置或内存位图 | [第 09 篇](09-rpc-interface.md) |
| 资源模型 | `VmResources` | 启动前累积配置的对象；其中五个设备在配置时就已被构造出来 | [第 10 篇](10-vm-resources-and-config.md) |
| 虚机状态 | `VmState` | `Uninitialized` / `Running` / `Paused`，ARM 适配版另加 `Faulted` | [第 09 篇](09-rpc-interface.md) |

---

## 3. guest 内存与脏页

| 中文 | 英文 | 一句话定义 | 首次出现 |
|---|---|---|---|
| 匿名映射 | anonymous mapping | 不带文件后备的 `mmap`，guest 内存的默认形态 | [第 13 篇](13-guest-memory.md) |
| 脏页位图 | dirty bitmap | 记录哪些页被写过的位图；KVM 侧与用户态侧各有一张，语义不同 | [第 14 篇](14-dirty-page-tracking.md) |
| 脏页 | dirty page | 自上一次基线以来被写过的页 | [第 14 篇](14-dirty-page-tracking.md) |
| 位图 sidecar | dirty bitmap sidecar（`dirty_bitmap_path`） | 创建快照时顺带写出的 FCDB 文件，说明本轮写了哪些页 | [第 67 篇](67-dirty-bitmap-sidecar.md) |
| 脏页跟踪后端 | `DirtyTrackingBackend` | `Off` / `KvmWriteProtect` / `Hdbss` 三选一的采集方式，输出统一汇入 KVM 位图 | [第 65 篇](65-dirty-tracking-backend.md) |
| 导出脏页 | `dump_dirty()` | 按「KVM 脏或用户态脏」逐页判定，把连续脏页攒成批次写进内存文件 | [第 37 篇](37-snapshot-create.md) |
| 零页位图 | empty bitmap | `GET /memory` 返回的第二张位图，标出内容全为零的页 | [第 51 篇](51-memory-resident-empty-api.md) |
| 脏位图文件格式 | FCDB | 24 字节头（魔数、版本、页大小、页数）加位图字的文件格式 | [第 67 篇](67-dirty-bitmap-sidecar.md) |
| 扁平页序 | flat page order | 各内存区域首尾相接的页编号空间；三个内存端点与 FCDB 都用它，不是 GPA | [第 50 篇](50-memory-mappings-api.md) |
| guest 内存对象 | `GuestMemoryMmap` | Firecracker 侧表示 guest 物理内存的类型，脏页位图是它的类型参数 | [第 13 篇](13-guest-memory.md) |
| 硬件脏页跟踪 | HDBSS（hardware dirty bit state structure） | 鲲鹏 950 的扩展：由 MMU 把被写的 GPA 追加进每 vCPU 的缓冲区，免去写保护 | [第 66 篇](66-hdbss.md) |
| 大页 | huge pages（HugeTLB） | 2 MiB 页后备的 guest 内存；与 balloon 互斥，恢复只能走 uffd | [第 13 篇](13-guest-memory.md) |
| 释放页建议 | `MADV_DONTNEED` | balloon inflate 用来真正归还宿主内存的 `madvise` 操作 | [第 34 篇](34-balloon.md) |
| 匿名共享文件 | memfd | 无名的内存文件，配了 vhost-user 块设备时用作 guest 内存后备 | [第 13 篇](13-guest-memory.md) |
| 内存区域 | memory region | guest 物理地址空间的一段连续内存，一个区域对应一个 memslot | [第 13 篇](13-guest-memory.md) |
| 常驻判定 | `mincore` | 查询一段映射里哪些页已有物理后备的系统调用 | [第 51 篇](51-memory-resident-empty-api.md) |
| 缺页 | page fault | 访问尚无物理后备的页；uffd 后端把它变成一条送给外部进程的事件 | [第 39 篇](39-uffd-backend.md) |
| 页表映射文件 | pagemap（`/proc/self/pagemap`） | 每页一条 64 位条目，bit 63 为 present、bit 57 为 uffd 写保护位 | [第 52 篇](52-memory-dirty-api.md) |
| 常驻页 | resident page | 已有物理后备的页；`GET /memory` 的第一张位图标的就是它 | [第 51 篇](51-memory-resident-empty-api.md) |
| 写回脏页 | `restore_dirty()` | 回滚时按位图把内存文件里的页读回 guest 内存，与 `dump_dirty()` 对称 | [第 70 篇](70-rollback-memory.md) |
| 回填 KVM 位 | `store_dirty_bitmap()` | 把取走的 KVM 脏位折叠进用户态位图，避免信息因一次失败而永久丢失 | [第 14 篇](14-dirty-page-tracking.md) |
| 脏页跟踪开关 | `track_dirty_pages` | `machine-config` 的字段，同时决定用户态位图是否存在与 memslot 是否带脏页日志标志 | [第 14 篇](14-dirty-page-tracking.md) |
| 用户态缺页 | userfaultfd（uffd） | 把缺页交给用户态进程处理的内核机制，快照恢复的第二种内存后端 | [第 39 篇](39-uffd-backend.md) |
| 填页操作 | `UFFDIO_COPY` | uffd 处理器把一段内容写进缺页区域的 ioctl，可带写保护模式 | [第 39 篇](39-uffd-backend.md) |
| 写保护 | write protect（WP） | 把页标成只读以便捕获写；uffd 的异步写保护（`WP_ASYNC`）由内核清位、不通知用户态 | [第 53 篇](53-uffd-write-protection.md) |

---

## 4. 设备与 virtio

| 中文 | 英文 | 一句话定义 | 首次出现 |
|---|---|---|---|
| 可用环 | available ring | 驱动写、设备读的环，登记待处理的描述符链首 | [第 04 篇](04-virtio-and-mmio-primer.md) |
| 气球设备 | balloon | 由 guest 驱动配合归还内存的 virtio 设备，建立在驱动可信之上 | [第 34 篇](34-balloon.md) |
| 启动计时设备 | boot timer | 只认一个魔法字节的伪设备，用来测量启动时延 | [第 24 篇](24-legacy-devices.md) |
| 设备总线 | `Bus` | 按起址排序的地址到设备映射表，负责把一次 MMIO 访问分派到设备对象 | [第 23 篇](23-bus-and-mmio-device-manager.md) |
| 配置区 | config space | virtio 设备暴露给驱动的只读或可读写参数区，例如块设备的扇区数 | [第 25 篇](25-virtio-device-model-and-transport.md) |
| 描述符链 | descriptor chain | 由描述符表里若干项串成的一次 I/O 请求，是设备处理的基本单位 | [第 04 篇](04-virtio-and-mmio-primer.md) |
| 设备激活 | device activation | 驱动写 `DRIVER_OK` 的那一刻，设备拿到 guest 内存句柄并开始工作 | [第 25 篇](25-virtio-device-model-and-transport.md) |
| 驱动就绪位 | `DRIVER_OK` | 状态寄存器里的最后一位，置位即触发激活 | [第 04 篇](04-virtio-and-mmio-primer.md) |
| 内建网络栈 | dumbo | 只为 MMDS 服务的极简 TCP/IP 实现，不注册事件源 | [第 31 篇](31-dumbo-tcpip-stack.md) |
| 键盘控制器 | i8042 | x86_64 上只认五条命令的 legacy 设备，复位事件与 vCPU 退出事件共用一个 eventfd | [第 24 篇](24-legacy-devices.md) |
| 异步 I/O 引擎 | io_uring | 块设备的第二种引擎，把已排好的请求并发交给宿主块设备，零拷贝 | [第 28 篇](28-io-uring-engine.md) |
| 分散聚集缓冲 | `IoVecBuffer` / iovec | 把描述符链翻译成能直接交给 `readv` / `writev` 的数组 | [第 26 篇](26-virtqueue-implementation.md) |
| 双端环形缓冲 | `IovDeque` | 用 memfd 加两次 `MAP_FIXED` 让跨环尾的元素仍能取出连续切片 | [第 26 篇](26-virtqueue-implementation.md) |
| 补发队列通知 | `kick_devices()` | resume 与快照恢复的第一步，补回暂停期间可能丢失的队列通知 | [第 23 篇](23-bus-and-mmio-device-manager.md) |
| legacy 设备 | legacy device | 串口、i8042、RTC 与 boot timer 四个非 virtio 设备 | [第 24 篇](24-legacy-devices.md) |
| 元数据服务 | MMDS（microVM metadata service） | 在网卡 TX 路径上按帧头拦截、由 dumbo 应答的 guest 元数据服务 | [第 32 篇](32-mmds.md) |
| MMIO 设备管理器 | `MMIODeviceManager` | 管理设备的 MMIO 地址、中断号与元信息记录，快照恢复时按原址复位 | [第 23 篇](23-bus-and-mmio-device-manager.md) |
| 传输层 | `MmioTransport` | 实现 virtio-mmio 寄存器语义的那一层，把寄存器读写翻译成对设备 trait 的调用 | [第 25 篇](25-virtio-device-model-and-transport.md) |
| 通知抑制 | notification suppression（`VIRTIO_RING_F_EVENT_IDX`） | 两端各写一个计数器以压掉不必要的 kick 与中断 | [第 04 篇](04-virtio-and-mmio-primer.md) |
| 速率限制器 | rate limiter | 带宽与 ops 两个维度的令牌桶，被动补充、靠 timerfd 解闸 | [第 35 篇](35-entropy-vmgenid-rate-limiter.md) |
| 资源分配器 | `ResourceAllocator` | 分配 MMIO 地址与 GSI 中断号；它的状态不进快照 | [第 23 篇](23-bus-and-mmio-device-manager.md) |
| 实时时钟 | RTC | aarch64 上的 PL031 墙上时钟，不实现中断 | [第 24 篇](24-legacy-devices.md) |
| 串口 | serial | 输出走非阻塞 stdout、输入靠一条 eventfd 背压回路的 legacy 设备 | [第 24 篇](24-legacy-devices.md) |
| tap 设备 | tap | 宿主上的虚拟网卡，virtio-net 的后端 | [第 30 篇](30-virtio-net.md) |
| 已用环 | used ring | 设备写、驱动读的环，登记已完成的描述符链与写入长度 | [第 04 篇](04-virtio-and-mmio-primer.md) |
| 外部设备后端 | vhost-user | 把 virtqueue 的处理交给另一个进程，数据面完全绕过 Firecracker | [第 29 篇](29-vhost-user-block.md) |
| 半虚拟化设备规范 | virtio | 用共享内存里的环取代硬件模拟的设备契约 | [第 04 篇](04-virtio-and-mmio-primer.md) |
| 块设备 | virtio-block | 把宿主上的一个普通文件变成 guest 眼里一块盘的 virtio 设备 | [第 27 篇](27-virtio-block.md) |
| MMIO 传输 | virtio-mmio | virtio 的 MMIO 传输方式，每设备占 4 KiB 一页、一条中断线 | [第 04 篇](04-virtio-and-mmio-primer.md) |
| 网卡 | virtio-net | 收发两个方向不对称的 virtio 网络设备，后端是 tap | [第 30 篇](30-virtio-net.md) |
| 熵源设备 | virtio-rng（entropy） | 把宿主随机数经一条队列递给 guest 的设备，同样受限流约束 | [第 35 篇](35-entropy-vmgenid-rate-limiter.md) |
| 队列 | virtqueue | 描述符表、可用环、已用环三块共享内存构成的数据通道 | [第 04 篇](04-virtio-and-mmio-primer.md) |
| 虚机世代 id | vmgenid | 一个「你被复制了」的信号设备，恢复时写入新值并发出通知 | [第 35 篇](35-entropy-vmgenid-rate-limiter.md) |
| 套接字设备 | vsock | 宿主与 guest 之间的套接字通道，由 unix muxer 收敛成一个 fd | [第 33 篇](33-vsock.md) |

---

## 5. 快照、恢复与原地回滚

| 中文 | 英文 | 一句话定义 | 首次出现 |
|---|---|---|---|
| 二进制序列化 | bincode | 状态文件用的紧密编码，不带字段信息，因此结构一改就要抬快照主版本 | [第 36 篇](36-snapshot-overview-and-format.md) |
| 提交点 | commit point | 回滚流程里「开始写内存」那一刻；越过它之后失败不可撤销 | [第 69 篇](69-rollback-api-and-phases.md) |
| 恢复构造参数 | `ConstructorArgs` | 恢复设备时由调用方现场提供的、不能序列化的上下文 | [第 40 篇](40-device-persist.md) |
| 校验和 | CRC64 | 状态文件末尾的校验值，覆盖魔数、版本与状态段；内存文件没有校验和 | [第 36 篇](36-snapshot-overview-and-format.md) |
| 设备状态集合 | `DeviceStates` | 快照里按设备类型分字段存放的设备状态，加一种设备就要抬主版本 | [第 40 篇](40-device-persist.md) |
| 差分快照 | Diff snapshot | 内存文件只含本轮脏页的稀疏文件；要求脏页跟踪已开启 | [第 36 篇](36-snapshot-overview-and-format.md) |
| 全量快照 | Full snapshot | 内存文件含全部 guest 内存，充当差分链的基线 | [第 36 篇](36-snapshot-overview-and-format.md) |
| 原地回滚 | in-place rollback | `PUT /snapshot/rollback`：保住进程与全部宿主资源，只把偏离的部分写回 | [第 69 篇](69-rollback-api-and-phases.md) |
| 内存文件 | memfile | 快照里存放 guest 内存的产物，各区域按顺序平铺，不复现 MMIO 空洞 | [第 36 篇](36-snapshot-overview-and-format.md) |
| 快照状态结构 | `MicrovmState` | 状态文件里的顶层结构，六个字段涵盖除 guest 内存以外的全部进程内状态 | [第 36 篇](36-snapshot-overview-and-format.md) |
| 持久化契约 | `Persist` trait | 规定每个可快照部件的形状：一个可序列化的 `State` 加一组恢复参数 | [第 40 篇](40-device-persist.md) |
| 差分合并工具 | rebase-snap | 把 Diff 内存文件合进基线的旧工具，已被 `snapshot-editor` 取代 | [第 41 篇](41-snapshot-tools-and-compat.md) |
| 累计回退位图 | `revert_bitmap_path` | 回滚请求里的可选字段，补的是更早轮次的累计脏页 | [第 69 篇](69-rollback-api-and-phases.md) |
| 取脏位图端点 | `PUT /snapshot/save-dirty-bitmap` | 只取脏页集合、不导出内存的端点，读完立刻折叠进用户态位图 | [第 68 篇](68-save-dirty-bitmap-api.md) |
| 快照 | snapshot | 状态文件加内存文件两件产物；磁盘不在其中 | [第 36 篇](36-snapshot-overview-and-format.md) |
| 快照编辑工具 | snapshot-editor | 读改快照的独立二进制：合并内存、改设备状态、删 aarch64 寄存器 | [第 41 篇](41-snapshot-tools-and-compat.md) |
| 快照格式版本 | snapshot format version | 独立于二进制版本的编号，v1.12.1 是 6.0.0，检查规则是主版本相等且次版本不超过 | [第 36 篇](36-snapshot-overview-and-format.md) |
| 稀疏文件 | sparse file | 有洞的文件；Diff 内存文件用洞表示「与基线相同」 | [第 41 篇](41-snapshot-tools-and-compat.md) |
| 拓扑 | topology | 回滚校验的对象：设备的数量、类型号与 id，对排列顺序不敏感 | [第 72 篇](72-rollback-devices.md) |
| 状态文件 | vmstate（snapshot file） | `snapshot_path` 指向的文件：魔数、版本字符串、bincode 状态、CRC64 | [第 36 篇](36-snapshot-overview-and-format.md) |

---

## 6. 安全、构建与可观测性

| 中文 | 英文 | 一句话定义 | 首次出现 |
|---|---|---|---|
| 内核过滤字节码 | BPF | seccomp 过滤器的实际形态，由 seccompiler 在构建期生成并内嵌进二进制 | [第 42 篇](42-seccomp.md) |
| cargo 工作空间 | cargo workspace | 十二个 crate 的统一构建单元，lint 规则在这一级声明 | [第 46 篇](46-code-organization-and-build.md) |
| 控制组 | cgroup | jailer 用来限制资源的内核机制，v1 与 v2 两套代码 | [第 43 篇](43-jailer.md) |
| Rust 包 | crate | Rust 的编译单元；本仓库的逻辑几乎都在 `vmm` 这一个库 crate 里 | [第 05 篇](05-rust-and-crates-primer.md) |
| 开发工具脚本 | devtool | 官方的容器化构建与测试入口，用来固定工具链版本 | [第 06 篇](06-build-run-debug.md) |
| 调试特性 | GDB（`gdb` feature） | 把 Firecracker 变成 GDB 远程目标的编译特性，调试对象是 guest 内核 | [第 45 篇](45-gdb-tracing-and-kani.md) |
| 监狱 | jailer | 一次性的启动器：布置 chroot、cgroup 与 namespace 后 `exec` 成 Firecracker | [第 43 篇](43-jailer.md) |
| 形式化验证工具 | Kani | 对解析路径做模型检查的工具，证明集中在 guest 可控数据上 | [第 45 篇](45-gdb-tracing-and-kani.md) |
| 分段计时 | `latencies_us` | metrics 里十个 API 级与 VMM 级两两成对的耗时字段，只保留最后一次值 | [第 44 篇](44-logging-and-metrics.md) |
| 日志器 | `LOGGER` | 全局静态的日志对象，走互斥锁与人类可读的行；写失败只计数不报错 | [第 44 篇](44-logging-and-metrics.md) |
| 指标 | metrics | 全局静态的原子计数树，按子系统分组、序列化成 JSON | [第 44 篇](44-logging-and-metrics.md) |
| 静态 libc | musl | 产物必须静态链接的 libc 实现，因为它要在 jailer 建的 chroot 里执行 | [第 06 篇](06-build-run-debug.md) |
| 命名空间 | namespace | jailer 用挂载与 PID 两类 namespace 切断进程对宿主文件系统与进程树的视野 | [第 43 篇](43-jailer.md) |
| 换根 | `pivot_root` | jailer 的 `chroot()` 实现中真正让旧文件系统树失去名字的一步 | [第 43 篇](43-jailer.md) |
| 集成测试框架 | pytest | 上游的集成与性能测试层；本项目的 aarch64 环境跑不了它 | [第 47 篇](47-testing.md) |
| 系统调用过滤 | seccomp filter | 按线程分三张表的系统调用白名单，默认动作是 trap | [第 42 篇](42-seccomp.md) |
| 过滤器编译器 | seccompiler | 把 JSON 策略编成 BPF 的构建期工具，产物用 `include_bytes!` 内嵌 | [第 42 篇](42-seccomp.md) |
| 序列化框架 | serde | 配置与状态结构的序列化来源；`skip_serializing_if` 之类属性会影响 API 语义 | [第 05 篇](05-rust-and-crates-primer.md) |
| 过滤违规信号 | SIGSYS | 触发 seccomp 规则之外的系统调用时收到的信号，进程以退出码 148 结束 | [第 42 篇](42-seccomp.md) |
| 错误类型宏 | thiserror / displaydoc | 错误枚举的统一写法，变体上的文档注释同时是 `Display` 与 `fault_message` | [第 05 篇](05-rust-and-crates-primer.md) |
| 函数级追踪 | tracing | 用过程宏加 `Drop` 打进出日志的插桩，能定位长耗时函数但不能测绝对时延 | [第 45 篇](45-gdb-tracing-and-kani.md) |

---

## 7. 架构相关：x86_64 与 aarch64

| 中文 | 英文 | 一句话定义 | 首次出现 |
|---|---|---|---|
| 高级配置与电源接口 | ACPI | x86_64 上向 guest 描述硬件的表集合，生成顺序由指针依赖决定 | [第 17 篇](17-x86-64-platform.md) |
| ACPI 机器语言 | AML | DSDT 里描述 virtio 设备的字节码，按设备添加顺序生成 | [第 17 篇](17-x86-64-platform.md) |
| CPU 特性枚举 | CPUID | x86 上 guest 查询处理器特性的指令，也是 CPU 模板与归一化的作用对象 | [第 16 篇](16-x86-64-vcpu.md) |
| CPU 模板 | CPU template | 一张「对 guest 声明什么、屏蔽什么」的清单，在 vCPU 启动前写进 KVM | [第 20 篇](20-cpu-templates.md) |
| 模板辅助工具 | cpu-template-helper | 用 mock 内核真的建一台 microVM 来回答「guest 会看到什么」的工具 | [第 22 篇](22-aarch64-templates-and-helper.md) |
| 设备树 | FDT（flattened device tree） | aarch64 上 guest 认识这台机器的唯一来源，引导前写好、之后不再更新 | [第 19 篇](19-aarch64-platform.md) |
| 全局描述符表 | GDT / IDT | x86_64 引导前由 VMM 写进 guest 内存固定地址的段与中断描述符表 | [第 16 篇](16-x86-64-vcpu.md) |
| 中断控制器 | GIC（GICv2 / GICv3） | aarch64 的中断控制器，必须在建 vCPU 之后创建；版本先试 v3 再退 v2 | [第 19 篇](19-aarch64-platform.md) |
| 半虚拟化时钟 | kvmclock | 属于 VM 状态的时钟；保存时要清掉 `KVM_CLOCK_TSC_STABLE` 输出标志 | [第 17 篇](17-x86-64-platform.md) |
| 首选 vCPU 类型 | `KVM_ARM_PREFERRED_TARGET` | 由宿主内核给出的目标 CPU 类型，Firecracker 不自己挑型号 | [第 18 篇](18-aarch64-vcpu.md) |
| vCPU 初始化 | `KVM_ARM_VCPU_INIT` | aarch64 上让 vCPU 可用的前置 ioctl；对已运行的 vCPU 调用即架构定义的复位 | [第 18 篇](18-aarch64-vcpu.md) |
| 系统事件退出 | `KVM_EXIT_SYSTEM_EVENT` | aarch64 上关机与重启统一经它回到用户态，两者都终止进程 | [第 18 篇](18-aarch64-vcpu.md) |
| 本地中断控制器 | LAPIC / IOAPIC | x86_64 上由 KVM 在内核里模拟的中断控制器，地址由架构固定 | [第 17 篇](17-x86-64-platform.md) |
| 主 id 寄存器 | MIDR | ARM 的处理器标识寄存器，快照恢复前比较它的厂商域 | [第 59 篇](59-aarch64-vs-x86-64-runtime-paths.md) |
| 多处理器亲和 id | MPIDR | 标识一颗 ARM 核的寄存器；GIC 的保存与恢复都需要它的列表 | [第 19 篇](19-aarch64-platform.md) |
| 多处理器表 | mptable | x86_64 上已被上游标记为废弃、但 v1.12.1 仍无条件写入的旧式拓扑表 | [第 17 篇](17-x86-64-platform.md) |
| 型号专用寄存器 | MSR（model-specific register） | x86 的一组系统寄存器；快照按分块顺序读写，`TSC_DEADLINE` 延后到最后 | [第 16 篇](16-x86-64-vcpu.md) |
| 归一化 | normalization | 无条件的 CPUID 改写：对齐拓扑字段、抹掉宿主机特有信息、关掉不该给 guest 的特性 | [第 21 篇](21-x86-64-cpuid-msr-normalization.md) |
| PE 内核映像 | PE（arm64 `Image`） | aarch64 加载器接受的内核格式；x86_64 侧是 ELF `vmlinux` | [第 61 篇](61-guest-kernel-on-arm.md) |
| 电源状态接口 | PSCI | ARM 的固件接口，次核启动与关机都经它；由 KVM 实现 | [第 18 篇](18-aarch64-vcpu.md) |
| 半虚拟化引导 | PVH | x86_64 的第二种引导协议，由内核映像里有没有 ELF note 决定 | [第 16 篇](16-x86-64-vcpu.md) |
| 可伸缩向量扩展 | SVE | ARM 的向量扩展，要求 `VCPU_INIT` 与 `VCPU_FINALIZE` 之间两阶段初始化 | [第 18 篇](18-aarch64-vcpu.md) |
| 时间戳计数器 | TSC | 属于 vCPU 状态的时钟；快照没有频率时只能恢复到同型号宿主 | [第 16 篇](16-x86-64-vcpu.md) |
| 零页 | zero page | Linux 64 位引导协议约定的参数结构，`rsi` 指向它 | [第 16 篇](16-x86-64-vcpu.md) |

---

## 8. 版本、部署与三层改动

| 中文 | 英文 | 一句话定义 | 首次出现 |
|---|---|---|---|
| ARM 适配版 | ARM port | KASandbox 仓库 `firecracker/` 在 `3863c76` 的形态：aarch64 构建修复、HDBSS 使能与 checkpoint / restore 扩展 | [第 01 篇](01-lineage-and-repo-map.md) |
| e2b 定制版 | e2b fork | e2b-dev/firecracker 的 `a41d3fb`：三个内存查询端点、uffd 写保护、可选 memfile 的快照 | [第 01 篇](01-lineage-and-repo-map.md) |
| 内存查询端点 | `GET /memory`、`GET /memory/dirty`、`GET /memory/mappings` | e2b 定制版新增的三个只读端点，分别给常驻与零页位图、脏页位图、区域宿主地址 | [第 49 篇](49-why-e2b-forked.md) |
| 硬件跟踪环境变量 | `FC_HDBSS_ORDER` / `FC_HDBSS_REQUIRED` | 分别控制硬件缓冲区档位与「启用失败是否算启动失败」的两个环境变量 | [第 65 篇](65-dirty-tracking-backend.md) |
| guest 内核仓库 | fc-kernels | 只有 `.config` 与构建脚本、没有源码补丁的内核配置仓库 | [第 56 篇](56-guest-kernel-requirements-and-e2b-configs.md) |
| 版本目录 | `/fc-versions/<版本名>/` | 部署侧存放 Firecracker 二进制的目录；目录名只是寻址标签，不标识 API 面 | [第 63 篇](63-integration-with-e2b-infra.md) |
| 鲲鹏 | Kunpeng | 本项目 aarch64 宿主的处理器系列，硬件脏页跟踪来自它的 950 代 | [第 60 篇](60-kunpeng-openeuler-host.md) |
| openEuler | openEuler | 宿主发行版；能力号 502 的 HDBSS 补丁来自它的非主线内核 | [第 60 篇](60-kunpeng-openeuler-host.md) |
| 编排器 | orchestrator | 调用 Firecracker API、管理差分树与磁盘分层的上层服务，不在本书范围内 | [第 63 篇](63-integration-with-e2b-infra.md) |
| 沙箱 | sandbox | 调用方视角下的一台 microVM 实例，由 orchestrator 创建、暂停与恢复 | [第 49 篇](49-why-e2b-forked.md) |
| 上游 v1.12.1 | upstream v1.12.1 | firecracker-microvm/firecracker 在 tag `v1.12.1`（`d990331f7`）的代码，全书的默认口径 | [第 01 篇](01-lineage-and-repo-map.md) |
| 版本名 | `v<swagger 版本>_<7 位哈希>` | 构建脚本拼出的版本字符串；只有哈希能标识实际的 API 面 | [第 55 篇](55-seccomp-build-upload-and-upstream-fixes.md) |

---

## 9. 小结

- 本表共收 183 条，分八张表：虚拟化与 KVM 23 条、进程结构与控制面 24 条、guest 内存与脏页 25 条、
  设备与 virtio 34 条、快照与回滚 20 条、安全与构建 21 条、架构相关 24 条、版本与部署 12 条。
- 「首次出现」列指的是实质引入该术语的篇目。第 01 篇的仓库地图与第 02 篇的取舍清单会提前点到大量名字，
  它们不算引入；只有三层版本称谓本身以第 01 篇为准。
- 最容易混淆的是四组词，查表时要连着看：脏页位图（KVM 侧 / 用户态侧）与位图 sidecar（写进磁盘的 FCDB 文件）；
  内存文件与状态文件；快照恢复（新建进程）与原地回滚（保住进程）；
  写保护式脏页跟踪与硬件脏页跟踪（出口相同、成本函数不同）。
- 位号空间有三套且互不通用：扁平页序（三个内存端点与 FCDB 共用）、GPA、内存文件偏移。
  `GET /memory/dirty` 的位图按区域各自向上取整到 64 位，与 `GET /memory` 的跨区域连续编号不是同一套规则。
- 同名不同物的还有两处：独立的 `utils` crate 与 `vmm` 内部的 `utils` 模块；
  部署目录名里的版本号与源码版本号。
- 中文译法以 [`STYLE.md`](STYLE.md) 第三节为准，本表是它的超集；不翻译的专有名词清单也在那一节。

## 延伸阅读 / 下一篇

- [第 75 篇 · 代码地图：crate、模块与篇目](75-code-map.md)：从术语反查它实现在哪个文件里。
- [第 76 篇 · API 端点总表](76-api-reference.md)：本表里出现的 API 路径的完整参数与响应。
- [第 77 篇 · 配置项、命令行参数、环境变量与 metrics 总表](77-config-cli-env-metrics-reference.md)：
  `track_dirty_pages`、`FC_HDBSS_ORDER`、`latencies_us` 等的完整清单。
- [第 78 篇 · 三层差异总表](78-layer-diff-tables.md)：三层版本称谓对应的文件级改动。
- [第 79 篇 · 阅读上游代码的方法与常见问题](79-reading-upstream-code.md)：拿到一个名字之后怎么在代码里追它。
- e2b 手册（`../e2b-infra/`）与 checkpoint / restore 手册（`../../e2b-infra-docs/rollback/docs/`）
  各有自己的术语表，orchestrator 侧的名词（差分树、磁盘分层、模板）在那两本书里定义。
