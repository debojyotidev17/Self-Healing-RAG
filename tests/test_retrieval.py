import pytest
from langchain_core.documents import Document
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.fusion import reciprocal_rank_fusion
from src.retrieval.hybrid import HybridRetriever

def test_bm25_retrieval_and_empty_query():
    docs = [
        Document(page_content="AcroCorp equipment stipend is $1500 for new hires.", metadata={"source": "policy.md"}),
        Document(page_content="Meal reimbursement limit is $75 per day during travel.", metadata={"source": "travel.md"})
    ]
    retriever = BM25Retriever()
    retriever.build_index(docs)
    
    res = retriever.search("equipment stipend", top_k=2)
    assert len(res) >= 1
    assert "policy.md" in res[0]["source"]
    
    empty_res = retriever.search("", top_k=2)
    assert empty_res == []

def test_reciprocal_rank_fusion_and_deduplication():
    vec_res = [
        {"document_id": "doc1", "chunk_id": "c1", "source": "doc1.md", "text": "Same text snippet", "score": 0.9},
        {"document_id": "doc2", "chunk_id": "c2", "source": "doc2.md", "text": "Unique text snippet", "score": 0.8}
    ]
    bm25_res = [
        {"document_id": "doc1", "chunk_id": "c1", "source": "doc1.md", "text": "Same text snippet", "score": 10.5}
    ]
    
    fused = reciprocal_rank_fusion(vec_res, bm25_res, top_k=5)
    assert len(fused) == 2
    # Top fused candidate should be the deduplicated "Same text snippet" with methods "bm25+vector"
    assert fused[0]["text"] == "Same text snippet"
    assert "bm25" in fused[0]["method"]
    assert "vector" in fused[0]["method"]

def test_hybrid_retriever_modes():
    retriever = HybridRetriever(mode="hybrid")
    res = retriever.search("PTO days full-time employees")
    assert isinstance(res, list)
    assert len(res) > 0
