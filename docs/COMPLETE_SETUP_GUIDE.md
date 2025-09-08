# Policy Management System - Complete Setup Guide

## Overview

I have successfully created a complete policy management system with three separate applications:

1. **PDF RAG App** (Port 8000) - Chat with PDF documents
2. **Database Chat App** (Port 8001) - Natural language database queries  
3. **Agentic AI App** (Port 8002) - Intelligent routing between services

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   PDF RAG Service   │    │ Database Chat Service│    │   Agentic AI        │
│   Port 8000         │    │   Port 8001         │    │   Port 8002         │
│                     │    │                     │    │                     │
│ • PDF Processing    │    │ • PostgreSQL        │    │ • Query Analysis    │
│ • Vector Search     │    │ • Text-to-SQL       │    │ • Service Routing   │
│ • Document Chat     │    │ • Natural Language  │    │ • Response Synthesis│
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
          │                          │                          │
          └─────────────────────────┐│┌─────────────────────────┘
                                   ↓│↓
                            ┌─────────────────────┐
                            │  Gemini 1.5 Flash  │
                            │   (LLM Backend)     │
                            └─────────────────────┘
```

## Quick Start

### 1. PDF RAG Application (Port 8000)
```bash
cd "c:\Users\rkram\OneDrive\Desktop\policy_rag_app"
python main.py
```
- **URL**: http://localhost:8000
- **Purpose**: Chat with PDF document content
- **Features**: Document chunking, vector search, contextual answers

### 2. Database Chat Application (Port 8001)
```bash
cd "c:\Users\rkram\OneDrive\Desktop\policy_rag_app\db_chat_app"
python main.py
```
- **URL**: http://localhost:8001
- **Purpose**: Natural language queries to PostgreSQL database
- **Features**: Text-to-SQL conversion, schema introspection, query execution

### 3. Agentic AI Application (Port 8002)
```bash
cd "c:\Users\rkram\OneDrive\Desktop\policy_rag_app\agentic_ai_app"
python main.py
```
- **URL**: http://localhost:8002
- **Purpose**: Intelligent routing between RAG and Database services
- **Features**: Intent analysis, multi-service orchestration, response synthesis

## Database Setup (Required for DB Chat and Agent)

### PostgreSQL Schema
```sql
CREATE TABLE policies (
    policy_number VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(100),
    status VARCHAR(20),
    pdf_path VARCHAR(255)
);

-- Sample data
INSERT INTO policies VALUES 
('POL001', 'John Smith', 'active', '/path/to/policy1.pdf'),
('POL002', 'Jane Doe', 'pending', '/path/to/policy2.pdf'),
('POL003', 'Bob Johnson', 'expired', '/path/to/policy3.pdf');
```

### Environment Variables (.env)
Create `.env` files in both `db_chat_app` and the main directory:
```env
# Database Configuration
DB_USER=postgres
DB_PASS=ram
DB_HOST=localhost
DB_PORT=5432
DB_NAME=insurance_db

# Optional: Gemini API Key (can be entered at runtime)
GOOGLE_API_KEY=your_gemini_api_key
```

## Usage Examples

### PDF RAG Service Queries
- "What does the policy cover?"
- "Explain the terms and conditions"
- "What are the exclusions?"
- "Tell me about the policy benefits"

### Database Service Queries
- "How many active policies do we have?"
- "List all customers with pending policies"
- "Find policies for John Smith"
- "Show me all expired policies"

### Agentic AI Queries (Hybrid)
- "Show me John Smith's policies and explain their coverage" (Routes to BOTH)
- "List all active policies and their key terms" (Routes to BOTH)
- "How many policies mention 'accident'?" (Routes to appropriate service)

## Technical Stack

- **Backend**: FastAPI with async support
- **AI/LLM**: Google Gemini 1.5 Flash
- **Database**: PostgreSQL with SQLAlchemy
- **Vector Store**: FAISS with sentence-transformers
- **Document Processing**: LangChain + PyPDF
- **Frontend**: HTML/JavaScript with runtime API key input
- **Communication**: HTTP REST APIs + aiohttp for service-to-service

## Key Features

### 1. Runtime API Key Configuration
- All apps support entering API key through web interface
- No need to restart services when changing API keys
- Secure handling with password-masked input

### 2. Intelligent Query Routing (Agentic AI)
- **RAG Routing**: Document content, explanations, policy details
- **Database Routing**: Structured queries, counts, filtering, customer lookup
- **Hybrid Routing**: Queries needing both structured data AND content

### 3. Service Health Monitoring
- Real-time service status indicators
- Automatic service discovery and health checks
- Graceful degradation when services are unavailable

### 4. Advanced Query Processing
- **Text-to-SQL**: Natural language to PostgreSQL conversion
- **Vector Search**: Semantic similarity matching for documents
- **Response Synthesis**: Combining multiple service responses

## File Structure

```
policy_rag_app/
├── main.py                 # PDF RAG service
├── rag_system.py          # Document processing logic
├── requirements.txt       # Dependencies
├── .env                   # Configuration
├── static/
│   ├── index.html         # Web interface
│   └── simple.html        # Alternative interface
├── vectorstore/           # FAISS vector database
├── db_chat_app/           # Standalone database chat
│   ├── main.py
│   ├── db_chat_system.py
│   ├── requirements.txt
│   ├── .env
│   └── static/index.html
└── agentic_ai_app/        # Intelligent agent system
    ├── main.py
    ├── agent_system.py
    ├── requirements.txt
    └── static/index.html
```

## Troubleshooting

### Common Issues
1. **API Key Errors**: Use runtime API key entry instead of environment variables
2. **Database Connection**: Ensure PostgreSQL is running and credentials are correct
3. **Service Communication**: Start services in order: RAG (8000) → Database (8001) → Agent (8002)
4. **Port Conflicts**: Check if ports 8000, 8001, 8002 are available

### Dependency Installation
Each app has its own `requirements.txt`. Install dependencies:
```bash
pip install -r requirements.txt
```

## Next Steps

1. Start all three services
2. Configure your database connection in `.env` files
3. Access the Agentic AI interface at http://localhost:8002
4. Enter your Gemini API key and start querying!

The system is now fully modular with clean separation of concerns and intelligent query routing capabilities.
