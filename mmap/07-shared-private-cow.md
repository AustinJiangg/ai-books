# 第 7 篇｜共享还是私有：MAP_SHARED、MAP_PRIVATE 与写时复制

> **本篇目标**：彻底搞懂 `MAP_SHARED` 和 `MAP_PRIVATE` 的区别；理解操作系统中最巧妙的技巧之一——**写时复制（Copy-on-Write，COW）**；并用它解释为什么 `fork` 一个占用 10GB 内存的进程只需要几毫秒。

---

## 一、原件与复印件

想象办公室里有一份共享的合同原件，放在公共文件柜里（页缓存）。

**共享方式（MAP_SHARED）**：你直接在原件上修改。其他同事打开文件柜，看到的就是你改过的版本；到了晚上，行政人员会把原件归档（写回磁盘）。

**私有方式（MAP_PRIVATE）**：你也可以直接翻阅原件，但是一旦你想在某一页上涂改，行政人员会先把**那一页**复印一份交给你，你在复印件上随便画。原件不变，同事看不到你的涂改，晚上归档时也不会归档你的复印件。

这就是两种映射的全部区别。下面看它在内核里是怎么实现的。

---

## 二、MAP_SHARED：直接改原件

```
 进程 A 的页表                   页缓存                      进程 B 的页表
 ┌──────────────┐          ┌──────────────────┐          ┌──────────────┐
 │ 0xffffa000.. │ ───────▶ │ 物理页 #1024      │ ◀─────── │ 0xffff7000.. │
 │  (可读写)     │          │ 文件第 0 页        │          │  (可读写)     │
 └──────────────┘          └──────────────────┘          └──────────────┘
                                    │
                                    │ 脏页，稍后写回
                                    ▼
                               磁盘上的文件
```

- 两个进程以 `MAP_SHARED` 映射同一个文件，它们的页表指向**同一个物理页**；
- A 写入的数据，B **立刻**就能读到（同一块物理内存，不需要任何"同步"）；
- 用 `read` 读这个文件的进程也能读到（同一个页缓存页）；
- 修改让页变脏，稍后由内核写回磁盘。

## 三、MAP_PRIVATE：写时才复印

### 3.1 读的时候和共享映射一样

`MAP_PRIVATE` 映射建立后，第一次**读**某一页时，内核做的事情和共享映射几乎一样：把页缓存里的那个物理页挂进页表。区别只有一个：

> **内核故意把页表项设为只读**，哪怕你在 mmap 时要求了 `PROT_WRITE`。

```
 进程 A 的页表                         页缓存
 ┌──────────────────────┐         ┌──────────────────┐
 │ 0xffffa000..          │ ──────▶ │ 物理页 #1024      │
 │ 菜单上：可读写、私有     │         │ 文件第 0 页        │
 │ 页表项：**只读**         │         └──────────────────┘
 └──────────────────────┘
```

### 3.2 写的时候：触发复制

当进程第一次**写**这一页时：

```
 ① 进程执行写指令
 ② MMU 发现页表项只读 → 权限缺页异常（第 4 篇"情况四"）
 ③ 内核查菜单：这段区域"可写 + 私有"
    → 判断：这不是错误，而是写时复制的时机
 ④ 分配一个新的物理页 #3000
 ⑤ 把 #1024 的 4KB 内容完整复制到 #3000
 ⑥ 修改页表项：指向 #3000，并设为**可写**
 ⑦ 返回，重新执行写指令，这次写进了 #3000
```

```
 进程 A 的页表                         页缓存
 ┌──────────────────────┐         ┌──────────────────┐
 │ 0xffffa000..          │    ╳    │ 物理页 #1024      │ ← 原件，未被修改
 │ 页表项：可写            │         └──────────────────┘
 └──────────┬───────────┘
            │                     ┌──────────────────┐
            └───────────────────▶ │ 物理页 #3000      │ ← A 的私有复印件
                                  │ （已被 A 修改）     │
                                  └──────────────────┘
```

此后：

- 进程 A 对这一页的所有读写都发生在 #3000 上，不再缺页；
- #3000 **不再属于任何文件**，它变成了一个"匿名页"（第 8 篇）。内存紧张时，它不能被简单丢弃（磁盘上没有它的副本），只能换出到交换区（swap）；
- 页缓存里的 #1024 原封不动，文件不会被修改。

