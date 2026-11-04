# 第 8 篇｜匿名映射：没有文件的 mmap

> **本篇目标**：理解不关联任何文件的**匿名映射**；揭开 `malloc` 背后的 `brk` 与 mmap；学会用 mmap 在进程之间共享内存（父子进程、无关进程）；认识 `/dev/shm`、tmpfs 和 `memfd_create`。最后提醒一个 ARM64 上特别要注意的问题：共享内存的**内存顺序**。

---

## 一、只要内存，不要文件

到目前为止，mmap 都是"把文件映射进来"。但很多时候，程序只是想要**一块内存**，和任何文件都没关系。

mmap 也能做到，只要加上 `MAP_ANONYMOUS` 标志：

```c
char *p = mmap(NULL, 1 << 20,                 // 1MB
               PROT_READ | PROT_WRITE,
               MAP_PRIVATE | MAP_ANONYMOUS,
               -1, 0);                        // 没有文件：fd 传 -1，offset 传 0
```

这叫**匿名映射（anonymous mapping）**，"匿名"指的是它背后没有名字（没有文件）。

在第 3 篇的 `/proc/self/maps` 里，那些没有路径、inode 为 0 的 `rw-p` 行，就是匿名映射。`[heap]` 和 `[stack]` 本质上也是匿名内存。

### 1.1 匿名页从哪里来

对匿名映射来说，缺页时没有文件可读。内核的处理很简单：

- **第一次写**：分配一个新物理页，**全部清零**，挂进页表；
- **第一次读（还没写过）**：内核甚至不分配新页，而是把一个全系统共享的、内容全是 0 的特殊物理页——**零页（zero page）**——以只读方式挂上去。之后如果写，再触发 COW，换成真正的新页。

这意味着：申请一大块内存、只读不写，几乎不消耗物理内存。

为什么一定要清零？第 4 篇讲过：物理页可能刚被别的进程用过，不清零就会泄露数据。这也带来了一个保证：**匿名映射的内存初始内容一定是 0**。

### 1.2 匿名页的去处

匿名页没有"磁盘上的原件"，所以内存紧张时不能像干净的页缓存页那样直接丢弃。内核只能把它写到**交换区（swap）**，等再访问时通过缺页读回来。没有配置 swap 的系统，匿名页就只能一直留在内存里，直到进程释放或被 OOM Killer 杀掉。

---

## 二、malloc 的秘密：brk 与 mmap

你每天都在用 `malloc`，它的内存从哪里来？

`malloc` 是 C 库（glibc）实现的函数，不是系统调用。glibc 向内核要内存有两条途径。

### 2.1 途径一：brk 扩展堆

进程的地址空间里有一块叫"堆"（heap）的区域，紧接在程序数据段之后。堆的末尾有一个边界，叫 **program break**。

```
 ┌──────────┬──────────────────────┬─ ─ ─ ─ ─ ─ ─ ─ ─ ─
 │ 程序数据段 │      堆（已分配）       │   （未分配的空地）
 └──────────┴──────────────────────┴─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                                   ▲
                             program break
                       brk() 把它往右推，堆就变大
```

系统调用 `brk` / `sbrk` 可以移动这个边界。glibc 一次多要一些（比如 132KB），然后自己把这片区域切成小块分给多次 `malloc`。

缺点：堆是**连续**的，只能从末尾收缩。如果堆顶的一小块还在使用，下面释放了的大片内存也无法还给系统。

### 2.2 途径二：直接 mmap

对于**大块**内存，glibc 直接调用 `mmap(MAP_PRIVATE | MAP_ANONYMOUS)` 单独映射一块。`free` 时直接 `munmap`，立刻还给系统，没有碎片问题。

分界线叫 **`M_MMAP_THRESHOLD`**，默认是 **128KB**。glibc 还会动态调整这个阈值（最高到 32MB，64 位系统上），以减少反复映射/解除映射的开销。

此外，多线程程序中，glibc 会为不同线程创建多个"分配区"（arena），这些分配区的内存也是用 mmap 申请的。

### 2.3 实验：用 strace 观察

