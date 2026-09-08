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


def test_role_specific_question_generation():
    roles = [
        "Machine Learning Engineer",
        "Data Scientist",
        "Backend Systems Engineer",
        "Software Engineer"
    ]
    generated = {}
    for role in roles:
        state: InterviewState = {
            "target_role": role,
            "current_difficulty": "Medium",
            "current_question_index": 0,
            "total_questions": 3,
            "candidate_profile": {"name": "Test Candidate", "skills": ["Python"]},
            "skill_gaps": [],
            "previous_topics": [],
            "question_history": [],
            "answer_history": [],
            "evaluation_history": []
        }
        res = question_agent.process(state)
        q = res["current_question"]
        generated[role] = q

    # Verify that each role receives a distinct question
    questions = [g["question"] for g in generated.values()]
    assert len(set(questions)) == len(roles), "Each role must receive a distinct question!"

    # Verify role-appropriate topics
    assert any(k in generated["Machine Learning Engineer"]["topic"].lower() for k in ["deep learning", "inference", "rag", "ml"])
    assert any(k in generated["Data Scientist"]["topic"].lower() for k in ["experimentation", "predictive", "statistical", "a/b"])
    assert any(k in generated["Backend Systems Engineer"]["topic"].lower() for k in ["distributed", "concurrency", "caching", "systems"])
    assert any(k in generated["Software Engineer"]["topic"].lower() for k in ["structures", "architecture", "concurrency", "algorithms"])


def test_duplicate_question_prevention():
    state: InterviewState = {
        "target_role": "Machine Learning Engineer",
        "current_difficulty": "Medium",
        "current_question_index": 0,
        "total_questions": 3,
        "candidate_profile": {"name": "Candidate", "skills": ["Python", "PyTorch"]},
        "skill_gaps": [],
        "previous_topics": [],
        "question_history": [],
        "answer_history": [],
        "evaluation_history": []
    }

    asked_questions = []
    prev_topics = []

    for turn in range(3):
        state["current_question_index"] = turn
        state["previous_topics"] = prev_topics
        state["question_history"] = [{"question": q, "topic": "ML"} for q in asked_questions]
        res = question_agent.process(state)
        q = res["current_question"]["question"]
        t = res["current_question"]["topic"]
        assert q not in asked_questions, f"Turn {turn + 1} generated duplicate question: {q}"
        asked_questions.append(q)
        prev_topics.append(t)

    assert len(set(asked_questions)) == 3, "All 3 questions in the session must be 100% unique!"


def test_difficulty_adaptation(client):
    # 1. Start interview
    start_payload = {
        "target_role": "Backend Lead",
        "difficulty": "Medium",
        "total_questions": 2
    }
    start_resp = client.post("/interviews/start", json=start_payload)
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]

    # 2. Submit short/incomplete answer -> should adapt to Easy
    ans_resp = client.post(f"/interviews/{session_id}/answer", json={"answer_text": "Not sure."})
    assert ans_resp.status_code == 200
    eval_data = ans_resp.json()["evaluation"]
    assert eval_data["next_difficulty"] == "Easy"

    # 3. Next question should reflect the adapted difficulty
    next_resp = client.post(f"/interviews/{session_id}/next")
    assert next_resp.status_code == 200
    next_data = next_resp.json()
    assert next_data["current_difficulty"] == "Easy"

