# 第 10 篇｜性能真相：mmap 一定比 read 快吗？

> **本篇目标**：打破"mmap 零拷贝所以一定更快"的迷思。系统地分析 mmap 省掉了什么、又额外付出了什么；理解缺页开销、TLB 击落、预读；学会使用 `madvise`、`MAP_POPULATE`、大页和 `mlock` 调优；并亲手写一个基准测试。

---

## 一、一个流行的说法

在网上搜索 mmap，你经常会看到这样的说法：

> "read 需要把数据从内核拷贝到用户空间，而 mmap 是零拷贝，所以 mmap 比 read 快。"

这句话**只说对了一半**。mmap 确实省掉了拷贝，但它也引入了 read 没有的开销。哪个更快，**取决于场景**。

我们先算清楚两边的账。

---

## 二、mmap 省掉了什么

### 2.1 数据拷贝

`read` 每读一字节都要从页缓存拷贝到用户缓冲区（第 5 篇）。现代 CPU 拷贝内存的速度大约是每秒十几到几十 GB，单核拷贝 1GB 数据需要几十毫秒，同时还会把 CPU 缓存"冲刷"一遍。mmap 没有这部分开销。

### 2.2 系统调用

`read` 每次调用都要切换到内核态再切回来（第 1 篇）。mmap 映射建立之后，访问数据完全不需要系统调用。

### 2.3 内存占用

`read` 时，数据在页缓存里有一份，在你的缓冲区里又有一份。如果 100 个进程都 `read` 同一个 1GB 文件到自己的缓冲区，就是 100GB + 1GB。而 100 个进程 mmap 同一个文件，只占用页缓存里的那 1GB。

### 2.4 编程便利

随机访问直接用下标，解析复杂格式不用操心缓冲区边界。这虽然不是"性能"，但常常间接带来性能：更简单的代码更容易优化。

---

## 三、mmap 额外付出了什么

### 3.1 缺页开销

`read` 的数据通路里没有缺页（读到的缓冲区通常早已在内存中）。mmap 的每个页第一次被访问时都要经历一次缺页异常：

- 从用户态陷入内核（类似一次系统调用的开销）；
- 查找 VMA、查找页缓存、加锁、修改页表；
- 返回用户态，重新执行指令。

一次小缺页通常需要**零点几到一两微秒**。对 4KB 一页来说，这相当于每 4KB 数据付出一次"系统调用级"的开销。

对比：`read` 用 1MB 的缓冲区读一个已缓存的文件，每 1MB 才一次系统调用；而 mmap 即使有 fault-around（第 6 篇，每 64KB 一次缺页），每 1MB 也要 16 次缺页。所以**顺序读一个大文件时，mmap 的缺页开销可能抵消甚至超过它省下的拷贝开销**。

### 3.2 页表的建立与销毁

每映射一页，就要填一个页表项；`munmap` 时要逐一清除。映射 10GB 文件并全部访问，意味着要创建约 260 万个页表项（4KB 页），页表本身就要占约 20MB 内存。

### 3.3 TLB 压力与 TLB 击落

**TLB 未命中**：第 3 篇讲过，TLB 只能缓存有限的翻译结果。在一个巨大的映射区域里随机跳转访问，TLB 会频繁未命中，每次都要做一次四级页表遍历。

**TLB 击落（shootdown）**：当 `munmap`、`mprotect` 或内核回收页面时，需要作废所有 CPU 核上相关的 TLB 条目。

- 在 x86 上，这需要给其他核发送**处理器间中断（IPI）**，让它们各自作废，开销很大；
- 在 ARM64 上，可以用带 `IS`（Inner Shareable）后缀的 `TLBI` 指令由硬件**广播**作废请求，再用 `DSB ISH` 等待完成，不需要打断其他核，这比 IPI 便宜得多。但当需要作废的范围很大、核数很多时，代价依然可观。ARMv8.4 引入的 TLB 范围作废指令（TLBI RVAE1IS 等）进一步降低了大范围作废的成本。

如果你的程序频繁地 mmap/munmap 小块区域（比如每处理一个请求就映射一次文件），这些开销会累积起来。

### 3.4 锁竞争

一个进程的所有映射由一个结构（`mm_struct`，第 11 篇）统一管理。历史上，缺页处理和 mmap/munmap 都要获取同一把锁（`mmap_lock`）。在多线程程序里，一个线程在做 mmap/munmap 时，其他线程的缺页处理可能被迫等待。

较新的内核（6.4 起）引入了**按 VMA 加锁**（per-VMA lock），大多数缺页不再需要全局锁，这个问题已大大缓解。

### 3.5 I/O 无法并行、无法异步

当数据不在页缓存中时，mmap 的访问会触发**大缺页**，线程**同步阻塞**直到这一页从磁盘读回。

