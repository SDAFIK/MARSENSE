import Image from "next/image";
import Link from "next/link";
import { Orbit, ArrowLeft, ArrowUpRight } from "lucide-react";
import PublicDemoButton from "@/components/public-demo-button";

const sources = [
  ["01 / ORBITAL","CTX + HiRISE","Cached NASA Mars Trek imagery supplies the Jezero orbital prior and local map. Display tints and illustrative mission geometry are separate from source pixels."],
  ["02 / ELEVATION","HiRISE DTM + MOLA","Genuine terrain samples support bounded, modeled slope analysis. Regional MOLA data is not a foot-scale hazard map; local slope is excluded if unavailable."],
  ["03 / GROUND","Navcam + Mastcam-Z","Calibrated rover products and cached ground imagery support source inspection. Replay footprints are illustrative; uploaded images require manual localization."],
  ["04 / LOCALIZATION","Mars 2020 PLACES","Rover pose and clock joins are retained with their limitations. Unknown or ambiguous camera footprints are not silently geolocated."],
  ["05 / PERCEPTION","AI4Mars","The genuine experimental classifier did not meet the required reliability threshold. The prototype uses conservative texture features and explicit human interpretation."],
  ["06 / SCIENCE CONTEXT","CRISM","Orbital spectral browse and coverage provide context. False-color imagery does not establish mineral identity."],
];

export default function SciencePage() {
  return <main className="science-brief">
    <header><Link className="wordmark" href="/"><Orbit size={28}/><span className="brand-stack"><span>MAR<span>SENSE</span></span><small>THE LIVING MARS MAP</small></span></Link><Link className="button secondary" href="/"><ArrowLeft size={16}/> Home</Link></header>
    <section className="science-hero"><Image fill unoptimized sizes="100vw" src="/api/assets/ground-navcam.jpg" alt="Cached NASA Perseverance Mars terrain"/><p className="eyebrow">TEAM REDSCAPE / NASA SPACE APPS 2026</p><h1>Science behind the <span>living map</span></h1><p>NASA tells us what we expect. Ground observations challenge our assumptions. Human verification determines which supported knowledge changes the map and informs future EVAs.</p><PublicDemoButton/></section>
    <section className="science-grid" aria-label="NASA source inventory">{sources.map(([type,title,detail])=><article key={title}><p className="eyebrow">{type}</p><h2>{title}</h2><p>{detail}</p></article>)}</section>
    <section className="science-limits"><h2>Scientific limits</h2><p>MARSENSE is an experimental decision-support research prototype, not certified astronaut navigation. The mission scenario, local geometry and replay interpretation are simulated. The source imagery and documented data products are genuine. Route distances are modeled; neither safety, suit telemetry nor classifier confidence is fabricated.</p><p>Human decisions update only supported footprints. Orbital priors and previous decisions remain in history; persistent knowledge can be inherited by a later EVA while dynamic observations expire.</p></section>
    <section className="science-links" aria-label="Project documentation"><a className="button secondary" href="https://github.com/SDAFIK/MARSENSE/blob/master/NASA_SOURCE_MATRIX.md">NASA source matrix <ArrowUpRight size={14}/></a><a className="button secondary" href="https://github.com/SDAFIK/MARSENSE/blob/master/SCIENTIFIC_AUDIT.md">Scientific audit <ArrowUpRight size={14}/></a><a className="button secondary" href="https://github.com/SDAFIK/MARSENSE">GitHub repository <ArrowUpRight size={14}/></a></section>
    <footer>NASA/JPL-Caltech and individual product credits are retained in source manifests. No NASA endorsement or operational certification is claimed.</footer>
  </main>;
}
