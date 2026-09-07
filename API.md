# REST API Documentation

The **AI Interview Coach** exposes a RESTful API powered by FastAPI with interactive Swagger/OpenAPI documentation accessible at `/docs` or `/redoc`.

Base URL: `http://localhost:8000`

---

## Table of Contents
1. [System & Health](#1-system--health)
2. [User Management](#2-user-management)
3. [NLP Parsing & Extraction](#3-nlp-parsing--extraction)
4. [Semantic Matching](#4-semantic-matching)
5. [Knowledge Base & RAG](#5-knowledge-base--rag)
6. [Interview Sessions & Multi-Agent Flow](#6-interview-sessions--multi-agent-flow)
7. [Analytics & Readiness ML](#7-analytics--readiness-ml)
8. [Voice & Speech](#8-voice--speech)
9. [Computer Vision Analytics](#9-computer-vision-analytics)

---

## 1. System & Health

### `GET /health`
Returns service operational health and database connectivity status.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "app_name": "AI Interview Coach",
  "version": "1.0.0",
  "environment": "development",
  "database": "connected"
}
```

---

## 2. User Management

### `POST /users`
Creates a candidate profile in the system.

**Request Body**:
```json
{
  "email": "alex.chen@example.com",
  "full_name": "Alex Chen"
}
```

**Response (201 Created)**:
```json
{
  "id": "usr_94b8e21a",
  "email": "alex.chen@example.com",
  "full_name": "Alex Chen",
  "created_at": "2026-09-08T01:30:00Z"
}
```

### `GET /users/{user_id}`
Fetches user details and associated interview history.

---

## 3. NLP Parsing & Extraction

### `POST /resumes/parse`
Parses raw resume text and extracts structured candidate profile data.

**Request Body**:
```json
{
  "raw_text": "Alex Chen\nSenior Software Engineer\nSkills: Python, FastAPI, Docker, PostgreSQL, PyTorch"
}
```

**Response (200 OK)**:
```json
{
  "name": "Alex Chen",
  "email": "alex.chen@example.com",
  "phone": "+1-555-0199",
  "skills": {
    "languages": ["Python"],
    "frameworks": ["FastAPI"],
    "databases": ["PostgreSQL"],
    "cloud_devops": ["Docker"],
    "ai_ml": ["PyTorch"],
    "system_design": []
  },
  "years_of_experience": 5.0,
  "education": ["B.S. Computer Science"]
}
```

### `POST /resumes/upload`
Accepts multipart file upload (`.pdf`, `.docx`, `.txt`) and returns parsed profile.

### `POST /jobs/parse`
Extracts structured role requirements, required/preferred skills, and tier from job descriptions.

---

## 4. Semantic Matching

### `POST /matching/match`
Calculates hybrid skill overlap and dense semantic similarity between a candidate profile and job requirements.

**Request Body**:
```json
{
  "resume_text": "Alex Chen... Python, Docker, FastAPI...",
  "job_description_text": "We are seeking a Backend Engineer skilled in Python, FastAPI, Docker, Kubernetes, and Kafka."
}
```

**Response (200 OK)**:
```json
{
  "overall_match_score": 78.5,
  "classification": "Strong Match",
  "keyword_overlap_score": 75.0,
  "semantic_similarity_score": 80.8,
  "matched_skills": ["Python", "FastAPI", "Docker"],
  "missing_skills": [
    {
      "skill": "Kubernetes",
      "priority": "High",
      "category": "cloud_devops"
    },
    {
      "skill": "Kafka",
      "priority": "Medium",
      "category": "system_design"
    }
  ]
}
```

---

## 5. Knowledge Base & RAG

### `GET /knowledge-base/topics`
Lists all available indexed technical disciplines.

**Response (200 OK)**:
```json
{
  "topics": [
    "python_oop",
    "system_design",
    "dsa",
    "sql_databases",
    "machine_learning",
    "genai_rag",
    "cloud_devops"
  ]
}
```

### `GET /knowledge-base/search?query=microservices+caching&top_k=3`
Executes semantic vector search over the FAISS index using cosine similarity.

**Response (200 OK)**:
```json
{
  "query": "microservices caching",
  "results": [
    {
      "content": "### Distributed Caching Strategies...",
      "metadata": {
        "source": "system_design.md",
        "topic": "system_design",
        "chunk_id": 4
      },
      "score": 0.8842
    }
  ]
}
```

---

## 6. Interview Sessions & Multi-Agent Flow

### `POST /interviews/start`
Initializes a new LangGraph multi-agent interview session.

**Request Body**:
```json
{
  "user_id": "usr_94b8e21a",
  "job_title": "Senior Backend Engineer",
  "resume_text": "...",
  "job_description_text": "...",
  "total_questions": 3
}
```

**Response (201 Created)**:
```json
{
  "session_id": "ses_8a12e3f4",
  "current_question_index": 0,
  "total_questions": 3,
  "focus_topics": ["cloud_devops", "system_design"],
  "first_question": {
    "question_id": "q_1",
    "question_text": "How would you design a distributed caching layer to mitigate cache stampedes?",
    "topic": "system_design",
    "difficulty": "Senior"
  }
}
```

### `POST /interviews/{session_id}/evaluate`
Submits candidate answer and triggers the `EvaluationAgent` for scoring.

**Request Body**:
```json
{
  "question_id": "q_1",
  "answer_text": "I would implement probabilistic early expiration and distributed mutex locking (single-flight pattern) via Redis."
}
```

**Response (200 OK)**:
```json
{
  "technical_score": 9.0,
  "communication_score": 8.5,
  "problem_solving_score": 9.0,
  "strengths": ["Clear mention of single-flight pattern", "Effective understanding of cache stampede mechanics"],
  "areas_for_improvement": ["Could elaborate on Redis cluster node failover handling"],
  "model_answer": "An optimal answer includes...",
  "is_session_completed": false,
  "next_question": {
    "question_id": "q_2",
    "question_text": "...",
    "topic": "cloud_devops"
  }
}
```

### `POST /interviews/{session_id}/recommend`
Generates comprehensive candidate preparation roadmap using `RecommendationAgent`.

---

## 7. Analytics & Readiness ML

### `POST /analytics/readiness`
Executes real-time inference using the Scikit-Learn readiness classifier.

**Request Body**:
```json
{
  "match_score": 82.0,
  "avg_technical_score": 8.5,
  "avg_communication_score": 8.0,
  "avg_problem_solving_score": 8.0,
  "completion_rate": 1.0,
  "difficulty_index": 3
}
```

**Response (200 OK)**:
```json
{
  "readiness_status": "Ready",
  "probabilities": {
    "Needs Improvement": 0.01,
    "Borderline": 0.04,
    "Ready": 0.95
  },
  "benchmark_summary": "Candidate exhibits strong alignment with Senior role benchmarks."
}
```

---

## 8. Voice & Speech

### `POST /voice/speak`
Synthesizes text into an audio file (`.mp3` via gTTS or `.wav` via synthetic fallback).

**Request Body**:
```json
{
  "text": "Could you explain how database indexes improve query performance?"
}
```

**Response (200 OK)**:
```json
{
  "audio_url": "/media/question_speech_48123.mp3",
  "format": "audio/mp3",
  "status": "success"
}
```

### `POST /voice/transcribe`
Transcribes uploaded audio files (`.wav`, `.mp3`, `.m4a`) into text.

---

## 9. Computer Vision Analytics

### `POST /vision/analyze-frame`
Processes a base64 encoded video frame and computes objective positioning metrics.

**Request Body**:
```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA..."
}
```

**Response (200 OK)**:
```json
{
  "face_detected": true,
  "posture_detected": true,
  "head_yaw_angle": 1.2,
  "head_pitch_angle": -2.4,
  "shoulder_tilt_angle": 0.8,
  "motion_energy": 0.04,
  "alignment_status": "Centered and Stable",
  "responsible_ai_notice": "Physical alignment metric only. Does not measure psychological or emotional states."
}
```
