# 第 8 章　派生类与类层次 ★

继承和多态是期末考试分值最高的部分，读程序题和编程大题都会考。与 Java 最大的不同是：**C++ 的成员函数默认不是虚函数，不加 `virtual` 就不会发生多态**。

## 8.1　继承的语法

```cpp
class Person {                       // 基类（父类）
protected:
    string name;
public:
    Person(const string& n) : name{n} { }
    void show() const { cout << "Name: " << name << endl; }
};

class Student : public Person {      // 派生类（子类），公有继承
    int score;
public:
    Student(const string& n, int s) : Person{n}, score{s} { }  // 在初始化列表中调用基类构造函数
    void study() const { cout << name << " is studying\n"; }   // 可以访问 protected 的 name
};

Student s("Tom", 90);
s.show();     // 继承来的函数
s.study();
```

- 语法：`class 派生类 : 继承方式 基类`。
- 继承方式省略时：`class` 默认 **private** 继承，`struct` 默认 public 继承。**几乎总是应该写 public。**
- C++ 没有 Java 的 `super` 关键字，用 `基类名::成员` 访问基类成员。
- C++ 支持多重继承（Java 只能单继承）。

## 8.2　三种继承方式（必考）

继承方式决定了基类成员在**派生类中**的访问权限。

| 基类中的成员 | public 继承后 | protected 继承后 | private 继承后 |
| --- | --- | --- | --- |
| public 成员 | public | protected | private |
| protected 成员 | protected | protected | private |
| private 成员 | 不可访问 | 不可访问 | 不可访问 |

**记法**：取“基类中的权限”与“继承方式”两者中**更严格**的那个；基类的 private 成员在派生类中**永远不可直接访问**（但它仍然存在于派生类对象中，占用空间）。

```cpp
class Base {
public:    int a;
protected: int b;
private:   int c;
};

class D1 : public Base {
    void f() {
        a = 1;    // 可以
        b = 2;    // 可以
        // c = 3; 错误：基类私有成员不可访问
    }
};

class D2 : private Base {
    void f() { a = 1; b = 2; }   // 在 D2 内部可以访问 a、b（它们变成了 D2 的 private）
};

int main() {
    D1 d1;
    d1.a = 1;     // 可以：公有继承后 a 仍是 public
    // d1.b = 2;  错误：b 是 protected
    D2 d2;
    // d2.a = 1;  错误：私有继承后 a 变成 private
}
```

**含义上的区别**：public 继承表示“**是一个**”（is-a）关系，学生是一个人；private 继承表示“**用……实现**”，通常可以用组合代替。

## 8.3　派生类的构造与析构（必考）

- **构造函数不会被继承**（C++11 可以用 `using Base::Base;` 显式继承构造函数，了解即可）。
- 派生类构造函数必须在初始化列表中调用基类构造函数；如果不写，就自动调用基类的**默认构造函数**，基类没有默认构造函数时编译报错。

**构造顺序**：

1. 基类的构造函数（多个基类时按**继承列表中的声明顺序**）
2. 派生类成员对象的构造函数（按成员**声明顺序**）
3. 派生类自己的构造函数体

**析构顺序与构造顺序完全相反。**

```cpp
class M {
public:
    M()  { cout << "M "; }
    ~M() { cout << "~M "; }
};
class B {
public:
    B(int x) { cout << "B" << x << ' '; }
    ~B() { cout << "~B "; }
};
class D : public B {
    M m;
public:
    D() : B(1) { cout << "D "; }
    ~D() { cout << "~D "; }
};

int main() { D d; }
// 输出：B1 M D ~D ~M ~B
```

口诀：**构造：先祖宗，再客人，后自己；析构：先自己，再客人，后祖宗。**（祖宗 = 基类，客人 = 成员对象）

## 8.4　同名成员的隐藏

派生类中定义了与基类同名的成员，基类的同名成员就被**隐藏**。

```cpp
class Base {
public:
    void f()      { cout << "Base::f()\n"; }
    void f(int)   { cout << "Base::f(int)\n"; }
};
class Derived : public Base {
public:
    void f()      { cout << "Derived::f()\n"; }
};

Derived d;
d.f();           // Derived::f()
// d.f(1);       错误！基类的所有 f 都被隐藏了，包括 f(int)
d.Base::f(1);    // 可以：用作用域限定访问基类版本
```

**易错（必考）**：只要名字相同就会隐藏基类的**所有**同名函数，与参数是否相同无关。如果想保留基类的重载版本，可以在派生类中写 `using Base::f;`。

## 8.5　赋值兼容规则（向上转换）