- 一个线程同一时刻只能等待一个缺页，无法同时发出多个读请求；
- 程序也无法在等待时去做别的事情。

而用 `pread` 配合多线程、或者 Linux 的 `io_uring`，程序可以同时发出几十上百个读请求，充分利用 NVMe SSD 的并行能力。在"数据不在内存、随机读"的场景下，这个差距可能达到数倍到数十倍。

### 3.6 错误处理

第 9 篇讲过，mmap 的 I/O 错误以 SIGBUS 的形式出现，处理起来比检查 `read` 的返回值麻烦得多。这不直接影响速度，但影响工程上的取舍。

---

## 四、场景分析

把上面两份账放在一起，可以得到一个粗略的判断：

| 场景 | 更可能占优的一方 | 原因 |
|---|---|---|
| 顺序读大文件，读一遍就扔 | **read**（大缓冲区）或二者持平 | mmap 的缺页开销抵消了省下的拷贝；read 的预读和大缓冲区很高效 |
| 数据已在内存，**随机小块**访问，反复多次 | **mmap** | 每次访问只是普通内存读，没有系统调用 |
| 多个进程共享同一份只读数据 | **mmap** | 只占一份内存 |
| 数据不在内存，随机读，需要高并发 I/O | **pread + 多线程 / io_uring** | mmap 的缺页是同步阻塞的 |
| 需要精确控制写入时机和顺序 | **write + fsync** | mmap 无法控制内核何时写回 |
| 解析复杂的二进制格式（如可执行文件、索引） | **mmap** | 编程简单，随机访问方便 |
| 频繁映射/解除映射小文件 | **read** | mmap 建立和销毁映射的固定开销较大 |

---

## 五、调优手段

### 5.1 预读与 madvise

内核默认会根据访问模式猜测要不要预读（第 5 篇）。对于 mmap，你可以用 `madvise` 主动告诉内核你打算怎么访问：

```c
int madvise(void *addr, size_t length, int advice);
```

常用的 `advice`：

| 建议 | 含义 | 适用场景 |
|---|---|---|
| `MADV_NORMAL` | 默认行为 | — |
| `MADV_SEQUENTIAL` | 我会顺序访问 | 内核加大预读，并更积极地回收已经读过的页 |
| `MADV_RANDOM` | 我会随机访问 | 内核关闭预读，避免读入用不到的数据 |
| `MADV_WILLNEED` | 我马上要用这段数据 | 内核**异步**开始把它读入页缓存，调用立即返回 |
| `MADV_DONTNEED` | 我暂时不用这段数据 | 立刻解除这段的页表映射；对私有匿名内存来说，物理页被释放，下次访问得到全 0 的新页 |
| `MADV_FREE` | 这段匿名内存可以回收（Linux 4.5+） | 比 DONTNEED 更"懒"：内存紧张时才真正回收；如果回收前你又写了，就保留 |
| `MADV_HUGEPAGE` / `MADV_NOHUGEPAGE` | 希望 / 不希望使用透明大页 | 见 5.3 节 |
| `MADV_POPULATE_READ` / `MADV_POPULATE_WRITE` | 立即为这段区域完成缺页（Linux 5.14+） | 提前付清缺页开销 |

示例：

```c
char *p = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);

madvise(p, size, MADV_SEQUENTIAL);           // 顺序扫描整个文件
// 或者
madvise(p, size, MADV_RANDOM);               // 像数据库索引那样随机查找
// 或者
madvise(p + off, 64 << 20, MADV_WILLNEED);   // 提前把接下来要用的 64MB 读进来
```

> `madvise` 只是"建议"，内核可以忽略。它也不会改变程序的正确性（`MADV_DONTNEED`、`MADV_FREE` 这类会丢弃数据的除外，要小心使用）。

### 5.2 MAP_POPULATE：映射时就付清缺页

```c
char *p = mmap(NULL, size, PROT_READ, MAP_PRIVATE | MAP_POPULATE, fd, 0);
```

内核在 mmap 返回之前，就把整个区域的页全部读入并填好页表。好处是之后的访问不会再有缺页，延迟稳定；代价是 mmap 本身变慢了，而且如果你最终只用到一小部分，就白白浪费了时间和内存。

适合"马上就要全部用到"、或者"对后续访问延迟非常敏感"的场景。

### 5.3 大页

第 3 篇讲过，ARM64 页表的 L2、L1 条目可以直接映射一大块内存。把它用起来就是**大页**：

| ARM64 粒度 | 普通页 | 常用大页 | 更大的页 |
|---|---|---|---|
| 4KB 粒度 | 4KB | 2MB（L2 块） | 1GB（L1 块） |
| 16KB 粒度 | 16KB | 32MB | — |
| 64KB 粒度 | 64KB | 512MB | — |

