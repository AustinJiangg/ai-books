# 第 1 章　基础：类型、变量与表达式 ☆

C++ 的基础语法与 C 基本相同，本章只讲考试关心的部分，以及 C++11 新增的写法。

## 1.1　最小的 C++ 程序

```cpp
#include <iostream>      // 输入输出流头文件，注意没有 .h
using namespace std;     // 使用标准名字空间，之后可以直接写 cout

int main() {
    int a, b;
    cin >> a >> b;                    // 从键盘读入两个整数
    cout << "sum = " << a + b << endl; // 输出，endl 表示换行并刷新
    return 0;                         // main 可以省略 return，默认返回 0
}
```

- `cout` 是输出流对象，`<<` 是插入运算符，可以连写。
- `cin` 是输入流对象，`>>` 是提取运算符，以空白字符分隔输入。
- 如果不写 `using namespace std;`，就要写成 `std::cout`、`std::endl`。Stroustrup 的书中通常写 `std::` 前缀。
- `main` 的返回类型必须是 `int`。

## 1.2　基本类型

| 类型 | 典型大小 | 说明 |
| --- | --- | --- |
| `bool` | 1 字节 | 取值 `true` / `false`；与整数相互转换时，非 0 为 `true` |
| `char` | 1 字节 | 字符，本质是小整数 |
| `int` | 4 字节 | 整数 |
| `long long` | 8 字节 | 长整数（C++11） |
| `float` | 4 字节 | 单精度浮点 |
| `double` | 8 字节 | 双精度浮点，默认的浮点字面量类型 |
| `void` | — | 表示“无类型”，用于函数返回值和 `void*` |

- 类型大小由实现决定，标准只保证 `1 == sizeof(char) <= sizeof(short) <= sizeof(int) <= sizeof(long) <= sizeof(long long)`。
- `sizeof` 是运算符，不是函数，结果以字节为单位。
- `unsigned` 类型没有负数，`unsigned int x = -1;` 得到一个很大的正数。

**字面量**：`10`（int）、`10L`（long）、`10u`（unsigned）、`3.14`（double）、`3.14f`（float）、`'a'`（char）、`"abc"`（字符串字面量，类型是 `const char[4]`，末尾有隐含的 `'\0'`）、`0x1F`（十六进制）、`017`（八进制）。

**易错**：`sizeof("abc")` 的值是 4，因为包括末尾的 `'\0'`。

## 1.3　初始化的三种写法

C++11 提供了统一的花括号初始化（列表初始化），Stroustrup 推荐优先使用它。

```cpp
int a = 7;      // 传统写法
int b(7);       // 构造函数风格
int c {7};      // 列表初始化（C++11）
int d = {7};    // 也是列表初始化

int e {};       // 值初始化，e 为 0
int f;          // 局部变量未初始化，值不确定！
```

**列表初始化的重要特点：禁止窄化转换。** 窄化是指可能丢失信息的转换，例如 double 转 int。

```cpp
int x1 = 7.8;   // 可以编译，x1 = 7（小数被截断）
int x2 {7.8};   // 编译错误：窄化转换
char c1 {300};  // 编译错误：300 超出 char 的范围
```

**易错**：全局变量和 `static` 变量未初始化时自动为 0；局部变量未初始化时值是随机的。

## 1.4　auto 与 decltype

`auto` 让编译器根据初始值推导变量类型。

```cpp
auto i = 10;        // int
auto d = 3.14;      // double
auto s = "hi";      // const char*
auto b {true};      // bool

vector<int> v {1, 2, 3};
auto it = v.begin(); // vector<int>::iterator，写起来方便很多
```

- `auto` 变量**必须初始化**，否则无法推导。
- `auto` 会去掉顶层的 `const` 和引用。如果要引用，写 `auto&`；要常量引用，写 `const auto&`。

```cpp
int x = 5;
int& rx = x;
auto a = rx;     // a 是 int（复制了一份），不是引用
a = 100;         // x 仍是 5
auto& b = rx;    // b 是 int&
b = 100;         // x 变为 100
```

`decltype(表达式)` 得到表达式的类型，但不计算表达式：

```cpp
int x = 1;
decltype(x) y = 2;      // y 是 int
decltype(x + 1.0) z;    // z 是 double
```

## 1.5　const 与 constexpr

- `const`：**我承诺不修改它**。值可以在运行时才确定。
- `constexpr`：**在编译时就能算出来**。用于数组大小、模板参数等需要常量表达式的地方。

```cpp
const int a = 10;          // 常量，必须初始化
int n;
cin >> n;
const int b = n;           // 可以：运行时确定，之后不能改
constexpr int c = 10 * 2;  // 可以：编译时就能算出
constexpr int d = n;       // 错误：n 在编译时未知

constexpr int square(int x) { return x * x; }  // constexpr 函数
int arr[square(3)];        // 可以：数组大小为 9
```

