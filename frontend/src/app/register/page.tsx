import Image from "next/image";
import Link from "next/link";
import { Orbit, ArrowLeft } from "lucide-react";
import RegistrationPanel from "@/components/registration-panel";

export default function RegisterPage() {
  return <main className="product-login">
    <Image unoptimized fill preload sizes="100vw" src="/api/assets/ground-navcam.jpg" alt="NASA Perseverance Navcam terrain" />
    <div className="login-shade"/>
    <header><Link className="wordmark" href="/"><Orbit size={30}/><span className="brand-stack"><span>MAR<span>SENSE</span></span><small>THE LIVING MARS MAP</small></span></Link><Link href="/login"><ArrowLeft size={16}/> Sign in</Link></header>
    <div className="login-content"><section><p className="eyebrow">AUTHORIZED EXPLORATION</p><h1>Join the<br/>MAR<span>SENSE</span> mission</h1><p>Your discoveries become part of the next explorer&apos;s knowledge.</p></section><section className="login-card"><h2>Mission registration</h2><p>Use the private, single-use invitation from your administrator. Registration does not grant administrative access.</p><RegistrationPanel/></section></div>
  </main>;
}
