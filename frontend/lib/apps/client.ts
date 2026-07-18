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

function isJsonResponse(response: Response): boolean {
  const mediaType = response.headers
    .get("content-type")
    ?.split(";", 1)[0]
    .trim()
    .toLowerCase();

  if (!mediaType) return false;

  return (
    mediaType === "application/json" ||
    (mediaType.startsWith("application/") && mediaType.endsWith("+json"))
  );
}

async function readCatalogJson(response: Response): Promise<unknown> {
  if (!response.ok) {
    throw new CatalogHttpError(response.status);
  }

  if (!isJsonResponse(response)) {
    throw new CatalogDataError(
      "Application catalog returned a non-JSON response",
    );
  }

  try {
    return (await response.json()) as unknown;
  } catch {
    throw new CatalogDataError("Application catalog returned invalid JSON");
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isAppManifest(value: unknown): value is AppManifest {
  if (!isRecord(value)) return false;

  const stringFields = [
    "id",
    "version",
    "name",
    "summary",
    "category",
    "icon",
    "frontend_route",
    "health_check_id",
  ] as const;
  if (stringFields.some((field) => typeof value[field] !== "string")) {
    return false;
  }

  const stringArrayFields = [
    "backend_route_prefixes",
    "backend_router_ids",
    "required_capabilities",
    "optional_capabilities",
    "required_permissions",
    "required_env_keys",
    "packaging_paths",
  ] as const;
  if (stringArrayFields.some((field) => !isStringArray(value[field]))) {
    return false;
  }

  if (
    !Array.isArray(value.dependencies) ||
    !value.dependencies.every(
      (dependency) =>
        isRecord(dependency) &&
        typeof dependency.app_id === "string" &&
        typeof dependency.minimum_version === "string",
    )
  ) {
    return false;
  }

  return (
    Array.isArray(value.demo_scenarios) &&
    value.demo_scenarios.every(
      (scenario) =>
        isRecord(scenario) &&
        typeof scenario.id === "string" &&
        typeof scenario.title === "string" &&
        typeof scenario.description === "string" &&
        typeof scenario.starter_prompt === "string",
    )
  );
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

  const payload = await readCatalogJson(response);
  if (!Array.isArray(payload) || !payload.every(isAppManifest)) {
    throw new CatalogDataError(
      "Application catalog returned an invalid manifest list",
    );
  }

  const apps = payload;
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

  const payload = await readCatalogJson(response);
  if (!isAppManifest(payload)) {
    throw new CatalogDataError(
      "Application catalog returned an invalid manifest",
    );
  }

  const app = payload;
  return validateFrontendRoute(app);
}
