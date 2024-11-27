import sys
import openpyxl
import time
import os
import shutil
import re
import pandas
import getopt
import csv
import codecs
from tqdm import tqdm
import inspect
import subprocess

def printUsage(lineno):
    print("usage: %s <-r|--ref <ref file>> [-e|--enno <enno result file>] [-s|--sg <sg result file>] [-m|--mode <Ac|Ar|Setup|Syntax mode>] [--csv] [--appendLabel] [--inferStatus <any|infer|uninfer>] [--dealDoubleQuotation] [--addColumn <column name>] (%s:%d)" % (sys.argv[0], os.path.abspath(__file__), lineno))
    print('''   
    -r|--ref <ref file>                 :   specify the reference file
    -e|--enno <enno result file>        :   specify the enno result file witch need be marked
    -s|--sg <sg result file>            :   specify the sg result file witch need be marked
    -m|--mode <Ac|Ar|Setup|Syntax>      :   specify the mark result mode: Ac or Ar or Setup or Syntax. [default: Ac]
    --csv                               :   specify the input files are the csv file
    --appendLabel                       :   specify the running mode: mark or appendLabel. [default: mark]
    --inferStatus                       :   specify the infer status: any, infer or uninfer. [default: any]
    --dealDoubleQuotation               :   specify the input files are the csv file
    --addColumn <column name>           :   add column from ref file to result file
    -h|--help                           :   show help manual
    ''')
    sys.exit(-1)

def convert_to_int(variable):
    try:
        return int(variable)
    except ValueError:
        return variable

def converge_to_int_for_col_of_dataFrame(data, colName):
    data[colName] = [convert_to_int(var) for var in refData[colName]]
    return data

def repr_invalid_str(variable):
    if '\1' in str(variable):
        variable = repr(variable)
    return variable

start_time = time.time()

csvType = 0
refFile = ""
ennoFile = ""
sgFile = ""
ennoXlsx = ""
sgXlsx = ""
mode = "Ac"
appendLabel = 0
inferStatus = "any"
dealDoubleQuotation = False
addColumn = False
addColumnName = ""

try:
    opts,args =  getopt.getopt(sys.argv[1:],"hr:e:s:m:",["help","ref=","enno=","sg=","mode=","csv","appendLabel","inferStatus=","dealDoubleQuotation","addColumn="])
except getopt.GetoptError:
    printUsage(0)

for opt,arg in opts:
    if opt in ('-h',"--help"):
        printUsage(0)
    elif opt in ("-r","--ref"):
        refFile = arg
    elif opt in ("-e", "--enno"):
        ennoFile = arg
    elif opt in ("-s", "--sg"):
        sgFile = arg
    elif opt in ("-m", "--mode"):
        mode = arg
    elif opt == "--csv":
        csvType = 1
    elif opt == "--appendLabel":
        appendLabel = 1
    elif opt == "--inferStatus":
        inferStatus = arg
    elif opt == "--dealDoubleQuotation":
        dealDoubleQuotation = True
    elif opt == "--addColumn":
        addColumn = True
        addColumnName = arg

if bool(refFile):
    if os.path.exists(refFile):
        refFileName = os.path.basename(refFile)
        if os.path.splitext(refFileName)[1] == ".csv":
            if dealDoubleQuotation:
                optmizeFile = f'{os.path.splitext(refFileName)[0]}_opt.csv'
                shutil.copy(refFile,optmizeFile)
                subprocess.call(["sed", "-i", "s/\"/\"\"/g", optmizeFile])
                subprocess.call(["sed", "-i", "s/,\"\"/,\"/g; s/\"\",/\",/g; s/\"\"$/\"/g", optmizeFile])
                refData = pandas.read_csv(optmizeFile,encoding='utf-8',encoding_errors='ignore',sep=',')
            else:
                refData = pandas.read_csv(refFile,encoding='utf-8',encoding_errors='ignore',sep=',')
        elif os.path.splitext(refFileName)[1] == ".xlsx":
            refData = pandas.read_excel(refFile)
        else:
            print("Error: invalid reference file type: " + refFile)
            sys.exit(0)
    else:
        print("Error: there is not such file: " + refFile)
        sys.exit(0)
else:
    print("Error: there is reference file, please check it")
    sys.exit(0)

refData['enno_line_num'] = [convert_to_int(var) for var in refData['enno_line_num']]
refData['sg_line_num'] = [convert_to_int(var) for var in refData['sg_line_num']]
refData['e_message'] = [repr_invalid_str(var) for var in refData['e_message']]
refData['s_message'] = [repr_invalid_str(var) for var in refData['s_message']]

