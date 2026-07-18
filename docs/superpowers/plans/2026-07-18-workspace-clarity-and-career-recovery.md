# Workspace Clarity and Career Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver opaque authenticated workspaces, correct AuraSQL and chat interaction layouts, and a unified Career Studio for resume scoring, explicit tailoring, and LaTeX resume creation.

**Architecture:** Introduce small shared surface/dialog primitives, then migrate the affected frontend routes without changing their domain ownership. Add a narrow Career facade that composes existing extraction, scoring, tailoring, evidence, and ResumeGen services; keep compatibility endpoints operational while the new `/career` UI becomes the primary entry point.

**Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS, Framer Motion, Vitest/Testing Library, FastAPI, Pydantic v2, SQLAlchemy, pytest

## Global Constraints

- Functional forms, tables, editors, chats, dialogs, inspectors, and result surfaces must be opaque.
- Cinematic imagery and Framer Motion remain, with reduced-motion fallbacks.
- Scoring must never start tailoring or modify a resume.
- Tailoring starts only from an explicit user action and publishable output uses verified evidence.
- Resume upload accepts `.pdf`, `.doc`, `.docx`, and `.txt`; JSON is advanced import only.
- Resume creation reuses and additively extends the existing LaTeX/PDF pipeline.
- Primary workflow navigation must not depend on `router.back()`, `window.prompt`, `window.confirm`, or `window.location.assign`.
- Existing user changes and unrelated worktree files must remain untouched.

---

### Task 1: Opaque Workspace and Accessible Dialog Foundation

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/components/cinematic/CinematicBackdrop.tsx`
- Modify: `frontend/components/shell/FocusCanvas.tsx`
- Modify: `frontend/components/shell/Inspector.tsx`
- Modify: `frontend/components/shell/ActionDock.tsx`
- Create: `frontend/components/ui/dialog.tsx`
- Create: `frontend/components/shell/WorkspaceSurface.tsx`
- Test: `frontend/tests/components/WorkspaceFoundation.test.tsx`

**Interfaces:**
- Produces: `WorkspaceSurface({ tone, className, children })`
- Produces: `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription`, `DialogFooter`
- Produces: CSS tokens `--workspace`, `--workspace-raised`, `--workspace-inset`, `--overlay`

- [ ] **Step 1: Write the failing foundation tests**

```tsx
render(<WorkspaceSurface data-testid="surface">Work</WorkspaceSurface>);
expect(screen.getByTestId("surface")).toHaveClass("bg-workspace");

render(<Dialog open><DialogContent><DialogTitle>Name context</DialogTitle></DialogContent></Dialog>);
expect(screen.getByRole("dialog", { name: "Name context" })).toBeVisible();
```

- [ ] **Step 2: Run the tests and confirm missing imports/classes**

Run: `cd frontend && npm test -- --run tests/components/WorkspaceFoundation.test.tsx`  
Expected: FAIL because the new components and surface utility do not exist.

- [ ] **Step 3: Implement tokens and primitives**

```tsx
export function WorkspaceSurface({ children, className, tone = "default", ...props }: Props) {
  return <div className={cn("bg-workspace text-foreground", tone === "inset" && "bg-workspace-inset", tone === "raised" && "bg-workspace-raised", className)} {...props}>{children}</div>;
}
```

Use Radix Dialog semantics with an opaque `bg-overlay` content surface, focus trapping, Escape handling, and focus restoration. Change the cinematic veil so artwork remains at canvas edges but the FocusCanvas content region receives a solid workspace layer. Remove backdrop blur from Inspector and ActionDock content surfaces.

- [ ] **Step 4: Run focused tests and typecheck**

Run: `cd frontend && npm test -- --run tests/components/WorkspaceFoundation.test.tsx tests/components/ShellPrimitives.test.tsx && npm run typecheck`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/globals.css frontend/components/cinematic/CinematicBackdrop.tsx frontend/components/shell frontend/components/ui/dialog.tsx frontend/tests/components/WorkspaceFoundation.test.tsx
git commit -m "feat(frontend): add opaque workspace foundation"
```

