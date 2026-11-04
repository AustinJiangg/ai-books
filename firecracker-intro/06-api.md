# 06. Firecracker 的 API：如何“遥控”一台虚拟机

> **《彻底搞懂 Firecracker》系列 · 第六篇**
>
> **读完本篇，你能理解：**
> - 为什么 Firecracker 用 “REST over Unix Socket” 作为控制接口
> - API 的全部资源、每个资源能用哪些 HTTP 方法
> - microVM 的状态机：哪些配置只能在开机前改，哪些可以在运行中改
> - API 请求在 Firecracker 内部是怎么被处理的
> - 怎么读懂错误信息，怎么配置日志和指标
> - 用 Python 写一个小型控制脚本
>
> **前置知识：** 第 05 篇。了解 HTTP 的基本概念（请求方法、状态码、JSON）。
>
> **版本：** Firecracker v1.17.0。

---

## 引子：遥控器上的按钮

第 05 篇我们用 `curl` 发了几个请求就造出了一台 microVM。如果把 Firecracker 比作一台电视机，API 就是遥控器。这一篇我们把遥控器上的每个按钮都认一遍，并搞清楚：

- 哪些按钮只能在“开机前”按（比如设置屏幕尺寸）；
- 哪些可以在“播放中”按（比如调音量）；
- 按下按钮后，电视机内部发生了什么。

---

## 一、为什么是 REST over Unix Socket

### 1.1 REST 是什么

**REST** 是一种设计 HTTP 接口的风格：把要操作的对象看成“资源”，每个资源有一个路径（URL），用 HTTP 方法表达动作：

| HTTP 方法 | 在 Firecracker 中的含义 |
|----------|----------------------|
| `GET` | 读取资源的当前状态 |
| `PUT` | 创建资源，或完整替换它的配置 |
| `PATCH` | 部分修改已有资源（通常用于运行中调整） |

比如 `PUT /drives/rootfs` 就是“创建（或替换）一个叫 rootfs 的磁盘”。

### 1.2 为什么走 Unix Socket

Firecracker 的 API 不监听任何网络端口，只在宿主机上创建一个 socket 文件。这样做有几个好处：

- **安全**：只有宿主机上能访问这个文件的进程才能控制 microVM，网络上的任何人都碰不到。配合文件权限和 jailer 的 chroot（第 14 篇），可以精确控制谁有权限；
- **不占用端口**：一台宿主机跑几千台 microVM，每台都要一个 API 端点，用 TCP 端口很快就会冲突或耗尽；
- **简单**：HTTP 协议工具链成熟，`curl`、各种语言的 HTTP 库都能直接用。

### 1.3 规范文件

API 的完整定义写在一份 OpenAPI（Swagger）规范里：源码中的 `src/firecracker/swagger/firecracker.yaml`，发布包里也附带了一份 `firecracker_spec-vX.Y.Z.yaml`。所有资源、字段、类型、必填项都以它为准。

你可以用任何 Swagger 工具打开它浏览，也可以用它自动生成各种语言的客户端代码。官方的 Go SDK（`firecracker-go-sdk`）就是这样生成的。

---

## 二、microVM 的状态机

理解 API 的关键是理解 microVM 的生命周期：

```
                    PUT /actions {InstanceStart}
   ┌─────────────┐  或 PUT /snapshot/load          ┌──────────┐
   │ Not started │ ──────────────────────────────▶ │ Running  │
   │  （开机前）   │                                  └────┬─────┘
   └─────────────┘                                 PATCH /vm │ ▲ PATCH /vm
         ▲                                     {Paused}  │ │ {Resumed}
         │                                               ▼ │
     启动进程                                         ┌──────────┐
                                                    │  Paused  │
                                                    └──────────┘
   Guest 执行 reboot / 内核 panic / 进程被杀  ──▶  进程退出（没有“Stopped”状态）
```

- **Not started（未启动）**：Firecracker 进程刚启动，等待配置。几乎所有“造机器”的配置都只能在这个阶段做；
- **Running（运行中）**：Guest 正在运行。只能做少量调整（限速、换磁盘文件、调气球大小等）；
- **Paused（已暂停）**：所有 vCPU 和设备都停止工作，这是创建快照的前提（第 15 篇）。

可以随时用 `GET /` 查看当前状态：

```bash
sudo curl -s --unix-socket /tmp/firecracker.socket http://localhost/ | jq
```

