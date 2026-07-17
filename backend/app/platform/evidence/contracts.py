from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from math import isfinite
from types import MappingProxyType
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_serializer,
    field_validator,
)


def _validate_json_value(value: Any, *, path: str = "parameters") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{path} contains a non-finite number")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains a non-string key")
            _validate_json_value(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_json_value(item, path=f"{path}[{index}]")
        return
    raise ValueError(f"{path} contains unsupported value type {type(value).__name__}")


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise ValueError(f"unsupported JSON value type {type(value).__name__}")


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


class EvidenceKind(StrEnum):
    COMPUTATION = "computation"
    CLAIM = "claim"
    DERIVED = "derived"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    DISPUTED = "disputed"
    REJECTED = "rejected"


class ComputationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, validate_default=True)

    kind: Literal[EvidenceKind.COMPUTATION] = EvidenceKind.COMPUTATION
    id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    dataset_snapshot_id: str = Field(min_length=1)
    method_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    method_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    parameters: Mapping[str, JsonValue] = Field(default_factory=dict)
    random_seed: int | None = None
    assumptions: Mapping[str, str] = Field(default_factory=dict)
    output_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact_ids: tuple[str, ...] = ()

    @field_validator("id", "run_id", "dataset_snapshot_id")
    @classmethod
    def reject_blank_identifier(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence identifiers must not be blank")
        return value

    @field_validator("artifact_ids")
    @classmethod
    def reject_blank_artifact_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("evidence identifiers must not be blank")
        return value

    @field_validator("parameters", mode="before")
    @classmethod
    def require_json_parameters(cls, value: Any) -> Any:
        _validate_json_value(value)
        return value

    @field_validator("parameters", "assumptions")
    @classmethod
    def freeze_mappings(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return _freeze(value)

    @field_serializer("parameters", "assumptions")
    def serialize_mappings(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return _thaw(value)


class ClaimEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal[EvidenceKind.CLAIM] = EvidenceKind.CLAIM
    id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    snippet: str | None = Field(default=None, max_length=1000)
    normalized_claim: str = Field(min_length=3, max_length=2000)
    verification_status: VerificationStatus
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("id", "source_id", "locator", "normalized_claim")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("claim evidence fields must not be blank")
        return value


class DerivedEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal[EvidenceKind.DERIVED] = EvidenceKind.DERIVED
    id: str = Field(min_length=1)
    parent_evidence_ids: tuple[str, ...] = Field(min_length=1)
    transformation: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    transformation_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    output_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("id")
    @classmethod
    def reject_blank_identifier(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("derived evidence identifiers must not be blank")
        return value

    @field_validator("parent_evidence_ids")
    @classmethod
    def reject_blank_parent_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("derived evidence identifiers must not be blank")
        return value
