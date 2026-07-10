# NexusMind Platform Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add validated application manifests, a backend application catalog, a common quality-result contract, and a tested manifest-driven frontend catalog without moving existing application implementations.

**Architecture:** Introduce a small `app.platform` package that describes and registers applications independently of their implementation modules. Expose the registry through a read-only API, consume it through a feature-scoped frontend client, and replace hard-coded top-level application navigation with catalog data. Existing routes remain unchanged during this compatibility-first phase.

**Tech Stack:** Python 3.11, FastAPI, Pydantic 2, pytest, Next.js 14, React 18, TypeScript 5, Tailwind CSS, Radix UI, Vitest, Testing Library, jest-dom, axe-core, Playwright

## Global Constraints

- No AI feature may claim perfect accuracy.
- Application identifiers are lowercase kebab-case and immutable after release.
- Application versions use `MAJOR.MINOR.PATCH` semantic version strings.
- Existing public routes remain functional.
- Disabled applications do not appear in the catalog or frontend navigation.
- Core contracts do not import application implementation modules.
- Frontend API code for the catalog lives outside the existing monolithic `frontend/lib/api.ts`.
- Frontend screens include loading, empty, partial, error, retry, responsive, keyboard, and screen-reader behavior.
- WCAG 2.2 AA is required.
- All new backend behavior is developed test-first with pytest.
- All new frontend behavior is developed test-first with Vitest and Testing Library.
- One Playwright smoke journey covers the catalog.

---

## File Structure

### Backend

- `backend/app/platform/__init__.py` — public platform package
- `backend/app/platform/apps/__init__.py` — public application-registry exports
- `backend/app/platform/apps/contracts.py` — immutable manifest and dependency contracts
- `backend/app/platform/apps/registry.py` — registration, enablement, dependency validation, and catalog lookup
- `backend/app/platform/apps/builtin.py` — manifests for the existing NexusMind applications
- `backend/app/platform/quality/__init__.py` — public quality-contract exports
- `backend/app/platform/quality/contracts.py` — evidence, validation, and common result envelope
- `backend/app/api/routes/apps.py` — read-only application catalog API
- `backend/tests/platform/test_app_manifest.py` — manifest validation tests
- `backend/tests/platform/factories.py` — shared platform-test manifest factory
- `backend/tests/platform/test_app_registry.py` — registry behavior tests
- `backend/tests/platform/test_apps_api.py` — API contract tests
- `backend/tests/platform/test_quality_contracts.py` — quality serialization tests
- `backend/requirements-dev.txt` — reproducible backend development and test dependencies

### Frontend

- `frontend/lib/apps/types.ts` — catalog API types
- `frontend/lib/apps/client.ts` — feature-scoped catalog client
- `frontend/lib/apps/useAppCatalog.ts` — catalog loading and retry state
- `frontend/components/platform/CapabilityBadge.tsx` — accessible capability label
- `frontend/components/platform/AppCard.tsx` — application summary card
- `frontend/components/platform/AppCatalog.tsx` — loading, error, empty, and populated catalog states
- `frontend/components/platform/AppNavigation.tsx` — manifest-driven desktop and mobile navigation
- `frontend/app/apps/page.tsx` — catalog route
- `frontend/app/apps/[appId]/page.tsx` — application overview and demo scenarios
- `frontend/test/setup.ts` — DOM and accessibility matcher setup
- `frontend/vitest.config.ts` — Vitest configuration
- `frontend/playwright.config.ts` — browser-test configuration
- `frontend/components/platform/__tests__/AppCatalog.test.tsx` — catalog component tests
- `frontend/components/platform/__tests__/AppNavigation.test.tsx` — navigation tests
- `frontend/app/apps/__tests__/page.test.tsx` — route-level behavior
- `frontend/e2e/app-catalog.spec.ts` — browser smoke journey

### Integration

- `backend/app/main.py` — install catalog router
- `frontend/components/layout/Header.tsx` — delegate application links to `AppNavigation`
- `frontend/package.json` — add test scripts and dependencies
- `Jenkinsfile` — enforce backend, frontend, MCP, and build gates

---

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

### Task 2: Validated Registry and Built-In Application Manifests

**Files:**

- Create: `backend/app/platform/apps/registry.py`
- Create: `backend/app/platform/apps/builtin.py`
- Modify: `backend/app/config.py:1-25`
- Modify: `backend/app/platform/apps/__init__.py`
- Create: `backend/tests/platform/test_app_registry.py`

**Interfaces:**

- Consumes: `AppManifest` from Task 1
- Produces: `AppRegistry.register()`, `AppRegistry.finalize()`, `AppRegistry.list_enabled()`, `AppRegistry.get()`, and `get_app_registry()`
- `finalize()` is mandatory before reads and validates missing dependencies and minimum versions.
- The registry is the backend catalog source of truth.

- [ ] **Step 1: Write registry tests**

```python
# backend/tests/platform/test_app_registry.py
import pytest

from app.platform.apps.builtin import build_builtin_registry
from app.platform.apps.contracts import AppDependency
from app.platform.apps.registry import AppRegistry, RegistryError
from tests.platform.factories import build_manifest


def test_registry_rejects_duplicate_application_id():
    registry = AppRegistry()
    registry.register(build_manifest())

    with pytest.raises(RegistryError, match="duplicate application id"):
        registry.register(build_manifest())


def test_registry_rejects_missing_dependency():
    registry = AppRegistry()
    registry.register(
        build_manifest(
            id="research-intelligence",
            dependencies=[AppDependency(app_id="knowledge-studio", minimum_version="1.0.0")],
        )
    )

    with pytest.raises(RegistryError, match="missing dependency knowledge-studio"):
        registry.finalize()


def test_registry_rejects_incompatible_dependency_version():
    registry = AppRegistry()
    registry.register(build_manifest(version="1.0.0"))
    registry.register(
        build_manifest(
            id="research-intelligence",
            frontend_route="/research",
            dependencies=[AppDependency(app_id="knowledge-studio", minimum_version="2.0.0")],
        )
    )

    with pytest.raises(RegistryError, match="requires knowledge-studio>=2.0.0"):
        registry.finalize()


def test_disabled_apps_are_not_returned():
    registry = build_builtin_registry(enabled_ids={"knowledge-studio", "aurasql"})

    assert [manifest.id for manifest in registry.list_enabled()] == ["aurasql", "knowledge-studio"]
    assert registry.get("career-studio") is None


def test_registry_rejects_unknown_enabled_application():
    with pytest.raises(RegistryError, match="unknown enabled application ids"):
        build_builtin_registry(enabled_ids={"not-installed"})


def test_builtin_registry_contains_six_flagships():
    registry = build_builtin_registry()

    assert {manifest.id for manifest in registry.list_enabled()} == {
        "aurasql",
        "career-studio",
        "data-analyst",
        "developer-studio",
        "knowledge-studio",
        "presentation-studio",
    }
```

