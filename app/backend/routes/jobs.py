from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.backend.schemas.profiles import JobAnalyzeRequest, JobAnalyzeResponse, JobProfile
from app.backend.dependencies.db import get_db
from database.repositories.user_repository import UserRepository
from nlp.jd_parser import jd_parser

router = APIRouter(prefix="/jobs", tags=["Job Descriptions"])


@router.post("/analyze", response_model=JobAnalyzeResponse)
def analyze_job_description(req: JobAnalyzeRequest, db: Session = Depends(get_db)):
    if not req.job_description_text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty.")

    profile = jd_parser.parse(req.job_description_text, default_title=req.title)

    repo = UserRepository(db)
    jd_record = repo.save_job_description(
        user_id=req.user_id,
        title=profile.job_title,
        raw_text=req.job_description_text,
        parsed_profile=profile.model_dump()
    )

    return JobAnalyzeResponse(
        jd_id=jd_record.id,
        profile=profile
    )


@router.get("/{jd_id}", response_model=JobAnalyzeResponse)
def get_job_description(jd_id: int, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    rec = repo.get_job_description(jd_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Job description not found.")
    profile = JobProfile(**rec.parsed_profile)
    return JobAnalyzeResponse(
        jd_id=rec.id,
        profile=profile
    )
