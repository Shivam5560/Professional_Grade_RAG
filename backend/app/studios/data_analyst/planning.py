from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .domain import (
    AnalysisIntent,
    AnalysisPlan,
    ColumnSemanticType,
    DatasetProfile,
    MethodDefinition,
    PlanStep,
    canonical_digest,
)
from .registry import MethodRegistry

_RELATIONSHIP_LANGUAGE = re.compile(
    r"\b(?:correlat\w*|relat(?:ed|ion|ionship)?|associat\w*|"
    r"depend\w*|move together)\b",
    re.IGNORECASE,
)


def parse_intent(
    question: str,
    business_context: Mapping[str, Any] | None = None,
) -> AnalysisIntent:
    normalized = " ".join(question.split())
    objective = f"Answer the dataset question: {normalized}"
    return AnalysisIntent(
        question=normalized,
        objective=objective[:500],
        relationship_requested=bool(_RELATIONSHIP_LANGUAGE.search(normalized)),
        business_context=business_context or {},
    )


def _step(
    *,
    step_id: str,
    method: MethodDefinition,
    columns: tuple[str, ...],
    prerequisites: tuple[str, ...],
    rationale: str,
) -> PlanStep:
    return PlanStep(
        id=step_id,
        method_id=method.id,
        method_version=method.version,
        input_columns=columns,
        parameters=method.default_parameters,
        prerequisite_step_ids=prerequisites,
        assumptions=method.required_assumptions,
        rationale=rationale,
    )


def build_analysis_plan(
    profile: DatasetProfile,
    intent: AnalysisIntent,
    registry: MethodRegistry | None = None,
) -> AnalysisPlan:
    active_registry = registry or MethodRegistry.initial()
    all_columns = tuple(column.name for column in profile.columns)
    categorical_columns = tuple(
        column.name
        for column in profile.columns
        if column.semantic_type
        in {ColumnSemanticType.CATEGORICAL, ColumnSemanticType.BOOLEAN}
    )
    numeric_profiles = tuple(
        column
        for column in profile.columns
        if column.semantic_type is ColumnSemanticType.NUMERIC
    )

    descriptive = active_registry.get("descriptive-summary")
    steps: list[PlanStep] = [
        _step(
            step_id="descriptive",
            method=descriptive,
            columns=all_columns,
            prerequisites=(),
            rationale="Profile every column and establish descriptive baseline values.",
        )
    ]

    if categorical_columns:
        frequency = active_registry.get("categorical-frequency")
        steps.append(
            _step(
                step_id="categorical-frequency",
                method=frequency,
                columns=categorical_columns,
                prerequisites=("descriptive",),
                rationale="Describe observed category prevalence for categorical inputs.",
            )
        )

    if intent.relationship_requested and len(numeric_profiles) >= 2:
        low_skew = all(
            column.skewness is not None and abs(column.skewness) <= 1.0
            for column in numeric_profiles
        )
        method_id = "pearson-correlation" if low_skew else "spearman-correlation"
        correlation = active_registry.get(method_id)
        selection_reason = (
            "All numeric inputs have finite absolute skewness at or below 1.0."
            if low_skew
            else "At least one numeric input is skewed or lacks a stable skew estimate."
        )
        steps.append(
            _step(
                step_id="correlation",
                method=correlation,
                columns=tuple(column.name for column in numeric_profiles),
                prerequisites=("descriptive",),
                rationale=f"{selection_reason} Use {method_id} for association only.",
            )
        )

    plan_payload = {
        "dataset_snapshot_id": profile.dataset_snapshot_id,
        "registry_version": active_registry.version,
        "intent": intent.model_dump(mode="json"),
        "steps": [step.model_dump(mode="json") for step in steps],
    }
    plan = AnalysisPlan(
        id=f"plan-{canonical_digest(plan_payload)[:24]}",
        dataset_snapshot_id=profile.dataset_snapshot_id,
        registry_version=active_registry.version,
        steps=tuple(steps),
    )
    return active_registry.validate_plan(plan)
