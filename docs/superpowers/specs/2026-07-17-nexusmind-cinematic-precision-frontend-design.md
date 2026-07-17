# NexusMind Cinematic Precision Frontend Design

**Status:** Approved  
**Date:** 2026-07-17  
**Scope:** Complete frontend visual system, public showcase, application shell, and all user-facing workspaces

## 1. Context

NexusMind Studio is a technically substantial platform spanning grounded RAG chat, document management, AuraSQL, multi-agent analysis, resume intelligence, document generation, and long-running workflows. The current frontend exposes these capabilities but has grown screen by screen. Important information competes for attention, application layouts diverge, and several pages combine navigation, controls, results, metadata, and decorative effects at equal visual weight.

The redesign must present NexusMind as a flagship solo-engineered product to viewers and recruiters while making daily use calmer and easier. It must feel highly creative on first contact, retain every meaningful capability, support authored dark and light modes, and remain disciplined about browser load, GPU use, memory, accessibility, and responsiveness.

This specification supersedes the visual direction of the narrower June 2026 UI/UX revamp while retaining its completed operational improvements such as the job center, lightweight tables, workflow stepper, and contextual loading states.

## 2. Goals

1. Create an unmistakable premium identity named **Cinematic Precision**.
2. Make the public experience compelling to recruiters without requiring credentials or live AI infrastructure.
3. Simplify every workspace through a consistent **Focus → Context → Inspect** hierarchy.
4. Preserve all existing frontend behaviors and backend API contracts.
5. Provide equally intentional dark and light modes.
6. Use rich animation at high-value moments without making operational work distracting or expensive.
7. Establish reusable components and tokens so future applications inherit the same quality.
8. Improve accessibility, mobile behavior, loading feedback, error recovery, and perceived performance.

## 3. Non-goals

- Rewriting backend services or changing API response contracts.
- Removing advanced information or expert controls.
- Making every screen continuously cinematic or WebGL-driven.
- Maintaining the eight existing color palettes. They will be replaced by one art-directed identity with system, dark, and light appearance settings.
- Presenting showcase fixtures as live or generated data.

## 4. Design principles

### 4.1 Product first, creator appropriately revealed

The opening experience establishes NexusMind as a serious standalone product. After capabilities and technical proof have earned credibility, an authored creator section identifies Shivam Sourav as the sole developer and explains architecture decisions, breadth of ownership, and engineering depth. Concise attribution remains in the footer, and the existing developer page becomes a deeper public engineering profile.

### 4.2 Visually heavy, technically disciplined

The interface may look computationally extravagant, but expensive work is isolated, lazy-loaded, paused when invisible, and replaced with static or reduced variants on constrained devices.

### 4.3 One dominant task per screen

Every route identifies the current intent, active content, and next meaningful action. Supporting context remains nearby. Deep detail is available on demand rather than permanently occupying the canvas.

### 4.4 No generic AI aesthetic

The identity avoids purple gradients, excessive neon glass, and undifferentiated card grids. Depth comes from material contrast, lighting, typography, and purposeful motion.

## 5. Experience architecture

### 5.1 Public flagship layer

The unauthenticated `/` route becomes the public flagship experience. It contains:

1. Cinematic opening statement and clear product positioning.
2. Interactive capability story covering Knowledge, AuraSQL, Analysis, and Career Studio.
3. Technical proof: grounded retrieval, schema awareness, workflow orchestration, observability, deployment, and measurable system characteristics.
4. Guided showcase entry points that do not require a backend.
5. Creator story and link to the detailed developer profile.
6. Calls to action for **Explore Showcase** and **Launch Live Workspace**.

Authentication remains at `/auth`. Authenticated users enter the catalog or their chosen application without replaying the full public presentation.

### 5.2 Showcase mode

`/showcase` provides the overview. `/showcase/knowledge`, `/showcase/aurasql`, `/showcase/analysis`, and `/showcase/career` provide realistic, interactive, precomputed journeys. Showcase mode:

