# 28 · 术语表与源码速查地图

> 本章汇编全书核心系统术语权威中英释义，并系统梳理 DeepInfer 源码树中各关键类、C++ 扩展接口与高性能算子的物理映射索引。
> **前置知识**：无。本章为全局速查工具。
> **源码指引**：全仓库核心文件。

---

## 1. 核心系统术语表（Glossary）

| 英文术语 | 中文标准译名 | 概念界定与工业语义 |
|---|---|---|
| **E/P/D Disaggregation** | E/P/D 解耦部署 | 将视觉编码（VE）、预填充（Prefill）与自回归解码（Decode）从物理硬件层面彻底分离部署的分布式云架构。 |
| **Wide-EP** | 宽专家并行 | 针对 Decode 阶段设计的超大专家并行拓扑（EP64~EP128），通过多卡分摊使每卡持有的专家数量降至极低，以突破访存带宽极限。 |
| **YOCO (You Only Cache Once)** | 单次缓存架构 | 仅在前半区编码层维护全局 KV 缓存，后半区消费层直接共享跨层隐状态（`shared_hidden`）的非同构网络架构。 |
| **SWA (Sliding Window Attention)** | 滑动窗口注意力 | 将局部注意力跨度严格限制在最近固定窗口（如 128 Token）内的计算模式，显存与计算随长度解耦。 |
| **Bounded Replay** | 有界重放 | 在局部缓存缺失时，仅向后回退常数阶（128 Token）进行局部注意力近似重构的机制，时间复杂度严格为 $O(1)$。 |
| **MHC (Multi-Head Hyper-Connections)** | 多头超连接 | 将单一残差流扩展为 $M$ 个并行通道，并在层间通过可学习矩阵动态混合的残差结构。 |
| **Engram** | 记忆印迹 / 嵌入增强 | 将高频固定的局部短语与语法模式外置为全局多阶 N-gram 稀疏哈希检索表的架构。 |
| **ZOS (Zero-Overhead Scheduling)** | 零开销异步调度 | CPU 调度规划与 GPU 前向计算完全无同步重叠执行，通过 Pinned Remap 与设备端算子就地修正消除 Host 气泡的机制。 |
| **EPLB (Expert-Parallel Load Balancing)** | 专家并行负载均衡 | 通过为 GPU 分配冗余物理专家副本，并基于历史步峰值多维贪心求解，在 NVLink 上热搬迁参数消除落后节点的系统。 |
| **DSpark / MTP** | 多词元预测推测解码 | 联合训练的辅助预测头，单步同时预测未来 $K$ 个词元，并根据置信度动态调整验证长度的推测解码技术。 |
| **3FS** | 3FS 分布式存储 | 专为大模型 KV 缓存设计的超大规模分布式文件系统，采用 10+2 纠删码、并发读取消长尾并支持 72h+ 留存。 |
| **GDR (GPUDirect RDMA)** | GPU 直通远程内存访问 | 网卡直接跨 PCIe 总线读写 GPU 显存的技术，完全绕过主机 CPU 与系统内存的中转。 |
| **Sync Guard** | 同步守卫 | 在推理执行热路径中拦截非法 `cudaStreamSynchronize` 或隐式同步调用的静态与动态断言检查机制。 |

---

## 2. 核心架构源码速查地图（Code Map）

### 2.1 C++ 核心引擎与扩展接口（`csrc/`）

| 核心文件路径 | 核心结构体 / 类 / 函数 | 职责与设计要点 |
|---|---|---|
| `csrc/engine/scheduler.hpp` | `Scheduler` | 纯 C++ 批调度器；实现 `_schedule_prefill`、`_schedule_decode`、ALL/ANY 双阈值 SPMD 投票与 LCFS 驱逐。 |
| `csrc/engine/scheduler.hpp` | `SchedulerOutputs` | 调度产物载体；封装调度出的序列列表、`seqlens_q` 预算、MTP 耗时估计。 |
| `csrc/engine/block_manager.hpp` | `BlockManager` / `Blocks` | 物理显存块与状态槽位管理器；基于侵入式双向链表管理自由块，保留块 0 作为安全占位黑洞。 |
| `csrc/engine/sequence.hpp` | `Sequence` / `SequenceMetadata` | 序列全生命周期状态机；维护 Token 序列、分支 ID、缓存映射表与调度状态。 |
| `csrc/engine/zos.cpp` | `prepare_zos_inputs` / `prepare_decode_zos_inputs` | ZOS 核心映射生成器；构建 `remap_cpu` 向量并打包 `fresh_input_ids`。 |
| `csrc/engine/mtp_varlen.hpp` | `SamplerRuntimeEstimator` / `ForwardRuntimeEstimator` | 滑动窗口中位数估时模型；动态跟踪 GPU 前向与采样实测耗时，指导变长验证预算。 |
| `csrc/utils/object_pool.hpp` | `ObjectPoolPyObject` | 无锁静态对象池；消除频繁创建销毁 Python/C++ 包装对象的垃圾回收开销。 |
| `csrc/cuda_utils.cpp` | `hook_cuda_stream_synchronize` | 同步守护拦截器；保障热路径绝对零阻塞。 |

---

### 2.2 Python 核心主控与运行时（`deepinfer/`）

