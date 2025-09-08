from typing import Dict, List, Any, TypedDict, Annotated, Optional
import json
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# State definition for LangGraph
class AgentState(TypedDict):
    query: str
    api_key: str
    intent_analysis: Optional[Dict[str, Any]]
    rag_result: Optional[Dict[str, Any]]
    db_result: Optional[Dict[str, Any]]
    mcp_result: Optional[Dict[str, Any]]  # Added for MCP service results
    final_response: Optional[str]
    final_answer: Optional[str]  # Added for storing processed answers
    service_routing: Optional[str]
    service_used: Optional[str]  # Added for tracking which service was used
    confidence_score: Optional[float]
    error: Optional[str]
    metadata: Dict[str, Any]

# Service helper classes for making HTTP requests
class RAGQueryTool:
    def __init__(self, rag_endpoint: str = "http://localhost:8000"):
        self.rag_endpoint = rag_endpoint
    
    async def _arun(self, query: str, api_key: str) -> Dict[str, Any]:
        """Async implementation"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.rag_endpoint}/chat",
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
                            "sources": data.get("sources", []),
                            "source": "RAG"
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
    
    async def query_async(self, query: str, api_key: str) -> Dict[str, Any]:
        """Async version for use in async contexts"""
        return await self._arun(query, api_key)
    
    def query(self, query: str, api_key: str) -> Dict[str, Any]:
        """Sync wrapper for async call"""
        return asyncio.run(self._arun(query, api_key))

class DatabaseQueryTool:
    def __init__(self, db_endpoint: str = "http://localhost:8003"):
        self.db_endpoint = db_endpoint
    
    async def _arun(self, query: str, api_key: str) -> Dict[str, Any]:
        """Async implementation"""
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
                            "sql_query": data.get("sql_query", ""),
                            "raw_results": data.get("raw_results", {}),
                            "source": "DATABASE"
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
    
    async def query_async(self, query: str, api_key: str) -> Dict[str, Any]:
        """Async version for use in async contexts"""
        return await self._arun(query, api_key)
    
    def query(self, query: str, api_key: str) -> Dict[str, Any]:
        """Sync wrapper for async call"""
        return asyncio.run(self._arun(query, api_key))

class MCPCalculatorTool:
    def __init__(self, mcp_endpoint: str = "http://localhost:8006"):
        self.mcp_endpoint = mcp_endpoint
    
    async def _arun(self, query: str, api_key: str) -> Dict[str, Any]:
        """Async implementation for MCP calculations"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mcp_endpoint}/chat",
                    json={"message": query, "api_key": api_key},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "answer": result.get("response", ""),
                            "calculation_result": result.get("calculation_result"),
                            "service_used": result.get("service_used", "MCP Calculator"),
                            "source": "MCP"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"MCP service error: {response.status} - {error_text}",
                            "source": "MCP"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": f"MCP service connection error: {str(e)}",
                "source": "MCP"
            }
    
    async def query_async(self, query: str, api_key: str) -> Dict[str, Any]:
        """Async version for use in async contexts"""
        return await self._arun(query, api_key)
    
    def query(self, query: str, api_key: str) -> Dict[str, Any]:
        """Sync wrapper for async call"""
        return asyncio.run(self._arun(query, api_key))

