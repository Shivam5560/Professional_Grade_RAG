from __future__ import annotations

from datetime import date

import pytest

from app.platform.evidence import VerificationStatus
from app.platform.quality import ValidationStatus
from app.studios.career.domain import (
    AddedKeyword,
    AssertedFact,
    CareerClaim,
    ClaimContext,
    ClaimObject,
    ClaimPredicate,
    ClaimSubject,
    ClaimSubjectKind,
    ClaimValueKind,
    DraftBullet,
    DraftTransformation,
    RequirementCategory,
    RequirementPriority,
    ResumeDraft,
    RoleRequirement,
    ScoreComponents,
    SourceSpan,
    TemporalScope,
)
from app.studios.career.matching import match_requirements, score_candidate_edge
from app.studios.career.validation import validate_draft
from app.studios.career.writing import draft_from_matches


SUBJECT = ClaimSubject(
    kind=ClaimSubjectKind.PERSON,
    id="person-7",
    label="Candidate",
)


def claim(
    kind: ClaimValueKind,
    value: str | int | float | bool,
    *,
    exact_text: str,
    predicate: ClaimPredicate = ClaimPredicate.PERFORMED,
    employer_id: str | None = "employer-acme",
    project_id: str | None = "project-platform",
    start: date = date(2023, 1, 1),
    end: date = date(2024, 12, 31),
    status: VerificationStatus = VerificationStatus.VERIFIED,
    unit: str | None = None,
    measure: str | None = None,
) -> CareerClaim:
    locator = f"claim:{kind.value}:{str(value).casefold().replace(' ', '-')}"
    return CareerClaim.create(
        subject=SUBJECT,
        predicate=predicate,
        object=ClaimObject(kind=kind, value=value, unit=unit, measure=measure),
        source_spans=(
            SourceSpan(
                source_id="resume-1",
                locator=locator,
                exact_text=exact_text,
            ),
        ),
        temporal_scope=TemporalScope(start=start, end=end),
        verification_status=status,
        confidence=0.95,
        verifier_id="reviewer-7",
        context=ClaimContext(employer_id=employer_id, project_id=project_id),
    )


def bullet(
    source_claims: tuple[CareerClaim, ...],
    *,
    transformation: DraftTransformation = DraftTransformation.REPHRASED,
    after_text: str,
    asserted_facts: tuple[AssertedFact, ...],
    added_keywords: tuple[AddedKeyword, ...] = (),
) -> DraftBullet:
    return DraftBullet(
        source_claim_ids=tuple(item.id for item in source_claims),
        transformation=transformation,
        before_text=tuple(
            item.source_spans[0].exact_text for item in source_claims
        ),
        after_text=after_text,
        asserted_facts=asserted_facts,
        added_keywords=added_keywords,
    )


def fact(source: CareerClaim, *, value: str | int | float | bool | None = None) -> AssertedFact:
    return AssertedFact(
        kind=source.object.kind,
        value=source.object.value if value is None else value,
        unit=source.object.unit,
        measure=getattr(source.object, "measure", None),
        source_claim_ids=(source.id,),
    )


def critical_codes(result: object) -> set[str]:
    return {
        issue.code
        for issue in result.quality.validations
        if issue.critical and issue.status is ValidationStatus.ERROR
    }


def test_drafter_copies_selected_evidence_with_complete_provenance() -> None:
    python_claim = claim(
        ClaimValueKind.SKILL,
        "Python",
        exact_text="Used Python in production.",
        predicate=ClaimPredicate.HAS_SKILL,
    )
    requirement = RoleRequirement(
        id="req-python",
        priority=RequirementPriority.REQUIRED,
        category=RequirementCategory.SKILL,
        description="Python",
        source_span=SourceSpan(
            source_id="job-1",
            locator="requirements:python",
            exact_text="Python is required.",
        ),
        confidence=0.95,
        weight=2.0,
    )
    components = ScoreComponents(
        semantic_relevance=0.95,
        evidence_strength=1.0,
        recency=0.9,
        duration_seniority=0.8,
        transferability=1.0,
        specificity=1.0,
    )
    match = match_requirements(
        (requirement,),
        (python_claim,),
        (score_candidate_edge(requirement, python_claim, components),),
    )

    draft = draft_from_matches(match)

    assert len(draft.bullets) == 1
    assert draft.publication_ready is False
    assert draft.bullets[0].source_claim_ids == (python_claim.id,)
    assert draft.bullets[0].transformation is DraftTransformation.COMPRESSED
    assert draft.bullets[0].before_text == ("Used Python in production.",)
    assert draft.bullets[0].after_text == "Python."
    assert draft.bullets[0].asserted_facts == (fact(python_claim),)


