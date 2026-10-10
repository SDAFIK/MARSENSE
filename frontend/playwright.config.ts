import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  use: {
    baseURL: "http://127.0.0.1:3001",
    viewport: { width: 1440, height: 1000 },
    channel: process.env.PLAYWRIGHT_CHANNEL || "msedge",
    trace: "retain-on-failure",
    launchOptions: { args: ["--enable-unsafe-swiftshader"] },
  },
  reporter: [["list"], ["html", { open: "never" }]],
  webServer: [
    {
      command: `${process.platform === "win32" ? "..\\.venv\\Scripts\\python.exe" : "../.venv/bin/python"} ../scripts/e2e_backend.py`,
      url: "http://127.0.0.1:8001/api/health",
      timeout: 60000,
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --port 3001",
      url: "http://127.0.0.1:3001",
      timeout: 120000,
      reuseExistingServer: false,
      env: { BACKEND_URL: "http://127.0.0.1:8001", NEXT_DIST_DIR: ".next-e2e" },
    },
  ],
});
