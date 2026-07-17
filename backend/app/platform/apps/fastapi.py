from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

from fastapi import APIRouter, FastAPI

from app.platform.apps.registry import AppRegistry, RegistryError


@dataclass(frozen=True)
class RouterSpec:
    module: str
    prefix: str
    tags: tuple[str, ...] = ()
    router_name: str = "router"


ROUTER_SPECS = {
    "chat": RouterSpec("app.api.routes.chat", "/api/v1"),
    "documents": RouterSpec("app.api.routes.documents", "/api/v1"),
    "history": RouterSpec("app.api.routes.history", "/api/v1/history", ("History",)),
    "aurasql": RouterSpec("app.api.routes.aurasql", "/api/v1", ("AuraSQL",)),
    "analysis": RouterSpec("app.api.routes.analysis", "/api/v1", ("Analysis",)),
    "presentation": RouterSpec(
        "app.api.routes.analysis",
        "/api/v1",
        ("Analysis",),
        router_name="presentation_router",
    ),
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

    resolved_routers: list[tuple[APIRouter, RouterSpec]] = []
    for router_id in sorted(router_ids):
        spec = ROUTER_SPECS[router_id]
        module = import_module(spec.module)
        router = getattr(module, spec.router_name, None)
        if not isinstance(router, APIRouter):
            raise RegistryError(
                f"application router {router_id!r} from {spec.module!r} "
                f"must expose an APIRouter as {spec.router_name!r}"
            )
        resolved_routers.append((router, spec))

    for router, spec in resolved_routers:
        app.include_router(router, prefix=spec.prefix, tags=list(spec.tags))
