#!/usr/bin/env python3
"""
SQL generation script for local Excel files.
"""

import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv
from rich.console import Console
import pandas as pd

console = Console()

def clean_identifier(name: str) -> str:
    """Clean and format SQL identifier names."""
    return name.strip().replace(" ", "_")

def generate_sql_for_sheet(sheet_name: str, df: pd.DataFrame) -> str:
    """Generate SQL CREATE TABLE statement for a sheet."""
    sql = f"-- Table: {sheet_name}\n"
    sql += f"CREATE TABLE IF NOT EXISTS {sheet_name} (\n"
    
    # Get all rows after the header row
    data_rows = df.iloc[1:]  # Skip the header row
    
    # Process each column definition row
    columns = []
    for _, row in data_rows.iterrows():
        col_name = clean_identifier(str(row[0]))  # First column has column name
        data_type = str(row[1]).upper() if pd.notna(row[1]) else "VARCHAR(255)"  # Second column has type
        constraints = []
        
        # Add constraints from both Constraints and Additional metadata columns
        if pd.notna(row[2]) and str(row[2]).strip():  # Constraints column
            constraint_str = str(row[2]).upper()
            if "UNIQUE" in constraint_str:
                constraints.append("UNIQUE")
            if "NOT NULL" in constraint_str:
                constraints.append("NOT NULL")
                
        if pd.notna(row[3]) and str(row[3]).strip():  # Additional metadata column
            metadata_str = str(row[3]).upper()
            if "PRIMARY KEY" in metadata_str:
                constraints.append("PRIMARY KEY")
                
        if col_name and not col_name.isspace():
            # Build column definition
            col_def = [f"    {col_name}", data_type]
            col_def.extend(constraints)
            columns.append(" ".join(col_def))
    
    sql += ",\n".join(columns)
    sql += "\n);"
    return sql

def main():
    """Main execution flow."""
    # Load environment variables
    load_dotenv()
    
    excel_path = os.path.join(os.environ.get("EXCEL_FILE_PATH", ""), "Sheet.xlsx")
    
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
        os.makedirs("sql_files", exist_ok=True)
        
        # Process each sheet
        for sheet_name in sheet_names:
            console.print(f"\nProcessing sheet: {sheet_name}")
            
            try:
                # Read the first 4 rows
                df = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=4, header=None)
                
                # Generate SQL
                sql_content = generate_sql_for_sheet(sheet_name, df)
                
                # Write SQL file
                sql_file_path = f"sql_files/{sheet_name}.sql"
                with open(sql_file_path, "w") as f:
                    f.write(sql_content)
                
                console.print(f"[green]Created SQL file: {sql_file_path}")
                
            except Exception as e:
                console.print(f"[red]Error processing sheet {sheet_name}: {str(e)}")
                console.print(f"[red]Exception details: {e}")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
