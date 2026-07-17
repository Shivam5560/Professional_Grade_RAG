from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from itertools import combinations

from app.platform.evidence import VerificationStatus
from app.platform.quality import (
    AIResult,
    EvidenceReference,
    QualityMetadata,
    ValidationIssue,
    ValidationStatus,
)
from app.studios.career.domain.claims import (
    CareerClaim,
    ClaimValueKind,
    JsonScalar,
)
from app.studios.career.domain.drafts import (
    AssertedFact,
    DraftBullet,
    DraftTransformation,
    ResumeDraft,
)

_NUMBER_PATTERN = re.compile(r"(?<![\w.])[-+]?\d+(?:,\d{3})*(?:\.\d+)?%?")
_UNSUPPORTED_CODE = {
    ClaimValueKind.EMPLOYER: "unsupported-employer",
    ClaimValueKind.TITLE: "unsupported-title",
    ClaimValueKind.DATE: "unsupported-date",
    ClaimValueKind.SKILL: "unsupported-skill",
    ClaimValueKind.DEGREE: "unsupported-degree",
    ClaimValueKind.METRIC: "metric-altered",
}


def _critical(code: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        message=message,
        status=ValidationStatus.ERROR,
        critical=True,
    )


def _normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _values_match(left: JsonScalar, right: JsonScalar) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return _normalized_text(left) == _normalized_text(right)
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    return left == right


def _fact_is_supported(fact: AssertedFact, claims: tuple[CareerClaim, ...]) -> bool:
    return any(
        claim.object.kind is fact.kind
        and _values_match(claim.object.value, fact.value)
        and _normalized_text(claim.object.unit or "")
        == _normalized_text(fact.unit or "")
        for claim in claims
    )


def _claim_supports_keyword(claim: CareerClaim, keyword: str) -> bool:
    normalized_keyword = _normalized_text(keyword)
    candidates = [
        str(claim.object.value),
        claim.subject.label,
        *(span.exact_text for span in claim.source_spans),
    ]
    pattern = re.compile(
        rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)",
        flags=re.IGNORECASE,
    )
    return any(pattern.search(_normalized_text(candidate)) for candidate in candidates)


def _decimal_numbers(text: str) -> set[Decimal]:
    numbers: set[Decimal] = set()
    for raw in _NUMBER_PATTERN.findall(text):
        normalized = raw.rstrip("%").replace(",", "")
        try:
            numbers.add(Decimal(normalized))
        except InvalidOperation:
            continue
    return numbers


def _allowed_numbers(claims: tuple[CareerClaim, ...]) -> set[Decimal]:
    values: set[Decimal] = set()
    for claim in claims:
        for span in claim.source_spans:
            values.update(_decimal_numbers(span.exact_text))
        if claim.object.kind is ClaimValueKind.METRIC:
            values.update(_decimal_numbers(str(claim.object.value)))
    return values


def _claims_are_compatible(left: CareerClaim, right: CareerClaim) -> bool:
    shared_employer = (
        left.context.employer_id is not None
        and left.context.employer_id == right.context.employer_id
    )
    shared_project = (
        left.context.project_id is not None
        and left.context.project_id == right.context.project_id
    )
    return (
        shared_employer or shared_project
    ) and left.temporal_scope.overlaps(right.temporal_scope)


def _validate_combination(
    bullet: DraftBullet,
    resolved_claims: tuple[CareerClaim, ...],
) -> tuple[ValidationIssue, ...]:
    if bullet.transformation is DraftTransformation.COMBINED:
        if len(resolved_claims) < 2:
            return (
                _critical(
                    "incompatible-combination",
                    "combined bullets require at least two resolved source claims",
                ),
            )
        if any(
            not _claims_are_compatible(left, right)
            for left, right in combinations(resolved_claims, 2)
        ):
            return (
                _critical(
                    "incompatible-combination",
                    "combined claims must share employer or project and temporal scope",
                ),
            )
    elif len(resolved_claims) > 1:
        return (
            _critical(
                "incompatible-combination",
                "multiple source claims require the combined transformation",
            ),
        )
    return ()


def _quality(
    issues: tuple[ValidationIssue, ...],
    *,
    trace_id: str,
) -> QualityMetadata:
    has_critical = any(issue.critical for issue in issues)
    return QualityMetadata(
        algorithm_versions={"career-truth-guardian": "1.0.0"},
        model_versions={},
        prompt_versions={},
        confidence_components={"truth": 0.0 if has_critical else 1.0},
        validations=issues,
        warnings=(),
        abstention_reason=(
            "career draft failed truth validation" if has_critical else None
        ),
        latency_ms=0.0,
        input_tokens=0,
        output_tokens=0,
        estimated_cost_usd=0.0,
        trace_id=trace_id,
    )


