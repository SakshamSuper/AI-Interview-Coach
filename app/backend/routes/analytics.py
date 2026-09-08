from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.backend.dependencies.db import get_db
from database.repositories.interview_repository import InterviewRepository
from analytics.metrics import aggregate_user_analytics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/{user_id}")
def get_user_analytics(user_id: int, db: Session = Depends(get_db)):
    data = aggregate_user_analytics(user_id=user_id, db=db)
    return data


@router.get("/session/{session_id}")
def get_session_analytics(session_id: int, db: Session = Depends(get_db)):
    repo = InterviewRepository(db)
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    evaluations = session.evaluations
    questions = session.questions
    answers = session.answers

    if not evaluations:
        return {
            "session_id": session_id,
            "status": session.status,
            "target_role": session.target_role,
            "has_evaluations": False
        }

    avg_tech = sum(e.technical_accuracy for e in evaluations) / len(evaluations)
    avg_rel = sum(e.relevance for e in evaluations) / len(evaluations)
    avg_comp = sum(e.completeness for e in evaluations) / len(evaluations)
    avg_clar = sum(e.clarity for e in evaluations) / len(evaluations)
    avg_comm = sum(e.communication for e in evaluations) / len(evaluations)
    avg_overall = sum(e.overall_score for e in evaluations) / len(evaluations)

    q_eval_list = []
    for q, a, e in zip(questions, answers, evaluations):
        q_eval_list.append({
            "question_number": q.question_number,
            "question_text": q.question_text,
            "topic": q.topic,
            "difficulty": q.difficulty,
            "candidate_answer": a.candidate_answer,
            "technical_accuracy": e.technical_accuracy,
            "relevance": e.relevance,
            "completeness": e.completeness,
            "clarity": e.clarity,
            "communication": e.communication,
            "overall_score": e.overall_score,
            "feedback": e.feedback,
            "strengths": e.strengths or [],
            "weaknesses": e.weaknesses or [],
            "missing_concepts": e.missing_concepts or []
        })

    return {
        "session_id": session_id,
        "target_role": session.target_role,
        "difficulty": session.difficulty,
        "status": session.status,
        "overall_score": session.overall_score or round(avg_overall, 1),
        "readiness_score": session.readiness_score,
        "readiness_label": session.readiness_label,
        "average_dimensions": {
            "technical_accuracy": round(avg_tech, 1),
            "relevance": round(avg_rel, 1),
            "completeness": round(avg_comp, 1),
            "clarity": round(avg_clar, 1),
            "communication": round(avg_comm, 1)
        },
        "questions_and_evaluations": q_eval_list,
        "recommendations": {
            "overall_summary": session.recommendation.overall_summary if session.recommendation else None,
            "strong_areas": session.recommendation.strong_areas if session.recommendation else [],
            "weak_areas": session.recommendation.weak_areas if session.recommendation else [],
            "learning_priorities": session.recommendation.learning_priorities if session.recommendation else [],
            "practice_questions": session.recommendation.practice_questions if session.recommendation else []
        } if session.recommendation else None
    }
