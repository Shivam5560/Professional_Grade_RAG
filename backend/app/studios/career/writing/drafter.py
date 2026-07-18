from __future__ import annotations

import re

from app.studios.career.domain.drafts import (
    AssertedFact,
    DraftBullet,
    DraftTransformation,
    ResumeDraft,
)
from app.studios.career.domain.matching import CareerMatchResult
from app.studios.career.domain.claims import ClaimPredicate
from app.studios.career.domain.requirements import RoleRequirement


def draft_from_matches(match_result: CareerMatchResult, *, requirements: tuple[RoleRequirement, ...] = ()) -> ResumeDraft:
    """Focus matched evidence into concise bullets without introducing facts."""

    claim_by_id = {claim.id: claim for claim in match_result.selected_evidence}
    requirement_by_id = {requirement.id: requirement for requirement in requirements}
    bullets: list[DraftBullet] = []
    for selected in match_result.selected_matches:
        claim = claim_by_id[selected.claim_id]
        source = claim.source_spans[0]
        focused_text = _role_focused_text(
            claim.predicate,
            str(claim.object.value).strip() or source.exact_text,
            requirement_by_id.get(selected.requirement_id),
        )
        bullets.append(
            DraftBullet(
                source_claim_ids=(claim.id,),
                transformation=DraftTransformation.COMPRESSED,
                asserted_facts=(
                    AssertedFact(
                        kind=claim.object.kind,
                        value=claim.object.value,
                        unit=claim.object.unit,
                        measure=claim.object.measure,
                        source_claim_ids=(claim.id,),
                    ),
                ),
                added_keywords=(),
                before_text=(source.exact_text,),
                after_text=focused_text,
            )
        )
    return ResumeDraft.create(bullets=tuple(bullets))


def _role_focused_text(predicate: ClaimPredicate, value: str, requirement: RoleRequirement | None) -> str:
    """Create resume-style language using only supported and neutral words."""
    if predicate is ClaimPredicate.HAS_SKILL:
        return f"Using {value.rstrip('.')}."
    if predicate is ClaimPredicate.WORKED_AT:
        return f"At {value.rstrip('.')}."
    if predicate is ClaimPredicate.HELD_TITLE:
        return f"As {value.rstrip('.')}."
    if requirement is not None and not re.search(r"\d", value):
        requirement_tokens = set(re.findall(r"[^\W\d_]+", requirement.description.lower()))
        words = value.rstrip(".").split()
        relevant = [word for word in words if re.sub(r"[^\w-]", "", word).lower() in requirement_tokens]
        remaining = [word for word in words if word not in relevant]
        if relevant and remaining:
            return f"{' '.join(relevant)} — {' '.join(remaining)}."
    return value.rstrip(".") + "."
