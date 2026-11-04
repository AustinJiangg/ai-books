# 11. 网络：让 microVM 连上世界

> **《彻底搞懂 Firecracker》系列 · 第十一篇**
>
> **读完本篇，你能理解：**
> - TAP 设备是什么，数据包怎样在 Guest 与宿主机网络栈之间流动
> - 三种常见的宿主机网络方案：路由 + NAT、网桥、每台 microVM 一个网络命名空间
> - 为什么 Firecracker 不做流量过滤，你需要在宿主机上做什么
> - 网络限速器的用法
> - MMDS 元数据服务的原理和 V2 会话令牌机制
> - vsock：不经过网络的 Host ↔ Guest 通信方式
>
> **前置知识：** 第 05 篇（实际配置过 TAP 和 NAT）、第 07 篇（VMM 线程）、第 10 篇（virtio 队列）。对 IP 地址、子网、路由有基本了解。
>
> **版本：** Firecracker v1.17.0。

---

## 引子：给楚门接一根电话线

楚门的小镇是个封闭的摄影棚，但导演组需要和他通话，楚门也需要“打电话给外面”。网络就是这根电话线。问题是：

- 线从哪里接出去？（TAP 设备）
- 外面的交换机怎么连？（宿主机网络方案）
- 谁来监听和限制通话内容？（宿主机防火墙，而不是 Firecracker）
- 导演组想给楚门递张纸条，非得打电话吗？（MMDS 和 vsock）

---

## 一、TAP：宿主机上的“虚拟网线插口”

### 1.1 TUN 与 TAP

Linux 提供两种虚拟网络设备，它们一端连着内核的网络栈，另一端连着一个用户态程序：

| 设备 | 工作层次 | 用户态程序读写的内容 |
|------|---------|-----------------|
| TUN | 第 3 层（IP 层） | IP 数据包 |
| **TAP** | 第 2 层（以太网层） | 完整的以太网帧（带 MAC 地址） |

在宿主机内核看来，TAP 设备就是一块普通网卡：可以给它配 IP、加入网桥、设置防火墙规则。区别在于，从这块“网卡”发出的帧不会到达物理网线，而是被一个用户态程序读走；用户态程序写入的帧，内核会当作“这块网卡收到的帧”来处理。

Firecracker 就是那个用户态程序。它打开 `/dev/net/tun`，绑定到你指定的 TAP 设备（`host_dev_name`），拿到一个文件描述符。

### 1.2 数据包的旅程

**Guest 发出（TX）：**

```
Guest 应用 → Guest 内核网络栈 → virtio-net 驱动 → TX 队列 → 按铃（ioeventfd）
   → Firecracker VMM 线程：从 Guest 内存读出以太网帧 → 检查限速 → 写入 TAP fd
   → 宿主机内核：“tap0 收到一个帧” → 路由/网桥/NAT → 物理网卡 → 互联网
```

**Guest 接收（RX）：**

```
互联网 → 物理网卡 → 宿主机内核路由 → “从 tap0 发出” → TAP fd 变为可读
   → Firecracker VMM 线程（epoll 唤醒）：检查限速 → 读出帧，直接写入 Guest 预先放在 RX 队列里的缓冲区
   → 更新已用环 → irqfd 中断 → Guest 驱动收包 → Guest 网络栈 → Guest 应用
```

为了提高效率，Firecracker 和 TAP 之间使用了 virtio-net 头部（vnet header），并在 Guest 支持时启用校验和卸载、TSO（大包分段卸载）等特性：Guest 可以把一个 64 KB 的大 TCP 包直接交下来，由宿主机内核负责切分，而不是由 Guest 切成几十个小包、经过几十次队列操作。v1.10 还加入了“可合并接收缓冲区”（MRG_RXBUF）特性，进一步提升收包性能。

### 1.3 MAC 地址

`guest_mac` 是 Guest 网卡的 MAC 地址。不指定的话，Guest 驱动会自己随机生成一个。在生产环境中，通常由编排系统分配固定的 MAC，便于和 IP 地址、防火墙规则对应。第 05 篇用的 CI 镜像甚至直接根据 MAC 推算 IP（`06:00:AC:10:00:02` → `172.16.0.2`）。

Firecracker 会统计 Guest 发出的、源 MAC 地址与配置不符的帧（指标 `net.tx_spoofed_mac_count`），但默认不会丢弃它们。防止 MAC 伪造同样是宿主机网络层面的责任。

