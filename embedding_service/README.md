# Embedding & Reranking Microservice

A standalone Docker-based microservice providing text embeddings (Ollama) and semantic reranking (HuggingFace BGE).

## Features

- 🚀 **Ollama Embeddings**: Fast text embeddings using gemma:2b or any Ollama model
- 🎯 **BGE Reranking**: State-of-the-art semantic reranking with BAAI/bge-reranker-v2-m3
- 🐳 **Docker Ready**: Pre-built image with models cached for fast startup
- ☁️ **Cloud Deployable**: Ready for Lightning.ai, AWS, GCP, Azure
- 📊 **REST API**: Simple HTTP endpoints for easy integration

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
docker-compose up -d
```

Service will be available at `http://localhost:8001`

### Option 2: Manual Docker Build

```bash
# Build image
docker build -t embedding-service .

# Run container
docker run -p 8001:8001 embedding-service
```

### Option 3: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install and start Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &

# Pull model
ollama pull gemma:2b

# Run service
uvicorn main:app --host 0.0.0.0 --port 8001
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8001/health
```

### Generate Embeddings

```bash
curl -X POST http://localhost:8001/api/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello world", "How are you?"]
  }'
```

**Response:**
```json
{
  "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
  "dimension": 768,
  "model": "gemma:2b"
}
```

### Rerank Documents

```bash
curl -X POST http://localhost:8001/api/v1/rerank \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "documents": [
      "Machine learning is a subset of AI",
      "Python is a programming language",
      "Deep learning uses neural networks"
    ],
    "top_k": 2
  }'
```

**Response:**
```json
{
  "results": [
    {
      "index": 0,
      "text": "Machine learning is a subset of AI",
      "score": 0.95
    },
    {
      "index": 2,
      "text": "Deep learning uses neural networks",
      "score": 0.78
    }
  ],
  "model": "BAAI/bge-reranker-v2-m3"
}
```

### List Available Models

```bash
curl http://localhost:8001/api/v1/models
```

## Deploy to Lightning.ai

### Step 1: Create `lightning.yaml`

```yaml
name: embedding-service

cluster:
  compute: cpu-medium
  disk_size: 50

build:
  dockerfile: Dockerfile

run:
  - uvicorn main:app --host 0.0.0.0 --port 8001

env:
  OLLAMA_MODEL: gemma:2b
  RERANKER_MODEL: BAAI/bge-reranker-v2-m3

expose:
  - port: 8001
    protocol: http
```

### Step 2: Deploy

```bash
# Install Lightning CLI
pip install lightning

# Login
lightning login

# Deploy
lightning deploy
```

### Step 3: Get Endpoint URL

Lightning.ai will provide a URL like:
```
https://your-app.lightning.dev
```

## Integration with Main RAG Backend

Update your main backend to use this service:

```python
# backend/app/services/embedding_service.py

import httpx

class RemoteEmbeddingService:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def get_embeddings(self, texts: list[str]):
        response = await self.client.post(
            f"{self.base_url}/api/v1/embeddings",
            json={"texts": texts}
        )
        return response.json()

# backend/app/core/reranker.py

class RemoteReranker:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def rerank(self, query: str, documents: list[str], top_k: int = 5):
        response = await self.client.post(
            f"{self.base_url}/api/v1/rerank",
            json={
                "query": query,
                "documents": documents,
                "top_k": top_k
            }
        )
        return response.json()
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `gemma:2b` | Ollama model for embeddings |
| `RERANKER_MODEL` | `BAAI/bge-reranker-v2-m3` | HuggingFace reranker model |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |

## Performance

- **Model Caching**: Models are downloaded during Docker build, eliminating startup delays
- **Batch Embeddings**: Process multiple texts in one request
- **GPU Support**: Add `--gpus all` to docker run for GPU acceleration

## Cloud Deployment Options

### Lightning.ai (Recommended)
- Easy deployment with `lightning deploy`
- Auto-scaling
- Built-in monitoring

### AWS ECS
```bash
# Build and push to ECR
docker build -t embedding-service .
docker tag embedding-service:latest <account>.dkr.ecr.us-east-1.amazonaws.com/embedding-service
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/embedding-service
```

### Google Cloud Run
```bash
gcloud run deploy embedding-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Container Apps
```bash
az containerapp up \
  --name embedding-service \
  --source . \
  --target-port 8001
```

## Monitoring

Access logs:
```bash
docker logs -f embedding-reranking-service
```

Logs are structured JSON for easy parsing:
```json
{
  "event": "embedding_request",
  "num_texts": 5,
  "model": "gemma:2b",
  "timestamp": "2025-12-19T18:54:10.441516Z"
}
```

## License

MIT
