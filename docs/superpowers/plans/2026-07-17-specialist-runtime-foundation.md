# Specialist Runtime Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add immutable, validated shared contracts for specialist-studio runs, evidence, artifacts, and human approvals.

**Architecture:** The new `app.platform` packages contain domain-only Pydantic contracts and pure transition functions. They have no dependency on Data Analyst or Career Studio, database sessions, FastAPI, or model providers. Both studios will consume these interfaces in their own follow-on plans, and persistence adapters will be added alongside the first durable workflows.

**Tech Stack:** Python 3.11, Pydantic 2, `StrEnum`, pytest

## Global Constraints

- Contracts are immutable after construction.
- Blank identifiers and naive datetimes are rejected.
- State transitions are explicit and terminal states cannot transition.
- Evidence is typed as computation, claim, or derived evidence and retains lineage.
- Artifact revisions are append-only and content-addressed.
- Career approvals allow exactly one terminal decision from a pending state.
- No studio-specific package may be imported by `app.platform`.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `backend/app/platform/runtime/contracts.py` | Run states, immutable run record, and transition function |
| `backend/app/platform/runtime/__init__.py` | Public runtime exports |
| `backend/app/platform/evidence/contracts.py` | Typed computation, claim, and derived evidence records |
| `backend/app/platform/evidence/__init__.py` | Public evidence exports |
| `backend/app/platform/artifacts/contracts.py` | Immutable artifact revision and revision factory |
| `backend/app/platform/artifacts/__init__.py` | Public artifact exports |
| `backend/app/platform/approvals/contracts.py` | Approval request, decisions, and pure decision function |
| `backend/app/platform/approvals/__init__.py` | Public approval exports |
| `backend/tests/platform/test_runtime_contracts.py` | Run validation and transition tests |
| `backend/tests/platform/test_evidence_contracts.py` | Evidence validation and lineage tests |
| `backend/tests/platform/test_artifact_approval_contracts.py` | Artifact and approval tests |
| `backend/tests/platform/test_specialist_contract_integration.py` | Cross-contract Data Analyst and Career examples |

### Task 1: Durable Run Contract

**Files:**
- Create: `backend/app/platform/runtime/contracts.py`
- Create: `backend/app/platform/runtime/__init__.py`
- Create: `backend/tests/platform/test_runtime_contracts.py`

**Interfaces:**
- Consumes: Pydantic `BaseModel`, `ConfigDict`, `Field`, and validators.
- Produces: `StudioRunState`, `StudioRun`, `InvalidRunTransition`, and `transition_run(run, target, *, now, current_step=None, progress=None)`.

- [ ] **Step 1: Write the failing run-contract tests**

```python
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.platform.runtime import (
    InvalidRunTransition,
    StudioRun,
    StudioRunState,
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


def test_run_is_frozen_and_rejects_naive_time():
    run = make_run()
    with pytest.raises(ValidationError):
        run.state = StudioRunState.RUNNING
    with pytest.raises(ValidationError):
        StudioRun(
            id="run-2", owner_id=7, studio_id="career", operation="draft",
            idempotency_key="request-2", input_fingerprint="b" * 64,
            created_at=datetime(2026, 7, 17), updated_at=NOW,
        )


def test_transition_updates_state_step_progress_and_time():
    running = transition_run(
        make_run(), StudioRunState.RUNNING, now=NOW,
        current_step="profile", progress=0.25,
    )
    assert running.state is StudioRunState.RUNNING
    assert running.current_step == "profile"
    assert running.progress == 0.25


def test_terminal_state_cannot_transition():
    running = transition_run(make_run(), StudioRunState.RUNNING, now=NOW)
    succeeded = transition_run(running, StudioRunState.SUCCEEDED, now=NOW)
    with pytest.raises(InvalidRunTransition):
        transition_run(succeeded, StudioRunState.RUNNING, now=NOW)


def test_awaiting_input_can_resume_or_cancel():
    running = transition_run(make_run(), StudioRunState.RUNNING, now=NOW)
    waiting = transition_run(running, StudioRunState.AWAITING_INPUT, now=NOW)
    assert transition_run(waiting, StudioRunState.RUNNING, now=NOW).state is StudioRunState.RUNNING
    assert transition_run(waiting, StudioRunState.CANCELLED, now=NOW).state is StudioRunState.CANCELLED
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && PYTHONPATH=. pytest tests/platform/test_runtime_contracts.py -q`

