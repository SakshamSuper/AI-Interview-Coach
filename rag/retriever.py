import os
from typing import List, Tuple, Dict, Any, Optional
from langchain_core.documents import Document
from rag.vector_store import vector_store
from config.settings import get_settings
from config.logger import logger

settings = get_settings()


class InterviewRAGRetriever:
    """Retriever for querying the technical knowledge base with thresholding and metadata formatting."""

    def __init__(self, vs=None):
        self.vector_store = vs or vector_store
        # Automatically load index if directory exists and index is not yet initialized
        if self.vector_store.index is None and os.path.exists(settings.FAISS_INDEX_DIR):
            self.vector_store.load_local(settings.FAISS_INDEX_DIR)

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        topic_filter: Optional[str] = None
    ) -> List[Tuple[Document, float]]:
        k = top_k or settings.TOP_K
        thresh = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD

        # Lazy check if index was created in another process
        if self.vector_store.index is None and os.path.exists(settings.FAISS_INDEX_DIR):
            self.vector_store.load_local(settings.FAISS_INDEX_DIR)

        results = self.vector_store.similarity_search_with_score(query, k=k * 2, threshold=thresh)

        if topic_filter:
            results = [
                (doc, score) for doc, score in results
                if topic_filter.lower() in doc.metadata.get("topic", "").lower()
            ]

        return results[:k]

    def build_grounded_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Retrieves top relevant chunks and formats them into a grounded context prompt string.
        """
        results = self.retrieve(query, top_k=top_k, threshold=threshold)

        if not results:
            return {
                "context_text": "No specific technical knowledge base documents found for this query.",
                "sources": [],
                "confidence_score": 0.0,
                "has_grounding": False
            }

        context_blocks = []
        sources = []
        top_score = results[0][1]

        for idx, (doc, score) in enumerate(results, start=1):
            doc_name = doc.metadata.get("document_name", "Unknown Source")
            topic = doc.metadata.get("topic", "General")
            chunk_id = doc.metadata.get("chunk_id", f"chunk_{idx}")
            sources.append({
                "source": doc_name,
                "topic": topic,
                "chunk_id": chunk_id,
                "score": round(score, 4)
            })

            context_blocks.append(
                f"[Source {idx}: {doc_name} | Topic: {topic} | Relevance: {round(score * 100, 1)}%]\n"
                f"{doc.page_content.strip()}"
            )

        formatted_context = "\n\n---\n\n".join(context_blocks)

        return {
            "context_text": formatted_context,
            "sources": sources,
            "confidence_score": top_score,
            "has_grounding": True
        }


rag_retriever = InterviewRAGRetriever()