- Is clearly labeled at all times.
- Never sends mutations to the live backend.
- Uses deterministic local fixtures and timed state transitions.
- Demonstrates meaningful end-to-end outcomes rather than static screenshots.
- Shares presentation components with live mode.
- Offers a direct transition to authentication when a viewer wants to use the real platform.

### 5.3 Unified product shell

The authenticated and showcase workspaces share a shell providing:

- Compact global navigation rail.
- Application switcher backed by the current application catalog.
- Contextual workspace header.
- Global command/search access.
- Persistent job center and connection state.
- System/dark/light appearance control.
- User or showcase identity.
- Responsive mobile navigation.

### 5.4 Focused application workspaces

The shell hosts Knowledge, AuraSQL, Analysis, Career Studio, workflows, and supporting management routes. Each application receives a recognizable accent and tailored task flow while sharing the same spacing, motion, typography, panels, drawers, status components, and responsive rules.

### 5.5 Route inventory

The redesign covers the following user-facing routes:

- Public: `/`, `/auth`, `/developer`, `/showcase`, and the four showcase routes defined above.
- Catalog: `/apps` and `/apps/[appId]`.
- Knowledge: `/chat` and `/knowledge-base`.
- AuraSQL: `/aurasql`, `/aurasql/query`, `/aurasql/history`, `/aurasql/connections`, `/aurasql/connections/new`, `/aurasql/connections/[id]`, and `/aurasql/contexts/new`.
- Analysis: `/analysis`, `/analysis/history`, `/analysis/[jobId]`, and `/analysis/[jobId]/report`.
- Career Studio: `/nexus`, `/nexus/resumes`, `/nexus/jd`, `/nexus/report`, and `/nexus/generate`.
- Workflows: `/workflows` and `/workflows/auto-tailor`.

After authentication, the default destination is `/apps` unless the user arrived with a valid application destination.

## 6. Cinematic Precision visual system

### 6.1 Dark mode

| Role | Token | Value |
|---|---|---|
| Page depth | Void | `#090A0D` |
| Elevated surface | Graphite | `#15171C` |
| Primary text | Pearl | `#F5F0E7` |
| Intelligence signal | Signal Mint | `#B7FBD7` |
| Human craft accent | Burnished Copper | `#E49A67` |
| Data accent | Data Cyan | `#67D6E8` |

Dark mode is the flagship default: dimensional graphite rather than pure black, luminous mint used sparingly, warm pearl typography, and selective copper illumination.

### 6.2 Light mode

| Role | Token | Value |
|---|---|---|
| Page base | Porcelain | `#F2EEE5` |
| Elevated surface | Paper | `#FBF8F2` |
| Primary text | Ink | `#181916` |
| Intelligence signal | Forest Mint | `#127A55` |
| Human craft accent | Oxidized Copper | `#A94E25` |
| Data accent | Deep Cyan | `#147D91` |

Light mode is authored independently rather than produced by token inversion. Warm neutral surfaces avoid sterile white dashboards and support long reading sessions.

### 6.3 Application accents

- Knowledge and RAG Chat: mint.
- AuraSQL: cyan.
- Analysis: copper and restrained amber for comparisons.
- Career Studio and Resume workflows: cobalt blue, not purple.
- Success, warning, destructive, and informational colors remain semantic and meet contrast requirements in both modes.

Application accents identify context; they do not recolor the entire shell.

### 6.4 Typography

- **Space Grotesk:** product display, headings, navigation, and primary interface text.
- **Newsreader:** rare editorial emphasis in flagship headlines and creator storytelling.
- **IBM Plex Mono:** SQL, metrics, trace identifiers, technical labels, and code.

Editorial type is a signature accent, not the default body face. Reading widths, line heights, and responsive type scales are tokenized.

### 6.5 Signature creative devices

