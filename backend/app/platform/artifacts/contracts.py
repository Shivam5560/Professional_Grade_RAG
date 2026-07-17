from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ArtifactRevision(BaseModel):
    model_config = ConfigDict(frozen=True)

    revision_id: str = Field(min_length=1)
    artifact_id: str = Field(min_length=1)
    revision: int = Field(gt=0)
    owner_id: int = Field(gt=0)
    studio_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    run_id: str = Field(min_length=1)
    media_type: str = Field(min_length=3)
    content_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_ids: tuple[str, ...] = ()
    supersedes_revision_id: str | None = None
    created_at: datetime

    @field_validator(
        "revision_id",
        "artifact_id",
        "run_id",
        "media_type",
        "supersedes_revision_id",
    )
    @classmethod
    def reject_blank_identifier(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("artifact identifiers must not be blank")
        return value

    @field_validator("evidence_ids")
    @classmethod
    def reject_blank_evidence_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("artifact evidence identifiers must not be blank")
        return value

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("artifact timestamps must be timezone-aware")
        return value


def create_artifact_revision(
    *,
    artifact_id: str,
    owner_id: int,
    studio_id: str,
    run_id: str,
    media_type: str,
    content_digest: str,
    created_at: datetime,
    evidence_ids: tuple[str, ...] = (),
    previous: ArtifactRevision | None = None,
) -> ArtifactRevision:
    revision = 1
    supersedes = None
    if previous is not None:
        if previous.artifact_id != artifact_id:
            raise ValueError("artifact revision must retain its artifact_id")
        if previous.owner_id != owner_id or previous.studio_id != studio_id:
            raise ValueError("artifact revision must retain owner and studio")
        if previous.content_digest == content_digest:
            raise ValueError("a new artifact revision requires different content")
        if created_at < previous.created_at:
            raise ValueError("artifact revision cannot be created earlier than its parent")
        revision = previous.revision + 1
        supersedes = previous.revision_id

    return ArtifactRevision(
        revision_id=f"{artifact_id}:r{revision}",
        artifact_id=artifact_id,
        revision=revision,
        owner_id=owner_id,
        studio_id=studio_id,
        run_id=run_id,
        media_type=media_type,
        content_digest=content_digest,
        evidence_ids=evidence_ids,
        supersedes_revision_id=supersedes,
        created_at=created_at,
    )