class LangGraphAgentSystem:
    def __init__(self):
        self.rag_tool = RAGQueryTool()
        self.db_tool = DatabaseQueryTool()
        self.mcp_tool = MCPCalculatorTool()
        self.llm = None
        self.groq_llm = None
        self.workflow = None
        self.groq_api_key = "YOUR_API_KEY_HERE"  # Groq fallback
        self._build_workflow()
        
    def setup_llm(self, api_key: str):
        """Setup the language model with Groq fallback"""
        try:
            # Try to setup Gemini first
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=api_key.strip(),
                temperature=0.1
            )
            print("[+] LangGraph agent LLM configured (Gemini)")
        except Exception as e:
            print(f"[-] Error setting up Gemini LLM: {e}")
            print("🔄 Falling back to Groq...")
            
        # Always setup Groq as backup
        try:
            self.groq_llm = ChatGroq(
                model_name="llama3-70b-8192",  # Fast and capable model
                groq_api_key=self.groq_api_key,
                temperature=0.1
            )
            print("[+] LangGraph agent Groq LLM configured")
        except Exception as groq_error:
            print(f"[-] Error setting up Groq LLM: {groq_error}")
            
        # If both fail, raise an exception
        if not self.llm and not self.groq_llm:
            raise Exception("Failed to setup both Gemini and Groq LLMs")
            
    def get_active_llm(self):
        """Get the active LLM, preferring Groq for reliability"""
        if self.groq_llm:
            return self.groq_llm, "Groq"
        elif self.llm:
            return self.llm, "Gemini"
        else:
            return None, "None"

    def _build_workflow(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_intent", self._analyze_intent_node)
        workflow.add_node("route_to_services", self._route_to_services_node)
        workflow.add_node("handle_greeting", self._handle_greeting_node)
        workflow.add_node("query_rag", self._query_rag_node)
        workflow.add_node("query_database", self._query_database_node)
        workflow.add_node("query_mcp", self._query_mcp_node)
        workflow.add_node("query_both", self._query_both_node)
        workflow.add_node("synthesize_response", self._synthesize_response_node)
        workflow.add_node("format_final_response", self._format_final_response_node)
        
        # Set entry point
        workflow.set_entry_point("analyze_intent")
        
        # Add edges
        workflow.add_edge("analyze_intent", "route_to_services")
        
        # Conditional routing from route_to_services
        workflow.add_conditional_edges(
            "route_to_services",
            self._routing_condition,
            {
                "greeting": "handle_greeting",
                "rag": "query_rag",
                "database": "query_database",
                "mcp": "query_mcp",
                "both": "query_both"
            }
        )
        
        # Connect query nodes to synthesis
        workflow.add_edge("handle_greeting", "format_final_response")
        workflow.add_edge("query_rag", "format_final_response")
        workflow.add_edge("query_database", "format_final_response")
        workflow.add_edge("query_mcp", "format_final_response")
        workflow.add_edge("query_both", "synthesize_response")
        workflow.add_edge("synthesize_response", "format_final_response")
        
        # End the workflow
        workflow.add_edge("format_final_response", END)
        
        self.workflow = workflow.compile()

    def _analyze_intent_node(self, state: AgentState) -> AgentState:
        """Node to analyze user intent"""
        query = state["query"]
        api_key = state["api_key"]
        
        if not self.llm and not self.groq_llm:
            self.setup_llm(api_key)
        
        # Get the active LLM
        active_llm, llm_type = self.get_active_llm()
        if not active_llm:
            raise Exception("No LLM available for intent analysis")
            
        analysis_prompt = f"""You are an intelligent query router for a policy management system. Analyze the user's question and determine which service(s) should handle it.

Available Services:
1. GREETING: For simple greetings like "hi", "hello", "hey", "good morning" - provide a welcome message
2. RAG (PDF Documents): Best for detailed policy content, terms, conditions, coverage details, explanations from PDF documents
3. DATABASE: Best for structured queries about policy numbers, customer names, statuses, counts, lists, filtering
4. MCP (Calculator): Best for insurance calculations like premium calculations, claim processing, insurance cost estimates
5. BOTH: When the query needs both structured data AND detailed document content

User Query: "{query}"

Guidelines:
- Use GREETING for: "hi", "hello", "hey", "good morning", "good afternoon", "good evening", or any simple greeting
- Use RAG for: "What does the policy cover?", "Explain the terms", "What are the exclusions?", "Policy details", "Coverage information"
- Use DATABASE for: "How many policies?", "List all customers", "Show active policies", "Find policy by number", "Customer information", "Policy status"
- Use MCP for: "Calculate premium", "Process claim", "Calculate insurance cost", "Premium calculation", "Claim calculation", "Insurance calculations"
- Use BOTH for: "Show me John's policy details and explain the coverage", "List active policies and their terms", "Find expired policies and their conditions"

IMPORTANT: If the query is just a greeting (like "hi", "hello", etc.), always choose GREETING service with high confidence.
IMPORTANT: If the query mentions "calculate", "premium", "claim", or insurance calculations, choose MCP service.

Respond with ONLY a JSON object in this format:
{{
    "service": "GREETING|RAG|DATABASE|MCP|BOTH",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this routing was chosen",
    "query_type": "greeting|document_content|structured_data|hybrid"
}}"""

        # Quick check for calculation queries - bypass LLM for speed
        query_lower = query.lower().strip()
        if any(keyword in query_lower for keyword in ['calculate', 'premium', 'claim', 'insurance']):
            print("🚀 Quick MCP routing - detected calculation keywords")
            state["intent_analysis"] = {
                "service": "MCP",
                "confidence": 1.0,
                "reasoning": "Quick route: Detected calculation keywords, routing directly to MCP",
                "query_type": "calculation"
            }
            return state
        
        # Quick check for greetings - bypass LLM for speed
        greetings = ['hi', 'hello', 'hey', 'greetings']
        if query_lower in greetings or len(query_lower.split()) <= 2 and any(greeting in query_lower for greeting in greetings):
            print("🚀 Quick greeting response")
            state["intent_analysis"] = {
                "service": "GREETING",
                "confidence": 1.0,
                "reasoning": "Quick route: Simple greeting detected",
                "query_type": "greeting"
            }
            return state

        try:
            messages = [SystemMessage(content="You are an expert query router."), 
                       HumanMessage(content=analysis_prompt)]
            
            # Use the active LLM (prefer Groq for reliability)
            print(f"🧠 Using {llm_type} for intent analysis")
            response = active_llm.invoke(messages)
            result_text = response.content.strip()
            
            # Clean up JSON response
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].strip()
            
            intent_analysis = json.loads(result_text)
            state["intent_analysis"] = intent_analysis
            state["confidence_score"] = intent_analysis.get("confidence", 0.0)
            
            print(f"🎯 Intent analysis: {intent_analysis}")
            
        except Exception as e:
            print(f"[-] Error analyzing intent: {e}")
            # Fallback logic with greeting detection
            query_lower = query.lower().strip()
            
            # Check for simple greetings first
            greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
            if query_lower in greetings or len(query_lower.split()) <= 2 and any(greeting in query_lower for greeting in greetings):
                state["intent_analysis"] = {
                    "service": "GREETING",
                    "confidence": 1.0,
                    "reasoning": "Fallback: Simple greeting detected, no service routing needed",
                    "query_type": "greeting"
                }
            elif any(keyword in query_lower for keyword in ['calculate', 'premium', 'claim', 'insurance', 'coverage', 'deductible']):
                state["intent_analysis"] = {
                    "service": "MCP",
                    "confidence": 0.9,
                    "reasoning": "Fallback: Detected calculation/insurance keywords, routing to MCP",
                    "query_type": "calculation"
                }
            elif any(keyword in query_lower for keyword in ['how many', 'list', 'show', 'count', 'find', 'customer', 'status', 'active', 'pending']):
                state["intent_analysis"] = {
                    "service": "DATABASE", 
                    "confidence": 0.7,
                    "reasoning": "Fallback: Detected structured query keywords",
                    "query_type": "structured_data"
                }
            else:
                state["intent_analysis"] = {
                    "service": "RAG",
                    "confidence": 0.7,
                    "reasoning": "Fallback: Default to document content search",
                    "query_type": "document_content"
                }
        
        return state

    def _route_to_services_node(self, state: AgentState) -> AgentState:
        """Node to determine service routing"""
        intent = state["intent_analysis"]
        service_choice = intent.get("service", "RAG").upper()
        state["service_routing"] = service_choice
        print(f"🚦 Routing to: {service_choice}")
        return state

    def _routing_condition(self, state: AgentState) -> str:
        """Conditional function for routing"""
        service_routing = state.get("service_routing", "RAG")
        if service_routing == "GREETING":
            return "greeting"
        elif service_routing == "DATABASE":
            return "database"
        elif service_routing == "MCP":
            return "mcp"
        elif service_routing == "BOTH":
            return "both"
        else:
            return "rag"

    def _handle_greeting_node(self, state: AgentState) -> AgentState:
        """Node to handle simple greetings without calling external services"""
        query = state["query"].lower().strip()
        
        greeting_responses = {
            "hi": "Hello! I'm your AI assistant for the Policy Management System. I can help you with:\n\n📄 **Document queries**: Ask about policy terms, conditions, coverage details, or exclusions\n🗃️ **Database queries**: Search for policies by customer, status, or policy numbers\n🤖 **Smart routing**: I'll automatically determine the best way to answer your questions\n\nWhat would you like to know about your policies?",
            "hello": "Hello! Welcome to the Policy Management System. I can help you access policy information from both documents and our database. What can I help you with today?",
            "hey": "Hey there! I'm here to help with your policy management needs. Ask me anything about policy details, customer information, or coverage terms.",
            "good morning": "Good morning! Ready to help you with your policy management tasks today. What would you like to explore?",
            "good afternoon": "Good afternoon! How can I assist you with your policy information today?",
            "good evening": "Good evening! I'm here to help with any policy-related questions you might have."
        }
        
        # Find the best matching greeting
        response = greeting_responses.get(query, greeting_responses["hi"])
        
        state["final_response"] = response
        print(f"👋 Greeting handled: {query} -> personalized response")
        return state

    async def _query_rag_node(self, state: AgentState) -> AgentState:
        """Node to query RAG service"""
        query = state["query"]
        api_key = state["api_key"]
        
        print("📄 Querying RAG service...")
        result = await self.rag_tool.query_async(query, api_key)
        print(f"[*] RAG query result type: {type(result)}")
        print(f"[*] RAG query result: {result}")
        
        # Ensure result is a dictionary
        if not isinstance(result, dict):
            print(f"⚠️ RAG result is not a dict, creating fallback")
            result = {
                "success": False,
                "error": f"RAG query returned {type(result)}: {result}",
                "source": "RAG"
            }
        
        state["rag_result"] = result
        
        return state

    async def _query_database_node(self, state: AgentState) -> AgentState:
        """Node to query database service"""
        query = state["query"]
        api_key = state["api_key"]
        
        print("🗃️ Querying database service...")
        result = await self.db_tool.query_async(query, api_key)
        print(f"[*] Database query result type: {type(result)}")
        print(f"[*] Database query result: {result}")
        
        # Ensure result is a dictionary
        if not isinstance(result, dict):
            print(f"⚠️ Database result is not a dict, creating fallback")
            result = {
                "success": False,
                "error": f"Database query returned {type(result)}: {result}",
                "source": "DATABASE"
            }
        
        state["db_result"] = result
        
        return state

    async def _query_mcp_node(self, state: AgentState) -> AgentState:
        """Node to query MCP calculator service"""
        query = state["query"]
        api_key = state["api_key"]
        
        print(f"[*] Querying MCP service with: {query}")
        result = await self.mcp_tool.query_async(query, api_key)
        
        if result.get("success"):
            state["mcp_result"] = result
            state["final_answer"] = result.get("answer", "")
            state["service_used"] = "MCP Calculator"
            state["metadata"] = {
                "calculation_result": result.get("calculation_result"),
                "service_used": result.get("service_used", "MCP Calculator"),
                "source": "MCP"
            }
        else:
            state["mcp_result"] = result
            state["final_answer"] = f"Sorry, I encountered an error with the calculation service: {result.get('error', 'Unknown error')}"
            state["service_used"] = "MCP Calculator (Error)"
            state["metadata"] = {
                "error": result.get("error"),
                "source": "MCP"
            }
        
        return state

    async def _query_both_node(self, state: AgentState) -> AgentState:
        """Node to query both services concurrently"""
        query = state["query"]
        api_key = state["api_key"]
        
        print("🔄 Querying both RAG and Database services...")
        
        # Run both queries concurrently using asyncio
        rag_task = asyncio.create_task(self.rag_tool.query_async(query, api_key))
        db_task = asyncio.create_task(self.db_tool.query_async(query, api_key))
        
        rag_result = await rag_task
        db_result = await db_task
        
        print(f"[*] RAG result type: {type(rag_result)}")
        print(f"[*] Database result type: {type(db_result)}")
        
        # Ensure results are dictionaries
        if not isinstance(rag_result, dict):
            print(f"⚠️ RAG result is not a dict, creating fallback")
            rag_result = {
                "success": False,
                "error": f"RAG query returned {type(rag_result)}: {rag_result}",
                "source": "RAG"
            }
        
        if not isinstance(db_result, dict):
            print(f"⚠️ Database result is not a dict, creating fallback")
            db_result = {
                "success": False,
                "error": f"Database query returned {type(db_result)}: {db_result}",
                "source": "DATABASE"
            }
        
        state["rag_result"] = rag_result
        state["db_result"] = db_result
        
        return state

    async def _synthesize_response_node(self, state: AgentState) -> AgentState:
        """Node to synthesize responses from multiple services"""
        if not self.llm and not self.groq_llm:
            self.setup_llm(state["api_key"])
        
        # Get the active LLM
        active_llm, llm_type = self.get_active_llm()
        if not active_llm:
            print("[-] No LLM available for synthesis")
            return state
            
        rag_result = state.get("rag_result", {})
        db_result = state.get("db_result", {})
        
        # Ensure results are dictionaries to avoid NoneType errors
        if not isinstance(rag_result, dict):
            rag_result = {}
        if not isinstance(db_result, dict):
            db_result = {}
            
        original_query = state["query"]
        
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
            messages = [SystemMessage(content="You are an expert information synthesizer."), 
                       HumanMessage(content=synthesis_prompt)]
            print(f"🧠 Using {llm_type} for response synthesis")
            response = await active_llm.ainvoke(messages)
            synthesized_response = response.content
            state["final_response"] = synthesized_response
            print("🔗 Response synthesized successfully")
            
        except Exception as e:
            print(f"[-] Error synthesizing response: {e}")
            # Fallback: Simple concatenation with null checks
            combined = ""
            if isinstance(rag_result, dict) and rag_result.get('success') and rag_result.get('response'):
                combined += f"📄 From documents: {rag_result['response']}\n\n"
            if isinstance(db_result, dict) and db_result.get('success') and db_result.get('response'):
                combined += f"📊 From database: {db_result['response']}"
            state["final_response"] = combined if combined else "Sorry, I couldn't process your query at this time."
        
        return state

    def _format_final_response_node(self, state: AgentState) -> AgentState:
        """Node to format the final response"""
        # If we have a synthesized response, use it
        if state.get("final_response"):
            return state
        
        # Otherwise, format based on single service result
        service_routing = state.get("service_routing", "RAG")
        
        if service_routing == "DATABASE" and state.get("db_result"):
            db_result = state.get("db_result", {})
            if isinstance(db_result, dict) and db_result.get("success"):
                state["final_response"] = db_result.get("response", "No response from database")
            else:
                error_msg = db_result.get('error', 'Unknown error') if isinstance(db_result, dict) else 'Invalid database result'
                state["final_response"] = f"Database query failed: {error_msg}"
                
        elif service_routing == "RAG" and state.get("rag_result"):
            rag_result = state.get("rag_result", {})
            if isinstance(rag_result, dict) and rag_result.get("success"):
                state["final_response"] = rag_result.get("response", "No response from RAG")
            else:
                error_msg = rag_result.get('error', 'Unknown error') if isinstance(rag_result, dict) else 'Invalid RAG result'
                state["final_response"] = f"RAG query failed: {error_msg}"
                
        elif service_routing == "MCP" and (state.get("final_answer") or state.get("mcp_result")):
            # Handle MCP service response
            if state.get("final_answer"):
                state["final_response"] = state["final_answer"]
            elif state.get("mcp_result"):
                mcp_result = state.get("mcp_result", {})
                if isinstance(mcp_result, dict) and mcp_result.get("success"):
                    state["final_response"] = mcp_result.get("answer", "No response from MCP")
                else:
                    error_msg = mcp_result.get('error', 'Unknown error') if isinstance(mcp_result, dict) else 'Invalid MCP result'
                    state["final_response"] = f"MCP query failed: {error_msg}"
        
        # Ensure we have a response
        if not state.get("final_response"):
            state["final_response"] = "Sorry, I couldn't process your query at this time."
        
        # Add metadata with null safety
        metadata = {
            "service_used": service_routing or "UNKNOWN",
            "intent_analysis": state.get("intent_analysis") or {},
            "confidence_score": state.get("confidence_score") or 0.0
        }
        
        # Add SQL query if available with null safety
        db_result = state.get("db_result")
        if isinstance(db_result, dict) and db_result.get("sql_query"):
            metadata["sql_query"] = db_result["sql_query"]
        
        # Add sources if available with null safety
        rag_result = state.get("rag_result")
        if isinstance(rag_result, dict) and rag_result.get("sources"):
            metadata["sources"] = rag_result["sources"]
        
        state["metadata"] = metadata
        
        return state

    async def process_query(self, query: str, api_key: str) -> Dict[str, Any]:
        """Main method to process user queries through the LangGraph workflow"""
        print(f"🤖 LangGraph agent processing query: {query}")
        
        try:
            # Initialize state
            initial_state = AgentState(
                query=query,
                api_key=api_key,
                intent_analysis=None,
                rag_result=None,
                db_result=None,
                final_response=None,
                service_routing=None,
                confidence_score=None,
                error=None,
                metadata={}
            )
            
            # Execute workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Extract results
            if final_state.get("final_response"):
                # Clean the response to remove any debug/routing information
                cleaned_response = self._clean_response_content(final_state["final_response"])
                
                return {
                    'success': True,
                    'response': cleaned_response,
                    'service_used': final_state.get("service_routing", "UNKNOWN"),
                    'intent_analysis': final_state.get("intent_analysis", {}),
                    'metadata': final_state.get("metadata", {}),
                    'sql_query': final_state.get("metadata", {}).get("sql_query", ""),
                    'rag_result': final_state.get("rag_result"),
                    'db_result': final_state.get("db_result")
                }
            elif final_state.get("final_answer"):
                # Handle MCP responses that use final_answer instead of final_response
                cleaned_response = self._clean_response_content(final_state["final_answer"])
                
                return {
                    'success': True,
                    'response': cleaned_response,
                    'service_used': final_state.get("service_used", final_state.get("service_routing", "MCP")),
                    'intent_analysis': final_state.get("intent_analysis", {}),
                    'metadata': final_state.get("metadata", {}),
                    'sql_query': final_state.get("metadata", {}).get("sql_query", ""),
                    'mcp_result': final_state.get("mcp_result"),
                    'rag_result': final_state.get("rag_result"),
                    'db_result': final_state.get("db_result")
                }
            else:
                return {
                    'success': False,
                    'error': final_state.get("error", "Unknown workflow error"),
                    'service_used': 'WORKFLOW',
                    'intent_analysis': final_state.get("intent_analysis", {})
                }
                
        except Exception as e:
            print(f"[-] LangGraph workflow error: {e}")
            return {
                'success': False,
                'error': f"Workflow processing error: {str(e)}",
                'service_used': 'WORKFLOW',
                'intent_analysis': {}
            }

    def _clean_response_content(self, response_text: str) -> str:
        """Clean response text by removing debug/routing information"""
        if not response_text:
            return response_text
        
        import re
        
        # Remove routing debug messages (comprehensive patterns)
        response_text = re.sub(r'🔄 Route:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE)
        response_text = re.sub(r'Route:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE)
        
        response_text = re.sub(r'🎯 Logic:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE | re.DOTALL)
        response_text = re.sub(r'Logic:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE | re.DOTALL)
        
        response_text = re.sub(r'📊 Confidence:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE)
        response_text = re.sub(r'Confidence:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE)
        
        # Remove SQL query displays
        response_text = re.sub(r'SQL:\s*SELECT.*?;(\s*\n)?', '', response_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove reasoning explanations
        response_text = re.sub(r'The query is asking.*?(?=\n\n|\n[A-Z]|$)', '', response_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove service routing explanations
        response_text = re.sub(r'which requires.*?service\.?', '', response_text, flags=re.IGNORECASE)
        response_text = re.sub(r'making DATABASE.*?service\.?', '', response_text, flags=re.IGNORECASE)
        response_text = re.sub(r'making RAG.*?service\.?', '', response_text, flags=re.IGNORECASE)
        
        # Clean up spacing
        response_text = re.sub(r'\n\s*\n', '\n\n', response_text)
        response_text = re.sub(r'\n{3,}', '\n\n', response_text)
        response_text = response_text.strip()
        
        return response_text

    async def check_services_health(self) -> Dict[str, bool]:
        """Check if all underlying services are available"""
        health_status = {"rag": False, "database": False, "mcp": False}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check RAG service
                try:
                    async with session.get("http://localhost:8000/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        health_status["rag"] = response.status == 200
                except:
                    pass
                
                # Check Database service
                try:
                    async with session.get("http://localhost:8003/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        health_status["database"] = response.status == 200
                except:
                    pass
                
                # Check MCP service
                try:
                    async with session.get("http://localhost:8006/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        health_status["mcp"] = response.status == 200
                except:
                    pass
        except:
            pass
            
        return health_status
