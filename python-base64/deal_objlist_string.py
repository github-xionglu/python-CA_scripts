import sys
import os
import pandas
import getopt
import base64

def printUsage():
    print("usage: %s -i|--input_file <input file> [-o|--output_file <output file>] [-c|--col_name <col name>] [-d|--decode] [--csv]" % (sys.argv[0]))
    print(
        '''
        -i | --input_file       :       specify the input file.
        -o | --output_file      :       specify the output file, the default is the input file name.
        -c | --col_name         :       specify the column of the file to encode or decode. [default: obj_list]
        -d | --decode           :       Specifies the decode process, the default is the encode process.
        --csv                   :       Specify the file type of the input file. [default: excel]
        -h | --help             :       show help manual.
        '''
    )
    sys.exit(-1)

def encode_str(encode_text):
    try:
        return base64.b64encode(encode_text.encode('utf-8')).decode('utf-8')
    except ValueError:
        return encode_text
    except AttributeError:
        return encode_text

def decode_str(decode_text):
    try:
        return base64.b64decode(decode_text.encode('utf-8')).decode('utf-8')
    except ValueError:
        return decode_text
    except AttributeError:
        return decode_text

def convert_to_int(variable):
    try:
        return int(variable)
    except ValueError:
        return variable

def trans_file(inputFile,colName,encode,isCsvFile):
    if not isCsvFile:
        inData = pandas.read_excel(inputFile)
    elif isCsvFile:
        inData = pandas.read_csv(inputFile)

    if encode:
        inData[colName] = [encode_str(encode_text) for encode_text in inData[colName]]
    elif not encode:
        inData[colName] = [decode_str(decode_text) for decode_text in inData[colName]]

    if 'enno_line_num' in inData.columns:
        inData['enno_line_num'] = [convert_to_int(var) for var in inData['enno_line_num']]
    if 'enno_line_num' in inData.columns:
        inData['sg_line_num'] = [convert_to_int(var) for var in inData['sg_line_num']]
    if 'is_analysis' in inData.columns:
        inData['is_analysis'] = [convert_to_int(var) for var in inData['is_analysis']]

    return inData

def main():
    inputFile = ""
    outputFile = ""
    colName = "obj_list"
    encode = True
    isCsvFile = False

    try:
        opts,args = getopt.getopt(sys.argv[1:],"hi:o:c:d",["help","input_file=","output_file=","col_name=","decode","csv"])
    except getopt.GetoptError:
        printUsage()

    for opt,arg in opts:
        if opt in ('-h','--help'):
            printUsage()
        elif opt in ("-i","--input_file"):
            inputFile = arg
        elif opt in ("-o","--output_file"):
            outputFile = arg
        elif opt in ("-c","--col_name"):
            colName = arg
        elif opt in ("-d","--decode"):
            encode = False
        elif opt == "--csv":
            isCsvFile = True

    if outputFile == "":
        outputFile = inputFile

    outputData = trans_file(inputFile,colName,encode,isCsvFile)

    if not isCsvFile:
        pandas.DataFrame(outputData).to_excel(outputFile, index=False)
    elif isCsvFile:
         pandas.DataFrame(outputData).to_csv(outputFile, index=False)

if __name__ == "__main__":
    main()
    