---

## 二、宿主机网络方案

Firecracker 只负责“把帧搬进搬出 TAP”，TAP 之后怎么连到外部网络，完全由你决定。下面是三种常见方案。

### 2.1 方案一：每台 microVM 一个小子网 + 路由 + NAT

这就是第 05 篇用的方案：

```
                宿主机
   ┌──────────────────────────────────────┐
   │  tap0 172.16.0.1/30  ←→  VM0 172.16.0.2
   │  tap1 172.16.0.5/30  ←→  VM1 172.16.0.6
   │  tap2 172.16.0.9/30  ←→  VM2 172.16.0.10
   │        │ 路由
   │        ▼
   │   iptables/nftables MASQUERADE（NAT）
   │        ▼
   │      eth0（宿主机物理网卡）
   └──────────────────────────────────────┘
```

每台 microVM 独享一个 `/30` 子网（4 个地址：网络地址、宿主机端、Guest 端、广播地址）。

**优点：** 每台 microVM 的流量在宿主机路由层面天然隔离，彼此无法直接通信（除非你允许），防火墙规则写起来清晰。

**缺点：** 每台 microVM 的 IP 都不同，需要分配和管理。

### 2.2 方案二：网桥

把所有 TAP 设备接入同一个 Linux 网桥：

```bash
sudo ip link add br0 type bridge
sudo ip addr add 10.0.0.1/24 dev br0
sudo ip link set br0 up

sudo ip tuntap add dev tap0 mode tap
sudo ip link set tap0 master br0
sudo ip link set tap0 up
# Guest 里配置 10.0.0.2/24，网关 10.0.0.1
```

**优点：** 简单，所有 microVM 在同一个二层网络里，类似一台物理交换机。

**缺点：** microVM 之间默认可以直接通信，甚至可以发起 ARP 欺骗等二层攻击。多租户场景下需要额外的隔离措施。

### 2.3 方案三：每台 microVM 一个网络命名空间

第 02 篇介绍过网络命名空间：每个命名空间有独立的网卡、路由表和防火墙规则。可以为每台 microVM 创建一个命名空间，把 TAP 放在里面，再用一对 veth 虚拟网线把命名空间连到宿主机主网络：

```
  ┌───────── netns vm0 ─────────┐
  │ tap0 172.16.0.1/30 ←→ VM0   │
  │   │ 路由 + NAT                │
  │ veth0-in ───────────────────┼──── veth0-out ──┐
  └─────────────────────────────┘                 │
                                          宿主机主命名空间
  ┌───────── netns vm1 ─────────┐                 │ 路由 / NAT
  │ tap0 172.16.0.1/30 ←→ VM1   │                 ▼
  │ veth1-in ───────────────────┼──── veth1-out  eth0
  └─────────────────────────────┘
```

**最大的好处：每台 microVM 可以使用完全相同的内部 IP 和 TAP 名字**（都是 `tap0`、`172.16.0.2`）。这对快照非常关键：从同一个快照恢复出 100 台 microVM，它们内部的网络配置是一模一样的，只有放进不同的命名空间才能同时运行（第 15 篇）。

jailer 的 `--netns` 参数可以让 Firecracker 进程直接进入指定的网络命名空间（第 14 篇）。很多基于 Firecracker 的沙箱平台都采用这种方案。

**代价：** 每台 microVM 多了一套命名空间、veth 对、路由和 NAT 规则，管理更复杂。尤其要注意 veth 设备名、内部网段在宿主机全局范围内不要和其他系统（Docker、其他编排工具等）的网络冲突——这是同一台机器上运行多套虚拟化/容器平台时最常见的故障来源之一。

### 2.4 动手：为第二台 microVM 准备网络（方案一）

```bash
TAP_DEV="tap1"
sudo ip tuntap add dev $TAP_DEV mode tap
sudo ip addr add 172.16.0.5/30 dev $TAP_DEV
sudo ip link set dev $TAP_DEV up
```

第二台 microVM 的配置使用 `"host_dev_name": "tap1"` 和 `"guest_mac": "06:00:AC:10:00:06"`（CI 镜像会自动配置为 `172.16.0.6`），以及**另一个 API socket 路径**和**另一份 rootfs 文件**（同一个可写 ext4 不能被两台 microVM 同时使用）。

