import sys
import time
import os
import re
import pandas
import getopt
import codecs
from tqdm import tqdm

def printUsage():
    print("usage: %s -c <ac file> -r <ar file> -s <setup file> -b <syntax file> --csv" % (sys.argv[0]))
    print('''
    [-c|--ac <ac file>]*                    :   specify the result file about the Ac rules
    [-r|--ar <ar file>]*                    :   specify the result file about the Ar rules
    [-s|--setup <setup file>]*              :   specify the result file about the Setup or Conv rules
    [-b|--builtin|--syntax <syntax file>]*  :   specify the result file about the syntax rules
    --csv                                   :   specify the specified result files type [default: excel]
    -h|--help                               :   show help manual
    ''')
    sys.exit(-1)

def getObjs(mode):
    if mode == 'ac':
        eObjs = ['enno_msgid', 'enno_file_name', 'enno_line_num', 'e_severity', 'e_message']
        sObjs = ['sg_rule', 'sg_file_name', 'sg_line_num', 's_severity', 's_message']
    elif mode == 'ar':
        eObjs = ['enno_id', 'enno_file_name', 'enno_line_num', 'e_severity', 'e_message']
        sObjs = ['sg_rule', 'sg_file_name', 'sg_line_num', 's_severity', 's_message']
    elif mode == 'setup':
        eObjs = ['enno_msgid', 'enno_file_name', 'enno_line_num', 'e_severity', 'e_message']
        sObjs = ['sg_rule', 'sg_file_name', 'sg_line_num', 's_severity', 's_message']
    elif mode == 'syntax':
        eObjs = ['enno_msgid', 'enno_file_name', 'enno_line_num', 'e_severity', 'e_message']
        sObjs = ['sg_rule', 'sg_file_name', 'sg_line_num', 's_severity', 's_message']
    
    return eObjs, sObjs

def markMsgStatus(totalData,msgData,flagCols):
    # msgData['result'] = None
    result = []
    msgData = msgData.reset_index()
    for index in msgData.index:
        isPass = 1
        messageLine = msgData.iloc[index]
        refMatchLines = totalData.loc[
            (totalData[flagCols[0]] == messageLine[flagCols[0]])
            &
            (totalData[flagCols[1]] == messageLine[flagCols[1]])
            &
            (totalData[flagCols[2]] == messageLine[flagCols[2]])
            &
            (totalData[flagCols[3]] == messageLine[flagCols[3]])
            &
            (totalData[flagCols[4]] == messageLine[flagCols[4]])
        ]

        for refMatchLinesIndex in refMatchLines.index:
            refResultValue = totalData.at[refMatchLinesIndex, 'result']
            if pandas.notna(refResultValue):
                refResultValue = str(refResultValue).strip()
            else:
                isPass = 0
                break
            
            if refResultValue != "Missing report" and refResultValue != "False report" and refResultValue != "Unmatch" and refResultValue != "pass":
                isPass = isPass
                continue
            elif refResultValue == "Missing report" or refResultValue == "False report" or refResultValue == "Unmatch" or refResultValue == "pass":
                refDiffIdValue = totalData.at[refMatchLinesIndex,'diff_basis']
                if pandas.notna(refDiffIdValue):
                    # refDiffIdValue = str(';'.join(str(refDiffIdValue).strip().split()))
                    isPass = isPass
                    for markItem in refDiffIdValue.split(";"):
                        if str(markItem).startswith('Diff') or str(markItem).startswith('diff') or str(markItem).startswith('pass-') or str(markItem).startswith('\"pass-'):
                            isPass = isPass
                        elif str(markItem).startswith('“pass-') or str(markItem).startswith('”pass-') or str(markItem).startswith('pass_'):
                            isPass = isPass
                        elif str(markItem).startswith('CDC') or str(markItem).startswith('cdc'):
                            isPass = 0
                            break
                        else:
                            isPass = 0
                            break
                    if  isPass == 0:
                        break
                    elif isPass == 1:
                        continue
                else:
                    refDiffIdValue = totalData.at[refMatchLinesIndex,'running_flag']
                    if pandas.notna(refDiffIdValue):
                        isPass = isPass
                        for markItem in refDiffIdValue.split(";"):
                            if str(markItem).startswith('Diff') or str(markItem).startswith('diff') or str(markItem).startswith('pass-') or str(markItem).startswith('\"pass-'):
                                isPass = isPass
                            elif str(markItem).startswith('“pass-') or str(markItem).startswith('”pass-') or str(markItem).startswith('pass_'):
                                isPass = isPass
                            elif str(markItem).startswith('CDC') or str(markItem).startswith('cdc'):
                                isPass = 0
                                break
                            else:
                                isPass = 0
                                break
                        if  isPass == 0:
                            break
                        elif isPass == 1:
                            continue
                    else:
                        isPass = 0
                        break
        if isPass == 0:
            # msgData.loc[index, 'result'] = 'unmatch'
            result.append('unmatch')
        elif isPass == 1:
            # msgData.loc[index, 'result'] = 'match'
            result.append('match')

    msgData['result'] = result
    return msgData.loc[msgData['result'] == 'unmatch']