此外，ARM64 页表项还有一个"**连续位**"（contiguous bit）：如果 16 个相邻的 4KB 页表项指向物理上连续、权限相同的内存，可以打上这个标记，TLB 就能用**一个条目**覆盖 64KB。较新的 Linux 内核（6.9 起）会利用它来支持"多尺寸透明大页"（mTHP）。

大页的好处：

- **TLB 覆盖面大幅增加**：一个 2MB 条目顶 512 个 4KB 条目。对随机访问大块内存的程序（数据库、科学计算、虚拟机），TLB 未命中率会显著下降；
- **页表更小，缺页更少**：一次缺页处理 2MB 而不是 4KB。

坏处：

- **内存浪费**：只用了 1 字节，也要占 2MB；
- **分配困难**：需要 2MB **物理上连续**的内存，系统运行久了内存碎片化，可能分配不到；
- **COW 代价**：大页的写时复制要复制 2MB。

Linux 有两种使用大页的方式：

**方式一：透明大页（THP，Transparent Huge Pages）**

内核自动尝试用大页。查看和设置：

```bash
cat /sys/kernel/mm/transparent_hugepage/enabled
# always [madvise] never      ← 方括号是当前值
```

- `always`：所有匿名内存都尝试用大页；
- `madvise`：只对调用了 `madvise(MADV_HUGEPAGE)` 的区域使用；
- `never`：关闭。

内核还有一个后台线程 `khugepaged`，会把零散的小页"合并"成大页。

THP 主要用于**匿名内存**。对于普通文件的 mmap，较新的内核和文件系统（如 XFS、ext4 支持"大 folio"之后）也能在页缓存中使用更大的页并以大页方式映射，但支持程度因内核版本和文件系统而异。

**方式二：hugetlbfs（显式大页）**

管理员预先保留一批大页，程序显式申请：

```bash
echo 512 | sudo tee /proc/sys/vm/nr_hugepages     # 预留 512 个 2MB 大页 = 1GB
grep Huge /proc/meminfo
```

```c
void *p = mmap(NULL, 1 << 30, PROT_READ | PROT_WRITE,
               MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, -1, 0);
```

这种方式稳定可靠，不会因为碎片分配失败（因为是预留的），但需要提前规划，内存也被专门占用。数据库和虚拟机（例如给 Firecracker 的客户机内存使用大页）常用这种方式。

### 5.4 mlock：把页钉在内存里

```c
mlock(p, size);       // 锁定这段区域：所有页立即调入内存，并且不会被换出或回收
munlock(p, size);
mlockall(MCL_CURRENT | MCL_FUTURE);   // 锁定进程的全部内存
```

适用于对延迟极度敏感的程序（实时音频、高频交易），或者存放密钥等不希望被换出到磁盘的敏感数据。受 `RLIMIT_MEMLOCK` 限制，普通用户能锁定的量通常很小。

### 5.5 减少映射/解除映射的次数

- 长期复用同一个映射，而不是每次用都重新 mmap；
- 一次映射大的范围，而不是很多次小映射；
- 避免频繁 `mprotect`，它和 munmap 一样需要作废 TLB。

---

## 六、动手：写一个基准测试

下面的程序对比四种方式读取同一个文件（假设文件已在页缓存中）：

```c
// bench.c —— 对比 read 与 mmap（请先让文件进入页缓存：cat 文件 > /dev/null）
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <time.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>

static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

static uint64_t sum(const uint8_t *p, size_t n) {
    uint64_t s = 0;
    for (size_t i = 0; i < n; i++) s += p[i];
    return s;
}

static uint8_t buf[1 << 20];          // 1MB 缓冲区

int main(int argc, char *argv[]) {
    if (argc != 2) { fprintf(stderr, "用法: %s 文件名\n", argv[0]); return 1; }
    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }
    struct stat st;
    fstat(fd, &st);
    size_t size = st.st_size;
    long page = sysconf(_SC_PAGESIZE);
    size_t npages = size / page;
    const int OPS = 500000;           // 随机访问次数
    uint64_t s;
    double t;

    // 1. read 顺序读（1MB 缓冲区）
    t = now(); s = 0;
    off_t off = 0;
    ssize_t n;
    while ((n = pread(fd, buf, sizeof buf, off)) > 0) { s += sum(buf, n); off += n; }
    printf("read  顺序: %7.3f s  (校验和 %" PRIu64 ")\n", now() - t, s);

    // 2. mmap 顺序读（含映射、缺页、解除映射的全部开销）
    t = now();
    uint8_t *p = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    s = sum(p, size);
    munmap(p, size);
    printf("mmap  顺序: %7.3f s  (校验和 %" PRIu64 ")\n", now() - t, s);

    // 3. pread 随机读：每次在随机页上读 64 字节
    srand(1); t = now(); s = 0;
    for (int i = 0; i < OPS; i++) {
        off_t o = (off_t)(rand() % npages) * page;
        pread(fd, buf, 64, o);
        s += sum(buf, 64);
    }
    printf("pread 随机: %7.3f s  (校验和 %" PRIu64 ")\n", now() - t, s);

    // 4. mmap 随机读：同样的访问序列
    p = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    madvise(p, size, MADV_RANDOM);
    for (int round = 1; round <= 2; round++) {
        srand(1); t = now(); s = 0;
        for (int i = 0; i < OPS; i++) {
            size_t o = (size_t)(rand() % npages) * page;
            s += sum(p + o, 64);
        }
        printf("mmap  随机(第%d轮): %7.3f s  (校验和 %" PRIu64 ")\n", round, now() - t, s);
    }
    munmap(p, size);
    close(fd);
    return 0;
}
```

