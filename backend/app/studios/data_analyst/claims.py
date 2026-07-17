from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from .domain import (
    ClaimVerification,
    ComputationRecord,
    EvidenceLink,
    FindingClaim,
    FindingLanguageClass,
    canonical_digest,
    canonical_json,
)

_CORRELATION_METHODS = frozenset(
    {"pearson-correlation", "spearman-correlation"}
)
_CAUSAL_LANGUAGE = re.compile(
    r"\b(?:caus(?:e|es|ed|ing)|driv(?:e|es|en|ing)|"
    r"leads?\s+to|effects?|impacts?)\b",
    re.IGNORECASE,
)


class EvidenceResolutionError(ValueError):
    """Raised when a claim path cannot be resolved safely."""


def resolve_evidence_value(record: ComputationRecord, value_path: str) -> Any:
    parts = value_path.split(".")
    if not parts or parts[0] != "output":
        raise EvidenceResolutionError("evidence value paths must start with output")

    current: Any = record.output
    for token in parts[1:]:
        if isinstance(current, Mapping):
            if token not in current:
                raise EvidenceResolutionError(f"mapping key does not exist: {token}")
            current = current[token]
            continue
        if isinstance(current, Sequence) and not isinstance(current, (str, bytes)):
            if not token.isdigit():
                raise EvidenceResolutionError(f"sequence index is invalid: {token}")
            index = int(token)
            if index >= len(current):
                raise EvidenceResolutionError(f"sequence index is out of range: {token}")
            current = current[index]
            continue
        raise EvidenceResolutionError(f"path continues beyond a scalar: {token}")
    return current


def _claim(
    *,
    subject: str,
    predicate: str,
    value: str | int | float | bool | None,
    scope: Mapping[str, Any],
    record: ComputationRecord,
    value_path: str,
    language_class: FindingLanguageClass,
    method_validity: float,
) -> FindingClaim:
    payload = {
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "scope": dict(scope),
        "evidence_id": record.evidence.id,
        "value_path": value_path,
        "language_class": language_class.value,
    }
    return FindingClaim(
        id=f"claim-{canonical_digest(payload)[:24]}",
        subject=subject,
        predicate=predicate,
        value=value,
        scope=scope,
        evidence_links=(
            EvidenceLink(
                evidence_id=record.evidence.id,
                value_path=value_path,
            ),
        ),
        confidence_components={
            "evidence-resolution": 1.0,
            "method-validity": method_validity,
        },
        language_class=language_class,
    )


def synthesize_claims(
    records: tuple[ComputationRecord, ...],
) -> tuple[FindingClaim, ...]:
    claims: list[FindingClaim] = []
    for record in records:
        if record.method_id == "descriptive-summary":
            claims.append(
                _claim(
                    subject="dataset",
                    predicate="has row count",
                    value=record.output["row_count"],
                    scope={"statistic": "row-count"},
                    record=record,
                    value_path="output.row_count",
                    language_class=FindingLanguageClass.OBSERVATION,
                    method_validity=1.0,
                )
            )
            for column_name, summary in record.output["columns"].items():
                mean = summary.get("mean")
                if summary["semantic_type"] != "numeric" or mean is None:
                    continue
                claims.append(
                    _claim(
                        subject=column_name,
                        predicate="has arithmetic mean",
                        value=mean,
                        scope={"statistic": "mean"},
                        record=record,
                        value_path=f"output.columns.{column_name}.mean",
                        language_class=FindingLanguageClass.OBSERVATION,
                        method_validity=1.0,
                    )
                )
        elif record.method_id == "categorical-frequency":
            for column_name, summary in record.output["columns"].items():
                frequencies = summary["frequencies"]
                if not frequencies:
                    continue
                top = frequencies[0]
                claims.append(
                    _claim(
                        subject=column_name,
                        predicate="has top category count",
                        value=top["count"],
                        scope={"category": top["value"]},
                        record=record,
                        value_path=f"output.columns.{column_name}.frequencies.0.count",
                        language_class=FindingLanguageClass.OBSERVATION,
                        method_validity=1.0,
                    )
                )
        elif record.method_id in _CORRELATION_METHODS:
            validity = (
                1.0
                if all(result.status.value == "pass" for result in record.assumption_results)
                else 0.8
            )
            for index, pair in enumerate(record.output["pairs"]):
                coefficient = pair["coefficient"]
                if coefficient is None:
                    continue
                left, right = pair["columns"]
                claims.append(
                    _claim(
                        subject=f"{left} and {right}",
                        predicate=f"have {pair['method']} correlation coefficient",
                        value=coefficient,
                        scope={"method": pair["method"]},
                        record=record,
                        value_path=f"output.pairs.{index}.coefficient",
                        language_class=FindingLanguageClass.ASSOCIATION,
                        method_validity=validity,
                    )
                )
    return tuple(claims)


def _same_json_value(left: Any, right: Any) -> bool:
    return canonical_json(left) == canonical_json(right)


def verify_claims(
    claims: tuple[FindingClaim, ...],
    records: tuple[ComputationRecord, ...],
) -> tuple[ClaimVerification, ...]:
    evidence_counts = Counter(record.evidence.id for record in records)
    records_by_evidence = {record.evidence.id: record for record in records}
    verifications: list[ClaimVerification] = []

    for claim in claims:
        issues: list[str] = []

        def add_issue(code: str) -> None:
            if code not in issues:
                issues.append(code)

        resolved_values: list[Any] = []
        supporting_records: list[ComputationRecord] = []
        for link in claim.evidence_links:
            if evidence_counts[link.evidence_id] == 0:
                add_issue("unknown-evidence")
                continue
            if evidence_counts[link.evidence_id] > 1:
                add_issue("ambiguous-evidence")
                continue
            record = records_by_evidence[link.evidence_id]
            supporting_records.append(record)
            try:
                resolved_values.append(resolve_evidence_value(record, link.value_path))
            except EvidenceResolutionError:
                add_issue("invalid-evidence-path")

        if (
            len(resolved_values) == len(claim.evidence_links)
            and not any(_same_json_value(value, claim.value) for value in resolved_values)
        ):
            add_issue("unsupported-value")

        association_only = any(
            record.method_id in _CORRELATION_METHODS for record in supporting_records
        )
        if association_only:
            if claim.language_class is not FindingLanguageClass.ASSOCIATION:
                add_issue("invalid-language-class")
            language = f"{claim.subject} {claim.predicate}"
            if _CAUSAL_LANGUAGE.search(language):
                add_issue("causal-language")

        verifications.append(
            ClaimVerification(
                claim_id=claim.id,
                accepted=not issues,
                issue_codes=tuple(issues),
            )
        )
    return tuple(verifications)
