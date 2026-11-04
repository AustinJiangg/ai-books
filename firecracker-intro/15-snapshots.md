# 15. 快照与恢复：毫秒级“复活”一台虚拟机

> **《彻底搞懂 Firecracker》系列 · 第十五篇**
>
> **读完本篇，你能理解：**
> - 一个 Firecracker 快照由哪些文件组成，分别保存了什么
> - 创建和恢复快照的完整 API 流程
> - 为什么恢复可以做到毫秒级：`MAP_PRIVATE` 与按需加载
> - 全量快照、差量快照，以及 userfaultfd 自定义内存加载
> - 从一个快照克隆出多台 microVM 时的“唯一性”陷阱：随机数、标识符、时钟、网络
> - 快照的兼容性限制和安全注意事项
>
> **前置知识：** 第 01 篇（寄存器即 CPU 状态）、第 07 篇（暂停）、第 09 篇（Guest 内存、脏页跟踪）、第 11 篇（网络命名空间、vsock）。
>
> **版本：** Firecracker v1.17.0（快照功能自 v1.13 起正式可用，差量快照仍为开发者预览）。

---

## 引子：游戏存档

玩电子游戏时，你可以在任何时刻“存档”，之后从存档点继续，就像什么都没发生过。存档里保存了游戏世界的全部状态：角色位置、背包物品、地图进度……

Firecracker 的快照就是给整台虚拟机“存档”：CPU 寄存器、内存、设备状态全部保存下来。之后可以在**另一个 Firecracker 进程**中，从存档点继续运行。

这带来了一个极具吸引力的用法：**先把一个函数的运行环境启动好（内核启动、Python 解释器加载、依赖库导入），存一个档；以后每次有请求来，直接从存档恢复，跳过所有的启动过程。** AWS Lambda 的 SnapStart 功能就是基于这一思路，大幅缩短了 Java 等运行时的冷启动时间。

---

## 一、快照里有什么

一次快照会产生两个文件，加上你自己管理的磁盘文件：

| 文件 | 内容 | 由谁生成 |
|------|------|---------|
| **microVM 状态文件**（snapshot file） | vCPU 寄存器、KVM 中各种内部状态（vGIC、定时器等）、所有设备的状态（virtio 队列位置、串口寄存器等）、机器配置 | Firecracker |
| **内存文件**（memory file） | Guest 内存的完整内容（或差量部分） | Firecracker |
| 磁盘文件 | rootfs 和数据盘的内容 | **你自己负责** |

几点注意：

- **磁盘不在快照里**。快照恢复时，磁盘文件必须处于“与创建快照时一致”的状态。如果快照后原 microVM 继续运行并修改了磁盘，用这份磁盘去恢复快照就会导致 Guest 文件系统的缓存与磁盘内容不一致。通常的做法是创建快照时同时复制（或 reflink）一份磁盘；
- **MMDS 的数据、日志和指标配置不在快照里**，恢复后需要重新设置；
- 状态文件里有一个 64 位 CRC 校验值，只能防止意外损坏，**不能防篡改**。快照文件被视为可信输入，在网络上传输或存储时，需要你自己做认证和加密。

---

## 二、动手：创建并恢复一个快照

### 2.1 创建快照

启动一台 microVM（第 05 篇），登录进去，制造一些“状态”：

```bash
# Guest 内
echo "I was here before the snapshot" > /root/marker.txt
sync
( i=0; while true; do echo "counter=$i" > /dev/ttyS0; i=$((i+1)); sleep 1; done ) &
```

串口终端上会每秒打印一个递增的计数器。

在宿主机上，**先暂停，再创建快照**：

```bash
SOCK=/tmp/firecracker.socket

# 1. 暂停
sudo curl -X PATCH --unix-socket $SOCK -d '{"state": "Paused"}' http://localhost/vm

# 2. 创建全量快照
sudo curl -X PUT --unix-socket $SOCK \
    -d '{
        "snapshot_type": "Full",
        "snapshot_path": "./snap.vmstate",
        "mem_file_path": "./snap.mem"
    }' \
    http://localhost/snapshot/create

# 3. 同时复制一份磁盘（此时 Guest 已暂停，磁盘内容不会再变）
cp ubuntu-24.04.ext4 snap-rootfs.ext4

ls -lh snap.vmstate snap.mem
```

`snap.mem` 的大小等于 Guest 内存大小；`snap.vmstate` 只有几十 KB。

现在可以结束原来的 microVM（`sudo pkill firecracker`）。

### 2.2 恢复快照

恢复必须在一个**全新的、未配置过的** Firecracker 进程中进行。首先，恢复后的 microVM 需要找到和原来一样的资源：

