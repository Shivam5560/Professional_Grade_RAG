from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.platform.approvals import ApprovalDecision, ApprovalStatus, decide_approval
from app.platform.evidence import VerificationStatus
from app.platform.quality import AIResult
from app.platform.runtime import StudioRun, StudioRunState
from app.studios.career.domain import (
    CareerClaim,
    ClaimContext,
    ClaimObject,
    ClaimPredicate,
    ClaimSubject,
    ClaimSubjectKind,
    ClaimValueKind,
    RequirementCategory,
    RequirementPriority,
    RoleRequirement,
    ScoreComponents,
    SourceSpan,
    TemporalScope,
)
from app.studios.career.matching import score_candidate_edge
from app.studios.career.workflow import CareerSpecialist


NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(minutes=5)
SUBJECT = ClaimSubject(
    kind=ClaimSubjectKind.PERSON,
    id="person-7",
    label="Candidate",
)


def make_run() -> StudioRun:
    return StudioRun(
        id="run-career-1",
        owner_id=7,
        studio_id="career",
        operation="draft",
        idempotency_key="career-draft-1",
        input_fingerprint="a" * 64,
        created_at=NOW,
        updated_at=NOW,
    )


def make_claim(
    *,
    status: VerificationStatus = VerificationStatus.VERIFIED,
) -> CareerClaim:
    return CareerClaim.create(
        subject=SUBJECT,
        predicate=ClaimPredicate.HAS_SKILL,
        object=ClaimObject(kind=ClaimValueKind.SKILL, value="Python"),
        source_spans=(
            SourceSpan(
                source_id="resume-1",
                locator="skills:python",
                exact_text="Built production services with Python.",
            ),
        ),
        temporal_scope=TemporalScope(
            start=date(2023, 1, 1),
            end=date(2025, 12, 31),
        ),
        verification_status=status,
        confidence=0.95 if status is VerificationStatus.VERIFIED else 0.65,
        verifier_id="reviewer-7",
        context=ClaimContext(
            employer_id="employer-acme",
            project_id="project-platform",
        ),
    )


def make_requirement() -> RoleRequirement:
    return RoleRequirement(
        id="req-python",
        priority=RequirementPriority.REQUIRED,
        category=RequirementCategory.SKILL,
        description="Production Python",
        source_span=SourceSpan(
            source_id="job-1",
            locator="requirements:python",
            exact_text="Production Python is required.",
        ),
        confidence=0.95,
        weight=3.0,
    )


def make_components() -> ScoreComponents:
    return ScoreComponents(
        semantic_relevance=0.95,
        evidence_strength=1.0,
        recency=0.9,
        duration_seniority=0.9,
        transferability=1.0,
        specificity=1.0,
    )


def test_inferred_claim_pauses_for_review() -> None:
    inferred = make_claim(status=VerificationStatus.INFERRED)

    response = CareerSpecialist().run(
        make_run(),
        claims=(inferred,),
        requirements=(make_requirement(),),
        candidate_edges=(),
        now=NOW,
    )

    assert response.run.state is StudioRunState.AWAITING_INPUT
    assert response.run.current_step == "claim-review"
    assert response.approval is not None
    assert response.approval.decision_type == "inferred-claims"
    assert response.approval.status is ApprovalStatus.PENDING
    assert response.approval.proposed_changes == (inferred.id,)
    assert response.approval.evidence_ids == (inferred.id,)
    assert isinstance(response.result, AIResult)
    assert response.result.output is None
    assert response.result.evidence[0].source_id == inferred.id


def test_verified_path_waits_for_final_resume_approval() -> None:
    verified = make_claim()
    requirement = make_requirement()
    edge = score_candidate_edge(requirement, verified, make_components())

    response = CareerSpecialist().run(
        make_run(),
        claims=(verified,),
        requirements=(requirement,),
        candidate_edges=(edge,),
        now=NOW,
    )

    assert response.run.state is StudioRunState.AWAITING_INPUT
    assert response.run.current_step == "final-resume-approval"
    assert response.approval is not None
    assert response.approval.decision_type == "final-resume"
    assert response.approval.proposed_changes == (response.result.output.draft.id,)
    assert response.approval.evidence_ids == (verified.id,)
    assert response.result.output.draft.publication_ready is False
    assert response.result.output.match.mandatory_coverage.lower_bound == 1.0
    assert response.result.output.match.unmatched_requirements == ()


def test_approved_resume_succeeds_with_end_to_end_provenance() -> None:
    verified = make_claim()
    requirement = make_requirement()
    edge = score_candidate_edge(requirement, verified, make_components())
    specialist = CareerSpecialist()
    first = specialist.run(
        make_run(),
        claims=(verified,),
        requirements=(requirement,),
        candidate_edges=(edge,),
        now=NOW,
    )
    assert first.approval is not None
    approval = decide_approval(
        first.approval,
        ApprovalDecision.APPROVE,
        reviewer_id=7,
        now=LATER,
        comment="Approved for publication",
    )

    final = specialist.run(
        first.run,
        claims=(verified,),
        requirements=(requirement,),
        candidate_edges=(edge,),
        now=LATER,
        approval=approval,
    )

    assert final.run.state is StudioRunState.SUCCEEDED
    assert final.result.output is not None
    assert final.result.output.draft.publication_ready is True
    assert final.approval == approval
    claim_ids = {verified.id}
    for draft_bullet in final.result.output.draft.bullets:
        assert set(draft_bullet.source_claim_ids) <= claim_ids
        for asserted_fact in draft_bullet.asserted_facts:
            assert set(asserted_fact.source_claim_ids) <= claim_ids
    assert {item.source_id for item in final.result.evidence} == {
        item.id for item in final.result.output.selected_evidence
    }


def test_final_approval_must_match_run_draft_owner_and_evidence() -> None:
    verified = make_claim()
    requirement = make_requirement()
    edge = score_candidate_edge(requirement, verified, make_components())
    specialist = CareerSpecialist()
    first = specialist.run(
        make_run(),
        claims=(verified,),
        requirements=(requirement,),
        candidate_edges=(edge,),
        now=NOW,
    )
    assert first.approval is not None
    approved = decide_approval(
        first.approval,
        ApprovalDecision.APPROVE,
        reviewer_id=7,
        now=LATER,
    )
    wrong_run = approved.model_copy(update={"run_id": "run-other"})

    with pytest.raises(ValueError, match="does not match"):
        specialist.run(
            first.run,
            claims=(verified,),
            requirements=(requirement,),
            candidate_edges=(edge,),
            now=LATER,
            approval=wrong_run,
        )


def test_no_selected_evidence_abstains_without_requesting_final_approval() -> None:
    verified = make_claim()

    response = CareerSpecialist().run(
        make_run(),
        claims=(verified,),
        requirements=(make_requirement(),),
        candidate_edges=(),
        now=NOW,
    )

    assert response.run.state is StudioRunState.FAILED
    assert response.run.current_step == "truth-validation"
    assert response.approval is None
    assert response.result.output is None
    assert response.result.quality.abstention_reason == (
        "career draft failed truth validation"
    )
