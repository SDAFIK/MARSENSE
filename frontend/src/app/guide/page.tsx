import Link from "next/link";
import PublicDemoButton from "@/components/public-demo-button";
import { ArrowLeft, ArrowRight, CheckCircle2, Compass, Layers, ScanLine, ShieldCheck, Route, History } from "lucide-react";

const steps = [
  { name: "Expect", title: "Start with Route Alpha", detail: "Open Mission Control and inspect the orbital-only Jezero terrain. The original route depends on an assumption about Area 14.", icon: Layers },
  { name: "Observe", title: "Discover the difference", detail: "Choose Observe, then Analyze terrain. The curated boulder-field replay creates provisional evidence.", icon: ScanLine },
  { name: "Compare", title: "Understand the impact", detail: "Read the expected-versus-observed evidence and the challenged route segment.", icon: Compass },
  { name: "Verify", title: "Make the human decision", detail: "Open Verify and confirm the observation. The AI cannot independently declare ground truth.", icon: ShieldCheck },
  { name: "Learn", title: "Watch the route change", detail: "Inspect Route Beta and its modeled distance. The original orbital prior remains available.", icon: Route },
  { name: "Inherit", title: "Hand knowledge to the next EVA", detail: "Open the future EVA or choose EVA-02. The verified discovery is inherited by the next mission.", icon: History },
];

export default function JudgeGuide() {
  return <main className="mars-experience">
    <header className="mx-header"><Link className="mx-outline" href="/"><ArrowLeft size={16}/> Home</Link><span className="mx-kicker">TEAM REDSCAPE / JUDGE GUIDE</span><Link className="mx-outline" href="/science">Science &amp; limits</Link></header>
    <section className="mx-journey" aria-labelledby="judge-title">
      <div className="mx-section-heading"><p className="mx-kicker">YOUR FIRST MARS MISSION</p><h1 id="judge-title">Discover it. Verify it. Pass it on.</h1><p>One guided journey demonstrates the living map. No account needed. The demonstration uses genuine NASA imagery and an explicitly simulated mission.</p></div>
      <PublicDemoButton/>
      <div className="mx-stage-grid judge-stage-grid">{steps.map(({name,title,detail,icon:Icon},i)=><article key={name}><div className="mx-stage-top"><Icon size={24}/><span>0{i+1} / 06</span></div><small>{name}</small><h3>{title}</h3><p>{detail}</p></article>)}</div>
      <div className="judge-result"><CheckCircle2 size={26}/><div><h2>What success looks like</h2><p>Route Alpha is retained, verified evidence changes local map knowledge, Route Beta is calculated, and EVA-02 inherits the discovery. Guest evidence is isolated and temporary.</p></div></div>
      <div className="mx-journey-action"><PublicDemoButton compact/><Link href="/signup" className="mx-outline">Advanced private workspace <ArrowRight size={16}/></Link></div>
    </section>
  </main>;
}
