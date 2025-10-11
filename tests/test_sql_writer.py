"""Unit tests for SQL file writer."""

import pytest
import os
import glob
from scripts.sql_writer import write_sql_files
import time
from datetime import datetime

@pytest.fixture
def temp_sql_dir(tmp_path):
    """Fixture providing a temporary directory for SQL files."""
    sql_dir = tmp_path / "sql_files"
    sql_dir.mkdir()
    return str(sql_dir)

@pytest.fixture
def sample_sql_map():
    """Fixture providing sample SQL statements."""
    return {
        "customers": "CREATE TABLE customers (\n  id INT PRIMARY KEY\n);",
        "orders": "ALTER TABLE orders ADD COLUMN status VARCHAR(255);"
    }

def test_write_new_files(temp_sql_dir, sample_sql_map):
    """Test writing SQL files when they don't exist."""
    written_files = write_sql_files(sample_sql_map, temp_sql_dir)
    
    assert len(written_files) == 2
    
    # Check file contents
    for table, sql in sample_sql_map.items():
        file_path = os.path.join(temp_sql_dir, f"{table}.sql")
        assert os.path.exists(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert content.strip() == sql.strip()

def test_backup_creation(temp_sql_dir):
    """Test backup creation when overwriting existing files."""
    # First write
    sql_map = {"test": "CREATE TABLE test (id INT);"}
    write_sql_files(sql_map, temp_sql_dir)
    
    # Sleep briefly to ensure different timestamp
    time.sleep(1)
    
    # Second write should create backup
    sql_map = {"test": "ALTER TABLE test ADD COLUMN name TEXT;"}
    write_sql_files(sql_map, temp_sql_dir)
    
    # Check for backup file
    backups = glob.glob(os.path.join(temp_sql_dir, "test.sql.bak.*"))
    assert len(backups) == 1
    
    # Verify backup contains original content
    with open(backups[0], 'r', encoding='utf-8') as f:
        backup_content = f.read()
        assert "CREATE TABLE test" in backup_content

def test_empty_sql_handling(temp_sql_dir):
    """Test handling of empty SQL statements."""
    sql_map = {
        "valid": "CREATE TABLE valid (id INT);",
        "empty": "",
        "whitespace": "   \n   "
    }
    
    written_files = write_sql_files(sql_map, temp_sql_dir)
    
    # Should only write the valid SQL file
    assert len(written_files) == 1
    assert os.path.basename(written_files[0]) == "valid.sql"

def test_newline_handling(temp_sql_dir):
    """Test handling of newlines in SQL content."""
    sql_map = {
        "test": "CREATE TABLE test (\n  id INT\n);"
    }
    
    write_sql_files(sql_map, temp_sql_dir)
    file_path = os.path.join(temp_sql_dir, "test.sql")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Should have content and end with exactly one newline
        assert content.strip() == sql_map["test"].strip()
        assert content.endswith('\n')
        assert not content.endswith('\n\n')

def test_multiple_writes(temp_sql_dir):
    """Test multiple writes to the same file create sequential backups."""
    sql_map = {"test": "Version 1"}
    write_sql_files(sql_map, temp_sql_dir)
    
    time.sleep(1)
    sql_map = {"test": "Version 2"}
    write_sql_files(sql_map, temp_sql_dir)
    
    time.sleep(1)
    sql_map = {"test": "Version 3"}
    write_sql_files(sql_map, temp_sql_dir)
    
    # Check number of backups
    backups = glob.glob(os.path.join(temp_sql_dir, "test.sql.bak.*"))
    assert len(backups) == 2  # Should have backups of versions 1 and 2
    
    # Verify current version
    with open(os.path.join(temp_sql_dir, "test.sql"), 'r') as f:
        assert f.read().strip() == "Version 3"