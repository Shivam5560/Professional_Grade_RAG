# NexusMind Modular AI Platform Design

## Purpose

NexusMind is a framework-first AI application showcase and solution accelerator. It demonstrates multiple production-grade applications built on one reusable platform, while allowing a requested solution to be shipped as:

`Nexus Core + selected applications + selected infrastructure adapters`

NexusMind is not a single tightly integrated SaaS product. Each application is a complete reference product that can run inside the showcase, be tested independently, and be packaged independently without copying unrelated application code.

## Product Principles

1. **Measured accuracy over unsupported guarantees.** No probabilistic AI system can guarantee perfect answers. NexusMind must instead maximize task accuracy, expose evidence, abstain when evidence is insufficient, and block releases when evaluation scores regress.
2. **Algorithms before prompts.** Deterministic parsing, validation, ranking, optimization, constraint solving, and statistical methods own tasks they can solve reliably. LLMs handle language understanding, synthesis, planning, and recovery within explicit contracts.
3. **Framework before application coupling.** Applications consume stable platform interfaces. They do not import another application's internal services or database models.
4. **Frontend is part of the framework.** Every platform capability includes reusable frontend contracts, states, error handling, accessibility, observability, and tests.
5. **Evidence is a first-class object.** Generated claims, SQL, recommendations, resume bullets, and presentation statements link to their source evidence whenever the task permits it.
6. **Quality is enforced continuously.** Unit, contract, integration, end-to-end, visual, security, performance, and AI evaluation suites are release gates.
7. **Clean delivery boundaries.** A selected application can be packaged with Nexus Core using a manifest instead of manual source deletion.
8. **Graceful degradation.** Provider, connector, reranker, rendering, and optional application failures do not crash unrelated capabilities.

## Scope

### Shared platform

- Application manifests, capability registry, and dependency validation
- Authentication, users, workspaces, permissions, and audit events
- Model gateway, prompt registry, structured-output validation, and cost policy
- Durable workflow execution, checkpoints, approval, retry, cancellation, and notifications
- Connector, ingestion, storage, retrieval, provenance, and evidence services
- Artifact versioning, sharing, review, and export
- Evaluation datasets, metrics, experiments, release gates, and production feedback
- Application catalog, demo scenarios, platform navigation, job center, evidence inspection, and quality reporting
- MCP, REST, and SDK access to approved platform capabilities
- Packaging profiles and deployment generation

### Flagship reference applications

- Knowledge Studio
- AuraSQL
- Data Analyst Studio
- Presentation Studio
- Career Studio
- Developer and MCP Studio

### Later reference applications

- Research Intelligence
- RFP and Proposal Copilot
- Contract and Policy Intelligence
- Customer Support Copilot
- Meeting-to-Knowledge Studio
- Architecture and Code Intelligence

Only Research Intelligence and RFP and Proposal Copilot are planned for the first expansion cycle. Other applications remain portfolio candidates until the flagship quality gates pass.

## Non-Goals

- Guaranteeing that generative models never make an error
- Building a no-code platform in the first release
- Supporting every listed application simultaneously
- Replacing proven databases, queues, or observability systems with custom implementations
- Moving existing application code merely to create a visually clean directory tree
- Adding autonomous agents where a deterministic workflow is safer and easier to evaluate

## Target Architecture

```text
NexusMind Showcase / Shipped Solution
                |
        Frontend Platform Shell
                |
      REST / SSE / WebSocket / MCP
                |
    +-----------+-------------------+
    |           Nexus Core          |
    | identity | jobs | artifacts   |
    | AI gateway | evidence | evals |
    | connectors | retrieval | audit|
    +-----------+-------------------+
                |
      Stable Application Contracts
                |
    +-----------+-----------+-------+
    | Knowledge | AuraSQL    | Career
    | Analyst   | Presentations | Research
    +-----------+-----------+-------+
                |
    PostgreSQL / pgvector / Object Storage
    RabbitMQ / Model Providers / Connectors
```

The first migration introduces contracts around the current implementation. Existing routes remain operational. Internal code movement happens only when a contract test proves that the new boundary is stable.

## Application Manifest

Every application provides an immutable manifest with:

- Stable application identifier and semantic version
- Display name, summary, icon, category, and capability badges
- Backend route prefixes and frontend route
- Required and optional platform capabilities
- Required environment keys without secret values
- Required database migration identifiers
- Required worker queues
- Demo scenario identifiers
- Health-check identifier
- Required permissions
- Packaging include paths

The platform registry validates duplicate identifiers, missing dependencies, incompatible capability versions, and invalid routes at startup. Invalid optional applications are disabled with a diagnostic; invalid core capabilities fail startup.

