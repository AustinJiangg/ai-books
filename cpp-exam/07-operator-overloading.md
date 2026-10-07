# 第 7 章　运算符重载 ★

运算符重载让自定义类型像内置类型一样使用运算符，例如两个复数可以直接写 `a + b`。Java 不支持运算符重载，这是 C++ 编程大题的高频考点。

## 7.1　基本概念与规则

运算符重载本质上是一个**名字特殊的函数**：`operator` 加上运算符符号。

```cpp
Complex operator+(const Complex& a, const Complex& b);
// a + b 等价于 operator+(a, b)
```

**不能重载的运算符（必考）**：

| 运算符 | 含义 |
| --- | --- |
| `.` | 成员访问 |
| `.*` | 成员指针访问 |
| `::` | 作用域解析 |
| `?:` | 条件运算符 |
| `sizeof` | 求大小 |
| `typeid` | 类型信息 |

记法：**带“点”的和 `sizeof`、`?:`、`::` 不能重载**。

**重载的规则（必考）**

1. 不能创造新的运算符，比如不能定义 `**`。
2. **不能改变运算符的操作数个数、优先级和结合性。**
3. 至少有一个操作数是用户自定义类型，不能改变内置类型的运算（不能重载 `int + int`）。
4. 不能有默认参数。
5. `=`、`[]`、`()`、`->` **只能重载为成员函数**。
6. `<<`、`>>`（用于流）通常只能重载为**非成员函数**（友元），因为左操作数是 `ostream`/`istream`。

## 7.2　成员函数与非成员函数两种形式

| 比较项 | 成员函数形式 | 非成员（友元）函数形式 |
| --- | --- | --- |
| 双目运算符的参数个数 | 1 个（左操作数是 `*this`） | 2 个 |
| 单目运算符的参数个数 | 0 个（后置 ++/-- 例外，见 7.5） | 1 个 |
| 左操作数 | 必须是本类对象 | 可以是任意类型 |
| `a + b` 的含义 | `a.operator+(b)` | `operator+(a, b)` |

**如何选择**

- `=`、`[]`、`()`、`->`、复合赋值 `+=` 等修改对象本身的运算符 → 成员函数。
- 对称的双目运算符（`+`、`-`、`==`、`<`）→ 非成员函数更好，因为左右两边都可以发生隐式转换。
- `<<`、`>>` → 必须是非成员函数。

**为什么对称运算符要用非成员？**

```cpp
class Complex {
public:
    Complex(double r = 0, double i = 0);   // double 可以隐式转换为 Complex
    Complex operator+(const Complex& b) const;   // 成员形式
};
Complex c(1, 2);
c + 1.0;     // 可以：c.operator+(Complex(1.0))
1.0 + c;     // 错误：1.0 不是对象，不能调用成员函数
```

如果改为非成员函数 `Complex operator+(const Complex&, const Complex&)`，两种写法都可以。

## 7.3　完整示例：复数类

这是最常见的编程大题，建议**背熟这个模板**。

```cpp
#include <iostream>
using namespace std;

class Complex {
    double re, im;
public:
    Complex(double r = 0, double i = 0) : re{r}, im{i} { }

    double real() const { return re; }
    double imag() const { return im; }

    // 复合赋值：成员函数，返回自身引用
    Complex& operator+=(const Complex& b) {
        re += b.re; im += b.im;
        return *this;
    }
    Complex& operator-=(const Complex& b) {
        re -= b.re; im -= b.im;
        return *this;
    }

    // 单目负号：成员函数，无参数
    Complex operator-() const { return Complex(-re, -im); }

    // 双目运算：友元函数，两个参数
    friend Complex operator+(const Complex& a, const Complex& b);
    friend Complex operator*(const Complex& a, const Complex& b);
    friend bool operator==(const Complex& a, const Complex& b);

    // 流运算符：必须是友元
    friend ostream& operator<<(ostream& os, const Complex& c);
    friend istream& operator>>(istream& is, Complex& c);
};

Complex operator+(const Complex& a, const Complex& b) {
    return Complex(a.re + b.re, a.im + b.im);
}
Complex operator*(const Complex& a, const Complex& b) {
    return Complex(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re);
}
bool operator==(const Complex& a, const Complex& b) {
    return a.re == b.re && a.im == b.im;
}
bool operator!=(const Complex& a, const Complex& b) {
    return !(a == b);           // 用 == 实现 !=，不需要友元
}
ostream& operator<<(ostream& os, const Complex& c) {
    os << "(" << c.re << ", " << c.im << ")";
    return os;                  // 返回流的引用，支持连续输出
}
istream& operator>>(istream& is, Complex& c) {
    is >> c.re >> c.im;         // c 不能是 const，因为要修改它
    return is;
}

int main() {
    Complex a(1, 2), b(3, 4);
    Complex c = a + b;
    cout << c << endl;          // (4, 6)
    cout << a * b << endl;      // (-5, 10)
    a += b;
    cout << a << -a << endl;    // (4, 6)(-4, -6)
    cout << (a == c) << endl;   // 1
    Complex d = 2.5 + a;        // 2.5 隐式转换为 Complex(2.5, 0)
    cout << d << endl;          // (6.5, 6)
}
```

