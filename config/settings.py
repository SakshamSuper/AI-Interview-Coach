import os
from functools import lru_cache
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core Application
    APP_NAME: str = "AI Interview Coach"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_PORT: int = 8501

    # LLM Provider Configuration
    LLM_PROVIDER: Literal["groq", "openai", "local_mock"] = "groq"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 2048

    # RAG & Embedding Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_STORE_TYPE: Literal["faiss", "chroma"] = "faiss"
    FAISS_INDEX_DIR: str = "data/knowledge_base/faiss_index"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.60

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./data/interview_coach.db"

    # Machine Learning Configuration
    ML_MODEL_PATH: str = "ml/models/interview_readiness_rf.joblib"
    ML_SCALER_PATH: str = "ml/models/readiness_scaler.joblib"

    # Directories
    UPLOAD_DIR: str = "data/uploads"
    TEMP_MEDIA_DIR: str = "data/temp_media"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached singleton settings instance."""
    return Settings()
