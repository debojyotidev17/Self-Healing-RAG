import logging
from typing import List, Dict, Any, Optional
from src.reranker.base import BaseReranker
from src.config import RERANKER_MODEL, RERANKER_ENABLED

logger = logging.getLogger(__name__)

class CrossEncoderReranker(BaseReranker):
    """
    Cross-Encoder Reranker using sentence-transformers CrossEncoder.
    Includes graceful fallback if model fails to load or execute.
    """
    def __init__(self, model_name: str = RERANKER_MODEL, enabled: bool = RERANKER_ENABLED):
        self.model_name = model_name
        self.enabled = enabled
        self.model = None
        self._init_failed = False

    def _load_model(self):
        if self.model is None and not self._init_failed and self.enabled:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading CrossEncoder model: {self.model_name}")
                self.model = CrossEncoder(self.model_name)
            except Exception as e:
                logger.warning(f"Failed to load CrossEncoder model '{self.model_name}': {e}. Falling back to fused retrieval order.")
                self._init_failed = True

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_n: int = 4) -> List[Dict[str, Any]]:
        if not documents:
            return []
            
        if not self.enabled:
            return documents[:top_n]
            
        self._load_model()
        
        if self.model is None:
            # Graceful Fallback to input document ordering
            return documents[:top_n]
            
        try:
            pairs = [[query, doc["text"]] for doc in documents]
            scores = self.model.predict(pairs)
            
            # Attach scores and sort
            scored_docs = []
            for doc, score in zip(documents, scores):
                doc_copy = dict(doc)
                doc_copy["rerank_score"] = float(score)
                scored_docs.append(doc_copy)
                
            scored_docs.sort(key=lambda d: d["rerank_score"], reverse=True)
            return scored_docs[:top_n]
        except Exception as e:
            logger.warning(f"Reranking execution failed: {e}. Falling back to fused retrieval order.")
            return documents[:top_n]
