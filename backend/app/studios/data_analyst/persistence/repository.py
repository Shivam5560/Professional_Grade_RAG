from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.platform.persistence import RecordAlreadyExists, RecordNotFound, StudioRunRepository
from app.studios.data_analyst.domain import (
    AnalysisPlan,
    ComputationRecord,
    DataAnalystRunResult,
    DatasetProfile,
    FindingClaim,
)

from .models import (
    DataAnalysisPlanRecord,
    DataComputationRecord,
    DataDatasetProfileRecord,
    DataDatasetSnapshotRecord,
    DataFindingClaimRecord,
)


@contextmanager
def _savepoint(session: Session):
    connection = session.connection()
    if connection.dialect.name == "sqlite" and not connection.connection.in_transaction:
        connection.exec_driver_sql("BEGIN")
    with session.begin_nested():
        yield


def _payload(contract) -> dict[str, object]:
    return contract.model_dump(mode="json")


def _digest(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _hydrate(row, contract_type):
    if _digest(row.payload) != row.payload_digest:
        raise ValueError("stored analysis payload digest mismatch")
    return contract_type.model_validate(row.payload)


@dataclass(frozen=True)
class DatasetSnapshot:
    id: str
    owner_id: int
    filename: str
    media_type: str
    byte_size: int
    content_digest: str
    storage_key: str
    profile: DatasetProfile
    created_at: datetime


class DataAnalystRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_snapshot(
        self,
        *,
        snapshot_id: str,
        owner_id: int,
        filename: str,
        media_type: str,
        byte_size: int,
        content_digest: str,
        storage_key: str,
        profile: DatasetProfile,
        created_at: datetime,
    ) -> DatasetSnapshot:
        if owner_id <= 0 or profile.dataset_snapshot_id != snapshot_id:
            raise ValueError("snapshot ownership and profile identity must be valid")
        profile_payload = _payload(profile)
        snapshot = DataDatasetSnapshotRecord(
            id=snapshot_id, owner_id=owner_id, filename=filename, media_type=media_type,
            byte_size=byte_size, content_digest=content_digest, storage_key=storage_key,
            created_at=created_at,
        )
        profile_record = DataDatasetProfileRecord(
            id=f"profile-{snapshot_id}", owner_id=owner_id, snapshot_id=snapshot_id,
            payload=profile_payload, payload_digest=_digest(profile_payload), created_at=created_at,
        )
        try:
            with _savepoint(self.session):
                self.session.add(snapshot)
                self.session.flush()
                self.session.add(profile_record)
                self.session.flush()
        except IntegrityError as exc:
            existing = self.session.execute(
                select(DataDatasetSnapshotRecord).where(
                    DataDatasetSnapshotRecord.owner_id == owner_id,
                    DataDatasetSnapshotRecord.content_digest == content_digest,
                )
            ).scalar_one_or_none()
            if existing is not None:
                return self.get_snapshot(existing.id, owner_id=owner_id)
            raise RecordAlreadyExists("dataset snapshot identity already exists") from exc
        return DatasetSnapshot(snapshot_id, owner_id, filename, media_type, byte_size, content_digest, storage_key, profile, created_at)

    def get_snapshot(self, snapshot_id: str, *, owner_id: int) -> DatasetSnapshot:
        row = self.session.execute(
            select(DataDatasetSnapshotRecord, DataDatasetProfileRecord)
            .join(DataDatasetProfileRecord, DataDatasetProfileRecord.snapshot_id == DataDatasetSnapshotRecord.id)
            .where(DataDatasetSnapshotRecord.id == snapshot_id, DataDatasetSnapshotRecord.owner_id == owner_id)
        ).one_or_none()
        if row is None:
            raise RecordNotFound("dataset snapshot not found")
        snapshot, profile = row
        hydrated = _hydrate(profile, DatasetProfile)
        return DatasetSnapshot(snapshot.id, snapshot.owner_id, snapshot.filename, snapshot.media_type, snapshot.byte_size, snapshot.content_digest, snapshot.storage_key, hydrated, _aware(snapshot.created_at))

    def persist_run_result(self, result: DataAnalystRunResult, *, owner_id: int, created_at: datetime) -> None:
        if not result.run_history or any(run.owner_id != owner_id for run in result.run_history):
            raise RecordNotFound("analysis run not found")
        run_id = result.run_history[0].id
        run_repository = StudioRunRepository(self.session)
        try:
            run_repository.get(run_id, owner_id=owner_id)
        except RecordNotFound:
            run_repository.create(result.run_history[0], owner_id=owner_id)
        self.get_snapshot(result.profile.dataset_snapshot_id, owner_id=owner_id)
        plan_payload = _payload(result.plan)
        rows: list[object] = [
            DataAnalysisPlanRecord(
                id=result.plan.id, owner_id=owner_id, run_id=run_id,
                snapshot_id=result.profile.dataset_snapshot_id, payload=plan_payload,
                payload_digest=_digest(plan_payload), created_at=created_at,
            )
        ]
        rows.extend(
            DataComputationRecord(
                id=item.id, owner_id=owner_id, run_id=run_id,
                snapshot_id=item.dataset_snapshot_id, sequence=index,
                payload=(payload := _payload(item)), payload_digest=_digest(payload), created_at=created_at,
            )
            for index, item in enumerate(result.computations)
        )
        claims = result.result.output.claims if result.result.output is not None else ()
        rows.extend(
            DataFindingClaimRecord(
                id=item.id, owner_id=owner_id, run_id=run_id,
                snapshot_id=result.profile.dataset_snapshot_id, sequence=index,
                payload=(payload := _payload(item)), payload_digest=_digest(payload), created_at=created_at,
            )
            for index, item in enumerate(claims)
        )
        try:
            with _savepoint(self.session):
                self.session.add_all(rows)
                self.session.flush()
        except IntegrityError as exc:
            raise RecordAlreadyExists("analysis result identity already exists") from exc

    def get_plan(self, run_id: str, *, owner_id: int) -> AnalysisPlan:
        StudioRunRepository(self.session).get(run_id, owner_id=owner_id)
        row = self.session.execute(select(DataAnalysisPlanRecord).where(DataAnalysisPlanRecord.run_id == run_id, DataAnalysisPlanRecord.owner_id == owner_id)).scalar_one_or_none()
        if row is None:
            raise RecordNotFound("analysis plan not found")
        return _hydrate(row, AnalysisPlan)

    def list_computations(self, run_id: str, *, owner_id: int) -> tuple[ComputationRecord, ...]:
        StudioRunRepository(self.session).get(run_id, owner_id=owner_id)
        rows = self.session.execute(select(DataComputationRecord).where(DataComputationRecord.run_id == run_id, DataComputationRecord.owner_id == owner_id).order_by(DataComputationRecord.sequence, DataComputationRecord.id)).scalars()
        return tuple(_hydrate(row, ComputationRecord) for row in rows)

    def list_claims(self, run_id: str, *, owner_id: int) -> tuple[FindingClaim, ...]:
        StudioRunRepository(self.session).get(run_id, owner_id=owner_id)
        rows = self.session.execute(select(DataFindingClaimRecord).where(DataFindingClaimRecord.run_id == run_id, DataFindingClaimRecord.owner_id == owner_id).order_by(DataFindingClaimRecord.sequence, DataFindingClaimRecord.id)).scalars()
        return tuple(_hydrate(row, FindingClaim) for row in rows)
