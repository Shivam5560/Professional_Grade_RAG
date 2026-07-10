# NexusMind Platform Master Roadmap

> **For agentic workers:** This is the coordination roadmap for a series of independently executable implementation plans. Do not implement the whole roadmap as one change. Each plan named below must use `superpowers:subagent-driven-development` or `superpowers:executing-plans` and pass its own review gates.

**Goal:** Evolve NexusMind into a framework-first AI application showcase whose shared core and selected reference applications can be packaged as production-grade solutions.

**Architecture:** Stabilize contracts around the current application before moving code. Build quality, evidence, workflow, artifact, and frontend platform primitives once; migrate each flagship through those contracts independently. Every phase ends with a deployable repository and preserves current routes until a tested migration exists.

**Tech Stack:** Python 3.11, FastAPI, Pydantic 2, SQLAlchemy, Alembic, PostgreSQL/pgvector, RabbitMQ, LlamaIndex, Next.js 14, React 18, TypeScript, Tailwind, Radix UI, Zustand, TanStack Query, Vitest, Testing Library, Playwright, Langfuse, Docker

## Global Constraints

- No AI feature may claim perfect accuracy.
- Critical generated outputs must include evidence, validation state, algorithm/model versions, and abstention reasons.
- Deterministic algorithms own parsing, validation, ranking, constraints, statistics, permissions, and safety checks wherever applicable.
- Application code may depend on Nexus Core contracts but not another application's internal modules.
- Backend and frontend contracts must be versioned together.
- Every backend capability includes frontend loading, empty, partial, error, retry, and accessibility states in the same phase.
- Every phase adds unit, contract, integration, frontend, end-to-end, and AI evaluation coverage appropriate to its risk.
- Existing public routes remain functional until a documented migration and compatibility test are present.
- Database changes require reversible Alembic migrations.
- Tokens and secrets must not appear in URLs, client logs, traces, or generated artifacts.
- WCAG 2.2 AA, keyboard navigation, reduced motion, and responsive layouts at 360, 768, 1024, and 1440 px are release requirements.
- Model or prompt changes cannot merge when a critical registered evaluation metric regresses below its threshold.

---

## Plan Series

### Plan 1: Platform Foundation and Application Catalog

**Purpose:** Establish stable application contracts and make the showcase manifest-driven without moving existing feature implementations.

**Backend outcomes:**

- Typed `AppManifest`, capability identifiers, semantic versions, dependencies, permissions, route metadata, environment requirements, demo scenarios, and health metadata
- Startup registry with duplicate, dependency, version, and route validation
- Manifests for Knowledge Studio, AuraSQL, Data Analyst, Presentation, Career, and Developer/MCP
- Read-only catalog API
- Shared quality-result envelope contract
- Contract-test foundation

**Frontend outcomes:**

- Typed application registry
- Application catalog, overview, capability badges, demo scenarios, architecture summary, health state, and request/deploy call to action
- Manifest-driven primary navigation
- Vitest, Testing Library, axe, and Playwright foundations

**Exit gate:** Disabling an application removes its navigation and prevents route registration without editing unrelated application files.

**Detailed plan:** `docs/superpowers/plans/2026-07-10-nexusmind-platform-foundation.md`

### Plan 2: Evaluation Control Plane and CI Quality Gates

**Purpose:** Make measured quality a platform capability before upgrading algorithms or prompts.

**Backend outcomes:**

- Evaluation dataset, case, run, metric, threshold, and result contracts
- Application evaluator registry
- Immutable evaluation run storage linked to commit, app, dataset, model, prompt, and algorithm versions
- Deterministic metric runner and model-judge adapter with strict version capture
- Release-gate command and machine-readable report
- Baseline datasets for Knowledge Chat, AuraSQL, Data Analysis, Presentation, and Career

**Frontend outcomes:**

- Quality dashboard by application and version
- Regression comparison, failed-case drill-down, evidence display, latency, and cost views
- Explicit distinction between deterministic metrics and model-judged metrics

**Algorithms and metrics:**

