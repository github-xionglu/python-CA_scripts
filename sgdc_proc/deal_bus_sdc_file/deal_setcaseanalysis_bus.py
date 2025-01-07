import sys
import time
import os
import re
import getopt

def printUsage():
    print("usage: %s -f <file1> -f <file2> ... [--csv]" % (sys.argv[0]))
    print('''
    [-f|--file <file>]*     :   specify the sdc file
    -h|--help               :   show help manual
    ''')
    sys.exit(-1)

def replace_in_file(file_path, base):

    old_pattern_without_bit = r'set_case_analysis \{b (\d+)\} -objects \[get_ports (\w+)\]'
    old_pattern_with_bit_range = r'set_case_analysis \{b (\d+)\} -objects \[get_ports (\w+)\[(\d+):(\d+)\]\]'
    new_pattern = 'set_case_analysis {} -objects [get_ports {}[{}]]'

    # 读取文件内容
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # 遍历每一行
    for i, line in enumerate(lines):
        # print (f'-----{i + 1}:{line}--------')
        # 查找匹配的内容
        match1 = re.search(old_pattern_without_bit, line)
        if match1:
            # 获取匹配的内容
            content = match1.group(0)
            value_str = match1.group(1)
            obj_name = match1.group(2)
            repeated_strings = [new_pattern.format(x,y,i) for x, y, i in zip(value_str, [obj_name]*len(value_str), list(range(len(value_str)-1, -1, -1)))]
            new_line = "; ".join(repeated_strings)
            lines[i] = f'{new_line}\n'
        else:
            match2 = re.search(old_pattern_with_bit_range, line)
            if match2:
                value_str = match2.group(1)
                obj_name = match2.group(2)
                from_num = match2.group(3)
                to_num = match2.group(4)
                numLen = len(value_str)
                if int(from_num) > int(to_num):
                    busRange = range(int(from_num), int(to_num) - 1, -1)
                    numSort = 1
                else:
                    busRange = range(int(from_num), int(to_num) + 1)
                    numSort = 0

                busLen = len(busRange)
                if busLen == numLen:
                    repeated_strings = [new_pattern.format(x,y,i) for x, y, i in zip(value_str, [obj_name]*busLen, busRange)]
                    new_line = "; ".join(repeated_strings)
                    lines[i] = f'{new_line}\n'
                elif busLen > numLen:
                    if numSort:
                        value_str = '0'*(busLen - numLen) + value_str
                    else:
                        value_str += '0'*(busLen - numLen)
                    repeated_strings = [new_pattern.format(x,y,i) for x, y, i in zip(value_str, [obj_name]*busLen, busRange)]
                    new_line = "; ".join(repeated_strings)
                    lines[i] = f'{new_line}\n'
                else:
                    continue

    # 写入修改后的内容
    with open(file_path, 'w') as file:
        file.writelines(lines)

def main():
    start_time = time.time()
    runOK = 0
    fileList = []

    try:
        opts,args =  getopt.getopt(sys.argv[1:],"hf:",["help","file="])
    except getopt.GetoptError:
        printUsage()

    for opt,arg in opts:
        if opt in ('-h','--help'):
            printUsage()
        elif opt in ("-f","--file"):
            runOK = 1
            fileList.append(arg)

    if runOK == 0:
        print("Error: No valid input")
        printUsage

    for sfile in fileList:
        # 使用函数
        replace_in_file(sfile, 2)

    end_time = time.time()
    print("程序运行时间为：{:.2f}秒".format(end_time - start_time))


if __name__ == '__main__':
    main()
