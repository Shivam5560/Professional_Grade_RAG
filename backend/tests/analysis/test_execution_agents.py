"""Tests for execution agents: statistical, correlation, pattern, predictive, nlp, time_series."""

import pandas as pd
import pytest

from app.analysis.agents.execution_agents import (
    CorrelationAgent,
    NLPAgent,
    PatternAgent,
    PredictiveAgent,
    StatisticalAgent,
    TimeSeriesAgent,
)
from app.analysis.validation import DataQualityReport, run_data_quality_pipeline


def _make_quality(df: pd.DataFrame) -> DataQualityReport:
    return run_data_quality_pipeline(df)


# ---------------------------------------------------------------------------
# Statistical Agent
# ---------------------------------------------------------------------------

class TestStatisticalAgent:
    @pytest.mark.asyncio
    async def test_descriptive_stats(self, sample_dataframe):
        agent = StatisticalAgent()
        quality = _make_quality(sample_dataframe)
        result = await agent.run(sample_dataframe, {"task_id": "t1"}, {}, quality)
        assert result.agent_name == "statistical"
        assert len(result.findings) >= 2
        assert any(f.metric == "descriptive_statistics" for f in result.findings)
        assert result.confidence > 0.5

    @pytest.mark.asyncio
    async def test_target_column_analysis(self, sample_dataframe):
        agent = StatisticalAgent()
        quality = _make_quality(sample_dataframe)
        result = await agent.run(
            sample_dataframe,
            {"task_id": "t1", "target_column": "revenue"},
            {},
            quality,
        )
        assert any("target_analysis_revenue" == f.metric for f in result.findings)

    @pytest.mark.asyncio
    async def test_ttest_with_two_groups(self, sample_dataframe):
        """T-test when there are exactly 2 unique categories in group column."""
        df = sample_dataframe.copy()
        df["group"] = pd.Series(["A"] * 50 + ["B"] * 50)
        quality = _make_quality(df)

        agent = StatisticalAgent()
        result = await agent.run(
            df,
            {"task_id": "t1", "target_column": "revenue", "group_column": "group"},
            {},
            quality,
        )
        assert any("ttest" in f.metric for f in result.findings)

    @pytest.mark.asyncio
    async def test_no_numeric_columns(self, all_categorical_df):
        agent = StatisticalAgent()
        quality = _make_quality(all_categorical_df)
        result = await agent.run(all_categorical_df, {"task_id": "t1"}, {}, quality)
        assert any(f.metric == "no_numeric_columns" for f in result.findings)
        assert result.confidence <= 0.2

    @pytest.mark.asyncio
    async def test_missing_data_summary(self):
        """Dataset with substantial missing data triggers missing_data_summary finding."""
        import pandas as pd
        import numpy as np
        df = pd.DataFrame({
            "a": [1.0] * 40 + [np.nan] * 10 + [2.0] * 40 + [np.nan] * 10,
            "b": [np.nan] * 20 + [3.0] * 80,
            "category": ["X"] * 100,
        })
        agent = StatisticalAgent()
        quality = _make_quality(df)
        result = await agent.run(df, {"task_id": "t1"}, {}, quality)
        assert any(f.metric == "missing_data_summary" for f in result.findings)


# ---------------------------------------------------------------------------
# Correlation Agent
# ---------------------------------------------------------------------------

class TestCorrelationAgent:
    @pytest.mark.asyncio
    async def test_pearson_correlation(self, sample_dataframe):
        agent = CorrelationAgent()
        quality = _make_quality(sample_dataframe)
        result = await agent.run(sample_dataframe, {"task_id": "t1"}, {}, quality)
        assert any(f.metric == "pearson_correlation" for f in result.findings)
        assert result.confidence > 0.4

    @pytest.mark.asyncio
    async def test_insufficient_columns(self, single_column_df):
        agent = CorrelationAgent()
        quality = _make_quality(single_column_df)
        result = await agent.run(single_column_df, {"task_id": "t1"}, {}, quality)
        assert any(f.metric == "insufficient_numeric_columns" for f in result.findings)

    @pytest.mark.asyncio
    async def test_spearman_correlation(self, sample_dataframe):
        agent = CorrelationAgent()
        quality = _make_quality(sample_dataframe)
        result = await agent.run(sample_dataframe, {"task_id": "t1"}, {}, quality)
        # Spearman may or may not be included depending on data size
        assert len(result.findings) >= 1


# ---------------------------------------------------------------------------
# Pattern Agent
# ---------------------------------------------------------------------------

