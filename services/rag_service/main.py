from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rag_system import RAGSystem
import uvicorn

# Add parent directories to path to find config
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import ENV_FILE, STATIC_DIR

# Load environment variables
load_dotenv(ENV_FILE)

app = FastAPI(title="PDF RAG Application", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Initialize RAG system
rag_system = None

class ChatRequest(BaseModel):
    message: str
    api_key: str

class ChatResponse(BaseModel):
    response: str
    sources: list = []

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup"""
    global rag_system
    
    try:
        rag_system = RAGSystem()
        print("[+] RAG system initialized")
    except Exception as e:
        print(f"[x] Error initializing RAG system: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Redirect to the LangGraph AI system"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Smart Policy Management System</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                max-width: 600px;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                padding: 40px;
                text-align: center;
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
                font-size: 2.5em;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 1.2em;
                line-height: 1.6;
            }
            .redirect-btn {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 10px;
                font-size: 1.1em;
                font-weight: bold;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
            }
            .redirect-btn:hover {
                background: #45a049;
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
            }
            .features {
                margin-top: 30px;
                text-align: left;
            }
            .feature {
                margin: 10px 0;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #4CAF50;
            }
            .feature strong {
                color: #333;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Smart Policy Management System</h1>
            <p class="subtitle">
                Powered by LangGraph AI with intelligent routing and Groq integration
            </p>
            
            <div class="features">
                <div class="feature">
                    <strong>🎯 Smart Intent Detection:</strong> Automatically routes your queries to the right service
                </div>
                <div class="feature">
                    <strong>📄 Document Analysis:</strong> Ask questions about your PDF policy documents
                </div>
                <div class="feature">
                    <strong>🗃️ Database Queries:</strong> Natural language to SQL conversion
                </div>
                <div class="feature">
                    <strong>🤖 Intelligent Greetings:</strong> Personalized responses and assistance
                </div>
                <div class="feature">
                    <strong>⚡ Quota-Free:</strong> Powered by Groq API for reliable, fast responses
                </div>
            </div>
            
            <a href="http://localhost:8002" class="redirect-btn">
                🚀 Launch AI System
            </a>
        </div>
        
        <script>
            // Auto-redirect after 5 seconds
            setTimeout(() => {
                window.location.href = 'http://localhost:8002';
            }, 5000);
        </script>
    </body>
    </html>
    """, status_code=200)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle PDF RAG chat requests"""
    import datetime
    print(f"🕒 Chat request received at {datetime.datetime.now()}")
    print(f"📝 Message: {request.message}")
    
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    print(f"[i] API Key received - Length: {len(request.api_key)}")
    print(f"[i] API Key preview: {request.api_key[:10]}...")
    
    try:
        if not rag_system:
            raise HTTPException(status_code=500, detail="RAG system not initialized")
        
        print(f"[>] Processing PDF query: {request.message[:50]}...")
        response = rag_system.query_with_key(request.message, request.api_key)
        print(f"[+] PDF query processed successfully")
        
        return ChatResponse(
            response=response["answer"],
            sources=response.get("sources", [])
        )
        
    except Exception as e:
        print(f"[x] Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "rag_initialized": rag_system is not None
    }

@app.get("/test-api")
async def test_api():
    """Test API key directly"""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return {"error": "No API key found"}
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello, this is a test.")
        
        return {
            "success": True,
            "api_key_length": len(api_key),
            "api_key_preview": api_key[:10] + "...",
            "response_preview": response.text[:100] + "..."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "api_key_length": len(api_key),
            "api_key_preview": api_key[:10] + "..."
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
