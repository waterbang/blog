---
title:  手写Mini Vue-Router && Mini Vuex
date: 2019-12-10 19:52:08
tags:   VUE
index_img:  /2019/12/10/2019-12-10-VUE-vuex-vue-router源码实现/routes1.png
---

#### 初始化项目 🏃
首先用vue-cli初始化我们的项目，分别选择

    ? Please pick a preset: Manually select features
    ? Check the features needed for your project: Babel, Router, Vuex, Linter
    ? Use history mode for router? (Requires proper server setup for index fallback in production) No
    ? Pick a linter / formatter config: Airbnb
    ? Pick additional lint features: Lint on save, Lint and fix on commit
    ? Where do you prefer placing config for Babel, ESLint, etc.? In dedicated config files
    ? Save this as a preset for future projects? No

<br>

在`.eslintrc.js`里添加规则，

      rules: {
        'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
        'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
        'no-sequences': 0,
        'no-param-reassign': 0,
        'implicit-arrow-linebreak': 0,
        'no-return-assign': 0,
        'no-underscore-dangle': 0,
        'no-restricted-globals': 0,
        'no-unused-expressions': 0,
        'no-unused-vars': 0,
      },

## Vue-router 🍭
首先我们将 `/router/index.js` 文件里的vue-router 改写成我们的,/vue-router

    //   /src/router/index.js
    import Vue from 'vue';
    import VueRouter from './vue-router';//改成自己的
    import Home from '../views/Home.vue';
    import About from '../views/About.vue';
    
    Vue.use(VueRouter);

<br>

### 初始化自己的vue-router 🎨
第一步`Vue.use(VueRouter)`,默认调用了install方法，并传入了一个vue的构造函数。
 可以用来扩展属性或者组件或者指令。   
    
    //   /src/router/vue-router.js
    let Vue;// 存起来
    class Router {
    };
    Router.install = (_Vue) => {
      Vue = _Vue; 
    };
    export default Router;
    
第二步，我们的根组件里面会传一个`router`,让子组件都可以拿到这个`router`。
    
    //  /main.js
    new Vue({
      router,
      store,
      render: h => h(App),
    }).$mount('#app');
    
我们可以直接这样写
    
    Vue.prototype.router = xxxx;
    
但是这样在每次`new Vue` 的时候都会带上router，我们希望在根组件以下才有。所以我们使用`Vue.mixin`,
它内部会把这个对象给每个属性，混合在一起。它内部就是将组件的生命周期做个数组，它会把mixin的方法放在前面，
组件的方法放在后面，像这样 `[beforeCreate,befoureCrate]`,执行的时候，循环。
    
     //   /src/router/vue-router.js
    Router.install = (_Vue) => {
      Vue = _Vue;
      Vue.mixin({
        beforeCreate() { // 组件创建之前，走这方法
          if(this.$options.router){ //  判断根组件是谁
          }
        },
      })
    };
    
这个`$options`,指的是`new Vue`传的内容，也就是下面代码的3，4，5行。

    //  /main.js
    new Vue({
      router,
      store,
      render: h => h(App),
    }).$mount('#app');
    
<br>

#### 完善mixin 🏋️‍♂️
让根组件下都有这个`router`。

``` javascript
//  /src/router/vue-router.js
Router.install = (_Vue) => {
  Vue = _Vue;
  Vue.mixin({
    beforeCreate() { // 组件创建之前，走这方法
      if (this.$options && this.$options.router) { //看看是不是根组件
        this.router = this.$options.router;
      } else { //  如果不是父亲就是儿子
        //  让所有的子组件都有router属性，指向当前 router
        this.router = this.$parent && this.$parent.router;
      }
    },
  });
};```

<br>


### 添加$route $router router-link router-view 🍕
每个组件都有 `$route` `$router` 我们接下来来添加它们，并注册一下两个组件

