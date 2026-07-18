from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

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
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(User(id=7, email="owner@example.com", hashed_password="x"))
        session.commit()

    def get_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session
            session.commit()

    app = FastAPI()
    app.include_router(
        create_career_router(
            session_dependency=get_session,
            owner_dependency=lambda: 7,
        )
    )
    with TestClient(app) as test_client:
        yield test_client


def test_uploads_a_resume_and_returns_inferred_source_claims(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def stored_resume(**_kwargs):
        return SimpleNamespace(
            resume_id="JANE-20260718-TEST",
            filename="resume.txt",
            status="uploaded",
        )

    monkeypatch.setattr(
        "app.studios.career.extraction.resume_source.extract_resume_data",
        lambda _text: {
            "personal_info": {"name": "Jane Doe", "email": "jane@example.com"},
            "work_experience": [
                {
                    "job_title": "Data Engineer",
                    "company": "Acme",
                    "dates": "2022 - Present",
                    "responsibilities": ["Built production data pipelines"],
                }
            ],
            "keywords": ["Python", "SQL"],
        },
    )
    monkeypatch.setattr(
        "app.studios.career.api.router.store_resume_source",
        stored_resume,
    )

    response = client.post(
        "/api/v2/career/sources/upload",
        files={
            "file": (
                "resume.txt",
                b"Jane Doe\nData Engineer\nBuilt production data pipelines",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["source"]["filename"] == "resume.txt"
    assert body["resume"]["resume_id"] == "JANE-20260718-TEST"
    assert body["claims"]
    assert all(
        item["claim"]["verification_status"] == "inferred"
        for item in body["claims"]
    )
    assert any(
        item["claim"]["object"]["value"] == "Python"
        for item in body["claims"]
    )


@pytest.mark.parametrize("filename", ["resume.exe", "resume.json", "../resume.txt"])
def test_rejects_unsupported_or_unsafe_resume_names(
    client: TestClient, filename: str
) -> None:
    response = client.post(
        "/api/v2/career/sources/upload",
        files={"file": (filename, b"resume", "application/octet-stream")},
    )

    assert response.status_code == 400


def test_rejects_empty_resume_content(client: TestClient) -> None:
    response = client.post(
        "/api/v2/career/sources/upload",
        files={"file": ("resume.txt", b"   ", "text/plain")},
    )

    assert response.status_code == 400


def test_parses_a_plain_job_description(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.studios.career.extraction.resume_source.extract_jd_data",
        lambda _text: {
            "job_title": "Senior Data Engineer",
            "required_skills": ["Python", "SQL"],
            "key_responsibilities": ["Own production data pipelines"],
            "other_qualifications": ["Cloud experience"],
        },
    )

    response = client.post(
        "/api/v2/career/roles/parse",
        json={"job_description": "We need a Senior Data Engineer with Python and SQL."},
    )

    assert response.status_code == 200, response.text
    assert response.json()["title"] == "Senior Data Engineer"
    assert {item["description"] for item in response.json()["requirements"]} >= {
        "Python",
        "SQL",
    }


def test_scores_a_stored_resume_without_accepting_an_authoritative_user_id(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scored_resume(**kwargs):
        return SimpleNamespace(
            id="analysis-1",
            resume_id=kwargs["resume_id"],
            overall_score=82.0,
            analysis={"ats_analysis": {"score": 90}, "match_analysis": {"overall_fit": "Strong"}},
            refined_recommendations=["Add one supported SQL outcome"],
            refined_justifications=["Strong skill coverage"],
            resume_data={"name": "Jane Doe"},
            created_at=None,
        )

    monkeypatch.setattr(
        "app.studios.career.api.router.score_stored_resume",
        scored_resume,
    )

    response = client.post(
        "/api/v2/career/scores",
        json={
            "resume_id": "JANE-20260718-TEST",
            "job_description": "We need a data engineer with Python and SQL.",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["overall_score"] == 82.0
    assert response.json()["resume_id"] == "JANE-20260718-TEST"


def test_rejects_score_payloads_that_try_to_choose_an_owner(client: TestClient) -> None:
    response = client.post(
        "/api/v2/career/scores",
        json={
            "owner_id": 99,
            "resume_id": "resume-1",
            "job_description": "A sufficiently detailed job description.",
        },
    )

    assert response.status_code == 422
