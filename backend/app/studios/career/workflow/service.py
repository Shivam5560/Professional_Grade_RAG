from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.platform.approvals import ApprovalRequest, ApprovalStatus
from app.platform.evidence import VerificationStatus
from app.platform.quality import AIResult, EvidenceReference, QualityMetadata
from app.platform.runtime import (
    StudioRun,
    StudioRunState,
    transition_run,
)
from app.studios.career.domain.claims import CareerClaim
from app.studios.career.domain.drafts import ResumeDraft
from app.studios.career.domain.matching import (
    CandidateEdge,
    CareerMatchResult,
)
from app.studios.career.domain.provenance import safe_evidence_snippet
from app.studios.career.domain.requirements import RoleRequirement
from app.studios.career.matching import match_requirements
from app.studios.career.validation import validate_draft
from app.studios.career.writing import draft_from_matches


class CareerDeliverable(BaseModel):
    model_config = ConfigDict(frozen=True)

    match: CareerMatchResult
    draft: ResumeDraft
    selected_evidence: tuple[CareerClaim, ...]
    final_approval_id: str | None = None

    @model_validator(mode="after")
    def validate_lineage_and_publication(self) -> Self:
        if self.selected_evidence != self.match.selected_evidence:
            raise ValueError("deliverable evidence must match selected match evidence")
        if self.draft.publication_ready and self.final_approval_id is None:
            raise ValueError("publication-ready drafts require a final approval id")
        if not self.draft.publication_ready and self.final_approval_id is not None:
            raise ValueError("non-publication drafts cannot carry a final approval id")
        return self


class CareerSpecialistResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    run: StudioRun
    match: CareerMatchResult | None = None
    approval: ApprovalRequest | None = None
    result: AIResult[CareerDeliverable]

    @model_validator(mode="after")
    def validate_publication_approval(self) -> Self:
        deliverable = self.result.output
        if deliverable is None or not deliverable.draft.publication_ready:
            return self
        if (
            self.approval is None
            or self.approval.status is not ApprovalStatus.APPROVED
            or self.approval.decision_type != "final-resume"
            or deliverable.final_approval_id != self.approval.id
        ):
            raise ValueError(
                "publication-ready output requires its approved final-resume request"
            )
        return self