def statistics(inData,mode):
    eObjs, sObjs = getObjs(mode)
    inData = pandas.DataFrame(inData)
    eMsgDataTotal = inData[eObjs]
    sMsgDataTotal = inData[sObjs]
    eMsgDataTotalWithoutEmpty = eMsgDataTotal[((eMsgDataTotal != '-') & (eMsgDataTotal.notna())).any(axis=1)]
    sMsgDataTotalWithoutEmpty = sMsgDataTotal[((sMsgDataTotal != '-') & (sMsgDataTotal.notna())).any(axis=1)]
    eMsgData = eMsgDataTotalWithoutEmpty.drop_duplicates(subset=eObjs, keep='first')
    sMsgData = sMsgDataTotalWithoutEmpty.drop_duplicates(subset=sObjs, keep='first')

    FalseMsgData = markMsgStatus(inData,eMsgData,eObjs)
    MissingMsgData = markMsgStatus(inData,sMsgData,sObjs)

    return len(eMsgData.index), len(sMsgData.index), len(FalseMsgData.index), len(MissingMsgData.index)

def statisticsFiles(files,is_csvFile,mode):
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
        
        eMsgNum, sMsgNum, falseMsgNum, missingMsgNum = statistics(inData,mode)
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
    acFileList = []
    arFileList = []
    setupFileList = []
    syntaxFileList = []
    acRun = 0
    arRun = 0
    setupRun = 0
    syntaxRun = 0

    try:
        opts,args =  getopt.getopt(sys.argv[1:],"hc:r:s:b:",["help","ac=","ar=","setup=","builtin=","syntax=","csv"])
    except getopt.GetoptError:
        printUsage()

    for opt,arg in opts:
        if opt in ('-h','--help'):
            printUsage()
        elif opt in ("-c","--ac"):
            acRun = 1
            acFileList.append(arg)
        elif opt in ("-r","--ar"):
            arRun = 1
            arFileList.append(arg)
        elif opt in ("-s","--setup"):
            setupRun = 1
            setupFileList.append(arg)
        elif opt in ("-b","--builtin","--syntax"):
            syntaxRun = 1
            syntaxFileList.append(arg)
        elif opt == "--csv":
            is_csvFile = 1

    if acRun == 0 and arRun == 0 and setupRun == 0 and syntaxRun == 0:
        print("Error: Invalid input")
        printUsage

    eMsgNumTotal = 0
    sMsgNumTotal = 0
    falseMsgNumTotal = 0
    missingMsgNumTotal = 0

    if acRun == 1:
        eMsgNum, sMsgNum, falseMsgNum, missingMsgNum = statisticsFiles(acFileList, is_csvFile, "ac")
        eMsgNumTotal += eMsgNum
        sMsgNumTotal += sMsgNum
        falseMsgNumTotal += falseMsgNum
        missingMsgNumTotal += missingMsgNum

    if arRun == 1:
        eMsgNum, sMsgNum, falseMsgNum, missingMsgNum = statisticsFiles(arFileList, is_csvFile, "ar")
        eMsgNumTotal += eMsgNum
        sMsgNumTotal += sMsgNum
        falseMsgNumTotal += falseMsgNum
        missingMsgNumTotal += missingMsgNum

    if setupRun == 1:
        eMsgNum, sMsgNum, falseMsgNum, missingMsgNum = statisticsFiles(setupFileList, is_csvFile, "setup")
        eMsgNumTotal += eMsgNum
        sMsgNumTotal += sMsgNum
        falseMsgNumTotal += falseMsgNum
        missingMsgNumTotal += missingMsgNum

    if syntaxRun == 1:
        eMsgNum, sMsgNum, falseMsgNum, missingMsgNum = statisticsFiles(syntaxFileList, is_csvFile, "syntax")
        eMsgNumTotal += eMsgNum
        sMsgNumTotal += sMsgNum
        falseMsgNumTotal += falseMsgNum
        missingMsgNumTotal += missingMsgNum

    falseRateTotal = divide(eMsgNumTotal, falseMsgNumTotal)
    missingRateTotal = divide(sMsgNumTotal, missingMsgNumTotal)

    return {'e_msg_num':eMsgNumTotal, 's_msg_num':sMsgNumTotal, 'false_msg_num':falseMsgNumTotal, 'missing_msg_num':missingMsgNumTotal, 'false_rate':falseRateTotal, 'missing_rate':missingRateTotal}

if __name__ == '__main__':
    print(main())
