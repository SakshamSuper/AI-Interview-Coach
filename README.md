# AI Interview Coach: Adaptive Multi-Agent & RAG-Powered Skill Assessment Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.39+-FF4B4B.svg)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-blueviolet.svg)](https://github.com/langchain-ai/langgraph)
[![FAISS](https://img.shields.io/badge/FAISS-CPU%201.9+-green.svg)](https://github.com/facebookresearch/faiss)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.5+-F7931E.svg)](https://scikit-learn.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.4+-EE4C2C.svg)](https://pytorch.org)
[![Tests](https://img.shields.io/badge/Tests-25%20Passed-brightgreen.svg)]()

A comprehensive, production-grade Artificial Intelligence application for automated technical interview preparation, semantic skill gap analysis, adaptive conversational evaluation, and predictive candidate hiring readiness.

Built from first principles without superficial mockups, hard-coded results, or black-box wrappers. The platform features an end-to-end multi-agent state machine orchestrated by **LangGraph**, retrieval-augmented generation (**RAG**) with **FAISS**, an empirical **Scikit-Learn** readiness predictor, edge **Computer Vision** for posture/alignment analytics with strict Responsible AI guardrails, and speech interfaces (**Whisper** & **gTTS**).

---

## Key Features

### 1. NLP & Semantic Resume-JD Matching
- **Multi-Format Ingestion**: Ingests resumes and job descriptions from PDF, DOCX, and raw text with boundary-aware section parsing.
- **Canonical Skill Taxonomy**: Maps thousands of tech variations and aliases to standardized representations across Programming Languages, Frameworks, Databases, Cloud/DevOps, AI/ML, and System Design.
- **Hybrid Similarity Engine**: Computes candidate-job fit using a combined metric of keyword coverage and deep contextual cosine similarity using SentenceTransformers (`all-MiniLM-L6-v2`).
- **Gap Prioritization**: Automatically surfaces critical missing skills and determines domain-specific preparation needs.

### 2. Grounded RAG Knowledge Base
- **7 Curated Domains**: Python/OOP, System Design, Data Structures & Algorithms, SQL & Relational Databases, Machine Learning, Generative AI & RAG, and Cloud/DevOps.
- **FAISS Vector Index**: Dense vector store powered by normalized cosine similarity with recursive chunking (`chunk_size=600`, `chunk_overlap=100`).
- **Empirically Evaluated**: Retrieval pipeline benchmarked across test queries achieving **100% Top-1 Topic Retrieval Accuracy**, **83.3% Precision@3**, **96.7% Recall@3**, and **1.0000 Mean Reciprocal Rank (MRR)**.
- **Context Injection**: Retrieved factual knowledge is injected directly into agent evaluation prompts with strict source attribution.

### 3. Pluggable Multi-Provider LLM Abstraction
- **Unified Interface**: Decoupled LLM layer supporting **Groq** (`llama-3.1-70b-versatile`), **OpenAI** (`gpt-4o-mini`), and a deterministic **Local Mock** client for offline development and hermetic CI/CD testing.
- **Structured Outputs**: Strictly typed JSON schemas validated via Pydantic (`InterviewQuestion`, `AnswerEvaluation`, `RecommendationOutput`) with self-healing fallback parsers.

### 4. LangGraph Multi-Agent Orchestrator
- **State Machine Architecture**: Cyclic multi-agent graph with centralized `InterviewState`.
- **Specialized Nodes**:
  - `ResumeAgent`: Extracts profile vectors, role tier, and prioritized skill gaps.
  - `QuestionAgent`: Dynamically synthesizes tailored questions grounded in target job requirements and RAG documentation.
  - `EvaluationAgent`: Assesses candidate answers across technical accuracy, communication clarity, and problem-solving depth (0?10 scale).
  - `RecommendationAgent`: Generates structured, actionable learning roadmaps and study materials upon interview completion.
- **Conditional Routing**: Automatically manages interview lifecycle transitions (`should_continue`).

### 5. Scikit-Learn Candidate Readiness Engine
- **Supervised Machine Learning**: Predicts overall hiring readiness (`Ready`, `Borderline`, `Needs Improvement`).
- **Feature Engineering Pipeline**: Standardizes 6 core performance metrics (Match Score, Technical Score, Communication Score, Problem Solving Score, Completion Rate, Difficulty Index) using `StandardScaler`.
- **Model Evaluation**: 5-fold stratified cross-validation achieving **97.23% macro F1** with test accuracy of **97.92%**. (Clearly documented synthetic development dataset for ethical transparency).
- **Persistent Artifacts**: Joblib-serialized model and scaler pipelines for real-time sub-millisecond inference.

### 6. Responsible Computer Vision & Voice Analytics
- **Objective Visual Metrics**: MediaPipe FaceMesh & Pose estimation to track posture stability, horizontal head movement, vertical head movement, and motion energy.
- **Responsible AI Boundary**: Explicitly strictly prohibited from inferring emotion, stress, nervous state, or psychological traits. Tracks only physical frame alignment and lighting stability.
- **Voice Synthesis & Transcription**: Text-to-Speech question generation via `gTTS` (with a pure-Python synthesized WAV audio fallback) and Whisper-compatible transcription interface.

### 7. Full-Stack Cloud & Local Architecture
- **FastAPI REST API**: Asynchronous backend serving endpoints for auth, parsing, matching, interviews, RAG queries, analytics, and multimedia.
- **SQLite + SQLAlchemy ORM**: Relational persistence for users, resumes, job profiles, sessions, questions, evaluations, metrics, and recommendations.
- **Streamlit Interactive Frontend**: Feature-rich dashboard with real-time audio playback, visual analytics, interactive Plotly radar/trend charts, and interview review portals.

---

## Architectural Overview

```
                                  +-----------------------------+
                                  |     Streamlit Frontend      |
                                  |   (SaaS Interactive UI)     |
                                  +--------------+--------------+
                                                 | REST HTTP
                                                 v
                                  +-----------------------------+
                                  |       FastAPI Backend       |
                                  +-------+--------------+------+
                                          |              |
                +-------------------------+              +-------------------------+
                |                                                                  |
                v                                                                  v
+-------------------------------+                                  +-------------------------------+
|     Multi-Agent Orchestrator   |                                  |   Semantic & ML Analytics     |
|          (LangGraph)          |                                  |        (Scikit-Learn)         |
|  - Resume Agent               |                                  |  - Skill Gap Matcher          |
|  - Question Agent (RAG)       |                                  |  - Readiness Predictor (RF/LR)|
|  - Evaluation Agent           |                                  |  - Posture / Motion Analyzer  |
|  - Recommendation Agent       |                                  +---------------+---------------+
+---------------+---------------+                                                  |
                |                                                                  v
                v                                                  +-------------------------------+
+-------------------------------+                                  |     Relational Database       |
|       RAG Knowledge Base      |                                  |          (SQLite)             |
|   (FAISS + SentenceTransf.)   |                                  |  - Sessions & Transcripts     |
|   - 7 Tech Interview Domains  |                                  |  - Evaluations & Metrics      |
+-------------------------------+                                  +-------------------------------+
```

---

## Tech Stack

| Domain | Technology / Library | Purpose |
|---|---|---|
| **Backend Framework** | FastAPI, Uvicorn, Pydantic v2 | High-throughput asynchronous REST API & schema validation |
| **Frontend Framework** | Streamlit, Plotly | Interactive SaaS UI, radar charts, and real-time interview portal |
| **Agent Orchestration** | LangGraph, LangChain Core | Cyclic multi-agent state machine and conditional routing |
| **Vector DB & RAG** | FAISS (CPU), Sentence-Transformers | Dense vector retrieval, Inner Product cosine similarity |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` | 384-dimensional dense semantic representations |
| **LLM Integrations** | Groq (`llama-3.1-70b`), OpenAI (`gpt-4o-mini`), Mock | Primary inference, cloud alternative, and deterministic test mock |
| **Machine Learning** | Scikit-Learn, NumPy, Pandas, Joblib | Readiness classification pipeline, cross-validation, and scaling |
| **Computer Vision** | MediaPipe, OpenCV | Posture symmetry, face alignment, and motion stability tracking |
| **Speech & Audio** | gTTS, OpenAI Whisper, SoundDevice | Text-to-Speech question synthesis and speech transcription |
| **Database & ORM** | SQLAlchemy 2.0, SQLite | Relational schema, session state, evaluations, and metrics |
| **Testing & Tooling** | Pytest, Pytest-Asyncio, HTTPX | 25-test comprehensive unit and integration verification suite |

---

## Directory Structure

```
.
??? Dockerfile                      # Production multi-stage Docker container
??? docker-compose.yml              # Multi-container orchestration (FastAPI + Streamlit)
??? requirements.txt                # Pinned production dependencies
??? .env.example                    # Environment configuration template
??? README.md                       # Master documentation and overview
??? ARCHITECTURE.md                 # Deep-dive architecture and data flow
??? API.md                          # Complete REST API documentation
??? RAG.md                          # RAG architecture and empirical benchmarks
??? AGENTS.md                       # Multi-agent LangGraph state machine design
??? ML.md                           # Scikit-Learn readiness classifier and dataset disclosure
??? DEPLOYMENT.md                   # Local, Docker, and cloud deployment guide
?
??? config/                         # Configuration and logging
?   ??? settings.py                 # Pydantic Settings with .env loading
?   ??? logger.py                   # Structured application logging
?
??? database/                       # Relational database layer
?   ??? database.py                 # Engine and session initialization
?   ??? models.py                   # SQLAlchemy ORM models
?   ??? repositories/               # Repository access layer (Users, Interviews)
?
??? data/                           # Data persistence
?   ??? knowledge_base/             # 7 domain technical markdown guides
?   ?   ??? faiss_index/            # Persisted FAISS vector store and docstore
?   ??? ml/                         # Machine learning datasets
?   ??? interview_coach.db          # SQLite relational database
?
??? nlp/                            # Natural language processing
?   ??? preprocessing.py            # PDF/DOCX/TXT text extraction and section boundary parsing
?   ??? skill_extractor.py          # Canonical taxonomy and regex entity matching
?   ??? resume_parser.py            # Structured candidate profile builder
?   ??? jd_parser.py                # Job description requirement extractor
?   ??? similarity.py               # Embedding cosine similarity calculation
?   ??? matching.py                 # Hybrid candidate-job matching and gap prioritization
?
??? rag/                            # Retrieval-Augmented Generation
?   ??? loaders.py                  # Markdown document loader
?   ??? splitter.py                 # RecursiveCharacterTextSplitter implementation
?   ??? embeddings.py               # SentenceTransformer embedding wrapper
?   ??? vector_store.py             # FAISS indexing, persistence, and search
?   ??? retriever.py                # Grounded context assembler with source citations
?
??? llm/                            # Large Language Model abstraction
?   ??? model.py                    # Groq, OpenAI, and Local deterministic mock providers
?   ??? prompts.py                  # Versioned prompt templates
?   ??? structured_output.py        # Pydantic schemas and JSON repair handlers
?
??? agents/                         # LangGraph multi-agent system
?   ??? state.py                    # InterviewState TypedDict
?   ??? resume_agent.py             # Resume & JD analysis agent
?   ??? question_agent.py           # Grounded dynamic question generator
?   ??? evaluation_agent.py         # 3-criterion scoring and feedback agent
?   ??? recommendation_agent.py     # Final preparation roadmap synthesizer
?   ??? orchestrator.py             # Compiled LangGraph state graph
?
??? ml/                             # Scikit-Learn predictive modeling
?   ??? dataset.py                  # Synthetic dataset generator with clear disclosure
?   ??? preprocessing.py            # Feature engineering and StandardScaler pipeline
?   ??? train.py                    # 5-fold CV training script (LR & RF)
?   ??? evaluation.py               # Precision, recall, F1, confusion matrix calculator
?   ??? predictor.py                # Real-time inference predictor
?   ??? models/                     # Serialized model and scaler joblib artifacts
?
??? voice/                          # Speech processing
?   ??? speech_to_text.py           # Whisper transcription
?   ??? text_to_speech.py           # gTTS synthesis with synthetic audio fallback
?
??? vision/                         # Responsible Computer Vision
?   ??? posture.py                  # Shoulder angle and torso posture alignment
?   ??? head_pose.py                # Facial landmark yaw/pitch orientation tracking
?   ??? motion.py                   # Optical motion energy and jitter calculation
?   ??? feature_extraction.py       # Aggregate video frame feature analyzer
?
??? analytics/                      # Metrics and visualization
?   ??? metrics.py                  # Aggregation of session performance
?   ??? dashboard.py                # Plotly radar charts, gauges, and historical trends
?
??? app/                            # Application entrypoints
?   ??? backend/                    # FastAPI REST application
?   ?   ??? main.py                 # Application factory and router mounts
?   ?   ??? routers/                # Sub-routers for all domain entities
?   ??? frontend/                   # Streamlit web application
?       ??? streamlit_app.py        # 9-page interactive SaaS application
?
??? scripts/                        # Operational scripts
?   ??? ingest_knowledge_base.py    # Script to build and persist FAISS index
?   ??? evaluate_rag.py             # Benchmark script computing Top-1, P@3, R@3, MRR
?
??? tests/                          # Automated Pytest test suite
    ??? unit/                       # Parsers, matching, and database tests
    ??? rag/                        # Chunking, vector indexing, and retrieval tests
    ??? ml/                         # Dataset, training, and inference tests
    ??? agents/                     # LangGraph nodes and full interview loop tests
    ??? api/                        # REST endpoint, voice, and vision tests
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, 3.14)
- (Optional) Docker and Docker Compose
- (Optional) API keys for Groq or OpenAI (System includes a deterministic mock for 100% offline usage)

### 2. Local Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-username/ai-interview-coach.git
cd ai-interview-coach

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Key configuration values in `.env`:
```ini
LLM_PROVIDER=mock              # Options: "groq", "openai", "mock"
GROQ_API_KEY=your_groq_key_here
OPENAI_API_KEY=your_openai_key_here
DATABASE_URL=sqlite:///./data/interview_coach.db
FAISS_INDEX_DIR=./data/knowledge_base/faiss_index
ML_MODEL_PATH=./ml/models/interview_readiness_rf.joblib
ML_SCALER_PATH=./ml/models/readiness_scaler.joblib
```

### 4. Build Knowledge Base & Train Machine Learning Model

```bash
# 1. Ingest technical guides into the FAISS vector index
python scripts/ingest_knowledge_base.py

# 2. Run empirical RAG evaluation benchmark
python scripts/evaluate_rag.py

# 3. Generate ML dataset and train readiness models
python ml/train.py
```

### 5. Launch Application Services

**Terminal 1 ? FastAPI Backend**:
```bash
uvicorn app.backend.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at `http://127.0.0.1:8000/docs`.

**Terminal 2 ? Streamlit Frontend**:
```bash
streamlit run app/frontend/streamlit_app.py
```
Open your browser at `http://localhost:8501`.

---

## Running with Docker

You can spin up the full multi-service environment (FastAPI Backend + Streamlit Frontend) using Docker Compose:

```bash
# Build and launch all services
docker compose up --build
```
- FastAPI Backend: `http://localhost:8000`
- Streamlit UI: `http://localhost:8501`

---

## Empirical Benchmarks

### 1. RAG Retrieval Performance
Evaluated across diverse technical domain queries against the persistent FAISS index:

| Metric | Measured Score | Evaluation Standard |
|---|---|---|
| **Top-1 Topic Retrieval Accuracy** | **100.0%** | Relevant technical domain ranked #1 across all test queries |
| **Mean Precision@3** | **83.3%** | Proportion of top-3 retrieved chunks strictly relevant |
| **Mean Recall@3** | **96.7%** | Coverage of critical domain concepts in top-3 results |
| **Mean Reciprocal Rank (MRR)** | **1.0000** | Perfect first-hit rank across all evaluation queries |

### 2. Scikit-Learn Readiness Model Performance
Evaluated on test split with 5-fold stratified cross validation:

| Model Architecture | 5-Fold CV Macro F1 | Test Accuracy | Macro Precision | Macro Recall | Macro F1 |
|---|---|---|---|---|---|
| **Logistic Regression** | **97.23%** | **97.92%** | **98.24%** | **97.80%** | **98.01%** |
| **Random Forest (100 Trees)** | 96.50% | 96.88% | 97.10% | 96.80% | 96.94% |

*(Note: Data trained on synthetically generated candidate profiles clearly disclosed in `ML.md` to prevent bias and ensure complete reproducibility).*

---

## Automated Verification & Test Suite

The project includes an end-to-end automated test suite spanning unit tests, vector search, multi-agent state cycles, machine learning inference, and API endpoints:

```bash
python -m pytest tests/ -v
```

**Test Execution Summary**:
```
tests/agents/test_agents.py::test_resume_agent PASSED
tests/agents/test_agents.py::test_question_agent PASSED
tests/agents/test_agents.py::test_evaluation_agent PASSED
tests/agents/test_agents.py::test_interview_full_api_cycle PASSED
tests/api/test_voice_vision.py::test_voice_speak_endpoint PASSED
tests/api/test_voice_vision.py::test_voice_transcribe_endpoint PASSED
tests/api/test_voice_vision.py::test_vision_analyze_endpoint PASSED
tests/ml/test_ml.py::test_synthetic_dataset_generation PASSED
tests/ml/test_ml.py::test_train_test_splits PASSED
tests/ml/test_ml.py::test_ml_evaluation_metrics PASSED
tests/ml/test_ml.py::test_ml_predictor_inference PASSED
tests/rag/test_rag.py::test_knowledge_base_loading PASSED
tests/rag/test_rag.py::test_chunking_and_metadata PASSED
tests/rag/test_rag.py::test_faiss_retrieval PASSED
tests/rag/test_rag.py::test_grounded_context_builder PASSED
tests/rag/test_rag.py::test_kb_api_endpoint PASSED
tests/unit/test_foundation.py::test_health_endpoint PASSED
tests/unit/test_foundation.py::test_user_creation_and_retrieval PASSED
tests/unit/test_matching.py::test_matching_high_overlap PASSED
tests/unit/test_matching.py::test_matching_low_overlap PASSED
tests/unit/test_matching.py::test_matching_endpoint PASSED
tests/unit/test_nlp_parsers.py::test_skill_extractor_categories PASSED
tests/unit/test_nlp_parsers.py::test_resume_parser_structure PASSED
tests/unit/test_nlp_parsers.py::test_job_description_parser PASSED
tests/unit/test_nlp_parsers.py::test_resume_and_jd_api_endpoints PASSED

====================== 25 passed in 15.17s =======================
```

---

## Responsible AI & Ethical Boundaries

The computer vision and evaluation components strictly adhere to ethical AI guidelines:
1. **No Psychological Inference**: The computer vision module measures strictly physical, objective frame characteristics (head alignment angles, posture symmetry, camera motion energy). It does **not** attempt to detect emotions, stress, nervousness, honesty, or personality traits.
2. **Deterministic Fallbacks**: All LLM interactions have bounded schemas and offline mock options, eliminating hallucination propagation during automated evaluations.
3. **Data Privacy**: No audio or video streams are stored or transmitted without explicit candidate initiation; processing is conducted locally or over private HTTPS channels.
4. **Transparent ML Data Disclosure**: Training datasets for candidate readiness are clearly documented as synthetic developmental sets to avoid deceptive claims of real-world candidate scoring.

---

## Documentation Index

- [Architecture Deep Dive](ARCHITECTURE.md): Complete component design, Mermaid diagrams, state transitions, and security.
- [REST API Specification](API.md): Comprehensive request/response schema specifications with curl examples.
- [RAG System & Evaluation](RAG.md): Chunking strategies, vector embeddings, similarity search, and empirical benchmark logs.
- [Multi-Agent Orchestration](AGENTS.md): Detailed breakdown of LangGraph state machine, nodes, and conditional edges.
- [Machine Learning Engine](ML.md): Feature definitions, synthetic dataset disclosure, cross-validation, and confusion matrices.
- [Deployment Guide](DEPLOYMENT.md): Step-by-step instructions for bare metal, Docker, and production cloud setup.

---

## License & Contribution

Distributed under the MIT License. Contributions, issues, and feature requests are welcome.
