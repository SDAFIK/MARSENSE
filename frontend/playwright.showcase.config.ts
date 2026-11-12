import { defineConfig } from "@playwright/test";
const python = process.platform === "win32" ? "..\\.venv\\Scripts\\python.exe" : "../.venv/bin/python";
export default defineConfig({
  testDir:"./showcase-e2e",
  outputDir:"./test-results/showcase",
  workers:1,
  timeout:90000,
  use:{baseURL:"http://localhost:3003",channel:process.env.PLAYWRIGHT_CHANNEL || undefined, viewport:{width:1440,height:1000},launchOptions:{args:["--enable-unsafe-swiftshader"]},trace:"retain-on-failure"},
  webServer:[
    {command:`${python} ../scripts/e2e_backend.py`,url:"http://127.0.0.1:8003/api/health",timeout:60000,reuseExistingServer:false,env:{MARSENSE_E2E_SHOWCASE:"1"}},
    {command:"npm run dev -- --port 3003",url:"http://localhost:3003",timeout:120000,reuseExistingServer:false,env:{BACKEND_URL:"http://127.0.0.1:8003",NEXT_DIST_DIR:".next-showcase-e2e"}},
  ],
});
