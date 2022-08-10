---
title: win10环境在node中使用RabbitMQ
date: 2020-03-13 21:39:54
tags: node.js
index_img: /2020/03/13/在node中使用RabbitMQ/login.png
---

### 前言
**注意：本篇内容以官方文档为主线加个人理解和采坑**
## 安装RabbitMQ

### 在windows10上安装
注意：安装RabbitMQ要先安装`Erlang`编程语言。需要翻墙下载，不然很慢。
>https://www.erlang.org/downloads

安装完需要设置系统变量。

#### 可以从github 上下载：

>https://github.com/rabbitmq/rabbitmq-server/releases

##### 或者点击直接下载
注意：这个链接在您到来之后可能不是最新版！
https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.8.3/rabbitmq-server-3.8.3.exe


#### 使用 `chocolatey`(Windows下的软件包管理器)
要安装RabbitMQ，请在命令行或PowerShell中运行以下命令:
```shell
choco install rabbitmq
```

### 在MacOS上下载
确保 Homebrew 为最新的：
```shell
brew update
```

然后下载rabbitmq
```shell
brew install rabbitmq
```

#### 也可以下载通用UNIX的二进制文件

>https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.8.3/rabbitmq-server-generic-unix-3.8.3.tar.xz


### 使用docker镜像
```shell
docker pull rabbitmq
```
<br>

### 配置RabbitMQ
**注意：接下来以windows10为基本环境**
如果您的环境为win10,下载完成记得将RabbitMQ的`/sbin`目录加入系统环境。
以便在任何地方控制您的MQ.
运行以下命令查看是否安装成功
```shell
rabbitmqctl status
```
#### 遇到的问题
我的RabbitMQ一启动就失败，系统日志显示了以下错误。
>RabbitMQ: Erlang machine stopped instantly (distribution name conflict?). The service is not restarted, ignoring OnFail option.

