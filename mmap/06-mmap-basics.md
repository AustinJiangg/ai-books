# 第 6 篇｜mmap 登场：把文件变成一个数组

> **本篇目标**：逐个参数讲清 `mmap` 和 `munmap`，写出第一个用 mmap **读**文件和**改**文件的程序，用实验验证"mmap 什么都不读、缺页才读"，并盘点新手最容易踩的坑。

---

## 一、一句话定义

> **mmap 在进程的虚拟地址空间里开辟一段区域，并把这段区域和某个"后台对象"（通常是文件的一部分）关联起来。之后访问这段地址，就等于访问那个对象。**

前五篇的知识在这里汇合：

- "开辟一段区域" = 在进程的"菜单"（VMA）上登记一个新条目（第 3、4 篇）；
- "关联到文件" = 这段地址发生缺页时，去文件的页缓存里找页（第 4、5 篇）；
- "访问地址就是访问文件" = 页表直接指向页缓存的物理页，没有拷贝（第 5 篇）。

---

## 二、函数原型

```c
#include <sys/mman.h>

void *mmap(void *addr, size_t length, int prot, int flags, int fd, off_t offset);
int   munmap(void *addr, size_t length);
```

`mmap` 的意思可以读成一句话：

> "请在我的地址空间里，**大约在 `addr` 附近**，开一段 **`length`** 字节的区域，权限为 **`prot`**，映射方式为 **`flags`**，内容来自文件 **`fd`** 从 **`offset`** 开始的部分。"

下面逐个拆解。

### 2.1 `addr`：希望放在哪里

- 绝大多数时候传 **`NULL`**，意思是"你（内核）帮我挑个地方"。内核会在 mmap 区域里找一块足够大的空白。
- 如果传一个具体地址，内核只把它当作**建议**，可能采纳也可能不采纳。
- 如果同时在 `flags` 里加了 `MAP_FIXED`，内核就**必须**放在这个地址。**危险**：如果那里原本已经有映射，会被**悄无声息地覆盖**。新代码建议用 `MAP_FIXED_NOREPLACE`（Linux 4.17+），遇到冲突会返回错误而不是覆盖。

### 2.2 `length`：映射多长

- 要映射的字节数，必须大于 0。
- 内核实际映射的长度会**向上取整到页大小的整数倍**。映射 100 字节，实际会占用一整页。

### 2.3 `prot`：权限（protection）

| 值 | 含义 |
|---|---|
| `PROT_READ` | 可读 |
| `PROT_WRITE` | 可写 |
| `PROT_EXEC` | 可执行（可以把这段内存里的内容当代码执行） |
| `PROT_NONE` | 什么都不能干（访问即段错误），常用于"占位"或"警戒区" |

可以用 `|` 组合，如 `PROT_READ | PROT_WRITE`。这些权限最终会被翻译成第 3 篇讲的页表项权限位。

### 2.4 `flags`：映射方式

`flags` 中**必须**且只能选一个下面的基本类型：

| 值 | 含义 |
|---|---|
| `MAP_SHARED` | **共享映射**：你的修改会写进页缓存，其他映射同一文件的进程能看到，最终会写回文件 |
| `MAP_PRIVATE` | **私有映射**：你的修改只有你自己能看到，不会写回文件（写时复制，第 7 篇详讲） |

还可以加上各种附加标志，常用的有：

| 附加标志 | 含义 |
|---|---|
| `MAP_ANONYMOUS` | 不关联文件，只要一块内存（第 8 篇详讲） |
| `MAP_FIXED` / `MAP_FIXED_NOREPLACE` | 必须使用 `addr` 指定的地址 |
| `MAP_POPULATE` | 映射时就把所有页预先准备好，避免后续缺页 |
| `MAP_NORESERVE` | 不为这段映射预留内存额度（与内存超售有关） |
| `MAP_HUGETLB` | 使用大页（第 10 篇） |
| `MAP_LOCKED` | 把页锁在内存里，不被换出 |

