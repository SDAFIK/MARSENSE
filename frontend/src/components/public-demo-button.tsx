"use client";

import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { launchGuestDemo } from "@/lib/api";

export default function PublicDemoButton({ compact = false, caption = true }: { compact?: boolean; caption?: boolean }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [slow, setSlow] = useState(false);
  async function launch() {
    setBusy(true);
    setError("");
    setSlow(false);
    const timer = window.setTimeout(() => setSlow(true), 6000);
    try {
      await launchGuestDemo();
      window.location.assign("/mission");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Demo unavailable. Please retry.");
    } finally {
      window.clearTimeout(timer);
      setBusy(false);
      setSlow(false);
    }
  }
  return <div className={`guest-launch${compact ? " compact" : ""}`}>
    <button className="button primary" onClick={launch} disabled={busy}>
      {busy ? "Preparing your demo…" : compact ? "Try demo" : "Launch Live Demo"} <ArrowRight size={18}/>
    </button>
    {!compact && caption && <p className="small muted">No account needed · Private simulated mission</p>}
    {busy && slow && !compact && <p className="small muted" role="status">The cloud service may be waking up. Your mission will open when it is ready.</p>}
    {error && <p role="alert" className="small">{error.includes("approved browser origin") ? "This website is not yet authorized by Mission Control. Please use the verified release link." : error} <button className="text-button" onClick={launch} disabled={busy}>Retry</button></p>}
  </div>;
}