```javascript
//  /src/router/vue-router.js
let Vue;// 存起来
class Router {
}

Router.install = (_Vue) => {
  Vue = _Vue;
  Vue.mixin({
    beforeCreate() { // 组件创建之前，走这方法
      //  判断根组件是谁
      if (this.$options && this.$options.router) {
        this.router = this.$options.router;
      } else { //  如果不是父亲就是儿子
        //  让所有的子组件都有router属性，指向当前 router
        this.router = this.$parent && this.$parent.router;
      }
        //  $route $router
      Object.defineProperty(this, '$route', {
        value: {},
      });
      Object.defineProperty(this, '$router', {
        value: {},
      });
    },
  });
 // router-link router-view
      Vue.component('router-link', {
        render() {
          return null;
        },
      });
      Vue.component('router-view', {
        render() {
          return null;
        },
      });
};
export default Router;
```


#### 完善 router-link 🍔
第一步，我们完善`to`。（~~我们也就一步~~）

    <!-- 字符串 -->
    <router-link to="home">Home</router-link>
    

像这样
```javascript
//  /src/router/vue-router.js
Vue.component('router-link', {
props: {
  to: String,
},
render() {
  return <a href={`#${this.to}`}>{this.$slots.default}</a>;
},
});
```

### 接收路由，渲染组件 🚄
我们在`/src/router/index.js`里，有个路由表，并在`new VueRouter`的时候传了进去，
接下来我们在VueRouter的构造函数里接收一下，并将它格式化为这样的格式：
<div align=center>
`{'/': Home, '/about':'xxx'}`
</div>
这样我切谁，就将对于的组件渲染上去。


我们的routes长这样。
```javascript
//  /src/router/index.js
const routes = [ // {'/': Home, '/about':'xxx'}
  {
    path: '/',
    name: 'home',
    component: Home,
  },
  {
    path: '/about',
    name: 'about',
    component: About,
  },
];
```


我们在构造函数里接收，并格式化`routes`。
    
    //  /src/router/vue-router.js
    class Router {
      constructor({ routes }) {
        this.routeMap = routes.reduce((memo, current) =>
        (memo[current.path] = current.component, memo), {});
        console.log(this.routeMap);
      }
    }

上面的意思是：将值取出来（current）,将path赋给当前的memo，值为current.component。
打印后长这样
![router1](./routes1.png)


#### 渲染组件到 router-view 🚅
我们先将路由固定为`home`页面

     //  /src/router/vue-router.js
        class Router {
          constructor({ routes }) {
            this.routeMap = routes.reduce((memo, current) =>
            (memo[current.path] = current.component, memo), {});
            this.route = { current: '/' };   // 增加了这行
          }
        }

然后修改`router-view`来渲染。
    
      Vue.component('router-view', {
        render(h) { //  这个this是个代理对象
          return h(this.router.routeMap[this.router.route.current]);
        },
      });

#### 监听几个事件 🚈
监听`load`事件。（组件加载完会执行），先看看当前组件有没有hash.

>路由分为两种：一种是hash的`#` ，另一种是h5的API `/` .
>hash不利已SEO优化，但是比较容易。

