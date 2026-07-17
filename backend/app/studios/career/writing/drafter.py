from __future__ import annotations

from app.studios.career.domain.drafts import (
    AssertedFact,
    DraftBullet,
    DraftTransformation,
    ResumeDraft,
)
from app.studios.career.domain.matching import CareerMatchResult


def draft_from_matches(match_result: CareerMatchResult) -> ResumeDraft:
    """Create a literal draft without introducing any new fact or keyword."""

    claim_by_id = {claim.id: claim for claim in match_result.selected_evidence}
    bullets: list[DraftBullet] = []
    for selected in match_result.selected_matches:
        claim = claim_by_id[selected.claim_id]
        source = claim.source_spans[0]
        bullets.append(
            DraftBullet(
                source_claim_ids=(claim.id,),
                transformation=DraftTransformation.VERBATIM,
                asserted_facts=(
                    AssertedFact(
                        kind=claim.object.kind,
                        value=claim.object.value,
                        unit=claim.object.unit,
                        source_claim_ids=(claim.id,),
                    ),
                ),
                added_keywords=(),
                before_text=(source.exact_text,),
                after_text=source.exact_text,
            )
        )
    return ResumeDraft.create(bullets=tuple(bullets))
