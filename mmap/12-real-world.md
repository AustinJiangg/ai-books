# 第 12 篇｜真实世界里的 mmap：谁在用、怎么用、踩过哪些坑

> **本篇目标**：看 mmap 在真实系统中的用法——动态链接器、数据库、设备与零拷贝、虚拟机（以 **Firecracker** 为例）；认识让用户程序接管缺页的 **userfaultfd**；汇总常见陷阱和排查工具；最后用一张图把整个系列串起来。

---

## 一、你每天都在用的 mmap：程序和动态库的加载

还记得第 1 篇的彩蛋吗？`strace cat` 时出现了好几行 `mmap`。现在我们有足够的知识看懂它们了。

### 1.1 内核加载可执行文件

当你执行一个程序时，`execve` 系统调用里的内核代码（ELF 加载器）会读取可执行文件的头部，找到其中描述"哪些部分要加载到内存哪里"的程序头（`PT_LOAD` 段），然后对每一段做一次**文件映射**：

- 代码段：`PROT_READ | PROT_EXEC`，私有映射；
- 只读数据：`PROT_READ`；
- 可读写数据：`PROT_READ | PROT_WRITE`，私有映射（写时复制，不会改动磁盘上的程序文件）；
- 未初始化数据（.bss）：匿名映射，初始全为 0。

程序启动时**一行代码都没有从磁盘读进来**，都是执行到哪里、缺页到哪里（第 4 篇做 `python3` 冷启动实验时看到的大缺页，就是这么来的）。

### 1.2 动态链接器加载共享库

程序依赖的共享库（如 `libc.so.6`）由动态链接器 `ld-linux-aarch64.so.1` 在用户态加载。用 strace 观察：

```bash
strace -e trace=openat,mmap,mprotect,munmap,close cat /dev/null 2>&1 | grep -A 9 libc.so
```

在 ARM64 上输出类似这样（地址和大小因系统而异）：

```
openat(AT_FDCWD, "/lib/aarch64-linux-gnu/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
mmap(NULL, 1826976, PROT_NONE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_DENYWRITE, -1, 0) = 0xffffa1c40000
mmap(0xffffa1c50000, 1761440, PROT_READ|PROT_EXEC, MAP_PRIVATE|MAP_FIXED|MAP_DENYWRITE, 3, 0) = 0xffffa1c50000
munmap(0xffffa1c40000, 65536)           = 0
munmap(0xffffa1dfd000, 5280)            = 0
mprotect(0xffffa1dd9000, 77824, PROT_NONE) = 0
mmap(0xffffa1dec000, 20480, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_FIXED|MAP_DENYWRITE, 3, 0x18c000) = 0xffffa1dec000
mmap(0xffffa1df1000, 49632, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_FIXED|MAP_ANONYMOUS, -1, 0) = 0xffffa1df1000
close(3)                                = 0
```

逐行翻译：

| 调用 | 作用 | 对应知识 |
|---|---|---|
| `mmap(NULL, …, PROT_NONE, MAP_ANONYMOUS)` | 先**预留**一整段地址空间，什么权限都没有 | 第 8 篇：用 PROT_NONE 预留地址 |
| `mmap(…, PROT_READ\|PROT_EXEC, MAP_FIXED, fd=3, 0)` | 把库的代码映射到预留区域里（按对齐要求选定的位置） | 第 6、7 篇：私有文件映射；`MAP_FIXED` 覆盖自己预留的区域 |
| 两次 `munmap` | 修剪掉为了对齐而多预留的头尾部分 | ARM64 上库常按 64KB 对齐，以兼容 64KB 页的内核 |
| `mprotect(…, PROT_NONE)` | 代码段和数据段之间的空隙设为不可访问 | 第 7 篇：警戒区 |
| `mmap(…, PROT_READ\|PROT_WRITE, MAP_FIXED, fd=3, 0x18c000)` | 从文件偏移 0x18c000 处映射可写数据段 | 私有可写映射，写时复制 |
| `mmap(…, MAP_ANONYMOUS)` | 映射 .bss，初始为 0 | 第 8 篇：匿名映射 |
| `close(3)` | 映射建立后关闭文件 | 第 6 篇：映射持有文件引用 |

之后，动态链接器还会进行**重定位**（修正库中引用的地址），写入的是私有可写页，触发 COW；完成后再用 `mprotect` 把一部分区域改回只读（称为 RELRO），防止被攻击者篡改。

