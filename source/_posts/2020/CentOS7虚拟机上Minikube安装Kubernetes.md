---
title: CentOS7虚拟机上`Minikube`安装Kubernetes
date: 2020-01-26 23:37:17
tags: Docker Kubernetes
index_img: /2020/01/26/CentOS7虚拟机上Minikube安装Kubernetes/kubernetes.png
---

### 前言

写这篇文章的原因是因为部署的时候遇到很多坑，而且我一个接着一个的跳进去，这篇文章为了防止再跳进去，希望这篇文章能帮到你。

> 注意：本文只是建议，查阅时请带有主观意见和独立思考。

### 确保有安装环境

你需要有`docker`，`kubectl`，`minikube`环境。
具体推荐阿里云的这篇文章[Minikube - Kubernetes 本地实验环境](https://yq.aliyun.com/articles/221687)。
或者直接进入[官方文档](https://kubernetes.io/zh/docs/tasks/tools/)。

这一定难不倒你。

### 入坑

我一开始看[官方文档](https://minikube.sigs.k8s.io/docs/start/linux/)，里的安装教程，由于我是在 VM 虚拟机中运行的
所以就要使用 sudo minikube start --vm-driver=none
于是开始报错：无法拉取镜像，开启 cluster 时出错。
记得每一次构建失败都要执行`minikube delete`

#### 拉取镜像应该采用镜像储存库

    minikube start --image-repository=registry.cn-hangzhou.aliyuncs.com/google_containers

如果这样可以那么恭喜你，可以关闭本文章继续学习了。
如果执行失败可以换成阿里云给出的解决方案。
下面代码中的`https://xxxxxx.mirror.aliyuncs.com`，你需要去阿里云[容器镜像服务>镜像加速地址](https://cr.console.aliyun.com/cn-beijing/instances/mirrors),来获取您的加速器。
你还可以顺便给 docker 配置个镜像加速器

![阿里云图片](./aliyun.png)

```shell
minikube start --image-mirror-country cn \
--iso-url=https://kubernetes.oss-cn-hangzhou.aliyuncs.com/minikube/iso/minikube-v1.6.0.iso \
--registry-mirror=https://xxxxxx.mirror.aliyuncs.com
```

> 我到这一步还是不行

### 如果出现无法拉取镜像

```shell
🚜  拉取镜像 ...
❌  无法拉取映像，有可能是正常状况：running cmd: "/bin/bash -c \"
sudo env PATH=/var/lib/minikube/binaries/v1.17.0:$PATH
kubeadm config images pull --config /var/tmp/minikube/kubeadm.yaml\"": /bin/bash -c "
sudo env PATH=/var/lib/minikube/binaries/v1.17.0:$PATH
kubeadm config images pull --config /var/tmp/minikube/kubeadm.yaml": exit status 1
```

#### 可以选择翻墙

可以把物理机的翻墙工具设置成全局，相信对你来说不是难事。

##### 如果您在 CentOS 虚拟机上安装了 shadowsocks

关闭代理，用您的物理机来代理

    while read var; do unset $var; done < <(env | grep -i proxy | awk -F= '{print $1}')

> 到此我解决了无法拉取镜像问题

### 遇到了开启 cluster 时出错

    💣  开启 cluster 时出错: init failed. cmd: "/bin/bash -c \"sudo env PATH=/var/lib/minikube/binaries/v1.17.0:$PATH kubeadm init --config /var/tmp/minikube/kubeadm.yaml  --ignore-preflight-errors=DirAvailable--etc-kubernetes-manifests,DirAvailable--var-lib-minikube,DirAvailable--var-lib-minikube-etcd,FileAvailable--etc-kubernetes-manifests-kube-scheduler.yaml,FileAvailable--etc-kubernetes-manifests-kube-apiserver.yaml,FileAvailable--etc-kubernetes-manifests-kube-controller-manager.yaml,FileAvailable--etc-kubernetes-manifests-etcd.yaml,Port-10250,Swap\"": /bin/bash -c "sudo env PATH=/var/lib/minikube/binaries/v1.17.0:$PATH kubeadm init --config /var/tmp/minikube/kubeadm.yaml  --ignore-preflight-errors=DirAvailable--etc-kubernetes-manifests,DirAvailable--var-lib-minikube,DirAvailable--var-lib-minikube-etcd,FileAvailable--etc-kubernetes-manifests-kube-scheduler.yaml,FileAvailable--etc-kubernetes-manifests-kube-apiserver.yaml,FileAvailable--etc-kubernetes-manifests-kube-controller-manager.yaml,FileAvailable--etc-kubernetes-manifests-etcd.yaml,Port-10250,Swap": exit status 1
    stdout:
    [init] Using Kubernetes version: v1.17.0
    [preflight] Running pre-flight checks

    stderr:
    W0127 01:14:50.575416    7722 common.go:77] your configuration file uses a deprecated API spec: "kubeadm.k8s.io/v1beta1". Please use 'kubeadm config migrate --old-config old.yaml --new-config new.yaml', which will write the new, similar spec using a newer API version.
    W0127 01:14:50.576165    7722 common.go:77] your configuration file uses a deprecated API spec: "kubeadm.k8s.io/v1beta1". Please use 'kubeadm config migrate --old-config old.yaml --new-config new.yaml', which will write the new, similar spec using a newer API version.
    W0127 01:14:50.578306    7722 validation.go:28] Cannot validate kube-proxy config - no validator is available
    W0127 01:14:50.578334    7722 validation.go:28] Cannot validate kubelet config - no validator is available
        [WARNING IsDockerSystemdCheck]: detected "cgroupfs" as the Docker cgroup driver. The recommended driver is "systemd". Please follow the guide at https://kubernetes.io/docs/setup/cri/
        [WARNING Hostname]: hostname "minikube" could not be reached
        [WARNING Hostname]: hostname "minikube": lookup minikube on 192.168.180.2:53: no such host
    error execution phase preflight: [preflight] Some fatal errors occurred:
        [ERROR FileContent--proc-sys-net-bridge-bridge-nf-call-iptables]: /proc/sys/net/bridge/bridge-nf-call-iptables contents are not set to 1
    [preflight] If you know what you are doing, you can make a check non-fatal with `--ignore-preflight-errors=...`
    To see the stack trace of this error execute with --v=5 or higher

