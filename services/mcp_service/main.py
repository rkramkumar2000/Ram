"""
FastAPI MCP Service for Insurance Calculations
==============================================

This FastAPI service provides MCP (Model Context Protocol) compliant endpoints
for insurance premium and claim calculations.

Endpoints:
- POST /calculate/premium - Calculate insurance premium
- POST /calculate/claim - Process insurance claim
- GET /tools - Get available MCP tools
- POST /tools/execute - Execute MCP tools
- GET /health - Health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import json
import asyncio
from datetime import datetime

from mcp_calculator import PremiumCalculator, ClaimCalculator, MCPCalculatorTools

# FastAPI app initialization
app = FastAPI(
    title="MCP Insurance Calculator Service",
    description="Model Context Protocol service for insurance premium and claim calculations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class PremiumCalculationRequest(BaseModel):
    policy_type: str = Field(..., description="Type of insurance policy")
    sub_type: str = Field(..., description="Sub-type of insurance")
    coverage_amount: float = Field(..., gt=0, description="Coverage amount in dollars")
    customer_age: int = Field(..., ge=18, le=100, description="Customer age")
    risk_factors: Optional[List[str]] = Field(default=None, description="List of risk factors")

class ClaimCalculationRequest(BaseModel):
    policy_type: str = Field(..., description="Type of insurance policy")
    claim_type: str = Field(..., description="Type of claim")
    claim_amount: float = Field(..., gt=0, description="Claim amount in dollars")
    policy_coverage: float = Field(..., gt=0, description="Policy coverage limit")

class MCPToolRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the MCP tool to execute")
    arguments: Dict[str, Any] = Field(..., description="Tool arguments")

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    api_key: Optional[str] = Field(default="", description="API key (optional)")

class ChatResponse(BaseModel):
    response: str
    calculation_result: Optional[Dict[str, Any]] = None
    service_used: str = "MCP Calculator"

# Initialize MCP tools
mcp_tools = MCPCalculatorTools()

@app.on_event("startup")
async def startup_event():
    """Initialize the MCP service on startup"""
    print("[+] MCP Insurance Calculator service initialized")

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Insurance Calculator Service</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-left: 4px solid #007acc; }
            .method { font-weight: bold; color: #007acc; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>MCP Insurance Calculator Service</h1>
            <p>Model Context Protocol service for insurance calculations</p>
            
            <h2>Available Endpoints:</h2>
            
            <div class="endpoint">
                <div class="method">POST /calculate/premium</div>
                <p>Calculate insurance premium based on policy details</p>
            </div>
            
            <div class="endpoint">
                <div class="method">POST /calculate/claim</div>
                <p>Process and calculate insurance claim payout</p>
            </div>
            
            <div class="endpoint">
                <div class="method">POST /chat</div>
                <p>Chat interface for natural language calculations</p>
            </div>
            
            <div class="endpoint">
                <div class="method">GET /tools</div>
                <p>Get available MCP tools</p>
            </div>
            
            <div class="endpoint">
                <div class="method">POST /tools/execute</div>
                <p>Execute MCP tools</p>
            </div>
            
            <div class="endpoint">
                <div class="method">GET /health</div>
                <p>Service health check</p>
            </div>
            
            <h2>Example Usage:</h2>
            <pre>
# Calculate premium
curl -X POST "http://localhost:8004/calculate/premium" \\
     -H "Content-Type: application/json" \\
     -d '{
       "policy_type": "life_insurance",
       "sub_type": "term",
       "coverage_amount": 100000,
       "customer_age": 35,
       "risk_factors": ["smoker"]
     }'

# Process claim
curl -X POST "http://localhost:8004/calculate/claim" \\
     -H "Content-Type: application/json" \\
     -d '{
       "policy_type": "auto_insurance",
       "claim_type": "collision",
       "claim_amount": 8000,
       "policy_coverage": 50000
     }'
            </pre>
        </div>
    </body>
    </html>
    """)

