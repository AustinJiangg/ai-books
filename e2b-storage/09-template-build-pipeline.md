# 第 9 篇｜从 Dockerfile 到 rootfs.ext4：模板构建流水线

> **本篇目标**：上一篇拿到了 Docker 镜像。本篇看它怎么一步步变成第 7 篇说的那六个文件：镜像怎么变成一块 ext4 根盘，虚拟机为什么要开机两次，模板里的每一步命令怎么变成一层，层缓存为什么能让第二次构建快很多，最后的“预取映射”又是怎么录出来的。全程只盯着一件事：**磁盘和内存数据是怎么产生、存到哪的**。

---

## 一、入口：一次构建请求

在这套环境里，建模板一般是在宿主机上跑一个 Python 脚本，比如 `benchmark/build_template.py`：

```python
template = (
    Template()
    .from_dockerfile('FROM harbor:443/e2b-orchestration/ubuntu:22.04-custom')
    .run_cmd('pip install numpy')        # 假设有这样一步
)
Template.build(template, alias='base', cpu_count=2, memory_mb=2048)
```

SDK 把它翻译成一串“步骤”，交给 api；api 记下一条 build 记录，分配一个 buildID，再通过 gRPC 交给 template-manager。这套环境的 SDK 被 `build.sh -i` 打过补丁（`dockerfile_parser.py`、`build_api.py`、`main.py` 等），主要是让它适配本地部署的地址和明文 http。

请求里和存储有关的参数有：

| 参数 | 含义 |
|---|---|
| `from_image` | 起点镜像，这里是 Harbor 上的 ubuntu |
| 步骤列表 | RUN、COPY、ENV、WORKDIR、USER 等 |
| `cpu_count`、`memory_mb` | 构建和运行时虚拟机的规格，决定 memfile 有多大 |
| `disk_size_mb` | 根盘最终多大 |
| 内核版本、Firecracker 版本 | 决定去 `/fc-kernels`、`/fc-versions` 下找哪个 |
| `huge_pages` | 内存用不用 2 MiB 大页，决定 memfile 的块大小 |

---

## 二、全景：五个阶段、多个层

template-manager 收到请求后，按顺序跑五个阶段：

```
 ① base       镜像 → ext4 根盘 → 开机两次 → 打快照       → 第 1 层
 ② user       创建默认用户                               → 第 2 层（新版模板才有）
 ③ steps      模板里的每一步命令，每步一层                 → 第 3 … N 层
 ④ finalize   跑配置脚本、启动命令，等就绪，打快照          → 最后一层（这就是模板）
 ⑤ optimize   恢复几次，录下启动时访问了哪些内存页           → 只改 metadata.json
```

注意：**每一层都是一次快照，都是一个完整的 build**，有自己的 buildID，都会上传到模板存储。一个有 5 步命令的模板，构建完会在 `/tmp/templates` 下留下七八个目录。最后一层的 header 会引用前面各层的数据文件（第 7 篇）。

下面按阶段讲。

---

## 三、base 阶段（一）：镜像变成 ext4

### 3.1 往镜像上加几层系统文件

镜像里只有 Ubuntu 的文件，要变成一台能被 E2B 管理的虚拟机，还缺几样东西。template-manager 在镜像上**追加几个 OCI 层**，放进：

- **envd**：沙箱里的守护进程，从宿主机的 `/fc-envd/envd` 拷来；
- **busybox**：一个精简的工具集，用作第一次开机时的 init。ARM 补丁换成了 glibc 版的 arm64 busybox（RPM 构建时拷进源码树，编译时嵌入 orchestrator 二进制）；
- **provision.sh**：第一次开机要跑的脚本；
- hostname、DNS 配置（`/etc/resolv.conf`）、envd 的 systemd 服务文件等。

追加层而不是直接改镜像，是因为镜像本身是只读的、按内容寻址的（第 8 篇）。

### 3.2 做一块空的 ext4

