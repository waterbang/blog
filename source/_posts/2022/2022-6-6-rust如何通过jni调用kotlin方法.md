---
title: 2022-6-6-rust如何通过jni调用kotlin方法
date: 2022-06-06 21:45:50
tags: rust
index_img: /2022/06/06/2022-6-6-rust如何通过jni调用kotlin方法/banner.jpeg
---

## 前言
网上这方面比较缺少或者不完整，因此记录一下整个流程。
增加一下关键字防止搜索不到，这篇教程能让有需要的人少几天的琢磨时间。

### 使用rust写安卓库
### rust调用android
### rust通过ffi调用kotlin

### 主要的流程
主要流程是通过全局缓存保存了android的环境变量。以此来实现在rust调用android方法。

### 尝试过的方法

1. 直接通过rust闭包保存android环境，出现了方法不安全。✖️
2. 通过线程通信，结合闭包传递信息给fni方法。出现了线程通信不安全。✖️
3. 通过全局变量。也就是接下来的方法。 ✅

### 首先先看android部分如何进行加载

下面是android部分代码。主要是是加载库，然后注册函数。

```kotlin
package org.bfchain.rust.example

import android.app.IntentService
import android.content.Intent
import android.util.Log
private const val TAG = "SERVICE"
class DenoService : IntentService("DenoService") {
    companion object {
        // 加载rust编译的so
        init {
            System.loadLibrary("rust_lib")
        }
    }
    interface IHandleCallback {
        fun handleCallback(string: String)
    }
    external fun nativeSetCallback(callback: IHandleCallback)
    override fun onHandleIntent(p0: Intent?) {
        // val appContext = applicationContext
//        makeStatusNotification("有医保的先rush", appContext)
        nativeSetCallback(object : IHandleCallback {
            override fun handleCallback(string: String) {
                Log.d("handleCallback", "now rust says:" + string)
                // callable_map[string]?.let { it() }  // todo 执行你android的方法
            }
        })
    }
}

```
`nativeSetCallback`函数就是我们通过jni可以调用的方法，我们需要在rust通过全局缓存，把`android`的状态都缓存下来，
以此来实现我们在rust可以直接调用android方法。


### 接下来编写rust部分的内容

先上代码，后面再解释。

```rust
use crate::js_bridge::call_android_js;
use android_logger::Config;
use lazy_static::*;
use log::{debug, error, info, Level};
use tokio;
// 引用标准库的一些内容
use std::{
    ffi::{c_void, CStr, CString},
    sync::{mpsc, Mutex},
    thread,
};
// 引用 jni 库的一些内容，就是上面添加的 jni 依赖
use jni::{
    objects::{GlobalRef, JObject, JString, JValue},
    sys::{jint, jstring, JNI_ERR,JNI_VERSION_1_4},
    JNIEnv, JavaVM, NativeMethod,
};

// 添加一个全局变量来缓存回调对象
lazy_static! {
    // jvm
    static ref JVM_GLOBAL: Mutex<Option<JavaVM>> = Mutex::new(None);
    //callback
    static ref JNI_CALLBACK: Mutex<Option<GlobalRef>> = Mutex::new(None);
}
/// 使用宏简化声明 NativeMethod 对象
/// ## Examples
/// ```
/// let method:NativeMethod = jni_method!(native_method, "(Ljava/lang/String;)V");
/// ```
macro_rules! jni_method {
    ( $method:tt, $signature:expr ) => {{
        jni::NativeMethod {
            name: jni::strings::JNIString::from(stringify!($method)),
            sig: jni::strings::JNIString::from($signature),
            fn_ptr: $method as *mut c_void,
        }
    }};
}
/// 动态库被 java 加载时 会出发此函数, 在此动态注册本地方法
#[no_mangle]
#[allow(non_snake_case)]
unsafe fn JNI_OnLoad(jvm: JavaVM, _reserved: *mut c_void) -> jint {
    let class_name: &str = "org/bfchain/rust/example/DenoService";
    let jni_methods = [
        // # 添加注册一个可以传递java回调对象的本地方法
        jni_method!(nativeSetCallback, "(Lorg/bfchain/rust/example/DenoService$IHandleCallback;)V"),
    ];

    let ok = register_natives(&jvm, class_name, jni_methods.as_ref());

    // 在动态库被java加载时, 缓存一个jvm到全局变量, 调用回调时使用
    let mut ptr_jvm = JVM_GLOBAL.lock().unwrap();
    *ptr_jvm = Some(jvm);
    JNI_VERSION_1_4
}