Expected: collection error containing `No module named 'app.platform.runtime'`.

- [ ] **Step 3: Implement the immutable run contract**

```python
from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StudioRunState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_INPUT = "awaiting_input"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


TERMINAL_STATES = frozenset({
    StudioRunState.SUCCEEDED,
    StudioRunState.FAILED,
    StudioRunState.CANCELLED,
    StudioRunState.EXPIRED,
})

ALLOWED_TRANSITIONS = {
    StudioRunState.QUEUED: frozenset({StudioRunState.RUNNING, StudioRunState.CANCELLED, StudioRunState.EXPIRED}),
    StudioRunState.RUNNING: frozenset({StudioRunState.AWAITING_INPUT, StudioRunState.SUCCEEDED, StudioRunState.FAILED, StudioRunState.CANCELLED}),
    StudioRunState.AWAITING_INPUT: frozenset({StudioRunState.RUNNING, StudioRunState.CANCELLED, StudioRunState.EXPIRED}),
    StudioRunState.SUCCEEDED: frozenset(),
    StudioRunState.FAILED: frozenset(),
    StudioRunState.CANCELLED: frozenset(),
    StudioRunState.EXPIRED: frozenset(),
}


class InvalidRunTransition(ValueError):
    pass


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
    failure_code: str | None = None
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


def transition_run(
    run: StudioRun,
    target: StudioRunState,
    *,
    now: datetime,
    current_step: str | None = None,
    progress: float | None = None,
) -> StudioRun:
    if target not in ALLOWED_TRANSITIONS[run.state]:
        raise InvalidRunTransition(f"cannot transition run from {run.state} to {target}")
    updates: dict[str, object] = {"state": target, "updated_at": now}
    if current_step is not None:
        updates["current_step"] = current_step
    if progress is not None:
        updates["progress"] = progress
    if target is StudioRunState.SUCCEEDED:
        updates["progress"] = 1.0
    return StudioRun.model_validate({**run.model_dump(), **updates})
```

Export the four public names from `backend/app/platform/runtime/__init__.py`.

- [ ] **Step 4: Run the run-contract tests**

Run: `cd backend && PYTHONPATH=. pytest tests/platform/test_runtime_contracts.py -q`

Expected: `4 passed`.

- [ ] **Step 5: Commit the run contract**

```bash
git add backend/app/platform/runtime backend/tests/platform/test_runtime_contracts.py
git commit -m "feat(platform): add specialist run contract"
```

### Task 2: Typed Evidence Contracts

**Files:**
- Create: `backend/app/platform/evidence/contracts.py`
- Create: `backend/app/platform/evidence/__init__.py`
- Create: `backend/tests/platform/test_evidence_contracts.py`

**Interfaces:**
- Consumes: no Task 1 types; evidence remains usable outside a live run.
- Produces: `EvidenceKind`, `VerificationStatus`, `ComputationEvidence`, `ClaimEvidence`, and `DerivedEvidence`.

- [ ] **Step 1: Write the failing evidence tests**

```python
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
        id="ev-1", run_id="run-1", dataset_snapshot_id="dataset-1",
        method_id="descriptive-summary", method_version="1.0.0",
        parameters={"columns": ["revenue"]}, random_seed=42,
        assumptions={"minimum_rows": "pass"}, output_digest="a" * 64,
        artifact_ids=("artifact-1",),
    )
    assert evidence.kind is EvidenceKind.COMPUTATION
    assert evidence.random_seed == 42


def test_claim_evidence_requires_source_span_and_status():
    with pytest.raises(ValidationError):
        ClaimEvidence(
            id="ev-2", source_id="resume-1", locator=" ",
            normalized_claim="Built a forecasting service",
            verification_status=VerificationStatus.VERIFIED, confidence=0.9,
        )


def test_derived_evidence_requires_parent_lineage():
    with pytest.raises(ValidationError):
        DerivedEvidence(
            id="ev-3", parent_evidence_ids=(),
            transformation="weighted-match", transformation_version="1.0.0",
            output_digest="b" * 64,
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && PYTHONPATH=. pytest tests/platform/test_evidence_contracts.py -q`

Expected: collection error containing `No module named 'app.platform.evidence'`.

- [ ] **Step 3: Implement typed evidence**

Create `backend/app/platform/evidence/contracts.py`:

