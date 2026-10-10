"use client";
import { useEffect, useState } from "react";
import { api, jsonRequest } from "@/lib/api";

type Session = {
  user: { name: string; role: string } | null;
  required: boolean;
  read_only: boolean;
};
export default function AuthPanel({ compact = false }: { compact?: boolean }) {
  const [session, setSession] = useState<Session | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    api<Session>("/auth/session")
      .then(setSession)
      .catch(() => {});
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
      window.location.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  }
  if (!session) return null;
  if (!session.required && !session.user && !session.read_only)
    return compact ? (
      <span className="demo-indicator">LOCAL DEMO SESSION</span>
    ) : null;
  const panel = (
    <section className="auth-panel panel" aria-label="Mission access">
      {session.read_only && (
        <p>Read-only demonstration · mission changes are disabled.</p>
      )}
      {session.user ? (
        <div>
          <strong>{session.user.name}</strong> ·{" "}
          {session.user.role.replaceAll("_", " ")}
          <button
            className="button secondary"
            disabled={busy}
            onClick={() => submit(true)}
          >
            Sign out
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
        {session.user?.name ?? (session.required ? "SIGN IN" : "READ ONLY")}
      </summary>
      {panel}
    </details>
  ) : (
    panel
  );
}
