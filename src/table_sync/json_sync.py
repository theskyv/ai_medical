from collections import defaultdict
from typing import List


from datasets import load_dataset

from neo4j import GraphDatabase

from src.configuration import config


class MedicalKGWriter:
    def __init__(self):
        self.driver = GraphDatabase.driver(**config.NEO4J_CONFIG)
        # 用于存储实体ID映射(名称→ID) 避免重复
        self.entity_ids = defaultdict(dict)  # {标签:{名称:ID}}

    def _generate_id(self, label, name):
        '''生辰唯一ID,确保同一类型实体名称唯一'''
        if name not in self.entity_ids[label]:
            # 生成格式如disease_1、symptom_3的ID
            new_id = f'{label.lower}_{len(self.entity_ids[label]) + 1}'
            self.entity_ids[label][name] = new_id
        return self.entity_ids[label][name]

    def write_disease_nodes(self, diseases: List[dict]):
        '''写入疾病节点(包含name和desc属性)'''
        cypher = '''UNWIND $diseases AS disease
                    MERGE (d:Disease {id:disease.id,name:disease.name})
                    SET d.desc = disease.desc
        '''
        self.driver.execute_query(cypher, diseases=diseases)

    def write_simple_nodes(self, label, entities:List[dict]):
        '''写入只有name属性的简单节点(科室,症状,药物,食物,传播途径,医学检查,治疗方式,人群类别,治疗周期等)'''
        cypher = f'''
                 UNWIND $entities AS entity
                 MERGE (e:{label} {{id:entity.id, name:entity.name}})
        '''
        self.driver.execute_query(cypher, entities=entities)

    def write_desc_nodes(self, label, entities:List[dict]):
        '''写入只有desc属性的节点(诱因、预防措施)'''
        cypher = f'''
                 UNWIND $entities AS entity
                 MERGE (e:{label} {{id:entity.id, desc:entity.desc}})      
        '''
        self.driver.execute_query(cypher, entities=entities)

    def write_relations(self, rel_type, start_label, end_label, relations):
        '''写入实体间的关系'''
        cypher = f'''
                 UNWIND $relations AS rel
                 MATCH (s:{start_label} {{id:rel.start_id}})
                 MATCH (e:{end_label} {{id:rel.end_id}})
                 MERGE (s)-[r:{rel_type}]->(e)
        '''
        self.driver.execute_query(cypher, relations=relations)


