import sys
import os
import re
import getopt
import time
import pandas
import csv
import codecs
from tqdm import tqdm
import numpy as np
import inspect

def printUsage(lineno):
    print("usage: %s <-e|--excel <excel file> | -c|--csv <csv file>> | -m|--mode <statistics mode> [-n|--nozero] [--split] (%s:%d)" % (sys.argv[0], os.path.abspath(__file__), lineno))
    print('''   
    -e|--excel  :   specify the excel file
    -c|--csv    :   specify the csv file
    -m|--mode   :   specify the statistics file mode: Ac, Ar, Setup or Syntax, default: Ac
    -n|--nozero :   Specify whether to filter out unreported rule data
    --split     :   "One-to-many" split into "multi-line"
    -h          :   show help manual
    ''')
    sys.exit(-1)

def statistics_Diff_Issue(inData, fileName, passDiffList, cdcDiffList):
    # 输入：单项-总数据
    # 输出：单项-差异数据统计 diffItemStr，issue数据统计 issueItemStr
    notMatchData = inData[inData['result'] != "match"]

    diffData = notMatchData[
        (notMatchData['result'].str.contains('|'.join(passDiffList),na=False))
        |
        ((notMatchData['diff_basis'].str.contains('|'.join(passDiffList),na=False)) & (~notMatchData['diff_basis'].str.contains('|'.join(cdcDiffList),na=True)))
        |
        (notMatchData['running_flag'].str.contains('|'.join(passDiffList),na=False))
    ]
    diffList = np.concatenate((diffData['result'].dropna().unique(),diffData['diff_basis'].dropna().unique(),diffData['running_flag'].dropna().unique()),axis=None)
    diffItemList = []
    diffItemStrList = []
    for diffItem in diffList:
        if not str(diffItem).startswith('Diff') and not str(diffItem).startswith('diff') and not str(diffItem).startswith('pass-'):
            continue
        diffItem = str(diffItem).split(';')
        for diffItem1 in diffItem:
            if str(diffItem1) in diffItemList:
                continue
            else:
                diffItemList.append(diffItem1)
                diffItem1_escape = re.escape(diffItem1)
                # diffItem1Data = diffData[
                #     diffData['result'].str.contains(diffItem1_escape,na=False)
                #     |
                #     diffData['diff_basis'].str.contains(diffItem1_escape,na=False)
                #     |
                #     diffData['running_flag'].str.contains(diffItem1_escape,na=False)
                # ]
                diffItem1Data = diffData[
                    diffData['result'].str.split(';').apply(lambda x: diffItem1 in x)
                    |
                    diffData['diff_basis'].str.split(';').apply(lambda x: diffItem1 in x)
                    |
                    diffData['running_flag'].str.split(';').apply(lambda x: diffItem1 in x)
                ]
                diffItem1MsgNum = len(diffItem1Data.index)
                diffItem1CaseList = diffItem1Data[fileName].dropna().unique()
                diffItem1CaseNum = len(diffItem1CaseList)
                diffItemStrList.append(f'{str(diffItem1)}: msg: {str(diffItem1MsgNum)}, case: {str(diffItem1CaseNum)}')
    diffStr = '\n'.join(tuple(diffItemStrList))
        
    issueData = notMatchData[notMatchData['diff_basis'].str.contains('|'.join(cdcDiffList),na=False)]
    issueList = issueData['diff_basis'].dropna().unique()
    issueItemList = []
    issueItemStrList = []
    for issueItem in issueList:
        if not str(issueItem).startswith('CDC') and not str(issueItem).startswith('cdc'):
            continue
        issueItem = str(issueItem).split(';')
        for issueItem1 in issueItem:
            if str(issueItem1) in issueItemList:
                continue
            else:
                issueItemList.append(issueItem1)
                issueItem1_escape = re.escape(issueItem1)
                # issueItem1Data = issueData[
                #     issueData['diff_basis'].str.contains(issueItem1_escape,na=False)
                # ]
                issueItem1Data = issueData[
                    issueData['diff_basis'].str.split(';').apply(lambda x: issueItem1 in x)
                ]
                issueItem1MsgNum = len(issueItem1Data.index)
                issueItem1CaseList = issueItem1Data[fileName].dropna().unique()
                issueItem1CaseNum = len(issueItem1CaseList)
                issueItemStrList.append(f'{str(issueItem1)}: msg: {str(issueItem1MsgNum)}, case: {str(issueItem1CaseNum)}')
    issueStr = '\n'.join(tuple(issueItemStrList))

    return diffStr, issueStr

