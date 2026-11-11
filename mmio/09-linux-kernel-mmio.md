# 第 9 篇｜Linux 内核驱动里的 MMIO

> **本篇目标**：把前八篇的原理落到 Linux 内核的实际代码上。读完本篇，你会知道内核驱动是如何拿到设备的物理地址、用 `ioremap` 建立映射、用 `readl`/`writel` 家族访问寄存器、管理 MMIO 资源的；能看懂一个最小的 platform 驱动骨架；并了解 regmap 和常用调试手段。

---

## 一、内核也要用虚拟地址

### 1.1 不能直接用物理地址

第 1 篇和第 3 篇的裸机例子里，我们直接把物理地址 `0x09000000` 当作指针来用。这在 MMU 关闭的环境下没问题。但 Linux 内核运行时，MMU 是**开着**的——内核代码里的每一个指针，都是**虚拟地址**，要经过页表翻译。

如果在内核里直接写：

```c
*(volatile u32 *)0x09000000 = 'A';   // 错误！
```

CPU 会把 `0x09000000` 当作一个虚拟地址去查页表。内核的页表里并没有这个虚拟地址的映射（或者映射到了完全不相干的地方），结果是一个内核缺页异常，系统打印一大串错误信息，甚至直接崩溃。

所以，内核要访问一个设备，必须先做一件事：**在页表里建立一个映射，让某个虚拟地址指向设备的物理地址，并且设置正确的内存属性。**

### 1.2 ioremap：为设备建立映射

这件事由 `ioremap` 函数来完成：

```c
void __iomem *base;

base = ioremap(0x09000000, 0x1000);   // 物理地址，长度
if (!base)
    return -ENOMEM;

// 现在 base 是一个虚拟地址，指向串口的寄存器
writel('A', base + 0x000);

// 用完之后
iounmap(base);
```

`ioremap` 做了三件事：

1. **在内核的虚拟地址空间里找一块空闲的区域**（位于内核专门留出的 vmalloc 区）；
2. **在内核页表里建立映射**：这块虚拟地址 → 设备的物理地址；
3. **设置正确的内存属性**：在 ARM64 上是 Device-nGnRE（第 5 篇讲过），在 x86 上是 UC-。

返回的 `base` 是一个虚拟地址。从此以后，`base + 偏移量` 就对应着设备的各个寄存器。

```
  内核虚拟地址空间                           物理地址空间
  ┌──────────────────┐                     ┌──────────────────┐
  │                  │                     │                  │
  │ base ──────────────── 页表映射 ────────→│ 0x09000000 串口   │
  │ (如 0xffff800080 │  属性=Device-nGnRE   │                  │
  │      0a0000)     │                     │                  │
  └──────────────────┘                     └──────────────────┘
```

`ioremap` 还有几个变体，第 5 篇已经介绍过：`ioremap_wc`（写合并）、`ioremap_np`（不允许提前写确认）、`ioremap_cache`（可缓存）。绝大多数驱动用默认的 `ioremap` 就行。

### 1.3 `__iomem`：一把类型锁

注意 `base` 的类型是 `void __iomem *`。`__iomem` 是什么？

它是一个**标记**，告诉内核的静态检查工具 **sparse**：“这个指针指向设备内存，不是普通内存”。在正常编译时，`__iomem` 什么都不做；但用 sparse 检查时（编译内核时加上 `C=1` 参数），如果你写出了这样的代码：

```c
u32 v = *(u32 *)base;          // 直接解引用 __iomem 指针
memcpy(buf, base, 64);         // 把 __iomem 指针传给普通函数
```

sparse 会发出警告：“你把一个 `__iomem` 指针当成普通指针用了”。

反过来，如果你把一个普通指针传给 `readl`，sparse 也会警告。

这样，**设备地址和普通地址在类型上被隔离开了**，只有专门的访问函数才能“打开”`__iomem` 指针。第 4 篇讲过为什么要这样做：直接解引用会遇到编译器优化、访问宽度、屏障等一系列问题，而访问函数把这些问题都处理好了。

---

## 二、访问函数家族

Linux 提供了一整个家族的 MMIO 访问函数。认识它们，就能看懂绝大部分驱动代码。