先用 `mkfs.ext4` 在一个普通文件里格式化出一个文件系统（简化）：

```bash
mkfs.ext4 -O ^dir_index,^64bit,... -b 4096 -m 0 -i <每多少字节一个 inode> rootfs.ext4 <上限>M
```

- `-b 4096`：块大小 4 KiB，就是第 2 篇说的 `RootfsBlockSize`；
- 大小先按一个**上限**来做（由特性开关控制），保证装得下。

这个文件放在 `/orchestrator/build-templates/<buildID>/` 下，是构建期间的临时工作目录，构建完就删。

### 3.3 解包

把这个 ext4 文件**用 loop 设备挂载**到一个临时目录（第 3 篇的 loop 设备在这里出场了）：

```bash
mount -o loop rootfs.ext4 /tmp/ext4-mountXXXX
```

然后把镜像的所有层按顺序解开，铺进这个目录。这时 template-manager 才真正从 Harbor 把一层层 `tar.gz` 拉下来。解完卸载。

### 3.4 检查、缩小、再检查

```bash
e2fsck -pfv rootfs.ext4       # 检查一致性
resize2fs -M rootfs.ext4      # 缩到能装下内容的最小尺寸
e2fsck -pfv rootfs.ext4       # 缩完再检查
```

先按上限做、再缩小，是因为解包之前不知道内容到底多大。到这一步，得到一个**刚好装下镜像内容**的 ext4 文件。

---

## 四、base 阶段（二）：开机两次

### 4.1 第一次开机：只跑 provision 脚本

镜像里的 Ubuntu 通常是给容器用的精简版，没有 systemd，没法当一台正常的虚拟机启动。所以第一次开机用 **busybox 当 init**，只做一件事：跑 `provision.sh`，把缺的东西装上。

`provision.sh` 会检查并安装这些包：

```
systemd systemd-sysv openssh-server sudo chrony linuxptp socat curl ca-certificates
```

ARM 补丁对这个脚本做了两处改动：

- 能识别 openEuler、RHEL 这类系统，用 `dnf` 装包；Ubuntu、Debian 仍用 `apt-get`；
- 包列表比上游少了 `fuse3 iptables git nfs-common` 几项。

脚本跑完把结果写到一个文件里，虚拟机关机。这一次开机**不打快照**，只为了改根盘。

这次开机时根盘不走 NBD，而是直接把 `rootfs.ext4` 文件交给 Firecracker（第 12 篇讲这种“Direct”方式）。

### 4.2 检查和扩容

provision 之后再 `e2fsck` 一次。然后**扩容**到模板要求的磁盘大小 `disk_size_mb`：

```bash
resize2fs rootfs.ext4 <disk_size_mb>M
```

扩出来的空间在文件里是“洞”，不占实际存储（第 2 篇的稀疏文件）。

### 4.3 第二次开机：正式启动

这一次用 systemd 正常启动，等 envd 起来、能响应请求。然后在里面执行一次 `sync`，把客户机页缓存里的数据刷到盘上。

接着**暂停虚拟机、打快照**。这是第一份真正的快照，产生第 1 层：

- `rootfs.ext4`：根盘是 Direct 方式，整个文件都被标记为“写过”，所以这一层的根盘数据是**完整的**；
- `memfile`：这次开机不是从快照恢复的，内存后端不是 UFFD，而是 Firecracker 自己管的内存（代码里叫 NoopMemory）。导出时先问 Firecracker “哪些页在内存里、哪些页全是零”（`GET /memory`），只导出在内存里且不全零的页，全零的映射到 `uuid.Nil`（第 7 篇）；
- `snapfile`、`metadata.json`、两个 header。

打快照的细节和暂停是同一套流程，第 14 篇详讲。

---

## 五、steps 阶段：每一步命令一层

### 5.1 一层是怎么做出来的

模板里的每一步（`RUN pip install numpy`、`COPY app.py /app/`……）各做一层。做法都一样：

