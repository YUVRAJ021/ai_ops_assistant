#!/usr/bin/env python3
"""
AI Operations Assistant - Main Entry Point
Supports API (FastAPI), CLI, and interactive modes
"""

import os
import sys
import json
import argparse
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from llm.gemini_client import GeminiClient
from tools.github_tool import GitHubTool
from tools.weather_tool import WeatherTool
from agents.planner_agent import PlannerAgent
from agents.executor_agent import ExecutorAgent
from agents.verifier_agent import VerifierAgent


class AIOperationsAssistant:
    """Main orchestrator for the AI Operations Assistant"""
    
    def __init__(self, gemini_api_key: str, github_token: Optional[str] = None):
        """
        Initialize the AI Operations Assistant
        
        Args:
            gemini_api_key: Google Gemini API key
            github_token: Optional GitHub personal access token
        """
        # Initialize LLM client
        self.llm = GeminiClient(gemini_api_key)
        
        # Initialize tools
        self.tools = [
            GitHubTool(token=github_token),
            WeatherTool()
        ]
        
        # Initialize agents
        self.planner = PlannerAgent(self.llm, self.tools)
        self.executor = ExecutorAgent(self.llm, self.tools)
        self.verifier = VerifierAgent(self.llm)
    
    def process_task(self, task: str, verbose: bool = False) -> dict:
        """
        Process a natural language task through the multi-agent pipeline
        
        Args:
            task: Natural language task description
            verbose: If True, print intermediate steps
            
        Returns:
            Dict containing the final response and metadata
        """
        result = {
            "task": task,
            "success": False,
            "response": None,
            "plan": None,
            "execution_results": None,
            "error": None
        }
        
        try:
            # Step 1: Planning
            if verbose:
                print("\n" + "="*60)
                print("🤖 PLANNER AGENT")
                print("="*60)
                print(f"Task: {task}\n")
                print("Creating execution plan...")
            
            plan_result = self.planner.process({"task": task})
            
            if not plan_result["success"]:
                result["error"] = f"Planning failed: {plan_result['error']}"
                return result
            
            result["plan"] = plan_result["plan"]
            
            if verbose:
                print("\n✅ Plan created:")
                print(json.dumps(plan_result["plan"], indent=2))
            
            # Step 2: Execution
            if verbose:
                print("\n" + "="*60)
                print("⚡ EXECUTOR AGENT")
                print("="*60)
                print("Executing plan steps...\n")
            
            exec_result = self.executor.process({"plan": plan_result["plan"]})
            result["execution_results"] = exec_result["results"]
            
            if verbose:
                for step_result in exec_result["results"]:
                    status = "✅" if step_result["success"] else "❌"
                    print(f"  {status} Step {step_result['step_number']}: {step_result['description']}")
                    if not step_result["success"]:
                        print(f"     Error: {step_result['error']}")
            
            # Step 3: Verification
            if verbose:
                print("\n" + "="*60)
                print("✔️  VERIFIER AGENT")
                print("="*60)
                print("Verifying and formatting results...\n")
            
            verify_result = self.verifier.process({
                "original_task": task,
                "plan": plan_result["plan"],
                "results": exec_result["results"]
            })
            
            result["success"] = verify_result["success"]
            result["response"] = verify_result["final_response"]
            
            if verbose:
                print("\n" + "="*60)
                print("📋 FINAL RESPONSE")
                print("="*60)
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result


# ============================================
# FastAPI Application
# ============================================

def create_api_app():
    """Create FastAPI application"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
    import os
    
    app = FastAPI(
        title="AI Operations Assistant",
        description="Multi-agent AI assistant for executing natural language tasks",
        version="1.0.0"
    )
    
    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Get the directory where main.py is located
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    
    class TaskRequest(BaseModel):
        task: str
        verbose: bool = False
    
    class TaskResponse(BaseModel):
        success: bool
        task: str
        response: Optional[str] = None
        error: Optional[str] = None
        plan: Optional[dict] = None
        execution_results: Optional[list] = None
    
    @app.get("/")
    def root():
        """Serve the main UI"""
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    
    @app.get("/api")
    def api_info():
        return {
            "name": "AI Operations Assistant",
            "version": "1.0.0",
            "endpoints": {
                "POST /task": "Submit a natural language task",
                "GET /health": "Health check",
                "GET /tools": "List available tools"
            }
        }
    
    @app.get("/health")
    def health():
        return {"status": "healthy"}
    
    @app.get("/tools")
    def list_tools():
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            return {"error": "GEMINI_API_KEY not configured"}
        
        assistant = AIOperationsAssistant(gemini_key)
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
                for tool in assistant.tools
            ]
        }
    
    @app.post("/task", response_model=TaskResponse)
    def process_task(request: TaskRequest):
        gemini_key = os.getenv("GEMINI_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        
        if not gemini_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
        
        try:
            assistant = AIOperationsAssistant(gemini_key, github_token)
            result = assistant.process_task(request.task, request.verbose)
            return TaskResponse(**result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


# ============================================
# CLI Interface
# ============================================

def run_cli():
    """Run the CLI interface"""
    parser = argparse.ArgumentParser(
        description="AI Operations Assistant - Execute natural language tasks using AI agents"
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="Task to execute (if not provided, enters interactive mode)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed execution steps"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start the API server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        print("Please set it in your .env file or environment")
        sys.exit(1)
    
    github_token = os.getenv("GITHUB_TOKEN")
    
    if args.api:
        # Start API server
        import uvicorn
        print(f"🚀 Starting AI Operations Assistant API on port {args.port}...")
        app = create_api_app()
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    elif args.task:
        # Single task mode
        assistant = AIOperationsAssistant(gemini_key, github_token)
        result = assistant.process_task(args.task, verbose=args.verbose)
        
        if result["success"]:
            print(result["response"])
        else:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
    else:
        # Interactive mode
        print("="*60)
        print("🤖 AI Operations Assistant - Interactive Mode")
        print("="*60)
        print("\nAvailable tools: GitHub (search repos, get user info), Weather (current & forecast)")
        print("Type 'quit' or 'exit' to stop, 'help' for examples\n")
        
        assistant = AIOperationsAssistant(gemini_key, github_token)
        
        while True:
            try:
                task = input("📝 Enter your task: ").strip()
                
                if not task:
                    continue
                
                if task.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break
                
                if task.lower() == "help":
                    print_help()
                    continue
                
                result = assistant.process_task(task, verbose=True)
                
                if result["success"]:
                    print("\n" + result["response"])
                else:
                    print(f"\n❌ Error: {result['error']}")
                
                print("\n" + "-"*60 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break


def print_help():
    """Print help information"""
    print("""
📚 Example Tasks:
-----------------
• "Find the top 5 Python web frameworks on GitHub"
• "What's the weather in New York and London?"
• "Get information about the tensorflow repository on GitHub"
• "Search for machine learning repositories with more than 10000 stars"
• "What's the weather forecast for Tokyo?"
• "Tell me about user 'torvalds' on GitHub and the weather in Helsinki"

💡 Tips:
---------
• Be specific about what you want
• You can combine multiple requests
• The assistant will break down complex tasks into steps
""")


if __name__ == "__main__":
    run_cli()
