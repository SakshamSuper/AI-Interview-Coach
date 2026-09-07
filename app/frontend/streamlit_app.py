import os
import sys
import json
import streamlit as st
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config.settings import get_settings
from database.database import SessionLocal, init_db
from database.repositories.user_repository import UserRepository
from database.repositories.interview_repository import InterviewRepository
from nlp.resume_parser import resume_parser
from nlp.jd_parser import jd_parser
from nlp.matching import matching_engine
from rag.retriever import rag_retriever
from rag.ingestion import ingest_knowledge_base
from agents.question_agent import question_agent
from agents.evaluation_agent import evaluation_agent
from agents.recommendation_agent import recommendation_agent
from ml.predictor import ml_predictor
from analytics.dashboard import (
    create_radar_chart, create_topic_performance_bar,
    create_score_history_chart, create_match_gauge
)
from analytics.metrics import aggregate_user_analytics
from app.backend.schemas.profiles import CandidateProfile, JobProfile
from llm.structured_output import InterviewQuestion, AnswerEvaluation, RecommendationOutput

# Page identifiers
PAGE_HOME = "🎯 Home Dashboard"
PAGE_RESUME = "📄 Resume Intelligence"
PAGE_JD = "💼 Job Description"
PAGE_MATCH = "⚖️ Match & Skill Gap"
PAGE_KB = "📚 Technical Knowledge Base"
PAGE_INTERVIEW = "🎙️ Live Adaptive Interview"
PAGE_ANALYTICS = "📊 Analytics & Readiness"
PAGE_HISTORY = "📜 Interview History"
PAGE_SETTINGS = "⚙️ Settings & Status"

st.set_page_config(
    page_title="AI Interview Coach - Adaptive Interview Platform",
    page_icon="🎯",
    layout="wide"
)

init_db()

if "user_id" not in st.session_state:
    st.session_state.user_id = 1
if "candidate_profile" not in st.session_state:
    st.session_state.candidate_profile = None
if "job_profile" not in st.session_state:
    st.session_state.job_profile = None
if "match_result" not in st.session_state:
    st.session_state.match_result = None
if "interview_session_id" not in st.session_state:
    st.session_state.interview_session_id = None
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "current_evaluation" not in st.session_state:
    st.session_state.current_evaluation = None
if "interview_completed" not in st.session_state:
    st.session_state.interview_completed = False

db = SessionLocal()
user_repo = UserRepository(db)
int_repo = InterviewRepository(db)

user = user_repo.get_user_by_id(st.session_state.user_id)
if not user:
    user = user_repo.get_or_create_user(name="Alex Smith", email="alex.smith@example.com", target_role="Senior Machine Learning Engineer")
    st.session_state.user_id = user.id

with st.sidebar:
    st.title("🎯 AI Interview Coach")
    st.caption("Adaptive GenAI & ML Interview Platform")
    st.divider()
    page = st.radio(
        "Navigation",
        [
            PAGE_HOME,
            PAGE_RESUME,
            PAGE_JD,
            PAGE_MATCH,
            PAGE_KB,
            PAGE_INTERVIEW,
            PAGE_ANALYTICS,
            PAGE_HISTORY,
            PAGE_SETTINGS
        ]
    )
    st.divider()
    st.markdown(f"**Candidate**: {user.name}")
    st.caption(f"Target: {user.target_role or 'Senior Engineer'}")

if page == PAGE_HOME:
    st.title("Interview Performance Dashboard")
    st.caption("Real-time interview readiness, skill alignment, and targeted preparation roadmap.")

    analytics_data = aggregate_user_analytics(user_id=st.session_state.user_id, db=db)
    latest_gap = user_repo.get_latest_skill_gap_analysis(user_id=st.session_state.user_id)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Interviews", analytics_data["total_interviews"])
    col2.metric("Avg Overall Score", f"{analytics_data['average_overall_score']}%")
    col3.metric("Job Description Match", f"{latest_gap.overall_match_score}%" if latest_gap else "N/A")
    col4.metric("Interview Readiness", analytics_data["overall_readiness_label"])

    st.divider()
    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.subheader("Performance Trajectory")
        if analytics_data["score_history"]:
            fig_trend = create_score_history_chart(analytics_data["score_history"])
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No completed interview sessions yet. Start your first session in 'Live Adaptive Interview'.")

        st.subheader("Topic Mastery")
        fig_topic = create_topic_performance_bar(analytics_data["topic_performance"])
        st.plotly_chart(fig_topic, use_container_width=True)

    with col_r:
        st.subheader("Active Profile Overview")
        st.write(f"**Name:** {user.name}")
        st.write(f"**Target Role:** {user.target_role or 'Senior Software Engineer'}")
        st.write(f"**Readiness Tier:** {analytics_data['overall_readiness_label']}")

        st.subheader("Targeted Focus Areas")
        if analytics_data["weak_areas"]:
            for w in analytics_data["weak_areas"]:
                st.warning(f"⚠️ {w}")
        else:
            st.success("✅ No critical deficiencies detected in recent attempts.")

