import { expect, test } from "@playwright/test";
import type { Snapshot } from "../src/lib/types";
test.describe.configure({ mode: "serial" });
test("primary acceptance: prior → observation → verify → Beta → reload → future EVA", async ({
  page,
  request,
}) => {
  await page.route(/https?:\/\//, (route) =>
    route.request().url().startsWith("http://127.0.0.1") ||
    route.request().url().startsWith("http://localhost")
      ? route.continue()
      : route.abort(),
  );
  await page.goto("/mission");
  await expect(
    page.getByRole("heading", { name: "Mission Control" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Route Alpha" }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Interactive Jezero map" }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/mission-before-desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Analyze terrain" }).click();
  await expect(
    page
      .getByRole("region", { name: "Evidence review" })
      .getByText("PROVISIONAL SAFETY ALERT", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Significant Difference", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Obstacle-Rich Terrain", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Confirm observation" }).click();
  await expect(
    page.getByRole("heading", { name: "Route Beta", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Ground Observed", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Confirmed by A. Rahman", { exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Route Beta", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Confirmed by A. Rahman", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Active mission").selectOption("eva-02");
  await expect(
    page.getByText("You’re starting where the last explorer left off."),
  ).toBeVisible();
  await expect(page.getByText(/1 inherited by this EVA/)).toBeVisible();
  const state = (await (
    await request.get("/api/missions/eva-02")
  ).json()) as Snapshot;
  expect(state.mission.inherited_evidence).toHaveLength(1);
  const beta = state.routes.find(
    (r) => r.id === state.mission.active_route_id,
  )!;
  expect(beta.distance_m).toBeGreaterThan(960);
  expect(beta.explanation).toContain("A. Rahman");
});
for (const [size, width, height] of [
  ["desktop", 1440, 1000],
  ["tablet", 834, 1112],
  ["mobile", 390, 844],
] as const) {
  for (const view of [
    "",
    "mission",
    "astronaut",
    "evidence",
    "memory",
    "comparison",
  ]) {
    test(`${view || "landing"} at ${size}: visible content, no overflow`, async ({
      page,
    }) => {
      const errors: string[] = [];
      page.on("pageerror", (error) => errors.push(error.message));
      await page.setViewportSize({ width, height });
      await page.goto(`/${view}`);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      if (view)
        await expect(
          page.getByText("1 verified observation", { exact: true }),
        ).toBeVisible();
      if (["mission", "astronaut", "comparison"].includes(view))
        await expect(page.locator(".map-canvas canvas").first()).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
      expect(errors).toEqual([]);
      await expect
        .poll(() =>
          page
            .locator("img")
            .evaluateAll((images) =>
              images.every(
                (img) =>
                  (img as HTMLImageElement).complete &&
                  (img as HTMLImageElement).naturalWidth > 0,
              ),
            ),
        )
        .toBe(true);
      await page.screenshot({
        path: `../docs/screenshots/${view || "landing"}-${size}.png`,
        fullPage: true,
      });
    });
  }
}
test("service failure explains what remains usable and retry recovers", async ({
  page,
}) => {
  await page.route("**/api/missions/**", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        detail:
          "Connection interrupted. Saved evidence remains available after reconnecting.",
      }),
    }),
  );
  await page.goto("/mission");
  await expect(
    page.getByRole("alert").filter({ hasText: "Mission service" }),
  ).toContainText("Saved evidence");
  await page.unroute("**/api/missions/**");
  await page.getByRole("button", { name: "Retry connection" }).click();
  await expect(
    page.getByRole("heading", { name: "Route Beta", exact: true }),
  ).toBeVisible();
});
test("keyboard navigation reaches mission controls", async ({ page }) => {
  await page.goto("/mission");
  await expect(
    page.getByRole("heading", { name: "Route Beta", exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to main content" }),
  ).toBeFocused();
  await page.getByLabel("Active mission").focus();
  await page.keyboard.press("ArrowDown");
  await expect(page.getByLabel("Active mission")).toBeFocused();
});
