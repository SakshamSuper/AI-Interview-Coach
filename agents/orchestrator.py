from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from agents.state import InterviewState
from agents.resume_agent import resume_agent
from agents.question_agent import question_agent
from agents.evaluation_agent import evaluation_agent
from agents.recommendation_agent import recommendation_agent
from config.logger import logger


def resume_node(state: InterviewState) -> InterviewState:
    res = resume_agent.process(state)
    return {**state, **res}


def question_node(state: InterviewState) -> InterviewState:
    res = question_agent.process(state)
    return {**state, **res}


def evaluation_node(state: InterviewState) -> InterviewState:
    res = evaluation_agent.process(state)
    return {**state, **res}


def difficulty_node(state: InterviewState) -> InterviewState:
    # Explicit adaptive difficulty engine node
    eval_hist = state.get("evaluation_history", [])
    if eval_hist:
        last_score = eval_hist[-1].get("overall_score", 70.0)
        curr_diff = state.get("current_difficulty", "Medium")

        # Two consecutive strong answers -> upgrade difficulty
        if len(eval_hist) >= 2 and eval_hist[-1].get("overall_score", 0) >= 80 and eval_hist[-2].get("overall_score", 0) >= 80:
            next_diff = "Hard"
        elif last_score >= 80:
            next_diff = "Hard" if curr_diff == "Medium" else curr_diff
        elif last_score <= 50:
            next_diff = "Easy" if curr_diff == "Medium" else curr_diff
        else:
            next_diff = "Medium"

        logger.info(f"DifficultyEngine: Score {last_score} -> Set next difficulty: {next_diff}")
        return {**state, "current_difficulty": next_diff}

    return state


def recommendation_node(state: InterviewState) -> InterviewState:
    res = recommendation_agent.process(state)
    return {**state, **res}


def should_continue(state: InterviewState) -> Literal["difficulty_node", "recommendation_node"]:
    curr_idx = state.get("current_question_index", 0)
    total_q = state.get("total_questions", 5)

    if curr_idx < total_q:
        logger.info(f"Routing conditional edge: {curr_idx}/{total_q} questions evaluated -> difficulty_node.")
        return "difficulty_node"
    else:
        logger.info(f"Routing conditional edge: All {total_q} questions completed -> recommendation_node.")
        return "recommendation_node"


def build_interview_graph():
    """Builds and compiles the full LangGraph multi-agent interview graph."""
    workflow = StateGraph(InterviewState)

    workflow.add_node("resume_node", resume_node)
    workflow.add_node("question_node", question_node)
    workflow.add_node("evaluation_node", evaluation_node)
    workflow.add_node("difficulty_node", difficulty_node)
    workflow.add_node("recommendation_node", recommendation_node)

    # Initial flow
    workflow.set_entry_point("resume_node")
    workflow.add_edge("resume_node", "question_node")

    # Evaluation branch
    workflow.add_conditional_edges(
        "evaluation_node",
        should_continue,
        {
            "difficulty_node": "difficulty_node",
            "recommendation_node": "recommendation_node"
        }
    )

    workflow.add_edge("difficulty_node", "question_node")
    workflow.add_edge("recommendation_node", END)

    return workflow.compile()


interview_graph = build_interview_graph()
