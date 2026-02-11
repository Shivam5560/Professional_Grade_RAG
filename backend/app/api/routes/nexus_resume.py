"""Nexus resume scoring endpoints."""

from typing import List
from fastapi import APIRouter, UploadFile, File, Form, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import NexusResumeFile, NexusResumeAnalysis
from app.models.schemas import (
    ResumeUploadResponse,
    ResumeFileInfo,
    ResumeListResponse,
    ResumeAnalyzeRequest,
    ResumeAnalyzeResponse,
    ResumeHistoryResponse,
    ResumeDashboardResponse,
)
from app.services.nexus_resume_service import (
    upload_resume,
    list_resumes,
    analyze_resume,
    list_history,
    build_dashboard,
)

router = APIRouter(prefix="/nexus", tags=["Nexus"])


def _serialize_resume(resume: NexusResumeFile) -> ResumeFileInfo:
    return ResumeFileInfo(
        id=resume.id,
        resume_id=resume.resume_id,
        filename=resume.filename,
        status=resume.status,
        created_at=resume.created_at.isoformat() if resume.created_at else "",
        updated_at=resume.updated_at.isoformat() if resume.updated_at else None,
    )


def _serialize_analysis(analysis: NexusResumeAnalysis) -> ResumeAnalyzeResponse:
    return ResumeAnalyzeResponse(
        analysis_id=analysis.id,
        resume_id=analysis.resume_id,
        overall_score=analysis.overall_score,
        job_description=analysis.job_description,
        analysis=analysis.analysis,
        created_at=analysis.created_at.isoformat() if analysis.created_at else "",
    )


@router.post("/resumes/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume_endpoint(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    record = await upload_resume(db, user_id, file)
    return ResumeUploadResponse(resume=_serialize_resume(record))


@router.get("/resumes/{user_id}", response_model=ResumeListResponse, status_code=status.HTTP_200_OK)
async def list_resumes_endpoint(user_id: int, db: Session = Depends(get_db)):
    resumes = list_resumes(db, user_id)
    return ResumeListResponse(
        list=[_serialize_resume(resume) for resume in resumes],
        total=len(resumes),
    )


@router.post("/resumes/analyze", response_model=ResumeAnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze_resume_endpoint(request: ResumeAnalyzeRequest, db: Session = Depends(get_db)):
    if not request.job_description.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description is required")
    analysis = await analyze_resume(db, request.user_id, request.resume_id, request.job_description)
    return _serialize_analysis(analysis)


@router.get("/resumes/history/{user_id}", response_model=ResumeHistoryResponse, status_code=status.HTTP_200_OK)
async def resume_history_endpoint(user_id: int, db: Session = Depends(get_db)):
    history = list_history(db, user_id)
    return ResumeHistoryResponse(
        list=[_serialize_analysis(item) for item in history],
        total=len(history),
    )


@router.get("/dashboard/{user_id}", response_model=ResumeDashboardResponse, status_code=status.HTTP_200_OK)
async def resume_dashboard_endpoint(user_id: int, db: Session = Depends(get_db)):
    dashboard = build_dashboard(db, user_id)
    latest = dashboard.get("latest_analysis")
    return ResumeDashboardResponse(
        resume_stats=dashboard.get("resume_stats", {}),
        monthly_stats=dashboard.get("monthly_stats", []),
        latest_analysis=_serialize_analysis(latest) if latest else None,
    )
