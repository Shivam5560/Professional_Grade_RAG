"""
Reranker using either local SentenceTransformerRerank or remote Lightning.ai service.
Supports both local and cloud-based reranking.
"""

from typing import Optional, List
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.schema import NodeWithScore, QueryBundle
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RemoteRerankerWrapper:
    """
    Wrapper for remote reranker to match LlamaIndex's postprocessor interface.
    """
    
    def __init__(self, base_url: str, top_n: int):
        from app.services.remote_embedding_service import RemoteReranker
        self.reranker = RemoteReranker(base_url)
        self.top_n = top_n
        logger.info(
            "remote_reranker_wrapper_initialized",
            base_url=base_url,
            top_n=top_n
        )
    
    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
        query_str: Optional[str] = None,
        **kwargs
    ) -> List[NodeWithScore]:
        """Postprocess nodes using remote service (sync version)."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # Handle both query_bundle and query_str
        if query_str and not query_bundle:
            query_bundle = QueryBundle(query_str=query_str)
        
        if not nodes or not query_bundle:
            return nodes
        
        # Run async code in a new thread to avoid event loop conflicts
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                asyncio.run,
                self._apostprocess_nodes(nodes, query_bundle)
            )
            return future.result()
    
    async def _apostprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        """Rerank nodes using remote service (async version)."""
        if not nodes or not query_bundle:
            return nodes
        
        # Extract texts and query
        query_str = query_bundle.query_str
        documents = [node.node.get_content() for node in nodes]
        
        # Call remote service
        results = await self.reranker.rerank(
            query=query_str,
            documents=documents,
            top_k=self.top_n
        )
        
        # Map results back to nodes
        reranked_nodes = []
        for result in results:
            original_node = nodes[result["index"]]
            # Update score with reranker score
            original_node.score = result["score"]
            reranked_nodes.append(original_node)
        
        return reranked_nodes
    
    def postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        """Public interface - delegates to _postprocess_nodes."""
        return self._postprocess_nodes(nodes, query_bundle)


def get_reranker(top_n: Optional[int] = None, model: Optional[str] = None):
    """
    Create a reranker instance - either local or remote based on settings.
    
    Args:
        top_n: Number of top results (default from config)
        model: Model name (default: BAAI/bge-reranker-v2-m3)
        
    Returns:
        Reranker instance (local or remote wrapper)
    """
    top_n = top_n or settings.top_k_rerank
    model = model or "BAAI/bge-reranker-v2-m3"
    
    if settings.use_remote_embedding_service:
        # Use remote reranker from Lightning.ai
        reranker = RemoteRerankerWrapper(
            base_url=settings.remote_embedding_service_url,
            top_n=top_n
        )
        logger.info(
            "reranker_initialized",
            type="remote",
            url=settings.remote_embedding_service_url,
            top_n=top_n
        )
    else:
        # Use local SentenceTransformerRerank
        reranker = SentenceTransformerRerank(
            model=model,
            top_n=top_n,
        )
        logger.info(
            "reranker_initialized",
            model=model,
            top_n=top_n,
            type="local_SentenceTransformerRerank"
        )
    
    return reranker

