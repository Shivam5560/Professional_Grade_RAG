# Workspace Clarity and Career Studio Recovery Design

**Status:** Approved design, pending written-spec review  
**Date:** 2026-07-18  
**Scope:** Shared authenticated workspace surfaces and storytelling, AuraSQL connection/context/query flows, Knowledge Studio chat layout, and full-stack Career Studio recovery

## 1. Decision

Improve the authenticated product through a shared opaque visual foundation, then deeply redesign AuraSQL, Knowledge Studio chat, and Career Studio.

Career Studio becomes the single user-facing home for three explicit workflows:

1. Score an existing resume.
2. Tailor an existing resume only after an explicit user action.
3. Create a resume by entering complete details and rendering it through the existing LaTeX-to-PDF pipeline.

The newer Career evidence model remains the truth and provenance layer beneath those workflows. JSON claim bundles remain supported as an advanced import, but they are not the primary user journey.

## 2. Relationship to Earlier Designs

This design refines rather than discards the approved cinematic product direction in:

- `2026-07-18-nexusmind-hype-cinematic-product-redesign.md`;
- `2026-07-17-nexusmind-cinematic-precision-frontend-design.md`;
- `2026-07-17-specialist-studios-v2-design.md`.

The following earlier decisions remain active:

- one dominant work canvas per route;
- Adaptive Rail and application-local navigation;
- authored cinematic media and Framer Motion interactions;
- progressive disclosure, inspectors, action docks, and artifact viewports;
- evidence-linked Career claims, truthful gaps, approval gates, and revision history;
- reduced-motion behavior and responsive, keyboard-accessible workspaces.

This design supersedes earlier implementation details in four places:

1. Functional surfaces are opaque. Cinematic media may remain around the canvas, but must not show through forms, editors, chats, tables, dialogs, or result surfaces.
2. Career Studio restores scoring, explicit auto-tailoring, and resume creation as first-class user workflows instead of exposing a JSON-first evidence prototype.
3. Career Studio requires narrow backend changes and reuses legacy capabilities. The earlier frontend-only constraint no longer applies to this recovery.
4. The existing LaTeX resume generator is retained and extended rather than removed.

The product continues to target Framer-quality animation in the existing Next.js application using Framer Motion. It is not being migrated to the Framer site builder.

## 3. Goals

1. Make every authenticated screen readable, intentional, and visually coherent.
2. Replace transparent working surfaces with the approved opaque-cinematic direction.
3. Give shared screens a consistent story: purpose, context, current task, outcome, and next action.
4. Keep AuraSQL connection and context creation inside the AuraSQL product shell.
5. Remove browser-native prompts and history-dependent navigation from AuraSQL.
6. Make chat timelines scroll independently while their composers remain fixed and usable.
7. Restore a complete Career Studio for resume scoring, explicit tailoring, and resume creation.
8. Accept real resume files rather than requiring users to construct JSON.
9. Preserve truth, evidence, and approval constraints beneath all Career generation.
10. Reuse proven backend services and avoid parallel implementations of extraction, scoring, tailoring, or PDF generation.

## 4. Non-Goals

- Rebuilding the public homepage or developer page.
- Migrating the product to the Framer site builder.
- Removing cinematic imagery or application-specific motion.
- Automatically modifying a resume after scoring.
- Claiming that an ATS score is a hiring probability.
- Allowing generated content to invent employers, titles, dates, degrees, skills, responsibilities, or metrics.
- Replacing the existing LaTeX generator with a new document engine.
- Performing unrelated backend refactors.

## 5. Shared Visual and Storytelling Foundation

### 5.1 Opaque Cinematic Direction

The selected direction is **Opaque Cinematic**.

- The application canvas uses a solid background in light and dark modes.
- Work panels use fully opaque surface tokens.
- Cinematic images and color fields remain visible only at controlled canvas edges, entry states, or dedicated media regions.
- Forms, tables, editors, chats, dialogs, inspectors, menus, and artifact previews never depend on backdrop blur for legibility.
- Shadows are restrained and communicate layering, not decoration.
- Borders, spacing, and typography create hierarchy before color or animation.

The shared theme introduces explicit surface roles rather than scattered alpha utilities:

- canvas;
- workspace;
- raised panel;
- inset editor;
- overlay/dialog;
- selected or accented surface.

Existing `bg-background/xx`, `bg-card/xx`, `backdrop-blur-*`, `glass-panel`, and similar classes are removed from functional authenticated surfaces as those screens are migrated.

### 5.2 Motion