在 public 继承下，**派生类对象可以当作基类对象使用**：

```cpp
Student s("Tom", 90);
Person p = s;       // 1. 派生类对象赋给基类对象：发生“切片”，只复制基类部分
Person& r = s;      // 2. 基类引用绑定派生类对象
Person* ptr = &s;   // 3. 基类指针指向派生类对象
```

- 通过基类的指针或引用，**只能访问基类中定义的成员**：`ptr->study();` 是错误的。
- 反过来不行：基类对象不能赋给派生类对象，基类指针不能直接赋给派生类指针（需要强制转换）。
- **对象切片**：`Person p = s;` 只复制了 s 中 Person 的部分，p 就是一个普通的 Person 对象，与 s 再无关系，也不会有多态行为。

## 8.6　虚函数与动态多态（必考）

**问题**：通过基类指针调用函数，调用的是谁的版本？

```cpp
class Shape {
public:
    void draw() const { cout << "Shape\n"; }      // 非虚函数
};
class Circle : public Shape {
public:
    void draw() const { cout << "Circle\n"; }
};

Shape* p = new Circle;
p->draw();    // 输出：Shape
```

没有 `virtual` 时，调用哪个函数由**指针的声明类型**决定（编译时确定，**静态绑定**）。

加上 `virtual`：

```cpp
class Shape {
public:
    virtual void draw() const { cout << "Shape\n"; }   // 虚函数
    virtual ~Shape() { }
};
class Circle : public Shape {
public:
    void draw() const override { cout << "Circle\n"; }  // 覆盖
};

Shape* p = new Circle;
p->draw();    // 输出：Circle
```

有 `virtual` 时，调用哪个函数由**指针实际指向的对象类型**决定（运行时确定，**动态绑定**）。这就是**多态**。

**发生动态多态的三个条件（必考）**

1. 基类中的函数声明为 `virtual`。
2. 派生类**覆盖**了这个函数（函数名、参数列表、const 属性都完全相同，返回类型相同或协变）。
3. 通过**基类的指针或引用**调用。

三者缺一不可。特别注意：**通过对象直接调用不发生多态**。

```cpp
Circle c;
Shape s = c;     // 切片
s.draw();        // Shape：通过对象调用，静态绑定
Shape& r = c;
r.draw();        // Circle：通过引用调用，动态绑定
```

**虚函数的其他规则**

- 基类中声明为 virtual 后，派生类中的覆盖函数**自动是虚函数**，`virtual` 可写可不写。
- **构造函数不能是虚函数**；析构函数可以而且常常应该是。
- **静态成员函数不能是虚函数**；友元函数不是成员，也不能是虚函数。
- **在构造函数和析构函数中调用虚函数，不会发生多态**，调用的是当前类自己的版本（因为此时派生类部分还没构造好或已经析构了）。
- 在成员函数中调用虚函数（通过隐含的 this），会发生多态。

```cpp
class A {
public:
    A() { hello(); }                       // 构造中调用：不多态
    virtual void hello() { cout << "A "; }
    void call() { hello(); }               // this->hello()：多态
};
class B : public A {
public:
    B() { hello(); }
    void hello() override { cout << "B "; }
};

int main() {
    B b;        // 输出：A B
    b.call();   // 输出：B
    A* p = &b;
    p->call();  // 输出：B
}
```

## 8.7　override 与 final（C++11）

- `override`：写在派生类函数后面，表示“我打算覆盖基类的虚函数”。如果基类没有匹配的虚函数（比如参数写错了、漏了 const），**编译器报错**，避免低级错误。
- `final`：写在虚函数后，表示派生类**不能再覆盖**它；写在类名后，表示这个类**不能被继承**。

```cpp
class Base {
public:
    virtual void f(int) const;
    virtual void g();
};
class D : public Base {
public:
    void f(int) const override;   // 正确
    // void f(int) override;      错误：少了 const，没有覆盖任何函数
    // void f(double) const override;  错误：参数不同
    void g() final;               // 后续派生类不能再覆盖 g
};
class E final : public D { };     // E 不能被继承
```

## 8.8　重载、覆盖、隐藏的区别（必考）

| 比较项 | 重载 overload | 覆盖 override | 隐藏 hide |
| --- | --- | --- | --- |
| 作用域 | 同一个类（同一作用域） | 基类与派生类 | 基类与派生类 |
| 函数名 | 相同 | 相同 | 相同 |
| 参数列表 | **必须不同** | **必须相同** | 可以相同，也可以不同 |
| virtual | 无关 | 基类函数**必须是 virtual** | 参数相同时基类函数**不是 virtual**；参数不同时无论是否 virtual |
| 绑定时机 | 编译时 | 运行时（通过指针/引用） | 编译时 |

