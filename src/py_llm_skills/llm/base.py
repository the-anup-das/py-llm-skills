from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        pass

    @abstractmethod
    def chat_completion_with_structure(self, messages: List[Dict[str, str]], response_model: Type[T]) -> T:
        """
        Get a structured response compatible with the given Pydantic model.
        """
        pass