def _approval_id(
    *,
    run_id: str,
    decision_type: str,
    proposed_changes: tuple[str, ...],
    evidence_ids: tuple[str, ...],
) -> str:
    canonical = json.dumps(
        {
            "run_id": run_id,
            "decision_type": decision_type,
            "proposed_changes": proposed_changes,
            "evidence_ids": evidence_ids,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"approval-{digest}"


def _pending_approval(
    *,
    run: StudioRun,
    decision_type: str,
    proposed_changes: tuple[str, ...],
    evidence_ids: tuple[str, ...],
    now: datetime,
) -> ApprovalRequest:
    return ApprovalRequest(
        id=_approval_id(
            run_id=run.id,
            decision_type=decision_type,
            proposed_changes=proposed_changes,
            evidence_ids=evidence_ids,
        ),
        run_id=run.id,
        owner_id=run.owner_id,
        decision_type=decision_type,
        proposed_changes=proposed_changes,
        evidence_ids=evidence_ids,
        created_at=now,
        updated_at=now,
    )


def _inferred_result(
    claims: tuple[CareerClaim, ...],
    *,
    run_id: str,
) -> AIResult[CareerDeliverable]:
    return AIResult[CareerDeliverable](
        output=None,
        evidence=tuple(
            EvidenceReference(
                source_id=claim.id,
                locator=span.locator,
                snippet=safe_evidence_snippet(span.exact_text),
                relevance=1.0,
            )
            for claim in claims
            for span in claim.source_spans
        ),
        quality=QualityMetadata(
            algorithm_versions={"career-specialist": "1.0.0"},
            model_versions={},
            prompt_versions={},
            confidence_components={
                "claim-review": min(claim.confidence for claim in claims)
            },
            validations=(),
            warnings=("inferred claims require review before matching",),
            abstention_reason=None,
            latency_ms=0.0,
            input_tokens=0,
            output_tokens=0,
            estimated_cost_usd=0.0,
            trace_id=f"{run_id}:inferred-claim-review",
        ),
    )


def _deliverable_result(
    *,
    match: CareerMatchResult,
    draft: ResumeDraft,
    truth_result: AIResult[ResumeDraft],
    final_approval_id: str | None = None,
) -> AIResult[CareerDeliverable]:
    if truth_result.output is None:
        return AIResult[CareerDeliverable](
            output=None,
            evidence=truth_result.evidence,
            quality=truth_result.quality,
        )
    return AIResult[CareerDeliverable](
        output=CareerDeliverable(
            match=match,
            draft=draft,
            selected_evidence=match.selected_evidence,
            final_approval_id=final_approval_id,
        ),
        evidence=truth_result.evidence,
        quality=truth_result.quality,
    )


def _validate_final_approval(
    approval: ApprovalRequest,
    *,
    run: StudioRun,
    draft: ResumeDraft,
    evidence_ids: tuple[str, ...],
) -> None:
    expected_id = _approval_id(
        run_id=run.id,
        decision_type="final-resume",
        proposed_changes=(draft.id,),
        evidence_ids=evidence_ids,
    )
    matches = (
        approval.id == expected_id
        and approval.run_id == run.id
        and approval.owner_id == run.owner_id
        and approval.decision_type == "final-resume"
        and approval.proposed_changes == (draft.id,)
        and approval.evidence_ids == evidence_ids
        and approval.status is ApprovalStatus.APPROVED
    )
    if not matches:
        raise ValueError("final approval does not match run, draft, owner, and evidence")


class CareerSpecialist:
    """Pure deterministic Career Studio vertical slice; performs no I/O."""

    def run(
        self,
        run: StudioRun,
        *,
        claims: tuple[CareerClaim, ...],
        requirements: tuple[RoleRequirement, ...],
        candidate_edges: tuple[CandidateEdge, ...],
        now: datetime,
        approval: ApprovalRequest | None = None,
    ) -> CareerSpecialistResponse:
        if run.studio_id != "career":
            raise ValueError("CareerSpecialist requires a career studio run")
        resumed_from_approval = run.state is StudioRunState.AWAITING_INPUT
        if resumed_from_approval and approval is None:
            raise ValueError("an awaiting Career Studio run requires an approval")
        if run.state is StudioRunState.QUEUED:
            if approval is not None:
                raise ValueError("a queued Career Studio run cannot have an approval")
            working_run = transition_run(
                run,
                StudioRunState.RUNNING,
                now=now,
                current_step="evidence-matching",
                progress=0.1,
            )
        elif run.state is StudioRunState.RUNNING:
            if approval is not None:
                raise ValueError("a running Career Studio run cannot have an approval")
            working_run = run
        elif resumed_from_approval:
            working_run = transition_run(
                run,
                StudioRunState.RUNNING,
                now=now,
                current_step="evidence-matching",
                progress=0.5,
            )
        else:
            raise ValueError(f"CareerSpecialist cannot execute a {run.state} run")

        inferred_claims = tuple(
            sorted(
                (
                    claim
                    for claim in claims
                    if claim.verification_status is VerificationStatus.INFERRED
                ),
                key=lambda claim: claim.id,
            )
        )
        if inferred_claims:
            if approval is not None:
                raise ValueError(
                    "approved inferred claims must be resubmitted as verified claims"
                )
            inferred_ids = tuple(claim.id for claim in inferred_claims)
            request = _pending_approval(
                run=working_run,
                decision_type="inferred-claims",
                proposed_changes=inferred_ids,
                evidence_ids=inferred_ids,
                now=now,
            )
            waiting_run = transition_run(
                working_run,
                StudioRunState.AWAITING_INPUT,
                now=now,
                current_step="claim-review",
                progress=0.15,
            )
            return CareerSpecialistResponse(
                run=waiting_run,
                approval=request,
                result=_inferred_result(inferred_claims, run_id=run.id),
            )

        match = match_requirements(requirements, claims, candidate_edges)
        draft = draft_from_matches(match)
        is_approved_publication = approval is not None
        truth_result = validate_draft(
            draft,
            claims=claims,
            for_publication=is_approved_publication,
            trace_id=f"{run.id}:truth-guardian",
        )
        if truth_result.output is None:
            failed_run = transition_run(
                working_run,
                StudioRunState.FAILED,
                now=now,
                current_step="truth-validation",
                progress=0.8,
            )
            return CareerSpecialistResponse(
                run=failed_run,
                match=match,
                approval=None,
                result=_deliverable_result(
                    match=match,
                    draft=draft,
                    truth_result=truth_result,
                ),
            )

        evidence_ids = tuple(sorted(claim.id for claim in match.selected_evidence))
        if approval is None:
            request = _pending_approval(
                run=working_run,
                decision_type="final-resume",
                proposed_changes=(draft.id,),
                evidence_ids=evidence_ids,
                now=now,
            )
            waiting_run = transition_run(
                working_run,
                StudioRunState.AWAITING_INPUT,
                now=now,
                current_step="final-resume-approval",
                progress=0.9,
            )
            return CareerSpecialistResponse(
                run=waiting_run,
                match=match,
                approval=request,
                result=_deliverable_result(
                    match=match,
                    draft=draft,
                    truth_result=truth_result,
                ),
            )

        if not resumed_from_approval:
            raise ValueError("final publication approval requires an awaiting run")
        _validate_final_approval(
            approval,
            run=run,
            draft=draft,
            evidence_ids=evidence_ids,
        )
        publication_draft = draft.mark_publication_ready()
        succeeded_run = transition_run(
            working_run,
            StudioRunState.SUCCEEDED,
            now=now,
            current_step="complete",
        )
        return CareerSpecialistResponse(
            run=succeeded_run,
            match=match,
            approval=approval,
            result=_deliverable_result(
                match=match,
                draft=publication_draft,
                truth_result=truth_result,
                final_approval_id=approval.id,
            ),
        )
