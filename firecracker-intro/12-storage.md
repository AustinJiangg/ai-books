# 12. 存储：rootfs、块设备与 I/O

> **《彻底搞懂 Firecracker》系列 · 第十二篇**
>
> **读完本篇，你能理解：**
> - virtio-block 设备的请求类型，以及 Firecracker 如何把它们映射到宿主机文件操作
> - 为什么 Firecracker 只支持“原始格式”的磁盘镜像
> - 如何从零制作一个最小的 rootfs，以及如何把容器镜像转换成 rootfs
> - 只读根盘、可写数据盘、overlay 的组合方式
> - `cache_type` 与 `io_engine` 两个关键选项的含义
> - 令牌桶限速器的工作原理
> - virtio-pmem 等其他存储选项
>
> **前置知识：** 第 05 篇（制作过 ext4 镜像）、第 10 篇（virtqueue）。
>
> **版本：** Firecracker v1.17.0，ARM64。

---

## 引子：给楚门一个“文件柜”

楚门的小镇里有一个巨大的文件柜（磁盘），他在里面存放生活的一切。导演组要决定：

- 文件柜从哪里来？（rootfs 怎么做）
- 柜子是共用的还是每人一个？（只读共享 vs 可写独占）
- 楚门写进柜子的东西，导演组什么时候真正存档？（缓存策略）
- 楚门翻柜子太勤快，会不会影响隔壁？（限速）

---

## 一、virtio-block：最简单的“块设备”

### 1.1 块设备是什么

磁盘在操作系统看来是一个**块设备**：一长串固定大小的块（扇区，通常 512 字节），可以按编号随机读写。文件系统（ext4、xfs……）在块设备之上组织出文件和目录。

virtio-block 设备向 Guest 呈现的正是这样一个块设备，在 Guest 里叫 `/dev/vda`、`/dev/vdb`……它的后端是宿主机上的一个**普通文件**（或一个块设备）。Guest 读第 N 个扇区，Firecracker 就读后端文件的第 `N × 512` 字节处。

### 1.2 请求类型

每个 virtio-block 请求由三部分组成（第 10 篇讲过描述符链）：请求头、数据缓冲区、状态字节。请求头里的类型决定了要做什么：

| 类型 | 含义 | Firecracker 在宿主机上做什么 |
|------|------|----------------------|
| `IN` | 读 | 从后端文件对应位置读数据，写入 Guest 缓冲区 |
| `OUT` | 写 | 从 Guest 缓冲区取数据，写入后端文件 |
| `FLUSH` | 刷盘 | 根据 `cache_type`，可能调用 `fsync` |
| `GET_ID` | 获取设备 ID | 返回一个设备标识字符串 |
| `DISCARD` | 告知某段数据已不再需要（类似 SSD 的 TRIM） | v1.17 起可选支持，在后端文件上“打洞”释放空间 |

### 1.3 为什么只支持原始格式

QEMU 支持 qcow2 等“智能”镜像格式：支持快照链、压缩、加密、按需增长。Firecracker 只支持**原始（raw）格式**：后端文件的第 N 个字节就是磁盘的第 N 个字节，没有任何元数据。

原因还是那三条：

- **安全**：解析复杂的镜像格式需要大量代码，而镜像文件有可能来自不可信的用户，解析器是潜在的攻击面；
- **性能**：没有格式转换，一次读请求就是一次 `pread`；
- **简单**：需要“按需增长”时，宿主机文件系统的稀疏文件就能做到；需要“写时复制”时，可以用宿主机文件系统的 reflink（如 XFS、Btrfs 的 `cp --reflink`）、LVM 精简快照或 device-mapper 等现成的宿主机机制。

---

## 二、制作 rootfs

### 2.1 rootfs 里至少要有什么

一个能启动的根文件系统需要：

1. **一个 init 程序**：内核挂载根文件系统后执行的第一个用户态程序（默认是 `/sbin/init`，可以用内核参数 `init=` 指定其他路径）；
2. **init 需要的库和工具**；
3. **一个 Guest 内核支持的文件系统格式**（ext4 最常用，Firecracker 官方 CI 内核内置了它）。

