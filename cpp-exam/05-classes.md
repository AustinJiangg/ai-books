# 第 5 章　类 ★

类是 C++ 面向对象的核心。概念上与 Java 相似，但写法和细节有很多不同。本章讲类的定义和成员，构造与析构的深入内容放在第 6 章。

## 5.1　面向对象的三大特性

- **封装**：把数据和操作数据的函数绑在一起，隐藏内部实现，只通过公开接口访问。
- **继承**：在已有类的基础上定义新类，复用并扩展代码（第 8 章）。
- **多态**：同一个接口，不同对象有不同的行为（第 8 章）。

## 5.2　类的定义

```cpp
class Date {
public:                          // 公有：类外可以访问
    void set(int y, int m, int d);
    void print() const;          // const 成员函数，见 5.7
    int year() const { return y; }   // 类内定义，自动 inline
private:                         // 私有：只有成员函数和友元可以访问
    int y, m, d;
};                               // 分号不能省！

// 在类外定义成员函数，要用 类名:: 限定
void Date::set(int yy, int mm, int dd) {
    y = yy; m = mm; d = dd;      // 直接访问成员
}
void Date::print() const {
    cout << y << '-' << m << '-' << d << endl;
}

int main() {
    Date today;                  // 创建对象（不需要 new！）
    today.set(2026, 10, 4);
    today.print();               // 输出：2026-10-4
    // today.y = 2000;           错误：y 是 private
    Date* p = &today;
    p->print();                  // 指针用 ->
}
```

**与 Java 的重要区别**

- C++ 中 `Date today;` **直接创建了一个对象**（在栈上），而 Java 中 `Date today;` 只是一个空引用。
- C++ 中 `Date* p = new Date;` 才相当于 Java 的 `new`，用完要 `delete p;`。
- 访问控制按区段写，`public:` 之后的成员都是公有的，直到遇到下一个访问说明符。
- 类定义结尾有分号。

## 5.3　访问控制

| 访问说明符 | 类的成员函数 | 友元 | 派生类的成员函数 | 类外（通过对象） |
| --- | --- | --- | --- | --- |
| `public` | 可以 | 可以 | 可以 | 可以 |
| `protected` | 可以 | 可以 | 可以 | 不可以 |
| `private` | 可以 | 可以 | 不可以 | 不可以 |

- `class` 默认 `private`，`struct` 默认 `public`。
- **访问控制是按类的，不是按对象的**：同一个类的成员函数可以访问**另一个同类对象**的私有成员。

```cpp
class Point {
    int x, y;
public:
    bool equals(const Point& other) const {
        return x == other.x && y == other.y;   // 可以访问 other 的私有成员
    }
};
```

## 5.4　构造函数

构造函数在对象创建时**自动调用**，用于初始化对象。

- 名字与类名相同，**没有返回类型**（连 void 都不写）。
- 可以重载，可以有默认参数。
- 通常是 public 的。

```cpp
class Date {
    int y, m, d;
public:
    Date() { y = 2000; m = 1; d = 1; }              // 默认构造函数
    Date(int yy, int mm, int dd) { y = yy; m = mm; d = dd; }
    Date(int yy) { y = yy; m = 1; d = 1; }
};

Date d1;               // 调用 Date()
Date d2(2026, 10, 4);  // 调用 Date(int,int,int)
Date d3 {2026, 10, 4}; // 同上，列表初始化写法
Date d4 = 2026;        // 调用 Date(int)，隐式转换，见 5.6
Date* p = new Date(2026);  // 堆上创建
```

**易错（必考）**：`Date d5();` 不是创建对象，而是**声明了一个函数** d5，它不接受参数、返回 Date。要调用默认构造函数，写 `Date d5;` 或 `Date d5 {};`。

**默认构造函数**是指不需要实参就能调用的构造函数，包括所有参数都有默认值的构造函数。

- 如果类中**一个构造函数都没写**，编译器会自动生成一个默认构造函数（什么也不做，内置类型成员的值不确定）。
- **只要写了任何一个构造函数，编译器就不再自动生成默认构造函数。** 此时 `Date d;` 会报错，除非自己写一个，或用 `Date() = default;` 要求编译器生成。

```cpp
class A {
public:
    A(int x) { }
};
A a1(5);    // 可以
A a2;       // 错误：没有默认构造函数
A arr[3];   // 错误：对象数组需要默认构造函数
```

## 5.5　成员初始化列表

```cpp
class Date {
    int y, m, d;
public:
    Date(int yy, int mm, int dd) : y{yy}, m{mm}, d{dd} { }   // 初始化列表
};
```

初始化列表与在函数体内赋值的区别：初始化列表是**真正的初始化**，函数体中是**先默认初始化，再赋值**。

