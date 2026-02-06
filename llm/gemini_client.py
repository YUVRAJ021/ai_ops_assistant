"""
Gemini LLM Client for AI Operations Assistant
Handles all LLM interactions with Google's Gemini API
"""

import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
from typing import Optional, Dict, Any


class GeminiClient:
    """Client for interacting with Google Gemini API"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-flash-lite-latest"):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google API key for Gemini
            model_name: Model to use (default: gemini-2.0-flash)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
    
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Generate text response from Gemini
        
        Args:
            prompt: User prompt
            system_instruction: Optional system instruction
            
        Returns:
            Generated text response
        """
        try:
            if system_instruction:
                model = genai.GenerativeModel(
                    self.model_name,
                    system_instruction=system_instruction
                )
                response = model.generate_content(prompt)
            else:
                response = self.model.generate_content(prompt)
            
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate JSON response from Gemini
        
        Args:
            prompt: User prompt
            system_instruction: Optional system instruction
            
        Returns:
            Parsed JSON response
        """
        full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON, no markdown or extra text."
        
        response = self.generate(full_prompt, system_instruction)
        
        # Clean up response - remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse: {response}")
