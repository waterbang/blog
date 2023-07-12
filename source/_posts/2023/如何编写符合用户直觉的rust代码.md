---
title: 如何编写符合用户直觉的rust代码
date: 2023-07-12 20:26:40
tags: rust
index_img: 2023/07/12/如何编写符合用户直觉的rust代码/images.png
---

## 前言

在我们编写一些 rust 代码的时候，应该遵循一些原则，来保证开发者调用的时候，符合他的直觉，用起来不会感到意外。

以下文章主要讨论实现一些常用的 Trait,来保证用户的代码进行正常工作，以及如何让我们的代码能符合用户正常的预期。

[rust 官方的 api 指南](https://rust-lang.github.io/api-guidelines/checklist.html)主要声明的四点原则。

- 可预测性
- 灵活性
- 可预见，显而易见。
- 受约束

## 积极实现大部分标准的 Trait

我们在编写接口的时候，我们应该为用户去实现一些常用的标准 Trait，让用户开发的时候不会感到意外。
因为你的库对用户来说是外部类型，用户无法为外部类型实现外部的 Trait。
比如：

- 期望每个类型都是 Clone 的。
- 可以发送任意的东西到另外的线程。
- 可以使用 {:?} 打印任意类型。

以下将讨论建议实现的 Trait。

### Debug Trait

几乎所有的类型都应该去实现 Debug Trait,使用`#[derive(Debug)]`是最佳实践。

> 注意:派生的 Trait 会为任意范型参数添加相同的约束 (bound)

```rust
use std::fmt::Debug;

#[derive(Debug)]
struct Pair<T> {
    a: T,
    b: T,
}

fn main() {
    let pair: Pair<i32> = Pair { a: 5, b: 10 };
    println!("pair: {:?}", pair);
}
```

注意，这里的 a 和 b 都是范型 T,因此也要求，a 和 b 都实现 Debug Trait。

我们也可以利用`fmt::Formatter` 来提供各种 `debug_xxx`辅助方法的手动实现。

- debug_struct
- debug_tuple
- debug_list
- debug_set
- debug_map

```rust
use std::fmt;

struct Pair<T> {
    a: T,
    b: T,
}
impl<T:fmt::Debug> fmt::Debug for Pair<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Pair")
        .field("a", &self.a)
        .field("b", &self.b)
        .finish()
    }
}
fn main() {
    let pair: Pair<i32> = Pair { a: 5, b: 10 };
    println!("pair: {:?}", pair);
}
```

这里主要实现了`debug_struct`,输出效果跟上面是一样的。

### Send 和 Sync

自己实现 Send 和 Sync 是非常麻烦的，因为需要程序员自己保证内存安全，如果一个类型的所有成员都实现了这些 Trait,那么该类型也会自动实现这些 Trait。

#### Send

如果不是 Send 的类型无法放在 Mutex 中，也不能在包合线程池的应用程序中传递使用。

```rust
use std::rc::Rc;

#[derive(Debug)]
struct MyBox(*mut u8);
unsafe impl Send for MyBox{}

fn main () {
    let mb = MyBox(Box::into_raw(Box::new(42)));
    let x = Rc::new(42);
    std::thread::spawn(move || {
        println!("{:?}",x);
    });
}
```

以上代码会报错：`Rc<i32>` cannot be sent between threads safely。因为`Rc<i32>`并没有实现 send Trait，而我们的 MyBox 实现了 send Trait，
因此我们只要把 x 替换为 mb，代码就不会报错了。

#### Sync

如果不是 Sync 的类型无法通过 Arc 共享，也无法被放置在静态变量中。
比如下面这段代码，x 没有实现 Sync Trait 在线程中共享也是不允许的。

```rust
use std::{sync::Arc, cell::RefCell};

fn main() {
    let x = Arc::new(RefCell::new(42));
    std::thread::spawn(move || {
        let mut x = x.borrow_mut();
        *x += 1;
    });
}
```

如果我们没有实现以上 Trait 需要在文档说明。

### Clone 和 Default

这两个都是比较常用的类型，他们的最佳声明实践是直接通过 derive 去声明。

- #[derive(Clone)]
- #[derive(Default)]

### PartialEq,PartialOrd,Hash,Eq,Ord

#### partialEq

这个 Trait 比较常用，是用来比较类型的两个实例,以下这个例子就可以直观的感受到。

```rust
#[derive(Debug, PartialEq)]
struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let point1 = Point { x: 1, y: 2 };
    let point2 = Point { x: 1, y: 2 };
    let point3 = Point { x: 1, y: 3 };
    println!("point1 == point2: {}", point1 == point2);
    println!("point1 == point3: {}", point1 == point3);
}
```

#### PartialOrd 和 Hash

它们两个相对专门化。
如果需要将类型作为 Map 中的 Key。则需要实现 PartialOrd，以便进行 Key 的比较。

```rust
use std::collections::BTreeMap;

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Clone)]
struct Person {
    name: String,
    age: u32,
}

fn main() {
    let mut ages: BTreeMap<Person, &str> = BTreeMap::new();
    let person1 = Person {
        name: "A".to_owned(),
        age: 25,
    };
    let person2 = Person {
        name: "B".to_owned(),
        age: 26,
    };
    let person3 = Person {
        name: "C".to_owned(),
        age: 27,
    };
    ages.insert(person1.clone(), "A 's age");
    ages.insert(person2.clone(), "B 's age");
    ages.insert(person3.clone(), "C 's age");

    for (person, description) in &ages {
        println!("{}: {} - {:?}", person.name, person.age, description);
    }
}
```

而如果要使用 std::collection 的集合类型进行去重的类型，则需要实现 Hash 以便进行哈希计算。

```rust
use std::{
    collections::HashSet,
    hash::{Hash, Hasher},
};

#[derive(Debug, PartialEq, Eq, Clone)]
struct Person {
    name: String,
    age: u32,
}
impl Hash for Person {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.name.hash(state);
        self.age.hash(state);
    }
}

fn main() {
    let mut persons: HashSet<Person> = HashSet::new();
    let person1 = Person {
        name: "A".to_owned(),
        age: 25,
    };
    let person2 = Person {
        name: "B".to_owned(),
        age: 26,
    };
    let person3 = Person {
        name: "C".to_owned(),
        age: 27,
    };
    persons.insert(person1.clone());
    persons.insert(person2.clone());
    persons.insert(person3.clone());
    println!("Persons {:?}", persons);
}
```

我们的 Person 类型就是实现了 Hash Trait。

#### Eq 和 Ord

Eq 和 Ord 有额外的语意要求，相当于是 PartialEq 和 PartialOrd 的扩展。

Eq 一些额外的要求：

- 反身性 (Reflexivity) : 对于任何对象 X，X = X 必须为真。
- 对称性 (Symmetry) : 对于任何对 X 和 Y，如 X = Y 为真，则 Y == X 也必须为真。
- 传递性 (Transitivity) : 对于对象 X、Y 和 Z 如 X == Y 为，并且 Y == Z 为真，则 X == Z 也必真。

Ord 一些额外的要求：

- 自反性 (Reflexivity) : 对于任何对象 X，X >= X 和 X <= X 必须为真。
- 反对称性 (Antisymmetry) : 对于任何对象 X 和 Y，如 X <= Y 和 Y >= X 都为真，则 Y = X 必须为真。
- 传递性 (Transitivity) : 对于任何对象 X、Y 和 Z,如果 X <= Y 和 Y <= Z 都为真则 X <= Z 必须为真。

### serde 下的 Serialize 和 Deserialize

他妈负责一些序列化和反序列化的。而 serde derive (crate) 提供了机制，可以覆盖单个字段或枚举变体的序列化，
由于 serde 是第三方库，用户可能不希望强制添加对它的依赖。
大多数库选择提供一个 serde 功能(feature) ，只有当用户选择启用该功能时才添加对 serde 的支持。

比如，我们的库的 cargo.toml 可以这样写：

```toml
[dependencies]
serde = { version = "1.0", optional = true }

[features]
serde = ["serde"]
```

这样让我们的`serde`是可选的，然后在 features 里面取一个名，也叫`serde`，这样用户在使用的时候就可以选择的去开启。

别人用的时候就可以这样子引用(我们的库叫 mylib)：

```toml
[dependencies]
mylib = { version = "0.1" features = ["serde"]}
```

用户在使用的时候，就可以自由选择，看是否开启`serde`。

### 不建议实现 Copy

我们通常不期望类型是 Copy 的,如果想要两个副本，通常希望调用 clone，因为 Copy 是隐性的，
用户在使用的时候，可能忘记他使用的类型已经被复制了。
并且 Copy 改变了移动给定类型值的语义，可能让开发者感到意外。

Copy 类型受到很多限制，一个最初简单的类型很容易变得不再满足 Copy 的要求。
例如持有了 String 或者其他非 Copy 的类型就会导致不得不移除 Copy，进而引发大的修改。

```rust
#[derive(Debug, Copy, Clone)]
struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let point1 = Point { x: 10, y: 20 };
    let point2 = point1; // 这里发生的是复制，而不是移动。
    println!("point1: {:?}", point1);
    println!("point2: {:?}", point2);
}
```

## 实现更舒适的 Trait

rust 不会自动为实现 Trait 的类型的引用，提供对应的实现。
比如：
Bar 实现了 Trait ,但是不能将 &Bar 传递给 `fn foo<T: Trait>(t:T)`。
因为 Trait 可能包含接受 &mut self 或 self 的方法，而这些方法无法在&Bar 上调用。

```rust
fn foo<T: MyTrait>(t: T) {}

trait MyTrait;
struct Bar;
impl MyTrait for Bar {}

//你可以这样使用
let bar = Bar;
foo(bar);
//但无法这样使用
let bar = Bar!
let bar_ref = &bar;
foo(bar_ref);
```

这对于看到 Trait 只有 &self 方法的用户来说，非常难受。
因此我们在定义新的 Trait 的时候，通常需要提供下列相应的全局实现

- &T where T: Trait
- &mut T where T: Trait
- Box<T> where T: Trait

```rust
impl MyTrait for &T
where
  T: MyTrait
{}

impl MyTrait for &mut T
where
  T: MyTrait
{}

impl MyTrait for Box<T>
where
  T: MyTrait
{}
```

### Iterator

对于任何可迭代的类型，考虑为 &MyType 和 &mut MyType 实现 IntoIterator
这样在循环中可直接使用借用实例，符合用户预期。

### 包装类型（Wrapper Types）

如果我们提供了相对透明的类型 (例 Arc),我们可以实现 Deref 和 AsRef 来对类型进行一定转换。

- 实现 Deref 允许你的包装类型在使用点运算符时，自动解引用为内部类型，从而可以直接调用内部类型的方法。
- 如果访问内部类型不需要任何复杂或潜在的低效逻辑，应考虑实现 AsRef，这样用户可以轻松地将 &WrapperType 作为 &InnerType 使用。
- 对于大多数包装类型，还应该在可能的情况下实现 From<InnerType>和 Into<InnerType>，以便用户可轻松地添加或移除包装。

例如：

```rust
use std::ops::Deref;

struct Wrapper(String);

impl Deref for Wrapper {
    type Target = String;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}
impl AsRef<str> for Wrapper {
    fn as_ref(&self) -> &str {
        &self.0
    }
}
impl From<String> for Wrapper {
    fn from(value: String) -> Self {
        Wrapper(value)
    }
}
impl From<Wrapper> for String {
    fn from(wrapper: Wrapper) -> Self {
        wrapper.0
    }
}
fn main() {
    let wrapper = Wrapper::from("water".to_string());

    // 使用. 运算符调用内部字符串类型的方法
    println!("Length: {}", wrapper.len());

    // 使用 as_ref 方法 转换为 &str 类型
    let inner_ref: &str = wrapper.as_ref();
    println!("Inner: {}", inner_ref);

    // 将 Wrapper 转换为内部类型 String
    let inner_string: String = wrapper.into();
    println!("Inner String: {}", inner_string);
}
```

Deref 和 AsRef 适用于广泛的实现类型可以充当的情况。

### Borrow Trait

Borrow 与 Deref 和 AsRef 有些类似，它针对了更狭窄的使用情况进行了定制，

- 允许调用者提供同一类型多个本质相同的变体的其中一个（Equivalent）。

例如：对于一个 HashSet<String>，Borrow 允许调用者提供 &str 或 &String。
虽然使用 AsRef 也可以实现类似的效果，但如果没有 Borrow 的额外要求，这种实现是不安全的，
因为 Borrow 要求目标类型实现的 Hash、Eq 和 Ord 必须与实现类型完全相同。

- Borrow 还为 Borrow<T>, &T 和 &mut T 提供了通用实现。这使得在 Trait 约束中使用它来接受给定类型的拥有值或引用值非常方便

> 注意： Borrow 仅适用当你的类型本质上与另一个类型等价时。

```rust
use std::borrow::Borrow;

fn print_length<S>(string: S)
where
    S: Borrow<str>,
{
    println!("Length: {}", string.borrow().len());
}

fn main() {
    let str1: &str = "Hello";
    let string1: String = String::from("World");

    print_length(str1);
    print_length(string1);
}
```

参数类型 S 是 Borrow<str>的，本质上是字符串的两个变体，因此这样传递是没问题的。

## 结束语

这些内容很好的理清了开发一个库的时候，我们应该去实现哪些 Trait，这会让我们的代码变得更加的符合用户直觉。

参考见：

- [杨旭老师教程](https://www.bilibili.com/video/BV1Pu4y1Z7dT?p=1&vd_source=5a551b309f4cee1aa97066b4d520cef5)
- [rust 官方的 api 指南](https://rust-lang.github.io/api-guidelines/predictability.html)
