from __future__ import annotations

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.services.nexus_resume_service import analyze_resume, upload_resume


async def store_resume_source(*, session: Session, owner_id: int, file: UploadFile):
    """Store an uploaded Career resume through the existing owner-scoped service."""
    return await upload_resume(session, owner_id, file)


async def score_stored_resume(
    *, session: Session, owner_id: int, resume_id: str, job_description: str
):
    """Run the existing scorer while deriving ownership from the Career session."""
    return await analyze_resume(session, owner_id, resume_id, job_description)