- [ ] **Step 2: Run the registry tests and confirm missing implementations**

Run: `cd backend && pytest tests/platform/test_app_registry.py -v`

Expected: FAIL during collection because `app.platform.apps.registry` and `builtin` do not exist.

- [ ] **Step 3: Implement the registry**

```python
# backend/app/platform/apps/registry.py
from __future__ import annotations

from app.platform.apps.contracts import AppManifest


class RegistryError(ValueError):
    pass


def _version_tuple(version: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in version.split("."))


class AppRegistry:
    def __init__(self, enabled_ids: set[str] | None = None) -> None:
        self._manifests: dict[str, AppManifest] = {}
        self._enabled_ids = enabled_ids
        self._finalized = False

    def register(self, manifest: AppManifest) -> None:
        if self._finalized:
            raise RegistryError("cannot register applications after finalization")
        if manifest.id in self._manifests:
            raise RegistryError(f"duplicate application id: {manifest.id}")
        self._manifests[manifest.id] = manifest

    def finalize(self) -> None:
        if self._enabled_ids is not None:
            unknown = self._enabled_ids - self._manifests.keys()
            if unknown:
                raise RegistryError(f"unknown enabled application ids: {sorted(unknown)}")
        for manifest in self._manifests.values():
            for dependency in manifest.dependencies:
                installed = self._manifests.get(dependency.app_id)
                if installed is None:
                    raise RegistryError(f"{manifest.id} has missing dependency {dependency.app_id}")
                if _version_tuple(installed.version) < _version_tuple(dependency.minimum_version):
                    raise RegistryError(
                        f"{manifest.id} requires {dependency.app_id}>={dependency.minimum_version}; "
                        f"installed {installed.version}"
                    )
        self._finalized = True

    def _require_finalized(self) -> None:
        if not self._finalized:
            raise RegistryError("registry must be finalized before reading")

    def list_enabled(self) -> list[AppManifest]:
        self._require_finalized()
        manifests = self._manifests.values()
        if self._enabled_ids is not None:
            manifests = [manifest for manifest in manifests if manifest.id in self._enabled_ids]
        return sorted(manifests, key=lambda manifest: manifest.id)

    def get(self, app_id: str) -> AppManifest | None:
        self._require_finalized()
        if self._enabled_ids is not None and app_id not in self._enabled_ids:
            return None
        return self._manifests.get(app_id)
```

- [ ] **Step 4: Add manifests for the existing applications**

```python
# backend/app/platform/apps/builtin.py
from app.config import settings
from app.platform.apps.contracts import AppManifest, Capability, DemoScenario
from app.platform.apps.registry import AppRegistry


def _scenario(identifier: str, title: str, description: str, prompt: str) -> DemoScenario:
    return DemoScenario(id=identifier, title=title, description=description, starter_prompt=prompt)


BUILTIN_MANIFESTS = (
    AppManifest(
        id="knowledge-studio", version="1.0.0", name="Knowledge Studio",
        summary="Evidence-backed chat, document comparison, and knowledge retrieval.",
        category="knowledge", icon="book-open", frontend_route="/chat",
        backend_route_prefixes=("/api/v1/chat", "/api/v1/documents"),
        required_capabilities=(Capability.AUTH, Capability.RETRIEVAL),
        optional_capabilities=(Capability.WORKFLOWS,),
        required_permissions=("documents:read",), required_env_keys=("LLM_PROVIDER",),
        demo_scenarios=(_scenario("compare-documents", "Compare documents", "Compare two documents and cite the supporting passages.", "Compare the selected documents and cite every material difference."),),
        health_check_id="knowledge", packaging_paths=("backend/app/core", "backend/app/api/routes/chat.py", "backend/app/api/routes/documents.py", "frontend/app/chat"),
    ),
    AppManifest(
        id="aurasql", version="1.0.0", name="AuraSQL",
        summary="Safe natural-language analytics across connected relational databases.",
        category="data", icon="database", frontend_route="/aurasql",
        backend_route_prefixes=("/api/v1/aurasql",),
        required_capabilities=(Capability.AUTH, Capability.SQL),
        required_permissions=("database:query",), required_env_keys=("LLM_PROVIDER",),
        demo_scenarios=(_scenario("revenue-analysis", "Revenue analysis", "Generate and explain a read-only revenue query.", "Show monthly revenue by region and explain the SQL."),),
        health_check_id="aurasql", packaging_paths=("backend/app/api/routes/aurasql.py", "backend/app/services/aurasql_db.py", "frontend/app/aurasql"),
    ),
    AppManifest(
        id="data-analyst", version="1.0.0", name="Data Analyst Studio",
        summary="Reproducible statistical analysis, insight prioritization, and reporting.",
        category="data", icon="chart-no-axes-combined", frontend_route="/analysis",
        backend_route_prefixes=("/api/v1/analysis",),
        required_capabilities=(Capability.AUTH, Capability.WORKFLOWS, Capability.ARTIFACTS),
        required_permissions=("analysis:run",), required_env_keys=("LLM_PROVIDER",),
        demo_scenarios=(_scenario("sales-diagnostics", "Sales diagnostics", "Profile a sales dataset and identify defensible drivers.", "Analyze the strongest drivers of sales and distinguish evidence from hypotheses."),),
        health_check_id="analysis", packaging_paths=("backend/app/analysis", "backend/app/api/routes/analysis.py", "frontend/app/analysis"),
    ),
    AppManifest(
        id="presentation-studio", version="1.0.0", name="Presentation Studio",
        summary="Narrative-first, data-backed presentation planning and PPTX generation.",
        category="content", icon="presentation", frontend_route="/analysis",
        backend_route_prefixes=("/api/v1/analysis/reports",),
        required_capabilities=(Capability.AUTH, Capability.ARTIFACTS, Capability.PRESENTATIONS),
        required_permissions=("presentation:generate",), required_env_keys=("LLM_PROVIDER",),
        demo_scenarios=(_scenario("executive-deck", "Executive deck", "Turn an analysis into an evidence-backed executive presentation.", "Create an executive deck with one decision per slide."),),
        health_check_id="presentations", packaging_paths=("backend/app/services/analysis/slide_generator.py", "frontend/app/analysis/[jobId]/report"),
    ),
    AppManifest(
        id="career-studio", version="1.0.0", name="Career Studio",
        summary="Truth-preserving resume analysis, tailoring, generation, and review.",
        category="career", icon="briefcase-business", frontend_route="/nexus",
        backend_route_prefixes=("/api/v1/nexus", "/api/v1/workflows/auto-tailor"),
        required_capabilities=(Capability.AUTH, Capability.WORKFLOWS, Capability.CAREER),
        required_permissions=("career:write",), required_env_keys=("LLM_PROVIDER",),
        demo_scenarios=(_scenario("tailor-resume", "Tailor a resume", "Match verified experience to a target role without inventing claims.", "Tailor this verified profile to the selected job description."),),
        health_check_id="career", packaging_paths=("backend/app/services/nexus_ai", "backend/app/analysis/workflows/auto_tailor_workflow.py", "frontend/app/nexus", "frontend/app/workflows/auto-tailor"),
    ),
    AppManifest(
        id="developer-studio", version="1.0.0", name="Developer and MCP Studio",
        summary="Inspect APIs, MCP tools, health, traces, and integration capabilities.",
        category="developer", icon="blocks", frontend_route="/developer",
        backend_route_prefixes=("/api/v1/health",),
        required_capabilities=(Capability.AUTH, Capability.MCP),
        required_permissions=("developer:read",), required_env_keys=(),
        demo_scenarios=(_scenario("inspect-tools", "Inspect tools", "Review the available MCP tools and platform health.", "List the enabled developer tools and their health."),),
        health_check_id="developer", packaging_paths=("mcp-server", "frontend/app/developer"),
    ),
)


def build_builtin_registry(enabled_ids: set[str] | None = None) -> AppRegistry:
    registry = AppRegistry(enabled_ids=enabled_ids)
    for manifest in BUILTIN_MANIFESTS:
        registry.register(manifest)
    registry.finalize()
    return registry


_registry = build_builtin_registry(set(settings.enabled_app_ids) or None)


def get_app_registry() -> AppRegistry:
    return _registry
```

