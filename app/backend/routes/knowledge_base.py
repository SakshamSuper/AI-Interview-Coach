import os
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from rag.retriever import rag_retriever
from rag.ingestion import ingest_knowledge_base
from config.settings import get_settings

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base & RAG"])
settings = get_settings()


class KBQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4
    threshold: Optional[float] = 0.40
    topic_filter: Optional[str] = None


class KBQueryResponse(BaseModel):
    query: str
    confidence_score: float
    has_grounding: bool
    context_text: str
    sources: List[Dict[str, Any]]


class KBStatusResponse(BaseModel):
    is_indexed: bool
    index_directory: str
    total_chunks: int
    dimension: Optional[int] = None
    topics: List[str]
    documents: List[str]


@router.get("", response_model=KBStatusResponse)
def get_kb_status():
    summary_path = os.path.join(settings.FAISS_INDEX_DIR, "index_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        return KBStatusResponse(
            is_indexed=True,
            index_directory=settings.FAISS_INDEX_DIR,
            total_chunks=summary.get("total_chunks", 0),
            dimension=summary.get("dimension", 384),
            topics=summary.get("topics", []),
            documents=summary.get("documents", [])
        )
    return KBStatusResponse(
        is_indexed=False,
        index_directory=settings.FAISS_INDEX_DIR,
        total_chunks=0,
        dimension=None,
        topics=[],
        documents=[]
    )


@router.post("/query", response_model=KBQueryResponse)
def query_knowledge_base(req: KBQueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    context_data = rag_retriever.build_grounded_context(
        query=req.query,
        top_k=req.top_k,
        threshold=req.threshold
    )

    return KBQueryResponse(
        query=req.query,
        confidence_score=context_data["confidence_score"],
        has_grounding=context_data["has_grounding"],
        context_text=context_data["context_text"],
        sources=context_data["sources"]
    )


@router.post("/ingest")
def trigger_ingestion():
    result = ingest_knowledge_base()
    return result
