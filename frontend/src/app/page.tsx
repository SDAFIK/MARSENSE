import Image from "next/image";
import Link from "next/link";
import PublicDemoButton from "@/components/public-demo-button";
import MarsGlobe from "@/components/mars-globe";
import { ArrowDown, ArrowUpRight, Orbit, Layers, ScanLine, ShieldCheck, Route, History, Compass } from "lucide-react";

const stages = [
  { label: "EXPECT", title: "Start with the orbital map", text: "NASA imagery establishes the prior terrain interpretation.", icon: Layers },
  { label: "OBSERVE", title: "See the ground", text: "A rover image or field observation challenges the assumption.", icon: ScanLine },
  { label: "COMPARE", title: "Find the difference", text: "Inspect expected and observed evidence side by side.", icon: Compass },
  { label: "VERIFY", title: "Put people in control", text: "A human confirms, rejects or requests more evidence.", icon: ShieldCheck },
  { label: "LEARN", title: "Recalculate the traverse", text: "Supported knowledge informs a new modeled route.", icon: Route },
  { label: "INHERIT", title: "Leave knowledge behind", text: "Future EVAs inherit verified persistent evidence.", icon: History },
];
export default function Home() {
  return <main className="mars-experience">
    <header className="mx-header">
      <Link className="mx-brand" href="/"><Orbit size={34}/><span>MARS<span>ENSE</span><small>THE LIVING MARS MAP</small></span></Link>
      <nav aria-label="Public navigation"><a href="#experience">The mission</a><Link href="/science">The science</Link><a href="https://github.com/SDAFIK/MARSENSE">GitHub <ArrowUpRight size={13}/></a></nav>
      <Link href="/workspace-login" className="mx-outline">My workspace <ArrowUpRight size={14}/></Link>
    </header>
    <section className="mx-hero" aria-labelledby="intro-title">
      <div className="mx-hero-copy">
        <p className="mx-kicker"><span/> TEAM REDSCAPE / NASA SPACE APPS 2026</p>
        <h1 id="intro-title">Every step makes<br className="mx-wide-break"/> Mars <em>more known.</em></h1>
        <p className="mx-lead">A living map for the next explorer. Compare what NASA sees from orbit with what humans discover on the ground, and turn verified evidence into better mission decisions.</p>
        <div className="mx-actions"><PublicDemoButton/><a href="#experience" className="mx-outline">Explore the mission <ArrowDown size={16}/></a></div>
        <div className="mx-proof"><span><ShieldCheck size={17}/> Human-verified decisions</span><span><Layers size={17}/> Real NASA imagery</span></div>
      </div>
      <div className="mx-planet" aria-label="Mars planetary context">
        <div className="mx-orbit mx-orbit-one"/><div className="mx-orbit mx-orbit-two"/>
        <div className="mx-planet-label"><span>01 / PLANETARY CONTEXT</span><strong>MARS</strong><small>NASA Viking imagery</small></div>
        <MarsGlobe/>
        <div className="mx-coordinate"><span>JEZERO CRATER</span><strong>18.44° N / 77.45° E</strong><small>Exploration scenario</small></div>
      </div>
      <div className="mx-hero-foot"><span>MISSION-01 / JEZERO RECONNAISSANCE</span><span>RESEARCH PROTOTYPE · NOT LIVE TELEMETRY</span></div>
    </section>
    <section className="mx-evidence-story" aria-labelledby="evidence-title">
      <div className="mx-section-heading"><p className="mx-kicker">01 / FROM ORBIT TO SURFACE</p><h2 id="evidence-title">One planet. Two perspectives.</h2><p>Real cached NASA imagery; the mission pairing and ground footprint are illustrative.</p></div>
      <div className="mx-image-pair">
        <figure><div className="mx-photo"><Image unoptimized fill sizes="(max-width: 750px) 100vw, 50vw" src="/api/assets/jezero-ctx.png" alt="Cached NASA CTX orbital terrain at Jezero"/></div><figcaption><span>01 / EXPECT</span><strong>Orbital perspective</strong><p>NASA CTX · retained prior</p></figcaption></figure>
        <div className="mx-pair-arrow" aria-hidden="true"><ArrowUpRight size={24}/></div>
        <figure><div className="mx-photo"><Image unoptimized fill sizes="(max-width: 750px) 100vw, 50vw" src="/api/assets/ground-navcam.jpg" alt="Cached NASA Perseverance Navcam surface image"/></div><figcaption><span>02 / OBSERVE</span><strong>Ground perspective</strong><p>Perseverance Navcam · cached context</p></figcaption></figure>
      </div>
    </section>
    <section id="experience" className="mx-journey"><div className="mx-section-heading"><p className="mx-kicker">02 / THE LIVING MAP</p><h2>Six steps. One continuous mission.</h2><p>Explore the complete evidence-to-knowledge workflow in your own isolated guest mission.</p></div>
      <div className="product-steps mx-stage-grid">{stages.map(({label,title,text,icon:Icon},i)=><article key={label}><div className="mx-stage-top"><Icon size={24}/><span>0{i+1}</span></div><small>{label}</small><h3>{title}</h3><p>{text}</p></article>)}</div>
      <div className="mx-journey-action"><PublicDemoButton compact/><Link href="/signup" className="mx-outline">Create a private workspace <ArrowUpRight size={15}/></Link></div>
    </section>
    <section className="mx-science"><div><p className="mx-kicker">03 / BUILT ON EVIDENCE</p><h2>Science first.<br/>Every decision traceable.</h2><p>Genuine NASA source products, preserved orbital priors, and a human decision record. MARSENSE does not claim live astronaut telemetry or certified navigation.</p></div><div><Link href="/science">NASA sources &amp; provenance <ArrowUpRight size={17}/></Link><a href="https://github.com/SDAFIK/MARSENSE">Source code &amp; documentation <ArrowUpRight size={17}/></a><Link href="/workspace-login">Open saved workspace <ArrowUpRight size={17}/></Link><Link href="/register">Join an invited mission <ArrowUpRight size={17}/></Link></div></section>
    <footer className="mx-footer"><span>TEAM REDSCAPE · NASA SPACE APPS 2026</span><span>Research prototype · <Link href="/login">Operator access</Link></span></footer>
  </main>;
}
