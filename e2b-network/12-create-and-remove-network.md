# 第 12 篇｜建网与拆网：CreateNetwork 一步一步

> **本篇目标**：跟着 orchestrator 的代码，把一个网络槽位从无到有地“建”一遍，再“拆”一遍。每一步都配上等价的 `ip`/`iptables` 命令，并回答“少了这一步会怎样”。读完本篇，你会对一个槽位里每一块网卡、每一条路由、每一条规则的来历了如指掌，也会明白为什么“拆不干净”是一个真实存在的运维问题。

---

## 一、开始之前：Go 程序切换命名空间要“锁线程”

orchestrator 是 Go 写的，建网的函数叫 `CreateNetwork`。它的第一行就很特别：

```go
runtime.LockOSThread()
defer runtime.UnlockOSThread()
```

为什么要锁线程？因为在 Linux 里，**“当前在哪个网络命名空间”是线程级别的属性**。一个线程用 `setns` 进入了 `ns-5`，它之后创建的网卡、加的路由、写的规则，都落在 `ns-5` 里。

而 Go 程序的协程（goroutine）会被调度器在不同的操作系统线程之间搬来搬去。如果不锁住：

1. 协程在线程 A 上进入了 `ns-5`。
2. 调度器把它挪到线程 B 上。线程 B 还在宿主机命名空间里。
3. 协程接下来加的规则，就落到了宿主机上。

这种 bug 极难排查。所以 E2B 先把协程钉在当前线程上，再记下宿主机命名空间的句柄，函数结束时无论成败都切回宿主机：

```go
hostNS, _ := netns.Get()       // 记住“家”在哪
defer netns.Set(hostNS)        // 无论怎样，最后都回家
```

---

## 二、建网的十一步

下面以槽位 5 为例，地址取这套环境的配置（Host 池 `10.13.0.0/16`、VRT 池 `10.14.0.0/16`）。宿主机的物理网卡假设叫 `enp125s0f0`。

![建网十一步](img/12-1-建网十一步.svg)

### 第 1 步：创建命名空间

```go
ns, _ := netns.NewNamed("ns-5")
```

等价命令：

```bash
ip netns add ns-5
```

`netns.NewNamed` 会创建一个新的网络命名空间，把它挂到 `/var/run/netns/ns-5`，**并且让当前线程进入它**。所以从这一步开始，线程已经身在 `ns-5` 了。

### 第 2 步：建 veth 对，配好命名空间这一头

```go
veth := &netlink.Veth{Name: "e2bv-5", PeerName: "eth0"}
netlink.LinkAdd(veth)                         // 在 ns-5 里建一对 veth
vpeer := netlink.LinkByName("eth0")
netlink.LinkSetUp(vpeer)
netlink.AddrAdd(vpeer, "10.14.0.11/31")      // 配 vpeer 地址
netlink.LinkSetNsFd(veth, hostNS)            // 把 e2bv-5 这头扔回宿主机
```

等价命令（在 `ns-5` 里执行）：

```bash
ip link add e2bv-5 type veth peer name eth0
ip link set eth0 up
ip addr add 10.14.0.11/31 dev eth0
ip link set e2bv-5 netns 1          # 送回宿主机命名空间
```

注意顺序：因为线程已经在 `ns-5` 里，veth 对的**两头一开始都在 `ns-5`**。代码先把 `eth0` 这头配好，再把 `e2bv-5` 那头“扔”回宿主机。

### 第 3 步：回到宿主机，配好宿主机那一头

```go
netns.Set(hostNS)                            // 切回宿主机
vethInHost := netlink.LinkByName("e2bv-5")
netlink.LinkSetUp(vethInHost)
netlink.AddrAdd(vethInHost, "10.14.0.10/31")
```

等价命令：

```bash
ip link set e2bv-5 up
ip addr add 10.14.0.10/31 dev e2bv-5
```

至此，宿主机和 `ns-5` 之间已经有一根通了的虚拟网线，两头各有一个 `/31` 地址。

### 第 4 步：再进命名空间，建 tap0、启用 lo

