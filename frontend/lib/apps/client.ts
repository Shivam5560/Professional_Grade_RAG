import type { AppManifest } from "./types";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

const JSON_HEADERS = {
  Accept: "application/json",
  "ngrok-skip-browser-warning": "true",
};

const SAFE_FRONTEND_ROUTE = /^\/(?!\/)[a-z0-9/_\-\[\]]*$/;

export class CatalogHttpError extends Error {
  constructor(readonly status: number) {
    super(`Application catalog unavailable (${status})`);
    this.name = "CatalogHttpError";
  }
}

export class CatalogDataError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CatalogDataError";
  }
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new CatalogHttpError(response.status);
  }

  return response.json() as Promise<T>;
}

function validateFrontendRoute(app: AppManifest): AppManifest {
  const route = app?.frontend_route;

  if (typeof route !== "string" || !SAFE_FRONTEND_ROUTE.test(route)) {
    const appId = app?.id ?? "unknown";
    throw new CatalogDataError(
      `Application catalog contains an unsafe frontend route for "${appId}"`,
    );
  }

  return app;
}

export async function listApps(
  fetcher: typeof fetch = fetch,
): Promise<AppManifest[]> {
  const response = await fetcher(`${API_BASE}/api/v1/apps`, {
    headers: JSON_HEADERS,
  });

  const apps = await readJson<AppManifest[]>(response);
  return apps.map(validateFrontendRoute);
}

export async function getApp(
  appId: string,
  fetcher: typeof fetch = fetch,
): Promise<AppManifest> {
  const response = await fetcher(
    `${API_BASE}/api/v1/apps/${encodeURIComponent(appId)}`,
    { headers: JSON_HEADERS },
  );

  const app = await readJson<AppManifest>(response);
  return validateFrontendRoute(app);
}
