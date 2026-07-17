# Career Studio V2 Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a deterministic, evidence-first Career Studio vertical slice from immutable career claims through weighted matching, truth-constrained drafting, validation, and approval-gated publication.

**Architecture:** The studio is a modular package under `app.studios.career` with frozen Pydantic domain contracts at its center. Pure scoring and matching functions consume explicit bounded inputs; drafting and validation resolve every assertion back to claim IDs; the workflow service composes these functions through the existing shared run, approval, evidence, and quality contracts without persistence, APIs, models, or network calls.

**Tech Stack:** Python 3.13, Pydantic 2.11.5, SciPy `linear_sum_assignment`, pytest, existing `app.platform` contracts.

## Global Constraints

- Modify only `backend/app/studios/career/**`, `backend/tests/studios/career/**`, this plan, and `.superpowers/sdd/career-studio-v2-report.md`.
- Use frozen, JSON-serializable Pydantic models; mutable mappings and collections are not accepted in canonical domain payloads.
- Use the existing `StudioRun`, `ApprovalRequest`, `AIResult`, `EvidenceReference`, `QualityMetadata`, and `ValidationIssue` public interfaces without changing shared platform files.
- Perform no LLM, provider, database, filesystem, or network calls from the Career Specialist core.
- Matching is deterministic and one-to-one: one atomic claim can satisfy at most one selected requirement.
- Publication requires verified claims, a critical-error-free Truth Guardian result, and an approved `final-resume` approval request.
- The core publication registry contains only `DraftTransformation.VERBATIM`. Its after text must equal one exact used source span. Other transformation labels remain available for audited draft/review records but must abstain with `unsupported-transformation` until a deterministic structured renderer is separately registered and tested.
- Every production behavior is introduced only after its focused test has failed for the expected missing-behavior reason.
- Record every RED and GREEN command and its observed result in `.superpowers/sdd/career-studio-v2-report.md`.

---

### Task 1: Immutable Career Claims and Typed Role Requirements

**Files:**
- Create: `backend/app/studios/__init__.py`
- Create: `backend/app/studios/career/__init__.py`
- Create: `backend/app/studios/career/domain/__init__.py`
- Create: `backend/app/studios/career/domain/claims.py`
- Create: `backend/app/studios/career/domain/requirements.py`
- Create: `backend/tests/studios/career/__init__.py`
- Create: `backend/tests/studios/career/test_claims_requirements.py`
- Create: `.superpowers/sdd/career-studio-v2-report.md`

**Interfaces:**
- Produces: `SourceSpan`, `TemporalScope`, `ClaimSubject`, `ClaimObject`, `CareerClaim`, `ClaimPredicate`, `ClaimValueKind`, `stable_claim_id`, `RequirementPriority`, `RequirementCategory`, and `RoleRequirement`.
- Consumes: `VerificationStatus` from `app.platform.evidence`.

- [ ] **Step 1: Write failing claim and requirement contract tests**

```python
def test_claim_is_deeply_immutable_and_json_safe():
    claim = make_claim()
    with pytest.raises(ValidationError):
        claim.confidence = 0.1
    with pytest.raises(ValidationError):
        claim.source_spans[0].exact_text = "changed"
    assert json.loads(claim.model_dump_json())["object"]["value"] == "Python"


def test_stable_claim_id_is_independent_of_source_span_input_order():
    assert stable_claim_id(**claim_parts(spans=(SPAN_A, SPAN_B))) == stable_claim_id(
        **claim_parts(spans=(SPAN_B, SPAN_A))
    )


def test_requirement_retains_priority_category_exact_span_confidence_and_weight():
    requirement = RoleRequirement(
        id="req-python",
        priority=RequirementPriority.REQUIRED,
        category=RequirementCategory.SKILL,
        description="Production Python",
        source_span=JOB_SPAN,
        confidence=0.95,
        weight=3.0,
    )
    assert requirement.source_span.exact_text == "Production Python"
    assert requirement.weight == 3.0
```

- [ ] **Step 2: Run the focused contract tests and verify RED**

