### Task 6: Typed Frontend Catalog Client and State Hook

**Files:**

- Create: `frontend/lib/apps/types.ts`
- Create: `frontend/lib/apps/client.ts`
- Create: `frontend/lib/apps/useAppCatalog.ts`
- Create: `frontend/lib/apps/__tests__/client.test.ts`
- Create: `frontend/lib/apps/__tests__/useAppCatalog.test.tsx`

**Interfaces:**

- Consumes: `GET /api/v1/apps` from Task 3
- Produces: `AppManifest`, `Capability`, `listApps()`, `getApp()`, and `useAppCatalog()`
- The hook exposes discriminated states: loading, success, empty, and error.

- [ ] **Step 1: Write client and hook tests**

```typescript
// frontend/lib/apps/__tests__/client.test.ts
import { listApps } from "../client";

test("loads the catalog from the versioned API", async () => {
  const fetcher = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => [{ id: "knowledge-studio", name: "Knowledge Studio" }],
  });

  const result = await listApps(fetcher as typeof fetch);

  expect(fetcher).toHaveBeenCalledWith(
    expect.stringMatching(/\/api\/v1\/apps$/),
    expect.objectContaining({ headers: { Accept: "application/json" } }),
  );
  expect(result[0].id).toBe("knowledge-studio");
});


test("throws a useful error for an unavailable catalog", async () => {
  const fetcher = vi.fn().mockResolvedValue({ ok: false, status: 503 });

  await expect(listApps(fetcher as typeof fetch)).rejects.toThrow("Application catalog unavailable (503)");
});
```

```tsx
// frontend/lib/apps/__tests__/useAppCatalog.test.tsx
import { act, renderHook, waitFor } from "@testing-library/react";

import { useAppCatalog } from "../useAppCatalog";

vi.mock("../client", () => ({ listApps: vi.fn() }));
import { listApps } from "../client";

const mockedListApps = vi.mocked(listApps);

test("moves from loading to success", async () => {
  mockedListApps.mockResolvedValue([{ id: "knowledge-studio", name: "Knowledge Studio" }] as never);
  const { result } = renderHook(() => useAppCatalog());

  expect(result.current.status).toBe("loading");
  await waitFor(() => expect(result.current.status).toBe("success"));
});


test("retry reloads an errored catalog", async () => {
  mockedListApps.mockRejectedValueOnce(new Error("offline"));
  mockedListApps.mockResolvedValueOnce([]);
  const { result } = renderHook(() => useAppCatalog());
  await waitFor(() => expect(result.current.status).toBe("error"));

  await act(async () => result.current.retry());

  await waitFor(() => expect(result.current.status).toBe("empty"));
  expect(mockedListApps).toHaveBeenCalledTimes(2);
});
```

- [ ] **Step 2: Run the tests and confirm feature modules are missing**

Run: `cd frontend && npm run test -- lib/apps/__tests__`

Expected: FAIL because `types.ts`, `client.ts`, and `useAppCatalog.ts` do not exist.

- [ ] **Step 3: Implement the frontend contracts**

```typescript
// frontend/lib/apps/types.ts
export type Capability =
  | "auth" | "retrieval" | "sql" | "workflows" | "artifacts"
  | "evaluation" | "presentations" | "career" | "mcp";

export interface DemoScenario {
  id: string;
  title: string;
  description: string;
  starter_prompt: string;
}

export interface AppDependency {
  app_id: string;
  minimum_version: string;
}

export interface AppManifest {
  id: string;
  version: string;
  name: string;
  summary: string;
  category: string;
  icon: string;
  frontend_route: string;
  backend_route_prefixes: string[];
  backend_router_ids: string[];
  required_capabilities: Capability[];
  optional_capabilities: Capability[];
  required_permissions: string[];
  required_env_keys: string[];
  dependencies: AppDependency[];
  demo_scenarios: DemoScenario[];
  health_check_id: string;
  packaging_paths: string[];
}
```

- [ ] **Step 4: Implement the feature-scoped client**

```typescript
// frontend/lib/apps/client.ts
import type { AppManifest } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Application catalog unavailable (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function listApps(fetcher: typeof fetch = fetch): Promise<AppManifest[]> {
  const response = await fetcher(`${API_BASE}/api/v1/apps`, {
    headers: { Accept: "application/json" },
  });
  return readJson<AppManifest[]>(response);
}

export async function getApp(appId: string, fetcher: typeof fetch = fetch): Promise<AppManifest> {
  const response = await fetcher(`${API_BASE}/api/v1/apps/${encodeURIComponent(appId)}`, {
    headers: { Accept: "application/json" },
  });
  return readJson<AppManifest>(response);
}
```

- [ ] **Step 5: Implement explicit catalog states**

```typescript
// frontend/lib/apps/useAppCatalog.ts
"use client";

import { useCallback, useEffect, useState } from "react";

import { listApps } from "./client";
import type { AppManifest } from "./types";

type CatalogState =
  | { status: "loading"; apps: []; error: null; retry: () => Promise<void> }
  | { status: "empty"; apps: []; error: null; retry: () => Promise<void> }
  | { status: "success"; apps: AppManifest[]; error: null; retry: () => Promise<void> }
  | { status: "error"; apps: []; error: Error; retry: () => Promise<void> };

export function useAppCatalog(): CatalogState {
  const [status, setStatus] = useState<CatalogState["status"]>("loading");
  const [apps, setApps] = useState<AppManifest[]>([]);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    setStatus("loading");
    setError(null);
    try {
      const catalog = await listApps();
      setApps(catalog);
      setStatus(catalog.length === 0 ? "empty" : "success");
    } catch (reason) {
      setApps([]);
      setError(reason instanceof Error ? reason : new Error("Unable to load applications"));
      setStatus("error");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return { status, apps, error, retry: load } as CatalogState;
}
```

- [ ] **Step 6: Run the feature tests**

Run: `cd frontend && npm run test -- lib/apps/__tests__`

Expected: 4 tests PASS.

- [ ] **Step 7: Commit the client**

```bash
git add frontend/lib/apps
git commit -m "feat(frontend): add typed application catalog client"
```

