# Cinematic Entry, Shell, and Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared cinematic motion/media foundation, homepage login overlay, authenticated Adaptive Icon Rail shell, and direct-launch application dashboard that every later application migration will consume.

**Architecture:** A typed presentation registry maps backend application manifests and route prefixes to authored media, accent, icon, and local-menu metadata. Public routes render without live API providers; authenticated routes mount one `CinematicAppShell` around existing feature content. `/apps` becomes the only authenticated dashboard and `/apps/[appId]` redirects directly to the manifest's `frontend_route`.

**Tech Stack:** Next.js 14 App Router, React 18, TypeScript, Tailwind CSS, Framer Motion 12, Radix/shadcn primitives, Lucide icons, Zustand, Vitest/Testing Library, Playwright, Codex image generation, `next/image`

## Global Constraints

- Keep the visible product architecture limited to homepage/login, application dashboard, selected application with local submenus, and developer page.
- Histories, settings, connections, documents, and reports remain separate inside their owning application; never create a global history or settings center.
- Every screen exposes one primary task; advanced capabilities use local submenus, inspectors, tabs, or sheets.
- Persistent cinematic media must remain readable under authored contrast veils in both dark and light modes.
- Use local optimized assets under `frontend/public/images/cinematic/`; production must not depend on remote placeholder URLs.
- Use Framer Motion for route, layout, navigation, media, gesture, and feedback motion.
- Respect `prefers-reduced-motion`, data saver, document visibility, and constrained devices.
- Do not change backend API contracts.
- Do not leave a migrated route using the legacy `Header`, aurora background, or duplicate global sidebar.
- No nested cards; page sections remain unframed and cards are reserved for repeated records or discrete artifacts.
- Verify desktop `1440x900`, tablet `1024x768`, and mobile `412x915` without overlap.

## Plan Boundary

This plan produces a working entry and shell foundation. The following independent plans must migrate application internals end to end:

1. Knowledge Chat and Knowledge Base.
2. AuraSQL, including first-class table and graph results.
3. Analysis setup, execution, report, and local history.
4. Career workflow, artifacts, and local submenus.
5. Workflows and remaining application-local routes.

---

### Task 1: Typed Application Presentation Registry

**Files:**
- Create: `frontend/lib/presentation/types.ts`
- Create: `frontend/lib/presentation/registry.ts`
- Test: `frontend/tests/lib/presentation-registry.test.ts`

**Interfaces:**
- Consumes: `AppManifest` from `frontend/lib/apps/types.ts`.
- Produces: `ApplicationPresentation`, `LocalDestination`, `presentationForApp(app)`, `presentationForPath(pathname)`, and `directApplicationRoute(app)`.

- [ ] **Step 1: Write the failing registry tests**

```ts
import { describe, expect, it } from "vitest";
import {
  directApplicationRoute,
  presentationForApp,
  presentationForPath,
} from "@/lib/presentation/registry";
import type { AppManifest } from "@/lib/apps/types";

const app = (id: string, frontend_route: string): AppManifest => ({
  id, frontend_route, name: id, version: "1.0.0", summary: "Summary",
  category: "test", icon: "blocks", backend_route_prefixes: [],
  backend_router_ids: [], required_capabilities: [], optional_capabilities: [],
  required_permissions: [], required_env_keys: [], dependencies: [],
  demo_scenarios: [], health_check_id: id, packaging_paths: [],
});

describe("application presentation registry", () => {
  it("maps enabled manifests to authored application identities", () => {
    expect(presentationForApp(app("aurasql", "/aurasql"))).toMatchObject({
      id: "aurasql", accent: "data", mainRoute: "/aurasql",
      localDestinations: expect.arrayContaining([
        expect.objectContaining({ label: "History", href: "/aurasql/history" }),
      ]),
    });
  });

  it("uses the longest matching application route", () => {
    expect(presentationForPath("/analysis/42/report").id).toBe("analysis");
  });

  it("launches catalog entries directly into their frontend route", () => {
    expect(directApplicationRoute(app("knowledge-studio", "/chat"))).toBe("/chat");
  });
});
```

- [ ] **Step 2: Run the registry tests and verify RED**

Run: `cd frontend && npm test -- tests/lib/presentation-registry.test.ts`

Expected: FAIL because `@/lib/presentation/registry` does not exist.

- [ ] **Step 3: Define presentation types**

```ts
// frontend/lib/presentation/types.ts
import type { LucideIcon } from "lucide-react";

export type ApplicationAccent = "signal" | "data" | "copper" | "career" | "neutral";

export interface LocalDestination {
  label: string;
  href: string;
  icon: LucideIcon;
  matches(pathname: string): boolean;
}

export interface ApplicationPresentation {
  id: string;
  name: string;
  shortName: string;
  mainRoute: string;
  routePrefixes: readonly string[];
  accent: ApplicationAccent;
  media: { dark: string; light: string; alt: string; focalPoint: string };
  headline: string;
  localDestinations: readonly LocalDestination[];
}
```