```bash
cp ubuntu-24.04.ext4 ubuntu-vm1.ext4
```

启动后，在宿主机上 `ping 172.16.0.6`，并试试 VM0 能否 ping 通 VM1——取决于宿主机的转发和防火墙设置。

---

## 三、流量过滤：Firecracker 不做，你必须做

官方设计文档明确指出：**Firecracker 不对网络流量做任何过滤，所有从 Guest 发出的流量都应视为不可信，必须在宿主机层面过滤。**

需要考虑的典型规则：

| 风险 | 宿主机规则示例 |
|------|------------|
| Guest 访问宿主机自身的服务（如数据库、管理接口） | 禁止从 TAP 进入宿主机 INPUT 链的流量，只放行必要的 |
| Guest 访问云平台元数据服务（如 `169.254.169.254`，可能泄露宿主机的云凭证） | 在 FORWARD 链丢弃发往该地址的流量 |
| Guest 之间互相访问 | 在 FORWARD 链禁止 TAP 之间的转发 |
| Guest 伪造源 IP | 只允许每个 TAP 发出源 IP 为分配给它的地址的包 |
| Guest 发起大量连接（网络洪泛） | 限速、连接数限制（官方生产指南有专门一节） |

用 nftables 的一个简化示例（假设 tap0 分配的 Guest IP 是 172.16.0.2）：

```bash
sudo nft add table inet fcfilter
sudo nft add chain inet fcfilter forward '{ type filter hook forward priority 0; policy accept; }'
# 禁止 Guest 访问云元数据服务
sudo nft add rule inet fcfilter forward iifname "tap0" ip daddr 169.254.169.254 drop
# 禁止源地址伪造
sudo nft add rule inet fcfilter forward iifname "tap0" ip saddr != 172.16.0.2 drop
# 禁止 Guest 之间直接通信
sudo nft add rule inet fcfilter forward iifname "tap*" oifname "tap*" drop
```

真实的生产规则要根据你的网络设计仔细制定，这里只是展示思路。

---

## 四、网络限速

每个网卡可以分别为**接收**和**发送**方向设置限速器，每个限速器可以同时限制**带宽**（字节/秒）和**包速率**（个/秒）：

```json
{
  "iface_id": "net1",
  "host_dev_name": "tap0",
  "rx_rate_limiter": {
    "bandwidth": { "size": 12500000, "one_time_burst": 0, "refill_time": 100 }
  },
  "tx_rate_limiter": {
    "bandwidth": { "size": 12500000, "refill_time": 100 },
    "ops":       { "size": 1000,     "refill_time": 100 }
  }
}
```

上面的配置意思是：每 100 毫秒补充 12.5 MB 令牌，即约 1 Gbit/s。令牌桶算法的细节放在第 12 篇讲（磁盘限速用的是同一套机制）。运行中可以通过 `PATCH /network-interfaces/net1` 修改。

动手验证：在 Guest 里用 `curl -o /dev/null` 下载一个大文件，或在宿主机运行 `iperf3 -s`、Guest 里运行 `iperf3 -c 172.16.0.1`，分别在有无限速的情况下比较吞吐。

---

## 五、MMDS：microVM 元数据服务

### 5.1 解决什么问题

Guest 启动后，常常需要获取一些由宿主机决定的信息：我的主机名是什么、我要运行哪个任务、访问某个服务的临时凭证是什么……

在云服务器上，这通常由**元数据服务**提供：虚拟机访问一个固定的链路本地地址（如 AWS EC2 的 `169.254.169.254`）即可读取。Firecracker 内置了一个类似的服务，叫 **MMDS（MicroVM Metadata Service）**。

### 5.2 它是怎么工作的

MMDS 的有趣之处在于：**它根本不在宿主机网络上。**

Firecracker 内部有一个极简的网络协议栈（源码中叫 `dumbo`，只实现了 ARP、IPv4、TCP 和 HTTP 的必要部分）。当某个网卡被允许访问 MMDS 时，VMM 线程在把 Guest 发出的每一帧写入 TAP 之前，会先检查：

- 如果是询问 MMDS IP 的 ARP 请求，由 dumbo 直接回复；
- 如果是发往 MMDS IP 的 TCP 包，交给 dumbo 处理，并把 HTTP 响应作为“收到的帧”放回 Guest 的接收队列；
- 其他帧照常写入 TAP。

