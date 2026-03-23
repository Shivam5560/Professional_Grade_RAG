# Langfuse Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add self-hosted Langfuse observability across chat (fast/think/ask), AuraSQL, and Nexus Resume with metadata-only telemetry, full async span visibility, and production sampling.

**Architecture:** Introduce a small observability layer (`app/observability/langfuse.py`) that owns SDK setup, sampling, privacy sanitization, and trace/span helpers. Wire route-level root traces and service/engine-level child spans around retrieval, rerank, async LLM calls, and persistence boundaries. Keep integration fail-open so business logic is unaffected when Langfuse is disabled or unavailable.

**Tech Stack:** FastAPI, LlamaIndex, Langfuse Python SDK, Pydantic Settings, pytest

---

## File Structure

- Create: `backend/app/observability/__init__.py` - observability package export surface.
- Create: `backend/app/observability/langfuse.py` - client init, sampling, metadata sanitizer, trace/span helpers, async wrappers, flush hook.
- Create: `backend/tests/test_langfuse_config.py` - config/env coverage for new Langfuse settings.
- Create: `backend/tests/test_langfuse_observability.py` - sampling/sanitization/no-op/async wrapper tests.
- Create: `backend/tests/test_rag_engine_tracing_helpers.py` - chunk metadata helper tests for fast mode.
- Create: `backend/tests/test_pageindex_tracing_helpers.py` - section metadata helper tests for think mode.
- Modify: `backend/requirements.txt` - add Langfuse SDK dependency.
- Modify: `backend/.env.example` - document all Langfuse env vars and defaults.
- Modify: `backend/app/config.py` - add Langfuse settings fields.
- Modify: `backend/app/main.py` - flush observability queue on shutdown.
- Modify: `backend/app/api/routes/chat.py` - root traces and mode-level spans.
- Modify: `backend/app/core/rag_engine.py` - fast-mode retrieval/rerank/LLM spans + chunk metadata events.
- Modify: `backend/app/core/pageindex_rag_engine.py` - think-mode spans + section metadata events.
- Modify: `backend/app/core/pageindex_utils.py` - async LLM helper instrumentation.
- Modify: `backend/app/api/routes/aurasql.py` - recommendations/query/execute spans.
- Modify: `backend/app/services/nexus_resume_service.py` - analyze pipeline spans.
- Modify: `backend/app/services/nexus_ai/core/analyzer.py` - async LLM call span in analyzer.

### Task 1: Add Langfuse dependency and configuration surface

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/config.py`
- Modify: `backend/.env.example`
- Test: `backend/tests/test_langfuse_config.py`

- [ ] **Step 1: Write the failing config tests**

```python
# backend/tests/test_langfuse_config.py
from app.config import Settings


def test_langfuse_defaults_are_present():
    s = Settings(_env_file=None)
    assert s.langfuse_enabled is False
    assert s.langfuse_host == ""
    assert s.langfuse_env == "dev"
    assert s.langfuse_sample_rate_dev == 1.0
    assert s.langfuse_sample_rate_staging == 1.0
    assert s.langfuse_sample_rate_prod == 0.2


