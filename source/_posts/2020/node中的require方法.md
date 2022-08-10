---
title: node中的require方法
date: 2020-03-10 17:31:11
tags: node.js
index_img: /2020/03/10/node中的require方法/logo.jpg
---

### 模块的概念
node中js文件就是一个模块。

#### 为什么出现模块的概念
防止命名冲突，可以把相同的功能封装到一起。

### 简单版的require
我们来实现一下自己的简易版require，源码里的实现还是挺复杂的。
在工作目录中创建文件 Module.js,内容如下：

``` javascript
function Modules() {
}

function req(){
}
req('./a');
```

再创建一个 a.json,内容如下：
```json
{
    "a":"xxx"
}
```
node模块是按照后缀名查找的，先`.js` 然后 `.json`文件。
所以我们在module.js中写入：
```javascript
Module.extensions = {
    '.js'() {},
    '.json'(){}
}
```

#### 第一步：把相对路径转换成绝对路径
要把用户传进来的相对路径转换成绝对路径。
先假设文件名有带后缀，然后判断是否存在该文件，
如果不存在，则从制定的文件后缀去拿出每一个后缀，让文件名和后缀拼接。
继续循环去查找文件是否存在。
接下来，给Module创建一个`resolveFileName`方法，来实现我们的逻辑：
> 需要引入path,和fs 模块
```javascript
// 给我一个相对路径，我给你解析成绝对路径
Module.resolveFileName = function (filename) {
  let absPath = path.resolve(__dirname, filename); // 1. 把相对路径转换为绝对路径
  let flag = fs.existsSync(absPath); // 判断文件是否存在
  let current;
  if (!flag) {
    let keys = Object.keys(Module.extensions); // 取后缀
    for (let i = 0; i < keys.length; i++) { 
      current = absPath + keys[i]; // 拼接每一个有可能的文件
      let flag = fs.existsSync(current);  // 判断是否存在
      if (flag) { 
        break;
      } else {
        current = null;
      }
    }
  }
  if (!current) { // 如果加了后缀还是不存在，则抛出错误
    throw new Error('文件不存在');
  }
  return current; // 返回路径
}
```

#### 第二步：根据绝对路径创建一个模块
模块里有id,和exports。所以我们在Module里写入：
```javascript
function Module(id) {
  this.id = id;
  this.exports = {}; // 模块的结果
}
```
创建一个module, 并且要加载这个模块, 所以，在req函数内写入：
```javascript
function req(filename) {
  let current = Module.resolveFileName(filename);
  let module = new Module(current); // 产生一个module
   module.load(); // 加载

  return module.exports; // 默认导出module.exports对象。
}
```

#### 第三步：模块的加载
模块的加载就是读取文件的内容,由于我们不知道传过来的是js还是json,
因此我们要根据不同的后缀，调用不同的处理方法：
```javascript
// 模块的加载就是读取文件的内容
Module.prototype.load = function() {
  let ext = path.extname(this.id);
  Module.extensions[ext](this); // 根据不同的后缀调用不同的处理方法。
}
```
这样处理方法就会接收到一个module,如果是json,那直接返回一个json就行。
```html
Module.extensions = {
  ".js"() {
  },
  ".json"(module) {
    let script = fs.readFileSync(module.id, 'utf8');
    module.exports = JSON.parse(script);
  }
}
```

到这里我们就能读取json文件的内容：
```html
let json = req('./a');
console.log(json);  //  {a:'xxx'}
```
#### 第四步：读取js

还有一种可能是js, js需要将exports,传给用户，让用户自己赋值。
先创建一个a.js,内容如下:
```html
module.exports = 'hello';
```
然后需要创建一个函数将用户传递的内容包裹起来：
```html
Module.wrapper = [
  '(function(module, exports, require, __filename, __dirname){',

  '})'
]
Module.extensions = {
  ".js"(module) {
    let script = fs.readFileSync(module.id, 'utf8'); // module.exports = 'hello';
    let fnStr = Module.wrapper[0] + script + Module.wrapper[1];
  },
  ".json"(module) {
    let script = fs.readFileSync(module.id, 'utf8');
    module.exports = JSON.parse(script);
  }
}
```
接下来要用到一个vm模块，它的`runInThisContext`方法能将字符串变成js代码。
>记得const vm = require('vm')；
转换完就像下面这样：
(function(module, exports, require, `__filename`, `__dirname`){module.exports = 'hello';})

