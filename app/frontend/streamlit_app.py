# -*- coding: utf-8 -*-
"""AI Interview Coach — Adaptive GenAI Interview Platform"""

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

# ── Page identifiers ──────────────────────────────────────────────────────────
PAGE_HOME      = "Home Dashboard"
PAGE_RESUME    = "Resume Intelligence"
PAGE_JD        = "Job Description"
PAGE_MATCH     = "Match & Skill Gap"
PAGE_KB        = "Knowledge Base"
PAGE_INTERVIEW = "Live Interview"
PAGE_ANALYTICS = "Analytics"
PAGE_HISTORY   = "Interview History"
PAGE_SETTINGS  = "Settings & Status"

st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="\U0001f3af",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ── Design system CSS ─────────────────────────────────────────────────────────
_CSS = """
<style>
html,body,[data-testid="stApp"]{background:#0f1117!important;color:#e2e8f0!important;font-family:Inter,'Segoe UI',system-ui,sans-serif!important}
#MainMenu,footer,header{visibility:hidden!important}
[data-testid="stToolbar"],[data-testid="stDecoration"],.stDeployButton{display:none!important}
[data-testid="stSidebar"]{background:#111827!important;border-right:1px solid #1f2937!important;padding:0!important}
[data-testid="stSidebar"]>div:first-child{padding:0!important}
.main .block-container{padding:1.5rem 2rem 2rem 2rem!important;max-width:1400px!important}
.card{background:#1a2035;border:1px solid #1f2937;border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:1rem}
.card-sm{background:#1a2035;border:1px solid #1f2937;border-radius:10px;padding:.9rem 1.1rem;margin-bottom:.6rem}
.page-header{margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid #1f2937}
.page-title{font-size:1.6rem;font-weight:700;color:#f1f5f9;margin:0 0 .2rem 0}
.page-subtitle{font-size:.85rem;color:#64748b;margin:0}
.section-label{font-size:.68rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#374151;margin:.6rem 0 .35rem 0;padding:0 1.25rem}
.nav-item{display:flex;align-items:center;gap:.65rem;padding:.55rem 1.25rem;border-radius:8px;margin:.05rem .75rem;font-size:.875rem;color:#6b7280}
.nav-item.active{background:#1e3a5f;color:#60a5fa;font-weight:600}
.nav-icon{font-size:.95rem;width:1.1rem;text-align:center}
.sidebar-brand{padding:1.25rem 1.25rem .75rem 1.25rem;border-bottom:1px solid #1f2937;margin-bottom:.5rem}
.brand-title{font-size:1rem;font-weight:700;color:#f1f5f9;margin:.3rem 0 .1rem 0}
.brand-sub{font-size:.7rem;color:#374151}
.sidebar-profile{margin:.4rem .75rem .75rem .75rem;padding:.6rem .9rem;background:#0d1320;border:1px solid #1f2937;border-radius:8px;font-size:.78rem;color:#475569}
.empty-state{text-align:center;padding:2.5rem 1.5rem;color:#374151}
.empty-icon{font-size:2.2rem;margin-bottom:.6rem}
.empty-title{font-size:.95rem;font-weight:600;color:#4b5563;margin-bottom:.3rem}
.empty-desc{font-size:.8rem;color:#374151}
.badge{display:inline-block;padding:.18em .6em;border-radius:20px;font-size:.7rem;font-weight:600;letter-spacing:.03em}
.badge-green{background:#064e3b;color:#6ee7b7}
.badge-yellow{background:#451a03;color:#fcd34d}
.badge-red{background:#450a0a;color:#fca5a5}
.badge-blue{background:#1e3a5f;color:#93c5fd}
.badge-gray{background:#1f2937;color:#9ca3af}
.score-bar-wrap{margin-bottom:.55rem}
.score-bar-label{display:flex;justify-content:space-between;font-size:.76rem;color:#94a3b8;margin-bottom:.2rem}
.score-bar-track{background:#1f2937;border-radius:4px;height:5px}
.score-bar-fill{height:5px;border-radius:4px;background:linear-gradient(90deg,#3b82f6,#818cf8)}
.question-block{background:#162032;border:1px solid #1d3557;border-left:4px solid #3b82f6;border-radius:10px;padding:1.2rem 1.4rem;margin-bottom:1rem}
.question-meta{display:flex;gap:.45rem;margin-bottom:.7rem;flex-wrap:wrap}
.question-text{font-size:.975rem;font-weight:500;color:#e2e8f0;line-height:1.55}
.eval-card{background:#0d1f12;border:1px solid #1a3a22;border-left:4px solid #10b981;border-radius:10px;padding:1.2rem 1.4rem;margin-bottom:1rem}
.gap-item{background:#1a1208;border:1px solid #2d1f05;border-radius:8px;padding:.65rem .9rem;margin-bottom:.45rem}
.gap-item-high{background:#1c0a0a;border-color:#3b1010}
.skill-tag{display:inline-block;background:#1e3a5f;color:#93c5fd;border-radius:6px;padding:.18em .5em;font-size:.71rem;font-weight:500;margin:.12em}
[data-testid="stTextArea"] textarea,[data-testid="stTextInput"] input{background:#1a2035!important;border:1px solid #2d3748!important;color:#e2e8f0!important;border-radius:8px!important}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#1d4ed8,#2563eb)!important;border:none!important;color:#fff!important;font-weight:600!important;border-radius:8px!important}
.stButton>button:not([kind="primary"]){background:#1f2937!important;border:1px solid #374151!important;color:#d1d5db!important;border-radius:8px!important;font-weight:500!important}
[data-testid="stExpander"]{background:#1a2035!important;border:1px solid #1f2937!important;border-radius:10px!important}
[data-testid="stMetric"]{background:#1a2035;border:1px solid #1f2937;border-radius:10px;padding:.7rem .9rem!important}
[data-testid="stMetricLabel"]{color:#64748b!important;font-size:.75rem!important}
[data-testid="stMetricValue"]{color:#f1f5f9!important}
.js-plotly-plot .plotly .main-svg{background:transparent!important}
hr{border-color:#1f2937!important}
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:#0f1117}
::-webkit-scrollbar-thumb{background:#2d3748;border-radius:3px}
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()

_DEFAULTS = {
    "user_id": 1, "candidate_profile": None, "job_profile": None,
    "match_result": None, "interview_session_id": None,
    "current_question": None, "current_evaluation": None,
    "interview_completed": False, "active_page": PAGE_HOME,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

db        = SessionLocal()
user_repo = UserRepository(db)
int_repo  = InterviewRepository(db)

user = user_repo.get_user_by_id(st.session_state.user_id)
if not user:
    user = user_repo.get_or_create_user(name="Candidate", email="user@aicoach.local", target_role=None)
    st.session_state.user_id = user.id

# ── Helpers ───────────────────────────────────────────────────────────────────
def score_bar(label, value, max_val=100.0):
    pct = max(0, min(100, (value / max_val) * 100)) if max_val else 0
    st.markdown(
        f'<div class="score-bar-wrap">'
        f'<div class="score-bar-label"><span>{label}</span><span>{value:.1f}%</span></div>'
        f'<div class="score-bar-track"><div class="score-bar-fill" style="width:{pct}%"></div></div>'
        f'</div>', unsafe_allow_html=True)

def readiness_badge(label):
    cls = {"Interview Ready": "badge-green", "Almost Ready": "badge-yellow",
           "Needs Improvement": "badge-red"}.get(label, "badge-gray")
    return f'<span class="badge {cls}">{label}</span>'

def difficulty_badge(label):
    cls = {"Easy": "badge-green", "Medium": "badge-yellow", "Hard": "badge-red"}.get(label, "badge-blue")
    return f'<span class="badge {cls}">{label}</span>'

def empty_state(icon, title, desc):
    st.markdown(
        f'<div class="empty-state"><div class="empty-icon">{icon}</div>'
        f'<div class="empty-title">{title}</div>'
        f'<div class="empty-desc">{desc}</div></div>', unsafe_allow_html=True)

_PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter, Segoe UI, sans-serif"),
    margin=dict(l=30, r=30, t=45, b=30),
)
_PLOTLY_CFG = {"displayModeBar": False}

def apply_dark(fig, height=300):
    fig.update_layout(**_PLOTLY_LAYOUT, height=height)
    fig.update_xaxes(gridcolor="#1f2937", zerolinecolor="#1f2937")
    fig.update_yaxes(gridcolor="#1f2937", zerolinecolor="#1f2937")
    return fig

# ── Sidebar ───────────────────────────────────────────────────────────────────
_NAV = [
    ("OVERVIEW",  [("\U0001f3e0", PAGE_HOME,      "Dashboard")]),
    ("PREPARE",   [("\U0001f4c4", PAGE_RESUME,    "Resume Intelligence"),
                   ("\U0001f4bc", PAGE_JD,         "Job Description"),
                   ("\u2696",     PAGE_MATCH,      "Match & Skill Gap"),
                   ("\U0001f4da", PAGE_KB,         "Knowledge Base")]),
    ("INTERVIEW", [("\U0001f399", PAGE_INTERVIEW,  "Live Adaptive Interview")]),
    ("INSIGHTS",  [("\U0001f4ca", PAGE_ANALYTICS,  "Analytics & Readiness"),
                   ("\U0001f4dc", PAGE_HISTORY,    "Interview History")]),
    ("SYSTEM",    [("\u2699",     PAGE_SETTINGS,   "Settings & Status")]),
]

with st.sidebar:
    _pname = st.session_state.candidate_profile.name if st.session_state.candidate_profile else None
    _prole = st.session_state.job_profile.job_title   if st.session_state.job_profile        else None

    st.markdown("""<div class="sidebar-brand">
  <div style="font-size:1.3rem">\U0001f3af</div>
  <div class="brand-title">AI Interview Coach</div>
  <div class="brand-sub">Adaptive GenAI &amp; ML Platform</div>