```go
netns.Set(ns)                                // 再进 ns-5
tap := &netlink.Tuntap{Name: "tap0", Mode: TAP}
netlink.LinkAdd(tap)
netlink.LinkSetUp(tap)
netlink.AddrAdd(tap, "169.254.0.22/30")
netlink.LinkSetUp(lo)                        // 启用命名空间的环回网卡
```

等价命令（在 `ns-5` 里执行）：

```bash
ip tuntap add tap0 mode tap
ip link set tap0 up
ip addr add 169.254.0.22/30 dev tap0
ip link set lo up
```

**少了会怎样**：

- 没有 `tap0`，Firecracker 启动时找不到要打开的设备，直接失败。
- 没有 `169.254.0.22` 这个地址，客户机发给网关的包就没人接。客户机问“谁是 `169.254.0.22`”，没有人回答。

新建的命名空间里，连 `lo` 都是关着的，要手动打开。

### 第 5 步：命名空间里加默认路由

```go
netlink.RouteAdd(&netlink.Route{Gw: "10.14.0.10"})   // 没写目的地 = 默认路由
```

等价命令：

```bash
ip route add default via 10.14.0.10
```

**少了会怎样**：客户机发往外网的包到了命名空间，命名空间不知道往哪送，直接丢弃。

### 第 6 步：命名空间里加两条 NAT 规则

这是第 10 篇“出口换门牌”的落地：

```bash
# 出去：源地址 169.254.0.21 换成 Host IP
iptables -t nat -A POSTROUTING -o eth0 -s 169.254.0.21 -j SNAT --to 10.13.0.5

# 进来：目的地址 Host IP 换成 169.254.0.21
iptables -t nat -A PREROUTING  -i eth0 -d 10.13.0.5    -j DNAT --to 169.254.0.21
```

**少了会怎样**：

- 没有 SNAT：包带着 `169.254.0.21` 的源地址离开命名空间。宿主机上几百个沙箱发出的包，源地址全都一样，回包根本分不清是谁的。
- 没有 DNAT：宿主机访问 `10.13.0.5` 的包进了命名空间，但命名空间里没有任何网卡是这个地址，客户机也不认这个地址，包被丢弃。orchestrator 连不上 envd。

### 第 7 步：命名空间里初始化 nftables 防火墙

```go
s.InitializeFirewall()
```

这一步在命名空间里建出第 8 篇看到的 `slot-firewall` 表：四个集合、五条规则，并往预置集合里填好内容。第 15 篇详讲。

**少了会怎样**：沙箱可以随意访问宿主机所在的内网、云元数据服务、同机其他沙箱的地址。安全防线直接没了。

### 第 8 步：回到宿主机，加一条到 Host IP 的路由

```go
netns.Set(hostNS)
netlink.RouteAdd(&netlink.Route{Dst: "10.13.0.5/32", Gw: "10.14.0.11"})
```

等价命令：

```bash
ip route add 10.13.0.5/32 via 10.14.0.11
```

**少了会怎样**：宿主机上的 orchestrator 想访问 `10.13.0.5:49983`（envd），宿主机路由表里找不到这个地址，就按默认路由把包从物理网卡发到机房网络里去了，永远到不了沙箱。

### 第 9 步：宿主机上加转发放行和 MASQUERADE

```bash
# 允许 e2bv-5 和物理网卡之间互相转发
iptables -A FORWARD -i e2bv-5 -o enp125s0f0 -j ACCEPT
iptables -A FORWARD -i enp125s0f0 -o e2bv-5 -j ACCEPT

# 从这个沙箱来的、要从物理网卡出去的包，源地址换成物理网卡的地址
iptables -t nat -A POSTROUTING -s 10.13.0.5/32 -o enp125s0f0 -j MASQUERADE
```

这里的 `enp125s0f0` 不是写死的。orchestrator 启动时读一遍路由表，找到**默认路由所在的网卡**，把它当作“默认出口网卡”（代码里叫 `defaultGateway`）。

**少了会怎样**：

- 没有 FORWARD 放行：如果宿主机的 FORWARD 默认策略是拒绝（很多发行版、Docker 都会这么设），沙箱发往外网的 UDP 包会在宿主机被丢弃。
- 没有 MASQUERADE：包带着 `10.13.0.5` 这个私有地址出了物理网卡。机房网关不认识它，回包回不来。

