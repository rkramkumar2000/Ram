"""Unit tests for schema parsing, catalog diffing, and LLM prompt generation."""

import pytest
from scripts.schema_parser import parse_rows_to_schema
from scripts.schema_catalog import SchemaCatalog
from scripts.llm_sql_generator import LLMSqlGenerator

def test_parse_rows_to_schema_header_only():
    """Test schema parsing with just header row."""
    rows = [
        ['id', 'name', 'email', 'created_at'],
        []  # Empty data row
    ]
    
    schema = parse_rows_to_schema('users', rows)
    assert schema['table_name'] == 'users'
    assert len(schema['columns']) == 4
    
    # Verify column inference
    columns = {col['name']: col['type'] for col in schema['columns']}
    assert columns['id'] == 'INT'  # Common naming convention
    assert columns['name'] == 'VARCHAR'
    assert columns['email'] == 'VARCHAR'
    assert columns['created_at'] == 'TIMESTAMP'  # Common naming convention

def test_parse_rows_to_schema_with_metadata():
    """Test schema parsing with header and metadata rows."""
    rows = [
        ['id', 'score', 'status', 'updated_at'],
        ['INT', 'DECIMAL(10,2)', 'ENUM', 'TIMESTAMP'],  # Type hints
        ['NOT NULL', 'NULL', "NOT NULL DEFAULT 'pending'", 'NOT NULL'],  # Constraints
        ['Primary Key', '', '', '']  # Additional metadata
    ]
    
    schema = parse_rows_to_schema('orders', rows)
    assert schema['table_name'] == 'orders'
    assert len(schema['columns']) == 4
    
    # Verify detailed column definitions
    columns = {col['name']: col for col in schema['columns']}
    
    assert columns['id']['type'] == 'INT'
    assert columns['id']['nullable'] is False
    assert columns['id']['primary_key'] is True
    
    assert columns['score']['type'] == 'DECIMAL(10,2)'
    assert columns['score']['nullable'] is True
    
    assert columns['status']['type'] == 'ENUM'
    assert columns['status']['nullable'] is False
    assert columns['status']['default'] == "'pending'"
    
    assert columns['updated_at']['type'] == 'TIMESTAMP'
    assert columns['updated_at']['nullable'] is False

def test_catalog_diff():
    """Test schema catalog diffing functionality."""
    old_schemas = {
        'users': {
            'table_name': 'users',
            'columns': [
                {'name': 'id', 'type': 'INT'},
                {'name': 'name', 'type': 'VARCHAR'}
            ]
        }
    }
    
    new_schemas = {
        'users': {
            'table_name': 'users',
            'columns': [
                {'name': 'id', 'type': 'INT'},
                {'name': 'name', 'type': 'VARCHAR'},
                {'name': 'email', 'type': 'VARCHAR'}  # Added column
            ]
        },
        'orders': {  # New table
            'table_name': 'orders',
            'columns': [
                {'name': 'id', 'type': 'INT'},
                {'name': 'user_id', 'type': 'INT'}
            ]
        }
    }
    
    catalog = SchemaCatalog('test_catalog')
    diff = catalog.diff(old_schemas, new_schemas)
    
    # Verify added tables
    assert 'orders' in diff.added_tables
    assert len(diff.added_tables) == 1
    
    # Verify changed tables
    assert 'users' in diff.changed_tables
    user_changes = diff.changed_tables['users']
    assert len(user_changes['added']) == 1
    assert user_changes['added'][0]['name'] == 'email'
    assert len(user_changes['removed']) == 0
    assert len(user_changes['modified']) == 0
    
    # Verify no removed tables
    assert len(diff.removed_tables) == 0

@pytest.mark.asyncio
async def test_llm_sql_prompt_format(monkeypatch):
    """Test LLM prompt generation and SQL extraction."""
    # Mock LLM response
    async def mock_llm_generate(*args, **kwargs):
        return """Here's the SQL to update the table:

```sql
ALTER TABLE users
ADD COLUMN email VARCHAR(255) NOT NULL,
ADD COLUMN status ENUM('active', 'inactive') DEFAULT 'active';
```

This will add the new columns with appropriate constraints."""
    
    # Create test schema changes
    sheet_columns = [
        {'name': 'id', 'type': 'INT', 'nullable': False},
        {'name': 'name', 'type': 'VARCHAR', 'nullable': False},
        {'name': 'email', 'type': 'VARCHAR', 'nullable': False},
        {'name': 'status', 'type': 'ENUM', 'nullable': False, 'default': "'active'"}
    ]
    
    existing_columns = [
        {'name': 'id', 'type': 'INT', 'nullable': False},
        {'name': 'name', 'type': 'VARCHAR', 'nullable': False}
    ]
    
    # Create generator with mocked LLM
    generator = LLMSqlGenerator('fake_api_key')
    monkeypatch.setattr(generator, '_generate_llm_response', mock_llm_generate)
    
    # Generate SQL
    sql = await generator.generate_sql_for_table('users', sheet_columns, existing_columns)
    
    # Verify SQL was extracted correctly
    assert sql.strip().startswith('ALTER TABLE users')
    assert 'ADD COLUMN email' in sql
    assert 'ADD COLUMN status' in sql
    assert sql.strip().endswith(';')
    
    # Verify prompt formatting
    prompt = generator._format_prompt('users', sheet_columns, existing_columns)
    assert 'table name: users' in prompt.lower()
    assert 'existing columns' in prompt.lower()
    assert 'new/updated columns' in prompt.lower()
    assert 'generate sql' in prompt.lower()