def test_fabricated_or_rounded_up_metric_abstains() -> None:
    metric_claim = claim(
        ClaimValueKind.METRIC,
        19.6,
        unit="percent",
        measure="throughput",
        exact_text="Improved throughput by 19.6 percent.",
        predicate=ClaimPredicate.MEASURED,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (metric_claim,),
                after_text="Improved throughput by 20 percent.",
                asserted_facts=(fact(metric_claim, value=20),),
            ),
        )
    )

    result = validate_draft(draft, claims=(metric_claim,), for_publication=True)

    assert result.output is None
    assert result.quality.abstention_reason == "career draft failed truth validation"
    assert "metric-altered" in critical_codes(result)


def test_metric_hidden_from_structured_facts_is_still_rejected() -> None:
    metric_claim = claim(
        ClaimValueKind.METRIC,
        19.6,
        unit="percent",
        measure="throughput",
        exact_text="Improved throughput by 19.6 percent.",
        predicate=ClaimPredicate.MEASURED,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (metric_claim,),
                after_text="Improved throughput by 20 percent.",
                asserted_facts=(),
            ),
        )
    )

    result = validate_draft(draft, claims=(metric_claim,), for_publication=True)

    assert result.output is None
    assert "metric-altered" in critical_codes(result)


def test_incompatible_combination_abstains() -> None:
    employer_a = claim(
        ClaimValueKind.RESPONSIBILITY,
        "Built a billing API",
        exact_text="Built a billing API.",
        employer_id="employer-a",
        project_id="project-billing",
        start=date(2021, 1, 1),
        end=date(2022, 1, 1),
    )
    employer_b = claim(
        ClaimValueKind.OUTCOME,
        "Reduced queue latency",
        exact_text="Reduced queue latency.",
        employer_id="employer-b",
        project_id="project-streaming",
        start=date(2024, 1, 1),
        end=date(2025, 1, 1),
        predicate=ClaimPredicate.ACHIEVED,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (employer_a, employer_b),
                transformation=DraftTransformation.COMBINED,
                after_text="Built a billing API and reduced queue latency.",
                asserted_facts=(fact(employer_a), fact(employer_b)),
            ),
        )
    )

    result = validate_draft(
        draft,
        claims=(employer_a, employer_b),
        for_publication=True,
    )

    assert result.output is None
    assert {
        "incompatible-combination",
        "unsupported-transformation",
    } <= critical_codes(result)


def test_supported_keyword_is_accepted_and_resolves_to_claim() -> None:
    python_claim = claim(
        ClaimValueKind.SKILL,
        "Python",
        exact_text="Used Python in production.",
        predicate=ClaimPredicate.HAS_SKILL,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (python_claim,),
                after_text="Production Python.",
                asserted_facts=(fact(python_claim),),
                added_keywords=(
                    AddedKeyword(
                        keyword="Python",
                        source_claim_ids=(python_claim.id,),
                    ),
                ),
            ),
        )
    )

    result = validate_draft(draft, claims=(python_claim,), for_publication=False)

    assert result.output == draft
    assert result.quality.abstention_reason is None
    assert result.evidence[0].source_id == python_claim.id
    assert result.evidence[0].locator == python_claim.source_spans[0].locator


def test_negation_reorder_cannot_publish_from_same_source_tokens() -> None:
    python_claim = claim(
        ClaimValueKind.SKILL,
        "Python",
        exact_text="Did not use Rust; used Python.",
        predicate=ClaimPredicate.HAS_SKILL,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (python_claim,),
                after_text="Used Rust.",
                asserted_facts=(fact(python_claim),),
            ),
        )
    )

    result = validate_draft(draft, claims=(python_claim,), for_publication=True)

    assert result.output is None
    assert "unsupported-transformation" in critical_codes(result)


def test_metric_direction_swap_cannot_publish() -> None:
    throughput = claim(
        ClaimValueKind.METRIC,
        20,
        unit="percent",
        measure="throughput",
        exact_text="Reduced latency and increased throughput by 20 percent.",
        predicate=ClaimPredicate.MEASURED,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (throughput,),
                after_text="Reduced throughput by 20 percent.",
                asserted_facts=(fact(throughput),),
            ),
        )
    )

    result = validate_draft(draft, claims=(throughput,), for_publication=True)

    assert result.output is None
    assert "unsupported-transformation" in critical_codes(result)


