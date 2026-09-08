from typing import Dict, Any, List
from langchain_core.tools import tool
from rag.retriever import rag_retriever
from nlp.similarity import calculate_semantic_similarity
from nlp.skill_extractor import skill_extractor


@tool
def knowledge_search_tool(query: str) -> str:
    """Searches the technical interview knowledge base for grounded domain principles."""
    res = rag_retriever.build_grounded_context(query, top_k=2)
    return res["context_text"]


@tool
def skill_match_tool(candidate_skills_csv: str, required_skill: str) -> str:
    """Evaluates how well a candidate's skills align with a target skill."""
    cand_list = [s.strip() for s in candidate_skills_csv.split(",") if s.strip()]
    best_sim = 0.0
    best_match = "None"
    for s in cand_list:
        sim = calculate_semantic_similarity(s, required_skill)
        if sim > best_sim:
            best_sim = sim
            best_match = s

    return f"Best alignment for '{required_skill}': '{best_match}' with {best_sim*100:.1f}% semantic similarity."


@tool
def extract_skills_tool(text: str) -> str:
    """Extracts technical skills and categorizes them from given text."""
    skills = skill_extractor.extract_skills(text)
    return f"Extracted {len(skills['all_skills'])} skills: {', '.join(skills['all_skills'])}"
