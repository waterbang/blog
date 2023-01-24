---
layout: port
title: 如何在v8中给js内置函数
date: 2023-01-24 12:56:20
tags: 
index_img: /2023/01/24/如何在v8中给js内置函数/header.png
---

### 前言

在v8中，内置的函数可以理解为在VM运行的一些内置的代码块，他们处在相同的作用域下。
如果您有ios(android)的`javascriptCore(interface/eventjavascript/more)`注入经验，或者其他的一些比较干净的`js`运行时的操作经验，您可以认为它们两者的共性是相同的。
那么建议您阅读英文的官方文档，本片文档仅用作个人入门使用。

### v8内置选择

V8 的内置函数可以使用多种不同的方法来实现（每种方法都有不同的权衡）：

1. Platform-dependent assembly language : 可以非常高效，但需要手动移植到所有平台并且难以维护。
2. C++：在风格上与运行时函数非常相似，可以使用 V8 强大的运行时功能，但通常不适合性能敏感的领域。
3. JavaScript：简洁易读的代码，访问快速内在函数，但频繁使用慢速运行时调用，由于类型污染导致不可预测的性能，以及围绕（复杂且不明显的）JS 语义的微妙问题。
4. CodeStubAssembler：提供非常接近汇编语言的高效低级功能，同时保持平台独立性和可读性。

> Platform-dependent assembly language 即平台相关的汇编语言，`CodeStubAssembler`是更好的选择。

### C++

`C++`的内置操作可以让您在`js`调用`C++`函数并且让`js`的对象能在`C++`上调用，适合C++程序员。

#### 前言

- 一个 isolate 是一个有自己堆的 VM 实例（从rusty_v8中能看到对isolate的操作）。
- 本地句柄是指向对象的指针。所有 V8 对象都使用句柄​​访问。由于 V8 垃圾收集器的工作方式，它们是必需的。
- 句柄范围可以被认为是任意数量句柄的容器。处理完句柄后，无需单独删除每个句柄，只需删除它们的作用域即可。
- 上下文是一个执行环境，它允许独立的、不相关的 JavaScript 代码在 V8 的单个实例中运行。您必须明确指定要运行任何 JavaScript 代码的上下文。

> 句柄包含一些持久化，不可复制之类的句柄，每次我们在js中new一个对象，就会在当前VM创建一个句柄。

#### inject hello world

直接来看这段代码，代码选自官方文档：
https://chromium.googlesource.com/v8/v8/+/branch-heads/6.8/samples/hello-world.cc

```C++

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "include/libplatform/libplatform.h"
#include "include/v8.h"
int main(int argc, char* argv[]) {
  // 初始化 V8。
  v8::V8::InitializeICUDefaultLocation(argv[0]);
  v8::V8::InitializeExternalStartupData(argv[0]);
  std::unique_ptr<v8::Platform> platform = v8::platform::NewDefaultPlatform();
  v8::V8::InitializePlatform(platform.get());
  v8::V8::Initialize();
  // 创建一个新的 Isolate 并使其成为当前 Isolate。
  v8::Isolate::CreateParams create_params;
  create_params.array_buffer_allocator =
      v8::ArrayBuffer::Allocator::NewDefaultAllocator();
  v8::Isolate* isolate = v8::Isolate::New(create_params);
  {
    v8::Isolate::Scope isolate_scope(isolate);
    // 创建一个堆栈分配的句柄范围。
    v8::HandleScope handle_scope(isolate);
    // 创建新的上下文.
    v8::Local<v8::Context> context = v8::Context::New(isolate);
    // 输入编译和运行 hello world 脚本的上下文。
    v8::Context::Scope context_scope(context);
    // 创建一个包含 JavaScript 源代码的字符串。
    v8::Local<v8::String> source =
        v8::String::NewFromUtf8(isolate, "'Hello' + ', World!'",
                                v8::NewStringType::kNormal)
            .ToLocalChecked();
    // 编译源代码。
    v8::Local<v8::Script> script =
        v8::Script::Compile(context, source).ToLocalChecked();
    //运行脚本得到结果。
    v8::Local<v8::Value> result = script->Run(context).ToLocalChecked();
    // 将结果转换为 UTF8 字符串并打印。
    v8::String::Utf8Value utf8(isolate, result);
    printf("%s\n", *utf8);
  }
  // 处理 isolate 并拆除 V8。
  isolate->Dispose();
  v8::V8::Dispose();
  v8::V8::ShutdownPlatform();
  delete create_params.array_buffer_allocator;
  return 0;
}
```

从上述的代码就能清楚的看到，本地句柄的创建，本地句柄保存在堆栈中，并在调用适当的析构函数时被删除。这些句柄的生命周期由句柄范围决定，通常在函数调用开始时创建。当 handle 作用域被删除时，垃圾收集器可以自由地释放 handle 作用域中 handle 先前引用的那些对象，前提是它们不再可以从 JavaScript 或其他 handle 访问。

### CodeStubAssembler

V8 的 CodeStubAssembler 是一个定制的、与平台无关的汇编器，它提供低级原语作为对汇编的精简抽象，但也提供了一个广泛的高级功能库。

#### 编写内置的CSA

我们将编写一个简单的 CSA 内置函数，它接受一个参数，并返回它是否代表数字42。内置函数通过将其安装在Math对象上而暴露给 JS。

这个例子演示了：