### 1.3 为什么系统里 100 个进程只占一份 libc？

libc 的代码段是 `MAP_PRIVATE` 映射的，但代码段**从来不被写**，所以永远不会触发写时复制。所有进程的页表都指向页缓存里的同一批物理页。100 个进程运行，libc 代码在物理内存里只有一份。这就是第 11 篇中 smaps 里 `Shared_Clean` 和 `Pss` 的意义。

> `MAP_DENYWRITE` 这个标志现在已被内核忽略。历史上它用于防止正在被执行的文件被写入。现在，如果你试图用 `O_WRONLY` 打开一个正在运行的程序文件，内核仍会返回 `ETXTBSY`（"文本文件忙"），这就是为什么升级软件时通常是"写新文件再改名替换"，而不是原地覆盖。

---

## 二、数据库：mmap 的拥护者与反对者

数据库是 mmap 最有争议的应用领域。

### 2.1 拥护者：LMDB

**LMDB**（Lightning Memory-Mapped Database）把整个数据库文件 mmap 进来，作为它的"缓存"：

- **读**：读取直接访问映射区域，返回的数据就是指向页缓存的指针，**真正的零拷贝**。读操作不需要加锁，也不需要系统调用；
- **写**：默认通过普通的 `write`/`pwrite` 写入（映射是只读的，防止程序的野指针意外破坏数据库）；也可以选择 `MDB_WRITEMAP` 让写入直接走映射；
- **一致性**：使用**写时复制的 B+ 树**，从不原地修改旧数据，新版本写到新的页上。提交时先 `fdatasync` 数据页，再写一个"元数据页"切换到新的树根。崩溃时，旧的元数据页依然指向一棵完整的旧树（第 9 篇讲的"写时复制数据结构"思路）；
- **地址稳定**：一开始就映射一个配置的最大大小（`mapsize`），文件在其中增长，所以返回给用户的指针一直有效（第 9 篇的"预留大块地址空间"）。

LMDB 代码量很小，读性能极高，被 OpenLDAP 等项目使用。

### 2.2 部分使用：SQLite、Lucene 等

- **SQLite** 支持 `PRAGMA mmap_size=N` 开启 mmap 读取，在大多数构建中默认关闭。开启后读操作走映射，写操作通常仍用 `write`；
- **Apache Lucene**（Elasticsearch 的底层）在 64 位系统上默认用 `MMapDirectory` 读取索引文件，大量依赖页缓存；
- **Kafka** 用 mmap 访问它的索引文件；
- **Prometheus** 的时序数据库也用 mmap 读取历史数据块。

它们的共同点是：**主要用 mmap 读，写入则走更可控的路径**。

### 2.3 反对者：为什么有的数据库放弃了 mmap

**MongoDB** 早期的存储引擎 MMAPv1 基于 mmap，后来被 WiredTiger 引擎取代，MMAPv1 在 4.2 版本中被移除。

2022 年，卡内基梅隆大学和慕尼黑工业大学的研究者在数据库会议 CIDR 上发表了一篇被广泛讨论的论文，标题大意是"你确定要在数据库管理系统里用 mmap 吗？"。论文总结的问题，恰好对应本系列的几个章节：

| 问题 | 说明 | 对应章节 |
|---|---|---|
| 事务安全 | 内核可能在任何时刻写回任何脏页，数据库无法阻止"未提交的修改"被写到磁盘 | 第 9 篇 |
| I/O 阻塞 | 缺页是同步的，数据库无法控制何时发生 I/O，也无法异步、并发地发起 I/O | 第 10 篇 |
| 错误处理 | I/O 错误变成 SIGBUS，难以优雅处理；校验数据完整性也更困难 | 第 9 篇 |
| 性能扩展性 | 在高速 NVMe 上，页表维护、TLB 击落、内核单线程的页面淘汰会成为瓶颈 | 第 10、11 篇 |

论文的结论是：对于数据量超过内存、追求高性能的数据库，自己管理缓冲池（配合 `O_DIRECT` 或 `io_uring`）通常是更好的选择。

当然，LMDB 等项目的作者也有反驳：通过合适的设计（如只读映射加写时复制），许多问题是可以规避的；在数据能装入内存的场景下，mmap 的简洁与高性能难以替代。

