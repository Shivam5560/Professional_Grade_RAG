# Career Studio V2 Core TDD Report

**Branch:** `career-studio-v2-core`  
**Worktree:** `/home/gopal/Professional_Grade_RAG/.worktrees/career-studio-v2`  
**Plan commit:** `cdcb3dd docs: plan career studio v2 core`

## Baseline

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/platform -q
```

Observed:

```text
....................                                                     [100%]
20 passed in 0.44s
```

## TDD Cycles

### Cycle 1 RED — immutable claims and typed requirements

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_claims_requirements.py -q
```

Observed expected failure:

```text
E   ModuleNotFoundError: No module named 'app.studios'
1 error in 0.39s
```

The test suite could not collect because the new Career Studio domain package had not been implemented.

### Cycle 1 GREEN — immutable claims and typed requirements

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_claims_requirements.py -q
```

Observed:

```text
...........                                                              [100%]
11 passed in 0.64s
```

### Cycle 2 RED — bounded scoring and one-to-one matching

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_matching.py -q
```

Observed expected failure:

```text
E   ImportError: cannot import name 'CoverageBand' from 'app.studios.career.domain'
1 error in 0.99s
```

The test suite could not collect because score, match, and calibrated coverage contracts had not been implemented.

### Cycle 2 GREEN — bounded scoring and one-to-one matching

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_matching.py -q -rA
```

Observed:

```text
............                                                             [100%]
12 passed in 29.38s
```

The passing cases include bounded component validation, preserved score breakdowns, no claim double-counting, deterministic tie behavior across input order, weighted coverage ranges, truthful unmatched requirements, inferred-evidence rejection, and edge integrity checks.

### Cycle 3 RED — evidence-constrained drafting and Truth Guardian

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_truth_guardian.py -q
```

Observed expected failure:

```text
E   ImportError: cannot import name 'AddedKeyword' from 'app.studios.career.domain'
1 error in 1.24s
```

The adversarial suite could not collect because provenance-carrying draft contracts and the Truth Guardian had not been implemented.

### Cycle 3 GREEN — evidence-constrained drafting and Truth Guardian

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_truth_guardian.py -q
```

Observed:

```text
............                                                             [100%]
12 passed in 0.93s
```

The passing adversarial cases cover verbatim provenance, fabricated and upward-rounded metrics (including metrics omitted from structured facts), incompatible employer/project and temporal combinations, supported keywords, inferred claims, missing/unknown provenance, and typed employer/title/date/skill/degree additions.

### Cycle 4 RED — approval-gated Career Specialist service

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_service.py -q
```

Observed expected failure:

```text
E   ModuleNotFoundError: No module named 'app.studios.career.workflow'
1 error in 5.03s
```

The workflow suite could not collect because the Career Specialist service and approval-gated state composition had not been implemented.

### Cycle 4 GREEN — approval-gated Career Specialist service

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_service.py -q
```

Observed:

```text
.....                                                                    [100%]
5 passed in 1.45s
```

The passing workflow cases cover inferred-claim review, final-resume approval, exact approval binding to run/draft/owner/evidence, publication-ready provenance resolution, and critical truth abstention when no evidence can support a draft.

### Cycle 5 RED — transformation history self-review regression

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_truth_guardian.py::test_missing_before_text_abstains_as_missing_provenance -q
```

Observed expected failure:

```text
E       AssertionError: assert ResumeDraft(...) is None
1 failed in 1.99s
```

Self-review showed that an otherwise supported rephrased bullet could omit its required before-text transformation history without abstaining.

### Cycle 5 GREEN — transformation history self-review regression

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_truth_guardian.py::test_missing_before_text_abstains_as_missing_provenance -q
```

Observed:

```text
.                                                                        [100%]
1 passed in 1.74s
```

## Final Verification

Full owned test directory:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career -q
```

Observed:

```text
.........................................                                [100%]
41 passed in 1.31s
```

