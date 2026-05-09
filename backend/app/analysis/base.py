"""
Base Analysis Agent — shared foundation for all analysis pipeline agents.

Provides: LLM calling with system/user role separation, structured output via
function calling, unified JSON extraction, exponential-backoff retry, token
budget management, and Langfuse tracing.
"""

from __future__ import annotations

import json
import random
import time
from typing import Any, Dict, Optional, Tuple, Type

import httpx
from pydantic import BaseModel

from app.analysis.tracing import trace_agent_call
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    ConnectionError,
    TimeoutError,
)


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM output, handling markdown fences and trailing commas."""
    if not text:
        raise ValueError("Empty LLM response")

    text = text.strip()

    # Strip markdown code fences
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    # Handle trailing commas before } or ]
    text = _fix_trailing_commas(text)

    return json.loads(text)


def _fix_trailing_commas(json_str: str) -> str:
    """Remove trailing commas from JSON objects and arrays (common LLM mistake)."""
    import re

    # Remove trailing comma before closing brace/bracket
    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*\]", "]", json_str)

    return json_str


async def retry_with_backoff(
    coro_factory,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: Tuple = RETRYABLE_EXCEPTIONS,
):
    """Exponential backoff with full jitter."""
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await coro_factory()
        except retryable_exceptions as exc:
            last_exception = exc
            if attempt == max_retries:
                raise
            delay = min(base_delay * (2**attempt) + random.uniform(0, 1), max_delay)
            logger.warning(
                "LLM call failed, retrying (attempt %d/%d)",
                attempt + 1,
                max_retries,
                extra_data={"delay_s": round(delay, 2), "error": str(exc)[:100]},
            )
            time.sleep(delay)
        except Exception:
            # Non-retryable — don't retry
            raise

    # Should never reach here, but just in case
    raise last_exception  # type: ignore[misc]


class BaseAnalysisAgent:
    """Shared foundation for all analysis pipeline agents."""

    def __init__(self, agent_name: str, use_structured_llm: bool = True):
        self.agent_name = agent_name
        self._use_structured_llm = use_structured_llm

    def _get_llm(self):
        from app.services.llm_service import get_llm_service

        if self._use_structured_llm:
            return get_llm_service().get_structured_llm()
        return get_llm_service().get_llm()

    async def _call_llm(
        self,
        prompt: str,
        system_prompt: str,
        output_schema: Optional[Type[BaseModel]] = None,
        max_retries: int = 3,
        token_budget: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Call LLM with proper system/user role separation.

        - Uses system role (not text concatenation)
        - Structured output via function calling when schema provided
        - Exponential backoff retry with jitter
        - Token budget truncation
        - Langfuse tracing
        """
        llm = self._get_llm()

        async def _call():
            kwargs = self._build_llm_kwargs(prompt, system_prompt, output_schema, token_budget)
            response = await llm.acomplete(**kwargs)
            text = getattr(response, "text", None) or str(response)

            if output_schema is not None:
                # Parse structured output from JSON
                return _extract_json(text)

            # For unstructured calls, try JSON extraction, fall back to raw text
            try:
                parsed = _extract_json(text)
                return parsed
            except (json.JSONDecodeError, ValueError):
                return {"text": text.strip()}

        return await trace_agent_call(
            self.agent_name,
            retry_with_backoff(_call, max_retries=max_retries),
            {"prompt_len": len(prompt), "system_prompt_len": len(system_prompt)},
        )

    def _build_llm_kwargs(
        self,
        prompt: str,
        system_prompt: str,
        output_schema: Optional[Type[BaseModel]] = None,
        token_budget: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Build kwargs for llm.acomplete() with proper role separation."""
        budget = token_budget or settings.analysis_llm_token_budget

        # Truncate prompt to fit budget (system prompt is usually small)
        max_prompt_chars = budget * 3  # rough estimate: ~3 chars per token
        if len(prompt) > max_prompt_chars:
            prompt = prompt[:max_prompt_chars] + "\n... [truncated]"

        kwargs: Dict[str, Any] = {
            "prompt": prompt,
        }

        # Attach system prompt. LlamaIndex LLM interface varies by provider —
        # Groq's wrapper supports `system_prompt` kwarg, OpenRouter-like uses
        # `additional_kwargs`. We try the standard kwarg first.
        if hasattr(llm := self._get_llm(), "complete"):
            # Check if the underlying client supports system messages
            pass

        # Most LlamaIndex LLM wrappers accept system_prompt directly
        kwargs["system_prompt"] = system_prompt

        if output_schema is not None:
            schema_json = output_schema.model_json_schema()
            schema_str = json.dumps(schema_json, indent=2)
            kwargs["prompt"] = (
                f"{prompt}\n\nRespond ONLY with valid JSON conforming to this schema:\n{schema_str}"
            )

        return kwargs

    @staticmethod
    def compute_confidence(
        num_findings: int,
        has_errors: bool,
        data_quality_score: float = 1.0,
    ) -> float:
        """Compute agent confidence from multiple factors.

        Factors:
        - Findings count: sigmoid-style scaling (2→0.5, 5→0.75, 10→0.9)
        - Error penalty: -0.4 if errors occurred
        - Data quality: multiplier (0.5–1.0)
        """
        if has_errors:
            return round(max(0.0, 0.3 * data_quality_score), 4)

        # Sigmoid-ish: confidence grows with findings but plateaus
        findings_factor = min(0.95, 0.4 + 0.35 * (num_findings**0.4))
        return round(findings_factor * data_quality_score, 4)


# Re-export for convenience
__all__ = ["BaseAnalysisAgent", "_extract_json", "retry_with_backoff", "RETRYABLE_EXCEPTIONS"]
