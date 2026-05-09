"""
Report builder service.
Assembles narrative, insights, sections, and charts into a final report payload.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.db.models import AnalysisChartAsset, AnalysisJob, AnalysisReport
from app.utils.logger import get_logger

logger = get_logger(__name__)


def build_and_save_report(
    db: Session,
    job_id: str,
    user_id: int,
    title: str,
    narrative: str,
    sections: List[Dict[str, Any]],
    insights: List[Dict[str, Any]],
    design_spec: Dict[str, Any],
    chart_paths: List[str],
) -> AnalysisReport:
    """Build a final report and persist it to the database."""
    report = AnalysisReport(
        id=f"report_{job_id}",
        job_id=job_id,
        user_id=user_id,
        title=title,
        narrative=narrative,
        sections=sections,
        insights=insights,
        design_spec=design_spec,
    )
    db.add(report)

    for idx, path in enumerate(chart_paths):
        chart = AnalysisChartAsset(
            id=f"chart_{job_id}_{idx}",
            job_id=job_id,
            user_id=user_id,
            filename=f"chart_{idx}.png",
            file_path=path,
        )
        db.add(chart)

    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if job:
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(report)
    logger.log_operation("Report built and saved", job_id=job_id, user_id=user_id, chart_count=len(chart_paths))
    return report
