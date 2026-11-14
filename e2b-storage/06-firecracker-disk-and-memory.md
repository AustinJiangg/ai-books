# 第 6 篇｜虚拟机的“盘”和“内存条”：Firecracker 眼中的存储

> **本篇目标**：基础篇的最后一篇，把视角转到虚拟机本身。Firecracker 给客户机提供了什么样的磁盘和内存？它怎么找到内核和根盘？它原生的快照功能存了什么、有什么局限？E2B 用的定制版 Firecracker 为了配合“按需取”“只存改动”，又多做了哪几件事？读完本篇，你会看到第 3、4 篇的 NBD 和 userfaultfd 是在哪里接上虚拟机的。

---

## 一、Firecracker 是什么

**Firecracker** 是亚马逊开源的一个虚拟机监控程序（VMM），专门用来跑“微虚拟机”（microVM）：只模拟最少的设备，启动快、占内存少。

在宿主机上，一台 Firecracker 虚拟机就是**一个普通进程**：

- 客户机的全部内存，就是这个进程地址空间里的一大块内存；
- 客户机的硬盘，是这个进程打开的一个宿主上的文件或设备；
- 外部通过一个 unix socket 上的 HTTP 接口控制它：设置内核、设置磁盘、启动、暂停、打快照……

本书只关心它的存储部分。

---

## 二、Firecracker 给客户机提供的存储设备

### 2.1 根盘：virtio-blk

Firecracker 给客户机提供一块 **virtio-blk** 磁盘。virtio 是一套“半虚拟化”设备标准：客户机知道自己在虚拟机里，用一套简单高效的协议和宿主通信，而不是假装自己在操作真实的硬盘控制器。

在客户机里，这块盘显示为 `/dev/vda`，挂载为根目录 `/`。

在宿主那头，Firecracker 需要一个**路径**。orchestrator 通过接口这样告诉它：

```go
// 简化
PUT /drives/rootfs
{
    "drive_id":       "rootfs",
    "path_on_host":   "/fc-vm/rootfs.ext4",   // 宿主上的路径
    "is_root_device": true,                    // 是根盘
    "is_read_only":   false                    // 可写
}
```

客户机读写 `/dev/vda` 的第 N 块，Firecracker 就去读写 `path_on_host` 的第 N×4096 字节处。至于这个路径背后是一个普通文件，还是一台 NBD 设备，Firecracker 不在乎。

### 2.2 内存

客户机的内存大小通过“机器配置”指定：

```go
// 简化
PUT /machine-config
{
    "vcpu_count":   2,
    "mem_size_mib": 2048,
    "smt":          false,     // ARM 上 Firecracker 不支持 SMT，补丁改成 false
    "huge_pages":   "2M",      // 用 2 MiB 大页支撑客户机内存
    "track_dirty_pages": ...   // 是否打开写跟踪，第 16 篇讲
}
```

`huge_pages: "2M"` 让 Firecracker 从大页池里申请客户机内存。这套环境的沙箱默认用大页。

### 2.3 内核

客户机内核也是一个宿主上的文件。orchestrator 按版本号去固定目录找：

```
/fc-kernels/<内核版本>/vmlinux.bin
```

部署脚本 `init-client.sh` 把 RPM 自带的内核放成了三份：

| 目录 | 放的是 |
|---|---|
| `/fc-kernels/vmlinux-6.1.158/` | RPM 里的 `bin/vmlinux.bin` |
| `/fc-kernels/vmlinux-6.1.102/` | 同一个文件，另一个名字 |
| `/fc-kernels/vmlinux-6.6.0-132.0.0/` | RPM 里的 `bin/vmlinux.bin.openeuler` |

目录名只是一个寻址用的标签。建模板时如果不指定内核版本，api 用编译进去的默认值 `vmlinux-6.1.158`。少了这个目录，建模板会在一开始就失败。

### 2.4 Firecracker 本身

Firecracker 的可执行文件也按版本放：

```
/fc-versions/<版本>/firecracker
```

这套环境用的是 RPM 自带的**定制版** Firecracker（`bin/firecracker`，只在 aarch64 包里有），部署时放到 `/fc-versions/v1.13.1/firecracker`。它和官方版的区别见本篇第五节。

---

## 三、同一个路径，不同的盘：mount 命名空间

这里有一个很巧妙的设计，和《E2B 沙箱网络从零讲透》里“每个沙箱都是 169.254.0.21”是同一个道理。

### 3.1 问题

快照会**记录**根盘的路径。一个模板的快照里写着“根盘在 `/fc-vm/rootfs.ext4`”。所有从这个快照恢复的沙箱，Firecracker 都会去打开**同一个路径**。

可每个沙箱的根盘应该是不同的东西：沙箱 1 用 `/dev/nbd3`，沙箱 2 用 `/dev/nbd7`。同一个路径怎么指向不同的盘？

