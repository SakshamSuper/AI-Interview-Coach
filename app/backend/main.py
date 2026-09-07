from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import get_settings
from config.logger import logger
from database.database import init_db
from app.backend.routes import (
    health, users, resumes, jobs, matching,
    knowledge_base, interviews, analytics, voice, vision
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI Interview Coach backend...")
    init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down AI Interview Coach backend...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Adaptive AI Interview Coach platform combining NLP, LangChain, FAISS, LangGraph, Scikit-Learn ML, and Computer Vision.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
