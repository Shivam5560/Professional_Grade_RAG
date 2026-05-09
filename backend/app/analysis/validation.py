"""
Data quality pipeline for ingested datasets.

Runs: schema validation → type inference → missing value detection →
      outlier flagging → overall quality score.

Downstream agents use the DataQualityReport for degradation decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DataQualityReport:
    overall_score: float  # 0.0 - 1.0
    total_rows: int
    total_columns: int
    missing_summary: Dict[str, float]  # column -> null_pct
    outlier_summary: Dict[str, int]  # column -> outlier_count (IQR method)
    type_inferences: Dict[str, str]  # column -> inferred_type
    warnings: List[str] = field(default_factory=list)
    numeric_columns: List[str] = field(default_factory=list)
    categorical_columns: List[str] = field(default_factory=list)
    datetime_columns: List[str] = field(default_factory=list)
    text_columns: List[str] = field(default_factory=list)

    @property
    def is_usable(self) -> bool:
        return self.overall_score >= 0.2


def run_data_quality_pipeline(df: pd.DataFrame) -> DataQualityReport:
    """Run the full data quality pipeline on a DataFrame."""
    if df is None or len(df) == 0:
        return DataQualityReport(
            overall_score=0.0,
            total_rows=0,
            total_columns=0,
            missing_summary={},
            outlier_summary={},
            type_inferences={},
            warnings=["Dataset is empty"],
        )

    total_rows = len(df)
    total_columns = len(df.columns)

    # 1. Type inference (catch datetime columns pandas missed)
    type_inferences = _infer_types(df)

    # 2. Classify columns
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64[ns]"]).columns.tolist()
    text_cols = _detect_text_columns(df, categorical_cols)

    # 3. Missing value detection
    missing_summary: Dict[str, float] = {}
    for col in df.columns:
        null_pct = round(float(df[col].isnull().mean()), 4)
        if null_pct > 0:
            missing_summary[col] = null_pct

    # 4. Outlier detection (IQR method on numeric columns)
    outlier_summary: Dict[str, int] = {}
    for col in numeric_cols:
        outliers = _count_outliers_iqr(df[col])
        if outliers > 0:
            outlier_summary[col] = outliers

    # 5. Generate warnings
    warnings: List[str] = []

    # High missing rate
    for col, pct in missing_summary.items():
        if pct > 0.5:
            warnings.append(f"Column '{col}' has >50% missing values ({pct:.1%})")
        elif pct > 0.2:
            warnings.append(f"Column '{col}' has >20% missing values ({pct:.1%})")

    # High outlier rate
    for col, count in outlier_summary.items():
        outlier_pct = count / total_rows if total_rows > 0 else 0
        if outlier_pct > 0.1:
            warnings.append(f"Column '{col}' has >10% outliers ({outlier_pct:.1%})")

    # Constant columns
    for col in numeric_cols:
        if df[col].nunique() <= 1:
            warnings.append(f"Column '{col}' is constant (all same value)")

    # Low row count
    if total_rows < 10:
        warnings.append(f"Dataset has only {total_rows} rows — statistical significance may be low")
    elif total_rows < 50:
        warnings.append(f"Dataset has only {total_rows} rows — some analyses may be unreliable")

    # High cardinality categorical
    for col in categorical_cols:
        unique_count = df[col].nunique()
        if unique_count > 100 and unique_count / total_rows > 0.5:
            warnings.append(f"Column '{col}' has high cardinality ({unique_count} unique values) — may be an ID column")

    # 6. Overall quality score
    overall_score = _compute_quality_score(
        total_rows=total_rows,
        total_columns=total_columns,
        missing_summary=missing_summary,
        outlier_summary=outlier_summary,
        warning_count=len(warnings),
    )

    logger.log_operation(
        "Data quality pipeline complete",
        score=round(overall_score, 3),
        rows=total_rows,
        cols=total_columns,
        warnings=len(warnings),
    )

    return DataQualityReport(
        overall_score=round(overall_score, 4),
        total_rows=total_rows,
        total_columns=total_columns,
        missing_summary=missing_summary,
        outlier_summary=outlier_summary,
        type_inferences=type_inferences,
        warnings=warnings,
        numeric_columns=numeric_cols,
        categorical_columns=categorical_cols,
        datetime_columns=datetime_cols,
        text_columns=text_cols,
    )


def _infer_types(df: pd.DataFrame) -> Dict[str, str]:
    """Infer column types beyond pandas defaults (e.g., datetime detection)."""
    inferences: Dict[str, str] = {}
    for col in df.columns:
        if df[col].dtype == "object":
            sample = df[col].dropna().head(100)
            if len(sample) == 0:
                continue
            # Try datetime inference
            try:
                inferred = pd.to_datetime(sample)
                if inferred.notna().sum() / len(inferred) > 0.8:
                    inferences[col] = "datetime"
            except (ValueError, TypeError):
                pass
    return inferences


def _detect_text_columns(df: pd.DataFrame, categorical_cols: List[str]) -> List[str]:
    """Detect free-text columns (long string content) vs categorical."""
    text_cols: List[str] = []
    for col in categorical_cols:
        sample = df[col].dropna().head(100)
        if len(sample) == 0:
            continue
        avg_len = sample.astype(str).str.len().mean()
        unique_ratio = df[col].nunique() / max(1, len(df[col].dropna()))
        # Text columns: long strings AND high uniqueness
        if avg_len > 50 and unique_ratio > 0.3:
            text_cols.append(col)
    return text_cols


def _count_outliers_iqr(series: pd.Series) -> int:
    """Count outliers using the IQR method (1.5x IQR)."""
    clean = series.dropna()
    if len(clean) < 4:
        return 0
    q1 = float(clean.quantile(0.25))
    q3 = float(clean.quantile(0.75))
    iqr = q3 - q1
    if iqr == 0:
        return 0
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return int(((clean < lower) | (clean > upper)).sum())


def _compute_quality_score(
    total_rows: int,
    total_columns: int,
    missing_summary: Dict[str, float],
    outlier_summary: Dict[str, int],
    warning_count: int,
) -> float:
    """Compute overall data quality score from multiple factors."""
    if total_rows == 0 or total_columns == 0:
        return 0.0

    # Row sufficiency (0-1): 100+ rows = full score
    row_score = min(1.0, np.log10(max(1, total_rows)) / 2.0)

    # Missing value penalty: average completeness across columns
    if missing_summary:
        avg_missing = sum(missing_summary.values()) / total_columns
        completeness = max(0.0, 1.0 - avg_missing)
    else:
        completeness = 1.0

    # Outlier penalty: average outlier rate across columns
    if outlier_summary and total_rows > 0:
        avg_outlier_rate = sum(outlier_summary.values()) / (total_columns * total_rows)
        outlier_score = max(0.0, 1.0 - avg_outlier_rate * 5)
    else:
        outlier_score = 1.0

    # Warning penalty
    warning_penalty = min(0.5, warning_count * 0.1)

    # Weighted composite
    score = (row_score * 0.15 + completeness * 0.50 + outlier_score * 0.25 + (1.0 - warning_penalty) * 0.10)
    return round(min(1.0, max(0.0, score)), 4)