```bash
dd if=/dev/urandom of=bench.bin bs=1M count=2048    # 2GB 测试文件
cat bench.bin > /dev/null                            # 预热：确保在页缓存中
gcc -O2 bench.c -o bench
./bench bench.bin
```

你可能会观察到这样的规律（具体数值随机器、内核版本、页大小、是否启用大页而大幅变化，请以自己的测量为准）：

1. **顺序读**：read 和 mmap 的差距不大，有时 read 甚至更快。mmap 省掉了拷贝，但付出了几万次缺页；
2. **pread 随机读**：每次访问都是一次系统调用加一次小拷贝；
3. **mmap 随机读第 1 轮**：很多页是第一次被访问，需要缺页，开销与 pread 相近；
4. **mmap 随机读第 2 轮**：大多数页已在页表中，访问就是纯粹的内存读，**明显快于 pread**——这正是 mmap 最擅长的场景。

可以进一步尝试：

- 去掉 `cat bench.bin > /dev/null` 并先清空缓存，观察冷数据下的差异；
- 在顺序读的 mmap 上加 `MAP_POPULATE` 或 `madvise(MADV_SEQUENTIAL)`；
- 用 `perf stat -e page-faults,dTLB-load-misses ./bench bench.bin` 观察缺页和 TLB 未命中的次数（不同 CPU 支持的事件名可能不同，可用 `perf list` 查看）。

---

## 七、一张决策图

```
              你的数据会被反复访问吗？
                 │
        ┌────────┴────────┐
       否                  是
        │                  │
  顺序读一遍？          数据能放进内存吗？
        │                  │
   用 read +         ┌─────┴─────┐
   大缓冲区         能             不能
   （或 mmap +       │              │
    MADV_SEQUENTIAL）│        随机访问且需要高并发 I/O？
                     │              │
               用 mmap 很合适   ┌────┴────┐
               （考虑大页、      是         否
                madvise）       │          │
                          pread/io_uring  mmap 可以，
                          + 自己管理缓存   但注意缺页阻塞
```

还有一个不在图里但同样重要的问题：**你需要精确控制数据何时落盘吗？** 如果需要（比如实现一个数据库），请认真阅读第 9 篇和第 12 篇的讨论，再决定是否让 mmap 负责写入。

---

## 本篇小结

| 要点 | 说明 |
|---|---|
| mmap 的收益 | 省拷贝、省系统调用、多进程共享一份内存、编程方便 |
| mmap 的成本 | 缺页、页表建立与销毁、TLB 未命中与击落、锁竞争、同步阻塞 I/O、SIGBUS |
| ARM64 TLB 击落 | `TLBI ... IS` 硬件广播，不需要 IPI，但大范围作废仍有成本 |
| 顺序读 | mmap 未必比大缓冲区 read 快 |
| 热数据随机读 | mmap 的主场 |
| 冷数据随机读 | 需要并发 I/O 时，pread/io_uring 更合适 |
| madvise | SEQUENTIAL / RANDOM / WILLNEED / DONTNEED / HUGEPAGE / POPULATE |
| MAP_POPULATE | 映射时预先完成所有缺页 |
| 大页 | ARM64 4KB 粒度下有 2MB / 1GB 块和 64KB 连续位；THP 自动、hugetlbfs 显式 |
| mlock | 锁定页，避免换出和缺页延迟 |

**下一篇预告**：[《内核视角：一次 mmap 调用在内核里走过的路》](11-kernel-internals.md)。我们将钻进 Linux 内核，看 `mm_struct` 和 VMA 如何组织一个进程的地址空间，跟踪一次 mmap 系统调用和一次缺页在 ARM64 上的完整代码路径，并学会读懂 `/proc/pid/smaps` 里的 RSS、PSS 等指标。
