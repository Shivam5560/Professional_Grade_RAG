"""
Resume Generator API routes.
Provides endpoints for generating resumes as PDF or LaTeX.
"""

import os
import tempfile
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, model_validator

from app.services.resume_generator import (
    generate_resume_pdf,
    generate_resume_latex,
    check_latex_available,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/resumegen", tags=["resumegen"])


# ── Pydantic models ────────────────────────────────────────────

class Experience(BaseModel):
    title: str = Field(default="", validation_alias=AliasChoices("title", "position"))
    company: str = ""
    location: str = ""
    dates: str = Field(default="", validation_alias=AliasChoices("dates", "duration"))
    responsibilities: List[str] = []


class Education(BaseModel):
    institution: str = ""
    degree: str = ""
    graduation_date: str = Field(default="", validation_alias=AliasChoices("graduation_date", "duration"))
    gpa: str = ""


class Project(BaseModel):
    title: str = Field(default="", validation_alias=AliasChoices("title", "name"))
    descriptions: List[str] = Field(default_factory=list, validation_alias=AliasChoices("descriptions", "description"))

    @model_validator(mode="after")
    def _normalize_descriptions(self):
        if isinstance(self.descriptions, str):
            self.descriptions = [self.descriptions]
        return self


class ResumeData(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    name: str = ""
    email: str = ""
    location: Optional[str] = ""
    linkedin_url: Optional[str] = Field(default="", validation_alias=AliasChoices("linkedin_url", "linkedin"))
    github_url: Optional[str] = Field(default="", validation_alias=AliasChoices("github_url", "github"))
    experiences: List[Experience] = Field(default_factory=list, validation_alias=AliasChoices("experiences", "experience"))
    education: List[Education] = []
    projects: List[Project] = []
    skills: Dict[str, Any] = {}


class GenerateRequest(BaseModel):
    data: ResumeData
    format: str = "pdf"  # "pdf" or "latex"


# ── Routes ─────────────────────────────────────────────────────

@router.get("/health")
async def resumegen_health():
    """Check ResumeGen service and LaTeX availability."""
    latex = check_latex_available()
    return {
        "status": "healthy",
        "latex_available": latex,
        "formats": ["pdf", "latex"] if latex else ["latex"],
    }


@router.post("/generate")
async def generate_resume(req: GenerateRequest):
    """Generate a resume PDF or LaTeX source."""
    resume_data = req.data.dict()
    logger.log_operation("resumegen_generate", format=req.format)

    if req.format == "latex":
        latex_src = generate_resume_latex(resume_data)
        return PlainTextResponse(
            content=latex_src,
            media_type="text/plain",
            headers={"Content-Disposition": 'attachment; filename="resume.tex"'},
        )

    # PDF generation
    if not check_latex_available():
        raise HTTPException(
            status_code=503,
            detail="PDF generation unavailable – pdflatex is not installed. Use format=latex to get the .tex source, or run the LaTeX install script.",
        )

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        result = generate_resume_pdf(resume_data, tmp.name)

    if result["success"]:
        return FileResponse(
            path=result["pdf_path"],
            filename="resume.pdf",
            media_type="application/pdf",
        )

    # Clean up on failure
    if result.get("pdf_path") and os.path.exists(result["pdf_path"]):
        os.unlink(result["pdf_path"])

    raise HTTPException(status_code=500, detail=result.get("message", "PDF generation failed"))
