import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    target_role = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    job_descriptions = relationship("JobDescription", back_populates="user", cascade="all, delete-orphan")
    interviews = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), default="pdf")
    raw_text = Column(Text, nullable=False)
    parsed_profile = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="resumes")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_profile = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="job_descriptions")


class SkillGapAnalysis(Base):
    __tablename__ = "skill_gap_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    jd_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=True)
    overall_match_score = Column(Float, nullable=False)
    match_category = Column(String(50), nullable=False)  # Strong, Moderate, Weak
    detailed_matches = Column(JSON, nullable=True)
    skill_gaps = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    target_role = Column(String(255), nullable=False)
    interview_type = Column(String(50), default="Technical")
    difficulty = Column(String(50), default="Medium")
    total_questions = Column(Integer, default=5)
    current_question_index = Column(Integer, default=0)
    status = Column(String(50), default="in_progress")  # in_progress, completed, abandoned
    overall_score = Column(Float, nullable=True)
    readiness_score = Column(Float, nullable=True)
    readiness_label = Column(String(50), nullable=True)  # Needs Improvement, Almost Ready, Interview Ready
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="interviews")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")
    answers = relationship("InterviewAnswer", back_populates="session", cascade="all, delete-orphan")
    evaluations = relationship("AnswerEvaluation", back_populates="session", cascade="all, delete-orphan")
    recommendation = relationship("Recommendation", back_populates="session", uselist=False, cascade="all, delete-orphan")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    topic = Column(String(100), nullable=False)
    difficulty = Column(String(50), nullable=False)
    question_type = Column(String(50), default="Technical")
    reason = Column(Text, nullable=True)
    expected_concepts = Column(JSON, nullable=True)
    source_context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("InterviewSession", back_populates="questions")
    answer = relationship("InterviewAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan")


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    candidate_answer = Column(Text, nullable=False)
    audio_path = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    question = relationship("InterviewQuestion", back_populates="answer")
    session = relationship("InterviewSession", back_populates="answers")
    evaluation = relationship("AnswerEvaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan")


class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("interview_answers.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    technical_accuracy = Column(Float, nullable=False)
    relevance = Column(Float, nullable=False)
    completeness = Column(Float, nullable=False)
    clarity = Column(Float, nullable=False)
    communication = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    missing_concepts = Column(JSON, nullable=True)
    feedback = Column(Text, nullable=True)
    next_difficulty = Column(String(50), default="Medium")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    answer = relationship("InterviewAnswer", back_populates="evaluation")
    session = relationship("InterviewSession", back_populates="evaluations")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    overall_summary = Column(Text, nullable=True)
    strong_areas = Column(JSON, nullable=True)
    weak_areas = Column(JSON, nullable=True)
    learning_priorities = Column(JSON, nullable=True)
    practice_questions = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("InterviewSession", back_populates="recommendation")


class VisionSessionMetric(Base):
    __tablename__ = "vision_session_metrics"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    avg_posture_stability = Column(Float, default=100.0)
    avg_movement_magnitude = Column(Float, default=0.0)
    movement_frequency = Column(Float, default=0.0)
    frame_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
