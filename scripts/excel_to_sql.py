#!/usr/bin/env python3
"""
Simple Excel to SQL converter for testing.
"""

import os
from dotenv import load_dotenv
import pandas as pd
from rich.console import Console
import asyncio

console = Console()

async def main():
    """Main execution flow."""
    # Load environment variables
    load_dotenv()
    
    excel_path = os.path.join(os.environ.get('EXCEL_FILE_PATH', ''), 'Sheet.xlsx')
    
    if not os.path.exists(excel_path):
        console.print(f"[red]Error: Excel file not found at {excel_path}")
        console.print(f"Looking for file at: {excel_path}")
        return

    console.print("[green]Starting SQL Schema Generation...")

    try:
        # Initialize Excel reading
        excel_file = pd.ExcelFile(excel_path)
        sheet_names = excel_file.sheet_names
        
        console.print(f"Found sheets: {sheet_names}")
        
        # Create sql_files directory
        os.makedirs('sql_files', exist_ok=True)
        
        # Process each sheet
        for sheet_name in sheet_names:
            console.print(f"\nProcessing sheet: {sheet_name}")
            
            try:
                # Read the sheet with headers
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
                
                # Create SQL file
                sql_file_path = f"sql_files/{sheet_name.lower()}.sql"
                with open(sql_file_path, 'w') as f:
                    f.write(f"-- Table: {sheet_name}\n")
                    f.write(f"CREATE TABLE IF NOT EXISTS {sheet_name.lower()} (\n")
                    
                    columns = []
                    # Process each row as a column definition
                    for _, row in df.iterrows():
                        col_name = row['Column names']
                        data_type = row['Data types']
                        constraints = row['Constraints']
                        metadata = row['Additional metadata']
                        
                        if pd.notna(col_name) and pd.notna(data_type):
                            col_def = f"    {col_name} {data_type}"
                            
                            if pd.notna(constraints):
                                col_def += f" {constraints}"
                            
                            if pd.notna(metadata) and 'PRIMARY KEY' in str(metadata).upper():
                                col_def += " PRIMARY KEY"
                                
                            columns.append(col_def)
                    
                    f.write(',\n'.join(columns))
                    f.write("\n);")
                
                console.print(f"[green]Created SQL file: {sql_file_path}")
                
            except Exception as e:
                console.print(f"[red]Error processing sheet {sheet_name}: {str(e)}")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())