# Data Analyst V2 Core Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, evidence-first Data Analyst core that profiles a pandas dataset, creates and executes a registered DAG plan, verifies computation-linked claims, and returns a successful shared-runtime result without an LLM or persistence.

**Architecture:** The new `app.studios.data_analyst` package is a domain-only vertical slice. Frozen Pydantic contracts define profiles, method plans, computation records, and claims; pure modules implement profiling, planning, registered execution, claim verification, and one orchestration service. The package depends only on pandas, NumPy, SciPy, Pydantic, and the existing public `app.platform` contracts.

**Tech Stack:** Python 3.11+, Pydantic 2.11.5, pandas, NumPy, SciPy, pytest

## Global Constraints

- Work only under `backend/app/studios/data_analyst/**`, `backend/tests/studios/data_analyst/**`, this plan, and `.superpowers/sdd/data-analyst-v2-report.md`.
- Do not modify shared platform contracts, legacy analysis packages, persistence, APIs, frontend code, or Career Studio files.
- All public domain records are frozen and serialize with `model_dump(mode="json")`.
- Dataset fingerprinting, method planning, execution outputs, evidence IDs, and output digests are deterministic.
- The profiler never mutates its input DataFrame.
- Plans contain unique step IDs, only registered method/version pairs, and an acyclic dependency graph.
- The initial registry is exactly `descriptive-summary`, `categorical-frequency`, `pearson-correlation`, and `spearman-correlation`, versioned independently behind registry version `1.0.0`.
- Profiling and descriptive analysis are always performed. Correlation is added only for a relationship intent with two usable numeric columns; Pearson is selected for low-skew inputs and Spearman otherwise.
- Every returned claim has an evidence ID and value path that resolves to the exact value in an immutable computation record.
- Association evidence cannot support causal wording or a non-association language class.
- No model provider, network call, database session, FastAPI router, or mutable global service is introduced.
- Execute every behavior through a witnessed RED test followed by the smallest GREEN implementation, and copy the commands/results into `.superpowers/sdd/data-analyst-v2-report.md`.

---

## File Structure

| File | Responsibility |
|---|---|
| `backend/app/studios/data_analyst/domain/json_values.py` | Deep-freeze/thaw JSON payloads and canonical SHA-256 digests |
| `backend/app/studios/data_analyst/domain/contracts.py` | Frozen profile, intent, method, DAG, computation, claim, and service-result contracts |
| `backend/app/studios/data_analyst/domain/__init__.py` | Public domain exports |
| `backend/app/studios/data_analyst/profiling.py` | Deterministic fingerprinting, semantic inference, and non-mutating profiling |
| `backend/app/studios/data_analyst/registry.py` | Versioned initial method registry and plan validation |
| `backend/app/studios/data_analyst/planning.py` | Deterministic intent parsing and registered DAG construction |
| `backend/app/studios/data_analyst/execution.py` | Registered pandas/SciPy method execution and computation evidence construction |
| `backend/app/studios/data_analyst/claims.py` | Claim synthesis, evidence-path resolution, and analytical verification |
| `backend/app/studios/data_analyst/service.py` | Queued-to-succeeded orchestration and verified `AIResult` assembly |
| `backend/app/studios/data_analyst/__init__.py` | Stable public package exports |
| `backend/tests/studios/data_analyst/test_contracts.py` | Frozen/JSON-safe contracts and invalid DAG cases |
| `backend/tests/studios/data_analyst/test_profiling.py` | Fingerprint, type inference, statistics, and immutability tests |
| `backend/tests/studios/data_analyst/test_planning.py` | Registry failures and deterministic method-choice tests |
| `backend/tests/studios/data_analyst/test_execution.py` | Real descriptive/frequency/correlation computation and evidence tests |
| `backend/tests/studios/data_analyst/test_claims.py` | Evidence resolution, unsupported values, and causal rejection tests |
| `backend/tests/studios/data_analyst/test_service.py` | End-to-end run state and evidence-resolution acceptance test |

### Task 1: Frozen Domain Contracts and Canonical JSON

**Files:**
- Create: `backend/app/studios/data_analyst/domain/json_values.py`
- Create: `backend/app/studios/data_analyst/domain/contracts.py`
- Create: `backend/app/studios/data_analyst/domain/__init__.py`
- Create: `backend/tests/studios/data_analyst/test_contracts.py`

