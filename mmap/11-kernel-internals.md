# 第 11 篇｜内核视角：一次 mmap 调用在内核里走过的路

> **本篇目标**：钻进 Linux 内核，认识管理进程地址空间的两个核心数据结构 **`mm_struct`** 和 **VMA**；跟踪一次 mmap 系统调用和一次缺页异常在 **ARM64** 上的代码路径；理解页缓存的 `address_space`、反向映射与内存回收；最后读懂 `/proc/pid/smaps` 中的 RSS、PSS 等指标。
>
> 本篇会出现一些内核函数名。你不需要记住它们，它们的作用是给你一张"地图"：以后想读内核源码时，知道从哪里下手。内核在不断演进，具体函数名在不同版本间可能有调整，本文以较新的 6.x 内核为准。

---

## 一、从进程到地址空间

Linux 内核用一个叫 `task_struct` 的结构描述每一个进程（或线程）。它里面有一个指针 `mm`，指向一个 **`mm_struct`**，这个结构描述了进程的**整个用户地址空间**。

```
 task_struct（进程/线程）
   │
   └── mm ──▶ mm_struct（地址空间）
                ├── pgd          ─▶ 这个进程的顶级页表（L0 表）的地址
                ├── mm_mt        ─▶ 所有 VMA 组成的树（maple tree）
                ├── mmap_lock    ─▶ 保护这个地址空间的读写锁
                ├── mmap_base    ─▶ mmap 区域的起点（从这里往下分配）
                ├── map_count    ─▶ VMA 的数量
                ├── total_vm     ─▶ 总共映射了多少页
                └── rss_stat     ─▶ 实际占用的物理页统计（文件页、匿名页、共享内存页）
```

同一个进程里的多个**线程**共享同一个 `mm_struct`，这就是为什么线程之间天然共享内存。`fork` 出来的子进程则得到一个**新的** `mm_struct`，里面的 VMA 和页表是从父进程复制来的（第 7 篇的 COW）。

进程切换时，ARM64 内核会把新进程 `mm->pgd` 对应的物理地址写进 **TTBR0_EL1** 寄存器（同时带上它的 ASID），从此 CPU 就在新进程的"世界"里翻译地址（第 3 篇）。

---

## 二、VMA：地址空间的"菜单条目"

第 4 篇我们把 VMA 比作"菜单"。现在看看它的真面目：**`struct vm_area_struct`**，描述一段**连续的、属性相同的**虚拟地址区域。

```
 struct vm_area_struct
   ├── vm_start, vm_end   区域的起止虚拟地址 [vm_start, vm_end)
   ├── vm_mm              属于哪个 mm_struct
   ├── vm_flags           属性：VM_READ / VM_WRITE / VM_EXEC / VM_SHARED / VM_MAYWRITE ...
   ├── vm_page_prot       由 vm_flags 换算出的页表项权限位（ARM64 格式）
   ├── vm_file            如果是文件映射：指向哪个文件；匿名映射为 NULL
   ├── vm_pgoff           这段区域起点对应文件中的第几页
   ├── vm_ops             一组回调函数：发生缺页时调用谁、页面要被写时通知谁
   └── anon_vma           用于匿名页的反向映射（见第六节）
```

`/proc/pid/maps` 里的**每一行，就是一个 VMA**：

```
ffff8a400000-ffff8a5a0000 r-xp 00000000 fe:01 2071   /usr/lib/aarch64-linux-gnu/libc.so.6
│            │            │    │                      │
vm_start     vm_end       │    vm_pgoff × 页大小        vm_file
                          vm_flags（r-x，p = 没有 VM_SHARED）
```

### 2.1 VMA 的组织

一个进程可能有成百上千个 VMA。缺页时内核需要快速回答"这个地址落在哪个 VMA 里"，所以 VMA 被组织在一棵查找树中。从 6.1 版本开始，Linux 用一种叫 **maple tree** 的 B 树变体来存放 VMA（之前用的是红黑树加链表）。

### 2.2 VMA 的数量限制

每个进程的 VMA 数量有上限：

```bash
cat /proc/sys/vm/max_map_count
# 65530
```

如果一个程序创建了大量零散的映射（比如成千上万个小文件各自 mmap，或者频繁对不同小段 `mprotect` 导致 VMA 分裂），可能撞上这个上限，mmap 返回 `ENOMEM`——即使内存还很充裕。Elasticsearch 等大量使用 mmap 的软件会要求调大这个值。

### 2.3 VMA 的合并与分裂

