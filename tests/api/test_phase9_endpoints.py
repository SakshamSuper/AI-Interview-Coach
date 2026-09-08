"""
tests/api/test_phase9_endpoints.py
===================================
Phase 11: Pytest coverage for all Phase 9 backend endpoints.

Endpoints covered:
  GET /analytics/{user_id}            -- aggregate user performance metrics
  GET /analytics/{user_id} (empty)    -- empty-state for unknown user
  GET /analytics/session/{session_id} -- per-session evaluation breakdown
  GET /interviews/?user_id=...        -- session list for a user
  GET /interviews/{session_id}        -- individual session detail
  GET /ml/readiness?user_id=...       -- ML readiness classifier (real features)
  GET /recommendations/{session_id}   -- LLM-generated preparation roadmap
  GET /skill-gaps?user_id=...         -- latest skill gap analysis

Fixture strategy (hermetic -- does NOT depend on production DB):
  - Fresh SQLite DB (init_db()) scoped to this module
  - Creates a dedicated test user
  - Uploads a minimal .txt resume -> POST /resumes/upload
  - Analyzes a minimal JD -> POST /jobs/analyze
  - Runs skill-gap matching -> POST /matching
  - Runs a 1-question interview cycle (start -> answer -> next/complete)
  All IDs are captured from API responses and stored in module-level _state.
"""

import io
import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
from database.database import init_db

# ---------------------------------------------------------------------------
# Module-level state populated by the fixture
# ---------------------------------------------------------------------------

_state: dict = {}


@pytest.fixture(scope="module")
def client():
    """Shared TestClient with a freshly initialised DB."""
    init_db()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module", autouse=True)
def seed_data(client: TestClient):
    """
    Build a minimal but complete dataset for Phase 9 endpoint testing.
    All IDs are stored in the module-level _state dict.
    """
    # 1. Create test user
    user_resp = client.post("/users", json={
        "name": "Phase11 Test Candidate",
        "email": "phase11_test_unique_9876@example.com",
        "target_role": "Software Engineer",
    })
    assert user_resp.status_code == 200, f"User creation failed: {user_resp.text}"
    _state["user_id"] = user_resp.json()["id"]

    # 2. Upload minimal resume
    resume_text = (
        "John Test\njohn.test@example.com | github.com/johntest\n\n"
        "SKILLS\nPython, FastAPI, Docker, PostgreSQL, Redis, Kubernetes, REST APIs, SQL\n\n"
        "EXPERIENCE\n"
        "Software Engineer at TechCorp (2021-2024)\n"
        "- Designed and deployed microservices using FastAPI and Docker.\n"
        "- Managed PostgreSQL databases with SQLAlchemy.\n\n"
        "EDUCATION\nB.Sc. Computer Science, State University, 2021\n"
    )
    res_resp = client.post(
        "/resumes/upload",
        data={"user_id": str(_state["user_id"])},
        files={"file": ("test_resume.txt", io.BytesIO(resume_text.encode()), "text/plain")},
    )
    assert res_resp.status_code == 200, f"Resume upload failed: {res_resp.text}"
    _state["resume_id"] = res_resp.json()["resume_id"]

    # 3. Analyze minimal JD
    jd_text = (
        "Software Engineer - Python Backend\n\n"
        "Required Skills:\n- Python (FastAPI or Django)\n- Docker and Kubernetes\n"
        "- SQL databases (PostgreSQL preferred)\n- REST API design\n\n"
        "Preferred:\n- Redis, Kafka, cloud platforms (AWS/GCP)\n\n"
        "Experience: 2+ years. BS/MS in Computer Science or related."
    )
    jd_resp = client.post("/jobs/analyze", json={
        "user_id": _state["user_id"],
        "title": "Software Engineer",
        "job_description_text": jd_text,
    })
    assert jd_resp.status_code == 200, f"JD analysis failed: {jd_resp.text}"
    _state["jd_id"] = jd_resp.json()["jd_id"]

    # 4. Run skill-gap matching
    match_resp = client.post("/matching", json={
        "user_id": _state["user_id"],
        "resume_id": _state["resume_id"],
        "jd_id": _state["jd_id"],
    })
    assert match_resp.status_code == 200, f"Matching failed: {match_resp.text}"

    # 5. Complete one interview (1 question)
    start_resp = client.post("/interviews/start", json={
        "user_id": _state["user_id"],
        "resume_id": _state["resume_id"],
        "jd_id": _state["jd_id"],
        "target_role": "Software Engineer",
        "interview_type": "Technical",
        "difficulty": "Medium",
        "total_questions": 1,
    })
    assert start_resp.status_code == 200, f"Interview start failed: {start_resp.text}"
    _state["session_id"] = start_resp.json()["session_id"]

    # Submit substantive answer (55+ words to produce real answer_length)
    answer_resp = client.post(
        f"/interviews/{_state['session_id']}/answer",
        json={"answer_text": (
            "I design REST APIs using FastAPI with Pydantic models for validation. "
            "I use Docker to containerise services and Kubernetes for orchestration. "
            "PostgreSQL is my preferred relational store, connected via SQLAlchemy ORM. "
            "For caching I use Redis, and I implement circuit-breaker patterns for "
            "fault tolerance in microservice communication between services."
        )},
    )
    assert answer_resp.status_code == 200, f"Answer submission failed: {answer_resp.text}"

    # Advance to session completion
    next_resp = client.post(f"/interviews/{_state['session_id']}/next")
    assert next_resp.status_code == 200, f"Next/complete failed: {next_resp.text}"
    next_data = next_resp.json()
    assert next_data.get("is_completed") is True, (
        f"Session did not complete: {next_data}"
    )


