"""
Unified RAG Infrastructure Provider Factory.

Single source of truth for LLM, Embedding, and Reranker instances
shared across all 3 tools: RAG Chat, AuraSQL, and Nexus Resume.

Each tool uses a DIFFERENT pgvector table but the SAME:
  - LLM provider (Groq)
  - Embedding provider (Remote / Cohere / Ollama)
  - Reranker provider (Local / Cohere / Remote) — not used by Nexus Resume
"""

from __future__ import annotations

import threading
from typing import Optional

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex, StorageContext

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()
_embed_model: Optional[BaseEmbedding] = None
_reranker = None


def get_embed_model() -> BaseEmbedding:
    """
    Return the shared embedding model instance.
    All 3 tools (RAG Chat, AuraSQL, Nexus Resume) use this same instance.
    Provider is selected via EMBEDDING_PROVIDER env var.
    """
    global _embed_model
    if _embed_model is not None:
        return _embed_model

    with _lock:
        if _embed_model is not None:
            return _embed_model

        provider = settings.embedding_provider

        if provider == "remote" or settings.use_remote_embedding_service:
            from app.services.remote_embedding_service import RemoteEmbeddingService

            _embed_model = RemoteEmbeddingService(
                base_url=settings.remote_embedding_service_url,
                model_name=settings.ollama_embedding_model,
            )
            logger.info(
                "rag_factory_embed_model_initialized",
                provider="remote",
                url=settings.remote_embedding_service_url,
                model=settings.ollama_embedding_model,
            )
        elif provider == "cohere":
            from app.services.cohere_service import get_cohere_service

            _embed_model = get_cohere_service().get_embed_model()
            logger.info(
                "rag_factory_embed_model_initialized",
                provider="cohere",
                model=settings.cohere_embedding_model,
            )
        else:
            from app.services.ollama_service import get_ollama_service

            _embed_model = get_ollama_service().get_embed_model()
            logger.info(
                "rag_factory_embed_model_initialized",
                provider="ollama",
                model=settings.ollama_embedding_model,
            )

        return _embed_model


def get_embed_dim() -> int:
    """Return the embedding dimension from the current model."""
    model = get_embed_model()
    return getattr(model, "embed_dim", 768)


def get_llm():
    """
    Return the primary LLM instance (Groq).
    Used by RAG Chat, Nexus Resume, and PageIndex.
    """
    from app.services.groq_service import get_groq_service

    return get_groq_service().get_llm()


def get_aurasql_llm():
    """
    Return the AuraSQL-specific LLM instance (Groq, lower max_tokens).
    """
    from app.services.groq_service import get_groq_service

    return get_groq_service().get_aurasql_llm()


def get_nexus_llm():
    """
    Return the Nexus Resume LLM instance (uses main model for better quality).
    """
    from app.services.groq_service import get_groq_service

    return get_groq_service().get_nexus_llm()


def get_reranker():
    """
    Return the shared reranker instance.
    Used by RAG Chat and AuraSQL. NOT used by Nexus Resume.
    Provider is selected via RERANKER_PROVIDER env var.
    """
    global _reranker
    if _reranker is not None:
        return _reranker

    with _lock:
        if _reranker is not None:
            return _reranker

        provider = settings.reranker_provider

        if provider == "cohere":
            from app.services.cohere_service import get_cohere_service

            _reranker = get_cohere_service().get_reranker()
            logger.info("rag_factory_reranker_initialized", provider="cohere")
        elif provider == "remote" or settings.use_remote_reranker_service:
            from app.services.remote_embedding_service import RemoteReranker

            _reranker = RemoteReranker(
                base_url=settings.remote_embedding_service_url,
            )
            logger.info("rag_factory_reranker_initialized", provider="remote")
        else:
            from llama_index.core.postprocessor import SentenceTransformerRerank

            _reranker = SentenceTransformerRerank(
                model="BAAI/bge-reranker-v2-m3",
                top_n=settings.top_k_rerank,
            )
            logger.info("rag_factory_reranker_initialized", provider="local")

        return _reranker


def create_pgvector_store(table_name: str) -> PGVectorStore:
    """
    Create a PGVectorStore pointing at the given table.

    Each tool has its own table:
      - RAG Chat:      settings.postgres_table_name  (rag_embeddings)
      - AuraSQL:       settings.aurasql_table_name   (aurasql_embeddings)
      - Nexus Resume:  settings.nexus_resume_table_name (nexus_resume_embeddings)

    All share the same PostgreSQL database and embedding dimension.
    """
    embed_dim = get_embed_dim()

    store = PGVectorStore.from_params(
        database=settings.postgres_db,
        host=settings.postgres_host,
        password=settings.postgres_password,
        port=settings.postgres_port,
        user=settings.postgres_user,
        table_name=table_name,
        embed_dim=embed_dim,
    )
    logger.info(
        "rag_factory_pgvector_store_created",
        table=table_name,
        embed_dim=embed_dim,
    )
    return store


def get_text_embeddings(texts: list[str], input_type: str = "search_document") -> list:
    """
    Batch-embed texts using the shared embedding model.
    Handles API differences between providers transparently.

    Args:
        texts: List of strings to embed.
        input_type: "search_query" or "search_document" (Cohere-specific).

    Returns:
        List of embedding vectors.
    """
    embed_model = get_embed_model()

    if hasattr(embed_model, "get_text_embedding_batch"):
        try:
            return embed_model.get_text_embedding_batch(
                texts, input_type=input_type, show_progress=False
            )
        except TypeError:
            return embed_model.get_text_embedding_batch(texts)

    if hasattr(embed_model, "get_text_embeddings"):
        return embed_model.get_text_embeddings(texts)

    if hasattr(embed_model, "_get_text_embeddings"):
        return embed_model._get_text_embeddings(texts)

    if hasattr(embed_model, "get_text_embedding"):
        return [embed_model.get_text_embedding(text) for text in texts]

    raise ValueError("Embedding model does not support batch embeddings")
