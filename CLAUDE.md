# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **NexusMind Studio**, a production-grade Retrieval-Augmented Generation (RAG) system. It consists of a Python FastAPI backend using LlamaIndex for orchestration, a Next.js 14 frontend, a TypeScript MCP server, and a standalone Python embedding microservice. The system supports hybrid search (BM25 + vector), confidence scoring, conversational context, Text2SQL (AuraSQL), resume analysis (Nexus Resume), and LaTeX resume generation.

## Common Commands

### Backend (Python 3.11)

All backend commands assume `cd backend` and an activated virtual environment (`source venv/bin/activate`).

- **Run dev server:** `python -m app.main` (serves on port 8000)
- **Run with reload:** `uvicorn app.main:app --reload --port 8000`
- **Run all tests:** `pytest`
- **Run single test:** `pytest tests/test_core_scorers.py::test_technical_score -v`
- **Install deps:** `pip install -r requirements.txt`
- **Database:** PostgreSQL with `pgvector` extension must be running. Connection configured via `.env`.

### Frontend (Node.js 18+)

All frontend commands assume `cd frontend`.

- **Run dev server:** `npm run dev` (serves on port 3000)
- **Build for production:** `npm run build`
- **Lint:** `npm run lint` (Next.js ESLint)
- **Install deps:** `npm install`

### MCP Server (TypeScript)

All MCP commands assume `cd mcp-server`.

- **Build:** `npm run build` (compiles `src/` to `dist/` via `tsc`)
- **Start:** `npm run start` (runs `node dist/index.js`)
- **No dev/watch script is configured.**

### Embedding Service (Python)

All embedding service commands assume `cd embedding_service`.

- **Run:** `python main.py` (serves on port 8001, requires Ollama)

## Architecture

### Backend (FastAPI)

The backend is a monolithic FastAPI app with a **service singleton pattern** and **LlamaIndex global Settings**.

**Entry point:** `backend/app/main.py`
- `Base.metadata.create_all(bind=engine)` creates SQLAlchemy tables at startup.
- The `lifespan` context manager warms up the `LLMService`, `VectorStoreService`, and `BM25Service` on first request.
- LlamaIndex `Settings.llm` and `Settings.embed_model` are configured globally at startup to prevent OpenAI defaults.

**API Layer:** `backend/app/api/routes/`
- `chat.py`: Dual-mode RAG endpoints (Fast/Think/Ask) with SSE streaming.
- `documents.py`: Document CRUD with user-scoped isolation.
- `auth.py`: JWT login/register with access/refresh tokens.
- `aurasql.py`: Text2SQL endpoints using schema-aware RAG.
- `nexus_resume.py`: Resume upload, analysis, and vector scoring.
- `resumegen.py`: LaTeX resume generation from structured JSON.
- `deps.py`: `get_current_user` dependency extracts JWT from `Authorization: Bearer` header and queries the `User` model.

**Core RAG Engine:** `backend/app/core/`
- `rag_engine.py`: Hybrid RAG pipeline — QueryFusionRetriever (BM25 + vector) → Cohere rerank → LLM generation → ConfidenceScorer.
- `pageindex_rag_engine.py`: Think-mode pipeline — LLM generates document tree → tree search → section retrieval → LLM answer.
- `retriever.py`: `QueryFusionRetriever` wrapping `BM25Service` and `PGVectorStore` with Reciprocal Rank Fusion.
- `confidence_scorer.py`: Multi-factor scoring (retrieval 55%, coherence 25%, coverage 15%, clarity 5%).
- `context_manager.py`: Wraps LlamaIndex `ChatMemoryBuffer` for conversation history.

**Services:** `backend/app/services/`
Services are lazy-loaded singletons accessed via `get_*_service()` factory functions. This is the canonical pattern for obtaining any backend service.
- `llm_service.py`: Manages multiple LLM instances (primary, AuraSQL, structured, Nexus) via Groq/OpenRouter.
- `vector_store.py`: `VectorStoreService` using LlamaIndex `PGVectorStore` for the main RAG index.
- `bm25_service.py`: Keyword search with `rank-bm25`, persisted to `data/bm25_index.pkl`.
- `rag_provider_factory.py`: **Central singleton factory** for embedding model, LLM, and reranker instances. Thread-safe. All other services import from here.
- `document_processor.py`: File ingestion + LlamaIndex `SentenceSplitter` chunking.
- `pageindex_service.py`: Tree generation, storage, and retrieval for Think mode.
- `cohere_service.py`: Cohere embeddings + reranking.
- `remote_embedding_service.py`: HTTP client to the Lightning.ai embedding microservice.
- `aurasql_db.py`: Live database connection introspection for Text2SQL.
- `nexus_resume_service.py`: Resume upload, extraction, analysis orchestration.

**Database:** `backend/app/db/`
- `database.py`: SQLAlchemy engine + session factory. `get_db()` yields sessions.
- Three separate pgvector tables: `rag_embeddings`, `aurasql_embeddings`, `nexus_resume_embeddings`.
- Models include `User`, `ChatSession`, `ChatMessage`, `Document`, `DocumentTreeStructure`, `AuraSqlConnection`, `NexusResumeFile`, etc.

