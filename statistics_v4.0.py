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

start_time = time.time()

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
    elif opt in ("split"):
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
        inData = pandas.read_excel(excelFile,sheet_name=0)
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
            inData = pandas.read_csv(csvFile,encoding='utf-8',encoding_errors='ignore')

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
                "^Recirculation flop",
                "^Enable Based Synchronizer"
            ],
            'ValidGate':[
                "^Synchronization at And gate",
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
                    "^Qualifier not found"
                ],
                "Ar_unsync01":[
                    "^Missing synchronizer"
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
            eReasonMsgIdTotal.append(msgId)
            eReasonReasonTotal.append(eReasonItem)
            # eReasonMsgTotalData: 某一条reason对应的总数据
            eReasonMsgTotalData = eMsgIdData[eMsgIdData[eReason].str.contains(eReasonItem,na=False)]
            eReasonMsgNum = len(eReasonMsgTotalData.index)
            eReasonMsgTotal.append(eReasonMsgNum)

            # eReasonCasesList: 某条reason对应的case的集合
            eReasonCasesList = eReasonMsgTotalData[eFileName].dropna().unique()
            eReasonCasesNum = len(eReasonCasesList)
            eReasonCaseTotal.append(eReasonCasesNum)

            # eReasonFalseReportData：某条reason对应的摸底误报总数
            # eReasonFalseReportDataLoc = eReasonMsgTotalData.loc[eReasonMsgTotalData[result] == falseReport]
            # eReasonFalseReportTotalLoc.append(len(eReasonFalseReportDataLoc.index))
            eReasonFalseReportData = eReasonMsgTotalData[
                (eReasonMsgTotalData[result] == falseReport)
                |
                (eReasonMsgTotalData[result] == unmatchReport)
            ]
            eReasonFalseReportTotal.append(len(eReasonFalseReportData.index))
            # print (eReasonFalseReportData)

            # eReasonRealFalseReportData：某条reason对应的真实误报总数
            eReasonRealFalseReportData = eReasonFalseReportData.loc[
                ~((eReasonFalseReportData[mark_diff].str.contains('|'.join(passDiffList),na=False)) & (~eReasonFalseReportData[mark_diff].str.contains('|'.join(cdcDiffList),na=True)))
                &
                ~eReasonFalseReportData[mark_running].str.contains('|'.join(passDiffList),na=False)
            ]
            eReasonRealFalseReportNum = len(eReasonRealFalseReportData.index)
            eReasonRealFalseReportTotal.append(eReasonRealFalseReportNum)
            # print (eReasonRealFalseReportData)

            # eReasonRealFalseCasesList：某条reason对应真实误报case集合
            eReasonRealFalseCasesList = eReasonRealFalseReportData[eFileName].dropna().unique()
            eReasonRealFalseCasesTotal.append(len(eReasonRealFalseCasesList))

            # eReasonFalseRatio： 某条reason对应的误报率
            if eReasonMsgNum == 0:
                eReasonFalseRatio.append(0)
            elif eReasonMsgNum != 0:
                eReasonFalseRatio.append('{:.2%}'.format(eReasonRealFalseReportNum / eReasonMsgNum))

            # eReasonDiffReportData：某条reason对应的差异种类及对应的误报message条数
            eReasonNotMatchData = eReasonMsgTotalData[eReasonMsgTotalData[result] != matchReport]
            eReasonDiffReportData = eReasonNotMatchData[
                (eReasonNotMatchData[mark_diff].str.contains('|'.join(passDiffList),na=False) & (~eReasonNotMatchData[mark_diff].str.contains('|'.join(cdcDiffList),na=True)))
                |
                eReasonNotMatchData[mark_running].str.contains('|'.join(passDiffList),na=False)
                |
                eReasonNotMatchData[result].str.contains('|'.join(passDiffList),na=False)
            ]
            # eReasonDiffStatistics.append(eReasonDiffReportData[mark_diff].value_counts())
            eReasonDiffList = np.concatenate((eReasonDiffReportData[result].dropna().unique(),eReasonDiffReportData[mark_diff].dropna().unique(),eReasonDiffReportData[mark_running].dropna().unique()),axis=None)
            eReasonDiffItemList = []
            eReasonDiffItemStr = []
            for diffItem in eReasonDiffList:
                if not str(diffItem).startswith('Diff') and not str(diffItem).startswith('diff') and not str(diffItem).startswith('pass-'):
                    continue
                diffItem = str(diffItem).split(';')
                if len(diffItem) == 1:
                    for diffItem1 in diffItem:
                        if str(diffItem) in eReasonDiffItemList:
                            continue
                        else:
                            eReasonDiffItemList.append(diffItem)
                            diffItem1_escape = re.escape(diffItem1)
                            eReasonDiffItem1Data = eReasonDiffReportData[
                                (eReasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False))
                                |
                                (eReasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False))
                                |
                                (eReasonDiffReportData[result].str.contains(diffItem1_escape,na=False))
                            ]
                            eReasonDiffItem1Num = len(eReasonDiffItem1Data.index)
                            eReasonDiffItem1CaseList = eReasonDiffItem1Data[eFileName].dropna().unique()
                            eReasonDiffItem1CaseNum = len(eReasonDiffItem1CaseList)
                            eReasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(eReasonDiffItem1Num) + ", case: " + str(eReasonDiffItem1CaseNum))
                elif len(diffItem) >= 2:
                    for diffItem1 in diffItem:
                        if str(diffItem1) in eReasonDiffItemList:
                            continue
                        else:
                            eReasonDiffItemList.append(diffItem1)
                            diffItem1_escape = re.escape(diffItem1)
                            eReasonDiffItem1Data = eReasonDiffReportData[
                                eReasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False)
                                |
                                eReasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False)
                                |
                                eReasonDiffReportData[result].str.contains(diffItem1_escape,na=False)
                            ]
                            eReasonDiffItem1Num = len(eReasonDiffItem1Data.index)
                            eReasonDiffItem1CaseList = eReasonDiffItem1Data[eFileName].dropna().unique()
                            eReasonDiffItem1CaseNum = len(eReasonDiffItem1CaseList)
                            eReasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(eReasonDiffItem1Num) + ", case: " + str(eReasonDiffItem1CaseNum))
            eReasonDiffStatistics.append('\n'.join(tuple(eReasonDiffItemStr)))

            eReasonIssueReportData = eReasonNotMatchData[eReasonNotMatchData[result].str.contains('|'.join(cdcDiffList),na=False)]
            if eReasonIssueReportData.empty:
                eReasonIssueStatistics.append('')
            else:
                eReasonIssueList = np.concatenate(eReasonIssueReportData[mark_diff].dropna().unique(),axis=None)
                eReasonIssueItemList = []
                eReasonIssueItemStr = []
                for issueItem in eReasonIssueList:
                    if not str(issueItem).startswith('cdc') and not str(issueItem).startswith('CDC'):
                        continue
                    issueItem = str(issueItem).split(';')
                    for issueItem1 in issueItem:
                        if str(issueItem1) in eReasonIssueItemList:
                            continue
                        else:
                            eReasonIssueItemList.append(issueItem1)
                            issueItem1_escape = re.escape(issueItem1)
                            eReasonIssueItem1Data = eReasonIssueReportData[eReasonIssueReportData[mark_diff].str.contains(issueItem1_escape,na=False)]
                            eReasonIssueItem1Num = len(eReasonIssueItem1Data.index)
                            eReasonIssueItem1CaseList = eReasonIssueItem1Data[eFileName].dropna().unique()
                            eReasonIssueItem1CaseNum = len(eReasonIssueItem1CaseList)
                            eReasonIssueItemStr.append(f'{str(issueItem1)}: msg: {str(eReasonIssueItem1Num)}, case: {str(eReasonIssueItem1CaseNum)}')
                eReasonIssueStatistics.append('\n'.join(tuple(eReasonIssueItemStr)))

            # sReasonItem: enno messageId reason对应的3方reason
            if mode == "Ac":
                sReasonItems = mapDict[msgId][eReasonItem]
                sReasonStrList = []
                for sReasonItem in sReasonItems:
                    sReasonStrList.append(sReasonItem[1:])
                sReasonRuleTotal.append("")
                sReasonReasonTotal.append("\n/\n".join(sReasonStrList))

                # 3方 report总数
                # print ("=============\n" + str(sReasonItems) + "\n")
                sReasonMsgTotalData = inData[inData[sReason].str.contains('|'.join(sReasonItems),na=False,regex=True)]
            elif mode == "Ar":
                sRuleReasonDict = mapDict[msgId][eReasonItem]
                sReasonRuleStrList = []
                sReasonStrList = []
                for sReasonRuleItem in list(sRuleReasonDict.keys()):
                    sReasonRuleStrList.append(sReasonRuleItem)
                    for sReasonItem in sRuleReasonDict[sReasonRuleItem]:
                        sReasonStrList.append(sReasonItem[1:])
                # print (f'=========\n{msgId}\n{eReasonItem}\n{sReasonRuleStrList}\n{sReasonStrList}')
                sReasonRuleTotal.append("\n/\n".join(list(sReasonRuleStrList)))
                sReasonReasonTotal.append("\n/\n".join(list(sReasonStrList)))

                # 3方 report总数
                # print ("=============\n" + str(sReasonItems) + "\n")
                sReasonMsgTotalData = inData[
                    (inData[sRule].str.contains('|'.join(list(sRuleReasonDict.keys())),na=False,regex=True))
                    &
                    (
                        (inData[sReason].str.contains('|'.join(list(sReasonStrList)),na=False,regex=True))
                        |
                        (inData[sReason] == eReasonItem)
                    )
                ]

            # print (sReasonMsgTotalData[sReason])
            sReasonMsgNum = len(sReasonMsgTotalData.index)
            sReasonMsgTotal.append(sReasonMsgNum)
            
            # 3方涉及case数
            sReasonCasesList = sReasonMsgTotalData[sFileName].dropna().unique()
            sReasonCaseTotal.append(len(sReasonCasesList))
            
            # 3方摸底漏报数
            sReasonFalseReportData = sReasonMsgTotalData[
                (sReasonMsgTotalData[result] == missingReport)
                |
                (sReasonMsgTotalData[result] == unmatchReport)
            ]
            sReasonFalseReportTotal.append(len(sReasonFalseReportData.index))

            # 3方真实漏报数
            sReasonRealFalseReportData = sReasonFalseReportData[
                ~((sReasonFalseReportData[mark_diff].str.contains('|'.join(passDiffList),na=False)) & (~sReasonFalseReportData[mark_diff].str.contains('|'.join(cdcDiffList),na=True)))
                &
                ~sReasonFalseReportData[mark_running].str.contains('|'.join(passDiffList),na=False)
            ]
            sReasonRealFalseReportNum = len(sReasonRealFalseReportData.index)
            sReasonRealFalseReportTotal.append(sReasonRealFalseReportNum)

            # 3方真实漏报case数
            sReasonRealFalseCasesList = sReasonRealFalseReportData[sFileName].dropna().unique()
            sReasonRealFalseCasesTotal.append(len(sReasonRealFalseCasesList))

            # 3方reason漏报率
            if sReasonMsgNum == 0:
                sReasonFalseRatio.append(0)
            elif sReasonMsgNum != 0:
                sReasonFalseRatio.append('{:.2%}'.format(sReasonRealFalseReportNum / sReasonMsgNum))

            # 3方reason对应的差异种类及对应的误报message条数
            sReasonNotMatchData = sReasonMsgTotalData[sReasonMsgTotalData[result] != matchReport]
            sReasonDiffReportData = sReasonNotMatchData[
                (sReasonNotMatchData[result].str.contains('|'.join(passDiffList),na=False) & (~sReasonNotMatchData[result].str.contains('|'.join(cdcDiffList),na=True)))
                |
                sReasonNotMatchData[mark_diff].str.contains('|'.join(passDiffList),na=False)
                |
                sReasonNotMatchData[mark_running].str.contains('|'.join(passDiffList),na=False)
            ]
            # sReasonDiffStatistics.append(sReasonDiffReportData[mark_diff].value_counts())
            sReasonDiffList = np.concatenate((sReasonDiffReportData[result].dropna().unique(),sReasonDiffReportData[mark_diff].dropna().unique(),sReasonDiffReportData[mark_running].dropna().unique()),axis=None)
            sReasonDiffItemList = []
            sReasonDiffItemStr = []
            for diffItem in sReasonDiffList:
                if not str(diffItem).startswith('Diff') and not str(diffItem).startswith('diff') and not str(diffItem).startswith('pass-'):
                    continue
                diffItem = str(diffItem).split(';')
                if len(diffItem) == 1:
                    for diffItem1 in diffItem:
                        if str(diffItem) in sReasonDiffItemList:
                            continue
                        else:
                            sReasonDiffItemList.append(diffItem)
                            diffItem1_escape = re.escape(diffItem1)
                            sReasonDiffItem1Data = sReasonDiffReportData[
                                (sReasonDiffReportData[result].str.contains(diffItem1_escape,na=False))
                                |
                                (sReasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False))
                                |
                                (sReasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False))
                            ]
                            sReasonDiffItem1Num = len(sReasonDiffItem1Data.index)
                            sReasonDiffItem1CaseList = sReasonDiffItem1Data[sFileName].dropna().unique()
                            sReasonDiffItem1CaseNum = len(sReasonDiffItem1CaseList)
                            sReasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(sReasonDiffItem1Num) + ", case: " + str(sReasonDiffItem1CaseNum))
                elif len(diffItem) >= 2:
                    for diffItem1 in diffItem:
                        if str(diffItem1) in sReasonDiffItemList:
                            continue
                        else:
                            sReasonDiffItemList.append(diffItem1)
                            diffItem1_escape = re.escape(diffItem1)
                            sReasonDiffItem1Data = sReasonDiffReportData[
                                sReasonDiffReportData[result].str.contains(diffItem1_escape,na=False)
                                |
                                sReasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False)
                                |
                                sReasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False)
                            ]
                            sReasonDiffItem1Num = len(sReasonDiffItem1Data.index)
                            sReasonDiffItem1CaseList = sReasonDiffItem1Data[sFileName].dropna().unique()
                            sReasonDiffItem1CaseNum = len(sReasonDiffItem1CaseList)
                            sReasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(sReasonDiffItem1Num) + ", case: " + str(sReasonDiffItem1CaseNum))
            sReasonDiffStatistics.append('\n'.join(tuple(sReasonDiffItemStr)))

            sReasonIssueReportData = sReasonNotMatchData[sReasonNotMatchData[result].str.contains('|'.join(cdcDiffList),na=False)]
            if sReasonIssueReportData.empty:
                sReasonIssueStatistics.append('')
            else:
                sReasonIssueList = np.concatenate(sReasonIssueReportData[mark_diff].dropna().unique(),axis=None)
                sReasonIssueItemList = []
                sReasonIssueItemStr = []
                for issueItem in sReasonIssueList:
                    if not str(issueItem).startswith('cdc') and not str(issueItem).startswith('CDC'):
                        continue
                    issueItem = str(issueItem).split(';')
                    for issueItem1 in issueItem:
                        if str(issueItem1) in sReasonIssueItemList:
                            continue
                        else:
                            sReasonIssueItemList.append(issueItem1)
                            issueItem1_escape = re.escape(issueItem1)
                            sReasonIssueItem1Data = sReasonIssueReportData[sReasonIssueReportData[mark_diff].str.contains(issueItem1_escape,na=False)]
                            sReasonIssueItem1Num = len(sReasonIssueItem1Data.index)
                            sReasonIssueItem1CaseList = sReasonIssueItem1Data[sFileName].dropna().unique()
                            sReasonIssueItem1CaseNum = len(sReasonIssueItem1CaseList)
                            sReasonIssueItemStr.append(f'{str(issueItem1)}: msg: {str(sReasonIssueItem1Num)}, case: {str(sReasonIssueItem1CaseNum)}')
                sReasonIssueStatistics.append('\n'.join(tuple(sReasonIssueItemStr)))
            # 总计reason对应的差异种类及对应的误报message条数
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
            # reasonFalseReportData = reasonMsgTotalData[
            #     (reasonMsgTotalData[result] == missingReport)
            #     |
            #     (reasonMsgTotalData[result] == falseReport)
            #     |
            #     (reasonMsgTotalData[result] == unmatchReport)
            # ]
            # reasonDiffReportData = reasonFalseReportData[
            #     reasonFalseReportData[mark_diff].str.contains('|'.join(passDiffList),na=False)
            #     |
            #     reasonFalseReportData[mark_running].str.contains('|'.join(passDiffList),na=False)
            # ]
            reasonFalseReportData = reasonMsgTotalData[reasonMsgTotalData[result] != matchReport]
            reasonDiffReportData = reasonFalseReportData[
                reasonFalseReportData[result].str.contains('|'.join(passDiffList),na=False)
                |
                (reasonFalseReportData[mark_diff].str.contains('|'.join(passDiffList),na=False) & (~reasonFalseReportData[mark_diff].str.contains('|'.join(cdcDiffList),na=True)))
                |
                reasonFalseReportData[mark_running].str.contains('|'.join(passDiffList),na=False)
            ]
            # sReasonDiffStatistics.append(sReasonDiffReportData[mark_diff].value_counts())
            reasonDiffList = np.concatenate((reasonDiffReportData[result].dropna().unique(),reasonDiffReportData[mark_diff].dropna().unique(),reasonDiffReportData[mark_running].dropna().unique()),axis=None)
            reasonDiffItemList = []
            reasonDiffItemStr = []
            for diffItem in reasonDiffList:
                if not str(diffItem).startswith('Diff') and not str(diffItem).startswith('diff') and not str(diffItem).startswith('pass-'):
                    continue
                diffItem = str(diffItem).split(';')
                if len(diffItem) == 1:
                    for diffItem1 in diffItem:
                        if str(diffItem) in reasonDiffItemList:
                            continue
                        else:
                            reasonDiffItemList.append(diffItem)
                            diffItem1_escape = re.escape(diffItem1)
                            reasonDiffItem1Data = reasonDiffReportData[
                                (reasonDiffReportData[result].str.contains(diffItem1_escape,na=False))
                                |
                                (reasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False))
                                |
                                (reasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False))
                            ]
                            reasonDiffItem1Num = len(reasonDiffItem1Data.index)
                            # reasonDiffItem1CaseList = reasonDiffItem1Data[fileName].dropna().unique()
                            eReasonDiffItem1CaseList = reasonDiffItem1Data[eFileName].dropna().unique()
                            sReasonDiffItem1CaseList = reasonDiffItem1Data[sFileName].dropna().unique()
                            reasonDiffItem1CaseList = list(set(list(eReasonDiffItem1CaseList) + list(sReasonDiffItem1CaseList)))
                            reasonDiffItem1CaseNum = len(reasonDiffItem1CaseList)
                            reasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(reasonDiffItem1Num) + ", case: " + str(reasonDiffItem1CaseNum))
                elif len(diffItem) >= 2:
                    for diffItem1 in diffItem:
                        if str(diffItem1) in reasonDiffItemList:
                            continue
                        else:
                            reasonDiffItemList.append(diffItem1)
                            diffItem1_escape = re.escape(diffItem1)
                            reasonDiffItem1Data = reasonDiffReportData[
                                reasonDiffReportData[result].str.contains(diffItem1_escape,na=False)
                                |
                                reasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False)
                                |
                                reasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False)
                            ]
                            reasonDiffItem1Num = len(reasonDiffItem1Data.index)
                            # reasonDiffItem1CaseList = reasonDiffItem1Data[fileName].dropna().unique()
                            eReasonDiffItem1CaseList = reasonDiffItem1Data[eFileName].dropna().unique()
                            sReasonDiffItem1CaseList = reasonDiffItem1Data[sFileName].dropna().unique()
                            reasonDiffItem1CaseList = list(set(list(eReasonDiffItem1CaseList) + list(sReasonDiffItem1CaseList)))
                            reasonDiffItem1CaseNum = len(reasonDiffItem1CaseList)
                            reasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(reasonDiffItem1Num) + ", case: " + str(reasonDiffItem1CaseNum))
            reasonDiffStatistics.append('\n'.join(tuple(reasonDiffItemStr)))

            reasonIssueReportData = reasonFalseReportData[reasonFalseReportData[mark_diff].str.contains('|'.join(cdcDiffList),na=False)]
            if reasonIssueReportData.empty:
                reasonIssueStatistics.append('')
            else:
                reasonIssueList = np.concatenate(reasonIssueReportData[mark_diff].dropna().unique(),axis=None)
                reasonIssueItemList = []
                reasonIssueItemStr = []
                for issueItem in reasonIssueList:
                    if not str(issueItem).startswith('cdc') and not str(issueItem).startswith('CDC'):
                        continue
                    issueItem = str(issueItem).split(';')
                    for issueItem1 in issueItem:
                        if str(issueItem1) in reasonIssueItemList:
                            continue
                        else:
                            reasonIssueItemList.append(issueItem1)
                            issueItem1_escape = re.escape(issueItem1)
                            reasonIssueItem1Data = reasonIssueReportData[reasonIssueReportData[mark_diff].str.contains(issueItem1_escape,na=False)]
                            reasonIssueItem1Num = len(reasonIssueItem1Data.index)
                            # reasonIssueItem1CaseList = reasonIssueItem1Data[fileName].dropna().unique()
                            eReasonIssueItem1CaseList = reasonIssueItem1Data[eFileName].dropna().unique()
                            sReasonIssueItem1CaseList = reasonIssueItem1Data[sFileName].dropna().unique()
                            reasonIssueItem1CaseList = list(set(list(eReasonDiffItem1CaseList) + list(sReasonDiffItem1CaseList)))
                            reasonIssueItem1CaseNum = len(reasonIssueItem1CaseList)
                            reasonIssueItemStr.append(f'{str(issueItem1)}: msg: {str(reasonIssueItem1Num)}, case: {str(reasonIssueItem1CaseNum)}')
                reasonIssueStatistics.append('\n'.join(tuple(reasonIssueItemStr)))

