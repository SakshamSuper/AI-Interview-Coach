"""
app/backend/schemas/ats.py
===========================
Pydantic models for the ATS Resume Compatibility Score endpoint.
"""
from typing import List
from pydantic import BaseModel


class ATSComponent(BaseModel):
    name: str
    score: float          # 0.0 - 100.0
    weight: float         # proportion used in overall score
    description: str


class ATSScoreResponse(BaseModel):
    overall_ats_score: float          # 0.0 - 100.0
    grade: str                        # A / B / C / D / F
    components: List[ATSComponent]
    matched_keywords: List[str]       # Strong Match + Matched skills
    missing_keywords: List[str]       # Partially Matched + Missing skills (required first)
    recommendations: List[str]        # 3-5 actionable strings
    disclaimer: str                   # Always present
