# 审校备忘（编写者交付说明中给其它篇目的建议，审校时逐条处理）

规划阶段调研中已发现、需要多篇口径一致的事项（编写开始后，编写者交付说明里的建议追加在本文件末尾）：

- 全书：AENV 补丁版 Firecracker 的四个被用到的补丁行为（可选 `mem_file_path`、`dirty-memory-ranges`、seek 取内存文件大小、drive `direct`）在 03 / 27 / 42 / 67 四篇的说法必须一致；未被使用的两个补丁（pmem seek、`guest-memory-regions`）只在 67 出现。
- 全书：「Rust 版 overlaybd 与上游格式兼容」只对 LSMT / ZFile / tar 包裹成立；Hybrid RW、`PMIDX001`、`OBCH`、`AENVMF01` 是扩展；05 / 34 / 35 / 39 / 73 口径一致。
- 26 ↔ 41：两级 refcount 与 `cache_fd` 的讲法统一；26 讲节点侧，41 讲 daemon 侧。
- 27 ↔ 42：27 只讲 FC 调用顺序，42 讲数据成层与共享设备；`moffset = HVA` 只在 42 详讲。
- 42：File 后端 MAP_PRIVATE 与「resumed VM 的脏页 = COW 过的页」在 AgentENV 仓库里没有代码依据，要到 fc-aenv 的 `vstate/memory.rs` 核实，否则标推论。
- 43 ↔ 49：startup pack 录制与消费在 43；制品与 attach 在 49；「v2 / v3 / v4 startup manifest」与魔数 `AENVMF01` 的称呼统一，混用问题写进 68。
- 13 ↔ 17 ↔ 55：数据面鉴权只在 13 详讲；17 与 55 引用。gateway 不验数据面凭据。
- 14 / 23：resume 缺省 TTL（`default_sandbox_timeout_secs` = 15 s）与 v2 create / connect 的 300 s、auto-resume 最小 300 s 并存，三篇说法一致。
- 22 ↔ 57：关闭时先 `UnregisterNode` 再 pause 落盘，造成重启前的 404 窗口；两篇口径一致。
- 47 ↔ 48：一致性对比表只放在 48 末尾；47 只讲 POSIX。managed-layers 无 GC 在 47、48、68 三处说法一致。
- 52 ↔ 53：从 ENTRYPOINT / CMD 推导 start_cmd 在步骤路径禁用、BuildKit 路径仍用 —— 两篇都要提，68 汇总。
- 56：「Schedule 不排除 UNHEALTHY 节点」与测试 `TestScheduleOnlyConsidersReadyNodes` 名不副实，要读 `node_registry.go::Snapshot()` 核实后再写。
- 61：firecracker-next 是否实现 `dirty-memory-ranges` 无法从本书基线确认，只能写推论。
- 文档漂移（68 汇总）：`docs/src/internals/networking.md` 的 host interaction「/31 per slot」、`sandbox-testing.md` 的 `[firecracker]` 写法、`template-builder-testing.md` 的记录路径与方法名、`p2p-design.md` 的 `fetch_byte_range` 返回类型、`services/README.md` 的 hostPath 与漏列的 RPC、`CLAUDE.md` 的三个失效链接。