注意：**rootfs 里不需要内核**，内核是由 Firecracker 直接加载的（第 08 篇）。也**不需要分区表**，整个文件就是一个文件系统即可。

### 2.2 动手：用 Alpine 制作一个最小 rootfs

Alpine Linux 提供一个只有几 MB 的“迷你根文件系统”压缩包，非常适合做实验。

```bash
cd ~/fc-lab
mkdir -p alpine-root

# 找到最新稳定版 aarch64 的 minirootfs 文件名并下载
BASE=https://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/aarch64
FILE=$(curl -fsSL $BASE/latest-releases.yaml | grep -A1 'flavor: alpine-minirootfs' | awk '/file:/{print $2}')
echo "$FILE"
curl -fsSLO $BASE/$FILE
sudo tar -xzf $FILE -C alpine-root
```

（如果自动解析文件名失败，可以在浏览器里打开 `$BASE/` 目录，手动找到 `alpine-minirootfs-*-aarch64.tar.gz`。）

Alpine 迷你版没有完整的 init 系统，我们自己写一个最简单的 init 脚本：

```bash
sudo tee alpine-root/init > /dev/null <<'EOF'
#!/bin/sh
mount -t proc     proc /proc
mount -t sysfs    sys  /sys
mount -t devtmpfs dev  /dev
hostname alpine-fc
echo ""
echo "=== Hello from a minimal Alpine microVM ==="
echo "kernel: $(uname -r), cpus: $(nproc)"
echo "type 'reboot -f' to exit"
exec /bin/sh </dev/ttyS0 >/dev/ttyS0 2>&1
EOF
sudo chmod +x alpine-root/init
```

打包成 ext4 镜像（64 MB 足够）：

```bash
truncate -s 64M alpine.ext4
sudo mkfs.ext4 -d alpine-root -F alpine.ext4
```

启动时的内核参数加上 `init=/init`：

```json
"boot-source": {
  "kernel_image_path": "./vmlinux-6.1.xxx",
  "boot_args": "keep_bootcon console=ttyS0 reboot=k panic=1 init=/init"
},
"drives": [
  { "drive_id": "rootfs", "path_on_host": "./alpine.ext4",
    "is_root_device": true, "is_read_only": false }
]
```

你会得到一个几乎“秒开”的 shell。把它和 Ubuntu rootfs 的启动时间对比一下（第 08 篇的测量方法），差异主要来自 systemd 启动大量服务的时间。

### 2.3 从容器镜像制作 rootfs

现实中最方便的 rootfs 来源是**容器镜像**：你已经有一个能跑的 Docker 镜像，只需要把它的文件系统导出来：

```bash
# 需要宿主机上有 Docker
CID=$(docker create --platform linux/arm64 python:3.12-slim)
docker export $CID -o python-rootfs.tar
docker rm $CID

mkdir -p py-root && sudo tar -xf python-rootfs.tar -C py-root
truncate -s 1G python.ext4
sudo mkfs.ext4 -d py-root -F python.ext4
```

需要注意：

- **容器镜像通常没有 init 程序**（容器运行时直接执行应用进程）。你需要自己加一个 init（像上面的脚本），或者用 `init=` 直接指定应用程序；但应用程序作为 PID 1 时要负责回收僵尸进程、处理信号，通常建议用一个小型 init（如 `tini`）或你自己的 Guest 代理程序；
- **网络配置**：容器镜像依赖容器运行时配置网络，在 microVM 里需要 init 自己配置 IP（或使用内核参数 `ip=` 让内核在启动时配置）；
- **DNS**：同理，要准备 `/etc/resolv.conf`。

Kata Containers、firecracker-containerd 等项目（第 17 篇）把这些工作自动化了：它们在 Guest 中运行一个代理，由代理负责挂载容器镜像的各层、启动容器进程。

---

