import { expect, test, type Locator, type Page } from "@playwright/test";

const auraSqlManifest = {
  id: "aurasql",
  version: "1.0.0",
  name: "AuraSQL",
  summary: "Query connected data",
  category: "data",
  icon: "database",
  frontend_route: "/aurasql",
  backend_route_prefixes: [],
  backend_router_ids: [],
  required_capabilities: [],
  optional_capabilities: [],
  required_permissions: [],
  required_env_keys: [],
  dependencies: [],
  demo_scenarios: [],
  health_check_id: "aurasql",
  packaging_paths: [],
};

async function prepareAuthenticatedDashboard(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem(
      "auth-storage",
      JSON.stringify({
        state: {
          isAuthenticated: true,
          user: { id: 1, email: "demo@nexusmind.local" },
          accessToken: "test",
          refreshToken: "test",
        },
        version: 0,
      }),
    );
  });
  await page.route("**/api/v1/apps", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([auraSqlManifest]),
    }),
  );
}

async function runningTransformAnimations(root: Locator) {
  return root.evaluate((element) =>
    element
      .getAnimations({ subtree: true })
      .filter(
        (animation) =>
          animation.playState === "running" &&
          animation.effect instanceof KeyframeEffect &&
          animation.effect
            .getKeyframes()
            .some(
              (frame) =>
                typeof frame.transform === "string" &&
                frame.transform !== "none",
            ),
      ).length,
  );
}

test("authenticated dashboard and shell remain uncluttered", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await prepareAuthenticatedDashboard(page);
  await page.goto("/apps");

  await expect(
    page.getByRole("region", { name: "Featured application" }),
  ).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Applications" }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Open AuraSQL" })).toHaveAttribute(
    "href",
    "/aurasql",
  );
  await expect(page.locator("main")).toHaveCount(1);
  const screenshot = await page.screenshot({
    path: `/tmp/nexusmind-dashboard-${testInfo.project.name}.png`,
    fullPage: true,
  });
  expect(screenshot.byteLength).toBeGreaterThan(20_000);
});

test("reduced motion disables cinematic transform animation", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await prepareAuthenticatedDashboard(page);
  await page.goto("/apps");

  const featured = page.getByRole("region", { name: "Featured application" });
  await expect(featured).toBeVisible();
  await expect.poll(() => runningTransformAnimations(featured)).toBe(0);
});

test("data saver disables cinematic transform animation", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "connection", {
      configurable: true,
      value: { saveData: true },
    });
  });
  await prepareAuthenticatedDashboard(page);
  await page.goto("/apps");

  const featured = page.getByRole("region", { name: "Featured application" });
  await expect(featured).toBeVisible();
  await expect.poll(() => runningTransformAnimations(featured)).toBe(0);
});

test("mobile uses the safe-area bottom bar instead of the desktop rail", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ width: 412, height: 915 });
  await prepareAuthenticatedDashboard(page);
  await page.goto("/apps");

  await expect(
    page.getByRole("navigation", { name: "Mobile applications" }),
  ).toBeVisible();
  await expect(page.locator('nav[aria-label="Applications"]')).toBeHidden();
  await expect(
    page.getByRole("region", { name: "Featured application" }),
  ).toBeVisible();
  const screenshot = await page.screenshot({
    path: `/tmp/nexusmind-mobile-shell-${testInfo.project.name}.png`,
    fullPage: true,
  });
  expect(screenshot.byteLength).toBeGreaterThan(15_000);
});
