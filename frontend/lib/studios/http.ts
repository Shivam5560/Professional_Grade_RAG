import { useAuthStore } from "@/lib/store";

export interface StudioClientOptions {
  baseUrl?: string;
  fetcher?: typeof fetch;
  getAccessToken?: () => string | null;
}

export class StudioHttpError extends Error {
  constructor(readonly status: number, message: string, readonly detail?: unknown) {
    super(message);
    this.name = "StudioHttpError";
  }
}

export class StudioHttpClient {
  protected readonly baseUrl: string;
  protected readonly fetcher: typeof fetch;
  private readonly getAccessToken: () => string | null;

  constructor(path: string, options: StudioClientOptions = {}) {
    const apiBase = (options.baseUrl ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/+$/, "");
    this.baseUrl = `${apiBase}${path}`;
    this.fetcher = options.fetcher ?? fetch;
    this.getAccessToken = options.getAccessToken ?? (() => useAuthStore.getState().accessToken);
  }

  protected async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const token = this.getAccessToken();
    const response = await this.fetcher(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        "ngrok-skip-browser-warning": "true",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init.headers,
      },
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => null);
      const message = detail && typeof detail === "object" && "detail" in detail
        ? String((detail as { detail: unknown }).detail)
        : `Studio request failed (${response.status})`;
      throw new StudioHttpError(response.status, message, detail);
    }
    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }
}
