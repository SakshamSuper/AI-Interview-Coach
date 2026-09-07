import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
from nlp.resume_parser import resume_parser
from nlp.jd_parser import jd_parser
from nlp.matching import matching_engine


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_matching_high_overlap():
    resume_text = """
David Kim
david.kim@example.com
Summary: Expert Python Engineer with 6 years experience in FastAPI, Docker, and PostgreSQL.
Skills: Python, FastAPI, Docker, Kubernetes, PostgreSQL, Git
Experience:
Senior Backend Engineer at CloudTech | 2021 - 2024
- Built distributed APIs with FastAPI and Python.
"""
    jd_text = """
Senior Backend Developer
Requirements:
- 5+ years of experience in Python and FastAPI.
- Strong hands-on experience with Docker and PostgreSQL.
- Kubernetes is required.
"""
    cand = resume_parser.parse(resume_text)
    jd = jd_parser.parse(jd_text)

    result = matching_engine.analyze_match(cand, jd)

    assert result.overall_match_score >= 70.0
    assert result.match_category in ["Strong Match", "Moderate Match"]
    assert "Python" in result.gap_report.strong_skills
    assert "FastAPI" in result.gap_report.strong_skills
    assert "Docker" in result.gap_report.strong_skills
    assert result.explanation.required_skills_coverage >= 75.0


def test_matching_low_overlap():
    resume_text = """
Chris Evans
chris@example.com
Summary: Digital marketing and social media specialist with SEO expertise.
Skills: SEO, Content Strategy, Google Analytics, Copywriting
"""
    jd_text = """
Lead Distributed Systems Engineer
Requirements:
- Strong experience in Rust, C++, Kubernetes, and Kafka.
- In-depth knowledge of Distributed Systems and High Availability.
"""
    cand = resume_parser.parse(resume_text)
    jd = jd_parser.parse(jd_text)

    result = matching_engine.analyze_match(cand, jd)

    assert result.overall_match_score < 50.0
    assert result.match_category == "Weak Match"
    assert len(result.gap_report.missing_skills) >= 2


def test_matching_endpoint(client):
    payload = {
        "raw_resume_text": "Skills: Python, Machine Learning, PyTorch, Docker",
        "raw_jd_text": "Requirements: Python, PyTorch, Large Language Models. 3+ years experience."
    }
    resp = client.post("/matching", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_match_score" in data
    assert "gap_report" in data
    assert "skill_breakdown" in data
    assert "explanation" in data
