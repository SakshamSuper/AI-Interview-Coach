# Deploying AI Interview Coach ML Backend to Render

This guide outlines how to deploy the FastAPI + ML backend to **[Render](https://render.com)** and connect it with your live Next.js frontend on **Vercel**.

---

## 1. Quick Deploy via Render Blueprint (Recommended)

Because a ender.yaml specification is already in the root of the repository, Render can automatically configure the service:

1. Log into your **[Render Dashboard](https://dashboard.render.com/)**.
2. In the top right, click **New +** &rarr; **Blueprint**.
3. Select and connect your repository: SakshamSuper/AI-Interview-Coach.
4. Render will detect ender.yaml and set up the **ai-interview-coach-backend** service automatically.
5. In the environment setup prompt:
   - Enter your GROQ_API_KEY (starts with gsk_...).
6. Click **Apply**.
7. Render will build the Docker container and start your FastAPI service.

---

## 2. Manual Setup on Render (Alternative)

If you prefer to configure manually:
1. Go to **[Render Dashboard](https://dashboard.render.com/)** &rarr; **New +** &rarr; **Web Service**.
2. Connect SakshamSuper/AI-Interview-Coach.
3. Configure the following settings:
   - **Name**: i-interview-coach-backend
   - **Language / Runtime**: Docker
   - **Region**: Oregon (US West) or Frankfurt (EU)
   - **Instance Type**: Free
   - **Health Check Path**: /health
4. Under **Environment Variables**, add:
   | Key | Value |
   | :--- | :--- |
   | APP_ENV | production |
   | LLM_PROVIDER | groq |
   | GROQ_API_KEY | *your_groq_api_key* |
   | LLM_MODEL | llama-3.3-70b-versatile |
   | CORS_ORIGINS | * |
   | DATABASE_URL | sqlite:///./data/interview_coach.db |
   | FAISS_INDEX_DIR | ./data/knowledge_base/faiss_index |
5. Click **Create Web Service**.

---

## 3. Link Render to Your Vercel Frontend

Once Render finishes deploying (it will show Live with a green checkmark):
1. Copy your service URL (e.g., https://ai-interview-coach-backend.onrender.com).
2. Go to your **[Vercel Dashboard](https://vercel.com/dashboard)**.
3. Select your frontend project (rontend-sable-phi-28).
4. Go to **Settings** &rarr; **Environment Variables**.
5. Add:
   - **Key**: BACKEND_API_URL
   - **Value**: https://ai-interview-coach-backend.onrender.com *(use your actual Render URL, without trailing slash)*
6. Go to **Deployments** &rarr; click the three dots on the latest deployment &rarr; **Redeploy**.

---

## 4. Verification
1. Visit https://your-backend.onrender.com/health in your browser. It should return:
   `json
   {
     status: healthy,
     app_name: AI Interview Coach,
     environment: production,
     database: connected,
     llm_provider: groq,
     vector_store: faiss,
     knowledge_base_ready: true
   }
   `
2. Visit your Vercel URL (https://frontend-sable-phi-28.vercel.app/).
3. The top bar indicator will show 🟢 API online, and all ML/AI features (Resume ATS scoring, skill matching, live technical interviews, and ML readiness predictions) will be fully functional online!
