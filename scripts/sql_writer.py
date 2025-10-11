"""SQL file writer with backup functionality."""

import os
import shutil
from datetime import datetime
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_sql_files(sql_map: Dict[str, str], output_dir: str = 'sql_files') -> List[str]:
    """Write SQL statements to files with backup functionality.
    
    Args:
        sql_map: Dictionary mapping table names to SQL statements
        output_dir: Directory to write SQL files (default: 'sql_files')
        
    Returns:
        List[str]: List of paths to written files
        
    Example:
        sql_map = {
            "customers": "CREATE TABLE customers ...",
            "orders": "ALTER TABLE orders ..."
        }
        written_files = write_sql_files(sql_map)
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    written_files = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for table_name, sql_content in sql_map.items():
        if not sql_content.strip():
            logger.warning(f"Empty SQL content for table {table_name}, skipping")
            continue
            
        # Construct file paths
        sql_file = os.path.join(output_dir, f"{table_name}.sql")
        
        # Create backup if file exists
        if os.path.exists(sql_file):
            backup_file = f"{sql_file}.bak.{timestamp}"
            try:
                shutil.copy2(sql_file, backup_file)
                logger.info(f"Created backup: {backup_file}")
            except Exception as e:
                logger.error(f"Failed to create backup for {sql_file}: {str(e)}")
                continue
        
        # Write new SQL content
        try:
            with open(sql_file, 'w', encoding='utf-8') as f:
                # Ensure SQL ends with newline
                sql_content = sql_content.strip() + '\n'
                f.write(sql_content)
            
            written_files.append(sql_file)
            logger.info(f"Written SQL file: {sql_file}")
            
        except Exception as e:
            logger.error(f"Failed to write {sql_file}: {str(e)}")
            # Try to restore from backup if it exists
            backup_file = f"{sql_file}.bak.{timestamp}"
            if os.path.exists(backup_file):
                try:
                    shutil.copy2(backup_file, sql_file)
                    logger.info(f"Restored from backup: {sql_file}")
                except Exception as restore_error:
                    logger.error(f"Failed to restore from backup: {str(restore_error)}")
    
    return written_files