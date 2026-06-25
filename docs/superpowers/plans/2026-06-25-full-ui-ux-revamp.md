# Full UI/UX Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all 10 requested UI/UX improvements in staged, independently verifiable commits.

**Architecture:** Add shared UI primitives and a job center first, then migrate specific workflows and table pages. Keep backend API contracts unchanged and prefer local UI state where no backend progress events exist.

**Tech Stack:** Next.js App Router, React 18, TypeScript, Tailwind CSS, lucide-react, existing Zustand/auth/job providers.

---

## File Structure

- Create `frontend/components/layout/JobCenter.tsx`: persistent job drawer and compact job indicator.
- Modify `frontend/components/providers/JobProvider.tsx`: enrich job metadata and expose update helpers.
- Modify `frontend/components/layout/Header.tsx`: mount job center and improve mobile nav.
- Create `frontend/components/ui/data-table.tsx`: lightweight reusable table for simple pages.
- Modify `frontend/app/aurasql/connections/page.tsx`: replace AG Grid with lightweight table.
- Modify `frontend/app/aurasql/history/page.tsx`: replace AG Grid with lightweight table.
- Modify `frontend/app/nexus/resumes/page.tsx`: replace AG Grid with lightweight table.
- Modify `frontend/app/workflows/auto-tailor/page.tsx`: convert primary workflow to stepper layout.
- Modify `frontend/app/aurasql/query/page.tsx`: refine workbench layout, results panel, status timeline.
- Modify route pages as needed for empty/error/retry states and mobile polish.

## Phase 1: Foundation and Job Center

- [ ] Extend `Job` type in `frontend/components/providers/JobProvider.tsx` with optional `title`, `description`, `progress`, `href`, and `createdAt`.
- [ ] Add `updateJob(id, patch)` to JobProvider and keep existing `addJob`, `removeJob`, `isJobActive` behavior compatible.
- [ ] Create `frontend/components/layout/JobCenter.tsx` with a header button showing active job count and a dropdown/drawer listing active jobs.
- [ ] Mount `JobCenter` inside `Header`.
- [ ] Update analysis start/upload and document upload call sites to pass readable job metadata.
- [ ] Verify with `npm run build`.
- [ ] Commit: `feat: add persistent job center`.

## Phase 2: Lightweight Tables

- [ ] Create `frontend/components/ui/data-table.tsx` supporting columns, empty state, loading state, row actions, and client-side text filter.
- [ ] Replace AG Grid in `frontend/app/aurasql/connections/page.tsx`.
- [ ] Replace AG Grid in `frontend/app/aurasql/history/page.tsx`.
- [ ] Replace AG Grid in `frontend/app/nexus/resumes/page.tsx`.
- [ ] Keep all current actions: query/edit/delete connection, history display, resume upload/select/delete/analyze flow.
- [ ] Verify `npm run build` and local route responses for the three pages.
- [ ] Commit: `perf: replace simple grids with lightweight tables`.

## Phase 3: Auto-Tailor Stepper

- [ ] Add local step model in `frontend/app/workflows/auto-tailor/page.tsx`: setup, running, review, complete.
- [ ] Render compact stepper above workflow content.
- [ ] Keep existing HITL actions and API calls unchanged.
- [ ] Move critique, scores, diff, and preview into a clearer review workspace.
- [ ] Improve empty and loading states for resume loading, missing score data, and missing preview data.
- [ ] Verify `npm run build` and `/workflows/auto-tailor`.
- [ ] Commit: `feat: refine auto-tailor stepper workflow`.

## Phase 4: AuraSQL Workbench

- [ ] Refine `frontend/app/aurasql/query/page.tsx` into stable left sidebar, central chat/SQL canvas, and contextual result area within existing component boundaries.
- [ ] Keep `AuraSqlSidebar` and all API calls unchanged.
- [ ] Add a per-message status timeline for generated SQL: generated, validated, executable, executed/error.
- [ ] Improve result panel with row count, column count, CSV export, filter, and empty/no-match states.
- [ ] Ensure generate and execute loaders are local to the active message and do not block the full screen.
- [ ] Verify `npm run build` and `/aurasql/query`.
- [ ] Commit: `feat: refine aurasql workbench`.

## Phase 5: Mobile, Performance, and Interaction Polish

- [ ] Improve `Header` mobile navigation with a compact menu instead of overflowing nav links.
- [ ] Lazy-load heavy UI dependencies where safe, especially diff viewer in Auto-Tailor.
- [ ] Remove remaining shader/blur-heavy visuals from operational pages that do not need them.
- [ ] Add consistent disabled reason text where primary actions cannot run.
- [ ] Add copy/download success toasts where missing.
- [ ] Run `npm run build`.
- [ ] Smoke test key routes with `curl -I`.
- [ ] Commit: `chore: polish mobile performance and interactions`.

## Verification Checklist

- [ ] `npm run build` exits 0.
- [ ] `/workflows` returns 200.
- [ ] `/analysis` returns 200.
- [ ] `/workflows/auto-tailor` returns 200.
- [ ] `/aurasql/query` returns 200.
- [ ] `/aurasql/connections` returns 200.
- [ ] `/aurasql/history` returns 200.
- [ ] `/nexus/resumes` returns 200.
- [ ] `git status --short` contains no revamp files except any pre-existing unrelated changes.
