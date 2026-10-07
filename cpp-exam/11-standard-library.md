# 第 11 章　标准库 ☆

笔试对标准库的要求一般是：会用 `vector`、`map` 等常用容器，理解迭代器，会调用 `sort`、`find` 等算法，了解智能指针，能写简单的文件读写。

## 11.1　STL 的组成

- **容器**：存放数据，如 `vector`、`list`、`map`、`set`。
- **迭代器**：访问容器元素的统一方式，用法像指针。
- **算法**：通用的操作，如排序、查找、计数，通过迭代器作用于容器。

三者的关系：算法不直接操作容器，而是通过迭代器访问元素，所以同一个算法可以用于不同容器。

## 11.2　vector

`vector` 是**动态数组**（`#include <vector>`），元素连续存储，支持随机访问，尾部插入删除快。相当于 Java 的 `ArrayList`。

```cpp
vector<int> v1;                  // 空
vector<int> v2(5);               // 5 个元素，都是 0
vector<int> v3(5, 7);            // 5 个元素，都是 7
vector<int> v4 {5, 7};           // 2 个元素：5 和 7（注意与 v3 的区别！）
vector<int> v5 = v4;             // 拷贝

v1.push_back(10);                // 尾部添加
v1.push_back(20);
v1.push_back(30);
cout << v1.size();               // 3
cout << v1[0];                   // 10，不检查越界
cout << v1.at(1);                // 20，越界时抛 out_of_range
cout << v1.front() << v1.back(); // 10 30
v1.pop_back();                   // 删除最后一个：10 20
v1.insert(v1.begin(), 5);        // 在开头插入：5 10 20
v1.erase(v1.begin() + 1);        // 删除下标 1：5 20
bool e = v1.empty();             // false
v1.clear();                      // 清空，size 变为 0
```

**易错（必考）**：`vector<int> v(5, 7)` 是 5 个 7；`vector<int> v {5, 7}` 是两个元素 5 和 7。花括号优先匹配初始化列表构造函数。

**size 与 capacity**：`size()` 是元素个数，`capacity()` 是已分配的空间能容纳的元素个数。空间不够时 vector 会重新分配一块更大的内存，并把元素搬过去，这会导致之前获取的指针、引用和迭代器**失效**。

**遍历的三种方式**

```cpp
vector<int> v {1, 2, 3};
for (size_t i = 0; i < v.size(); ++i) cout << v[i];         // 下标
for (auto it = v.begin(); it != v.end(); ++it) cout << *it;  // 迭代器
for (int x : v) cout << x;                                   // 范围 for
```

**存放对象**

```cpp
struct Student { string name; int score; };
vector<Student> stu {{"Tom", 90}, {"Amy", 85}};
stu.push_back({"Bob", 78});
for (const auto& s : stu) cout << s.name << ' ' << s.score << endl;
```

## 11.3　其他常用容器

| 容器 | 头文件 | 特点 | 类似 Java |
| --- | --- | --- | --- |
| `vector` | `<vector>` | 动态数组，随机访问快，尾部增删快 | ArrayList |
| `list` | `<list>` | 双向链表，任意位置增删快，不支持下标访问 | LinkedList |
| `deque` | `<deque>` | 双端队列，两端增删快 | ArrayDeque |
| `map` | `<map>` | 键值对，按键**有序**存储（红黑树），键唯一 | TreeMap |
| `set` | `<set>` | 有序集合，元素唯一 | TreeSet |
| `unordered_map` | `<unordered_map>` | 哈希表，无序，查找平均 O(1) | HashMap |
| `stack` / `queue` | `<stack>` / `<queue>` | 容器适配器，栈和队列 | Stack / Queue |

**list**

```cpp
list<int> lst {3, 1, 2};
lst.push_front(0);           // 0 3 1 2
lst.push_back(9);            // 0 3 1 2 9
lst.sort();                  // list 有自己的 sort 成员函数：0 1 2 3 9
// lst[1];                   错误：list 不支持下标
```

**map**

```cpp
map<string, int> score;
score["Tom"] = 90;               // 插入或修改
score["Amy"] = 85;
score.insert({"Bob", 78});       // 插入
cout << score["Tom"];            // 90

for (const auto& p : score)      // 按键的字典序遍历：Amy Bob Tom
    cout << p.first << ": " << p.second << endl;

if (score.find("Jack") == score.end()) cout << "没找到";   // 查找
if (score.count("Amy")) cout << "有 Amy";                  // count 返回 0 或 1
score.erase("Bob");              // 删除
```

