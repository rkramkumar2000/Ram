"""Test suite for SQL generation functionality."""

import pytest
from scripts.generate_sql import generate_create_table, generate_insert_statements
from scripts.sheets_client import SheetsClient
from scripts.llm_sql import LLMSQLHelper
from scripts.git_ops import GitOps

def test_generate_create_table():
    """Test CREATE TABLE statement generation."""
    columns = [
        {'name': 'id', 'type': int},
        {'name': 'name', 'type': str},
        {'name': 'active', 'type': bool}
    ]
    sql = generate_create_table('test_table', columns)
    assert 'CREATE TABLE' in sql
    assert 'test_table' in sql
    assert 'id INTEGER' in sql
    assert 'name TEXT' in sql
    assert 'active BOOLEAN' in sql

def test_generate_insert_statements():
    """Test INSERT statement generation."""
    data = [
        {'id': 1, 'name': 'Test', 'active': True},
        {'id': 2, 'name': 'Test2', 'active': False}
    ]
    statements = generate_insert_statements('test_table', data)
    assert len(statements) == 2
    assert all('INSERT INTO test_table' in stmt for stmt in statements)

# Add more tests for sheets_client.py, llm_sql.py, and git_ops.py