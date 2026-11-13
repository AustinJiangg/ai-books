# 27 · 配置体系与环境变量全参考

> 本章提供 DeepInfer 推理框架中全部核心配置参数（`EngineArgs`）、运行时环境变量（`DEEPINFER_*`）与调试探针开关的权威速查手册。
> **前置知识**：无。本章为查阅型参考工具。
> **源码指引**：`deepinfer/environ.py`、`deepinfer/engine/arg_utils.py`、`deepinfer/config.py`。

---

## 1. 核心环境变量分类全索引（`DEEPINFER_*`）

DeepInfer 内部采用基于描述符的类型化环境变量解析系统（`deepinfer/environ.py` 中的 `EnvVar`），在模块首次被访问时执行惰性加载与线程安全缓存。

### 1.1 硬件加速器与通信控制

| 环境变量名 | 类型 | 默认值 | 作用与配置说明 |
|---|---|---|---|
| `DEEPINFER_ACCELERATOR` | string | `"nvidia"` | 目标加速器平台类型，可选 `"nvidia"` 或 `"ascend"`。决定算子后端与依赖库加载。 |
| `DEEPINFER_NCCL_NUM_SMS` | int | `32` | 限制 NCCL / DeepEP 集合通信 Kernel 能够占用的最大 SM 核心配额，为计算预留资源。 |
| `DEEPINFER_USERBUFFER_COMM_SMS` | int | `None` | 显式覆写 UserBuffer 内部通信使用的 SM 数量。 |
| `DEEPINFER_GLOO_TIMEOUT` | float | `14400.0` | Gloo 控制面通信超时时间（秒），默认 4 小时。 |
| `DEEPINFER_REARRANGE_P2P_GROUPS` | int | `1` | EPLB 权重重排时的 P2P 并发通道数。 |

---

### 1.2 调度器与异步流水线（ZOS）

| 环境变量名 | 类型 | 默认值 | 作用与配置说明 |
|---|---|---|---|
| `DEEPINFER_ZERO_OVERHEAD_SCHEDULING` | bool | `True` | 是否启用 ZOS 零开销异步批调度器，实现 CPU 调度与 GPU 前向的完全流水线重叠。 |
| `DEEPINFER_PREFILL_ATTEMPT_INTERVAL` | int | `70` | NORMAL 引擎下，尝试触发 Prefill 的全员 `ALL` 判定周期步数（每 N 个 Decode Step）。 |
| `DEEPINFER_PREFILL_ANY_ATTEMPT_INTERVAL`| int | `100`| NORMAL 引擎下，任一 Rank 想做即触发的兜底 `ANY` 判定周期步数。 |
| `DEEPINFER_PREFILL_MAX_SUM_SEQLEN_K` | int | `2**30` | Prefill 单批次中累加的最大上下文总 Token 长度阈值，防止单步打满计算队列。 |
| `DEEPINFER_REARRANGE_AFTER_PREFILL_IN_NORMAL_ENGINE` | bool | `False` | 是否在 NORMAL 引擎刚完成 Prefill 阶段后立即触发一次 EPLB 专家负载重新排布。 |

---

### 1.3 模型架构创新（YOCO、SWA 与 Engram）

| 环境变量名 | 类型 | 默认值 | 作用与配置说明 |
|---|---|---|---|
| `DEEPINFER_YOCO_PREFILL_TRUNCATION_MODE` | choice | `"off"` | YOCO 预填充截断模式，可选 `"off"`、`"mask"`、`"compact"`。生产推荐 `"compact"`。 |
| `DEEPINFER_YOCO_PREFILL_KEEP_TOKENS` | int | `140` | YOCO 紧凑模式下消费层保留的尾部 Token 数（128 SWA 窗口 + 12 个回滚缓冲）。 |
| `DEEPINFER_INDEX_ATTN_MEMORY_LIMIT` | int | `10GB` | 稀疏索引注意力（Index Attention）允许占用的最大显存上限（字节）。 |
| `DEEPINFER_ENGRAM_PAD_TOKEN` | int | `2` | Engram 压缩词表中专门用于填充 Padding 的保留 Token ID。 |
| `DEEPINFER_ENGRAM_FORCE_GPU_STORAGE` | bool | 平台联动 | 是否强制将全部分片 Engram 嵌入表常驻显存（昇腾平台默认强制开启）。 |

