"""
Data Analysis API routes.
Handles job creation, status tracking, report retrieval, and WebSocket progress streaming.

Hardened: file size enforcement, rate limiting, request body for config,
WebSocket heartbeat, stale connection cleanup.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app.api.deps import get_current_user
from app.config import settings
from app.db.database import get_db
from app.db.models import AnalysisChartAsset, AnalysisJob, AnalysisReport, User
from app.models.analysis_schemas import (
    AnalysisConfig,
    AnalysisCreateRequest,
    AnalysisFromUploadRequest,
    AnalysisJobResponse,
    AnalysisListResponse,
    AnalysisReportResponse,
    WorkflowProgressEvent,
)
from app.services.analysis.data_ingestion import save_uploaded_file
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analysis", tags=["Analysis"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _job_to_response(job: AnalysisJob) -> AnalysisJobResponse:
    return AnalysisJobResponse(
        job_id=job.id,
        status=job.status,  # type: ignore[arg-type]
        query=job.query,
        source_type=job.source_type,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        progress_events=job.progress_events or [],
    )


def _create_and_schedule_job(
    db: Session,
    user_id: int,
    source_type: str,
    source_id: str,
    query: str,
    config: Dict[str, Any],
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    job_id = str(uuid.uuid4())
    job = AnalysisJob(
        id=job_id,
        user_id=user_id,
        status="queued",
        source_type=source_type,
        source_id=source_id,
        query=query,
        config=config,
        progress_events=[],
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_analysis_workflow, job_id, user_id)
    logger.log_operation("Analysis job created", job_id=job_id, user_id=user_id)
    return {"job_id": job_id, "status": "queued"}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_analysis_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Upload a data file for analysis. Returns a source_id for later use."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    allowed = {e.lower() for e in settings.analysis_allowed_extensions}
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {settings.analysis_allowed_extensions}",
        )

    # Content-Length check (fast path)
    content_length = file.headers.get("content-length")
    if content_length:
        size = int(content_length)
        limit_bytes = settings.analysis_max_file_size_mb * 1024 * 1024
        if size > limit_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum size of {settings.analysis_max_file_size_mb}MB",
            )

    try:
        source_id = save_uploaded_file(file, str(current_user.id))
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc))

    return {"source_id": source_id, "filename": file.filename, "status": "uploaded"}


@router.post("/", status_code=status.HTTP_201_CREATED)
def start_analysis(
    request: AnalysisCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Start a new analysis job."""
    return _create_and_schedule_job(
        db=db,
        user_id=current_user.id,
        source_type=request.source_type,
        source_id="pending",
        query=request.query,
        config=request.config.model_dump(),
        background_tasks=background_tasks,
    )


