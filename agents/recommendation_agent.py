from typing import Dict, Any
from agents.state import InterviewState
from llm.model import llm_service
from config.logger import logger


class RecommendationAgent:
    """Agent responsible for post-interview performance synthesis and study roadmaps."""

    def process(self, state: InterviewState) -> Dict[str, Any]:
        logger.info("RecommendationAgent: Generating final interview recommendations and roadmap...")

        target_role = state.get("target_role", "Software Engineer")
        eval_hist = state.get("evaluation_history", [])
        q_hist = state.get("question_history", [])
        gaps = state.get("skill_gaps", [])

        # Calculate average overall score
        total_score = sum(e.get("overall_score", 0) for e in eval_hist)
        avg_score = (total_score / len(eval_hist)) if eval_hist else 75.0

        # Build summary of evaluations
        eval_lines = []
        for idx, (q, ev) in enumerate(zip(q_hist, eval_hist), start=1):
            eval_lines.append(
                f"Q{idx} ({q.get('topic', 'Topic')} - {q.get('difficulty', 'Medium')}): "
                f"Score {ev.get('overall_score', 0)}/100. "
                f"Strengths: {', '.join(ev.get('strengths', []))}. "
                f"Weaknesses: {', '.join(ev.get('weaknesses', []))}."
            )

        summary_text = "\n".join(eval_lines) or "Standard technical session completed."

        rec_obj = llm_service.generate_recommendations(
            target_role=target_role,
            total_questions=len(eval_hist),
            average_score=round(avg_score, 1),
            evaluations_summary=summary_text,
            skill_gaps=", ".join(gaps) if gaps else "None"
        )

        rec_dict = rec_obj.model_dump()

        return {
            "recommendations": rec_dict,
            "status": "completed"
        }


recommendation_agent = RecommendationAgent()