**返回值类型的选择（必考）**

| 运算符 | 返回类型 | 原因 |
| --- | --- | --- |
| `+` `-` `*` `/` | 值（`Complex`） | 产生一个新对象；不能返回局部对象的引用 |
| `+=` `-=` `=` | 引用（`Complex&`） | 返回对象自身，支持 `(a += b) += c`、`a = b = c` |
| `==` `<` 等 | `bool` | 比较结果 |
| `<<` `>>` | `ostream&` / `istream&` | 支持 `cout << a << b` 连续输出 |
| 前置 `++` | 引用 | 返回修改后的对象自身 |
| 后置 `++` | 值 | 返回修改前的副本 |
| `[]` | 引用 | 可以作左值：`a[i] = 5` |

## 7.4　重载 << 和 >> 的要点

```cpp
ostream& operator<<(ostream& os, const T& obj);
istream& operator>>(istream& is, T& obj);
```

**易错（必考）**

1. 必须是非成员函数，通常声明为友元以访问私有成员。如果写成成员函数，调用形式会变成 `obj << cout`，不符合习惯。
2. 第一个参数和返回值都是**流的引用**。流对象不能拷贝，所以不能按值传递或返回。
3. `<<` 的第二个参数用 `const T&`；`>>` 的第二个参数用 `T&`（要修改）。
4. 函数内用参数 `os` 输出，而不是 `cout`，这样也可以输出到文件流。
5. 最后要 `return os;`。

## 7.5　自增自减：前置与后置（必考）

前置和后置通过一个**额外的 int 哑元参数**来区分：

```cpp
class Counter {
    int n;
public:
    Counter(int x = 0) : n{x} { }

    Counter& operator++() {        // 前置 ++c：无参数
        ++n;
        return *this;              // 返回修改后的自身（引用）
    }

    Counter operator++(int) {      // 后置 c++：int 参数仅用于区分，不使用
        Counter old = *this;       // 保存旧值
        ++n;                       // 也可以写 ++(*this);
        return old;                // 返回旧值（按值）
    }

    int get() const { return n; }
};

int main() {
    Counter c(5);
    Counter a = ++c;    // c = 6, a = 6
    Counter b = c++;    // b = 6, c = 7
    cout << a.get() << b.get() << c.get();   // 667
}
```

如果写成友元函数：前置为 `friend Counter& operator++(Counter& c);`，后置为 `friend Counter operator++(Counter& c, int);`。

**为什么前置效率更高**：后置需要构造一个旧值副本并按值返回，前置不需要。所以 C++ 中推荐写 `++i`。

## 7.6　赋值运算符

赋值运算符只能是成员函数。如果没写，编译器会生成一个逐成员赋值（浅拷贝）的版本。类中有指针成员时，必须自己写深拷贝版本（见 6.5）。

```cpp
T& operator=(const T& other) {
    if (this != &other) {     // 1. 防自我赋值
        // 2. 释放旧资源
        // 3. 复制 other 的资源
    }
    return *this;             // 4. 返回自身引用
}
```

## 7.7　下标运算符 [] 与函数调用运算符 ()

**下标运算符**：只能是成员函数，通常提供 const 和非 const 两个版本。

```cpp
class IntArray {
    int* data;
    int size;
public:
    IntArray(int n) : data{new int[n]{}}, size{n} { }
    ~IntArray() { delete[] data; }

    int& operator[](int i) {                 // 非 const 对象调用，可修改
        if (i < 0 || i >= size) throw out_of_range("index");
        return data[i];
    }
    const int& operator[](int i) const {     // const 对象调用，只读
        if (i < 0 || i >= size) throw out_of_range("index");
        return data[i];
    }
};

IntArray arr(5);
arr[2] = 10;               // 返回引用，所以能作左值
cout << arr[2];            // 10
```

