from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, TypeAlias

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.platform.approvals import (
    ApprovalDecision,
    ApprovalRequest,
    decide_approval,
)
from app.platform.artifacts import ArtifactRevision
from app.platform.evidence import (
    ClaimEvidence,
    ComputationEvidence,
    DerivedEvidence,
)
from app.platform.persistence.models import (
    StudioApprovalRecord,
    StudioArtifactRecord,
    StudioEvidenceRecord,
    StudioQualityResultRecord,
    StudioRunRecord,
)
from app.platform.persistence.serialization import hydrate_contract, serialize_contract
from app.platform.quality import QualityMetadata
from app.platform.runtime import (
    StudioRun,
    StudioRunState,
    request_run_cancellation,
    transition_run,
)


EvidenceContract: TypeAlias = ComputationEvidence | ClaimEvidence | DerivedEvidence


class PersistenceDomainError(ValueError):
    """Base class for stable specialist persistence errors."""


class RecordNotFound(PersistenceDomainError):
    """Raised for missing and cross-owner resources without leaking existence."""


class RecordAlreadyExists(PersistenceDomainError):
    """Raised when an append-only identity is already stored."""


class IdempotencyConflict(PersistenceDomainError):
    """Raised when a key is replayed with a different request fingerprint."""


class ArtifactRevisionConflict(PersistenceDomainError):
    """Raised when an artifact compare-and-swap parent is stale."""


def _require_owner(owner_id: int) -> None:
    if owner_id <= 0:
        raise ValueError("owner_id must be positive")


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _payload_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@contextmanager
def _rollback_safe_savepoint(session: Session) -> Iterator[None]:
    """Keep uniqueness handling inside the caller-owned transaction.

    Python's SQLite driver does not start a transaction for SELECT statements
    in legacy transaction mode. A SAVEPOINT opened after an owner lookup would
    then become the outermost transaction, and releasing it would commit the
    write. Start that real outer transaction explicitly on SQLite; PostgreSQL
    and other transactional drivers already do this themselves.
    """

    connection = session.connection()
    if connection.dialect.name == "sqlite":
        driver_connection = connection.connection
        if not driver_connection.in_transaction:
            connection.exec_driver_sql("BEGIN")
    with session.begin_nested():
        yield


def _run_from_record(record: StudioRunRecord) -> StudioRun:
    return StudioRun.model_validate(
        {
            "id": record.id,
            "owner_id": record.owner_id,
            "studio_id": record.studio_id,
            "operation": record.operation,
            "idempotency_key": record.idempotency_key,
            "input_fingerprint": record.input_fingerprint,
            "state": record.state,
            "current_step": record.current_step,
            "progress": record.progress,
            "failure_code": record.failure_code,
            "cancellation_requested": record.cancellation_requested,
            "created_at": _aware(record.created_at),
            "updated_at": _aware(record.updated_at),
        }
    )


def _apply_run(record: StudioRunRecord, run: StudioRun) -> None:
    record.state = run.state.value
    record.current_step = run.current_step
    record.progress = run.progress
    record.failure_code = run.failure_code
    record.cancellation_requested = run.cancellation_requested
    record.updated_at = run.updated_at


class StudioRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _owned_record(self, run_id: str, *, owner_id: int) -> StudioRunRecord:
        _require_owner(owner_id)
        record = self.session.execute(
            select(StudioRunRecord).where(
                StudioRunRecord.id == run_id,
                StudioRunRecord.owner_id == owner_id,
            )
        ).scalar_one_or_none()
        if record is None:
            raise RecordNotFound("studio run not found")
        return record

    def create(self, run: StudioRun, *, owner_id: int) -> StudioRun:
        _require_owner(owner_id)
        if run.owner_id != owner_id:
            raise RecordNotFound("studio run not found")

        idempotent_record = self.session.execute(
            select(StudioRunRecord).where(
                StudioRunRecord.owner_id == owner_id,
                StudioRunRecord.studio_id == run.studio_id,
                StudioRunRecord.idempotency_key == run.idempotency_key,
            )
        ).scalar_one_or_none()
        if idempotent_record is not None:
            if idempotent_record.input_fingerprint != run.input_fingerprint:
                raise IdempotencyConflict(
                    "idempotency key was already used with a different input fingerprint"
                )
            return _run_from_record(idempotent_record)

        record = StudioRunRecord(
            id=run.id,
            owner_id=owner_id,
            studio_id=run.studio_id,
            operation=run.operation,
            idempotency_key=run.idempotency_key,
            input_fingerprint=run.input_fingerprint,
            state=run.state.value,
            current_step=run.current_step,
            progress=run.progress,
            failure_code=run.failure_code,
            cancellation_requested=run.cancellation_requested,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )
        try:
            with _rollback_safe_savepoint(self.session):
                self.session.add(record)
                self.session.flush()
        except IntegrityError as exc:
            raced_record = self.session.execute(
                select(StudioRunRecord).where(
                    StudioRunRecord.owner_id == owner_id,
                    StudioRunRecord.studio_id == run.studio_id,
                    StudioRunRecord.idempotency_key == run.idempotency_key,
                )
            ).scalar_one_or_none()
            if raced_record is not None:
                if raced_record.input_fingerprint != run.input_fingerprint:
                    raise IdempotencyConflict(
                        "idempotency key was already used with a different input fingerprint"
                    ) from exc
                return _run_from_record(raced_record)
            raise RecordAlreadyExists("studio run identity already exists") from exc
        return _run_from_record(record)

    def get(self, run_id: str, *, owner_id: int) -> StudioRun:
        return _run_from_record(self._owned_record(run_id, owner_id=owner_id))

    def transition(
        self,
        run_id: str,
        target: StudioRunState,
        *,
        owner_id: int,
        now: datetime,
        current_step: str | None = None,
        progress: float | None = None,
        failure_code: str | None = None,
    ) -> StudioRun:
        record = self._owned_record(run_id, owner_id=owner_id)
        transitioned = transition_run(
            _run_from_record(record),
            target,
            now=now,
            current_step=current_step,
            progress=progress,
            failure_code=failure_code,
        )
        _apply_run(record, transitioned)
        self.session.flush()
        return transitioned

    def request_cancellation(
        self,
        run_id: str,
        *,
        owner_id: int,
        now: datetime,
    ) -> StudioRun:
        record = self._owned_record(run_id, owner_id=owner_id)
        requested = request_run_cancellation(_run_from_record(record), now=now)
        _apply_run(record, requested)
        self.session.flush()
        return requested


_EVIDENCE_TYPES: dict[str, type[EvidenceContract]] = {
    evidence_type.__name__: evidence_type
    for evidence_type in (ComputationEvidence, ClaimEvidence, DerivedEvidence)
}


class StudioEvidenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(
        self,
        run_id: str,
        evidence: EvidenceContract,
        *,
        owner_id: int,
        created_at: datetime,
    ) -> EvidenceContract:
        StudioRunRepository(self.session)._owned_record(run_id, owner_id=owner_id)
        evidence_run_id = getattr(evidence, "run_id", run_id)
        if evidence_run_id != run_id:
            raise ValueError("evidence run_id must match its persisted run")
        payload = serialize_contract(evidence)
        record = StudioEvidenceRecord(
            id=evidence.id,
            owner_id=owner_id,
            run_id=run_id,
            evidence_kind=evidence.kind.value,
            contract_name=type(evidence).__name__,
            payload_version=1,
            payload=payload,
            payload_digest=_payload_digest(payload),
            created_at=created_at,
        )
        try:
            with _rollback_safe_savepoint(self.session):
                self.session.add(record)
                self.session.flush()
        except IntegrityError as exc:
            raise RecordAlreadyExists("evidence identity already exists") from exc
        return evidence

    def get(self, evidence_id: str, *, owner_id: int) -> EvidenceContract:
        _require_owner(owner_id)
        record = self.session.execute(
            select(StudioEvidenceRecord).where(
                StudioEvidenceRecord.id == evidence_id,
                StudioEvidenceRecord.owner_id == owner_id,
            )
        ).scalar_one_or_none()
        if record is None:
            raise RecordNotFound("studio evidence not found")
        contract_type = _EVIDENCE_TYPES.get(record.contract_name)
        if contract_type is None:
            raise PersistenceDomainError("unsupported stored evidence contract")
        return hydrate_contract(contract_type, record.payload)

    def list_for_run(
        self,
        run_id: str,
        *,
        owner_id: int,
    ) -> tuple[EvidenceContract, ...]:
        StudioRunRepository(self.session)._owned_record(run_id, owner_id=owner_id)
        records = self.session.execute(
            select(StudioEvidenceRecord)
            .where(
                StudioEvidenceRecord.run_id == run_id,
                StudioEvidenceRecord.owner_id == owner_id,
            )
            .order_by(StudioEvidenceRecord.created_at, StudioEvidenceRecord.id)
        ).scalars()
        hydrated: list[EvidenceContract] = []
        for record in records:
            contract_type = _EVIDENCE_TYPES.get(record.contract_name)
            if contract_type is None:
                raise PersistenceDomainError("unsupported stored evidence contract")
            hydrated.append(hydrate_contract(contract_type, record.payload))
        return tuple(hydrated)