### 3.3 为什么是"按页"复制？

COW 的粒度是**一页**。一个 1GB 的私有映射，如果你只改了其中 3 个字节，而这 3 个字节分布在 3 个不同的页上，那么只会复制 3 页（12KB），其他页仍然和页缓存共享。

这就是"写时复制"的精髓：**能共享就共享，非复制不可时才复制，而且只复制被改的那一页。**

---

## 四、实验一：共享与私有的直观对比

```c
// share_vs_private.c
// 用法: ./a.out shared   或   ./a.out private
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/wait.h>

int main(int argc, char *argv[]) {
    int shared = (argc > 1 && strcmp(argv[1], "shared") == 0);

    // 准备一个文件
    int fd = open("demo.txt", O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    write(fd, "original content\n", 17);

    char *p = mmap(NULL, 17, PROT_READ | PROT_WRITE,
                   shared ? MAP_SHARED : MAP_PRIVATE, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    close(fd);

    pid_t pid = fork();            // 子进程继承这个映射
    if (pid == 0) {
        memcpy(p, "CHILD WROTE THIS", 16);
        printf("[子进程] 我看到: %.16s\n", p);
        return 0;
    }

    waitpid(pid, NULL, 0);         // 等子进程写完
    printf("[父进程] 我看到: %.16s\n", p);
    munmap(p, 17);
    return 0;
}
```

```bash
gcc share_vs_private.c -o svp

./svp shared
# [子进程] 我看到: CHILD WROTE THIS
# [父进程] 我看到: CHILD WROTE THIS      ← 父进程看到了子进程的修改
cat demo.txt
# CHILD WROTE THIS                       ← 文件也被修改了

./svp private
# [子进程] 我看到: CHILD WROTE THIS
# [父进程] 我看到: original content      ← 父进程看不到
cat demo.txt
# original content                       ← 文件没变
```

`fork` 之后，父子进程共享同一个映射：

- `MAP_SHARED` 时，大家指向同一个页缓存页，子进程的修改就是对文件的修改；
- `MAP_PRIVATE` 时，子进程写的时候触发 COW，修改只落在它自己的复印件上。

---

## 五、实验二：私有映射的一个"反直觉"细节

问题：`MAP_PRIVATE` 映射之后，**别人**通过 `write` 修改了文件，我能看到吗？

直觉可能是"私有映射是我自己的快照，看不到"。但答案是：**取决于你有没有写过那一页。**

- 你**没写过**的页：页表仍然指向页缓存的原件，别人改了原件，你立刻能看到；
- 你**写过**的页：已经换成了你的私有复印件，别人怎么改原件都与你无关。

```c
// private_view.c —— 观察私有映射何时"脱离"文件
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

int main(void) {
    long page = sysconf(_SC_PAGESIZE);

    // 准备一个 2 页大的文件，全是 'a'
    int fd = open("view.bin", O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    for (long i = 0; i < 2 * page; i++) write(fd, "a", 1);

    char *p = mmap(NULL, 2 * page, PROT_READ | PROT_WRITE, MAP_PRIVATE, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }

    printf("初始:              第0页=%c 第1页=%c\n", p[0], p[page]);

    p[0] = 'M';                         // 我写第 0 页 → 触发 COW
    printf("我写第0页后:        第0页=%c 第1页=%c\n", p[0], p[page]);

    pwrite(fd, "X", 1, 0);              // 别人（这里用 pwrite 模拟）改文件第 0 页
    pwrite(fd, "X", 1, page);           // 也改文件第 1 页
    printf("文件被别人改了之后:  第0页=%c 第1页=%c\n", p[0], p[page]);

    munmap(p, 2 * page);
    close(fd);
    return 0;
}
```

```
初始:              第0页=a 第1页=a
我写第0页后:        第0页=M 第1页=a
文件被别人改了之后:  第0页=M 第1页=X   ← 第1页没写过，看到了别人的修改
```

POSIX 标准没有规定这种情况下的行为，这是 Linux 的实际表现。所以：

