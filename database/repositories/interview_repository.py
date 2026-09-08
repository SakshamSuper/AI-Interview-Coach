import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database.models import (
    InterviewSession, InterviewQuestion, InterviewAnswer,
    AnswerEvaluation, Recommendation, VisionSessionMetric
)


class InterviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, user_id: Optional[int], target_role: str,
                       interview_type: str = "Technical", difficulty: str = "Medium",
                       total_questions: int = 5) -> InterviewSession:
        session = InterviewSession(
            user_id=user_id,
            target_role=target_role,
            interview_type=interview_type,
            difficulty=difficulty,
            total_questions=total_questions,
            current_question_index=0,
            status="in_progress"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: int) -> Optional[InterviewSession]:
        return self.db.query(InterviewSession).filter(InterviewSession.id == session_id).first()

    def list_sessions_for_user(self, user_id: Optional[int] = None) -> List[InterviewSession]:
        query = self.db.query(InterviewSession)
        if user_id:
            query = query.filter(InterviewSession.user_id == user_id)
        return query.order_by(InterviewSession.created_at.desc()).all()

    def add_question(self, session_id: int, question_number: int, question_text: str,
                     topic: str, difficulty: str, question_type: str = "Technical",
                     reason: Optional[str] = None, expected_concepts: Optional[List[str]] = None,
                     source_context: Optional[str] = None) -> InterviewQuestion:
        q = InterviewQuestion(
            session_id=session_id,
            question_number=question_number,
            question_text=question_text,
            topic=topic,
            difficulty=difficulty,
            question_type=question_type,
            reason=reason,
            expected_concepts=expected_concepts or [],
            source_context=source_context
        )
        self.db.add(q)
        self.db.commit()
        self.db.refresh(q)
        return q

    def get_question_by_number(self, session_id: int, question_number: int) -> Optional[InterviewQuestion]:
        return self.db.query(InterviewQuestion).filter(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.question_number == question_number
        ).first()

    def get_questions_for_session(self, session_id: int) -> List[InterviewQuestion]:
        return self.db.query(InterviewQuestion).filter(
            InterviewQuestion.session_id == session_id
        ).order_by(InterviewQuestion.question_number.asc()).all()

    def record_answer(self, session_id: int, question_id: int,
                      candidate_answer: str, audio_path: Optional[str] = None) -> InterviewAnswer:
        ans = InterviewAnswer(
            session_id=session_id,
            question_id=question_id,
            candidate_answer=candidate_answer,
            audio_path=audio_path
        )
        self.db.add(ans)
        self.db.commit()
        self.db.refresh(ans)
        return ans

    def record_evaluation(self, session_id: int, answer_id: int,
                          technical_accuracy: float, relevance: float, completeness: float,
                          clarity: float, communication: float, overall_score: float,
                          strengths: List[str], weaknesses: List[str], missing_concepts: List[str],
                          feedback: str, next_difficulty: str) -> AnswerEvaluation:
        eval_record = AnswerEvaluation(
            session_id=session_id,
            answer_id=answer_id,
            technical_accuracy=technical_accuracy,
            relevance=relevance,
            completeness=completeness,
            clarity=clarity,
            communication=communication,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_concepts=missing_concepts,
            feedback=feedback,
            next_difficulty=next_difficulty
        )
        self.db.add(eval_record)

        # Update session difficulty and question index
        session = self.get_session(session_id)
        if session:
            session.difficulty = next_difficulty
            session.current_question_index += 1

        self.db.commit()
        self.db.refresh(eval_record)
        return eval_record

    def complete_session(self, session_id: int, overall_score: float,
                         readiness_score: float, readiness_label: str) -> Optional[InterviewSession]:
        session = self.get_session(session_id)
        if session:
            session.status = "completed"
            session.overall_score = overall_score
            session.readiness_score = readiness_score
            session.readiness_label = readiness_label
            session.completed_at = datetime.datetime.utcnow()
            self.db.commit()
            self.db.refresh(session)
        return session

    def save_recommendation(self, session_id: int, user_id: Optional[int],
                            overall_summary: str, strong_areas: List[str],
                            weak_areas: List[str], learning_priorities: List[str],
                            practice_questions: List[str]) -> Recommendation:
        rec = Recommendation(
            session_id=session_id,
            user_id=user_id,
            overall_summary=overall_summary,
            strong_areas=strong_areas,
            weak_areas=weak_areas,
            learning_priorities=learning_priorities,
            practice_questions=practice_questions
        )
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)
        return rec

    def record_vision_metrics(self, session_id: int, avg_posture_stability: float,
                              avg_movement_magnitude: float, movement_frequency: float,
                              frame_count: int) -> VisionSessionMetric:
        v = VisionSessionMetric(
            session_id=session_id,
            avg_posture_stability=avg_posture_stability,
            avg_movement_magnitude=avg_movement_magnitude,
            movement_frequency=movement_frequency,
            frame_count=frame_count
        )
        self.db.add(v)
        self.db.commit()
        self.db.refresh(v)
        return v
