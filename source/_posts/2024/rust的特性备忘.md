---
title: rust的特性备忘
date: 2024-05-16 21:54:54
tags: rust
index_img: /2024/05/16/rust的特性备忘/title.jpeg
---

## 前言

由于个人学习的知识学一门忘一门，因此在这里总结一些比较容易忘记的细节内容，以备复习。

> 参考 ：杨旭<<Rust 编程语言中级教程>> ,《Rust for Rustaceans》

## 引用

rust 提供的引用是指针的一种高级抽象。引用就是指针。

- 引用始终引用的是有效数据
- 引用与 usize 的倍数对齐
- 引用可以动态大小的类型提供上述保障

引用会保证在内存中对齐，没有对齐的部分会填充字节，从而不会影响代码的运行速度。

例如：i32 类型在内存中占用的空间为 4 字节。

> rust 会把不没有固定长度的类型存储在内部指针的附近,这样可以让程序永远不会超出程序在内存中运行的空间，产生溢出漏洞，

## Raw Pointers（原始指针）

原始指针是没有 Rust 标准保障的内存地址，即本质上都是需要 unsafe 块包裹的。
它的速度极快，但是不安全。

- 不可变 Raw Pointer： `*const T`
- 可变的 Raw Pointer：`*mutT`

> 注意： `*constT`，这三个标记放在一起表示的是一个类型
>
> 例子： `*const String`

`*const T` 和 `*mutT` 之间差异很小，可以互相转换。

Rust 的引用（&mutT 和 &T ）会编译为原始指针。这意味着无需冒险进入 unsafe 块，就可以获得原始指针的性能。

### 例子：把引用转为原始指针

```rust
fn main() {
  let a:i64 = 42;
  let a_ptr: *const i64 = &a as *const i64;
  println!("a: {} ({:p})",a,a_ptr);
}
// ouput=> a: 42 (0x7ff7bd530670)
```

> {:p} 可以打印指针地址

解引用 （dereference）：通过指针从 RAM 内存提取数据的过程 叫做对指针进行解引用

```rust
fn main() {
    let a: i64 = 42;
    let a_ptr: *const i64 = &a as *const i64;
    let a_addr: usize = unsafe { std::mem::transmute(a_ptr) };
    println!("a: {} ({:p}... 0x{:x})", a, a_ptr, a_addr + 7);
}
// output=> a: 42 (0x7ff7bacca370... 0x7ff7bacca377)
```

> std::mem::transmute :将一种类型的值的位重新解释为另一种类型。两种类型必须具有相同的大小。如果不能保证这一点，编译将失败。

### 重要的提示 🔥

- 在底层，引用（&T 和 &mutT）被实现为原始指针。但引用带有额外的保障，应该始终作为首选使用
- 访问 原始指针 的值总是 unsafe 的
- 原始指针 不拥有值的所有权
- 在访问时编译器不会检查数据的合法性
- 允许多个 原始指针 指向同一数据
- Rust 无法保证共享数据的合法性

#### 什么时候可以使用原始指针

- 某些 OS 或第三方库需要使用，例如与 C 交互。
- 共享对某些内容的访问至关重要，运行时性能要求高。

## Smart Pointer（智能指针）

智能指针倾向于包装原始指针，附加更多的能力，不仅仅是对内存地址解引用。

### `Box<T>`

可以把任何东西都放在 Box 里。可接受几乎任何类型的长期存储。新的安全编程时代的主力军。

- 优点：将值集中存储在 Heap。
- 缺点：大小增加。

### `Rc<T>`

`Rc<T>`是 Rust 的能干而吝啬的簿记员。它知道谁借了什么，何时借了什么。

- 优点：对值的共享访问。
- 缺点：大小增加。运行时成本增加，线程不安全。

### `Arc<T>`

`Arc<T>`是 Rust 的大使。它可以跨线程共享值，保证这些值不会相互干扰。

- 优点：对值的共享访问，线程安全。
- 缺点：大小增加,运行时成本增加。

### `Cell<T>`

变态专家，具有改变不可变值的能力。

- 优点：内部可变性。
- 缺点：大小增加,性能降低。

### `RefCell<T>`

