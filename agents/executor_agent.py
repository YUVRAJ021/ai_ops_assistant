"""
Executor Agent for AI Operations Assistant
Executes planned steps and calls APIs
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from llm.gemini_client import GeminiClient
from tools.base_tool import BaseTool


class ExecutorAgent(BaseAgent):
    """Agent responsible for executing planned steps"""
    
    MAX_RETRIES = 3
    
    def __init__(self, llm_client: GeminiClient, available_tools: List[BaseTool]):
        """
        Initialize Executor Agent
        
        Args:
            llm_client: Configured Gemini client
            available_tools: List of available tools for execution
        """
        super().__init__(llm_client)
        self.tools = {tool.name: tool for tool in available_tools}
    
    @property
    def name(self) -> str:
        return "Executor"
    
    @property
    def role(self) -> str:
        return "Executes planned steps by calling appropriate tools and APIs"
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the plan steps
        
        Args:
            input_data: Dict containing 'plan' with steps to execute
            
        Returns:
            Dict containing:
                - success: bool
                - results: List of step results
                - error: Optional error message
        """
        plan = input_data.get("plan", {})
        steps = plan.get("steps", [])
        
        if not steps:
            return {
                "success": False,
                "results": [],
                "error": "No steps to execute"
            }
        
        results = []
        all_successful = True
        
        for step in steps:
            step_result = self._execute_step(step)
            results.append(step_result)
            
            if not step_result["success"]:
                all_successful = False
                # Continue with other steps even if one fails
        
        return {
            "success": all_successful,
            "results": results,
            "plan_context": {
                "task_understanding": plan.get("task_understanding", ""),
                "expected_output": plan.get("expected_output", "")
            },
            "error": None if all_successful else "Some steps failed"
        }
    
    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step with retry logic"""
        step_number = step.get("step_number", "?")
        description = step.get("description", "No description")
        tool_name = step.get("tool", "")
        parameters = step.get("parameters", {})
        
        if tool_name not in self.tools:
            return {
                "step_number": step_number,
                "description": description,
                "tool": tool_name,
                "success": False,
                "data": None,
                "error": f"Unknown tool: {tool_name}"
            }
        
        tool = self.tools[tool_name]
        last_error = None
        
        # Retry logic
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                result = tool.execute(**parameters)
                
                if result.get("success"):
                    return {
                        "step_number": step_number,
                        "description": description,
                        "tool": tool_name,
                        "success": True,
                        "data": result.get("data"),
                        "error": None
                    }
                else:
                    last_error = result.get("error", "Unknown error")
                    
            except Exception as e:
                last_error = str(e)
            
            # Log retry attempt
            if attempt < self.MAX_RETRIES:
                print(f"  Retry {attempt}/{self.MAX_RETRIES} for step {step_number}...")
        
        # All retries failed
        return {
            "step_number": step_number,
            "description": description,
            "tool": tool_name,
            "success": False,
            "data": None,
            "error": f"Failed after {self.MAX_RETRIES} attempts: {last_error}"
        }
