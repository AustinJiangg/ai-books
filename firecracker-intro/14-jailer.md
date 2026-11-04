# 14. Jailer：给 Firecracker 再套一层笼子

> **《彻底搞懂 Firecracker》系列 · 第十四篇**
>
> **读完本篇，你能：**
> - 理解 jailer 的定位：一个“以 root 启动、布置好牢房、然后自废武功”的启动器
> - 说出 jailer 执行的每一个步骤及其安全意义
> - 动手用 jailer 启动一台 microVM：准备用户、cgroup、网络命名空间、chroot 中的文件
> - 验证 Firecracker 进程确实被关进了牢笼
> - 掌握生产环境中 jailer 的常用参数和注意事项
>
> **前置知识：** 第 02 篇（namespace、cgroups）、第 05 篇（手动启动）、第 13 篇（安全模型）。
>
> **版本：** Firecracker / jailer v1.17.0，ARM64，cgroup v2。

---

## 引子：先布置牢房，再把自己锁进去

到目前为止，我们都是用 `sudo` 运行 Firecracker 的——它以 root 身份运行，能看到宿主机上的所有文件。如果 Guest 利用某个漏洞控制了 Firecracker 进程，它就拥有了 root 权限（尽管 seccomp 还挡着）。

更好的做法是让 Firecracker 以**普通用户**身份、在**一个几乎空无一物的目录**里运行。但有个矛盾：布置这样的环境（创建 cgroup、chroot、进入命名空间、创建设备文件）恰恰需要 root 权限。

**jailer** 解决了这个矛盾。它是一个以 root 身份启动的小程序，按顺序做完所有需要特权的准备工作，然后**放弃所有特权**，再用 `exec` 把自己替换成 Firecracker。从这一刻起，Firecracker 进程从未拥有过 root 权限。

就像一个狱警亲手把牢房布置好，然后走进去、锁上门、把钥匙扔掉，最后变成了犯人本身。

---

## 一、jailer 做了什么

按官方文档描述的顺序，jailer 依次执行：

| 步骤 | 操作 | 安全意义 |
|-----|------|---------|
| 1 | 校验所有参数和路径、VM ID 的格式 | 防止路径注入 |
| 2 | 关闭除标准输入输出外的所有已打开文件 | 防止从父进程继承意外的文件句柄 |
| 3 | 清空所有环境变量 | 防止环境变量影响 Firecracker 的行为 |
| 4 | 创建 chroot 目录 `<chroot_base>/<exec_file_name>/<id>/root` | 每台 microVM 一个独立的“牢房” |
| 5 | 把 Firecracker 二进制**复制**进 chroot 目录 | 每个进程使用独立的二进制副本，不与其他 Firecracker 进程共享内存页 |
| 6 | 设置资源限制（`setrlimit`），默认最多 2048 个文件描述符 | 防止耗尽文件句柄 |
| 7 | 创建 cgroup 并把自己加入，写入配置的 cgroup 参数 | 限制 CPU、内存等资源 |
| 8 | 进入新的挂载命名空间，用 `pivot_root` 切换根目录到 chroot 目录，卸载旧根，再 `chroot` | Firecracker 只能看到牢房里的文件 |
| 9 | 在牢房里用 `mknod` 创建 `/dev/net/tun` 和 `/dev/kvm` | 只提供 Firecracker 必需的两个设备 |
| 10 | 把牢房根目录和这两个设备的属主改为指定的 uid/gid | 降权后依然能使用它们 |
| 11 | （可选）加入指定的网络命名空间 | 网络隔离 |
| 12 | （可选）`--daemonize`：脱离终端，标准输入输出重定向到 `/dev/null` | 后台运行 |
| 13 | （可选）`--new-pid-ns`：在新的 PID 命名空间中创建子进程 | 进程视图隔离，Firecracker 成为该命名空间的 1 号进程 |
| 14 | 切换到指定的 uid/gid | **降权，放弃 root** |
| 15 | `exec` 成 Firecracker，附带 `--id` 等参数，以及 `--` 之后的额外参数 | jailer 消失，Firecracker 登场 |

注意第 8 步用的是 `pivot_root` 而不是简单的 `chroot`：单纯的 `chroot` 存在一些已知的“越狱”手法，而 `pivot_root` 配合新的挂载命名空间并卸载旧根，可以彻底切断与宿主机文件系统的联系。

---

## 二、jailer 的参数

```
jailer --id <id>
       --exec-file <firecracker 二进制路径>
       --uid <uid> --gid <gid>
       [--chroot-base-dir <目录>]          默认 /srv/jailer
       [--cgroup-version <1|2>]            默认 1；现代发行版多为 2
       [--cgroup <文件>=<值>] ...           可多次指定
       [--parent-cgroup <相对路径>]         默认为 exec-file 的文件名
       [--netns <网络命名空间路径>]
       [--resource-limit <资源>=<值>] ...   fsize、no-file
       [--daemonize]
       [--new-pid-ns]
       [-- <传给 Firecracker 的额外参数>]
```