### Task 2: AuraSQL Navigation, Forms, and Product Dialogs

**Files:**
- Modify: `frontend/app/aurasql/connections/new/page.tsx`
- Modify: `frontend/app/aurasql/connections/[id]/page.tsx`
- Modify: `frontend/app/aurasql/connections/page.tsx`
- Modify: `frontend/app/aurasql/contexts/new/page.tsx`
- Modify: `frontend/app/aurasql/contexts/page.tsx`
- Modify: `frontend/app/aurasql/query/page.tsx`
- Create: `frontend/components/aurasql/ContextNameDialog.tsx`
- Create: `frontend/components/aurasql/DeleteAuraSqlResourceDialog.tsx`
- Test: `frontend/tests/components/AuraSqlFlows.test.tsx`

**Interfaces:**
- Produces: `ContextNameDialog({ open, connectionLabel, selectedTables, initialName, saving, error, onCancel, onSave })`
- Produces: `DeleteAuraSqlResourceDialog({ open, resourceName, resourceType, deleting, error, onCancel, onConfirm })`

- [ ] **Step 1: Write failing navigation and dialog tests**

```tsx
expect(screen.getByRole("button", { name: "Cancel" })).toHaveAttribute("data-destination", "/aurasql/connections");
await user.click(screen.getByRole("button", { name: "Save context" }));
expect(screen.getByRole("dialog", { name: "Name schema context" })).toBeVisible();
expect(window.prompt).not.toHaveBeenCalled();
```

Add a source scan assertion ensuring the affected files contain none of `router.back()`, `window.prompt`, `window.confirm`, or `window.location.assign`.

- [ ] **Step 2: Run the tests and verify current legacy behavior fails**

Run: `cd frontend && npm test -- --run tests/components/AuraSqlFlows.test.tsx`  
Expected: FAIL on browser-native navigation/dialog behavior.

- [ ] **Step 3: Migrate connection and context forms into `AuraSqlPage`**

Use deterministic destinations:

```tsx
<Button type="button" variant="ghost" data-destination="/aurasql/connections" onClick={() => router.push("/aurasql/connections")}>Cancel</Button>
```

After connection creation, route to `/aurasql/contexts/new?connection=${connection.id}`. After context creation, route to `/aurasql/query?context=${context.id}`. Preserve form and table selections on request failure.

- [ ] **Step 4: Replace prompt/confirm flows**

Open `ContextNameDialog` from the Schema inspector, require a trimmed name, preserve it after server failure, and dismiss only after a successful save. Use `DeleteAuraSqlResourceDialog` for connection/context deletion and surface request errors inside it.

- [ ] **Step 5: Run focused tests and typecheck**

Run: `cd frontend && npm test -- --run tests/components/AuraSqlFlows.test.tsx tests/components/AuraSqlResultViewport.test.tsx && npm run typecheck`  
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/app/aurasql frontend/components/aurasql frontend/tests/components/AuraSqlFlows.test.tsx
git commit -m "feat(aurasql): repair connection and context workflows"
```

### Task 3: Fixed AuraSQL and Knowledge Composers

**Files:**
- Modify: `frontend/components/shell/FocusCanvas.tsx`
- Modify: `frontend/app/aurasql/query/page.tsx`
- Modify: `frontend/app/chat/page.tsx`
- Modify: `frontend/components/chat/ChatInterface.tsx`
- Modify: `frontend/components/chat/MessageInput.tsx`
- Modify: `frontend/components/chat/MessageList.tsx`
- Test: `frontend/tests/components/FixedComposerLayouts.test.tsx`

**Interfaces:**
- Produces: a stable `data-scroll-owner="messages|query-results"` region
- Produces: a stable `data-fixed-composer="knowledge|aurasql"` region

- [ ] **Step 1: Write failing scroll-ownership tests**

```tsx
expect(screen.getByTestId("knowledge-composer")).toHaveAttribute("data-fixed-composer", "knowledge");
expect(screen.getByTestId("knowledge-message-scroll")).toHaveAttribute("data-scroll-owner", "messages");
expect(screen.getByTestId("aurasql-composer")).toHaveAttribute("data-fixed-composer", "aurasql");
```

- [ ] **Step 2: Run tests and observe missing layout contracts**

Run: `cd frontend && npm test -- --run tests/components/FixedComposerLayouts.test.tsx`  
Expected: FAIL.

- [ ] **Step 3: Implement viewport and internal scroll layout**

Use `h-[calc(100svh-var(--shell-offset))] min-h-0 overflow-hidden` on the workspace, `min-h-0 flex-1 overflow-y-auto` only on message/query content, and an opaque `shrink-0 border-t bg-workspace-raised` composer. Bound textareas at `max-h-48 overflow-y-auto`.

- [ ] **Step 4: Run layout and chat regression tests**

Run: `cd frontend && npm test -- --run tests/components/FixedComposerLayouts.test.tsx tests/components/KnowledgeSurfaces.test.ts && npm run typecheck`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/shell/FocusCanvas.tsx frontend/app/aurasql/query/page.tsx frontend/app/chat/page.tsx frontend/components/chat frontend/tests/components/FixedComposerLayouts.test.tsx
git commit -m "fix(frontend): keep chat and query composers fixed"
```