elif mode == "Setup" or mode == "Syntax":
    for msgId in outputMsgOrder:
        # e msgId list
        # eReasonMsgIdTotal.append(msgId)
        eMsgIdData = inData[inData[eMsgId] == msgId]

        # e reason list
        # eReasonReasonTotal.append("")
        eReasonMsgTotalData = eMsgIdData

        # e msg total num
        eReasonMsgNum = len(eReasonMsgTotalData.index)
        # eReasonMsgTotal.append(eReasonMsgNum)

        # eReasonCasesList: 某条reason对应的case的集合
        eReasonCasesList = eReasonMsgTotalData[eFileName].dropna().unique()
        eReasonCasesNum = len(eReasonCasesList)
        # eReasonCaseTotal.append(eReasonCasesNum)

        # eReasonFalseReportData：某条reason对应的摸底误报总数
        eReasonFalseReportData = eReasonMsgTotalData[
            (eReasonMsgTotalData[result] == falseReport)
            |
            (eReasonMsgTotalData[result] == unmatchReport)
        ]
        # eReasonFalseReportTotal.append(len(eReasonFalseReportData.index))
        # print (eReasonFalseReportData)

        # eReasonRealFalseReportData：某条reason对应的真实误报总数
        eReasonRealFalseReportData = eReasonFalseReportData[
            ~((eReasonFalseReportData[mark_diff].str.contains('|'.join(passDiffList),na=False)) & (~eReasonFalseReportData[mark_diff].str.contains('|'.join(cdcDiffList),na=True)))
            &
            ~eReasonFalseReportData[mark_running].str.contains('|'.join(passDiffList),na=False)
        ]
        eReasonRealFalseReportNum = len(eReasonRealFalseReportData.index)
        # eReasonRealFalseReportTotal.append(eReasonRealFalseReportNum)
        # print (eReasonRealFalseReportData)

        # eReasonRealFalseCasesList：某条reason对应真实误报case集合
        eReasonRealFalseCasesList = eReasonRealFalseReportData[eFileName].dropna().unique()
        # eReasonRealFalseCasesTotal.append(len(eReasonRealFalseCasesList))

        # eReasonFalseRatio： 某条reason对应的误报率
        if eReasonMsgNum == 0:
            eReasonFalseRatioNum = 0
        elif eReasonMsgNum != 0:
            eReasonFalseRatioNum = '{:.2%}'.format(eReasonRealFalseReportNum / eReasonMsgNum)
        # eReasonFalseRatio.append(eReasonFalseRatioNum)


        # eReasonDiffReportData：某条reason对应的差异种类及对应的误报message条数
        eReasonNotMatchData = eReasonMsgTotalData[eReasonMsgTotalData[result] != matchReport]
        eReasonDiffReportData = eReasonNotMatchData[
            eReasonNotMatchData[result].str.contains('|'.join(passDiffList),na=False)
            |
            ((eReasonNotMatchData[mark_diff].str.contains('|'.join(passDiffList),na=False)) & (~eReasonNotMatchData[mark_diff].str.contains('|'.join(cdcDiffList),na=True)))
            |
            eReasonNotMatchData[mark_running].str.contains('|'.join(passDiffList),na=False)
        ]
        # eReasonDiffStatistics.append(eReasonDiffReportData[mark_diff].value_counts())
        eReasonDiffList = np.concatenate((eReasonDiffReportData[result].dropna().unique(),eReasonDiffReportData[mark_diff].dropna().unique(),eReasonDiffReportData[mark_running].dropna().unique()),axis=None)
        eReasonDiffItemList = []
        eReasonDiffItemStr = []
        for diffItem in eReasonDiffList:
            if not str(diffItem).startswith('Diff') and not str(diffItem).startswith('diff') and not str(diffItem).startswith('pass-'):
                    continue
            diffItem = str(diffItem).split(';')
            if len(diffItem) == 1:
                for diffItem1 in diffItem:
                    if str(diffItem) in eReasonDiffItemList:
                        continue
                    else:
                        eReasonDiffItemList.append(diffItem)
                        diffItem1_escape = re.escape(diffItem1)
                        eReasonDiffItem1Data = eReasonDiffReportData[
                            eReasonDiffReportData[result].str.contains(diffItem1_escape,na=False)
                            |
                            eReasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False)
                            |
                            eReasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False)
                        ]
                        eReasonDiffItem1Num = len(eReasonDiffItem1Data.index)
                        eReasonDiffItem1CaseList = eReasonDiffItem1Data[eFileName].dropna().unique()
                        eReasonDiffItem1CaseNum = len(eReasonDiffItem1CaseList)
                        eReasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(eReasonDiffItem1Num) + ", case: " + str(eReasonDiffItem1CaseNum))
            elif len(diffItem) >= 2:
                for diffItem1 in diffItem:
                    if str(diffItem1) in eReasonDiffItemList:
                        continue
                    else:
                        eReasonDiffItemList.append(diffItem1)
                        diffItem1_escape = re.escape(diffItem1)
                        eReasonDiffItem1Data = eReasonDiffReportData[
                            eReasonDiffReportData[result].str.contains(diffItem1_escape,na=False)
                            |
                            eReasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False)
                            |
                            eReasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False)
                        ]
                        eReasonDiffItem1Num = len(eReasonDiffItem1Data.index)
                        eReasonDiffItem1CaseList = eReasonDiffItem1Data[eFileName].dropna().unique()
                        eReasonDiffItem1CaseNum = len(eReasonDiffItem1CaseList)
                        eReasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(eReasonDiffItem1Num) + ", case: " + str(eReasonDiffItem1CaseNum))
        # eReasonDiffStatistics.append('\n'.join(tuple(eReasonDiffItemStr)))
            eReasonIssueReportData = eReasonNotMatchData[eReasonNotMatchData[result].str.contains('|'.join(cdcDiffList),na=False)]
            if eReasonIssueReportData.empty:
                eReasonIssueItemStr = ''
            else:
                eReasonIssueList = np.concatenate(eReasonIssueReportData[mark_diff].dropna().unique(),axis=None)
                eReasonIssueItemList = []
                eReasonIssueItemStr = []
                for issueItem in eReasonIssueList:
                    if not str(issueItem).startswith('cdc') and not str(issueItem).startswith('CDC'):
                        continue
                    issueItem = str(issueItem).split(';')
                    for issueItem1 in issueItem:
                        if str(issueItem1) in eReasonIssueItemList:
                            continue
                        else:
                            eReasonIssueItemList.append(issueItem1)
                            issueItem1_escape = re.escape(issueItem1)
                            eReasonIssueItem1Data = eReasonIssueReportData[eReasonIssueReportData[mark_diff].str.contains(issueItem1_escape,na=False)]
                            eReasonIssueItem1Num = len(eReasonIssueItem1Data.index)
                            eReasonIssueItem1CaseList = eReasonIssueItem1Data[eFileName].dropna().unique()
                            eReasonIssueItem1CaseNum = len(eReasonIssueItem1CaseList)
                            eReasonIssueItemStr.append(f'{str(issueItem1)}: msg: {str(eReasonIssueItem1Num)}, case: {str(eReasonIssueItem1CaseNum)}')

        # 3方对应的rule
        sRuleItems = mapDict[msgId]
        for sRuleItem in sRuleItems:
            eReasonMsgIdTotal.append(msgId)
            eReasonReasonTotal.append("")
            eReasonMsgTotal.append(eReasonMsgNum)
            eReasonCaseTotal.append(eReasonCasesNum)
            eReasonFalseReportTotal.append(len(eReasonFalseReportData.index))
            eReasonRealFalseReportTotal.append(eReasonRealFalseReportNum)
            eReasonRealFalseCasesTotal.append(len(eReasonRealFalseCasesList))
            eReasonFalseRatio.append(eReasonFalseRatioNum)
            eReasonDiffStatistics.append('\n'.join(tuple(eReasonDiffItemStr)))
            eReasonIssueStatistics.append('\n'.join(tuple(eReasonIssueItemStr)))

            sReasonRuleTotal.append(sRuleItem)
            sReasonReasonTotal.append("")

            # 3方 report 总数
            sRuleData = inData[inData[sRule] == sRuleItem]
            sReasonMsgTotalData = sRuleData

            # # sReasonItem: enno messageId reason对应的3方reason
            # sReasonItems = mapDict[msgId][eReasonItem]
            # sReasonStrList = []
            # for sReasonItem in sReasonItems:
            #     sReasonStrList.append(sReasonItem[1:])
            # sReasonReasonTotal.append("\n/\n".join(sReasonStrList))

            # # 3方 report总数
            # # print ("=============\n" + str(sReasonItems) + "\n")
            # sReasonMsgTotalData = inData[inData[sReason].str.contains('|'.join(sReasonItems),na=False,regex=True)]
            # # print (sReasonMsgTotalData[sReason])
            sReasonMsgNum = len(sReasonMsgTotalData.index)
            sReasonMsgTotal.append(sReasonMsgNum)

            # 3方涉及case数
            sReasonCasesList = sReasonMsgTotalData[sFileName].dropna().unique()
            sReasonCaseTotal.append(len(sReasonCasesList))
            
            # 3方摸底漏报数
            sReasonFalseReportData = sReasonMsgTotalData[
                (sReasonMsgTotalData[result] == missingReport)
                |
                (sReasonMsgTotalData[result] == unmatchReport)
            ]
            sReasonFalseReportTotal.append(len(sReasonFalseReportData.index))

            # 3方真实漏报数
            sReasonRealFalseReportData = sReasonFalseReportData[
                ~((sReasonFalseReportData[mark_diff].str.contains('|'.join(passDiffList),na=False)) & (~sReasonFalseReportData[mark_diff].str.contains('|'.join(cdcDiffList),na=True)))
                &
                ~sReasonFalseReportData[mark_running].str.contains('|'.join(passDiffList),na=False)
            ]
            sReasonRealFalseReportNum = len(sReasonRealFalseReportData.index)
            sReasonRealFalseReportTotal.append(sReasonRealFalseReportNum)

            # 3方真实漏报case数
            sReasonRealFalseCasesList = sReasonRealFalseReportData[sFileName].dropna().unique()
            sReasonRealFalseCasesTotal.append(len(sReasonRealFalseCasesList))

            # 3方reason漏报率
            if sReasonMsgNum == 0:
                sReasonFalseRatio.append(0)
            elif sReasonMsgNum != 0:
                sReasonFalseRatio.append('{:.2%}'.format(sReasonRealFalseReportNum / sReasonMsgNum))

            # 3方reason对应的差异种类及对应的误报message条数
            sReasonNotMatchData = sReasonMsgTotalData[sReasonMsgTotalData[result] != matchReport]
            sReasonDiffReportData = sReasonNotMatchData[
                ((sReasonNotMatchData[result].str.contains('|'.join(passDiffList),na=False)) & (~sReasonNotMatchData[result].str.contains('|'.join(cdcDiffList),na=True)))
                |
                sReasonNotMatchData[mark_diff].str.contains('|'.join(passDiffList),na=False)
                |
                sReasonNotMatchData[mark_running].str.contains('|'.join(passDiffList),na=False)
            ]
            # sReasonDiffStatistics.append(sReasonDiffReportData[mark_diff].value_counts())
            sReasonDiffList = np.concatenate((sReasonDiffReportData[result].dropna().unique(),sReasonDiffReportData[mark_diff].dropna().unique(),sReasonDiffReportData[mark_running].dropna().unique()),axis=None)
            sReasonDiffItemList = []
            sReasonDiffItemStr = []
            for diffItem in sReasonDiffList:
                if not str(diffItem).startswith('Diff') and not str(diffItem).startswith('diff') and not str(diffItem).startswith('pass-'):
                    continue
                diffItem = str(diffItem).split(';')
                if len(diffItem) == 1:
                    for diffItem1 in diffItem:
                        if str(diffItem) in sReasonDiffItemList:
                            continue
                        else:
                            sReasonDiffItemList.append(diffItem)
                            diffItem1_escape = re.escape(diffItem1)
                            sReasonDiffItem1Data = sReasonDiffReportData[
                                sReasonDiffReportData[result].str.contains(diffItem1_escape,na=False)
                                |
                                sReasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False)
                                |
                                sReasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False)
                            ]
                            sReasonDiffItem1Num = len(sReasonDiffItem1Data.index)
                            sReasonDiffItem1CaseList = sReasonDiffItem1Data[sFileName].dropna().unique()
                            sReasonDiffItem1CaseNum = len(sReasonDiffItem1CaseList)
                            sReasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(sReasonDiffItem1Num) + ", case: " + str(sReasonDiffItem1CaseNum))
                elif len(diffItem) >= 2:
                    for diffItem1 in diffItem:
                        if str(diffItem1) in sReasonDiffItemList:
                            continue
                        else:
                            sReasonDiffItemList.append(diffItem1)
                            diffItem1_escape = re.escape(diffItem1)
                            sReasonDiffItem1Data = sReasonDiffReportData[
                                sReasonDiffReportData[result].str.contains(diffItem1_escape,na=False)
                                |
                                sReasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False)
                                |
                                sReasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False)
                            ]
                            sReasonDiffItem1Num = len(sReasonDiffItem1Data.index)
                            sReasonDiffItem1CaseList = sReasonDiffItem1Data[sFileName].dropna().unique()
                            sReasonDiffItem1CaseNum = len(sReasonDiffItem1CaseList)
                            sReasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(sReasonDiffItem1Num) + ", case: " + str(sReasonDiffItem1CaseNum))
            sReasonDiffStatistics.append('\n'.join(tuple(sReasonDiffItemStr)))
            # 总计reason对应的差异种类及对应的误报message条数
            sReasonIssueReportData = sReasonNotMatchData[sReasonNotMatchData[result].str.contains('|'.join(cdcDiffList),na=False)]
            if sReasonIssueReportData.empty:
                sReasonIssueStatistics.append('')
            else:
                sReasonIssueList = np.concatenate(sReasonIssueReportData[mark_diff].dropna().unique(),axis=None)
                sReasonIssueItemList = []
                sReasonIssueItemStr = []
                for issueItem in sReasonIssueList:
                    if not str(issueItem).startswith('cdc') and not str(issueItem).startswith('CDC'):
                        continue
                    issueItem = str(issueItem).split(';')
                    for issueItem1 in issueItem:
                        if str(issueItem1) in sReasonIssueItemList:
                            continue
                        else:
                            sReasonIssueItemList.append(issueItem1)
                            issueItem1_escape = re.escape(issueItem1)
                            sReasonIssueItem1Data = sReasonIssueReportData[sReasonIssueReportData[mark_diff].str.contains(issueItem1_escape,na=False)]
                            sReasonIssueItem1Num = len(sReasonIssueItem1Data.index)
                            sReasonIssueItem1CaseList = sReasonIssueItem1Data[sFileName].dropna().unique()
                            sReasonIssueItem1CaseNum = len(sReasonIssueItem1CaseList)
                            sReasonIssueItemStr.append(f'{str(issueItem1)}: msg: {str(sReasonIssueItem1Num)}, case: {str(sReasonIssueItem1CaseNum)}')
                sReasonIssueStatistics.append('\n'.join(tuple(sReasonIssueItemStr)))

            reasonMsgTotalData = inData[
                (inData[eMsgId] == msgId)
                |
                (inData[sRule].str.contains('|'.join(sRuleItems),na=False,regex=True))
            ]
            reasonFalseReportData = reasonMsgTotalData[reasonMsgTotalData[result] != matchReport]
            reasonDiffReportData = reasonFalseReportData[
                reasonFalseReportData[result].str.contains('|'.join(passDiffList),na=False)
                |
                ((reasonFalseReportData[mark_diff].str.contains('|'.join(passDiffList),na=False)) & (~reasonFalseReportData[mark_diff].str.contains('|'.join(cdcDiffList),na=True)))
                |
                reasonFalseReportData[mark_running].str.contains('|'.join(passDiffList),na=False)
            ]
            # sReasonDiffStatistics.append(sReasonDiffReportData[mark_diff].value_counts())
            reasonDiffList = np.concatenate((reasonDiffReportData[result].dropna().unique(),reasonDiffReportData[mark_diff].dropna().unique(),reasonDiffReportData[mark_running].dropna().unique()),axis=None)
            reasonDiffItemList = []
            reasonDiffItemStr = []
            for diffItem in reasonDiffList:
                if not str(diffItem).startswith('Diff') and not str(diffItem).startswith('diff') and not str(diffItem).startswith('pass-'):
                    continue
                diffItem = str(diffItem).split(';')
                if len(diffItem) == 1:
                    for diffItem1 in diffItem:
                        if str(diffItem) in reasonDiffItemList:
                            continue
                        else:
                            reasonDiffItemList.append(diffItem)
                            diffItem1_escape = re.escape(diffItem1)
                            reasonDiffItem1Data = reasonDiffReportData[
                                reasonDiffReportData[result].str.contains(diffItem1_escape,na=False)
                                |
                                reasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False)
                                |
                                reasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False)
                            ]
                            reasonDiffItem1Num = len(reasonDiffItem1Data.index)
                            # reasonDiffItem1CaseList = reasonDiffItem1Data[fileName].dropna().unique()
                            eReasonDiffItem1CaseList = reasonDiffItem1Data[eFileName].dropna().unique()
                            sReasonDiffItem1CaseList = reasonDiffItem1Data[sFileName].dropna().unique()
                            reasonDiffItem1CaseList = list(set(eReasonDiffItem1CaseList + sReasonDiffItem1CaseList))
                            reasonDiffItem1CaseNum = len(reasonDiffItem1CaseList)
                            reasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(reasonDiffItem1Num) + ", case: " + str(reasonDiffItem1CaseNum))
                elif len(diffItem) >= 2:
                    for diffItem1 in diffItem:
                        if str(diffItem1) in reasonDiffItemList:
                            continue
                        else:
                            reasonDiffItemList.append(diffItem1)
                            diffItem1_escape = re.escape(diffItem1)
                            reasonDiffItem1Data = reasonDiffReportData[
                                reasonDiffReportData[result].str.contains(diffItem1_escape,na=False)
                                |
                                reasonDiffReportData[mark_diff].str.contains(diffItem1_escape,na=False)
                                |
                                reasonDiffReportData[mark_running].str.contains(diffItem1_escape,na=False)
                            ]
                            reasonDiffItem1Num = len(reasonDiffItem1Data.index)
                            # reasonDiffItem1CaseList = reasonDiffItem1Data[fileName].dropna().unique()
                            eReasonDiffItem1CaseList = reasonDiffItem1Data[eFileName].dropna().unique()
                            sReasonDiffItem1CaseList = reasonDiffItem1Data[sFileName].dropna().unique()
                            reasonDiffItem1CaseList = list(set(list(eReasonDiffItem1CaseList) + list(sReasonDiffItem1CaseList)))
                            reasonDiffItem1CaseNum = len(reasonDiffItem1CaseList)
                            reasonDiffItemStr.append(str(diffItem1) + ": msg: " + str(reasonDiffItem1Num) + ", case: " + str(reasonDiffItem1CaseNum))
            reasonDiffStatistics.append('\n'.join(tuple(reasonDiffItemStr)))

            reasonIssueReportData = reasonFalseReportData[reasonFalseReportData[mark_diff].str.contains('|'.join(cdcDiffList),na=False)]
            if reasonIssueReportData.empty:
                reasonIssueStatistics.append('')
            else:
                reasonIssueList = np.concatenate(reasonIssueReportData[mark_diff].dropna().unique(),axis=None)
                reasonIssueItemList = []
                reasonIssueItemStr = []
                for issueItem in reasonIssueList:
                    if not str(issueItem).startswith('cdc') and not str(issueItem).startswith('CDC'):
                        continue
                    issueItem = str(issueItem).split(';')
                    for issueItem1 in issueItem:
                        if str(issueItem1) in reasonIssueItemList:
                            continue
                        else:
                            reasonIssueItemList.append(issueItem1)
                            issueItem1_escape = re.escape(issueItem1)
                            reasonIssueItem1Data = reasonIssueReportData[reasonIssueReportData[mark_diff].str.contains(issueItem1_escape,na=False)]
                            reasonIssueItem1Num = len(reasonIssueItem1Data.index)
                            # reasonIssueItem1CaseList = reasonIssueItem1Data[fileName].dropna().unique()
                            eReasonIssueItem1CaseList = reasonIssueItem1Data[eFileName].dropna().unique()
                            sReasonIssueItem1CaseList = reasonIssueItem1Data[sFileName].dropna().unique()
                            reasonIssueItem1CaseList = list(set(list(eReasonIssueItem1CaseList) + list(sReasonIssueItem1CaseList)))
                            reasonIssueItem1CaseNum = len(reasonIssueItem1CaseList)
                            reasonIssueItemStr.append(f'{str(issueItem1)}: msg: {str(reasonIssueItem1Num)}, case: {str(reasonIssueItem1CaseNum)}')
                reasonIssueStatistics.append('\n'.join(tuple(reasonIssueItemStr)))

outputData = {}
outputData[eMsgId] = eReasonMsgIdTotal
outputData[sRule] = sReasonRuleTotal
# outputData[eReason] = eReasonList
outputData[eReason] = eReasonReasonTotal
outputData[sReason] = sReasonReasonTotal

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
# pandas.DataFrame(outputData).to_excel(resultExcelName,index=False)
