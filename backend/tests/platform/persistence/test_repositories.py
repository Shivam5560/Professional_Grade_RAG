from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.db.database import Base
from app.db.models import User
from app.platform.approvals import ApprovalDecision, ApprovalRequest, ApprovalStatus
from app.platform.artifacts import ArtifactRevision, create_artifact_revision
from app.platform.evidence import ComputationEvidence
from app.platform.quality import QualityMetadata
from app.platform.runtime import StudioRun, StudioRunState
from app.platform.persistence.models import (
    StudioApprovalRecord,
    StudioArtifactRecord,
    StudioEvidenceRecord,
    StudioQualityResultRecord,
    StudioRunRecord,
)
from app.platform.persistence.repositories import (
    ArtifactRevisionConflict,
    IdempotencyConflict,
    RecordAlreadyExists,
    RecordNotFound,
    StudioApprovalRepository,
    StudioArtifactRepository,
    StudioEvidenceRepository,
    StudioQualityRepository,
    StudioRunRepository,
)


NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def _digest(character: str = "a") -> str:
    return character * 64


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(
        engine,
        tables=[
            User.__table__,
            StudioRunRecord.__table__,
            StudioEvidenceRecord.__table__,
            StudioArtifactRecord.__table__,
            StudioApprovalRecord.__table__,
            StudioQualityResultRecord.__table__,
        ],
    )
    with Session(engine) as setup:
        setup.execute(
            User.__table__.insert(),
            [
                {"id": 1, "email": "one@example.test", "hashed_password": "x"},
                {"id": 2, "email": "two@example.test", "hashed_password": "x"},
            ],
        )
        setup.commit()

    with Session(engine, expire_on_commit=False) as test_session:
        yield test_session


def _run(
    *,
    run_id: str = "run-1",
    owner_id: int = 1,
    idempotency_key: str = "request-1",
    fingerprint: str | None = None,
) -> StudioRun:
    return StudioRun(
        id=run_id,
        owner_id=owner_id,
        studio_id="data-analyst-v2",
        operation="analyze",
        idempotency_key=idempotency_key,
        input_fingerprint=fingerprint or _digest(),
        created_at=NOW,
        updated_at=NOW,
    )


def _evidence(*, evidence_id: str = "evidence-1") -> ComputationEvidence:
    return ComputationEvidence(
        id=evidence_id,
        run_id="run-1",
        dataset_snapshot_id="snapshot-1",
        method_id="pearson-correlation",
        method_version="1.0.0",
        parameters={"columns": ["revenue", "cost"]},
        assumptions={"linearity": "checked"},
        output_digest=_digest("b"),
    )


def _approval(*, approval_id: str = "approval-1") -> ApprovalRequest:
    return ApprovalRequest(
        id=approval_id,
        run_id="run-1",
        owner_id=1,
        decision_type="publish-draft",
        proposed_changes=("draft-1",),
        evidence_ids=("evidence-1",),
        created_at=NOW,
        updated_at=NOW,
    )


def test_run_create_is_idempotent_for_same_fingerprint(session: Session) -> None:
    repository = StudioRunRepository(session)

    first = repository.create(_run(run_id="run-original"), owner_id=1)
    second = repository.create(_run(run_id="run-retry"), owner_id=1)

    assert second == first
    assert second.id == "run-original"
    assert session.query(StudioRunRecord).count() == 1


def test_run_idempotency_key_rejects_a_different_fingerprint(session: Session) -> None:
    repository = StudioRunRepository(session)
    repository.create(_run(), owner_id=1)

    with pytest.raises(IdempotencyConflict, match="different input fingerprint"):
        repository.create(_run(run_id="run-2", fingerprint=_digest("f")), owner_id=1)