第 13 篇会讲到：沙箱的 **TCP** 出站并不走 FORWARD 和这条 MASQUERADE，而是被下一步的 REDIRECT 交给本机代理。真正走这条路的是 UDP（比如 DNS）和 ICMP。

### 第 10 步：宿主机上加六条 REDIRECT

先是三条“访问宿主内部服务”的改道，目的地址都是 `192.0.2.1`（第 19 篇）：

```bash
iptables -t nat -A PREROUTING -i e2bv-5 -p tcp -d 192.0.2.1 --dport 80   -j REDIRECT --to-port 5010  # hyperloop
iptables -t nat -A PREROUTING -i e2bv-5 -p tcp -d 192.0.2.1 --dport 111  -j REDIRECT --to-port 5012  # portmap
iptables -t nat -A PREROUTING -i e2bv-5 -p tcp -d 192.0.2.1 --dport 2049 -j REDIRECT --to-port 5011  # NFS 代理
```

再是三条“出站 TCP 交给防火墙代理”的改道（第 16 篇）：

```bash
iptables -t nat -A PREROUTING -i e2bv-5 -p tcp --dport 80  -j REDIRECT --to-port 5016   # HTTP
iptables -t nat -A PREROUTING -i e2bv-5 -p tcp --dport 443 -j REDIRECT --to-port 5017   # TLS
iptables -t nat -A PREROUTING -i e2bv-5 -p tcp             -j REDIRECT --to-port 5018   # 其他 TCP
```

注意顺序很重要：规则从上往下匹配、命中即停。发往 `192.0.2.1:80` 的包先命中第一条，去 hyperloop，而不会被后面的“所有 80 端口 → 5016”截走。

### 第 11 步（本环境补丁新增）：打开一个 conntrack 句柄

```go
s.openConntrackHandle(ctx)
```

为这个命名空间预先打开一个用来操作 conntrack 表的 netlink 套接字，保存在槽位对象里。它和建网本身无关，是为第 20 篇讲的“快照回滚时清理 conntrack”做准备。打开失败也不影响槽位使用。

---

## 三、建完之后：一个槽位在系统里留下了什么

把上面的步骤汇总一下，一个槽位在系统里留下的东西：

| 位置 | 东西 | 数量 |
|---|---|---|
| `/var/run/netns/` | 挂载点 `ns-5` | 1 |
| `ns-5` 里 | 网卡 `lo`、`eth0`（vpeer）、`tap0` | 3 |
| `ns-5` 里 | 默认路由 | 1 |
| `ns-5` 里 | iptables nat 规则（SNAT、DNAT） | 2 |
| `ns-5` 里 | nftables 表 `slot-firewall` | 1 张（4 个集合、5 条规则） |
| 宿主机 | 网卡 `e2bv-5` | 1 |
| 宿主机 | `/32` 路由 | 1 |
| 宿主机 | iptables nat 规则（1 条 MASQUERADE + 6 条 REDIRECT） | 7 |
| 宿主机 | iptables filter 规则（2 条 FORWARD） | 2 |

请特别记住最后两行：**每个槽位在宿主机上留下 9 条 iptables 规则**。300 个槽位就是 2700 条。第 21 篇会看到，这个数字一旦失控会带来什么麻烦。

---

## 四、拆网：RemoveNetwork

槽位不再需要时，比如复用队列满了、orchestrator 退出，就要拆掉。拆网的函数叫 `RemoveNetwork`，大致按相反顺序进行：

1. **丢弃 conntrack 句柄**（补丁新增）。关闭这个套接字可能很慢（第 20 篇），所以交给后台协程去关，不阻塞拆网。
2. **关闭防火墙的连接**。命名空间里的 nftables 表会随命名空间一起消失，这里只是释放程序里的资源。
3. **删除宿主机上的 iptables 规则**：2 条 FORWARD、1 条 MASQUERADE、hyperloop 的 REDIRECT、3 条防火墙代理的 REDIRECT。
4. **删除宿主机上到 Host IP 的 `/32` 路由**。
5. **删除宿主机上的 `e2bv-5` 网卡**。删掉一头，另一头也会跟着消失。
6. **删除 NFS 代理和 portmap 的 REDIRECT 规则**。
7. **删除命名空间** `ns-5`。命名空间里的 `tap0`、NAT 规则、nftables 表、路由，全都随之消失。

