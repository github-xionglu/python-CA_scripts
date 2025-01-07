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

def printUsage(lineno):
    print("usage: %s -r|--ref_file <reference file> -n|--new_file <target file> -m|--mode <enno|sg> (%s:%d)" % (sys.argv[0], os.path.abspath(__file__), lineno))
    print('''   
    -r|--ref_file   :   specify the history mark csv file
    -n|--new_file   :   specify the target mark csv file
    -m|--mode       :   specify the csv file type, enno or sg
    -h|--help       :   show help manual
    ''')
    sys.exit(-1)

def convert_to_int(variable):
    try:
        return int(variable)
    except ValueError:
        return variable

def compare_history_mark(newData, refData, colNamestoSearch):
    if "new_diff_mark" in newData.columns:
        pass
    else:
        newData["new_diff_mark"] = None

    if "reduced_diff_mark" in newData.columns:
        pass
    else:
        newData["reduced_diff_mark"] = None

    for index in tqdm(newData.index):
        isSame = 1
        messageLine = newData.iloc[index]
        newResultValue = messageLine['Result']
        newResultValueList = newResultValue.split(';')

        refMatchData = refData.loc[
            refData[colNamestoSearch].eq(messageLine[colNamestoSearch]).all(axis=1)
        ]

        refMatchLinesIndexList = refMatchData.index
        if len(refMatchLinesIndexList) == 0:
            newData.loc[index, "new_diff_mark"] = newResultValue
            newData.loc[index, "reduced_diff_mark"] = ""
        elif len(refMatchLinesIndexList) > 2:
            # print(f'Warn: The messages "{messageLine[colNamestoSearch]}" is matched with multi message, please check')
            # refResultValue = refMatchData.iloc[0]['Result']
            # refResultValueList = refResultValue.split(";")
            refResultValueList = []
            for i in range(len(refMatchLinesIndexList)):
                refResultValue = refMatchData.iloc[i]['Result']
                refResultValueList.extend(refResultValue.split(";"))
            refResultValueList = sorted(set(refResultValueList))

            newDiffMark = set(newResultValueList) - set(refResultValueList)
            newData.loc[index, "new_diff_mark"] = str(";".join(sorted(set(newDiffMark))))

            reducedDiffMark = set(refResultValueList) - set(newResultValueList)
            newData.loc[index, "reduced_diff_mark"] = str(";".join(sorted(set(reducedDiffMark))))
        elif len(refMatchLinesIndexList) == 1:
            refResultValue = refMatchData.iloc[0]['Result']
            refResultValueList = refResultValue.split(";")

            newDiffMark = set(newResultValueList) - set(refResultValueList)
            newData.loc[index, "new_diff_mark"] = str(";".join(sorted(set(newDiffMark))))
            
            reducedDiffMark = set(refResultValueList) - set(newResultValueList)
            newData.loc[index, "reduced_diff_mark"] = str(";".join(sorted(set(reducedDiffMark))))

    return newData

def main():
    refFile = ""
    newFile = ""
    mode = ""

    try:
        opts,args =  getopt.getopt(sys.argv[1:],"hr:n:m:",["help","ref_file=","new_file=","mode="])
    except getopt.GetoptError:
        printUsage(sys._getframe().f_lineno)

    for opt,arg in opts:
        if opt in ('-h',"--help"):
            printUsage(sys._getframe().f_lineno)
        elif opt in ("-r","--ref_file"):
            refFile = arg
        elif opt in ("-n", "--new_file"):
            newFile = arg
        elif opt in ("-m","--mode"):
            mode = arg
        
    if refFile == "" or newFile == "":
        printUsage(sys._getframe().f_lineno)

    refData = pandas.read_csv(refFile,encoding='utf-8')
    newData = pandas.read_csv(newFile,encoding='utf-8')

    if 'Result' not in newData.columns:
        print(f'Error: The new file "{newFile}" is not a standard file, please check it')

    if 'Result' not in refData.columns:
        print(f'Error: The new file "{refFile}" is not a standard file, please check it')

    refData['Line'] = [convert_to_int(var) for var in refData['Line']]
    newData['Line'] = [convert_to_int(var) for var in newData['Line']]

    if mode == "enno":
        colNamestoSearch = ['ERule', 'Enno_id', 'File', 'Severity', 'Line', 'Message']
    elif mode == "sg":
        colNamestoSearch = ['ARule', 'File', 'Severity', 'Line', 'Message']
    else:
        print(f'Error: Invalid argument of the mode, please check.')
        printUsage(sys._getframe().f_lineno)

    resultData = compare_history_mark(newData, refData, colNamestoSearch)
    pandas.DataFrame(resultData).to_csv(newFile, index=False)

if __name__ == "__main__":
    main()
