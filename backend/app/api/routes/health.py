"""
Health check endpoints.
"""

from fastapi import APIRouter, status
from app.models.schemas import HealthResponse
from app.services.ollama_service import get_ollama_service
from app.services.groq_service import get_groq_service
from app.services.vector_store import get_vector_store_service
from app.services.bm25_service import get_bm25_service
from app.config import settings
from app.utils.logger import get_logger
from app import __version__
import httpx

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Check the health of the application and its components.
    
    Returns:
        HealthResponse with status of all components
    """
    try:
        # Check Ollama service (embeddings only)
        ollama_service = get_ollama_service()
        ollama_healthy = await ollama_service.check_health()
        
        # Check Groq service (LLM)
        groq_service = get_groq_service()
        groq_healthy = await groq_service.check_health()
        
        # Check vector store (PostgreSQL)
        vector_store = get_vector_store_service()
        postgres_healthy = vector_store.check_health()
        
        # Check BM25 service
        bm25_service = get_bm25_service()
        bm25_stats = bm25_service.get_stats()
        bm25_healthy = bm25_stats.get("index_available", False)
        
        # Determine overall status
        all_healthy = ollama_healthy and groq_healthy and postgres_healthy
        
        if all_healthy:
            overall_status = "healthy"
        elif groq_healthy or postgres_healthy:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        components = {
            "ollama_embeddings": "connected" if ollama_healthy else "disconnected",
            "groq_llm": "connected" if groq_healthy else "disconnected",
            "postgres_vector_store": "connected" if postgres_healthy else "disconnected",
            "bm25_index": "loaded" if bm25_healthy else "not_loaded",
        }
        
        logger.info("health_check_completed", status=overall_status, components=components)
        
        return HealthResponse(
            status=overall_status,
            components=components,
            version=__version__
        )
        
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        
        return HealthResponse(
            status="unhealthy",
            components={
                "ollama_embeddings": "unknown",
                "groq_llm": "unknown",
                "postgres_vector_store": "unknown",
                "bm25_index": "unknown",
            },
            version=__version__
        )


@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping_services():
    """
    Comprehensive health check endpoint to keep all services alive.
    Checks and pings:
    - Embedding services (remote or local Ollama)
    - Reranking services (remote or local)
    - LLM service (Groq)
    - Database (PostgreSQL with pgvector)
    - BM25 index
    
    Returns:
        Detailed status of all services with individual health checks
    """
    import datetime
    
    results = {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "services": {},
        "summary": {
            "total": 0,
            "healthy": 0,
            "unhealthy": 0
        }
    }
    
    try:
        # 1. Check Embedding Service (Remote or Local)
        if settings.use_remote_embedding_service:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{settings.remote_embedding_service_url}/health"
                    )
                    if response.status_code == 200:
                        results["services"]["embedding"] = {
                            "type": "remote",
                            "status": "healthy",
                            "url": settings.remote_embedding_service_url
                        }
                        logger.info("ping_remote_embedding_success")
                        results["summary"]["healthy"] += 1
                    else:
                        results["services"]["embedding"] = {
                            "type": "remote",
                            "status": "unhealthy",
                            "error": f"HTTP {response.status_code}"
                        }
                        results["summary"]["unhealthy"] += 1
            except Exception as e:
                logger.warning("ping_remote_embedding_failed", error=str(e))
                results["services"]["embedding"] = {
                    "type": "remote",
                    "status": "unhealthy",
                    "error": str(e)
                }
                results["summary"]["unhealthy"] += 1
        else:
            try:
                ollama_service = get_ollama_service()
                if await ollama_service.check_health():
                    results["services"]["embedding"] = {
                        "type": "local_ollama",
                        "status": "healthy",
                        "model": settings.ollama_embedding_model
                    }
                    logger.info("ping_ollama_embedding_success")
                    results["summary"]["healthy"] += 1
                else:
                    results["services"]["embedding"] = {
                        "type": "local_ollama",
                        "status": "unhealthy",
                        "error": "Health check failed"
                    }
                    results["summary"]["unhealthy"] += 1
            except Exception as e:
                logger.warning("ping_ollama_embedding_failed", error=str(e))
                results["services"]["embedding"] = {
                    "type": "local_ollama",
                    "status": "unhealthy",
                    "error": str(e)
                }
                results["summary"]["unhealthy"] += 1
        
        results["summary"]["total"] += 1
        
        # 2. Check Reranking Service (Remote or Local)
        if settings.use_remote_embedding_service:
            # Remote reranker (same service as embeddings)
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{settings.remote_embedding_service_url}/health"
                    )
                    if response.status_code == 200:
                        results["services"]["reranker"] = {
                            "type": "remote",
                            "status": "healthy",
                            "url": settings.remote_embedding_service_url
                        }
                        logger.info("ping_remote_reranker_success")
                        results["summary"]["healthy"] += 1
                    else:
                        results["services"]["reranker"] = {
                            "type": "remote",
                            "status": "unhealthy",
                            "error": f"HTTP {response.status_code}"
                        }
                        results["summary"]["unhealthy"] += 1
            except Exception as e:
                logger.warning("ping_remote_reranker_failed", error=str(e))
                results["services"]["reranker"] = {
                    "type": "remote",
                    "status": "unhealthy",
                    "error": str(e)
                }
                results["summary"]["unhealthy"] += 1
        else:
            # Local CrossEncoder reranker (always available if installed)
            try:
                results["services"]["reranker"] = {
                    "type": "local_crossencoder",
                    "status": "healthy",
                    "model": "BAAI/bge-reranker-v2-m3"
                }
                logger.info("local_reranker_available")
                results["summary"]["healthy"] += 1
            except Exception as e:
                results["services"]["reranker"] = {
                    "type": "local_crossencoder",
                    "status": "unhealthy",
                    "error": str(e)
                }
                results["summary"]["unhealthy"] += 1
        
        results["summary"]["total"] += 1
        
        # 3. Check Groq LLM Service
        try:
            groq_service = get_groq_service()
            if await groq_service.check_health():
                results["services"]["llm"] = {
                    "type": "groq",
                    "status": "healthy",
                    "model": settings.groq_model
                }
                logger.info("ping_groq_success")
                results["summary"]["healthy"] += 1
            else:
                results["services"]["llm"] = {
                    "type": "groq",
                    "status": "unhealthy",
                    "error": "Health check failed"
                }
                results["summary"]["unhealthy"] += 1
        except Exception as e:
            logger.warning("ping_groq_failed", error=str(e))
            results["services"]["llm"] = {
                "type": "groq",
                "status": "unhealthy",
                "error": str(e)
            }
            results["summary"]["unhealthy"] += 1
        
        results["summary"]["total"] += 1
        
        # 4. Check PostgreSQL Vector Store
        try:
            vector_store = get_vector_store_service()
            if vector_store.check_health():
                results["services"]["database"] = {
                    "type": "postgresql_pgvector",
                    "status": "healthy",
                    "host": settings.postgres_host,
                    "database": settings.postgres_db
                }
                logger.info("ping_postgres_success")
                results["summary"]["healthy"] += 1
            else:
                results["services"]["database"] = {
                    "type": "postgresql_pgvector",
                    "status": "unhealthy",
                    "error": "Connection failed"
                }
                results["summary"]["unhealthy"] += 1
        except Exception as e:
            logger.warning("ping_postgres_failed", error=str(e))
            results["services"]["database"] = {
                "type": "postgresql_pgvector",
                "status": "unhealthy",
                "error": str(e)
            }
            results["summary"]["unhealthy"] += 1
        
        results["summary"]["total"] += 1
        
        # 5. Check BM25 Index
        try:
            bm25_service = get_bm25_service()
            bm25_stats = bm25_service.get_stats()
            if bm25_stats.get("index_available", False):
                results["services"]["bm25"] = {
                    "type": "local_index",
                    "status": "healthy",
                    "documents": bm25_stats.get("num_documents", 0)
                }
                logger.info("ping_bm25_success")
                results["summary"]["healthy"] += 1
            else:
                results["services"]["bm25"] = {
                    "type": "local_index",
                    "status": "degraded",
                    "message": "No documents indexed"
                }
                results["summary"]["healthy"] += 1  # Still counts as healthy
        except Exception as e:
            logger.warning("ping_bm25_failed", error=str(e))
            results["services"]["bm25"] = {
                "type": "local_index",
                "status": "unhealthy",
                "error": str(e)
            }
            results["summary"]["unhealthy"] += 1
        
        results["summary"]["total"] += 1
        
        # Determine overall status
        if results["summary"]["unhealthy"] == 0:
            results["status"] = "healthy"
        elif results["summary"]["healthy"] > results["summary"]["unhealthy"]:
            results["status"] = "degraded"
        else:
            results["status"] = "unhealthy"
        
        logger.info(
            "ping_services_complete",
            status=results["status"],
            healthy=results["summary"]["healthy"],
            unhealthy=results["summary"]["unhealthy"]
        )
        
        return results
        
    except Exception as e:
        logger.error("ping_services_failed", error=str(e))
        return {
            "status": "error",
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e),
            "services": results.get("services", {}),
            "summary": results.get("summary", {"total": 0, "healthy": 0, "unhealthy": 0})
        }