```json
{
  "id": "anonymous-instance",
  "state": "Not started",
  "vmm_version": "1.17.0",
  "app_name": "Firecracker"
}
```

---

## 三、资源全景图

下表列出 v1.17.0 的全部 API 资源。“开机前”指 Not started 状态，“运行中”指 Running/Paused 状态。

### 3.1 机器与启动

| 资源 | 方法 | 时机 | 作用 |
|------|------|------|------|
| `/machine-config` | PUT / PATCH | 开机前 | vCPU 数、内存大小、大页、脏页跟踪、CPU 模板 |
| `/machine-config` | GET | 任意 | 查看当前机器配置 |
| `/cpu-config` | PUT | 开机前 | 自定义 CPU 模板（第 16 篇） |
| `/boot-source` | PUT | 开机前 | 内核路径、启动参数、initrd |
| `/actions` | PUT | 见下 | `InstanceStart`（开机）、`FlushMetrics`（立刻刷新指标）、`SendCtrlAltDel`（发送 Ctrl+Alt+Del，v1.17 中仅 x86_64 支持；ARM64 支持已合入主线，将在后续版本提供） |
| `/vm` | PATCH | 运行中 | 暂停 / 恢复 |
| `/vm/config` | GET | 任意 | 导出完整配置（格式与 `--config-file` 一致） |

### 3.2 设备

| 资源 | 方法 | 时机 | 作用 |
|------|------|------|------|
| `/drives/{drive_id}` | PUT | 开机前 | 添加 virtio-block 磁盘 |
| `/drives/{drive_id}` | PATCH | 运行中 | 更换后端文件（`path_on_host`）、修改限速器 |
| `/network-interfaces/{iface_id}` | PUT | 开机前 | 添加 virtio-net 网卡 |
| `/network-interfaces/{iface_id}` | PATCH | 运行中 | 修改收发限速器 |
| `/vsock` | PUT | 开机前 | 添加 vsock 设备（第 11 篇） |
| `/entropy` | PUT | 开机前 | 添加 virtio-rng 熵源 |
| `/pmem/{id}` | PUT / PATCH | 开机前 / 运行中 | 持久内存设备 |
| `/balloon` | PUT / PATCH / GET | 开机前创建，运行中调整 | 内存气球（第 9 篇） |
| `/balloon/statistics` | GET / PATCH | 运行中 | 读取 Guest 内存统计 / 修改轮询间隔 |
| `/balloon/hinting/*` | PATCH / GET | 运行中 | 空闲页提示（v1.14 起） |
| `/hotplug/memory` | PUT / PATCH / GET | 开机前配置，运行中调整 | virtio-mem 内存热插拔（v1.14 起） |
| `/serial` | PUT | 开机前 | 把串口输出重定向到文件（v1.14 起） |

### 3.3 元数据、快照、可观测性

| 资源 | 方法 | 时机 | 作用 |
|------|------|------|------|
| `/mmds/config` | PUT | 开机前 | 配置 MMDS 版本、IP、允许访问的网卡（第 11 篇） |
| `/mmds` | PUT / PATCH / GET | 任意 | 写入、更新、读取元数据 |
| `/snapshot/create` | PUT | 已暂停 | 创建快照（第 15 篇） |
| `/snapshot/load` | PUT | 开机前（空进程） | 从快照恢复 |
| `/logger` | PUT | 开机前 | 日志输出位置与级别 |
| `/metrics` | PUT | 开机前 | 指标输出位置 |
| `/version` | GET | 任意 | Firecracker 版本 |

> 💡 **小规律：** 大部分 `PUT` 是“造机器”，只能在开机前用；大部分 `PATCH` 是“调参数”，用于运行中。这符合 Firecracker 的极简理念：microVM 开机后，它的硬件构成基本就固定了。

---

## 四、几个重要资源的字段

### 4.1 machine-config

```json
{
  "vcpu_count": 2,
  "mem_size_mib": 1024,
  "smt": false,
  "track_dirty_pages": false,
  "huge_pages": "None"
}
```

