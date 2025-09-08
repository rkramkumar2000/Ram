from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from db_chat_system import DatabaseChatSystem
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI(title="Database Chat Application", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Database chat system
db_chat_system = None

class ChatRequest(BaseModel):
    message: str
    api_key: str

class ChatResponse(BaseModel):
    response: str
    sql_query: str = ""
    raw_results: dict = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the Database chat system on startup"""
    global db_chat_system
    
    try:
        db_chat_system = DatabaseChatSystem()
        print("[+] Database chat system initialized")
    except Exception as e:
        print(f"[-] Error initializing database chat system: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the database chat interface"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle database chat requests"""
    import datetime
    print(f"🕒 Database chat request received at {datetime.datetime.now()}")
    print(f"📝 Message: {request.message}")
    
    if not db_chat_system:
        raise HTTPException(status_code=500, detail="Database chat system not initialized")
    
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    print(f"[*] API Key received - Length: {len(request.api_key)}")
    print(f"[*] API Key preview: {request.api_key[:10]}...")
    
    try:
        print(f"[*] Processing database query: {request.message[:50]}...")
        response = db_chat_system.chat_with_database(request.message, request.api_key)
        print(f"[+] Database query processed successfully")
        
        return ChatResponse(
            response=response["answer"],
            sql_query=response.get("sql_query", ""),
            raw_results=response.get("raw_results", {})
        )
        
    except Exception as e:
        print(f"[-] Error in database chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "db_chat_initialized": db_chat_system is not None
    }

@app.get("/schema")
async def get_schema():
    """Get database schema information"""
    if not db_chat_system:
        raise HTTPException(status_code=500, detail="Database chat system not initialized")
    
    try:
        schema = db_chat_system.get_table_schema()
        sample_data = db_chat_system.get_sample_data()
        return {
            "schema": schema,
            "sample_data": sample_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting schema: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
