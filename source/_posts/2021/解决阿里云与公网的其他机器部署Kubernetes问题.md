---
title: 解决阿里云与公网的其他机器部署Kubernetes问题
date: 2021-03-31 14:25:36
tags: Kubernetes
index_img: /2020/01/26/CentOS7虚拟机上Minikube安装Kubernetes/kubernetes.png
---

## 前言

由于阿里云的公网 ip 绑定的网卡在外层网关，所以机器地监听不到

### 基本环境得安装

#### Debian / Ubuntu

```shell
apt-get update && apt-get install -y apt-transport-https
curl https://mirrors.aliyun.com/kubernetes/apt/doc/apt-key.gpg | apt-key add -
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb https://mirrors.aliyun.com/kubernetes/apt/ kubernetes-xenial main
EOF
apt-get update
apt-get install -y kubelet kubeadm kubectl
```

> 另外，你也可以指定版本安装
> apt-get install kubectl=1.19.3-00 kubelet=1.19.3-00 kubeadm=1.19.3-00

#### CentOS / RHEL / Fedora

```shell
cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF
setenforce 0
yum install -y kubelet kubeadm kubectl
systemctl enable kubelet && systemctl start kubelet
```

## Main

**_ 下面代码除特殊说明的 x.x.x.x 都是您的 master 节点公网地址 _**

### 构建 etcd

k8s 1.8 版本后，允许分段构建，所以我们要先构建一下 etcd phase。执行下面代码

```shell
kubeadm init phase etcd local
```

您需要**打开两个终端**，一个执行 `kubeadm init ...` 也就是下面创建集群的代码,此时会卡住。
另一个需要修改`etcd.yaml`里面的`listen-client-urls`和`listen-peer-urls`，具体看下面代码，

### 第一个终端创建集群

```shell
kubeadm init --image-repository=registry.aliyuncs.com/google_containers --apiserver-advertise-address=x.x.x.x --service-cidr=10.1.0.0/16  --pod-network-cidr=10.244.0.0/16
```

执行完第一个窗口会卡住，接着切换 master 的到第二个终端，执行下面代码。

### 第二个终端修改 etcd 监听地址

```shell
#第二个终端执行
vim /etc/kubernetes/manifests/etcd.yaml
```

#### 第二个终端原来的内容：

```shell
#······ more
  - --client-cert-auth=true
    - --data-dir=/var/lib/etcd
    - --initial-advertise-peer-urls=https://x.x.x.x:2380
    - --initial-cluster=master=https://x.x.x.x:2380
    - --key-file=/etc/kubernetes/pki/etcd/server.key
    - --listen-client-urls=https://127.0.0.1:2379,https://x.x.x.x:2379
    - --listen-metrics-urls=http://127.0.0.1:2381
    - --listen-peer-urls=https://x.x.x.x:2380
    - --name=master
#······ more
```

#### 第二个终端修改后的内容：

```shell
#······ more
  - --client-cert-auth=true
    - --data-dir=/var/lib/etcd
    - --initial-advertise-peer-urls=https://x.x.x.x:2380
    - --initial-cluster=master=https://x.x.x.x:2380
    - --key-file=/etc/kubernetes/pki/etcd/server.key
    - --listen-client-urls=https://127.0.0.1:2379
    - --listen-metrics-urls=http://127.0.0.1:2381
    - --listen-peer-urls=https://127.0.0.1:2380
    - --name=master
#······  more
```

稍等一会，第一个窗口 `kubeadm init ...`就执行成功了。

### 执行成功，终端会提醒我们执行下面命令

```shell
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

#### 将 worker 加入集群

接着在 worker 节点 执行 `kubeadm join` 的代码， token 有效期默认 2 小时。

### 查看加入的节点

```shell
kubectl get ndoes
```

会查看到 master 节点和 node 节点都是 NotReady 状态。

### 接着就需要安装网络环境

#### 在 master 节点和 node 节点都安装 flannel 插件

```shell
 kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
```

## 如果遇到错误就看日志

### 执行下面命令看看是否都处于 runing 状态

```shell
kubectl get pods --all-namespaces
```

看 kubelet

```shell
journalctl -f -u kubelet
```

### pod 一直 CrashLoopBackOff

看看 log 对症下药

```shell
kubectl logs pod-name
```

看看是不是有缺少什么东西，如果缺少了就从 master 节点复制,如：

### The connection to the server localhost:8080 was refused - did you specify the right host or port?

```shell
# 这命令在 master 节点执行，x.x.x.x为你报错的节点的公网ip
scp /etc/docker/daemon.json root@x.x.x.x:/etc/docker/daemon.json
```

或者前往 对于的[github issuse](https://github.com/kubernetes/kubernetes/issues/50295)

### failed: open /run/systemd/resolve/resolv.conf: no such file or directory

```shell
## 复制master的文件
scp /run/systemd/resolve/resolv.conf root@x.x.x.x:/run/systemd/resolve/resolv.conf
systemctl daemon-reload
```

### /sys/fs/cgroup/pids/system.slice/etcd.service: no such file or directory

```shell
 vim /etc/docker/daemon.json
vim /run/flannel/subnet.env
```

### network plugin is not ready: cni config uninitialized

```shell
vim /etc/cni/net.d/10-flannel.conflist
##输入下面内容
{
  "name": "cbr0",
  "cniVersion": "0.3.1",
  "plugins": [
    {
      "type": "flannel",
      "delegate": {
        "hairpinMode": true,
        "isDefaultGateway": true
      }
    },
    {
      "type": "portmap",
      "capabilities": {
        "portMappings": true
      }
    }
  ]
}

```

### network: /run/flannel/subnet.env is missing FLANNEL_NETWORK

```shell
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
kubectl get pods --all-namespaces
```

> 排错技巧，[kubeadm 进行故障排查](https://kubernetes.io/zh/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/)， [Kubernetes 常用命令](https://www.jianshu.com/p/2ded3a8cc788).
