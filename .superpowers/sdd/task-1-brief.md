### Task 1: Immutable Application Manifest Contract

**Files:**

- Create: `backend/app/platform/__init__.py`
- Create: `backend/app/platform/apps/__init__.py`
- Create: `backend/app/platform/apps/contracts.py`
- Create: `backend/tests/platform/__init__.py`
- Create: `backend/tests/platform/test_app_manifest.py`
- Create: `backend/tests/platform/factories.py`

**Interfaces:**

- Produces: `Capability`, `AppDependency`, `DemoScenario`, and `AppManifest`
- `AppManifest.id: str` is lowercase kebab-case.
- `AppManifest.version: str` is semantic version `MAJOR.MINOR.PATCH`.
- `AppManifest.required_capabilities` and `optional_capabilities` contain `Capability` values.
- `AppManifest.backend_router_ids` names bootstrap router adapters without importing them.
- `AppManifest.model_dump(mode="json")` is the API serialization source.

- [ ] **Step 1: Write the failing manifest tests**

```python
# backend/tests/platform/factories.py
from app.platform.apps.contracts import AppManifest, Capability, DemoScenario


def build_manifest(**overrides):
    values = {
        "id": "knowledge-studio",
        "version": "1.0.0",
        "name": "Knowledge Studio",
        "summary": "Evidence-backed document intelligence.",
        "category": "knowledge",
        "icon": "book-open",
        "frontend_route": "/chat",
        "backend_route_prefixes": ["/api/v1/chat", "/api/v1/documents"],
        "backend_router_ids": ["chat", "documents", "history"],
        "required_capabilities": [Capability.AUTH, Capability.RETRIEVAL],
        "optional_capabilities": [Capability.WORKFLOWS],
        "required_permissions": ["documents:read"],
        "required_env_keys": ["LLM_PROVIDER"],
        "dependencies": [],
        "demo_scenarios": [
            DemoScenario(
                id="compare-policies",
                title="Compare two policies",
                description="Find differences and cite both documents.",
                starter_prompt="Compare the leave policies and cite each difference.",
            )
        ],
        "health_check_id": "knowledge",
        "packaging_paths": ["backend/app/core", "frontend/app/chat"],
    }
    values.update(overrides)
    return AppManifest(**values)
```

```python
# backend/tests/platform/test_app_manifest.py
import pytest
from pydantic import ValidationError

from app.platform.apps.contracts import (
    AppDependency,
    Capability,
)
from tests.platform.factories import build_manifest


def test_manifest_is_immutable_and_json_serializable():
    manifest = build_manifest()

    assert manifest.model_dump(mode="json")["required_capabilities"] == ["auth", "retrieval"]
    with pytest.raises(ValidationError):
        manifest.name = "Changed"


@pytest.mark.parametrize("app_id", ["Knowledge", "knowledge_studio", "knowledge studio", "-knowledge"])
def test_manifest_rejects_non_kebab_case_identifier(app_id):
    with pytest.raises(ValidationError):
        build_manifest(id=app_id)


@pytest.mark.parametrize("version", ["1", "1.0", "v1.0.0", "1.0.0-beta"])
def test_manifest_rejects_non_release_semver(version):
    with pytest.raises(ValidationError):
        build_manifest(version=version)


def test_dependency_rejects_self_reference():
    with pytest.raises(ValidationError):
        build_manifest(
            dependencies=[AppDependency(app_id="knowledge-studio", minimum_version="1.0.0")]
        )


def test_required_and_optional_capabilities_cannot_overlap():
    with pytest.raises(ValidationError):
        build_manifest(optional_capabilities=[Capability.RETRIEVAL])
```

- [ ] **Step 2: Run the test and confirm the contract is missing**

Run: `cd backend && pytest tests/platform/test_app_manifest.py -v`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'app.platform'`.

- [ ] **Step 3: Implement the manifest contract**

```python
# backend/app/platform/apps/contracts.py
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
```

```python
# backend/app/platform/apps/__init__.py
from app.platform.apps.contracts import AppDependency, AppManifest, Capability, DemoScenario

__all__ = ["AppDependency", "AppManifest", "Capability", "DemoScenario"]
```

```python
# backend/app/platform/__init__.py
"""Reusable NexusMind platform contracts and services."""
```

```python
# backend/tests/platform/__init__.py
"""Platform contract tests."""
```

- [ ] **Step 4: Run the manifest tests**

Run: `cd backend && pytest tests/platform/test_app_manifest.py -v`

Expected: 11 tests PASS.

- [ ] **Step 5: Commit the contract**

```bash
git add backend/app/platform backend/tests/platform
git commit -m "feat(platform): add immutable application manifests"
```

