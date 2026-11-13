# Vercel deployment

The user authorized public deployment and made the source repository public:
https://github.com/SDAFIK/MARSENSE . Verified 2026-11-13: existing Docker/Tailscale
backend https://desktop-sdfik.tailf13324.ts.net returns production health 200.
Vercel project redscape has staging deployment
https://redscape-nzyvxnmnx-sadib-dewans-projects.vercel.app (commit c926819),
READY with homepage, health, session, login and NASA imagery checks passing.
Authenticated hosted browser acceptance and final production promotion remain gated.

## Frontend import

1. Sign in to Vercel and import `SDAFIK/MARSENSE`. Use **Redscape** as the
   requested project/team display name, with project slug `redscape` if
   available. The final hostname must be taken from the successful deployment;
   do not assume ownership of `redscape.vercel.app`.
2. Set Root Directory to `frontend` and Framework Preset to Next.js.
3. Use the project's `npm run build` and default Next.js output settings.
4. Set the server-only `BACKEND_URL` to the public HTTPS FastAPI origin.
   This value is required at build time because the API rewrite is generated
   by `next.config.ts`. Do not use localhost or a `NEXT_PUBLIC` secret.
5. Deploy, then verify `/api/health`, source imagery, sign-in and the complete
   observation -> verification -> rerouting -> reload -> inheritance flow.
6. Add the verified public website URL to README and repository About settings.

## Durable backend requirement

Vercel can execute FastAPI functions, but its function filesystem does not
provide durable shared SQLite storage. The current backend also stores uploads
and original evidence on disk. Deploy that backend on a persistent host using
the existing production configuration; do not move its database to `/tmp`,
silently reset missions, or expose writable unauthenticated demo mode.

Configure production identities, HTTPS and exact allowed browser origin. For
the existing single-instance deployment use the named mission-data volume.
Keep local user services/data intact. See `../DEPLOYMENT.md` for storage,
identity, backup and recovery steps. Alternatively, a separately specified
database/object-storage migration would be needed for an entirely serverless
system; it has not been performed.

Vercel Hobby project redscape uses the frontend root, Next.js and Node 24.x.
The staging environment's server-only BACKEND_URL points to the existing
Tailscale origin. No paid server or database was created. Do not treat a staging
deployment as production; prepare the production environment variables and
exact CORS origin, stage the tested build, verify hosted authentication and
mission workflow, then promote only after all release gates pass. The GitHub
repository remains public; GitHub Pages is not the backend deployment path.

References: https://vercel.com/docs/frameworks/backend/fastapi and
https://vercel.com/kb/guide/is-sqlite-supported-in-vercel .
