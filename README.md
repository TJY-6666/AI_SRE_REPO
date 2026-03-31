# AI SRE Watchdog - 新手从零开始工作坊指南

欢迎来到本次工作坊！本项目展示了如何将一个基于 Python 的 AI 安全日志分析系统（包含日志生成器和接收器），从本地运行、Docker 容器化，到最终部署在 Google Kubernetes Engine (GKE) 上的完整流程。

不需要你有任何前置经验，跟着下面的步骤一步步复制粘贴即可！

---

## 🌟 零首付起步：安装必备软件（课前准备）
如果你的电脑是全新的，请先安装以下必备工具。安装过程只需一直点击「下一步 (Next) / 同意」即可：
1. **[Python 3.10+](https://www.python.org/downloads/)**（Windows 用户在安装页面的最底部，**请务必打勾勾选 `[Add python.exe to PATH]`**）
2. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**（安装完成后，请双击桌面图标打开它，并保持在后台运行，电脑右下角应该能看到一只小鲸鱼图标🐳）
3. **[Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install)**（用于在命令行连接你的 Google Cloud）
4. **代码编辑器**（为了方便查看代码，推荐下载 [Visual Studio Code](https://code.visualstudio.com/)）

*(注意: `kubectl` 命令行工具通常在你安装完毕 Docker Desktop 后就会自动附带上了。)*

---

## 📂 第一步：打开命令行并进入项目
在 Windows 电脑上：
1. 打开文件管理器，找到讲师发给你的 `dryrun_folder` 文件夹并**双击进入该文件夹**。
2. 点击最上方白色的**路径地址栏**，把里面的字全部删掉。
3. 输入 `powershell` 这几个字母，然后按下回车键 `Enter`。
4. 此时会弹出一个蓝/黑色的命令行窗口，这个就是我们要施展魔法的地方。接下来所有的代码都在这里粘贴运行！

**(⚠️ 避坑提醒：在接下来整个工作坊的操作中，请确保你当前一直身处在 `dryrun_folder` 的根目录里！)**

---

## 💻 阶段一：本地小试牛刀 (Python)
在开始打包和上云前，我们先用 Python 本身的办法把代码跑起来。为了不弄乱电脑自带的环境，我们会给程序创建一个叫“虚拟环境 (venv)”的隔离温室。

### 1. 运行接收器 (Receiver)
输入以下命令进入接收器文件夹，并为它“建个温室”：

```powershell
# 1. 走进接收器房间
cd log_receiver_folder

# 2. 徒手建一个名为 venv 的虚拟环境温室
python -m venv venv

# 3. 激活温室！ (成功的话，你会看到命令行最前面多了一个绿色的 (venv) 字样)
venv\Scripts\activate
# 注: 如果你是 Mac/Linux 用户，这里命令不一样，请用: source venv/bin/activate

# 4. 根据购物清单 (requirements) 去下载需要的 Python 包
pip install -r requirements.txt

# 5. 启动代码程序！
python app.py
```
🎉 成功起飞！现在打开你的浏览器（Chrome），在网址那一栏输入并访问 [http://localhost:5000/](http://localhost:5000/)，就能看到超炫酷的赛博风前端面板啦！

看够以后回到蓝色的命令行，在键盘上按下 **`Ctrl + C`** 来强行结束程序。
然后输入 `cd ..` 按下回车，代表“退回到外面一层”（回到 `dryrun_folder`）。

### 2. (可选) 本地运行模拟黑客生成器
和上面一模一样的原理，我们让“攻击测试端”也跑起来。
```powershell
cd log_generator_folder
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
此时它会每隔15秒不停地制造“虚假”的攻击日志，发送到你的面板上。
不想玩了的话，同样按下 **`Ctrl + C`** 结束，再输入 `cd ..` 退回一步。

---

## 🐳 阶段二：装箱打包 (Docker 容器化)
只发给别人代码的话，别人的电脑还得照样费事安装各种包和配置。为了避免“在我的电脑上明明可以跑！”的尴尬境地。我们要把程序和它的“温室”整个装进一个大铁盒子里，这就是“集装箱”(Docker Image)。

### 1. 构建镜像 (Build)
根据已经写好的 `Dockerfile` (打包说明书)，我们来封箱。（进行这一步前，请瞄一眼电脑右下角，确保 Docker 鲸鱼图标正在运行中）

```powershell
# 打包接收器 (最后那个半角句号 '.' 千万别漏掉，它代表用当前的目录)
docker build -t log_receiver_image:v1 .\log_receiver_folder\

# 打包发射黑客日志的生成器
docker build -t log_generator_image:v1 .\log_generator_folder\
```
*这可能需要两三分钟去层层封装并下载所需的零件，耐心等一下。*

### 2. 扯线——给盒子之间修一条网线
```powershell
# 在 Docker 里拉出一条名为 sre-network 的“内网专属线路”
docker network create sre-network
```

### 3. 让集装箱跑起来 (Run Container)
首先启动作为大脑的接收器，把它插到刚拉好的网线上，然后把内部监控大屏暴露在我们电脑的 5000 端口上：
```powershell
# 这里的 -d 代表让它自己悄悄在后台跑
docker run -d --name log_receiver_container --network sre-network --network-alias log-receiver -p 5000:5000 log_receiver_image:v1
```

接着启动伪装成黑客的生成器，把接收器的“名字”通过环境变量写在名片上直接告诉它：
```powershell
docker run -d --name log_generator_container --network sre-network -e SERVICE_B_URL="http://log-receiver:5000/logs" log_generator_image:v1
```
💡 **太棒了！** 你现在拥抱了当前火热的“容器化微服务架构”！再刷新一下 [http://localhost:5000/](http://localhost:5000/)，一切如常，看起来跟之前没区别，但背后使用的技术栈已经截然不同了。

*(如果你又想“关机”了，可以用 `docker stop log_receiver_container` 和 `docker stop log_generator_container`。)*

---

## 🎁 隐藏路线 (无 Docker 专用)：一键云端代工打包法 (Cloud Build)
如果你因为电脑配置原因没有安装 Docker Desktop，完全可以直接跳过【阶段二】！使用 Google 提供的 Cloud Build 功能，你可以把本地代码直接抛给云服务器，让云端帮你一键全自动打包、贴标签并存入云仓库！

*(⚠️前置条件：使用前请确保你已经跟着讲师，在 GCP 网页上提前建好了 Artifact Registry 仓库。并记得以下命令把 `gen-lang-client-xxxx` 换成你自己的！)*
```powershell
# 一键在云端打包并入库接收器 (千万别漏了最后那个代表文件夹的反斜杠和点 .)
gcloud builds submit --tag us-central1-docker.pkg.dev/gen-lang-client-xxxxxxxx/docker-dryrun-repo/log_receiver_image:v1 .\log_receiver_folder

# 一键在云端打包并入库生成器 
gcloud builds submit --tag us-central1-docker.pkg.dev/gen-lang-client-xxxxxxxx/docker-dryrun-repo/log_generator_image:v1 .\log_generator_folder
```
跑完上面这两行魔法代码，你就**相当于完成了云端发货，可以直接跳过下面的【第2步】和【第3步】**，从【第4步 获取集群大门钥匙】开始往后跟着做就行啦！

---

## ☁️ 阶段三：星辰大海 (实战上线 Google Kubernetes Engine)
现在你的电脑玩得飞起，但真正的互联网商业应用是要放到 24 小时开机的云服务集群里让成千上万的人使用的。

### 1. 登录云端申请地盘
打开浏览器，登录 [Google Cloud Console](https://console.cloud.google.com/)。
跟着讲师的指引去“开卡激活”：
- 搜索寻找 **Artifact Registry** 服务，新建一个用于囤积云端 Docker 集装箱的货栈。
- 搜索寻找 **Kubernetes Engine** 服务，创建一个名为 Autopilot Cluster 的"全自动智能集群托管大本营" (GKE)。

### 2. 打上寄货地址的运单标签 (Tag)
你需要先拿到云平台的通行授权，配置好让本地的 Docker 有资格直接向你的 GCP (Google Cloud) 推送包裹：
```powershell
gcloud auth configure-docker us-central1-docker.pkg.dev
```

拿出前面自己用 Docker 打包好的本地集装箱，狠狠地贴上一张有着 Google 云端寄放站完整网点地址的快递标签：
*(⚠️必须注意：请把下面的 `gen-lang-client-xxxxxxxxxx` 等一长串东西，替换成了你自己真正的 GCP 项目 ID 以及在云端创立的仓库名字！)*

```powershell
# 给生成器的集装箱贴条
docker tag log_generator_image:v1 us-central1-docker.pkg.dev/gen-lang-client-xxxxxxxx/docker-dryrun-repo/log_generator_image:v1

# 给接收器的集装箱贴条
docker tag log_receiver_image:v1 us-central1-docker.pkg.dev/gen-lang-client-xxxxxxxx/docker-dryrun-repo/log_receiver_image:v1 
```

### 3. 把货箱用卡车送上“云层” (Push)
开始发货！
```powershell
docker push us-central1-docker.pkg.dev/gen-lang-client-xxxxxxxx/docker-dryrun-repo/log_receiver_image:v1

docker push us-central1-docker.pkg.dev/gen-lang-client-xxxxxxxx/docker-dryrun-repo/log_generator_image:v1 
```

### 4. 获取集群“最高级防盗门钥匙” (Credentials)
货到了，我们需要进去大本营布置。这里的作用是进行身份认证并连接这个云端 GKE 集群：
```powershell
gcloud container clusters get-credentials docker-dryrun-cluster --region us-central1 --project gen-lang-client-xxxxxxxx
```

### 5. 看我的 Kubernetes 一键魔术 (Deployment & Apply)
还记得 `dryrun_folder` 项目标配的那个 `k8s` 文件夹么？
里面就是所谓的架构设计说明书（yaml），它清晰地列明了需要多少辆卡车、怎么布线、坏了怎么自愈等设定。

运行以下命令，就是把图纸往包工头身上一砸：“全自动盖好这个房子！”
```powershell
kubectl apply -f k8s/
```

使用 Kubernetes 的"总监工监控视角"查看包工队的建造情况：
```powershell
kubectl get pods -w
```
等待片刻，眼看着状态一行行变成了光荣的 `Running`。
*(查看完毕后，随时按下 `Ctrl + C` 可以从挂机视角的命令中退出)*

### 6. 从任意一台电脑远程访问 (Port Forwarding 展示)
由于当前的教程版还没外挂暴露一个面向公众的“大门”(比如 Ingress 或者外部的 LoadBalancer 真实 IP)，想要看运行情况，我们需要走个地下秘密隧道，强行把云端的端口投影传送到现在你坐着的电脑上：
```powershell
kubectl port-forward svc/log-receiver-svc 5000:5000 
```

此时再次！第三次打开浏览器访问大屏幕的网址 `http://localhost:5000/`。
**🎉 恭喜你完成闯关！！** 
它看起来仍像熟悉的单机网页开发演示，但其本质已经是一个**在地球某处的数据中心里使用 Google 集群、基于微服务化运作，并支持 Kubernetes 自动监控拓展的企业级系统框架！** 

一小时之内，你已经摸索通透了如今互联网顶尖大厂必备技能库的整条核心链路流程！给自己鼓个掌吧！👏