**Interfaces:**
- Produces: `canonical_digest(value) -> str`, `ColumnSemanticType`, `ColumnProfile`, `DatasetProfile`, `AnalysisIntent`, `MethodDefinition`, `PlanStep`, `AnalysisPlan`, `AssumptionResult`, `ComputationRecord`, `EvidenceLink`, `FindingClaim`, `ClaimVerification`, `AnalysisOutput`, and `DataAnalystRunResult`.
- `AnalysisPlan` validates unique step IDs, existing dependency IDs, no self-dependencies, and no dependency cycles at construction.

- [ ] **Step 1: Write failing contract tests**

```python
def test_analysis_plan_rejects_duplicate_and_cyclic_steps(method_steps):
    with pytest.raises(ValidationError, match="unique"):
        AnalysisPlan(id="plan", dataset_snapshot_id="ds", registry_version="1.0.0", steps=(method_steps[0], method_steps[0]))
    cyclic = (
        method_steps[0].model_copy(update={"id": "a", "prerequisite_step_ids": ("b",)}),
        method_steps[1].model_copy(update={"id": "b", "prerequisite_step_ids": ("a",)}),
    )
    with pytest.raises(ValidationError, match="acyclic"):
        AnalysisPlan(id="plan", dataset_snapshot_id="ds", registry_version="1.0.0", steps=cyclic)


def test_nested_payloads_are_frozen_and_json_safe(computation_record):
    with pytest.raises(TypeError):
        computation_record.output["row_count"] = 9
    assert json.dumps(computation_record.model_dump(mode="json"), allow_nan=False)
```

- [ ] **Step 2: Verify RED**

Run: `cd backend && PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst/test_contracts.py -q`

Expected: collection fails because `app.studios.data_analyst` does not exist.

- [ ] **Step 3: Implement the minimal immutable contracts**

Use `ConfigDict(frozen=True, validate_default=True)`, tuples instead of lists, mapping proxies for payloads, field serializers that thaw mappings for JSON, and a depth-first DAG validator. Restrict identifiers and semantic versions with the same kebab-case/semver patterns used by the shared contracts. Represent evidence paths as dot-separated mapping keys/list indexes beginning with `output`.

- [ ] **Step 4: Verify GREEN**

Run the command from Step 2.

Expected: all contract tests pass with no warnings.

- [ ] **Step 5: Commit**

```bash
git add backend/app/studios/data_analyst/domain backend/tests/studios/data_analyst/test_contracts.py .superpowers/sdd/data-analyst-v2-report.md
git commit -m "feat(data-analyst): add immutable core contracts"
```

### Task 2: Deterministic Dataset Fingerprinting and Profiling

**Files:**
- Create: `backend/app/studios/data_analyst/profiling.py`
- Create: `backend/tests/studios/data_analyst/test_profiling.py`

**Interfaces:**
- Produces: `fingerprint_dataframe(frame: pd.DataFrame) -> str` and `profile_dataframe(frame: pd.DataFrame) -> DatasetProfile`.
- Type precedence: boolean dtype, datetime dtype, numeric dtype, boolean-like objects, datetime-like objects, identifier-name plus uniqueness, low-cardinality categorical, then text.
- Numeric skewness is emitted only for at least three non-null values and at least two distinct values.

- [ ] **Step 1: Write failing profiler tests**

```python
def test_fingerprint_is_deterministic_sensitive_and_non_mutating():
    frame = sample_frame()
    original = frame.copy(deep=True)
    first = fingerprint_dataframe(frame)
    assert first == fingerprint_dataframe(frame.copy(deep=True))
    changed = frame.copy(deep=True)
    changed.loc[0, "revenue"] += 1
    assert first != fingerprint_dataframe(changed)
    pd.testing.assert_frame_equal(frame, original)


def test_profile_infers_types_and_quality_statistics():
    profile = profile_dataframe(sample_frame())
    by_name = {column.name: column for column in profile.columns}
    assert profile.row_count == 6 and profile.column_count == 7
    assert by_name["revenue"].semantic_type is ColumnSemanticType.NUMERIC
    assert by_name["region"].semantic_type is ColumnSemanticType.CATEGORICAL
    assert by_name["event_at"].semantic_type is ColumnSemanticType.DATETIME
    assert by_name["active"].semantic_type is ColumnSemanticType.BOOLEAN
    assert by_name["customer_id"].semantic_type is ColumnSemanticType.IDENTIFIER
    assert by_name["notes"].semantic_type is ColumnSemanticType.TEXT
    assert by_name["revenue"].missing_count == 1
    assert by_name["revenue"].skewness is not None
```

- [ ] **Step 2: Verify RED**

Run: `cd backend && PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst/test_profiling.py -q`