---

### 1.4 推测解码与确定性采样

| 环境变量名 | 类型 | 默认值 | 作用与配置说明 |
|---|---|---|---|
| `DEEPINFER_USE_NEXTN_DECODE` | int | `5` | DFlash / MTP 推测解码单步预测的 Draft Token 最大数量。设为 0 时关闭推测。 |
| `DEEPINFER_ENABLE_MTP_VARLEN` | bool | `False` | 是否启用 DSpark 基于置信度的自适应变长推测验证。生产建议开启以提升吞吐。 |
| `DEEPINFER_MAX_BACKTRACKING_TOKENS` | int | `Auto` | 推测验证失败时允许的最大回滚步数，自动对齐为 `USE_NEXTN_DECODE + 1`。 |
| `DEEPINFER_BATCH_INVARIANT` | bool | `False` | 启用批次无关前向推理（仅限 NVIDIA），消除浮点非结合律导致的并发输出漂移。 |
| `DEEPINFER_SAMPLER_FORCE_TOPK` | int | `None` | 全局强制覆盖采样的 Top-K 参数（用于特定基准压测）。 |
| `DEEPINFER_DECODE_TOKEN_BLACKLIST` | string | `""` | 解码黑名单 Token ID 列表（以逗号分隔），在采样时被强行屏蔽。 |

---

### 1.5 CUDA Graph 与运行时优化

| 环境变量名 | 类型 | 默认值 | 作用与配置说明 |
|---|---|---|---|
| `DEEPINFER_ENFORCE_EAGER` | bool | `False` | 强制全流程在 Eager 模式下运行，禁用任何 CUDA Graph 捕获（常用于排障调试）。 |
| `DEEPINFER_CUDAGRAPH_BATCH_SIZE_INTERVAL` | int | `8` | 主模型解码 CUDA Graph 捕获的分桶步长间隔。 |
| `DEEPINFER_DFLASH_ENFORCE_EAGER` | bool | `False` | 针对 DFlash 推测模块单独禁用 CUDA Graph。 |
| `DEEPINFER_DFLASH_CUDAGRAPH_BATCH_SIZE_INTERVAL` | int | `8` | DFlash 模块的批处理分桶步长间隔。 |
| `DEEPINFER_DECODE_PERF_CACHE_DIR` | string | `None` | 各分桶静态图性能测速缓存持久化目录。 |
| `DEEPINFER_DISABLE_SYNC_GUARD` | bool | `False` | 关闭热路径非法同步屏障拦截检查（生产环境中严禁开启此项）。 |

---

### 1.6 显存管理、状态缓存与多模态

| 环境变量名 | 类型 | 默认值 | 作用与配置说明 |
|---|---|---|---|
| `DEEPINFER_NUM_STATE_SLOTS_RATIO` | float | `1.2` | SWA 状态缓存槽位数相对于最大并发序列数 `max_num_seqs` 的预留倍率。 |
| `DEEPINFER_PREFILL_STORE_EXTRA_STATE`| bool | `False`| 是否在 Prefill 结束时额外保留超出 128 边界的微小尾巴状态。 |
| `DEEPINFER_PREFILL_STORE_EXTRA_SIZE` | int | `128` | 额外状态存储缓冲区尺寸。 |
| `DEEPINFER_USE_MULTIMODAL_POOL` | bool | `False` | 是否为视觉高分辨率图文特征启用独立的预分配内存池。 |
| `DEEPINFER_MULTIMODAL_POOL_SIZE_GB` | int | `8` | 独立多模态特征缓冲池的静态显存容量（GB）。 |

---

### 1.7 结构化输出（xgrammar）控制

| 环境变量名 | 类型 | 默认值 | 作用与配置说明 |
|---|---|---|---|
| `DEEPINFER_SO_BUILDER_CPUS` | int | `4` | 专职用于编译 JSON Schema / EBNF 语法自动机的后台并发 CPU 核心数。 |
| `DEEPINFER_XGRAMMAR_CACHE_LIMIT_BYTES`| int | `10GB` | 全局文法编译结果 LRU 缓存的内存容量上限。 |
| `DEEPINFER_XGRAMMAR_TIMEOUT` | int | `20` | 单次文法编译的最大超时限制（秒）。 |
| `DEEPINFER_XGRAMMAR_DEBUG` | bool | `False` | 打印结构化输出自动机的逐步状态转移与 Bitmask 生成调试日志。 |

