from __future__ import annotations

from collections.abc import Mapping
from itertools import combinations
from math import isfinite
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from app.platform.evidence import ComputationEvidence

from .domain import (
    AnalysisPlan,
    AssumptionResult,
    AssumptionStatus,
    ColumnSemanticType,
    ComputationRecord,
    DatasetProfile,
    MethodDefinition,
    PlanStep,
    canonical_digest,
    canonical_json,
)
from .profiling import fingerprint_dataframe
from .registry import MethodRegistry


class DatasetFingerprintMismatch(ValueError):
    """Raised when execution data differs from the planned snapshot."""


def _finite_float(value: Any) -> float | None:
    result = float(value)
    return result if isfinite(result) else None


def _json_scalar(value: Any) -> str | int | float | bool | None:
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, np.generic):
        return _json_scalar(value.item())
    if isinstance(value, float):
        return value if isfinite(value) else None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (str, bool, int)):
        return value
    raise TypeError(f"unsupported computation scalar: {type(value).__name__}")


def _execute_descriptive(
    frame: pd.DataFrame,
    profile: DatasetProfile,
    step: PlanStep,
) -> tuple[dict[str, Any], tuple[AssumptionResult, ...], tuple[str, ...]]:
    profiles = {column.name: column for column in profile.columns}
    output_columns: dict[str, Any] = {}
    for name in step.input_columns:
        column_profile = profiles[name]
        summary: dict[str, Any] = {
            "semantic_type": column_profile.semantic_type.value,
            "non_null_count": column_profile.non_null_count,
            "missing_count": column_profile.missing_count,
            "missing_fraction": column_profile.missing_fraction,
            "unique_count": column_profile.unique_count,
            "unique_fraction": column_profile.unique_fraction,
        }
        if column_profile.semantic_type is ColumnSemanticType.NUMERIC:
            values = pd.to_numeric(frame[name].dropna(), errors="raise").astype(float)
            summary.update(
                {
                    "mean": _finite_float(values.mean()) if len(values) else None,
                    "standard_deviation": (
                        _finite_float(values.std(ddof=1)) if len(values) > 1 else None
                    ),
                    "minimum": _finite_float(values.min()) if len(values) else None,
                    "median": _finite_float(values.median()) if len(values) else None,
                    "maximum": _finite_float(values.max()) if len(values) else None,
                }
            )
        output_columns[name] = summary

    assumption = AssumptionResult(
        name="valid-snapshot",
        status=AssumptionStatus.PASS,
        detail="The execution fingerprint matches the profiled dataset snapshot.",
    )
    return (
        {
            "row_count": profile.row_count,
            "column_count": profile.column_count,
            "columns": output_columns,
        },
        (assumption,),
        (),
    )


def _execute_frequency(
    frame: pd.DataFrame,
    step: PlanStep,
) -> tuple[dict[str, Any], tuple[AssumptionResult, ...], tuple[str, ...]]:
    include_missing = bool(step.parameters.get("include_missing", True))
    max_categories = int(step.parameters.get("max_categories", 50))
    output_columns: dict[str, Any] = {}
    for name in step.input_columns:
        series = frame[name]
        selected = series if include_missing else series.dropna()
        denominator = len(selected)
        raw_counts = selected.value_counts(dropna=False, sort=False)
        frequencies = [
            {
                "value": _json_scalar(value),
                "count": int(count),
                "fraction": int(count) / denominator if denominator else 0.0,
            }
            for value, count in raw_counts.items()
        ]
        frequencies.sort(
            key=lambda row: (-row["count"], canonical_json(row["value"]))
        )
        output_columns[name] = {"frequencies": frequencies[:max_categories]}

    assumption = AssumptionResult(
        name="categorical-input",
        status=AssumptionStatus.PASS,
        detail="All planned inputs were profiled as categorical or boolean.",
    )
    return {"columns": output_columns}, (assumption,), ()


def _pair_assumptions(
    left: pd.Series,
    right: pd.Series,
    method: MethodDefinition,
) -> dict[str, str]:
    results = {
        "minimum-paired-samples": (
            AssumptionStatus.PASS.value
            if len(left) >= method.minimum_sample_size
            else AssumptionStatus.FAIL.value
        ),
        "non-constant": (
            AssumptionStatus.PASS.value
            if left.nunique() >= 2 and right.nunique() >= 2
            else AssumptionStatus.FAIL.value
        ),
    }
    if method.id == "pearson-correlation":
        skews = (
            _finite_float(left.skew()) if len(left) >= 3 and left.nunique() >= 2 else None,
            _finite_float(right.skew()) if len(right) >= 3 and right.nunique() >= 2 else None,
        )
        results["low-skew"] = (
            AssumptionStatus.PASS.value
            if all(skew is not None and abs(skew) <= 1.0 for skew in skews)
            else AssumptionStatus.WARNING.value
        )
    else:
        results["monotonic-relationship"] = AssumptionStatus.WARNING.value
    return results


def _aggregate_assumptions(
    method: MethodDefinition,
    pair_results: tuple[Mapping[str, str], ...],
) -> tuple[AssumptionResult, ...]:
    results: list[AssumptionResult] = []
    for name in method.required_assumptions:
        statuses = [pair[name] for pair in pair_results]
        if AssumptionStatus.FAIL.value in statuses:
            status = AssumptionStatus.FAIL
        elif AssumptionStatus.WARNING.value in statuses:
            status = AssumptionStatus.WARNING
        else:
            status = AssumptionStatus.PASS
        results.append(
            AssumptionResult(
                name=name,
                status=status,
                detail=f"{status.value} across {len(pair_results)} planned pair(s).",
            )
        )
    return tuple(results)