### 2.1 基本读写

| 宽度 | 读 | 写 |
|---|---|---|
| 8 位 | `readb(addr)` | `writeb(val, addr)` |
| 16 位 | `readw(addr)` | `writew(val, addr)` |
| 32 位 | `readl(addr)` | `writel(val, addr)` |
| 64 位 | `readq(addr)` | `writeq(val, addr)` |

后缀字母来自历史上的叫法：**b**yte（字节）、**w**ord（字，16 位）、**l**ong（长字，32 位）、**q**uad（四字，64 位）。

注意 `writel` 的参数顺序是**先值后地址**，这和很多人的直觉相反，新手经常写反。

这些函数默认按**小端序**访问（PCI 设备的标准）。如果设备的寄存器是大端序的，可以用 `ioread32be`/`iowrite32be` 这类函数。

### 2.2 有屏障和无屏障

第 6 篇详细讲过：

- `readl` / `writel`：**带屏障**，保证和前后的普通内存访问之间的顺序；
- `readl_relaxed` / `writel_relaxed`：**不带屏障**，只保证同一设备的访问按顺序，更快。

规则：**默认用带屏障的版本；确认安全且性能关键时才用 `_relaxed`。**

### 2.3 `ioread32` 系列

你可能还会在驱动里看到另一套函数：`ioread8`、`ioread16`、`ioread32`、`iowrite32` 等。它们和 `readl` 系列功能几乎一样，区别在于：**它们既能访问 MMIO，也能访问端口 I/O**。

这主要是为 PCI 设备准备的。有的 PCI 设备同时提供 MMIO 和端口 I/O 两种访问方式（第 10 篇会讲），驱动可以用 `pci_iomap` 得到一个统一的“cookie”，然后用 `ioread32` 访问，函数内部会自动判断这个 cookie 是 MMIO 地址还是端口号。

对于只有 MMIO 的设备（比如 ARM SoC 上的大部分设备），用 `readl` 系列就好。

### 2.4 块操作

第 4 篇讲过，不能用 `memcpy` 访问设备内存。Linux 提供了专门的版本：

| 函数 | 作用 |
|---|---|
| `memcpy_fromio(dst, src_io, len)` | 从设备内存拷贝到普通内存 |
| `memcpy_toio(dst_io, src, len)` | 从普通内存拷贝到设备内存 |
| `memset_io(dst_io, val, len)` | 把设备内存的一段设成某个值 |

它们内部会以安全的宽度、对齐方式逐个访问。

还有一类用于**反复读写同一个地址**的函数——典型场景是 FIFO 数据寄存器（第 3 篇）：

```c
readsl(base + FIFO_DATA, buf, count);    // 从同一地址连续读 count 个 32 位值
writesl(base + FIFO_DATA, buf, count);   // 往同一地址连续写 count 个 32 位值
```

注意和 `memcpy_fromio` 的区别：`memcpy_fromio` 的源地址是**递增**的（读一段连续的设备内存），`readsl` 的源地址是**固定**的（反复读同一个寄存器）。

### 2.5 轮询辅助宏

驱动里经常需要“轮询某个寄存器直到某一位变成某个值，但最多等多久”。自己写容易出错（忘了超时、忘了让出 CPU），Linux 提供了现成的宏（在 `<linux/iopoll.h>` 里）：

```c
u32 val;
int ret;

// 每 10 微秒读一次 STATUS，直到 READY 位为 1，最多等 1000 微秒
ret = readl_poll_timeout(base + STATUS, val, val & READY, 10, 1000);
if (ret)
    dev_err(dev, "设备没有在 1ms 内就绪\n");
```

它会反复读寄存器，把值放进 `val`，检查条件；超时返回 `-ETIMEDOUT`。还有一个 `_atomic` 版本，可以在不能睡眠的上下文（比如持有自旋锁时）里用。

### 2.6 小结

```
                        Linux MMIO 访问函数
                                │
      ┌──────────────┬──────────┼──────────────┬─────────────────┐
      ▼              ▼          ▼              ▼                 ▼
   单次读写        无屏障版    MMIO/PIO 通用    块操作              轮询
 readb/w/l/q    *_relaxed    ioread8/16/32  memcpy_fromio   readl_poll_timeout
 writeb/w/l/q                iowrite8/16/32 memcpy_toio
                                            memset_io
                                            readsl/writesl
```

