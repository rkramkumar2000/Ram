"""Client for reading schema definitions from local Excel sheets."""

import pandas as pd
import os
from typing import List, Dict, Any

class LocalSheetsClient:
    def __init__(self, excel_file_path: str):
        """Initialize with path to local Excel file."""
        if not os.path.exists(excel_file_path):
            raise FileNotFoundError(f"Excel file not found: {excel_file_path}")
        self.excel_file_path = excel_file_path

    def list_tables(self) -> List[str]:
        """Get list of all sheet names (tables)."""
        return pd.ExcelFile(self.excel_file_path).sheet_names

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Read schema definition from specified sheet."""
        try:
            # Read the first 4 rows (headers, types, constraints, metadata)
            df = pd.read_excel(
                self.excel_file_path,
                sheet_name=table_name,
                nrows=4,  # Read only the schema definition rows
                header=None
            )

            # Convert to list of lists format
            rows = df.values.tolist()
            
            # Remove any None/NaN values and convert to empty strings
            rows = [[str(cell) if pd.notna(cell) else '' for cell in row] for row in rows]

            return {
                'table_name': table_name,
                'rows': rows
            }
        except Exception as e:
            raise Exception(f"Error reading schema for table {table_name}: {str(e)}")

    def close(self):
        """Cleanup (not needed for local files but kept for compatibility)."""
        pass