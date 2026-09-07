from typing import Dict, Any
from agents.state import InterviewState
from llm.model import llm_service
from rag.retriever import rag_retriever
from config.logger import logger


class EvaluationAgent:
    """Agent responsible for structured multi-dimensional evaluation of candidate answers."""

    def process(self, state: InterviewState) -> Dict[str, Any]:
        curr_q = state.get("current_question", {})
        cand_ans = state.get("current_answer", "")
        curr_diff = state.get("current_difficulty", "Medium")

        logger.info(f"EvaluationAgent: Evaluating answer for topic '{curr_q.get('topic')}'...")

        # Retrieve RAG context for question grounding
        rag_res = rag_retriever.build_grounded_context(
            f"{curr_q.get('topic', '')} {curr_q.get('question', '')}"
        )
        rag_context = rag_res["context_text"]

        eval_res = llm_service.evaluate_answer(
            question_text=curr_q.get("question", ""),
            topic=curr_q.get("topic", "Technical"),
            difficulty=curr_q.get("difficulty", curr_diff),
            expected_concepts=", ".join(curr_q.get("expected_concepts", [])),
            rag_context=rag_context,
            candidate_answer=cand_ans
        )

        eval_dict = eval_res.model_dump()

        # Update histories
        q_hist = list(state.get("question_history", []))
        if curr_q:
            q_hist.append(curr_q)

        ans_hist = list(state.get("answer_history", []))
        ans_hist.append(cand_ans)

        eval_hist = list(state.get("evaluation_history", []))
        eval_hist.append(eval_dict)

        q_idx = state.get("current_question_index", 0) + 1

        return {
            "current_evaluation": eval_dict,
            "question_history": q_hist,
            "answer_history": ans_hist,
            "evaluation_history": eval_hist,
            "current_question_index": q_idx,
            "current_difficulty": eval_dict.get("next_difficulty", curr_diff)
        }


evaluation_agent = EvaluationAgent()
