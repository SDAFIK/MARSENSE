# MARSENSE public competition demo

## Judge journey

Open the public homepage and choose **Launch Live Demo**. No account, invitation or administrator password is needed after the guest-enabled release is deployed.

1. Mission Control: inspect the Jezero orbital prior, Area 14 and Route Alpha.
2. OBSERVE: choose the boulder-field replay, then Analyze terrain.
3. COMPARE: inspect the provisional difference and affected assumption A17.
4. VERIFY: review and confirm the simulated observation (or request evidence/reject).
5. LEARN: inspect the computed Route Beta and bounded verified footprint.
6. Select EVA-02 to inspect inherited knowledge. Explore Astronaut View, Evidence Inspector, Route Comparison and Exploration Memory.
7. Open the GUEST DEMO access menu and select Reset my demo or Exit demo.

The demonstration uses real cached NASA pixels with clearly labeled curated scenario annotations and illustrative local geometry. Guest verification is simulation, not a scientific measurement. The authenticated application retains real image upload, provenance, actual OpenCV processing and reviewer roles.

## Isolation and capacity

Guest tokens are scoped to temporary, independent SQLite stores, with a one-hour lifetime, bounded action count and a maximum of 32 active sessions per API process. The current deployment uses one API worker. Guest state survives ordinary navigation and reload within its browser tab but not server restart, expiry or explicit exit. Guests cannot access production mission APIs or upload images. Do not publish administrator credentials. Production records and original NASA assets are not reset by the demo.

## Release checks

- Exact-head application and Docker CI, including the production-mode guest browser cases.
- Run the Windows host record-preservation helper before upgrading; retain backups and rollback images.
- Deploy the tested release with exact HTTPS origins; verify health and run the following against the actual production hostname and final Vercel hostname:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/hosted-public-demo.ps1 -Origin https://<public-origin>
```

This credential-free smoke test creates two temporary guests, executes the full mission workflow and validates separation, reset, logout and production API denial. It never authenticates into or resets the production workspace. A separate browser walkthrough checks map rendering, images, navigation and responsive appearance.

The existing authenticated showcase is a separate environment. It is not the anonymous judge link. Until deployment and real signed-out acceptance pass, the no-login demo is a release candidate, not a verified live feature.