1. **Nexus Aperture:** concentric intelligence signal for hero moments, product identity, loading, and major transitions.
2. **Reasoning Threads:** animated relationships between sources, schemas, evidence, operations, and conclusions.
3. **Material Transition:** cinematic graphite gracefully yields to focused work surfaces when a task begins.
4. **Outcome Bloom:** restrained completion signature for generated reports, successful analyses, and important workflow milestones.

These devices recur selectively to build recognition. They never run continuously on every route.

## 7. Information architecture: Focus → Context → Inspect

### 7.1 Tier 1: always visible

- The user's current intent.
- Active content or result.
- Primary action and next meaningful step.
- Critical status that changes the user's decision.

### 7.2 Tier 2: contextual

- Attached files.
- Active database or application mode.
- Confidence, validation, and job progress.
- Compact filters relevant to the current result.

### 7.3 Tier 3: on demand

- Complete citations and source excerpts.
- Database schema and metadata.
- Logs, traces, histories, advanced settings, and export details.
- Secondary visualizations and raw technical output.

Tier 3 content opens in contextual inspectors, drawers, sheets, or dedicated detail routes. It remains keyboard accessible and deep-linkable where appropriate.

## 8. Application UX

### 8.1 Knowledge and RAG Chat

- Center the conversation at a readable width.
- Replace permanently competing sidebars with the global rail and contextual history/source drawers.
- Represent selected files and mode as compact, editable context near the composer.
- Show confidence and citation count inline with the answer.
- Open full evidence in an inspector when requested.
- Keep streaming, diagrams, source citations, session history, and file selection intact.

### 8.2 AuraSQL

- Organize the primary workbench into **Ask → Review → Results**.
- Show only the active query and result by default.
- Keep connection and context visible as compact status.
- Open schema, recommendations, history, and metadata through contextual inspectors.
- Keep generated SQL, validation, execution status, results, filters, charting, and export available.
- Preserve connection, context, history, and query-management routes while migrating them to shared layouts.

### 8.3 Analysis

- Present setup as a concise guided configuration rather than a field wall.
- Keep long-running status local and in the global job center.
- Make the live run page emphasize current phase, meaningful events, and recoverable errors.
- Structure the report around an executive narrative with progressively disclosed methods, charts, diagnostics, and raw outputs.

### 8.4 Career Studio and Resume workflows

- Create one clear journey from resume selection and job description through analysis, tailoring, review, and export.
- Preserve score explanations, diffs, critiques, PDF generation, and human-in-the-loop actions.
- Move detailed sub-scores, metadata, and generated artifacts into tabs or inspectors when they are not the current decision.

### 8.5 Catalog, workflows, knowledge base, and supporting routes

- Use outcome-oriented application cards with one primary action.
- Consolidate repetitive management layouts onto shared tables, empty states, filters, and confirmation patterns.
- Retain catalog-based visibility and application route isolation already present on the current branch.

## 9. Component architecture

The implementation should introduce bounded component families rather than another large page-specific layer.

### 9.1 Foundation

- Theme tokens and semantic color aliases.
- Responsive spacing, type, radius, elevation, and layering tokens.
- Shared motion definitions and reduced-motion variants.
- Theme bootstrap that avoids flash and migrates legacy palette preferences to the new system setting.

### 9.2 Shell

- `AppShell`
- `GlobalRail`
- `WorkspaceHeader`
- `ApplicationSwitcher`
- `CommandMenu`
- `AppearanceControl`
- Existing `JobCenter`, integrated visually rather than replaced

### 9.3 Workspace

- `WorkspaceFrame`
- `ContextBar`
- `InspectorPanel` with desktop panel and mobile sheet behavior
- `PrimaryActionBar`
- `StatusTimeline`
- `FocusedEmptyState`
- `OperationError`
- Shared loading and skeleton primitives

### 9.4 Flagship and showcase

- `FlagshipHero`
- `CapabilityStory`
- `TechnicalProof`
- `CreatorStory`
- `ShowcaseProvider`
- Application-specific showcase scenes built from real presentation components

