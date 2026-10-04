# 写作规约

本文件是全书的体例与口径约定。七十多篇文档要读起来像一本书而不是一堆笔记，靠的是这里的规则。
每一篇的编写者在动笔前必须通读本文件；审校时逐条对照。

编写计划（讲哪些主题、每篇写什么）在 [`OUTLINE.md`](OUTLINE.md)；读者导览在 [`README.md`](README.md)；
图的画法在 [`FIGURE-GUIDE.md`](FIGURE-GUIDE.md)。

---

## 一、这本书是什么

一本关于 **AgentENV**（[kvcache-ai/AgentENV](https://github.com/kvcache-ai/AgentENV)，tag `v0.2.3`）的教材：
这个为 agent 环境设计的沙箱平台由哪些部件构成、每个部件怎么工作、为什么这样设计、每个决定的代价是什么；
它依赖的 Firecracker 补丁做了什么；以及它和 e2b infra 在同一组问题上做了哪些不同的取舍。

对标的质量：**可以出版的计算机系统教材**，读者是美国顶级大学计算机专业的本科高年级与研究生。
他们懂操作系统、存储、网络与分布式系统的基本概念，但不一定接触过 io_uring、ublk、overlaybd、Firecracker 或 Rust 异步编程。
凡是全书要依赖的预备知识，第一部分按需讲解；正文其它地方不假设读者读过 AgentENV 的任何文档，
也不假设读者读过本仓库另外两本书（e2b 手册、Firecracker 手册）。需要那两本书的背景时链接过去，不复述。

### 五条质量标准

1. **每个论断可追溯。** 凡涉及系统行为的陈述，要么给出代码位置（文件路径 + 函数名），
   要么明确标注为推论（「推论：…」）。读者必须能区分事实与推论。
2. **先讲问题，再讲方案。** 任何机制出场前，读者应当已经知道不这么做会怎样。
3. **代价与收益成对出现。** 只讲收益的段落是宣传稿，不是教材。
4. **每篇自足但不重复。** 交叉引用用链接，不复制正文；确实要重复的关键结论，用「回顾」明确标出。
5. **配图服务于理解，不是装饰。** 表格用于对比与枚举；流程图 / 时序图用于时序与依赖；
   结构图用于部件与边界。没有第四类图。

---

## 二、版本与称谓口径

全书只有**一条主线基线**，外加它依赖的补丁版 Firecracker 与两个对照对象。称谓固定，不得混用：

| 称谓 | 指什么 | 代码位置（编写时用） |
|---|---|---|
| **AgentENV v0.2.3** | kvcache-ai/AgentENV tag `v0.2.3`（commit `6cccaa7842bd`，2026-09-30） | `tmp/e2b-book-src/agentenv/` |
| **AENV 补丁版 Firecracker** | kvcache-ai/firecracker tag `aenv-deps`（commit `90288c39`）：上游 v1.15.1 之上 7 个提交。发布资产名是 `1.15.1-patch-v1`，即 `config/deps_manifest.toml` 的 `[firecracker.kvm]` | `tmp/e2b-book-src/fc-aenv/`；差异：`git -C tmp/e2b-book-src/fc-aenv diff v1.15.1 aenv-deps -- <path>` |
| **上游 Firecracker v1.15.1** | firecracker-microvm/firecracker tag `v1.15.1`（commit `f82c0bd0`） | 同一 clone 的 tag `v1.15.1` |
| **Rust 版 overlaybd** | AgentENV 仓库内的 `storage/overlaybd` crate：用 Rust 重写的 overlaybd 在线数据面 | `tmp/e2b-book-src/agentenv/storage/overlaybd/` |
| **上游 overlaybd** | containerd/overlaybd（C++，tcmu 前端） | `tmp/e2b-book-src/overlaybd-upstream/`（只为核实格式兼容） |
| **overlaybd 工具** | kvcache-ai/overlaybd `static-v1.0.18-aenv.1` 发布的 `overlaybd-create/apply/commit/resize` 二进制 | 不读源码，只讲调用方式 |
| **e2b infra** | e2b-dev/infra tag `2026.09`，即 e2b 手册的基线 | 优先读 e2b 手册；必要时读 `tmp/e2b-book-src/upstream/` |

五条纪律：

1. **未特别说明处，全书讲的都是 AgentENV v0.2.3。** 写「AgentENV」就是指 v0.2.3；只有讲版本历史时才写其它版本号。
   不写 main 分支在 v0.2.3 之后的改动。
2. **Firecracker 本身的机制不在本书展开。** 需要时用一两句话回顾，并在「延伸阅读」里链接 Firecracker 手册对应篇。
   AENV 补丁版 Firecracker 的改动集中在第 67 篇；其它篇用到某个补丁行为时，写「AENV 补丁版 Firecracker 新增的 `GET /vm/dirty-memory-ranges`」，
   并链接第 67 篇。不要把补丁行为写成上游就有。
3. **overlaybd 的三个称谓不得混用。** 「Rust 版 overlaybd」是在线读写路径；「overlaybd 工具」是离线转换与扩容；「上游 overlaybd」只在讲格式兼容时出现。
   讲格式时要说明是「与上游兼容」还是「AgentENV 扩展」。
4. **与 e2b infra 的对照**：第 65、66 篇集中讲。其它篇若某个机制与 e2b infra 的做法明显不同，可在小结之前加一个小节，
   名字固定为「**## N. 与 e2b infra 的对照**」，两到四句话，只讲「e2b 怎么做、为什么这里不同、代价是什么」，不展开，不评优劣。
   没有明显差异就不加这一节。e2b 侧的依据来自 e2b 手册；拿不准的写「推论：」。
5. **描述设计时写取舍，不写评判。** 写「这里放弃了 X 换取 Y」「这个假设在 Z 情况下不成立」，不写「设计缺陷」「做得不对」。
   凡是明显的技术债（注释掉的代码路径、TODO、文档与代码不一致、名不副实的测试），如实指出并说明后果，语气中性；
   集中汇总在第 68 篇。不写过程叙事（「后来改成」「我们决定」），除非那个演化本身是要讲的知识点
   （例如 uffd 方案为什么被块设备 File 后端取代：讲成「两种方案的比较」，不讲成「项目的历史」）。

与另外两本手册的关系：

- e2b 手册（本仓库 `../e2b-infra/`）：链接写成 `[e2b 手册第 31 篇](../e2b-infra/31-uffd-memory-backend.md)`。
- Firecracker 手册（本仓库 `../firecracker/`）：链接写成 `[Firecracker 手册第 38 篇](../firecracker/38-snapshot-load.md)`。
- 打包成 HTML 后这类链接指向外部文件，所以**只在「延伸阅读」里用，正文里不依赖它**。
  正文里需要提到时写「（见 Firecracker 手册第 38 篇）」这样的文字，不加链接。

### 关于代码的引用位置

- AgentENV 代码：写成 `src/orchestrator/service.rs` 这样的仓库相对路径，必要时加函数名：`service.rs` 的 `launch_sandbox()`。
  Go 代码同样：`services/scheduler/internal/service.go` 的 `Schedule()`。
  **不写绝对路径，不写行号**（行号随版本漂移；函数名不会）。
- AENV 补丁版 Firecracker：同样用 firecracker 仓库相对路径，并说明「AENV 补丁版在此处加了 …」：`src/vmm/src/vstate/vm.rs` 的 `get_dirty_memory_ranges_preserve()`。
- 引用代码片段只截取说明问题的部分；超过 30 行改用文字描述 + 位置指引。
  片段中允许省略号 `…` 与删减，但不得改写语义。
- Rust 类型与函数：`Orchestrator`、`SandboxState::Pausing`、`ImageFile::create_snapshot_and_restack()`。
  trait 方法写 `Trait::method()`，关联函数写 `Type::new()`。
- 生成代码（`src/api/generated/`、`thirdparty/firecracker-client/`、`src/custom_extension_api/generated/`、`services/api/proto/*.pb.go`）
  只在讲生成机制时引用；讲行为时引用它的来源（`openapi.yml`、`firecracker.yaml`、`scheduler.proto`）。
- 文档（`docs/src/**`、`AGENTS.md`）只作参考。文档与代码不一致时以代码为准，并在交付说明里记下这处不一致。

---

## 三、术语表（固定译法）

正文中文；标识符、文件名、命令、路径保持英文原样。下表中的术语按表中写法使用，
第一次出现时给出英文（括号内），之后可只用中文或只用英文，但**同一篇内保持一致**。

| 中文 | 英文 | 备注 |
|---|---|---|
| 沙箱 | sandbox | 一台 microVM 及其附属资源；API 与代码里的 sandbox |
| 微型虚拟机 | microVM | 不翻译 |
| 客户机 / 宿主机 | guest / host | 首次出现后用 guest / host |
| 节点 | node | 运行 `server` 进程的一台宿主机 |
| 模板 | template | source = Template 的快照记录 |
| 快照 | snapshot | 仓库里的已提交快照；区别于 Firecracker 的快照文件时写「Firecracker 快照」 |
| 快照仓库 | snapshot repository | POSIX 或对象存储后端；持久真相 |
| 制品 | artifact | 快照的组成文件（vm_state、manifest、层、startup manifest） |
| 层 / 层栈 | layer / layer stack | overlaybd 层；多层叠成层栈 |
| 下层 / 可写层 | lower / upper | 首次出现后可用英文 |
| 封存 | seal | 把可写层原地封口成只读层 |
| 重叠层 | restack | 封存当前 upper、把它压到 lower 栈顶、换上新的空 upper；首次出现后用 restack |
| 压实 | compact | 把多层合并成一层；首次出现后可用 compact |
| 卷 | volume | 持久块存储，可挂到多个沙箱 |
| 附加盘 | extra drive | 冷启动时随沙箱创建的块设备 |
| 内存层 | memory layer | 内存快照对应的 overlaybd 层 |
| 脏页 | dirty page | |
| 脏页区间 | dirty memory ranges | AENV 补丁版 Firecracker 的 `GET /vm/dirty-memory-ranges` 返回值 |
| 宿主虚拟地址 | HVA（host virtual address） | |
| 页缓存 | page cache | 内核块设备 / 文件页缓存 |
| 按需加载 | lazy loading（on-demand loading） | |
| 启动包 | startup pack | 首触页 trace 与 startup manifest 的统称；首次出现后可用英文 |
| 预热池 | warm pool | |
| 槽位 | slot | 网络槽位（一个 netns）；卷槽位（预留的 virtio-blk 设备） |
| 网络命名空间 | netns（network namespace） | |
| 出站策略 | egress policy | |
| 透明代理 | transparent proxy | egress 代理 |
| 反向代理 | reverse proxy | 节点内 `/proxy` 与 gateway |
| 控制面 / 数据面 | control plane / data plane | 控制面 = 带 API key 的管理请求；数据面 = 送进 guest 的流量 |
| 绑定 | binding | scheduler 里 sandbox → node 的映射 |
| 心跳 | heartbeat | |
| 驱逐 | eviction | 自动驱逐（auto-eviction）：TTL 到期后 pause 或 delete |
| 过期时间 | TTL / timeout | 正文统一写 TTL，API 字段名照写 `timeout` |
| 自定义扩展 | custom extension | 首次出现后可用英文 |
| 用户态块设备 | ublk | 不翻译 |
| 守护进程 | daemon | `uvm-ublk-daemon` 写作 ublk-daemon |
| 运行时 | runtime | tokio runtime 与「运行时目录 / 运行时层」两种语境，必须能从上下文分清 |
| 取消安全 | cancellation safety | |
| 能力 | capability | Linux capability，`CAP_SYS_ADMIN` 等照写 |
| 虚拟化模式 | virtualization mode | KVM / PVM |

**不翻译**的专有名词：AgentENV、AENV、E2B、e2b、Firecracker、KVM、PVM、virtio、io_uring、ublk、overlaybd、LSMT、ZFile、OCI、BuildKit、
buildctl、regctl、envd、MMDS、tap、veth、iptables、conntrack、userfaultfd（uffd）、RocksDB、opendal、iroh、tokio、axum、tonic、
confique、Redis、Kubernetes、EndpointSlice、DaemonSet、gateway、scheduler、orchestrator、Rust、Go、cargo、crate、Docker、systemd、DAMON。

---

## 四、体例

### 4.1 每篇的固定结构

```
# NN · 标题

> 一到三句话说明本篇讲什么、为什么值得读。
>
> **读者**：… 　**预备**：第 N 篇 … 　**代码**：`src/a.rs`、`storage/b/src/c.rs`

---

## 0. 本篇要回答的问题
1. … （3–6 个具体问题，读者读完应能自答）

## 1. …（正文各节）
…
## N. 小结
- 结论清单（5–10 条），不是内容复述

## 延伸阅读 / 下一篇
- 相关篇目与外部资料
```

- 标题格式 `# NN · 标题`，NN 是两位篇号，中间是「·」（U+00B7），两侧各一个空格。
- 二级标题用「## 数字. 标题」，三级用「### 数字.数字 标题」。不用四级以下标题。
- 「## 0. 本篇要回答的问题」与「## N. 小结」是必需的。
- 可选小节「## N. 与 e2b infra 的对照」放在小结之前（见第二节第 4 条）。

### 4.2 篇幅

正文 **3000–5000 汉字**（不含代码块与表格）。少于 2500 或多于 6500 要重新审视范围。
一篇讲不完就在 OUTLINE 里拆篇，不硬塞。附录篇（69–73）以表格为主，不受下限约束。

### 4.3 语言

- 一句话一个意思。段落不超过 6 行。
- 用「它」指代系统部件，不拟人化到「它认为」「它希望」。
- 不用「显然」「众所周知」；需要读者相信的地方给证据。
- 不用感叹号。不用 emoji。不写宣传腔（「极致」「秒级」「颠覆」）。
- 数字与单位之间留空格（`512 MiB`、`20 ms`）；容量统一 KiB / MiB / GiB；时间统一 ms / s。
- **本书不给性能数字。** README 与文档里的延迟、密度、超卖比等宣称不引用；需要说明量级时讲机制（「写入量正比于脏页数」），不讲测量值。
  代码里作为配置默认值出现的数字（超时、水位、并发度）可以写，那是行为，不是性能。
- Rust 语言本身只讲本书用得到的（第 07 篇）；正文里不做 Rust 教学，不解释 `Result`、`Option`、借用。

### 4.4 图

- 新画的图一律用内嵌 mermaid。可用类型：`flowchart`、`sequenceDiagram`、`stateDiagram-v2`、`classDiagram`（少用）。
- mermaid 节点文字中**不要**出现未转义的括号、引号、`|`、`{}`；标签里的中文与英文之间加空格。
  节点标签统一用方括号 `A[文字]` 或双引号 `A["文字 (带括号)"]`。
- 目录结构、文件布局、字节布局、位域用 ASCII 代码块（```text），不用 mermaid。
- 每篇建议 1–3 张图；一张图不超过 20 个节点。
- 尺寸、重叠、各类图的具体画法与检查工具见 [FIGURE-GUIDE.md](FIGURE-GUIDE.md)；以 `tools/figcheck.sh` 的 PASS 为准。
- 时序图常用参与者短名（在图前正文里说明）：`cli`、`api`、`orch`（orchestrator）、`fc`（Firecracker 进程）、`ublkd`（ublk-daemon）、
  `envd`、`repo`（快照仓库）、`gw`（gateway）、`sched`（scheduler）。

### 4.5 表格

- 对比表第一列是对比维度，后续列是被比较的对象。
- 枚举表（API 端点、字段、配置项、RPC）保持列数 ≤ 5，长说明进正文。

### 4.6 交叉引用

- 引用别的篇目一律写显式链接：`[第 42 篇 · 内存快照](42-memory-snapshot-over-ublk.md)`，
  引用到小节时加锚点：`[第 34 篇 §2](34-lsmt-format-and-index.md#2-段映射)`。
- 锚点用 GitHub 规则：全小写、去标点、空格转连字符、中文保留；
  「## 2. 段映射」的锚点是 `#2-段映射`；「### 3.2 Hybrid 写入」的锚点是 `#32-hybrid-写入`。
- 不写「见上文」「如前所述」。
- 只链接到 OUTLINE 里存在的文件名。目标篇还没写时只链到文件，不加锚点。
- 另外两本手册只在「延伸阅读」里链接（见第二节）。

### 4.7 代码与命令

- 行内代码：函数名、类型名、字段名、文件名、环境变量、路径、命令、API 路径、配置键（`[pool.firecracker]`、`memory_snapshot.track_dirty_pages`）。
- 代码块标注语言（```rust、```go、```bash、```json、```toml、```yaml、```text、```mermaid）。
- 命令示例给完整可运行的形式，不写 `$` 提示符。
- API 请求示例用 ```json 给请求体，路径与方法写在正文（`POST /v2/sandboxes`）。

---

## 五、编写者自检清单

提交前逐条确认：

- [ ] 标题、题注、「0. 本篇要回答的问题」、「小结」、「延伸阅读 / 下一篇」齐全
- [ ] 正文 3000–5000 汉字
- [ ] 每个行为论断都能对应到代码位置或标注了「推论」
- [ ] 代码路径都是仓库相对路径，函数名与代码一致（读过代码，不是凭印象）
- [ ] 术语与第三节一致；称谓与第二节一致（AgentENV v0.2.3 / AENV 补丁版 Firecracker / 上游 Firecracker v1.15.1 / Rust 版 overlaybd / 上游 overlaybd / overlaybd 工具 / e2b infra）
- [ ] 补丁版 Firecracker 的行为没有写成上游就有；AgentENV 扩展的格式没有写成上游兼容
- [ ] 没有性能数字；没有宣传腔
- [ ] mermaid 代码块语法合法（用 `tools/mdmermaid.mjs` 检查），节点标签无未转义字符
- [ ] 每张图在 `tools/figcheck.sh` 下 PASS（见 FIGURE-GUIDE.md）
- [ ] 所有交叉链接指向 OUTLINE 中存在的文件名（用 `tools/mdlinks.py` 检查）；另外两本手册只出现在「延伸阅读」
- [ ] 没有过程叙事、没有「我们决定」
- [ ] 「与 e2b infra 的对照」小节（若有）不超过四句、不评优劣
- [ ] 「本篇要回答的问题」里的每个问题，正文都有明确的回答