- 创建一个带有 JavaScript 链接的内置 CSA，它可以像 JS 函数一样被调用。
- 使用 CSA 实现简单逻辑：Smi 和堆编号处理、条件以及对 TFS 内置函数的调用。
- 使用 CSA 变量。
- Math在对象上安装内置的 CSA 。

#### 声明 `MathIs42`

在`src/builtins/builtins-definitions.h`声明如下内容：

```C++
#define BUILTIN_LIST_BASE(CPP, API, TFJ, TFC, TFS, TFH, ASM, DBG)              \
  // […snip…]
  TFJ(MathIs42, 1, kX)                                                         \
  // […snip…]
```

可以看到内置函数在BUILTIN_LIST_BASE宏中声明，BUILTIN_LIST_BASE采用几个不同的宏来表示不同的内置类型。

- TFJ：JavaScript 链接。
- TFS：存根链接。
- TFC：需要自定义接口描述符的内置存根链接（例如，如果参数未标记或需要在特定寄存器中传递）。
- TFH：用于 IC 处理程序的内置专用存根链接。

> 注意：如果定义了多个内置函数，需要注意他们的顺序。

#### 定义MathIs42

在`src/builtins/builtins-math-gen.cc`编写如下内容，您也可以查看`src/builtins/builtins-*-gen.cc`这些文件，会找到很多熟悉的身影。

```C++
// TF_BUILTIN是一个方便的宏，用于创建给定对象的一个新子类
//幕后的汇编程序。
TF_BUILTIN(MathIs42, MathBuiltinsAssembler) {
  //加载当前函数上下文(每个存根的隐式参数)和X参数。注意，我们可以通过名称来引用参数.
  Node* const context = Parameter(Descriptor::kContext);
  Node* const x = Parameter(Descriptor::kX);

  //在这一点上，x基本上可以是任何东西- Smi, HeapNumber，undefined，或任何其他任意JS对象。
  // 让我们调用ToNumber，将x转换为我们可以使用的数字。
  // CallBuiltin可以方便地调用任何CSA内置。
  Node* const number = CallBuiltin(Builtins::kToNumber, context, x);

  //创建一个CSA变量来存储结果值。
  //变量是kTagged，因为我们将只存储带标记的指针。
  VARIABLE(var_result, MachineRepresentation::kTagged);

  //我们需要定义两个标签作为跳转目标。
  Label if_issmi(this), if_isheapnumber(this), out(this);

  // ToNumber总是返回一个数字。我们需要区分Smis和堆号——在这里，我们检查number是否为Smi，并且是有条件跳转到相应的标签。
  Branch(TaggedIsSmi(number)， &if_issmi， &if_isheapnumber);

  //绑定标签开始为它生成代码。
  BIND(&if_issmi);
  ｛
    // SelectBooleanConstant返回JS的true/false值
    //传递的条件是否为true/false。结果必然是我们的
    // var_result变量，然后无条件跳转到out标签。
    var_result.Bind(SelectBooleanConstant(SmiEqual(number, SmiConstant(42))));
    Goto(&out);
  }

  BIND(&if_isheapnumber);
  ｛
    // 只是为了确保ToNumber只能返回Smi或堆号。我们在这里添加一个断言，验证number实际上是堆号。
    CSA_ASSERT(this, IsHeapNumber(number));
    // 堆数包装浮点值。我们需要显式地提取此值，执行浮点比较。
    // 然后再次绑定基于结果的var_result。
    Node* const value = LoadHeapNumberValue(number);
    Node* const is_42 = Float64Equal(value, Float64Constant(42));
    var_result.Bind(SelectBooleanConstant(is_42));
    Goto(&out);
  }

  BIND(&out);
  {
    Node* const result = var_result.value();
    CSA_ASSERT(this, IsBoolean(result));
    Return(result);
  }
}
 
```

#### 设置到js中

像Math这样的内置对象主要是在`src/bootstrapper.cc`中设置的。代码如下:

 ```C++
// 设置Math的现有代码，为了清晰起见包含在这里。
Handle<JSObject> math = factory->NewJSObject(cons, TENURED);
JSObject::AddProperty(global, name, math, DONT_ENUM);
// […snip…]
SimpleInstallFunction(math, "is42", Builtins::kMathIs42, 1, true);//++
 ```

 当设置完之后，就可以编译调用了。

 ```shell
 $ out/debug/d8
d8> Math.is42(42);
true
d8> Math.is42('42.0');
true
d8> Math.is42(true);
false
d8> Math.is42({ valueOf: () => 42 });
true
 ```

 使用 TFS 构建内置函数是在编译时生成的，并包含在 V8 快照中，不会在isolate中占用大量的空间。

 #### 为我们的内置函数编写测试代码

 在`test/cctest/compiler/test-run-stubs.cc`编写内容如下：

 ```C++
TEST(MathIsHeapNumber42) {
  HandleAndZoneScope scope;
  Isolate* isolate = scope.main_isolate();
  Heap* heap = isolate->heap();
  Zone* zone = scope.main_zone();

  StubTester tester(isolate, zone, Builtins::kMathIs42);
  Handle<Object> result1 = tester.Call(Handle<Smi>(Smi::FromInt(0), isolate));
  CHECK(result1->BooleanValue());
}
 ```

 ### 参考

 1. https://v8.dev/docs


### 叽里呱啦

欲吊文章太守，仍歌杨柳春风。
「西江月·平山堂」
苏轼