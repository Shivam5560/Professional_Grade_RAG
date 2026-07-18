from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.platform.approvals import ApprovalDecision, ApprovalStatus
from app.platform.artifacts import ArtifactRevision, create_artifact_revision
from app.platform.evidence import ClaimEvidence
from app.platform.persistence import (
    StudioApprovalRepository,
    StudioArtifactRepository,
    StudioEvidenceRepository,
    StudioQualityRepository,
    StudioRunRepository,
)
from app.platform.runtime import StudioRun, StudioRunState
from app.studios.career import (
    CandidateEdge,
    CareerSpecialist,
    DraftTransformation,
    REGISTERED_PUBLICATION_TRANSFORMATIONS,
    match_requirements,
    score_candidate_edge,
    ScoreComponents,
    validate_draft,
)
from app.studios.career.api.contracts import (
    ClaimDecisionRequest,
    DraftCreateRequest,
    DraftRefinementResponse,
    DraftWorkflowResponse,
    MatchCreateRequest,
    PublicationResponse,
    RoleCreateRequest,
    SourceIngestionRequest,
    SourceIngestionResponse,
    CandidateEdgeInput,
)
from app.platform.evidence import VerificationStatus
from app.studios.career.domain import RoleRequirement
from app.studios.career.persistence import CareerDraft, CareerMatch, CareerRepository, CareerRole


class UnsupportedCareerCapability(ValueError):
    """A capability was deliberately omitted instead of being simulated."""


_CAREER_STOP_WORDS = {"and", "the", "with", "for", "from", "that", "this", "role", "work", "need", "requiring"}


def _career_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9+#.]+", value.lower())
        if len(token) > 2 and token not in _CAREER_STOP_WORDS
    }