Expected: collection fails because `profiling` is missing.

- [ ] **Step 3: Implement canonical fingerprinting and the profiler**

Normalize DataFrame schema, index, and scalar values into canonical JSON. Encode missing, non-finite, datetime, date, time, timedelta, bytes, NumPy scalar, and ordinary JSON scalar values explicitly; reject unsupported values instead of using unstable object representations. Copy no input data for mutation and never assign into the caller's frame.

- [ ] **Step 4: Verify GREEN**

Run the command from Step 2.

Expected: profiler tests pass with no warnings.

- [ ] **Step 5: Commit**

```bash
git add backend/app/studios/data_analyst/profiling.py backend/tests/studios/data_analyst/test_profiling.py .superpowers/sdd/data-analyst-v2-report.md
git commit -m "feat(data-analyst): add deterministic dataset profiling"
```

### Task 3: Versioned Method Registry and DAG Planner

**Files:**
- Create: `backend/app/studios/data_analyst/registry.py`
- Create: `backend/app/studios/data_analyst/planning.py`
- Create: `backend/tests/studios/data_analyst/test_planning.py`

**Interfaces:**
- Produces: `MethodRegistry.initial()`, `MethodRegistry.get(method_id, version=None)`, `MethodRegistry.validate_plan(plan)`, `parse_intent(question, context=None)`, and `build_analysis_plan(profile, intent, registry=None)`.
- Planner step IDs and plan ID are deterministic content-derived identifiers.

- [ ] **Step 1: Write failing registry and planning tests**

```python
def test_registry_rejects_unknown_method_and_version(profile):
    registry = MethodRegistry.initial()
    bad = build_analysis_plan(profile, parse_intent("summarize"), registry)
    bad_step = bad.steps[0].model_copy(update={"method_id": "invented-method"})
    with pytest.raises(UnregisteredMethodError):
        registry.validate_plan(bad.model_copy(update={"steps": (bad_step,)}))


@pytest.mark.parametrize(
    ("values", "expected"),
    [([1, 2, 3, 4, 5, 6], "pearson-correlation"), ([1, 1, 1, 1, 1, 100], "spearman-correlation")],
)
def test_planner_selects_correlation_from_skew_not_model_guess(values, expected):
    profile = profile_dataframe(pd.DataFrame({"x": values, "y": [2, 4, 6, 8, 10, 12]}))
    plan = build_analysis_plan(profile, parse_intent("How are x and y related?"))
    assert plan.steps[0].method_id == "descriptive-summary"
    assert expected in {step.method_id for step in plan.steps}
    correlation = next(step for step in plan.steps if step.method_id == expected)
    assert correlation.prerequisite_step_ids == ("descriptive",)
    assert correlation.assumptions and correlation.rationale
```

- [ ] **Step 2: Verify RED**

Run: `cd backend && PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst/test_planning.py -q`

Expected: collection fails because registry/planning modules are missing.

- [ ] **Step 3: Implement the four-method registry and deterministic planner**

Declare supported semantic types, sample minima, required assumptions, deterministic defaults, cost class, output description, limitations, and semantic implementation version for each method. Always add `descriptive-summary`; add `categorical-frequency` when categorical columns exist; add exactly one correlation step for relationship intent and two or more numeric columns. Select Pearson only when selected columns have finite skewness with absolute value at most `1.0`; otherwise select Spearman and record the reason.

- [ ] **Step 4: Verify GREEN**

Run the command from Step 2.

Expected: planning tests pass with no warnings.

- [ ] **Step 5: Commit**

```bash
git add backend/app/studios/data_analyst/registry.py backend/app/studios/data_analyst/planning.py backend/tests/studios/data_analyst/test_planning.py .superpowers/sdd/data-analyst-v2-report.md
git commit -m "feat(data-analyst): add registered DAG planning"
```

### Task 4: Registered Method Execution and Computation Evidence

**Files:**
- Create: `backend/app/studios/data_analyst/execution.py`
- Create: `backend/tests/studios/data_analyst/test_execution.py`

**Interfaces:**
- Produces: `execute_analysis_plan(frame, profile, plan, *, run_id, registry=None) -> tuple[ComputationRecord, ...]`.
- Consumes only plans that pass registry validation and whose snapshot fingerprint matches the DataFrame.

- [ ] **Step 1: Write failing execution tests**

