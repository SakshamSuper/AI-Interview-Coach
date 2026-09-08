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
        job_prof = state.get("job_profile", {})
        gaps = state.get("skill_gaps", [])
        prev_topics = state.get("previous_topics", [])
        q_hist = state.get("question_history", [])
        ans_hist = state.get("answer_history", [])
        eval_hist = state.get("evaluation_history", [])

        # Collect previous questions to prevent any duplicate questions
        previous_questions_list = [q.get("question") for q in q_hist if isinstance(q, dict) and q.get("question")]
        previous_questions_str = "\n".join(f"- {q}" for q in previous_questions_list) if previous_questions_list else "None"

        # Determine target topic: prioritize uncovered skill gaps -> uncovered JD required skills -> role archetype topics
        target_topic = None
        for gap in gaps:
            if gap not in prev_topics:
                target_topic = gap
                break

        if not target_topic:
            job_req_skills = job_prof.get("required_skills", [])
            for skill in job_req_skills:
                if skill not in prev_topics:
                    target_topic = skill
                    break

        if not target_topic:
            role_lower = target_role.lower()
            if any(k in role_lower for k in ["machine learning", "ml ", "ml/", "ai ", "deep learning", "nlp", "computer vision"]):
                role_topics = ["Deep Learning & Optimization", "Model Serving & Inference", "Generative AI & RAG", "ML Evaluation & Data Drift"]
            elif any(k in role_lower for k in ["data scientist", "data science", "analytics", "statistic"]):
                role_topics = ["Experimentation & A/B Testing", "Predictive Modeling & Feature Engineering", "Statistical Foundations & Distributions"]
            elif any(k in role_lower for k in ["data engineer", "big data", "etl", "data platform"]):
                role_topics = ["Distributed Data Processing", "Real-time Streaming & Ingestion", "Data Warehousing & Lakehouse Architecture"]
            elif any(k in role_lower for k in ["backend", "distributed", "platform", "cloud", "devops", "sre"]):
                role_topics = ["Distributed Systems & Consensus", "Concurrency & Transaction Management", "High Availability & Caching Architecture"]
            else:
                role_topics = ["Data Structures & Algorithms", "System Architecture & Scalability", "Concurrency & Thread Safety"]

            for rt in role_topics:
                if rt not in prev_topics:
                    target_topic = rt
                    break
            if not target_topic:
                target_topic = role_topics[0]

        logger.info(f"QuestionAgent: Generating question {q_idx}/{total_q} at {curr_diff} difficulty for topic '{target_topic}'...")

        # Query RAG knowledge base for grounding
        rag_res = rag_retriever.build_grounded_context(f"{target_role} {target_topic} architecture principles")
        rag_context = rag_res["context_text"]

        # Check if last evaluation missed critical concepts -> generate follow-up
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
                    previous_questions=previous_questions_str,
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
        
        # Extract candidate projects
        proj_list = cand_prof.get("projects", [])
        proj_titles = [p.get("title") for p in proj_list if isinstance(p, dict) and p.get("title")]
        candidate_projects_str = ", ".join(proj_titles[:3]) if proj_titles else "None"

        # Extract job required skills
        job_req_skills = job_prof.get("required_skills", [])
        job_skills_str = ", ".join(job_req_skills[:10]) if job_req_skills else "General Engineering"

        question_obj = llm_service.generate_question(
            target_role=target_role,
            candidate_name=cand_prof.get("name", "Candidate"),
            candidate_skills=candidate_skills_str,
            candidate_projects=candidate_projects_str,
            experience_summary=exp_summary,
            current_difficulty=curr_diff,
            target_topic=target_topic,
            skill_gaps=", ".join(gaps[:5]) if gaps else "General Architecture",
            job_required_skills=job_skills_str,
            question_number=q_idx,
            total_questions=total_q,
            previous_topics=", ".join(prev_topics) if prev_topics else "None",
            previous_questions=previous_questions_str,
            rag_context=rag_context
        )

        q_dict = question_obj.model_dump()
        return {
            "current_question": q_dict,
            "previous_topics": list(set(prev_topics + [q_dict.get("topic", target_topic)]))
        }


question_agent = QuestionAgent()