---

### 1.8 EPLB 负载均衡与监控

| 环境变量名 | 类型 | 默认值 | 作用与配置说明 |
|---|---|---|---|
| `DEEPINFER_OVERRIDE_NUM_EXTRA_EXPERTS` | int | `None` | 手动强制指定每张 GPU 上挂载的冗余物理专家副本数量。 |
| `DEEPINFER_EXPERT_COUNT_WINDOW_SIZE` | int | `100` | 统计专家历史负载的滑动窗口步数（Steps）。 |
| `DEEPINFER_EXPERT_REARRANGEMENT_STEP_INTERVAL` | int | `1000` | 重新触发贪心装箱求解与跨卡权重热搬迁的步数周期。 |
| `DEEPINFER_MOE_LB_STAT_INTERVAL` | int | `128` | 计算并打印当前集群 `moe_lb` 失衡比率的周期间隔。 |
| `DEEPINFER_SHOW_EPLB_DETAIL` | bool | `False` | 打印各层物理专家在各 GPU Rank 上的实时重排分布明细。 |
| `DEEPINFER_PROFILE_HTTP_ENABLE` | bool | `False` | 开启内置的 HTTP 实时性能指标采集服务。 |
| `DEEPINFER_PROFILE_HTTP_PORT_BASE` | int | `6070` | 性能指标 HTTP 监听基准端口。 |

---

## 2. 核心命令行启动参数速查（`EngineArgs`）

通过 Python API 或 CLI 启动 `LLMEngine` 时支持的常用核心配置对象 `EngineArgs`：

```python
from deepinfer.engine.arg_utils import EngineArgs

args = EngineArgs(
    model="deepseek-ai/DeepSeek-V4.1-Flash-1017",
    engine_type=0,                  # 0: NORMAL, 1: PROMPT, 2: COMPLETION
    tensor_parallel_size=1,         # 张量并行度 (固定为 1)
    pipeline_parallel_size=1,       # 流水线并行度 (固定为 1)
    max_num_seqs=256,               # 最大并发解码序列数
    max_num_batched_tokens=32768,   # 单步批次允许的最大总 Token 预算
    gpu_memory_utilization=0.90,    # 显存安全预算利用率 (默认 90%)
    block_size=128,                 # Paged KV 物理块尺寸 (推荐 128)
    chunked_prefill=True,           # 启用分块预填充以平抑算力峰值
    trust_remote_code=True,         # 允许加载自定义架构权重
)
```

---

## 3. 生产环境推荐配置模板

针对 8 卡标准 GPU 生产节点（如 8x SM100），推荐的标准环境导出行如下：

```bash
# 平台与通信优化
export DEEPINFER_ACCELERATOR=nvidia
export DEEPINFER_NCCL_NUM_SMS=32

# 调度与流水线加速
export DEEPINFER_ZERO_OVERHEAD_SCHEDULING=1
export DEEPINFER_PREFILL_ATTEMPT_INTERVAL=70
export DEEPINFER_PREFILL_ANY_ATTEMPT_INTERVAL=100

# 模型与算法极致截断
export DEEPINFER_YOCO_PREFILL_TRUNCATION_MODE=compact
export DEEPINFER_YOCO_PREFILL_KEEP_TOKENS=140

# DSpark 动态推测验证
export DEEPINFER_USE_NEXTN_DECODE=5
export DEEPINFER_ENABLE_MTP_VARLEN=1

# 结构化输出与 CUDA Graph
export DEEPINFER_SO_BUILDER_CPUS=4
export DEEPINFER_CUDAGRAPH_BATCH_SIZE_INTERVAL=8

# EPLB 负载均衡自适应
export DEEPINFER_EXPERT_COUNT_WINDOW_SIZE=100
export DEEPINFER_EXPERT_REARRANGEMENT_STEP_INTERVAL=1000
```
