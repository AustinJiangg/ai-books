# 第 14 篇｜暂停与恢复：一次增量快照是怎么做出来的

> **本篇目标**：第四部分讲快照。本篇从最常用的“暂停”讲起：用户调用 `sandbox.pause()` 之后，orchestrator 做了哪些事，按什么顺序做，每一步为什么这样做。读完本篇，你会知道一次暂停怎么产生一个新的 build：内存的脏页怎么被找出来、怎么从 Firecracker 进程里直接拷出来；磁盘的 COW 文件怎么变成 diff；新的 header 怎么合成；六个文件怎么写进 `/tmp/templates`。最后讲恢复，以及删快照时存储里的文件到底删不删。

---

## 一、暂停对用户意味着什么

E2B 的 SDK 里有一个操作：

```python
sbx.pause()          # 暂停
...
sbx = Sandbox.connect(sbx.sandbox_id)   # 过几小时再恢复，ID 不变
```

暂停之后：

- 这个沙箱不再占用 CPU 和内存，Firecracker 进程退出了；
- 它的状态（内存里所有进程、根盘上所有文件）被存了下来；
- 之后可以按同一个沙箱 ID 恢复，里面的程序从暂停那一刻接着运行。

从存储的角度看，**暂停 = 打一次快照，产生一个新 build**。这个新 build 只装“这个沙箱从上次恢复到现在改过的东西”，header 把其余部分指向之前的各代 build（第 7 篇）。

---

## 二、谁来发起

调用链是：

```
SDK ──▶ api ──▶ orchestrator 的 Pause 接口（gRPC）
          │
          └─ api 先在数据库里为这次快照记一条 build 记录，分配新的 buildID，随请求带过来
```

orchestrator 收到请求后：

1. 找到这个沙箱，并“锁住”它，防止同时有别的操作（比如另一次暂停、检查点）；
2. 调用 `Sandbox.Pause` 打快照；
3. 把快照**立刻**放进本机的模板缓存表（第 11 篇），这样马上恢复时不用等上传；
4. **后台**上传到存储后端，不等它完成就返回；
5. 后台停掉这个沙箱，清理资源。

注意第 3、4 步：暂停接口返回时，快照可能还没写进 `/tmp/templates`。但本机已经可以用它恢复了，因为数据都在本地缓存里。

---

## 三、打快照的八步

`Sandbox.Pause` 的主体，按顺序是这些步骤：

```
 ① 停健康检查
 ② 让 Firecracker 暂停虚拟机
 ③ 让 Firecracker 写 snapfile（不导出内存）
 ④ 问出这一轮哪些内存页要导出（脏页位图）
 ⑤ 把这些页从 Firecracker 进程里直接拷出来，生成 memfile diff 和新 memfile.header
 ⑥ 弹出磁盘的 COW 文件，停掉沙箱，生成 rootfs diff 和新 rootfs.ext4.header
 ⑦ 写 metadata.json
 ⑧ 返回六样东西，交给上层放进缓存、后台上传
```

逐步看。

### 3.1 ① ② 先停下来

先停掉对 envd 的健康检查，免得暂停期间误报“沙箱死了”。然后调用 Firecracker 的暂停接口：所有 vCPU 停止运行。从这一刻起，客户机内存和磁盘都不会再变化，可以安全地读了。

### 3.2 ③ 只写机器状态

```
PUT /snapshot/create
{ "snapshot_type": "Full", "snapshot_path": "/orchestrator/template/<新buildID>/cache/<随机>/snapfile" }
```

注意**没有** `mem_file_path`。这是定制版 Firecracker 的特性（第 6 篇）：只写 vCPU 和设备状态，并把磁盘缓冲刷下去，不导出内存。snapfile 直接写在本地缓存目录里。

### 3.3 ④ 哪些页要导出

这是整个流程最关键的一步，也是 ARM 补丁改动最多的地方。要回答的问题是：

