from __future__ import annotations

from collections.abc import Iterable

from scipy.optimize import linear_sum_assignment

from app.platform.evidence import VerificationStatus
from app.studios.career.domain.claims import CareerClaim
from app.studios.career.domain.matching import (
    CandidateEdge,
    CareerMatchResult,
    CoverageBand,
    CoverageSummary,
    SelectedMatch,
)
from app.studios.career.domain.requirements import (
    RequirementPriority,
    RoleRequirement,
)

TRANSFERABLE_THRESHOLD = 0.75


def _require_unique_ids(items: Iterable[object], *, kind: str) -> None:
    identifiers = [getattr(item, "id") for item in items]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{kind} identifiers must be unique")


def _coverage_band(lower_bound: float, upper_bound: float) -> CoverageBand:
    if upper_bound == 0.0:
        return CoverageBand.NONE
    if lower_bound == 1.0:
        return CoverageBand.COMPLETE
    if lower_bound >= 0.75:
        return CoverageBand.SUBSTANTIAL
    if upper_bound >= 0.5:
        return CoverageBand.PARTIAL
    return CoverageBand.LIMITED


def _coverage_for(
    requirements: tuple[RoleRequirement, ...],
    selected_by_requirement: dict[str, SelectedMatch],
    priority: RequirementPriority,
) -> CoverageSummary:
    relevant = tuple(item for item in requirements if item.priority is priority)
    total_weight = sum(item.weight for item in relevant)
    selected = tuple(
        (item, selected_by_requirement[item.id])
        for item in relevant
        if item.id in selected_by_requirement
    )
    confident_weight = sum(item.weight for item, match in selected if not match.uncertain)
    possible_weight = sum(item.weight for item, _ in selected)
    lower_bound = confident_weight / total_weight if total_weight else 0.0
    upper_bound = possible_weight / total_weight if total_weight else 0.0
    return CoverageSummary(
        total_weight=total_weight,
        confident_matched_weight=confident_weight,
        possible_matched_weight=possible_weight,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        band=_coverage_band(lower_bound, upper_bound),
    )


def match_requirements(
    requirements: tuple[RoleRequirement, ...],
    claims: tuple[CareerClaim, ...],
    candidate_edges: tuple[CandidateEdge, ...],
    *,
    minimum_score: float = 0.45,
    uncertainty_threshold: float = 0.65,
) -> CareerMatchResult:
    """Return a deterministic maximum-weight one-to-one evidence assignment."""

    if not 0.0 <= minimum_score <= 1.0:
        raise ValueError("minimum_score must be between 0 and 1")
    if not minimum_score <= uncertainty_threshold <= 1.0:
        raise ValueError(
            "uncertainty_threshold must be between minimum_score and 1"
        )

    _require_unique_ids(requirements, kind="requirement")
    _require_unique_ids(claims, kind="claim")
    requirement_by_id = {item.id: item for item in requirements}
    claim_by_id = {item.id: item for item in claims}

    edge_by_pair: dict[tuple[str, str], CandidateEdge] = {}
    for edge in candidate_edges:
        if edge.requirement_id not in requirement_by_id:
            raise ValueError(
                f"candidate edge references unknown requirement {edge.requirement_id}"
            )
        if edge.claim_id not in claim_by_id:
            raise ValueError(f"candidate edge references unknown claim {edge.claim_id}")
        if claim_by_id[edge.claim_id].verification_status is not VerificationStatus.VERIFIED:
            raise ValueError("candidate edges may use only verified claims")
        pair = (edge.requirement_id, edge.claim_id)
        if pair in edge_by_pair:
            raise ValueError("duplicate candidate edge for requirement and claim")
        edge_by_pair[pair] = edge

    ordered_requirements = tuple(sorted(requirements, key=lambda item: item.id))
    ordered_claims = tuple(sorted(claims, key=lambda item: item.id))
    if not ordered_requirements:
        return CareerMatchResult(
            selected_matches=(),
            mandatory_coverage=_coverage_for((), {}, RequirementPriority.REQUIRED),
            preferred_coverage=_coverage_for((), {}, RequirementPriority.PREFERRED),
            unmatched_requirements=(),
            uncertain_matches=(),
            uncertain_requirement_ids=(),
            transferable_matches=(),
            selected_evidence=(),
        )

    claim_count = len(ordered_claims)
    invalid_objective = -1.0
    objective_matrix = [
        [invalid_objective] * claim_count + [0.0] * len(ordered_requirements)
        for _ in ordered_requirements
    ]
    for row, requirement in enumerate(ordered_requirements):
        for column, claim in enumerate(ordered_claims):
            edge = edge_by_pair.get((requirement.id, claim.id))
            if edge is not None and edge.score >= minimum_score:
                objective_matrix[row][column] = edge.score * requirement.weight

    row_indices, column_indices = linear_sum_assignment(
        objective_matrix,
        maximize=True,
    )
    selected: list[SelectedMatch] = []
    for row, column in zip(row_indices.tolist(), column_indices.tolist(), strict=True):
        if column >= claim_count or objective_matrix[row][column] <= 0.0:
            continue
        requirement = ordered_requirements[row]
        claim = ordered_claims[column]
        edge = edge_by_pair[(requirement.id, claim.id)]
        selected.append(
            SelectedMatch(
                requirement_id=requirement.id,
                claim_id=claim.id,
                components=edge.components,
                score=edge.score,
                strength=edge.strength,
                objective_weight=objective_matrix[row][column],
                uncertain=edge.score < uncertainty_threshold,
            )
        )

    selected_matches = tuple(sorted(selected, key=lambda item: item.requirement_id))
    selected_by_requirement = {
        item.requirement_id: item for item in selected_matches
    }
    unmatched_requirements = tuple(
        item
        for item in ordered_requirements
        if item.id not in selected_by_requirement
    )
    uncertain_matches = tuple(item for item in selected_matches if item.uncertain)
    transferable_matches = tuple(
        item
        for item in selected_matches
        if item.components.transferability >= TRANSFERABLE_THRESHOLD
    )
    selected_evidence = tuple(
        claim_by_id[item.claim_id] for item in selected_matches
    )

    return CareerMatchResult(
        selected_matches=selected_matches,
        mandatory_coverage=_coverage_for(
            ordered_requirements,
            selected_by_requirement,
            RequirementPriority.REQUIRED,
        ),
        preferred_coverage=_coverage_for(
            ordered_requirements,
            selected_by_requirement,
            RequirementPriority.PREFERRED,
        ),
        unmatched_requirements=unmatched_requirements,
        uncertain_matches=uncertain_matches,
        uncertain_requirement_ids=tuple(
            item.requirement_id for item in uncertain_matches
        ),
        transferable_matches=transferable_matches,
        selected_evidence=selected_evidence,
    )
