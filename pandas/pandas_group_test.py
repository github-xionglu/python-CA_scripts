import pandas as pd

# 创建一个示例DataFrame
data = {
    'A': ['a', '-', '-', '', 'a', 'a', 'd'],
    'B': ['', '-', '-', '', 'b', 'c', 's'],
    'C': ['a', '-', 'b', '', 'c', 'ac;cd;cs', 'ca;cc;se'],
    'D': ['a', '-', '-', '', 'b', 'c', 'e'],
    'E': ['a', '-', 'b', '', 'c', 'd', 's']
}
df = pd.DataFrame(data)

non_empty_rows = df[((df != '-') & (df != '')).any(axis=1)]
print (non_empty_rows)
print('- - - -')
aa = [data['E'][index] for index in non_empty_rows.index]
print (aa)
# print('\n'.join(map(str, aa)))
print ('-----===========------')

# # 打印非空行
# print(non_empty_rows)
# non_empty_rows = non_empty_rows.reset_index()
# print(non_empty_rows)


# for index in non_empty_rows.index:
#     print (index)
#     print (non_empty_rows.iloc[index])
#     print ('==========')
listA = ['A','D']
listA.append('E')
print (listA)
groupData = non_empty_rows.groupby(listA)

for name, group in groupData:
    print(f"Group: {name}")
    # print(group[['C','D']])
    bb = group[['C','D']]
    # print (f'bb:\n{bb.loc[bb['C'] == 'c']}')
    print (bb)
    print('------------')
    cc = bb.loc[
        (bb['C'].str.split(';').apply(lambda x: all(xitem.startswith('a') or xitem.startswith('c') for xitem in x)))
    ]
    # cc = bb.loc[
    #     (bb['C'].str.startswith(tuple(['a','c'])))
    # ]
    print (cc)
    print("=============")
