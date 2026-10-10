import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./auth-e2e", workers: 1, timeout: 60000,
  use: { baseURL: "http://127.0.0.1:3002", channel: "msedge", viewport: { width: 1440, height: 1000 } },
  webServer: [
    { command: "..\\.venv\\Scripts\\python.exe ../scripts/e2e_backend.py", url: "http://127.0.0.1:8002/api/health", timeout: 60000, env: { MARSENSE_E2E_AUTH: "1" } },
    { command: "npm run dev -- --port 3002", url: "http://127.0.0.1:3002", timeout: 120000, env: { BACKEND_URL: "http://127.0.0.1:8002", NEXT_DIST_DIR: ".next-auth-e2e" } },
  ],
});
