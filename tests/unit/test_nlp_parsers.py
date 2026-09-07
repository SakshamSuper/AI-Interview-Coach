import io
import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
from nlp.resume_parser import resume_parser
from nlp.jd_parser import jd_parser
from nlp.skill_extractor import skill_extractor


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_skill_extractor_categories():
    text = "Experience with Python, Django, PostgreSQL, Docker, AWS, PyTorch, and Machine Learning."
    res = skill_extractor.extract_skills(text)
    assert "Python" in res["programming_languages"]
    assert "Django" in res["frameworks"]
    assert "PostgreSQL" in res["databases"]
    assert "Docker" in res["cloud_devops"]
    assert "AWS" in res["cloud_devops"]
    assert "PyTorch" in res["frameworks"]
    assert "Machine Learning" in res["ai_ml_domain"]


def test_resume_parser_structure():
    raw_text = """
Sarah Connor
sarah.c@cyberdyne.org | 555-987-6543 | github.com/sconnor

Professional Summary
Senior Software Engineer specialized in distributed systems and cloud microservices.

Work Experience
Lead Developer at Skynet Defense | 2020 - 2024
- Architected cloud pipelines with Go, Python, and Docker.
- Orchestrated microservices with Kubernetes on AWS.

Education
Bachelor of Science in Computer Science - MIT 2018

Skills
Languages: Python, Go, C++
Frameworks: FastAPI, React
Cloud: AWS, Docker, Kubernetes
"""
    profile = resume_parser.parse(raw_text, "sarah_connor_resume.txt")
    assert profile.name == "Sarah Connor"
    assert profile.contact.email == "sarah.c@cyberdyne.org"
    assert "Python" in profile.programming_languages
    assert "Go" in profile.programming_languages
    assert "Kubernetes" in profile.cloud_devops
    assert len(profile.education) >= 1
    assert profile.education[0].degree in ["Bachelor of Science", "B.S."]


def test_job_description_parser():
    raw_jd = """
Senior Cloud Engineer
Requirements:
- 4+ years of professional software development.
- Strong proficiency in Python, Docker, and Kubernetes.
- Experience with AWS and Terraform.

Preferred Qualifications:
- Experience with Go and Microservices.
- Familiarity with CI/CD pipelines.

Responsibilities:
- Build resilient infrastructure as code.
- Optimize container deployments.
"""
    jd_profile = jd_parser.parse(raw_jd)
    assert jd_profile.job_title == "Senior Cloud Engineer"
    assert jd_profile.role_level == "Senior"
    assert jd_profile.min_years_experience == 4
    assert "Python" in jd_profile.required_skills
    assert "Docker" in jd_profile.required_skills
    assert "Go" in jd_profile.preferred_skills


def test_resume_and_jd_api_endpoints(client):
    # Test resume upload endpoint with in-memory txt file
    resume_bytes = b"""
Alice Bob
alice@test.com
Skills: Python, FastAPI, Docker
Experience:
Software Engineer at Acme Corp | 2022 - 2024
- Built APIs with FastAPI and Python.
"""
    files = {"file": ("test_resume.txt", io.BytesIO(resume_bytes), "text/plain")}
    resp = client.post("/resumes/upload", files=files)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["filename"] == "test_resume.txt"
    assert "Python" in res_data["profile"]["programming_languages"]

    # Test JD analyze endpoint
    jd_payload = {
        "title": "Backend Python Developer",
        "job_description_text": "Requirements: Python, FastAPI, PostgreSQL. 3+ years experience."
    }
    jd_resp = client.post("/jobs/analyze", json=jd_payload)
    assert jd_resp.status_code == 200
    jd_data = jd_resp.json()
    assert jd_data["profile"]["job_title"] == "Backend Python Developer"
    assert "Python" in jd_data["profile"]["required_skills"]
