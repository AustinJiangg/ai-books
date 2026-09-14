# 写作规约

本文件是全书的体例与口径约定。几十篇文档要读起来像一本书而不是一堆笔记，靠的是这里的规则。
每一篇的编写者在动笔前必须通读本文件；审校时逐条对照。

编写计划（讲哪些主题、每篇写什么）在 [`OUTLINE.md`](OUTLINE.md)；读者导览在 [`README.md`](README.md)；
图的画法在 [`FIGURE-GUIDE.md`](FIGURE-GUIDE.md)。

---

## 一、这本书是什么

一本关于 **Firecracker** 的教材：这个 VMM（virtual machine monitor）由哪些部件构成、每个部件怎么工作、
为什么这样设计、每个决定的代价是什么；e2b 为了自己的内存管线在它上面改了什么；
把它搬到 aarch64（鲲鹏 / openEuler）并为 checkpoint / restore 扩展时又改了什么。

对标的质量：**可以出版的计算机系统教材**，读者是美国顶级大学计算机专业的本科高年级与研究生。
他们懂操作系统、体系结构与系统编程的基本概念，但不一定接触过 KVM、virtio、Rust 系统编程或 Firecracker。
凡是全书要依赖的预备知识，第一部分按需讲解；正文其它地方不假设读者读过 Firecracker 的任何文档，
也不假设读者读过本仓库另一本书（e2b 手册）。需要 e2b 侧背景时链接过去，不复述。

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

全书涉及**三层**代码基线，一层叠一层。称谓固定，不得混用：

| 称谓 | 指什么 | 代码位置（编写时用） |
|---|---|---|
| **上游 v1.12.1** | firecracker-microvm/firecracker 在 tag `v1.12.1` 的代码（commit `d990331f7`） | `tmp/e2b-book-src/fc-upstream/` |
| **e2b 定制版** | e2b-dev/firecracker 分支 `firecracker-v1.12-direct-mem` 的 commit `a41d3fb`（e2b infra 2026.09 钉的默认版本 `v1.12.1_a41d3fb`）：在上游 v1.12.1 之上的 28 个提交，加了内存查询 API、uffd 写保护、可选 memfile 的快照、构建脚本，并合入几处上游 v1.12 分支的修复；加上 e2b-dev/fc-kernels release `v0.0.8` 的 guest 内核配置 | `tmp/e2b-book-src/fc-e2b/`；差异：`git -C tmp/e2b-book-src/fc-e2b diff v1.12.1 a41d3fb -- <path>` |
| **ARM 适配版** | KASandbox 仓库 `firecracker/` 目录在分支 `jll` commit `3863c76` 的形态：迁入 e2b 分叉的 `54a1c1a`（比 a41d3fb 少 uffd 写保护那个提交），加 aarch64 构建修复与 HDBSS 使能，再加本项目为 checkpoint / restore 做的扩展（HDBSS 硬化、脏位图 sidecar、`PUT /snapshot/rollback`、`PUT /snapshot/save-dirty-bitmap`）。部署在鲲鹏上的 `firecracker.arm` 就是它。guest 内核用 e2b-dev/fc-kernels 的 arm64 官方构建，没有改动 | `tmp/e2b-book-src/kasandbox-jll/firecracker/`；checkpoint 扩展之前的中间状态：`tmp/e2b-book-src/kasandbox-arm/firecracker/`（`b8e85c3`）；差异：`git -C KASandbox diff 9e880db b8e85c3 -- firecracker`、`git -C KASandbox diff b8e85c3 3863c76 -- firecracker` |

书里提到 ARM 适配版内部的两段时，写「ARM 适配版的构建与运行部分」「ARM 适配版的 checkpoint / restore 扩展」；不要造第四个称谓。

四条纪律：

1. **未特别说明处，全书讲的都是上游 v1.12.1。** 两层改动分别集中在第九、第十部分。
   上游各篇若某个机制在后面某一层有变化，在该篇小结之前加一个小节，名字固定为
   「**## N. 后续各层的差异**」，两三句话 + 指向对应部分的链接，不展开。没有差异就不加这一节。
2. 描述改动时，**写「上游的假设在这里不成立」「为了 X 放弃了 Y」，不写「上游的缺陷」「某版本做得不对」**。
   凡是明显的技术债（例如注释掉的代码路径、环境变量做开关），如实指出并说明后果，语气中性。
3. **不用内部代号**：不写 M1 / M2 / v3、jll / jll-xfs / deltabox 分支、某某同事、「路线 A」。
   不写「我们决定」「后来改成」这类过程叙事，除非那个过程本身是要讲的知识点
   （例如回滚时 vCPU 为什么选 reinit 而不是只写寄存器：这是设计取舍，要讲；但讲成「两种做法的比较」，不讲成「我们试了两次」）。
   XFS + reflink 路线全书只在第 63、68 篇各提一句。
