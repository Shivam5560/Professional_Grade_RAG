from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .claims import SourceSpan


class RequirementPriority(StrEnum):
    REQUIRED = "required"
    PREFERRED = "preferred"


class RequirementCategory(StrEnum):
    SKILL = "skill"
    RESPONSIBILITY = "responsibility"
    OUTCOME = "outcome"
    EXPERIENCE = "experience"
    SENIORITY = "seniority"
    EDUCATION = "education"
    CERTIFICATION = "certification"
    LOCATION = "location"
    WORK_MODE = "work-mode"
    DOMAIN = "domain"


class RoleRequirement(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    priority: RequirementPriority
    category: RequirementCategory
    description: str = Field(min_length=1, max_length=1000)
    source_span: SourceSpan
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    weight: float = Field(gt=0.0, allow_inf_nan=False)

    @field_validator("description")
    @classmethod
    def reject_blank_description(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("requirement description must not be blank")
        return value
