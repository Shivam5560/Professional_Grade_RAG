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
    SourceSpan,
)
from app.studios.career.domain.drafts import (
    AssertedFact,
    DraftBullet,
    DraftTransformation,
    REGISTERED_PUBLICATION_TRANSFORMATIONS,
    ResumeDraft,
)
from app.studios.career.domain.provenance import safe_evidence_snippet

_NUMBER_PATTERN = re.compile(r"(?<![\w.])[-+]?\d+(?:,\d{3})*(?:\.\d+)?%?")
_DATE_PATTERN = re.compile(
    r"\b(?:19|20)\d{2}(?:-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|[12]\d|3[01]))?)?\b"
)
_WORD_PATTERN = re.compile(r"[^\W\d_]+(?:[-'][^\W\d_]+)*", re.UNICODE)
_CLAUSE_DELIMITER = re.compile(r"[.;,\n]|\band\b", re.IGNORECASE)
_NEUTRAL_PROSE_TOKENS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "with",
        "without",
        "using",
        "for",
        "to",
        "of",
        "in",
        "on",
        "by",
        "at",
        "from",
        "as",
        "across",
        "through",
        "into",
        "within",
        "during",
        "via",
        "per",
    }
)
_UNIT_ALIAS_FAMILIES = (
    frozenset({"percent", "percentage", "%"}),
    frozenset({"usd", "dollar", "dollars", "$"}),
    frozenset({"eur", "euro", "euros", "€"}),
    frozenset({"inr", "rupee", "rupees", "₹"}),
)
_SYMBOL_UNIT_ALIASES = frozenset({"%", "$", "€", "₹"})
_UNSUPPORTED_CODE = {
    ClaimValueKind.EMPLOYER: "unsupported-employer",
    ClaimValueKind.TITLE: "unsupported-title",
    ClaimValueKind.DATE: "unsupported-date",
    ClaimValueKind.SKILL: "unsupported-skill",
    ClaimValueKind.DEGREE: "unsupported-degree",
    ClaimValueKind.METRIC: "metric-altered",
}

UsedSpan = tuple[CareerClaim, SourceSpan]


def _critical(code: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        message=message,
        status=ValidationStatus.ERROR,
        critical=True,
    )


def _normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _word_tokens(value: str) -> tuple[str, ...]:
    return tuple(match.group(0).casefold() for match in _WORD_PATTERN.finditer(value))


def _phrase_is_present(text: str, phrase: str) -> bool:
    if phrase.strip() == "%":
        return "%" in text
    phrase_tokens = _word_tokens(phrase)
    text_tokens = _word_tokens(text)
    if not phrase_tokens:
        return False
    width = len(phrase_tokens)
    return any(
        text_tokens[index : index + width] == phrase_tokens
        for index in range(len(text_tokens) - width + 1)
    )


def _unit_is_present(text: str, unit: str) -> bool:
    normalized_unit = _normalized_text(unit)
    aliases = next(
        (
            family
            for family in _UNIT_ALIAS_FAMILIES
            if normalized_unit in family
        ),
        frozenset({normalized_unit}),
    )
    return any(
        alias in text
        if alias in _SYMBOL_UNIT_ALIASES
        else _phrase_is_present(text, alias)
        for alias in aliases
    )


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
        and _normalized_text(claim.object.measure or "")
        == _normalized_text(fact.measure or "")
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


def _decimal(raw: str | int | float) -> Decimal | None:
    normalized = str(raw).rstrip("%").replace(",", "")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def _date_matches(text: str) -> tuple[re.Match[str], ...]:
    return tuple(_DATE_PATTERN.finditer(text))


def _mention_context(text: str, start: int, end: int) -> str:
    delimiters = tuple(_CLAUSE_DELIMITER.finditer(text))
    context_start = max(
        (match.end() for match in delimiters if match.end() <= start),
        default=0,
    )
    context_end = min(
        (match.start() for match in delimiters if match.start() >= end),
        default=len(text),
    )
    return text[context_start:context_end]


