"""
SIMPLIFIED Hybrid Retriever using LlamaIndex built-ins
Replaces 150+ lines of custom code with ~20 lines
"""

from typing import Optional
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core import VectorStoreIndex
from app.services.vector_store import get_vector_store_service
from app.services.bm25_service import get_bm25_service
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_simplified_hybrid_retriever(top_k: Optional[int] = None):
    """
    Create hybrid retriever using LlamaIndex's QueryFusionRetriever.
    Automatically combines multiple retrievers with smart fusion.
    
    This replaces our custom HybridRetriever with RRF implementation.
    LlamaIndex does this better out-of-the-box.
    """
    top_k = top_k or settings.top_k_retrieval
    
    # Get vector store
    vector_store = get_vector_store_service()
    vector_index = vector_store.index
    
    # Create vector retriever
    vector_retriever = vector_index.as_retriever(
        similarity_top_k=top_k,
        similarity_threshold=settings.similarity_threshold
    )
    
    # Get BM25 retriever
    bm25_service = get_bm25_service()
    bm25_retriever = bm25_service.get_retriever(top_k=top_k)
    
    # LlamaIndex's QueryFusionRetriever automatically:
    # 1. Runs both retrievers
    # 2. Fuses results using Reciprocal Rank Fusion
    # 3. Returns top K combined results
    retriever = QueryFusionRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        similarity_top_k=top_k,
        num_queries=1,  # Don't generate query variations
        mode="reciprocal_rerank",  # Use RRF fusion (same as our custom impl)
        use_async=True,
    )
    
    logger.info(
        "simplified_hybrid_retriever_initialized",
        top_k=top_k,
        mode="reciprocal_rerank"
    )
    
    return retriever


"""
COMPARISON:

Custom Implementation (retriever.py):
- 169 lines of code
- Manual RRF implementation
- Manual node merging
- More prone to bugs

LlamaIndex Built-in (above):
- 30 lines of code
- Battle-tested RRF from LlamaIndex
- Automatic optimization
- Well-maintained

Same functionality, 80% less code!
"""