4. **Firecracker 一侧与 orchestrator 一侧分工**：本书讲 Firecracker 进程内发生的事，外加 guest 内核的配置（不讲内核源码）。
   orchestrator 怎么调用这些 API、差分树、磁盘分层、测试与性能数据，在 e2b 手册与 checkpoint / restore 手册里；需要时链接，不复述。

与另外两本手册的关系：

- e2b 手册（本仓库 `../e2b-infra/`）：链接写成 `[e2b 手册第 37 篇](../e2b-infra/37-pause-and-snapshot.md)`。
  打包成 HTML 后这类链接指向外部文件，所以**只在「延伸阅读」里用，正文里不依赖它**。
- checkpoint / restore 手册：`../../e2b-infra-docs/rollback/docs/<file>.md`，同样只在延伸阅读里用。

### 关于代码的引用位置

- 上游代码：写成 `src/vmm/src/vstate/vm.rs` 这样的仓库相对路径（相对于 firecracker 仓库根，
  KASandbox 里就是相对于 `firecracker/` 目录），必要时加函数名：`vm.rs` 的 `snapshot_memory_to_file()`。
  **不写绝对路径，不写行号**（行号随版本漂移；函数名不会）。
- 各层的改动：同样用仓库相对路径，并说明「e2b 定制版在此处加了 …」「ARM 适配版在此处改为 …」。
- guest 内核：`fc-kernels` 仓库相对路径：`configs/arm64/6.1.158.config`、`build.sh`。本书不讲内核源码。
- 引用代码片段只截取说明问题的部分；超过 30 行改用文字描述 + 位置指引。
  片段中允许省略号 `…` 与删减，但不得改写语义。
- Rust 代码里的类型与函数：`Vmm`、`VmmAction::CreateSnapshot`、`GuestMemoryExtension::dump_dirty()`。
  trait 方法写 `Trait::method()`，关联函数写 `Type::new()`。

---

## 三、术语表（固定译法）

正文中文；标识符、文件名、命令、路径保持英文原样。下表中的术语按表中写法使用，
第一次出现时给出英文（括号内），之后可只用中文或只用英文，但**同一篇内保持一致**。

| 中文 | 英文 | 备注 |
|---|---|---|
| 虚拟机监控器 | VMM（virtual machine monitor） | 首次出现后一律用 VMM |
| 微型虚拟机 | microVM | 不翻译 |
| 客户机 | guest | 首次出现后可用 guest |
| 宿主机 | host | 同上 |
| vCPU | vCPU | 不翻译 |
| 内存槽位 | memslot（KVM memory slot） | KVM 语境 |
| 客户机物理地址 | GPA（guest physical address） | |
| 宿主虚拟地址 | HVA（host virtual address） | |
| 脏页 | dirty page | |
| 脏页位图 | dirty bitmap | KVM 日志与 Firecracker 用户态位图都用这个词，要指明是哪一个 |
| 写保护 | write protect（WP） | |
| 大页 | huge pages | 2 MiB HugeTLB |
| 缺页 | page fault | |
| 快照 | snapshot | vmstate 文件 + 内存文件 |
| 内存文件 | memfile | 快照中的 guest 内存产物；e2b 的叫法 |
| 状态文件 | vmstate（snapshot file） | `snapshot_path` 指向的文件 |
| 全量 / 差分快照 | Full / Diff snapshot | |
| 暂停 / 恢复 | pause / resume | `PATCH /vm` |
| 原地回滚 | in-place rollback | ARM 适配版的 `PUT /snapshot/rollback` |
| 设备 | device | virtio 设备与 legacy 设备的统称 |
| 队列 | virtqueue | virtio 语境，首次出现后可用 queue |
| 描述符链 | descriptor chain | |
| 传输层 | transport | virtio-mmio |
| 事件循环 / 事件管理器 | event loop / EventManager | |
| 速率限制器 | rate limiter | 令牌桶 |
| 中断 | interrupt | irqfd / ioeventfd 保持英文 |
| 系统调用过滤 | seccomp filter | |
| 监狱 | jailer | 不翻译 |
| CPU 模板 | CPU template | |
| 元数据服务 | MMDS（microVM metadata service） | |
| 设备树 | FDT（flattened device tree） | aarch64 |
| 中断控制器 | GIC | aarch64，不翻译 |
| 硬件脏页跟踪 | HDBSS（hardware dirty bit state structure） | 鲲鹏 950 特性；首次出现给全称 |
| 控制面 | control plane | API server + rpc_interface |
| 数据面 | data plane | 设备 I/O 路径 |
| 位图 sidecar | dirty bitmap sidecar | `dirty_bitmap_path` 写出的 FCDB 文件 |
| 拓扑 | topology | 回滚校验语境：设备数量、类型与顺序 |

**不翻译**的专有名词：Firecracker、KVM、virtio、virtio-mmio、vhost-user、userfaultfd、io_uring、seccomp、BPF、
jailer、cgroup、namespace、musl、Rust、cargo、crate、serde、bincode、Kani、pytest、devtool、Docker、
tap、vsock、balloon、ACPI、PVH、CPUID、MSR、PSCI、SVE、openEuler、鲲鹏（Kunpeng）、e2b、orchestrator。

