# Production Deployment Guide: AI Interview Coach

This document details the production deployment, infrastructure architecture, environment configurations, and operational playbooks for the **AI Interview Coach** application.

---

## 1. Production Architecture Overview

The system is deployed using a decoupled, cloud-native architecture optimized for performance, scalability, and security:

```mermaid
flowchart TD
    subgraph Client Layer
        Browser[User Web Browser]
    end

    subgraph Vercel Edge / Serverless Network
        VercelFront[Next.js 16.3.4 App Router]
        NextAuth[NextAuth v4 Session & JWT]
        VercelRewrite[Next.js API Rewrite Proxy /api/py]
    end

    subgraph Cloud Infrastructure - Render
        FastAPI[FastAPI 0.115+ Backend Service]
        Uvicorn[Uvicorn ASGI Engine - Port 8000]
        CORS[Configurable CORS Middleware]
        LangGraph[LangGraph State Machine Engine]
        RAG[RAG Retrieval Engine / FAISS]
        ML[Scikit-Learn ML Readiness Predictor]
        Disk[(Render Persistent Disk: /var/data)]
    end

    subgraph External Managed APIs
        GroqCloud[Groq Cloud LLM API: openai/gpt-oss-120b & llama-3.3-70b]
        GoogleOAuth[Google Cloud OAuth 2.0 Provider]
    end

    Browser <-->|HTTPS| VercelFront
    VercelFront <--> NextAuth
    NextAuth <-->|OAuth2 Token Exchange| GoogleOAuth
    VercelFront -->|Proxy Rewrite /api/py| VercelRewrite
    VercelRewrite <-->|Secure HTTPS / mTLS| FastAPI
    FastAPI <--> CORS
    FastAPI <--> LangGraph
    LangGraph <--> RAG
    LangGraph <--> ML
    FastAPI <-->|High-Speed Inference| GroqCloud
    FastAPI <--> Disk
    RAG <--> Disk
```

### Architecture Highlights:
- **Frontend (Vercel)**: Next.js 16 App Router running with Turbopack, responsive UI/UX, Google OAuth authentication via NextAuth, and automated API proxy rewrites routing `/api/py/*` to Render.
- **Backend (Render)**: Python 3.11 FastAPI service serving RESTful endpoints, running deterministic LangGraph state machine orchestrators, FAISS semantic search, and Scikit-Learn readiness models.
- **Persistent Storage**: Render Persistent Disk mounted at `/var/data` preserving SQLite relational databases (`interview_coach.db`) and FAISS vector indices (`faiss_index`) across redeployments and service restarts.
- **LLM Engine**: Groq Cloud inference (`openai/gpt-oss-120b` and `llama-3.3-70b-versatile`) delivering sub-second token generation with zero rate-limit errors.

---

## 2. Prerequisites

Ensure you have the following accounts and credentials ready prior to deployment:

