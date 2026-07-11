### Task 3: Read-Only Application Catalog API

**Files:**

- Create: `backend/app/api/routes/apps.py`
- Create: `backend/app/platform/apps/fastapi.py`
- Modify: `backend/app/main.py:12-142`
- Create: `backend/tests/platform/test_apps_api.py`
- Create: `backend/tests/platform/test_app_routing.py`

**Interfaces:**

- Consumes: `get_app_registry()` from Task 2
- Produces: `GET /api/v1/apps` and `GET /api/v1/apps/{app_id}`
- Unknown or disabled applications return HTTP 404.
- Catalog responses are ordered by application identifier.
- Only router identifiers owned by enabled manifests are installed.
- Authentication, catalog, health, and notifications remain Core routers and are always installed.

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

```python
# backend/tests/platform/test_app_routing.py
from fastapi import FastAPI

from app.platform.apps.builtin import build_builtin_registry
from app.platform.apps.fastapi import install_enabled_application_routers


def test_disabled_application_routes_are_not_registered():
    app = FastAPI()
    registry = build_builtin_registry(enabled_ids={"knowledge-studio"})

    install_enabled_application_routers(app, registry)

    paths = {route.path for route in app.routes}
    assert any(path.startswith("/api/v1/chat") for path in paths)
    assert any(path.startswith("/api/v1/documents") for path in paths)
    assert not any(path.startswith("/api/v1/aurasql") for path in paths)
    assert not any(path.startswith("/api/v1/analysis") for path in paths)
    assert not any(path.startswith("/api/v1/nexus") for path in paths)


def test_shared_router_is_installed_once_for_multiple_owners():
    app = FastAPI()
    registry = build_builtin_registry(enabled_ids={"data-analyst", "presentation-studio"})

    install_enabled_application_routers(app, registry)

    analysis_paths = [route.path for route in app.routes if route.path.startswith("/api/v1/analysis")]
    assert analysis_paths
    assert len(analysis_paths) == len(set(analysis_paths))
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

- [ ] **Step 4: Implement lazy router registration for enabled applications**

```python
# backend/app/platform/apps/fastapi.py
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

from fastapi import FastAPI

from app.platform.apps.registry import AppRegistry, RegistryError


@dataclass(frozen=True)
class RouterSpec:
    module: str
    prefix: str
    tags: tuple[str, ...] = ()


ROUTER_SPECS = {
    "chat": RouterSpec("app.api.routes.chat", "/api/v1"),
    "documents": RouterSpec("app.api.routes.documents", "/api/v1"),
    "history": RouterSpec("app.api.routes.history", "/api/v1/history", ("History",)),
    "aurasql": RouterSpec("app.api.routes.aurasql", "/api/v1", ("AuraSQL",)),
    "analysis": RouterSpec("app.api.routes.analysis", "/api/v1", ("Analysis",)),
    "nexus-resume": RouterSpec("app.api.routes.nexus_resume", "/api/v1", ("Nexus Resume",)),
    "resume-generator": RouterSpec("app.api.routes.resumegen", "/api/v1", ("Resume Generator",)),
    "workflows": RouterSpec("app.api.routes.workflows", "/api/v1", ("Workflows",)),
}


def install_enabled_application_routers(app: FastAPI, registry: AppRegistry) -> None:
    router_ids = {
        router_id
        for manifest in registry.list_enabled()
        for router_id in manifest.backend_router_ids
    }
    unknown = router_ids - ROUTER_SPECS.keys()
    if unknown:
        raise RegistryError(f"application manifests reference unknown routers: {sorted(unknown)}")

    for router_id in sorted(router_ids):
        spec = ROUTER_SPECS[router_id]
        module = import_module(spec.module)
        app.include_router(module.router, prefix=spec.prefix, tags=list(spec.tags))
```

- [ ] **Step 5: Install Core and enabled application routers in the main application**

```python
# backend/app/main.py import block
from app.api.routes import apps, auth, health, notifications
from app.platform.apps import get_app_registry
from app.platform.apps.fastapi import install_enabled_application_routers
```

```python
# backend/app/main.py router block
app.include_router(apps.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
install_enabled_application_routers(app, get_app_registry())
```

- [ ] **Step 6: Run API, routing, and registry tests**

Run: `cd backend && pytest tests/platform/test_apps_api.py tests/platform/test_app_routing.py tests/platform/test_app_registry.py -v`

Expected: all tests PASS.

- [ ] **Step 7: Verify OpenAPI includes the catalog operations**

Run: `cd backend && python -c "from app.main import app; paths=app.openapi()['paths']; assert '/api/v1/apps' in paths; assert '/api/v1/apps/{app_id}' in paths; print('catalog paths verified')"`

Expected: `catalog paths verified`.

- [ ] **Step 8: Commit the API and route isolation**

```bash
git add backend/app/api/routes/apps.py backend/app/platform/apps/fastapi.py backend/app/main.py backend/tests/platform/test_apps_api.py backend/tests/platform/test_app_routing.py
git commit -m "feat(api): expose catalog and isolate application routes"
```

