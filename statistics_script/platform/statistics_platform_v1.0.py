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

def convert_to_str(variable):
    try:
        return str(variable)
    except ValueError:
        return variable

def statisticsStatus(statusData):
    statusData['diff_basis'] = [convert_to_str(var) for var in statusData['diff_basis']]
    statusData['running_flag'] = [convert_to_str(var) for var in statusData['running_flag']]
    unmatchData = statusData[~(
        (
            (statusData['result'] == 'match') | (statusData['result'].str.startswith('pass-'))
        )
        |
        (
            (
                (statusData['result'] != 'match') & (~statusData['result'].str.startswith('pass-'))
            )
            &
            (
                (
                    (statusData['diff_basis'].str.split(';').apply(lambda x: all(item.startswith(('Diff', 'diff', 'pass-', '\"pass-', '“pass-', '”pass-', 'pass_')) for item in x)))
                )
                |
                (
                    (statusData['diff_basis'].str.contains('nan'))
                    &
                    ((statusData['running_flag'].str.split(';').apply(lambda x: all(item.startswith(('Diff', 'diff', 'pass-', '\"pass-', '“pass-', '”pass-', 'pass_')) for item in x))))
                )
            )
        )
    )
    ]
    
    if unmatchData.empty:
        return 'match'
    else:
        return 'unmatch'

def statisticsNum(msgData):
    msgTotal = 0
    unmatchMsgTotal = 0
    for msg, group in msgData:
        msgTotal += 1
        status = statisticsStatus(group)
        if status == 'unmatch':
            unmatchMsgTotal += 1  
    return msgTotal, unmatchMsgTotal
        
def addColFromAToB(da,db,colNameList):
    for colName in colNameList:
        db[colName] = [da[colName][index] for index in db.index]
    return db

def statistics(inData):
    dealFile_colNameList = inData.columns.values
    if 'enno_msgid' in dealFile_colNameList:
        eObjs = ['enno_msgid', 'enno_file_name', 'enno_line_num', 'e_severity', 'e_message']
    elif 'enno_id' in dealFile_colNameList:
        eObjs = ['enno_id', 'enno_file_name', 'enno_line_num', 'e_severity', 'e_message']
    sObjs = ['sg_rule', 'sg_file_name', 'sg_line_num', 's_severity', 's_message']
    inData = pandas.DataFrame(inData)
    eMsgDataTotal = inData[eObjs]
    sMsgDataTotal = inData[sObjs]
    eMsgDataTotalWithoutEmpty = eMsgDataTotal[((eMsgDataTotal != '-') & (eMsgDataTotal.notna())).any(axis=1)]
    sMsgDataTotalWithoutEmpty = sMsgDataTotal[((sMsgDataTotal != '-') & (sMsgDataTotal.notna())).any(axis=1)]

    eMsgDataTotalWithoutEmpty = addColFromAToB(inData, eMsgDataTotalWithoutEmpty, ['test_name', 'result', 'diff_basis', 'running_flag'])
    sMsgDataTotalWithoutEmpty = addColFromAToB(inData, sMsgDataTotalWithoutEmpty, ['test_name', 'result', 'diff_basis', 'running_flag'])

    eGroupData = eMsgDataTotalWithoutEmpty.groupby(eObjs + ['test_name'])
    sGroupData = sMsgDataTotalWithoutEmpty.groupby(sObjs + ['test_name'])

    eMsgNum, falseMsgNum = statisticsNum(eGroupData)
    sMsgNum, missingMsgNum = statisticsNum(sGroupData)
    return eMsgNum, sMsgNum, falseMsgNum, missingMsgNum

def statisticsFiles(files,is_csvFile):
    eMsgNumTotal = 0
    sMsgNumTotal = 0
    falseMsgNumTotal = 0
    missingMsgNumTotal = 0
    for sfile in files:
        print (f'start to statistics the {sfile}...')
        eMsgNum = 0
        sMsgNum = 0
        falseMsgNum = 0
        missingMsgNum = 0
        if is_csvFile:
            inData = pandas.read_csv(sfile,encoding='utf-8',encoding_errors='ignore',dtype={'diff_basis':str,'running_flag':str})
        else:
            inData = pandas.read_excel(sfile)
        
        eMsgNum, sMsgNum, falseMsgNum, missingMsgNum = statistics(inData)
        eMsgNumTotal += eMsgNum
        sMsgNumTotal += sMsgNum
        falseMsgNumTotal += falseMsgNum
        missingMsgNumTotal += missingMsgNum

    return eMsgNumTotal, sMsgNumTotal, falseMsgNumTotal, missingMsgNumTotal

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

    eMsgNumTotal = 0
    sMsgNumTotal = 0
    falseMsgNumTotal = 0
    missingMsgNumTotal = 0

    eMsgNum, sMsgNum, falseMsgNum, missingMsgNum = statisticsFiles(fileList, is_csvFile)
    eMsgNumTotal += eMsgNum
    sMsgNumTotal += sMsgNum
    falseMsgNumTotal += falseMsgNum
    missingMsgNumTotal += missingMsgNum

    falseRateTotal = divide(eMsgNumTotal, falseMsgNumTotal)
    missingRateTotal = divide(sMsgNumTotal, missingMsgNumTotal)

    end_time = time.time()
    print("程序运行时间为：{:.2f}秒".format(end_time - start_time))
    return {'e_msg_num':eMsgNumTotal, 's_msg_num':sMsgNumTotal, 'false_msg_num':falseMsgNumTotal, 'missing_msg_num':missingMsgNumTotal, 'false_rate':falseRateTotal, 'missing_rate':missingRateTotal}

if __name__ == '__main__':
    print(main())