- [ ] **Step 5: Add deployment-level application enablement configuration**

Add the following field under `Settings` API configuration:

```python
# backend/app/config.py
enabled_app_ids: List[str] = Field(default_factory=list, alias="NEXUS_ENABLED_APPS")
```

An empty list enables every built-in application for the showcase. A deployment supplies a JSON array such as `NEXUS_ENABLED_APPS='["knowledge-studio","developer-studio"]'` to enable a subset. Unknown identifiers fail registry finalization.

- [ ] **Step 6: Export the registry interfaces**

```python
# backend/app/platform/apps/__init__.py
from app.platform.apps.builtin import get_app_registry
from app.platform.apps.contracts import AppDependency, AppManifest, Capability, DemoScenario
from app.platform.apps.registry import AppRegistry, RegistryError

__all__ = [
    "AppDependency", "AppManifest", "AppRegistry", "Capability", "DemoScenario",
    "RegistryError", "get_app_registry",
]
```

- [ ] **Step 7: Run the registry and manifest tests**

Run: `cd backend && pytest tests/platform/test_app_manifest.py tests/platform/test_app_registry.py -v`

Expected: all tests PASS.

- [ ] **Step 8: Commit the registry**

```bash
git add backend/app/platform/apps backend/app/config.py backend/tests/platform/factories.py backend/tests/platform/test_app_registry.py
git commit -m "feat(platform): register built-in NexusMind applications"
```

### Task 3: Read-Only Application Catalog API

**Files:**

- Create: `backend/app/api/routes/apps.py`
- Modify: `backend/app/main.py:12-142`
- Create: `backend/tests/platform/test_apps_api.py`

**Interfaces:**

- Consumes: `get_app_registry()` from Task 2
- Produces: `GET /api/v1/apps` and `GET /api/v1/apps/{app_id}`
- Unknown or disabled applications return HTTP 404.
- Catalog responses are ordered by application identifier.

- [ ] **Step 1: Write API tests**

```python
# backend/tests/platform/test_apps_api.py
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.apps import router


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


def test_list_apps_returns_serialized_catalog():
    response = build_client().get("/api/v1/apps")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["id"] == "aurasql"
    assert {item["id"] for item in payload} >= {"knowledge-studio", "career-studio"}
    assert payload[0]["version"].count(".") == 2


def test_get_app_returns_demo_scenarios():
    response = build_client().get("/api/v1/apps/knowledge-studio")

    assert response.status_code == 200
    assert response.json()["demo_scenarios"][0]["starter_prompt"]


def test_get_unknown_app_returns_404():
    response = build_client().get("/api/v1/apps/not-installed")

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"
```

- [ ] **Step 2: Run the API tests and confirm the route is missing**

Run: `cd backend && pytest tests/platform/test_apps_api.py -v`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'app.api.routes.apps'`.

- [ ] **Step 3: Implement the catalog router**

```python
# backend/app/api/routes/apps.py
from fastapi import APIRouter, HTTPException, status

from app.platform.apps import AppManifest, get_app_registry

router = APIRouter(tags=["Applications"])


@router.get("/apps", response_model=list[AppManifest])
def list_applications() -> list[AppManifest]:
    return get_app_registry().list_enabled()


@router.get("/apps/{app_id}", response_model=AppManifest)
def get_application(app_id: str) -> AppManifest:
    manifest = get_app_registry().get(app_id)
    if manifest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return manifest