- [ ] **Step 4: Implement the registry with explicit application ownership**

```ts
// frontend/lib/presentation/registry.ts
import { BookOpen, BriefcaseBusiness, Database, FileText, History, Settings2 } from "lucide-react";
import type { AppManifest } from "@/lib/apps/types";
import type { ApplicationPresentation, LocalDestination } from "./types";

const destination = (label: string, href: string, icon: LocalDestination["icon"]): LocalDestination => ({
  label, href, icon,
  matches: (pathname) => pathname === href || pathname.startsWith(`${href}/`),
});

const presentations: readonly ApplicationPresentation[] = [
  {
    id: "knowledge-studio", name: "Knowledge Studio", shortName: "Knowledge",
    mainRoute: "/chat", routePrefixes: ["/chat", "/knowledge-base"], accent: "signal",
    media: { dark: "/images/cinematic/knowledge-dark.jpg", light: "/images/cinematic/knowledge-light.jpg", alt: "Layered archival material illuminated by connected evidence", focalPoint: "62% 42%" },
    headline: "Evidence becomes understanding.",
    localDestinations: [destination("Chat", "/chat", BookOpen), destination("History", "/chat?panel=history", History), destination("Documents", "/knowledge-base", FileText)],
  },
  {
    id: "aurasql", name: "AuraSQL", shortName: "AuraSQL",
    mainRoute: "/aurasql", routePrefixes: ["/aurasql"], accent: "data",
    media: { dark: "/images/cinematic/aurasql-dark.jpg", light: "/images/cinematic/aurasql-light.jpg", alt: "Architectural data structures receding through luminous space", focalPoint: "70% 48%" },
    headline: "Ask the business. Inspect the truth.",
    localDestinations: [destination("Query", "/aurasql", Database), destination("History", "/aurasql/history", History), destination("Connections", "/aurasql/connections", Settings2)],
  },
  {
    id: "analysis", name: "Data Analyst Studio", shortName: "Analysis",
    mainRoute: "/analysis", routePrefixes: ["/analysis"], accent: "copper",
    media: { dark: "/images/cinematic/analysis-dark.jpg", light: "/images/cinematic/analysis-light.jpg", alt: "Observed structures separating clear signal from surrounding complexity", focalPoint: "68% 38%" },
    headline: "See the signal inside the noise.",
    localDestinations: [destination("Analyze", "/analysis", FileText), destination("History", "/analysis/history", History)],
  },
  {
    id: "career-studio", name: "Career Studio", shortName: "Career",
    mainRoute: "/career", routePrefixes: ["/career", "/nexus"], accent: "career",
    media: { dark: "/images/cinematic/career-dark.jpg", light: "/images/cinematic/career-light.jpg", alt: "Human craft and verified documents arranged as a precise professional narrative", focalPoint: "72% 44%" },
    headline: "Turn verified work into opportunity.",
    localDestinations: [destination("Workspace", "/career", BriefcaseBusiness), destination("Resumes", "/nexus/resumes", FileText), destination("Settings", "/career?panel=settings", Settings2)],
  },
];

const fallback: ApplicationPresentation = {
  id: "platform", name: "NexusMind", shortName: "Workspace", mainRoute: "/apps",
  routePrefixes: ["/apps", "/workflows"], accent: "neutral",
  media: { dark: "/images/cinematic/platform-dark.jpg", light: "/images/cinematic/platform-light.jpg", alt: "A precise cinematic system of connected workspaces", focalPoint: "65% 44%" },
  headline: "Choose an intent. Enter the system.", localDestinations: [],
};

export function presentationForApp(app: AppManifest): ApplicationPresentation {
  return presentations.find((item) => item.id === app.id || item.mainRoute === app.frontend_route) ?? { ...fallback, id: app.id, name: app.name, shortName: app.name, mainRoute: app.frontend_route };
}

export function presentationForPath(pathname: string): ApplicationPresentation {
  return presentations.flatMap((item) => item.routePrefixes.map((prefix) => ({ item, prefix }))).filter(({ prefix }) => pathname === prefix || pathname.startsWith(`${prefix}/`)).sort((a, b) => b.prefix.length - a.prefix.length)[0]?.item ?? fallback;
}

export const directApplicationRoute = (app: AppManifest): string => app.frontend_route;
```

- [ ] **Step 5: Run the registry tests and verify GREEN**

Run: `cd frontend && npm test -- tests/lib/presentation-registry.test.ts`

Expected: 3 tests PASS.

- [ ] **Step 6: Commit the registry**

```bash
git add frontend/lib/presentation frontend/tests/lib/presentation-registry.test.ts
git commit -m "feat(frontend): add application presentation registry"
```

---

### Task 2: Shared Motion and Media Primitives