---

## 四、体例

### 4.1 每篇的固定结构

```
# NN · 标题

> 一到三句话说明本篇讲什么、为什么值得读。
>
> **读者**：… 　**预备**：第 N 篇 … 　**代码**：`src/vmm/src/a.rs`、`src/vmm/src/b.rs`

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
- 上游各篇末尾如有后续层的差异，小节名固定为「## N. 后续各层的差异」（放在小结之前）。

### 4.2 篇幅

正文 **3000–5000 汉字**（不含代码块与表格）。少于 2500 或多于 6500 要重新审视范围。
一篇讲不完就在 OUTLINE 里拆篇，不硬塞。

### 4.3 语言

- 一句话一个意思。段落不超过 6 行。
- 用「它」指代系统部件，不拟人化到「它认为」「它希望」。
- 不用「显然」「众所周知」；需要读者相信的地方给证据。
- 不用感叹号。不用 emoji。
- 数字与单位之间留空格（`512 MiB`、`20 ms`）；容量统一 MiB / GiB；时间统一 ms（μs 只用于 Firecracker 内部分段计时）。
- 任何性能数字必须紧跟测量条件（机型、内核、guest 大小、并发度）。本书原则上不给性能数字；
  需要时链接 checkpoint / restore 手册。
- Rust 语言本身只讲本书用得到的（第 5 篇）；正文里不做 Rust 教学，不解释 `Result`、`Option`、借用。

### 4.4 图

- 新画的图一律用内嵌 mermaid。可用类型：`flowchart`、`sequenceDiagram`、`stateDiagram-v2`、`classDiagram`（少用）。
- mermaid 节点文字中**不要**出现未转义的括号、引号、`|`、`{}`；标签里的中文与英文之间加空格。
  节点标签统一用方括号 `A[文字]` 或双引号 `A["文字 (带括号)"]`。
- 目录结构、文件布局、字节布局、寄存器布局用 ASCII 代码块（```text），不用 mermaid。
- 每篇建议 1–3 张图；一张图不超过 20 个节点。
- 尺寸、重叠、各类图的具体画法与检查工具见 [FIGURE-GUIDE.md](FIGURE-GUIDE.md)；以 `tools/figcheck.sh` 的 PASS 为准。

### 4.5 表格

- 对比表第一列是对比维度，后续列是被比较的对象。
- 枚举表（API 端点、字段、配置项、系统调用）保持列数 ≤ 5，长说明进正文。

### 4.6 交叉引用

- 引用别的篇目一律写显式链接：`[第 36 篇 · 创建快照](36-snapshot-create.md)`，
  引用到小节时加锚点：`[第 14 篇 §3](14-dirty-page-tracking.md#3-两张位图)`。
- 锚点用 GitHub 规则：全小写、去标点、空格转连字符、中文保留；
  「## 3. 两张位图」的锚点是 `#3-两张位图`；「### 3.2 写保护」的锚点是 `#32-写保护`。
- 不写「见上文」「如前所述」。
- 只链接到 OUTLINE 里存在的文件名。目标篇还没写时只链到文件，不加锚点。
- 另外两本手册只在「延伸阅读」里链接（见第二节）。

### 4.7 代码与命令

- 行内代码：函数名、类型名、字段名、文件名、环境变量、路径、命令、API 路径。
- 代码块标注语言（```rust、```bash、```json、```yaml、```text、```mermaid、```c）。
- 命令示例给完整可运行的形式，不写 `$` 提示符。
- API 请求示例用 ```json 给请求体，路径与方法写在正文（`PUT /snapshot/create`）。

---

## 五、编写者自检清单

提交前逐条确认：

- [ ] 标题、题注、「0. 本篇要回答的问题」、「小结」、「延伸阅读 / 下一篇」齐全
- [ ] 正文 3000–5000 汉字
- [ ] 每个行为论断都能对应到代码位置或标注了「推论」
- [ ] 代码路径都是仓库相对路径，函数名与代码一致（读过代码，不是凭印象）
- [ ] 术语与第三节一致；版本称谓与第二节一致（上游 v1.12.1 / e2b 定制版 / ARM 适配版）
- [ ] mermaid 代码块语法合法（用 `tools/mdmermaid.mjs` 检查），节点标签无未转义字符
- [ ] 每张图在 `tools/figcheck.sh` 下 PASS（见 FIGURE-GUIDE.md）
- [ ] 所有交叉链接指向 OUTLINE 中存在的文件名（用 `tools/mdlinks.py` 检查）
- [ ] 没有内部代号、没有过程叙事、没有「我们决定」
- [ ] 上游篇目末尾的「后续各层的差异」小节（若该机制在后面某层有变化）
- [ ] 「本篇要回答的问题」里的每个问题，正文都有明确的回答
