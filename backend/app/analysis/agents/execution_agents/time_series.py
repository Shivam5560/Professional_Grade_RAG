"""
Time Series Agent — temporal analysis.

Trend decomposition, seasonality detection, stationarity tests, and
rolling statistics.

Uses statsmodels (optional). Degrades gracefully when unavailable.
Only runs when config.include_time_series is True and datetime column exists.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.analysis.base import BaseAnalysisAgent
from app.analysis.events import AgentFinding, AgentResult
from app.analysis.validation import DataQualityReport
from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


class TimeSeriesAgent(BaseAnalysisAgent):
    """Time series decomposition, stationarity, and seasonality analysis."""

    def __init__(self):
        super().__init__(agent_name="time_series", use_structured_llm=False)

    async def run(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any],
        profile: Dict[str, Any],
        quality: DataQualityReport,
    ) -> AgentResult:
        findings: List[AgentFinding] = []
        errors = False

        # Resolve date column
        date_col = params.get("date_column") or params.get("target_column")
        if not date_col:
            # Try inferred datetime columns
            if quality.datetime_columns:
                date_col = quality.datetime_columns[0]
            elif quality.type_inferences:
                for col, inferred in quality.type_inferences.items():
                    if inferred == "datetime":
                        date_col = col
                        break

        if not date_col or date_col not in df.columns:
            findings.append(AgentFinding(metric="no_datetime_column", value="No datetime column found", description="Time series analysis requires a datetime column. Specify with date_column config.", significance=0.1))
            return AgentResult(agent_name="time_series", task_id=params.get("task_id", ""), findings=findings, confidence=0.1)

        # Resolve value column
        value_col = params.get("target_column") or params.get("value_column")
        if not value_col or value_col == date_col:
            # Pick first numeric column that isn't the date
            value_col = None
            for c in quality.numeric_columns:
                if c != date_col:
                    value_col = c
                    break

        if not value_col or value_col not in df.columns or value_col == date_col:
            findings.append(AgentFinding(metric="no_value_column", value="No distinct numeric value column found", description="Time series needs a numeric value column separate from the date column to analyze over time.", significance=0.1))
            return AgentResult(agent_name="time_series", task_id=params.get("task_id", ""), findings=findings, confidence=0.1)

        # Prepare time series
        try:
            ts_df = df[[date_col, value_col]].copy()
            ts_df[date_col] = pd.to_datetime(ts_df[date_col], errors="coerce")
            ts_df = ts_df.dropna(subset=[date_col, value_col])

            # Group duplicate dates by calculating their mean to prevent duplicate key alignment issues
            if ts_df[date_col].duplicated().any():
                ts_df = ts_df.groupby(date_col, as_index=False)[value_col].mean()

            ts_df = ts_df.sort_values(date_col)
            ts_df = ts_df.set_index(date_col)

            if len(ts_df) < 10:
                findings.append(AgentFinding(metric="too_few_timepoints", value={"count": len(ts_df)}, description=f"Only {len(ts_df)} time points after cleaning. Need ≥10.", significance=0.1))
                return AgentResult(agent_name="time_series", task_id=params.get("task_id", ""), findings=findings, confidence=0.1)

            series = ts_df[value_col]
        except Exception as exc:
            logger.log_error("Time series preparation failed", exc)
            errors = True
            return AgentResult(agent_name="time_series", task_id=params.get("task_id", ""), findings=[AgentFinding(metric="preparation_error", value=str(exc), description="Failed to prepare time series data.", significance=0.0)], confidence=0.0)

        # 1. Time series overview
        findings.append(AgentFinding(
            metric="time_series_overview",
            value={
                "date_column": date_col,
                "value_column": value_col,
                "start_date": str(series.index.min().date()),
                "end_date": str(series.index.max().date()),
                "num_timepoints": int(len(series)),
                "frequency_hint": _infer_frequency(series.index),
            },
            description=f"{len(series)} time points from {series.index.min().date()} to {series.index.max().date()}.",
            significance=0.55,
        ))

        # 2. Basic statistics
        findings.append(AgentFinding(
            metric="time_series_stats",
            value={
                "mean": round(float(series.mean()), 4),
                "std": round(float(series.std()), 4),
                "min": round(float(series.min()), 4),
                "max": round(float(series.max()), 4),
                "min_date": str(series.idxmin().date()),
                "max_date": str(series.idxmax().date()),
            },
            description=f"'{value_col}' ranges from {series.min():.2f} to {series.max():.2f} (mean={series.mean():.2f}).",
            significance=0.6,
        ))

        # 3. Stationarity test (Augmented Dickey-Fuller)
        if HAS_STATSMODELS:
            try:
                adf_result = adfuller(series.dropna(), autolag="AIC")
                adf_stat = float(adf_result[0])
                adf_p = float(adf_result[1])
                is_stationary = adf_p < 0.05
                findings.append(AgentFinding(
                    metric="stationarity",
                    value={
                        "test": "Augmented Dickey-Fuller",
                        "statistic": round(adf_stat, 4),
                        "p_value": round(adf_p, 6),
                        "is_stationary": is_stationary,
                        "critical_value_5pct": float(adf_result[4]["5%"]),
                    },
                    description=f"{'Stationary' if is_stationary else 'Non-stationary'} series (ADF p={adf_p:.4f}). {'Good for forecasting.' if is_stationary else 'Differencing may be needed for ARIMA models.'}",
                    significance=0.8,
                ))
            except Exception as exc:
                logger.log_error("ADF test failed", exc)
                errors = True

        # 4. Trend decomposition
        if HAS_STATSMODELS and len(series) >= 20:
            try:
                # Determine period
                freq = _infer_frequency(series.index)
                period_map = {"daily": 7, "weekly": 52, "monthly": 12, "quarterly": 4, "yearly": 1}
                period = period_map.get(freq, min(7, len(series) // 2))
                period = max(2, period)

                if len(series) >= period * 2:
                    decomp = seasonal_decompose(series.dropna(), model="additive", period=period, extrapolate_trend="freq")

                    # Extract trend direction
                    trend = decomp.trend.dropna()
                    if len(trend) >= 2:
                        trend_start = float(trend.iloc[:max(2, len(trend) // 10)].mean())
                        trend_end = float(trend.iloc[-max(2, len(trend) // 10):].mean())
                        trend_change_pct = round((trend_end - trend_start) / abs(trend_start) * 100, 1) if trend_start != 0 else 0
                        trend_direction = "upward" if trend_change_pct > 2 else "downward" if trend_change_pct < -2 else "stable"

                        findings.append(AgentFinding(
                            metric="trend_decomposition",
                            value={
                                "method": "additive_decomposition",
                                "period": period,
                                "trend_direction": trend_direction,
                                "trend_change_pct": trend_change_pct,
                                "seasonality_strength": round(float(decomp.seasonal.std()), 4),
                                "residual_std": round(float(decomp.resid.std()), 4),
                            },
                            description=f"Trend is {trend_direction} ({trend_change_pct:+.1f}% change). Seasonality strength: {decomp.seasonal.std():.2f}, residual noise: {decomp.resid.std():.2f}.",
                            significance=0.85 if abs(trend_change_pct) > 5 else 0.6,
                        ))
            except Exception as exc:
                logger.log_error("Trend decomposition failed", exc)
                errors = True
        elif not HAS_STATSMODELS:
            findings.append(AgentFinding(metric="statsmodels_unavailable", value="statsmodels not installed", description="Install statsmodels for time series decomposition: pip install statsmodels", significance=0.0))

        # 5. Rolling statistics
        window = max(2, len(series) // 10)
        try:
            rolling_mean = series.rolling(window=window).mean().dropna()
            rolling_std = series.rolling(window=window).std().dropna()

            # Direction changes in rolling mean
            if len(rolling_mean) >= 3:
                recent_mean = float(rolling_mean.iloc[-1])
                early_mean = float(rolling_mean.iloc[0])
                findings.append(AgentFinding(
                    metric="rolling_statistics",
                    value={
                        "window": window,
                        "rolling_mean_start": round(early_mean, 4),
                        "rolling_mean_end": round(recent_mean, 4),
                        "rolling_mean_change_pct": round((recent_mean - early_mean) / abs(early_mean) * 100, 2) if early_mean != 0 else 0,
                    },
                    description=f"Rolling {window}-period mean changed from {early_mean:.2f} to {recent_mean:.2f}. Volatility (rolling std) may indicate regime changes.",
                    significance=0.55,
                ))
        except Exception as exc:
            logger.log_error("Rolling statistics failed", exc)

        confidence = self.compute_confidence(len(findings), errors, quality.overall_score)
        return AgentResult(agent_name="time_series", task_id=params.get("task_id", ""), findings=findings, confidence=confidence)


def _infer_frequency(index: pd.DatetimeIndex) -> str:
    """Infer the frequency of a datetime index."""
    if len(index) < 2:
        return "unknown"
    diffs = index[1:] - index[:-1]
    median_diff_days = float(np.median(diffs.total_seconds())) / 86400
    if median_diff_days < 1.5:
        return "daily"
    elif median_diff_days < 10:
        return "weekly"
    elif median_diff_days < 40:
        return "monthly"
    elif median_diff_days < 120:
        return "quarterly"
    return "yearly"