**这场争论没有标准答案，但它恰好是检验你是否理解本系列的绝佳材料：** 如果你能看懂双方每一个论点背后的机制，你就真正理解了 mmap。

---

## 三、零拷贝与设备映射

### 3.1 mmap 是"零拷贝"吗？

假设一个 Web 服务器要把文件发送给客户端：

| 方式 | 数据拷贝次数（CPU 拷贝） |
|---|---|
| `read` 到缓冲区，再 `write` 到套接字 | 2 次：页缓存 → 用户缓冲区 → 套接字缓冲区 |
| `mmap` 文件，再 `write` 映射区域到套接字 | 1 次：页缓存（通过映射）→ 套接字缓冲区 |
| `sendfile(sock, file_fd, ...)` | 0 次（在支持的网卡上，数据可直接从页缓存 DMA 到网卡） |

所以 mmap 只是"少一次拷贝"，在"把文件发到网络"这件事上，`sendfile` 或 `splice` 才是更彻底的零拷贝。mmap 的零拷贝优势在于**程序自己要读这些数据**的场景。

### 3.2 映射设备内存

mmap 不只能映射文件，也能映射**设备**。驱动程序在自己的 `mmap` 回调里（第 11 篇），通常调用 `remap_pfn_range()` 把设备的物理地址直接填进进程的页表：

- **帧缓冲**（`/dev/fb0`）：映射后，写内存就是在屏幕上画像素；
- **GPU**：显卡驱动通过 mmap 让程序直接访问显存或与 GPU 共享的内存；
- **用户态驱动**：DPDK、SPDK 等高性能网络/存储框架通过 VFIO 或 UIO，把网卡、NVMe 控制器的寄存器（PCIe BAR 空间）mmap 到用户空间，完全绕过内核直接操作硬件。

在 ARM64 上，映射设备时页表项会带上不同的**内存属性**（通过页表项的 AttrIndx 字段选择 MAIR_EL1 寄存器里预设的属性）：

- 普通内存：可缓存（Normal, Cacheable）；
- 设备寄存器：**Device-nGnRE** 等类型，不经过缓存，访问不能被合并或重排序，每次读写都真实到达设备；
- 帧缓冲这类：常用 Normal Non-cacheable，允许写合并以提高效率。

这就是第 2 篇讲的 MMIO 在用户空间的延伸：通过 mmap，程序也能"用读写内存的方式操作设备"。

### 3.3 内核与用户共享的环形缓冲区

很多现代内核接口都用 mmap 建立内核与用户程序之间的**共享内存**，以避免反复的系统调用和拷贝：

- **io_uring**：提交队列和完成队列是 mmap 出来的环形缓冲区，程序把请求写进去、从里面读结果；
- **perf**：性能事件的采样数据通过 mmap 的环形缓冲区传给用户程序；
- **AF_XDP**：高速网络数据包通过 mmap 的共享内存区域收发；
- **eBPF**：某些类型的 BPF map 可以直接 mmap 到用户空间读写。

---

## 四、虚拟机：Firecracker 如何用 mmap 管理客户机内存

虚拟机是 mmap 最精彩的应用场景之一，它把本系列几乎所有的知识都用上了。我们以 Firecracker（一个基于 KVM 的轻量级虚拟机监控程序，常用于运行安全容器和无服务器函数）为例。

### 4.1 客户机的"物理内存"其实是主机进程的虚拟内存

启动一个 1GB 内存的 Firecracker 微虚拟机时，Firecracker 进程大致做了这样的事：

```c
// 概念示意（Firecracker 本身用 Rust 编写）
void *guest_mem = mmap(NULL, 1UL << 30, PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE, -1, 0);

struct kvm_userspace_memory_region region = {
    .slot            = 0,
    .guest_phys_addr = 0x80000000,          // 客户机看到的物理地址起点
    .memory_size     = 1UL << 30,
    .userspace_addr  = (uint64_t)guest_mem, // 对应主机进程中的虚拟地址
};
ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, &region);
```

- 用一次**匿名 mmap** 申请 1GB 虚拟内存，`MAP_NORESERVE` 表示不预先占用内存额度；
- 通过 `KVM_SET_USER_MEMORY_REGION` 告诉 KVM："客户机物理地址 `0x8000_0000` 开始的 1GB，对应我进程里这段虚拟地址。"在 ARM64 上，Firecracker 把客户机内存（DRAM）放在客户机物理地址 2GB 处，低于它的地址留给虚拟设备（MMIO）；
- 客户机里的 Linux 以为自己有 1GB 物理内存，但它在主机上只是一个 mmap 区域。

