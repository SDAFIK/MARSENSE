# F1 authenticated showcase

This separate Docker project is an operator-controlled, shared showcase, not a
public anonymous or per-visitor sandbox. Only authorized accounts may mutate
it; only ADMIN may reset it. Production replay and reset remain disabled.
The showcase uses a distinct cookie, dedicated identity file and database volume.
Uploads are disabled in showcase; curated NASA replay is labeled simulated.

Run on the existing host using a separate private identity file (create with
scripts/create_auth_user.py or the existing Docker identity provisioning command,
using a different directory and credentials). Set MARSENSE_SHOWCASE_USERS_FILE
to that absolute file and MARSENSE_SHOWCASE_ORIGINS to a JSON array containing
the exact HTTPS showcase origin. For the same Funnel hostname on port 8443,
the origin includes :8443. Do not reuse production credentials.

```powershell
docker compose -p marsense-showcase -f compose.showcase.yaml config --quiet
docker compose -p marsense-showcase -f compose.showcase.yaml up -d --build --wait
curl.exe --fail http://127.0.0.1:8081/api/health
```

Only after CI and local checks pass, configure a separate HTTPS Funnel listener
on 8443 targeting loopback port 8081. Check existing Funnel configuration and
do not replace the production listener. Verify the actual origin, sign in,
record the obstacle replay, confirm, inspect Beta and EVA-02, reload, then reset
using the authenticated admin control. Reset clears only showcase mission
entities; authentication records remain. Do not distribute admin credentials.

No paid resources, no production data migration, no production volume deletion.
The showcase is shared by invited users; concurrent presentations should be
scheduled or hosted in separate isolated instances. External hosting and live
acceptance are not claimed until actually verified.