**以下情况必须使用初始化列表（必考）**：

1. `const` 数据成员。
2. 引用类型的数据成员。
3. 没有默认构造函数的类类型成员。
4. 基类没有默认构造函数时，初始化基类（第 8 章）。

```cpp
class B {
public:
    B(int) { }      // B 没有默认构造函数
};
class A {
    const int id;
    int& ref;
    B b;
public:
    A(int i, int& r) : id{i}, ref{r}, b{i} { }   // 三者都必须在初始化列表中
    // A(int i, int& r) { id = i; ... }          错误
};
```

**易错（读程序题常考）**：成员的初始化顺序**由成员在类中的声明顺序决定**，与初始化列表中的书写顺序无关。

```cpp
class X {
    int a;
    int b;
public:
    X(int v) : b{v}, a{b + 1} { }   // 先初始化 a（此时 b 还没初始化！），再初始化 b
};
// a 的值是不确定的
```

**C++11 类内成员初始化**：可以在声明成员时直接给默认值，构造函数没有初始化它时就使用这个值。

```cpp
class Date {
    int y {2000};
    int m {1};
    int d {1};
public:
    Date() { }                         // y=2000, m=1, d=1
    Date(int yy) : y{yy} { }           // y=yy, m=1, d=1
};
```

**委托构造函数（C++11）**：一个构造函数调用同类的另一个构造函数。

```cpp
class Date {
    int y, m, d;
public:
    Date(int yy, int mm, int dd) : y{yy}, m{mm}, d{dd} { }
    Date() : Date(2000, 1, 1) { }      // 委托给上面的构造函数
};
```

## 5.6　explicit 构造函数

**只用一个实参就能调用的构造函数**，会被编译器当作**隐式类型转换**。

```cpp
class Meter {
    double v;
public:
    Meter(double x) : v{x} { }
};
void show(Meter m);

Meter m = 3.5;   // 可以：double 隐式转换为 Meter
show(2.0);       // 可以：自动构造临时 Meter
```

这种隐式转换有时会带来意外。在构造函数前加 `explicit` 可以禁止它：

```cpp
class Meter {
    double v;
public:
    explicit Meter(double x) : v{x} { }
};
Meter m1(3.5);     // 可以：直接初始化
Meter m2 {3.5};    // 可以
// Meter m3 = 3.5; 错误：不允许隐式转换
// show(2.0);      错误
show(Meter{2.0});  // 可以：显式构造
```

Stroustrup 建议：单参数构造函数默认都加 `explicit`，除非确实需要隐式转换。

## 5.7　const 成员函数与 mutable

在成员函数参数表后加 `const`，表示**这个函数不会修改对象的状态**。

```cpp
class Date {
    int d;
public:
    int day() const { return d; }        // const 成员函数
    void addDay(int n) { d += n; }       // 非 const 成员函数
    // int bad() const { d++; return d; }  错误：const 函数不能修改成员
};

const Date cd;          // 常对象（这里假设有默认构造函数）
cd.day();               // 可以
// cd.addDay(1);        错误：常对象只能调用 const 成员函数
Date d;
d.day();                // 可以：非 const 对象两种函数都能调用
d.addDay(1);
```

**规则总结（必考）**

| 调用者 \\ 被调函数 | const 成员函数 | 非 const 成员函数 |
| --- | --- | --- |
| const 对象（或 const 引用、指向 const 的指针） | 可以 | **不可以** |
| 非 const 对象 | 可以 | 可以 |

- const 成员函数中不能修改数据成员，也**不能调用非 const 成员函数**。
- 函数声明和类外定义都要写 `const`：`int Date::day() const { ... }`。
- 可以按是否 `const` 重载：`int& at(int i);` 和 `const int& at(int i) const;`，const 对象调用后者。
- 只读的成员函数都应该声明为 const，否则用 `const&` 传进来的对象无法调用它。

**mutable**：被 `mutable` 修饰的数据成员，即使在 const 成员函数中也可以修改，常用于缓存、计数等不影响对象“逻辑状态”的成员。

```cpp
class Data {
    mutable int accessCount = 0;
    int value = 0;
public:
    int get() const { ++accessCount; return value; }   // 可以
};
```

**常数据成员**：`const int id;` 必须在构造函数的初始化列表中初始化（或用类内初始值），之后不能修改。

## 5.8　this 指针

每个非静态成员函数都有一个隐含参数 `this`，指向调用该函数的对象。

- 在类 X 的非 const 成员函数中，`this` 的类型是 `X*`；在 const 成员函数中是 `const X*`。
- `this` 本身不能被修改。

**用途 1：区分同名的参数和成员**

```cpp
class Point {
    int x, y;
public:
    void set(int x, int y) { this->x = x; this->y = y; }
};
```