- Retrieval Recall@K, Precision@K, MRR, and nDCG
- Citation entailment and evidence coverage
- Text2SQL exact execution-result comparison and safety violations
- Statistical result tolerance and narrative claim support
- Presentation geometry, overflow, contrast, repetition, and evidence coverage
- Career claim preservation, requirement coverage, and fabrication count

**Exit gate:** CI rejects a deliberately regressed model or prompt against at least one critical metric for each flagship application.

### Plan 3: Durable Jobs, Artifacts, Evidence, and Audit

**Purpose:** Make every long-running workflow recoverable and every output traceable.

**Backend outcomes:**

- Server-backed job state machine with idempotency, checkpoints, retry categories, cancellation, expiration, and approval events
- Versioned artifact service for reports, decks, resumes, charts, SQL results, and research notes
- Evidence reference and claim-evidence link contracts
- Workspace-aware audit events
- SSE/WebSocket events as projections of durable job state

**Frontend outcomes:**

- Server-hydrated job center that survives refresh
- Job timeline, cancel, retry, resume, approval, and failure-detail experiences
- Artifact library with versions, diff, restore, comments, approval, and export state
- Evidence inspector shared by all result pages

**Exit gate:** A running analysis survives browser refresh and server process restart from its latest durable checkpoint.

### Plan 4: Model Gateway, Prompt Registry, and Adaptive Retrieval

**Purpose:** Replace scattered provider and retrieval decisions with evaluated policies.

**Backend outcomes:**

- Task contracts for generation, structured generation, embedding, reranking, and tool use
- Provider adapters with fallback, retry, circuit breaker, cost, latency, and privacy policy
- Versioned prompt registry and structured-output repair policy
- Retrieval router selecting lexical, dense, structural, SQL, graph, or no retrieval
- RRF fusion, cross-encoder reranking, MMR diversity, structural expansion, and answerability gate
- Response envelope with evidence, confidence components, warnings, and abstention

**Frontend outcomes:**

- Provider and policy settings
- Retrieval trace showing strategy, candidates, reranking, evidence selection, and abstention
- Prompt/model experiment comparison linked to evaluation runs

**Exit gate:** The router outperforms the current fixed default on the registered evaluation set without exceeding its latency and cost budgets.

### Plan 5: Knowledge Studio and AuraSQL

**Purpose:** Demonstrate high-accuracy unstructured and structured-data applications on the new core.

**Knowledge Studio algorithms:**

- Query classification and decomposition
- Hybrid retrieval with RRF and reranking
- Parent-child or PageIndex structural context
- Evidence coverage and abstention
- Claim-level citations and contradiction reporting
- Multimodal document and table extraction

**AuraSQL algorithms:**

- Schema graph and relationship inference
- Column statistics and representative-value retrieval
- Semantic metric layer
- SQLGlot AST validation and dialect normalization
- Read-only execution sandbox, row/time limits, `EXPLAIN`, bounded repair, and result sanity checks

**Frontend outcomes:**

- Research notebook, source comparison, citation viewer, and reusable collections
- AuraSQL schema explorer, query plan, generated SQL diff, execution safety display, saved analyses, dashboards, and scheduled reports

**Exit gate:** Both applications meet their registered quality thresholds on unseen evaluation cases and expose complete evidence or execution traces.

### Plan 6: Data Analyst and Presentation Studio

**Purpose:** Produce reproducible analysis and visually validated editable presentations.

**Data-analysis algorithms:**

- Type inference and data-quality scoring
- Assumption-aware statistical test selection
- Variable-type-aware correlation
- Time-series backtesting and baseline comparison
- Leakage-aware modeling and calibrated validation
- Reproducible computation artifacts

**Presentation algorithms:**

- Structured deck document model
- Audience and narrative planning
- Constraint-based layout solver
- Asset relevance scoring
- Deterministic geometry, overflow, contrast, and accessibility checks
- Vision-model visual critique bounded by hard rules
- Slide-level regeneration with approved-slide locking

**Frontend outcomes:**

