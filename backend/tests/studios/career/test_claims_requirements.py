from __future__ import annotations

import json
from datetime import date

import pytest
from pydantic import ValidationError

from app.platform.evidence import VerificationStatus
from app.studios.career.domain import (
    CareerClaim,
    ClaimContext,
    ClaimObject,
    ClaimPredicate,
    ClaimSubject,
    ClaimSubjectKind,
    ClaimValueKind,
    RequirementCategory,
    RequirementPriority,
    RoleRequirement,
    SourceSpan,
    TemporalScope,
    stable_claim_id,
)


SPAN_A = SourceSpan(
    source_id="resume-2026",
    locator="page-1:lines-4-5",
    exact_text="Built production services with Python.",
)
SPAN_B = SourceSpan(
    source_id="portfolio-2026",
    locator="project-api:paragraph-2",
    exact_text="Python powered the API implementation.",
)
SUBJECT = ClaimSubject(
    kind=ClaimSubjectKind.PERSON,
    id="person-gopal",
    label="Gopal",
)
PYTHON_OBJECT = ClaimObject(kind=ClaimValueKind.SKILL, value="Python")
SCOPE = TemporalScope(start=date(2024, 1, 1), end=date(2025, 12, 31))
CONTEXT = ClaimContext(employer_id="employer-acme", project_id="project-api")


def make_claim(
    *,
    source_spans: tuple[SourceSpan, ...] = (SPAN_A,),
    object_: ClaimObject = PYTHON_OBJECT,
    verification_status: VerificationStatus = VerificationStatus.VERIFIED,
) -> CareerClaim:
    return CareerClaim.create(
        subject=SUBJECT,
        predicate=ClaimPredicate.HAS_SKILL,
        object=object_,
        source_spans=source_spans,
        temporal_scope=SCOPE,
        verification_status=verification_status,
        confidence=0.96,
        verifier_id="reviewer-7",
        context=CONTEXT,
        related_claim_ids=("claim-related",),
    )


def test_claim_is_deeply_immutable_and_json_safe() -> None:
    claim = make_claim()

    with pytest.raises(ValidationError):
        claim.confidence = 0.1
    with pytest.raises(ValidationError):
        claim.source_spans[0].exact_text = "changed"

    payload = json.loads(claim.model_dump_json())
    assert payload["object"]["value"] == "Python"
    assert payload["temporal_scope"]["start"] == "2024-01-01"
    assert payload["related_claim_ids"] == ["claim-related"]


def test_stable_claim_id_ignores_span_and_relationship_input_order() -> None:
    forward = stable_claim_id(
        subject=SUBJECT,
        predicate=ClaimPredicate.HAS_SKILL,
        object=PYTHON_OBJECT,
        source_spans=(SPAN_A, SPAN_B),
        temporal_scope=SCOPE,
        context=CONTEXT,
        related_claim_ids=("claim-z", "claim-a"),
    )
    reverse = stable_claim_id(
        subject=SUBJECT,
        predicate=ClaimPredicate.HAS_SKILL,
        object=PYTHON_OBJECT,
        source_spans=(SPAN_B, SPAN_A),
        temporal_scope=SCOPE,
        context=CONTEXT,
        related_claim_ids=("claim-a", "claim-z"),
    )

    assert forward == reverse
    assert forward.startswith("claim-")
    assert len(forward) == 30


def test_claim_identity_is_stable_across_review_status_changes() -> None:
    inferred = make_claim(verification_status=VerificationStatus.INFERRED)
    verified = make_claim(verification_status=VerificationStatus.VERIFIED)

    assert inferred.id == verified.id


def test_claim_identity_changes_when_atomic_fact_changes() -> None:
    python_claim = make_claim()
    java_claim = make_claim(
        object_=ClaimObject(kind=ClaimValueKind.SKILL, value="Java")
    )

    assert python_claim.id != java_claim.id


def test_claim_rejects_non_finite_metric_and_invalid_temporal_scope() -> None:
    with pytest.raises(ValidationError, match="finite"):
        ClaimObject(kind=ClaimValueKind.METRIC, value=float("inf"), unit="percent")

    with pytest.raises(ValidationError, match="cannot precede"):
        TemporalScope(start=date(2025, 1, 1), end=date(2024, 1, 1))


def test_claim_requires_atomic_source_provenance_and_verifier_identity() -> None:
    with pytest.raises(ValidationError):
        CareerClaim.create(
            subject=SUBJECT,
            predicate=ClaimPredicate.HAS_SKILL,
            object=PYTHON_OBJECT,
            source_spans=(),
            temporal_scope=SCOPE,
            verification_status=VerificationStatus.INFERRED,
            confidence=0.5,
            verifier_id=" ",
            context=CONTEXT,
        )


def test_requirement_retains_typed_priority_category_and_exact_span() -> None:
    source_span = SourceSpan(
        source_id="job-42",
        locator="requirements:line-3",
        exact_text="Production Python experience is required.",
    )
    requirement = RoleRequirement(
        id="req-production-python",
        priority=RequirementPriority.REQUIRED,
        category=RequirementCategory.SKILL,
        description="Production Python experience",
        source_span=source_span,
        confidence=0.95,
        weight=3.0,
    )

    assert requirement.priority is RequirementPriority.REQUIRED
    assert requirement.category is RequirementCategory.SKILL
    assert requirement.source_span.exact_text == source_span.exact_text
    assert requirement.weight == 3.0
    with pytest.raises(ValidationError):
        requirement.weight = 1.0


@pytest.mark.parametrize("weight", [0.0, -1.0, float("inf"), float("nan")])
def test_requirement_weight_must_be_finite_and_positive(weight: float) -> None:
    with pytest.raises(ValidationError):
        RoleRequirement(
            id="req-python",
            priority=RequirementPriority.PREFERRED,
            category=RequirementCategory.SKILL,
            description="Python",
            source_span=SourceSpan(
                source_id="job-42",
                locator="preferred:line-1",
                exact_text="Python preferred.",
            ),
            confidence=0.8,
            weight=weight,
        )
