from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StudioRunState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_INPUT = "awaiting_input"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


TERMINAL_STATES = frozenset(
    {
        StudioRunState.SUCCEEDED,
        StudioRunState.FAILED,
        StudioRunState.CANCELLED,
        StudioRunState.EXPIRED,
    }
)

ALLOWED_TRANSITIONS = {
    StudioRunState.QUEUED: frozenset(
        {
            StudioRunState.RUNNING,
            StudioRunState.CANCELLED,
            StudioRunState.EXPIRED,
        }
    ),
    StudioRunState.RUNNING: frozenset(
        {
            StudioRunState.AWAITING_INPUT,
            StudioRunState.SUCCEEDED,
            StudioRunState.FAILED,
            StudioRunState.CANCELLED,
        }
    ),
    StudioRunState.AWAITING_INPUT: frozenset(
        {
            StudioRunState.RUNNING,
            StudioRunState.CANCELLED,
            StudioRunState.EXPIRED,
        }
    ),
    StudioRunState.SUCCEEDED: frozenset(),
    StudioRunState.FAILED: frozenset(),
    StudioRunState.CANCELLED: frozenset(),
    StudioRunState.EXPIRED: frozenset(),
}


class InvalidRunTransition(ValueError):
    """Raised when a studio run attempts a forbidden state transition."""


class StudioRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    owner_id: int = Field(gt=0)
    studio_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    operation: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    idempotency_key: str = Field(min_length=1, max_length=200)
    input_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    state: StudioRunState = StudioRunState.QUEUED
    current_step: str | None = None
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    failure_code: str | None = Field(
        default=None,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    cancellation_requested: bool = False
    created_at: datetime
    updated_at: datetime

    @field_validator("id", "idempotency_key", "current_step", "failure_code")
    @classmethod
    def reject_blank_strings(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("string identifiers must not be blank")
        return value

    @field_validator("created_at", "updated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("run timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_lifecycle_invariants(self) -> "StudioRun":
        if self.updated_at < self.created_at:
            raise ValueError("run updated_at cannot precede created_at")
        if self.state is StudioRunState.FAILED and self.failure_code is None:
            raise ValueError("failed run requires a failure_code")
        if self.state is not StudioRunState.FAILED and self.failure_code is not None:
            raise ValueError("failure_code is only valid for failed runs")
        if self.state is StudioRunState.CANCELLED and not self.cancellation_requested:
            raise ValueError("cancelled run requires a cancellation request")
        if self.state is StudioRunState.SUCCEEDED and self.progress != 1.0:
            raise ValueError("succeeded run requires complete progress")
        return self


def transition_run(
    run: StudioRun,
    target: StudioRunState,
    *,
    now: datetime,
    current_step: str | None = None,
    progress: float | None = None,
    failure_code: str | None = None,
) -> StudioRun:
    if target not in ALLOWED_TRANSITIONS[run.state]:
        raise InvalidRunTransition(
            f"cannot transition run from {run.state} to {target}"
        )
    if now < run.updated_at:
        raise InvalidRunTransition("transition time cannot be earlier than updated_at")
    if progress is not None and progress < run.progress:
        raise InvalidRunTransition("run progress cannot move backwards")
    if target is StudioRunState.FAILED and not (failure_code or "").strip():
        raise InvalidRunTransition("failed transition requires a failure_code")
    if target is not StudioRunState.FAILED and failure_code is not None:
        raise InvalidRunTransition("failure_code is only valid for failed transitions")
    if run.cancellation_requested and target is StudioRunState.SUCCEEDED:
        raise InvalidRunTransition("a cancellation-requested run cannot succeed")

    updates: dict[str, object] = {"state": target, "updated_at": now}
    if current_step is not None:
        updates["current_step"] = current_step
    if progress is not None:
        updates["progress"] = progress
    if target is StudioRunState.SUCCEEDED:
        updates["progress"] = 1.0
    if target is StudioRunState.FAILED:
        updates["failure_code"] = failure_code
    if target is StudioRunState.CANCELLED:
        updates["cancellation_requested"] = True

    return StudioRun.model_validate({**run.model_dump(), **updates})


def request_run_cancellation(run: StudioRun, *, now: datetime) -> StudioRun:
    if run.state in TERMINAL_STATES:
        raise InvalidRunTransition(
            f"cannot request cancellation for terminal run {run.state}"
        )
    if now < run.updated_at:
        raise InvalidRunTransition(
            "cancellation request time cannot be earlier than updated_at"
        )
    return StudioRun.model_validate(
        {
            **run.model_dump(),
            "cancellation_requested": True,
            "updated_at": now,
        }
    )
