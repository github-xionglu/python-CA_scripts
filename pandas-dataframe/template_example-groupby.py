import pandas as pd

# 创建一个示例DataFrame
data = {
    'A': ['a', '-', '-', '', 'a', 'a'],
    'B': ['', '-', '-', '', 'b', 'c'],
    'C': ['a', '-', 'b', '', 'c', 'ca'],
    'D': ['a', '-', '-', '', 'b', 'c'],
    'E': ['a', '-', 'b', '', 'c', 'd']
}
df = pd.DataFrame(data)

non_empty_rows = df[((df != '-') & (df != '')).any(axis=1)]

# # 打印非空行
# print(non_empty_rows)
# non_empty_rows = non_empty_rows.reset_index()
# print(non_empty_rows)


# for index in non_empty_rows.index:
#     print (index)
#     print (non_empty_rows.iloc[index])
#     print ('==========')

groupData = non_empty_rows.groupby(['A','D'])

for name, group in groupData:
    print(f"Group: {name}")
    # print(group[['C','D']])
    bb = group[['C','D']]
    # print (f'bb:\n{bb.loc[bb['C'] == 'c']}')
    print (bb)
    print('------------')
    cc = bb.loc[
        (bb['C'].str.startswith(tuple(['a','c'])))
    ]
    print (cc)
    print("=============")

#### return ####
Group: ('-', '-')
   C  D
2  b  -
------------
Empty DataFrame
Columns: [C, D]
Index: []
=============
Group: ('a', 'a')
   C  D
0  a  a
------------
   C  D
0  a  a
=============
Group: ('a', 'b')
   C  D
4  c  b
------------
   C  D
4  c  b
=============
Group: ('a', 'c')
    C  D
5  ca  c
------------
    C  D
5  ca  c
=============