**易错**：`const` 变量必须在定义时初始化，之后任何赋值都是编译错误。

## 1.6　运算符要点

大部分运算符与 C、Java 一致，考试常考以下几点。

**整数除法与取余**

```cpp
cout << 7 / 2;     // 3（整数相除，结果截断）
cout << 7 / 2.0;   // 3.5
cout << -7 / 2;    // -3（C++11 起向 0 截断）
cout << -7 % 3;    // -1（余数符号与被除数相同）
```

**自增自减**

```cpp
int i = 5;
int a = i++;   // a = 5, i = 6（先用后加）
int b = ++i;   // b = 7, i = 7（先加后用）
```

**易错**：`i = i++ + ++i;` 这类在一个表达式里多次修改同一变量的写法是**未定义行为**，结果不确定。考试如果出这种题，答“未定义”。

**逻辑运算的短路**

```cpp
int x = 0;
if (x != 0 && 10 / x > 1) { }  // && 左边为假，右边不再计算，不会除 0
int a = 0, b = 0;
if (a++ || b++) { }           // a++ 的值为 0（假），所以计算 b++
// 此时 a = 1, b = 1
```

**条件运算符与逗号运算符**

```cpp
int m = (a > b) ? a : b;   // 取较大值
int k = (a = 1, b = 2, a + b);  // 逗号表达式的值是最后一个表达式的值，k = 3
```

**赋值与相等**：`if (x = 5)` 是赋值，条件永远为真；比较要写 `==`。

**优先级口诀（从高到低）**：作用域 `::` → 后缀（`()` `[]` `->` `.` `后置++`）→ 单目（`!` `~` `前置++` `*` `&` `sizeof` `new` `delete`）→ 乘除余 → 加减 → 移位 → 关系 → 相等 → 位与 → 异或 → 位或 → 逻辑与 → 逻辑或 → 条件 → 赋值 → 逗号。拿不准时加括号。

## 1.7　类型转换

**隐式转换**：算术运算中，较小的类型自动提升为较大的类型。`char`、`short` 先提升为 `int`；`int` 与 `double` 运算时转为 `double`。

```cpp
int i = 3;
double d = i / 2;     // 1.0：先整数除得 1，再转为 double
double e = i / 2.0;   // 1.5
```

**显式转换**：C++ 推荐使用具名转换，而不是 C 风格的 `(int)x`。

| 写法 | 用途 |
| --- | --- |
| `static_cast<T>(x)` | 常规的、编译器能检查的转换，如 double→int、基类指针→派生类指针（不检查） |
| `dynamic_cast<T>(x)` | 多态类型的安全向下转换，运行时检查（第 8 章） |
| `const_cast<T>(x)` | 去掉或加上 `const` |
| `reinterpret_cast<T>(x)` | 按位重新解释，如指针↔整数，很危险 |

```cpp
double d = 3.7;
int n = static_cast<int>(d);   // n = 3
```

## 1.8　语句：选择与循环

`if`、`switch`、`while`、`do-while`、`for` 的用法与 C/Java 相同。注意：

- `switch` 的 `case` 后必须是整型常量表达式；**没写 `break` 会继续执行下一个 case**（贯穿）。
- `do { } while (条件);` 至少执行一次，末尾有分号。
- `break` 跳出最内层循环或 switch；`continue` 跳到下一次循环。

```cpp
int x = 2;
switch (x) {
    case 1: cout << "A";
    case 2: cout << "B";   // 从这里进入
    case 3: cout << "C";   // 没有 break，继续执行
            break;
    default: cout << "D";
}
// 输出：BC
```

**范围 for 循环（C++11）**：遍历数组或容器的每个元素，与 Java 的 for-each 类似。

```cpp
int arr[] {1, 2, 3, 4};
for (int x : arr)        // x 是元素的副本
    cout << x << ' ';    // 输出：1 2 3 4

for (int& x : arr)       // x 是元素的引用，可以修改原数组
    x *= 2;              // arr 变为 2 4 6 8

for (const auto& x : arr) // 只读且不拷贝，处理大对象时常用
    cout << x << ' ';
```

**易错**：想通过范围 for 修改元素，必须写 `&`，否则改的是副本。

## 1.9　本章小结

- 列表初始化 `{}` 禁止窄化转换。
- `auto` 必须初始化，并且会去掉引用和顶层 `const`。
- `const` 表示不修改，`constexpr` 表示编译期可求值。
- 整数相除会截断；`&&` 和 `||` 会短路。
- `switch` 中漏写 `break` 会贯穿；范围 for 要修改元素需用引用。