```python
def test_executes_real_correlation_with_assumptions_and_evidence():
    frame = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
    profile = profile_dataframe(frame)
    plan = build_analysis_plan(profile, parse_intent("relationship between x and y"))
    records = execute_analysis_plan(frame, profile, plan, run_id="run-1")
    correlation = next(record for record in records if record.method_id == "pearson-correlation")
    pair = correlation.output["pairs"][0]
    assert pair["method"] == "pearson"
    assert pair["columns"] == ("x", "y")
    assert pair["coefficient"] == pytest.approx(1.0)
    assert pair["p_value"] == pytest.approx(0.0)
    assert pair["sample_count"] == 5
    assert pair["assumption_results"]["non-constant"] == "pass"
    assert correlation.evidence.output_digest == correlation.output_digest
    assert len(json.dumps(correlation.model_dump(mode="json"), allow_nan=False)) > 0


def test_execution_digest_is_canonical_and_repeatable(frame, profile, plan):
    first = execute_analysis_plan(frame, profile, plan, run_id="run-1")
    second = execute_analysis_plan(frame.copy(deep=True), profile, plan, run_id="run-1")
    assert [record.output_digest for record in first] == [record.output_digest for record in second]
    assert [record.evidence.model_dump(mode="json") for record in first] == [record.evidence.model_dump(mode="json") for record in second]
```

- [ ] **Step 2: Verify RED**

Run: `cd backend && PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst/test_execution.py -q`

Expected: collection fails because execution is missing.

- [ ] **Step 3: Implement registered execution**

Topologically execute plan steps after registry and fingerprint checks. Descriptive output includes row/column counts and per-column missingness/uniqueness plus numeric count/mean/standard deviation/minimum/median/maximum. Frequency output contains stable value/count/fraction rows. Correlation output contains method, ordered pair, finite coefficient or `None`, finite p-value or `None`, sample count, and per-pair assumption statuses. Build `ComputationEvidence` with the plan parameters, method version, assumption map, deterministic output digest, and no artifact IDs.

- [ ] **Step 4: Verify GREEN**

Run the command from Step 2.

Expected: execution tests pass with no SciPy warnings.

- [ ] **Step 5: Commit**

```bash
git add backend/app/studios/data_analyst/execution.py backend/tests/studios/data_analyst/test_execution.py .superpowers/sdd/data-analyst-v2-report.md
git commit -m "feat(data-analyst): execute registered evidence methods"
```

### Task 5: Evidence-Linked Claim Synthesis and Verification

**Files:**
- Create: `backend/app/studios/data_analyst/claims.py`
- Create: `backend/tests/studios/data_analyst/test_claims.py`

**Interfaces:**
- Produces: `synthesize_claims(records) -> tuple[FindingClaim, ...]`, `resolve_evidence_value(record, path)`, and `verify_claims(claims, records) -> tuple[ClaimVerification, ...]`.

- [ ] **Step 1: Write failing claim tests**

```python
def test_synthesized_claims_resolve_to_exact_computation_values(records):
    claims = synthesize_claims(records)
    checks = verify_claims(claims, records)
    assert claims and all(check.accepted for check in checks)
    for claim in claims:
        link = claim.evidence_links[0]
        record = next(item for item in records if item.evidence.id == link.evidence_id)
        assert resolve_evidence_value(record, link.value_path) == claim.value


def test_verifier_rejects_unsupported_value_and_causal_correlation_claim(correlation_claim, records):
    unsupported = correlation_claim.model_copy(update={"value": 0.12345})
    causal = correlation_claim.model_copy(update={"predicate": "causes an increase in"})
    assert verify_claims((unsupported,), records)[0].accepted is False
    result = verify_claims((causal,), records)[0]
    assert result.accepted is False
    assert "causal-language" in result.issue_codes
```

- [ ] **Step 2: Verify RED**

Run: `cd backend && PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst/test_claims.py -q`

Expected: collection fails because claims is missing.

- [ ] **Step 3: Implement synthesis and verification**

Synthesize dataset row-count, numeric mean, categorical top-frequency, and valid correlation-coefficient claims directly from computation output paths. Resolve mapping keys and tuple indexes without evaluation or attribute access. Reject missing/duplicate evidence IDs, invalid paths, value mismatches, non-association language classes for correlation, and causal terms such as `cause`, `causes`, `caused`, `drives`, `leads to`, `effect`, and `impact` when evidence is association-only.

- [ ] **Step 4: Verify GREEN**

Run the command from Step 2.

Expected: claim tests pass with no warnings.

- [ ] **Step 5: Commit**

```bash
git add backend/app/studios/data_analyst/claims.py backend/tests/studios/data_analyst/test_claims.py .superpowers/sdd/data-analyst-v2-report.md
git commit -m "feat(data-analyst): verify computation-linked claims"
```

