##测试代码

from datasets import load_dataset

dataset = load_dataset('json',data_files='../../data/knowledge_graph/medical_kg.jsonl')['train']
# print(dataset)
# features: ['name', 'desc', 'acompany', 'department', 'symptom', 'cause', 'drug', 'eat', 'not_eat', 'way', 'prevent',
#            'check', 'treat', 'people', 'duration'],
# num_rows: 3776
# print(len(dataset['name']))
# #
# print(type(dataset))
# print(type(dataset['name']))
# print(dataset['name'])
name = []
desc = []
for i,item in enumerate(dataset,1):
    name = item['name']
    desc = item['desc']
    print(name)
    print(desc)
    if i == 2:
        break


