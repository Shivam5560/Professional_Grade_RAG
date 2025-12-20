"""
Remote Embedding Service Client
Connects to Lightning.ai hosted embedding and reranking service
"""

from typing import List, Optional
import httpx
import structlog
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.bridge.pydantic import PrivateAttr

logger = structlog.get_logger(__name__)


class RemoteEmbeddingService(BaseEmbedding):
    """
    Remote embedding service that connects to Lightning.ai hosted service.
    Compatible with LlamaIndex's BaseEmbedding interface.
    Thread-safe implementation that creates a new client for each request.
    """
    
    _base_url: str = PrivateAttr()
    _model_name: str = PrivateAttr()
    
    def __init__(
        self,
        base_url: str,
        model_name: str = "embeddinggemma",
        **kwargs
    ):
        """
        Initialize remote embedding service.
        
        Args:
            base_url: Base URL of the remote service
            model_name: Name of the embedding model to use
        """
        super().__init__(**kwargs)
        self._base_url = base_url.rstrip('/')
        self._model_name = model_name
        
        logger.info(
            "remote_embedding_service_initialized",
            base_url=base_url,
            model=model_name
        )
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a single query (sync version)."""
        return self._run_async_in_sync(self._aget_query_embedding(query))
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a single query (async version)."""
        embeddings = await self._get_embeddings([query])
        return embeddings[0]
    
    def _get_text_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text (sync version)."""
        return self._run_async_in_sync(self._aget_text_embedding(text))
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text (async version)."""
        embeddings = await self._get_embeddings([text])
        return embeddings[0]
    
    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts (sync version)."""
        return self._run_async_in_sync(self._get_embeddings(texts))
    
    def _run_async_in_sync(self, coro):
        """
        Run an async coroutine from sync context.
        Handles the case where we're already in an event loop (like FastAPI).
        """
        import asyncio
        import concurrent.futures
        import threading
        
        def run_in_new_loop():
            """Run coroutine in a completely new event loop in a new thread."""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        
        try:
            # Check if we're in a running event loop
            loop = asyncio.get_running_loop()
            # We are in an event loop, run in a separate thread with new loop
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(coro)
    
    async def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings from remote service.
        Creates a new client for each request to avoid event loop issues.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        # Create a new client for each request to avoid event loop issues
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                logger.info(
                    "calling_remote_embedding_service",
                    num_texts=len(texts),
                    base_url=self._base_url,
                    endpoint="/api/v1/embeddings"
                )
                
                response = await client.post(
                    f"{self._base_url}/api/v1/embeddings",
                    json={"texts": texts}
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(
                    "remote_embeddings_generated_successfully",
                    num_texts=len(texts),
                    dimension=data.get("dimension"),
                    base_url=self._base_url
                )
                
                return data["embeddings"]
                
            except Exception as e:
                logger.error(
                    "remote_embedding_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    num_texts=len(texts),
                    base_url=self._base_url
                )
                raise


class RemoteReranker:
    """
    Remote reranking service that connects to Lightning.ai hosted service.
    Thread-safe implementation that creates a new client for each request.
    """
    
    def __init__(self, base_url: str):
        """
        Initialize remote reranker.
        
        Args:
            base_url: Base URL of the remote service
        """
        self.base_url = base_url.rstrip('/')
        
        logger.info(
            "remote_reranker_initialized",
            base_url=base_url
        )
    
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[dict]:
        """
        Rerank documents based on query relevance.
        
        Args:
            query: Search query
            documents: List of document texts to rerank
            top_k: Number of top documents to return
            
        Returns:
            List of dicts with 'index', 'text', and 'score' keys
        """
        # Create a new client for each request to avoid event loop issues
        # Increase timeout to 60s for reranking (can be slow with many documents)
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                payload = {
                    "query": query,
                    "documents": documents
                }
                if top_k:
                    payload["top_k"] = top_k
                
                logger.info(
                    "calling_remote_reranker_service",
                    num_docs=len(documents),
                    query_preview=query[:100],
                    base_url=self.base_url,
                    endpoint="/api/v1/rerank",
                    top_k=top_k
                )
                
                response = await client.post(
                    f"{self.base_url}/api/v1/rerank",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(
                    "remote_rerank_complete_successfully",
                    num_docs=len(documents),
                    num_results=len(data["results"]),
                    top_score=data["results"][0]["score"] if data["results"] else 0,
                    base_url=self.base_url
                )
                
                return data["results"]
                
            except httpx.TimeoutException as e:
                logger.error(
                    "remote_rerank_timeout",
                    error=str(e),
                    num_docs=len(documents),
                    timeout_seconds=60.0
                )
                raise
            except httpx.HTTPStatusError as e:
                logger.error(
                    "remote_rerank_http_error",
                    error=str(e),
                    status_code=e.response.status_code,
                    response_text=e.response.text[:500],
                    num_docs=len(documents)
                )
                raise
            except Exception as e:
                logger.error(
                    "remote_rerank_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    num_docs=len(documents)
                )
                raise
