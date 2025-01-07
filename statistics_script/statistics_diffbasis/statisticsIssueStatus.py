#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import openpyxl
import time
import os
import re
import pandas
import getopt
import csv
import codecs
from tqdm import tqdm

start_time = time.time()

def printUsage():
    print("usage: %s <-e|--excel <excel file> | -c|--csv <csv file>> -r|--ref <ref issue status file> -p|--pattern <statistics pattern>" % (sys.argv[0]))
    print('''
    -e|--excel  :   specify the excel file
    -c|--csv    :   specify the csv file
    -r|--ref    :   specify the issue status file
    -p|--pattern    : specify the statistics pattern
    -h          :   show help manual
    ''')
    sys.exit(-1)

excelFile = ""
csvFile = ""
refFile = ''
pattern = ""

try:
    opts,args =  getopt.getopt(sys.argv[1:],"hr:e:c:p:",["ref=","excel=","csv=","pattern="])
except getopt.GetoptError:
    printUsage()

for opt,arg in opts:
    if opt == '-h':
        printUsage()
    elif opt in ("-r","--ref"):
        refFile = arg
    elif opt in ("-e","--excel"):
        excelFile = arg
    elif opt in ("-c", "--csv"):
        csvFile = arg
    elif opt in ("-p", "--pattern"):
        pattern = arg

if not bool(refFile):
    print("Error: Invalid input")
    printUsage

if bool(excelFile) and bool(csvFile):
    print ("Error: only need input one file")
    printUsage

if not bool(excelFile) and not bool(csvFile):
    print("Error: Invalid input")
    printUsage
    
if bool(excelFile):
    if os.path.exists(excelFile):
        excelFileName = os.path.basename(excelFile)
        resultFileName = "statistics_" + os.path.splitext(excelFileName)[0] + ".txt"
        inData = pandas.read_excel(excelFile,sheet_name=0)
elif bool(csvFile):
    if os.path.exists(csvFile):
        csvFileName = os.path.basename(csvFile)
        resultFileName = "statistics_" + os.path.splitext(excelFileName)[0] + ".txt"
        if os.path.splitext(csvFileName)[1] == ".csv":
            f = open(csvFile,'rb')
            content = f.read()
            source_encoding='utf-8'
            try:
                content.decode('utf-8').encode('utf-8')
                source_encoding = 'utf-8'
            except:
                try:
                    content.decode('gbk').encode('utf-8')
                    source_encoding = 'gbk'
                except:
                    try:
                        content.decode('gb2312').encode('utf-8')
                        source_encoding = 'gb2312'
                    except:
                        try:
                            content.decode('gb18030').encode('utf-8')
                            source_encoding = 'gb18030'
                        except:
                            try:
                                content.decode('big5').encode('utf-8')
                                source_encoding = 'big5'
                            except:
                                content.decode('cp936').encode('utf-8')
                                source_encoding = 'cp936'
            block_size = 4096
            with codecs.open(csvFile,'r',source_encoding) as f:
                with codecs.open("tmp.csv",'w','utf-8') as f2:
                    while True:
                        content = f.read(block_size)
                        if not content:
                            break
                        f2.write(content)
            os.remove(csvFile)
            os.rename('tmp.csv',csvFile)
            inData = pandas.read_csv(csvFile,encoding='utf-8',encoding_errors='ignore')

issueMessageData = inData[inData['diff_basis'].str.contains(pattern,na=False)]

print (issueMessageData[['result','diff_basis','running_flag']])
issueList = issueMessageData['diff_basis'].dropna().unique()

refData = pandas.read_excel(refFile)
print (refData)

issueStatusDict = {}
for issueItem in issueList:
    issueStatusData = refData[refData['主题'].str.contains(issueItem,na=False)]
    if issueStatusData.empty:
        # issueStatusDict[issueItem] = ""
        print (f'{issueItem}    :   "Not found"')
    else:
        # print (issueStatusData['状态'].values)
        issueStatus = issueStatusData['状态'].values
        # issueStatusDict[issueItem] = str(issueStatus)
        print (f'{issueItem}    :   {str(issueStatus)}')

# print (issueStatusDict)
# sys.exit(0)
# count = issueMessageData['diff_basis'].str.lower().value_counts()
# pandas.set_option('display.max_rows',None)
# print(count)
# file = open(resultFileName,'w')
# file.write(str(count))
# file.close()
