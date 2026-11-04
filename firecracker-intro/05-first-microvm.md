# 05. 动手：在 ARM64 机器上跑起第一台 microVM

> **《彻底搞懂 Firecracker》系列 · 第五篇**
>
> **读完本篇，你能：**
> - 准备好 Firecracker 二进制、Guest 内核和根文件系统
> - 理解启动一台 microVM 至少需要哪几样东西
> - 用 `curl` 通过 API 一步步配置并启动 microVM
> - 给 microVM 接上网络，从宿主机 SSH 进去
> - 用配置文件“一条命令”启动 microVM
> - 排查最常见的几类报错
>
> **前置知识：** 第 01～04 篇。会用 `sudo`、`curl`、`ssh`。
>
> **实验环境：** ARM64 Linux，`/dev/kvm` 可读写（第 02 篇第九节的检查全部通过），能访问互联网，已安装 `curl`、`squashfs-tools`（提供 `unsquashfs`）、`e2fsprogs`（提供 `mkfs.ext4`）、`iproute2`、`iptables`、`jq`、`openssh-client`。
>
> **版本：** Firecracker v1.17.0。

---

## 引子：开机需要什么

一台真实电脑要开机，至少需要：CPU 和内存（硬件）、一个操作系统内核、一块装着系统文件的硬盘。microVM 也一样：

| 真实电脑 | microVM | 由谁提供 |
|---------|---------|---------|
| CPU、内存 | vCPU、Guest 内存 | Firecracker + KVM，通过 `machine-config` 配置 |
| 内核（藏在硬盘的 /boot 里，由 GRUB 加载） | **Guest 内核镜像文件**，直接交给 Firecracker | 你准备，通过 `boot-source` 指定 |
| 系统盘 | **根文件系统镜像**（一个 ext4 格式的文件） | 你准备，通过 `drives` 指定 |
| 网卡（可选） | virtio-net，后端是宿主机 TAP 设备 | 你准备 TAP，通过 `network-interfaces` 指定 |

所以本篇的工作就是：**准备三个文件（Firecracker、内核、rootfs），再告诉 Firecracker 怎么组装它们。**

建议新建一个干净的工作目录，后面所有命令都在里面执行：

```bash
mkdir -p ~/fc-lab && cd ~/fc-lab
```

---

## 一、获取 Firecracker

```bash
ARCH="$(uname -m)"     # 应该是 aarch64
release_url="https://github.com/firecracker-microvm/firecracker/releases"
latest=$(basename $(curl -fsSLI -o /dev/null -w %{url_effective} ${release_url}/latest))
curl -L ${release_url}/download/${latest}/firecracker-${latest}-${ARCH}.tgz | tar -xz

# 为了方便，把主程序和 jailer 复制出来并改个短名字
cp release-${latest}-${ARCH}/firecracker-${latest}-${ARCH} ./firecracker
cp release-${latest}-${ARCH}/jailer-${latest}-${ARCH} ./jailer
./firecracker --version
```

> 💡 如果你想固定在本系列使用的版本，把 `latest` 直接写成 `v1.17.0` 即可。

---

## 二、获取 Guest 内核和根文件系统

### 2.1 为什么用官方 CI 的产物

Guest 内核需要编译进 virtio 驱动、8250 串口、PL031 RTC 等 Firecracker 用到的设备支持，而且最好去掉用不着的东西以加快启动。自己从零配置内核是第 08 篇之后的进阶话题，这里先用 Firecracker 官方 CI（持续集成测试）使用的内核和 Ubuntu 根文件系统，它们存放在一个公开的 S3 存储桶里。

> ⚠️ 官方明确说明：这些资源仅用于演示和测试，不要直接用于生产。

### 2.2 下载

下面的脚本来自官方入门文档，它会自动找到最新一批 CI 产物里最高版本的内核和 Ubuntu 镜像：

