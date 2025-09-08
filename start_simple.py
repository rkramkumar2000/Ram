#!/usr/bin/env python3
import subprocess
import time
import sys
import os

def start_service(name, directory, command, port):
    """Start a service in a specific directory"""
    print(f"Starting {name}...")
    try:
        # Change to service directory and start
        full_command = f"cd {directory} && {command}"
        process = subprocess.Popen(
            full_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Wait a bit for service to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"✅ {name} started successfully on port {port}")
            return process
        else:
            print(f"❌ {name} failed to start")
            if process.stdout:
                output = process.stdout.read()
                print(f"Error: {output}")
            return None
    except Exception as e:
        print(f"❌ Error starting {name}: {e}")
        return None

def main():
    print("🚀 Starting MCP System (Simple)")
    print("="*50)
    
    # Define services
    mcp_dir = r"c:\Users\rkram\OneDrive\Desktop\policy_rag_app\mcp_service"
    langgraph_dir = r"c:\Users\rkram\OneDrive\Desktop\policy_rag_app\agentic_ai_app"
    
    processes = []
    
    # Start MCP service
    mcp_process = start_service(
        "MCP Calculator",
        mcp_dir,
        "python -m uvicorn main:app --host 0.0.0.0 --port 8006",
        8006
    )
    if mcp_process:
        processes.append(mcp_process)
    
    # Start LangGraph service
    langgraph_process = start_service(
        "LangGraph Router", 
        langgraph_dir,
        "python -m uvicorn main:app --host 0.0.0.0 --port 8007",
        8007
    )
    if langgraph_process:
        processes.append(langgraph_process)
    
    if not processes:
        print("❌ No services started successfully")
        return
    
    print(f"\n✅ Started {len(processes)} services")
    print("\n📍 Access Points:")
    print("   • Web Interface: http://localhost:8007")
    print("   • MCP API: http://localhost:8006")
    print("\n🧪 Test: Calculate premium for life insurance for a 35-year-old")
    print("\n⏳ Press Ctrl+C to stop all services...")
    
    # Keep services running
    try:
        while True:
            time.sleep(1)
            # Check if any process died
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"⚠️ Service {i+1} stopped unexpectedly")
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down all services...")
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()