### 2.5 `fd`：哪个文件

用 `open` 打开的文件描述符。匿名映射时传 `-1`。

**重要**：`mmap` 成功之后，**可以立即 `close(fd)`**，映射依然有效。因为映射本身持有了对文件的引用，文件不会因为 fd 关闭而"消失"。

### 2.6 `offset`：从文件的哪里开始

从文件第 `offset` 个字节开始映射。**它必须是页大小的整数倍**，否则 `mmap` 直接失败，`errno` 为 `EINVAL`。

> 再次提醒：ARM64 Linux 的页大小可能是 4KB、16KB 或 64KB，**永远用 `sysconf(_SC_PAGESIZE)` 获取页大小**，不要写死 4096。一份在 4KB 系统上运行良好的代码，拿到 64KB 页的服务器上就可能因为 offset 不对齐而失败。

### 2.7 返回值

- 成功：返回映射区域的**起始地址**（一个指针，通常是页对齐的）。
- 失败：返回 **`MAP_FAILED`**（它的值是 `(void *)-1`），并设置 `errno`。

**新手头号错误**：用 `NULL` 判断 mmap 是否失败。mmap 失败**不返回 NULL**，必须和 `MAP_FAILED` 比较：

```c
char *p = mmap(...);
if (p == MAP_FAILED) {     // ✅ 正确
    perror("mmap");
}
if (p == NULL) { ... }     // ❌ 错误：失败时 p 是 (void*)-1，不是 NULL
```

### 2.8 `munmap`：解除映射

```c
munmap(addr, length);
```

把这段地址从"菜单"上删掉，清理对应的页表项（并作废 TLB）。之后再访问这段地址就是段错误。

- 不调用 `munmap`，进程退出时内核也会自动清理所有映射；
- 但对于长期运行的程序，用完不 `munmap` 就是**地址空间泄漏**；
- `munmap` **不保证**把修改写到磁盘上（第 9 篇详讲），它只是解除映射。修改过的页仍然留在页缓存里，稍后照常写回。

---

## 三、第一个程序：用 mmap 读文件

我们写一个程序，统计文件的字节数、行数，并打印第一行。

```c
// mmap_count.c —— 用 mmap 统计文件行数
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "用法: %s 文件名\n", argv[0]);
        return 1;
    }

    // 1. 打开文件
    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }

    // 2. 获取文件大小
    struct stat st;
    if (fstat(fd, &st) < 0) { perror("fstat"); return 1; }
    size_t size = st.st_size;
    if (size == 0) {                     // 空文件不能映射（length 必须 > 0）
        printf("空文件\n");
        close(fd);
        return 0;
    }

    // 3. 映射整个文件：只读、私有
    const char *p = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }

    // 4. 映射建立后，fd 就可以关掉了
    close(fd);

    // 5. 像访问数组一样访问文件！
    size_t lines = 0;
    for (size_t i = 0; i < size; i++) {
        if (p[i] == '\n')
            lines++;
    }

    printf("文件大小: %zu 字节\n", size);
    printf("行数:     %zu\n", lines);

    // 打印第一行
    printf("第一行:   ");
    for (size_t i = 0; i < size && p[i] != '\n'; i++)
        putchar(p[i]);
    putchar('\n');

    // 6. 解除映射
    munmap((void *)p, size);
    return 0;
}
```

```bash
gcc -O2 mmap_count.c -o mmap_count
./mmap_count /etc/passwd
# 文件大小: 1876 字节
# 行数:     35
# 第一行:   root:x:0:0:root:/root:/bin/bash
```

看看第 5 步的循环：`p[i] == '\n'`。整个程序里**没有一次 `read` 调用**，文件就像一个普通的 `char` 数组。

### 3.1 与 read 版本对比

```c
// read 版本的核心循环
char buf[65536];
ssize_t n;
while ((n = read(fd, buf, sizeof buf)) > 0) {
    for (ssize_t i = 0; i < n; i++)
        if (buf[i] == '\n') lines++;
}
```

