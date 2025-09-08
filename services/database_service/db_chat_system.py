import os
import psycopg2
from sqlalchemy import create_engine, text
import google.generativeai as genai
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

class DatabaseChatSystem:
    def __init__(self):
        self.db_config = {
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASS'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME')
        }
        self.engine = None
        self.model = None
        self.groq_model = None
        self.groq_api_key = "YOUR_API_KEY_HERE"  # Groq fallback
        self.setup_database_connection()
        
    def setup_database_connection(self):
        """Setup database connection"""
        try:
            connection_string = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            self.engine = create_engine(connection_string)
            print("[+] Database connection established")
        except Exception as e:
            print(f"[-] Database connection failed: {e}")
            raise
            
    def setup_model(self, api_key: str):
        """Setup Groq model with Gemini fallback"""
        try:
            # Setup Groq first (preferred for reliability and speed)
            self.groq_model = ChatGroq(
                model_name="llama3-70b-8192",
                groq_api_key=self.groq_api_key,
                temperature=0.1
            )
            print("[+] Groq model configured for database chat")
        except Exception as e:
            print(f"[-] Error setting up Groq model: {e}")
            
        # Also setup Gemini as backup
        try:
            genai.configure(api_key=api_key.strip())
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("[+] Gemini model configured for database chat (backup)")
        except Exception as e:
            print(f"[-] Error setting up Gemini model: {e}")
            
        # If both fail, raise an exception
        if not self.groq_model and not self.model:
            raise Exception("Failed to setup both Groq and Gemini models")
            
    def get_active_model(self):
        """Get the active model, preferring Groq for reliability"""
        if self.groq_model:
            return self.groq_model, "Groq"
        elif self.model:
            return self.model, "Gemini"
        else:
            return None, "None"
            
    def get_table_schema(self):
        """Get the database schema information"""
        try:
            with self.engine.connect() as connection:
                # Get table info for policies table
                schema_query = """
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = 'policies'
                ORDER BY ordinal_position;
                """
                
                result = connection.execute(text(schema_query))
                schema_info = result.fetchall()
                
                schema_text = "Table: policies\n"
                for row in schema_info:
                    schema_text += f"- {row[0]} ({row[1]}) {'NULL' if row[2] == 'YES' else 'NOT NULL'}\n"
                
                return schema_text
        except Exception as e:
            print(f"[-] Error getting schema: {e}")
            return "Table schema unavailable"
            
    def get_sample_data(self, limit=3):
        """Get sample data from the policies table"""
        try:
            with self.engine.connect() as connection:
                sample_query = f"SELECT * FROM policies LIMIT {limit};"
                result = connection.execute(text(sample_query))
                sample_data = result.fetchall()
                
                if sample_data:
                    sample_text = "Sample data:\n"
                    for row in sample_data:
                        sample_text += f"Policy: {row[0]}, Customer: {row[1]}, Status: {row[2]}, PDF: {row[3]}\n"
                    return sample_text
                else:
                    return "No sample data available"
        except Exception as e:
            print(f"[-] Error getting sample data: {e}")
            return "Sample data unavailable"
            
    def text_to_sql(self, question: str, api_key: str):
        """Convert natural language question to SQL query"""
        if not self.groq_model and not self.model:
            self.setup_model(api_key)
            
        # Get the active model
        active_model, model_type = self.get_active_model()
        if not active_model:
            raise Exception("No LLM available for SQL generation")
            
        schema = self.get_table_schema()
        sample_data = self.get_sample_data()
        
        prompt = f"""You are a SQL expert. Convert the natural language question to a SQL query for PostgreSQL.

Database Schema:
{schema}

{sample_data}

Rules:
1. Only use the 'policies' table
2. Use proper PostgreSQL syntax
3. Be case-sensitive with column names
4. Return only the SQL query, no explanation
5. Use appropriate WHERE clauses for filtering
6. For partial matches, use ILIKE operator

Question: {question}

SQL Query:"""

        try:
            print(f"🔍 Using {model_type} for SQL generation")
            
            if model_type == "Groq":
                # Use LangChain ChatGroq
                from langchain.schema import HumanMessage, SystemMessage
                messages = [
                    SystemMessage(content="You are a SQL expert. Generate only SQL queries without explanations."),
                    HumanMessage(content=prompt)
                ]
                response = active_model.invoke(messages)
                sql_query = response.content.strip()
            else:
                # Use Gemini SDK
                response = active_model.generate_content(prompt)
                sql_query = response.text.strip()
            
            # Clean up the response - remove markdown formatting if present
            if '```sql' in sql_query:
                sql_query = sql_query.split('```sql')[1].split('```')[0].strip()
            elif '```' in sql_query:
                sql_query = sql_query.split('```')[1].strip()
            
            return sql_query
        except Exception as e:
            raise ValueError(f"Error generating SQL: {str(e)}")
            
    def execute_sql_query(self, sql_query: str):
        """Execute SQL query and return results"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(sql_query))
                
                # Handle different types of queries
                if sql_query.strip().upper().startswith('SELECT'):
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    return {
                        'success': True,
                        'columns': list(columns),
                        'data': [dict(zip(columns, row)) for row in rows],
                        'row_count': len(rows)
                    }
                else:
                    # For INSERT, UPDATE, DELETE queries
                    connection.commit()
                    return {
                        'success': True,
                        'message': 'Query executed successfully',
                        'rows_affected': result.rowcount
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def format_results(self, query_results: dict, original_question: str, api_key: str):
        """Format query results into natural language"""
        if not query_results['success']:
            return f"[-] Database Error: {query_results['error']}"
            
        if 'data' in query_results:
            # Format SELECT results
            data = query_results['data']
            if not data:
                return "No results found for your query."
            
            # Create a summary using LLM
            data_summary = f"Found {len(data)} records:\n"
            for i, record in enumerate(data[:10], 1):  # Limit to first 10 records
                data_summary += f"{i}. "
                for key, value in record.items():
                    data_summary += f"{key}: {value}, "
                data_summary = data_summary.rstrip(', ') + "\n"
            
            if len(data) > 10:
                data_summary += f"... and {len(data) - 10} more records"
                
            # Use LLM to create a natural language summary
            summary_prompt = f"""Based on this database query result, provide a natural language summary for the user.

