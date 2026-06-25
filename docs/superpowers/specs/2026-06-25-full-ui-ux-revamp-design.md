# Full UI/UX Revamp Design

## Goal

Implement the remaining 10 UI/UX improvements as a staged production-workspace revamp, improving clarity, performance, loading feedback, mobile usability, and workflow continuity without changing backend contracts.

## Scope

This revamp covers:
- Persistent job center for long-running work.
- AuraSQL workbench layout and contextual query status.
- Replacement of simple AG Grid pages with lightweight tables.
- Auto-Tailor stepper and clearer review states.
- Shared design tokens and status states.
- Better empty, error, retry, and confirmation flows.
- Mobile responsiveness for the main operational screens.
- Performance improvements through lighter components and lazy-loaded heavy dependencies where practical.
- Better result/report presentation affordances.
- Interaction polish for loading buttons, copy/download actions, and disabled states.

## Architecture

Use shared frontend primitives first, then migrate screens onto them incrementally. The app should keep one production workspace visual language: restrained header, 8px panel radius, dense but readable page sections, and contextual status feedback instead of full-page blocking loaders.

The JobProvider remains the central source for cross-page jobs. New UI reads from the provider and existing local page state; no backend API changes are required for this phase. Where backend progress is unavailable, the UI shows deterministic local operation states and clear messaging rather than fake percentages.

## Phases

1. Foundation and job center.
2. Lightweight table replacement for simple data grids.
3. Auto-Tailor stepper.
4. AuraSQL workbench refinement.
5. Mobile, performance, and interaction polish.

Each phase must build successfully and can be committed independently.

## Success Criteria

- `npm run build` passes after every phase.
- `/workflows`, `/analysis`, `/workflows/auto-tailor`, `/aurasql/query`, `/aurasql/connections`, `/aurasql/history`, and `/nexus/resumes` load locally.
- Simple table pages no longer require AG Grid in their page bundles.
- Long-running operations show visible status near the operation source and, where appropriate, in the job center.
- The UI remains visually calmer and more production-oriented than the previous shader/glass-heavy treatment.
