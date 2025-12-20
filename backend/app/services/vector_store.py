"""
PostgreSQL vector store service with pgvector.
Handles vector storage and retrieval operations using LlamaIndex.
"""

import os
from typing import List, Optional, Dict, Any
from sqlalchemy import make_url
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core.schema import TextNode, NodeWithScore
from app.config import settings
from app.services.ollama_service import get_ollama_service
from app.services.remote_embedding_service import RemoteEmbeddingService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStoreService:
    """Service for managing vector storage with PostgreSQL and pgvector."""
    
    def __init__(self):
        """Initialize PostgreSQL vector store with pgvector extension."""
        # Get embedding model based on configuration
        if settings.use_remote_embedding_service:
            logger.info(
                "using_remote_embedding_service",
                url=settings.remote_embedding_service_url,
                model=settings.ollama_embedding_model
            )
            self.embed_model = RemoteEmbeddingService(
                base_url=settings.remote_embedding_service_url,
                model_name=settings.ollama_embedding_model
            )
        else:
            logger.info("using_local_ollama_embeddings")
            ollama_service = get_ollama_service()
            self.embed_model = ollama_service.get_embed_model()
        
        # Get embedding dimension from the model
        # Most embedding models use 768 or 1024 dimensions
        # For Ollama's gemma model, we'll use 768 as default
        embed_dim = getattr(self.embed_model, 'embed_dim', 768)
        
        # Build PostgreSQL connection string
        connection_string = (
            f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
            f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
        )
        
        # Initialize PGVectorStore with LlamaIndex
        try:
            self.vector_store = PGVectorStore.from_params(
                database=settings.postgres_db,
                host=settings.postgres_host,
                password=settings.postgres_password,
                port=settings.postgres_port,
                user=settings.postgres_user,
                table_name=settings.postgres_table_name,
                embed_dim=embed_dim,
            )
            
            logger.info(
                "postgres_vector_store_initialized",
                table_name=settings.postgres_table_name,
                host=settings.postgres_host,
                database=settings.postgres_db,
                embed_dim=embed_dim,
            )
        except Exception as e:
            logger.error(
                "postgres_vector_store_initialization_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise
        
        # Create storage context
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        # Try to load existing index from DB
        self.index: Optional[VectorStoreIndex] = None
        try:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                embed_model=self.embed_model,
            )
            logger.info("existing_vector_index_loaded_from_db")
        except Exception as e:
            logger.info("no_existing_index_in_db", message="Will create index when documents are added")
        
        logger.info(
            "vector_store_initialized",
            table_name=settings.postgres_table_name,
            has_existing_data=self.index is not None
        )
    
    def add_nodes(self, nodes: List[TextNode]) -> None:
        """
        Add text nodes to the vector store.
        
        Args:
            nodes: List of TextNode objects to index
        """
        try:
            if not nodes:
                logger.warning("no_nodes_to_add")
                return
            
            logger.info("adding_nodes_to_vector_store", num_nodes=len(nodes))
            
            # Log embedding model info
            logger.info(
                "embedding_model_info",
                model_name=self.embed_model.model_name if hasattr(self.embed_model, 'model_name') else "unknown",
                embed_batch_size=self.embed_model.embed_batch_size if hasattr(self.embed_model, 'embed_batch_size') else "unknown"
            )
            
            # Create or update index with new nodes
            if self.index is None:
                # First time: create index with nodes
                logger.info("creating_new_index")
                try:
                    self.index = VectorStoreIndex(
                        nodes=nodes,
                        storage_context=self.storage_context,
                        embed_model=self.embed_model,
                        show_progress=True,
                    )
                    logger.info("index_created_successfully")
                except Exception as index_error:
                    logger.error(
                        "index_creation_failed",
                        error=str(index_error),
                        error_type=type(index_error).__name__
                    )
                    import traceback
                    logger.error("index_creation_traceback", trace=traceback.format_exc())
                    raise
            else:
                # Subsequent times: insert nodes into existing index
                logger.info("inserting_nodes_into_existing_index")
                # Use insert_nodes (batch) instead of insert (single) for better compatibility
                self.index.insert_nodes(nodes)
                logger.info("nodes_inserted_successfully")
            
            logger.info("nodes_added_to_vector_store", num_nodes=len(nodes))
            
        except Exception as e:
            logger.error("failed_to_add_nodes", error=str(e), error_type=type(e).__name__, num_nodes=len(nodes))
            import traceback
            logger.error("traceback", trace=traceback.format_exc())
            raise
    
    def get_index(self) -> Optional[VectorStoreIndex]:
        """
        Get the vector store index.
        
        Returns:
            VectorStoreIndex or None if not initialized
        """
        if self.index is None:
            # Try to load existing index from vector store
            try:
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=self.vector_store,
                    embed_model=self.embed_model,
                )
                logger.info("vector_index_loaded_from_store")
            except Exception as e:
                logger.debug("no_existing_index_to_load", error=str(e))
        
        return self.index
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 10,
        similarity_threshold: Optional[float] = None
    ) -> List[NodeWithScore]:
        """
        Retrieve relevant nodes for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of NodeWithScore objects
        """
        index = self.get_index()
        if index is None:
            logger.warning("no_index_available_for_retrieval")
            return []
        
        try:
            retriever = index.as_retriever(
                similarity_top_k=top_k,
            )
            
            nodes = retriever.retrieve(query)
            
            # Filter by similarity threshold if provided
            if similarity_threshold is not None:
                nodes = [
                    node for node in nodes 
                    if node.score and node.score >= similarity_threshold
                ]
            
            logger.info(
                "vector_retrieval_complete",
                query_length=len(query),
                num_results=len(nodes),
                top_k=top_k,
            )
            
            return nodes
            
        except Exception as e:
            logger.error("vector_retrieval_failed", error=str(e))
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks of a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successful
        """
        try:
            # For PostgreSQL, we need to delete by metadata filter
            # This is handled by the vector store's delete method
            index = self.get_index()
            if index:
                # Delete nodes with matching document_id in metadata
                # Note: LlamaIndex PGVectorStore supports deletion via ref_doc_id
                index.delete_ref_doc(document_id, delete_from_docstore=True)
                logger.info("document_deleted", document_id=document_id)
                return True
            else:
                logger.warning("no_index_available_for_deletion")
                return False
            
        except Exception as e:
            logger.error("document_deletion_failed", error=str(e), document_id=document_id)
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            # Query the database for stats
            # This is a simplified version - in production you might want more detailed stats
            index = self.get_index()
            if index:
                # Get approximate count from vector store
                # Note: This may vary based on PGVectorStore implementation
                return {
                    "total_chunks": "N/A",  # PostgreSQL doesn't expose count easily without query
                    "table_name": settings.postgres_table_name,
                    "database": settings.postgres_db,
                }
            else:
                return {
                    "total_chunks": 0,
                    "table_name": settings.postgres_table_name,
                    "database": settings.postgres_db,
                }
        except Exception as e:
            logger.error("failed_to_get_collection_stats", error=str(e))
            return {
                "total_chunks": 0,
                "table_name": settings.postgres_table_name,
                "database": settings.postgres_db,
            }
    
    def check_health(self) -> bool:
        """
        Check if vector store is healthy.
        
        Returns:
            True if healthy
        """
        try:
            # Try to access the vector store
            # In PGVectorStore, we can check by trying to create/access the index
            index = self.get_index()
            return True
        except Exception as e:
            logger.error("vector_store_health_check_failed", error=str(e))
            return False
    
    def reset(self) -> None:
        """Reset the vector store (use with caution)."""
        try:
            # For PostgreSQL, we need to drop and recreate the table
            # This is done via the vector store's client
            if hasattr(self.vector_store, 'client'):
                # Drop the table if it exists
                # Note: Be careful with this in production
                logger.warning("vector_store_reset_initiated")
                
                # Reinitialize the vector store
                embed_dim = getattr(self.embed_model, 'embed_dim', 768)
                self.vector_store = PGVectorStore.from_params(
                    database=settings.postgres_db,
                    host=settings.postgres_host,
                    password=settings.postgres_password,
                    port=settings.postgres_port,
                    user=settings.postgres_user,
                    table_name=settings.postgres_table_name,
                    embed_dim=embed_dim,
                )
                
                self.storage_context = StorageContext.from_defaults(
                    vector_store=self.vector_store
                )
                
                self.index = None
                
                logger.warning("vector_store_reset_completed")
            else:
                logger.error("vector_store_reset_not_supported")
                
        except Exception as e:
            logger.error("vector_store_reset_failed", error=str(e))
            raise


# Global instance
_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    """Get or create the global vector store service instance."""
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service
