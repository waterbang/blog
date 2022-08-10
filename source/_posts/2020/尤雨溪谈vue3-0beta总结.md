---
title: 尤雨溪谈vue3.0beta总结
date: 2020-04-21 22:41:25
tags: VUE
index_img: /2020/04/21/尤雨溪谈vue3-0beta总结/index.png
---
### 前言
vue3.0测试版已经发布了。尤雨溪在`bilibili`直播中，分享了一些新特性。
vue3中所有的一手信息，可以在[RFC](https://github.com/vuejs/rfcs)中查阅。
>https://github.com/vuejs/vue-next#status-beta
>视频链接
>链接：https://pan.baidu.com/s/1l18x-Duubn17XQx8XZJR_A 
 提取码：otbp 

您可以在Vue CLI中通过[vue-cli-plugin-vue-next](https://github.com/vuejs/vue-cli-plugin-vue-next)获得实验性支持。

## 亮点
·   Performance （通过一些细节实现性能的提高）
·   Tree-shaking support（没有用到的API不进行打包）
·   [Composition API](https://composition-api.vuejs.org/) （vue的组合API）
·   `Fragment`, `Teleport`, `Suspense` （新的内置的功能）
·   Better TypeScript support （更强的TS支持）
·   Custom Renderer API（第一方暴露自定义渲染API）

## 性能（Performance）
>性能比较只比较JavaScript引擎占用的时间，场景皆为模拟，具体看真实的环境。
>[vue3模板编译的程序](https://vue-next-template-explorer.netlify.app/#%7B%22src%22%3A%22%3Cdiv%3EHello%20World!%3C%2Fdiv%3E%22%2C%22options%22%3A%7B%22mode%22%3A%22module%22%2C%22prefixIdentifiers%22%3Afalse%2C%22optimizeBindings%22%3Afalse%2C%22hoistStatic%22%3Afalse%2C%22cacheHandlers%22%3Afalse%2C%22scopeId%22%3Anull%7D%7D)

### 重写了 virtual dom
virtual dom本质上还是需要去花时间去编译的。vue3利用了编译器的特性，通过分析模板，来实现模板编译时的优化。
生成优化过后的virtual dom。


### 优化模板编译（Compiler informed fast paths）
假如我们要编译以下代码：
```html
<div>
  <span>static</span>
  <span>{{msg}}</span>
</div>
```
它会编译成下面这样：
```js
import { createVNode as _createVNode, toDisplayString as _toDisplayString, openBlock as _openBlock, createBlock as _createBlock } from "vue"
export function render(_ctx, _cache) {
  return (_openBlock(), _createBlock("div", null, [
    _createVNode("span", null, "static"),
    _createVNode("span", null, _toDisplayString(_ctx.msg), 1 /* TEXT */) //page flag
  ]))
}
// Check the console for the AST
```
vue会在运行时，只有带有page flag的节点会被真正的追踪。也就是说，当我们后续要更新的时候，vue就会直接去找到这个动态节点。
而且通过flag的信息，可以知道只需要要比较text内容的变动，不需要去管其他的属性，或者绑定。
并且不用管层级嵌套得很深，它的动态节点是直接跟Block的根节点绑定起来的。所以不再需要去遍历静态的节点。
再看以下代码：
```html
<div>
  <span>static</span>
  <span id = "bar">{{msg}}</span>
</div>
```
编译成下面这样
```html
import { createVNode as _createVNode, toDisplayString as _toDisplayString, openBlock as _openBlock, createBlock as _createBlock } from "vue"
export function render(_ctx, _cache) {
  return (_openBlock(), _createBlock("div", null, [
    _createVNode("span", null, "static"),
    _createVNode("span", { id: "bar" }, _toDisplayString(_ctx.msg), 1 /* TEXT */)
  ]))
}
```
这个id是静态的，所以我们的page flag 也没有变化，对于runtime来说，这个id存不存在都没有区别。
只有在创建的时候创建了一次，后续的更新都不用管了。
如果将id改成动态：
```html
<div>
  <span>static</span>
  <span :id = "bar">{{msg}}</span>
</div>
```
编译后：
```html
import { createVNode as _createVNode, toDisplayString as _toDisplayString, openBlock as _openBlock, createBlock as _createBlock } from "vue"
export function render(_ctx, _cache) {
  return (_openBlock(), _createBlock("div", null, [
    _createVNode("span", null, "static"),
    _createVNode("span", { id: _ctx.bar }, _toDisplayString(_ctx.msg), 9 /* TEXT, PROPS */, ["id"])
  ]))
}
```
做成动态绑定之后，page flag 变成 `/* TEXT, PROPS */, ["id"]`,它告诉我们，不仅有text的变化，还有PROPS的变化，变化的就是数组里的id。

这样就既跳出了virtual dom性能的瓶颈，又保留了可以手写render的灵活性。
也可以理解为：既有react的灵活性，又有基于模板的性能保证。


### 侦听缓存（cacheHandlers）
假如我们要绑定一个事件：
```html
<div>
  <span @click = "onClick">{{msg}}</span>
</div>
```
默认没有优化的编译是这样的:
```html
import { toDisplayString as _toDisplayString, createVNode as _createVNode, openBlock as _openBlock, createBlock as _createBlock } from "vue"
export function render(_ctx, _cache) {
  return (_openBlock(), _createBlock("div", null, [
    _createVNode("span", { onClick: _ctx.onClick }, _toDisplayString(_ctx.msg), 9 /* TEXT, PROPS */, ["onClick"])
  ]))
}
```
我们需要将它看作一个动态的绑定，如果后续要替换掉onClick是需要进行一次更新的。
如果我们使用`cacheHandlers`,进行优化：
```html
import { toDisplayString as _toDisplayString, createVNode as _createVNode, openBlock as _openBlock, createBlock as _createBlock } from "vue"

export function render(_ctx, _cache) {
  return (_openBlock(), _createBlock("div", null, [
    _createVNode("span", {
      onClick: _cache[1] || (_cache[1] = $event => (_ctx.onClick($event)))
    }, _toDisplayString(_ctx.msg), 1 /* TEXT */)
  ]))
}
```
它会生成一个内联函数，这个内联函数才会去引用当前最新的`onClick`,然后把这个内联函数缓存起来。
第一次执行的时候，会创建这个函数并且缓存，后续直接在缓存里读取这个函数。
所以上面的没有再标记flag,将其变成了静态的。
我们还可以在`click`里手写内联函数，vue也会将内联函数缓存起来，帮助你跳过更多的更新。
这个的优势主要体现在组件上：
```html
<div>
  <Foo @click = "()=>foo()">{{msg}}</Foo>
</div>
```
这样导致的问题是：父组件一旦更新，子组件也会跟着更新。
`cacheHandlers`解决了这个问题，并且vue3在编译时就帮你做好，让我们不用考虑这个问题。

### 更快的服务器渲染 （ 2-3x faster SSR*）
如果我们在进行SSR的时候，有很多的静态内容：
```html
<div>
  <div>
    <span>hello</span>
  </div>
    <div>
    <span>hello</span>
  </div>
    <div>
    <span>hello</span>
  </div>
    <div>
    <span>hello</span>
  </div>
  <div :id = "bar"></div>
</div>
```
编译结果：
```html
import { ssrRenderAttr as _ssrRenderAttr } from "@vue/server-renderer"

export function ssrRender(_ctx, _push, _parent) {
  _push(`<div><div><span>hello</span></div><div><span>hello</span></div><div><span>hello</span></div>
<div><span>hello</span></div><div${_ssrRenderAttr("id", _ctx.bar)}></div></div>`)
}
```
它在编译的时候会将其当作一个字符串，直接推进Buffer里。如果包含动态id,也会尽量渲染成一个字符串。
这样服务端渲染的性能会大大提高。
并且如果在客户端的时候，静态节点达到一定的阈值，会直接对其innerHTML。

## Tree-shaking
这是vue3比2的一个较大的区别。比如说你没有用到`v-model` 或者 `transition`这些功能，就不会去编译到最后的包里。
这个Tree-shaking是通过编译器来实现的，举例来说。
如果我们引入一个div:
```html
<div></div>
```
它会引入以下内容：
```html
import { createVNode as _createVNode, openBlock as _openBlock, createBlock as _createBlock } from "vue"
export function render(_ctx, _cache) {
  return (_openBlock(), _createBlock("div"))
}
```
只有当你使用到的时候，才会被引入进去，而虚拟节点的更新算法和响应式系统，这是无论如何都会引入到你的包里的。
如果我们引入一个text的`v-model`:
```html
<input v-model="foo">
```
它会引入以下代码：
```html
import { vModelText as _vModelText, createVNode as _createVNode, withDirectives as _withDirectives, openBlock as _openBlock, createBlock as _createBlock } from "vue"
```
它将会把针对文字输入框的v-model代码引入进来。
如果我们改成`checkbox`:
```html
<input v-model="foo" type="checkbox">
```
它将会引入`checkbox`的代码:
```html
import { vModelCheckbox as _vModelCheckbox, createVNode as _createVNode, withDirectives as
 _withDirectives, openBlock as _openBlock, createBlock as _createBlock } from "vue"
```
 vue会尽可能的引入少的包，没有引入的会被tree-shaking掉。
 它在只引入一个HelloWorld，最终打包出来的大小只有13.5kb。
 
 ## [Composition API](https://composition-api.vuejs.org/api.html)
vue2百分之九十的代码在vue3是不受影响的。`Composition API`可以理解为一个新添加的API，它不影响对其他功能的使用。
它还可以与现有的逻辑一起使用。
抽离公共逻辑的时候，在vue2里用`mixins`，但是在vue3里就不要使用了，尽量使用`Composition API`。
其核心的api有：
·   [reactive]()
·   [ref](https://composition-api.vuejs.org/api.html#ref)
·   [computed](https://composition-api.vuejs.org/api.html#computed)
·   [readonly](https://composition-api.vuejs.org/api.html#readonly)
·   [watchEffect](https://composition-api.vuejs.org/api.html#watchEffect)
·   [watch](https://composition-api.vuejs.org/api.html#watch)
再加一个[Lifecycle Hooks](https://composition-api.vuejs.org/api.html#lifecycle-hooks)
其他的一些是一些工具函数，类似于`Loadsh`。

## Fragments （碎片）
这个功能让我们不用在用一个div把文件包裹起来，我们的模板可以只是一个纯文字，也可以是多个节点，它会自动变成碎片。
如果是渲染函数，也可以直接返回一个数组，也会自动变成一个碎片。

## `<Teleoirt>`
对标react的<Portal>,它可以接收一个disable的参数，如果disable的话，就会将本来应该传送出去的东西，
挪回来，放到原来的渲染树里面。主要是用于一些响应式的设计。

## `<Suspense>`
它会在嵌套树中等待嵌套异步依赖项。也就是说，它会在一个嵌套的组件树，渲染到一个屏幕上之前，先在内存中进行渲染，
在渲染的过程中，会记录所有存在异步依赖的组件，它只有在所有的异步依赖组件都resolve之后，才会把整个树渲染到DOM。
如果你的组件里有一个 async setup()的函数，这个组件就会被看成一个异步组件。
这样在一定程度上，实现了一个嵌套的异步调度。

## TypeScript
vue3用TS进行重写了，但不代表我们一定得用TS进行开发，我们用TS或者JS都能在开发的时候，获得类型声明，或者引入的自动补全。
用了TS，也会有更多的好处，比如有更强的静态类型检测。vue3也有TSX的支持。

## 自定义渲染器API(Custom Renderer API)
这个在vue2里可以通过一个非暴露的API进行实现,但是会产生一些依赖上同步的问题。
在vue3里变成了一个普通的API,充分暴露给了用户。

>扩展：[Vue.js自定义组件渲染器](https://alligator.io/vuejs/custom-component-renderers/)
>[`Vugel`](https://vugel.planning.nl/)


## [Vite](https://github.com/vuejs/vite)
可以看成一个小的HTTP服务器。
他可以直接引入一个script:
```html
<div id="app"></div>
<script type="module" src="/main.js"></script>
```
这样可以直接不用打包，用原生的ES6 import：
```html
import { createApp } from 'vue'
import Comp from './Comp.vue'

createApp(Comp).mount('#app')
```
这样它就会去服务器上请求对于的Vue文件，然后编译成javaScript发回去。
这个东西没有打包，没有编译，支持热更新。这个热更新请求哪个文件，哪个文件才会去打包。
而且浏览器会帮我们做缓存，感觉这个挺不错的。

### 结束语
但满目京尘，东风竟日吹露桃。
「忆旧游·记愁横浅黛」
周邦彦