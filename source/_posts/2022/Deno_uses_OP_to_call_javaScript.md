---
title: Deno uses OP to call javaScript
date: 2022-08-10 21:22:28
tags: deno javascript
index_img:
---

## preface

>⚠️ This IS MY FIRST ATTEMPT TO write IN English. Please note that the following code may be wrong. It is still being modified.

`javascript` using `op` to call `rust` is relatively simple, and the `Deno` source code also has many examples.
This paper mainly focuses on how `deno` calls` javascript `, or in another way, how to give `deno` data to `javascript`.
The approach in this paper is to write polling functions in javascript that constantly ask rust for data. To achieve back pressure.

### How to write

The pseudocode is as follows.

```rust
// Remember to register the OP function with the JS Runtime
[op]
op_rust_to_js_buffer() -> Result<Vec<u8>,AnyError> {
 // This DATA is a global static variable
  match DATA {
    Some(r)=> {Ok(r)}，
    Err(e) => {deno_core::error::custom_error{
      "op_rust_to_js_buffer",
      "no Found data"
    }}
  }
}
```

```javascript
function op_rust_to_js_buffer() {
  try {
    const buffer = Deno.core.opSync("op_rust_to_js_buffer");  // return Vec<u8> -> Unit8Array
    const result = new Textdecoder().decode(new Unit8Array(buffer));
    console.log(result);
    return result;
  }catch(e) {
    return false;
  }
}
function handlerFactory() {
  setInterval(() => {
    const data = op_rust_to_js_buffer(); // server boom 
    //....
  });
}
handlerFactory();
```

I've tried the following, but it has a heap overflow.

```javascript
function op_rust_to_js_buffer() {
  new Promise((resolve,reject) => {
    try {
      const buffer = Deno.core.opAsync("op_rust_to_js_buffer").then();  // return Vec<u8> -> Unit8Array
      const result = new Textdecoder().decode(new Unit8Array(buffer));
      console.log(result);
      resolve(result)
    }catch(e) {
      reject(e);
    }
  }).finally(() => op_rust_to_js_buffer())
}
```

[Gaubee](https://github.com/Gaubee):

```javascript
/// 两个核心函数
const callRust = Deno.core.opSync("op_js_to_rust");
const waitRustBuffer = Deno.core.opAsync("op_rust_to_js_buffer");

/// 原始的调用
let acc_call_id = 0;
{
  const callId = acc_call_id++;
  callRust(callId, ...some_args);

  const buffer1 = await waitRustBuffer(callId);
  const buffer2 = await waitRustBuffer(callId);
  const buffer3 = await waitRustBuffer(callId);
  //...
}

/// 深度封装
class MyModule {
  private static _acc_id = 0;
  private _id = MyModule._acc_id++;
  /**
   * 第一种封装，使用 AsyncGenerator
   */
  async *call1(...args) {
    const callId = this._id;
    callRust(callId, ...args);

    do {
      const buffer1 = await waitRustBuffer(callId);
      /// 基于数据的规范，来定义什么时候结束
      if (buffer1.length === 0) {
        break;
      }
      /// 返回数据
      yield buffer1;
      /// 这里是重点，使用 do-while ，替代 finally，可以避免堆栈溢出。
    } while (true);
  }
  /**
   * 第二种封装，手写 AsyncGenerator
   */
  call2(...args) {
    const callId = this._id;
    callRust(callId, ...args);

    return {
      async next() {
        const buffer = await waitRustBuffer(callId);
        return {
          value: buffer,
          done: buffer.length === 0,
        };
      },
      return() {
        /// 这里可以手动控制异步迭代器被 “中止” 释放
      },
      throw() {
        /// 这里可以手动控制异步迭代器被 “中止” 释放
      },
    };
  }
}
```

整理了一下：

```typescript
export function loopRustBuffer() {
  return {
    async next() {
      let buffer = null;
      try {
        buffer = await Deno.core.opAsync("op_rust_to_js_buffer");
        const string = new TextDecoder().decode(new Uint8Array(buffer));
        console.log("rust send message to deno_js:", string);
        return {
          value: string,
          done: false,
        };
      } catch (e) {
        return {
          value: buffer,
          done: true,
        };
      }
    },
    return() {
      /// Here you can manually control the asynchronous iterator to be "aborted" and released
    },
    throw() {
      /// Here you can manually control the asynchronous iterator to be "aborted" and released
    },
  };
}

async *waterOverflow() {
    do {
        const buffer = await loopRustBuffer().next();
        /// Data-based specification to define when to end
        // if (isWaitingData > this.hightWaterMark) {
        //   console.log(
        //     "waterOverflow====>",
        //     isWaitingData,
        //     hightWaterMark
        //   );
        //   break;
        // }
        if (!buffer.done) {
          this.isWaitingData++;
        }
        yield buffer;
        /// Here is the point, use do-while instead of finally, you can avoid stack overflow。
    } while (true);
  }

(async function () {
  for await (let num of waterOverflow()) {
    if (!num.done) {
      console.log("webView.waterOverflow:", num);
    }
  }
})();

```