这就是第 8 篇的匿名映射，加上第 4 篇的按需分页：**客户机没碰过的内存，主机上不占任何物理页。** 这让一台主机可以运行成千上万个微虚拟机。

### 4.2 ARM64 的两阶段地址翻译

客户机里的程序访问一个地址，要经过**两次翻译**：

```
 客户机程序的虚拟地址 (VA)
        │  第一阶段：客户机内核自己的页表（客户机的 TTBR0/TTBR1_EL1）
        ▼
 客户机"物理"地址（ARM 称为 IPA，中间物理地址）
        │  第二阶段：KVM 管理的 stage-2 页表（由 VTTBR_EL2 指向，在 EL2 生效）
        ▼
 主机物理地址 (PA)
```

第 1 篇提到的 EL2（虚拟机管理器级别）在这里登场了：stage-2 页表由主机的 KVM 维护，客户机完全看不到它。

当客户机第一次访问某个 IPA，而 stage-2 页表里还没有对应条目时，会触发一次 **stage-2 缺页**，CPU 陷入 EL2 交给 KVM 处理：

1. KVM 根据内存区域登记，把 IPA 换算成 Firecracker 进程里的主机虚拟地址；
2. KVM 像普通的内核代码那样"访问"这个主机虚拟地址，如果主机页表里也还没有，就触发**主机侧的普通缺页**（第 4 篇），分配一个清零的物理页；
3. KVM 把这个物理页填进 stage-2 页表；
4. 返回客户机，重新执行出错的指令。

缺页套缺页，但对客户机来说完全透明。

### 4.3 快照与恢复：MAP_PRIVATE 的妙用

Firecracker 支持把运行中的虚拟机**保存成快照**（包含内存文件和设备状态），之后从快照快速恢复。恢复时，客户机内存可以有两种"后端"：

**后端一：文件映射**

```c
void *guest_mem = mmap(NULL, mem_size, PROT_READ | PROT_WRITE,
                       MAP_PRIVATE, snapshot_mem_fd, 0);
```

把快照内存文件**私有映射**为客户机内存。这一行代码同时用到了：

- **按需分页**（第 4 篇）：恢复时不读整个内存文件，客户机访问到哪一页，才从文件读哪一页，所以恢复几乎瞬间完成；
- **页缓存**（第 5 篇）：从同一个快照恢复的多个虚拟机，读到的是页缓存里的同一份物理页；
- **写时复制**（第 7 篇）：客户机写某一页时，才复制出一份私有页，快照文件本身永远不会被修改。

**后端二：userfaultfd**

Firecracker 也可以把客户机内存注册到 **userfaultfd**（见下一节），把缺页处理交给一个外部的"页面错误处理进程"。这个处理进程可以从任何地方取得页面内容：本地文件、远端存储、内存压缩池……这为更灵活的恢复策略（例如预取热点页面、跨主机懒加载）打开了大门。

### 4.4 其他用到 mmap 知识的地方

- **气球设备（balloon）**：主机想回收客户机暂时不用的内存时，客户机里的气球驱动"吃掉"一些页并把页号报告给 Firecracker，Firecracker 对这些页调用 `madvise(MADV_DONTNEED)`（第 10 篇），立即把物理页归还给主机；
- **大页**：Firecracker 可以配置用 2MB 大页（hugetlbfs）作为客户机内存，减少两阶段翻译下的 TLB 压力（第 10 篇）；
- **增量快照**：借助 KVM 的脏页跟踪，只保存自上次快照以来被写过的页（与第 9 篇讲的"内核如何追踪写入"思路相似）；
- **与外部进程共享客户机内存**：使用 vhost-user 等机制时，客户机内存改用 `memfd_create` 创建的共享映射，再把 fd 传给后端进程映射同一块内存（第 8 篇）。

---

## 五、userfaultfd：让用户程序接管缺页

### 5.1 是什么

正常情况下，缺页由内核处理：匿名页清零、文件页从页缓存取。**userfaultfd** 让一个用户程序说："这段内存的缺页，交给我来处理。"

工作流程：