/// 方法实现
#[no_mangle]
pub fn nativeSetCallback(env: JNIEnv, _obj: JObject, callback: JObject) {
    // 创建一个全局引用,
    let callback = env.new_global_ref(JObject::from(callback)).unwrap();

    // 添加到全局缓存
    let mut ptr_fn = JNI_CALLBACK.lock().unwrap();
    *ptr_fn = Some(callback);
}

unsafe fn register_natives(jvm: &JavaVM, class_name: &str, methods: &[NativeMethod]) -> jint {
    let env: JNIEnv = jvm.get_env().unwrap();
    let jni_version = env.get_version().unwrap();
    let version: jint = jni_version.into();

    let clazz = match env.find_class(class_name) {
        Ok(clazz) => clazz,
        Err(e) => {
            error!("java class not found : {:?}", e);
            return JNI_ERR;
        }
    };
    let result = env.register_native_methods(clazz, &methods);

    if result.is_ok() {
        info!("register_natives : succeed");
        version
    } else {
        error!("register_natives : failed ");
        JNI_ERR
    }
}
```

#### JNI_OnLoad 

这个函数在你加载so库的时候会自动调用，并不用在android里声明。他返回的是JNI版本，你需要选择你支持的版本。

> jni_method 的第二个参数是函数签名，如果你在android注册的函数不一样，需要自己修改函数签名。
> 如何查找函数的签名，直接google。

#### nativeSetCallback

` env.new_global_ref`是必须的，他可以帮助我们创建全局引用，我们的方法就可以跨方法跨线程调用，这里面的callback就是我们需要传递的闭包函数。

### 回调函数入口

下面的函数是利用闭包去执行上面缓存的`android`环境。`call_method`里的`handleCallback`函数，
我传递的参数是字符串，因此函数签名为`(Ljava/lang/String;)V`。
```rust
/// 回调 Callback 对象的 { void handleCallback(string: String) } 函数
pub fn call_java_callback(fun_type: &'static str) {
        android_logger::init_once(
        Config::default()
            .with_min_level(Level::Debug)
            .with_tag("myrust::handleCallback"),
    );
    log::info!("i am call_java_callback xxxxxxx1{:?}",fun_type);
    call_jvm(&JNI_CALLBACK, move |obj: JObject, env: &JNIEnv| {
        let s = String::from(fun_type);
        let response: JString = env
            .new_string(fun_type)
            .expect("Couldn't create java string!");
        match env.call_method(
            obj,
            "handleCallback",
            "(Ljava/lang/String;)V",
            &[JValue::from(JObject::from(response))],
        ) {
            Ok(jvalue) => {
                debug!("callback succeed: {:?}", jvalue);
            }
            Err(e) => {
                error!("callback failed : {:?}", e);
            }
        }
    });
}
/// # 封装jvm调用
fn call_jvm<F>(callback: &Mutex<Option<GlobalRef>>, run: F)
where
    F: Fn(JObject, &JNIEnv) + Send + 'static,
{
    let ptr_jvm = JVM_GLOBAL.lock().unwrap();
    if (*ptr_jvm).is_none() {
        return;
    }
    let ptr_fn = callback.lock().unwrap();
    if (*ptr_fn).is_none() {
        return;
    }
    let jvm: &JavaVM = (*ptr_jvm).as_ref().unwrap();
    match jvm.attach_current_thread_permanently() {
        Ok(env) => {
            let obj = (*ptr_fn).as_ref().unwrap().as_obj();
            run(obj, &env);
            // 检查回调是否发生异常, 如果有异常发生,则打印并清空
            if let Ok(true) = env.exception_check() {
                let _ = env.exception_describe();
                let _ = env.exception_clear();
            }
        }
        Err(e) => {
            debug!("jvm attach_current_thread failed: {:?}", e);
        }
    }
}
```

jni部分的函数已经写完了，接下来直接去调用`call_java_callback`函数就可以了。

### 调用call_java_callback

`use crate::android::android_inter;`就是上面文件的位置。具体根据您项目位置导入。
下面的`fun_type`参数就是要传递给android的，以此来调用android函数。

```rust
#[cfg(target_os = "android")]
use crate::android::android_inter;
pub fn call_android(fun_type: &str) {
    let callback = Box::leak(String::from(fun_type).into_boxed_str());
    #[cfg(target_os = "android")]
    android_inter::call_java_callback(callback);
}
```

>  Box::leak(String::from(fun_type).into_boxed_str()); 可以把&str变量转化成静态&'static str


### 结束🐟

如果此文章对您有帮助请发个表情告诉我，如果有其他建议或者勘误请直接留言。

垂杨拂绿水，摇艳东风年。
「折杨柳」
李白