```python
from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class EvidenceKind(StrEnum):
    COMPUTATION = "computation"
    CLAIM = "claim"
    DERIVED = "derived"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    DISPUTED = "disputed"
    REJECTED = "rejected"


class ComputationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: Literal[EvidenceKind.COMPUTATION] = EvidenceKind.COMPUTATION
    id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    dataset_snapshot_id: str = Field(min_length=1)
    method_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    method_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    parameters: Mapping[str, Any] = Field(default_factory=dict)
    random_seed: int | None = None
    assumptions: Mapping[str, str] = Field(default_factory=dict)
    output_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact_ids: tuple[str, ...] = ()

    @field_validator("id", "run_id", "dataset_snapshot_id", "artifact_ids")
    @classmethod
    def reject_blank_identifiers(cls, value):
        values = value if isinstance(value, tuple) else (value,)
        if any(not item.strip() for item in values):
            raise ValueError("evidence identifiers must not be blank")
        return value

    @field_validator("parameters", "assumptions")
    @classmethod
    def freeze_mappings(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return MappingProxyType(dict(value))

    @field_serializer("parameters", "assumptions")
    def serialize_mappings(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)


class ClaimEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: Literal[EvidenceKind.CLAIM] = EvidenceKind.CLAIM
    id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    snippet: str | None = Field(default=None, max_length=1000)
    normalized_claim: str = Field(min_length=3, max_length=2000)
    verification_status: VerificationStatus
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("id", "source_id", "locator", "normalized_claim")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("claim evidence fields must not be blank")
        return value


class DerivedEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: Literal[EvidenceKind.DERIVED] = EvidenceKind.DERIVED
    id: str = Field(min_length=1)
    parent_evidence_ids: tuple[str, ...] = Field(min_length=1)
    transformation: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    transformation_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    output_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("id", "parent_evidence_ids")
    @classmethod
    def reject_blank_identifiers(cls, value):
        values = value if isinstance(value, tuple) else (value,)
        if any(not item.strip() for item in values):
            raise ValueError("derived evidence identifiers must not be blank")
        return value
```

Create `backend/app/platform/evidence/__init__.py`:

```python
from .contracts import (
    ClaimEvidence,
    ComputationEvidence,
    DerivedEvidence,
    EvidenceKind,
    VerificationStatus,
)

__all__ = [
    "ClaimEvidence",
    "ComputationEvidence",
    "DerivedEvidence",
    "EvidenceKind",
    "VerificationStatus",
]
```

- [ ] **Step 4: Run the evidence tests**

Run: `cd backend && PYTHONPATH=. pytest tests/platform/test_evidence_contracts.py -q`

Expected: `3 passed`.

- [ ] **Step 5: Commit evidence contracts**

```bash
git add backend/app/platform/evidence backend/tests/platform/test_evidence_contracts.py
git commit -m "feat(platform): add typed evidence contracts"
```

### Task 3: Artifact Revisions and Approval Decisions

**Files:**
- Create: `backend/app/platform/artifacts/contracts.py`
- Create: `backend/app/platform/artifacts/__init__.py`
- Create: `backend/app/platform/approvals/contracts.py`
- Create: `backend/app/platform/approvals/__init__.py`
- Create: `backend/tests/platform/test_artifact_approval_contracts.py`

**Interfaces:**
- Consumes: string evidence IDs and run IDs from prior contracts.
- Produces: `ArtifactRevision`, `create_artifact_revision`, `ApprovalStatus`, `ApprovalDecision`, `ApprovalRequest`, `InvalidApprovalDecision`, and `decide_approval`.

- [ ] **Step 1: Write failing artifact and approval tests**

