import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Mapping, Optional

from app.config import settings

logger = logging.getLogger(__name__)

_llamaindex_handler_configured = False
_llamaindex_handler_setup_attempted = False
_llamaindex_handler_setup_error: Optional[str] = None


def _is_langfuse_enabled() -> bool:
    return bool(
        settings.langfuse_enabled
        and (settings.langfuse_host or "").strip()
        and (settings.langfuse_public_key or "").strip()
        and (settings.langfuse_secret_key or "").strip()
    )


def _ensure_langfuse_env_from_settings() -> None:
    public_key = (settings.langfuse_public_key or "").strip()
    secret_key = (settings.langfuse_secret_key or "").strip()
    host = (settings.langfuse_host or "").strip()
    env_name = (settings.langfuse_env or "dev").strip()

    if public_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
    if secret_key:
        os.environ["LANGFUSE_SECRET_KEY"] = secret_key
    if host:
        os.environ["LANGFUSE_HOST"] = host
    if env_name:
        os.environ["LANGFUSE_ENV"] = env_name


def configure_llamaindex_langfuse_handler() -> bool:
    """
    Official LlamaIndex integration path:
      pip install llama-index-callbacks-langfuse
      from llama_index.core import set_global_handler
      set_global_handler("langfuse")
    """
    global _llamaindex_handler_configured, _llamaindex_handler_setup_attempted, _llamaindex_handler_setup_error

    if _llamaindex_handler_configured:
        return True

    if _llamaindex_handler_setup_attempted:
        return False

    if not _is_langfuse_enabled():
        return False

    _llamaindex_handler_setup_attempted = True

    try:
        from llama_index.core import set_global_handler

        _ensure_langfuse_env_from_settings()
        set_global_handler("langfuse")

        _llamaindex_handler_configured = True
        logger.info(
            "LlamaIndex Langfuse global handler configured",
            extra={
                "langfuse_host": settings.langfuse_host,
                "langfuse_env": settings.langfuse_env,
            },
        )
        return True
    except Exception as exc:
        _llamaindex_handler_setup_error = str(exc)
        logger.warning(
            f"LlamaIndex Langfuse global handler setup failed: {exc}",
            extra={"error": str(exc)},
        )
        return False


def set_llamaindex_trace_params(
    name: str,
    metadata: Optional[Mapping[str, Any]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[Any] = None,
) -> None:
    """
    Official per-request trace metadata wiring:
      from llama_index.core import global_handler
      global_handler.set_trace_params(...)
    """
    if not _is_langfuse_enabled():
        return

    if not configure_llamaindex_langfuse_handler():
        return

    try:
        from llama_index.core import global_handler
    except Exception:
        return

    if global_handler is None or not hasattr(global_handler, "set_trace_params"):
        return

    params: Dict[str, Any] = {
        "metadata": {"trace_name": name, **(dict(metadata or {}))},
        "session_id": session_id,
        "user_id": user_id,
    }
    params = {k: v for k, v in params.items() if v not in (None, "", {})}

    if not params:
        return

    try:
        global_handler.set_trace_params(**params)
    except Exception as exc:
        logger.warning("Failed to set LlamaIndex Langfuse trace params", extra={"error": str(exc)})


# Backward-compatible helpers used by existing callsites.
@contextmanager
def trace_request(name: str, metadata: Optional[Mapping[str, Any]] = None, **kwargs: Any) -> Iterator[Any]:
    if _is_langfuse_enabled():
        set_llamaindex_trace_params(
            name=name,
            metadata=metadata,
            session_id=kwargs.get("session_id"),
            user_id=kwargs.get("user_id"),
        )
    yield None


@contextmanager
def trace_span(name: str, trace: Any = None, metadata: Optional[Mapping[str, Any]] = None, **kwargs: Any) -> Iterator[Any]:
    # Official callback handler captures framework-level events.
    yield None


async def trace_async_call(
    name: str,
    coro: Any,
    metadata: Optional[Mapping[str, Any]] = None,
    trace: Any = None,
) -> Any:
    return await coro


def record_chunk_event(name: str, metadata: Optional[Mapping[str, Any]] = None, trace: Any = None) -> None:
    return


def flush_langfuse() -> None:
    # No direct SDK flush in official set_global_handler path.
    return


def log_langfuse_startup_status() -> None:
    enabled = bool(settings.langfuse_enabled)
    configured = bool(
        (settings.langfuse_host or "").strip()
        and (settings.langfuse_public_key or "").strip()
        and (settings.langfuse_secret_key or "").strip()
    )

    startup_info = {
        "langfuse_enabled": enabled,
        "langfuse_configured": configured,
        "langfuse_active": bool(enabled and configured),
        "langfuse_env": settings.langfuse_env,
        "langfuse_integration": "llamaindex_global_handler_official",
    }

    if not startup_info["langfuse_active"]:
        logger.info("Langfuse startup status", extra=startup_info)
        return

    startup_info["langfuse_ready"] = bool(configure_llamaindex_langfuse_handler())
    startup_info["langfuse_setup_error"] = _llamaindex_handler_setup_error
    logger.info("Langfuse startup status", extra=startup_info)
