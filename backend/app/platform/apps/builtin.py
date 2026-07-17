from app.config import settings
from app.platform.apps.contracts import AppDependency, AppManifest, Capability, DemoScenario
from app.platform.apps.registry import AppRegistry


def _scenario(identifier: str, title: str, description: str, prompt: str) -> DemoScenario:
    return DemoScenario(id=identifier, title=title, description=description, starter_prompt=prompt)


BUILTIN_MANIFESTS = (
    AppManifest(
        id="knowledge-studio", version="1.0.0", name="Knowledge Studio",
        summary="Evidence-backed chat, document comparison, and knowledge retrieval.",
        category="knowledge", icon="book-open", frontend_route="/chat",
        backend_route_prefixes=("/api/v1/chat", "/api/v1/documents"),
        backend_router_ids=("chat", "documents", "history"),
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
        backend_router_ids=("aurasql",),
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
        backend_router_ids=("analysis",),
        required_capabilities=(Capability.AUTH, Capability.WORKFLOWS, Capability.ARTIFACTS),
        required_permissions=("analysis:run",), required_env_keys=("LLM_PROVIDER",),
        demo_scenarios=(_scenario("sales-diagnostics", "Sales diagnostics", "Profile a sales dataset and identify defensible drivers.", "Analyze the strongest drivers of sales and distinguish evidence from hypotheses."),),
        health_check_id="analysis", packaging_paths=("backend/app/analysis", "backend/app/api/routes/analysis.py", "frontend/app/analysis"),
    ),
    AppManifest(
        id="presentation-studio", version="1.0.0", name="Presentation Studio",
        summary="Narrative-first, data-backed presentation planning and PPTX generation.",
        category="content", icon="presentation", frontend_route="/analysis",
        backend_route_prefixes=("/api/v1/analysis",),
        backend_router_ids=("presentation",),
        required_capabilities=(Capability.AUTH, Capability.ARTIFACTS, Capability.PRESENTATIONS),
        required_permissions=("presentation:generate",), required_env_keys=("LLM_PROVIDER",),
        dependencies=(AppDependency(app_id="data-analyst", minimum_version="1.0.0"),),
        demo_scenarios=(_scenario("executive-deck", "Executive deck", "Turn an analysis into an evidence-backed executive presentation.", "Create an executive deck with one decision per slide."),),
        health_check_id="presentations", packaging_paths=("backend/app/services/analysis/slide_generator.py", "frontend/app/analysis/[jobId]/report"),
    ),
    AppManifest(
        id="career-studio", version="1.0.0", name="Career Studio",
        summary="Truth-preserving resume analysis, tailoring, generation, and review.",
        category="career", icon="briefcase-business", frontend_route="/nexus",
        backend_route_prefixes=("/api/v1/nexus", "/api/v1/workflows/auto-tailor"),
        backend_router_ids=("nexus-resume", "resume-generator", "workflows"),
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
        backend_router_ids=(),
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
