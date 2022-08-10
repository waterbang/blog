---
title: 小程序使用组件实现tarBar隐藏显示
date: 2020-10-28 16:59:38
tags: 小程序
index_img: /2020/10/28/小程序使用组件实现tarBar隐藏显示/direction.png
---

### 前言

本篇文章解决场景：

**您的小程序有个需求，就是切换tarBar的时候实现隐藏。如果您使用过中转页面实现跳转，会在安卓机上发现有明显的白屏。**

> 以下代码可直接复制粘贴，只需要将tarbar数据换成自己的

![gif](./gif.gif)


### 配置自定义tarbar

在项目的app.json，的tarBar对象内添加配置：`custom:true`，代码如下：
```json
.....
"tabBar": {
    "custom": true,  // +++
    "backgroundColor": "#fafafa",
    "borderStyle": "white",
    "selectedColor": "#e14739",
    "color": "#404040",
.....
```

### 创建custom-tar-bar组件

创建结构如下：
```
compoment
├── custom-tab-bar
│   ├── index.js
│   ├── index.json
│   ├── index.wxml
│   └── index.wxss
```

#### wxml
编辑wxml页面，代码如下：
```
<cover-view class="tab-bar">
  <cover-view class="tab-bar-border"></cover-view>
  <cover-view wx:for="{{list}}" wx:key="index" class="tab-bar-item" data-path="{{item.pagePath}}" data-index="{{index}}" bindtap="switchTab">
    <cover-image src="{{_index === index ? item.selectedIconPath : item.iconPath}}"></cover-image>
    <cover-view style="color: {{_index === index ? selectedColor : color}}">{{item.text}}</cover-view>
  </cover-view>
</cover-view>
```

#### wxss
样式代码如下：

``` wxss
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 48px;
  background: white;
  display: flex;
  padding-bottom: env(safe-area-inset-bottom);
}

.tab-bar-border {
  background-color: rgba(0, 0, 0, 0.33);
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 1px;
  transform: scaleY(0.5);
}

.tab-bar-item {
  flex: 1;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}

.tab-bar-item cover-image {
  width: 27px;
  height: 27px;
}

.tab-bar-item cover-view {
  font-size: 10px;
}
```

#### json
json页面不用动，代码如下：

```
{
  "component": true,
  "usingComponents": {}
}
```

#### js页面
js页面需要注意一下，因为我们要实现隐藏页面，所以我们需要创建个空页面来当我们要实际跳转页面的替身（替身稻草人）。
并且，在我们点击跳转的时候，会触发`switchTab()`函数，我们在函数中拦截一下这个跳转，让他跳转到我们真正要去的页面。

> data里面的数据，就是你app.json里，tarbar的数据

```
Component({
  properties: {
    _index: Number
  },
  data: {
    color: "#7A7E83",
    selectedColor: "#666666",
    list: [
      {
        pagePath: "",
        iconPath: "",
        selectedIconPath: "",
        text: "首页",
      },
      {
        pagePath: "/pages/yinchang/index/index", // 实际上不会跳这个页面
        iconPath: "",
        selectedIconPath: "",
        text: "需要隐藏的页面",
      },
      {
        pagePath: "",
        iconPath: "",
        selectedIconPath: "",
        text: "我的",
      }
    ]
  },
  methods: {
    switchTab(e) {
      const data = e.currentTarget.dataset
      const url = data.path
      if (data.index === 1) { // 拦截跳转
        wx.navigateTo({
          url: '/pages/create/create', // 实际上跳转的页面，并且能返回
        })
      } else {
        wx.switchTab({url})
      }
    }
  }
})

```

到此组件创建完毕

### 引入页面
在您需要显示的页面，引入上面创建的组件，举例一个home页面.

#### json引入

```
  "navigationBarTitleText": "首页",
  "usingComponents": {
    "custom-tab-bar": "/compoment/custom-tab-bar/index"
  }
```

#### wxml使用
由于我们首页的索引是0，所以给组件传0，避免点击效果渲染错误。（举一反三）
```
<custom-tab-bar _index="0"></custom-tab-bar>
```

到此功能就结束了，希望有快速解决您的需要。
如果有其他问题请留言，我会继续补充。

### 结束语
但年年燕子，晚烟斜日。
「满江红·金陵乌衣园」
吴潜