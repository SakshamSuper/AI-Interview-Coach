import os
import json
import pickle
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
import faiss
from langchain_core.documents import Document
from rag.embeddings import interview_embeddings
from config.settings import get_settings
from config.logger import logger

settings = get_settings()


class VectorStoreBase(ABC):
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        pass

    @abstractmethod
    def similarity_search_with_score(
        self, query: str, k: int = 4, threshold: float = 0.0
    ) -> List[Tuple[Document, float]]:
        pass

    @abstractmethod
    def save_local(self, folder_path: str) -> None:
        pass

    @abstractmethod
    def load_local(self, folder_path: str) -> bool:
        pass


class FAISSVectorStore(VectorStoreBase):
    """FAISS-backed Vector Store supporting cosine similarity, metadata persistence, and thresholding."""

    def __init__(self, embedding_fn=None):
        self.embedding_fn = embedding_fn or interview_embeddings
        self.index = None
        self.documents: List[Document] = []
        self.dimension = None

    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            return

        texts = [doc.page_content for doc in documents]
        raw_embs = self.embedding_fn.embed_documents(texts)
        embs = np.array(raw_embs, dtype=np.float32)

        # Normalize vectors for cosine similarity via inner product
        faiss.normalize_L2(embs)
        self.dimension = embs.shape[1]

        if self.index is None:
            # IndexFlatIP calculates inner product on normalized vectors = cosine similarity
            self.index = faiss.IndexFlatIP(self.dimension)

        self.index.add(embs)
        self.documents.extend(documents)
        logger.info(f"Added {len(documents)} document chunks to FAISS index. Total: {self.index.ntotal}")

    def similarity_search_with_score(
        self, query: str, k: int = 4, threshold: float = 0.0
    ) -> List[Tuple[Document, float]]:
        if self.index is None or self.index.ntotal == 0:
            return []

        query_emb = np.array([self.embedding_fn.embed_query(query)], dtype=np.float32)
        faiss.normalize_L2(query_emb)

        top_k = min(k, self.index.ntotal)
        scores, indices = self.index.search(query_emb, top_k)

        results: List[Tuple[Document, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            cos_sim = float(score)
            if cos_sim >= threshold:
                results.append((self.documents[idx], cos_sim))

        return results

    def similarity_search(
        self, query: str, k: int = 4, threshold: float = 0.0
    ) -> List[Document]:
        return [doc for doc, _ in self.similarity_search_with_score(query, k, threshold)]

    def save_local(self, folder_path: str) -> None:
        os.makedirs(folder_path, exist_ok=True)
        if self.index is None:
            logger.warning("FAISS index is empty; skipping save.")
            return

        index_path = os.path.join(folder_path, "index.faiss")
        metadata_path = os.path.join(folder_path, "metadata.pkl")

        faiss.write_index(self.index, index_path)
        with open(metadata_path, "wb") as f:
            pickle.dump(self.documents, f)

        # Also write summary json for easy inspection
        summary_path = os.path.join(folder_path, "index_summary.json")
        summary = {
            "total_chunks": len(self.documents),
            "dimension": self.dimension,
            "topics": list(set(d.metadata.get("topic", "unknown") for d in self.documents)),
            "documents": list(set(d.metadata.get("document_name", "unknown") for d in self.documents))
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"FAISS vector store successfully persisted to: {folder_path}")

    def load_local(self, folder_path: str) -> bool:
        index_path = os.path.join(folder_path, "index.faiss")
        metadata_path = os.path.join(folder_path, "metadata.pkl")

        if not (os.path.exists(index_path) and os.path.exists(metadata_path)):
            return False

        try:
            self.index = faiss.read_index(index_path)
            self.dimension = self.index.d
            with open(metadata_path, "rb") as f:
                self.documents = pickle.load(f)
            logger.info(f"Loaded FAISS vector store from {folder_path} with {self.index.ntotal} vectors.")
            return True
        except Exception as e:
            logger.error(f"Failed loading FAISS index from {folder_path}: {e}")
            return False


# Global singleton instance
vector_store = FAISSVectorStore()
