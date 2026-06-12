# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Install system build deps (only needed at build time, NOT copied to final image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Create venv and install all Python deps — no cache to keep layer small
RUN uv venv /opt/venv && \
    uv pip install --no-cache --python /opt/venv -r requirements.txt && \
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -name "*.pyc" -delete && \
    find /opt/venv -name "*.pyo" -delete

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy the pre-built venv
COPY --from=builder /opt/venv /opt/venv

# Copy gunicorn production config
COPY gunicorn.conf.py .

# Copy application source
COPY app ./app

# Create ALL runtime data directories
RUN mkdir -p \
    ./data/chroma_db \
    ./data/documents \
    ./data/resumes \
    ./data/analysis_uploads \
    ./data/analysis_charts \
    ./data/analysis_slides

EXPOSE 8000

# Production: gunicorn manages workers, uvicorn handles async ASGI per worker.
# - 2 workers (tuned for 2-core i3-7100U)
# - 15-min timeout (analysis workflows are long-running)
# - Auto-restart after 1000 requests (prevents memory leaks)
# - preload_app for copy-on-write RAM savings
# Override workers at runtime: docker run -e GUNICORN_WORKERS=3 ...
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]
