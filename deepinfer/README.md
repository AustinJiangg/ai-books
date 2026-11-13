# DeepInfer 技术手册

一本关于 **DeepInfer**（[deepseek-ai/DeepInfer](https://github.com/deepseek-ai/DeepInfer)，代码基线为 commit `9bd9cf2`）的教材式技术手册，深入剖析支撑 DeepSeek 大规模线上推理服务（如 DeepSeek-V4.1-Flash）的核心框架架构与底层实现。

DeepInfer 是为大模型超大规模云端生产环境研发的高吞吐、低时延推理引擎。在单一生产集群中，它支撑了日均 **155 万亿 Token** 的服务规模，在低谷电价下创造了每 GPU 卡时 38 美元的商业价值。

为了突破传统推理引擎在超长上下文与超大模型规模下的「访存墙」、「通信墙」与「CPU 发射气泡」，DeepInfer 提出并实现了一系列软硬件协同突破：
- **模型架构创新**：支持 You Only Cache Once（YOCO / CED）单次缓存架构、SWA 128-token 常数有界重放、Multi-Head Hyper-Connections（MHC）多通道残差扩展与 Engram N-gram 局部增强；
- **计算与精度极致优化**：全面落地 MXFP8 与 MXFP4 极低精度计算，深度整合 FlashMLA、DeepGEMM、DeepSelect 与定制 TileLang 融合算子；
- **零开销异步调度（ZOS）**：彻底解耦 CPU 批调度与 GPU 前向执行，通过固定内存 Remap 向量与设备端就地修正，抹平全部 Host-Device 同步开销；
- **大规模专家并行负载均衡（EPLB）**：针对 Decode 阶段引入 Wide-EP（EP64–128），通过动态冗余专家副本与 NVLink 对称内存（`symm_mem`）实现微秒级零拷贝专家权重热排布；
- **生产级推测与解耦体系**：集成 DSpark / DFlash MTP 动态置信度推测解码、结构化输出自动机、Vision Encoder 独立单卡路由，以及与 3FS 分布式 KV 存储（10+2 EC、72 小时持久化）的深度整合。

未特别说明处，全书讲的都是 **DeepInfer 官方开源主分支基线**。版本称谓与术语规约见 [`STYLE.md`](STYLE.md)，配图规范见 [`FIGURE-GUIDE.md`](FIGURE-GUIDE.md)，全书规划详见 [`OUTLINE.md`](OUTLINE.md)。

---

## 怎么读

| 读者背景与关注点 | 建议精读路径 |
|---|---|
| **想先看全貌与技术架构** | **00 → 01 → 08 → 09** |
| **算法与模型架构研究员** | **02 → 03 → 04 → 05 → 06 → 16 → 17** |
| **推理系统与调度器核心研发** | **09 → 10 → 11 → 12 → 13 → 14** |
| **GPU 算子与高性能计算工程师** | **06 → 07 → 15 → 17 → 18 → 19** |
| **推测解码与高级功能开发者** | **11 → 20 → 21 → 22 → 23** |
| **多模态与分布式集群架构师** | **08 → 24 → 25 → 26** |
| **SRE 运维与性能排障工程师** | **01 → 07 → 26 → 27 → 28** |

---

## 目录

### 第〇部分　导读与工程全景

| # | 文档 | 内容要点 |
|---|---|---|
| 00 | [`00-overview.md`](00-overview.md) | 全书导读与 DeepInfer 总览：155 万亿 Token 日吞吐背后的工程体系 |
| 01 | [`01-repo-map-and-build.md`](01-repo-map-and-build.md) | 仓库地图、构建系统与 NVIDIA / Ascend 双平台环境准备 |

### 第一部分　核心架构与前沿创新

| # | 文档 | 内容要点 |
|---|---|---|
| 02 | [`02-yoco-architecture-and-compaction.md`](02-yoco-architecture-and-compaction.md) | YOCO 架构与前缀截断机制：Consumer 隐藏层共享与 Compact 内存重排 |
| 03 | [`03-swa-and-bounded-replay.md`](03-swa-and-bounded-replay.md) | SWA 滑动窗口与有界重放：128-token 常数重放与状态缓存设计 |
| 04 | [`04-mhc-multi-head-hyper-connections.md`](04-mhc-multi-head-hyper-connections.md) | Multi-Head Hyper-Connections (MHC)：多通道残差流扩张与融合 GEMM |
| 05 | [`05-engram-runtime.md`](05-engram-runtime.md) | Engram 运行时与压缩词表：多阶 N-gram 哈希、分片聚合与门控注入 |
| 06 | [`06-low-precision-fp4-mxfp8.md`](06-low-precision-fp4-mxfp8.md) | 极致低精度计算体系：Main KV MXFP8/FP4 与 MoE 权重打包机制 |

### 第二部分　异构硬件与并行运行时

| # | 文档 | 内容要点 |
|---|---|---|
| 07 | [`07-hardware-abstraction-and-topology.md`](07-hardware-abstraction-and-topology.md) | 异构加速器抽象与 NUMA 绑定：SM100 与 Ascend 950 硬件适配层 |
| 08 | [`08-parallelism-and-userbuffer.md`](08-parallelism-and-userbuffer.md) | 混合并行体系与 UserBuffer 零拷贝通信：DP/EP/CP 与对齐内存管理 |

### 第三部分　调度与引擎核心

| # | 文档 | 内容要点 |
|---|---|---|
| 09 | [`09-engine-architecture.md`](09-engine-architecture.md) | LLMEngine 架构与生命周期：Normal/Prompt/Completion 引擎驱动 |
| 10 | [`10-scheduler-core-and-step-voting.md`](10-scheduler-core-and-step-voting.md) | C++ 调度器核心与 SPMD 步型投票：ALL/ANY 投票规约与 LCFS 驱逐 |
| 11 | [`11-zos-zero-overhead-scheduler.md`](11-zos-zero-overhead-scheduler.md) | ZOS 零开销异步调度器：流水线异步重叠与 GPU 侧就地序列修正 |
| 12 | [`12-block-manager-and-prefix-caching.md`](12-block-manager-and-prefix-caching.md) | BlockManager 与分块 KV 缓存管理：双向链表、写时复制与前缀哈希树 |

### 第四部分　Worker 运行态与 CUDA Graph

| # | 文档 | 内容要点 |
|---|---|---|
| 13 | [`13-worker-pipeline-and-overlap.md`](13-worker-pipeline-and-overlap.md) | Worker 执行流水线与重叠机制：三段论执行模型与异步采样事件级联 |
| 14 | [`14-cuda-graph-runner.md`](14-cuda-graph-runner.md) | CUDA Graph 捕获与分级批处理执行：静态内存映射与多级 Batch 尺寸分桶 |
| 15 | [`15-memory-and-cache-engine.md`](15-memory-and-cache-engine.md) | CacheEngine 与显存-宿主内存层级管理：主显存、状态缓存与预热池 |

### 第五部分　模型骨干与算子实现

| # | 文档 | 内容要点 |
|---|---|---|
| 16 | [`16-deepseek-v4-model-architecture.md`](16-deepseek-v4-model-architecture.md) | DeepSeek-V4 网络结构全景解析：主干前向、跨层拓扑与残差连接 |
| 17 | [`17-mla-and-flashmla.md`](17-mla-and-flashmla.md) | Multi-Head Latent Attention (MLA) 与 FlashMLA 算子加速实现 |
| 18 | [`18-deepgemm-and-tilelang-kernels.md`](18-deepgemm-and-tilelang-kernels.md) | DeepGEMM 与 TileLang 自研算子库：JIT 编译特化与动态调度修正 |
| 19 | [`19-deepseek-moe-and-deepep.md`](19-deepseek-moe-and-deepep.md) | DeepSeek-MoE 与 DeepEP 通信库：细粒度专家路由与低时延 All-to-All |

### 第六部分　推测解码与高级特性

| # | 文档 | 内容要点 |
|---|---|---|
| 20 | [`20-dspark-speculative-decoding.md`](20-dspark-speculative-decoding.md) | DSpark / DFlash MTP 推测解码全流程：Draft 生成与主模型联合校验 |
| 21 | [`21-confidence-scheduled-verification.md`](21-confidence-scheduled-verification.md) | 动态置信度调度与自适应验证长度：边际收益排序与算力节约算法 |
| 22 | [`22-structured-outputs.md`](22-structured-outputs.md) | 结构化输出与 Grammar 匹配自动机：xgrammar 解耦编译与回滚掩码 |
| 23 | [`23-batch-invariant-and-deterministic-sampling.md`](23-batch-invariant-and-deterministic-sampling.md) | 批次无关推理与确定性采样：浮点不可换序消除与确定性采样器 |

### 第七部分　多模态与集群生产体系

| # | 文档 | 内容要点 |
|---|---|---|
| 24 | [`24-deepseek-vl-multimodal.md`](24-deepseek-vl-multimodal.md) | DeepSeek-VL 多模态视觉编码与动态路由：单卡 VE 独立解耦与动态 Patch |
| 25 | [`25-eplb-dynamic-load-balancing.md`](25-eplb-dynamic-load-balancing.md) | EPLB 专家并行负载均衡：多步贪心重排策略与 NVLink 零拷贝热换 |
| 26 | [`26-cluster-serving-and-3fs-kv-storage.md`](26-cluster-serving-and-3fs-kv-storage.md) | E/P/D 分离部署与 3FS 分布式 KV 存储：10+2 EC、GDR 交换与 72h 留存 |

### 第八部分　附录与工程参考

| # | 文档 | 内容要点 |
|---|---|---|
| 27 | [`27-configuration-and-env-reference.md`](27-configuration-and-env-reference.md) | 配置体系与环境变量全参考：EngineArgs 与 DEEPINFER_* 环境变量清单 |
| 28 | [`28-glossary-and-code-map.md`](28-glossary-and-code-map.md) | 术语表与源码速查地图：关键核心类、C++ 扩展接口与算子对照索引 |
