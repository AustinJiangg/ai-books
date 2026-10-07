# 写作规约

本文件是全书的体例与口径约定。九十多篇文档要读起来像一本书而不是一堆笔记，靠的是这里的规则。
每一篇的编写者在动笔前必须通读本文件；审校时逐条对照。

编写计划（讲哪些主题、每篇写什么）在 [`OUTLINE.md`](OUTLINE.md)；读者导览在 [`README.md`](README.md)。

---

## 一、这本书是什么

一本关于 **e2b 服务端基础设施**（[e2b-dev/infra](https://github.com/e2b-dev/infra)）的教材：
它由哪些部件构成、每个部件怎么工作、为什么这样设计、每个决定的代价是什么，
以及把它移植到 aarch64（鲲鹏 / openEuler）时改了什么、为什么要改。

对标的质量：**可以出版的计算机系统教材**，读者是美国顶级大学计算机专业的本科高年级与研究生。
他们懂操作系统、网络与分布式系统的基本概念，但不一定接触过 KVM、userfaultfd、Firecracker、Nomad。
凡是全书要依赖的预备知识，第一部分按需讲解；正文其它地方不假设读者读过 e2b 的任何文档。

### 五条质量标准

1. **每个论断可追溯。** 凡涉及系统行为的陈述，要么给出代码位置（文件路径 + 函数名），
   要么明确标注为推论（「推论：…」）。读者必须能区分事实与推论。
2. **先讲问题，再讲方案。** 任何机制出场前，读者应当已经知道不这么做会怎样。
3. **代价与收益成对出现。** 只讲收益的段落是宣传稿，不是教材。
4. **每篇自足但不重复。** 交叉引用用链接，不复制正文；确实要重复的关键结论，
   用「回顾」明确标出。
5. **配图服务于理解，不是装饰。** 表格用于对比与枚举；流程图 / 时序图用于时序与依赖；
   结构图用于部件与边界。没有第四类图。

---

## 二、版本与称谓口径

全书涉及三个代码基线，称谓固定，不得混用：

| 称谓 | 指什么 | 代码位置（编写时用） |
|---|---|---|
| **上游 2026.09** | e2b-dev/infra 在 tag `2026.09` 的代码（commit `f8c2f0cde`） | `tmp/e2b-book-src/upstream/` |
| **ARM 适配版** | 在上游 2026.09 之上的 aarch64 移植补丁（infra-arm 的 commit `fbee6fcd1`，即 RPM 里的 `0001-adapted-for-arm-architecture.patch` 在本书截稿时的主体），加上分叉 Firecracker 的 ARM 修复、fc-kernels 的 arm64 内核配置 | `tmp/e2b-book-src/arm/`、`tmp/e2b-book-src/kasandbox-arm/firecracker/`、`fc-kernels-arm/` |
| **单机离线版** | 把 ARM 适配版打成 RPM、在一台 openEuler/aarch64 服务器上离线部署的形态（`e2b-infra` 仓库） | `e2b-infra/`（spec、`e2b-deploy/`、`single-node-offline-deploy.md`、`deploy-docs/`） |

三条纪律：

1. **未特别说明处，全书讲的都是上游 2026.09。** ARM 适配版的差异集中在第十部分；
   上游各篇若某个机制在 ARM 上有变化，在该篇末尾加一个「**ARM 适配版的差异**」小节，
   两三句话 + 指向第十部分的链接，不展开。
2. 描述 ARM 改动时，**写「上游的假设在 aarch64 上不成立」，不写「上游的缺陷」**；
   同理，写「ARM 适配版为了 X 放弃了 Y」，不写「ARM 版本做得不对」。
   凡是明显的技术债（例如放宽的超时、注释掉的代码路径），如实指出并说明后果，语气中性。
3. **不用内部代号**：不写 M1 / M2 / v3、jll 分支、某某同事。不写「我们决定」「后来改成」
   这类过程叙事，除非那个过程本身是要讲的知识点。

与 checkpoint / restore 手册的关系：本书**不重复**那本手册的内容。第 87 篇给概览与指引；
其它地方需要提到时，链接到 `../../e2b-infra-docs/rollback/docs/<file>.md`。

### 关于代码的引用位置

- 上游代码：写成 `packages/orchestrator/internal/sandbox/sandbox.go` 这样的仓库相对路径，
  必要时加函数名：`sandbox.go` 的 `ResumeSandbox()`。**不写绝对路径，不写行号**
  （行号随版本漂移；函数名不会）。
- ARM 适配版的改动：同样用仓库相对路径，并说明「ARM 适配版在此处改为 …」。
- 分叉 Firecracker：`src/vmm/src/...`（相对于 firecracker 仓库根）。
- 单机离线版：`e2b-infra.spec`、`e2b-deploy/build.sh`、`e2b-deploy/dep/<file>`。
- 引用代码片段只截取说明问题的部分；超过 30 行改用文字描述 + 位置指引。
  片段中允许省略号 `…` 与删减，但不得改写语义。

---

## 三、术语表（固定译法）

正文中文；标识符、文件名、命令、路径保持英文原样。下表中的术语按表中写法使用，
第一次出现时给出英文（括号内），之后可只用中文或只用英文，但**同一篇内保持一致**。

| 中文 | 英文 | 备注 |
|---|---|---|
| 沙箱 | sandbox | 一台运行中的 microVM 及其宿主侧资源 |
| 模板 | template | 沙箱的「镜像」；一个模板有多次构建 |
| 构建 | build | 模板的一次具体产物，由 build ID（UUID）标识 |
| 快照 | snapshot | 通用概念；e2b 里 pause 产生的也是一个 build |
| 暂停 / 恢复 | pause / resume | e2b 的原生快照与从快照拉起 |
| 编排器 | orchestrator | 首次出现后一律用英文 `orchestrator` |
| 模板管理器 | template-manager | 同上，用英文 |
| 边缘代理 | client-proxy（edge） | 两个名字指同一进程，首次出现时说明 |
| envd | envd | 沙箱内守护进程，不翻译 |
| 节点 | node | 运行 orchestrator 的宿主机 |
| 集群 | cluster | 一组节点 + 一组 edge |
| 团队 | team | 租户单位 |
| 档位 | tier | 团队的资源配额等级 |
| 内存文件 | memfile | 快照中的 guest 内存产物 |
| 根文件系统 | rootfs | 快照中的磁盘产物 |
| 映射表 | header | `memfile.header` / `rootfs.ext4.header`，记录块到某一代 diff 的映射 |
| 差分 | diff | 只含改动块的产物 |
| 块 | block | header 里的映射单位 |
| 分片 | chunk | 从对象存储按范围拉取的单位 |
| 层 | layer | 模板构建中的缓存单位 |
| 网络槽位 | slot | 一套预分配的 netns / IP / tap 等 |
| 大页 | huge pages | 2 MiB HugeTLB |
| 缺页 | page fault | |
| 写保护 | write protect（WP） | userfaultfd 语境 |
| 预取 | prefetch | |
| 写时复制 | copy-on-write（COW） | |
| 对象存储 | object storage | GCS / S3 / MinIO 统称 |
| 特性开关 | feature flag | LaunchDarkly 驱动 |

**不翻译**的专有名词：Firecracker、KVM、userfaultfd、NBD、overlay、netns、veth、tap、
Nomad、Consul、Terraform、Packer、Helm、Kubernetes、gRPC、Connect-RPC、OpenAPI、
OpenTelemetry、Loki、ClickHouse、Redis、PostgreSQL、MinIO、Harbor、systemd、busybox、
openEuler、鲲鹏（Kunpeng）。

---

## 四、体例

### 4.1 每篇的固定结构

```
# NN · 标题

> 一到三句话说明本篇讲什么、为什么值得读。
>
> **读者**：… 　**预备**：第 N 篇 … 　**代码**：`path/a.go`、`path/b.go`

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
- 上游各篇末尾如有 ARM 差异，小节名固定为「## N. ARM 适配版的差异」（放在小结之前）。

### 4.2 篇幅

正文 **3000–5000 汉字**（不含代码块与表格）。少于 2500 或多于 6500 要重新审视范围。
一篇讲不完就在 OUTLINE 里拆篇，不硬塞。

### 4.3 语言

- 一句话一个意思。段落不超过 6 行。
- 用「它」指代系统部件，不拟人化到「它认为」「它希望」。
- 不用「显然」「众所周知」；需要读者相信的地方给证据。
- 不用感叹号。不用 emoji。
- 数字与单位之间留空格（`512 MiB`、`20 ms`）；容量统一 MiB / GiB；时间统一 ms（μs 只用于 Firecracker 内部分段）。
- 任何性能数字必须紧跟测量条件（机型、内核、存储后端、模板大小、并发度）。

### 4.4 图

- 新画的图一律用内嵌 mermaid（GitHub、VS Code 直接渲染；后来者可修改）。
  可用类型：`flowchart`、`sequenceDiagram`、`stateDiagram-v2`、`classDiagram`（少用）。
- mermaid 节点文字中**不要**出现未转义的括号、引号、`|`、`{}`；标签里的中文与英文之间加空格。
  节点标签统一用方括号 `A[文字]` 或双引号 `A["文字 (带括号)"]`。
- 目录结构、文件布局、字节布局用 ASCII 代码块（```text），不用 mermaid。
- 每篇建议 1–3 张图；一张图不超过 20 个节点。
- 尺寸、重叠、各类图的具体画法与检查工具见 [FIGURE-GUIDE.md](FIGURE-GUIDE.md)；以 `tools/figcheck.sh` 的 PASS 为准。

### 4.5 表格

- 对比表第一列是对比维度，后续列是被比较的对象。
- 枚举表（接口、字段、配置项）保持列数 ≤ 5，长说明进正文。

### 4.6 交叉引用

- 引用别的篇目一律写显式链接：`[第 27 篇 · ResumeSandbox](27-resume-sandbox.md)`，
  引用到小节时加锚点：`[第 31 篇 §3](31-uffd-memory-backend.md#3-缺页处理)`。
- 锚点用 GitHub 规则：全小写、去标点、空格转连字符、中文保留；
  「## 3. 缺页处理」的锚点是 `#3-缺页处理`；「### 3.2 写保护」的锚点是 `#32-写保护`。
- 不写「见上文」「如前所述」。
- 只链接到 OUTLINE 里存在的文件名。目标篇还没写时只链到文件，不加锚点。

### 4.7 代码与命令

- 行内代码：函数名、字段名、文件名、环境变量、路径、命令。
- 代码块标注语言（```go、```bash、```yaml、```text、```mermaid）。
- 命令示例给完整可运行的形式，不写 `$` 提示符。

---

## 五、编写者自检清单

提交前逐条确认：

- [ ] 标题、题注、「0. 本篇要回答的问题」、「小结」、「延伸阅读 / 下一篇」齐全
- [ ] 正文 3000–5000 汉字
- [ ] 每个行为论断都能对应到代码位置或标注了「推论」
- [ ] 代码路径都是仓库相对路径，函数名与代码一致（读过代码，不是凭印象）
- [ ] 术语与第三节一致；版本称谓与第二节一致
- [ ] mermaid 代码块语法合法（用 `tools/mdmermaid.mjs` 检查），节点标签无未转义字符
- [ ] 每张图在 `tools/figcheck.sh` 下 PASS（见 FIGURE-GUIDE.md）
- [ ] 所有交叉链接指向 OUTLINE 中存在的文件名（用 `tools/mdlinks.py` 检查）
- [ ] 没有内部代号、没有过程叙事、没有「我们决定」
- [ ] 上游篇目末尾的 ARM 差异小节（若该机制在 ARM 上有变化）
- [ ] 「本篇要回答的问题」里的每个问题，正文都有明确的回答
