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
    page.getByRole("tab", { name: "EXPECT", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(
    page.getByRole("complementary", { name: "Mission trace and evidence" }),
  ).toContainText("Route Alpha");
  await expect(
    page.getByRole("region", { name: "Interactive Jezero map" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "OBSERVE", exact: true }).click();
  await page.getByRole("button", { name: "Analyze terrain" }).click();
  await expect(
    page.getByRole("tab", { name: "COMPARE", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("tabpanel")).toContainText(
    "Significant Difference",
  );
  await expect(page.getByRole("tabpanel")).toContainText(
    "Obstacle-Rich Terrain",
  );
  await page.getByRole("tab", { name: "VERIFY", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Evidence review" }),
  ).toContainText("PROVISIONAL SAFETY ALERT");
  await page.getByRole("button", { name: "Confirm observation" }).click();
  await expect(
    page.getByRole("tab", { name: "LEARN", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(
    page.getByRole("heading", { name: "Route Beta", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("complementary", { name: "Mission trace and evidence" }),
  ).toContainText("Route Beta");
  await page.getByRole("tab", { name: "VERIFY", exact: true }).click();
  await expect(
    page.getByText("Confirmed by A. Rahman", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Active mission").selectOption("eva-02");
  await expect(
    page.getByText("INHERITED FROM EVA-01", { exact: false }),
  ).toBeVisible();
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
    }, testInfo) => {
      const errors: string[] = [];
      page.on("pageerror", (error) => errors.push(error.message));
      await page.setViewportSize({ width, height });
      await page.emulateMedia({ reducedMotion: "reduce" });
      await page.goto(`/${view}`);
      if (view === "mission") {
        await expect(
          page.getByRole("tablist", { name: "Mission workflow" }),
        ).toBeVisible();
      } else
        await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      if (view) await expect(page.getByLabel("Active mission")).toBeVisible();
      // A shell heading can appear before the mission API finishes loading.
      // Capture the actual data-backed view, not an empty loading state.
      if (view === "evidence")
        await expect(page.getByRole("navigation", { name: "Evidence hierarchy" })).toBeVisible();
      if (view === "memory")
        await expect(page.getByRole("heading", { name: "Knowledge that Lives On" })).toBeVisible();
      if (["mission", "astronaut", "comparison", "memory"].includes(view)) {
        await expect(page.locator(".map-canvas canvas").first()).toBeVisible();
        await expect.poll(() => page.locator(".map-panel").evaluateAll(
          (maps) => maps.length > 0 && maps.every((map) => map.getAttribute("data-renderer") === "webgl"),
        )).toBe(true);
      }
      // Trigger natural lazy-loading for images below the first viewport.
      for (const image of await page.locator("img").all()) {
        if (await image.isVisible()) await image.scrollIntoViewIfNeeded();
      }
      await page.evaluate(() => window.scrollTo(0, 0));
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
        path: testInfo.outputPath(`${view || "landing"}-${size}.png`),
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
  await expect(
    page.getByRole("heading", { name: "Mission state unavailable" }),
  ).toBeVisible();
  await expect(
    page.getByText("Your evidence is preserved", { exact: true }),
  ).toHaveCount(0);
  await page.unroute("**/api/missions/**");
  await page.getByRole("button", { name: "Retry connection" }).click();
  await expect(
    page.getByRole("complementary", { name: "Mission trace and evidence" }),
  ).toContainText("Route Beta");
});
test("keyboard navigation reaches mission controls", async ({ page }) => {
  await page.goto("/mission");
  await expect(
    page.getByRole("complementary", { name: "Mission trace and evidence" }),
  ).toContainText("Route Beta");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to main content" }),
  ).toBeFocused();
  await page.getByLabel("Active mission").focus();
  await page.keyboard.press("ArrowDown");
  await expect(page.getByLabel("Active mission")).toBeFocused();
});
