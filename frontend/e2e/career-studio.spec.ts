import { expect, test, type Page } from "@playwright/test";

async function prepareCareer(page: Page) {
  await page.addInitScript(() => localStorage.setItem("auth-storage", JSON.stringify({ state: { isAuthenticated: true, user: { id: 1, email: "career@example.com" }, accessToken: "test", refreshToken: "test" }, version: 0 })));
  await page.route("**/api/v1/apps", (route) => route.fulfill({ status: 200, contentType: "application/json", body: "[]" }));
  await page.route("**/api/v1/nexus/resumes/1", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ list: [], total: 0 }) }));
}

test("Career Studio tells a three-outcome story and preserves explicit choice", async ({ page }, testInfo) => {
  await prepareCareer(page);
  await page.goto("/career");

  await expect(page.getByRole("heading", { name: "Turn experience into your next opportunity" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Score Resume" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Tailor Resume" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Create Resume" })).toBeVisible();

  await page.getByRole("button", { name: "Create Resume" }).click();
  await expect(page).toHaveURL(/\/career\?workflow=create$/);
  await expect(page.getByRole("heading", { name: "Create Resume" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Resume creator steps" })).toBeVisible();

  const surface = page.locator("section.bg-workspace-raised").first();
  await expect(surface).toBeVisible();
  expect(await surface.evaluate((element) => getComputedStyle(element).backgroundColor)).not.toMatch(/rgba\([^)]*,\s*0(?:\.\d+)?\)/);
  await page.screenshot({ path: `/tmp/career-studio-${testInfo.project.name}.png`, fullPage: true });
});
