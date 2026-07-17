# Career Studio V2 Core TDD Report

**Branch:** `career-studio-v2-core`
**Worktree:** `/home/gopal/Professional_Grade_RAG/.worktrees/career-studio-v2`
**Plan commit after final rebase:** `dfa8296 docs: plan career studio v2 core`

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

## Pre-review Verification

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
git diff --name-only 7d01024^..HEAD
```

Observed: the residue scan and whitespace check produced no findings. Every committed path is within the assigned plan, Career Studio application/test packages, or SDD report ownership boundary.

## Design Self-Review

- **Sections 1-5 — evidence and shared contracts:** Career domain code depends inward on the existing platform runtime, evidence status, approval, and quality contracts. Platform code remains unchanged. Result and validation envelopes use `AIResult`, `EvidenceReference`, `QualityMetadata`, and critical `ValidationIssue` records.
- **Section 7.2 — canonical evidence graph:** Claims are typed atomic subject/predicate/object records with one or more exact source spans, temporal scope, context, relationships, verification status, confidence, verifier identity, canonical IDs, deep freezing, and JSON serialization tests.
- **Section 7.3 — role requirements:** Requirements retain required/preferred priority, typed category, description, exact job source span, confidence, and finite positive weight. They are never reduced to a keyword bag.
- **Section 7.4 — matching:** All six bounded score components are retained. SciPy maximum-weight bipartite assignment uses sorted identifiers and dummy unmatched columns, prevents claim reuse, weights the objective by requirement importance, and exposes mandatory/preferred coverage ranges, categorical bands, uncertain matches, transferable matches, truthful gaps, and selected evidence.
- **Sections 7.5-7.6 — drafting and truth:** Every bullet retains claim IDs, transformation, typed asserted facts, supported added keywords, and before/after text. Transformation labels are audit data, not publication authority. The deterministic core publication registry contains only exact-span `VERBATIM`; compressed, combined, reordered, and rephrased bullets abstain as `unsupported-transformation` until a structured renderer is registered and tested. Independent prose, date, metric scalar/unit/measure/context, compatibility, verification, and exact-span lineage checks remain defense in depth. Currency and percent symbols normalize to their typed unit families without weakening metric measure/context binding.
- **Section 9 — deterministic failure handling:** The service performs no I/O or model calls. Critical truth failures transition the run to failed while preserving match coverage separately; meaningful user decisions transition to awaiting input.
- **Section 11 — release gates:** Tests witness zero double-counting, deterministic ties, fabricated metric rejection, typed fact rejection, approval binding, and claim-level draft provenance. ATS layout and artifact round-trip gates are outside this core-only assignment.
- **Sections 14-15 — TDD vertical slice:** Nine witnessed RED/GREEN cycles cover claims/requirements, matching, drafting/truth, workflow approvals, self-review, two independent adversarial reviews, and hardened-runtime integration. The final path is claim graph → typed requirements → weighted match → constrained draft → truth validation → approval state.

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

### Cycle 7 RED — hardened runtime failure categorization after rebase

After rebasing locally onto `specialist-studios-v2` commit `b337298`, the shared runtime requires failed transitions to carry a categorized failure code.

Command:

```bash
UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_service.py::test_no_selected_evidence_abstains_without_requesting_final_approval -q
```

Observed expected failure:

```text
E   app.platform.runtime.contracts.InvalidRunTransition: failed transition requires a failure_code
1 failed in 18.15s
```

The Career Specialist truth-abstention path still used the older runtime call shape and could not create a valid failed run under the hardened lifecycle invariants.

### Cycle 7 GREEN — hardened runtime failure categorization after rebase

Command:

```bash
UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_service.py::test_no_selected_evidence_abstains_without_requesting_final_approval -q
```

Observed:

```text
.                                                                        [100%]
1 passed in 2.22s
```

The truth-validation abstention now passes `failure_code="validation-error"` directly to the shared transition function, and the service regression asserts the categorized failure on the returned run.

### Cycle 8 RED — monotonic approval resume after rebase

Command:

```bash
UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career tests/platform -q --junitxml=/tmp/career-post-rebase.xml
```

Observed expected integration failures:

```text
FAILED test_approved_resume_succeeds_with_end_to_end_provenance - InvalidRunTransition: run progress cannot move backwards
FAILED test_final_approval_must_match_run_draft_owner_and_evidence - expected approval mismatch, got progress transition failure
2 failed, 77 passed in 6.55s
```

The pre-hardening resume path explicitly reset final-approval progress from `0.9` to `0.5`, violating the rebased runtime's monotonic progress invariant before approval checks could run.

### Cycle 8 GREEN — monotonic approval resume after rebase

Command:

```bash
UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_service.py::test_approved_resume_succeeds_with_end_to_end_provenance tests/studios/career/test_service.py::test_final_approval_must_match_run_draft_owner_and_evidence -q
```

Observed:

```text
..                                                                       [100%]
2 passed in 1.69s
```

The resume transition now preserves the awaiting run's existing progress while updating state and step, allowing exact approval validation and successful publication to proceed under the hardened runtime.

## Final Post-review and Post-rebase Verification

Command:

```bash
UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career tests/platform -q --junitxml=/tmp/career-post-rebase-green.xml
```

Observed:

```text
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 1.91s
```

This final combined run includes 46 owned Career Studio tests and 33 rebased shared platform contract tests.

### Cycle 9 RED — deterministic publication boundary and unit aliases

Command (from the worktree root):

```bash
PYTHONPATH=backend UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest backend/tests/studios/career/test_truth_guardian.py -q -k 'negation_reorder or metric_direction_swap or normalized_unit_aliases or unregistered_synonym'
```

Observed expected failures:

```text
FAILED test_negation_reorder_cannot_publish_from_same_source_tokens
FAILED test_metric_direction_swap_cannot_publish
FAILED test_verbatim_metric_accepts_normalized_unit_aliases[$20 revenue-USD-revenue]
FAILED test_verbatim_metric_accepts_normalized_unit_aliases[€20 revenue-EUR-revenue]
FAILED test_verbatim_metric_accepts_normalized_unit_aliases[₹20 revenue-INR-revenue]
FAILED test_verbatim_metric_accepts_normalized_unit_aliases[20% throughput-percent-throughput]
FAILED test_unregistered_synonym_rephrase_is_explicitly_non_publishable
7 failed, 17 deselected in 22.92s
```

The failures reproduce the release blockers: token membership alone accepted a negation reversal and a metric-direction reversal; canonical unit names did not recognize symbol aliases; and a rejected synonym rephrase lacked the explicit `unsupported-transformation` classification required by the intentionally limited publication contract.

### Cycle 9 GREEN — deterministic publication boundary and unit aliases

Commands:

```bash
PYTHONPATH=backend UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest backend/tests/studios/career/test_truth_guardian.py -q -k 'negation_reorder or metric_direction_swap or normalized_unit_aliases or unregistered_synonym'
PYTHONPATH=backend UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest backend/tests/studios/career -q --junitxml=/tmp/career-second-review-green.xml
```

Observed:

```text
.......                                                                  [100%]
7 passed, 17 deselected in 1.91s

