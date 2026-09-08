from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class SkillMatchItem(BaseModel):
    skill: str
    match_score: float = Field(..., ge=0.0, le=100.0)  # Percentage 0 - 100
    category: str  # Strong Match, Matched, Partially Matched, Missing
    is_required: bool
    context_found: Optional[str] = None


class SkillGapItem(BaseModel):
    skill: str
    is_required: bool
    gap_priority: str  # High, Medium, Low
    current_proficiency_estimate: float
    recommended_topics: List[str] = Field(default_factory=list)


class SkillGapReport(BaseModel):
    strong_skills: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    partially_matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    high_priority_gaps: List[SkillGapItem] = Field(default_factory=list)


class MatchScoreExplanation(BaseModel):
    required_skills_coverage: float
    preferred_skills_coverage: float
    semantic_similarity_score: float
    experience_education_alignment: float
    summary_explanation: str


class MatchAnalysisResponse(BaseModel):
    overall_match_score: float
    match_category: str  # Strong Match, Moderate Match, Weak Match
    skill_breakdown: List[SkillMatchItem]
    gap_report: SkillGapReport
    explanation: MatchScoreExplanation

    model_config = ConfigDict(from_attributes=True)


class MatchAnalysisRequest(BaseModel):
    user_id: Optional[int] = None
    resume_id: Optional[int] = None
    jd_id: Optional[int] = None
    raw_resume_text: Optional[str] = None
    raw_jd_text: Optional[str] = None
