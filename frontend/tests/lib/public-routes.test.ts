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
