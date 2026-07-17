# Specialist Studios V2 Backend Cutover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` and follow each RED/GREEN checkpoint in order.

**Goal:** Persist the reviewed Data Analyst and Career Studio cores, expose owner-scoped `/api/v2` contracts, switch the application registry to those routers, and remove legacy backend entry points only after replacement contract tests pass.

**Architecture:** Keep the studios as a modular monolith. Shared SQLAlchemy records and repositories live under `app.platform.persistence`; studio-specific persistence and API adapters live inside each studio. Routers call synchronous in-process application services during this phase. Domain contracts remain independent from FastAPI and SQLAlchemy. JSON columns store versioned frozen payloads, while owner, run, state, lineage, revision, and lookup identities remain relational and indexed.

**Tech stack:** FastAPI, Pydantic 2, SQLAlchemy, PostgreSQL-compatible SQL, pytest, pandas/SciPy specialist cores.

## Non-negotiable constraints

- Authentication is authoritative. Request bodies never accept an owner or user ID.
- Every repository read and mutation is owner-scoped, including artifacts and approvals.
- Idempotency is enforced by `(owner_id, studio_id, idempotency_key)` and input fingerprint.
- Artifact revisions are append-only. Creating a child revision uses an atomic compare-and-swap against the current parent and unique `(artifact_id, revision)` storage.
- Evidence and quality payloads are serialized with `model_dump(mode="json")` and hydrated through the public Pydantic contracts.
- Dataset uploads validate extension, MIME signature, size, parser limits, archive safety, and spreadsheet formula hazards before persistence.
- This phase performs no provider/network calls. It invokes the reviewed deterministic cores in process.
- Cancellation and approval use the shared hardened transition helpers; persisted state cannot bypass model invariants.
- Legacy routers remain installed until replacement router, ownership, migration, and registry tests are green. They are then removed without a compatibility adapter.

## Parallel ownership map

After Task 2 is complete, Tasks 3 and 4 may run in parallel.

| Slice | Exclusive production ownership |
|---|---|
| Shared persistence | `backend/app/platform/persistence/**`, `backend/migrations/specialist_studios_v2_0001.sql`, `backend/tests/platform/persistence/**` |
| Data Analyst API | `backend/app/studios/data_analyst/persistence/**`, `backend/app/studios/data_analyst/api/**`, `backend/tests/studios/data_analyst/api/**` |
| Career API | `backend/app/studios/career/persistence/**`, `backend/app/studios/career/api/**`, `backend/tests/studios/career/api/**` |
| Cutover integration | `backend/app/platform/apps/{fastapi.py,builtin.py}`, route-removal files, integration tests |

Do not modify another slice's files. Shared-contract changes require a new reviewed task rather than an incidental edit.

---

## Task 1: Shared durable records and SQL migration

**Files:**

- Create `backend/app/platform/persistence/__init__.py`
- Create `backend/app/platform/persistence/models.py`
- Create `backend/app/platform/persistence/serialization.py`
- Create `backend/migrations/specialist_studios_v2_0001.sql`
- Create `backend/tests/platform/persistence/test_models.py`
- Create `backend/tests/platform/persistence/test_migration_contract.py`

### RED

Write tests asserting:

- `StudioRunRecord`, `StudioEvidenceRecord`, `StudioArtifactRecord`, `StudioApprovalRecord`, and `StudioQualityResultRecord` use the shared `Base`;
- every user-scoped table has non-null `owner_id` and indexed `run_id` where applicable;
- run idempotency and artifact revision uniqueness are declared;
- artifact parent/revision fields cannot represent an immediate-parent mismatch;
- Pydantic contracts round-trip through JSON serialization without mutation or non-finite values;
- the SQL migration creates the same tables, unique constraints, foreign keys, and indexes and has a guarded transaction.

Run:

```bash
cd backend
PYTHONPATH=. /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with sqlalchemy pytest tests/platform/persistence/test_models.py tests/platform/persistence/test_migration_contract.py -q
```