#### 解决问题

它提示我们

    [ERROR FileContent--proc-sys-net-bridge-bridge-nf-call-iptables]:
    /proc/sys/net/bridge/bridge-nf-call-iptables contents are not set to 1

##### 输入命令

    echo "1" >/proc/sys/net/bridge/bridge-nf-call-iptables
    swaoiff-a

然后 vim /etc/fstab，注释掉下面这一行：

```shell script

#/dev/mapper/rhel-swap   swap                    swap    defaults        0 0

```

查看是否成功
free -m
free 那边是 0 就是成功。

##### 重新构建

    minikube delete
    minikube start --image-repository=registry.cn-hangzhou.aliyuncs.com/google_containers

> 到此我解决了所有问题。如果有人带我觉得这就是几分钟的事情。

### 成功图

![](./success.png)

#### 如果执行 minikube dashboard 出现 503

请将您的虚拟机升到 8G 的运行内存

### 如果 kubectl 出现连接超时或不可达

像这样

    The connection to the server <server-name:port> was refused - did you specify the right host or port?

而且使用 curl 的时候像这样

    Could not resolve proxy: http//127.0.0.1; 未知的错误

请检查您的代理，可以注释掉，运行 vi /etc/profile

> http_proxy=http://代理地址:端口
> ssl_proxy=http://代理地址:端口

如果看到这样的地址请注释掉

### 结束语 😋

> 注意：以上问题是具体问题，请根据具体问题具体分析，仅供参考。

如果有问题请留言，第一时间回复。
现在凌晨 1：33，饿了。

长歌吟松风，曲尽河星稀。
「下终南山过斛斯山人宿置酒」
李白
