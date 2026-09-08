import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
from rag.loaders import kb_loader
from rag.splitter import kb_splitter
from rag.vector_store import FAISSVectorStore
from rag.retriever import rag_retriever


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_knowledge_base_loading():
    docs = kb_loader.load_directory("data/knowledge_base")
    assert len(docs) >= 5
    topics = [d.metadata.get("topic") for d in docs]
    assert any("Python" in t for t in topics)
    assert any("System Design" in t for t in topics)


def test_chunking_and_metadata():
    docs = kb_loader.load_directory("data/knowledge_base")
    chunks = kb_splitter.split_documents(docs)
    assert len(chunks) > len(docs)
    sample = chunks[0]
    assert "chunk_id" in sample.metadata
    assert "topic" in sample.metadata
    assert "document_name" in sample.metadata


def test_faiss_retrieval():
    results = rag_retriever.retrieve("What is CAP theorem?", top_k=2)
    assert len(results) > 0
    top_doc, score = results[0]
    assert score > 0.40
    assert "System Design" in top_doc.metadata.get("topic", "")


def test_grounded_context_builder():
    context_data = rag_retriever.build_grounded_context("Explain Python GIL and multithreading")
    assert context_data["has_grounding"] is True
    assert "Python" in context_data["context_text"]
    assert len(context_data["sources"]) > 0


def test_kb_api_endpoint(client):
    status_resp = client.get("/knowledge-base")
    assert status_resp.status_code == 200
    assert status_resp.json()["is_indexed"] is True

    query_resp = client.post("/knowledge-base/query", json={"query": "ACID database transactions"})
    assert query_resp.status_code == 200
    data = query_resp.json()
    assert data["has_grounding"] is True
    assert data["confidence_score"] > 0.40
