# 个人博客

> 地址：https://waterbang.top

![alt text](source/_posts/2024/FEDAY/halou.jpg)

这里是发表个人观点，保存个人记录的地方，并且应该，大约，也许，有可能每年会有一篇年终总结。


### hexo docs

[hexo docs](https://hexo.io/zh-cn/docs/commands)


### 常用命令

- `hexo clean` - 清理缓存
- `hexo generate` - 生成静态文件
- `hexo server` - 启动服务器
- `hexo deploy` - 部署网站
- `hexo new "文章标题"` - 新建文章
- `hexo help` - 查看帮助

### 自动部署

使用 Node.js 24（版本记录在 `.nvmrc`），首次安装执行 `npm ci`，本地构建执行 `npm run build`。

将代码推送到 `main` 后，GitHub Actions 的 `Pages` 工作流会安装锁定依赖、构建 `public/` 并发布到 GitHub Pages。仅执行本地 commit 不会触发发布；也可以在 Actions 页面手动运行该工作流。

在仓库 Actions 页面确认 build 和 deploy 均成功后，访问 https://waterbang.top 检查结果。此流程无需手动执行 `npm run d` 或推送 `gh-pages` 分支。