**用途 2：返回对象自身，实现链式调用**

```cpp
class Counter {
    int n = 0;
public:
    Counter& add(int k) { n += k; return *this; }   // 返回自身的引用
    int get() const { return n; }
};
Counter c;
c.add(1).add(2).add(3);
cout << c.get();   // 6
```

**易错**：如果 `add` 返回 `Counter`（不带 &），返回的是副本，链式调用后面的 `add` 修改的是副本，`c.get()` 只得到 1。

## 5.9　static 成员

**静态数据成员**属于整个类，而不属于某个对象，所有对象共享同一份。

```cpp
class Student {
    string name;
    static int count;         // 声明：所有对象共享
public:
    Student(const string& n) : name{n} { ++count; }
    ~Student() { --count; }
    static int getCount() { return count; }   // 静态成员函数
};

int Student::count = 0;       // 定义并初始化：必须在类外，不加 static

int main() {
    cout << Student::getCount();   // 0，不需要对象，用 类名:: 调用
    Student a{"Tom"}, b{"Amy"};
    cout << a.getCount();          // 2，也可以通过对象调用
    {
        Student c{"Bob"};
        cout << Student::getCount(); // 3
    }
    cout << Student::getCount();   // 2，c 已被析构
}
```

**要点（必考）**

- 非 const 的静态数据成员**必须在类外定义一次**，形如 `int Student::count = 0;`，定义时不再写 `static`。
- `static const int` 整型成员或 `constexpr` 静态成员可以在类内直接初始化：`static const int max = 100;`。
- 静态数据成员在没有任何对象时就已经存在。
- `sizeof(对象)` 不包括静态数据成员。

**静态成员函数**

- **没有 this 指针**，所以**不能访问非静态成员**（数据或函数），只能访问静态成员。
- 不能声明为 `const` 或 `virtual`。
- 可以用 `类名::函数名()` 调用，不需要对象。

## 5.10　友元

友元可以访问类的私有和保护成员。友元**不是**类的成员。

**友元函数**

```cpp
class Point {
    int x, y;
public:
    Point(int a, int b) : x{a}, y{b} { }
    friend double dist(const Point& p, const Point& q);  // 声明友元
};

double dist(const Point& p, const Point& q) {   // 普通函数，不加 Point::，不加 friend
    int dx = p.x - q.x, dy = p.y - q.y;          // 可以访问私有成员
    return sqrt(dx * dx + dy * dy);
}
```

**友元类**：类 B 的所有成员函数都可以访问类 A 的私有成员。

```cpp
class A {
    int secret = 42;
    friend class B;
};
class B {
public:
    int peek(const A& a) { return a.secret; }   // 可以
};
```

**友元的性质（常考判断题）**

- 友元关系**不能继承**：B 是 A 的友元，B 的派生类不是 A 的友元。
- 友元关系**不是双向的**：B 是 A 的友元，A 不一定是 B 的友元。
- 友元关系**不能传递**：B 是 A 的友元，C 是 B 的友元，C 不是 A 的友元。
- 友元声明可以放在类中任意位置，不受 public/private 影响。
- 友元函数没有 this 指针，必须通过参数访问对象。
- 友元破坏了封装，应谨慎使用。最常见的用途是重载 `<<` 和 `>>` 运算符（第 7 章）。

## 5.11　对象数组与对象指针

```cpp
class P {
    int v;
public:
    P(int x = 0) : v{x} { cout << "C" << v << ' '; }
    ~P() { cout << "D" << v << ' '; }
};

int main() {
    P arr[3] {1, 2};          // arr[0]=1, arr[1]=2, arr[2] 用默认参数 0
    P* p = new P[2];          // 动态对象数组，每个元素调用默认构造函数
    delete[] p;
}
// 输出：C1 C2 C0 C0 C0 D0 D0 D0 D2 D1
```

解读：

- `arr` 依次构造 C1 C2 C0。
- `new P[2]` 构造 C0 C0；`delete[] p` 析构这两个，D0 D0。
- `main` 结束时 `arr` 的元素按**相反顺序**析构：D0 D2 D1。

## 5.12　本章小结

- C++ 中 `ClassName obj;` 直接创建对象；`ClassName obj();` 是函数声明。
- 写了任何构造函数后，编译器就不再生成默认构造函数。
- const 成员、引用成员、无默认构造函数的成员对象，必须用初始化列表初始化；初始化顺序按声明顺序。
- 单参数构造函数会引起隐式转换，用 `explicit` 禁止。
- const 对象只能调用 const 成员函数。
- 静态数据成员在类外定义；静态成员函数没有 this，不能访问非静态成员。
- 友元不能继承、不对称、不传递。
