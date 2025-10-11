#!/usr/bin/env python3
"""
SQL generation script for local Excel files.
"""

import os
import sys
from typing import List, Dict
from dotenv import load_dotenv
from rich.console import Console
import pandas as pd
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
                # Read the first 4 rows
                df = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=4, header=None)
                
                # Convert to lists and clean up NaN values
                rows = df.values.tolist()
                rows = [[str(cell) if pd.notna(cell) else '' for cell in row] for row in rows]
                
                # Create SQL file
                sql_file_path = f"sql_files/{sheet_name}.sql"
                with open(sql_file_path, 'w') as f:
                    f.write(f"-- Table: {sheet_name}\n")
                    f.write("CREATE TABLE IF NOT EXISTS " + sheet_name + " (\n")
                    
                    # First row contains column names
                    columns = []
                    for i, col_name in enumerate(rows[0]):
                        if col_name.strip():  # Skip empty columns
                            col_def = f"    {col_name} {rows[1][i] or 'VARCHAR(255)'}"  # Use second row for types
                            if i < len(rows[2]) and 'NOT NULL' in rows[2][i].upper():  # Check constraints
                                col_def += " NOT NULL"
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

console = Console()

async def main():
    """Main execution flow."""
    # Load environment variables
    load_dotenv()
    excel_path = os.path.join(os.environ.get('EXCEL_FILE_PATH', ''), 'Sheet.xlsx')
    
    if not os.path.exists(excel_path):
        console.print(f"[red]Error: Excel file not found at {excel_path}")
        return

    console.print("[green]Starting SQL Schema Generation...")

    try:
        # Initialize client
        sheets_client = LocalSheetsClient(excel_path)
        
        # Get schemas from sheets
        console.print("Reading schemas from Excel sheets...")
        for table in sheets_client.list_tables():
            console.print(f"Processing table: {table}")
            table_data = sheets_client.get_table_schema(table)
            schema = parse_rows_to_schema(table, table_data['rows'])
            console.print(f"Schema for {table}:", schema)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
    column_defs = []
    for col in columns:
        col_type = infer_sql_type(col['type'])
        column_defs.append(f"{col['name']} {col_type}")
    
    sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {',\n        '.join(column_defs)}
    );
    """
    return sqlparse.format(sql, reindent=True)

def generate_insert_statements(table_name: str, data: List[Dict]) -> List[str]:
    """Generate INSERT statements for data."""
    if not data:
        return []
    
    columns = list(data[0].keys())
    statements = []
    
    for row in data:
        values = [str(row[col]) if row[col] is not None else 'NULL' for col in columns]
        sql = f"""
        INSERT INTO {table_name}
        ({', '.join(columns)})
        VALUES
        ({', '.join(values)});
        """
        statements.append(sqlparse.format(sql, reindent=True))
    
    return statements

def infer_sql_type(value: any) -> str:
    """Infer SQL data type from Python value."""
    if isinstance(value, int):
        return 'INTEGER'
    elif isinstance(value, float):
        return 'DECIMAL'
    elif isinstance(value, bool):
        return 'BOOLEAN'
    else:
        return 'TEXT'