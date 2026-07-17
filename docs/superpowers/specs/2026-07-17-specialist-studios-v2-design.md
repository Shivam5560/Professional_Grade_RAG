# Data Analyst and Career Studio V2 Design

**Date:** 2026-07-17  
**Status:** Approved for implementation  
**Decision owner:** Product owner  

## 1. Decision

Replace the current Data Analyst and Resume Studio implementations, their backend contracts, and their frontend integrations. The replacement is a modular monolith inside the existing FastAPI application. Each studio owns its domain model, orchestration, tools, validation, persistence, and API router while sharing authentication, durable jobs, evidence, quality metadata, artifacts, observability, and approvals.

The replacement will not preserve the legacy API as a compatibility layer. The existing frontend routes may remain familiar (`/analysis` and a renamed `/career` experience), but they will consume the new contracts. Legacy analysis, Nexus resume, resume-generator, and auto-tailor routes are removed only after the new clients and migration tests pass.

## 2. Why the Current Implementations Are Insufficient

### Data Analyst

The existing eight-step workflow has useful checkpointing and deterministic executors, but it loses important analytical meaning between stages. Planning mostly selects one of six broad executors and passes shallow parameters. Some methods are selected with broad heuristics, model validation is not consistently leakage-aware or baseline-relative, and narrative claims do not retain immutable links to the computations that support them. A polished narrative can therefore look stronger than its analytical provenance.

### Resume Studio

The current implementation combines one-shot LLM extraction, hand-weighted similarity or ATS scores, iterative rewriting, and PDF generation. It does not have a canonical verified career profile, claim-level provenance, explicit job-requirement entities, or a deterministic rule preventing a draft from introducing an unsupported employer, date, skill, degree, responsibility, or metric. The displayed fit score is more precise than the underlying evidence warrants.

## 3. Product Principles

1. **Evidence before prose.** A generated statement is publishable only when it references a computation record or a verified career claim.
2. **Deterministic tools before model judgment.** Models interpret intent, explain findings, and propose plans. Typed tools perform calculations, matching, validation, and artifact generation.
3. **Specialization through boundaries.** A specialist has a narrow contract, curated tools, explicit inputs and outputs, and a validator. Merely giving another prompt a role name does not create a specialist.
4. **Calibrated uncertainty.** Confidence is computed from evidence strength, method validity, data quality, and agreement—not from prose or finding count. The system abstains when critical validation fails.
5. **Reproducibility.** Analytical conclusions retain dataset snapshots, method versions, parameters, seeds, assumptions, and outputs. Career drafts retain source claim IDs, transformation history, and approvals.
6. **Autonomy with meaningful gates.** Data analysis normally runs end to end. Career Studio pauses for inferred-claim review and final publication approval.
7. **No false causality or false career claims.** Correlation is not described as causation without an appropriate design. Resume content cannot invent facts to improve a match score.

## 4. Architecture

```text
FastAPI application
├── platform/
│   ├── jobs/          durable run states, events, idempotency, cancellation
│   ├── evidence/      immutable evidence and provenance records
│   ├── quality/       AIResult, validations, versions, costs, abstention
│   ├── artifacts/     versioned files and structured outputs
│   └── approvals/     awaiting-input decisions and audit records
├── studios/data_analyst/
│   ├── api/           v2 request/response contracts and router
│   ├── domain/        plan, method, computation, claim, report models
│   ├── planning/      intent parser and deterministic method planner
│   ├── tools/         profiling, statistics, ML, time series, charts
│   ├── workflow/      state machine and recovery
│   ├── validation/    assumptions, leakage, sanity, claim verifier
│   └── evaluation/    golden datasets and release metrics
└── studios/career/
    ├── api/           v2 profile, role, match, draft, approval, artifact APIs
    ├── domain/        claims, evidence, requirements, matches, drafts
    ├── extraction/    source parsing into reviewable claims
    ├── matching/      weighted bipartite requirement-to-claim matching
    ├── writing/       evidence-constrained resume and career content
    ├── validation/    truth, ATS, chronology, duplication, layout checks
    ├── workflow/      state machine and approval pauses
    └── evaluation/    fabrication, coverage, and writing-quality gates
```

