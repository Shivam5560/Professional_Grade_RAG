"""
Hybrid retriever using LlamaIndex's QueryFusionRetriever.
Combines BM25 and vector search automatically.
"""

from typing import List, Optional
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.retrievers import BaseRetriever, QueryFusionRetriever
from app.services.vector_store import get_vector_store_service
from app.services.bm25_service import get_bm25_service
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BM25Retriever(BaseRetriever):
    """Wrapper to make BM25Service compatible with LlamaIndex retrievers."""
    
    def __init__(
        self, 
        top_k: int = 10,
        user_id: Optional[int] = None,
        document_ids: Optional[List[str]] = None
    ):
        super().__init__()
        self.top_k = top_k
        self.user_id = user_id
        self.document_ids = document_ids
        self.bm25_service = get_bm25_service()
    
    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes using BM25 with optional filters."""
        return self.bm25_service.search(
            query=query_bundle.query_str,
            top_k=self.top_k,
            user_id=self.user_id,
            document_ids=self.document_ids
        )


def get_hybrid_retriever(
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
    user_id: Optional[int] = None,
    document_ids: Optional[List[str]] = None
) -> Optional[QueryFusionRetriever]:
    """
    Create a hybrid retriever using LlamaIndex's QueryFusionRetriever.
    
    This automatically combines BM25 and vector search using Reciprocal Rank Fusion.
    Much simpler than our custom implementation!
    
    Args:
        top_k: Number of results to return (default from config)
        similarity_threshold: Minimum similarity score (default from config)
        user_id: Filter results by user ID
        document_ids: Filter results by specific document IDs
        
    Returns:
        QueryFusionRetriever instance or None if no documents exist
    """
    top_k = top_k or settings.top_k_retrieval
    similarity_threshold = similarity_threshold or settings.similarity_threshold
    
    # Get vector store
    vector_store_service = get_vector_store_service()
    vector_index = vector_store_service.index
    
    # Check if index exists (documents have been uploaded)
    if vector_index is None:
        logger.warning(
            "no_vector_index_available",
            message="No documents have been uploaded yet. Please upload documents first."
        )
        return None
    
    # Create vector retriever
    vector_retriever = vector_index.as_retriever(
        similarity_top_k=top_k,
    )
    
    # Create BM25 retriever with filters
    bm25_retriever = BM25Retriever(
        top_k=top_k,
        user_id=user_id,
        document_ids=document_ids
    )
    
    # Use LlamaIndex's QueryFusionRetriever for automatic hybrid search
    # It handles RRF (Reciprocal Rank Fusion) automatically
    hybrid_retriever = QueryFusionRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        similarity_top_k=top_k,
        num_queries=1,  # Don't generate query variations
        mode="reciprocal_rerank",  # Use RRF for fusion
        use_async=False,  # Simplified sync execution
    )
    
    logger.info(
        "hybrid_retriever_initialized",
        top_k=top_k,
        similarity_threshold=similarity_threshold,
        user_id=user_id,
        num_document_filters=len(document_ids) if document_ids else 0,
        mode="query_fusion_with_rrf",
        type="QueryFusionRetriever"
    )
    
    return hybrid_retriever
