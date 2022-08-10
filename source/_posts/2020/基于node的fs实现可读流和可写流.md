---
title: 基于node的fs实现可读流和可写流
date: 2020-03-29 10:48:29
tags: node.js
index_img: /2020/03/10/node中的require方法/logo.jpg
---

### 前言
确保您有node.js的环境。

## 可读流（ReadStream）
先来看看核心方法如何使用，这也是我们开发中真正使用的。在工作目录下先创建一个`1.txt`,写入 你好
然后创建一个`stream.js`,内容如下：

```html
let fs = require('fs');
let path = require('path');

let rs = fs.createReadStream(path.resolve(__dirname,'1.txt'))
let arr = [];

rs.on('data',function(data){ // buffer
    arr.push(data);
})
rs.on('end',function(){
   console.log(Buffer.concat(arr).toString());
});

```

上面代码中我们创建了一个arr数组来存我们每次读取的二进制数据。其形式为buffer。
其内部每次读取到数据就会触发我们监听的`data`事件。然后把数据返还给我们，而`end`事件是结束时触发的。两者都是固定的。
上面调用`fs.createReadStream()` 默认是流是暂停的，只有我们手动监听`data`事件的时候才会进行数据读取。
> 内部触发事件具体看[官方文档](http://nodejs.cn/api/fs.html#fs_class_fs_readstream)

### 可传的参数

`fs.createReadStream(path，[options])`的第二个参数允许我们进行传参，我们先来了解一下各个参数的作用。

```html
let rs = fs.createReadStream('./1.txt',{
    flags:'r', // 当前要做什么操作，具体可以看下面的文件系统标志
    encoding:null, // 默认是buffer
    highWaterMark:2,// 内部会创建 64k大的buffer
    mode:438,// 文件的权限 438为8进制，换成二进制为110110110
    autoClose:true, //默认为true ,在`error`或`end` 事件时，文件描述符会自动关闭。
    start:0,
    end:6 // start 和 end 就是读取一定范围的字节。
});
```
1.  `flags` 具体要进行的操作，如读取 `r` 或者写入 `w`。 默认 r
2.  `encoding`  其可以是 Buffer 接受的任何一种字符编码。 默认 null
3.  `fd` 如果指定，其内部将会忽略path参数，并使用指定的文件描述符。 默认为 null
4.  `mode` 文件的权限，跟linux一样，4->可读 2->可写 1->可执行， 默认为 0o666或者438
5.  `autoClose` 是否在触发error或者end事件时自动关闭文件。 默认为 true
6.  `emitClose` 默认情况下，流在销毁后将不会触发 'close' 事件。更改为true可以更改此行为。 默认为 false
7.  `start end` 设置读取的范围。默认读取全部内容。
8.  `highWaterMark` 默认每次读取64K，内部创建64K的缓冲区（buffer）。 默认为 64*1024

>注意: *文件写入时。如果文件不存在则创建文件，如果文件已存在则截断文件。* 
>*文件在读取时。如果文件不存在，则出现异常。*

### ReadStream.js
我们在工作目录创建文件 `ReadStream.js`,来写我们自己的可读流。
我们要先明确内部的流在创建的时候是暂停的。就跟我们的龙头一样。data事件就是我们的开关。
其次内部为了降低耦合，用了发布订阅。
我们首先要改一下stream.js,来用上我们自己的ReadStream。代码如下：

```html
const fs = require('fs');
let ReadStream = require('./ReadStream');
let rs = new ReadStream('./1.txt',{
    flags:'r', // 当前要做什么操作，具体可以看下面的文件系统标志
    encoding:null, // 默认是buffer
    highWaterMark:2,// 内部会创建 64k大的buffer
    mode:438,// 文件的权限 438为8进制，换成二进制为110110110
    autoClose:true, //默认为true ,在`error`或`end` 事件时，文件描述符会自动关闭。
    start:0,
    end:6 // start 和 end 就是读取一定范围的字节。
});
rs.on('open',function(fd){
    console.log('文件打开触发open事件',fd)
});
let arr = [];
rs.on('data',function(data){ // 每次读取到的结果
    console.log(data);
    arr.push(data); // 存起来
})
rs.on('end',function(){
    console.log('文件读取完毕')
     console.log(Buffer.concat(arr).toString());
});
rs.on('close',function(){
    console.log('文件关闭')
});
```
接下来就可以创建我们自己的ReadStream了，内部会基于node.js的[events](http://nodejs.cn/api/events.html)和[fs](http://nodejs.cn/api/fs.html)模块。
先引入两个模块，然后我们的类要继承events，接着把常用的可选参数传入。
读取的第一步就是要将文件打开，借助fs模块我们可以打开文件，并获得文件标识符，以方便下一步动作。
我们用一个`flowing`参数标识流是否是暂停的。并且在注册了`data`事件之后，将其打开。
代码如下：
```html
const EventEmitter = require('events');
const fs = require('fs');
class ReadStream extends EventEmitter{
  constructor(path, options = {}) {
    super();
    this.path = path;
    this.flags = options.flags || 'r';
    this.encoding = options.encoding || null;
    this.highWaterMark = options.highWaterMark || 64*1024;
    this.mode = options.mode || 438;
    this.autoClose = options.autoClose || true;
    this.start = options.start || 0;
    this.end = options.end;

    this.flowing = null; // 默认是暂停模式
    this.offset = 0; // 读取文件的偏移量
    this.open(); // 打开文件 (异步)
    this.on('newListener',(type) => {
    console.log(type);
     if(type === 'data') {
      this.flowing = true;
      this.read();
     }
    })
  }
  read() {
    console.log(this.fd);  // undefined
   }
  open() {
    fs.open(this.path, this.flags, (err,fd) =>{
      this.fd = fd;
      this.emit('open', this.fd);
    })
  }
}
```
上面的[newListener](http://nodejs.cn/api/events.html#events_event_newlistener)事件,为其注册监听器，会传递事件名称和对要添加的监听器的引用。
type打印内容如下：
![newListener](./newListener.png)

在我们打开文件要对其进行读取的时候，发现文件打开操作是异步的，而读取操作是同步的。文件还没打开就去读取是不得行的。
所以在`read()`的时候，this.fd是undefined。我们现在要解决的就是让`read()`比`open()`慢。
process.nextTick是不行的，它指定的任务会发生在所有异步任务之前。
解决方法是给`read()`注册一个open监听器，文件描述符获取到后触发这个open事件。
然后再去再次调用`read()`，这样就能在`read()`里获取到this.fd。具体代码如下：
```html
read() {
    if(typeof this.fd !== "number") { // 因为read 比open先调用
      return this.once('open', this.read); // 先把read方法存起来， 等open后再次调用。
    }
    console.log(this.fd);
  }
  open() {
    fs.open(this.path, this.flags, (err,fd) =>{
      this.fd = fd;
      this.emit('open', this.fd);
    })
  }
```
输出如下：
![fd](./fd.png)

这样就能获取到文件描述符，接下来就是进行连续读的操作，read()代码如下：
```html
 read() {
    if(typeof this.fd !== "number") { // 因为read 比open先调用
      return this.once('open', this.read); // 先把read方法存起来， 等open后再次调用。
    }
    let buffer = Buffer.alloc(this.highWaterMark); // 每次读多少个

    fs.read(this.fd, buffer, 0, this.highWaterMark, this.offset, (err, bytesRead) => {
      this.offset += bytesRead; // 每次往前走
      if(bytesRead > 0) { //判断是否读完
      this.emit('data', buffer); // 如果读取到了内容就触发data事件
      this.read();
      } else {
        this.emit('end');
      }
    })
  }
```
fs.read的各个参数分别是：
`this.fd`: 要操作的文件标识符
`buffer`: 给一个多大的缓冲区
`0`：从buffer什么位置开始填进去
`this.highWaterMark`： 每次读多少
`this.offset`：每次写入文件的偏移量
然后我们每次读取到数据，就去触发data事件，然后把读到的buffer传递出去。如果bytesRead小于或等于零，表示读完了直接触发end事件就可以了。
我们还需要进一步完善我们的读取操作。把我们的end和start参数用上，并且添加close和控制流的方法：
```html
const EventEmitter = require('events');
const fs = require('fs');
class ReadStream extends EventEmitter{
  constructor(path, options = {}) {
    super();
    this.path = path;
    this.flags = options.flags || 'r';
    this.encoding = options.encoding || null;
    this.highWaterMark = options.highWaterMark || 64*1024;
    this.mode = options.mode || 438;
    this.autoClose = options.autoClose || true;
    this.start = options.start || 0;
    this.end = options.end;

    this.flowing = null; // 默认是暂停模式
    this.offset = 0; //偏移量
    this.open(); // 打开文件 (异步)
    this.on('newListener',(type) => {
     if(type === 'data') {
      this.flowing = true;
      this.read();
     }
    })
  }
  read() {
    if(typeof this.fd !== "number") { // 因为read 比open先调用
      return this.once('open', this.read); // 先把read方法存起来， 等open后再次调用。
    }

    let howMuchToRead = this.end
    ? Math.min(this.highWaterMark, this.end-this.start + 1 - this.offset)
    : this.highWaterMark;
    let buffer = Buffer.alloc(howMuchToRead);

    fs.read(this.fd, buffer, 0, howMuchToRead, this.offset, (err, bytesRead) => {
      this.offset += bytesRead;
      if(bytesRead > 0) {
      this.emit('data', buffer); // 如果读取到了内容就触发data事件
      this.flowing && this.read();
      } else {
        this.emit('end');
        this.close();
      }
    })
  }
  close() {
    if(this.autoClose) {
      fs.close(this.fd, () => {
        this.emit('close');
      })
    }
  }
  open() {
    fs.open(this.path, this.flags, (err,fd) =>{
      this.fd = fd;
      this.emit('open', this.fd);
    })
  }
  pause() {
    this.flowing = false;
  }
  resume() {
    this.flowing = true;
    this.read();
  }
}
```
如果我们传了end和start,我们就需要算出每次一共读几个，防止最后一次读取的时候超过end。
然后加上控制流的方法。还有条件。我们的可读流就完成了。

## 可写流（writeStream）

### 用法
可写流最主要的就是 `write` 和 `end` 事件，一个是写入操作，一个是关闭操作。
我们先来实现一个写一点，等待写完，再次进行写的操作。这样可以节省内存占用。
创建一个write.js 文件用来写入我们的代码：
```html
let fs = require('fs');
let ws = fs.createWriteStream('./1.txt',{
  highWaterMark:3 // 预计占用的内存
})
let index = 0;
function write() {
  let flag = true;
  while(index < 10 && flag) {
    flag = ws.write(index + ''); // 转换成 String
    index++;
  }
  if(index > 9) {
    ws.end(); // 关闭文件 关闭可写流
  }
}
write();

ws.on('drain', function(){
  console.log('预计内存满了');
  write();
})
```
highWaterMark参数表示预计占用的内存,默认为16K.
其内部在写入的个数达到了，且预计的大小被写入到文件后清空了，就会触发`drain`事件，
所以我们可以在`drain`事件里，再次调用write方法。输出内容如下：
![write1](./write1.png)

由于我们写入10个数，每次写3个，所以drain触发了3次。
> **注意：
> 由于内部不知道什么时候写完的，所以我们需要手动调用end事件。
> 可写流写入是数据只能是字符串或者Buffer。**

### writeStream.js
接下来创建自己的可写流，创建`writeStream.js`文件,改写write.js 内容如下：
```html
let fs = require('fs');
let WriteStream = require('./writeStream')
let ws = new WriteStream('./1.txt',{
  highWaterMark:3,// 预期占用几个内存
  encoding:'utf8',// 写入的编码
  start:0, // 从文件的第0个位置开始写入
  mode:438,
  flags:'w' // 默认操作是可写
})
let index = 0;
function write() {
  let flag = true;
  while(index < 10 && flag) {
    flag = ws.write(index + '');
    console.log(flag)
    index++;
  }
  if(index > 9) {
    ws.end(); // 关闭文件 关闭可写流
  }
}
write();

ws.on('drain', function(){
  console.log('预计内存满了');
  write();
})
ws.on('close',function(){
  console.log('关闭了文件');
})
```

刚开始的写法跟可读流是一样的，我们引入events模块，然后把参数在构造函数中赋值。可读流一创建就可以进行写的操作，
那么它在创建的时候肯定是打开了的，接下来先创建 open() write() end() 方法，内容如下：
```html
const EventEmitter = require('events');
class WriteStream {
  constructor(path, options = {}) {
    super();
    this.path = path;
    this.highWaterMark = options.highWaterMark || 16 * 1024
    this.encoding = options.encoding || 'utf8';
    this.start = options.start || 0;
    this.mode = options.mode || 0o666;
    this.flags = options.flags || 'w';
    // 先打开文件
    this.open();
  }
  open() {

  }
  write() {

  }
  end() {
    
  }
}

module.exports = WriteStream;
```
先完善我们的open()方法，用户会同步调用write方法，在取的时候并不一定能取到文件标识符，而且用户调用write方法时，
需要先判断当前是否正在写入，如果正在写入需要先放到缓存中，如果不是正在写入，需要真正的写入文件当中。
我们还需要创建几个变量，具体代码如下：
```html
class WriteStream {
  constructor(path, options = {}) {
    super();
    this.path = path;
    this.highWaterMark = options.highWaterMark || 16 * 1024
    this.encoding = options.encoding || 'utf8';
    this.start = options.start || 0;
    this.mode = options.mode || 0o666;
    this.flags = options.flags || 'w';
    // 先打开文件
    this.open();
    // 缓存区 
    this.cache = [];
    this.writing = false; // 判断是否正在被写入
    this.len = 0; // 缓存区的大小
    this.needDrain = false; // 是否触发drain事件
    this.offset = this.start; // offset 表示每次写入的偏移量
  }
  open() { // 先打开文件
    fs.open(this.path, this.flags, (err, fd) => {
      this.fd = fd;
      this.emit('open', fd);
    })
  }
  write() {

  }
}
```
接下来完善write方法,第一个参数是写入的数据，第二个是编码没给用默认的编码，第三个是个callback。
我们首先要先判断，写入的数据是不是buffer,如果不是转换成buffer。接着统计写入数据的个数，
然后和highWaterMark比较，返回一个flag。代码如下：
```html
 write(chunk, encoding = this.encoding, callback) {// 用户会同步的调用write方法
    chunk = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk); // 判断这个chunk 是不是buffer 如果不是buffer转化成buffer
    this.len += chunk.length; // 统计写入数据的个数
    let flag = this.len < this.highWaterMark;
    return flag;
  }
```
运行write.js文件，输出:
>true
true
false

这样子是没错的，flag返回的是告知还有没有空间，我们的highWaterMark传入的是3，所以第三个写入满了，就返回了false。
这样我们可以得知，什么时候应该触发drain事件。然后我们需要将除了第一次数据真实写入，而其他都放到缓存中。
然后再去清空缓存队列，每次取第一个，进行真正的写入。而且每次调用的时候，还需要执行自己的成功操作，并且清空队列。代码如下：
```html
 write(chunk, encoding = this.encoding, callback) {// 用户会同步的调用write方法
    chunk = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk); // 判断这个chunk 是不是buffer 如果不是buffer转化成buffer
    this.len += chunk.length; // 统计写入数据的个数
    let flag = this.len < this.highWaterMark;
    this.needDrain = !flag; //相反操作
    if (this.writing) { // 当前是否正在写入
      this.cache.push({ // 将除了第一次真实的写入，其他都放到缓存中
        chunk,
        encoding,
        callback
      })
    } else {
      this.writing = true; // 标识是否正在写入
      this._write(chunk, encoding, () => {
        callback && callback(); // 先执行自己的成功操作
        this.clearBuffer(); // 再去清空队列中的第一个
      });// 真实像文件中写入
    }
    return flag;
  }
```
我们先来创建真正写入的核心方法_write,它获取this.fd，需要等待open事件触发，跟可读流一样。
接着进行文件的写入操作:
```html
  // 核心的写入方法
  _write(chunk, encoding, clearBuffer) {
    if (typeof this.fd !== 'number') { //  write方法相对于open 是先调用的
      return this.once('open', () => this._write(chunk, encoding, clearBuffer))
    }
    fs.write(this.fd, chunk, 0, chunk.length, this.offset, (err, written) => {
      // written 表示真实写入的个数
      this.offset += written; // 增加偏移量
      this.len -= written; // 减少缓存中的数据
      clearBuffer(); // 清空缓存
    })
  }
```
fs.write的各个参数分别是：
`this.fd`: 要操作的文件标识符
`chunk`: 写入的数据
`chunk.length`: 读取buffer多少个字节
`0`：0表示把数据的第0个位置开始写入
`this.highWaterMark`： 每次读多少
`this.offset`：每次写入文件的偏移量
接下来要写清空缓存中的方法，需要判断缓存中是否有数据，如果有就取出第一个进行写入，如果没有数据且this.needDrain为true，
就表示数据都被清空了，需要从新设置变量然后触发drain事件：
```html
 clearBuffer() {
    // 去缓存中取
    let obj = this.cache.shift();
    if (obj) { // 需要写入
      this._write(obj.chunk, obj.encoding, () => {
        obj.callback && obj.callback();
        this.clearBuffer();
      });
    } else {
      if (this.needDrain) {
        this.needDrain = false; // 下一次需要重新判断是否需要触发drain事件
        this.writing = false; //告诉下一次调用write 应该像文件中写入
        this.emit('drain');
      }
    }
  }
```
这样我们的写入方法就完成了，再到write.js里run一下，内容是正确的，最后还需要完善close和end方法。
close比较简单直接调用fs的close方法就行了：
```html
  close() {
    fs.close(this.fd, () => {
      this.emit('close')
    })
  }
```
接着就是end方法，end方法可以传参，第一个是写入的内容，第二个是编码，
如果传递参数，我们需要先强制清空缓存，然后写入end方法的内容，接着再关闭文件,代码如下：
```html
  end(chunk, encoding) {  
    if (chunk) {
      chunk = Buffer.isBuffer(chunk)?chunk:Buffer.from(chunk);
      return this.write(chunk, encoding, () => {
        this.close()
      })
    }
    this.close();
  }
```

这样我们就完成了可写流。

### 结束语
错误之处留言告知，谢谢你！。

记得金銮同唱第，春风上国繁华。
「临江仙·记得金銮同唱第」
欧阳修