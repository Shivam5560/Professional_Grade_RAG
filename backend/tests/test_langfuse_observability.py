import asyncio
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.observability import langfuse
from app.observability.langfuse import trace_async_call


def test_trace_async_call_returns_result_without_langfuse(monkeypatch) -> None:
    monkeypatch.setattr(settings, "langfuse_enabled", False)

    async def _sample_coro() -> dict:
        return {"status": "ok", "value": 42}

    result = asyncio.run(trace_async_call("unit-test-call", _sample_coro(), metadata={"safe": "value"}))

    assert result == {"status": "ok", "value": 42}


def test_trace_request_propagates_inner_exception() -> None:
    expected = RuntimeError("request boom")

    with pytest.raises(RuntimeError) as caught:
        with langfuse.trace_request("request-trace"):
            raise expected

    assert caught.value is expected


def test_trace_span_propagates_inner_exception() -> None:
    expected = ValueError("span boom")

    with pytest.raises(ValueError) as caught:
        with langfuse.trace_span("child-span", trace=None):
            raise expected

    assert caught.value is expected


def test_configure_llamaindex_langfuse_handler_is_false_when_disabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "langfuse_enabled", False)
    monkeypatch.setattr(settings, "langfuse_host", "")
    monkeypatch.setattr(settings, "langfuse_public_key", "")
    monkeypatch.setattr(settings, "langfuse_secret_key", "")
    monkeypatch.setattr(langfuse, "_llamaindex_handler_configured", False)
    monkeypatch.setattr(langfuse, "_llamaindex_handler_setup_attempted", False)

    assert langfuse.configure_llamaindex_langfuse_handler() is False


def test_configure_llamaindex_langfuse_handler_sets_global_handler(monkeypatch) -> None:
    called = {"count": 0, "kwargs": None}

    def _fake_set_global_handler(handler_name, **kwargs):
        assert handler_name == "langfuse"
        called["count"] += 1
        called["kwargs"] = kwargs

    monkeypatch.setattr(settings, "langfuse_enabled", True)
    monkeypatch.setattr(settings, "langfuse_host", "https://cloud.langfuse.com")
    monkeypatch.setattr(settings, "langfuse_public_key", "pk-test")
    monkeypatch.setattr(settings, "langfuse_secret_key", "sk-test")
    monkeypatch.setattr(langfuse, "_llamaindex_handler_configured", False)
    monkeypatch.setattr(langfuse, "_llamaindex_handler_setup_attempted", False)
    monkeypatch.setattr(langfuse, "_llamaindex_handler_setup_error", None)

    import types

    fake_module = types.SimpleNamespace(set_global_handler=_fake_set_global_handler)
    monkeypatch.setitem(sys.modules, "llama_index.core", fake_module)

    ready = langfuse.configure_llamaindex_langfuse_handler()

    assert ready is True
    assert called["count"] == 1
    assert called["kwargs"] == {}


