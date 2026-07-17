# Data Analyst V2 Core TDD Report

## Scope

Implementation is restricted to the Data Analyst v2 core domain vertical slice. It adds no API, persistence, frontend, legacy-analysis changes, model calls, or network calls.

## Baseline

Command:

```text
cd backend && UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/platform -q
```

Output:

```text
....................                                                     [100%]
20 passed in 0.44s
```

## RED/GREEN Log

### 1. Domain contracts — RED

Command:

```text
cd backend && UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst/test_contracts.py -q
```

Expected failure:

```text
ModuleNotFoundError: No module named 'app.studios'
1 error in 0.42s
```

### 1. Domain contracts — GREEN

```text
.......                                                                  [100%]
7 passed in 0.88s
```

### 2. Dataset profiling — RED

```text
ModuleNotFoundError: No module named 'app.studios.data_analyst.profiling'
1 error in 3.51s
```

### 2. Dataset profiling — GREEN

```text
......                                                                   [100%]
6 passed in 1.28s
```

### 3. Registry and planning — RED

```text
ModuleNotFoundError: No module named 'app.studios.data_analyst.planning'
1 error in 6.69s
```

### 3. Registry and planning — GREEN

```text
........                                                                 [100%]
8 passed in 3.89s
```

### 4. Registered method execution — RED

```text
ModuleNotFoundError: No module named 'app.studios.data_analyst.execution'
1 error in 1.52s
```

### 4. Registered method execution — GREEN

```text
......                                                                   [100%]
6 passed in 6.95s
```

### 5. Claim synthesis and verification — RED

```text
ModuleNotFoundError: No module named 'app.studios.data_analyst.claims'
1 error in 0.89s
```

### 5. Claim synthesis and verification — GREEN

```text
.........                                                                [100%]
9 passed in 2.76s
```

### 6. End-to-end specialist service — RED

```text
ImportError: cannot import name 'DataAnalystSpecialist' from 'app.studios.data_analyst'
1 error in 0.97s
```

### 6. End-to-end specialist service — GREEN

```text
....                                                                     [100%]
4 passed in 9.61s
```

### 7. Review regression: arbitrary column-name evidence paths — RED

Root cause: synthesis interpolated raw column names into dot-delimited locators, and `EvidenceLink` allowed only alphanumeric dot tokens. A valid column named `gross.margin / usd` therefore could not produce a claim.

```text
FAILED tests/studios/data_analyst/test_claims.py::test_claim_paths_support_arbitrary_valid_column_names
String should match pattern '^output(?:\.[A-Za-z0-9_-]+)+$'
1 failed in 2.17s
```

### 8. Review regression: expanded causal overreach vocabulary — RED

```text
5 failed, 5 passed in 4.22s
Missing rejections: results in, responsible for, determines, influences, causal relationship
```

### 7–8. Review regressions — GREEN

```text
...........                                                              [100%]
11 passed in 2.94s
```

### 9. Review regression: executor input-type preflight — RED

```text
ImportError: cannot import name 'MethodPrerequisiteError'
1 error in 4.49s
```

### 9. Executor input-type preflight — GREEN

```text
.                                                                        [100%]
1 passed in 5.26s
```

## Final Verification

Syntax/import compilation:

```text
cd backend && UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache PYTHONPATH=. uv run --isolated --with pydantic==2.11.5 --with pandas --with numpy --with scipy python -m compileall -q app/studios/data_analyst
exit 0
```

Complete owned suite:

```text
cd backend && UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/studios/data_analyst -q
...............................................                          [100%]
47 passed in 3.10s
```

Shared platform compatibility:

```text
cd backend && UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache PYTHONPATH=. uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy pytest tests/platform -q
....................                                                     [100%]
20 passed in 0.23s
```

Repository checks:

```text
git diff --check
exit 0
```

The changed-path audit against `3a6fd55` contains only the assigned plan, `backend/app/studios/data_analyst/**`, `backend/tests/studios/data_analyst/**`, and this report.

## Design Self-Review

- Sections 1–5: the slice consumes only the existing frozen runtime, evidence, and quality contracts; no shared-platform or reverse studio dependency was added.
- Section 6: covered by immutable profiles/intents/methods/plans/computations/claims, deterministic profiling, a four-method registry, DAG and method-input preflight, pandas/SciPy execution, canonical digests, computation evidence, synthesis, and analytical verification.
- Section 9: the in-memory core uses explicit queued → running → succeeded/failed transitions and critically abstains instead of publishing a failed claim. Durable leases/retry/persistence remain outside this core-only assignment.
- Section 11: fixtures verify method choice, assumption diagnostics, deterministic reruns, exact numerical evidence resolution, arbitrary-column locators, and adversarial causal-language rejection.
- Section 14: each production unit and every review regression has a witnessed RED/GREEN cycle above; all output contracts serialize without non-finite JSON values.
- Section 15: the executable path is snapshot/fingerprint → profile → registered plan → computations/evidence → verified `AIResult`, with no LLM or network dependency.

Deliberately excluded as required by the initial core boundary: persistence, APIs, UI, editable-plan endpoints, artifacts/notebooks/reports, broad statistical/ML/time-series catalogs, and durable worker retry/cancellation. No requested core scope is known to be missing.

## Independent Review Fix Pass

The branch was rebased onto hardened shared-platform head `b337298` before this
pass so the regressions exercised the current runtime and evidence invariants.

### Hardened runtime failure transition — RED

The existing failure-path service test first exposed that frozen plan parameters
had to be serialized to JSON containers for the hardened `ComputationEvidence`.
After that compatibility boundary was corrected, the same regression reached the
target runtime failure:

```text
InvalidRunTransition: failed transition requires a failure_code
1 failed
```

### Hardened runtime failure transition — GREEN

`failure_code` is now supplied atomically to `transition_run`; the post-transition
model reconstruction was removed.

```text
1 passed
```

### Exact multi-link resolution and global causal guard — RED

```text
FAILED test_verifier_requires_every_evidence_link_to_support_the_claim_value
FAILED test_verifier_rejects_causal_language_for_descriptive_evidence
2 failed
```

### Exact multi-link resolution and global causal guard — GREEN

Each link must now resolve exactly to the claim value. Causal wording is rejected
for every initial registered method because none of those methods identifies a
causal effect.

```text
1 passed
1 passed
```

### Computation integrity — RED

```text
FAILED test_computation_record_rejects_digest_forged_for_unchanged_output
FAILED test_computation_record_requires_exact_evidence_assumption_results
2 failed
```

### Computation integrity — GREEN

`ComputationRecord` now recomputes its canonical output digest and requires its
evidence assumption map to equal the record's typed assumption results exactly.

```text
1 passed
1 passed
```

### Correlation input preflight — RED

```text
FAILED test_execution_preflights_two_numeric_inputs_for_correlation
1 failed
```

### Correlation input preflight — GREEN

Correlation steps with fewer than two numeric inputs are rejected before method
execution, preventing an empty pair set from producing vacuous PASS assumptions.

```text
1 passed
```

### Review-pass combined verification

```text
........................................................................ [ 84%]
.............                                                            [100%]
85 passed in 6.45s
```

This combined run covers the complete owned Data Analyst suite and the hardened
shared-platform suite.
