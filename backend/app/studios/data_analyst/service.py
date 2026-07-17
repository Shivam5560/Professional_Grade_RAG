from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any

import pandas as pd

from app.platform.quality import (
    AIResult,
    EvidenceReference,
    QualityMetadata,
    ValidationIssue,
    ValidationStatus,
)
from app.platform.runtime import StudioRun, StudioRunState, transition_run

from .claims import synthesize_claims, verify_claims
from .domain import (
    AnalysisOutput,
    ComputationRecord,
    DataAnalystRunResult,
    FindingClaim,
    canonical_digest,
)
from .execution import execute_analysis_plan
from .planning import build_analysis_plan, parse_intent
from .profiling import fingerprint_dataframe, profile_dataframe
from .registry import MethodRegistry

ClaimSynthesizer = Callable[
    [tuple[ComputationRecord, ...]],
    tuple[FindingClaim, ...],
]


class DataAnalystSpecialist:
    """Deterministic evidence-first Data Analyst core orchestrator."""

    def __init__(
        self,
        *,
        registry: MethodRegistry | None = None,
        claim_synthesizer: ClaimSynthesizer = synthesize_claims,
    ) -> None:
        self._registry = registry or MethodRegistry.initial()
        self._claim_synthesizer = claim_synthesizer

    def _quality(
        self,
        *,
        trace_id: str,
        claims: tuple[FindingClaim, ...],
        computations: tuple[ComputationRecord, ...],
        validation: ValidationIssue,
        abstention_reason: str | None = None,
    ) -> QualityMetadata:
        method_validity = min(
            (
                float(claim.confidence_components["method-validity"])
                for claim in claims
            ),
            default=0.0,
        )
        warnings = tuple(
            dict.fromkeys(
                warning
                for computation in computations
                for warning in computation.warnings
            )
        )
        return QualityMetadata(
            algorithm_versions={
                "claim-verifier": "1.0.0",
                "data-profiler": "1.0.0",
                "method-registry": self._registry.version,
                **{
                    method.id: method.version for method in self._registry.methods
                },
            },
            model_versions={},
            prompt_versions={},
            confidence_components={
                "evidence-resolution": 1.0 if validation.status is ValidationStatus.PASS else 0.0,
                "method-validity": method_validity,
            },
            validations=(validation,),
            warnings=warnings,
            abstention_reason=abstention_reason,
            latency_ms=0.0,
            input_tokens=0,
            output_tokens=0,
            estimated_cost_usd=0.0,
            trace_id=trace_id,
        )

    def analyze(
        self,
        frame: pd.DataFrame,
        question: str,
        *,
        owner_id: int,
        run_id: str,
        idempotency_key: str,
        now: datetime,
        business_context: Mapping[str, Any] | None = None,
    ) -> DataAnalystRunResult:
        input_fingerprint = fingerprint_dataframe(frame)
        queued = StudioRun(
            id=run_id,
            owner_id=owner_id,
            studio_id="data-analyst",
            operation="analyze",
            idempotency_key=idempotency_key,
            input_fingerprint=input_fingerprint,
            created_at=now,
            updated_at=now,
        )
        running = transition_run(
            queued,
            StudioRunState.RUNNING,
            now=now,
            current_step="profile",
            progress=0.1,
        )

        profile = profile_dataframe(frame)
        intent = parse_intent(question, business_context)
        plan = build_analysis_plan(profile, intent, self._registry)
        computations = execute_analysis_plan(
            frame,
            profile,
            plan,
            run_id=run_id,
            registry=self._registry,
        )
        claims = self._claim_synthesizer(computations)
        verifications = verify_claims(claims, computations)
        trace_id = f"trace-{canonical_digest({'run_id': run_id, 'plan_id': plan.id})[:24]}"

        rejected = tuple(
            verification for verification in verifications if not verification.accepted
        )
        if rejected:
            failure_code = "claim-verification-failed"
            failed = transition_run(
                running,
                StudioRunState.FAILED,
                now=now,
                current_step="verify-claims",
                progress=0.9,
                failure_code=failure_code,
            )
            validation = ValidationIssue(
                code="claim-resolution",
                message="At least one synthesized claim lacks exact computation support.",
                status=ValidationStatus.ERROR,
                critical=True,
            )
            abstention_reason = (
                "One or more synthesized claims did not resolve to computation evidence."
            )
            return DataAnalystRunResult(
                run_history=(queued, running, failed),
                profile=profile,
                plan=plan,
                computations=computations,
                result=AIResult[AnalysisOutput](
                    output=None,
                    evidence=(),
                    quality=self._quality(
                        trace_id=trace_id,
                        claims=(),
                        computations=computations,
                        validation=validation,
                        abstention_reason=abstention_reason,
                    ),
                ),
            )

        references: list[EvidenceReference] = []
        seen_references: set[tuple[str, str]] = set()
        for claim in claims:
            for link in claim.evidence_links:
                key = (link.evidence_id, link.value_path)
                if key in seen_references:
                    continue
                seen_references.add(key)
                references.append(
                    EvidenceReference(
                        source_id=link.evidence_id,
                        locator=link.value_path,
                        relevance=1.0,
                    )
                )

        validation = ValidationIssue(
            code="claim-resolution",
            message="Every published claim resolves to an exact computation value.",
            status=ValidationStatus.PASS,
            critical=True,
        )
        succeeded = transition_run(
            running,
            StudioRunState.SUCCEEDED,
            now=now,
            current_step="verified-claims",
            progress=1.0,
        )
        return DataAnalystRunResult(
            run_history=(queued, running, succeeded),
            profile=profile,
            plan=plan,
            computations=computations,
            result=AIResult[AnalysisOutput](
                output=AnalysisOutput(claims=claims),
                evidence=tuple(references),
                quality=self._quality(
                    trace_id=trace_id,
                    claims=claims,
                    computations=computations,
                    validation=validation,
                ),
            ),
        )
