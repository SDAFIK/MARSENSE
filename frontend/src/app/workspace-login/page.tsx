import Image from "next/image";
import Link from "next/link";
import { Orbit, ArrowLeft } from "lucide-react";
import WorkspaceAuth from "@/components/workspace-auth";
import PublicDemoButton from "@/components/public-demo-button";

export default function WorkspaceLoginPage() {
  return <main className="product-login">
    <Image unoptimized fill preload sizes="100vw" src="/api/assets/ground-navcam.jpg" alt="NASA Perseverance Navcam terrain" />
    <div className="login-shade"/>
    <header><Link className="wordmark" href="/"><Orbit size={30}/><span className="brand-stack"><span>MAR<span>SENSE</span></span><small>THE LIVING MARS MAP</small></span></Link><Link href="/"><ArrowLeft size={16}/> Back to Home</Link></header>
    <div className="login-content">
      <section><p className="eyebrow">WELCOME BACK, EXPLORER.</p><h1>Return to<br/><span>Mars</span></h1><p>Continue your saved mission, observations and evidence history.</p></section>
      <section className="login-card"><h2>Sign in to your workspace</h2><WorkspaceAuth/><PublicDemoButton/><p className="small muted">Existing invited mission? <Link href="/login">Operator mission sign in</Link>.</p></section>
    </div>
  </main>;
}
