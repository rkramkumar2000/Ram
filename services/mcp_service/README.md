# MCP Insurance Calculator Service

## Overview

The MCP (Model Context Protocol) Insurance Calculator Service provides premium and claim calculation capabilities using hardcoded insurance logic. This service integrates with the Policy RAG App to handle calculation-related queries.

## Features

- **Premium Calculation**: Calculate insurance premiums based on policy type, coverage amount, customer age, and risk factors
- **Claim Processing**: Process insurance claims and calculate payout amounts
- **MCP Compliance**: Follows Model Context Protocol standards for tool definitions
- **Natural Language Interface**: Chat endpoint for conversational calculations
- **Multiple Policy Types**: Supports life, auto, health, and home insurance

## Service Architecture

```
Policy RAG App
├── RAG Service (8000) - Document retrieval and analysis
├── Database Service (8003) - Structured data queries  
├── MCP Service (8004) - Premium and claim calculations
└── LangGraph Service (8002) - Intelligent routing and orchestration
```

## API Endpoints

### Core Endpoints

- `POST /calculate/premium` - Calculate insurance premium
- `POST /calculate/claim` - Process insurance claim
- `POST /chat` - Natural language calculation interface
- `GET /tools` - Get available MCP tools
- `POST /tools/execute` - Execute MCP tools
- `GET /health` - Service health check

### Example Usage

#### Premium Calculation
```bash
curl -X POST "http://localhost:8004/calculate/premium" \
     -H "Content-Type: application/json" \
     -d '{
       "policy_type": "life_insurance",
       "sub_type": "term",
       "coverage_amount": 100000,
       "customer_age": 35,
       "risk_factors": ["smoker"]
     }'
```

#### Claim Processing
```bash
curl -X POST "http://localhost:8004/calculate/claim" \
     -H "Content-Type: application/json" \
     -d '{
       "policy_type": "auto_insurance",
       "claim_type": "collision",
       "claim_amount": 8000,
       "policy_coverage": 50000
     }'
```

#### Natural Language Interface
```bash
curl -X POST "http://localhost:8004/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Calculate premium for life insurance"
     }'
```

## Supported Calculations

### Policy Types and Sub-types

**Life Insurance:**
- Term life insurance
- Whole life insurance  
- Universal life insurance

**Auto Insurance:**
- Liability coverage
- Comprehensive coverage
- Collision coverage

**Health Insurance:**
- Basic plan
- Premium plan
- Platinum plan

**Home Insurance:**
- Basic coverage
- Comprehensive coverage
- Premium coverage

### Risk Factors

- `smoker` - 1.75x premium multiplier
- `high_risk_occupation` - 1.40x premium multiplier
- `poor_health` - 1.60x premium multiplier
- `good_driver` - 0.85x premium multiplier (discount)
- `safe_neighborhood` - 0.90x premium multiplier (discount)
- `security_system` - 0.95x premium multiplier (discount)

### Age Multipliers

- 18-25: 1.50x (higher risk)
- 26-35: 1.20x
- 36-45: 1.00x (base rate)
- 46-55: 1.30x
- 56-65: 1.80x
- 66-100: 2.50x (highest risk)

## Integration with LangGraph

The MCP service is integrated into the LangGraph agentic system for intelligent routing:

- **Query Detection**: Automatically routes calculation queries to MCP service
- **Natural Language**: Accepts queries like "calculate premium" or "process claim"
- **Smart Routing**: Uses intent analysis to determine when calculations are needed
- **Response Integration**: Calculation results are integrated into conversational responses

## Sample Queries

When using the integrated system (http://localhost:8002), you can ask:

- "Calculate premium for life insurance"
- "Process a claim for auto insurance"
- "How much would insurance cost for a 35-year-old?"
- "Calculate premium"
- "Process claim"

## Configuration

The service uses hardcoded calculation logic for demonstration purposes:

```python
# Base rates (monthly premium per $1000 coverage)
BASE_RATES = {
    "life_insurance": {
        "term": 0.50,
        "whole": 2.50,
        "universal": 1.80
    }
    # ... more rates
}
```

## Installation and Setup

1. **Install Dependencies**:
   ```bash
   cd mcp_service
   pip install -r requirements.txt
   ```

2. **Start the Service**:
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload
   ```

3. **Or use the multi-service launcher**:
   ```bash
   cd ../
   python start_all_services.py
   ```

## Testing

Test the service directly:

```python
# Test premium calculation
response = requests.post("http://localhost:8004/calculate/premium", json={
    "policy_type": "life_insurance",
    "sub_type": "term", 
    "coverage_amount": 100000,
    "customer_age": 35,
    "risk_factors": []
})

# Test via chat interface  
response = requests.post("http://localhost:8004/chat", json={
    "message": "Calculate premium"
})
```

## Development Notes

- **Hardcoded Logic**: All calculations use predetermined rates and rules
- **Demo Purpose**: Designed for demonstration of MCP integration
- **Extensible**: Can be extended with real actuarial logic and external data
- **MCP Compliant**: Follows Model Context Protocol tool standards

## Files

- `main.py` - FastAPI service with endpoints
- `mcp_calculator.py` - Core calculation logic and MCP tools
- `requirements.txt` - Python dependencies

## Service Status

- **Port**: 8004
- **Status**: Running and integrated with Policy RAG App
- **Health Check**: GET /health
- **Integration**: Connected to LangGraph routing system

The MCP service is now fully integrated into your Policy RAG App ecosystem!