```bash
ARCH="$(uname -m)"
S3="https://s3.amazonaws.com/spec.ccfc.min"

# 找到最新一批 CI 产物（目录名以 YYYYMMDD 日期开头）
CI_ARTIFACTS_PREFIX=$(curl -fsSL "$S3?list-type=2&prefix=firecracker-ci/&delimiter=/" \
    | grep -oP "(?<=<Prefix>)firecracker-ci/[0-9]{8}-[^/]+/(?=</Prefix>)" \
    | sort | tail -1)

# 找到并下载最新的内核
latest_kernel_key=$(curl -fsSL "$S3?list-type=2&prefix=${CI_ARTIFACTS_PREFIX}${ARCH}/vmlinux-" \
    | grep -oP "(?<=<Key>)(${CI_ARTIFACTS_PREFIX}${ARCH}/vmlinux-[0-9]+\.[0-9]+\.[0-9]{1,3})(?=</Key>)" \
    | sort -V | tail -1)
wget "$S3/${latest_kernel_key}"

# 找到并下载最新的 Ubuntu 根文件系统（squashfs 格式）
latest_ubuntu_key=$(curl -fsSL "$S3?list-type=2&prefix=${CI_ARTIFACTS_PREFIX}${ARCH}/ubuntu-" \
    | grep -oP "(?<=<Key>)(${CI_ARTIFACTS_PREFIX}${ARCH}/ubuntu-[0-9]+\.[0-9]+\.squashfs)(?=</Key>)" \
    | sort -V | tail -1)
ubuntu_version=$(basename $latest_ubuntu_key .squashfs | grep -oE '[0-9]+\.[0-9]+')
wget -O ubuntu-$ubuntu_version.squashfs.upstream "$S3/$latest_ubuntu_key"

ls -lh vmlinux-* ubuntu-*
```

**关于内核文件名：** 在 ARM64 上，这个文件虽然叫 `vmlinux-x.y.z`，但它其实是 ARM64 Linux 的 **`Image` 格式**（未压缩的、可直接引导的内核映像），而不是 x86 上那种 ELF 格式的 vmlinux。可以验证一下：

```bash
file vmlinux-*
# 典型输出包含：Linux kernel ARM64 boot executable Image
```

Firecracker 在 ARM64 上只接受这种未压缩的 `Image`（第 08 篇解释原因），不接受 `Image.gz` 之类的压缩格式。

### 2.3 把 squashfs 转成 ext4，并放入 SSH 公钥

CI 的根文件系统是只读的 squashfs 格式，也没有我们的 SSH 公钥。我们把它解开，加上公钥，再打包成一个 1 GB 的 ext4 镜像文件：

```bash
# 解压 squashfs 到 squashfs-root/ 目录
unsquashfs ubuntu-$ubuntu_version.squashfs.upstream

# 生成一对 SSH 密钥，把公钥放进 Guest 的 root 用户目录
ssh-keygen -f id_rsa -N ""
cp -v id_rsa.pub squashfs-root/root/.ssh/authorized_keys
mv -v id_rsa ./ubuntu-$ubuntu_version.id_rsa

# 创建一个 1 GB 的空文件，并把目录内容格式化进去成为 ext4 镜像
sudo chown -R root:root squashfs-root
truncate -s 1G ubuntu-$ubuntu_version.ext4
sudo mkfs.ext4 -d squashfs-root -F ubuntu-$ubuntu_version.ext4
```

几个命令的含义：

- `truncate -s 1G` 创建一个“看起来”1 GB 的稀疏文件，实际并不立刻占用 1 GB 磁盘；
- `mkfs.ext4 -d 目录` 在格式化的同时，把指定目录的内容写进新文件系统。

检查一下准备好的三样东西：

```bash
KERNEL=$(ls vmlinux-* | tail -1)
ROOTFS=$(ls *.ext4 | tail -1)
KEY_NAME=$(ls *.id_rsa | tail -1)
echo "Kernel: $KERNEL"; echo "Rootfs: $ROOTFS"; echo "SSH Key: $KEY_NAME"
e2fsck -fn $ROOTFS > /dev/null && echo "rootfs 是有效的 ext4"
```