Expected: collection fails because `app.platform.persistence` does not exist.

### GREEN

Implement append-oriented SQLAlchemy records. Use string IDs, timezone-aware timestamps, explicit state/status strings, JSON payloads, content digests, and relational owner/run/revision columns. Keep the migration PostgreSQL-compatible and safe to run once. Serialization helpers must validate back into the public contract type rather than returning raw dictionaries.

Run the focused tests and `python -m compileall -q app/platform/persistence`.

### Commit

```bash
git add backend/app/platform/persistence backend/tests/platform/persistence backend/migrations/specialist_studios_v2_0001.sql
git commit -m "feat(platform): persist specialist runtime records"
```

## Task 2: Owner-scoped repositories, idempotency, approvals, and artifact CAS

**Files:**

- Create `backend/app/platform/persistence/repositories.py`
- Create `backend/tests/platform/persistence/test_repositories.py`
- Modify `backend/app/platform/persistence/__init__.py`

### RED

Use an isolated SQLite session for behavioral repository tests. Prove:

- creating the same run idempotency key and fingerprint returns the same run;
- reusing the key with a different fingerprint rejects;
- a second owner cannot read, cancel, approve, or attach evidence to the first owner's run;
- state transitions hydrate the contract, call the shared helper, then persist the validated result;
- cancellation-requested runs can only become cancelled;
- approval decisions require the run owner and preserve reviewer/timestamp audit fields;
- artifact revision 1 has no parent, revision N has parent revision N-1, stale concurrent parents reject, and duplicate revisions reject;
- transaction rollback leaves no partial evidence/artifact/approval state.

Run:

```bash
cd backend
PYTHONPATH=. /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with sqlalchemy pytest tests/platform/persistence/test_repositories.py -q
```

Expected: imports or behaviors fail before repositories are implemented.

### GREEN

Implement small repositories with an explicit SQLAlchemy `Session` constructor. Every method accepts `owner_id` as a required keyword and includes it in the query predicate. Use `flush()` within caller-owned transactions. Convert uniqueness races into stable domain errors. Artifact compare-and-swap must use a conditional query/update or locked parent row; an application-only pre-check is insufficient.

Run all `tests/platform` plus compile and diff checks.

### Commit

```bash
git add backend/app/platform/persistence backend/tests/platform/persistence
git commit -m "feat(platform): add owner-scoped specialist repositories"
```

---

## Task 3: Data Analyst snapshot persistence and `/api/v2/data-analyst`

**Depends on:** Task 2.

**Files:**

- Create `backend/app/studios/data_analyst/persistence/__init__.py`
- Create `backend/app/studios/data_analyst/persistence/models.py`
- Create `backend/app/studios/data_analyst/persistence/repository.py`
- Create `backend/app/studios/data_analyst/api/__init__.py`
- Create `backend/app/studios/data_analyst/api/contracts.py`
- Create `backend/app/studios/data_analyst/api/service.py`
- Create `backend/app/studios/data_analyst/api/router.py`
- Create `backend/tests/studios/data_analyst/api/test_repository.py`
- Create `backend/tests/studios/data_analyst/api/test_router.py`
- Create `backend/tests/studios/data_analyst/api/test_upload_security.py`

### RED: persistence

Test immutable dataset snapshots, profiles, plans, computations, and claims. Assert owner/run/snapshot lookup indexes, append-only computation and claim IDs, exact frozen payload hydration, and rollback on partial run persistence.

### RED: upload security

Test valid bounded CSV upload and rejection of:

- extension/MIME mismatch;
- oversized request and excessive row/column/parser limits;
- NUL/binary content and unsafe archive formats;
- spreadsheet cells beginning with formula control characters when later export would be unsafe;
- filenames used as filesystem paths.

The application service should hash bytes, parse into a bounded DataFrame, build the reviewed profile, and persist the snapshot by digest. Raw bytes stay behind an opaque storage key; tests may use an in-memory test store.

### RED: router contract

Build a minimal FastAPI test app with dependency overrides for authentication, DB, and snapshot storage. Prove:

