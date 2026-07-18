import { describe, expect, it, vi } from "vitest";

import {
  CatalogDataError,
  getApp,
  listApps,
} from "../../lib/apps/client";

const validApp = {
  id: "knowledge-studio",
  version: "1.0.0",
  name: "Knowledge Studio",
  summary: "Grounded knowledge work",
  category: "knowledge",
  icon: "book-open",
  frontend_route: "/chat",
  backend_route_prefixes: ["/api/v1/chat"],
  backend_router_ids: ["chat"],
  required_capabilities: ["retrieval"],
  optional_capabilities: [],
  required_permissions: [],
  required_env_keys: [],
  dependencies: [],
  demo_scenarios: [],
  health_check_id: "knowledge",
  packaging_paths: [],
};

describe("application catalog client", () => {
  it("bypasses the ngrok browser warning when loading the catalog", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response("[]", {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await listApps(fetcher as typeof fetch);

    expect(fetcher).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/apps$/),
      expect.objectContaining({
        headers: expect.objectContaining({
          "ngrok-skip-browser-warning": "true",
        }),
      }),
    );
  });

  it("converts a successful HTML response into a stable catalog data error", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response("<!DOCTYPE html><html><body>ngrok warning</body></html>", {
        status: 200,
        headers: { "Content-Type": "text/html; charset=utf-8" },
      }),
    );

    const result = listApps(fetcher as typeof fetch);

    await expect(result).rejects.toEqual(
      expect.objectContaining({
        name: "CatalogDataError",
        message: "Application catalog returned a non-JSON response",
      }),
    );
    await expect(result).rejects.toBeInstanceOf(CatalogDataError);
    await expect(result).rejects.not.toBeInstanceOf(SyntaxError);
  });

  it("converts malformed JSON into a stable catalog data error", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response('{"apps":', {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(listApps(fetcher as typeof fetch)).rejects.toEqual(
      expect.objectContaining({
        name: "CatalogDataError",
        message: "Application catalog returned invalid JSON",
      }),
    );
  });

  it("rejects JSON that does not contain a manifest list", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ apps: [validApp] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(listApps(fetcher as typeof fetch)).rejects.toEqual(
      expect.objectContaining({
        name: "CatalogDataError",
        message: "Application catalog returned an invalid manifest list",
      }),
    );
  });

  it("rejects an invalid single-manifest response", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([validApp]), {
        status: 200,
        headers: { "Content-Type": "application/problem+json" },
      }),
    );

    await expect(
      getApp("knowledge-studio", fetcher as typeof fetch),
    ).rejects.toEqual(
      expect.objectContaining({
        name: "CatalogDataError",
        message: "Application catalog returned an invalid manifest",
      }),
    );
  });
});
