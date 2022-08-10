---
title: 实现简单的koa
date: 2020-04-07 14:58:20
tags: node.js
index_img: /2020/04/07/实现简单的koa/index.png
---
### 前言
贴一波官网[koa](https://koa.bootcss.com/)

## 简介
koa 通过async函数帮助我们避免了回调函数。他的源码都是用类写的，基于http模块，
它的源码只有4个文件，分别是：
`application.js` : 应用入口，核心文件
` context.js` ： 上下文，主要为辅助方法
`request.js` ： 专门对应于请求
` response.js` ： 专门对应响应

### 如何用 
需要先引入koa,它会返回一个类,koa基于原生的node方法封装了request,和response。
koa 怕用户还要区分原生的req和res，与koa自己封装的封装了request,和response。
用 ctx代理了原生和koa封装的方法。这样就非常方便了。如我们要取路径：
    
    ctx.request.path
 
 这样子不太方便，直接下面这样就行了
 
       ctx.path
 
 
 koa核心用法
```html
const Koa = require('koa');

const app =  new Koa();

app.use((ctx,next) => {
  ctx.body = "hello!";
})

app.listen(3000);
```
koa帮我们解决了很多恶心的事，比如：
之前不能直接返回对象，现在只要：
```html
ctx.body = {obj:"water"}
```

> **注意：koa不建议绕过response，应该避免使用以下node属性：
>res.statusCode res.writeHead() res.write() res.end()**

## 构建自己的koa
在你的工作目录下创建，如下结构：
```html
|-koa
|-server.js
|-koa
    |-application.js
    |-context.js
    |-request.js
    |-response.js
```

为了先实现简单点,我们先用点原生的方法作为过渡，在server.js里写入以下代码：
```html
const Koa = require('./koa/application');

let app = new Koa();

app.use((req, res) => {
  res.end('hello');
})

app.listen(2000);
```

### Application
接着我们需要导出一个Koa类，源码里面默认叫`Application`。
然后添加两个方法，listen是监听一个端口号，use是存了一个函数，当请求到来的时候执行，代码如下：
```html
class Application{
  use(){ // 用来注册方法

  }
  listen(..args) { // 用来监听端口

  }
}

module.exports = Application;
```

#### listen && use
用http模块创建监听方法：
```html
const http = require('http');

class Application{
  use(fn){

  }
  handleRequest(req, res) {

  }
  listen(...args) {
    let server = http.createServer(this.handleRequest.bind(this));
    server.listen(...args);
  }
}

module.exports = Application;
```
把handleRequest拿出去用来接收use的方法，接着将fn放到handleRequest里面执行：
```html
const http = require('http');

class Application{
  use(fn){
    this.fn = fn;
  } 
  handleRequest(req, res) {
    this.fn(req, res);
  }
  listen(...args) {
    let server = http.createServer(this.handleRequest.bind(this));
    server.listen(...args);
  }
}

module.exports = Application;
```
这样就实现了一个简单的功能。我们用[nodemon](https://www.npmjs.com/package/nodemon)跑一下，在浏览器就能看到结果。

> 全局安装nodemon:  
>npm install -g nodemon 
>或者安装为开发依赖  
>npm install --save-dev nodemon

### 向Koa靠拢
koa没有实现res和req，只有一个ctx,我们需要封装request和response对象到ctx上，先修改一下server.js：
```
const Koa = require('./koa/application');

let app = new Koa();

app.use((ctx) => {
})

app.listen(2000);
```
接下来我们先来用上其他的文件，把对应的功能放到对应的文件，然后引入到application.js,
并且将引入的对象放到this上，为了不破坏原有的方法，并且方便扩展，使用`Object.create()`创建对象：

```html
// context.js
const context = {
}
module.exports = context;
```
```html
// response.js
const response = {
}
module.exports = response;
```
```html
// request.js
const request = {

}
module.exports = request;
```
在构造方法上赋值：
```html
const http = require('http');

const context = require('./context');
const response = require('./response');
const request = require('./request');

class Application{
  constructor() {
    this.context = context;
    this.response = response;
    this.request = request;
  }
  use(fn){
    this.fn = fn;
  } 
  handleRequest(req, res) {
    this.fn(req, res);
  }
  listen(...args) {
    let server = http.createServer(this.handleRequest.bind(this));
    server.listen(...args);
  }
}
module.exports = Application;
```

现在就需要变化fn()那边的req和res,将其变为ctx,ctx整合了req(原生),res(原生),request(自己的),response(自己的)。
我们先创建一个函数，来整合四个属性。：
```html
const http = require('http');

const context = require('./context');
const response = require('./response');
const request = require('./request');

class Application{
  constructor() {
    this.context = context;
    this.response = response;
    this.request = request;
  }
  use(fn){
    this.fn = fn;
  }
  createContext(req, res) {
    let context = Object.create(this.context);
    context.req = req;
    context.res = res;
    context.request = Object.create(this.request);
    context.response = Object.create(this.response);
    return context;
  }
  handleRequest(req, res) {
    let ctx = this.createContext(req, res);
    this.fn(ctx);
  }
  listen(...args) {
    let server = http.createServer(this.handleRequest.bind(this));
    server.listen(...args);
  }
}

module.exports = Application;
```

#### 增加url
现在来修改一下server.js文件，来尝试获取一下url:
```html
const Koa = require('./koa/application');

let app = new Koa();
app.use((ctx) => {
  console.log(ctx.req.url); // 原生
  console.log(ctx.request.req.url); // 原生
  console.log(ctx.request.url); // 自己的
  console.log(ctx.url); // 自己的
})

app.listen(2000);
```
上面四个在原生的Koa是全部能打印出来的, 而我们的只能获取到第一个，接着我们在创建上下文的时候，
将原生的方法，赋值给我们自己的方法，来支持第二个打印：
```html
  createContext(req, res) {
    let context = Object.create(this.context);
    context.request = Object.create(this.request);
    context.response = Object.create(this.response);
    context.req = context.request.req =  req;
    context.res = context.response.res =  res;
    return context;
  }
```
这样子第二个也能打印出来了。接下来我们来解决ctx.request.url，我们先回到request.js文件，
里面的url需要动态获取，我们使用属性访问器的方式，来帮助我们处理复杂逻辑。代码如下：
```html
// request.js
const request = {
  get url() { 
    return this.req.url; // this === ctx.request
  }
}

module.exports = request;
```
这样子取this.req.url时，取的就是ctx.request上的url,所以第三个也就可以了。
![/](./console1.png)

最后一个是最难的，我们取ctx.url,真正取的是ctx.request.url。这时候就可以做一个代理模式。
正好我们的context.js只做一件事：实现代理功能，代码如下：
```html
const context = {}

Object.defineProperty(context,'url' ,{
  get() {
    return this.request.url; // 这里的this指代的是自己创建的context
  }
})

module.exports = context;
```
#### 增加method
Koa源码是使用一个非标准且快废弃的属性[`__defineGetter__`](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Global_Objects/Object/__defineGetter__)，所以我改用了`Object.defineProperty`。
如果我们现在把server.js 里面的url换成method呢？是不是还得写一个defineProperty，
所以我们要把defineProperty封装一下：
```html
const context = {}
function defineGetter(property, key) {
  Object.defineProperty(context,key ,{
    get() {
      return this[property][key];
    }
  })
}

defineGetter('request', 'url');
defineGetter('request', 'method');

module.exports = context;
```
我们还得在自己的request.js上添加一个获取method的方法：
```html
const request = {
  get url() { 
    return this.req.url; // this === ctx.request
  },
  get method() {
    return this.req.method;
  }
}

module.exports = request;
```
这样就能打印出method。
![console2](./console2.png)

为什么不在request.js上也封装方法呢？ 因为它是拿来扩展的，比如我们要增加一个path：
```html
const url = require('url');
const request = {
  get url() { 
    return this.req.url; // this === ctx.request
  },
  get method() {
    return this.req.method;
  },
  get path(){
    return url.parse(this.req.url).pathname;
  }

}

module.exports = request;
```
然后在context.js里新增代码：
```html
defineGetter('request', 'path');
```
这样就给自己的request扩展了个方法。

### ctx.body
接下来设置一下body属性，先修改一下server.js代码：
```html
const Koa = require('./koa/application');

let app = new Koa();
app.use((ctx) => {
  ctx.response.body = 'hello';
  console.log(ctx.body); 
})

app.listen(2000);
```
ctx代理了response方法，所以ctx.body就是ctx.response.body。
接下来需要在response.js里给body设置get和set方法：
```html
const response = {
  _body:'',
  get body() {
    return this._body;
  },
  set body(newValue) {
    this._body = newValue;
  }
}

module.exports = response;
```
然后在context.js里，再增加一行代码：
```html
defineGetter('response', 'body');
```
这样就能打印出hello。

但是如果我们是赋值给ctx.body呢：
```html
app.use((ctx) => {
  ctx.body = 'hello';
  console.log(ctx.response.body); 
})
```
要实现这样的效果，我们要给ctx.body设置的时候，也得走到response里去，
编辑context.js，新增加个set,随便修改个方法名：
```html
const context = {}
function defineAgency(property, key) {
  Object.defineProperty(context, key, {
    get() {
      return this[property][key];
    },
    set(newValue) {
      this[property][key] = newValue;
    }
  })
}

defineAgency('request', 'url');
defineAgency('request', 'method');
defineAgency('request', 'path');
defineAgency('response', 'body');

module.exports = context;
```
这样就能在ctx.body上赋值了。

### 组合
app.use里，不仅有ctx,而且还有next，如果我们写了多个use,需要调一下next(),来执行下一个方法。
这里就是洋葱模型。在koa里有个compose方法，会将所有的方法组合成一个大的promise。

#### 洋葱模型
```html
const Koa = require('koa');

const app =  new Koa();

app.use((ctx,next) => {
  console.log(1);
  next();
  console.log(4);
});

app.use((ctx,next) => {
  console.log(2);
  next();
  console.log(5);
});

app.use((ctx,next) => {
  console.log(3);
  next();
  console.log(6);
});

app.listen(3000);
```
执行顺序就是
![洋葱模型](./ycmx.png)

#### 中间件
中间件可以理解为use方法，它可以决定是否向下执行。在执行异步的时候，可以使用async + await语法。

>写koa一定得在next前面加await要不就加return,不然它不会等待里面的函数执行完。


接下来我们的use就需要将方法存起来了，方便后期执行。然后在handleRequest方法，等所有promise执行完，
将结果返回去。代码如下：
```html
// application.js
const http = require('http');

const context = require('./context');
const response = require('./response');
const request = require('./request');

class Application{
  constructor() {
    this.context = context;
    this.response = response;
    this.request = request;
    this.middlewares = []; // +++++
  }
  use(fn){
    this.middlewares.push(fn);  // +++++
  }
  createContext(req, res) {
    let context = Object.create(this.context);
    context.request = Object.create(this.request);
    context.response = Object.create(this.response);
    context.req = context.request.req =  req;
    context.res = context.response.res =  res;
    return context;
  }
  handleRequest(req, res) {
    let ctx = this.createContext(req, res);
    this.compose(ctx).then(() => {      // +++++
      let _body = ctx.body;             // +++++
      res.end(_body);                   // +++++
    });                                 // +++++
  }
  listen(...args) {
    let server = http.createServer(this.handleRequest.bind(this));
    server.listen(...args);
  }
}

module.exports = Application;
```

### compose

这里面最主要的就是this.compose方法。它返回的就是一个promise。
我们先来修改一下server.js，让它来检测我们的compose:
```html
const Koa = require('./koa/application');

const app =  new Koa();

const my = () => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      console.log("my");
      resolve();
    }, 1000);
  });
};

app.use(async(ctx,next) => {
  console.log(1);
  await next();
  console.log(4);
});

app.use(async(ctx,next) => {
  console.log(2);
  await my();
  next();
  console.log(5);
});

app.use((ctx,next) => {
  console.log(3);
  next();
  console.log(6);
});

app.listen(3000);
```
先取出第一个函数，执行，然后派发给下一个函数，我们先直接写,不考虑promise。
```html
  compose(ctx) {
    function dispatch(index) {
     let middle =  this.middlewares[index];
     middle(ctx,()=> dispatch(index+1)); // 这个箭头函数指的就是下一个函数
    }
    return dispatch(0)
  }
```
现在有可能这个方法是一个普通函数。如果它不是个promise，我们也把他变成promise。
这样保证方法执行完，返回一个promise.并且我们再加上终止条件。如果终止了直接返回一个成功的promise。
```html
  compose(ctx) {
    let dispatch = (index) => {
      if (index == this.middlewares.length) return Promise.resolve();// 返回一个成功的Promise
      let middle = this.middlewares[index]; // 拿出第一个use 让其执行
      return Promise.resolve(middle(ctx, () => dispatch(index + 1))); //  执行的时候传递ctx,next方法
    }
    return dispatch(0);
  }
```
这样我们在server.js运行，就能看到跟源码一样的结果。核心逻辑只有3行。
但是我们的代码还不够健壮，我们接下来要防止next调用多次，造成代码顺序混乱。
然后再加上错误处理，并且将错误用事件抛出，代码如下：
```html
const http = require('http');
const EventEmitter = require('events');

const context = require('./context');
const response = require('./response');
const request = require('./request');

class Application extends EventEmitter {
  constructor() {
    super();
    this.context = context;
    this.response = response;
    this.request = request;
    this.middlewares = [];
  }
  use(fn) {
    this.middlewares.push(fn);
  }
  createContext(req, res) {
    let context = Object.create(this.context);
    context.request = Object.create(this.request);
    context.response = Object.create(this.response);
    context.req = context.request.req = req;
    context.res = context.response.res = res;
    return context;
  }
  compose(ctx) {
    let i = -1
    let dispatch = (index) => {
      if (index <= i) return Promise.reject(new Error('next() called multiple times'))
      i = index
      if (index == this.middlewares.length) return Promise.resolve();// 返回一个成功的Promise
      let middle = this.middlewares[index]; // 拿出第一个use 让其执行
     try {
      return Promise.resolve(middle(ctx, () => dispatch(index + 1))); //  执行的时候传递ctx,next方法
     } catch (err){
      return Promise.reject(err)
     }
    }
    return dispatch(0);
  }
  handleRequest(req, res) {
    let ctx = this.createContext(req, res);
    this.compose(ctx).then(() => {
      let _body = ctx.body;
      res.end(_body);
    }).catch(err => {
      this.emit('error', err);
    });
  }
  listen(...args) {
    let server = http.createServer(this.handleRequest.bind(this));
    server.listen(...args);
  }
}

module.exports = Application;
```
最后我们来让body支持一下对象,并且可以返回文件，它需要引入Stream模块。
```html
const http = require('http');
const EventEmitter = require('events');
let Stream = require('stream');

const context = require('./context');
const response = require('./response');
const request = require('./request');

class Application extends EventEmitter {
  constructor() {
    super();
    this.context = context;
    this.response = response;
    this.request = request;
    this.middlewares = [];
  }
  use(fn) {
    this.middlewares.push(fn);
  }
  createContext(req, res) {
    let context = Object.create(this.context);
    context.request = Object.create(this.request);
    context.response = Object.create(this.response);
    context.req = context.request.req = req;
    context.res = context.response.res = res;
    return context;
  }
  compose(ctx) {
    let i = -1
    let dispatch = (index) => {
      if (index <= i) return Promise.reject(new Error('next() called multiple times'))
      i = index
      if (index == this.middlewares.length) return Promise.resolve();// 返回一个成功的Promise
      let middle = this.middlewares[index]; // 拿出第一个use 让其执行
     try {
      return Promise.resolve(middle(ctx, () => dispatch(index + 1))); //  执行的时候传递ctx,next方法
     } catch (err){
      return Promise.reject(err)
     }
    }
    return dispatch(0);
  }
  handleRequest(req, res) {
    let ctx = this.createContext(req, res);
    this.compose(ctx).then(() => {
      let _body = ctx.body;
      if(_body instanceof Stream){
          return _body.pipe(res);
      }else if(typeof _body === 'object'){
          return res.end(JSON.stringify(_body));
      }else{
          return res.end(_body);
      }
    }).catch(err => {
      this.emit('error', err);
    });
  }
  listen(...args) {
    let server = http.createServer(this.handleRequest.bind(this));
    server.listen(...args);
  }
}

module.exports = Application;
```
这样我们就实现了koa 90%的方法了。

### 结束语
怪来一夜蛙声歇，又作东风十日寒。
「绝句」
吴涛