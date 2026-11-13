"use client";

import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { launchGuestDemo } from "@/lib/api";

export default function PublicDemoButton() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function launch() {
    setBusy(true);
    setError("");
    try {
      await launchGuestDemo();
      window.location.assign("/mission");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Demo unavailable. Please retry.");
    } finally {
      setBusy(false);
    }
  }
  return <div className="guest-launch">
    <button className="button primary" onClick={launch} disabled={busy}>
      {busy ? "Preparing your demo…" : "Launch Live Demo"} <ArrowRight size={18}/>
    </button>
    <p className="small muted">No account needed · Private simulated mission</p>
    {error && <p role="alert" className="small">{error}</p>}
  </div>;
}