- 新映射和相邻的已有 VMA 属性完全相同（同一个文件且偏移连续、权限相同等）时，内核会**合并**成一个 VMA；
- 对 VMA 中间一段做 `munmap` 或 `mprotect`，会把一个 VMA **分裂**成两个或三个。

---

## 三、mmap 系统调用的内核之旅

当你在 ARM64 上调用：

```c
p = mmap(NULL, size, PROT_READ, MAP_SHARED, fd, 0);
```

内核里大致发生了这些事：

```
 用户态：glibc 的 mmap() 把参数放进 x0~x5，调用号 222 放进 x8，执行 svc #0
   │
   ▼
 内核入口：el0_svc → 按 x8 查系统调用表
   │
   ▼
 arch/arm64/kernel/sys.c: sys_mmap(addr, len, prot, flags, fd, off)
   │   检查 off 是否页对齐，不对齐直接返回 -EINVAL（第 6 篇的那个错误）
   ▼
 ksys_mmap_pgoff()        根据 fd 找到 struct file，处理 MAP_HUGETLB 等
   ▼
 vm_mmap_pgoff()          安全检查（LSM），获取 mmap_lock（写锁）
   ▼
 do_mmap()                核心逻辑：
   │   ├─ 把 PROT_* 和 MAP_* 换算成 vm_flags
   │   ├─ 检查文件打开方式与权限是否匹配（第 7 篇的权限表就在这里检查）
   │   └─ get_unmapped_area()：在地址空间里找一段足够大的空白
   │        （默认从 mmap_base 往低地址方向找，即"自顶向下"布局）
   ▼
 mmap_region()            
   │   ├─ 如果新区域与旧映射重叠（MAP_FIXED），先把旧的解除映射
   │   ├─ 尝试与相邻 VMA 合并；不能合并就分配一个新的 vm_area_struct
   │   ├─ 调用文件的 mmap 回调：file->f_op->mmap(file, vma)
   │   │     例如 ext4 在这里设置 vma->vm_ops = &ext4_file_vm_ops，
   │   │     其中 .fault = filemap_fault（缺页时从页缓存取页）
   │   │          .map_pages = filemap_map_pages（fault-around 用）
   │   │          .page_mkwrite = ext4_page_mkwrite（页第一次被写时通知文件系统）
   │   ├─ 把 VMA 插入 mm 的 maple tree
   │   └─ 把 VMA 挂到文件的 i_mmap 树上（反向映射用，见第六节）
   ▼
 释放 mmap_lock
   │
   └─ 如果指定了 MAP_POPULATE：现在才逐页触发缺页、填满页表
   ▼
 返回起始地址
```

请注意整条路径里**缺席**的东西：没有读磁盘，没有分配物理页，没有填写页表（除非 `MAP_POPULATE`）。mmap 系统调用只做了一件事：**登记一个 VMA**。这正是第 4 篇"按需分页"在代码层面的体现。

### 3.1 文件系统和驱动的 mmap 回调

`file->f_op->mmap` 是一个非常重要的扩展点。不同类型的"文件"在这里决定自己被映射时的行为：

| 文件类型 | mmap 回调做什么 |
|---|---|
| 普通文件（ext4、XFS） | 设置 `vm_ops`，缺页时走页缓存 |
| tmpfs / 共享内存 | 设置 shmem 的 `vm_ops`，缺页时分配内存页 |
| 设备驱动（显卡、帧缓冲） | 通常直接调用 `remap_pfn_range()`，把设备的物理地址填进页表（第 12 篇） |
| 不支持映射的文件（如管道） | 没有 mmap 回调，mmap 返回 `ENODEV` |

---

## 四、缺页的内核之旅（ARM64）

现在程序访问 `p[0]`，页表项无效，触发缺页。