| 对比项 | read 版本 | mmap 版本 |
|---|---|---|
| 需要自己管理缓冲区 | 是 | 否 |
| 数据拷贝 | 每次 read 拷贝一次 | 无 |
| 系统调用次数 | 文件大小 ÷ 缓冲区大小 | mmap + munmap 各一次（但有缺页） |
| 随机访问第 N 个字节 | 需要 `lseek` + `read` | 直接 `p[N]` |
| 处理跨缓冲区的数据（如一行被切成两半） | 麻烦 | 不存在这个问题 |

最后一项其实是 mmap 在编程上最大的便利之一：解析文件格式时，数据结构可能横跨任意位置，read 版本需要处理"读了一半"的情况，mmap 版本则完全不用操心。

---

## 四、第二个程序：用 mmap 修改文件

把文件中所有小写字母改成大写，**直接在原文件上修改**：

```c
// mmap_upper.c —— 用 mmap 把文件内容改成大写
#include <stdio.h>
#include <ctype.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "用法: %s 文件名\n", argv[0]);
        return 1;
    }

    // 要修改文件，必须以读写方式打开
    int fd = open(argv[1], O_RDWR);
    if (fd < 0) { perror("open"); return 1; }

    struct stat st;
    if (fstat(fd, &st) < 0) { perror("fstat"); return 1; }
    if (st.st_size == 0) { close(fd); return 0; }

    // 可读可写 + 共享映射：修改会进入页缓存，最终写回文件
    char *p = mmap(NULL, st.st_size, PROT_READ | PROT_WRITE,
                   MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    close(fd);

    for (off_t i = 0; i < st.st_size; i++)
        p[i] = toupper((unsigned char)p[i]);   // 直接赋值就是在改文件

    munmap(p, st.st_size);
    return 0;
}
```

```bash
gcc mmap_upper.c -o mmap_upper
echo "hello, mmap world" > test.txt
./mmap_upper test.txt
cat test.txt
# HELLO, MMAP WORLD
```

关键的三个组合：

1. `open(..., O_RDWR)`：文件必须以**读写**方式打开；
2. `PROT_READ | PROT_WRITE`：映射区域可写；
3. `MAP_SHARED`：修改要写回文件。

如果把 `MAP_SHARED` 换成 `MAP_PRIVATE`，程序照样能运行，`p` 里的内容也确实变成了大写，但 `cat test.txt` 会发现**文件没变**。原因留到下一篇讲。

注意：mmap **不能改变文件的大小**。你只能在已有的范围内修改。想往文件末尾追加内容，需要先用 `ftruncate` 把文件变大，再映射（第 9 篇）。

---

## 五、mmap 背后发生了什么：一条时间线

我们把前几篇的知识串起来，看看 `mmap_count` 运行时，内核到底做了什么。

```
时刻 ①  mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0)
        内核：
        - 在 mmap 区域找一段足够大的空白虚拟地址
        - 在"菜单"上登记一个新条目（VMA）：
            "0xffff9a000000 起的 size 字节 → 文件 X 的 0 字节起，只读，私有"
        - 不读文件！不分配物理页！不填页表！
        - 返回 0xffff9a000000

时刻 ②  close(fd)
        菜单条目自己持有文件引用，映射不受影响

时刻 ③  第一次执行 p[0]
        MMU：页表项无效 → 缺页异常
        内核：
        - 查菜单：属于刚才那个映射，对应文件第 0 页
        - 查文件 X 的页缓存：第 0 页在吗？
            · 不在 → 分配物理页，从磁盘读（大缺页），顺便预读后面的若干页
            · 在   → 小缺页
        - 把这个页缓存页（以及附近已在缓存中的一些页）填入页表，标记只读
        - 重新执行 p[0]，成功

时刻 ④  p[1] ... p[4095]
        同一页，TLB 命中，和访问普通数组一样快

时刻 ⑤  p[4096]
        如果时刻③已经顺便映射了这一页，就直接命中；否则再来一次缺页

时刻 ⑥  munmap
        删除菜单条目，清除页表项，作废 TLB
        页缓存里的页仍然留着（其他人可能还要用）
```