### Task 4: Career Resume Intake and Unified Backend Facade

**Files:**
- Create: `backend/app/studios/career/extraction/resume_source.py`
- Create: `backend/app/studios/career/extraction/__init__.py`
- Modify: `backend/app/studios/career/api/contracts.py`
- Modify: `backend/app/studios/career/api/service.py`
- Modify: `backend/app/studios/career/api/router.py`
- Test: `backend/tests/studios/career/api/test_resume_intake.py`

**Interfaces:**
- Produces: `extract_resume_source(filename: str, content: bytes) -> ExtractedResumeSource`
- Produces: `POST /api/v2/career/sources/upload` multipart endpoint
- Produces: `POST /api/v2/career/roles/parse` accepting `{ "job_description": string }`

- [ ] **Step 1: Write failing upload contract tests**

```python
response = client.post("/api/v2/career/sources/upload", files={"file": ("resume.txt", b"Jane Doe\nData Engineer", "text/plain")})
assert response.status_code == 201
assert response.json()["source"]["filename"] == "resume.txt"
assert all(item["claim"]["verification_status"] == "inferred" for item in response.json()["claims"])
```

Cover unsupported extension, empty content, oversized input, owner scoping, and parser failure.

- [ ] **Step 2: Run the focused backend tests**

Run: `cd backend && pytest tests/studios/career/api/test_resume_intake.py -q`  
Expected: FAIL with missing route/module.

- [ ] **Step 3: Implement bounded extraction adapter**

Reuse `validate_file_extension`, `validate_file_size`, and `extract_text_from_file`. Store uploads through an explicit temporary file with a validated suffix and guaranteed cleanup. Convert extracted resume sections into bounded, source-spanned inferred claims using a Career-owned adapter; do not log raw text.

- [ ] **Step 4: Add authenticated multipart and role-parse routes**

The route derives `owner_id` from authentication, never accepts an authoritative user ID, and returns the existing `SourceIngestionResponse` shape. Plain job-description parsing returns normalized requirements plus source spans.

- [ ] **Step 5: Run Career backend regressions**

Run: `cd backend && pytest tests/studios/career -q`  
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/studios/career backend/tests/studios/career/api/test_resume_intake.py
git commit -m "feat(career): accept resume files and plain job descriptions"
```

### Task 5: ResumeGen Additive Schema and Rendering Extension

**Files:**
- Modify: `backend/app/api/routes/resumegen.py`
- Modify: `backend/app/services/resume_generator.py`
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/lib/api.ts`
- Test: `backend/tests/api/test_resumegen_extended.py`
- Test: `frontend/tests/studios/resume-creator-client.test.ts`

