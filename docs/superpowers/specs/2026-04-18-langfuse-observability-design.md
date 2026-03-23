# Langfuse Observability Design for LlamaIndex Backend

Date: 2026-04-18
Status: Proposed (approved in chat, pending implementation plan)

## 1) Objective

Add Langfuse observability to the backend so we can trace end-to-end execution for all LlamaIndex-backed and adjacent AI flows, with:

- Full pipeline visibility (request trace + per-stage spans)
- Metadata-only capture (no raw prompt/response/chunk text)
- Self-hosted Langfuse support
- Production sampling (lower overhead), full capture in non-prod

## 2) Scope

In scope (v1):

- Chat flows (`/api/v1/chat/query`, `/api/v1/chat/stream`)
  - `fast` mode (`app/core/rag_engine.py`)
  - `think` mode (`app/core/pageindex_rag_engine.py`)
  - `ask` mode (direct LLM)
- AuraSQL flows (`/api/v1/aurasql/recommendations`, `/api/v1/aurasql/query`, `/api/v1/aurasql/execute`)
- Nexus Resume analyze flow (`/api/v1/nexus/resumes/analyze`)
- Shared LLM async call tracing (`acomplete`, `aquery`, stream paths)
- Retrieved chunk metadata capture for vector/BM25 stages
- Config surface in both `app/config.py` and `.env.example`

Out of scope (v1):

- Capturing full prompt/response/chunk text
- Historical backfill of traces for prior requests
- Distributed trace propagation to external services not called by this app runtime

## 3) Requirements and Decisions

- Scope: all major AI flows listed above
- Trace depth: full pipeline spans + stage metadata
- Privacy: metadata only
- Chunk visibility: metadata only (document_id/filename/page/chunk_id/score/rank)
- LLM async visibility: yes, all async call sites in scope are wrapped as spans
- Deployment: self-hosted Langfuse (`LANGFUSE_HOST` required)
- Sampling: 100% in dev/staging, sampled in prod (configurable)

## 4) Current Architecture Touchpoints

Primary locations:

- Chat routing and mode orchestration: `backend/app/api/routes/chat.py`
- Fast mode pipeline: `backend/app/core/rag_engine.py`
- Think mode pipeline: `backend/app/core/pageindex_rag_engine.py`
- Think mode LLM helper: `backend/app/core/pageindex_utils.py`
- AuraSQL route-level LLM/retrieval: `backend/app/api/routes/aurasql.py`
- AuraSQL query engine construction: `backend/app/services/aurasql_vector_store.py`
- Nexus analysis orchestration: `backend/app/services/nexus_resume_service.py`
- Provider/model selection: `backend/app/services/llm_service.py`
- App settings: `backend/app/config.py`

## 5) Proposed Observability Architecture

Create a dedicated module:

- `backend/app/observability/langfuse.py`

Responsibilities:

1. Initialize and cache a Langfuse client singleton.
2. Decide if a request should be traced based on environment + sample rates.
3. Provide helper wrappers to start/end traces and spans safely.
4. Enforce metadata-only payload policy through sanitization.
5. Fail open: observability failures must never block product logic.

### 5.1 API surface in `app/observability/langfuse.py`

Planned helpers (exact signatures can vary slightly in implementation):

- `get_langfuse_client()`
- `langfuse_enabled() -> bool`
- `should_sample_trace(env_name: str) -> bool`
- `start_trace(name: str, user_id: str | None, session_id: str | None, metadata: dict) -> TraceHandle | None`
- `start_span(trace_or_parent, name: str, metadata: dict) -> SpanHandle | None`
- `end_span_ok(span, output_meta: dict | None = None) -> None`
- `end_span_error(span, exc: Exception, metadata: dict | None = None) -> None`
- `update_trace(trace, metadata: dict | None = None, output_meta: dict | None = None) -> None`
- `close_trace(trace) -> None`
- `sanitize_metadata(data: dict) -> dict`

### 5.2 Fail-open behavior

If Langfuse is disabled, misconfigured, or unreachable:

- app behavior is unchanged
- helper methods no-op
- warning log emitted once per period to avoid log spam

## 6) Configuration Changes

Add to `backend/app/config.py`:

- `langfuse_enabled: bool = Field(default=False, alias="LANGFUSE_ENABLED")`
- `langfuse_host: str = Field(default="", alias="LANGFUSE_HOST")`
- `langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")`
- `langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")`
- `langfuse_env: str = Field(default="dev", alias="LANGFUSE_ENV")`
- `langfuse_sample_rate_dev: float = Field(default=1.0, alias="LANGFUSE_SAMPLE_RATE_DEV")`
- `langfuse_sample_rate_staging: float = Field(default=1.0, alias="LANGFUSE_SAMPLE_RATE_STAGING")`
- `langfuse_sample_rate_prod: float = Field(default=0.2, alias="LANGFUSE_SAMPLE_RATE_PROD")`

Add to `backend/.env.example`:

- `LANGFUSE_ENABLED=false`
- `LANGFUSE_HOST=`
- `LANGFUSE_PUBLIC_KEY=`
- `LANGFUSE_SECRET_KEY=`
- `LANGFUSE_ENV=dev`
- `LANGFUSE_SAMPLE_RATE_DEV=1.0`
- `LANGFUSE_SAMPLE_RATE_STAGING=1.0`
- `LANGFUSE_SAMPLE_RATE_PROD=0.2`

## 7) Sampling Strategy

- Sampling decision occurs once at request start.
- Child spans follow the same decision (no partial traces per request).
- Default behavior:
  - dev: 100%
  - staging: 100%
  - prod: 20%
- Rates are configurable through env vars.

## 8) Data Capture Policy (Metadata-Only)

Allowed metadata:

- request identifiers: `trace_id`, `session_id`, internal request ID
- user identifiers: `user_id` (existing app id)
- routing/mode: endpoint, mode, flow name
- model/provider: provider, model id, structured-model flag
- retrieval stats: retrieved counts, reranked counts, top-k, thresholds
- chunk metadata: `document_id`, `filename`, `page`, `chunk_id`, score, rank, retriever type
- latency metrics and token usage aggregates
- status flags: fallback used, compaction applied, validation failed
- confidence outputs: score/level

Disallowed in Langfuse payloads:

- raw prompts
- raw LLM responses
- raw chunk/document text
- SQL result rows
- resume raw extracted text
- credentials/secrets/API keys/passwords

## 9) Instrumentation Plan by Flow

### 9.1 Chat API (`backend/app/api/routes/chat.py`)

Root trace per request:

- `chat.query` for `/query`
- `chat.stream` for `/stream`

Top-level spans:

- `chat.resolve_mode`
- `chat.persist_user_message`
- `chat.route_fast` or `chat.route_think` or `chat.route_ask`
- `chat.diagram_extraction` (if requested)
- `chat.persist_assistant_message`

Include metadata: mode, session_id, user_id, context document count, processing time.

### 9.2 Fast mode (`backend/app/core/rag_engine.py`)

Spans:

- `fast.reformulate_query`
- `fast.retrieve.vector`
- `fast.retrieve.bm25`
- `fast.fuse_and_dedupe`
- `fast.rerank`
- `fast.prompt_build`
- `fast.llm.acomplete` (or `fast.llm.stream` for streaming)
- `fast.history_compaction` (if applied)
- `fast.confidence_score`
- `fast.fallback_history_only` (when retrieval empty)

Chunk metadata events:

- one event per top reranked node with `document_id`, `filename`, `page`, `chunk_id`, score, rank, retriever hint.

### 9.3 Think mode (`backend/app/core/pageindex_rag_engine.py`, `backend/app/core/pageindex_utils.py`)

Spans:

- `think.discover_documents`
- `think.tree_presence_check`
- `think.auto_generate_trees` (if triggered)
- `think.tree_search_llm` (per document)
- `think.node_select_and_context_build`
- `think.answer_llm`
- `think.history_fallback` (if no context sections)

Metadata includes selected node counts, source counts, confidence bands, and timing.

### 9.4 Ask mode (inside chat route)

Spans:

- `ask.prompt_build`
- `ask.llm.acomplete` or `ask.llm.stream`
- `ask.token_usage_extract`

### 9.5 AuraSQL (`backend/app/api/routes/aurasql.py`)

Root traces:

- `aurasql.recommendations`
- `aurasql.query`
- `aurasql.execute`

Key spans:

- `aurasql.schema_snapshot_load`
- `aurasql.vector_query.aquery`
- `aurasql.parse_response`
- `aurasql.sql_validation`
- `aurasql.confidence_calc`
- `aurasql.sql_execute`

Metadata includes context_id, connection_id (non-secret), table count, validation errors count, query status.

### 9.6 Nexus Resume (`backend/app/services/nexus_resume_service.py`)

Root trace:

- `nexus.resume.analyze`

Spans:

- `nexus.resume_load`
- `nexus.resume_text_source` (cache hit vs file extract)
- `nexus.analyzer_v2_call`
- `nexus.score_aggregation`
- `nexus.persist_analysis`

No raw resume/job-description text is sent; only metadata and scores.

## 10) Async LLM and Query Engine Visibility

Instrumentation wrappers cover async boundaries:

- `await llm.acomplete(...)`
- `await query_engine.aquery(...)`
- streaming generation via async iterator (`astream_complete` and token loop)

Each async stage gets start/end timestamps, status, and error metadata, enabling accurate latency diagnostics for awaited operations.

## 11) Error Handling and Reliability

- Every span wrapper catches exceptions and records sanitized error metadata (`error_type`, shortened message, stage name).
- Exception is re-raised to preserve existing business logic behavior.
- Langfuse client errors are swallowed (with warning log), never propagated to request handlers.

## 12) Testing and Verification Plan

Unit tests:

- sampling decision by env and rates
- metadata sanitizer strips forbidden fields
- wrappers behave as no-op when disabled/misconfigured

Integration/manual verification:

1. Run one request each for:
   - chat fast
   - chat think
   - chat ask
   - aurasql query
   - nexus analyze
2. Validate Langfuse UI shows:
   - root trace per request
   - expected child spans
   - chunk metadata events (no chunk text)
   - async LLM spans with timings
3. Force an LLM error path and verify trace records error metadata without app crash.

## 13) Rollout Plan

Phase 1:

- Add dependency and observability module
- Add config wiring in `config.py` and `.env.example`

Phase 2:

- Instrument chat and fast/think/ask paths

Phase 3:

- Instrument AuraSQL and Nexus analyze

Phase 4:

- Validate in staging (100% sampling), then enable production sampling

## 14) Risks and Mitigations

Risk: performance overhead from dense span creation.

- Mitigation: production sampling + concise metadata payloads.

Risk: accidental sensitive data leakage.

- Mitigation: centralized sanitizer + explicit denylist + no raw text policy.

Risk: trace gaps in mixed sync/async paths.

- Mitigation: route-level root traces + helper wrappers around all awaited LLM/query calls.

## 15) Acceptance Criteria

Implementation is accepted when:

1. Langfuse config exists in both `backend/app/config.py` and `backend/.env.example`.
2. All in-scope flows emit traces and stage spans when enabled.
3. Production sampling works per configured rates.
4. Retrieved chunk metadata is visible without chunk text.
5. Async LLM/query calls are visible with timing and status.
6. Disabling Langfuse leaves business behavior unchanged.