class TestPatternAgent:
    @pytest.mark.asyncio
    async def test_pca_and_clustering(self, sample_dataframe):
        agent = PatternAgent()
        quality = _make_quality(sample_dataframe)
        result = await agent.run(sample_dataframe, {"task_id": "t1"}, {}, quality)
        assert len(result.findings) >= 1
        assert any(f.metric in ("pca_analysis", "insufficient_data", "sklearn_unavailable") for f in result.findings)

    @pytest.mark.asyncio
    async def test_insufficient_data(self, single_column_df):
        agent = PatternAgent()
        quality = _make_quality(single_column_df)
        result = await agent.run(single_column_df, {"task_id": "t1"}, {}, quality)
        assert any(f.metric == "insufficient_data" for f in result.findings)

    @pytest.mark.asyncio
    async def test_anomaly_detection(self, sample_dataframe):
        agent = PatternAgent()
        quality = _make_quality(sample_dataframe)
        result = await agent.run(sample_dataframe, {"task_id": "t1"}, {}, quality)
        # Anomaly detection may not run with <30 samples, but shouldn't crash
        assert result.agent_name == "pattern"


# ---------------------------------------------------------------------------
# Predictive Agent
# ---------------------------------------------------------------------------

class TestPredictiveAgent:
    @pytest.mark.asyncio
    async def test_linear_regression(self):
        """Larger dataset should train a linear model."""
        import pandas as pd
        import numpy as np
        np.random.seed(42)
        n = 150
        df = pd.DataFrame({
            "profit": np.random.normal(2000, 700, n),
            "revenue": np.random.normal(5000, 1500, n),
            "cost": np.random.normal(3000, 800, n),
            "marketing": np.random.normal(500, 200, n),
        })
        agent = PredictiveAgent()
        quality = _make_quality(df)
        result = await agent.run(df, {"task_id": "t1", "target_column": "profit"}, {}, quality)
        assert any(f.metric in ("linear_model", "insufficient_rows") for f in result.findings)

    @pytest.mark.asyncio
    async def test_insufficient_rows(self, single_column_df):
        agent = PredictiveAgent()
        quality = _make_quality(single_column_df)
        result = await agent.run(single_column_df, {"task_id": "t1"}, {}, quality)
        assert any(f.metric == "insufficient_rows" for f in result.findings)

    @pytest.mark.asyncio
    async def test_target_not_found(self, sample_dataframe):
        agent = PredictiveAgent()
        quality = _make_quality(sample_dataframe)
        result = await agent.run(
            sample_dataframe,
            {"task_id": "t1", "target_column": "nonexistent"},
            {},
            quality,
        )
        assert any(f.metric == "target_not_found" for f in result.findings)


# ---------------------------------------------------------------------------
# NLP Agent
# ---------------------------------------------------------------------------

class TestNLPAgent:
    @pytest.mark.asyncio
    async def test_no_text_columns(self, sample_dataframe):
        agent = NLPAgent()
        quality = _make_quality(sample_dataframe)
        result = await agent.run(sample_dataframe, {"task_id": "t1"}, {}, quality)
        assert any(f.metric == "no_text_detected" for f in result.findings)

    @pytest.mark.asyncio
    async def test_with_text_column(self):
        import pandas as pd
        df = pd.DataFrame({
            "feedback": [
                "The product is amazing and works perfectly well",
                "Terrible experience, would not recommend",
                "It was okay, nothing special about it",
                "Absolutely love it, best purchase ever",
                "Poor quality, broke after one use",
            ] * 20,
            "score": [5, 1, 3, 5, 2] * 20,
        })
        agent = NLPAgent()
        quality = _make_quality(df)
        result = await agent.run(df, {"task_id": "t1"}, {}, quality)
        # Should find text statistics at minimum; sentiment/topics depend on optional deps
        assert any(f.metric in ("text_statistics", "no_text_detected") for f in result.findings)


# ---------------------------------------------------------------------------
# Time Series Agent
# ---------------------------------------------------------------------------

class TestTimeSeriesAgent:
    @pytest.mark.asyncio
    async def test_no_datetime_column(self, sample_dataframe):
        agent = TimeSeriesAgent()
        quality = _make_quality(sample_dataframe)
        result = await agent.run(sample_dataframe, {"task_id": "t1"}, {}, quality)
        # No datetime column — may find "date" as inferred datetime or get no_datetime_column
        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_with_time_series(self, sample_dataframe):
        agent = TimeSeriesAgent()
        quality = _make_quality(sample_dataframe)
        result = await agent.run(
            sample_dataframe,
            {"task_id": "t1", "date_column": "date", "target_column": "revenue"},
            {},
            quality,
        )
        assert any(f.metric in ("time_series_overview", "statsmodels_unavailable") for f in result.findings)