| 参数 | 说明 |
|------|------|
| `--id` | microVM 的唯一标识，只能包含字母、数字和连字符，最长 64 个字符。它决定了 chroot 目录和 cgroup 的名字，也会传给 Firecracker 作为实例 ID |
| `--exec-file` | Firecracker 二进制的路径。必须是与 jailer **同一版本**的、静态链接（musl）的 Firecracker |
| `--uid`、`--gid` | 降权后使用的用户和组。**建议每台 microVM 使用不同的 uid/gid**，这样即使逃逸，不同 microVM 之间也无法互相访问文件 |
| `--cgroup` | 例如 `memory.max=1073741824`、`cpu.max=50000 100000`、`cpuset.cpus=2-3` |
| `--netns` | 例如 `/var/run/netns/vm1`，由 `ip netns add vm1` 创建 |
| `--resource-limit` | `no-file=1024`（最大文件描述符数）、`fsize=…`（能创建的最大文件大小） |
| `--` 之后 | 原样传给 Firecracker，例如 `--api-sock /api.socket`、`--config-file /vm.json` |

---

## 三、动手：用 jailer 启动 microVM

下面的实验假设你在 `~/fc-lab` 目录，里面有第 05 篇准备好的 `firecracker`、`jailer`、内核和 rootfs。所有命令都需要 root 权限。

### 3.1 准备变量和用户

```bash
cd ~/fc-lab
VM_ID="vm1"
FC_UID=10001
FC_GID=10001
CHROOT_BASE=/srv/jailer
JAIL_ROOT=$CHROOT_BASE/firecracker/$VM_ID/root    # jailer 会创建它

KERNEL=$(ls vmlinux-* | tail -1)
ROOTFS=$(ls ubuntu-*.ext4 | tail -1)

# 创建一个专用的组和用户（不能登录、没有家目录）
sudo groupadd -g $FC_GID fc-$VM_ID 2>/dev/null || true
sudo useradd -u $FC_UID -g $FC_GID -M -s /usr/sbin/nologin fc-$VM_ID 2>/dev/null || true
```

### 3.2 准备 cgroup v2

确认宿主机使用的是 cgroup v2：

```bash
stat -fc %T /sys/fs/cgroup     # 输出 cgroup2fs 表示 v2
```

jailer 会在 `/sys/fs/cgroup/<parent_cgroup>/<id>` 创建 cgroup（`parent_cgroup` 默认是可执行文件名 `firecracker`）。在 cgroup v2 中，要在子 cgroup 里使用某个控制器（如 `memory`、`cpu`），必须在它所有祖先 cgroup 的 `cgroup.subtree_control` 中启用该控制器。jailer 会沿路径自动完成这一步，你只需要确认这些控制器在根 cgroup 中可用：

```bash
cat /sys/fs/cgroup/cgroup.controllers      # 应包含 cpu、cpuset、memory 等
```

如果某个控制器不在列表里，通常是被系统的其他配置占用或内核未启用，需要先解决这个问题。

### 3.3 准备网络命名空间和 TAP

```bash
sudo ip netns add $VM_ID
# 在命名空间里创建 TAP，并把属主设为 microVM 的用户——
# 降权后的 Firecracker 没有 CAP_NET_ADMIN，只能打开属于自己的 TAP
sudo ip netns exec $VM_ID ip tuntap add dev tap0 mode tap user $FC_UID group $FC_GID
sudo ip netns exec $VM_ID ip addr add 172.16.0.1/30 dev tap0
sudo ip netns exec $VM_ID ip link set tap0 up
```

（为了聚焦 jailer，这里不配置命名空间到外网的连接，Guest 只能和命名空间内的 `172.16.0.1` 通信。打通外网需要 veth 对和 NAT，见第 11 篇方案三。）

### 3.4 准备 chroot 里的文件

jailer 会在启动时创建 `$JAIL_ROOT`，但我们需要**事先**把内核和 rootfs 放进去。目录提前建好不影响 jailer（已存在的目录会被直接使用）：

```bash
sudo mkdir -p $JAIL_ROOT
# 内核可以用硬链接（同一文件系统内，不占额外空间），rootfs 每台 microVM 一份副本
sudo ln -f $KERNEL $JAIL_ROOT/vmlinux 2>/dev/null || sudo cp $KERNEL $JAIL_ROOT/vmlinux
sudo cp $ROOTFS $JAIL_ROOT/rootfs.ext4
sudo chown $FC_UID:$FC_GID $JAIL_ROOT/vmlinux $JAIL_ROOT/rootfs.ext4
```

