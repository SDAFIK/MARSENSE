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
  await expect(page.getByRole("button", { name: "Analyze terrain", exact: true })).toBeDisabled();
  await page.getByLabel("Estimated location uncertainty (m, optional)").fill("12");
  await page.getByRole("checkbox", { name: /I confirm this is the manually placed footprint/ }).check();
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
  expect(observation.metadata_note).toContain("Observer-estimated location uncertainty: 12 m");
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

test("self-service signup creates a private saved mission and personal login restores it", async ({ page }) => {
  await page.goto("/signup");
  await page.getByLabel("Display name").fill("Personal Explorer");
  await page.getByLabel("Username", { exact: true }).fill("personal-explorer");
  await page.getByLabel("Password", { exact: true }).fill("isolated-personal-explorer-password");
  await page.getByRole("button", { name: "Create my workspace" }).click();
  await expect(page).toHaveURL(/\/mission$/);
  await expect(page.getByRole("tab", { name: "EXPECT", exact: true })).toBeVisible();
  await expect(page.locator("summary").filter({ hasText: "MY WORKSPACE" })).toBeVisible();
  await page.getByRole("tab", { name: "OBSERVE", exact: true }).click();
  await expect(page.getByLabel("Upload ground image")).toBeAttached();
  const source = await page.request.get("/api/assets/ground-navcam.jpg");
  await page.getByLabel("Upload ground image").setInputFiles({
    name: "personal-fixture.jpg", mimeType: "image/jpeg", buffer: await source.body(),
  });
  await page.getByRole("checkbox", { name: /I confirm this is the manually placed footprint/ }).check();
  await page.getByRole("button", { name: "Analyze terrain", exact: true }).click();
  await expect(page.getByRole("tab", { name: "COMPARE", exact: true })).toHaveAttribute("aria-selected", "true");
  await page.getByRole("tab", { name: "VERIFY", exact: true }).click();
  const review = page.getByRole("region", { name: "Evidence review" });
  await review.getByLabel("Human terrain identification").selectOption("obstacle-rich terrain");
  await review.getByRole("button", { name: "Confirm observation" }).click();
  await expect(page.getByRole("heading", { name: "Route Beta", exact: true })).toBeVisible();
  await page.locator("summary").filter({ hasText: "MY WORKSPACE" }).click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/workspace-login$/);
  await page.getByLabel("Username", { exact: true }).fill("personal-explorer");
  await page.getByLabel("Password", { exact: true }).fill("isolated-personal-explorer-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/mission$/);
  await expect(page.getByRole("complementary", { name: "Mission trace and evidence" })).toContainText("Route Beta");
});


test("guest mobile navigation connects astronaut evidence routes and future memory", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  const inspect = async (screen: string) => {
    await page.screenshot({ path: testInfo.outputPath(`guest-${screen}-mobile.png`), fullPage: true });
    const layout = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth - innerWidth,
      viewport: innerWidth,
      offenders: Array.from(document.querySelectorAll("body *")).flatMap((node) => {
        const rect = node.getBoundingClientRect();
        return rect.right > innerWidth + 1 && rect.width > 0
          ? [{ tag: node.tagName, className: node.getAttribute("class"), right: Math.round(rect.right) }]
          : [];
      }).slice(0, 24),
    }));
    expect(layout.overflow, JSON.stringify({ screen, ...layout })).toBeLessThanOrEqual(1);
  };
  await page.goto("/");
  await page.getByRole("button", { name: "Launch Live Demo", exact: true }).click();
  await expect(page.getByRole("tab", { name: "EXPECT", exact: true })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Mission trace and evidence" })).toContainText("Route Alpha");
  await inspect("mission");
  await page.getByRole("link", { name: "Astronaut View", exact: true }).click();
  await expect(page.getByRole("region", { name: "Ground observation view" })).toBeVisible();
  await expect(page.getByLabel("Demonstration observation")).toBeVisible();
  await expect(page.getByLabel("Upload ground image")).toHaveCount(0);
  const analyzed = page.waitForResponse(response =>
    response.url().endsWith("/api/public-demo/observations/demo") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Analyze terrain", exact: true }).click();
  expect((await analyzed).ok()).toBeTruthy();
  await expect(page.locator(".notice")).toContainText("Human review required");
  await inspect("astronaut");

  await page.getByRole("link", { name: "Evidence Inspector", exact: true }).click();
  await expect(page.getByRole("navigation", { name: "Evidence hierarchy" })).toBeVisible();
  await page.getByRole("button", { name: "HUMAN DECISION", exact: true }).click();
  await page.getByRole("region", { name: "Evidence review" }).getByRole("button", { name: "Confirm observation" }).click();
  await expect(page.getByText("Confirmed by Guest reviewer (simulation)", { exact: true })).toBeVisible();
  await inspect("evidence");

  await page.getByRole("link", { name: "Route Comparison", exact: true }).click();
  await expect(page.locator(".route-compare-data")).toContainText("Route Beta");
  await page.getByRole("button", { name: "After", exact: true }).click();
  await expect(page.getByRole("slider", { name: "Before / After map slider" })).toHaveValue("0");
  await inspect("comparison");

  await page.getByRole("link", { name: "Exploration Memory", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Knowledge that Lives On" })).toBeVisible();
  await expect(page.locator(".memory-stats")).toContainText("1 confirmed ground records");
  await page.getByLabel("Active mission").selectOption("eva-02");
  await expect(page.locator(".memory-stats")).toContainText("1 inherited records");
  await inspect("memory");

  await page.getByRole("link", { name: "Mission Control", exact: true }).click();
  await expect(page.getByRole("complementary", { name: "Mission trace and evidence" })).toContainText("Route Beta");
  await page.locator("summary").filter({ hasText: "GUEST DEMO" }).click();
  await page.getByRole("button", { name: "Exit demo", exact: true }).click();
  await expect(page).toHaveURL(/\/$/);
  expect(errors).toEqual([]);
});
