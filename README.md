# ai-books —— AI 写的书

这里放用 AI Agent 编写的书。每本书一个目录，正文是一篇篇 Markdown，在 GitHub 上点开就能读；
每本书另有一个单文件网页版，放在 GitHub Pages 上：<https://austinjiangg.github.io/ai-books/>。

## 书目

- **e2b 服务端基础设施技术手册** · [网页版](https://austinjiangg.github.io/ai-books/html/e2b-infra.html) · [Markdown](e2b-infra/README.md)<br>
  [e2b-dev/infra](https://github.com/e2b-dev/infra) tag `2026.09` 及其 aarch64（鲲鹏 / openEuler）适配版。
- **Firecracker 技术手册** · [网页版](https://austinjiangg.github.io/ai-books/html/firecracker.html) · [Markdown](firecracker/README.md)<br>
  上游 Firecracker v1.12.1、e2b 定制版、ARM 适配版与 checkpoint / restore 扩展四层的代码讲解。
- **AI Agent 沙箱** · [网页版](https://austinjiangg.github.io/ai-books/html/agent-sandbox.html) · [Markdown](agent-sandbox/README.md)<br>
  Agent 沙箱作为 RL 训练、评测与产品推理的基础设施：隔离原语、参考架构、案例与研究议程。
- **C++ 期末笔试突击手册** · [网页版](https://austinjiangg.github.io/ai-books/html/cpp-exam.html) · [Markdown](cpp-exam/README.md)<br>
  按 Stroustrup《C++程序设计语言》（第 4 版，C++11）讲大学 C++ 期末笔试考点。
- **AgentENV 技术手册** · [网页版](https://austinjiangg.github.io/ai-books/html/agentenv.html) · [Markdown](agentenv/README.md)<br>
  [kvcache-ai/AgentENV](https://github.com/kvcache-ai/AgentENV) tag `v0.2.3` 的代码讲解，并与 e2b infra 逐项对照。
- **mmap 从零讲透** · [网页版](https://austinjiangg.github.io/ai-books/html/mmap.html) · [Markdown](mmap/README.md)<br>
  写给新手的 mmap 教程：从系统调用、虚拟内存、缺页与页缓存讲到写时复制、落盘、性能、内核实现与 Firecracker。
- **彻底搞懂 Firecracker** · [网页版](https://austinjiangg.github.io/ai-books/html/firecracker-intro.html) · [Markdown](firecracker-intro/README.md)<br>
  写给新手的 Firecracker 教程（v1.17.0，以 ARM64 为例）：从电脑如何运转、KVM 讲到动手启动 microVM、virtio、网络、存储、jailer、快照、性能与源码导读。
- **MMIO 从零讲透** · [网页版](https://austinjiangg.github.io/ai-books/html/mmio.html) · [Markdown](mmio/README.md)<br>
  写给新手的 MMIO 教程：从 CPU 怎么控制硬件、地址空间与设备寄存器讲到 volatile、内存属性、屏障、中断、DMA、Linux 驱动、PCIe、用户态访问与虚拟机。
- **E2B 沙箱网络从零讲透** · [网页版](https://austinjiangg.github.io/ai-books/html/e2b-network.html) · [Markdown](e2b-network/README.md)<br>
  写给新手的 E2B 沙箱网络教程（2026.09 + ARM 补丁，单机鲲鹏部署）：从 IP、路由、DNS、网络命名空间、veth、tap、iptables/nftables、NAT 与 conntrack 讲到网络槽位、出站防火墙、入口代理、部署配置与排障。

网页版是单个 HTML 文件，图可点击放大，手机也能看；想离线看，在页面上 Ctrl+S（Mac 上 ⌘+S）存下来即可。

## 仓库结构

- `<书>/`：一本书，`README.md` 是导读与目录，正文是 `NN-xxx.md`。
- [`html/`](html/)：各书的网页版。
- [`tools/`](tools/)：检查与生成网页版的脚本。