- **TAP 设备**：名字相同（这里是 `tap0`），需要事先创建好；
- **磁盘文件**：路径相同。我们把复制的磁盘放回原路径，或者在恢复前把原文件替换掉。

```bash
cp snap-rootfs.ext4 ubuntu-24.04.ext4     # 让磁盘回到快照时刻的状态

# 终端 1：启动一个空的 Firecracker
sudo rm -f /tmp/firecracker.socket
sudo ./firecracker --api-sock /tmp/firecracker.socket

# 终端 2：加载快照并立即恢复运行
sudo curl -X PUT --unix-socket /tmp/firecracker.socket \
    -d '{
        "snapshot_path": "./snap.vmstate",
        "mem_backend": { "backend_type": "File", "backend_path": "./snap.mem" },
        "resume_vm": true
    }' \
    http://localhost/snapshot/load
```

切到终端 1：**计数器从暂停前的数字继续往上数**。SSH 进去看看 `/root/marker.txt` 依然在。整台虚拟机就像只是“眨了一下眼”。

试着测一下恢复耗时：

```bash
time sudo curl -s -X PUT --unix-socket /tmp/firecracker.socket \
    -d '{"snapshot_path": "./snap.vmstate",
         "mem_backend": {"backend_type": "File", "backend_path": "./snap.mem"},
         "resume_vm": true}' \
    http://localhost/snapshot/load
```

通常只需要几毫秒到几十毫秒，比完整启动快得多。

### 2.3 恢复时修改资源名

如果恢复环境里 TAP 设备或 vsock 路径与原来不同，可以在加载时覆盖：

```json
{
  "snapshot_path": "./snap.vmstate",
  "mem_backend": { "backend_type": "File", "backend_path": "./snap.mem" },
  "network_overrides": [ { "iface_id": "net1", "host_dev_name": "tap7" } ],
  "vsock_override": { "uds_path": "./v7.sock" },
  "resume_vm": true
}
```

（TAP 改名自 v1.12 起支持，vsock 路径覆盖自 v1.16 起支持。）

---

## 三、为什么恢复这么快

### 3.1 内存不是“读进来”的，是“映射进来”的

直觉上，恢复一台 1 GiB 内存的 microVM，需要把 1 GiB 的内存文件读进内存，至少要几百毫秒。但 Firecracker 并不这么做。

它用 `MAP_PRIVATE` 方式把内存文件 `mmap` 成 Guest 内存：

```
Guest 读某页 ──▶ 缺页 ──▶ 宿主内核从文件（或页缓存）读入这一页 ──▶ 映射给 Guest
Guest 写某页 ──▶ 写时复制（copy-on-write）──▶ 宿主内核复制一份匿名页给 Guest，原文件不变
```

结果：

- **恢复瞬间几乎不读任何数据**，只是建立映射关系；
- Guest 实际访问到哪些页，才加载哪些页（按需加载）；
- **多台 microVM 从同一个快照恢复时，没被修改的页在宿主机页缓存中只有一份**，天然共享；
- Guest 的写入不会污染内存文件，同一个快照可以反复使用。

代价是：恢复后的 microVM 在整个生命周期内都依赖这个内存文件，不能删除它。

### 3.2 恢复后的“热身”

按需加载意味着恢复后的头一段时间里，Guest 会频繁触发缺页（每次都是一次 Stage-2 缺页 + 一次宿主机缺页，可能还伴随磁盘读取）。如果快照放在慢速存储上，恢复后的第一个请求会比较慢。

缓解方法：

- 把快照放在本地 SSD 或内存文件系统（tmpfs）上；
- 预先把内存文件读入宿主机页缓存（`cat snap.mem > /dev/null` 或 `vmtouch` 之类的工具）；
- 使用大页（第 09 篇），一次缺页映射 2 MiB，大大减少缺页次数；v1.17 起加载快照时也可以通过 `huge_pages` 字段指定大页配置；
- 使用 userfaultfd 自己控制加载策略（下一节）。

---

## 四、进阶：差量快照与 userfaultfd

### 4.1 差量快照（开发者预览）

如果开启了脏页跟踪（`track_dirty_pages: true`，第 09 篇），可以创建**差量快照**：只保存自上次快照以来被修改过的内存页。

```bash
sudo curl -X PUT --unix-socket $SOCK \
    -d '{"snapshot_type": "Diff", "snapshot_path": "./snap2.vmstate", "mem_file_path": "./snap2.mem"}' \
    http://localhost/snapshot/create
```

差量内存文件是一个**稀疏文件**：大小和完整内存一样，但只有被修改的页有实际内容，其余部分是“空洞”，不占磁盘空间。

要恢复差量快照，需要先用 `snapshot-editor` 工具把它“叠加”到基础的全量快照内存文件上：

