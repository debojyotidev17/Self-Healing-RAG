import json
import time
import uuid
import logging
from typing import Dict, Any, List
from openai import OpenAI
from src.state import RAGState, Citation
from src.config import (
    OPENAI_API_KEY,
    GENERATOR_MODEL,
    CRITIC_MODEL,
    FINAL_CONTEXT_K,
    RERANKER_TOP_N
)
from src.retrieval.hybrid import HybridRetriever
from src.reranker.cross_encoder import CrossEncoderReranker

logger = logging.getLogger(__name__)

# Initialize OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# Singletons for Retriever & Reranker
hybrid_retriever = HybridRetriever()
cross_reranker = CrossEncoderReranker()

def retrieve_node(state: RAGState) -> Dict[str, Any]:
    """
    Executes Hybrid Retrieval (Vector + BM25 + RRF Fusion) and CrossEncoder Reranking.
    Tracks queries_attempted to prevent duplicate retrieval loops.
    """
    start_time = time.time()
    active_query = state.get("reformulated_query") or state["question"]
    queries_attempted = list(state.get("queries_attempted", []))
    
    if active_query not in queries_attempted:
        queries_attempted.append(active_query)

    # 1. Hybrid Search (Vector + Lexical BM25 + RRF)
    retrieval_start = time.time()
    fused_candidates = hybrid_retriever.search(active_query)
    retrieval_ms = round((time.time() - retrieval_start) * 1000, 2)

    # 2. CrossEncoder Reranking
    rerank_start = time.time()
    reranked_chunks = cross_reranker.rerank(
        query=active_query,
        documents=fused_candidates,
        top_n=FINAL_CONTEXT_K
    )
    reranking_ms = round((time.time() - rerank_start) * 1000, 2)

    total_retrieval_ms = round((time.time() - start_time) * 1000, 2)

    trace_entry = (
        f"🔍 [Retrieve & Rerank] Retrieved {len(fused_candidates)} fused candidates, "
        f"reranked top-{len(reranked_chunks)} chunks for query: '{active_query}' "
        f"(Retrieval: {retrieval_ms}ms, Rerank: {reranking_ms}ms)"
    )
    
    current_trace = list(state.get("trace_log", []))
    current_trace.append(trace_entry)

    # Initialize or update latency breakdown
    trace_info = state.get("trace_info") or {
        "trace_id": str(uuid.uuid4())[:8],
        "latency_ms": {
            "retrieval_ms": 0.0,
            "reranking_ms": 0.0,
            "generation_ms": 0.0,
            "critique_ms": 0.0,
            "reformulation_ms": 0.0,
            "total_ms": 0.0
        },
        "retry_count": state.get("retry_count", 0),
        "grounded": False,
        "fallback": False,
        "cache_hit": False
    }
    
    trace_info["latency_ms"]["retrieval_ms"] += retrieval_ms
    trace_info["latency_ms"]["reranking_ms"] += reranking_ms

    return {
        "queries_attempted": queries_attempted,
        "retrieved_chunks": reranked_chunks,
        "trace_log": current_trace,
        "trace_info": trace_info
    }

def generate_node(state: RAGState) -> Dict[str, Any]:
    """
    Generates an answer based strictly on retrieved context with citation markers [1], [2].
    """
    start_time = time.time()
    chunks = state.get("retrieved_chunks", [])
    
    # Format numbered context snippets for claim-level citation
    context_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        source = chunk.get("source", "unknown")
        text = chunk.get("text", "")
        context_blocks.append(f"[{idx}] Source: {source}\n{text}")
        
    context_str = "\n\n---\n\n".join(context_blocks)
    question = state["question"]

    system_prompt = (
        "You are an accurate enterprise AI assistant. Answer the question ONLY using the provided context below. "
        "Every factual statement in your answer MUST include source citation numbers in square brackets, e.g. [1], [2], corresponding to the provided sources.\n"
        "If the context does not contain enough information to answer the question confidently, explicitly say: "
        "'I don't have enough information in the provided context.' Do not use outside knowledge or fabricate citations."
    )

    user_prompt = f"Retrieved Context:\n{context_str}\n\nQuestion: {question}"

    response = client.chat.completions.create(
        model=GENERATOR_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0
    )

    answer = response.choices[0].message.content.strip()
    generation_ms = round((time.time() - start_time) * 1000, 2)

    trace_entry = (
        f"✍️ [Generate] Candidate answer generated ({generation_ms}ms): "
        f"'{answer[:100]}...'" if len(answer) > 100 else f"✍️ [Generate] Candidate answer generated ({generation_ms}ms): '{answer}'"
    )
    
    current_trace = list(state.get("trace_log", []))
    current_trace.append(trace_entry)

    trace_info = state.get("trace_info", {})
    if "latency_ms" in trace_info:
        trace_info["latency_ms"]["generation_ms"] += generation_ms

    return {
        "answer": answer,
        "trace_log": current_trace,
        "trace_info": trace_info
    }