Run from `backend`:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy pytest tests/studios/career/test_claims_requirements.py -q
```

Expected: collection fails because `app.studios.career.domain` does not exist.

- [ ] **Step 3: Implement minimal frozen domain contracts**

Implement `stable_claim_id` as a SHA-256 digest of canonical JSON containing the typed subject, predicate, object, sorted source spans, temporal scope, context IDs, and sorted related claim IDs. Use a `claim-` prefix and a fixed 24-hex-character digest suffix. Restrict claim object values to finite JSON scalar values and require non-blank source locators and exact text. `CareerClaim.create(...)` computes the ID rather than accepting an unstable caller-generated ID.

Define role requirements as typed entities rather than keywords:

```python
class RequirementPriority(StrEnum):
    REQUIRED = "required"
    PREFERRED = "preferred"


class RequirementCategory(StrEnum):
    SKILL = "skill"
    RESPONSIBILITY = "responsibility"
    OUTCOME = "outcome"
    EXPERIENCE = "experience"
    SENIORITY = "seniority"
    EDUCATION = "education"
    CERTIFICATION = "certification"
    LOCATION = "location"
    WORK_MODE = "work-mode"
    DOMAIN = "domain"
```

Each `RoleRequirement` is frozen and validates a non-blank ID and description, exact source text, confidence in `[0, 1]`, and finite positive weight.

- [ ] **Step 4: Run the contract tests and verify GREEN**

Run the Step 2 command. Expected: all tests pass with no warnings.

- [ ] **Step 5: Commit the domain contracts**

```bash
git add backend/app/studios backend/tests/studios/career .superpowers/sdd/career-studio-v2-report.md
git commit -m "feat(career): add immutable evidence graph contracts"
```

### Task 2: Deterministic Edge Scoring and One-to-One Matching

**Files:**
- Create: `backend/app/studios/career/domain/matching.py`
- Create: `backend/app/studios/career/matching/__init__.py`
- Create: `backend/app/studios/career/matching/scoring.py`
- Create: `backend/app/studios/career/matching/optimizer.py`
- Create: `backend/tests/studios/career/test_matching.py`
- Modify: `backend/app/studios/career/domain/__init__.py`
- Modify: `backend/app/studios/career/__init__.py`
- Modify: `.superpowers/sdd/career-studio-v2-report.md`

**Interfaces:**
- Consumes: `CareerClaim`, `RoleRequirement`, `RequirementPriority`, and `VerificationStatus`.
- Produces: `ScoreComponents`, `CandidateEdge`, `SelectedMatch`, `CoverageBand`, `CoverageSummary`, `CareerMatchResult`, `score_candidate_edge(...)`, and `match_requirements(...)`.

- [ ] **Step 1: Write failing scoring and matching tests**

```python
def test_score_validates_and_preserves_each_component():
    components = ScoreComponents(
        semantic_relevance=0.9,
        evidence_strength=1.0,
        recency=0.8,
        duration_seniority=0.7,
        transferability=0.6,
        specificity=0.9,
    )
    edge = score_candidate_edge(REQUIRED_PYTHON, VERIFIED_PYTHON, components)
    assert edge.components == components
    assert edge.score == pytest.approx(0.86)
    with pytest.raises(ValidationError):
        ScoreComponents(semantic_relevance=1.01, evidence_strength=1, recency=1,
                        duration_seniority=1, transferability=1, specificity=1)


def test_matching_does_not_double_count_one_claim():
    result = match_requirements(
        requirements=(REQ_PYTHON, REQ_APIS),
        claims=(CLAIM_PLATFORM,),
        candidate_edges=(EDGE_PYTHON, EDGE_APIS),
    )
    assert len(result.selected_matches) == 1
    assert len(result.unmatched_requirement_ids) == 1


def test_matching_ties_are_deterministic_across_input_order():
    forward = match_requirements(REQUIREMENTS, CLAIMS, TIED_EDGES)
    reverse = match_requirements(tuple(reversed(REQUIREMENTS)), tuple(reversed(CLAIMS)),
                                 tuple(reversed(TIED_EDGES)))
    assert forward.selected_matches == reverse.selected_matches


def test_coverage_is_weighted_and_uncertainty_is_a_range():
    result = match_requirements(WEIGHTED_REQUIREMENTS, CLAIMS, EDGES)
    assert result.mandatory_coverage.lower_bound == pytest.approx(0.75)
    assert result.mandatory_coverage.upper_bound == pytest.approx(1.0)
    assert result.uncertain_requirement_ids == ("req-uncertain",)
```

- [ ] **Step 2: Run matching tests and verify RED**

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy pytest tests/studios/career/test_matching.py -q
```