</div>""", unsafe_allow_html=True)

    _all_pages = [p for _, items in _NAV for _, p, _ in items]
    _idx = _all_pages.index(st.session_state.active_page) if st.session_state.active_page in _all_pages else 0
    page = st.radio("nav", _all_pages, label_visibility="collapsed", index=_idx)
    st.session_state.active_page = page

    _nav_html = ""
    for _sec, _items in _NAV:
        _nav_html += f'<div class="section-label">{_sec}</div>'
        for _icon, _pid, _label in _items:
            _cls = " active" if page == _pid else ""
            _nav_html += f'<div class="nav-item{_cls}"><span class="nav-icon">{_icon}</span>{_label}</div>'
        _nav_html += "<div style='height:.3rem'></div>"
    st.markdown(_nav_html, unsafe_allow_html=True)

    if _pname or _prole:
        _cn = _pname or "Candidate"
        _cr = _prole or (user.target_role or "Role not set")
        st.markdown(
            f'<div class="sidebar-profile">'
            f'<div style="font-size:.65rem;color:#374151;margin-bottom:.1rem">ACTIVE PROFILE</div>'
            f'<div style="font-weight:600;color:#e2e8f0;font-size:.8rem">{_cn}</div>'
            f'<div style="font-size:.7rem;color:#475569">{_cr}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="sidebar-profile">'
            '<div style="font-size:.65rem;color:#374151;margin-bottom:.1rem">PROFILE</div>'
            '<div style="font-size:.75rem;color:#374151">No resume loaded</div></div>',
            unsafe_allow_html=True)

if page == PAGE_HOME:
    st.markdown("""<div class="page-header">
  <div class="page-title">Interview Performance Dashboard</div>
  <div class="page-subtitle">Real-time readiness, skill alignment, and preparation roadmap</div>
