from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class ValidationIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    message: str = Field(min_length=3, max_length=500)
    status: ValidationStatus
    critical: bool = False


class QualityMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    algorithm_versions: dict[str, str] = Field(default_factory=dict)
    model_versions: dict[str, str] = Field(default_factory=dict)
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    confidence_components: dict[str, float] = Field(default_factory=dict)
    validations: tuple[ValidationIssue, ...] = ()
    warnings: tuple[str, ...] = ()
    abstention_reason: str | None = None
    latency_ms: float = Field(ge=0.0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)
    trace_id: str
    evaluation_run_id: str | None = None

    @model_validator(mode="after")
    def validate_quality_state(self) -> "QualityMetadata":
        invalid = [
            name
            for name, value in self.confidence_components.items()
            if not 0.0 <= value <= 1.0
        ]
        if invalid:
            raise ValueError(
                f"confidence components must be between 0 and 1: {sorted(invalid)}"
            )
        has_critical_error = any(
            issue.critical and issue.status == ValidationStatus.ERROR
            for issue in self.validations
        )
        if has_critical_error and not self.abstention_reason:
            raise ValueError("critical validation errors require abstention_reason")
        return self


class AIResult(BaseModel, Generic[OutputT]):
    output: OutputT | None
    evidence: tuple[EvidenceReference, ...] = ()
    quality: QualityMetadata
