from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RELEASE_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class Capability(StrEnum):
    AUTH = "auth"
    RETRIEVAL = "retrieval"
    SQL = "sql"
    WORKFLOWS = "workflows"
    ARTIFACTS = "artifacts"
    EVALUATION = "evaluation"
    PRESENTATIONS = "presentations"
    CAREER = "career"
    MCP = "mcp"


class AppDependency(BaseModel):
    model_config = ConfigDict(frozen=True)

    app_id: str = Field(pattern=KEBAB_CASE.pattern)
    minimum_version: str = Field(pattern=RELEASE_SEMVER.pattern)


class DemoScenario(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=KEBAB_CASE.pattern)
    title: str = Field(min_length=3, max_length=80)
    description: str = Field(min_length=10, max_length=240)
    starter_prompt: str = Field(min_length=3, max_length=1000)


class AppManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=KEBAB_CASE.pattern)
    version: str = Field(pattern=RELEASE_SEMVER.pattern)
    name: str = Field(min_length=3, max_length=80)
    summary: str = Field(min_length=10, max_length=240)
    category: str = Field(pattern=KEBAB_CASE.pattern)
    icon: str = Field(pattern=KEBAB_CASE.pattern)
    frontend_route: str = Field(pattern=r"^/[a-z0-9/_\-\[\]]*$")
    backend_route_prefixes: tuple[str, ...] = ()
    backend_router_ids: tuple[str, ...] = ()
    required_capabilities: tuple[Capability, ...] = ()
    optional_capabilities: tuple[Capability, ...] = ()
    required_permissions: tuple[str, ...] = ()
    required_env_keys: tuple[str, ...] = ()
    dependencies: tuple[AppDependency, ...] = ()
    demo_scenarios: tuple[DemoScenario, ...] = ()
    health_check_id: str = Field(pattern=KEBAB_CASE.pattern)
    packaging_paths: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_relationships(self) -> "AppManifest":
        overlap = set(self.required_capabilities) & set(self.optional_capabilities)
        if overlap:
            raise ValueError(f"capabilities cannot be both required and optional: {sorted(overlap)}")
        if any(dependency.app_id == self.id for dependency in self.dependencies):
            raise ValueError("an application cannot depend on itself")
        if len(set(self.backend_route_prefixes)) != len(self.backend_route_prefixes):
            raise ValueError("backend route prefixes must be unique within a manifest")
        if len(set(self.backend_router_ids)) != len(self.backend_router_ids):
            raise ValueError("backend router identifiers must be unique within a manifest")
        if len({scenario.id for scenario in self.demo_scenarios}) != len(self.demo_scenarios):
            raise ValueError("demo scenario identifiers must be unique within a manifest")
        return self
