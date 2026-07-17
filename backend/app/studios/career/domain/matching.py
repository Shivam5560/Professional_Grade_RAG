from __future__ import annotations

from enum import StrEnum
from math import isclose
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .claims import CareerClaim
from .requirements import RoleRequirement

COMPONENT_WEIGHTS = {
    "semantic_relevance": 0.35,
    "evidence_strength": 0.20,
    "recency": 0.10,
    "duration_seniority": 0.10,
    "transferability": 0.10,
    "specificity": 0.15,
}


class MatchStrength(StrEnum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class CoverageBand(StrEnum):
    NONE = "none"
    LIMITED = "limited"
    PARTIAL = "partial"
    SUBSTANTIAL = "substantial"
    COMPLETE = "complete"


class ScoreComponents(BaseModel):
    model_config = ConfigDict(frozen=True)

    semantic_relevance: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    evidence_strength: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    recency: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    duration_seniority: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    transferability: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    specificity: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)

    def weighted_score(self) -> float:
        return sum(
            getattr(self, component) * weight
            for component, weight in COMPONENT_WEIGHTS.items()
        )


def strength_for_score(score: float) -> MatchStrength:
    if score >= 0.8:
        return MatchStrength.STRONG
    if score >= 0.65:
        return MatchStrength.MODERATE
    return MatchStrength.WEAK


class CandidateEdge(BaseModel):
    model_config = ConfigDict(frozen=True)

    requirement_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    components: ScoreComponents
    score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    strength: MatchStrength

    @model_validator(mode="after")
    def validate_derived_values(self) -> Self:
        expected_score = self.components.weighted_score()
        if not isclose(self.score, expected_score, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("candidate edge score does not match its component breakdown")
        if self.strength is not strength_for_score(self.score):
            raise ValueError("candidate edge strength does not match its score")
        return self


class SelectedMatch(BaseModel):
    model_config = ConfigDict(frozen=True)

    requirement_id: str
    claim_id: str
    components: ScoreComponents
    score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    strength: MatchStrength
    objective_weight: float = Field(gt=0.0, allow_inf_nan=False)
    uncertain: bool


class CoverageSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_weight: float = Field(ge=0.0, allow_inf_nan=False)
    confident_matched_weight: float = Field(ge=0.0, allow_inf_nan=False)
    possible_matched_weight: float = Field(ge=0.0, allow_inf_nan=False)
    lower_bound: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    upper_bound: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    band: CoverageBand

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        if self.confident_matched_weight > self.possible_matched_weight:
            raise ValueError("confident matched weight cannot exceed possible weight")
        if self.possible_matched_weight > self.total_weight:
            raise ValueError("possible matched weight cannot exceed total weight")
        if self.lower_bound > self.upper_bound:
            raise ValueError("coverage lower bound cannot exceed upper bound")
        return self


class CareerMatchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    selected_matches: tuple[SelectedMatch, ...]
    mandatory_coverage: CoverageSummary
    preferred_coverage: CoverageSummary
    unmatched_requirements: tuple[RoleRequirement, ...]
    uncertain_matches: tuple[SelectedMatch, ...]
    uncertain_requirement_ids: tuple[str, ...]
    transferable_matches: tuple[SelectedMatch, ...]
    selected_evidence: tuple[CareerClaim, ...]