@pytest.mark.parametrize(
    "source_text,unit,measure",
    [
        ("$20 revenue", "USD", "revenue"),
        ("€20 revenue", "EUR", "revenue"),
        ("₹20 revenue", "INR", "revenue"),
        ("20% throughput", "percent", "throughput"),
    ],
)
def test_verbatim_metric_accepts_normalized_unit_aliases(
    source_text: str,
    unit: str,
    measure: str,
) -> None:
    metric_claim = claim(
        ClaimValueKind.METRIC,
        20,
        unit=unit,
        measure=measure,
        exact_text=source_text,
        predicate=ClaimPredicate.MEASURED,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (metric_claim,),
                transformation=DraftTransformation.VERBATIM,
                after_text=source_text,
                asserted_facts=(fact(metric_claim),),
            ),
        )
    )

    result = validate_draft(draft, claims=(metric_claim,), for_publication=True)

    assert result.output == draft
    assert result.quality.abstention_reason is None


def test_unregistered_synonym_rephrase_is_explicitly_non_publishable() -> None:
    responsibility = claim(
        ClaimValueKind.RESPONSIBILITY,
        "Built Python APIs",
        exact_text="Built Python APIs.",
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (responsibility,),
                after_text="Developed Python APIs.",
                asserted_facts=(fact(responsibility),),
            ),
        )
    )

    result = validate_draft(
        draft,
        claims=(responsibility,),
        for_publication=True,
    )

    assert result.output is None
    assert "unsupported-transformation" in critical_codes(result)


def test_publishable_draft_rejects_inferred_claim_and_missing_provenance() -> None:
    inferred = claim(
        ClaimValueKind.SKILL,
        "Python",
        exact_text="Possibly used Python.",
        predicate=ClaimPredicate.HAS_SKILL,
        status=VerificationStatus.INFERRED,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (inferred,),
                after_text="Used Python.",
                asserted_facts=(
                    AssertedFact(
                        kind=ClaimValueKind.SKILL,
                        value="Python",
                        source_claim_ids=(),
                    ),
                ),
            ),
        )
    )

    result = validate_draft(draft, claims=(inferred,), for_publication=True)

    assert result.output is None
    assert {"unverified-claim", "missing-provenance"} <= critical_codes(result)


@pytest.mark.parametrize(
    "kind,value,expected_code",
    [
        (ClaimValueKind.EMPLOYER, "Acme", "unsupported-employer"),
        (ClaimValueKind.TITLE, "Principal Engineer", "unsupported-title"),
        (ClaimValueKind.DATE, "2025-01-01", "unsupported-date"),
        (ClaimValueKind.SKILL, "Rust", "unsupported-skill"),
        (ClaimValueKind.DEGREE, "PhD", "unsupported-degree"),
    ],
)
def test_typed_fact_additions_are_rejected(
    kind: ClaimValueKind,
    value: str,
    expected_code: str,
) -> None:
    python_claim = claim(
        ClaimValueKind.SKILL,
        "Python",
        exact_text="Used Python in production.",
        predicate=ClaimPredicate.HAS_SKILL,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (python_claim,),
                after_text=f"Python; {value}.",
                asserted_facts=(
                    AssertedFact(
                        kind=kind,
                        value=value,
                        source_claim_ids=(python_claim.id,),
                    ),
                ),
            ),
        )
    )

    result = validate_draft(draft, claims=(python_claim,), for_publication=True)

    assert result.output is None
    assert expected_code in critical_codes(result)


def test_unknown_claim_and_unsupported_keyword_abstain() -> None:
    python_claim = claim(
        ClaimValueKind.SKILL,
        "Python",
        exact_text="Used Python in production.",
        predicate=ClaimPredicate.HAS_SKILL,
    )
    draft = ResumeDraft.create(
        bullets=(
            DraftBullet(
                source_claim_ids=(python_claim.id, "claim-unknown"),
                transformation=DraftTransformation.REPHRASED,
                before_text=(python_claim.source_spans[0].exact_text,),
                after_text="Built Kubernetes services.",
                asserted_facts=(fact(python_claim),),
                added_keywords=(
                    AddedKeyword(
                        keyword="Kubernetes",
                        source_claim_ids=(python_claim.id,),
                    ),
                ),
            ),
        )
    )

    result = validate_draft(draft, claims=(python_claim,), for_publication=True)

    assert result.output is None
    assert {"unknown-claim", "unsupported-keyword"} <= critical_codes(result)


