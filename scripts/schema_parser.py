"""Schema parsing utilities for SheetSQL."""

from typing import List, Dict, Any, Optional
import re

def normalize_bool(value: str) -> bool:
    """Normalize various string boolean representations to Python bool.
    
    Args:
        value (str): String value to normalize
        
    Returns:
        bool: Normalized boolean value
    """
    if not value or value.lower().strip() in ('no', 'false', '0', 'null', 'n', ''):
        return False
    return True

def normalize_datatype(datatype: Optional[str]) -> Optional[str]:
    """Normalize SQL datatype strings.
    
    Args:
        datatype (Optional[str]): Raw datatype string
        
    Returns:
        Optional[str]: Normalized datatype or None if invalid
    """
    if not datatype:
        return None
        
    # Strip size parameters and normalize case
    base_type = re.sub(r'\(.*\)', '', datatype).strip().upper()
    
    # Common type mappings
    type_mappings = {
        'INTEGER': 'INTEGER',
        'INT': 'INTEGER',
        'BIGINT': 'BIGINT',
        'SMALLINT': 'SMALLINT',
        'TEXT': 'TEXT',
        'VARCHAR': 'TEXT',
        'CHAR': 'TEXT',
        'STRING': 'TEXT',
        'FLOAT': 'FLOAT',
        'DOUBLE': 'FLOAT',
        'DECIMAL': 'DECIMAL',
        'NUMERIC': 'DECIMAL',
        'BOOLEAN': 'BOOLEAN',
        'BOOL': 'BOOLEAN',
        'DATE': 'DATE',
        'TIMESTAMP': 'TIMESTAMP',
        'DATETIME': 'TIMESTAMP'
    }
    
    return type_mappings.get(base_type, None)

def parse_rows_to_schema(rows: List[List[str]], table_name: str) -> Dict[str, Any]:
    """Parse sheet rows into a structured schema definition.
    
    This function handles two formats:
    1. Simple format with just column names in the header row
    2. Extended format with metadata rows (datatype, nullable, default)
    
    Args:
        rows (List[List[str]]): List of rows from the sheet, where first row contains headers
        table_name (str): Name of the table to use in schema
        
    Returns:
        Dict[str, Any]: Schema definition in the format:
        {
            "table_name": str,
            "columns": [
                {
                    "name": str,
                    "datatype": Optional[str],
                    "nullable": bool,
                    "default": Optional[str],
                    "primary": bool
                },
                ...
            ]
        }
        
    Raises:
        ValueError: If rows list is empty or first row has no columns
    """
    if not rows or not rows[0]:
        raise ValueError("Empty rows list or no columns in header row")
    
    # Extract header row
    headers = [h.strip() for h in rows[0] if h.strip()]
    
    # Initialize schema
    schema = {
        "table_name": table_name,
        "columns": []
    }
    
    # Check if we have metadata rows
    has_metadata = False
    metadata_map = {}
    
    # Look for metadata rows (checking first cell of each row)
    for row in rows[1:4]:  # Check up to 3 rows after header
        if not row:
            continue
        marker = row[0].lower().strip()
        if marker in ('datatype', 'type', 'data type'):
            metadata_map['datatype'] = row[1:]
            has_metadata = True
        elif marker in ('nullable', 'null'):
            metadata_map['nullable'] = row[1:]
            has_metadata = True
        elif marker in ('default'):
            metadata_map['default'] = row[1:]
            has_metadata = True
    
    # Process each column
    for idx, name in enumerate(headers):
        column = {"name": name, "primary": name.lower() == 'id'}  # Simple primary key inference
        
        if has_metadata:
            # Get datatype if present
            if 'datatype' in metadata_map and idx < len(metadata_map['datatype']):
                raw_type = metadata_map['datatype'][idx].strip()
                column["datatype"] = normalize_datatype(raw_type)
            else:
                column["datatype"] = None
                
            # Get nullable if present
            if 'nullable' in metadata_map and idx < len(metadata_map['nullable']):
                column["nullable"] = normalize_bool(metadata_map['nullable'][idx])
            else:
                column["nullable"] = True
                
            # Get default if present
            if 'default' in metadata_map and idx < len(metadata_map['default']):
                default_val = metadata_map['default'][idx].strip()
                column["default"] = None if default_val.lower() == 'null' else default_val
            else:
                column["default"] = None
        else:
            # Simple format - set defaults
            column["datatype"] = None
            column["nullable"] = True
            column["default"] = None
        
        schema["columns"].append(column)
    
    return schema