## 三、多块磁盘与只读共享

### 3.1 多块磁盘

一台 microVM 可以挂载多块磁盘，按添加顺序依次为 `/dev/vda`（根设备总是 `vda`）、`/dev/vdb`……

```bash
truncate -s 1G data.ext4 && mkfs.ext4 -F data.ext4

sudo curl -X PUT --unix-socket /tmp/firecracker.socket \
    -d '{"drive_id": "data", "path_on_host": "./data.ext4",
         "is_root_device": false, "is_read_only": false}' \
    http://localhost/drives/data
```

Guest 里：`mount /dev/vdb /mnt`。

### 3.2 只读根盘 + 可写数据盘

在需要运行大量相同环境的场景中，一个常见的模式是：

```
所有 microVM 共享同一个只读的 rootfs 文件（is_read_only: true）
每台 microVM 有自己的一小块可写盘（或使用 tmpfs）
Guest 里用 overlayfs 把两者叠加成一个“可写的根”
```

好处：

- **节省磁盘**：基础镜像只存一份；
- **节省内存**：宿主机的页缓存（page cache）中，基础镜像的内容也只需要缓存一份，所有 microVM 读同一个文件时共享缓存；
- **安全**：Guest 无论如何都无法修改基础镜像。

只读根盘的配置：

```json
{ "drive_id": "rootfs", "path_on_host": "/images/base.ext4",
  "is_root_device": true, "is_read_only": true }
```

Firecracker 会以只读方式打开文件，并在内核命令行中追加 `ro`；Guest 对它的任何写请求都会返回错误。

在 Guest 里搭建 overlay 通常由 init 脚本完成，思路如下（示意）：

```sh
mount -t tmpfs tmpfs /overlay            # 或 mount /dev/vdb /overlay
mkdir -p /overlay/upper /overlay/work /newroot
mount -t overlay overlay \
      -o lowerdir=/,upperdir=/overlay/upper,workdir=/overlay/work /newroot
# 然后用 pivot_root 或 switch_root 切换到 /newroot 并执行真正的 init
```

### 3.3 运行中更换后端文件

`PATCH /drives/{id}` 可以在 microVM 运行时把磁盘的后端换成另一个文件（比如“插入”一张新的数据盘）：

```bash
sudo curl -X PATCH --unix-socket /tmp/firecracker.socket \
    -d '{"drive_id": "data", "path_on_host": "./data2.ext4"}' \
    http://localhost/drives/data
```

Firecracker 会更新磁盘容量并通知 Guest 配置发生了变化。Guest 里应该先卸载旧文件系统，更换后再挂载。不要在挂载状态下更换，否则 Guest 的文件系统缓存会与新磁盘内容不一致，导致数据损坏。

---

## 四、两个关键选项

### 4.1 cache_type：Guest 说“刷盘”时，要不要真的刷

Guest 的文件系统在需要保证数据持久化时（比如数据库提交事务、`sync` 命令），会向磁盘发送 `FLUSH` 请求。

| 值 | 行为 | 适用场景 |
|----|------|---------|
| `Unsafe`（默认） | 不向 Guest 宣告支持 flush，Guest 的写入只是进入宿主机的页缓存，由宿主机自行决定何时落盘 | 临时环境、Serverless 函数——宿主机断电时丢数据也无所谓 |
| `Writeback` | 向 Guest 宣告支持 flush，收到 `FLUSH` 时对后端文件调用 `fsync` | 需要数据持久性保证的场景 |

`Unsafe` 这个名字很直白：如果宿主机崩溃或断电，Guest 认为“已经保存”的数据可能丢失。对于用完即销毁的 microVM，这完全可以接受，而且性能更好。

### 4.2 io_engine：同步还是异步

| 值 | 实现 | 状态 |
|----|------|------|
| `Sync`（默认） | VMM 线程直接调用 `pread`/`pwrite` 等系统调用，等待完成 | 生产可用 |
| `Async` | 使用 Linux 的 **io_uring** 接口，VMM 线程提交请求后不等待，完成时再处理 | **开发者预览**，需要宿主机内核 5.10.51 以上 |