def statistics_Num_case_unmatch_ratio(inData, fileName, passDiffList, cdcDiffList):
    # 输入：单项-总数据
    # 输出：单项-总msg数 msgNum，总case数 caseNum，总误报/漏报数 unmatchMsgNum，-总误报/漏报case数-，真实误报/漏报数 realUnmatchMsgNum，真实误报/漏报case数 realUnmatchCaseNum，误报率/漏报率 ratioNum
    msgNum = len(inData.index)
    
    caseList = inData[fileName].dropna().unique()
    caseNum = len(caseList)

    unmatchData = inData[inData['result'].isin(['False report', 'Missing report', 'Unmatch'])]
    unmatchMsgNum = len(unmatchData)

    realUnmatchData = unmatchData[
        ~((unmatchData['diff_basis'].str.contains('|'.join(passDiffList),na=False)) & (~unmatchData['diff_basis'].str.contains('|'.join(cdcDiffList),na=True)))
        &
        ~unmatchData['running_flag'].str.contains('|'.join(passDiffList),na=False)
    ]
    realUnmatchMsgNum = len(realUnmatchData.index)

    realUnmatchCaseList = realUnmatchData[fileName].dropna().unique()
    realUnmatchCaseNum = len(realUnmatchCaseList)

    if msgNum == 0:
        ratioNum = 0
    elif msgNum != 0:
        ratioNum = '{:.2%}'.format(realUnmatchMsgNum / msgNum)
    
    return msgNum, caseNum, unmatchMsgNum, realUnmatchMsgNum, realUnmatchCaseNum, ratioNum

start_time = time.time()

excelFile = ""
csvFile = ""
mode = "Ac"
nozero = 0
splitType = False

try:
    opts,args =  getopt.getopt(sys.argv[1:],"he:c:m:n",["excel=","csv=","mode=","nozero","split"])
except getopt.GetoptError:
    printUsage(inspect.currentframe().f_lineno)

for opt,arg in opts:
    if opt == '-h':
        printUsage(inspect.currentframe().f_lineno)
    elif opt in ("-e","--excel"):
        excelFile = arg
    elif opt in ("-c", "--csv"):
        csvFile = arg
    elif opt in ("-m", "--mode"):
        mode = arg
    elif opt in ("-n", "--nozero"):
        nozero = 1
    elif opt in ("--split"):
        splitType = True
    
if bool(excelFile) and bool(csvFile):
    print ("Error: only need input one file")
    printUsage(inspect.currentframe().f_lineno)

if not bool(excelFile) and not bool(csvFile):
    print("Error: Invalid input")
    printUsage(inspect.currentframe().f_lineno)
    
if bool(excelFile):
    if os.path.exists(excelFile):
        excelFileName = os.path.basename(excelFile)
        resultExcelName = "statistics_" + os.path.splitext(excelFileName)[0] + ".xlsx"
        resultCsvName = "statistics_" + os.path.splitext(excelFileName)[0] + ".csv"
        inData = pandas.read_excel(excelFile,sheet_name=0,dtype={'diff_basis':str})
elif bool(csvFile):
    if os.path.exists(csvFile):
        csvFileName = os.path.basename(csvFile)
        resultExcelName = "statistics_" + os.path.splitext(csvFileName)[0] + ".xlsx"
        resultCsvName = "statistics_" + os.path.splitext(csvFileName)[0] + ".csv"
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
            inData = pandas.read_csv(csvFile,encoding='utf-8',encoding_errors='ignore',dtype={'diff_basis':str})

