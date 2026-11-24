import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from src.graph import run_self_healing_rag
from src.eval.baseline import BaselineRAG
from src.config import MAX_RETRIES

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Production Self-Healing RAG API",
    description="Enterprise API exposing a stateful Self-Healing RAG engine with Hybrid Retrieval, Cross-Encoder Reranking, Redis Caching, and Tracing.",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

baseline_rag = BaselineRAG()

class CitationModel(BaseModel):
    citation_id: int
    document_id: str
    chunk_id: str
    source: str
    relevance_score: float

class LatencyBreakdownModel(BaseModel):
    retrieval_ms: float
    reranking_ms: float
    generation_ms: float
    critique_ms: float
    reformulation_ms: float
    total_ms: float

class TraceInfoModel(BaseModel):
    trace_id: str
    latency_ms: LatencyBreakdownModel
    retry_count: int
    grounded: bool
    fallback: bool
    cache_hit: bool

class AskRequest(BaseModel):
    question: str = Field(..., description="Query question to process.", min_length=1)
    max_retries: int = Field(default=MAX_RETRIES, description="Maximum allowed retries before fallback.", ge=0, le=5)
    use_cache: bool = Field(default=True, description="Whether to check/populate Redis semantic cache.")
    mode: str = Field(default="self_healing", description="Execution mode: 'self_healing' or 'baseline'.")

class AskResponse(BaseModel):
    final_response: str = Field(..., description="The verified grounded response or safe fallback message.")
    grounded: bool = Field(..., description="Whether response passed critic fact-check.")
    retry_count: int = Field(..., description="Total reformulation retries executed.")
    fallback: bool = Field(..., description="Whether response fell back to safety message.")
    citations: List[CitationModel] = Field(default=[], description="Structured source citations.")
    trace_log: List[str] = Field(default=[], description="Human-readable step execution log.")
    trace: Optional[TraceInfoModel] = Field(default=None, description="Observability trace ID and latency breakdown.")

@app.get("/")
def read_root():
    return {
        "service": "Self-Healing RAG Engine",
        "status": "operational",
        "version": "2.0.0",
        "retrieval_mode": "hybrid",
        "reranker": "enabled"
    }

@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """
    Executes a query through the Self-Healing RAG pipeline or Baseline linear pipeline.
    """
    cleaned_q = request.question.strip()
    if not cleaned_q:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question string cannot be empty or whitespace only."
        )

    try:
        if request.mode == "baseline":
            base_res = baseline_rag.run(cleaned_q)
            unanswerable_triggers = ["don't have enough information", "do not have enough information"]
            is_fallback = any(t in base_res["final_response"].lower() for t in unanswerable_triggers)
            
            return AskResponse(
                final_response=base_res["final_response"],
                grounded=not is_fallback,
                retry_count=0,
                fallback=is_fallback,
                citations=[CitationModel(**c) for c in base_res["citations"]],
                trace_log=["🚀 [Baseline] Executed linear pipeline (Retrieve -> Rerank -> Generate)."],
                trace=TraceInfoModel(
                    trace_id="baseline",
                    latency_ms=LatencyBreakdownModel(
                        retrieval_ms=0.0,
                        reranking_ms=0.0,
                        generation_ms=base_res["latency_ms"],
                        critique_ms=0.0,
                        reformulation_ms=0.0,
                        total_ms=base_res["latency_ms"]
                    ),
                    retry_count=0,
                    grounded=not is_fallback,
                    fallback=is_fallback,
                    cache_hit=False
                )
            )

        # Self-Healing Mode
        effective_max_retries = min(request.max_retries, 2)
        result_state = run_self_healing_rag(
            question=cleaned_q,
            max_retries=effective_max_retries,
            use_cache=request.use_cache
        )

        final_response = result_state.get("final_response") or "No response generated."
        grounded = bool(result_state.get("critique_grounded", False))
        retry_count = int(result_state.get("retry_count", 0))
        trace_log = result_state.get("trace_log", [])
        raw_citations = result_state.get("citations", [])
        raw_trace = result_state.get("trace_info") or {}

        is_fallback = raw_trace.get("fallback", not grounded)

        citations_models = [CitationModel(**c) for c in raw_citations]
        
        trace_model = None
        if raw_trace and "latency_ms" in raw_trace:
            lat = raw_trace["latency_ms"]
            trace_model = TraceInfoModel(
                trace_id=str(raw_trace.get("trace_id", "unknown")),
                latency_ms=LatencyBreakdownModel(
                    retrieval_ms=float(lat.get("retrieval_ms", 0.0)),
                    reranking_ms=float(lat.get("reranking_ms", 0.0)),
                    generation_ms=float(lat.get("generation_ms", 0.0)),
                    critique_ms=float(lat.get("critique_ms", 0.0)),
                    reformulation_ms=float(lat.get("reformulation_ms", 0.0)),
                    total_ms=float(lat.get("total_ms", 0.0))
                ),
                retry_count=retry_count,
                grounded=grounded,
                fallback=is_fallback,
                cache_hit=bool(raw_trace.get("cache_hit", False))
            )

        return AskResponse(
            final_response=final_response,
            grounded=grounded,
            retry_count=retry_count,
            fallback=is_fallback,
            citations=citations_models,
            trace_log=trace_log,
            trace=trace_model
        )

    except Exception as e:
        logger.error(f"API endpoint execution exception: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Self-Healing RAG execution error: {str(e)}"
        )