回忆第 07 篇：所有设备都在一个 VMM 线程里处理。用 `Sync` 引擎时，如果后端磁盘很慢（比如网络存储），一次 `pread` 可能阻塞几毫秒，这期间这台 microVM 的网卡、vsock 等其他设备都得等着。`Async` 引擎通过 io_uring 让 VMM 线程在等待磁盘时可以去处理其他事件，并且能同时提交多个请求，对高延迟、高并发的存储后端提升明显。

> 💡 主线开发版中还加入了“块设备多队列”：可以为一块磁盘配置多个队列，每个队列由一个独立的工作线程处理。这将进一步缓解单 VMM 线程的瓶颈，预计在后续版本中提供。

---

## 五、令牌桶限速器

### 5.1 为什么要限速

一台宿主机上的所有 microVM 共享同一块物理磁盘（或网卡）。一个 Guest 疯狂读写，就会让其他所有 Guest 变慢——这叫“吵闹的邻居”（noisy neighbor）问题。

### 5.2 令牌桶算法

Firecracker 的磁盘、网卡、熵源、pmem 都支持同一套限速器，使用经典的**令牌桶**算法：

```
        每 refill_time 毫秒，补充 size 个令牌（匀速补充）
                    │
                    ▼
            ┌───────────────┐
            │   令牌桶        │  最多装 size 个令牌
            │   ● ● ● ● ●    │
            └───────┬───────┘
                    │ 每个请求取走令牌（按字节数或按 1 次操作）
                    ▼
       令牌够 → 立刻处理；令牌不够 → 等待，直到补充足够的令牌
```

每个限速器可以包含两个桶：

| 桶 | 令牌单位 | 限制什么 |
|----|---------|---------|
| `bandwidth` | 字节 | 吞吐量（MB/s） |
| `ops` | 次 | 操作速率（IOPS 或包/秒） |

每个桶有三个参数：

| 参数 | 含义 |
|------|------|
| `size` | 桶的容量，也是每个周期补充的令牌数 |
| `refill_time` | 把空桶补满需要的时间（毫秒） |
| `one_time_burst` | 一次性的额外令牌，用完不再补充，用于允许启动时的突发 |

**换算示例：** `{"size": 104857600, "refill_time": 1000}` 表示每秒补充 100 MiB 的令牌，即平均限速 100 MiB/s；同时桶满时可以瞬间突发 100 MiB。

```json
"rate_limiter": {
  "bandwidth": { "size": 104857600, "refill_time": 1000, "one_time_burst": 524288000 },
  "ops":       { "size": 2000,      "refill_time": 1000 }
}
```

这个配置意味着：平均 100 MiB/s、2000 IOPS；开机后额外允许 500 MiB 的突发流量（比如加快启动时读取镜像）。

### 5.3 动手：验证磁盘限速

给数据盘配置 10 MiB/s 的限速，然后在 Guest 里测试：

```bash
# Guest 内：直接 I/O 绕过 Guest 页缓存，读 200 MiB
dd if=/dev/vdb of=/dev/null bs=1M count=200 iflag=direct
```

`dd` 报告的速度应该接近 10 MB/s。去掉限速再测一次对比。

宿主机层面还应配合 cgroup 的 io 控制器，从整体上限制每个 Firecracker 进程的磁盘带宽（官方生产指南有相关建议）。

---

## 六、其他存储选项

### 6.1 virtio-pmem（v1.14 起）

**持久内存设备**把宿主机上的一个文件直接 `mmap` 进 Guest 的物理地址空间。Guest 可以用 DAX（直接访问）模式挂载其中的文件系统，读文件时**直接访问映射的内存**，不经过 Guest 自己的页缓存。

这有一个很大的好处：多台 microVM 映射同一个只读文件时，宿主机只需要在内存里保留一份，Guest 内部也不会再重复缓存一份。对于大量 microVM 共享同一基础镜像的场景，可以显著节省内存。