if mode == "Ac" or mode == "Ar":
    # 目前Ac部分3方未加rule名。Ar部分增加rule名，统计部分只有Ac，Ar部分需要增加一层dict判断
    mapDict = {
        'AcNoSyncScheme':{
            'MissingSynchronizer':["^Qualifier not found"],
            'SrcConverge':["^Sources from different domains converge before being synchronized"]
        },
        'AcSyncCtrlPath':{
            'LongDelaySignal':["^does not require synchronization \(long-delay/quasi-static\)"],
            'MultiFlop':["^Conventional multi-flop"],
            'UserDefinedCell':["^synchronizing cell\(cell name : .*\)"],
            'UserDefinedQual':["^qualifier .* defined on destination"]
        },
        'AcSyncDataPath':{
            'CGICAutoInferred':["^Clock Gate Synchronization \(auto-detected clock gating\)"],
            'CGICLibraryCell':["^Clock Gate Synchronization \(library clock gating cell\)"],
            'CGICUserDefinedCell':["^Clock Gate Synchronization \(user-defined clock gating cell\)"],
            'CGICUserDefinedQual':["^Clock Based User-Defined Qualifier"],
            'MuxSelect':["^Mux-select sync"],
            'RecirculationMux':[
                "^Recirculation flop.*",
                "^Enable Based Synchronizer",
                "^Enable Based User-Defined Qualifier"
            ],
            'ValidGate':[
                "^Synchronization at And gate.*",
                "^Merges with valid .* qualifier"
            ]
        },
        'AcUnsyncCtrlPath':{
            'CtrlClkDomainMismatch':["^Clock domains of destination instance and synchronizer flop do not match"],
            'CtrlPotentialSynRstUndefined':["^Sync reset used in multi-flop synchronizer"],
            'InvalidSyncCell':["^Invalid synchronizer .*"],
            'MultiFanout':["^Destination instance is driving multiple paths"],
            'NonstaticComboInCrossing':["^Combinational logic used between crossing"],
            'UnsyncSyncRst':["^Unsynchronized synchronous reset"]
        },
        'AcUnsyncDataPath':{
            'InvalidGate':["^Gating logic not accepted: gate-type invalid"],
            'NoDestMuxDataPin':["^Gating logic not accepted: only sources drive MUX data inputs; atleast one destination domain signal should drive a MUX data input"],
            'QualMergesOtherSrc':[
                "^User-defined qualifier merges with another source with non-deterministic enable condition before gating logic",
                "^Qualifier merges with another source with non-deterministic enable condition before gating logic"
            ],
            'QualMergesSameSrc':[
                "^Qualifier merges with the same source before gating logic",
                "^User-defined qualifier merges with the same source before gating logic"
            ],
            'QualMuxDataPin':[
                "^Gating logic not accepted: source and qualifier drive MUX data inputs",
                "^Gating logic not accepted: source and user-defined qualifier drive MUX data inputs"
            ],
            'SrcMuxSelPin':["^Gating logic not accepted: source drives MUX select input"],
            'SrcSameAsQualSrc':["^Qualifier not accepted: crossing source is the same as source of qualifier"]
        },
        'ArSyncCtrlPath':{
            'MultiFlop':{
                'Ar_sync01':[
                    "^Multi-flop reset synchronizer"
                ]
            },
            'UDS':{
                'Ar_sync01':[
                    "^User-Defined reset Synchronizer"
                ]
            },
            'GeneratedReset':{
                'Ar_sync01':[
                    "^Generated reset"
                ]
            }
        },
        'ArUnsyncCtrlPath':{
            'MissingSynchronizer':{
                "Reset_sync02":[
                    "^Reset_sync02"
                ],
                "Ar_unsync01":[
                    "^Missing synchronizer",
                    "^Invalid reset synchronizer"
                ]
            }
        },
        'ChyArSyncMultiTimes':{
            'ChyArSyncMultiTimes':{
                "Reset_sync04":[
                    "^Reset_sync04"
                ]
            }
        }
    }
elif mode == "Setup":
    # Setup只有rule和msgId对应：
    mapDict = {
        "ChyAcSyncMultiTimes" : ["Ac_coherency06"],
        "SetupClockGlitch" : ["Clock_glitch05"], 
        "IntegrityClockConverge" : ["Clock_converge01"],
        "ChySameSrcConvIncSeq" : ["Ac_conv01"],
        "ChySameSrcConvExcSeq" : ["Ac_conv02"],
        "ChyDiffSrcConv" : ["Ac_conv03"],
        "ChyCtrlBusNoConv" : ["Ac_conv04"],
        "ChyDataBusDiffSyncScheme" : ["Ac_conv04"],
        "ChyDataBusDiffEnable" : ["Ac_conv04"],
        "IntegrityRstConvOnComb" : ["Ar_converge01"],
        "SetupClkUndefined" : ["Setup_clockreset01"],
        "SetupRstNotDefined" : ["Setup_clockreset01"],
        "SetupClkInferred" : ["Clock_info01"],
        "SetupClkNetUndefined" : ["Clock_info03a"],
        "SetupClkTiedToConst" : ["Clock_info03c"],
        "SetupAsyncClkConvOnMux" : ["Clock_info05"],
        "SetupSyncClkConvOnMux" : ["Clock_info05"],
        "SetupAsyncClkConvOnComb" : ["Clock_info05b"],
        "SetupSyncClkConvOnComb" : ["Clock_info05b"],
        "SetupClkMuxNotRcvClocks" : ["Clock_info05c"],
        "SetupPortFullyConstrained" : ["Setup_port01"],
        "SetupPortIgnoredSeqClkUnconstrained" : ["Setup_port01"],
        "SetupPortIgnoredUnconnected" : ["Setup_port01"],
        "SetupPortIgnoredNotToSeq" : ["Setup_port01"],
        "SetupPortPartiallyConstrained" : ["Setup_port01"],
        "SetupPortNoConstraint" : ["Setup_port01"],
        "SetupConstraintConflict" : ["Setup_check01"],
        "SetupBBoxPinNoConstraint" : ["Setup_blackbox01"],
        "SetupBBoxPinFullyConstrained" : ["Setup_blackbox01"],
        "SetupBBoxPinPartiallyConstrained" : ["Setup_blackbox01"],
        "SetupBBoxPinIgnored" : ["Setup_blackbox01"],
        "SetupDataTiedToConst" : ["Clock_info03b"],
        "SetupInputMultiClkSampled" : ["Clock_sync05","Clock_sync05a"],
        "SetupOutputMultiClkDriven" : ["Clock_sync06","Clock_sync06a"],
        "SetupRstSenseMissing" : ["Ac_resetvalue01"],
        "SetupResetInferred" : ["Reset_info01"],
        "SetupRstNetNotDefined" : ["Reset_info09a"]
    }
    outputMsgOrder = ['ChyAcSyncMultiTimes','SetupClockGlitch','IntegrityClockConverge','ChySameSrcConvIncSeq','ChySameSrcConvExcSeq','ChyDiffSrcConv','ChyCtrlBusNoConv','ChyDataBusDiffSyncScheme','ChyDataBusDiffEnable','IntegrityRstConvOnComb','SetupClkUndefined','SetupRstNotDefined','SetupClkInferred','SetupClkNetUndefined','SetupClkTiedToConst','SetupAsyncClkConvOnMux','SetupSyncClkConvOnMux','SetupAsyncClkConvOnComb','SetupSyncClkConvOnComb','SetupClkMuxNotRcvClocks','SetupPortFullyConstrained','SetupPortIgnoredSeqClkUnconstrained','SetupPortIgnoredUnconnected','SetupPortIgnoredNotToSeq','SetupPortPartiallyConstrained','SetupPortNoConstraint','SetupConstraintConflict','SetupBBoxPinNoConstraint','SetupBBoxPinFullyConstrained','SetupBBoxPinPartiallyConstrained','SetupBBoxPinIgnored','SetupDataTiedToConst','SetupInputMultiClkSampled','SetupOutputMultiClkDriven','SetupRstSenseMissing','SetupResetInferred','SetupRstNetNotDefined']
