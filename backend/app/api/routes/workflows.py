"""
API routes for orchestrating LlamaIndex workflows.
Includes endpoints to start, track, and interact with the Auto-Tailor workflow.
"""

from __future__ import annotations

import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User, NexusResumeFile, NexusResumeAnalysis
from app.analysis.workflows.auto_tailor_workflow import AutoTailorWorkflow, RewriteEvent
from app.services.resume_generator import generate_resume_pdf
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/workflows", tags=["Workflows"])


# ─── Pydantic Request/Response Models ───────────────────────────────────────

class StartTailorRequest(BaseModel):
    resume_id: str = Field(..., description="ID of the NexusResumeFile uploaded by the user")
    job_description: str = Field(..., description="Job Description text to tailor against")
    target_score: float = Field(default=85.0, description="ATS score threshold to stop iterations")
    max_iterations: int = Field(default=3, description="Maximum automated rewrite cycles")

class RejectTailorRequest(BaseModel):
    comments: str = Field(..., description="User feedback/comments for refining in the next iteration")


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/auto-tailor/start", status_code=status.HTTP_201_CREATED)
async def start_auto_tailor(
    payload: StartTailorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Launch the Auto-Tailor workflow.
    Checks user ownership, creates the database record, and runs the first iteration.
    """
    logger.info(f"User {current_user.id} starting Auto-Tailor for resume {payload.resume_id}")

    # 1. Verify resume file ownership
    resume_file = (
        db.query(NexusResumeFile)
        .filter(
            NexusResumeFile.resume_id == payload.resume_id,
            NexusResumeFile.user_id == current_user.id
        )
        .first()
    )
    if not resume_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master resume file not found or unauthorized access"
        )

    # 2. Create the analysis tracking record
    analysis_id = str(uuid.uuid4())
    initial_analysis_payload = {
        "status": "running",
        "current_iteration": 0,
        "target_score": payload.target_score,
        "latest_score": 0.0,
        "resume_data": {},
        "scores_breakdown": {},
        "critic_feedback": "",
        "history": []
    }

    analysis_record = NexusResumeAnalysis(
        id=analysis_id,
        resume_id=payload.resume_id,
        user_id=current_user.id,
        job_description=payload.job_description,
        analysis=initial_analysis_payload,
        overall_score=0.0
    )
    db.add(analysis_record)
    db.commit()

    # 3. Instantiate and run LlamaIndex Workflow inline
    try:
        workflow = AutoTailorWorkflow(db=db, analysis_id=analysis_id, disable_validation=True, timeout=300.0)
        result = await workflow.run(
            resume_id=payload.resume_id,
            job_description=payload.job_description,
            target_score=payload.target_score,
            max_iterations=payload.max_iterations
        )
        
        # Reload analysis record to reflect updates made inside workflow steps
        db.refresh(analysis_record)
        
        # If workflow finished completely (met threshold on first run)
        if result.get("status") == "completed":
            analysis_record.overall_score = result.get("latest_score")
            analysis_record.analysis = {
                **analysis_record.analysis,
                "status": "completed",
                "pdf_path": result.get("pdf_path"),
                "resume_data": result.get("resume_data"),
                "scores_breakdown": result.get("scores_breakdown"),
                "critic_feedback": result.get("critic_feedback")
            }
            resume_file.status = "analyzed"
            db.commit()
            
        return {
            "analysis_id": analysis_id,
            "status": result.get("status"),
            "current_iteration": result.get("current_iteration"),
            "latest_score": result.get("latest_score"),
            "resume_data": result.get("resume_data"),
            "scores_breakdown": result.get("scores_breakdown"),
            "critic_feedback": result.get("critic_feedback"),
            "pdf_path": result.get("pdf_path")
        }
    except Exception as e:
        logger.error(f"Auto-Tailor workflow execution failed: {e}", exc_info=True)
        analysis_record.analysis = {
            **analysis_record.analysis,
            "status": "failed",
            "error": str(e)
        }
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow failed: {str(e)}"
        )


@router.get("/auto-tailor/{analysis_id}")
async def get_auto_tailor_status(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the current state of an Auto-Tailor run."""
    analysis = (
        db.query(NexusResumeAnalysis)
        .filter(
            NexusResumeAnalysis.id == analysis_id,
            NexusResumeAnalysis.user_id == current_user.id
        )
        .first()
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found"
        )

    payload = analysis.analysis or {}
    
    # Return structured format
    return {
        "analysis_id": analysis_id,
        "resume_id": analysis.resume_id,
        "job_description": analysis.job_description,
        "status": payload.get("status", "unknown"),
        "current_iteration": payload.get("current_iteration", 0),
        "target_score": payload.get("target_score", 85.0),
        "latest_score": payload.get("latest_score", 0.0),
        "resume_data": payload.get("resume_data", {}),
        "scores_breakdown": payload.get("scores_breakdown", {}),
        "critic_feedback": payload.get("critic_feedback", ""),
        "history": payload.get("history", []),
        "pdf_path": payload.get("pdf_path"),
        "created_at": analysis.created_at
    }


@router.post("/auto-tailor/{analysis_id}/respond")
async def respond_to_human_interrupt(
    analysis_id: str,
    payload: RespondTailorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    User responds to the 'paused_for_human' suspension.
    Options:
    - 'approve': Compiles PDF, marks as completed.
    - 'abort': Marks as aborted.
    - 'refine': Resumes workflow starting direct at rewrite/tailoring with user guidance.
    """
    logger.info(f"User responding to Auto-Tailor {analysis_id} with action: {payload.action}")

    analysis_record = (
        db.query(NexusResumeAnalysis)
        .filter(
            NexusResumeAnalysis.id == analysis_id,
            NexusResumeAnalysis.user_id == current_user.id
        )
        .first()
    )
    if not analysis_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found")

    state = analysis_record.analysis or {}
    current_status = state.get("status")

    if current_status != "paused_for_human":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not awaiting user response (current status: {current_status})"
        )

    if payload.action == "abort":
        state["status"] = "aborted"
        analysis_record.analysis = state
        db.commit()
        return {"status": "aborted", "message": "Workflow aborted by user"}

    if payload.action == "approve":
        resume_data = state.get("resume_data", {})
        from app.config import settings
        import os
        from app.services.resume_generator import generate_resume_pdf
        upload_dir = settings.nexus_resume_upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        pdf_filename = f"tailored_{analysis_record.id}.pdf"
        pdf_path = os.path.join(upload_dir, pdf_filename)
        
        result = generate_resume_pdf(resume_data, pdf_path)
        if not result.get("success"):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF generation failed: {result.get('message')}")

        state["status"] = "completed"
        state["pdf_path"] = pdf_path
        analysis_record.analysis = state
        
        resume_file = db.query(NexusResumeFile).filter(NexusResumeFile.resume_id == analysis_record.resume_id).first()
        if resume_file:
            resume_file.status = "analyzed"
            
        db.commit()
        return {
            "status": "completed",
            "pdf_path": pdf_path,
            "message": "Resume approved and compiled successfully."
        }

    if payload.action == "refine":
        if not payload.user_feedback:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User feedback is required for refinement action")

        state["status"] = "running"
        analysis_record.analysis = state
        db.commit()

        from app.services.messaging import publish_message
        job_payload = {
            "job_type": "auto_tailor_reiterate",
            "job_id": analysis_id,
            "user_id": str(current_user.id),
            "user_feedback": payload.user_feedback
        }
        await publish_message("jobs", job_payload)

        return {
            "analysis_id": analysis_id,
            "status": "resubmitted",
            "message": "Auto-Tailor reiteration submitted to background worker."
        }

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid action: {payload.action}")



@router.get("/auto-tailor/{analysis_id}/download")
async def download_tailored_pdf(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Serve the compiled PDF file of a completed Auto-Tailor run."""
    analysis = (
        db.query(NexusResumeAnalysis)
        .filter(
            NexusResumeAnalysis.id == analysis_id,
            NexusResumeAnalysis.user_id == current_user.id
        )
        .first()
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found"
        )

    state = analysis.analysis or {}
    pdf_path = state.get("pdf_path")

    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compiled PDF file not found or not yet generated"
        )

    return FileResponse(
        path=pdf_path,
        filename=f"tailored_resume_{analysis_id[:8]}.pdf",
        media_type="application/pdf"
    )