> 和这个沙箱的“父 build”相比，客户机内存有哪些页不一样了？

只要这些页导出了，新 build 的 header 就能把其余页指回父 build，恢复时内容完全一致。

orchestrator 有三种回答方式，按优先级：

| 来源 | 判据 | 什么时候用 |
|---|---|---|
| **写跟踪位图** | Firecracker 打开了写跟踪（KVM 脏页日志），直接问它“哪些页被写过”，再并上之前检查点时攒下的部分 | 本机开了写跟踪（有 HDBSS 硬件，或手工设了 `FC_TRACK_DIRTY_PAGES=true`） |
| **常驻页判据** | 问 Firecracker 的 `GET /memory/dirty`：页在内存里、且没有 UFFD 写保护封条 | 没开写跟踪，或写跟踪的结果不可信 |
| **常驻 + 全零** | 问 `GET /memory`：哪些页在内存里、哪些全是零 | 虚拟机不是从快照恢复的（NoopMemory，第 13 篇） |

第二种是上游原本的做法。在 x86 上它是精确的；在 ARM 补丁下，因为填页时不再贴封条，它变成了“**被换入过的页**都算”，比真正写过的页多。第 15 篇专门讲这件事和第一种方式的来历。

不管哪种，结果都是一张位图：第 N 位为 1，表示第 N 页要导出。

### 3.4 ⑤ 直接从 Firecracker 进程里拷

有了位图，接下来要把这些页的内容拿出来。Firecracker 没有导出内存（第 ③ 步），orchestrator 自己去拿：

```go
// 简化自 ExportMemory
m := fc.GET("/memory/mappings")          // 客户机内存每一段在 FC 进程里的虚拟地址
for 位图里每一段连续的页 {
    远端地址 += m.转成FC进程里的地址(这一段)
}
cache := NewCacheFromProcessMemory(pid, 远端地址, 本地文件)
         // 内部用 process_vm_readv 一次性把这些地址的内容读进本地文件
```

本地文件是 `/orchestrator/build/<新buildID>-memfile-<随机>`，脏页按顺序紧凑地写进去。这就是新 build 的 memfile diff。

为什么不让 Firecracker 自己写？

- 少一次中转：Firecracker 写文件、orchestrator 再读文件，变成 orchestrator 直接读一次；
- 天然只导出脏页：想要哪几页就读哪几页；
- `process_vm_readv` 一次系统调用可以读很多段不连续的地址。

### 3.5 合成新的 memfile.header

```go
newHeader := 位图.ToDiffHeader(父build的memfile.header, 新buildID)
```

就是第 7 篇第六节的三步：位图变映射、覆盖合并、规整。代数加 1。

ARM 补丁在这里有一处细节：写跟踪位图是按 **4 KiB** 记的，而模板的 memfile header 是 2 MiB 一块。合成时新 header 的块大小会跟着变细到 4 KiB。因为映射本来就是按字节记的，旧的 2 MiB 映射在 4 KiB 粒度下依然有效。

### 3.6 ⑥ 磁盘：弹出 COW 文件

磁盘的处理在第 12 篇讲过，这里把顺序串起来：

1. 把 overlay 的上层（COW 文件）弹出来，不再接受写；
2. **在后台停掉沙箱**：Firecracker 退出，NBD 断开，设备归还；
3. 等 NBD 上所有请求都处理完；
4. 按位图从小到大，把 COW 文件里写过的块紧凑地写进 `/orchestrator/build/<新buildID>-rootfs.ext4-<随机>`，全零的块单独记、不写；
5. 用同样的方法合成新的 rootfs.ext4.header。

磁盘这一侧没有“判据”之争：COW 文件里有的块，一定是写过的。**磁盘增量永远是精确的。**

注意第 2 步：打完这一步，原来那台虚拟机就没了。暂停本来就要停掉它，所以没问题。但这也说明，同一套代码如果用在“打快照后继续运行”的场景（比如构建模板时每一层），要用新 build **重新创建**一个沙箱接着跑（第 9 篇的“从上一层恢复”就是这样）。

