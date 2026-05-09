"""Shared fixtures for analysis tests."""

import pandas as pd
import pytest


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """100-row DataFrame with numeric, categorical, datetime, text columns, nulls, and outliers."""
    import numpy as np

    np.random.seed(42)
    n = 100
    data = {
        "id": range(1, n + 1),
        "revenue": np.random.normal(5000, 1500, n),
        "cost": np.random.normal(3000, 800, n),
        "profit": np.random.normal(2000, 700, n),
        "region": np.random.choice(["North", "South", "East", "West"], n),
        "category": np.random.choice(["A", "B", "C"], n),
        "date": pd.date_range("2024-01-01", periods=n, freq="D"),
        "rating": np.random.uniform(1, 5, n),
    }
    df = pd.DataFrame(data)

    # Inject nulls
    df.loc[10:12, "revenue"] = np.nan
    df.loc[50:54, "cost"] = np.nan
    df.loc[80, "region"] = None

    # Inject outlier
    df.loc[0, "revenue"] = 50000
    df.loc[1, "profit"] = -15000

    return df


@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    return pd.DataFrame()


@pytest.fixture
def single_column_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3, 4, 5]})


@pytest.fixture
def all_categorical_df() -> pd.DataFrame:
    return pd.DataFrame({
        "color": ["red", "blue", "green", "red", "blue"] * 20,
        "size": ["S", "M", "L", "S", "M"] * 20,
    })


@pytest.fixture
def sample_profile() -> dict:
    return {
        "row_count": 100,
        "column_count": 8,
        "numeric_columns": ["revenue", "cost", "profit", "rating"],
        "categorical_columns": ["region", "category"],
        "datetime_columns": ["date"],
        "columns": [
            {"name": c, "dtype": "int64", "null_count": 0, "null_pct": 0.0, "unique_count": 100, "sample_values": [1, 2, 3, 4, 5]}
            for c in ["id", "revenue", "cost", "profit", "region", "category", "date", "rating"]
        ],
        "numeric_summary": {},
    }
