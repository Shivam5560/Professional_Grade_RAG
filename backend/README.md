# Professional RAG System - Backend

## Overview

Professional-grade RAG (Retrieval-Augmented Generation) system with advanced features:
- **Hybrid Search**: BM25 + Vector Search + Reranking
- **Confidence Scoring**: Multi-factor confidence assessment
- **Conversational Context**: Chat history integration
- **LlamaIndex Orchestration**: Modular and composable architecture

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/) installed and running
- Required Ollama models:
  ```bash
  ollama pull embeddinggemma
  ollama pull gemma3:4b
  ollama pull bge-reranker-v2-m3
  ```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and adjust settings:
```bash
cp .env.example .env
```

### 3. Run the Server

```bash
# Development mode (with auto-reload)
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Verify Installation

Visit:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

## API Endpoints

### Health
- `GET /api/v1/health` - System health status

### Chat
- `POST /api/v1/chat/query` - Query the RAG system
- `GET /api/v1/chat/history/{session_id}` - Get chat history
- `DELETE /api/v1/chat/history/{session_id}` - Clear chat history

### Documents
- `POST /api/v1/documents/upload` - Upload a document
- `GET /api/v1/documents/list` - List documents
- `DELETE /api/v1/documents/{document_id}` - Delete a document

## Example Usage

### Query Example

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/chat/query",
    json={
        "query": "What is machine learning?",
        "session_id": "my-session-123"
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence_score']}%")
print(f"Sources: {len(result['sources'])}")
```

### Document Upload Example

```python
import requests

with open("document.txt", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/documents/upload",
        files={"file": f},
        data={"title": "My Document", "category": "Technical"}
    )

result = response.json()
print(f"Document ID: {result['document_id']}")
print(f"Chunks created: {result['chunks_created']}")
```

## Configuration

Key settings in `.env`:

```bash
# Ollama models
OLLAMA_LLM_MODEL=gemma3:4b
OLLAMA_EMBEDDING_MODEL=gemma

# RAG settings
CHUNK_SIZE=512
CHUNK_OVERLAP=128  # 25% overlap
TOP_K_RETRIEVAL=10
TOP_K_RERANK=5

# Confidence scoring weights
WEIGHT_RETRIEVAL=0.40
WEIGHT_COHERENCE=0.30
WEIGHT_COVERAGE=0.20
WEIGHT_CLARITY=0.10
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── models/              # Pydantic models & prompts
│   ├── services/            # External services (Ollama, ChromaDB, BM25)
│   ├── core/                # Core RAG logic (engine, retriever, scorer)
│   ├── api/                 # API routes & middleware
│   └── utils/               # Utilities (logging, validation)
├── data/                    # Data storage (created automatically)
├── requirements.txt
├── Dockerfile
└── .env
```

## Docker Deployment

```bash
# Build image
docker build -t rag-backend .

# Run container
docker run -p 8000:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v $(pwd)/data:/app/data \
  rag-backend
```

## Development

### Adding New Features

1. **New Endpoint**: Add route in `app/api/routes/`
2. **New Service**: Add service in `app/services/`
3. **Core Logic**: Modify `app/core/rag_engine.py`

### Logging

Structured JSON logging with structlog:

```python
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("event_name", key1="value1", key2="value2")
```

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Pull required models
ollama pull gemma
ollama pull gemma3:4b
```

### ChromaDB Persistence
- Data stored in `./data/chroma_db/`
- Delete folder to reset database

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Performance Tips

1. **Adjust chunk size** based on document type
2. **Tune retrieval parameters** (top_k, similarity_threshold)
3. **Monitor confidence scores** to calibrate weights
4. **Use Docker** for consistent deployment

## License

MIT License - See LICENSE file for details