（这个类还需要按三法则补上拷贝构造和拷贝赋值，此处省略。）

**函数调用运算符**：重载了 `()` 的类对象可以像函数一样调用，叫做**函数对象**（仿函数）。

```cpp
class Less {
public:
    bool operator()(int a, int b) const { return a < b; }
};
Less cmp;
cout << cmp(1, 2);         // 1，等价于 cmp.operator()(1, 2)
sort(v.begin(), v.end(), Less{});   // 可以作为算法的比较器
```

lambda 表达式实际上就是编译器自动生成的函数对象。

## 7.8　类型转换

**转换构造函数**：其他类型 → 本类。即只需一个实参的构造函数（见 5.6）。

**类型转换运算符**：本类 → 其他类型。

```cpp
class Fraction {
    int num, den;
public:
    Fraction(int n, int d = 1) : num{n}, den{d} { }   // 转换构造：int → Fraction
    operator double() const {                          // 转换运算符：Fraction → double
        return static_cast<double>(num) / den;
    }
};

Fraction f(3, 4);
double d = f;          // 0.75，隐式调用 operator double()
double e = f + 1.0;    // 1.75：f 先转为 double
```

**转换运算符的特点**：

- 形式为 `operator 类型名() const`，**不写返回类型**，**没有参数**。
- 必须是成员函数。
- 可以加 `explicit`（C++11），此时只能显式转换：`static_cast<double>(f)`，或在 `if (f)` 这类条件中使用（针对 `explicit operator bool`）。

**易错**：同时提供转换构造函数和转换运算符时，容易产生二义性。例如上面的 Fraction 若再重载 `Fraction operator+(const Fraction&, const Fraction&)`，那么 `f + 1` 既可以把 1 转成 Fraction，也可以把 f 转成 double，编译器报二义性错误。

## 7.9　完整示例：字符串类（深拷贝 + 运算符重载）

```cpp
#include <iostream>
#include <cstring>
using namespace std;

class MyString {
    char* p;
    int len;
public:
    MyString(const char* s = "") {
        len = strlen(s);
        p = new char[len + 1];
        strcpy(p, s);
    }
    MyString(const MyString& o) : len{o.len} {       // 拷贝构造
        p = new char[len + 1];
        strcpy(p, o.p);
    }
    MyString& operator=(const MyString& o) {         // 拷贝赋值
        if (this != &o) {
            char* np = new char[o.len + 1];
            strcpy(np, o.p);
            delete[] p;
            p = np;
            len = o.len;
        }
        return *this;
    }
    ~MyString() { delete[] p; }

    int size() const { return len; }
    char& operator[](int i) { return p[i]; }
    const char& operator[](int i) const { return p[i]; }

    friend MyString operator+(const MyString& a, const MyString& b) {
        char* tmp = new char[a.len + b.len + 1];
        strcpy(tmp, a.p);
        strcat(tmp, b.p);
        MyString r(tmp);
        delete[] tmp;
        return r;
    }
    friend bool operator==(const MyString& a, const MyString& b) {
        return strcmp(a.p, b.p) == 0;
    }
    friend ostream& operator<<(ostream& os, const MyString& s) {
        return os << s.p;
    }
};

int main() {
    MyString a("Hello"), b(" World");
    MyString c = a + b;
    cout << c << ' ' << c.size() << endl;   // Hello World 11
    c[0] = 'h';
    cout << c << endl;                      // hello World
    a = c;
    cout << (a == c) << endl;               // 1
}
```

注意：友元函数可以直接定义在类内，它仍然不是成员函数。

## 7.10　本章小结

- 不能重载：`.`、`.*`、`::`、`?:`、`sizeof`、`typeid`。
- 重载不能改变操作数个数、优先级、结合性。
- `=`、`[]`、`()`、`->` 只能是成员；`<<`、`>>` 只能是非成员。
- 成员形式的双目运算符只有 1 个参数；友元形式有 2 个。
- `+` 返回值，`+=` 和 `=` 返回 `*this` 的引用，`<<` 返回 `ostream&`。
- 后置 `++` 带 `int` 哑元参数，返回旧值的副本；前置 `++` 返回自身引用。
- 转换运算符 `operator T()` 不写返回类型、没有参数。
