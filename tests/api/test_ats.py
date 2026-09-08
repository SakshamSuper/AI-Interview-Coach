"""
tests/api/test_ats.py
======================
Tests for the POST /ats/score endpoint.

Strategy (hermetic):
  - Creates a test user, uploads a minimal resume, analyzes a minimal JD
  - Runs /ats/score with those IDs
  - Validates response structure, score ranges, and disclaimer presence
"""
import io
import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
from database.database import init_db

_state: dict = {}

MINIMAL_RESUME = """
John Smith
john.smith@example.com | github.com/jsmith

SKILLS
Python, FastAPI, PostgreSQL, Docker, REST APIs, Machine Learning

EXPERIENCE
Software Engineer — Acme Corp (2021 - Present)
  Built scalable REST APIs with FastAPI and PostgreSQL.
  Deployed services using Docker and Kubernetes.

EDUCATION
B.S. Computer Science — State University, 2021

CERTIFICATIONS
AWS Certified Developer Associate
"""

MINIMAL_JD = """
Senior Backend Engineer

We are looking for a Senior Backend Engineer with 3+ years experience.

Required Skills: Python, FastAPI, PostgreSQL, Docker, REST APIs
Preferred Skills: Kubernetes, Redis, GraphQL

Education: Bachelor's degree in Computer Science or related field.
Min Experience: 3 years
"""


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module", autouse=True)
def seed_data(client: TestClient):
    # Create user
    u = client.post("/users", json={
        "name": "ATS Test User",
        "email": "ats_test_unique_qwerty789@example.com",
    })
    assert u.status_code == 200
    _state["user_id"] = u.json()["id"]

    # Upload resume
    files = {"file": ("test_resume.txt", io.BytesIO(MINIMAL_RESUME.encode("utf-8")), "text/plain")}
    data = {"user_id": str(_state["user_id"])}
    r = client.post("/resumes/upload", files=files, data=data)
    assert r.status_code == 200, f"Resume upload failed: {r.text}"
    _state["resume_id"] = r.json()["resume_id"]

    # Analyze JD
    jd = client.post("/jobs/analyze", json={
        "user_id": _state["user_id"],
        "title": "Senior Backend Engineer",
        "job_description_text": MINIMAL_JD,
    })
    assert jd.status_code == 200, f"JD analyze failed: {jd.text}"
    _state["jd_id"] = jd.json()["jd_id"]


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestATSScore:
    def test_valid_request_returns_200(self, client):
        """Valid resume_id + jd_id must return 200 with all required fields."""
        resp = client.post("/ats/score", json={
            "resume_id": _state["resume_id"],
            "jd_id": _state["jd_id"],
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "overall_ats_score" in data
        assert "grade" in data
        assert "components" in data
        assert "matched_keywords" in data
        assert "missing_keywords" in data
        assert "recommendations" in data
        assert "disclaimer" in data

    def test_overall_score_in_range(self, client):
        """overall_ats_score must be between 0 and 100."""
        resp = client.post("/ats/score", json={
            "resume_id": _state["resume_id"],
            "jd_id": _state["jd_id"],
        })
        assert resp.status_code == 200
        score = resp.json()["overall_ats_score"]
        assert 0.0 <= score <= 100.0

    def test_all_component_scores_in_range(self, client):
        """Every component score must be 0-100."""
        resp = client.post("/ats/score", json={
            "resume_id": _state["resume_id"],
            "jd_id": _state["jd_id"],
        })
        assert resp.status_code == 200
        for comp in resp.json()["components"]:
            assert 0.0 <= comp["score"] <= 100.0, f"Bad score for {comp['name']}: {comp['score']}"

    def test_six_components_present(self, client):
        """There must be exactly 6 ATS components."""
        resp = client.post("/ats/score", json={
            "resume_id": _state["resume_id"],
            "jd_id": _state["jd_id"],
        })
        assert resp.status_code == 200
        assert len(resp.json()["components"]) == 6

    def test_matched_and_missing_disjoint(self, client):
        """matched_keywords and missing_keywords must be disjoint sets."""
        resp = client.post("/ats/score", json={
            "resume_id": _state["resume_id"],
            "jd_id": _state["jd_id"],
        })
        assert resp.status_code == 200
        data = resp.json()
        matched = set(data["matched_keywords"])
        missing = set(data["missing_keywords"])
        overlap = matched & missing
        assert not overlap, f"Overlap found: {overlap}"

    def test_disclaimer_always_present(self, client):
        """Disclaimer string must always be present and non-empty."""
        resp = client.post("/ats/score", json={
            "resume_id": _state["resume_id"],
            "jd_id": _state["jd_id"],
        })
        assert resp.status_code == 200
        disclaimer = resp.json()["disclaimer"]
        assert len(disclaimer) > 20
        assert "ATS" in disclaimer or "applicant tracking" in disclaimer.lower()

    def test_missing_resume_id_returns_422(self, client):
        """Omitting resume_id must return 422 validation error."""
        resp = client.post("/ats/score", json={"jd_id": _state["jd_id"]})
        assert resp.status_code == 422

    def test_missing_jd_id_returns_422(self, client):
        """Omitting jd_id must return 422 validation error."""
        resp = client.post("/ats/score", json={"resume_id": _state["resume_id"]})
        assert resp.status_code == 422

    def test_nonexistent_resume_returns_404(self, client):
        """A resume_id that does not exist must return 404."""
        resp = client.post("/ats/score", json={"resume_id": 999999, "jd_id": _state["jd_id"]})
        assert resp.status_code == 404

    def test_nonexistent_jd_returns_404(self, client):
        """A jd_id that does not exist must return 404."""
        resp = client.post("/ats/score", json={"resume_id": _state["resume_id"], "jd_id": 999999})
        assert resp.status_code == 404

    def test_grade_is_valid_letter(self, client):
        """Grade must be one of A, B, C, D, F."""
        resp = client.post("/ats/score", json={
            "resume_id": _state["resume_id"],
            "jd_id": _state["jd_id"],
        })
        assert resp.status_code == 200
        assert resp.json()["grade"] in ("A", "B", "C", "D", "F")

    def test_recommendations_not_empty(self, client):
        """recommendations list must have at least 1 item."""
        resp = client.post("/ats/score", json={
            "resume_id": _state["resume_id"],
            "jd_id": _state["jd_id"],
        })
        assert resp.status_code == 200
        assert len(resp.json()["recommendations"]) >= 1
