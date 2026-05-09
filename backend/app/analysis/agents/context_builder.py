"""
Context Builder Agent.
Loads the dataset and builds a rich profile for downstream agents.
Uses DatasetCache to avoid redundant disk I/O.
"""

from __future__ import annotations

from typing import Any, Dict

from app.analysis.cache import DatasetCache
from app.analysis.events import ContextBuiltResult
from app.analysis.validation import run_data_quality_pipeline
from app.services.analysis.data_ingestion import profile_dataframe
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    """Builds dataset context by loading data, profiling, and running quality checks."""

    def run(self, source_id: str, user_id: int, max_rows: int = 50000) -> ContextBuiltResult:
        """Load dataset via cache, build profile and quality report."""
        df = DatasetCache.get_or_load(source_id, str(user_id), max_rows=max_rows)
        profile = profile_dataframe(df)
        quality = run_data_quality_pipeline(df)

        logger.log_operation(
            "Context built",
            rows=profile["row_count"],
            columns=profile["column_count"],
            quality_score=quality.overall_score,
            warnings=len(quality.warnings),
        )

        return ContextBuiltResult(
            dataset_ref=source_id,
            profile_json=profile,
            columns=[c["name"] for c in profile["columns"]],
            row_count=profile["row_count"],
            data_quality=quality,
        )
