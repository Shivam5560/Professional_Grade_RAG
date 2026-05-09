# Data Analysis Agent — System Design Document

**Date:** 2026-05-09
**Status:** Draft (pending review)
**Author:** AI Architect

---

## 1. Goal

Build a **production-grade, multi-agent Data Analysis system** that ingests structured data (CSV, Excel, live DB) and unstructured data (documents), automatically profiles the data, decomposes analytical tasks, executes them in parallel via specialized sub-agents, synthesizes insights into a narrative, and generates polished, interactive reports with charts and optional slide decks.

The system must be implemented as a **separate FastAPI service** (`data_analysis/`) integrated with the existing NexusMind Studio infrastructure, leveraging **LlamaIndex framework capabilities** (Workflows, Agents, Tools, Embeddings) instead of manual orchestration code.

---

## 2. Architecture Overview

The design follows a **Workflow-Centric Orchestration** pattern (Approach B from brainstorming):

- A single **LlamaIndex Workflow** (`AnalysisWorkflow`) enforces the 5-layer architecture from `tasks.md` via typed, checkpointed steps.
- The Execution layer fans out into **parallel LlamaIndex Agent sub-workflows**.
- State is persisted to PostgreSQL for fault tolerance.
- Progress is streamed to the frontend via WebSocket.
- Charts and reports are generated using Plotly and assembled by a `SlideComposer`.

### High-Level Diagram

```
Frontend (Next.js)
  │ POST /api/v1/analysis
  │ WS   /api/v1/analysis/{id}/ws
  ▼
Data Analysis Backend (FastAPI + LlamaIndex)
  │
  ├── AnalysisWorkflow (LlamaIndex Workflow)
  │   ├── Step 1: TaskDecomposer
  │   ├── Step 2: ContextBuilder
  │   ├── Step 3: StrategyPlanner
  │   ├── Step 4: ExecutionDispatcher ──▶ 6 Parallel Sub-Workflows
  │   │                                      (Statistical, Pattern, etc.)
  │   ├── Step 5: InsightPrioritizer
  │   ├── Step 6: NarrativeGenerator
  │   ├── Step 7: DesignIntelligence
  │   └── Step 8: SlideComposer
  │
  ├── DataIngestionService
  ├── ChartGenerator (Plotly)
  └── ReportStore (PostgreSQL)
  │
  ▼
Shared Infrastructure
  ├── PostgreSQL (schema: data_analysis)
  ├── LlamaIndex Settings (LLM, Embeddings)
  ├── AuraSqlDB (live DB connections)
  └── Langfuse (observability)
```

---

## 3. Service Topology

### 3.1 New Service: `data_analysis/`

A standalone FastAPI application at the repository root:

```
data_analysis/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, Settings init
│   ├── api/
│   │   ├── deps.py              # Auth, DB session, current user
│   │   └── routes.py            # /analyze, /status, /result, /cancel, /ws
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (shared with backend)
│   │   ├── db.py                # Async SQLAlchemy engine + session
│   │   ├── models.py            # ORM: AnalysisJob, Report, ChartAsset
│   │   ├── events.py            # Workflow Event type definitions
│   │   └── state_store.py       # PostgreSQL-backed WorkflowStateStore
│   ├── workflows/
│   │   ├── analysis_workflow.py    # Main 8-step Workflow
│   │   └── execution_subworkflow.py # Reusable sub-workflow template
│   ├── agents/
│   │   ├── orchestrator_tools.py    # Tools exposed to top-level planner
│   │   ├── context_builder.py
│   │   ├── strategy_planner.py
│   │   ├── execution/
│   │   │   ├── statistical.py
│   │   │   ├── pattern.py
│   │   │   ├── correlation.py
│   │   │   ├── predictive.py
│   │   │   ├── nlp_text.py
│   │   │   └── time_series.py
│   │   ├── insight_prioritizer.py
│   │   ├── narrative_generator.py
│   │   ├── design_intelligence.py
│   │   └── slide_composer.py
│   ├── services/
│   │   ├── data_ingestion.py
│   │   ├── data_profiler.py
│   │   ├── chart_generator.py
│   │   └── report_store.py
│   └── utils/
│       └── sampling.py          # Stratified sampling for large datasets
├── tests/
├── Dockerfile
├── requirements.txt
└── README.md
```

