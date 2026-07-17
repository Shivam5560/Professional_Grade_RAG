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
from .drafts import (
    AddedKeyword,
    AssertedFact,
    DraftBullet,
    DraftTransformation,
    ResumeDraft,
    stable_draft_id,
)

__all__ = [
    "AddedKeyword",
    "AssertedFact",
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
    "DraftBullet",
    "DraftTransformation",
    "MatchStrength",
    "RequirementCategory",
    "RequirementPriority",
    "RoleRequirement",
    "ResumeDraft",
    "ScoreComponents",
    "SelectedMatch",
    "SourceSpan",
    "TemporalScope",
    "stable_claim_id",
    "stable_draft_id",
]