---

## 三、资源管理：谁在用这块地址

### 3.1 防止两个驱动抢同一个设备

如果两个驱动都 `ioremap` 了同一个设备的地址，并且都去操作它的寄存器，设备的状态就会被搞乱。内核需要一种机制来记录“哪段物理地址已经被谁占用了”。

这就是 `request_mem_region`：

```c
if (!request_mem_region(0x09000000, 0x1000, "my-uart")) {
    pr_err("这段地址已经被别人占用了\n");
    return -EBUSY;
}

base = ioremap(0x09000000, 0x1000);
...
iounmap(base);
release_mem_region(0x09000000, 0x1000);
```

`request_mem_region` 不建立任何映射，它只是在内核的资源树里**登记**一笔：“`0x09000000`～`0x09000FFF` 现在归 `my-uart` 了”。如果这段地址已经被别人登记过，就返回失败。

还记得第 2 篇的 `/proc/iomem` 吗？

```
09000000-09000fff : pl011@9000000
  09000000-09000fff : 9000000.pl011 pl011@9000000
```

第一行是内核根据设备树登记的“这里有个设备”，缩进的第二行就是驱动通过 `request_mem_region`（或者它的封装）登记的“这个设备被我认领了”。`/proc/iomem` 就是这棵资源树的文本视图。

### 3.2 devm：自动清理

上面的代码有一个问题：申请和释放必须严格配对。如果驱动初始化到一半失败了，要记得把前面申请的东西逆序释放掉；如果忘了，就会造成资源泄漏。驱动里经常出现一大串 `goto err_xxx` 来处理这种情况，很容易写错。

Linux 提供了一套 **devm（device-managed，设备托管）** 版本的函数。它们会把申请的资源**挂在设备对象上**，当驱动卸载或初始化失败时，内核自动按逆序释放所有资源：

```c
// 申请 + 映射，一步到位，失败或卸载时自动释放
base = devm_ioremap_resource(dev, res);
if (IS_ERR(base))
    return PTR_ERR(base);
// 不需要写 iounmap 和 release_mem_region
```

`devm_ioremap_resource` 内部依次调用了 `devm_request_mem_region` 和 `devm_ioremap`，相当于把“登记”和“映射”合并成了一步。

现代 Linux 驱动几乎全部使用 devm 系列函数，代码因此简洁了很多。

---

## 四、从设备树到驱动

### 4.1 地址从哪里来

上面的例子里，`0x09000000` 是写死在代码里的。但第 2 篇说过，Linux 不会这样做——设备的地址应该来自**设备树**（或 ACPI、PCI 枚举）。

那么，设备树里的 `reg` 属性，是怎么变成驱动代码里的 `base` 指针的？

### 4.2 platform 设备与 platform 驱动

在 Linux 里，那些“不能自动发现、要靠设备树或 ACPI 描述”的设备（大多数 SoC 片上设备），统一叫做 **platform 设备**。对应的驱动叫 **platform 驱动**。

整个流程是：

```
① 启动时，内核解析设备树
       │
       │  发现节点：
       │  my-device@9100000 {
       │      compatible = "acme,demo-device";
       │      reg = <0x0 0x09100000 0x0 0x1000>;
       │      interrupts = <0 20 4>;
       │  };
       ▼
② 内核为它创建一个 platform_device 对象
   并把 reg 转换成一个“资源”(struct resource)：
   类型=MEM，起始=0x09100000，结束=0x09100FFF
       │
       ▼
③ 驱动注册时声明：我能驱动 compatible = "acme,demo-device" 的设备
       │
       ▼
④ 内核发现两者匹配，调用驱动的 probe 函数，把 platform_device 传进去
       │
       ▼
⑤ 驱动在 probe 里：取出资源 → ioremap → 开始访问寄存器
```

（这里的 `acme,demo-device` 是一个虚构的设备，只用于演示。）

### 4.3 在 probe 里拿到地址

第 ⑤ 步的典型写法：

