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
- 
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