The domain packages may depend on `platform`, but `platform` cannot import either studio. Data Analyst and Career Studio cannot import each other. This keeps later service extraction possible without paying the distributed-systems cost now.

## 5. Shared Runtime Contracts

### 5.1 Run State

Every long-running operation uses one state model:

- `queued`
- `running`
- `awaiting_input`
- `succeeded`
- `failed`
- `cancelled`
- `expired`

Transitions are monotonic and validated. A run has an owner, studio ID, operation, idempotency key, input fingerprint, current step, progress, timestamps, cancellation flag, and categorized failure. Retrying the same idempotency key returns the existing run unless the caller explicitly requests a new revision.

### 5.2 Evidence and Results

The existing immutable `AIResult`, `EvidenceReference`, `QualityMetadata`, and `ValidationIssue` contracts remain the outer result envelope. V2 adds typed evidence records:

- `ComputationEvidence`: dataset snapshot, code or tool ID, parameters, seed, assumptions, output digest, and artifact IDs.
- `ClaimEvidence`: source document, source span, normalized claim, verification status, and confidence.
- `DerivedEvidence`: parent evidence IDs, deterministic transformation, and version.

Critical validation errors require an abstention reason and no publishable output.

### 5.3 Artifacts

Artifacts are immutable revisions with owner, studio, run, media type, content digest, lineage, and metadata. New revisions supersede old ones but do not overwrite them. Initial artifact types include dataset profiles, computation tables, charts, notebooks, analytical reports, career profiles, coverage matrices, resume drafts, and PDFs.

### 5.4 Approvals

An approval identifies a run, decision type, proposed changes, evidence, status, reviewer, and timestamp. Decisions are `approve`, `reject`, or `revise`. Only Career Studio uses mandatory approval in the initial release:

- review claims inferred from unstructured source text;
- approve the final resume before PDF publication.

## 6. Data Analyst Studio

### 6.1 User Contract

The user supplies a dataset or governed database snapshot, a question, and optional business context. The system returns:

- an editable analysis plan;
- a data-quality and semantic profile;
- method-specific computations with assumptions and diagnostics;
- evidence-linked findings and clearly labeled hypotheses;
- reproducible tables, charts, and a notebook-style execution trace;
- an executive report whose claims link back to computations;
- explicit limitations and recommended next analyses.

### 6.2 Specialist Components

1. **Intent Analyst** converts the request into decision objective, metrics, entities, segments, time grain, target, constraints, and ambiguity. It asks for input only when different interpretations would materially change the result.
2. **Data Profiler** deterministically infers types, missingness, uniqueness, distributions, outliers, time coverage, candidate identifiers, target risks, and sensitive fields.
3. **Method Planner** chooses registered methods using intent and data properties. It cannot name an unregistered tool. Each plan item records prerequisites, assumptions, inputs, expected output, cost class, and fallback.
4. **Statistical Investigator** performs descriptive and inferential work with effect sizes, confidence intervals, multiple-testing correction, power warnings, and assumption-aware test choice.
5. **Relationship Investigator** selects Pearson, Spearman, mutual information, Cramer's V, or other registered measures by variable type and distribution. It detects confounding risk and never upgrades association to causality.
6. **Segment and Anomaly Investigator** selects segmentation or anomaly methods by sample size, dimensionality, and distribution and explains stability limitations.
7. **Forecasting Investigator** validates time grain, uses rolling-origin backtesting, compares against naive and seasonal baselines, and reports forecast intervals and horizon limitations.
8. **Predictive Investigator** defines the prediction task, creates leakage-safe splits and preprocessing pipelines, compares interpretable baselines, calibrates where appropriate, and reports error slices and stability.
9. **Insight Synthesizer** creates structured candidate claims from computation evidence; it does not write directly from raw datasets.
10. **Analytical Verifier** rejects unsupported numbers, causal overreach, invalid methods, poor model comparisons, and claims without evidence IDs.
11. **Report Composer** turns verified claims into an audience-appropriate narrative and visual artifact without changing the claim payload.