```
Guest: GET http://169.254.169.254/latest/meta-data
   │ 以太网帧
   ▼
Firecracker VMM 线程 ──是 MMDS 的帧？──是──▶ dumbo 协议栈 ──▶ 从 MMDS 数据存储取值 ──▶ 回复帧注入 Guest
                         │
                         否
                         ▼
                      写入 TAP（宿主机网络）
```

所以 MMDS 流量**永远不会出现在宿主机网络上**，也不会和宿主机所在云平台的真实元数据服务冲突。

### 5.3 配置 MMDS

**开机前：**

```bash
SOCK=/tmp/firecracker.socket

# 允许 net1 网卡访问 MMDS，使用 V2 版本（推荐）
sudo curl -X PUT --unix-socket $SOCK \
    -d '{
        "version": "V2",
        "network_interfaces": ["net1"],
        "ipv4_address": "169.254.169.254"
    }' \
    http://localhost/mmds/config
```

`ipv4_address` 默认就是 `169.254.169.254`，可以改成其他链路本地地址（`169.254.0.0/16` 范围内）。`version` 不填时默认为 V1，但 **V1 已被弃用**，将在下一个大版本中移除，新项目应使用 V2。

**任意时刻写入数据：**

```bash
sudo curl -X PUT --unix-socket $SOCK \
    -d '{
        "latest": {
            "meta-data": {
                "hostname": "demo-vm",
                "task": { "id": 42, "command": "python3 /app/main.py" }
            }
        }
    }' \
    http://localhost/mmds

# 局部更新
sudo curl -X PATCH --unix-socket $SOCK \
    -d '{"latest": {"meta-data": {"hostname": "renamed-vm"}}}' \
    http://localhost/mmds

# 宿主机侧查看
sudo curl -s --unix-socket $SOCK http://localhost/mmds | jq
```

### 5.4 在 Guest 里读取（V2）

```bash
# Guest 内：先确保有到 MMDS 地址的路由
ip route add 169.254.169.254 dev eth0

# 第一步：获取会话令牌（有效期 21600 秒）
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
      -H "X-metadata-token-ttl-seconds: 21600")

# 第二步：带着令牌读取数据
curl -s -H "X-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/
curl -s -H "X-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/hostname
curl -s -H "X-metadata-token: $TOKEN" -H "Accept: application/json" \
     http://169.254.169.254/latest/meta-data/task
```

默认情况下，叶子节点以纯文本返回，目录节点返回子项列表；加上 `Accept: application/json` 可以拿到 JSON 格式。v1.13 起还兼容 EC2 IMDS 风格的请求头（`X-aws-ec2-metadata-token`），方便直接复用为 EC2 编写的工具。

### 5.5 为什么需要令牌

V2 的“先 PUT 拿令牌、再 GET 读数据”看起来多此一举，其实是一项安全设计。它借鉴了 EC2 IMDSv2：许多 SSRF（服务端请求伪造）漏洞只能让应用发出 GET 请求，攻击者借此读取元数据服务中的敏感凭证。要求先发 PUT 请求获取令牌，可以挡住大部分此类攻击。MMDS 还会拒绝带有 `X-Forwarded-For` 头的 PUT 请求，防止经过代理转发的请求获取令牌。

---

## 六、vsock：不走网络的“对讲机”

### 6.1 为什么需要 vsock

有时宿主机上的程序和 Guest 里的程序需要通信，但：

- 你不想给 Guest 配网卡（更小的攻击面、更快的启动）；
- 或者不想让这种控制通信经过可能被 Guest 篡改的网络配置。

**vsock（virtio socket）** 提供了一种类似 TCP 的、面向连接的 socket 通信，但不需要 IP 地址，只需要 **CID（上下文 ID）+ 端口号**：

- 宿主机的 CID 固定为 **2**；
- 每个 Guest 有一个唯一的 CID（必须 ≥ 3），在配置 vsock 设备时指定。

在 Guest 内，程序使用标准的 `AF_VSOCK` 地址族编程，和写 TCP 程序几乎一样。

### 6.2 Firecracker 的特殊之处：映射到 Unix socket

在 Firecracker 中，**宿主机这一端不是 `AF_VSOCK`，而是一个 Unix Domain Socket**。这让宿主机程序不需要依赖内核的 vhost-vsock 模块，也让 jailer 的 chroot 隔离更容易实施。

配置（开机前）：

