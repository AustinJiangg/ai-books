# 第 12 章　考前速查 ★

考前最后一天读这一章。每一条都是一个常考点，看不懂的回到对应章节复习。

## 12.1　易错点汇总

**基础与指针（第 1–4 章）**

- 列表初始化 `int x {7.8};` 是窄化，编译错误。
- `auto` 会去掉引用：`auto a = ref;` 得到副本。
- `const int* p` 不能改 `*p`；`int* const p` 不能改 `p`。
- 引用必须初始化、不能为空、不能改绑；`r = y;` 是给被引用的变量赋值。
- 非 const 引用不能绑定字面量：`int& r = 5;` 错误，`const int& r = 5;` 正确。
- 不能返回局部变量的引用或指针。
- `new[]` 配 `delete[]`；`new` 调用构造函数，`malloc` 不调用。
- 数组作参数退化为指针，函数内 `sizeof(arr)` 是指针大小。
- `switch` 漏 `break` 会贯穿。
- 只有返回类型不同不能重载。
- 默认参数从右往左；声明和定义中只写一次。
- `static` 局部变量只初始化一次。
- lambda `[=]` 在定义时拷贝外部变量，之后外部变量变化不影响它。
- `enum class` 的值要写 `Color::red`，不能隐式转 int。

**类（第 5–7 章）**

- `Date d();` 是函数声明，不是创建对象。
- 写了任何构造函数，编译器就不再生成默认构造函数。
- const 成员、引用成员、无默认构造的成员对象必须在初始化列表中初始化。
- 成员按**声明顺序**初始化，与初始化列表顺序无关。
- const 对象只能调用 const 成员函数；const 成员函数不能修改成员（`mutable` 除外）。
- 静态数据成员要在类外定义：`int A::count = 0;`。
- 静态成员函数没有 this，不能访问非静态成员，不能是 const 或 virtual。
- 友元不能继承、不对称、不传递。
- 析构函数没有参数、不能重载。
- 拷贝构造参数必须是 `const X&`，不能按值传。
- `X b = a;` 调拷贝构造；`b = a;` 调拷贝赋值。
- 有指针成员时要深拷贝，遵守三法则/五法则。
- 拷贝赋值：防自我赋值 → 释放旧资源 → 复制 → `return *this;`。
- `std::move` 只是类型转换，不移动任何东西。
- 不能重载：`.` `.*` `::` `?:` `sizeof` `typeid`。
- `=` `[]` `()` `->` 只能是成员函数；`<<` `>>` 是非成员（友元）。
- 后置 `++` 有 `int` 哑元参数，返回旧值的副本。

**继承与多态（第 8 章）**

- 基类的 private 成员在派生类中不可直接访问（任何继承方式）。
- `class` 默认 private 继承。
- 构造：虚基类 → 基类 → 成员 → 自己；析构相反。
- 派生类同名函数隐藏基类**所有**同名函数。
- 多态 = virtual + 覆盖（签名完全一致）+ 基类指针/引用调用。通过对象调用不发生多态。
- 构造函数中调用虚函数不发生多态。
- 构造函数不能是虚函数；有虚函数的基类应有虚析构函数。
- 抽象类不能创建对象，但可以有指针和引用。
- 派生类没有覆盖全部纯虚函数，仍然是抽象类。
- `dynamic_cast` 指针失败返回 nullptr，引用失败抛 `bad_cast`。

**异常、模板、标准库（第 9–11 章）**

- catch 按顺序匹配，第一个匹配的执行；int 不匹配 double；派生类 catch 写在前，`catch(...)` 写在最后。
- 栈展开时局部对象被析构；构造函数抛异常时不调用该对象的析构函数。
- 函数模板推导不做隐式转换：`max(3, 2.5)` 推导失败。
- 类模板类外定义成员：`template <typename T> void Stack<T>::push(...)`。
- `vector<int> v(5, 7)` 是 5 个 7；`v {5, 7}` 是 2 个元素。
- map 的 `[]` 访问不存在的键会插入它。
- `end()` 是尾后位置，不能解引用。
- `unique_ptr` 不能拷贝，只能移动。

## 12.2　读程序题的解题步骤

