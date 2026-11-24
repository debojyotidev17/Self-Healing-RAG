import numpy as np
from typing import List, Dict, Any

def calculate_mrr(retrieved_sources: List[str], expected_sources: List[str]) -> float:
    """Calculates Mean Reciprocal Rank (MRR) for retrieved document sources."""
    if not expected_sources or not retrieved_sources:
        return 0.0
    for rank, src in enumerate(retrieved_sources, start=1):
        if any(exp.lower() in src.lower() for exp in expected_sources):
            return 1.0 / rank
    return 0.0

def calculate_recall_at_k(retrieved_sources: List[str], expected_sources: List[str]) -> float:
    """Calculates Recall@K for retrieved document sources."""
    if not expected_sources:
        return 1.0
    if not retrieved_sources:
        return 0.0
    matched = 0
    for exp in expected_sources:
        if any(exp.lower() in src.lower() for src in retrieved_sources):
            matched += 1
    return matched / len(expected_sources)

def calculate_precision_at_k(retrieved_sources: List[str], expected_sources: List[str]) -> float:
    """Calculates Precision@K for retrieved document sources."""
    if not retrieved_sources:
        return 0.0
    if not expected_sources:
        return 0.0
    matched = 0
    for src in retrieved_sources:
        if any(exp.lower() in src.lower() for exp in expected_sources):
            matched += 1
    return matched / len(retrieved_sources)

def calculate_percentiles(values: List[float]) -> Dict[str, float]:
    """Calculates average, p50, and p95 for a list of numerical values."""
    if not values:
        return {"avg": 0.0, "p50": 0.0, "p95": 0.0}
    arr = np.array(values)
    return {
        "avg": float(np.mean(arr)),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95))
    }

def estimate_cost(total_tokens: int) -> float:
    """Estimates OpenAI gpt-4o-mini cost based on token counts (~$0.0003 per 1k tokens)."""
    return round((total_tokens / 1000.0) * 0.0003, 5)