if addColumn:
    if addColumnName == "":
        print (f"Error: the name of the column is not invaild, {os.path.abspath(__file__)}:{sys._getframe().f_lineno}")
        printUsage(sys._getframe().f_lineno)
    if addColumnName not in refData.columns:
        print (f"Error: the column, {addColumnName}, is not exist in the ref file, {refFile}, {os.path.abspath(__file__)}:{sys._getframe().f_lineno}")
        printUsage(sys._getframe().f_lineno)

if inferStatus == "any":
    refData = refData
elif inferStatus == "infer":
    refData = refData[~refData['test_name'].str.startswith('uninfer_')]
elif inferStatus == "uninfer":
    refData = refData[refData['test_name'].str.startswith('uninfer_')]
else:
    print(f'Invalid argument {inferStatus} of the option "--inferStatus"')

if not bool(ennoFile) and not bool(sgFile):
    print ("Error: there is not correct input file, enno result file or/and sg result file")
    sys.exit(0)

runOK = 0
runEnno = 0
runSg = 0
if bool(ennoFile):
    if not os.path.exists(ennoFile):
        print("Warn: the " + ennoFile + " is not a file")
    else:
        if csvType == 0:
            ennoData = pandas.read_excel(ennoFile)
        elif csvType == 1:
            ennoData = pandas.read_csv(ennoFile,encoding='utf-8',encoding_errors='ignore',sep=',')
        ennoData['Line'] = [convert_to_int(var) for var in ennoData['Line']]
        ennoData['Message'] = [repr_invalid_str(var) for var in ennoData['Message']]
        runEnno = 1
        runOK = 1
if bool(sgFile):
    if not os.path.exists(sgFile):
        print("Warn: the " + sgFile + " is not a file")
    else:
        if csvType == 0:
            sgData = pandas.read_excel(sgFile)
        elif csvType == 1:
            sgData = pandas.read_csv(sgFile,encoding='utf-8',encoding_errors='ignore',sep=',')
        sgData['Line'] = [convert_to_int(var) for var in sgData['Line']]
        sgData['Message'] = [repr_invalid_str(var) for var in sgData['Message']]
        runSg = 1
        runOK = 1
if runOK == 0:
    sys.exit(0)

refTitles = refData.columns
if 'diff_basis' not in refTitles or 'enno_file_name' not in refTitles or 'sg_file_name' not in refTitles or 'e_message' not in refTitles or 's_message' not in refTitles:
    print("Error: the file " + refFile + " is not a standard workbook")
    print ('refTitles:' + refTitles)
    sys.exit(0)

fromTag = refFileName

logFile = "mark_ca_result.log"
writeLog = open(logFile,"w")