| 字段 | 说明 |
|------|------|
| `vcpu_count` | vCPU 数量，1～32（x86 开启 SMT 时必须是 1 或偶数） |
| `mem_size_mib` | 内存大小（MiB），默认 128 |
| `smt` | 是否向 Guest 呈现超线程。**ARM64 上不支持，只能是 false** |
| `track_dirty_pages` | 是否记录哪些内存页被改过，用于差量快照（第 15 篇） |
| `huge_pages` | `None`（普通 4K 页）、`2M`（hugetlbfs 大页）、`Transparent`（透明大页，v1.17 起）（第 9 篇） |
| `cpu_template` | 静态 CPU 模板（已不推荐，改用 `/cpu-config`） |

`PUT` 会把未提供的可选字段**重置为默认值**；`PATCH` 只修改你提供的字段。

### 4.2 drives

```json
{
  "drive_id": "data",
  "path_on_host": "/srv/vm1/data.ext4",
  "is_root_device": false,
  "is_read_only": false,
  "cache_type": "Unsafe",
  "io_engine": "Sync",
  "rate_limiter": {
    "bandwidth": { "size": 52428800, "refill_time": 1000 },
    "ops":       { "size": 1000,     "refill_time": 1000 }
  }
}
```

| 字段 | 说明 |
|------|------|
| `drive_id` | 自定义名字，同时出现在 URL 里 |
| `is_root_device` | 是否作为根文件系统（会自动追加 `root=/dev/vda rw` 或 `ro`） |
| `partuuid` | 如果镜像里有分区，用分区的 UUID 指定根分区 |
| `cache_type` | `Unsafe`（默认，不把 Guest 的 flush 请求传给宿主机磁盘）或 `Writeback`（尊重 flush，更安全但更慢） |
| `io_engine` | `Sync`（默认）或 `Async`（基于 io_uring，**开发者预览**）（第 12 篇） |
| `rate_limiter` | 限速器，令牌桶算法（第 12 篇） |

**磁盘的顺序很重要：** 根设备总是 `/dev/vda`，其余磁盘按添加顺序依次是 `/dev/vdb`、`/dev/vdc`……

### 4.3 network-interfaces

```json
{
  "iface_id": "eth0",
  "host_dev_name": "tap0",
  "guest_mac": "06:00:AC:10:00:02",
  "mtu": 1500,
  "rx_rate_limiter": { "bandwidth": { "size": 10485760, "refill_time": 100 } },
  "tx_rate_limiter": { "bandwidth": { "size": 10485760, "refill_time": 100 } }
}
```

`host_dev_name` 必须是一个已经存在的 TAP 设备。`mtu` 字段从 v1.16 开始提供。

### 4.4 actions

```bash
# 开机
curl -X PUT --unix-socket $SOCK -d '{"action_type": "InstanceStart"}' http://localhost/actions
# 立刻把指标写到 metrics 文件
curl -X PUT --unix-socket $SOCK -d '{"action_type": "FlushMetrics"}' http://localhost/actions
```

---

## 五、请求在 Firecracker 内部的旅程

当你发出一个 `curl` 请求，Firecracker 内部发生了这些事：

```
curl ──HTTP──▶ Unix socket
                  │
          ┌───────▼────────┐
          │  API 线程 fc_api │  ① 解析 HTTP 和 JSON，校验格式
          └───────┬────────┘
                  │ ② 把请求封装成一个“指令”，放进通道（channel）
                  │    并写 eventfd 唤醒 VMM 线程
          ┌───────▼────────┐
          │  VMM 主线程      │  ③ 事件循环收到通知，取出指令
          │  （事件循环）     │  ④ 修改配置 / 创建设备 / 启动 vCPU
          └───────┬────────┘
                  │ ⑤ 把结果通过另一个通道送回
          ┌───────▼────────┐
          │  API 线程        │  ⑥ 生成 HTTP 响应（204 或带错误信息的 400）
          └────────────────┘
```

为什么要分两个线程？

- **API 线程从不进入“快车道”**：它只负责处理 HTTP，不碰 Guest 内存、不处理设备 I/O。官方设计文档特别强调这一点；
- **所有状态修改都集中在 VMM 线程**：避免多线程同时修改 microVM 状态带来的复杂加锁问题；
- **两个线程的 seccomp 规则不同**：API 线程只允许它需要的系统调用（ARM64 上约三十个），即使 HTTP 解析代码有漏洞，能做的事也非常有限（第 13 篇）。

这也解释了第 05 篇里为什么要在 `InstanceStart` 前 `sleep 0.015s`：前面的请求虽然已经返回，但在极端情况下，建议给 VMM 线程一点处理时间（入门文档的保守做法）。

