# Foundation Production Fixes Report

## Production files

- `backend/app/platform/apps/registry.py`
- `backend/app/platform/apps/contracts.py`
- `frontend/app/apps/error.tsx`
- `frontend/components/layout/Header.tsx`

## Changes

- Added explicit enabled dependency validation during registry finalization. An
  explicitly enabled application now causes an actionable `RegistryError` when
  one of its required application dependencies is installed but not enabled.
  Unknown enabled identifiers, installed dependency checks, minimum-version
  checks, and `None` meaning all registered applications remain unchanged.
- Tightened `frontend_route` to a normalized same-origin root-relative path:
  one leading slash, non-empty path segments, no repeated or trailing slash
  except the root route, and only the existing lowercase alphanumeric,
  underscore, hyphen, slash, and bracket character set. Protocol-relative,
  query, fragment, backslash, percent-encoded, and traversal forms are rejected.
- Added per-item validation for `backend_route_prefixes`. Prefixes must be
  normalized absolute paths with a single leading slash and lowercase
  alphanumeric, underscore, or hyphen segments; query, fragment, backslash,
  percent-encoded, repeated-slash, trailing-slash, and traversal forms are
  rejected. The model's field names and serialized JSON shape are unchanged.
- Added the `/apps` route-segment client error boundary for non-404 failures.
  It uses the shared `Alert` and `Button` components, exposes an accessible alert
  message, and calls the framework-provided `reset()` callback from Retry.
  Existing `notFound()` handling in the detail page was not changed.
- Added explicit accessible names to the icon-only notification and account
  controls. The live LLM/backend indicator now exposes a polite, atomic status
  with readable screen-reader text while retaining its existing visual dot,
  title, behavior, and layout.
- Preserved the existing uncommitted manifest-driven Header navigation changes
  and made only additive accessibility edits plus trailing-whitespace cleanup.

## Deferred review findings

The following decision-dependent items were intentionally not changed:

- Splitting the shared analysis router.
- Migrating hard-coded navigation outside `Header`.
- Changing `/api/v1` information metadata.

No tests or test files were added.

## Static verification

- Reviewed all four production files and their scoped diffs directly.
- Parsed both modified Python files with the standard-library AST parser; both
  parsed successfully.
- Scanned the four production files for trailing whitespace after cleanup; no
  matches remained.
- Ran `git diff --check` over the three tracked production files; it exited
  successfully with no output.
- Inspected the new TypeScript error boundary and modified JSX/imports for
  client-boundary placement, component signatures, balanced syntax, accessible
  semantics, and consistency with shared UI patterns.
- Confirmed statically that malformed route forms are excluded by segment-based
  patterns and that each explicitly enabled manifest is checked against every
  declared dependency before `_finalized` is set.

## Verification limits and repository state

- Tests, builds, lint, typecheck, and runtime commands were not run, as
  instructed. Type/framework integration and rendered behavior therefore remain
  unverified by executable tooling.
- Files remain unstaged and uncommitted; no Git writes were attempted.
- `.superpowers` was changed only by adding this report.
- `graphify-out` was not modified.

## Concerns

- No executable verification was permitted. Confidence is based on AST parsing,
  diff/whitespace checks, and direct static inspection only.
