import time
import uuid
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.state import RAGState
from src.config import MAX_RETRIES
from src.nodes import (
    retrieve_node,
    generate_node,
    critique_node,
    reformulate_node,
    fallback_node,
    finalize_node
)
from src.cache.redis_cache import RedisCache

# Singleton Redis Cache instance
redis_cache = RedisCache()

def route_after_critique(state: RAGState) -> str:
    """
    Conditional routing function evaluating critique verdict and retry count.
    
    Routes:
        'end': If critique_grounded is True -> move to finalize -> END.
        'reformulate': If critique_grounded is False AND retry_count < max_retries -> move to reformulate -> retrieve.
        'fallback': If critique_grounded is False AND retry_count >= max_retries -> move to fallback -> END.
    """
    if state.get("critique_grounded", False):
        return "end"
    elif state.get("retry_count", 0) < state.get("max_retries", MAX_RETRIES):
        return "reformulate"
    else:
        return "fallback"

def build_graph() -> StateGraph:
    """
    Builds and compiles the stateful LangGraph for Self-Healing RAG.
    
    Graph Topology:
        retrieve -> generate -> critique -> conditional_router
                                                ├── 'end' -> finalize -> END
                                                ├── 'reformulate' -> reformulate -> retrieve (CYCLE)
                                                └── 'fallback' -> fallback -> END
    """
    builder = StateGraph(RAGState)
    
    # 1. Add all nodes
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("generate", generate_node)
    builder.add_node("critique", critique_node)
    builder.add_node("reformulate", reformulate_node)
    builder.add_node("fallback", fallback_node)
    builder.add_node("finalize", finalize_node)
    
    # 2. Set entry point
    builder.set_entry_point("retrieve")
    
    # 3. Add deterministic edges
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", "critique")
    
    # 4. Add conditional edges after critique
    builder.add_conditional_edges(
        "critique",
        route_after_critique,
        {
            "end": "finalize",
            "reformulate": "reformulate",
            "fallback": "fallback"
        }
    )
    
    # 5. Add loop back edge from reformulate to retrieve (CYCLE)
    builder.add_edge("reformulate", "retrieve")
    
    # 6. Add terminal edges to END
    builder.add_edge("finalize", END)
    builder.add_edge("fallback", END)
    
    return builder.compile()

# Singleton compiled graph instance
graph_app = build_graph()

def run_self_healing_rag(question: str, max_retries: int = MAX_RETRIES, use_cache: bool = True) -> RAGState:
    """
    Helper function to invoke the self-healing RAG graph with observability and Redis semantic caching.
    """
    start_total = time.time()
    
    # 1. Check Redis Cache
    if use_cache:
        cached_result = redis_cache.get(question)
        if cached_result:
            cached_result["trace_log"] = list(cached_result.get("trace_log", [])) + ["⚡ [Cache] Returned response from Redis semantic cache."]
            if "trace_info" in cached_result and cached_result["trace_info"]:
                cached_result["trace_info"]["cache_hit"] = True
            return cached_result

    # 2. Initial State Setup
    trace_id = str(uuid.uuid4())[:8]
    initial_state: RAGState = {
        "question": question,
        "reformulated_query": None,
        "queries_attempted": [],
        "retrieved_chunks": [],
        "answer": None,
        "critique_grounded": None,
        "critique_reasoning": None,
        "critique_confidence": None,
        "critique_unsupported_claims": [],
        "retry_count": 0,
        "max_retries": max_retries,
        "final_response": None,
        "citations": [],
        "trace_log": [f"🚀 [Start] Processing question: '{question}' (Trace ID: {trace_id}, Max Retries: {max_retries})"],
        "trace_info": {
            "trace_id": trace_id,
            "latency_ms": {
                "retrieval_ms": 0.0,
                "reranking_ms": 0.0,
                "generation_ms": 0.0,
                "critique_ms": 0.0,
                "reformulation_ms": 0.0,
                "total_ms": 0.0
            },
            "retry_count": 0,
            "grounded": False,
            "fallback": False,
            "cache_hit": False
        }
    }
    
    # 3. Invoke LangGraph
    final_output = graph_app.invoke(initial_state)
    
    # 4. Calculate total latency
    total_ms = round((time.time() - start_total) * 1000, 2)
    if "trace_info" in final_output and final_output["trace_info"]:
        final_output["trace_info"]["latency_ms"]["total_ms"] = total_ms
        final_output["trace_info"]["retry_count"] = final_output.get("retry_count", 0)

    # 5. Store in Redis Cache if grounded
    if use_cache and final_output.get("critique_grounded", False) and not final_output.get("trace_info", {}).get("fallback", False):
        redis_cache.set(question, final_output)
        
    return final_output

if __name__ == "__main__":
    print("=== Testing Upgraded Production Self-Healing RAG Graph ===")
    test_q = "What is the equipment stipend for new hires at AcroCorp?"
    res = run_self_healing_rag(test_q)
    print("\n--- Final Response ---")
    print(res.get("final_response"))
    print("\n--- Citations ---")
    print(res.get("citations"))
    print("\n--- Trace Info ---")
    print(res.get("trace_info"))
