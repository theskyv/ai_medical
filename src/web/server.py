
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_neo4j.vectorstores.neo4j_vector import SearchType

from configuration import config

#🌻🌻🌻
INTENT_INFO = {
    "request": [
        "挂号预约", "检查预约", "住院预约", "报告查询/下载", "费用支付/退费",
        "转诊/转院申请", "病例邮寄", "个人信息修改", "服务投诉", "建议反馈", "系统故障反馈"
    ],
    "consult": [
        "疾病对应详情", "疾病对应科室", "疾病对应症状", "疾病对应并发症", "疾病对应诱因",
        "疾病对应药物", "疾病宜食用", "疾病忌食用", "疾病对应传播途径", "疾病对应预防措施",
        "疾病对应易感人群", "疾病对应检查", "疾病对应治疗方式", "疾病对应治疗周期", "症状解读",
        "诱因导致疾病", "药物用于疾病", "食物益于疾病", "食物忌于疾病", "人群类别易感疾病", "检查项目用于疾病"
    ]
}

class ChatService:
    def __init__(self):
        self.graph = Neo4jGraph(url=config.NEO4J_CONFIG['uri'],
                                username=config.NEO4J_CONFIG['auth'][0],
                                password=config.NEO4J_CONFIG['auth'][1])
        # 🌻🌻🌻
        self.INTENT_INFO = INTENT_INFO

        self.llm = ChatDeepSeek(model='deepseek-chat', api_key=config.DEEPSEEK_API_KEY)

        self.embedding_model = HuggingFaceEmbeddings(model_name='BAAI/bge-small-zh-v1.5',
                                                     encode_kwargs={"normalize_embeddings": True})
        self.neo4j_vectors = self._init_neo4j_vectors()

        self.json_parser = JsonOutputParser()
        self.str_parser = StrOutputParser()

    def _init_neo4j_vectors(self):
        labels = ['Cause', 'Check', 'Department', 'Disease', 'Drug', 'Duration', 'Food', 'People', 'Symptom', 'Treat',
                  'Way', 'PreventWay']
        return {label: self._create_neo4j_vector(label) for label in labels}

    def _create_neo4j_vector(self, label):
        if label == 'PreventWay':
            index_name = 'preventWay_vector_index'
            keyword_index_name = 'preventWay_full_text_index'
        else:
            index_name = f'{label.lower()}_vector_index'
            keyword_index_name = f'{label.lower()}_full_text_index'

        return Neo4jVector.from_existing_index(
            self.embedding_model,
            url=config.NEO4J_CONFIG['uri'],
            username=config.NEO4J_CONFIG['auth'][0],
            password=config.NEO4J_CONFIG['auth'][1],
            index_name=index_name,
            keyword_index_name=keyword_index_name,
            search_type=SearchType.HYBRID
        )
    #✨🎈❗❗❗❗❗主方法
    # 修改chat主方法，添加意图分流逻辑🌻🌻🌻
    # 在chat方法最开头先调用_classify_intent，根据意图走不同流程：
    # 若为consult（医疗咨询）：走原有 “生成
    # Cypher→查图谱→生成回答” 流程；
    # 若为request（事务办理）：直接返回操作引导（如 “请点击【挂号预约】按钮进行操作”），无需查图谱；
    # 若为unknown（未知）：返回提示（如 “暂未支持该需求，请换个问题试试”）。
    def chat(self, question):
        intent = self._classify_intent(question)
        print('\n\n')
        print(f'🎯用户意图分类结果:{intent}')
        print('='*50)
        #⛳意图1：事务办理（request）→ 直接返回操作引导
        if intent == "request":
            # 可根据具体关键词细化引导（如含“挂号”则引导挂号，含“报告”则引导查报告）
            for req_keyword in self.INTENT_INFO["request"]:
                # 把关键词和问题都转成小写，再判断是否包含核心词（更灵活）
                # if req_keyword.replace("/", "").lower() in question.lower():
                # if req_keyword in question:
                # 1.🥀拆分关键词为核心词（比如“费用支付/退费”拆成["费用", "支付", "退费"]）
                core_words = req_keyword.replace("/", " ").split()  # 先把/换成空格，再按空格拆分
                # 2.🌾检查用户问题是否包含任何一个核心词（忽略大小写）
                if any(word.lower() in question.lower() for word in core_words):
                    return f"请通过【{req_keyword}】功能入口进行操作（点击页面对应按钮即可）"
            return "请选择页面中的事务功能按钮（如挂号预约、报告查询等）进行操作"

        #⛳意图2：未知需求→返回提示
        # elif intent == "unknown":
        #     return "暂未支持该类型的需求，请尝试咨询医疗相关问题（如“感冒症状”）或选择页面事务按钮"
        elif intent == "unknown":
            # 调用大模型，让大模型尝试回答未知问题
            unknown_prompt = PromptTemplate.from_template('''
                你是一个医疗行业领域的智能医生小助手,精通各种医学知识以及熟悉所有的医院诊断流程。
                请你根据自己仅有的知识，尽可能回答用户的问题。如果确实无法回答，就回复“暂未支持该需求，请换个问题试试”。
                
                要求:
                1.回答简洁、准确,使用人类的自然语言。
                2.仅输出普通文本。
                3.直接给出具体结论，无需额外冗余内容。

                用户问题：{question}
            ''')
            formatted_prompt = unknown_prompt.format(question=question)
            return self.str_parser.invoke(self.llm.invoke(formatted_prompt))

        #⛳意图3：医疗咨询（consult）→ 走原有图谱查询流程（以下为原有代码，不变）
        else:
            # 1.根据用户的question以及图数据库的schema 生成cypher语句以及需要对齐的实体
            result = self._generate_cypher(question)
            cypher = result['cypher_query']
            entities_to_align = result['entities_to_align']
            print(f'🎉第一步结果-->{result}')
            print(f'🎉生成的查询语句-->{cypher}')
            print('=' * 50)

            # 2.通过混合检索去做实体对齐
            aligned_entities = self._entity_align(entities_to_align)
            print(f'🥪第二步需要对齐的实体-->{aligned_entities}')
            print('='*50)

            # 3.执行cypher语句
            query_result = self._execute_query(cypher,aligned_entities)
            # print(f'🍱第三步执行cypher语句的结果-->{query_result}')

            # 4.根据用户问题和查询结果生成自然语言回复
            answer = self._generate_answer(question,query_result)
            return answer

    #🌻🌻🌻 新增：意图分类方法
    def _classify_intent(self, question):
        """判断用户问题的意图：request（事务）、consult（咨询）、unknown（未知）"""
        # 1. 把意图关键词拼接成提示，让LLM判断
        intent_prompt = PromptTemplate.from_template('''
            请判断用户问题属于以下哪种意图：
            - request（事务办理）：包含{request_keywords}
            - consult（医疗咨询）：包含{consult_keywords}
            若都不属于，输出"unknown"。
            要求：仅输出"request"、"consult"或"unknown"，不添加任何多余内容。
            用户问题：{question}
        ''')
        # 2. 格式化提示（把意图关键词列表转成字符串）
        formatted_prompt = intent_prompt.format(
            request_keywords="、".join(self.INTENT_INFO["request"]),
            consult_keywords="、".join(self.INTENT_INFO["consult"]),
            question=question
        )
        # 3. 调用LLM获取意图结果
        intent_result = self.llm.invoke(formatted_prompt)
        return self.str_parser.invoke(intent_result).strip()


    def _generate_cypher(self, question):
        prompt = '''
                你是一个专业的Neo4j Cypher查询生成器,你的任务是根据用户问题生成一条Cypher查询语句,用于从知识图谱中获取回答用户问题所需的信息。
                
                用户问题:{question}
                知识图谱结构信息:{schema_info}
                
                要求:
                1.生成参数化Cypher查询语句,用param_0,param_1等代替具体值
                2.识别需要对齐的实体
                3.必须严格使用以下JSON格式输出结果
                {{
                    "cypher_query": "生成的Cypher语句",
                    "entities_to_align":[
                        {{
                            "param_name": "param_0",
                            "entity": "原始实体名称",
                            "label": "节点类型"
                        }}
                    ]
                }}
        '''

        prompt = PromptTemplate.from_template(prompt)
        prompt = prompt.format(question=question, schema_info=self.graph.schema)
        # print(f'🍅知识图谱机构信息:{self.graph.schema}')


        output = self.llm.invoke(prompt)
        # print(self.str_parser.invoke(output))
        return self.json_parser.invoke(output)

    def _entity_align(self, entities_to_align):
        for index, entity_to_align in enumerate(entities_to_align):
            label = entity_to_align['label']
            entity = entity_to_align['entity']
            aligned_entity = self.neo4j_vectors[label].similarity_search(entity,k=1)[0].page_content
            print(f'💚原实体:{entity}-->对齐实体:{aligned_entity}')
            print('='*50)
            entities_to_align[index]['entity'] = aligned_entity #🔥原地修改
        return entities_to_align

    def _execute_query(self, cypher, aligned_entities):
        params = {aligned_entity['param_name']: aligned_entity['entity'] for aligned_entity in aligned_entities}
        return  self.graph.query(cypher,params=params)

    def _generate_answer(self, question, query_result):
        prompt = '''
                你是一个医疗行业领域的智能医生小助手,精通各种医学知识以及熟悉所有的医院诊断流程。根据用户问题,以及数据库查询结果生成回答。
                要求:
                1.回答简洁、准确,使用人类的自然语言。
                2.仅输出普通文本。
                3.直接给出具体结论，无需额外冗余内容。
                用户问题:{question}
                数据库返回结果:{query_result}
        '''
        prompt = prompt.format(question=question,query_result=query_result)
        result = self.llm.invoke(prompt)
        return self.str_parser.invoke(result)


if __name__ == '__main__':
    chat_service = ChatService()
    user_question = '吃完雪糕之后肚子疼应该怎么办呢？'
    response = chat_service.chat(user_question)
    print(response)


'''
二、添加意图配置的核心作用
避免无效查询：比如用户问 “怎么挂号”，原有逻辑会试图生成 Cypher 查知识图谱，但图谱里没有 “挂号操作入口” 数据，最终会返回无效回答；加意图后直接引导到操作按钮，体验更优。
明确功能边界：区分 “知识问答” 和 “事务操作”，让系统知道哪些需求该查图谱、哪些该引导操作，符合智能医疗助手的实际使用场景。
方便后续扩展：若后续新增事务功能（如 “疫苗预约”），只需在INTENT_INFO["request"]里加关键词，无需修改核心查询逻辑，维护更简单。
三、测试验证建议
测试request意图：输入 “我要挂号”，应返回 “请通过【挂号预约】功能入口进行操作”；
测试consult意图：输入 “吃完雪糕肚子疼怎么办”，应走原有图谱查询流程，返回医疗建议；
测试unknown意图：输入 “今天天气怎么样”，应返回 “暂未支持该类型的需求...”。
'''