def test_missing_before_text_abstains_as_missing_provenance() -> None:
    python_claim = claim(
        ClaimValueKind.SKILL,
        "Python",
        exact_text="Used Python in production.",
        predicate=ClaimPredicate.HAS_SKILL,
    )
    draft = ResumeDraft.create(
        bullets=(
            DraftBullet(
                source_claim_ids=(python_claim.id,),
                transformation=DraftTransformation.REPHRASED,
                before_text=(),
                after_text="Built Python services.",
                asserted_facts=(fact(python_claim),),
            ),
        )
    )

    result = validate_draft(draft, claims=(python_claim,), for_publication=True)

    assert result.output is None
    assert "missing-provenance" in critical_codes(result)


def test_raw_prose_assertions_are_reconciled_without_trusting_fact_metadata() -> None:
    python_claim = claim(
        ClaimValueKind.SKILL,
        "Python",
        exact_text="Used Python in production.",
        predicate=ClaimPredicate.HAS_SKILL,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (python_claim,),
                after_text=(
                    "Principal Engineer at Google with a PhD using Rust and Python "
                    "in 2025."
                ),
                asserted_facts=(fact(python_claim),),
            ),
        )
    )

    result = validate_draft(draft, claims=(python_claim,), for_publication=True)

    assert result.output is None
    assert {"unsupported-text-assertion", "unsupported-date"} <= critical_codes(
        result
    )


def test_metric_scalar_cannot_move_between_unit_measure_and_context() -> None:
    throughput = claim(
        ClaimValueKind.METRIC,
        20,
        unit="percent",
        measure="throughput",
        exact_text="Improved throughput by 20 percent.",
        predicate=ClaimPredicate.MEASURED,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (throughput,),
                after_text="Generated $20 million in revenue.",
                asserted_facts=(
                    AssertedFact(
                        kind=ClaimValueKind.METRIC,
                        value=20,
                        unit="percent",
                        measure="throughput",
                        source_claim_ids=(throughput.id,),
                    ),
                ),
            ),
        )
    )

    result = validate_draft(draft, claims=(throughput,), for_publication=True)

    assert result.output is None
    assert "metric-altered" in critical_codes(result)


def test_evidence_references_exact_used_span_with_deterministic_deduplication() -> None:
    first = SourceSpan(
        source_id="a-resume-1",
        locator="skills:first",
        exact_text="Python appears in the skills list.",
    )
    second = SourceSpan(
        source_id="z-portfolio-1",
        locator="project:second",
        exact_text="Used Python to build the project API.",
    )
    python_claim = CareerClaim.create(
        subject=SUBJECT,
        predicate=ClaimPredicate.HAS_SKILL,
        object=ClaimObject(kind=ClaimValueKind.SKILL, value="Python"),
        source_spans=(first, second),
        temporal_scope=TemporalScope(
            start=date(2023, 1, 1),
            end=date(2024, 12, 31),
        ),
        verification_status=VerificationStatus.VERIFIED,
        confidence=0.95,
        verifier_id="reviewer-7",
        context=ClaimContext(
            employer_id="employer-acme",
            project_id="project-platform",
        ),
    )
    used_bullet = DraftBullet(
        source_claim_ids=(python_claim.id,),
        transformation=DraftTransformation.VERBATIM,
        before_text=(second.exact_text,),
        after_text=second.exact_text,
        asserted_facts=(fact(python_claim),),
    )
    draft = ResumeDraft.create(bullets=(used_bullet, used_bullet))

    result = validate_draft(draft, claims=(python_claim,), for_publication=True)

    assert result.output is not None
    assert len(result.evidence) == 1
    assert result.evidence[0].source_id == python_claim.id
    assert result.evidence[0].locator == second.locator
    assert result.evidence[0].snippet == second.exact_text


def test_long_used_source_span_retains_locator_without_snippet_overflow() -> None:
    long_text = "Python " + ("production-service " * 80)
    long_claim = claim(
        ClaimValueKind.SKILL,
        "Python",
        exact_text=long_text,
        predicate=ClaimPredicate.HAS_SKILL,
    )
    draft = ResumeDraft.create(
        bullets=(
            bullet(
                (long_claim,),
                transformation=DraftTransformation.VERBATIM,
                after_text=long_text,
                asserted_facts=(fact(long_claim),),
            ),
        )
    )

    result = validate_draft(draft, claims=(long_claim,), for_publication=True)

    assert result.output is not None
    assert result.evidence[0].locator == long_claim.source_spans[0].locator
    assert result.evidence[0].snippet is not None
    assert len(result.evidence[0].snippet) <= 1000
