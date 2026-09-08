# ANTIGRAVITY HANDOFF: AI INTERVIEW COACH

**Project Continuity & Architectural Handover Document**  
*Document Version: 1.0.0*  
*Last Updated: 2026-09-08*

---

## 1. Project Overview

**AI Interview Coach** is an enterprise-grade, adaptive technical interview assessment platform designed for machine learning, software engineering, and GenAI candidates. It combines:
- **Natural Language Processing (NLP)**: Resume entity extraction, Job Description (JD) requirement parsing, and semantic skill taxonomy categorization.
- **Retrieval-Augmented Generation (RAG)**: FAISS vector database indexed with 31 grounded engineering standards across 7 core technical domains using `sentence-transformers/all-MiniLM-L6-v2`.
- **Multi-Agent State Machine**: LangGraph directed acyclic graph orchestrating deterministic state transitions across Resume Agent, Question Agent, Evaluation Agent, and Recommendation Agent.
- **Predictive Machine Learning**: Scikit-Learn `RandomForestClassifier` trained to evaluate candidate readiness tiers (`Interview Ready`, `Almost Ready`, `Needs Improvement`).
- **Multimodal Subsystems**: Voice synthesis (TTS via gTTS/offline PCM chime), Speech-to-Text (STT via Whisper), and Computer Vision (posture & movement stability tracking via OpenCV & MediaPipe Pose).
- **Backend**: FastAPI RESTful backend backed by SQLAlchemy ORM and SQLite (`data/interview_coach.db`).
- **Primary Frontend (Target)**: Next.js 16 (React 19, TypeScript 5, Tailwind CSS 4, App Router).
- **Fallback Frontend (Preserved)**: Streamlit dark-mode application running on port 8501.

---

## 2. Current Architecture

```
                                  USER BROWSER
                         ┌──────────────┴──────────────┐
                         │                             │
                   Port 3000                      Port 8501
           ┌─────────────▼────────────┐   ┌────────────▼────────────┐
           │   Next.js 16 (Primary)   │   │   Streamlit (Fallback)   │
           │  React 19, TypeScript,   │   │   app/frontend/          │
           │   Tailwind CSS 4, App    │   │   streamlit_app.py       │
           │      Router UI           │   └────────────┬────────────┘
           └─────────────┬────────────┘                │
                         │                             │
                 HTTP Proxy (/api/py/*)                │ In-process
                         │                             │ Python imports
                         ▼                             │
           ┌───────────────────────────────────────────▼────────────┐
           │                FastAPI Backend (Port 8000)             │
           │                  app/backend/main.py                   │
           └───────┬────────────┬────────────┬────────────┬─────────┘
                   │            │            │            │
    ┌──────────────▼─────┐ ┌────▼─────┐ ┌────▼─────┐ ┌────▼──────────────┐
    │     NLP & Match    │ │ RAG Core │ │ Multi-   │ │ ML Readiness      │
    │ nlp/resume_parser  │ │ rag/     │ │ Agents   │ │ ml/predictor      │
    │ nlp/jd_parser      │ │ FAISS    │ │ LangGraph│ │ RandomForest      │
    │ nlp/matching       │ │ MiniLM   │ │ agents/  │ │ Scaler (.joblib)  │
    └──────────────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬──────────────┘
                   │            │            │            │
                   └────────────┼────────────┼────────────┘
                                │            │
                         ┌──────▼────────────▼──────┐
                         │   SQLite Database & ORM  │
                         │ data/interview_coach.db  │
                         │ database/models.py       │
                         └──────────────────────────┘
```

---

## 3. Current Migration Status

The project is undergoing a **frontend modernization** from Streamlit to Next.js + React + TypeScript.
- **Rule**: Zero changes to the AI/ML backend, agents, LangChain/LangGraph logic, RAG vector store, or database models.
- **Strategy**: The backend and the Streamlit frontend remain fully operational while Next.js is built out phase-by-phase. Next.js communicates strictly via the existing FastAPI REST API.

