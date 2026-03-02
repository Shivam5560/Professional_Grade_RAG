"""
Groq service — backward-compatibility shim.

All LLM logic now lives in ``llm_service.py`` which supports multiple
providers (Groq, OpenRouter).  This module re-exports the same public
symbols so existing imports keep working without changes.
"""

from app.services.llm_service import LLMService as GroqService  # noqa: F401
from app.services.llm_service import get_llm_service as get_groq_service  # noqa: F401

__all__ = ["GroqService", "get_groq_service"]
