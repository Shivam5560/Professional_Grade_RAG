from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.platform.persistence import IdempotencyConflict, RecordNotFound
from app.platform.runtime import InvalidRunTransition

from .contracts import (
    AnalysisRunResponse,
    ClaimListResponse,
    ComputationListResponse,
    DatasetUploadResponse,
    StartAnalysisRequest,
)
from .service import (
    CsvUploadPolicy,
    DataAnalystApplicationService,
    InMemorySnapshotStore,
    SnapshotStore,
    UnsafeDatasetUpload,
)

router = APIRouter(prefix="/api/v2/data-analyst", tags=["data-analyst-v2"])
_default_snapshot_store = InMemorySnapshotStore()


def get_snapshot_store() -> SnapshotStore:
    return _default_snapshot_store


def _service(db: Session, storage: SnapshotStore) -> DataAnalystApplicationService:
    return DataAnalystApplicationService(db, storage)


def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, RecordNotFound):
        return HTTPException(status_code=404, detail="resource not found")
    if isinstance(exc, (IdempotencyConflict, InvalidRunTransition)):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, UnsafeDatasetUpload):
        code = 413 if exc.code == "request-too-large" else 400
        return HTTPException(status_code=code, detail={"code": exc.code, "message": str(exc)})
    return HTTPException(status_code=422, detail={"code": "invalid-analysis-request", "message": str(exc)})


@router.post("/datasets", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    request: Request,
    filename: str = Header(alias="X-Filename", min_length=1, max_length=255),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: SnapshotStore = Depends(get_snapshot_store),
) -> DatasetUploadResponse:
    policy = CsvUploadPolicy()
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > policy.max_bytes:
            raise _translate(UnsafeDatasetUpload("request-too-large", "dataset exceeds the byte limit"))
    try:
        snapshot = _service(db, storage).upload_dataset(
            bytes(content), owner_id=current_user.id, filename=filename,
            media_type=request.headers.get("content-type", ""), policy=policy,
        )
    except Exception as exc:
        raise _translate(exc) from exc
    return DatasetUploadResponse(snapshot_id=snapshot.id, profile=snapshot.profile)


@router.post("/runs", response_model=AnalysisRunResponse, status_code=status.HTTP_201_CREATED)
def start_analysis(
    payload: StartAnalysisRequest,
    response: Response,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: SnapshotStore = Depends(get_snapshot_store),
) -> AnalysisRunResponse:
    try:
        view, created = _service(db, storage).start_analysis(
            owner_id=current_user.id, snapshot_id=payload.snapshot_id,
            question=payload.question, business_context=payload.business_context,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        raise _translate(exc) from exc
    response.status_code = 201 if created else 200
    return view


@router.get("/runs/{run_id}", response_model=AnalysisRunResponse)
def get_analysis_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: SnapshotStore = Depends(get_snapshot_store),
) -> AnalysisRunResponse:
    try:
        return _service(db, storage).get_run(run_id, owner_id=current_user.id)
    except Exception as exc:
        raise _translate(exc) from exc


@router.get("/runs/{run_id}/computations", response_model=ComputationListResponse)
def list_computations(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ComputationListResponse:
    try:
        values = DataAnalystApplicationService(db, _default_snapshot_store).data.list_computations(run_id, owner_id=current_user.id)
    except Exception as exc:
        raise _translate(exc) from exc
    return ComputationListResponse(computations=values)


@router.get("/runs/{run_id}/claims", response_model=ClaimListResponse)
def list_claims(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClaimListResponse:
    try:
        values = DataAnalystApplicationService(db, _default_snapshot_store).data.list_claims(run_id, owner_id=current_user.id)
    except Exception as exc:
        raise _translate(exc) from exc
    return ClaimListResponse(claims=values)


@router.post("/runs/{run_id}/cancel", response_model=AnalysisRunResponse)
def cancel_analysis(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: SnapshotStore = Depends(get_snapshot_store),
) -> AnalysisRunResponse:
    try:
        return _service(db, storage).cancel(run_id, owner_id=current_user.id)
    except Exception as exc:
        raise _translate(exc) from exc
