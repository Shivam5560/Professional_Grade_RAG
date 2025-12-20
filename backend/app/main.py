"""
Main FastAPI application entry point.
Professional-grade RAG system with LlamaIndex orchestration.
Uses Groq for LLM inference and PostgreSQL for vector storage.
"""

import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from llama_index.core import Settings
from app.config import settings
from app.utils.logger import get_logger
from app.api.middleware import setup_middleware
from app.api.routes import chat, documents, health, auth, history
from app import __version__
from app.db.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "application_starting",
        version=__version__,
        environment=settings.log_level,
    )
    
    # Initialize services (lazy loading will occur on first use)
    from app.services.groq_service import get_groq_service
    from app.services.vector_store import get_vector_store_service
    from app.services.bm25_service import get_bm25_service
    
    try:
        # Warm up services
        groq_service = get_groq_service()
        vector_store = get_vector_store_service()
        bm25_service = get_bm25_service()
        
        # Configure embedding model based on settings
        if settings.use_remote_embedding_service:
            from app.services.remote_embedding_service import RemoteEmbeddingService
            embed_model = RemoteEmbeddingService(
                base_url=settings.remote_embedding_service_url,
                model_name=settings.ollama_embedding_model
            )
            logger.info(
                "remote_embedding_service_configured",
                url=settings.remote_embedding_service_url,
                model=settings.ollama_embedding_model
            )
        else:
            from app.services.ollama_service import get_ollama_service
            ollama_service = get_ollama_service()
            embed_model = ollama_service.get_embed_model()
            ollama_healthy = await ollama_service.check_health()
            if not ollama_healthy:
                logger.warning("ollama_embeddings_not_available_on_startup")
        
        # Configure LlamaIndex global Settings to prevent OpenAI defaults
        Settings.llm = groq_service.get_llm()
        Settings.embed_model = embed_model
        Settings.chunk_size = settings.chunk_size
        Settings.chunk_overlap = settings.chunk_overlap
        
        logger.info(
            "llamaindex_settings_configured",
            llm_model=settings.groq_model,
            embed_model=settings.ollama_embedding_model,
            chunk_size=settings.chunk_size,
            remote_embeddings=settings.use_remote_embedding_service
        )
        
        groq_healthy = await groq_service.check_health()
        if not groq_healthy:
            logger.warning("groq_llm_not_available_on_startup")
        
        logger.info("services_initialized")
        
    except Exception as e:
        logger.error("service_initialization_failed", error=str(e))
    
    logger.info("application_started")
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    
    # Cleanup if needed
    logger.info("application_shutdown_complete")


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
        log_level=settings.log_level.lower(),
    )