---

## 4. Completed Phases

### Phase 1: Next.js Project Initialization
- Scaffolded `frontend/` using `create-next-app` with Next.js 16.3.4, React 19.2.8, TypeScript 5, Tailwind CSS 4, and ESLint.
- Configured API proxy rewrites in `frontend/next.config.ts`:
  ```typescript
  async rewrites() {
    return [
      { source: "/api/py/:path*", destination: "http://127.0.0.1:8000/:path*" }
    ];
  }
  ```
- Created `frontend/.env.local` (`NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`).
- Installed `lucide-react`, `clsx`, and `tailwind-merge`.
- Verified development build and runtime startup on `http://localhost:3000`.

### Phase 2: Design System & Core Layout
- Defined enterprise dark theme in `frontend/app/globals.css` (`#0b0f17` background, `#111827` cards, `#1f2937` borders, `#3b82f6` accent).
- Created atomic UI components in `frontend/components/ui/`: `Button.tsx`, `Card.tsx`, `Badge.tsx`, `ProgressBar.tsx`, `EmptyState.tsx`.
- Created layout components in `frontend/components/layout/`:
  - `Sidebar.tsx`: SaaS grouped navigation (`OVERVIEW`, `PREPARE`, `INTERVIEW`, `INSIGHTS`, `SYSTEM`) with active route styling and candidate profile indicator.
  - `Header.tsx`: Real-time backend status polling (`/api/py/health` and `/api/py/knowledge-base`) with live pulse badge.
- Mounted root layout in `frontend/app/layout.tsx` with `suppressHydrationWarning`.
- Scaffolded all 8 primary application routes: `/resume`, `/jobs`, `/matching`, `/knowledge`, `/interview`, `/analytics`, `/history`, `/settings`.
- Completed **Phase 2 Verification Pass**:
  - Removed all hardcoded demo metrics from candidate workspace.
  - Connected candidate dashboard to `/api/py/analytics/1` and `/api/py/skill-gaps?user_id=1`.
  - Connected Sidebar profile widget to `/api/py/users/1`.
  - Resolved hydration warnings and deprecated form attributes.
  - Verified `npm run build` compiles with zero errors across all routes.

---

## 5. Current Phase

**Phase 2 Completed & Verified.** Awaiting user approval to proceed to Phase 3.

---

## 6. Next Phase

**Phase 3: Real Candidate Dashboard Integration**
- Transition `/` (Dashboard) into a fully functional candidate workspace.
- Implement live charts using Recharts (Score Trajectory line chart, Topic Mastery bar chart).
- Implement target job alignment circular gauge.
- Add live "Priority Focus Areas" based on real `weak_areas` from `/api/py/analytics/1`.
- Cleanly relocate or encapsulate the Phase 2 design-system specimen gallery into an auxiliary developer view.

---

## 7. Frontend Architecture (Next.js)

```
frontend/
├── app/
│   ├── layout.tsx             # Root layout with Sidebar, Header, suppressHydrationWarning
│   ├── globals.css            # Dark theme CSS variables, custom scrollbars
│   ├── page.tsx               # Candidate workspace + design system specimen
│   ├── resume/page.tsx        # Resume ingestion & profile viewer (UI scaffold)
│   ├── jobs/page.tsx          # Job description analyzer (UI scaffold)
│   ├── matching/page.tsx      # Match score & skill gap diagnostics (UI scaffold)
│   ├── knowledge/page.tsx     # FAISS vector store telemetry & RAG sandbox (UI scaffold)
│   ├── interview/page.tsx     # Adaptive interview session setup wizard (UI scaffold)
│   ├── analytics/page.tsx     # Multidimensional scores & ML readiness (UI scaffold)
│   ├── history/page.tsx       # Session audit trail & Q&A transcript cards (UI scaffold)
│   └── settings/page.tsx      # Microservice topology & AI parameters (UI scaffold)
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx        # Grouped nav, route highlighting, dynamic user widget
│   │   └── Header.tsx         # Breadcrumbs & live FastAPI/FAISS health telemetry
│   └── ui/
│       ├── Button.tsx         # Variants: primary, secondary, outline, ghost, danger
│       ├── Card.tsx           # Card, CardHeader, CardTitle, CardDescription, CardContent
│       ├── Badge.tsx          # Semantic badges: default, success, warning, danger, info, purple
│       ├── ProgressBar.tsx    # Dual-color animated gradient progress bar
│       └── EmptyState.tsx     # Centered zero-state placeholder with CTA slot
├── lib/
│   └── utils/
│       └── cn.ts              # clsx + twMerge utility function
├── .env.local                 # NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
├── next.config.ts             # API proxy rewrites to FastAPI
├── package.json               # Dependencies (Next 16, React 19, Lucide, Tailwind 4)
└── tsconfig.json              # TypeScript configuration
```

