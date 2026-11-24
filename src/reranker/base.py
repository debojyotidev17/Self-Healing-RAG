from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseReranker(ABC):
    """Abstract interface for Reranker stage."""
    
    @abstractmethod
    def rerank(self, query: str, documents: List[Dict[str, Any]], top_n: int = 4) -> List[Dict[str, Any]]:
        """
        Rerank candidate document dictionaries given a query.
        Returns top_n ranked documents with updated relevance scores.
        """
        pass
