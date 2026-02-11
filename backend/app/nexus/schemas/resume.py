"""Pydantic schemas for Nexus resume scoring."""

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime


class ResumeUploadResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    resume_id: str
    status: str
    uploaded_at: datetime
    user_id: int


class ResumeListItem(BaseModel):
    id: int
    file_name: str
    file_path: str
    resume_id: str
    status: str
    uploaded_at: datetime
    user_id: int


class ResumeListResponse(BaseModel):
    count: int
    list: List[ResumeListItem]


class ResumeAnalyzeRequest(BaseModel):
    user_id: int
    resume_id: str
    job_description: str


class ResumeAnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    analysis_id: int


class ResumeHistoryItem(BaseModel):
    analysis_id: int
    resume_id: str
    file_name: str
    overall_score: Optional[float]
    created_at: datetime


class ResumeHistoryResponse(BaseModel):
    items: List[ResumeHistoryItem]
    total: int


class DashboardResponse(BaseModel):
    user: Dict[str, Any]
    resume_stats: Dict[str, Any]
    overall_counts: Dict[str, int]
    latest_analysis: Optional[Dict[str, Any]]
    monthly_stats: List[Dict[str, Any]]