def _digest(value: object) -> str:
    canonical = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class CareerApplicationService:
    def __init__(self, session: Session, *, owner_id: int) -> None:
        self.session = session
        self.owner_id = owner_id
        self.career = CareerRepository(session)
        self.runs = StudioRunRepository(session)
        self.evidence = StudioEvidenceRepository(session)
        self.approvals = StudioApprovalRepository(session)
        self.artifacts = StudioArtifactRepository(session)
        self.quality = StudioQualityRepository(session)

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)

    def ingest_source(self, request: SourceIngestionRequest) -> SourceIngestionResponse:
        claims = request.require_structured_claims()
        return self.ingest_claims(filename=request.filename, media_type=request.media_type, claims=claims)

    def ingest_claims(self, *, filename: str, media_type: str, claims) -> SourceIngestionResponse:
        source_ids = {span.source_id for claim in claims for span in claim.source_spans}
        if len(source_ids) != 1:
            raise ValueError("structured claims must resolve to exactly one source id")
        source_id = next(iter(source_ids))
        payload = [claim.model_dump(mode="json") for claim in claims]
        now = self.now()
        source = self.career.add_source(
            source_id=source_id,
            owner_id=self.owner_id,
            filename=filename,
            media_type=media_type,
            content_digest=_digest(payload),
            created_at=now,
        )
        revisions = tuple(
            self.career.add_claim(claim, owner_id=self.owner_id, created_at=now)
            for claim in claims
        )
        return SourceIngestionResponse(source=source, claims=revisions)

    def review_claim(self, logical_claim_id: str, request: ClaimDecisionRequest):
        replacement = request.replacement.to_claim() if request.replacement else None
        return self.career.review_claim(
            logical_claim_id,
            action=request.action.value,
            owner_id=self.owner_id,
            reviewer_id=self.owner_id,
            now=self.now(),
            replacement=replacement,
        )

    def create_role(self, request: RoleCreateRequest) -> CareerRole:
        return self.career.add_role(
            role_id=request.role_id,
            title=request.title,
            requirements=request.requirements,
            owner_id=self.owner_id,
            created_at=self.now(),
        )

    def create_match(self, request: MatchCreateRequest) -> CareerMatch:
        role = self.career.get_role(request.role_id, owner_id=self.owner_id)
        claims_by_id = {
            item.claim.id: item.claim
            for item in self.career.list_current_claims(owner_id=self.owner_id)
        }
        edges: list[CandidateEdge] = []
        for edge_input in request.candidate_edges:
            requirement = next(
                (item for item in role.requirements if item.id == edge_input.requirement_id),
                None,
            )
            claim = claims_by_id.get(edge_input.claim_id)
            if requirement is None or claim is None:
                raise ValueError("candidate edge references unknown owned evidence")
            edges.append(score_candidate_edge(requirement, claim, edge_input.components))
        result = match_requirements(
            role.requirements,
            tuple(claims_by_id.values()),
            tuple(edges),
        )
        return self.career.add_match(
            match_id=request.match_id,
            role_id=request.role_id,
            result=result,
            owner_id=self.owner_id,
            created_at=self.now(),
        )

    def prepare_tailoring(
        self,
        *,
        source_id: str,
        title: str,
        requirements: tuple[RoleRequirement, ...],
    ) -> DraftWorkflowResponse:
        revisions = self.career.list_current_claims(owner_id=self.owner_id, source_id=source_id)
        verified = tuple(
            revision.claim
            for revision in revisions
            if revision.claim.verification_status is VerificationStatus.VERIFIED
        )
        if not verified:
            raise ValueError("Review and verify at least one extracted evidence claim before tailoring")

        suffix = uuid.uuid4().hex
        role = self.create_role(RoleCreateRequest(role_id=f"career-role-{suffix}", title=title, requirements=requirements))
        edges: list[CandidateEdgeInput] = []
        for requirement in role.requirements:
            requirement_tokens = _career_tokens(requirement.description)
            for claim in verified:
                claim_text = " ".join(
                    [claim.subject.label, str(claim.object.value), *(span.exact_text for span in claim.source_spans)]
                )
                claim_tokens = _career_tokens(claim_text)
                overlap = len(requirement_tokens & claim_tokens) / max(1, len(requirement_tokens))
                if overlap <= 0:
                    continue
                components = ScoreComponents(
                    semantic_relevance=min(1.0, overlap),
                    evidence_strength=max(0.9, claim.confidence),
                    recency=0.5,
                    duration_seniority=0.5,
                    transferability=min(1.0, overlap),
                    specificity=0.8,
                )
                edges.append(CandidateEdgeInput(requirement_id=requirement.id, claim_id=claim.id, components=components))

        match = self.create_match(MatchCreateRequest(match_id=f"career-match-{suffix}", role_id=role.id, candidate_edges=tuple(edges)))
        if not match.result.selected_matches:
            raise ValueError("No verified evidence matches the target role; review the job description or evidence")
        return self.create_draft(
            DraftCreateRequest(match_id=match.id),
            idempotency_key=f"tailoring-{suffix}",
        )

    def create_draft(self, request: DraftCreateRequest, *, idempotency_key: str, refinement_note: str | None = None) -> DraftWorkflowResponse:
        match = self.career.get_match(request.match_id, owner_id=self.owner_id)
        role = self.career.get_role(match.role_id, owner_id=self.owner_id)
        now = self.now()
        fingerprint = _digest({"match_id": request.match_id, "result": match.result.model_dump(mode="json"), "refinement_note": refinement_note})
        run_id = f"career-run-{_digest([self.owner_id, idempotency_key, fingerprint])[:24]}"
        run = self.runs.create(
            StudioRun(
                id=run_id,
                owner_id=self.owner_id,
                studio_id="career",
                operation="draft",
                idempotency_key=idempotency_key,
                input_fingerprint=fingerprint,
                created_at=now,
                updated_at=now,
            ),
            owner_id=self.owner_id,
        )
        if run.state is not StudioRunState.QUEUED:
            draft = self._draft_for_run(run.id)
            approval = self.approvals.get(draft.approval_id or "", owner_id=self.owner_id)
            return DraftWorkflowResponse(
                run=run,
                match=match.result,
                draft=draft.draft,
                approval=approval,
                quality=self.quality.get(
                    f"{run.id}:quality", owner_id=self.owner_id
                ),
            )

        edges = self._edges_from_match(match)
        requirements = role.requirements
        if refinement_note:
            note_tokens = _career_tokens(refinement_note)
            requirements = tuple(sorted(requirements, key=lambda item: (-len(_career_tokens(item.description) & note_tokens), item.id)))
        response = CareerSpecialist().run(
            run,
            claims=match.result.selected_evidence,
            requirements=requirements,
            candidate_edges=edges,
            now=now,
        )
        if response.result.output is None or response.approval is None or response.match is None:
            raise ValueError("career specialist abstained before producing a draft")
        self.runs.transition(run.id, StudioRunState.RUNNING, owner_id=self.owner_id, now=now, current_step="evidence-matching", progress=0.1)
        persisted_run = self.runs.transition(run.id, StudioRunState.AWAITING_INPUT, owner_id=self.owner_id, now=now, current_step=response.run.current_step, progress=response.run.progress)
        persisted_evidence_ids: list[str] = []
        for claim in response.match.selected_evidence:
            span = claim.source_spans[0]
            evidence_id = f"{run.id}:{claim.id}"[:255]
            self.evidence.add(
                run.id,
                ClaimEvidence(
                    id=evidence_id,
                    source_id=span.source_id,
                    locator=span.locator,
                    snippet=span.exact_text[:1000],
                    normalized_claim=span.exact_text,
                    verification_status=claim.verification_status,
                    confidence=claim.confidence,
                ),
                owner_id=self.owner_id,
                created_at=now,
            )
            persisted_evidence_ids.append(evidence_id)
        approval_request = response.approval.model_copy(update={"evidence_ids": tuple(sorted(persisted_evidence_ids))})
        approval = self.approvals.add(approval_request, owner_id=self.owner_id)
        saved = self.career.add_draft(
            run_id=run.id,
            match_id=match.id,
            draft=response.result.output.draft,
            owner_id=self.owner_id,
            created_at=now,
            truth_valid=True,
            approval_id=approval.id,
        )
        self.quality.add(
            f"{run.id}:quality",
            run.id,
            response.result.quality,
            owner_id=self.owner_id,
            created_at=now,
        )
        return DraftWorkflowResponse(run=persisted_run, match=response.match, draft=saved.draft, approval=approval, quality=response.result.quality)

    def decide_approval(self, approval_id: str, decision: ApprovalDecision, *, comment: str | None):
        return self.approvals.decide(approval_id, decision, owner_id=self.owner_id, now=self.now(), comment=comment)

    def refine_draft(self, draft_id: str, *, comment: str) -> DraftRefinementResponse:
        note = comment.strip()
        if not note:
            raise ValueError("refinement comment is required")
        previous = self.career.get_draft(draft_id, owner_id=self.owner_id)
        if not previous.approval_id:
            raise ValueError("draft has no bound approval")
        approval = self.approvals.get(previous.approval_id, owner_id=self.owner_id)
        if approval.status is not ApprovalStatus.REVISION_REQUESTED:
            raise ValueError("request changes on the current draft before refining")
        response = self.create_draft(
            DraftCreateRequest(match_id=previous.match_id),
            idempotency_key=f"refine-{previous.run_id}-{_digest(note)[:16]}",
            refinement_note=note,
        )
        return DraftRefinementResponse(
            **response.model_dump(),
            supersedes_run_id=previous.run_id,
            refinement_note=note,
        )

    def publish(self, draft_id: str) -> PublicationResponse:
        saved = self.career.get_draft(draft_id, owner_id=self.owner_id)
        if not saved.approval_id:
            raise ValueError("draft has no bound approval")
        approval = self.approvals.get(saved.approval_id, owner_id=self.owner_id)
        if approval.status is not ApprovalStatus.APPROVED:
            raise ValueError("draft approval is not approved")
        if not saved.truth_valid:
            raise ValueError("draft is not truth-valid")
        if any(
            bullet.transformation not in REGISTERED_PUBLICATION_TRANSFORMATIONS
            for bullet in saved.draft.bullets
        ):
            raise ValueError("draft uses an unregistered publication transformation")
        match = self.career.get_match(saved.match_id, owner_id=self.owner_id)
        run = self.runs.get(saved.run_id, owner_id=self.owner_id)
        now = self.now()
        persisted_evidence_ids = tuple(item.id for item in self.evidence.list_for_run(run.id, owner_id=self.owner_id))
        if approval.run_id != run.id or approval.proposed_changes != (saved.draft.id,) or approval.evidence_ids != persisted_evidence_ids:
            raise ValueError("draft approval does not match the current revision")
        truth_result = validate_draft(
            saved.draft,
            claims=match.result.selected_evidence,
            for_publication=True,
            trace_id=f"{run.id}:truth-guardian-publication",
        )
        if truth_result.output is None:
            raise ValueError("truth guardian rejected publication")
        publication_draft = truth_result.output.mark_publication_ready()
        self.runs.transition(run.id, StudioRunState.RUNNING, owner_id=self.owner_id, now=now, current_step="truth-validation")
        succeeded = self.runs.transition(run.id, StudioRunState.SUCCEEDED, owner_id=self.owner_id, now=now, current_step="complete")
        published = self.career.mark_published(draft_id, owner_id=self.owner_id, now=now)
        content = publication_draft.model_dump(mode="json")
        artifact = create_artifact_revision(
            artifact_id=f"career-{draft_id}",
            owner_id=self.owner_id,
            studio_id="career",
            run_id=run.id,
            media_type="application/vnd.nexus.resume+json",
            content_digest=_digest(content),
            created_at=now,
            evidence_ids=tuple(sorted(claim.id for claim in match.result.selected_evidence)),
        )
        artifact = self.artifacts.create(artifact, owner_id=self.owner_id, expected_parent_revision_id=None)
        return PublicationResponse(run=succeeded, draft=publication_draft, approval=approval, artifact=artifact, artifact_content=content)

    def get_artifact(self, revision_id: str) -> ArtifactRevision:
        return self.artifacts.get_revision(revision_id, owner_id=self.owner_id)

    def _draft_for_run(self, run_id: str) -> CareerDraft:
        from app.studios.career.persistence.models import CareerDraftRecord
        from sqlalchemy import select

        record = self.session.execute(select(CareerDraftRecord.draft_id).where(CareerDraftRecord.run_id == run_id, CareerDraftRecord.owner_id == self.owner_id)).scalar_one()
        return self.career.get_draft(record, owner_id=self.owner_id)

    @staticmethod
    def _edges_from_match(match: CareerMatch) -> tuple[CandidateEdge, ...]:
        return tuple(
            CandidateEdge(
                requirement_id=item.requirement_id,
                claim_id=item.claim_id,
                components=item.components,
                score=item.score,
                strength=item.strength,
            )
            for item in match.result.selected_matches
        )