def critique_node(state: RAGState) -> Dict[str, Any]:
    """
    Independent LLM fact-checker validating answer grounding.
    Includes robust structured JSON validation and malformed error handling.
    """
    start_time = time.time()
    chunks = state.get("retrieved_chunks", [])
    context_str = "\n\n---\n\n".join([f"Source: {c.get('source', 'unknown')}\n{c.get('text', '')}" for c in chunks])
    answer = state.get("answer", "")
    question = state["question"]

    # Short-circuit check for explicit unanswerable fallback statement
    if "don't have enough information" in answer.lower():
        critique_ms = round((time.time() - start_time) * 1000, 2)
        trace_entry = f"✅ [Critique] Passed fact-check! (Generator correctly declared lack of context)."
        current_trace = list(state.get("trace_log", []))
        current_trace.append(trace_entry)
        
        trace_info = state.get("trace_info", {})
        if "latency_ms" in trace_info:
            trace_info["latency_ms"]["critique_ms"] += critique_ms

        return {
            "critique_grounded": True,
            "critique_reasoning": "Generator acknowledged missing context.",
            "critique_confidence": 1.0,
            "critique_unsupported_claims": [],
            "trace_log": current_trace,
            "trace_info": trace_info
        }

    system_prompt = (
        "You are a strict fact-checker. Given the retrieved context and the candidate answer, "
        "determine if EVERY factual claim in the answer is directly supported by the context. "
        "Do not be lenient. If the answer contains any claim not in the context, mark grounded=false "
        "and list the unsupported claims.\n\n"
        "You MUST respond ONLY with a JSON object matching this exact schema:\n"
        "{\n"
        '  "grounded": boolean,\n'
        '  "reasoning": "string explanation",\n'
        '  "confidence": float between 0.0 and 1.0,\n'
        '  "unsupported_claims": ["list", "of", "unsupported", "claims"]\n'
        "}"
    )

    user_prompt = f"Question: {question}\n\nRetrieved Context:\n{context_str}\n\nCandidate Answer:\n{answer}"

    try:
        response = client.chat.completions.create(
            model=CRITIC_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        raw_content = response.choices[0].message.content.strip()
        critique_data = json.loads(raw_content)
        
        grounded = bool(critique_data.get("grounded", False))
        reasoning = str(critique_data.get("reasoning", "No reasoning provided."))
        confidence = float(critique_data.get("confidence", 0.5))
        unsupported = list(critique_data.get("unsupported_claims", []))
    except Exception as e:
        logger.warning(f"Critic parsing or API failure ({e}). Safely marking grounded=False.")
        grounded = False
        reasoning = f"Critic JSON parsing exception: {str(e)}"
        confidence = 0.0
        unsupported = ["Malformed critic response"]

    critique_ms = round((time.time() - start_time) * 1000, 2)

    if grounded:
        trace_entry = f"✅ [Critique] Passed fact-check! Grounded=True (Confidence: {confidence:.2f}, Time: {critique_ms}ms)"
    else:
        trace_entry = f"⚠️ [Critique] Failed fact-check! Grounded=False (Confidence: {confidence:.2f}, Time: {critique_ms}ms). Reason: {reasoning}"

    current_trace = list(state.get("trace_log", []))
    current_trace.append(trace_entry)

    trace_info = state.get("trace_info", {})
    if "latency_ms" in trace_info:
        trace_info["latency_ms"]["critique_ms"] += critique_ms

    return {
        "critique_grounded": grounded,
        "critique_reasoning": reasoning,
        "critique_confidence": confidence,
        "critique_unsupported_claims": unsupported,
        "trace_log": current_trace,
        "trace_info": trace_info
    }

def reformulate_node(state: RAGState) -> Dict[str, Any]:
    """
    Intelligent query reformulator.
    Generates optimized search query and detects duplicate queries to prevent loops.
    """
    start_time = time.time()
    reasoning = state.get("critique_reasoning", "Lacked required details.")
    unsupported = state.get("critique_unsupported_claims", [])
    original_question = state["question"]
    current_retry = state.get("retry_count", 0) + 1
    queries_attempted = list(state.get("queries_attempted", []))

    system_prompt = (
        "You are an expert search query optimizer for enterprise documentation. "
        "Your job is to rewrite search queries to retrieve better matching factual documents without changing user intent."
    )

    user_prompt = (
        f"Original User Question: {original_question}\n"
        f"Critique Rejection Reason: {reasoning}\n"
        f"Unsupported Claims: {', '.join(unsupported)}\n\n"
        "Rewrite the search query to target key terminology and missing documentation. "
        "Return ONLY the rewritten query text, nothing else."
    )

    response = client.chat.completions.create(
        model=GENERATOR_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    reformulated_query = response.choices[0].message.content.strip().strip('"').strip("'")
    reformulation_ms = round((time.time() - start_time) * 1000, 2)

    # Prevent repeated identical queries
    if reformulated_query in queries_attempted:
        logger.info(f"Duplicate query detected ('{reformulated_query}'). Forcing max_retries to terminate loop.")
        trace_entry = f"🔄 [Reformulate] Duplicate query detected ('{reformulated_query}'). Proceeding to fallback."
        current_retry = state.get("max_retries", 2)
    else:
        trace_entry = f"🔄 [Reformulate] Retry {current_retry}/{state['max_retries']}: Rewrote query to '{reformulated_query}' ({reformulation_ms}ms)"

    current_trace = list(state.get("trace_log", []))
    current_trace.append(trace_entry)

    trace_info = state.get("trace_info", {})
    if "latency_ms" in trace_info:
        trace_info["latency_ms"]["reformulation_ms"] += reformulation_ms

    return {
        "reformulated_query": reformulated_query,
        "retry_count": current_retry,
        "trace_log": current_trace,
        "trace_info": trace_info
    }

def fallback_node(state: RAGState) -> Dict[str, Any]:
    """
    Hardcoded safe response executed when retries are exhausted or grounding fails.
    Does NOT call the LLM.
    """
    fallback_response = "I don't have enough information in the available documents to answer this confidently."
    trace_entry = f"🛑 [Fallback] Max retries ({state['max_retries']}) reached. Outputting safe fallback response."
    
    current_trace = list(state.get("trace_log", []))
    current_trace.append(trace_entry)

    trace_info = state.get("trace_info", {})
    trace_info["fallback"] = True
    trace_info["grounded"] = False

    return {
        "final_response": fallback_response,
        "citations": [],
        "trace_log": current_trace,
        "trace_info": trace_info
    }

def finalize_node(state: RAGState) -> Dict[str, Any]:
    """
    Finalizes grounded response and maps source document citations.
    """
    answer = state.get("answer", "")
    chunks = state.get("retrieved_chunks", [])
    
    # Generate structured citation provenance objects
    citations: List[Citation] = []
    for idx, chunk in enumerate(chunks, start=1):
        source = chunk.get("source", "unknown")
        doc_id = chunk.get("document_id", source)
        chunk_id = chunk.get("chunk_id", f"{source}_chunk_{idx}")
        score = float(chunk.get("rerank_score", chunk.get("score", 1.0)))
        
        citations.append({
            "citation_id": idx,
            "document_id": doc_id,
            "chunk_id": chunk_id,
            "source": source,
            "relevance_score": round(score, 4)
        })

    trace_entry = f"🎉 [Finalize] Answer verified as grounded with {len(citations)} source citations."
    current_trace = list(state.get("trace_log", []))
    current_trace.append(trace_entry)

    trace_info = state.get("trace_info", {})
    trace_info["grounded"] = True
    trace_info["fallback"] = False

    return {
        "final_response": answer,
        "citations": citations,
        "trace_log": current_trace,
        "trace_info": trace_info
    }
