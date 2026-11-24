import os
from typing import List, Dict, Any, Optional
from langchain_chroma import Chroma
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.fusion import reciprocal_rank_fusion
from src.config import (
    RETRIEVAL_MODE,
    VECTOR_TOP_K,
    BM25_TOP_K,
    FUSED_TOP_K,
    BM25_INDEX_PATH
)
from src.ingest import get_vector_store

class HybridRetriever:
    """
    Unified Hybrid Search Retriever combining Vector Search (ChromaDB) 
    and Lexical Search (BM25) with Reciprocal Rank Fusion (RRF).
    """
    def __init__(self, mode: str = RETRIEVAL_MODE, bm25_index_path: str = BM25_INDEX_PATH):
        self.mode = mode.lower()
        self.vector_store: Chroma = get_vector_store()
        
        self.bm25_retriever: Optional[BM25Retriever] = None
        if os.path.exists(bm25_index_path):
            self.bm25_retriever = BM25Retriever(index_path=bm25_index_path)

    def search_vector(self, query: str, top_k: int = VECTOR_TOP_K) -> List[Dict[str, Any]]:
        """Executes vector similarity search in ChromaDB."""
        docs = self.vector_store.similarity_search_with_relevance_scores(query, k=top_k)
        
        results = []
        for rank, item in enumerate(docs):
            # doc, score tuple
            if isinstance(item, tuple):
                doc, score = item
            else:
                doc = item
                score = 1.0 / (rank + 1)
                
            source_file = doc.metadata.get("source", "unknown")
            chunk_id = doc.metadata.get("chunk_id", f"{source_file}_chunk_{rank}")
            doc_id = doc.metadata.get("doc_id", source_file)
            
            results.append({
                "document_id": doc_id,
                "chunk_id": chunk_id,
                "source": source_file,
                "text": doc.page_content,
                "score": float(score),
                "method": "vector"
            })
            
        return results

    def search_bm25(self, query: str, top_k: int = BM25_TOP_K) -> List[Dict[str, Any]]:
        """Executes lexical search using BM25 index."""
        if not self.bm25_retriever:
            return []
        return self.bm25_retriever.search(query, top_k=top_k)

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Main retrieval method dispatching based on configured mode (hybrid, vector, or bm25).
        """
        if self.mode == "vector":
            return self.search_vector(query, top_k=FUSED_TOP_K)
        elif self.mode == "bm25":
            return self.search_bm25(query, top_k=FUSED_TOP_K)
        else: # Default: hybrid
            vec_res = self.search_vector(query, top_k=VECTOR_TOP_K)
            bm25_res = self.search_bm25(query, top_k=BM25_TOP_K)
            
            if not bm25_res:
                return vec_res[:FUSED_TOP_K]
            if not vec_res:
                return bm25_res[:FUSED_TOP_K]
                
            return reciprocal_rank_fusion(
                vector_results=vec_res,
                bm25_results=bm25_res,
                top_k=FUSED_TOP_K
            )