---

## 六、错误处理

请求失败时，Firecracker 返回 HTTP 400（或其他 4xx），响应体是一个 JSON：

```bash
sudo curl -s -X PUT --unix-socket /tmp/firecracker.socket \
    -d '{"vcpu_count": 0, "mem_size_mib": 128}' \
    http://localhost/machine-config
```

```json
{"fault_message":"The number of vCPUs must be greater than 0, less than 32 and must be 1 or an even number if SMT is enabled."}
```

（具体措辞可能随版本略有变化。“1 或偶数”的限制只在开启 SMT 时生效，而 ARM64 不支持 SMT，所以在 ARM64 上 1～32 之间任意数量都可以。）

常见错误类型：

| 错误 | 原因 |
|------|------|
| 字段校验失败 | 数值超出范围、缺少必填字段、字段名拼错 |
| 状态不允许 | 开机后还想 `PUT /drives`，或没暂停就创建快照 |
| 文件问题 | 内核/磁盘路径不存在或没有权限 |
| 资源冲突 | TAP 设备被占用、两个设备用了同一个 ID |

**小技巧：** 给 `curl` 加 `-i` 参数可以看到 HTTP 状态码，加 `-s` 隐藏进度条，再用 `jq` 美化输出。

---

## 七、日志与指标

### 7.1 日志（logger）

```json
{
  "log_path": "/var/log/fc/vm1.log",
  "level": "Info",
  "show_level": true,
  "show_log_origin": false
}
```

- `level`：`Error`、`Warning`、`Info`（默认）、`Debug`、`Trace`，大小写不敏感；
- `log_path`：普通文件或命名管道（FIFO）。从 v1.14 起，文件不存在时会自动创建；
- 也可以在命令行配置：`--log-path`、`--level`、`--show-level`、`--show-log-origin`。

### 7.2 指标（metrics）

```bash
sudo curl -X PUT --unix-socket $SOCK \
    -d '{"metrics_path": "./metrics.json"}' http://localhost/metrics
```

Firecracker 会以 JSON 格式输出大量计数器：API 请求数、每个设备的读写字节数、vCPU 退出次数、seccomp 违规次数等。输出时机是：开机时一次、之后每 60 秒一次、收到 `FlushMetrics` 时、以及发生 panic 时。

```bash
tail -n 1 metrics.json | jq '.block, .net, .vcpu' | head -40
```

第 16 篇会讲如何利用这些指标分析性能。

---

## 八、动手：一个 Python 控制脚本

`curl` 适合手工操作，写自动化程序时更方便的是用编程语言。Python 标准库本身不直接支持 Unix socket 上的 HTTP，但只要稍微扩展一下 `http.client` 就可以。

新建 `fcctl.py`：

```python
#!/usr/bin/env python3
"""极简的 Firecracker API 客户端，只用 Python 标准库。"""
import http.client
import json
import socket
import sys


class UnixHTTPConnection(http.client.HTTPConnection):
    """通过 Unix Domain Socket 发送 HTTP 请求。"""

    def __init__(self, socket_path):
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)


class Firecracker:
    def __init__(self, socket_path="/tmp/firecracker.socket"):
        self.socket_path = socket_path

    def _request(self, method, path, body=None):
        conn = UnixHTTPConnection(self.socket_path)
        payload = json.dumps(body) if body is not None else None
        headers = {"Content-Type": "application/json"} if payload else {}
        conn.request(method, path, body=payload, headers=headers)
        resp = conn.getresponse()
        data = resp.read().decode()
        conn.close()
        if resp.status >= 400:
            raise RuntimeError(f"{method} {path} -> {resp.status}: {data}")
        return json.loads(data) if data else None

    # —— 常用操作 ——
    def info(self):
        return self._request("GET", "/")

    def machine(self, vcpus, mem_mib):
        self._request("PUT", "/machine-config",
                      {"vcpu_count": vcpus, "mem_size_mib": mem_mib})

    def kernel(self, path, args):
        self._request("PUT", "/boot-source",
                      {"kernel_image_path": path, "boot_args": args})

    def drive(self, drive_id, path, root=False, read_only=False):
        self._request("PUT", f"/drives/{drive_id}",
                      {"drive_id": drive_id, "path_on_host": path,
                       "is_root_device": root, "is_read_only": read_only})

    def net(self, iface_id, tap, mac):
        self._request("PUT", f"/network-interfaces/{iface_id}",
                      {"iface_id": iface_id, "host_dev_name": tap, "guest_mac": mac})

    def start(self):
        self._request("PUT", "/actions", {"action_type": "InstanceStart"})

    def pause(self):
        self._request("PATCH", "/vm", {"state": "Paused"})

    def resume(self):
        self._request("PATCH", "/vm", {"state": "Resumed"})

    def config(self):
        return self._request("GET", "/vm/config")


if __name__ == "__main__":
    # 用法：sudo python3 fcctl.py <内核文件> <rootfs 文件>
    kernel_path, rootfs_path = sys.argv[1], sys.argv[2]
    fc = Firecracker()
    print("before:", fc.info()["state"])
    fc.machine(vcpus=2, mem_mib=512)
    fc.kernel(kernel_path, "keep_bootcon console=ttyS0 reboot=k panic=1")
    fc.drive("rootfs", rootfs_path, root=True)
    fc.net("net1", "tap0", "06:00:AC:10:00:02")
    fc.start()
    print("after:", fc.info()["state"])
    print(json.dumps(fc.config(), indent=2))
```

