import os
import time
from typing import Dict, Any
from rag.loaders import kb_loader
from rag.splitter import kb_splitter
from rag.vector_store import FAISSVectorStore
from config.settings import get_settings
from config.logger import logger

settings = get_settings()


def ingest_knowledge_base(
    kb_dir: str = "data/knowledge_base",
    output_dir: str = None
) -> Dict[str, Any]:
    start_time = time.time()
    dest_dir = output_dir or settings.FAISS_INDEX_DIR
    logger.info(f"Starting knowledge base ingestion from '{kb_dir}' into '{dest_dir}'...")

    # 1. Load documents
    docs = kb_loader.load_directory(kb_dir)
    if not docs:
        logger.warning(f"No documents found in {kb_dir}!")
        return {
            "status": "empty",
            "total_documents": 0,
            "total_chunks": 0,
            "elapsed_seconds": round(time.time() - start_time, 2)
        }

    logger.info(f"Loaded {len(docs)} documents.")

    # 2. Chunk documents
    chunks = kb_splitter.split_documents(docs)
    logger.info(f"Split into {len(chunks)} cohesive chunks.")

    # 3. Embed and build vector index
    store = FAISSVectorStore()
    store.add_documents(chunks)

    # 4. Persist to disk
    store.save_local(dest_dir)

    elapsed = round(time.time() - start_time, 2)
    unique_topics = sorted(list(set(c.metadata.get("topic", "General") for c in chunks)))

    result = {
        "status": "success",
        "total_documents": len(docs),
        "total_chunks": len(chunks),
        "topics": unique_topics,
        "output_dir": dest_dir,
        "elapsed_seconds": elapsed
    }
    logger.info(f"Ingestion completed in {elapsed}s: {len(chunks)} chunks across {len(unique_topics)} topics.")
    return result