Expected: collection fails because matching contracts and functions are absent.

- [ ] **Step 3: Implement bounded scoring with a preserved breakdown**

Use documented fixed component weights summing to one:

```python
COMPONENT_WEIGHTS = {
    "semantic_relevance": 0.35,
    "evidence_strength": 0.20,
    "recency": 0.10,
    "duration_seniority": 0.10,
    "transferability": 0.10,
    "specificity": 0.15,
}
```

`ScoreComponents` rejects non-finite or out-of-range values. `CandidateEdge` retains the exact component object, the deterministic weighted score, requirement ID, claim ID, and a categorical strength band. Do not label the score as a hiring probability.

- [ ] **Step 4: Implement deterministic maximum-weight matching and calibrated coverage**

Sort requirement and claim IDs before constructing the assignment matrix. Optimize `edge.score * requirement.weight` using `scipy.optimize.linear_sum_assignment`, include one zero-weight dummy column per requirement so unsupported requirements remain unmatched, and reject duplicate or dangling candidate edges. Only verified claims are eligible. Use stable row/column ordering as the deterministic tie rule.

Classify selected edges below `0.65` as uncertain. Coverage stores matched weight and total weight, plus lower and upper bounds: the lower bound includes confident matches only, while the upper bound also includes selected uncertain matches. Expose required and preferred coverage separately, selected evidence IDs, unmatched requirements, and uncertain matches.

- [ ] **Step 5: Run matching tests and verify GREEN**

Run the Step 2 command. Expected: all matching tests pass with no warnings.

- [ ] **Step 6: Commit scoring and matching**

```bash
git add backend/app/studios/career backend/tests/studios/career/test_matching.py .superpowers/sdd/career-studio-v2-report.md
git commit -m "feat(career): add deterministic evidence matching"
```

### Task 3: Evidence-Constrained Drafts and Truth Guardian

**Files:**
- Create: `backend/app/studios/career/domain/drafts.py`
- Create: `backend/app/studios/career/writing/__init__.py`
- Create: `backend/app/studios/career/writing/drafter.py`
- Create: `backend/app/studios/career/validation/__init__.py`
- Create: `backend/app/studios/career/validation/truth_guardian.py`
- Create: `backend/tests/studios/career/test_truth_guardian.py`
- Modify: `backend/app/studios/career/domain/__init__.py`
- Modify: `backend/app/studios/career/__init__.py`
- Modify: `.superpowers/sdd/career-studio-v2-report.md`

**Interfaces:**
- Consumes: canonical claims, selected matches, `AIResult`, `EvidenceReference`, `QualityMetadata`, `ValidationIssue`, and `ValidationStatus`.
- Produces: `DraftTransformation`, `AssertedFact`, `AddedKeyword`, `DraftBullet`, `ResumeDraft`, `draft_from_matches(...)`, and `validate_draft(...) -> AIResult[ResumeDraft]`.

- [ ] **Step 1: Write failing draft and adversarial truth tests**

```python
def test_fabricated_or_rounded_up_metric_abstains():
    draft = draft_with_metric(asserted_value=20)
    result = validate_draft(draft, claims=(metric_claim(value=19.6),), for_publication=True)
    assert result.output is None
    assert result.quality.abstention_reason == "career draft failed truth validation"
    assert critical_codes(result) == {"metric-altered"}


def test_incompatible_combination_abstains():
    result = validate_draft(
        combined_draft(CLAIM_EMPLOYER_A_2022, CLAIM_EMPLOYER_B_2024),
        claims=(CLAIM_EMPLOYER_A_2022, CLAIM_EMPLOYER_B_2024),
        for_publication=True,
    )
    assert result.output is None
    assert "incompatible-combination" in critical_codes(result)


def test_supported_keyword_is_accepted_and_resolves_to_claim():
    result = validate_draft(
        draft_with_keyword("Python", support=(PYTHON_CLAIM.id,)),
        claims=(PYTHON_CLAIM,), for_publication=False,
    )
    assert result.output is not None
    assert result.evidence[0].source_id == PYTHON_CLAIM.id


def test_publishable_draft_rejects_inferred_claim_and_missing_provenance():
    result = validate_draft(INFERRED_DRAFT_WITH_MISSING_FACT_LINEAGE,
                            claims=(INFERRED_CLAIM,), for_publication=True)
    assert {"unverified-claim", "missing-provenance"} <= critical_codes(result)
```

