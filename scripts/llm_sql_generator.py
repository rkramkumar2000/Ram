"""SQL generation using Google's Gemini LLM."""

import google.generativeai as genai
import json
import logging
import re
from typing import List, Dict, Optional, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass

class SqlGenerationError(LLMError):
    """Exception for SQL generation failures."""
    pass

class LLMSqlGenerator:
    """SQL generator using Gemini LLM."""
    
    SYSTEM_PROMPT = """You are a careful SQL DDL generator. Output only valid MySQL DDL statements in a single code block. Do not output explanations."""
    
    def __init__(self, api_key: str = "AIzaSyCFNkNglwYan_t-JvByO3mtjou6-wKa6b8"):
        """Initialize the SQL generator.
        
        Args:
            api_key: Gemini API key
        """
        genai.configure(api_key=api_key)
        
        # Configure the model
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Start chat with system prompt
        self.chat = self.model.start_chat(history=[
            {
                "role": "user",
                "parts": [self.SYSTEM_PROMPT]
            }
        ])
        
        logger.info("Initialized LLM SQL generator with Gemini")

    def _extract_sql(self, response: str) -> str:
        """Extract SQL from code fence in LLM response.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Extracted SQL statements
            
        Raises:
            SqlGenerationError: If SQL cannot be extracted
        """
        # Look for SQL between code fences
        match = re.search(r'```sql\s*(.*?)\s*```', response, re.DOTALL)
        if not match:
            raise SqlGenerationError("No SQL found in LLM response")
        
        sql = match.group(1).strip()
        if not sql:
            raise SqlGenerationError("Empty SQL in LLM response")
            
        return sql

    @retry(
        retry=retry_if_exception_type((Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def generate_sql_for_table(
        self,
        table_name: str,
        sheet_columns: List[Dict[str, Any]],
        existing_columns: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate SQL DDL for a table based on sheet and existing columns.
        
        Args:
            table_name: Name of the table
            sheet_columns: Column definitions from Google Sheet
            existing_columns: Existing column definitions from DB/repo, or None
            
        Returns:
            Generated SQL statements
            
        Raises:
            SqlGenerationError: If SQL generation fails
        """
        try:
            # Format the prompt
            prompt = f"""
Table name: {table_name}
Existing columns (in DB / repo): {json.dumps(existing_columns) if existing_columns else 'none'}
Columns from Google Sheet: {json.dumps(sheet_columns)}

Rules:
1) If the table does not exist -> generate a CREATE TABLE statement with sensible types, primary key if 'id' present, NOT NULL where nullable=false, DEFAULT where provided.
2) If the table exists -> generate ALTER TABLE statements that ADD only the new columns (never DROP or MODIFY).
3) Use MySQL syntax. Use IF NOT EXISTS for CREATE TABLE if appropriate; for ALTER use ADD COLUMN IF NOT EXISTS pattern (e.g., check existence then add).
4) If datatype is missing, infer common types (INT for numeric-looking names/id, VARCHAR(255) for names/emails, TEXT for large text, DATETIME for *_at timestamps).
5) Output only SQL inside a single ```sql ... ``` code fence. No explanations.

Output format:
- For CREATE: a single CREATE TABLE statement.
- For ALTER: one or more ALTER TABLE ... ADD COLUMN ...; statements.
"""
            
            logger.debug(f"Sending prompt for table {table_name}")
            
            # Get response from LLM
            response = await self.chat.send_message_async(prompt)
            
            if not response or not response.text:
                raise SqlGenerationError("Empty response from LLM")
            
            # Extract and validate SQL
            sql = self._extract_sql(response.text)
            
            logger.info(f"Generated SQL for table {table_name}")
            logger.debug(f"Generated SQL:\n{sql}")
            
            return sql
            
        except Exception as e:
            logger.error(f"Error generating SQL for table {table_name}: {str(e)}")
            raise SqlGenerationError(f"Failed to generate SQL: {str(e)}")

    def generate_sql_for_table_sync(
        self,
        table_name: str,
        sheet_columns: List[Dict[str, Any]],
        existing_columns: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Synchronous version of generate_sql_for_table.
        
        This is a convenience wrapper that runs the async method in a new event loop.
        For better performance in async applications, use generate_sql_for_table directly.
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(
            self.generate_sql_for_table(table_name, sheet_columns, existing_columns)
        )