</div>""", unsafe_allow_html=True)

    analytics_data = aggregate_user_analytics(user_id=st.session_state.user_id, db=db)
    latest_gap     = user_repo.get_latest_skill_gap_analysis(user_id=st.session_state.user_id)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Sessions",    analytics_data["total_interviews"])
    k2.metric("Avg Overall Score", f"{analytics_data['average_overall_score']}%" if analytics_data['average_overall_score'] else "\u2014")
    k3.metric("Job Match",         f"{latest_gap.overall_match_score:.0f}%" if latest_gap else "\u2014")
    k4.metric("ML Readiness",      analytics_data["overall_readiness_label"])

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
    _ac, _ = st.columns([2, 5])
    with _ac:
        if st.button("\U0001f680  Start New Interview", type="primary", use_container_width=True):
            st.session_state.interview_session_id = None
            st.session_state.interview_completed  = False
            st.session_state.current_question     = None
            st.session_state.current_evaluation   = None
            st.session_state.active_page          = PAGE_INTERVIEW
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    _cl, _cr = st.columns([3, 2])

    with _cl:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Score Trajectory**")
        if analytics_data["score_history"]:
            _f1 = create_score_history_chart(analytics_data["score_history"])
            st.plotly_chart(apply_dark(_f1, 255), use_container_width=True, config=_PLOTLY_CFG)
        else:
            empty_state("\U0001f4c8", "No interview data yet", "Complete a session to track score progress.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Topic Proficiency**")
        if analytics_data["topic_performance"]:
            _f2 = create_topic_performance_bar(analytics_data["topic_performance"])
            st.plotly_chart(apply_dark(_f2, 255), use_container_width=True, config=_PLOTLY_CFG)
        else:
            empty_state("\U0001f9e0", "No topic data", "Answer questions across topics to see breakdown.")
        st.markdown('</div>', unsafe_allow_html=True)

    with _cr:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Job Alignment**")
        if latest_gap:
            _f3 = create_match_gauge(latest_gap.overall_match_score)
            st.plotly_chart(apply_dark(_f3, 190), use_container_width=True, config=_PLOTLY_CFG)
            st.markdown(f'Match: &nbsp;<span class="badge badge-blue">{latest_gap.match_category}</span>', unsafe_allow_html=True)
        else:
            empty_state("\u2696", "No match analysis", "Load resume + JD and run the Match engine.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Priority Focus Areas**")
        _weak   = analytics_data.get("weak_areas", [])
        _strong = analytics_data.get("strong_areas", [])
        if _weak:
            for _w in _weak:
                st.markdown(f'\u26a0\ufe0f &nbsp;<span style="color:#fcd34d">{_w}</span>', unsafe_allow_html=True)
        elif _strong:
            st.markdown('<span class="badge badge-green">\u2714 No weak areas detected</span>', unsafe_allow_html=True)
        else:
            empty_state("\U0001f4a1", "No data", "Complete interviews to identify focus areas.")
        st.markdown('</div>', unsafe_allow_html=True)

elif page == PAGE_RESUME:
    st.markdown("""<div class="page-header">
  <div class="page-title">Resume Intelligence</div>
  <div class="page-subtitle">Upload your resume \u2014 skills, experience, and education extracted automatically</div>
