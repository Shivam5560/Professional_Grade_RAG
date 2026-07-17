from __future__ import annotations

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
    CoverageBand,
    RequirementCategory,
    RequirementPriority,
    RoleRequirement,
    ScoreComponents,
    SourceSpan,
    TemporalScope,
)
from app.studios.career.matching import match_requirements, score_candidate_edge


SUBJECT = ClaimSubject(
    kind=ClaimSubjectKind.PERSON,
    id="person-7",
    label="Candidate",
)
SCOPE = TemporalScope(start=date(2023, 1, 1), end=date(2025, 12, 31))
CONTEXT = ClaimContext(employer_id="employer-acme", project_id="project-platform")


def claim(
    value: str,
    *,
    status: VerificationStatus = VerificationStatus.VERIFIED,
) -> CareerClaim:
    slug = value.casefold().replace(" ", "-")
    return CareerClaim.create(
        subject=SUBJECT,
        predicate=ClaimPredicate.HAS_SKILL,
        object=ClaimObject(kind=ClaimValueKind.SKILL, value=value),
        source_spans=(
            SourceSpan(
                source_id="resume-1",
                locator=f"skills:{slug}",
                exact_text=f"Used {value} in production.",
            ),
        ),
        temporal_scope=SCOPE,
        verification_status=status,
        confidence=0.95,
        verifier_id="reviewer-7",
        context=CONTEXT,
    )


def requirement(
    identifier: str,
    description: str,
    *,
    priority: RequirementPriority = RequirementPriority.REQUIRED,
    weight: float = 1.0,
) -> RoleRequirement:
    return RoleRequirement(
        id=identifier,
        priority=priority,
        category=RequirementCategory.SKILL,
        description=description,
        source_span=SourceSpan(
            source_id="job-1",
            locator=f"requirements:{identifier}",
            exact_text=description,
        ),
        confidence=0.9,
        weight=weight,
    )


def components(
    semantic: float,
    *,
    evidence: float = 1.0,
    recency: float = 1.0,
    duration_seniority: float = 1.0,
    transferability: float = 1.0,
    specificity: float = 1.0,
) -> ScoreComponents:
    return ScoreComponents(
        semantic_relevance=semantic,
        evidence_strength=evidence,
        recency=recency,
        duration_seniority=duration_seniority,
        transferability=transferability,
        specificity=specificity,
    )


def test_score_validates_and_preserves_each_component() -> None:
    req = requirement("req-python", "Python")
    python_claim = claim("Python")
    breakdown = components(
        0.9,
        recency=0.8,
        duration_seniority=0.7,
        transferability=0.6,
        specificity=0.9,
    )

    edge = score_candidate_edge(req, python_claim, breakdown)

    assert edge.components == breakdown
    assert edge.score == pytest.approx(0.86)
    assert edge.requirement_id == req.id
    assert edge.claim_id == python_claim.id


@pytest.mark.parametrize(
    "field,value",
    [
        ("semantic_relevance", 1.01),
        ("evidence_strength", -0.01),
        ("recency", float("nan")),
        ("duration_seniority", float("inf")),
        ("transferability", -float("inf")),
        ("specificity", 1.1),
    ],
)
def test_score_rejects_invalid_components(field: str, value: float) -> None:
    values = {
        "semantic_relevance": 1.0,
        "evidence_strength": 1.0,
        "recency": 1.0,
        "duration_seniority": 1.0,
        "transferability": 1.0,
        "specificity": 1.0,
    }
    values[field] = value

    with pytest.raises(ValidationError):
        ScoreComponents(**values)


