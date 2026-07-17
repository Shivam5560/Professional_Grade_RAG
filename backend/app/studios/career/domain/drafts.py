from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .claims import ClaimObject, ClaimValueKind, JsonScalar


class DraftTransformation(StrEnum):
    VERBATIM = "verbatim"
    COMPRESSED = "compressed"
    COMBINED = "combined"
    REORDERED = "reordered"
    REPHRASED = "rephrased"


def _validate_claim_ids(value: tuple[str, ...]) -> tuple[str, ...]:
    if any(not item.strip() for item in value):
        raise ValueError("source claim identifiers must not be blank")
    if len(set(value)) != len(value):
        raise ValueError("source claim identifiers must be unique")
    return value


class AssertedFact(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ClaimValueKind
    value: JsonScalar
    unit: str | None = Field(default=None, max_length=100)
    source_claim_ids: tuple[str, ...] = ()

    @field_validator("source_claim_ids")
    @classmethod
    def validate_claim_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _validate_claim_ids(value)

    @model_validator(mode="after")
    def validate_fact_value(self) -> Self:
        ClaimObject(kind=self.kind, value=self.value, unit=self.unit)
        return self


class AddedKeyword(BaseModel):
    model_config = ConfigDict(frozen=True)

    keyword: str = Field(min_length=1, max_length=200)
    source_claim_ids: tuple[str, ...] = ()

    @field_validator("keyword")
    @classmethod
    def reject_blank_keyword(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("added keyword must not be blank")
        return value

    @field_validator("source_claim_ids")
    @classmethod
    def validate_claim_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _validate_claim_ids(value)


class DraftBullet(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_claim_ids: tuple[str, ...] = ()
    transformation: DraftTransformation
    asserted_facts: tuple[AssertedFact, ...] = ()
    added_keywords: tuple[AddedKeyword, ...] = ()
    before_text: tuple[str, ...] = ()
    after_text: str = Field(min_length=1, max_length=4000)

    @field_validator("source_claim_ids")
    @classmethod
    def validate_claim_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _validate_claim_ids(value)

    @field_validator("before_text")
    @classmethod
    def validate_before_text(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("draft before text must not be blank")
        return value

    @field_validator("after_text")
    @classmethod
    def reject_blank_after_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("draft after text must not be blank")
        return value


def stable_draft_id(bullets: tuple[DraftBullet, ...]) -> str:
    canonical = json.dumps(
        [bullet.model_dump(mode="json") for bullet in bullets],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"draft-{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"


class ResumeDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^draft-[a-f0-9]{24}$")
    bullets: tuple[DraftBullet, ...]
    publication_ready: bool = False

    @model_validator(mode="after")
    def validate_stable_identifier(self) -> Self:
        if self.id != stable_draft_id(self.bullets):
            raise ValueError("draft id does not match canonical bullet content")
        return self

    @classmethod
    def create(
        cls,
        *,
        bullets: tuple[DraftBullet, ...],
        publication_ready: bool = False,
    ) -> "ResumeDraft":
        return cls(
            id=stable_draft_id(bullets),
            bullets=bullets,
            publication_ready=publication_ready,
        )

    def mark_publication_ready(self) -> "ResumeDraft":
        return ResumeDraft(
            id=self.id,
            bullets=self.bullets,
            publication_ready=True,
        )