```c
static int demo_probe(struct platform_device *pdev) {
    struct resource *res;
    void __iomem *base;

    // 取出第 0 个 MEM 类型的资源（对应设备树 reg 的第一段）
    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);

    // 登记 + 映射
    base = devm_ioremap_resource(&pdev->dev, res);
    if (IS_ERR(base))
        return PTR_ERR(base);
    ...
}
```

这个模式实在太常见了，于是内核又提供了一个更简洁的封装，一行搞定：

```c
base = devm_platform_ioremap_resource(pdev, 0);
```

这一行做了四件事：从设备树来的资源里取第 0 段地址、在资源树里登记、`ioremap` 建立映射、注册自动清理。

**驱动代码里从此不再出现任何具体的物理地址。** 同一个驱动，在不同的芯片上，只要设备树里的 `reg` 不同，就能自动适配。

---

## 五、一个最小驱动的骨架

现在把所有东西组合起来，看一个完整（但最小化）的 platform 驱动。假设我们有一个虚构的“演示设备”，它有三个寄存器：

```
偏移量    寄存器      作用
0x00      ID          只读，固定值 0xDE000001，用来确认设备存在
0x04      CTRL        控制：位 0 = 启用
0x08      COUNTER     只读，设备启用后每毫秒加 1
```

驱动的功能是：加载时启用设备，并通过 sysfs 文件把计数器的值暴露给用户。

```c
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/io.h>
#include <linux/of.h>

#define REG_ID       0x00
#define REG_CTRL     0x04
#define REG_COUNTER  0x08
#define CTRL_EN      BIT(0)
#define DEMO_ID      0xDE000001

struct demo_dev {
    void __iomem *base;
};

// 用户读 /sys/.../counter 时调用
static ssize_t counter_show(struct device *dev,
                            struct device_attribute *attr, char *buf)
{
    struct demo_dev *d = dev_get_drvdata(dev);
    u32 v = readl(d->base + REG_COUNTER);          // MMIO 读
    return sysfs_emit(buf, "%u\n", v);
}
static DEVICE_ATTR_RO(counter);

static int demo_probe(struct platform_device *pdev)
{
    struct demo_dev *d;
    u32 id;

    // 1. 分配驱动私有数据（devm：自动释放）
    d = devm_kzalloc(&pdev->dev, sizeof(*d), GFP_KERNEL);
    if (!d)
        return -ENOMEM;

    // 2. 拿到 MMIO 地址并映射
    d->base = devm_platform_ioremap_resource(pdev, 0);
    if (IS_ERR(d->base))
        return PTR_ERR(d->base);

    // 3. 读 ID 寄存器，确认设备真的在那里
    id = readl(d->base + REG_ID);
    if (id != DEMO_ID) {
        dev_err(&pdev->dev, "ID 不对：0x%08x\n", id);
        return -ENODEV;
    }

    // 4. 启用设备（读-改-写）
    writel(readl(d->base + REG_CTRL) | CTRL_EN, d->base + REG_CTRL);

    // 5. 保存私有数据，创建 sysfs 文件
    platform_set_drvdata(pdev, d);
    dev_info(&pdev->dev, "演示设备已启用\n");
    return device_create_file(&pdev->dev, &dev_attr_counter);
}

static void demo_remove(struct platform_device *pdev)
{
    struct demo_dev *d = platform_get_drvdata(pdev);

    device_remove_file(&pdev->dev, &dev_attr_counter);
    // 关闭设备
    writel(readl(d->base + REG_CTRL) & ~CTRL_EN, d->base + REG_CTRL);
    // base 的 iounmap 由 devm 自动完成
}

// 这个驱动能驱动哪些设备
static const struct of_device_id demo_of_match[] = {
    { .compatible = "acme,demo-device" },
    { }
};
MODULE_DEVICE_TABLE(of, demo_of_match);

static struct platform_driver demo_driver = {
    .probe  = demo_probe,
    .remove = demo_remove,
    .driver = {
        .name           = "demo-device",
        .of_match_table = demo_of_match,
    },
};
module_platform_driver(demo_driver);

MODULE_LICENSE("GPL");
```

（这是一个说明性的示例，省略了一些细节，比如 `remove` 回调的返回类型在不同内核版本中有过变化。）

### 5.1 逐段解读

