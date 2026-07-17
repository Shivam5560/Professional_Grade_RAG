# Cinematic Precision Foundation and Flagship Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the tested Cinematic Precision design foundation, public flagship homepage, deterministic showcase mode, redesigned authentication surface, and recruiter-facing creator story as the first production-ready slice of the approved frontend revamp.

**Architecture:** Introduce a semantic dark/light token system and a flash-free appearance provider without changing backend contracts. Build the public experience from small brand, flagship, and showcase components; showcase data flows through deterministic local adapters while live authentication and the current application catalog remain intact.

**Tech Stack:** Next.js 14 App Router, React 18, TypeScript 5, Tailwind CSS 3, Framer Motion 12, Three.js 0.183 behind a dynamic import, Vitest, React Testing Library, and Playwright.

## Global Constraints

- Preserve all existing backend API contracts and the current application-catalog route isolation.
- Public `/` must render without authentication or a live backend; authenticated workspace entry remains `/apps`.
- Showcase routes are labeled, deterministic, and must never call live mutation APIs.
- Dark tokens: Void `#090A0D`, Graphite `#15171C`, Pearl `#F5F0E7`, Signal Mint `#B7FBD7`, Burnished Copper `#E49A67`, Data Cyan `#67D6E8`.
- Light tokens: Porcelain `#F2EEE5`, Paper `#FBF8F2`, Ink `#181916`, Forest Mint `#127A55`, Oxidized Copper `#A94E25`, Deep Cyan `#147D91`.
- Remove purple AI gradients and the eight-palette selector; expose only system, dark, and light preferences.
- Use Space Grotesk for product typography, Newsreader only for editorial emphasis, and IBM Plex Mono for technical content.
- Render meaningful static content before optional cinematic modules load.
- Use at most one WebGL context, cap DPR at `1.5`, pause when off-screen or hidden, and dispose every Three.js resource on unmount.
- Respect `prefers-reduced-motion`, coarse pointers, data-saver, and devices reporting less than 4 GB memory.
- Run unit tests, type checking, and a production build before every task commit.
- Do not commit `.superpowers/brainstorm/` or generated `graphify-out/memory/` files.

---

## Program Decomposition

The approved specification spans independent product subsystems. Implement them through these separately reviewed plans:

1. **This plan:** foundation, public flagship, showcase, authentication, and creator profile.
2. **Follow-up plan:** unified application shell, catalog, Knowledge, RAG Chat, and knowledge base.
3. **Follow-up plan:** AuraSQL dashboard, Ask → Review → Results workbench, connections, contexts, and history.
4. **Follow-up plan:** Analysis, Career Studio, ResumeGen, workflows, and Auto-Tailor.
5. **Follow-up plan:** cross-browser accessibility, visual regression, bundle enforcement, and memory/GPU hardening across all migrated routes.

Each plan must leave a working production build. Do not mix later workspace migrations into this foundation plan.

## File Structure

### Create

- `frontend/vitest.config.ts` — jsdom test configuration and `@/` alias.
- `frontend/vitest.setup.ts` — jest-dom registration and browser API cleanup.
- `frontend/lib/appearance.ts` — pure preference migration, resolution, DOM application, and bootstrap script.
- `frontend/tests/lib/appearance.test.ts` — appearance unit tests.
- `frontend/components/theme/AppearanceProvider.tsx` — appearance context and system-preference subscription.
- `frontend/components/theme/AppearanceControl.tsx` — accessible system/light/dark menu.
- `frontend/tests/components/AppearanceProvider.test.tsx` — provider and control behavior.
- `frontend/lib/effects.ts` — pure cinematic-effects eligibility policy.
- `frontend/hooks/useCinematicEffects.ts` — runtime media/network/device/visibility state.
- `frontend/components/brand/NexusAperture.tsx` — static and CSS-animated identity mark.
- `frontend/components/brand/ReasoningThreads.tsx` — accessible-hidden SVG relationship field.
- `frontend/components/brand/CinematicScene.tsx` — isolated, disposable Three.js hero enhancement.
- `frontend/tests/lib/effects.test.ts` — effects-policy tests.
- `frontend/lib/flagship-content.ts` — typed public copy, capability facts, proof points, and creator summary.
- `frontend/components/flagship/PublicHeader.tsx` — public navigation and appearance/workspace actions.
- `frontend/components/flagship/FlagshipHero.tsx` — opening experience and optional scene boundary.
- `frontend/components/flagship/CapabilityStory.tsx` — four application narratives.
- `frontend/components/flagship/TechnicalProof.tsx` — implementation proof grid.
- `frontend/components/flagship/CreatorStory.tsx` — appropriately positioned solo-developer story.
- `frontend/components/flagship/PublicFooter.tsx` — concise attribution and navigation.
- `frontend/tests/components/FlagshipPage.test.tsx` — public content and link contract.
- `frontend/lib/showcase/types.ts` — scenario and state contracts.
- `frontend/lib/showcase/fixtures.ts` — deterministic Knowledge, AuraSQL, Analysis, and Career scenarios.
- `frontend/lib/showcase/reducer.ts` — pure scenario state transitions.
- `frontend/components/showcase/ShowcaseProvider.tsx` — isolated local showcase state.
- `frontend/components/showcase/ShowcaseShell.tsx` — persistent demo labeling and navigation.
- `frontend/components/showcase/ShowcaseExperience.tsx` — shared scenario renderer.
- `frontend/app/showcase/page.tsx` — showcase overview.
- `frontend/app/showcase/[experience]/page.tsx` — statically generated scenario routes.
- `frontend/tests/lib/showcase.test.ts` — fixture and reducer tests.
- `frontend/components/auth/AuthPanel.tsx` — testable login/register form presentation.
- `frontend/tests/components/AuthPanel.test.tsx` — form validation and submission tests.
- `frontend/lib/public-routes.ts` — pure public-route classification for offline-safe provider composition.
- `frontend/components/layout/RouteProviders.tsx` — mount live API providers only inside product routes.
- `frontend/tests/lib/public-routes.test.ts` — route isolation policy tests.
- `frontend/lib/creator-profile.ts` — typed engineering profile content.
- `frontend/tests/components/DeveloperPage.test.tsx` — creator proof and navigation assertions.
- `frontend/playwright.config.ts` — desktop and mobile E2E projects.
- `frontend/e2e/flagship.spec.ts` — public, theme, showcase, auth, and creator journeys.

### Modify

- `frontend/package.json` and `frontend/package-lock.json` — test dependencies and scripts.
- `frontend/app/globals.css` — replace legacy palette blocks with semantic Cinematic Precision tokens and utilities.
- `frontend/app/layout.tsx` — fonts, metadata, appearance bootstrap, and route-aware provider composition.
- `frontend/components/layout/ClientProviders.tsx` — make the appearance provider wrap application children.
- `frontend/lib/theme.ts` — remove palette behavior and retain a small compatibility facade during later route migration.
- `frontend/hooks/useAppTheme.ts` — delegate legacy consumers to the new appearance context.
- `frontend/components/layout/Header.tsx` — replace the palette chooser with `AppearanceControl`.
- `frontend/app/page.tsx` — replace the authenticated dashboard/auth switch with the public flagship composition.
- `frontend/app/auth/page.tsx` — preserve API calls while adopting the new panel and visual treatment.
- `frontend/app/developer/page.tsx` — turn the existing developer surface into the public engineering profile.

---

### Task 1: Test Harness and Pure Appearance Model

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/vitest.setup.ts`
- Create: `frontend/lib/appearance.ts`
- Create: `frontend/tests/lib/appearance.test.ts`

**Interfaces:**
- Produces: `ThemePreference = "system" | "light" | "dark"`.
- Produces: `ResolvedTheme = "light" | "dark"`.
- Produces: `readThemePreference(storage)`, `resolveTheme(preference, systemDark)`, `persistThemePreference(storage, preference)`, `applyResolvedTheme(root, preference, resolved)`, and `themeBootstrapScript`.
- Consumed by: Tasks 2, 4, 6, and 8.

- [ ] **Step 1: Install the unit-test dependencies and add scripts**

Run:

```bash
cd frontend
npm install --save-dev vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

Update `frontend/package.json` scripts to exactly:

```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "next lint",
  "typecheck": "tsc --noEmit",
  "test": "vitest run",
  "test:watch": "vitest"
}
```

Expected: `package-lock.json` records the new dev dependencies and `npm install` exits `0`.

- [ ] **Step 2: Configure Vitest**

Create `frontend/vitest.config.ts`:

```ts
import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, ".") } },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
    restoreMocks: true,
  },
});
```

Create `frontend/vitest.setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => cleanup());
```

- [ ] **Step 3: Write the failing appearance tests**

Create `frontend/tests/lib/appearance.test.ts`:

```ts
import {
  APPEARANCE_STORAGE_KEY,
  applyResolvedTheme,
  persistThemePreference,
  readThemePreference,
  resolveTheme,
} from "@/lib/appearance";

function memoryStorage(seed: Record<string, string> = {}) {
  const values = new Map(Object.entries(seed));
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    removeItem: (key: string) => values.delete(key),
    value: (key: string) => values.get(key),
  };
}

describe("appearance", () => {
  it("migrates the legacy light mode and removes the palette", () => {
    const storage = memoryStorage({ "theme-mode": "light", "theme-palette": "royal" });
    expect(readThemePreference(storage)).toBe("light");
    expect(storage.value(APPEARANCE_STORAGE_KEY)).toBe("light");
    expect(storage.value("theme-palette")).toBeUndefined();
  });

  it("defaults invalid values to system", () => {
    const storage = memoryStorage({ [APPEARANCE_STORAGE_KEY]: "violet" });
    expect(readThemePreference(storage)).toBe("system");
  });

  it("resolves system preference without changing explicit choices", () => {
    expect(resolveTheme("system", true)).toBe("dark");
    expect(resolveTheme("system", false)).toBe("light");
    expect(resolveTheme("light", true)).toBe("light");
  });

  it("writes the DOM contract used by CSS and hydration", () => {
    const root = document.documentElement;
    applyResolvedTheme(root, "system", "dark");
    expect(root).toHaveClass("dark");
    expect(root).toHaveAttribute("data-theme-mode", "dark");
    expect(root).toHaveAttribute("data-theme-preference", "system");
  });

  it("persists only the new preference key", () => {
    const storage = memoryStorage();
    persistThemePreference(storage, "dark");
    expect(storage.value(APPEARANCE_STORAGE_KEY)).toBe("dark");
  });
});
```

- [ ] **Step 4: Run the tests and verify the missing-module failure**

Run: `cd frontend && npm test -- tests/lib/appearance.test.ts`

Expected: FAIL because `@/lib/appearance` does not exist.

- [ ] **Step 5: Implement the pure appearance model**

Create `frontend/lib/appearance.ts`:

```ts
export type ThemePreference = "system" | "light" | "dark";
export type ResolvedTheme = "light" | "dark";

export const APPEARANCE_STORAGE_KEY = "nexusmind-theme";
const LEGACY_MODE_KEY = "theme-mode";
const LEGACY_PALETTE_KEY = "theme-palette";

export interface AppearanceStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

function isPreference(value: string | null): value is ThemePreference {
  return value === "system" || value === "light" || value === "dark";
}

export function readThemePreference(storage: AppearanceStorage): ThemePreference {
  const current = storage.getItem(APPEARANCE_STORAGE_KEY);
  if (isPreference(current)) return current;

  const legacy = storage.getItem(LEGACY_MODE_KEY);
  const migrated: ThemePreference = legacy === "light" || legacy === "dark" ? legacy : "system";
  storage.setItem(APPEARANCE_STORAGE_KEY, migrated);
  storage.removeItem(LEGACY_MODE_KEY);
  storage.removeItem(LEGACY_PALETTE_KEY);
  return migrated;
}

export function persistThemePreference(
  storage: AppearanceStorage,
  preference: ThemePreference,
): void {
  storage.setItem(APPEARANCE_STORAGE_KEY, preference);
  storage.removeItem(LEGACY_MODE_KEY);
  storage.removeItem(LEGACY_PALETTE_KEY);
}

export function resolveTheme(
  preference: ThemePreference,
  systemPrefersDark: boolean,
): ResolvedTheme {
  return preference === "system" ? (systemPrefersDark ? "dark" : "light") : preference;
}

export function applyResolvedTheme(
  root: HTMLElement,
  preference: ThemePreference,
  resolved: ResolvedTheme,
): void {
  root.classList.toggle("dark", resolved === "dark");
  root.dataset.themeMode = resolved;
  root.dataset.themePreference = preference;
  root.style.colorScheme = resolved;
}

export const themeBootstrapScript = `(() => {
  try {
    const key = "${APPEARANCE_STORAGE_KEY}";
    const stored = localStorage.getItem(key);
    const legacy = localStorage.getItem("${LEGACY_MODE_KEY}");
    const preference = ["system", "light", "dark"].includes(stored || "")
      ? stored
      : (["light", "dark"].includes(legacy || "") ? legacy : "system");
    localStorage.setItem(key, preference);
    localStorage.removeItem("${LEGACY_MODE_KEY}");
    localStorage.removeItem("${LEGACY_PALETTE_KEY}");
    const dark = preference === "dark" ||
      (preference === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
    const root = document.documentElement;
    root.classList.toggle("dark", dark);
    root.dataset.themeMode = dark ? "dark" : "light";
    root.dataset.themePreference = preference;
    root.style.colorScheme = dark ? "dark" : "light";
  } catch {}
})();`;
```

- [ ] **Step 6: Verify unit tests, types, and build**

Run:

```bash
cd frontend
npm test -- tests/lib/appearance.test.ts
npm run typecheck
npm run build
```

Expected: all five tests PASS, TypeScript exits `0`, and Next.js production build exits `0`.

- [ ] **Step 7: Commit the test foundation and appearance model**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/vitest.setup.ts frontend/lib/appearance.ts frontend/tests/lib/appearance.test.ts
git commit -m "test(frontend): add appearance foundation"
```

---

### Task 2: Cinematic Tokens and Flash-free Appearance Runtime

**Files:**
- Modify: `frontend/app/globals.css:11-221`
- Modify: `frontend/tailwind.config.js`
- Modify: `frontend/app/layout.tsx:1-48`
- Modify: `frontend/components/layout/ClientProviders.tsx:1-7`
- Create: `frontend/components/theme/AppearanceProvider.tsx`
- Create: `frontend/components/theme/AppearanceControl.tsx`
- Create: `frontend/tests/components/AppearanceProvider.test.tsx`
- Modify: `frontend/lib/theme.ts:1-59`
- Modify: `frontend/hooks/useAppTheme.ts:1-39`
- Modify: `frontend/components/layout/Header.tsx:1-243`
- Modify: `frontend/app/auth/page.tsx:1-45,225-255`

**Interfaces:**
- Consumes: Task 1 appearance functions and types.
- Produces: `AppearanceProvider`, `useAppearance(): { preference, resolvedTheme, setPreference }`, and `AppearanceControl`.
- Compatibility: `useAppTheme()` continues returning `mode` and `toggleMode` until later workspace plans migrate all consumers; palette fields are removed.

- [ ] **Step 1: Write failing provider and control tests**

Create `frontend/tests/components/AppearanceProvider.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AppearanceProvider, useAppearance } from "@/components/theme/AppearanceProvider";
import { AppearanceControl } from "@/components/theme/AppearanceControl";

function Probe() {
  const appearance = useAppearance();
  return <output>{appearance.preference}:{appearance.resolvedTheme}</output>;
}

describe("AppearanceProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    window.matchMedia = ((query: string) => ({
      matches: query.includes("dark"),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })) as typeof window.matchMedia;
  });

  it("starts from system and resolves the media preference", () => {
    render(<AppearanceProvider><Probe /></AppearanceProvider>);
    expect(screen.getByText("system:dark")).toBeInTheDocument();
  });

  it("lets the user select light mode accessibly", async () => {
    render(<AppearanceProvider><AppearanceControl /><Probe /></AppearanceProvider>);
    await userEvent.click(screen.getByRole("button", { name: /appearance/i }));
    await userEvent.click(screen.getByRole("menuitemradio", { name: /light/i }));
    expect(screen.getByText("light:light")).toBeInTheDocument();
    expect(document.documentElement).not.toHaveClass("dark");
  });
});
```

- [ ] **Step 2: Run the tests and verify missing-component failures**

Run: `cd frontend && npm test -- tests/components/AppearanceProvider.test.tsx`

Expected: FAIL because the theme components do not exist.

- [ ] **Step 3: Implement `AppearanceProvider`**

Create `frontend/components/theme/AppearanceProvider.tsx`:

```tsx
"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  applyResolvedTheme,
  persistThemePreference,
  readThemePreference,
  resolveTheme,
  type ResolvedTheme,
  type ThemePreference,
} from "@/lib/appearance";

interface AppearanceValue {
  preference: ThemePreference;
  resolvedTheme: ResolvedTheme;
  setPreference(preference: ThemePreference): void;
}

const AppearanceContext = createContext<AppearanceValue | null>(null);