1. **先找 main**，从第一行开始逐行“执行”，在草稿纸上记录每个变量和对象的值。
2. **每遇到一个对象定义**，问自己：调用哪个构造函数？是默认构造、带参构造、拷贝构造还是移动构造？如果有基类和成员对象，按“基类 → 成员 → 自己”的顺序写出所有输出。
3. **每遇到一次函数调用**，看参数传递方式：按值传对象会调用拷贝构造，函数结束时形参析构；按引用传则没有构造和析构。
4. **每遇到一个赋值号**，判断左边对象是否刚刚定义：是 → 构造；否 → 赋值运算符。
5. **每遇到通过指针或引用调用成员函数**，判断这个函数在基类中是否 virtual：是 → 看对象的实际类型；否 → 看指针的声明类型。
6. **每遇到 `}`**，把这个块中的局部对象按定义的**逆序**析构。
7. **main 结束后**，析构 main 中剩余的局部对象（逆序），再析构 static 局部对象和全局对象（逆序）。`new` 出来但没有 `delete` 的对象**不会析构**。
8. 最后**数一遍**：构造和析构的次数是否对应（没有 delete 的堆对象除外）。

**综合练习**（答案在下方）

```cpp
class Base {
public:
    Base() { cout << "B "; }
    Base(const Base&) { cout << "Bc "; }
    virtual void show() const { cout << "Base::show "; }
    void hi() const { cout << "Base::hi "; }
    virtual ~Base() { cout << "~B "; }
};
class Derived : public Base {
public:
    Derived() { cout << "D "; }
    void show() const override { cout << "Derived::show "; }
    void hi() const { cout << "Derived::hi "; }
    ~Derived() { cout << "~D "; }
};

void f1(Base b)        { b.show(); }
void f2(const Base& b) { b.show(); b.hi(); }

int main() {
    Derived d;
    f1(d);
    f2(d);
    Base* p = new Derived;
    p->show();
    delete p;
}
```

**答案与分析**

1. `Derived d;` → `B D`
2. `f1(d)`：按值传参，形参是 Base 类型，用 Base 的拷贝构造（切片）→ `Bc`；`b.show()` 通过对象调用，b 就是 Base → `Base::show`；函数结束形参析构 → `~B`
3. `f2(d)`：引用，不拷贝；`show` 是虚函数 → `Derived::show`；`hi` 非虚 → `Base::hi`
4. `new Derived` → `B D`；`p->show()` → `Derived::show`；`delete p`，虚析构 → `~D ~B`
5. main 结束，d 析构 → `~D ~B`

**完整输出**：`B D Bc Base::show ~B Derived::show Base::hi B D Derived::show ~D ~B ~D ~B`

## 12.3　编程大题模板

**模板 A：运算符重载类**（分数类）

```cpp
#include <iostream>
#include <stdexcept>
using namespace std;

int gcd_(int a, int b) { return b == 0 ? a : gcd_(b, a % b); }

class Fraction {
    int num, den;
    void reduce() {
        if (den < 0) { num = -num; den = -den; }
        int g = gcd_(num < 0 ? -num : num, den);
        if (g != 0) { num /= g; den /= g; }
    }
public:
    Fraction(int n = 0, int d = 1) : num{n}, den{d} {
        if (d == 0) throw invalid_argument("denominator is zero");
        reduce();
    }
    Fraction& operator+=(const Fraction& o) {
        num = num * o.den + o.num * den;
        den = den * o.den;
        reduce();
        return *this;
    }
    friend Fraction operator+(Fraction a, const Fraction& b) { return a += b; }
    friend Fraction operator-(const Fraction& a, const Fraction& b) {
        return Fraction(a.num * b.den - b.num * a.den, a.den * b.den);
    }
    friend Fraction operator*(const Fraction& a, const Fraction& b) {
        return Fraction(a.num * b.num, a.den * b.den);
    }
    friend bool operator==(const Fraction& a, const Fraction& b) {
        return a.num == b.num && a.den == b.den;
    }
    friend bool operator<(const Fraction& a, const Fraction& b) {
        return a.num * b.den < b.num * a.den;     // 分母已保证为正
    }
    Fraction& operator++() { num += den; return *this; }            // 前置：加 1
    Fraction operator++(int) { Fraction t = *this; ++*this; return t; }  // 后置
    friend ostream& operator<<(ostream& os, const Fraction& f) {
        if (f.den == 1) return os << f.num;
        return os << f.num << '/' << f.den;
    }
    friend istream& operator>>(istream& is, Fraction& f) {
        char slash;
        is >> f.num >> slash >> f.den;            // 输入格式如 3/4
        f.reduce();
        return is;
    }
};

int main() {
    Fraction a(1, 2), b(1, 3);
    cout << a + b << endl;      // 5/6
    cout << a - b << endl;      // 1/6
    cout << a * b << endl;      // 1/6
    cout << (b < a) << endl;    // 1
    cout << a++ << endl;        // 1/2（输出旧值）
    cout << a << endl;          // 3/2
    // 不要写成 cout << a++ << ' ' << a;：C++11 中同一表达式内的求值顺序不确定
    cout << a + 1 << endl;      // 5/2：1 隐式转换为 Fraction(1)
}
```

**模板 B：抽象基类 + 多态**（员工工资）

