from __future__ import annotations

import pandas as pd
import pytest

from app.studios.data_analyst.domain import ColumnSemanticType
from app.studios.data_analyst.profiling import (
    fingerprint_dataframe,
    profile_dataframe,
)


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "revenue": [10.0, 20.0, None, 40.0, 50.0, 100.0],
            "region": ["north", "south", "north", "south", "north", "south"],
            "event_at": [
                "2026-01-01",
                "2026-01-02",
                "2026-01-03",
                "2026-01-04",
                "2026-01-05",
                "2026-01-06",
            ],
            "active": pd.Series([True, False, True, True, False, True], dtype="boolean"),
            "customer_id": ["C-001", "C-002", "C-003", "C-004", "C-005", "C-006"],
            "notes": [
                "first order arrived early",
                "customer requested a callback",
                "invoice corrected after review",
                "renewal conversation is pending",
                "account expanded into a new team",
                "support case closed successfully",
            ],
        }
    )


def test_fingerprint_is_deterministic_sensitive_and_non_mutating() -> None:
    frame = sample_frame()
    original = frame.copy(deep=True)

    first = fingerprint_dataframe(frame)
    second = fingerprint_dataframe(frame.copy(deep=True))
    changed = frame.copy(deep=True)
    changed.loc[0, "revenue"] = 11.0

    assert first == second
    assert first != fingerprint_dataframe(changed)
    assert len(first) == 64
    pd.testing.assert_frame_equal(frame, original)


def test_fingerprint_includes_schema_index_and_order() -> None:
    frame = sample_frame()

    reordered = frame[["region", "revenue", "event_at", "active", "customer_id", "notes"]]
    reindexed = frame.copy(deep=True)
    reindexed.index = range(10, 16)

    assert fingerprint_dataframe(frame) != fingerprint_dataframe(reordered)
    assert fingerprint_dataframe(frame) != fingerprint_dataframe(reindexed)


def test_profile_infers_semantic_types_and_quality_statistics() -> None:
    frame = sample_frame()
    original = frame.copy(deep=True)

    profile = profile_dataframe(frame)
    by_name = {column.name: column for column in profile.columns}

    assert profile.dataset_snapshot_id.startswith("dataset-")
    assert profile.fingerprint == fingerprint_dataframe(frame)
    assert profile.row_count == 6
    assert profile.column_count == 6
    assert by_name["revenue"].semantic_type is ColumnSemanticType.NUMERIC
    assert by_name["region"].semantic_type is ColumnSemanticType.CATEGORICAL
    assert by_name["event_at"].semantic_type is ColumnSemanticType.DATETIME
    assert by_name["active"].semantic_type is ColumnSemanticType.BOOLEAN
    assert by_name["customer_id"].semantic_type is ColumnSemanticType.IDENTIFIER
    assert by_name["notes"].semantic_type is ColumnSemanticType.TEXT
    assert by_name["revenue"].missing_count == 1
    assert by_name["revenue"].missing_fraction == pytest.approx(1 / 6)
    assert by_name["region"].unique_count == 2
    assert by_name["region"].unique_fraction == pytest.approx(1 / 3)
    assert by_name["revenue"].skewness is not None
    assert by_name["revenue"].skewness > 0
    assert by_name["region"].skewness is None
    pd.testing.assert_frame_equal(frame, original)


def test_profile_detects_numeric_identifier_by_name_and_uniqueness() -> None:
    profile = profile_dataframe(
        pd.DataFrame({"account_id": [101, 102, 103, 104], "amount": [1, 2, 3, 4]})
    )
    by_name = {column.name: column for column in profile.columns}

    assert by_name["account_id"].semantic_type is ColumnSemanticType.IDENTIFIER
    assert by_name["amount"].semantic_type is ColumnSemanticType.NUMERIC


def test_profile_supports_empty_dataframes() -> None:
    profile = profile_dataframe(
        pd.DataFrame(
            {
                "amount": pd.Series(dtype="float64"),
                "enabled": pd.Series(dtype="bool"),
            }
        )
    )

    assert profile.row_count == 0
    assert profile.column_count == 2
    assert all(column.missing_fraction == 0.0 for column in profile.columns)
    assert all(column.unique_fraction == 0.0 for column in profile.columns)


def test_profile_rejects_duplicate_or_non_string_column_names() -> None:
    duplicate = pd.DataFrame([[1, 2]], columns=["amount", "amount"])
    non_string = pd.DataFrame([[1]], columns=[7])

    with pytest.raises(ValueError, match="unique"):
        profile_dataframe(duplicate)
    with pytest.raises(TypeError, match="strings"):
        profile_dataframe(non_string)
