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

__all__ = [
    "CareerClaim",
    "ClaimContext",
    "ClaimObject",
    "ClaimPredicate",
    "ClaimSubject",
    "ClaimSubjectKind",
    "ClaimValueKind",
    "RequirementCategory",
    "RequirementPriority",
    "RoleRequirement",
    "SourceSpan",
    "TemporalScope",
    "stable_claim_id",
]
