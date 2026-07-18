from __future__ import annotations

from collections.abc import Callable, Generator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from pathlib import Path, PurePath
import uuid
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import NexusResumeFile, User
from app.platform.approvals import InvalidApprovalDecision
from app.platform.persistence import (
    IdempotencyConflict,
    PersistenceDomainError,
    RecordAlreadyExists,
    RecordNotFound,
)
from app.studios.career.api.contracts import (
    ApprovalDecisionRequest,
    CareerScoreRequest,
    CareerScoreResponse,
    ClaimDecisionRequest,
    DraftCreateRequest,
    MatchCreateRequest,
    JobDescriptionParseRequest,
    ParsedRoleResponse,
    RoleCreateRequest,
    SourceIngestionRequest,
    TailoringPrepareRequest,
)
from app.studios.career.extraction import extract_resume_source, parse_job_description
from app.studios.career.integrations import score_stored_resume, store_resume_source
from app.utils.validators import validate_file_extension, validate_file_size
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

    @router.post("/sources/upload", status_code=status.HTTP_201_CREATED)
    async def upload_source(
        file: UploadFile = File(...),
        app: CareerApplicationService = Depends(service),
    ):
        filename = file.filename or ""
        suffix = PurePath(filename).suffix.lower()
        if filename != PurePath(filename).name or ".." in filename or not validate_file_extension(filename, [".pdf", ".doc", ".docx", ".txt"]):
            raise HTTPException(status_code=400, detail="Upload a PDF, DOC, DOCX, or TXT resume with a safe filename")
        allowed_media_types = {
            ".pdf": {"application/pdf"},
            ".doc": {"application/msword", "application/octet-stream"},
            ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/octet-stream"},
            ".txt": {"text/plain", "application/octet-stream"},
        }
        media_type = (file.content_type or "application/octet-stream").lower()
        if media_type not in allowed_media_types[suffix]:
            raise HTTPException(status_code=400, detail=f"The declared media type does not match a {suffix} resume")
        content = await file.read()
        if not content.strip():
            raise HTTPException(status_code=400, detail="Resume file is empty")
        if not validate_file_size(len(content), 10):
            raise HTTPException(status_code=413, detail="Resume file exceeds the 10 MB limit")
        try:
            extracted = extract_resume_source(
                filename,
                content,
                source_id=f"source-{app.owner_id}-{uuid.uuid4().hex}",
            )
            await file.seek(0)
            ingested = _translate(lambda: app.ingest_claims(filename=filename, media_type=file.content_type or "application/octet-stream", claims=extracted.claims))
            resume = await store_resume_source(session=app.session, owner_id=app.owner_id, file=file)
            return {
                **ingested.model_dump(mode="json"),
                "resume": {
                    "resume_id": resume.resume_id,
                    "filename": resume.filename,
                    "status": resume.status,
                },
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/sources/resumes/{resume_id}", status_code=status.HTTP_201_CREATED)
    def ingest_stored_resume(
        resume_id: str,
        app: CareerApplicationService = Depends(service),
    ):
        resume = (
            app.session.query(NexusResumeFile)
            .filter(
                NexusResumeFile.resume_id == resume_id,
                NexusResumeFile.user_id == app.owner_id,
            )
            .first()
        )
        if resume is None:
            raise HTTPException(status_code=404, detail="resume not found")
        path = Path(resume.filepath)
        if not path.is_file():
            raise HTTPException(status_code=404, detail="stored resume file is unavailable")
        content = path.read_bytes()
        try:
            extracted = extract_resume_source(
                resume.filename,
                content,
                source_id=f"source-{app.owner_id}-{uuid.uuid4().hex}",
            )
            ingested = _translate(
                lambda: app.ingest_claims(
                    filename=resume.filename,
                    media_type={
                        ".pdf": "application/pdf",
                        ".doc": "application/msword",
                        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        ".txt": "text/plain",
                    }.get(PurePath(resume.filename).suffix.lower(), "application/octet-stream"),
                    claims=extracted.claims,
                )
            )
            return {
                **ingested.model_dump(mode="json"),
                "resume": {
                    "resume_id": resume.resume_id,
                    "filename": resume.filename,
                    "status": resume.status,
                },
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

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

    @router.post("/roles/parse", response_model=ParsedRoleResponse)
    def parse_role(request: JobDescriptionParseRequest):
        try:
            title, requirements = parse_job_description(request.job_description)
            return ParsedRoleResponse(title=title, requirements=requirements)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/scores", status_code=status.HTTP_201_CREATED, response_model=CareerScoreResponse)
    async def create_score(
        request: CareerScoreRequest,
        app: CareerApplicationService = Depends(service),
    ):
        analysis = await score_stored_resume(
            session=app.session,
            owner_id=app.owner_id,
            resume_id=request.resume_id,
            job_description=request.job_description,
        )
        return CareerScoreResponse(
            analysis_id=analysis.id,
            resume_id=analysis.resume_id,
            overall_score=analysis.overall_score,
            analysis=analysis.analysis or {},
            refined_recommendations=analysis.refined_recommendations,
            refined_justifications=analysis.refined_justifications,
            resume_data=analysis.resume_data,
            created_at=analysis.created_at.isoformat() if analysis.created_at else "",
        )

    @router.post("/tailoring/prepare", status_code=status.HTTP_201_CREATED)
    def prepare_tailoring(
        request: TailoringPrepareRequest,
        app: CareerApplicationService = Depends(service),
    ):
        try:
            title, requirements = parse_job_description(request.job_description)
            return _translate(
                lambda: app.prepare_tailoring(
                    source_id=request.source_id,
                    title=title,
                    requirements=requirements,
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

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


def _current_owner_id(current_user: User = Depends(get_current_user)) -> int:
    return int(current_user.id)


router = create_career_router(
    session_dependency=get_db,
    owner_dependency=_current_owner_id,
)