### 3.7 ⑦ ⑧ 收尾

把模板的 `metadata.json` 改一下（换成新 buildID、当前内核和 Firecracker 版本），写到本地缓存目录。然后返回六样东西：

| 东西 | 在哪 |
|---|---|
| snapfile | `/orchestrator/template/<新buildID>/cache/<随机>/snapfile` |
| metadata.json | 同一目录 |
| memfile diff | `/orchestrator/build/<新buildID>-memfile-<随机>` |
| memfile.header | 内存里 |
| rootfs diff | `/orchestrator/build/<新buildID>-rootfs.ext4-<随机>` |
| rootfs.ext4.header | 内存里 |

---

## 四、上传

上层把这六样东西放进模板缓存后，后台上传：

```
StoreFile(memfile diff  →  <新buildID>/memfile)
StoreFile(rootfs diff   →  <新buildID>/rootfs.ext4)
Put(序列化的 memfile.header  →  <新buildID>/memfile.header)
Put(序列化的 rootfs header   →  <新buildID>/rootfs.ext4.header)
StoreFile(snapfile      →  <新buildID>/snapfile)
StoreFile(metadata.json →  <新buildID>/metadata.json)
```

在这套环境里，存储后端是 Local（第 10 篇），“上传”就是把文件**拷贝**到 `/tmp/templates/<新buildID>/` 下。拷贝完，本地缓存里的那几份还在，按第 11 篇的 TTL 慢慢回收。

所以一次暂停之后，同一份 diff 数据在机器上至少有两份：一份在 `/orchestrator/build`（硬盘，及其页缓存），一份在 `/tmp/templates`（tmpfs，即内存）。

---

## 五、一次暂停产生了多少数据

举个例子：一个 2 GiB 内存、5 GiB 根盘的沙箱，恢复后跑了 10 分钟，装了一个 30 MB 的包。

| 文件 | 大小量级 | 由什么决定 |
|---|---|---|
| snapfile | 几十 KB | 虚拟机配置，基本固定 |
| memfile | 几十 MB 到几百 MB | 导出的页数（取决于第 ④ 步用哪种判据） |
| memfile.header | 几 KB 到几十 KB | 映射条数 |
| rootfs.ext4 | 几十 MB | 写过的磁盘块：包本身加文件系统元数据 |
| rootfs.ext4.header | 几 KB | 映射条数 |
| metadata.json | 几 KB | 含预取清单 |

内存 diff 的大小是最不稳定的一项。在 x86 上它约等于“写过的页”；在这套 ARM 环境、没开写跟踪的情况下，它约等于“这一轮恢复后**碰过**的所有页”，往往大得多。第 15 篇看实测数字。

---

## 六、恢复

恢复（resume）在实现上就是“用某个 build 创建沙箱”，和从模板创建沙箱是**同一条路**：

```
 api 查数据库：这个沙箱暂停时对应哪个 buildID
      │
      ▼
 orchestrator 创建沙箱，指定这个 buildID
      │  模板缓存表里有吗？刚暂停的话有（第二节第 3 步），否则从存储后端加载 header 等小文件
      │  分配网络槽位、NBD 设备
      │  新建 COW 文件（空的）、UFFD socket
      │  启动新的 Firecracker，加载 snapfile，内存走 UFFD
      ▼
 客户机从暂停那一刻接着运行
      │  读内存 / 读磁盘 → 查新 build 的 header → 去对应那一代的数据里取
```

几点要注意：

- **沙箱 ID 不变，但一切都是新的**：新的 Firecracker 进程、新的 NBD 设备、新的 COW 文件、新的 UFFD。文件名里的随机串（第 6 篇）就是为了让新旧两套文件不撞名；
- **链变长了**：恢复后再暂停，新 build 的父亲是刚才这个 build，代数再加 1。header 是拍平的，链再长，读一页也只查一次表（第 5 篇）；
- **检查点作废**：沙箱打过的检查点（第 16 篇）属于旧的 Firecracker 进程，恢复后全部作废。

