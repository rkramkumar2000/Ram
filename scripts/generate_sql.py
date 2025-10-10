#!/usr/bin/env python3
"""
SQL generation module for creating schema and data insertion statements.
"""

import sqlparse
from typing import List, Dict

def generate_create_table(table_name: str, columns: List[Dict]) -> str:
    """Generate CREATE TABLE SQL statement."""
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