```c
// malloc_demo.c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    printf("--- 小块 ---\n");
    fflush(stdout);
    char *a = malloc(100);

    printf("--- 大块 ---\n");
    fflush(stdout);
    char *b = malloc(1 << 20);      // 1MB

    printf("--- 释放大块 ---\n");
    fflush(stdout);
    free(b);

    free(a);
    return 0;
}
```

```bash
gcc malloc_demo.c -o malloc_demo
strace -e trace=brk,mmap,munmap,write ./malloc_demo 2>&1 | tail -12
```

输出类似（省略了程序启动阶段的部分）：

```
write(1, "--- 小块 ---\n", 16)
brk(NULL)                               = 0xaaaae1d6e000
brk(0xaaaae1d8f000)                     = 0xaaaae1d8f000        ← 小块：推进 program break
write(1, "--- 大块 ---\n", 16)
mmap(NULL, 1052672, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0xffff9c6ff000
                                                                ← 大块：直接匿名 mmap
write(1, "--- 释放大块 ---\n", 22)
munmap(0xffff9c6ff000, 1052672)         = 0                     ← free 大块：直接 munmap
```

几点观察：

- `malloc(100)` 触发了 `brk`，推进了 132KB（`0x21000` 字节），后续小块分配直接从这里切，不再调用系统调用；
- `malloc(1MB)` 直接 `mmap` 了 1052672 字节（1MB 加上一页，用于存放 glibc 的管理信息）；
- `free` 大块时立刻 `munmap`。

### 2.4 线程栈

每创建一个线程，`pthread_create` 都会用匿名 mmap 为它分配一块栈（默认 8MB），并在栈的末端用 `mprotect` 设置一个 `PROT_NONE` 的**保护页**。线程栈溢出时撞到保护页，立刻段错误，而不是悄悄踩坏相邻的内存。

8MB 的线程栈并不会真的占用 8MB 物理内存，按需分页让它只占实际用到的那部分。

---

## 三、父子进程共享内存：MAP_SHARED | MAP_ANONYMOUS

匿名映射也可以是**共享**的。`MAP_SHARED | MAP_ANONYMOUS` 创建的内存，在 `fork` 之后父子进程看到的是**同一块物理内存**（不走 COW）。这是父子进程间通信最简单的方式。

```c
// shared_counter.c —— 4 个子进程共同累加一个计数器
#include <stdio.h>
#include <stdatomic.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/wait.h>

struct shared {
    long        plain;     // 普通变量
    atomic_long atomic;    // 原子变量
};

int main(void) {
    struct shared *s = mmap(NULL, sizeof *s, PROT_READ | PROT_WRITE,
                            MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (s == MAP_FAILED) { perror("mmap"); return 1; }
    // 匿名映射的内容一定是 0，不用手动初始化

    const int N = 4, LOOPS = 1000000;
    for (int i = 0; i < N; i++) {
        if (fork() == 0) {
            for (int j = 0; j < LOOPS; j++) {
                s->plain++;                         // 非原子：读-改-写，会互相覆盖
                atomic_fetch_add(&s->atomic, 1);    // 原子：保证不丢失
            }
            _exit(0);
        }
    }
    for (int i = 0; i < N; i++) wait(NULL);

    printf("期望值:     %d\n", N * LOOPS);
    printf("普通变量:   %ld\n", s->plain);
    printf("原子变量:   %ld\n", atomic_load(&s->atomic));
    munmap(s, sizeof *s);
    return 0;
}
```

```bash
gcc -O1 shared_counter.c -o shared_counter && ./shared_counter
# 期望值:     4000000
# 普通变量:   1328547        ← 丢失了大量更新
# 原子变量:   4000000        ← 正确
```

这个实验同时说明了两件事：

1. 四个进程确实在操作**同一块内存**（否则每个进程的修改父进程都看不到，结果会是 0）；
2. **共享内存本身不提供任何同步**。`s->plain++` 实际上是"读出来、加一、写回去"三步，多个进程同时做就会互相覆盖。必须使用原子操作或锁。

> 如果把 `MAP_SHARED` 改成 `MAP_PRIVATE`，两个计数器都会是 0：每个子进程的修改都落在 COW 产生的私有复印件上，父进程看不到。

---

## 四、无关进程之间共享内存

父子进程可以通过继承共享映射。但如果是两个毫不相关的程序（比如一个生产者、一个消费者），它们怎么找到同一块内存呢？

