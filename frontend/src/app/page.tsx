import Image from "next/image";
import Link from "next/link";
import PublicDemoButton from "@/components/public-demo-button";
import { Orbit, Layers, ScanLine, ShieldCheck, Route, History, ArrowUpRight } from "lucide-react";
const features = [
  { icon: Layers, title: "Real NASA data", detail: "Cached orbital imagery, elevation and rover context." },
  { icon: ScanLine, title: "Compare & detect", detail: "Understand differences between prior and ground evidence." },
  { icon: ShieldCheck, title: "Human verified", detail: "AI informs the decision; people confirm the map." },
  { icon: Route, title: "Adaptive routes", detail: "Reevaluate the traverse using verified footprints." },
  { icon: History, title: "Living memory", detail: "Pass verified knowledge to the next EVA." },
];
export default function Home() {
  return <main className="showcase-landing product-home">
    <Image className="landing-terrain" unoptimized fill preload sizes="100vw" src="/api/assets/ground-navcam.jpg" alt="Cached NASA Perseverance Navcam Mars terrain" />
    <div className="landing-shade" />
    <header><Link className="wordmark" href="/"><Orbit size={30}/><span className="brand-stack"><span>MAR<span>SENSE</span></span><small>THE LIVING MARS MAP</small></span></Link><nav aria-label="Public navigation"><a href="#experience">Experience</a><Link href="/science">Science &amp; About</Link><a href="https://github.com/SDAFIK/MARSENSE">GitHub <ArrowUpRight size={12}/></a><Link href="/workspace-login">My workspace</Link></nav><PublicDemoButton compact/></header>
    <section className="product-hero" aria-labelledby="intro-title">
      <p className="competition-kicker">TEAM REDSCAPE <span>·</span> NASA SPACE APPS 2026</p><p className="eyebrow">NASA TELLS US WHAT WE EXPECT.<br/>ASTRONAUTS SHOW US WHAT IS ACTUALLY THERE.</p>
      <h1 id="intro-title">MAR<span>SENSE</span></h1>
      <p className="landing-subtitle">THE LIVING MARS MAP</p>
      <p className="landing-copy">An evidence-aware Mars exploration prototype that learns from ground observations, compares them with NASA data, and helps future explorers inherit a more informed map.</p>
      <div className="hero-actions"><PublicDemoButton/><Link className="button secondary" href="/signup">Create your workspace</Link><a className="button secondary" href="#experience">Explore the mission story</a></div>
      <div className="hero-orbital" aria-label="Mission concept"><div className="hero-orbital-label"><span>JEZERO CRATER</span><small>18.44° N, 77.45° E</small></div><Image unoptimized loading="eager" width={280} height={160} src="/api/assets/jezero-ctx.png" alt="Cached Jezero orbital imagery"/><div className="hero-orbital-label"><span>EXPECT · ORBITAL PRIOR</span><small>NASA CTX</small></div><Image unoptimized loading="eager" width={280} height={160} src="/api/assets/ground-navcam.jpg" alt="NASA Perseverance Navcam boulder field"/><div className="hero-orbital-label"><span>OBSERVE · GROUND CONTEXT</span><small>Navcam</small></div><p>Real NASA images · illustrative mission pairing</p></div>
    </section>
    <section id="experience" className="product-experience"><div className="feature-grid">{features.map(({icon:Icon,title,detail})=><article key={title}><Icon size={23}/><h2>{title}</h2><p>{detail}</p></article>)}</div><div className="product-steps">{["EXPECT","OBSERVE","COMPARE","VERIFY","LEARN","INHERIT"].map((s,i)=><div className="product-step" key={s}><span>0{i+1}</span><strong>{s}</strong></div>)}</div></section>
    <section id="science" className="competition-science"><div><p className="eyebrow">SCIENTIFIC FOUNDATION</p><h2>Evidence before decisions.</h2><p>NASA orbital imagery provides the baseline. Ground observations challenge assumptions, human reviewers decide, and supported changes inform computed routes and future mission memory.</p></div><div><p className="eyebrow">EXPLORE THE PROJECT</p><Link href="/science">NASA sources &amp; provenance <ArrowUpRight size={14}/></Link><a href="https://github.com/SDAFIK/MARSENSE">Source code &amp; documentation <ArrowUpRight size={14}/></a><Link href="/workspace-login">Open your saved workspace <ArrowUpRight size={14}/></Link><Link href="/register">Join an invited mission <ArrowUpRight size={14}/></Link></div></section><footer>Real cached NASA imagery · Illustrative mission geometry · Human verification required · Team Redscape · <Link href="/login">Operator access</Link></footer>
  </main>;
}