### 3.2 解法

orchestrator 不是直接启动 Firecracker，而是用 `unshare -m` 先给它开一个**独立的 mount 命名空间**，再在里面执行一小段脚本（简化）：

```bash
unshare -m -- bash -c '
  mount --make-rprivate /
  mount -t tmpfs tmpfs /fc-vm                       # 在自己的命名空间里，/fc-vm 是一块私有的 tmpfs
  ln -s /orchestrator/sandbox/rootfs-<沙箱ID>-<随机串>.link /fc-vm/rootfs.ext4
  mkdir -p /fc-vm/vmlinux-6.1.158
  ln -s /fc-kernels/vmlinux-6.1.158/vmlinux.bin /fc-vm/vmlinux-6.1.158/vmlinux.bin
  exec <进入网络命名空间> /fc-versions/v1.13.1/firecracker --api-sock /tmp/fc-<沙箱ID>-<随机串>.sock
'
```

mount 命名空间和网络命名空间类似：每个命名空间有自己的一套挂载点，互相看不见。所以：

- 每个 Firecracker 都看到一个 `/fc-vm/rootfs.ext4`；
- 但在各自的命名空间里，它指向不同的东西。

### 3.3 一条三跳的链接

顺着链接走下去：

```
 Firecracker 打开 /fc-vm/rootfs.ext4                （快照里记的固定路径）
        │ 符号链接（在私有 tmpfs 里）
        ▼
 /orchestrator/sandbox/rootfs-<沙箱ID>-<随机串>.link  （每个沙箱一个）
        │ 符号链接（orchestrator 准备好根盘后指过去）
        ▼
 /dev/nbd3                                          （这个沙箱分到的 NBD 设备）
```

中间那个 `.link` 文件是 orchestrator 用来“改指向”的把手。根盘准备好之前它指向 `/dev/null`，准备好之后改成指向分到的 `/dev/nbdN`。

文件名里的随机串，是为了让同一个沙箱 ID 暂停又恢复时，新旧两份文件不会撞名。这个随机串后面在 COW 文件、socket 文件的名字里都会看到。

---

## 四、原生快照：存了什么，局限在哪

### 4.1 创建快照

Firecracker 原生支持快照。先暂停虚拟机，再调用：

```go
PUT /snapshot/create
{
    "snapshot_type": "Full",            // 或 "Diff"
    "snapshot_path": "/path/snapfile",  // 机器状态
    "mem_file_path": "/path/memfile"    // 内存
}
```

产物两个文件：

| 文件 | 内容 | 大小 |
|---|---|---|
| snapfile（也叫 vmstate） | CPU 寄存器、中断控制器、各虚拟设备的状态，以及磁盘路径、内存配置等 | 很小，KB 到 MB 级 |
| memfile | 客户机内存 | 和客户机内存一样大 |

注意：**快照不包括磁盘**。磁盘内容由外部自己保证和快照一致。

两种类型：

- **Full**：整份内存写出去。2 GB 的客户机就是 2 GB 的文件，每次快照都写一遍。
- **Diff**：只写自上次快照以来被写过的页。需要先打开写跟踪（`track_dirty_pages`），产物是一个稀疏文件，**不能单独加载**，要自己把基础快照和各代 Diff 合并成一份完整的 memfile 才能用。

### 4.2 加载快照

启动一个新的 Firecracker 进程，调用：

```go
PUT /snapshot/load
{
    "snapshot_path": "/path/snapfile",
    "mem_backend": {
        "backend_type": "File" 或 "Uffd",
        "backend_path": "/path/memfile" 或 "/path/uffd.sock"
    }
}
```

内存后端有两种：

- **File**：Firecracker 把 memfile 整个 mmap 进来，靠内核的缺页从文件里读。
- **Uffd**：Firecracker 建一个 userfaultfd，登记客户机内存区域，然后通过 `backend_path` 指定的 unix socket 把这个 UFFD 的文件描述符**交给外部程序**。之后客户机缺页，由外部程序负责填页（第 4 篇第五节）。

E2B 用的是 **Uffd** 后端。外部程序就是 orchestrator。

### 4.3 原生方案对 E2B 的三个不合适

1. **全量快照的开销和内存大小挂钩**，和“改了多少”无关。一个空闲的沙箱暂停一次也要写 2 GB。
2. **Diff 链要自己合并**，而且合并是线性的，链一长，恢复就慢。
3. **产物是本地文件**。要放到存储后端、多台机器共享、按需取页，都得另外做一层。

---

## 五、定制版 Firecracker 多做的几件事

E2B 用的不是官方 Firecracker，而是一个定制版本。这套环境 RPM 里带的那个二进制，又在 E2B 定制版的基础上加了回滚功能。和存储有关的改动有这几处：

### 5.1 打快照时可以不导出内存