**易错**：用 `[]` 访问一个**不存在的键**时，map 会**自动插入**这个键，值为默认值（int 为 0）。只想查询时应使用 `find` 或 `count`。

**set**

```cpp
set<int> s {5, 1, 3, 1, 5};
for (int x : s) cout << x << ' ';   // 1 3 5（自动去重并排序）
s.insert(2);
cout << s.count(3);                 // 1
```

**stack 与 queue**

```cpp
stack<int> st;
st.push(1); st.push(2);
cout << st.top();     // 2
st.pop();             // pop 不返回值！

queue<int> q;
q.push(1); q.push(2);
cout << q.front();    // 1
q.pop();
```

## 11.4　迭代器

迭代器是一种“泛化的指针”，用于遍历容器。

- `c.begin()`：指向第一个元素。
- `c.end()`：指向**最后一个元素的下一个位置**（尾后位置），不能解引用。
- `*it`：访问元素；`++it`：移到下一个元素；`it->member`：访问元素的成员。
- 区间是**左闭右开**的 `[begin, end)`。空容器的 `begin() == end()`。

```cpp
vector<int> v {10, 20, 30};
vector<int>::iterator it = v.begin();   // 或 auto it = v.begin();
cout << *it;          // 10
++it;
cout << *it;          // 20
*it = 25;             // 修改元素
cout << *(v.end() - 1);   // 30，vector 的迭代器支持 +、-（随机访问迭代器）

vector<int>::const_iterator cit = v.cbegin();   // 只读迭代器
// *cit = 1;          错误

for (auto rit = v.rbegin(); rit != v.rend(); ++rit)   // 反向遍历
    cout << *rit;     // 30 25 10
```

**迭代器的种类**：vector、deque 是随机访问迭代器，支持 `it + n`、`it1 < it2`；list、map、set 是双向迭代器，只支持 `++` 和 `--`。

**易错：在遍历中删除元素**。`erase` 后被删元素的迭代器失效，要使用 erase 的返回值（指向被删元素的下一个）：

```cpp
for (auto it = v.begin(); it != v.end(); ) {
    if (*it % 2 == 0) it = v.erase(it);   // 正确
    else ++it;
}
```

## 11.5　常用算法

头文件 `<algorithm>`，数值算法 `accumulate` 在 `<numeric>`。

```cpp
vector<int> v {5, 3, 8, 1, 9, 3};

sort(v.begin(), v.end());                       // 升序：1 3 3 5 8 9
sort(v.begin(), v.end(), greater<int>());       // 降序：9 8 5 3 3 1
sort(v.begin(), v.end(), [](int a, int b) { return a > b; });  // 用 lambda 降序

auto it = find(v.begin(), v.end(), 8);          // 查找，返回迭代器
if (it != v.end()) cout << "找到，下标 " << it - v.begin();

int c = count(v.begin(), v.end(), 3);           // 统计等于 3 的个数：2
int n = count_if(v.begin(), v.end(), [](int x) { return x > 4; });   // 大于 4 的个数：3
auto p = find_if(v.begin(), v.end(), [](int x) { return x < 2; });  // 第一个小于 2 的

int s = accumulate(v.begin(), v.end(), 0);      // 求和：29
auto mx = max_element(v.begin(), v.end());      // 最大值的迭代器
cout << *mx;                                    // 9
reverse(v.begin(), v.end());                    // 反转

for_each(v.begin(), v.end(), [](int x) { cout << x << ' '; });

int arr[] {4, 2, 6};
sort(arr, arr + 3);                             // 普通数组也可以：指针就是迭代器
```

**对自定义类型排序**：重载 `<` 或传入比较函数。

```cpp
struct Student {
    string name;
    int score;
    bool operator<(const Student& o) const { return score < o.score; }
};
vector<Student> stu {{"Tom", 90}, {"Amy", 85}, {"Bob", 95}};
sort(stu.begin(), stu.end());     // 按 score 升序：Amy Tom Bob
sort(stu.begin(), stu.end(), [](const Student& a, const Student& b) {
    return a.name < b.name;       // 按名字排序
});
```

**易错**：`sort` 需要随机访问迭代器，不能用于 `list`，list 要用自己的 `lst.sort()`。

## 11.6　智能指针（C++11）

智能指针是用 RAII 管理动态内存的类模板（`#include <memory>`），离开作用域时自动 `delete`，避免内存泄漏。

**unique_ptr：独占所有权**

