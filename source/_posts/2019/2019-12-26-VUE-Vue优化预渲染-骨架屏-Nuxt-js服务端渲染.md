---
title: 'Vue优化预渲染,骨架屏,Nuxt.js服务端渲染'
date: 2019-12-26 12:50:14
tags: VUE
index_img: /2019/12/26/2019-12-26-VUE-Vue优化预渲染-骨架屏-Nuxt-js服务端渲染/nuxt-emoji.png
---

## 1.   编码优化🍞

### 1.data属性
data中的数据都会增加getter和setter，会收集对应的watcher，只有在需要渲染到视图上的才需要放到data，所以没有响应式需求的不要放在data里面。
defineReactive源码
```javascript
//在Object上定义反应属性。
function defineReactive (
  obj,
  key,
  val,
  customSetter,
  shallow
) {
  var dep = new Dep(); 

  var property = Object.getOwnPropertyDescriptor(obj, key);
  if (property && property.configurable === false) {
    return
  }
  var getter = property && property.get;
  if (!getter && arguments.length === 2) {
    val = obj[key];
  }
  var setter = property && property.set;

  var childOb = !shallow && observe(val);
  Object.defineProperty(obj, key, {
    enumerable: true,
    configurable: true,
    get: function reactiveGetter () { 
      var value = getter ? getter.call(obj) : val;
      if (Dep.target) { //把watcher放到target里
        dep.depend();  //依赖搜集
        if (childOb) { //如果有子集
          childOb.dep.depend(); //也塞进去，目的是兼容数组。
          if (Array.isArray(value)) {
            dependArray(value);
          }
        }
      }
      return value
    },
    set: function reactiveSetter (newVal) { //每次更新的时候
      var value = getter ? getter.call(obj) : val;
      /* eslint-disable no-self-compare */
      if (newVal === value || (newVal !== newVal && value !== value)) {
        return
      }
      /* eslint-enable no-self-compare */
      if (process.env.NODE_ENV !== 'production' && customSetter) {
        customSetter();
      }
      if (setter) {
        setter.call(obj, newVal);
      } else {
        val = newVal;
      }
      childOb = !shallow && observe(newVal);
      dep.notify(); //通知watcher去更新，执行watcher的update
    }
  });
}
```

### 2.SPA页面采用keep-alive缓存组件
keep-alive会缓存我们的组件，它会把组件缓存到内存中，下一次访问的时候，会从缓存中拿出来。
keep-alive是个函数式组件，里面有个render()方法。他会把默认的插槽拿出来，找到第一个组件(里面只能放一个组件)。
拿到后先去判断是否有include和exclude，这两个是判断缓存哪一些，不缓存哪一些。

```html
render () {
    const slot = this.$slots.default
    const vnode: VNode = getFirstComponentChild(slot)  // 获取第一个组件节点
    const componentOptions: ?VNodeComponentOptions = vnode && vnode.componentOptions
    if (componentOptions) {
      // check pattern
      const name: ?string = getComponentName(componentOptions)
      const { include, exclude } = this
      if (
        // not included
        (include && (!name || !matches(include, name))) ||
        // excluded
        (exclude && name && matches(exclude, name))
      ) {
        return vnode
      }

      // 缓存vnode
      const { cache, keys } = this
      const key: ?string = vnode.key == null
        // same constructor may get registered as different local components
        // so cid alone is not enough (#3269)
        ? componentOptions.Ctor.cid + (componentOptions.tag ? `::${componentOptions.tag}` : '')
        : vnode.key
      if (cache[key]) { //如果有缓存，直接将缓存返回
        vnode.componentInstance = cache[key].componentInstance
        // make current key freshest
        remove(keys, key)
        keys.push(key)
      } else {
        cache[key] = vnode //缓存下来下次用
        keys.push(key)
        // 超过缓存限制，就从第一个开始删除
        if (this.max && keys.length > parseInt(this.max)) {
          pruneCacheEntry(cache, keys[0], keys, this._vnode)
        }
      }

      vnode.data.keepAlive = true
    }
    return vnode || (slot && slot[0])
  }
}
```

### 3.拆分组件
不拆分和拆分有什么区别呢？
vue有个特点，它是按组件刷新的。数据一变，就会刷新当前组件，如果都写到一起了，如果数据一变，整个组件都要刷新。
拆分之后，一个组件的数据变了，可以只更新那个小组件。核心就是：**减少不必要的渲染（尽可能细化拆分组件）**
还有就是**提高复用性，增加代码可维护性**。

