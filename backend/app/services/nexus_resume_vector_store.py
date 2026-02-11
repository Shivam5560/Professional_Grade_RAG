"""Nexus resume vector store using pgvector."""

from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.schema import TextNode
from llama_index.vector_stores.postgres import PGVectorStore
from app.config import settings
from app.services.ollama_service import get_ollama_service
from app.services.remote_embedding_service import RemoteEmbeddingService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NexusResumeVectorStore:
    def __init__(self):
        provider = settings.embedding_provider
        if provider == "remote" or settings.use_remote_embedding_service:
            self.embed_model = RemoteEmbeddingService(
                base_url=settings.remote_embedding_service_url,
                model_name=settings.ollama_embedding_model,
            )
        elif provider == "cohere":
            from app.services.cohere_service import get_cohere_service
            self.embed_model = get_cohere_service().get_embed_model()
        else:
            self.embed_model = get_ollama_service().get_embed_model()

        embed_dim = getattr(self.embed_model, "embed_dim", 768)

        self.vector_store = PGVectorStore.from_params(
            database=settings.postgres_db,
            host=settings.postgres_host,
            password=settings.postgres_password,
            port=settings.postgres_port,
            user=settings.postgres_user,
            table_name=settings.nexus_resume_table_name,
            embed_dim=embed_dim,
        )

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


_vector_store: Optional[NexusResumeVectorStore] = None


def get_nexus_resume_vector_store() -> NexusResumeVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = NexusResumeVectorStore()
    return _vector_store