---

## 8. Backend Architecture (FastAPI)

- **Root File**: `app/backend/main.py`
- **Port**: `8000`
- **CORS**: `allow_origins=["*"]`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`.
- **Routers Registered**:
  - `health`: `/health`
  - `users`: `/users`
  - `resumes`: `/resumes`
  - `jobs`: `/jobs`
  - `matching`: `/matching`, `/skill-gaps`
  - `knowledge_base`: `/knowledge-base`
  - `interviews`: `/interviews`, `/recommendations`
  - `analytics`: `/analytics`
  - `voice`: `/voice`
  - `vision`: `/vision`

---

## 9. FastAPI API Contracts (Verified Actual Implementation)

| Method | Endpoint | Request Model | Response Model | Description |
|---|---|---|---|---|
| `GET` | `/health` | None | `HealthResponse` | DB connectivity, FAISS presence, LLM provider |
| `POST` | `/users` | `UserCreateRequest` (`name`, `email`, `target_role`) | `UserResponse` | Create or fetch candidate record |
| `GET` | `/users` | None | `List[UserResponse]` | List all registered users |
| `GET` | `/users/{user_id}` | Path: `user_id` | `UserResponse` | Get single user details |
| `POST` | `/resumes/upload` | Multipart: `file`, `user_id` (optional) | `ResumeUploadResponse` | Ingest PDF/DOCX/TXT, parse entity profile, save DB |
| `GET` | `/resumes/{resume_id}` | Path: `resume_id` | `ResumeUploadResponse` | Get parsed candidate profile |
| `POST` | `/jobs/analyze` | `JobAnalyzeRequest` (`job_description_text`, `title`, `user_id`) | `JobAnalyzeResponse` | Parse JD into requirements and seniority |
| `GET` | `/jobs/{jd_id}` | Path: `jd_id` | `JobAnalyzeResponse` | Get parsed job profile |
| `POST` | `/matching` | `MatchAnalysisRequest` (`resume_id`, `jd_id`, `raw_resume_text`, `raw_jd_text`, `user_id`) | `MatchAnalysisResponse` | Semantic alignment & prioritized skill gaps |
| `GET` | `/skill-gaps` | Query: `user_id` | `MatchAnalysisResponse` | Get latest stored skill gap analysis (404 if none) |
| `GET` | `/knowledge-base` | None | `KBStatusResponse` | Read index telemetry (`total_chunks`, `topics`) |
| `POST` | `/knowledge-base/query` | `KBQueryRequest` (`query`, `top_k`, `threshold`) | `KBQueryResponse` | RAG vector search across interview topics |
| `POST` | `/knowledge-base/ingest` | None | Dict | Rebuild FAISS index from markdown files |
| `POST` | `/interviews/start` | `InterviewStartRequest` (`user_id`, `target_role`, `difficulty`, `total_questions`) | `InterviewStartResponse` | Initialize session and generate Question 1 |
| `GET` | `/interviews/{session_id}/question` | Path: `session_id` | `InterviewQuestion` | Fetch current active question for session |
| `POST` | `/interviews/{session_id}/answer` | `AnswerSubmitRequest` (`answer_text`, `audio_path`) | `AnswerSubmitResponse` | Multi-criteria evaluation of candidate answer |
| `POST` | `/interviews/{session_id}/next` | Path: `session_id` | `NextQuestionResponse` | Generate next question OR finalize with recommendations & ML readiness |
| `GET` | `/interviews/{session_id}` | Path: `session_id` | `InterviewSessionSummary` | High-level session metadata |
| `GET` | `/recommendations/{session_id}` | Path: `session_id` | `RecommendationOutput` | Personalized 4-week preparation roadmap |
| `GET` | `/analytics/{user_id}` | Path: `user_id` | Dict | Aggregated user scores, topic mastery, history |
| `GET` | `/analytics/session/{session_id}` | Path: `session_id` | Dict | Detailed session audit trail and Q&A breakdown |
| `POST` | `/voice/speak` | `SpeakRequest` (`text`) | `SpeakResponse` | Text-to-speech audio synthesis |
| `POST` | `/voice/transcribe` | Multipart: `file` | `TranscribeResponse` | Speech-to-text transcription |
| `POST` | `/vision/analyze` | `VisionAnalyzeRequest` (`session_id`, `frame_count`, `fps`) | `VisionAnalyzeResponse` | Posture stability & movement magnitude |

---

## 10. LangChain / RAG Architecture

- **Vector Store**: FAISS (Index Flat IP on normalized embeddings).
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- **Index Directory**: `data/knowledge_base/faiss_index/`
  - `index.faiss`: Binary vector index.
  - `index.pkl`: Document chunks and metadata mapping.
  - `index_summary.json`: Summary metadata (31 chunks, 7 domains).
- **Similarity Threshold**: `0.25` (calibrated in `.env` and `config/settings.py`).
- **Retriever**: `rag.retriever.GroundedRetriever.build_grounded_context(query, top_k=4, threshold=0.25)` returns `{ context_text, sources, confidence_score, has_grounding }`.
- **Knowledge Domains (7)**: Data Structures & Algorithms, Generative AI & RAG, Machine Learning & AI, System Design, SQL & DBMS, Cloud & DevOps, Python & OOP.

---

## 11. LangGraph / Multi-Agent Architecture

- **State Definition**: `agents/state.py:InterviewState` (TypedDict holding session context, profiles, questions, answers, evaluations, readiness score, recommendations).
- **Orchestrator**: `agents/orchestrator.py:build_interview_graph()`
  - Node `resume_node`: Ingests resume/JD and calculates prioritized gaps.
  - Node `question_node`: Constructs grounded adaptive technical questions.
  - Node `evaluation_node`: Multi-criteria evaluation (Technical Accuracy, Relevance, Completeness, Clarity, Communication).
  - Node `difficulty_node`: Escalates to `Hard` after consecutive scores >= 80, drops to `Easy` if <= 50, otherwise `Medium`.
  - Node `recommendation_node`: Synthesizes session results into a 4-week roadmap.
  - Conditional Edge `should_continue`: Routes to `difficulty_node` if `idx < total`, else `recommendation_node`.
- **LLM Abstraction**: `llm/model.py:get_llm_client()`. Uses `GroqLLMClient` (Llama-3-70b-versatile) if `GROQ_API_KEY` is present, `OpenAILLMClient` if `OPENAI_API_KEY` is present, or `LocalMockLLMClient` (hermetic offline deterministic fallback).

---

## 12. Machine Learning Architecture

- **Classifier**: Scikit-Learn `RandomForestClassifier` (`ml/models/interview_readiness_rf.joblib`).
- **Scaler**: `StandardScaler` (`ml/models/readiness_scaler.joblib`).
- **Input Feature Vector (11 features)**:
  1. `technical_score` (0-100)
  2. `relevance_score` (0-100)
  3. `completeness_score` (0-100)
  4. `clarity_score` (0-100)
  5. `communication_score` (0-100)
  6. `answer_length` (words count)
  7. `keyword_coverage` (0.0-1.0)
  8. `difficulty_numeric` (1=Easy, 2=Medium, 3=Hard)
  9. `attempt_number`
  10. `previous_score` (0-100)
  11. `topic_accuracy` (0-100)
- **Output Labels**:
  - `Interview Ready` (Score >= 75)
  - `Almost Ready` (Score 55 - 74)
  - `Needs Improvement` (Score < 55)

---

## 13. Database Structure (SQLAlchemy / SQLite)

- **Database Path**: `data/interview_coach.db`
- **Engine**: SQLite with foreign key enforcement (`PRAGMA foreign_keys=ON`).
- **Tables (10)**:
  1. `users`: Candidate profiles (id, name, email, target_role, created_at).
  2. `resumes`: Uploaded resumes (id, user_id, filename, file_type, raw_text, parsed_profile JSON).
  3. `job_descriptions`: Job postings (id, user_id, title, raw_text, parsed_profile JSON).
  4. `skill_gap_analyses`: Alignment reports (id, user_id, overall_match_score, match_category, detailed_matches JSON, skill_gaps JSON).
  5. `interview_sessions`: Interview state (id, user_id, target_role, difficulty, status, total_questions, current_question_index, overall_score, readiness_score, readiness_label).
  6. `interview_questions`: Questions per session (id, session_id, question_number, question_text, topic, difficulty, expected_concepts JSON, source_context).
  7. `interview_answers`: Candidate responses (id, session_id, question_id, candidate_answer, audio_path).
  8. `answer_evaluations`: Multi-criteria scores (id, session_id, answer_id, technical_accuracy, relevance, completeness, clarity, communication, overall_score, strengths JSON, weaknesses JSON, missing_concepts JSON, feedback, next_difficulty).
  9. `recommendations`: Post-interview preparation roadmaps (id, session_id, user_id, overall_summary, strong_areas JSON, weak_areas JSON, learning_priorities JSON, practice_questions JSON).
  10. `vision_session_metrics`: Movement & posture stability data (id, session_id, avg_posture_stability, avg_movement_magnitude, movement_frequency, frame_count).

---

## 14. Voice & Computer Vision Architecture

### Voice Pipeline (`voice/`)
- **Speech-to-Text (`voice/speech_to_text.py`)**: `AudioTranscriber` uses `openai-whisper` (base model) with graceful fallback to heuristic transcript parsing.
- **Text-to-Speech (`voice/text_to_speech.py`)**: `AudioSynthesizer` uses Google TTS (`gTTS`) to generate MP3s; falls back offline to mathematical PCM WAV chime generator (`wave` + `struct`).
- **Audio Output Directory**: `data/temp_media/`

### Vision Pipeline (`vision/`)
- **Posture & Motion Extraction (`vision/feature_extraction.py`)**: `VisionAnalyticsPipeline` processes video frames with `MediaPipe Pose` (`mp.solutions.pose`).
  - Shoulder angle alignment calculation (`vision/posture.py`).
  - Head pose & center displacement stability (`vision/head_pose.py`).
  - Inter-frame motion magnitude & frequency (`vision/motion.py`).
  - **Ethical AI Guardrail**: Strictly tracks posture and movement stability; never attempts emotion detection or psychological inference.

---

## 15. Next.js Structure & Conventions

- **Next.js Version**: 16.3.4 (Turbopack)
- **React Version**: 19.2.8
- **TypeScript**: Strict typing enabled in `tsconfig.json`.
- **CSS**: Tailwind CSS 4 via `@import "tailwindcss";` in `globals.css`.
- **Important File Formatting Rule**: When writing `.tsx` / `.ts` / `.css` files on Windows using PowerShell, **never write a UTF-8 BOM (`\ufeff`)**. Use `[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))` or single-quoted heredocs `@' ... '@`.
- **Hydration**: `suppressHydrationWarning` must remain on `<html>` and `<body>` in `app/layout.tsx`.
- **Form Controls**: Use `defaultValue` instead of `selected` on `<select>` options.

---

## 16. Important Environment Variables (`.env` & `frontend/.env.local`)

```ini
# Backend .env
APP_NAME=AI Interview Coach
APP_ENV=development
DEBUG=True
HOST=127.0.0.1
PORT=8000
DATABASE_URL=sqlite:///./data/interview_coach.db
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3-70b-versatile
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
FAISS_INDEX_DIR=./data/knowledge_base/faiss_index
SIMILARITY_THRESHOLD=0.25
ML_MODEL_PATH=./ml/models/interview_readiness_rf.joblib
ML_SCALER_PATH=./ml/models/readiness_scaler.joblib
TEMP_MEDIA_DIR=./data/temp_media
UPLOAD_DIR=./data/uploads

