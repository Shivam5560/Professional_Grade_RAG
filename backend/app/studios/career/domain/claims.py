from __future__ import annotations

import hashlib
import json
from datetime import date
from enum import StrEnum
from math import isfinite
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.platform.evidence import VerificationStatus

JsonScalar = str | int | float | bool


class ClaimSubjectKind(StrEnum):
    PERSON = "person"
    ROLE = "role"
    EMPLOYER = "employer"
    PROJECT = "project"
    EDUCATION = "education"
    CERTIFICATION = "certification"
    SKILL = "skill"


class ClaimValueKind(StrEnum):
    EMPLOYER = "employer"
    TITLE = "title"
    DATE = "date"
    SKILL = "skill"
    DEGREE = "degree"
    METRIC = "metric"
    RESPONSIBILITY = "responsibility"
    OUTCOME = "outcome"
    PROJECT = "project"
    CERTIFICATION = "certification"
    LOCATION = "location"
    WORK_MODE = "work-mode"


class ClaimPredicate(StrEnum):
    WORKED_AT = "worked-at"
    HELD_TITLE = "held-title"
    HAS_SKILL = "has-skill"
    EARNED_DEGREE = "earned-degree"
    OCCURRED_ON = "occurred-on"
    PERFORMED = "performed"
    ACHIEVED = "achieved"
    MEASURED = "measured"
    WORKED_ON = "worked-on"
    EARNED_CERTIFICATION = "earned-certification"
    LOCATED_IN = "located-in"


class SourceSpan(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str = Field(min_length=1, max_length=200)
    locator: str = Field(min_length=1, max_length=500)
    exact_text: str = Field(min_length=1, max_length=4000)

    @field_validator("source_id", "locator", "exact_text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source span fields must not be blank")
        return value


class TemporalScope(BaseModel):
    model_config = ConfigDict(frozen=True)

    start: date | None = None
    end: date | None = None
    label: str | None = Field(default=None, max_length=200)

    @field_validator("label")
    @classmethod
    def normalize_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        if self.start is None and self.end is None and self.label is None:
            raise ValueError("temporal scope requires a date or descriptive label")
        if self.start is not None and self.end is not None and self.end < self.start:
            raise ValueError("temporal scope end cannot precede start")
        return self

    def overlaps(self, other: "TemporalScope") -> bool:
        if self.start is not None and other.end is not None and self.start > other.end:
            return False
        if other.start is not None and self.end is not None and other.start > self.end:
            return False
        if self.start is None and self.end is None:
            return self.label == other.label
        if other.start is None and other.end is None:
            return self.label == other.label
        return True


class ClaimSubject(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ClaimSubjectKind
    id: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=500)

    @field_validator("id", "label")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("claim subject fields must not be blank")
        return value


class ClaimObject(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ClaimValueKind
    value: JsonScalar
    unit: str | None = Field(default=None, max_length=100)

    @field_validator("value")
    @classmethod
    def validate_json_scalar(cls, value: JsonScalar) -> JsonScalar:
        if isinstance(value, str) and not value.strip():
            raise ValueError("claim object value must not be blank")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("numeric claim object value must be finite")
        return value

    @field_validator("unit")
    @classmethod
    def normalize_unit(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_metric(self) -> Self:
        if self.kind is ClaimValueKind.METRIC:
            if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
                raise ValueError("metric claim values must be numeric")
            if self.unit is None:
                raise ValueError("metric claim values require a unit")
        return self


class ClaimContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    employer_id: str | None = Field(default=None, max_length=200)
    project_id: str | None = Field(default=None, max_length=200)

    @field_validator("employer_id", "project_id")
    @classmethod
    def reject_blank_identifier(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("claim context identifiers must not be blank")
        return value


def stable_claim_id(
    *,
    subject: ClaimSubject,
    predicate: ClaimPredicate,
    object: ClaimObject,
    source_spans: tuple[SourceSpan, ...],
    temporal_scope: TemporalScope,
    context: ClaimContext,
    related_claim_ids: tuple[str, ...] = (),
) -> str:
    ordered_spans = sorted(
        (span.model_dump(mode="json") for span in source_spans),
        key=lambda item: (item["source_id"], item["locator"], item["exact_text"]),
    )
    identity = {
        "subject": subject.model_dump(mode="json"),
        "predicate": predicate.value,
        "object": object.model_dump(mode="json"),
        "source_spans": ordered_spans,
        "temporal_scope": temporal_scope.model_dump(mode="json"),
        "context": context.model_dump(mode="json"),
        "related_claim_ids": sorted(related_claim_ids),
    }
    canonical = json.dumps(
        identity,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"claim-{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"


class CareerClaim(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^claim-[a-f0-9]{24}$")
    subject: ClaimSubject
    predicate: ClaimPredicate
    object: ClaimObject
    source_spans: tuple[SourceSpan, ...] = Field(min_length=1)
    temporal_scope: TemporalScope
    verification_status: VerificationStatus
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    verifier_id: str = Field(min_length=1, max_length=200)
    context: ClaimContext = Field(default_factory=ClaimContext)
    related_claim_ids: tuple[str, ...] = ()

    @field_validator("verifier_id")
    @classmethod
    def reject_blank_verifier(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("verifier identity must not be blank")
        return value

    @field_validator("source_spans")
    @classmethod
    def reject_duplicate_spans(
        cls, value: tuple[SourceSpan, ...]
    ) -> tuple[SourceSpan, ...]:
        identities = {
            (span.source_id, span.locator, span.exact_text) for span in value
        }
        if len(identities) != len(value):
            raise ValueError("claim source spans must be unique")
        return value

    @field_validator("related_claim_ids")
    @classmethod
    def validate_related_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("related claim identifiers must not be blank")
        if len(set(value)) != len(value):
            raise ValueError("related claim identifiers must be unique")
        return value

    @model_validator(mode="after")
    def validate_stable_identifier(self) -> Self:
        expected = stable_claim_id(
            subject=self.subject,
            predicate=self.predicate,
            object=self.object,
            source_spans=self.source_spans,
            temporal_scope=self.temporal_scope,
            context=self.context,
            related_claim_ids=self.related_claim_ids,
        )
        if self.id != expected:
            raise ValueError("claim id does not match canonical claim content")
        return self

    @classmethod
    def create(
        cls,
        *,
        subject: ClaimSubject,
        predicate: ClaimPredicate,
        object: ClaimObject,
        source_spans: tuple[SourceSpan, ...],
        temporal_scope: TemporalScope,
        verification_status: VerificationStatus,
        confidence: float,
        verifier_id: str,
        context: ClaimContext | None = None,
        related_claim_ids: tuple[str, ...] = (),
    ) -> "CareerClaim":
        canonical_context = context or ClaimContext()
        canonical_spans = tuple(
            sorted(
                source_spans,
                key=lambda span: (span.source_id, span.locator, span.exact_text),
            )
        )
        canonical_related_ids = tuple(sorted(related_claim_ids))
        return cls(
            id=stable_claim_id(
                subject=subject,
                predicate=predicate,
                object=object,
                source_spans=canonical_spans,
                temporal_scope=temporal_scope,
                context=canonical_context,
                related_claim_ids=canonical_related_ids,
            ),
            subject=subject,
            predicate=predicate,
            object=object,
            source_spans=canonical_spans,
            temporal_scope=temporal_scope,
            verification_status=verification_status,
            confidence=confidence,
            verifier_id=verifier_id,
            context=canonical_context,
            related_claim_ids=canonical_related_ids,
        )
