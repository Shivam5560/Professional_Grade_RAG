from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import User
from app.studios.career.api.router import create_career_router


@pytest.fixture
def client() -> Iterator[tuple[TestClient, dict[str, int]]]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                User(id=7, email="owner@example.com", hashed_password="x"),
                User(id=8, email="other@example.com", hashed_password="x"),
            ]
        )
        session.commit()

    owner = {"id": 7}

    def get_session() -> Iterator[Session]:
        with Session(engine) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def get_owner_id() -> int:
        return owner["id"]

    app = FastAPI()
    app.include_router(
        create_career_router(
            session_dependency=get_session,
            owner_dependency=get_owner_id,
        )
    )
    with TestClient(app) as test_client:
        yield test_client, owner


def claim_payload(source_id: str = "source-1") -> dict[str, object]:
    return {
        "subject": {"kind": "person", "id": "person-7", "label": "Candidate"},
        "predicate": "has-skill",
        "object": {"kind": "skill", "value": "Python"},
        "source_spans": [
            {
                "source_id": source_id,
                "locator": "skills:1",
                "exact_text": "Built production services with Python.",
            }
        ],
        "temporal_scope": {
            "start": date(2023, 1, 1).isoformat(),
            "end": date(2025, 12, 31).isoformat(),
        },
        "verification_status": "inferred",
        "confidence": 0.7,
        "verifier_id": "structured-ingestion",
        "context": {},
        "related_claim_ids": [],
    }


def requirement_payload() -> dict[str, object]:
    return {
        "id": "req-python",
        "priority": "required",
        "category": "skill",
        "description": "Production Python",
        "source_span": {
            "source_id": "role-1",
            "locator": "requirements:1",
            "exact_text": "Production Python is required.",
        },
        "confidence": 1.0,
        "weight": 3.0,
    }


def components_payload() -> dict[str, float]:
    return {
        "semantic_relevance": 1.0,
        "evidence_strength": 1.0,
        "recency": 1.0,
        "duration_seniority": 1.0,
        "transferability": 1.0,
        "specificity": 1.0,
    }


def create_verified_claim(test_client: TestClient) -> dict[str, object]:
    source = test_client.post(
        "/api/v2/career/sources",
        json={
            "filename": "resume.json",
            "media_type": "application/json",
            "ingestion_mode": "structured",
            "claims": [claim_payload()],
        },
    )
    assert source.status_code == 201, source.text
    initial = source.json()["claims"][0]
    verified = test_client.post(
        f"/api/v2/career/claims/{initial['logical_claim_id']}/decisions",
        json={"action": "verify"},
    )
    assert verified.status_code == 200, verified.text
    return verified.json()


def create_role(test_client: TestClient) -> dict[str, object]:
    response = test_client.post(
        "/api/v2/career/roles",
        json={
            "role_id": "role-1",
            "title": "Senior Platform Engineer",
            "requirements": [requirement_payload()],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_match(test_client: TestClient, claim_id: str) -> dict[str, object]:
    response = test_client.post(
        "/api/v2/career/matches",
        json={
            "match_id": "match-1",
            "role_id": "role-1",
            "candidate_edges": [
                {
                    "requirement_id": "req-python",
                    "claim_id": claim_id,
                    "components": components_payload(),
                }
            ],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_structured_ingestion_claim_audit_role_match_and_approval_gated_publish(
    client: tuple[TestClient, dict[str, int]],
) -> None:
    test_client, _ = client
    verified = create_verified_claim(test_client)
    claim_id = verified["claim"]["id"]
    create_role(test_client)
    match = create_match(test_client, claim_id)

    assert match["result"]["mandatory_coverage"]["lower_bound"] == 1.0
    assert "hiring_probability" not in str(match).lower()

    draft_response = test_client.post(
        "/api/v2/career/drafts",
        headers={"Idempotency-Key": "career-draft-1"},
        json={"match_id": "match-1"},
    )
    assert draft_response.status_code == 201, draft_response.text
    draft_body = draft_response.json()
    assert draft_body["run"]["state"] == "awaiting_input"
    assert draft_body["draft"]["publication_ready"] is False
    assert draft_body["approval"]["decision_type"] == "final-resume"

    replay = test_client.post(
        "/api/v2/career/drafts",
        headers={"Idempotency-Key": "career-draft-1"},
        json={"match_id": "match-1"},
    )
    assert replay.status_code == 201, replay.text
    assert replay.json()["run"]["id"] == draft_body["run"]["id"]
    assert replay.json()["draft"]["id"] == draft_body["draft"]["id"]

    unpublished = test_client.post(
        f"/api/v2/career/drafts/{draft_body['draft']['id']}/publish"
    )
    assert unpublished.status_code == 409

    approval = test_client.post(
        f"/api/v2/career/approvals/{draft_body['approval']['id']}/decisions",
        json={"decision": "approve", "comment": "Approved"},
    )
    assert approval.status_code == 200, approval.text

    published = test_client.post(
        f"/api/v2/career/drafts/{draft_body['draft']['id']}/publish"
    )
    assert published.status_code == 200, published.text
    published_body = published.json()
    assert published_body["draft"]["publication_ready"] is True
    assert published_body["run"]["state"] == "succeeded"
    assert published_body["artifact"]["evidence_ids"] == [claim_id]
    assert published_body["artifact_content"] == published_body["draft"]
    assert all(
        bullet["transformation"] == "compressed"
        for bullet in published_body["draft"]["bullets"]
    )


def test_cross_owner_resources_are_uniformly_not_found(
    client: tuple[TestClient, dict[str, int]],
) -> None:
    test_client, owner = client
    verified = create_verified_claim(test_client)
    create_role(test_client)
    create_match(test_client, verified["claim"]["id"])
    draft = test_client.post(
        "/api/v2/career/drafts",
        headers={"Idempotency-Key": "career-owner-scope"},
        json={"match_id": "match-1"},
    ).json()
    approval_id = draft["approval"]["id"]
    draft_id = draft["draft"]["id"]

    owner["id"] = 8
    paths = [
        "/api/v2/career/sources/source-1",
        "/api/v2/career/roles/role-1",
        "/api/v2/career/matches/match-1",
        f"/api/v2/career/drafts/{draft_id}",
        f"/api/v2/career/approvals/{approval_id}",
    ]
    for path in paths:
        response = test_client.get(path)
        assert response.status_code == 404, (path, response.text)


def test_request_bodies_never_accept_owner_identity(
    client: tuple[TestClient, dict[str, int]],
) -> None:
    test_client, _ = client
    response = test_client.post(
        "/api/v2/career/sources",
        json={
            "owner_id": 8,
            "filename": "resume.json",
            "media_type": "application/json",
            "ingestion_mode": "structured",
            "claims": [claim_payload()],
        },
    )
    assert response.status_code == 422