两个值得注意的细节：

- **为什么要显式删 veth？** 删掉命名空间时，里面那头 veth 被销毁，宿主机这头本来也会跟着消失。但代码注释说，这个“跟着消失”可能有延迟。如果紧接着又要建一个同名的 `e2bv-5`，就可能撞上还没消失的旧网卡。所以显式先删。
- **命名空间里的东西不用逐条删。** 删掉命名空间，里面的一切就都没了。这是命名空间的一大好处。

![拆网](img/12-2-拆网.svg)

---

## 五、拆不干净会怎样

### 5.1 正常退出与异常退出

orchestrator 正常退出时，会把池子里所有空闲槽位逐个拆掉。但如果它是被 `kill -9` 强杀的、机器断电了、或者拆网中途出错，就会留下“残骸”。

### 5.2 两种残骸

1. **残留的命名空间和 veth。** `/var/run/netns/ns-*` 和宿主机上的 `e2bv-*` 还在，但已经没有任何程序在管它们。
2. **残留的 iptables 规则。** 这是更隐蔽、危害更大的一种。宿主机上那 9 条规则，**不会因为网卡被删而自动消失**。它们会一直留在表里，只是因为匹配的网卡名不存在了而永远不会命中。

### 5.3 残骸的后果

- **残留命名空间会“占坑”。** orchestrator 启动时会扫描 `/var/run/netns`，已经存在的 `ns-N` 被视为“别人的”，以后不再使用这个编号。残留越多，可用编号越少（第 20 篇）。
- **残留规则会拖慢一切。** 第 8 篇讲过，iptables 每修改一条规则，都要把整张表读出来再写回去。残留规则攒到几万条之后，每建一个新槽位（要加 9 条规则）都变得很慢，部署脚本里任何 iptables 操作也都变慢。

这套环境的部署脚本为此专门写了清理逻辑：停服务时识别出“在用”和“残留”的槽位，只清理残留的命名空间、veth 和 iptables 规则，并且用批量方式一次删除上万条规则（第 21 篇）。

---

## 本篇小结

| 步骤 | 做了什么 | 少了会怎样 |
|---|---|---|
| 锁线程 | 把协程钉在一个系统线程上 | 规则可能落到错误的命名空间 |
| 1 建命名空间 | `ns-5`，线程随即进入 | — |
| 2 建 veth、配 vpeer | `eth0` 配 `10.14.0.11/31`，另一头送回宿主 | 命名空间与宿主之间不通 |
| 3 配宿主那头 | `e2bv-5` 配 `10.14.0.10/31` | 同上 |
| 4 建 tap0、启用 lo | `169.254.0.22/30` | Firecracker 起不来；客户机找不到网关 |
| 5 默认路由 | `default via 10.14.0.10` | 出站包在命名空间被丢 |
| 6 两条 NAT | 出 SNAT、入 DNAT | 回包分不清；宿主连不上 envd |
| 7 nftables | 出站防火墙 | 沙箱能访问内网和元数据服务 |
| 8 宿主 `/32` 路由 | Host IP → vpeer | 宿主访问 Host IP 走错方向 |
| 9 FORWARD + MASQUERADE | 转发放行、换成物理网卡地址 | UDP 出站被丢或回不来 |
| 10 六条 REDIRECT | 内部服务 3 条 + 防火墙代理 3 条 | 内部服务不可用；TCP 不经过防火墙 |
| 11 conntrack 句柄 | 补丁新增，为回滚准备 | 回滚变慢，但不影响使用 |
| 拆网 | 删宿主规则、路由、veth，再删命名空间 | 残留命名空间占坑，残留规则拖慢 iptables |

**下一篇预告**：[《包的旅程：出站、回程与宿主访问沙箱》](13-packet-journey.md)。网络建好了，下一篇放一个包进去：跟着它从沙箱里的 `curl` 出发，一跳一跳地走到互联网，再跟着回包一路走回来。每一跳的源地址、目的地址怎么变，哪条规则在起作用，都会一一写清楚。