对不可变引用执行改变的能力，但有代价。

- 优点：内部可变性，可与仅接受不可变引用的 `Rc`、`Arc` 嵌套使用。
- 缺点：大小增加，运行时成本增加，缺乏编译时保障。

### `Cow<T>`

封闭并提供对借用数据的不可变访问，并在需要修改所有权时延迟克隆数据。

- 优点：当只是只读访问时可以避免写入。
- 缺点：大小可能会增加.

### `String`

可处理可变长度的文本，展示了如何构建安全的抽象。

- 优点：动态按需增长，在运行时保证正确编码。
- 缺点：过度分配内存大小。

### `Vec<T>`

程序最常用的存储系统；它在创建和销毁值时保持数据有序。

- 优点：动态按需增长。
- 缺点：过度分配内存大小。

### `RawVec<T>`

是`Vec<T>`和其它动态大小类型的基石，知道如何按需给你的数据提供一个家。

- 优点：动态按需增长。与内存分配器一起配合寻找空间。
- 缺点：代码上一般用不到。

### `Unique<T>`

作为值的唯一所有者，可保证拥有完全控制权。

- 优点：需要独占值的类型（如 String）的基础.
- 缺点：代码上一般用不到。

### `Shared<T>`

分享所有权。

- 优点：共享所有权,可以将内存与 T 的宽度对齐，即使是空的时候。
- 缺点：代码上一般用不到。

## 内存

有 3 个比较重要的内存区域`stack`,`heap`,`static`。

- stack 比较快，在内存中比较整齐。
- heap 比较慢，在内存中比较混乱。

## stack 栈内存

Stack 是一段内存. 其调用顺序是 LIFO（后进先出）的。
程序把它作为一个暂存空间，用于函数调用,main 函数就接近 Stack 底部。

想把数据放在 Stack，编译器必须知道类型的大小。

> 首选使用 Stack,也就是实现了 Sized 的类型。

### Stack Frame

Stack Frame 与 rust 的声明周期相关。

每个函数都拥有自己的 Frame 当函数返回时，它的 Frame 就被回收了,构成函数本地变量值的那些字节不会立即擦除， 但访问它们也是不安全的。

因为它们可能被后续的函数调用所重写（如果后续函数调用的 Frame 与回收的这个有重合的话）。

但即使没有被重写，它们也可能包含无法合法使用的值。例如函数返回后被移动的值。

### 小技巧

当一个函数即需要兼容 `&str`和 `String`的参数。

> $str 存在 Stack 上，String 存储在 Heap 上。

`AsRef<T>` 要求参数实现到 T 这个类型的引用，即使参数不是这样的类型。

```rust
fn is_strong<T: AsRef<str>>(password:T) -> bool {
  password.as_ref().len() > 6
}
```

`Into<String>` 要求参数转化为 String 这个类型。但是会涉及比较多的步骤。

```rust
fn is_strong<T: Into<String>>(password:T) -> bool {
  password.as_ref().len() > 6
}
```

## Heap 堆内存

Heap 在内存中是混乱的，它是一个内存池，并没有绑定到当前程序的调用栈，是为在编译时没有已知大小的类型准备的。

例如：

- 切片类型 [T]
- 随着程序运行动态改变的 String,Vec<T>
- trait 对象，它允许程序员来模拟一些动态语言的特性：通过允许将多个类型放进一个容器
- 一些类型的大小不会改变，但是无法告诉编译器需要分配多少内存

Heap 允许你显式的分配连续的内存块。当这么做时，你会得到一个指针，它指向内存块开始的地方。

Heap 内存中的值会一直有效，直到你对它显式的释放。如果你想让值活得比当前函数 frame 的生命周期还长，就很有用。

### Heap 线程安全

如果想把值送到另一个线程，当前线程可能根本无法与那个线程共享 stack frames，你就可以把它存放在 heap 上。

因为函数返回时 heap 上的分配并不会消失，所以你在一个地方为值分配内存，把指向它的指针传给另一个线程，就可以让那个线程继续安全的操作于这个值。

换一种说法：当你分配 heap 内存时，结果指针会有一个无约束的生命周期，你的程序让它活多久都行。

