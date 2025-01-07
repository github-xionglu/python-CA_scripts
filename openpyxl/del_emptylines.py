import os
import sys
import getopt
import openpyxl
from tqdm import tqdm

def printUsage():
    print("usage: %s -f|--inputfile <file>" % (sys.argv[0]))
    print('''   
    -f|--inputfile    :   specify the file
    -h                :   show help manual
    ''')
    sys.exit(-1)

def del_emptylines(file):
    wb = openpyxl.load_workbook(file)
    ws = wb.active
    for row in tqdm(ws.iter_rows()):
        if all(cell.value is None for cell in row):
            ws.delete_rows(row[0].row)
            
    wb.save(file)

if __name__ == "__main__":
    file = ""

    try:
        opts,args =  getopt.getopt(sys.argv[1:],"hf:",["inputfile="])
    except getopt.GetoptError:
        printUsage()

    for opt,arg in opts:
        if opt == '-h':
            printUsage()
        elif opt in ('-f','--inputfile'):
            file = arg

    print (file)
    if file == "":
        print(f'ERROR: No valid input file')
    else:
        if os.path.exists(file):
            del_emptylines(file)
        else:
            print(f'file, {file}, is not exists')
