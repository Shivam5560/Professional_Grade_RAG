FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Install system dependencies needed for building python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Create a virtual environment and install dependencies without cache
RUN uv venv /opt/venv && \
    uv pip install --no-cache --python /opt/venv -r requirements.txt

# Final stage - minimal slim image
FROM python:3.11-slim

WORKDIR /app

# Copy the built virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Make sure we use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY app ./app

# Create data directories
RUN mkdir -p ./data/chroma_db ./data/documents

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