def validate_draft(
    draft: ResumeDraft,
    *,
    claims: tuple[CareerClaim, ...],
    for_publication: bool,
    trace_id: str = "career-truth-guardian",
) -> AIResult[ResumeDraft]:
    """Resolve every structured assertion to canonical evidence or abstain."""

    if len({claim.id for claim in claims}) != len(claims):
        raise ValueError("canonical claims must have unique identifiers")
    claim_by_id = {claim.id: claim for claim in claims}
    issues: list[ValidationIssue] = []
    evidence_claim_ids: set[str] = set()

    if not draft.bullets:
        issues.append(_critical("missing-provenance", "draft contains no evidence bullets"))

    for bullet_index, bullet in enumerate(draft.bullets):
        if not bullet.source_claim_ids:
            issues.append(
                _critical(
                    "missing-provenance",
                    f"bullet {bullet_index} has no source claim identifiers",
                )
            )
        if not bullet.asserted_facts:
            issues.append(
                _critical(
                    "missing-provenance",
                    f"bullet {bullet_index} has no structured asserted facts",
                )
            )

        resolved: list[CareerClaim] = []
        for claim_id in bullet.source_claim_ids:
            claim = claim_by_id.get(claim_id)
            if claim is None:
                issues.append(
                    _critical(
                        "unknown-claim",
                        f"bullet {bullet_index} references unknown claim {claim_id}",
                    )
                )
                continue
            resolved.append(claim)
            evidence_claim_ids.add(claim.id)
            if (
                for_publication
                and claim.verification_status is not VerificationStatus.VERIFIED
            ):
                issues.append(
                    _critical(
                        "unverified-claim",
                        f"publishable bullet {bullet_index} references {claim.verification_status} claim {claim.id}",
                    )
                )

        resolved_claims = tuple(resolved)
        issues.extend(_validate_combination(bullet, resolved_claims))

        source_texts = {
            span.exact_text
            for claim in resolved_claims
            for span in claim.source_spans
        }
        if any(text not in source_texts for text in bullet.before_text):
            issues.append(
                _critical(
                    "source-text-mismatch",
                    f"bullet {bullet_index} before text does not resolve to its claims",
                )
            )
        if (
            bullet.transformation is DraftTransformation.VERBATIM
            and bullet.after_text not in source_texts
        ):
            issues.append(
                _critical(
                    "source-text-mismatch",
                    f"verbatim bullet {bullet_index} changed its source text",
                )
            )

        unsupported_numbers = _decimal_numbers(bullet.after_text) - _allowed_numbers(
            resolved_claims
        )
        if unsupported_numbers:
            issues.append(
                _critical(
                    "metric-altered",
                    f"bullet {bullet_index} introduces or changes numeric values",
                )
            )

        bullet_claim_ids = set(bullet.source_claim_ids)
        for fact_index, asserted in enumerate(bullet.asserted_facts):
            if not asserted.source_claim_ids:
                issues.append(
                    _critical(
                        "missing-provenance",
                        f"fact {fact_index} in bullet {bullet_index} has no source claims",
                    )
                )
                continue
            if not set(asserted.source_claim_ids) <= bullet_claim_ids:
                issues.append(
                    _critical(
                        "missing-provenance",
                        f"fact {fact_index} in bullet {bullet_index} cites claims outside the bullet",
                    )
                )
            fact_claims = tuple(
                claim_by_id[claim_id]
                for claim_id in asserted.source_claim_ids
                if claim_id in claim_by_id
            )
            if not _fact_is_supported(asserted, fact_claims):
                code = _UNSUPPORTED_CODE.get(asserted.kind, "unsupported-fact")
                issues.append(
                    _critical(
                        code,
                        f"fact {fact_index} in bullet {bullet_index} is not supported by its claims",
                    )
                )

        for keyword_index, added in enumerate(bullet.added_keywords):
            if not added.source_claim_ids:
                issues.append(
                    _critical(
                        "missing-provenance",
                        f"keyword {keyword_index} in bullet {bullet_index} has no source claims",
                    )
                )
                continue
            if not set(added.source_claim_ids) <= bullet_claim_ids:
                issues.append(
                    _critical(
                        "missing-provenance",
                        f"keyword {keyword_index} in bullet {bullet_index} cites claims outside the bullet",
                    )
                )
            keyword_claims = tuple(
                claim_by_id[claim_id]
                for claim_id in added.source_claim_ids
                if claim_id in claim_by_id
            )
            if not any(
                _claim_supports_keyword(claim, added.keyword)
                for claim in keyword_claims
            ):
                issues.append(
                    _critical(
                        "unsupported-keyword",
                        f"keyword {added.keyword!r} in bullet {bullet_index} lacks factual support",
                    )
                )

    deduplicated_issues = tuple(
        {
            (issue.code, issue.message): issue
            for issue in issues
        }.values()
    )
    evidence = tuple(
        EvidenceReference(
            source_id=claim_id,
            locator=claim_by_id[claim_id].source_spans[0].locator,
            snippet=claim_by_id[claim_id].source_spans[0].exact_text,
            relevance=1.0,
        )
        for claim_id in sorted(evidence_claim_ids)
    )
    has_critical = bool(deduplicated_issues)
    return AIResult[ResumeDraft](
        output=None if has_critical else draft,
        evidence=evidence,
        quality=_quality(deduplicated_issues, trace_id=trace_id),
    )