例题：

```cpp
class Base {
public:
    virtual void f(int x) { cout << "Base::f(int)\n"; }
    void g() { cout << "Base::g\n"; }
    virtual void h(double) { cout << "Base::h\n"; }
};
class Derived : public Base {
public:
    void f(int x) override { cout << "Derived::f(int)\n"; }   // 覆盖
    void g() { cout << "Derived::g\n"; }                      // 隐藏（g 非虚）
    void h(int) { cout << "Derived::h\n"; }                   // 隐藏（参数不同）
};

int main() {
    Derived d;
    Base* pb = &d;
    pb->f(1);     // Derived::f(int)：覆盖 + 基类指针 → 多态
    pb->g();      // Base::g：非虚，按指针类型
    pb->h(1.5);   // Base::h：Derived::h(int) 没有覆盖 h(double)
    d.g();        // Derived::g
    d.h(1.5);     // Derived::h：基类的 h 被隐藏，1.5 被转换为 int
}
```

## 8.9　虚析构函数（必考）

```cpp
class Base {
public:
    ~Base() { cout << "~Base "; }          // 非虚析构
};
class Derived : public Base {
    int* data = new int[100];
public:
    ~Derived() { delete[] data; cout << "~Derived "; }
};

Base* p = new Derived;
delete p;     // 只输出 ~Base，Derived 的析构函数没有被调用 → 内存泄漏
```

通过基类指针删除派生类对象时，如果基类的析构函数**不是虚函数**，只会调用基类的析构函数（严格地说是**未定义行为**）。

把基类析构函数声明为虚函数后：

```cpp
class Base {
public:
    virtual ~Base() { cout << "~Base "; }
};
// delete p; 输出：~Derived ~Base
```

**规则：只要一个类打算作为基类被多态使用（有虚函数），它的析构函数就应该是虚函数。**

## 8.10　纯虚函数与抽象类

```cpp
class Shape {
public:
    virtual double area() const = 0;     // 纯虚函数：= 0
    virtual void draw() const = 0;
    virtual ~Shape() { }
};
```

- 含有至少一个纯虚函数的类是**抽象类**。
- **抽象类不能创建对象**：`Shape s;` 和 `new Shape` 都是错误的。
- 但可以定义抽象类的**指针和引用**：`Shape* p;`、`Shape& r = c;`。
- 派生类必须覆盖**所有**纯虚函数才能成为具体类；只要有一个没覆盖，派生类仍是抽象类。
- 抽象类相当于 Java 的 `abstract class` 或 `interface`。
- 纯虚函数也可以有函数体（在类外定义），了解即可。

## 8.11　多态的典型应用（编程大题模板）

```cpp
#include <iostream>
#include <vector>
using namespace std;

const double PI = 3.14159;

class Shape {                                   // 抽象基类
public:
    virtual double area() const = 0;
    virtual double perimeter() const = 0;
    virtual void print() const {
        cout << "area = " << area() << ", perimeter = " << perimeter() << endl;
    }
    virtual ~Shape() { }
};

class Circle : public Shape {
    double r;
public:
    explicit Circle(double radius) : r{radius} { }
    double area() const override { return PI * r * r; }
    double perimeter() const override { return 2 * PI * r; }
};

class Rectangle : public Shape {
    double w, h;
public:
    Rectangle(double width, double height) : w{width}, h{height} { }
    double area() const override { return w * h; }
    double perimeter() const override { return 2 * (w + h); }
};

class Square : public Rectangle {
public:
    explicit Square(double a) : Rectangle(a, a) { }
};

double totalArea(const vector<Shape*>& shapes) {
    double sum = 0;
    for (const Shape* s : shapes)
        sum += s->area();                       // 多态调用
    return sum;
}

int main() {
    vector<Shape*> shapes;
    shapes.push_back(new Circle(1));
    shapes.push_back(new Rectangle(2, 3));
    shapes.push_back(new Square(2));

    for (const Shape* s : shapes) s->print();
    cout << "total = " << totalArea(shapes) << endl;

    for (Shape* s : shapes) delete s;           // 虚析构保证正确释放
}
```

**写这类题的检查清单**

1. 基类中的接口函数加 `virtual`，没有合理默认实现的写成纯虚函数 `= 0`。
2. 基类加 `virtual ~Base() { }`。
3. 派生类用 `public` 继承，构造函数在初始化列表中调用基类构造函数。
4. 派生类覆盖函数的签名（参数、const）与基类完全一致，加上 `override`。
5. 用基类指针或引用（数组、vector）统一处理，`new` 出来的对象最后 `delete`。

