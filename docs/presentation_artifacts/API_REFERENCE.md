# AI Interview Coach — Production API Reference

Base URL: `http://127.0.0.1:8000` (FastAPI backend)

---

## 1. Authentication Endpoints

### `GET /auth/me`
- **Purpose**: Resolves or creates the database user associated with the authenticated session.
- **Authentication**: Bearer JWT (`Authorization: Bearer <token>`) or NextAuth Proxy Headers (`X-Auth-User-Email`).
- **Response** (`200 OK`):
  ```json
  {
    "id": 8,
    "email": "sakshamaggarwal2475@gmail.com",
    "name": "Saksham Aggarwal",
    "avatar_url": null,
    "target_role": "Senior Software Engineer"
  }
  ```

---

## 2. Resume & Job Description Endpoints

### `POST /resumes/upload`
- **Purpose**: Uploads and parses candidate resume file (`.pdf`, `.docx`, `.txt`).
- **Request**: Multipart Form Data (`file`, `user_id`).
- **Response** (`200 OK`):
  ```json
  {
    "resume_id": 56,
    "profile": {
      "name": "Saksham Aggarwal",
      "email": "sakshamaggarwal2475@gmail.com",
      "skills": ["Python", "FastAPI", "React", "Next.js", "Docker", "PostgreSQL", "Redis"],
      "projects": [
        {"title": "AI Posture Analysis & LLM Agent Assistant", "technologies": ["React", "Next.js", "LangChain", "FastAPI", "Redis"]},
        {"title": "Crypto Analyst Pro", "technologies": ["Python", "Pandas", "FastAPI", "Scikit-learn", "Streamlit"]}
      ]
    }
  }
  ```

### `POST /jobs/analyze`
- **Purpose**: Ingests and parses a job description into structured requirements.
- **Request** (`application/json`):
  ```json
  {
    "user_id": 8,
    "title": "Google - Software Engineer",
    "job_description_text": "Role: Software Engineer\nRequired Skills: Python, System Design, C++..."
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "jd_id": 74,
    "profile": {
      "job_title": "Software Engineer",
      "experience_level": "Mid-Senior",
      "required_skills": ["Python", "System Design", "C++"],
      "preferred_skills": ["Kubernetes", "gRPC"]
    }
  }
  ```

---

## 3. Matching & ATS Endpoints

### `POST /ats/score`
- **Purpose**: Computes 6-component ATS-style resume compatibility score.
- **Request** (`application/json`):
  ```json
  {
    "resume_id": 56,
    "jd_id": 74
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "overall_ats_score": 49.0,
    "grade": "D",
    "components": [
      {"name": "Keyword & Skill Coverage", "score": 45.0, "weight": 0.28},
      {"name": "Required Skill Coverage", "score": 50.0, "weight": 0.22},
      {"name": "Semantic Relevance", "score": 42.0, "weight": 0.20},
      {"name": "Experience Alignment", "score": 50.0, "weight": 0.15},
      {"name": "Education Alignment", "score": 75.0, "weight": 0.10},
      {"name": "Resume Completeness", "score": 80.0, "weight": 0.05}
    ],
    "matched_keywords": ["Python"],
    "missing_keywords": ["C++", "System Design"],
    "recommendations": ["Add missing required keywords to your resume: C++, System Design."]
  }
  ```

### `POST /matching`
- **Purpose**: Computes hybrid skill match and categorized skill gaps.
- **Request** (`application/json`):
  ```json
  {
    "resume_id": 56,
    "jd_id": 74,
    "user_id": 8
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "overall_match_score": 49.5,
    "match_category": "Weak Match",
    "gap_report": {
      "matched_skills": ["Python"],
      "missing_skills": ["C++", "Distributed Systems", "Kubernetes", "System Design"]
    }
  }
  ```

---

## 4. Practice Interview Endpoints

### `POST /interviews/start`
- **Purpose**: Initializes an adaptive LangGraph interview session.
- **Request** (`application/json`):
  ```json
  {
    "user_id": 8,
    "resume_id": 56,
    "jd_id": 74,
    "target_role": "Software Engineer",
    "difficulty": "Medium",
    "total_questions": 3
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "session_id": 111,
    "target_role": "Software Engineer",
    "difficulty": "Medium",
    "total_questions": 3,
    "question_number": 1,
    "question": {
      "question": "Explain how the Python GIL impacts CPU-bound versus I/O-bound tasks...",
      "topic": "Python & OOP",
      "difficulty": "Medium",
      "expected_concepts": ["GIL", "CPython mutex", "multiprocessing"]
    }
  }
  ```

### `POST /interviews/{id}/answer`
- **Purpose**: Evaluates candidate answer across 5 scoring dimensions.
- **Request** (`application/json`):
  ```json
  {
    "answer_text": "In Python, memory management combines reference counting and cyclic GC..."
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "session_id": 111,
    "question_id": 1,
    "is_last_question": false,
    "evaluation": {
      "technical_accuracy": 84.0,
      "relevance": 88.0,
      "completeness": 78.0,
      "clarity": 84.0,
      "communication": 86.0,
      "overall_score": 84.0,
      "feedback": "Thorough and articulate response covering the core architecture and practical trade-offs well."
    }
  }
  ```

### `POST /interviews/{id}/next`
- **Purpose**: Advances the state machine turn or triggers completion.
- **Response** (`200 OK`):
  ```json
  {
    "session_id": 111,
    "is_completed": false,
    "question_number": 2,
    "current_difficulty": "Hard",
    "question": {
      "question": "Analyze CPython bytecode execution, GIL release during I/O operations...",
      "topic": "Python & OOP",
      "difficulty": "Hard"
    }
  }
  ```

---

## 5. Analytics & Readiness Endpoints

### `GET /analytics/{user_id}`
- **Purpose**: Aggregates session performance, score trajectory, and topic breakdown.
- **Response** (`200 OK`):
  ```json
  {
    "total_interviews": 42,
    "completed_interviews": 21,
    "average_overall_score": 80.7,
    "average_technical_score": 81.2,
    "overall_readiness_label": "Almost Ready",
    "topic_performance": {
      "Python & OOP": 81.4,
      "System Design & Optimization": 78.0
    }
  }
  ```

### `GET /ml/readiness?user_id={id}`
- **Purpose**: Returns empirical ML prediction from the Scikit-Learn readiness model.
- **Response** (`200 OK`):
  ```json
  {
    "readiness_label": "Almost Ready",
    "readiness_score": 70.0,
    "class_probabilities": {
      "Interview Ready": 0.32,
      "Almost Ready": 0.68,
      "Needs Improvement": 0.00
    },
    "model_architecture": "LogisticRegression"
  }
  ```

---

## 6. Voice & Health Endpoints

### `POST /voice/transcribe`
- **Request**: Multipart Audio File (`audio`).
- **Response** (`200 OK`): `{"transcript": "In Python, memory management combines...", "model": "whisper-base"}`

### `GET /health`
- **Response** (`200 OK`): `{"status": "healthy", "version": "1.0.0", "faiss_loaded": true, "llm_client": "LocalMockLLMClient"}`