**Interfaces:**
- Extends: `ResumeGenData` with phone, portfolio, summary, locations, dates, links, certifications, awards, languages, custom sections, and `section_order`
- Preserves: existing aliases `experience/experiences`, `position/title`, `duration/dates`, `linkedin/linkedin_url`, and `github/github_url`

- [ ] **Step 1: Write failing compatibility and new-section tests**

```python
latex = generate_resume_latex({"name": "Jane", "email": "j@x.com", "phone": "+1 555", "summary": "Data leader", "certifications": [{"name": "AWS", "issuer": "Amazon"}]})
assert "+1 555" in latex
assert "Professional Summary" in latex
assert "Certifications" in latex
```

Also assert an old payload still produces Experience, Education, Projects, and Additional sections.

- [ ] **Step 2: Run backend and frontend client tests**

Run: `cd backend && pytest tests/api/test_resumegen_extended.py -q`  
Run: `cd frontend && npm test -- --run tests/studios/resume-creator-client.test.ts`  
Expected: FAIL on missing fields/sections.

- [ ] **Step 3: Extend Pydantic and TypeScript models additively**

Use default-empty optional fields and `extra="ignore"`; normalize old and new aliases in `normalizeResumeGenPayload`. Add safe section builders and render them according to validated `section_order`, appending any populated section omitted from the order.

- [ ] **Step 4: Run focused tests**

Run: `cd backend && pytest tests/api/test_resumegen_extended.py -q && cd ../frontend && npm test -- --run tests/studios/resume-creator-client.test.ts && npm run typecheck`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routes/resumegen.py backend/app/services/resume_generator.py backend/tests/api/test_resumegen_extended.py frontend/lib/types.ts frontend/lib/api.ts frontend/tests/studios/resume-creator-client.test.ts
git commit -m "feat(career): extend latex resume creator schema"
```

### Task 6: Unified Career Studio Frontend

**Files:**
- Replace: `frontend/app/career/page.tsx`
- Create: `frontend/components/studios/career/CareerHome.tsx`
- Create: `frontend/components/studios/career/ResumeIntake.tsx`
- Create: `frontend/components/studios/career/ScoreWorkspace.tsx`
- Create: `frontend/components/studios/career/TailorWorkspace.tsx`
- Create: `frontend/components/studios/career/ResumeCreator.tsx`
- Create: `frontend/components/studios/career/ResumePreview.tsx`
- Create: `frontend/lib/studios/career/creator-reducer.ts`
- Modify: `frontend/lib/studios/career/client.ts`
- Test: `frontend/tests/components/CareerStudioUnified.test.tsx`
- Test: `frontend/tests/studios/career-creator-reducer.test.ts`

**Interfaces:**
- Produces: URL workflow values `score`, `tailor`, `create`
- Produces: `CareerStudioClient.uploadResume(file)`, `parseRole(jobDescription)`, scoring/tailoring facade methods
- Produces: `ResumeCreatorState` and pure reducer actions for add/remove/update/reorder/autosave hydration

- [ ] **Step 1: Write failing workflow and explicit-tailor tests**

```tsx
expect(screen.getByRole("button", { name: "Score Resume" })).toBeVisible();
expect(screen.getByRole("button", { name: "Tailor Resume" })).toBeVisible();
expect(screen.getByRole("button", { name: "Create Resume" })).toBeVisible();
await user.click(screen.getByRole("button", { name: "Run score" }));
expect(mockStartTailor).not.toHaveBeenCalled();
```

Creator tests cover every approved field group, repeatable entries, reorder, validation, preview, autosave hydration, PDF, and `.tex` actions.

- [ ] **Step 2: Run focused Career tests**

Run: `cd frontend && npm test -- --run tests/components/CareerStudioUnified.test.tsx tests/studios/career-creator-reducer.test.ts`  
Expected: FAIL because the unified components do not exist.

- [ ] **Step 3: Implement Career home and intake**

Render three opaque workflow choices with outcome-led copy. `ResumeIntake` accepts PDF/DOC/DOCX/TXT and hides JSON behind Advanced Import. Use normal job-description textareas. Keep upload/extraction/score/tailor progress and errors inside the active workspace.

- [ ] **Step 4: Implement Score and explicit Tailor workspaces**

Score shows ATS compatibility separately from evidence coverage, strengths, gaps, keywords, and review actions. The only bridge to tailoring is an explicit `Tailor this resume` action followed by a strategy review and `Start tailoring` confirmation.

- [ ] **Step 5: Implement Resume Creator and preview**

Use the pure reducer for all approved field groups and section order. Persist a versioned draft in local storage, render a real HTML resume preview, and call the existing PDF/LaTeX client methods. Do not add a second renderer.

- [ ] **Step 6: Run Career frontend regressions and typecheck**

Run: `cd frontend && npm test -- --run tests/components/CareerStudioUnified.test.tsx tests/components/CareerExperience.test.tsx tests/studios/career-creator-reducer.test.ts tests/studios/career-client.test.ts && npm run typecheck`  
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/app/career/page.tsx frontend/components/studios/career frontend/lib/studios/career frontend/tests/components/CareerStudioUnified.test.tsx frontend/tests/studios/career-creator-reducer.test.ts
git commit -m "feat(career): unify scoring tailoring and resume creation"
```