def _artifact_from_record(record: StudioArtifactRecord) -> ArtifactRevision:
    return ArtifactRevision.model_validate(
        {
            "revision_id": record.revision_id,
            "artifact_id": record.artifact_id,
            "revision": record.revision,
            "owner_id": record.owner_id,
            "studio_id": record.studio_id,
            "run_id": record.run_id,
            "media_type": record.media_type,
            "content_digest": record.content_digest,
            "evidence_ids": tuple(record.evidence_ids),
            "supersedes_revision_id": record.supersedes_revision_id,
            "created_at": _aware(record.created_at),
        }
    )


class StudioArtifactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        revision: ArtifactRevision,
        *,
        owner_id: int,
        expected_parent_revision_id: str | None,
    ) -> ArtifactRevision:
        if revision.owner_id != owner_id:
            raise RecordNotFound("artifact revision not found")
        run_record = StudioRunRepository(self.session)._owned_record(
            revision.run_id,
            owner_id=owner_id,
        )
        if run_record.studio_id != revision.studio_id:
            raise ValueError("artifact studio_id must match its run")
        if expected_parent_revision_id != revision.supersedes_revision_id:
            raise ArtifactRevisionConflict("stale artifact parent")

        record = StudioArtifactRecord(
            revision_id=revision.revision_id,
            artifact_id=revision.artifact_id,
            revision=revision.revision,
            owner_id=owner_id,
            studio_id=revision.studio_id,
            run_id=revision.run_id,
            media_type=revision.media_type,
            content_digest=revision.content_digest,
            evidence_ids=list(revision.evidence_ids),
            is_current=True,
            supersedes_revision_id=revision.supersedes_revision_id,
            created_at=revision.created_at,
        )
        try:
            with _rollback_safe_savepoint(self.session):
                if revision.revision > 1:
                    result = self.session.execute(
                        update(StudioArtifactRecord)
                        .where(
                            StudioArtifactRecord.revision_id
                            == expected_parent_revision_id,
                            StudioArtifactRecord.artifact_id == revision.artifact_id,
                            StudioArtifactRecord.revision == revision.revision - 1,
                            StudioArtifactRecord.owner_id == owner_id,
                            StudioArtifactRecord.studio_id == revision.studio_id,
                            StudioArtifactRecord.is_current.is_(True),
                        )
                        .values(is_current=False)
                    )
                    if result.rowcount != 1:
                        raise ArtifactRevisionConflict("stale artifact parent")
                self.session.add(record)
                self.session.flush()
        except IntegrityError as exc:
            raise RecordAlreadyExists("artifact revision already exists") from exc
        return revision

    def get_revision(self, revision_id: str, *, owner_id: int) -> ArtifactRevision:
        _require_owner(owner_id)
        record = self.session.execute(
            select(StudioArtifactRecord).where(
                StudioArtifactRecord.revision_id == revision_id,
                StudioArtifactRecord.owner_id == owner_id,
            )
        ).scalar_one_or_none()
        if record is None:
            raise RecordNotFound("artifact revision not found")
        return _artifact_from_record(record)

    def get_latest(self, artifact_id: str, *, owner_id: int) -> ArtifactRevision:
        _require_owner(owner_id)
        record = self.session.execute(
            select(StudioArtifactRecord)
            .where(
                StudioArtifactRecord.artifact_id == artifact_id,
                StudioArtifactRecord.owner_id == owner_id,
                StudioArtifactRecord.is_current.is_(True),
            )
            .order_by(StudioArtifactRecord.revision.desc())
        ).scalars().first()
        if record is None:
            raise RecordNotFound("artifact revision not found")
        return _artifact_from_record(record)


