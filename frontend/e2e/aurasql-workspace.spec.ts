import { expect, test, type Page } from "@playwright/test";

async function prepareAuraSql(page: Page) {
  await page.addInitScript(() => localStorage.setItem("auth-storage", JSON.stringify({ state: { isAuthenticated: true, user: { id: 1, email: "data@example.com" }, accessToken: "test", refreshToken: "test" }, version: 0 })));
  await page.route("**/api/v1/apps", (route) => route.fulfill({ status: 200, contentType: "application/json", body: "[]" }));
  await page.route("**/api/v1/aurasql/**", (route) => {
    const pathname = new URL(route.request().url()).pathname;
    const connection = { id: "conn-1", name: "Warehouse", db_type: "postgresql", host: "db.local", port: 5432, username: "analyst", database: "analytics", schema_name: "public", ssl_required: true, created_at: "" };
    const context = { id: "ctx-1", connection_id: "conn-1", name: "Revenue", table_names: ["orders", "customers"], created_at: "" };
    if (pathname.endsWith("/aurasql/connections")) return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ connections: [connection] }) });
    if (pathname.endsWith("/aurasql/contexts")) return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ contexts: [context] }) });
    if (pathname.endsWith("/aurasql/history/sessions")) return route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
    if (pathname.endsWith("/aurasql/connections/conn-1/tables")) return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ tables: ["orders", "customers"] }) });
    return route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });
}

test("AuraSQL keeps the question composer inside a solid fixed workspace", async ({ page }, testInfo) => {
  await prepareAuraSql(page);
  await page.goto("/aurasql/query?context=ctx-1");

  await expect(page.getByRole("heading", { name: "Ask the business. Inspect the truth." })).toBeVisible();
  const composer = page.locator('[data-fixed-composer="aurasql"]');
  const scrollOwner = page.locator('[data-scroll-owner="query-results"]');
  await expect(composer).toBeVisible();
  await expect(scrollOwner).toBeVisible();

  await scrollOwner.evaluate((element) => {
    const spacer = document.createElement("div");
    spacer.style.height = "1200px";
    element.appendChild(spacer);
    element.scrollTop = 500;
  });
  const composerBox = await composer.boundingBox();
  const scrollBox = await scrollOwner.boundingBox();
  expect(composerBox).not.toBeNull();
  expect(scrollBox).not.toBeNull();
  expect(composerBox!.y).toBeGreaterThanOrEqual(scrollBox!.y - 1);
  expect(await composer.evaluate((element) => getComputedStyle(element).backgroundColor)).not.toMatch(/rgba\([^)]*,\s*0(?:\.\d+)?\)/);
  await page.screenshot({ path: `/tmp/aurasql-workspace-${testInfo.project.name}.png`, fullPage: true });
});