- **`of_device_id` 表**：声明“我能驱动 `compatible = "acme,demo-device"` 的设备”。内核用这张表和设备树做匹配。
- **`module_platform_driver`**：一个宏，展开后就是模块加载时注册驱动、卸载时注销驱动。
- **`demo_probe`**：设备和驱动匹配成功后被调用。这里是驱动的“初始化”入口。
  - 第 2 步一行代码完成了“设备树 → 物理地址 → 登记 → 映射”的全过程；
  - 第 3 步读 ID 是一个好习惯：如果设备树写错了地址，或者设备没上电，读出来的 ID 就不对（可能是全 F 或 0，第 2 篇讲过），驱动可以及早发现问题，而不是在后面出现莫名其妙的错误；
  - 第 4 步是第 3 篇讲的读-改-写。
- **`counter_show`**：用户 `cat /sys/devices/platform/9100000.my-device/counter` 时被调用，每次都做一次真正的 MMIO 读。
- **`demo_remove`**：驱动卸载时被调用，关闭设备。映射的释放由 devm 自动完成。

### 5.2 这个骨架里的 MMIO 知识点

回顾一下，这短短几十行代码里用到了前面多少篇的知识：

| 代码 | 对应知识 |
|---|---|
| 设备树里的 `reg` | 第 2 篇：设备的地址从哪里来 |
| `devm_platform_ioremap_resource` | 本篇：登记 + 映射；第 5 篇：设置 Device 内存属性 |
| `void __iomem *` | 第 4 篇：不直接解引用，通过访问函数 |
| `readl` / `writel` | 第 4 篇：保证宽度；第 6 篇：自带屏障 |
| 读 ID 检查 | 第 2 篇：地址错误时可能读回全 F |
| 读-改-写 CTRL | 第 3 篇：位操作、读-改-写 |
| COUNTER 每次都要真读 | 第 3 篇：寄存器的值会被设备改变 |

一个真实的驱动还会有：中断处理（第 7 篇，用 `devm_request_irq`）、DMA（第 8 篇）、时钟和电源管理（设备没上电时访问寄存器可能卡死总线，第 2 篇提过）、锁（保护读-改-写）等等。但 MMIO 部分的骨架就是这样。

---

## 六、regmap：寄存器访问的抽象层

### 6.1 问题

有些设备不是通过 MMIO 访问的，而是通过 **I²C** 或 **SPI** 这类低速串行总线（比如很多传感器、电源管理芯片、音频编解码芯片）。它们也有“寄存器”的概念，但读写一个寄存器要通过总线发送一串数据，而不是一次内存访问。

更麻烦的是，同一款芯片可能有 MMIO 版本和 I²C 版本。如果为每种总线写一套驱动，大部分逻辑都是重复的。

### 6.2 regmap 的思路

Linux 提供了一个叫 **regmap** 的抽象层。驱动程序只需要调用统一的接口：

```c
regmap_read(map, REG_COUNTER, &val);
regmap_write(map, REG_CTRL, CTRL_EN);
regmap_update_bits(map, REG_CTRL, CTRL_EN, CTRL_EN);   // 读-改-写，带锁
```

至于底层是 MMIO、I²C 还是 SPI，在创建 `map` 的时候决定一次就行（比如 MMIO 设备用 `devm_regmap_init_mmio` 创建）。

regmap 还附送了很多实用功能：

- **`regmap_update_bits`**：内置锁保护的读-改-写，避免第 3 篇说的竞争问题；
- **寄存器缓存**：对于 I²C 这类慢速总线，regmap 可以在内存里缓存寄存器的值，读的时候不用真的去总线上读（当然，对于状态寄存器这种会自己变的，要标记为“易变的”，不缓存）；
- **调试接口**：通过 debugfs 可以直接查看和修改所有寄存器的值。

对于 MMIO 设备，用不用 regmap 是个选择题：简单的驱动直接用 `readl`/`writel` 更直接；复杂的、或者需要支持多种总线的驱动，用 regmap 更省事。

---

## 七、调试 MMIO 的常用手段

### 7.1 `/proc/iomem`

第 2 篇已经介绍过。排查“驱动加载失败，报 `-EBUSY`”这类问题时，先看 `/proc/iomem`，看看这段地址是不是已经被别的驱动认领了。