```bash
# snapshot-editor 在第 05 篇解压出的 release 目录里
SE=$(ls release-*/snapshot-editor-* | grep -v debug)
$SE edit-memory rebase \
    --memory-path ./snap.mem \
    --diff-path ./snap2.mem
```

之后用 `snap.mem` 和 `snap2.vmstate` 恢复。

从 v1.13 起，即使没有开启脏页跟踪，也可以创建差量快照——Firecracker 会用 `mincore` 系统调用粗略判断哪些页被访问过（要求宿主机没有开启 swap）。

### 4.2 userfaultfd：自己当“内存供应商”

`mem_backend` 的另一种类型是 `Uffd`：

```json
"mem_backend": { "backend_type": "Uffd", "backend_path": "./uffd.sock" }
```

**userfaultfd（UFFD）** 是 Linux 的一个机制：当进程访问某段内存缺页时，不由内核自动处理，而是通知一个用户态程序，由它决定往这一页里填什么内容。

使用方式：

1. 你编写一个“缺页处理程序”，监听 `uffd.sock`；
2. Firecracker 加载快照时，创建 Guest 内存（空的），注册 userfaultfd，把 UFFD 文件描述符和内存布局信息通过 `uffd.sock` 发给你的处理程序；
3. Guest 每次访问一个尚未填充的页，你的处理程序收到通知，从任何地方取得这一页的内容（本地文件、网络、对象存储、压缩包……），用 `UFFDIO_COPY` 填进去；
4. Guest 继续运行。

这打开了很多可能性：

- **从远端按需拉取内存**：快照存在远端存储上，恢复时不需要先把整个文件下载到本地；
- **智能预取**：记录 Guest 恢复后的访问模式，下次恢复时提前加载这些页；
- **去重与压缩**：多个快照的相同页只存一份；
- **内存回收**：配合气球设备，Guest 放回的页会触发 `remove` 事件（v1.11 起）。

Firecracker 仓库的 `src/firecracker/examples/uffd/` 目录里有几个示例处理程序（全部预先加载、按需加载等），是很好的起点。

---

## 五、克隆的陷阱：唯一性问题

快照最诱人的用法，是**从一个快照恢复出很多台 microVM**。但这里隐藏着一个深刻的问题：**这些 microVM 在恢复的那一瞬间是完全相同的。**

### 5.1 哪些东西本应唯一

| 状态 | 克隆后的问题 |
|------|------------|
| 内核随机数生成器的内部状态 | 多台 microVM 生成**相同的随机数**——密钥、会话令牌、TCP 序列号可能重复 |
| 用户态程序缓存的随机数、UUID | 同上，而且内核无法帮忙 |
| 已经生成的密钥、令牌 | 多台机器共享同一个“私钥” |
| 主机名、机器 ID（`/etc/machine-id`） | 相同 |
| MAC 地址、IP 地址 | 相同，放在同一网络里会冲突 |
| 已建立的 TCP 连接 | 多台机器“继承”同一个连接，状态全乱 |
| 时钟 | 恢复后，Guest 的时间停留在快照时刻，可能落后很多 |

官方文档对此的立场很明确：**同一个快照状态被恢复执行超过一次，就被视为不安全的**，除非你有可靠的机制保证唯一性。

### 5.2 Firecracker 提供的帮助

**VMGenID（虚拟机代际标识）**

一个特殊的虚拟设备，向 Guest 暴露一个 16 字节的随机标识。每次从快照恢复时，Firecracker 都会更换这个标识，并在恢复 vCPU 之前向 Guest 发送一个中断。

Linux 5.18 起（使用 ACPI 的 x86）、6.10 起（使用设备树的 ARM64）支持 VMGenID：检测到标识变化时，内核会**用新值重新播种自己的随机数生成器**。这样，恢复后 `/dev/urandom`、`getrandom()` 产生的随机数就是各不相同的。

> 在 ARM64 上，Guest 内核需要 6.10 以上（或在 6.1 上回移植相关补丁）才能通过设备树使用 VMGenID。

**VMClock（v1.15 起）**

另一个设备，让 Guest 中的程序能感知“我刚刚被从快照恢复了”（时钟发生了中断），从而有机会做出反应，比如重新同步时间、重新生成密钥。

**vsock 传输重置**

创建快照时，Firecracker 会向 Guest 发送 vsock 的“传输重置”事件，所有已建立的 vsock 连接都会被关闭；Guest 中正在监听的 vsock 端口依然有效，可以接受新连接。

### 5.3 你需要自己做的

