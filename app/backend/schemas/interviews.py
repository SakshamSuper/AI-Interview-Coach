from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from llm.structured_output import InterviewQuestion, AnswerEvaluation, RecommendationOutput


class InterviewStartRequest(BaseModel):
    user_id: Optional[int] = None
    resume_id: Optional[int] = None
    jd_id: Optional[int] = None
    target_role: Optional[str] = "Senior Software Engineer"
    interview_type: Optional[str] = "Technical"
    difficulty: Optional[str] = "Medium"
    total_questions: Optional[int] = 5


class InterviewStartResponse(BaseModel):
    session_id: int
    target_role: str
    interview_type: str
    difficulty: str
    total_questions: int
    question_number: int
    question: InterviewQuestion


class AnswerSubmitRequest(BaseModel):
    answer_text: str
    audio_path: Optional[str] = None


class AnswerSubmitResponse(BaseModel):
    session_id: int
    question_id: int
    evaluation: AnswerEvaluation
    is_last_question: bool


class NextQuestionResponse(BaseModel):
    session_id: int
    is_completed: bool
    question_number: Optional[int] = None
    total_questions: int
    current_difficulty: str
    question: Optional[InterviewQuestion] = None
    recommendations: Optional[RecommendationOutput] = None
    overall_score: Optional[float] = None
    readiness_label: Optional[str] = None
    readiness_score: Optional[float] = None


class InterviewSessionSummary(BaseModel):
    session_id: int
    user_id: Optional[int]
    target_role: str
    interview_type: str
    difficulty: str
    status: str
    total_questions: int
    current_question_index: int
    overall_score: Optional[float]
    readiness_score: Optional[float]
    readiness_label: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