### Heap 机制

Heap 上面的变量必须通过指针访问。Rust 里与 Heap 交互的首要机制就是 Box 类型。

```rust
fn main() {
  let a:i32 = 40; // Stack
  let b:Box<i32> = Box::new(60); // Heap
  let result:i32 = a + *b; // 用指针访问。
}
```

当`Box:new（value）`时，值就会放在 heap 上，返回的`Box<T>`就是指向 heap 上该值的指针。当 box 被丢弃时，内存就被释放。

如果忘记释放 heap 内存，就会导致内存泄漏
有时你就想让内存泄露。

例子：在生命周期没有结束的时候手动释放。

```rust
fn main() {
    let a: Box<i32> = Box::new(1);
    let b: Box<i32> = Box::new(1);
    let result = *a + *b;
    drop(a);
    println!("{}", result);
}
```

#### 如何让内存泄露 🔥

例如有一个只读的配置，整个程序都需要访间它。就可以把它分配在 heap 上。

通过 Box:leak 得到一个'static 引用，从而显式的让其进行泄露。

## Static 静态内存

- static 内存实际是一个统称，它指的是程序编译后的文件中几个密切相关的区域。
  - 当程序执行时，这些区域会自动加载到你程序的内存里。
- static 内存里的值在你的程序的整个执行期间会一直存活。
- 程序的 static 内存是包含程序二进制代码的（通常映射为只读的）。
  - 随着程序的执行，它会在本文段的二进制代码中挨个指令进行遍历，而当函数被调用时就进行跳跃。
- static 内存会持有使用 static 声明的变量的内存，也包括某些常量值， 例如字符串。

### ‘static

'static 是特殊的生命周期,它的名字就是来自于 static 内存区，它将引用标记为只要 static 内存还存在（程序关闭前），那么引用就合法。

static 变量的内存在程序开始运行时就分配了，到 static 内存中变量的引用，按定义来说，就是'static 的，因为在程序关闭前它不会被释放。

一旦你创建了一个'static 生命周期的引用，就程序的其余部分而言，它所指向的内容都可能在 static 内存中，因为程序想要使用它多久就可以使用多久。

#### `T:'static`

其表示类型 T 可以存活我们想要的任何时长（直到程序关闭），同时这也要求 T 是拥有所有权的和自给自足的。

要求这个类型不借用其他的值，要么借用的值也都是`‘static`的。

### const 与 static 的区别

```rust
const x:i32 = 123;
```

- const 关键字会把紧随它的东西声明为常量
- 常量可在编译时完全计算出来。
- 在编译期间，任何引用常量的代码会被替换为常量的计算结果值
- 常量没有内存或关联其它存储（因为它不是一个地方）
- 可以把常量理解为某个特殊值的方便的名称

## 所有权

Rust 内存模型的核心思想：所有的值都只有一个所有者。

只有一个位置（通常是作用域）来负责释放每个值。

- 这是通过借用检查器来实现的。
- 如果值移动了（赋值新变量、推到 Vec、置于 Heap），其所有者也变成新的位置了。

有些类型不遵守这个规则。

- 如果值的类型实现了 Copy trait，重新赋值时到新内存地址时发生的是复制，而不是移动。
- 大多数原始类型，例如整数、浮点类型等，都实现了 Copy。

### 如何实现 Copy

实现 Copy trait 必须可以按位（bit）来复制值,不包括以下类型。

1. 含有 non-Copy 类型的类型
2. 拥有这类资源的类型：当类型的值被丢弃时，必须被释放该资源。

假设 Box 是 Copy 的，并且进行赋值 `box1 = box2`
那么它们在走出内存的时候，都会认为在 Heap 上，有一段内存是属于自己的。
都会去释放这个内存，这样就会产生问题。

## 引用

### &T 共享引用（不可变的引用）

共享引用背后的值不可变，因此又叫不可变引用。

`&T`就是可以共享的指针，可以同时存在任意数量的引用的引用指向同一个值，每个共享的引用都实现了 Copy.

### &mut T 可变引用

可变引用都是单一线程独占的,可变引用只允许你修改引用所指向的内存地址。