### Task 7: Shared Storytelling Pass and End-to-End Verification

**Files:**
- Modify: affected authenticated route copy and opaque surface usage under `frontend/app/`
- Modify: `frontend/lib/presentation/registry.ts`
- Modify: focused frontend tests as required by copy/accessibility changes
- Test: `frontend/e2e/cinematic-shell.spec.ts`
- Test: `frontend/e2e/career-studio.spec.ts`
- Test: `frontend/e2e/aurasql-workspace.spec.ts`

**Interfaces:**
- Consumes: Tasks 1–6 shared components and workflows
- Produces: verified purpose/context/task/outcome/next-action story on authenticated routes

- [ ] **Step 1: Add failing route-level acceptance tests**

Assert the affected routes expose one primary heading, current context, primary action, actionable empty/error state, opaque workspace marker, and accessible names. Add browser layout assertions for fixed composers at desktop and mobile sizes.

- [ ] **Step 2: Run focused E2E tests**

Run: `cd frontend && npx playwright test e2e/cinematic-shell.spec.ts e2e/career-studio.spec.ts e2e/aurasql-workspace.spec.ts`  
Expected: FAIL on incomplete storytelling/layout assertions.

- [ ] **Step 3: Complete the shared storytelling and opacity migration**

Apply concise purpose/context/outcome copy and `WorkspaceSurface` to remaining shared authenticated screen regions reached by the shell. Remove glass utilities from affected routes while preserving cinematic edge media and motion.

- [ ] **Step 4: Run full verification**

Run: `cd backend && pytest tests/studios/career tests/api/test_resumegen_extended.py -q`  
Run: `cd frontend && npm test && npm run typecheck && npm run build`  
Run: `cd frontend && npx playwright test e2e/cinematic-shell.spec.ts e2e/career-studio.spec.ts e2e/aurasql-workspace.spec.ts`  
Expected: all commands PASS.

- [ ] **Step 5: Review responsive and accessible behavior**

Visually inspect Career, AuraSQL query/context/connection, and Knowledge Chat at desktop, tablet, and mobile widths in light, dark, and reduced-motion modes. Confirm no overlapping controls, background bleed-through, lost focus, document scrolling, or hidden composers.

- [ ] **Step 6: Commit**

```bash
git add frontend backend
git commit -m "feat: complete workspace clarity and career recovery"
```

## Plan Self-Review

- Spec coverage: shared opacity/motion/storytelling, AuraSQL, fixed composers, Career file intake, score/tailor/create, evidence rules, LaTeX reuse, errors, accessibility, and verification each map to Tasks 1–7.
- Type consistency: `ResumeGenData`, Career client methods, dialog props, and fixed-layout data attributes are introduced before their consumers.
- Scope: public homepage and unrelated backend domains remain excluded.
- Migration safety: compatibility routes and payload aliases remain until unified Career tests pass.