elif mode == 'Syntax':
    mapDict = {
        "CmdInvalid" : ['SGDCSTX_002'],
        "CmdOptionValueInvalid" : ['SGDCSTX_008','SGDC_reset_synchronizer04','SGDC_reset_synchronizer06','SGDC_reset_synchronizer07','FalsePathSetup','SGDC_cdc_false_path06','SGDC_cdc_false_path07','SGDC_qualifier02a','SGDC_qualifier02c','SGDC_qualifier03a','SGDC_qualifier03c'],
        "CmdNoOptionInput" : ['SGDC_cdc_false_path05'],
        "CmdArgValueInvalid" : ['SGDCSTX_008'],
        "CmdArgValueNotSingle" : ['SGDCSTX_007'],
        "CmdEndingDoubleQuoteMissing" : ['SGDCSTX_009'],
        "CmdFailedInvalidObjArg" : ['SGDCSTX-004','SGDC_quasi_static01'],
        "CmdOverride" : ['SGDCWRN_123','SGDC_reset_synchronizer10'],
        "CMD-1000" : ['SGDCSTX-003','SGDCSTX-004','SGDCSTX_011','SGDCSTX_012'],
        "CMD-1001" : ['SGDCSTX-003'],
        "CMD-1002" : ['SGDCSTX-003'],
        "CMD-1005" : ['SGDCSTX-004','SGDCSTX_011','SGDC_qualifier09','SGDC_qualifier15'],
        "CMD-1006" : ['SGDCSTX-004','SGDCSTX_008','SGDCSTX_019','SGDC_qualifier15'],
        "CMD-1007" : ['SGDCSTX_008','checkSGDC_nottogether01'],
        "CMD-1016" : ['SGDCSTX_008','SGDCSTX_011'],
        "CMD_2084" : ['SGDCSTX_019'],
        "CMD-2085" : ['SGDCSTX_007'],
        "CdcFalsePathNoCrossing" : ['FalsePathSetup'],
        "CdcFalsePathUnmatched" : ['SGDC_cdc_false_path06'],
        "CdcFalsePathOptionMissing" : ['SGDC_cdc_false_path07'],
        "RstSenseInvalid" : ['SGDCSTX_008','SGDC_reset04'],
        "RstSrcObjIllegal" : ['SGDC_reset01'],
        "RstNameExisted" : ['SGDC_reset02','SGDC_reset03'],
        "RstSynchronizerNotInFanoutPath" : ['SGDC_reset_synchronizer02'],
        "RstSynchronizerUnused" : ['SGDC_reset_synchronizer08'],
        "ReadFailed" : ['SGDCSTX_019','SGDCSTX_020'],
        "ClockNameExisted" : ['SGDCWRN_121','SGDCWRN_123'],
        "ClkSrcObjIllegal" : ['SGDC_clock01','SGDCSTX_008'],
        "ClockNameOrSourceMustSpecified" : ['SGDCSTX-004'],
        "ConstraintValueFailed" : ['SGDCSTX_008'],
        "MultiArgsInvalid" : ['SGDCSTX_012'],
        "OptionDependencyError" : ['checkSGDC_together02','SGDCSTX_008'],
        "ObjectlsNotFound" : ['SGDCSTX-003','SGDCSTX_008','SGDCSTX_011','SGDCSTX_013','SGDC_reset_synchronizer01','SGDC_reset_synchronizer03','SGDC_reset_synchronizer05','SGDC_cdc_false_path01','SGDC_cdc_false_path02','SGDC_qualifier01','SGDC_qualifier02a','SGDC_qualifier02b','SGDC_qualifier03a','SGDC_qualifier03b','SGDC_quasi_static01','SGDC_IP_block01'],
        "ObjectUnusedInDesign" : ['SGDC_clock01','SGDC_reset01','SGDC_reset_synchronizer01','SGDC_reset_synchronizer03','SGDC_reset_synchronizer05','SGDC_qualifier01','SGDC_quasi_static01'],
        "QualNameInvalid" : ['SGDC_qualifier01'],
        "QualFromToDomainSame" : ['SGDC_qualifier10'],
        "QualifierFailed" : ['QualifierSetup'],
        "SetupClkNotPropagated" : ['Propagate_Clocks'],
        "SetupClkPropagated" : ['Propagate_Clocks'],
        "SetupRstNotPropagated" : ['Propagate_Resets'],
        "SetupRstPropagated" : ['Propagate_Resets'],
        "SyncCellFromToDomainSame" : ['SGDC_sync_cell04'],
        "SyncCellFailed" : ['SyncCellSetup'],
        "AbstractPortModuleUninstantiated" : ['SGDC_abstract_port01'],
        "IpBlockModuleUninstantiated" : ['SGDC_IP_block01'],
    }
    outputMsgOrder = ["CMD-1002","CMD-1005","CMD-1006","CMD-1007","CMD-1016","CMD-2085",
    "ReadFailed","CmdInvalid","CmdNoOptionInput","CmdOptionValueInvalid","CmdEndingDoubleQuoteMissing","CmdOverride","OptionDependencyError","MultiArgsInvalid",
    "SetupClkPropagated","SetupClkNotPropagated","SetupRstPropagated","SetupRstNotPropagated",
    "ClkSrcObjIllegal","ClockNameExisted","RstSrcObjIllegal","RstNameExisted","CdcFalsePathUnmatched","CdcFalsePathNoCrossing","CdcFalsePathOptionMissing","RstSynchronizerUnused","RstSynchronizerNotInFanoutPath","RstSenseInvalid","AbstractPortModuleUninstantiated","IpBlockModuleUninstantiated","SyncCellFromToDomainSame","QualFromToDomainSame"]