```rust
fn main() {
  let x:i32 = 42;
  let mut y: &i32 = &x;
  let z:&mut &i32 = &mut y; //  可以通过z来修改y的值
}
```

y 前面有 mut 关键字，因此也可以修改成其他值的引用，简单来说就是 y 可以修改成其他值，但是不可以通过 y 来修改 x 的值。

```rust
let mut y: &i32 = &x;
```

z 前面没有 mut 关键字，因此 z 不能持有其它的引用，只能持有 y 的引用。
但是可以通过 z 来修改 y 的值。

```rust
let z:&mut &i32 = &mut y;
```

### 内部可变性

类型可以通过共享引用来修改值。主要分为两种。

#### 通过共享引用获得可变引用

有`Mutex`,`RefCell` ，它们如果对某个值提供了可变引用，那么同时只会存在一个可变引用。

依赖 `UnsafeCell`类型，这是通过共享引用修改值的唯一方式。

#### 通过共享引用可以替换值

`std:syn:atomic`,`srd::cell::Cell`,它们没有提供可变引用到内部值，提供的是就地操作值的方法。

> 例：无法获得到 usize 或 i32 的直接引用，但是可以读取和替换值

### Cell 类型

Cell 提供对值的整体替换，返回值的副本，其无法跨线程共享，内部值不会发生并发修改，即便是通过共享引用发生的修改。

不会提供到 Cell 内部的值的引用，因此可以一直移动它。

## 生命周期

Rust 里每个引用都有生命周期，它就是引用保持合法的作用域， 大多数时候是隐式和推断出来的。
对某个变量取得引用时生命周期开始，当变量移动或离开作用域时生命周期结束。

### 借用检查器 （Borrow Checker）

每当具有某个生命周期 a 的引用被使用，借用检查器都会检查‘a
是否还存活,流程如下：

1. 追踪路径直到‘a 开始（获得引用）的地方
2. 从这开始，检查沿着路径是否存在冲突
3. 保证引用指向一个可安全访问的值

#### 生命周期重启 （生命周期更新）

```rust
let mut x:Box<i32> = Box::new(42);
let mut z =  &x; // z的生命周期开始了
for i in 0..100 {
  println!("{}",z);
  x = Box::new(i); // x的生命周期在这里被更新了
  z = &x; // 这里必须更新z的生命周期，也就是更新了x的引用,不更新引用将会报错，因为x一直处于被z借用的状态，无法被重新赋值。
}
println!("{}",z);
```

借用检测器是保守的，如果不确定某个借用是否合法，借用检查器就会拒绝该借用。

借用检查器有时需要帮助来理解某个借用为什么是合法的，这也是 Unsafe Rust 存在的部分原因。

## 泛型生命周期

主要是为了借用检查器能检查一些在类型中存储引用的生命周期。
例如：在该类型方法中返回引用，且存活比 self 的长。

rust 允许你基于一个或多个生命周期将类型的定义泛型化。但是这会让类型签名更加的复杂，因此需要遵循以下两点：

- 只有类型包含多个引用时，你才应该使用多个生命周期参数
- 它方法返回的引用只应绑定到其中一个引用的生命周期

多个类型引用示例

```rust
struct StrSplit<'s, 'p> {
    delimiter: &'p str, // 第二个泛型生命周期
    document: &'s str,  // 第一个泛型生命周期
}

impl<'s, 'p> Iterator for StrSplit<'s, 'p> {
    type Item = &'s str;

    fn next(&mut self) -> Option<Self::Item> {
        todo!()
    }
}

fn str_before(s: &str, c: char) -> Option<&str> {
    StrSplit {
        document: s,
        delimiter: &c.to_string(), // 这里的生命周期是比较短的，是当前函数所拥有的
    }
    .next()
}
```

### 生命周期扩展 （Variance）

如果 A 是 B 的子类，那么 A 至少和 B 一样有用。这跟其他类型的继承或者叫扩展是相同的。

比如：如果函数接收 &'a str 的参数，那么就可以传入 &'static str 的参数。因为'static 是 a 的“子类”，‘static 至少跟任何‘a 存活的一样长。

#### 三种 Variance

