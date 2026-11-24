import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in .env file.")

# LLM & Embedding Models
GENERATOR_MODEL = os.getenv("GENERATOR_MODEL", "gpt-4o-mini")
CRITIC_MODEL = os.getenv("CRITIC_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Vector & BM25 Store Directories
CHROMA_PERSIST_DIR = str(BASE_DIR / "data" / "chroma_db")
CHROMA_COLLECTION_NAME = "self_healing_rag"
BM25_INDEX_PATH = str(BASE_DIR / "data" / "bm25_index.pkl")
SOURCE_DOCS_DIR = str(BASE_DIR / "data" / "source_docs")

# Retrieval & Fusion Settings
RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "hybrid")  # hybrid | vector | bm25
VECTOR_TOP_K = int(os.getenv("VECTOR_TOP_K", 20))
BM25_TOP_K = int(os.getenv("BM25_TOP_K", 20))
FUSED_TOP_K = int(os.getenv("FUSED_TOP_K", 20))

# Reranker Settings
RERANKER_ENABLED = os.getenv("RERANKER_ENABLED", "true").lower() == "true"
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RERANKER_TOP_N = int(os.getenv("RERANKER_TOP_N", 20))
FINAL_CONTEXT_K = int(os.getenv("FINAL_CONTEXT_K", 4))

# Pipeline Safety & Retry Caps
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 2))

# Redis Caching Settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", 86400))  # 24 hours
