from __future__ import annotations

from collections.abc import Callable, Generator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.platform.approvals import InvalidApprovalDecision
from app.platform.persistence import (
    IdempotencyConflict,
    PersistenceDomainError,
    RecordAlreadyExists,
    RecordNotFound,
)
from app.studios.career.api.contracts import (
    ApprovalDecisionRequest,
    ClaimDecisionRequest,
    DraftCreateRequest,
    MatchCreateRequest,
    RoleCreateRequest,
    SourceIngestionRequest,
)
from app.studios.career.api.service import CareerApplicationService, UnsupportedCareerCapability
from app.studios.career.persistence import InvalidCareerState


def _translate(call: Callable[[], Any]) -> Any:
    try:
        return call()
    except RecordNotFound as exc:
        raise HTTPException(status_code=404, detail="resource not found") from exc
    except UnsupportedCareerCapability as exc:
        raise HTTPException(
            status_code=501,
            detail={
                "code": "unsupported-capability",
                "capability": "free-form-extraction",
                "message": str(exc),
            },
        ) from exc
    except (RecordAlreadyExists, IdempotencyConflict, InvalidCareerState, InvalidApprovalDecision) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def create_career_router(
    *,
    session_dependency: Callable[..., Generator[Session, None, None]],
    owner_dependency: Callable[..., int],
) -> APIRouter:
    router = APIRouter(prefix="/api/v2/career", tags=["career-v2"])

    def service(
        session: Session = Depends(session_dependency),
        owner_id: int = Depends(owner_dependency),
    ) -> CareerApplicationService:
        return CareerApplicationService(session, owner_id=owner_id)

    @router.post("/sources", status_code=status.HTTP_201_CREATED)
    def create_source(
        request: SourceIngestionRequest,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.ingest_source(request))

    @router.get("/sources/{source_id}")
    def get_source(
        source_id: str,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.career.get_source(source_id, owner_id=app.owner_id))

    @router.post("/claims/{logical_claim_id}/decisions")
    def decide_claim(
        logical_claim_id: str,
        request: ClaimDecisionRequest,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.review_claim(logical_claim_id, request))

    @router.post("/roles", status_code=status.HTTP_201_CREATED)
    def create_role(
        request: RoleCreateRequest,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.create_role(request))

    @router.get("/roles/{role_id}")
    def get_role(
        role_id: str,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.career.get_role(role_id, owner_id=app.owner_id))

    @router.post("/matches", status_code=status.HTTP_201_CREATED)
    def create_match(
        request: MatchCreateRequest,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.create_match(request))

    @router.get("/matches/{match_id}")
    def get_match(
        match_id: str,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.career.get_match(match_id, owner_id=app.owner_id))

    @router.post("/drafts", status_code=status.HTTP_201_CREATED)
    def create_draft(
        request: DraftCreateRequest,
        app: CareerApplicationService = Depends(service),
        idempotency_key: str = Header(
            alias="Idempotency-Key", min_length=1, max_length=200
        ),
    ):
        return _translate(lambda: app.create_draft(request, idempotency_key=idempotency_key))

    @router.get("/drafts/{draft_id}")
    def get_draft(
        draft_id: str,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.career.get_draft(draft_id, owner_id=app.owner_id))

    @router.post("/approvals/{approval_id}/decisions")
    def decide_approval(
        approval_id: str,
        request: ApprovalDecisionRequest,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.decide_approval(approval_id, request.decision, comment=request.comment))

    @router.get("/approvals/{approval_id}")
    def get_approval(
        approval_id: str,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.approvals.get(approval_id, owner_id=app.owner_id))

    @router.post("/drafts/{draft_id}/publish")
    def publish(
        draft_id: str,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.publish(draft_id))

    @router.get("/artifacts/{revision_id}")
    def get_artifact(
        revision_id: str,
        app: CareerApplicationService = Depends(service),
    ):
        return _translate(lambda: app.get_artifact(revision_id))

    return router
