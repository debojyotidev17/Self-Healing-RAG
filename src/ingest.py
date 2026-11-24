import os
from pathlib import Path
from typing import List, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    SOURCE_DOCS_DIR
)

def load_documents(source_dir: str) -> List[Document]:
    """Load all .txt and .md files from source_docs directory."""
    documents = []
    source_path = Path(source_dir)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory '{source_dir}' does not exist.")
        
    for file_path in source_path.glob("*"):
        if file_path.suffix.lower() in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                doc = Document(
                    page_content=content,
                    metadata={"source": file_path.name}
                )
                documents.append(doc)
                
    return documents

def process_and_embed_documents() -> Tuple[int, int]:
    """Reads source docs, splits into chunks, embeds and persists to Chroma DB."""
    raw_documents = load_documents(SOURCE_DOCS_DIR)
    
    if not raw_documents:
        print(f"No .txt or .md documents found in '{SOURCE_DOCS_DIR}'.")
        return 0, 0

    # Recursive Character Text Splitter (500 chars/tokens, 50 overlap)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents(raw_documents)
    
    # Initialize OpenAI Embeddings model
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY
    )
    
    # Create or update persistent Chroma database
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR
    )
    
    # Build and persist BM25 lexical index
    from src.retrieval.bm25 import BM25Retriever
    from src.config import BM25_INDEX_PATH
    
    bm25_builder = BM25Retriever()
    bm25_builder.build_index(chunks, save_path=BM25_INDEX_PATH)
    print(f"BM25 Lexical Index persisted to: '{BM25_INDEX_PATH}'")
    
    return len(raw_documents), len(chunks)

def get_vector_store() -> Chroma:
    """Helper function to load the persistent Chroma vector store."""
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY
    )
    return Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )

if __name__ == "__main__":
    print(f"Starting ingestion from '{SOURCE_DOCS_DIR}'...")
    num_files, num_chunks = process_and_embed_documents()
    print(f"\n--- Ingestion Complete ---")
    print(f"Files Processed: {num_files}")
    print(f"Chunks Created:  {num_chunks}")
    print(f"Chroma DB stored at: '{CHROMA_PERSIST_DIR}'")
