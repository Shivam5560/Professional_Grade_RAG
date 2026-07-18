import { expect, test } from "@playwright/test";

test("flagship presents the product without a separate showcase", async ({ page }, testInfo) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(
    page.getByRole("heading", { name: /intelligence, made tangible/i }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: /explore showcase/i })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "AuraSQL" })).toBeVisible();
  const screenshot = await page.screenshot({
    path: `/tmp/nexusmind-flagship-${testInfo.project.name}.png`,
    fullPage: true,
  });
  expect(screenshot.byteLength).toBeGreaterThan(25_000);
});

test("appearance persists across public routes", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.getByRole("combobox", { name: /appearance/i }).selectOption("light");
  await page.getByRole("link", { name: /read the engineering story/i }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme-mode", "light");
});

test("authentication opens inside the flagship", async ({ page }, testInfo) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.getByRole("link", { name: /log in/i }).click();
  await expect(page).toHaveURL(/\?auth=login/);
  await expect(page.getByRole("dialog", { name: /enter nexusmind/i })).toBeVisible();
  await expect(
    page.getByRole("button", { name: /enter nexusmind/i }),
  ).toBeVisible();
  const screenshot = await page.screenshot({
    path: `/tmp/nexusmind-auth-${testInfo.project.name}.png`,
  });
  expect(screenshot.byteLength).toBeGreaterThan(20_000);
});

test("reduced motion omits the ambient WebGL scene", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/", { waitUntil: "domcontentloaded" });

  await expect(
    page.getByRole("heading", { name: /intelligence, made tangible/i }),
  ).toBeVisible();
  await expect(page.locator("canvas")).toHaveCount(0);
});

test("legacy public routes redirect to the flagship", async ({ page }) => {
  await page.goto("/auth", { waitUntil: "domcontentloaded" });
  await expect(page).toHaveURL(/\?auth=login/);
  await expect(page.getByRole("dialog", { name: /enter nexusmind/i })).toBeVisible();
  await page.goto("/showcase", { waitUntil: "domcontentloaded" });
  await expect(page).toHaveURL(/\/$/);
});

test("public experiences make no live API requests", async ({ page }) => {
  const apiRequests: string[] = [];
  page.on("request", (request) => {
    const pathname = new URL(request.url()).pathname;
    if (pathname.startsWith("/api/")) apiRequests.push(request.url());
  });

  for (const route of [
    "/",
    "/developer",
    "/auth",
  ]) {
    await page.goto(route, { waitUntil: "domcontentloaded" });
    await expect(page.locator("body")).toBeVisible();
  }

  expect(apiRequests).toEqual([]);
});
