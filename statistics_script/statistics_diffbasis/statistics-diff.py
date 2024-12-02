import sys
import time
import os
import re
import pandas
import getopt

def printUsage():
    print("usage: %s -f <file1> -f <file2> ... [--csv]" % (sys.argv[0]))
    print('''
    [-f|--file <file>]*     :   specify the result file about the Ac rules
    -c|--csv                :   specify the specified result files type [default: excel]
    -h|--help               :   show help manual
    ''')
    sys.exit(-1)

def statistics(inData):
    diffBasisDict = {}
    diffBasisGroup = inData.groupby('diff_basis')
    for diff, group in diffBasisGroup:
        num = len(group.index)
        diffBasisDict[diff] = num

    return diffBasisDict

def mergeDictBySum(dictA, dictB):
    dictC = dictA.copy()
    for key, value in dictB.items():
        if key in dictC:
            dictC[key] += value
        else:
            dictC[key] = value
    return dictC

def statisticsFiles(files,is_csvFile):
    diffDictTotal = {}
    for sfile in files:
        print (f'start to statistics the {sfile}...')
        diffDict = {}
        if is_csvFile:
            inData = pandas.read_csv(sfile,encoding='utf-8',encoding_errors='ignore',dtype={'diff_basis':str,'running_flag':str})
        else:
            inData = pandas.read_excel(sfile)
        
        diffDict = statistics(inData)
        diffDictTotal = mergeDictBySum(diffDictTotal,diffDict)

    return diffDictTotal

def divide(a, b):
    try:
        return '{:.2%}'.format(b / a)
    except ZeroDivisionError:
        return '{:.2%}'.format(0)

def main():
    start_time = time.time()

    is_csvFile = 0
    fileList = []
    runOK = 0

    try:
        opts,args =  getopt.getopt(sys.argv[1:],"hcf:",["help","file=","csv"])
    except getopt.GetoptError:
        printUsage()

    for opt,arg in opts:
        if opt in ('-h','--help'):
            printUsage()
        elif opt in ("-f","--file"):
            runOK = 1
            fileList.append(arg)
        elif opt in ("-c","--csv"):
            is_csvFile = 1

    if runOK == 0:
        print("Error: Invalid input")
        printUsage

    diffDict = statisticsFiles(fileList, is_csvFile)
    end_time = time.time()
    print("程序运行时间为：{:.2f}秒".format(end_time - start_time))

    dealDiffDict = {}
    for key, val in diffDict.items():
        for ikey in key.split(';'):
            if ikey in dealDiffDict:
                dealDiffDict[ikey] += val
            else:
                dealDiffDict[ikey] = val
    return (dealDiffDict)

if __name__ == '__main__':
    # print(main())
    diffDict = main()
    df = pandas.DataFrame({'diff_id': diffDict.keys(), 'num': diffDict.values()})
    df.to_excel('statistics.xlsx', index=False)
