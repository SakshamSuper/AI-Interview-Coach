# AI Interview Coach — Screenshot & Media Index for Presentation

This index maps key application interfaces to their corresponding presentation slides and rationale.

| Screenshot # | Page / View | URL | What to Show | Key Rationale | Recommended Slide |
|:---:|---|---|---|---|:---:|
| **SS-01** | **Login** | `/login` | NextAuth Google Sign-In card | Demonstrates production auth, OAuth 2.0, and secure session handoff | Slide 4 (Architecture) |
| **SS-02** | **Resume Analysis** | `/resume` | Status pill `2 · projects`, extracted skills, and detailed project cards | Proves multi-project parsing regex and extraction integrity | Slide 5 (Resume & ATS) |
| **SS-03** | **Job Description** | `/jobs` | Form with synthetic JD input and parsed seniority/skills | Shows real-time JD parsing and requirement extraction | Slide 5 (Resume & ATS) |
| **SS-04** | **ATS Score** | `/matching` | 6-Component ATS compatibility breakdown (0–100 score, letter grade) | Demonstrates multi-criteria compatibility scoring without duplicate parsing | Slide 5 (Resume & ATS) |
| **SS-05** | **Skill Gap Report** | `/matching` | Missing skills pill list (e.g. Caching, Distributed Systems, Kafka) | Proves hybrid set-overlap and priority gap identification | Slide 5 (Resume & ATS) |
| **SS-06** | **Knowledge Base** | `/knowledge` | Retrieved markdown chunks with L2 distance scores and topic filters | Grounds interview questions in verified system architecture standards | Slide 6 (RAG Pipeline) |
| **SS-07** | **Interactive Interview** | `/interview` | Adaptive question card with difficulty badge, topic tag, and answer textarea | Demonstrates LangGraph state machine active questioning node | Slide 7 (LangGraph) |
| **SS-08** | **Answer Evaluation** | `/interview` | 5-Axis scoring table (Accuracy, Relevance, Completeness, Clarity, Communication) | Proves structured multi-criteria rubric evaluation and constructive feedback | Slide 7 (LangGraph) |
| **SS-09** | **Interview Completion** | `/interview` | Final overall score, strengths, improvement areas, and 4-week roadmap | Shows RecommendationAgent synthesis and actionable preparation planning | Slide 7 (LangGraph) |
| **SS-10** | **Performance Dashboard** | `/` | Total sessions (42), score trajectory line chart, topic mastery, recent sessions | Demonstrates SQLite persistence, live telemetry, and zero-data empty handling | Slide 10 (UI Screens) |
| **SS-11** | **Performance Analytics** | `/analytics` | Score progression chart, skill dimension bars, and Scikit-Learn readiness panel | Proves empirical ML readiness classification and multi-axis performance tracking | Slide 8 (ML Readiness) |
| **SS-12** | **Session History** | `/history` | Chronological session table with dates, roles, scores, and expandable Q&A | Shows full session history auditability and multi-turn persistence | Slide 10 (UI Screens) |
| **SS-13** | **Settings & System Health** | `/settings` | System health indicators (FastAPI, FAISS, Whisper, SQLite, Auth) | Proves full-stack operational health and component observability | Slide 11 (Testing) |