Motion remains an important part of the product story:

- route and application transitions;
- staged entry and empty-state reveals;
- active navigation indicators;
- inspector and dialog transitions;
- workflow progress, live status, charts, and artifact changes;
- small hover, press, focus, and success feedback.

Active workspaces avoid continuous foreground effects that compete with typing, reading, or data inspection. Reduced-motion mode preserves all information and replaces large movement with immediate state changes or short fades.

### 5.3 Screen Story

Authenticated screens follow one narrative order:

1. **Purpose:** what outcome this screen enables.
2. **Context:** the active files, connection, role, mode, or artifact.
3. **Current task:** the one action or decision in focus.
4. **Outcome:** the visible result, evidence, or progress.
5. **Next action:** the safest useful continuation.

Copy is concise and operational. Storytelling appears in headings, stage descriptions, empty states, progress labels, result summaries, and recovery guidance rather than promotional paragraphs.

### 5.4 Shared Components

Add or refine shared components for:

- opaque workspace and inset surfaces;
- workflow/story headers;
- operation states for empty, loading, success, error, and retry;
- accessible product dialogs and confirmation dialogs;
- fixed or sticky composer/action regions;
- field groups and repeatable structured entries;
- artifact previews and before/after comparisons.

Shared components accept typed content and states. They do not import application-specific clients or own domain state.

## 6. AuraSQL

### 6.1 Connection Flow

`/aurasql/connections/new` and connection editing use the standard AuraSQL shell and opaque form components.

- The form describes why each database detail is required.
- Validation appears beside the relevant field.
- Save progress does not replace the whole screen with a decorative overlay.
- Cancel always returns to `/aurasql/connections`.
- Back returns to `/aurasql/connections` unless the form is part of the post-connection onboarding flow.
- Successful connection creation continues to `/aurasql/contexts/new?connection=<id>` with a clear “Connection saved; choose tables” transition.
- The browser history stack is never treated as the product state machine.

### 6.2 Context Flow

Context creation remains in the AuraSQL shell and uses the selected connection from the URL when valid.

- Connection selection, table filter, selected count, and selected-table summary remain visible.
- Table lists are the only scrollable region when long.
- Context name is required and validated.
- Successful context creation opens `/aurasql/query?context=<id>`.
- Cancel returns to `/aurasql/contexts`.
- The flow preserves selection and errors after a failed save.

### 6.3 In-Query Context Naming

Saving selected tables from the Schema inspector opens an in-product dialog. `window.prompt` is prohibited.

The dialog contains:

- a context name field;
- the active connection;
- selected-table count and compact table summary;
- Cancel and Save actions;
- inline required-name and server errors;
- loading state that prevents duplicate submission without dismissing the dialog.

Updating an existing context uses explicit update copy and does not ask for a new name unless the user chooses Rename.

Browser-native `confirm` calls used by AuraSQL deletion flows are replaced with the shared confirmation dialog.

### 6.4 Query Workspace

The main flow remains `Ask -> Review SQL -> Explore Results`.

- The application viewport is stable.
- The question composer remains fixed within the query workspace.
- Generated SQL and results use the remaining scrollable region.
- The SQL editor may grow only within a bounded height and then scroll internally.
- Connection, context, and dialect remain compact context controls.
- Schema and recommendation details remain in the inspector.
- Table and graph result modes remain first-class.

## 7. Knowledge Studio Chat

Knowledge Studio uses a fixed workspace layout:

- the page and shell do not scroll during an active conversation;
- the message timeline is the only primary scroll container;
- the composer is an opaque footer anchored inside the workspace;
- the textarea grows to a bounded maximum and then scrolls internally;
- attachment and mode controls remain reachable at every message depth;
- mobile safe-area spacing prevents the composer from being covered;
- new messages scroll the timeline, not the document body.

The empty state explains what the user can learn from their evidence, how file context changes an answer, and offers focused starting prompts. Message sources, confidence, and context usage remain visible without overwhelming the conversation.

## 8. Career Studio Product Structure

### 8.1 Entry

`/career` opens a clear choice between three primary workflows:

1. **Score Resume** — inspect an existing resume against a target job without changing it.
2. **Tailor Resume** — explicitly start an evidence-grounded revision for a selected resume and job.
3. **Create Resume** — enter complete details and build a LaTeX-rendered resume.

Recent resumes, drafts, scoring results, and artifacts are accessible through Career-local navigation or an inspector. JSON is placed under **Advanced structured import**.

### 8.2 Resume Intake

