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
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
    """
    Upload resume and extract text (no LLM call on upload).
    Text is cached for analysis.
    """
    from app.services.nexus_ai.simple_extractor import extract_text_from_file
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    resume_id = _generate_resume_id(user)
    file_path = await _save_resume_file(file, resume_id)

    # Extract text from file (no LLM)
    logger.info(f"Extracting text from resume {resume_id}")
    try:
        resume_text = extract_text_from_file(file_path)
        extracted_data = {"_raw_text": resume_text[:50000]}
        extraction_status = "uploaded"
        logger.info(f"Resume {resume_id} text extracted successfully ({len(resume_text)} chars)")
    except Exception as e:
        logger.error(f"Failed to extract resume text: {e}")
        extracted_data = {"_extraction_failed": True, "_error": str(e)}
        extraction_status = "uploaded"

    record = NexusResumeFile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        resume_id=resume_id,
        filename=file.filename,
        filepath=file_path,
        status=extraction_status,
        extracted_data=extracted_data,
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
    """
    Analyze resume against job description using new clean architecture.
    
    New flow (1 LLM call):
      1. Get resume text from cached data or file
      2. Call analyze_resume_v2 (single LLM call + algorithmic scoring)
      3. Save and return results
    """
    from app.services.nexus_ai.simple_extractor import extract_text_from_file
    from app.services.nexus_ai.core.analyzer import analyze_resume_v2
    
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

    # Get resume text
    if resume.extracted_data and resume.extracted_data.get("_raw_text"):
        logger.info(f"Using cached resume text for {resume_id}")
        resume_text = resume.extracted_data.get("_raw_text", "")
    else:
        logger.info(f"Extracting text from file for {resume_id}")
        resume_text = extract_text_from_file(resume.filepath)
        # Cache for future use
        if resume.extracted_data:
            resume.extracted_data["_raw_text"] = resume_text[:50000]
        else:
            resume.extracted_data = {"_raw_text": resume_text[:50000]}
        db.commit()
    
    if not resume_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume text is empty")
    
    # Single LLM call + algorithmic scoring
    logger.info(f"Running analysis for {resume_id} (1 LLM call + scoring)")
    analysis_result = await analyze_resume_v2(resume_text, job_description)
    
    if not analysis_result.get("success"):
        logger.error(f"Analysis failed: {analysis_result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=analysis_result.get("error", "Analysis failed")
        )
    
    overall_score = analysis_result["scores"]["overall"]
    
    # Build analysis payload for database
    analysis_payload = {
        "overall_score": overall_score,
        "fit_category": analysis_result["scores"]["fit_category"],
        "score_breakdown": analysis_result["scores"]["breakdown"],
        
        # Technical/Skills analysis
        "technical_score": {
            "similarity_score": analysis_result["skills_analysis"]["technical_score"],
            "matched_skills": analysis_result["skills_analysis"]["matched_skills"],
            "missing_skills": analysis_result["skills_analysis"]["missing_skills"],
        },
        
        # Grammar/Writing analysis
        "grammar_analysis": (lambda wa: {
            "score": wa.get("score"),
            "clarity_score": wa.get("clarity_score"),
            "action_verbs_used": wa.get("action_verbs_used", []),
            "quantified_achievements": wa.get("quantified_achievements", []),
            "recommendations": wa.get("suggestions", []),
            "section_scores": {},
        })(analysis_result.get("writing_analysis", {})),
        
        # ATS analysis
        "ats_analysis": analysis_result["ats_analysis"],
        
        # Section analysis
        "section_analysis": analysis_result["section_analysis"],
        
        # Recommendations
        "refined_recommendations": analysis_result.get("recommendations", []),
        "refined_justifications": [],  # Populated from match_analysis
        
        # Resume/JD data
        "resume_data": {
            "name": analysis_result["candidate"].get("name"),
            "email": analysis_result["candidate"].get("email"),
            "phone": analysis_result["candidate"].get("phone"),
            "skills": analysis_result["skills_analysis"]["candidate_skills"],
            "experience": analysis_result.get("experience", []),
            "education": analysis_result.get("education", []),
            "certifications": analysis_result.get("certifications", []),
        },
        "jd_data": analysis_result.get("job_analysis", {}),
        "match_analysis": analysis_result.get("match_analysis", {}),
    }
    
    # Build justifications from match analysis
    match_analysis = analysis_result.get("match_analysis", {})
    justifications = []
    if match_analysis.get("experience_match"):
        justifications.append(f"Experience: {match_analysis['experience_match']}")
    if match_analysis.get("education_match"):
        justifications.append(f"Education: {match_analysis['education_match']}")
    if match_analysis.get("overall_fit"):
        justifications.append(f"Overall: {match_analysis['overall_fit']}")
    analysis_payload["refined_justifications"] = justifications
    
    logger.info(f"Analysis complete. Overall score: {overall_score}")
    
    # Save to database
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


def _convert_to_normal_types(data: Dict) -> Dict:
    """Convert numpy types to native Python types recursively."""
    new_data: Dict = {}
    for key, value in data.items():
        if hasattr(value, "item"):
            new_data[key] = value.item()
        elif isinstance(value, dict):
            new_data[key] = _convert_to_normal_types(value)
        elif isinstance(value, list):
            new_data[key] = [item.item() if hasattr(item, "item") else item for item in value]
        else:
            new_data[key] = value
    return new_data


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


def delete_resume(db: Session, user_id: int, resume_id: str) -> bool:
    """
    Delete a resume and all associated data.
    
    Deletes:
    - Resume file from disk
    - Resume record from database
    - All analysis records (cascade)
    - Vector embeddings from pgvector
    
    Returns True if deleted, raises HTTPException if not found.
    """
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
    
    # Delete file from disk
    if resume.filepath and os.path.exists(resume.filepath):
        try:
            os.remove(resume.filepath)
        except OSError:
            pass  # File already gone
    
    # Delete vector embeddings for this resume
    try:
        from app.services.nexus_resume_vector_store import get_nexus_resume_vector_store
        vector_store = get_nexus_resume_vector_store()
        vector_store.delete_by_resume_id(resume_id)
    except Exception:
        pass  # Vector store deletion is best-effort
    
    # Delete database records (analyses cascade automatically)
    db.delete(resume)
    db.commit()
    
    return True
