# Docker部署
## 1.安装DockerDesktop
https://blog.csdn.net/weixin_45145684/article/details/144729149
![img.png](img.png)

## 2.创建.venv环境
退出当前项目所在的conda环境,切到新建的.venv环境
①下载pipreqs库，使用以下命令 pip install pipreqs \
②使用以下命令生成requirements.txt文件 pipreqs . --encoding=utf8 --force \
③生成的requirements.txt文件如下，不会出现所有的python库包 \
④下载requirements.txt的所有库包的方法命令如下 \
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```
### 生成requirements.txt文件
https://blog.csdn.net/qq_53644346/article/details/138506229?ops_request_misc=%257B%2522request%255Fid%2522%253A%2522ea8290e3d18c717a0d2847d9d4cd4798%2522%252C%2522scm%2522%253A%252220140713.130102334..%2522%257D&request_id=ea8290e3d18c717a0d2847d9d4cd4798&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~top_positive~default-1-138506229-null-null.142%5Ev102%5Epc_search_result_base7&utm_term=%E7%94%9F%E6%88%90requirements.txt%E6%96%87%E4%BB%B6&spm=1018.2226.3001.4187 \
方法3（推荐）\
前两种方法适用于将解释器中的所有安装包写入requirements.txt文件中，但是如果需要保存本项目中使用过的安装包时（尤其是生成自己python代码所使用的安装包），则按照以下步骤进行：\
在Anaconda Prompt中，首先安装pipreqs，\
**python**
```bash
pip install pipreqs
```
然后进入到你所在的项目根目录，运行以下命令：
**shell**
```bash
pipreqs ./ --encoding=utf-8
```
### 报错:UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb1 in position 81: invalid start byte
请参数解决方案:https://blog.csdn.net/weixin_41934979/article/details/139256562?ops_request_misc=%257B%2522request%255Fid%2522%253A%25220c1fe91e4788ee754031bce02906e8cc%2522%252C%2522scm%2522%253A%252220140713.130102334.pc%255Fall.%2522%257D&request_id=0c1fe91e4788ee754031bce02906e8cc&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~first_rank_ecpm_v1~rank_v31_ecpm-1-139256562-null-null.142^v102^pc_search_result_base7&utm_term=%E4%BD%BF%E7%94%A8%20pipreqs%20.%2F%20--encoding%3Dutf-8%E6%97%B6UnicodeDecodeError%3A%20utf-8%20codec%20cant%20decode%20byte%200xb1%20in%20position%2081%3A%20invalid%20start%20byte&spm=1018.2226.3001.4187 
```bash
pipreqs --ignore .venv --force
```
--ignore: 忽略执行 \
--force : 强制覆盖requirements.txt的内容

❗❗❗确保在.venv程序能跑通✅

## 3.编写Dockerfile(核心配置文件)
Dockerfile 是 “说明书”，告诉 Docker 如何打包你的项目(比如基础环境、安装依赖、启动命令)。 \
在你的项目根目录（和 requirements.txt 同级）新建 Dockerfile 文件，内容示例：
```bash
# 1. 选择基础 Python 环境（选和你项目匹配的版本，比如 3.9）
FROM python:3.9-slim

# 2. 设置工作目录（容器内的文件夹，类似你本地的项目目录）
WORKDIR /app

# 3. 复制项目文件到容器内（本地的 requirements.txt 和 src 文件夹，复制到容器的 /app 下）
COPY requirements.txt .
COPY src/ ./src/