Specialists 4–8 are tools behind the planner, not autonomous conversational personas. Parallel execution is allowed only when plan items have no unresolved dependencies.

### 6.3 Method Registry

Every analytical method declares:

- supported variable types and minimum sample conditions;
- required assumptions and diagnostic functions;
- parameter schema and deterministic defaults;
- resource limits and cost class;
- output schema, confidence components, and known limitations;
- implementation and semantic version;
- evaluator cases and release thresholds.

The planner produces a typed directed acyclic graph. The executor validates it before running anything. Invalid plans are repaired once; otherwise the run abstains with actionable guidance.

### 6.4 Computation and Claim Model

`AnalysisPlan` contains `PlanStep` records. A completed step creates a `ComputationRecord` with input snapshot ID, method ID/version, parameters, random seed, code digest, assumption results, metrics, warnings, and artifacts. A `FindingClaim` contains a subject, predicate, value, scope, evidence IDs, confidence components, and language class (`observation`, `association`, `prediction`, `hypothesis`, or `recommendation`).

The narrative receives only verified `FindingClaim` objects. All rendered numbers are resolved from their evidence payload, preventing the model from silently changing values.

### 6.5 API

Base path: `/api/v2/data-analyst`

- `POST /datasets` — upload and create immutable dataset snapshot
- `GET /datasets/{dataset_id}/profile`
- `POST /runs` — start an analysis using an idempotency key
- `GET /runs/{run_id}` — status, progress, plan, warnings
- `POST /runs/{run_id}/cancel`
- `PATCH /runs/{run_id}/plan` — edit before execution if the run is still plannable
- `GET /runs/{run_id}/computations`
- `GET /runs/{run_id}/claims`
- `GET /runs/{run_id}/report`
- `GET /artifacts/{artifact_id}`

All endpoints are owner-scoped. The server derives the user from authentication; request bodies never accept an authoritative `user_id`.

## 7. Career Studio

### 7.1 User Contract

The user builds a canonical, verified career profile from resumes and supporting material, supplies a target role, reviews uncertain claims, and receives:

- a structured requirement analysis;
- a requirement-to-evidence coverage matrix;
- calibrated strengths, truthful gaps, and uncertainty;
- role-specific resume drafts with claim provenance;
- ATS compatibility diagnostics separated from role fit;
- approved PDF/DOCX artifacts and version comparisons;
- reusable interview stories and application guidance derived from the same evidence.

### 7.2 Career Evidence Graph

The canonical graph contains people, roles, employers, projects, education, certifications, skills, responsibilities, outcomes, dates, and metrics. Every claim has:

- a stable claim ID and typed subject/predicate/object;
- one or more source spans;
- `verified`, `inferred`, `disputed`, or `rejected` status;
- confidence and verifier identity;
- temporal scope and relationships to other claims.

Inferred claims cannot be used in a published resume until approved. Rejected claims remain in the audit trail and are excluded from generation.

### 7.3 Job Requirement Model

The Role Analyst parses a job description into normalized requirements:

- mandatory and preferred skills;
- responsibilities and expected outcomes;
- experience, seniority, education, certification, location, and work-mode constraints;
- domain vocabulary and ATS terms;
- confidence and exact source spans.

Requirements are not treated as a flat keyword bag.

### 7.4 Matching

The matcher creates candidate edges between requirements and verified claims. Edge weight combines semantic relevance, evidence strength, recency, duration, seniority, transferability, and specificity. Maximum-weight bipartite matching prevents one claim from satisfying unrelated requirements multiple times. Explicit composite claims may support more than one requirement only when the relationship is modeled and visible.