| 核心文件路径 | 核心类 / 模块 | 职责与设计要点 |
|---|---|---|
| `deepinfer/engine/llm_engine.py` | `LLMEngine` | 主控大脑；主循环驱动、请求生命周期管理、多进程 Worker 协同与统计输出。 |
| `deepinfer/worker/worker.py` | `Worker` | GPU 物理执行体；实现 `Forward` -> 延后 `PostProcess` -> `Sample` 的三段论执行流。 |
| `deepinfer/worker/cuda_graph_runner.py` | `CUDAGraphRunner` | 解码静态图运行器；分级分桶（Interval 8）捕获与重放，处理占位符槽位绑定。 |
| `deepinfer/worker/dflash_cuda_graph_runner.py` | `DFlashCUDAGraphRunner` | DFlash 推测模块专属静态图捕获运行器；与主模型图通过事件流无缝串联。 |
| `deepinfer/worker/cache_engine.py` | `CacheEngine` | 显存与宿主内存规划中心；启动期干跑压测确定最大可用块数并分配物理大张量。 |
| `deepinfer/platform.py` | `Platform` / `PLATFORM` | 异构硬件抽象单例；屏蔽 NVIDIA CUDA 与华为昇腾 CANN 的底层 API 分歧。 |
| `deepinfer/environ.py` | `envs` / `EnvVar` | 类型化环境变量描述符容器；统一配置解析与线程安全缓存。 |

---

### 2.3 模型拓扑与算法算子层（`deepinfer/model_executor/`）

| 核心文件路径 | 核心类 / 模块 | 职责与设计要点 |
|---|---|---|
| `models/deepseek.py` | `DeepseekModel` / `DeepseekForCausalLM` | 模型顶层骨干；集成 MLA、YOCO、MHC、MoE、Engram 与 MTP 全链路前向。 |
| `models/v4_modules/yoco.py` | `yoco_boundary_compact` / `yoco_enabled` | YOCO 紧凑截断算子；在边界层将消费层张量行数压缩为 140 行，算力减半。 |
| `models/v4_modules/mhc_modeling.py`| `mhc_pre_big_fuse` / `mhc_head` | 多头超连接大融合算子；单 Kernel 完成 Pre-Norm、Split-K GEMM 与混合。 |
| `models/v4_modules/engram.py` | `EngramRuntime` / `CompressedTokenizer` | 记忆印迹运行时；GPU 多阶 N-gram 哈希、分片嵌入跨卡拉取与门控融合。 |
| `models/v4_modules/moe.py` | `DeepseekMoE` | 细粒度专家路由实现；结合常驻共享专家与动态路由专家的 Mega MoE 融合计算。 |
| `eplb/policy.py` | `_batch_greedy_indices` | EPLB 核心调度算法；多历史步峰值最小化贪心背包求解，产出物理放置索引。 |
| `eplb/shuffle.py` | `expert_model_parallel_shuffle_inplace` | 专家权重热重排；基于 NVLink 对称内存实现微秒级零拷贝跨卡权重热搬运。 |
| `models/mtp/dflash.py` | `DFlash` | 多词元预测推测模块；原地抽头主模型深层特征，并行输出 5 个候选 Draft Token。 |
| `parallel_utils/userbuffer.py` | `_UserBufferManager` / `limit_num_sms` | 专用通信缓冲区预分配；动态限制通信 SM 配额，实现算网零冲突重叠。 |

---

### 2.4 底层算子与通信加速库（`vendor/` & `tilelang_ops/`）

| 算子库 / 模块路径 | 语言栈 | 解决的关键技术瓶颈 |
|---|---|---|
| `vendor/FlashMLA` | CUDA / SASS | 多头潜在注意力专用解码算子；利用矩阵吸收实现压缩潜变量直接计算，带宽利用率 > 85%。 |
| `vendor/DeepGEMM` | CUDA / C++ JIT | 动态非对齐 $M$ 维度特化矩阵乘库；原生硬件级支持 MXFP8 与 MXFP4（ue8m0）低精度点积。 |
| `vendor/DeepEP` | CUDA / IPC | 专为 Wide-EP 设计的超低延迟 MoE 通信库；NVLink 统一虚拟编址 P2P 直读直写，延迟 < 25 微秒。 |
| `vendor/DeepSelect` | CUDA / Warp Shuffle | 针对 256 个细粒度专家的高性能并行 Top-K 路由算子，耗时 < 30 微秒。 |
| `tilelang_ops/compute_seqlens_k_zos.py`| TileLang | ZOS 设备端长度就地修正算子；在 GPU 上利用上一步接受词元更新序列长度，消除 CPU 同步。 |
| `tilelang_ops/fused_sample.py` | TileLang | 全融合采样算子；在 SM 片上直接完成 Bitmask 过滤、Temperature 缩放与 Top-P 采样，免除全词表写回。 |
| `tilelang_ops/schedule_mtp_varlen.py` | TileLang | DSpark 变长验证动态求解算子；在 GPU 片上并行计算条件累乘并贪心截断。 |
| `structure_output/` | Python / C++ | 基于 xgrammar 的语法约束自动机；生成紧凑 Bitmask 并支持推测解码多步回滚。 |

---

## 3. 全书知识闭环结语

至此，《DeepInfer 技术手册》完成了从宏观系统拓扑、异构硬件底层、C++ 异步调度中枢、模型深度骨干、推测解码前沿，到分布式 100 PiB 存储基建的全景剖析。

DeepInfer 的成功向世界证明：**大语言模型的终极推理效率，绝非单纯依赖算力硬件的单点堆砌，而是来自于从算法数学建模、模型层级拓扑、分布式通信编排、存储介质分级到微指令算子融合的全局全栈协同演进！**