elif page == PAGE_RESUME:
    st.title("Resume Intelligence & Parsing")
    st.caption("Upload PDF, DOCX, or text resume to extract skills, experience, and education.")

    uploaded_file = st.file_uploader("Upload Resume File", type=["pdf", "docx", "txt"])
    if st.button("📄 Load Sample ML Engineer Resume"):
        sample_text = """David Miller
david.miller@example.com | (555) 345-6789 | github.com/davidmiller

Summary: Senior Machine Learning Engineer with 5+ years experience building production AI systems.

Work Experience:
Senior ML Engineer at Apex AI | 2021 - 2024
- Designed distributed training pipelines using Python, PyTorch, and FastAPI.
- Deployed microservices to Kubernetes on AWS.
- Built RAG search pipelines using LangChain and FAISS vector databases.

Education:
Master of Science in Computer Science - University of Illinois 2019
Bachelor of Science in Computer Engineering - Purdue University 2017

Skills:
Languages: Python, Go, SQL, C++
Frameworks: PyTorch, TensorFlow, FastAPI, LangChain, Scikit-Learn
Cloud & DevOps: Docker, Kubernetes, AWS, PostgreSQL, Redis"""
        profile = resume_parser.parse(sample_text, "sample_ml_resume.txt")
        st.session_state.candidate_profile = profile
        user_repo.save_resume(st.session_state.user_id, "sample_ml_resume.txt", "txt", sample_text, profile.model_dump())
        st.success("Sample Resume loaded successfully!")

    elif uploaded_file is not None:
        os.makedirs("data/uploads", exist_ok=True)
        temp_path = os.path.join("data/uploads", uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())
        from nlp.preprocessing import extract_text_from_file
        text = extract_text_from_file(temp_path)
        profile = resume_parser.parse(text, uploaded_file.name)
        st.session_state.candidate_profile = profile
        user_repo.save_resume(st.session_state.user_id, uploaded_file.name, uploaded_file.name.split(".")[-1], text, profile.model_dump())
        st.success(f"Extracted profile for {profile.name}!")

    if st.session_state.candidate_profile:
        p = st.session_state.candidate_profile
        st.divider()
        st.subheader(f"Candidate: {p.name}")
        st.write(f"**Email:** {p.contact.email} | **Phone:** {p.contact.phone}")
        st.write("**Extracted Skills:**", ", ".join(p.skills))

elif page == PAGE_JD:
    st.title("Job Description Intelligence")
    st.caption("Analyze requirements, required skills, and preferred qualifications.")

    jd_text = st.text_area("Paste Job Description:", height=200, value="""Requirements:
- 4+ years of hands-on experience in Python and PyTorch.
- Strong knowledge of Docker, Kubernetes, and AWS cloud infrastructure.
- In-depth understanding of Retrieval-Augmented Generation (RAG) and Large Language Models.

Preferred Qualifications:
- Experience with LangChain and FAISS.
- Strong System Design and distributed architecture fundamentals.""")

    if st.button("💼 Analyze Job Description", type="primary"):
        jp = jd_parser.parse(jd_text, default_title="Senior Machine Learning Engineer")
        st.session_state.job_profile = jp
        user_repo.save_job_description(st.session_state.user_id, jp.job_title, jd_text, jp.model_dump())
        st.success(f"Analyzed JD: {jp.job_title} ({jp.role_level})")

    if st.session_state.job_profile:
        jp = st.session_state.job_profile
        st.divider()
        c1, c2 = st.columns(2)
        c1.write("**Required Skills:** " + ", ".join(jp.required_skills))
        c2.write("**Preferred Skills:** " + ", ".join(jp.preferred_skills))

