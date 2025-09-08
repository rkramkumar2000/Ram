import subprocess
import time
import os

def start_service(name, command, cwd=None):
    print(f"🚀 Starting {name}...")
    try:
        process = subprocess.Popen(command, shell=True, cwd=cwd)
        print(f"✅ {name} started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None

def main():
    print("=" * 60)
    print("🎯 Starting All Policy RAG App Services")
    print("=" * 60)
    
    base_dir = r"c:\Users\rkram\OneDrive\Desktop\policy_rag_app"
    
    services = [
        {
            "name": "RAG Service (Port 8000)",
            "command": "python -m uvicorn main:app --host 127.0.0.1 --port 8000",
            "cwd": os.path.join(base_dir, "services", "rag_service")
        },
        {
            "name": "Database Service (Port 8003)", 
            "command": "python -m uvicorn main:app --host 127.0.0.1 --port 8003",
            "cwd": os.path.join(base_dir, "services", "database_service")
        },
        {
            "name": "MCP Service (Port 8006)",
            "command": "python -m uvicorn main:app --host 127.0.0.1 --port 8006", 
            "cwd": os.path.join(base_dir, "services", "mcp_service")
        },
        {
            "name": "LangGraph Service (Port 8007)",
            "command": "python -m uvicorn main:app --host 127.0.0.1 --port 8007",
            "cwd": os.path.join(base_dir, "services", "langgraph_service") 
        }
    ]
    
    processes = []
    
    for service in services:
        process = start_service(service["name"], service["command"], service["cwd"])
        if process:
            processes.append(process)
        time.sleep(2)  # Wait between services
    
    print("\n" + "=" * 60)
    print(f"✅ Started {len(processes)} services successfully!")
    print("=" * 60)
    print("📍 Service URLs:")
    print("   • RAG Service: http://127.0.0.1:8000")
    print("   • Database Service: http://127.0.0.1:8003") 
    print("   • MCP Service: http://127.0.0.1:8006")
    print("   • LangGraph Service: http://127.0.0.1:8007")
    print("\n🧪 Test the system at: http://127.0.0.1:8007")
    print("\n⏳ Press Ctrl+C to stop all services...")
    
    try:
        # Keep script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()