> **`MAP_PRIVATE` 不是"快照"**。它只保证"你的修改不影响别人"，不保证"别人的修改不影响你"。如果需要一个不受外界影响的稳定副本，要么确保文件不会被修改，要么自己完整拷贝一份。

---

## 六、COW 的最大用户：fork

### 6.1 fork 是什么

`fork()` 是 Unix 创建新进程的方式：它把当前进程**完整复制**一份，产生一个子进程。子进程拥有和父进程一模一样的内存内容。

Shell 里每执行一条命令，都会先 `fork` 自己，然后在子进程里 `exec` 那条命令。服务器程序也常用 `fork` 创建工作进程。Redis 做持久化快照时也会 `fork`。

### 6.2 傻瓜式实现会怎样

如果 `fork` 真的把父进程的所有内存逐字节复制一份：

- 一个占用 10GB 内存的进程，`fork` 要复制 10GB，耗时数秒；
- 内存立刻翻倍；
- 而大多数情况下，子进程马上就会调用 `exec` 去运行另一个程序，刚复制的 10GB 立刻作废。

这太浪费了。

### 6.3 用 COW 实现 fork

Linux 的 `fork` 实际上这样做：

1. **复制"菜单"和页表**，而不是复制数据页本身；
2. 把父子双方页表中所有**可写的私有页**都改为**只读**；
3. 让每个物理页的"引用计数"加 1，表示现在有两个进程在用它。

```
 fork 之后：

 父进程页表                  物理内存                  子进程页表
 ┌──────────┐            ┌────────────┐            ┌──────────┐
 │ 页表项 只读 │ ─────────▶ │ 物理页 #500 │ ◀───────── │ 页表项 只读 │
 └──────────┘            │ 引用计数 = 2 │            └──────────┘
                         └────────────┘
```

之后，无论父进程还是子进程写某一页，都会触发 COW：复制这一页，写的那一方拿到复印件。另一方如果后来也去写，发现引用计数已经变回 1，就不用再复制，直接把页表项改回可写即可。

所以 `fork` 的成本主要是**复制页表**，与内存大小成正比但远小于复制数据本身（4KB 数据只对应 8 字节页表项），对于 10GB 内存的进程通常在几毫秒到几十毫秒之间。

### 6.4 实验三：fork 的速度与 COW 的代价

```c
// fork_cow.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/resource.h>
#include <sys/wait.h>

static double now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1e3 + ts.tv_nsec / 1e6;
}

int main(void) {
    size_t size = 2UL << 30;                       // 2GB
    long page = sysconf(_SC_PAGESIZE);
    char *mem = malloc(size);
    if (!mem) { perror("malloc"); return 1; }
    memset(mem, 1, size);                          // 先把 2GB 全部写一遍，确保真的占用内存

    double t0 = now_ms();
    pid_t pid = fork();
    if (pid == 0) {
        double t1 = now_ms();
        printf("[子] fork 耗时约 %.2f ms\n", t1 - t0);

        struct rusage ru;
        getrusage(RUSAGE_SELF, &ru);
        long before = ru.ru_minflt;

        for (size_t i = 0; i < size; i += page)    // 子进程把每一页都写一遍
            mem[i] = 2;

        getrusage(RUSAGE_SELF, &ru);
        printf("[子] 写遍 2GB 耗时 %.2f ms，触发缺页 %ld 次（每次都是一次 COW 复制）\n",
               now_ms() - t1, ru.ru_minflt - before);
        _exit(0);
    }
    waitpid(pid, NULL, 0);
    printf("[父] mem[0] 仍然是 %d\n", mem[0]);
    free(mem);
    return 0;
}
```

典型结果（具体数值因机器而异）：

```
[子] fork 耗时约 15.30 ms
[子] 写遍 2GB 耗时 820.45 ms，触发缺页 524288 次（每次都是一次 COW 复制）
[父] mem[0] 仍然是 1
```

- `fork` 2GB 进程只用了十几毫秒；
- 子进程写遍所有页时，才真正付出复制的代价：52 万次缺页、每次复制 4KB；
- 父进程的数据完全不受影响。

> 如果系统启用了透明大页，`memset` 后的内存可能是 2MB 大页，缺页次数会少很多。