eMsgId='enno_msgid'
sRule='sg_rule'
if mode == "Ac" or mode == "Setup" or mode == "Syntax":
    eReason='enno_reason'
    sReason='sg_reason'
elif mode == "Ar":
    eMsgId='enno_id'
    eReason = 'Reason'
    sReason = 'Reason'
# fileName='file_name'
eFileName='enno_file_name'
sFileName='sg_file_name'
result='result'
matchReport='match'
falseReport='False report'
missingReport='Missing report'
unmatchReport='Unmatch'
mark_diff='diff_basis'
mark_running='running_flag'
passDiffList=['Diff','diff','pass-']
cdcDiffList=['CDC','cdc']

eMsgIdList = []
if mark_diff in inData.columns:
    inData[mark_diff] = inData[mark_diff].astype(str)
if mark_running in inData.columns:
    inData[mark_running] = inData[mark_running].astype(str)
eMsgIdDataList = inData[eMsgId].dropna().unique()
for eMsgIdDataItem in eMsgIdDataList:
    eMsgIdList += eMsgIdDataItem.split()
eMsgIdList = tuple(sorted(set(eMsgIdList)))

eReasonMsgIdTotal = []
eReasonReasonTotal = []
eReasonMsgTotal = []
eReasonCaseTotal = []
eReasonFalseReportTotal = []
# eReasonFalseReportTotalLoc = []
eReasonRealFalseReportTotal = []
eReasonRealFalseCasesTotal = []
eReasonFalseRatio = []
eReasonDiffStatistics=[]

sReasonRuleTotal = []
sReasonReasonTotal = []
sReasonMsgTotal = []
sReasonCaseTotal = []
sReasonFalseReportTotal = []
sReasonRealFalseReportTotal = []
sReasonRealFalseCasesTotal = []
sReasonFalseRatio = []
sReasonDiffStatistics = []

reasonDiffStatistics = []

eReasonIssueStatistics = []
sReasonIssueStatistics = []
reasonIssueStatistics = []

