"""Unit tests for LLM SQL generator."""

import pytest
from scripts.llm_sql_generator import LLMSqlGenerator, SqlGenerationError
import asyncio

@pytest.fixture
def sql_generator():
    """Fixture providing an LLMSqlGenerator instance."""
    return LLMSqlGenerator()

@pytest.mark.asyncio
async def test_create_table(sql_generator):
    """Test generating CREATE TABLE statement."""
    sheet_columns = [
        {
            "name": "id",
            "datatype": "INTEGER",
            "nullable": False,
            "default": None
        },
        {
            "name": "email",
            "datatype": "VARCHAR",
            "nullable": False,
            "default": None
        },
        {
            "name": "created_at",
            "datatype": None,  # Test type inference
            "nullable": True,
            "default": None
        }
    ]
    
    sql = await sql_generator.generate_sql_for_table("users", sheet_columns)
    
    # Basic validation
    assert sql.strip().startswith("CREATE TABLE")
    assert "users" in sql
    assert "id" in sql
    assert "email" in sql
    assert "created_at" in sql
    assert "PRIMARY KEY" in sql.upper()
    assert "NOT NULL" in sql.upper()

@pytest.mark.asyncio
async def test_alter_table(sql_generator):
    """Test generating ALTER TABLE statements."""
    existing_columns = [
        {
            "name": "id",
            "datatype": "INTEGER",
            "nullable": False
        }
    ]
    
    new_columns = [
        {
            "name": "id",
            "datatype": "INTEGER",
            "nullable": False
        },
        {
            "name": "email",
            "datatype": "VARCHAR",
            "nullable": False
        }
    ]
    
    sql = await sql_generator.generate_sql_for_table(
        "users",
        new_columns,
        existing_columns
    )
    
    # Basic validation
    assert sql.strip().startswith("ALTER TABLE")
    assert "ADD COLUMN" in sql.upper()
    assert "email" in sql
    assert "id" not in sql  # Shouldn't add existing column

@pytest.mark.asyncio
async def test_type_inference(sql_generator):
    """Test datatype inference for columns without specified types."""
    sheet_columns = [
        {
            "name": "user_id",
            "datatype": None,
            "nullable": False
        },
        {
            "name": "full_name",
            "datatype": None,
            "nullable": True
        },
        {
            "name": "description",
            "datatype": None,
            "nullable": True
        },
        {
            "name": "updated_at",
            "datatype": None,
            "nullable": True
        }
    ]
    
    sql = await sql_generator.generate_sql_for_table("users", sheet_columns)
    
    # Check inferred types
    assert "INT" in sql.upper()  # for user_id
    assert "VARCHAR" in sql.upper()  # for full_name
    assert "TEXT" in sql.upper()  # for description
    assert "DATETIME" in sql.upper()  # for updated_at

@pytest.mark.asyncio
async def test_error_handling(sql_generator):
    """Test error handling with invalid input."""
    with pytest.raises(SqlGenerationError):
        await sql_generator.generate_sql_for_table("users", [])

def test_sync_wrapper(sql_generator):
    """Test synchronous wrapper method."""
    sheet_columns = [
        {
            "name": "id",
            "datatype": "INTEGER",
            "nullable": False
        }
    ]
    
    sql = sql_generator.generate_sql_for_table_sync("users", sheet_columns)
    assert "CREATE TABLE" in sql.upper()
    assert "id" in sql

@pytest.mark.asyncio
async def test_sql_extraction(sql_generator):
    """Test SQL extraction from LLM response."""
    # This test might need to be adjusted based on actual LLM response format
    sheet_columns = [{"name": "id", "datatype": "INTEGER"}]
    sql = await sql_generator.generate_sql_for_table("test", sheet_columns)
    
    # Basic validation
    assert "```" not in sql
    assert sql.strip()
    assert ";" in sql