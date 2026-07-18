import { describe, expect, it, vi } from "vitest";

import { listApps } from "../../lib/apps/client";

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
});
