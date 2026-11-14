import { chromium } from "playwright";
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
const origin = "https://redscape-eight.vercel.app";
const output = "test-results/public-website";
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ args: ["--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce" });
page.setDefaultTimeout(45000);
const errors = [];
page.on("pageerror", error => errors.push(error.message));
const visible = locator => locator.waitFor({ state: "visible" });
const text = (locator, value) => visible(locator.filter({ hasText: value }));
const button = name => page.getByRole("button", { name, exact: true });
const link = name => page.getByRole("link", { name, exact: true });
const screenshot = async name => {
  for (const image of await page.locator("img").all()) {
    if (await image.isVisible()) await image.scrollIntoViewIfNeeded();
  }
  await page.waitForFunction(() => Array.from(document.images).filter(img => img.getClientRects().length > 0).every(img => img.complete && img.naturalWidth > 0));
  if (await page.locator(".map-panel").count()) {
    await page.waitForFunction(() => Array.from(document.querySelectorAll(".map-panel")).every(map => map.getAttribute("data-renderer") === "webgl"));
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), name + ": horizontal overflow");
  await page.screenshot({ path: output + "/" + name + ".png", fullPage: true, animations: "disabled" });
};
try {
  let ready = false;
  for (let i = 0; i < 5; i++) {
    try {
      const response = await page.goto(origin, { timeout: 30000 });
      if (response?.ok() && await page.locator(".mars-experience").isVisible() && await button("Launch Live Demo").isVisible()) { ready = true; break; }
    } catch { /* transient deployment propagation */ }
    await page.waitForTimeout(5000);
  }
  assert(ready, "Public landing page is unavailable");
  await visible(page.getByRole("heading", { name: /Every step makes Mars more known/ }));
  await visible(page.getByText("Planetary context ready", { exact: true }));
  await visible(page.locator(".product-steps").getByText("INHERIT", { exact: true }));
  await screenshot("landing-desktop");
  await page.setViewportSize({ width: 390, height: 844 });
  await screenshot("landing-mobile");
  await page.setViewportSize({ width: 1440, height: 1000 });
  let healthy = false;
  for (let i = 0; i < 3; i++) {
    try {
      const response = await page.request.get(origin + "/api/health", { timeout: 70000 });
      if (response.ok() && (await response.json()).status === "ok") { healthy = true; break; }
    } catch { /* Render free service may cold-start */ }
    await page.waitForTimeout(3000);
  }
  assert(healthy, "Same-origin production API health failed");
  for (const path of ["ground-navcam.jpg", "jezero-hirise.png", "jezero-ctx.png"]) {
    const response = await page.request.get(origin + "/api/assets/" + path);
    assert(response.ok(), "NASA image HTTP " + response.status() + ": " + path);
    assert((response.headers()["content-type"] || "").startsWith("image/"), "Expected NASA image: " + path);
  }
  await button("Launch Live Demo").click();
  await visible(page.getByRole("tab", { name: "EXPECT", exact: true }));
  await visible(page.locator(".mission-command-v3"));
  await visible(page.getByRole("region", { name: "Mission overview" }));
  await text(page.getByRole("complementary", { name: "Mission trace and evidence" }), "Route Alpha");
  await visible(page.getByText("MARSENSE / v2.0", { exact: true }));
  await screenshot("mission-desktop");

  // The following writes affect only this ephemeral signed-out guest mission.
  await link("Astronaut View").click();
  const ground = page.getByRole("region", { name: "Ground observation view" });
  const controls = page.getByRole("complementary", { name: "Observation and decision controls" });
  await visible(ground);
  await visible(page.locator(".field-experience-v3"));
  await visible(controls.getByRole("button", { name: "Observe", exact: true }));
  await screenshot("astronaut-desktop");
  await page.setViewportSize({ width: 390, height: 844 });
  await visible(page.locator(".nav-mobile-label").filter({ hasText: "Field" }));
  await ground.getByRole("button", { name: "Route context", exact: true }).click();
  await visible(controls.locator('button[aria-pressed="true"]').filter({ hasText: "Route" }));
  await ground.getByRole("button", { name: "Record observation", exact: true }).click();
  await visible(page.getByLabel("Demonstration observation"));
  const analyzed = page.waitForResponse(response => response.url().endsWith("/api/public-demo/observations/demo") && response.request().method() === "POST", { timeout: 90000 });
  await button("Analyze terrain").click();
  assert((await analyzed).ok(), "Guest observation failed");
  await text(page.locator(".notice"), "Human review required");
  await screenshot("astronaut-mobile");

  await link("Evidence Inspector").click();
  await visible(page.getByRole("navigation", { name: "Evidence hierarchy" }));
  await visible(page.locator(".evidence-studio-v3"));
  await page.locator(".studio-original summary").click();
  await visible(page.locator(".studio-original img"));
  await page.locator(".studio-original summary").click();
  await button("Open human review").click();
  await page.getByRole("region", { name: "Evidence review" }).getByRole("button", { name: "Confirm observation", exact: true }).click();
  await visible(page.getByText("Confirmed by Guest reviewer (simulation)", { exact: true }));
  await screenshot("evidence-mobile");

  await link("Route Comparison").click();
  await visible(page.locator(".route-studio-v3"));
  const route = page.getByRole("region", { name: "Route comparison summary" });
  await text(route, "Route Alpha");
  await text(route, "Route Beta");
  await text(route, "DISTANCE CHANGE");
  await button("After").click();
  assert.equal(await page.getByRole("slider", { name: "Before / After map slider" }).inputValue(), "0");
  await screenshot("comparison-mobile");

  await link("Exploration Memory").click();
  await visible(page.locator(".memory-archive-v3"));
  await text(page.locator(".memory-stats"), "1 confirmed ground records");
  await page.getByLabel("Active mission").selectOption("eva-02");
  await text(page.locator(".memory-stats"), "1 inherited records");
  await screenshot("memory-mobile");

  await link("Intelligence Center").click();
  await visible(page.locator(".intel-observatory-v3"));
  await visible(page.getByRole("region", { name: "Current mission briefing" }));
  await visible(page.getByRole("img", { name: "Mars globe rendered from NASA Viking imagery" }));
  await visible(page.getByText("Planetary context ready", { exact: true }));
  await button("Rotate Mars left").click();
  await button("Play Mars rotation").click();
  await visible(button("Pause Mars rotation"));
  await button("Pause Mars rotation").click();
  await screenshot("intelligence-mobile");

  await link("Mission Control").click();
  await text(page.getByRole("complementary", { name: "Mission trace and evidence" }), "Route Beta");
  await screenshot("mission-mobile");
  await page.locator("summary").filter({ hasText: "GUEST DEMO" }).click();
  await button("Exit demo").click();
  await page.waitForURL(origin + "/");
  assert.deepEqual(errors, [], "Browser errors");
  console.log("Public MARSENSE cinematic rebuild: all seven rebuilt screens, desktop/mobile guest mission, images, human review, reroute, inheritance and exit passed.");
} finally {
  // Clean up only this test's own guest session if the browser failed before exit.
  if (page.url().startsWith(origin)) {
    await page.evaluate(async () => {
      const token = sessionStorage.getItem("marsense-guest-token");
      if (token) {
        await fetch("/api/public-demo/auth/logout", { method: "POST", headers: { "X-Marsense-Demo": token } }).catch(() => {});
        sessionStorage.removeItem("marsense-guest-token");
      }
    }).catch(() => {});
  }
  await browser.close();
}