### 3.2 Shared Infrastructure

- **PostgreSQL:** Uses the **existing** PostgreSQL instance (single infrastructure). All analysis tables live in a dedicated schema `data_analysis` with standard table names: `analysis_jobs`, `reports`, `chart_assets`, `workflow_states`. **Multi-tenancy is enforced via a `user_id` column on every table** — there are no per-user tables, schemas, or dynamically named tables. Queries are filtered by `user_id` at the application layer.
- **LlamaIndex Settings:** Reuses the existing `rag_provider_factory.py` pattern. The `data_analysis` service imports the shared config module to set `Settings.llm` and `Settings.embed_model`.
- **Langfuse:** Workflow steps emit Langfuse spans automatically via the global callback handler.
- **AuraSqlDB:** Live DB connections are delegated to the existing main backend via an internal API call (or direct service import if colocated).

### 3.3 Deployment Modes

- **Default:** Standalone container/service (`docker-compose` adds `data_analysis` service).
- **Simplified:** Mounted as a sub-router under the main backend (`/analysis/*`) for single-service deployments. This is controlled by an env var `DATA_ANALYSIS_MOUNTED=true`.

---

## 4. The 5-Layer Workflow Design

The core of the system is `AnalysisWorkflow`, a LlamaIndex `Workflow` subclass.

### 4.1 Event Types

All communication between steps is typed via Pydantic-based `Event` subclasses:

```python
from llama_index.core.workflow import Event, StartEvent, StopEvent
from typing import List

class AnalysisTask(Event):
    task_id: str
    description: str
    required_agents: List[str]

class TaskDecomposedEvent(Event):
    tasks: List[AnalysisTask]

class ContextBuiltEvent(Event):
    dataset_ref: str
    profile_json: dict
    embedding_nodes: List[dict]

class AgentInvocation(Event):
    agent_name: str
    task_id: str
    parameters: dict

class StrategyPlannedEvent(Event):
    invocations: List[AgentInvocation]

class AgentResult(Event):
    agent_name: str
    task_id: str
    findings: List[dict]
    confidence: float

class ExecutionCompleteEvent(Event):
    results: List[AgentResult]

class Insight(Event):
    insight_id: str
    content: str
    significance_score: float
    source_agents: List[str]

class InsightsPrioritizedEvent(Event):
    insights: List[Insight]

class NarrativeGeneratedEvent(Event):
    executive_summary: str
    sections: List[dict]  # markdown blocks

class DesignSpec(Event):
    theme: str
    color_palette: List[str]
    layout: str
    chart_specs: List[dict]

class AnalysisCompleteEvent(Event):
    report_id: str
    narrative: str
    chart_urls: List[str]
    slide_deck_url: str | None
```

### 4.2 Workflow Steps

```python
from llama_index.core.workflow import Workflow, step

class AnalysisWorkflow(Workflow):
    @step
    async def decompose(self, ev: StartEvent) -> TaskDecomposedEvent:
        # ...

    @step
    async def build_context(self, ev: TaskDecomposedEvent) -> ContextBuiltEvent:
        # ...

    @step
    async def plan_strategy(self, ev: ContextBuiltEvent) -> StrategyPlannedEvent:
        # ...

    @step
    async def dispatch_execution(self, ev: StrategyPlannedEvent) -> ExecutionCompleteEvent:
        # Spawns parallel sub-workflows via asyncio.gather
        # ...

    @step
    async def prioritize_insights(self, ev: ExecutionCompleteEvent) -> InsightsPrioritizedEvent:
        # ...

    @step
    async def generate_narrative(self, ev: InsightsPrioritizedEvent) -> NarrativeGeneratedEvent:
        # ...

    @step
    async def design(self, ev: NarrativeGeneratedEvent) -> DesignSpec:
        # ...

    @step
    async def compose(self, ev: DesignSpec) -> StopEvent:
        # ...
```

---

## 5. Agent Specifications

Each agent is a **LlamaIndex `FunctionCallingAgent`** configured with a system prompt and a curated set of `FunctionTool` instances. Agents do not use manual `if/else` logic; they reason about which tools to call.

### 5.1 Task Decomposition Agent

