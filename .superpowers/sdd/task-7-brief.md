### Task 7: Accessible Application Catalog and Overview Pages

**Files:**

- Create: `frontend/components/platform/CapabilityBadge.tsx`
- Create: `frontend/components/platform/AppCard.tsx`
- Create: `frontend/components/platform/AppCatalog.tsx`
- Create: `frontend/components/platform/__tests__/AppCatalog.test.tsx`
- Create: `frontend/app/apps/page.tsx`
- Create: `frontend/app/apps/[appId]/page.tsx`
- Create: `frontend/app/apps/__tests__/page.test.tsx`

**Interfaces:**

- Consumes: `useAppCatalog()` and `getApp()` from Task 6
- Produces: `/apps` and `/apps/{appId}`
- Application cards expose one primary link named `Open {application name}`.
- The overview page links to the existing `frontend_route` and lists demo scenarios.

- [ ] **Step 1: Write catalog state and accessibility tests**

```tsx
// frontend/components/platform/__tests__/AppCatalog.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppCatalog } from "../AppCatalog";

vi.mock("@/lib/apps/useAppCatalog", () => ({ useAppCatalog: vi.fn() }));
import { useAppCatalog } from "@/lib/apps/useAppCatalog";

const mockedCatalog = vi.mocked(useAppCatalog);
const retry = vi.fn();

test("renders loading state with an accessible status", () => {
  mockedCatalog.mockReturnValue({ status: "loading", apps: [], error: null, retry });
  render(<AppCatalog />);
  expect(screen.getByRole("status", { name: /loading applications/i })).toBeInTheDocument();
});

test("renders retryable error state", async () => {
  mockedCatalog.mockReturnValue({ status: "error", apps: [], error: new Error("offline"), retry });
  render(<AppCatalog />);
  await userEvent.click(screen.getByRole("button", { name: /retry/i }));
  expect(retry).toHaveBeenCalledOnce();
});

test("renders app links and capability labels", () => {
  mockedCatalog.mockReturnValue({
    status: "success",
    error: null,
    retry,
    apps: [{
      id: "knowledge-studio", version: "1.0.0", name: "Knowledge Studio",
      summary: "Evidence-backed document intelligence.", category: "knowledge", icon: "book-open",
      frontend_route: "/chat", backend_route_prefixes: [], required_capabilities: ["auth", "retrieval"],
      backend_router_ids: [],
      optional_capabilities: [], required_permissions: [], required_env_keys: [], dependencies: [],
      demo_scenarios: [], health_check_id: "knowledge", packaging_paths: [],
    }],
  });
  render(<AppCatalog />);
  expect(screen.getByRole("link", { name: "Open Knowledge Studio" })).toHaveAttribute("href", "/apps/knowledge-studio");
  expect(screen.getByText("retrieval")).toBeInTheDocument();
});

test("catalog populated state has no automatic accessibility violations", async () => {
  const axe = (await import("axe-core")).default;
  mockedCatalog.mockReturnValue({
    status: "success", error: null, retry,
    apps: [{
      id: "knowledge-studio", version: "1.0.0", name: "Knowledge Studio",
      summary: "Evidence-backed document intelligence.", category: "knowledge", icon: "book-open",
      frontend_route: "/chat", backend_route_prefixes: [], required_capabilities: ["auth", "retrieval"],
      backend_router_ids: [],
      optional_capabilities: [], required_permissions: [], required_env_keys: [], dependencies: [],
      demo_scenarios: [], health_check_id: "knowledge", packaging_paths: [],
    }],
  });
  const { container } = render(<AppCatalog />);
  const result = await axe.run(container);
  expect(result.violations).toEqual([]);
});
```

```tsx
// frontend/app/apps/__tests__/page.test.tsx
import { render, screen } from "@testing-library/react";
import AppsPage from "../page";

vi.mock("@/components/platform/AppCatalog", () => ({
  AppCatalog: () => <div>Application catalog test double</div>,
}));

test("renders the application catalog route", () => {
  render(<AppsPage />);
  expect(screen.getByRole("heading", { name: /application showcase/i })).toBeInTheDocument();
  expect(screen.getByText("Application catalog test double")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test and confirm components are missing**

Run: `cd frontend && npm run test -- components/platform/__tests__/AppCatalog.test.tsx`

Expected: FAIL because `AppCatalog.tsx` does not exist.

- [ ] **Step 3: Implement capability badges and cards**

```tsx
// frontend/components/platform/CapabilityBadge.tsx
import type { Capability } from "@/lib/apps/types";

export function CapabilityBadge({ capability }: { capability: Capability }) {
  return (
    <span className="rounded-full border border-border bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
      {capability}
    </span>
  );
}
```

```tsx
// frontend/components/platform/AppCard.tsx
import Link from "next/link";

