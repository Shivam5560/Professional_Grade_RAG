from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from math import isclose, isfinite
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.platform.evidence import ComputationEvidence
from app.platform.quality import AIResult
from app.platform.runtime import StudioRun

from .json_values import freeze_json, thaw_json

SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"
KEBAB_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
DIGEST_PATTERN = r"^[a-f0-9]{64}$"


class FrozenContract(BaseModel):
    model_config = ConfigDict(frozen=True, validate_default=True)


class ColumnSemanticType(StrEnum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    TEXT = "text"
    IDENTIFIER = "identifier"


class MethodCostClass(StrEnum):
    LOW = "low"
    MEDIUM = "medium"


class AssumptionStatus(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class FindingLanguageClass(StrEnum):
    OBSERVATION = "observation"
    ASSOCIATION = "association"
    PREDICTION = "prediction"
    HYPOTHESIS = "hypothesis"
    RECOMMENDATION = "recommendation"


class ColumnProfile(FrozenContract):
    name: str = Field(min_length=1)
    dtype: str = Field(min_length=1)
    semantic_type: ColumnSemanticType
    non_null_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    missing_fraction: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    unique_count: int = Field(ge=0)
    unique_fraction: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    skewness: float | None = Field(default=None, allow_inf_nan=False)

    @field_validator("name", "dtype")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("column fields must not be blank")
        return value

    @model_validator(mode="after")
    def validate_statistics(self) -> "ColumnProfile":
        total = self.non_null_count + self.missing_count
        expected_missing = self.missing_count / total if total else 0.0
        expected_unique = (
            self.unique_count / self.non_null_count if self.non_null_count else 0.0
        )
        if self.unique_count > self.non_null_count:
            raise ValueError("unique_count cannot exceed non_null_count")
        if not isclose(self.missing_fraction, expected_missing, abs_tol=1e-12):
            raise ValueError("missing_fraction does not match column counts")
        if not isclose(self.unique_fraction, expected_unique, abs_tol=1e-12):
            raise ValueError("unique_fraction does not match column counts")
        return self


class DatasetProfile(FrozenContract):
    dataset_snapshot_id: str = Field(min_length=1)
    fingerprint: str = Field(pattern=DIGEST_PATTERN)
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    columns: tuple[ColumnProfile, ...] = ()

    @field_validator("dataset_snapshot_id")
    @classmethod
    def reject_blank_snapshot_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("dataset_snapshot_id must not be blank")
        return value

    @model_validator(mode="after")
    def validate_columns(self) -> "DatasetProfile":
        if self.column_count != len(self.columns):
            raise ValueError("column_count must match columns")
        names = [column.name for column in self.columns]
        if len(names) != len(set(names)):
            raise ValueError("column names must be unique")
        expected_rows = {
            column.non_null_count + column.missing_count for column in self.columns
        }
        if expected_rows and expected_rows != {self.row_count}:
            raise ValueError("column counts must match row_count")
        return self


class AnalysisIntent(FrozenContract):
    question: str = Field(min_length=3, max_length=2000)
    objective: str = Field(min_length=3, max_length=500)
    relationship_requested: bool = False
    business_context: Mapping[str, Any] = Field(default_factory=dict)

    @field_validator("question", "objective")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("analysis intent text must not be blank")
        return value

    @field_validator("business_context")
    @classmethod
    def freeze_context(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return freeze_json(value)

    @field_serializer("business_context")
    def serialize_context(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return thaw_json(value)


class MethodDefinition(FrozenContract):
    id: str = Field(pattern=KEBAB_PATTERN)
    version: str = Field(pattern=SEMVER_PATTERN)
    supported_semantic_types: tuple[ColumnSemanticType, ...] = Field(min_length=1)
    minimum_sample_size: int = Field(ge=1)
    required_assumptions: tuple[str, ...] = ()
    default_parameters: Mapping[str, Any] = Field(default_factory=dict)
    cost_class: MethodCostClass
    output_schema: str = Field(min_length=3, max_length=1000)
    limitations: tuple[str, ...] = ()
    implementation_digest: str = Field(pattern=DIGEST_PATTERN)

    @field_validator("required_assumptions", "limitations")
    @classmethod
    def validate_text_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("method text entries must not be blank")
        if len(value) != len(set(value)):
            raise ValueError("method text entries must be unique")
        return value

    @field_validator("default_parameters")
    @classmethod
    def freeze_parameters(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return freeze_json(value)

    @field_serializer("default_parameters")
    def serialize_parameters(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return thaw_json(value)


class PlanStep(FrozenContract):
    id: str = Field(pattern=KEBAB_PATTERN)
    method_id: str = Field(pattern=KEBAB_PATTERN)
    method_version: str = Field(pattern=SEMVER_PATTERN)
    input_columns: tuple[str, ...] = ()
    parameters: Mapping[str, Any] = Field(default_factory=dict)
    prerequisite_step_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    rationale: str = Field(min_length=3, max_length=1000)

    @field_validator("input_columns", "prerequisite_step_ids", "assumptions")
    @classmethod
    def validate_unique_text(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("plan entries must not be blank")
        if len(value) != len(set(value)):
            raise ValueError("plan entries must be unique")
        return value

    @field_validator("parameters")
    @classmethod
    def freeze_parameters(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return freeze_json(value)

    @field_serializer("parameters")
    def serialize_parameters(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return thaw_json(value)


class AnalysisPlan(FrozenContract):
    id: str = Field(min_length=1)
    dataset_snapshot_id: str = Field(min_length=1)
    registry_version: str = Field(pattern=SEMVER_PATTERN)
    steps: tuple[PlanStep, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_dag(self) -> "AnalysisPlan":
        step_ids = [step.id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("plan step IDs must be unique")
        known_ids = set(step_ids)
        for step in self.steps:
            unknown = set(step.prerequisite_step_ids) - known_ids
            if unknown:
                raise ValueError(
                    f"step {step.id} has unknown prerequisite IDs: {sorted(unknown)}"
                )
            if step.id in step.prerequisite_step_ids:
                raise ValueError("a step cannot depend on itself")

        dependencies = {
            step.id: set(step.prerequisite_step_ids) for step in self.steps
        }
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(step_id: str) -> None:
            if step_id in visiting:
                raise ValueError("analysis plan must be acyclic")
            if step_id in visited:
                return
            visiting.add(step_id)
            for dependency in dependencies[step_id]:
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in step_ids:
            visit(step_id)
        return self


class AssumptionResult(FrozenContract):
    name: str = Field(pattern=KEBAB_PATTERN)
    status: AssumptionStatus
    detail: str = Field(min_length=3, max_length=500)


class ComputationRecord(FrozenContract):
    id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    step_id: str = Field(pattern=KEBAB_PATTERN)
    dataset_snapshot_id: str = Field(min_length=1)
    method_id: str = Field(pattern=KEBAB_PATTERN)
    method_version: str = Field(pattern=SEMVER_PATTERN)
    parameters: Mapping[str, Any] = Field(default_factory=dict)
    random_seed: int | None = None
    code_digest: str = Field(pattern=DIGEST_PATTERN)
    assumption_results: tuple[AssumptionResult, ...] = ()
    output: Mapping[str, Any]
    output_digest: str = Field(pattern=DIGEST_PATTERN)
    warnings: tuple[str, ...] = ()
    artifact_ids: tuple[str, ...] = ()
    evidence: ComputationEvidence

    @field_validator("parameters", "output")
    @classmethod
    def freeze_payload(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return freeze_json(value)

    @field_serializer("parameters", "output")
    def serialize_payload(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return thaw_json(value)

    @field_validator("warnings", "artifact_ids")
    @classmethod
    def validate_unique_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("computation entries must not be blank")
        if len(value) != len(set(value)):
            raise ValueError("computation entries must be unique")
        return value

    @model_validator(mode="after")
    def validate_evidence(self) -> "ComputationRecord":
        expected = (
            self.run_id,
            self.dataset_snapshot_id,
            self.method_id,
            self.method_version,
            self.output_digest,
        )
        actual = (
            self.evidence.run_id,
            self.evidence.dataset_snapshot_id,
            self.evidence.method_id,
            self.evidence.method_version,
            self.evidence.output_digest,
        )
        if actual != expected:
            raise ValueError("computation evidence does not match its record")
        if thaw_json(self.parameters) != thaw_json(self.evidence.parameters):
            raise ValueError("computation evidence parameters do not match")
        if self.artifact_ids != self.evidence.artifact_ids:
            raise ValueError("computation evidence artifacts do not match")
        return self


class EvidenceLink(FrozenContract):
    evidence_id: str = Field(min_length=1)
    value_path: str = Field(pattern=r"^/output(?:/(?:[^~/]|~0|~1)+)+$")

    @field_validator("evidence_id")
    @classmethod
    def reject_blank_evidence_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence_id must not be blank")
        return value


ClaimValue = str | int | float | bool | None


class FindingClaim(FrozenContract):
    id: str = Field(min_length=1)
    subject: str = Field(min_length=1, max_length=500)
    predicate: str = Field(min_length=1, max_length=500)
    value: ClaimValue
    scope: Mapping[str, Any] = Field(default_factory=dict)
    evidence_links: tuple[EvidenceLink, ...] = Field(min_length=1)
    confidence_components: Mapping[str, float] = Field(default_factory=dict)
    language_class: FindingLanguageClass

    @field_validator("value")
    @classmethod
    def require_finite_value(cls, value: ClaimValue) -> ClaimValue:
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("claim values must be finite")
        return value

    @field_validator("scope")
    @classmethod
    def freeze_scope(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return freeze_json(value)

    @field_validator("confidence_components")
    @classmethod
    def freeze_confidence(
        cls, value: Mapping[str, float]
    ) -> Mapping[str, float]:
        if any(not name.strip() for name in value):
            raise ValueError("confidence names must not be blank")
        if any(not isfinite(score) or not 0.0 <= score <= 1.0 for score in value.values()):
            raise ValueError("confidence values must be finite and between 0 and 1")
        return freeze_json(value)

    @field_serializer("scope", "confidence_components")
    def serialize_claim_mapping(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return thaw_json(value)


class ClaimVerification(FrozenContract):
    claim_id: str = Field(min_length=1)
    accepted: bool
    issue_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_result(self) -> "ClaimVerification":
        if self.accepted and self.issue_codes:
            raise ValueError("accepted claims cannot contain issue codes")
        if not self.accepted and not self.issue_codes:
            raise ValueError("rejected claims require issue codes")
        return self


class AnalysisOutput(FrozenContract):
    claims: tuple[FindingClaim, ...]


class DataAnalystRunResult(FrozenContract):
    run_history: tuple[StudioRun, ...]
    profile: DatasetProfile
    plan: AnalysisPlan
    computations: tuple[ComputationRecord, ...]
    result: AIResult[AnalysisOutput]
