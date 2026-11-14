"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { launchGuestDemo } from "@/lib/api";

export default function PublicDemoButton({ compact = false, caption = true }: { compact?: boolean; caption?: boolean }) {
  const router=useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function cloud() {
    setBusy(true);setError("");
    try {await launchGuestDemo();router.push("/mission");}
    catch(e){setError(e instanceof Error?e.message:"Cloud mission unavailable.");}
    finally{setBusy(false);}
  }
  return <div className={`guest-launch${compact ? " compact" : ""}`}>
    <button className="button primary" onClick={()=>router.push("/demo")}>
      {compact?"Try demo":"Launch Live Demo"} <ArrowRight size={18}/>
    </button>
    {!compact&&caption&&<p className="small muted">No account needed · Instant browser simulation · No cloud wait</p>}
    {!compact&&<><button className="text-button small" onClick={cloud} disabled={busy}>{busy?"Connecting to cloud…":"Launch Cloud Demo"}</button>{busy&&<p className="small muted" role="status">Cloud service may wake slowly. The instant demo remains available above.</p>}</>}
    {error&&<p role="alert" className="small">{error} <Link href="/demo" className="text-button">Open instant demo instead</Link></p>}
  </div>;
}
