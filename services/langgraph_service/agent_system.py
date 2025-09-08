import google.generativeai as genai
import requests
import json
from typing import Dict, List, Any
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class AgentSystem:
    def __init__(self):
        self.rag_endpoint = "http://localhost:8000"  # PDF RAG service
        self.db_endpoint = "http://localhost:8001"   # Database chat service
        self.model = None
        
    def setup_model(self, api_key: str):
        """Setup Gemini model for agent decision making"""
        try:
            genai.configure(api_key=api_key.strip())
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Agent model configured")
        except Exception as e:
            print(f"❌ Error setting up agent model: {e}")
            raise

    def analyze_query_intent(self, query: str, api_key: str) -> Dict[str, Any]:
        """Analyze user query to determine which services to use"""
        if not self.model:
            self.setup_model(api_key)
        
        analysis_prompt = f"""You are an intelligent query router for a policy management system. Analyze the user's question and determine which service(s) should handle it.

Available Services:
1. RAG (PDF Documents): Best for detailed policy content, terms, conditions, coverage details, explanations from PDF documents
2. DATABASE: Best for structured queries about policy numbers, customer names, statuses, counts, lists, filtering
3. BOTH: When the query needs both structured data AND detailed document content

User Query: "{query}"

Guidelines:
- Use RAG for: "What does the policy cover?", "Explain the terms", "What are the exclusions?", "Policy details", "Coverage information"
- Use DATABASE for: "How many policies?", "List all customers", "Show active policies", "Find policy by number", "Customer information", "Policy status"
- Use BOTH for: "Show me John's policy details and explain the coverage", "List active policies and their terms", "Find expired policies and their conditions"

Respond with ONLY a JSON object in this format:
{{
    "service": "RAG|DATABASE|BOTH",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this routing was chosen",
    "query_type": "document_content|structured_data|hybrid"
}}"""

        try:
            response = self.model.generate_content(analysis_prompt)
            result_text = response.text.strip()
            
            # Clean up JSON response
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].strip()
            
            return json.loads(result_text)
        except Exception as e:
            print(f"❌ Error analyzing query intent: {e}")
            # Fallback logic
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in ['how many', 'list', 'show', 'count', 'find', 'customer', 'status', 'active', 'pending']):
                return {
                    "service": "DATABASE",
                    "confidence": 0.7,
                    "reasoning": "Fallback: Detected structured query keywords",
                    "query_type": "structured_data"
                }
            else:
                return {
                    "service": "RAG",
                    "confidence": 0.7,
                    "reasoning": "Fallback: Default to document content search",
                    "query_type": "document_content"
                }

    async def query_rag_service(self, query: str, api_key: str) -> Dict[str, Any]:
        """Query the RAG service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.rag_endpoint}/chat",
                    json={
                        "message": query,
                        "api_key": api_key,
                        "chat_type": "pdf"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "response": data.get("response", ""),
                            "source": "RAG",
                            "metadata": data.get("metadata", {})
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"RAG service error: {response.status} - {error_text}",
                            "source": "RAG"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": f"RAG service connection error: {str(e)}",
                "source": "RAG"
            }

    async def query_database_service(self, query: str, api_key: str) -> Dict[str, Any]:
        """Query the Database service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.db_endpoint}/chat",
                    json={
                        "message": query,
                        "api_key": api_key
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "response": data.get("response", ""),
                            "source": "DATABASE",
                            "sql_query": data.get("sql_query", ""),
                            "raw_results": data.get("raw_results", {})
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Database service error: {response.status} - {error_text}",
                            "source": "DATABASE"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": f"Database service connection error: {str(e)}",
                "source": "DATABASE"
            }

    def synthesize_responses(self, rag_result: Dict, db_result: Dict, original_query: str, api_key: str) -> str:
        """Combine responses from multiple services into a coherent answer"""
        if not self.model:
            self.setup_model(api_key)
        
        synthesis_prompt = f"""You are an intelligent assistant that combines information from multiple sources to provide comprehensive answers.

Original User Query: "{original_query}"

RAG Response (from PDF documents): {rag_result.get('response', 'No RAG response')}

Database Response (from structured data): {db_result.get('response', 'No database response')}

Instructions:
1. Combine both responses into a single, coherent answer
2. Prioritize the most relevant information for the user's query
3. If both sources provide complementary information, present them together
4. If one source is more relevant, lead with that but mention the other if useful
5. Maintain a natural, conversational tone
6. Don't mention "RAG" or "Database" - just provide the integrated information

Provide a comprehensive response:"""

        try:
            response = self.model.generate_content(synthesis_prompt)
            return response.text
        except Exception as e:
            # Fallback: Simple concatenation
            combined = ""
            if rag_result.get('success') and rag_result.get('response'):
                combined += f"📄 From documents: {rag_result['response']}\n\n"
            if db_result.get('success') and db_result.get('response'):
                combined += f"📊 From database: {db_result['response']}"
            return combined if combined else "Sorry, I couldn't process your query at this time."

    async def process_query(self, query: str, api_key: str) -> Dict[str, Any]:
        """Main method to process user queries through the agent system"""
        print(f"🤖 Agent processing query: {query}")
        
        try:
            # Step 1: Analyze query intent
            print("🔍 Analyzing query intent...")
            intent_analysis = self.analyze_query_intent(query, api_key)
            print(f"📊 Intent analysis: {intent_analysis}")
            
            service_choice = intent_analysis.get("service", "RAG")
            
            # Step 2: Route to appropriate services
            if service_choice == "RAG":
                print("📄 Routing to RAG service...")
                rag_result = await self.query_rag_service(query, api_key)
                
                if rag_result['success']:
                    return {
                        'success': True,
                        'response': rag_result['response'],
                        'service_used': 'RAG',
                        'intent_analysis': intent_analysis,
                        'metadata': rag_result.get('metadata', {})
                    }
                else:
                    return {
                        'success': False,
                        'error': rag_result['error'],
                        'service_used': 'RAG',
                        'intent_analysis': intent_analysis
                    }
                    
            elif service_choice == "DATABASE":
                print("🗃️ Routing to Database service...")
                db_result = await self.query_database_service(query, api_key)
                
                if db_result['success']:
                    return {
                        'success': True,
                        'response': db_result['response'],
                        'service_used': 'DATABASE',
                        'intent_analysis': intent_analysis,
                        'sql_query': db_result.get('sql_query', ''),
                        'raw_results': db_result.get('raw_results', {})
                    }
                else:
                    return {
                        'success': False,
                        'error': db_result['error'],
                        'service_used': 'DATABASE',
                        'intent_analysis': intent_analysis
                    }
                    
            else:  # BOTH
                print("🔄 Routing to both RAG and Database services...")
                
                # Query both services concurrently
                rag_task = self.query_rag_service(query, api_key)
                db_task = self.query_database_service(query, api_key)
                
                rag_result, db_result = await asyncio.gather(rag_task, db_task)
                
                # Synthesize responses
                if rag_result['success'] or db_result['success']:
                    print("🔗 Synthesizing responses...")
                    synthesized_response = self.synthesize_responses(rag_result, db_result, query, api_key)
                    
                    return {
                        'success': True,
                        'response': synthesized_response,
                        'service_used': 'BOTH',
                        'intent_analysis': intent_analysis,
                        'rag_result': rag_result,
                        'db_result': db_result,
                        'sql_query': db_result.get('sql_query', '') if db_result['success'] else '',
                        'metadata': rag_result.get('metadata', {}) if rag_result['success'] else {}
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Both services failed - RAG: {rag_result.get('error', 'Unknown error')}, DB: {db_result.get('error', 'Unknown error')}",
                        'service_used': 'BOTH',
                        'intent_analysis': intent_analysis
                    }
                    
        except Exception as e:
            print(f"❌ Agent processing error: {e}")
            return {
                'success': False,
                'error': f"Agent processing error: {str(e)}",
                'service_used': 'AGENT',
                'intent_analysis': {}
            }

    async def check_services_health(self) -> Dict[str, bool]:
        """Check if both underlying services are available"""
        health_status = {"rag": False, "database": False}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check RAG service
                try:
                    async with session.get(f"{self.rag_endpoint}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        health_status["rag"] = response.status == 200
                except:
                    pass
                
                # Check Database service
                try:
                    async with session.get(f"{self.db_endpoint}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        health_status["database"] = response.status == 200
                except:
                    pass
        except:
            pass
            
        return health_status