```
 ① 程序创建 userfaultfd，得到一个文件描述符 uffd
 ② 用 UFFDIO_REGISTER 把一段内存区域注册到 uffd
 ③ 某个线程访问这段区域中的一个缺失页
      → 内核不再自己处理，而是让这个线程暂停，并往 uffd 上投递一条"缺页消息"
 ④ 处理线程从 uffd 读到消息：哪个地址缺页了
 ⑤ 处理线程准备好这一页的内容，用 UFFDIO_COPY 把它"放进"缺页地址
 ⑥ 内核填好页表，唤醒第③步暂停的线程，它重新执行指令，读到了处理线程提供的数据
```

用途：

- 虚拟机**热迁移**（post-copy 方式）：先把虚拟机切换到目标主机运行，内存页在被访问时才从源主机拉取；
- 虚拟机**快照懒加载**（如上一节的 Firecracker）；
- 垃圾回收器、检查点/恢复工具（CRIU）等。

### 5.2 一个最小示例

```c
// uffd_demo.c —— 用 userfaultfd 让用户线程处理缺页
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <linux/userfaultfd.h>

#ifndef UFFD_USER_MODE_ONLY
#define UFFD_USER_MODE_ONLY 1       // Linux 5.11+：只处理用户态访问引发的缺页
#endif

static long page;
static int  uffd;

static void *fault_handler(void *arg) {
    (void)arg;
    // 准备一个"源页"，每次缺页时往里写不同内容
    char *src = mmap(NULL, page, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    int count = 0;
    for (;;) {
        struct uffd_msg msg;
        if (read(uffd, &msg, sizeof msg) != sizeof msg)   // 阻塞，直到有缺页消息
            continue;
        if (msg.event != UFFD_EVENT_PAGEFAULT)
            continue;

        unsigned long addr = msg.arg.pagefault.address & ~(page - 1);
        memset(src, 0, page);
        snprintf(src, page, "第 %d 次缺页由用户线程处理（页地址 %#lx）", ++count, addr);

        struct uffdio_copy copy = {
            .dst = addr, .src = (unsigned long)src, .len = page, .mode = 0,
        };
        if (ioctl(uffd, UFFDIO_COPY, &copy) < 0)          // 把内容放进缺页地址并唤醒
            perror("UFFDIO_COPY");
    }
    return NULL;
}

int main(void) {
    page = sysconf(_SC_PAGESIZE);

    uffd = syscall(SYS_userfaultfd, O_CLOEXEC | UFFD_USER_MODE_ONLY);
    if (uffd < 0) { perror("userfaultfd（可能需要 root 或较新的内核）"); return 1; }

    struct uffdio_api api = { .api = UFFD_API };
    if (ioctl(uffd, UFFDIO_API, &api) < 0) { perror("UFFDIO_API"); return 1; }

    size_t len = 4 * page;
    char *area = mmap(NULL, len, PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (area == MAP_FAILED) { perror("mmap"); return 1; }

    struct uffdio_register reg = {
        .range = { .start = (unsigned long)area, .len = len },
        .mode  = UFFDIO_REGISTER_MODE_MISSING,            // 接管"页缺失"类缺页
    };
    if (ioctl(uffd, UFFDIO_REGISTER, &reg) < 0) { perror("UFFDIO_REGISTER"); return 1; }

    pthread_t t;
    pthread_create(&t, NULL, fault_handler, NULL);

    for (int i = 0; i < 4; i++)                           // 依次访问 4 页，每页触发一次缺页
        printf("第 %d 页的内容: %s\n", i, area + i * page);

    printf("再次访问第 0 页（不会再缺页）: %s\n", area);
    return 0;
}
```

```bash
gcc uffd_demo.c -o uffd_demo -pthread && ./uffd_demo
# 第 0 页的内容: 第 1 次缺页由用户线程处理（页地址 0xffff9e6f0000）
# 第 1 页的内容: 第 2 次缺页由用户线程处理（页地址 0xffff9e6f1000）
# 第 2 页的内容: 第 3 次缺页由用户线程处理（页地址 0xffff9e6f2000）
# 第 3 页的内容: 第 4 次缺页由用户线程处理（页地址 0xffff9e6f3000）
# 再次访问第 0 页（不会再缺页）: 第 1 次缺页由用户线程处理（页地址 0xffff9e6f0000）
```

