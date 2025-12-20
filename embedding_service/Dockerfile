# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download models during build (cached in image)
# This speeds up container startup significantly
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-reranker-v2-m3')"

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start Ollama in background and run the FastAPI app
CMD ollama serve & \
    sleep 5 && \
    ollama pull embeddinggemma && \
    uvicorn main:app --host 0.0.0.0 --port 8001
