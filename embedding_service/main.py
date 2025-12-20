"""
Embedding & Reranking Microservice

This service provides:
1. Text embeddings via Ollama (embeddinggemma model)
2. Reranking via HuggingFace BGE model

Deploy on Lightning.ai or any cloud platform.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from contextlib import asynccontextmanager
import structlog
from sentence_transformers import CrossEncoder
import ollama
import os

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Global model instances
reranker_model = None
ollama_client = None

# Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "embeddinggemma")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "mixedbread-ai/mxbai-rerank-large-v2")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global reranker_model, ollama_client
    
    # Startup
    logger.info("service_starting", service="embedding-reranking")
    
    # Initialize Ollama client
    try:
        ollama_client = ollama.Client(host=OLLAMA_HOST)
        # Verify Ollama is accessible
        ollama_client.list()
        logger.info("ollama_initialized", host=OLLAMA_HOST, model=OLLAMA_MODEL)
    except Exception as e:
        logger.error("ollama_init_failed", error=str(e))
        ollama_client = None
    
    # Load reranker model
    try:
        reranker_model = CrossEncoder(RERANKER_MODEL)
        logger.info("reranker_initialized", model=RERANKER_MODEL)
    except Exception as e:
        logger.error("reranker_init_failed", error=str(e))
        raise
    
    logger.info("service_started")
    
    yield
    
    # Shutdown (cleanup if needed)
    logger.info("service_shutting_down")


# Initialize FastAPI app
app = FastAPI(
    title="Embedding & Reranking Service",
    version="1.0.0",
    description="Microservice for text embeddings and semantic reranking",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class EmbeddingRequest(BaseModel):
    """Request for text embedding"""
    texts: List[str] = Field(..., description="List of texts to embed")
    model: Optional[str] = Field(None, description="Override default model")


class EmbeddingResponse(BaseModel):
    """Response containing embeddings"""
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    dimension: int = Field(..., description="Dimension of each embedding")
    model: str = Field(..., description="Model used for embeddings")


class RerankRequest(BaseModel):
    """Request for reranking documents"""
    query: str = Field(..., description="Search query")
    documents: List[str] = Field(..., description="List of documents to rerank")
    top_k: Optional[int] = Field(None, description="Number of top documents to return")


class RerankResult(BaseModel):
    """Single reranked result"""
    index: int = Field(..., description="Original index in input list")
    text: str = Field(..., description="Document text")
    score: float = Field(..., description="Relevance score")


class RerankResponse(BaseModel):
    """Response containing reranked documents"""
    results: List[RerankResult] = Field(..., description="Reranked documents")
    model: str = Field(..., description="Model used for reranking")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ollama_available": ollama_client is not None,
        "reranker_available": reranker_model is not None,
        "ollama_model": OLLAMA_MODEL,
        "reranker_model": RERANKER_MODEL
    }


@app.post("/api/v1/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest):
    """
    Generate embeddings for input texts using Ollama.
    
    Args:
        request: EmbeddingRequest with texts to embed
        
    Returns:
        EmbeddingResponse with embedding vectors
    """
    if not ollama_client:
        raise HTTPException(status_code=503, detail="Ollama service not available")
    
    try:
        model = request.model or OLLAMA_MODEL
        embeddings = []
        
        logger.info(
            "embedding_request",
            num_texts=len(request.texts),
            model=model
        )
        
        for text in request.texts:
            response = ollama_client.embeddings(
                model=model,
                prompt=text
            )
            embeddings.append(response['embedding'])
        
        dimension = len(embeddings[0]) if embeddings else 0
        
        logger.info(
            "embeddings_generated",
            count=len(embeddings),
            dimension=dimension
        )
        
        return EmbeddingResponse(
            embeddings=embeddings,
            dimension=dimension,
            model=model
        )
        
    except Exception as e:
        logger.error("embedding_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")


@app.post("/api/v1/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """
    Rerank documents based on query relevance using BGE reranker.
    
    Args:
        request: RerankRequest with query and documents
        
    Returns:
        RerankResponse with reranked documents
    """
    if not reranker_model:
        raise HTTPException(status_code=503, detail="Reranker model not available")
    
    try:
        logger.info(
            "rerank_request",
            query=request.query[:100],
            num_docs=len(request.documents)
        )
        
        # Prepare query-document pairs for reranker
        pairs = [[request.query, doc] for doc in request.documents]
        
        # Get relevance scores
        scores = reranker_model.predict(pairs)
        
        # Create results with original indices
        results = [
            {"index": idx, "text": doc, "score": float(score)}
            for idx, (doc, score) in enumerate(zip(request.documents, scores))
        ]
        
        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Apply top_k if specified
        if request.top_k:
            results = results[:request.top_k]
        
        logger.info(
            "rerank_complete",
            num_results=len(results),
            top_score=results[0]["score"] if results else 0
        )
        
        return RerankResponse(
            results=[RerankResult(**r) for r in results],
            model=RERANKER_MODEL
        )
        
    except Exception as e:
        logger.error("rerank_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Reranking failed: {str(e)}")


@app.get("/api/v1/models")
async def list_models():
    """List available models"""
    ollama_models = []
    if ollama_client:
        try:
            model_list = ollama_client.list()
            ollama_models = [m['name'] for m in model_list.get('models', [])]
        except:
            pass
    
    return {
        "ollama_models": ollama_models,
        "reranker_model": RERANKER_MODEL,
        "default_embedding_model": OLLAMA_MODEL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
