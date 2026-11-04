# 大纲

**读者**：会一点编程（能看懂简单的 C 代码）、但没学过操作系统的新手。
**写法**：从现实问题出发，先讲“为什么需要”，再讲“是什么”，最后讲“怎么用、坑在哪”。每篇都有比喻、文字图和可以自己跑的小实验。
**约定**：代码用 C + Linux；涉及硬件细节（页表、MMU 等）时以 ARM64（aarch64）为例，必要时对比 x86；涉及虚拟机监控程序时以 Firecracker 为例。
**规模**：12 篇，每篇约 3500～6000 字。

## 第一部分　打地基：为什么需要 mmap

### 第 1 篇　从读一个文件说起

- `cat` 是怎么把文件内容打印出来的
- 用户态与内核态（ARM64 的 EL0～EL3），门卫由硬件把守
- 系统调用：`svc` 指令、调用号放 `x8`、参数放 `x0`～`x5`
- 文件描述符；写一个迷你 `cat`
- 一次 `read` 背后数据搬了几次，拷贝与切换的代价
- 实验：`dd` 不同块大小的耗时对比；`strace cat`
- 引子：能不能让文件像数组一样直接出现在内存里

### 第 2 篇　内存到底是什么

- 字节与地址，指针的本质
- 存储层级与速度差距，缓存行与局部性
- 物理地址空间，MMIO
- 实验：两个进程在同一地址存不同的值
- 为什么不能直接用物理地址：踩踏、隔离、碎片、重定位、容量

### 第 3 篇　虚拟内存

- 页与页帧，地址拆成页号与页内偏移；ARM64 的 4K/16K/64K 粒度
- ARM64 四级页表，页表项标志位，块映射
- MMU、TTBR0/TTBR1、TLB、TLB 击落、ASID
- 进程地址空间布局；读懂 `/proc/self/maps`

### 第 4 篇　缺页异常

- 按需分页；ARM64 上缺页的完整流程（FAR/ESR/ELR，指令重新执行）
- VMA（“菜单”）与页表的区别
- 五种情况：匿名清零、已缓存文件页、读盘、写只读页、段错误
- 小缺页与大缺页
- 实验：`malloc` 1GB 不等于占用 1GB；制造段错误并读 dmesg

### 第 5 篇　页缓存

- 以文件为单位组织，全系统每页一份
- `read` 的完整过程，预读
- `write` 与脏页、回写时机、`fsync`
- `free` 里的 buff/cache 与 available
- 实验：冷热缓存对比、`fincore`、观察脏页
- `O_DIRECT`
- 关键领悟：`read` 拷贝页缓存，mmap 直接映射页缓存

## 第二部分　认识 mmap：是什么、怎么用

### 第 6 篇　mmap 登场

- 参数逐个讲：`addr`、`length`、`prot`、`flags`、`fd`、`offset`；`MAP_FAILED`；`munmap`
- 程序：用 mmap 统计行数；用 mmap 原地改文件
- 一条时间线：mmap 什么都不读，缺页才读；fault-around
- 映射超出文件末尾：末页补 0，整页越界 SIGBUS
- 新手常见错误清单，映射文件中间任意位置

### 第 7 篇　共享还是私有

- `MAP_SHARED` 与 `MAP_PRIVATE` 的直观区别
- 写时复制在页表层面的实现，按页复制
- 实验：fork 后子进程写，父进程看；私有映射不是快照
- fork 如何靠 COW 变快，COW 的副作用
- 文件打开方式与映射权限的组合，`mprotect`

### 第 8 篇　匿名映射

- `MAP_ANONYMOUS`，零页，初始全 0，匿名页只能换出
- `malloc` 的 `brk` 与 mmap 两条途径；线程栈与保护页
- `MAP_SHARED | MAP_ANONYMOUS` 父子共享计数器
- tmpfs、`/dev/shm`、`shm_open`、`memfd_create` 与封印
- ARM64 弱内存序：共享内存通信必须用原子操作或锁

### 第 9 篇　数据什么时候真正落盘

- 写入后的数据在页缓存；内核如何追踪 mmap 写入
- `msync` 的 `MS_SYNC` 与 `MS_ASYNC`，`fsync`
- `munmap`、进程退出、断电分别意味着什么
- 崩溃一致性：写回顺序不可控、撕裂写；WAL 与写时复制数据结构
- 错误如何报告；SIGBUS 的成因、实验与预防
- 混用 `read`/`write` 与 mmap；改变文件大小的三种做法

## 第三部分　深入与实战：为什么、何时用

### 第 10 篇　性能真相

- mmap 省掉了什么、多付出了什么（缺页、页表、TLB、锁、同步 I/O）
- ARM64 的 `TLBI ... IS` 广播与 x86 IPI
- 场景分析；`madvise`、`MAP_POPULATE`、大页（THP、hugetlbfs、连续位）、`mlock`
- 基准测试程序与决策图

### 第 11 篇　内核视角

- `mm_struct`、VMA、maple tree、`max_map_count`
- mmap 系统调用的内核路径，`f_op->mmap` 与 `vm_ops`
- ARM64 缺页的内核路径，folio
- `address_space`、反向映射、内存回收与换出
- 实验：读懂 `/proc/pid/smaps`，RSS 与 PSS

### 第 12 篇　真实世界里的 mmap

- 程序与动态库加载，为什么 100 个进程只占一份 libc
- 数据库：LMDB、SQLite、Lucene；“数据库该不该用 mmap”之争
- 零拷贝与设备映射，ARM64 内存属性，内核共享环形缓冲区
- Firecracker：匿名 mmap 作客户机内存、ARM64 两阶段翻译、快照用 `MAP_PRIVATE` 或 userfaultfd
- userfaultfd 最小示例
- 常见陷阱汇总、排查工具清单、全系列一张图
