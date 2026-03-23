import asyncio
from dataclasses import dataclass
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.rag_engine import _build_retrieval_chunk_metadata


@dataclass
class _FakeNode:
    metadata: dict

    def get_content(self) -> str:
        return "sensitive chunk text that must not be traced"


@dataclass
class _FakeNodeWithScore:
    node: _FakeNode
    score: float


def test_build_retrieval_chunk_metadata_excludes_chunk_text() -> None:
    nodes = [
        _FakeNodeWithScore(
            node=_FakeNode(
                metadata={
                    "document_id": "doc-1",
                    "filename": "guide.pdf",
                    "page": 3,
                    "chunk_id": "chunk-001",
                    "text": "this should never appear",
                    "content": "this should never appear either",
                }
            ),
            score=0.91,
        ),
        _FakeNodeWithScore(
            node=_FakeNode(
                metadata={
                    "document_id": "doc-2",
                    "filename": "notes.md",
                    "page": None,
                    "chunk_id": "chunk-002",
                }
            ),
            score=0.44,
        ),
    ]

    payload = _build_retrieval_chunk_metadata(nodes, retriever="vector")

    assert payload == [
        {
            "retriever": "vector",
            "rank": 1,
            "document_id": "doc-1",
            "filename": "guide.pdf",
            "page": 3,
            "chunk_id": "chunk-001",
            "score": 0.91,
        },
        {
            "retriever": "vector",
            "rank": 2,
            "document_id": "doc-2",
            "filename": "notes.md",
            "page": None,
            "chunk_id": "chunk-002",
            "score": 0.44,
        },
    ]

    serialized = str(payload)
    assert "sensitive chunk text" not in serialized
    assert "this should never appear" not in serialized


def test_rag_query_sets_official_trace_params(monkeypatch) -> None:
    from app.core import rag_engine as rag_module
    session_messages = []

    class _FakeNodePayload:
        def __init__(self, node_id: str, metadata: dict, content: str):
            self.node_id = node_id
            self.metadata = metadata
            self._content = content

        def get_content(self) -> str:
            return self._content

    class _FakeRetrieverNode:
        def __init__(self, node_id: str, score: float):
            self.score = score
            self.node = _FakeNodePayload(
                node_id=node_id,
                metadata={"filename": "guide.pdf", "page": 1, "chunk_id": f"chunk-{node_id}", "document_id": "doc-1"},
                content="retrieved content",
            )

    vector_nodes = [_FakeRetrieverNode("node-1", 0.9)]
    bm25_nodes = [_FakeRetrieverNode("node-2", 0.8)]

    class _FakeLLMResponse:
        def __init__(self):
            self.text = "CONFIDENCE: 80\nAnswer body"

    async def _fake_completion():
        return _FakeLLMResponse()

    class _FakeLLM:
        def acomplete(self, prompt):
            return _fake_completion()

    class _FakeLLMService:
        def get_llm(self):
            return _FakeLLM()

    monkeypatch.setattr(rag_module, "get_llm_service", lambda: _FakeLLMService())
    monkeypatch.setattr(rag_module, "get_reranker", lambda: SimpleNamespace(postprocess_nodes=lambda nodes, _qb: nodes))

    engine = rag_module.RAGEngine()

    class _FakeVectorStore:
        def retrieve(self, **kwargs):
            return vector_nodes

    class _FakeBm25:
        def search(self, **kwargs):
            return bm25_nodes

    class _FakeReranker:
        def postprocess_nodes(self, nodes, _query_bundle):
            return nodes

    class _FakeContextManager:
        def add_message(self, session_id, role, content, confidence_score=None):
            session_messages.append((session_id, role, content, confidence_score))

        def reformulate_query(self, _session_id, query):
            return query

        def get_context_string(self, _session_id, max_messages=8):
            return "history"

    captured = {}

    def _capture_trace_params(**kwargs):
        captured.update(kwargs)

    async def _fake_compact_history(history_str, query, context_str, threshold=0.85, trace=None):
        return history_str, False, {
            "context_tokens_used": 100,
            "context_tokens_max": 1000,
            "context_utilization_pct": 10.0,
            "near_limit": False,
            "compaction_applied": False,
        }

    fake_trace = object()

    monkeypatch.setattr("app.services.vector_store.get_vector_store_service", lambda: _FakeVectorStore())
    monkeypatch.setattr("app.services.bm25_service.get_bm25_service", lambda: _FakeBm25())
    monkeypatch.setattr(rag_module, "set_llamaindex_trace_params", _capture_trace_params)
    monkeypatch.setattr(engine, "reranker", _FakeReranker())
    monkeypatch.setattr(engine, "context_manager", _FakeContextManager())
    monkeypatch.setattr(engine, "_compact_history_if_needed", _fake_compact_history)

    class _FakeConfidenceScorer:
        def calculate_confidence(self, **kwargs):
            return {"confidence_score": 78.0, "confidence_level": "high", "breakdown": {}}

    monkeypatch.setattr(engine, "confidence_scorer", _FakeConfidenceScorer())

    result = asyncio.run(
        engine.query(
            query="what is this",
            session_id="session-1",
            use_context=True,
            user_id=1,
            context_document_ids=["doc-1"],
            trace=fake_trace,
        )
    )

    assert result["session_id"] == "session-1"
    assert result["answer"] == "Answer body"
    assert captured["name"] == "rag.fast.query"
    assert captured["session_id"] == "session-1"
    assert captured["user_id"] == "1"
    assert captured["metadata"] == {
        "use_context": True,
        "has_doc_filter": True,
        "doc_filter_count": 1,
    }


