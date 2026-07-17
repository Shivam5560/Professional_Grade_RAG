from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.platform.evidence import ComputationEvidence
from app.studios.data_analyst.domain import (
    AnalysisPlan,
    ColumnProfile,
    ColumnSemanticType,
    ComputationRecord,
    DatasetProfile,
    MethodDefinition,
    PlanStep,
    canonical_digest,
)


def make_step(
    step_id: str,
    *,
    prerequisites: tuple[str, ...] = (),
) -> PlanStep:
    return PlanStep(
        id=step_id,
        method_id="descriptive-summary",
        method_version="1.0.0",
        input_columns=("revenue",),
        parameters={"quantiles": [0.5]},
        prerequisite_step_ids=prerequisites,
        assumptions=("minimum-sample-size",),
        rationale="Establish a deterministic dataset baseline.",
    )


def make_record() -> ComputationRecord:
    evidence = ComputationEvidence(
        id="evidence-1",
        run_id="run-1",
        dataset_snapshot_id="dataset-1",
        method_id="descriptive-summary",
        method_version="1.0.0",
        parameters={"columns": ["revenue"]},
        assumptions={"minimum-sample-size": "pass"},
        output_digest="a" * 64,
    )
    return ComputationRecord(
        id="computation-1",
        run_id="run-1",
        step_id="descriptive",
        dataset_snapshot_id="dataset-1",
        method_id="descriptive-summary",
        method_version="1.0.0",
        parameters={"columns": ["revenue"]},
        random_seed=None,
        code_digest="b" * 64,
        assumption_results=(),
        output={"row_count": 3, "columns": {"revenue": {"mean": 2.0}}},
        output_digest="a" * 64,
        evidence=evidence,
    )


def test_profile_and_method_contracts_are_frozen_and_json_safe() -> None:
    column = ColumnProfile(
        name="revenue",
        dtype="float64",
        semantic_type=ColumnSemanticType.NUMERIC,
        non_null_count=2,
        missing_count=1,
        missing_fraction=1 / 3,
        unique_count=2,
        unique_fraction=1.0,
        skewness=None,
    )
    profile = DatasetProfile(
        dataset_snapshot_id="dataset-1",
        fingerprint="c" * 64,
        row_count=3,
        column_count=1,
        columns=(column,),
    )
    method = MethodDefinition(
        id="descriptive-summary",
        version="1.0.0",
        supported_semantic_types=(ColumnSemanticType.NUMERIC,),
        minimum_sample_size=1,
        required_assumptions=("minimum-sample-size",),
        default_parameters={"quantiles": [0.5]},
        cost_class="low",
        output_schema="Per-column descriptive statistics.",
        limitations=("Does not establish causality.",),
        implementation_digest="d" * 64,
    )

    with pytest.raises(ValidationError):
        profile.row_count = 4
    with pytest.raises(TypeError):
        method.default_parameters["quantiles"] = (0.25,)
    with pytest.raises(AttributeError):
        method.default_parameters["quantiles"].append(0.75)
    assert json.dumps(profile.model_dump(mode="json"), allow_nan=False)
    assert method.model_dump(mode="json")["default_parameters"] == {
        "quantiles": [0.5]
    }


def test_analysis_plan_rejects_duplicate_step_ids() -> None:
    step = make_step("descriptive")

    with pytest.raises(ValidationError, match="unique"):
        AnalysisPlan(
            id="plan-1",
            dataset_snapshot_id="dataset-1",
            registry_version="1.0.0",
            steps=(step, step),
        )


def test_analysis_plan_rejects_missing_dependency() -> None:
    step = make_step("correlation", prerequisites=("missing",))

    with pytest.raises(ValidationError, match="unknown prerequisite"):
        AnalysisPlan(
            id="plan-1",
            dataset_snapshot_id="dataset-1",
            registry_version="1.0.0",
            steps=(step,),
        )


def test_analysis_plan_rejects_dependency_cycle() -> None:
    first = make_step("first", prerequisites=("second",))
    second = make_step("second", prerequisites=("first",))

    with pytest.raises(ValidationError, match="acyclic"):
        AnalysisPlan(
            id="plan-1",
            dataset_snapshot_id="dataset-1",
            registry_version="1.0.0",
            steps=(first, second),
        )


def test_computation_record_payload_is_deeply_frozen_and_json_safe() -> None:
    record = make_record()

    with pytest.raises(TypeError):
        record.output["row_count"] = 9
    with pytest.raises(TypeError):
        record.output["columns"]["revenue"]["mean"] = 8.0
    with pytest.raises(AttributeError):
        record.parameters["columns"].append("profit")

    payload = record.model_dump(mode="json")
    assert payload["parameters"] == {"columns": ["revenue"]}
    assert payload["output"]["columns"]["revenue"]["mean"] == 2.0
    assert json.dumps(payload, allow_nan=False)


def test_computation_record_requires_matching_evidence() -> None:
    record = make_record()
    mismatched = record.evidence.model_copy(update={"output_digest": "e" * 64})

    with pytest.raises(ValidationError, match="evidence"):
        ComputationRecord.model_validate(
            {**record.model_dump(mode="python"), "evidence": mismatched}
        )


def test_canonical_digest_is_order_independent_for_mapping_keys() -> None:
    assert canonical_digest({"b": 2, "a": [1, 3]}) == canonical_digest(
        {"a": [1, 3], "b": 2}
    )
    assert canonical_digest({"a": [1, 3]}) != canonical_digest({"a": [3, 1]})