`mem_file_path` 变成**可选的**。不传它，Firecracker 只写 snapfile，并把磁盘缓冲刷下去，**不导出内存**。

为什么？因为 E2B 想自己导出内存，而且只导出脏页（第 14 篇）。

### 5.2 新增三个查询接口

| 接口 | 返回什么 | 用途 |
|---|---|---|
| `GET /memory/mappings` | 客户机内存的每一段，对应 Firecracker 进程里的哪个虚拟地址、多大、页多大 | orchestrator 据此用 `process_vm_readv` 去拷内存 |
| `GET /memory/dirty` | 一张位图：哪些页自开启写保护以来被写过 | 暂停时只导出脏页 |
| `GET /memory` | 两张位图：哪些页在内存里（常驻），哪些页全是零 | 第一次快照时剔除全零页 |

前两个配合起来，orchestrator 就能做到：“问 Firecracker 哪些页脏了，再问这些页在你进程的哪个地址，然后我自己把它们拷出来。”Firecracker 只负责“停下来、报告情况”，数据搬运由 orchestrator 完成。

### 5.3 回滚

这套环境的定制版还多了**原地回滚**的能力：不新开进程，直接把客户机内存和 vCPU 状态倒回到某个检查点。配套的，打快照时可以额外写出一个**脏页位图文件**（FCDB 格式），交给 orchestrator 做检查点的增量。第 16 篇讲。

### 5.4 这些改动在哪看得到

定制版 Firecracker 的源码不在本书依据的两个仓库里。本书对它的描述来自两处：

- orchestrator 里调用它的代码，以及接口定义文件 `firecracker.yml`；
- RPM 里带的 `firecracker.arm` 二进制没有去掉调试符号，能看到像 `get_dirty_memory`、`PagemapReader`、`is_write_protected` 这样的函数名。

---

## 六、一张图：Firecracker 和它周围的存储

把这篇和前几篇串起来，一个运行中的沙箱，Firecracker 周围是这样的：

```
                         ┌─────────────── orchestrator（template-manager 进程）───────────────┐
                         │                                                                   │
                         │   NBD 服务（接线员）            UFFD 处理程序（仓库管理员）           │
                         │     │  按块回答读写               │  按页填内存                       │
                         │     │                            │                                   │
                         │     ▼                            ▼                                   │
                         │   写时复制 + 模板根盘            模板 memfile（按映射表取）              │
                         └─────┬────────────────────────────┬──────────────────────────────────┘
                     socketpair│                  unix socket│传 UFFD 句柄
                               ▼                            │
                          /dev/nbdN                         │
                               ▲                            │
              符号链接 .link ───┘                            │
                               ▲                            │
  ┌──── 独立 mount 命名空间 ────┼────────────────────────────┼───────────────┐
  │                            │                            ▼               │
  │  /fc-vm/rootfs.ext4 ───────┘     Firecracker 进程：客户机内存（2 MiB 大页）  │
  │  /fc-vm/<内核版本>/vmlinux.bin                    │                       │
  │                                                  │ virtio-blk             │
  │                                         客户机 /dev/vda → /              │
  └─────────────────────────────────────────────────────────────────────────┘
```

后面三篇各负责一块：

- 第 11 篇：图上方“模板根盘”“模板 memfile”的本地缓存从哪来；
- 第 12 篇：左半边，NBD 服务和写时复制；
- 第 13 篇：右半边，UFFD 处理程序和大页。

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| Firecracker | 跑微虚拟机的 VMM，一台虚拟机就是一个宿主进程 |
| virtio-blk | 客户机里的 `/dev/vda`，宿主那头是一个路径 |
| 机器配置 | 内存大小、是否用 2 MiB 大页、是否打开写跟踪 |
| `/fc-kernels`、`/fc-versions` | 按版本号存放内核和 Firecracker 的目录 |
| mount 命名空间 | 让每个 Firecracker 看到同一个 `/fc-vm/rootfs.ext4`，背后却是各自的盘 |
| `.link` 符号链接 | orchestrator 改指向的把手，最终指向 `/dev/nbdN` |
| snapfile | 机器状态，很小；快照不含磁盘 |
| Full / Diff 快照 | 原生快照的两种类型，Diff 要自己合并 |
| Uffd 内存后端 | 加载快照时把缺页处理交给外部程序 |
| 定制版的改动 | 不导出内存、`/memory/dirty`、`/memory/mappings`、`/memory`、原地回滚 |

**下一篇预告**：[《模板长什么样：一个 buildID 目录里的六个文件》](07-template-six-files.md)。基础篇到此结束。第二部分从模板开始：一个模板在存储里到底是哪几个文件？那张“拍平的映射表”header 在代码里长什么样？读完下一篇，你就能拿着一份 header，手工算出沙箱读第 N 块时该去哪个文件的哪个位置。