使用方法（TAP 设备按第 05 篇 4.1 节准备好）：

```bash
# 终端 1
sudo rm -f /tmp/firecracker.socket
sudo ./firecracker --api-sock /tmp/firecracker.socket

# 终端 2
sudo python3 fcctl.py ./vmlinux-6.1.xxx ./ubuntu-24.04.ext4
```

你会看到状态从 `Not started` 变成 `Running`，并打印出完整配置。

再试试暂停和恢复（另开一个 Python 交互环境）：

```bash
sudo python3 -c "
from fcctl import Firecracker
import time
fc = Firecracker()
fc.pause();  print(fc.info()['state'])
time.sleep(5)
fc.resume(); print(fc.info()['state'])
"
```

暂停的 5 秒内，如果你正 SSH 在 Guest 里，会发现终端完全“冻住”了——vCPU 线程和设备都停了。恢复后，一切继续，Guest 内部的程序甚至察觉不到中间丢了 5 秒（墙上时间除外）。

---

## 九、其他控制方式

| 方式 | 适用场景 |
|------|---------|
| `curl` | 手工调试、学习 |
| `--config-file` | 启动参数固定的场景，一条命令开机 |
| `--no-api` + `--config-file` | 完全不需要运行时控制，进一步减少攻击面 |
| `firecracker-go-sdk` | 用 Go 编写编排系统 |
| 自己的 HTTP 客户端 | 任何语言都可以，按 Swagger 规范实现即可 |

---

## 小结

| 要点 | 内容 |
|------|------|
| 接口形式 | Unix socket 上的 REST，规范见 `firecracker.yaml` |
| 状态机 | Not started → Running ⇄ Paused；没有 Stopped，退出即结束 |
| 方法规律 | `PUT` 多用于开机前“造机器”，`PATCH` 多用于运行中“调参数” |
| 内部处理 | API 线程解析 → 通道 + eventfd → VMM 线程执行 → 结果返回 |
| 错误 | 4xx + `{"fault_message": ...}` |
| 可观测性 | `/logger` 和 `/metrics`，指标每 60 秒刷新一次 |

---

## 思考题

1. 为什么“添加磁盘”只能在开机前做，而“更换磁盘的后端文件”可以在运行中做？后者在 Guest 里需要配合什么操作？
2. API 线程和 VMM 线程之间为什么用“通道 + eventfd”通信，而不是直接让 API 线程去修改配置？
3. 用 `GET /vm/config` 导出一台运行中 microVM 的配置，再用它作为 `--config-file` 启动一台新的 microVM，能得到一模一样的机器吗？哪些东西会不同？
4. 一台 microVM 配置了 `--no-api`，它还能被暂停吗？还能创建快照吗？
5. 如果把 socket 文件的权限设成任何人可写，会有什么安全风险？

---

## 下一篇预告

**[07. 进程与线程模型](07-process-and-threads.md)**

我们已经在 `top -H` 里见过 `fc_api`、`fc_vcpu 0` 这些线程。下一篇深入 Firecracker 的内部结构：每个线程负责什么、事件循环如何工作、为什么选择 Rust。
