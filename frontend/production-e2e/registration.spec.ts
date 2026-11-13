import { expect, test } from "@playwright/test";

test("invite-only registration, role assignment and authenticated browser access", async ({ page }, testInfo) => {
  await page.goto("/login");
  await page.getByLabel("Username", { exact: true }).fill("operator");
  await page.getByLabel("Password", { exact: true }).fill("isolated-admin-test-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/mission$/);
  await page.locator("summary").filter({ hasText: "Test Administrator" }).click();
  await page.getByRole("link", { name: "Account settings" }).click();
  await expect(page).toHaveURL(/\/account$/);
  await page.getByRole("button", { name: "Issue invitation" }).click();
  const code = await page.locator("[data-invitation-code]").textContent();
  expect(code).toHaveLength(43);
  await page.getByRole("button", { name: "Hide code" }).click();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("button", { name: "Sign in", exact: true })).toBeVisible();
  await page.goto("/register");
  for (const [label, width, height] of [
    ["desktop", 1440, 1000], ["mobile", 390, 844], ["small-mobile", 360, 800],
  ] as const) {
    await page.setViewportSize({ width, height });
    await expect(page.getByRole("button", { name: "Create invited account" })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
    await page.screenshot({ path: testInfo.outputPath(`registration-${label}.png`), fullPage: true });
  }
  await page.getByLabel("Invitation code", { exact: true }).fill(code!);
  await page.getByLabel("Username", { exact: true }).fill("invited-explorer");
  await page.getByLabel("Display name", { exact: true }).fill("Invited Explorer");
  await page.getByLabel("Password", { exact: true }).fill("isolated-invited-test-password");
  await page.getByLabel("Confirm password", { exact: true }).fill("isolated-invited-test-password");
  await page.getByRole("button", { name: "Create invited account" }).click();
  await expect(page.getByText("Account registered", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Continue to sign in" }).click();
  await page.getByLabel("Username", { exact: true }).fill("invited-explorer");
  await page.getByLabel("Password", { exact: true }).fill("isolated-invited-test-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/mission$/);
  await expect(page.getByRole("tab", { name: "EXPECT", exact: true })).toBeVisible();
  await page.reload();
  const state = await (await page.request.get("/api/auth/session")).json();
  expect(state.user.role).toBe("ASTRONAUT");
  await page.locator("summary").filter({ hasText: "Invited Explorer" }).click();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("heading", { name: "Sign in to the living map" })).toBeVisible();
});