监听`hashchange`事件，在改变的时候将路由改掉。

    //  /src/router/vue-router.js
    class Router {
      constructor({ routes }) {
        this.routeMap = routes.reduce((memo, current) =>
          (memo[current.path] = current.component, memo), {});
        this.route = { current: '/ };
        window.addEventListener('load', () => {
          location.hash ? '' : location.hash = '/';
        });
        window.addEventListener('hashchange', () => {
          this.route.current = location.hash.slice(1);
        });
      }
    }

但是我们的this.route.current并不是一个响应式数据，改了值以后视图不会刷新。
**如何将不是响应式的数据变成响应式数据呢？**

     Vue.util.defineReactive(this, 'route', { current: '/' });

上面代码的意思：就是给这个人（`this`）,定义一个这样的数据（`route`），值是（`{ current: '/' }`） ；


接下来我们来写 `mini vuex`;

## Store 👳‍♀️

store的模式跟router的套路一样。它 new 了一个 `Vuex.Store`导出后，放到`/main.js`里面来，
然后放到它的实例里面。让每个人都有this.$store。
让我们来写出我们的套路,（也是~~写插件~~的套路），新建`/src/store/vuex.js`,代码如下：
    
    //  /src/store/vuex.js
    let Vue;
    class Store {
    }
    const install = (_Vue) => {
      Vue = _Vue;
    };
    export default {
      Store,
      install,
    };

接下来我们需要接收一下new传进来的参数，并且给组件注入一个$store。
    
    //  /src/store/vuex.js
    let Vue;
    class Store {
      constructor(options) {
      }
    }
    const install = (_Vue) => {
      Vue = _Vue;
      Vue.mixin({
        beforeCreate() {
          if (this.$options && this.$options.store) {
            this.$store = this.$options.store;
          } else {
            this.$store = this.$parent && this.$parent.$store;
          }
        },
      })
    };
    export default {
      Store,
      install,
    };



### 开始共享我们的数据 👲
我们先在`/src/store/index.js`,放个值。

     state: {
        name: 'waterbang'
      },

然后在`/src/store/index.js`,接收：

    constructor(options) {
        this.state = options.state;
     }

这样我们就可以共享数据，并在组件内使用` {{this.$store.state}}`取到数据了。

### 接着修改我们的数据 🧔
第一步，先在`/src/store/index.js`,里定义`mutations`里的函数:
    
     mutations: {
        setUsername(state) {
          state.name = 'water';
        },
      },
      
第二步，在`App.vue`里，定义`commit`：

      mounted() {
        this.$store.commit('setUsername');
      },
      
第三步，由于commit是$store里的方法，我们接下来在我们的`vuex`里面来新建这个方法：

    // /src/store/vuex.js
    class Store {
      constructor(options) {
        this.state = options.state;
        this.mutations = options.mutations; // 取出mutations
      }
    
      commit = (eventName) => {
        this.mutations[eventName](this.state); //   匹配对应的函数，并执行
      }
    }
    
但是，问题来了，到现在为止，我们刷新，视图还是不会变，这是因为我们的数据是直接传进来的,并不是响应式数据。


我们可以采用 `new Vue` 创建一个实例来解决，将状态变成响应式的，如果数据更新，则视图刷新。
如果想要深入了解响应式原理看这位大佬写的[Vue原理解析（六）：全面深入理解响应式原理(上)-对象基础篇](https://juejin.im/post/5d4ad8686fb9a06b2766b625)。
    
     // /src/store/vuex.js
    class Store {
      constructor(options) {
        this.vm = new Vue({
          data: { state: options.state },
        });
        this.state = this.vm.state;
        this.mutations = options.mutations;
      }
    
      commit = (eventName) => {
        this.mutations[eventName](this.state);
      }
    }
    
这样就实现了基本的`mutations`。

#### actions 🎅
接下来轮到了`actions`。

第一步先来增加一下`actions`里的方法。
    
    actions: {
        setUsername({ commit }) {
          setTimeout(() => {
            commit('setUsername');
          }, 1000);
        },
      },
      
然后到App.vue里修改一下内容。

     mounted() {
        this.$store.dispatch('setUsername');
      },

最后我们到`/src/store/vuex.js`，里增加我们的`dispatch`方法。

    class Store {
      constructor(options) {
        this.vm = new Vue({
          data: { state: options.state },
        });
        this.state = this.vm.state;
        this.mutations = options.mutations;
        this.actions = options.actions;
      }
    
      commit = (eventName) => {
        this.mutations[eventName](this.state);
      }
    
      dispatch = (eventName) => {
        this.actions[eventName](this); //这里的this是当前的Store
      }
    }
    
然后我们的`actions`完成了,刷新后过一秒更新数据。

## 结束语 🏐
花雾萦风缥缈，歌珠滴水清圆。「西江月·别梦已随流水」——苏轼。