### 7.2 `devmem` 工具

`devmem`（BusyBox 自带）或 `devmem2` 是一个用户态小工具，可以直接读写任意物理地址：

```
# devmem 0x09100000 32          ← 读 32 位
0xDE000001
# devmem 0x09100004 32 0x1      ← 写 32 位
```

它的原理是通过 `/dev/mem` 把物理地址 mmap 到用户空间（第 11 篇详讲）。在调试新硬件时非常方便——不用写驱动，就能直接戳一戳寄存器，看看设备有没有反应。

**但要非常小心**：写错了地址可能导致系统崩溃；读了“读有副作用”的寄存器（第 3 篇）可能干扰驱动的正常工作。而且出于安全考虑，很多发行版的内核限制了 `/dev/mem` 的访问范围。

### 7.3 debugfs 寄存器转储

驱动可以用 `debugfs_create_regset32` 这样的辅助函数，在 debugfs 里创建一个文件，读这个文件就能一次性看到设备所有寄存器的当前值。很多驱动都提供了这样的调试文件，通常在 `/sys/kernel/debug/` 下面。使用 regmap 的驱动会自动获得类似的功能。

### 7.4 追踪 MMIO 访问

如果想知道驱动到底在什么时候、往哪个寄存器写了什么值：

- **x86 上的 `mmiotrace`**：内核内置的一个追踪器，可以记录指定驱动的所有 MMIO 访问。它最初是为了逆向分析闭源显卡驱动而开发的。
- **较新的内核里的 `rwmmio` 追踪事件**：开启相应的内核配置后，`readl`/`writel` 等访问函数会产生追踪事件，可以用 ftrace 记录下来。这是一个跨架构的方案。

### 7.5 常见错误速查

| 现象 | 可能的原因 |
|---|---|
| probe 返回 `-EBUSY` | 地址已被其他驱动占用，查 `/proc/iomem` |
| 读出来全是 `0xFFFFFFFF` | 地址错了、设备没上电、时钟没开、PCI 设备掉了 |
| 读出来全是 0 | 地址错了（落在空洞里）、设备没复位完 |
| 系统卡死 | 访问了没上电的设备，总线挂死 |
| 内核报 “Unable to handle kernel paging request” | 直接用物理地址当指针，或 `iounmap` 后还在访问 |
| sparse 报 “incorrect type in argument (different address spaces)” | `__iomem` 指针和普通指针混用 |

---

## 本篇小结

| 概念 | 一句话解释 |
|---|---|
| `ioremap` | 在内核页表里建立设备物理地址的映射，并设置 Device 属性 |
| `__iomem` | 标记设备指针，配合 sparse 检查，防止直接解引用 |
| `readb/w/l/q`、`writeb/w/l/q` | 8/16/32/64 位 MMIO 读写，带屏障 |
| `_relaxed` 版本 | 不带屏障，同设备内保序 |
| `ioread32` 系列 | MMIO 和端口 I/O 通用，常配合 `pci_iomap` |
| `memcpy_fromio` / `memcpy_toio` | 设备内存的安全拷贝 |
| `readsl` / `writesl` | 反复读写同一个 FIFO 寄存器 |
| `readl_poll_timeout` | 带超时的寄存器轮询 |
| `request_mem_region` | 在资源树里登记地址占用，防止冲突 |
| devm 系列 | 设备托管资源，失败或卸载时自动释放 |
| platform 设备/驱动 | 由设备树或 ACPI 描述的设备及其驱动 |
| `devm_platform_ioremap_resource` | 一行完成取资源、登记、映射、托管 |
| regmap | 统一 MMIO/I²C/SPI 的寄存器访问抽象 |
| `devmem` | 用户态直接读写物理地址的调试工具 |

**下一篇预告**：[《PCI 与 PCIe：设备地址是“谈”出来的》](10-pci-and-pcie.md)。platform 设备的地址是写在设备树里的，但你电脑里的显卡、网卡、NVMe 硬盘，它们的地址是从哪来的？我们会看到 PCI 设备如何通过“配置空间”和“BAR”与系统“谈判”出自己的 MMIO 地址。