- **Role:** Breaks the user's natural language request into discrete, executable analytical tasks.
- **Type:** `FunctionCallingAgent`
- **Tools:** None (pure reasoning).
- **Input:** User query string + dataset profile summary.
- **Output:** `List[AnalysisTask]`.
- **System Prompt:** "You are an expert data analyst. Given a user question and a dataset profile, break the request into 1-5 specific analytical sub-tasks. Each task must specify which analysis domains are relevant: statistical, pattern, correlation, predictive, nlp, time_series."

### 5.2 Context Builder Agent

- **Role:** Ingests raw data, profiles it, and builds semantic context for downstream agents.
- **Type:** `FunctionCallingAgent`
- **Tools:**
  - `load_dataset(source_type, source_id) -> DataFrame` (calls `DataIngestionService`)
  - `profile_dataframe(df) -> dict` (calls `DataProfiler`)
  - `embed_schema(columns, samples) -> List[TextNode]` (calls embedding model)
- **Input:** `TaskDecomposedEvent`
- **Output:** `ContextBuiltEvent`

### 5.3 Strategy Planner Agent

- **Role:** Maps tasks to the optimal execution agents and determines invocation order/dependencies.
- **Type:** `FunctionCallingAgent`
- **Tools:**
  - `get_available_agents() -> List[str]`
  - `select_agents_for_task(task_description, profile) -> List[str]`
- **Input:** `ContextBuiltEvent`
- **Output:** `StrategyPlannedEvent`

### 5.4 Statistical Analysis Agent

- **Role:** Runs descriptive and inferential statistics.
- **Type:** `FunctionCallingAgent` (runs inside `ExecutionSubWorkflow`)
- **Tools:**
  - `describe(df) -> dict`
  - `ttest(group_a, group_b) -> dict`
  - `anova(df, target, factors) -> dict`
  - `chi2(df, col1, col2) -> dict`
  - `mann_whitney(group_a, group_b) -> dict`
- **Library Backend:** `scipy.stats`, `statsmodels`, `pandas`.
- **Output:** `AgentResult` with findings + p-values.

### 5.5 Pattern Detection Agent

- **Role:** Identifies trends, seasonality, clusters, and anomalies.
- **Type:** `FunctionCallingAgent`
- **Tools:**
  - `detect_trend(series) -> dict`
  - `detect_seasonality(series) -> dict`
  - `detect_anomalies(df, method="isolation_forest") -> dict`
  - `cluster_features(df, n_clusters) -> dict`
- **Library Backend:** `sklearn`, `statsmodels`.

### 5.6 Correlation Agent

- **Role:** Measures relationships between variables using multiple metrics.
- **Type:** `FunctionCallingAgent`
- **Tools:**
  - `pearson_corr(df, cols) -> dict`
  - `spearman_corr(df, cols) -> dict`
  - `mutual_information(df, cols) -> dict`
  - `cramers_v(df, col1, col2) -> dict`
- **Library Backend:** `scipy`, `sklearn`.

### 5.7 Predictive Analysis Agent

- **Role:** Builds lightweight predictive models and extracts feature importance.
- **Type:** `FunctionCallingAgent`
- **Tools:**
  - `linear_regression(X, y) -> dict`
  - `logistic_regression(X, y) -> dict`
  - `feature_importance(model) -> dict`
- **Library Backend:** `sklearn`, `shap` (for interpretability).
- **Constraint:** Models are trained on sampled data and are ephemeral (not persisted). Only results + charts are stored.

### 5.8 NLP / Text Analysis Agent

- **Role:** Analyzes unstructured or semi-structured text columns.
- **Type:** `FunctionCallingAgent`
- **Tools:**
  - `sentiment_analysis(text_series) -> dict`
  - `topic_modeling(text_series, n_topics) -> dict`
  - `entity_extraction(text_series) -> dict`
- **Library Backend:** `transformers` (pipeline), `spacy`.

### 5.9 Time Series Agent

- **Role:** Decomposes time series and generates forecasts.
- **Type:** `FunctionCallingAgent`
- **Tools:**
  - `decompose_series(series, model="additive") -> dict`
  - `forecast_prophet(df, date_col, target_col, periods) -> dict`
  - `forecast_arima(series, order) -> dict`
- **Library Backend:** `statsmodels`, `prophet`, `pandas`.

### 5.10 Insight Prioritization Agent