---

## 七、删除快照：数据库删了，文件还在

第 5、7 篇反复强调：只要有 header 指向某一代 build，那一代的数据文件就必须留着。

设想这样一条链：

```
 模板 A ──▶ 暂停得到 B ──▶ 恢复、再暂停得到 C
```

C 的 header 里同时有指向 A、B、C 的映射。如果有人直接 `rm -rf /tmp/templates/<B>`，C 恢复时读到指向 B 的那些页，就会去一个不存在的文件里读，沙箱启动失败或运行中出错。所以**不要手工删 `/tmp/templates` 里的目录**。

那通过 SDK 或 API 删除呢？这个版本的 api 是这样做的：

- 删一个暂停中沙箱的快照、删一个模板：**只删数据库里的记录**（模板、build、别名等），并让 api 的缓存失效；
- **不删存储里的文件**。删模板的代码里有一段注释写得很直白：build 是分层的 diff，可能还被别的 build 的 header 引用，所以这里**故意**不从存储里删除构建产物。

真正会删存储文件的只有两种情况：

- 模板构建**失败**：template-manager 删掉这次 buildID 前缀下的文件（第 9 篇）；
- 构建被**取消**：api 让 template-manager 删掉正在构建的那几个 build。

换句话说，在这套环境里，`/tmp/templates` **只增不减**。正常删除不会让它变小。它变小只有三种途径：宿主机重启（tmpfs 清空，全部丢失）、`systemd-tmpfiles` 清理 10 天没访问的文件（第 10 篇，可能误删仍被引用的旧层），或者人工清理。这是一个需要运维关注的容量问题，第 19 篇会再算这笔账。

删除之后，本地缓存里的那几份也不会立刻消失，要等 25 小时 TTL 过期或 orchestrator 重启（第 11 篇）。

---

## 八、看一眼

```bash
# 刚暂停后，本地缓存里多了什么（按时间倒序）
ls -lt /orchestrator/build | head
ls -lt /orchestrator/template | head

# 存储后端里的新 build（Local 后端）
ls -lt /tmp/templates | head -3
du -sh /tmp/templates/<新buildID>/*

# orchestrator 日志里，这次暂停用了哪种判据、导出了多少页
#   "memfile diff page set for the native pause"  source=tracked / tracked+accumulated / resident
```

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| 暂停 | 打一次快照，产生新 build，停掉 Firecracker |
| 先缓存后上传 | 快照先放进本机模板缓存，上传在后台进行 |
| snapfile | 不传 `mem_file_path`，只写机器状态 |
| 脏页位图 | 三种来源：写跟踪位图、常驻页判据、常驻加全零 |
| `process_vm_readv` | 按 `/memory/mappings` 直接从 Firecracker 进程读出要导出的页 |
| 新 header | 位图变映射、覆盖父 header、规整，代数加 1 |
| 磁盘 diff | 弹出 COW 文件、停沙箱、按位图导出，永远精确 |
| 上传 | Local 后端就是拷贝到 `/tmp/templates/<buildID>/` |
| 恢复 | 用这个 build 创建沙箱，ID 不变，进程、设备、文件全是新的 |
| 删除 | 走 API 只删数据库记录，不删文件；手工删中间一代会打断后代 |

**下一篇预告**：[《ARM 上的增量为什么“偏大”：脏页判据与实测》](15-arm-incremental-snapshot.md)。本篇第 3.3 节留了一个问题：同样是“暂停一次”，为什么在这套 ARM 环境上导出的内存页会比 x86 上多很多？下一篇从 UFFD 写保护封条讲起，看 ARM 补丁注释掉的那三行带来了什么，实测数字是多少，以及补丁后来加的“写跟踪位图”这条路是怎么把它补回来的。
