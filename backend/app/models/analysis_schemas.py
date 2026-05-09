"""
Pydantic schemas for the Data Analysis module.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AnalysisTask(BaseModel):
    task_id: str
    description: str
    required_agents: List[str]


class AgentInvocation(BaseModel):
    agent_name: str
    task_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    agent_name: str
    task_id: str
    findings: List[Dict[str, Any]]
    confidence: float = Field(ge=0.0, le=1.0)


class Insight(BaseModel):
    insight_id: str
    content: str
    significance_score: float = Field(ge=0.0, le=1.0)
    source_agents: List[str]


class ReportSection(BaseModel):
    title: str
    content: str
    chart_id: Optional[str] = None


class DesignSpec(BaseModel):
    theme: str
    color_palette: List[str]
    layout: Literal["grid", "list", "slides"]
    chart_specs: List[Dict[str, Any]]


class AnalysisConfig(BaseModel):
    max_rows: int = Field(default=50000, ge=100, le=1000000)
    include_predictive: bool = True
    include_nlp: bool = False
    include_time_series: bool = False
    output_format: List[Literal["interactive", "pptx"]] = ["interactive"]
    target_columns: Optional[List[str]] = None
    date_column: Optional[str] = None


class AnalysisCreateRequest(BaseModel):
    source_type: Literal["csv", "xlsx", "parquet", "json"]
    query: str = Field(..., min_length=1, max_length=2000)
    config: AnalysisConfig = Field(default_factory=AnalysisConfig)


class AnalysisFromUploadRequest(BaseModel):
    source_id: str = Field(..., min_length=1, description="Source ID from a prior file upload")
    query: str = Field(..., min_length=1, max_length=2000)
    config: AnalysisConfig = Field(default_factory=AnalysisConfig)


class AnalysisJobResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    query: str
    source_type: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress_events: List[Dict[str, Any]] = Field(default_factory=list)


class AnalysisReportResponse(BaseModel):
    report_id: str
    job_id: str
    title: Optional[str]
    narrative: Optional[str]
    sections: List[ReportSection]
    insights: List[Insight]
    chart_urls: List[str]
    slide_deck_url: Optional[str] = None
    created_at: Optional[datetime] = None


class WorkflowProgressEvent(BaseModel):
    step_name: str
    timestamp: datetime
    payload: Dict[str, Any] = Field(default_factory=dict)


class AnalysisListResponse(BaseModel):
    jobs: List[AnalysisJobResponse]
    total: int


class ChartSpec(BaseModel):
    chart_type: Literal["bar", "line", "scatter", "histogram", "heatmap", "box", "pie"]
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    title: str = "Chart"
    colors: Optional[List[str]] = None
