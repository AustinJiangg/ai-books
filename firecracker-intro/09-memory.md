# 09. 内存：Guest 眼里的“物理内存”从哪来

> **《彻底搞懂 Firecracker》系列 · 第九篇**
>
> **读完本篇，你能理解：**
> - Guest 内存在宿主机上的真实形态：一块 `mmap` 出来的匿名内存
> - 为什么 Guest 内存是“按需分配”的，以及这如何让内存超卖成为可能
> - 为什么 Guest 释放的内存不会自动还给宿主机，气球设备如何解决这个问题
> - 大页（2M hugetlbfs、透明大页）能带来什么好处，有什么限制
> - 脏页跟踪、内存热插拔的作用
> - 内存超卖的风险，以及生产环境的内存安全建议
>
> **前置知识：** 第 01 篇（虚拟内存、页表）、第 03 篇（Stage-2、内存槽）、第 08 篇（地址地图）。
>
> **版本：** Firecracker v1.17.0，ARM64。

---

## 引子：一家“先上车后买票”的酒店

假设你开了一家酒店，有 100 个房间。你发现客人订房后常常很晚才入住，甚至根本不来；入住的客人也往往只用一两天。于是你决定：

- 客人预订时，只在本子上记一笔，不真正锁定房间；
- 客人真正到店时，才给他分配一个空房间；
- 客人退房后，房间可以给别人用。

这样，100 个房间就能接 150 个甚至 200 个预订。这就是“超卖”。它的风险也很明显：如果某天所有客人同时到店，就会有人没房间住。

Firecracker 管理 Guest 内存的方式和这家酒店非常相似。这一篇就讲清楚其中的机制和风险。

---

## 一、Guest 内存的真实形态

### 1.1 就是一块 mmap

当你配置 `mem_size_mib: 1024`，Firecracker 在启动时做的事情本质上是：

```c
void *mem = mmap(NULL, 1024 << 20,
                 PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE,
                 -1, 0);
```

然后通过 `KVM_SET_USER_MEMORY_REGION` 告诉 KVM：“Guest 的 IPA `0x8000_0000` 起的 1 GiB，对应我进程里 `mem` 开始的这块地址”。

几个标志的含义：

| 标志 | 含义 |
|------|------|
| `MAP_ANONYMOUS` | 不对应任何文件，就是一块“白纸”内存 |
| `MAP_PRIVATE` | 这块内存是本进程私有的 |
| `MAP_NORESERVE` | 不预先为它预留交换空间或物理内存，用多少算多少 |

（当配置了 vhost-user 设备时，Guest 内存需要与另一个进程共享，Firecracker 会改用 `memfd_create` 创建的共享内存。这属于进阶场景。）

### 1.2 三层映射

一次 Guest 内存访问，完整的地址变换链路是：

```
Guest 进程 VA
  │  Guest 页表（Stage-1，Guest 内核管理）
  ▼
Guest 物理地址 IPA（如 0x8000_1000）
  │  Stage-2 页表（KVM 管理）
  ▼
宿主机物理地址 PA
  ▲
  │  宿主机页表（宿主内核为 Firecracker 进程管理）
Firecracker 进程中的 VA（mem + 0x1000）
```

KVM 的工作，就是保证“IPA → PA”与“Firecracker 进程 VA → PA”指向同一个物理页。这样，**Firecracker 在自己进程里读写 `mem + 偏移`，就等于读写 Guest 的物理内存**——这正是 virtio 设备能直接从 Guest 内存取数据的原因（第 10 篇）。

### 1.3 按需分配

`mmap` 返回时，宿主机**一个物理页都没有分配**，只是在 Firecracker 进程的地址空间里登记了一段区域。

当 Guest 第一次访问某个 IPA：

1. Stage-2 页表里没有这个地址的映射，触发 Stage-2 缺页，陷入 KVM；
2. KVM 发现这个 IPA 属于内存槽，算出对应的 Firecracker 进程 VA；
3. KVM 在宿主内核里对这个 VA 触发一次普通的缺页处理，宿主内核分配一个物理页（并清零）；
4. KVM 填上 Stage-2 映射，返回 Guest 重新执行那条指令。

整个过程对 Guest 和 Firecracker 用户态都是透明的。

### 1.4 动手：观察按需分配

启动一台配置了 2048 MiB 内存的 microVM，然后在宿主机上：

```bash
FC_PID=$(pgrep -f 'firecracker --api-sock' | head -1)
grep -E 'VmRSS|VmSize' /proc/$FC_PID/status
```

