"""
tests/api/test_auth.py
=======================
Tests for the GET /auth/me endpoint.

Two auth paths tested:
  1. X-Auth-Email / X-Auth-Name headers (from AuthContext — server-verified session)
  2. Authorization: Bearer <hs256_jwt> (full JWT path)

No real Google OAuth credentials needed — tests fabricate valid JWTs
signed with the NEXTAUTH_SECRET.
"""
import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
from database.database import init_db


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


def _make_jwt(secret: str, email: str, name: str) -> str:
    """Create a minimal HS256 JWT matching NextAuth format."""
    from jose import jwt
    payload = {"email": email, "name": name, "sub": email}
    return jwt.encode(payload, secret, algorithm="HS256")


SECRET = "a56866a6f87acc930891037d87ae2aa699b1d886b7923257aea0ef381b7ef795"
TEST_EMAIL = "auth_test_unique_xyz123@example.com"
TEST_NAME = "Auth Test User"


# ─── Header path tests ────────────────────────────────────────────────────────

class TestAuthMeHeaderPath:
    def test_no_credentials_returns_401(self, client):
        """No auth headers at all must return 401."""
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_empty_email_header_returns_401(self, client):
        """Empty X-Auth-Email must be treated as missing credentials."""
        resp = client.get("/auth/me", headers={"X-Auth-Email": ""})
        assert resp.status_code == 401

    def test_valid_header_creates_user(self, client):
        """Valid X-Auth-Email + X-Auth-Name headers must return 200 with a user record."""
        resp = client.get(
            "/auth/me",
            headers={
                "X-Auth-Email": TEST_EMAIL,
                "X-Auth-Name": TEST_NAME,
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == TEST_EMAIL
        assert data["name"] == TEST_NAME
        assert isinstance(data["id"], int)
        assert data["id"] > 0

    def test_same_email_is_idempotent(self, client):
        """Calling /auth/me twice with the same email must return the same user_id."""
        headers = {"X-Auth-Email": TEST_EMAIL, "X-Auth-Name": TEST_NAME}
        r1 = client.get("/auth/me", headers=headers)
        r2 = client.get("/auth/me", headers=headers)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"]


# ─── Bearer JWT path tests ────────────────────────────────────────────────────

class TestAuthMeBearerPath:
    def test_invalid_token_returns_401(self, client):
        """Garbage bearer token must return 401."""
        resp = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer not.a.real.token"}
        )
        assert resp.status_code == 401

    def test_valid_hs256_jwt_resolves_user(self, client):
        """A correctly signed HS256 JWT must return 200 with user info."""
        token = _make_jwt(SECRET, "bearer_test_unique_abc@example.com", "Bearer Test")
        resp = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "bearer_test_unique_abc@example.com"
        assert isinstance(data["id"], int)
