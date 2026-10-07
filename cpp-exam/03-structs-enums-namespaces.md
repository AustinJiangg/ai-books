# 第 3 章　结构、枚举与名字空间 ☆

这一章内容不难，但 `enum class` 和名字空间是 C++11 教材的特色，选择填空容易考到。

## 3.1　struct

`struct` 把多个数据组合成一个新类型。

```cpp
struct Point {
    int x;
    int y;
};

Point p1 {1, 2};        // 列表初始化，x=1, y=2
Point p2 = p1;          // 整体拷贝（与数组不同，结构体可以整体赋值）
p2.x = 10;              // 不影响 p1
Point* pp = &p1;
cout << pp->x;          // 通过指针访问成员用 ->，等价于 (*pp).x
```

- C++ 中定义变量时可以省略 `struct` 关键字，直接写 `Point p;`（C 中要写 `struct Point p;`）。
- 结构体定义末尾的分号**不能省**。
- **C++ 中 struct 和 class 几乎一样**，都可以有成员函数、构造函数、继承。唯一的区别是：**struct 的成员和继承默认是 public，class 默认是 private**。

## 3.2　枚举：普通 enum

```cpp
enum Color { red, green, blue };     // 值依次为 0、1、2
enum Level { low = 1, mid = 5, high }; // high = 6

Color c = red;
int n = c;          // 可以：普通枚举可隐式转换为 int
// Color c2 = 1;    错误：int 不能隐式转换为枚举
```

普通枚举的问题：

1. 枚举值的名字直接暴露在外层作用域，容易冲突：再定义一个 `enum Light { red, yellow };` 就会和 `Color` 的 `red` 冲突。
2. 会隐式转换为 int，可能被误用。

## 3.3　枚举类 enum class（C++11）

```cpp
enum class Color { red, green, blue };
enum class Light { red, yellow, green };  // 不冲突

Color c = Color::red;          // 必须加作用域限定
// Color c2 = red;             错误
// int n = c;                  错误：不能隐式转换为 int
int n = static_cast<int>(c);   // 可以：显式转换，n = 0
if (c == Color::red) { }       // 可以：同类型比较
```

| 比较项 | `enum` | `enum class` |
| --- | --- | --- |
| 枚举值的作用域 | 外层作用域 | 限定在枚举内部，需写 `Color::red` |
| 隐式转换为 int | 可以 | 不可以，需 `static_cast` |
| 类型安全 | 弱 | 强 |

还可以指定底层类型：`enum class Flag : char { a, b };`。

## 3.4　名字空间 namespace

名字空间用来避免不同库之间的名字冲突，类似 Java 的 package。

```cpp
namespace MyLib {
    int count = 0;
    void hello() { cout << "MyLib hello"; }
    namespace Inner {             // 可以嵌套
        void hi() { }
    }
}

int main() {
    MyLib::hello();               // 用 :: 访问
    MyLib::Inner::hi();
    MyLib::count = 5;
}
```

**三种使用方式**

```cpp
std::cout << 1;            // 1. 每次写全名（最安全）

using std::cout;           // 2. using 声明：只引入一个名字
cout << 1;

using namespace std;       // 3. using 指令：引入整个名字空间的所有名字
cout << 1;
```

- 名字空间可以分多次定义，内容会合并。
- 没有名字的名字空间（匿名名字空间）中的名字只在当前文件内可见，作用类似 C 中的 `static` 全局变量。
- **全局作用域运算符**：`::x` 表示全局的 x，常用于局部变量遮蔽了全局变量时。

```cpp
int x = 1;
int main() {
    int x = 2;
    cout << x << ::x;      // 输出：21
}
```

**易错**：头文件中不要写 `using namespace std;`，因为包含这个头文件的所有文件都会受影响。

## 3.5　源文件与头文件的组织

一个程序通常分成多个文件：

- **头文件（.h）**：放**声明**，如类定义、函数原型、`extern` 变量声明。
- **源文件（.cpp）**：放**定义**，如函数体、全局变量定义。

```cpp
// point.h
#ifndef POINT_H          // 头文件保护：防止重复包含
#define POINT_H
struct Point { int x, y; };
double distance(Point a, Point b);   // 函数声明
extern int pointCount;               // 变量声明（不分配内存）
#endif

// point.cpp
#include "point.h"
#include <cmath>
int pointCount = 0;                  // 变量定义
double distance(Point a, Point b) {  // 函数定义
    return std::sqrt((a.x-b.x)*(a.x-b.x) + (a.y-b.y)*(a.y-b.y));
}

// main.cpp
#include "point.h"
int main() { Point p {1, 2}; }
```

**声明与定义的区别（常考）**

- **声明**告诉编译器“有这么个东西”，可以出现多次。
- **定义**真正创建它（分配内存或给出函数体），整个程序中只能出现一次，这叫**单一定义规则（ODR）**。
- `extern int x;` 是声明；`int x;` 和 `int x = 1;` 是定义。
- `#include <...>` 在系统目录中查找，`#include "..."` 先在当前目录中查找。

## 3.6　本章小结

- struct 与 class 的唯一区别是默认访问权限（struct 默认 public）。
- `enum class` 有作用域、不能隐式转为 int，访问写 `Color::red`。
- 名字空间用 `::` 访问；`using` 声明引入一个名字，`using namespace` 引入全部。
- 头文件放声明，源文件放定义；头文件要加保护宏。