答案是：**给内存起个名字**，让它看起来像一个文件，两边都去映射这个"文件"。

### 4.1 tmpfs：活在内存里的文件系统

Linux 有一种特殊的文件系统叫 **tmpfs**。它的文件完全存在于内存（页缓存）中，不对应任何磁盘。内存紧张时，它的页可以被换出到 swap。

系统通常在 `/dev/shm` 挂载了一个 tmpfs：

```bash
df -h /dev/shm
# Filesystem      Size  Used Avail Use% Mounted on
# tmpfs           7.8G     0  7.8G   0% /dev/shm
```

往 `/dev/shm` 里写文件，就是往内存里写数据，速度极快，但重启就没了。

内核内部，`MAP_SHARED | MAP_ANONYMOUS` 的共享匿名内存，其实也是借助同一套机制（shmem）实现的，只不过那个"文件"没有名字。

### 4.2 POSIX 共享内存：shm_open

`shm_open` 是一个标准接口，在 Linux 上它其实就是在 `/dev/shm` 里打开一个文件：

```c
// shm_writer.c —— 生产者：创建共享内存并写入消息
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

#define NAME "/demo_shm"
#define SIZE 4096

int main(void) {
    int fd = shm_open(NAME, O_CREAT | O_RDWR, 0600);   // 实际创建 /dev/shm/demo_shm
    if (fd < 0) { perror("shm_open"); return 1; }
    if (ftruncate(fd, SIZE) < 0) { perror("ftruncate"); return 1; }  // 设置大小

    char *p = mmap(NULL, SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    close(fd);

    snprintf(p, SIZE, "你好，我是进程 %d 写的消息", getpid());
    printf("已写入，按回车退出并删除共享内存\n");
    getchar();

    munmap(p, SIZE);
    shm_unlink(NAME);          // 删除名字（所有人解除映射后内存才真正释放）
    return 0;
}
```

```c
// shm_reader.c —— 消费者：打开同名共享内存并读取
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

#define NAME "/demo_shm"
#define SIZE 4096

int main(void) {
    int fd = shm_open(NAME, O_RDONLY, 0);
    if (fd < 0) { perror("shm_open"); return 1; }

    char *p = mmap(NULL, SIZE, PROT_READ, MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    close(fd);

    printf("读到: %s\n", p);
    munmap(p, SIZE);
    return 0;
}
```

```bash
gcc shm_writer.c -o shm_writer      # 老版本 glibc 需要加 -lrt
gcc shm_reader.c -o shm_reader

# 终端 1
./shm_writer
# 已写入，按回车退出并删除共享内存

# 终端 2
./shm_reader
# 读到: 你好，我是进程 7001 写的消息
ls -l /dev/shm/demo_shm
# -rw------- 1 you you 4096 Nov  2 10:00 /dev/shm/demo_shm
```

整个流程完全就是第 6 篇的"文件映射"：打开文件、设置大小、`MAP_SHARED` 映射。唯一的区别是这个文件住在内存里。两个进程的页表指向 tmpfs 里同一批物理页，读写都没有任何拷贝。

### 4.3 memfd_create：没有路径的内存文件

`shm_open` 需要一个全局可见的名字，可能和别人冲突，用完还得记得删除。Linux 3.17 引入了 `memfd_create`：

```c
#define _GNU_SOURCE
#include <sys/mman.h>

int fd = memfd_create("my_buffer", MFD_CLOEXEC);   // 名字只用于调试显示
ftruncate(fd, size);
void *p = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
```

它创建一个**只能通过 fd 访问**的内存文件，不在任何目录里出现。要和别的进程共享，可以：

- 通过 `fork` 继承 fd；
- 通过 Unix 域套接字把 fd "发送"给另一个进程（`SCM_RIGHTS`）。

`memfd_create` 还支持"封印"（sealing）：创建者可以宣布"这个文件从此不能再变大、不能再变小、不能再被写"，接收方就可以放心地映射，不必担心对方偷偷截断文件导致自己 SIGBUS（第 9 篇）。

它在虚拟化和图形系统中用得很多：例如虚拟机监控程序可以用 memfd 作为客户机内存，再把 fd 交给另一个进程（如 vhost-user 后端），让对方直接映射同一块客户机内存。

