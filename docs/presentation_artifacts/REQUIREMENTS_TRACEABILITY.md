# AI Interview Coach — Requirements Traceability Matrix

| ID | Requirement Specification | Implementation Component | Evidence File / Route | Verification Test | Status |
|:---:|---|---|---|---|:---:|
| **REQ-01** | Multi-format resume parsing (PDF, DOCX, TXT) | `nlp.resume_parser.ResumeParser` | `nlp/resume_parser.py` | `tests/unit/test_nlp_parsers.py::test_resume_parser_structure` | **VERIFIED** |
| **REQ-02** | Multiple project boundary extraction | `nlp.resume_parser` line classifier | `nlp/resume_parser.py` | `tests/unit/test_nlp_parsers.py::test_multiple_project_extraction` | **VERIFIED** |
| **REQ-03** | Job Description requirement & seniority parsing | `nlp.jd_parser.JobDescriptionParser` | `nlp/jd_parser.py` | `tests/unit/test_nlp_parsers.py::test_job_description_parser` | **VERIFIED** |
| **REQ-04** | Hybrid skill gap matching & categorization | `nlp.matching.MatchingEngine` | `nlp/matching.py` | `tests/unit/test_matching.py::test_matching_high_overlap` | **VERIFIED** |
| **REQ-05** | 6-Component ATS compatibility scoring | `app.backend.routes.ats` | `app/backend/routes/ats.py` | `tests/api/test_ats.py::TestATSScore::test_all_component_scores_in_range` | **VERIFIED** |
| **REQ-06** | Grounded technical RAG knowledge retrieval | `rag.knowledge_base.FAISSVectorStore` | `rag/knowledge_base.py` | `tests/rag/test_rag.py::test_faiss_retrieval` | **VERIFIED** |
| **REQ-07** | Deterministic LangGraph multi-agent flow | `agents.orchestrator` StateGraph | `agents/orchestrator.py` | `tests/agents/test_agents.py::test_interview_full_api_cycle` | **VERIFIED** |
| **REQ-08** | Multi-criteria 5-axis answer evaluation | `agents.evaluation_agent.EvaluationAgent` | `agents/evaluation_agent.py` | `tests/agents/test_agents.py::test_evaluation_agent` | **VERIFIED** |
| **REQ-09** | Adaptive remedial follow-up questioning | `agents.question_agent.QuestionAgent` | `agents/question_agent.py` | `tests/agents/test_agents.py::test_question_agent` | **VERIFIED** |
| **REQ-10** | Empirical ML interview readiness classification | `ml.predictor.MLReadinessPredictor` | `ml/predictor.py` | `tests/ml/test_ml.py::test_ml_predictor_inference` | **VERIFIED** |
| **REQ-11** | Local speech-to-text audio transcription | `voice.transcriber.AudioTranscriber` | `voice/transcriber.py` | `tests/api/test_voice_vision.py::test_voice_transcribe_success_returns_actual_transcript` | **VERIFIED** |
| **REQ-12** | Google OAuth authentication & route protection | NextAuth.js v5 + FastAPI Guard | `frontend/lib/auth.ts`, `app/backend/routes/auth.py` | `tests/api/test_auth.py::TestAuthMeHeaderPath::test_valid_header_creates_user` | **VERIFIED** |
| **REQ-13** | User data isolation & session persistence | SQLAlchemy ORM multi-tenant queries | `database/repositories/` | `tests/unit/test_foundation.py::test_user_creation_and_retrieval` | **VERIFIED** |
| **REQ-14** | Responsive analytics & intentional empty states | Next.js Recharts + compact PanelEmpty | `frontend/app/page.tsx`, `frontend/app/analytics/page.tsx` | Playwright browser telemetry (0 errors) | **VERIFIED** |
| **REQ-15** | Role-specific question differentiation in offline mode | `LocalMockLLMClient.generate_text` | `llm/model.py` | 20-Company Simulation Audit | **DEFICIENT (Requires Live API / Bank)** |