```

- [ ] **Step 4: Install the router in the main application**

```python
# backend/app/main.py import block
from app.api.routes import analysis, apps, aurasql, auth, chat, documents, health, history
from app.api.routes import nexus_resume, notifications, resumegen, workflows
```

```python
# backend/app/main.py router block
app.include_router(apps.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
```

- [ ] **Step 5: Run API and registry tests**

Run: `cd backend && pytest tests/platform/test_apps_api.py tests/platform/test_app_registry.py -v`

Expected: all tests PASS.

- [ ] **Step 6: Verify OpenAPI includes the catalog operations**

Run: `cd backend && python -c "from app.main import app; paths=app.openapi()['paths']; assert '/api/v1/apps' in paths; assert '/api/v1/apps/{app_id}' in paths; print('catalog paths verified')"`

Expected: `catalog paths verified`.

- [ ] **Step 7: Commit the API**

```bash
git add backend/app/api/routes/apps.py backend/app/main.py backend/tests/platform/test_apps_api.py
git commit -m "feat(api): expose application catalog"
```

### Task 4: Common Evidence and Quality Result Contract

**Files:**

- Create: `backend/app/platform/quality/__init__.py`
- Create: `backend/app/platform/quality/contracts.py`
- Create: `backend/tests/platform/test_quality_contracts.py`

**Interfaces:**

- Produces: `EvidenceReference`, `ValidationIssue`, `ValidationStatus`, `QualityMetadata`, and generic `AIResult[T]`
- Critical validation errors require an abstention reason.
- Confidence components are named bounded values rather than one unexplained scalar.

- [ ] **Step 1: Write quality-contract tests**

```python
# backend/tests/platform/test_quality_contracts.py
import pytest
from pydantic import ValidationError

from app.platform.quality.contracts import (
    AIResult,
    EvidenceReference,
    QualityMetadata,
    ValidationIssue,
    ValidationStatus,
)


def metadata(**overrides):
    values = {
        "algorithm_versions": {"retrieval": "rrf-v1"},
        "model_versions": {"generator": "provider/model"},
        "prompt_versions": {"answer": "1.0.0"},
        "confidence_components": {"evidence_coverage": 0.92},
        "validations": [],
        "warnings": [],
        "abstention_reason": None,
        "latency_ms": 120.0,
        "input_tokens": 100,
        "output_tokens": 20,
        "estimated_cost_usd": 0.001,
        "trace_id": "trace-1",
        "evaluation_run_id": None,
    }
    values.update(overrides)
    return QualityMetadata(**values)


def test_result_serializes_evidence_and_quality_versions():
    result = AIResult[str](
        output="Supported answer",
        evidence=[EvidenceReference(source_id="doc-1", locator="page:2", snippet="Evidence")],
        quality=metadata(),
    )

    payload = result.model_dump(mode="json")
    assert payload["quality"]["algorithm_versions"]["retrieval"] == "rrf-v1"
    assert payload["evidence"][0]["source_id"] == "doc-1"


def test_critical_validation_requires_abstention():
    issue = ValidationIssue(
        code="unsupported-claim",
        message="The claim has no evidence.",
        status=ValidationStatus.ERROR,
        critical=True,
    )

    with pytest.raises(ValidationError, match="critical validation errors require abstention_reason"):
        metadata(validations=[issue])


def test_confidence_components_are_bounded():
    with pytest.raises(ValidationError):
        metadata(confidence_components={"evidence_coverage": 1.01})
```

- [ ] **Step 2: Run the tests and confirm the contract is missing**

Run: `cd backend && pytest tests/platform/test_quality_contracts.py -v`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'app.platform.quality'`.

- [ ] **Step 3: Implement the quality contracts**

```python
# backend/app/platform/quality/contracts.py
from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

OutputT = TypeVar("OutputT")


class ValidationStatus(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"


class EvidenceReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    snippet: str | None = Field(default=None, max_length=1000)
    relevance: float | None = Field(default=None, ge=0.0, le=1.0)


class ValidationIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    message: str = Field(min_length=3, max_length=500)
    status: ValidationStatus
    critical: bool = False


class QualityMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    algorithm_versions: dict[str, str] = Field(default_factory=dict)
    model_versions: dict[str, str] = Field(default_factory=dict)
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    confidence_components: dict[str, float] = Field(default_factory=dict)
    validations: tuple[ValidationIssue, ...] = ()
    warnings: tuple[str, ...] = ()
    abstention_reason: str | None = None
    latency_ms: float = Field(ge=0.0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)
    trace_id: str
    evaluation_run_id: str | None = None

    @model_validator(mode="after")
    def validate_quality_state(self) -> "QualityMetadata":
        invalid = [name for name, value in self.confidence_components.items() if not 0.0 <= value <= 1.0]
        if invalid:
            raise ValueError(f"confidence components must be between 0 and 1: {sorted(invalid)}")
        has_critical_error = any(
            issue.critical and issue.status == ValidationStatus.ERROR for issue in self.validations
        )
        if has_critical_error and not self.abstention_reason:
            raise ValueError("critical validation errors require abstention_reason")
        return self


class AIResult(BaseModel, Generic[OutputT]):
    output: OutputT | None
    evidence: tuple[EvidenceReference, ...] = ()
    quality: QualityMetadata
```

```python
# backend/app/platform/quality/__init__.py
from app.platform.quality.contracts import (
    AIResult,
    EvidenceReference,
    QualityMetadata,
    ValidationIssue,
    ValidationStatus,
)

__all__ = [
    "AIResult", "EvidenceReference", "QualityMetadata", "ValidationIssue", "ValidationStatus",
]
```

- [ ] **Step 4: Run the quality-contract tests**

Run: `cd backend && pytest tests/platform/test_quality_contracts.py -v`

Expected: 3 tests PASS.

- [ ] **Step 5: Commit the quality envelope**

```bash
git add backend/app/platform/quality backend/tests/platform/test_quality_contracts.py
git commit -m "feat(platform): add evidence and quality result contracts"
```

### Task 5: Frontend Test and Accessibility Foundation

**Files:**

- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/test/setup.ts`
- Create: `frontend/test/setup.test.tsx`
- Create: `frontend/playwright.config.ts`

**Interfaces:**

- Produces: `npm run test`, `npm run test:watch`, `npm run test:a11y`, and `npm run test:e2e`
- `@/` path aliases resolve in Vitest.
- DOM tests include jest-dom matchers.
- Playwright uses the existing Next.js development command.

- [ ] **Step 1: Add test scripts and pinned development dependencies**

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:a11y": "vitest run --testNamePattern accessibility",
    "test:e2e": "playwright test"
  },
  "devDependencies": {
    "@playwright/test": "1.49.1",
    "@testing-library/jest-dom": "6.6.3",
    "@testing-library/react": "16.1.0",
    "@testing-library/user-event": "14.5.2",
    "@types/node": "^20.9.0",
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@types/react-plotly.js": "^2.6.4",
    "@types/three": "^0.183.1",
    "@types/uuid": "^9.0.7",
    "@vitejs/plugin-react": "4.3.4",
    "autoprefixer": "^10.4.16",
    "axe-core": "4.10.2",
    "eslint": "^8.54.0",
    "eslint-config-next": "^14.2.5",
    "jsdom": "25.0.1",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.0",
    "typescript": "^5.3.2",
    "vitest": "2.1.8"
  }
}
```

Apply only the `scripts` and `devDependencies` keys above; preserve the existing `dependencies` key exactly. Run `npm install` to update `frontend/package-lock.json`.

- [ ] **Step 2: Add Vitest configuration and DOM setup**

```typescript
// frontend/vitest.config.ts
import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, ".") } },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./test/setup.ts"],
    include: ["**/*.test.{ts,tsx}"],
    restoreMocks: true,
  },
});
```

```typescript
// frontend/test/setup.ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 3: Add Playwright configuration**

```typescript
// frontend/playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  retries: 1,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-chromium", use: { ...devices["Pixel 7"] } },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: true,
  },
});
```

- [ ] **Step 4: Add a test proving the DOM harness is operational**

```tsx
// frontend/test/setup.test.tsx
import { render, screen } from "@testing-library/react";

