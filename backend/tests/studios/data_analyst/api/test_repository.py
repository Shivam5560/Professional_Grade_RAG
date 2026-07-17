from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import Session

from app.db.database import Base
from app.db.models import User
from app.platform.persistence import RecordAlreadyExists, RecordNotFound
from app.platform.runtime import StudioRun
from app.studios.data_analyst import DataAnalystSpecialist
from app.studios.data_analyst.persistence import (
    DataAnalystRepository,
    DataComputationRecord,
    DataDatasetSnapshotRecord,
    DataFindingClaimRecord,
)

NOW = datetime(2026, 7, 18, 10, 0, tzinfo=timezone.utc)


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    event.listen(engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all(
            [
                User(id=7, email="owner@example.test", hashed_password="x"),
                User(id=8, email="other@example.test", hashed_password="x"),
            ]
        )
        db.commit()
        yield db


def _result():
    frame = pd.DataFrame(
        {"revenue": [10.0, 20.0, 30.0], "profit": [1.0, 3.0, 5.0]}
    )
    return DataAnalystSpecialist().analyze(
        frame,
        "How are revenue and profit related?",
        owner_id=7,
        run_id="run-1",
        idempotency_key="idem-1",
        now=NOW,
    )


def test_models_declare_owner_run_snapshot_indexes() -> None:
    for model in (DataDatasetSnapshotRecord, DataComputationRecord, DataFindingClaimRecord):
        indexes = inspect(model).local_table.indexes
        indexed_columns = {column.name for index in indexes for column in index.columns}
        assert "owner_id" in indexed_columns
    assert "run_id" in {
        column.name
        for index in inspect(DataComputationRecord).local_table.indexes
        for column in index.columns
    }
    assert "snapshot_id" in {
        column.name
        for index in inspect(DataComputationRecord).local_table.indexes
        for column in index.columns
    }


def test_repository_round_trips_frozen_snapshot_profile_plan_computations_and_claims(session: Session) -> None:
    result = _result()
    repo = DataAnalystRepository(session)
    snapshot = repo.add_snapshot(
        snapshot_id=result.profile.dataset_snapshot_id,
        owner_id=7,
        filename="metrics.csv",
        media_type="text/csv",
        byte_size=42,
        content_digest="a" * 64,
        storage_key="opaque/key",
        profile=result.profile,
        created_at=NOW,
    )
    repo.persist_run_result(result, owner_id=7, created_at=NOW)
    session.commit()

    assert snapshot.profile == result.profile
    assert repo.get_snapshot(snapshot.id, owner_id=7).profile == result.profile
    assert repo.get_plan("run-1", owner_id=7) == result.plan
    assert repo.list_computations("run-1", owner_id=7) == result.computations
    assert repo.list_claims("run-1", owner_id=7) == result.result.output.claims
    with pytest.raises(RecordNotFound):
        repo.get_snapshot(snapshot.id, owner_id=8)
    with pytest.raises(RecordNotFound):
        repo.list_computations("run-1", owner_id=8)


def test_computation_and_claim_identities_are_append_only(session: Session) -> None:
    result = _result()
    repo = DataAnalystRepository(session)
    repo.add_snapshot(
        snapshot_id=result.profile.dataset_snapshot_id,
        owner_id=7,
        filename="metrics.csv",
        media_type="text/csv",
        byte_size=42,
        content_digest="a" * 64,
        storage_key="opaque/key",
        profile=result.profile,
        created_at=NOW,
    )
    repo.persist_run_result(result, owner_id=7, created_at=NOW)
    with pytest.raises(RecordAlreadyExists):
        repo.persist_run_result(result, owner_id=7, created_at=NOW)


def test_caller_rollback_removes_partial_analysis_records(session: Session) -> None:
    result = _result()
    repo = DataAnalystRepository(session)
    repo.add_snapshot(
        snapshot_id=result.profile.dataset_snapshot_id,
        owner_id=7,
        filename="metrics.csv",
        media_type="text/csv",
        byte_size=42,
        content_digest="a" * 64,
        storage_key="opaque/key",
        profile=result.profile,
        created_at=NOW,
    )
    repo.persist_run_result(result, owner_id=7, created_at=NOW)
    session.rollback()

    with pytest.raises(RecordNotFound):
        repo.get_snapshot(result.profile.dataset_snapshot_id, owner_id=7)

