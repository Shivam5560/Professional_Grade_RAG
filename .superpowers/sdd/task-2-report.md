# Task 2 Report: Validated Registry and Built-In Application Manifests

## Status

Implemented the production-only portions of Task 2. Tests were neither created nor modified, and no tests were run, per the latest user instruction.

## Production files

- Created `backend/app/platform/apps/registry.py`
  - Adds `RegistryError`.
  - Adds `AppRegistry.register()`, `finalize()`, `list_enabled()`, and `get()`.
  - Enforces unique application IDs, finalization before reads, enabled-ID validation, dependency presence, and minimum semantic versions.
- Created `backend/app/platform/apps/builtin.py`
  - Defines the six required flagship manifests with the exact Task 2 production values.
  - Adds `build_builtin_registry()` and the eagerly finalized singleton exposed by `get_app_registry()`.
- Modified `backend/app/config.py`
  - Adds `enabled_app_ids: List[str]` with the `NEXUS_ENABLED_APPS` alias and an empty-list default.
- Modified `backend/app/platform/apps/__init__.py`
  - Publicly exports `AppRegistry`, `RegistryError`, and `get_app_registry` alongside the Task 1 contracts.

## Static checks performed

- `git diff --check`: passed with no whitespace errors.
- Parsed all five relevant Python modules with Python 3 `ast.parse`: passed.
- Inspected the diff and working-tree scope: no test files changed; `graphify-out/` was not touched.
- Confirmed all six built-in application IDs are present:
  - `aurasql`
  - `career-studio`
  - `data-analyst`
  - `developer-studio`
  - `knowledge-studio`
  - `presentation-studio`
- Confirmed registry read methods call the finalization guard and enabled results sort by application ID.

## Self-review

- Import cycles: the public package imports `builtin`; `builtin` imports `contracts` and `registry`; `registry` imports only `contracts`. Python can initialize these submodules without a reverse dependency into `builtin`, so there is no circular dependency chain.
- Initialization: the built-in singleton is constructed and finalized eagerly. Empty `NEXUS_ENABLED_APPS` enables all built-ins; unknown configured IDs raise `RegistryError` during initialization as required.
- Settings parsing: `List[str]` plus a Pydantic `Field` alias matches the existing settings conventions and accepts the documented JSON-array environment representation.
- Manifest correctness: values were transcribed from the Task 2 brief, including routes, router IDs, capabilities, permissions, environment keys, scenarios, health IDs, and packaging paths.
- Dependency/finalization behavior: registration closes after finalization; reads fail before finalization; missing and under-versioned dependencies fail finalization; disabled manifests are hidden from both read interfaces.
- Scope: only the four requested production files are intended for the Task 2 commit. This report remains under `.superpowers/` and is not part of the production commit.

## Omitted tests and concerns

- Per instruction, no tests were written or run, and no runtime import smoke check was performed.
- Consequently, behavior is supported by static inspection only until the deferred registry and manifest tests are added and executed.
- Eager package initialization means an invalid `NEXUS_ENABLED_APPS` deployment value intentionally prevents imports of `app.platform.apps`; this is the required fail-fast behavior but should be considered when diagnosing startup failures.

## Follow-up fix: immutable enablement snapshot

- Fixed `AppRegistry` retaining the caller-owned mutable `enabled_ids` set by reference.
- Construction now snapshots configured identifiers into a `frozenset`, while preserving `None` as the enable-all sentinel.
- External mutation of the original set can no longer alter reads after finalization or bypass the enabled-ID validation performed by `finalize()`.
- Static verification after the fix:
  - Parsed `backend/app/platform/apps/registry.py` with Python 3 `ast.parse`: passed.
  - `git diff --check`: passed.
- No tests or runtime imports were run, per instruction.
- The review note about hard-coded frontend visibility was intentionally not addressed because Tasks 6–8 own that planned integration.
