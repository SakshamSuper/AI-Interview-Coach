from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from database.models import InterviewSession, AnswerEvaluation, SkillGapAnalysis


def aggregate_user_analytics(user_id: Optional[int], db: Session) -> Dict[str, Any]:
    query = db.query(InterviewSession)
    if user_id:
        query = query.filter(InterviewSession.user_id == user_id)

    sessions = query.order_by(InterviewSession.created_at.asc()).all()

    if not sessions:
        return {
            "total_interviews": 0,
            "overall_readiness_label": "Not Evaluated",
            "average_overall_score": 0.0,
            "average_technical_score": 0.0,
            "average_communication_score": 0.0,
            "average_relevance_score": 0.0,
            "average_completeness_score": 0.0,
            "average_clarity_score": 0.0,
            "topic_performance": {},
            "score_history": [],
            "recent_interviews": [],
            "strong_areas": [],
            "weak_areas": []
        }

    completed_sessions = [s for s in sessions if s.status == "completed" and s.overall_score is not None]

    score_history = [
        {
            "session_id": s.id,
            "date": s.created_at.strftime("%Y-%m-%d %H:%M"),
            "role": s.target_role,
            "score": s.overall_score,
            "difficulty": s.difficulty,
            "readiness": s.readiness_label or "In Progress"
        }
        for s in sessions
    ]

    all_evaluations: List[AnswerEvaluation] = []
    for s in sessions:
        all_evaluations.extend(s.evaluations)

    topic_scores: Dict[str, List[float]] = {}
    for s in sessions:
        for q in s.questions:
            if q.answer and q.answer.evaluation:
                t = q.topic
                if t not in topic_scores:
                    topic_scores[t] = []
                topic_scores[t].append(q.answer.evaluation.overall_score)

    topic_performance = {
        t: round(sum(scores) / len(scores), 1)
        for t, scores in topic_scores.items()
    }

    avg_overall = (sum(s.overall_score for s in completed_sessions) / len(completed_sessions)) if completed_sessions else 0.0
    avg_tech = (sum(e.technical_accuracy for e in all_evaluations) / len(all_evaluations)) if all_evaluations else 0.0
    avg_comm = (sum(e.communication for e in all_evaluations) / len(all_evaluations)) if all_evaluations else 0.0
    avg_rel = (sum(e.relevance for e in all_evaluations) / len(all_evaluations)) if all_evaluations else 0.0
    avg_comp = (sum(e.completeness for e in all_evaluations) / len(all_evaluations)) if all_evaluations else 0.0
    avg_clar = (sum(e.clarity for e in all_evaluations) / len(all_evaluations)) if all_evaluations else 0.0

    if completed_sessions:
        latest_session = completed_sessions[-1]
        readiness_label = latest_session.readiness_label or (
            "Interview Ready" if avg_overall >= 80 else ("Almost Ready" if avg_overall >= 60 else "Needs Improvement")
        )
    else:
        readiness_label = "Not Evaluated"

    strong_areas = [t for t, s in topic_performance.items() if s >= 75.0]
    weak_areas = [t for t, s in topic_performance.items() if s < 65.0]

    return {
        "total_interviews": len(sessions),
        "completed_interviews": len(completed_sessions),
        "overall_readiness_label": readiness_label,
        "average_overall_score": round(avg_overall, 1),
        "average_technical_score": round(avg_tech, 1),
        "average_communication_score": round(avg_comm, 1),
        "average_relevance_score": round(avg_rel, 1),
        "average_completeness_score": round(avg_comp, 1),
        "average_clarity_score": round(avg_clar, 1),
        "topic_performance": topic_performance,
        "score_history": score_history,
        "strong_areas": strong_areas,
        "weak_areas": weak_areas
    }
