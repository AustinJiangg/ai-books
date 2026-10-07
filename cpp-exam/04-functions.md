# 第 4 章　函数 ★

本章的考点集中在参数传递、重载规则、默认参数、`static` 局部变量和 lambda。

## 4.1　声明与定义

```cpp
int add(int a, int b);          // 声明（原型），参数名可省略：int add(int, int);

int main() {
    cout << add(1, 2);          // 调用前必须先见到声明或定义
}

int add(int a, int b) {         // 定义
    return a + b;
}
```

- 函数必须先声明后使用。
- 返回类型不是 `void` 的函数必须在所有路径上 `return` 一个值。
- C++11 还可以写**尾置返回类型**：`auto add(int a, int b) -> int { return a + b; }`。

## 4.2　参数传递方式总结

| 写法 | 方式 | 是否拷贝 | 能否修改实参 | 典型用途 |
| --- | --- | --- | --- | --- |
| `void f(int x)` | 值传递 | 是 | 不能 | 小的内置类型 |
| `void f(int* p)` | 指针传递 | 拷贝地址 | 能（通过 \*p） | 可能为空的参数、数组 |
| `void f(int& x)` | 引用传递 | 否 | 能 | 需要修改实参 |
| `void f(const T& x)` | const 引用 | 否 | 不能 | 只读的大对象（string、vector、类对象） |
| `void f(T&& x)` | 右值引用 | 否 | 能（是临时对象） | 移动语义 |

**选择原则**：小对象只读用值传递；大对象只读用 `const&`；要修改实参用 `&`。

## 4.3　函数重载

同一作用域中，函数名相同、**参数列表不同**（个数、类型或顺序不同）的函数构成重载。

```cpp
int    max(int a, int b)         { return a > b ? a : b; }
double max(double a, double b)   { return a > b ? a : b; }
int    max(int a, int b, int c)  { return max(max(a, b), c); }

max(1, 2);       // 调用第 1 个
max(1.5, 2.5);   // 调用第 2 个
max(1, 2, 3);    // 调用第 3 个
```

**易错（必考）**

- **只有返回类型不同，不能构成重载**：`int f(int);` 和 `double f(int);` 冲突。
- 参数名不同不算不同：`f(int a)` 和 `f(int b)` 是同一个函数。
- 顶层 `const` 不算不同：`f(int)` 和 `f(const int)` 是同一个函数。
- 但 `f(int&)` 和 `f(const int&)` 可以重载；`f(int*)` 和 `f(const int*)` 也可以。
- 成员函数可以按是否 `const` 重载（第 5 章）。

**重载解析**：编译器按以下优先级选择最佳匹配：精确匹配 → 类型提升（如 char→int、float→double）→ 标准转换（如 int→double、double→int）→ 用户定义的转换。如果有两个同样好的候选，就是**二义性**，编译报错。

```cpp
void f(int);
void f(double);
f('a');     // char→int 是提升，调用 f(int)
f(1.0f);    // float→double 是提升，调用 f(double)
f(1L);      // long→int 和 long→double 都是标准转换，二义性，报错
```

## 4.4　默认参数

```cpp
void print(int a, int b = 10, int c = 20) {
    cout << a << ' ' << b << ' ' << c << endl;
}
print(1);         // 1 10 20
print(1, 2);      // 1 2 20
print(1, 2, 3);   // 1 2 3
```

**规则（必考）**

1. 默认参数必须**从右往左**连续给出：`void f(int a = 1, int b);` 是错误的。
2. 调用时实参从左往右匹配，不能跳过中间的参数：`print(1, , 3)` 是错误的。
3. 默认参数**只能指定一次**，通常写在声明中，定义中不再写。

```cpp
void g(int x = 5);          // 声明中给出默认值
void g(int x) { }           // 定义中不能再写 = 5
```

**默认参数与重载的二义性**：

```cpp
void h(int a);
void h(int a, int b = 0);
h(1);   // 二义性：两个都能匹配
```

## 4.5　inline 函数

```cpp
inline int square(int x) { return x * x; }
```

- `inline` 建议编译器在调用处直接展开函数体，省去函数调用的开销。只是建议，编译器可以不采纳。
- 适合短小、频繁调用的函数；不适合包含循环、递归的大函数。
- 与宏相比，`inline` 函数有类型检查，参数只求值一次，更安全。
- **在类定义内部定义的成员函数自动是 inline 的。**

宏的陷阱示例：

```cpp
#define SQ(x) x * x
cout << SQ(1 + 2);     // 展开为 1 + 2 * 1 + 2 = 5，而不是 9
cout << square(1 + 2); // 9
```

## 4.6　作用域与存储期

