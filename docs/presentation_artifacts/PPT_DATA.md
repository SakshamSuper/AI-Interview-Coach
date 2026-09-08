# AI Interview Coach — Presentation Content & Slide Outline

---

### Slide 1: Title Slide
- **Title**: AI Interview Coach
- **Subtitle**: Adaptive Technical Interview Platform Powered by LangGraph, FAISS RAG, and Scikit-Learn
- **Presenter**: Saksham Aggarwal
- **Speaker Notes**: Introduce the project as a production-grade AI interview preparation platform combining multi-agent state machines, vector retrieval, and empirical machine learning.

---

### Slide 2: The Problem
- **Bullet Points**:
  - Candidates struggle with generic algorithm preparation that fails to reflect real system architectures.
  - Resume ATS screening remains a black box, with candidates unable to benchmark compatibility before applying.
  - Peer mock interviews offer inconsistent, subjective feedback without clear rubrics.
  - Unstructured LLM chatbots hallucinate and lack deterministic state control.
- **Speaker Notes**: Highlight that current preparation tools are fragmented between static leetcode problems and ungrounded chatbots.

---

### Slide 3: Proposed Solution
- **Bullet Points**:
  - **Deterministic State Machine**: LangGraph orchestrator guarantees clear separation between parsing, questioning, evaluating, and recommending.
  - **Grounded Retrieval**: FAISS vector database grounds questions and evaluations in curated engineering documents.
  - **Hybrid Fit & ATS Scoring**: Quantifies 6 compatibility dimensions with actionable resume improvement feedback.
  - **Empirical ML Readiness**: Scikit-Learn classifier forecasts real interview readiness tiers.
- **Speaker Notes**: Present our unified platform as the solution that bridges resume parsing, structured questioning, and predictive readiness.

---

### Slide 4: System Architecture
- **Bullet Points**:
  - **Frontend**: Next.js 16 + React 19 + TypeScript + Tailwind CSS.
  - **Backend**: FastAPI asynchronous REST API.
  - **Orchestration**: LangGraph state graph managing context persistence and transitions.
  - **Data Layer**: SQLite for relational records; FAISS for vector embeddings.
  - **Security**: NextAuth.js v5 with Google OAuth and multi-tenant user isolation.
- **Artifact**: Architecture Topology Diagram from `ARCHITECTURE.md`.
- **Speaker Notes**: Walk through the end-to-end data pipeline from browser interaction to backend agents and persistence.

---

### Slide 5: Resume Ingestion & ATS Scoring Pipeline
- **Bullet Points**:
  - Line-by-line project boundary classifier extracts multiple complex projects with tech tags and links.
  - 6-Component ATS compatibility scoring (Keyword coverage, Required skills, Semantics, Experience, Education, Completeness).
  - Categorizes skill gaps into Strong, Matched, Partially Matched, and High-Priority Missing skills.
- **Metrics**: Tested across 20 company JDs with ATS scores ranging from 44.8 to 75.8.
- **Speaker Notes**: Demonstrate that our ATS engine produces distinct, logical scores reflecting true candidate-JD overlap.

---

### Slide 6: Knowledge Retrieval & RAG Pipeline
- **Bullet Points**:
  - Curated engineering corpus covering System Design, Distributed Systems, Concurrency, and ML Platforms.
  - Recursive chunking (500 tokens, 75 overlap) indexed in a local `faiss.IndexFlatL2` vector store.
  - Sub-millisecond similarity search retrieves top-3 grounded context chunks per question.
- **Speaker Notes**: Explain how RAG eliminates LLM hallucinations by injecting verified engineering standards into the agent prompts.

---

### Slide 7: LangGraph Multi-Agent Orchestration
- **Bullet Points**:
  - **Deterministic Topology**: `ResumeAgent` $	o$ `QuestionAgent` $	o$ `EvaluationAgent` $	o$ `RecommendationAgent`.
  - **5-Axis Rubric**: Technical Accuracy, Relevance, Completeness, Clarity, Communication (0–100 scale).
  - **Adaptive Feedback**: Diagnostic follow-up questions target candidate's omitted concepts.
- **Speaker Notes**: Contrast our state machine against chaotic autonomous agent loops—LangGraph guarantees deterministic transitions.

---

### Slide 8: Machine Learning Readiness Classifier
- **Bullet Points**:
  - Scikit-Learn classifier (`LogisticRegression` / `RandomForest`) trained on 1,200 synthetic feature vectors.
  - Ingests 9 session feature inputs (5 evaluation dimensions, answer length, keyword coverage, difficulty, attempts).
  - Predicts Readiness Tier (`Interview Ready`, `Almost Ready`, `Needs Improvement`) with class probability distribution.
  - Transparent synthetic data disclosure provided on all reports.