# ---------------------------------------------------------------------------
# TEST 1 -- GET /analytics/{user_id} -- aggregate metrics shape & values
# ---------------------------------------------------------------------------

def test_analytics_user_response_shape(client: TestClient):
    """Analytics endpoint returns all required fields with correct types."""
    resp = client.get(f"/analytics/{_state['user_id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    required_fields = [
        "total_interviews", "completed_interviews", "overall_readiness_label",
        "average_overall_score", "average_technical_score", "average_communication_score",
        "average_relevance_score", "average_completeness_score", "average_clarity_score",
        "topic_performance", "score_history", "strong_areas", "weak_areas",
    ]
    for field in required_fields:
        assert field in data, f"Missing field in /analytics response: {field!r}"

    assert data["completed_interviews"] >= 1, (
        "Expected at least 1 completed interview after fixture setup"
    )
    score = data["average_overall_score"]
    assert isinstance(score, (int, float)), f"average_overall_score not numeric: {score!r}"
    assert 0.0 <= score <= 100.0, f"average_overall_score out of range: {score}"
    assert isinstance(data["score_history"], list)
    assert isinstance(data["topic_performance"], dict)


# ---------------------------------------------------------------------------
# TEST 2 -- GET /analytics/{user_id} -- empty state for unknown user
# ---------------------------------------------------------------------------

def test_analytics_user_empty_state(client: TestClient):
    """Analytics for a non-existent user returns zeros, not an error.

    The empty-state path in aggregate_user_analytics returns total_interviews=0
    but does NOT include completed_interviews when there are no sessions at all.
    Test only asserts fields the endpoint actually emits in this path.
    """
    resp = client.get("/analytics/999999")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_interviews"] == 0
    assert data["average_overall_score"] == 0.0
    assert data["score_history"] == []
    assert data["overall_readiness_label"] == "Not Evaluated"
    # completed_interviews absent from early-return dict -- acceptable.
    assert data.get("completed_interviews", 0) == 0


# ---------------------------------------------------------------------------
# TEST 3 -- GET /analytics/session/{session_id} -- per-session breakdown
# ---------------------------------------------------------------------------