def test_set_llamaindex_trace_params_calls_global_handler(monkeypatch) -> None:
    captured = {}

    def _fake_set_trace_params(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(settings, "langfuse_enabled", True)
    monkeypatch.setattr(settings, "langfuse_host", "https://cloud.langfuse.com")
    monkeypatch.setattr(settings, "langfuse_public_key", "pk-test")
    monkeypatch.setattr(settings, "langfuse_secret_key", "sk-test")
    monkeypatch.setattr(langfuse, "configure_llamaindex_langfuse_handler", lambda: True)
    monkeypatch.setattr(langfuse, "_llamaindex_handler_configured", True)

    import types

    fake_module = types.SimpleNamespace(global_handler=types.SimpleNamespace(set_trace_params=_fake_set_trace_params))
    monkeypatch.setitem(sys.modules, "llama_index.core", fake_module)

    langfuse.set_llamaindex_trace_params(
        name="chat.query",
        metadata={"mode": "fast"},
        session_id="session-1",
        user_id=1,
    )

    assert captured["session_id"] == "session-1"
    assert captured["user_id"] == 1
    assert captured["metadata"]["trace_name"] == "chat.query"
    assert captured["metadata"]["mode"] == "fast"


def test_trace_request_sets_trace_params_when_enabled(monkeypatch) -> None:
    called = {"count": 0}

    def _fake_set_trace_params(name, metadata=None, session_id=None, user_id=None):
        called["count"] += 1
        assert name == "chat.query"
        assert metadata == {"mode": "fast"}
        assert session_id == "session-1"
        assert user_id == 1

    monkeypatch.setattr(settings, "langfuse_enabled", True)
    monkeypatch.setattr(settings, "langfuse_host", "https://cloud.langfuse.com")
    monkeypatch.setattr(settings, "langfuse_public_key", "pk-test")
    monkeypatch.setattr(settings, "langfuse_secret_key", "sk-test")
    monkeypatch.setattr(langfuse, "set_llamaindex_trace_params", _fake_set_trace_params)

    with langfuse.trace_request("chat.query", metadata={"mode": "fast"}, session_id="session-1", user_id=1):
        pass

    assert called["count"] == 1


def test_trace_request_is_noop_when_disabled(monkeypatch) -> None:
    called = {"count": 0}

    def _fake_set_trace_params(*args, **kwargs):
        called["count"] += 1

    monkeypatch.setattr(settings, "langfuse_enabled", False)
    monkeypatch.setattr(langfuse, "set_llamaindex_trace_params", _fake_set_trace_params)

    with langfuse.trace_request("chat.query", metadata={"mode": "fast"}, session_id="session-1", user_id=1):
        pass

    assert called["count"] == 0


def test_flush_langfuse_is_noop() -> None:
    langfuse.flush_langfuse()


def test_log_langfuse_startup_status_logs_when_inactive(monkeypatch) -> None:
    captured = {}

    def _fake_info(message, extra=None):
        captured["message"] = message
        captured["extra"] = extra

    monkeypatch.setattr(settings, "langfuse_enabled", False)
    monkeypatch.setattr(settings, "langfuse_host", "")
    monkeypatch.setattr(settings, "langfuse_public_key", "")
    monkeypatch.setattr(settings, "langfuse_secret_key", "")
    monkeypatch.setattr(langfuse.logger, "info", _fake_info)

    langfuse.log_langfuse_startup_status()

    assert captured["message"] == "Langfuse startup status"
    assert captured["extra"]["langfuse_enabled"] is False
    assert captured["extra"]["langfuse_configured"] is False
    assert captured["extra"]["langfuse_active"] is False


def test_log_langfuse_startup_status_initializes_when_active(monkeypatch) -> None:
    called = {"count": 0}

    def _fake_configure_handler():
        called["count"] += 1
        return True

    monkeypatch.setattr(settings, "langfuse_enabled", True)
    monkeypatch.setattr(settings, "langfuse_host", "https://cloud.langfuse.com")
    monkeypatch.setattr(settings, "langfuse_public_key", "pk-test")
    monkeypatch.setattr(settings, "langfuse_secret_key", "sk-test")
    monkeypatch.setattr(langfuse, "configure_llamaindex_langfuse_handler", _fake_configure_handler)

    langfuse.log_langfuse_startup_status()

    assert called["count"] == 1


def test_chat_stream_think_mode_sets_trace_params_for_stream_lifecycle(monkeypatch) -> None:
    from app.api.routes import chat as chat_module
    from app.models.schemas import ChatRequest

    captured = {}

    def _fake_set_llamaindex_trace_params(**kwargs):
        captured["trace_kwargs"] = kwargs

    class _FakeDbSession:
        def __init__(self):
            self.user_id = 1
            self.updated_at = None

    class _FakeQuery:
        def __init__(self, db_session):
            self._db_session = db_session

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return self._db_session

        def order_by(self, *args, **kwargs):
            return self

        def limit(self, *args, **kwargs):
            return self

        def all(self):
            return []

    class _FakeDb:
        def __init__(self):
            self._db_session = _FakeDbSession()

        def query(self, model):
            return _FakeQuery(self._db_session)

        def add(self, obj):
            return None

        def commit(self):
            return None

    class _FakeThinkEngine:
        async def query(self, **kwargs):
            captured["think_query_trace"] = kwargs.get("trace")
            captured["think_query_session_id"] = kwargs.get("session_id")
            return {
                "answer": "think answer",
                "confidence_score": 80.0,
                "confidence_level": "high",
                "sources": [],
                "processing_time_ms": 10.0,
                "reasoning": "reasoning",
                "session_id": kwargs["session_id"],
                "token_usage": None,
            }

    async def _consume_stream(response) -> str:
        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
        return "".join(chunks)

    monkeypatch.setattr(chat_module, "set_llamaindex_trace_params", _fake_set_llamaindex_trace_params)
    monkeypatch.setattr(chat_module, "_load_recent_session_messages", lambda db, session_id: [])
    monkeypatch.setattr(chat_module, "_format_history_for_prompt", lambda messages: "")
    monkeypatch.setattr(chat_module, "_sync_context_manager_from_db", lambda session_id, messages: None)
    monkeypatch.setattr(chat_module, "extract_drawio_xml", lambda answer: (answer, None))
    monkeypatch.setattr(chat_module, "is_diagram_request", lambda query: False)
    monkeypatch.setattr("app.core.pageindex_rag_engine.get_pageindex_rag_engine", lambda: _FakeThinkEngine())

    request = ChatRequest(
        query="why",
        session_id="session-1",
        mode="think",
        context_document_ids=["doc-1", "doc-2"],
    )
    response = asyncio.run(
        chat_module.stream_query(
            request=request,
            db=_FakeDb(),
            current_user=SimpleNamespace(id=1),
        )
    )

    payload = asyncio.run(_consume_stream(response))

    assert "event: final" in payload
    assert captured["think_query_trace"] is None
    assert captured["think_query_session_id"] == "session-1"
    assert captured["trace_kwargs"]["name"] == "chat.stream"
    assert captured["trace_kwargs"]["metadata"] == {
        "mode": "think",
        "context_doc_count": 2,
        "has_ask_files": False,
        "session_id": "session-1",
    }
    assert captured["trace_kwargs"]["session_id"] == "session-1"
    assert captured["trace_kwargs"]["user_id"] == "1"