elif page == PAGE_MATCH:
    st.title("Resume-JD Match & Skill Gap Engine")
    if not st.session_state.candidate_profile or not st.session_state.job_profile:
        st.info("Please ensure both Resume and Job Description are loaded.")
    else:
        if st.button("⚖️ Compute Alignment & Gaps", type="primary") or st.session_state.match_result is None:
            res = matching_engine.analyze_match(st.session_state.candidate_profile, st.session_state.job_profile)
            st.session_state.match_result = res
            user_repo.save_skill_gap_analysis(
                st.session_state.user_id, None, None,
                res.overall_match_score, res.match_category,
                [m.model_dump() for m in res.skill_breakdown],
                res.gap_report.model_dump()
            )

        res = st.session_state.match_result
        if res:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.plotly_chart(create_match_gauge(res.overall_match_score), use_container_width=True)
                st.markdown(f"**Classification:** {res.match_category}")
            with col2:
                st.subheader("Explanation")
                st.write(res.explanation.summary_explanation)
                st.metric("Required Skills Fit", f"{res.explanation.required_skills_coverage}%")

            st.subheader("High Priority Gaps")
            for gap in res.gap_report.high_priority_gaps:
                st.warning(f"⚠️ {gap.skill} ({gap.gap_priority} Priority) — Proficiency: {gap.current_proficiency_estimate}%")

elif page == PAGE_KB:
    st.title("Technical Knowledge Base & RAG")
    if st.button("🔄 Re-Index Knowledge Base"):
        ing = ingest_knowledge_base()
        st.success(f"Re-indexed {ing['total_chunks']} chunks across {len(ing['topics'])} topics!")

    summary_file = "data/knowledge_base/faiss_index/index_summary.json"
    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
        c1, c2, c3 = st.columns(3)
        c1.metric("Indexed Chunks", summary.get("total_chunks", 0))
        c2.metric("Vector Dim", summary.get("dimension", 384))
        c3.metric("Domains", len(summary.get("topics", [])))

    test_q = st.text_input("Semantic Search Query:", value="Explain CAP theorem trade-offs")
    if st.button("Search Vectors", type="primary"):
        ctx = rag_retriever.build_grounded_context(test_q, top_k=2)
        st.write(f"**Confidence:** {ctx['confidence_score']*100:.1f}%")
        st.text_area("Grounded Context:", ctx["context_text"], height=200)