# Frontend .env.local
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

---

## 17. Running Commands & Execution Environment

### Backend (FastAPI):
```powershell
python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000
```

### Next.js Frontend:
```powershell
cd frontend
npm.cmd run dev -- -p 3000
```
*(Use `npm.cmd` on Windows to bypass PowerShell script execution policy).*

### Fallback Streamlit Frontend:
```powershell
python -m streamlit run app/frontend/streamlit_app.py --server.port 8501 --server.headless true
```

### Running Test Suite:
```powershell
pytest -v
```

---

## 18. Ports

| Port | Service | Process / Technology |
|---|---|---|
| **8000** | Backend API | Uvicorn / FastAPI |
| **3000** | Primary Frontend | Next.js 16 / React 19 (Dev Server) |
| **8501** | Fallback Frontend | Streamlit Python Application |

---

## 19. Files Modified / Created During Migration

### Created in `frontend/`:
- `package.json`, `package-lock.json`, `tsconfig.json`, `next.config.ts`, `eslint.config.mjs`
- `.env.local`
- `app/globals.css`, `app/layout.tsx`, `app/page.tsx`
- `app/resume/page.tsx`, `app/jobs/page.tsx`, `app/matching/page.tsx`, `app/knowledge/page.tsx`
- `app/interview/page.tsx`, `app/analytics/page.tsx`, `app/history/page.tsx`, `app/settings/page.tsx`
- `components/layout/Sidebar.tsx`, `components/layout/Header.tsx`
- `components/ui/Button.tsx`, `Card.tsx`, `Badge.tsx`, `ProgressBar.tsx`, `EmptyState.tsx`
- `lib/utils/cn.ts`

