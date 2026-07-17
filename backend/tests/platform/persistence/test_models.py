from __future__ import annotations

from datetime import datetime, timezone
from math import nan

import pytest
from pydantic import BaseModel
from sqlalchemy import CheckConstraint, UniqueConstraint, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.platform.approvals import ApprovalRequest
from app.platform.artifacts import ArtifactRevision
from app.platform.evidence import ComputationEvidence
from app.platform.quality import QualityMetadata
from app.platform.runtime import StudioRun


def _now() -> datetime:
    return datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def _digest(character: str = "a") -> str:
    return character * 64


def _contracts() -> tuple[BaseModel, ...]:
    now = _now()
    return (
        StudioRun(
            id="run-1",
            owner_id=7,
            studio_id="data-analyst-v2",
            operation="analyze",
            idempotency_key="request-1",
            input_fingerprint=_digest(),
            created_at=now,
            updated_at=now,
        ),
        ComputationEvidence(
            id="evidence-1",
            run_id="run-1",
            dataset_snapshot_id="snapshot-1",
            method_id="pearson-correlation",
            method_version="1.0.0",
            parameters={"columns": ["revenue", "cost"], "alpha": 0.05},
            assumptions={"linearity": "checked"},
            output_digest=_digest("b"),
        ),
        ArtifactRevision(
            revision_id="artifact-1:r1",
            artifact_id="artifact-1",
            revision=1,
            owner_id=7,
            studio_id="data-analyst-v2",
            run_id="run-1",
            media_type="application/json",
            content_digest=_digest("c"),
            evidence_ids=("evidence-1",),
            created_at=now,
        ),
        ApprovalRequest(
            id="approval-1",
            run_id="run-1",
            owner_id=7,
            decision_type="publish-draft",
            proposed_changes=("draft-1",),
            evidence_ids=("evidence-1",),
            created_at=now,
            updated_at=now,
        ),
        QualityMetadata(
            algorithm_versions={"planner": "1.0.0"},
            confidence_components={"coverage": 0.85},
            latency_ms=3.5,
            input_tokens=0,
            output_tokens=0,
            estimated_cost_usd=0.0,
            trace_id="trace-1",
        ),
    )


def test_records_share_application_base_and_owner_run_indexes() -> None:
    from app.platform.persistence.models import (
        StudioApprovalRecord,
        StudioArtifactRecord,
        StudioEvidenceRecord,
        StudioQualityResultRecord,
        StudioRunRecord,
    )

    record_types = (
        StudioRunRecord,
        StudioEvidenceRecord,
        StudioArtifactRecord,
        StudioApprovalRecord,
        StudioQualityResultRecord,
    )
    assert all(issubclass(record_type, Base) for record_type in record_types)

    for record_type in record_types:
        table = inspect(record_type).local_table
        assert table.c.owner_id.nullable is False

    for record_type in record_types[1:]:
        table = inspect(record_type).local_table
        assert table.c.run_id.nullable is False
        assert table.c.run_id.index is True or any(
            table.c.run_id in index.columns for index in table.indexes
        )


def test_run_idempotency_and_artifact_revision_uniqueness_are_declared() -> None:
    from app.platform.persistence.models import StudioArtifactRecord, StudioRunRecord

    run_unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in StudioRunRecord.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    artifact_unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in StudioArtifactRecord.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("owner_id", "studio_id", "idempotency_key") in run_unique_columns
    assert ("artifact_id", "revision") in artifact_unique_columns


def test_artifact_lineage_has_database_enforced_immediate_parent_constraint() -> None:
    from app.db.models import User
    from app.platform.persistence.models import StudioArtifactRecord, StudioRunRecord

    checks = {
        constraint.name
        for constraint in StudioArtifactRecord.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert "ck_studio_artifacts_immediate_parent" in checks

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[User.__table__, StudioRunRecord.__table__, StudioArtifactRecord.__table__],
    )
    now = _now()
    with Session(engine) as session:
        session.add(
            StudioRunRecord(
                id="run-1",
                owner_id=7,
                studio_id="data-analyst-v2",
                operation="analyze",
                idempotency_key="request-1",
                input_fingerprint=_digest(),
                state="queued",
                progress=0.0,
                cancellation_requested=False,
                created_at=now,
                updated_at=now,
            )
        )
        session.flush()
        session.add(
            StudioArtifactRecord(
                revision_id="artifact-1:r2",
                artifact_id="artifact-1",
                revision=2,
                owner_id=7,
                studio_id="data-analyst-v2",
                run_id="run-1",
                media_type="application/json",
                content_digest=_digest("c"),
                evidence_ids=[],
                supersedes_revision_id="artifact-1:r7",
                created_at=now,
            )
        )
        with pytest.raises(IntegrityError):
            session.flush()


@pytest.mark.parametrize("contract", _contracts(), ids=lambda item: type(item).__name__)
def test_public_contracts_round_trip_as_independent_json(contract: BaseModel) -> None:
    from app.platform.persistence.serialization import hydrate_contract, serialize_contract

    payload = serialize_contract(contract)
    hydrated = hydrate_contract(type(contract), payload)

    assert hydrated == contract
    assert hydrated is not contract
    assert payload == contract.model_dump(mode="json")

    payload["persistence_probe"] = True
    assert "persistence_probe" not in contract.model_dump(mode="json")


def test_serialization_rejects_non_finite_json_values() -> None:
    from app.platform.persistence.serialization import SerializationError, serialize_contract

    class UnsafeContract(BaseModel):
        value: float

    with pytest.raises(SerializationError, match="finite JSON"):
        serialize_contract(UnsafeContract(value=nan))