if runEnno == 1:
    enno_start_time = time.time()
    print (f'start mark enno result file...')
    if 'from' in ennoData.columns:
        pass
    else:
        ennoData['from'] = None

    if addColumn:
        if addColumnName in ennoData.columns:
            pass
        elif addColumnName not in ennoData.columns:
            ennoData[addColumnName] = None

    for index in tqdm(ennoData.index):
        isPass = 1
        messageLine = ennoData.iloc[index]
        ennoResultValue = messageLine['Result']
        if appendLabel == 0:
            flag = ennoResultValue == "ok" or ennoResultValue == "enno_reason_more" or ennoResultValue == "undo" or ennoResultValue == "auto_waive"
        elif appendLabel == 1:
            flag = not pandas.isnull(ennoResultValue)
        if flag:
            continue
        else:
            if messageLine['Message'] is None:
                continue
            messageStr = messageLine['Message']
            if mode == "Ac":
                refMatchLines = refData.loc[
                    (refData['enno_file_name'] == messageLine['File'])
                    &
                    (refData['e_message'].isin([messageLine['Message'], f'{messageStr} ']))
                    &
                    (refData['enno_msgid'] == messageLine['Enno_id'])
                    &
                    (refData['enno_reason'] == messageLine['ERule'])
                    &
                    (refData['enno_line_num'] == convert_to_int(messageLine['Line']))
                ]
            elif mode == "Ar":
                refMatchLines = refData.loc[
                    (refData['enno_file_name'] == messageLine['File'])
                    &
                    (refData['e_message'].isin([messageLine['Message'], f'{messageStr} ']))
                    &
                    (refData['enno_id'] == messageLine['Enno_id'])
                    &
                    (refData['enno_line_num'] == convert_to_int(messageLine['Line']))
                ]
            elif mode == "Setup":
                refMatchLines = refData.loc[
                    (refData['enno_file_name'] == messageLine['File'])
                    &
                    (refData['e_message'].isin([messageLine['Message'], f'{messageStr} ']))
                    &
                    (refData['enno_msgid'] == messageLine['ERule'])
                    &
                    (refData['enno_line_num'] == convert_to_int(messageLine['Line']))
                ]
            elif mode == "Syntax":
                refMatchLines = refData.loc[
                    (refData['enno_file_name'] == messageLine['File'])
                    &
                    (refData['e_message'].isin([messageLine['Message'], f'{messageStr} ']))
                    &
                    (refData['enno_msgid'] == messageLine['ERule'])
                    &
                    (refData['e_severity'] == messageLine['Severity'])
                    &
                    (refData['enno_line_num'] == convert_to_int(messageLine['Line']))
                ]
            else:
                refMatchLines = refData.loc[
                    (refData['enno_file_name'] == messageLine['File'])
                    &
                    (refData['e_message'].isin([messageLine['Message'], f'{messageStr} ']))
                    &
                    (refData['enno_msgid'] == messageLine['Enno_id'])
                    &
                    (refData['enno_reason'] == messageLine['ERule'])
                    &
                    (refData['enno_line_num'] == convert_to_int(messageLine['Line']))
                ]

            refMatchLinesIndexList = refMatchLines.index
            if len(refMatchLinesIndexList) == 0:
                # print("cannot found the message: " + ennoMsgCell_value + ", row num: " + str(i))
                writeLog.write("=====================\ncannot found the message: \n" + str(messageStr) + "\nrow num: " + str(index + 1) + "\n")
                writeLog.write("refMatchLines: \n" + str(refMatchLines) + "\n")
                ennoData.loc[index, 'Result'] = ""
                continue
            elif len(refMatchLinesIndexList) >= 1:
                writeLog.write(f'refMatchLines: \n{str(refMatchLines)}\n')
                forCAResult = []
                for refMatchLinesIndex in refMatchLinesIndexList:
                    refResultValue = refData.at[refMatchLinesIndex,'result']
                    if pandas.notna(refResultValue):
                        refResultValue = str(refResultValue).strip()
                    else:
                        isPass = 0
                        break
                    if refResultValue != "Missing report" and refResultValue != "False report" and refResultValue != "Unmatch" and refResultValue != "pass":
                        isPass = isPass
                        forCAResult.append(refResultValue)
                        continue
                    elif refResultValue == "Missing report" or refResultValue == "False report" or refResultValue == "Unmatch" or refResultValue == "pass":
                        refDiffIdValue = refData.at[refMatchLinesIndex,'diff_basis']
                        if pandas.notna(refDiffIdValue):
                            # refDiffIdValue = str(';'.join(str(refDiffIdValue).strip().split()))
                            isPass = isPass
                            forCAResult.extend(refDiffIdValue.split(";"))
                            continue
                        else:
                            refDiffIdValue = refData.at[refMatchLinesIndex,'running_flag']
                            if pandas.notna(refDiffIdValue):
                                #
                                isPass = isPass
                                forCAResult.extend(refDiffIdValue.split(";"))
                            else:
                                isPass = 0
                                break
                if not bool(isPass):
                    ennoData.loc[index, 'Result'] = ""
                    continue
                else:
                    ennoData.loc[index, 'from'] = fromTag
                    ennoData.loc[index, 'Result'] = str(";".join(sorted(set(sorted(forCAResult)))))
                
                if addColumn:
                    ennoData.loc[index, addColumnName] = repr(refData.at[refMatchLinesIndexList[0],addColumnName])

    ennoData.to_csv(ennoFile,index=False,encoding='utf-8')

    enno_end_time = time.time()
    print("enno反标运行时间为：{:.2f}秒".format(enno_end_time - enno_start_time))




