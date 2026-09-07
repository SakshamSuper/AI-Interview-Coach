# Deployment & Operations Guide

## 1. Overview

The **AI Interview Coach** is engineered for flexible deployment across local developer environments, containerized Docker instances, and production cloud infrastructures.

---

## 2. Environment Configuration

All application components are configured through environment variables loaded via Pydantic Settings (`config/settings.py`). A template is provided in `.env.example`.

| Variable | Type | Default | Description |
|---|---|---|---|
| `APP_NAME` | `str` | `"AI Interview Coach"` | Application identifier |
| `APP_ENV` | `str` | `"development"` | Environment mode (`development`, `production`, `test`) |
| `HOST` | `str` | `"0.0.0.0"` | Backend host binding |
| `PORT` | `int` | `8000` | Backend port binding |
| `LLM_PROVIDER` | `str` | `"mock"` | Active LLM client: `"groq"`, `"openai"`, or `"mock"` |
| `GROQ_API_KEY` | `str` | `""` | API key for Groq Cloud inference |
| `GROQ_MODEL` | `str` | `"llama-3.1-70b-versatile"` | Groq LLM model name |
| `OPENAI_API_KEY` | `str` | `""` | API key for OpenAI inference & Whisper |
| `OPENAI_MODEL` | `str` | `"gpt-4o-mini"` | OpenAI LLM model name |
| `DATABASE_URL` | `str` | `"sqlite:///./data/interview_coach.db"` | SQLAlchemy database connection URI |
| `FAISS_INDEX_DIR`| `str` | `"./data/knowledge_base/faiss_index"` | Path to persisted FAISS index files |
| `ML_MODEL_PATH` | `str` | `"./ml/models/interview_readiness_rf.joblib"`| Serialized Scikit-Learn classifier path |
| `ML_SCALER_PATH`| `str` | `"./ml/models/readiness_scaler.joblib"` | Serialized StandardScaler path |
| `TEMP_MEDIA_DIR`| `str` | `"./data/media"` | Transient storage for generated audio/video |

---

## 3. Local Bare-Metal Setup

### Prerequisites
- Python 3.10 to 3.14
- OS packages: `ffmpeg` (for audio processing) and C++ build tools (for binary extensions)

### Step-by-Step Instructions

1. **Clone and create virtual environment**:
   ```bash
   git clone https://github.com/your-username/ai-interview-coach.git
   cd ai-interview-coach
   python -m venv venv
   source venv/bin/activate   # On Windows: .\venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Initialize Artifacts**:
   ```bash
   # Index RAG knowledge base
   python scripts/ingest_knowledge_base.py

   # Train Scikit-Learn models
   python ml/train.py
   ```

4. **Start Application Services**:
   ```bash
   # Terminal 1 - Backend
   uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --reload

   # Terminal 2 - Frontend
   streamlit run app/frontend/streamlit_app.py --server.port 8501
   ```

---

## 4. Containerized Docker Deployment

### Multi-Container Orchestration (`docker-compose.yml`)

The easiest method to deploy the complete platform is with Docker Compose, which provisions both the FastAPI backend and Streamlit frontend in an isolated network with persisted volume mounts.

```bash
# Build images and start services in the foreground
docker compose up --build

# Or run in detached background mode
docker compose up -d
```

### Stopping the Services
```bash
docker compose down
```

### Manual Single-Image Build
You can build the unified image manually:
```bash
docker build -t ai-interview-coach:latest .
```

To run the backend:
```bash
docker run -p 8000:8000 --env-file .env -v $(pwd)/data:/app/data ai-interview-coach:latest
```

To run the frontend:
```bash
docker run -p 8501:8501 -e BACKEND_URL=http://host.docker.internal:8000 ai-interview-coach:latest \
    streamlit run app/frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 5. Production Cloud Deployment Best Practices

When transitioning from local/Docker development to AWS (ECS/EKS), GCP (Cloud Run/GKE), or Azure:

### 1. Database Transition
While SQLite is ideal for local development and demonstration, production multi-replica environments should use a managed PostgreSQL database (AWS RDS, GCP Cloud SQL):
```ini
DATABASE_URL=postgresql+psycopg2://user:password@db-host:5432/interview_coach
```
SQLAlchemy 2.0 ORM models in `database/models.py` are fully compatible with PostgreSQL.

### 2. Reverse Proxy & SSL Termination
Deploy an Nginx or Cloudflare reverse proxy in front of FastAPI and Streamlit:
- Forward `/api/*` and `/docs` to FastAPI (`port 8000`).
- Forward `/` and WebSocket streams (`/_stcore/stream`) to Streamlit (`port 8501`).
- Enforce strict TLS 1.3 encryption.

### 3. High Availability & Secrets Management
- Store API keys (`GROQ_API_KEY`, `OPENAI_API_KEY`) in AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault.
- Scale FastAPI ASGI worker processes using Gunicorn:
  ```bash
  gunicorn app.backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
  ```

---

## 6. Health Checks & Verification

FastAPI includes a health check endpoint at `/health`:
```bash
curl -f http://localhost:8000/health
```
In Docker, this health check runs every 30 seconds to guarantee high availability.
