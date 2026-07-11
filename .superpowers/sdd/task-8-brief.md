### Task 8: Manifest-Driven Header Navigation

**Files:**

- Create: `frontend/components/platform/AppNavigation.tsx`
- Create: `frontend/components/platform/__tests__/AppNavigation.test.tsx`
- Modify: `frontend/components/layout/Header.tsx:1-160`

**Interfaces:**

- Consumes: `useAppCatalog()` from Task 6
- Produces: desktop and mobile links for enabled applications
- The dashboard and application-catalog links remain platform links.
- Catalog failure retains platform links and exposes no stale application links.

- [ ] **Step 1: Write enabled-app and failure-state tests**

```tsx
// frontend/components/platform/__tests__/AppNavigation.test.tsx
import { render, screen } from "@testing-library/react";

import { AppNavigation } from "../AppNavigation";

vi.mock("@/lib/apps/useAppCatalog", () => ({ useAppCatalog: vi.fn() }));
import { useAppCatalog } from "@/lib/apps/useAppCatalog";
const mockedCatalog = vi.mocked(useAppCatalog);

test("renders only enabled application links", () => {
  mockedCatalog.mockReturnValue({
    status: "success", error: null, retry: vi.fn(),
    apps: [{ id: "knowledge-studio", name: "Knowledge Studio", frontend_route: "/chat" }] as never,
  });
  render(<AppNavigation pathname="/chat" />);

  expect(screen.getByRole("link", { name: "Knowledge Studio" })).toHaveAttribute("href", "/chat");
  expect(screen.queryByRole("link", { name: "AuraSQL" })).not.toBeInTheDocument();
});


test("catalog failure keeps platform navigation usable", () => {
  mockedCatalog.mockReturnValue({ status: "error", apps: [], error: new Error("offline"), retry: vi.fn() });
  render(<AppNavigation pathname="/apps" />);

  expect(screen.getByRole("link", { name: "Applications" })).toHaveAttribute("href", "/apps");
  expect(screen.getByText(/application navigation unavailable/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test and confirm navigation is missing**

Run: `cd frontend && npm run test -- components/platform/__tests__/AppNavigation.test.tsx`

Expected: FAIL because `AppNavigation.tsx` does not exist.

- [ ] **Step 3: Implement manifest-driven navigation**

```tsx
// frontend/components/platform/AppNavigation.tsx
"use client";

import Link from "next/link";

import { cn } from "@/lib/utils";
import { useAppCatalog } from "@/lib/apps/useAppCatalog";

export function AppNavigation({ pathname, mobile = false }: { pathname: string; mobile?: boolean }) {
  const catalog = useAppCatalog();
  const baseClass = mobile ? "block rounded-md px-3 py-2 text-sm" : "rounded-md px-3 py-2 text-sm";
  const linkClass = (active: boolean) => cn(baseClass, active ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground");

  return (
    <nav aria-label="Primary applications" className={mobile ? "space-y-1" : "flex items-center gap-1"}>
      <Link className={linkClass(pathname === "/")} href="/">Dashboard</Link>
      <Link className={linkClass(pathname.startsWith("/apps"))} href="/apps">Applications</Link>
      {catalog.status === "success" && catalog.apps.map((app) => (
        <Link key={app.id} className={linkClass(pathname.startsWith(app.frontend_route))} href={app.frontend_route}>
          {app.name}
        </Link>
      ))}
      {catalog.status === "error" ? <span className="sr-only">Application navigation unavailable</span> : null}
    </nav>
  );
}
```

- [ ] **Step 4: Replace hard-coded application arrays in `Header`**

Add:

```tsx
import { AppNavigation } from "@/components/platform/AppNavigation";
```

Delete the `mainNavLinks` array. Replace the desktop map with:

```tsx
<div className="ml-6 hidden whitespace-nowrap lg:block">
  <AppNavigation pathname={pathname ?? "/"} />
</div>
```

Replace the mobile map with:

```tsx
<div className="absolute right-0 top-full z-50 mt-2 w-64 rounded-lg border border-border bg-background p-2 shadow-xl">
  <AppNavigation pathname={pathname ?? "/"} mobile />
</div>
```

Retain the existing mobile menu open/close button. Add an effect that closes `mobileNavOpen` when `pathname` changes:

```tsx
useEffect(() => { setMobileNavOpen(false); }, [pathname]);
```

- [ ] **Step 5: Run navigation and catalog tests**

Run: `cd frontend && npm run test -- components/platform`

Expected: all tests PASS.

- [ ] **Step 6: Run lint and production build**

Run: `cd frontend && npm run lint && npm run build`

Expected: both commands exit 0.

- [ ] **Step 7: Commit navigation**

```bash
git add frontend/components/platform/AppNavigation.tsx frontend/components/platform/__tests__/AppNavigation.test.tsx frontend/components/layout/Header.tsx
git commit -m "feat(frontend): drive application navigation from manifests"
```

