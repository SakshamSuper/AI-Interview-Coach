from typing import TypedDict, List, Dict, Any, Optional


class InterviewState(TypedDict, total=False):
    session_id: int
    user_id: Optional[int]
    target_role: str
    interview_type: str
    current_difficulty: str
    total_questions: int
    current_question_index: int
    candidate_profile: Dict[str, Any]
    job_profile: Dict[str, Any]
    skill_gaps: List[str]
    previous_topics: List[str]
    current_question: Optional[Dict[str, Any]]
    current_answer: Optional[str]
    current_evaluation: Optional[Dict[str, Any]]
    question_history: List[Dict[str, Any]]
    answer_history: List[str]
    evaluation_history: List[Dict[str, Any]]
    recommendations: Optional[Dict[str, Any]]
    status: str