### 5.1 "顺便映射附近的页"：fault-around

时刻③提到，缺页时内核会"顺便"把附近已经在页缓存里的页一起填入页表。这个机制叫 **fault-around**，默认一次最多处理 64KB（即 16 个 4KB 页），由调试文件系统里的参数 `/sys/kernel/debug/fault_around_bytes` 控制。它只对**读操作引起的文件映射缺页**生效，并且只"顺便"映射那些**已经在页缓存里**的页，不会为此额外读磁盘。

它的意义在于：顺序访问一个已缓存的文件时，不必每 4KB 就缺页一次，而是每 64KB 缺页一次，开销降到约 1/16。

### 实验：数一数缺页次数

在 `mmap_count.c` 的 `munmap` 前加上几行：

```c
#include <sys/resource.h>
// ...
struct rusage ru;
getrusage(RUSAGE_SELF, &ru);
printf("小缺页: %ld，大缺页: %ld\n", ru.ru_minflt, ru.ru_majflt);
```

然后用一个 100MB 的文件测试：

```bash
dd if=/dev/urandom of=big100.bin bs=1M count=100
gcc -O2 mmap_count.c -o mmap_count

# 冷缓存
sync; echo 3 | sudo tee /proc/sys/vm/drop_caches
./mmap_count big100.bin

# 热缓存
./mmap_count big100.bin
```

你可能会观察到：

- 100MB = 25600 个 4KB 页，但小缺页数远小于 25600（热缓存时约为 1600 左右再加上程序启动的开销），这就是 fault-around 的效果：25600 ÷ 16 = 1600；
- 冷缓存时会出现一些大缺页，同时预读让后续的很多访问变成了小缺页。

（具体数字取决于内核版本、页大小、是否启用了大页，看量级即可。）

---

## 六、映射超出文件末尾会怎样？

这是一个容易让人困惑的地方。假设文件大小是 **5000 字节**，页大小 4096。

```
文件内容:  |<-------- 5000 字节 -------->|
页划分:    |<---- 第0页 4096 ---->|<---- 第1页 4096 ---->|<---- 第2页 ---->
                                  4096    5000          8192             12288
```

### 情况一：映射 5000 字节

```c
char *p = mmap(NULL, 5000, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
```

内核实际映射 2 页（8192 字节）。

- `p[0]` ~ `p[4999]`：文件内容，正常读写；
- `p[5000]` ~ `p[8191]`：**可以访问**，读出来是 0。写进去不会报错，但**这些写入不会进入文件**（文件大小还是 5000）。

### 情况二：映射 12288 字节（比文件大得多）

```c
char *p = mmap(NULL, 12288, PROT_READ, MAP_SHARED, fd, 0);   // mmap 本身会成功！
```

- `p[0]` ~ `p[8191]`：同上；
- `p[8192]` 及以后：这一页**完全在文件末尾之外**，访问它会收到 **SIGBUS** 信号（总线错误），程序默认会崩溃。

```
Bus error (core dumped)
```

**规律：文件末尾所在的那一页可以安全访问（多出的部分是 0）；完全超出文件末尾的页，访问即 SIGBUS。**

SIGBUS 和 SIGSEGV 的区别：

- **SIGSEGV**：这个地址根本不在"菜单"上；
- **SIGBUS**：这个地址在菜单上，但背后的文件没有对应的数据，内核无法兑现。

第 9 篇还会看到 SIGBUS 的另一种常见成因：**映射之后文件被别人截短了**。

---

## 七、新手常见错误清单