def test_run_reads_transitions_and_cancellation_are_owner_scoped(
    session: Session,
) -> None:
    repository = StudioRunRepository(session)
    repository.create(_run(), owner_id=1)

    with pytest.raises(RecordNotFound):
        repository.get("run-1", owner_id=2)
    with pytest.raises(RecordNotFound):
        repository.request_cancellation("run-1", owner_id=2, now=NOW + timedelta(seconds=1))

    running = repository.transition(
        "run-1",
        StudioRunState.RUNNING,
        owner_id=1,
        now=NOW + timedelta(seconds=1),
        current_step="profile",
        progress=0.25,
    )
    assert running.state is StudioRunState.RUNNING
    assert running.current_step == "profile"


def test_transition_hydrates_then_uses_shared_transition_helper(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.platform.persistence.repositories as repository_module

    repository = StudioRunRepository(session)
    repository.create(_run(), owner_id=1)
    calls: list[StudioRun] = []
    actual_transition = repository_module.transition_run

    def tracking_transition(run: StudioRun, *args, **kwargs) -> StudioRun:
        calls.append(run)
        return actual_transition(run, *args, **kwargs)

    monkeypatch.setattr(repository_module, "transition_run", tracking_transition)
    repository.transition(
        "run-1",
        StudioRunState.RUNNING,
        owner_id=1,
        now=NOW + timedelta(seconds=1),
    )

    assert len(calls) == 1
    assert isinstance(calls[0], StudioRun)
    assert calls[0].state is StudioRunState.QUEUED


def test_cancellation_requested_run_can_only_become_cancelled(session: Session) -> None:
    repository = StudioRunRepository(session)
    repository.create(_run(), owner_id=1)
    repository.transition(
        "run-1",
        StudioRunState.RUNNING,
        owner_id=1,
        now=NOW + timedelta(seconds=1),
    )
    requested = repository.request_cancellation(
        "run-1",
        owner_id=1,
        now=NOW + timedelta(seconds=2),
    )
    assert requested.cancellation_requested is True

    with pytest.raises(ValueError, match="can only transition to cancelled"):
        repository.transition(
            "run-1",
            StudioRunState.SUCCEEDED,
            owner_id=1,
            now=NOW + timedelta(seconds=3),
        )

    cancelled = repository.transition(
        "run-1",
        StudioRunState.CANCELLED,
        owner_id=1,
        now=NOW + timedelta(seconds=3),
    )
    assert cancelled.state is StudioRunState.CANCELLED


def test_evidence_persistence_hydrates_contract_and_rejects_cross_owner(
    session: Session,
) -> None:
    StudioRunRepository(session).create(_run(), owner_id=1)
    repository = StudioEvidenceRepository(session)

    with pytest.raises(RecordNotFound):
        repository.add("run-1", _evidence(), owner_id=2, created_at=NOW)

    stored = repository.add("run-1", _evidence(), owner_id=1, created_at=NOW)
    assert stored == _evidence()
    assert repository.get("evidence-1", owner_id=1) == _evidence()
    with pytest.raises(RecordNotFound):
        repository.get("evidence-1", owner_id=2)


def test_approval_decision_is_owner_authorized_and_preserves_audit(
    session: Session,
) -> None:
    StudioRunRepository(session).create(_run(), owner_id=1)
    StudioEvidenceRepository(session).add(
        "run-1", _evidence(), owner_id=1, created_at=NOW
    )
    repository = StudioApprovalRepository(session)
    repository.add(_approval(), owner_id=1)

    with pytest.raises(RecordNotFound):
        repository.decide(
            "approval-1",
            ApprovalDecision.APPROVE,
            owner_id=2,
            now=NOW + timedelta(minutes=1),
        )

    decided = repository.decide(
        "approval-1",
        ApprovalDecision.APPROVE,
        owner_id=1,
        now=NOW + timedelta(minutes=1),
        comment="Reviewed against source evidence",
    )
    assert decided.status is ApprovalStatus.APPROVED
    assert decided.reviewer_id == 1
    assert decided.comment == "Reviewed against source evidence"
    assert decided.updated_at == NOW + timedelta(minutes=1)


def test_artifact_revision_compare_and_swap_rejects_stale_parent(
    session: Session,
) -> None:
    StudioRunRepository(session).create(_run(), owner_id=1)
    repository = StudioArtifactRepository(session)
    first = create_artifact_revision(
        artifact_id="artifact-1",
        owner_id=1,
        studio_id="data-analyst-v2",
        run_id="run-1",
        media_type="application/json",
        content_digest=_digest("c"),
        created_at=NOW,
        evidence_ids=(),
    )
    repository.create(first, owner_id=1, expected_parent_revision_id=None)
    next_time = NOW + timedelta(minutes=1)
    winning_child = create_artifact_revision(
        artifact_id="artifact-1",
        owner_id=1,
        studio_id="data-analyst-v2",
        run_id="run-1",
        media_type="application/json",
        content_digest=_digest("d"),
        created_at=next_time,
        previous=first,
    )
    stale_child = ArtifactRevision.model_validate(
        {
            **winning_child.model_dump(),
            "content_digest": _digest("e"),
        }
    )

    assert repository.create(
        winning_child,
        owner_id=1,
        expected_parent_revision_id=first.revision_id,
    ) == winning_child
    with pytest.raises(ArtifactRevisionConflict, match="stale artifact parent"):
        repository.create(
            stale_child,
            owner_id=1,
            expected_parent_revision_id=first.revision_id,
        )

    assert repository.get_latest("artifact-1", owner_id=1) == winning_child


def test_artifact_duplicate_revision_and_cross_owner_access_reject(
    session: Session,
) -> None:
    StudioRunRepository(session).create(_run(), owner_id=1)
    repository = StudioArtifactRepository(session)
    first = create_artifact_revision(
        artifact_id="artifact-1",
        owner_id=1,
        studio_id="data-analyst-v2",
        run_id="run-1",
        media_type="application/json",
        content_digest=_digest("c"),
        created_at=NOW,
    )
    repository.create(first, owner_id=1, expected_parent_revision_id=None)

    with pytest.raises(RecordAlreadyExists, match="artifact revision"):
        repository.create(first, owner_id=1, expected_parent_revision_id=None)
    with pytest.raises(RecordNotFound):
        repository.get_latest("artifact-1", owner_id=2)


def test_quality_results_are_owner_scoped_and_contract_hydrated(session: Session) -> None:
    StudioRunRepository(session).create(_run(), owner_id=1)
    quality = QualityMetadata(
        algorithm_versions={"planner": "1.0.0"},
        confidence_components={"coverage": 0.9},
        latency_ms=4.0,
        input_tokens=0,
        output_tokens=0,
        estimated_cost_usd=0.0,
        trace_id="trace-1",
    )
    repository = StudioQualityRepository(session)
    assert repository.add(
        "quality-1",
        "run-1",
        quality,
        owner_id=1,
        created_at=NOW,
    ) == quality
    assert repository.get("quality-1", owner_id=1) == quality
    with pytest.raises(RecordNotFound):
        repository.get("quality-1", owner_id=2)


def test_rollback_leaves_no_partial_evidence_artifact_or_approval(
    session: Session,
) -> None:
    StudioRunRepository(session).create(_run(), owner_id=1)
    session.commit()

    StudioEvidenceRepository(session).add(
        "run-1", _evidence(), owner_id=1, created_at=NOW
    )
    artifact = create_artifact_revision(
        artifact_id="artifact-rollback",
        owner_id=1,
        studio_id="data-analyst-v2",
        run_id="run-1",
        media_type="application/json",
        content_digest=_digest("f"),
        created_at=NOW,
    )
    StudioArtifactRepository(session).create(
        artifact,
        owner_id=1,
        expected_parent_revision_id=None,
    )
    StudioApprovalRepository(session).add(_approval(), owner_id=1)
    session.rollback()

    assert session.query(StudioEvidenceRecord).count() == 0
    assert session.query(StudioArtifactRecord).count() == 0
    assert session.query(StudioApprovalRecord).count() == 0
