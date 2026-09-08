from typing import Dict, Any
from agents.state import InterviewState
from config.logger import logger


class ResumeAgent:
    """Agent responsible for candidate background analysis and gap contextualization."""

    def process(self, state: InterviewState) -> Dict[str, Any]:
        logger.info("ResumeAgent: Processing candidate profile and job requirements...")

        cand_profile = state.get("candidate_profile", {})
        job_profile = state.get("job_profile", {})

        cand_skills = set(cand_profile.get("skills", []))
        req_skills = job_profile.get("required_skills", [])

        # Find gaps
        gaps = [s for s in req_skills if s not in cand_skills]
        if not gaps:
            gaps = job_profile.get("preferred_skills", ["System Design", "Microservices"])

        return {
            "skill_gaps": gaps,
            "target_role": state.get("target_role") or job_profile.get("job_title", "Software Engineer")
        }


resume_agent = ResumeAgent()