注意：可写的 rootfs 必须让降权后的用户**可读可写**，内核至少要可读。

### 3.5 准备配置文件

在 jailer 中，**所有路径都是相对于牢房根目录的**。Firecracker 看到的 `/vmlinux`，在宿主机上其实是 `$JAIL_ROOT/vmlinux`：

```bash
sudo tee $JAIL_ROOT/vm.json > /dev/null <<EOF
{
  "boot-source": {
    "kernel_image_path": "/vmlinux",
    "boot_args": "keep_bootcon console=ttyS0 reboot=k panic=1"
  },
  "drives": [
    { "drive_id": "rootfs", "path_on_host": "/rootfs.ext4",
      "is_root_device": true, "is_read_only": false }
  ],
  "machine-config": { "vcpu_count": 2, "mem_size_mib": 512 },
  "network-interfaces": [
    { "iface_id": "net1", "guest_mac": "06:00:AC:10:00:02", "host_dev_name": "tap0" }
  ]
}
EOF
sudo chown $FC_UID:$FC_GID $JAIL_ROOT/vm.json
```

### 3.6 启动

```bash
sudo ./jailer \
    --id $VM_ID \
    --exec-file $(pwd)/firecracker \
    --uid $FC_UID --gid $FC_GID \
    --chroot-base-dir $CHROOT_BASE \
    --cgroup-version 2 \
    --cgroup memory.max=$((768 * 1024 * 1024)) \
    --cgroup cpu.max="100000 100000" \
    --netns /var/run/netns/$VM_ID \
    --new-pid-ns \
    --resource-limit no-file=1024 \
    -- \
    --api-sock /api.socket \
    --config-file /vm.json
```

几点说明：

- `memory.max` 设为 768 MiB，比 Guest 的 512 MiB 多一些，留给 Firecracker 自身和设备缓冲区；
- `cpu.max="100000 100000"` 表示每 100 毫秒最多使用 100 毫秒 CPU 时间，即最多 1 个核的算力（尽管 Guest 有 2 个 vCPU）；
- 没有加 `--daemonize`，所以串口输出会直接显示在当前终端，便于观察。生产环境通常会加上它；
- API socket 在宿主机上的路径是 `$JAIL_ROOT/api.socket`。

你会看到 Guest 照常启动。

---

## 四、验证牢笼

另开一个终端：

```bash
VM_ID=vm1
JAIL_ROOT=/srv/jailer/firecracker/$VM_ID/root

# 1. 找到 Firecracker 的 PID（jailer 会把它写进牢房里的 pid 文件）
FC_PID=$(sudo cat $JAIL_ROOT/firecracker.pid)
echo "Firecracker PID: $FC_PID"

# 2. 以什么用户运行？有没有特权？
ps -o user,pid,comm -p $FC_PID
sudo grep -E '^(Uid|Gid|CapEff|CapBnd|Seccomp|NoNewPrivs)' /proc/$FC_PID/status
```

你应该看到：用户是 `fc-vm1`（10001）；`CapEff`（有效能力集）为全 0，说明没有任何特权；`Seccomp: 2`。

```bash
# 3. 它眼中的根目录是什么？
sudo ls -la /proc/$FC_PID/root/
```

只有寥寥几个文件：`firecracker`（二进制副本）、`vmlinux`、`rootfs.ext4`、`vm.json`、`api.socket`、`dev/`（里面只有 `kvm` 和 `net/tun`）、`firecracker.pid`。宿主机的 `/etc`、`/home`、`/usr` 全都不存在。

```bash
# 4. 所在的命名空间和 cgroup
sudo ls -l /proc/$FC_PID/ns/ | grep -E 'mnt|net|pid'
ls -l /proc/self/ns/ | grep -E 'mnt|net|pid'     # 对比宿主机 shell 的命名空间编号
cat /proc/$FC_PID/cgroup
cat /sys/fs/cgroup/firecracker/$VM_ID/memory.max
cat /sys/fs/cgroup/firecracker/$VM_ID/cpu.max

# 5. 通过 API 操作（注意 socket 路径）
sudo curl -s --unix-socket $JAIL_ROOT/api.socket http://localhost/ | jq
```

**体验 cgroup 的效果：** 在 Guest 里同时跑两个满负荷进程（`yes > /dev/null &` 两次），在宿主机上用 `top -p $FC_PID` 观察——整个 Firecracker 进程的 CPU 占用会被限制在 100% 左右（一个核），而不是 200%。

---

## 五、清理

jailer 不负责清理，这是使用者（编排系统）的责任：

