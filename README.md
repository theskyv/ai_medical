医疗智能助手系统
项目介绍
一款集成 医疗知识问答 与 医院事务办理引导 的智能助手系统。基于 Neo4j 知识图谱存储医疗领域数据，结合大模型实现意图识别与自然语言交互，可精准区分用户的 “医疗咨询需求”（如疾病症状、用药建议）与 “事务办理需求”（如挂号、报告查询），提供高效、贴合场景的响应。
核心功能
功能模块	具体能力
意图识别	自动分类用户需求为 consult（医疗咨询）、request（事务办理）、unknown（未知需求）
医疗知识问答	基于 Neo4j 知识图谱，回答疾病、症状、药物、检查项目等医疗相关问题
事务办理引导	针对挂号、报告查询、费用支付等需求，直接引导至对应功能入口
实体对齐优化	通过向量检索实现用户输入实体与图谱数据的精准匹配（如 “肚子疼” 对齐 “腹痛”）
技术栈
后端框架：Python（核心逻辑）
知识图谱：Neo4j（存储医疗实体与关系）
大模型集成：DeepSeek（意图识别、Cypher 生成、回答生成）
向量检索：HuggingFace Embeddings（BAAI/bge-small-zh-v1.5，实体对齐）
LangChain 组件：LangChain-Core、LangChain-Neo4j、LangChain-DeepSeek（流程编排）
环境准备
1. 依赖安装
在项目根目录执行以下命令，安装所需依赖：
bash
# 推荐使用虚拟环境（如 venv 或 conda）
pip install -r requirements.txt
requirements.txt 内容（直接复制使用）
txt
langchain==0.2.0
langchain-core==0.2.0
langchain-community==0.2.0
langchain-neo4j==0.1.14
langchain-deepseek==0.1.0
huggingface-hub==0.23.0
transformers==4.41.0
torch==2.3.0
neo4j==5.18.0
python-dotenv==1.0.1
2. 配置文件设置
在项目根目录创建 configuration.py 文件，填入以下内容并修改对应参数：
python
运行
# configuration.py
config = {
    "NEO4J_CONFIG": {
        "uri": "bolt://localhost:7687",  # 替换为你的 Neo4j 连接地址
        "auth": ("neo4j", "your-neo4j-password")  # 替换为你的 Neo4j 用户名与密码
    },
    "DEEPSEEK_API_KEY": "your-deepseek-api-key"  # 替换为你的 DeepSeek API 密钥（从官网获取）
}
3. Neo4j 图谱准备
启动 Neo4j 服务（本地或云端），确保能通过上述 uri 正常连接。
导入医疗领域数据至 Neo4j，需包含以下实体标签：
Cause（病因）、Check（检查项目）、Department（科室）、Disease（疾病）
Drug（药物）、Duration（治疗周期）、Food（食物）、People（易感人群）
Symptom（症状）、Treat（治疗方式）、Way（传播途径）、PreventWay（预防措施）
为各实体创建 向量索引 与 全文索引（参考代码中 _init_neo4j_vectors 方法逻辑）。
系统启动
切换至项目 src 目录（若核心脚本 main.py 在 src 文件夹下）：
bash
cd /path/to/your-project/src  # 替换为你的项目 src 目录实际路径
执行启动命令，指定 app 动作：
bash
python main.py app
启动成功后，可通过接口调用（如扩展 Flask/FastAPI）或命令行测试交互功能。
功能测试
测试用例参考
测试类型	用户输入示例	预期输出效果
事务办理（request）	“我要挂号”	“请通过【挂号预约】功能入口进行操作（点击页面对应按钮即可）”
医疗咨询（consult）	“吃完雪糕肚子疼怎么办”	基于图谱返回医疗建议（如 “可能为肠胃痉挛，建议热敷腹部，避免生冷食物”）
未知需求（unknown）	“今天天气怎么样”	大模型尝试回答，或返回 “暂未支持该类型的需求，请尝试咨询医疗相关问题”
系统问题	“你是谁”	大模型返回自我介绍（如 “我是医疗智能助手，可解答医疗问题或引导事务办理”）
调试日志
启动后终端会输出关键流程日志，便于排查问题：
意图分类结果：🎯用户意图分类结果:consult
生成的 Cypher 语句：🎉生成的查询语句:MATCH (d:Disease)-[:has_symptom]->(s:Symptom) WHERE d.name = $param_0 RETURN s.name
实体对齐结果：💚原实体:肚子疼-->对齐实体:腹痛
扩展说明
1. 新增事务功能
若需添加新的事务类型（如 “疫苗预约”），仅需在代码的 INTENT_INFO 中补充关键词：
python
运行
INTENT_INFO = {
    "request": [
        # 原有事务（如挂号预约、报告查询等）
        "疫苗预约"  # 新增事务关键词
    ],
    "consult": [
        # 原有医疗咨询关键词...
    ]
}
2. 优化医疗知识
扩展图谱数据：新增疾病、药物、检查项目等实体与关系，丰富问答内容。
更新向量模型：替换 HuggingFaceEmbeddings 的 model_name（如使用 BAAI/bge-large-zh-v1.5），提升实体对齐精度。
3. 前端对接示例
可基于 Flask 封装接口，提供给前端调用，示例代码如下：
python
运行
# src/api.py（新增文件）
from flask import Flask, request, jsonify
from chat_service import ChatService

app = Flask(__name__)
chat_service = ChatService()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    question = data.get("question")
    if not question:
        return jsonify({"code": 400, "msg": "请输入问题"})
    response = chat_service.chat(question)
    return jsonify({"code": 200, "data": {"answer": response}})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
注意事项
Neo4j 性能优化：若图谱数据量较大，建议调整向量索引维度、全文索引权重，提升查询速度。
密钥安全管理：不要将 DEEPSEEK_API_KEY 或 Neo4j 密码硬编码，推荐使用 .env 文件（配合 python-dotenv）管理：
env
# .env 文件（项目根目录）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
DEEPSEEK_API_KEY=your-deepseek-api-key
并修改 configuration.py 读取环境变量：
python
运行
from dotenv import load_dotenv
import os

load_dotenv()  # 加载 .env 文件

config = {
    "NEO4J_CONFIG": {
        "uri": os.getenv("NEO4J_URI"),
        "auth": (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    },
    "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY")
}
大模型调用成本：DeepSeek API 调用会产生费用，测试阶段建议控制调用频率，或替换为本地部署的大模型（如 Llama 系列）。
