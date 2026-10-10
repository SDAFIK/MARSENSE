import { expect, test } from "@playwright/test";

test("calibrated orbital context keeps provenance and uncertainty visible", async ({ page }) => {
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/evidence");
    await page.locator("summary").filter({ hasText: "Orbital CRISM science context" }).click();
    await expect(page.getByText(/FRT000047A3_07_BRTANJ_MTR3/)).toBeVisible();
    await expect(page.getByText(/No mineral identity inferred/)).toBeVisible();
    await expect(page.getByText(/PDS and ENVI header mappings differ/)).toBeVisible();
    await page.locator("summary").filter({ hasText: "Calibrated Navigation Camera Left" }).click();
    await expect(page.getByText("Image footprint unavailable. Spatial uncertainty unknown.").first()).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  }
});
