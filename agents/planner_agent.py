"""
Planner Agent for AI Operations Assistant
Converts user input into a step-by-step plan and selects tools
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from llm.gemini_client import GeminiClient
from tools.base_tool import BaseTool


class PlannerAgent(BaseAgent):
    """Agent responsible for planning and task decomposition"""
    
    def __init__(self, llm_client: GeminiClient, available_tools: List[BaseTool]):
        """
        Initialize Planner Agent
        
        Args:
            llm_client: Configured Gemini client
            available_tools: List of available tools for planning
        """
        super().__init__(llm_client)
        self.tools = {tool.name: tool for tool in available_tools}
    
    @property
    def name(self) -> str:
        return "Planner"
    
    @property
    def role(self) -> str:
        return "Analyzes user tasks and creates step-by-step execution plans with tool selection"
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user task and create execution plan
        
        Args:
            input_data: Dict containing 'task' key with user's natural language request
            
        Returns:
            Dict containing:
                - success: bool
                - plan: List of steps with tool assignments
                - error: Optional error message
        """
        task = input_data.get("task", "")
        
        if not task:
            return {
                "success": False,
                "plan": None,
                "error": "No task provided"
            }
        
        # Build tool descriptions for the prompt
        tool_descriptions = self._build_tool_descriptions()
        
        # Create planning prompt
        system_instruction = """You are a task planning agent. Your job is to analyze user requests and create detailed execution plans.

You must respond with a valid JSON object containing a plan with steps.

Each step must include:
- step_number: Sequential number starting from 1
- description: What this step does
- tool: Name of the tool to use (must be one of the available tools)
- parameters: Object with parameters for the tool

Be precise and use only the available tools. Break complex tasks into smaller steps."""

        prompt = f"""User Task: {task}

Available Tools:
{tool_descriptions}

Create a step-by-step plan to accomplish this task. Respond with JSON in this exact format:
{{
    "task_understanding": "Brief explanation of what the user wants",
    "steps": [
        {{
            "step_number": 1,
            "description": "Description of what this step does",
            "tool": "tool_name",
            "parameters": {{
                "param1": "value1"
            }}
        }}
    ],
    "expected_output": "What the final result should contain"
}}"""

        try:
            plan = self.llm.generate_json(prompt, system_instruction)
            
            # Validate the plan
            validation_result = self._validate_plan(plan)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "plan": None,
                    "error": validation_result["error"]
                }
            
            return {
                "success": True,
                "plan": plan,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "plan": None,
                "error": f"Planning failed: {str(e)}"
            }
    
    def _build_tool_descriptions(self) -> str:
        """Build formatted tool descriptions for the prompt"""
        descriptions = []
        for name, tool in self.tools.items():
            desc = f"""Tool: {name}
Description: {tool.description}
Parameters: {tool.parameters}
"""
            descriptions.append(desc)
        return "\n".join(descriptions)
    
    def _validate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated plan"""
        if not isinstance(plan, dict):
            return {"valid": False, "error": "Plan is not a valid object"}
        
        if "steps" not in plan:
            return {"valid": False, "error": "Plan has no steps"}
        
        steps = plan.get("steps", [])
        if not steps:
            return {"valid": False, "error": "Plan has empty steps"}
        
        for i, step in enumerate(steps):
            if "tool" not in step:
                return {"valid": False, "error": f"Step {i+1} has no tool specified"}
            
            tool_name = step["tool"]
            if tool_name not in self.tools:
                return {"valid": False, "error": f"Step {i+1} uses unknown tool: {tool_name}"}
            
            if "parameters" not in step:
                return {"valid": False, "error": f"Step {i+1} has no parameters"}
        
        return {"valid": True, "error": None}
