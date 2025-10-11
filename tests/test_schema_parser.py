"""Unit tests for schema parsing functionality."""

import pytest
from scripts.schema_parser import parse_rows_to_schema, normalize_datatype, normalize_bool

def test_empty_rows():
    """Test handling of empty input."""
    with pytest.raises(ValueError):
        parse_rows_to_schema([], "test_table")

def test_simple_format():
    """Test parsing of simple format with only column names."""
    rows = [
        ["id", "name", "email"]
    ]
    schema = parse_rows_to_schema(rows, "users")
    
    assert schema["table_name"] == "users"
    assert len(schema["columns"]) == 3
    
    # Check id column is marked as primary
    assert schema["columns"][0] == {
        "name": "id",
        "datatype": None,
        "nullable": True,
        "default": None,
        "primary": True
    }
    
    # Check regular column
    assert schema["columns"][1] == {
        "name": "name",
        "datatype": None,
        "nullable": True,
        "default": None,
        "primary": False
    }

def test_extended_format():
    """Test parsing of extended format with metadata rows."""
    rows = [
        ["id", "name", "email", "active"],
        ["datatype", "INTEGER", "TEXT", "VARCHAR(255)", "BOOLEAN"],
        ["nullable", "NO", "YES", "NO", "true"],
        ["default", "null", "John Doe", "null", "true"]
    ]
    schema = parse_rows_to_schema(rows, "users")
    
    assert schema["table_name"] == "users"
    assert len(schema["columns"]) == 4
    
    # Check id column
    assert schema["columns"][0] == {
        "name": "id",
        "datatype": "INTEGER",
        "nullable": False,
        "default": None,
        "primary": True
    }
    
    # Check name column
    assert schema["columns"][1] == {
        "name": "name",
        "datatype": "TEXT",
        "nullable": True,
        "default": "John Doe",
        "primary": False
    }
    
    # Check email column
    assert schema["columns"][2] == {
        "name": "email",
        "datatype": "TEXT",  # VARCHAR normalized to TEXT
        "nullable": False,
        "default": None,
        "primary": False
    }

def test_datatype_normalization():
    """Test normalization of various SQL datatypes."""
    test_cases = [
        ("INT", "INTEGER"),
        ("VARCHAR(255)", "TEXT"),
        ("CHAR(10)", "TEXT"),
        ("TEXT", "TEXT"),
        ("BOOL", "BOOLEAN"),
        ("DATETIME", "TIMESTAMP"),
        ("invalid_type", None),
        (None, None),
        ("", None)
    ]
    
    for input_type, expected in test_cases:
        assert normalize_datatype(input_type) == expected

def test_boolean_normalization():
    """Test normalization of various boolean representations."""
    true_values = ["YES", "yes", "True", "true", "1", "Y"]
    false_values = ["NO", "no", "False", "false", "0", "N", "", None]
    
    for value in true_values:
        assert normalize_bool(value) is True
        
    for value in false_values:
        assert normalize_bool(value) is False

def test_partial_metadata():
    """Test handling of partial metadata rows."""
    rows = [
        ["id", "name", "email"],
        ["datatype", "INTEGER", "TEXT", "VARCHAR(255)"],
        ["nullable", "NO", "YES"]  # Missing one value
    ]
    schema = parse_rows_to_schema(rows, "users")
    
    assert len(schema["columns"]) == 3
    assert schema["columns"][2]["nullable"] is True  # Default when missing

def test_whitespace_handling():
    """Test handling of whitespace in input."""
    rows = [
        [" id ", " name ", " email "],
        [" datatype ", " INTEGER ", " TEXT ", " VARCHAR "],
        ["nullable", " NO ", " YES ", " NO "]
    ]
    schema = parse_rows_to_schema(rows, "users")
    
    assert schema["columns"][0]["name"] == "id"
    assert schema["columns"][1]["name"] == "name"
    assert schema["columns"][2]["name"] == "email"