# 编写计划与各章要点

**读者**：学过一点 Java 和 C、但都不熟练，这学期几乎没学 C++，一周后参加大学 C++ 期末笔试的学生。

**教材**：Stroustrup《C++程序设计语言》（第 4 版，C++11）。

**范围**：只覆盖笔试；上机考试不在本书范围内。总篇幅控制在 10 万字以内。

| 章 | 文件 | 要点 |
|---|---|---|
| 0 | `00-guide.md` | 重要程度表、笔试题型、读程序题的答题方法、本书约定 |
| 1 | `01-basics.md` | 程序结构、基本类型、`{}` 初始化与窄化、`auto`/`decltype`、`const`/`constexpr`、运算符、类型转换、范围 for |
| 2 | `02-pointers-arrays-references.md` | 指针、`nullptr`、数组与指针、C 字符串、`const` 与指针、引用、`new`/`delete`、`string`、右值引用入门 |
| 3 | `03-structs-enums-namespaces.md` | `struct`、`enum` 与 `enum class`、名字空间、头文件与源文件、声明与定义 |
| 4 | `04-functions.md` | 参数传递、重载与重载解析、默认参数、`inline`、`static` 局部变量、递归、函数指针、lambda |
| 5 | `05-classes.md` | 访问控制、构造函数、初始化列表、`explicit`、`const` 成员函数、`this`、`static` 成员、友元 |
| 6 | `06-construction-copy-move.md` | 析构、RAII、构造/析构顺序、拷贝构造、深浅拷贝、移动语义、`=default`/`=delete`、三/五/零法则 |
| 7 | `07-operator-overloading.md` | 规则与限制、成员与友元形式、复数类、`<<`/`>>`、前后置 `++`、`=`、`[]`、`()`、类型转换、字符串类 |
| 8 | `08-inheritance-polymorphism.md` | 继承方式、构造顺序、隐藏、赋值兼容、虚函数、`override`/`final`、重载覆盖隐藏、虚析构、抽象类、虚继承、`dynamic_cast` |
| 9 | `09-exceptions.md` | `try`/`throw`/`catch`、匹配规则、重新抛出、标准异常、栈展开、`noexcept` |
| 10 | `10-templates.md` | 函数模板、推导、与普通函数的重载、类模板、类外定义成员、特例化 |
| 11 | `11-standard-library.md` | `vector`、`list`、`map`、`set`、迭代器、算法、智能指针、I/O 流与文件 |
| 12 | `12-quick-reference.md` | 易错点汇总、读程序题步骤、综合练习、三个编程大题模板、简答题问答 |
