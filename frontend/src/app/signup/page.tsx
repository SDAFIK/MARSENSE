import Image from "next/image";
import Link from "next/link";
import { Orbit, ArrowLeft } from "lucide-react";
import WorkspaceAuth from "@/components/workspace-auth";
import PublicDemoButton from "@/components/public-demo-button";

export default function SignupPage() {
  return <main className="product-login">
    <Image unoptimized fill preload sizes="100vw" src="/api/assets/ground-navcam.jpg" alt="NASA Perseverance Navcam terrain" />
    <div className="login-shade"/>
    <header><Link className="wordmark" href="/"><Orbit size={30}/><span className="brand-stack"><span>MAR<span>SENSE</span></span><small>THE LIVING MARS MAP</small></span></Link><Link href="/"><ArrowLeft size={16}/> Back to Home</Link></header>
    <div className="login-content">
      <section><p className="eyebrow">YOUR DISCOVERIES. YOUR MISSION.</p><h1>Build your<br/><span>Living Map</span></h1><p>Observe, verify, adapt and preserve your own exploration knowledge.</p></section>
      <section className="login-card"><h2>Create your workspace</h2><p>Start an independent Jezero mission and save your exploration history.</p><WorkspaceAuth signup/><PublicDemoButton/><p className="small muted">Joining an existing operator mission? <Link href="/register">Use your invitation</Link>.</p></section>
    </div>
  </main>;
}
