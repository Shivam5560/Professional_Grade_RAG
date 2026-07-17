from __future__ import annotations

from app.studios.career.domain.claims import CareerClaim
from app.studios.career.domain.matching import (
    CandidateEdge,
    ScoreComponents,
    strength_for_score,
)
from app.studios.career.domain.requirements import RoleRequirement


def score_candidate_edge(
    requirement: RoleRequirement,
    claim: CareerClaim,
    components: ScoreComponents,
) -> CandidateEdge:
    """Score an explicitly proposed edge without deriving semantic judgments."""

    score = components.weighted_score()
    return CandidateEdge(
        requirement_id=requirement.id,
        claim_id=claim.id,
        components=components,
        score=score,
        strength=strength_for_score(score),
    )
