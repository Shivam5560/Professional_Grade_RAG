"""
Predictive Agent — supervised modeling for target prediction.

Linear/logistic regression with feature importance via Random Forest.
Uses sklearn. Degrades gracefully for small datasets.

Only runs when config.include_predictive is True.
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


class PredictiveAgent(BaseAnalysisAgent):
    """Supervised predictive modeling."""

    def __init__(self):
        super().__init__(agent_name="predictive", use_structured_llm=False)

    async def run(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any],
        profile: Dict[str, Any],
        quality: DataQualityReport,
    ) -> AgentResult:
        findings: List[AgentFinding] = []
        errors = False

        target = params.get("target_column")
        numeric_cols = quality.numeric_columns
        min_rows = 100
        min_features = 2

        if len(df) < min_rows:
            findings.append(AgentFinding(
                metric="insufficient_rows",
                value={"rows": len(df), "required": min_rows},
                description=f"Predictive modeling needs ≥{min_rows} rows. Found {len(df)}.",
                significance=0.1,
            ))
            return AgentResult(agent_name="predictive", task_id=params.get("task_id", ""), findings=findings, confidence=0.1)

        try:
            from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
            from sklearn.linear_model import LinearRegression, LogisticRegression
            from sklearn.model_selection import cross_val_score, train_test_split
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            findings.append(AgentFinding(metric="sklearn_unavailable", value="scikit-learn not installed", description="Predictive modeling requires scikit-learn.", significance=0.0))
            return AgentResult(agent_name="predictive", task_id=params.get("task_id", ""), findings=findings, confidence=0.0)

        # Prepare features (numeric only for baseline model)
        if not target:
            # Auto-select: use first numeric column with decent variance as target
            if len(numeric_cols) < 2:
                findings.append(AgentFinding(
                    metric="insufficient_features",
                    value={"numeric_count": len(numeric_cols)},
                    description="Need ≥2 numeric columns (features + target).",
                    significance=0.1,
                ))
                return AgentResult(agent_name="predictive", task_id=params.get("task_id", ""), findings=findings, confidence=0.1)
            target = numeric_cols[-1]

        if target not in df.columns:
            findings.append(AgentFinding(metric="target_not_found", value={"target": target}, description=f"Target column '{target}' not in dataset.", significance=0.0))
            return AgentResult(agent_name="predictive", task_id=params.get("task_id", ""), findings=findings, confidence=0.0)

        # Build feature set
        feature_cols = [c for c in numeric_cols if c != target][:10]  # cap at 10 features
        if len(feature_cols) < 1:
            findings.append(AgentFinding(metric="no_features", value="No predictor columns available after removing target.", description="Need at least 1 predictor.", significance=0.0))
            return AgentResult(agent_name="predictive", task_id=params.get("task_id", ""), findings=findings, confidence=0.0)

        model_df = df[feature_cols + [target]].dropna()
        if len(model_df) < min_rows:
            findings.append(AgentFinding(metric="too_few_clean_rows", value={"clean_rows": len(model_df)}, description=f"Only {len(model_df)} complete rows after dropping nulls.", significance=0.1))
            return AgentResult(agent_name="predictive", task_id=params.get("task_id", ""), findings=findings, confidence=0.1)

        X = model_df[feature_cols].values
        y = model_df[target].values

        try:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        except Exception as exc:
            logger.log_error("Feature scaling failed in predictive agent", exc)
            errors = True
            return AgentResult(
                agent_name="predictive",
                task_id=params.get("task_id", ""),
                findings=[AgentFinding(metric="scaling_error", value=str(exc), description="Feature scaling failed.", significance=0.0)],
                confidence=0.0,
            )

        is_classification = _is_categorical_target(model_df[target])

        # ---- Linear Model ----
        try:
            if is_classification:
                model = LogisticRegression(max_iter=1000, random_state=42)
                cv_scores = cross_val_score(model, X_scaled, y, cv=min(3, len(model_df) // 30), scoring="f1_weighted")
                model.fit(X_scaled, y)
                if len(model.classes_) == 2:
                    coefs = model.coef_[0]
                else:
                    coefs = np.mean(np.abs(model.coef_), axis=0)
                model_type = "LogisticRegression"
            else:
                model = LinearRegression()
                cv_scores = cross_val_score(model, X_scaled, y, cv=min(3, len(model_df) // 30), scoring="r2")
                model.fit(X_scaled, y)
                coefs = model.coef_
                model_type = "LinearRegression"

            feature_importance = [
                {"feature": f, "coefficient": round(float(c), 4)}
                for f, c in sorted(zip(feature_cols, coefs), key=lambda x: abs(x[1]), reverse=True)
            ]

            cv_mean = float(np.mean(cv_scores))
            cv_std = float(np.std(cv_scores))

            findings.append(AgentFinding(
                metric="linear_model",
                value={
                    "model_type": model_type,
                    "task_type": "classification" if is_classification else "regression",
                    "target": target,
                    "features": feature_cols,
                    "cv_score_mean": round(cv_mean, 4),
                    "cv_score_std": round(cv_std, 4),
                    "feature_importance": feature_importance,
                },
                description=(
                    f"{model_type} predicting '{target}' using {len(feature_cols)} features. "
                    f"CV score: {cv_mean:.3f} (±{cv_std:.3f}). "
                    f"Top predictor: '{feature_importance[0]['feature']}' (coef={feature_importance[0]['coefficient']:.4f})."
                ),
                significance=0.85 if cv_mean > (0.5 if is_classification else 0.3) else 0.55,
            ))
        except Exception as exc:
            logger.log_error("Linear model training failed", exc)
            errors = True
            findings.append(AgentFinding(metric="linear_model_error", value=str(exc), description="Linear model training failed.", significance=0.0))

        # ---- Feature Importance via Random Forest ----
        if len(feature_cols) >= 2 and len(model_df) >= 150:
            try:
                if is_classification:
                    rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42, n_jobs=1)
                else:
                    rf = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42, n_jobs=1)

                rf.fit(X_scaled, y)
                rf_importance = [
                    {"feature": f, "importance": round(float(imp), 4)}
                    for f, imp in sorted(zip(feature_cols, rf.feature_importances_), key=lambda x: x[1], reverse=True)
                ]

                findings.append(AgentFinding(
                    metric="feature_importance_rf",
                    value={"top_features": rf_importance[:5]},
                    description=f"Random Forest feature importance: top predictor is '{rf_importance[0]['feature']}' (importance={rf_importance[0]['importance']:.4f}).",
                    significance=0.7,
                ))
            except Exception as exc:
                logger.log_error("Random Forest feature importance failed", exc)

        confidence = self.compute_confidence(len(findings), errors, quality.overall_score)

        return AgentResult(agent_name="predictive", task_id=params.get("task_id", ""), findings=findings, confidence=confidence)


def _is_categorical_target(series: pd.Series) -> bool:
    """Heuristic: is this a classification target?"""
    if not pd.api.types.is_numeric_dtype(series):
        return True
    n_unique = series.nunique()
    n_total = len(series.dropna())
    # Few unique values relative to total → likely categorical
    return n_unique <= 10 and n_unique / n_total < 0.05