一块"匿名内存"里的内容，完全由另一个线程按需"编造"出来。把第 `snprintf` 那一行换成"从快照文件读取对应页"或"从网络拉取对应页"，你就得到了 Firecracker 快照懒加载和虚拟机热迁移的核心思路。

> 出于安全考虑，许多发行版默认限制非特权用户使用 userfaultfd（`/proc/sys/vm/unprivileged_userfaultfd` 为 0）。`UFFD_USER_MODE_ONLY` 标志允许非特权用户只处理用户态访问引起的缺页；如果你的内核较老不支持，可以用 root 运行并去掉这个标志。

---

## 六、常见陷阱大汇总

| 陷阱 | 后果 | 对策 | 详见 |
|---|---|---|---|
| 用 `NULL` 判断 mmap 失败 | 失败后访问 `(void*)-1` | 与 `MAP_FAILED` 比较 | 第 6 篇 |
| 写死页大小 4096 | 在 16KB/64KB 页的 ARM64 系统上 offset 不对齐 | `sysconf(_SC_PAGESIZE)` | 第 3、6 篇 |
| 映射空文件 | `EINVAL` | 先检查大小 | 第 6 篇 |
| 访问超出文件末尾的页 | SIGBUS | 不越界；先 `ftruncate`/`fallocate` | 第 6、9 篇 |
| 映射后文件被截短 | SIGBUS | 文件锁、memfd 封印 | 第 9 篇 |
| 稀疏文件写入时磁盘满 | SIGBUS | 用 `fallocate` 预分配 | 第 9 篇 |
| 以为 `MAP_PRIVATE` 是快照 | 看到别人对未写过页的修改 | 需要稳定副本时自己拷贝 | 第 7 篇 |
| 以为 `munmap`/退出会落盘 | 断电丢数据 | `msync(MS_SYNC)` | 第 9 篇 |
| 用 `MS_ASYNC` 当持久化 | 没有任何保证 | 用 `MS_SYNC` | 第 9 篇 |
| 从不检查 `msync`/`fsync` 返回值 | 写回 I/O 错误被忽略 | 检查返回值 | 第 9 篇 |
| `MAP_FIXED` 覆盖已有映射 | 悄悄破坏其他数据（比如某个库） | `MAP_FIXED_NOREPLACE`，或只覆盖自己预留的区域 | 第 6、9 篇 |
| 共享内存不做同步 | 数据竞争；ARM64 弱内存序下更易出错 | 原子操作 / 锁 | 第 8 篇 |
| 频繁 mmap/munmap 小区域 | TLB 击落、VMA 操作开销大 | 复用映射 | 第 10 篇 |
| 大量零散映射 | 撞上 `max_map_count`，返回 `ENOMEM` | 合并映射或调大限制 | 第 11 篇 |
| 认为 mmap 一定更快 | 顺序读或冷数据随机读反而更慢 | 按场景选择，实测 | 第 10 篇 |
| fork 后父进程大量写 | COW 导致内存突增 | 预留内存余量；减少 fork 后的写 | 第 7 篇 |

---

## 七、排查工具清单

| 工具 | 用途 |
|---|---|
| `strace -e trace=memory` | 查看程序调用的 mmap、munmap、mprotect、brk、madvise 等 |
| `cat /proc/PID/maps` | 进程的所有映射（VMA） |
| `cat /proc/PID/smaps`、`smaps_rollup` | 每个映射的 RSS、PSS、脏页、匿名页、交换量 |
| `pmap -X PID` | 以表格形式查看映射与内存统计 |
| `/usr/bin/time -v 命令` | 统计大缺页和小缺页次数 |
| `perf stat -e page-faults,major-faults,minor-faults` | 统计缺页事件 |
| `perf stat -e dTLB-load-misses`（事件名因 CPU 而异） | 观察 TLB 未命中 |
| `free -h`、`/proc/meminfo` | 页缓存、脏页、大页等全局情况 |
| `fincore 文件` | 查看一个文件有多少在页缓存中 |
| `vmstat 1` | 观察换入换出（si/so）、I/O、内存变化 |
| `cat /sys/kernel/mm/transparent_hugepage/enabled` | 透明大页设置 |
| `dmesg` | 查看段错误、OOM Killer 等内核日志 |
| `bpftrace` / `perf trace` | 深入跟踪内核中的缺页处理路径 |

---

## 八、全系列回顾：一张图串起所有概念

