#测试 demo

from collections import defaultdict

#默认值为字典
dict_dict = defaultdict(dict)
# print(dict_dict)
dict_dict['person']['name']='小明'
dict_dict['person']['age']=25
print(dict_dict)
print(dict_dict['person'])