- **Role:** Ranks, deduplicates, and resolves contradictions across all execution agent results.
- **Type:** `FunctionCallingAgent`
- **Tools:** None (pure reasoning over structured findings).
- **Input:** `ExecutionCompleteEvent`
- **Output:** `InsightsPrioritizedEvent`
- **Logic:** LLM receives a JSON of all findings with confidence scores and returns a ranked list with a `significance_score` (0-1).

### 5.11 Narrative Generation Agent

- **Role:** Converts prioritized insights into executive summaries and contextual explanations.
- **Type:** `FunctionCallingAgent`
- **Tools:** None.
- **Input:** `InsightsPrioritizedEvent`
- **Output:** `NarrativeGeneratedEvent`
- **System Prompt:** "You are a senior data storyteller. Write an executive summary and detailed sections in Markdown. Each insight must have a 'So What?' and an actionable recommendation."

### 5.12 Design Intelligence Agent

- **Role:** Selects visual layout, color palette, and chart types based on data domain and narrative.
- **Type:** `FunctionCallingAgent`
- **Tools:**
  - `get_domain_palette(domain) -> List[str]` (maps domain to color hexes)
  - `select_chart_type(insight_type, data_shape) -> str`
- **Input:** `NarrativeGeneratedEvent`
- **Output:** `DesignSpec`
- **Domain Palettes:**
  - Finance: `['#1f4e79', '#2e75b5', '#70ad47', '#ffc000']`
  - Healthcare: `['#5b9bd5', '#a5d6a7', '#ffcc80', '#ef9a9a']`
  - Sales: `['#c55a11', '#ed7d31', '#4472c4', '#70ad47']`
  - Generic: `['#4f81bd', '#9cbb58', '#f79646', '#8064a2']`

### 5.13 Slide Composer Agent

- **Role:** Generates Plotly charts and assembles the final report structure.
- **Type:** `FunctionCallingAgent`
- **Tools:**
  - `generate_plotly_chart(spec, df) -> str` (returns chart JSON or image path)
  - `generate_slide_deck(report_sections, charts) -> str` (returns PPTX path)
  - `apply_brand_kit(report, colors, fonts) -> dict`
- **Input:** `DesignSpec`
- **Output:** `AnalysisCompleteEvent`
- **Library Backend:** `plotly`, `python-pptx`, `jinja2`.

---

## 6. Data Ingestion & Profiling

### 6.1 Source Types

| Source | Handler | Notes |
|--------|---------|-------|
| CSV | `pandas.read_csv` | UTF-8 inferred. Chunked for >500MB. |
| Excel | `pandas.read_excel` | Supports `.xlsx`, `.xls`. Multi-sheet merged. |
| Live DB | AuraSqlDB query | User provides SQL. Results streamed to DataFrame. |
| Document tables | `camelot` / `tabula-py` | Extracts tables from PDFs. |

### 6.2 Profiling

- **Automatic:** `DataProfiler` runs `df.info()`, `df.describe()`, null analysis, cardinality checks, and correlation matrix.
- **Semantic Context:** Column names + top 10 sample values per column are embedded using the shared embedding model. This enables the Strategy Planner to match vague user queries ("revenue") to actual columns ("sales_amount").
- **Sampling:** Datasets >100k rows use stratified sampling (10% or max 50k rows) for agent reasoning. Full data is used for final chart rendering.

---

## 7. Execution Layer: Parallel Sub-Workflows

The `dispatch_execution` step is the performance-critical fan-out point.

```python
@step
async def dispatch_execution(self, ev: StrategyPlannedEvent) -> ExecutionCompleteEvent:
    sub_workflows = []
    for inv in ev.invocations:
        agent_cls = AGENT_REGISTRY[inv.agent_name]
        sub = ExecutionSubWorkflow(agent_cls, inv.parameters, timeout=300)
        sub_workflows.append(sub.run())

    results = await asyncio.gather(*sub_workflows, return_exceptions=True)
    # Failed sub-workflows are logged but do not crash the parent workflow.
    # Partial results are collected.
    return ExecutionCompleteEvent(results=[r for r in results if not isinstance(r, Exception)])
```

The `AGENT_REGISTRY` is a module-level dictionary mapping agent names (e.g., `"statistical"`) to their `FunctionCallingAgent` factory functions. It is defined in `app/agents/execution/__init__.py`.