```
 用户态 EL0：ldr w0, [x1]       ← x1 = p
   │  MMU 翻译失败
   ▼
 硬件：FAR_EL1 = 出错地址，ESR_EL1 = 原因，ELR_EL1 = 出错指令地址
       切换到 EL1，跳到异常向量表中"来自 EL0 的同步异常"入口
   ▼
 el0t_64_sync_handler()  读 ESR 的异常类别（EC）字段：
   │   EC = 数据访问异常（Data Abort from lower EL）→ el0_da()
   │   EC = 指令访问异常（Instruction Abort）     → el0_ia()
   ▼
 do_mem_abort(far, esr, regs)
   │   根据 ESR 中的故障状态码（DFSC）查一张表 fault_info[]：
   │     "第 0~3 级翻译错误"   → do_translation_fault → do_page_fault
   │     "第 1~3 级权限错误"   → do_page_fault
   │     "第 0~3 级访问标志错误" → do_page_fault
   │     对齐错误、同步外部错误等 → 其他处理函数
   ▼
 do_page_fault()
   │   ├─ 从 ESR 判断这次是读、写还是取指
   │   ├─ 先尝试只锁住这一个 VMA（lock_vma_under_rcu，6.4+ 的按 VMA 加锁）
   │   │   不行再退回到获取 mmap_lock 读锁
   │   ├─ 找到地址所在的 VMA；找不到 → SIGSEGV
   │   ├─ 检查访问类型是否被 VMA 允许（往只读 VMA 写？）；不允许 → SIGSEGV
   │   └─ handle_mm_fault(vma, addr, flags)
   ▼
 __handle_mm_fault()
   │   逐级找到（必要时分配）L0 → L1 → L2 页表；
   │   如果这是可以用大页的区域，可能在 L2 这一级直接处理 2MB 大页
   ▼
 handle_pte_fault()        到达 L3 页表项，按情况分派：
   │
   ├─ 页表项为空 + 匿名 VMA        → do_anonymous_page()
   │      读：映射全局零页；写：分配清零的新页              （第 8 篇）
   │
   ├─ 页表项为空 + 文件 VMA        → do_fault()
   │      ├─ 读访问               → do_read_fault()
   │      │     先 do_fault_around()：把附近已在页缓存的页一起映射（第 6 篇）
   │      │     再调用 vma->vm_ops->fault，即 filemap_fault()
   │      ├─ 写访问 + 私有映射     → do_cow_fault()
   │      │     从页缓存取页，复制一份新的匿名页再映射       （第 7 篇）
   │      └─ 写访问 + 共享映射     → do_shared_fault()
   │            取页后调用 page_mkwrite 通知文件系统，标记脏页 （第 9 篇）
   │
   ├─ 页表项存在但"不在内存"（指向交换区） → do_swap_page()，从 swap 读回
   │
   └─ 页表项存在，写访问但只读       → do_wp_page()
          私有页被多方共享 → 写时复制；只有自己在用 → 直接改成可写
          共享文件页 → 调用 page_mkwrite，标记脏页，改成可写
   ▼
 filemap_fault()（文件读缺页的核心）
   │   ├─ 在文件的页缓存（address_space）里查找这一页
   │   ├─ 找到且数据有效 → 小缺页
   │   └─ 没找到 → 触发同步预读，分配页、发起磁盘 I/O，进程睡眠等待 → 大缺页
   ▼
 设置页表项（写入物理页地址和权限位），必要时维护 TLB
   ▼
 逐层返回，执行 eret，回到 ELR_EL1 指向的指令重新执行
```

把这张图和第 4、6、7、8、9 篇对照着看，你会发现前面讲过的每一种情况，在内核里都有明确对应的处理函数。

### 4.1 关于 folio

阅读较新的内核代码时，你会频繁看到 **folio** 这个词。它是内核对"一个或多个物理连续页组成的一块内存"的抽象。以前页缓存和匿名内存都以单个 4KB `struct page` 为单位管理，引入 folio 之后，内核可以更自然地以 16KB、64KB、2MB 等更大的单位管理内存，这也是文件 mmap 能使用大页的基础。初学时，把 folio 理解为"页"即可。

---

## 五、页缓存：address_space

第 5 篇说每个文件有一个"缓存目录"。在内核里，它是 **`struct address_space`**，每个文件的 inode 都有一个（`inode->i_mapping`）：

```
 struct address_space
   ├── i_pages      ─▶ 一棵 xarray 树：文件页号 → 缓存的 folio
   ├── i_mmap       ─▶ 一棵区间树：所有映射了这个文件的 VMA
   ├── a_ops        ─▶ 文件系统提供的操作：如何从磁盘读一页、如何把脏页写回
   └── nrpages      ─▶ 当前缓存了多少页
```

- `read()` 和 mmap 缺页都通过 `i_pages` 查找页面，这就是两者共享同一份缓存的原因；
- `i_mmap` 记录了"谁映射了我"，这是下一节反向映射的关键；
- `a_ops` 让页缓存与具体文件系统解耦：ext4、XFS、NFS 各自实现如何读写。

---

## 六、反向映射：这一页被谁映射了？

### 6.1 为什么需要反向

页表是"正向"的：给一个虚拟地址，查出物理页。但内核有时需要回答相反的问题：

> **给我一个物理页，告诉我它被哪些进程的哪些虚拟地址映射了。**

什么时候需要？