def _approval_from_record(record: StudioApprovalRecord) -> ApprovalRequest:
    return ApprovalRequest.model_validate(
        {
            "id": record.id,
            "run_id": record.run_id,
            "owner_id": record.owner_id,
            "decision_type": record.decision_type,
            "proposed_changes": tuple(record.proposed_changes),
            "evidence_ids": tuple(record.evidence_ids),
            "status": record.status,
            "reviewer_id": record.reviewer_id,
            "comment": record.comment,
            "created_at": _aware(record.created_at),
            "updated_at": _aware(record.updated_at),
        }
    )


class StudioApprovalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _owned_record(
        self,
        approval_id: str,
        *,
        owner_id: int,
    ) -> StudioApprovalRecord:
        _require_owner(owner_id)
        record = self.session.execute(
            select(StudioApprovalRecord).where(
                StudioApprovalRecord.id == approval_id,
                StudioApprovalRecord.owner_id == owner_id,
            )
        ).scalar_one_or_none()
        if record is None:
            raise RecordNotFound("studio approval not found")
        return record

    def add(self, request: ApprovalRequest, *, owner_id: int) -> ApprovalRequest:
        if request.owner_id != owner_id:
            raise RecordNotFound("studio approval not found")
        StudioRunRepository(self.session)._owned_record(
            request.run_id,
            owner_id=owner_id,
        )
        evidence_ids = set(request.evidence_ids)
        matched_ids = set(
            self.session.execute(
                select(StudioEvidenceRecord.id).where(
                    StudioEvidenceRecord.owner_id == owner_id,
                    StudioEvidenceRecord.run_id == request.run_id,
                    StudioEvidenceRecord.id.in_(evidence_ids),
                )
            ).scalars()
        )
        if matched_ids != evidence_ids:
            raise RecordNotFound("approval evidence not found")

        record = StudioApprovalRecord(
            id=request.id,
            owner_id=owner_id,
            run_id=request.run_id,
            decision_type=request.decision_type,
            proposed_changes=list(request.proposed_changes),
            evidence_ids=list(request.evidence_ids),
            status=request.status.value,
            reviewer_id=request.reviewer_id,
            comment=request.comment,
            created_at=request.created_at,
            updated_at=request.updated_at,
        )
        try:
            with _rollback_safe_savepoint(self.session):
                self.session.add(record)
                self.session.flush()
        except IntegrityError as exc:
            raise RecordAlreadyExists("approval identity already exists") from exc
        return request

    def get(self, approval_id: str, *, owner_id: int) -> ApprovalRequest:
        return _approval_from_record(
            self._owned_record(approval_id, owner_id=owner_id)
        )

    def decide(
        self,
        approval_id: str,
        decision: ApprovalDecision,
        *,
        owner_id: int,
        now: datetime,
        comment: str | None = None,
    ) -> ApprovalRequest:
        record = self._owned_record(approval_id, owner_id=owner_id)
        decided = decide_approval(
            _approval_from_record(record),
            decision,
            reviewer_id=owner_id,
            now=now,
            comment=comment,
        )
        record.status = decided.status.value
        record.reviewer_id = decided.reviewer_id
        record.comment = decided.comment
        record.updated_at = decided.updated_at
        self.session.flush()
        return decided


class StudioQualityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(
        self,
        result_id: str,
        run_id: str,
        quality: QualityMetadata,
        *,
        owner_id: int,
        created_at: datetime,
    ) -> QualityMetadata:
        StudioRunRepository(self.session)._owned_record(run_id, owner_id=owner_id)
        payload = serialize_contract(quality)
        record = StudioQualityResultRecord(
            id=result_id,
            owner_id=owner_id,
            run_id=run_id,
            payload_version=1,
            payload=payload,
            payload_digest=_payload_digest(payload),
            created_at=created_at,
        )
        try:
            with _rollback_safe_savepoint(self.session):
                self.session.add(record)
                self.session.flush()
        except IntegrityError as exc:
            raise RecordAlreadyExists("quality result identity already exists") from exc
        return quality

    def get(self, result_id: str, *, owner_id: int) -> QualityMetadata:
        _require_owner(owner_id)
        record = self.session.execute(
            select(StudioQualityResultRecord).where(
                StudioQualityResultRecord.id == result_id,
                StudioQualityResultRecord.owner_id == owner_id,
            )
        ).scalar_one_or_none()
        if record is None:
            raise RecordNotFound("quality result not found")
        return hydrate_contract(QualityMetadata, record.payload)
