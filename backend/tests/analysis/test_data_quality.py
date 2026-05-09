"""Tests for DataQualityReport and run_data_quality_pipeline."""

import pytest

from app.analysis.validation import (
    DataQualityReport,
    _count_outliers_iqr,
    _detect_text_columns,
    _infer_types,
    run_data_quality_pipeline,
)


class TestDataQualityPipeline:
    def test_normal_dataframe(self, sample_dataframe):
        report = run_data_quality_pipeline(sample_dataframe)
        assert report.total_rows == 100
        assert report.total_columns == 8
        assert report.overall_score > 0.5
        assert "revenue" in report.numeric_columns
        assert "region" in report.categorical_columns
        assert report.is_usable

    def test_empty_dataframe(self, empty_dataframe):
        report = run_data_quality_pipeline(empty_dataframe)
        assert report.total_rows == 0
        assert report.overall_score == 0.0
        assert not report.is_usable
        assert "Dataset is empty" in report.warnings

    def test_missing_value_detection(self, sample_dataframe):
        report = run_data_quality_pipeline(sample_dataframe)
        assert "revenue" in report.missing_summary
        assert report.missing_summary["revenue"] > 0

    def test_outlier_detection(self, sample_dataframe):
        report = run_data_quality_pipeline(sample_dataframe)
        assert "revenue" in report.outlier_summary
        assert report.outlier_summary["revenue"] > 0

    def test_warnings_generated(self):
        """Dataset with severe issues produces warnings."""
        import pandas as pd
        import numpy as np
        df = pd.DataFrame({
            "mostly_null": [np.nan] * 70 + [1.0] * 30,
            "all_same": [5] * 100,
            "numeric": list(range(100)),
        })
        df.loc[0:15, "numeric"] = 99999  # Inject many outliers
        report = run_data_quality_pipeline(df)
        assert len(report.warnings) > 0

    def test_small_dataset_warning(self):
        import pandas as pd
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        report = run_data_quality_pipeline(df)
        assert any("only 3 rows" in w for w in report.warnings)


class TestCountOutliersIQR:
    def test_no_outliers(self):
        import pandas as pd
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0] * 10)
        assert _count_outliers_iqr(series) == 0

    def test_has_outliers(self):
        import pandas as pd
        series = pd.Series([1, 2, 3, 4, 5, 100])
        assert _count_outliers_iqr(series) > 0

    def test_small_series(self):
        import pandas as pd
        assert _count_outliers_iqr(pd.Series([1])) == 0


class TestDetectTextColumns:
    def test_detect_long_text(self):
        import pandas as pd
        # Unique long texts — each one different to pass uniqueness threshold
        texts = [f"this is a very long text description number {i} with lots of words " * 5 for i in range(30)]
        df = pd.DataFrame({
            "short": ["a", "b", "c"] * 10,
            "long": texts,
        })
        text_cols = _detect_text_columns(df, ["short", "long"])
        assert "long" in text_cols
        assert "short" not in text_cols


class TestInferTypes:
    def test_infer_datetime(self):
        import pandas as pd
        df = pd.DataFrame({"dates": ["2024-01-01", "2024-02-15", "2024-03-30"] * 10})
        inferences = _infer_types(df)
        assert inferences.get("dates") == "datetime"