- **Timeout:** Each sub-workflow has a hard timeout of 300 seconds.
- **Isolation:** Sub-workflows run in the same process but operate on read-only DataFrame copies.
- **Failure Model:** `return_exceptions=True` ensures partial success. The `InsightPrioritizer` notes missing agents in the narrative.
- **Concurrency Limit:** An `asyncio.Semaphore(6)` limits concurrent LLM + compute calls to prevent overwhelming the LLM provider.

---

## 8. Presentation Layer

### 8.1 Chart Generation

- **Engine:** Plotly (interactive JSON for frontend, static PNG for slide decks).
- **Process:** The `SlideComposer` iterates over `design_spec.chart_specs` and calls `ChartGenerator.create_chart(spec, df)`.
- **Storage:** Chart assets are saved to `data/analysis_charts/{job_id}/` and served via `/api/v1/analysis/{job_id}/charts/{filename}`.

### 8.2 Report Formats

| Format | Description |
|--------|-------------|
| Interactive Web Report | JSON structure consumed by the frontend. Contains narrative Markdown + Plotly chart JSON. |
| PPTX Slide Deck | Generated via `python-pptx` with Jinja2 templates. One slide per major insight. |
| PDF Export | (Future) Convert interactive report to PDF via `weasyprint` or `playwright`. |

### 8.3 Frontend Rendering

- The frontend `/analysis` page polls `GET /analysis/{id}` for state transitions.
- On completion, it renders the narrative in a scrollable viewer and Plotly charts in an interactive grid.
- Slide deck is downloadable via `GET /analysis/{id}/slides`.

---

## 9. Frontend Integration

### 9.1 New Route & Navigation

- **Path:** `/analysis` in the Next.js frontend.
- **Navigation:** Added to the main sidebar/navbar as "Data Analysis" with a `BarChart3` icon (from `lucide-react`).
- **Route Guard:** Requires authentication (reuses existing `AuthGuard` HOC).

### 9.2 Screen Designs

#### Screen 1: Analysis Hub (`/analysis`)

**Layout:** Full-width page with a centered max-width container (`max-w-5xl`).

**Components:**
- **Header:** Title "Data Analysis" + subtitle "Upload data, ask questions, get insights."
- **Source Selector Tabs:** Three tabs — "Upload File", "Live Database", "Existing Document".
    - **Upload File:** Drag-and-drop zone (uses `react-dropzone`) accepting `.csv`, `.xlsx`, `.xls`. Shows file name, row count preview, and a "Remove" button after upload. Max file size: 100MB.
    - **Live Database:** Dropdown selector populated from `GET /api/v1/aurasql/connections`. After selection, shows a SQL input field ( Monaco editor or plain textarea) with a "Test Query" button that previews the first 10 rows.
    - **Existing Document:** (Future) Lists user documents that contain extractable tables.
- **Query Input:** Large textarea with placeholder "e.g., What are the key trends in revenue and which factors drive customer churn?" Min height `120px`. Character counter (max 500).
- **Configuration Accordion:** Collapsible section with:
    - Toggle: "Include predictive modeling" (default: on)
    - Toggle: "Generate slide deck" (default: on)
    - Slider: "Max rows for analysis" (10k - 100k, default 50k)
- **Submit Button:** Full-width primary button "Start Analysis". Disabled until source + query are provided. Shows spinner during submission.

**State Flow:** On submit, calls `POST /api/v1/analysis`, receives `job_id`, and navigates to `/analysis/{job_id}`.

#### Screen 2: Analysis Progress (`/analysis/[jobId]`)

**Layout:** Split view — left sidebar (progress), right main area (live preview).

**Left Sidebar (Progress Panel):**
- **Job Status Badge:** "Queued" | "Running" | "Completed" | "Failed" (color-coded: yellow, blue, green, red).
- **Progress Steps:** Vertical stepper showing the 8 workflow steps:
    1. Decomposing Task
    2. Building Context
    3. Planning Strategy
    4. Running Analysis (shows sub-agent names as they start: "Statistical Agent running...")
    5. Prioritizing Insights
    6. Generating Narrative
    7. Designing Visuals
    8. Composing Report
- **Current Step:** Highlighted with a pulsing dot.
- **Elapsed Time:** Timer since job start.
- **Cancel Button:** "Cancel Analysis" (red outline). Calls `POST /api/v1/analysis/{job_id}/cancel`.

