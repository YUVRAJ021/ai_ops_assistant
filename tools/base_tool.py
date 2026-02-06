"""
Base Tool class for AI Operations Assistant
All tools must inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """Abstract base class for all tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters
        
        Returns:
            Dict containing:
                - success: bool
                - data: Any (result data)
                - error: Optional[str] (error message if failed)
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for LLM context"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
