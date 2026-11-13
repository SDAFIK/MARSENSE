import { expect, test } from "@playwright/test";
import type { Evidence, Snapshot } from "../src/lib/types";

test("production-mode real image upload, role separation, human decision and future EVA", async ({
  page, request,
}, testInfo) => {
  const origin = "http://localhost:3004";
  // Genuine cached NASA pixels are used as a disposable upload fixture.
  // The manual footprint and reviewer interpretation are illustrative, not science validation.
  const source = await request.get("/api/assets/ground-navcam.jpg");
  expect(source.ok()).toBeTruthy();
  const bytes = await source.body();
  expect((await request.get("/api/missions/eva-01")).status()).toBe(401);
  await page.goto("/login");
  await expect(page.getByLabel("Username", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Password", { exact: true })).toBeVisible();
  for (const [name, width, height] of [
    ["desktop", 1440, 1000], ["tablet", 834, 1112], ["mobile", 390, 844],
  ] as const) {
    await page.setViewportSize({ width, height });
    await expect(page.getByRole("button", { name: "Sign in", exact: true })).toBeVisible();
    await expect.poll(() => page.locator(".product-login img").evaluateAll(
      (images) => images.length > 0 && images.every((image) => (image as HTMLImageElement).complete && (image as HTMLImageElement).naturalWidth > 0),
    )).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
    await page.screenshot({ path: testInfo.outputPath(`login-${name}.png`), fullPage: true });
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByLabel("Username", { exact: true }).fill("astronaut");
  await page.getByLabel("Password", { exact: true }).fill("isolated-astronaut-test-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/mission$/);
  await expect(page.getByRole("tab", { name: "EXPECT", exact: true })).toBeVisible();
  const before = await (await page.request.get("/api/missions/eva-01")).json() as Snapshot;
  await page.getByRole("tab", { name: "OBSERVE", exact: true }).click();
  await expect(page.getByLabel("Upload ground image")).toBeAttached();
  await expect(page.getByLabel("Demonstration observation")).toHaveCount(0);
  await page.getByLabel("Upload ground image").setInputFiles({
    name: "cached-navcam-test.jpg", mimeType: "image/jpeg", buffer: bytes,
  });
  await expect(page.getByText("Manually locate the supported footprint", { exact: false })).toBeVisible();
  await expect(page.getByAltText("Selected ground image before submission")).toBeVisible();
  await page.getByLabel("Observation details (optional)").fill("Disposable fixture; manually placed footprint.");
  const upload = page.waitForResponse((response) => response.url().endsWith("/api/observations/upload") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Analyze terrain", exact: true }).click();
  const response = await upload;
  expect(response.ok()).toBeTruthy();
  const evidence = await response.json() as Evidence;
  expect(evidence.source_type).toBe("ground");
  expect(evidence.verification_state).toBe("PROVISIONAL");
  expect(evidence.model_output?.engine).toBe("opencv-texture-candidate");
  expect(evidence.model_confidence).toBeNull();
  expect(evidence.model_output?.confidence_label).toBe("not estimated");
  await expect(page.getByRole("tab", { name: "COMPARE", exact: true })).toHaveAttribute("aria-selected", "true");
  const provisional = await (await page.request.get("/api/missions/eva-01")).json() as Snapshot;
  expect(provisional.routes).toHaveLength(1);
  expect(provisional.routes[0].coordinates).toEqual(before.routes[0].coordinates);
  expect(provisional.evidence.filter((item) => item.source_type === "orbital")).toEqual(before.evidence.filter((item) => item.source_type === "orbital"));
  const denied = await page.request.post(`/api/evidence/${evidence.id}/verify`, {
    headers: { Origin: origin },
    data: { decision: "CONFIRMED", reviewer: "Untrusted", note: "Role denial test", human_terrain: "obstacle-rich terrain" },
  });
  expect(denied.status()).toBe(403);
  await page.locator("summary").filter({ hasText: "Test Astronaut" }).click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Sign in to the living map" })).toBeVisible();
  await page.goto("/login");
  await page.getByLabel("Username", { exact: true }).fill("reviewer");
  await page.getByLabel("Password", { exact: true }).fill("isolated-reviewer-test-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/mission$/);
  await page.getByRole("tab", { name: "VERIFY", exact: true }).click();
  const review = page.getByRole("region", { name: "Evidence review" });
  await expect(review.getByRole("button", { name: "Confirm observation" })).toBeDisabled();
  await review.getByLabel("Human terrain identification").selectOption("obstacle-rich terrain");
  await review.getByLabel("Your verification note").fill("Illustrative fixture reviewed by an authorized human; manually placed footprint.");
  await review.getByRole("button", { name: "Confirm observation" }).click();
  await expect(page.getByRole("heading", { name: "Route Beta", exact: true })).toBeVisible();
  const current = await (await page.request.get("/api/missions/eva-01")).json() as Snapshot;
  const verified = current.evidence.find((item) => item.id === evidence.id);
  expect(verified?.verified_by).toBe("Test Reviewer");
  expect(verified?.verification_state).toBe("CONFIRMED");
  expect(current.routes.find((route) => route.id === current.mission.active_route_id)?.name).toBe("Route Beta");
  expect(current.evidence.filter((item) => item.source_type === "orbital")).toEqual(before.evidence.filter((item) => item.source_type === "orbital"));
  const observation = await (await page.request.get(`/api/observations/${evidence.observation_id}`)).json();
  expect(observation.metadata_note).toContain("Disposable fixture");
  const original = await page.request.get(observation.original_asset_reference);
  expect(original.ok()).toBeTruthy();
  expect(await original.body()).toEqual(bytes);
  expect((await request.get(evidence.raw_asset_reference)).status()).toBe(401);
  await page.screenshot({ path: testInfo.outputPath("production-confirmed.png"), fullPage: true });
  await page.reload();
  await expect(page.getByRole("complementary", { name: "Mission trace and evidence" })).toContainText("Route Beta");
  await page.getByLabel("Active mission").selectOption("eva-02");
  await expect(page.getByText("INHERITED FROM EVA-01", { exact: false })).toBeVisible();
  const future = await (await page.request.get("/api/missions/eva-02")).json() as Snapshot;
  expect(future.mission.inherited_evidence).toContain(evidence.id);
});

test("guest launch needs no account and isolates the complete simulated mission", async ({ page, browser }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Launch Live Demo" }).click();
  await expect(page).toHaveURL(/\/mission$/);
  await expect(page.getByRole("tab", { name: "EXPECT", exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "OBSERVE", exact: true }).click();
  await expect(page.getByLabel("Demonstration observation")).toBeVisible();
  await page.getByRole("button", { name: "Analyze terrain", exact: true }).click();
  await expect(page.getByRole("tab", { name: "COMPARE", exact: true })).toHaveAttribute("aria-selected", "true");
  await page.getByRole("tab", { name: "VERIFY", exact: true }).click();
  await page.getByRole("region", { name: "Evidence review" }).getByRole("button", { name: "Confirm observation" }).click();
  await expect(page.getByRole("heading", { name: "Route Beta", exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("complementary", { name: "Mission trace and evidence" })).toContainText("Route Beta");
  await page.getByLabel("Active mission").selectOption("eva-02");
  await expect(page.getByText("INHERITED FROM EVA-01", { exact: false })).toBeVisible();
  const other = await browser.newContext({ baseURL: "http://localhost:3004" });
  try {
    const visitor = await other.newPage();
    await visitor.goto("/");
    await visitor.getByRole("button", { name: "Launch Live Demo" }).click();
    await expect(visitor.getByRole("complementary", { name: "Mission trace and evidence" })).toContainText("Route Alpha");
    await expect(visitor.getByRole("complementary", { name: "Mission trace and evidence" })).not.toContainText("Route Beta");
  } finally { await other.close(); }
  await page.locator("summary").filter({ hasText: "GUEST DEMO" }).click();
  page.once("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "Reset my demo" }).click();
  await expect(page.getByRole("complementary", { name: "Mission trace and evidence" })).toContainText("Route Alpha");
  await expect(page.getByRole("complementary", { name: "Mission trace and evidence" })).not.toContainText("Route Beta");
  await page.locator("summary").filter({ hasText: "GUEST DEMO" }).click();
  await page.getByRole("button", { name: "Exit demo" }).click();
  await expect(page).toHaveURL(/\/$/);
});
