from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint

from app.db.database import Base
from app.platform.persistence.models import OWNER_FOREIGN_KEY


class DataDatasetSnapshotRecord(Base):
    __tablename__ = "data_analyst_dataset_snapshots"
    __table_args__ = (
        UniqueConstraint("owner_id", "content_digest", name="uq_data_snapshot_owner_digest"),
        Index("ix_data_snapshot_owner_id", "owner_id"),
    )

    id = Column(String(255), primary_key=True)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    media_type = Column(String(100), nullable=False)
    byte_size = Column(Integer, nullable=False)
    content_digest = Column(String(64), nullable=False)
    storage_key = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class DataDatasetProfileRecord(Base):
    __tablename__ = "data_analyst_dataset_profiles"
    __table_args__ = (Index("ix_data_profile_owner_snapshot", "owner_id", "snapshot_id"),)

    id = Column(String(255), primary_key=True)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    snapshot_id = Column(String(255), ForeignKey("data_analyst_dataset_snapshots.id", ondelete="CASCADE"), nullable=False, unique=True)
    payload = Column(JSON, nullable=False)
    payload_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class DataAnalysisPlanRecord(Base):
    __tablename__ = "data_analyst_plans"
    __table_args__ = (
        UniqueConstraint("owner_id", "run_id", name="uq_data_plan_owner_run"),
        Index("ix_data_plan_owner_run", "owner_id", "run_id"),
        Index("ix_data_plan_snapshot_id", "snapshot_id"),
    )

    id = Column(String(255), primary_key=True)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    run_id = Column(String(255), ForeignKey("studio_runs.id", ondelete="CASCADE"), nullable=False)
    snapshot_id = Column(String(255), ForeignKey("data_analyst_dataset_snapshots.id", ondelete="CASCADE"), nullable=False)
    payload = Column(JSON, nullable=False)
    payload_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class DataComputationRecord(Base):
    __tablename__ = "data_analyst_computations"
    __table_args__ = (
        Index("ix_data_computation_owner_run", "owner_id", "run_id"),
        Index("ix_data_computation_snapshot_id", "snapshot_id"),
    )

    id = Column(String(255), primary_key=True)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    run_id = Column(String(255), ForeignKey("studio_runs.id", ondelete="CASCADE"), nullable=False)
    snapshot_id = Column(String(255), ForeignKey("data_analyst_dataset_snapshots.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    payload_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class DataFindingClaimRecord(Base):
    __tablename__ = "data_analyst_finding_claims"
    __table_args__ = (
        Index("ix_data_claim_owner_run", "owner_id", "run_id"),
        Index("ix_data_claim_snapshot_id", "snapshot_id"),
    )

    id = Column(String(255), primary_key=True)
    owner_id = Column(Integer, ForeignKey(OWNER_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    run_id = Column(String(255), ForeignKey("studio_runs.id", ondelete="CASCADE"), nullable=False)
    snapshot_id = Column(String(255), ForeignKey("data_analyst_dataset_snapshots.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    payload_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