## features: ['name', 'desc', 'accompany', 'department', 'symptom', 'cause', 'drug', 'eat',
# 'not_eat', 'way', 'prevent', 'check', 'treat', 'people', 'duration'],
if __name__ == '__main__':
    # 加载数据集
    dataset = load_dataset('json', data_files='../../data/knowledge_graph/medical_kg.jsonl')['train']
    print(f"✅ 成功加载数据集，共包含 {len(dataset)} 种疾病数据")

    # 初始化写入器
    kg_writer = MedicalKGWriter()
    print(f"✅ 医疗知识图谱写入器初始化完成（连接Neo4j：{config.NEO4J_CONFIG.get('uri')}）")

    all_relations = []  # 存储所有关系
    for item in dataset:
        # 🔥1.1处理疾病节点(Disease)
        disease_name = item['name']
        disease_id = kg_writer._generate_id('Disease', disease_name)
        disease_data = {
            'id': disease_id,
            'name': disease_name,
            'desc': item.get('desc', '')
        }
        kg_writer.write_disease_nodes([disease_data])  # 单次写入一个疾病

        # 🔥1.2处理伴随疾病(Accompany)及关系(多值列表)
        accompanies = item.get('accompany', [])
        for acc_name in accompanies:
            if acc_name:  # 跳过空值
                # 伴随疾病也是Disease类型
                acc_id = kg_writer._generate_id('Disease', acc_name)
                # 确保伴随疾病节点已创建
                kg_writer.write_disease_nodes([{
                    'id': acc_id,
                    'name': acc_name,
                    'desc': ''
                }])

                all_relations.append({
                    'start_id': disease_id,
                    'end_id': acc_id,
                    'rel_type': 'ACCOMPANY',
                    'start_label': 'Disease',
                    'end_label': 'Disease'
                })

        # 🔥1.3 处理科室(Department)及关系
        departments = item.get('department', [])
        for dept_name in departments:
            if dept_name:  # 跳过空值
                dept_id = kg_writer._generate_id('Department', dept_name)
                kg_writer.write_simple_nodes('Department', [{'id': dept_id, 'name': dept_name}])
                # 🍑疾病-->科室 的belong关系
                all_relations.append({
                    'start_id': disease_id,
                    'end_id': dept_id,
                    'rel_type': 'BELONG',
                    'start_label': 'Disease',
                    'end_label': 'Department'
                })

        # 🔥 1.4 处理症状(Symptom)及关系(多值列表)
        symptoms = item.get('symptom', [])
        for symptom_name in symptoms:
            if symptom_name:  # 跳过空值
                symptom_id = kg_writer._generate_id('Symptom', symptom_name)
                kg_writer.write_simple_nodes('Symptom', [{'id': symptom_id, 'name': symptom_name}])

                # 疾病-->症状 HAVE
                all_relations.append({
                    'start_id': disease_id,
                    'end_id': symptom_id,
                    'rel_type': 'HAVE',
                    'start_label': 'Disease',
                    'end_label': 'Symptom'
                })

        # 🔥1.5处理诱因及关系
        cause_desc = item.get('cause', '')
        if cause_desc:
            cause_id = kg_writer._generate_id('Cause', cause_desc)
            kg_writer.write_desc_nodes('Cause', [{'id': cause_id, 'desc': cause_desc}])
            all_relations.append({
                'start_id': cause_id,
                'end_id': disease_id,
                'rel_type': 'LEAD_TO',
                'start_label': 'Cause',
                'end_label': 'Disease'
            })

        # 🔥1.6处理药物及关系
        drugs = item.get('drug', [])
        for drug_name in drugs:
            if drug_name:  # 跳过空值
                drug_id = kg_writer._generate_id('Drug', drug_name)
                kg_writer.write_simple_nodes('Drug', [{'id':drug_id,'name':drug_name}])
                # 疾病-->药物 COMMON_USE
                all_relations.append({
                    'start_id': disease_id,
                    'end_id': drug_id,
                    'rel_type': 'COMMON_USE',
                    'start_label': 'Disease',
                    'end_label': 'Drug'
                })

        # 🔥1.7食物及关系
        food_eat = item.get('eat', [])
        for food_name in food_eat:
            if food_name:
                food_id = kg_writer._generate_id('Food', food_name)
                kg_writer.write_simple_nodes('Food', [{'id':food_id,'name':food_name}])

                # 疾病-->食物 EAT
                all_relations.append({
                    'start_id': disease_id,
                    'end_id': food_id,
                    'rel_type': 'EAT',
                    'start_label': 'Disease',
                    'end_label': 'Food'
                })

        food_no_eat = item.get('not_eat', [])
        for food_name in food_no_eat:
            if food_name:
                food_id = kg_writer._generate_id('Food', food_name)
                kg_writer.write_simple_nodes('Food', [{'id':food_id,'name':food_name}])

                # 疾病-->食物 EAT
                all_relations.append({
                    'start_id': disease_id,
                    'end_id': food_id,
                    'rel_type': 'NO_EAT',
                    'start_label': 'Disease',
                    'end_label': 'Food'
                })

        # 🔥1.8传播途径及关系
        way_desc = item.get('way', '')
        if way_desc:
            way_id = kg_writer._generate_id('Way', way_desc)
            kg_writer.write_desc_nodes('Way', [{'id':way_id,'desc':way_desc}])

            # 疾病-->传播途径 TRANSMIT
            all_relations.append({
                'start_id': disease_id,
                'end_id': way_id,
                'rel_type': 'TRANSMIT',
                'start_label': 'Disease',
                'end_label': 'Way'
            })

        # 🔥1.9预防措施
        prevent_desc = item.get('prevent', '')
        if prevent_desc:
            prevent_id = kg_writer._generate_id('PreventWay', prevent_desc)
            kg_writer.write_desc_nodes('PreventWay', [{'id': prevent_id, 'desc': prevent_desc}])

            # 预防措施-->疾病 PREVENT
            all_relations.append({
                'start_id': prevent_id,
                'end_id': disease_id,
                'rel_type': 'PREVENT',
                'start_label': 'PreventWay',
                'end_label': 'Disease'
            })

        # 🔥1.10医学检查
        checks = item.get('check', [])
        for check_name in checks:
            if check_name:  # 跳过空值
                check_id = kg_writer._generate_id('Check', check_name)
                kg_writer.write_simple_nodes('Check', [{'id': check_id, 'name': check_name}])
                # 医学检查-->疾病 检查
                all_relations.append({
                    'start_id': check_id,
                    'end_id': disease_id,
                    'rel_type': 'TO_CHECK',
                    'start_label': 'Check',
                    'end_label': 'Disease'
                })

        # 🔥1.11治疗方式
        treats = item.get('treat', [])
        for treat_name in treats:
            if treat_name:  # 跳过空值
                treat_id = kg_writer._generate_id('Treat', treat_name)
                kg_writer.write_simple_nodes('Treat', [{'id': treat_id, 'name': treat_name}])
                # 治疗方式-->疾病  治疗
                all_relations.append({
                    'start_id': treat_id,
                    'end_id': disease_id,
                    'rel_type': 'TO_TREAT',
                    'start_label': 'Treat',
                    'end_label': 'Disease'
                })
        # 🔥1.12人群类别
        people_desc = item.get('people', '')
        if people_desc:  # 跳过空值
            people_id = kg_writer._generate_id('People', people_desc)
            kg_writer.write_desc_nodes('People', [{'id': people_id, 'desc': people_desc}])
            # 疾病-->人群类别  COMMON_ON
            all_relations.append({
                'start_id': disease_id,
                'end_id': people_id,
                'rel_type': 'COMMON_ON',
                'start_label': 'Disease',
                'end_label': 'People'
            })

        # 🔥1.13治疗周期
        dur_desc = item.get('duration', '')
        if dur_desc:  # 跳过空值
            duration_id = kg_writer._generate_id('Duration', dur_desc)
            kg_writer.write_desc_nodes('Duration', [{'id': duration_id, 'desc': dur_desc}])
            # 疾病-->人群类别  COMMON_ON
            all_relations.append({
                'start_id': disease_id,
                'end_id': duration_id,
                'rel_type': 'TREAT_DURATION',
                'start_label': 'Disease',
                'end_label': 'Duration'
            })

    # 2.批量写入所有关系(优化:按关系类型分组批量写入,提高效率)
    relation_groups = defaultdict(list)  # {'key1':[],'key2':[],...}
    for rel in all_relations:
        key = (rel['rel_type'], rel['start_label'], rel['end_label'])
        relation_groups[key].append({'start_id': rel['start_id'], 'end_id': rel['end_id']})

    for (rel_type, start_label, end_label), relations in relation_groups.items():
        kg_writer.write_relations(rel_type, start_label, end_label, relations)
    print(f'医疗知识图谱写入完成！\n共处理{len(dataset)}种疾病,生成{len(all_relations)}条关系') #共处理3776种疾病,生成131791条关系

