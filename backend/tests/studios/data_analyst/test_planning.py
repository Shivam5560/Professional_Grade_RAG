from __future__ import annotations

import pandas as pd
import pytest

from app.studios.data_analyst.planning import build_analysis_plan, parse_intent
from app.studios.data_analyst.profiling import profile_dataframe
from app.studios.data_analyst.registry import (
    MethodRegistry,
    UnregisteredMethodError,
)


def test_initial_registry_contains_only_versioned_supported_methods() -> None:
    registry = MethodRegistry.initial()

    assert registry.version == "1.0.0"
    assert {method.id for method in registry.methods} == {
        "descriptive-summary",
        "categorical-frequency",
        "pearson-correlation",
        "spearman-correlation",
    }
    for method in registry.methods:
        assert method.version == "1.0.0"
        assert method.required_assumptions
        assert method.output_schema
        assert method.limitations
        assert len(method.implementation_digest) == 64


def test_registry_rejects_unknown_method_and_version() -> None:
    registry = MethodRegistry.initial()

    with pytest.raises(UnregisteredMethodError, match="invented-method"):
        registry.get("invented-method")
    with pytest.raises(UnregisteredMethodError, match="9.0.0"):
        registry.get("descriptive-summary", "9.0.0")

    profile = profile_dataframe(pd.DataFrame({"amount": [1, 2, 3]}))
    plan = build_analysis_plan(profile, parse_intent("Summarize the data"), registry)
    bad_step = plan.steps[0].model_copy(update={"method_id": "invented-method"})
    with pytest.raises(UnregisteredMethodError, match="invented-method"):
        registry.validate_plan(plan.model_copy(update={"steps": (bad_step,)}))


def test_planner_always_adds_descriptive_and_uses_registered_metadata() -> None:
    profile = profile_dataframe(pd.DataFrame({"amount": [1, 2, 3]}))
    registry = MethodRegistry.initial()

    plan = build_analysis_plan(profile, parse_intent("Give me a summary"), registry)

    assert len(plan.steps) == 1
    step = plan.steps[0]
    definition = registry.get(step.method_id, step.method_version)
    assert step.id == "descriptive"
    assert step.method_id == "descriptive-summary"
    assert step.assumptions == definition.required_assumptions
    assert step.parameters == definition.default_parameters
    assert step.input_columns == ("amount",)
    assert step.rationale
    assert registry.validate_plan(plan) is plan


def test_planner_adds_categorical_frequency_from_profile() -> None:
    profile = profile_dataframe(
        pd.DataFrame(
            {
                "amount": [1, 2, 3, 4],
                "region": ["north", "south", "north", "south"],
                "active": [True, False, True, True],
            }
        )
    )

    plan = build_analysis_plan(profile, parse_intent("Summarize the data"))
    frequency = next(
        step for step in plan.steps if step.method_id == "categorical-frequency"
    )

    assert frequency.input_columns == ("region", "active")
    assert frequency.prerequisite_step_ids == ("descriptive",)


@pytest.mark.parametrize(
    ("values", "expected_method"),
    [
        ([1, 2, 3, 4, 5, 6], "pearson-correlation"),
        ([1, 1, 1, 1, 1, 100], "spearman-correlation"),
    ],
)
def test_planner_selects_correlation_from_skew(
    values: list[int],
    expected_method: str,
) -> None:
    profile = profile_dataframe(
        pd.DataFrame({"x": values, "y": [2, 4, 6, 8, 10, 12]})
    )

    plan = build_analysis_plan(
        profile,
        parse_intent("How are x and y related?"),
    )
    correlation = next(
        step for step in plan.steps if step.method_id.endswith("-correlation")
    )

    assert plan.steps[0].method_id == "descriptive-summary"
    assert correlation.method_id == expected_method
    assert correlation.input_columns == ("x", "y")
    assert correlation.prerequisite_step_ids == ("descriptive",)
    assert correlation.assumptions
    assert correlation.rationale


def test_planner_does_not_guess_correlation_without_intent_or_numeric_pair() -> None:
    numeric_profile = profile_dataframe(pd.DataFrame({"x": [1, 2], "y": [3, 4]}))
    mixed_profile = profile_dataframe(
        pd.DataFrame({"x": [1, 2, 3], "region": ["a", "b", "a"]})
    )

    summary = build_analysis_plan(numeric_profile, parse_intent("Summarize x and y"))
    relationship = build_analysis_plan(
        mixed_profile,
        parse_intent("How are x and region related?"),
    )

    assert not any(step.method_id.endswith("-correlation") for step in summary.steps)
    assert not any(
        step.method_id.endswith("-correlation") for step in relationship.steps
    )


def test_planning_is_deterministic_and_context_is_frozen() -> None:
    profile = profile_dataframe(pd.DataFrame({"x": [1, 2, 3], "y": [3, 2, 1]}))
    context = {"decision": "pricing", "segments": ["enterprise"]}
    intent = parse_intent("Relationship between x and y", context)

    first = build_analysis_plan(profile, intent)
    second = build_analysis_plan(profile, intent)

    assert first == second
    assert first.id == second.id
    with pytest.raises(TypeError):
        intent.business_context["decision"] = "retention"
    with pytest.raises(AttributeError):
        intent.business_context["segments"].append("consumer")
