"use client";

import Image from "next/image";
import Link from "next/link";
import {useMemo,useState,useSyncExternalStore} from "react";
import {ArrowRight, CheckCircle2, Compass, History, Layers, Orbit, RotateCcw, Route, ScanLine, ShieldCheck} from "lucide-react";
import {ALPHA,BETA,FOOTPRINT,HABITAT,TARGET,calculateAlternatives,parseReplay,readReplay,serverReplay,subscribeReplay,writeReplay,type Action,type Traverse} from "@/lib/judge-replay";
import styles from "./judge-demo.module.css";

const stages=[
  {name:"Expect",title:"Start with the orbital prior",icon:Layers},
  {name:"Observe",title:"Discover what the map misses",icon:ScanLine},
  {name:"Compare",title:"Two perspectives. One question.",icon:Compass},
  {name:"Verify",title:"You make the decision.",icon:ShieldCheck},
  {name:"Learn",title:"The living map adapts.",icon:Route},
  {name:"Inherit",title:"The next explorer knows more.",icon:History},
];
const points=(route:Traverse)=>route.coordinates.map(([x,y])=>x+","+ (800-y)).join(" ");
function MissionMap({confirmed=false,showFootprint=false,mode="both",alternative}:{
  confirmed?:boolean;showFootprint?:boolean;mode?:"before"|"after"|"both";alternative?:Traverse;
}) {
  return <div className={styles.map}>
    <Image src="/judge-assets/jezero-hirise.png" alt="Cached NASA HiRISE Jezero terrain" width={1200} height={800} unoptimized className={styles.mapImage} priority/>
    <svg viewBox="0 0 1200 800" role="img" aria-label={confirmed?"Illustrative route comparison with confirmed obstacle footprint and Route Beta":"Illustrative orbital-only Route Alpha schematic"} className={styles.mapOverlay}>
      <defs><pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse"><path d="M 80 0 L 0 0 0 80" fill="none" stroke="#c3e0ec" strokeWidth="1" opacity=".25"/></pattern></defs>
      <rect width="1200" height="800" fill="url(#grid)"/>
      <rect x="440" y="0" width="320" height="800" fill="#e4ad63" fillOpacity=".12" stroke="#ffdb9d" strokeWidth="3" strokeDasharray="14 8"/>
      <text x="600" y="54" textAnchor="middle" fill="#fff4dc" fontSize="29" fontWeight="600">AREA 14</text>
      {showFootprint&&<rect x={FOOTPRINT.xmin} y={800-FOOTPRINT.ymax} width={FOOTPRINT.xmax-FOOTPRINT.xmin} height={FOOTPRINT.ymax-FOOTPRINT.ymin} fill={confirmed?"#e05f44":"#ffc66f"} fillOpacity=".42" stroke={confirmed?"#ff7858":"#ffd18d"} strokeWidth="5" strokeDasharray={confirmed?undefined:"12 8"}/>}
      {(!confirmed||mode!=="after")&&<polyline points={points(ALPHA)} stroke="#f0e8dd" strokeWidth="9" strokeLinecap="round" strokeLinejoin="round" strokeDasharray={confirmed?"14 12":undefined} fill="none"/>}
      {confirmed&&mode!=="before"&&<polyline points={points(alternative??BETA)} stroke="#8fe0ba" strokeWidth="11" strokeLinecap="round" strokeLinejoin="round" fill="none"/>}
      <circle cx={HABITAT[0]} cy={800-HABITAT[1]} r="16" fill="#0b1620" stroke="#fcddb0" strokeWidth="6"/>
      <path d="M1080 381 L1099 400 L1080 419 L1061 400 Z" fill="#94e3c0" stroke="#172d30" strokeWidth="5"/>
      <text x="120" y="458" textAnchor="middle" fill="#fff" fontSize="29" fontWeight="600" paintOrder="stroke" stroke="#0d1520" strokeWidth="5">Habitat</text>
      <text x={TARGET[0]} y="458" textAnchor="middle" fill="#fff" fontSize="29" fontWeight="600" paintOrder="stroke" stroke="#0d1520" strokeWidth="5">Delta target</text>
    </svg>
    <div className={styles.mapTag}><span/> JEZERO / LOCAL GRID</div>
    <div className={styles.mapCredit}>NASA/JPL-Caltech · illustrative grid; not image-registered</div>
  </div>;
}
function GroundImage(){return <figure className={styles.photo}><Image src="/judge-assets/ground-navcam.jpg" alt="NASA Perseverance Navcam boulder-field mosaic PIA26072" width={1280} height={720} unoptimized className={styles.photoImage}/><figcaption>Perseverance Navcam · PIA26072 · genuine NASA/JPL-Caltech imagery. Location in this mission is simulated.</figcaption></figure>;}
function OrbitalImage(){return <figure className={styles.photo}><Image src="/judge-assets/jezero-ctx.png" alt="Cached NASA CTX orbital terrain in Jezero" width={1200} height={800} unoptimized className={styles.photoImage}/><figcaption>NASA Mars Trek / CTX · illustrative orbital soil interpretation, not a NASA terrain classification.</figcaption></figure>;}
export default function JudgeDemo() {
  const raw=useSyncExternalStore(subscribeReplay,readReplay,serverReplay);
  const state=useMemo(()=>parseReplay(raw),[raw]);
  const {stage,decision}=state;
  const confirmed=decision==="confirmed";
  const [mode,setMode]=useState<"before"|"after"|"both">("both");
  const [options,setOptions]=useState<Traverse[]|null>(null);
  const [selected,setSelected]=useState(0);
  function act(action:Action){
    if(action==="reset"){setOptions(null);setSelected(0);setMode("both");}
    writeReplay(action);
  }
  const route=confirmed?BETA:ALPHA;
  return <main className={styles.shell}>
    <header className={styles.header}>
      <Link href="/" className={styles.brand}><Orbit size={30}/><span>MARS<strong>ENSE</strong><small>THE LIVING MARS MAP</small></span></Link>
      <div className={styles.headerRight}><span className={styles.status}><i/> BROWSER DEMO</span><Link href="/guide" className={styles.secondary}>Guide</Link><Link href="/workspace-login" className={styles.secondary}>Cloud workspace</Link></div>
    </header>
    <section className={styles.intro}>
      <div><p className={styles.kicker}>TEAM REDSCAPE / NASA SPACE APPS 2026</p><h1>Jezero reconnaissance.</h1><p>Discover it. Verify it. Pass it on. Explore the complete mission without an account or a cloud service.</p></div>
      <div className={styles.localInfo}><CheckCircle2 size={20}/><div><strong>Instant, isolated simulation</strong><span>Runs entirely in this browser. No cloud records are changed.</span></div></div>
    </section>
    <nav className={styles.progress} aria-label="Six mission stages">{stages.map(({name,icon:Icon},i)=><div key={name} aria-current={i===stage?"step":undefined} className={i===stage?styles.current:i<stage?styles.done:styles.step}><Icon size={18}/><span><small>0{i+1}</small>{name}</span></div>)}</nav>
    <section className={styles.content} aria-label="Guided mission">
      <div className={styles.mainCard}>
        <div className={styles.cardHeading}><div><p className={styles.kicker}>0{stage+1} / 06 · {stages[stage].name.toUpperCase()}</p><h2>{stages[stage].title}</h2></div><span className={styles.chip}>{stage===5?"EVA-02 · S. CHEN":"EVA-01 · A. RAHMAN"}</span></div>
        {stage===0&&<><MissionMap/><div className={styles.legend}><span><i className={styles.alpha}/> Route Alpha</span><span>960 m modeled baseline</span><span>Area 14 · assumption A17</span></div></>}
        {stage===1&&<GroundImage/>}
        {(stage===2||stage===3)&&<><div className={styles.pair}><OrbitalImage/><GroundImage/></div><div className={styles.evidenceRow}><div><span>EXPECTED</span><strong>Soil</strong></div><ArrowRight size={22}/><div><span>OBSERVED · CURATED REPLAY</span><strong>Obstacle-rich terrain</strong></div></div><MissionMap showFootprint/></>}
        {stage===4&&<><div className={styles.metrics}><div><span>ORIGINAL TRAVERSE</span><strong>Route Alpha</strong><small>{ALPHA.distance.toFixed(0)} m</small></div><div><span>ACTIVE TRAVERSE</span><strong className={styles.green}>Route Beta</strong><small>{BETA.distance.toFixed(0)} m</small></div><div><span>DISTANCE CHANGE</span><strong className={styles.orange}>+{(BETA.distance-ALPHA.distance).toFixed(0)} m</strong><small>Modeled distance, not safety</small></div></div><MissionMap confirmed showFootprint mode={mode} alternative={options?.[selected]}/><div className={styles.mapButtons} aria-label="Route comparison">{(["before","both","after"] as const).map(v=><button key={v} aria-pressed={mode===v} onClick={()=>setMode(v)}>{v==="both"?"Compare":v==="before"?"Before":"After"}</button>)}</div></>}
        {stage===5&&<><div className={styles.inheritance}><History size={32}/><div><span className={styles.kicker}>EVA 01 → EVA 02</span><h3>One verified record inherited.</h3><p>The Area 14 obstacle footprint and its human decision travel with the next mission. The original NASA prior stays unchanged.</p></div></div><MissionMap confirmed showFootprint/><div className={styles.evidenceRow}><div><span>INHERITED EVIDENCE</span><strong>Area 14 · Confirmed</strong></div><div><span>ACTIVE MODELED TRAVERSE</span><strong>Route Beta · {BETA.distance.toFixed(0)} m</strong></div></div></>}
      </div>
      <aside className={styles.side}>
        <div className={styles.panel}>
          <p className={styles.kicker}>MISSION ACTION</p>
          {stage===0&&<><h3>What do we expect?</h3><p>NASA orbital imagery supplies the context. This simulated EVA starts with a low-obstacle soil assumption along Route Alpha.</p><div className={styles.note}>A17: Area 14 is assumed to contain continuous, low-obstacle soil.</div><button className={styles.primary} onClick={()=>act("observe")}>Go to observation <ArrowRight size={18}/></button></>}
          {stage===1&&<><h3>Look closer.</h3><p>Use the real Navcam boulder-field image in the curated Area 14 replay. This is a predefined scenario, not live model inference or automatic camera localization.</p><button className={styles.primary} onClick={()=>act("analyze")}>Analyze terrain <ScanLine size={18}/></button></>}
          {stage===2&&<><h3>Assumption challenged.</h3><p>Obstacle-rich terrain differs from the orbital soil interpretation. The simulated 160 × 160 m footprint intersects Route Alpha.</p><div className={styles.note}>Provisional evidence · human review required. The map has not been updated.</div><button className={styles.primary} onClick={()=>act("review")}>Open human review <ShieldCheck size={18}/></button></>}
          {stage===3&&<><h3>Human review</h3><p>Confirm only the supported footprint. The original orbital prior remains immutable.</p>{decision==="rejected"?<><div role="status" className={styles.note}>Rejected. Route Alpha remains active. No knowledge is added.</div><button className={styles.primary} onClick={()=>act("reset")}>Restart demo <RotateCcw size={18}/></button></>:<>{decision==="more"&&<div role="status" className={styles.note}>More evidence requested. Route Alpha remains unchanged.</div>}<button className={styles.primary} onClick={()=>act("confirm")}>Confirm observation <CheckCircle2 size={18}/></button><button className={styles.secondary} onClick={()=>act("reject")}>Reject observation</button>{decision==="more"?<button className={styles.secondary} onClick={()=>act("analyze")}>Review another replay</button>:<button className={styles.secondary} onClick={()=>act("more")}>Request more evidence</button>}</>}</>}
          {stage===4&&<><h3>Verified. Recalculated.</h3><p>Confirmation blocks only the supported obstacle footprint. A browser-local A* search calculates Route Beta using the same 40 m grid and distance/uncertainty cost rules as the backend’s no-slope teaching scenario.</p><div className={styles.note}>Confirmed by Guest reviewer (simulation). No certified safe route is claimed.</div><button className={styles.primary} onClick={()=>act("inherit")}>Continue to next EVA <ArrowRight size={18}/></button><button className={styles.secondary} onClick={()=>{setOptions(calculateAlternatives(true));setSelected(0);setMode("after");}}>Calculate route options</button>{options&&<div className={styles.options} role="status">{options.map((p,i)=><button key={i} aria-pressed={selected===i} onClick={()=>{setSelected(i);setMode("after");}}>{i===0?"Lowest modeled cost": "Alternative "+i}<strong>{p.distance.toFixed(0)} m</strong></button>)}<small>Read-only bounded search; not a safety ranking.</small></div>}</>}
          {stage===5&&<><h3>Every mission builds knowledge.</h3><p>EVA-02 inherits the confirmed obstacle record. The next explorer starts with more knowledge than EVA-01, without losing the original evidence.</p><div className={styles.success}><CheckCircle2 size={20}/> Mission complete</div><button className={styles.primary} onClick={()=>act("reset")}>Replay the mission <RotateCcw size={18}/></button><Link className={styles.secondary} href="/science">Explore NASA sources <ArrowRight size={16}/></Link></>}
        </div>
        <div className={styles.panel}><p className={styles.kicker}>MISSION STATE</p><dl className={styles.state}><div><dt>Active route</dt><dd>{confirmed?"Route Beta":"Route Alpha"}</dd></div><div><dt>Modeled distance</dt><dd>{route.distance.toFixed(0)} m</dd></div><div><dt>Human decision</dt><dd>{decision==="none"?"Not observed":decision==="pending"?"Provisional":decision==="more"?"More evidence":decision==="confirmed"?"Confirmed":"Rejected"}</dd></div><div><dt>Inherited records</dt><dd>{stage===5?1:0}</dd></div></dl><button className={styles.secondary} onClick={()=>act("reset")}><RotateCcw size={16}/> Reset demo</button></div>
        <div className={styles.panel}><p className={styles.kicker}>SCIENCE &amp; PROVENANCE</p><p>Genuine NASA CTX, HiRISE and Navcam imagery. The EVA, route grid, local image footprint and replay annotation are illustrative. Slope is excluded. This is decision-support research, not certified astronaut navigation.</p><a href="https://github.com/SDAFIK/MARSENSE/blob/master/NASA_SOURCE_MATRIX.md" target="_blank" rel="noreferrer">Source matrix ↗</a></div>
      </aside>
    </section>
    <footer className={styles.footer}><span>MARSENSE · Team Redscape · NASA Space Apps 2026</span><span>Browser-local replay · Every step makes Mars more known.</span></footer>
  </main>;
}