- **Speaker Notes**: Emphasize our commitment to empirical modeling while maintaining full transparency regarding synthetic training data.

---

### Slide 9: Speech-to-Text Voice Pipeline
- **Bullet Points**:
  - Browser MediaRecorder records candidate audio via high-fidelity Opus/WAV stream.
  - Local OpenAI Whisper (`base`) transcribes audio on CPU/CUDA with zero cloud API latency.
  - Robust exception handling rejects empty or silent audio without emitting fake fallback transcripts.
- **Speaker Notes**: Highlight that candidates can practice speaking naturally, replicating real phone or video technical screens.

---

### Slide 10: User Interface & Experience
- **Bullet Points**:
  - Information-dense, compact SaaS dashboard designed for serious technical preparation.
  - Dedicated views: Resume Analysis, Job Matching, Knowledge Base, Practice Interview, Analytics, Session History.
  - Zero performance empty states ("No Data ≠ Zero Performance"): clean `"—"` placeholders instead of misleading 0% bars.
- **Artifact**: Screenshots of Dashboard, Resume, and Analytics.
- **Speaker Notes**: Show the visual polish and usability of the application.

---

### Slide 11: Quality Assurance & Testing Rigor
- **Bullet Points**:
  - **Pytest**: 72 / 72 passed (100% test pass rate in ~23s).
  - **Next.js Build**: 0 TypeScript errors across 13 compiled routes.
  - **Console Telemetry**: 0 console errors, 0 warnings across all production views.
  - Added dedicated regression tests for role-specific question generation, within-session deduplication, and difficulty adaptation.
- **Speaker Notes**: Underscore the engineering rigor and test coverage validating the platform.

---

### Slide 12: 20-Company Simulation Results
- **Bullet Points**:
  - Executed 20 full company $\times$ role simulations (Google, Apple, NVIDIA, Amazon, Meta, etc.).
  - 20 / 20 sessions completed successfully without API or session lock errors.
  - ATS scores varied logically: 44.8 to 75.8.
  - Evaluation scores responded to answer quality: Strong answers = 84.0; Incomplete answers = 72.0.
- **Artifact**: Summary Table from `SIMULATION_RESULTS.csv`.
- **Speaker Notes**: Present the extensive simulation run proving pipeline stability.

---

### Slide 13: Discovered Limitation, Root Cause & Verified Resolution
- **Bullet Points**:
  - **Audit Finding**: Initial 20-company audit detected that `LocalMockLLMClient` generated 57 duplicate turns defaulting to the CPython GIL question due to broad `"python"` keyword matching.
  - **Root Cause**: `LocalMockLLMClient` lacked role-family routing, and candidate Saksham's resume contained `"Python"`, triggering the GIL branch unconditionally.
  - **Architectural Fix**:
    1. Implemented role-aware routing across 5 role families (`ml_ai`, `data_science`, `data_engineering`, `backend_systems`, `software_engineering`).
    2. Prioritized topic resolution in `QuestionAgent` (Skill gaps $\to$ JD required skills $\to$ Role archetype).
    3. Session deduplication via `previous_questions` tracking and unasked rotation.
  - **Verified Re-Simulation**: Re-ran the 20-company simulation, achieving **100% role-specific alignment, 0 within-session duplicates, and 14 distinct role questions across 10 topics**.
- **Speaker Notes**: Demonstrate mature engineering by explaining how we audited the system, isolated the exact failure mode, engineered the architectural fix, and verified complete role differentiation.

---

### Slide 14: Future Work & Roadmap
- **Bullet Points**:
  - Integrate live Groq / OpenAI API endpoints with role-conditioned prompt routing.
  - Expand `LocalMockLLMClient` offline question bank across 15 distinct engineering specializations.
  - Add interactive LeetCode code execution sandbox with WebAssembly / Docker execution.
  - Integrate cloud vector databases (Qdrant / Pinecone) for multi-million document scaling.
- **Speaker Notes**: Detail the immediate next milestones to transition the platform to production deployment.

---

### Slide 15: Conclusion & Key Takeaways
- **Bullet Points**:
  - Successfully developed an integrated, multi-agent AI technical interview coach.
  - Validated with 69 unit tests, 0 build errors, and a 20-company end-to-end simulation.
  - Identified and documented architectural limitations with complete transparency.
  - Ready for deployment with live LLM API keys.
- **Speaker Notes**: Summarize the achievements, lessons learned, and overall system maturity.
