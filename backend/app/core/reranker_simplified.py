"""
SIMPLIFIED Reranker using LlamaIndex patterns
Much cleaner implementation using cross-encoder reranking
Supports both local and remote reranking services
"""

from typing import List, Optional
from llama_index.core.schema import NodeWithScore
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from sentence_transformers import CrossEncoder
from app.config import settings
from app.utils.logger import get_logger
from app.services.remote_embedding_service import RemoteReranker
import asyncio

logger = get_logger(__name__)


class SimpleCrossEncoderReranker(BaseNodePostprocessor):
    """
    Simple reranker using HuggingFace CrossEncoder.
    Works with any cross-encoder model including BGE reranker.
    """
    
    top_n: int = 5
    model_name: str = "BAAI/bge-reranker-v2-m3"
    
    def __init__(self, top_n: int = 5, model_name: str = "BAAI/bge-reranker-v2-m3", **kwargs):
        super().__init__(**kwargs)
        self.top_n = top_n
        self.model_name = model_name
        
        # Initialize CrossEncoder model
        self.model = CrossEncoder(model_name)
        
        logger.info("cross_encoder_reranker_initialized", 
                   model=model_name, 
                   top_n=top_n)
    
    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_str: Optional[str] = None
    ) -> List[NodeWithScore]:
        """
        Rerank nodes using cross-encoder.
        
        Args:
            nodes: List of nodes with initial scores
            query_str: Query string
            
        Returns:
            Reranked nodes
        """
        if not nodes or not query_str:
            return nodes
        
        try:
            # Prepare query-document pairs
            pairs = [[query_str, node.node.get_content()] for node in nodes]
            
            # Get relevance scores from cross-encoder
            scores = self.model.predict(pairs)
            
            # Update node scores and sort
            for idx, score in enumerate(scores):
                nodes[idx].score = float(score)
            
            # Sort by score and return top_n
            reranked = sorted(nodes, key=lambda x: x.score, reverse=True)[:self.top_n]
            
            logger.info(
                "nodes_reranked",
                input_nodes=len(nodes),
                output_nodes=len(reranked),
                avg_score=sum(n.score for n in reranked) / len(reranked)
            )
            
            return reranked
            
        except Exception as e:
            logger.error("reranking_failed", error=str(e))
            return nodes[:self.top_n]


def get_reranker(top_n: Optional[int] = None) -> SimpleCrossEncoderReranker:
    """
    Get reranker instance.
    Uses remote reranker if configured, otherwise uses local CrossEncoder.
    """
    top_n = top_n or settings.top_k_rerank
    
    if settings.use_remote_embedding_service:
        logger.info(
            "using_remote_reranker",
            url=settings.remote_embedding_service_url,
            top_n=top_n
        )
        return RemoteRerankerWrapper(
            base_url=settings.remote_embedding_service_url,
            top_n=top_n
        )
    else:
        logger.info("using_local_crossencoder_reranker", top_n=top_n)
        return SimpleCrossEncoderReranker(
            top_n=top_n,
            model_name="BAAI/bge-reranker-v2-m3"
        )


class RemoteRerankerWrapper(BaseNodePostprocessor):
    """
    Wrapper for remote reranker service to work with LlamaIndex.
    """
    
    top_n: int = 5
    base_url: str = ""
    
    def __init__(self, base_url: str, top_n: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.top_n = top_n
        self.base_url = base_url
        self.remote_reranker = RemoteReranker(base_url)
        
        logger.info("remote_reranker_wrapper_initialized", 
                   base_url=base_url,
                   top_n=top_n)
    
    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_str: Optional[str] = None
    ) -> List[NodeWithScore]:
        """
        Rerank nodes using remote reranker service.
        
        Args:
            nodes: List of nodes with initial scores
            query_str: Query string
            
        Returns:
            Reranked nodes
        """
        if not nodes or not query_str:
            return nodes
        
        try:
            # Extract document texts
            documents = [node.node.get_content() for node in nodes]
            
            # Call remote reranker (async operation)
            results = asyncio.run(self.remote_reranker.rerank(
                query=query_str,
                documents=documents,
                top_k=self.top_n
            ))
            
            # Map results back to nodes
            reranked_nodes = []
            for result in results:
                original_idx = result["index"]
                node = nodes[original_idx]
                node.score = result["score"]
                reranked_nodes.append(node)
            
            logger.info(
                "remote_rerank_wrapper_complete",
                input_nodes=len(nodes),
                output_nodes=len(reranked_nodes),
                avg_score=sum(n.score for n in reranked_nodes) / len(reranked_nodes) if reranked_nodes else 0
            )
            
            return reranked_nodes
            
        except Exception as e:
            logger.error("remote_reranking_failed", error=str(e), error_type=type(e).__name__)
            # Fallback to top_n nodes on error
            return nodes[:self.top_n]

