# LangGraph Agentic AI Policy Management System

An advanced agent system powered by LangGraph that uses workflow orchestration to route user queries to the most appropriate service (RAG, Database, or both) with sophisticated state management.

## Architecture

The system consists of three main services with LangGraph-powered workflow orchestration:

1. **RAG Service** (Port 8000) - PDF document content search
2. **Database Service** (Port 8001) - Structured data queries
3. **LangGraph Agentic AI Service** (Port 8002) - Intelligent query routing with workflow management

## LangGraph Workflow

The agent uses a sophisticated state-based workflow:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Analyze Intent │───▶│ Route Services  │───▶│  Query Services │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                        ┌─────────────┐        ┌─────────────────┐
                        │    RAG      │        │   Synthesize    │
                        │ DATABASE    │───────▶│   Response      │
                        │    BOTH     │        └─────────────────┘
                        └─────────────┘                  │
                                                         ▼
                                               ┌─────────────────┐
                                               │ Format Final    │
                                               │   Response      │
                                               └─────────────────┘
```

## Features

- 🤖 **LangGraph Workflow Engine**: State management and workflow orchestration
- 🔄 **Multi-Node Processing**: Separate nodes for intent analysis, routing, querying, and synthesis
- 📊 **Sophisticated Intent Analysis**: Uses Gemini LLM to understand query requirements
- 🌐 **Web Interface**: Real-time service status monitoring with LangGraph branding
- ⚡ **Concurrent Processing**: Parallel execution of multiple service queries
- 🎯 **Confidence Scoring**: Detailed reasoning for routing decisions
- 🔍 **State Tracking**: Complete workflow state management and debugging

## LangGraph Workflow Nodes

### 1. **analyze_intent**
- Analyzes user query using Gemini LLM
- Determines routing strategy (RAG/DATABASE/BOTH)
- Provides confidence scoring and reasoning

### 2. **route_to_services**
- Routes query based on intent analysis
- Sets workflow path for subsequent nodes

### 3. **query_rag / query_database / query_both**
- Executes service queries (sequential or parallel)
- Handles service communication and error management

### 4. **synthesize_response**
- Combines multiple service responses
- Uses LLM for coherent response generation

### 5. **format_final_response**
- Formats final response with metadata
- Adds workflow information and debugging data

## Setup

### Prerequisites
Ensure the following services are running:
- RAG Service on `http://localhost:8000`
- Database Service on `http://localhost:8001`

### Installation
```bash
pip install -r requirements.txt
```

### Run the Agent
```bash
python main.py
```

The agent service will start on `http://localhost:8002`

## Usage

1. Open `http://localhost:8002` in your browser
2. Enter your Gemini API key
3. Click "Initialize Agent" to check service availability
4. Start asking questions - the agent will automatically route to the best service(s)

## Agent Decision Process

1. **Intent Analysis**: Uses Gemini LLM to analyze the query and determine routing strategy
2. **Service Selection**: Routes to RAG, Database, or both services based on analysis
3. **Concurrent Execution**: When using both services, queries them simultaneously
4. **Response Synthesis**: Combines multiple responses into a coherent answer
5. **Metadata Provision**: Shows routing decisions and confidence scores

## API Endpoints

- `GET /` - Web interface
- `POST /chat` - Process queries through the agent
- `GET /health` - Health check with service status
- `GET /services/status` - Detailed service availability
- `POST /analyze` - Analyze query intent without execution

## Service Integration

The agent communicates with underlying services via HTTP:

```python
# RAG Service
POST http://localhost:8000/chat
{
    "message": "query",
    "api_key": "key",
    "chat_type": "pdf"
}

# Database Service  
POST http://localhost:8001/chat
{
    "message": "query",
    "api_key": "key"
}
```

## Configuration

The agent service runs on port 8002 by default. You can modify this in `main.py`:

```python
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
```

## Error Handling

- Graceful fallback when services are unavailable
- Detailed error reporting and logging
- Service health monitoring and status indicators
- Retry logic for transient failures

## Technology Stack

- **FastAPI**: Async web framework
- **LangGraph**: Workflow orchestration and state management
- **LangChain**: LLM integration and tooling
- **Gemini 1.5 Flash**: Intent analysis and response synthesis
- **aiohttp**: Async HTTP client for service communication
- **HTML/JavaScript**: Interactive web interface with LangGraph branding