- `VmSize`（虚拟大小）会超过 2 GB——包含了整块 Guest 内存的地址空间；
- `VmRSS`（实际驻留在物理内存中的大小）则小得多，大约是 Guest 启动过程中实际碰过的内存量。

然后在 Guest 里分配并写入 1 GB 内存：

```bash
# Guest 内（如果有 python3）
python3 -c "b = bytearray(1024*1024*1024); import time; time.sleep(600)" &
```

再看宿主机上的 `VmRSS`，会增加约 1 GB。

---

## 二、只借不还：Guest 释放的内存去哪了

### 2.1 问题

接着上面的实验：在 Guest 里结束那个 Python 进程（`kill %1`），Guest 里用 `free -m` 看，内存已经释放了。但在宿主机上看 `VmRSS`——**几乎没有变化**。

原因是：Guest 内核释放内存，只是在它自己的“空闲页列表”里记了一笔，这些页依然被映射着，宿主机并不知道它们已经没用了。从宿主机的角度，这些页曾经被访问过，就一直驻留在内存中。

时间一长，一台 microVM 的 RSS 会逐渐增长到它配置的上限，即使 Guest 实际只用了一小部分。这会严重影响超卖的效果。

### 2.2 解决方案一：气球设备（virtio-balloon）

**气球**是一个形象的比喻：在 Guest 内存里放一个气球，宿主机想要回收内存时就“吹大”气球，气球占据的那部分内存就被宿主机收回；想还给 Guest 时就“放气”。

工作原理：

```
宿主机：PATCH /balloon {"amount_mib": 512}    ← 我想从 Guest 拿回 512 MiB
           │
           ▼
Firecracker：通过 virtio 配置空间告诉 Guest 的气球驱动“目标大小 512 MiB”
           │
           ▼
Guest 气球驱动：向 Guest 内核申请 512 MiB 内存（像普通程序一样分配）
                把这些页的地址通过 virtio 队列告诉 Firecracker
           │
           ▼
Firecracker：对这些页调用 madvise(MADV_DONTNEED)
             → 宿主内核释放对应的物理页
```

结果：Guest 少了 512 MiB 可用内存（被气球“占着”），宿主机拿回了 512 MiB 物理内存。

配置气球设备（开机前）：

```bash
sudo curl -X PUT --unix-socket /tmp/firecracker.socket \
    -d '{
        "amount_mib": 0,
        "deflate_on_oom": true,
        "stats_polling_interval_s": 1
    }' \
    http://localhost/balloon
```

| 字段 | 含义 |
|------|------|
| `amount_mib` | 气球的目标大小。0 表示一开始不占内存 |
| `deflate_on_oom` | Guest 内存不足时，是否允许 Guest 自动给气球放气（避免 Guest 内进程被 OOM 杀死） |
| `stats_polling_interval_s` | 每隔几秒从 Guest 获取一次内存统计；0 表示关闭统计 |

运行中调整和查看：

```bash
# 吹气球：回收 512 MiB
sudo curl -X PATCH --unix-socket /tmp/firecracker.socket \
    -d '{"amount_mib": 512}' http://localhost/balloon

# 查看 Guest 内存统计（空闲内存、可用内存、缺页次数等）
sudo curl -s --unix-socket /tmp/firecracker.socket \
    http://localhost/balloon/statistics | jq
```

在 Guest 里用 `free -m` 观察，总可用内存会减少；在宿主机上看 `VmRSS`，会下降。

**气球的局限：**
- 需要 Guest 内核里有气球驱动（`CONFIG_VIRTIO_BALLOON`）；
- 需要宿主机“主动”决定吹多大，这就需要一个外部的控制程序根据统计数据做决策；
- **一个恶意的 Guest 可以不配合**——忽略气球请求，或者假装吹了又偷偷用。所以气球只能作为“优化”，不能作为安全保证。真正的内存上限要靠 cgroups（第 14 篇）。

### 2.3 解决方案二：空闲页报告与提示（v1.14 起）

气球需要宿主机猜测 Guest 有多少空闲内存。virtio-balloon 还有两个更“自动”的特性：

- **空闲页报告（free page reporting）**：Guest 内核在后台持续把较大的空闲内存块（通常 2 MiB 以上）报告给 Firecracker，Firecracker 直接释放它们。之后 Guest 再用到这些页时，会按需重新分配；
- **空闲页提示（free page hinting）**：由宿主机主动发起一轮“请告诉我你有哪些空闲页”，常用于创建快照前缩小内存文件（第 15 篇）。

