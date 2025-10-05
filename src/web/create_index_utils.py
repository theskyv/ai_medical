import dotenv
dotenv.load_dotenv()
##创建全文索引和向量索引
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jGraph

from src.configuration import config


class IndexUtil:
    def __init__(self):
        self.graph = Neo4jGraph(url=config.NEO4J_CONFIG['uri'],
                                username=config.NEO4J_CONFIG['auth'][0],
                                password=config.NEO4J_CONFIG['auth'][1])
        self.embedding_model = HuggingFaceEmbeddings(model_name='BAAI/bge-small-zh-v1.5',
                                                     encode_kwargs = {"normalize_embeddings": True})

    def create_full_text_index(self,index_name,label,property):
        cypher = f'''
                CREATE FULLTEXT INDEX {index_name}  IF NOT EXISTS
                FOR (n:{label}) ON EACH [n.{property}]
        '''
        self.graph.query(cypher)
        print(f'🍉{label}全文索引cypher语句-->{cypher}')

    def create_vector_index(self,index_name,label,source_property,embedding_property):
        embedding_dim = self._add_embedding(label,source_property,embedding_property)
        cypher=f'''
               CREATE VECTOR INDEX {index_name} IF NOT EXISTS
                FOR (m:{label})
                ON m.{embedding_property}
                OPTIONS {{ indexConfig: {{
                 `vector.dimensions`: {embedding_dim},
                 `vector.similarity_function`: 'cosine'
            }}
            }}
        '''
        self.graph.query(cypher)
        print(f'🍇{label}向量索引cypher语句-->{cypher}')

    def _add_embedding(self,label,source_property,embedding_property):
        '''
        1.从图数据库中提取指定节点的文本数据。
        2.使用嵌入模型将文本数据转换为嵌入向量。
        3.将嵌入向量存储回图数据库中对应的节点属性中。
        4.返回嵌入向量的维度。
        '''
        cypher = f'''
                MATCH (n:{label}) RETURN n.{source_property} AS text,id(n) AS id
        '''
        results = self.graph.query(cypher) #🌳字典形式
        docs = [result['text'] for result in results]
        embeddings = self.embedding_model.embed_documents(docs)

        batch_embedding=[]
        for result,embedding in zip(results,embeddings):
            item = {'id':result['id'],'embedding':embedding}
            batch_embedding.append(item)

        cypher = f'''
                UNWIND $BATCH_EMBEDDING AS item
                MATCH (n:{label}) WHERE id(n) = item.id
                SET n.{embedding_property} = item.embedding
        '''
        self.graph.query(cypher,params={'BATCH_EMBEDDING':batch_embedding})
        return len(embeddings[0])

if __name__ == '__main__':
    index_util = IndexUtil()

    #1.疾病节点--索引
    index_util.create_full_text_index('disease_full_text_index','Disease','name')
    index_util.create_vector_index('disease_vector_index','Disease','name','embedding')
    print('🍊疾病节点--索引(全文+向量)已创建')

    #2.科室节点--索引
    index_util.create_full_text_index('department_full_text_index','Department','name')
    index_util.create_vector_index('department_vector_index','Department','name','embedding')
    print('🍊科室节点--索引(全文+向量)已创建')

    #3.症状节点--索引
    index_util.create_full_text_index('symptom_full_text_index','Symptom','name')
    index_util.create_vector_index('symptom_vector_index','Symptom','name','embedding')
    print('🍊症状节点--索引(全文+向量)已创建')

    #4.诱因节点--索引
    index_util.create_full_text_index('cause_full_text_index','Cause','desc')
    index_util.create_vector_index('cause_vector_index','Cause','desc','embedding')
    print('🍊诱因节点--索引(全文+向量)已创建')

    #5.药物节点--索引
    index_util.create_full_text_index('drug_full_text_index','Drug','name')
    index_util.create_vector_index('drug_vector_index','Drug','name','embedding')
    print('🍊药物节点--索引(全文+向量)已创建')

    #6.食物节点--索引
    index_util.create_full_text_index('food_full_text_index','Food','name')
    index_util.create_vector_index('food_vector_index','Food','name','embedding')
    print('🍊食物节点--索引(全文+向量)已创建')

    #7.传播途径节点--索引
    index_util.create_full_text_index('way_full_text_index','Way','desc')
    index_util.create_vector_index('way_vector_index','Way','desc','embedding')
    print('🍊传播途径节点--索引(全文+向量)已创建')

    #8.预防措施节点--索引
    index_util.create_full_text_index('preventWay_full_text_index','PreventWay','desc')
    index_util.create_vector_index('preventWay_vector_index','PreventWay','desc','embedding')
    print('🍊预防措施节点--索引(全文+向量)已创建')

    #9.医学检查节点--索引
    index_util.create_full_text_index('check_full_text_index','Check','name')
    index_util.create_vector_index('check_vector_index','Check','name','embedding')
    print('🍊医学检查节点--索引(全文+向量)已创建')

    #10.治疗方式节点--索引
    index_util.create_full_text_index('treat_full_text_index','Treat','name')
    index_util.create_vector_index('treat_vector_index','Treat','name','embedding')
    print('🍊治疗方式节点--索引(全文+向量)已创建')

    #11.人群类别节点--索引
    index_util.create_full_text_index('people_full_text_index','People','desc')
    index_util.create_vector_index('people_vector_index','People','desc','embedding')
    print('🍊人群类别节点--索引(全文+向量)已创建')

    #12.治疗周期索引--索引
    index_util.create_full_text_index('duration_full_text_index','Duration','desc')
    index_util.create_vector_index('duration_vector_index','Duration','desc','embedding')
    print('🍊治疗周期节点--索引(全文+向量)已创建')




