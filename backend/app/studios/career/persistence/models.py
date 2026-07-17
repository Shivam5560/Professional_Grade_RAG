from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.db.database import Base
from app.platform.persistence.models import OWNER_FOREIGN_KEY


class CareerSourceRecord(Base):
    __tablename__ = "career_sources"
    __table_args__ = (Index("ix_career_sources_owner_created", "owner_id", "created_at"),)

    id = Column(String(255), primary_key=True)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    media_type = Column(String(100), nullable=False)
    content_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class CareerClaimRevisionRecord(Base):
    __tablename__ = "career_claim_revisions"
    __table_args__ = (
        UniqueConstraint("logical_claim_id", "revision", name="uq_career_claim_logical_revision"),
        Index("ix_career_claim_revisions_owner_logical", "owner_id", "logical_claim_id"),
        Index("ix_career_claim_revisions_owner_source", "owner_id", "source_id"),
    )

    revision_id = Column(String(510), primary_key=True)
    logical_claim_id = Column(String(255), nullable=False)
    claim_id = Column(String(255), nullable=False)
    revision = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    source_id = Column(String(255), ForeignKey("career_sources.id", ondelete="CASCADE"), nullable=False)
    supersedes_revision_id = Column(String(510), ForeignKey("career_claim_revisions.revision_id"), nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)
    status = Column(String(32), nullable=False)
    verifier_id = Column(String(255), nullable=False)
    reviewer_id = Column(Integer, nullable=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class CareerRoleRecord(Base):
    __tablename__ = "career_roles"
    __table_args__ = (Index("ix_career_roles_owner_created", "owner_id", "created_at"),)

    id = Column(String(255), primary_key=True)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class CareerRequirementRecord(Base):
    __tablename__ = "career_requirements"
    __table_args__ = (
        UniqueConstraint("role_id", "requirement_id", name="uq_career_role_requirement"),
        Index("ix_career_requirements_owner_role", "owner_id", "role_id"),
    )

    record_id = Column(String(510), primary_key=True)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    role_id = Column(String(255), ForeignKey("career_roles.id", ondelete="CASCADE"), nullable=False)
    requirement_id = Column(String(255), nullable=False)
    source_id = Column(String(255), nullable=False)
    locator = Column(String(500), nullable=False)
    exact_text = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class CareerMatchRecord(Base):
    __tablename__ = "career_matches"
    __table_args__ = (Index("ix_career_matches_owner_role", "owner_id", "role_id"),)

    id = Column(String(255), primary_key=True)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    role_id = Column(String(255), ForeignKey("career_roles.id", ondelete="CASCADE"), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class CareerRequirementMatchRecord(Base):
    __tablename__ = "career_requirement_matches"
    __table_args__ = (
        UniqueConstraint("match_id", "requirement_record_id", name="uq_career_match_requirement"),
        UniqueConstraint("match_id", "claim_revision_id", name="uq_career_match_claim"),
        Index("ix_career_requirement_matches_owner_match", "owner_id", "match_id"),
    )

    id = Column(String(1020), primary_key=True)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    match_id = Column(String(255), ForeignKey("career_matches.id", ondelete="CASCADE"), nullable=False)
    requirement_record_id = Column(String(510), ForeignKey("career_requirements.record_id"), nullable=False)
    claim_revision_id = Column(String(510), ForeignKey("career_claim_revisions.revision_id"), nullable=False)
    score = Column(String(64), nullable=False)


class CareerDraftRecord(Base):
    __tablename__ = "career_drafts"
    __table_args__ = (
        UniqueConstraint("owner_id", "run_id", "draft_id", name="uq_career_run_draft"),
        Index("ix_career_drafts_owner_run", "owner_id", "run_id"),
    )

    record_id = Column(String(765), primary_key=True)
    draft_id = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    run_id = Column(String(255), ForeignKey("studio_runs.id", ondelete="CASCADE"), nullable=False)
    match_id = Column(String(255), ForeignKey("career_matches.id"), nullable=False)
    payload = Column(JSON, nullable=False)
    truth_valid = Column(Boolean, nullable=False, default=False)
    approval_id = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class CareerDraftClaimRecord(Base):
    __tablename__ = "career_draft_claims"
    __table_args__ = (
        UniqueConstraint("draft_record_id", "bullet_index", "claim_revision_id", name="uq_career_draft_bullet_claim"),
        Index("ix_career_draft_claims_owner_draft", "owner_id", "draft_record_id"),
    )

    id = Column(String(1020), primary_key=True)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    draft_record_id = Column(String(765), ForeignKey("career_drafts.record_id", ondelete="CASCADE"), nullable=False)
    bullet_index = Column(Integer, nullable=False)
    claim_revision_id = Column(String(510), ForeignKey("career_claim_revisions.revision_id"), nullable=False)
    transformation = Column(String(32), nullable=False)
