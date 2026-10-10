import { test, expect } from "@playwright/test";

test("full map preserves mission framing and closes with Escape", async ({ page }) => {
  await page.goto("/mission");
  await page.getByRole("button", { name: "Open full map", exact: true }).click();
  await expect(page.locator(".map-expanded")).toBeVisible();
  await page.getByRole("checkbox", { name: "Routes", exact: true }).uncheck();
  await expect(page.getByRole("checkbox", { name: "Routes", exact: true })).not.toBeChecked();
  await page.getByRole("combobox", { name: "Orbital imagery layer" }).selectOption("ctx");
  await expect(page.getByRole("combobox", { name: "Orbital imagery layer" })).toHaveValue("ctx");
  await page.keyboard.press("Escape");
  await expect(page.locator(".map-expanded")).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Open full map", exact: true }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.screenshot({ path: "../docs/screenshots/full-map-mobile.png" });
});

test("Evidence Inspector exposes source ancestry without changing final decisions", async ({ page, request }) => {
  const response = await request.post("/api/observations/demo", { data: { mission_id: "eva-01", scenario: "match" } });
  expect(response.ok()).toBeTruthy();
  await page.goto("/evidence");
  await page.getByText("Evidence ancestry & independent support", { exact: true }).click();
  await expect(page.getByText("Supporting evidence:", { exact: false })).toBeVisible();
  await page.getByLabel("Instrument / source").fill("Prototype camera");
  await page.getByLabel("Acquisition episode").fill("single-burst");
  await page.getByLabel("Independence rationale").fill("Single correlated replay acquisition, not independent validation.");
  await page.getByRole("button", { name: "Record source declaration" }).click();
  await expect(page.getByText("Prototype camera / episode single-burst", { exact: false })).toBeVisible();
});
