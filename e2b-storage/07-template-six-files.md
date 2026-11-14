# 第 7 篇｜模板长什么样：一个 buildID 目录里的六个文件

> **本篇目标**：本篇是理解全书的钥匙。它回答一个问题：**一个模板在存储里到底是什么？**答案是一个以 buildID 命名的目录，里面六个文件。本篇逐个讲这六个文件，重点讲其中两个 header，也就是第 5 篇说的“拍平的映射表”。读完本篇，你能拿着一份 header，手工算出沙箱读第 N 块时该去哪个文件的哪个位置。

---

## 一、template、build、buildID

先分清三个词。

- **template（模板）**：用户眼里的“一个环境”，比如“装好 Python 和 Jupyter 的 Ubuntu”。它有一个模板 ID，还可以有别名（alias），比如 `base`。
- **build**：模板的**一次具体产物**。同一个模板改了 Dockerfile 重新构建，就多一个 build。每个 build 有一个 UUID，叫 **buildID**。
- **快照也是 build**：沙箱暂停时会打一次快照，这次快照的产物同样是一个新的 build，有新的 buildID（第 14 篇）。

所以存储里**只有 build，没有“模板”**。“模板”和“快照”都是数据库里的记录，指向某个 buildID。

> **一个常见的误会**：SDK 的 `create_snapshot()` 返回一个类似 `l1xjsvf1d8h3umr8d11y:default` 的字符串。它是“模板 ID:标签”，不是 buildID。想在存储目录里找到它对应的文件，要么按时间找最新的目录，要么去 PostgreSQL 的 build 表里查。

---

## 二、六个文件

每个 build 在存储里是一个目录，名字就是 buildID。在这套环境里，它位于 `/tmp/templates/<buildID>/`（为什么是这里，第 10 篇讲）：

```
$ ls -l /tmp/templates/7c1e9b52-3f0a-4d1e-9a3b-2c6f8d0e4a11/
-rw-r--r-- 1 root root       84  memfile.header
-rw-r--r-- 1 root root 2147483648  memfile
-rw-r--r-- 1 root root     1224  metadata.json
-rw-r--r-- 1 root root     4344  rootfs.ext4.header
-rw-r--r-- 1 root root 5368709120  rootfs.ext4
-rw-r--r-- 1 root root    41820  snapfile
```

代码里，这六个名字是写死的常量：

```go
MemfileName  = "memfile"
RootfsName   = "rootfs.ext4"
SnapfileName = "snapfile"
MetadataName = "metadata.json"
HeaderSuffix = ".header"
```

逐个说：

| 文件 | 内容 | 是完整的还是只有改动 |
|---|---|---|
| `snapfile` | Firecracker 的机器状态：CPU 寄存器、设备状态等（第 6 篇） | 每次都是完整的，本来就小 |
| `memfile` | 客户机内存的数据 | 模板构建完时基本完整；暂停快照时只有脏页 |
| `memfile.header` | 内存的映射表 | 每次都是一张完整的表 |
| `rootfs.ext4` | 根盘的数据 | 模板构建完时完整；暂停快照时只有写过的块 |
| `rootfs.ext4.header` | 根盘的映射表 | 每次都是一张完整的表 |
| `metadata.json` | 内核版本、Firecracker 版本、启动命令、预取信息等 | 完整 |

关键在第三列。`memfile` 和 `rootfs.ext4` 叫**数据文件**，它们可能只装着“这一层改了什么”；两个 `.header` 叫**映射表**，它们永远描述**完整**的内存和磁盘，告诉你每一块该去哪一层取。

---

## 三、metadata.json：模板的“说明书”

`metadata.json` 是一个 JSON 文件，大致长这样（节选、简化）：

```json
{
  "version": 2,
  "template": {
    "build_id": "7c1e9b52-...",
    "kernel_version": "vmlinux-6.1.158",
    "firecracker_version": "v1.13.1"
  },
  "context": {
    "user": "user",
    "workdir": "/home/user",
    "env_vars": { "PATH": "..." }
  },
  "start": {
    "start_command": "...",
    "ready_command": "..."
  },
  "from_image": "harbor:443/e2b-orchestration/ubuntu:22.04-custom",
  "prefetch": {
    "memory": {
      "indices": [0, 1, 37, 38, 512, ...],
      "access_types": ["r", "w", "r", "r", "p", ...],
      "block_size": 2097152
    }
  }
}
```

各部分的用途：

- `template`：恢复这个 build 时用哪个内核、哪个 Firecracker。orchestrator 据此找 `/fc-kernels/<内核版本>/` 和 `/fc-versions/<FC 版本>/`（第 6 篇）。
- `context`：之后在沙箱里执行命令时默认用哪个用户、哪个目录、哪些环境变量。
- `start`：模板的启动命令和就绪检查命令。
- `from_image` 或 `from_template`：这个模板是基于哪个镜像或哪个模板做出来的。
- `prefetch`：**预取映射**。模板构建时记录下“沙箱启动过程中按顺序访问了哪些内存块，是读、写还是预取”，以后恢复时提前把这些块准备好（第 13 篇）。

