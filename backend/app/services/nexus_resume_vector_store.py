"""Nexus resume vector store using pgvector.

Uses the unified RAG provider factory for embedding model and pgvector store.
Table: settings.nexus_resume_table_name (nexus_resume_embeddings)
"""

from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.schema import TextNode
from llama_index.vector_stores.postgres import PGVectorStore
from app.config import settings
from app.services.rag_provider_factory import get_embed_model, create_pgvector_store
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NexusResumeVectorStore:
    def __init__(self):
        self.embed_model = get_embed_model()
        self.vector_store = create_pgvector_store(settings.nexus_resume_table_name)

        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index: Optional[VectorStoreIndex] = None

    def get_index(self) -> VectorStoreIndex:
        if self.index is None:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                embed_model=self.embed_model,
            )
        return self.index

    def add_nodes(self, nodes: List[TextNode]) -> None:
        if not nodes:
            return
        if self.index is None:
            self.index = VectorStoreIndex(
                nodes=nodes,
                storage_context=self.storage_context,
                embed_model=self.embed_model,
                show_progress=True,
            )
        else:
            self.index.insert_nodes(nodes)

    def get_query_engine(self, resume_id: str, doc_type: str):
        """Get retriever for manual querying (not query engine)."""
        from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters

        index = self.get_index()
        filters = MetadataFilters(
            filters=[
                ExactMatchFilter(key="resume_id", value=resume_id),
                ExactMatchFilter(key="doc_type", value=doc_type),
            ]
        )
        # Return retriever with 2 chunks for good context
        retriever = index.as_retriever(similarity_top_k=2, filters=filters)
        return retriever

    def has_nodes(self, resume_id: str, doc_type: str) -> bool:
        try:
            table = self.vector_store._table_class
            if hasattr(self.vector_store, "_initialize"):
                self.vector_store._initialize()
            session_factory = self.vector_store._session
            query = (
                select(table.id)
                .where(table.metadata_["resume_id"].astext == resume_id)
                .where(table.metadata_["doc_type"].astext == doc_type)
                .limit(1)
            )
            with session_factory() as session:
                return session.execute(query).first() is not None
        except Exception as exc:
            logger.warning("nexus_resume_vector_store_has_nodes_failed", error=str(exc))
            return False

    def delete_by_resume_id(self, resume_id: str) -> int:
        """
        Delete all vector embeddings for a given resume_id.
        Includes both 'resume' and 'jd' doc_types associated with this resume.
        
        Returns number of deleted rows.
        """
        try:
            from sqlalchemy import delete as sql_delete
            
            table = self.vector_store._table_class
            if hasattr(self.vector_store, "_initialize"):
                self.vector_store._initialize()
            session_factory = self.vector_store._session
            
            stmt = sql_delete(table).where(
                table.metadata_["resume_id"].astext == resume_id
            )
            
            with session_factory() as session:
                result = session.execute(stmt)
                session.commit()
                deleted_count = result.rowcount
                logger.info(f"Deleted {deleted_count} embeddings for resume {resume_id}")
                return deleted_count
        except Exception as exc:
            logger.warning(f"delete_by_resume_id failed: {exc}")
            return 0


_vector_store: Optional[NexusResumeVectorStore] = None


def get_nexus_resume_vector_store() -> NexusResumeVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = NexusResumeVectorStore()
    return _vector_store