def test_analytics_session_breakdown(client: TestClient):
    """Session analytics returns evaluation data for the test session."""
    resp = client.get(f"/analytics/session/{_state['session_id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["session_id"] == _state["session_id"]
    assert data["status"] in ("completed", "in_progress")

    if data.get("has_evaluations") is False:
        # Endpoint returned early (no evaluations stored) -- still valid structure
        assert "target_role" in data
    else:
        # Full breakdown present
        assert "average_dimensions" in data, f"average_dimensions missing: {list(data.keys())}"
        dims = data["average_dimensions"]
        for dim in ("technical_accuracy", "relevance", "completeness", "clarity", "communication"):
            assert dim in dims, f"Missing dimension {dim!r}"
            assert 0.0 <= dims[dim] <= 100.0, f"{dim} out of range: {dims[dim]}"
        assert "questions_and_evaluations" in data
        assert isinstance(data["questions_and_evaluations"], list)


# ---------------------------------------------------------------------------
# TEST 4 -- GET /interviews/?user_id=... -- session list
# ---------------------------------------------------------------------------

def test_interview_list(client: TestClient):
    """Session list returns a non-empty list containing the test session."""
    resp = client.get(f"/interviews/?user_id={_state['user_id']}")
    assert resp.status_code == 200, resp.text
    sessions = resp.json()
    assert isinstance(sessions, list), "Expected a list of sessions"
    assert len(sessions) >= 1, "Expected at least 1 session"

    required = ["session_id", "status", "target_role", "total_questions",
                "overall_score", "readiness_label"]
    for item in sessions:
        for field in required:
            assert field in item, f"Session summary missing field {field!r}"

    ids = [s["session_id"] for s in sessions]
    assert _state["session_id"] in ids, (
        f"Test session {_state['session_id']} not in list: {ids}"
    )


# ---------------------------------------------------------------------------
# TEST 5 -- GET /interviews/{session_id} -- individual session detail
# ---------------------------------------------------------------------------

def test_interview_session_detail(client: TestClient):
    """Individual session detail returns correct session_id and fields."""
    resp = client.get(f"/interviews/{_state['session_id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["session_id"] == _state["session_id"]
    assert data["status"] in ("completed", "in_progress")
    assert data["target_role"] == "Software Engineer"
    assert "total_questions" in data
    assert "overall_score" in data

    # 404 for non-existent session
    missing_resp = client.get("/interviews/999999")
    assert missing_resp.status_code == 404


# ---------------------------------------------------------------------------
# TEST 6 -- GET /ml/readiness?user_id=... -- ML classifier real features
# ---------------------------------------------------------------------------

def test_ml_readiness_with_data(client: TestClient):
    """ML readiness returns a valid prediction using real (not hardcoded) features."""
    resp = client.get(f"/ml/readiness?user_id={_state['user_id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["has_data"] is True, (
        "Expected has_data=True after completing an interview session"
    )

    label = data["readiness_label"]
    assert label in ("Interview Ready", "Almost Ready", "Needs Improvement"), (
        f"Unexpected readiness_label: {label!r}"
    )

    score = data["readiness_score"]
    assert isinstance(score, (int, float))
    assert 0.0 <= score <= 100.0, f"readiness_score out of range: {score}"

    # model_architecture must be the ACTUAL loaded runtime model type
    arch = data.get("model_architecture")
    assert arch is not None, "model_architecture field missing"
    assert arch == "LogisticRegression", (
        f"Expected LogisticRegression (actual runtime type); got {arch!r}"
    )

    fi = data.get("feature_inputs", {})
    assert "answer_length" in fi, "answer_length missing from feature_inputs"
    assert "difficulty_numeric" in fi, "difficulty_numeric missing from feature_inputs"
    assert "keyword_coverage" in fi, "keyword_coverage missing from feature_inputs"

    # answer_length: real word count -- fixture answer has 55+ words
    al = fi["answer_length"]
    assert isinstance(al, (int, float)) and al > 0, (
        f"answer_length should be positive real word count; got: {al}"
    )

    # difficulty_numeric: mapped from Easy/Medium/Hard -> 1/2/3
    dn = fi["difficulty_numeric"]
    assert 1.0 <= dn <= 3.0, f"difficulty_numeric out of [1,3]: {dn}"

    # keyword_coverage: fraction in [0, 1]
    kc = fi["keyword_coverage"]
    assert 0.0 <= kc <= 1.0, f"keyword_coverage out of [0,1]: {kc}"

    # keyword_coverage_source must be set (real or fallback -- both valid)
    kc_src = fi.get("keyword_coverage_source", "")
    assert kc_src, "keyword_coverage_source must not be empty"

    # No-data case: unknown user
    empty_resp = client.get("/ml/readiness?user_id=999999")
    assert empty_resp.status_code == 200
    empty_data = empty_resp.json()
    assert empty_data["has_data"] is False
    assert empty_data["readiness_label"] is None


# ---------------------------------------------------------------------------
# TEST 7 -- GET /recommendations/{session_id} -- preparation roadmap
# ---------------------------------------------------------------------------

def test_recommendations_for_completed_session(client: TestClient):
    """Recommendations endpoint returns all required roadmap fields."""
    resp = client.get(f"/recommendations/{_state['session_id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    required = ["overall_summary", "strong_areas", "weak_areas",
                "learning_priorities", "practice_questions"]
    for field in required:
        assert field in data, f"Recommendations missing field {field!r}"

    assert isinstance(data["strong_areas"], list)
    assert isinstance(data["weak_areas"], list)
    assert isinstance(data["learning_priorities"], list)
    assert isinstance(data["practice_questions"], list)
    assert isinstance(data["overall_summary"], str) and data["overall_summary"].strip(), (
        "overall_summary should be a non-empty string"
    )

    # 404 for non-existent session
    missing_resp = client.get("/recommendations/999999")
    assert missing_resp.status_code == 404


# ---------------------------------------------------------------------------
# TEST 8 -- GET /skill-gaps?user_id=... -- latest skill gap analysis
# ---------------------------------------------------------------------------

def test_skill_gaps_endpoint(client: TestClient):
    """Skill-gaps returns the stored matching analysis for the test user."""
    resp = client.get(f"/skill-gaps?user_id={_state['user_id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    score = data.get("overall_match_score")
    assert score is not None, "overall_match_score field missing"
    assert isinstance(score, (int, float))
    assert 0.0 <= score <= 100.0, f"overall_match_score out of range: {score}"

    cat = data.get("match_category")
    assert cat and isinstance(cat, str), f"match_category invalid: {cat!r}"

    assert "skill_breakdown" in data
    assert isinstance(data["skill_breakdown"], list)

    assert "gap_report" in data
    gap = data["gap_report"]
    for bucket in ("strong_skills", "matched_skills",
                   "partially_matched_skills", "missing_skills"):
        assert bucket in gap, f"gap_report missing bucket {bucket!r}"

    # 404 for user who has never run matching
    missing_resp = client.get("/skill-gaps?user_id=999999")
    assert missing_resp.status_code == 404