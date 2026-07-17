from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.platform.approvals import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    InvalidApprovalDecision,
    decide_approval,
)
from app.platform.artifacts import create_artifact_revision


NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def make_approval(*, approval_id: str = "approval-1") -> ApprovalRequest:
    return ApprovalRequest(
        id=approval_id,
        run_id="run-1",
        owner_id=7,
        decision_type="final-resume",
        proposed_changes=("draft-1",),
        evidence_ids=("claim-1",),
        created_at=NOW,
        updated_at=NOW,
    )


def test_artifact_revision_is_append_only_and_links_lineage():
    first = create_artifact_revision(
        artifact_id="report-1",
        owner_id=7,
        studio_id="data-analyst",
        run_id="run-1",
        media_type="application/json",
        content_digest="a" * 64,
        created_at=NOW,
        evidence_ids=("ev-1",),
    )
    second = create_artifact_revision(
        artifact_id="report-1",
        owner_id=7,
        studio_id="data-analyst",
        run_id="run-2",
        media_type="application/json",
        content_digest="b" * 64,
        created_at=NOW,
        evidence_ids=("ev-2",),
        previous=first,
    )

    assert first.revision == 1
    assert second.revision == 2
    assert second.supersedes_revision_id == first.revision_id


def test_artifact_revision_requires_changed_content():
    first = create_artifact_revision(
        artifact_id="report-1",
        owner_id=7,
        studio_id="data-analyst",
        run_id="run-1",
        media_type="application/json",
        content_digest="a" * 64,
        created_at=NOW,
    )

    with pytest.raises(ValueError, match="different content"):
        create_artifact_revision(
            artifact_id="report-1",
            owner_id=7,
            studio_id="data-analyst",
            run_id="run-2",
            media_type="application/json",
            content_digest="a" * 64,
            created_at=NOW,
            previous=first,
        )


def test_artifact_rejects_naive_timestamp():
    with pytest.raises(ValidationError):
        create_artifact_revision(
            artifact_id="report-1",
            owner_id=7,
            studio_id="data-analyst",
            run_id="run-1",
            media_type="application/json",
            content_digest="a" * 64,
            created_at=datetime(2026, 7, 17),
        )


def test_artifact_revision_time_cannot_move_backwards():
    first = create_artifact_revision(
        artifact_id="report-1",
        owner_id=7,
        studio_id="data-analyst",
        run_id="run-1",
        media_type="application/json",
        content_digest="a" * 64,
        created_at=NOW,
    )
    earlier = datetime(2026, 7, 17, 11, 59, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="earlier"):
        create_artifact_revision(
            artifact_id="report-1",
            owner_id=7,
            studio_id="data-analyst",
            run_id="run-2",
            media_type="application/json",
            content_digest="b" * 64,
            created_at=earlier,
            previous=first,
        )


def test_pending_approval_accepts_one_terminal_decision():
    approved = decide_approval(
        make_approval(),
        ApprovalDecision.APPROVE,
        reviewer_id=7,
        now=NOW,
        comment="Ready to publish",
    )

    assert approved.status is ApprovalStatus.APPROVED
    assert approved.comment == "Ready to publish"
    with pytest.raises(InvalidApprovalDecision):
        decide_approval(
            approved,
            ApprovalDecision.REJECT,
            reviewer_id=7,
            now=NOW,
        )


def test_revision_decision_requires_comment():
    with pytest.raises(InvalidApprovalDecision, match="require a comment"):
        decide_approval(
            make_approval(approval_id="approval-2"),
            ApprovalDecision.REVISE,
            reviewer_id=7,
            now=NOW,
        )


def test_approval_rejects_naive_timestamp():
    with pytest.raises(ValidationError):
        ApprovalRequest(
            id="approval-3",
            run_id="run-1",
            owner_id=7,
            decision_type="inferred-claims",
            proposed_changes=("claim-2",),
            evidence_ids=("source-1",),
            created_at=datetime(2026, 7, 17),
            updated_at=NOW,
        )


def test_decided_approval_requires_reviewer():
    with pytest.raises(ValidationError):
        ApprovalRequest(
            id="approval-4",
            run_id="run-1",
            owner_id=7,
            decision_type="final-resume",
            proposed_changes=("draft-1",),
            evidence_ids=("claim-1",),
            status=ApprovalStatus.APPROVED,
            created_at=NOW,
            updated_at=NOW,
        )