### Untouched Backend:
- All files in `app/backend/`, `nlp/`, `rag/`, `agents/`, `ml/`, `voice/`, `vision/`, `database/`, and `config/` remain 100% unaltered.

---

## 20. Files That Must NOT Be Modified Unnecessarily

The following files contain calibrated, validated logic and must be preserved:
- `config/settings.py` & `.env` (`SIMILARITY_THRESHOLD=0.25` is calibrated).
- `nlp/resume_parser.py`, `nlp/jd_parser.py`, `nlp/matching.py`.
- `rag/retriever.py`, `rag/ingestion.py`, `rag/vector_store.py`.
- `agents/state.py`, `agents/orchestrator.py`, `agents/*_agent.py`.
- `ml/predictor.py` & `ml/models/*`.
- `database/models.py` & `database/repositories/*`.
- `app/frontend/streamlit_app.py` (remains active as a verified baseline fallback).

---

## 21. Known Backend API Gaps (To Be Addressed When Needed)

During the architecture audit, three non-breaking API extensions were identified:
1. **`GET /interviews`**: Currently, `routes/interviews.py` only has `GET /interviews/{session_id}`. A `GET /interviews?user_id=X` endpoint calling `InterviewRepository.list_sessions_for_user(user_id)` is needed for the Next.js `/history` tab.
2. **Audio File URL**: `POST /voice/speak` returns a local disk path (`data/temp_media/...`). Serving this via `StaticFiles` or a `FileResponse` endpoint will be required for in-browser audio playback in Phase 12.
3. **Webcam Frame Burst Ingestion**: `routes/vision.py` currently tests blank frames. An endpoint accepting JPEG frames or a WebM blob will be needed in Phase 13.

