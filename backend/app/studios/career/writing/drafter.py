from __future__ import annotations

from app.studios.career.domain.drafts import (
    AssertedFact,
    DraftBullet,
    DraftTransformation,
    ResumeDraft,
)
from app.studios.career.domain.matching import CareerMatchResult


def draft_from_matches(match_result: CareerMatchResult) -> ResumeDraft:
    """Focus matched evidence into concise bullets without introducing facts."""

    claim_by_id = {claim.id: claim for claim in match_result.selected_evidence}
    bullets: list[DraftBullet] = []
    for selected in match_result.selected_matches:
        claim = claim_by_id[selected.claim_id]
        source = claim.source_spans[0]
        focused_text = str(claim.object.value).strip() or source.exact_text
        focused_text = focused_text.rstrip(".") + "."
        if focused_text == source.exact_text:
            focused_text = focused_text.rstrip(".")
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
