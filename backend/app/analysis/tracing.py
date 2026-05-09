"""
Analysis-specific Langfuse tracing utilities.

Thin wrappers around app.observability that set the correct analysis context
(module, agent name, job_id as session_id).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Optional

from app.observability import set_llamaindex_trace_params, trace_async_call
from app.utils.logger import get_logger

logger = get_logger(__name__)


@contextmanager
def trace_agent_step(
    agent_name: str,
    step_name: str,
    job_id: str,
    user_id: int,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Context manager that sets LlamaIndex trace params for an analysis agent step.

    Usage:
        with trace_agent_step("TaskDecomposer", "decompose", job_id, user_id):
            result = await decomposer.run(query, profile)
    """
    merged_meta = {
        "module": "analysis",
        "agent": agent_name,
        "step": step_name,
        **(metadata or {}),
    }
    try:
        set_llamaindex_trace_params(
            name=f"analysis.{agent_name}.{step_name}",
            metadata=merged_meta,
            session_id=job_id,
            user_id=str(user_id),
        )
        logger.debug("Trace started for agent=%s step=%s job=%s", agent_name, step_name, job_id)
        yield
    finally:
        pass  # Langfuse handles span closure via global handler


async def trace_agent_call(agent_name: str, coro, metadata: Optional[Dict[str, Any]] = None):
    """Trace an async agent operation. Thin wrapper around observability.trace_async_call."""
    merged_meta = {
        "module": "analysis",
        "agent": agent_name,
        **(metadata or {}),
    }
    return await trace_async_call(
        f"analysis.{agent_name}",
        coro,
        merged_meta,
    )
