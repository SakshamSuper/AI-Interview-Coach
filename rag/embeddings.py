from typing import List
from langchain_core.embeddings import Embeddings
from nlp.similarity import generate_embeddings


class LocalInterviewEmbeddings(Embeddings):
    """LangChain-compatible Embeddings wrapper using SentenceTransformers or Fallback."""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        arr = generate_embeddings(texts)
        return [list(map(float, vec)) for vec in arr]

    def embed_query(self, text: str) -> List[float]:
        vec = generate_embeddings(text)
        return list(map(float, vec))


interview_embeddings = LocalInterviewEmbeddings()
