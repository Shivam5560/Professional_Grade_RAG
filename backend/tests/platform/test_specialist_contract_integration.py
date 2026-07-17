from datetime import datetime, timezone

from app.platform.approvals import ApprovalRequest
from app.platform.evidence import (
    ClaimEvidence,
    ComputationEvidence,
    VerificationStatus,
)
from app.platform.quality import AIResult, EvidenceReference, QualityMetadata
from app.platform.runtime import StudioRun, StudioRunState, transition_run


NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def quality(trace_id: str) -> QualityMetadata:
    return QualityMetadata(
        algorithm_versions={"contract-test": "1.0.0"},
        model_versions={},
        prompt_versions={},
        confidence_components={"evidence": 1.0},
        latency_ms=1.0,
        input_tokens=0,
        output_tokens=0,
        estimated_cost_usd=0.0,
        trace_id=trace_id,
    )


def test_data_analyst_result_resolves_to_computation():
    evidence = ComputationEvidence(
        id="ev-compute",
        run_id="run-analysis",
        dataset_snapshot_id="dataset-1",
        method_id="descriptive-summary",
        method_version="1.0.0",
        parameters={},
        assumptions={},
        output_digest="a" * 64,
    )
    result = AIResult[dict](
        output={
            "claim": "Revenue median is 42",
            "evidence_id": evidence.id,
        },
        evidence=(
            EvidenceReference(
                source_id=evidence.id,
                locator="metrics.revenue.median",
            ),
        ),
        quality=quality("trace-analysis"),
    )

    assert result.output is not None
    assert result.output["evidence_id"] == result.evidence[0].source_id


def test_career_draft_waits_for_approval_of_inferred_claim():
    run = StudioRun(
        id="run-career",
        owner_id=7,
        studio_id="career",
        operation="draft",
        idempotency_key="career-1",
        input_fingerprint="b" * 64,
        created_at=NOW,
        updated_at=NOW,
    )
    waiting = transition_run(
        transition_run(run, StudioRunState.RUNNING, now=NOW),
        StudioRunState.AWAITING_INPUT,
        now=NOW,
        current_step="claim-review",
    )
    claim = ClaimEvidence(
        id="claim-1",
        source_id="resume-1",
        locator="page-1:lines-4-5",
        normalized_claim="Led a platform migration",
        verification_status=VerificationStatus.INFERRED,
        confidence=0.7,
    )
    approval = ApprovalRequest(
        id="approval-claim-1",
        run_id=waiting.id,
        owner_id=waiting.owner_id,
        decision_type="inferred-claims",
        proposed_changes=(claim.id,),
        evidence_ids=(claim.source_id,),
        created_at=NOW,
        updated_at=NOW,
    )

    assert waiting.state is StudioRunState.AWAITING_INPUT
    assert approval.proposed_changes == (claim.id,)
