import { defineConfig } from "@playwright/test";

const python = process.platform === "win32"
  ? "..\\.venv\\Scripts\\python.exe"
  : "../.venv/bin/python";

export default defineConfig({
  testDir: "./production-e2e",
  outputDir: "./test-results/production",
  workers: 1,
  timeout: 90000,
  use: {
    baseURL: "http://localhost:3004",
    viewport: { width: 1440, height: 1000 },
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
    launchOptions: { args: ["--enable-unsafe-swiftshader"] },
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `${python} ../scripts/e2e_backend.py`,
      url: "http://127.0.0.1:8004/api/health",
      timeout: 60000,
      reuseExistingServer: false,
      env: { MARSENSE_E2E_PRODUCTION: "1" },
    },
    {
      command: "npm run dev -- --port 3004",
      url: "http://localhost:3004",
      timeout: 120000,
      reuseExistingServer: false,
      env: {
        BACKEND_URL: "http://127.0.0.1:8004",
        NEXT_DIST_DIR: ".next-production-e2e",
      },
    },
  ],
});
