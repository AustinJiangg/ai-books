# 第 9 章　异常处理 ☆

C++ 的异常机制与 Java 类似，但有几点不同：可以抛出**任何类型**的值（包括 int、string），没有 `finally`，也没有受检异常。

## 9.1　基本语法

```cpp
double divide(double a, double b) {
    if (b == 0)
        throw runtime_error("divide by zero");   // 抛出异常对象
    return a / b;
}

int main() {
    try {
        cout << divide(10, 2) << endl;   // 5
        cout << divide(1, 0) << endl;    // 抛出异常，后面的语句不再执行
        cout << "不会执行" << endl;
    }
    catch (const runtime_error& e) {     // 捕获
        cout << "错误：" << e.what() << endl;
    }
    cout << "程序继续" << endl;
}
// 输出：
// 5
// 错误：divide by zero
// 程序继续
```

- `throw 表达式;` 抛出异常，当前函数立即停止执行。
- `try` 块中出现异常后，跳到匹配的 `catch` 块，`try` 块中剩下的语句不再执行。
- 执行完 `catch` 块后，继续执行整个 try-catch 结构之后的语句，**不会回到抛出点**。
- 如果没有任何 `catch` 能匹配，异常会沿调用链向上传递；一直到 `main` 都没被捕获，程序调用 `std::terminate()` 终止。

## 9.2　抛出任意类型

```cpp
try {
    throw 42;                 // 抛出 int
}
catch (int e) {
    cout << "int: " << e;     // int: 42
}

try {
    throw string("oops");
}
catch (const string& s) {
    cout << s;
}
```

**易错**：`throw "error";` 抛出的是 `const char*`，必须用 `catch (const char* s)` 捕获，`catch (string s)` 捕获不到。

## 9.3　catch 的匹配规则（必考）

1. 按 `catch` 子句的**书写顺序**依次检查，**第一个**匹配的被执行，其余的忽略。
2. 匹配时**几乎不做类型转换**：`throw 1;`（int）不能被 `catch (double)` 捕获。
3. 允许的转换只有：派生类到基类（public 继承）、非 const 到 const、数组/函数到指针。
4. `catch (...)` 捕获**所有类型**的异常，必须放在最后。

因为派生类异常能被基类的 catch 捕获，所以**派生类的 catch 必须写在基类的 catch 前面**，否则永远执行不到。

```cpp
try {
    throw out_of_range("index");        // out_of_range 派生自 logic_error，后者派生自 exception
}
catch (const out_of_range& e) { cout << "A"; }    // 先写派生类
catch (const logic_error& e)  { cout << "B"; }
catch (const exception& e)    { cout << "C"; }
catch (...)                   { cout << "D"; }    // 最后写 ...
// 输出：A
```

如果把 `catch (const exception& e)` 放在第一个，那么任何标准异常都会被它捕获，输出 C。

**为什么用引用捕获**：`catch (const exception& e)` 用引用捕获，可以避免拷贝，也能保持多态，`e.what()` 调用的是派生类的版本。如果按值捕获 `catch (exception e)`，会发生**切片**，丢失派生类的信息。

## 9.4　重新抛出

在 catch 块中写 `throw;`（不带表达式），把当前异常重新抛出，交给外层处理。

```cpp
void f() {
    try {
        throw runtime_error("bad");
    }
    catch (const exception& e) {
        cout << "f 处理一部分 ";
        throw;                          // 重新抛出原来的异常
    }
}

int main() {
    try { f(); }
    catch (const runtime_error& e) { cout << "main 捕获：" << e.what(); }
}
// 输出：f 处理一部分 main 捕获：bad
```

`throw;` 重新抛出的是**原来的异常对象**（类型仍是 runtime_error）；而 `throw e;` 会抛出 e 的副本，类型是 e 的静态类型 exception，发生切片。

## 9.5　标准异常类

头文件 `<stdexcept>` 和 `<exception>`。

```text
exception
├── logic_error          逻辑错误（程序本可以避免）
│   ├── invalid_argument   无效参数
│   ├── out_of_range       越界，如 vector::at
│   ├── length_error
│   └── domain_error
├── runtime_error        运行时错误
│   ├── overflow_error
│   ├── underflow_error
│   └── range_error
├── bad_alloc            new 失败
└── bad_cast             dynamic_cast 引用转换失败
```

- 所有标准异常都有虚函数 `const char* what() const`，返回错误描述。
- `vector` 的 `v.at(i)` 越界会抛出 `out_of_range`；`v[i]` 越界不检查。

**自定义异常类**：一般从 `exception` 或其派生类继承。

```cpp
class MyError : public runtime_error {
    int code;
public:
    MyError(const string& msg, int c) : runtime_error{msg}, code{c} { }
    int getCode() const { return code; }
};

try {
    throw MyError("file missing", 404);
}
catch (const MyError& e) {
    cout << e.what() << ' ' << e.getCode();   // file missing 404
}
```

## 9.6　栈展开与 RAII（必考理解）

异常抛出后，从 throw 点到 catch 点之间的每一层函数都会退出，这些函数中**已经构造的局部对象会被自动析构**，这叫**栈展开**。

```cpp
class R {
    string name;
public:
    R(const string& n) : name{n} { cout << "构造" << name << ' '; }
    ~R() { cout << "析构" << name << ' '; }
};

void g() {
    R b("B");
    throw 1;
    R c("C");       // 不会执行
}
void f() {
    R a("A");
    g();
}
int main() {
    try { f(); }
    catch (int) { cout << "捕获"; }
}
// 输出：构造A 构造B 析构B 析构A 捕获
```

注意：**析构在进入 catch 块之前完成**。

这就是 RAII 能保证资源安全的原因：资源交给局部对象管理，无论正常返回还是异常退出，析构函数都会释放资源。反过来，用裸指针 `new` 的资源在异常发生时会泄漏：

```cpp
void leak() {
    int* p = new int[100];
    mayThrow();          // 如果这里抛异常
    delete[] p;          // 这行不会执行 → 内存泄漏
}
void safe() {
    vector<int> v(100);  // 或 unique_ptr<int[]> p(new int[100]);
    mayThrow();          // 抛异常时 v 会被自动析构
}
```

**其他要点**

- **构造函数中抛出异常**：对象被认为没有构造成功，**不会调用它的析构函数**，但已经构造好的成员和基类部分会被析构。
- **析构函数不应该抛出异常**：如果在栈展开过程中析构函数又抛出异常，程序直接调用 `terminate()` 终止。C++11 中析构函数默认就是 `noexcept` 的。

## 9.7　noexcept（C++11）

```cpp
void f() noexcept;          // 承诺不抛出异常
void g() noexcept(false);   // 可能抛出（和不写一样）
```

- 如果标记了 `noexcept` 的函数仍然抛出异常，程序直接调用 `terminate()` 终止，不会被外层 catch 捕获。
- 移动构造函数、移动赋值、析构函数、swap 通常应标记 `noexcept`。
- C++98 的异常规格说明 `void f() throw(int);` 已在 C++11 中弃用。

## 9.8　本章小结

- `throw` 后当前函数立即退出，跳到第一个类型匹配的 catch；处理完不会回到抛出点。
- catch 匹配几乎不做类型转换（int 不匹配 double），但派生类能匹配基类，所以派生类的 catch 写在前面，`catch(...)` 写在最后。
- 用 `const&` 捕获，避免切片；`throw;` 重新抛出原异常。
- 栈展开时局部对象会被析构，析构发生在进入 catch 之前。
- 构造函数抛异常时不调用该对象的析构函数；析构函数不应抛异常。
