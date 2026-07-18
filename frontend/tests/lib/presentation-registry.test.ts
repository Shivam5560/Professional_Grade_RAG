import { describe, expect, it } from "vitest";

import type { AppManifest } from "@/lib/apps/types";
import {
  directApplicationRoute,
  presentationForApp,
  presentationForPath,
} from "@/lib/presentation/registry";

const app = (id: string, frontend_route: string): AppManifest => ({
  id,
  frontend_route,
  name: id,
  version: "1.0.0",
  summary: "Summary",
  category: "test",
  icon: "blocks",
  backend_route_prefixes: [],
  backend_router_ids: [],
  required_capabilities: [],
  optional_capabilities: [],
  required_permissions: [],
  required_env_keys: [],
  dependencies: [],
  demo_scenarios: [],
  health_check_id: id,
  packaging_paths: [],
});

describe("application presentation registry", () => {
  it("maps enabled manifests to authored application identities", () => {
    expect(presentationForApp(app("aurasql", "/aurasql"))).toMatchObject({
      id: "aurasql",
      accent: "data",
      mainRoute: "/aurasql",
      localDestinations: expect.arrayContaining([
        expect.objectContaining({ label: "History", href: "/aurasql/history" }),
      ]),
    });
  });

  it("uses the longest matching application route", () => {
    expect(presentationForPath("/analysis/42/report").id).toBe("analysis");
  });

  it("launches catalog entries directly into their frontend route", () => {
    expect(directApplicationRoute(app("knowledge-studio", "/chat"))).toBe(
      "/chat",
    );
  });
});
