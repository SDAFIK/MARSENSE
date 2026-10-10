# MARSENSE frontend - Redscape

The Next.js frontend is published in the public
[MARSENSE repository](https://github.com/SDAFIK/MARSENSE/tree/master/frontend).
Backend hosting is deferred at the user's request. No live Vercel deployment
has been verified and no paid backend server has been created.

## Screens

- Landing: introduces the NASA prior -> observation -> comparison -> learning flow.
- Mission Control: EXPECT, OBSERVE, COMPARE, VERIFY and LEARN local contexts.
- Astronaut View: next target, active route, terrain evidence and review actions.
- Evidence Inspector: original sources, model output, human interpretation and decisions.
- Exploration Memory: chronological evidence locations and future-EVA inheritance.
- Before & After: aligned prior and confirmed-footprint map comparison.

The interface uses real cached NASA imagery and explicitly illustrative mission
geometry. Human verification, source provenance and supported footprint limits
remain part of the existing backend behavior.

## Local development

Use Node.js 24 and start the Python backend using the repository README.
Then, from this directory:

```powershell
npm ci
$env:BACKEND_URL='http://127.0.0.1:8000'
npm run dev
```

Open http://127.0.0.1:3000 . `BACKEND_URL` is a server-only setting. API calls
use the same-origin `/api` rewrite. Without a running API, imagery, mission
records, verification and rerouting are unavailable; source delivery does not
make those services live.

## Checks

```powershell
npm run test
npm run lint
npm run typecheck
npm run build
```

The redesign passed nine component tests, lint, TypeScript and a production
build. See [visual QA](../design-qa.md) for browser acceptance and limitations.

## Vercel setup

Import `SDAFIK/MARSENSE` into the signed-in Vercel account. Requested project
name: `redscape`. Root Directory: `frontend`. Framework: Next.js.
The checked-in `vercel.json` selects the framework.

Configure a public HTTPS `BACKEND_URL` before deploying the connected system.
The current SQLite/upload backend needs durable storage. Vercel sign-in is
complete, but backend provisioning and full-system deployment are deferred.
See [Vercel deployment instructions](../docs/VERCEL_DEPLOYMENT.md).
