"""
Configuration settings for Policy RAG App
"""
import os
from pathlib import Path

# Base directory - root of the project
BASE_DIR = Path(__file__).parent.parent

# Service directories
SERVICES_DIR = BASE_DIR / "services"
RAG_SERVICE_DIR = SERVICES_DIR / "rag_service"
DATABASE_SERVICE_DIR = SERVICES_DIR / "database_service"
MCP_SERVICE_DIR = SERVICES_DIR / "mcp_service"
LANGGRAPH_SERVICE_DIR = SERVICES_DIR / "langgraph_service"

# Shared directories
SHARED_DIR = BASE_DIR / "shared"
STATIC_DIR = SHARED_DIR / "static"

# Data directories
DATA_DIR = BASE_DIR / "data"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"

# Config directory
CONFIG_DIR = BASE_DIR / "config"

# Ensure directories exist
for directory in [DATA_DIR, VECTORSTORE_DIR, STATIC_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Service ports
SERVICE_PORTS = {
    "rag": 8000,
    "database": 8003,
    "mcp": 8006,
    "langgraph": 8007
}

# Environment file path
ENV_FILE = CONFIG_DIR / ".env"