test("provides DOM and jest-dom matchers", () => {
  render(<button type="button">Ready</button>);
  expect(screen.getByRole("button", { name: "Ready" })).toBeEnabled();
});
```

- [ ] **Step 5: Run the harness test**

Run: `cd frontend && npm run test -- test/setup.test.tsx`

Expected: 1 test PASS.

- [ ] **Step 6: Commit the test foundation**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/test frontend/playwright.config.ts
git commit -m "test(frontend): add component accessibility and browser foundations"
```

### Task 6: Typed Frontend Catalog Client and State Hook

**Files:**

- Create: `frontend/lib/apps/types.ts`
- Create: `frontend/lib/apps/client.ts`
- Create: `frontend/lib/apps/useAppCatalog.ts`
- Create: `frontend/lib/apps/__tests__/client.test.ts`
- Create: `frontend/lib/apps/__tests__/useAppCatalog.test.tsx`

**Interfaces:**

- Consumes: `GET /api/v1/apps` from Task 3
- Produces: `AppManifest`, `Capability`, `listApps()`, `getApp()`, and `useAppCatalog()`
- The hook exposes discriminated states: loading, success, empty, and error.

- [ ] **Step 1: Write client and hook tests**

```typescript
// frontend/lib/apps/__tests__/client.test.ts
import { listApps } from "../client";

test("loads the catalog from the versioned API", async () => {
  const fetcher = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => [{ id: "knowledge-studio", name: "Knowledge Studio" }],
  });

  const result = await listApps(fetcher as typeof fetch);

  expect(fetcher).toHaveBeenCalledWith(
    expect.stringMatching(/\/api\/v1\/apps$/),
    expect.objectContaining({ headers: { Accept: "application/json" } }),
  );
  expect(result[0].id).toBe("knowledge-studio");
});


test("throws a useful error for an unavailable catalog", async () => {
  const fetcher = vi.fn().mockResolvedValue({ ok: false, status: 503 });

  await expect(listApps(fetcher as typeof fetch)).rejects.toThrow("Application catalog unavailable (503)");
});
```

```tsx
// frontend/lib/apps/__tests__/useAppCatalog.test.tsx
import { act, renderHook, waitFor } from "@testing-library/react";

import { useAppCatalog } from "../useAppCatalog";

vi.mock("../client", () => ({ listApps: vi.fn() }));
import { listApps } from "../client";

const mockedListApps = vi.mocked(listApps);

test("moves from loading to success", async () => {
  mockedListApps.mockResolvedValue([{ id: "knowledge-studio", name: "Knowledge Studio" }] as never);
  const { result } = renderHook(() => useAppCatalog());

  expect(result.current.status).toBe("loading");
  await waitFor(() => expect(result.current.status).toBe("success"));
});


test("retry reloads an errored catalog", async () => {
  mockedListApps.mockRejectedValueOnce(new Error("offline"));
  mockedListApps.mockResolvedValueOnce([]);
  const { result } = renderHook(() => useAppCatalog());
  await waitFor(() => expect(result.current.status).toBe("error"));

  await act(async () => result.current.retry());

  await waitFor(() => expect(result.current.status).toBe("empty"));
  expect(mockedListApps).toHaveBeenCalledTimes(2);
});
```

- [ ] **Step 2: Run the tests and confirm feature modules are missing**

Run: `cd frontend && npm run test -- lib/apps/__tests__`

Expected: FAIL because `types.ts`, `client.ts`, and `useAppCatalog.ts` do not exist.

- [ ] **Step 3: Implement the frontend contracts**

```typescript
// frontend/lib/apps/types.ts
export type Capability =
  | "auth" | "retrieval" | "sql" | "workflows" | "artifacts"
  | "evaluation" | "presentations" | "career" | "mcp";

export interface DemoScenario {
  id: string;
  title: string;
  description: string;
  starter_prompt: string;
}

export interface AppDependency {
  app_id: string;
  minimum_version: string;
}

export interface AppManifest {
  id: string;
  version: string;
  name: string;
  summary: string;
  category: string;
  icon: string;
  frontend_route: string;
  backend_route_prefixes: string[];
  required_capabilities: Capability[];
  optional_capabilities: Capability[];
  required_permissions: string[];
  required_env_keys: string[];
  dependencies: AppDependency[];
  demo_scenarios: DemoScenario[];
  health_check_id: string;
  packaging_paths: string[];
}
```

- [ ] **Step 4: Implement the feature-scoped client**

```typescript
// frontend/lib/apps/client.ts
import type { AppManifest } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Application catalog unavailable (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function listApps(fetcher: typeof fetch = fetch): Promise<AppManifest[]> {
  const response = await fetcher(`${API_BASE}/api/v1/apps`, {
    headers: { Accept: "application/json" },
  });
  return readJson<AppManifest[]>(response);
}

export async function getApp(appId: string, fetcher: typeof fetch = fetch): Promise<AppManifest> {
  const response = await fetcher(`${API_BASE}/api/v1/apps/${encodeURIComponent(appId)}`, {
    headers: { Accept: "application/json" },
  });
  return readJson<AppManifest>(response);
}
```

- [ ] **Step 5: Implement explicit catalog states**

```typescript
// frontend/lib/apps/useAppCatalog.ts
"use client";

import { useCallback, useEffect, useState } from "react";

import { listApps } from "./client";
import type { AppManifest } from "./types";

type CatalogState =
  | { status: "loading"; apps: []; error: null; retry: () => Promise<void> }
  | { status: "empty"; apps: []; error: null; retry: () => Promise<void> }
  | { status: "success"; apps: AppManifest[]; error: null; retry: () => Promise<void> }
  | { status: "error"; apps: []; error: Error; retry: () => Promise<void> };

export function useAppCatalog(): CatalogState {
  const [status, setStatus] = useState<CatalogState["status"]>("loading");
  const [apps, setApps] = useState<AppManifest[]>([]);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    setStatus("loading");
    setError(null);
    try {
      const catalog = await listApps();
      setApps(catalog);
      setStatus(catalog.length === 0 ? "empty" : "success");
    } catch (reason) {
      setApps([]);
      setError(reason instanceof Error ? reason : new Error("Unable to load applications"));
      setStatus("error");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return { status, apps, error, retry: load } as CatalogState;
}
```

