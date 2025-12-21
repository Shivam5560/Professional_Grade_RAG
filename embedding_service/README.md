# Embedding & Reranking Microservice

A standalone Docker-based microservice providing text embeddings (Ollama) and semantic reranking (HuggingFace).

## Features

- 🚀 **Ollama Embeddings**: Fast text embeddings using embeddinggemma or any Ollama model
- ⚡ **Batch Processing**: Optimized parallel processing with configurable batch sizes (10-50x faster)
- 🔄 **Auto-Retry**: Exponential backoff retry logic for reliability
- 🎯 **BGE Reranking**: State-of-the-art semantic reranking with mixedbread-ai/mxbai-rerank-large-v2
- 📊 **Performance Metrics**: Built-in `/metrics` endpoint for monitoring throughput
- 🐳 **Docker Ready**: Pre-built image with models cached for fast startup
- ☁️ **Cloud Deployable**: Ready for Lightning.ai, AWS, GCP, Azure
- 📡 **REST API**: Simple HTTP endpoints for easy integration

## Performance

**Before Optimization**: Sequential processing (1 text at a time)
- 50 texts × 0.5s = **25 seconds**

**After Optimization**: Batch processing with parallelization
- 50 texts ÷ 10 batch size × 0.5s = **2.5 seconds** (10x faster)
- With 5 concurrent requests: **~1.5 seconds** (16x faster)

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

### Get Performance Metrics

```bash
curl http://localhost:8001/metrics
```

**Response:**
```json
{
  "total_requests": 42,
  "total_texts_processed": 1050,
  "total_time_seconds": 125.3,
  "failed_requests": 1,
  "average_batch_time": 2.98,
  "average_texts_per_request": 25.0,
  "average_texts_per_second": 8.38,
  "configuration": {
    "batch_size": 10,
    "max_concurrent_requests": 5,
    "ollama_model": "embeddinggemma",
    "reranker_model": "mixedbread-ai/mxbai-rerank-large-v2"
  }
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `embeddinggemma` | Ollama model for embeddings |
| `RERANKER_MODEL` | `mixedbread-ai/mxbai-rerank-large-v2` | HuggingFace reranker model |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `EMBEDDING_BATCH_SIZE` | `10` | Number of texts to process per batch |
| `MAX_CONCURRENT_REQUESTS` | `5` | Maximum concurrent Ollama API calls |

### Tuning for Performance

**Small documents (< 20 chunks)**:
```bash
export EMBEDDING_BATCH_SIZE=5
export MAX_CONCURRENT_REQUESTS=3
```

**Medium documents (20-100 chunks)**:
```bash
export EMBEDDING_BATCH_SIZE=10
export MAX_CONCURRENT_REQUESTS=5
```

**Large documents (100+ chunks)**:
```bash
export EMBEDDING_BATCH_SIZE=20
export MAX_CONCURRENT_REQUESTS=10
```

**Note**: Higher concurrency requires more CPU/memory. Start conservative and increase based on monitoring.

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
  OLLAMA_MODEL: embeddinggemma
  RERANKER_MODEL: mixedbread-ai/mxbai-rerank-large-v2
  EMBEDDING_BATCH_SIZE: 10
  MAX_CONCURRENT_REQUESTS: 5

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

The backend already integrates with this service. Ensure these settings are configured:

**Backend `.env` file:**
```bash
# Enable remote embedding service
USE_REMOTE_EMBEDDING_SERVICE=true
REMOTE_EMBEDDING_SERVICE_URL=https://your-lightning-app.cloudspaces.litng.ai

# Embedding configuration
EMBEDDING_BATCH_SIZE=10
EMBEDDING_REQUEST_TIMEOUT=120
```

The backend automatically:
- Batches embedding requests for efficiency
- Retries failed requests with exponential backoff (3 attempts)
- Adjusts timeout dynamically based on batch size
- Logs detailed performance metrics

## Retry Logic & Reliability

Both the embedding service and backend client implement automatic retry with exponential backoff:

**Embedding Service:**
- 3 retry attempts per text
- Initial wait: 1s, max wait: 10s
- Retries on any Ollama API errors

**Backend Client:**
- 3 retry attempts per batch
- Initial wait: 2s, max wait: 30s
- Retries on timeout and HTTP errors only

**Total resilience**: Up to 9 attempts for each text (3 service-level × 3 client-level)

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

## Monitoring & Observability

### Logs

Access container logs:
```bash
docker logs -f embedding-reranking-service
```

Logs are structured JSON with detailed information:
```json
{
  "event": "embedding_request_received",
  "num_texts": 50,
  "model": "embeddinggemma",
  "batch_size": 10,
  "timestamp": "2025-12-21T10:30:15.123456Z"
}
{
  "event": "processing_batch",
  "batch_num": 1,
  "batch_size": 10,
  "total_batches": 5
}
{
  "event": "batch_complete",
  "batch_size": 10,
  "time_seconds": 0.52,
  "texts_per_second": 19.23
}
{
  "event": "all_embeddings_complete",
  "total_texts": 50,
  "total_time_seconds": 2.34,
  "texts_per_second": 21.37
}
```

### Metrics Endpoint

Monitor real-time performance:
```bash
curl http://localhost:8001/metrics
```

Key metrics to watch:
- `average_texts_per_second`: Throughput indicator (target: > 10)
- `failed_requests`: Error rate (target: < 1%)
- `average_batch_time`: Latency indicator (target: < 5s)

### Health Checks

```bash
curl http://localhost:8001/health
```

Returns service status and configuration.

## Troubleshooting

**Slow performance?**
- Increase `MAX_CONCURRENT_REQUESTS` (default: 5)
- Ensure Ollama is running locally or accessible
- Check `/metrics` for bottlenecks

**Timeout errors?**
- Backend automatically adjusts timeout based on batch size
- For very large batches (> 100 texts), increase `EMBEDDING_REQUEST_TIMEOUT` in backend config

**Memory issues?**
- Reduce `EMBEDDING_BATCH_SIZE` and `MAX_CONCURRENT_REQUESTS`
- Monitor container memory with `docker stats`

## License

MIT