```cpp
unique_ptr<int> p1 {new int(5)};
auto p2 = make_unique<int>(10);        // C++14 的写法，更推荐
cout << *p1;                           // 5

// unique_ptr<int> p3 = p1;            错误：不能拷贝
unique_ptr<int> p3 = std::move(p1);    // 可以移动：所有权转给 p3，p1 变为空
if (!p1) cout << "p1 为空";

unique_ptr<Shape> s {new Circle(1)};
s->area();                             // 用法和普通指针一样，支持多态
// p1、p2、p3、s 离开作用域时自动 delete 所指对象
```

**shared_ptr：共享所有权**

```cpp
shared_ptr<int> a = make_shared<int>(42);
cout << a.use_count();     // 1
{
    shared_ptr<int> b = a; // 可以拷贝，两者指向同一对象
    cout << a.use_count(); // 2
}                          // b 销毁，计数减 1
cout << a.use_count();     // 1
// 计数变为 0 时，对象被自动 delete
```

| 比较项 | `unique_ptr` | `shared_ptr` |
| --- | --- | --- |
| 所有权 | 独占，同一时刻只有一个指针拥有对象 | 共享，多个指针共同拥有 |
| 拷贝 | 不能拷贝，只能移动 | 可以拷贝 |
| 何时释放对象 | unique_ptr 销毁时 | 最后一个 shared_ptr 销毁时（引用计数为 0） |
| 开销 | 与裸指针相同 | 需要维护引用计数 |

`weak_ptr` 用于打破 `shared_ptr` 的循环引用，不增加引用计数，了解即可。

## 11.7　I/O 流与文件读写

**流类的层次**：`istream`（输入）、`ostream`（输出）、`iostream`；文件流 `ifstream`、`ofstream`、`fstream`（`#include <fstream>`）；字符串流 `istringstream`、`ostringstream`（`#include <sstream>`）。

**格式控制**（`#include <iomanip>`）

```cpp
double pi = 3.14159265;
cout << fixed << setprecision(2) << pi;     // 3.14（fixed 下表示小数点后 2 位）
cout << setw(8) << 42;                      // "      42"，宽度 8，右对齐；setw 只对下一项有效
cout << setw(8) << left << 42;              // "42      "
cout << right << setfill('0') << setw(5) << 42;   // "00042"（先改回右对齐）
cout << hex << 255;                         // ff
cout << boolalpha << true;                  // true
```

**写文件**

```cpp
#include <fstream>
ofstream fout("data.txt");          // 打开文件（不存在则创建，存在则清空）
if (!fout) { cerr << "打开失败"; return 1; }
fout << "Tom " << 90 << endl;
fout << "Amy " << 85 << endl;
fout.close();                       // 也可以不写，fout 析构时自动关闭

ofstream fapp("data.txt", ios::app);   // 追加模式
```

**读文件**

```cpp
ifstream fin("data.txt");
if (!fin) { cerr << "打开失败"; return 1; }
string name;
int score;
while (fin >> name >> score) {      // 读取成功时继续循环
    cout << name << ": " << score << endl;
}

ifstream fin2("data.txt");
string line;
while (getline(fin2, line)) {       // 按行读取
    cout << line << endl;
}
```

**打开模式**：`ios::in`（读）、`ios::out`（写）、`ios::app`（追加）、`ios::binary`（二进制）、`ios::trunc`（清空），可以用 `|` 组合。

**易错**：用 `while (!fin.eof())` 控制循环容易导致最后一行被处理两次，应写成 `while (fin >> x)`。

**字符串流**：常用于字符串与数字之间的转换。

```cpp
istringstream iss("10 20 30");
int a, b, c;
iss >> a >> b >> c;                 // a=10, b=20, c=30

ostringstream oss;
oss << "score=" << 95;
string s = oss.str();               // "score=95"
```

## 11.8　本章小结

- `vector<int> v(5, 7)` 是 5 个 7，`v {5, 7}` 是 2 个元素；`v[i]` 不检查越界，`v.at(i)` 检查。
- map 按键有序；用 `[]` 访问不存在的键会插入该键。
- `end()` 指向尾后位置，区间左闭右开；erase 后要用返回值更新迭代器。
- `sort` 需要随机访问迭代器，list 用成员函数 `sort()`；自定义类型排序需重载 `<` 或传比较函数。
- `unique_ptr` 独占、只能移动；`shared_ptr` 共享、引用计数为 0 时释放。
- 文件读取用 `while (fin >> x)` 或 `while (getline(fin, line))`。
