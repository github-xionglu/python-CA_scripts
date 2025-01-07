from openpyxl import load_workbook
from openpyxl.drawing.image import Image

wbName = 'ar_result_2024_08_01.xlsx'
wb = load_workbook(wbName)

sheet_names = wb.sheetnames
for sheet_name in sheet_names:
    if sheet_name != 'ar_result_2024_08_01':
        sheet = wb[sheet_name]
        wb.remove(sheet)

wb.save('test-delshet.xlsx')
