"""
Unified LLM service with pluggable providers.

Supported providers:
  - groq      → Groq Cloud (via llama-index-llms-groq)
  - openrouter → OpenRouter (OpenAI-compatible, via llama-index-llms-openai)

The provider is selected via the LLM_PROVIDER env var (default: "groq").
API key and model can be set with LLM_API_KEY / LLM_MODEL, or fall back
to the legacy GROQ_API_KEY / GROQ_MODEL vars for backward compatibility.
"""

from __future__ import annotations

import time
from typing import Optional

from llama_index.core.llms import LLM

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Provider-specific LLM constructors
# ---------------------------------------------------------------------------

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Default structured-output models per provider (small & fast, no reasoning)
_DEFAULT_STRUCTURED_MODELS = {
    "groq": "llama-3.1-8b-instant",
    "openrouter": "meta-llama/llama-3.1-8b-instruct",
}


def _create_groq_llm(
    model: str,
    api_key: str,
    temperature: float = 0.5,
    max_tokens: int = 8192,
    context_window: int = 128_000,
    reasoning_effort: Optional[str] = "high",
) -> LLM:
    """Create a Groq LLM via llama-index-llms-groq."""
    from llama_index.llms.groq import Groq

    kwargs: dict = dict(
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        context_window=context_window,
    )
    if reasoning_effort:
        kwargs["reasoning_effort"] = reasoning_effort
    return Groq(**kwargs)


def _create_openrouter_llm(
    model: str,
    api_key: str,
    temperature: float = 0.5,
    max_tokens: int = 8192,
    context_window: int = 128_000,
    **_extra,
) -> LLM:
    """Create an OpenRouter LLM using OpenAILike (no model-name validation)."""
    from llama_index.llms.openai_like import OpenAILike

    return OpenAILike(
        model=model,
        api_key=api_key,
        api_base=OPENROUTER_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
        context_window=context_window,
        is_chat_model=True,
        # OpenRouter requires these headers for tracking / rate-limiting
        default_headers={
            "HTTP-Referer": "https://professional-rag.local",
            "X-Title": "Professional RAG System",
        },
    )


_PROVIDER_FACTORIES = {
    "groq": _create_groq_llm,
    "openrouter": _create_openrouter_llm,
}


def _resolve_provider() -> str:
    provider = settings.llm_provider.lower().strip()
    if provider not in _PROVIDER_FACTORIES:
        raise ValueError(
            f"Unsupported LLM_PROVIDER '{provider}'. "
            f"Choose from: {', '.join(_PROVIDER_FACTORIES)}"
        )
    return provider


def _resolve_api_key(provider: str) -> str:
    """Return the API key, falling back to GROQ_API_KEY for backward compat."""
    key = settings.llm_api_key or (
        settings.groq_api_key if provider == "groq" else ""
    )
    if not key:
        env_hint = "LLM_API_KEY" if provider != "groq" else "LLM_API_KEY or GROQ_API_KEY"
        raise ValueError(
            f"{env_hint} must be set when LLM_PROVIDER='{provider}'"
        )
    return key


def _resolve_model(provider: str) -> str:
    """Return the model name, falling back to GROQ_MODEL for backward compat."""
    return settings.llm_model or (
        settings.groq_model if provider == "groq" else ""
    ) or "llama-3.1-70b-versatile"


def _resolve_structured_model(provider: str) -> str:
    """Return the structured-output model name."""
    return (
        settings.llm_structured_model
        or _DEFAULT_STRUCTURED_MODELS.get(provider, "llama-3.1-8b-instant")
    )


# ---------------------------------------------------------------------------
# LLMService
# ---------------------------------------------------------------------------

class LLMService:
    """
    Provider-agnostic LLM service.

    Drop-in replacement for the former GroqService.
    Exposes the same `.get_llm()`, `.get_aurasql_llm()`,
    `.get_structured_llm()`, `.get_nexus_llm()`, and `.check_health()` API.
    """

    def __init__(self) -> None:
        self.provider = _resolve_provider()
        self.api_key = _resolve_api_key(self.provider)
        self.model = _resolve_model(self.provider)

        factory = _PROVIDER_FACTORIES[self.provider]

        # Primary LLM (reasoning / general)
        self.llm: LLM = factory(
            model=self.model,
            api_key=self.api_key,
            temperature=0.5,
            max_tokens=8192,
            context_window=128_000,
            reasoning_effort="high",
        )

        # AuraSQL LLM (deterministic, lower token budget)
        self._aurasql_llm: LLM = factory(
            model=self.model,
            api_key=self.api_key,
            temperature=0.1,
            max_tokens=settings.aurasql_max_tokens,
        )

        # Structured-output LLM (small model, no reasoning, JSON tasks)
        structured_model = _resolve_structured_model(self.provider)
        self._structured_llm: LLM = factory(
            model=structured_model,
            api_key=self.api_key,
            temperature=0.1,
            max_tokens=32_000,
            context_window=128_000,
        )

        # Health-check caching
        self._last_health_check: Optional[float] = None
        self._last_health_status: bool = True
        self._health_check_cache_duration: int = 60

        logger.log_operation(
            "🤖 LLM initialized",
            provider=self.provider,
            model=self.model,
            structured_model=structured_model,
        )

    # -- Public accessors (same API surface as the old GroqService) ---------

    def get_llm(self) -> LLM:
        """Return the primary LLM instance."""
        return self.llm

    def get_aurasql_llm(self) -> LLM:
        """Return the AuraSQL-tuned LLM instance."""
        return self._aurasql_llm

    def get_structured_llm(self) -> LLM:
        """Return the structured-output LLM (JSON extraction, summaries)."""
        return self._structured_llm

    def get_nexus_llm(self) -> LLM:
        """Return the Nexus Resume LLM (uses primary model)."""
        return self.llm

    # -- Health check -------------------------------------------------------

    async def check_health(self) -> bool:
        """
        Lightweight health probe with 60-second result caching.
        """
        now = time.time()
        if (
            self._last_health_check is not None
            and (now - self._last_health_check) < self._health_check_cache_duration
        ):
            return self._last_health_status

        try:
            response = await self.llm.acomplete("Hello")
            healthy = bool(response.text)
        except Exception as e:
            logger.log_error("LLM health check", e)
            healthy = False

        self._last_health_check = now
        self._last_health_status = healthy
        return healthy


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Return (or create) the global LLMService singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
