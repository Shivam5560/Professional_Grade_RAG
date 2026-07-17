# Backend Router Isolation Brief

## Goal

Give Data Analyst and Presentation Studio distinct FastAPI router ownership while preserving the current public URL `/api/v1/analysis/{job_id}/report/download` whenever Presentation Studio is enabled.

## Required production changes

- Keep data-analysis endpoints on `app.api.routes.analysis.router`.
- Move the PPTX download endpoint onto a distinct `APIRouter` owned only by Presentation Studio. It may remain in the compatibility `analysis.py` module as a separately exported router; a separate module is not required.
- Extend `RouterSpec` so a router ID can resolve a named `APIRouter` export instead of assuming every module exposes only `router`.
- Add a distinct `presentation` router ID and map it to the presentation router export.
- Update built-in manifests:
  - Data Analyst owns only `analysis`.
  - Presentation Studio owns only `presentation`.
  - Presentation Studio declares a required dependency on Data Analyst `>=1.0.0`, because the current presentation export consumes completed analysis jobs and reports.
  - Route metadata must describe the actual compatibility route prefix rather than the nonexistent `/api/v1/analysis/reports` prefix.
- Preserve atomic router resolution: resolve and validate every selected router before mutating the FastAPI application.
- Preserve all current endpoint paths, authentication/ownership checks, response behavior, download cleanup, and enabled-all defaults.

## Isolation behavior

- Data Analyst enabled, Presentation disabled: analysis jobs/reports/charts/WebSockets are registered; PPTX download is absent.
- Presentation enabled, Data Analyst disabled: registry finalization fails with the existing enabled-dependency error.
- Both enabled: all current routes are registered once, including PPTX download.

## User verification direction

Implement production code only. Do not add or run tests, builds, imports, or runtime commands. Static syntax/diff review is allowed. Commit the scoped production changes if Git writes are available.
