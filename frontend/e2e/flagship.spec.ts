import { expect, test } from "@playwright/test";

test("flagship leads to a deterministic showcase", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(
    page.getByRole("heading", { name: /intelligence, made tangible/i }),
  ).toBeVisible();
  const showcaseLink = page
    .getByRole("link", { name: /explore showcase/i })
    .first();
  await expect(showcaseLink).toHaveAttribute("href", "/showcase");
  await showcaseLink.click();
  await expect(page).toHaveURL(/\/showcase$/);
  await expect(page.getByRole("status")).toContainText(
    /precomputed demonstration/i,
  );
  const auraSqlLink = page.getByRole("link", {
    name: /move from intent/i,
  });
  await expect(auraSqlLink).toHaveAttribute("href", "/showcase/aurasql");
  await auraSqlLink.click();
  await expect(page).toHaveURL(/showcase\/aurasql/);
  await page
    .getByRole("button", { name: /continue demonstration/i })
    .click();
  await expect(
    page.getByRole("heading", { name: "Review", exact: true }),
  ).toBeVisible();
});

test("appearance persists across public routes", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /appearance/i }).click();
  await page.getByRole("menuitemradio", { name: /light/i }).click();
  await page.getByRole("link", { name: /read the engineering story/i }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme-mode", "light");
});

test("live CTA reaches focused authentication", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const liveWorkspaceLink = page
    .getByRole("link", { name: /launch live workspace/i })
    .first();
  await expect(liveWorkspaceLink).toHaveAttribute("href", "/auth");
  await liveWorkspaceLink.click();
  await expect(page).toHaveURL(/\/auth$/);
  await expect(
    page.getByRole("button", { name: /enter nexusmind/i }),
  ).toBeVisible();
});

test("public experiences make no live API requests", async ({ page }) => {
  const apiRequests: string[] = [];
  page.on("request", (request) => {
    const pathname = new URL(request.url()).pathname;
    if (pathname.startsWith("/api/")) apiRequests.push(request.url());
  });

  for (const route of [
    "/",
    "/showcase",
    "/showcase/knowledge",
    "/developer",
    "/auth",
  ]) {
    await page.goto(route, { waitUntil: "domcontentloaded" });
    await expect(page.locator("main")).toBeVisible();
  }

  expect(apiRequests).toEqual([]);
});
