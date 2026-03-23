import asyncio
import os
import sys
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class _FakeDb:
    def __init__(self, context=None, connection=None, session=None):
        self._context = context
        self._connection = connection
        self._session = session
        self.added = []
        self.commits = 0

    def query(self, model):
        name = getattr(model, "__name__", "")
        if name == "AuraSqlContext":
            return _FakeQuery(self._context)
        if name == "AuraSqlConnection":
            return _FakeQuery(self._connection)
        if name == "AuraSqlChatSession":
            return _FakeQuery(self._session)
        raise AssertionError(f"Unexpected model queried: {name}")

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1


def test_aurasql_recommendations_uses_request_trace_and_schema_fallback(monkeypatch) -> None:
    from app.api.routes import aurasql as aurasql_module
    from app.models.aurasql_schemas import AuraSqlRecommendationsRequest

    fake_trace = object()
    captured = {
        "request_name": None,
        "request_metadata": None,
        "span_calls": [],
        "async_call": None,
    }

    @contextmanager
    def _fake_trace_request(name, metadata=None, **kwargs):
        captured["request_name"] = name
        captured["request_metadata"] = metadata
        yield fake_trace

    @contextmanager
    def _fake_trace_span(name, trace=None, metadata=None, **kwargs):
        captured["span_calls"].append((name, trace, metadata))
        yield None

    async def _fake_trace_async_call(name, coro, metadata=None, trace=None):
        captured["async_call"] = (name, trace, metadata)
        return await coro

    class _FakeLlmService:
        def get_aurasql_llm(self):
            return None

    class _FakeQueryEngine:
        async def aquery(self, _prompt):
            return SimpleNamespace(response="")

    class _FakeVectorStore:
        def get_query_engine(self, _vector_context_id):
            return _FakeQueryEngine()

    context = SimpleNamespace(
        id="ctx-1",
        user_id=1,
        table_names=["users"],
        schema_snapshot={"orders": [{"column_name": "id"}]},
        vector_context_id="vector-ctx-1",
    )

    monkeypatch.setattr(aurasql_module, "trace_request", _fake_trace_request)
    monkeypatch.setattr(aurasql_module, "trace_span", _fake_trace_span)
    monkeypatch.setattr(aurasql_module, "trace_async_call", _fake_trace_async_call)
    monkeypatch.setattr(aurasql_module, "get_llm_service", lambda: _FakeLlmService())
    monkeypatch.setattr(aurasql_module, "get_aurasql_vector_store", lambda: _FakeVectorStore())

    response = asyncio.run(
        aurasql_module.get_recommendations(
            payload=AuraSqlRecommendationsRequest(context_id="ctx-1"),
            db=_FakeDb(context=context),
            current_user=SimpleNamespace(id=1),
        )
    )

    assert response.recommendations[0] == "Show recent rows from orders."
    assert captured["request_name"] == "aurasql.recommendations"
    assert captured["request_metadata"] == {
        "context_id": "ctx-1",
        "table_count": 1,
    }
    assert captured["async_call"] == (
        "aurasql.recommendations.vector_aquery",
        fake_trace,
        {"vector_context_id": "vector-ctx-1"},
    )
    assert ("aurasql.recommendations.schema_snapshot_load", fake_trace, {"schema_table_count": 1}) in captured["span_calls"]
    assert ("aurasql.recommendations.parse", fake_trace, None) in captured["span_calls"]


def test_aurasql_query_sql_fallback_extracts_tables_and_forwards_trace(monkeypatch) -> None:
    from app.api.routes import aurasql as aurasql_module
    from app.models.aurasql_schemas import AuraSqlQueryRequest

    fake_trace = object()
    captured = {
        "request_name": None,
        "request_metadata": None,
        "span_calls": [],
        "async_call": None,
    }

    @contextmanager
    def _fake_trace_request(name, metadata=None, **kwargs):
        captured["request_name"] = name
        captured["request_metadata"] = metadata
        yield fake_trace

    @contextmanager
    def _fake_trace_span(name, trace=None, metadata=None, **kwargs):
        captured["span_calls"].append((name, trace, metadata))
        yield None

    async def _fake_trace_async_call(name, coro, metadata=None, trace=None):
        captured["async_call"] = (name, trace, metadata)
        return await coro

    class _FakeLlmService:
        def get_aurasql_llm(self):
            return None

    class _FakeQueryEngine:
        async def aquery(self, _prompt):
            return SimpleNamespace(response="```sql\nSELECT id FROM users LIMIT 5;\n```")

    class _FakeVectorStore:
        def get_query_engine(self, _vector_context_id):
            return _FakeQueryEngine()

    context = SimpleNamespace(
        id="ctx-1",
        connection_id="conn-1",
        user_id=1,
        table_names=["users"],
        schema_snapshot={"users": [{"column_name": "id"}]},
        vector_context_id="vector-ctx-1",
    )
    connection = SimpleNamespace(id="conn-1", db_type="postgresql")
    db = _FakeDb(context=context, connection=connection)

    monkeypatch.setattr(aurasql_module, "trace_request", _fake_trace_request)
    monkeypatch.setattr(aurasql_module, "trace_span", _fake_trace_span)
    monkeypatch.setattr(aurasql_module, "trace_async_call", _fake_trace_async_call)
    monkeypatch.setattr(aurasql_module, "get_llm_service", lambda: _FakeLlmService())
    monkeypatch.setattr(aurasql_module, "get_aurasql_vector_store", lambda: _FakeVectorStore())

    response = asyncio.run(
        aurasql_module.generate_query(
            payload=AuraSqlQueryRequest(
                context_id="ctx-1",
                query="List users",
            ),
            db=db,
            current_user=SimpleNamespace(id=1),
        )
    )

    assert response.sql.lower().startswith("select id from users")
    assert response.explanation == "Generated from model output."
    assert response.source_tables == []
    assert response.validation_errors == []
    assert db.commits == 1
    assert captured["request_name"] == "aurasql.query"
    assert captured["request_metadata"] == {
        "context_id": "ctx-1",
        "has_output_dialect": False,
        "query_length": 10,
    }
    assert captured["async_call"][0] == "aurasql.query.vector_aquery"
    assert captured["async_call"][1] is fake_trace
    assert captured["async_call"][2]["vector_context_id"] == "vector-ctx-1"
    assert captured["async_call"][2]["prompt_chars"] > 0
    assert ("aurasql.query.schema_snapshot_load", fake_trace, {"schema_table_count": 1}) in captured["span_calls"]
    assert ("aurasql.query.parse_validation_confidence", fake_trace, None) in captured["span_calls"]


