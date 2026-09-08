from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.backend.schemas.interviews import (
    InterviewStartRequest, InterviewStartResponse,
    AnswerSubmitRequest, AnswerSubmitResponse,
    NextQuestionResponse, InterviewSessionSummary
)
from app.backend.schemas.profiles import CandidateProfile, JobProfile
from app.backend.dependencies.db import get_db
from database.repositories.interview_repository import InterviewRepository
from database.repositories.user_repository import UserRepository
from agents.question_agent import question_agent
from agents.evaluation_agent import evaluation_agent
from agents.recommendation_agent import recommendation_agent
from llm.structured_output import InterviewQuestion, AnswerEvaluation, RecommendationOutput
from ml.predictor import ml_predictor
from config.logger import logger

router = APIRouter(tags=["Interviews"])


@router.post("/interviews/start", response_model=InterviewStartResponse)
def start_interview(req: InterviewStartRequest, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    int_repo = InterviewRepository(db)

    cand_profile = None
    if req.resume_id:
        res_rec = user_repo.get_resume(req.resume_id)
        if res_rec and res_rec.parsed_profile:
            cand_profile = CandidateProfile(**res_rec.parsed_profile)
    elif req.user_id:
        res_rec = user_repo.get_latest_resume_for_user(req.user_id)
        if res_rec and res_rec.parsed_profile:
            cand_profile = CandidateProfile(**res_rec.parsed_profile)

    if not cand_profile:
        cand_profile = CandidateProfile(
            name="Candidate",
            skills=["Python", "System Design", "SQL"],
            experience=[]
        )

    job_profile = None
    if req.jd_id:
        jd_rec = user_repo.get_job_description(req.jd_id)
        if jd_rec and jd_rec.parsed_profile:
            job_profile = JobProfile(**jd_rec.parsed_profile)
    elif req.user_id:
        jd_rec = user_repo.get_latest_job_description_for_user(req.user_id)
        if jd_rec and jd_rec.parsed_profile:
            job_profile = JobProfile(**jd_rec.parsed_profile)

    if not job_profile:
        job_profile = JobProfile(
            job_title=req.target_role or "Senior Software Engineer",
            required_skills=["System Design", "Microservices", "Python"],
            preferred_skills=["Docker", "Kubernetes"]
        )

    target_role = req.target_role or job_profile.job_title

    session = int_repo.create_session(
        user_id=req.user_id,
        target_role=target_role,
        interview_type=req.interview_type or "Technical",
        difficulty=req.difficulty or "Medium",
        total_questions=req.total_questions or 5
    )

    state = {
        "session_id": session.id,
        "target_role": target_role,
        "current_difficulty": session.difficulty,
        "current_question_index": 0,
        "total_questions": session.total_questions,
        "candidate_profile": cand_profile.model_dump(),
        "job_profile": job_profile.model_dump(),
        "skill_gaps": [s for s in job_profile.required_skills if s not in set(cand_profile.skills)],
        "previous_topics": [],
        "question_history": [],
        "answer_history": [],
        "evaluation_history": []
    }

    q_res = question_agent.process(state)
    q_data = q_res["current_question"]
    question_obj = InterviewQuestion(**q_data)

    db_q = int_repo.add_question(
        session_id=session.id,
        question_number=1,
        question_text=question_obj.question,
        topic=question_obj.topic,
        difficulty=question_obj.difficulty,
        question_type=question_obj.question_type,
        reason=question_obj.reason,
        expected_concepts=question_obj.expected_concepts,
        source_context=question_obj.source_context
    )

    return InterviewStartResponse(
        session_id=session.id,
        target_role=session.target_role,
        interview_type=session.interview_type,
        difficulty=session.difficulty,
        total_questions=session.total_questions,
        question_number=1,
        question=question_obj
    )


@router.get("/interviews/{session_id}/question", response_model=InterviewQuestion)
def get_current_question(session_id: int, db: Session = Depends(get_db)):
    int_repo = InterviewRepository(db)
    session = int_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    curr_idx = session.current_question_index + 1
    q = int_repo.get_question_by_number(session_id, curr_idx)
    if not q:
        questions = int_repo.get_questions_for_session(session_id)
        if not questions:
            raise HTTPException(status_code=404, detail="No questions found for this session.")
        q = questions[-1]

    return InterviewQuestion(
        question=q.question_text,
        topic=q.topic,
        difficulty=q.difficulty,
        question_type=q.question_type,
        reason=q.reason,
        expected_concepts=q.expected_concepts or [],
        source_context=q.source_context
    )


@router.post("/interviews/{session_id}/answer", response_model=AnswerSubmitResponse)
def submit_answer(session_id: int, req: AnswerSubmitRequest, db: Session = Depends(get_db)):
    int_repo = InterviewRepository(db)
    session = int_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    questions = int_repo.get_questions_for_session(session_id)
    if not questions:
        raise HTTPException(status_code=400, detail="No active question to answer.")

    current_q = questions[-1]

    ans_record = int_repo.record_answer(
        session_id=session_id,
        question_id=current_q.id,
        candidate_answer=req.answer_text,
        audio_path=req.audio_path
    )

    state = {
        "current_question": {
            "question": current_q.question_text,
            "topic": current_q.topic,
            "difficulty": current_q.difficulty,
            "expected_concepts": current_q.expected_concepts or []
        },
        "current_answer": req.answer_text,
        "current_difficulty": session.difficulty,
        "question_history": [{"question": q.question_text, "topic": q.topic} for q in questions],
        "answer_history": [ans_record.candidate_answer],
        "evaluation_history": [],
        "current_question_index": session.current_question_index
    }

    eval_out = evaluation_agent.process(state)
    eval_dict = eval_out["current_evaluation"]
    eval_obj = AnswerEvaluation(**eval_dict)

    int_repo.record_evaluation(
        session_id=session_id,
        answer_id=ans_record.id,
        technical_accuracy=eval_obj.technical_accuracy,
        relevance=eval_obj.relevance,
        completeness=eval_obj.completeness,
        clarity=eval_obj.clarity,
        communication=eval_obj.communication,
        overall_score=eval_obj.overall_score,
        strengths=eval_obj.strengths,
        weaknesses=eval_obj.weaknesses,
        missing_concepts=eval_obj.missing_concepts,
        feedback=eval_obj.feedback,
        next_difficulty=eval_obj.next_difficulty
    )

    if eval_obj.next_difficulty:
        session.difficulty = eval_obj.next_difficulty
        db.commit()

    is_last = (session.current_question_index >= session.total_questions)

    return AnswerSubmitResponse(
        session_id=session_id,
        question_id=current_q.id,
        evaluation=eval_obj,
        is_last_question=is_last
    )


@router.post("/interviews/{session_id}/next", response_model=NextQuestionResponse)
def get_next_question(session_id: int, db: Session = Depends(get_db)):
    int_repo = InterviewRepository(db)
    session = int_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    if session.current_question_index >= session.total_questions:
        questions = int_repo.get_questions_for_session(session_id)
        evaluations = session.evaluations
        answers = session.answers

        state = {
            "target_role": session.target_role,
            "question_history": [{"question": q.question_text, "topic": q.topic, "difficulty": q.difficulty} for q in questions],
            "evaluation_history": [
                {
                    "overall_score": e.overall_score,
                    "strengths": e.strengths or [],
                    "weaknesses": e.weaknesses or []
                }
                for e in evaluations
            ],
            "skill_gaps": []
        }

        rec_out = recommendation_agent.process(state)
        rec_data = rec_out["recommendations"]
        rec_obj = RecommendationOutput(**rec_data)

        # Average individual scores
        avg_tech = sum(e.technical_accuracy for e in evaluations) / len(evaluations) if evaluations else 70.0
        avg_rel = sum(e.relevance for e in evaluations) / len(evaluations) if evaluations else 70.0
        avg_comp = sum(e.completeness for e in evaluations) / len(evaluations) if evaluations else 70.0
        avg_clar = sum(e.clarity for e in evaluations) / len(evaluations) if evaluations else 70.0
        avg_comm = sum(e.communication for e in evaluations) / len(evaluations) if evaluations else 70.0
        avg_score = sum(e.overall_score for e in evaluations) / len(evaluations) if evaluations else 70.0

        total_words = sum(len(a.candidate_answer.split()) for a in answers)
        avg_len = (total_words / len(answers)) if answers else 50

        diff_num = 3 if session.difficulty == "Hard" else (2 if session.difficulty == "Medium" else 1)

        # Predict readiness using Scikit-Learn Model
        ml_features = {
            "technical_score": avg_tech,
            "relevance_score": avg_rel,
            "completeness_score": avg_comp,
            "clarity_score": avg_clar,
            "communication_score": avg_comm,
            "answer_length": avg_len,
            "keyword_coverage": min(1.0, avg_comp / 100.0),
            "difficulty_numeric": diff_num,
            "attempt_number": len(evaluations),
            "previous_score": avg_score,
            "average_previous_score": avg_score,
            "topic_accuracy": avg_tech
        }
        ml_res = ml_predictor.predict_readiness(ml_features)

        readiness_label = ml_res["readiness_label"]
        readiness_score = ml_res["readiness_score"]

        int_repo.complete_session(
            session_id=session_id,
            overall_score=round(avg_score, 1),
            readiness_score=readiness_score,
            readiness_label=readiness_label
        )

        int_repo.save_recommendation(
            session_id=session_id,
            user_id=session.user_id,
            overall_summary=rec_obj.overall_summary,
            strong_areas=rec_obj.strong_areas,
            weak_areas=rec_obj.weak_areas,
            learning_priorities=rec_obj.learning_priorities,
            practice_questions=rec_obj.practice_questions
        )

        return NextQuestionResponse(
            session_id=session_id,
            is_completed=True,
            total_questions=session.total_questions,
            current_difficulty=session.difficulty,
            recommendations=rec_obj,
            overall_score=round(avg_score, 1),
            readiness_label=readiness_label,
            readiness_score=readiness_score
        )

    # Next question generation
    questions = int_repo.get_questions_for_session(session_id)
    evaluations = session.evaluations
    answers = session.answers

    user_repo = UserRepository(db)
    cand_profile = None
    if session.user_id:
        res_rec = user_repo.get_latest_resume_for_user(session.user_id)
        if res_rec and res_rec.parsed_profile:
            cand_profile = CandidateProfile(**res_rec.parsed_profile)
    if not cand_profile:
        cand_profile = CandidateProfile(
            name="Candidate",
            skills=["Python", "System Design", "SQL"],
            experience=[]
        )

    job_profile = None
    if session.user_id:
        jd_rec = user_repo.get_latest_job_description_for_user(session.user_id)
        if jd_rec and jd_rec.parsed_profile:
            job_profile = JobProfile(**jd_rec.parsed_profile)
    if not job_profile:
        job_profile = JobProfile(
            job_title=session.target_role,
            required_skills=["System Design", "Microservices", "Python"],
            preferred_skills=["Docker", "Kubernetes"]
        )

    skill_gaps = [s for s in job_profile.required_skills if s not in set(cand_profile.skills)]

    state = {
        "session_id": session_id,
        "target_role": session.target_role,
        "current_difficulty": session.difficulty,
        "current_question_index": session.current_question_index,
        "total_questions": session.total_questions,
        "candidate_profile": cand_profile.model_dump(),
        "job_profile": job_profile.model_dump(),
        "skill_gaps": skill_gaps,
        "previous_topics": [q.topic for q in questions],
        "question_history": [{"question": q.question_text, "topic": q.topic} for q in questions],
        "answer_history": [a.candidate_answer for a in answers],
        "evaluation_history": [
            {
                "technical_accuracy": e.technical_accuracy,
                "overall_score": e.overall_score,
                "missing_concepts": e.missing_concepts or [],
                "weaknesses": e.weaknesses or []
            }
            for e in evaluations
        ]
    }

    q_res = question_agent.process(state)
    q_data = q_res["current_question"]
    question_obj = InterviewQuestion(**q_data)

    next_num = len(questions) + 1
    int_repo.add_question(
        session_id=session.id,
        question_number=next_num,
        question_text=question_obj.question,
        topic=question_obj.topic,
        difficulty=question_obj.difficulty,
        question_type=question_obj.question_type,
        reason=question_obj.reason,
        expected_concepts=question_obj.expected_concepts,
        source_context=question_obj.source_context
    )

    return NextQuestionResponse(
        session_id=session_id,
        is_completed=False,
        question_number=next_num,
        total_questions=session.total_questions,
        current_difficulty=session.difficulty,
        question=question_obj
    )


@router.get("/interviews/{session_id}", response_model=InterviewSessionSummary)
def get_interview_session(session_id: int, db: Session = Depends(get_db)):
    int_repo = InterviewRepository(db)
    session = int_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    # The ORM InterviewSession uses `id` as its primary key column name.
    # The response schema InterviewSessionSummary exposes it as `session_id`.
    # FastAPI's response model serialization cannot bridge this rename
    # automatically, so we construct the schema explicitly here.
    return InterviewSessionSummary(
        session_id=session.id,
        user_id=session.user_id,
        target_role=session.target_role,
        interview_type=session.interview_type,
        difficulty=session.difficulty,
        status=session.status,
        total_questions=session.total_questions,
        current_question_index=session.current_question_index,
        overall_score=session.overall_score,
        readiness_score=session.readiness_score,
        readiness_label=session.readiness_label,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )



@router.get("/interviews/", response_model=List[InterviewSessionSummary])
def list_interviews(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Return all sessions for a user, newest first."""
    int_repo = InterviewRepository(db)
    sessions = int_repo.list_sessions_for_user(user_id=user_id)
    return [
        InterviewSessionSummary(
            session_id=s.id,
            user_id=s.user_id,
            target_role=s.target_role,
            interview_type=s.interview_type,
            difficulty=s.difficulty,
            status=s.status,
            total_questions=s.total_questions,
            current_question_index=s.current_question_index,
            overall_score=s.overall_score,
            readiness_score=s.readiness_score,
            readiness_label=s.readiness_label,
            created_at=s.created_at,
            completed_at=s.completed_at,
        )
        for s in sessions
    ]


@router.get("/ml/readiness")
def get_ml_readiness(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Invoke the existing ML readiness classifier using aggregated evaluation data.

    Feature derivation (FEATURE_COLUMNS order preserved exactly as in ml/preprocessing.py):
      technical_score       — avg AnswerEvaluation.technical_accuracy across all sessions
      relevance_score       — avg AnswerEvaluation.relevance
      completeness_score    — avg AnswerEvaluation.completeness
      clarity_score         — avg AnswerEvaluation.clarity
      communication_score   — avg AnswerEvaluation.communication
      answer_length         — avg word count of InterviewAnswer.candidate_answer (REAL)
      keyword_coverage      — avg(SkillMatchItem.match_score)/100 from SkillGapAnalysis.detailed_matches (REAL)
      difficulty_numeric    — avg of per-question difficulty_numeric: Easy=1, Medium=2, Hard=3 (REAL)
      attempt_number        — number of completed sessions for this user
      previous_score        — avg AnswerEvaluation.overall_score across all sessions
      average_previous_score— same as previous_score (aggregate equivalent)
      topic_accuracy        — avg AnswerEvaluation.technical_accuracy (best proxy for topic-specific perf)
    """
    from analytics.metrics import aggregate_user_analytics
    from database.models import InterviewSession, InterviewAnswer, InterviewQuestion

    analytics = aggregate_user_analytics(user_id=user_id, db=db)
    n = analytics.get("completed_interviews", 0)

    if n == 0:
        return {
            "has_data": False,
            "message": "No completed interview sessions yet. Complete an interview to get your ML readiness prediction.",
            "readiness_label": None,
            "readiness_score": None,
        }

    # ── Derive answer_length from real persisted candidate_answer text ────────
    DIFF_MAP = {"Easy": 1, "Medium": 2, "Hard": 3}

    answer_lengths = []
    difficulty_nums = []
    fallback_answer_length = False
    fallback_difficulty = False

    # Query all answers+questions for this user's sessions
    session_q = db.query(InterviewSession)
    if user_id:
        session_q = session_q.filter(InterviewSession.user_id == user_id)
    user_sessions = session_q.all()

    for session in user_sessions:
        for answer in session.answers:
            # answer_length: word count of actual candidate text
            text = answer.candidate_answer or ""
            words = len(text.split()) if text.strip() else None
            if words is not None and words > 0:
                answer_lengths.append(float(words))
            # difficulty_numeric: from the linked question's difficulty column
            if answer.question and answer.question.difficulty:
                diff_str = answer.question.difficulty
                diff_num = DIFF_MAP.get(diff_str)
                if diff_num is not None:
                    difficulty_nums.append(float(diff_num))

    # Compute averages; fall back to documented defaults if data missing
    if answer_lengths:
        avg_answer_length = round(sum(answer_lengths) / len(answer_lengths), 1)
    else:
        avg_answer_length = 80.0       # documented fallback — no answer text available
        fallback_answer_length = True

    if difficulty_nums:
        avg_difficulty_numeric = round(sum(difficulty_nums) / len(difficulty_nums), 3)
    else:
        avg_difficulty_numeric = 2.0   # documented fallback — no difficulty data available
        fallback_difficulty = True

    # ── Derive keyword_coverage from persisted SkillGapAnalysis.detailed_matches ──
    #
    # Training definition (ml/dataset.py line 46):
    #   kw_cov = clip(latent_ability * 0.85 + noise, 0.1, 1.0)
    #   Represents: fraction of JD keywords covered by the candidate, on 0-to-1 scale.
    #
    # Real inference equivalent (semantically identical):
    #   avg(SkillMatchItem.match_score for all JD skills) / 100.0
    #   where match_score ∈ [0, 100] = how well each JD keyword is covered by the candidate.
    #   Computed by nlp.matching.MatchingEngine.analyze_match() and already persisted
    #   in SkillGapAnalysis.detailed_matches (JSON column, no schema change required).
    #
    # Fallback (user never ran skill-gap analysis):
    #   0.5 — the neutral prior (training-set mean ≈ 0.46), NOT avg_overall/100.
    #   Explicitly flagged in keyword_coverage_source so it is never mistaken for real data.
    from database.repositories.user_repository import UserRepository
    import json as _json

    user_repo = UserRepository(db)
    skill_gap_rec = user_repo.get_latest_skill_gap_analysis(user_id=user_id)

    kw_coverage: float
    kw_coverage_source: str
    fallback_keyword_coverage = False

    if skill_gap_rec and skill_gap_rec.detailed_matches:
        dm = skill_gap_rec.detailed_matches
        # detailed_matches is stored as Python list via SQLAlchemy JSON column;
        # may be a raw string if driver serializes manually.
        if isinstance(dm, str):
            dm = _json.loads(dm)
        if dm and isinstance(dm, list):
            scores = [item.get("match_score", 0.0) for item in dm if isinstance(item, dict)]
            if scores:
                kw_coverage = round(sum(scores) / (len(scores) * 100.0), 4)
                kw_coverage_source = "real(avg_skill_match_score/100, SkillGapAnalysis.detailed_matches)"
            else:
                kw_coverage = 0.5
                kw_coverage_source = "neutral_prior(0.5, detailed_matches_empty)"
                fallback_keyword_coverage = True
        else:
            kw_coverage = 0.5
            kw_coverage_source = "neutral_prior(0.5, detailed_matches_malformed)"
            fallback_keyword_coverage = True
    else:
        # User has never run a matching / skill-gap analysis.
        # Use training-set neutral prior (≈0.5) rather than a semantically wrong proxy.
        kw_coverage = 0.5
        kw_coverage_source = "neutral_prior(0.5, no_skill_gap_analysis_run)"
        fallback_keyword_coverage = True

    # ── Build full feature vector (order must match FEATURE_COLUMNS exactly) ──
    avg_overall = analytics.get("average_overall_score", 0.0)
    avg_tech = analytics.get("average_technical_score", 0.0)

    features = {
        "technical_score":        avg_tech,
        "relevance_score":        analytics.get("average_relevance_score", 0.0),
        "completeness_score":     analytics.get("average_completeness_score", 0.0),
        "clarity_score":          analytics.get("average_clarity_score", 0.0),
        "communication_score":    analytics.get("average_communication_score", 0.0),
        "answer_length":          avg_answer_length,         # REAL: avg word count
        "keyword_coverage":       kw_coverage,               # REAL: avg JD skill match / 100
        "difficulty_numeric":     avg_difficulty_numeric,    # REAL: avg mapped difficulty
        "attempt_number":         float(n),
        "previous_score":         avg_overall,
        "average_previous_score": avg_overall,
        "topic_accuracy":         avg_tech,
    }

    prediction = ml_predictor.predict_readiness(features)
    prediction["has_data"] = True
    prediction["sessions_used"] = n
    prediction["feature_inputs"] = {
        "avg_technical":            features["technical_score"],
        "avg_relevance":            features["relevance_score"],
        "avg_completeness":         features["completeness_score"],
        "avg_clarity":              features["clarity_score"],
        "avg_communication":        features["communication_score"],
        "answer_length":            avg_answer_length,
        "answer_length_source":     "fallback(80.0)" if fallback_answer_length else "real(avg_word_count)",
        "keyword_coverage":         kw_coverage,
        "keyword_coverage_source":  kw_coverage_source,
        "difficulty_numeric":       avg_difficulty_numeric,
        "difficulty_source":        "fallback(2.0)" if fallback_difficulty else "real(avg_per_question)",
        "attempt_number":           float(n),
        "sessions_completed":       n,
        "avg_overall":              avg_overall,
    }
    return prediction


@router.get("/recommendations/{session_id}", response_model=RecommendationOutput)
def get_interview_recommendations(session_id: int, db: Session = Depends(get_db)):
    int_repo = InterviewRepository(db)
    session = int_repo.get_session(session_id)
    if not session or not session.recommendation:
        raise HTTPException(status_code=404, detail="Recommendations not found for this session.")
    rec = session.recommendation
    return RecommendationOutput(
        overall_summary=rec.overall_summary or "",
        strong_areas=rec.strong_areas or [],
        weak_areas=rec.weak_areas or [],
        learning_priorities=rec.learning_priorities or [],
        practice_questions=rec.practice_questions or []
    )