| 问题 | 建议做法 |
|------|---------|
| 用户态程序的随机状态 | 在快照恢复后（可以借助 VMClock 的通知或 vsock 上的“你已恢复”消息）让程序重新初始化随机数、令牌、密钥 |
| 不要在快照前生成长期密钥 | 密钥、证书、凭证等在恢复后再获取（比如通过 MMDS 下发） |
| 网络标识 | 使用网络命名空间方案（第 11 篇），让每个克隆在独立的命名空间里使用相同的内部 IP，外部通过 NAT 区分；或者恢复后在 Guest 内重新配置网络 |
| TCP 连接 | 快照前关闭对外连接，恢复后重新建立 |
| 时间 | 恢复后让 Guest 重新同步时间 |

官方仓库中的 `docs/snapshotting/random-for-clones.md` 和 `network-for-clones.md` 详细讨论了这些问题。

---

## 六、兼容性：在哪里能恢复

快照对环境的要求非常严格。官方的原则是：**快照必须在与创建时相同的软件和硬件配置上恢复。**

| 维度 | 要求 |
|------|------|
| Firecracker 版本 | 快照格式有独立的版本号，新版本 Firecracker 只能加载与自己兼容的快照格式。格式升级时（版本历史中多次出现“用户需要重新生成快照”），旧快照就不能用了。`firecracker --snapshot-version` 可以查看当前支持的格式版本 |
| CPU 型号 | 必须相同。Guest 在快照前已经检测过 CPU 特性并据此运行，换成特性不同的 CPU 会出问题。CPU 模板可以帮助统一不同 CPU 的特性视图（第 16 篇） |
| GIC 版本（ARM64） | GICv2 与 GICv3 之间不能互相恢复 |
| 宿主机内核 | 原则上相同；官方仅在有限的情况下验证过“在更新的内核上恢复” |
| cgroup 版本 | 官方强烈建议使用 cgroup v2，cgroup v1 下恢复延迟明显偏高 |

另外，不要在 Guest 内核启动的极早期创建快照——那时中断处理可能还没就绪，恢复时 VMGenID 注入的中断可能导致 Guest 崩溃。

---

## 七、实际应用模式

### 7.1 预热池

```
启动 microVM → 内核启动 → 运行时初始化（加载 Python、导入库）→ 暂停 → 快照 S
                                                                    │
请求到来 → 从 S 恢复一台 microVM（毫秒级）→ 处理请求 → 销毁           ◀─┘
```

### 7.2 分层快照

- 第一层：通用的“已启动的 Linux”快照；
- 第二层：在此基础上加载了特定语言运行时的快照；
- 第三层：加载了某个用户应用代码的快照。

配合 UFFD 和去重存储，不同层之间的公共内存页只需存储一份。

### 7.3 暂停与迁移

把一台长期运行但暂时空闲的 microVM 存成快照、释放资源，需要时再恢复（甚至在另一台配置相同的宿主机上恢复）。这实际上提供了一种“冷迁移”能力，弥补了 Firecracker 不支持在线热迁移的不足（第 04 篇）。

---

## 小结

| 要点 | 内容 |
|------|------|
| 快照组成 | 状态文件 + 内存文件；磁盘由用户自行管理 |
| 创建 | `PATCH /vm Paused` → `PUT /snapshot/create` |
| 恢复 | 全新进程中 `PUT /snapshot/load`，TAP 名和磁盘路径需一致（或使用覆盖参数） |
| 快的原因 | 内存文件 `MAP_PRIVATE` 映射，按需加载、写时复制、多实例共享页缓存 |
| 差量快照 | 只保存脏页，稀疏文件，用 `snapshot-editor` 叠加（开发者预览） |
| UFFD | 自定义缺页处理，可按需从远端拉取、预取、去重 |
| 唯一性 | 同一状态恢复多次即存在风险；VMGenID 重播种内核随机数，其他状态需自行处理 |
| 兼容性 | 相同 CPU 型号、兼容的快照格式版本、相同 GIC 版本 |

---

## 思考题

1. 为什么创建快照前必须先暂停 microVM？如果不暂停会发生什么？
2. 从同一个快照恢复出 100 台 microVM，它们的宿主机内存总占用大概是怎样的？随着时间推移会怎样变化？
3. 一个 Web 服务在快照前已经生成了用于签发会话的 HMAC 密钥。从这个快照克隆出多个实例会有什么安全问题？
4. VMGenID 能解决 OpenSSL 在用户态缓存的随机数状态吗？为什么？
5. 快照文件为什么必须被当作可信输入？如果攻击者能修改 `snap.mem`，他能做什么？

---

## 下一篇预告

**[16. 性能与可观测性](16-performance-and-observability.md)**

下一篇系统地讨论如何测量 microVM 的启动时间、内存开销和 I/O 性能，影响这些指标的关键因素，CPU 模板的作用，以及如何利用 Firecracker 的日志和指标定位问题。