### 4.v-if
当前值为false时内部指令不会执行，具有阻断功能。比如说面板，弹框，里面包含很多逻辑，用户不点我们可以使里面先不执行。

### 5.key保证唯一性
·   vue默认采用就地复用原则，可以加key保证唯一性

```html
<template>
  <div id="app">
    <div id="nav">
      <button @click="show =! show">按钮</button>
      <input type="text" v-if="show" :key="1">
      <input type="password" v-else  :key="2">
    </div>
  </div>
</template>
<script>
export default {
  data() {
    return {
      show: true,
    };
  },
};
</script>
```
·   如果数据项的顺序被改变，Vue不会移动DOM元素来匹配数据项的顺序。它默认会比对内容，如果内容有变，就会多次去创建DOM，删除DOM。
这样的性能消耗更大，所以我们如果写循环代码，尽量用唯一的key来实现。这里面主要是DOM Diff的策略。

·   应该使用数据的id作为key的属性。

### 6.Object.freeze
vue会实现数据劫持，给每个数据增加getter和setter,如果希望数据只是用来展示到页面上而已，并不需要改数据视图会刷新。
这样的话，就可以用Object.freeze冻结数据。

```html
Object.freeze([{value: 1},{value: 2}])
```

在数据劫持时，属性不会被配置，不会从新定义
```html
const property = Object.getOwnPropertyDescriptor(obj, key)
if (property && property.configurable === false) {
return
}
```


深冻结
```html
// 深冻结函数.
function deepFreeze(obj) {
  // 取回定义在obj上的属性名
  var propNames = Object.getOwnPropertyNames(obj);
  // 在冻结自身之前冻结属性
  propNames.forEach(function(name) {
    var prop = obj[name];
    // 如果prop是个对象，冻结它
    if (typeof prop == 'object' && prop !== null)
      deepFreeze(prop);
  });
  // 冻结自身(no-op if already frozen)
  return Object.freeze(obj);
}
```

### 7.路由懒加载，异步组件
动态加载组件，依赖`webpack-codespliting`功能，不能单独去用，它会拆分这个路由。
比如：当我们这个路由匹配到了，它会调用这个函数将路由动态加载上去。
webpack如果遇到import语法，会单独打包出js文件，加载的时候使用`JSONP`的语法，动态加载上去。
```html
 const router = new VueRouter({
    router: [
        {path: '/footer',component: () => import(/* webpackChunkName: "footer" */ '../views/Footer.vue'),},
        {path: '/about',component: () => import(/* webpackChunkName: "about" */ '../views/About.vue'),},
    ]
})
```

