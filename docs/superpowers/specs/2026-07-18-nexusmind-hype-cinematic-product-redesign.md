# NexusMind Hype-Level Cinematic Product Redesign

**Status:** Approved direction, pending written-spec review  
**Date:** 2026-07-18  
**Scope:** Animated public homepage, login access, authenticated application dashboard, each application with local submenus, and developer page

## 1. Context

The existing frontend partially implemented the earlier Cinematic Precision direction. The public homepage and authentication route changed, but the application catalog and authenticated product remain inconsistent. They combine basic catalog cards, legacy headers and sidebars, old glass/aurora styling, dense control walls, and application-specific layouts that do not behave like one product.

This redesign is a full-system rebuild. It must not stop after the public routes or place a new shell around unchanged legacy screens. Every user-facing route will adopt the same navigation, hierarchy, motion, responsive behavior, and quality bar while preserving existing backend contracts and application capabilities.

The visual benchmark is the expressive, highly animated work featured in Framer Hype. NexusMind will use comparable energy and craft without copying a particular site or sacrificing operational clarity.

## 2. Goals

1. Make the complete product feel polished, premium, visually distinctive, and current.
2. Reduce cognitive load by giving every screen one dominant task or result.
3. Replace inconsistent navigation with one Adaptive Icon Rail system.
4. Use persistent cinematic imagery across authenticated screens without reducing readability.
5. Apply Framer-quality motion to routing, navigation, content, feedback, and live artifacts.
6. Give each application a distinct visual and motion identity inside a shared product system.
7. Preserve every meaningful feature through progressive disclosure rather than simultaneous display.
8. Keep AuraSQL tables and graphs first-class because visualization is central to its workflow.
9. Support desktop, tablet, mobile, keyboard use, reduced motion, and authored dark and light modes.
10. Verify every migrated route visually and behaviorally before considering its application family complete.
11. Eliminate top-level screen sprawl: users move from homepage to dashboard to one application, with application-specific history and settings kept inside that application's submenu.

## 3. Non-Goals

- Rebuilding backend services or changing API contracts.
- Migrating the application into the Framer site builder.
- Copying or embedding arbitrary Framer Marketplace components.
- Converting live charts, SQL results, reports, or evidence into static images.
- Displaying all available controls at once.
- Running expensive animation continuously when a route is hidden or reduced motion is enabled.
- Shipping remote placeholder images as production dependencies.
- Creating a global history center, global settings center, separate showcase area, or other top-level destinations outside the approved product structure.
- Promoting application history, settings, connections, or advanced tools into global navigation.

## 4. Approved Direction

### 4.1 Canvas First

Each route contains one dominant work canvas. Navigation, context, and advanced capabilities remain available but do not compete with the current task.

The standard authenticated composition is:

1. Adaptive Icon Rail.
2. Persistent cinematic media layer.
3. Readability veil and material surface.
4. Focus canvas for the current task or artifact.
5. Compact context ribbon.
6. On-demand inspector.
7. Contextual action dock.

Page sections are unframed layouts. Cards are reserved for repeated records, discrete artifacts, and modal tools. Cards will not be nested.

### 4.2 Adaptive Icon Rail

The rail replaces page-specific global headers, duplicated sidebars, and inconsistent application navigation.

- Compact icon-first desktop rail with tooltips.
- NexusMind identity and application switcher at the top.
- Application destinations in the middle.
- Jobs, appearance, help, and account actions at the bottom.
- Current application accent and animated active indicator.
- Optional contextual sub-navigation shown only for application routes that require it.
- Command menu for switching applications, opening recent work, and starting primary actions.
- Mobile adaptation as a stable bottom bar plus an application sheet.

The rail never expands permanently over the work canvas. Labels appear through hover, focus, temporary expansion, or the switcher.

### 4.3 Persistent Cinematic Media

Every application family receives an authored image collection and media behavior:

- Knowledge: archives, illuminated materials, evidence, and connected structures.
- AuraSQL: architecture, structured systems, grids, and flowing data.
- Analysis: editorial observation, comparison, and signal extraction.
- Career: human craft, documents, identity, and professional transformation.
- Workflows: sequences, mechanisms, orchestration, and progression.

Media remains present during active work but is controlled through darkening, cropping, blur, focal positioning, and material overlays. It must never reduce text contrast or make tables, editors, charts, or forms difficult to read.

Production assets will be generated as original bitmap imagery with the Codex image-generation capability, then stored locally under `frontend/public/images/cinematic/`. Real licensed photography is allowed only when generated media cannot represent the subject accurately. Remote placeholder URLs are prohibited in the finished product.

### 4.4 Hype-Level Motion

Motion is a structural tool, not a collection of unrelated effects. The implementation will use the existing React application with Motion/Framer Motion.

Approved motion behaviors include:

- Full-screen masked route transitions.
- Shared-element transitions from catalog items to application workspaces.
- Kinetic typography and sequenced content reveals.
- Persistent image parallax, crossfades, and focal movement.
- Scroll-linked media transformations on public and editorial surfaces.
- Animated rail, application switcher, command menu, inspectors, and action dock.
- Hover, tap, focus, drag, and mobile gesture feedback.
- Animated charts, counters, evidence maps, progress, and timelines.
- Cinematic loading, empty, success, and completion states.
- Selective shaders, distortion, grain, and light sweeps.

