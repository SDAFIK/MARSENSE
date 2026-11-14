"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, clearGuestDemo, clearWorkspaceMode, jsonRequest } from "@/lib/api";

type Session = {
  user: { name: string; role: string } | null;
  required: boolean;
  read_only: boolean;
  registration_enabled?: boolean;
  public_demo?: boolean;
  personal_workspace?: boolean;
  environment: "demo" | "production" | "showcase";
};
export default function AuthPanel({ compact = false, afterSignIn }: { compact?: boolean; afterSignIn?: "/mission" }) {
  const [session, setSession] = useState<Session | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    api<Session>("/auth/session")
      .then(setSession)
      .catch(() => setError("Mission authentication is unavailable. Reconnect and retry."));
  }, []);
  async function submit(logout = false) {
    setBusy(true);
    setError("");
    try {
      await api(
        logout ? "/auth/logout" : "/auth/login",
        jsonRequest(logout ? {} : { username, password }),
      );
      setPassword("");
      if (session?.public_demo && logout) {
        clearGuestDemo();
        window.location.assign("/");
        return;
      }
      if (session?.personal_workspace && logout) {
        clearWorkspaceMode();
        window.location.assign("/workspace-login");
        return;
      }
      if (!logout) { clearGuestDemo(); clearWorkspaceMode(); }
      if (!logout && afterSignIn) {
        window.location.href = new URL(afterSignIn, window.location.origin).href;
      } else window.location.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  }
  async function resetShowcase() {
    if (!window.confirm(session?.public_demo ? "Reset only your guest demo?" : "Reset only the isolated showcase mission history?")) return;
    setBusy(true);
    setError("");
    try {
      await api("/showcase/reset", jsonRequest({}));
      sessionStorage.setItem("marsense-mission", "eva-01");
      window.location.href = new URL("/mission", window.location.origin).href;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Showcase reset failed");
    } finally { setBusy(false); }
  }
  if (!session) return <span className="small muted" role={error ? "alert" : "status"}>
    {error || "Checking mission access…"}
    {error && <button className="text-button" onClick={() => window.location.reload()}>Retry</button>}
  </span>;
  if (!session.required && !session.user && !session.read_only)
    return compact ? (
      <span className="demo-indicator">LOCAL DEMO SESSION</span>
    ) : null;
  const panel = (
    <section className="auth-panel panel" aria-label="Mission access">
      {session.public_demo ? <p><strong>PRIVATE GUEST DEMO</strong> · Curated replay, simulated footprints. Your session expires after one hour; no production records are touched.</p> : session.environment === "showcase" && <p><strong>ISOLATED SHOWCASE</strong> · Curated replay, simulated footprints. Separate mission history.</p>}
      {session.personal_workspace && <p><strong>PERSONAL WORKSPACE</strong> · Your saved mission and uploaded evidence are separate from all other accounts.</p>}
      {session.read_only && (
        <p>Read-only demonstration · mission changes are disabled.</p>
      )}
      {session.user ? (
        <div>
          <strong>{session.user.name}</strong> ·{" "}
          {session.user.role.replaceAll("_", " ")}
          {(session.public_demo || (session.environment === "showcase" && session.user.role === "ADMIN")) && (
            <button className="button secondary" disabled={busy} onClick={resetShowcase}>{session.public_demo ? "Reset my demo" : "Reset showcase"}</button>
          )}
          {session.registration_enabled && <Link className="button secondary" href="/account">Account settings</Link>}
          <button
            className="button secondary"
            disabled={busy}
            onClick={() => submit(true)}
          >
            {session.public_demo ? "Exit demo" : "Sign out"}
          </button>
        </div>
      ) : (
        session.required && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void submit();
            }}
          >
            <strong>Sign in to the mission workspace</strong>
            <label>
              Username
              <input
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </label>
            <label>
              Password
              <input
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            <button className="button primary" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"}
            </button>
            {session.registration_enabled && <Link href="/register">Register with an invitation</Link>}
          </form>
        )
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
  return compact ? (
    <details
      className="session-access"
      open={session.required && !session.user}
    >
      <summary>
        {session.public_demo ? "GUEST DEMO" : session.personal_workspace ? "MY WORKSPACE" : `${session.environment === "showcase" ? "SHOWCASE · " : ""}${session.user?.name ?? (session.required ? "SIGN IN" : "READ ONLY")}`}
      </summary>
      {panel}
    </details>
  ) : (
    panel
  );
}
