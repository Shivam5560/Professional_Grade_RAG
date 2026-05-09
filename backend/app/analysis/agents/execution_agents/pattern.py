"""
Pattern Agent — clustering, dimensionality reduction, and anomaly detection.

Uses sklearn. Pure computation (no LLM), degrades gracefully when sklearn
is unavailable or data is insufficient.
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


class PatternAgent(BaseAnalysisAgent):
    """Unsupervised pattern discovery: clustering, PCA, anomaly detection."""

    def __init__(self):
        super().__init__(agent_name="pattern", use_structured_llm=False)

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

        if len(numeric_cols) < 2 or len(df) < 10:
            findings.append(AgentFinding(
                metric="insufficient_data",
                value={"numeric_count": len(numeric_cols), "row_count": len(df)},
                description=f"Need ≥2 numeric columns and ≥10 rows for pattern analysis. Found {len(numeric_cols)} numeric cols, {len(df)} rows.",
                significance=0.1,
            ))
            return AgentResult(
                agent_name="pattern",
                task_id=params.get("task_id", ""),
                findings=findings,
                confidence=0.1,
            )

        try:
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            findings.append(AgentFinding(
                metric="sklearn_unavailable",
                value="scikit-learn not installed",
                description="Pattern analysis requires scikit-learn.",
                significance=0.0,
            ))
            return AgentResult(
                agent_name="pattern",
                task_id=params.get("task_id", ""),
                findings=findings,
                confidence=0.0,
            )

        # Prepare scaled numeric data
        numeric_df = df[numeric_cols].dropna()
        if len(numeric_df) < 10:
            findings.append(AgentFinding(
                metric="too_few_clean_rows",
                value={"clean_rows": len(numeric_df)},
                description="After dropping nulls, too few rows remain for pattern analysis.",
                significance=0.1,
            ))
            return AgentResult(
                agent_name="pattern",
                task_id=params.get("task_id", ""),
                findings=findings,
                confidence=0.1,
            )

        try:
            scaler = StandardScaler()
            scaled = scaler.fit_transform(numeric_df)
        except Exception as exc:
            logger.log_error("Scaling failed for pattern analysis", exc)
            errors = True
            findings.append(AgentFinding(
                metric="scaling_error",
                value=str(exc),
                description="Failed to scale data for pattern analysis.",
                significance=0.0,
            ))
            return AgentResult(
                agent_name="pattern",
                task_id=params.get("task_id", ""),
                findings=findings,
                confidence=0.0,
            )

        # 1. PCA (2 components)
        n_components = min(2, len(numeric_cols))
        try:
            pca = PCA(n_components=n_components)
            pca_result = pca.fit_transform(scaled)
            explained_var = pca.explained_variance_ratio_.tolist()
            cum_explained = float(np.sum(explained_var))

            # Top contributing features for PC1
            pc1_loadings = list(zip(numeric_cols, pca.components_[0]))
            pc1_loadings.sort(key=lambda x: abs(x[1]), reverse=True)

            findings.append(AgentFinding(
                metric="pca_analysis",
                value={
                    "n_components": n_components,
                    "explained_variance_ratio": [round(v, 4) for v in explained_var],
                    "cumulative_explained": round(cum_explained, 4),
                    "top_pc1_features": [
                        {"column": col, "loading": round(float(ld), 4)}
                        for col, ld in pc1_loadings[:5]
                    ],
                },
                description=(
                    f"PCA: First {n_components} components explain {cum_explained:.1%} of variance. "
                    f"Top PC1 driver: '{pc1_loadings[0][0]}' (loading={pc1_loadings[0][1]:.3f})."
                ),
                significance=0.8 if cum_explained > 0.6 else 0.5,
            ))
        except Exception as exc:
            logger.log_error("PCA failed", exc)
            errors = True

        # 2. K-means clustering (k=2 to 5, pick best silhouette score)
        if len(numeric_df) >= 20:
            try:
                from sklearn.cluster import KMeans
                from sklearn.metrics import silhouette_score

                best_k = 2
                best_silhouette = -1.0
                best_labels = None

                for k in range(2, min(6, len(numeric_df) // 5 + 1)):
                    km = KMeans(n_clusters=k, random_state=42, n_init=10)
                    labels = km.fit_predict(scaled)
                    sil = silhouette_score(scaled, labels)
                    if sil > best_silhouette:
                        best_silhouette = sil
                        best_k = k
                        best_labels = labels

                # Cluster sizes
                if best_labels is not None:
                    unique, counts = np.unique(best_labels, return_counts=True)
                    cluster_sizes = {f"cluster_{int(u)}": int(c) for u, c in zip(unique, counts)}
                    findings.append(AgentFinding(
                        metric="kmeans_clustering",
                        value={
                            "optimal_k": best_k,
                            "silhouette_score": round(best_silhouette, 4),
                            "cluster_sizes": cluster_sizes,
                            "interpretation": (
                                "Well-separated clusters (silhouette > 0.5)." if best_silhouette > 0.5
                                else "Moderate cluster separation (silhouette 0.25–0.5)." if best_silhouette > 0.25
                                else "Weak cluster structure (silhouette < 0.25). Data may not have natural groupings."
                            ),
                        },
                        description=f"K-means found {best_k} clusters (silhouette={best_silhouette:.3f}). Largest cluster has {max(cluster_sizes.values())} points.",
                        significance=0.7 if best_silhouette > 0.3 else 0.4,
                    ))
            except Exception as exc:
                logger.log_error("K-means clustering failed", exc)
                errors = True

        # 3. Anomaly detection (Isolation Forest)
        if len(numeric_df) >= 30:
            try:
                from sklearn.ensemble import IsolationForest

                iso = IsolationForest(contamination=0.05, random_state=42, n_jobs=1)
                anomaly_labels = iso.fit_predict(scaled)
                n_anomalies = int((anomaly_labels == -1).sum())

                findings.append(AgentFinding(
                    metric="anomaly_detection",
                    value={
                        "algorithm": "IsolationForest",
                        "contamination_expected": 0.05,
                        "anomalies_found": n_anomalies,
                        "anomaly_pct": round(n_anomalies / len(scaled) * 100, 2),
                    },
                    description=f"Isolation Forest detected {n_anomalies} potential anomalies ({n_anomalies / len(scaled):.1%} of data). These rows deviate significantly from the norm.",
                    significance=0.7 if n_anomalies > 0 else 0.35,
                ))
            except Exception as exc:
                logger.log_error("Anomaly detection failed", exc)
                errors = True

        # 4. Column cardinality analysis
        for col in quality.categorical_columns:
            unique_count = int(df[col].nunique())
            if unique_count > 50 and unique_count / max(len(df), 1) > 0.5:
                findings.append(AgentFinding(
                    metric=f"high_cardinality_{col}",
                    value={"unique_values": unique_count, "total_rows": len(df), "ratio": round(unique_count / max(len(df), 1), 3)},
                    description=f"Column '{col}' has {unique_count} unique values — may be an ID, not a feature. Consider excluding from analysis.",
                    significance=0.6,
                ))

        confidence = self.compute_confidence(
            num_findings=len(findings),
            has_errors=errors,
            data_quality_score=quality.overall_score,
        )

        return AgentResult(
            agent_name="pattern",
            task_id=params.get("task_id", ""),
            findings=findings,
            confidence=confidence,
        )
