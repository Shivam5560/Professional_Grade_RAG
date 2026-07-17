from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.platform.evidence import VerificationStatus
from app.platform.persistence import RecordAlreadyExists, RecordNotFound
from app.platform.persistence.repositories import StudioRunRepository
from app.studios.career.domain import CareerClaim, CareerMatchResult, ResumeDraft, RoleRequirement
from app.studios.career.persistence.models import (
    CareerClaimRevisionRecord,
    CareerDraftClaimRecord,
    CareerDraftRecord,
    CareerMatchRecord,
    CareerRequirementMatchRecord,
    CareerRequirementRecord,
    CareerRoleRecord,
    CareerSourceRecord,
)


class InvalidCareerState(ValueError):
    """Raised when persisted career evidence is not eligible for the requested action."""


class CareerSource(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    owner_id: int
    filename: str
    media_type: str
    content_digest: str
    created_at: datetime


class CareerClaimRevision(BaseModel):
    model_config = ConfigDict(frozen=True)
    revision_id: str
    logical_claim_id: str
    revision: int
    source_id: str
    claim: CareerClaim
    supersedes_revision_id: str | None = None
    reviewer_id: int | None = None
    created_at: datetime


class CareerRole(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    title: str
    requirements: tuple[RoleRequirement, ...]
    created_at: datetime


class CareerMatch(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    role_id: str
    result: CareerMatchResult
    created_at: datetime


class CareerDraft(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    run_id: str
    match_id: str
    draft: ResumeDraft
    truth_valid: bool
    approval_id: str | None = None
    published_at: datetime | None = None
    created_at: datetime


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class CareerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_source(self, *, source_id: str, owner_id: int, filename: str, media_type: str, content_digest: str, created_at: datetime) -> CareerSource:
        if owner_id <= 0 or not filename.strip() or len(content_digest) != 64:
            raise ValueError("invalid career source")
        record = CareerSourceRecord(id=source_id, owner_id=owner_id, filename=filename, media_type=media_type, content_digest=content_digest, created_at=created_at)
        self._add(record, "career source already exists")
        return self.get_source(source_id, owner_id=owner_id)

    def get_source(self, source_id: str, *, owner_id: int) -> CareerSource:
        record = self.session.execute(select(CareerSourceRecord).where(CareerSourceRecord.id == source_id, CareerSourceRecord.owner_id == owner_id)).scalar_one_or_none()
        if record is None:
            raise RecordNotFound("career source not found")
        return CareerSource(id=record.id, owner_id=record.owner_id, filename=record.filename, media_type=record.media_type, content_digest=record.content_digest, created_at=_aware(record.created_at))

    def add_claim(self, claim: CareerClaim, *, owner_id: int, created_at: datetime) -> CareerClaimRevision:
        source_ids = {span.source_id for span in claim.source_spans}
        if len(source_ids) != 1:
            raise ValueError("a persisted claim must resolve to exactly one source")
        source_id = next(iter(source_ids))
        self.get_source(source_id, owner_id=owner_id)
        return self._append_claim(claim=claim, logical_claim_id=claim.id, revision=1, source_id=source_id, owner_id=owner_id, created_at=created_at, supersedes_revision_id=None, reviewer_id=None)

    def get_claim(self, logical_claim_id: str, *, owner_id: int) -> CareerClaimRevision:
        record = self.session.execute(select(CareerClaimRevisionRecord).where(CareerClaimRevisionRecord.logical_claim_id == logical_claim_id, CareerClaimRevisionRecord.owner_id == owner_id, CareerClaimRevisionRecord.is_current.is_(True))).scalar_one_or_none()
        if record is None:
            raise RecordNotFound("career claim not found")
        return self._claim_from_record(record)

    def get_claim_by_content_id(self, claim_id: str, *, owner_id: int) -> CareerClaimRevision:
        record = self.session.execute(select(CareerClaimRevisionRecord).where(CareerClaimRevisionRecord.claim_id == claim_id, CareerClaimRevisionRecord.owner_id == owner_id, CareerClaimRevisionRecord.is_current.is_(True))).scalar_one_or_none()
        if record is None:
            raise RecordNotFound("career claim not found")
        return self._claim_from_record(record)

    def list_current_claims(self, *, owner_id: int, source_id: str | None = None) -> tuple[CareerClaimRevision, ...]:
        query = select(CareerClaimRevisionRecord).where(CareerClaimRevisionRecord.owner_id == owner_id, CareerClaimRevisionRecord.is_current.is_(True))
        if source_id is not None:
            self.get_source(source_id, owner_id=owner_id)
            query = query.where(CareerClaimRevisionRecord.source_id == source_id)
        records = self.session.execute(query.order_by(CareerClaimRevisionRecord.logical_claim_id)).scalars()
        return tuple(self._claim_from_record(record) for record in records)

    def review_claim(self, logical_claim_id: str, *, action: Literal["verify", "reject", "revise"], owner_id: int, reviewer_id: int, now: datetime, replacement: CareerClaim | None = None) -> CareerClaimRevision:
        if reviewer_id != owner_id:
            raise RecordNotFound("career claim not found")
        current = self.get_claim(logical_claim_id, owner_id=owner_id)
        if action == "revise":
            if replacement is None:
                raise ValueError("claim revision requires replacement content")
            if replacement.verification_status is not VerificationStatus.VERIFIED:
                raise ValueError("replacement claim must be verified")
            next_claim = replacement.model_copy(update={"verifier_id": str(reviewer_id)})
        else:
            if replacement is not None:
                raise ValueError("replacement is only valid for revise")
            status = VerificationStatus.VERIFIED if action == "verify" else VerificationStatus.REJECTED
            next_claim = current.claim.model_copy(update={"verification_status": status, "confidence": max(current.claim.confidence, 0.9) if status is VerificationStatus.VERIFIED else 0.0, "verifier_id": str(reviewer_id)})
        source_ids = {span.source_id for span in next_claim.source_spans}
        if source_ids != {current.source_id}:
            raise ValueError("claim revisions cannot move between sources")
        current_record = self.session.get(CareerClaimRevisionRecord, current.revision_id)
        assert current_record is not None
        current_record.is_current = False
        return self._append_claim(claim=next_claim, logical_claim_id=current.logical_claim_id, revision=current.revision + 1, source_id=current.source_id, owner_id=owner_id, created_at=now, supersedes_revision_id=current.revision_id, reviewer_id=reviewer_id)

    def add_role(self, *, role_id: str, title: str, requirements: tuple[RoleRequirement, ...], owner_id: int, created_at: datetime) -> CareerRole:
        if not requirements:
            raise ValueError("career role requires typed requirements")
        role = CareerRoleRecord(id=role_id, owner_id=owner_id, title=title, created_at=created_at)
        self._add(role, "career role already exists")
        for requirement in requirements:
            record_id = f"{role_id}:{requirement.id}"
            span = requirement.source_span
            self._add(CareerRequirementRecord(record_id=record_id, owner_id=owner_id, role_id=role_id, requirement_id=requirement.id, source_id=span.source_id, locator=span.locator, exact_text=span.exact_text, payload=requirement.model_dump(mode="json"), created_at=created_at), "career requirement already exists")
        return self.get_role(role_id, owner_id=owner_id)

    def get_role(self, role_id: str, *, owner_id: int) -> CareerRole:
        role = self.session.execute(select(CareerRoleRecord).where(CareerRoleRecord.id == role_id, CareerRoleRecord.owner_id == owner_id)).scalar_one_or_none()
        if role is None:
            raise RecordNotFound("career role not found")
        requirements = self.session.execute(select(CareerRequirementRecord).where(CareerRequirementRecord.role_id == role_id, CareerRequirementRecord.owner_id == owner_id).order_by(CareerRequirementRecord.requirement_id)).scalars()
        return CareerRole(id=role.id, title=role.title, requirements=tuple(RoleRequirement.model_validate(item.payload) for item in requirements), created_at=_aware(role.created_at))

    def add_match(self, *, match_id: str, role_id: str, result: CareerMatchResult, owner_id: int, created_at: datetime) -> CareerMatch:
        role = self.get_role(role_id, owner_id=owner_id)
        requirements = {requirement.id for requirement in role.requirements}
        if any(item.requirement_id not in requirements for item in result.selected_matches):
            raise ValueError("match references a requirement outside its role")
        record = CareerMatchRecord(id=match_id, owner_id=owner_id, role_id=role_id, payload=result.model_dump(mode="json"), created_at=created_at)
        self._add(record, "career match already exists")
        for selected in result.selected_matches:
            claim_revision = self.get_claim_by_content_id(selected.claim_id, owner_id=owner_id)
            requirement_record_id = f"{role_id}:{selected.requirement_id}"
            relation_id = f"{match_id}:{requirement_record_id}:{claim_revision.revision_id}"
            self._add(CareerRequirementMatchRecord(id=relation_id, owner_id=owner_id, match_id=match_id, requirement_record_id=requirement_record_id, claim_revision_id=claim_revision.revision_id, score=format(selected.score, ".17g")), "career match relation already exists")
        return self.get_match(match_id, owner_id=owner_id)

    def get_match(self, match_id: str, *, owner_id: int) -> CareerMatch:
        record = self.session.execute(select(CareerMatchRecord).where(CareerMatchRecord.id == match_id, CareerMatchRecord.owner_id == owner_id)).scalar_one_or_none()
        if record is None:
            raise RecordNotFound("career match not found")
        return CareerMatch(id=record.id, role_id=record.role_id, result=CareerMatchResult.model_validate(record.payload), created_at=_aware(record.created_at))

    def add_draft(self, *, run_id: str, match_id: str, draft: ResumeDraft, owner_id: int, created_at: datetime, truth_valid: bool = True, approval_id: str | None = None) -> CareerDraft:
        StudioRunRepository(self.session).get(run_id, owner_id=owner_id)
        self.get_match(match_id, owner_id=owner_id)
        resolved: dict[str, CareerClaimRevision] = {}
        for bullet in draft.bullets:
            for claim_id in bullet.source_claim_ids:
                revision = self.get_claim_by_content_id(claim_id, owner_id=owner_id)
                if revision.claim.verification_status is not VerificationStatus.VERIFIED:
                    raise InvalidCareerState("drafts require verified current claims")
                resolved[claim_id] = revision
        record_id = f"{run_id}:{draft.id}"
        self._add(CareerDraftRecord(record_id=record_id, draft_id=draft.id, owner_id=owner_id, run_id=run_id, match_id=match_id, payload=draft.model_dump(mode="json"), truth_valid=truth_valid, approval_id=approval_id, created_at=created_at), "career draft already exists")
        for bullet_index, bullet in enumerate(draft.bullets):
            for claim_id in bullet.source_claim_ids:
                revision = resolved[claim_id]
                relation_id = f"{record_id}:{bullet_index}:{revision.revision_id}"
                self._add(CareerDraftClaimRecord(id=relation_id, owner_id=owner_id, draft_record_id=record_id, bullet_index=bullet_index, claim_revision_id=revision.revision_id, transformation=bullet.transformation.value), "career draft claim already exists")
        return self.get_draft(draft.id, owner_id=owner_id)

    def get_draft(self, draft_id: str, *, owner_id: int) -> CareerDraft:
        record = self.session.execute(select(CareerDraftRecord).where(CareerDraftRecord.draft_id == draft_id, CareerDraftRecord.owner_id == owner_id).order_by(CareerDraftRecord.created_at.desc())).scalars().first()
        if record is None:
            raise RecordNotFound("career draft not found")
        return CareerDraft(id=record.draft_id, run_id=record.run_id, match_id=record.match_id, draft=ResumeDraft.model_validate(record.payload), truth_valid=record.truth_valid, approval_id=record.approval_id, published_at=_aware(record.published_at) if record.published_at else None, created_at=_aware(record.created_at))

    def bind_approval(self, draft_id: str, approval_id: str, *, owner_id: int) -> CareerDraft:
        record = self._draft_record(draft_id, owner_id=owner_id)
        record.approval_id = approval_id
        self.session.flush()
        return self.get_draft(draft_id, owner_id=owner_id)

    def mark_published(self, draft_id: str, *, owner_id: int, now: datetime) -> CareerDraft:
        record = self._draft_record(draft_id, owner_id=owner_id)
        record.published_at = now
        self.session.flush()
        return self.get_draft(draft_id, owner_id=owner_id)

    def _draft_record(self, draft_id: str, *, owner_id: int) -> CareerDraftRecord:
        record = self.session.execute(select(CareerDraftRecord).where(CareerDraftRecord.draft_id == draft_id, CareerDraftRecord.owner_id == owner_id)).scalar_one_or_none()
        if record is None:
            raise RecordNotFound("career draft not found")
        return record

    def _append_claim(self, *, claim: CareerClaim, logical_claim_id: str, revision: int, source_id: str, owner_id: int, created_at: datetime, supersedes_revision_id: str | None, reviewer_id: int | None) -> CareerClaimRevision:
        revision_id = f"{logical_claim_id}:r{revision}"
        record = CareerClaimRevisionRecord(revision_id=revision_id, logical_claim_id=logical_claim_id, claim_id=claim.id, revision=revision, owner_id=owner_id, source_id=source_id, supersedes_revision_id=supersedes_revision_id, is_current=True, status=claim.verification_status.value, verifier_id=claim.verifier_id, reviewer_id=reviewer_id, payload=claim.model_dump(mode="json"), created_at=created_at)
        self._add(record, "career claim revision already exists")
        return self._claim_from_record(record)

    @staticmethod
    def _claim_from_record(record: CareerClaimRevisionRecord) -> CareerClaimRevision:
        return CareerClaimRevision(revision_id=record.revision_id, logical_claim_id=record.logical_claim_id, revision=record.revision, source_id=record.source_id, claim=CareerClaim.model_validate(record.payload), supersedes_revision_id=record.supersedes_revision_id, reviewer_id=record.reviewer_id, created_at=_aware(record.created_at))

    def _add(self, record: object, message: str) -> None:
        try:
            self.session.add(record)
            self.session.flush()
        except IntegrityError as exc:
            raise RecordAlreadyExists(message) from exc