---

## 四、header：拍平的映射表

### 4.1 两部分

每个 `.header` 文件是一个小小的二进制文件，由两部分组成：

```
┌──────────────── 元数据（64 字节）────────────────┐
│ Version     版本号（当前是 3）                    │
│ BlockSize   块大小                               │
│ Size        完整的内存或磁盘有多大                 │
│ Generation  代数：模板构建出来是 0，每快照一次 +1   │
│ BuildId     这一代自己的 buildID                  │
│ BaseBuildId 最初那一代（第 0 代）的 buildID        │
├──────────────── 映射数组（每条 40 字节）───────────┤
│ 映射 1： Offset  Length  BuildId  BuildStorageOffset │
│ 映射 2： ……                                       │
│ ……                                               │
└──────────────────────────────────────────────────┘
```

代码里的定义（原样）：

```go
type Metadata struct {
    Version     uint64
    BlockSize   uint64
    Size        uint64
    Generation  uint64
    BuildId     uuid.UUID
    BaseBuildId uuid.UUID
}

type BuildMap struct {
    Offset             uint64     // 在完整的内存或磁盘里，从哪个字节开始
    Length             uint64     // 这一段多长
    BuildId            uuid.UUID  // 这一段的数据实际存在哪个 build 里
    BuildStorageOffset uint64     // 在那个 build 的数据文件里，从哪个字节开始
}
```

两个结构都用小端序直接写成二进制，没有任何压缩。所以 header 很小：64 字节加上每条映射 40 字节。

### 4.2 块大小

元数据里的 `BlockSize` 决定了映射的粒度：

- **根盘**：4 KiB；
- **内存**：模板用大页时是 2 MiB，不用大页时是 4 KiB。

所有映射的 `Offset` 和 `Length` 都是块大小的整数倍。

> 这套环境的 ARM 补丁放宽了一处限制：内存 header 是 2 MiB 一块，但某一次增量可以按 4 KiB 的页来记（检查点、暂停时的脏页是按 4 KiB 统计的），合成新 header 时块大小随之变细。因为映射本来就是按字节记的，2 MiB 的区间一定也是 4 KiB 的整数倍，旧的映射依然有效。

### 4.3 映射数组覆盖全部

映射数组按 `Offset` 从小到大排列，首尾相接，**不重不漏地覆盖从 0 到 `Size` 的整个范围**。任何一个字节，都能在且只能在一条映射里找到。

---

## 五、手工查一次表

### 5.1 一个例子

假设有这样一条链：

- **build A**：模板构建完成，第 0 代。根盘 5 GiB，`rootfs.ext4` 是完整的 5 GiB。
- **build B**：从 A 创建沙箱，跑了一会儿，写了根盘第 5000～5099 块，然后暂停。B 的 `rootfs.ext4` 只有这 100 块，400 KiB。
- **build C**：从 B 恢复，写了第 1000～1001 块，然后又暂停。C 的 `rootfs.ext4` 只有这 2 块，8 KiB。

C 的 `rootfs.ext4.header` 是这样的（块号换算成字节时乘 4096）：

| # | Offset（块） | Length（块） | BuildId | BuildStorageOffset（块） |
|---|---|---|---|---|
| 1 | 0 | 1000 | A | 0 |
| 2 | 1000 | 2 | **C** | 0 |
| 3 | 1002 | 3998 | A | 1002 |
| 4 | 5000 | 100 | **B** | 0 |
| 5 | 5100 | 1305620 | A | 5100 |

元数据：`Generation=2`，`BuildId=C`，`BaseBuildId=A`，`Size=5 GiB`，`BlockSize=4096`。

### 5.2 读几个块

**读第 1001 块**：

1. 找到包含 1001 的映射：第 2 条，`Offset=1000`，`Length=2`。
2. 偏移量 = 1001 − 1000 = 1。
3. 数据在 C 的 `rootfs.ext4` 里第 0 + 1 = 1 块处。

**读第 5050 块**：

1. 第 4 条，`Offset=5000`。
2. 偏移量 = 50。
3. 数据在 B 的 `rootfs.ext4` 第 0 + 50 = 50 块处。

**读第 3 块**：

1. 第 1 条。
2. 数据在 A 的 `rootfs.ext4` 第 3 块处。

不管链有多长，**都只查一次表**。代码里这个操作叫 `GetShiftedMapping`：给一个偏移，返回“去哪个 build、那个文件里的哪个偏移、从这里开始还能连续读多长”。

### 5.3 注意 BuildStorageOffset

