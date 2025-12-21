"""
Ollama service for embeddings only.
Wraps Ollama API calls for embedding generation in the RAG system.
Note: LLM functionality has been moved to Groq service.
"""

import time
from typing import List, Optional
import httpx
from llama_index.embeddings.ollama import OllamaEmbedding
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaService:
    """Service for interacting with Ollama embedding models."""
    
    def __init__(self):
        """Initialize Ollama service with embedding model configuration."""
        self.base_url = settings.ollama_base_url
        self.embedding_model = settings.ollama_embedding_model
        self.reranker_model = settings.ollama_reranker_model
        
        # Initialize embedding model with explicit embed_batch_size
        self.embed_model = OllamaEmbedding(
            model_name=self.embedding_model,
            base_url=self.base_url,
            embed_batch_size=10,  # Explicitly set batch size
        )
        
        # Health check caching to prevent excessive API calls
        self._last_health_check: Optional[float] = None
        self._last_health_status: bool = True
        self._health_check_cache_duration: int = 60  # Cache for 60 seconds
        
        logger.log_operation("📚 Ollama embeddings initialized", model=self.embedding_model)
    
    async def check_health(self) -> bool:
        """
        Check if Ollama service is available.
        Uses caching to prevent excessive API calls during health checks.
        
        Returns:
            True if service is healthy
        """
        # Check if we have a recent cached result
        current_time = time.time()
        if (self._last_health_check is not None and 
            (current_time - self._last_health_check) < self._health_check_cache_duration):
            logger.debug(
                "ollama_health_check_cached",
                cached_status=self._last_health_status,
                seconds_since_check=int(current_time - self._last_health_check)
            )
            return self._last_health_status
        
        # Perform actual health check
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                is_healthy = response.status_code == 200
                
                # Update cache
                self._last_health_check = current_time
                self._last_health_status = is_healthy
                
                return is_healthy
        except Exception as e:
            logger.log_error("Ollama health check", e)
            
            # Update cache with failure
            self._last_health_check = current_time
            self._last_health_status = False
            
            return False
    
    async def list_models(self) -> List[str]:
        """
        List available Ollama models.
        
        Returns:
            List of model names
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error("failed_to_list_ollama_models", error=str(e))
        return []
    
    def get_embed_model(self) -> OllamaEmbedding:
        """Get the embedding model instance."""
        return self.embed_model
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        try:
            embedding = await self.embed_model.aget_text_embedding(text)
            return embedding
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e), text_length=len(text))
            raise
    
    async def rerank(
        self, 
        query: str, 
        documents: List[str], 
        top_k: Optional[int] = None
    ) -> List[tuple[int, float]]:
        """
        Rerank documents using BGE reranker model via Ollama API.
        BGE reranker is a cross-encoder that outputs relevance scores.
        
        Args:
            query: Search query
            documents: List of document texts
            top_k: Number of top results to return
            
        Returns:
            List of (index, score) tuples sorted by score
        """
        if not documents:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                scores = []
                
                # BGE reranker expects: "query: <query> passage: <document>"
                # The model outputs an embedding where the score can be derived
                for idx, doc in enumerate(documents):
                    # Proper BGE reranker format
                    prompt = f"query: {query} passage: {doc}"
                    
                    # Use embeddings API - BGE reranker outputs a score embedding
                    response = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={
                            "model": self.reranker_model,
                            "prompt": prompt
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        embedding = result.get("embedding", [])
                        
                        if embedding:
                            # For BGE reranker via Ollama, use the magnitude of the embedding
                            # as the relevance score (higher magnitude = more relevant)
                            import math
                            score = math.sqrt(sum(x * x for x in embedding))
                            
                            # Normalize to 0-1 range (typical BGE scores are 0-30)
                            # Using tanh for soft normalization
                            normalized_score = math.tanh(score / 20.0)
                            
                            scores.append((idx, normalized_score))
                        else:
                            scores.append((idx, 0.0))
                    else:
                        logger.warning(
                            "reranker_request_failed",
                            status_code=response.status_code,
                            doc_index=idx
                        )
                        scores.append((idx, 0.0))
                
                # Sort by score descending
                scores.sort(key=lambda x: x[1], reverse=True)
                
                if top_k:
                    scores = scores[:top_k]
                
                logger.info(
                    "documents_reranked",
                    num_documents=len(documents),
                    top_k=top_k or len(documents),
                    avg_score=sum(s[1] for s in scores) / len(scores) if scores else 0.0,
                    score_range=f"{min(s[1] for s in scores):.3f}-{max(s[1] for s in scores):.3f}" if scores else "N/A"
                )
                
                return scores
                
        except Exception as e:
            logger.error("reranking_failed", error=str(e))
            import traceback
            logger.error("reranking_traceback", trace=traceback.format_exc())
            # Return original order with descending scores
            return [(i, 1.0 - (i * 0.1)) for i in range(min(len(documents), top_k or len(documents)))]


# Global instance
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """Get or create the global Ollama service instance."""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
