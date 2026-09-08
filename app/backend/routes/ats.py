"""
app/backend/routes/ats.py
==========================
ATS-style Resume Compatibility Score endpoint.

POST /ats/score
  - Loads resume + JD from DB (already parsed on upload)
  - Delegates to existing MatchingEngine.analyze_match()
  - Adds education_alignment + resume_completeness scoring
  - Returns ATSScoreResponse with component breakdown + recommendations

No duplicate parsing: CandidateProfile and JobProfile are reconstructed
from the parsed_profile JSON columns already stored in the DB.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.backend.dependencies.db import get_db
from app.backend.schemas.ats import ATSScoreResponse, ATSComponent
from app.backend.schemas.profiles import CandidateProfile, JobProfile
from database.repositories.user_repository import UserRepository
from nlp.matching import matching_engine

router = APIRouter(prefix="/ats", tags=["ATS Score"])

DISCLAIMER = (
    "This is an application-generated ATS-style compatibility score for guidance only. "
    "It is not produced by or affiliated with any applicant tracking system "
    "(Workday, Greenhouse, Lever, iCIMS, etc.)."
)


class ATSScoreRequest(BaseModel):
    resume_id: int
    jd_id: int


def _score_education(candidate: CandidateProfile, job: JobProfile) -> float:
    """Score education alignment: 0-100."""
    requirements = [r.lower() for r in job.education_requirements]
    if not requirements:
        return 75.0  # No stated requirement — neutral

    degree_keywords = {
        "phd": ["phd", "ph.d", "doctor"],
        "master": ["master", "m.s", "ms", "mtech", "mba", "m.eng"],
        "bachelor": ["bachelor", "b.s", "bs", "btech", "b.e", "b.eng", "undergraduate"],
        "associate": ["associate"],
    }

    candidate_degrees = " ".join(
        f"{e.degree} {e.field_of_study or ''}".lower()
        for e in candidate.education
    )
    req_text = " ".join(requirements)

    # Check if any degree keyword in requirements matches candidate education
    for tier_keywords in degree_keywords.values():
        req_match = any(kw in req_text for kw in tier_keywords)
        cand_match = any(kw in candidate_degrees for kw in tier_keywords)
        if req_match and cand_match:
            return 95.0
        if req_match and not cand_match:
            return 45.0

    return 70.0  # Requirement found but could not parse — neutral-low


def _score_completeness(candidate: CandidateProfile) -> float:
    """Score resume completeness based on presence of key sections: 0-100."""
    checks = [
        bool(candidate.name and candidate.name != "Unknown"),   # name
        bool(candidate.contact and candidate.contact.email),    # email
        len(candidate.skills) >= 3,                             # skills
        len(candidate.experience) >= 1,                         # experience
        len(candidate.education) >= 1,                          # education
    ]
    return round(sum(checks) / len(checks) * 100, 1)


def _ats_grade(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _build_recommendations(components: list[ATSComponent], missing: list[str]) -> list[str]:
    recs = []
    score_map = {c.name: c.score for c in components}

    if score_map.get("Keyword & Skill Coverage", 100) < 60 and missing:
        top = ", ".join(missing[:4])
        recs.append(f"Add these missing or weak keywords to your resume: {top}.")

    if score_map.get("Semantic Relevance", 100) < 55:
        recs.append(
            "Align your resume language with the job description — mirror key phrases and terminology."
        )

    if score_map.get("Required Skill Coverage", 100) < 60:
        req_missing = [k for k in missing[:6]]
        if req_missing:
            recs.append(
                f"You are missing required skills: {', '.join(req_missing[:4])}. "
                "Add project or work experience demonstrating these."
            )

    if score_map.get("Experience Alignment", 100) < 60:
        recs.append(
            "The role requires more years of experience than your resume shows. "
            "Highlight relevant projects and impact metrics to bridge the gap."
        )

    if score_map.get("Education Alignment", 100) < 60:
        recs.append(
            "The job description specifies an education requirement not clearly reflected in your resume. "
            "Make your degree and field of study prominent."
        )

    if score_map.get("Resume Completeness", 100) < 80:
        recs.append(
            "Improve resume completeness: add your contact email, more work experience entries, "
            "or a skills section with at least 5 skills."
        )

    if not recs:
        recs.append("Strong profile! Continue tailoring your resume for each specific role.")

    return recs[:5]


@router.post("/score", response_model=ATSScoreResponse)
def compute_ats_score(req: ATSScoreRequest, db: Session = Depends(get_db)):
    """
    Compute an ATS-style compatibility score for a resume + job description pair.
    Reuses all existing NLP parsing and MatchingEngine infrastructure.
    """
    repo = UserRepository(db)

    # Load resume from DB (already parsed on upload)
    resume_rec = repo.get_resume(req.resume_id)
    if not resume_rec:
        raise HTTPException(status_code=404, detail=f"Resume id={req.resume_id} not found.")
    if not resume_rec.parsed_profile:
        raise HTTPException(status_code=422, detail="Resume has not been parsed. Re-upload the resume.")

    # Load JD from DB (already parsed on analyze)
    jd_rec = repo.get_job_description(req.jd_id)
    if not jd_rec:
        raise HTTPException(status_code=404, detail=f"Job description id={req.jd_id} not found.")
    if not jd_rec.parsed_profile:
        raise HTTPException(status_code=422, detail="Job description has not been parsed. Re-analyze it.")

    # Reconstruct typed profiles from stored JSON
    candidate = CandidateProfile(**resume_rec.parsed_profile)
    job = JobProfile(**jd_rec.parsed_profile)

    # Run existing MatchingEngine (provides 4 of 6 ATS components)
    match = matching_engine.analyze_match(candidate, job)
    exp = match.explanation

    # Compute 2 new components
    edu_score = _score_education(candidate, job)
    completeness_score = _score_completeness(candidate)

    # Required-skills-only sub-score
    req_scores = [
        item.match_score for item in match.skill_breakdown if item.is_required
    ]
    req_only_avg = round(sum(req_scores) / len(req_scores), 1) if req_scores else exp.required_skills_coverage

    # Build component list (ordered by weight desc)
    components = [
        ATSComponent(
            name="Keyword & Skill Coverage",
            score=round(exp.required_skills_coverage, 1),
            weight=0.28,
            description="How well your skills match the keywords and skills listed in the job description."
        ),
        ATSComponent(
            name="Required Skill Coverage",
            score=req_only_avg,
            weight=0.22,
            description="Coverage of skills explicitly marked as required (not just preferred) by the employer."
        ),
        ATSComponent(
            name="Semantic Relevance",
            score=round(exp.semantic_similarity_score, 1),
            weight=0.20,
            description="Overall language and terminology alignment between your resume and the job description."
        ),
        ATSComponent(
            name="Experience Alignment",
            score=round(exp.experience_education_alignment, 1),
            weight=0.15,
            description="How well your years and type of experience match the role requirements."
        ),
        ATSComponent(
            name="Education Alignment",
            score=round(edu_score, 1),
            weight=0.10,
            description="Whether your educational background meets the degree or field requirements stated in the JD."
        ),
        ATSComponent(
            name="Resume Completeness",
            score=round(completeness_score, 1),
            weight=0.05,
            description="Presence of key resume sections: name, email, skills, experience, education."
        ),
    ]

    # Weighted overall ATS score
    overall = sum(c.score * c.weight for c in components)
    overall = round(max(0.0, min(100.0, overall)), 1)

    # Keyword classification
    matched = [
        item.skill for item in match.skill_breakdown
        if item.category in ("Strong Match", "Matched")
    ]
    missing = (
        [item.skill for item in match.skill_breakdown if item.category in ("Partially Matched", "Missing") and item.is_required] +
        [item.skill for item in match.skill_breakdown if item.category in ("Partially Matched", "Missing") and not item.is_required]
    )

    recommendations = _build_recommendations(components, missing)

    return ATSScoreResponse(
        overall_ats_score=overall,
        grade=_ats_grade(overall),
        components=components,
        matched_keywords=matched,
        missing_keywords=missing,
        recommendations=recommendations,
        disclaimer=DISCLAIMER,
    )
