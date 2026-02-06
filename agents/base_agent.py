"""
Base Agent class for AI Operations Assistant
All agents must inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from llm.gemini_client import GeminiClient


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, llm_client: GeminiClient):
        """
        Initialize agent with LLM client
        
        Args:
            llm_client: Configured Gemini client instance
        """
        self.llm = llm_client
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name identifier"""
        pass
    
    @property
    @abstractmethod
    def role(self) -> str:
        """Agent role description"""
        pass
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and return result
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Processed result
        """
        pass
