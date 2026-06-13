"""
Main FastAPI application entry point.
Professional-grade RAG system with LlamaIndex orchestration.
Uses Groq for LLM inference and PostgreSQL for vector storage.
"""

import logging
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from llama_index.core import Settings
from app.config import settings
from app.utils.logger import get_logger
from app.api.middleware import setup_middleware
from app.api.routes import chat, documents, health, auth, history
from app.api.routes import nexus_resume
from app.api.routes import aurasql
from app.api.routes import resumegen
from app.api.routes import analysis
from app.api.routes import workflows
from app.api.routes import notifications
from app import __version__
from app.db.database import engine, Base
from app.services.messaging import consume_notifications
from app.observability import (
    flush_langfuse,
    log_langfuse_startup_status,
)

logger = get_logger(__name__)

# Create tables at import time (non-blocking — will fail fast if DB unreachable)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"Table creation skipped (DB may not be available): {e}")


async def _warmup_services() -> None:
    """Warm up services in background with a hard timeout of 30 seconds."""
    try:
        async with asyncio.timeout(30):
            from app.services.llm_service import get_llm_service
            from app.services.vector_store import get_vector_store_service
            from app.services.bm25_service import get_bm25_service

            llm_svc = get_llm_service()
            vector_store = get_vector_store_service()
            bm25_service = get_bm25_service()

            embed_model = vector_store.embed_model

            Settings.llm = llm_svc.get_llm()
            Settings.embed_model = embed_model
            Settings.chunk_size = settings.chunk_size
            Settings.chunk_overlap = settings.chunk_overlap

            logger.log_operation(
                "LlamaIndex settings configured",
                llm_provider=settings.llm_provider,
                llm_model=llm_svc.model,
                embed_provider=settings.embedding_provider,
                chunk_size=settings.chunk_size,
            )

            # LLM health check is best-effort, not blocking
            try:
                async with asyncio.timeout(10):
                    await llm_svc.check_health()
            except asyncio.TimeoutError:
                logger.warning("LLM health check timed out — continuing anyway")
            except Exception as e:
                logger.warning(f"LLM health check failed: {e}")

            logger.log_operation("Services warmed up")

    except asyncio.TimeoutError:
        logger.warning("Service warmup timed out after 30s — services will lazy-load on first request")
    except Exception as e:
        logger.log_error("Service warmup", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    Warmup runs in background — the API is ready immediately.
    """
    # Startup
    settings.validate_security_posture()
    log_langfuse_startup_status()
    logger.log_operation(
        "Application starting",
        version=__version__,
        environment=settings.log_level,
    )

    # Fire-and-forget warmup — don't block API readiness
    warmup_task = asyncio.create_task(_warmup_services())


    # Start notifications consumer
    consumer_task = asyncio.create_task(consume_notifications())

    logger.log_operation("API ready")


    yield

    # Shutdown
    warmup_task.cancel()
    try:
        await warmup_task
    except asyncio.CancelledError:
        pass


    # Shutdown consumer
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    logger.log_operation("Application shutting down")

    flush_langfuse()
    logger.log_operation("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Professional RAG System",
    description="Advanced RAG system with hybrid search, confidence scoring, and conversational context",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup middleware
setup_middleware(app)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1/history", tags=["History"])
app.include_router(aurasql.router, prefix="/api/v1", tags=["AuraSQL"])
app.include_router(nexus_resume.router, prefix="/api/v1", tags=["Nexus Resume"])
app.include_router(resumegen.router, prefix="/api/v1", tags=["Resume Generator"])
app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(workflows.router, prefix="/api/v1", tags=["Workflows"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Professional RAG System",
        "version": __version__,
        "status": "online",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1")
async def api_info():
    """API version information."""
    return {
        "version": "v1",
        "endpoints": {
            "health": "/api/v1/health",
            "chat": "/api/v1/chat/query",
            "history": "/api/v1/chat/history/{session_id}",
            "upload": "/api/v1/documents/upload",
            "documents": "/api/v1/documents/list",
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        reload_excludes=["data", "data/*", "data/**/*", "*.pptx", "*.png", "*.json"],
        log_level=settings.log_level.lower(),
    )