```json
{
  "amount_mib": 0,
  "deflate_on_oom": true,
  "free_page_reporting": true
}
```

这两个功能都需要较新的 Guest 内核支持，且部分处于开发者预览阶段，使用前请查看官方 `docs/ballooning.md` 中的最新状态。

---

## 三、大页

### 3.1 为什么大页能提升性能

第 01 篇说过，内存按“页”映射，常见的页大小是 4 KiB。每次地址翻译的结果会缓存在 CPU 的 TLB（地址翻译缓存）里，但 TLB 容量有限。

在虚拟机里情况更糟：一次 TLB 未命中需要走 **Stage-1 和 Stage-2 两层页表**，在最坏情况下需要访问内存几十次。

如果用 **2 MiB 的大页**：

- 同样大小的 TLB 能覆盖 512 倍的内存范围，TLB 未命中大大减少；
- 页表层级少一级，每次未命中的代价也更小；
- Stage-2 缺页的次数大大减少（每次缺页能映射 2 MiB 而不是 4 KiB），启动和快照恢复后“热身”更快。

官方文档提到，使用 2M 大页能让启动时间最多缩短约一半（以其启动性能测试为准）。

### 3.2 Firecracker 的三种模式

`machine-config` 的 `huge_pages` 字段：

| 值 | 实现方式 | 要求 |
|----|---------|------|
| `None`（默认） | 普通页（宿主机默认页大小，通常 4K） | 无 |
| `2M` | hugetlbfs 2 MiB 大页 | 宿主机必须**预先**留出足够的大页池 |
| `Transparent`（v1.17 起） | `madvise(MADV_HUGEPAGE)`，由内核在可能时自动使用透明大页 | 内存大小必须是 2 MiB 的整数倍；宿主机开启了 THP |

### 3.3 动手：使用 2M 大页

```bash
# 宿主机：预留 600 个 2 MiB 大页（约 1.2 GB）
echo 600 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
grep -i huge /proc/meminfo
```

启动配置：

```json
"machine-config": {
  "vcpu_count": 2,
  "mem_size_mib": 1024,
  "huge_pages": "2M"
}
```

启动后再看 `/proc/meminfo` 中的 `HugePages_Free`，会随 Guest 使用而减少。

> ⚠️ **注意：** 由于 Firecracker 使用 `MAP_NORESERVE`，大页池不够用时，Guest 访问新内存会导致 Firecracker 收到 `SIGBUS` 信号而崩溃。务必为所有使用大页的 microVM 预留足够的池。另外，hugetlbfs 内存配合传统气球的效果有限，官方建议改用空闲页报告或提示。

### 3.4 ARM64 上的页大小

ARM64 支持 4K、16K、64K 三种基础页大小。大多数发行版（以及 Firecracker 官方支持的宿主机配置）使用 4K 页。如果你的宿主机内核使用 64K 页，可以用 `getconf PAGESIZE` 确认——Firecracker 也能运行，但不在官方测试矩阵内，大页的大小和行为也会不同。

---

## 四、脏页跟踪

**脏页**是指被修改过的内存页。KVM 可以记录 Guest 自某个时刻以来写过哪些页：

```json
"machine-config": { "track_dirty_pages": true, ... }
```

开启后，KVM 会在 Stage-2 页表中把所有页先设成“只读”，Guest 第一次写某页时触发一次陷入，KVM 记下这一页，再恢复可写。Firecracker 可以通过 `KVM_GET_DIRTY_LOG` 读取这个记录。

它的主要用途是**差量快照**：第二次快照只需要保存上次以来改过的页（第 15 篇）。代价是每页第一次写会多一次陷入，对写内存密集的负载有一定性能影响，所以默认关闭。

---

## 五、内存热插拔（v1.14 起）

传统上，microVM 开机后内存大小就固定了。v1.14 引入了 **virtio-mem** 设备，允许在运行中给 Guest 增加或减少内存：

```bash
# 开机前：预留一块最大 4 GiB 的可热插拔区域
sudo curl -X PUT --unix-socket /tmp/firecracker.socket \
    -d '{"total_size_mib": 4096}' http://localhost/hotplug/memory

# 运行中：插入 1 GiB
sudo curl -X PATCH --unix-socket /tmp/firecracker.socket \
    -d '{"requested_size_mib": 1024}' http://localhost/hotplug/memory

# 查看状态
sudo curl -s --unix-socket /tmp/firecracker.socket http://localhost/hotplug/memory | jq
```

（字段细节以 `docs/memory-hotplug.md` 为准。）