**Configuration:** `backend/app/config.py`
- `Settings(BaseSettings)` loads from `.env`. Uses `pydantic-settings` with `Field(alias="ENV_VAR_NAME")`.
- Key providers: `LLM_PROVIDER` (groq/openrouter), `EMBEDDING_PROVIDER` (remote/cohere/ollama), `RERANKER_PROVIDER` (remote/cohere).

### Frontend (Next.js 14 + App Router)

**Framework:** Next.js 14 App Router, React 18, TypeScript, Tailwind CSS.

**UI Primitives:** shadcn/ui built on Radix UI (`@radix-ui/react-*`). Components live in `frontend/components/ui/` and `frontend/components/`.

**State Management:** Zustand with `persist` middleware.
- `frontend/lib/store.ts`: `useAuthStore` persists user + tokens to `localStorage`.
- Zustand is the standard for all new global state.

**API Client:** `frontend/lib/api.ts`
- `ApiClient` class wraps `fetch` with JWT injection from `useAuthStore`.
- Base URL: `NEXT_PUBLIC_API_BASE_URL` + `/api/v1`.
- All backend types are declared in `frontend/lib/types.ts`.

**Theming:** `frontend/app/layout.tsx`
- Uses `Space_Grotesk` and `IBM_Plex_Mono` fonts.
- `data-theme-palette="graphite" data-theme-mode="dark"` are set on `<html>`.
- `ClientProviders` in `frontend/components/layout/ClientProviders.tsx` wraps app-level providers.

**Key Pages:**
- `/` (root): Chat interface.
- `/aurasql/*`: Text2SQL dashboard.
- `/nexus/*`: Resume analysis and generation.

### MCP Server (TypeScript)

- `mcp-server/src/index.ts`: stdio transport MCP server using `@modelcontextprotocol/sdk`.
- Proxies to backend REST API with bearer-token auth.
- Tools: `health_check`, `chat_query` (fast/think/ask), `list_user_documents`, `list_tools_catalog`.

### Embedding Service (Python)

- `embedding_service/main.py`: FastAPI microservice on port 8001.
- `/api/v1/embeddings`: Ollama `nomic-embed-text-v2-moe` or `embeddinggemma`.
- `/api/v1/rerank`: `sentence-transformers` CrossEncoder (`BAAI/bge-reranker-v2-m3`).
- Designed for remote GPU deployment (e.g., Lightning.ai).

## Key Design Patterns

**Service Singletons:** Never instantiate services directly. Always use `get_llm_service()`, `get_vector_store_service()`, `get_bm25_service()`, etc. These are module-level functions that return cached instances.

**RAG Provider Factory:** `backend/app/services/rag_provider_factory.py` is the single source of truth for `Settings.llm`, `Settings.embed_model`, and reranker instances. If you need to change the LLM or embedding model, this is the file.

**User-Scoped Isolation:** Every document, chat session, analysis job, and resume is filtered by `user_id`. The `get_current_user` dependency enforces this at the API layer.

**Dual-Mode RAG:** The system has two retrieval strategies:
1. **Fast Mode** (`rag_engine.py`): BM25 + vector fusion → rerank → answer. Good for factual lookups.
2. **Think Mode** (`pageindex_rag_engine.py`): LLM navigates a generated document tree to find relevant sections. Good for complex reasoning over long documents.

**Observability:** Langfuse is integrated via LlamaIndex callbacks (`set_global_handler("langfuse")`). Spans are emitted for every retrieval and generation step.

**Streaming:** Chat responses stream via Server-Sent Events (SSE). The backend uses `_iter_llm_tokens` to yield tokens; the frontend consumes them via `EventSource`.

## Deployment

- **Backend:** Docker multi-stage build using `ghcr.io/astral-sh/uv:latest` for fast pip installs. Exposes port 8000.
- **Frontend:** Docker multi-stage build (`node:20-alpine`). Uses Next.js standalone output. Exposes port 3000.
- **No root `docker-compose.yml`**: Each service has its own Dockerfile but there is no top-level orchestration file. The embedding service has its own `docker-compose.yml`.
- **Database:** PostgreSQL + pgvector extension must be provisioned separately.

## Testing

- **Backend:** `pytest` in `backend/tests/`. Tests are not organized into subdirectories; they are flat files prefixed with `test_`.
- **Frontend:** No test framework is configured (no Jest, Vitest, or Playwright in `package.json`).
- **MCP Server:** No test framework configured.

## Environment Variables

The backend requires a `.env` file with:
- `GROQ_API_KEY` or `LLM_API_KEY` + `LLM_PROVIDER`
- `POSTGRES_*` database credentials
- `COHERE_API_KEY` (if using Cohere embeddings/rerank)
- `JWT_SECRET` and `JWT_REFRESH_SECRET`
- `LANGFUSE_*` (optional, for observability)

The frontend requires `.env.local` with:
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- `NEXT_PUBLIC_API_VERSION=v1`
