from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.db.database import Base


OWNER_FOREIGN_KEY = "users_nexus_rag.id"


class StudioRunRecord(Base):
    __tablename__ = "studio_runs"
    __table_args__ = (
        UniqueConstraint(
            "owner_id",
            "studio_id",
            "idempotency_key",
            name="uq_studio_runs_owner_studio_idempotency",
        ),
        Index("ix_studio_runs_owner_id", "owner_id"),
        Index("ix_studio_runs_owner_state", "owner_id", "state"),
    )

    id = Column(String(255), primary_key=True)
    owner_id = Column(
        Integer,
        ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"),
        nullable=False,
    )
    studio_id = Column(String(100), nullable=False)
    operation = Column(String(100), nullable=False)
    idempotency_key = Column(String(200), nullable=False)
    input_fingerprint = Column(String(64), nullable=False)
    state = Column(String(32), nullable=False)
    current_step = Column(String(255), nullable=True)
    progress = Column(Float, nullable=False, default=0.0)
    failure_code = Column(String(100), nullable=True)
    cancellation_requested = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class StudioEvidenceRecord(Base):
    __tablename__ = "studio_evidence"
    __table_args__ = (
        Index("ix_studio_evidence_owner_run", "owner_id", "run_id"),
    )

    id = Column(String(255), primary_key=True)
    owner_id = Column(
        Integer,
        ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"),
        nullable=False,
    )
    run_id = Column(
        String(255),
        ForeignKey("studio_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_kind = Column(String(32), nullable=False)
    contract_name = Column(String(100), nullable=False)
    payload_version = Column(Integer, nullable=False, default=1)
    payload = Column(JSON, nullable=False)
    payload_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

class StudioArtifactRecord(Base):
    __tablename__ = "studio_artifacts"
    __table_args__ = (
        UniqueConstraint(
            "artifact_id",
            "revision",
            name="uq_studio_artifacts_artifact_revision",
        ),
        CheckConstraint("revision >= 1", name="ck_studio_artifacts_positive_revision"),
        CheckConstraint(
            "(revision = 1 AND supersedes_revision_id IS NULL) OR "
            "(revision > 1 AND supersedes_revision_id = "
            "artifact_id || ':' || 'r' || CAST(revision - 1 AS VARCHAR))",
            name="ck_studio_artifacts_immediate_parent",
        ),
        Index("ix_studio_artifacts_owner_artifact", "owner_id", "artifact_id"),
    )

    revision_id = Column(String(255), primary_key=True)
    artifact_id = Column(String(255), nullable=False)
    revision = Column(Integer, nullable=False)
    owner_id = Column(
        Integer,
        ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"),
        nullable=False,
    )
    studio_id = Column(String(100), nullable=False)
    run_id = Column(
        String(255),
        ForeignKey("studio_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    media_type = Column(String(255), nullable=False)
    content_digest = Column(String(64), nullable=False)
    evidence_ids = Column(JSON, nullable=False)
    is_current = Column(Boolean, nullable=False, default=True)
    supersedes_revision_id = Column(
        String(255),
        ForeignKey("studio_artifacts.revision_id"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False)


class StudioApprovalRecord(Base):
    __tablename__ = "studio_approvals"
    __table_args__ = (
        Index("ix_studio_approvals_owner_run", "owner_id", "run_id"),
    )

    id = Column(String(255), primary_key=True)
    owner_id = Column(
        Integer,
        ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"),
        nullable=False,
    )
    run_id = Column(
        String(255),
        ForeignKey("studio_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision_type = Column(String(100), nullable=False)
    proposed_changes = Column(JSON, nullable=False)
    evidence_ids = Column(JSON, nullable=False)
    status = Column(String(32), nullable=False)
    reviewer_id = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class StudioQualityResultRecord(Base):
    __tablename__ = "studio_quality_results"
    __table_args__ = (
        Index("ix_studio_quality_results_owner_run", "owner_id", "run_id"),
    )

    id = Column(String(255), primary_key=True)
    owner_id = Column(
        Integer,
        ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"),
        nullable=False,
    )
    run_id = Column(
        String(255),
        ForeignKey("studio_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payload_version = Column(Integer, nullable=False, default=1)
    payload = Column(JSON, nullable=False)
    payload_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