- [ ] **Step 2: Run truth tests and verify RED**

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy pytest tests/studios/career/test_truth_guardian.py -q
```

Expected: collection fails because draft and validation contracts are absent.

- [ ] **Step 3: Implement provenance-carrying draft contracts and deterministic drafting**

Every `DraftBullet` stores a non-empty tuple of source claim IDs, transformation enum, before text tuple, after text, typed asserted facts with their own support claim IDs, and added keywords with support claim IDs. Transformation labels record attempted draft operations; they do not by themselves authorize publication. `draft_from_matches` creates one deterministic verbatim bullet per selected claim, copying the exact source text and typed claim object; it never generates new facts or metrics.

- [ ] **Step 4: Implement Truth Guardian critical gates and abstention**

Resolve every bullet source, asserted fact support ID, and keyword support ID against the supplied claim map. Emit critical `ValidationIssue` values for:

- missing or unknown provenance;
- non-verified claims in publication validation;
- publication transformations not present in `REGISTERED_PUBLICATION_TRANSFORMATIONS`; this slice registers only exact-span `VERBATIM`;
- unsupported employer, title, date, skill, degree, metric, or other facts;
- created, moved, changed, or rounded-up metrics;
- unsupported keywords;
- `combined` bullets without at least two claims;
- claim combinations lacking a shared employer or project context and overlapping temporal scope.

On any critical issue, return `AIResult(output=None, ...)` with the issues and abstention reason. Otherwise return the frozen draft plus deduplicated `EvidenceReference` objects pointing to claim IDs and exact source locators.

- [ ] **Step 5: Run truth tests and verify GREEN**

Run the Step 2 command. Expected: all truth tests pass with no warnings.

- [ ] **Step 6: Commit drafting and validation**

```bash
git add backend/app/studios/career backend/tests/studios/career/test_truth_guardian.py .superpowers/sdd/career-studio-v2-report.md
git commit -m "feat(career): enforce evidence-constrained drafting"
```

### Task 4: Approval-Gated Career Specialist Vertical Slice

**Files:**
- Create: `backend/app/studios/career/workflow/__init__.py`
- Create: `backend/app/studios/career/workflow/service.py`
- Create: `backend/tests/studios/career/test_service.py`
- Modify: `backend/app/studios/career/__init__.py`
- Modify: `.superpowers/sdd/career-studio-v2-report.md`

**Interfaces:**
- Consumes: shared `StudioRun` transitions, shared approvals, match result, deterministic drafter, and Truth Guardian result.
- Produces: `CareerDeliverable`, `CareerSpecialistResponse`, and `CareerSpecialist.run(...)`.

- [ ] **Step 1: Write failing workflow tests**

```python
def test_inferred_claim_pauses_for_review():
    response = CareerSpecialist().run(RUN, claims=(INFERRED_CLAIM,),
                                      requirements=(REQ,), candidate_edges=(), now=NOW)
    assert response.run.state is StudioRunState.AWAITING_INPUT
    assert response.approval.decision_type == "inferred-claims"
    assert response.approval.proposed_changes == (INFERRED_CLAIM.id,)


def test_verified_path_waits_for_final_resume_approval():
    response = CareerSpecialist().run(RUN, claims=(VERIFIED_CLAIM,),
                                      requirements=(REQ,), candidate_edges=(EDGE,), now=NOW)
    assert response.run.state is StudioRunState.AWAITING_INPUT
    assert response.approval.decision_type == "final-resume"
    assert response.result.output.draft.publication_ready is False


def test_approved_resume_succeeds_with_end_to_end_provenance():
    first = CareerSpecialist().run(RUN, claims=CLAIMS, requirements=REQUIREMENTS,
                                   candidate_edges=EDGES, now=NOW)
    approval = decide_approval(first.approval, ApprovalDecision.APPROVE,
                               reviewer_id=RUN.owner_id, now=LATER)
    final = CareerSpecialist().run(first.run, claims=CLAIMS, requirements=REQUIREMENTS,
                                   candidate_edges=EDGES, now=LATER,
                                   approval=approval)
    assert final.run.state is StudioRunState.SUCCEEDED
    assert final.result.output.draft.publication_ready is True
    for bullet in final.result.output.draft.bullets:
        assert set(bullet.source_claim_ids) <= {claim.id for claim in CLAIMS}
    assert {item.source_id for item in final.result.evidence} == {
        claim.id for claim in final.result.output.selected_evidence
    }
