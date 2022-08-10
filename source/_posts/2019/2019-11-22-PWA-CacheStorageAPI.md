---
title: PWA-CacheStorageAPI
date: 2019-11-22 13:42:15
tags: Progressive Web App
index_img: /2019/11/22/2019-11-22-PWA-CacheStorageAPI/cacheStorage.png
---
>[《PWA实战》](https://github.com/TalAter/gotham_imperial_hotel)记录。[以]塔勒·埃特尔 著 张俊达 译

<br>

### CacheStorage API


CacheStorage是一种全新的缓存层，你拥有完全的控制权。(遵循[同源策略](https://baike.baidu.com/item/同源策略))

<br>

#### 在CacheStorage中储存请求

示例：
	
	//serviceworker.js
	self.addEventListener("install",function(event){
	       event.waitUntil(
	        caches.open("gih-cache").then(function(cache){
	            return cache.add('/index-offline.html');
	        })
	       );
	});
	
首先我们来理解一下新的命令
`caches.open()` : 
打开并返回一个现有的缓存，如果没有找到对应名称的缓存，就创建它并返回。(并且它返回的是一个用promise包裹的cache对象。)

`cache.add()` : 
这个方法将请求文件并将文件放入缓存中，传入的参数就是对应的键名。
在install事件中，通过`waitUntil`等待缓存完成，确保了在整个链条中如果遇到任何问题，service sorker都不会被安装。

<br>

#### 在CacheStorage中取回请求

示例：
	
	//servicesocker.js  
	self.addEventListener("fetch",function(event){
	    event.respondWith(
	        fetch(event.request).catch(function(){
	            return caches.match("/indedx-offline.html");
	        })
	    );
	});

新的命令：
`match(request,[options])` : 
第一个参数是需要在缓存中寻找的内容，可以是request对象或者URL。
第二个参数是非必传的选项对象。（比如 caches.match(event.request,{`ignoreSearch:true`} 这样将会匹配到请求的URL，同时忽略查询的参数。 ）
`match`返回的是一个pormise，由`resolve`方法包裹的在缓存中找到的第一个response对象。当找不到任何内容时，它返回
undefined。
因为在找不到内容时，返回的pormise也不会进入`reject`,所以应该在返回之前判断是否找到匹配。
	
	//就像这样
	caches.match("/login.png").then(function(response){
		if(response){
		return response;
		}
	});

<br>

#### 缓存多个请求

示例：
	
	//servicesocker.js  
	const CACHE_NAME = "gih-cache";
	const CACHED_URLS = [
	    "index-offline.html",
	    "https:maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css",
	    "/css/gih-offline.css",
	    "/img/jumbo-background-sm.jpg",
	    "/img/logo-header.png"
	];
	 
	self.addEventListener("install",function(event){
	       event.waitUntil(
	        caches.open(CACHE_NAME).then(function(cache){
	            return cache.addAll(CACHED_URLS);
	        })
	       );
	})
	
新的命令：
`cache.addAll()` : 
与cache,add()类似，但是其接收的是一组URL，并全部储存到缓存，如果任何一个请求失败，将会返回`promise.reject`。

<br>

#### 接收每个请求

示例：
	
	//servicesocker.js  
	self.addEventListener("fetch",function(event){
	    event.respondWith(
	        fetch(event.request).catch(function(){
	            return caches.match(event.request).then(function(response){
	                if(response){
	                    return response;
	                }else if(event.request.header.get("accept").includes("text/html")){
	                    return caches.match("/index-offline.html");
	                }
	            });
	        })
	    );
	});

在这个请求中，新的fetch事件仍然试图向网络发起请求权，但是如果请求失败，则继续处理catch块中的函数。

<br>

##### `陷阱`

通过传递request对象（例如：caches.match(event.request)）来查找缓存中的条目有一个潜在的陷阱需要注意。
例如：您的网站有一个爆款活动，用户从a页面点击进入活动页面，
您缓存的内容长这样（`https://waterbang.top/activity.html?source=a`）。
用户从b页面点击进入，您的内容长这样（`https://waterbang.top/activity.html？id=2&source=b`）。
如果您从a页面使用caches.match(event.request),尝试去寻找(`/activity.html?source=a`),会找不到任何内容。
如果你可以确保查询字符串对于页面内容不会产生影响。可以使用ignoreSearch选项，通知match() 方法忽略字符串查询。
	
	caches.match(event.request,{ignoreSearch: true})

这样会匹配到请求的URL的条目，同时会忽略查询参数。

<br>

### HTTP缓存和HTTP头

CacheStorage不能取代过去的HTTP缓存。
如果你的服务器提供的文件包含一个HTTP头，说明该文件可以缓存一年（`Cache-Control: max-age=31536000`）,
游览器就会一直使用游览器缓存来提供这个文件。
如果你在一周之后更新了main.css并且打算更新service worker，让其重新调用cache.addAll(["./main.css"]),那么该文件会从游览器缓存中返回，而不是网络中返回

<br>

### 缓存管理，清除旧缓存

我们不仅要创建缓存，还应该负责的处理不再需要的旧资源缓存
熟悉新的命令：
`caches.delete(cacheName) `:
接收一个缓存名字做为参数，并删除对应的缓存。

`caches.keys()` :
该函数能获取所有的缓存名称，返回一个promise，成功的时候会得到一个包含缓存名称的数组。
    
    caches.keys().then(function(){
        cacheName.forEach(function(cacheName){
            caches.delete(cacheName);
        })
    })
 
 <br>
 
 ##### 我们如何管理我们的缓存
 
 任何时候，我们的应用最多需要两份缓存，一份是当前激活的service worker,
 另外一份是正在安装但是未激活的service worker（如果存在的话）。
 我们上面的缓存请求的代码已经完成了，接下来我们要实现：当新的service worker激活的时候，
 安全清除旧的service worker创建的缓存。
 我们可以在serviceworker.js文件底部，添加一个新的监听事件来完成 ——`activate`事件
 
    //servicesocker.js  
    self.addEventListener("activate",function(event) {
      event.waitUntil(
        caches.keys().then(function(cacheNames){
          return Promise.all(
            cacheNames.map(function(cacheName){
              if(CACHE_NAME !== cacheName && cacheName.startsWith("git-cache")){
                return caches.delete(cacheName);
              }
            })
          );
        })
      );
    });

让我们看看我们的代码
首先我们用`event.waitUntil`,来让service worker 完成激活之前，先等待我们删除旧的缓存。
由于caches.keys返回的是一个promise,其成功时会返回一个数组，该数组包含所有缓存的名称。
我们需要拿到这个数组，然后创建一个promise，来迭代数组中的每个缓存（_Array.map()_），并且用Promise.all()返回。

Promise.all() 接收一个promise数组，并且返回一个单独的promise，如果数组中的任何一个promise返回失败（reject）,
那么这整个都会创建失败，只有全部完成才会返回完成。

<br>

#### 重用已缓存的响应

当我们每次去安装service worker的时候，都会去创建一份新的缓存。这样是低效的，我们如果可以在创建新缓存的时候，
先去遍历一遍不可变文件的列表，然后从现有的缓存中复制到新的缓存。
    
    //serviceworker.js
    const immutableRequests = [ //我们的不可变资源
      "/fancy_header_background.mp4",
      "vendor/bootstrap/3.3.7/bootstrap.min.css",
      "/css/style-v355.css"
    ];
    const mutableRequest = [ //每次创建新缓存都要去网络中请求的URL
      "app-settings.json",
      "index.html"
    ];
    
    self.addEventListener("install",function(event){
      event.waitUntil(caches.open("cache-v2")).then(function(cache){
        let newImmutableRequests =[];
        return Promise.all(
          immutableRequests.map(function(url){
            return caches.match(url).then(function(response){
              if(response){
                return response;
              }else{
                newImmutableRequests.push(url);
                return Promise.resolve();
              }
            });
          })
        ).then(function(){
          return cache.addAll(newImmutableRequests.concat(mutableRequest));
        });
      });
    });

在大部分的service worker中，上面这种模式是适用的，但是作者给我们提供了一种更加方便的方法。

    importScript(cache.adderall.js);
    self.addEventListener("install",function(event){
        event.waitUntil(
            caches.open("cache-v2").then(function(cache){
                return adderall.addAll(cache,IMMUTABLE_URLS<MUTABLE_URLS);
            })
        )
    })
    
点击[cache.adderall](https://github.com/TalAter/cache.adderall)，进一步了解。

#### 结束🐟

>清晨入古寺，初日照高林。——「题破山寺后禅院」  常建
           