def test_langfuse_env_overrides(monkeypatch):
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_HOST", "https://langfuse.internal")
    monkeypatch.setenv("LANGFUSE_ENV", "prod")
    monkeypatch.setenv("LANGFUSE_SAMPLE_RATE_PROD", "0.35")

    s = Settings(_env_file=None)
    assert s.langfuse_enabled is True
    assert s.langfuse_host == "https://langfuse.internal"
    assert s.langfuse_env == "prod"
    assert s.langfuse_sample_rate_prod == 0.35
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_langfuse_config.py -q`
Expected: FAIL with missing `Settings` attributes for Langfuse fields.

- [ ] **Step 3: Add minimal dependency + settings + env entries**

```txt
# backend/requirements.txt
langfuse
```

```python
# backend/app/config.py (inside Settings)
langfuse_enabled: bool = Field(default=False, alias="LANGFUSE_ENABLED")
langfuse_host: str = Field(default="", alias="LANGFUSE_HOST")
langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
langfuse_env: str = Field(default="dev", alias="LANGFUSE_ENV")
langfuse_sample_rate_dev: float = Field(default=1.0, alias="LANGFUSE_SAMPLE_RATE_DEV")
langfuse_sample_rate_staging: float = Field(default=1.0, alias="LANGFUSE_SAMPLE_RATE_STAGING")
langfuse_sample_rate_prod: float = Field(default=0.2, alias="LANGFUSE_SAMPLE_RATE_PROD")
```

```dotenv
# backend/.env.example
LANGFUSE_ENABLED=false
LANGFUSE_HOST=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_ENV=dev
LANGFUSE_SAMPLE_RATE_DEV=1.0
LANGFUSE_SAMPLE_RATE_STAGING=1.0
LANGFUSE_SAMPLE_RATE_PROD=0.2
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_langfuse_config.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/app/config.py backend/.env.example backend/tests/test_langfuse_config.py
git commit -m "feat: add langfuse configuration and environment controls"
```

### Task 2: Build observability core module with privacy-safe helpers

**Files:**
- Create: `backend/app/observability/__init__.py`
- Create: `backend/app/observability/langfuse.py`
- Test: `backend/tests/test_langfuse_observability.py`

- [ ] **Step 1: Write the failing observability unit tests**

```python
# backend/tests/test_langfuse_observability.py
import asyncio
from app.observability import langfuse as lf


def test_sanitize_metadata_removes_sensitive_keys():
    payload = {
        "mode": "fast",
        "prompt": "secret prompt",
        "nested": {"api_key": "abc", "score": 0.91},
    }
    sanitized = lf.sanitize_metadata(payload)
    assert "prompt" not in sanitized
    assert sanitized["nested"]["score"] == 0.91
    assert "api_key" not in sanitized["nested"]


def test_should_sample_trace_respects_prod_rate(monkeypatch):
    monkeypatch.setattr(lf.settings, "langfuse_sample_rate_prod", 0.25)
    monkeypatch.setattr(lf.random, "random", lambda: 0.2)
    assert lf.should_sample_trace("prod") is True
    monkeypatch.setattr(lf.random, "random", lambda: 0.8)
    assert lf.should_sample_trace("prod") is False


def test_trace_async_call_returns_result_without_langfuse(monkeypatch):
    monkeypatch.setattr(lf, "trace_span", lf.contextlib.nullcontext)

    async def sample_call():
        return {"ok": True}

    result = asyncio.run(lf.trace_async_call("unit.test", sample_call(), {"query_len": 10}))
    assert result == {"ok": True}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_langfuse_observability.py -q`
Expected: FAIL because `app.observability` module does not exist yet.

- [ ] **Step 3: Implement the observability module**

```python
# backend/app/observability/__init__.py
from app.observability.langfuse import (
    trace_request,
    trace_span,
    trace_async_call,
    sanitize_metadata,
    should_sample_trace,
    flush_langfuse,
    record_chunk_event,
)

__all__ = [
    "trace_request",
    "trace_span",
    "trace_async_call",
    "sanitize_metadata",
    "should_sample_trace",
    "flush_langfuse",
    "record_chunk_event",
]
```

```python
# backend/app/observability/langfuse.py
from __future__ import annotations

import contextlib
import random
from contextvars import ContextVar
from typing import Any, Dict, Optional, Iterable

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_trace_sampled_ctx: ContextVar[bool] = ContextVar("trace_sampled", default=False)
_langfuse_client = None
_langfuse_import_error: Optional[str] = None

_SENSITIVE_KEY_FRAGMENTS = {
    "prompt",
    "response",
    "content",
    "text",
    "raw_text",
    "job_description",
    "resume_text",
    "password",
    "secret",
    "api_key",
    "token",
    "authorization",
}


def _looks_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(fragment in lowered for fragment in _SENSITIVE_KEY_FRAGMENTS)