与气球相比，virtio-mem 以较大的内存块为单位工作，Guest 看到的“总内存”真的会变化，更适合“按需扩容”的场景。同样需要 Guest 内核支持（`CONFIG_VIRTIO_MEM`）。

---

## 六、内存超卖：收益与风险

### 6.1 为什么能超卖

综合前面的机制：

- Guest 内存按需分配，没用到的不占物理内存；
- 气球和空闲页报告能回收 Guest 不再使用的内存；
- 大多数 Serverless 函数的实际内存使用远低于配置值。

因此，一台 256 GB 内存的宿主机，可以运行“配置总和”远超 256 GB 的 microVM。

### 6.2 风险

**风险一：集体爆发。** 如果大量 microVM 同时用满内存，宿主机物理内存耗尽，宿主内核的 OOM Killer 会选择杀死某些进程——很可能是某个 Firecracker 进程，对应的 microVM 瞬间消失。

**风险二：一个 Guest 影响所有人。** 恶意 Guest 可以故意写满全部配置内存，并拒绝配合气球。

**应对措施：**

| 措施 | 作用 |
|------|------|
| 用 cgroups 限制每个 Firecracker 进程的内存（第 14 篇） | 单个 microVM 不能超过额度，超了只杀它自己 |
| 监控宿主机内存水位，调度器控制超卖比例 | 避免集体爆发 |
| 合理设置 `deflate_on_oom` | 平衡 Guest 内部稳定性与宿主机回收效果 |

### 6.3 安全相关的宿主机建议

官方的生产环境指南（`docs/prod-host-setup.md`）中与内存相关的几条：

- **关闭交换分区（swap），或使用加密交换**：Guest 的内存可能被换出到磁盘，如果磁盘不加密，microVM 结束后数据可能残留在磁盘上；
- **关闭 KSM（Kernel Samepage Merging）**：KSM 会把不同进程中内容相同的页合并成一页以节省内存，但这会引入跨 microVM 的侧信道攻击风险（攻击者可以通过写入时间判断其他 microVM 是否有相同内容的页）；
- **使用具备 Rowhammer 缓解能力的内存**：防止通过高频访问内存导致相邻物理位翻转的攻击。

检查你的宿主机：

```bash
cat /proc/swaps                         # 有内容表示开启了 swap
cat /sys/kernel/mm/ksm/run              # 0 表示 KSM 已关闭
```

---

## 小结

| 机制 | 解决的问题 | 关键点 |
|------|----------|-------|
| `mmap` + `MAP_NORESERVE` | 提供 Guest 内存 | 按需分配，进程 VA 与 Guest IPA 一一对应 |
| Stage-2 缺页 | 首次访问时分配物理页 | 对 Guest 和 VMM 用户态透明 |
| virtio-balloon | Guest 释放的内存不会自动归还 | 需要 Guest 配合，不能作为安全边界 |
| 空闲页报告/提示 | 更自动地回收空闲内存 | 需要较新 Guest 内核 |
| 大页（2M / THP） | TLB 压力、两级页表开销、缺页次数 | 2M 需预留池，否则 SIGBUS |
| 脏页跟踪 | 差量快照 | 有写入性能开销，默认关闭 |
| virtio-mem | 运行中扩缩内存 | v1.14 起 |
| cgroups 内存限制 | 防止单个 microVM 拖垮宿主机 | 真正的安全边界 |

---

## 思考题

1. Firecracker 进程的 `VmRSS` 能超过 `mem_size_mib` 吗？除了 Guest 内存，还有哪些东西会占用这个进程的内存？
2. 为什么说“Guest 第一次访问内存时，宿主内核会把页清零”是一个重要的安全特性？
3. 一个 Guest 在启动后立刻把全部内存写一遍（有些系统启动时会这么做），对超卖有什么影响？怎么应对？
4. 气球吹大后，Guest 里的程序再申请内存，会发生什么？`deflate_on_oom` 设置为 true 和 false 时分别会怎样？
5. 两台 microVM 运行相同的 rootfs 和程序，它们的内存里有大量相同的内容。为什么不用 KSM 合并它们来节省内存？

---

## 下一篇预告

**[10. 设备模型：virtio-mmio 全解析](10-virtio.md)**

我们反复提到 virtio、virtqueue、ioeventfd、irqfd。下一篇把它们彻底讲透：一个 virtio 设备是如何被发现、协商、初始化的，环形队列到底长什么样，中断是怎样从 Firecracker 送到 Guest 的，以及 MMIO 与 PCI 两种传输方式的区别。