1. **GitHub Repository**: Pushed and clean repository containing this codebase.
2. **Render Account**: Account at [render.com](https://render.com) for backend hosting.
3. **Vercel Account**: Account at [vercel.com](https://vercel.com) for frontend hosting.
4. **Groq Cloud API Key**: Active API key from [console.groq.com](https://console.groq.com) (Format: `gsk_...`).
5. **Google Cloud OAuth Credentials**:
   - Google Cloud Console -> APIs & Services -> Credentials.
   - Authorized Javascript Origin: `https://<your-vercel-app>.vercel.app` (and `http://localhost:3000`).
   - Authorized Redirect URI: `https://<your-vercel-app>.vercel.app/api/auth/callback/google`.
6. **NextAuth Encryption Secret**: Generated 32-byte secret string:
   ```bash
   openssl rand -base64 32
   ```

---

## 3. Step-by-Step Render Deployment (FastAPI Backend)

### Option A: Using Render Blueprint (`render.yaml`) - Recommended
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository.
4. Render will automatically detect `render.yaml` and configure:
   - Web service: `interview-coach-api`
   - Persistent disk: `data_disk` (5GB mounted at `/var/data`)
   - Health check: `/health`
5. In the Environment Variables screen, input your secret `GROQ_API_KEY`.
6. Click **Apply**.

### Option B: Manual Service Creation
1. Go to [Render Dashboard](https://dashboard.render.com) -> **New +** -> **Web Service**.
2. Select your repository.
3. Configure the following service settings:
   - **Name**: `interview-coach-api`
   - **Region**: Choose closest to your users (e.g., `Oregon (US West)` or `Frankfurt (EU)`).
   - **Branch**: `main` or `master`
   - **Root Directory**: Leave blank (root).
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python scripts/train_ml_model.py && python scripts/ingest_knowledge_base.py
     ```
   - **Start Command**:
     ```bash
     uvicorn app.backend.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Starter ($7/month recommended for persistent disk support).
4. **Attach Persistent Disk**:
   - Under **Disks**, click **Add Disk**.
   - **Name**: `interview-coach-data`
   - **Mount Path**: `/var/data`
   - **Size**: `5 GB`
5. **Set Environment Variables**:
   ```env
   APP_ENV=production
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk_your_actual_groq_key_here
   GROQ_MODEL=openai/gpt-oss-120b
   DATABASE_URL=sqlite:////var/data/interview_coach.db
   FAISS_INDEX_DIR=/var/data/knowledge_base/faiss_index
   ML_MODEL_PATH=/app/ml/models/interview_readiness_rf.joblib
   ML_SCALER_PATH=/app/ml/models/readiness_scaler.joblib
   CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
   WHISPER_MODEL=tiny
   ```
6. **Health Check Path**:
   - In **Advanced** -> **Health Check Path**, enter: `/health`
7. Click **Create Web Service**.
8. Note your public backend URL (e.g., `https://interview-coach-api.onrender.com`).

---

## 4. Step-by-Step Vercel Deployment (Next.js Frontend)

1. Log in to [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository.
4. Configure Project Settings:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click Edit and select `frontend`.
   - **Build Command**: `next build` (default).
   - **Output Directory**: `.next` (default).
   - **Install Command**: `npm install` (default).
5. Configure Environment Variables:
   | Key | Value | Description |
   |---|---|---|
   | `BACKEND_API_URL` | `https://interview-coach-api.onrender.com` | Internal Next.js proxy target |
   | `NEXT_PUBLIC_API_URL` | `https://interview-coach-api.onrender.com` | Browser fallback API target |
   | `NEXTAUTH_URL` | `https://<your-vercel-domain>.vercel.app` | Production authentication URL |
   | `NEXTAUTH_SECRET` | `<your-32-byte-secret>` | Encryption key for JWTs |
   | `GOOGLE_CLIENT_ID` | `...apps.googleusercontent.com` | Google OAuth Client ID |
   | `GOOGLE_CLIENT_SECRET` | `GOCSPX-...` | Google OAuth Client Secret |
6. Click **Deploy**.
7. Once deployed, copy your production Vercel URL and update:
   - Google Cloud Console: Add Vercel URL to Authorized Origins & Redirect URIs.
   - Render Backend: Add Vercel URL to `CORS_ORIGINS`.

---

## 5. Environment Variables Reference Table

| Variable Name | Required | Default / Recommended | Purpose & Scope |
|---|---|---|---|
| `APP_ENV` | Yes | `production` | Enables production mode, disables debug endpoints |
| `LLM_PROVIDER` | Yes | `groq` | Directs LLM orchestrator to Groq Cloud API |
| `GROQ_API_KEY` | Yes | *Secret* (`gsk_...`) | Groq API authentication token |
| `GROQ_MODEL` | No | `openai/gpt-oss-120b` | Model identifier (or `llama-3.3-70b-versatile`) |
| `DATABASE_URL` | Yes | `sqlite:////var/data/interview_coach.db` | SQLAlchemy DB connection string (SQLite or PostgreSQL) |
| `FAISS_INDEX_DIR` | Yes | `/var/data/knowledge_base/faiss_index` | Location of indexed FAISS vectors |
| `ML_MODEL_PATH` | Yes | `/app/ml/models/interview_readiness_rf.joblib` | Path to trained Scikit-Learn readiness model |
| `ML_SCALER_PATH` | Yes | `/app/ml/models/readiness_scaler.joblib` | Path to Scikit-Learn standard feature scaler |
| `CORS_ORIGINS` | Yes | `https://your-frontend.vercel.app` | Comma-separated allowed CORS browser origins |
| `WHISPER_MODEL` | No | `tiny` | Audio model size (`tiny`, `base`, `small`) |
| `BACKEND_API_URL` | Yes | `https://your-backend.onrender.com` | Frontend server-side proxy target (Vercel) |
| `NEXTAUTH_URL` | Yes | `https://your-frontend.vercel.app` | Canonical NextAuth callback origin (Vercel) |
| `NEXTAUTH_SECRET` | Yes | *Secret (32+ chars)* | Session token cryptographic encryption key |
| `GOOGLE_CLIENT_ID` | Yes | `...apps.googleusercontent.com` | OAuth 2.0 Client Identifier |
| `GOOGLE_CLIENT_SECRET` | Yes | *Secret (`GOCSPX-...`)* | OAuth 2.0 Client Secret |

---

## 6. Database Persistence Guide

### SQLite on Persistent Disk (Standard Setup)
- Default connection: `sqlite:////var/data/interview_coach.db`
- **Safety**: Render's persistent disk survives web service restarts, deploys, and container rebuilding.
- **Backup**: Download `/var/data/interview_coach.db` via Render Shell:
  ```bash
  sqlite3 /var/data/interview_coach.db ".backup '/var/data/backup.db'"
  ```

### External Managed PostgreSQL (High Concurrency Setup)
For higher concurrent load (>50 simultaneous interviews):
1. Provision a PostgreSQL instance (Render Managed PostgreSQL, Supabase, or AWS RDS).
2. Set `DATABASE_URL`:
   ```env
   DATABASE_URL=postgresql://coach_user:password@host:5432/interview_coach
   ```
3. SQLAlchemy models in `database/models.py` are dialect-agnostic and will create all tables automatically via `Base.metadata.create_all(bind=engine)`.

---

## 7. FAISS Vector Store in Production

- **Self-Healing Lifespan**: The backend includes self-healing startup logic in `app/backend/main.py`. If `index.faiss` is missing at startup (e.g. fresh disk initialization), the service runs `ingest_knowledge_base()` in background upon startup, indexing the 5 markdown knowledge-base docs in ~2 seconds.
- **Pre-building**: The build command in `render.yaml` executes `python scripts/ingest_knowledge_base.py`, ensuring indices are populated before Uvicorn starts listening.

---

## 8. Production Verification Checklist

Run this post-deployment checklist against your production deployment:

- [ ] **1. Health Endpoint**: `GET https://<render-url>/health` returns HTTP 200 with:
  ```json
  {"status":"healthy","llm_provider":"groq","database":"connected","faiss_vector_store":"loaded"}
  ```
- [ ] **2. Frontend Availability**: `GET https://<vercel-url>/` renders Dashboard with 0 console errors.
- [ ] **3. Google Authentication**: Login button directs to Google OAuth consent screen and redirects back with active user session.
- [ ] **4. Resume ATS Parsing**: Uploading sample resume to `/resume` parses skills and returns ATS score.
- [ ] **5. Job Description Extraction**: Pasting job description to `/jobs` extracts role, requirements, and seniorities.
- [ ] **6. Skill Gap Match**: `/matching` shows hybrid fit score, strong matches, and prioritized missing skills.
- [ ] **7. Live Interview Generation**: Starting interview generates role-tailored technical Question 1 via Groq within 1.5 seconds.
- [ ] **8. Answer Evaluation**: Submitting answer generates technical, communication, and problem-solving scores with feedback.
- [ ] **9. Analytics Display**: `/analytics` displays session scores and Scikit-Learn readiness classification.
- [ ] **10. Settings & RAG**: `/settings` confirms LLM status and RAG query sandbox returns grounded chunks.

---

## 9. Cost Estimation

### Free Tier ($0 / month)
- **Frontend (Vercel)**: Hobby Plan — $0 / month (Unlimited builds, edge routing, 100GB bandwidth).
- **Backend (Render)**: Free Web Service — $0 / month (512MB RAM, shared CPU).
  - *Note*: Free instances spin down after 15 minutes of inactivity (50s cold start) and do not support persistent disks.
- **LLM (Groq Cloud)**: Developer Free Tier — $0 / month (30 RPM, 14,400 RPD for `llama-3.3-70b-versatile` and `openai/gpt-oss-120b`).
- **Total**: **$0.00 / month**

### Production Starter Tier ($8.25 / month) — Recommended
- **Frontend (Vercel)**: Hobby Plan — $0 / month.
- **Backend (Render)**: Starter Web Service — $7.00 / month (Always on, 512MB RAM, no cold starts).
- **Persistent Disk (Render)**: 5GB Disk — $1.25 / month ($0.25/GB/month).
- **LLM (Groq Cloud)**: Pay-as-you-go or free allowance.
- **Total**: **$8.25 / month**

---

## 10. Monitoring & Maintenance

- **Uptime Monitoring**: Configure a free monitor on [UptimeRobot](https://uptimerobot.com) to ping `https://<render-url>/health` every 5 minutes. This prevents free-tier spin-downs.
- **Memory Consumption**:
  - Base FastAPI + FAISS + LangGraph: ~180MB RAM.
  - Whisper (`tiny` model): ~75MB RAM.
  - Total operational footprint: ~255MB RAM (safely within 512MB limit).
- **Logs**:
  - Render Dashboard -> **Logs** stream live stdout/stderr from Uvicorn.
  - Vercel Dashboard -> **Logs** stream edge middleware and serverless functions.

---

## 11. Rollback Procedure

- **Frontend Rollback (Instant)**:
  1. Open Vercel Dashboard -> **Deployments**.
  2. Select the previous stable deployment.
  3. Click **...** -> **Promote to Production**. Instant switch in < 5 seconds.
- **Backend Rollback**:
  1. Open Render Dashboard -> **Deploys**.
  2. Select previous deploy -> Click **Rollback to this deploy**.
  3. Or revert git commit: `git revert HEAD && git push origin main`.

---

## 12. Security & Compliance Checklist

- **Secrets Management**: 0 API keys or passwords are committed to Git. All secrets are injected via encrypted environment variables.
- **CORS Defense**: Scoped strict origins via `allow_origin_regex` (`https://.*\.vercel\.app`) and explicit `CORS_ORIGINS`.
- **JWT Protection**: Encrypted NextAuth session cookies with `SameSite=Lax` and `Secure` flags.
- **OWASP Top 10 Mitigation**:
  - *Injection*: SQLAlchemy parameterized ORM queries prevent SQL injection.
  - *Broken Authentication*: Delegated OAuth 2.0 to Google Identity.
  - *Sensitive Data Exposure*: Enforced HTTPS/TLS across both Vercel and Render endpoints.
  - *Security Misconfiguration*: Swagger/OpenAPI docs exposed cleanly; debug headers stripped in production.
