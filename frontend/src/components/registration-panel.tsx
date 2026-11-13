"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, jsonRequest } from "@/lib/api";

export default function RegistrationPanel() {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [token, setToken] = useState("");
  const [username, setUsername] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [registered, setRegistered] = useState(false);
  useEffect(() => {
    api<{ registration_enabled?: boolean }>("/auth/session")
      .then((state) => setEnabled(Boolean(state.registration_enabled)))
      .catch(() => setError("Unable to check registration availability."));
  }, []);
  async function register() {
    setError("");
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await api("/auth/register", jsonRequest({ token: token.trim(), username, name: name.trim(), password }));
      setToken("");
      setPassword("");
      setConfirm("");
      setRegistered(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed. Contact Mission Control.");
    } finally {
      setBusy(false);
    }
  }
  return <section className="auth-panel panel" aria-label="Invitation registration">
    {registered ? <div role="status"><h3>Account registered</h3><p>Your invitation has been redeemed. Sign in with your new credentials.</p><Link className="button primary" href="/login">Continue to sign in</Link></div>
      : enabled ? <form onSubmit={(e) => { e.preventDefault(); void register(); }}>
        <label>Invitation code<input required autoComplete="off" spellCheck={false} value={token} onChange={(e) => setToken(e.target.value)} /></label>
        <label>Username<input required autoComplete="username" minLength={3} maxLength={40} pattern="[a-z0-9][a-z0-9_.\x2d]{2,39}" value={username} onChange={(e) => setUsername(e.target.value.toLowerCase())} /></label>
        <p className="small muted">Use 3–40 lowercase letters, digits, periods, underscores or hyphens.</p>
        <label>Display name<input required autoComplete="name" minLength={2} maxLength={80} value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label>Password<input required type="password" autoComplete="new-password" minLength={15} maxLength={256} value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        <label>Confirm password<input required type="password" autoComplete="new-password" minLength={15} maxLength={256} value={confirm} onChange={(e) => setConfirm(e.target.value)} /></label>
        <p className="small muted">Choose at least 15 characters. Your role comes from your invitation.</p>
        <button className="button primary" disabled={busy}>{busy ? "Registering…" : "Create invited account"}</button>
        <Link href="/login">Already have an account? Sign in</Link>
      </form> : <p role="status">{enabled === false ? "Registration is unavailable in this environment. Ask your mission administrator." : "Checking registration availability…"}</p>}
    {error && <p role="alert" className="error-message">{error}</p>}
  </section>;
}