### Task 6: End-to-End Data Analyst Specialist Service

**Files:**
- Create: `backend/app/studios/data_analyst/service.py`
- Create: `backend/app/studios/data_analyst/__init__.py`
- Create: `backend/tests/studios/data_analyst/test_service.py`

**Interfaces:**
- Produces: `DataAnalystSpecialist.analyze(frame, question, *, owner_id, run_id, idempotency_key, now, business_context=None) -> DataAnalystRunResult`.
- Returns queued/running/succeeded run history, profile, plan, computation records, computation evidence, and `AIResult[AnalysisOutput]` containing only verified claims.

- [ ] **Step 1: Write the failing end-to-end acceptance test**

```python
def test_specialist_runs_profile_plan_compute_verify_without_llm():
    result = DataAnalystSpecialist().analyze(
        pd.DataFrame({"revenue": [10, 20, 30, 40, 50], "profit": [1, 2, 3, 4, 5], "region": ["n", "s", "n", "s", "n"]}),
        "How are revenue and profit related by region?",
        owner_id=7,
        run_id="run-analysis-1",
        idempotency_key="request-1",
        now=datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc),
    )
    assert tuple(run.state for run in result.run_history) == (
        StudioRunState.QUEUED, StudioRunState.RUNNING, StudioRunState.SUCCEEDED,
    )
    assert result.result.output is not None
    assert result.result.output.claims
    records_by_evidence = {record.evidence.id: record for record in result.computations}
    for claim in result.result.output.claims:
        for link in claim.evidence_links:
            assert link.evidence_id in records_by_evidence
            assert resolve_evidence_value(records_by_evidence[link.evidence_id], link.value_path) == claim.value
    assert {ref.source_id for ref in result.result.evidence} == {
        link.evidence_id for claim in result.result.output.claims for link in claim.evidence_links
    }
    assert result.result.quality.input_tokens == 0
    assert result.result.quality.output_tokens == 0
```

- [ ] **Step 2: Verify RED**

Run: `cd backend && PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst/test_service.py -q`

Expected: collection fails because the specialist service is missing.

- [ ] **Step 3: Implement deterministic orchestration**

Create the queued shared `StudioRun`, transition to running at `profile`, run profile → intent → plan → execution → synthesis → verification, and transition to succeeded at `verified-claims`. Assemble `AIResult` with one deduplicated `EvidenceReference` per evidence link, algorithm versions only, zero tokens/cost, deterministic trace ID, evidence confidence `1.0`, and a passing claim-resolution validation. If internally synthesized claims fail verification, return no publishable output, a critical validation error, and an abstention reason rather than publishing unsupported content.

- [ ] **Step 4: Verify GREEN and the complete owned suite**

Run: `cd backend && PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst/test_service.py -q`

Then run: `cd backend && PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst -q`

Expected: all owned tests pass with no warnings.

- [ ] **Step 5: Self-review and commit**

Review sections 1–6, 9, 11, 14, and 15 of the approved design against the implementation; verify every initial-slice Data Analyst requirement has a test; scan owned files for placeholders, network/model imports, mutable output payloads, and invalid digest handling. Record the review and any deliberately excluded broader-v2 scope in the SDD report.

```bash
git add backend/app/studios/data_analyst backend/tests/studios/data_analyst .superpowers/sdd/data-analyst-v2-report.md
git commit -m "feat(data-analyst): add evidence-first specialist service"
```

### Task 7: Fresh Verification and Branch Handoff

**Files:**
- Modify: `.superpowers/sdd/data-analyst-v2-report.md`

- [ ] **Step 1: Run syntax/import verification**

Run: `cd backend && PYTHONPATH=. uv run --isolated --with pydantic==2.11.5 --with pandas --with numpy --with scipy python -m compileall -q app/studios/data_analyst`

Expected: exit code `0` and no output.

- [ ] **Step 2: Run the full owned test directory from a clean command**

Run: `cd backend && PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst -q`

Expected: exit code `0`, all tests passed, no warnings.

- [ ] **Step 3: Verify ownership and repository state**

Run: `git status --short && git diff --check && git log --oneline --decorate -8`

Expected: only the owned report may remain modified before its final commit; `git diff --check` emits no errors; history contains a separate plan commit and logical implementation commits.

- [ ] **Step 4: Commit the final execution report**

```bash
git add .superpowers/sdd/data-analyst-v2-report.md
git commit -m "docs(data-analyst): record core verification"
```
