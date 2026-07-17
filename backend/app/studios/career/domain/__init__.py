"""Canonical Career Studio domain contracts."""

from .claims import (
    CareerClaim,
    ClaimContext,
    ClaimObject,
    ClaimPredicate,
    ClaimSubject,
    ClaimSubjectKind,
    ClaimValueKind,
    SourceSpan,
    TemporalScope,
    stable_claim_id,
)
from .requirements import (
    RequirementCategory,
    RequirementPriority,
    RoleRequirement,
)
from .matching import (
    CandidateEdge,
    CareerMatchResult,
    CoverageBand,
    CoverageSummary,
    MatchStrength,
    ScoreComponents,
    SelectedMatch,
)

__all__ = [
    "CareerClaim",
    "CandidateEdge",
    "CareerMatchResult",
    "ClaimContext",
    "ClaimObject",
    "ClaimPredicate",
    "ClaimSubject",
    "ClaimSubjectKind",
    "ClaimValueKind",
    "CoverageBand",
    "CoverageSummary",
    "MatchStrength",
    "RequirementCategory",
    "RequirementPriority",
    "RoleRequirement",
    "ScoreComponents",
    "SelectedMatch",
    "SourceSpan",
    "TemporalScope",
    "stable_claim_id",
]
