@echo off
cd /d "C:\Users\rkram\OneDrive\Desktop\policy_rag_app\agentic_ai_app"
echo Starting LangGraph AI Service...
python -m uvicorn main:app --host 0.0.0.0 --port 8002
pause
