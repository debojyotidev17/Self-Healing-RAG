import time
from typing import Dict, Any, List
from openai import OpenAI
from src.config import OPENAI_API_KEY, GENERATOR_MODEL, FINAL_CONTEXT_K
from src.retrieval.hybrid import HybridRetriever
from src.reranker.cross_encoder import CrossEncoderReranker

client = OpenAI(api_key=OPENAI_API_KEY)
retriever = HybridRetriever()
reranker = CrossEncoderReranker()

class BaselineRAG:
    """
    Standard Linear Baseline RAG Pipeline.
    Architecture: Query -> Hybrid Retrieve -> Rerank -> Generate -> Output.
    Does NOT include Critic fact-checking or query reformulation loops.
    Used for scientific benchmark comparisons against Self-Healing RAG.
    """
    def run(self, question: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # 1. Retrieval & Reranking
        candidates = retriever.search(question)
        reranked = reranker.rerank(question, candidates, top_n=FINAL_CONTEXT_K)
        
        # 2. Context Preparation
        context_blocks = []
        for idx, chunk in enumerate(reranked, start=1):
            source = chunk.get("source", "unknown")
            text = chunk.get("text", "")
            context_blocks.append(f"[{idx}] Source: {source}\n{text}")
            
        context_str = "\n\n---\n\n".join(context_blocks)
        
        system_prompt = (
            "You are an enterprise AI assistant. Answer the question using the provided context below. "
            "Include source citation numbers in square brackets [1], [2] for statement claims."
        )
        user_prompt = f"Context:\n{context_str}\n\nQuestion: {question}"

        # 3. Generation
        response = client.chat.completions.create(
            model=GENERATOR_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        answer = response.choices[0].message.content.strip()
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        # Format citations
        citations = []
        for idx, chunk in enumerate(reranked, start=1):
            citations.append({
                "citation_id": idx,
                "document_id": chunk.get("document_id", chunk.get("source", "unknown")),
                "chunk_id": chunk.get("chunk_id", "unknown"),
                "source": chunk.get("source", "unknown"),
                "relevance_score": float(chunk.get("rerank_score", chunk.get("score", 1.0)))
            })

        return {
            "question": question,
            "final_response": answer,
            "retrieved_chunks": reranked,
            "citations": citations,
            "latency_ms": elapsed_ms
        }