- `POST /api/v2/data-analyst/datasets` returns snapshot ID and profile;
- `POST /runs` uses an `Idempotency-Key` header and never accepts `user_id`;
- `GET /runs/{id}`, `/computations`, and `/claims` return only the authenticated owner's data;
- starting a deterministic run persists queued → running → succeeded and exact evidence-linked claims;
- invalid analysis critically abstains and persists categorized failure;
- cancellation uses request/cancel semantics and rejects post-cancellation success;
- unknown/cross-owner IDs return 404 without leaking existence.

Run:

```bash
cd backend
PYTHONPATH=. /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with sqlalchemy --with fastapi==0.115.12 --with httpx==0.25.2 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst/api -q
```

### GREEN

Implement the smallest synchronous adapter around `DataAnalystSpecialist`. Request/response contracts expose profile, plan, run, computations, claims, limitations, and quality metadata directly; do not flatten them into generic dictionaries. Report/artifact endpoints may return `501` only if they are omitted from the registered router and documented as the next slice—do not advertise fake completion.

Run the complete Data Analyst and platform suites.

### Commit

```bash
git add backend/app/studios/data_analyst/{persistence,api} backend/tests/studios/data_analyst/api
git commit -m "feat(data-analyst): expose durable v2 analysis API"
```

---

## Task 4: Career persistence and `/api/v2/career`

**Depends on:** Task 2. May run in parallel with Task 3.

**Files:**

- Create `backend/app/studios/career/persistence/__init__.py`
- Create `backend/app/studios/career/persistence/models.py`
- Create `backend/app/studios/career/persistence/repository.py`
- Create `backend/app/studios/career/api/__init__.py`
- Create `backend/app/studios/career/api/contracts.py`
- Create `backend/app/studios/career/api/service.py`
- Create `backend/app/studios/career/api/router.py`
- Create `backend/tests/studios/career/api/test_repository.py`
- Create `backend/tests/studios/career/api/test_router.py`
- Create `backend/tests/studios/career/api/test_upload_security.py`

### RED: persistence

Prove append-only source, claim, role, requirement, match, draft, and draft-claim records. Corrections create superseding claim revisions; rejected claims remain auditable and cannot enter a publication draft. Draft-to-claim and requirement-to-match relationships are relational, not hidden only inside JSON.

### RED: router and approvals

Using an authenticated FastAPI test app, prove:

- `POST /sources` accepts a bounded supported document and creates reviewable claims without accepting owner identity;
- structured claim ingestion is supported for the deterministic phase; unimplemented free-form extraction returns an explicit capability error rather than fabricated claims;
- profile claim verify/reject/revise actions are owner-scoped and audited;
- `POST /roles` stores typed requirements and exact spans;
- `POST /matches` returns one-to-one matches and calibrated coverage ranges;
- `POST /drafts` returns evidence-linked deterministic drafts and pauses for inferred-claim or final approval;
- approval decisions bind owner, run, draft, and evidence IDs exactly;
- publish rejects unapproved, stale, truth-invalid, or non-verbatim/unregistered transformations;
- cross-owner source, role, match, draft, approval, and artifact access returns 404.

Run:

```bash
cd backend
PYTHONPATH=. /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with sqlalchemy --with fastapi==0.115.12 --with httpx==0.25.2 --with scipy pytest tests/studios/career/api -q
```

### GREEN

Implement a synchronous adapter around `CareerSpecialist`. Preserve the conservative publication boundary from the reviewed core: exact verbatim or explicitly registered deterministic transformations only. Keep ATS parseability separate from match coverage; do not return a hiring probability.

Run the complete Career and platform suites.

### Commit

```bash
git add backend/app/studios/career/{persistence,api} backend/tests/studios/career/api
git commit -m "feat(career): expose durable truth-gated v2 API"
```

---

## Task 5: Register v2 routers and switch application manifests

**Depends on:** Tasks 3 and 4.

**Files:**

