"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, jsonRequest } from "@/lib/api";

type Role = "ASTRONAUT" | "MISSION_CONTROL";
type Session = { user: { name: string; role: string } | null; registration_enabled?: boolean };
type Invitation = { id: string; role: Role; expires_at: number; used_by: string | null; revoked: boolean };
type Account = { id: string; username: string; name: string; role: Role; disabled: boolean };
type AdminState = { accounts: Account[]; invitations: Invitation[] };
export default function AccountManager() {
  const [session, setSession] = useState<Session | null>(null);
  const [state, setState] = useState<AdminState | null>(null);
  const [role, setRole] = useState<Role>("ASTRONAUT");
  const [code, setCode] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const refresh = useCallback(async () => {
    try {
      const current = await api<Session>("/auth/session");
      setSession(current);
      if (current.user?.role === "ADMIN" && current.registration_enabled) {
        setState(await api<AdminState>("/auth/admin"));
      } else setState(null);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Account service unavailable.");
    }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  async function action(path: string, body: unknown, message: string) {
    setBusy(true);
    setError("");
    try {
      const result = await api<{ token?: string }>(path, jsonRequest(body));
      if (result.token) setCode(result.token);
      setNotice(message);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Account action failed.");
    } finally {
      setBusy(false);
    }
  }
  return <section className="panel account-manager" aria-label="Mission account settings">
    <h2>Mission account settings</h2>
    {!session ? <p role="status">Checking account access…</p> : !session.user
      ? <p>Sign in to manage your account. <Link href="/login">Open mission sign in</Link></p>
      : <p><strong>{session.user.name}</strong> · {session.user.role.replaceAll("_", " ")}</p>}
    {state && <>
      <h3>Invite an explorer</h3>
      <p className="small muted">Codes expire after 24 hours, can be redeemed once and cannot create an administrator. Share privately.</p>
      <label className="field-label">Invited role<select value={role} disabled={busy} onChange={(e) => setRole(e.target.value as Role)}><option value="ASTRONAUT">Astronaut</option><option value="MISSION_CONTROL">Mission Control</option></select></label>
      <button className="button primary" disabled={busy} onClick={() => void action("/auth/invitations", { role }, "Invitation issued. Copy it before closing this page.")}>Issue invitation</button>
      {code && <div className="invite-code"><output data-invitation-code aria-label="Invitation code">{code}</output><button className="button secondary" onClick={async () => { try { await navigator.clipboard.writeText(code); setNotice("Invitation copied. Share it privately."); } catch { setNotice("Select and copy the code manually."); } }}>Copy code</button><button className="text-button" onClick={() => setCode(null)}>Hide code</button></div>}
      <h3>Invitation history</h3>
      {state.invitations.length === 0 && <p className="small muted">No invitations issued.</p>}
      {state.invitations.map((invite) => <article className="account-row" key={invite.id}><div><strong>{invite.role.replaceAll("_", " ")}</strong><p className="small muted">{invite.used_by ? "Redeemed" : invite.revoked ? "Revoked" : invite.expires_at * 1000 <= Date.now() ? "Expired" : "Pending"} · expires {new Date(invite.expires_at * 1000).toLocaleString()}</p></div>{!invite.used_by && !invite.revoked && <button className="button secondary" disabled={busy} onClick={() => void action("/auth/invitations/" + invite.id + "/revoke", {}, "Invitation revoked.")}>Revoke</button>}</article>)}
      <h3>Invited accounts</h3>
      {state.accounts.length === 0 && <p className="small muted">No registered accounts yet. Bootstrap identities remain managed by the operator.</p>}
      {state.accounts.map((account) => <article className="account-row" key={account.id}><div><strong>{account.name}</strong><p className="small muted">{account.username} · {account.role.replaceAll("_", " ")} · {account.disabled ? "Disabled" : "Active"}</p></div>{!account.disabled && <button className="button secondary" disabled={busy} onClick={() => { if (window.confirm("Disable this invited account and its access?")) void action("/auth/accounts/" + account.id + "/disable", {}, "Account disabled."); }}>Disable account</button>}</article>)}
    </>}
    {notice && <p role="status" className="small muted">{notice}</p>}
    {error && <p role="alert" className="error-message">{error} <button className="text-button" onClick={() => void refresh()}>Retry</button></p>}
    <Link className="button secondary" href="/mission">Return to Mission Control</Link>
  </section>;
}