def test_aurasql_execute_success_forwards_request_trace_to_execute_call(monkeypatch) -> None:
    from app.api.routes import aurasql as aurasql_module
    from app.models.aurasql_schemas import AuraSqlExecuteRequest

    fake_trace = object()
    captured = {
        "request_name": None,
        "request_metadata": None,
        "span_calls": [],
        "async_call": None,
    }

    @contextmanager
    def _fake_trace_request(name, metadata=None, **kwargs):
        captured["request_name"] = name
        captured["request_metadata"] = metadata
        yield fake_trace

    @contextmanager
    def _fake_trace_span(name, trace=None, metadata=None, **kwargs):
        captured["span_calls"].append((name, trace, metadata))
        yield None

    async def _fake_trace_async_call(name, coro, metadata=None, trace=None):
        captured["async_call"] = (name, trace, metadata)
        return await coro

    async def _fake_execute_sql(_config, _sql):
        return ["id"], [{"id": 1}]

    connection = SimpleNamespace(
        id="conn-1",
        user_id=1,
        db_type="postgresql",
        host="localhost",
        port=5432,
        username="db_user",
        database="demo",
        schema_name="public",
        ssl_required=True,
        secret=SimpleNamespace(encrypted_password="encrypted"),
    )
    db = _FakeDb(connection=connection)

    monkeypatch.setattr(aurasql_module, "trace_request", _fake_trace_request)
    monkeypatch.setattr(aurasql_module, "trace_span", _fake_trace_span)
    monkeypatch.setattr(aurasql_module, "trace_async_call", _fake_trace_async_call)
    monkeypatch.setattr(aurasql_module, "decrypt_secret", lambda _value: "clear-password")
    monkeypatch.setattr(aurasql_module, "execute_sql", _fake_execute_sql)

    response = asyncio.run(
        aurasql_module.execute_sql_query(
            payload=AuraSqlExecuteRequest(
                connection_id="conn-1",
                sql="SELECT id FROM users",
                session_id="session-1",
            ),
            db=db,
            current_user=SimpleNamespace(id=1),
        )
    )

    assert response.columns == ["id"]
    assert response.rows == [{"id": 1}]
    assert db.commits == 1
    assert captured["request_name"] == "aurasql.execute"
    assert captured["request_metadata"] == {
        "connection_id": "conn-1",
        "session_id": "session-1",
        "sql_length": 20,
    }
    assert captured["async_call"] == (
        "aurasql.execute.db_call",
        fake_trace,
        {"db_type": "postgresql"},
    )
    assert ("aurasql.execute.sql_execute", fake_trace, None) in captured["span_calls"]


def test_aurasql_execute_failure_still_uses_trace_and_returns_http_500(monkeypatch) -> None:
    from app.api.routes import aurasql as aurasql_module
    from app.models.aurasql_schemas import AuraSqlExecuteRequest

    fake_trace = object()
    captured = {
        "async_call": None,
    }

    @contextmanager
    def _fake_trace_request(name, metadata=None, **kwargs):
        yield fake_trace

    @contextmanager
    def _fake_trace_span(name, trace=None, metadata=None, **kwargs):
        yield None

    async def _fake_trace_async_call(name, coro, metadata=None, trace=None):
        captured["async_call"] = (name, trace, metadata)
        return await coro

    async def _failing_execute_sql(_config, _sql):
        raise RuntimeError("db unavailable")

    connection = SimpleNamespace(
        id="conn-1",
        user_id=1,
        db_type="postgresql",
        host="localhost",
        port=5432,
        username="db_user",
        database="demo",
        schema_name="public",
        ssl_required=True,
        secret=SimpleNamespace(encrypted_password="encrypted"),
    )
    db = _FakeDb(connection=connection)

    monkeypatch.setattr(aurasql_module, "trace_request", _fake_trace_request)
    monkeypatch.setattr(aurasql_module, "trace_span", _fake_trace_span)
    monkeypatch.setattr(aurasql_module, "trace_async_call", _fake_trace_async_call)
    monkeypatch.setattr(aurasql_module, "decrypt_secret", lambda _value: "clear-password")
    monkeypatch.setattr(aurasql_module, "execute_sql", _failing_execute_sql)

    with pytest.raises(HTTPException) as caught:
        asyncio.run(
            aurasql_module.execute_sql_query(
                payload=AuraSqlExecuteRequest(
                    connection_id="conn-1",
                    sql="SELECT id FROM users",
                    session_id="session-1",
                ),
                db=db,
                current_user=SimpleNamespace(id=1),
            )
        )

    assert caught.value.status_code == 500
    assert db.commits == 1
    assert len(db.added) == 1
    assert db.added[0].status == "failed"
    assert db.added[0].error_message == "db unavailable"
    assert captured["async_call"] == (
        "aurasql.execute.db_call",
        fake_trace,
        {"db_type": "postgresql"},
    )