---

## 三、启动 Firecracker 进程

Firecracker 的使用方式是：**先启动一个“空”的 Firecracker 进程，再通过 API 告诉它要造一台什么样的虚拟机，最后发出“开机”指令。**

API 不走网络端口，而是走一个 **Unix Domain Socket**（宿主机上的一个特殊文件，进程间通过它通信）。

打开**第一个终端**：

```bash
cd ~/fc-lab
API_SOCKET="/tmp/firecracker.socket"
sudo rm -f $API_SOCKET
sudo ./firecracker --api-sock "${API_SOCKET}"
```

进程启动后会停在那里等待指令，没有任何输出。这个终端将成为 microVM 的**串口控制台**——Guest 开机后，内核日志和登录提示都会出现在这里。

> 💡 为了简单，本篇用 `sudo` 运行 Firecracker。生产环境绝对不应该这样做，第 14 篇会用 jailer 以普通用户身份运行它。

---

## 四、通过 API 配置并启动

打开**第二个终端**，进入同一个目录。下面每一步都是一次 HTTP `PUT` 请求，`curl --unix-socket` 让 curl 通过 socket 文件而不是网络发送请求，URL 里的 `localhost` 只是占位。

### 4.1 准备 TAP 网卡（宿主机侧）

```bash
cd ~/fc-lab
TAP_DEV="tap0"
TAP_IP="172.16.0.1"
MASK_SHORT="/30"

sudo ip link del "$TAP_DEV" 2> /dev/null || true
sudo ip tuntap add dev "$TAP_DEV" mode tap
sudo ip addr add "${TAP_IP}${MASK_SHORT}" dev "$TAP_DEV"
sudo ip link set dev "$TAP_DEV" up

# 允许转发，并用 NAT 让 Guest 能通过宿主机上网
sudo sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"
sudo iptables -P FORWARD ACCEPT
HOST_IFACE=$(ip -j route list default | jq -r '.[0].dev')
sudo iptables -t nat -D POSTROUTING -o "$HOST_IFACE" -j MASQUERADE 2>/dev/null || true
sudo iptables -t nat -A POSTROUTING -o "$HOST_IFACE" -j MASQUERADE
```

TAP 设备是宿主机上的一块“虚拟网卡”，Firecracker 会把 Guest 发出的数据包写进它，从它读出的数据包交给 Guest。`/30` 网段只有两个可用地址：宿主机这端 `172.16.0.1`，Guest 那端 `172.16.0.2`。第 11 篇会详细解释这些网络配置。

### 4.2 配置日志

```bash
API_SOCKET="/tmp/firecracker.socket"
LOGFILE="./firecracker.log"

sudo curl -X PUT --unix-socket "${API_SOCKET}" \
    --data "{
        \"log_path\": \"${LOGFILE}\",
        \"level\": \"Debug\",
        \"show_level\": true,
        \"show_log_origin\": true
    }" \
    "http://localhost/logger"
```

成功的请求不返回任何内容（HTTP 204 No Content）。失败时会返回一段 JSON，里面的 `fault_message` 说明原因。

### 4.3 配置机器规格

```bash
sudo curl -X PUT --unix-socket "${API_SOCKET}" \
    --data '{
        "vcpu_count": 2,
        "mem_size_mib": 1024
    }' \
    "http://localhost/machine-config"
```

不配置这一步的话，默认是 1 个 vCPU、128 MiB 内存。

### 4.4 配置内核

```bash
KERNEL="./$(ls vmlinux* | tail -1)"
KERNEL_BOOT_ARGS="keep_bootcon console=ttyS0 reboot=k panic=1"

sudo curl -X PUT --unix-socket "${API_SOCKET}" \
    --data "{
        \"kernel_image_path\": \"${KERNEL}\",
        \"boot_args\": \"${KERNEL_BOOT_ARGS}\"
    }" \
    "http://localhost/boot-source"
```

`boot_args` 是传给 Guest 内核的**命令行参数**：

