import numpy as np
from typing import List, Union
from config.settings import get_settings
from config.logger import logger

settings = get_settings()

_transformer_model = None


def get_embedding_model():
    """Lazily loads and caches the SentenceTransformer model with fallback."""
    global _transformer_model
    if _transformer_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            _transformer_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({str(e)}). Using TF-IDF/n-gram fallback.")
            _transformer_model = "fallback"
    return _transformer_model


def compute_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Computes cosine similarity between two 1D or 2D numpy vectors."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def generate_embeddings(texts: Union[str, List[str]]) -> np.ndarray:
    """Generates normalized vector embeddings for given texts."""
    is_single = isinstance(texts, str)
    text_list = [texts] if is_single else texts

    model = get_embedding_model()
    if model != "fallback":
        try:
            embeddings = model.encode(text_list, show_progress_bar=False, normalize_embeddings=True)
            return embeddings[0] if is_single else embeddings
        except Exception as e:
            logger.warning(f"Embedding encoding failed: {e}. Falling back to TF-IDF.")

    # Fallback to character/word n-gram vectorizer from scikit-learn
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    vectors = vectorizer.fit_transform(text_list).toarray()
    # Normalize
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized = vectors / norms
    return normalized[0] if is_single else normalized


def calculate_semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Calculates semantic similarity between two texts (0.0 to 1.0).
    Uses SentenceTransformers with TF-IDF fallback.
    """
    if not text_a or not text_b:
        return 0.0

    model = get_embedding_model()
    if model != "fallback":
        try:
            embs = model.encode([text_a, text_b], normalize_embeddings=True)
            sim = float(np.dot(embs[0], embs[1]))
            return max(0.0, min(1.0, sim))
        except Exception as e:
            logger.warning(f"SentenceTransformer similarity failed: {e}")

    # Fallback via TfidfVectorizer
    from sklearn.feature_extraction.text import TfidfVectorizer
    try:
        vec = TfidfVectorizer().fit_transform([text_a, text_b])
        dense = vec.toarray()
        sim = compute_cosine_similarity(dense[0], dense[1])
        return max(0.0, min(1.0, sim))
    except Exception:
        return 0.0