def test_matching_does_not_double_count_one_claim() -> None:
    python_req = requirement("req-python", "Python")
    api_req = requirement("req-api", "API engineering")
    platform_claim = claim("Python platform APIs")
    edges = (
        score_candidate_edge(python_req, platform_claim, components(0.95)),
        score_candidate_edge(api_req, platform_claim, components(0.85)),
    )

    result = match_requirements(
        requirements=(python_req, api_req),
        claims=(platform_claim,),
        candidate_edges=edges,
    )

    assert len(result.selected_matches) == 1
    assert result.selected_matches[0].requirement_id == python_req.id
    assert result.selected_evidence == (platform_claim,)
    assert tuple(item.id for item in result.unmatched_requirements) == (api_req.id,)


def test_matching_ties_are_deterministic_across_input_order() -> None:
    requirements = (
        requirement("req-a", "Skill A"),
        requirement("req-b", "Skill B"),
    )
    claims = (claim("Skill A"), claim("Skill B"))
    tied_edges = tuple(
        score_candidate_edge(req, evidence, components(0.8))
        for req in requirements
        for evidence in claims
    )

    forward = match_requirements(requirements, claims, tied_edges)
    reverse = match_requirements(
        tuple(reversed(requirements)),
        tuple(reversed(claims)),
        tuple(reversed(tied_edges)),
    )

    assert forward.selected_matches == reverse.selected_matches
    assert tuple(match.requirement_id for match in forward.selected_matches) == (
        "req-a",
        "req-b",
    )
    assert len({match.claim_id for match in forward.selected_matches}) == 2


def test_coverage_is_weighted_and_uncertainty_is_a_range() -> None:
    core_req = requirement("req-core", "Core systems", weight=3.0)
    uncertain_req = requirement("req-uncertain", "Event streaming", weight=1.0)
    preferred_gap = requirement(
        "req-cloud-security",
        "Cloud security",
        priority=RequirementPriority.PREFERRED,
        weight=2.0,
    )
    core_claim = claim("Core systems")
    streaming_claim = claim("Event streaming")
    core_edge = score_candidate_edge(core_req, core_claim, components(0.9))
    uncertain_edge = score_candidate_edge(
        uncertain_req,
        streaming_claim,
        components(
            0.5,
            evidence=0.6,
            recency=0.5,
            duration_seniority=0.5,
            transferability=0.6,
            specificity=0.5,
        ),
    )

    result = match_requirements(
        requirements=(core_req, uncertain_req, preferred_gap),
        claims=(core_claim, streaming_claim),
        candidate_edges=(core_edge, uncertain_edge),
        minimum_score=0.4,
        uncertainty_threshold=0.65,
    )

    assert result.mandatory_coverage.lower_bound == pytest.approx(0.75)
    assert result.mandatory_coverage.upper_bound == pytest.approx(1.0)
    assert result.mandatory_coverage.band is CoverageBand.SUBSTANTIAL
    assert result.preferred_coverage.lower_bound == 0.0
    assert result.preferred_coverage.upper_bound == 0.0
    assert result.uncertain_requirement_ids == (uncertain_req.id,)
    assert tuple(item.id for item in result.unmatched_requirements) == (
        preferred_gap.id,
    )
    assert result.transferable_matches == (result.selected_matches[0],)


def test_matching_rejects_unverified_candidate_evidence() -> None:
    req = requirement("req-python", "Python")
    inferred = claim("Python", status=VerificationStatus.INFERRED)
    edge = score_candidate_edge(req, inferred, components(0.9))

    with pytest.raises(ValueError, match="verified"):
        match_requirements((req,), (inferred,), (edge,))


def test_matching_rejects_dangling_and_duplicate_edges() -> None:
    req = requirement("req-python", "Python")
    python_claim = claim("Python")
    edge = score_candidate_edge(req, python_claim, components(0.9))

    with pytest.raises(ValueError, match="duplicate"):
        match_requirements((req,), (python_claim,), (edge, edge))

    other_req = requirement("req-other", "Other")
    dangling = score_candidate_edge(other_req, python_claim, components(0.9))
    with pytest.raises(ValueError, match="unknown requirement"):
        match_requirements((req,), (python_claim,), (dangling,))
