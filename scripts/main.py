#!/usr/bin/env python3
"""
Main orchestration script for SheetSQL schema sync.
"""

import os
import sys
import logging
import argparse
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from sheets_client import SheetsClient, SheetError
from schema_catalog import SchemaCatalog, SchemaDiff
from llm_sql_generator import LLMSqlGenerator, SqlGenerationError
from sql_writer import write_sql_files
from git_ops import GitOps, GitError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SyncError(Exception):
    """Base exception for sync operations."""
    pass

def load_environment() -> Dict[str, str]:
    """Load and validate required environment variables.
    
    Returns:
        Dict[str, str]: Environment variables
        
    Raises:
        SyncError: If required variables are missing
    """
    load_dotenv()
    
    required_vars = {
        'GOOGLE_CREDENTIALS_FILE': 'Path to Google credentials JSON',
        'SHEET_ID': 'Google Sheet ID to sync',
        'GITHUB_TOKEN': 'GitHub personal access token',
        'GITHUB_REPO': 'GitHub repository (owner/repo)',
        'LOCAL_REPO_PATH': 'Local repository path'
    }
    
    missing = []
    env_vars = {}
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"{var} ({description})")
        env_vars[var] = value
    
    if missing:
        raise SyncError(
            "Missing required environment variables:\n" +
            "\n".join(f"- {var}" for var in missing)
        )
    
    return env_vars

def format_summary(
    diff: SchemaDiff,
    pr_url: Optional[str] = None,
    sql_files: Optional[List[str]] = None
) -> str:
    """Format a nice summary of the sync operation.
    
    Args:
        diff: Schema differences
        pr_url: URL of created pull request
        sql_files: List of SQL files written
        
    Returns:
        str: Formatted summary
    """
    console = Console()
    
    # Create summary table
    summary = Table(title="Schema Sync Summary")
    summary.add_column("Category", style="cyan")
    summary.add_column("Details", style="green")
    
    # Add tables created
    if diff.added_tables:
        summary.add_row(
            "Tables Created",
            "\n".join(f"• {table}" for table in diff.added_tables)
        )
    
    # Add tables modified
    if diff.changed_tables:
        modified = []
        for table, changes in diff.changed_tables.items():
            details = []
            if changes['added']:
                details.append(f"Added columns: {', '.join(c['name'] for c in changes['added'])}")
            if changes['modified']:
                details.append(f"Modified columns: {', '.join(c['name'] for c in changes['modified'])}")
            if details:
                modified.append(f"• {table}:\n  " + "\n  ".join(details))
        
        if modified:
            summary.add_row("Tables Modified", "\n".join(modified))
    
    # Add SQL files
    if sql_files:
        summary.add_row(
            "SQL Files",
            "\n".join(f"• {Path(f).name}" for f in sql_files)
        )
    
    # Add PR information
    if pr_url:
        summary.add_row("Pull Request", f"• {pr_url}")
    
    return console.render_str(summary)

async def main(dry_run: bool = False, force: bool = False):
    """Main sync orchestration.
    
    Args:
        dry_run: If True, only show diff and SQL
        force: If True, create branch even without changes
    """
    try:
        # 1. Load environment
        logger.info("Loading environment variables...")
        env = load_environment()
        
        # 2. Initialize clients
        logger.info("Initializing clients...")
        sheets_client = SheetsClient(
            env['GOOGLE_CREDENTIALS_FILE'],
            env['SHEET_ID']
        )
        
        sql_generator = LLMSqlGenerator()
        schema_catalog = SchemaCatalog()
        
        if not dry_run:
            git_ops = GitOps(
                f"https://github.com/{env['GITHUB_REPO']}.git",
                env['LOCAL_REPO_PATH'],
                repo_name=env['GITHUB_REPO']
            )
        
        # 3. Get schemas from sheets
        logger.info("Reading schemas from Google Sheets...")
        tables = sheets_client.list_tables()
        new_schemas = {}
        
        for table in tables:
            schema = sheets_client.get_table_schema(table)
            new_schemas[schema['table_name']] = schema
        
        # 4. Load existing schema and compute diff
        logger.info("Computing schema differences...")
        old_schema = schema_catalog.load().get('schemas', {})
        diff = schema_catalog.diff(old_schema, new_schemas)
        
        if not diff.has_changes() and not force:
            logger.info("No schema changes detected.")
            print(format_summary(diff))
            return
        
        # 5. Generate SQL for changes
        logger.info("Generating SQL statements...")
        sql_map = {}
        
        # Handle new tables
        for table in diff.added_tables:
            sql = await sql_generator.generate_sql_for_table(
                table,
                new_schemas[table]['columns']
            )
            sql_map[table] = sql
        
        # Handle modified tables
        for table, changes in diff.changed_tables.items():
            if changes['added'] or changes['modified']:
                sql = await sql_generator.generate_sql_for_table(
                    table,
                    new_schemas[table]['columns'],
                    old_schema.get(table, {}).get('columns', [])
                )
                sql_map[table] = sql
        
        if dry_run:
            logger.info("Dry run - showing SQL only")
            for table, sql in sql_map.items():
                print(f"\n--- {table} ---\n{sql}")
            print("\n" + format_summary(diff))
            return
        
        # 6. Write SQL files
        logger.info("Writing SQL files...")
        sql_files = write_sql_files(sql_map)
        
        # 7. Git operations
        logger.info("Performing Git operations...")
        git_ops.clone_or_update_repo()
        
        branch_name = git_ops.create_timestamped_branch('schema-update')
        git_ops.add_and_commit(sql_files, "Update database schema")
        git_ops.push_branch(branch_name)
        
        # Create PR
        pr_url = git_ops.create_pull_request(
            branch_name,
            "Update Database Schema",
            f"Schema updates:\n\n{format_summary(diff)}"
        )
        
        # 8. Update schema catalog
        logger.info("Updating schema catalog...")
        schema_catalog.save(new_schemas)
        
        # 9. Print summary
        print("\n" + format_summary(diff, pr_url, sql_files))
        
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database schema sync from Google Sheets")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show diff and SQL without making changes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Create branch even if no changes detected"
    )
    
    args = parser.parse_args()
    
    import asyncio
    asyncio.run(main(args.dry_run, args.force))