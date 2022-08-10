---
title: TypeScript-使用typescript构建vue应用
date: 2019-11-25 15:17:57
tags:   typescript
index_img: 
---

### 砍柴先磨刀 🎄

我们使用VSCode来进行编码，首先我们要安装`TSLint`和`TSLint Vue`来规范和校验我们的编码。（代码质量第一位）
(*这两个家伙会经常发生失灵的情况*)

#### 配置TSLint

1.  打开 File->Preferences->Settings

2.  搜索TSLint

3.  打开Settings.json

3.  将下面代码复制进去


            //setting.json
          { 
           "editor.codeActionsOnSave": {
                "source.fixAll.tslint": true
            },
          }

4.  我是关闭vsCode然后再打开生效的。

#### 创建类的Vue模板

1.  点击File->Preferences->User Snippets 

2.  然后点击 New Snippets 新建文件 `vuets-code-snippet.json.code-snippets`

<img src="./snippets.png" >

3.  将下列模板复制进去
    
    
    //vuets-code-snippet.json.code-snippets
    {
        "Print to console": {
            "prefix": "vuets",
            "body": [
                "<template>",
                "",
                "</template>",
                "<script lang='ts'>",
                "import { Component, Vue, Prop } from 'vue-property-decorator';",
                "import  from '@/components/ .vue'",
                "@Component({",
                "    components: {",
                "        ",
                "    }",
                "})",
                "export default class componentName extends Vue {",
                "    @Prop(type)private propName = propValue;",
                "    private variableName: typeName = variableValue;",
                "    public methodName() {",
                "        ",
                "    }",
                "}",
                "</script>",
                "<style lang='less' scoped >",
                "",
                "</style>"
            ],
            "description": "basic vue typescript template"
        }
    }
    
    
4.  然后在.vue文件就可以打出`vuets` 加`Tab` 就可以生成模板啦。


### 使用vue-cli创建项目
 
 选择typescript,其他按照需求来
 
      (*) Babel
      (*) TypeScript
      ( ) Progressive Web App (PWA) Support
      (*) Router
      (*) Vuex
      (*) CSS Pre-processors
      (*) Linter / Formatter
      ( ) Unit Testing
      ( ) E2E Testing


#### 献上代码规范

