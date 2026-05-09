"""
Correlation Agent — relationship strength between variables.

Computes Pearson, Spearman rank correlation, top-N strongest pairs,
and correlation clusters. Pure computation (no LLM).
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


class CorrelationAgent(BaseAnalysisAgent):
    """Correlation analysis between numeric columns."""

    def __init__(self):
        super().__init__(agent_name="correlation", use_structured_llm=False)

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

        if len(numeric_cols) < 2:
            findings.append(AgentFinding(
                metric="insufficient_numeric_columns",
                value={"numeric_count": len(numeric_cols)},
                description=f"Need at least 2 numeric columns for correlation analysis. Found {len(numeric_cols)}.",
                significance=0.1,
            ))
            return AgentResult(
                agent_name="correlation",
                task_id=params.get("task_id", ""),
                findings=findings,
                confidence=0.1,
            )

        numeric_df = df[numeric_cols]

        # 1. Pearson correlation matrix
        try:
            pearson = numeric_df.corr().round(4).to_dict()

            # Find strongest pairs (excluding self-correlations)
            strong_pairs = []
            seen = set()
            for i, col_a in enumerate(numeric_cols):
                for col_b in numeric_cols[i + 1:]:
                    val = pearson[col_a][col_b]
                    if not np.isnan(val) and abs(val) > 0.3:
                        direction = "positive" if val > 0 else "negative"
                        strength = "strong" if abs(val) > 0.7 else "moderate" if abs(val) > 0.5 else "weak"
                        strong_pairs.append({
                            "column_a": col_a,
                            "column_b": col_b,
                            "correlation": round(val, 4),
                            "direction": direction,
                            "strength": strength,
                        })

            strong_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            top_n = strong_pairs[:15]

            # Overall interpretation
            top_is_strong = top_n and abs(top_n[0]["correlation"]) > 0.7
            findings.append(AgentFinding(
                metric="pearson_correlation",
                value={
                    "correlation_matrix": pearson,
                    "strongest_relationships": top_n[:5],
                },
                description=(
                    f"Pearson correlation across {len(numeric_cols)} numeric columns. "
                    f"Strongest relationship: {top_n[0]['column_a']} ↔ {top_n[0]['column_b']} "
                    f"(r={top_n[0]['correlation']:.3f}, {top_n[0]['direction']} {top_n[0]['strength']})."
                ) if top_n else f"No notable correlations (|r| > 0.3) among {len(numeric_cols)} numeric columns.",
                significance=0.9 if top_is_strong else 0.55,
            ))
        except Exception as exc:
            logger.log_error("Pearson correlation failed", exc)
            errors = True

        # 2. Spearman rank correlation (robust to non-linear relationships)
        if len(numeric_cols) >= 3 and len(df) > 20:
            try:
                spearman = numeric_df.corr(method="spearman").round(4).to_dict()
                findings.append(AgentFinding(
                    metric="spearman_correlation",
                    value={"correlation_matrix": spearman},
                    description="Spearman rank correlation — captures monotonic (not just linear) relationships. Compare with Pearson to detect non-linear associations.",
                    significance=0.6,
                ))
            except Exception as exc:
                logger.log_error("Spearman correlation failed", exc)

        # 3. Correlation cluster detection — groups of intercorrelated columns
        if len(numeric_cols) >= 4:
            try:
                corr_matrix = numeric_df.corr().abs().values
                num_clusters_found = 0
                cluster_list = []
                assigned = set()
                for i in range(len(numeric_cols)):
                    if i in assigned:
                        continue
                    cluster = [numeric_cols[i]]
                    for j in range(i + 1, len(numeric_cols)):
                        if j not in assigned and corr_matrix[i][j] > 0.7:
                            cluster.append(numeric_cols[j])
                            assigned.add(j)
                    if len(cluster) >= 2:
                        assigned.add(i)
                        cluster_list.append(cluster)
                        num_clusters_found += 1

                if cluster_list:
                    findings.append(AgentFinding(
                        metric="correlation_clusters",
                        value={"clusters": cluster_list, "cluster_count": num_clusters_found},
                        description=f"Found {num_clusters_found} cluster(s) of highly intercorrelated columns (|r| > 0.7). Column groups may be redundant.",
                        significance=0.7,
                    ))
            except Exception as exc:
                logger.log_error("Cluster detection failed", exc)

        confidence = self.compute_confidence(
            num_findings=len(findings),
            has_errors=errors,
            data_quality_score=quality.overall_score,
        )

        return AgentResult(
            agent_name="correlation",
            task_id=params.get("task_id", ""),
            findings=findings,
            confidence=confidence,
        )