Shared platform contract regression:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/platform -q
```

Observed:

```text
....................                                                     [100%]
20 passed in 0.51s
```

Quality and ownership checks:

```bash
rg -n 'TO''DO|TB''D|FIX''ME|print\(|breakpoint\(' backend/app/studios/career backend/tests/studios/career .superpowers/sdd/career-studio-v2-report.md
git diff --check
git diff --name-only cdcb3dd^..HEAD
```

Observed: the residue scan and whitespace check produced no findings. Every committed path is within the assigned plan, Career Studio application/test packages, or SDD report ownership boundary.

## Design Self-Review

- **Sections 1-5 — evidence and shared contracts:** Career domain code depends inward on the existing platform runtime, evidence status, approval, and quality contracts. Platform code remains unchanged. Result and validation envelopes use `AIResult`, `EvidenceReference`, `QualityMetadata`, and critical `ValidationIssue` records.
- **Section 7.2 — canonical evidence graph:** Claims are typed atomic subject/predicate/object records with one or more exact source spans, temporal scope, context, relationships, verification status, confidence, verifier identity, canonical IDs, deep freezing, and JSON serialization tests.
- **Section 7.3 — role requirements:** Requirements retain required/preferred priority, typed category, description, exact job source span, confidence, and finite positive weight. They are never reduced to a keyword bag.
- **Section 7.4 — matching:** All six bounded score components are retained. SciPy maximum-weight bipartite assignment uses sorted identifiers and dummy unmatched columns, prevents claim reuse, weights the objective by requirement importance, and exposes mandatory/preferred coverage ranges, categorical bands, uncertain matches, transferable matches, truthful gaps, and selected evidence.
- **Sections 7.5-7.6 — drafting and truth:** Every bullet retains claim IDs, transformation, typed asserted facts, supported added keywords, and before/after text. Combination requires shared employer/project context and overlapping time. Numeric text and metric facts must match exactly; unsupported typed facts, keywords, non-verified publication claims, incompatible combinations, and missing lineage are critical abstentions.
- **Section 9 — deterministic failure handling:** The service performs no I/O or model calls. Critical truth failures transition the run to failed while preserving match coverage separately; meaningful user decisions transition to awaiting input.
- **Section 11 — release gates:** Tests witness zero double-counting, deterministic ties, fabricated metric rejection, typed fact rejection, approval binding, and claim-level draft provenance. ATS layout and artifact round-trip gates are outside this core-only assignment.
- **Sections 14-15 — TDD vertical slice:** Five witnessed RED/GREEN cycles cover claims/requirements, matching, drafting/truth, workflow approvals, and a self-review regression. The final path is claim graph → typed requirements → weighted match → constrained draft → truth validation → approval state.

## Scope and Integration Notes

- Composite evidence reuse is intentionally absent from this first slice; every atomic claim is one-to-one, which satisfies the stricter no-double-counting rule.
- Persistence, APIs, source extraction, ATS layout, artifact rendering, frontend, interview coaching, and cover letters remain excluded by the assigned delivery boundary.
- The optimizer directly imports SciPy as explicitly allowed. Adding SciPy as a direct production dependency is outside the strictly owned paths; the isolated verification command supplies it explicitly.

### Cycle 6 RED — independent Truth Guardian adversarial review

Commands:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_claims_requirements.py::test_metric_claim_requires_typed_unit_and_measure tests/studios/career/test_truth_guardian.py::test_raw_prose_assertions_are_reconciled_without_trusting_fact_metadata tests/studios/career/test_truth_guardian.py::test_metric_scalar_cannot_move_between_unit_measure_and_context tests/studios/career/test_truth_guardian.py::test_evidence_references_exact_used_span_with_deterministic_deduplication tests/studios/career/test_truth_guardian.py::test_long_used_source_span_retains_locator_without_snippet_overflow -q -rA
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_truth_guardian.py::test_evidence_references_exact_used_span_with_deterministic_deduplication -q
```

Observed expected failures:

```text
FAILED test_metric_claim_requires_typed_unit_and_measure - DID NOT RAISE
FAILED test_raw_prose_assertions_are_reconciled_without_trusting_fact_metadata - missing unsupported prose/date issues
FAILED test_metric_scalar_cannot_move_between_unit_measure_and_context - draft did not abstain
FAILED test_long_used_source_span_retains_locator_without_snippet_overflow - EvidenceReference snippet exceeds 1000 characters
4 failed, 1 passed in 11.05s

FAILED test_evidence_references_exact_used_span_with_deterministic_deduplication - expected project:second, got skills:first
1 failed in 1.72s
```

The failures confirm four context-loss defects: caller metadata was trusted for nonnumeric prose, metric values lost unit/measure binding, claim-level evidence hardcoded the first span, and evidence snippets were not bounded.

### Cycle 6 GREEN — independent Truth Guardian adversarial review

Commands used an isolated, offline uv environment backed by the sandbox-writable shared cache at `/tmp/data-analyst-v2-uv-cache` after home-cache escalation became unavailable:

```bash
UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_claims_requirements.py::test_metric_claim_requires_typed_unit_and_measure tests/studios/career/test_truth_guardian.py::test_raw_prose_assertions_are_reconciled_without_trusting_fact_metadata tests/studios/career/test_truth_guardian.py::test_metric_scalar_cannot_move_between_unit_measure_and_context tests/studios/career/test_truth_guardian.py::test_evidence_references_exact_used_span_with_deterministic_deduplication tests/studios/career/test_truth_guardian.py::test_long_used_source_span_retains_locator_without_snippet_overflow -q --junitxml=/tmp/career-review-green.xml
UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career -q --junitxml=/tmp/career-review-full.xml
```

Observed:

```text
.....                                                                    [100%]
5 passed in 1.91s

..............................................                           [100%]
46 passed in 1.89s
```

Truth Guardian now uses a conservative independent prose-token policy, distinguishes unsupported dates, binds numeric mentions to metric scalar/unit/measure and the exact cited claim context, resolves evidence from the exact before-text span, deduplicates deterministically, and safely bounds evidence snippets.
