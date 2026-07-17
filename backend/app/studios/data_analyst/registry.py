from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .domain import (
    AnalysisPlan,
    ColumnSemanticType,
    MethodCostClass,
    MethodDefinition,
    canonical_digest,
)


class UnregisteredMethodError(ValueError):
    """Raised when a plan references a method/version outside the registry."""


@dataclass(frozen=True, slots=True, init=False)
class MethodRegistry:
    version: str
    _methods: Mapping[tuple[str, str], MethodDefinition]

    def __init__(self, version: str, methods: Iterable[MethodDefinition]) -> None:
        indexed: dict[tuple[str, str], MethodDefinition] = {}
        for method in methods:
            key = (method.id, method.version)
            if key in indexed:
                raise ValueError(f"duplicate registered method: {method.id}@{method.version}")
            indexed[key] = method
        if not indexed:
            raise ValueError("method registry cannot be empty")
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "_methods", MappingProxyType(indexed))

    @property
    def methods(self) -> tuple[MethodDefinition, ...]:
        return tuple(self._methods[key] for key in sorted(self._methods))

    def get(self, method_id: str, version: str | None = None) -> MethodDefinition:
        if version is not None:
            try:
                return self._methods[(method_id, version)]
            except KeyError as exc:
                raise UnregisteredMethodError(
                    f"unregistered method: {method_id}@{version}"
                ) from exc

        matches = [
            method
            for (registered_id, _), method in self._methods.items()
            if registered_id == method_id
        ]
        if len(matches) != 1:
            raise UnregisteredMethodError(f"unregistered method: {method_id}")
        return matches[0]

    def validate_plan(self, plan: AnalysisPlan) -> AnalysisPlan:
        if plan.registry_version != self.version:
            raise UnregisteredMethodError(
                "plan registry version "
                f"{plan.registry_version} does not match {self.version}"
            )
        for step in plan.steps:
            method = self.get(step.method_id, step.method_version)
            missing = set(method.required_assumptions) - set(step.assumptions)
            if missing:
                raise ValueError(
                    f"step {step.id} omits required assumptions: {sorted(missing)}"
                )
        return plan

    @classmethod
    def initial(cls) -> "MethodRegistry":
        all_types = tuple(ColumnSemanticType)

        def definition(
            *,
            method_id: str,
            supported_types: tuple[ColumnSemanticType, ...],
            minimum_sample_size: int,
            assumptions: tuple[str, ...],
            parameters: dict[str, object],
            output_schema: str,
            limitations: tuple[str, ...],
        ) -> MethodDefinition:
            version = "1.0.0"
            return MethodDefinition(
                id=method_id,
                version=version,
                supported_semantic_types=supported_types,
                minimum_sample_size=minimum_sample_size,
                required_assumptions=assumptions,
                default_parameters=parameters,
                cost_class=MethodCostClass.LOW,
                output_schema=output_schema,
                limitations=limitations,
                implementation_digest=canonical_digest(
                    {
                        "executor": "data-analyst-core",
                        "method_id": method_id,
                        "method_version": version,
                    }
                ),
            )

        return cls(
            "1.0.0",
            (
                definition(
                    method_id="descriptive-summary",
                    supported_types=all_types,
                    minimum_sample_size=1,
                    assumptions=("valid-snapshot",),
                    parameters={"quantiles": [0.25, 0.5, 0.75]},
                    output_schema="Dataset counts and per-column descriptive statistics.",
                    limitations=("Description does not establish association or causality.",),
                ),
                definition(
                    method_id="categorical-frequency",
                    supported_types=(
                        ColumnSemanticType.CATEGORICAL,
                        ColumnSemanticType.BOOLEAN,
                    ),
                    minimum_sample_size=1,
                    assumptions=("categorical-input",),
                    parameters={"include_missing": True, "max_categories": 50},
                    output_schema="Stable value, count, and fraction rows by column.",
                    limitations=("Rare categories may be hidden by the category limit.",),
                ),
                definition(
                    method_id="pearson-correlation",
                    supported_types=(ColumnSemanticType.NUMERIC,),
                    minimum_sample_size=3,
                    assumptions=(
                        "minimum-paired-samples",
                        "non-constant",
                        "low-skew",
                    ),
                    parameters={"alternative": "two-sided"},
                    output_schema="Pearson coefficient, p-value, sample count, and diagnostics per pair.",
                    limitations=(
                        "Measures linear association only and cannot establish causality.",
                    ),
                ),
                definition(
                    method_id="spearman-correlation",
                    supported_types=(ColumnSemanticType.NUMERIC,),
                    minimum_sample_size=3,
                    assumptions=(
                        "minimum-paired-samples",
                        "non-constant",
                        "monotonic-relationship",
                    ),
                    parameters={"alternative": "two-sided"},
                    output_schema="Spearman coefficient, p-value, sample count, and diagnostics per pair.",
                    limitations=(
                        "Measures monotonic association only and cannot establish causality.",
                    ),
                ),
            ),
        )
