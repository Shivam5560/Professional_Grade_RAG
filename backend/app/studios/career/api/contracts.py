from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import PurePath
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.platform.approvals import ApprovalDecision, ApprovalRequest
from app.platform.artifacts import ArtifactRevision
from app.platform.evidence import VerificationStatus
from app.platform.quality import QualityMetadata
from app.platform.runtime import StudioRun
from app.studios.career.domain import (
    CareerClaim,
    CareerMatchResult,
    ClaimContext,
    ClaimObject,
    ClaimPredicate,
    ClaimSubject,
    ResumeDraft,
    RoleRequirement,
    ScoreComponents,
    SourceSpan,
    TemporalScope,
)
from app.studios.career.persistence import (
    CareerClaimRevision,
    CareerDraft,
    CareerMatch,
    CareerRole,
    CareerSource,
)


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StructuredClaimInput(StrictRequest):
    subject: ClaimSubject
    predicate: ClaimPredicate
    object: ClaimObject
    source_spans: tuple[SourceSpan, ...] = Field(min_length=1)
    temporal_scope: TemporalScope
    verification_status: VerificationStatus = VerificationStatus.INFERRED
    confidence: float = Field(ge=0.0, le=1.0)
    verifier_id: str = Field(min_length=1, max_length=200)
    context: ClaimContext = Field(default_factory=ClaimContext)
    related_claim_ids: tuple[str, ...] = ()

    def to_claim(self) -> CareerClaim:
        return CareerClaim.create(
            subject=self.subject,
            predicate=self.predicate,
            object=self.object,
            source_spans=self.source_spans,
            temporal_scope=self.temporal_scope,
            verification_status=self.verification_status,
            confidence=self.confidence,
            verifier_id=self.verifier_id,
            context=self.context,
            related_claim_ids=self.related_claim_ids,
        )


class SourceIngestionRequest(StrictRequest):
    filename: str = Field(min_length=1, max_length=255)
    media_type: Literal["application/json", "text/plain"]
    ingestion_mode: Literal["structured", "free-form"]
    claims: tuple[StructuredClaimInput, ...] = Field(default=(), max_length=200)
    raw_text: str | None = Field(default=None, max_length=100_000)

    @field_validator("filename")
    @classmethod
    def require_plain_filename(cls, value: str) -> str:
        if value != PurePath(value).name or "/" in value or "\\" in value or ".." in value:
            raise ValueError("filename must not be a filesystem path")
        return value

    @model_validator(mode="after")
    def validate_mode(self) -> Self:
        if self.ingestion_mode == "structured":
            if self.media_type != "application/json" or not self.claims or self.raw_text is not None:
                raise ValueError("structured ingestion requires JSON claims only")
        elif self.media_type != "text/plain" or not (self.raw_text or "").strip() or self.claims:
            raise ValueError("free-form ingestion requires bounded text only")
        return self

    def require_structured_claims(self) -> tuple[CareerClaim, ...]:
        if self.ingestion_mode != "structured":
            from .service import UnsupportedCareerCapability

            raise UnsupportedCareerCapability("free-form-extraction is not available in the deterministic runtime")
        return tuple(item.to_claim() for item in self.claims)


class SourceIngestionResponse(BaseModel):
    source: CareerSource
    claims: tuple[CareerClaimRevision, ...]


class ClaimDecisionAction(StrEnum):
    VERIFY = "verify"
    REJECT = "reject"
    REVISE = "revise"


class ClaimDecisionRequest(StrictRequest):
    action: ClaimDecisionAction
    replacement: StructuredClaimInput | None = None

    @model_validator(mode="after")
    def validate_replacement(self) -> Self:
        if (self.action is ClaimDecisionAction.REVISE) != (self.replacement is not None):
            raise ValueError("only revise decisions require replacement claim content")
        return self


class RoleCreateRequest(StrictRequest):
    role_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=500)
    requirements: tuple[RoleRequirement, ...] = Field(min_length=1, max_length=200)


class JobDescriptionParseRequest(StrictRequest):
    job_description: str = Field(min_length=10, max_length=30_000)


class ParsedRoleResponse(BaseModel):
    title: str
    requirements: tuple[RoleRequirement, ...]


class CareerScoreRequest(StrictRequest):
    resume_id: str = Field(min_length=1, max_length=200)
    job_description: str = Field(min_length=10, max_length=30_000)


class CareerScoreResponse(BaseModel):
    analysis_id: str
    resume_id: str
    overall_score: float | None = None
    analysis: dict[str, Any]
    refined_recommendations: list[str] | dict[str, str] | None = None
    refined_justifications: list[str] | dict[str, str] | None = None
    resume_data: dict[str, Any] | None = None
    created_at: str = ""


class TailoringPrepareRequest(StrictRequest):
    source_id: str = Field(min_length=1, max_length=200)
    job_description: str = Field(min_length=10, max_length=30_000)


class CandidateEdgeInput(StrictRequest):
    requirement_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    components: ScoreComponents


class MatchCreateRequest(StrictRequest):
    match_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    role_id: str = Field(min_length=1)
    candidate_edges: tuple[CandidateEdgeInput, ...] = Field(max_length=5000)


class DraftCreateRequest(StrictRequest):
    match_id: str = Field(min_length=1)


class ApprovalDecisionRequest(StrictRequest):
    decision: ApprovalDecision
    comment: str | None = Field(default=None, max_length=2000)


class DraftRefinementRequest(StrictRequest):
    comment: str = Field(min_length=1, max_length=2000)


class DraftWorkflowResponse(BaseModel):
    run: StudioRun
    match: CareerMatchResult
    draft: ResumeDraft
    approval: ApprovalRequest
    quality: QualityMetadata


class DraftRefinementResponse(DraftWorkflowResponse):
    supersedes_run_id: str
    refinement_note: str


class PublicationResponse(BaseModel):
    run: StudioRun
    draft: ResumeDraft
    approval: ApprovalRequest
    artifact: ArtifactRevision
    artifact_content: dict[str, Any]


class CapabilityErrorResponse(BaseModel):
    code: Literal["unsupported-capability"] = "unsupported-capability"
    capability: str
    message: str
