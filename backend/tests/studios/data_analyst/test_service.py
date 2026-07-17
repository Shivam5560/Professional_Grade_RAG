from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from app.platform.quality import ValidationStatus
from app.platform.runtime import StudioRunState
from app.studios.data_analyst import DataAnalystSpecialist
from app.studios.data_analyst.claims import (
    resolve_evidence_value,
    synthesize_claims,
)

NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "revenue": [10.0, 20.0, 30.0, 40.0, 50.0],
            "profit": [1.0, 2.0, 3.0, 4.0, 5.0],
            "region": ["north", "south", "north", "south", "north"],
        }
    )


def analyze(specialist: DataAnalystSpecialist | None = None):
    return (specialist or DataAnalystSpecialist()).analyze(
        sample_frame(),
        "How are revenue and profit related by region?",
        owner_id=7,
        run_id="run-analysis-1",
        idempotency_key="request-1",
        now=NOW,
        business_context={"decision": "quarterly planning"},
    )


def test_specialist_runs_profile_plan_compute_verify_without_llm() -> None:
    result = analyze()

    assert tuple(run.state for run in result.run_history) == (
        StudioRunState.QUEUED,
        StudioRunState.RUNNING,
        StudioRunState.SUCCEEDED,
    )
    assert result.run_history[0].studio_id == "data-analyst"
    assert result.run_history[0].operation == "analyze"
    assert result.run_history[-1].progress == 1.0
    assert result.run_history[-1].current_step == "verified-claims"
    assert result.run_history[0].input_fingerprint == result.profile.fingerprint
    assert {step.method_id for step in result.plan.steps} == {
        "descriptive-summary",
        "categorical-frequency",
        "pearson-correlation",
    }
    assert result.result.output is not None
    assert result.result.output.claims
    assert all(record.evidence.output_digest == record.output_digest for record in result.computations)


def test_every_published_claim_and_number_resolves_to_computation_evidence() -> None:
    result = analyze()
    assert result.result.output is not None
    records_by_evidence = {
        record.evidence.id: record for record in result.computations
    }

    for claim in result.result.output.claims:
        for link in claim.evidence_links:
            assert link.evidence_id in records_by_evidence
            assert (
                resolve_evidence_value(
                    records_by_evidence[link.evidence_id],
                    link.value_path,
                )
                == claim.value
            )

    expected_references = {
        (link.evidence_id, link.value_path)
        for claim in result.result.output.claims
        for link in claim.evidence_links
    }
    assert {
        (reference.source_id, reference.locator)
        for reference in result.result.evidence
    } == expected_references
    assert result.result.quality.input_tokens == 0
    assert result.result.quality.output_tokens == 0
    assert result.result.quality.estimated_cost_usd == 0.0
    assert result.result.quality.abstention_reason is None
    assert result.result.quality.validations[0].status is ValidationStatus.PASS
    assert json.dumps(result.model_dump(mode="json"), allow_nan=False)


def test_specialist_rerun_is_deterministic() -> None:
    first = analyze()
    second = analyze()

    assert first == second
    assert [record.output_digest for record in first.computations] == [
        record.output_digest for record in second.computations
    ]
    assert [record.evidence.id for record in first.computations] == [
        record.evidence.id for record in second.computations
    ]


def test_specialist_abstains_if_synthesized_claim_does_not_resolve() -> None:
    def unsupported_claims(records):
        valid = synthesize_claims(records)
        return (valid[0].model_copy(update={"value": 999_999}),)

    result = analyze(DataAnalystSpecialist(claim_synthesizer=unsupported_claims))

    assert result.run_history[-1].state is StudioRunState.FAILED
    assert result.run_history[-1].failure_code == "claim-verification-failed"
    assert result.result.output is None
    assert result.result.evidence == ()
    assert result.result.quality.abstention_reason == (
        "One or more synthesized claims did not resolve to computation evidence."
    )
    issue = result.result.quality.validations[0]
    assert issue.status is ValidationStatus.ERROR
    assert issue.critical is True