def _number_mentions(text: str) -> tuple[tuple[Decimal, str], ...]:
    date_ranges = tuple((item.start(), item.end()) for item in _date_matches(text))
    mentions: list[tuple[Decimal, str]] = []
    for match in _NUMBER_PATTERN.finditer(text):
        if any(
            match.start() >= date_start and match.end() <= date_end
            for date_start, date_end in date_ranges
        ):
            continue
        value = _decimal(match.group(0))
        if value is not None:
            mentions.append(
                (value, _mention_context(text, match.start(), match.end()))
            )
    return tuple(mentions)


def _metric_mention_is_supported(
    value: Decimal,
    context: str,
    claims: tuple[CareerClaim, ...],
) -> bool:
    matching_claims = tuple(
        claim
        for claim in claims
        if claim.object.kind is ClaimValueKind.METRIC
        and _decimal(claim.object.value) == value
    )
    return any(
        claim.object.unit is not None
        and claim.object.measure is not None
        and _unit_is_present(context, claim.object.unit)
        and _phrase_is_present(context, claim.object.measure)
        for claim in matching_claims
    )


def _numeric_text_is_supported(
    text: str,
    used_spans: tuple[UsedSpan, ...],
) -> bool:
    used_claims = tuple(
        {claim.id: claim for claim, _ in used_spans}.values()
    )
    metric_claims = tuple(
        claim
        for claim in used_claims
        if claim.object.kind is ClaimValueKind.METRIC
    )
    nonmetric_numbers = {
        value
        for claim, span in used_spans
        if claim.object.kind is not ClaimValueKind.METRIC
        for value, _ in _number_mentions(span.exact_text)
    }
    for value, context in _number_mentions(text):
        matching_metric_exists = any(
            _decimal(claim.object.value) == value for claim in metric_claims
        )
        if matching_metric_exists:
            if not _metric_mention_is_supported(value, context, metric_claims):
                return False
        elif value not in nonmetric_numbers:
            return False
    return True


def _resolve_used_spans(
    bullet: DraftBullet,
    resolved_claims: tuple[CareerClaim, ...],
) -> tuple[tuple[UsedSpan, ...], tuple[str, ...]]:
    records: dict[tuple[str, str, str, str], UsedSpan] = {}
    unmatched: list[str] = []
    for before_text in bullet.before_text:
        matches = tuple(
            (claim, span)
            for claim in sorted(resolved_claims, key=lambda item: item.id)
            for span in claim.source_spans
            if span.exact_text == before_text
        )
        if not matches:
            unmatched.append(before_text)
            continue
        for claim, span in matches:
            records[(claim.id, span.source_id, span.locator, span.exact_text)] = (
                claim,
                span,
            )
    return tuple(records[key] for key in sorted(records)), tuple(unmatched)


def _unsupported_dates(
    text: str,
    used_spans: tuple[UsedSpan, ...],
) -> tuple[str, ...]:
    allowed = {
        match.group(0)
        for _, span in used_spans
        for match in _date_matches(span.exact_text)
    }
    allowed.update(
        match.group(0)
        for claim, _ in used_spans
        if claim.object.kind is ClaimValueKind.DATE
        for match in _date_matches(str(claim.object.value))
    )
    return tuple(
        sorted(
            {
                match.group(0)
                for match in _date_matches(text)
                if match.group(0) not in allowed
            }
        )
    )