看第 3 条和第 5 条：A 的数据是完整的，所以 `BuildStorageOffset` 就等于 `Offset`。而 B 和 C 的数据文件只装了改动，紧凑排列，所以 B 的那 100 块从 B 文件的第 0 块开始放。`BuildStorageOffset` 就是用来把“完整磁盘里的位置”翻译成“diff 文件里的位置”的。

---

## 六、新的一代 header 是怎么来的

打快照时，新 header 由“上一代 header”加“本次改动”合成，分三步：

```go
// 简化自 ToDiffHeader
diffMapping := 本次改动.toDiffMapping(新buildID)      // ① 把位图变成映射
m := MergeMappings(上一代.Mapping, diffMapping)       // ② 覆盖合并
m = NormalizeMappings(m)                              // ③ 规整
metadata := 上一代.Metadata.NextGeneration(新buildID) // 代数 +1，BaseBuildId 不变
```

**① 位图变映射**：本次改动是一张位图，第 N 位为 1 表示第 N 块被写过。把连续的 1 合并成一段，依次编进新的数据文件。比如写过第 1000、1001 块，就得到一条 `{Offset=1000, Length=2, BuildId=C, BuildStorageOffset=0}`。

**② 覆盖合并**：把新映射“盖”在旧映射上。旧映射里被盖住的部分切掉，剩下的部分保留。上面例子里，B 的第 3 条原本是 `{0, 5000, A, 0}`，被 C 的 `{1000, 2}` 一盖，切成了 `{0, 1000, A, 0}`、`{1000, 2, C, 0}`、`{1002, 3998, A, 1002}` 三段。

**③ 规整**：把相邻且可以连起来的映射合并，减少条数。

---

## 七、全零块：不占存储的“空洞”

客户机内存里有大量全零的页，比如还没用过的空闲内存。把它们写进 memfile 纯属浪费。

E2B 的做法是：映射的 `BuildId` 可以是一个特殊值 **`uuid.Nil`**（全零 UUID），表示“这一段全是零，不在任何文件里”。读的时候遇到它，直接返回零。

```
 映射：{Offset=1 GiB, Length=512 MiB, BuildId=00000000-0000-..., BuildStorageOffset=0}
 意思：从 1 GiB 开始的 512 MiB 全是零
```

全零的判断发生在模板构建后的第一次快照：Firecracker 的 `GET /memory` 接口会返回“哪些页全是零”（第 6 篇），这些页被映射到 `uuid.Nil`。之后暂停产生的快照只关心脏页，不再做全零剔除。

---

## 八、拍平的代价，再说一次

第 5 篇说过：只要有 header 指向某一层，那一层就必须留着。看上面 C 的 header，它直接引用了 A、B、C 三个 build 的数据文件。

所以：

- 删除 B 的快照记录，**不能**删掉 `/tmp/templates/<B>/` 目录，否则 C 就坏了；
- 删快照、删模板都应该通过 API，让服务端判断哪些数据还在被引用；
- 不要手工去 `/tmp/templates` 里删目录。

---

## 九、新旧格式

代码里还留着一段兼容逻辑：如果在存储里找不到 `.header` 文件，就把数据文件当成一个“没有 header 的老模板”，假设它是完整的，块大小按内存 2 MiB、根盘 4 KiB 处理，自动生成一张只有一条映射的 header：

```
{Offset=0, Length=整个文件, BuildId=自己, BuildStorageOffset=0}
```

这是为了兼容很早以前构建的模板。这套环境的所有模板都是新构建的，都有 header，这段逻辑基本用不到。

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| build | 模板的一次产物或一次快照，以 buildID 为名的一个目录 |
| 六个文件 | `snapfile`、`memfile`、`memfile.header`、`rootfs.ext4`、`rootfs.ext4.header`、`metadata.json` |
| 数据文件 | `memfile` 和 `rootfs.ext4`，可能只装这一层的改动 |
| header | 永远描述完整的内存或磁盘：64 字节元数据加若干 40 字节映射 |
| 映射 | 一段范围的数据在哪个 build 的数据文件里、从哪开始 |
| Generation | 代数，模板构建出来是 0，每快照一次加 1 |
| 查表 | 给一个偏移，一次找到 build 和那个文件里的偏移 |
| 合成新 header | 位图变映射、覆盖合并、规整 |
| `uuid.Nil` | 全零的一段，不占存储，读时直接给零 |
| metadata.json | 内核和 FC 版本、运行上下文、启动命令、预取映射 |

**下一篇预告**：[《模板的原料仓库：Harbor 与镜像的存放》](08-harbor-image-registry.md)。知道了模板长什么样，接下来看它是怎么做出来的。做模板的第一步是拿到一个 Docker 镜像，比如 `harbor:443/e2b-orchestration/ubuntu:22.04-custom`。下一篇讲这个镜像存在哪、镜像在仓库里是怎么存的、这套环境的 Harbor 是怎么装起来的，以及 template-manager 是怎么从 Harbor 拿到镜像的。