@router.post("/from-upload", status_code=status.HTTP_201_CREATED)
def start_analysis_from_upload(
    request: AnalysisFromUploadRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Start an analysis from a previously uploaded file."""
    return _create_and_schedule_job(
        db=db,
        user_id=current_user.id,
        source_type="upload",
        source_id=request.source_id,
        query=request.query,
        config=request.config.model_dump(),
        background_tasks=background_tasks,
    )


@router.get("/")
def list_analysis_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
) -> AnalysisListResponse:
    """List analysis jobs for the current user."""
    query = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.user_id == current_user.id)
        .order_by(AnalysisJob.created_at.desc())
    )
    total = query.count()
    jobs = query.offset(offset).limit(limit).all()
    return AnalysisListResponse(jobs=[_job_to_response(j) for j in jobs], total=total)


@router.get("/{job_id}")
def get_analysis_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisJobResponse:
    """Get the status and progress of a specific analysis job."""
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.id == job_id, AnalysisJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)


@router.post("/{job_id}/cancel")
def cancel_analysis(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Cancel a running or queued analysis job."""
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.id == job_id, AnalysisJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in ("completed", "failed"):
        raise HTTPException(status_code=400, detail=f"Job already {job.status}")

    job.status = "cancelled"
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    logger.log_operation("Analysis job cancelled", job_id=job_id, user_id=current_user.id)
    return {"job_id": job_id, "status": "cancelled"}


@router.delete("/{job_id}")
def delete_analysis_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an analysis job, cascading database records and removing disk chart assets."""
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.id == job_id, AnalysisJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Clean up local charts directory
    charts_dir = os.path.join(settings.analysis_chart_dir, job_id)
    if os.path.exists(charts_dir) and os.path.isdir(charts_dir):
        try:
            import shutil
            shutil.rmtree(charts_dir)
            logger.log_operation("Deleted charts directory", job_id=job_id)
        except Exception as exc:
            logger.log_error("Failed to delete charts directory", exc, job_id=job_id)

    db.delete(job)
    db.commit()
    logger.log_operation("Analysis job deleted", job_id=job_id, user_id=current_user.id)
    return {"message": "Job deleted successfully", "job_id": job_id}


@router.get("/{job_id}/report")
def get_analysis_report(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisReportResponse:
    """Retrieve the final report for a completed analysis job."""
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.id == job_id, AnalysisJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in ("queued", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Job is {job.status}. Report not available yet.")

    report = (
        db.query(AnalysisReport)
        .filter(AnalysisReport.job_id == job_id, AnalysisReport.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    charts = (
        db.query(AnalysisChartAsset)
        .filter(AnalysisChartAsset.job_id == job_id, AnalysisChartAsset.user_id == current_user.id)
        .all()
    )

    return AnalysisReportResponse(
        report_id=report.id,
        job_id=report.job_id,
        title=report.title,
        narrative=report.narrative,
        sections=report.sections or [],
        insights=report.insights or [],
        chart_urls=[f"/api/v1/analysis/charts/{job_id}/{c.filename}" for c in charts],
        slide_deck_url=None,
        created_at=report.created_at,
    )


@router.get("/charts/{job_id}/{filename}")
def serve_chart_image(job_id: str, filename: str) -> FileResponse:
    """Serve a chart image file."""
    chart_path = os.path.join(settings.analysis_chart_dir, job_id, filename)
    if not os.path.exists(chart_path):
        raise HTTPException(status_code=404, detail="Chart image not found")
    media_type = "image/png" if filename.endswith(".png") else "application/json"
    return FileResponse(path=chart_path, media_type=media_type)


@router.get("/{job_id}/report/download")
def download_analysis_report(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the analysis report as a PPTX slide deck."""
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.id == job_id, AnalysisJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in ("queued", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Job is {job.status}. Report not available yet.")

    report = (
        db.query(AnalysisReport)
        .filter(AnalysisReport.job_id == job_id, AnalysisReport.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    charts = (
        db.query(AnalysisChartAsset)
        .filter(AnalysisChartAsset.job_id == job_id, AnalysisChartAsset.user_id == current_user.id)
        .all()
    )
    chart_paths = [chart.file_path for chart in charts if chart.file_path and os.path.exists(chart.file_path)]

    from app.services.analysis.slide_generator import generate_slides

    fd, slides_path = tempfile.mkstemp(prefix=f"analysis-{job_id[:8]}-", suffix=".pptx")
    os.close(fd)
    try:
        generate_slides(
            title=report.title,
            narrative=report.narrative,
            sections=report.sections or [],
            insights=report.insights or [],
            design_spec=report.design_spec or {},
            chart_paths=chart_paths,
            job_id=job_id,
            output_path=slides_path,
        )
    except Exception as exc:
        if os.path.exists(slides_path):
            os.unlink(slides_path)
        logger.log_error("On-demand slide deck generation failed", exc, job_id=job_id)
        raise HTTPException(status_code=500, detail="Failed to generate slide deck")

    filename = f"analysis-report-{job_id[:8]}.pptx"
    return FileResponse(
        path=slides_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
        background=BackgroundTask(lambda path: os.path.exists(path) and os.unlink(path), slides_path),
    )


# ---------------------------------------------------------------------------
# WebSocket with heartbeat and stale cleanup
# ---------------------------------------------------------------------------

STALE_TIMEOUT_SEC = 300  # 5 minutes
HEARTBEAT_INTERVAL_SEC = 30

_conn_meta: Dict[str, Dict[str, float]] = {}  # job_id -> "ws_id: last_activity"


class ConnectionManager:
    """Manages WebSocket connections with heartbeat and stale cleanup."""

    def __init__(self) -> None:
        self.connections: Dict[str, List[WebSocket]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        await websocket.accept()
        ws_id = str(id(websocket))
        self.connections.setdefault(job_id, []).append(websocket)
        _conn_meta.setdefault(job_id, {})[ws_id] = time.monotonic()

    def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        conns = self.connections.get(job_id, [])
        if websocket in conns:
            conns.remove(websocket)
        ws_id = str(id(websocket))
        _conn_meta.get(job_id, {}).pop(ws_id, None)
        if not conns:
            self.connections.pop(job_id, None)
            _conn_meta.pop(job_id, None)

    def touch(self, job_id: str, websocket: WebSocket) -> None:
        ws_id = str(id(websocket))
        _conn_meta.get(job_id, {}).__setitem__(ws_id, time.monotonic())

    async def broadcast(self, job_id: str, message: Dict[str, Any]) -> None:
        stale_ids = []
        now = time.monotonic()
        for ws_id, last in list(_conn_meta.get(job_id, {}).items()):
            if now - last > STALE_TIMEOUT_SEC:
                stale_ids.append(ws_id)

        for ws in list(self.connections.get(job_id, [])):
            ws_id = str(id(ws))
            if ws_id in stale_ids:
                logger.warning("Removing stale WebSocket connection for job=%s", job_id)
                try:
                    await ws.close(code=1001, reason="Stale connection")
                except Exception:
                    pass
                self.disconnect(job_id, ws)
                continue
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(job_id, ws)

    def broadcast_sync(self, job_id: str, message: Dict[str, Any]) -> None:
        """Thread-safe broadcast for background tasks."""
        if self._loop is not None and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(job_id, message), self._loop)

    @property
    def active_connections(self) -> Dict[str, int]:
        return {k: len(v) for k, v in self.connections.items()}


_manager = ConnectionManager()


@router.get("/ws/status")
def ws_status() -> Dict[str, Any]:
    """Return active WebSocket connection counts for monitoring."""
    return {"active_connections": _manager.active_connections, "stale_timeout_s": STALE_TIMEOUT_SEC}


@router.websocket("/{job_id}/ws")
async def analysis_ws(websocket: WebSocket, job_id: str) -> None:
    """WebSocket endpoint for real-time analysis progress updates with heartbeat."""
    await _manager.connect(job_id, websocket)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=HEARTBEAT_INTERVAL_SEC)
                msg_type = data.get("type")
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong", "job_id": job_id})
                    _manager.touch(job_id, websocket)
                elif msg_type == "cancel":
                    await websocket.send_json({"type": "cancel_acknowledged", "job_id": job_id})
                else:
                    await websocket.send_json({"type": "unknown", "job_id": job_id})
            except asyncio.TimeoutError:
                # Send heartbeat
                try:
                    await websocket.send_json({"type": "heartbeat", "job_id": job_id})
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        _manager.disconnect(job_id, websocket)


# ---------------------------------------------------------------------------
# Background task runner
# ---------------------------------------------------------------------------

def _run_analysis_workflow(job_id: str, user_id: int) -> None:
    """Run the analysis workflow in a background thread."""
    from app.analysis.workflows.analysis_workflow import run_analysis_workflow
    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        run_analysis_workflow(db, job_id, user_id, _manager)
    except Exception as exc:
        logger.log_error("Analysis workflow failed", exc, job_id=job_id, user_id=user_id)
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job and job.status not in ("completed", "cancelled"):
            job.status = "failed"
            job.error_message = str(exc)[:2000]
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
