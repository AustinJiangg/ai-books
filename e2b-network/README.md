# E2B 沙箱网络从零讲透

一本写给计算机新手的 E2B 沙箱网络教程，讲的是一套实际在用的部署：

- **源码**：上游 [e2b-dev/infra](https://github.com/e2b-dev/infra) tag `2026.09`，加 ARM 适配补丁。
- **机器**：单机鲲鹏服务器，openEuler。
- **部署**：RPM 安装到 `/opt/e2b-infra`，依次执行 `build.sh -d/-i/-s`。

前 8 篇是够用的网络基础：IP 与子网、路由、TCP、DNS、网络命名空间、veth、tap、iptables、NAT、conntrack、nftables。

之后按全景图一段段拆开：

1. 虚拟机的网卡。
2. 为什么每个沙箱的地址都是 `169.254.0.21`。
3. 一个网络槽位的拓扑与建网过程。
4. 包的完整旅程，沙箱里的 DNS。
5. 出站管控：命名空间里的 nftables，以及按域名过滤的 TCP 防火墙代理。
6. 入站与内部通道：宿主机的 dnsmasq 与 80→3002、从 SDK 到 envd 的两层代理、`192.0.2.1` 背后的宿主服务。

最后讲槽位池与快照回滚时的 conntrack 清理、部署脚本里的每一项网络配置，以及排障与安全。

约 5.7 万汉字，22 篇。

本书只读不练，没有需要动手的实验；文中的代码和命令都是帮助理解的示例片段，不追求完整可运行。

## 目录

### 第一部分　打地基：够用的网络知识

- [第 1 篇　从一行 `curl` 说起：E2B 沙箱网络要解决什么问题](01-what-sandbox-network-solves.md)
- [第 2 篇　网络基础（一）：IP 地址、子网与几类特殊地址](02-ip-addresses-and-subnets.md)
- [第 3 篇　网络基础（二）：以太网、ARP、路由表与转发](03-ethernet-arp-routing.md)
- [第 4 篇　网络基础（三）：TCP、UDP、端口与连接](04-tcp-udp-ports.md)
- [第 5 篇　网络基础（四）：DNS 是怎么工作的](05-how-dns-works.md)
- [第 6 篇　Linux 虚拟网络的积木：网络命名空间、veth 与 tap](06-netns-veth-tap.md)
- [第 7 篇　Netfilter（一）：iptables、NAT 与 conntrack](07-iptables-nat-conntrack.md)
- [第 8 篇　Netfilter（二）：nftables 与集合](08-nftables-and-sets.md)

### 第二部分　一个沙箱的网络栈

- [第 9 篇　虚拟机的网卡：Firecracker、virtio-net 与 tap](09-firecracker-virtio-net-tap.md)
- [第 10 篇　快照带来的难题：为什么每个沙箱都是 169.254.0.21](10-snapshot-same-address.md)
- [第 11 篇　一个槽位的拓扑：几块网卡、几个地址](11-slot-topology.md)
- [第 12 篇　建网与拆网：CreateNetwork 一步一步](12-create-and-remove-network.md)
- [第 13 篇　包的旅程：出站、回程与宿主访问沙箱](13-packet-journey.md)
- [第 14 篇　沙箱里的 DNS](14-dns-inside-sandbox.md)

### 第三部分　管住出站流量

- [第 15 篇　出站防火墙（一）：命名空间里的 nftables](15-nftables-firewall.md)
- [第 16 篇　出站防火墙（二）：TCP 防火墙代理](16-tcp-firewall-proxy.md)

### 第四部分　入站与内部通道

- [第 17 篇　宿主机的入口：dnsmasq、Consul DNS 与 80→3002](17-host-entry-dns-iptables.md)
- [第 18 篇　从 SDK 到 envd：一次沙箱请求的完整路径](18-sdk-to-envd.md)
- [第 19 篇　沙箱访问宿主服务：192.0.2.1 背后的 hyperloop、NFS 与 portmap](19-sandbox-to-host-services.md)

### 第五部分　规模、运维与这套环境的改动

- [第 20 篇　槽位池、复用与快照回滚下的 conntrack](20-slot-pool-and-conntrack.md)
- [第 21 篇　部署脚本里的网络配置：build.sh 的 -d、-i、-s](21-deploy-script-network-config.md)
- [第 22 篇　全景、排障与安全](22-big-picture-troubleshooting-security.md)

编写用文件：[`OUTLINE.md`](OUTLINE.md)（各篇要点）。

## 怎么读

- **第 1 篇的全景图是全书的地图**：后面每一篇都在放大它的某一段，读到迷糊时回去看一眼。
- **第 2～8 篇是通用基础**：只讲后面要用到的网络和 Linux 知识，不涉及 E2B。有网络基础的读者可以只看每篇的小结表。
- **第 10 篇是钥匙**：“快照里的地址改不了”推出了整套设计。只想抓主线，读第 1、10、11、13 篇即可。
- **第 15～19 篇讲规则**：每一条 iptables、nftables 规则从哪来、防什么。第 19 篇末尾有全书地址转换总表。
- **第 20、21 篇最贴近运维**：槽位池、残留清理、部署顺序、配置项总表、与 AgentENV 同机。
- **第 22 篇可以当手册用**：附排障速查表、安全回顾和术语表。
- 每篇末尾有“本篇小结”表格，复习时过一遍小结即可。