### 4.4 其他共享内存方式

还有一套更古老的 System V 共享内存（`shmget` / `shmat`），接口风格不同，但底层同样基于 shmem。新代码一般推荐 `shm_open` 或 `memfd_create`。

---

## 五、ARM64 特别提醒：共享内存与内存顺序

在 ARM64 上使用共享内存时，有一个比 x86 更容易踩的坑：**内存顺序（memory ordering）**。

考虑这样一段"生产者-消费者"代码：

```c
// 生产者                          // 消费者
data = 42;                         while (ready == 0) ;   // 等待
ready = 1;                         printf("%d\n", data);  // 期望打印 42
```

在 x86 上，这段代码（编译器不乱来的前提下）通常"碰巧能用"，因为 x86 的内存模型比较强，写操作的顺序在其他核看来基本保持不变。

但 ARM64 是**弱内存模型**：CPU 为了性能，允许其他核看到的写入顺序与程序顺序不同。消费者可能看到 `ready == 1`，却读到旧的 `data`。

正确的做法是使用带有内存顺序语义的原子操作：

```c
#include <stdatomic.h>

// 生产者
data = 42;
atomic_store_explicit(&ready, 1, memory_order_release);   // ARM64 上编译为 stlr 指令

// 消费者
while (atomic_load_explicit(&ready, memory_order_acquire) == 0)  // 编译为 ldar 指令
    ;
printf("%d\n", data);   // 保证读到 42
```

`release` 保证"在它之前的写入，不会被排到它之后"；`acquire` 保证"在它之后的读取，不会被排到它之前"。ARM64 有专门的 `stlr`（store-release）和 `ldar`（load-acquire）指令来高效实现这种语义。

**结论：在共享内存里做进程间通信，永远使用原子操作、锁（比如 `pthread_mutex` 配合 `PTHREAD_PROCESS_SHARED` 属性）或其他同步原语，不要依赖"看起来能用"的普通读写。**

---

## 六、匿名映射的其他用途

| 用途 | 做法 |
|---|---|
| 大块临时缓冲区 | `MAP_PRIVATE \| MAP_ANONYMOUS`，用完 `munmap`，立刻归还系统 |
| 预留一大段地址空间 | 先用 `PROT_NONE` 映射一大块（不占物理内存），之后按需 `mprotect` 打开一部分。很多语言运行时（Go、Java）的堆都这么做 |
| 警戒页 | 在缓冲区前后各放一页 `PROT_NONE`，越界即段错误，便于调试 |
| 自定义内存分配器 | jemalloc、tcmalloc 等都直接用 mmap 向内核批发内存 |
| 释放但保留地址 | 对匿名私有映射调用 `madvise(MADV_DONTNEED)`，物理页立刻归还系统，地址仍可用，下次访问得到全 0 的新页 |

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| 匿名映射 | `MAP_ANONYMOUS`，不关联文件，fd 传 -1 |
| 零页 | 全系统共享的全 0 物理页，只读不写的匿名内存都指向它 |
| 匿名内存初始为 0 | 出于安全必须清零，程序也可依赖这一点 |
| swap | 匿名页没有磁盘原件，回收时只能换出到交换区 |
| brk | 推进 program break 扩展堆，适合小块分配 |
| malloc 阈值 | 默认 ≥128KB 的分配直接用 mmap，free 时直接 munmap |
| 共享匿名映射 | `MAP_SHARED \| MAP_ANONYMOUS`，fork 后父子共享同一物理内存 |
| tmpfs / /dev/shm | 存在内存中的文件系统 |
| shm_open | 在 /dev/shm 创建有名字的共享内存，供无关进程映射 |
| memfd_create | 创建没有路径、只能通过 fd 传递的内存文件，支持封印 |
| ARM64 内存顺序 | 弱内存模型，共享内存通信必须用原子操作或锁 |

**下一篇预告**：[《数据什么时候真正落盘：一致性、同步与崩溃》](09-msync-and-sigbus.md)。你在 mmap 区域里写下的数据，此刻究竟在哪里？`munmap` 了就安全了吗？断电会怎样？文件被别人截断时为什么会收到 SIGBUS？我们会一一解答，并学会用 `msync` 保护你的数据。
