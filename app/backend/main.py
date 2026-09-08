from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import get_settings
from config.logger import logger
from database.database import init_db
from app.backend.routes import (
    health, users, resumes, jobs, matching,
    knowledge_base, interviews, analytics, voice, vision, auth, ats
)

settings = get_settings()


import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI Interview Coach backend...")
    init_db()
    logger.info("Database initialized.")

    # Self-healing FAISS knowledge base index check for containerized / fresh deployments
    faiss_file = os.path.join(settings.FAISS_INDEX_DIR, "index.faiss")
    if not os.path.exists(faiss_file):
        logger.info("FAISS index not found on startup. Ingesting knowledge base documents...")
        try:
            from rag.ingestion import ingest_knowledge_base
            ingest_knowledge_base()
            logger.info("Knowledge base successfully initialized on startup.")
        except Exception as e:
            logger.warning(f"Could not auto-ingest knowledge base on startup: {e}")

    yield
    logger.info("Shutting down AI Interview Coach backend...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Adaptive AI Interview Coach platform combining NLP, LangChain, FAISS, LangGraph, Scikit-Learn ML, and Computer Vision.",
    version="1.0.0",
    lifespan=lifespan
)

# Parse CORS origins from settings
cors_origins_raw = (settings.CORS_ORIGINS or "*").strip()
if cors_origins_raw == "*":
    # Development / permissive mode: allow localhost, common dev ports, and Vercel preview deploys
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8501"]
    cors_origin_regex = r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app)(:\d+)?$"
else:
    cors_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]
    cors_origin_regex = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routes
app.include_router(health.router)
app.include_router(users.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(matching.router)
app.include_router(knowledge_base.router)
app.include_router(interviews.router)
app.include_router(analytics.router)
app.include_router(voice.router)
app.include_router(vision.router)
app.include_router(auth.router)
app.include_router(ats.router)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