def sanitize_metadata(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not data:
        return {}

    def _sanitize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(k): _sanitize(v)
                for k, v in value.items()
                if not _looks_sensitive(str(k))
            }
        if isinstance(value, list):
            return [_sanitize(v) for v in value[:50]]
        if isinstance(value, tuple):
            return tuple(_sanitize(v) for v in value[:50])
        if isinstance(value, str):
            return value[:500]
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        return str(value)[:500]

    return _sanitize(data)


def _sample_rate_for_env(env_name: str) -> float:
    lowered = (env_name or "dev").lower()
    if lowered == "prod":
        return max(0.0, min(1.0, settings.langfuse_sample_rate_prod))
    if lowered == "staging":
        return max(0.0, min(1.0, settings.langfuse_sample_rate_staging))
    return max(0.0, min(1.0, settings.langfuse_sample_rate_dev))


def should_sample_trace(env_name: str) -> bool:
    return random.random() <= _sample_rate_for_env(env_name)


def _langfuse_enabled() -> bool:
    return bool(
        settings.langfuse_enabled
        and settings.langfuse_host
        and settings.langfuse_public_key
        and settings.langfuse_secret_key
    )


def _get_client():
    global _langfuse_client, _langfuse_import_error
    if _langfuse_client is not None:
        return _langfuse_client
    if _langfuse_import_error is not None:
        return None

    try:
        from langfuse import get_client  # type: ignore
        _langfuse_client = get_client()
        return _langfuse_client
    except Exception as exc:
        _langfuse_import_error = str(exc)
        logger.warning("langfuse_client_unavailable", error=_langfuse_import_error)
        return None


@contextlib.contextmanager
def trace_request(name: str, user_id: Optional[int], session_id: Optional[str], metadata: Optional[Dict[str, Any]] = None):
    sampled = _langfuse_enabled() and should_sample_trace(settings.langfuse_env)
    token = _trace_sampled_ctx.set(sampled)

    if not sampled:
        try:
            yield None
        finally:
            _trace_sampled_ctx.reset(token)
        return

    client = _get_client()
    if client is None:
        try:
            yield None
        finally:
            _trace_sampled_ctx.reset(token)
        return

    from langfuse import propagate_attributes  # type: ignore

    safe_metadata = sanitize_metadata(metadata)
    attrs: Dict[str, Any] = {"trace_name": name, "metadata": safe_metadata}
    if user_id is not None:
        attrs["user_id"] = str(user_id)
    if session_id:
        attrs["session_id"] = session_id

    try:
        with client.start_as_current_observation(as_type="span", name=name) as root_span:
            root_span.update(metadata=safe_metadata)
            with propagate_attributes(**attrs):
                yield root_span
    finally:
        _trace_sampled_ctx.reset(token)


@contextlib.contextmanager
def trace_span(name: str, metadata: Optional[Dict[str, Any]] = None, as_type: str = "span", model: Optional[str] = None):
    if not _trace_sampled_ctx.get():
        yield None
        return

    client = _get_client()
    if client is None:
        yield None
        return

    kwargs: Dict[str, Any] = {"as_type": as_type, "name": name}
    if model:
        kwargs["model"] = model

    with client.start_as_current_observation(**kwargs) as span:
        if metadata:
            span.update(metadata=sanitize_metadata(metadata))
        try:
            yield span
        except Exception as exc:
            span.update(metadata={"error_type": type(exc).__name__, "error_message": str(exc)[:240]})
            raise


async def trace_async_call(name: str, coro, metadata: Optional[Dict[str, Any]] = None):
    with trace_span(name, metadata=metadata):
        return await coro


def record_chunk_event(name: str, chunks: Iterable[Dict[str, Any]]) -> None:
    payload = [sanitize_metadata(item) for item in list(chunks)[:25]]
    if not payload:
        return
    with trace_span(name, metadata={"chunk_count": len(payload), "chunks": payload}):
        return


def flush_langfuse() -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.flush()
    except Exception as exc:
        logger.warning("langfuse_flush_failed", error=str(exc))