if mode == "Ac" or mode == "Ar":
    for msgId in eMsgIdList:
        eMsgIdData = inData[inData[eMsgId] == msgId]
        # eReasonList = set(eMsgIdData[eReason].values)
        eReasonList = []
        eReasonDataList = eMsgIdData[eReason].dropna().unique()
        for eReasonDataItem in eReasonDataList:
            eReasonList += eReasonDataItem.split()
        eReasonList = tuple(sorted(set(eReasonList)))
        
        for eReasonItem in eReasonList:
            # 获取enno数据
            # 已有enno msgId：msgId，enno reason: eReasonItem
            eReasonMsgTotalData = eMsgIdData[eMsgIdData[eReason].str.contains(eReasonItem,na=False)]
            
            eReasonMsgNum, eReasonCaseNum, eReasonFalseReportNum, eReasonRealFalseReportNum, eReasonRealFalseCaseNum, eReasonFalseRatioNum = statistics_Num_case_unmatch_ratio(eReasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)
            eReasonDiffStr, eReasonIssueStr = statistics_Diff_Issue(eReasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)

            if not splitType:
                eReasonMsgIdTotal.append(msgId)
                eReasonReasonTotal.append(eReasonItem)
                eReasonMsgTotal.append(eReasonMsgNum)
                eReasonCaseTotal.append(eReasonCaseNum)
                eReasonFalseReportTotal.append(eReasonFalseReportNum)
                eReasonRealFalseReportTotal.append(eReasonRealFalseReportNum)
                eReasonRealFalseCasesTotal.append(eReasonRealFalseCaseNum)
                eReasonFalseRatio.append(eReasonFalseRatioNum)
                eReasonDiffStatistics.append(eReasonDiffStr)
                eReasonIssueStatistics.append(eReasonIssueStr)

                if mode == "Ac":
                    sReasonItems = mapDict[msgId][eReasonItem]
                    sReasonStrList = []
                    for sReasonItem in sReasonItems:
                        sReasonStrList.append(sReasonItem[1:])
                    sReasonRuleTotal.append("")
                    sReasonReasonTotal.append("\n/\n".join(sReasonStrList))
                    sReasonMsgTotalData = inData[inData[sReason].str.contains('|'.join(sReasonItems),na=False,regex=True)]
                elif mode == "Ar":
                    sRuleReasonDict = mapDict[msgId][eReasonItem]
                    sReasonRuleStrList = []
                    sReasonStrList = []
                    for sReasonRuleItem in list(sRuleReasonDict.keys()):
                        sReasonRuleStrList.append(sReasonRuleItem)
                        for sReasonItem in sRuleReasonDict[sReasonRuleItem]:
                            sReasonStrList.append(sReasonItem[1:])
                    sReasonRuleTotal.append("\n/\n".join(list(sReasonRuleStrList)))
                    sReasonReasonTotal.append("\n/\n".join(list(sReasonStrList)))
                    sReasonMsgTotalData = inData[
                        (inData[sRule].str.contains('|'.join(list(sRuleReasonDict.keys())),na=False,regex=True))
                        &
                        (
                            (inData[sReason].str.contains('|'.join(list(sReasonStrList)),na=False,regex=True))
                            |
                            (inData[sReason] == eReasonItem)
                        )
                    ]
                sReasonMsgNum, sReasonCaseNum, sReasonFalseReportNum, sReasonRealFalseReportNum, sReasonRealFalseCaseNum, sReasonFalseRatioNum = statistics_Num_case_unmatch_ratio(sReasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)
                sReasonDiffStr, sReasonIssueStr = statistics_Diff_Issue(sReasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)

                sReasonMsgTotal.append(sReasonMsgNum)
                sReasonCaseTotal.append(sReasonCaseNum)
                sReasonFalseReportTotal.append(sReasonFalseReportNum)
                sReasonRealFalseReportTotal.append(sReasonRealFalseReportNum)
                sReasonRealFalseCasesTotal.append(sReasonRealFalseCaseNum)
                sReasonFalseRatio.append(sReasonFalseRatioNum)
                sReasonDiffStatistics.append(sReasonDiffStr)
                sReasonIssueStatistics.append(sReasonIssueStr)

                if mode == "Ac":
                    reasonMsgTotalData = inData[
                        (
                            (inData[eMsgId] == msgId)
                            &
                            (inData[eReason].str.contains(eReasonItem,na=False))
                        )
                        |
                        (inData[sReason].str.contains('|'.join(sReasonItems),na=False,regex=True))
                    ]
                elif mode == "Ar":
                    reasonMsgTotalData = inData[
                        (
                            (inData[eMsgId] == msgId)
                            &
                            (inData[eReason].str.contains(eReasonItem,na=False))
                        )
                        |
                        (inData[sReason].str.contains('|'.join(list(sReasonStrList)),na=False,regex=True))
                    ]
                diffStr, issueStr = statistics_Diff_Issue(reasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)
                reasonDiffStatistics.append(diffStr)
                reasonIssueStatistics.append(issueStr)
            elif splitType:
                if mode == "Ac":
                    sReasonRuleStrList = ['any']
                elif mode == "Ar":
                    sRuleReasonDict = mapDict[msgId][eReasonItem]
                    sReasonRuleStrList = []
                    for sReasonRuleItem in list(sRuleReasonDict.keys()):
                        sReasonRuleStrList.append(sReasonRuleItem)
                        
                ### 下面待重新处理
                for sReasonRuleItem in sReasonRuleStrList:
                    if mode == "Ac":
                        sReasonItems = mapDict[msgId][eReasonItem]
                        sReasonStrList = []
                        for sReasonItem in sReasonItems:
                            sReasonStrList.append(sReasonItem[1:])
                    elif mode == "Ar":
                        sRuleReasonDict = mapDict[msgId][eReasonItem]
                        sReasonStrList = []
                        for sReasonItem in sRuleReasonDict[sReasonRuleItem]:
                            sReasonStrList.append(sReasonItem[1:])
                    for sReasonItem in sReasonStrList:
                        eReasonMsgIdTotal.append(msgId)
                        eReasonReasonTotal.append(eReasonItem)
                        eReasonMsgTotal.append(eReasonMsgNum)
                        eReasonCaseTotal.append(eReasonCaseNum)
                        eReasonFalseReportTotal.append(eReasonFalseReportNum)
                        eReasonRealFalseReportTotal.append(eReasonRealFalseReportNum)
                        eReasonRealFalseCasesTotal.append(eReasonRealFalseCaseNum)
                        eReasonFalseRatio.append(eReasonFalseRatioNum)
                        eReasonDiffStatistics.append(eReasonDiffStr)
                        eReasonIssueStatistics.append(eReasonIssueStr)

                        if mode == "Ac":
                            sReasonRuleTotal.append("")
                            sReasonReasonTotal.append(sReasonItem)
                            sReasonMsgTotalData = inData[inData[sReason].str.contains(sReasonItem,na=False,regex=True)]
                        elif mode == "Ar":
                            sReasonRuleTotal.append(sReasonRuleItem)
                            sReasonReasonTotal.append(sReasonItem)
                            sReasonMsgTotalData = inData[
                                (inData[sRule].str.contains(sReasonRuleItem,na=False,regex=True))
                                &
                                (
                                    (inData[sReason] == sReasonItem)
                                    |
                                    (inData[sReason] == eReasonItem)
                                )
                            ]
                        sReasonMsgNum, sReasonCaseNum, sReasonFalseReportNum, sReasonRealFalseReportNum, sReasonRealFalseCaseNum, sReasonFalseRatioNum = statistics_Num_case_unmatch_ratio(sReasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)
                        sReasonDiffStr, sReasonIssueStr = statistics_Diff_Issue(sReasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)

                        sReasonMsgTotal.append(sReasonMsgNum)
                        sReasonCaseTotal.append(sReasonCaseNum)
                        sReasonFalseReportTotal.append(sReasonFalseReportNum)
                        sReasonRealFalseReportTotal.append(sReasonRealFalseReportNum)
                        sReasonRealFalseCasesTotal.append(sReasonRealFalseCaseNum)
                        sReasonFalseRatio.append(sReasonFalseRatioNum)
                        sReasonDiffStatistics.append(sReasonDiffStr)
                        sReasonIssueStatistics.append(sReasonIssueStr)

                        if mode == "Ac":
                            reasonMsgTotalData = inData[
                                (
                                    (inData[eMsgId] == msgId)
                                    &
                                    (inData[eReason].str.contains(eReasonItem,na=False))
                                )
                                |
                                (inData[sReason].str.contains(sReasonItem,na=False,regex=True))
                            ]
                        elif mode == "Ar":
                            reasonMsgTotalData = inData[
                                (
                                    (inData[eMsgId] == msgId)
                                    &
                                    (inData[eReason].str.contains(eReasonItem,na=False))
                                )
                                |
                                (
                                    (inData[sRule].str.contains(sReasonRuleItem,na=False,regex=True))
                                    &
                                    (
                                        (inData[sReason].str.contains(sReasonItem,na=False,regex=True))
                                        |
                                        (inData[sReason].str.contains(eReasonItem,na=False,regex=True))
                                    )
                                )
                            ]
                        diffStr, issueStr = statistics_Diff_Issue(reasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)
                        reasonDiffStatistics.append(diffStr)
                        reasonIssueStatistics.append(issueStr)