| 错误 | 现象 | 原因 / 正确做法 |
|---|---|---|
| 用 `NULL` 判断失败 | 失败后继续访问 `(void*)-1`，段错误 | 和 `MAP_FAILED` 比较 |
| offset 不是页大小倍数 | `EINVAL` | 用 `sysconf(_SC_PAGESIZE)` 对齐 offset，再在映射内部加偏移 |
| 映射空文件 | `EINVAL`（length 为 0） | 先检查文件大小 |
| 只读打开 + `MAP_SHARED` + `PROT_WRITE` | `EACCES` | 想写回文件就用 `O_RDWR` 打开 |
| 以 `O_WRONLY` 打开后映射 | `EACCES` | mmap 至少需要文件可读 |
| 访问超出文件末尾的整页 | SIGBUS | 映射长度不要超过文件大小，或先用 `ftruncate` 扩大文件 |
| 想用 mmap 追加内容 | 写不进去或 SIGBUS | 先 `ftruncate` 扩大文件 |
| 忘记 `munmap` | 长期运行的程序地址空间逐渐耗尽 | 用完及时解除映射 |
| 以为 `munmap` 会落盘 | 断电后数据丢失 | 需要持久化时调用 `msync`（第 9 篇） |
| 在 `munmap` 后继续使用指针 | 段错误 | 解除映射后指针立刻失效 |

### 如何映射文件中间任意位置

假设要映射文件从第 10000 字节开始的 100 字节，而 offset 必须页对齐：

```c
long page = sysconf(_SC_PAGESIZE);
off_t want = 10000;
off_t aligned = want & ~(page - 1);      // 向下对齐到页边界：8192
size_t delta = want - aligned;           // 多映射的前导部分：1808

char *base = mmap(NULL, delta + 100, PROT_READ, MAP_PRIVATE, fd, aligned);
if (base == MAP_FAILED) { /* 处理错误 */ }
char *data = base + delta;               // data[0] 就是文件第 10000 字节

/* 使用 data[0] ~ data[99] */

munmap(base, delta + 100);               // 注意：munmap 要用 base，不是 data
```

---

## 八、亲眼看看映射

把下面这段加到程序里，在映射之后暂停一下：

```c
printf("映射地址: %p，按回车继续\n", (void *)p);
getchar();
```

在另一个终端查看这个进程的内存地图：

```bash
cat /proc/$(pgrep mmap_count)/maps | grep big100
# ffff8e800000-ffff94c00000 r--p 00000000 fe:01 393224   /home/you/big100.bin
```

这一行就是你的 mmap：地址范围、只读私有（`r--p`）、文件偏移 0、对应的文件。和第 3 篇里看到的 C 库映射一模一样，只不过这次是你亲手创建的。

---

## 本篇小结

| 要点 | 说明 |
|---|---|
| `addr` | 通常传 NULL；`MAP_FIXED` 会覆盖已有映射，慎用 |
| `length` | 向上取整到页大小，必须 > 0 |
| `prot` | `PROT_READ / WRITE / EXEC / NONE` |
| `flags` | 必选 `MAP_SHARED` 或 `MAP_PRIVATE`，可加附加标志 |
| `fd` / `offset` | offset 必须页对齐；映射后 fd 可以关闭 |
| 返回值 | 失败返回 `MAP_FAILED`，不是 NULL |
| 本质 | mmap 只登记，缺页时才把页缓存页挂入页表 |
| fault-around | 一次缺页顺便映射附近已缓存的页，减少缺页次数 |
| 超出文件末尾 | 末尾所在页的剩余部分读出为 0；完全超出的页访问会 SIGBUS |

**下一篇预告**：[《共享还是私有：MAP_SHARED、MAP_PRIVATE 与写时复制》](07-shared-private-cow.md)。为什么 `MAP_PRIVATE` 下修改了内容但文件没变？修改的数据去哪儿了？我们会揭开**写时复制（COW）**的机制，顺便解答一个经典问题：为什么 `fork` 一个占用 10GB 内存的进程只需要几毫秒？