**Files:**
- Create: `frontend/lib/motion.ts`
- Create: `frontend/components/motion/MotionRoute.tsx`
- Create: `frontend/components/cinematic/CinematicBackdrop.tsx`
- Test: `frontend/tests/components/CinematicBackdrop.test.tsx`

**Interfaces:**
- Consumes: `ApplicationPresentation.media`, `useCinematicEffects()`, and appearance state from the document root.
- Produces: `motionTokens`, `MotionRoute`, and `CinematicBackdrop`.

- [ ] **Step 1: Write the failing backdrop test**

```tsx
import { render, screen } from "@testing-library/react";
import { CinematicBackdrop } from "@/components/cinematic/CinematicBackdrop";

vi.mock("@/hooks/useCinematicEffects", () => ({ useCinematicEffects: () => ({ enabled: true, visible: true }) }));

it("renders local dark and light cinematic sources with a readability veil", () => {
  render(<CinematicBackdrop media={{ dark: "/dark.webp", light: "/light.webp", alt: "Authored scene", focalPoint: "70% 40%" }} />);
  expect(screen.getByAltText("Authored scene")).toHaveAttribute("src", expect.stringContaining("dark.webp"));
  expect(screen.getByTestId("cinematic-veil")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test and verify RED**

Run: `cd frontend && npm test -- tests/components/CinematicBackdrop.test.tsx`

Expected: FAIL because `CinematicBackdrop` does not exist.

- [ ] **Step 3: Add shared motion tokens**

```ts
// frontend/lib/motion.ts
export const motionTokens = {
  ease: [0.22, 1, 0.36, 1] as const,
  route: { duration: 0.72 },
  reveal: { duration: 0.58 },
  quick: { duration: 0.2 },
  spring: { type: "spring" as const, stiffness: 260, damping: 30, mass: 0.8 },
};

export const routeVariants = {
  initial: { opacity: 0, y: 16, filter: "blur(10px)" },
  enter: { opacity: 1, y: 0, filter: "blur(0px)" },
  exit: { opacity: 0, y: -10, filter: "blur(8px)" },
};
```

- [ ] **Step 4: Implement `MotionRoute` and `CinematicBackdrop`**

```tsx
// frontend/components/motion/MotionRoute.tsx
"use client";
import { motion, useReducedMotion } from "framer-motion";
import { routeVariants, motionTokens } from "@/lib/motion";

export function MotionRoute({ routeKey, children }: { routeKey: string; children: React.ReactNode }) {
  const reduced = useReducedMotion();
  return <motion.div key={routeKey} initial={reduced ? false : "initial"} animate="enter" exit="exit" variants={reduced ? { enter: { opacity: 1 } } : routeVariants} transition={{ ...motionTokens.route, ease: motionTokens.ease }} className="min-h-full">{children}</motion.div>;
}
```

```tsx
// frontend/components/cinematic/CinematicBackdrop.tsx
"use client";
import { getImageProps } from "next/image";
import { motion } from "framer-motion";
import { useCinematicEffects } from "@/hooks/useCinematicEffects";
import type { ApplicationPresentation } from "@/lib/presentation/types";

export function CinematicBackdrop({ media }: { media: ApplicationPresentation["media"] }) {
  const effects = useCinematicEffects();
  const common = { alt: media.alt, fill: true, sizes: "100vw", className: "object-cover", style: { objectPosition: media.focalPoint } } as const;
  const dark = getImageProps({ ...common, src: media.dark, priority: true }).props;
  const light = getImageProps({ ...common, src: media.light, priority: true }).props;
  return <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-background">
    <motion.div animate={effects.enabled && effects.visible ? { scale: [1.02, 1.075], x: [0, -12] } : undefined} transition={{ duration: 18, repeat: Infinity, repeatType: "mirror", ease: "easeInOut" }} className="absolute inset-0">
      <picture><source media="(prefers-color-scheme: light)" srcSet={light.srcSet} /><img {...dark} alt={media.alt} /></picture>
    </motion.div>
    <div data-testid="cinematic-veil" className="absolute inset-0 bg-[linear-gradient(105deg,hsl(var(--background)/.98)_0%,hsl(var(--background)/.86)_48%,hsl(var(--background)/.48)_100%)]" />
    <div className="absolute inset-0 bg-noise opacity-20 mix-blend-soft-light" />
  </div>;
}
```

- [ ] **Step 5: Run focused tests and typecheck**

Run: `cd frontend && npm test -- tests/components/CinematicBackdrop.test.tsx && npm run typecheck`

Expected: test PASS and TypeScript exits 0. If `next/image` rewriting changes the assertion, assert `src` contains the encoded filename rather than mocking the component.

- [ ] **Step 6: Commit motion primitives**

```bash
git add frontend/lib/motion.ts frontend/components/motion frontend/components/cinematic frontend/tests/components/CinematicBackdrop.test.tsx
git commit -m "feat(frontend): add cinematic motion primitives"
```

---

### Task 3: Original Cinematic Asset Collection

**Files:**
- Create: `frontend/public/images/cinematic/platform-dark.jpg`
- Create: `frontend/public/images/cinematic/platform-light.jpg`
- Create: `frontend/public/images/cinematic/knowledge-dark.jpg`
- Create: `frontend/public/images/cinematic/knowledge-light.jpg`
- Create: `frontend/public/images/cinematic/aurasql-dark.jpg`
- Create: `frontend/public/images/cinematic/aurasql-light.jpg`
- Create: `frontend/public/images/cinematic/analysis-dark.jpg`
- Create: `frontend/public/images/cinematic/analysis-light.jpg`
- Create: `frontend/public/images/cinematic/career-dark.jpg`
- Create: `frontend/public/images/cinematic/career-light.jpg`
- Create: `frontend/public/images/cinematic/manifest.json`
- Modify: `frontend/next.config.js`
- Test: `frontend/tests/lib/cinematic-assets.test.ts`

**Interfaces:**
- Consumes: paths defined by `frontend/lib/presentation/registry.ts`.
- Produces: local 16:9 desktop masters with safe focal regions and documented prompts.

- [ ] **Step 1: Write the failing asset-contract test**

```ts
import { access, readFile } from "node:fs/promises";
import path from "node:path";
import { expect, it } from "vitest";