- covariant(协变)： 某类型只能用“子类型”替代

  - 例如：&'staticT 可替代 &'aT

- invariant(不变)：必须提供指定的类型

  - 例如：&mutT，对于 T 来说就是 invariant 的

- contravariant(逆变)：函数对参数的要求越低，参数可发挥的作用越大

```rust
let x1 : &'static str; // 更有用一些
let x2: &'a str;

fn take_fun1(&'static str1) // 限制更大
fn take_fun2(&'a str2) // 限制宽松
```

如上所示，在函数中，限制更宽松将会更有用一些，而在外部的话，存活得更久则更有用一些。

下面的示例为什么只有一个字段却使用两个生命周期呢？

```rust
struct MutStr<'a, 'b> {
    s: &'a mut &'b str,
}

fn main() {
    let mut r = "hello";
    *MutStr { s: &mut r }.s = "world"; // 对外部的r创建了一个可变的引用
    println!("{}", r); // 打印 world
}
```

上述示例中，`'a`是可变的，`'b`是不可变的。而在

```rust
*MutStr { s: &mut r }.s = "world";
```

的时候，对创建的 s 进行了修改，其对应的就是`'a`这个生命周期。

而 `*MutStr`结构体里面的 s 是静态的，因为 r 的生命周期是静态的，因此对于着 `'b` 这个不可变的生命周期。

## 内存对齐 repr(transparent)

### `#[repr(C)]`

C 的对齐方案编译较快，但是运行较慢。

这个对齐方式在内存中有一定的限制，需要将所有字段按原 struct 定义的顺序放置。

```rust
#[repr(C)]
struct Foo {
  tiny:bool, // 1byte 填充3个，和normal组成8个
  normal:u32, // 4bytes
  small:u8, // 1 byte  填充 7个对齐8个
  long:u64, // 8bytes
  short:u16, // 2bytes 填充6个进行对齐
}
```

这个结构体最大的是 long 拥有 8bytes，因此 tiny 后面将会填充 3 个字节，跟 normal4 个字节组合成 8 个字节。

而 small 拥有 1 个字节，它将继续填充 7 个字节，跟 8 字节对齐。

后面的 short 也将继续填充 6 字节，跟 8 字节对齐。一共 32 字节。

### `#[repr(Rust)]`

`repr(Rust)`允许重新对字段排序，可按大小递减的顺序排列。

对于 Foo 例子来说就不需要填充了：

```rust
#[repr(Rust)]
struct Foo {
  long:u64, // 8bytes
  normal:u32, // 4bytes // 下面组成8字节，跟上面的对齐
  short:u16, // 2bytes
  small:u8, // 1 byte
  tiny:bool, // 1byte
}
```

直接把最大的字段放前面，这样一下子就知道需要对齐到多少字节。一共 16bytes。

对布局的保证少了，编译器有余地进行重新安排，代码会更高效。但是编译时间会长一点。

### `$[repr(packed)]` 无填充布局

可以告诉编译器字段之间无需任何填充，但是需要承担不对齐访问的性能损失，并且可能会导致代码运行速度慢.
极端情况下，如果 CPU 仅支持对齐操作，可导致程序崩溃。

什么场景下使用：

- 内存有限，类型实例较多
- 通过低带宽网络连接发送内存表示

### `#[repr(align(n))]` 给特定字段或类型更大的对齐

这个主要是用来避免伪共享。

> 伪共享 （false sharing）：两个不同的 CPU 访问共享同一个缓存行的不同变量时， 就发生了伪共享。理论上它们可以并行操作，但最终它们都争相更新缓存中的同一个条目。它可导致并发类程序中的巨大性能降级。

## Sized 类型和宽指针

### Sized

rust 中除了两个常见的类型 Trait 对象和切片(slice)类型，大多数类型自动实现了 Sized,它的大小在编译时就已知了。

自定义的 Type Bound 自动包含`T:Sized`，除非你写明`T:?Sized`。

### 宽指针(Wide Pointer)

宽指针就是普通指针，附加了一个字大小(word-sized)的字段。

如果需要接收 DST（trait 对象，切片等）类型就需要宽指针，当引用 DST 时，编译器就会自动为你组建一个宽指针。

