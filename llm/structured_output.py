import json
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class InterviewQuestion(BaseModel):
    question: str = Field(..., description="The interview question text.")
    topic: str = Field(..., description="Technical topic or domain.")
    difficulty: str = Field("Medium", description="Easy, Medium, or Hard.")
    question_type: str = Field("Technical", description="Technical, Behavioral, Problem-Solving, Scenario-Based.")
    reason: Optional[str] = Field(None, description="Reason this question was selected based on gaps or background.")
    expected_concepts: List[str] = Field(default_factory=list, description="Key concepts candidate should cover.")
    source_context: Optional[str] = Field(None, description="RAG or resume grounding snippet.")

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        v_title = v.strip().title()
        return v_title if v_title in ["Easy", "Medium", "Hard"] else "Medium"


class AnswerEvaluation(BaseModel):
    technical_accuracy: float = Field(..., ge=0.0, le=100.0)
    relevance: float = Field(..., ge=0.0, le=100.0)
    completeness: float = Field(..., ge=0.0, le=100.0)
    clarity: float = Field(..., ge=0.0, le=100.0)
    communication: float = Field(..., ge=0.0, le=100.0)
    overall_score: float = Field(..., ge=0.0, le=100.0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    feedback: str = Field(..., description="Constructive, actionable coaching feedback.")
    recommended_topics: List[str] = Field(default_factory=list)
    next_difficulty: str = Field("Medium", description="Recommended next difficulty: Easy, Medium, Hard.")

    @field_validator("next_difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        v_title = v.strip().title()
        return v_title if v_title in ["Easy", "Medium", "Hard"] else "Medium"


class RecommendationOutput(BaseModel):
    overall_summary: str
    strong_areas: List[str] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)
    learning_priorities: List[str] = Field(default_factory=list)
    practice_questions: List[str] = Field(default_factory=list)


def parse_and_repair_json(raw_text: str) -> Dict[str, Any]:
    """
    Extracts and repairs JSON from raw LLM output, handling markdown fences and common syntax errors.
    """
    cleaned = raw_text.strip()

    # Extract inside ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    # If starts with { and ends with }
    json_match = re.search(r"(\{[\s\S]*\})", cleaned)
    if json_match:
        candidate_json = json_match.group(1).strip()
        try:
            return json.loads(candidate_json)
        except json.JSONDecodeError:
            # Basic repair: trailing commas before closing braces
            repaired = re.sub(r",\s*([\]}])", r"\1", candidate_json)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Could not parse valid JSON from LLM output: {raw_text[:200]}...")