### 6.5 COW 的副作用

- **写放大**：只改 1 个字节，也要复制整整 4KB（大页下可能是 2MB）。
- **内存突增**：Redis 在 `fork` 后做持久化，如果此时有大量写请求，父进程会疯狂触发 COW，内存占用可能接近翻倍。这是 Redis 运维中的经典问题。
- **延迟抖动**：每次 COW 缺页都要分配内存、复制数据。

---

## 七、权限组合：什么能映射，什么不能

mmap 的权限受到**文件打开方式**的约束。内核的原则是：**不能通过 mmap 获得比打开文件时更大的权限。**

| 文件打开方式 | 映射方式 | `PROT_READ` | `PROT_READ \| PROT_WRITE` |
|---|---|---|---|
| `O_RDONLY` | `MAP_PRIVATE` | ✅ | ✅（写的是私有复印件，不影响文件） |
| `O_RDONLY` | `MAP_SHARED` | ✅ | ❌ `EACCES`（你没有写文件的权限） |
| `O_RDWR` | `MAP_PRIVATE` | ✅ | ✅ |
| `O_RDWR` | `MAP_SHARED` | ✅ | ✅（修改写回文件） |
| `O_WRONLY` | 任意 | ❌ `EACCES` | ❌ `EACCES`（映射至少需要可读） |

注意第一行：**只读打开的文件，可以私有地可写映射**。这非常合理：你修改的只是自己的复印件，文件本身毫发无损。动态链接器加载共享库时就是这么做的（第 12 篇）。

另一个限制：如果文件所在的文件系统以只读方式挂载，`MAP_SHARED + PROT_WRITE` 同样会失败。

### 7.1 映射后修改权限：mprotect

```c
int mprotect(void *addr, size_t len, int prot);
```

可以在映射之后修改某段区域的权限（同样以页为单位）。比如：

- 把一段内存设为 `PROT_NONE`，做成"警戒区"，一旦越界访问就立刻段错误。线程栈底部的保护页就是这么实现的；
- JIT 编译器（比如 JavaScript 引擎）先以可写方式生成机器码，再改为只读可执行；
- 共享库加载后，把重定位完成的区域改为只读，防止被篡改（RELRO 技术）。

`mprotect` 同样不能突破文件打开方式的限制：对 `O_RDONLY` 打开的文件做的 `MAP_SHARED` 映射，无法通过 `mprotect` 改为可写。

---

## 八、如何选择

| 场景 | 选择 | 原因 |
|---|---|---|
| 修改文件并保存 | `MAP_SHARED` | 修改需要写回文件 |
| 多个进程通过文件共享数据 | `MAP_SHARED` | 大家看同一份物理页 |
| 只读访问文件 | 两者皆可，常用 `MAP_PRIVATE` | 不写就不会复制，性能相同；私有映射更不容易误改文件 |
| 加载程序和库 | `MAP_PRIVATE` | 需要在内存中做少量修改（重定位），但不能改动磁盘上的文件 |
| 以文件为"模板"，各自修改 | `MAP_PRIVATE` | 例如从快照文件恢复虚拟机内存，见第 12 篇 |

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| `MAP_SHARED` | 页表直接指向页缓存，修改所有人可见并写回文件 |
| `MAP_PRIVATE` | 读时共享页缓存，写时复制一份私有页，修改不影响文件 |
| 写时复制（COW） | 页表项故意设为只读，写时触发缺页，内核复制该页后再放行 |
| COW 粒度 | 以页为单位，只复制被写的页 |
| 私有映射不是快照 | 没写过的页仍能看到别人对文件的修改 |
| fork | 只复制页表并全部设为只读，靠 COW 推迟真正的复制 |
| 权限约束 | mmap 不能获得比 open 更大的权限；`O_RDONLY` 也能做可写私有映射 |
| mprotect | 映射后修改页的权限 |

**下一篇预告**：[《匿名映射：没有文件的 mmap》](08-anonymous-mapping.md)。如果 mmap 不关联任何文件呢？我们会发现 `malloc` 的秘密、进程间共享内存的实现方式，以及 `/dev/shm` 这个"活在内存里的文件系统"。
