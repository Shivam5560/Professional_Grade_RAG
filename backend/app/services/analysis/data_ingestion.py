"""
Data Ingestion utilities for analysis workflows.
Handles saving uploaded files and loading datasets into pandas DataFrames
with bounded file size enforcement.
"""

from __future__ import annotations

import io
import json
import os
from typing import Any, Dict

import pandas as pd
from fastapi import UploadFile

from app.config import settings
from app.utils.logger import get_logger
from app.utils.json_safety import sanitize_json

logger = get_logger(__name__)


class BoundedFileReader:
    """Wraps a file-like object, raising ValueError if exceeded."""

    def __init__(self, stream, max_bytes: int):
        self._stream = stream
        self._max_bytes = max_bytes
        self._bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        chunk = self._stream.read(size)
        self._bytes_read += len(chunk)
        if self._bytes_read > self._max_bytes:
            raise ValueError(
                f"File exceeds maximum allowed size of {self._max_bytes / (1024 * 1024):.0f}MB"
            )
        return chunk


def save_uploaded_file(file: UploadFile, user_id: str) -> str:
    """Save an uploaded file with size enforcement. Returns a source_id."""
    max_bytes = settings.analysis_max_file_size_mb * 1024 * 1024
    source_id = f"{user_id}_{os.urandom(8).hex()}"
    upload_dir = os.path.join(settings.analysis_upload_dir, user_id)
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1].lower()
    dest_path = os.path.join(upload_dir, f"{source_id}{ext}")

    # Read in chunks with size enforcement
    total = 0
    with open(dest_path, "wb") as f:
        while True:
            chunk = file.file.read(8192)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                os.remove(dest_path)
                raise ValueError(
                    f"File exceeds maximum allowed size of {settings.analysis_max_file_size_mb}MB"
                )
            f.write(chunk)

    logger.log_operation("File saved for analysis", source_id=source_id, path=dest_path, size_bytes=total)
    return source_id


def load_dataset(source_id: str, user_id: str, max_rows: int = 50000) -> pd.DataFrame:
    """Load a dataset from a previously uploaded file."""
    return load_dataset_from_disk(source_id, user_id, max_rows)


def load_dataset_from_disk(source_id: str, user_id: str, max_rows: int = 50000) -> pd.DataFrame:
    """Load a dataset from a previously uploaded file."""
    upload_dir = os.path.join(settings.analysis_upload_dir, user_id)

    files = [f for f in os.listdir(upload_dir) if f.startswith(source_id)]
    if not files:
        raise FileNotFoundError(f"No file found for source_id {source_id}")

    file_path = os.path.join(upload_dir, files[0])
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(file_path, nrows=max_rows)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, nrows=max_rows)
    elif ext == ".parquet":
        df = pd.read_parquet(file_path)
        if len(df) > max_rows:
            df = df.head(max_rows)
    elif ext == ".json":
        with open(file_path) as f:
            data = json.load(f)
        if isinstance(data, list):
            df = pd.json_normalize(data)
        else:
            df = pd.json_normalize([data])
        if len(df) > max_rows:
            df = df.head(max_rows)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    logger.log_operation("Dataset loaded", rows=len(df), columns=len(df.columns), source_id=source_id)
    return df


def profile_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a structured profile of a DataFrame for downstream agents."""
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64[ns]"]).columns.tolist()

    profile: Dict[str, Any] = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "datetime_columns": datetime_cols,
        "columns": [],
        "numeric_summary": {},
    }

    for col in df.columns:
        col_info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_pct": round(float(df[col].isnull().mean()), 4),
            "unique_count": int(df[col].nunique()),
            "sample_values": df[col].dropna().head(5).tolist(),
        }
        profile["columns"].append(col_info)

    if numeric_cols:
        profile["numeric_summary"] = df[numeric_cols].describe().to_dict()

    profile["analysis_brief"] = _build_analysis_brief(df, numeric_cols, categorical_cols, datetime_cols)

    return sanitize_json(profile)


def _build_analysis_brief(
    df: pd.DataFrame,
    numeric_cols: list[str],
    categorical_cols: list[str],
    datetime_cols: list[str],
) -> Dict[str, Any]:
    """Create a compact analyst brief that helps LLM agents build a story from a raw CSV/XLSX."""
    likely_targets = _infer_likely_targets(df)
    high_missing = [
        {"column": col, "missing_pct": round(float(df[col].isna().mean()), 4)}
        for col in df.columns
        if df[col].isna().mean() >= 0.1
    ][:8]
    segment_candidates = [
        {"column": col, "unique_count": int(df[col].nunique(dropna=True))}
        for col in categorical_cols
        if 2 <= df[col].nunique(dropna=True) <= 30
    ][:8]
    measure_candidates = [
        col for col in numeric_cols
        if not _looks_like_identifier(col, df[col])
    ][:12]
    return {
        "likely_targets": likely_targets,
        "measure_candidates": measure_candidates,
        "segment_candidates": segment_candidates,
        "time_candidates": datetime_cols[:5],
        "high_missing_columns": high_missing,
        "dataset_shape": "wide" if len(df.columns) >= 30 else "tall" if len(df) >= 10000 else "standard",
    }


def _infer_likely_targets(df: pd.DataFrame) -> list[str]:
    priority_tokens = (
        "target", "label", "outcome", "default", "churn", "conversion", "revenue",
        "profit", "sales", "risk", "score", "status", "retention",
    )
    matches = [
        col for col in df.columns
        if any(token in str(col).lower() for token in priority_tokens)
    ]
    if matches:
        return matches[:6]
    numeric_cols = [
        col for col in df.select_dtypes(include="number").columns
        if not _looks_like_identifier(col, df[col])
    ]
    return numeric_cols[:3]


def _looks_like_identifier(col: str, series: pd.Series) -> bool:
    name = str(col).lower()
    if name in {"id", "row_id", "record_id", "index"} or name.endswith("_id"):
        return True
    non_null = series.dropna()
    if non_null.empty:
        return False
    return pd.api.types.is_numeric_dtype(non_null) and non_null.nunique(dropna=True) / max(len(non_null), 1) > 0.95
