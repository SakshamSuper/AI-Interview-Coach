# AI Interview Coach — Project Overview

## 1. Executive Summary
The **AI Interview Coach** is an adaptive, multi-agent technical interview preparation platform designed to bridge the preparation-to-performance gap for software engineering, data science, and machine learning candidates. Powered by an orchestrated **LangGraph** state machine, **FAISS** vector retrieval-augmented generation (RAG), and a **Scikit-Learn** readiness classifier, the platform transforms static resume analysis and isolated leetcode drills into realistic, interactive technical interviews.

## 2. Problem Statement
Technical interviewing in modern technology hiring faces severe limitations:
- **Generic Preparation**: Candidates drill standardized algorithm puzzles that fail to reflect role-specific system architectures or company-specific technology stacks.
- **Disconnected Resume & Role Alignment**: Candidates lack objective visibility into how applicant tracking systems (ATS) and hiring managers parse their resumes against job descriptions (JDs).
- **Subjective and Delayed Feedback**: Mock interviews with peers lack rigorous evaluation across objective dimensions (technical depth, communication clarity, problem-solving reasoning).
- **Static Linear Flows**: Traditional AI interview chatbots use unconstrained prompt loops prone to hallucinations, repeating questions, or failing to probe deeper when candidates omit critical concepts.

## 3. Motivation
To create an end-to-end, deterministic interview training system that:
1. Grounds questions in verified domain knowledge bases rather than ungrounded LLM memory.
2. Models the interview process as an explicit state machine with guaranteed state transitions.
3. Quantifies candidate readiness through empirical machine learning rather than arbitrary numerical heuristics.
4. Delivers actionable feedback, ATS compatibility scoring, and tailored 4-week preparation roadmaps.

## 4. Proposed Solution
An integrated full-stack platform providing:
1. **Resume & JD NLP Parsing**: Rule-based regex and entity extraction isolating skills, experience tiers, and project architectures.
2. **Hybrid Fit & ATS Scoring**: Multi-component compatibility scoring evaluating keyword coverage, required skills, semantic similarity, and experience alignment.
3. **Domain-Grounded RAG**: A FAISS vector store indexing curated software architecture, OOP, distributed systems, and ML engineering standards.
4. **Adaptive Multi-Agent LangGraph Machine**: Deterministic orchestration separating resume ingestion, question generation, answer evaluation, and roadmap synthesis.
5. **Multi-Axis Rubric Evaluation**: Scoring answers on a 0–100 scale across Technical Accuracy, Relevance, Completeness, Clarity, and Communication.
6. **ML Interview Readiness Classifier**: Scikit-Learn model predicting empirical readiness tiers (`Interview Ready`, `Almost Ready`, `Needs Improvement`).
7. **Production User Authentication**: NextAuth.js v5 with Google OAuth, HttpOnly JWT cookies, and strict multi-tenant database isolation.

## 5. Target Users
- **Junior to Senior Software Engineers**: Preparing for backend, distributed systems, and core systems roles.
- **Machine Learning & AI Engineers**: Preparing for deep learning, MLOps, model deployment, and RAG architecture interviews.
- **Data Scientists & Quantitative Analysts**: Preparing for statistical modeling, time series, and pipeline interviews.
- **Career Changers & University Graduates**: Seeking objective ATS resume benchmarking and structured interview simulations.

## 6. Core Workflow
```
[User Login (Google OAuth)]
       ↓
[Upload Resume (PDF)] ──> [Extract Skills & 2 Projects]
       ↓
[Input Job Description] ──> [ATS Compatibility (0-100) & Skill Gap Analysis]
       ↓
[Configure Interview (Role, Difficulty, Questions)]
       ↓
[LangGraph State Machine Execution]
   ├── Node 1: QuestionAgent (FAISS Grounding + Follow-Up Adaptation)
   ├── Candidate Input (Text or Whisper Voice STT)
   ├── Node 2: EvaluationAgent (5-Axis Scoring & Remedial Diagnostics)
   └── Loop until Total Questions Reached
       ↓
[Node 3: RecommendationAgent (Aggregated Score + Scikit-Learn ML Readiness + 4-Week Roadmap)]
       ↓
[Analytics Dashboard & SQLite Session History]
```

## 7. Major Modules & Directory Structure
- `app/backend/`: FastAPI application server and REST route controllers (`auth`, `resumes`, `jobs`, `matching`, `ats`, `interviews`, `analytics`, `voice`).
- `nlp/`: Document extraction, preprocessing, resume parser, JD parser, and hybrid skill gap matcher.
- `rag/`: Document ingestion, chunking, sentence embeddings, and FAISS vector retriever (`knowledge_base.py`).
- `agents/`: LangGraph multi-agent state graph (`ResumeAgent`, `QuestionAgent`, `EvaluationAgent`, `RecommendationAgent`, `orchestrator.py`).
- `llm/`: LLM client abstraction (OpenAI, Groq, and hermetic `LocalMockLLMClient`), prompt templates, and Pydantic JSON parser.
- `ml/`: Synthetic dataset generation, Scikit-Learn classifier training (`ReadinessPredictor`), feature engineering, and inference.
- `voice/`: Local OpenAI Whisper speech-to-text transcriber (`transcriber.py`).
- `database/`: SQLAlchemy ORM models (`User`, `Resume`, `JobDescription`, `SkillGapAnalysis`, `InterviewSession`, `InterviewQuestion`, `InterviewEvaluation`).
- `frontend/`: Next.js 16 (App Router), React 19, Tailwind CSS, TypeScript, Recharts, Lucide icons, and NextAuth.js v5.

## 8. Technology Stack Summary
| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 16.3.4, React 19, TypeScript, Tailwind CSS, Recharts |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2, Python 3.14 |
| **Orchestration** | LangGraph, LangChain Core |
| **Vector Database** | FAISS (Facebook AI Similarity Search), SentenceTransformers / TF-IDF |
| **Machine Learning** | Scikit-Learn (LogisticRegression, RandomForest), NumPy, Pandas |
| **Speech-to-Text** | OpenAI Whisper (Local inference via CPU/CUDA) |
| **Authentication** | NextAuth.js v5, Google OAuth 2.0, Jose JWT |
| **Persistence** | SQLite, SQLAlchemy 2.0 ORM |