def _unsupported_prose_tokens(
    bullet: DraftBullet,
    used_spans: tuple[UsedSpan, ...],
    supported_keywords: tuple[str, ...],
) -> tuple[str, ...]:
    allowed = set(_NEUTRAL_PROSE_TOKENS)
    for claim, span in used_spans:
        allowed.update(_word_tokens(span.exact_text))
        allowed.update(_word_tokens(str(claim.object.value)))
        allowed.update(_word_tokens(claim.subject.label))
        allowed.update(_word_tokens(claim.object.unit or ""))
        allowed.update(_word_tokens(claim.object.measure or ""))
    for keyword in supported_keywords:
        allowed.update(_word_tokens(keyword))
    return tuple(sorted(set(_word_tokens(bullet.after_text)) - allowed))


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
        algorithm_versions={"career-truth-guardian": "1.2.0"},
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
    """Independently reconcile draft text and metadata to canonical evidence."""

    if len({claim.id for claim in claims}) != len(claims):
        raise ValueError("canonical claims must have unique identifiers")
    claim_by_id = {claim.id: claim for claim in claims}
    issues: list[ValidationIssue] = []
    evidence_spans: dict[tuple[str, str, str, str], UsedSpan] = {}

    if not draft.bullets:
        issues.append(_critical("missing-provenance", "draft contains no evidence bullets"))

    for bullet_index, bullet in enumerate(draft.bullets):
        if (
            for_publication
            and bullet.transformation
            not in REGISTERED_PUBLICATION_TRANSFORMATIONS
        ):
            issues.append(
                _critical(
                    "unsupported-transformation",
                    f"bullet {bullet_index} uses unregistered publication transformation {bullet.transformation.value}",
                )
            )
        if not bullet.source_claim_ids:
            issues.append(
                _critical(
                    "missing-provenance",
                    f"bullet {bullet_index} has no source claim identifiers",
                )
            )
        if not bullet.before_text:
            issues.append(
                _critical(
                    "missing-provenance",
                    f"bullet {bullet_index} has no before-text transformation history",
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
        used_spans, unmatched_before_text = _resolve_used_spans(
            bullet,
            resolved_claims,
        )
        for claim, span in used_spans:
            evidence_spans[(claim.id, span.source_id, span.locator, span.exact_text)] = (
                claim,
                span,
            )
        if unmatched_before_text:
            issues.append(
                _critical(
                    "source-text-mismatch",
                    f"bullet {bullet_index} before text does not resolve to its claims",
                )
            )
        used_claim_ids = {claim.id for claim, _ in used_spans}
        unused_claim_ids = set(bullet.source_claim_ids) - used_claim_ids
        if unused_claim_ids:
            issues.append(
                _critical(
                    "missing-provenance",
                    f"bullet {bullet_index} does not identify a used span for every claim",
                )
            )
        used_source_texts = {span.exact_text for _, span in used_spans}
        if (
            bullet.transformation is DraftTransformation.VERBATIM
            and bullet.after_text not in used_source_texts
        ):
            issues.append(
                _critical(
                    "source-text-mismatch",
                    f"verbatim bullet {bullet_index} changed its source text",
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

        supported_keywords: list[str] = []
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
            if any(
                _claim_supports_keyword(claim, added.keyword)
                for claim in keyword_claims
            ):
                supported_keywords.append(added.keyword)
            else:
                issues.append(
                    _critical(
                        "unsupported-keyword",
                        f"keyword {added.keyword!r} in bullet {bullet_index} lacks factual support",
                    )
                )

        unsupported_dates = _unsupported_dates(bullet.after_text, used_spans)
        if unsupported_dates:
            issues.append(
                _critical(
                    "unsupported-date",
                    f"bullet {bullet_index} introduces unsupported dates",
                )
            )
        if not _numeric_text_is_supported(bullet.after_text, used_spans):
            issues.append(
                _critical(
                    "metric-altered",
                    f"bullet {bullet_index} introduces or moves a typed numeric value",
                )
            )
        unsupported_tokens = _unsupported_prose_tokens(
            bullet,
            used_spans,
            tuple(supported_keywords),
        )
        if unsupported_tokens:
            preview = ", ".join(unsupported_tokens[:12])
            issues.append(
                _critical(
                    "unsupported-text-assertion",
                    f"bullet {bullet_index} introduces unsupported prose tokens: {preview}",
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
            source_id=claim.id,
            locator=span.locator,
            snippet=safe_evidence_snippet(span.exact_text),
            relevance=1.0,
        )
        for claim, span in (
            evidence_spans[key] for key in sorted(evidence_spans)
        )
    )
    has_critical = any(issue.critical for issue in deduplicated_issues)
    return AIResult[ResumeDraft](
        output=None if has_critical else draft,
        evidence=evidence,
        quality=_quality(deduplicated_issues, trace_id=trace_id),
    )