export function AppearanceProvider({ children }: { children: React.ReactNode }) {
  const media = typeof window === "undefined" ? null : window.matchMedia("(prefers-color-scheme: dark)");
  const [preference, setPreferenceState] = useState<ThemePreference>(() =>
    typeof window === "undefined" ? "system" : readThemePreference(window.localStorage),
  );
  const [systemDark, setSystemDark] = useState(media?.matches ?? true);
  const resolvedTheme = resolveTheme(preference, systemDark);

  useEffect(() => {
    const query = window.matchMedia("(prefers-color-scheme: dark)");
    const update = (event: MediaQueryListEvent) => setSystemDark(event.matches);
    setSystemDark(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    applyResolvedTheme(document.documentElement, preference, resolvedTheme);
  }, [preference, resolvedTheme]);

  const setPreference = useCallback((next: ThemePreference) => {
    persistThemePreference(window.localStorage, next);
    setPreferenceState(next);
  }, []);

  const value = useMemo(
    () => ({ preference, resolvedTheme, setPreference }),
    [preference, resolvedTheme, setPreference],
  );

  return <AppearanceContext.Provider value={value}>{children}</AppearanceContext.Provider>;
}

export function useAppearance(): AppearanceValue {
  const value = useContext(AppearanceContext);
  if (!value) throw new Error("useAppearance must be used within AppearanceProvider");
  return value;
}
```

- [ ] **Step 4: Implement the accessible appearance control**

Create `frontend/components/theme/AppearanceControl.tsx` using the existing Radix dropdown primitives:

```tsx
"use client";

import { Laptop, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuLabel,
  DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAppearance } from "./AppearanceProvider";
import type { ThemePreference } from "@/lib/appearance";

const choices = [
  { value: "system", label: "System", icon: Laptop },
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
] satisfies Array<{ value: ThemePreference; label: string; icon: typeof Sun }>;

export function AppearanceControl() {
  const { preference, resolvedTheme, setPreference } = useAppearance();
  const Icon = resolvedTheme === "dark" ? Moon : Sun;
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button aria-label="Appearance" size="icon" variant="ghost"><Icon className="h-4 w-4" /></Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-44">
        <DropdownMenuLabel>Appearance</DropdownMenuLabel>
        <DropdownMenuRadioGroup value={preference} onValueChange={(value) => setPreference(value as ThemePreference)}>
          {choices.map(({ value, label, icon: ChoiceIcon }) => (
            <DropdownMenuRadioItem key={value} value={value}>
              <ChoiceIcon className="mr-2 h-4 w-4" />{label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

- [ ] **Step 5: Replace legacy palette tokens with the approved semantic tokens**

In `frontend/app/globals.css`, keep Tailwind directives and route-specific utilities but replace the existing `:root`, `.theme-*`, and `.dark` blocks with:

```css
@layer base {
  :root {
    --font-sans: var(--font-space-grotesk);
    --font-editorial: var(--font-newsreader);
    --font-mono: var(--font-ibm-plex-mono);
    --background: 41 31% 92%;
    --foreground: 80 6% 9%;
    --card: 40 53% 97%;
    --card-foreground: 80 6% 9%;
    --popover: 40 53% 97%;
    --popover-foreground: 80 6% 9%;
    --primary: 158 74% 27%;
    --primary-foreground: 40 53% 97%;
    --secondary: 39 24% 87%;
    --secondary-foreground: 80 6% 9%;
    --muted: 39 24% 87%;
    --muted-foreground: 36 8% 39%;
    --accent: 19 64% 40%;
    --accent-foreground: 40 53% 97%;
    --destructive: 4 68% 45%;
    --destructive-foreground: 40 53% 97%;
    --border: 36 20% 81%;
    --input: 36 20% 81%;
    --ring: 158 74% 27%;
    --signal: 158 74% 27%;
    --copper: 19 64% 40%;
    --data: 189 76% 32%;
    --chart-1: 158 74% 27%;
    --chart-2: 189 76% 32%;
    --chart-3: 19 64% 40%;
    --chart-4: 219 68% 47%;
    --chart-5: 39 62% 43%;
    --sidebar-background: 80 6% 9%;
    --sidebar-foreground: 38 41% 93%;
    --sidebar-primary: 25 70% 65%;
    --sidebar-primary-foreground: 225 18% 4%;
    --sidebar-accent: 225 14% 15%;
    --sidebar-accent-foreground: 38 41% 93%;
    --sidebar-border: 225 10% 23%;
    --sidebar-ring: 148 89% 85%;
    --bubble-bot: 40 53% 97%;
    --bubble-user: 39 24% 87%;
    --radius: 0.75rem;
    color-scheme: light;
  }

  .dark {
    --background: 225 18% 4%;
    --foreground: 38 41% 93%;
    --card: 225 14% 10%;
    --card-foreground: 38 41% 93%;
    --popover: 225 14% 10%;
    --popover-foreground: 38 41% 93%;
    --primary: 148 89% 85%;
    --primary-foreground: 153 31% 8%;
    --secondary: 225 12% 15%;
    --secondary-foreground: 38 41% 93%;
    --muted: 225 12% 15%;
    --muted-foreground: 38 10% 65%;
    --accent: 25 70% 65%;
    --accent-foreground: 225 18% 4%;
    --destructive: 4 62% 42%;
    --destructive-foreground: 38 41% 93%;
    --border: 225 10% 20%;
    --input: 225 10% 20%;
    --ring: 148 89% 85%;
    --signal: 148 89% 85%;
    --copper: 25 70% 65%;
    --data: 189 72% 66%;
    --chart-1: 148 89% 85%;
    --chart-2: 189 72% 66%;
    --chart-3: 25 70% 65%;
    --chart-4: 219 100% 72%;
    --chart-5: 39 72% 65%;
    --sidebar-background: 225 18% 4%;
    --sidebar-foreground: 38 41% 93%;
    --sidebar-primary: 148 89% 85%;
    --sidebar-primary-foreground: 153 31% 8%;
    --sidebar-accent: 225 12% 15%;
    --sidebar-accent-foreground: 38 41% 93%;
    --sidebar-border: 225 10% 20%;
    --sidebar-ring: 148 89% 85%;
    --bubble-bot: 225 14% 10%;
    --bubble-user: 225 12% 15%;
    color-scheme: dark;
  }
}
```

Replace purple gradient utilities with mint/copper material gradients. Keep SQL token colors mapped to `--signal`, `--data`, and `--copper`.

- [ ] **Step 6: Install fonts and compose providers without a flash**

Extend `frontend/tailwind.config.js` under `theme.extend`:

```js
fontFamily: {
  sans: ["var(--font-space-grotesk)", "system-ui", "sans-serif"],
  editorial: ["var(--font-newsreader)", "Georgia", "serif"],
  mono: ["var(--font-ibm-plex-mono)", "ui-monospace", "monospace"],
},
```

Replace `frontend/app/layout.tsx` with:

```tsx
import type { Metadata } from "next";
import { IBM_Plex_Mono, Newsreader, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { ClientProviders } from "@/components/layout/ClientProviders";
import { JobProvider } from "@/components/providers/JobProvider";
import { AppCatalogProvider } from "@/lib/apps/useAppCatalog";
import { themeBootstrapScript } from "@/lib/appearance";

const space = Space_Grotesk({ subsets: ["latin"], variable: "--font-space-grotesk", display: "swap" });
const newsreader = Newsreader({ subsets: ["latin"], variable: "--font-newsreader", display: "swap", style: ["normal", "italic"] });
const mono = IBM_Plex_Mono({ subsets: ["latin"], variable: "--font-ibm-plex-mono", weight: ["400", "600"], display: "swap" });

export const metadata: Metadata = {
  title: { default: "NexusMind — Intelligence made tangible", template: "%s · NexusMind" },
  description: "Grounded research, data intelligence, and high-stakes output in one authored AI system.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en" suppressHydrationWarning className={`${space.variable} ${newsreader.variable} ${mono.variable}`}><head><script dangerouslySetInnerHTML={{ __html: themeBootstrapScript }} /></head><body><ClientProviders><AppCatalogProvider><JobProvider>{children}</JobProvider></AppCatalogProvider></ClientProviders></body></html>;
}
```

Replace `frontend/components/layout/ClientProviders.tsx` with:

```tsx
"use client";
import { AppearanceProvider } from "@/components/theme/AppearanceProvider";
import { Toaster } from "@/hooks/useToast";
export function ClientProviders({ children }: { children: React.ReactNode }) {
  return <AppearanceProvider>{children}<Toaster /></AppearanceProvider>;
}
```

- [ ] **Step 7: Remove palette controls and retain a compatibility hook**

In `Header.tsx` and `auth/page.tsx`, remove `ThemePalette`, palette option arrays, palette icon imports, and `DropdownMenuRadio*` usage for themes. Replace each complete legacy theme menu with:

```tsx
<AppearanceControl />
```

Replace `frontend/hooks/useAppTheme.ts` with:

```ts
"use client";
import { useAppearance } from "@/components/theme/AppearanceProvider";

export function useAppTheme() {
  const { resolvedTheme, setPreference } = useAppearance();
  return {
    mode: resolvedTheme,
    toggleMode: () => setPreference(resolvedTheme === "dark" ? "light" : "dark"),
  };
}
```

Replace `frontend/lib/theme.ts` with:

```ts
import { applyResolvedTheme, persistThemePreference, readThemePreference, resolveTheme, type ResolvedTheme } from "./appearance";
export type ThemeMode = ResolvedTheme;
export function readThemeMode(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  return resolveTheme(readThemePreference(window.localStorage), matchMedia("(prefers-color-scheme: dark)").matches);
}
export function applyTheme(mode: ThemeMode): void {
  if (typeof document !== "undefined") applyResolvedTheme(document.documentElement, mode, mode);
}
export function persistTheme(mode: ThemeMode): void {
  if (typeof window !== "undefined") persistThemePreference(window.localStorage, mode);
}
```

Do not retain `ThemePalette`, `readThemePalette`, `nextPalette`, or `data-theme-palette` behavior.

- [ ] **Step 8: Verify appearance behavior and the production build**

Run:

```bash
cd frontend
npm test -- tests/lib/appearance.test.ts tests/components/AppearanceProvider.test.tsx
npm run typecheck
npm run build
rg "ThemePalette|readThemePalette|nextPalette|data-theme-palette" app components hooks lib -g '*.ts' -g '*.tsx'
```

Expected: seven tests PASS, the legacy-theme `rg` has no matches, and the build exits `0`.

- [ ] **Step 9: Commit the token and appearance runtime**

```bash
git add frontend/app/globals.css frontend/tailwind.config.js frontend/app/layout.tsx frontend/components/layout/ClientProviders.tsx frontend/components/theme frontend/tests/components/AppearanceProvider.test.tsx frontend/lib/theme.ts frontend/hooks/useAppTheme.ts frontend/components/layout/Header.tsx frontend/app/auth/page.tsx
git commit -m "feat(frontend): add cinematic appearance system"
```

---

### Task 3: Adaptive Brand Motion and Cinematic Hero Scene

**Files:**
- Create: `frontend/lib/effects.ts`
- Create: `frontend/hooks/useCinematicEffects.ts`
- Create: `frontend/components/brand/NexusAperture.tsx`
- Create: `frontend/components/brand/ReasoningThreads.tsx`
- Create: `frontend/components/brand/CinematicScene.tsx`
- Modify: `frontend/lib/motion.ts`
- Create: `frontend/tests/lib/effects.test.ts`

**Interfaces:**
- Produces: `EffectsEnvironment`, `shouldEnableCinematicEffects(environment): boolean`.
- Produces: `useCinematicEffects(): { enabled: boolean; visible: boolean }`.
- Produces: `NexusAperture`, `ReasoningThreads`, and default-exported `CinematicScene`.
- Consumed by: Tasks 4, 5, 6, and 7.

- [ ] **Step 1: Write the failing effects-policy tests**

Create `frontend/tests/lib/effects.test.ts`:

```ts
import { shouldEnableCinematicEffects } from "@/lib/effects";

const capable = { reducedMotion: false, coarsePointer: false, saveData: false, deviceMemory: 8 };

describe("shouldEnableCinematicEffects", () => {
  it("enables the scene on a capable device", () => expect(shouldEnableCinematicEffects(capable)).toBe(true));
  it.each([
    { ...capable, reducedMotion: true },
    { ...capable, saveData: true },
    { ...capable, coarsePointer: true },
    { ...capable, deviceMemory: 2 },
  ])("disables expensive effects for constrained environments", (environment) => {
    expect(shouldEnableCinematicEffects(environment)).toBe(false);
  });
});
```

- [ ] **Step 2: Verify the missing-module failure**

Run: `cd frontend && npm test -- tests/lib/effects.test.ts`

Expected: FAIL because `@/lib/effects` does not exist.

- [ ] **Step 3: Implement the pure policy and runtime hook**

Create `frontend/lib/effects.ts`:

```ts
export interface EffectsEnvironment {
  reducedMotion: boolean;
  coarsePointer: boolean;
  saveData: boolean;
  deviceMemory?: number;
}

export function shouldEnableCinematicEffects(environment: EffectsEnvironment): boolean {
  return !environment.reducedMotion &&
    !environment.coarsePointer &&
    !environment.saveData &&
    (environment.deviceMemory === undefined || environment.deviceMemory >= 4);
}
```

Create `frontend/hooks/useCinematicEffects.ts`:

```ts
"use client";

import { useEffect, useState } from "react";
import { shouldEnableCinematicEffects } from "@/lib/effects";

interface NavigatorHints extends Navigator {
  connection?: { saveData?: boolean };
  deviceMemory?: number;
}

function readState() {
  const hints = navigator as NavigatorHints;
  return {
    enabled: shouldEnableCinematicEffects({
      reducedMotion: matchMedia("(prefers-reduced-motion: reduce)").matches,
      coarsePointer: matchMedia("(pointer: coarse)").matches,
      saveData: hints.connection?.saveData === true,
      deviceMemory: hints.deviceMemory,
    }),
    visible: document.visibilityState === "visible",
  };
}

export function useCinematicEffects() {
  const [state, setState] = useState({ enabled: false, visible: true });

  useEffect(() => {
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    const coarse = matchMedia("(pointer: coarse)");
    const update = () => setState(readState());
    update();
    reduced.addEventListener("change", update);
    coarse.addEventListener("change", update);
    document.addEventListener("visibilitychange", update);
    return () => {
      reduced.removeEventListener("change", update);
      coarse.removeEventListener("change", update);
      document.removeEventListener("visibilitychange", update);
    };
  }, []);

  return state;
}
```

- [ ] **Step 4: Implement the static brand signatures**

Create `frontend/components/brand/NexusAperture.tsx`:

```tsx
import { cn } from "@/lib/utils";

export function NexusAperture({ className }: { className?: string }) {
  return (
    <div aria-hidden className={cn("nexus-breathe relative aspect-square w-52 rounded-full border border-[hsl(var(--signal)/.3)]", className)}>
      <div className="nexus-orbit absolute inset-[14%] rounded-full border border-dashed border-[hsl(var(--copper)/.38)]" />
      <div className="absolute inset-[31%] rounded-full border border-[hsl(var(--signal)/.52)]" />
      <div className="absolute inset-[46%] rounded-full bg-[hsl(var(--signal))] shadow-[0_0_32px_hsl(var(--signal)/.6)]" />
    </div>
  );
}
```

Create `frontend/components/brand/ReasoningThreads.tsx`:

```tsx
import { cn } from "@/lib/utils";

export function ReasoningThreads({ className }: { className?: string }) {
  return (
    <svg aria-hidden className={cn("h-full w-full", className)} viewBox="0 0 640 260" fill="none">
      <defs>
        <linearGradient id="thread-mint" x1="40" y1="210" x2="310" y2="60" gradientUnits="userSpaceOnUse">
          <stop stopColor="hsl(var(--signal))" /><stop offset="1" stopColor="hsl(var(--data))" />
        </linearGradient>
        <linearGradient id="thread-copper" x1="310" y1="60" x2="590" y2="190" gradientUnits="userSpaceOnUse">
          <stop stopColor="hsl(var(--data))" /><stop offset="1" stopColor="hsl(var(--copper))" />
        </linearGradient>
      </defs>
      <path d="M48 208C142 194 190 86 310 62" stroke="url(#thread-mint)" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
      <path d="M310 62C398 60 470 180 590 190" stroke="url(#thread-copper)" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
      <path d="M48 208C220 242 420 232 590 190" stroke="hsl(var(--foreground)/.16)" vectorEffect="non-scaling-stroke" />
      {[[48,208],[310,62],[455,145],[590,190]].map(([cx, cy], index) => (
        <circle key={index} cx={cx} cy={cy} r="5" fill={index === 3 ? "hsl(var(--copper))" : "hsl(var(--signal))"} />
      ))}
    </svg>
  );
}
```

Add the exact utility classes and keyframes to `globals.css`:

```css
@keyframes nexus-orbit { to { transform: rotate(360deg); } }
@keyframes nexus-breathe { 50% { transform: scale(1.035); opacity: .72; } }
.nexus-orbit { animation: nexus-orbit 18s linear infinite; }
.nexus-breathe { animation: nexus-breathe 6s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) {
  .nexus-orbit, .nexus-breathe { animation: none; }
}
```

- [ ] **Step 5: Implement the isolated Three.js scene**

Create `frontend/components/brand/CinematicScene.tsx`:

```tsx
"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

const fragment = `
  uniform float uTime;
  varying vec2 vUv;
  void main() {
    vec2 p = vUv - .5;
    float radius = length(p);
    float wave = sin(radius * 28.0 - uTime * .55) * .5 + .5;
    float mintField = smoothstep(.55, .04, radius) * (.22 + wave * .12);
    float copperField = smoothstep(.28, .0, distance(vUv, vec2(.76,.22))) * .2;
    vec3 mint = vec3(.718,.984,.843);
    vec3 copper = vec3(.894,.604,.404);
    vec3 color = mint * mintField + copper * copperField;
    gl_FragColor = vec4(color, min(.34, mintField + copperField));
  }
`;

export default function CinematicScene({ active }: { active: boolean }) {
  const hostRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!active || !host) return;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.setClearColor(0x000000, 0);
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const geometry = new THREE.PlaneGeometry(2, 2);
    const material = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      uniforms: { uTime: { value: 0 } },
      vertexShader: "varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position,1.0);}",
      fragmentShader: fragment,
    });
    scene.add(new THREE.Mesh(geometry, material));

    let frame = 0;
    let intersecting = false;
    const render = (time: number) => {
      material.uniforms.uTime.value = time / 1000;
      renderer.render(scene, camera);
      frame = intersecting ? requestAnimationFrame(render) : 0;
    };
    const intersection = new IntersectionObserver(([entry]) => {
      intersecting = entry.isIntersecting;
      if (intersecting && frame === 0) frame = requestAnimationFrame(render);
      if (!intersecting && frame !== 0) { cancelAnimationFrame(frame); frame = 0; }
    }, { threshold: 0.05 });
    intersection.observe(host);

    const resize = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      renderer.setSize(width, height, false);
    });
    resize.observe(host);

    return () => {
      if (frame) cancelAnimationFrame(frame);
      intersection.disconnect();
      resize.disconnect();
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
    };
  }, [active]);

  return <div ref={hostRef} aria-hidden className="pointer-events-none absolute inset-0" />;
}
```

The capability hook intentionally lives outside this heavy module. `CinematicScene` is only rendered after eligibility is true, preventing constrained devices from downloading the dynamic Three.js chunk merely to return `null`.

- [ ] **Step 6: Replace filter-heavy shared motion definitions**

Update `frontend/lib/motion.ts` so `fadeUp` animates only opacity and transform:

```ts
export const easeOut = [0.22, 1, 0.36, 1] as const;
export const durations = { fast: 0.16, medium: 0.28, slow: 0.48 } as const;
export const fadeUp = { hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0 } };
export const fadeIn = { hidden: { opacity: 0 }, show: { opacity: 1 } };
export const staggerContainer = { hidden: {}, show: { transition: { staggerChildren: 0.07 } } };
```

- [ ] **Step 7: Verify policy, types, build, and cleanup contract**

Run:

```bash
cd frontend
npm test -- tests/lib/effects.test.ts
npm run typecheck
npm run build
rg "forceContextLoss|dispose\(\)|cancelAnimationFrame" components/brand/CinematicScene.tsx
```

Expected: five policy tests PASS; typecheck/build exit `0`; the grep output includes all three cleanup mechanisms.

- [ ] **Step 8: Commit the adaptive brand-motion foundation**

```bash
git add frontend/lib/effects.ts frontend/hooks/useCinematicEffects.ts frontend/components/brand frontend/lib/motion.ts frontend/app/globals.css frontend/tests/lib/effects.test.ts
git commit -m "feat(frontend): add adaptive cinematic brand motion"
```

---

### Task 4: Public Flagship Homepage

**Files:**
- Create: `frontend/lib/flagship-content.ts`
- Create: `frontend/components/flagship/PublicHeader.tsx`
- Create: `frontend/components/flagship/FlagshipHero.tsx`
- Create: `frontend/components/flagship/CapabilityStory.tsx`
- Create: `frontend/components/flagship/TechnicalProof.tsx`
- Create: `frontend/components/flagship/CreatorStory.tsx`
- Create: `frontend/components/flagship/PublicFooter.tsx`
- Modify: `frontend/app/page.tsx`
- Create: `frontend/tests/components/FlagshipPage.test.tsx`

**Interfaces:**
- Consumes: `AppearanceControl`, brand signatures, optional `CinematicScene`, current auth store, and `/apps`/`/auth` routes.
- Produces: static-first public `/`, `CAPABILITIES`, `PROOF_POINTS`, and `CREATOR_SUMMARY` content contracts.
- Consumed by: Tasks 5, 7, and 8.

- [ ] **Step 1: Write the failing public-page contract test**

Create `frontend/tests/components/FlagshipPage.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import FlagshipPage from "@/app/page";

vi.mock("next/dynamic", () => ({ default: () => () => null }));
vi.mock("@/lib/store", () => ({ useAuthStore: () => ({ isAuthenticated: false }) }));
vi.mock("@/hooks/useCinematicEffects", () => ({
  useCinematicEffects: () => ({ enabled: false, visible: true }),
}));
vi.mock("@/components/theme/AppearanceControl", () => ({
  AppearanceControl: () => <button aria-label="Appearance">Appearance</button>,
}));

describe("FlagshipPage", () => {
  it("explains the product before presenting creator attribution", () => {
    render(<FlagshipPage />);
    const product = screen.getByRole("heading", { name: /intelligence, made tangible/i });
    const creator = screen.getByRole("heading", { name: /built end to end by shivam sourav/i });
    expect(product.compareDocumentPosition(creator) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("offers showcase and live-workspace paths", () => {
    render(<FlagshipPage />);
    expect(screen.getByRole("link", { name: /explore showcase/i })).toHaveAttribute("href", "/showcase");
    expect(screen.getByRole("link", { name: /launch live workspace/i })).toHaveAttribute("href", "/auth");
  });

  it.each(["Knowledge", "AuraSQL", "Analysis", "Career Studio"])("shows %s", (name) => {
    render(<FlagshipPage />);
    expect(screen.getByRole("heading", { name })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the contract test and verify failure against the current dashboard**

Run: `cd frontend && npm test -- tests/components/FlagshipPage.test.tsx`

Expected: FAIL because the current page conditionally renders auth/dashboard content and lacks the approved headings.

- [ ] **Step 3: Create typed factual content**

Create `frontend/lib/flagship-content.ts` with:

```ts
export interface CapabilityStoryItem {
  id: "knowledge" | "aurasql" | "analysis" | "career";
  name: string;
  statement: string;
  proof: readonly string[];
  showcaseHref: string;
}

export const CAPABILITIES: readonly CapabilityStoryItem[] = [
  { id: "knowledge", name: "Knowledge", statement: "Grounded answers with evidence kept in view.", proof: ["Hybrid retrieval", "Source citations", "Confidence scoring"], showcaseHref: "/showcase/knowledge" },
  { id: "aurasql", name: "AuraSQL", statement: "Natural-language questions become reviewable, executable SQL.", proof: ["Schema context", "SQL validation", "Exportable results"], showcaseHref: "/showcase/aurasql" },
  { id: "analysis", name: "Analysis", statement: "Multi-agent analysis becomes an executive narrative, not a log wall.", proof: ["Statistical methods", "Visual reports", "Persistent jobs"], showcaseHref: "/showcase/analysis" },
  { id: "career", name: "Career Studio", statement: "Resume evidence turns into targeted, explainable improvements.", proof: ["JD alignment", "ATS scoring", "PDF generation"], showcaseHref: "/showcase/career" },
] as const;

export const PROOF_POINTS = [
  ["Retrieval", "BM25 + vector fusion with reranking"],
  ["Reasoning", "Fast and deep document navigation modes"],
  ["Data", "Schema-aware SQL generation and execution"],
  ["Operations", "Observable long-running analysis workflows"],
] as const;

export const CREATOR_SUMMARY = {
  name: "Shivam Sourav",
  heading: "Built end to end by Shivam Sourav",
  body: "A solo-engineered AI platform spanning product design, retrieval, data systems, workflow orchestration, observability, and deployment.",
  href: "/developer",
} as const;
```

- [ ] **Step 4: Build the public component family**

Implement the components with these responsibilities and exact visible contracts:

- `PublicHeader`: `NEXUSMIND` wordmark; anchors for `Capabilities`, `Proof`, and `Creator`; `AppearanceControl`; an authenticated `Open workspace` link to `/apps` or unauthenticated `Launch live` link to `/auth`.
- `FlagshipHero`: eyebrow `A system for serious thinking`; H1 `Intelligence, made tangible.` with `made tangible` in editorial copper; body copy from the approved design; links `Explore showcase` and `Launch live workspace`; static `NexusAperture`; dynamically imported `CinematicScene` with `ssr: false`.
- `CapabilityStory`: `<section id="capabilities">` mapping `CAPABILITIES` to four outcome-led stories; no generic dashboard card grid.
- `TechnicalProof`: `<section id="proof">` rendering `PROOF_POINTS` and repository-backed architecture statements only.
- `CreatorStory`: `<section id="creator">` using `CREATOR_SUMMARY` after proof.
- `PublicFooter`: `Designed and engineered by Shivam Sourav`, links to `/developer`, `/showcase`, `/auth`, and `/apps`.

All sections use semantic headings, a maximum reading width of `72rem`, visible focus styles, and motion-safe reveals. Do not include fabricated usage counts, customer claims, latency claims, or testimonials.

Use these complete component structures:

```tsx
// frontend/components/flagship/PublicHeader.tsx
"use client";
import Link from "next/link";
import { AppearanceControl } from "@/components/theme/AppearanceControl";
import { useAuthStore } from "@/lib/store";

export function PublicHeader() {
  const { isAuthenticated } = useAuthStore();
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-6 px-4 sm:px-6">
        <Link href="/" className="font-black tracking-[.18em]">NEXUSMIND</Link>
        <nav aria-label="Public" className="ml-auto hidden items-center gap-5 text-sm text-muted-foreground md:flex">
          <Link href="/#capabilities">Capabilities</Link><Link href="/#proof">Proof</Link><Link href="/#creator">Creator</Link>
        </nav>
        <AppearanceControl />
        <Link className="rounded-full bg-foreground px-4 py-2 text-sm font-semibold text-background" href={isAuthenticated ? "/apps" : "/auth"}>
          {isAuthenticated ? "Open workspace" : "Launch live"}
        </Link>
      </div>
    </header>
  );
}
```

```tsx
// frontend/components/flagship/FlagshipHero.tsx
"use client";
import dynamic from "next/dynamic";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { NexusAperture } from "@/components/brand/NexusAperture";
import { useCinematicEffects } from "@/hooks/useCinematicEffects";
const CinematicScene = dynamic(() => import("@/components/brand/CinematicScene"), { ssr: false });

export function FlagshipHero() {
  const { enabled, visible } = useCinematicEffects();
  return (
    <section className="relative isolate flex min-h-[92svh] items-center overflow-hidden px-4 pb-20 pt-28 sm:px-6">
      {enabled ? <CinematicScene active={visible} /> : null}
      <div className="mx-auto grid w-full max-w-7xl items-center gap-14 lg:grid-cols-[1.1fr_.9fr]">
        <div className="relative z-10">
          <p className="font-mono text-xs font-semibold uppercase tracking-[.28em] text-[hsl(var(--signal))]">A system for serious thinking</p>
          <h1 className="mt-6 max-w-4xl text-5xl font-black leading-[.92] tracking-[-.06em] sm:text-7xl lg:text-8xl">
            Intelligence,<br /><em className="font-editorial font-normal text-[hsl(var(--copper))]">made tangible.</em>
          </h1>
          <p className="mt-7 max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">Grounded research, data intelligence, and high-stakes output in one authored system.</p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link href="/showcase" className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 font-semibold text-primary-foreground">Explore showcase <ArrowRight className="h-4 w-4" /></Link>
            <Link href="/auth" className="rounded-full border border-border px-5 py-3 font-semibold">Launch live workspace</Link>
          </div>
        </div>
        <div className="relative mx-auto grid min-h-80 w-full place-items-center"><NexusAperture className="w-72 sm:w-96" /></div>
      </div>
    </section>
  );
}
```

```tsx
// frontend/components/flagship/CapabilityStory.tsx
import Link from "next/link";
import { CAPABILITIES } from "@/lib/flagship-content";

export function CapabilityStory() {
  return (
    <section id="capabilities" className="border-y border-border/60 bg-card/40 px-4 py-24 sm:px-6">
      <div className="mx-auto max-w-7xl">
        <p className="font-mono text-xs uppercase tracking-[.24em] text-primary">One platform · Four outcomes</p>
        <h2 className="mt-4 max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">Move from evidence to a finished decision.</h2>
        <div className="mt-14 divide-y divide-border/70">
          {CAPABILITIES.map((item, index) => (
            <article key={item.id} className="grid gap-6 py-9 md:grid-cols-[5rem_1fr_1fr_auto] md:items-center">
              <span className="font-mono text-sm text-muted-foreground">0{index + 1}</span>
              <h3 className="text-2xl font-bold">{item.name}</h3>
              <div><p className="text-muted-foreground">{item.statement}</p><p className="mt-2 text-sm">{item.proof.join(" · ")}</p></div>
              <Link className="font-semibold text-primary" href={item.showcaseHref}>Experience →</Link>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
```

```tsx
// frontend/components/flagship/TechnicalProof.tsx
import { ReasoningThreads } from "@/components/brand/ReasoningThreads";
import { PROOF_POINTS } from "@/lib/flagship-content";

export function TechnicalProof() {
  return (
    <section id="proof" className="px-4 py-24 sm:px-6">
      <div className="mx-auto max-w-7xl">
        <p className="font-mono text-xs uppercase tracking-[.24em] text-primary">Technical proof</p>
        <h2 className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl">Substance behind the surface.</h2>
        <div className="relative mt-12 overflow-hidden rounded-3xl border border-border bg-card">
          <ReasoningThreads className="h-48 border-b border-border opacity-70" />
          <dl className="grid gap-px bg-border md:grid-cols-2">
            {PROOF_POINTS.map(([term, detail]) => <div key={term} className="bg-card p-7"><dt className="font-mono text-xs uppercase tracking-[.2em] text-[hsl(var(--copper))]">{term}</dt><dd className="mt-3 text-lg font-semibold">{detail}</dd></div>)}
          </dl>
        </div>
      </div>
    </section>
  );
}
```

```tsx
// frontend/components/flagship/CreatorStory.tsx
import Link from "next/link";
import { CREATOR_SUMMARY } from "@/lib/flagship-content";

export function CreatorStory() {
  return (
    <section id="creator" className="px-4 py-24 sm:px-6">
      <div className="mx-auto grid max-w-7xl gap-8 rounded-[2rem] bg-foreground p-8 text-background sm:p-12 lg:grid-cols-[.8fr_1.2fr]">
        <p className="font-mono text-xs uppercase tracking-[.24em] text-[hsl(var(--copper))]">The creator behind the system</p>
        <div><h2 className="text-4xl font-bold tracking-tight">{CREATOR_SUMMARY.heading}</h2><p className="mt-5 max-w-2xl leading-7 opacity-70">{CREATOR_SUMMARY.body}</p><Link className="mt-7 inline-flex font-semibold text-[hsl(var(--signal))]" href={CREATOR_SUMMARY.href}>Read the engineering story →</Link></div>
      </div>
    </section>
  );
}
```

```tsx
// frontend/components/flagship/PublicFooter.tsx
import Link from "next/link";
export function PublicFooter() {
  return <footer className="border-t border-border px-4 py-8 sm:px-6"><div className="mx-auto flex max-w-7xl flex-col gap-4 text-sm text-muted-foreground sm:flex-row sm:items-center"><p>Designed and engineered by Shivam Sourav.</p><nav aria-label="Footer" className="sm:ml-auto flex gap-5"><Link href="/developer">Developer</Link><Link href="/showcase">Showcase</Link><Link href="/auth">Live</Link><Link href="/apps">Apps</Link></nav></div></footer>;
}
```

- [ ] **Step 5: Replace the root route with static-first composition**

Replace `frontend/app/page.tsx` with a server component that imports the six public components and renders them in this order:

```tsx
import { CapabilityStory } from "@/components/flagship/CapabilityStory";
import { CreatorStory } from "@/components/flagship/CreatorStory";
import { FlagshipHero } from "@/components/flagship/FlagshipHero";
import { PublicFooter } from "@/components/flagship/PublicFooter";
import { PublicHeader } from "@/components/flagship/PublicHeader";
import { TechnicalProof } from "@/components/flagship/TechnicalProof";

export default function FlagshipPage() {
  return (
    <div className="min-h-screen overflow-x-clip bg-background text-foreground">
      <PublicHeader />
      <main>
        <FlagshipHero />
        <CapabilityStory />
        <TechnicalProof />
        <CreatorStory />
      </main>
      <PublicFooter />
    </div>
  );
}
```

The page must not import `apiClient`, `useAppCatalog`, `AuthPage`, `ShaderAnimation`, or router-prefetch logic.

- [ ] **Step 6: Verify the flagship contract, bundle boundary, and build**

Run:

```bash
cd frontend
npm test -- tests/components/FlagshipPage.test.tsx
npm run typecheck
npm run build
rg "apiClient|useAppCatalog|AuthPage|ShaderAnimation" app/page.tsx
```

Expected: all seven expectations PASS; typecheck/build exit `0`; final `rg` produces no matches.

- [ ] **Step 7: Commit the public flagship**

```bash
git add frontend/lib/flagship-content.ts frontend/components/flagship frontend/app/page.tsx frontend/tests/components/FlagshipPage.test.tsx
git commit -m "feat(frontend): launch cinematic flagship homepage"
```

---

### Task 5: Deterministic Recruiter Showcase

**Files:**
- Create: `frontend/lib/showcase/types.ts`
- Create: `frontend/lib/showcase/fixtures.ts`
- Create: `frontend/lib/showcase/reducer.ts`
- Create: `frontend/components/showcase/ShowcaseProvider.tsx`
- Create: `frontend/components/showcase/ShowcaseShell.tsx`
- Create: `frontend/components/showcase/ShowcaseExperience.tsx`
- Create: `frontend/app/showcase/page.tsx`
- Create: `frontend/app/showcase/[experience]/page.tsx`
- Create: `frontend/tests/lib/showcase.test.ts`

**Interfaces:**
- Produces: `ShowcaseId`, `ShowcaseScenario`, `ShowcaseState`, `getShowcaseScenario(id)`, and `showcaseReducer(state, action)`.
- Route contract: only `knowledge`, `aurasql`, `analysis`, and `career` are valid dynamic segments.
- Constraint: no showcase file imports `apiClient`, authenticated stores, or live feature hooks.

- [ ] **Step 1: Write failing fixture and reducer tests**

Create `frontend/tests/lib/showcase.test.ts`:

```ts
import { getShowcaseScenario, SHOWCASE_SCENARIOS } from "@/lib/showcase/fixtures";
import { initialShowcaseState, showcaseReducer } from "@/lib/showcase/reducer";

describe("showcase", () => {
  it("defines all approved deterministic experiences", () => {
    expect(Object.keys(SHOWCASE_SCENARIOS)).toEqual(["knowledge", "aurasql", "analysis", "career"]);
  });

  it("rejects unknown route input", () => expect(getShowcaseScenario("billing")).toBeNull());

  it("advances one step at a time and clamps at the end", () => {
    const scenario = getShowcaseScenario("knowledge")!;
    let state = initialShowcaseState(scenario);
    state = showcaseReducer(state, { type: "advance" });
    expect(state.activeStep).toBe(1);
    for (let index = 0; index < 20; index += 1) state = showcaseReducer(state, { type: "advance" });
    expect(state.activeStep).toBe(scenario.steps.length - 1);
    expect(state.status).toBe("complete");
  });

  it("restarts without retaining simulated output state", () => {
    const scenario = getShowcaseScenario("aurasql")!;
    const advanced = showcaseReducer(initialShowcaseState(scenario), { type: "advance" });
    expect(showcaseReducer(advanced, { type: "restart" })).toEqual(initialShowcaseState(scenario));
  });
});
```

- [ ] **Step 2: Run the tests and verify missing-module failures**

Run: `cd frontend && npm test -- tests/lib/showcase.test.ts`

Expected: FAIL because showcase modules do not exist.

- [ ] **Step 3: Define scenario and state contracts**

Create `frontend/lib/showcase/types.ts`:

```ts
export type ShowcaseId = "knowledge" | "aurasql" | "analysis" | "career";
export type ShowcaseStatus = "ready" | "running" | "complete";

export interface ShowcaseStep {
  id: string;
  label: string;
  title: string;
  summary: string;
  evidence: readonly string[];
}

export interface ShowcaseScenario {
  id: ShowcaseId;
  eyebrow: string;
  title: string;
  prompt: string;
  accent: "knowledge" | "data" | "analysis" | "career";
  steps: readonly ShowcaseStep[];
}

export interface ShowcaseState {
  scenario: ShowcaseScenario;
  activeStep: number;
  status: ShowcaseStatus;
}

export type ShowcaseAction = { type: "advance" } | { type: "restart" };
```

- [ ] **Step 4: Create repository-backed deterministic fixtures**

Create `frontend/lib/showcase/fixtures.ts`:

```ts
import type { ShowcaseId, ShowcaseScenario } from "./types";

const steps = (items: Array<[string, string, string, readonly string[]]>) =>
  items.map(([id, title, summary, evidence], index) => ({ id, label: `0${index + 1}`, title, summary, evidence }));

export const SHOWCASE_SCENARIOS: Record<ShowcaseId, ShowcaseScenario> = {
  knowledge: {
    id: "knowledge", eyebrow: "Grounded knowledge", title: "Trace an answer back to evidence.",
    prompt: "Summarize the revenue risks and cite the strongest evidence.", accent: "knowledge",
    steps: steps([
      ["retrieve", "Retrieve", "Hybrid search combines semantic and keyword candidates.", ["BM25 keyword signal", "Vector similarity", "User-scoped documents"]],
      ["rerank", "Rerank", "The strongest passages are reordered for the question.", ["Cross-encoder relevance", "Duplicate suppression", "Top evidence retained"]],
      ["answer", "Answer", "The response keeps citations and confidence visible.", ["Three cited sources", "94% confidence", "Evidence inspector ready"]],
    ]),
  },
  aurasql: {
    id: "aurasql", eyebrow: "Schema-aware data", title: "Move from intent to a reviewable result.",
    prompt: "Show quarterly revenue growth by region for the last two years.", accent: "data",
    steps: steps([
      ["ask", "Ask", "The question is grounded in the active warehouse context.", ["Production warehouse selected", "Relevant tables identified", "Business intent retained"]],
      ["review", "Review", "Generated SQL is formatted and validated before execution.", ["Schema names verified", "Read-only statement", "Validation passed"]],
      ["results", "Results", "A deterministic result is ready for inspection or export.", ["24 rows returned", "Three columns", "Chart and CSV available"]],
    ]),
  },
  analysis: {
    id: "analysis", eyebrow: "Multi-agent analysis", title: "Turn a dataset into an executive narrative.",
    prompt: "Find the strongest drivers of churn and recommend actions.", accent: "analysis",
    steps: steps([
      ["plan", "Plan", "The workflow chooses methods that match the dataset and question.", ["Data quality checked", "Correlation selected", "Segment analysis queued"]],
      ["execute", "Execute", "Specialized agents run the approved statistical work.", ["Five segments compared", "Outliers inspected", "Visual evidence generated"]],
      ["narrate", "Narrate", "Findings become a prioritized decision brief.", ["Four findings ranked", "Methods disclosed", "Report ready"]],
    ]),
  },
  career: {
    id: "career", eyebrow: "Career intelligence", title: "Make resume improvements explainable.",
    prompt: "Align this resume to the role without inventing experience.", accent: "career",
    steps: steps([
      ["compare", "Compare", "Resume evidence is matched to the job description.", ["Skills mapped", "Gaps identified", "Existing evidence preserved"]],
      ["improve", "Improve", "Suggested changes remain reviewable and reversible.", ["Impact language refined", "Keywords contextualized", "Diff ready"]],
      ["export", "Export", "The approved resume is prepared as a polished artifact.", ["ATS score updated", "Human approval retained", "PDF ready"]],
    ]),
  },
};

export function getShowcaseScenario(id: string): ShowcaseScenario | null {
  return Object.prototype.hasOwnProperty.call(SHOWCASE_SCENARIOS, id)
    ? SHOWCASE_SCENARIOS[id as ShowcaseId]
    : null;
}
```

- [ ] **Step 5: Implement the pure reducer**

Create `frontend/lib/showcase/reducer.ts`:

```ts
import type { ShowcaseAction, ShowcaseScenario, ShowcaseState } from "./types";

export const initialShowcaseState = (scenario: ShowcaseScenario): ShowcaseState => ({
  scenario,
  activeStep: 0,
  status: "ready",
});

export function showcaseReducer(state: ShowcaseState, action: ShowcaseAction): ShowcaseState {
  if (action.type === "restart") return initialShowcaseState(state.scenario);
  const last = state.scenario.steps.length - 1;
  const activeStep = Math.min(state.activeStep + 1, last);
  return { ...state, activeStep, status: activeStep === last ? "complete" : "running" };
}
```

- [ ] **Step 6: Build the showcase presentation and routes**

Create the provider:

```tsx
// frontend/components/showcase/ShowcaseProvider.tsx
"use client";
import { createContext, useContext, useMemo, useReducer } from "react";
import { initialShowcaseState, showcaseReducer } from "@/lib/showcase/reducer";
import type { ShowcaseScenario, ShowcaseState } from "@/lib/showcase/types";

interface Value { state: ShowcaseState; advance(): void; restart(): void; }
const Context = createContext<Value | null>(null);
export function ShowcaseProvider({ scenario, children }: { scenario: ShowcaseScenario; children: React.ReactNode }) {
  const [state, dispatch] = useReducer(showcaseReducer, scenario, initialShowcaseState);
  const value = useMemo(() => ({ state, advance: () => dispatch({ type: "advance" }), restart: () => dispatch({ type: "restart" }) }), [state]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useShowcase() {
  const value = useContext(Context);
  if (!value) throw new Error("useShowcase must be used within ShowcaseProvider");
  return value;
}
```

Create the shell and experience:

```tsx
// frontend/components/showcase/ShowcaseShell.tsx
import Link from "next/link";
import { AppearanceControl } from "@/components/theme/AppearanceControl";
const routes = [["Knowledge","knowledge"],["AuraSQL","aurasql"],["Analysis","analysis"],["Career","career"]] as const;
export function ShowcaseShell({ children }: { children: React.ReactNode }) {
  return <div className="min-h-screen bg-background text-foreground"><div role="status" className="bg-[hsl(var(--copper))] px-4 py-2 text-center font-mono text-xs font-bold uppercase tracking-[.18em] text-black">Showcase mode · Precomputed demonstration</div><header className="border-b border-border"><div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-4"><Link href="/" className="font-black tracking-[.16em]">NEXUSMIND</Link><nav aria-label="Showcase experiences" className="ml-auto hidden gap-4 text-sm md:flex">{routes.map(([label,id]) => <Link key={id} href={`/showcase/${id}`}>{label}</Link>)}</nav><AppearanceControl /><Link className="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground" href="/auth">Use the live workspace</Link></div></header>{children}</div>;
}
```

```tsx
// frontend/components/showcase/ShowcaseExperience.tsx
"use client";
import { useShowcase } from "./ShowcaseProvider";
export function ShowcaseExperience() {
  const { state, advance, restart } = useShowcase();
  const active = state.scenario.steps[state.activeStep];
  return <main className="mx-auto grid max-w-7xl gap-10 px-4 py-16 lg:grid-cols-[.75fr_1.25fr]"><section><p className="font-mono text-xs uppercase tracking-[.22em] text-primary">{state.scenario.eyebrow}</p><h1 className="mt-4 text-4xl font-bold tracking-tight sm:text-6xl">{state.scenario.title}</h1><div className="mt-8 rounded-2xl border border-border bg-card p-5"><p className="text-xs uppercase tracking-wider text-muted-foreground">Prompt</p><p className="mt-2 font-semibold">{state.scenario.prompt}</p></div></section><section className="rounded-3xl border border-border bg-card p-6 sm:p-8"><ol className="grid grid-cols-3 gap-2">{state.scenario.steps.map((step,index) => <li key={step.id} aria-current={index === state.activeStep ? "step" : undefined} className={`rounded-xl border p-3 ${index <= state.activeStep ? "border-primary bg-primary/5" : "border-border"}`}><span className="font-mono text-xs">{step.label}</span><strong className="mt-2 block">{step.title}</strong></li>)}</ol><div className="mt-8 min-h-56 rounded-2xl bg-muted p-6"><p className="font-mono text-xs uppercase tracking-[.18em] text-[hsl(var(--copper))]">{state.status}</p><h2 className="mt-3 text-2xl font-bold">{active.title}</h2><p className="mt-3 text-muted-foreground">{active.summary}</p><ul className="mt-6 space-y-2">{active.evidence.map((item) => <li key={item}>✓ {item}</li>)}</ul></div><div className="mt-6 flex gap-3"><button onClick={advance} disabled={state.status === "complete"} className="rounded-full bg-primary px-5 py-3 font-semibold text-primary-foreground disabled:opacity-50">Continue demonstration</button><button onClick={restart} className="rounded-full border border-border px-5 py-3 font-semibold">Restart</button></div></section></main>;
}
```

Create the overview:

```tsx
// frontend/app/showcase/page.tsx
import Link from "next/link";
import { ShowcaseShell } from "@/components/showcase/ShowcaseShell";
import { SHOWCASE_SCENARIOS } from "@/lib/showcase/fixtures";
export default function ShowcasePage() {
  return <ShowcaseShell><main className="mx-auto max-w-7xl px-4 py-20"><p className="font-mono text-xs uppercase tracking-[.22em] text-primary">Choose a guided outcome</p><h1 className="mt-4 max-w-4xl text-5xl font-bold tracking-tight">Explore the system without infrastructure or credentials.</h1><div className="mt-12 grid gap-5 md:grid-cols-2">{Object.values(SHOWCASE_SCENARIOS).map((scenario) => <Link key={scenario.id} href={`/showcase/${scenario.id}`} className="rounded-3xl border border-border bg-card p-7"><span className="font-mono text-xs uppercase tracking-wider text-[hsl(var(--copper))]">{scenario.eyebrow}</span><h2 className="mt-3 text-2xl font-bold">{scenario.title}</h2><p className="mt-4 text-muted-foreground">{scenario.prompt}</p></Link>)}</div></main></ShowcaseShell>;
}
```

Create the dynamic route:

```ts
export function generateStaticParams() {
  return ["knowledge", "aurasql", "analysis", "career"].map((experience) => ({ experience }));
}
```

```tsx
// frontend/app/showcase/[experience]/page.tsx
import { notFound } from "next/navigation";
import { ShowcaseExperience } from "@/components/showcase/ShowcaseExperience";
import { ShowcaseProvider } from "@/components/showcase/ShowcaseProvider";
import { ShowcaseShell } from "@/components/showcase/ShowcaseShell";
import { getShowcaseScenario } from "@/lib/showcase/fixtures";
export function generateStaticParams() { return ["knowledge", "aurasql", "analysis", "career"].map((experience) => ({ experience })); }
export default function Page({ params }: { params: { experience: string } }) {
  const scenario = getShowcaseScenario(params.experience);
  if (!scenario) notFound();
  return <ShowcaseProvider scenario={scenario}><ShowcaseShell><ShowcaseExperience /></ShowcaseShell></ShowcaseProvider>;
}
```

- [ ] **Step 7: Verify determinism, route safety, and build**

Run:

```bash
cd frontend
npm test -- tests/lib/showcase.test.ts
npm run typecheck
npm run build
rg "apiClient|useAuthStore|useChat|useAnalysis" lib/showcase components/showcase app/showcase
```

Expected: four tests PASS; all five showcase pages are emitted by the build; final `rg` has no matches.

- [ ] **Step 8: Commit showcase mode**

```bash
git add frontend/lib/showcase frontend/components/showcase frontend/app/showcase frontend/tests/lib/showcase.test.ts
git commit -m "feat(frontend): add deterministic product showcase"
```

---

### Task 6: Focused Authentication Experience

**Files:**
- Create: `frontend/components/auth/AuthPanel.tsx`
- Create: `frontend/tests/components/AuthPanel.test.tsx`
- Create: `frontend/lib/public-routes.ts`
- Create: `frontend/tests/lib/public-routes.test.ts`
- Create: `frontend/components/layout/RouteProviders.tsx`
- Modify: `frontend/app/auth/page.tsx`
- Modify: `frontend/app/layout.tsx`

**Interfaces:**
- Produces: `AuthPanel` with injectable `onLogin` and `onRegister` async callbacks.
- Preserves: `apiClient.login(email, password)` and `apiClient.register(email, password, fullName)`.
- Route contract: successful login or registration redirects to `/apps`.
- Provider contract: `/`, `/auth`, `/developer`, and `/showcase/*` never mount catalog/job API providers; live product routes do.

- [ ] **Step 1: Write failing form behavior and public-route policy tests**

Create `frontend/tests/components/AuthPanel.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthPanel } from "@/components/auth/AuthPanel";

describe("AuthPanel", () => {
  it("submits login credentials", async () => {
    const onLogin = vi.fn().mockResolvedValue(undefined);
    render(<AuthPanel onLogin={onLogin} onRegister={vi.fn()} />);
    await userEvent.type(screen.getByLabelText(/email/i), "shivam@example.com");
    await userEvent.type(screen.getByLabelText(/^password$/i), "secret-pass");
    await userEvent.click(screen.getByRole("button", { name: /enter nexusmind/i }));
    expect(onLogin).toHaveBeenCalledWith({ email: "shivam@example.com", password: "secret-pass" });
  });

  it("blocks mismatched registration passwords", async () => {
    const onRegister = vi.fn();
    render(<AuthPanel onLogin={vi.fn()} onRegister={onRegister} />);
    await userEvent.click(screen.getByRole("tab", { name: /create account/i }));
    await userEvent.type(screen.getByLabelText(/full name/i), "Shivam Sourav");
    await userEvent.type(screen.getByLabelText(/email/i), "shivam@example.com");
    await userEvent.type(screen.getByLabelText(/^password$/i), "secret-pass");
    await userEvent.type(screen.getByLabelText(/confirm password/i), "different-pass");
    await userEvent.click(screen.getByRole("button", { name: /create workspace/i }));
    expect(onRegister).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/passwords do not match/i);
  });
});
```

Create `frontend/tests/lib/public-routes.test.ts`:

```ts
import { isPublicRoute } from "@/lib/public-routes";

describe("isPublicRoute", () => {
  it.each(["/", "/auth", "/developer", "/showcase", "/showcase/knowledge"])(
    "keeps %s independent of live API providers",
    (pathname) => expect(isPublicRoute(pathname)).toBe(true),
  );

  it.each(["/apps", "/chat", "/aurasql/query", "/analysis"])(
    "mounts live providers for %s",
    (pathname) => expect(isPublicRoute(pathname)).toBe(false),
  );
});
```

- [ ] **Step 2: Run tests and verify the missing-component failure**

Run: `cd frontend && npm test -- tests/components/AuthPanel.test.tsx tests/lib/public-routes.test.ts`

Expected: FAIL because `AuthPanel` and `public-routes` do not exist.

- [ ] **Step 3: Implement the testable panel**

Create `frontend/components/auth/AuthPanel.tsx`:

```tsx
"use client";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export interface LoginValues { email: string; password: string; }
export interface RegisterValues extends LoginValues { fullName: string; }
interface AuthPanelProps {
  onLogin(values: LoginValues): Promise<void>;
  onRegister(values: RegisterValues): Promise<void>;
}

export function AuthPanel({ onLogin, onRegister }: AuthPanelProps) {
  const [tab, setTab] = useState("login");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const data = new FormData(event.currentTarget);
    try { await onLogin({ email: String(data.get("email")), password: String(data.get("password")) }); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to sign in."); }
    finally { setBusy(false); }
  }

  async function submitRegistration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const data = new FormData(event.currentTarget);
    const fullName = String(data.get("fullName")).trim();
    const email = String(data.get("email"));
    const password = String(data.get("password"));
    if (!fullName) { setError("Full name is required."); return; }
    if (password !== String(data.get("confirmation"))) { setError("Passwords do not match."); return; }
    setBusy(true);
    try { await onRegister({ fullName, email, password }); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to create the workspace."); }
    finally { setBusy(false); }
  }

  const field = "mt-2";
  return <Tabs value={tab} onValueChange={(value) => { setTab(value); setError(""); }}>
    <TabsList className="grid w-full grid-cols-2"><TabsTrigger value="login">Sign in</TabsTrigger><TabsTrigger value="register">Create account</TabsTrigger></TabsList>
    {error ? <p id="auth-error" role="alert" className="mt-4 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
    <TabsContent value="login"><form onSubmit={submitLogin} className="mt-6 space-y-5"><div><Label htmlFor="login-email">Email</Label><Input className={field} id="login-email" name="email" type="email" required aria-describedby={error ? "auth-error" : undefined} /></div><div><Label htmlFor="login-password">Password</Label><Input className={field} id="login-password" name="password" type="password" required minLength={8} /></div><Button className="w-full" disabled={busy} type="submit">{busy ? "Authenticating…" : "Enter NexusMind"}</Button></form></TabsContent>
    <TabsContent value="register"><form onSubmit={submitRegistration} className="mt-6 space-y-5"><div><Label htmlFor="register-name">Full name</Label><Input className={field} id="register-name" name="fullName" required /></div><div><Label htmlFor="register-email">Email</Label><Input className={field} id="register-email" name="email" type="email" required /></div><div><Label htmlFor="register-password">Password</Label><Input className={field} id="register-password" name="password" type="password" required minLength={8} /></div><div><Label htmlFor="register-confirmation">Confirm password</Label><Input className={field} id="register-confirmation" name="confirmation" type="password" required minLength={8} /></div><Button className="w-full" disabled={busy} type="submit">{busy ? "Creating…" : "Create workspace"}</Button></form></TabsContent>
    <p aria-live="polite" className="sr-only">{busy ? "Authentication request in progress" : ""}</p>
  </Tabs>;
}
```

- [ ] **Step 4: Recompose the auth route around the panel**

Replace `frontend/app/auth/page.tsx` with:

```tsx
"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthPanel, type LoginValues, type RegisterValues } from "@/components/auth/AuthPanel";
import { NexusAperture } from "@/components/brand/NexusAperture";
import { AppearanceControl } from "@/components/theme/AppearanceControl";
import { useToast } from "@/hooks/useToast";
import { apiClient } from "@/lib/api";

export default function AuthPage() {
  const router = useRouter();
  const { toast } = useToast();
  const fail = (reason: unknown, title: string) => {
    const error = reason instanceof Error ? reason : new Error("The request could not be completed.");
    toast({ title, description: error.message, variant: "destructive" });
    throw error;
  };
  const login = async ({ email, password }: LoginValues) => {
    try { await apiClient.login(email, password); toast({ title: "Welcome back", description: "Opening your workspace…" }); router.push("/apps"); }
    catch (reason) { fail(reason, "Login failed"); }
  };
  const register = async ({ fullName, email, password }: RegisterValues) => {
    try { await apiClient.register(email, password, fullName); await apiClient.login(email, password); toast({ title: "Workspace created", description: "Opening NexusMind…" }); router.push("/apps"); }
    catch (reason) { fail(reason, "Registration failed"); }
  };
  return <main className="relative min-h-screen overflow-hidden bg-background px-4 py-6 sm:px-6"><div className="mx-auto flex max-w-7xl items-center justify-between"><Link href="/" className="font-black tracking-[.16em]">NEXUSMIND</Link><AppearanceControl /></div><div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-7xl items-center gap-12 py-12 lg:grid-cols-[1.05fr_.95fr]"><section><NexusAperture className="mb-10 w-36" /><p className="font-mono text-xs uppercase tracking-[.24em] text-primary">Live workspace</p><h1 className="mt-4 max-w-2xl text-5xl font-black leading-[.95] tracking-[-.055em] sm:text-6xl">Your live NexusMind workspace.</h1><ul className="mt-8 space-y-3 text-muted-foreground"><li>Grounded answers with evidence</li><li>Schema-aware data intelligence</li><li>Persistent, observable workflows</li></ul><Link href="/showcase" className="mt-8 inline-flex font-semibold text-[hsl(var(--copper))]">Explore the showcase first →</Link></section><section className="rounded-[2rem] border border-border bg-card p-6 shadow-2xl sm:p-9"><h2 className="text-2xl font-bold">Enter the system</h2><p className="mt-2 text-sm text-muted-foreground">Authenticate to use live data and saved work.</p><div className="mt-7"><AuthPanel onLogin={login} onRegister={register} /></div></section></div></main>;
}
```

- [ ] **Step 5: Isolate public routes from live-data providers**

Create `frontend/lib/public-routes.ts`:

```ts
const PUBLIC_ROUTES = new Set(["/", "/auth", "/developer", "/showcase"]);

export function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.has(pathname) || pathname.startsWith("/showcase/");
}
```

Create `frontend/components/layout/RouteProviders.tsx`:

```tsx
"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { JobProvider } from "@/components/providers/JobProvider";
import { AppCatalogProvider } from "@/lib/apps/useAppCatalog";
import { isPublicRoute } from "@/lib/public-routes";

export function RouteProviders({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  if (isPublicRoute(pathname)) return children;
  return <AppCatalogProvider><JobProvider>{children}</JobProvider></AppCatalogProvider>;
}
```

In `frontend/app/layout.tsx`, remove the direct `JobProvider` and `AppCatalogProvider` imports, import `RouteProviders`, and use this provider boundary:

```tsx
<ClientProviders>
  <RouteProviders>{children}</RouteProviders>
</ClientProviders>
```

This is required for the offline public-route contract: mounting a provider that immediately fetches the application catalog is an API dependency even when the page does not consume the result.

- [ ] **Step 6: Verify auth behavior, route isolation, and build**

Run:

```bash
cd frontend
npm test -- tests/components/AuthPanel.test.tsx tests/lib/public-routes.test.ts
npm run typecheck
npm run build
rg "ShaderAnimation|ThemePalette|simpleicons|isLoginOverlayVisible" app/auth components/auth
rg "AppCatalogProvider|JobProvider" app/layout.tsx
```

Expected: all route-policy and auth tests PASS; typecheck/build exit `0`; both final `rg` commands have no matches.

- [ ] **Step 7: Commit focused authentication and public-route isolation**

```bash
git add frontend/components/auth/AuthPanel.tsx frontend/app/auth/page.tsx frontend/tests/components/AuthPanel.test.tsx frontend/lib/public-routes.ts frontend/tests/lib/public-routes.test.ts frontend/components/layout/RouteProviders.tsx frontend/app/layout.tsx
git commit -m "feat(frontend): simplify cinematic authentication"
```

---

### Task 7: Public Creator Engineering Profile

**Files:**
- Create: `frontend/lib/creator-profile.ts`
- Modify: `frontend/app/developer/page.tsx`
- Modify: `frontend/components/flagship/CreatorStory.tsx`
- Modify: `frontend/lib/flagship-content.ts`
- Create: `frontend/tests/components/DeveloperPage.test.tsx`

**Interfaces:**
- Produces: `CREATOR_PROFILE` as the single source for creator identity, ownership areas, engineering principles, and project links.
- Consumed by: homepage creator story and `/developer`.

- [ ] **Step 1: Write the failing creator-profile test**

Create `frontend/tests/components/DeveloperPage.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import DeveloperPage from "@/app/developer/page";

vi.mock("@/lib/store", () => ({ useAuthStore: () => ({ isAuthenticated: false }) }));
vi.mock("@/components/theme/AppearanceControl", () => ({
  AppearanceControl: () => <button aria-label="Appearance">Appearance</button>,
}));

describe("DeveloperPage", () => {
  it("states solo ownership and shows engineering breadth", () => {
    render(<DeveloperPage />);
    expect(screen.getByRole("heading", { name: /shivam sourav/i })).toBeInTheDocument();
    expect(screen.getByText(/solely designed and developed/i)).toBeInTheDocument();
    for (const area of ["Product design", "RAG systems", "Data intelligence", "Platform engineering"]) {
      expect(screen.getByRole("heading", { name: area })).toBeInTheDocument();
    }
  });

  it("returns visitors to product proof and showcase", () => {
    render(<DeveloperPage />);
    expect(screen.getByRole("link", { name: /view product/i })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: /explore showcase/i })).toHaveAttribute("href", "/showcase");
    expect(screen.getByRole("link", { name: /github/i })).toHaveAttribute("href", "https://github.com/Shivam5560");
    expect(screen.getByRole("link", { name: /linkedin/i })).toHaveAttribute("href", "https://linkedin.com/in/shivam-sourav-b889aa204/");
  });
});
```

- [ ] **Step 2: Run the test and verify failure against the current profile**

Run: `cd frontend && npm test -- tests/components/DeveloperPage.test.tsx`

Expected: FAIL because the required authored ownership language and headings are absent.

- [ ] **Step 3: Create the typed creator profile**

Create `frontend/lib/creator-profile.ts`:

```ts
export const CREATOR_PROFILE = {
  name: "Shivam Sourav",
  role: "Associate Software Engineer · Nomura Fintech",
  ownership: "NexusMind was solely designed and developed by Shivam Sourav—from product experience and frontend systems to retrieval, data workflows, observability, and deployment.",
  areas: [
    { title: "Product design", detail: "Information architecture, interaction systems, responsive UI, and accessible workflows." },
    { title: "RAG systems", detail: "Hybrid retrieval, reranking, citations, confidence, and document reasoning." },
    { title: "Data intelligence", detail: "Schema-aware SQL, multi-agent analysis, visualization, and reports." },
    { title: "Platform engineering", detail: "FastAPI services, PostgreSQL/pgvector, observability, containers, and application isolation." },
  ],
  principles: ["Evidence over spectacle", "Progressive disclosure", "Observable systems", "Performance by design"],
  links: [
    { label: "GitHub", href: "https://github.com/Shivam5560" },
    { label: "LinkedIn", href: "https://linkedin.com/in/shivam-sourav-b889aa204/" },
  ],
} as const;
```

- [ ] **Step 4: Rebuild `/developer` as an authored engineering narrative**

Replace `frontend/app/developer/page.tsx` with:

```tsx
import Link from "next/link";
import { NexusAperture } from "@/components/brand/NexusAperture";
import { PublicHeader } from "@/components/flagship/PublicHeader";
import { PublicFooter } from "@/components/flagship/PublicFooter";
import { CREATOR_PROFILE } from "@/lib/creator-profile";

const architecture = [
  ["Knowledge", "Hybrid retrieval, reranking, citations, and confidence."],
  ["AuraSQL", "Schema context, query generation, validation, and results."],
  ["Analysis", "Specialized agents, persistent jobs, charts, and reports."],
  ["Career Studio", "Resume evidence, JD alignment, review, and export."],
] as const;

export default function DeveloperPage() {
  return <div className="min-h-screen bg-background text-foreground"><PublicHeader /><main className="pt-16"><section className="px-4 py-24 sm:px-6"><div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[1fr_.7fr] lg:items-center"><div><p className="font-mono text-xs uppercase tracking-[.24em] text-primary">Creator and engineer</p><h1 className="mt-5 text-5xl font-black tracking-[-.055em] sm:text-7xl">{CREATOR_PROFILE.name}</h1><p className="mt-4 text-lg text-[hsl(var(--copper))]">{CREATOR_PROFILE.role}</p><p className="mt-7 max-w-3xl text-lg leading-8 text-muted-foreground">{CREATOR_PROFILE.ownership}</p><div className="mt-9 flex gap-3"><Link className="rounded-full bg-primary px-5 py-3 font-semibold text-primary-foreground" href="/">View product</Link><Link className="rounded-full border border-border px-5 py-3 font-semibold" href="/showcase">Explore showcase</Link></div><nav aria-label="Creator links" className="mt-6 flex gap-5 text-sm font-semibold text-muted-foreground">{CREATOR_PROFILE.links.map((link) => <a key={link.label} href={link.href} target="_blank" rel="noreferrer">{link.label}</a>)}</nav></div><NexusAperture className="mx-auto w-64" /></div></section><section className="border-y border-border bg-card/50 px-4 py-20 sm:px-6"><div className="mx-auto grid max-w-7xl gap-px overflow-hidden rounded-3xl border border-border bg-border md:grid-cols-2">{CREATOR_PROFILE.areas.map((area) => <article key={area.title} className="bg-card p-8"><h2 className="text-2xl font-bold">{area.title}</h2><p className="mt-3 leading-7 text-muted-foreground">{area.detail}</p></article>)}</div></section><section className="px-4 py-24 sm:px-6"><div className="mx-auto max-w-7xl"><p className="font-mono text-xs uppercase tracking-[.24em] text-primary">System architecture</p><h2 className="mt-4 text-4xl font-bold">One platform, four specialist experiences.</h2><div className="mt-12 divide-y divide-border">{architecture.map(([name, detail]) => <article key={name} className="grid gap-3 py-6 md:grid-cols-[12rem_1fr]"><h3 className="text-xl font-bold">{name}</h3><p className="text-muted-foreground">{detail}</p></article>)}</div><div className="mt-16 rounded-3xl bg-foreground p-8 text-background"><h2 className="text-3xl font-bold">Engineering principles</h2><ul className="mt-6 grid gap-4 sm:grid-cols-2">{CREATOR_PROFILE.principles.map((principle) => <li key={principle} className="border-l-2 border-[hsl(var(--copper))] pl-4">{principle}</li>)}</ul><p className="mt-8 max-w-3xl text-sm leading-7 opacity-70">Built with Next.js, React, TypeScript, FastAPI, PostgreSQL, pgvector, LlamaIndex, containerized services, and production observability.</p></div></div></section></main><PublicFooter /></div>;
}
```

Replace `frontend/components/flagship/CreatorStory.tsx` with:

```tsx
import Link from "next/link";
import { CREATOR_PROFILE } from "@/lib/creator-profile";
export function CreatorStory() {
  return <section id="creator" className="px-4 py-24 sm:px-6"><div className="mx-auto grid max-w-7xl gap-8 rounded-[2rem] bg-foreground p-8 text-background sm:p-12 lg:grid-cols-[.8fr_1.2fr]"><p className="font-mono text-xs uppercase tracking-[.24em] text-[hsl(var(--copper))]">The creator behind the system</p><div><h2 className="text-4xl font-bold tracking-tight">Built end to end by {CREATOR_PROFILE.name}</h2><p className="mt-5 max-w-2xl leading-7 opacity-70">{CREATOR_PROFILE.ownership}</p><Link className="mt-7 inline-flex font-semibold text-[hsl(var(--signal))]" href="/developer">Read the engineering story →</Link></div></div></section>;
}
```

Remove `CREATOR_SUMMARY` from `frontend/lib/flagship-content.ts`; `CREATOR_PROFILE` is now the only creator-content source.

- [ ] **Step 5: Verify profile contract, no remote icon dependencies, and build**

Run:

```bash
cd frontend
npm test -- tests/components/DeveloperPage.test.tsx tests/components/FlagshipPage.test.tsx
npm run typecheck
npm run build
rg "cdn.simpleicons|raw.githubusercontent|ShaderAnimation" app/developer components/flagship/CreatorStory.tsx
```

Expected: creator and flagship tests PASS; typecheck/build exit `0`; final `rg` has no matches.

- [ ] **Step 6: Commit the creator profile**

```bash
git add frontend/lib/creator-profile.ts frontend/lib/flagship-content.ts frontend/app/developer/page.tsx frontend/components/flagship/CreatorStory.tsx frontend/tests/components/DeveloperPage.test.tsx
git commit -m "feat(frontend): add authored creator engineering profile"
```

---

### Task 8: End-to-End Flagship Verification and Performance Guardrails

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/flagship.spec.ts`
- Modify: `frontend/next.config.js`
- Modify: `frontend/README.md`

**Interfaces:**
- Consumes: all prior task routes and accessible labels.
- Produces: `npm run test:e2e` and desktop/mobile regression coverage.

- [ ] **Step 1: Install Playwright and add the E2E script**

Run:

```bash
cd frontend
npm install --save-dev @playwright/test
npx playwright install chromium
```

Add scripts:

```json
"test:e2e": "playwright test",
"verify": "npm test && npm run typecheck && npm run build"
```

- [ ] **Step 2: Configure desktop and mobile projects**

Create `frontend/playwright.config.ts`:

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 1,
  reporter: "list",
  use: { baseURL: "http://127.0.0.1:3000", trace: "retain-on-failure" },
  webServer: {
    command: "npm run dev",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: true,
    timeout: 120_000,
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
    { name: "mobile-chromium", use: { ...devices["Pixel 7"] } },
  ],
});
```

- [ ] **Step 3: Write the end-to-end journeys**

Create `frontend/e2e/flagship.spec.ts`:

```ts
import { expect, test } from "@playwright/test";

test("flagship leads to a deterministic showcase", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /intelligence, made tangible/i })).toBeVisible();
  await page.getByRole("link", { name: /explore showcase/i }).first().click();
  await expect(page.getByText(/precomputed demonstration/i)).toBeVisible();
  await page.getByRole("link", { name: /move from intent/i }).click();
  await expect(page).toHaveURL(/showcase\/aurasql/);
  await page.getByRole("button", { name: /continue demonstration/i }).click();
  await expect(page.getByText(/review/i)).toBeVisible();
});

test("appearance persists across public routes", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /appearance/i }).click();
  await page.getByRole("menuitemradio", { name: /light/i }).click();
  await page.getByRole("link", { name: /read the engineering story/i }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme-mode", "light");
});

test("live CTA reaches focused authentication", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /launch live workspace/i }).first().click();
  await expect(page).toHaveURL(/\/auth$/);
  await expect(page.getByRole("button", { name: /enter nexusmind/i })).toBeVisible();
});

test("public experiences make no live API requests", async ({ page }) => {
  const apiRequests: string[] = [];
  page.on("request", (request) => {
    const pathname = new URL(request.url()).pathname;
    if (pathname.startsWith("/api/")) apiRequests.push(request.url());
  });

  for (const route of ["/", "/showcase", "/showcase/knowledge", "/developer", "/auth"]) {
    await page.goto(route);
    await expect(page.locator("main")).toBeVisible();
  }

  expect(apiRequests).toEqual([]);
});
```

- [ ] **Step 4: Add static security and loading headers**

Update `next.config.js` to keep `output: "standalone"` and `reactStrictMode: true`, and add headers for all routes:

```js
async headers() {
  return [{
    source: "/:path*",
    headers: [
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "X-Frame-Options", value: "DENY" },
    ],
  }]
}
```

Do not add a CSP in this phase because the inline flash-prevention script needs a nonce-based deployment design; record that explicitly in the README rather than shipping a broken policy.

- [ ] **Step 5: Document the public/live/showcase split**

Update `frontend/README.md` with:

- `/` public flagship.
- `/showcase/*` deterministic, backend-free, labeled demonstrations.
- `/auth` live authentication and `/apps` live catalog.
- `npm test`, `npm run test:e2e`, `npm run typecheck`, and `npm run verify` commands.
- Cinematic effects eligibility and graceful fallback behavior.
- LAN/Tailscale preview command `npm run dev -- --hostname 0.0.0.0` and the requirement to use the host machine's current Tailscale IP with port `3000`.
- Note that production CSP integration must provide a nonce for the theme bootstrap script.

- [ ] **Step 6: Run the complete foundation verification**

Run:

```bash
cd frontend
npm run verify
npm run test:e2e
```

Expected: all unit tests PASS; typecheck/build exit `0`; all four E2E tests pass in both desktop and mobile projects for eight passing results.

- [ ] **Step 7: Inspect the production route output and heavy dependency boundary**

Run:

```bash
cd frontend
npm run build
rg "from ['\"]three['\"]" app components lib -g '*.ts' -g '*.tsx'
```

Expected: `/`, `/showcase`, four showcase routes, `/auth`, and `/developer` build successfully. The only direct `three` imports in the new foundation are in `components/brand/CinematicScene.tsx`; existing legacy shader files may still contain imports but must not be imported by the new public routes.

- [ ] **Step 8: Commit the verified foundation slice**

```bash
git add frontend/package.json frontend/package-lock.json frontend/playwright.config.ts frontend/e2e/flagship.spec.ts frontend/next.config.js frontend/README.md
git commit -m "test(frontend): verify flagship experience"
```

---

## Phase Completion Gate

Before starting the shell and Knowledge follow-up plan, verify:

```bash
cd frontend
npm run verify
npm run test:e2e
git status --short
```

Required outcome:

- Unit, type, build, desktop E2E, and mobile E2E checks pass.
- `/` works with the backend stopped.
- `/showcase/*` makes no API requests and is visibly labeled.
- `/auth` preserves login and registration API behavior and redirects to `/apps`.
- Appearance has only system/light/dark choices and persists across routes.
- Public routes use no purple gradients or remote icon CDNs.
- The optional hero scene is dynamically loaded, pausable, and disposable.
- Git status contains only known pre-existing untracked graph/mockup artifacts.