**Right Main Area (Live Preview):**
- **WebSocket Feed:** Raw event stream from `WS /api/v1/analysis/{job_id}/ws` displayed as a scrollable, collapsible JSON log (developer mode toggle).
- **Partial Results:** As agents complete, their findings appear here in real-time (e.g., "Statistical Agent found: revenue correlates with marketing spend (r=0.82)").

**Empty State:** Before any events, shows an animated illustration (Lottie or Framer Motion) with text "Starting your analysis..."

**Error State:** If job fails, shows error message + "View Logs" button + "Try Again" button (redirects back to `/analysis` with pre-filled form).

#### Screen 3: Report Viewer (`/analysis/[jobId]/report` — auto-redirected on completion)

**Layout:** Full-width with a sticky top toolbar.

**Sticky Toolbar:**
- **Back Button:** "← All Analyses" (navigates to `/analysis/history`).
- **Report Title:** Editable inline (default: "Analysis Report — {timestamp}").
- **Action Buttons:**
    - "Download PPTX" (primary outline) — `GET /api/v1/analysis/{job_id}/slides`
    - "Share" (copies link to clipboard)
    - "Re-run" (restarts with same source + query)

**Report Body (Scrollable):**
- **Executive Summary Card:** Top section with white background, rounded corners, shadow. Contains the generated narrative summary in Markdown (rendered via `react-markdown`).
- **Insights Grid:** Responsive grid (`grid-cols-1 md:grid-cols-2`) of insight cards.
    - **Insight Card:**
        - Header: Insight title + significance score badge (0-1, color: green if >0.8, yellow if 0.5-0.8, gray if <0.5).
        - Body: Insight description in Markdown.
        - Chart Area: If the insight has an associated chart, renders the Plotly chart JSON using `react-plotly.js` in a responsive container.
        - Footer: "Source: {agent_name}" tag.
- **Detailed Sections:** Accordions for each analysis domain (Statistical, Patterns, Correlations, etc.). Each contains findings + charts.

**Empty / Loading State:** Skeleton loaders for cards and charts while data is being fetched.

#### Screen 4: Analysis History (`/analysis/history`)

**Layout:** Full-width table/list view.

**Components:**
- **Header:** "Analysis History" + "New Analysis" button (redirects to `/analysis`).
- **Table:** Columns: Job ID (truncated), Query (truncated, tooltip on hover), Source Type, Status, Created At, Actions.
- **Actions:** "View Report" (link to `/analysis/[jobId]/report`), "Delete" (with confirmation modal).
- **Pagination:** Server-side pagination via `GET /api/v1/analysis?page={n}`.
- **Filters:** Status filter (dropdown), date range picker.

### 9.3 Component Library

All UI components reuse the existing shadcn/ui primitives:
- `Button`, `Card`, `Badge`, `Tabs`, `Accordion`, `Slider`, `Skeleton`, `Tooltip`, `Dialog`, `DropdownMenu`, `Table`, `Textarea`.
- **New Components (to build):**
    - `AnalysisStepper`: Custom vertical stepper for workflow progress.
    - `InsightCard`: Card with integrated Plotly chart container.
    - `FileDropzone`: Wrapper around `react-dropzone` with styling.
    - `SqlQueryEditor`: Monaco Editor instance for SQL input.
    - `PlotlyChart`: Wrapper around `react-plotly.js` with theme-aware colors.

### 9.4 State Management

- **Zustand Store:** `useAnalysisStore`
    - `activeJobId: string | null`
    - `jobStatus: 'idle' | 'queued' | 'running' | 'completed' | 'failed'`
    - `progressEvents: WorkflowEvent[]` (append-only stream from WebSocket)
    - `reportData: Report | null`
    - `actions: { startAnalysis, cancelAnalysis, setReportData, appendEvent }`
- **React Query:** Uses `@tanstack/react-query` for:
    - Fetching analysis history (`GET /api/v1/analysis`)
    - Fetching report data (`GET /api/v1/analysis/{job_id}/report`)
    - Polling job status as fallback when WebSocket is unavailable.

### 9.5 WebSocket Integration