代码如下：
```html
Module.extensions = {
  ".js"(module) {
    let script = fs.readFileSync(module.id, 'utf8'); // module.exports = 'hello';
    let fnStr = Module.wrapper[0] + script + Module.wrapper[1];
    let fn = vm.runInThisContext(fnStr); // 让字符串变成js代码
    fn.call(module.exports, module, module.exports, req, module.id, path.dirname(module.id));// 给用户更改对象
  },
  ".json"(module) {
    let script = fs.readFileSync(module.id, 'utf8');
    module.exports = JSON.parse(script);
  }
}
```
>第一个参数是改变this的指向，第二个是module,第三个是module.exports,第四个是文件名，第五个是父路径。

#### 第五步：缓存module
这样就能打印出js的内容，但是这样会有多次引用的问题，每次`req`同一文件的时候都会创建一个module.
所以我们用一个缓存，来实现多次加载，只有一次，代码如下：

```html
Module._cache = {};
function req(filename) {
  let current = Module.resolveFileName(filename);
  if(Module._cache[current]){
    return Module._cache[current].exports; // 如果加载过了，直接返回exports
  }
  let module = new Module(current);
  Module._cache[current] = module;
  module.load();
  return module.exports; // 默认导出module.exports对象。
}
let json = req('./a');
console.log(json);
```
这样我们的req就完成了。

### module.exports和exports
module.exports和exports是相等的。
```html
// a.js
console.log(module.exports === exports); // true
module.exports = 'hello';
```
但是为什么我们使用module.exports导出可以，直接用exports导出不行呢？
```html
module.exports = 'hello'; // => hello
exports = 'hello' // {}
```
这是因为，他们的关系是：
    
    let exports = module.exports = {};

所以我们开发时应该采用`export.a` 或者 `module.exports`;
不要使用global,会导致全局污染。

### 模块的查找路径
一般情况下会先查找文件，找不到的话，找文件夹，再找不到会报错。

#### 第三方文件夹查找
它会找node_modules下的同名文件下的index.js,如果找不到，会向上级查找。直到根目录。
如果文件夹下的入口文件不叫index.js，需要建一个package.json，声明入口文件，内容如下：
```json
{
  "main":"a.js"
}
```
这样就能查找到。如果没有main 会找index.js -> index.json

### 完整代码如下：
```html
const path = require('path');
const fs = require('fs');
const vm = require('vm');

function Module(id) {
  this.id = id;
  this.exports = {}; // 模块的结果
}

Module.wrapper = [
  '(function(module, exports, require, __filename, __dirname){',

  '})'
]
Module.extensions = {
  ".js"(module) {
    let script = fs.readFileSync(module.id, 'utf8'); // module.exports = 'hello';
    let fnStr = Module.wrapper[0] + ' ' + script + Module.wrapper[1];
    let fn = vm.runInThisContext(fnStr); // 让字符串变成js代码
    fn.call(module.exports, module, module.exports, req, module.id, path.dirname(module.id));
  },
  ".json"(module) {
    let script = fs.readFileSync(module.id, 'utf8');
    module.exports = JSON.parse(script);
  }
}
// 给我一个相对路径，我给你解析成绝对路径
Module.resolveFileName = function (filename) {
  let absPath = path.resolve(__dirname, filename); // 1. 把相对路径转换为绝对路径
  let flag = fs.existsSync(absPath); // 判断文件是否存在
  let current;
  if (!flag) {
    let keys = Object.keys(Module.extensions);
    for (let i = 0; i < keys.length; i++) {
      current = absPath + keys[i];
      let flag = fs.existsSync(current);
      if (flag) {
        break;
      } else {
        current = null;
      }
    }
  }
  if (!current) { // 如果加了后缀还是不存在，则抛出错误
    throw new Error('文件不存在');
  }
  return current;
}

// 模块的加载就是读取文件的内容
Module.prototype.load = function () {
  let ext = path.extname(this.id);
  Module.extensions[ext](this); // 根据不同的后缀调用不同的处理方法。
}
Module._cache = {};
function req(filename) {
  let current = Module.resolveFileName(filename);
  if (Module._cache[current]) {
    return Module._cache[current].exports; // 如果加载过了，直接返回exports
  }
  let module = new Module(current);
  Module._cache[current] = module;
  module.load();
  return module.exports; // 默认导出module.exports对象。
}
let json = req('./a');
console.log(json);
```

### over

西塞山前白鹭飞，桃花流水鳜鱼肥。
「渔父歌」
张志和

