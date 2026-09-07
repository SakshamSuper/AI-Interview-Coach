import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
from agents.resume_agent import resume_agent
from agents.question_agent import question_agent
from agents.evaluation_agent import evaluation_agent
from agents.recommendation_agent import recommendation_agent
from agents.state import InterviewState


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_resume_agent():
    state: InterviewState = {
        "candidate_profile": {"skills": ["Python", "FastAPI"]},
        "job_profile": {"job_title": "Backend Lead", "required_skills": ["Python", "FastAPI", "Kubernetes", "Kafka"]}
    }
    res = resume_agent.process(state)
    assert "Kubernetes" in res["skill_gaps"]
    assert "Kafka" in res["skill_gaps"]
    assert "Python" not in res["skill_gaps"]


def test_question_agent():
    state: InterviewState = {
        "target_role": "Python Backend Engineer",
        "current_difficulty": "Medium",
        "current_question_index": 0,
        "total_questions": 3,
        "candidate_profile": {"name": "Alex", "skills": ["Python", "Django"]},
        "skill_gaps": ["PostgreSQL", "Docker"],
        "previous_topics": [],
        "question_history": [],
        "answer_history": [],
        "evaluation_history": []
    }
    res = question_agent.process(state)
    q = res["current_question"]
    assert "question" in q
    assert "topic" in q
    assert "difficulty" in q


def test_evaluation_agent():
    state: InterviewState = {
        "current_question": {
            "question": "Explain how the Python GIL affects multithreading.",
            "topic": "Python & OOP",
            "difficulty": "Medium",
            "expected_concepts": ["GIL", "CPython mutex", "multiprocessing"]
        },
        "current_answer": "The Python GIL is a mutex in CPython that prevents multiple native threads from executing bytecodes at the same time.",
        "current_difficulty": "Medium",
        "question_history": [],
        "answer_history": [],
        "evaluation_history": [],
        "current_question_index": 0
    }
    res = evaluation_agent.process(state)
    ev = res["current_evaluation"]
    assert ev["technical_accuracy"] >= 50.0
    assert "overall_score" in ev
    assert len(ev["strengths"]) > 0
    assert "feedback" in ev


def test_interview_full_api_cycle(client):
    # 1. Start interview
    start_payload = {
        "target_role": "Senior Cloud Engineer",
        "interview_type": "Technical",
        "difficulty": "Medium",
        "total_questions": 1
    }
    start_resp = client.post("/interviews/start", json=start_payload)
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    session_id = start_data["session_id"]
    assert start_data["question_number"] == 1
    assert "question" in start_data["question"]

    # 2. Submit answer
    answer_payload = {
        "answer_text": "We deploy Docker containers onto Kubernetes clusters managed by AWS EKS, using Helm charts for declarative updates."
    }
    answer_resp = client.post(f"/interviews/{session_id}/answer", json=answer_payload)
    assert answer_resp.status_code == 200
    eval_data = answer_resp.json()["evaluation"]
    assert eval_data["overall_score"] > 0

    # 3. Request next question (should finalize session since total_questions = 1)
    next_resp = client.post(f"/interviews/{session_id}/next")
    assert next_resp.status_code == 200
    next_data = next_resp.json()
    assert next_data["is_completed"] is True
    assert next_data["recommendations"] is not None
    assert next_data["readiness_label"] in ["Interview Ready", "Almost Ready", "Needs Improvement"]