- Modify `backend/app/platform/apps/fastapi.py`
- Modify `backend/app/platform/apps/builtin.py`
- Create `backend/tests/platform/apps/test_specialist_v2_routing.py`
- Create `backend/tests/integration/test_specialist_v2_cutover.py`

### RED

Assert:

- registry IDs `data-analyst-v2` and `career-studio-v2` resolve to the new routers;
- manifests advertise `/api/v2/data-analyst` and `/api/v2/career`, no provider env requirement for deterministic capabilities, and accurate packaging paths;
- route tables contain each v2 route exactly once;
- authenticated smoke flows persist and retrieve one analysis and one approval-gated career draft;
- legacy routes are still present during this task, so removal has an explicit later gate.

### GREEN

Add router specs with prefix `/api/v2`. Update existing `data-analyst` and `career-studio` manifests in place rather than creating duplicate homepage applications. Keep frontend routes unchanged until the client cutover phase.

Run registry, platform, both studio, and integration suites.

### Commit

```bash
git add backend/app/platform/apps backend/tests/platform/apps backend/tests/integration/test_specialist_v2_cutover.py
git commit -m "feat(platform): register specialist studios v2 APIs"
```

## Task 6: Remove legacy backend entry points after replacement verification

**Depends on:** Task 5 green and a recorded migration dry run.

**Candidate files:**

- Delete `backend/app/api/routes/analysis.py`
- Delete `backend/app/api/routes/nexus_resume.py`
- Delete `backend/app/api/routes/resumegen.py`
- Delete or detach `backend/app/api/routes/workflows.py` auto-tailor routes
- Remove legacy router specs and manifest paths from `backend/app/platform/apps/fastapi.py` and `builtin.py`
- Remove legacy worker dispatch branches only when no enabled application references them
- Create `backend/tests/integration/test_no_legacy_specialist_routes.py`

### RED

First run and record all Task 5 tests plus a migration dry run against a disposable database. Then add a route-table test asserting these paths are absent:

- `/api/v1/analysis/**`
- `/api/v1/nexus/**`
- `/api/v1/resumegen/**`
- `/api/v1/workflows/auto-tailor/**`

and v2 paths remain present.

Expected before removal: the absence test fails.

### GREEN

Remove router registration and dead legacy imports. Delete implementation files only after `rg` proves no non-test references. Preserve trustworthy legacy database records; this phase does not destructively drop old tables. Data migration/backfill is a separate reviewed operational change.

Run:

```bash
cd backend
PYTHONPATH=. /home/gopal/.local/bin/uv run --isolated --with pytest --with pytest-asyncio --with pydantic==2.11.5 --with pydantic-settings==2.1.0 --with sqlalchemy --with fastapi==0.115.12 --with httpx==0.25.2 --with pandas --with numpy --with scipy pytest tests/platform tests/studios/data_analyst tests/studios/career tests/integration/test_specialist_v2_cutover.py tests/integration/test_no_legacy_specialist_routes.py -q
```

Also run `python -m compileall -q app/platform app/studios`, `git diff --check`, and a changed-path audit.

### Commit

```bash
git add -A backend/app/api/routes backend/app/platform/apps backend/tests/integration
git commit -m "refactor(platform): retire legacy specialist backends"
```

## Final backend acceptance gate

- Fresh database migration succeeds and a second run is a safe no-op or produces the documented already-applied result.
- Owner A cannot infer or access any owner B identifier across both APIs.
- Repeated idempotent analysis starts do not duplicate runs or computations.
- Stale artifact revisions and stale approvals reject atomically.
- Every Data Analyst number resolves to persisted computation evidence.
- Every publishable Career assertion resolves to a verified persisted claim and a registered deterministic transformation.
- Cancellation cannot later publish a successful artifact.
- No legacy specialist route is registered.
- Full platform, Data Analyst, Career, API, integration, compile, and diff checks pass from the integrated branch.

The frontend replacement (`/analysis` client contracts and `/career` workspace) starts only after this backend gate is green and receives its own TDD plan.