直接复制下面代码粘贴到你的`tslint.json`就可以了，然后想深入了解可以看[官方tslint.json设置篇](https://ts.xcatliu.com/engineering/lint)
    
    {
      "defaultSeverity": "warning",
      "extends": [
          "tslint:recommended"
      ],
      "linterOptions": {
          "exclude": [
              "node_modules/**"
          ]
      },
      "no-trailing-whitespace": false,
      "rules": {
          "quotemark": false,
          "indent": [true, "spaces", 4],
          "interface-name": false,
          "ordered-imports": false,
          "object-literal-sort-keys": false,
          "no-console": false,
          "no-debugger": false,
         
          "no-unused-expression": [true, "allow-fast-null-checks"], 
          "no-unused-variable": false, 
          "triple-equals": true,
          "no-parameter-reassignment": true,
          "no-conditional-assignment": true,
          "no-construct": true, 
          "no-duplicate-super": true, 
          "no-duplicate-switch-case": true,
          "no-object-literal-type-assertion": true, 
          "no-return-await": true, 
          "no-sparse-arrays": true, 
          "no-string-throw": true,
          "no-switch-case-fall-through": true, 
          "prefer-object-spread": true, 
          "radix": true, 
          "cyclomatic-complexity": [
              true,
              20
          ], 
          "deprecation": true, 
          "use-isnan": true, 
          "no-duplicate-imports": true, 
          "no-mergeable-namespace": true, 
          "encoding": true, 
          "import-spacing": true,
          "interface-over-type-literal": true,
          "new-parens": true,
          "no-angle-bracket-type-assertion": true, 
          "no-consecutive-blank-lines": [
              true,
              3
          ]  
        }
    }


### 我们来实现todoItem


#### 抽离接口文件

接口是可以导出的，我们将接口抽离出来
在src目录下新建types文件夹，新建todo.ts文件，内容如下

        
    export interface ITodo {
        text: string;
        complete: boolean;
    }



####  创建基础文件

我们可以先了解：[Vue属性装饰器](https://www.npmjs.com/package/vue-property-decorator),让我们更快的编码。
 >@Prop
  @PropSync
  @Model
  @Watch
  @Provide
  @Inject
  @ProvideReactive
  @InjectReactive
  @Emit
  @Ref
  @Component（由 vue-class-component提供）
  Mixins（mixins 由 vue-class-component 提供的名为helper的函数）

##### Home.vue应该像这样

    /src/views/Home.vue
    <template>
      <div>
        <ul>
          <li v-for="(item,index) in lists" :key="index">
            <TodoItem :item="item" :index="index" @say="say"></TodoItem>
          </li>
        </ul>
      </div>
    </template>
    <script lang='ts'>
    import { Component, Vue } from "vue-property-decorator";
    import TodoItem from "../components/TodoItem";
    import { ITodo } from "../types/todo";
    
    @Component({
      components: {
        TodoItem,
      },
    })
    export default class Home extends Vue {
      public lists: ITodo[] = [
        { text: "打代码" },
        { text: "睡觉" },
      ];
    
      get count() {
        return this.lists.length;
      }
      public say(): void {
        console.log("你在干啥");
      }
    }
    </script>
    }

我们先来看一下@Component里面是什么东西

    import Vue, { ComponentOptions } from 'vue';
    import { VueClass } from './declarations';
    export { createDecorator, VueDecorator, mixins } from './util';
    declare function Component<V extends Vue>(options: ComponentOptions<V> & ThisType<V>): <VC extends VueClass<V>>(target: VC) => VC;
    declare namespace Component {   //外部命名空间声明
        var registerHooks: (keys: string[]) => void;
    }
    declare function Component<VC extends VueClass<Vue>>(target: VC): VC;
    declare namespace Component {
        var registerHooks: (keys: string[]) => void;
    }
    export default Component;  //这里我们看得懂


他给我们吐出了一个Component，所以他其实干了这样事

    export default {
        component:{},
        props: {},
        watch: { }
    }


##### 在 /components里新建TodoItem.tsx

内容如下
    
        /components/TodoItem.tsx
     import { Component, Vue, Prop } from 'vue-property-decorator';
     import { ITodo } from '../types/todo';
     
     @Component
     export default class TodoItem extends Vue {
         @Prop(Object) public item !: ITodo;  //属性传递的方法
         @Prop(Number) public index !: number;
         public save() {
             this.$emit('say');
         }
         public render() {
             return <h1>{this.item.text}<button on-click={this.save}>触发方法</button></h1>;
         }
     }


让我们来认识一下这个语法糖

    //原来的写法
    props: {
        item: {
            type: ITodo,
            defalut: ''
        }
    }
    
    //语法糖的写法
    @Prop(Object) public item !: ITodo;  //属性传递的方法

加`！`的意思是如果是空的，就不校验，代表这个值一定有。


##### @Emit语法糖

以上代码实现父向子传递数据，和子触发父方法。
但是这样写不够好看，官方给我们提供了一个更加美观的装饰器(`Emit`)。将TodoItem.tsx内容改写如下
    
    /src/components/TodoItem.tsx
    import { Component, Vue, Prop, Emit } from 'vue-property-decorator';
    import { ITodo } from '../types/todo';
    
    @Component
    export default class TodoItem extends Vue {
        @Prop(Object) public item !: ITodo;
        @Prop(Number) public index !: number;
        @Emit('say') //我要触发的是父亲的方法
        public save() {
             return "hello";
        }
        public render() {
            return <h1>{this.item.text}<button on-click={this.save}>触发方法</button></h1>;
        }
    }

` @Emit('say')`传入的是父亲的方法，但是如果父亲的方法和要装饰的方法名称相同，里面的内容可以不传` @Emit()`

那传参怎么传呢？ 我们现在已经return出了一个`hello`，现在只需要改写一下父亲的方法

    public say(msg: string): void {
        console.log(msg);
      }

这样就能接收到数据。


#### 实现点击加1的操作
    
    /src/components/TodoItem.tsx
    import { Component, Vue, Prop, Emit } from 'vue-property-decorator';
    import { ITodo } from '../types/todo';
    
    @Component
    export default class TodoItem extends Vue {
        public count: number = 1;  //声明常量方法
        @Prop(Object) public item !: ITodo;
        @Prop(Number) public index !: number;
        @Emit('say')
        public save() {
           return "hello";
        }
        public increment() {
            this.count += 1;
        }
        public render() {
            return <h1>{this.item.text}<button on-click={this.save}>触发方法</button>
            {this.count}
            <button on-click={this.increment}>点击加一</button>
            </h1>;
        }
    }


##### 现在我想监控count变化

Watch装饰器可以满足我们的要求，但是它只能监控方法，或类。
    
    /src/components/TodoItem.tsx
    import { Component, Vue, Prop, Emit, Watch } from 'vue-property-decorator';
    import { ITodo } from '../types/todo';
    
    @Component
    export default class TodoItem extends Vue {
        public count: number = 1;
        @Prop(Object) public item !: ITodo;
        @Prop(Number) public index !: number;
        @Emit('say')
        public save() {
           return "hello";
        }
    
        @Watch('count') //监控
        public fn(){
            console.log("count加1了");
        }
    
        public increment() {
            this.count += 1;
        }
        public render() {
            return <h1>{this.item.text}<button on-click={this.save}>触发方法</button>
            {this.count}
            <button on-click={this.increment}>点击加一</button>
            </h1>;
        }
    }

#### 加上vuex

##### 我们首先改写我们的Home.vue

该写完应该像下面这样

    /src/views/Home.vue
    <template>
      <div>
        <ul>
          <li v-for="(item,index) in lists" :key="index">
            <TodoItem :item="item" :index="index" @say="say"></TodoItem>
          </li>
        </ul>
        {{this.lists}}
      </div>
    </template>
    <script lang='ts'>
    import { Component, Vue } from "vue-property-decorator";
    import TodoItem from "../components/TodoItem";
    import { ITodo } from "../types/todo";
    import { State, Mutation, Action } from "vuex-class"; //引入
    
    @Component({
      components: {
        TodoItem,
      },
    })
    export default class Home extends Vue {
      @State("lists") public lists!: [];  //@State
      get count() {
        return this.lists.length;
      }
      
     @Mutation("hello") public say!: () => void; //触发mutation里的方法
      private mounted() {
        this.say();
      }
      //   public say(msg: string): void {
      //     console.log(msg);
      //   }
    }
    </script>

##### 编写/store/index.ts 文件

    /src/store/index.ts
    import Vue from 'vue';
    import Vuex from 'vuex';
    
    Vue.use(Vuex);
    // tslint:disable-next-line: no-duplicate-imports
    import { ITodo } from '../types/todo';
    
    interface IList {
      lists: ITodo[];
    }
    
    export default new Vuex.Store< IList>({
      state: {
        lists: [
          {text: '吃饭', complete: true},
          {text: '打代码', complete: false},
        ],
      },
      mutations: {
        hello() {
          console.log(1);
        },
      },
      actions: {
      },
      modules: {
      },
    });


#### 结束🐟

芙蓉湖上芙蓉花，秋风未落如朝霞。「送荪友」——纳兰性德