# 4. 安装依赖（用清华源加速，避免网络问题）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 设置容器启动命令（启动你的项目，和本地执行的命令一致）
CMD ["python", "src/main.py", "app"]
```
## 4.构建镜像
镜像是 “打包好的环境包”，包含 Python、依赖包、你的项目代码。 \
启动Docker Desktop \
🟣🟢🟡可以先把基础镜像给pull下来再构建
```bash
docker pull python:3.12-slim
```

在终端进入项目根目录（确保和 Dockerfile 同级），执行构建命令：
```bash
# 格式：docker build -t 镜像名:版本号 . （末尾的 . 表示“从当前目录的 Dockerfile 构建”）
docker build -t medical_assistant:v1.0 .
```
- 执行后会看到 “Step 1/5 : FROM python:3.9-slim” 等日志，等待构建完成（首次会下载基础镜像，可能慢一点）。\
- 构建成功后，用 docker images 命令能看到你刚创建的 medical-assistant:v1.0 镜像。

## 5.创建并运行Docker容器
容器是 “镜像的运行实例”，相当于启动一个独立的 “小电脑” 跑你的项目。\
执行创建容器的命令：
```bash
# 格式：docker run -d --name 容器名 镜像名:版本号 （-d 表示“后台运行”）
#docker run -d --name med-assist-container medical-assistant:v1.0
#docker run -d --name medical_container --add-host="host.docker.internal:host-gateway" medical_assistant:v1.0
docker run -d --name medical_container --add-host="host.docker.internal:host-gateway" -p 8000:8000 medical_assistant:v1.0
```
- **-p 8000:8000** 表示 “宿主机的 8000 端口 ↔ 容器内的 8000 端口”，如果宿主机 8000 端口被占用，可改宿主机端口（比如 -p 8888:8000，后续访问用 8888 端口）。
- 运行后用 docker ps 命令能看到 medical_container 容器处于 “Up” 状态，说明项目正在容器内运行。
- 如果需要查看容器内的日志（比如调试报错），执行：
```bash
docker logs medical_container
```
## 6.服务器sudo docker pull python:3.12-slim不行怎么办❓
直接复制就能用的国内源拉取命令，不用改配置、不用重启docker
**直接用国内源拉取python:3.12-slim**
```bash
sudo docker pull docker.1ms.run/library/python:3.12-slim
```
拉下来之后，照样可以用原名，不影响你后面写 Dockerfile：
```bash
sudo docker tag docker.1ms.run/library/python:3.12-slim python:3.12-slim
```
**如果你要在 Dockerfile 里直接用国内源**
把这一行写进 Dockerfile：
```bash
FROM docker.1ms.run/library/python:3.12-slim
```
**备用国内源（上面不行就换这个）**
```bash
sudo docker pull mirror.baidubce.com/library/python:3.12-slim
```
--------------------------------------------------------------------------
FROM = 从...开始 \
docker.1ms.run = 国内Docker镜像加速地址 \
library/python = 官方python镜像 \
3.12-slim = Python3.12精简版 \
整句意思：我要从国内源下载 Python 3.12 精简版，作为我容器的基础系统。 

正常写法 FROM python:3.12-slim，但国内网络拉不动，会超时。 \
FROM python:3.12-slim → FROM docker.io/library/python:3.12-slim(👈Docker会自动帮你补全) \
**但用国内加速时，不会自动补全** 所以必须手动写全 
```bash
FROM docker.1ms.run/library/python:3.12-slim
```

--------------------------------------------------------------------------------
**检查日志** \
虽然容器跑起来了，但可能内部报错了（比如模型没加载完）。输入这个命令看实时输出： 
```bash
sudo docker logs -f ee7672b6578f
```
(注：ee76... 是你sudo docker ps的 CONTAINER ID)

## 7.容器操作命令🦜
```bash
sudo -i #切换到root超级用户的交互式登录环境 -i(--login)
docker ps
docker ps -a
docker container ls -a  #⭐ docker：调用 Docker 工具  container：操作容器  ls：list = 列出  -a：all = 显示所有容器（包括已停止的）
docker logs -f obs_meeting_qa #实时跟踪查看名为 obs_meeting_qa 的Docker容器的日志输出
docker exec -it obs_meeting_qa bash  #exec:表示已运行的容器中执行命令   obs_meeting_qa目标容器的名称   bash要在容器内执行的命令:启动bash终端
```
## 8.服务器 / 远程机器上安装并启动 JupyterLab 服务
```bash
pip install jupyterlab
```
```bash
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```
```bash
jupyter server list     # 它会列出当前正在运行的服务以及完整的带Token的URL
jupyter server password    # 强制设置新密码
```
🥳启动一个可被外部访问的 JupyterLab 服务，运行在 8888 端口，不自动弹浏览器，允许 root 运行
- jupyter lab：启动 JupyterLab 服务
- --ip=0.0.0.0：允许所有 IP 地址访问（也就是可以从局域网其他机器、或者公网访问这个服务，而不是只能本机访问）
- --port=8888：指定服务运行在 8888 端口（浏览器访问时要加 :8888）
- --no-browser：启动后不自动打开浏览器（适合在服务器 / 远程环境运行，手动在浏览器打开）
- --allow-root：允许 root 用户 启动服务（Linux / 服务器环境下，root 权限运行时需要加这个参数，否则会报错）

🦞测试服务器之间是否连通
- 先 ping 10.189.1.127 → 确认主机在线；
- 再用 telnet/nc 测试 18008 端口 → 确认服务可用。
```bash
# 第一步：ping 测试主机连通性
ping 10.189.1.127

# 第二步：测试 18008 端口（推荐用 nc，比 telnet 更清晰）
telnet 10.189.1.127 18008
nc -zv 10.189.1.127 18008
```
------
⭐linux创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

conda deactivate #退出base环境

deactivate #退出(venv) 虚拟环境
```

🦜快速查询你服务器 公网 IP 地址、归属地和运营商 的命令
```bash
curl cip.cc  
```