</div>""", unsafe_allow_html=True)

    _uc, _ = st.columns([3, 2])
    with _uc:
        uploaded_file = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=["pdf","docx","txt"])
        _b1, _b2 = st.columns(2)
        _load_sample = _b1.button("\U0001f4c4 Load Sample Resume", use_container_width=True)
        _clear_btn   = _b2.button("Clear Profile", use_container_width=True)

    if _clear_btn:
        st.session_state.candidate_profile = None
        st.rerun()

    if _load_sample:
        _sample_text = """David Miller
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
        _profile = resume_parser.parse(_sample_text, "sample_ml_resume.txt")
        st.session_state.candidate_profile = _profile
        user_repo.save_resume(st.session_state.user_id, "sample_ml_resume.txt", "txt", _sample_text, _profile.model_dump())
        st.success("\u2714 Sample resume loaded.")

    elif uploaded_file is not None:
        os.makedirs("data/uploads", exist_ok=True)
        _tmp = os.path.join("data/uploads", uploaded_file.name)
        with open(_tmp, "wb") as _fh:
            _fh.write(uploaded_file.read())
        from nlp.preprocessing import extract_text_from_file
        _txt = extract_text_from_file(_tmp)
        _profile = resume_parser.parse(_txt, uploaded_file.name)
        st.session_state.candidate_profile = _profile
        user_repo.save_resume(st.session_state.user_id, uploaded_file.name,
                              uploaded_file.name.split(".")[-1], _txt, _profile.model_dump())
        st.success(f"\u2714 Profile extracted for **{_profile.name}**")

    if st.session_state.candidate_profile:
        _p = st.session_state.candidate_profile
        st.markdown("<hr>", unsafe_allow_html=True)
        _ic, _sc = st.columns([2, 3])
        with _ic:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"**{_p.name}**")
            if hasattr(_p, "contact") and _p.contact:
                if _p.contact.email:  st.markdown(f"\U0001f4e7 `{_p.contact.email}`")
                if _p.contact.phone:  st.markdown(f"\U0001f4de `{_p.contact.phone}`")
            _exp = getattr(_p, "experience_level", None) or getattr(_p, "seniority_level", None)
            if _exp:
                st.markdown(f'Experience: &nbsp;<span class="badge badge-blue">{_exp}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if hasattr(_p, "education") and _p.education:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**Education**")
                for _edu in _p.education:
                    st.markdown(f"\U0001f393 {_edu if isinstance(_edu,str) else str(_edu)}")
                st.markdown('</div>', unsafe_allow_html=True)
        with _sc:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**Extracted Skills**")
            _tags = "".join(f'<span class="skill-tag">{_s}</span>' for _s in _p.skills)
            st.markdown(f'<div style="line-height:2">{_tags}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if hasattr(_p, "work_experience") and _p.work_experience:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**Work Experience**")
                for _e in _p.work_experience:
                    st.markdown(f"\u2022 {_e if isinstance(_e,str) else str(_e)}")
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("<hr>", unsafe_allow_html=True)
        empty_state("\U0001f4c4", "No resume loaded", "Upload your resume or load the sample to get started.")

elif page == PAGE_JD:
    st.markdown("""<div class="page-header">
  <div class="page-title">Job Description Intelligence</div>
  <div class="page-subtitle">Paste a job description to extract required skills, seniority, and focus areas</div>
</div>""", unsafe_allow_html=True)

    _jd_text = st.text_area("Paste Job Description", height=220, value="""Requirements:
- 4+ years of hands-on experience in Python and PyTorch.
- Strong knowledge of Docker, Kubernetes, and AWS cloud infrastructure.
- In-depth understanding of Retrieval-Augmented Generation (RAG) and Large Language Models.

Preferred Qualifications:
- Experience with LangChain and FAISS.
- Strong System Design and distributed architecture fundamentals.""")

    _bc, _ = st.columns([2, 5])
    with _bc:
        if st.button("\U0001f4bc Analyze Job Description", type="primary", use_container_width=True):
            _jp = jd_parser.parse(_jd_text, default_title="Senior Machine Learning Engineer")
            st.session_state.job_profile = _jp
            user_repo.save_job_description(st.session_state.user_id, _jp.job_title, _jd_text, _jp.model_dump())
            st.success(f"\u2714 Analyzed: **{_jp.job_title}** ({_jp.role_level})")

    if st.session_state.job_profile:
        _jp = st.session_state.job_profile
        st.markdown("<hr>", unsafe_allow_html=True)
        _rc, _pc = st.columns(2)
        with _rc:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**Required Skills**")
            for _sk in _jp.required_skills:
                st.markdown(f'\u2022 <span class="skill-tag">{_sk}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with _pc:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**Preferred Skills**")
            for _sk in _jp.preferred_skills:
                st.markdown(f'\u2022 <span class="skill-tag">{_sk}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("<hr>", unsafe_allow_html=True)
        empty_state("\U0001f4bc", "No JD analyzed", "Paste a job posting above and click Analyze.")

elif page == PAGE_MATCH:
    st.markdown("""<div class="page-header">
  <div class="page-title">Match &amp; Skill Gap Analysis</div>
  <div class="page-subtitle">Semantic alignment score between your resume and the target role</div>
</div>""", unsafe_allow_html=True)

    if not st.session_state.candidate_profile or not st.session_state.job_profile:
        empty_state("\u26a0\ufe0f", "Resume or Job Description missing",
                    "Load your resume in 'Resume Intelligence' and analyze a JD in 'Job Description' first.")
    else:
        _bc2, _ = st.columns([2, 5])
        with _bc2:
            _run_match = st.button("\u2696 Run Alignment Analysis", type="primary", use_container_width=True)

        if _run_match or st.session_state.match_result is None:
            with st.spinner("Computing semantic alignment..."):
                _res = matching_engine.analyze_match(st.session_state.candidate_profile, st.session_state.job_profile)
            st.session_state.match_result = _res
            user_repo.save_skill_gap_analysis(
                st.session_state.user_id, None, None,
                _res.overall_match_score, _res.match_category,
                [_m.model_dump() for _m in _res.skill_breakdown],
                _res.gap_report.model_dump()
            )

        _res = st.session_state.match_result
        if _res:
            st.markdown("<hr>", unsafe_allow_html=True)
            _gc, _dc = st.columns([2, 3])
            with _gc:
                st.markdown('<div class="card" style="text-align:center">', unsafe_allow_html=True)
                _fg = create_match_gauge(_res.overall_match_score)
                st.plotly_chart(apply_dark(_fg, 200), use_container_width=True, config=_PLOTLY_CFG)
                st.markdown(
                    f'<div style="text-align:center"><span class="badge badge-blue" '
                    f'style="font-size:.82rem;padding:.3em .8em">{_res.match_category}</span></div>',
                    unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**Score Breakdown**")
                score_bar("Required Skills Coverage", _res.explanation.required_skills_coverage)
                _sem = getattr(_res.explanation, "semantic_similarity_score", None)
                if _sem is not None:
                    score_bar("Semantic Similarity", _sem * 100)
                st.markdown('</div>', unsafe_allow_html=True)
            with _dc:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**Summary**")
                st.markdown(f'<div style="color:#94a3b8;font-size:.875rem;line-height:1.6">{_res.explanation.summary_explanation}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                _matched = [_s for _s in _res.skill_breakdown if _s.is_matched]
                if _matched:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("**Matched Skills**")
                    _mt = "".join(f'<span class="skill-tag">\u2713 {_s.skill}</span>' for _s in _matched)
                    st.markdown(f'<div style="line-height:2">{_mt}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                _hg = _res.gap_report.high_priority_gaps
                _mg = _res.gap_report.medium_priority_gaps
                if _hg or _mg:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("**Skill Gaps**")
                    for _gap in _hg:
                        st.markdown(
                            f'<div class="gap-item gap-item-high">'
                            f'<span class="badge badge-red">HIGH</span> &nbsp;'
                            f'<strong style="color:#fca5a5">{_gap.skill}</strong>'
                            f'<span style="float:right;font-size:.72rem;color:#64748b">Proficiency: {_gap.current_proficiency_estimate}%</span></div>',
                            unsafe_allow_html=True)
                    for _gap in _mg:
                        st.markdown(
                            f'<div class="gap-item"><span class="badge badge-yellow">MED</span> &nbsp;<strong style="color:#fcd34d">{_gap.skill}</strong></div>',
                            unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

elif page == PAGE_KB:
    st.markdown("""<div class="page-header">
  <div class="page-title">Technical Knowledge Base</div>
  <div class="page-subtitle">FAISS vector store \u2014 RAG-grounded context for question generation</div>
</div>""", unsafe_allow_html=True)

    _sf = "data/knowledge_base/faiss_index/index_summary.json"
    if os.path.exists(_sf):
        with open(_sf, "r", encoding="utf-8") as _fh:
            _summary = json.load(_fh)
        _c1, _c2, _c3 = st.columns(3)
        _c1.metric("Indexed Chunks",    _summary.get("total_chunks", 0))
        _c2.metric("Vector Dimensions", _summary.get("dimension", 384))
        _c3.metric("Knowledge Domains", len(_summary.get("topics", [])))
        _topics = _summary.get("topics", [])
        if _topics:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**Indexed Domains**")
            _tt = "".join(f'<span class="skill-tag">{_t}</span>' for _t in _topics)
            st.markdown(f'<div style="line-height:2">{_tt}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Knowledge base index not found. Click Re-Index to build it.")

    _ri, _ = st.columns([2, 5])
    with _ri:
        if st.button("\U0001f504 Re-Index Knowledge Base", use_container_width=True):
            with st.spinner("Indexing..."):
                _ing = ingest_knowledge_base()
            st.success(f"\u2714 Indexed {_ing['total_chunks']} chunks across {len(_ing['topics'])} topics")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Semantic Search**")
    st.markdown('<div style="color:#475569;font-size:.78rem;margin-bottom:.6rem">Query the vector store to inspect context the Question Agent will receive</div>', unsafe_allow_html=True)
    _test_q = st.text_input("Search query", value="Explain CAP theorem trade-offs", label_visibility="collapsed")
    if st.button("\U0001f50d Search Vectors", type="primary"):
        with st.spinner("Retrieving context..."):
            _ctx = rag_retriever.build_grounded_context(_test_q, top_k=3)
        _conf     = _ctx.get("confidence_score", 0) * 100
        _grounded = _ctx.get("has_grounding", False)
        st.markdown(
            f'Confidence: &nbsp;<span class="badge {"badge-green" if _conf > 50 else "badge-yellow"}">{_conf:.1f}%</span>'
            f' &nbsp;Grounded: &nbsp;<span class="badge {"badge-green" if _grounded else "badge-red"}">{"Yes" if _grounded else "No"}</span>',
            unsafe_allow_html=True)
        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        st.text_area("Retrieved Context", _ctx.get("context_text",""), height=180)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == PAGE_INTERVIEW:
    st.markdown("""<div class="page-header">
  <div class="page-title">Live Adaptive Interview</div>
  <div class="page-subtitle">AI-generated questions that adapt in real-time to your performance</div>
</div>""", unsafe_allow_html=True)

    if st.session_state.interview_completed:
        _sess = int_repo.list_sessions_for_user(st.session_state.user_id)
        _ls   = _sess[0] if _sess else None
        st.markdown('<div class="eval-card">', unsafe_allow_html=True)
        st.markdown("### \U0001f3c1 Interview Complete")
        if _ls:
            _sv = _ls.overall_score or 0
            _rl = _ls.readiness_label or "Not evaluated"
            st.markdown(
                f'Overall Score: &nbsp;<strong style="color:#34d399;font-size:1.25rem">{_sv:.1f}%</strong>'
                f' &nbsp;&nbsp;Readiness: &nbsp;{readiness_badge(_rl)}', unsafe_allow_html=True)
            if _ls.recommendation:
                _rec = _ls.recommendation
                st.markdown(f'<div style="color:#94a3b8;font-size:.875rem;margin-top:.75rem">{_rec.overall_summary}</div>', unsafe_allow_html=True)
                if _rec.learning_priorities:
                    st.markdown("**Priority Topics:**")
                    for _lp in _rec.learning_priorities:
                        st.markdown(f"\u2022 {_lp}")
        st.markdown('</div>', unsafe_allow_html=True)
        _nc, _ = st.columns([2, 5])
        with _nc:
            if st.button("\U0001f501 Start New Session", type="primary", use_container_width=True):
                st.session_state.interview_session_id = None
                st.session_state.interview_completed  = False
                st.session_state.current_question     = None
                st.session_state.current_evaluation   = None
                st.rerun()

    elif st.session_state.interview_session_id is None:
        _sc2, _ = st.columns([3, 2])
        with _sc2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**Session Configuration**")
            _role = st.text_input("Target Role",
                value=(st.session_state.job_profile.job_title
                       if st.session_state.job_profile
                       else (user.target_role or "Senior Machine Learning Engineer")))
            _dc, _nc2 = st.columns(2)
            _diff  = _dc.selectbox("Starting Difficulty", ["Medium","Easy","Hard"], index=0)
            _num_q = _nc2.slider("Questions", 1, 5, 2)
            for _tip in ["\U0001f4a1 Questions adapt to your answer quality",
                         "\U0001f9e0 Strong answers escalate difficulty",
                         "\U0001f4cb Weak answers trigger targeted follow-ups"]:
                st.markdown(f'<div style="color:#374151;font-size:.75rem;margin-top:.2rem">{_tip}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("\U0001f680 Start Interview", type="primary", use_container_width=True):
                _cand_p = st.session_state.candidate_profile or CandidateProfile(name=user.name, skills=["Python","System Design"])
                _job_p  = st.session_state.job_profile or JobProfile(job_title=_role, required_skills=["Python","RAG"])
                _session = int_repo.create_session(st.session_state.user_id, _role, difficulty=_diff, total_questions=_num_q)
                _q_res = question_agent.process({
                    "session_id": _session.id, "target_role": _role, "current_difficulty": _diff,
                    "current_question_index": 0, "total_questions": _num_q,
                    "candidate_profile": _cand_p.model_dump(), "job_profile": _job_p.model_dump(),
                    "skill_gaps": ["System Design","RAG"], "previous_topics": [],
                    "question_history": [], "answer_history": [], "evaluation_history": []
                })
                _q_obj = InterviewQuestion(**_q_res["current_question"])
                int_repo.add_question(_session.id, 1, _q_obj.question, _q_obj.topic, _q_obj.difficulty,
                                      _q_obj.question_type, _q_obj.reason, _q_obj.expected_concepts, _q_obj.source_context)
                st.session_state.interview_session_id = _session.id
                st.session_state.current_question     = _q_obj
                st.session_state.current_evaluation   = None
                st.session_state.interview_completed  = False
                st.rerun()

    else:
        _session  = int_repo.get_session(st.session_state.interview_session_id)
        _q_obj    = st.session_state.current_question
        _curr_idx = _session.current_question_index + 1
        _prog_pct = (_curr_idx - 1) / max(_session.total_questions, 1)

        st.markdown(
            f'<div style="display:flex;justify-content:space-between;font-size:.75rem;color:#475569;margin-bottom:.25rem">'
            f'<span>Question {_curr_idx} of {_session.total_questions}</span>'
            f'<span>{int(_prog_pct*100)}% complete</span></div>', unsafe_allow_html=True)
        st.progress(_prog_pct)

        st.markdown(
            f'<div class="question-block">'
            f'<div class="question-meta">'
            f'<span class="badge badge-blue">{_q_obj.topic}</span>'
            f'{difficulty_badge(_q_obj.difficulty)}'
            f'<span class="badge badge-gray">{_q_obj.question_type or "Technical"}</span></div>'
            f'<div class="question-text">{_q_obj.question}</div></div>', unsafe_allow_html=True)

        if st.session_state.current_evaluation is None:
            _ans = st.text_area("Your Answer", height=150, placeholder="Type your answer here...")
            _bs, _bsamp, _ = st.columns([2, 2, 3])
            _submit_clicked = _bs.button("\u2714 Submit Answer", type="primary", use_container_width=True)
            _sample_clicked = _bsamp.button("\U0001f4dd Use Sample Answer", use_container_width=True)

            def _submit(_answer_text):
                _questions = int_repo.get_questions_for_session(_session.id)
                _ans_rec   = int_repo.record_answer(_session.id, _questions[-1].id, _answer_text)
                _eval_res  = evaluation_agent.process({
                    "current_question": _q_obj.model_dump(), "current_answer": _answer_text,
                    "current_difficulty": _session.difficulty,
                    "question_history": [{"question": _q.question_text, "topic": _q.topic} for _q in _questions],
                    "answer_history": [_answer_text], "evaluation_history": [],
                    "current_question_index": _session.current_question_index
                })
                _eval_obj = AnswerEvaluation(**_eval_res["current_evaluation"])
                int_repo.record_evaluation(
                    _session.id, _ans_rec.id, _eval_obj.technical_accuracy, _eval_obj.relevance,
                    _eval_obj.completeness, _eval_obj.clarity, _eval_obj.communication,
                    _eval_obj.overall_score, _eval_obj.strengths, _eval_obj.weaknesses,
                    _eval_obj.missing_concepts, _eval_obj.feedback, _eval_obj.next_difficulty)
                st.session_state.current_evaluation = _eval_obj

            if _submit_clicked:
                if not _ans.strip():
                    st.error("Please enter an answer before submitting.")
                else:
                    with st.spinner("Evaluating..."):
                        _submit(_ans)
                    st.rerun()

            if _sample_clicked:
                _sa = ("The Python GIL is a mutex in CPython that prevents multiple native threads "
                       "from executing bytecodes concurrently. To overcome it for CPU-bound tasks, "
                       "we use multiprocessing to spawn separate processes with independent memory heaps.")
                with st.spinner("Submitting sample..."):
                    _submit(_sa)
                st.rerun()

        else:
            _ev = st.session_state.current_evaluation
            _oc = "#34d399" if _ev.overall_score >= 75 else ("#fbbf24" if _ev.overall_score >= 55 else "#f87171")
            st.markdown(
                f'<div class="eval-card">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.9rem">'
                f'<span style="font-weight:600;color:#e2e8f0">Evaluation Result</span>'
                f'<span style="font-size:1.35rem;font-weight:700;color:{_oc}">{_ev.overall_score:.1f}%</span></div>',
                unsafe_allow_html=True)
            _s1, _s2 = st.columns(2)
            with _s1:
                score_bar("Technical Accuracy", _ev.technical_accuracy)
                score_bar("Relevance",           _ev.relevance)
                score_bar("Completeness",        _ev.completeness)
            with _s2:
                score_bar("Clarity",       _ev.clarity)
                score_bar("Communication", _ev.communication)
            st.markdown("</div>", unsafe_allow_html=True)

            if _ev.feedback:
                st.markdown(f'<div class="card-sm" style="color:#94a3b8;font-size:.875rem">\U0001f4ac {_ev.feedback}</div>', unsafe_allow_html=True)

            _fl, _fr = st.columns(2)
            with _fl:
                if _ev.strengths:
                    st.markdown('<div class="card-sm">', unsafe_allow_html=True)
                    st.markdown("**Strengths**")
                    for _s in _ev.strengths:
                        st.markdown(f'\u2705 <span style="color:#6ee7b7;font-size:.82rem">{_s}</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            with _fr:
                if _ev.weaknesses or _ev.missing_concepts:
                    st.markdown('<div class="card-sm">', unsafe_allow_html=True)
                    st.markdown("**Areas to Improve**")
                    for _w in (_ev.weaknesses or []):
                        st.markdown(f'\u26a0\ufe0f <span style="color:#fcd34d;font-size:.82rem">{_w}</span>', unsafe_allow_html=True)
                    for _mc in (_ev.missing_concepts or []):
                        st.markdown(f'\u2795 <span style="color:#94a3b8;font-size:.82rem">Missing: {_mc}</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(f'Next difficulty: &nbsp;{difficulty_badge(_ev.next_difficulty or "Medium")}', unsafe_allow_html=True)
            st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

            _is_last = _session.current_question_index >= _session.total_questions
            _nc1, _nc2, _ = st.columns([2, 2, 3])

            if _is_last:
                if _nc1.button("\U0001f3c1 Finalize & View Results", type="primary", use_container_width=True):
                    _evals     = _session.evaluations
                    _avg_score = sum(_e.overall_score for _e in _evals) / len(_evals) if _evals else 70.0
                    _ml_res = ml_predictor.predict_readiness({
                        "technical_score": _avg_score, "relevance_score": _avg_score,
                        "completeness_score": _avg_score, "clarity_score": _avg_score,
                        "communication_score": _avg_score, "answer_length": 60,
                        "keyword_coverage": 0.75, "difficulty_numeric": 2,
                        "attempt_number": len(_evals), "previous_score": _avg_score,
                        "average_previous_score": _avg_score, "topic_accuracy": _avg_score
                    })
                    _rec_out = recommendation_agent.process({
                        "target_role": _session.target_role,
                        "evaluation_history": [{"overall_score": _e.overall_score, "strengths": _e.strengths, "weaknesses": _e.weaknesses} for _e in _evals],
                        "question_history":   [{"topic": _q.topic, "difficulty": _q.difficulty} for _q in _session.questions],
                        "skill_gaps": []
                    })
                    _rec_obj = RecommendationOutput(**_rec_out["recommendations"])
                    int_repo.complete_session(_session.id, round(_avg_score, 1), _ml_res["readiness_score"], _ml_res["readiness_label"])
                    int_repo.save_recommendation(_session.id, _session.user_id, _rec_obj.overall_summary,
                        _rec_obj.strong_areas, _rec_obj.weak_areas, _rec_obj.learning_priorities, _rec_obj.practice_questions)
                    st.session_state.interview_completed = True
                    st.rerun()
            else:
                if _nc1.button("\u27a1 Next Question", type="primary", use_container_width=True):
                    _questions = int_repo.get_questions_for_session(_session.id)
                    _q_res = question_agent.process({
                        "session_id": _session.id, "target_role": _session.target_role,
                        "current_difficulty": _session.difficulty,
                        "current_question_index": _session.current_question_index,
                        "total_questions": _session.total_questions, "candidate_profile": {},
                        "job_profile": {"job_title": _session.target_role, "required_skills": ["System Design","RAG"]},
                        "skill_gaps": ["System Design"],
                        "previous_topics": [_q.topic for _q in _questions],
                        "question_history": [{"question": _q.question_text, "topic": _q.topic} for _q in _questions],
                        "answer_history": [_a.candidate_answer for _a in _session.answers],
                        "evaluation_history": [{"technical_accuracy": _e.technical_accuracy, "overall_score": _e.overall_score,
                                                "missing_concepts": _e.missing_concepts or [], "weaknesses": _e.weaknesses or []}
                                               for _e in _session.evaluations]
                    })
                    _next_q = InterviewQuestion(**_q_res["current_question"])
                    int_repo.add_question(_session.id, len(_questions)+1, _next_q.question, _next_q.topic,
                                         _next_q.difficulty, _next_q.question_type, _next_q.reason,
                                         _next_q.expected_concepts, _next_q.source_context)
                    st.session_state.current_question   = _next_q
                    st.session_state.current_evaluation = None
                    st.rerun()

elif page == PAGE_ANALYTICS:
    st.markdown("""<div class="page-header">
  <div class="page-title">Analytics &amp; ML Readiness</div>
  <div class="page-subtitle">Performance dimensions, score trajectory, and AI-predicted interview readiness</div>
</div>""", unsafe_allow_html=True)

    _ad = aggregate_user_analytics(user_id=st.session_state.user_id, db=db)

    if _ad["total_interviews"] == 0:
        empty_state("\U0001f4ca", "No interview data", "Complete at least one session to see analytics.")
    else:
        _a1, _a2, _a3, _a4, _a5 = st.columns(5)
        _a1.metric("Sessions",   _ad["total_interviews"])
        _a2.metric("Avg Score",  f"{_ad['average_overall_score']}%")
        _a3.metric("Tech Depth", f"{_ad['average_technical_score']}%")
        _a4.metric("Clarity",    f"{_ad['average_clarity_score']}%")
        _a5.metric("Readiness",  _ad["overall_readiness_label"])
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        _rc2, _sc2 = st.columns([3, 2])
        with _rc2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**Evaluation Dimensions**")
            _fr = create_radar_chart(
                _ad["average_technical_score"], _ad["average_relevance_score"],
                _ad["average_completeness_score"], _ad["average_clarity_score"],
                _ad["average_communication_score"]
            )
            _fr = apply_dark(_fr, 340)
            _fr.update_layout(polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(gridcolor="#1f2937", linecolor="#1f2937", tickfont=dict(color="#475569", size=9)),
                angularaxis=dict(gridcolor="#1f2937", linecolor="#1f2937")))
            st.plotly_chart(_fr, use_container_width=True, config=_PLOTLY_CFG)
            st.markdown('</div>', unsafe_allow_html=True)

        with _sc2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**Score Summary**")
            score_bar("Technical Accuracy", _ad["average_technical_score"])
            score_bar("Relevance",          _ad["average_relevance_score"])
            score_bar("Completeness",       _ad["average_completeness_score"])
            score_bar("Clarity",            _ad["average_clarity_score"])
            score_bar("Communication",      _ad["average_communication_score"])
            st.markdown('</div>', unsafe_allow_html=True)

            _rl2 = _ad["overall_readiness_label"]
            _rb  = {"Interview Ready":"#0d1f12","Almost Ready":"#1a1208","Needs Improvement":"#1c0a0a"}.get(_rl2,"#1a2035")
            st.markdown(
                f'<div class="card" style="background:{_rb};text-align:center;margin-top:0">'
                f'<div style="font-size:.65rem;color:#374151;margin-bottom:.3rem">ML PREDICTED READINESS</div>'
                f'{readiness_badge(_rl2)}'
                f'<div style="font-size:.68rem;color:#374151;margin-top:.3rem">Scikit-Learn classifier</div></div>',
                unsafe_allow_html=True)

        _sess2 = int_repo.list_sessions_for_user(st.session_state.user_id)
        if _sess2 and _sess2[0].recommendation:
            _rec2 = _sess2[0].recommendation
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**Personalized Study Roadmap**")
            st.markdown(f'<div style="color:#94a3b8;font-size:.875rem;margin-bottom:.6rem">{_rec2.overall_summary}</div>', unsafe_allow_html=True)
            if _rec2.learning_priorities:
                for _p2 in _rec2.learning_priorities:
                    st.markdown(
                        f'<div style="padding:.35rem 0;border-bottom:1px solid #1f2937;font-size:.875rem;color:#e2e8f0">'
                        f'<span style="color:#3b82f6;margin-right:.4rem">\u2192</span>{_p2}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif page == PAGE_HISTORY:
    st.markdown("""<div class="page-header">
  <div class="page-title">Interview History</div>
  <div class="page-subtitle">Complete log of all recorded sessions with Q&amp;A transcripts and evaluations</div>
</div>""", unsafe_allow_html=True)

    _hsess = int_repo.list_sessions_for_user(st.session_state.user_id)
    if not _hsess:
        empty_state("\U0001f4dc", "No sessions recorded", "Your history will appear here after completing a session.")
    else:
        for _hs in _hsess:
            _hsd = f"{_hs.overall_score:.1f}%" if _hs.overall_score else "In Progress"
            _hsb = '<span class="badge badge-green">Completed</span>' if _hs.status == "completed" else '<span class="badge badge-yellow">In Progress</span>'
            with st.expander(f"Session #{_hs.id}  \u2014  {_hs.target_role}  \u2014  {_hsd}"):
                st.markdown(f'{_hsb} &nbsp;Difficulty: &nbsp;{difficulty_badge(_hs.difficulty)} &nbsp;Readiness: &nbsp;{readiness_badge(_hs.readiness_label or "Not evaluated")}', unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)
                for _hq in _hs.questions:
                    st.markdown(
                        f'<div class="card-sm">'
                        f'<div style="font-size:.7rem;color:#374151;margin-bottom:.2rem">Q{_hq.question_number} \u00b7 {_hq.topic} \u00b7 {_hq.difficulty}</div>'
                        f'<div style="color:#e2e8f0;font-size:.875rem;font-weight:500">{_hq.question_text}</div>',
                        unsafe_allow_html=True)
                    if _hq.answer:
                        st.markdown(f'<div style="color:#64748b;font-size:.78rem;margin-top:.3rem">\U0001f4ac {_hq.answer.candidate_answer}</div>', unsafe_allow_html=True)
                        if _hq.answer.evaluation:
                            _hev = _hq.answer.evaluation
                            st.markdown(
                                f'<div style="margin-top:.3rem">Score: <strong style="color:#34d399">{_hev.overall_score:.1f}%</strong>'
                                f' &nbsp;\u00b7&nbsp; <span style="color:#64748b;font-size:.75rem">{_hev.feedback}</span></div>',
                                unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

elif page == PAGE_SETTINGS:
    st.markdown("""<div class="page-header">
  <div class="page-title">Settings &amp; System Status</div>
  <div class="page-subtitle">Runtime configuration, active components, and integration health</div>
</div>""", unsafe_allow_html=True)

    _s = get_settings()
    _sl, _sr = st.columns(2)
    with _sl:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**LLM & Embedding**")
        st.markdown(f'Provider: &nbsp;<span class="badge badge-blue">{_s.LLM_PROVIDER}</span>', unsafe_allow_html=True)
        st.markdown(f'Model: &nbsp;<code style="color:#93c5fd">{_s.EMBEDDING_MODEL}</code>', unsafe_allow_html=True)
        st.markdown(f'Vector Store: &nbsp;<span class="badge badge-blue">{_s.VECTOR_STORE_TYPE}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with _sr:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Database**")
        _dbu = _s.DATABASE_URL.split("///")[-1] if "///" in _s.DATABASE_URL else _s.DATABASE_URL
        st.markdown(f'<code style="color:#93c5fd">{_dbu}</code>', unsafe_allow_html=True)
        st.markdown(f'Similarity Threshold: &nbsp;<span class="badge badge-yellow">{_s.SIMILARITY_THRESHOLD}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**System Components**")
    _comps = [
        ("\U0001f9e0", "LangGraph Multi-Agent Pipeline",    "4 agents: Resume \u2192 Question \u2192 Evaluation \u2192 Recommendation"),
        ("\U0001f4da", "FAISS RAG Vector Store",            "31 grounded knowledge chunks across 7 domains"),
        ("\U0001f916", "LLM Service",                       f"Provider: {_s.LLM_PROVIDER} (LocalMockLLMClient active if no API key)"),
        ("\U0001f4ca", "Scikit-Learn Readiness Classifier", "3-class: Interview Ready / Almost Ready / Needs Improvement"),
        ("\U0001f5c4",  "SQLAlchemy ORM",                   "10 tables: sessions, questions, answers, evaluations, recommendations"),
        ("\u2699",      "NLP Parsers",                      "Resume parser + JD parser + semantic skill matcher"),
    ]
    for _ci, _cn, _cd in _comps:
        st.markdown(
            f'<div style="display:flex;align-items:flex-start;gap:.7rem;padding:.55rem 0;border-bottom:1px solid #1f2937">'
            f'<span style="font-size:1rem;margin-top:.1rem">{_ci}</span>'
            f'<div><div style="font-weight:600;color:#e2e8f0;font-size:.875rem">{_cn}</div>'
            f'<div style="font-size:.72rem;color:#475569">{_cd}</div></div>'
            f'<span class="badge badge-green" style="margin-left:auto;flex-shrink:0">Active</span></div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

db.close()