- **内存回收**：要把一个页从内存里踢出去，必须先把**所有**指向它的页表项都清除，否则进程会访问到一个已经被挪作他用的物理页；
- **页面迁移**：在 NUMA 系统里把页挪到离 CPU 更近的内存节点，或者为了拼出大页而整理碎片，都要更新所有映射；
- **文件被截断**：第 9 篇的 SIGBUS 实验里，截断文件后内核要把所有映射了被截掉部分的页表项清除。

### 6.2 怎么做

Linux 的反向映射（rmap）分两种情况：

- **文件页**：从页找到它所属文件的 `address_space`，再遍历 `i_mmap` 树里所有覆盖这个文件偏移的 VMA，在每个 VMA 对应的页表里找到并清除那个页表项；
- **匿名页**：每个匿名页记录一个 `anon_vma` 指针，`anon_vma` 把可能映射这个页的所有 VMA 串在一起（包括 fork 出来的父子进程的 VMA）。

反向映射的遍历本身有开销。一个被成千上万个进程映射的页（比如 libc 的代码页），回收它要清除成千上万个页表项。

---

## 七、内存回收与换出

当空闲内存不足时，内核的后台线程 **kswapd** 会被唤醒，开始回收页面（内存极度紧张时，正在申请内存的进程也会亲自参与回收，称为"直接回收"）。

回收的大致过程：

1. 从 LRU 链表的"不活跃"一端挑选页面；
2. 检查页表项的**访问标志**（ARM64 页表项中的 AF 位）：最近被访问过的页，给它"第二次机会"，移回活跃链表；
   - ARMv8.1 起支持硬件自动设置 AF 位；不支持时，内核会先清除 AF，下次访问时触发一次"访问标志错误"缺页来得知"它被访问了"；
3. 通过反向映射，清除所有指向该页的页表项（并作废 TLB）；
4. 根据页的类型处理：
   - **干净的文件页**：磁盘上有一样的内容，直接丢弃；
   - **脏的文件页**：先写回磁盘，再丢弃；
   - **匿名页**：写入交换区（swap），页表项改为记录交换区位置；没有 swap 就无法回收；
5. 物理页归还给空闲内存池。

之后进程再访问这些地址，会触发缺页：文件页从磁盘重新读回（大缺页），匿名页从 swap 读回（`do_swap_page`）。

如果回收也救不回来，内核会启动 **OOM Killer**，根据内存占用等因素选出一个进程杀掉（第 4 篇）。

> 对 mmap 来说这意味着：**文件映射是"可回收"的内存**。你 mmap 了一个 100GB 的文件并读遍了它，并不会导致内存耗尽——内核会在内存紧张时悄悄回收那些已经不常用的页，等你再访问时重新读入。代价是可能出现大量大缺页，性能下降。

---

## 八、实验：读懂 /proc/pid/smaps

`/proc/pid/maps` 只告诉你有哪些 VMA；`/proc/pid/smaps` 则给出每个 VMA 的**详细内存统计**。

### 8.1 实验程序

```c
// smaps_demo.c —— 映射一个文件并读遍，再申请并写满一块匿名内存，然后暂停
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>

int main(int argc, char *argv[]) {
    if (argc != 2) { fprintf(stderr, "用法: %s 文件名\n", argv[0]); return 1; }
    long page = sysconf(_SC_PAGESIZE);

    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }
    struct stat st;
    fstat(fd, &st);
    char *f = mmap(NULL, st.st_size, PROT_READ, MAP_SHARED, fd, 0);
    if (f == MAP_FAILED) { perror("mmap"); return 1; }
    volatile char sink = 0;
    for (off_t i = 0; i < st.st_size; i += page) sink += f[i];   // 读遍文件映射

    size_t anon_size = 32 << 20;                                 // 32MB 匿名内存
    char *a = mmap(NULL, anon_size, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (a == MAP_FAILED) { perror("mmap"); return 1; }
    memset(a, 1, anon_size);                                     // 写满

    printf("PID %d，文件映射 %p，匿名映射 %p。按回车退出\n", getpid(), (void *)f, (void *)a);
    getchar();
    return 0;
}
```

```bash
dd if=/dev/urandom of=data64.bin bs=1M count=64
gcc smaps_demo.c -o smaps_demo

# 终端 1 和终端 2 各运行一个实例
./smaps_demo data64.bin
```

### 8.2 查看文件映射的统计

在第三个终端里：

```bash
PID=$(pgrep -n smaps_demo)
grep -A 22 data64.bin /proc/$PID/smaps
```

输出类似（截取主要字段）：

