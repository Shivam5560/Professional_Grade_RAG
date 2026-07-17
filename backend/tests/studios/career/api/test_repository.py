from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.database import Base
from app.db.models import User
from app.platform.evidence import VerificationStatus
from app.platform.persistence import RecordNotFound
from app.platform.persistence.models import StudioRunRecord
from app.studios.career.domain import (
    CareerClaim,
    CareerMatchResult,
    ClaimObject,
    ClaimPredicate,
    ClaimSubject,
    ClaimSubjectKind,
    ClaimValueKind,
    CoverageBand,
    CoverageSummary,
    DraftBullet,
    DraftTransformation,
    MatchStrength,
    RequirementCategory,
    RequirementPriority,
    ResumeDraft,
    RoleRequirement,
    ScoreComponents,
    SelectedMatch,
    SourceSpan,
    TemporalScope,
)
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
from app.studios.career.persistence.repository import (
    CareerRepository,
    InvalidCareerState,
)


NOW = datetime(2026, 7, 18, 8, 0, tzinfo=timezone.utc)


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    tables = [
        User.__table__,
        StudioRunRecord.__table__,
        CareerSourceRecord.__table__,
        CareerClaimRevisionRecord.__table__,
        CareerRoleRecord.__table__,
        CareerRequirementRecord.__table__,
        CareerMatchRecord.__table__,
        CareerRequirementMatchRecord.__table__,
        CareerDraftRecord.__table__,
        CareerDraftClaimRecord.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)
    with Session(engine) as db:
        db.add_all(
            [
                User(id=7, email="owner@example.com", hashed_password="x"),
                User(id=8, email="other@example.com", hashed_password="x"),
            ]
        )
        db.commit()
        db.add(
            StudioRunRecord(
                id="run-1",
                owner_id=7,
                studio_id="career",
                operation="draft",
                idempotency_key="run-1",
                input_fingerprint="a" * 64,
                state="queued",
                progress=0.0,
                cancellation_requested=False,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        db.commit()
        yield db


def make_claim(
    source_id: str = "source-1",
    *,
    status: VerificationStatus = VerificationStatus.INFERRED,
    value: str = "Python",
) -> CareerClaim:
    return CareerClaim.create(
        subject=ClaimSubject(
            kind=ClaimSubjectKind.PERSON,
            id="person-7",
            label="Candidate",
        ),
        predicate=ClaimPredicate.HAS_SKILL,
        object=ClaimObject(kind=ClaimValueKind.SKILL, value=value),
        source_spans=(
            SourceSpan(
                source_id=source_id,
                locator="skills:1",
                exact_text=f"Built production services with {value}.",
            ),
        ),
        temporal_scope=TemporalScope(
            start=date(2023, 1, 1),
            end=date(2025, 12, 31),
        ),
        verification_status=status,
        confidence=0.7 if status is VerificationStatus.INFERRED else 0.95,
        verifier_id="structured-ingestion" if status is VerificationStatus.INFERRED else "7",
    )


def make_requirement() -> RoleRequirement:
    return RoleRequirement(
        id="req-python",
        priority=RequirementPriority.REQUIRED,
        category=RequirementCategory.SKILL,
        description="Production Python",
        source_span=SourceSpan(
            source_id="role-1",
            locator="requirements:1",
            exact_text="Production Python is required.",
        ),
        confidence=1.0,
        weight=3.0,
    )


def make_match(claim: CareerClaim, requirement: RoleRequirement) -> CareerMatchResult:
    components = ScoreComponents(
        semantic_relevance=1.0,
        evidence_strength=1.0,
        recency=1.0,
        duration_seniority=1.0,
        transferability=1.0,
        specificity=1.0,
    )
    selected = SelectedMatch(
        requirement_id=requirement.id,
        claim_id=claim.id,
        components=components,
        score=1.0,
        strength=MatchStrength.STRONG,
        objective_weight=3.0,
        uncertain=False,
    )
    coverage = CoverageSummary(
        total_weight=3.0,
        confident_matched_weight=3.0,
        possible_matched_weight=3.0,
        lower_bound=1.0,
        upper_bound=1.0,
        band=CoverageBand.COMPLETE,
    )
    empty_coverage = CoverageSummary(
        total_weight=0.0,
        confident_matched_weight=0.0,
        possible_matched_weight=0.0,
        lower_bound=0.0,
        upper_bound=0.0,
        band=CoverageBand.NONE,
    )
    return CareerMatchResult(
        selected_matches=(selected,),
        mandatory_coverage=coverage,
        preferred_coverage=empty_coverage,
        unmatched_requirements=(),
        uncertain_matches=(),
        uncertain_requirement_ids=(),
        transferable_matches=(selected,),
        selected_evidence=(claim,),
    )


def make_draft(claim: CareerClaim) -> ResumeDraft:
    text = claim.source_spans[0].exact_text
    return ResumeDraft.create(
        bullets=(
            DraftBullet(
                source_claim_ids=(claim.id,),
                transformation=DraftTransformation.VERBATIM,
                before_text=(text,),
                after_text=text,
            ),
        )
    )


def test_models_keep_relationships_relational_and_owner_indexed() -> None:
    assert CareerSourceRecord.__table__.c.owner_id.nullable is False
    assert CareerClaimRevisionRecord.__table__.c.source_id.foreign_keys
    assert CareerRequirementRecord.__table__.c.role_id.foreign_keys
    assert CareerRequirementMatchRecord.__table__.c.requirement_record_id.foreign_keys
    assert CareerDraftClaimRecord.__table__.c.claim_revision_id.foreign_keys
    assert any(
        index.name == "ix_career_claim_revisions_owner_logical"
        for index in CareerClaimRevisionRecord.__table__.indexes
    )


def test_claim_review_creates_append_only_audited_revisions(session: Session) -> None:
    repo = CareerRepository(session)
    repo.add_source(
        source_id="source-1",
        owner_id=7,
        filename="resume.json",
        media_type="application/json",
        content_digest="a" * 64,
        created_at=NOW,
    )
    initial = repo.add_claim(make_claim(), owner_id=7, created_at=NOW)

    verified = repo.review_claim(
        initial.logical_claim_id,
        action="verify",
        owner_id=7,
        reviewer_id=7,
        now=NOW,
    )

    assert initial.revision == 1
    assert verified.revision == 2
    assert verified.supersedes_revision_id == initial.revision_id
    assert verified.claim.verification_status is VerificationStatus.VERIFIED
    assert verified.reviewer_id == 7
    records = session.execute(
        select(CareerClaimRevisionRecord).order_by(CareerClaimRevisionRecord.revision)
    ).scalars().all()
    assert [record.status for record in records] == ["inferred", "verified"]
    assert records[0].is_current is False
    assert records[1].is_current is True


def test_revise_preserves_logical_identity_and_rejected_claim_cannot_enter_draft(
    session: Session,
) -> None:
    repo = CareerRepository(session)
    repo.add_source(
        source_id="source-1",
        owner_id=7,
        filename="resume.json",
        media_type="application/json",
        content_digest="b" * 64,
        created_at=NOW,
    )
    initial = repo.add_claim(make_claim(), owner_id=7, created_at=NOW)
    revised_claim = make_claim(status=VerificationStatus.VERIFIED, value="Python 3")
    revised = repo.review_claim(
        initial.logical_claim_id,
        action="revise",
        owner_id=7,
        reviewer_id=7,
        now=NOW,
        replacement=revised_claim,
    )
    assert revised.logical_claim_id == initial.logical_claim_id
    assert revised.claim.id != initial.claim.id

    rejected = repo.review_claim(
        initial.logical_claim_id,
        action="reject",
        owner_id=7,
        reviewer_id=7,
        now=NOW,
    )
    requirement = make_requirement()
    role = repo.add_role(
        role_id="role-1",
        title="Senior Engineer",
        requirements=(requirement,),
        owner_id=7,
        created_at=NOW,
    )
    match = repo.add_match(
        match_id="match-1",
        role_id=role.id,
        result=make_match(rejected.claim, requirement),
        owner_id=7,
        created_at=NOW,
    )
    with pytest.raises(InvalidCareerState, match="verified current claims"):
        repo.add_draft(
            run_id="run-1",
            match_id=match.id,
            draft=make_draft(rejected.claim),
            owner_id=7,
            created_at=NOW,
        )


def test_match_and_draft_relationships_are_append_only_and_owner_scoped(
    session: Session,
) -> None:
    repo = CareerRepository(session)
    repo.add_source(
        source_id="source-1",
        owner_id=7,
        filename="resume.json",
        media_type="application/json",
        content_digest="c" * 64,
        created_at=NOW,
    )
    claim_revision = repo.add_claim(
        make_claim(status=VerificationStatus.VERIFIED),
        owner_id=7,
        created_at=NOW,
    )
    requirement = make_requirement()
    role = repo.add_role(
        role_id="role-1",
        title="Senior Engineer",
        requirements=(requirement,),
        owner_id=7,
        created_at=NOW,
    )
    result = make_match(claim_revision.claim, requirement)
    match = repo.add_match(
        match_id="match-1",
        role_id=role.id,
        result=result,
        owner_id=7,
        created_at=NOW,
    )
    draft = repo.add_draft(
        run_id="run-1",
        match_id=match.id,
        draft=make_draft(claim_revision.claim),
        owner_id=7,
        created_at=NOW,
    )

    assert len(repo.get_role(role.id, owner_id=7).requirements) == 1
    assert repo.get_match(match.id, owner_id=7).result == result
    assert repo.get_draft(draft.id, owner_id=7).draft == draft.draft
    assert session.query(CareerRequirementMatchRecord).count() == 1
    assert session.query(CareerDraftClaimRecord).count() == 1
    with pytest.raises(RecordNotFound):
        repo.get_source("source-1", owner_id=8)
    with pytest.raises(RecordNotFound):
        repo.get_role(role.id, owner_id=8)
    with pytest.raises(RecordNotFound):
        repo.get_match(match.id, owner_id=8)
    with pytest.raises(RecordNotFound):
        repo.get_draft(draft.id, owner_id=8)


def test_caller_rollback_removes_partial_career_graph(session: Session) -> None:
    repo = CareerRepository(session)
    repo.add_source(
        source_id="source-rollback",
        owner_id=7,
        filename="resume.json",
        media_type="application/json",
        content_digest="d" * 64,
        created_at=NOW,
    )
    repo.add_claim(
        make_claim(source_id="source-rollback"),
        owner_id=7,
        created_at=NOW,
    )
    session.rollback()

    assert session.query(CareerSourceRecord).count() == 0
    assert session.query(CareerClaimRevisionRecord).count() == 0
