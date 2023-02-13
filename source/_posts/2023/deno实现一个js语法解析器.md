---
title: deno实现一个js语法解析器
date: 2023-02-12 22:39:25
tags: deno javascript
index_img: 2023/02/12/deno实现一个js语法解析器/tokenizer.png
---

## 前言

`javascript`是解释型语言，在v8中，源代码需要经过词法和语法分析，转化为AST, 再进行语义分析，最后转化成字节码执行。

语法分析成AST可以在这里体验：[https://esprima.org/demo/parse.html](https://esprima.org/demo/parse.html)。

本次deno 实现的源码在这里获取：[deno-ast](https://github.com/HighValyrian/deno-ast.git),开源学习随意复制。


## Parser(解析器)

Parser分为Tokenizer(分词器),和parser（解析器）。

### Tokenizer

分词器的最终目的是帮助我们将代码进行词法分析，分割成一个一个的小token，方便我们的parser去解析成AST.

我们先来测试一下我们`tokenizer`的效果。

把源码clone下来之后，运行：

```bash
deno test --filter "tokenizerTest"
```
![tokenizer](./tokenizer.png)

这些就是我们生产的token，有了这些token,我们的parser才能转化为AST。
`tokenizer`最核心的就是正则表达式，本质上就是用正则表达式去提取token。具体的正则定义可以查看[Tokenizer.ts](https://github.com/HighValyrian/deno-ast/blob/main/src/Tokenizer.ts)文件。

### Parser

接下来继续看parser，里面主要的内容就是下面两个

- BNF（巴科斯范式）
- Finite-state machine（有限状态机）

#### 巴科斯范式

巴科斯范式我个人的理解是一种使用递归思想来描述计算机语言的定义规范。
想进一步学习可以查看[bnf](http://sighingnow.github.io/%E7%BC%96%E8%AF%91%E5%8E%9F%E7%90%86/bnf.html)等相关内容。
不过，个人觉得最值得学习的还是编译器的优化，这比较重要。

我们来看一个代码的结构声明。代码位于[parser](https://github.com/HighValyrian/deno-ast/blob/main/src/Parser.ts)

```ts
    /**
     * ReturnStatement
     *   : 'return' OptExpression ';'
     */
    ReturnStatement() {
        this._eat('return'); // 吃掉当前的token
        const argument =
            this.currentToken.type !== ';' ? this.Expression() : null; // 这里的token已经是下一个的了
        this._eat(';');

        return {
            type: 'ReturnStatement',
            argument,
        };
    }
```
上面就是对return的一个声明，表示这个`ReturnStatement`需要以下结构：
>: 'return' OptExpression ';'
一个return关键字，加上可选择的表达(Expression在代码下面有进行结构声明)，然后结尾一个分号表示结束。

而一些`Statement`状态的转移主要是依赖我们的Statement函数：

```ts
  /**
   * Statement
   *   : ExpressionStatement
   *   | BlockStatement
   *   | EmptyStatement
   *   | VariableStatement
   *   | IfStatement
   *   | IterationStatement
   *   | FunctionDeclaration
   *   | ClassDeclaration
   *   | ReturnStatement
   *   ;
   */
  Statement(): Record<string, unknown> | undefined {
    switch (this.currentToken.type) {
      case ";":
        return this.EmptyStatement();
      case "if":
        return this.IfStatement();
      case "{":
        return this.BlockStatement();
      case "let":
        return this.VariableStatement();
      case "fun":
        return this.FunctionDeclaration();
      case "class":
        return this.ClassDeclaration();
      case "return":
        return this.ReturnStatement();
      case "while":
      case "do":
      case "for":
        return this.IterationStatement();
      default:
        return this.ExpressionStatement();
    }
  }
```

他帮助我们把`tokeninzer`生成的token转移到各个具体的声明去，构造我们的抽象语法树。

#### Finite-state machine（有限状态机）

在我们的parser里，可以理解成一系列状态的转移，每个方法都是一个状态。
每个函数的调用可以看作是一个状态的转移。
比如`parser.ts`里状态的转移是：

>Program -> StatementList -> Statement ...

最终的状态都会在`Literal`结束。

### 输出AST

我们运行以下测试，就能得到我们要的结果：

```bash
deno test --filter "parserTest"
```

这样我们就将代码转换为抽象语法树了。

```ts
    class add {
      fun constructor(x, y) {
        this.x = x;
        this.y = y;
      }      

      fun calc() {
        return this.x + this.y;
      }
    }
```

<details><summary>AST</summary>
```json
{
    "type": "Program",
    "body": [
        {
            "type": "ClassDeclaration",
            "id": {
                "type": "Identifier",
                "name": "Point"
            },
            "superClass": null,
            "body": {
                "type": "BlockStatement",
                "body": [
                    {
                        "type": "FunctionDeclaration",
                        "name": {
                            "type": "Identifier",
                            "name": "constructor"
                        },
                        "params": [
                            {
                                "type": "Identifier",
                                "name": "x"
                            },
                            {
                                "type": "Identifier",
                                "name": "y"
                            }
                        ],
                        "body": {
                            "type": "BlockStatement",
                            "body": [
                                {
                                    "type": "ExpressionStatement",
                                    "expression": {
                                        "type": "AssignmentExpression",
                                        "operator": "=",
                                        "left": {
                                            "type": "MemberExpression",
                                            "computed": false,
                                            "object": {
                                                "type": "ThisExpression"
                                            },
                                            "property": {
                                                "type": "Identifier",
                                                "name": "x"
                                            }
                                        },
                                        "right": {
                                            "type": "Identifier",
                                            "name": "x"
                                        }
                                    }
                                },
                                {
                                    "type": "ExpressionStatement",
                                    "expression": {
                                        "type": "AssignmentExpression",
                                        "operator": "=",
                                        "left": {
                                            "type": "MemberExpression",
                                            "computed": false,
                                            "object": {
                                                "type": "ThisExpression"
                                            },
                                            "property": {
                                                "type": "Identifier",
                                                "name": "y"
                                            }
                                        },
                                        "right": {
                                            "type": "Identifier",
                                            "name": "y"
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "type": "FunctionDeclaration",
                        "name": {
                            "type": "Identifier",
                            "name": "calc"
                        },
                        "params": [],
                        "body": {
                            "type": "BlockStatement",
                            "body": [
                                {
                                    "type": "ReturnStatement",
                                    "argument": {
                                        "type": "BinaryExpression",
                                        "operator": "+",
                                        "left": {
                                            "type": "MemberExpression",
                                            "computed": false,
                                            "object": {
                                                "type": "ThisExpression"
                                            },
                                            "property": {
                                                "type": "Identifier",
                                                "name": "x"
                                            }
                                        },
                                        "right": {
                                            "type": "MemberExpression",
                                            "computed": false,
                                            "object": {
                                                "type": "ThisExpression"
                                            },
                                            "property": {
                                                "type": "Identifier",
                                                "name": "y"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    ]
}
```
</details>


我们可以看到，最外层包裹着`Program`，而class 的类型为`ClassDeclaration`。
而他的body里又包裹着两个`FunctionDeclaration`,也就是我们的函数声明`fun`。


## 结束语

分享一个最近很喜欢的表情包哈哈

![哈哈](./expression.png)

### 感谢

- [rdp](https://github.com/AttackOnMorty/rdp)
- [https://esprima.org](https://esprima.org/demo/parse.html)