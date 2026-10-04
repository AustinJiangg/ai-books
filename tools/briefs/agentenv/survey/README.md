# 规划阶段的代码调研笔记

写 OUTLINE 之前，按五个区域各做了一轮源码调研（AgentENV v0.2.3 / 6cccaa7，AENV 补丁版 Firecracker aenv-deps / 90288c39）。
这些笔记是**编写的起点，不是依据**：调研者读过代码，但没有逐条复核；标【推断】【需核实】【未验证】的更要自己确认。
笔记里的行号随版本漂移，正文里不要照抄；正文按 STYLE.md 只写路径 + 函数名。

| 文件 | 区域 | 主要对应篇目 |
|---|---|---|
| [`A-api.md`](A-api.md) | API 层、认证、反向代理、E2B 兼容、custom extension、aenv CLI | 12–18、33、62 |
| [`B-runtime.md`](B-runtime.md) | orchestrator、沙箱运行时、网络、配置、宿主准备 | 09–11、19–33、59、61 |
| [`C-storage.md`](C-storage.md) | Rust 版 overlaybd、ublk、ublk-daemon、内存快照、startup pack、uffd-core | 04、05、34–44、73 |
| [`D-snapshot.md`](D-snapshot.md) | 镜像转换、快照仓库、resolve、rootfs 导出、fork、模板、BuildKit、P2P | 45–53、58 |
| [`E-controlplane-deploy-fc.md`](E-controlplane-deploy-fc.md) | gateway、scheduler、心跳、部署、测试、发布、Firecracker 补丁层、仓库全貌 | 01、54–57、59–64、67 |

每份笔记的「意外发现 / 技术债」一节是第 68 篇的素材；「章节拆分建议」一节已经被 OUTLINE 吸收。
