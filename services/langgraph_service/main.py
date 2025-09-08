from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from langgraph_agent_system import LangGraphAgentSystem
import uvicorn
import asyncio

import re

# Load environment variables
load_dotenv()

def clean_response(response_text: str) -> str:
    """Clean response text by removing debug/routing information"""
    if not response_text:
        return response_text
    
    # Remove routing debug messages (more comprehensive patterns)
    response_text = re.sub(r'🔄 Route:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'Route:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE)
    
    response_text = re.sub(r'🎯 Logic:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE | re.DOTALL)
    response_text = re.sub(r'Logic:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE | re.DOTALL)
    
    response_text = re.sub(r'📊 Confidence:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'Confidence:.*?(?=\n|$)', '', response_text, flags=re.IGNORECASE)
    
    # Remove SQL query displays
    response_text = re.sub(r'SQL:\s*SELECT.*?;(\s*\n)?', '', response_text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove reasoning explanations that start with "The query is asking"
    response_text = re.sub(r'The query is asking.*?(?=\n\n|\n[A-Z]|$)', '', response_text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove service routing explanations
    response_text = re.sub(r'which requires.*?service\.?', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'making DATABASE.*?service\.?', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'making RAG.*?service\.?', '', response_text, flags=re.IGNORECASE)
    
    # Remove multiple newlines and clean up spacing
    response_text = re.sub(r'\n\s*\n', '\n\n', response_text)
    response_text = re.sub(r'\n{3,}', '\n\n', response_text)
    
    # Trim whitespace
    response_text = response_text.strip()
    
    return response_text

app = FastAPI(title="LangGraph Agentic AI - Policy Management System", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files with absolute path - this will serve index.html at root
static_dir = os.path.join(os.path.dirname(__file__), "static")
print(f"[*] Mounting static directory: {static_dir}")

# Define API routes first, then mount static files
# This ensures API routes take precedence over static files

# Initialize LangGraph Agent system
agent_system = None

class ChatRequest(BaseModel):
    message: str
    api_key: str

class ChatResponse(BaseModel):
    response: str
    service_used: str = ""
    intent_analysis: dict = {}
    sql_query: str = ""
    metadata: dict = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the LangGraph Agent system on startup"""
    global agent_system
    
    try:
        agent_system = LangGraphAgentSystem()
        print("[+] LangGraph agentic AI system initialized")
        
        # Check underlying services
        health_status = await agent_system.check_services_health()
        print(f"[*] Service health check: RAG={health_status['rag']}, Database={health_status['database']}, MCP={health_status['mcp']}")
        
    except Exception as e:
        print(f"[-] Error initializing LangGraph agent system: {e}")

# Root route is now handled by static file mounting

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle agentic AI chat requests"""
    import datetime
    print(f"🕒 LangGraph AI request received at {datetime.datetime.now()}")
    print(f"📝 Message: {request.message}")
    
    if not agent_system:
        raise HTTPException(status_code=500, detail="LangGraph agent system not initialized")
    
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    print(f"[*] API Key received - Length: {len(request.api_key)}")
    print(f"[*] API Key preview: {request.api_key[:10]}...")
    
    try:
        print(f"[*] Processing query through LangGraph workflow: {request.message[:50]}...")
        result = await agent_system.process_query(request.message, request.api_key)
        
        if result['success']:
            print(f"[+] LangGraph workflow completed successfully using {result.get('service_used', 'unknown')} service(s)")
            
            # Clean the response to remove debug/routing information
            cleaned_response = clean_response(result["response"])
            
            return ChatResponse(
                response=cleaned_response,
                service_used=result.get("service_used", ""),
                intent_analysis=result.get("intent_analysis", {}),
                sql_query=result.get("sql_query", ""),
                metadata=result.get("metadata", {})
            )
        else:
            print(f"[-] LangGraph workflow failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
    except Exception as e:
        print(f"[-] Error in LangGraph AI endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint with service status"""
    if not agent_system:
        return {"status": "unhealthy", "error": "LangGraph agent system not initialized"}
    
    try:
        service_health = await agent_system.check_services_health()
        return {
            "status": "healthy",
            "agent_initialized": True,
            "agent_type": "LangGraph",
            "services": service_health,
            "all_services_available": all(service_health.values())
        }
    except Exception as e:
        return {
            "status": "partial",
            "agent_initialized": True,
            "error": str(e)
        }

@app.get("/services/status")
async def get_services_status():
    """Get detailed status of underlying services"""
    if not agent_system:
        raise HTTPException(status_code=500, detail="LangGraph agent system not initialized")
    
    try:
        service_health = await agent_system.check_services_health()
        return {
            "rag_service": {
                "available": service_health["rag"],
                "endpoint": "http://localhost:8000",
                "description": "PDF RAG Service - Document content search"
            },
            "database_service": {
                "available": service_health["database"],
                "endpoint": "http://localhost:8003",
                "description": "Database Chat Service - Structured data queries"
            },
            "mcp_service": {
                "available": service_health["mcp"],
                "endpoint": "http://localhost:8006",
                "description": "MCP Service - Insurance premium calculations"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking services: {str(e)}")

@app.post("/analyze")
async def analyze_query(request: ChatRequest):
    """Analyze query intent without executing"""
    if not agent_system:
        raise HTTPException(status_code=500, detail="LangGraph agent system not initialized")
    
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    try:
        # For LangGraph system, we need to use the internal method
        agent_system.setup_llm(request.api_key)
        
        # Create a minimal state to analyze intent
        from langgraph_agent_system import AgentState
        temp_state = AgentState(
            query=request.message,
            api_key=request.api_key,
            intent_analysis=None,
            rag_result=None,
            db_result=None,
            final_response=None,
            service_routing=None,
            confidence_score=None,
            error=None,
            metadata={}
        )
        
        # Run just the intent analysis
        result_state = agent_system._analyze_intent_node(temp_state)
        
        return {
            "query": request.message,
            "analysis": result_state.get("intent_analysis", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing query: {str(e)}")

# Mount static files AFTER all API routes are defined
# This ensures API routes take precedence over static file serving
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