.....................................................                    [100%]
53 passed in 3.68s
```

Publication now permits only transformations in the explicit registry, which contains exact-span `VERBATIM` for this deterministic slice. Negation reordering, outcome-direction changes, arbitrary combination/rephrase, and unregistered synonyms therefore abstain with `unsupported-transformation`; the initial drafter/service path is unchanged because it already renders exact source spans. Typed units accept percent, USD, EUR, and INR word/symbol aliases while retaining exact metric scalar and measure checks.

## Final Second-review Integration Verification

The branch was rebased cleanly onto the current local `specialist-studios-v2` integration head `8bd2724`, which contains Data Analyst head `f6d05f0` plus the committed backend cutover plan.

Combined shared-platform and specialist tests:

```bash
PYTHONPATH=backend UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with pandas --with numpy --with scipy python -m pytest backend/tests/platform backend/tests/studios/data_analyst backend/tests/studios/career -q
```

Observed:

```text
........................................................................ [ 52%]
..................................................................       [100%]
138 passed in 52.90s
```

Both specialist packages compile:

```bash
PYTHONPATH=backend UV_CACHE_DIR=/tmp/data-analyst-v2-uv-cache UV_OFFLINE=1 /home/gopal/.local/bin/uv run --isolated --with pydantic==2.11.5 --with pandas --with numpy --with scipy python -m compileall -q backend/app/studios/data_analyst backend/app/studios/career
```

Observed: exit code `0` with no compiler diagnostics.
