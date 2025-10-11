"""Schema catalog management and diffing functionality."""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import click
from rich.console import Console
from rich.table import Table

@dataclass
class SchemaDiff:
    """Schema difference representation."""
    added_tables: List[str]
    removed_tables: List[str]
    changed_tables: Dict[str, Dict[str, List[Dict[str, Any]]]]

    def has_changes(self) -> bool:
        """Check if there are any changes in the diff."""
        return bool(
            self.added_tables or
            self.removed_tables or
            self.changed_tables
        )

class SchemaCatalog:
    """Manages schema versioning and comparison."""

    def __init__(self, catalog_path: str = "sql_files/schema_catalog.json"):
        """Initialize schema catalog.
        
        Args:
            catalog_path (str): Path to the catalog JSON file
        """
        self.catalog_path = catalog_path
        self.catalog: Dict[str, Any] = {}
        self._ensure_catalog_dir()

    def _ensure_catalog_dir(self) -> None:
        """Ensure the catalog directory exists."""
        os.makedirs(os.path.dirname(self.catalog_path), exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """Load schema catalog from file.
        
        Returns:
            Dict[str, Any]: The loaded catalog or empty dict if file doesn't exist
        """
        try:
            if os.path.exists(self.catalog_path):
                with open(self.catalog_path, 'r') as f:
                    self.catalog = json.load(f)
            return self.catalog
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse catalog file: {e}")
            return {}
        except Exception as e:
            print(f"Warning: Error loading catalog: {e}")
            return {}

    def save(self, schema_dict: Dict[str, Any]) -> None:
        """Save schema to catalog with version information.
        
        Args:
            schema_dict (Dict[str, Any]): Schema to save
        """
        current_time = datetime.now().isoformat()
        
        # Add version metadata
        versioned_schema = {
            "version": current_time,
            "schemas": schema_dict
        }
        
        try:
            with open(self.catalog_path, 'w') as f:
                json.dump(versioned_schema, f, indent=2)
            self.catalog = versioned_schema
        except Exception as e:
            raise Exception(f"Failed to save schema catalog: {e}")

    def _compare_columns(self,
                        old_cols: List[Dict[str, Any]],
                        new_cols: List[Dict[str, Any]],
                        safe_mode: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """Compare columns between old and new schema versions.
        
        Args:
            old_cols (List[Dict[str, Any]]): Old column definitions
            new_cols (List[Dict[str, Any]]): New column definitions
            safe_mode (bool): If True, only track added columns
            
        Returns:
            Dict with added and removed columns
        """
        old_col_names = {col['name'] for col in old_cols}
        new_col_names = {col['name'] for col in new_cols}
        
        added = [col for col in new_cols if col['name'] not in old_col_names]
        
        # In safe mode, we don't track removed columns
        removed = [] if safe_mode else [
            col for col in old_cols if col['name'] not in new_col_names
        ]
        
        # Check for column modifications
        modified = []
        for new_col in new_cols:
            for old_col in old_cols:
                if new_col['name'] == old_col['name']:
                    # Compare all attributes except 'name'
                    old_dict = dict(old_col)
                    new_dict = dict(new_col)
                    del old_dict['name']
                    del new_dict['name']
                    if old_dict != new_dict:
                        modified.append({
                            'name': new_col['name'],
                            'old': old_dict,
                            'new': new_dict
                        })
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified
        }

    def diff(self,
            old_schema: Optional[Dict[str, Any]] = None,
            new_schema: Optional[Dict[str, Any]] = None,
            safe_mode: bool = True) -> SchemaDiff:
        """Compare two schema versions and return differences.
        
        Args:
            old_schema (Optional[Dict[str, Any]]): Old schema (uses catalog if None)
            new_schema (Optional[Dict[str, Any]]): New schema to compare
            safe_mode (bool): If True, only track added columns
            
        Returns:
            SchemaDiff: Object containing schema differences
        """
        if old_schema is None:
            old_schema = self.catalog.get('schemas', {})
        if new_schema is None:
            raise ValueError("New schema is required for diff")
            
        old_tables = set(old_schema.keys())
        new_tables = set(new_schema.keys())
        
        added_tables = list(new_tables - old_tables)
        removed_tables = list(old_tables - new_tables) if not safe_mode else []
        
        changed_tables = {}
        for table in old_tables & new_tables:
            old_cols = old_schema[table].get('columns', [])
            new_cols = new_schema[table].get('columns', [])
            
            col_changes = self._compare_columns(old_cols, new_cols, safe_mode)
            if any(col_changes.values()):
                changed_tables[table] = col_changes
        
        return SchemaDiff(
            added_tables=added_tables,
            removed_tables=removed_tables,
            changed_tables=changed_tables
        )

def format_column(col: Dict[str, Any]) -> str:
    """Format column definition for display.
    
    Args:
        col (Dict[str, Any]): Column definition
        
    Returns:
        str: Formatted column string
    """
    parts = [f"{col['name']}"]
    if col.get('datatype'):
        parts.append(col['datatype'])
    if not col.get('nullable', True):
        parts.append('NOT NULL')
    if col.get('default') is not None:
        parts.append(f"DEFAULT {col['default']}")
    if col.get('primary', False):
        parts.append('PRIMARY KEY')
    return ' '.join(parts)

@click.command()
@click.option('--catalog-path', default='sql_files/schema_catalog.json',
              help='Path to schema catalog file')
@click.option('--new-schema', help='Path to new schema JSON file')
@click.option('--safe-mode/--no-safe-mode', default=True,
              help='Only show added columns (safe mode) vs. show all changes')
def show_diff(catalog_path: str, new_schema: str, safe_mode: bool):
    """CLI command to show schema differences."""
    console = Console()
    
    try:
        catalog = SchemaCatalog(catalog_path)
        old_schema = catalog.load().get('schemas', {})
        
        with open(new_schema, 'r') as f:
            new_schema_data = json.load(f)
        
        diff = catalog.diff(old_schema, new_schema_data, safe_mode)
        
        if not diff.has_changes():
            console.print("\n[green]No schema changes detected[/green]\n")
            return
        
        # Show added tables
        if diff.added_tables:
            console.print("\n[green]Added Tables:[/green]")
            for table in diff.added_tables:
                console.print(f"  + {table}")
        
        # Show removed tables
        if diff.removed_tables:
            console.print("\n[red]Removed Tables:[/red]")
            for table in diff.removed_tables:
                console.print(f"  - {table}")
        
        # Show changed tables
        if diff.changed_tables:
            console.print("\n[yellow]Changed Tables:[/yellow]")
            for table, changes in diff.changed_tables.items():
                console.print(f"\n  {table}:")
                
                if changes['added']:
                    console.print("    Added Columns:")
                    for col in changes['added']:
                        console.print(f"      + {format_column(col)}")
                
                if changes['removed']:
                    console.print("    Removed Columns:")
                    for col in changes['removed']:
                        console.print(f"      - {format_column(col)}")
                
                if changes['modified']:
                    console.print("    Modified Columns:")
                    for mod in changes['modified']:
                        console.print(f"      ~ {mod['name']}:")
                        console.print(f"        From: {format_column({'name': mod['name'], **mod['old']})}")
                        console.print(f"        To:   {format_column({'name': mod['name'], **mod['new']})}")
        
        console.print()  # Empty line at end
        
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]\n")

if __name__ == '__main__':
    show_diff()