- **Hook:** `useAnalysisSocket(jobId: string)`
- **Behavior:**
    - Connects to `WS /api/v1/analysis/{job_id}/ws` on mount.
    - On message: parses JSON event, appends to `progressEvents` in Zustand.
    - On `AnalysisCompleteEvent`: transitions status to "completed", fetches full report via REST, navigates to `/analysis/{job_id}/report`.
    - On `WorkflowErrorEvent`: transitions status to "failed", logs error.
    - Auto-reconnect with exponential backoff (max 5 attempts).
    - Disconnects on unmount.

### 9.6 Responsive Design

- **Desktop (>1024px):** Split view for progress page, 2-column insight grid.
- **Tablet (768-1024px):** Single column insight grid, progress sidebar becomes collapsible drawer.
- **Mobile (<768px):** Full-width stacked layout, progress steps shown as horizontal stepper, charts scroll horizontally if needed.

---

## 10. API Specification

### 10.1 Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/analysis` | JWT | Start analysis job. Body: `{source_type, source_id, query, config?}`. Response: `{job_id}` |
| GET | `/api/v1/analysis/{job_id}` | JWT | Get job status + partial results. |
| WS | `/api/v1/analysis/{job_id}/ws` | JWT | Stream progress events. |
| POST | `/api/v1/analysis/{job_id}/cancel` | JWT | Cancel running job. |
| GET | `/api/v1/analysis/{job_id}/report` | JWT | Fetch final report JSON. |
| GET | `/api/v1/analysis/{job_id}/slides` | JWT | Download PPTX. |
| GET | `/api/v1/analysis/{job_id}/charts/{file}` | JWT | Serve chart image/JSON. |

### 10.2 Request / Response Example

**POST /api/v1/analysis**
```json
{
  "source_type": "csv",
  "source_id": "uploads/sales_2025.csv",
  "query": "What are the key trends in revenue and which factors drive customer churn?",
  "config": {
    "max_rows": 50000,
    "include_predictive": true,
    "output_format": ["interactive", "pptx"]
  }
}
```

**Response:**
```json
{
  "job_id": "da-uuid-1234",
  "status": "queued",
  "created_at": "2026-05-09T10:00:00Z"
}
```

---

## 11. Integration with Existing Infrastructure

### 11.1 LlamaIndex Settings

The `data_analysis` service imports the shared configuration module (extracted from the main backend) to initialize:

```python
from llama_index.core import Settings
from shared.config import get_llm, get_embed_model

Settings.llm = get_llm()
Settings.embed_model = get_embed_model()
```

### 11.2 PostgreSQL

- Uses the same DB host/credentials.
- Schema `data_analysis` is created via Alembic migration (shared migration folder or separate).

### 11.3 AuraSqlDB

- For live DB sources, the analysis backend calls the main backend's internal endpoint `GET /internal/aurasql/{connection_id}/query` or imports the `AuraSqlDB` service directly if colocated.

### 11.4 Auth

- Reuses the same JWT secret and `deps.py` dependency (`get_current_user`).
- All analysis jobs are scoped to `user_id`.

---

## 12. Error Handling, Retries & Timeouts

### 12.1 Workflow-Level

- **Checkpointing:** Every step emits an event that is serialized to PostgreSQL by `PostgresWorkflowCheckpointStore`. On restart, `Workflow.run()` resumes from the last checkpoint.
- **Timeouts:** Parent workflow timeout: 15 minutes. Sub-workflow timeout: 5 minutes.
- **Retries:** LLM calls use LlamaIndex's built-in retry with exponential backoff (3 attempts). Analysis tool calls (scipy, sklearn) retry once on transient errors.

### 12.2 Agent-Level

- If an agent produces malformed JSON, a `RecoveryStep` re-prompts the LLM with the schema and previous error.
- If an agent tool fails (e.g., OOM on large matrix), it returns a structured error object instead of crashing.

### 12.3 Graceful Degradation

- If `PredictiveAnalysisAgent` fails, the report still contains results from the other 5 agents, with a note: "Predictive modeling was unavailable for this dataset."
- If PPTX generation fails, the interactive report is still delivered.

---

## 13. Observability

### 13.1 Langfuse

- All workflow steps emit Langfuse spans via the global LlamaIndex callback handler.
- Each agent invocation is a child span.
- Tags: `agent_name`, `job_id`, `user_id`, `source_type`.

### 13.2 Logging

