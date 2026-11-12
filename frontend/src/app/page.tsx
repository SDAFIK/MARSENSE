import Image from "next/image";
import Link from "next/link";
import { Orbit, ArrowRight, Layers, ScanLine, ShieldCheck, Route, History } from "lucide-react";
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
    <header><Link className="wordmark" href="/"><Orbit size={30}/><span className="brand-stack"><span>MAR<span>SENSE</span></span><small>THE LIVING MARS MAP</small></span></Link><nav aria-label="Public navigation"><Link href="/mission">Mission</Link><a href="#experience">Experience</a><Link href="/login">Sign in</Link></nav><Link className="button primary" href="/mission">Enter Mission Control <ArrowRight size={16}/></Link></header>
    <section className="product-hero" aria-labelledby="intro-title">
      <p className="eyebrow">NASA TELLS US WHAT WE EXPECT.<br/>ASTRONAUTS SHOW US WHAT IS ACTUALLY THERE.</p>
      <h1 id="intro-title">MAR<span>SENSE</span></h1>
      <p className="landing-subtitle">THE LIVING MARS MAP</p>
      <p className="landing-copy">An evidence-aware Mars exploration prototype that learns from ground observations, compares them with NASA data, and helps future explorers inherit a more informed map.</p>
      <div className="hero-actions"><Link className="button primary" href="/mission">Enter Mission Control <ArrowRight size={18}/></Link><a className="button secondary" href="#experience">Explore the mission story</a></div>
      <div className="hero-orbital"><Image unoptimized width={280} height={160} src="/api/assets/jezero-ctx.png" alt="Cached Jezero orbital imagery"/><span>JEZERO CRATER · 18.44° N, 77.45° E</span></div>
    </section>
    <section id="experience" className="product-experience"><div className="feature-grid">{features.map(({icon:Icon,title,detail})=><article key={title}><Icon size={23}/><h2>{title}</h2><p>{detail}</p></article>)}</div><div className="product-steps">{["EXPECT","OBSERVE","COMPARE","VERIFY","LEARN"].map((s,i)=><Link key={s} href="/mission"><span>0{i+1}</span><strong>{s}</strong></Link>)}</div></section>
    <footer>Real cached NASA imagery · Illustrative mission geometry · Human verification required · Team Redscape</footer>
  </main>;
}