| 参数 | 作用 |
|------|------|
| `console=ttyS0` | 把控制台输出到第一个串口——也就是第一个终端 |
| `keep_bootcon` | ARM64 上建议加：保留早期启动控制台，避免切换控制台时丢失前面的启动日志 |
| `reboot=k` | 重启方式。配合 Firecracker 的行为，Guest 里执行 `reboot` 会让 Firecracker 退出 |
| `panic=1` | 内核崩溃 1 秒后自动重启（也就是让 Firecracker 退出），而不是卡住 |

### 4.5 配置根文件系统

```bash
ROOTFS="./$(ls *.ext4 | tail -1)"

sudo curl -X PUT --unix-socket "${API_SOCKET}" \
    --data "{
        \"drive_id\": \"rootfs\",
        \"path_on_host\": \"${ROOTFS}\",
        \"is_root_device\": true,
        \"is_read_only\": false
    }" \
    "http://localhost/drives/rootfs"
```

`is_root_device: true` 会让 Firecracker 自动在内核命令行里追加 `root=/dev/vda rw`，告诉 Guest 内核从第一块 virtio 磁盘挂载根文件系统。

### 4.6 配置网卡

```bash
FC_MAC="06:00:AC:10:00:02"

sudo curl -X PUT --unix-socket "${API_SOCKET}" \
    --data "{
        \"iface_id\": \"net1\",
        \"guest_mac\": \"$FC_MAC\",
        \"host_dev_name\": \"$TAP_DEV\"
    }" \
    "http://localhost/network-interfaces/net1"
```

这个 MAC 地址是精心挑选的：CI 根文件系统里有一个开机脚本 `fcnet-setup.sh`，它把 `06:00:` 之后的 4 组十六进制数转成 IP 地址。`AC:10:00:02` 就是 `172.16.0.2`。Guest 开机后会自动给网卡配置这个 IP。

### 4.7 开机！

```bash
sleep 0.015s     # API 请求是异步处理的，稍等一下确保前面的配置都已生效

sudo curl -X PUT --unix-socket "${API_SOCKET}" \
    --data '{ "action_type": "InstanceStart" }' \
    "http://localhost/actions"
```

现在切回**第一个终端**，你会看到 Linux 内核的启动日志飞速滚过，最后出现登录提示：

```
[    0.000000] Booting Linux on physical CPU 0x0000000000 [0x...]
[    0.000000] Linux version 6.1.xxx ...
[    0.000000] Machine model: linux,dummy-virt
...
Ubuntu 24.04 LTS ubuntu-fc-uvm ttyS0

ubuntu-fc-uvm login:
```

注意 `Machine model: linux,dummy-virt` 这一行——这是 Firecracker 写进设备树里的“机器型号”，第 08 篇会看到它从哪里来。

用户名和密码都是 `root`，你可以直接在串口控制台登录。

---

## 五、SSH 登录与联网

回到**第二个终端**：

```bash
KEY_NAME=./$(ls *.id_rsa | tail -1)

# 给 Guest 加默认路由和 DNS，让它能上网
ssh -i $KEY_NAME root@172.16.0.2 "ip route add default via 172.16.0.1 dev eth0"
ssh -i $KEY_NAME root@172.16.0.2 "echo 'nameserver 8.8.8.8' > /etc/resolv.conf"

# 登录
ssh -i $KEY_NAME root@172.16.0.2
```

---

## 六、探索“楚门”眼中的世界

登录 Guest 后，执行下面这些命令，对照第 02 篇的“容器实验”体会区别：

```bash
uname -a            # 内核版本和宿主机不同！这是一个独立的内核
uname -m            # aarch64
nproc               # 2，我们配置的 vCPU 数
free -m             # 约 1 GB
cat /proc/cpuinfo | head -20

# 看看有哪些设备
ls /sys/bus/virtio/devices/       # virtio0、virtio1 ……
cat /sys/bus/virtio/devices/*/device   # 设备类型编号：1=网卡，2=块设备
lsblk                              # vda：我们的 rootfs
ip addr show eth0                  # 172.16.0.2

# 设备树：Firecracker 告诉 Guest 的“硬件清单”
ls /proc/device-tree/
cat /proc/device-tree/compatible; echo
ls /proc/device-tree/ | grep -E 'virtio|uart|rtc|intc'

# 看看中断
cat /proc/interrupts

# 内核启动日志里的设备信息
dmesg | grep -iE 'virtio|ttyS0|pl031|gic' | head -20

# 能上网吗？
ping -c 3 8.8.8.8
```