- [ ] **Step 6: Run the feature tests**

Run: `cd frontend && npm run test -- lib/apps/__tests__`

Expected: 4 tests PASS.

- [ ] **Step 7: Commit the client**

```bash
git add frontend/lib/apps
git commit -m "feat(frontend): add typed application catalog client"
```

### Task 7: Accessible Application Catalog and Overview Pages

**Files:**

- Create: `frontend/components/platform/CapabilityBadge.tsx`
- Create: `frontend/components/platform/AppCard.tsx`
- Create: `frontend/components/platform/AppCatalog.tsx`
- Create: `frontend/components/platform/__tests__/AppCatalog.test.tsx`
- Create: `frontend/app/apps/page.tsx`
- Create: `frontend/app/apps/[appId]/page.tsx`
- Create: `frontend/app/apps/__tests__/page.test.tsx`

**Interfaces:**

- Consumes: `useAppCatalog()` and `getApp()` from Task 6
- Produces: `/apps` and `/apps/{appId}`
- Application cards expose one primary link named `Open {application name}`.
- The overview page links to the existing `frontend_route` and lists demo scenarios.

- [ ] **Step 1: Write catalog state and accessibility tests**

```tsx
// frontend/components/platform/__tests__/AppCatalog.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppCatalog } from "../AppCatalog";

vi.mock("@/lib/apps/useAppCatalog", () => ({ useAppCatalog: vi.fn() }));
import { useAppCatalog } from "@/lib/apps/useAppCatalog";

const mockedCatalog = vi.mocked(useAppCatalog);
const retry = vi.fn();

test("renders loading state with an accessible status", () => {
  mockedCatalog.mockReturnValue({ status: "loading", apps: [], error: null, retry });
  render(<AppCatalog />);
  expect(screen.getByRole("status", { name: /loading applications/i })).toBeInTheDocument();
});

test("renders retryable error state", async () => {
  mockedCatalog.mockReturnValue({ status: "error", apps: [], error: new Error("offline"), retry });
  render(<AppCatalog />);
  await userEvent.click(screen.getByRole("button", { name: /retry/i }));
  expect(retry).toHaveBeenCalledOnce();
});

test("renders app links and capability labels", () => {
  mockedCatalog.mockReturnValue({
    status: "success",
    error: null,
    retry,
    apps: [{
      id: "knowledge-studio", version: "1.0.0", name: "Knowledge Studio",
      summary: "Evidence-backed document intelligence.", category: "knowledge", icon: "book-open",
      frontend_route: "/chat", backend_route_prefixes: [], required_capabilities: ["auth", "retrieval"],
      optional_capabilities: [], required_permissions: [], required_env_keys: [], dependencies: [],
      demo_scenarios: [], health_check_id: "knowledge", packaging_paths: [],
    }],
  });
  render(<AppCatalog />);
  expect(screen.getByRole("link", { name: "Open Knowledge Studio" })).toHaveAttribute("href", "/apps/knowledge-studio");
  expect(screen.getByText("retrieval")).toBeInTheDocument();
});

test("catalog populated state has no automatic accessibility violations", async () => {
  const axe = (await import("axe-core")).default;
  mockedCatalog.mockReturnValue({
    status: "success", error: null, retry,
    apps: [{
      id: "knowledge-studio", version: "1.0.0", name: "Knowledge Studio",
      summary: "Evidence-backed document intelligence.", category: "knowledge", icon: "book-open",
      frontend_route: "/chat", backend_route_prefixes: [], required_capabilities: ["auth", "retrieval"],
      optional_capabilities: [], required_permissions: [], required_env_keys: [], dependencies: [],
      demo_scenarios: [], health_check_id: "knowledge", packaging_paths: [],
    }],
  });
  const { container } = render(<AppCatalog />);
  const result = await axe.run(container);
  expect(result.violations).toEqual([]);
});
```

```tsx
// frontend/app/apps/__tests__/page.test.tsx
import { render, screen } from "@testing-library/react";
import AppsPage from "../page";

vi.mock("@/components/platform/AppCatalog", () => ({
  AppCatalog: () => <div>Application catalog test double</div>,
}));

test("renders the application catalog route", () => {
  render(<AppsPage />);
  expect(screen.getByRole("heading", { name: /application showcase/i })).toBeInTheDocument();
  expect(screen.getByText("Application catalog test double")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test and confirm components are missing**

Run: `cd frontend && npm run test -- components/platform/__tests__/AppCatalog.test.tsx`

Expected: FAIL because `AppCatalog.tsx` does not exist.

- [ ] **Step 3: Implement capability badges and cards**

```tsx
// frontend/components/platform/CapabilityBadge.tsx
import type { Capability } from "@/lib/apps/types";

export function CapabilityBadge({ capability }: { capability: Capability }) {
  return (
    <span className="rounded-full border border-border bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
      {capability}
    </span>
  );
}
```

```tsx
// frontend/components/platform/AppCard.tsx
import Link from "next/link";

import { CapabilityBadge } from "./CapabilityBadge";
import type { AppManifest } from "@/lib/apps/types";

export function AppCard({ app }: { app: AppManifest }) {
  return (
    <article className="flex h-full flex-col rounded-2xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{app.category}</p>
          <h2 className="mt-2 text-xl font-semibold text-foreground">{app.name}</h2>
        </div>
        <span className="text-xs text-muted-foreground">v{app.version}</span>
      </div>
      <p className="mt-3 flex-1 text-sm leading-6 text-muted-foreground">{app.summary}</p>
      <div className="mt-5 flex flex-wrap gap-2" aria-label={`${app.name} capabilities`}>
        {app.required_capabilities.map((capability) => (
          <CapabilityBadge key={capability} capability={capability} />
        ))}
      </div>
      <Link className="mt-6 inline-flex font-semibold text-primary underline-offset-4 hover:underline" href={`/apps/${app.id}`}>
        Open {app.name}
      </Link>
    </article>
  );
}
```

- [ ] **Step 4: Implement all catalog states**

```tsx
// frontend/components/platform/AppCatalog.tsx
"use client";

import { AppCard } from "./AppCard";
import { Button } from "@/components/ui/button";
import { useAppCatalog } from "@/lib/apps/useAppCatalog";