import { CapabilityBadge } from "./CapabilityBadge";
import type { AppManifest } from "@/lib/apps/types";

export function AppCard({ app }: { app: AppManifest }) {
  return (
    <article className="flex h-full flex-col rounded-2xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{app.category}</p>
          <h2 className="mt-2 text-xl font-semibold text-foreground">{app.name}</h2>
        </div>
        <span className="text-xs text-muted-foreground">v{app.version}</span>
      </div>
      <p className="mt-3 flex-1 text-sm leading-6 text-muted-foreground">{app.summary}</p>
      <div className="mt-5 flex flex-wrap gap-2" aria-label={`${app.name} capabilities`}>
        {app.required_capabilities.map((capability) => (
          <CapabilityBadge key={capability} capability={capability} />
        ))}
      </div>
      <Link className="mt-6 inline-flex font-semibold text-primary underline-offset-4 hover:underline" href={`/apps/${app.id}`}>
        Open {app.name}
      </Link>
    </article>
  );
}
```

- [ ] **Step 4: Implement all catalog states**

```tsx
// frontend/components/platform/AppCatalog.tsx
"use client";

import { AppCard } from "./AppCard";
import { Button } from "@/components/ui/button";
import { useAppCatalog } from "@/lib/apps/useAppCatalog";

export function AppCatalog() {
  const catalog = useAppCatalog();

  if (catalog.status === "loading") {
    return <div role="status" aria-label="Loading applications" className="py-16 text-muted-foreground">Loading applications…</div>;
  }
  if (catalog.status === "error") {
    return (
      <section role="alert" className="rounded-2xl border border-destructive/40 p-6">
        <h2 className="font-semibold">Application catalog unavailable</h2>
        <p className="mt-2 text-sm text-muted-foreground">{catalog.error.message}</p>
        <Button className="mt-4" onClick={() => void catalog.retry()}>Retry</Button>
      </section>
    );
  }
  if (catalog.status === "empty") {
    return (
      <section className="rounded-2xl border border-dashed border-border p-10 text-center">
        <h2 className="font-semibold">No applications are enabled</h2>
        <p className="mt-2 text-sm text-muted-foreground">Enable an application manifest to add it to this deployment.</p>
      </section>
    );
  }
  return (
    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
      {catalog.apps.map((app) => <AppCard key={app.id} app={app} />)}
    </div>
  );
}
```

- [ ] **Step 5: Implement the catalog route**

```tsx
// frontend/app/apps/page.tsx
import { AppCatalog } from "@/components/platform/AppCatalog";

export default function AppsPage() {
  return (
    <main className="mx-auto min-h-screen max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">NexusMind</p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight text-foreground">Application showcase</h1>
      <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">
        Production-grade AI reference applications built on reusable Nexus Core capabilities.
      </p>
      <section className="mt-10" aria-label="Enabled applications"><AppCatalog /></section>
    </main>
  );
}
```

- [ ] **Step 6: Implement the application overview route**

```tsx
// frontend/app/apps/[appId]/page.tsx
import Link from "next/link";
import { notFound } from "next/navigation";

import { getApp } from "@/lib/apps/client";
import { CapabilityBadge } from "@/components/platform/CapabilityBadge";
import type { AppManifest } from "@/lib/apps/types";

export default async function AppOverviewPage({ params }: { params: { appId: string } }) {
  let app: AppManifest;
  try {
    app = await getApp(params.appId);
  } catch {
    notFound();
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Link href="/apps" className="text-sm text-muted-foreground hover:text-foreground">← All applications</Link>
      <h1 className="mt-6 text-4xl font-semibold tracking-tight">{app.name}</h1>
      <p className="mt-4 max-w-3xl text-lg leading-8 text-muted-foreground">{app.summary}</p>
      <div className="mt-6 flex flex-wrap gap-2">{app.required_capabilities.map((item) => <CapabilityBadge key={item} capability={item} />)}</div>
      <Link href={app.frontend_route} className="mt-8 inline-flex rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground">Launch {app.name}</Link>
      <section className="mt-12" aria-labelledby="demo-scenarios">
        <h2 id="demo-scenarios" className="text-2xl font-semibold">Guided scenarios</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {app.demo_scenarios.map((scenario) => (
            <article key={scenario.id} className="rounded-xl border border-border p-5">
              <h3 className="font-semibold">{scenario.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{scenario.description}</p>
              <pre className="mt-4 whitespace-pre-wrap rounded-lg bg-muted p-3 text-xs">{scenario.starter_prompt}</pre>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
```

- [ ] **Step 7: Run component and route tests**

Run: `cd frontend && npm run test -- components/platform app/apps`

Expected: all catalog and route tests PASS.

- [ ] **Step 8: Commit the catalog experience**

```bash
git add frontend/components/platform frontend/app/apps
git commit -m "feat(frontend): add accessible application showcase"
```

