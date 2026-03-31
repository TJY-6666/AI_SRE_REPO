# AI SRE Watchdog - 工作坊完整指南

本项目展示了如何将一个基于 Python 的 AI 安全日志分析系统（包含日志生成器 `log-generator` 和接收器 `log-receiver`），从本地虚拟环境运行、Docker 容器化，到最终部署在 Google Kubernetes Engine (GKE) 上的完整链路。

---

## 目录
1. [阶段一：本地环境搭建与测试](#阶段一本地环境搭建与测试)
2. [阶段二：Docker 容器化与网络配置](#阶段二docker-容器化与网络配置)
3. [阶段三：部署到 Google Cloud (GKE)](#阶段三部署到-google-cloud-gke)

---

## 阶段一：本地环境搭建与测试
在开始使用容器前，我们先确保代码能在本地机器上正常运行。这需要为每一个服务创建一个独立的 Python 虚拟环境。

### 1. 创建并激活虚拟环境
请在对应的服务文件夹内（如 `log_receiver_folder`）运行以下命令：
```powershell
# 创建名为 venv 的虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate
# 如果是 Mac/Linux，请使用: source venv/bin/activate
```

### 2. 安装依赖
确保文件夹内提供了 `requirements.txt`：
```powershell
pip install -r requirements.txt
```

### 3. 运行服务
启动应用：
```powershell
python app.py
```
启动成功后，打开浏览器访问 [http://localhost:5000/](http://localhost:5000/)，即可查看前端面板。

---

## 阶段二：Docker 容器化与网络配置
接下来我们将两个应用打包进 Docker 镜像，并在同一台电脑上使用 Docker 网络让它们互相通信。

### 1. 编写与构建镜像
你需要为每个服务准备好 `Dockerfile`，然后构建它们（注意后面的 `.` 代表当前目录）：
```powershell
# 在 receiver 目录下构建:
docker build -t log_receiver_image:v1 .

# 在 generator 目录下构建:
docker build -t log_generator_image:v1 .
```

### 2. 创建 Docker 专属网络
为了让两个容器能通过名字互相访问，我们需要创建一个自定义桥接网络：
```powershell
docker network create sre-network
```

### 3. 运行容器
首先运行 Receiver 服务（并暴露 `5000` 端口供本地访问）：
```powershell
docker run -d --name log_receiver_container --network sre-network -p 5000:5000 log_receiver_image:v1
```

接着运行 Generator 服务，并通过环境变量注入 Receiver 的网络地址：
```powershell
docker run -it --name log_generator_container --network sre-network -e SERVICE_B_URL="http://log_receiver_container:5000/logs" log_generator_image:v1
```

---

## 阶段三：部署到 Google Cloud (GKE)
本地测试完美后，现在我们将应用部署到真正的云环境中。

### 1. 准备云端资源 (GCP Console)
- 去 Google Cloud 控制台创建一个供储存镜像的 **Artifact Registry (GAR)** 仓库。
- 去 GKE 控制台创建一个 **Autopilot 模式的 Kubernetes Cluster**。
- 为你的 K8s 编写好需要用到的 `yaml` 部署文件。

### 2. 授权与打标签 (Tag)
先配置本地 Docker 具有向 GCP 推送镜像的权限：
```powershell
gcloud auth configure-docker us-central1-docker.pkg.dev
```

将刚在本地做好的 Docker 镜像打上 GAR 的远程标签（格式为 `<REGION>-docker.pkg.dev/<PROJECT_ID>/<REPO_NAME>/<IMAGE_NAME>:<TAG>`）：
```powershell
docker tag log_generator_image:v1 us-central1-docker.pkg.dev/gen-lang-client-0205187891/docker-dryrun-repo/log_generator_image:v1

docker tag log_receiver_image:v1 us-central1-docker.pkg.dev/gen-lang-client-0205187891/docker-dryrun-repo/log_receiver_image:v1 
```

### 3. 推送镜像 (Push)
把镜像正式上传到 Google 云端：
```powershell
docker push us-central1-docker.pkg.dev/gen-lang-client-0205187891/docker-dryrun-repo/log_receiver_image:v1

docker push us-central1-docker.pkg.dev/gen-lang-client-0205187891/docker-dryrun-repo/log_generator_image:v1 
```

### 4. 连接云端 K8s 集群
取得控制这间云端“厂房”的主权钥匙（凭证）：
```powershell
gcloud container clusters get-credentials docker-dryrun-cluster --region us-central1 --project gen-lang-client-0205187891
```

### 5. 部署应用并观察状态
一次性应用我们写好的 `yaml` 规则来启动 Pod 和 Service：
```powershell
kubectl apply -f k8s/
```

使用观察模式，等待 Pod 状态变为 `Running`：
```powershell
kubectl get pods -w
```
*(按下 `Ctrl + C` 可以退出观察模式)*

### 6. 云端端口转发测试
集群跑起来后，因为我们还没有配置 LoadBalancer 或 Ingress 对外暴露它，可以先通过端口转发（Port Forwarding）把云端服务印到本地电脑上：
```powershell
kubectl port-forward svc/log-receiver-svc 5000:5000 
```
此时你再次打开浏览器的 [http://localhost:5000/](http://localhost:5000/)，看到的将是在云端集群里飞驰的 AI 监控面板了！🎉
