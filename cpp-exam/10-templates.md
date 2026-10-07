# 第 10 章　模板 ☆

模板让一份代码适用于多种类型，作用类似 Java 的泛型，但实现机制不同：C++ 模板在**编译时为每种用到的类型生成一份独立的代码**（实例化），而且可以用于 int、double 等内置类型。

## 10.1　函数模板

```cpp
template <typename T>              // 也可以写 template <class T>，两者等价
T myMax(T a, T b) {
    return a > b ? a : b;
}

int main() {
    cout << myMax(3, 7);           // T 推导为 int，输出 7
    cout << myMax(2.5, 1.5);       // T 推导为 double，输出 2.5
    cout << myMax<string>("apple", "pear");  // 显式指定 T，输出 pear
    // myMax(3, 2.5);              错误：T 推导出 int 和 double 两种，矛盾
    cout << myMax<double>(3, 2.5); // 可以：显式指定后 3 转换为 double
}
```

**要点**

- `template <typename T>` 声明模板参数 T，T 是一个类型占位符。
- 调用时编译器根据实参**自动推导** T，这叫**模板实参推导**。
- **推导时不做隐式类型转换**：`myMax(3, 2.5)` 中两个参数推导出的 T 不一致，报错。
- 函数模板本身不是函数，用具体类型调用时才**实例化**出一个真正的函数。
- 模板中对 T 的使用要求 T 支持相应的操作：`myMax` 要求 T 支持 `>`。如果用一个没有重载 `>` 的类调用，编译报错。
- 注意 `myMax("apple", "pear")` 不指定类型时，T 推导为 `const char*`，比较的是**地址**而不是字符串内容。

**多个模板参数**

```cpp
template <typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {   // 返回类型由 a+b 决定
    return a + b;
}
cout << add(1, 2.5);    // 3.5
```

**非类型模板参数**：模板参数也可以是一个常量值。

```cpp
template <typename T, int N>
T sum(const T (&arr)[N]) {        // N 自动推导为数组长度
    T s {};
    for (int i = 0; i < N; ++i) s += arr[i];
    return s;
}
int a[] {1, 2, 3, 4};
cout << sum(a);    // 10
```

## 10.2　函数模板与普通函数的重载

```cpp
template <typename T>
void show(T x) { cout << "模板 "; }

void show(int x) { cout << "普通 "; }

show(1);        // 普通：精确匹配时优先选普通函数
show(1.5);      // 模板：模板生成 show<double> 精确匹配
show<>(1);      // 模板：<> 强制使用模板
show('a');      // 模板：模板生成 show<char> 精确匹配，优于普通函数需要的 char→int 提升
```

**规则**：普通函数和模板都能**同样好地**匹配时，**优先选择普通函数**；模板能产生更好的匹配时，选模板。

## 10.3　类模板

```cpp
template <typename T>
class Stack {
    T* data;
    int top;
    int cap;
public:
    explicit Stack(int n = 10) : data{new T[n]}, top{0}, cap{n} { }
    ~Stack() { delete[] data; }
    Stack(const Stack&) = delete;              // 简化起见禁止拷贝
    Stack& operator=(const Stack&) = delete;

    void push(const T& x);
    T pop();
    bool empty() const { return top == 0; }
    int size() const { return top; }
};

// 类外定义成员函数：每个函数前都要写 template，类名后要写 <T>
template <typename T>
void Stack<T>::push(const T& x) {
    if (top == cap) throw overflow_error("stack full");
    data[top++] = x;
}

template <typename T>
T Stack<T>::pop() {
    if (top == 0) throw underflow_error("stack empty");
    return data[--top];
}

int main() {
    Stack<int> s1;                 // 必须显式指定类型（C++11 中类模板不能自动推导）
    s1.push(1); s1.push(2); s1.push(3);
    while (!s1.empty()) cout << s1.pop() << ' ';   // 3 2 1

    Stack<string> s2(5);
    s2.push("hello");
    cout << s2.pop();              // hello
}
```

**易错（必考）**

1. 类外定义成员函数时，格式为：

    ```text
    template <typename T>
    返回类型 类名<T>::函数名(参数) { ... }
    ```

    两处都不能漏：前面的 `template <typename T>` 和类名后的 `<T>`。

2. 使用类模板时**必须给出模板实参**：`Stack<int> s;`，不能写 `Stack s;`。
3. `Stack` 是模板名，`Stack<int>` 才是一个类型。`Stack<int>` 和 `Stack<double>` 是两个**完全不同、互不相关**的类。
4. 模板的定义（包括成员函数的定义）通常**全部写在头文件中**。因为编译器在实例化时需要看到完整的定义，如果把成员函数定义放在 .cpp 文件里，链接时会报“未定义的引用”。

**类模板的友元与运算符**：在类模板内直接定义友元函数最简单。

```cpp
template <typename T>
class Pair {
    T first, second;
public:
    Pair(const T& a, const T& b) : first{a}, second{b} { }
    T getMax() const { return first > second ? first : second; }
    friend ostream& operator<<(ostream& os, const Pair& p) {   // 类内定义
        return os << "(" << p.first << ", " << p.second << ")";
    }
};
Pair<int> p(3, 8);
cout << p << ' ' << p.getMax();   // (3, 8) 8
```

**默认模板参数**

```cpp
template <typename T = int, int N = 10>
class Array { T data[N]; };
Array<> a1;              // Array<int, 10>
Array<double, 5> a2;
```

## 10.4　模板特例化（了解）

某个特定类型需要特殊处理时，可以为它单独写一个版本。

```cpp
template <typename T>
bool isEqual(T a, T b) { return a == b; }

template <>                                     // 全特例化
bool isEqual<const char*>(const char* a, const char* b) {
    return strcmp(a, b) == 0;                   // 比较内容而不是地址
}
```

类模板也可以特例化，例如标准库中 `vector<bool>` 就是一个特例化版本。

## 10.5　本章小结

- `template <typename T>` 与 `template <class T>` 等价。
- 函数模板会自动推导类型，推导时不做隐式转换；推导冲突时需显式指定 `f<double>(...)`。
- 普通函数与模板匹配程度相同时，优先普通函数。
- 类模板使用时必须写 `Stack<int>`；类外定义成员要写 `template <typename T>` 和 `Stack<T>::`。
- 模板的定义通常放在头文件中。