elif mode == "Setup" or mode == "Syntax":
    for msgId in outputMsgOrder:
        # e msgId list
        # eReasonMsgIdTotal.append(msgId)
        eMsgIdData = inData[inData[eMsgId] == msgId]

        # e reason list
        # eReasonReasonTotal.append("")
        eReasonMsgTotalData = eMsgIdData

        eReasonMsgNum, eReasonCaseNum, eReasonFalseReportNum, eReasonRealFalseReportNum, eReasonRealFalseCaseNum, eReasonFalseRatioNum = statistics_Num_case_unmatch_ratio(eReasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)
        eReasonDiffStr, eReasonIssueStr = statistics_Diff_Issue(eReasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)
        
        # 3方对应的rule
        sRuleItems = mapDict[msgId]
        for sRuleItem in sRuleItems:
            eReasonMsgIdTotal.append(msgId)
            eReasonReasonTotal.append("")
            eReasonMsgTotal.append(eReasonMsgNum)
            eReasonCaseTotal.append(eReasonCaseNum)
            eReasonFalseReportTotal.append(eReasonFalseReportNum)
            eReasonRealFalseReportTotal.append(eReasonRealFalseReportNum)
            eReasonRealFalseCasesTotal.append(eReasonRealFalseCaseNum)
            eReasonFalseRatio.append(eReasonFalseRatioNum)
            eReasonDiffStatistics.append(eReasonDiffStr)
            eReasonIssueStatistics.append(eReasonIssueStr)

            sReasonRuleTotal.append(sRuleItem)
            sReasonReasonTotal.append("")

            # 3方 report 总数
            sRuleData = inData[inData[sRule] == sRuleItem]
            sReasonMsgTotalData = sRuleData

            sReasonMsgNum, sReasonCaseNum, sReasonFalseReportNum, sReasonRealFalseReportNum, sReasonRealFalseCaseNum, sReasonFalseRatioNum = statistics_Num_case_unmatch_ratio(sReasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)
            sReasonDiffStr, sReasonIssueStr = statistics_Diff_Issue(sReasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)

            sReasonMsgTotal.append(sReasonMsgNum)
            sReasonCaseTotal.append(sReasonCaseNum)
            sReasonFalseReportTotal.append(sReasonFalseReportNum)
            sReasonRealFalseReportTotal.append(sReasonRealFalseReportNum)
            sReasonRealFalseCasesTotal.append(sReasonRealFalseCaseNum)
            sReasonFalseRatio.append(sReasonFalseRatioNum)
            sReasonDiffStatistics.append(sReasonDiffStr)
            sReasonIssueStatistics.append(sReasonIssueStr)

            reasonMsgTotalData = inData[
                (inData[eMsgId] == msgId)
                |
                (inData[sRule].str.contains('|'.join(sRuleItems),na=False,regex=True))
            ]
            diffStr, issueStr = statistics_Diff_Issue(reasonMsgTotalData, 'test_name', passDiffList, cdcDiffList)
            reasonDiffStatistics.append(diffStr)
            reasonIssueStatistics.append(issueStr)