```
ffff7c000000-ffff80000000 r--s 00000000 fe:01 393301   /home/you/data64.bin
Size:              65536 kB
Rss:               65536 kB
Pss:               32768 kB
Shared_Clean:      65536 kB
Shared_Dirty:          0 kB
Private_Clean:         0 kB
Private_Dirty:         0 kB
Referenced:        65536 kB
Anonymous:             0 kB
Swap:                  0 kB
```

| 字段 | 含义 | 本例解读 |
|---|---|---|
| `Size` | VMA 的大小（虚拟） | 映射了 64MB |
| `Rss` | 这段区域中**实际在物理内存里**的部分（Resident Set Size） | 64MB 都已调入 |
| `Pss` | 按共享人数**分摊**后的占用（Proportional Set Size） | 两个进程共享，每人分摊 32MB |
| `Shared_Clean` | 和其他进程共享、且干净的页 | 页缓存页被两个进程共享 |
| `Private_Dirty` | 只有自己在用、且被修改过的页 | 0（只读映射） |
| `Anonymous` | 匿名页的量 | 0（这是文件映射） |
| `Swap` | 被换出到交换区的量 | 0 |

**RSS 与 PSS 的区别**是理解"一个进程到底占了多少内存"的关键：

- 把所有进程的 RSS 加起来，共享的页会被**重复计算**，总和可能远大于实际物理内存；
- 把所有进程的 PSS 加起来，正好等于这些进程实际占用的物理内存总量。

如果只运行一个实例，你会看到 `Pss` 等于 `Rss`，`Shared_Clean` 变为 0 而 `Private_Clean` 变为 64MB——"私有"在这里的意思只是"当前只有我一个进程映射了它"，和 `MAP_PRIVATE` 不是一回事。

### 8.3 查看匿名映射的统计

在 smaps 里找到程序打印出的匿名映射地址那一段：

```
Size:              32768 kB
Rss:               32768 kB
Pss:               32768 kB
Private_Dirty:     32768 kB
Anonymous:         32768 kB
AnonHugePages:     30720 kB      ← 如果启用了透明大页，大部分可能是 2MB 大页
```

匿名内存写过之后全部是 `Private_Dirty`：它只属于这个进程，而且没有磁盘原件，回收时只能换出。

### 8.4 更方便的工具

```bash
cat /proc/$PID/smaps_rollup     # 整个进程的汇总
pmap -X $PID                    # 表格形式展示每个映射的 RSS、PSS、脏页等
```

### 8.5 （选做）观察内核里的缺页处理

如果安装了 bpftrace，可以统计某个程序的缺页在内核中的调用次数：

```bash
sudo bpftrace -e 'kprobe:handle_mm_fault /comm == "smaps_demo"/ { @faults = count(); }'
# 在另一个终端运行 ./smaps_demo data64.bin，回车退出后按 Ctrl-C 结束 bpftrace
```

还可以把 `handle_mm_fault` 换成 `filemap_fault`、`do_anonymous_page`（若内核符号可见）等，看看文件映射和匿名映射分别走了哪条路径。

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| `mm_struct` | 一个进程的完整用户地址空间，包含页表根、VMA 树和锁 |
| VMA | 一段属性相同的连续虚拟地址区域，maps 文件中的一行 |
| maple tree | 6.1+ 内核组织 VMA 的数据结构 |
| `max_map_count` | 每个进程 VMA 数量上限，默认 65530 |
| mmap 系统调用 | 找空白地址、创建 VMA、调用文件的 mmap 回调，不分配物理内存 |
| `vm_ops` | 文件系统/驱动提供的回调，决定缺页时如何取页 |
| ARM64 缺页路径 | el0_da → do_mem_abort → do_page_fault → handle_mm_fault → 按情况分派 |
| `filemap_fault` | 文件读缺页核心：查页缓存，必要时读盘 |
| `address_space` | 文件的页缓存，含页索引、映射者列表和读写方法 |
| 反向映射 | 从物理页找到所有映射它的页表项，用于回收、迁移、截断 |
| 内存回收 | kswapd 按 LRU 和 AF 位挑页，干净文件页直接丢，匿名页换出 |
| RSS / PSS | RSS 是驻留量（共享重复计算），PSS 是按共享人数分摊后的量 |

**下一篇预告**：[《真实世界里的 mmap：谁在用、怎么用、踩过哪些坑》](12-real-world.md)。系列最后一篇，我们会看到 mmap 在动态链接器、数据库、设备驱动、虚拟机（Firecracker）中的真实用法，认识让用户程序接管缺页的 `userfaultfd`，并用一张图把整个系列串起来。