export function AppCatalog() {
  const catalog = useAppCatalog();

  if (catalog.status === "loading") {
    return <div role="status" aria-label="Loading applications" className="py-16 text-muted-foreground">Loading applications…</div>;
  }
  if (catalog.status === "error") {
    return (
      <section role="alert" className="rounded-2xl border border-destructive/40 p-6">
        <h2 className="font-semibold">Application catalog unavailable</h2>
        <p className="mt-2 text-sm text-muted-foreground">{catalog.error.message}</p>
        <Button className="mt-4" onClick={() => void catalog.retry()}>Retry</Button>
      </section>
    );
  }
  if (catalog.status === "empty") {
    return (
      <section className="rounded-2xl border border-dashed border-border p-10 text-center">
        <h2 className="font-semibold">No applications are enabled</h2>
        <p className="mt-2 text-sm text-muted-foreground">Enable an application manifest to add it to this deployment.</p>
      </section>
    );
  }
  return (
    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
      {catalog.apps.map((app) => <AppCard key={app.id} app={app} />)}
    </div>
  );
}
```

- [ ] **Step 5: Implement the catalog route**

```tsx
// frontend/app/apps/page.tsx
import { AppCatalog } from "@/components/platform/AppCatalog";

export default function AppsPage() {
  return (
    <main className="mx-auto min-h-screen max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">NexusMind</p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight text-foreground">Application showcase</h1>
      <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">
        Production-grade AI reference applications built on reusable Nexus Core capabilities.
      </p>
      <section className="mt-10" aria-label="Enabled applications"><AppCatalog /></section>
    </main>
  );
}
```

- [ ] **Step 6: Implement the application overview route**

```tsx
// frontend/app/apps/[appId]/page.tsx
import Link from "next/link";
import { notFound } from "next/navigation";

import { getApp } from "@/lib/apps/client";
import { CapabilityBadge } from "@/components/platform/CapabilityBadge";
import type { AppManifest } from "@/lib/apps/types";

