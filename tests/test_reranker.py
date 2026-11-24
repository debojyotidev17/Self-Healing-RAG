import pytest
from src.reranker.cross_encoder import CrossEncoderReranker

def test_cross_encoder_reranker_success_and_fallback():
    reranker = CrossEncoderReranker(enabled=True)
    candidates = [
        {"document_id": "doc1", "source": "unrelated.md", "text": "Unrelated guidelines for billing."},
        {"document_id": "doc2", "source": "stipend.md", "text": "New hires receive $1,500 equipment stipend for home office."}
    ]
    
    reranked = reranker.rerank("equipment stipend for new hires", candidates, top_n=2)
    assert len(reranked) == 2
    assert "stipend.md" in reranked[0]["source"]
    assert "rerank_score" in reranked[0]

def test_cross_encoder_disabled_fallback():
    reranker = CrossEncoderReranker(enabled=False)
    candidates = [{"text": "Sample 1"}, {"text": "Sample 2"}]
    res = reranker.rerank("query", candidates, top_n=1)
    assert len(res) == 1
    assert res[0]["text"] == "Sample 1"