- Structured JSON logging via `structlog`.
- Each log line includes `job_id`, `step_name`, `agent_name`, `duration_ms`.

### 13.3 Metrics

- Prometheus metrics endpoint `/metrics`.
- Counters: `analysis_jobs_started`, `analysis_jobs_completed`, `analysis_jobs_failed`.
- Histograms: `workflow_duration_seconds`, `agent_execution_duration_seconds`.

---

## 14. State Persistence & Recovery

### 14.1 WorkflowStateStore

Implements a custom checkpoint store that serializes the LlamaIndex Workflow `Context` dictionary to PostgreSQL after every step completion:

```python
class PostgresWorkflowCheckpointStore:
    """Serializes workflow context to PostgreSQL for fault-tolerant recovery."""

    async def save_checkpoint(self, workflow_id: str, context_dict: dict) -> None:
        """UPSERT into analysis_workflow_states."""

    async def load_checkpoint(self, workflow_id: str) -> dict | None:
        """SELECT latest checkpoint from analysis_workflow_states."""

    async def delete_checkpoint(self, workflow_id: str) -> None:
        """Clean up after workflow completion."""
```

This store is injected into the `AnalysisWorkflow` constructor and called at the end of each `@step` via a decorator wrapper.

### 14.2 Job Lifecycle

1. **Queued:** Job record created. Workflow not yet started.
2. **Running:** Workflow started, checkpoints active.
3. **Paused:** (If cancel requested mid-step, waits for current step to finish then stops.)
4. **Completed:** Final report persisted.
5. **Failed:** Error logged, partial results available.

---

## 15. Security & Multi-Tenancy

- **User Isolation:** All queries to `analysis_jobs` and `reports` are filtered by `user_id`.
- **File Access:** Uploaded files are stored in `data/analysis_uploads/{user_id}/` to prevent cross-user access.
- **SQL Injection:** Live DB queries are parameterized. Only `SELECT` statements are allowed (enforced by `sqlparse` AST check).
- **Sandboxing:** Agent code execution (scipy, sklearn) runs in the same process. No arbitrary code execution is permitted. Tools are hardcoded wrappers.

---

## 16. Testing Strategy

### 16.1 Unit Tests

- **Agent Tool Tests:** Each tool function (e.g., `ttest`, `detect_anomalies`) tested against synthetic datasets.
- **Event Serialization:** All custom `Event` subclasses round-trip through JSON correctly.

### 16.2 Integration Tests

- **End-to-End Workflow:** A full workflow run on a fixture CSV (e.g., Titanic dataset) asserting that all 8 steps complete and the final report contains expected charts.
- **Failure Injection:** Tests that sub-workflow failures are handled gracefully.

### 16.3 Frontend Tests

- **Component Tests:** Upload form, progress bar, report viewer.
- **E2E Tests:** User uploads CSV, types query, waits for report, downloads PPTX.

---

## 17. Deployment

### 17.1 Docker

```dockerfile
# data_analysis/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 17.2 docker-compose

Add `data_analysis` service to existing `docker-compose.yml`:

```yaml
services:
  data_analysis:
    build: ./data_analysis
    ports:
      - "8001:8001"
    env_file:
      - .env
    depends_on:
      - postgres
    volumes:
      - ./data:/app/data
```

### 17.3 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_ANALYSIS_PORT` | `8001` | Service port |
| `DATA_ANALYSIS_MOUNTED` | `false` | If `true`, mounts as sub-router in main backend |
| `ANALYSIS_MAX_ROWS` | `50000` | Max rows for agent reasoning |
| `ANALYSIS_SUBWORKFLOW_TIMEOUT` | `300` | Sub-workflow timeout (seconds) |
| `ANALYSIS_WORKFLOW_TIMEOUT` | `900` | Parent workflow timeout (seconds) |

---

## 18. Future Considerations

- **Real-time Analysis:** WebSocket streaming of sub-agent progress (currently only workflow-level progress is streamed).
- **Custom Agent Plugins:** Allow users to register custom Python analysis functions as tools.
- **Collaborative Reports:** Share report URLs between users with role-based access.
- **Advanced Visualizations:** Add support for `altair`, `seaborn`, and 3D charts.
- **Caching:** Cache DataFrame profiles and embedding nodes to speed up re-analysis of the same dataset.

---

**End of Document**