if runSg == 1:
    sg_start_time = time.time()
    print (f'start mark sg result file...')

    if 'from' in sgData.columns:
        pass
    else:
        sgData['from'] = None

    if addColumn:
        if addColumnName in sgData.columns:
            pass
        elif addColumnName not in sgData.columns:
            sgData[addColumnName] = None

    for index in tqdm(sgData.index):
        isPass = 1
        messageLine = sgData.iloc[index]
        sgResultValue = messageLine['Result']
        if appendLabel == 0:
            flag = sgResultValue == "ok" or sgResultValue == "enno_reason_more" or sgResultValue == "undo"
        elif appendLabel == 1:
            flag = not pandas.isnull(sgResultValue)
        if flag:
            continue
        else:
            if messageLine['Message'] is None:
                continue
            messageStr = messageLine['Message']
            if mode == "Ac":
                refMatchLines = refData.loc[
                    (refData['sg_file_name'] == messageLine['File'])
                    &
                    (refData['s_message'].isin([messageLine['Message'], f'{messageStr} ']))
                    &
                    (refData['sg_reason'] == messageLine['ARule'])
                    &
                    (refData['sg_line_num'] == convert_to_int(messageLine['Line']))
                ]
            elif mode == "Ar":
                refMatchLines = refData.loc[
                    (refData['sg_file_name'] == messageLine['File'])
                    &
                    (refData['s_message'].isin([messageLine['Message'], f'{messageStr} ']))
                    &
                    (refData['sg_line_num'] == convert_to_int(messageLine['Line']))
                ]
            elif mode == "Setup":
                refMatchLines = refData.loc[
                    (refData['sg_file_name'] == messageLine['File'])
                    &
                    (refData['s_message'].isin([messageLine['Message'], f'{messageStr} ']))
                    &
                    (refData['sg_rule'] == messageLine['ARule'])
                    &
                    (refData['sg_line_num'] == convert_to_int(messageLine['Line']))
                ]
            elif mode == "Syntax":
                refMatchLines = refData.loc[
                    (refData['sg_file_name'] == messageLine['File'])
                    &
                    (refData['s_message'].isin([messageLine['Message'], f'{messageStr} ']))
                    &
                    (refData['sg_rule'] == messageLine['ARule'])
                    &
                    (refData['sg_line_num'] == convert_to_int(messageLine['Line']))
                ]
            else:
                refMatchLines = refData.loc[
                    (refData['sg_file_name'] == messageLine['File'])
                    &
                    (refData['s_message'].isin([messageLine['Message'], f'{messageStr} ']))
                    &
                    (refData['sg_reason'] == messageLine['ARule'])
                    &
                    (refData['sg_line_num'] == convert_to_int(messageLine['Line']))
                ]

            refMatchLinesIndexList = refMatchLines.index
            if len(refMatchLinesIndexList) == 0:
                writeLog.write("=====================\ncannot found the message: \n" + str(messageStr) + "\nrow num: " + str(index) + "\n")
                sgData.loc[index, 'Result'] = ''
                continue
            elif len(refMatchLinesIndexList) >= 1:
                forCAResult = []
                for refMatchLinesIndex in refMatchLinesIndexList:
                    refResultValue = refData.at[refMatchLinesIndex,'result']
                    if pandas.notna(refResultValue):
                        refResultValue = str(refResultValue).strip()
                    else:
                        isPass = 0
                        break
                    if refResultValue != "Missing report" and refResultValue != "False report" and refResultValue != "Unmatch" and refResultValue != "pass":
                        isPass = isPass
                        forCAResult.append(refResultValue)
                        continue
                    elif refResultValue == "Missing report" or refResultValue == "False report" or refResultValue == "Unmatch" or refResultValue == "pass":
                        refDiffIdValue = refData.at[refMatchLinesIndex,'diff_basis']
                        if pandas.notna(refDiffIdValue):
                            # refDiffIdValue = str(';'.join(str(refDiffIdValue).strip().split()))
                            isPass = isPass
                            forCAResult.extend(refDiffIdValue.split(";"))
                        else:
                            refDiffIdValue = refData.at[refMatchLinesIndex,'running_flag']
                            if pandas.notna(refDiffIdValue):
                                # refDiffIdValue = str(';'.join(str(refDiffIdValue).strip().split()))
                                isPass = isPass
                                forCAResult.extend(refDiffIdValue.split(";"))
                            else:
                                isPass = 0
                                break
                if isPass == 0:
                    sgData.loc[index, 'Result'] = ""
                    continue
                else:
                    sgData.loc[index, 'from'] = fromTag
                    sgData.loc[index, 'Result'] = str(";".join(sorted(set(sorted(forCAResult)))))

                if addColumn:
                    sgData.loc[index, addColumnName] = repr(refData.at[refMatchLinesIndexList[0],addColumnName])

    if csvType == 0:
        sgData.to_excel(sgFile,index=False,encoding='utf-8')
    elif csvType == 1:
        sgData.to_csv(sgFile,index=False,encoding='utf-8')

    sg_end_time = time.time()
    print("SG反标运行时间为：{:.2f}秒".format(sg_end_time - sg_start_time))

writeLog.close()
end_time = time.time()
print("程序运行时间为：{:.2f}秒".format(end_time - start_time))
