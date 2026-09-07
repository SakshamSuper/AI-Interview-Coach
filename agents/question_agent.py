from typing import Dict, Any, List
from agents.state import InterviewState
from llm.model import llm_service
from rag.retriever import rag_retriever
from config.logger import logger


class QuestionAgent:
    """Agent responsible for dynamic, RAG-grounded, difficulty-adapted question generation."""

    def process(self, state: InterviewState) -> Dict[str, Any]:
        q_idx = state.get("current_question_index", 0) + 1
        total_q = state.get("total_questions", 5)
        curr_diff = state.get("current_difficulty", "Medium")
        target_role = state.get("target_role", "Software Engineer")
        cand_prof = state.get("candidate_profile", {})
        gaps = state.get("skill_gaps", [])
        prev_topics = state.get("previous_topics", [])

        logger.info(f"QuestionAgent: Generating question {q_idx}/{total_q} at {curr_diff} difficulty...")

        # Determine target topic to prioritize uncovered gaps
        target_topic = gaps[0] if gaps else "System Design"
        for gap in gaps:
            if gap not in prev_topics:
                target_topic = gap
                break

        # Query RAG knowledge base for grounding
        rag_res = rag_retriever.build_grounded_context(f"{target_role} {target_topic} architecture principles")
        rag_context = rag_res["context_text"]

        # Check if last evaluation missed critical concepts -> generate follow-up
        eval_hist = state.get("evaluation_history", [])
        ans_hist = state.get("answer_history", [])
        q_hist = state.get("question_history", [])

        if eval_hist and ans_hist and q_hist and eval_hist[-1].get("missing_concepts") and len(q_hist) > 0:
            last_eval = eval_hist[-1]
            # If accuracy is moderate (< 75) and missing concepts exist, generate targeted follow-up
            if last_eval.get("technical_accuracy", 100) < 75.0 and len(last_eval.get("missing_concepts", [])) > 0:
                logger.info("QuestionAgent: Generating adaptive follow-up targeting missing concepts...")
                question_obj = llm_service.generate_follow_up(
                    target_role=target_role,
                    previous_question=q_hist[-1].get("question", ""),
                    previous_answer=ans_hist[-1],
                    technical_accuracy=last_eval.get("technical_accuracy", 0),
                    missing_concepts=", ".join(last_eval.get("missing_concepts", [])),
                    weaknesses=", ".join(last_eval.get("weaknesses", [])),
                    current_topic=q_hist[-1].get("topic", target_topic),
                    current_difficulty=curr_diff,
                    rag_context=rag_context
                )
                q_dict = question_obj.model_dump()
                return {
                    "current_question": q_dict,
                    "previous_topics": list(set(prev_topics + [q_dict.get("topic", target_topic)]))
                }

        # Standard new adaptive question
        candidate_skills_str = ", ".join(cand_prof.get("skills", [])[:15]) or "General Programming"
        exp_list = cand_prof.get("experience", [])
        exp_summary = exp_list[0].get("title", "") if exp_list else "Software Developer"

        question_obj = llm_service.generate_question(
            target_role=target_role,
            candidate_name=cand_prof.get("name", "Candidate"),
            candidate_skills=candidate_skills_str,
            experience_summary=exp_summary,
            current_difficulty=curr_diff,
            skill_gaps=", ".join(gaps[:5]) if gaps else "General System Design",
            question_number=q_idx,
            total_questions=total_q,
            previous_topics=", ".join(prev_topics) if prev_topics else "None",
            rag_context=rag_context
        )

        q_dict = question_obj.model_dump()
        return {
            "current_question": q_dict,
            "previous_topics": list(set(prev_topics + [q_dict.get("topic", target_topic)]))
        }


question_agent = QuestionAgent()
