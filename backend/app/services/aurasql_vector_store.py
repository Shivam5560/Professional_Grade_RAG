"""AuraSQL vector store for schema contexts using pgvector.

Uses the unified RAG provider factory for embedding model and pgvector store.
Table: settings.aurasql_table_name (aurasql_embeddings)
"""

from __future__ import annotations

from typing import List, Optional
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.schema import TextNode
from llama_index.vector_stores.postgres import PGVectorStore
from app.config import settings
from app.services.rag_provider_factory import get_embed_model, create_pgvector_store
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuraSqlVectorStore:
    def __init__(self):
        self.embed_model = get_embed_model()
        self.vector_store = create_pgvector_store(settings.aurasql_table_name)

        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index: Optional[VectorStoreIndex] = None

    def get_index(self) -> VectorStoreIndex:
        if self.index is None:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                embed_model=self.embed_model,
            )
        return self.index

    def add_schema_nodes(self, nodes: List[TextNode]) -> None:
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

    def get_query_engine(self, context_id: str):
        from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
        from llama_index.core.query_engine import RetrieverQueryEngine

        index = self.get_index()
        filters = MetadataFilters(filters=[ExactMatchFilter(key="context_id", value=context_id)])
        retriever = index.as_retriever(similarity_top_k=settings.aurasql_top_k, filters=filters)
        return RetrieverQueryEngine.from_args(retriever=retriever, llm=Settings.llm)


_vector_store: Optional[AuraSqlVectorStore] = None


def get_aurasql_vector_store() -> AuraSqlVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = AuraSqlVectorStore()
    return _vector_store