Motion intensity is tiered:

- Public homepage and application catalog: maximum expression.
- Application entry and empty states: high expression.
- Active workspaces: persistent but slower background motion; interaction and live-result motion receive priority.
- Reports and results: motion directs attention to conclusions and changes.
- Reduced-motion mode: fades, immediate layout changes, and static imagery preserve all information and functionality.

## 5. Information Hierarchy

### 5.1 Always Visible

- Current intent.
- Active work or result.
- Primary action or next step.
- Critical status affecting the user's decision.

### 5.2 Contextual

- Active files, database, mode, job, filters, and validation state.
- Compact controls directly affecting the visible result.
- Secondary action relevant to the current state.

### 5.3 On Demand

- Sources, excerpts, complete schema, logs, traces, raw output, metadata, histories, advanced settings, and export configuration.
- These open through inspectors, drawers, sheets, tabs, or dedicated detail routes.

No route may expose Tier 3 information by default unless that detail is the route's primary purpose.

## 6. Shared Screen Components

- `CinematicAppShell`: global authenticated composition and application identity.
- `AdaptiveRail`: icon navigation, switcher, global utilities, and mobile adaptation.
- `CinematicBackdrop`: responsive local media, focal treatment, readability veil, and motion controls.
- `FocusCanvas`: stable primary work region.
- `CanvasHeader`: compact title, status, and route actions.
- `ContextRibbon`: active files, connection, mode, filters, and job context.
- `Inspector`: desktop side panel and mobile sheet for Tier 3 detail.
- `ActionDock`: primary command and contextual secondary actions.
- `ArtifactViewport`: reports, documents, SQL, tables, charts, generated outputs, and previews.
- `MotionRoute`: route transition and shared-element coordination.
- `OperationState`: consistent loading, empty, error, offline, permission, and retry states.
- `CommandMenu`: application switching, recent work, navigation, and creation commands.

These components define layout and behavior. Application-specific components supply domain content without recreating the shell.

## 7. Route and Application Architecture

The visible product architecture contains four surfaces only:

1. Public homepage with login access.
2. Authenticated application dashboard.
3. The selected application and its own local submenus.
4. Developer page.

No other destination appears in global navigation.

### 7.1 Public Homepage and Login

- `/` is the single public product surface: a Hype-level animated hero experience with product identity, cinematic application glimpses, concise technical proof, developer entry, and a clear login action.
- Login opens from the homepage as a side panel, modal, or focused overlay so the user does not enter a separate marketing-style authentication screen.
- `/auth` remains a deep-link and session-expiry target, but renders the same homepage authentication overlay rather than a distinct visual page.
- Authenticated users can go directly to `/apps`.
- `/developer` is the only additional public page.
- Existing showcase URLs are removed from visible navigation and redirect to the homepage or relevant authenticated application.

### 7.2 Authenticated Application Dashboard

- `/apps` is the only authenticated top-level dashboard.
- It displays every enabled application from the catalog and lets the user select one.
- One featured application dominates the viewport; the remaining applications use a motion-driven gallery rather than a uniform card grid.
- The dashboard may include restrained live visualizations, recent application status, and meaningful system signals, but it does not become an analytics wall.
- It does not expose application settings, histories, connections, schemas, document management, or workflow configuration.
- Dashboard-to-application navigation uses a shared media and title transition.
- `/apps/[appId]` does not become an extra intermediate screen. It launches or resolves to the application's main screen.

### 7.3 Application Main Screens and Local Submenus

Every application has one main screen containing only the user's primary purpose. Additional capabilities live in that application's local submenu, inspector, tabs, or sheets. They never become global destinations.

The Adaptive Icon Rail switches applications. After an application is selected, its local submenu provides only that application's secondary destinations such as history, settings, connections, documents, or reports.

#### Knowledge

- Main screen: conversation and composer. Mode and selected files live in the context ribbon. Confidence and citation count remain inline with answers.
- Local submenu: chat history and knowledge documents.
- Complete evidence, source excerpts, file selection, and document details open in inspectors or sheets.
- Knowledge history remains separate from every other application's history.

#### AuraSQL

- Main screen: connection-aware `Ask -> Review SQL -> Explore Results` workflow.
- Table and graph views are equal first-class result modes on the main screen.
- Graph mode supports appropriate chart selection, series controls, filters, tooltips, responsive resizing, and export.
- Generated SQL, validation, execution state, and data lineage remain near the active result.
- Local submenu: AuraSQL history, connections, contexts, and AuraSQL-specific settings.
- Schema, recommendations, metadata, and advanced chart configuration open through dedicated inspectors.
- AuraSQL history remains separate from every other application's history.

#### Analysis

- Main screen: guided dataset and objective setup; after launch, the same application surface transitions to live execution and then the report.
- The live state emphasizes current phase, latest meaningful event, and recovery action.
- The report emphasizes executive narrative; charts, methods, diagnostics, and raw outputs use progressive tabs and inspectors.
- Local submenu: analysis-only history and analysis settings.
- Analysis history remains separate from every other application's history.