我尝试了多种解决方式。但是都没有用，最后把`erlang`和`RabbitMQ`卸载掉，都换成最新版本解决了问题。
注意：
1.  RabbitMQ无法安装到具有ASCII字符的路径,也就是路径不能有中文
2.  需要用管理员身份安装Erlang环境。
3.  安装路径不要有空格。（未实践！）
官方对错误的解答：[Windows怪癖](https://www.rabbitmq.com/windows-quirks.html)

#### 安装可视化插件
先查看RabbitMQ的全部插件，运行以下命令：
```shell
rabbitmq-plugins list
```
输出内容如下：
```shell
Listing plugins with pattern ".*" ...
 Configured: E = explicitly enabled; e = implicitly enabled
 | Status: [failed to contact rabbit@waterbang - status not shown]
 |/
....
[  ] rabbitmq_federation_management    3.8.3
[  ] rabbitmq_jms_topic_exchange       3.8.3
[  ] rabbitmq_management               3.8.3 // 这个是我们要安装的管理插件
[  ] rabbitmq_management_agent         3.8.3
[  ] rabbitmq_mqtt                     3.8.3
[  ] rabbitmq_peer_discovery_aws       3.8.3
[  ] rabbitmq_peer_discovery_common    3.8.3
[  ] rabbitmq_peer_discovery_consul    3.8.3
[  ] rabbitmq_peer_discovery_etcd      3.8.3
[  ] rabbitmq_peer_discovery_k8s       3.8.3
...
```
运行以下命令进行安装：
```shell
rabbitmq-plugins enable rabbitmq_management
```
输出以下内容为安装成功
```shell
Enabling plugins on node rabbit@waterbang:
rabbitmq_management
The following plugins have been configured:
  rabbitmq_management
  rabbitmq_management_agent
  rabbitmq_web_dispatch
Applying plugin configuration to rabbit@waterbang...
The following plugins have been enabled:
  rabbitmq_management
  rabbitmq_management_agent
  rabbitmq_web_dispatch

set 3 plugins.
Offline change; changes will take effect at broker restart.
```


## 如何在node中传递消息
我们来跟着官方的入门例子来进行第一步，将生产者连接到RabbitMQ,发送一条消息后退出。
下面是我们要实现的基本模型。中间蓝色的队列是消息缓冲区。
![hello world](./helloword.png)
### 安装amqp.node
`amqplib`是一个为Node.JS制作[AMQP 0-9-1](https://www.rabbitmq.com/amqp-0-9-1-reference.html)客户端的库，它支持Callback和Promise两种风格。
接下来在您的工作目录运行：
```shell
npm install amqplib
```

### 生产者
安装完成后开始写代码。创建生产者send.js。先连接道RabbitMQ服务器，
这是RabbitMQ给我们的一个最重要的接口，代码如下：
```html
var amqp = require('amqplib');

amqp.connect('amqp://localhost:5672').then((conn) => {  // 创建一个通道
  console.log(conn);
}, (err) => {
  throw Error('connection fail:===>' + err);
})
```
它返回给我们一个ChannelModel。接下来我们用它来创建一个通道,并且用`assertQueue(queue,[options])`声明一个队列。
它接收两个参数：
`queue`是一个字符串；如果您提供一个空字符串或其他虚假值（包括null和undefined），则服务器将为您创建一个随机名称。
`options`是一个对象，可以为空或null，如果是最后一个参数，则可以完全省略。
选项中的相关字段是：
1.  exclusive：如果为true，则将队列的作用域限定为连接（默认为false）
2.  durable：如果为true，则队列将在代理重新启动后幸存下来，并对exclusive和的作用取模autoDelete。如果未提供，则默认为true，这与其他方法不同
3.  autoDelete：如果为true，则当使用者数量降至零（默认值为false）时，将删除队列。
4.  arguments：附加参数，通常是某种特定于代理的扩展的参数，例如，高可用性，TTL。
*想要了解得更加详细[点我](https://www.squaremobius.net/amqp.node/channel_api.html#channel_assertQueue)*，代码如下：

```html
var amqp = require('amqplib');

amqp.connect('amqp://localhost:5672').then((conn) => {  // 连接到RabbitMQ服务器
  return conn.createChannel().then((ch) => { // 创建一个通道
    console.log(ch);
    let q = 'Queue'; // 队列名称
    let msg = 'How are you!'; // 发送的消息
    let ok = ch.assertQueue(q, { durable: false }); // 创建队列
  }).finally(() => {
    conn.close();
  });
}, (err) => {
  throw Error('connection fail:===>' + err);
})
```
它返回给我们一个Channel，接下来我们来发送消息到队列.
具体代码如下：

```html
var amqp = require('amqplib');

amqp.connect('amqp://localhost:5672').then((conn) => {  // 连接到RabbitMQ
  return conn.createChannel().then((ch) => { // 创建一个通道
    let q = 'Queue';
    let msg = 'How are you!';
    let ok = ch.assertQueue(q, { durable: false }); // 声明队列

    return ok.then((_qok) => {
       for (let i = 0; i < 100; i++) {
            ch.sendToQueue(q, Buffer.from(`${msg} 第${i}条消息`));
        }
      console.log(" [x] Sent '%s'", msg);
      return ch.close(); // 关闭通道
    })
  }).finally(() => {
    conn.close();
  });
}, (err) => {
  throw Error('connection fail:===>' + err);
})
```
>API详解[sendToQueue](https://www.squaremobius.net/amqp.node/channel_api.html#channel_sendToQueue)
>Buffer.from() :创建一个新缓冲区，其中填充了指定的字符串


### 消费者
接下我们来跟着上面一样写出消费者的代码，我们将使消费者保持运行状态以监听消息并打印出来。
我们一样要创建一个队列，防止在没有运行生产者的时候运行消费者。
具体代码如下：
```html
var amqp = require('amqplib');

amqp.connect('amqp://localhost:5672').then((conn) => { // 连接到RabbitMQ
  process.once('SIGINT', () => { conn.close(); }); // （beforeExit）在退出之前,关闭通道。

  return conn.createChannel().then((ch) => { // 创建通道
    let queue = 'Queue';
    let ok = ch.assertQueue(queue, {durable: false});  // 创建队列，（关闭持久化）

    ok = ok.then(function(_qok) {
      return ch.consume(queue, (msg) => {  // 取出消息（消费）
        console.log(" [x] 消费了 '%s'", msg.content.toString());
      }, {noAck: true});
    });

    return ok.then((_consumeOk) => {
      console.log(' [*] Waiting for messages. To exit press CTRL+C');
    });
  });
}).catch(console.warn);
```
`noAck: true`，如果为true，表示当消费者收到消息不会通知RabbitMQ，消费者收到了消息就会立即从队列中删除。
> 消费API -> [consume](https://www.squaremobius.net/amqp.node/channel_api.html#channel_consume)

这样就实现了基本的消息发送和接收。

## 任务队列
使用任务队列的优点之一是能够轻松并行化工作。如果我们有很多工作，我们可以增加更多的消费者，这样就可以轻松扩展。
我们先来修改一下上面send.js的代码，让它能在命令行接收消息。代码如下：
```html
var amqp = require('amqplib');

amqp.connect('amqp://localhost:5672').then((conn) => {  // 创建一个通道
  return conn.createChannel().then((ch) => {
    let q = 'task_queue';
    let msg = process.argv.slice(2).join('') || 'helloWord!';
    let ok = ch.assertQueue(q, { durable: true });

    return ok.then((_qok) => {
        ch.sendToQueue(q, Buffer.from(msg), {
          persistent: true
        });
      console.log(" [x] Sent '%s'", msg);
      return ch.close();
    })
  }).finally(() => {
    conn.close();
  });
}, (err) => {
  throw Error('connection fail:===>' + err);
})
```
>`persistent: true`如果是true，则消息将在代理重新启动后继续存在，前提是它在一个队列中，该队列也在重新启动后继续存在.

接下来修改一下上面的receive.js，让它在处理消息的时候伪造一秒钟的停顿。
它将从队列中弹出消息并执行任务，我们将其命名为`worker.js`，具体代码如下：
```html
var amqp = require('amqplib');

amqp.connect('amqp://localhost:5672').then((conn) => {
  process.once('SIGINT', () => { conn.close(); }); //beforeExit 执行close。
  return conn.createChannel().then((ch) => {
    let queue = 'task_queue'; // 保证使用该队列的时候先声明该队列
    let ok = ch.assertQueue(queue, {durable: true});

    ok = ok.then(function(_qok) {
      return ch.consume(queue, (msg) => {
        let secs = msg.content.toString().split('.').length - 1; //几个点就延迟几秒
         console.log(" [x] Received %s", msg.content.toString());
         setTimeout(function() {
           console.log(" [x] Done");
         }, secs * 1000);
      }, {noAck: true});
    });

    return ok.then((_consumeOk) => {
      console.log(' [*] Waiting for messages. To exit press CTRL+C');
    });
  });
}).catch(console.warn);
```

### 循环调度
默认情况下，RabbitMQ将按顺序将每个消息发送给下一个使用者。
平均而言，每个消费者都会收到相同数量的消息。这种分发消息的方式称为循环。
具体效果如下：
![TaskQueue](./TaskQueue.png)

### 消息确认
如果其中一个使用者开始一项漫长的任务并仅部分完成而死掉，会发生什么情况。
使用我们当前的代码，RabbitMQ一旦向消费者发送了一条消息，便立即将其标记为删除。
在这种情况下，如果您杀死一个消费者，我们将丢失正在处理的消息。我们还将丢失所有发送给该特定消费者但尚未处理的消息。
但是我们不想丢失任何任务。如果一个消费者死亡，我们希望将任务交付给另一个消费者。
接下来我们来修改一下代码，开启`{noAck: false}`选项，一旦我们完成了一项任务，消费者会发送一个确认消息。
修改worker.js,具体如下：
```html
var amqp = require('amqplib');

amqp.connect('amqp://localhost:5672').then((conn) => {
  process.once('SIGINT', () => { conn.close(); }); //beforeExit 执行close。

  return conn.createChannel().then((ch) => {
    let queue = 'task_queue'; // 保证使用该队列的时候先声明该队列
    let ok = ch.assertQueue(queue, {durable: true});
    ok = ok.then(function(_qok) {

      return ch.consume(queue, (msg) => {
        let secs = msg.content.toString().split('.').length - 1;
         console.log(" [x] Received %s", msg.content.toString());
         setTimeout(function() {
           console.log(" [x] Done");
           ch.ack(msg);  // ++  // 确认给定的消息
         }, secs * 1000);
      }, {noAck: false}); // == 
    });

    return ok.then((_consumeOk) => {
      console.log(' [*] Waiting for messages. To exit press CTRL+C');
    });
  });
}).catch(console.warn);
```
这样就能防止消费者挂掉后，由它处理的任务失败掉，我们来故意挂掉消费者1号，具体效果如下：
![TaskQueue_out.png](./TaskQueue_out.png)

消费者挂掉后，未确认的消息被重发了。

### 消息持久化
我们已经实现了如何确保消费者死亡，任务也不会丢失。但是，如果RabbitMQ服务器停止，我们的任务仍然会丢失。
如果您要告知RabbitMQ,确保消息不会消失，需要做两件事：我们需要将队列和消息都标记上持久性。
首先，我们需要确保RabbitMQ永远不会丢失队列。为此，我们需要将其声明为持久的：
```shell
channel.assertQueue('hello', {durable: true});
```
>注意：RabbitMQ不允许您使用不同的参数重新定义现有队列，并且将向尝试执行此操作的任何程序返回错误。

接下来将消息标记为持久消息：
```shell
channel.sendToQueue(queue，Buffer.from(msg)，{ persistent：true });
```

消息持久化并不会真正的写入磁盘，它只是保存到缓存当中，持久性并不强，但对于简单队列而言，已经绰绰有余了。
如果还需要更强的保存能力，可以使用[发布者确认](https://www.rabbitmq.com/confirms.html)

### 公平分配
为了不让RabbitMQ盲目的将消息的第n条消息发送给第n个使用者。这样在有的任务重，有的任务轻的时候，
可能会出现一位工人将一直忙碌而另一位工人将几乎不做任何工作。
发生这种情况是因为RabbitMQ在消息进入队列时才调度消息。它不会查看消费者的未确认消息数。
为了解决这个问题我们需要做以下配置：
```shell
channel.prefetch(1);
```
在处理并确认上一条消息之前，不要将新消息发送给工作人员。而是将其分派给尚不繁忙的下一个工作人员。

## 发布订阅
上面我们实现了把每个任务恰好交付给一个工人，接下来我们来实现，将消息传递给多个工人。
我们来跟着官方的例子，构建一个简单的日志记录系统。就是将已发布的日志广播到所有接收者。
它由两个程序组成：第一个程序将发出日志消息，第二个程序将接收并打印它们。

### 交换（Exchanges）
它是Rabbit的消息交换模型。核心思想是生产者从不将任何消息直接发送到队列。
一方面，它接收来自生产者的消息，另一方面，将它们推入队列。
但是它如何知道应该将消息加入队列，还是丢弃呢？规则由交换类型定义。
有四种交换类型可用：`direct`,`topic`,`headers`,`fanout`。
`fanout`交换类型正是我们需要的，它只是将接收到的所有消息广播到它知道的所有队列中。
```html
ch.assertExchange('logs','fanout',{durable：false })
```
>Channel的`assertExchange`用来断言交换的存在，与队列一样。
>参数类型为：assertExchange(exchange, type, [options])

如果要知道您的服务器上的交换可以运行：
```shell
rabbitmqctl list_exchanges
```

#### 默认交换
我们以前使用的都是默认交换
```html
channel.sendToQueue('hello'，Buffer.from('Hello World！'));
```
在这里，我们使用默认或无名称交换：消息以指定为第一个参数的名称路由到队列（如果存在）。
接下来我们指定发布到`logs`交换中：
```html
channel.publish('logs', '', Buffer.from('Hello World！'));
```
`publish`功能和`sendToQueue`差不多，第二个参数的空字符串表示我们不想将消息发送到任何特定的队列。

### 绑定
我们已经创建了一个`fanout`交换和一个队列。现在我们需要告诉交换机将消息发送到我们的队列。交换和队列之间的关系称为绑定。
```HTML
channel.bindQueue(queue_name, 'logs', '');
```
>[bindQueue](https://www.squaremobius.net/amqp.node/channel_api.html#channel_bindQueue):声明从交换机到队列的路由路径

这此我们将消息发送到`logs`交换器，而不是无名的默认交换器。
发送时我们需要提供一个路由密钥，但是对于`fanout`交换，它的值将被忽略。这是emit_log.js脚本的代码 ：
```html
const amqp = require('amqplib');

amqp.connect('amqp://localhost').then((conn) => {
  return conn.createChannel().then((ch) => {
    const ex = 'logs';
    let ok = ch.assertExchange(ex, 'fanout', {durable: false}) // 声明交换

    let message = process.argv.slice(2).join(' ') ||
      'info: Hello World!';

    return ok.then(() => {
      ch.publish(ex, '', Buffer.from(message));
      console.log(" [x] Sent '%s'", message);
      return ch.close();
    });
  }).finally(() => { conn.close(); });
}).catch(console.warn);
```
从上面我们可以看到，建立连接之后，我们声明了交换。
如果没有队列绑定到对应的交换那么消息将丢失。receive_log.js代码如下：
```html
const amqp = require('amqplib');

amqp.connect('amqp://localhost').then( (conn) => {
  process.once('SIGINT', () => { conn.close(); });
  return conn.createChannel().then((ch) => {
    let ok = ch.assertExchange('logs', 'fanout', { durable: false });
    ok = ok.then(() => {
      return ch.assertQueue('', { exclusive: true });
    });
    ok = ok.then((qok) => {
      return ch.bindQueue(qok.queue, 'logs', '').then(function () {  // 绑定队列
        return qok.queue;
      });
    });
    ok = ok.then((queue) => {
      return ch.consume(queue, logMessage, { noAck: true });
    });
    return ok.then(() => {
      console.log(' [*] Waiting for logs. To exit press CTRL+C');
    });

    function logMessage(msg) {
      console.log(" [x] '%s'", msg.content.toString());
    }
  });
}).catch(console.warn);
```
运行结果如下：
![fady](./fady.png)

## over
助秋风雨来何速，惊破秋窗秋梦绿。
「代别离·秋窗风雨夕」
曹雪芹