from __future__ import annotations

import json

import pandas as pd
import pytest

from app.studios.data_analyst.domain import AssumptionStatus, canonical_digest
from app.studios.data_analyst.execution import (
    DatasetFingerprintMismatch,
    MethodPrerequisiteError,
    execute_analysis_plan,
)
from app.studios.data_analyst.planning import build_analysis_plan, parse_intent
from app.studios.data_analyst.profiling import profile_dataframe


def relationship_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 4.0, 5.0],
            "y": [2.0, 4.0, 6.0, 8.0, 10.0],
            "region": ["north", "south", "north", "south", "north"],
        }
    )


def execute(frame: pd.DataFrame, question: str = "relationship between x and y"):
    profile = profile_dataframe(frame)
    plan = build_analysis_plan(profile, parse_intent(question))
    return profile, plan, execute_analysis_plan(
        frame,
        profile,
        plan,
        run_id="run-1",
    )


def test_executes_descriptive_and_frequency_methods_without_mutation() -> None:
    frame = relationship_frame()
    original = frame.copy(deep=True)

    _, _, records = execute(frame, "Summarize the dataset")
    descriptive = next(
        record for record in records if record.method_id == "descriptive-summary"
    )
    frequency = next(
        record for record in records if record.method_id == "categorical-frequency"
    )

    assert descriptive.output["row_count"] == 5
    assert descriptive.output["column_count"] == 3
    assert descriptive.output["columns"]["x"]["mean"] == pytest.approx(3.0)
    assert descriptive.output["columns"]["x"]["median"] == pytest.approx(3.0)
    assert descriptive.output["columns"]["x"]["missing_count"] == 0
    counts = frequency.output["columns"]["region"]["frequencies"]
    assert counts[0] == {"value": "north", "count": 3, "fraction": 0.6}
    assert counts[1] == {"value": "south", "count": 2, "fraction": 0.4}
    pd.testing.assert_frame_equal(frame, original)


def test_executes_real_pearson_with_assumptions_and_evidence() -> None:
    _, _, records = execute(relationship_frame())
    correlation = next(
        record for record in records if record.method_id == "pearson-correlation"
    )
    pair = correlation.output["pairs"][0]

    assert pair["method"] == "pearson"
    assert pair["columns"] == ("x", "y")
    assert pair["coefficient"] == pytest.approx(1.0)
    assert pair["p_value"] == pytest.approx(0.0)
    assert pair["sample_count"] == 5
    assert pair["assumption_results"]["minimum-paired-samples"] == "pass"
    assert pair["assumption_results"]["non-constant"] == "pass"
    assert pair["assumption_results"]["low-skew"] == "pass"
    assert {result.name for result in correlation.assumption_results} == {
        "minimum-paired-samples",
        "non-constant",
        "low-skew",
    }
    assert all(
        result.status is AssumptionStatus.PASS
        for result in correlation.assumption_results
    )
    assert correlation.output_digest == canonical_digest(correlation.output)
    assert correlation.evidence.output_digest == correlation.output_digest
    assert correlation.evidence.method_id == correlation.method_id
    assert correlation.evidence.artifact_ids == ()
    assert correlation.artifact_ids == ()
    assert correlation.warnings == ()
    assert json.dumps(correlation.model_dump(mode="json"), allow_nan=False)


def test_spearman_uses_pairwise_complete_samples_and_reports_p_value() -> None:
    frame = pd.DataFrame(
        {
            "x": [1.0, 1.0, 1.0, 2.0, 20.0, None],
            "y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        }
    )

    _, _, records = execute(frame)
    correlation = next(
        record for record in records if record.method_id == "spearman-correlation"
    )
    pair = correlation.output["pairs"][0]

    assert pair["method"] == "spearman"
    assert pair["sample_count"] == 5
    assert pair["coefficient"] is not None
    assert pair["p_value"] is not None
    assert pair["assumption_results"]["monotonic-relationship"] == "warning"


def test_constant_pair_abstains_from_coefficient_without_scipy_warning() -> None:
    frame = pd.DataFrame({"x": [1, 1, 1, 1], "y": [1, 2, 3, 4]})

    _, _, records = execute(frame)
    correlation = next(
        record for record in records if record.method_id == "spearman-correlation"
    )
    pair = correlation.output["pairs"][0]

    assert pair["coefficient"] is None
    assert pair["p_value"] is None
    assert pair["assumption_results"]["non-constant"] == "fail"
    assert "constant-input" in correlation.warnings


def test_execution_is_deterministic_and_serializable() -> None:
    frame = relationship_frame()
    profile, plan, first = execute(frame)
    second = execute_analysis_plan(
        frame.copy(deep=True),
        profile,
        plan,
        run_id="run-1",
    )

    assert first == second
    assert [record.output_digest for record in first] == [
        record.output_digest for record in second
    ]
    assert [record.evidence.model_dump(mode="json") for record in first] == [
        record.evidence.model_dump(mode="json") for record in second
    ]


def test_execution_rejects_dataset_that_does_not_match_profile() -> None:
    frame = relationship_frame()
    profile = profile_dataframe(frame)
    plan = build_analysis_plan(profile, parse_intent("relationship between x and y"))
    changed = frame.copy(deep=True)
    changed.loc[0, "x"] = 999.0

    with pytest.raises(DatasetFingerprintMismatch, match="fingerprint"):
        execute_analysis_plan(changed, profile, plan, run_id="run-1")


def test_execution_preflights_supported_input_types_before_running() -> None:
    frame = relationship_frame()
    profile = profile_dataframe(frame)
    plan = build_analysis_plan(profile, parse_intent("relationship between x and y"))
    changed_steps = tuple(
        step.model_copy(update={"input_columns": ("x", "region")})
        if step.method_id == "pearson-correlation"
        else step
        for step in plan.steps
    )
    invalid_plan = plan.model_copy(update={"steps": changed_steps})

    with pytest.raises(MethodPrerequisiteError, match="region.*categorical"):
        execute_analysis_plan(
            frame,
            profile,
            invalid_plan,
            run_id="run-1",
        )
