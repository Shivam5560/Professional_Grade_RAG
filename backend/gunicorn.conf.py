"""
Gunicorn production configuration for Nexus Backend.

Tuned for: Intel i3-7100U (2 cores / 4 threads), 4-8 GB RAM.
Each worker loads ~400-500 MB (numpy, pandas, spacy, statsmodels, scikit-learn).

Usage:
    gunicorn -c gunicorn.conf.py app.main:app
"""

import multiprocessing
import os

# ── Workers ──────────────────────────────────────────────────────────────────
# Formula: min(2 * CPU_cores, RAM_safe_limit)
# i3-7100U = 2 cores.  Each worker ≈ 400-500 MB.
# 2 workers = ~1 GB for Python + OS + DB overhead = safe for 4-8 GB RAM.
# Override at runtime: GUNICORN_WORKERS=3 docker run ...
workers = int(os.getenv("GUNICORN_WORKERS", min(2, multiprocessing.cpu_count())))

# UvicornWorker gives us async ASGI support inside each gunicorn worker.
worker_class = "uvicorn.workers.UvicornWorker"

# ── Binding ──────────────────────────────────────────────────────────────────
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# ── Timeouts ─────────────────────────────────────────────────────────────────
# Analysis workflows can take 5-15 minutes; graceful_timeout lets in-flight
# analysis jobs finish during hot restarts.
timeout = int(os.getenv("GUNICORN_TIMEOUT", 900))       # 15 min — matches ANALYSIS_WORKFLOW_TIMEOUT
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 120))  # 2 min for graceful shutdown
keepalive = 5  # seconds to wait for next request on a keep-alive connection

# ── Worker lifecycle ─────────────────────────────────────────────────────────
# Restart workers after N requests to prevent memory leaks from long-running
# scientific Python operations (pandas/numpy/plotly can fragment memory).
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = 50  # randomize restart to avoid thundering herd

# Pre-load the app in the master process, then fork.
# Saves ~100-200 MB RAM via copy-on-write (numpy/pandas shared pages).
preload_app = True

# ── Logging ──────────────────────────────────────────────────────────────────
accesslog = "-"   # stdout
errorlog = "-"    # stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'

# ── Security & Limits ────────────────────────────────────────────────────────
# Limit request line and header sizes to prevent abuse.
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# ── Server Mechanics ─────────────────────────────────────────────────────────
# Reuse port allows zero-downtime restarts.
reuse_port = True

# tmp file-based worker heartbeat (works in Docker without /dev/shm issues).
worker_tmp_dir = "/dev/shm"

# Forward proxy headers (NGINX / cloud load balancer in front).
forwarded_allow_ips = os.getenv("GUNICORN_FORWARDED_ALLOW_IPS", "*")
proxy_protocol = False
