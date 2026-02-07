"""
Cohere service for embeddings and reranking.
"""

from typing import List, Optional
import asyncio
import cohere
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.postprocessor.cohere_rerank import CohereRerank
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CohereEmbedding768(BaseEmbedding):
    """Cohere embedding wrapper that enforces 768-dim vectors."""

    embed_dim: int = 768
    _client: cohere.Client = PrivateAttr()
    _model_name: str = PrivateAttr()

    def __init__(self, client: cohere.Client, model_name: str, **kwargs):
        super().__init__(**kwargs)
        self._client = client
        self._model_name = model_name

    def _truncate_or_pad(self, values: List[float]) -> List[float]:
        if len(values) >= self.embed_dim:
            return values[: self.embed_dim]
        return values + [0.0] * (self.embed_dim - len(values))

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._truncate_or_pad(self._embed_texts_sync([query], input_type="search_query")[0])

    async def _aget_query_embedding(self, query: str) -> List[float]:
        values = await asyncio.to_thread(self._embed_texts_sync, [query], "search_query")
        return self._truncate_or_pad(values[0])

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._truncate_or_pad(self._embed_texts_sync([text], input_type="search_document")[0])

    async def _aget_text_embedding(self, text: str) -> List[float]:
        values = await asyncio.to_thread(self._embed_texts_sync, [text], "search_document")
        return self._truncate_or_pad(values[0])

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        values = self._embed_texts_sync(texts, input_type="search_document")
        return [self._truncate_or_pad(v) for v in values]

    def _embed_texts_sync(self, texts: List[str], input_type: str) -> List[List[float]]:
        response = self._client.embed(
            texts=texts,
            model=self._model_name,
            input_type=input_type,
        )
        return response.embeddings

        return [self._truncate_or_pad(self._cohere.get_text_embedding(t)) for t in texts]


class CohereService:
    """Service for Cohere embeddings and reranking."""

    def __init__(self):
        if not settings.cohere_api_key:
            logger.log_operation("⚠️  COHERE_API_KEY not set", level="WARNING")
            raise ValueError("COHERE_API_KEY must be set when using Cohere")

        self.client = cohere.Client(settings.cohere_api_key)
        self.embed_model_768 = CohereEmbedding768(
            self.client,
            settings.cohere_embedding_model,
        )

        self.rerank_model = CohereRerank(
            api_key=settings.cohere_api_key,
            model=settings.cohere_rerank_model,
            top_n=settings.top_k_rerank,
        )

        logger.log_operation(
            "🔮 Cohere service initialized",
            embed_model=settings.cohere_embedding_model,
            rerank_model=settings.cohere_rerank_model,
        )

    def get_embed_model(self) -> CohereEmbedding768:
        return self.embed_model_768

    def get_reranker(self) -> CohereRerank:
        return self.rerank_model

    async def check_health(self) -> bool:
        try:
            _ = await self.embed_model_768.aget_text_embedding("health_check")
            return True
        except Exception as e:
            logger.log_error("Cohere health check", e)
            return False


_cohere_service: Optional[CohereService] = None


def get_cohere_service() -> CohereService:
    global _cohere_service
    if _cohere_service is None:
        _cohere_service = CohereService()
    return _cohere_service
