from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from math import isfinite
from types import MappingProxyType
from typing import Generic, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

OutputT = TypeVar("OutputT")


class ValidationStatus(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"


class EvidenceReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    snippet: str | None = Field(default=None, max_length=1000)
    relevance: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("source_id", "locator")
    @classmethod
    def require_non_blank_identifier(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence identifiers must not be blank")
        return value


class ValidationIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    message: str = Field(min_length=3, max_length=500)
    status: ValidationStatus
    critical: bool = False


class QualityMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    algorithm_versions: Mapping[str, str] = Field(default_factory=dict)
    model_versions: Mapping[str, str] = Field(default_factory=dict)
    prompt_versions: Mapping[str, str] = Field(default_factory=dict)
    confidence_components: Mapping[str, float] = Field(default_factory=dict)
    validations: tuple[ValidationIssue, ...] = ()
    warnings: tuple[str, ...] = ()
    abstention_reason: str | None = None
    latency_ms: float = Field(ge=0.0, allow_inf_nan=False)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0, allow_inf_nan=False)
    trace_id: str
    evaluation_run_id: str | None = None

    @field_validator("algorithm_versions", "model_versions", "prompt_versions")
    @classmethod
    def freeze_version_mapping(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        if any(not key.strip() for key in value):
            raise ValueError("version mapping keys must not be blank")
        if any(not version.strip() for version in value.values()):
            raise ValueError("version mapping values must not be blank")
        return MappingProxyType(dict(value))

    @field_validator("confidence_components")
    @classmethod
    def freeze_confidence_components(
        cls, value: Mapping[str, float]
    ) -> Mapping[str, float]:
        invalid_names = [name for name in value if not name.strip()]
        if invalid_names:
            raise ValueError("confidence component names must not be blank")
        invalid_values = [
            name
            for name, component in value.items()
            if not isfinite(component) or not 0.0 <= component <= 1.0
        ]
        if invalid_values:
            raise ValueError(
                "confidence components must be finite and between 0 and 1: "
                f"{sorted(invalid_values)}"
            )
        return MappingProxyType(dict(value))

    @field_validator("abstention_reason")
    @classmethod
    def normalize_abstention_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("evaluation_run_id")
    @classmethod
    def normalize_evaluation_run_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("trace_id")
    @classmethod
    def require_non_blank_trace_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("trace_id must not be blank")
        return value

    @field_serializer(
        "algorithm_versions",
        "model_versions",
        "prompt_versions",
        "confidence_components",
    )
    def serialize_mapping(
        self, value: Mapping[str, str] | Mapping[str, float]
    ) -> dict[str, str | float]:
        return dict(value)

    @model_validator(mode="after")
    def validate_quality_state(self) -> "QualityMetadata":
        has_critical_error = any(
            issue.critical and issue.status == ValidationStatus.ERROR
            for issue in self.validations
        )
        if has_critical_error and not self.abstention_reason:
            raise ValueError("critical validation errors require abstention_reason")
        return self


class AIResult(BaseModel, Generic[OutputT]):
    """Frozen envelope; an arbitrary OutputT may still contain mutable state."""

    model_config = ConfigDict(frozen=True)

    output: OutputT | None
    evidence: tuple[EvidenceReference, ...] = ()
    quality: QualityMetadata
