import pytest
from src.graph import run_self_healing_rag

def test_answerable_question_graph_execution():
    res = run_self_healing_rag("What is the equipment stipend for new hires at AcroCorp?", max_retries=2, use_cache=False)
    assert res.get("critique_grounded") is True
    assert "1,500" in res.get("final_response", "")
    assert len(res.get("citations", [])) >= 1
    assert res.get("retry_count", 0) <= 2

def test_unanswerable_question_fallback_execution():
    res = run_self_healing_rag("What is AcroCorp's pet-friendly office policy in Seattle?", max_retries=2, use_cache=False)
    assert "don't have enough information" in res.get("final_response", "").lower() or res.get("trace_info", {}).get("fallback") is True
