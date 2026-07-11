### Task 4: Common Evidence and Quality Result Contract

**Files:**

- Create: `backend/app/platform/quality/__init__.py`
- Create: `backend/app/platform/quality/contracts.py`
- Create: `backend/tests/platform/test_quality_contracts.py`

**Interfaces:**

- Produces: `EvidenceReference`, `ValidationIssue`, `ValidationStatus`, `QualityMetadata`, and generic `AIResult[T]`
- Critical validation errors require an abstention reason.
- Confidence components are named bounded values rather than one unexplained scalar.

- [ ] **Step 1: Write quality-contract tests**

```python
# backend/tests/platform/test_quality_contracts.py
import pytest
from pydantic import ValidationError

from app.platform.quality.contracts import (
    AIResult,
    EvidenceReference,
    QualityMetadata,
    ValidationIssue,
    ValidationStatus,
)


def metadata(**overrides):
    values = {
        "algorithm_versions": {"retrieval": "rrf-v1"},
        "model_versions": {"generator": "provider/model"},
        "prompt_versions": {"answer": "1.0.0"},
        "confidence_components": {"evidence_coverage": 0.92},
        "validations": [],
        "warnings": [],
        "abstention_reason": None,
        "latency_ms": 120.0,
        "input_tokens": 100,
        "output_tokens": 20,
        "estimated_cost_usd": 0.001,
        "trace_id": "trace-1",
        "evaluation_run_id": None,
    }
    values.update(overrides)
    return QualityMetadata(**values)


def test_result_serializes_evidence_and_quality_versions():
    result = AIResult[str](
        output="Supported answer",
        evidence=[EvidenceReference(source_id="doc-1", locator="page:2", snippet="Evidence")],
        quality=metadata(),
    )

    payload = result.model_dump(mode="json")
    assert payload["quality"]["algorithm_versions"]["retrieval"] == "rrf-v1"
    assert payload["evidence"][0]["source_id"] == "doc-1"


def test_critical_validation_requires_abstention():
    issue = ValidationIssue(
        code="unsupported-claim",
        message="The claim has no evidence.",
        status=ValidationStatus.ERROR,
        critical=True,
    )

    with pytest.raises(ValidationError, match="critical validation errors require abstention_reason"):
        metadata(validations=[issue])


def test_confidence_components_are_bounded():
    with pytest.raises(ValidationError):
        metadata(confidence_components={"evidence_coverage": 1.01})
```

- [ ] **Step 2: Run the tests and confirm the contract is missing**

Run: `cd backend && pytest tests/platform/test_quality_contracts.py -v`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'app.platform.quality'`.

- [ ] **Step 3: Implement the quality contracts**

```python
# backend/app/platform/quality/contracts.py
from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

OutputT = TypeVar("OutputT")


class ValidationStatus(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"


class EvidenceReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    snippet: str | None = Field(default=None, max_length=1000)
    relevance: float | None = Field(default=None, ge=0.0, le=1.0)


class ValidationIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    message: str = Field(min_length=3, max_length=500)
    status: ValidationStatus
    critical: bool = False


class QualityMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    algorithm_versions: dict[str, str] = Field(default_factory=dict)
    model_versions: dict[str, str] = Field(default_factory=dict)
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    confidence_components: dict[str, float] = Field(default_factory=dict)
    validations: tuple[ValidationIssue, ...] = ()
    warnings: tuple[str, ...] = ()
    abstention_reason: str | None = None
    latency_ms: float = Field(ge=0.0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)
    trace_id: str
    evaluation_run_id: str | None = None

    @model_validator(mode="after")
    def validate_quality_state(self) -> "QualityMetadata":
        invalid = [name for name, value in self.confidence_components.items() if not 0.0 <= value <= 1.0]
        if invalid:
            raise ValueError(f"confidence components must be between 0 and 1: {sorted(invalid)}")
        has_critical_error = any(
            issue.critical and issue.status == ValidationStatus.ERROR for issue in self.validations
        )
        if has_critical_error and not self.abstention_reason:
            raise ValueError("critical validation errors require abstention_reason")
        return self


class AIResult(BaseModel, Generic[OutputT]):
    output: OutputT | None
    evidence: tuple[EvidenceReference, ...] = ()
    quality: QualityMetadata
```

```python
# backend/app/platform/quality/__init__.py
from app.platform.quality.contracts import (
    AIResult,
    EvidenceReference,
    QualityMetadata,
    ValidationIssue,
    ValidationStatus,
)

__all__ = [
    "AIResult", "EvidenceReference", "QualityMetadata", "ValidationIssue", "ValidationStatus",
]
```

- [ ] **Step 4: Run the quality-contract tests**

Run: `cd backend && pytest tests/platform/test_quality_contracts.py -v`

Expected: 3 tests PASS.

- [ ] **Step 5: Commit the quality envelope**

```bash
git add backend/app/platform/quality backend/tests/platform/test_quality_contracts.py
git commit -m "feat(platform): add evidence and quality result contracts"
```