---

## 22. Design System Decisions

- **Color Harmony**:
  - Background: `#0b0f17` (Deep Obsidian).
  - Cards: `#111827` (Rich Slate) with `1px solid #1f2937` (Charcoal).
  - Accent: `#3b82f6` (Electric Blue).
  - Success: `#10b981` (Emerald).
  - Warning: `#f59e0b` (Amber).
  - Danger: `#ef4444` (Rose/Crimson).
- **Component Rules**:
  - Compact KPI metrics with semantic status chips.
  - Zero hardcoded candidate analytics; real data or explicit empty states only.
  - Test/specimen UI elements must always carry an explicit "UI Specimen" badge.
  - Responsive layout: Fixed collapsible sidebar on desktop, responsive main content column.

---

## 23. Testing Status

- **Pytest Suite**: 25/25 tests passing (`tests/test_nlp.py`, `tests/test_rag.py`, `tests/test_agents.py`, `tests/test_ml.py`, `tests/test_api.py`).
- **End-to-End Validation**: E2E pipeline script executed and passing all 6 phases.
- **Next.js Production Build**: `npm run build` compiles with 0 errors across all 10 routes.
- **Browser QA**: Verified via Playwright automation; clean console output with zero hydration errors.

---

## 24. Docker Status

- `Dockerfile` & `docker-compose.yml` are currently configured to build the Python environment and run:
  - `backend`: `uvicorn app.backend.main:app --port 8000`
  - `frontend`: `streamlit run app/frontend/streamlit_app.py --port 8501`
