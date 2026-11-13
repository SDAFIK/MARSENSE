import { defineConfig } from "@playwright/test";

const python = process.platform === "win32"
  ? "..\\.venv\\Scripts\\python.exe"
  : "../.venv/bin/python";

export default defineConfig({
  testDir: "./auth-e2e",
  workers: 1,
  timeout: 60000,
  use: {
    baseURL: "http://127.0.0.1:3002",
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
    viewport: { width: 1440, height: 1000 },
    launchOptions: { args: ["--enable-unsafe-swiftshader"] },
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `${python} ../scripts/e2e_backend.py`,
      url: "http://127.0.0.1:8002/api/health",
      timeout: 60000,
      reuseExistingServer: false,
      env: { MARSENSE_E2E_AUTH: "1" },
    },
    {
      command: "npm run dev -- --port 3002",
      url: "http://127.0.0.1:3002",
      timeout: 120000,
      reuseExistingServer: false,
      env: {
        BACKEND_URL: "http://127.0.0.1:8002",
        NEXT_DIST_DIR: ".next-auth-e2e",
      },
    },
  ],
});
