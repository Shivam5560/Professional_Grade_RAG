from __future__ import annotations

import base64
import hashlib
import json
import re
from collections.abc import Mapping
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from math import isfinite
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)

from .domain import ColumnProfile, ColumnSemanticType, DatasetProfile

_IDENTIFIER_NAME = re.compile(
    r"(?:^id$|(?:^|[_\s-])id$|identifier$|uuid$|(?:^|[_\s-])key$)",
    re.IGNORECASE,
)
_BOOLEAN_TEXT = frozenset({"true", "false", "yes", "no", "y", "n", "0", "1"})


def _normalize_scalar(value: Any) -> Any:
    if value is None or value is pd.NA or value is pd.NaT:
        return {"$missing": True}
    if isinstance(value, np.datetime64):
        if np.isnat(value):
            return {"$missing": True}
        return {"$datetime": pd.Timestamp(value).isoformat()}
    if isinstance(value, np.timedelta64):
        if np.isnat(value):
            return {"$missing": True}
        return {"$timedelta-ns": int(value / np.timedelta64(1, "ns"))}
    if isinstance(value, np.generic):
        return _normalize_scalar(value.item())
    if isinstance(value, float):
        if np.isnan(value):
            return {"$missing": True}
        if not isfinite(value):
            return {"$float": "infinity" if value > 0 else "-infinity"}
        return value
    if isinstance(value, pd.Timestamp):
        return {"$datetime": value.isoformat()}
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, time):
        return {"$time": value.isoformat()}
    if isinstance(value, pd.Timedelta):
        return {"$timedelta-ns": value.value}
    if isinstance(value, timedelta):
        return {"$timedelta-seconds": value.total_seconds()}
    if isinstance(value, Decimal):
        return {"$decimal": format(value, "f")}
    if isinstance(value, bytes):
        return {"$bytes": base64.b64encode(value).decode("ascii")}
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("dataframe object mappings require string keys")
        return {
            "$mapping": {
                key: _normalize_scalar(item)
                for key, item in sorted(value.items())
            }
        }
    if isinstance(value, (list, tuple)):
        return {"$sequence": [_normalize_scalar(item) for item in value]}
    if isinstance(value, (str, bool, int)):
        return value
    raise TypeError(f"unsupported dataframe scalar type: {type(value).__name__}")


def fingerprint_dataframe(frame: pd.DataFrame) -> str:
    """Hash dataframe schema, index, order, and values without mutating it."""
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")

    payload = {
        "columns": [
            {
                "label": _normalize_scalar(label),
                "dtype": str(dtype),
            }
            for label, dtype in zip(frame.columns.tolist(), frame.dtypes.tolist())
        ],
        "index": {
            "names": [_normalize_scalar(name) for name in frame.index.names],
            "dtypes": (
                [str(level.dtype) for level in frame.index.levels]
                if isinstance(frame.index, pd.MultiIndex)
                else [str(frame.index.dtype)]
            ),
            "values": [_normalize_scalar(value) for value in frame.index.tolist()],
        },
        "rows": [
            [_normalize_scalar(value) for value in row]
            for row in frame.itertuples(index=False, name=None)
        ],
    }
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_identifier(name: str, non_null_count: int, unique_fraction: float) -> bool:
    return bool(
        non_null_count
        and unique_fraction >= 0.95
        and _IDENTIFIER_NAME.search(name)
    )


def _is_boolean_like(non_null: pd.Series) -> bool:
    if non_null.empty:
        return False
    values = non_null.tolist()
    if all(isinstance(value, (bool, np.bool_)) for value in values):
        return True
    if all(isinstance(value, str) for value in values):
        normalized = {value.strip().lower() for value in values}
        return bool(normalized) and normalized <= _BOOLEAN_TEXT
    return False


def _is_datetime_like(non_null: pd.Series) -> bool:
    if non_null.empty:
        return False
    values = non_null.tolist()
    if all(isinstance(value, (datetime, date, pd.Timestamp)) for value in values):
        return True
    if not all(isinstance(value, str) for value in values):
        return False
    parsed = pd.to_datetime(non_null.astype("string"), errors="coerce", format="mixed")
    return float(parsed.notna().mean()) >= 0.9


def _infer_semantic_type(
    name: str,
    series: pd.Series,
    non_null: pd.Series,
    unique_fraction: float,
) -> ColumnSemanticType:
    if is_bool_dtype(series.dtype):
        return ColumnSemanticType.BOOLEAN
    if is_datetime64_any_dtype(series.dtype):
        return ColumnSemanticType.DATETIME
    if _is_identifier(name, len(non_null), unique_fraction):
        return ColumnSemanticType.IDENTIFIER
    if is_numeric_dtype(series.dtype):
        return ColumnSemanticType.NUMERIC
    if _is_boolean_like(non_null):
        return ColumnSemanticType.BOOLEAN
    if _is_datetime_like(non_null):
        return ColumnSemanticType.DATETIME
    if isinstance(series.dtype, pd.CategoricalDtype):
        return ColumnSemanticType.CATEGORICAL
    if non_null.empty or unique_fraction <= 0.5:
        return ColumnSemanticType.CATEGORICAL
    return ColumnSemanticType.TEXT


def _numeric_skewness(
    non_null: pd.Series,
    semantic_type: ColumnSemanticType,
) -> float | None:
    if semantic_type is not ColumnSemanticType.NUMERIC:
        return None
    if len(non_null) < 3 or int(non_null.nunique(dropna=True)) < 2:
        return None
    skewness = float(pd.to_numeric(non_null, errors="raise").astype(float).skew())
    return skewness if isfinite(skewness) else None


def profile_dataframe(frame: pd.DataFrame) -> DatasetProfile:
    """Create a deterministic semantic and quality profile."""
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    columns = frame.columns.tolist()
    if any(not isinstance(name, str) for name in columns):
        raise TypeError("dataframe column names must be strings")
    if len(columns) != len(set(columns)):
        raise ValueError("dataframe column names must be unique")

    row_count = len(frame)
    profiles: list[ColumnProfile] = []
    for name in columns:
        series = frame[name]
        non_null = series.dropna()
        non_null_count = int(non_null.size)
        missing_count = row_count - non_null_count
        unique_count = int(non_null.nunique(dropna=True))
        missing_fraction = missing_count / row_count if row_count else 0.0
        unique_fraction = unique_count / non_null_count if non_null_count else 0.0
        semantic_type = _infer_semantic_type(
            name,
            series,
            non_null,
            unique_fraction,
        )
        profiles.append(
            ColumnProfile(
                name=name,
                dtype=str(series.dtype),
                semantic_type=semantic_type,
                non_null_count=non_null_count,
                missing_count=missing_count,
                missing_fraction=missing_fraction,
                unique_count=unique_count,
                unique_fraction=unique_fraction,
                skewness=_numeric_skewness(non_null, semantic_type),
            )
        )

    fingerprint = fingerprint_dataframe(frame)
    return DatasetProfile(
        dataset_snapshot_id=f"dataset-{fingerprint[:24]}",
        fingerprint=fingerprint,
        row_count=row_count,
        column_count=len(columns),
        columns=tuple(profiles),
    )