通过将非 Sized 类型放在宽指针后边，就可弥补 Sized 和非 Sized 类型间的差距。

例如：切片 slice, 它的附加信息就是切片的长度。

> 备注：Box 和 Arc 都支持存储宽指针，所以它们都支持`T:?Sized`

## 编译和分派

### 静态分派 (static dispatch)

静态分派的意思是需要为每个类型复制一份（方法体），每份都有自己的地址，可用来跳转。

编译器会复制泛型类型以及所有的实现块。并把每个实例的泛型参数使用具体类型替换。

例如：Vec<i32>，就是对 Vec 做一个完整的复制，所有遇到的 T 都换成 i32。

> 注意：编译器其实不会做完整的复制粘贴，它只复制你用的代码.

```rust
impl String {
  pub fn contains(&self,p impl Pattern) -> bool {
    p.is_contained_in(self)
  }
}
```

p 参数是 `impl Pattern`类型，针对不同的 Pattern 类型，该方法都会复制一遍。

因为我们需要知道 is_contained_in 方法的地址，以便进行调用。CPU 需要知道在哪跳转和继续执行。
对于任何给定的 Pattern，编译器知道那个地址是 Pattern 类型实现 Trait 方法的地址。
不存在一个可给任意类型用的通用地址。

#### 单态化 (monomorphization)

从一个泛型类型到多个非泛型类型的过程叫做单态化。当编译器开始优化代码时，就好像根本没有泛型！

- 每个实例都是单独优化的，具有了所有的已知类型
- 所以 is_contained_in 方法调用的执行效率就如同 Trait 不存在一样
- 编译器对涉及的类型完全掌握，甚至可以将它进行 inline 实现

但是单态化也是有代价的

- 所有的实例需要单独编译，编译时间增加（如果不能优化编译）
- 每个单态化的函数会有自己的一段机器码，让程序更大
- 指令在泛型方法的不同实例间无法共享，CPU 的指令缓存效率降低，因为它需要持有相同指令的多个不同副本

### 动态分派 (dynamic dispatch)

动态分派，使代码可以调用泛型类型上的 trait 方法，而无需知道具体的类型。

```rust
impl String {
  pub fn contains(&self,p &dyn Pattern) -> bool {
    p.is_contained_in(&*self)
  }
}
```

它只要求调用者提供两个信息：

1. Pattern 的地址
2. is_contained_in 的地址

#### vtable

调用者会提供指向一块内存的指针，它叫做虚方法表（virtual method table）或叫 vtable。它持上例该类型所有的 trait 方法实现的地址，其中一个就是 is_contained_in。

当代码想调用提供类型的一个 trait 方法时，就会从 vtable 查询 is_contained_in 方法的实现地址，并调用，这允许我们使用相同的函数体，而不关心调用者想要使用的类型。

每个 vtable 还包含具体类型的布局和对齐信息

#### 保证对象安全

- trait 所有的方法都不能是泛型的，也不可以使用 Self
- trait 不可拥有静态方法（我们无法知道在哪个实例上调用的方法）

动态分派的优点是，编译时间减少提升 CPU 指令缓存效率。

缺点是，编译器无法对特定类型优化,只能通过 vtable 调用。
函数直接调用方法的开销增加。trait object 上的每次方法调用都需要查 vtable。

### 如何选择

在 library 中使用静态分派，因为无法知道用户的需求,这样用户可自行选择,如果使用动态分派，用户也就没有选择。

在 binary 中使用动态分派,  因为 binary 是最终代码，并且动态分派使代码更整洁（省去了泛型参数），编译更快,但是以边际性能为代价。

## Trait 泛型方式

有两种：

- 泛型类型参数：`trait Foo<T>`
- 关联类型：`trait Foo {type Bar;}`

区别

- 使用关联类型：对于指定类型的 trait 只有一个实现
- 使用泛型类型参数：多个实现

简单来说可以的话尽量使用关联类型。

### 泛型 (类型参数) Trait

泛型 Trait 必须指定所有的泛型类型参数，并重复写这些参数的 Bound，维护较难。
如果添加泛型类型参数到某个 Trait，该 Trait 的所有用户必须都进行更新代码。

