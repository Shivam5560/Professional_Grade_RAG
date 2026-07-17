from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class ApprovalDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"


class InvalidApprovalDecision(ValueError):
    """Raised when an approval cannot accept the requested decision."""


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    owner_id: int = Field(gt=0)
    decision_type: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    proposed_changes: tuple[str, ...] = Field(min_length=1)
    evidence_ids: tuple[str, ...] = Field(min_length=1)
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer_id: int | None = Field(default=None, gt=0)
    comment: str | None = Field(default=None, max_length=2000)
    created_at: datetime
    updated_at: datetime

    @field_validator("id", "run_id", "comment")
    @classmethod
    def reject_blank_string(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("approval fields must not be blank")
        return value

    @field_validator("proposed_changes", "evidence_ids")
    @classmethod
    def reject_blank_identifiers(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("approval fields must not be blank")
        return value

    @field_validator("created_at", "updated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("approval timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def require_decision_audit(self) -> "ApprovalRequest":
        if self.status is ApprovalStatus.PENDING and self.reviewer_id is not None:
            raise ValueError("pending approval cannot have a reviewer")
        if self.status is not ApprovalStatus.PENDING and self.reviewer_id is None:
            raise ValueError("decided approval requires a reviewer")
        if (
            self.status is ApprovalStatus.REVISION_REQUESTED
            and not (self.comment or "").strip()
        ):
            raise ValueError("revision requests require a comment")
        if self.updated_at < self.created_at:
            raise ValueError("approval updated_at cannot precede created_at")
        return self


def decide_approval(
    request: ApprovalRequest,
    decision: ApprovalDecision,
    *,
    reviewer_id: int,
    now: datetime,
    comment: str | None = None,
) -> ApprovalRequest:
    if request.status is not ApprovalStatus.PENDING:
        raise InvalidApprovalDecision("only pending approvals can be decided")
    if reviewer_id <= 0:
        raise InvalidApprovalDecision("reviewer_id must be positive")

    normalized_comment = comment.strip() if comment else None
    if decision is ApprovalDecision.REVISE and not normalized_comment:
        raise InvalidApprovalDecision("revision requests require a comment")

    status_by_decision = {
        ApprovalDecision.APPROVE: ApprovalStatus.APPROVED,
        ApprovalDecision.REJECT: ApprovalStatus.REJECTED,
        ApprovalDecision.REVISE: ApprovalStatus.REVISION_REQUESTED,
    }
    return ApprovalRequest.model_validate(
        {
            **request.model_dump(),
            "status": status_by_decision[decision],
            "reviewer_id": reviewer_id,
            "comment": normalized_comment,
            "updated_at": now,
        }
    )
