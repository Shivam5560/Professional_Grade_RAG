# Deployment Guide — NexusMind Studio

> Frontend on **Vercel** · Backend on **Render** · Embedding Service remote  
> Complete guide for deploying all services in production.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
3. [Backend Deployment (Render)](#backend-deployment-render)
4. [ResumeGen Frontend (Vercel)](#resumegen-frontend-vercel)
5. [ResumeGen Backend (Render)](#resumegen-backend-render)
6. [Embedding Service (Remote)](#embedding-service-remote)
7. [CORS Configuration](#cors-configuration)
8. [Environment Variables Reference](#environment-variables-reference)
9. [Resource Constraints & Free Tier Limits](#resource-constraints--free-tier-limits)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌──────────────────┐    HTTPS     ┌──────────────────┐
│  Vercel          │ ──────────── │  Render           │
│  (Frontend)      │    API       │  (Backend)        │
│  Next.js App     │    calls     │  FastAPI + DB     │
└──────────────────┘              └──────────────────┘
                                         │
                                    ┌────┴────────┐
                                    │  PostgreSQL  │
                                    │  (pgvector)  │
                                    └─────────────┘
                                         │
                              ┌──────────┴──────────┐
                              │  Embedding Service   │
                              │  (Remote/LitServe)   │
                              └─────────────────────┘
```

---

## Frontend Deployment (Vercel)

### Prerequisites
- GitHub account with the repo pushed
- Vercel account (free tier works)

### Step-by-Step

1. **Connect Repository**
   - Go to [vercel.com](https://vercel.com) → "Add New Project"
   - Import your GitHub repository
   - Set **Root Directory** to `frontend`

2. **Framework Settings**
   - Framework Preset: **Next.js**
   - Build Command: `npm run build` (auto-detected)
   - Output Directory: `.next` (auto-detected)
   - Install Command: `npm install`

3. **Environment Variables** (Settings → Environment Variables)
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   NEXT_PUBLIC_EMBEDDING_URL=https://your-embedding-service.onrender.com
   ```

4. **Deploy**
   - Click "Deploy" — Vercel auto-builds and deploys
   - Get your URL: `https://your-project.vercel.app`

### Custom Domain (Optional)
- Settings → Domains → Add your domain
- Update DNS records as instructed by Vercel

---

## Backend Deployment (Render)

### Prerequisites
- Render account (free tier available)
- PostgreSQL database (Render provides managed instances)

### Step-by-Step

1. **Create PostgreSQL Database**
   - Render Dashboard → "New" → "PostgreSQL"
   - Name: `nexusmind-db`
   - Plan: Free (or Starter for production)
   - Note the **Internal Database URL** and **External Database URL**

2. **Create Web Service**
   - Dashboard → "New" → "Web Service"
   - Connect GitHub repo
   - Set **Root Directory** to `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   GROQ_API_KEY=gsk_your_groq_api_key
   EMBEDDING_SERVICE_URL=https://your-embedding-service.onrender.com
   RERANKER_SERVICE_URL=https://your-reranker.onrender.com
   LLM_PROVIDER=groq
   LLM_MODEL=llama-3.3-70b-versatile
   CORS_ORIGINS=https://your-frontend.vercel.app,https://your-resumegen.vercel.app
   SECRET_KEY=your-secure-random-key-here
   ENVIRONMENT=production
   ```

4. **Health Check Path**: `/health`

5. **Deploy** — Render auto-detects the Dockerfile or buildpack

### Database Migrations
After first deploy, run migrations via Render Shell:
```bash
cd backend
python -c "from app.db.database import init_db; import asyncio; asyncio.run(init_db())"
```

### Resource Note
LaTeX compilation is CPU-intensive. Free tier on Render (512MB RAM, 0.1 CPU) can handle it but may be slow. **Starter plan** ($7/mo, 512MB RAM, 0.5 CPU) is recommended for production use.

---

## Embedding Service (Remote)

The embedding service runs as a separate microservice using LitServe.

### Deployment Options

**Option A: Render Web Service**
1. Create Web Service → Root Dir: `embedding_service`
2. Environment: Docker (uses the Dockerfile in `embedding_service/`)
3. **Requires GPU or sufficient CPU/RAM** — embedding models need ~2GB RAM minimum
4. Environment Variables:
   ```
   PORT=8001
   MODEL_NAME=mixedbread-ai/mxbai-embed-large-v1
   ```

**Option B: RunPod / Modal / Replicate (GPU)**
For better performance, deploy on a GPU service:
- RunPod Serverless: $0.00026/s with GPU
- Modal: Pay per second with GPU
- Hugging Face Inference Endpoints

**Option C: Use Hosted API**
Use third-party embedding APIs:
- OpenAI Embeddings API
- Cohere Embed API
- Voyage AI

### Connecting Remote Embeddings

Update backend environment:
```
EMBEDDING_SERVICE_URL=https://your-embedding-service.onrender.com
```

The backend connects to the embedding service via HTTP:
```
POST /embed
Body: { "texts": ["text1", "text2"], "is_query": false }
Response: { "embeddings": [[0.1, 0.2, ...], ...] }
```

---

## CORS Configuration

### Why CORS Matters
When frontend (Vercel) and backend (Render) are on different domains, browsers block cross-origin requests by default. CORS headers must be configured on the backend.

### Backend CORS Setup (FastAPI)

The main backend (`backend/app/main.py`) configures CORS:

```python
from fastapi.middleware.cors import CORSMiddleware

# In production, list exact origins
origins = [
    "https://your-frontend.vercel.app",
    "https://your-resumegen.vercel.app",
    "http://localhost:3000",  # Local dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

### ResumeGen Backend CORS (`ResumeGen/backend/main.py`)

```python
origins = [
    "https://your-resumegen.vercel.app",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Important CORS Rules
1. **Never use `allow_origins=["*"]` in production** with `allow_credentials=True`
2. Always list exact frontend URLs
3. Update CORS origins when domain changes
4. The Vercel frontend uses API routes (`/api/*`) as a proxy — this avoids CORS for ResumeGen since requests go to the same domain first

### Vercel API Routes (CORS Proxy Pattern)
ResumeGen uses Next.js API routes as a proxy:
```
Browser → Vercel /api/generate-resume → Render backend /generate-resume
```
This eliminates CORS issues because the browser only talks to the Vercel domain.

---

## Environment Variables Reference

### Main Frontend (Vercel)
| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL on Render |
| `NEXT_PUBLIC_EMBEDDING_URL` | No | Direct embedding service URL |

### Main Backend (Render)
| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `GROQ_API_KEY` | Yes | Groq API key for LLM |
| `EMBEDDING_SERVICE_URL` | Yes | Embedding service URL |
| `RERANKER_SERVICE_URL` | No | Reranker service URL |
| `LLM_PROVIDER` | No | `groq` (default) |
| `LLM_MODEL` | No | Model name |
| `CORS_ORIGINS` | Yes | Comma-separated frontend URLs |
| `SECRET_KEY` | Yes | JWT secret key |
| `ENVIRONMENT` | No | `production` |

### ResumeGen Frontend (Vercel)
| Variable | Required | Description |
|----------|----------|-------------|
| `BACKEND_URL` | Yes | ResumeGen backend URL on Render |
| `NEXT_PUBLIC_BACKEND_URL` | Yes | Same as above (client-side fallback) |

### ResumeGen Backend (Render)
| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | No | Port (default: 8000) |
| `CORS_ORIGINS` | Yes | ResumeGen frontend URL |

### Embedding Service (Render / GPU)
| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | No | Port (default: 8001) |
| `MODEL_NAME` | No | Embedding model name |

---

## Resource Constraints & Free Tier Limits

### Vercel Free Tier
| Resource | Limit |
|----------|-------|
| Bandwidth | 100 GB/month |
| Serverless Function Execution | 100 GB-hours/month |
| Serverless Function Duration | 10 seconds (Hobby), 60s (Pro) |
| Build Minutes | 6000 min/month |
| Deployments | Unlimited |
| **Verdict** | ✅ **Sufficient** for frontend + ResumeGen frontend |

### Render Free Tier
| Resource | Limit |
|----------|-------|
| Web Services | 750 hours/month (spins down after 15 min inactivity) |
| RAM | 512 MB |
| CPU | 0.1 shared |
| PostgreSQL | 256 MB storage, expires after 90 days |
| **Verdict** | ⚠️ **Usable for demo** — cold starts of 30-60s after inactivity |

### Will It Run?

| Service | Free Tier Feasible? | Notes |
|---------|-------------------|----|
| Main Frontend | ✅ Yes | Vercel handles static + SSR efficiently |
| Main Backend | ⚠️ Marginal | 512MB RAM tight for FastAPI + LlamaIndex. Works with Groq (no local LLM) |
| ResumeGen Frontend | ✅ Yes | Vercel, lightweight Next.js app |
| ResumeGen Backend | ⚠️ Marginal | LaTeX compilation needs RAM. May timeout on free tier |
| Embedding Service | ❌ Not recommended | Embedding models need 1-2GB+ RAM. Use hosted API instead |
| PostgreSQL | ⚠️ Temporary | Free tier expires after 90 days on Render |

### Recommended Starter Setup ($14/month)
- **Vercel**: Free (frontend)
- **Render Starter**: $7/mo (main backend, 512MB, 0.5 CPU)
- **Render Starter**: $7/mo (ResumeGen backend with LaTeX)
- **Render PostgreSQL**: Free tier (256MB) or $7/mo (1GB)
- **Embeddings**: Use Groq/OpenAI API (pay per use, very cheap)

### Optimizations for Free Tier
1. **Keep backend warm**: Use UptimeRobot to ping `/health` every 14 minutes
2. **Use Groq for LLM**: Free tier with generous limits, avoids running local models
3. **Use hosted embeddings**: OpenAI `text-embedding-3-small` at $0.02/1M tokens
4. **Minimize cold starts**: Reduce dependencies, use slim Docker images

---

## Troubleshooting

### CORS Errors
```
Access to fetch at 'https://backend.onrender.com' from origin 'https://frontend.vercel.app' 
has been blocked by CORS policy
```
**Fix**: Add the exact frontend URL to `CORS_ORIGINS` on the backend. Don't include trailing slashes.

### Vercel Serverless Timeout
```
FUNCTION_INVOCATION_TIMEOUT
```
**Fix**: ResumeGen API route has `maxDuration: 30`. On free tier, limit is 10s. Upgrade to Pro ($20/mo) or optimize LaTeX compilation.

### Render Cold Start
Backend takes 30-60s to respond after inactivity.
**Fix**: Use UptimeRobot to ping `/health` every 14 minutes.

### Embedding Service Out of Memory
```
MemoryError or Killed
```
**Fix**: Use a hosted embedding API instead of self-hosting. Or upgrade to Render Starter (512MB+).

### Database Connection Refused
```
psycopg2.OperationalError: could not connect to server
```
**Fix**: Ensure `DATABASE_URL` uses the **Internal** URL if backend and DB are on the same Render region.

### LaTeX Compilation Failed
```
PDF compilation failed: pdflatex not found
```
**Fix**: Ensure the Docker image includes `texlive-latex-base` and related packages.

---

## Quick Start Checklist

- [ ] Push code to GitHub
- [ ] Create Vercel project for `frontend/`
- [ ] Create Vercel project for `ResumeGen/front/`
- [ ] Create Render PostgreSQL database
- [ ] Create Render web service for `backend/`
- [ ] Create Render web service for `ResumeGen/backend/` (Docker)
- [ ] Set environment variables on all services
- [ ] Configure CORS origins
- [ ] Verify health endpoints
- [ ] Set up UptimeRobot pings (optional)
- [ ] Test end-to-end flow

---

*Documentation maintained by Shivam Sourav — Last updated February 2026*