Original Question: {original_question}

Query Results:
{data_summary}

Provide a clear, conversational summary of the results:"""

            try:
                if not self.model:
                    self.setup_model(api_key)
                    
                response = self.model.generate_content(summary_prompt)
                formatted_response = response.text
                
                # Clean response of any debug/routing information
                import re
                formatted_response = re.sub(r'🔄 Route:.*?\n', '', formatted_response)
                formatted_response = re.sub(r'🎯 Logic:.*?\n', '', formatted_response)
                formatted_response = re.sub(r'📊 Confidence:.*?\n', '', formatted_response)
                formatted_response = re.sub(r'SQL:\s*SELECT.*?;(\s*\n)?', '', formatted_response, flags=re.DOTALL)
                formatted_response = formatted_response.strip()
                
                return formatted_response
            except:
                return data_summary  # Fallback to raw summary
        else:
            # Format non-SELECT results
            return query_results.get('message', 'Query executed successfully')
            
    def chat_with_database(self, question: str, api_key: str):
        """Main method to chat with database"""
        print(f"🔍 Database chat question: {question}")
        
        try:
            # Convert question to SQL
            print("🔄 Converting question to SQL...")
            sql_query = self.text_to_sql(question, api_key)
            print(f"📝 Generated SQL: {sql_query}")
            
            # Execute SQL query
            print("⚡ Executing SQL query...")
            results = self.execute_sql_query(sql_query)
            
            # Format results
            print("📊 Formatting results...")
            formatted_response = self.format_results(results, question, api_key)
            
            return {
                'answer': formatted_response,
                'sql_query': sql_query,
                'raw_results': results
            }
            
        except Exception as e:
            print(f"[-] Database chat error: {e}")
            return {
                'answer': f"Sorry, I encountered an error while processing your database query: {str(e)}",
                'sql_query': f"-- Unable to generate SQL query due to error: {str(e)}",
                'raw_results': {'success': False, 'error': str(e)}
            }