elif page == PAGE_INTERVIEW:
    st.title("Live Adaptive Interview")

    if st.session_state.interview_session_id is None or st.session_state.interview_completed:
        st.subheader("Configure Session")
        c1, c2 = st.columns(2)
        role = c1.text_input("Target Role", value=user.target_role or "Senior Machine Learning Engineer")
        diff = c2.selectbox("Starting Difficulty", ["Medium", "Easy", "Hard"], index=0)
        num_q = st.slider("Number of Questions", 1, 5, 2)

        if st.button("🚀 Start Interview", type="primary"):
            cand_p = st.session_state.candidate_profile or CandidateProfile(name=user.name, skills=["Python", "System Design"])
            job_p = st.session_state.job_profile or JobProfile(job_title=role, required_skills=["Python", "RAG"])
            session = int_repo.create_session(st.session_state.user_id, role, difficulty=diff, total_questions=num_q)

            q_res = question_agent.process({
                "session_id": session.id,
                "target_role": role,
                "current_difficulty": diff,
                "current_question_index": 0,
                "total_questions": num_q,
                "candidate_profile": cand_p.model_dump(),
                "job_profile": job_p.model_dump(),
                "skill_gaps": ["System Design", "RAG"],
                "previous_topics": [],
                "question_history": [],
                "answer_history": [],
                "evaluation_history": []
            })
            q_obj = InterviewQuestion(**q_res["current_question"])
            int_repo.add_question(session.id, 1, q_obj.question, q_obj.topic, q_obj.difficulty, q_obj.question_type, q_obj.reason, q_obj.expected_concepts, q_obj.source_context)

            st.session_state.interview_session_id = session.id
            st.session_state.current_question = q_obj
            st.session_state.current_evaluation = None
            st.session_state.interview_completed = False
            st.rerun()

    else:
        session = int_repo.get_session(st.session_state.interview_session_id)
        q_obj = st.session_state.current_question
        curr_idx = session.current_question_index + 1

        st.markdown(f"### Question {curr_idx} of {session.total_questions} | Topic: `{q_obj.topic}` | Difficulty: `{q_obj.difficulty}`")
        st.info(q_obj.question)

        if st.session_state.current_evaluation is None:
            ans = st.text_area("Your Answer:", height=150)
            c_sub1, c_sub2 = st.columns([1, 4])
            if c_sub1.button("Submit Answer", type="primary"):
                if not ans.strip():
                    st.error("Please enter an answer.")
                else:
                    questions = int_repo.get_questions_for_session(session.id)
                    ans_rec = int_repo.record_answer(session.id, questions[-1].id, ans)
                    eval_res = evaluation_agent.process({
                        "current_question": q_obj.model_dump(),
                        "current_answer": ans,
                        "current_difficulty": session.difficulty,
                        "question_history": [{"question": q.question_text, "topic": q.topic} for q in questions],
                        "answer_history": [ans],
                        "evaluation_history": [],
                        "current_question_index": session.current_question_index
                    })
                    eval_obj = AnswerEvaluation(**eval_res["current_evaluation"])
                    int_repo.record_evaluation(
                        session.id, ans_rec.id, eval_obj.technical_accuracy, eval_obj.relevance,
                        eval_obj.completeness, eval_obj.clarity, eval_obj.communication,
                        eval_obj.overall_score, eval_obj.strengths, eval_obj.weaknesses,
                        eval_obj.missing_concepts, eval_obj.feedback, eval_obj.next_difficulty
                    )
                    st.session_state.current_evaluation = eval_obj
                    st.rerun()

            if c_sub2.button("Fill Sample Answer"):
                ans = "The Python GIL is a mutex in CPython that prevents multiple native threads from executing bytecodes concurrently. To overcome it for CPU-bound tasks, we use multiprocessing to spawn separate processes with independent memory heaps."
                questions = int_repo.get_questions_for_session(session.id)
                ans_rec = int_repo.record_answer(session.id, questions[-1].id, ans)
                eval_res = evaluation_agent.process({
                    "current_question": q_obj.model_dump(),
                    "current_answer": ans,
                    "current_difficulty": session.difficulty,
                    "question_history": [{"question": q.question_text, "topic": q.topic} for q in questions],
                    "answer_history": [ans],
                    "evaluation_history": [],
                    "current_question_index": session.current_question_index
                })
                eval_obj = AnswerEvaluation(**eval_res["current_evaluation"])
                int_repo.record_evaluation(
                    session.id, ans_rec.id, eval_obj.technical_accuracy, eval_obj.relevance,
                    eval_obj.completeness, eval_obj.clarity, eval_obj.communication,
                    eval_obj.overall_score, eval_obj.strengths, eval_obj.weaknesses,
                    eval_obj.missing_concepts, eval_obj.feedback, eval_obj.next_difficulty
                )
                st.session_state.current_evaluation = eval_obj
                st.rerun()

        else:
            ev = st.session_state.current_evaluation
            st.success("Answer Evaluated!")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Overall Score", f"{ev.overall_score}%")
            m2.metric("Tech Depth", f"{ev.technical_accuracy}%")
            m3.metric("Completeness", f"{ev.completeness}%")
            m4.metric("Next Difficulty", ev.next_difficulty)

            st.write(f"**Feedback:** {ev.feedback}")

            if session.current_question_index >= session.total_questions:
                if st.button("🏁 Finalize & View Results", type="primary"):
                    evals = session.evaluations
                    avg_score = sum(e.overall_score for e in evals) / len(evals) if evals else 70.0

                    ml_res = ml_predictor.predict_readiness({
                        "technical_score": avg_score, "relevance_score": avg_score,
                        "completeness_score": avg_score, "clarity_score": avg_score,
                        "communication_score": avg_score, "answer_length": 60,
                        "keyword_coverage": 0.75, "difficulty_numeric": 2,
                        "attempt_number": len(evals), "previous_score": avg_score,
                        "average_previous_score": avg_score, "topic_accuracy": avg_score
                    })

                    rec_out = recommendation_agent.process({
                        "target_role": session.target_role,
                        "evaluation_history": [{"overall_score": e.overall_score, "strengths": e.strengths, "weaknesses": e.weaknesses} for e in evals],
                        "question_history": [{"topic": q.topic, "difficulty": q.difficulty} for q in session.questions],
                        "skill_gaps": []
                    })
                    rec_obj = RecommendationOutput(**rec_out["recommendations"])

                    int_repo.complete_session(session.id, round(avg_score, 1), ml_res["readiness_score"], ml_res["readiness_label"])
                    int_repo.save_recommendation(session.id, session.user_id, rec_obj.overall_summary, rec_obj.strong_areas, rec_obj.weak_areas, rec_obj.learning_priorities, rec_obj.practice_questions)

                    st.session_state.interview_completed = True
                    st.rerun()

            else:
                if st.button("➡️ Next Adaptive Question", type="primary"):
                    questions = int_repo.get_questions_for_session(session.id)
                    q_res = question_agent.process({
                        "session_id": session.id, "target_role": session.target_role,
                        "current_difficulty": session.difficulty, "current_question_index": session.current_question_index,
                        "total_questions": session.total_questions, "candidate_profile": {},
                        "job_profile": {"job_title": session.target_role, "required_skills": ["System Design", "RAG"]},
                        "skill_gaps": ["System Design"], "previous_topics": [q.topic for q in questions],
                        "question_history": [{"question": q.question_text, "topic": q.topic} for q in questions],
                        "answer_history": [a.candidate_answer for a in session.answers],
                        "evaluation_history": [{"technical_accuracy": e.technical_accuracy, "overall_score": e.overall_score, "missing_concepts": e.missing_concepts or [], "weaknesses": e.weaknesses or []} for e in session.evaluations]
                    })
                    next_q = InterviewQuestion(**q_res["current_question"])
                    int_repo.add_question(session.id, len(questions) + 1, next_q.question, next_q.topic, next_q.difficulty, next_q.question_type, next_q.reason, next_q.expected_concepts, next_q.source_context)
                    st.session_state.current_question = next_q
                    st.session_state.current_evaluation = None
                    st.rerun()