```
 1. 从上一层的快照恢复一个沙箱     （第 12、13 篇的 NBD + UFFD，毫秒级）
 2. 在沙箱里执行这一步              （通过 envd 跑命令、传文件）
 3. 暂停，打快照                   （只存这一步改过的块和页）
 4. 上传到模板存储                 （异步进行，不阻塞下一步）
```

因为第 3 步只存改动，所以：

- `RUN pip install numpy` 这一层的 `rootfs.ext4` 只有 numpy 写进去的那些块；
- 它的 header 把其余部分都指向前面的层。

### 5.2 层缓存：同样的步骤不做第二次

如果你改了模板的第 4 步重新构建，前 3 步完全没变，有必要再跑一遍吗？没必要。E2B 给每一层算一个**哈希**：

```
第 N 层的哈希 = hash(第 N-1 层的哈希, 这一步的内容, 相关参数……)
```

做完一层后，往**构建缓存存储**里写一个小文件：

```
<缓存范围>/index/<哈希>   内容：{"template": {"build_id": "<这一层的 buildID>"}}
```

下次构建时，先算哈希，去 index 里查：查到了，就直接用那个 buildID 作为这一层，跳过整个“恢复—执行—快照—上传”。因为哈希包含了上一层的哈希，所以只要前面任何一步变了，后面的哈希全都会变，不会错用缓存。

### 5.3 COPY 的文件

`COPY` 步骤要把宿主机上的文件传进沙箱。设计上，SDK 先按文件内容算一个哈希，向 api 要一个“上传链接”，把文件打成 tar 上传到构建缓存存储：

```
<缓存范围>/files/<哈希>.tar
```

再由 template-manager 取出来放进沙箱。

这里有一个这套环境要注意的地方：模板存储和构建缓存存储都是 `Local` 后端（第 10 篇），而 `Local` 后端的“生成上传链接”接口直接返回错误，代码原文是：

```go
func (s *fsStorage) UploadSignedURL(...) (string, error) {
    return "", fmt.Errorf("file system storage does not support signed URLs")
}
```

所以带本地文件 `COPY` 的模板，在这套环境上会在上传这一步出问题。作者自己的测试模板只用了 `FROM` 和 `RUN`，没有碰到它。

### 5.4 上传按顺序确认

每一层的上传是异步的，但写 index 这一步会**等前面所有层都上传完**才做。原因是：如果第 5 层的 index 先写了，而第 4 层的数据还没传完，另一次构建恰好命中第 5 层的缓存，就会去读一个还不存在的第 4 层，直接出错。

---

## 六、finalize 阶段：最后一层

最后一层就是用户最终拿到的模板。它要做：

1. 从最后一个步骤层恢复沙箱；
2. 跑 **configure.sh**：开 swap、建用户、改目录权限等收尾配置。ARM 补丁把这个脚本从 bash 改成了 POSIX sh 写法（`#!/bin/sh`），并区分 Debian 系和 openEuler 系；
3. 如果模板有**启动命令**，在后台把它跑起来；
4. 反复执行**就绪命令**，直到它成功（比如检查某个端口已经在监听）；
5. 暂停、打快照、上传。

这一层的快照里，启动命令已经在跑、服务已经就绪。以后从它恢复的沙箱，打开就是“服务已就绪”的状态，这正是 E2B 毫秒启动的意义所在。

---

## 七、optimize 阶段：录一份“预取清单”

最后一个阶段不产生新层，只往 `metadata.json` 里加一样东西：**预取映射**。

做法是：

1. 从最终模板恢复沙箱，等 envd 响应；
2. 记下这个过程中 UFFD 处理过哪些内存块、顺序如何、是读是写；
3. 关掉沙箱，**重复几次**；
4. 只保留**每一次都出现**的块，按平均顺序排好；
5. 写进 `metadata.json` 的 `prefetch.memory`，重新上传这个文件。

