import json

import pytest
from pydantic import ValidationError

from app.platform.evidence import (
    ClaimEvidence,
    ComputationEvidence,
    DerivedEvidence,
    EvidenceKind,
    VerificationStatus,
)


def test_computation_evidence_retains_reproducibility_fields():
    evidence = ComputationEvidence(
        id="ev-1",
        run_id="run-1",
        dataset_snapshot_id="dataset-1",
        method_id="descriptive-summary",
        method_version="1.0.0",
        parameters={"columns": ["revenue"]},
        random_seed=42,
        assumptions={"minimum_rows": "pass"},
        output_digest="a" * 64,
        artifact_ids=("artifact-1",),
    )

    assert evidence.kind is EvidenceKind.COMPUTATION
    assert evidence.random_seed == 42
    assert evidence.parameters["columns"] == ("revenue",)


def test_computation_evidence_mappings_are_frozen():
    evidence = ComputationEvidence(
        id="ev-1",
        run_id="run-1",
        dataset_snapshot_id="dataset-1",
        method_id="descriptive-summary",
        method_version="1.0.0",
        parameters={"column": "revenue"},
        assumptions={},
        output_digest="a" * 64,
    )

    with pytest.raises(TypeError):
        evidence.parameters["column"] = "profit"

    nested = ComputationEvidence(
        id="ev-nested",
        run_id="run-1",
        dataset_snapshot_id="dataset-1",
        method_id="descriptive-summary",
        method_version="1.0.0",
        parameters={"columns": ["revenue"]},
        assumptions={},
        output_digest="c" * 64,
    )
    with pytest.raises(AttributeError):
        nested.parameters["columns"].append("profit")


def test_computation_evidence_serializes_frozen_payloads_as_json():
    evidence = ComputationEvidence(
        id="ev-json",
        run_id="run-1",
        dataset_snapshot_id="dataset-1",
        method_id="descriptive-summary",
        method_version="1.0.0",
        parameters={"columns": ["revenue"]},
        assumptions={"minimum_rows": "pass"},
        output_digest="d" * 64,
    )

    payload = evidence.model_dump(mode="json")

    assert payload["parameters"] == {"columns": ["revenue"]}
    assert payload["assumptions"] == {"minimum_rows": "pass"}

    round_trip = json.loads(evidence.model_dump_json())
    assert round_trip["parameters"] == {"columns": ["revenue"]}


def test_computation_evidence_copies_input_payload_before_freezing():
    source = {"filters": [{"column": "region", "values": ["west"]}]}
    evidence = ComputationEvidence(
        id="ev-copy",
        run_id="run-1",
        dataset_snapshot_id="dataset-1",
        method_id="descriptive-summary",
        method_version="1.0.0",
        parameters=source,
        assumptions={},
        output_digest="e" * 64,
    )

    source["filters"][0]["values"].append("east")

    assert evidence.parameters["filters"][0]["values"] == ("west",)


@pytest.mark.parametrize("unsupported", [{"bad": {"mutable"}}, {"bad": object()}])
def test_computation_evidence_rejects_non_json_values(unsupported):
    with pytest.raises(ValidationError):
        ComputationEvidence(
            id="ev-invalid",
            run_id="run-1",
            dataset_snapshot_id="dataset-1",
            method_id="descriptive-summary",
            method_version="1.0.0",
            parameters=unsupported,
            assumptions={},
            output_digest="f" * 64,
        )


def test_claim_evidence_requires_source_span():
    with pytest.raises(ValidationError):
        ClaimEvidence(
            id="ev-2",
            source_id="resume-1",
            locator=" ",
            normalized_claim="Built a forecasting service",
            verification_status=VerificationStatus.VERIFIED,
            confidence=0.9,
        )


def test_derived_evidence_requires_parent_lineage():
    with pytest.raises(ValidationError):
        DerivedEvidence(
            id="ev-3",
            parent_evidence_ids=(),
            transformation="weighted-match",
            transformation_version="1.0.0",
            output_digest="b" * 64,
        )
