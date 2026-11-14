import Link from "next/link";
import { Orbit, ArrowLeft } from "lucide-react";
import AuthPanel from "@/components/auth-panel";
import AccountManager from "@/components/account-manager";

export default function AccountPage() {
  return <main className="product-login account-page">
    <header><Link className="wordmark" href="/"><Orbit size={30}/><span className="brand-stack"><span>MAR<span>SENSE</span></span><small>THE LIVING MARS MAP</small></span></Link><Link href="/mission"><ArrowLeft size={16}/> Mission Control</Link></header>
    <div className="account-layout"><section className="login-card"><p className="eyebrow">SECURE EXPLORATION</p><h1>Your mission access</h1><AuthPanel/><p className="small muted">Administrative bootstrap identities are managed privately by the host operator.</p></section><AccountManager/></div>
  </main>;
}