| 种类 | 定义位置 | 生命周期 | 未初始化时的值 |
| --- | --- | --- | --- |
| 局部变量 | 函数或块内 | 进入块时创建，离开块时销毁 | 不确定 |
| `static` 局部变量 | 函数内加 `static` | 第一次执行到定义时初始化，程序结束时销毁 | 0 |
| 全局变量 | 所有函数之外 | 整个程序运行期间 | 0 |
| 动态对象 | `new` 创建 | 直到 `delete` | 视写法而定 |

**static 局部变量（读程序题常考）**：只初始化一次，函数返回后值保留。

```cpp
void counter() {
    static int n = 0;   // 只在第一次调用时初始化
    int m = 0;          // 每次调用都重新初始化
    ++n; ++m;
    cout << n << m << ' ';
}
int main() {
    counter(); counter(); counter();
}
// 输出：11 21 31
```

**名字遮蔽**：内层作用域的名字会遮蔽外层的同名名字。

```cpp
int x = 1;
int main() {
    int x = 2;
    {
        int x = 3;
        cout << x;     // 3
    }
    cout << x;         // 2
    cout << ::x;       // 1
}
```

## 4.7　递归

函数直接或间接调用自身。必须有**终止条件**，否则会无限递归导致栈溢出。

```cpp
int fact(int n) {
    if (n <= 1) return 1;          // 终止条件
    return n * fact(n - 1);        // 递归调用
}

int fib(int n) {
    return n < 2 ? n : fib(n - 1) + fib(n - 2);
}
```

读递归程序时，画出调用树逐层展开，注意输出语句在递归调用**之前**还是**之后**：

```cpp
void f(int n) {
    if (n == 0) return;
    cout << n;      // 在递归之前输出
    f(n - 1);
    cout << n;      // 在递归之后输出
}
f(3);   // 输出：321123
```

## 4.8　函数指针（了解）

```cpp
int add(int a, int b) { return a + b; }
int (*pf)(int, int) = add;   // pf 是指向函数的指针
cout << pf(2, 3);            // 5
```

注意括号：`int* pf(int, int)` 是返回 `int*` 的函数声明，不是函数指针。

## 4.9　lambda 表达式（C++11）

lambda 是**匿名函数**，可以就地定义，常配合标准库算法使用。

**基本语法**：

```text
[捕获列表](参数列表) -> 返回类型 { 函数体 }
```

返回类型通常可以省略，由编译器推导。

```cpp
auto add = [](int a, int b) { return a + b; };
cout << add(2, 3);              // 5

vector<int> v {5, 2, 8, 1};
sort(v.begin(), v.end(), [](int a, int b) { return a > b; });  // 降序
// v: 8 5 2 1
```

**捕获列表（必考）**：决定 lambda 能否使用外部的局部变量，以及如何使用。

| 写法 | 含义 |
| --- | --- |
| `[]` | 不捕获任何外部变量 |
| `[x]` | 按值捕获 x（复制一份，lambda 内不能修改） |
| `[&x]` | 按引用捕获 x（可以修改外部的 x） |
| `[=]` | 按值捕获所有用到的外部变量 |
| `[&]` | 按引用捕获所有用到的外部变量 |
| `[=, &x]` | x 按引用，其余按值 |
| `[&, x]` | x 按值，其余按引用 |
| `[this]` | 捕获当前对象，可访问成员 |

```cpp
int a = 1, b = 2;
auto f1 = [a]() { return a + 10; };
auto f2 = [&b]() { b = 100; };
a = 50;
cout << f1();     // 11：按值捕获的是定义 lambda 时 a 的值 1
f2();
cout << b;        // 100
```

**易错**：

- 按值捕获发生在 **lambda 定义时**，之后外部变量的变化不会影响 lambda 中的副本。
- 按值捕获的变量在 lambda 内默认不能修改；如果要修改副本，需加 `mutable`：`[a]() mutable { a++; }`，修改的仍只是副本。
- 全局变量和 `static` 变量不需要捕获就能直接使用。

```cpp
int count = 0;
vector<int> v {1, 2, 3, 4, 5, 6};
for_each(v.begin(), v.end(), [&count](int x) { if (x % 2 == 0) ++count; });
cout << count;    // 3
```

## 4.10　本章小结

- 只有返回类型不同不能构成重载；有两个同等匹配时是二义性错误。
- 默认参数从右往左给出，只能在声明或定义中指定一次。
- `static` 局部变量只初始化一次，值在调用之间保留。
- 类内定义的成员函数自动 inline。
- lambda 的 `[=]` 按值捕获（定义时拷贝），`[&]` 按引用捕获。