动态导入组件，如果我们有一个组件特别复杂，希望用户点了这个按钮，它才弹出来，这时候就可以使用异步组件。
它返回的是一个Promise，它会等待这个组件渲染完成再去显示。
```html
import Search from "./Search";
export default {
    components: {
        Search: () => import("./Search");
    }
};
```
>注意
>
>如果您使用的是 Babel，你将需要添加 [syntax-dynamic-import](https://babeljs.io/docs/en/babel-plugin-syntax-dynamic-import/) 插件，才能使 Babel 可以正确地解析语法。


但是这里有个坑，不能直接传入一个变量，下面是概要，具体看[官方文档](https://webpack.js.org/api/module-methods/#import)
>无法使用完全动态的import语句，例如import(foo)。因为foo可能是系统或项目中任何文件的任何路径。这样把全部文件打包了是会报错的。

我们还可以使用webpackInclude和webpackExclude选项，来减少webpack导入的文件数量，他们接受一个正则表达式。
webpackInclude和webpackExclude选项不会干扰前缀。例如：./locale。

`webpackInclude`：在导入解析期间将与之匹配的正则表达式。仅将匹配的模块捆绑在一起。

`webpackExclude`：在导入解析期间将与之匹配的正则表达式。匹配的任何模块都不会捆绑在一起。
```html
//官方文档中的例子
import(
  /* webpackInclude: /\.json$/ */
  /* webpackExclude: /\.noimport\.json$/ */
  `./locale/${language}`
);
```
 
 ### 8.runtime运行时
在开发时尽量采用单文件的方式（.vue），他不需要我们运行时去编译template。
 webpack打包时会将模板进行编译([vue-template-compiler](https://www.npmjs.com/package/vue-template-compiler))
 但是如果使用new Vue({template}),里面的template是在代码运行的时候去编译模板，对性能有损耗。
 
 ### 9.数据持久化问题
 可以使用`vuex-persist`进行数据持久化，因为我们vue里的数据，一刷新就会丢，所以我们要把数据存到localStorage里。
 但是如果频繁的对localStorage进行操作，对性能的损耗也很大，`vuex-persist`提供了一个过滤功能来解决这个问题，您可以过滤掉不想引起存储更新的任何改变。
 第二个方法是进行节流。
 >vuex-persist具体用法看其的[GitHub文档](https://github.com/championswimmer/vuex-persist)；
 >window.localStorage（在PC重新启动后仍然存在，直到您清除浏览器数据为止）
 window.sessionStorage（关闭浏览器选项卡时消失）


## 2.   vue加载性能优化 🌓
1.  第三方模块按需引入，如element-ui。也可以使用babel-plugin-component按需加载组件。
>[babel-plugin-component](https://juejin.im/post/5b35c49bf265da598f156446)用法和[npm官方文档](https://www.npmjs.com/package/babel-plugin-component)

2.  图片懒加载，滚动到可视区域动态加载。比如像[vue-lazyload](https://www.npmjs.com/package/vue-lazyload);

3.  滚动渲染可视区域，数据较大时只渲染可视区域，如果一次性渲染太多的节点，可能会挂掉或者卡顿。
>具体用法看[再谈前端虚拟列表的实现](https://zhuanlan.zhihu.com/p/34585166)
>也有现成的插件可以使用[vue-scroll](https://www.npmjs.com/package/vue-scroll)。


## 3.   用户体验👍

### 1.  app-skeleton
配置webpack插件 [vue-skeleton-webpack-plugin](https://www.npmjs.com/package/vue-skeleton-webpack-plugin)
单页骨架屏
```html
import Vue from 'vue'
// 引入的骨架屏组件
import skeletonHome from './skeleton/skeletonHome.vue'
export default new Vue({
    components: {
        skeletonHome,
    },
    template: `<skeletonHome/> `
});
plugins: [
    new SkeletonWebpackPlugin({ // 我们编写的插件
        webpackConfig: {
            entry: {
                app: require('./src/entry-skeleton.js')
            }
        }
    })
]
```

带路由的骨架屏，编写skeleton.js文件

```html
import Vue from 'vue';
import Skeleton1 from './Skeleton1';
import Skeleton2 from './Skeleton2';

export default new Vue({
    components: {
        Skeleton1,
        Skeleton2
    },
    template: `
        <div>
            <skeleton1 id="skeleton1" style="display:none"/>
            <skeleton2 id="skeleton2" style="display:none"/>
        </div>
    `
});
```
configureWebpack里的配置
```html
new SkeletonWebpackPlugin({
    webpackConfig: {
        entry: {
            app: path.join(__dirname, './src/skeleton.js'),
        },
    },
    router: {
        mode: 'history',
        routes: [
            {
                path: '/',
                skeletonId: 'skeleton1'
            },
            {
                path: '/about',
                skeletonId: 'skeleton2'
            },
        ]
    },
    minimize: true,
    quiet: true,
})
```
#### 具体用法
先来创建一个单页的骨架屏
##### 1. 先在根目录创建一个vue.config.js
粘贴下面代码
```html
let SkeletonWebpackPlugin = require('vue-skeleton-webpack-plugin');
const path = require('path');
module.exports = {
  configureWebpack:{
    plugins:[
      new SkeletonWebpackPlugin({ 
          webpackConfig: {
              entry: {
                  app: path.resolve('./src/entry-skeleton.js')
              }
          }
      })
  ]
  }
}

```
##### 2. 创建./src/entry-skeleton.js
放上我们的骨架屏
```html
import Vue from 'vue';

export default new Vue({
  render() {
    return <h1>hello Vue</h1>;
  },
});
```
##### 这样就ok啦
用npm run serve 试试！

>参考
>[为vue项目添加骨架屏](https://xiaoiver.github.io/coding/2017/07/30/%E4%B8%BAvue%E9%A1%B9%E7%9B%AE%E6%B7%BB%E5%8A%A0%E9%AA%A8%E6%9E%B6%E5%B1%8F.html)
>[基于 vue-skeleton-webpack-plugin 的骨架屏实战](https://juejin.im/post/5d457bad5188255d8249c7f4)


#### 姜文大佬实现的原理
实现骨架屏插件
```html
class MyPlugin {
    apply(compiler) {
        compiler.plugin('compilation', (compilation) => {
            compilation.plugin(
                'html-webpack-plugin-before-html-processing',
                (data) => {
                    data.html = data.html.replace(`<div id="app"></div>`, `
                        <div id="app">
                            <div id="home" style="display:none">首页 骨架屏</div>
                            <div id="about" style="display:none">about页面骨架屏</div>
                        </div>
                        <script>
                            if(window.hash == '#/about' ||  location.pathname=='/about'){
                                document.getElementById('about').style.display="block"
                            }else{
                                document.getElementById('home').style.display="block"
                            }
                        </script>
                    `);
                    return data;
                }
            )
        });
    }
}
```

### 2.  app-shell
一般配合PWA使用,百度的[Lavas](https://lavas.baidu.com/pwa)。
使用serviceWorker，第一次加载，第二次到本地。

## 4.   SEO优化方案 🏃

### 1.vue的预渲染插件
`npm install prerender-spa-lpugin`

缺陷是数据不够动态，可以使用ssr服务端渲染
```html
const path = require('path')
const PrerenderSPAPlugin = require('prerender-spa-plugin')

module.exports = {
  plugins: [
    ...
    new PrerenderSPAPlugin({
      // Required - The path to the webpack-outputted app to prerender.
      staticDir: path.join(__dirname, 'dist'),
      // Required - Routes to render.
      routes: [ '/', '/about', '/some/deep/nested/route' ],
    })
  ]
}
```
里面主要用到一个包是puppeteer，他是一个无头浏览器，运行它会打开一个浏览器，但是你看不见它，
它会先将页面放在浏览器上去跑，然后生成节点，渲染成HTML,一般用作e2e,或爬虫。

### 2.  服务端渲染
概念：放在浏览器进行就是浏览器渲染，放在服务器进行就是服务器渲染。就跟以前的模板渲染一样。

客户端渲染不利于SEO搜索引擎优化
服务端渲染是可以被爬虫抓取到的，客户端异步渲染是很难被爬虫抓取到的
SSR直接将HTML轴向传递给浏览器。大大加快了首屏加载时间。
SSR占用更多的CPU和内存资源
一些常用的浏览器API可能无法正常使用
在vue中只支持beforeCreate和created两个生命周期

### 3. 什么是nuxt
Nuxt.js是使用Webpack和Node.js进行封装的基于Vue的SSR框架

#### nuxt特点
优点：
更好的SEO，由于搜索引擎爬虫抓取工具可以直接查看完全渲染的页面。首屏渲染速度快

缺点：
Node.js中渲染完整的应用程序，显然只比提供静态文件的服务器更多占用CPU资源。需要考虑服务器负载，缓存策略

具体查看[nuxt.js官方文档](https://zh.nuxtjs.org/guide/installation)

### 4.  webpack打包优化

1.  使用cdn方式加载第三方模块，设置[externals](https://webpack.docschina.org/configuration/externals/).

例如，从 CDN 引入 jQuery，而不是把它打包：
index.html
```html
<script
  src="https://code.jquery.com/jquery-3.1.0.js"
  integrity="sha256-slogkvB1K3VOkzAI8QITxV3VzpOnkeNVsKvtkYLMjfk="
  crossorigin="anonymous">
</script>
```
webpack.config.js
```html
module.exports = {
  //...
  externals: {
    jquery: 'jQuery'
  }
}
```

2.  多线程打包`happypack`
具体查看这篇文章[使用 happypack 提升 Webpack 项目构建速度](https://juejin.im/post/5c6e0c3a518825621f2a6f45)

3.  splitChunks抽离公共文件

4.  sourceMap的配置
>webpack性能优化具体看[webpack各种优化](https://www.waterbang.top/2019/11/24/2019-11-24-webpack-webpack%E5%90%84%E7%A7%8D%E4%BC%98%E5%8C%96/)
>webpack-bundle-analyzer 分析打包插件


### 5.  服务端缓存，客户端缓存
##6.   服务端gzip压缩
可以减小文件体积，传输速度更快。gzip是节省带宽和加快站点速度的有效方法。
具体查看[「简明性能优化」双端开启Gzip指南](https://juejin.im/post/5cb7ee0e51882532fe3440ea)

## 结束语 🏐
人悄悄，帘外月胧明。「小重山·昨夜寒蛩不住鸣」——岳飞
