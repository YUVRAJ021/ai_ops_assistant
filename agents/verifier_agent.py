"""
Verifier Agent for AI Operations Assistant
Validates results and formats final output
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from llm.gemini_client import GeminiClient


class VerifierAgent(BaseAgent):
    """Agent responsible for verifying and formatting results"""
    
    def __init__(self, llm_client: GeminiClient):
        """
        Initialize Verifier Agent
        
        Args:
            llm_client: Configured Gemini client
        """
        super().__init__(llm_client)
    
    @property
    def name(self) -> str:
        return "Verifier"
    
    @property
    def role(self) -> str:
        return "Validates execution results and formats final output for the user"
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify and format execution results
        
        Args:
            input_data: Dict containing:
                - original_task: The user's original request
                - plan: The execution plan
                - results: Results from executor
                
        Returns:
            Dict containing:
                - success: bool
                - final_response: Formatted response for user
                - issues: List of any issues found
                - error: Optional error message
        """
        original_task = input_data.get("original_task", "")
        plan = input_data.get("plan", {})
        results = input_data.get("results", [])
        
        # Analyze completeness
        analysis = self._analyze_completeness(plan, results)
        
        # Generate final formatted response using LLM
        final_response = self._generate_final_response(
            original_task, plan, results, analysis
        )
        
        return {
            "success": analysis["complete"],
            "final_response": final_response,
            "issues": analysis["issues"],
            "raw_results": results,
            "error": None if analysis["complete"] else "Some data may be incomplete"
        }
    
    def _analyze_completeness(self, plan: Dict[str, Any], results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze if execution results are complete"""
        issues = []
        successful_steps = 0
        total_steps = len(results)
        
        for result in results:
            if result.get("success"):
                successful_steps += 1
            else:
                issues.append({
                    "step": result.get("step_number"),
                    "description": result.get("description"),
                    "error": result.get("error")
                })
        
        return {
            "complete": successful_steps == total_steps,
            "successful_steps": successful_steps,
            "total_steps": total_steps,
            "success_rate": (successful_steps / total_steps * 100) if total_steps > 0 else 0,
            "issues": issues
        }
    
    def _generate_final_response(
        self,
        original_task: str,
        plan: Dict[str, Any],
        results: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> str:
        """Generate a well-formatted final response using LLM"""
        
        system_instruction = """You are a response formatting agent. Your job is to take raw execution results and create a clear, well-formatted response for the user.

Guidelines:
- Be concise but comprehensive
- Highlight key information
- Use clear formatting (bullet points, sections)
- If there were failures, explain what happened
- Make the response easy to understand"""

        # Build results summary for LLM
        results_summary = self._build_results_summary(results)
        
        prompt = f"""Original Task: {original_task}

Task Understanding: {plan.get('task_understanding', 'N/A')}
Expected Output: {plan.get('expected_output', 'N/A')}

Execution Results:
{results_summary}

Analysis:
- Success Rate: {analysis['success_rate']:.1f}%
- Completed: {analysis['successful_steps']}/{analysis['total_steps']} steps
- Issues: {len(analysis['issues'])}

Please create a clear, formatted response that:
1. Summarizes what was requested
2. Presents the key findings/data
3. Notes any issues or incomplete data
4. Is easy for a human to read and understand

Format the response nicely with sections and bullet points where appropriate."""

        try:
            response = self.llm.generate(prompt, system_instruction)
            return response
        except Exception as e:
            # Fallback to basic formatting if LLM fails
            return self._fallback_format(original_task, results, analysis)
    
    def _build_results_summary(self, results: List[Dict[str, Any]]) -> str:
        """Build a text summary of results for the LLM"""
        summary_parts = []
        
        for result in results:
            status = "✓" if result.get("success") else "✗"
            step_num = result.get("step_number", "?")
            desc = result.get("description", "No description")
            
            part = f"Step {step_num} [{status}]: {desc}"
            
            if result.get("success") and result.get("data"):
                # Include relevant data (truncated if too long)
                data_str = str(result["data"])
                if len(data_str) > 500:
                    data_str = data_str[:500] + "..."
                part += f"\n  Data: {data_str}"
            elif not result.get("success"):
                part += f"\n  Error: {result.get('error', 'Unknown error')}"
            
            summary_parts.append(part)
        
        return "\n\n".join(summary_parts)
    
    def _fallback_format(
        self,
        original_task: str,
        results: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> str:
        """Fallback formatting if LLM fails"""
        lines = [
            "=" * 50,
            "AI Operations Assistant - Results",
            "=" * 50,
            "",
            f"Task: {original_task}",
            "",
            f"Status: {'Complete' if analysis['complete'] else 'Partial'}",
            f"Success Rate: {analysis['success_rate']:.1f}%",
            "",
            "Results:",
            "-" * 30
        ]
        
        for result in results:
            status = "SUCCESS" if result.get("success") else "FAILED"
            lines.append(f"\nStep {result.get('step_number')}: {result.get('description')}")
            lines.append(f"Status: {status}")
            
            if result.get("success") and result.get("data"):
                lines.append(f"Data: {result.get('data')}")
            elif not result.get("success"):
                lines.append(f"Error: {result.get('error')}")
        
        if analysis["issues"]:
            lines.extend(["", "Issues:", "-" * 30])
            for issue in analysis["issues"]:
                lines.append(f"- Step {issue['step']}: {issue['error']}")
        
        return "\n".join(lines)