it("ships every cinematic asset locally with prompt metadata", async () => {
  const root = path.resolve("public/images/cinematic");
  const manifest = JSON.parse(await readFile(path.join(root, "manifest.json"), "utf8"));
  expect(manifest.assets).toHaveLength(10);
  for (const asset of manifest.assets) {
    expect(asset.prompt.length).toBeGreaterThan(80);
    await expect(access(path.join(root, asset.file))).resolves.toBeUndefined();
  }
});
```

- [ ] **Step 2: Run the test and verify RED**

Run: `cd frontend && npm test -- tests/lib/cinematic-assets.test.ts`

Expected: FAIL with `ENOENT` for `manifest.json`.

- [ ] **Step 3: Generate the five dark masters with the imagegen skill**

Use the exact shared direction below, replacing `[SUBJECT]` for platform, knowledge, AuraSQL, analysis, and career:

```text
Create a premium cinematic editorial photograph for a sophisticated AI product interface. Subject: [SUBJECT]. Ultra-wide 16:9 composition, architectural depth, graphite and pearl material palette with restrained mint/cyan/copper light depending on the subject, realistic physical texture, clear focal subject positioned in the right 40 percent, quiet low-detail negative space across the left 55 percent for readable UI, no text, no logos, no screens, no purple gradient, no stock-photo staging, no bokeh blobs. Dark authored exposure, high dynamic range, precise and elegant rather than futuristic cliché.
```

Subject replacements:

- Platform: `interconnected workspaces expressed as monumental precise architecture`.
- Knowledge: `layered archival material and illuminated evidence connections`.
- AuraSQL: `structured architectural grids and flowing relational data`.
- Analysis: `observational structures separating a strong signal from surrounding complexity`.
- Career: `human craft, verified documents, and professional transformation without a posed portrait`.

Expected: five generated bitmap masters with consistent art direction and readable left-side safe areas.

- [ ] **Step 4: Generate the five light masters**

Reuse the exact prompts with this final sentence appended:

```text
Light authored exposure using porcelain, paper, ink, forest mint, deep cyan, and oxidized copper; preserve contrast and physical depth without beige monotony.
```

Expected: five light masters that are independent compositions, not inverted dark images.

- [ ] **Step 5: Optimize and record the assets**

Run from `frontend` after placing generated PNG masters in `/tmp/nexusmind-cinematic/`:

```bash
mkdir -p public/images/cinematic
for file in /tmp/nexusmind-cinematic/*.png; do
  name=$(basename "$file" .png)
  sips --resampleWidth 2400 -s format jpeg -s formatOptions 88 "$file" --out "public/images/cinematic/${name}.jpg"
done
```

Add `images: { formats: ["image/avif", "image/webp"] }` to `next.config.js` so Next.js serves responsive AVIF/WebP variants while keeping portable local JPEG masters.

Create `manifest.json` with entries shaped exactly as:

```json
{
  "assets": [
    {
      "file": "platform-dark.jpg",
      "application": "platform",
      "mode": "dark",
      "width": 2400,
      "height": 1350,
      "focalPoint": "65% 44%",
      "prompt": "Create a premium cinematic editorial photograph for a sophisticated AI product interface. Subject: interconnected workspaces expressed as monumental precise architecture. Ultra-wide 16:9 composition with a quiet left-side UI-safe region and authored graphite exposure; no text, logos, screens, purple gradients, stock staging, or bokeh decoration."
    }
  ]
}
```

Repeat the complete prompt metadata for all ten files; do not use ellipses in the real manifest.

- [ ] **Step 6: Run the asset test and inspect contact sheets**

Run: `cd frontend && npm test -- tests/lib/cinematic-assets.test.ts`

Expected: PASS.

Create a contact sheet using macOS Quick Look thumbnails or install-free browser rendering; save the reviewed sheet to `/tmp/nexusmind-cinematic-contact.jpg` and do not add it to git.

Inspect `/tmp/nexusmind-cinematic-contact.jpg` with the image viewer. Reject any image containing pseudo-text, logos, unusable UI contrast, repeated composition, or stock-like people.

- [ ] **Step 7: Commit the asset collection**

```bash
git add frontend/public/images/cinematic frontend/next.config.js frontend/tests/lib/cinematic-assets.test.ts
git commit -m "feat(frontend): add original cinematic media collection"
```

---

### Task 4: Focus Canvas and Inspector Primitives

**Files:**
- Create: `frontend/components/shell/FocusCanvas.tsx`
- Create: `frontend/components/shell/CanvasHeader.tsx`
- Create: `frontend/components/shell/ContextRibbon.tsx`
- Create: `frontend/components/shell/Inspector.tsx`
- Create: `frontend/components/shell/ActionDock.tsx`
- Test: `frontend/tests/components/ShellPrimitives.test.tsx`

**Interfaces:**
- Produces the stable composition used by all later application plans.
- `Inspector` owns `open`, `onOpenChange`, `title`, and responsive panel/sheet behavior; feature modules own inspector content.

- [ ] **Step 1: Write failing composition tests**

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FocusCanvas } from "@/components/shell/FocusCanvas";
import { Inspector } from "@/components/shell/Inspector";

it("keeps one named primary work region", () => {
  render(<FocusCanvas ariaLabel="AuraSQL result">Result</FocusCanvas>);
  expect(screen.getByRole("main", { name: "AuraSQL result" })).toHaveTextContent("Result");
});

it("opens advanced detail only when requested", async () => {
  function Harness() { const [open, setOpen] = React.useState(false); return <><button onClick={() => setOpen(true)}>Evidence</button><Inspector open={open} onOpenChange={setOpen} title="Evidence">Sources</Inspector></>; }
  render(<Harness />);
  expect(screen.queryByText("Sources")).not.toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "Evidence" }));
  expect(screen.getByText("Sources")).toBeVisible();
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && npm test -- tests/components/ShellPrimitives.test.tsx`

Expected: FAIL because shell primitives do not exist.

- [ ] **Step 3: Implement the primitives using unframed layout and stable dimensions**

`FocusCanvas` must render a named `<main>` with `min-h-[calc(100svh-2rem)]`, `pl-0 md:pl-[4.5rem]`, and a constrained inner region. `CanvasHeader` renders eyebrow, title, description, status, and actions without a card container. `ContextRibbon` renders compact removable context items in one horizontal overflow region. `ActionDock` is fixed only on mobile and sticky within the canvas on desktop. `Inspector` uses a fixed right panel at `min-width: 1024px` and a full-height dialog/sheet below that breakpoint.

Use this public API exactly:

```tsx
export function FocusCanvas(props: { ariaLabel: string; children: React.ReactNode; className?: string }): JSX.Element;
export function CanvasHeader(props: { eyebrow?: string; title: string; description?: string; status?: React.ReactNode; actions?: React.ReactNode }): JSX.Element;
export function ContextRibbon(props: { children: React.ReactNode; label?: string }): JSX.Element;
export function Inspector(props: { open: boolean; onOpenChange(open: boolean): void; title: string; children: React.ReactNode }): JSX.Element;
export function ActionDock(props: { primary: React.ReactNode; secondary?: React.ReactNode }): JSX.Element;
```

- [ ] **Step 4: Run focused tests and typecheck**

Run: `cd frontend && npm test -- tests/components/ShellPrimitives.test.tsx && npm run typecheck`

Expected: tests PASS and TypeScript exits 0.

- [ ] **Step 5: Commit primitives**

```bash
git add frontend/components/shell frontend/tests/components/ShellPrimitives.test.tsx
git commit -m "feat(frontend): add focus canvas primitives"
```

---

### Task 5: Adaptive Icon Rail and Authenticated Shell

**Files:**
- Create: `frontend/components/shell/AdaptiveRail.tsx`
- Create: `frontend/components/shell/ApplicationSwitcher.tsx`
- Create: `frontend/components/shell/LocalSubmenu.tsx`
- Create: `frontend/components/shell/CinematicAppShell.tsx`
- Modify: `frontend/components/layout/RouteProviders.tsx`
- Test: `frontend/tests/components/CinematicAppShell.test.tsx`

**Interfaces:**
- Consumes: `CatalogState`, `presentationForPath(pathname)`, auth store, appearance control, and existing `JobCenter`.
- Produces: one global shell for every non-public route and local submenu metadata for later feature plans.

- [ ] **Step 1: Write failing shell behavior tests**

```tsx
import { render, screen } from "@testing-library/react";
import { CinematicAppShell } from "@/components/shell/CinematicAppShell";

vi.mock("next/navigation", () => ({ usePathname: () => "/aurasql", useRouter: () => ({ push: vi.fn() }) }));

it("shows application navigation and only the active application's local submenu", () => {
  render(<CinematicAppShell catalog={{ status: "success", apps: [], error: null, retry: vi.fn() } as never}><div>AuraSQL work</div></CinematicAppShell>);
  expect(screen.getByRole("navigation", { name: "Applications" })).toBeInTheDocument();
  expect(screen.getByRole("navigation", { name: "AuraSQL sections" })).toBeInTheDocument();
  expect(screen.getByText("AuraSQL work")).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "Analysis history" })).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && npm test -- tests/components/CinematicAppShell.test.tsx`

Expected: FAIL because the shell does not exist.

- [ ] **Step 3: Implement the rail and switcher**

The desktop rail is `56px` wide inside a `12px` viewport inset, uses Lucide icon buttons with Radix tooltips, and never renders text inside rounded rectangles when an icon communicates the action. It includes dashboard, enabled applications, jobs, appearance, developer, and account/logout. Active application uses a shared-layout `motion.span` with `layoutId="active-application"`.

The mobile version is a five-slot bottom bar: Dashboard, current application, application switcher, jobs, account. Additional applications appear in `ApplicationSwitcher`.

- [ ] **Step 4: Implement the shell and route provider integration**

```tsx
// intended RouteProviders structure
export function RouteProviders({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (isPublicRoute(pathname)) return children;
  return <AppCatalogProvider><JobProvider><AuthenticatedShellBoundary>{children}</AuthenticatedShellBoundary></JobProvider></AppCatalogProvider>;
}

function AuthenticatedShellBoundary({ children }: { children: React.ReactNode }) {
  const catalog = useAppCatalog();
  return <CinematicAppShell catalog={catalog}>{children}</CinematicAppShell>;
}
```

`CinematicAppShell` renders `CinematicBackdrop`, `AdaptiveRail`, the active `LocalSubmenu`, and `MotionRoute`. It does not render the legacy `Header`.

- [ ] **Step 5: Run shell and public-provider regression tests**

Run: `cd frontend && npm test -- tests/components/CinematicAppShell.test.tsx tests/lib/public-routes.test.ts tests/apps/catalog-client.test.ts`

Expected: all tests PASS; public route tests confirm no catalog fetch is mounted for `/`, `/auth`, or `/developer`.

- [ ] **Step 6: Commit the authenticated shell**

```bash
git add frontend/components/shell frontend/components/layout/RouteProviders.tsx frontend/tests/components/CinematicAppShell.test.tsx
git commit -m "feat(frontend): add adaptive authenticated shell"
```

---

### Task 6: Direct-Launch Cinematic Application Dashboard

**Files:**
- Modify: `frontend/app/apps/page.tsx`
- Replace: `frontend/components/platform/AppCatalog.tsx`
- Replace: `frontend/components/platform/AppCard.tsx`
- Create: `frontend/components/platform/CinematicAppGallery.tsx`
- Create: `frontend/components/platform/DashboardSignal.tsx`
- Modify: `frontend/app/apps/[appId]/page.tsx`
- Test: `frontend/tests/components/ApplicationDashboard.test.tsx`

**Interfaces:**
- Consumes: `useAppCatalog()`, `presentationForApp(app)`, and `directApplicationRoute(app)`.
- Produces: a featured application gallery with direct application links and non-dense loading/error/empty states.

- [ ] **Step 1: Write failing dashboard tests**

```tsx
import { render, screen } from "@testing-library/react";
import { AppCatalog } from "@/components/platform/AppCatalog";
import { useAppCatalog } from "@/lib/apps/useAppCatalog";
vi.mock("@/lib/apps/useAppCatalog", () => ({ useAppCatalog: vi.fn() }));

it("features one app and launches manifests directly", () => {
  vi.mocked(useAppCatalog).mockReturnValue({ status: "success", error: null, retry: vi.fn(), apps: [
    { id: "knowledge-studio", name: "Knowledge Studio", frontend_route: "/chat", summary: "Evidence", category: "knowledge", version: "1", icon: "book-open", required_capabilities: [], optional_capabilities: [], backend_route_prefixes: [], backend_router_ids: [], required_permissions: [], required_env_keys: [], dependencies: [], demo_scenarios: [], health_check_id: "knowledge", packaging_paths: [] },
    { id: "aurasql", name: "AuraSQL", frontend_route: "/aurasql", summary: "Data", category: "data", version: "1", icon: "database", required_capabilities: [], optional_capabilities: [], backend_route_prefixes: [], backend_router_ids: [], required_permissions: [], required_env_keys: [], dependencies: [], demo_scenarios: [], health_check_id: "aurasql", packaging_paths: [] },
  ] } as never);
  render(<AppCatalog />);
  expect(screen.getAllByRole("link", { name: /open/i })[0]).toHaveAttribute("href", "/chat");
  expect(screen.getByRole("region", { name: "Featured application" })).toBeInTheDocument();
  expect(screen.queryByText(/guided scenarios/i)).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && npm test -- tests/components/ApplicationDashboard.test.tsx`

Expected: FAIL because existing cards link through `/apps/[appId]` and no featured region exists.

- [ ] **Step 3: Implement the motion gallery**

`CinematicAppGallery` keeps one `activeIndex`, renders one full-viewport featured application, and uses a compact horizontal selector for the remainder. Selecting an app crossfades the persistent media, headline, summary, and restrained `DashboardSignal`. The signal is a decorative live-status visualization only; it must not add metrics, settings, histories, or application controls.

Use direct links:

```tsx
<Link href={directApplicationRoute(app)} aria-label={`Open ${app.name}`}>
  Open workspace <ArrowRight aria-hidden />
</Link>
```

Loading preserves the final hero dimensions. Error shows one retry action. Empty state shows one administrator-facing message without feature copy.

- [ ] **Step 4: Replace intermediate app detail routing**

```tsx
// frontend/app/apps/[appId]/page.tsx
import { notFound, redirect } from "next/navigation";
import { CatalogHttpError, getApp } from "@/lib/apps/client";

export default async function AppLaunch({ params }: { params: { appId: string } }) {
  try { const app = await getApp(params.appId); redirect(app.frontend_route); }
  catch (error) { if (error instanceof CatalogHttpError && error.status === 404) notFound(); throw error; }
}
```

- [ ] **Step 5: Run dashboard tests and typecheck**

Run: `cd frontend && npm test -- tests/components/ApplicationDashboard.test.tsx && npm run typecheck`

Expected: tests PASS and TypeScript exits 0.

- [ ] **Step 6: Commit dashboard**

```bash
git add frontend/app/apps frontend/components/platform frontend/tests/components/ApplicationDashboard.test.tsx
git commit -m "feat(frontend): rebuild application dashboard"
```

---

### Task 7: Homepage Login Overlay and Public Route Simplification

**Files:**
- Create: `frontend/components/auth/AuthOverlay.tsx`
- Create: `frontend/components/auth/AuthController.tsx`
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/components/flagship/FlagshipHero.tsx`
- Modify: `frontend/components/flagship/PublicHeader.tsx`
- Replace: `frontend/app/auth/page.tsx`
- Replace: `frontend/app/showcase/page.tsx`
- Replace: `frontend/app/showcase/[experience]/page.tsx`
- Modify: `frontend/lib/public-routes.ts`
- Modify: `frontend/tests/components/FlagshipPage.test.tsx`
- Modify: `frontend/e2e/flagship.spec.ts`

**Interfaces:**
- Produces: login/register overlay controlled by `?auth=login|register`; successful authentication navigates to `/apps`.
- `/auth` redirects to `/?auth=login`; showcase routes redirect to `/`.

- [ ] **Step 1: Replace old public-route expectations with failing tests**

```tsx
it("opens authentication from the flagship without a separate auth page", async () => {
  const user = userEvent.setup();
  render(<FlagshipPage searchParams={{}} />);
  await user.click(screen.getByRole("button", { name: /log in/i }));
  expect(screen.getByRole("dialog", { name: /enter nexusmind/i })).toBeVisible();
  expect(screen.queryByRole("link", { name: /explore showcase/i })).not.toBeInTheDocument();
});
```

Update E2E expectations so `/auth` resolves to `/?auth=login`, the login dialog is visible, `/showcase` redirects to `/`, and only `/developer` remains as a secondary public destination.

- [ ] **Step 2: Run tests and verify RED**

Run: `cd frontend && npm test -- tests/components/FlagshipPage.test.tsx && npm run test:e2e -- --grep "authentication|public"`

Expected: unit and E2E failures because the current UI links to `/auth` and `/showcase`.

- [ ] **Step 3: Implement `AuthOverlay` and controller**

`AuthOverlay` is a right-side desktop panel and full-screen mobile dialog. It contains the existing `AuthPanel`, a close icon button, cinematic backdrop continuity, and no marketing card column. `AuthController` owns login/register API calls, toast messages, query-string state, focus return, Escape handling, and `router.push("/apps")` after success.

Use this interface:

```tsx
export function AuthController({ initialMode }: { initialMode?: "login" | "register" }): JSX.Element;
export function AuthOverlay(props: { open: boolean; mode: "login" | "register"; onOpenChange(open: boolean): void; onLogin(values: LoginValues): Promise<void>; onRegister(values: RegisterValues): Promise<void> }): JSX.Element;
```

- [ ] **Step 4: Convert public route entry points**

`FlagshipHero` and `PublicHeader` use buttons or links to `/?auth=login` that open the overlay without a full page transition. `app/auth/page.tsx` becomes:

```tsx
import { redirect } from "next/navigation";
export default function AuthRedirect() { redirect("/?auth=login"); }
```

Both showcase page files redirect to `/`. Keep showcase paths classified as public redirects so they never mount the authenticated catalog provider during redirect hydration.

- [ ] **Step 5: Run public tests and E2E**

Run: `cd frontend && npm test -- tests/components/FlagshipPage.test.tsx tests/components/AuthPanel.test.tsx tests/lib/public-routes.test.ts && npm run test:e2e -- --grep "authentication|public"`

Expected: all focused tests PASS on desktop and mobile projects.

- [ ] **Step 6: Commit homepage authentication**

```bash
git add frontend/app/page.tsx frontend/app/auth frontend/app/showcase frontend/components/auth frontend/components/flagship frontend/lib/public-routes.ts frontend/tests/components/FlagshipPage.test.tsx frontend/e2e/flagship.spec.ts
git commit -m "feat(frontend): integrate login into cinematic homepage"
```

---

### Task 8: Visual, Responsive, Accessibility, and Build Gate

**Files:**
- Modify: `frontend/e2e/flagship.spec.ts`
- Create: `frontend/e2e/cinematic-shell.spec.ts`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/.gitignore` only if Playwright output is not already ignored

**Interfaces:**
- Verifies the completed subsystem at public, dashboard, direct-launch, and shell boundaries.

- [ ] **Step 1: Add shell and dashboard Playwright assertions**

```ts
test("authenticated dashboard and shell remain uncluttered", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("auth-storage", JSON.stringify({ state: { isAuthenticated: true, user: { id: 1, email: "demo@nexusmind.local" }, accessToken: "test", refreshToken: "test" }, version: 0 })));
  await page.route("**/api/v1/apps", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ id: "aurasql", version: "1.0.0", name: "AuraSQL", summary: "Query connected data", category: "data", icon: "database", frontend_route: "/aurasql", backend_route_prefixes: [], backend_router_ids: [], required_capabilities: [], optional_capabilities: [], required_permissions: [], required_env_keys: [], dependencies: [], demo_scenarios: [], health_check_id: "aurasql", packaging_paths: [] }]) }));
  await page.goto("/apps");
  await expect(page.getByRole("region", { name: "Featured application" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Applications" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Open AuraSQL" })).toHaveAttribute("href", "/aurasql");
  await expect(page.locator("main")).toHaveCount(1);
});
```

Add reduced-motion coverage using `page.emulateMedia({ reducedMotion: "reduce" })` and assert cinematic elements have no active transform animation. Add mobile coverage asserting the bottom bar is visible and desktop rail is hidden.

- [ ] **Step 2: Run complete unit tests**

Run: `cd frontend && npm test`

Expected: all Vitest files PASS with zero unhandled errors.

- [ ] **Step 3: Run typecheck and lint**

Run: `cd frontend && npm run typecheck && npm run lint`

Expected: both commands exit 0. Existing warnings must be recorded; new warnings in changed files must be fixed.

- [ ] **Step 4: Run production build**

Run: `cd frontend && npm run build`

Expected: optimized build exits 0 and includes `/`, `/apps`, `/apps/[appId]`, `/auth`, and `/developer`.

- [ ] **Step 5: Run desktop and mobile Playwright suites**

Run: `cd frontend && npm run test:e2e -- e2e/flagship.spec.ts e2e/cinematic-shell.spec.ts`

Expected: both Playwright projects PASS.

- [ ] **Step 6: Perform visual screenshot and pixel checks**

Capture `/`, `/?auth=login`, `/apps`, and one application route at `1440x900`, `1024x768`, and `412x915`. Inspect every screenshot for text/image contrast, stable image crop, one dominant canvas, no nested cards, no clipped rail or bottom bar, and no overlapping text/actions.

For each screenshot, use a pixel histogram or canvas-pixel sample to confirm the viewport is not blank and media contains meaningful tonal variation. Re-run after every CSS correction.

- [ ] **Step 7: Verify repository scope and commit the gate**

Run: `git status --short && git diff --check`

Expected: only intended frontend and test files are modified; `.superpowers/brainstorm/` remains untracked and must not be committed.

```bash
git add frontend/e2e frontend/app/globals.css frontend/.gitignore
git commit -m "test(frontend): verify cinematic entry and shell"
```

---

## Completion Handoff

After this plan passes, create and execute the Knowledge application plan next. Do not declare the full redesign complete: AuraSQL, Analysis, Career, Workflows, and their application-local submenu routes remain explicitly outstanding until their own plans and visual gates pass.
