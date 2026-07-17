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
) -> CareerClaim:
    locator = f"claim:{kind.value}:{str(value).casefold().replace(' ', '-')}"
    return CareerClaim.create(
        subject=SUBJECT,
        predicate=predicate,
        object=ClaimObject(kind=kind, value=value, unit=unit),
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
    assert draft.bullets[0].transformation is DraftTransformation.VERBATIM
    assert draft.bullets[0].before_text == ("Used Python in production.",)
    assert draft.bullets[0].after_text == "Used Python in production."
    assert draft.bullets[0].asserted_facts == (fact(python_claim),)


def test_fabricated_or_rounded_up_metric_abstains() -> None:
    metric_claim = claim(
        ClaimValueKind.METRIC,
        19.6,
        unit="percent",
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
    assert "incompatible-combination" in critical_codes(result)


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
                after_text="Built production Python services.",
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

    result = validate_draft(draft, claims=(python_claim,), for_publication=True)

    assert result.output == draft
    assert result.quality.abstention_reason is None
    assert result.evidence[0].source_id == python_claim.id
    assert result.evidence[0].locator == python_claim.source_spans[0].locator


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