outputData = {}
outputData[eMsgId] = eReasonMsgIdTotal
outputData[sRule] = sReasonRuleTotal
# outputData[eReason] = eReasonList
outputData['eReason'] = eReasonReasonTotal
outputData['sReason'] = sReasonReasonTotal

outputData['enno_total_message'] = eReasonMsgTotal
outputData['enno_total_case'] = eReasonCaseTotal
# outputData['total_false_loc'] = eReasonFalseReportTotalLoc
outputData['enno_total_false'] = eReasonFalseReportTotal
outputData['real_false'] = eReasonRealFalseReportTotal
outputData['real_false_case'] = eReasonRealFalseCasesTotal
outputData['false_report_ratio'] = eReasonFalseRatio
# outputData['eReasonDiffStatistics'] = eReasonDiffStatistics

outputData['s_total_message'] = sReasonMsgTotal
outputData['s_total_case'] = sReasonCaseTotal
outputData['s_total_miss'] = sReasonFalseReportTotal
outputData['real_miss'] = sReasonRealFalseReportTotal
outputData['real_miss_case'] = sReasonRealFalseCasesTotal
outputData['miss_report_ratio'] = sReasonFalseRatio

outputData['eReasonDiffStatistics'] = eReasonDiffStatistics
outputData['sReasonDiffStatistics'] = sReasonDiffStatistics

outputData['reasonDiffStatistics'] = reasonDiffStatistics

outputData['eReasonIssueStatistics'] = eReasonIssueStatistics
outputData['sReasonIssueStatistics'] = sReasonIssueStatistics
outputData['reasonIssueStatistics'] = reasonIssueStatistics
if nozero == 1:
    outputData = pandas.DataFrame(outputData)
    outputData = outputData[
        (outputData['enno_total_message'] != 0)
        &
        (outputData['s_total_message'] != 0)
    ]
pandas.DataFrame(outputData).to_csv(resultCsvName,index=False)
print(pandas.DataFrame(outputData))
# pandas.DataFrame(outputData).to_excel(resultExcelName,index=False)
