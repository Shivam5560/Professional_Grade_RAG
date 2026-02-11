"""Nexus resume scoring service utilities."""

import os
import uuid
import random
import string
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any, Optional

import aiofiles
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import User, NexusResumeFile, NexusResumeAnalysis
from app.utils.validators import validate_file_extension, validate_file_size
from app.services.nexus_ai.analyzer import analyze_resume as run_resume_analysis


def _generate_resume_id(user: User, length: int = 4) -> str:
    prefix_source = user.full_name or user.email or "USER"
    safe_prefix = prefix_source[:6].strip().upper().replace(" ", "")
    date = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{safe_prefix}-{date}-{random_suffix}"


async def _save_resume_file(file: UploadFile, resume_id: str) -> str:
    if not validate_file_extension(file.filename, settings.nexus_resume_allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(settings.nexus_resume_allowed_extensions)}",
        )

    content = await file.read()
    if not validate_file_size(len(content), settings.nexus_resume_max_size_mb):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum allowed: {settings.nexus_resume_max_size_mb} MB",
        )

    upload_dir = Path(settings.nexus_resume_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower()
    stored_name = f"{resume_id}{ext}"
    stored_path = upload_dir / stored_name

    async with aiofiles.open(stored_path, "wb") as out_file:
        await out_file.write(content)

    return str(stored_path)


async def upload_resume(db: Session, user_id: int, file: UploadFile) -> NexusResumeFile:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    resume_id = _generate_resume_id(user)
    file_path = await _save_resume_file(file, resume_id)

    record = NexusResumeFile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        resume_id=resume_id,
        filename=file.filename,
        filepath=file_path,
        status="uploaded",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_resumes(db: Session, user_id: int) -> List[NexusResumeFile]:
    return (
        db.query(NexusResumeFile)
        .filter(NexusResumeFile.user_id == user_id)
        .order_by(NexusResumeFile.created_at.desc())
        .all()
    )


async def analyze_resume(
    db: Session,
    user_id: int,
    resume_id: str,
    job_description: str,
) -> NexusResumeAnalysis:
    resume = (
        db.query(NexusResumeFile)
        .filter(
            NexusResumeFile.user_id == user_id,
            NexusResumeFile.resume_id == resume_id,
        )
        .first()
    )
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    if not os.path.exists(resume.filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume file missing")

    analysis_payload = run_resume_analysis(resume.filepath, job_description, resume.resume_id)
    overall_score = analysis_payload.get("overall_score")

    analysis = NexusResumeAnalysis(
        id=str(uuid.uuid4()),
        resume_id=resume.resume_id,
        user_id=user_id,
        job_description=job_description,
        analysis=analysis_payload,
        overall_score=overall_score,
    )
    db.add(analysis)

    resume.status = "analyzed"
    db.commit()
    db.refresh(analysis)

    return analysis


def list_history(db: Session, user_id: int) -> List[NexusResumeAnalysis]:
    return (
        db.query(NexusResumeAnalysis)
        .filter(NexusResumeAnalysis.user_id == user_id)
        .order_by(NexusResumeAnalysis.created_at.desc())
        .all()
    )


def build_dashboard(
    db: Session,
    user_id: int,
) -> Dict[str, Any]:
    resume_rows = (
        db.query(NexusResumeFile)
        .filter(NexusResumeFile.user_id == user_id)
        .order_by(NexusResumeFile.created_at.desc())
        .all()
    )
    analysis_rows = (
        db.query(NexusResumeAnalysis)
        .filter(NexusResumeAnalysis.user_id == user_id)
        .order_by(NexusResumeAnalysis.created_at.desc())
        .all()
    )

    total_resumes = len(resume_rows)
    analyzed_resumes = sum(1 for row in resume_rows if row.status == "analyzed")
    pending_resumes = total_resumes - analyzed_resumes

    monthly = defaultdict(lambda: {"uploaded": 0, "analyzed": 0})
    for resume in resume_rows:
        if resume.created_at:
            key = resume.created_at.strftime("%Y-%m")
            monthly[key]["uploaded"] += 1
    for analysis in analysis_rows:
        if analysis.created_at:
            key = analysis.created_at.strftime("%Y-%m")
            monthly[key]["analyzed"] += 1

    monthly_stats = [
        {
            "month": month,
            **values,
        }
        for month, values in sorted(monthly.items())
    ]

    latest_analysis = analysis_rows[0] if analysis_rows else None

    return {
        "resume_stats": {
            "total": total_resumes,
            "analyzed": analyzed_resumes,
            "pending": pending_resumes,
        },
        "monthly_stats": monthly_stats,
        "latest_analysis": latest_analysis,
    }