```python
from datetime import datetime, timezone

import pytest

from app.platform.approvals import (
    ApprovalDecision, ApprovalRequest, ApprovalStatus,
    InvalidApprovalDecision, decide_approval,
)
from app.platform.artifacts import create_artifact_revision

NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def test_artifact_revision_is_append_only_and_links_lineage():
    first = create_artifact_revision(
        artifact_id="report-1", owner_id=7, studio_id="data-analyst",
        run_id="run-1", media_type="application/json", content_digest="a" * 64,
        created_at=NOW, evidence_ids=("ev-1",),
    )
    second = create_artifact_revision(
        artifact_id="report-1", owner_id=7, studio_id="data-analyst",
        run_id="run-2", media_type="application/json", content_digest="b" * 64,
        created_at=NOW, evidence_ids=("ev-2",), previous=first,
    )
    assert first.revision == 1
    assert second.revision == 2
    assert second.supersedes_revision_id == first.revision_id


def test_pending_approval_accepts_one_terminal_decision():
    pending = ApprovalRequest(
        id="approval-1", run_id="run-1", owner_id=7,
        decision_type="final-resume", proposed_changes=("draft-1",),
        evidence_ids=("claim-1",), created_at=NOW, updated_at=NOW,
    )
    approved = decide_approval(
        pending, ApprovalDecision.APPROVE, reviewer_id=7, now=NOW,
        comment="Ready to publish",
    )
    assert approved.status is ApprovalStatus.APPROVED
    with pytest.raises(InvalidApprovalDecision):
        decide_approval(approved, ApprovalDecision.REJECT, reviewer_id=7, now=NOW)


def test_revision_decision_requires_comment():
    pending = ApprovalRequest(
        id="approval-2", run_id="run-1", owner_id=7,
        decision_type="inferred-claims", proposed_changes=("claim-2",),
        evidence_ids=("source-1",), created_at=NOW, updated_at=NOW,
    )
    with pytest.raises(InvalidApprovalDecision):
        decide_approval(pending, ApprovalDecision.REVISE, reviewer_id=7, now=NOW)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && PYTHONPATH=. pytest tests/platform/test_artifact_approval_contracts.py -q`

Expected: collection errors for `app.platform.approvals` and `app.platform.artifacts`.

- [ ] **Step 3: Implement artifact revision contracts**

Create `backend/app/platform/artifacts/contracts.py`:

```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ArtifactRevision(BaseModel):
    model_config = ConfigDict(frozen=True)

    revision_id: str = Field(min_length=1)
    artifact_id: str = Field(min_length=1)
    revision: int = Field(gt=0)
    owner_id: int = Field(gt=0)
    studio_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    run_id: str = Field(min_length=1)
    media_type: str = Field(min_length=3)
    content_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_ids: tuple[str, ...] = ()
    supersedes_revision_id: str | None = None
    created_at: datetime

    @field_validator(
        "revision_id", "artifact_id", "run_id", "media_type",
        "supersedes_revision_id", "evidence_ids",
    )
    @classmethod
    def reject_blank_identifiers(cls, value):
        if value is None:
            return value
        values = value if isinstance(value, tuple) else (value,)
        if any(not item.strip() for item in values):
            raise ValueError("artifact identifiers must not be blank")
        return value

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("artifact timestamps must be timezone-aware")
        return value


def create_artifact_revision(
    *,
    artifact_id: str,
    owner_id: int,
    studio_id: str,
    run_id: str,
    media_type: str,
    content_digest: str,
    created_at: datetime,
    evidence_ids: tuple[str, ...] = (),
    previous: ArtifactRevision | None = None,
) -> ArtifactRevision:
    revision = 1
    supersedes = None
    if previous is not None:
        if previous.artifact_id != artifact_id:
            raise ValueError("artifact revision must retain its artifact_id")
        if previous.owner_id != owner_id or previous.studio_id != studio_id:
            raise ValueError("artifact revision must retain owner and studio")
        if previous.content_digest == content_digest:
            raise ValueError("a new artifact revision requires different content")
        revision = previous.revision + 1
        supersedes = previous.revision_id
    return ArtifactRevision(
        revision_id=f"{artifact_id}:r{revision}",
        artifact_id=artifact_id,
        revision=revision,
        owner_id=owner_id,
        studio_id=studio_id,
        run_id=run_id,
        media_type=media_type,
        content_digest=content_digest,
        evidence_ids=evidence_ids,
        supersedes_revision_id=supersedes,
        created_at=created_at,
    )
```

Create `backend/app/platform/artifacts/__init__.py`:

```python
from .contracts import ArtifactRevision, create_artifact_revision

__all__ = ["ArtifactRevision", "create_artifact_revision"]
```

- [ ] **Step 4: Implement approval contracts**

```python
from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    pass


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

    @field_validator("id", "run_id", "proposed_changes", "evidence_ids", "comment")
    @classmethod
    def reject_blank_values(cls, value):
        if value is None:
            return value
        values = value if isinstance(value, tuple) else (value,)
        if any(not item.strip() for item in values):
            raise ValueError("approval fields must not be blank")
        return value

    @field_validator("created_at", "updated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("approval timestamps must be timezone-aware")
        return value


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
    return ApprovalRequest.model_validate({
        **request.model_dump(),
        "status": status_by_decision[decision],
        "reviewer_id": reviewer_id,
        "comment": normalized_comment,
        "updated_at": now,
    })
```

