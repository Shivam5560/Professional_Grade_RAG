from fastapi import APIRouter, FastAPI

from app.platform.apps.builtin import build_builtin_registry
from app.platform.apps.fastapi import ROUTER_SPECS, install_enabled_application_routers


def _manifest(app_id: str):
    manifest = build_builtin_registry().get(app_id)
    assert manifest is not None
    return manifest


def test_data_analyst_manifest_uses_only_the_v2_studio() -> None:
    manifest = _manifest("data-analyst")

    assert manifest.version == "2.0.0"
    assert manifest.frontend_route == "/analysis"
    assert manifest.backend_route_prefixes == ("/api/v2/data-analyst",)
    assert manifest.backend_router_ids == ("data-analyst-v2",)
    assert manifest.required_env_keys == ()
    assert "backend/app/studios/data_analyst" in manifest.packaging_paths
    assert "backend/app/api/routes/analysis.py" not in manifest.packaging_paths


def test_career_manifest_uses_only_the_v2_studio() -> None:
    manifest = _manifest("career-studio")

    assert manifest.version == "2.0.0"
    assert manifest.frontend_route == "/career"
    assert manifest.backend_route_prefixes == ("/api/v2/career",)
    assert manifest.backend_router_ids == ("career-v2",)
    assert manifest.required_env_keys == ()
    assert "backend/app/studios/career" in manifest.packaging_paths
    assert "backend/app/services/nexus_ai" not in manifest.packaging_paths


def test_specialist_router_registry_exposes_v2_and_detaches_legacy_ids() -> None:
    assert ROUTER_SPECS["data-analyst-v2"].module == "app.studios.data_analyst.api.router"
    assert ROUTER_SPECS["career-v2"].module == "app.studios.career.api.router"
    assert ROUTER_SPECS["data-analyst-v2"].prefix == ""
    assert ROUTER_SPECS["career-v2"].prefix == ""

    assert "analysis" not in ROUTER_SPECS
    assert "nexus-resume" not in ROUTER_SPECS
    assert "resume-generator" not in ROUTER_SPECS
    assert "workflows" not in ROUTER_SPECS


def test_both_v2_modules_expose_installable_routers() -> None:
    from app.studios.career.api.router import router as career_router
    from app.studios.data_analyst.api.router import router as data_router

    assert isinstance(career_router, APIRouter)
    assert isinstance(data_router, APIRouter)

    career_paths = {route.path for route in career_router.routes}
    data_paths = {route.path for route in data_router.routes}
    assert "/api/v2/career/sources" in career_paths
    assert "/api/v2/career/drafts" in career_paths
    assert "/api/v2/data-analyst/datasets" in data_paths
    assert "/api/v2/data-analyst/runs" in data_paths


def test_enabled_specialist_studios_install_only_the_v2_routes() -> None:
    app = FastAPI()
    registry = build_builtin_registry({"data-analyst", "career-studio"})

    install_enabled_application_routers(app, registry)

    paths = {route.path for route in app.routes}
    assert "/api/v2/data-analyst/datasets" in paths
    assert "/api/v2/career/sources" in paths
    assert not any(path.startswith("/api/v1/analysis") for path in paths)
    assert not any(path.startswith("/api/v1/nexus") for path in paths)
    assert not any(path.startswith("/api/v1/workflows/auto-tailor") for path in paths)