## Accuracy and Algorithm Architecture

### Common answer contract

AI-facing applications return a common result envelope containing:

- Output payload
- Evidence references
- Algorithm and model versions
- Confidence components rather than one opaque number
- Validation results
- Warnings and abstention reason
- Latency, token usage, and estimated cost
- Trace and evaluation identifiers

Applications may define typed payloads, but they cannot remove the common quality metadata.

### Retrieval

The retrieval framework supports composable strategies selected by an explicit router:

1. Query classification identifies factual lookup, comparison, synthesis, structural navigation, SQL, and unsupported requests.
2. Candidate retrieval combines BM25, dense vectors, metadata filters, and application-specific retrieval.
3. Reciprocal Rank Fusion combines heterogeneous rankings without assuming comparable raw scores.
4. Cross-encoder reranking improves top-result precision.
5. Maximum Marginal Relevance reduces duplicate context when diversity is valuable.
6. Parent-child or structural expansion restores context lost at chunk boundaries.
7. An answerability gate checks evidence coverage before generation.
8. The generator cites evidence spans and abstains when coverage remains below the application threshold.

Offline evaluation tracks retrieval recall, precision, mean reciprocal rank, normalized discounted cumulative gain, citation correctness, faithfulness, answer relevance, latency, and cost. Thresholds are application-specific and stored with evaluation dataset versions.

### AuraSQL

AuraSQL combines LLM planning with deterministic database controls:

- Schema graph and relationship extraction
- Column statistics and representative-value indexes
- Semantic metric definitions
- SQLGlot AST parsing and dialect normalization
- Allowlisted statement classes
- Read-only transactions and row/time limits
- `EXPLAIN` or dry-run validation where supported
- Execution-guided repair with bounded retries
- Result-shape and value sanity checks
- Golden query and execution-result evaluation

The system never executes unparsed generated SQL and never treats syntactic validity as semantic accuracy.

### Career Studio

Career Studio uses an evidence graph and a weighted bipartite matching model:

- One node set represents verified candidate claims.
- One node set represents parsed job requirements.
- Edges represent semantic match, evidence strength, recency, seniority, and transferability.
- Maximum-weight matching produces coverage without double-counting one claim across unrelated requirements.
- Deterministic validators reject unverified employers, dates, degrees, skills, and metrics.
- The LLM may rephrase verified claims but cannot introduce a claim without an evidence identifier.

The user sees evidence coverage, missing requirements, uncertainty, and truthful gaps instead of an uncalibrated ATS promise.

### Data Analyst Studio

The analysis planner selects deterministic methods based on data properties and user intent:

- Type inference and data-quality profiling
- Statistical tests with assumptions recorded
- Correlation measures selected by variable type
- Time-series validation, backtesting, and baseline comparison
- Leakage-aware predictive modeling
- Anomaly methods selected by sample size and distribution
- Reproducible Python or SQL execution artifacts

Narratives and recommendations link to computation outputs. Unsupported causal claims are labeled as hypotheses.

### Presentation Studio

Presentation generation uses a structured deck model and constraint-based composition:

- Narrative planner creates claims, evidence, audience intent, and story arc.
- Slide planner selects slide roles and information density.
- Layout solver applies minimum font size, safe margins, hierarchy, contrast, and object-overlap constraints.
- Asset selector scores charts, diagrams, icons, and generated imagery for narrative relevance.
- Renderer produces PPTX and preview images.
- Visual critic checks overflow, contrast, alignment, repetition, evidence coverage, and brand consistency.
- Only failed slides are regenerated; approved slides remain locked.

Visual evaluation uses deterministic geometry checks plus vision-model critique. Vision-model critique cannot override hard accessibility and overflow rules.

## Evaluation Framework

Each application registers:

- Dataset schema and version
- Metric implementations
- Minimum release thresholds
- Maximum latency and cost budgets
- Required deterministic validations
- Evaluator model and prompt versions when model-based evaluation is unavoidable
- Production feedback mapping

Evaluation results are immutable and linked to a git commit, application version, model version, prompt version, dataset version, and infrastructure profile. A model or prompt upgrade is rejected when any critical metric falls below its threshold, even if average quality improves.

## Workflow Framework

All long-running operations use a durable job contract:

- Queued, running, awaiting-input, succeeded, failed, cancelled, and expired states
- Monotonic progress events
- Idempotency keys
- Step checkpoints
- Bounded retries with categorized failure reasons
- Human approval and correction events
- Cancellation propagation
- Artifact and evaluation links
- Server-side job history

Frontend state is reconstructed from the server after refresh. WebSocket or SSE delivers updates but is never the source of truth.