export default async function AppOverviewPage({ params }: { params: { appId: string } }) {
  let app: AppManifest;
  try {
    app = await getApp(params.appId);
  } catch {
    notFound();
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Link href="/apps" className="text-sm text-muted-foreground hover:text-foreground">← All applications</Link>
      <h1 className="mt-6 text-4xl font-semibold tracking-tight">{app.name}</h1>
      <p className="mt-4 max-w-3xl text-lg leading-8 text-muted-foreground">{app.summary}</p>
      <div className="mt-6 flex flex-wrap gap-2">{app.required_capabilities.map((item) => <CapabilityBadge key={item} capability={item} />)}</div>
      <Link href={app.frontend_route} className="mt-8 inline-flex rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground">Launch {app.name}</Link>
      <section className="mt-12" aria-labelledby="demo-scenarios">
        <h2 id="demo-scenarios" className="text-2xl font-semibold">Guided scenarios</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {app.demo_scenarios.map((scenario) => (
            <article key={scenario.id} className="rounded-xl border border-border p-5">
              <h3 className="font-semibold">{scenario.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{scenario.description}</p>
              <pre className="mt-4 whitespace-pre-wrap rounded-lg bg-muted p-3 text-xs">{scenario.starter_prompt}</pre>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
```

- [ ] **Step 7: Run component and route tests**

Run: `cd frontend && npm run test -- components/platform app/apps`

Expected: all catalog and route tests PASS.

- [ ] **Step 8: Commit the catalog experience**

```bash
git add frontend/components/platform frontend/app/apps
git commit -m "feat(frontend): add accessible application showcase"
```

### Task 8: Manifest-Driven Header Navigation

**Files:**

- Create: `frontend/components/platform/AppNavigation.tsx`
- Create: `frontend/components/platform/__tests__/AppNavigation.test.tsx`
- Modify: `frontend/components/layout/Header.tsx:1-160`

**Interfaces:**

- Consumes: `useAppCatalog()` from Task 6
- Produces: desktop and mobile links for enabled applications
- The dashboard and application-catalog links remain platform links.
- Catalog failure retains platform links and exposes no stale application links.

- [ ] **Step 1: Write enabled-app and failure-state tests**

```tsx
// frontend/components/platform/__tests__/AppNavigation.test.tsx
import { render, screen } from "@testing-library/react";

import { AppNavigation } from "../AppNavigation";

vi.mock("@/lib/apps/useAppCatalog", () => ({ useAppCatalog: vi.fn() }));
import { useAppCatalog } from "@/lib/apps/useAppCatalog";
const mockedCatalog = vi.mocked(useAppCatalog);

test("renders only enabled application links", () => {
  mockedCatalog.mockReturnValue({
    status: "success", error: null, retry: vi.fn(),
    apps: [{ id: "knowledge-studio", name: "Knowledge Studio", frontend_route: "/chat" }] as never,
  });
  render(<AppNavigation pathname="/chat" />);

  expect(screen.getByRole("link", { name: "Knowledge Studio" })).toHaveAttribute("href", "/chat");
  expect(screen.queryByRole("link", { name: "AuraSQL" })).not.toBeInTheDocument();
});


test("catalog failure keeps platform navigation usable", () => {
  mockedCatalog.mockReturnValue({ status: "error", apps: [], error: new Error("offline"), retry: vi.fn() });
  render(<AppNavigation pathname="/apps" />);

  expect(screen.getByRole("link", { name: "Applications" })).toHaveAttribute("href", "/apps");
  expect(screen.getByText(/application navigation unavailable/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test and confirm navigation is missing**

Run: `cd frontend && npm run test -- components/platform/__tests__/AppNavigation.test.tsx`

Expected: FAIL because `AppNavigation.tsx` does not exist.

- [ ] **Step 3: Implement manifest-driven navigation**

```tsx
// frontend/components/platform/AppNavigation.tsx
"use client";

import Link from "next/link";

import { cn } from "@/lib/utils";
import { useAppCatalog } from "@/lib/apps/useAppCatalog";

export function AppNavigation({ pathname, mobile = false }: { pathname: string; mobile?: boolean }) {
  const catalog = useAppCatalog();
  const baseClass = mobile ? "block rounded-md px-3 py-2 text-sm" : "rounded-md px-3 py-2 text-sm";
  const linkClass = (active: boolean) => cn(baseClass, active ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground");

  return (
    <nav aria-label="Primary applications" className={mobile ? "space-y-1" : "flex items-center gap-1"}>
      <Link className={linkClass(pathname === "/")} href="/">Dashboard</Link>
      <Link className={linkClass(pathname.startsWith("/apps"))} href="/apps">Applications</Link>
      {catalog.status === "success" && catalog.apps.map((app) => (
        <Link key={app.id} className={linkClass(pathname.startsWith(app.frontend_route))} href={app.frontend_route}>
          {app.name}
        </Link>
      ))}
      {catalog.status === "error" ? <span className="sr-only">Application navigation unavailable</span> : null}
    </nav>
  );
}
```

- [ ] **Step 4: Replace hard-coded application arrays in `Header`**

Add:

```tsx
import { AppNavigation } from "@/components/platform/AppNavigation";
```

Delete the `mainNavLinks` array. Replace the desktop map with:

```tsx
<div className="ml-6 hidden whitespace-nowrap lg:block">
  <AppNavigation pathname={pathname ?? "/"} />
</div>
```

Replace the mobile map with:

```tsx
<div className="absolute right-0 top-full z-50 mt-2 w-64 rounded-lg border border-border bg-background p-2 shadow-xl">
  <AppNavigation pathname={pathname ?? "/"} mobile />
</div>
```

Retain the existing mobile menu open/close button. Add an effect that closes `mobileNavOpen` when `pathname` changes:

```tsx
useEffect(() => { setMobileNavOpen(false); }, [pathname]);
```

- [ ] **Step 5: Run navigation and catalog tests**

Run: `cd frontend && npm run test -- components/platform`

Expected: all tests PASS.

- [ ] **Step 6: Run lint and production build**

Run: `cd frontend && npm run lint && npm run build`

Expected: both commands exit 0.

- [ ] **Step 7: Commit navigation**

```bash
git add frontend/components/platform/AppNavigation.tsx frontend/components/platform/__tests__/AppNavigation.test.tsx frontend/components/layout/Header.tsx
git commit -m "feat(frontend): drive application navigation from manifests"
```

### Task 9: CI Gates and Complete Foundation Verification

**Files:**

- Create: `backend/requirements-dev.txt`
- Modify: `Jenkinsfile`
- Create: `frontend/e2e/app-catalog.spec.ts`

**Interfaces:**

- Consumes: backend tests, frontend tests/build, Playwright catalog journey, and MCP TypeScript build
- Produces: a CI pipeline that cannot push to the repository and fails on any quality gate

- [ ] **Step 1: Pin backend development dependencies**

```text
# backend/requirements-dev.txt
-r requirements.txt
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
```

- [ ] **Step 2: Make the browser journey deterministic with a catalog contract fixture**

```typescript
// frontend/e2e/app-catalog.spec.ts
import { expect, test } from "@playwright/test";

test("visitor can browse the application showcase", async ({ page }) => {
  await page.route("**/api/v1/apps", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([{
        id: "knowledge-studio", version: "1.0.0", name: "Knowledge Studio",
        summary: "Evidence-backed document intelligence.", category: "knowledge", icon: "book-open",
        frontend_route: "/chat", backend_route_prefixes: [], required_capabilities: ["auth", "retrieval"],
        optional_capabilities: [], required_permissions: [], required_env_keys: [], dependencies: [],
        demo_scenarios: [], health_check_id: "knowledge", packaging_paths: [],
      }]),
    });
  });
  await page.goto("/apps");
  await expect(page.getByRole("heading", { name: /application showcase/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /open knowledge studio/i })).toBeVisible();
});
```

- [ ] **Step 3: Replace the Jenkins stages with read-only quality gates**

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Backend Tests') {
            steps {
                dir('backend') {
                    sh 'python3 -m venv venv'
                    sh '. venv/bin/activate && pip install -r requirements-dev.txt'
                    sh '. venv/bin/activate && pytest tests/platform -v --cov=app.platform --cov-fail-under=90'
                    sh '. venv/bin/activate && pytest -q'
                }
            }
        }
        stage('Frontend Quality') {
            steps {
                dir('frontend') {
                    sh 'npm ci'
                    sh 'npm run lint'
                    sh 'npm run test'
                    sh 'npm run build'
                }
            }
        }
        stage('MCP Build') {
            steps {
                dir('mcp-server') {
                    sh 'npm ci'
                    sh 'npm run build'
                }
            }
        }
        stage('Catalog Browser Smoke') {
            steps {
                dir('frontend') {
                    sh 'npx playwright install --with-deps chromium'
                    sh 'npm run test:e2e -- --project=chromium'
                }
            }
        }
    }

    post {
        always { cleanWs() }
    }
}
```

- [ ] **Step 4: Run the full backend suite**

Run: `cd backend && pytest -q`

Expected: all tests PASS.

- [ ] **Step 5: Run platform coverage gate**

Run: `cd backend && pytest tests/platform -v --cov=app.platform --cov-fail-under=90`

Expected: tests PASS and platform coverage is at least 90%.

- [ ] **Step 6: Run frontend unit, lint, and build gates**

Run: `cd frontend && npm run lint && npm run test && npm run build`

Expected: all commands exit 0.

- [ ] **Step 7: Run the catalog browser journey at desktop and mobile sizes**

Run: `cd frontend && npm run test:e2e`

Expected: Chromium and mobile Chromium catalog journeys PASS.

- [ ] **Step 8: Run the MCP build**

Run: `cd mcp-server && npm ci && npm run build`

Expected: TypeScript compilation exits 0.

- [ ] **Step 9: Verify disabled-application behavior manually through the registry test harness**

Run:

```bash
cd backend && python -c "from app.platform.apps.builtin import build_builtin_registry; r=build_builtin_registry({'knowledge-studio'}); assert [a.id for a in r.list_enabled()]==['knowledge-studio']; print('enablement verified')"
```

Expected: `enablement verified`.

- [ ] **Step 10: Commit CI and development dependencies**

```bash
git add backend/requirements-dev.txt frontend/e2e/app-catalog.spec.ts Jenkinsfile
git commit -m "ci: enforce platform backend frontend and MCP gates"
```

## Foundation Completion Checklist

- [ ] Six existing applications have immutable validated manifests.
- [ ] Disabled applications are absent from backend catalog and frontend navigation.
- [ ] Catalog APIs appear in OpenAPI.
- [ ] Common evidence and quality metadata serialize without application imports.
- [ ] The catalog has loading, error, retry, empty, populated, desktop, and mobile behavior.
- [ ] Frontend component, accessibility, and browser test tools run in CI.
- [ ] The Jenkins pipeline contains no write-back or push stage.
- [ ] Existing backend routes and frontend application routes still build and pass tests.
- [ ] Platform backend coverage is at least 90%.
