#!/usr/bin/env python3
"""
Google Sheets client for accessing and reading spreadsheet data with schema inference.
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional, Any
import time
from tenacity import retry, stop_after_attempt, wait_exponential

class SheetError(Exception):
    """Base exception for sheet operations."""
    pass

class SheetConnectionError(SheetError):
    """Exception for connection issues."""
    pass

class SheetNotFoundError(SheetError):
    """Exception when sheet is not found."""
    pass

class SheetSchemaError(SheetError):
    """Exception for schema parsing issues."""
    pass

class SheetsClient:
    def __init__(self, service_account_file: str, sheet_id: str):
        """Initialize the Google Sheets client.
        
        Args:
            service_account_file (str): Path to service account credentials JSON
            sheet_id (str): Google Sheet ID to connect to
        """
        self.sheet_id = sheet_id
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        try:
            self.credentials = Credentials.from_service_account_file(
                service_account_file, scopes=self.scope
            )
            self.client = gspread.authorize(self.credentials)
            self.spreadsheet = self.client.open_by_key(sheet_id)
        except Exception as e:
            raise SheetConnectionError(f"Failed to initialize sheets client: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def list_tables(self) -> List[str]:
        """List all available worksheets/tables in the spreadsheet.
        
        Returns:
            List[str]: List of worksheet titles
        """
        try:
            return [ws.title for ws in self.spreadsheet.worksheets()]
        except Exception as e:
            raise SheetNotFoundError(f"Failed to list worksheets: {str(e)}")

    def _infer_sql_type(self, value: Any) -> str:
        """Infer SQL data type from sample value."""
        if isinstance(value, bool):
            return "BOOLEAN"
        elif isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "DECIMAL"
        elif isinstance(value, str):
            try:
                time.strptime(value, "%Y-%m-%d")
                return "DATE"
            except ValueError:
                try:
                    time.strptime(value, "%Y-%m-%d %H:%M:%S")
                    return "TIMESTAMP"
                except ValueError:
                    return "TEXT"
        return "TEXT"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def get_table_schema(self, table_name: str) -> Dict:
        """Get structured schema information for a worksheet.
        
        Args:
            table_name (str): Name of the worksheet
            
        Returns:
            Dict containing table schema:
            {
                "table_name": str,
                "columns": [
                    {
                        "name": str,
                        "datatype": str,
                        "nullable": bool,
                        "default": Optional[Any]
                    },
                    ...
                ]
            }
        """
        try:
            worksheet = self.spreadsheet.worksheet(table_name)
            all_values = worksheet.get_all_values()
            
            if not all_values:
                raise SheetSchemaError(f"Worksheet '{table_name}' is empty")

            headers = all_values[0]
            if len(all_values) < 2:
                # Only header row present, create basic schema
                return {
                    "table_name": table_name,
                    "columns": [
                        {
                            "name": col.strip(),
                            "datatype": "TEXT",
                            "nullable": True,
                            "default": None
                        }
                        for col in headers if col.strip()
                    ]
                }

            # Check if metadata rows exist
            metadata_rows = {
                "datatype": [],
                "nullable": [],
                "default": []
            }

            # Look for metadata rows by checking row headers
            for row in all_values[1:4]:  # Check first few rows for metadata
                if not row:
                    continue
                first_cell = row[0].lower().strip()
                if first_cell in metadata_rows:
                    metadata_rows[first_cell] = row[1:]
                    continue
                break  # Stop when we hit data rows

            # Determine data start row
            data_start = 1
            for key, values in metadata_rows.items():
                if values:
                    data_start += 1

            # Get sample data row for type inference
            sample_row = all_values[data_start] if len(all_values) > data_start else None

            # Build column definitions
            columns = []
            for i, header in enumerate(headers[1:], 1):  # Skip first column if it's row headers
                if not header.strip():
                    continue

                column = {"name": header.strip()}

                # Set datatype
                if metadata_rows["datatype"]:
                    column["datatype"] = metadata_rows["datatype"][i-1].strip().upper() or "TEXT"
                else:
                    # Infer from sample data
                    sample_value = sample_row[i] if sample_row and i < len(sample_row) else None
                    column["datatype"] = self._infer_sql_type(sample_value)

                # Set nullable
                if metadata_rows["nullable"]:
                    column["nullable"] = metadata_rows["nullable"][i-1].lower().strip() in ('true', 'yes', '1')
                else:
                    column["nullable"] = True

                # Set default
                if metadata_rows["default"]:
                    default_val = metadata_rows["default"][i-1].strip()
                    column["default"] = None if default_val.lower() == 'null' else default_val
                else:
                    column["default"] = None

                columns.append(column)

            return {
                "table_name": table_name,
                "columns": columns
            }

        except gspread.exceptions.WorksheetNotFound:
            raise SheetNotFoundError(f"Worksheet '{table_name}' not found")
        except Exception as e:
            raise SheetSchemaError(f"Error parsing schema for '{table_name}': {str(e)}")

    def get_table_data(self, table_name: str) -> List[Dict]:
        """Get the actual data from the table, excluding metadata rows.
        
        Args:
            table_name (str): Name of the worksheet
            
        Returns:
            List[Dict]: List of dictionaries containing the table data
        """
        schema = self.get_table_schema(table_name)
        worksheet = self.spreadsheet.worksheet(table_name)
        
        # Determine number of metadata rows (datatype, nullable, default)
        all_values = worksheet.get_all_values()
        data_start = 1  # Start after header row
        metadata_markers = {'datatype', 'nullable', 'default'}
        
        # Skip metadata rows if present
        while (data_start < len(all_values) and 
               all_values[data_start][0].lower().strip() in metadata_markers):
            data_start += 1
        
        # Get data using column names from schema
        column_names = [col["name"] for col in schema["columns"]]
        data = []
        
        for row in all_values[data_start:]:
            if len(row) < len(column_names):
                row.extend([''] * (len(column_names) - len(row)))
            data.append(dict(zip(column_names, row)))
            
        return data