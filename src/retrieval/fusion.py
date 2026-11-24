from typing import List, Dict, Any, Optional

def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    c: int = 60,
    top_k: int = 20
) -> List[Dict[str, Any]]:
    """
    Reciprocal Rank Fusion (RRF) algorithm combining vector and BM25 search rankings.
    
    Formula:
        RRF_Score(doc) = sum( 1 / (c + rank(doc)) ) across all retrieval lists.
        
    Deduplicates candidates based on text content.
    """
    rrf_scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    def process_ranking(results: List[Dict[str, Any]], method_name: str):
        for rank, doc in enumerate(results, start=1):
            text = doc["text"].strip()
            if not text:
                continue
                
            # Key doc by text fingerprint to deduplicate across methods
            doc_key = text
            
            if doc_key not in doc_map:
                doc_map[doc_key] = {
                    "document_id": doc.get("document_id", "unknown"),
                    "chunk_id": doc.get("chunk_id", "unknown"),
                    "source": doc.get("source", "unknown"),
                    "text": text,
                    "methods": [method_name],
                    "raw_scores": {method_name: doc.get("score", 0.0)}
                }
                rrf_scores[doc_key] = 0.0
            else:
                doc_map[doc_key]["methods"].append(method_name)
                doc_map[doc_key]["raw_scores"][method_name] = doc.get("score", 0.0)

            # RRF score accumulation
            rrf_scores[doc_key] += 1.0 / (c + rank)

    process_ranking(vector_results, "vector")
    process_ranking(bm25_results, "bm25")

    # Sort candidates by combined RRF score descending
    sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)[:top_k]

    fused_results = []
    for key in sorted_keys:
        item = doc_map[key]
        fused_results.append({
            "document_id": item["document_id"],
            "chunk_id": item["chunk_id"],
            "source": item["source"],
            "text": item["text"],
            "score": round(rrf_scores[key], 6),
            "method": "+".join(sorted(list(set(item["methods"]))))
        })

    return fused_results