The result exposes mandatory coverage, preferred coverage, unsupported requirements, transferable evidence, uncertain matches, and the exact evidence chosen. It reports ranges or categories when calibration does not justify a precise score.

### 7.5 Specialist Components

1. **Profile Curator** extracts atomic claims and requests approval for uncertain facts.
2. **Role Analyst** builds the typed requirement graph from the job description.
3. **Evidence Matcher** performs deterministic weighted matching and coverage calculation.
4. **Career Strategist** chooses positioning, ordering, and truthful gap-handling strategy.
5. **Resume Writer** may select, reorder, compress, or rephrase verified claims. Every bullet carries source claim IDs.
6. **Truth Guardian** compares every draft assertion, employer, title, date, skill, degree, and metric against approved claims. Any unsupported assertion is a critical error.
7. **ATS Validator** checks parseability, headings, keyword coverage, contact structure, and layout risks. ATS compatibility remains distinct from candidate-role fit.
8. **Editorial Critic** checks specificity, repetition, action-result structure, readability, seniority alignment, and page budget without inventing content.
9. **Artifact Renderer** generates revisioned DOCX/PDF files and verifies text extraction after rendering.

### 7.6 Draft Transformations

Every generated bullet stores:

- source claim IDs;
- selected transformation (`verbatim`, `compressed`, `combined`, `reordered`, or `rephrased`);
- before and after text;
- added keywords and where their factual support comes from;
- Truth Guardian result.

Combining claims is allowed only when they share a compatible employer/project and time scope. Metrics may never be synthesized, rounded upward, or transferred between claims.

### 7.7 API

Base path: `/api/v2/career`

- `POST /sources` — upload resume or supporting source
- `GET /sources/{source_id}`
- `GET /profile`
- `PATCH /profile/claims/{claim_id}` — correct or enrich a claim
- `POST /profile/claims/{claim_id}/verify`
- `POST /roles` — parse a target role
- `GET /roles/{role_id}/requirements`
- `POST /matches` — create requirement-to-claim match run
- `GET /matches/{match_id}`
- `POST /drafts` — create an evidence-constrained draft
- `GET /drafts/{draft_id}`
- `POST /drafts/{draft_id}/revise`
- `POST /approvals/{approval_id}` — approve, reject, or request revision
- `POST /drafts/{draft_id}/publish` — requires final approval
- `GET /artifacts/{artifact_id}`

## 8. Persistence

Shared tables:

- `studio_runs`
- `studio_run_events`
- `studio_artifacts`
- `studio_approvals`
- `studio_evidence`
- `studio_quality_results`

Data Analyst tables:

- `analysis_datasets`
- `analysis_plans`
- `analysis_plan_steps`
- `analysis_computations`
- `analysis_claims`
- `analysis_reports`

Career Studio tables:

- `career_sources`
- `career_claims`
- `career_claim_evidence`
- `career_roles`
- `career_requirements`
- `career_match_runs`
- `career_match_edges`
- `career_drafts`
- `career_draft_claims`

JSON is used for versioned method payloads and rendering metadata, not as a substitute for core relational entities. Owner IDs and run IDs are indexed on every user-scoped table. Immutable records are appended; corrections create superseding revisions.

## 9. Workflow and Failure Handling

Each workflow is an explicit state machine persisted after every successful step. Workers claim steps using leases. A lease expiry permits safe retry because steps use idempotency keys and content digests.

Errors are categorized as validation, user-input, dependency, resource-limit, transient-provider, internal, or cancelled. Retry policies apply only to transient errors. Partial computations and draft revisions remain available after failure. Cancellation propagates to queued and running child work and prevents artifact publication.

If the LLM is unavailable, deterministic profiling, matching, and validation remain accessible where meaningful. The system clearly reports which interpretive stage could not complete. It never silently substitutes generic prose.

## 10. Frontend Replacement

### Data Analyst Workspace