- Editable analysis plan and computation trace
- Interactive report workspace
- Outline approval, deck editor, slide navigator, evidence panel, brand kit, template import, slide-level regeneration, preview, comments, and export

**Exit gate:** Generated decks pass geometry and accessibility gates, preserve evidence links, and support editing one slide without regenerating approved slides.

### Plan 7: Career Studio Evidence Architecture

**Purpose:** Make truthful career intelligence the product differentiator.

**Algorithms:**

- Canonical verified career profile
- Evidence graph for experience, education, projects, skills, dates, and metrics
- Structured job-requirement decomposition
- Weighted bipartite requirement-to-claim matching
- Recency, seniority, transferability, and evidence-strength scoring
- Deterministic fabrication validators
- Calibrated coverage and gap reporting

**Frontend outcomes:**

- Career profile and evidence editor
- Requirement coverage matrix
- Claim provenance viewer
- Resume version and variant comparison
- Cover letter, recruiter message, interview stories, opportunity comparison, and application tracker

**Exit gate:** No exported resume contains an employer, degree, date, skill, or metric without a verified evidence reference or an explicit user-approved override recorded in the audit log.

### Plan 8: Research Intelligence and RFP Copilot

**Purpose:** Add two reference applications that reuse the full core while demonstrating commercially distinct workflows.

**Research Intelligence:**

- Research plan, source collection, credibility scoring, contradiction analysis, claim graph, report, and presentation generation

**RFP Copilot:**

- Requirement extraction, compliance matrix, knowledge retrieval, evidence-backed drafting, missing-answer detection, review workflow, proposal export, and executive presentation

**Frontend outcomes:**

- Guided demo scenarios and reusable templates
- Human approval at plan, evidence, draft, and export stages
- Side-by-side source, claim, and generated-content review

**Exit gate:** Both applications can be disabled or packaged independently and share no internal application imports.

### Plan 9: Packaging, Deployment Profiles, and Developer Platform

**Purpose:** Convert the modular architecture into a repeatable delivery mechanism.

**Outcomes:**

- Packaging profiles selecting Core, applications, adapters, connectors, and branding
- Dependency and compatibility resolution
- Generated environment schema, Docker Compose, Helm values, migrations, smoke tests, and operations guide
- REST/OpenAPI client generation
- Expanded MCP tools for applications, jobs, artifacts, evidence, and approvals
- Developer portal with API playground, webhook testing, traces, usage, and deployment request flow

**Exit gate:** CI builds and smoke-tests at least three profiles: Core + Knowledge, Core + AuraSQL, and Core + Career.

## Cross-Plan Frontend Rules

Frontend work is not deferred to a final polish phase. Every plan must deliver its usable frontend slice with:

- Generated or contract-checked API types
- Route-level error boundary
- Loading, empty, partial, success, and error stories
- Keyboard and screen-reader tests
- Responsive behavior
- Analytics events containing identifiers and timings but no sensitive content
- Unit/component tests and a Playwright happy path
- Visual regression for stable, business-critical screens

## Architectural Review Gates

Before starting each detailed plan, reviewers must confirm:

1. The capability belongs in Nexus Core or one named application, not both.
2. Interfaces expose behavior and contracts rather than database internals.
3. Deterministic algorithms are used wherever they can replace probabilistic judgment.
4. The evaluation dataset and success metric exist before prompt or model optimization.
5. Failure, abstention, and partial-result behavior are specified.
6. Frontend states and accessibility behavior are part of the deliverable.
7. The application can still be disabled and packaged independently.

## Program Completion Criteria

- Six flagship applications use stable manifests and common platform contracts.
- Two additional reference applications demonstrate reuse without internal coupling.
- Three packaging profiles are built and smoke-tested automatically.
- Every flagship has enforced AI quality, latency, and cost thresholds.
- Durable jobs and artifacts survive refresh and process restart.
- Evidence and validation state are visible for every critical generated output.
- Frontend component, browser, accessibility, and visual regression suites run in CI.
- Security, dependency, migration, and performance checks are release gates.