## Artifact Framework

Artifacts include decks, reports, resumes, SQL results, charts, research notes, and exports. The framework provides:

- Typed content payload and renderer version
- Immutable versions and mutable working draft pointer
- Evidence references
- Parent-child lineage
- Diff, restore, comments, and approval
- Public or workspace-scoped sharing
- Retention and deletion
- Export status and download authorization

## Frontend Platform Design

### Platform shell

The frontend is a modular application host with:

- Application catalog and application overview pages
- Manifest-driven navigation
- Workspace and demo-mode switcher
- Persistent server-backed job center
- Artifact library
- Evidence and trace inspector
- Quality and evaluation dashboard
- Settings for providers, connectors, permissions, and branding
- Consistent loading, empty, partial, error, retry, and offline states

### Application experience contract

Each application frontend provides:

- Overview and guided demo
- Primary workflow entry page
- History page
- Result or artifact page
- Settings contribution when required
- Capability badges and architecture explanation
- Example scenarios
- Accessibility labels and keyboard navigation
- Error boundaries and retry behavior
- Analytics events that contain no sensitive content

### Design system

The existing Tailwind and Radix foundation remains. The platform adds semantic tokens for surface, text, border, status, quality, evidence, and application identity. Components consume semantic tokens rather than hard-coded colors.

Responsive behavior is defined at 360 px, 768 px, 1024 px, and 1440 px. WCAG 2.2 AA contrast and keyboard navigation are release requirements. Motion respects `prefers-reduced-motion`.

### Frontend state boundaries

- Server state: TanStack Query or equivalent query cache
- Authentication and small durable preferences: Zustand
- Workflow state: backend job API plus event stream
- Form state: local component state or form library
- Shareable filters and selected resources: URL state

Large page components are split by feature responsibility. API types are generated from OpenAPI or shared schemas rather than maintained as one manual file.

## Packaging and Delivery

A packaging profile selects:

- Core capability versions
- Application manifests
- Database, queue, storage, model, and connector adapters
- Frontend applications and navigation
- Environment schema
- Deployment target

The packager resolves dependencies, validates compatibility, generates deployment files, and runs application smoke tests. It never deletes files from the monorepo to create a distribution.

## Security and Privacy

- Short-lived access tokens are not placed in query strings.
- Secrets remain server-side and are referenced by identifiers.
- Resume and document content is classified as sensitive by default.
- Workspace isolation is enforced in services and repositories, not only routes.
- Uploaded files are size-limited, type-validated, malware-scanned, and retained by policy.
- Audit events record access, generation, export, sharing, and deletion.
- Evaluation and observability capture metadata by default and redact sensitive content.
- Generated SQL runs under least-privilege, read-only credentials unless an explicitly approved application requires otherwise.

## Testing and Release Gates

### Required test layers

- Backend unit tests for algorithms and validators
- Contract tests for manifests and platform interfaces
- Integration tests for database, queue, storage, and provider adapters
- Frontend component tests with Vitest and Testing Library
- Browser journeys with Playwright
- Visual regression for major application states and rendered slides
- Accessibility checks
- Security and dependency scans
- Load tests for retrieval, streaming, and job execution
- AI evaluation suites for every flagship application

### Merge requirements

A change cannot merge when:

- A critical deterministic validation fails
- An application evaluation falls below its registered threshold
- A core contract is broken without a versioned migration
- New frontend states lack loading, empty, error, and accessibility coverage
- A database change lacks a reversible migration
- A public API change lacks schema and client updates

## Delivery Sequence

1. Platform contracts and application catalog
2. Quality envelope, evaluation registry, and CI foundations
3. Durable jobs, artifacts, evidence, and frontend platform shell
4. Model gateway and adaptive retrieval
5. Knowledge Studio and AuraSQL upgrades
6. Data Analyst and Presentation Studio upgrades
7. Career Studio evidence architecture
8. Research Intelligence and RFP reference applications
9. Packaging profiles and generated distributions

Every sequence item must leave the repository deployable and preserve existing public routes until a documented migration is available.

## Success Criteria

- An existing application appears in the catalog through a validated manifest.
- A disabled application cannot register routes or navigation.
- A shipped profile contains only Core and its selected application dependencies.
- Every long-running workflow survives frontend refresh and reports server-backed status.
- Every flagship application has a versioned evaluation dataset and enforced release thresholds.
- Generated outputs expose evidence, validation state, model/algorithm versions, and abstention reasons.
- Frontend workflows meet WCAG 2.2 AA and have component plus browser coverage.
- Model and prompt upgrades cannot silently reduce a critical application metric.
- Application-specific code does not import another application's internal modules.

