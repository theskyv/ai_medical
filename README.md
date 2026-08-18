```bash
# 在root权限下执行命令(sudo -i)
# 如果 10.8.81.3 上没有lhr用户账号
# -m 创建/home/LHR家目录
# -s /bin/bash 指定使用bash作为shell
useradd -m -s /bin/bash lhr

# 重置/设置密码
passwd appgroup

# 切换登录  - 代表login(登录式 shell) su = switch user，切换用户
su - lhr

# 退出lhr 回到root
exit

#含义：把本机的文件夹，复制到远端机器10.8.81.3的~/data/目录下
scp -r /data/models/modelscope/models LHR@10.8.81.3:~/data


```

### fastapi && docker部署（封装bge-m3服务）
目录结构
```bash
bge-m3-fastapi/
├── main.py
├── Dockerfile
└── docker-compose.yml
```
🐣1.main.py
```bash
import os
from fastapi import FastAPI, Body
from FlagEmbedding import BGEM3FlagModel

# 锁定使用显卡2，和docker配置保持一致
os.environ["CUDA_VISIBLE_DEVICES"] = "2"

app = FastAPI(title="BGE-M3 稠密+稀疏向量服务")

# 加载模型，低显存优化
model = BGEM3FlagModel(
    model_name_or_path="/root/.cache/huggingface/hub/models--BAAI--bge-m3",
    use_fp16=True,
    device="cuda"
)

@app.post("/api/embed")
async def embed_texts(
    texts: list[str] = Body(..., description="输入文本列表"),
    return_dense: bool = True,
    return_sparse: bool = True
):
    # 显存紧张batch设1最稳
    encode_res = model.encode(
        texts,
        return_dense=return_dense,
        return_sparse=return_sparse,
        return_colbert_vecs=False,
        batch_size=4
    )
    res_list = []
    dense_list = encode_res.get("dense_vecs", [])
    sparse_list = encode_res.get("lexical_weights", [])

    for idx in range(len(texts)):
        item = {}
        if return_dense and idx < len(dense_list):
            item["dense"] = dense_list[idx].tolist()
        if return_sparse and idx < len(sparse_list):
            item["sparse"] = sparse_list[idx]
        res_list.append(item)
    return {"code": 200, "msg": "success", "data": res_list}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
🪁2.Dockerfile 构建镜像文件
```bash
# 换成国内拉取无压力的 Python 镜像
FROM python:3.10-slim

WORKDIR /app

# 换成阿里云 Ubuntu 源（加速 apt 安装）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装基础依赖
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# 清华 PyPI 源安装依赖（超快）
RUN pip install --no-cache-dir \
    torch==2.3.1 \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    FlagEmbedding==1.3.2 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝代码
COPY main.py .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]
```
🐦‍🔥3.docker-compose.yml 编排文件（指定 GPU 卡号）
```bash
services:
  bge-m3-service:
    build: .
    container_name: bge-m3-fastapi-service
    ports:
      - "8003:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["2"]  # 改成你要用的显卡编号 0/1/2/3
              capabilities: [gpu]
    volumes:
      # 挂载本地预下载好的模型，避免容器内重新下载
      - /data/models/modelscope/models/bge-m3:/root/.cache/huggingface/hub/models--BAAI--bge-m3
    restart: always
    environment:
      - TZ=Asia/Shanghai
```
**前置准备**  \
提前用modelscope下载好模型到路径：/data/models/modelscope/models/bge-m3 \
确认服务器2 号显卡空闲显存≥3.5G，原有业务服务不停止  \

**一键部署启动**
```bash
# 进入项目文件夹
cd bge-m3-fastapi

# 构建镜像+后台启动
docker-compose up -d --build
# 或者改成新命令（不带横杠，大部分新版 Docker 都自带）
docker compose up -d --build

# 查看运行日志
docker-compose logs -f

# 停止服务
docker-compose down
```
**接口测试**
```bash
curl -X POST http://你的服务器IP:8004/api/embed \
-H "Content-Type: application/json" \
-d '["测试文档内容","BGE-M3向量模型"]'