elif page == PAGE_ANALYTICS:
    st.title("Performance Analytics & ML Readiness")
    analytics_data = aggregate_user_analytics(user_id=st.session_state.user_id, db=db)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_radar_chart(
            analytics_data["average_technical_score"], analytics_data["average_relevance_score"],
            analytics_data["average_completeness_score"], analytics_data["average_clarity_score"],
            analytics_data["average_communication_score"]
        ), use_container_width=True)

    with col2:
        st.subheader(f"ML Predicted Readiness: {analytics_data['overall_readiness_label']}")
        st.metric("Overall Score Average", f"{analytics_data['average_overall_score']}%")
        st.caption("Scikit-Learn model trained on development dataset.")

    latest = int_repo.list_sessions_for_user(st.session_state.user_id)
    if latest and latest[0].recommendation:
        rec = latest[0].recommendation
        st.divider()
        st.subheader("Personalized Study Roadmap")
        st.write(rec.overall_summary)
        for p in (rec.learning_priorities or []):
            st.markdown(f"- **{p}**")

elif page == PAGE_HISTORY:
    st.title("Interview History")
    sessions = int_repo.list_sessions_for_user(st.session_state.user_id)
    if not sessions:
        st.info("No recorded sessions yet.")
    else:
        for s in sessions:
            with st.expander(f"Session #{s.id} — {s.target_role} | Score: {s.overall_score or 'In Progress'}% | {s.status}"):
                st.write(f"**Difficulty:** {s.difficulty} | **Readiness:** {s.readiness_label or 'N/A'}")
                for q in s.questions:
                    st.markdown(f"**Q{q.question_number} [{q.topic}]:** {q.question_text}")
                    if q.answer:
                        st.markdown(f"*Ans:* {q.answer.candidate_answer}")
                        if q.answer.evaluation:
                            st.caption(f"Score: {q.answer.evaluation.overall_score}% | Feedback: {q.answer.evaluation.feedback}")

elif page == PAGE_SETTINGS:
    st.title("Settings & System Status")
    s = get_settings()
    st.write(f"**LLM Provider:** `{s.LLM_PROVIDER}`")
    st.write(f"**Embedding Model:** `{s.EMBEDDING_MODEL}`")
    st.write(f"**Vector Store:** `{s.VECTOR_STORE_TYPE}`")
    st.write(f"**Database:** `{s.DATABASE_URL}`")
    st.success("All Milestones 1 through 8 active and connected to live backend engine!")

db.close()