def test_compact_history_if_needed_compacts_using_structured_llm(monkeypatch) -> None:
    from app.core import rag_engine as rag_module
    fake_trace = object()

    class _FakeSummaryResponse:
        text = "- Keep this short summary"

    class _FakeStructuredLLM:
        def acomplete(self, _prompt):
            async def _complete():
                return _FakeSummaryResponse()

            return _complete()

    class _FakeLLMService:
        def get_llm(self):
            return _FakeStructuredLLM()

        def get_structured_llm(self):
            return _FakeStructuredLLM()

    monkeypatch.setattr(rag_module, "get_llm_service", lambda: _FakeLLMService())
    monkeypatch.setattr(rag_module, "get_reranker", lambda: SimpleNamespace(postprocess_nodes=lambda nodes, _qb: nodes))
    monkeypatch.setattr(rag_module.settings, "llm_context_window", 100)

    engine = rag_module.RAGEngine()

    compacted, compacted_applied, usage = asyncio.run(
        engine._compact_history_if_needed(
            history_str="history " * 200,
            query="What happened?",
            context_str="context " * 120,
            trace=fake_trace,
        )
    )

    assert compacted.startswith("- Keep this short summary")
    assert compacted_applied is True
    assert usage["compaction_applied"] is True


def test_iter_llm_tokens_falls_back_to_acomplete(monkeypatch) -> None:
    from app.core import rag_engine as rag_module
    fake_trace = object()

    class _FakeFallbackResponse:
        text = "fallback completion text"

    class _EmptyAsyncStream:
        def __aiter__(self):
            async def _iter():
                if False:
                    yield None

            return _iter()

    class _FakeLLM:
        def astream_complete(self, _prompt):
            return _EmptyAsyncStream()

        def acomplete(self, _prompt):
            async def _complete():
                return _FakeFallbackResponse()

            return _complete()

    class _FakeLLMService:
        def get_llm(self):
            return _FakeLLM()

    monkeypatch.setattr(rag_module, "get_llm_service", lambda: _FakeLLMService())
    monkeypatch.setattr(rag_module, "get_reranker", lambda: SimpleNamespace(postprocess_nodes=lambda nodes, _qb: nodes))

    engine = rag_module.RAGEngine()

    async def _collect_tokens():
        tokens = []
        async for token in engine._iter_llm_tokens("prompt", trace=fake_trace):
            tokens.append(token)
        return tokens

    tokens = asyncio.run(_collect_tokens())

    assert tokens == ["fallback completion text"]
