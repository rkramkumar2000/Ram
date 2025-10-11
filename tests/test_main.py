"""Unit tests for main orchestration script."""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from scripts.main import load_environment, format_summary, main
from scripts.schema_catalog import SchemaDiff

@pytest.fixture
def mock_env(monkeypatch):
    """Fixture providing mock environment variables."""
    env_vars = {
        'GOOGLE_CREDENTIALS_FILE': '/path/to/credentials.json',
        'SHEET_ID': 'test-sheet-id',
        'GITHUB_TOKEN': 'test-token',
        'GITHUB_REPO': 'test/repo',
        'LOCAL_REPO_PATH': '/path/to/repo'
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars

def test_load_environment_success(mock_env):
    """Test successful environment loading."""
    env = load_environment()
    assert env['GOOGLE_CREDENTIALS_FILE'] == '/path/to/credentials.json'
    assert env['SHEET_ID'] == 'test-sheet-id'
    assert env['GITHUB_TOKEN'] == 'test-token'

def test_load_environment_missing_vars(monkeypatch):
    """Test environment loading with missing variables."""
    monkeypatch.delenv('GOOGLE_CREDENTIALS_FILE', raising=False)
    
    with pytest.raises(Exception) as exc_info:
        load_environment()
    assert 'GOOGLE_CREDENTIALS_FILE' in str(exc_info.value)

def test_format_summary():
    """Test summary formatting."""
    diff = SchemaDiff(
        added_tables=['customers'],
        removed_tables=[],
        changed_tables={
            'orders': {
                'added': [{'name': 'status'}],
                'removed': [],
                'modified': [{'name': 'total'}]
            }
        }
    )
    
    summary = format_summary(
        diff,
        'https://github.com/test/repo/pull/1',
        ['sql_files/customers.sql', 'sql_files/orders.sql']
    )
    
    assert 'customers' in summary
    assert 'orders' in summary
    assert 'status' in summary
    assert 'total' in summary
    assert 'https://github.com/test/repo/pull/1' in summary

@pytest.mark.asyncio
async def test_main_no_changes():
    """Test main function with no changes."""
    with patch('scripts.main.load_environment') as mock_load_env, \
         patch('scripts.sheets_client.SheetsClient') as MockSheets, \
         patch('scripts.schema_catalog.SchemaCatalog') as MockCatalog:
        
        # Mock environment
        mock_load_env.return_value = {
            'GOOGLE_CREDENTIALS_FILE': 'creds.json',
            'SHEET_ID': 'sheet-id',
            'GITHUB_TOKEN': 'token',
            'GITHUB_REPO': 'test/repo',
            'LOCAL_REPO_PATH': '/path/to/repo'
        }
        
        # Mock sheets client
        mock_sheets = MockSheets.return_value
        mock_sheets.list_tables.return_value = ['users']
        mock_sheets.get_table_schema.return_value = {
            'table_name': 'users',
            'columns': []
        }
        
        # Mock catalog with no changes
        mock_catalog = MockCatalog.return_value
        mock_catalog.load.return_value = {'schemas': {'users': {'columns': []}}}
        mock_catalog.diff.return_value = SchemaDiff([], [], {})
        
        # Run main
        await main(dry_run=True)
        
        # Verify no SQL generation was attempted
        mock_sheets.list_tables.assert_called_once()
        mock_catalog.diff.assert_called_once()

@pytest.mark.asyncio
async def test_main_with_changes():
    """Test main function with schema changes."""
    with patch('scripts.main.load_environment') as mock_load_env, \
         patch('scripts.sheets_client.SheetsClient') as MockSheets, \
         patch('scripts.schema_catalog.SchemaCatalog') as MockCatalog, \
         patch('scripts.llm_sql_generator.LLMSqlGenerator') as MockSQL, \
         patch('scripts.git_ops.GitOps') as MockGit, \
         patch('scripts.main.write_sql_files') as mock_write_sql:
        
        # Mock environment
        mock_load_env.return_value = {
            'GOOGLE_CREDENTIALS_FILE': 'creds.json',
            'SHEET_ID': 'sheet-id',
            'GITHUB_TOKEN': 'token',
            'GITHUB_REPO': 'test/repo',
            'LOCAL_REPO_PATH': '/path/to/repo'
        }
        
        # Mock sheets client
        mock_sheets = MockSheets.return_value
        mock_sheets.list_tables.return_value = ['users']
        mock_sheets.get_table_schema.return_value = {
            'table_name': 'users',
            'columns': [{'name': 'id', 'type': 'INT'}]
        }
        
        # Mock catalog with changes
        mock_catalog = MockCatalog.return_value
        mock_catalog.load.return_value = {'schemas': {}}
        mock_catalog.diff.return_value = SchemaDiff(
            ['users'],
            [],
            {}
        )
        
        # Mock SQL generator
        mock_sql = MockSQL.return_value
        mock_sql.generate_sql_for_table = AsyncMock(
            return_value="CREATE TABLE users (id INT);"
        )
        
        # Mock Git operations
        mock_git = MockGit.return_value
        mock_git.create_pull_request.return_value = "https://github.com/test/repo/pull/1"
        
        # Mock SQL file writing
        mock_write_sql.return_value = ['sql_files/users.sql']
        
        # Run main
        await main()
        
        # Verify workflow
        mock_sheets.list_tables.assert_called_once()
        mock_sql.generate_sql_for_table.assert_called_once()
        mock_write_sql.assert_called_once()
        mock_catalog.save.assert_called_once()
        mock_git.create_pull_request.assert_called_once()

@pytest.mark.asyncio
async def test_main_dry_run():
    """Test main function in dry-run mode."""
    with patch('scripts.main.load_environment') as mock_load_env, \
         patch('scripts.sheets_client.SheetsClient') as MockSheets, \
         patch('scripts.schema_catalog.SchemaCatalog') as MockCatalog, \
         patch('scripts.llm_sql_generator.LLMSqlGenerator') as MockSQL, \
         patch('scripts.git_ops.GitOps') as MockGit:
        
        # Mock environment
        mock_load_env.return_value = {
            'GOOGLE_CREDENTIALS_FILE': 'creds.json',
            'SHEET_ID': 'sheet-id',
            'GITHUB_TOKEN': 'token',
            'GITHUB_REPO': 'test/repo',
            'LOCAL_REPO_PATH': '/path/to/repo'
        }
        
        # Mock sheets client
        mock_sheets = MockSheets.return_value
        mock_sheets.list_tables.return_value = ['users']
        mock_sheets.get_table_schema.return_value = {
            'table_name': 'users',
            'columns': [{'name': 'id', 'type': 'INT'}]
        }
        
        # Mock catalog with changes
        mock_catalog = MockCatalog.return_value
        mock_catalog.load.return_value = {'schemas': {}}
        mock_catalog.diff.return_value = SchemaDiff(
            ['users'],
            [],
            {}
        )
        
        # Mock SQL generator
        mock_sql = MockSQL.return_value
        mock_sql.generate_sql_for_table = AsyncMock(
            return_value="CREATE TABLE users (id INT);"
        )
        
        # Run main in dry-run mode
        await main(dry_run=True)
        
        # Verify no Git operations were performed
        MockGit.assert_not_called()
        mock_catalog.save.assert_not_called()