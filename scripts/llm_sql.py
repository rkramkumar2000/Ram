#!/usr/bin/env python3
"""
LLM integration for SQL optimization and validation.
"""

from openai import OpenAI
import os

class LLMSQLHelper:
    def __init__(self, api_key: str = None):
        """Initialize LLM client."""
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

    def validate_sql(self, sql_statement: str) -> tuple[bool, str]:
        """Validate SQL statement using LLM."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Validate the following SQL statement and suggest improvements if needed."},
                    {"role": "user", "content": sql_statement}
                ]
            )
            return True, response.choices[0].message.content
        except Exception as e:
            return False, str(e)

    def optimize_schema(self, table_definition: str) -> str:
        """Get schema optimization suggestions."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a database expert. Review this table schema and suggest optimizations:"},
                    {"role": "user", "content": table_definition}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return str(e)