Large existing route files should be decomposed when responsibilities are clear, especially AuraSQL query, Auto-Tailor, authentication, and chat. Refactoring must remain scoped to presentation and view-state boundaries required by this redesign.

## 10. Data flow

Live and showcase rendering share a presentation-facing interface:

```text
Route
  → experience mode resolution
  → live API adapter OR showcase fixture adapter
  → feature view model / local state
  → shared workspace components
  → contextual status, inspector, and job surfaces
```

Live mode continues to use the existing API client, Zustand auth state, analysis stores, hooks, and job provider. Showcase mode supplies deterministic fixtures through feature-level adapters and does not populate authenticated stores or persist simulated mutations as real user data.

Route components should orchestrate data and composition. Reusable presentation components should not call APIs directly. Feature hooks own asynchronous state and expose explicit loading, success, empty, and error states.

## 11. Motion and visual performance

### 11.1 Motion hierarchy

- **Ambient:** very slow, low-amplitude flagship light and aperture movement.
- **Navigational:** route, panel, drawer, and application transitions.
- **Responsive:** hover, press, focus, drag, copy, and selection feedback.
- **Narrative:** capability reveals and reasoning-thread sequences.
- **Outcome:** completion blooms and generated-result reveals.

### 11.2 Runtime rules

- Use a maximum of one WebGL context on a page.
- Dynamically import Three.js scenes, Plotly, diff viewers, and other heavy modules.
- Do not include WebGL or analytics visualization libraries in routes that do not render them.
- Cap device pixel ratio for GPU scenes and provide static image/CSS fallbacks.
- Pause animation when off-screen, when the document is hidden, and when the relevant route is inactive.
- Prefer transform and opacity animation; avoid sustained large-area blur and filter animation.
- Respect `prefers-reduced-motion` and provide an in-product reduced-effects setting if runtime detection indicates pressure.
- Disable nonessential pointer-reactive behavior on coarse pointers and constrained viewports.
- Prevent animation from delaying content, navigation, authentication, or primary actions.

### 11.3 Performance acceptance

- Establish production bundle baselines before migration and prevent unexplained route growth.
- Public and operational routes must render meaningful static structure before optional cinematic modules load.
- Internal targets are LCP under 2.5 seconds, INP under 200 milliseconds, and CLS under 0.1 on the test profile defined in section 14.4.
- Browser checks must include heap stability across repeated navigation, no leaked WebGL contexts, no animation while hidden, and acceptable GPU/CPU use during idle workspaces.

## 12. Responsive and accessible behavior

- Desktop uses a compact rail, focused canvas, and optional inspector.
- Tablet collapses the inspector into an overlay panel and keeps primary actions anchored.
- Mobile becomes a single focused column with bottom-sheet context and navigation.
- Every interaction is available by keyboard without relying on hover or custom cursor behavior.
- Focus order follows visual order; dialogs and drawers restore focus correctly.
- Both modes meet contrast requirements, including muted text and status colors.
- Animation respects reduced motion; status is never communicated by motion or color alone.
- Loading, streaming, errors, and job updates use appropriate live-region behavior without excessive announcements.

## 13. Error, empty, and degraded states

- Operation errors appear beside the failed action and preserve user input.
- Retriable failures include a clear retry action and useful explanation.
- Global API failures preserve the shell, navigation, and any safe cached content.
- Showcase fallback is offered only as an explicit labeled choice, never as silent substitution for live output.
- Empty states explain the benefit, required prerequisite, and next action.
- Disabled controls explain why they are unavailable.
- Failed optional cinematic modules fall back to static branded visuals without affecting the task.

## 14. Testing and verification

The frontend currently lacks a dedicated automated test framework. This redesign will establish proportionate coverage.

### 14.1 Component and state tests

- Add Vitest and React Testing Library.
- Test theme bootstrap and legacy preference migration.
- Test shell, inspector, responsive navigation, context bar, error, empty, and loading states.
- Test live/showcase mode isolation and fixture determinism.

