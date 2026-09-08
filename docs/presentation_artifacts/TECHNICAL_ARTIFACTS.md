# AI Interview Coach — Technical Implementation Evidence

This document catalogues the actual implementation details and code evidence across all functional modules.

---

## 1. Natural Language Processing (NLP)

### 1.1 Resume Parser (`nlp/resume_parser.py`)
- **Document Ingestion**: Supports `.pdf`, `.docx`, and `.txt` formats via `pypdf`/`pdfplumber` and `python-docx`.
- **Project Extraction Algorithm**: Uses a stateful line-by-line boundary classifier (`is_project_header`) inspecting font capitalization, title delimiters (colon, hyphen, em-dash), project dates, and tech stacks.
- **Skill Extraction (`nlp/skill_extractor.py`)**: Tokenizes input and performs case-insensitive dictionary matching across 250+ categorized technology keywords (Languages, Frameworks, Cloud, Databases, DevOps, ML/AI).
- **Candidate Profile Output**: Strictly validated Pydantic model (`CandidateProfile`):
  ```python
  class CandidateProfile(BaseModel):
      name: Optional[str] = None
      email: Optional[str] = None
      skills: List[str] = Field(default_factory=list)
      experience_years: Optional[float] = None
      projects: List[ProjectExperience] = Field(default_factory=list)
      education: List[Education] = Field(default_factory=list)
  ```

### 1.2 Job Description Parser (`nlp/jd_parser.py`)
- Identifies role seniority (Junior, Mid, Senior, Lead, Staff, Principal) using contextual regex heuristics.
- Segregates requirements into `required_skills` versus `preferred_skills`.
- Extracts education degree requirements (BS, MS, PhD) and minimum required years of experience.

---

## 2. ATS & Hybrid Skill Matching

### 2.1 Hybrid Matching Engine (`nlp/matching.py`)
Computes an empirical match score:
$$	ext{MatchScore} = 0.50 	imes 	ext{ReqCoverage} + 0.20 	imes 	ext{PrefCoverage} + 0.20 	imes 	ext{SemanticSimilarity} + 0.10 	imes 	ext{ExpEduAlignment}$$

- **Skill Gap Classification**:
  - `Strong Match`: Skill directly matched with contextual evidence.
  - `Matched`: Exact keyword match found in candidate profile.
  - `Partially Matched`: Related technology family match (e.g. FastAPI $\leftrightarrow$ Flask).
  - `Missing`: Required skill completely absent from candidate profile.

### 2.2 ATS Compatibility Engine (`app/backend/routes/ats.py`)
Deconstructs compatibility into 6 weighted dimensions:
1. Keyword & Skill Coverage: **28%**
2. Required Skill Coverage: **22%**
3. Semantic Relevance: **20%**
4. Experience Alignment: **15%**
5. Education Alignment: **10%**
6. Resume Completeness (Name, Email, Skills, Experience, Education): **5%**

---

## 3. Retrieval-Augmented Generation (RAG) & FAISS

### 3.1 Knowledge Ingestion (`rag/knowledge_base.py`)
- **Corpus**: Pre-compiled, curated technical markdown files in `rag/documents/` covering System Design, Distributed Systems, Python/OOP, Concurrency, and ML Systems.
- **Chunking**: Character-recursive splitting with 500-token chunk sizes and 75-token sliding window overlap.
- **Vector Storage**: `faiss.IndexFlatL2` indexing dense normalized embeddings.
- **Retrieval Pipeline**:
  - `retriever.get_relevant_chunks(query, top_k=3)` computes L2 similarity.
  - Formats grounded context chunks with metadata tags (`source_doc`, `topic`, `chunk_id`).

---

## 4. LangGraph Multi-Agent State Machine

### 4.1 Topology (`agents/orchestrator.py`)
- Graph compiled via `langgraph.graph.StateGraph(InterviewState)`:
  - `resume_agent` $	o$ `question_agent` $	o$ `candidate_answer` $	o$ `evaluation_agent` $	o$ `should_continue` conditional edge $	o$ `recommendation_agent` $	o$ `END`.

### 4.2 Centralized Typed State (`agents/state.py`)
```python
class InterviewState(TypedDict):
    session_id: int
    target_role: str
    current_difficulty: str
    current_question_index: int
    total_questions: int
    candidate_profile: Dict[str, Any]
    job_profile: Dict[str, Any]
    skill_gaps: List[str]
    question_history: List[Dict[str, Any]]
    answer_history: List[Dict[str, Any]]
    evaluation_history: List[Dict[str, Any]]
```

---

## 5. Machine Learning Readiness Classifier

### 5.1 Architecture & Training (`ml/predictor.py`)
- **Classifier**: Scikit-Learn `LogisticRegression` / `RandomForestClassifier`.
- **Synthetic Training Dataset**: 1,200 synthetic interview feature vectors generated across 3 readiness classes:
  - `Interview Ready` (Class 2)
  - `Almost Ready` (Class 1)
  - `Needs Improvement` (Class 0)
- **Input Features (9 Dimensions)**:
  1. `avg_technical` (0–100)
  2. `avg_relevance` (0–100)
  3. `avg_completeness` (0–100)
  4. `avg_clarity` (0–100)
  5. `avg_communication` (0–100)
  6. `answer_length` (average words per response)
  7. `keyword_coverage` (ratio of expected concepts addressed)
  8. `difficulty_numeric` (1=Easy, 2=Medium, 3=Hard)
  9. `attempt_number` (total sessions completed)
- **Model Output**: Predicted readiness tier, class probability distribution, and mandatory synthetic training disclaimer.

---

## 6. Voice & Audio Transcription

### 6.1 Audio Transcriber Service (`voice/transcriber.py`)
- **Engine**: Local `openai-whisper` (`base` model, running on CPU/CUDA).
- **Resilience Guarantees**:
  - Rejects empty, missing, or corrupt audio files with descriptive HTTP 400 errors.
  - Validates minimum audio duration and non-silent waveform.
  - Zero fabricated transcript strings: if transcription fails, it explicitly throws an exception rather than emitting fake text.

---

## 7. Authentication & Security

### 7.1 NextAuth.js v5 + FastAPI Header/JWT Guard
- **Token Mechanism**: HttpOnly JWT session cookie managed by Next.js.
- **Backend Verification**:
  - Direct Next.js proxy route passes decoded claims via verified internal headers (`X-Auth-User-Email`, `X-Auth-User-Name`).
  - Direct REST clients authenticate via standard `Authorization: Bearer <HS256_JWT>` verified using shared `NEXTAUTH_SECRET`.
- **Database Multi-Tenancy**: All database queries filter strictly by `user_id`, preventing cross-account data leakage.
