import os
import pickle
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

def simple_tokenize(text: str) -> List[str]:
    """Simple lowercase word tokenizer for BM25 indexing."""
    return re.findall(r"\w+", text.lower())

class BM25Retriever:
    """
    Lightweight local BM25 lexical retriever.
    Builds and persists a BM25Okapi index over document chunks.
    """
    def __init__(self, index_path: Optional[str] = None):
        self.index_path = index_path
        self.documents: List[Document] = []
        self.bm25: Optional[BM25Okapi] = None
        self.corpus_tokens: List[List[str]] = []
        
        if index_path and os.path.exists(index_path):
            self.load_index(index_path)

    def build_index(self, documents: List[Document], save_path: Optional[str] = None):
        """Build BM25 index from a list of Document objects."""
        self.documents = documents
        self.corpus_tokens = [simple_tokenize(doc.page_content) for doc in documents]
        self.bm25 = BM25Okapi(self.corpus_tokens)
        
        if save_path:
            self.save_index(save_path)

    def save_index(self, path: str):
        """Serialize BM25 index and document metadata to pickle file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "corpus_tokens": self.corpus_tokens
            }, f)
        self.index_path = path

    def load_index(self, path: str):
        """Load BM25 index from pickle file."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.corpus_tokens = data["corpus_tokens"]
            self.bm25 = BM25Okapi(self.corpus_tokens)
        self.index_path = path

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Execute BM25 search for query.
        Returns top_k result dictionaries containing text, metadata, score, and method.
        """
        if not self.bm25 or not self.documents:
            return []

        query_tokens = simple_tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        
        # Sort indices by score descending
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            doc = self.documents[idx]
            source_file = doc.metadata.get("source", "unknown")
            chunk_id = doc.metadata.get("chunk_id", f"{source_file}_chunk_{idx}")
            doc_id = doc.metadata.get("doc_id", source_file)
            
            results.append({
                "document_id": doc_id,
                "chunk_id": chunk_id,
                "source": source_file,
                "text": doc.page_content,
                "score": score,
                "method": "bm25"
            })
            
        return results