curl -X POST "http://10.8.81.1:8003/api/embed" -H "Content-Type: application/json" -d "[\"小明做什么工作？\"]"
```
返回内容同时包含稠密向量 dense + 稀疏权重 sparse，直接可存入 Milvus 混合索引。 \
**切换显卡修改位置** \
- main.py 里：os.environ["CUDA_VISIBLE_DEVICES"] = "2" \
- docker-compose.yml 里：device_ids: ["2"] \
- 两处数字保持一致即可。 

-----

# 医疗智能助手系统
## 项目介绍
一款集成医疗知识问答与医院事务办理引导的智能助手系统。基于 Neo4j 知识图谱存储医疗领域数据，结合大模型实现意图识别与自然语言交互，可精准区分用户的 “医疗咨询需求”（如疾病症状、用药建议）与 “事务办理需求”（如挂号、报告查询），提供高效、贴合场景的响应。

## 核心功能
| 功能模块       | 具体能力                                                                 |
|----------------|--------------------------------------------------------------------------|
| 意图识别       | 自动分类用户需求为 `consult`（医疗咨询）、`request`（事务办理）、`unknown`（未知需求） |
| 医疗知识问答   | 基于 Neo4j 知识图谱，回答疾病、症状、药物、检查项目等医疗相关问题         |
| 事务办理引导   | 针对挂号、报告查询、费用支付等需求，直接引导至对应功能入口               |
| 实体对齐优化   | 通过向量检索实现用户输入实体与图谱数据的精准匹配（如“肚子疼”对齐“腹痛”） |

## 技术栈
- 后端框架：Python（核心逻辑）
- 知识图谱：Neo4j（存储医疗实体与关系）
- 大模型集成：DeepSeek（意图识别、Cypher 生成、回答生成）
- 向量检索：HuggingFace Embeddings（BAAI/bge-small-zh-v1.5，实体对齐）
- LangChain 组件：LangChain-Core、LangChain-Neo4j、LangChain-DeepSeek（流程编排）

## 环境准备
### 1. 依赖安装
在项目根目录执行以下命令（推荐使用虚拟环境如 venv 或 conda）：
```bash
pip install -r requirements.txt
```
#### requirements.txt 完整内容

langchain==0.2.0 \
langchain-core==0.2.0 \
langchain-community==0.2.0 \
langchain-neo4j==0.1.14 \
langchain-deepseek==0.1.0 \
huggingface-hub==0.23.0 \
transformers==4.41.0 \
torch==2.3.0  \
neo4j==5.18.0 \
python-dotenv==1.0.1     

### 2. 配置文件设置
在项目根目录创建 configuration.py 文件，替换实际参数后使用：\
python 
运行 
#### configuration.py
config = { \
    "NEO4J_CONFIG": { \
        "uri": "bolt://localhost:7687",  # 替换为 Neo4j 服务地址（本地/云端） \
        "auth": ("neo4j", "your-neo4j-password")  # 替换为 Neo4j 用户名与密码 \
    }, \
    "DEEPSEEK_API_KEY": "your-deepseek-api-key"  # 替换为 DeepSeek 官网获取的 API 密钥 \
}

### 3. Neo4j 知识图谱准备
- 启动服务：本地部署需下载 Neo4j 社区版并启动，云端部署可使用 Neo4j AuraDB 并获取连接信息。  \
- 导入数据：需包含实体标签：Cause（病因）、Check（检查项目）、Department（科室）、Disease（疾病）、Drug（药物）、Duration（治疗周期）、Food（食物）、People（易感人群）、Symptom（症状）、Treat（治疗方式）、Way（传播途径）、PreventWay（预防措施）。  \
- 创建索引：在 Neo4j 浏览器执行以下语句（以 Disease 为例，其他实体类似）：  \
<br>

**cypher**语句👇
  
#### 向量索引（适配 384 维向量模型）
CREATE VECTOR INDEX disease_vector_index \
FOR (n:Disease) ON (n.embedding) \ 
OPTIONS {indexConfig: { \
    `vector.dimensions`: 512, \
    `vector.similarity_function`: 'cosine' \
}};

#### 全文索引（支持中文分词）
CREATE FULLTEXT INDEX disease_full_text_index \ 
FOR (n:Disease) ON EACH [n.name, n.description] \
OPTIONS {indexConfig: {`fulltext.analyzer`: 'chinese'}}; 

### 系统启动
切换到 src 目录（替换实际路径）：
```bash
cd /path/to/your-project/src
```
执行启动命令：
```bash
python main.py app
```

### 功能测试
| 测试类型       | 用户输入示例               | 预期输出效果                                                                 |
|----------------|----------------------------|------------------------------------------------------------------------------|
| request（事务） | “我要挂号”                 | “请通过【挂号预约】功能入口进行操作（点击页面对应按钮即可）”                 |
| consult（咨询） | “吃完雪糕肚子疼怎么办”     | 基于图谱返回：“可能为肠胃痉挛（诱因：生冷食物刺激），建议热敷腹部，避免生冷食物” |
| unknown（未知） | “今天天气怎么样”           | “暂未支持该类型的需求，请尝试咨询医疗相关问题或选择页面事务按钮”             |


### 注意事项
密钥安全：推荐用 .env 文件管理敏感信息（配合 python-dotenv），避免硬编码，.env 文件需添加到 .gitignore。 \
性能优化：图谱数据量大时，可调整索引配置、开启 Neo4j 缓存提升查询速度。 \
成本控制：DeepSeek API 调用有费用，测试阶段可限制调用频率或替换为本地开源大模型（如 Llama 3）。 

-------
