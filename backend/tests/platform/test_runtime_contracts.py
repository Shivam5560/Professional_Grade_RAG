from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.platform.runtime import (
    InvalidRunTransition,
    StudioRun,
    StudioRunState,
    request_run_cancellation,
    transition_run,
)


NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def make_run() -> StudioRun:
    return StudioRun(
        id="run-1",
        owner_id=7,
        studio_id="data-analyst",
        operation="analyze",
        idempotency_key="request-1",
        input_fingerprint="a" * 64,
        created_at=NOW,
        updated_at=NOW,
    )


def test_run_is_frozen():
    run = make_run()

    with pytest.raises(ValidationError):
        run.state = StudioRunState.RUNNING


def test_run_rejects_naive_time():
    with pytest.raises(ValidationError):
        StudioRun(
            id="run-2",
            owner_id=7,
            studio_id="career",
            operation="draft",
            idempotency_key="request-2",
            input_fingerprint="b" * 64,
            created_at=datetime(2026, 7, 17),
            updated_at=NOW,
        )


def test_transition_updates_state_step_progress_and_time():
    later = datetime(2026, 7, 17, 12, 1, tzinfo=timezone.utc)

    running = transition_run(
        make_run(),
        StudioRunState.RUNNING,
        now=later,
        current_step="profile",
        progress=0.25,
    )

    assert running.state is StudioRunState.RUNNING
    assert running.current_step == "profile"
    assert running.progress == 0.25
    assert running.updated_at == later


def test_terminal_state_cannot_transition():
    running = transition_run(make_run(), StudioRunState.RUNNING, now=NOW)
    succeeded = transition_run(running, StudioRunState.SUCCEEDED, now=NOW)

    with pytest.raises(InvalidRunTransition):
        transition_run(succeeded, StudioRunState.RUNNING, now=NOW)


def test_awaiting_input_can_resume_or_cancel():
    running = transition_run(make_run(), StudioRunState.RUNNING, now=NOW)
    waiting = transition_run(running, StudioRunState.AWAITING_INPUT, now=NOW)

    resumed = transition_run(waiting, StudioRunState.RUNNING, now=NOW)
    cancelled = transition_run(waiting, StudioRunState.CANCELLED, now=NOW)

    assert resumed.state is StudioRunState.RUNNING
    assert cancelled.state is StudioRunState.CANCELLED


def test_run_rejects_updated_time_before_creation():
    earlier = datetime(2026, 7, 17, 11, 59, tzinfo=timezone.utc)

    with pytest.raises(ValidationError):
        StudioRun(
            id="run-2",
            owner_id=7,
            studio_id="career",
            operation="draft",
            idempotency_key="request-2",
            input_fingerprint="b" * 64,
            created_at=NOW,
            updated_at=earlier,
        )


def test_transition_rejects_backdated_time_and_progress_regression():
    later = datetime(2026, 7, 17, 12, 1, tzinfo=timezone.utc)
    running = transition_run(
        make_run(),
        StudioRunState.RUNNING,
        now=later,
        progress=0.5,
    )

    with pytest.raises(InvalidRunTransition, match="earlier"):
        transition_run(
            running,
            StudioRunState.AWAITING_INPUT,
            now=NOW,
        )
    with pytest.raises(InvalidRunTransition, match="progress"):
        transition_run(
            running,
            StudioRunState.AWAITING_INPUT,
            now=later,
            progress=0.25,
        )


def test_failed_transition_requires_categorized_failure_code():
    running = transition_run(make_run(), StudioRunState.RUNNING, now=NOW)

    with pytest.raises(InvalidRunTransition, match="failure_code"):
        transition_run(running, StudioRunState.FAILED, now=NOW)

    failed = transition_run(
        running,
        StudioRunState.FAILED,
        now=NOW,
        failure_code="validation-error",
    )
    assert failed.failure_code == "validation-error"


def test_cancellation_request_is_distinct_from_cancelled_completion():
    running = transition_run(make_run(), StudioRunState.RUNNING, now=NOW)
    requested = request_run_cancellation(running, now=NOW)

    assert requested.state is StudioRunState.RUNNING
    assert requested.cancellation_requested is True

    cancelled = transition_run(requested, StudioRunState.CANCELLED, now=NOW)
    assert cancelled.state is StudioRunState.CANCELLED
    assert cancelled.cancellation_requested is True


def test_cancellation_requested_queued_run_can_only_be_cancelled():
    requested = request_run_cancellation(make_run(), now=NOW)

    with pytest.raises(InvalidRunTransition, match="cancellation-requested"):
        transition_run(requested, StudioRunState.RUNNING, now=NOW)

    cancelled = transition_run(requested, StudioRunState.CANCELLED, now=NOW)
    assert cancelled.state is StudioRunState.CANCELLED


def test_cancellation_requested_running_run_can_only_be_cancelled():
    running = transition_run(make_run(), StudioRunState.RUNNING, now=NOW)
    requested = request_run_cancellation(running, now=NOW)

    with pytest.raises(InvalidRunTransition, match="cancellation-requested"):
        transition_run(requested, StudioRunState.AWAITING_INPUT, now=NOW)

    cancelled = transition_run(requested, StudioRunState.CANCELLED, now=NOW)
    assert cancelled.state is StudioRunState.CANCELLED
