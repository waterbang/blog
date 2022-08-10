---
title: '基础机器学习:使用CNN的手写数字识别'
date: 2020-06-10 15:46:14
tags: TensorFlow.js
index_img: /2020/06/10/基础机器学习-使用CNN的手写数字识别/input-data.png
---

### 前言

本章将基于[TensorFlow.js](https://www.tensorflow.org/js/)模型，使用卷积神经网络识别手写数字。
使用的打包工具是[parcel](https://parceljs.org/getting_started.html)。
这个手写数字是机器学习领域的HelloWorld,我们将会创建一个浏览器的网页来承载我们的模型。
这个模型将会学习大量的示例，和正确的输出结果，来训练模型。这被称为[监督学习](https://developers.google.cn/machine-learning/problem-framing/cases)。

#### 训练集介绍
训练集是著名的[MNIST](http://yann.lecun.com/exdb/mnist/),（需要翻墙），图像是黑白两色，大小为28×28像素。
Google的开发人员已经帮我们将这些大量的图片数据，变成了一张雪碧图，并且给了我们一个加载这些数据的`data.js`。这样我们就可以专注于训练的部分。

![allData](./allData.png)

总共有65,000张图像，资源链接如下：（链接失效评论区留言）
>链接：https://pan.baidu.com/s/1BuaB5mMCWYKHCpy3rMxIsg 
 提取码：gec2

#### data.js介绍
提供的代码包含一个`MnistData`具有两个公共方法的类：

nextTrainBatch(batchSize)：从训练集中返回随机的一批图像及其标签。
nextTestBatch(batchSize)：从测试集中返回一批图像及其标签。
`MnistData`类还执行重排和规范化数据的重要步骤。

## 开始编码

### 创建文件
在您的工作目录下创建`mnist`文件夹，和`data`文件夹，前者是我们的工作目录，后者要起个静态资源服务，以便我们的data.js加载。
在`mnist`文件夹下创建index.html,和index.js,并且把上面下载的data.js放进去。
在`data`文件夹下放上面下载的`mnist_images.png`和`mnist_labels_uint8`两个文件。


#### 安装依赖

本次将用到`@tensorflow/tfjs`,`@tensorflow/tfjs-vis`,`http-server`,`parcel`这些包，运行下列命令进行安装。

```shell
npm i @tensorflow/tfjs @tensorflow/tfjs-vis --save
npm i -g parcel-bundler http-server
```


工作结束后您的目录应该像这样
```shell
|-node_modules
|-data
    |-mnist_images.png
    |-mnist_labels_uint8
|-mnist
    |--data.js
    |--index.html
    |--index.js
|-package.json
|-package-lock.json
```

### 启动静态服务器
我们先把静态服务器开起来，直接在工作目录下运行：
```shell
hs .\data\ --cors
```
因为我们的端口不一样，加个`--cors`来防止跨域。

#### 修改data.js
data.js里面有两行是加载文件的，需要翻墙才能下载，所以我们将加载的地址替换成我们的静态服务器地址：
将:
```js
    const MNIST_IMAGES_SPRITE_PATH =
    'https://storage.googleapis.com/learnjs-data/model-builder/mnist_images.png';
     const MNIST_LABELS_PATH =
    'https://storage.googleapis.com/learnjs-data/model-builder/mnist_labels_uint8';
```
替换成
```js
const MNIST_IMAGES_SPRITE_PATH =
    'http://127.0.0.1:8080/mnist_images.png';
const MNIST_LABELS_PATH =
    'http://127.0.0.1:8080/mnist_labels_uint8';
```
这样data.js就能帮助我们加载数据了，我们也可以去学习data.js里的代码，以便我们后续创建属于自己加载数据的方法。


## 显示输出数据

### 观察数据
接下来我们来加载我们的训练数据，并且显示到我们的训练板上。我们会把我们的代码用`window.onload`包裹起来，
当然您也可以监听`DOMContentLoaded`事件。
先取出20组的测试数据，在index.js写入：
```
window.onload = () => {
  const data = new MnistData();
  await data.load();
  const examples = data.nextTestBatch(20);
  console.log(examples);
}
```
然后输入shell命令：
```shell
parcel .\mnist\index.html
```
等待编译完成，就能在浏览器看到我们取出来的数据结构。
![dataStyle](./dataStyle.png)

我们需要关注的就是这个张量的数据样式:`shape[20, 784]`。
第一个20表示我们取了20组的数据。
第二个784表示的是28×28×1,前两个28是代表图片的像素点，后面的1表示是黑白图片，因为黑白图片的RGB通道只占一个。
如果是彩色，那就要变成28×28×3。


### 切割数据
我们现在已经取出了数据了，接下来就是要切割成一张一张的图片，下面将用到TensorFlow.js给我们提供的处理数据的API：
[slice](https://js.tensorflow.org/api/2.0.0/#slice)： 这个会帮助我们对张量进行切割，类似于js的splice。
[reshape](https://js.tensorflow.org/api/2.0.0/#tf.Tensor.reshape)： 这个会帮助我们重新定义张量的形状，有利于我们将张量转换成像素显示出来。

```javascript
window.onload = () => {
  const data = new MnistData();
  await data.load();
  const examples = data.nextTestBatch(20);
  const numExamples = examples.xs.shape[0]; // 取出数据的个数
   for (let i = 0; i < numExamples; i += 1) {
       const imageTensor = tf.tidy(() => {
           return examples.xs.slice([i, 0], [1, 784])
                             .reshape([28, 28, 1]);
       });
    }
}
```
我们将数据用[tf.tidy](https://js.tensorflow.org/api/2.0.0/#tidy)包裹起来，他能帮助我们自动清除内存，这样能防止我们在处理大数据的时候，出现内存泄漏。
下面我们会借助TensorFlow.js的[toPixels](https://js.tensorflow.org/api/2.0.0/#browser.toPixels),将数据绘制在画布上。
他对输入数据的格式有要求，所以我们在切割完要调用`reshape([28, 28, 1])`转换数据格式。

### 显示数据
接着我们先在页面上用`canvas`画出我们的数据，并且显示到我们的训练板上。
我们要先调用[tfvis.visor().surface](https://js.tensorflow.org/api_vis/1.4.0/#tfvis.Visor.surface)，来创建一个训练板。
并且创建canvas元素，用[toPixels](https://js.tensorflow.org/api/2.0.0/#browser.toPixels)API,将我们的数据转换成像素，并画出来。
toPixels返回的是一个Promise。
具体代码如下：
````
window.onload = async () => {
  const data = new MnistData();
  await data.load();
  const examples = data.nextTestBatch(20);
  const numExamples = examples.xs.shape[0];
  const surface = tfvis.visor().surface({ name: '输入数据例子',tab:'输入数据' });
  for (let i = 0; i < numExamples; i += 1) {
      const imageTensor = tf.tidy(() => {
          return examples.xs
              .slice([i, 0], [1, 784])
              .reshape([28, 28, 1]);
      });

      const canvas = document.createElement('canvas');
      canvas.width = 28;
      canvas.height = 28;
      canvas.style = 'margin: 3px';
      await tf.browser.toPixels(imageTensor, canvas);
      surface.drawArea.appendChild(canvas);
  }
}
````
如果不出意外，您将看到以下内容：
![inputData](./input-data.png)


## 模型

### 卷积神经网络的定义
卷积神经网络是模拟人视觉的处理过程，它包含的层为
·卷积层
·池化层
·全连接层

#### 卷积层
卷积层可以用来帮助我们提取图像的特征，计算机基于卷积运算来提取特征。
[Image Kernels](https://setosa.io/ev/image-kernels/)这个网站,可以帮助我们理解底层操作。
图像中越白的数值越大，越黑的数据越小，范围为0-255
![data-size](./data-size.png)
接下来我们看看如何用卷积矩阵来提取特征。用一个outline内核为例。

##### outline
outline的特征矩阵为：
[-1 -1 -1]
[-1  8 -1]
[-1 -1 -1]
将这个矩阵乘以像素的值再相加，就能输出一个特征值，它可以帮我们提取图片的轮廓。
![img](./img.png)

不同的内核可以帮我们提取图片不同的特征，我们只需要知道卷积操作是用来帮我们提取特征的就行。
而一个卷积层使用了`多个卷积核`对图像进行卷积操作，因为一个图像的特征是非常丰富的。

>卷积层提取特征参考资料
>https://cs231n.github.io/convolutional-networks/

![strides](./filters.gif)

卷积层训练的结果就是卷积核，我们在模型里需要输入的有:
`kernelSize`: 滑动窗口的大小，如果设置为5，它将指定了一个正方形的5x5卷积窗口。
`filters`: 指定大小为kernelSize的窗口数。
`strides`: 每次走的步长。

#### 池化层
将一个或多个由前趋的卷积层创建的矩阵压缩为较小的矩阵。池化通常是取整个池化区域的最大值或平均值。
池化层有助于帮助我们在输入矩阵中实现`平移不变性`。

>平移不变性：例如，无论一只狗位于画面正中央还是画面左侧，该算法仍然可以识别它。

![pooling](./pooling.png)

池化层也帮助了我们减少了计算量，以前是特征都要计算，现在只要计算最强特征就行了。并且可以间接帮助我们防止过拟合。
我们只需要知道，池化层仅仅是用来帮我们压缩训练的数据，减少计算量，它并没有权重需要训练。

#### 全连接层
全连接层主要是作为输出层，和多分类下作为分类器，是比较常用的。全连接层有权重需要训练。


### 创建模型结构
接下来我们来在代码中定义我们的模型，其实tf.js已经帮我们把API封装好了，我们只需要调用就好了。

#### 定义卷积层
我们添加的模型还是sequential()，连续的模型，第一层先添加一个二维的卷积层，因为我们图片是二维的。
接着上面的代码往下写：
```javaScript
   ...
  const model = tf.sequential();
  model.add(tf.layers.conv2d({
      inputShape: [28, 28, 1],
      kernelSize: 3,
      filters: 8,
      strides: 1,
      activation: 'relu',
      kernelInitializer: 'varianceScaling'
  }));
```
`inputShape: [28, 28, 1]`: 输入数据的结构，分别对应长和宽，后面的1表示RGB占一个通道，为黑白图片。
`kernelSize: 3`: 卷积核大小，像我们上面的矩阵就是3×3的卷积窗口，我们这里设置为5的卷积窗口。
`filters: 8`: 指定大小为kernelSize的窗口数。我们这里用8个。
`strides: 1`: 步长，就是每次移动的步数。
`activation: 'relu'`: 设置激活函数`relu：f(x)=max(0,x)`,他在x小于0的时候输出0，在大于0的时候输出自己。
![relu](./relu.png)
`kernelInitializer: 'varianceScaling'`: 用于随机初始化模型权重的方法，能加快收敛速度。

#### 定义个最大池化层
第二层定义个最大池化层,并且设置两个超参数。接着写代码如下：
```javaScript
  model.add(tf.layers.maxPool2d({
    poolSize: [2, 2],
    strides: [2, 2]
  }));
```
`poolSize: [2, 2]`: 池化的尺寸。
`strides: [2, 2]`: 每次移动的步数。
定义了两层之后我们就已经提取了一轮的特征了，（可以理解为提取了横或竖的特征）我们接着再来定义第二轮的特征。
```javaScript
model.add(tf.layers.conv2d({
    kernelSize: 5,
    filters: 16,
    strides: 1,
    activation: 'relu',
    kernelInitializer: 'varianceScaling'
  }));

  model.add(tf.layers.maxPool2d({
    poolSize: [2, 2],
    strides: [2, 2]
  }));
```
就是将上面两层模型再写一遍，`inputShape`不用再写一次，模型会自动计算出来，但是`filters`要填得大一点，因为我们要提取更多的特征。

### 摊平数据
我们现在的数据是高维数据，卷积操作往往会增加进入其中的数据的大小。
在将它们传递到最终分类层之前，我们需要将数据展平为一个长数组。`tf.layers.flatten()`可以帮助我们拍平数组。
这是到达最后一层：`dense`层进行分类的最普遍的操作。
```javaScript
  model.add(tf.layers.flatten());
```

>平坦层中没有权重。它只是将其输入展开为一个长数组。

#### 全连接层(dense)
这是最后一层，我们需要先设置一下神经元个数`units:10`,因为我们输出的分类是10个。
设置激活函数`softmax`,这个函数也称为归一化指数函数，它能将一个含任意实数的K维向量z“压缩”到另一个K维实向量σ(z)中，
使得每一个元素的范围都在(0,1)之间，并且所有元素的和为1。
设置层的初始化方法:`varianceScaling`。具体代码如下：
```jacaScript
  model.add(tf.layers.dense({
    units: 10,
    activation: 'softmax',
    kernelInitializer: 'varianceScaling'
  }))
```

## 训练
我们的卷积模型已经定义好了，下一步就是要来设置一下损失函数和优化器。
第二步就是准备训练的数据，第三步就是可视化训练过程。

### 设置损失函数和优化器
在`compile`中设置交叉熵损失函数:`categoricalCrossentropy`，设置了一阶梯度优化：`自适应矩估计（Adam）`，
设置度量单位，准确度：`accuracy`。
```js
  model.compile({
    loss: 'categoricalCrossentropy',
    optimizer: tf.train.adam(),
    metrics: ['accuracy']
  })
```
接下来是准备数据.
### 准备要训练的数据
这是第二步，我们需要准备训练集和验证集。

#### 取出训练集
有一点要注意的是我们操作张量(tensor)的时候，要放在tidy中,它会帮我们清除两边的张量(tensor),减少干扰。
并且在执行完之后清除由分配的所有中间张量(tensor)。
取出500个训练集，具体看您机器性能。
```javaScript
  const [trainXs, trainYs] = tf.tidy(() => {
    const d = data.nextTrainBatch(500);
    return [
      d.xs.reshape([500, 28, 28, 1]), // 改变数据的形状，变成适合我们模型的形状。
      d.labels
    ];
  })
```

#### 取出验证集
取出100个验证集.验证集可以看看训练得咋样，有没有过拟合或欠拟合。
```js
  const [testXs, testYs] = tf.tidy(() => {
    const d = data.nextTestBatch(100);
    return [
      d.xs.reshape([100, 28, 28, 1]),
      d.labels
    ];
  });
```


### 调用tfvis可视化训练过程
接下来就是加载我们的训练集和验证集了。

```js
  await model.fit(trainXs, trainYs, {
    validationData: [testXs, testYs],
    batchSize: 50, // 一次训练多少个
    epochs: 20, // 训练几轮
    callbacks: tfvis.show.fitCallbacks(
        { name: '训练效果' },
        ['loss', 'val_loss', 'acc', 'val_acc'],
        { callbacks: ['onEpochEnd'] } // 只想看到onEpochEnd
    )
  });
```
`'loss', 'val_loss'`表示的是要显示训练集和验证集的损失。
`'acc', 'val_acc'` 表示要显示训练集和验证集的精确度。

接下来就可以观察到我们的结果了。启动命令：
>parcel .\mnist\index.html

![loo](loo.png)
因为机器的原因，我们的误差还是很难降下来，您可以尝试增加训练数据来减少误差。

### 进行预测
我们的渣渣模型已经训练好了，很期待它会对我们写的数字作何反应。
我们接下来就要在网页上用canvas写出数字，并且转换为张量，然后输入模型进行预测。
直接上代码,先来HTML的代码：
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Document</title>
</head>
<body>
  <canvas width="300" height="300" style="border: 2px solid #666;"></canvas>
<br>
<button onclick="clear();" style="margin: 4px;">清除</button>
<button onclick="predict();" style="margin: 4px;">预测</button>
  <script src="./index.js"></script>
</body>
</html>
```

接下来写clear和predict方法，它们需要挂载到window上。
```html

  const canvas = document.querySelector('canvas');

  canvas.addEventListener('mousemove', (e) => { // 当鼠标划过的时候
    if (e.buttons === 1) { // 如果按着左键
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = 'rgb(255,255,255)'; // 白的字
      ctx.fillRect(e.offsetX, e.offsetY, 25, 25);
    }
  });

  window.clear = () => {
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = 'rgb(0,0,0)'; // 设置黑底
    ctx.fillRect(0, 0, 300, 300); // 填充大小
  };

  clear(); // 每次初始化的时候都清空一下

  window.predict = () => {
    const input = tf.tidy(() => {
      return tf.image.resizeBilinear(
        tf.browser.fromPixels(canvas), // 将canvas转换为张量
        [28, 28], // 将300×300 的图片转换为28×28
        true // 设置4个边角
      ).slice([0, 0, 0], [28, 28, 1]) // 将彩色图片转换为黑白图片，删除了RGB另外两个通道
        .toFloat() // 转换为float
        .div(255) // 除去255，进行归一化处理
        .reshape([1, 28, 28, 1]); // 将张量变成输入的形状，要跟输入数据保查一致
    });
    const pred = model.predict(input).argMax(1); // 进行预测
    alert(`预测结果为 ${pred.dataSync()[0]}`); // 转换为普通数据结构，不然是个数组
  };
```
接下来就可以开心的进行预测了。
![预测](./yc.png)
因为我们的训练数据并不是很多，所以预测的成功率大约只有70%.(很多7都识别成1)。

感谢看到最后。

### 结束语
草色烟光残照里，无言谁会凭阑意。
「蝶恋花·伫倚危楼风细细」
柳永