- In Phase 14, `docker-compose.yml` will be updated to include the Next.js multi-stage production container on port 3000 while retaining port 8501 for fallback.

---

## 25. Exact Instructions for Continuing the Migration

When resuming the session to proceed with **Phase 3 (Dashboard Integration)**:

1. **Verify Daemons**: Ensure FastAPI is running on `8000` and Next.js is running on `3000`.
   - FastAPI: `python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000`
   - Next.js: `cd frontend; npm.cmd run dev -- -p 3000`
2. **Implement Phase 3 Scope**:
   - Install `recharts` in `frontend/`: `npm.cmd install recharts`.
   - In `frontend/app/page.tsx`, replace specimen components with real Recharts visualizations:
     - Score Trajectory Chart (Line/Area chart bound to `analytics.score_history`).
     - Topic Mastery Chart (Bar chart bound to `analytics.topic_performance`).
     - Real Match Gauge bound to `skillGap.overall_match_score`.
     - Priority Focus Areas card bound to `analytics.weak_areas`.
3. **Verify Build**: Run `npm.cmd run build` inside `frontend/` to ensure TypeScript types and Next.js Turbopack compilation succeed.
4. **Validate Visually**: Check the browser at `http://localhost:3000/` and verify that when data is empty, polished empty states appear; when data exists, real charts render.
5. **Stop & Report**: Summarize changes to the user and request approval before moving to Phase 4 (Resume & JD).

---

## HANDOFF SUMMARY

- **CURRENT STATUS**: Phase 1 & Phase 2 complete and verified. Next.js 16 app live and functional. Backend untouched.
- **CURRENT PHASE**: Phase 2 (Completed & Verified).
- **NEXT ACTION**: Awaiting user approval to begin Phase 3 (Real Candidate Dashboard Integration with Recharts).
- **BLOCKERS**: None. All dependencies installed, ports active, and API proxy verified.
- **LAST VERIFIED**: 2026-09-08 (Next.js 16 Turbopack build: 0 errors; HTTP status: 200 OK across all routes).