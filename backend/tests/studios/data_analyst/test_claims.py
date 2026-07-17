from __future__ import annotations

import pandas as pd
import pytest

from app.studios.data_analyst.claims import (
    resolve_evidence_value,
    synthesize_claims,
    verify_claims,
)
from app.studios.data_analyst.domain import FindingLanguageClass
from app.studios.data_analyst.execution import execute_analysis_plan
from app.studios.data_analyst.planning import build_analysis_plan, parse_intent
from app.studios.data_analyst.profiling import profile_dataframe


def computation_records(frame: pd.DataFrame | None = None):
    active_frame = frame if frame is not None else pd.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 4.0, 5.0],
            "y": [2.0, 4.0, 6.0, 8.0, 10.0],
            "region": ["north", "south", "north", "south", "north"],
        }
    )
    profile = profile_dataframe(active_frame)
    plan = build_analysis_plan(
        profile,
        parse_intent("How are x and y related by region?"),
    )
    return execute_analysis_plan(
        active_frame,
        profile,
        plan,
        run_id="run-1",
    )


def correlation_claim_and_records():
    records = computation_records()
    claim = next(
        item
        for item in synthesize_claims(records)
        if item.language_class is FindingLanguageClass.ASSOCIATION
    )
    return claim, records


def test_synthesized_claims_resolve_to_exact_computation_values() -> None:
    records = computation_records()
    claims = synthesize_claims(records)

    checks = verify_claims(claims, records)

    assert claims
    assert all(check.accepted for check in checks)
    assert {claim.language_class for claim in claims} >= {
        FindingLanguageClass.OBSERVATION,
        FindingLanguageClass.ASSOCIATION,
    }
    for claim in claims:
        assert len(claim.evidence_links) == 1
        link = claim.evidence_links[0]
        record = next(
            item for item in records if item.evidence.id == link.evidence_id
        )
        assert resolve_evidence_value(record, link.value_path) == claim.value


def test_verifier_rejects_unknown_evidence_invalid_path_and_value_mismatch() -> None:
    claim, records = correlation_claim_and_records()
    unknown_link = claim.evidence_links[0].model_copy(
        update={"evidence_id": "evidence-missing"}
    )
    bad_path_link = claim.evidence_links[0].model_copy(
        update={"value_path": "output.pairs.99.coefficient"}
    )
    unknown = claim.model_copy(update={"evidence_links": (unknown_link,)})
    bad_path = claim.model_copy(update={"evidence_links": (bad_path_link,)})
    mismatched = claim.model_copy(update={"value": 0.12345})

    assert verify_claims((unknown,), records)[0].issue_codes == (
        "unknown-evidence",
    )
    assert verify_claims((bad_path,), records)[0].issue_codes == (
        "invalid-evidence-path",
    )
    assert verify_claims((mismatched,), records)[0].issue_codes == (
        "unsupported-value",
    )


@pytest.mark.parametrize(
    "predicate",
    [
        "causes growth in",
        "drives changes in",
        "leads to higher",
        "has an effect on",
        "impacts",
        "results in higher",
        "is responsible for",
        "determines",
        "influences",
        "has a causal relationship with",
    ],
)
def test_verifier_rejects_causal_language_for_association_evidence(
    predicate: str,
) -> None:
    claim, records = correlation_claim_and_records()
    causal = claim.model_copy(update={"predicate": predicate})

    result = verify_claims((causal,), records)[0]

    assert result.accepted is False
    assert "causal-language" in result.issue_codes


def test_verifier_requires_association_language_class_for_correlation() -> None:
    claim, records = correlation_claim_and_records()
    observation = claim.model_copy(
        update={"language_class": FindingLanguageClass.OBSERVATION}
    )

    result = verify_claims((observation,), records)[0]

    assert result.accepted is False
    assert result.issue_codes == ("invalid-language-class",)


def test_synthesizer_abstains_from_failed_correlation_value() -> None:
    records = computation_records(
        pd.DataFrame({"x": [1, 1, 1, 1], "y": [1, 2, 3, 4]})
    )

    claims = synthesize_claims(records)

    assert claims
    assert not any(
        claim.language_class is FindingLanguageClass.ASSOCIATION
        for claim in claims
    )
    assert all(check.accepted for check in verify_claims(claims, records))


def test_claim_paths_support_arbitrary_valid_column_names() -> None:
    frame = pd.DataFrame(
        {
            "gross.margin / usd": [1.0, 2.0, 3.0, 4.0],
            "net.revenue": [2.0, 4.0, 6.0, 8.0],
        }
    )
    records = computation_records(frame)

    claims = synthesize_claims(records)

    assert claims
    assert all(check.accepted for check in verify_claims(claims, records))
    for claim in claims:
        link = claim.evidence_links[0]
        record = next(item for item in records if item.evidence.id == link.evidence_id)
        assert resolve_evidence_value(record, link.value_path) == claim.value