Score and Tailor accept `.pdf`, `.doc`, `.docx`, and `.txt`. Advanced import additionally accepts the existing JSON claim bundle.

The server:

1. validates extension, media type, and size;
2. extracts bounded text using the existing resume/document extraction utility;
3. records the uploaded resume through the existing owner-scoped storage path;
4. converts extracted facts into source-linked Career claims;
5. marks automatically inferred claims for review;
6. returns a normalized source/profile response usable by scoring and tailoring.

Encrypted, corrupt, empty, or unsupported files return actionable errors. Raw resume content is not written to general-purpose logs.

### 8.3 Score Resume

The user selects or uploads a resume, pastes a normal job description, and explicitly starts scoring.

The result separates:

- ATS compatibility and parseability;
- requirement coverage and role fit;
- supported strengths;
- missing or weak keywords;
- truthful gaps;
- uncertain extracted evidence;
- practical improvement priorities.

Scoring does not alter the resume. The next actions are **Review evidence**, **Tailor this resume**, or **Return to Career Studio**.

### 8.4 Tailor Resume

Tailoring begins only when the user explicitly selects **Tailor this resume** or starts the Tailor workflow from Career Studio.

The flow is:

1. select a stored resume or upload one;
2. provide the target job description;
3. review score, gaps, and the proposed tailoring strategy;
4. explicitly start generation;
5. inspect evidence-linked before/after changes;
6. approve, request refinement with feedback, or abort;
7. export the approved artifact.

No scoring request, upload completion, or page navigation automatically starts tailoring. Draft assertions must resolve to verified claims. Unsupported content blocks publication.

### 8.5 Create Resume

Create Resume restores and improves the former multi-step ResumeGen form while retaining the existing LaTeX backend and PDF conversion path.

The guided editor supports:

- personal details: full name, email, phone, location, LinkedIn, GitHub, and portfolio;
- professional summary;
- repeatable experience entries: company, position, location, dates, and any number of achievement bullets;
- repeatable education entries: institution, degree, location, dates, and GPA;
- repeatable project entries: title, link, technologies, dates, and any number of highlights;
- dynamic skill categories;
- certifications;
- awards;
- languages;
- optional custom sections.

Users can add, remove, reorder, and revisit sections. The editor provides:

- inline validation;
- local draft recovery/autosave;
- completion summaries per step;
- a real formatted preview rather than only a field-count summary;
- PDF export through the existing LaTeX conversion path;
- `.tex` source export;
- clear fallback guidance when PDF compilation is unavailable.

The generator schema and template are extended additively so current clients and existing payload aliases continue to work.

## 9. Backend Integration

### 9.1 Reuse

The implementation reuses:

- Nexus resume file validation, storage, and text extraction;
- existing resume scoring and analysis services;
- existing auto-tailor workflow and approval/refinement actions;
- Career V2 claims, matching, drafting, truth validation, approvals, and artifacts;
- ResumeGen LaTeX generation and `/api/latex-to-pdf` conversion.

Shared capabilities are extracted behind narrow service adapters where direct route-to-route coupling currently exists. New Career routes do not call legacy HTTP endpoints internally.

### 9.2 Career API Facade

Career Studio receives a coherent owner-scoped API facade for:

- multipart resume source upload;
- plain-text job description parsing;
- scoring start and result retrieval;
- explicit tailoring start, status, refinement, abort, approval, and artifact download;
- resume-creator draft payload validation and LaTeX/PDF rendering.

Existing endpoints may remain during migration, but Career Studio consumes the unified facade. Authoritative user IDs come from authentication, not request bodies.

Long-running extraction, scoring, and tailoring use existing job/run semantics. Idempotency prevents accidental duplicate generation.

### 9.3 Evidence Rules

- Automatically extracted claims begin as inferred unless deterministically supported and explicitly allowed by the domain rule.
- Tailoring uses verified claims only for publishable assertions.
- Every changed bullet retains source claim IDs and before/after text.
- Metrics cannot be invented, increased, transferred, or rounded to appear stronger.
- ATS diagnostics remain distinct from role-fit evidence.
- Final tailored publication requires explicit approval.

## 10. State and Navigation

- Shareable selections use URL state where safe: Career workflow, stored resume, role, AuraSQL connection, and context.
- Secrets, raw resume text, unsaved form values, and job descriptions are not placed in URLs.
- Deterministic route destinations replace `router.back()` for primary workflow navigation.
- Form input survives recoverable errors.
- Long-running jobs reconnect through durable identifiers.
- Create Resume autosave is owner/device scoped and versioned so stale drafts do not silently overwrite newer work.

