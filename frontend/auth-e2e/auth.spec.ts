import { test, expect } from "@playwright/test";

test("sign in, identity-bound confirmation, sign out", async ({ page }) => {
  await page.goto("/mission");
  await page.getByLabel("Username", { exact: true }).fill("reviewer");
  await page.getByLabel("Password", { exact: true }).fill("isolated-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
  await page.getByRole("button", { name: "Analyze terrain" }).click();
  await page.getByRole("button", { name: "Confirm observation", exact: true }).click();
  await expect(page.getByText("Confirmed by Test Reviewer", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("button", { name: "Sign in", exact: true })).toBeVisible();
});