#### Career

- Main screen: one progressive journey from source evidence and target role through matching, revision, approval, and export.
- Only the current stage is expanded. Completed stages collapse into compact summaries and remain revisitable.
- Evidence, score explanations, unsupported claims, diffs, critiques, and metadata open in contextual review components.
- Generated documents and PDFs use the ArtifactViewport.
- Local submenu: career-only history, resumes, generated artifacts, and career settings.
- Career history remains separate from every other application's history.

#### Workflows and Other Catalog Applications

- Each enabled workflow or future catalog application appears on `/apps` and opens directly into its own primary task screen.
- The main screen shows the active stage, current artifact, current decision, and one next action.
- Local submenu: that application's own history, templates, and settings only when those capabilities exist.
- Logs, retry controls, model detail, and advanced settings remain in the application inspector.

### 7.4 Local Submenu Screen Rules

Application histories, settings, connections, documents, reports, and configuration may use separate internal routes for refresh safety and deep linking, but they remain visibly contained inside the selected application.

- They do not appear as top-level global screens.
- They reuse the application's imagery, accent, rail state, and local submenu.
- They show one list, form, or artifact per screen.
- Histories are never merged across applications.
- Details use an inspector when deep linking is unnecessary.
- A dedicated internal route is used only when state must be shareable or refresh-safe.

## 8. Data and State Flow

- Existing API clients and backend contracts remain unchanged unless a verified frontend defect requires correction.
- The application catalog continues to control enabled navigation destinations.
- The shell reads route metadata from a typed application presentation registry containing media, accent, transition identity, and contextual destinations.
- Application state remains owned by its existing feature modules. Shared shell components receive typed view state rather than importing feature internals.
- URL state is used for shareable filters, active result modes, tabs, and detail selection where appropriate.
- Long-running jobs continue through the global job provider and receive shell-level status without duplicating progress panels on every route.

## 9. Error, Loading, and Empty States

- Loading states preserve the final layout dimensions and use application-specific cinematic sequences.
- Errors explain what failed, preserve user input, and expose a direct retry or recovery action.
- Empty states provide one meaningful starting action and contextual media rather than feature descriptions.
- Offline and authentication-expired states are distinct from server failures.
- Partial data remains visible when safe; an inspector can explain degraded sections.
- Motion never hides error text or delays access to recovery actions.

## 10. Responsive Behavior

- Desktop uses the compact rail and optional right inspector.
- Tablet keeps the rail compact and converts wide inspectors into overlays when required.
- Mobile uses a bottom navigation bar, application sheet, full-height inspectors, and a stable primary action region.
- Dense tables switch to horizontally scrollable or record-detail views without losing fields.
- Charts retain explicit aspect ratios and readable legends.
- Text, buttons, counters, grids, and toolbars have stable responsive dimensions and must not overlap.
- Cinematic media uses art-directed crops per breakpoint rather than a single uncontrolled background crop.

## 11. Accessibility and Performance

- All actions remain keyboard accessible with visible focus states.
- Icon-only controls include tooltips and accessible names.
- Color contrast is validated over every media treatment.
- `prefers-reduced-motion` disables large movement, parallax, autoplay-like sequences, and cursor effects.
- Motion pauses when content is off-screen or the document is hidden.
- Images use `next/image`, explicit dimensions, responsive sources, and local optimized formats.
- Only current-route hero media may be preloaded; other application media loads on intent or navigation.
- Heavy shader, Rive, or Three.js effects are isolated, lazy-loaded, and given static fallbacks.
- Live data and primary interaction must remain responsive while decorative motion is active.

## 12. Testing and Completion Criteria

Each application family is complete only when:

1. Every route in that family uses the new shell and screen hierarchy.
2. Legacy global headers, duplicate sidebars, aurora backgrounds, and conflicting navigation are removed from those routes.
3. Existing user workflows and API behavior pass focused tests.
4. Loading, empty, error, success, and retry states are covered.
5. Desktop, tablet, and mobile screenshots are visually reviewed.
6. No text, action, chart, table, media, or navigation element overlaps.
7. Reduced motion and keyboard navigation are verified.
8. Cinematic assets render locally and do not depend on remote placeholders.
9. Route transitions and persistent media do not cause layout shifts.
10. The frontend test suite, typecheck, lint, and production build pass.

## 13. Delivery Strategy

The full-system rebuild will be implemented in complete vertical phases:

1. Foundation, asset pipeline, motion system, and authenticated shell.
2. Application dashboard and direct application-launch routing.
3. Knowledge Chat and Knowledge Base.
4. AuraSQL and first-class graph system.
5. Analysis configuration, run, history, and report.
6. Career routes and artifact review.
7. Workflows and every application-local submenu route.
8. Homepage/login and developer alignment, cross-route polish, accessibility, performance, and complete visual regression pass.

Each phase must replace its legacy routes end to end. A phase is not complete when only its entry screen has been redesigned.