## 8.12　多重继承与虚基类

**多重继承**：一个类有多个直接基类。

```cpp
class A { public: A() { cout << "A "; } void f() { } };
class B { public: B() { cout << "B "; } void f() { } };
class C : public B, public A {           // 按此处的顺序构造：B 再 A
public:
    C() : A(), B() { cout << "C "; }      // 初始化列表的顺序无关
};
C c;          // 输出：B A C
// c.f();     错误：二义性，不知道是 A::f 还是 B::f
c.A::f();     // 可以：用作用域限定消除二义性
```

**菱形继承问题**：

```text
      Animal
      /    \
   Horse   Bird
      \    /
      Pegasus
```

如果 Horse 和 Bird 都普通地继承 Animal，Pegasus 对象中就会有**两份** Animal 的成员，访问时产生二义性，还浪费空间。

**虚继承**解决这个问题：

```cpp
class Animal {
public:
    int age;
    Animal(int a = 0) : age{a} { cout << "Animal "; }
};
class Horse : virtual public Animal {          // 虚继承
public: Horse() { cout << "Horse "; }
};
class Bird : virtual public Animal {
public: Bird() { cout << "Bird "; }
};
class Pegasus : public Horse, public Bird {
public:
    Pegasus() : Animal(5) { cout << "Pegasus "; }  // 虚基类由最终派生类直接初始化
};

Pegasus p;      // 输出：Animal Horse Bird Pegasus（Animal 只构造一次）
p.age = 3;      // 可以：只有一份 age，没有二义性
```

**虚基类的要点**

- 用 `virtual public 基类` 声明，被虚继承的类叫**虚基类**。
- 最终派生类中只保留一份虚基类子对象。
- **虚基类由最终派生类（最底层的类）负责初始化**，中间类对虚基类构造函数的调用会被忽略。
- **虚基类最先构造**，在所有非虚基类之前。

## 8.13　四种类型转换与 dynamic_cast

| 转换 | 用途 | 检查时机 |
| --- | --- | --- |
| `static_cast` | 相关类型之间的常规转换；基类指针转派生类指针（**不检查**是否真的是派生类对象） | 编译时 |
| `dynamic_cast` | 多态类型的安全向下转换 | **运行时** |
| `const_cast` | 去除 const | 编译时 |
| `reinterpret_cast` | 无关类型之间的低级转换 | 不检查 |

**dynamic_cast**：要求基类至少有一个虚函数（即**多态类型**）。

```cpp
Shape* s = new Circle(1);

Circle* c = dynamic_cast<Circle*>(s);        // 成功：s 确实指向 Circle
Rectangle* r = dynamic_cast<Rectangle*>(s);  // 失败：返回 nullptr
if (r) { /* ... */ }                         // 使用前要检查

Shape& ref = *s;
Rectangle& rr = dynamic_cast<Rectangle&>(ref);  // 引用转换失败时抛出 std::bad_cast 异常
```

- 指针转换失败返回 `nullptr`；引用转换失败抛出 `bad_cast` 异常（因为没有“空引用”）。
- `typeid(*s).name()` 可以获取对象的实际类型（需要 `#include <typeinfo>`）。

## 8.14　虚函数的实现原理（了解）

- 每个含有虚函数的类有一张**虚函数表（vtbl）**，表中存放该类各虚函数的地址。
- 每个对象中有一个隐藏的**虚表指针（vptr）**，指向所属类的虚函数表。所以含虚函数的类，`sizeof` 会多出一个指针的大小。
- 调用虚函数时，通过对象的 vptr 找到虚函数表，再找到函数地址，因此可以在运行时决定调用哪个版本。

## 8.15　本章小结

- public 继承下，基类 public/protected 保持不变；基类 private 在派生类中永远不可访问。
- 构造顺序：虚基类 → 基类（按继承声明顺序）→ 成员对象（按声明顺序）→ 自己；析构相反。
- 同名函数会隐藏基类的所有同名重载。
- 多态三条件：virtual、覆盖（签名完全一致）、通过基类指针或引用调用。
- 构造函数中调用虚函数不发生多态；构造函数不能是虚函数；有虚函数的基类要有虚析构函数。
- 含纯虚函数的是抽象类，不能实例化，但可以定义指针和引用。
- 虚继承让菱形继承中只保留一份基类，由最底层的类初始化。
- `dynamic_cast` 失败：指针返回 nullptr，引用抛 `bad_cast`。
