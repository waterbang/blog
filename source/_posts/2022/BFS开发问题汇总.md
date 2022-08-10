---
title: BFS开发问题汇总
date: 2022-08-08 23:11:26
tags: rust kotlin deno javascript
index_img:
---

## 前言

BFS运行时本质上是一个操作系统，主要目的是

1. 为了解决现代单页面应用（SPA）的性能不足问题。
2. 为开发者提供`android`,`ios`和`desktop`端的应用开发。
3. 为了契合面向角色编程和开发BFS资产做准备，为区块链开发做社区基础建设。

## rust混合编译问题

### 修复 failed to run custom build command for `ring v0.16.20`

运行  

```bash
RUST_BACKTRACE=1 cargo build --target=aarch64-linux-android --release
```

发现

```bash
 --- stderr
  error occurred: Failed to find tool. Is `aarch64-linux-android-clang` installed?
```

原因是环境变量的名称错误，需要更改一下

```bash
cd /Users/mac/Library/Android/sdk/ndk/21.3.6528147/toolchains/llvm/prebuilt/darwin-x86_64/bin/

cp aarch64-linux-android28-clang aarch64-linux-android-clang 
```

### 修复error: failed to run custom build command for `libffi-sys v1.3.2`

```bash
brew install autoconf automake libtool   
```

然后 在ext/ffi/cargo.toml
修改版本为：libffi = "3.0.0"

## rust_v8 问题汇总

### 解决使用容器编译下载报错问题（这块仅供参考，具体位置查看build.rs文件）

1. 下载: <https://codeload.github.com/denoland/ninja_gn_binaries/tar.gz/refs/tags/20220517>
解压到：tools目录下

2. 下载: <https://commondatastorage.googleapis.com/chromium-browser-clang/Linux_x64/clang-llvmorg-15-init-9576-g75f9e83a-3.tgz>
解压到：tools/clang  

3. 下载: <https://commondatastorage.googleapis.com/chrome-linux-sysroot/toolchain/3dc473ad845d3ae810c3e1be6f377e3eaa301c6e/debian_bullseye_arm64_sysroot.tar.xz>
解压到：build/linux/debian_bullseye_arm64-sysroot

4. 下载：git clone <https://chromium.googlesource.com/chromium/src/third_party/android_platform>
5. 下载：git clone <https://github.com/denoland/android_ndk.git>
6. 下载：git clone <https://chromium.googlesource.com/catapult.git>
到 third_party
并且需要添加到环境变量：`GN`, `NINJA`,`CLANG_BASE_PATH`, `GN_ARGS`

#### ERROR at //build/config/mac/mac_sdk.gni:95:31: No value named "xcode_build" in scope "_mac_sdk_result"[v8 0.48.0] xcode_build =_mac_sdk_result.xcode_build

安装 xcode

#### ERROR at dynamically parsed input that //build/config/mac/mac_sdk.gni:93:19 loaded :1:15: This is not a valid number.xcode_build=11C505

File "/Users/mac/Desktop/waterbang/project/rust/rusty_v8/build/config/apple/sdk_info.py", line 71
修改为 `int[lines[-1].split(](-1),16)`

#### fatal error: 'features.h' file not found

检查  `--sysroot=../../../../third_party/android_ndk/toolchains/llvm/prebuilt/darwin-x86_64/sysroot`
观察ndk,是否没有`darwin-x86_64`,把目录下：
`third_party/android_ndk/toolchains/llvm/prebuilt/`的其他版本复制一分重命名为`darwin-x86_64`，或者是别的系统名。

## android 问题汇总

### 使用android studio生成JNI

打开设置路径：Tools->External Tools , 点击添加。

![add jni](./jni.jpeg)

> -classpath -v -jni -d $ContentRoot$/jni
> -d $ContentRoot$/jni  -cp "$Classpath$" $FileFQPackage$.$FileNameWithoutAllExtensions$
> $ModuleFileDir$