```rust
impl PartialEq<BookFormat> for Book
Fromlterator::<U32>::from_iter
```

### 关联类型 Trait

编译器只需要知道实现 Trait 的类型。

Bound 可完全位于 Trait 本身，不必重复使用，未来再添加 关联类型 也不影响用户使用。

```rust
trait Contains {
  type A;
  type B;
  fn contains(&self, _: &Self::A, _: &Self:B) -> bool;
}
```

具体的类型会决定 Trait 内关联类型的类型，无需使用消除歧义的函数。

```rust
impl Contains for Container {
    type A = i32;
    type B = i32;

    fn contains(&self, num_1: &i32, num_2: &i32) -> bool {
        (&self.0 == num_1) && (&self.1 == num_2)
    }

    fn first(&self) -> i32 { self.0 }

    fn last(&self) -> i32 { self.1 }
}
```

注意：

- 不可以对多个 Target 类型来实现 Deref

```rust
pub trait Deref {
    type Target: ?Sized;
    fn deref(&self) -> &Self::Target;
}
```

- 不可以使用多个 Item 来实现 Iterator

```rust
pub trait Interator {
  type Item;
}
```

## 孤儿规则 (orphan rule)

定义：对于给定的类型和方法，只会有一个正确的选择，用于该方法对该类型的实现。

只要 trait 或者 类型在你本地的 crate，那就可以为该类型实现该 trait。

可以为你的类型实现 Debug；可以为 bool 实现 MyTrait，不能为 bool 实现 Debug。

### Blanket Implementation (一揽子的实施)

`impl<T>MyTrait for T where T：`

例如：`impl<T: Display> ToString for T｛｝`

`where T`实现一系列的类型,不局限于一个特定的类型，而是应用于更广泛的类型。
只有定义 trait 的 crate 允许使用 Blanket Implementation。

注意：添加 Blanket Implementation 到现有 trait 属于破坏性变化。

### 基础类型

目前包括，`&`,`&mut`,`Box`,它们被标记为`#[fundamental]`,并且因为太基础了，需要允许任何人在它们上实现 trait（即使违反孤儿规则）。因此在孤儿规则检查前，它们就会被抹除。

### Covered Implementation (覆盖实施)

有时需要为外部类型实现外部 trait。

例如：`impl From<MyType> for Vec<i32>`

孤儿规则制定了一个狭窄的豁免：允许在非常特定的情况下为外来类型实现外来 trait。

例如：` impl<Pi..=Pn> ForeignTrait<Ti..=Tn> for T0`

只在以下条件被允许：

- 至少有一个 Ti 是本地类型。
- 没有 T 在第一个这样的 Ti 前（T 是指泛型类型 PI.=Pn 中的一个）。
- 泛型类型参数 Ps 允许出现在 TO..Ti，只要它们被某种中间 （intermediate）类型所 cover。

如果 T 作为其他类型（例 Vec<T>）的类型参数出现，那就说 T 被 cover 了。而 T 只作为本身，或者位于基础类型后（例 &T），就无法被覆盖了。

例子：

- 符合的：

```rust
impl<T> From<T> for MyType
impl<T> From<T> for MyType<T>
impl<T> From<MyType> for Vec<T>
impl<T> ForeignTrait<MyType, T> for Vec<T>
```

- 不符合的：

```rust
impl<T> ForeignTrait for T
impl<T> From<T> for T
impl<T> From<Vec<T>> for T
impl<T> From<MyType<T>> for T
impl<T> From<T> for Vec<T>
impl<T> ForeignTrait<T, MyType> for Vec<T>
```

- 为现有 trait 添加新的实现，且至少包含一个新的本地类型，该本地类型
  满足豁免条件，这就是非破坏性的变化
- 为现有 trait 添加的实现不满足上述要求，就是破坏性变化

注意：

- `impl<T> ForeignTrait<LocalType, T> for ForeignType`，本地类型出现在前面，是合法的。

- `impl<T>ForeignTrait<T, LocalType> for ForeignType`，T 出现在本地类型前面是非法的。