```bash
VM_ID=vm1
sudo kill $(sudo cat /srv/jailer/firecracker/$VM_ID/root/firecracker.pid) 2>/dev/null
sleep 1
sudo rm -rf /srv/jailer/firecracker/$VM_ID
sudo rmdir /sys/fs/cgroup/firecracker/$VM_ID 2>/dev/null
sudo ip netns del $VM_ID
```

在生产环境中，编排系统需要可靠地处理这些清理工作：microVM 异常退出时也要回收 chroot 目录、cgroup、网络命名空间、TAP 设备，以及删除可写盘以防数据残留。

---

## 六、生产环境中的 jailer

### 6.1 推荐做法

| 做法 | 原因 |
|------|------|
| **每台 microVM 独立的 uid/gid** | 即使两台 microVM 都被攻破，它们也无法访问彼此的文件 |
| 使用 `--new-pid-ns` | Firecracker 看不到宿主机上的其他进程 |
| 使用 `--netns` | 网络隔离，并能复用相同的内部 IP（快照克隆需要） |
| 用 `--cgroup` 同时限制内存、CPU，必要时用 `cpuset` 绑核 | 资源隔离，避免吵闹的邻居 |
| 用 `--resource-limit` 限制文件描述符和文件大小 | 防止资源耗尽 |
| 共享的只读镜像用硬链接放进 chroot | 节省空间，宿主机页缓存共享 |
| 用 `--daemonize`，日志和指标写到 chroot 内的文件或命名管道 | 后台运行；外部程序读取 |
| 控制系统中的挂载点数量 | 官方文档指出，挂载点越多、并发创建越多，jailer 越慢（`pivot_root` 需要处理挂载传播） |

### 6.2 文件放进牢房的方式

| 方式 | 适用 |
|------|------|
| 硬链接（`ln`） | 只读、共享的文件（内核、基础镜像），要求在同一个文件系统上 |
| 复制（`cp`）或 reflink（`cp --reflink`） | 每台 microVM 独立的可写盘 |
| 绑定挂载（`mount --bind`） | 需要访问其他文件系统上的文件时（注意挂载点数量的影响） |

### 6.3 一个常见的坑

`/dev/net/tun` 和 `/dev/kvm` 是由 jailer 在牢房里用 `mknod` 创建的。这要求 chroot 所在的文件系统**允许设备文件**——如果 `/srv/jailer` 所在分区以 `nodev` 选项挂载，Firecracker 将无法打开它们。

---

## 小结

```
          root 身份
jailer ─────────────────────────────────────────────────────▶ exec
 │ 校验参数 → 关闭 fd → 清环境变量
 │ 建 chroot 目录 → 复制 firecracker 二进制
 │ setrlimit → 建 cgroup 并加入
 │ unshare(mount ns) → pivot_root → chroot
 │ mknod /dev/kvm、/dev/net/tun → chown
 │ setns(net ns) → [daemonize] → [clone(new pid ns)]
 │ setgid/setuid（降权）
 ▼
firecracker（普通用户、无特权、chroot、cgroup 限制、seccomp 过滤）
```

| 要点 | 内容 |
|------|------|
| 定位 | 以 root 准备环境，然后降权 exec 成 Firecracker |
| 牢房路径 | `<chroot_base>/<exec_file_name>/<id>/root` |
| 路径规则 | API 和配置中的路径都相对于牢房根目录 |
| 必需设备 | 只有 `/dev/kvm` 和 `/dev/net/tun` |
| PID | 写在牢房里的 `firecracker.pid` |
| 清理 | jailer 不管，由编排系统负责 |

---

## 思考题

1. 为什么 jailer 要把 Firecracker 二进制**复制**进每个牢房，而不是硬链接或共享同一个文件？
2. 降权后的 Firecracker 没有 `CAP_NET_ADMIN`，为什么它还能使用 TAP 设备？如果 TAP 设备的属主不是它的 uid 会怎样？
3. 在 jailer 下，一个被攻破的 Firecracker 进程调用 `openat("/etc/shadow", ...)` 会怎样？seccomp 允许 `openat`，为什么这依然是安全的？
4. 不使用 `--new-pid-ns` 时，被攻破的 Firecracker 能看到宿主机上的其他进程吗？能对它们做什么？
5. 如果 `memory.max` 设得刚好等于 Guest 内存大小，会发生什么？

---

## 下一篇预告

**[15. 快照与恢复：毫秒级“复活”一台虚拟机](15-snapshots.md)**

下一篇讲 Firecracker 最强大的特性之一：把一台运行中的 microVM 完整“冻结”到文件，再在毫秒级时间内恢复——甚至从一个快照恢复出成百上千台。我们还会讨论这背后隐藏的随机数、唯一性和时钟问题。
