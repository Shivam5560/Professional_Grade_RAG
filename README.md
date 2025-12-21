m# Professional-Grade RAG System

A production-ready Retrieval-Augmented Generation (RAG) system with advanced features including hybrid search, confidence scoring, and conversational context management.

## 🌟 Features

### Core Capabilities
- **Hybrid Search**: Combines BM25 keyword search with semantic vector search
- **Intelligent Reranking**: Uses mxbai-rerank-large-v2 for optimal result ordering
- **Confidence Scoring**: Multi-factor confidence assessment (retrieval, coherence, coverage, clarity)
- **Conversational Context**: Maintains chat history for follow-up questions
- **Source Citations**: Every answer includes traceable source references
- **Professional UI**: Modern Next.js interface with real-time updates

### Technical Highlights
- **LlamaIndex Orchestration**: Modular, composable RAG pipeline
- **Groq Integration**: High-performance LLM inference (OpenAI gpt-oss 20b)
- **PostgreSQL + pgvector**: Robust vector storage and retrieval
- **Flexible Embeddings**: Support for local Ollama or remote embedding services
- **Type-Safe**: Full TypeScript support in frontend

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL** with `pgvector` extension
- **Groq API Key**
- **Ollama** 

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GROQ_API_KEY and DB settings

# Start backend
python -m app.main
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local

# Start development server
npm run dev
```

### 3. Embedding Service (Optional)

If using the standalone embedding service:

```bash
cd embedding-service
ollama pull embeddinggemma
python main.py
```


### Query via UI

1. Open http://localhost:3000
2. Type your question in the input box
3. View answer with:
   - Confidence score (%)
   - Confidence level (high/medium/low)
   - Source citations with relevance scores

## 🏗️ Architecture

```
┌─────────────┐
│   Next.js   │  ← User Interface
│  Frontend   │
└──────┬──────┘
       │ REST API
┌──────▼──────┐
│   FastAPI   │  ← API Layer
│   Backend   │
└──────┬──────┘
       │
┌──────▼──────────────────┐
│  LlamaIndex Pipeline    │  ← RAG Orchestration
│  - Hybrid Retriever     │
│  - BGE Reranker         │
│  - Confidence Scorer    │
│  - Context Manager      │
└──────┬──────────────────┘
       │
┌──────┴─────┬─────────┬──────────┐
│ PostgreSQL │  Groq   │   BM25   │  ← Storage & Models
│ (pgvector) │  (LLM)  │  (Index) │
└────────────┴─────────┴──────────┘
```

## 📂 Project Structure

```
Professional_Grade_RAG/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # RAG engine, retriever, scorer
│   │   ├── models/         # Pydantic models, prompts
│   │   ├── services/       # Groq, Postgres, BM25
│   │   └── utils/          # Logging, validation
│   ├── data/               # Document storage
│   └── requirements.txt
├── frontend/               # Next.js Frontend
│   ├── app/               # Pages and layouts
│   ├── components/        # React components
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # API client, utilities
│   └── package.json
├── embedding-service/     # Standalone Embedding Service
│   ├── main.py
│   └── docker-compose.yml
└── README.md            # This file
```

## ⚙️ Configuration

### Backend Environment Variables

```bash
# Groq API
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=openai/gpt-oss-20b

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rag_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Embeddings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=embeddinggemma
USE_REMOTE_EMBEDDING_SERVICE=false

# RAG Settings
CHUNK_SIZE=512
CHUNK_OVERLAP=128
TOP_K_RETRIEVAL=10
TOP_K_RERANK=5
```

### Frontend Environment Variables

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1
```

## 🎯 Confidence Scoring

The system calculates confidence using four factors:

1. **Retrieval Score (55%)**: Quality of retrieved documents
2. **Answer Coherence (25%)**: LLM self-assessment
3. **Source Coverage (15%)**: Number and distribution of sources
4. **Query Clarity (5%)**: Quality of query understanding

**Confidence Levels:**
- 🟢 **High (80-100%)**: Strong evidence from multiple sources
- 🟡 **Medium (50-79%)**: Moderate evidence, some ambiguity
- 🔴 **Low (<50%)**: Weak evidence, insufficient data

## 🔧 Troubleshooting

### Database Connection
Ensure PostgreSQL is running and the `pgvector` extension is installed:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Groq API
Verify your API key is valid and set in the `.env` file.

## 📈 Performance Tips

1. **Chunk Size**: Adjust `CHUNK_SIZE` based on document type
2. **Top-K Values**: Tune `TOP_K_RETRIEVAL` and `TOP_K_RERANK`
3. **Confidence Weights**: Calibrate weights based on your use case

## 🛠️ Development

### Adding New Features

**Backend:**
1. Add route in `backend/app/api/routes/`
2. Implement logic in `backend/app/core/` or `backend/app/services/`
3. Update schemas in `backend/app/models/schemas.py`

**Frontend:**
1. Create component in `frontend/components/`
2. Add to page in `frontend/app/page.tsx`
3. Update types in `frontend/lib/types.ts`


## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **LlamaIndex**: RAG orchestration framework
- **Ollama**: Local LLM inference
- **ChromaDB**: Vector database
- **shadcn/ui**: UI component library
- **FastAPI**: Modern Python web framework
- **Next.js**: React framework

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs: `docker-compose logs`
3. Consult `PLAN.md` for architecture details

---

**Built with ❤️ for professional RAG applications**
