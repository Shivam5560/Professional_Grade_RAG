# Backend Router Isolation Report

## Status

Implemented the router-isolation brief in production code on branch `enhancements`.
The changes are intentionally uncommitted because the parent task explicitly directed that no Git writes be attempted during handoff.

## Production files changed

- `backend/app/api/routes/analysis.py`
  - Added a distinct `presentation_router` with the existing `/analysis` prefix and `Analysis` tag.
  - Moved only `GET /{job_id}/report/download` to `presentation_router`.
  - Left the download handler body unchanged, preserving authentication, user/job ownership filtering, report and chart lookup, response metadata, failure cleanup, and response-background cleanup.
  - Kept all other analysis HTTP and WebSocket decorators on `router`.

- `backend/app/platform/apps/fastapi.py`
  - Added `RouterSpec.router_name`, defaulting to `router`, so existing router IDs retain their current resolution behavior.
  - Added the `presentation` router ID, resolving `app.api.routes.analysis.presentation_router` under the existing `/api/v1` install prefix.
  - Changed router resolution and validation to use the named export.
  - Preserved atomic application mutation: all selected exports are imported, resolved, and validated as `APIRouter` instances before the first `app.include_router` call.

- `backend/app/platform/apps/builtin.py`
  - Kept Data Analyst ownership at `backend_router_ids=("analysis",)`.
  - Changed Presentation Studio ownership to `backend_router_ids=("presentation",)`.
  - Added the required `data-analyst>=1.0.0` manifest dependency.
  - Replaced the nonexistent `/api/v1/analysis/reports` metadata prefix with the actual compatibility prefix `/api/v1/analysis`.

## Static verification performed

- Parsed all three changed Python files with `ast.parse`; syntax parsing succeeded.
- Enumerated decorators in `analysis.py`: 11 routes remain on `router`, and exactly one route (`GET /{job_id}/report/download`) is owned by `presentation_router`.
- Confirmed both module routers use `/analysis`, producing the unchanged public download URL when installed with the `/api/v1` `RouterSpec` prefix.
- Confirmed no duplicate `(router, method, path)` decorator registrations in `analysis.py`.
- Confirmed the `presentation` spec names `presentation_router`, resolution uses `spec.router_name`, and APIRouter validation occurs before routers are appended for installation.
- Confirmed the resolution loop completes before the separate `include_router` loop begins.
- Statically inspected the two manifests: Data Analyst owns only `analysis`; Presentation Studio owns only `presentation`, advertises `/api/v1/analysis`, and requires Data Analyst `>=1.0.0`.
- Confirmed the existing enabled-dependency validation and enabled-all default were not modified.
- Ran `git diff --check`; it exited successfully with no diagnostics.
- A separate read-only code review found no Critical, Important, or Minor issues and assessed the diff as ready to merge under the permitted static-only verification scope.

Per direction, no tests, builds, application imports, servers, OpenAPI generation, or dependency commands were created or run.

## Commit and working-tree status

- Commit: none; scoped production changes remain uncommitted.
- Scoped uncommitted production files:
  - `backend/app/api/routes/analysis.py`
  - `backend/app/platform/apps/fastapi.py`
  - `backend/app/platform/apps/builtin.py`
- Unrelated `.superpowers` changes already present in the shared worktree were not modified or staged, apart from this requested report.
- `graphify-out` was not touched.

## Concerns

- No production-code concern was found during static inspection or independent review.
- Runtime verification of the three enablement combinations and generated OpenAPI route inventory remains intentionally deferred by user direction.
