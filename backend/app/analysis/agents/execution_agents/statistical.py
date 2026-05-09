"""
Statistical Agent — descriptive and inferential statistics.

Pure computation (no LLM). Uses scipy for statistical tests.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from app.analysis.base import BaseAnalysisAgent
from app.analysis.events import AgentFinding, AgentResult
from app.analysis.validation import DataQualityReport
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StatisticalAgent(BaseAnalysisAgent):
    """Descriptive and inferential statistics on numeric and categorical columns."""

    def __init__(self):
        super().__init__(agent_name="statistical", use_structured_llm=False)

    async def run(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any],
        profile: Dict[str, Any],
        quality: DataQualityReport,
    ) -> AgentResult:
        findings: List[AgentFinding] = []
        errors = False
        numeric_cols = quality.numeric_columns

        if not numeric_cols:
            findings.append(AgentFinding(
                metric="no_numeric_columns",
                value="No numeric columns found",
                description="Statistical analysis requires numeric data. Only categorical/text columns present.",
                significance=0.1,
            ))
            return AgentResult(
                agent_name="statistical",
                task_id=params.get("task_id", ""),
                findings=findings,
                confidence=0.1,
            )

        # 1. Descriptive statistics for all numeric columns
        try:
            desc = df[numeric_cols].describe().to_dict()
            findings.append(AgentFinding(
                metric="descriptive_statistics",
                value=desc,
                description=f"Summary statistics (count, mean, std, min, quartiles, max) for {len(numeric_cols)} numeric columns.",
                significance=0.85,
            ))
        except Exception as exc:
            logger.log_error("Descriptive stats failed", exc)
            errors = True
            findings.append(AgentFinding(
                metric="descriptive_statistics_error",
                value=str(exc),
                description="Failed to compute descriptive statistics.",
                significance=0.0,
            ))

        # 2. Distribution analysis per column (skewness, kurtosis, normality test)
        for col in numeric_cols[:10]:  # Cap at 10 to avoid bloat
            try:
                clean = df[col].dropna()
                if len(clean) < 8:
                    continue

                skew = float(clean.skew())
                kurt = float(clean.kurtosis())

                # Shapiro-Wilk normality test (sample up to 5000)
                sample = clean.sample(min(5000, len(clean)), random_state=42) if len(clean) > 5000 else clean
                shapiro_stat, shapiro_p = scipy_stats.shapiro(sample)

                interpretation = "normally distributed" if shapiro_p > 0.05 else "not normally distributed"
                findings.append(AgentFinding(
                    metric=f"distribution_{col}",
                    value={
                        "mean": round(float(clean.mean()), 4),
                        "median": round(float(clean.median()), 4),
                        "std": round(float(clean.std()), 4),
                        "skewness": round(skew, 4),
                        "kurtosis": round(kurt, 4),
                        "shapiro_p_value": round(shapiro_p, 6),
                        "normality_interpretation": interpretation,
                    },
                    description=f"Distribution of '{col}': {interpretation} (Shapiro-Wilk p={shapiro_p:.4f}). Skew={skew:.2f}.",
                    significance=0.75 if abs(skew) > 1.0 else 0.55,
                ))
            except Exception as exc:
                logger.log_error("Distribution analysis failed for column", exc, column=col)
                errors = True

        # 3. Target column deep dive
        target = params.get("target_column")
        if target and target in df.columns and pd.api.types.is_numeric_dtype(df[target]):
            clean = df[target].dropna()
            findings.append(AgentFinding(
                metric=f"target_analysis_{target}",
                value={
                    "count": int(len(clean)),
                    "mean": round(float(clean.mean()), 4),
                    "median": round(float(clean.median()), 4),
                    "std": round(float(clean.std()), 4),
                    "min": round(float(clean.min()), 4),
                    "max": round(float(clean.max()), 4),
                    "p25": round(float(clean.quantile(0.25)), 4),
                    "p75": round(float(clean.quantile(0.75)), 4),
                    "p95": round(float(clean.quantile(0.95)), 4),
                    "iqr": round(float(clean.quantile(0.75) - clean.quantile(0.25)), 4),
                },
                description=f"Detailed distribution of target column '{target}'.",
                significance=0.88,
            ))

        # 4. T-tests if group_column specified
        group_col = params.get("group_column")
        if group_col and group_col in df.columns and target and target in df.columns:
            groups = df[group_col].dropna().unique()
            if len(groups) == 2:
                try:
                    g1 = df[df[group_col] == groups[0]][target].dropna()
                    g2 = df[df[group_col] == groups[1]][target].dropna()
                    if len(g1) > 1 and len(g2) > 1:
                        t_stat, t_p = scipy_stats.ttest_ind(g1, g2)
                        significance = 0.9 if t_p < 0.05 else 0.55
                        findings.append(AgentFinding(
                            metric=f"ttest_{target}_by_{group_col}",
                            value={
                                "group_1": str(groups[0]),
                                "group_2": str(groups[1]),
                                "group_1_mean": round(float(g1.mean()), 4),
                                "group_2_mean": round(float(g2.mean()), 4),
                                "t_statistic": round(float(t_stat), 4),
                                "p_value": round(float(t_p), 6),
                                "significant": t_p < 0.05,
                            },
                            description=f"Independent t-test: {target} differs {'significantly' if t_p < 0.05 else 'insignificantly'} between {groups[0]} and {groups[1]} (p={t_p:.4f}).",
                            significance=significance,
                        ))
                except Exception as exc:
                    logger.log_error("T-test failed", exc)
                    errors = True

        # 5. Categorical frequency analysis
        for cat_col in quality.categorical_columns[:5]:
            try:
                top_n = df[cat_col].value_counts().head(10).to_dict()
                unique_count = int(df[cat_col].nunique())
                findings.append(AgentFinding(
                    metric=f"categorical_{cat_col}",
                    value={"top_categories": {str(k): int(v) for k, v in top_n.items()}, "unique_count": unique_count},
                    description=f"'{cat_col}' has {unique_count} unique values. Top category: '{list(top_n.keys())[0]}' ({list(top_n.values())[0]} occurrences).",
                    significance=0.6,
                ))
            except Exception:
                pass

        # 6. Missing value summary
        missing_cols = [c for c, pct in quality.missing_summary.items() if pct > 0.05]
        if missing_cols:
            findings.append(AgentFinding(
                metric="missing_data_summary",
                value={c: quality.missing_summary[c] for c in missing_cols},
                description=f"{len(missing_cols)} columns have >5% missing values. Highest: '{missing_cols[0]}' ({quality.missing_summary[missing_cols[0]]:.1%}).",
                significance=0.7,
            ))

        confidence = self.compute_confidence(
            num_findings=len(findings),
            has_errors=errors,
            data_quality_score=quality.overall_score,
        )

        return AgentResult(
            agent_name="statistical",
            task_id=params.get("task_id", ""),
            findings=findings,
            confidence=confidence,
        )
