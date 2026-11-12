import Image from "next/image";
import Link from "next/link";
import { Orbit, ArrowLeft } from "lucide-react";
import AuthPanel from "@/components/auth-panel";
export default function LoginPage() {
  return <main className="product-login">
    <Image unoptimized fill preload sizes="100vw" src="/api/assets/ground-navcam.jpg" alt="NASA Perseverance Navcam terrain" />
    <div className="login-shade"/>
    <header><Link className="wordmark" href="/"><Orbit size={30}/><span className="brand-stack"><span>MAR<span>SENSE</span></span><small>THE LIVING MARS MAP</small></span></Link><Link href="/"><ArrowLeft size={16}/> Back to Home</Link></header>
    <div className="login-content"><section><p className="eyebrow">NASA TELLS US WHAT WE EXPECT.</p><h1>Welcome to<br/>MAR<span>SENSE</span></h1><p>The Living Mars Map</p></section><section className="login-card"><h2>Welcome Back</h2><p>Access Mission Control with your authorized account.</p><AuthPanel afterSignIn="/mission"/><Link className="button secondary" href="/mission">Open mission workspace</Link><p className="small muted">Roles are assigned by the administrator. No public account creation or NASA sign-in is provided.</p></section></div>
  </main>;
}
