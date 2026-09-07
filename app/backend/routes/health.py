import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.backend.schemas.common import HealthResponse
from app.backend.dependencies.db import get_db
from config.settings import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health_status(db: Session = Depends(get_db)):
    settings = get_settings()

    # Test database connectivity
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check knowledge base FAISS index presence
    kb_ready = os.path.exists(settings.FAISS_INDEX_DIR) and os.path.exists(
        os.path.join(settings.FAISS_INDEX_DIR, "index.faiss")
    )

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        database=db_status,
        llm_provider=settings.LLM_PROVIDER,
        vector_store=settings.VECTOR_STORE_TYPE,
        knowledge_base_ready=kb_ready,
        version="1.0.0"
    )