```
                               ┌────────────────────────────┐
                               │   用户程序（EL0）              │
                               │   p = mmap(...);  p[i] = x;  │   第 1、6 篇
                               └─────────────┬──────────────┘
                                             │ 普通的内存访问指令
                                             ▼
               ┌────────────────────── MMU（第 3 篇）─────────────────────┐
               │  查 TLB → 未命中则遍历四级页表（TTBR0_EL1 → L0→L1→L2→L3）   │
               │  页表项有效且权限允许？                                     │
               └───────┬──────────────────────────────────┬────────────┘
                     是 │                                  │ 否：缺页异常（第 4 篇）
                       ▼                                  ▼
             直接访问物理内存                   内核（EL1）：do_page_fault（第 11 篇）
             （与普通数组一样快）                查 VMA（mmap 登记的"菜单"）
                                                       │
                ┌──────────────┬───────────────┬───────┴──────┬──────────────────┐
                ▼              ▼               ▼              ▼                  ▼
          不在任何 VMA     匿名映射         文件映射·读      私有映射·写        共享映射·写
             SIGSEGV       （第 8 篇）       （第 5、6 篇）   （第 7 篇）         （第 9 篇）
                          零页 / 清零新页   查页缓存           复制一份私有页      标记脏页
                                          ├ 命中：小缺页     （写时复制）        稍后写回磁盘
                                          └ 未命中：读盘                       msync 强制落盘
                                            （大缺页）
                                          超出文件末尾：SIGBUS
                                                       │
                                                       ▼
                                      ┌────────────────────────────────┐
                                      │ 页缓存（address_space，第 5 篇）  │ ◀── read()/write() 也走这里
                                      │ 全系统每个文件页只有一份           │      所以两者天然一致
                                      └───────────────┬────────────────┘
                                                      │ 回写 / 预读 / 回收（第 5、11 篇）
                                                      ▼
                                                 磁盘上的文件

  性能调优（第 10 篇）：madvise · MAP_POPULATE · 大页 · mlock · 减少 TLB 击落
  真实世界（第 12 篇）：动态库加载 · 数据库 · 设备映射 · Firecracker 虚拟机 · userfaultfd
```

---

## 九、结语

回到第 1 篇开头那个看似简单的问题："程序是怎么读文件的？"

一路走来，我们发现 mmap 这一个系统调用背后，站着操作系统里最核心的一整套机制：

- **用户态与内核态**划定了安全边界；
- **虚拟内存与页表**让每个进程活在自己的世界里，也让"把文件放进地址空间"成为可能；
- **缺页异常**让一切都可以按需发生，于是映射 10GB 文件只需一瞬间；
- **页缓存**让文件内容在内存里只有一份，mmap 和 read 看到的是同一样东西；
- **写时复制**让共享与隔离兼得，fork 和程序加载因此变得廉价；
- 而**落盘、一致性、性能**这些现实问题，则提醒我们：没有免费的午餐，每一种便利都有它的代价。

mmap 的思想可以浓缩成一句话：

> **不要搬运数据，去改变看待数据的方式。**

不是把文件内容拷贝到程序里，而是调整页表，让程序"看到"文件本来所在的那块内存。理解了这一点，你再看到任何"映射"——内存映射 I/O、虚拟机的两阶段翻译、用户态驱动、零拷贝网络——都会觉得似曾相识。

---

## 本篇小结

| 场景 | mmap 扮演的角色 |
|---|---|
| 程序与动态库加载 | 私有文件映射 + 匿名 .bss + mprotect；代码页在所有进程间共享 |
| LMDB | 只读映射实现零拷贝读，写时复制 B+ 树保证一致性 |
| SQLite / Lucene / Kafka | 主要用于读，写入走 write |
| 数据库争论 | 事务安全、I/O 阻塞、错误处理、扩展性 vs 简洁与高读性能 |
| 设备映射 | 驱动用 remap_pfn_range 映射设备内存；ARM64 用 Device 内存属性 |
| 内核共享缓冲区 | io_uring、perf、AF_XDP 都用 mmap 共享环形队列 |
| Firecracker | 匿名 mmap 作客户机内存，注册给 KVM；ARM64 两阶段翻译；快照用 MAP_PRIVATE 或 userfaultfd 懒加载 |
| userfaultfd | 把缺页交给用户线程，用 UFFDIO_COPY 填页 |

（全系列完）
