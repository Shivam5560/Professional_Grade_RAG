from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.platform.quality import QualityMetadata
from app.platform.runtime import StudioRun
from app.studios.data_analyst.domain import AnalysisPlan, ComputationRecord, DatasetProfile, FindingClaim
from app.studios.data_analyst.domain.json_values import freeze_json, thaw_json


class ApiContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DatasetUploadResponse(ApiContract):
    snapshot_id: str
    profile: DatasetProfile


class StartAnalysisRequest(ApiContract):
    snapshot_id: str = Field(min_length=1)
    question: str = Field(min_length=3, max_length=2000)
    business_context: Mapping[str, Any] = Field(default_factory=dict)

    @field_validator("business_context")
    @classmethod
    def freeze_context(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return freeze_json(value)

    @field_serializer("business_context")
    def serialize_context(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return thaw_json(value)


class AnalysisRunResponse(ApiContract):
    run: StudioRun
    run_history: tuple[StudioRun, ...]
    profile: DatasetProfile | None = None
    plan: AnalysisPlan | None = None
    limitations: tuple[str, ...] = ()
    quality: QualityMetadata | None = None
    abstention_reason: str | None = None


class ComputationListResponse(ApiContract):
    computations: tuple[ComputationRecord, ...]


class ClaimListResponse(ApiContract):
    claims: tuple[FindingClaim, ...]
