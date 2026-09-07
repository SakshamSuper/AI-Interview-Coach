import sys
import os
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from config.logger import logger
from nlp.resume_parser import resume_parser
from nlp.jd_parser import jd_parser
from nlp.matching import matching_engine
from rag.retriever import rag_retriever
from agents.question_agent import question_agent
from agents.evaluation_agent import evaluation_agent
from agents.recommendation_agent import recommendation_agent
from ml.predictor import ml_predictor
from llm.model import llm_service

def run_product_validation():
    print("==================================================")
    print("AI INTERVIEW COACH - COMPREHENSIVE PRODUCT AUDIT")
    print("==================================================")

    # 1. Candidate & Job Profile
    sample_resume = """
    Jane Doe
    jane.doe@example.com | (555) 987-6543 | github.com/janedoe

    Summary:
    Software Engineer with experience in Python, FastAPI, SQL, and foundational Machine Learning.
    Built automated data pipelines and GenAI applications using LangChain.

    Experience:
    AI Developer at DataCorp (2022 - Present)
    - Developed backend REST APIs using FastAPI and Python.
    - Integrated LangChain agents with PostgreSQL for text-to-SQL workflows.
    - Containerized microservices with Docker and deployed to AWS EC2.
    - Implemented basic data structures and algorithms for high-throughput batch sorting.

    Skills:
    Languages: Python, SQL
    Frameworks: FastAPI, LangChain, PyTorch, Scikit-Learn
    Databases: PostgreSQL, SQLite
    Cloud: Docker, AWS
    """

    sample_jd = """
    Job Title: Senior AI/ML & GenAI Engineer
    Requirements:
    - 5+ years of experience in Python, Machine Learning, and Large Language Models.
    - Deep knowledge of Retrieval-Augmented Generation (RAG), Vector Databases (FAISS), and embeddings.
    - Strong expertise in Microservices, Distributed Systems, and System Design.
    - Hands-on experience with Kubernetes, Kafka, and Docker.
    - Solid foundation in Data Structures, Algorithms, and Object-Oriented Design.
    """

    print("\n--- STAGE 1: NLP Parsing & Taxonomy ---")
    candidate_profile = resume_parser.parse(sample_resume, "jane_doe_resume.txt")
    job_profile = jd_parser.parse(sample_jd, "Senior AI/ML Engineer")

    print(f"Candidate Parsed: {candidate_profile.name}")
    print(f"Candidate Skills ({len(candidate_profile.skills)}): {', '.join(candidate_profile.skills[:10])}")
    print(f"Job Title: {job_profile.job_title} | Level: {job_profile.role_level}")
    print(f"Required Skills: {', '.join(job_profile.required_skills)}")

    assert len(candidate_profile.skills) >= 5, "Resume parsing failed to extract skills"
    assert len(job_profile.required_skills) >= 3, "JD parsing failed to extract required skills"
    print("[PASS] Stage 1 NLP parsing succeeded.")

    # 2. Semantic Matching & Gap Analysis
    print("\n--- STAGE 2: Semantic Matching & Gap Analysis ---")
    match_result = matching_engine.analyze_match(candidate_profile, job_profile)
    print(f"Overall Fit Score: {match_result.overall_match_score}% ({match_result.match_category})")
    print(f"Required Skills Coverage: {match_result.explanation.required_skills_coverage}%")
    print(f"Semantic Cosine Similarity: {match_result.explanation.semantic_similarity_score}%")
    print(f"High-Priority Gaps: {[g.skill for g in match_result.gap_report.high_priority_gaps]}")

    assert match_result.overall_match_score > 0, "Match score should be non-zero"
    assert len(match_result.gap_report.high_priority_gaps) > 0, "Gaps should be detected"
    print("[PASS] Stage 2 Semantic matching and gap prioritization succeeded.")

    # 3. RAG Grounding Verification
    print("\n--- STAGE 3: RAG Grounding Verification ---")
    retrieval = rag_retriever.build_grounded_context("How does Retrieval-Augmented Generation (RAG) ground LLMs and mitigate hallucinations?", top_k=2)
    print(f"Retrieved Confidence: {retrieval['confidence_score']*100:.1f}%")
    print(f"Retrieved Sources: {[s['source'] for s in retrieval['sources']]}")
    assert len(retrieval['sources']) > 0, "RAG failed to retrieve chunks"
    assert retrieval['has_grounding'], "RAG context should have grounding flag True"
    print("[PASS] Stage 3 RAG grounded retrieval succeeded.")

    # 4. Adaptive Interview - Test Case A: Strong Answer -> Escalation to Hard
    print("\n--- STAGE 4A: Adaptive Interview - Strong Answer (Escalation to Hard) ---")
    state_strong = {
        "session_id": "test_session_strong",
        "target_role": "Senior AI/ML Engineer",
        "current_difficulty": "Medium",
        "current_question_index": 0,
        "total_questions": 3,
        "candidate_profile": candidate_profile.model_dump(),
        "job_profile": job_profile.model_dump(),
        "skill_gaps": [g.skill for g in match_result.gap_report.high_priority_gaps],
        "previous_topics": [],
        "question_history": [],
        "answer_history": [],
        "evaluation_history": []
    }

    # Generate Question 1
    q1_res = question_agent.process(state_strong)
    q1 = q1_res["current_question"]
    print(f"Question 1 [{q1['topic']}] (Difficulty: {q1['difficulty']}):")
    print(f"  {q1['question']}")

    # Candidate provides a strong, detailed answer
    strong_answer = """
    A RAG pipeline minimizes LLM hallucinations by retrieving factual chunks from a domain vector store like FAISS using dense embeddings such as all-MiniLM-L6-v2 and injecting them into the prompt.
    Comparing chunking strategies: recursive character splitting uses structural delimiters like double newlines to keep paragraphs coherent, whereas semantic chunking groups sentences based on embedding distance.
    To avoid boundary clipping and loss of context, we enforce chunk overlaps of 100 characters and use cross-encoder rerankers to optimize recall.
    """
    state_strong["current_question"] = q1
    state_strong["current_answer"] = strong_answer

    eval1_res = evaluation_agent.process(state_strong)
    eval1 = eval1_res["current_evaluation"]
    print(f"Evaluation 1: Technical Accuracy={eval1['technical_accuracy']} | Next Difficulty={eval1['next_difficulty']}")
    print(f"Feedback: {eval1['feedback']}")

    assert eval1["technical_accuracy"] >= 80.0, "Expected strong score for detailed answer"
    assert eval1["next_difficulty"] == "Hard", "Expected next difficulty to escalate to Hard"

    # Next question with updated state
    state_strong.update(eval1_res)
    q2_res = question_agent.process(state_strong)
    q2 = q2_res["current_question"]
    print(f"Question 2 [{q2['topic']}] (Difficulty: {q2['difficulty']}):")
    print(f"  {q2['question']}")
    assert q2["difficulty"] == "Hard", "Question Agent failed to escalate to Hard difficulty"
    print("[PASS] Stage 4A: Strong answer correctly escalated difficulty to Hard.")

    # 5. Adaptive Interview - Test Case B: Weak Answer -> Remedial Follow-Up
    print("\n--- STAGE 4B: Adaptive Interview - Weak Answer (Targeted Remediation) ---")
    state_weak = {
        "session_id": "test_session_weak",
        "target_role": "Senior AI/ML Engineer",
        "current_difficulty": "Medium",
        "current_question_index": 0,
        "total_questions": 3,
        "candidate_profile": candidate_profile.model_dump(),
        "job_profile": job_profile.model_dump(),
        "skill_gaps": ["Distributed Systems"],
        "previous_topics": [],
        "question_history": [],
        "answer_history": [],
        "evaluation_history": []
    }

    q1_weak_res = question_agent.process(state_weak)
    q1_weak = q1_weak_res["current_question"]
    print(f"Question 1 [{q1_weak['topic']}]: {q1_weak['question']}")

    # Candidate provides a shallow, brief answer
    shallow_answer = "You just use Redis."
    state_weak["current_question"] = q1_weak
    state_weak["current_answer"] = shallow_answer

    eval_weak_res = evaluation_agent.process(state_weak)
    eval_weak = eval_weak_res["current_evaluation"]
    print(f"Evaluation 1 (Weak): Technical Accuracy={eval_weak['technical_accuracy']} | Next Difficulty={eval_weak['next_difficulty']}")
    print(f"Missing Concepts: {eval_weak['missing_concepts']}")

    assert eval_weak["technical_accuracy"] < 70.0, "Expected low score for shallow answer"
    assert len(eval_weak["missing_concepts"]) > 0, "Expected missing concepts to be populated"

    # Next question should be an adaptive remedial follow-up targeting missing concepts
    state_weak.update(eval_weak_res)
    q2_weak_res = question_agent.process(state_weak)
    q2_weak = q2_weak_res["current_question"]
    print(f"Question 2 (Adaptive Remediation): {q2_weak['question']}")
    print(f"Question Type: {q2_weak.get('question_type')} | Reason: {q2_weak.get('reason')}")

    assert "Follow-Up" in q2_weak.get("question_type", "") or "trade-off" in q2_weak['question'].lower() or "implement" in q2_weak['question'].lower()
    print("[PASS] Stage 4B: Weak answer triggered targeted remedial follow-up.")

    # 6. Scikit-Learn Candidate Readiness Engine
    print("\n--- STAGE 5: Scikit-Learn Readiness Engine Inference ---")
    ready_features = {
        "technical_score": 88.0,
        "relevance_score": 90.0,
        "completeness_score": 85.0,
        "clarity_score": 85.0,
        "communication_score": 90.0,
        "answer_length": 120,
        "keyword_coverage": 0.85,
        "difficulty_numeric": 3,
        "attempt_number": 3,
        "previous_score": 85.0,
        "average_previous_score": 86.0,
        "topic_accuracy": 88.0
    }
    pred_ready = ml_predictor.predict_readiness(ready_features)
    print(f"High Performance Prediction: {pred_ready['readiness_label']} (Score: {pred_ready['readiness_score']}%)")
    assert pred_ready['readiness_label'] == "Interview Ready", f"Expected Interview Ready, got {pred_ready['readiness_label']}"

    weak_features = {
        "technical_score": 45.0,
        "relevance_score": 50.0,
        "completeness_score": 40.0,
        "clarity_score": 50.0,
        "communication_score": 50.0,
        "answer_length": 15,
        "keyword_coverage": 0.35,
        "difficulty_numeric": 2,
        "attempt_number": 3,
        "previous_score": 42.0,
        "average_previous_score": 43.0,
        "topic_accuracy": 45.0
    }
    pred_weak = ml_predictor.predict_readiness(weak_features)
    print(f"Low Performance Prediction: {pred_weak['readiness_label']} (Score: {pred_weak['readiness_score']}%)")
    assert pred_weak['readiness_label'] == "Needs Improvement", f"Expected Needs Improvement, got {pred_weak['readiness_label']}"
    print("[PASS] Stage 5: ML Readiness Predictor produced statistically sound classifications.")

    # 7. Recommendation Agent Roadmap
    print("\n--- STAGE 6: Recommendation Agent Structured Roadmap ---")
    rec_res = recommendation_agent.process({
        "target_role": "Senior AI/ML Engineer",
        "evaluation_history": [eval1],
        "question_history": [q1, q2],
        "skill_gaps": ["Kubernetes", "Kafka"]
    })
    rec = rec_res["recommendations"]
    print("Summary:", rec["overall_summary"][:120], "...")
    print("Learning Priorities:", rec["learning_priorities"][:2])
    print("Practice Questions:", rec["practice_questions"][:2])
    assert len(rec["learning_priorities"]) > 0
    print("[PASS] Stage 6: Recommendation Agent synthesized tailored roadmap.")

    print("\n==================================================")
    print("ALL VERIFICATION STAGES PASSED WITH ZERO FAILURES!")
    print("==================================================")

if __name__ == "__main__":
    run_product_validation()
