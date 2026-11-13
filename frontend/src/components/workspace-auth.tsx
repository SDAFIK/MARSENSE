"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { api, enterWorkspace, jsonRequest } from "@/lib/api";

type Session = { user: { name: string } | null; signup_enabled: boolean; cloud_auth?: boolean };

export default function WorkspaceAuth({ signup = false }: { signup?: boolean }) {
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [session, setSession] = useState<Session | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => {
    let active = true;
    api<Session>("/workspaces/auth/session").then(value => {
      if (active) setSession(value);
    }).catch(() => { if (active) setError("Workspace identity service is unavailable. Reload to retry."); });
    return () => { active = false; };
  }, []);
  function enter() {
    enterWorkspace();
    window.location.assign("/mission");
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      setMessage("");
      const result = await api<{ confirmation_required?: boolean }>("/workspaces/auth/" + (signup ? "signup" : "login"),
        jsonRequest({ ...(session?.cloud_auth ? { email: username } : { username }), password, ...(signup ? { name } : {}) }));
      setPassword("");
      if (result.confirmation_required) {
        setMessage("Check your email to confirm your account, then return here to sign in.");
        return;
      }
      enter();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Workspace access failed.");
    } finally { setBusy(false); }
  }
  return <section className="auth-panel" aria-label="Personal workspace account">
    {session?.user && <div className="notice">
      <p>Welcome back, {session.user.name}.</p>
      <button className="button primary" onClick={enter}>Continue to my workspace</button>
    </div>}
    {!session ? <p role="status">{error ? "Identity service unavailable." : "Checking account access…"}</p> : !session.signup_enabled ? <p role="alert">Personal accounts are unavailable here. You can still launch the guest demonstration.</p> : <form onSubmit={submit}>
      {signup && <label>Display name<input required value={name} maxLength={80} minLength={2} autoComplete="name" onChange={e => setName(e.target.value)}/></label>}
      <label>{session.cloud_auth ? "Email" : "Username"}<input type={session.cloud_auth ? "email" : "text"} required autoComplete="username" value={username} maxLength={session.cloud_auth ? 254 : signup ? 40 : 100} minLength={signup ? 3 : 1} pattern={!session.cloud_auth && signup ? "[a-z0-9][a-z0-9_.\\-]{2,39}" : undefined} onChange={e => setUsername(e.target.value)}/></label>
      <label>Password<input type="password" required autoComplete={signup ? "new-password" : "current-password"} minLength={signup ? 15 : 1} maxLength={signup ? 256 : 1024} value={password} onChange={e => setPassword(e.target.value)}/></label>
      {signup && <p className="small muted">Use at least 15 characters. Your personal mission data is private to your account. {session.cloud_auth ? "Confirm your email before signing in." : "No email or external identity provider is required."}</p>}
      <button className="button primary" disabled={busy}>{busy ? "Preparing workspace…" : signup ? "Create my workspace" : "Sign in"}</button>
    </form>}
    {error && <p role="alert">{error}</p>}
    {message && <p role="status" className="notice">{message}</p>}
    <p className="small">{signup ? <>Already have an account? <Link href="/workspace-login">Sign in</Link></> : <>New here? <Link href="/signup">Create an account</Link></>}</p>
  </section>;
}