@app.post("/calculate/premium")
async def calculate_premium(request: PremiumCalculationRequest):
    """Calculate insurance premium"""
    print(f"[*] Premium calculation request: {request.policy_type} - {request.sub_type}")
    
    result = PremiumCalculator.calculate_premium(
        policy_type=request.policy_type,
        sub_type=request.sub_type,
        coverage_amount=request.coverage_amount,
        customer_age=request.customer_age,
        risk_factors=request.risk_factors
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    print(f"[+] Premium calculated: ${result['premium_calculation']['monthly_premium']}/month")
    return result

@app.post("/calculate/claim")
async def calculate_claim(request: ClaimCalculationRequest):
    """Process insurance claim"""
    print(f"[*] Claim calculation request: {request.policy_type} - {request.claim_type}")
    
    result = ClaimCalculator.calculate_claim(
        policy_type=request.policy_type,
        claim_type=request.claim_type,
        claim_amount=request.claim_amount,
        policy_coverage=request.policy_coverage
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    print(f"[+] Claim processed: ${result['claim_calculation']['payout_amount']} payout")
    return result

@app.post("/chat")
async def chat_with_calculator(request: ChatRequest):
    """Chat interface for natural language calculations"""
    print(f"[*] Chat request: {request.message[:50]}...")
    
    message_lower = request.message.lower()
    
    try:
        # Simple pattern matching for demo purposes
        if "premium" in message_lower or "calculate premium" in message_lower:
            # Default premium calculation
            result = PremiumCalculator.calculate_premium(
                policy_type="life_insurance",
                sub_type="term",
                coverage_amount=100000,
                customer_age=35,
                risk_factors=[]
            )
            
            if result["success"]:
                premium = result["premium_calculation"]
                response = f"Based on a standard term life insurance policy for a 35-year-old with $100,000 coverage:\n\n"
                response += f"Monthly Premium: ${premium['monthly_premium']}\n"
                response += f"Annual Premium: ${premium['annual_premium']}\n"
                response += f"Base Rate: ${premium['base_rate']} per $1000 coverage\n"
                response += f"Age Multiplier: {premium['age_multiplier']}\n"
                response += f"Risk Multiplier: {premium['risk_multiplier']}"
                
                return ChatResponse(
                    response=response,
                    calculation_result=result,
                    service_used="MCP Premium Calculator"
                )
        
        elif "claim" in message_lower or "calculate claim" in message_lower:
            # Default claim calculation
            result = ClaimCalculator.calculate_claim(
                policy_type="auto_insurance",
                claim_type="collision",
                claim_amount=8000,
                policy_coverage=50000
            )
            
            if result["success"]:
                claim = result["claim_calculation"]
                response = f"Based on a standard auto collision claim:\n\n"
                response += f"Claim Amount: ${claim['claim_amount']}\n"
                response += f"Policy Coverage: ${claim['policy_coverage']}\n"
                response += f"Deductible: ${claim['deductible']}\n"
                response += f"Payout Amount: ${claim['payout_amount']}\n"
                response += f"Status: {claim['approval_status']}\n"
                response += f"Processing Time: {claim['processing_days']} days\n"
                response += f"Claim ID: {claim['claim_id']}"
                
                return ChatResponse(
                    response=response,
                    calculation_result=result,
                    service_used="MCP Claim Calculator"
                )
        
        else:
            response = """I can help you with insurance calculations! Try asking about:

• "Calculate premium" - I'll calculate a sample life insurance premium
• "Process claim" - I'll calculate a sample auto insurance claim

For detailed calculations, use the specific endpoints:
• POST /calculate/premium
• POST /calculate/claim

Available policy types: life_insurance, auto_insurance, health_insurance, home_insurance"""
            
            return ChatResponse(
                response=response,
                service_used="MCP Calculator Help"
            )
            
    except Exception as e:
        print(f"[-] Chat processing error: {e}")
        return ChatResponse(
            response=f"Sorry, I encountered an error processing your request: {str(e)}",
            service_used="MCP Calculator Error"
        )

@app.get("/tools")
async def get_mcp_tools():
    """Get available MCP tools"""
    return {
        "tools": mcp_tools.get_available_tools(),
        "service": "MCP Insurance Calculator",
        "version": "1.0.0"
    }

@app.post("/tools/execute")
async def execute_mcp_tool(request: MCPToolRequest):
    """Execute an MCP tool"""
    print(f"[*] Executing MCP tool: {request.tool_name}")
    
    result = await mcp_tools.execute_tool(request.tool_name, request.arguments)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Tool execution failed"))
    
    print(f"[+] MCP tool executed successfully: {request.tool_name}")
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MCP Insurance Calculator",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "available_tools": len(mcp_tools.get_available_tools())
    }

@app.get("/info")
async def service_info():
    """Get service information"""
    return {
        "service_name": "MCP Insurance Calculator",
        "version": "1.0.0",
        "description": "Model Context Protocol service for insurance calculations",
        "capabilities": [
            "Premium calculation",
            "Claim processing",
            "MCP tool execution",
            "Natural language interface"
        ],
        "supported_policies": ["life_insurance", "auto_insurance", "health_insurance", "home_insurance"],
        "endpoints": [
            "/calculate/premium",
            "/calculate/claim",
            "/chat",
            "/tools",
            "/tools/execute",
            "/health"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