def _execute_correlation(
    frame: pd.DataFrame,
    step: PlanStep,
    method: MethodDefinition,
) -> tuple[dict[str, Any], tuple[AssumptionResult, ...], tuple[str, ...]]:
    method_name = "pearson" if method.id == "pearson-correlation" else "spearman"
    output_pairs: list[dict[str, Any]] = []
    all_assumptions: list[Mapping[str, str]] = []
    warnings: list[str] = []

    def add_warning(code: str) -> None:
        if code not in warnings:
            warnings.append(code)

    for left_name, right_name in combinations(step.input_columns, 2):
        paired = frame[[left_name, right_name]].dropna()
        left = pd.to_numeric(paired[left_name], errors="raise").astype(float)
        right = pd.to_numeric(paired[right_name], errors="raise").astype(float)
        assumptions = _pair_assumptions(left, right, method)
        all_assumptions.append(assumptions)

        if assumptions["minimum-paired-samples"] == AssumptionStatus.FAIL.value:
            add_warning("insufficient-paired-samples")
        if assumptions["non-constant"] == AssumptionStatus.FAIL.value:
            add_warning("constant-input")

        coefficient: float | None = None
        p_value: float | None = None
        if (
            assumptions["minimum-paired-samples"] == AssumptionStatus.PASS.value
            and assumptions["non-constant"] == AssumptionStatus.PASS.value
        ):
            alternative = str(step.parameters.get("alternative", "two-sided"))
            if method_name == "pearson":
                result = stats.pearsonr(left, right, alternative=alternative)
            else:
                result = stats.spearmanr(left, right, alternative=alternative)
            coefficient = _finite_float(result.statistic)
            p_value = _finite_float(result.pvalue)

        output_pairs.append(
            {
                "method": method_name,
                "columns": [left_name, right_name],
                "coefficient": coefficient,
                "p_value": p_value,
                "sample_count": len(paired),
                "assumption_results": dict(assumptions),
            }
        )

    aggregate = _aggregate_assumptions(method, tuple(all_assumptions))
    return {"pairs": output_pairs}, aggregate, tuple(warnings)


def _topological_steps(plan: AnalysisPlan) -> tuple[PlanStep, ...]:
    remaining = list(plan.steps)
    completed: set[str] = set()
    ordered: list[PlanStep] = []
    while remaining:
        ready = next(
            (
                step
                for step in remaining
                if set(step.prerequisite_step_ids) <= completed
            ),
            None,
        )
        if ready is None:
            raise ValueError("analysis plan contains unresolved dependencies")
        remaining.remove(ready)
        ordered.append(ready)
        completed.add(ready.id)
    return tuple(ordered)


def execute_analysis_plan(
    frame: pd.DataFrame,
    profile: DatasetProfile,
    plan: AnalysisPlan,
    *,
    run_id: str,
    registry: MethodRegistry | None = None,
) -> tuple[ComputationRecord, ...]:
    active_registry = registry or MethodRegistry.initial()
    active_registry.validate_plan(plan)
    if plan.dataset_snapshot_id != profile.dataset_snapshot_id:
        raise DatasetFingerprintMismatch("plan and profile snapshot IDs differ")
    if fingerprint_dataframe(frame) != profile.fingerprint:
        raise DatasetFingerprintMismatch(
            "dataframe fingerprint does not match the planned dataset snapshot"
        )

    records: list[ComputationRecord] = []
    for step in _topological_steps(plan):
        missing_columns = set(step.input_columns) - set(frame.columns)
        if missing_columns:
            raise ValueError(f"planned columns are missing: {sorted(missing_columns)}")
        method = active_registry.get(step.method_id, step.method_version)
        if method.id == "descriptive-summary":
            output, assumption_results, warnings = _execute_descriptive(
                frame, profile, step
            )
        elif method.id == "categorical-frequency":
            output, assumption_results, warnings = _execute_frequency(frame, step)
        elif method.id in {"pearson-correlation", "spearman-correlation"}:
            output, assumption_results, warnings = _execute_correlation(
                frame, step, method
            )
        else:  # Registry validation makes this defensive branch unreachable.
            raise ValueError(f"registered method has no executor: {method.id}")

        output_digest = canonical_digest(output)
        identity = {
            "run_id": run_id,
            "step_id": step.id,
            "method_id": method.id,
            "method_version": method.version,
            "output_digest": output_digest,
        }
        evidence = ComputationEvidence(
            id=f"evidence-{canonical_digest({**identity, 'kind': 'evidence'})[:24]}",
            run_id=run_id,
            dataset_snapshot_id=profile.dataset_snapshot_id,
            method_id=method.id,
            method_version=method.version,
            parameters=step.parameters,
            random_seed=None,
            assumptions={
                result.name: result.status.value for result in assumption_results
            },
            output_digest=output_digest,
            artifact_ids=(),
        )
        records.append(
            ComputationRecord(
                id=f"computation-{canonical_digest({**identity, 'kind': 'record'})[:24]}",
                run_id=run_id,
                step_id=step.id,
                dataset_snapshot_id=profile.dataset_snapshot_id,
                method_id=method.id,
                method_version=method.version,
                parameters=step.parameters,
                random_seed=None,
                code_digest=method.implementation_digest,
                assumption_results=assumption_results,
                output=output,
                output_digest=output_digest,
                warnings=warnings,
                artifact_ids=(),
                evidence=evidence,
            )
        )
    return tuple(records)