```cpp
#include <iostream>
#include <vector>
#include <memory>
#include <string>
using namespace std;

class Employee {
protected:
    string name;
public:
    explicit Employee(const string& n) : name{n} { }
    virtual double salary() const = 0;           // 纯虚函数
    virtual void print() const {
        cout << name << ": " << salary() << endl;  // 调用的是派生类的 salary
    }
    virtual ~Employee() = default;               // 虚析构
};

class Manager : public Employee {
    double fixed;
public:
    Manager(const string& n, double f) : Employee{n}, fixed{f} { }
    double salary() const override { return fixed; }
};

class HourlyWorker : public Employee {
    double rate;
    int hours;
public:
    HourlyWorker(const string& n, double r, int h) : Employee{n}, rate{r}, hours{h} { }
    double salary() const override {
        return hours <= 40 ? rate * hours : rate * 40 + rate * 1.5 * (hours - 40);
    }
};

class SalesPerson : public Employee {
    double base, sales;
public:
    SalesPerson(const string& n, double b, double s) : Employee{n}, base{b}, sales{s} { }
    double salary() const override { return base + sales * 0.05; }
    void print() const override {
        cout << "[Sales] ";
        Employee::print();                       // 调用基类版本
    }
};

int main() {
    vector<unique_ptr<Employee>> staff;          // 用智能指针，不必手动 delete
    staff.push_back(make_unique<Manager>("Alice", 8000));        // make_unique 是 C++14
    staff.push_back(make_unique<HourlyWorker>("Bob", 50, 45));
    staff.push_back(make_unique<SalesPerson>("Carol", 3000, 40000));

    double total = 0;
    for (const auto& e : staff) {
        e->print();
        total += e->salary();
    }
    cout << "Total: " << total << endl;
}
// 输出：
// Alice: 8000
// Bob: 2375
// [Sales] Carol: 5000
// Total: 15375
```

如果考试不允许用 `unique_ptr`，就用 `vector<Employee*>`，最后循环 `delete`。

**模板 C：管理资源的类（五法则）**

```cpp
class IntVec {
    int* data;
    size_t n;
public:
    explicit IntVec(size_t size = 0) : data{size ? new int[size]{} : nullptr}, n{size} { }

    IntVec(const IntVec& o) : data{o.n ? new int[o.n] : nullptr}, n{o.n} {   // 拷贝构造
        for (size_t i = 0; i < n; ++i) data[i] = o.data[i];
    }
    IntVec& operator=(const IntVec& o) {          // 拷贝赋值
        if (this != &o) {
            int* p = o.n ? new int[o.n] : nullptr;
            for (size_t i = 0; i < o.n; ++i) p[i] = o.data[i];
            delete[] data;
            data = p;
            n = o.n;
        }
        return *this;
    }
    IntVec(IntVec&& o) noexcept : data{o.data}, n{o.n} {   // 移动构造
        o.data = nullptr;
        o.n = 0;
    }
    IntVec& operator=(IntVec&& o) noexcept {      // 移动赋值
        if (this != &o) {
            delete[] data;
            data = o.data;  n = o.n;
            o.data = nullptr;  o.n = 0;
        }
        return *this;
    }
    ~IntVec() { delete[] data; }                  // 析构

    size_t size() const { return n; }
    int& operator[](size_t i) { return data[i]; }
    const int& operator[](size_t i) const { return data[i]; }
};
```

## 12.4　简答题常见问答

| 问题 | 答题要点 |
| --- | --- |
| 引用和指针的区别 | 引用必须初始化、不能为空、不能改绑、无需解引用；指针可为空、可改指向、有多级指针 |
| new/delete 与 malloc/free 的区别 | 运算符与函数；调用构造/析构；类型安全；失败抛 bad_alloc |
| 为什么需要虚析构函数 | 通过基类指针 delete 派生类对象时，确保调用派生类析构函数，避免资源泄漏 |
| 深拷贝与浅拷贝 | 浅拷贝只复制指针值，两个对象共享内存，导致重复释放；深拷贝分配新内存并复制内容 |
| 重载、覆盖、隐藏 | 见 8.8 节的表格：作用域、参数、virtual、绑定时机 |
| 什么是 RAII | 构造函数获取资源、析构函数释放资源，利用对象生命周期自动管理资源，异常安全 |
| 移动语义的作用 | 对临时对象直接转移资源所有权而不复制，提高效率 |
| 抽象类 | 含纯虚函数的类，不能实例化，作为接口供派生类实现 |
| 静态多态与动态多态 | 静态：函数重载、模板，编译时确定；动态：虚函数，运行时根据对象实际类型确定 |
| struct 与 class 的区别 | 默认访问权限和默认继承方式：struct 为 public，class 为 private |

祝考试顺利。