### 14.2 End-to-end tests

- Add Playwright journeys for public showcase, authentication, catalog navigation, Chat, AuraSQL, Analysis, Resume Studio, and appearance persistence.
- Verify keyboard-only navigation and key mobile workflows.
- Verify backend failures, empty states, and retry behavior.

### 14.3 Visual and performance verification

- Capture approved desktop and mobile screenshots in dark and light modes.
- Run production builds and route smoke tests throughout migration.
- Inspect route bundles after introducing or moving heavy dependencies.
- Profile flagship animation, route changes, repeated panel use, and background-tab behavior.
- Confirm no new console errors, hydration warnings, layout instability, or leaked animation loops.

### 14.4 Test profile

- Desktop visual and interaction baseline: Chromium at `1440×900`.
- Mobile visual and interaction baseline: Chromium emulating a `412×915` touch viewport.
- Performance baseline: the mobile viewport with 4× CPU slowdown and Fast 4G network throttling against a production build.
- Cross-browser functional coverage: current Playwright Chromium, Firefox, and WebKit desktop projects plus representative Chromium and WebKit mobile emulation.
- Memory and lifecycle profile: ten repeated cross-application navigations and five open/close cycles for each heavy inspector or visualization. Heap usage must settle after garbage collection, WebGL context count must not accumulate, and hidden routes must not continue animation work.

## 15. Delivery strategy

The redesign should ship in independently buildable phases:

1. **Foundation:** tokens, typography, theme bootstrap, motion runtime, shared states, and test scaffolding.
2. **Flagship:** public homepage, showcase mode, creator story, and authentication treatment.
3. **Shell:** global rail, header, app switching, command access, jobs, and responsive structure.
4. **Knowledge:** Chat and knowledge-base migration.
5. **AuraSQL:** dashboard, workbench, connection, context, and history migration.
6. **Analysis:** setup, live run, history, and reports.
7. **Career and workflows:** Nexus routes, ResumeGen, Auto-Tailor, and workflow catalog.
8. **Hardening:** accessibility, responsive parity, visual regression, bundle and memory profiling, and final cross-route polish.

Each phase must preserve working routes, pass its relevant tests, and end with a production build. Feature work should not overwrite unrelated changes committed after this specification.

## 16. Success criteria

The redesign is complete when:

1. Every route in section 5.5 uses the Cinematic Precision tokens and appropriate shared layout.
2. Dark, light, and system settings work without flash and persist correctly.
3. Purple AI gradients and the legacy multi-palette selector are removed.
4. Public showcase journeys work without live backend dependencies and remain clearly labeled.
5. Chat and AuraSQL demonstrate the approved Focus → Context → Inspect hierarchy.
6. Analysis, Career Studio, workflows, and supporting routes preserve all existing capabilities with reduced default clutter.
7. Desktop, tablet, and mobile primary journeys are usable by keyboard and meet contrast and reduced-motion requirements.
8. Heavy visual dependencies are route-scoped, lazy-loaded, paused when inactive, and backed by graceful fallbacks.
9. Automated component and end-to-end coverage protects shared behavior and core journeys.
10. Production builds, smoke tests, browser performance checks, and memory/GPU checks pass on the section 14.4 test profile.

## 17. Approved direction summary

- Audience: viewers and recruiters, with daily usability retained.
- Scope: unified flagship system, not a homepage-only facelift.
- Art direction: Cinematic Precision.
- Modes: equally authored dark and light, plus system preference.
- Core colors: mint intelligence signal and burnished copper human accent; no purple.
- Creator positioning: product first, creator story after technical proof.
- Recruiter resilience: clearly labeled deterministic showcase mode.
- Workspace model: Focus → Context → Inspect.
- Animation: rich at entrances and outcomes, restrained during focused work.
- Engineering priority: reusable boundaries, accessibility, route-level performance, and complete regression protection.