以后从这个模板创建沙箱时，orchestrator 会按这份清单，在客户机真正访问之前就把这些块准备好（第 13 篇）。

这一步失败不会让构建失败：预取只是优化，没有也能用。

---

## 八、构建完，东西都在哪

假设一个模板有两步命令，构建完后：

```
/tmp/templates/                         模板存储（第 10 篇）
├── <base 层 buildID>/                  六个文件，rootfs 完整，memfile 去掉了全零页
├── <user 层 buildID>/                  六个文件，只含改动
├── <step1 层 buildID>/                 六个文件，只含改动
├── <step2 层 buildID>/                 六个文件，只含改动
└── <finalize 层 buildID>/              六个文件，只含改动；header 引用上面所有层
                                        metadata.json 含预取映射
                                        ← 这就是 api 记录里“模板”指向的 build

/tmp/build-cache/<缓存范围>/             构建缓存存储
├── index/<哈希1>   → base 层 buildID
├── index/<哈希2>   → user 层 buildID
├── index/<哈希3>   → step1 层 buildID
└── ……

/orchestrator/build-templates/          构建时的工作目录，构建结束即删
/orchestrator/build/、/orchestrator/template/   本地缓存（第 11 篇），每一层也在这里有一份
```

如果构建**失败**，template-manager 会把这次 buildID 前缀下的文件都删掉（`DeleteObjectsWithPrefix`），但已经成功的前几层不受影响，下次还能命中缓存。

---

## 九、几个和存储相关的坑

| 现象 | 原因 |
|---|---|
| 建模板卡在 `Provisioning sandbox template` 后失败 | `/fc-kernels/<版本>/vmlinux.bin` 不存在，或 provision 脚本在客户机里装包失败 |
| 等 envd 60 秒超时，报 `build was cancelled` | 宿主的 `ip_forward` 是 0，宿主探不到客户机里的 envd（网络问题，见网络书第 21 篇） |
| 改了第 N 步后，前面的步骤还是重新执行了 | 前面某一步的哈希变了，比如 `FROM` 的镜像标签指向了新内容 |
| `/tmp/templates` 越来越大 | 每一层、每一个旧版本都在这里，只有删模板才回收 |
| 宿主机重启后模板没了，但缓存索引还在 | 两者都在 `/tmp`，都会丢；如果只丢了一个，会出现“命中缓存却找不到层”的错误 |

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| 五个阶段 | base、user、steps、finalize、optimize |
| 每层一个 build | 每一步都是一次快照，有自己的 buildID，都上传 |
| 追加系统层 | envd、busybox、provision.sh 等以 OCI 层的形式加到镜像上 |
| 镜像转 ext4 | mkfs 一个上限大小的文件，loop 挂载解包，e2fsck，缩到最小 |
| 第一次开机 | busybox 当 init，只跑 provision.sh 装 systemd 等，不打快照 |
| 扩容 | 按 `disk_size_mb` 扩大，扩出的部分是稀疏的 |
| 第二次开机 | systemd 正常启动，等 envd，打第一份快照，根盘完整、内存去掉全零页 |
| 层缓存 | 按哈希在构建缓存存储里记“哈希 → buildID”，命中就跳过 |
| COPY 文件 | 存在构建缓存的 `files/<哈希>.tar`；Local 后端不支持上传链接 |
| finalize | 跑 configure.sh、启动命令，等就绪后打最后一层 |
| optimize | 恢复几次，录下共同访问的内存块，写进 metadata.json |

**下一篇预告**：[《模板存到哪：存储后端、Local 与“装了没用”的 MinIO》](10-storage-backends.md)。上面反复提到“上传到模板存储”。下一篇讲这个“模板存储”到底是什么：E2B 支持哪几种存储后端，这套环境的 `.env` 写了 MinIO 为什么没生效，模板为什么最后落在了 `/tmp/templates`，以及这意味着什么。
