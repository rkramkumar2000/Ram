# Policy RAG App - Refactored Structure

## 🏗️ **New Organized Structure**

```
policy_rag_app/
├── 📁 config/                     # Configuration files
│   ├── .env                       # Environment variables
│   └── settings.py               # Centralized settings
├── 📁 services/                  # All microservices
│   ├── 📁 rag_service/           # PDF RAG service (Port 8000)
│   │   ├── main.py
│   │   ├── rag_system.py
│   │   └── static/
│   ├── 📁 database_service/      # Database chat (Port 8003)
│   │   ├── main.py
│   │   ├── db_chat_system.py
│   │   ├── .env
│   │   └── static/
│   ├── 📁 mcp_service/           # MCP calculator (Port 8006)
│   │   ├── main.py
│   │   └── mcp_calculator.py
│   └── 📁 langgraph_service/     # LangGraph agent (Port 8007)
│       ├── main.py
│       ├── agent_system.py
│       ├── langgraph_agent_system.py
│       └── static/
├── 📁 shared/                    # Shared resources
│   └── 📁 static/               # Common UI files
│       ├── index.html           # Main dashboard
│       ├── database.html
│       └── langgraph.html
├── 📁 data/                     # Data storage
│   └── 📁 vectorstore/          # Vector database files
├── 📁 scripts/                  # Management scripts
│   └── start_all_services_fixed.py
├── 📁 docs/                     # Documentation
│   ├── README.md
│   └── COMPLETE_SETUP_GUIDE.md
└── requirements.txt             # Root dependencies
```

## 🚀 **How to Start Services**

### Quick Start (All Services)
```bash
cd c:\Users\rkram\OneDrive\Desktop\policy_rag_app
python scripts\start_all_services_fixed.py
```

### Individual Services
```bash
# RAG Service
cd services\rag_service
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Database Service  
cd services\database_service
python -m uvicorn main:app --host 127.0.0.1 --port 8003

# MCP Service
cd services\mcp_service
python -m uvicorn main:app --host 127.0.0.1 --port 8006

# LangGraph Service
cd services\langgraph_service
python -m uvicorn main:app --host 127.0.0.1 --port 8007
```

## 🎯 **Service URLs**
- **Main Dashboard**: `http://localhost:8000/static/` (from any service)
- **RAG Service**: `http://localhost:8000`
- **Database Service**: `http://localhost:8003`
- **MCP Service**: `http://localhost:8006/docs`
- **LangGraph Agent**: `http://localhost:8007`

## 📋 **Benefits of New Structure**

### ✅ **Better Organization**
- Clear separation of concerns
- Each service is self-contained
- Shared resources properly organized
- Configuration centralized

### ✅ **Improved Maintainability**
- Easier to find and modify code
- Independent service development
- Cleaner import paths
- Better version control

### ✅ **Enhanced Scalability**
- Services can be deployed independently
- Easy to add new services
- Better resource management
- Microservices architecture ready

### ✅ **Development Benefits**
- Consistent project structure
- Shared utilities and configurations
- Better documentation organization
- Easier testing and debugging

## 🔧 **Configuration**

The new structure uses a centralized configuration system:
- **Environment variables**: `config/.env`
- **Settings**: `config/settings.py`
- **Shared paths**: Automatically configured via `settings.py`

## 📊 **Migration Notes**

All file paths have been updated to work with the new structure:
- ✅ Vectorstore paths updated
- ✅ Static file paths updated  
- ✅ Environment file paths updated
- ✅ Service startup paths updated

## 🎨 **New Dashboard**

The main dashboard (`shared/static/index.html`) provides:
- Real-time service health monitoring
- Quick access to all services
- Clean, modern interface
- Service status indicators

This refactored structure follows microservices best practices and makes the Policy RAG App more professional, maintainable, and scalable!
