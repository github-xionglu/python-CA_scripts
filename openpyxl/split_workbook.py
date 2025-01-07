import argparse
import sys
from datetime import datetime
from openpyxl import load_workbook 
import pandas as pd

def process_excel(input_file, x_param):
    current_date = datetime.now().strftime("%m%d")
    output_file = f"{x_param}_analysis_{current_date}.xlsx"
    match_output_file = f"{x_param}_match_{current_date}.xlsx"

    # Load the workbook and select the active worksheet
    wb = load_workbook(input_file)
    ws = wb.active

    # Convert the worksheet to a DataFrame
    data = ws.values
    columns = next(data)[0:]  # Get the first row as columns
    df = pd.DataFrame(data, columns=columns)

    # Define the conditions to check
    def check_conditions(group):
        condition_1 = ~group['result'].isin(['False report', 'Missing report', 'Unmatch'])
        condition_2 = (group['is_analysis'] == 7) & group[['diff_basis']].notnull().all(axis=1)
        return (condition_1 | condition_2).all()

    to_delete = df.groupby('test_name').filter(check_conditions).index
    deleted_rows = df.loc[to_delete]
    remaining_rows = df.drop(to_delete)

    # Write the remaining rows back to the worksheet
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        remaining_rows.to_excel(writer, index=False)

    # Save the deleted rows to a new workbook
    with pd.ExcelWriter(match_output_file, engine='openpyxl') as writer:
        deleted_rows.to_excel(writer, index=False)

def main():
    parser = argparse.ArgumentParser(description='Process an Excel file based on a specified mode.')
    parser.add_argument('input_file', type=str, help='Path to the input Excel file')
    parser.add_argument('mode', type=str, choices=['ac', 'ar', 'setup', 'bulitin'], help='Mode of operation: ac, ar, setup, bulitin')

    args = parser.parse_args()

    process_excel(args.input_file, args.mode)

if __name__ == '__main__':
    main()

# 用于拆分表格脚本
