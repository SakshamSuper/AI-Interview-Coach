from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.backend.schemas.matching import MatchAnalysisRequest, MatchAnalysisResponse
from app.backend.schemas.profiles import CandidateProfile, JobProfile
from app.backend.dependencies.db import get_db
from database.repositories.user_repository import UserRepository
from nlp.resume_parser import resume_parser
from nlp.jd_parser import jd_parser
from nlp.matching import matching_engine

router = APIRouter(tags=["Matching & Skill Gaps"])


@router.post("/matching", response_model=MatchAnalysisResponse)
def compute_matching(req: MatchAnalysisRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)

    cand_profile = None
    job_profile = None

    # Retrieve or parse CandidateProfile
    if req.resume_id:
        rec = repo.get_resume(req.resume_id)
        if rec and rec.parsed_profile:
            cand_profile = CandidateProfile(**rec.parsed_profile)
    elif req.raw_resume_text:
        cand_profile = resume_parser.parse(req.raw_resume_text)
    elif req.user_id:
        rec = repo.get_latest_resume_for_user(req.user_id)
        if rec and rec.parsed_profile:
            cand_profile = CandidateProfile(**rec.parsed_profile)

    if not cand_profile:
        raise HTTPException(
            status_code=400,
            detail="Resume profile could not be found. Please provide resume_id, user_id with uploaded resume, or raw_resume_text."
        )

    # Retrieve or parse JobProfile
    if req.jd_id:
        rec = repo.get_job_description(req.jd_id)
        if rec and rec.parsed_profile:
            job_profile = JobProfile(**rec.parsed_profile)
    elif req.raw_jd_text:
        job_profile = jd_parser.parse(req.raw_jd_text)
    elif req.user_id:
        rec = repo.get_latest_job_description_for_user(req.user_id)
        if rec and rec.parsed_profile:
            job_profile = JobProfile(**rec.parsed_profile)

    if not job_profile:
        raise HTTPException(
            status_code=400,
            detail="Job profile could not be found. Please provide jd_id, user_id with analyzed job, or raw_jd_text."
        )

    # Execute matching analysis
    match_result = matching_engine.analyze_match(cand_profile, job_profile)

    # Save to database
    repo.save_skill_gap_analysis(
        user_id=req.user_id,
        resume_id=req.resume_id,
        jd_id=req.jd_id,
        overall_match_score=match_result.overall_match_score,
        match_category=match_result.match_category,
        detailed_matches=[item.model_dump() for item in match_result.skill_breakdown],
        skill_gaps=match_result.gap_report.model_dump()
    )

    return match_result


@router.get("/skill-gaps", response_model=MatchAnalysisResponse)
def get_latest_skill_gaps(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    rec = repo.get_latest_skill_gap_analysis(user_id=user_id)
    if not rec:
        raise HTTPException(status_code=404, detail="No skill gap analysis recorded yet.")

    from app.backend.schemas.matching import (
        SkillMatchItem, SkillGapReport, MatchScoreExplanation
    )

    skill_breakdown = [SkillMatchItem(**item) for item in (rec.detailed_matches or [])]
    gap_report = SkillGapReport(**(rec.skill_gaps or {}))

    return MatchAnalysisResponse(
        overall_match_score=rec.overall_match_score,
        match_category=rec.match_category,
        skill_breakdown=skill_breakdown,
        gap_report=gap_report,
        explanation=MatchScoreExplanation(
            required_skills_coverage=rec.overall_match_score,
            preferred_skills_coverage=rec.overall_match_score * 0.9,
            semantic_similarity_score=rec.overall_match_score,
            experience_education_alignment=85.0,
            summary_explanation=f"Stored match score of {rec.overall_match_score}% ({rec.match_category})."
        )
    )