你会发现这台“电脑”极其简洁：没有 PCI 总线（默认 MMIO 模式下）、没有 USB、没有显卡，只有几个 virtio 设备、一个串口、一个时钟和中断控制器。

同时，在**宿主机**上开第三个终端看看：

```bash
ps -eLf | grep [f]irecracker          # 一个进程，多个线程
top -H -p $(pgrep -f 'firecracker --api-sock')   # 按线程查看 CPU 占用
```

你应该能看到名为 `firecracker`、`fc_api`、`fc_vcpu 0`、`fc_vcpu 1` 的线程——第 07 篇的主角。

### 关机

在 Guest 里执行：

```bash
reboot
```

第一个终端里的 Firecracker 进程会随之退出。正如第 03、04 篇所说，Firecracker 不实现“重启”，Guest 请求重启就意味着这台 microVM 生命结束。

---

## 七、一条命令启动：配置文件模式

每次敲七八个 `curl` 很麻烦。Firecracker 支持把所有启动前配置写进一个 JSON 文件，用 `--config-file` 参数一次性启动。JSON 的键名就是 API 资源的名字。

新建 `vm_config.json`（把内核和 rootfs 文件名换成你实际的文件名）：

```json
{
  "boot-source": {
    "kernel_image_path": "./vmlinux-6.1.xxx",
    "boot_args": "keep_bootcon console=ttyS0 reboot=k panic=1"
  },
  "drives": [
    {
      "drive_id": "rootfs",
      "path_on_host": "./ubuntu-24.04.ext4",
      "is_root_device": true,
      "is_read_only": false
    }
  ],
  "machine-config": {
    "vcpu_count": 2,
    "mem_size_mib": 1024
  },
  "network-interfaces": [
    {
      "iface_id": "net1",
      "guest_mac": "06:00:AC:10:00:02",
      "host_dev_name": "tap0"
    }
  ],
  "logger": {
    "log_path": "./firecracker.log",
    "level": "Info"
  }
}
```

启动（TAP 设备仍需事先创建好）：

```bash
sudo rm -f /tmp/firecracker.socket
sudo ./firecracker --api-sock /tmp/firecracker.socket --config-file vm_config.json
```

配置文件模式会**直接开机**，不需要再发 `InstanceStart`。API socket 依然可用，可以用来做开机后的操作（第 06 篇）。如果连 API 都不需要，可以用 `--no-api` 完全关闭它。

---

## 八、可选：试试 PCI 传输方式

从 v1.13 起，Firecracker 可以选择用 **PCI** 而不是 MMIO 来呈现 virtio 设备，官方入门文档推荐打开，因为吞吐量更高、延迟更低。只需在启动 Firecracker 时加一个参数：

```bash
sudo ./firecracker --api-sock /tmp/firecracker.socket --config-file vm_config.json --enable-pci
```

这要求 Guest 内核编译了 PCI 和 virtio-pci 支持（官方 CI 内核已经包含）。进入 Guest 后执行 `lspci`（如果 rootfs 里有这个工具）或 `ls /sys/bus/pci/devices/`，就能看到 virtio 设备挂在 PCI 总线上了。

本系列讲原理时以默认的 **virtio-mmio** 为主，因为它更简单直观；第 10 篇会专门对比两种方式。

---

## 九、常见问题排查

