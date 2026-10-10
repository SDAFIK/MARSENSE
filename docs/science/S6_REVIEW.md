# S6 authentication implementation and review

Design sources reviewed 2026-10-10:
- https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

Opaque random 256-bit session secrets are stored only as SHA-256 identifiers
in SQLite. Cookies are HttpOnly, SameSite=Strict and Secure in production.
Server enforcement includes eight-hour absolute expiry, thirty-minute idle
expiry, logout revocation, approved Origin on cookie-authenticated mutations,
and Mission Control/Admin roles for review/source declarations. User IDs and
server-resolved names are recorded on immutable HumanDecision records with
mission, observation, decision and time. Existing local decisions retain their
self-asserted identity classification. Legacy service tokens can read only.

Passwords are salted scrypt N=131072/r=8/p=1; only hashes are provisioned in a
private operator-managed JSON file. No real account/password is seeded. Browser
credentials are never placed in localStorage. Fixed credentials in auth tests
belong only to disposable fixtures. Login failures are capped per direct client
address at five per five minutes and serialized within the single API worker.
Production must retain the documented reverse-proxy rate limit and single-worker
configuration; the in-process limiter is not a distributed anti-abuse service.

Security review: no anonymous production mutation bypass; no submitted reviewer
impersonation; no service-token mutation; source declarations use session names;
audit entities immutable; original human decisions remain unchanged. Demo mode
is explicitly local self-asserted behavior, and read_only blocks mission writes.
No external security assessment, public deployment or MFA claim is made.

Validation: role/identity/origin/logout/expiry/read-only integration tests pass;
25 auth-plus-core tests pass. Isolated browser sign-in → confirm as Test Reviewer
→ sign-out passes. Final Secure-cookie/throttling check recorded in STATUS.md.