The `/analysis` experience becomes a workspace with dataset profile, editable plan, live run graph, computation notebook, findings/evidence panel, report canvas, limitations, and artifact history. Users can inspect how a number was computed and which assumptions passed.

### Career Workspace

Resume Studio is renamed Career Studio and moves to `/career`. It includes source ingestion, claim review, canonical profile, job requirements, coverage matrix, gap strategy, evidence-linked editor, validation panel, approval queue, version comparison, and export. The interface never presents ATS compatibility as a hiring probability.

The homepage manifest and navigation use `career-studio`; obsolete `/nexus` and `/workflows/auto-tailor` entry points are removed after the migrated pages pass route tests.

## 11. Evaluation and Release Gates

### Data Analyst

- correct method selection on typed scenario fixtures;
- assumption diagnostics present for every registered inferential method;
- no target leakage in adversarial predictive fixtures;
- forecasting beats or honestly loses to declared baselines;
- every published numerical claim resolves to computation evidence;
- zero unsupported causal language in the critical evaluation set;
- deterministic reruns match within declared tolerances.

### Career Studio

- zero unsupported employers, titles, dates, degrees, skills, or metrics in the critical fabrication set;
- every draft assertion resolves to approved claim IDs;
- mandatory-requirement coverage matches hand-labeled fixtures within the registered threshold;
- no double counting outside modeled composite evidence;
- ATS checks distinguish parseability from role fit;
- rendered artifacts round-trip through text extraction without material loss.

A release fails if a critical metric fails even when the average score improves. Evaluation records include git commit, application version, model and prompt versions, dataset version, latency, and cost.

## 12. Security and Privacy

- Ownership comes exclusively from authenticated identity.
- Uploaded files are validated by extension, MIME signature, size, and parser limits.
- Spreadsheet formula injection and unsafe archive contents are rejected.
- Database-backed analyses use read-only snapshots and query limits.
- Sensitive columns and career claims are labeled before model use.
- Logs store identifiers and digests rather than raw datasets, resumes, or job descriptions.
- Artifact access is authorized per request and uses safe filenames or object-store keys.

## 13. Migration Strategy

1. Build shared run, evidence, artifact, and approval contracts with persistence and tests.
2. Build Data Analyst domain models, method registry, planner, validators, workflow, and API.
3. Migrate `/analysis` to the v2 API and pass evidence/reproducibility acceptance tests.
4. Build Career graph, role parser, matching, truth-constrained drafting, validators, workflow, and API.
5. Migrate the UI to `/career` and pass fabrication and approval acceptance tests.
6. Migrate useful legacy records into source/artifact history where trustworthy.
7. Remove old routers, worker branches, models, pages, and settings after route and data-migration verification.

Removal is the final migration step, not the first, so the repository remains runnable throughout implementation. No public compatibility adapter is retained after cutover.

## 14. Testing Strategy

Implementation follows test-driven development:

- contract tests for frozen models, identifiers, state transitions, and ownership;
- unit tests for every deterministic tool and validator;
- property tests for evidence lineage, truth preservation, matching constraints, and idempotency;
- adversarial tests for leakage, causal overreach, fabricated metrics, chronology conflicts, and prompt injection in uploaded text;
- workflow tests for retry, resume, cancellation, approval pause, and partial failure;
- API tests for authorization, lifecycle, and artifact access;
- golden evaluation fixtures for both studios;
- frontend route, contract, accessibility, and critical-flow tests.

Model-based evaluation may supplement but cannot override deterministic critical gates.

## 15. Initial Delivery Boundary

The first executable vertical slice will establish shared contracts plus one end-to-end path per studio:

- Data Analyst: upload snapshot → profile → deterministic analysis plan → computation evidence → verified claim result.
- Career Studio: ingest structured source → claim graph → role requirements → weighted match → evidence-constrained draft → truth validation → approval state.

This slice deliberately excludes presentation generation, interview coaching, cover letters, and broad method catalogs until the evidence and truth foundations pass their gates.