```

- [ ] **Step 2: Run workflow tests and verify RED**

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy pytest tests/studios/career/test_service.py -q
```

Expected: collection fails because `CareerSpecialist` is absent.

- [ ] **Step 3: Implement the deterministic service state machine**

Normalize queued runs to running using `transition_run`. If inferred claims exist, transition to `awaiting_input` at `claim-review`, create a deterministic pending `ApprovalRequest(decision_type="inferred-claims")`, and return without using inferred evidence. Otherwise compute the one-to-one match, draft from selected verified evidence, and validate it.

If validation abstains, transition the run to failed and preserve the `AIResult` critical issues. If validation passes without an approved final request, transition to `awaiting_input` at `final-resume-approval`, create a deterministic pending `ApprovalRequest(decision_type="final-resume")`, and expose only a non-publication-ready draft. Accept final approval only when its run ID, owner ID, decision type, proposed draft ID, evidence IDs, and approved status match the recomputed result. Resume the waiting run, validate for publication, mark the copied draft `publication_ready=True`, and transition to succeeded.

- [ ] **Step 4: Run workflow tests and verify GREEN**

Run the Step 2 command. Expected: all service tests pass with no warnings.

- [ ] **Step 5: Commit the service slice**

```bash
git add backend/app/studios/career backend/tests/studios/career/test_service.py .superpowers/sdd/career-studio-v2-report.md
git commit -m "feat(career): add approval-gated specialist service"
```

### Task 5: Full Verification and Design Self-Review

**Files:**
- Modify: `backend/tests/studios/career/**` only if a newly discovered gap first receives a failing regression test
- Modify: `backend/app/studios/career/**` only to make such a regression test pass
- Modify: `.superpowers/sdd/career-studio-v2-report.md`

**Interfaces:**
- Verifies all interfaces from Tasks 1-4 as one owned vertical slice.

- [ ] **Step 1: Run the complete owned test directory**

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy pytest tests/studios/career -q
```

Expected: every Career Studio test passes with pristine output.

- [ ] **Step 2: Re-read design sections 1-5, 7, 9, 11, 14, and 15 against the implementation**

Confirm explicitly in the report that the slice has immutable atomic claims, typed weighted requirements, bounded score components, deterministic one-to-one matching, calibrated coverage, provenance-carrying drafts, critical truth abstention, inferred and final approval pauses, no network calls, and end-to-end evidence resolution. Record any omitted requirement as a concern rather than implying it is complete.

- [ ] **Step 3: Scan only owned paths for placeholders and debug residue**

```bash
rg -n 'TO''DO|TB''D|FIX''ME|print\(|breakpoint\(' backend/app/studios/career backend/tests/studios/career .superpowers/sdd/career-studio-v2-report.md
```

Expected: no matches.

- [ ] **Step 4: Inspect the owned diff and verify path isolation**

```bash
git status --short
git diff --check
git diff --name-only HEAD~4..HEAD
```

Expected: no whitespace errors and no modified path outside the assigned ownership set.

- [ ] **Step 5: Commit final review corrections and report**

```bash
git add backend/app/studios/career backend/tests/studios/career .superpowers/sdd/career-studio-v2-report.md
git commit -m "test(career): complete core vertical slice verification"
```

## Plan Self-Review

- **Spec coverage:** Tasks 1-4 map to design sections 7.2-7.6 and the Career path in section 15; Task 5 maps to sections 3, 5, 9, 11, and 14. UI, persistence, extraction, ATS layout checks, and artifact rendering remain outside the assigned delivery boundary.
- **Placeholder scan:** The plan contains executable interfaces, assertions, commands, expected failures, and expected successful outcomes; it contains no deferred implementation marker.
- **Type consistency:** `CareerClaim` and `RoleRequirement` feed scoring; `CandidateEdge` feeds matching; `CareerMatchResult` feeds drafting; `ResumeDraft` feeds Truth Guardian; and `CareerSpecialistResponse` wraps the shared `AIResult` and `ApprovalRequest` contracts consistently.
- **Execution choice:** The assigning agent explicitly requested implementation in this session, so execute inline with `superpowers:executing-plans` and checkpoint at each logical commit.