```bash
sudo curl -X PUT --unix-socket /tmp/firecracker.socket \
    -d '{"id": "pmem0", "path_on_host": "./rootfs.ext4", "root_device": true, "read_only": true}' \
    http://localhost/pmem/pmem0
```

（字段以 `docs/pmem.md` 为准。作为根设备时，Firecracker 会生成 `root=/dev/pmem0` 之类的启动参数。）

### 6.2 initrd

`boot-source` 中可以通过 `initrd_path` 指定一个初始内存盘。内核会把它解压到内存中作为最初的根文件系统。它适合放一个小型 init 程序，负责准备好真正的根文件系统（比如组装 overlay、解密磁盘）后再切换过去。

### 6.3 vhost-user-blk（开发者预览）

把块设备的处理交给 Firecracker 之外的另一个进程（如 SPDK 等高性能存储引擎），通过共享内存直接访问 Guest 的 virtqueue。适合需要极致存储性能或特殊存储后端的场景，但会让 Guest 内存变成共享内存，且目前不支持快照。

---

## 七、生产环境建议

| 建议 | 原因 |
|------|------|
| 为每台 microVM 准备独立的可写盘，绝不共享可写镜像 | 两个内核同时写同一个文件系统，必然损坏数据 |
| 基础镜像设为只读共享 | 节省磁盘与内存，防止篡改 |
| 用稀疏文件、reflink 或 LVM 精简卷创建可写盘 | 快速创建，不浪费空间 |
| 用 jailer 时，把镜像文件硬链接或复制进 chroot 目录，并设置正确的属主 | Firecracker 在 chroot 中只能看到里面的文件（第 14 篇） |
| 配置限速器 + cgroup io 控制 | 防止吵闹的邻居 |
| 临时环境用 `Unsafe`，需要持久化的用 `Writeback` | 在性能与可靠性之间取舍 |
| microVM 销毁后安全删除其可写盘 | 防止数据残留 |

---

## 小结

| 主题 | 要点 |
|------|------|
| virtio-block | 后端是宿主机原始格式文件；请求类型：读、写、刷盘、获取 ID、discard |
| rootfs | 需要 init 和文件系统；不需要内核和分区表；可由容器镜像导出 |
| 只读共享 | 基础镜像只读共享 + 每台独立可写层（overlay） |
| `cache_type` | `Unsafe`（默认，不落盘）/ `Writeback`（尊重 flush） |
| `io_engine` | `Sync`（默认）/ `Async`（io_uring，开发者预览） |
| 令牌桶 | `bandwidth` 与 `ops` 两个桶；`size`、`refill_time`、`one_time_burst` |
| pmem | 文件直接映射为 Guest 内存，DAX 访问，适合共享只读镜像 |

---

## 思考题

1. 在 `cache_type: Unsafe` 下，Guest 里执行 `sync` 之后，数据最远到达了哪里（Guest 页缓存、宿主机页缓存，还是物理磁盘）？为什么 Guest 不会因此报错？
2. 两台 microVM 同时以可写方式挂载同一个 ext4 镜像，会发生什么？只读挂载呢？
3. 一个 1 GiB 的 rootfs 用 `truncate` 创建后只写入了 100 MB 数据，它在宿主机上实际占多少磁盘空间？Guest 删除文件后，空间会被释放吗？（提示：discard）
4. 设置 `size: 1000, refill_time: 100` 的 ops 限速器，平均 IOPS 是多少？允许的瞬时突发是多少？
5. 为什么共享只读镜像能节省宿主机内存？使用 virtio-block 和使用 virtio-pmem 时，节省的方式有什么区别？

---

## 下一篇预告

**[13. 安全模型：为什么敢把陌生人的代码放进来](13-security-model.md)**

前面十二篇里，“安全”这个词出现了无数次。下一篇把它们串起来：Firecracker 的威胁模型是什么，纵深防御的每一层分别挡住了什么，seccomp 过滤器是怎样工作的。
