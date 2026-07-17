from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.db.database import Base, get_db
from app.db.models import User
from app.studios.data_analyst.api.router import get_snapshot_store, router
from app.studios.data_analyst.api.service import InMemorySnapshotStore


@pytest.fixture()
def client_bundle():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    with Session(engine) as seed:
        seed.add_all([
            User(id=7, email="owner@example.test", hashed_password="x"),
            User(id=8, email="other@example.test", hashed_password="x"),
        ])
        seed.commit()

    app = FastAPI()
    app.include_router(router)
    store = InMemorySnapshotStore()
    current = {"id": 7}

    def db_override():
        with Session(engine) as session:
            yield session

    def user_override():
        return User(id=current["id"], email="request@example.test", hashed_password="x")

    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[get_current_user] = user_override
    app.dependency_overrides[get_snapshot_store] = lambda: store
    with TestClient(app) as client:
        yield client, current


def _upload(client: TestClient):
    return client.post(
        "/api/v2/data-analyst/datasets",
        content=b"revenue,profit,region\n10,2,north\n20,4,south\n30,6,north\n",
        headers={"Content-Type": "text/csv", "X-Filename": "metrics.csv"},
    )


def test_upload_and_deterministic_run_expose_typed_evidence(client_bundle) -> None:
    client, _ = client_bundle
    uploaded = _upload(client)
    assert uploaded.status_code == 201
    snapshot_id = uploaded.json()["snapshot_id"]
    domain_snapshot_id = uploaded.json()["profile"]["dataset_snapshot_id"]
    assert domain_snapshot_id.startswith("dataset-")

    started = client.post(
        "/api/v2/data-analyst/runs",
        json={"snapshot_id": snapshot_id, "question": "How are revenue and profit related?"},
        headers={"Idempotency-Key": "request-1"},
    )
    assert started.status_code == 201, started.text
    body = started.json()
    assert body["run"]["state"] == "succeeded"
    assert [item["state"] for item in body["run_history"]] == ["queued", "running", "succeeded"]
    assert body["plan"]["dataset_snapshot_id"] == domain_snapshot_id
    assert body["quality"]["validations"][0]["critical"] is True

    run_id = body["run"]["id"]
    computations = client.get(f"/api/v2/data-analyst/runs/{run_id}/computations")
    claims = client.get(f"/api/v2/data-analyst/runs/{run_id}/claims")
    status = client.get(f"/api/v2/data-analyst/runs/{run_id}")
    assert status.status_code == computations.status_code == claims.status_code == 200
    evidence_ids = {item["evidence"]["id"] for item in computations.json()["computations"]}
    assert evidence_ids
    assert all(
        link["evidence_id"] in evidence_ids
        for claim in claims.json()["claims"]
        for link in claim["evidence_links"]
    )

    replay = client.post(
        "/api/v2/data-analyst/runs",
        json={"snapshot_id": snapshot_id, "question": "How are revenue and profit related?"},
        headers={"Idempotency-Key": "request-1"},
    )
    assert replay.status_code == 200
    assert replay.json()["run"]["id"] == run_id

    independent = client.post(
        "/api/v2/data-analyst/runs",
        json={"snapshot_id": snapshot_id, "question": "How are revenue and profit related?"},
        headers={"Idempotency-Key": "request-independent"},
    )
    assert independent.status_code == 201
    assert independent.json()["run"]["id"] != run_id


def test_same_dataset_has_owner_scoped_opaque_snapshot_identity(client_bundle) -> None:
    client, current = client_bundle
    first = _upload(client)
    replay = _upload(client)
    assert replay.status_code == 201
    assert replay.json()["snapshot_id"] == first.json()["snapshot_id"]

    current["id"] = 8
    other = _upload(client)
    assert other.status_code == 201
    assert other.json()["snapshot_id"] != first.json()["snapshot_id"]
    assert other.json()["profile"]["dataset_snapshot_id"] == first.json()["profile"]["dataset_snapshot_id"]


def test_request_never_accepts_owner_and_cross_owner_is_404(client_bundle) -> None:
    client, current = client_bundle
    snapshot_id = _upload(client).json()["snapshot_id"]
    rejected = client.post(
        "/api/v2/data-analyst/runs",
        json={"snapshot_id": snapshot_id, "question": "Summarize revenue", "user_id": 8},
        headers={"Idempotency-Key": "request-2"},
    )
    assert rejected.status_code == 422

    started = client.post(
        "/api/v2/data-analyst/runs",
        json={"snapshot_id": snapshot_id, "question": "Summarize revenue"},
        headers={"Idempotency-Key": "request-3"},
    )
    run_id = started.json()["run"]["id"]
    current["id"] = 8
    assert client.get(f"/api/v2/data-analyst/runs/{run_id}").status_code == 404
    assert client.get(f"/api/v2/data-analyst/runs/{run_id}/computations").status_code == 404
    assert client.get(f"/api/v2/data-analyst/runs/{run_id}/claims").status_code == 404
    assert client.post(f"/api/v2/data-analyst/runs/{run_id}/cancel").status_code == 404


def test_invalid_analysis_abstains_with_category_and_idempotency_conflicts(client_bundle) -> None:
    client, _ = client_bundle
    snapshot_id = _upload(client).json()["snapshot_id"]
    failed = client.post(
        "/api/v2/data-analyst/runs",
        json={"snapshot_id": snapshot_id, "question": "???"},
        headers={"Idempotency-Key": "bad-request"},
    )
    assert failed.status_code == 201
    assert failed.json()["run"]["state"] == "failed"
    assert failed.json()["run"]["failure_code"] == "invalid-analysis-request"
    assert failed.json()["abstention_reason"]
    assert failed.json()["quality"]["validations"][0]["critical"] is True

    conflict = client.post(
        "/api/v2/data-analyst/runs",
        json={"snapshot_id": snapshot_id, "question": "Summarize revenue"},
        headers={"Idempotency-Key": "bad-request"},
    )
    assert conflict.status_code == 409


def test_terminal_run_cannot_be_cancelled(client_bundle) -> None:
    client, _ = client_bundle
    snapshot_id = _upload(client).json()["snapshot_id"]
    started = client.post(
        "/api/v2/data-analyst/runs",
        json={"snapshot_id": snapshot_id, "question": "Summarize revenue"},
        headers={"Idempotency-Key": "cancel-request"},
    )
    run_id = started.json()["run"]["id"]
    cancelled = client.post(f"/api/v2/data-analyst/runs/{run_id}/cancel")
    assert cancelled.status_code == 409
