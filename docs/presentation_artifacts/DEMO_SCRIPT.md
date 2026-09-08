# AI Interview Coach — Live Demonstration Protocol (5–10 Minutes)

This step-by-step script guides presenters through an end-to-end demonstration of the platform.

---

### Step 1: User Authentication & Tenant Resolution (0:00 – 0:45)
- **Action**: Navigate to `http://localhost:3000/login`. Point out the Google Sign-In button and NextAuth integration.
- **What to show**: Sidebar displaying the authenticated candidate profile (`Saksham Aggarwal` / `sakshamaggarwal2475@gmail.com`).
- **Verbal Explanation**:
  > *"The platform replaces hardcoded demo identities with real authentication via NextAuth.js v5 and Google OAuth. Sessions are persisted in HttpOnly JWT cookies, and the backend resolves a unique SQLite user ID to guarantee strict data isolation."*

---

### Step 2: Resume Ingestion & Project Extraction (0:45 – 1:30)
- **Action**: Navigate to `/resume`. Show the parsed candidate view.
- **What to show**: 
  - Header pill: `2 · projects`.
  - Project Cards: `AI Posture Analysis & LLM Agent Assistant` and `Crypto Analyst Pro` with full technology badges (`FastAPI`, `Redis`, `LangChain`, `Pandas`).
- **Verbal Explanation**:
  > *"Our custom line-by-line boundary classifier in `nlp/resume_parser.py` accurately extracts multiple multi-line projects, parsing descriptions, dates, GitHub URLs, and categorized skill badges."*

---

### Step 3: Job Description & ATS Compatibility Scoring (1:30 – 2:30)
- **Action**: Navigate to `/jobs`, paste a target Job Description (e.g. NVIDIA ML Engineer), and navigate to `/matching`.
- **What to show**:
  - ATS Compatibility Score (0–100 scale, letter grade).
  - 6-Component breakdown (Keyword coverage, Semantic similarity, Experience, Education).
  - Skill Gap Report (Matched skills vs High-priority missing skills).
- **Verbal Explanation**:
  > *"The ATS engine calculates a 6-component weighted compatibility score without duplicate parsing, identifying high-priority skill gaps and actionable recommendations to optimize candidate resumes before applying."*

---

### Step 4: Grounded Knowledge Base & RAG Query (2:30 – 3:15)
- **Action**: Navigate to `/knowledge`. Submit a query (e.g. `Cache stampede mitigation`).
- **What to show**: Retrieved markdown chunks from the FAISS vector index with L2 distance relevance scores and topic tags.
- **Verbal Explanation**:
  > *"Rather than relying on unconstrained LLM memory, our RAG pipeline indexes curated engineering knowledge chunks into a local FAISS index, grounding subsequent interview questions in verified technical standards."*

---

### Step 5: Interactive Adaptive Interview (3:15 – 5:00)
- **Action**: Navigate to `/interview`. Start a 3-question technical interview session.
- **What to show**:
  - Adaptive question card with topic badge (`Python & OOP`) and difficulty (`Medium`).
  - Candidate answer textarea.
  - Submitting answer and rendering 5-axis evaluation score table (`Technical Accuracy`, `Relevance`, `Completeness`, `Clarity`, `Communication`).
  - Next Question transitioning based on LangGraph conditional edge.
- **Verbal Explanation**:
  > *"The interview runs on a LangGraph state machine. Upon submitting an answer, the EvaluationAgent evaluates technical reasoning and communication clarity across 5 dimensions, dynamically adjusting the next question difficulty."*

---

### Step 6: Final Results, Analytics & Readiness Prediction (5:00 – 6:30)
- **Action**: Navigate to `/analytics` and `/history`.
- **What to show**:
  - Score progression line chart across completed sessions.
  - Performance dimensions bar chart.
  - Scikit-Learn ML Readiness panel displaying class probabilities (`Almost Ready` 70.0%).
  - Session history table showing chronological attempts.
- **Verbal Explanation**:
  > *"Upon interview completion, our RecommendationAgent synthesizes a 4-week preparation roadmap, and our Scikit-Learn classifier computes an empirical readiness tier, giving candidates an objective forecast of their interview readiness."*

---

### Step 7: Transparent Disclosure of Current Limitations (6:30 – 7:30)
- **Action**: Navigate to `/settings` or reference the Simulation Audit.
- **Verbal Explanation**:
  > *"During our 20-company simulation audit, we discovered that while ATS scoring and answer evaluation differentiated properly, our local mock LLM client defaulted to the same Python GIL questions because the candidate's resume contained Python. Fixing this mock router or attaching a live Groq/OpenAI key is our immediate next milestone."*
