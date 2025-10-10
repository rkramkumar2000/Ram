"""Unit tests for schema catalog functionality."""

import pytest
import os
import json
from scripts.schema_catalog import SchemaCatalog, SchemaDiff

@pytest.fixture
def temp_catalog(tmp_path):
    """Fixture providing a temporary catalog file."""
    catalog_path = tmp_path / "test_catalog.json"
    return str(catalog_path)

@pytest.fixture
def sample_schema():
    """Fixture providing a sample schema for testing."""
    return {
        "users": {
            "columns": [
                {
                    "name": "id",
                    "datatype": "INTEGER",
                    "nullable": False,
                    "default": None,
                    "primary": True
                },
                {
                    "name": "email",
                    "datatype": "TEXT",
                    "nullable": False,
                    "default": None,
                    "primary": False
                }
            ]
        }
    }

def test_catalog_initialization(temp_catalog):
    """Test catalog initialization and directory creation."""
    catalog = SchemaCatalog(temp_catalog)
    assert os.path.exists(os.path.dirname(temp_catalog))

def test_save_and_load(temp_catalog, sample_schema):
    """Test saving and loading schema catalog."""
    catalog = SchemaCatalog(temp_catalog)
    
    # Save schema
    catalog.save(sample_schema)
    assert os.path.exists(temp_catalog)
    
    # Load schema
    loaded = catalog.load()
    assert 'version' in loaded
    assert 'schemas' in loaded
    assert loaded['schemas'] == sample_schema

def test_empty_catalog_load(temp_catalog):
    """Test loading non-existent catalog."""
    catalog = SchemaCatalog(temp_catalog)
    assert catalog.load() == {}

def test_diff_added_table(temp_catalog):
    """Test diffing when adding a new table."""
    old_schema = {}
    new_schema = {
        "users": {
            "columns": [
                {
                    "name": "id",
                    "datatype": "INTEGER",
                    "nullable": False,
                    "primary": True
                }
            ]
        }
    }
    
    catalog = SchemaCatalog(temp_catalog)
    diff = catalog.diff(old_schema, new_schema)
    
    assert diff.added_tables == ["users"]
    assert diff.removed_tables == []
    assert diff.changed_tables == {}

def test_diff_changed_table(temp_catalog):
    """Test diffing when modifying a table."""
    old_schema = {
        "users": {
            "columns": [
                {
                    "name": "id",
                    "datatype": "INTEGER",
                    "nullable": False,
                    "primary": True
                }
            ]
        }
    }
    
    new_schema = {
        "users": {
            "columns": [
                {
                    "name": "id",
                    "datatype": "INTEGER",
                    "nullable": False,
                    "primary": True
                },
                {
                    "name": "email",
                    "datatype": "TEXT",
                    "nullable": False,
                    "primary": False
                }
            ]
        }
    }
    
    catalog = SchemaCatalog(temp_catalog)
    diff = catalog.diff(old_schema, new_schema)
    
    assert not diff.added_tables
    assert not diff.removed_tables
    assert "users" in diff.changed_tables
    assert len(diff.changed_tables["users"]["added"]) == 1
    assert diff.changed_tables["users"]["added"][0]["name"] == "email"

def test_safe_mode_diff(temp_catalog):
    """Test diffing in safe mode (only additions)."""
    old_schema = {
        "users": {
            "columns": [
                {"name": "id", "datatype": "INTEGER"},
                {"name": "to_remove", "datatype": "TEXT"}
            ]
        }
    }
    
    new_schema = {
        "users": {
            "columns": [
                {"name": "id", "datatype": "INTEGER"},
                {"name": "new_col", "datatype": "TEXT"}
            ]
        }
    }
    
    catalog = SchemaCatalog(temp_catalog)
    
    # Test in safe mode
    safe_diff = catalog.diff(old_schema, new_schema, safe_mode=True)
    assert not safe_diff.removed_tables
    assert len(safe_diff.changed_tables["users"]["removed"]) == 0
    assert len(safe_diff.changed_tables["users"]["added"]) == 1
    
    # Test with safe mode off
    unsafe_diff = catalog.diff(old_schema, new_schema, safe_mode=False)
    assert len(unsafe_diff.changed_tables["users"]["removed"]) == 1
    assert len(unsafe_diff.changed_tables["users"]["added"]) == 1

def test_modified_column_detection(temp_catalog):
    """Test detection of modified columns."""
    old_schema = {
        "users": {
            "columns": [
                {
                    "name": "id",
                    "datatype": "INTEGER",
                    "nullable": False
                }
            ]
        }
    }
    
    new_schema = {
        "users": {
            "columns": [
                {
                    "name": "id",
                    "datatype": "BIGINT",  # Changed datatype
                    "nullable": False
                }
            ]
        }
    }
    
    catalog = SchemaCatalog(temp_catalog)
    diff = catalog.diff(old_schema, new_schema)
    
    assert "users" in diff.changed_tables
    assert len(diff.changed_tables["users"]["modified"]) == 1
    modified = diff.changed_tables["users"]["modified"][0]
    assert modified["name"] == "id"
    assert modified["old"]["datatype"] == "INTEGER"
    assert modified["new"]["datatype"] == "BIGINT"