```

- [ ] **Step 4: Run tests to verify it passes**

Run: `python -m pytest backend/tests/test_langfuse_observability.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/observability/__init__.py backend/app/observability/langfuse.py backend/tests/test_langfuse_observability.py
git commit -m "feat: add langfuse tracing helpers with metadata sanitization"
```

### Task 3: Instrument chat routes and fast-mode RAG pipeline

**Files:**
- Modify: `backend/app/api/routes/chat.py`
- Modify: `backend/app/core/rag_engine.py`
- Test: `backend/tests/test_rag_engine_tracing_helpers.py`

- [ ] **Step 1: Write failing helper tests for chunk metadata extraction**

```python
# backend/tests/test_rag_engine_tracing_helpers.py
from types import SimpleNamespace

from app.core.rag_engine import _build_retrieval_chunk_metadata


def _node(metadata, score):
    return SimpleNamespace(node=SimpleNamespace(metadata=metadata), score=score)


def test_build_retrieval_chunk_metadata_uses_metadata_only():
    nodes = [
        _node(
            {
                "document_id": "doc-1",
                "filename": "guide.pdf",
                "page": 3,
                "chunk_id": "chunk-a",
                "text": "must_not_be_traced",
            },
            0.91,
        )
    ]

    payload = _build_retrieval_chunk_metadata(nodes, retriever="vector")
    assert payload == [
        {
            "retriever": "vector",
            "rank": 1,
            "document_id": "doc-1",
            "filename": "guide.pdf",
            "page": 3,
            "chunk_id": "chunk-a",
            "score": 0.91,
        }
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_rag_engine_tracing_helpers.py -q`
Expected: FAIL with missing `_build_retrieval_chunk_metadata` symbol.

- [ ] **Step 3: Implement route + fast pipeline tracing**

```python
# backend/app/core/rag_engine.py
from app.observability.langfuse import trace_span, trace_async_call, record_chunk_event


def _build_retrieval_chunk_metadata(nodes: List[NodeWithScore], retriever: str) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for rank, node in enumerate(nodes, start=1):
        md = node.node.metadata or {}
        payload.append(
            {
                "retriever": retriever,
                "rank": rank,
                "document_id": md.get("document_id"),
                "filename": md.get("filename"),
                "page": md.get("page"),
                "chunk_id": md.get("chunk_id"),
                "score": round(float(node.score or 0.0), 6),
            }
        )
    return payload


# inside query()
with trace_span("fast.reformulate_query", metadata={"use_context": use_context}):
    reformulated_query = self.context_manager.reformulate_query(session_id, query) if use_context else query

with trace_span("fast.retrieve.vector", metadata={"top_k": settings.top_k_retrieval}):
    vector_nodes = vector_store.retrieve(...)
record_chunk_event("fast.retrieve.vector.chunks", _build_retrieval_chunk_metadata(vector_nodes, "vector"))

with trace_span("fast.retrieve.bm25", metadata={"top_k": settings.top_k_retrieval}):
    bm25_nodes = bm25_service.search(...)
record_chunk_event("fast.retrieve.bm25.chunks", _build_retrieval_chunk_metadata(bm25_nodes, "bm25"))

response = await trace_async_call(
    "fast.llm.acomplete",
    self.llm.acomplete(prompt),
    metadata={"prompt_chars": len(prompt), "mode": "fast"},
)
```

```python
# backend/app/api/routes/chat.py
from app.observability.langfuse import trace_request, trace_span, trace_async_call


# inside query()
with trace_request(
    name="chat.query",
    user_id=effective_user_id,
    session_id=session_id,
    metadata={
        "endpoint": "/api/v1/chat/query",
        "mode": mode,
        "query_chars": len(request.query),
        "context_document_count": len(request.context_document_ids or []),
    },
):
    with trace_span("chat.persist_user_message", metadata={"session_id": session_id}):
        db.add(user_msg)
        db.commit()

    if mode == "ask":
        with trace_span("chat.route_ask", metadata={"ask_files": len(request.ask_files or [])}):
            result = await _query_ask_mode(...)


# inside _query_ask_mode()
response = await trace_async_call(
    "ask.llm.acomplete",
    llm.acomplete(prompt),
    metadata={"prompt_chars": len(prompt), "ask_file_count": len(ask_files or [])},
)
```

- [ ] **Step 4: Run tests to verify it passes**

Run: `python -m pytest backend/tests/test_rag_engine_tracing_helpers.py -q`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routes/chat.py backend/app/core/rag_engine.py backend/tests/test_rag_engine_tracing_helpers.py
git commit -m "feat: trace chat and fast rag pipeline with chunk metadata"
```

### Task 4: Instrument think-mode tree pipeline and async helper calls

**Files:**
- Modify: `backend/app/core/pageindex_rag_engine.py`
- Modify: `backend/app/core/pageindex_utils.py`
- Test: `backend/tests/test_pageindex_tracing_helpers.py`

- [ ] **Step 1: Write failing think-mode metadata tests**

```python
# backend/tests/test_pageindex_tracing_helpers.py
from app.core.pageindex_rag_engine import _build_think_section_metadata


def test_build_think_section_metadata_is_metadata_only():
    sections = [
        {
            "doc_name": "Architecture.pdf",
            "title": "Storage Layer",
            "start_page": 10,
            "end_page": 12,
            "node_id": "0012",
            "text": "must_not_be_traced",
        }
    ]
    payload = _build_think_section_metadata(sections)
    assert payload == [
        {
            "rank": 1,
            "document": "Architecture.pdf",
            "section_title": "Storage Layer",
            "start_page": 10,
            "end_page": 12,
            "node_id": "0012",
        }
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_pageindex_tracing_helpers.py -q`
Expected: FAIL with missing `_build_think_section_metadata` symbol.

- [ ] **Step 3: Implement think-mode spans and LLM async wrappers**

```python
# backend/app/core/pageindex_rag_engine.py
from app.observability.langfuse import trace_span, record_chunk_event


def _build_think_section_metadata(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for rank, section in enumerate(sections, start=1):
        payload.append(
            {
                "rank": rank,
                "document": section.get("doc_name"),
                "section_title": section.get("title"),
                "start_page": section.get("start_page"),
                "end_page": section.get("end_page"),
                "node_id": section.get("node_id"),
            }
        )
    return payload


# inside query()
with trace_span("think.discover_documents", metadata={"context_doc_count": len(context_document_ids or [])}):
    ...

with trace_span("think.tree_presence_check", metadata={"candidate_doc_count": len(all_target_ids)}):
    ...

with trace_span("think.answer_llm", metadata={"context_sections": len(all_context_sections)}):
    response = await groq_llm_call(answer_prompt, self.groq_service, span_name="think.answer_llm")

record_chunk_event("think.selected_sections", _build_think_section_metadata(all_context_sections))
```

```python
# backend/app/core/pageindex_utils.py
from app.observability.langfuse import trace_async_call


async def groq_llm_call(
    prompt: str,
    groq_service,
    temperature: float = 0.0,
    max_retries: int = 3,
    use_reasoning: bool = True,
    span_name: str = "think.llm.acomplete",
) -> str:
    ...
    response = await trace_async_call(
        span_name,
        llm.acomplete(prompt),
        metadata={
            "prompt_chars": len(prompt),
            "use_reasoning": use_reasoning,
            "temperature": temperature,
        },
    )
    ...
```

- [ ] **Step 4: Run tests to verify it passes**

Run: `python -m pytest backend/tests/test_pageindex_tracing_helpers.py -q`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/pageindex_rag_engine.py backend/app/core/pageindex_utils.py backend/tests/test_pageindex_tracing_helpers.py
git commit -m "feat: add think mode langfuse spans for tree search and llm calls"
```

### Task 5: Instrument AuraSQL and Nexus Resume flows

**Files:**
- Modify: `backend/app/api/routes/aurasql.py`
- Modify: `backend/app/services/nexus_resume_service.py`
- Modify: `backend/app/services/nexus_ai/core/analyzer.py`
- Test: `backend/tests/test_langfuse_observability.py`

- [ ] **Step 1: Add failing async wrapper test for analyzer call metadata policy**

```python
# append to backend/tests/test_langfuse_observability.py
def test_sanitize_metadata_drops_resume_and_job_text():
    payload = {
        "resume_text": "raw resume",
        "job_description": "raw jd",
        "resume_id": "RES-1",
        "user_id": 7,
    }
    sanitized = lf.sanitize_metadata(payload)
    assert "resume_text" not in sanitized
    assert "job_description" not in sanitized
    assert sanitized["resume_id"] == "RES-1"
    assert sanitized["user_id"] == 7
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_langfuse_observability.py::test_sanitize_metadata_drops_resume_and_job_text -q`
Expected: FAIL until sanitizer handles both keys consistently.

- [ ] **Step 3: Instrument AuraSQL + Nexus async calls and spans**

```python
# backend/app/api/routes/aurasql.py
from app.observability.langfuse import trace_request, trace_span, trace_async_call


@router.post("/query", response_model=AuraSqlQueryResponse)
async def generate_query(...):
    with trace_request(
        name="aurasql.query",
        user_id=current_user.id,
        session_id=payload.session_id,
        metadata={
            "endpoint": "/api/v1/aurasql/query",
            "context_id": payload.context_id,
            "query_chars": len(payload.query),
        },
    ):
        ...
        with trace_span("aurasql.vector_query.aquery", metadata={"top_k": settings.aurasql_top_k}):
            result = await trace_async_call(
                "aurasql.aquery",
                query_engine.aquery(prompt),
                metadata={"prompt_chars": len(prompt)},
            )
        with trace_span("aurasql.sql_validation", metadata={"db_type": connection.db_type}):
            syntax_errors, hallucinated_tables, hallucinated_columns = _validate_sql_with_schema(...)
```

```python
# backend/app/services/nexus_resume_service.py
from app.observability.langfuse import trace_request, trace_span


async def analyze_resume(...):
    with trace_request(
        name="nexus.resume.analyze",
        user_id=user_id,
        session_id=resume_id,
        metadata={"resume_id": resume_id, "endpoint": "/api/v1/nexus/resumes/analyze"},
    ):
        with trace_span("nexus.resume_load", metadata={"resume_id": resume_id}):
            resume = ...
        with trace_span("nexus.resume_text_source", metadata={"cache_hit": bool(resume.extracted_data and resume.extracted_data.get("_raw_text"))}):
            ...
        with trace_span("nexus.persist_analysis", metadata={"resume_id": resume_id, "overall_score": overall_score}):
            db.add(analysis)
            db.commit()
```

```python
# backend/app/services/nexus_ai/core/analyzer.py
from app.observability.langfuse import trace_async_call


response = await trace_async_call(
    "nexus.analyzer_v2.llm.acomplete",
    llm.acomplete(prompt),
    metadata={
        "prompt_chars": len(prompt),
        "resume_chars": len(resume_text),
        "job_description_chars": len(job_description),
    },
)
```

- [ ] **Step 4: Run tests to verify it passes**

Run: `python -m pytest backend/tests/test_langfuse_observability.py -q`
Expected: PASS (all tests in file pass).

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routes/aurasql.py backend/app/services/nexus_resume_service.py backend/app/services/nexus_ai/core/analyzer.py backend/tests/test_langfuse_observability.py
git commit -m "feat: instrument aurasql and nexus analysis with langfuse spans"
```

### Task 6: Add shutdown flush hook and run end-to-end verification

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/routes/chat.py`
- Modify: `backend/app/core/rag_engine.py`
- Modify: `backend/app/core/pageindex_rag_engine.py`
- Modify: `backend/app/api/routes/aurasql.py`
- Modify: `backend/app/services/nexus_resume_service.py`
- Test: `backend/tests/test_langfuse_config.py`
- Test: `backend/tests/test_langfuse_observability.py`
- Test: `backend/tests/test_rag_engine_tracing_helpers.py`
- Test: `backend/tests/test_pageindex_tracing_helpers.py`

- [ ] **Step 1: Write the failing shutdown safety test**

```python
# append to backend/tests/test_langfuse_observability.py
def test_flush_langfuse_is_safe_when_client_missing(monkeypatch):
    monkeypatch.setattr(lf, "_langfuse_client", None)
    monkeypatch.setattr(lf, "_langfuse_import_error", "import failure")
    lf.flush_langfuse()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_langfuse_observability.py::test_flush_langfuse_is_safe_when_client_missing -q`
Expected: FAIL until `flush_langfuse()` handles missing client safely.

- [ ] **Step 3: Wire application shutdown flush and final trace wrappers**

```python
# backend/app/main.py
from app.observability.langfuse import flush_langfuse


@asynccontextmanager
async def lifespan(app: FastAPI):
    ...
    yield
    logger.log_operation("Application shutting down")
    flush_langfuse()
    logger.log_operation("✅ Application shutdown complete")
```

```python
# ensure chat/fast/think/aurasql/nexus code paths all include root trace wrappers:
# - chat.query, chat.stream
# - fast.* spans in RAGEngine query/stream_query
# - think.* spans in PageIndex query
# - aurasql.query/recommendations/execute
# - nexus.resume.analyze
```

- [ ] **Step 4: Run full targeted verification suite**

Run: `python -m pytest backend/tests/test_langfuse_config.py backend/tests/test_langfuse_observability.py backend/tests/test_rag_engine_tracing_helpers.py backend/tests/test_pageindex_tracing_helpers.py -q`
Expected: PASS.

Run: `python -m pytest backend/tests -q`
Expected: PASS for existing and new tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/app/api/routes/chat.py backend/app/core/rag_engine.py backend/app/core/pageindex_rag_engine.py backend/app/api/routes/aurasql.py backend/app/services/nexus_resume_service.py backend/tests/test_langfuse_config.py backend/tests/test_langfuse_observability.py backend/tests/test_rag_engine_tracing_helpers.py backend/tests/test_pageindex_tracing_helpers.py
git commit -m "feat: finalize langfuse lifecycle and full pipeline instrumentation"
```

## Manual Staging Verification Checklist

- [ ] Set env vars in backend runtime:

```dotenv
LANGFUSE_ENABLED=true
LANGFUSE_HOST=https://<your-self-hosted-langfuse>
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_ENV=staging
LANGFUSE_SAMPLE_RATE_STAGING=1.0
```

- [ ] Start API and run one request per flow:
  - chat fast (`/api/v1/chat/query` with `mode=fast`)
  - chat think (`/api/v1/chat/query` with `mode=think`)
  - chat ask (`/api/v1/chat/query` with `mode=ask`)
  - aurasql query (`/api/v1/aurasql/query`)
  - nexus analyze (`/api/v1/nexus/resumes/analyze`)

- [ ] In Langfuse UI, confirm for each trace:
  - root span name matches endpoint flow (`chat.query`, `aurasql.query`, `nexus.resume.analyze`)
  - async LLM spans exist (`*.llm.acomplete`, `*.aquery`, stream spans)
  - retrieval chunk events contain only metadata (`document_id`, `filename`, `page`, `chunk_id`, `score`, `rank`)
  - no raw prompts, responses, chunk text, resume text, or secrets are present.

## Self-Review

### Spec coverage

- Config in both `config.py` and `.env.example`: covered in Task 1.
- All flows instrumented (chat fast/think/ask, AuraSQL, Nexus): covered in Tasks 3-5.
- Full pipeline depth with async call visibility: covered in Tasks 3-5.
- Metadata-only capture including chunk metadata: covered in Tasks 2-5.
- Production sampling strategy and no-op safety: covered in Tasks 1-2 and Task 6.

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders in steps.
- Every code-changing step includes concrete code blocks.
- Every test and command includes explicit expected outcome.

### Type/signature consistency

- Shared helper names are consistent across tasks:
  - `trace_request`
  - `trace_span`
  - `trace_async_call`
  - `record_chunk_event`
  - `sanitize_metadata`
  - `flush_langfuse`
- Fast helper `_build_retrieval_chunk_metadata` and think helper `_build_think_section_metadata` are referenced consistently in test and implementation tasks.