```bash
sudo curl -X PUT --unix-socket /tmp/firecracker.socket \
    -d '{"guest_cid": 3, "uds_path": "./v.sock"}' \
    http://localhost/vsock
```

两个方向的连接方式不同：

**Guest 主动连接宿主机（Guest → Host）：**

1. 宿主机程序监听 Unix socket `./v.sock_52`（即 `uds_path` + `_` + 端口号）；
2. Guest 程序连接 `CID 2，端口 52`；
3. Firecracker 把这个连接转接到 `./v.sock_52`。

**宿主机主动连接 Guest（Host → Guest）：**

1. Guest 程序监听 vsock 端口 52；
2. 宿主机程序连接 Unix socket `./v.sock`，并发送一行文本 `CONNECT 52\n`；
3. Firecracker 回复一行 `OK <宿主机侧分配的端口>\n`，之后这个连接就和 Guest 的 52 端口打通了。

### 6.3 动手：用 socat 体验

需要宿主机和 Guest 里都有 `socat`（1.7.4 以上版本支持 vsock）。

**宿主机连 Guest：**

```bash
# Guest 内：监听 vsock 端口 52
socat VSOCK-LISTEN:52,fork -

# 宿主机（在 Firecracker 的工作目录下）：
sudo socat - UNIX-CONNECT:./v.sock
CONNECT 52              ← 手动输入
OK 1073741824           ← Firecracker 回复
hello guest             ← 之后输入的内容会出现在 Guest 的终端里
```

**Guest 连宿主机：**

```bash
# 宿主机：
sudo socat - UNIX-LISTEN:./v.sock_52

# Guest 内：
socat - VSOCK-CONNECT:2:52
hello host
```

### 6.4 vsock 的典型用途

- **Guest 代理（agent）通信**：许多基于 Firecracker 的平台在 Guest 里运行一个小代理程序，宿主机通过 vsock 下发命令（执行代码、读写文件）、收集输出。Kata Containers、各类代码沙箱都采用了类似的设计；
- **日志和指标回传**：Guest 内的日志通过 vsock 直接发给宿主机，不占用业务网络；
- **快照场景**：创建快照时 Firecracker 会给 Guest 发送一个“传输重置”事件，断开所有 vsock 连接；恢复后，双方需要重新建立连接（第 15 篇）。v1.16 起还支持在恢复时改写 `uds_path`。

---

## 小结

| 机制 | 作用 | 关键点 |
|------|------|-------|
| TAP | Guest 网卡在宿主机上的对端 | 第 2 层设备，Firecracker 读写以太网帧 |
| 路由 + NAT | 每台 microVM 独立子网 | 隔离清晰，IP 需管理 |
| 网桥 | microVM 在同一二层网络 | 简单，但需防二层攻击 |
| 网络命名空间 | 每台 microVM 独立网络环境 | 可复用相同内部 IP，适合快照克隆 |
| 流量过滤 | 防止 Guest 滥用网络 | **Firecracker 不做，宿主机必须做** |
| 限速器 | 公平分配网络带宽 | 带宽 + 包速率，收发分开 |
| MMDS | 给 Guest 提供元数据 | 内置 dumbo 协议栈，流量不出进程；推荐 V2 |
| vsock | Host ↔ Guest 直接通信 | 宿主机侧是 Unix socket；`CONNECT <port>` 协议 |

---

## 思考题

1. 为什么 MMDS 的流量“不会出现在宿主机网络上”是一项重要的安全特性？
2. 如果宿主机上没有为 TAP 配置任何防火墙规则，一个恶意 Guest 可以做哪些事？
3. 用网络命名空间方案时，100 台从同一快照恢复的 microVM 内部都是 `172.16.0.2`。外部要访问其中某一台的服务，该怎么做？
4. vsock 的 Guest 侧使用标准的 `AF_VSOCK`，宿主机侧却是 Unix socket。这种设计对用 jailer 运行的 Firecracker 有什么好处？
5. 一台只需要接收任务、执行计算、返回结果的 microVM，能完全不配网卡吗？它该如何接收任务和返回结果？

---

## 下一篇预告

**[12. 存储：rootfs、块设备与 I/O](12-storage.md)**

下一篇讲 microVM 的“硬盘”：怎样从容器镜像制作 rootfs、只读根盘加可写数据盘的组合、同步与 io_uring 两种 I/O 引擎、缓存策略，以及令牌桶限速器的工作原理。