| 现象 | 可能原因 | 解决办法 |
|------|---------|---------|
| `curl: (7) Couldn't connect to server` | Firecracker 没在运行；socket 路径不一致；`curl` 和 `firecracker` 一个用了 sudo 一个没用 | 确认进程在运行；`ss -a \| grep firecracker.socket`；两边权限保持一致 |
| 启动 Firecracker 报 socket 已存在 | 上次的 socket 文件没删 | `sudo rm -f /tmp/firecracker.socket` |
| `Error creating KVM object` 或打不开 `/dev/kvm` | 无 KVM 或无权限 | 回到第 02 篇第九节检查 |
| `InstanceStart` 返回错误，提到内核文件 | 内核路径错误；ARM64 上用了压缩内核或 x86 内核 | 检查路径；`file` 命令确认是 ARM64 `Image` |
| 串口完全没有输出 | `boot_args` 没有 `console=ttyS0`；或在后台运行导致看不到 | 检查启动参数；看 `firecracker.log` |
| 内核启动后卡在 `VFS: Unable to mount root fs` | rootfs 不是有效的 ext4；没有设置 `is_root_device` | 用 `e2fsck` 检查；确认 drives 配置 |
| SSH 连不上 | TAP 没建好；MAC 地址与 IP 不匹配；Guest 网络脚本没跑 | 宿主机 `ip addr show tap0`；串口登录后 `ip addr` 检查 |
| Guest 不能上网 | 没加默认路由/DNS；宿主机没开转发或 NAT | 重做第五节和 4.1 节 |
| 退出后再次启动报 TAP 设备忙 | 旧进程未完全退出 | `pgrep firecracker` 确认后再启动 |

查看 Firecracker 自己的日志永远是排错第一步：

```bash
cat firecracker.log
```

---

## 十、清理

```bash
sudo pkill firecracker                 # 如果还在运行
sudo ip link del tap0
sudo rm -f /tmp/firecracker.socket
HOST_IFACE=$(ip -j route list default | jq -r '.[0].dev')
sudo iptables -t nat -D POSTROUTING -o "$HOST_IFACE" -j MASQUERADE
```

工作目录里的内核、rootfs、二进制都保留着，后面的篇章会反复使用。

---

## 小结

启动一台 microVM 的完整流程：

```
准备文件              配置资源（PUT）                    开机
───────────         ──────────────────────           ──────────
firecracker 二进制    /logger           日志            /actions
Guest 内核 Image   →  /machine-config   规格        →   InstanceStart
rootfs.ext4          /boot-source      内核 + 参数
TAP 设备             /drives/{id}      磁盘
                     /network-interfaces/{id} 网卡
```

| 要点 | 内容 |
|------|------|
| 三样必需品 | Firecracker、未压缩的 ARM64 内核 `Image`、ext4 rootfs |
| 控制方式 | Unix socket 上的 REST API，或 `--config-file` 一次性配置 |
| ARM64 特别注意 | 内核必须是 `Image` 格式；启动参数建议加 `keep_bootcon` |
| 关机 | Guest 里 `reboot`，Firecracker 进程退出 |
| 生产差异 | 不用 sudo，用 jailer；不用 CI 镜像 |

---

## 思考题

1. 为什么 Firecracker 选择 Unix Domain Socket 而不是 TCP 端口来提供 API？
2. 我们把 rootfs 设置为可写（`is_read_only: false`）。如果同时启动两台 microVM 使用同一个 ext4 文件，会发生什么？
3. 第一个终端为什么会显示 Guest 的登录提示？数据是怎么从 Guest 到达这个终端的？（提示：第 03 篇 6.3 节）
4. 把 `mem_size_mib` 改成 4096 启动，然后在宿主机上用 `ps -o rss -p <firecracker 的 PID>` 查看实际内存占用。结果和 4096 MB 差多少？为什么？
5. 不配置网卡也能启动 microVM 吗？试一试。

---

## 下一篇预告

**[06. Firecracker 的 API：如何“遥控”一台虚拟机](06-api.md)**

我们刚才只用了 API 的一小部分。下一篇系统梳理所有资源、开机前后哪些能改、错误怎么看，并用 Python 写一个小小的控制脚本。