Create `backend/app/platform/approvals/__init__.py`:

```python
from .contracts import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    InvalidApprovalDecision,
    decide_approval,
)

__all__ = [
    "ApprovalDecision",
    "ApprovalRequest",
    "ApprovalStatus",
    "InvalidApprovalDecision",
    "decide_approval",
]
```

- [ ] **Step 5: Run the artifact and approval tests**

Run: `cd backend && PYTHONPATH=. pytest tests/platform/test_artifact_approval_contracts.py -q`

Expected: `3 passed`.

- [ ] **Step 6: Commit artifact and approval contracts**

```bash
git add backend/app/platform/artifacts backend/app/platform/approvals backend/tests/platform/test_artifact_approval_contracts.py
git commit -m "feat(platform): add artifact and approval contracts"
```

### Task 4: Cross-Contract Specialist Examples

**Files:**
- Create: `backend/tests/platform/test_specialist_contract_integration.py`

**Interfaces:**
- Consumes: every public contract from Tasks 1–3 and existing `AIResult`, `EvidenceReference`, `QualityMetadata`.
- Produces: executable examples proving both studios can compose the shared contracts without importing one another.

- [ ] **Step 1: Write the integration examples**

```python
from datetime import datetime, timezone

from app.platform.approvals import ApprovalRequest
from app.platform.artifacts import create_artifact_revision
from app.platform.evidence import ClaimEvidence, ComputationEvidence, VerificationStatus
from app.platform.quality import AIResult, EvidenceReference, QualityMetadata
from app.platform.runtime import StudioRun, StudioRunState, transition_run

NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def quality(trace_id: str) -> QualityMetadata:
    return QualityMetadata(
        algorithm_versions={"contract-test": "1.0.0"}, model_versions={},
        prompt_versions={}, confidence_components={"evidence": 1.0},
        latency_ms=1.0, input_tokens=0, output_tokens=0,
        estimated_cost_usd=0.0, trace_id=trace_id,
    )


def test_data_analyst_result_resolves_to_computation():
    evidence = ComputationEvidence(
        id="ev-compute", run_id="run-analysis", dataset_snapshot_id="dataset-1",
        method_id="descriptive-summary", method_version="1.0.0",
        parameters={}, assumptions={}, output_digest="a" * 64,
    )
    result = AIResult[dict](
        output={"claim": "Revenue median is 42", "evidence_id": evidence.id},
        evidence=(EvidenceReference(source_id=evidence.id, locator="metrics.revenue.median"),),
        quality=quality("trace-analysis"),
    )
    assert result.output["evidence_id"] == result.evidence[0].source_id


def test_career_draft_waits_for_approval_of_inferred_claim():
    run = StudioRun(
        id="run-career", owner_id=7, studio_id="career", operation="draft",
        idempotency_key="career-1", input_fingerprint="b" * 64,
        created_at=NOW, updated_at=NOW,
    )
    waiting = transition_run(
        transition_run(run, StudioRunState.RUNNING, now=NOW),
        StudioRunState.AWAITING_INPUT, now=NOW, current_step="claim-review",
    )
    claim = ClaimEvidence(
        id="claim-1", source_id="resume-1", locator="page-1:lines-4-5",
        normalized_claim="Led a platform migration",
        verification_status=VerificationStatus.INFERRED, confidence=0.7,
    )
    approval = ApprovalRequest(
        id="approval-claim-1", run_id=waiting.id, owner_id=waiting.owner_id,
        decision_type="inferred-claims", proposed_changes=(claim.id,),
        evidence_ids=(claim.source_id,), created_at=NOW, updated_at=NOW,
    )
    assert waiting.state is StudioRunState.AWAITING_INPUT
    assert approval.proposed_changes == (claim.id,)
```

- [ ] **Step 2: Run all platform contract tests**

Run: `cd backend && PYTHONPATH=. pytest tests/platform -q`

Expected: `12 passed`.

- [ ] **Step 3: Run existing analysis contract tests for regression safety**

Run: `cd backend && PYTHONPATH=. pytest tests/analysis/test_base_agent.py tests/analysis/test_workflow_integration.py -q`

Expected: all selected tests pass.

- [ ] **Step 4: Commit the integration examples**

```bash
git add backend/tests/platform/test_specialist_contract_integration.py
git commit -m "test(platform): verify specialist contract composition"
```
