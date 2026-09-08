import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
from database.database import SessionLocal, init_db
from database.models import User
from config.settings import get_settings


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "version" in data


def test_user_creation_and_retrieval(client):
    unique_email = "test_user_foundation@example.com"
    payload = {
        "name": "Alex Smith",
        "email": unique_email,
        "target_role": "Backend Engineer"
    }
    create_resp = client.post("/users", json=payload)
    assert create_resp.status_code == 200
    user_data = create_resp.json()
    assert user_data["name"] == "Alex Smith"
    assert user_data["email"] == unique_email
    user_id = user_data["id"]

    get_resp = client.get(f"/users/{user_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == user_id