## 11. Error and Recovery Behavior

Every error state answers three questions: what failed, what was preserved, and what the user can do next.

Required cases include:

- AuraSQL credential or schema failure;
- unavailable database or table metadata;
- duplicate or invalid context name;
- expired authentication;
- resume type, size, encryption, extraction, or empty-text failure;
- scoring or tailoring job failure;
- unsupported claim detected during generation;
- LaTeX validation or PDF conversion failure;
- network interruption during long-running work.

Errors remain inside the relevant opaque work surface. Full-screen blocking overlays are reserved for operations that genuinely prevent all interaction.

## 12. Accessibility, Responsive Behavior, and Performance

- Dialogs trap focus, restore focus on close, close with Escape where safe, and expose accessible names and descriptions.
- Fixed composers respect keyboard navigation, mobile keyboards, and safe areas.
- Every icon-only action has an accessible label and visible tooltip.
- Light and dark surface tokens meet contrast requirements without relying on backdrop content.
- Tables and repeatable resume sections remain usable at narrow widths.
- Reduced motion removes large transitions and background movement.
- Decorative media and motion must not block typing, scrolling, query execution, or artifact preview.
- Resume previews and heavy editors load only when their workflow is active.

## 13. Testing Strategy

### 13.1 Frontend

- shared surface and dialog component tests;
- AuraSQL deterministic navigation tests;
- context naming, save failure, update, and deletion dialog tests;
- AuraSQL query layout tests proving composer and content scroll ownership;
- Knowledge chat layout tests proving timeline-only scrolling and fixed composer behavior;
- Career workflow entry and explicit-tailor tests;
- resume upload type and error tests;
- score-result storytelling and action tests;
- creator field, repeatable section, reorder, autosave, validation, preview, and download tests;
- keyboard and reduced-motion tests;
- responsive browser verification for desktop, tablet, and mobile;
- typecheck and production build.

### 13.2 Backend

- multipart upload validation and owner scoping;
- PDF, DOC, DOCX, and TXT extraction adapters;
- empty, corrupt, encrypted, oversized, and unsupported file cases;
- source-to-claim provenance and inferred-status tests;
- plain-text role parsing tests;
- scoring separation between ATS compatibility and evidence coverage;
- proof that scoring cannot start tailoring;
- explicit tailoring, idempotency, refinement, abort, approval, and publication tests;
- Truth Guardian fabrication tests;
- additive ResumeGen schema compatibility tests;
- LaTeX escaping and new-section rendering tests;
- PDF and `.tex` response tests.

## 14. Acceptance Criteria

The work is complete when:

1. Authenticated functional surfaces no longer use transparent glass treatment in migrated shared components and affected routes.
2. Cinematic imagery and Framer Motion remain present without reducing workspace legibility.
3. Shared storytelling conventions improve authenticated screens, with detailed rewrites in AuraSQL, Knowledge Chat, and Career Studio.
4. AuraSQL create/edit screens remain inside its shell and never depend on browser history for workflow navigation.
5. AuraSQL context naming and deletion use accessible in-product dialogs, not browser prompts or confirms.
6. AuraSQL and Knowledge composers remain visible while only their intended content regions scroll.
7. Career Studio exposes Score, Tailor, and Create as its three primary workflows.
8. PDF, DOC, DOCX, and TXT resumes can enter the Career workflow without JSON preparation.
9. A score operation never changes or tailors a resume.
10. Tailoring begins only after an explicit user action and preserves evidence-linked before/after changes.
11. Resume Creator exposes the approved complete field set and reuses the LaTeX/PDF generator.
12. Existing compatible ResumeGen payloads still render.
13. Unsupported Career assertions block publication.
14. Focused frontend and backend tests, type checks, and production builds pass.
15. Desktop, tablet, mobile, keyboard, dark/light, and reduced-motion behavior receive visual review.

## 15. Delivery Boundaries

Implementation will proceed in dependency order:

1. shared opaque surface and dialog foundations;
2. AuraSQL navigation, forms, dialogs, and fixed query layout;
3. Knowledge Chat fixed layout and storytelling;
4. Career backend adapters and unified API facade;
5. Career Score workflow;
6. explicit Tailor workflow migration;
7. Resume Creator restoration and LaTeX extension;
8. shared-screen storytelling pass;
9. accessibility, responsive, motion, regression, and production verification.

The detailed implementation plan will define exact files, test-first increments, compatibility sequencing, and migration checkpoints.
