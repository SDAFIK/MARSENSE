"use client";

import Image from "next/image";
import Link from "next/link";
import { Activity, Database, Layers, Radar, RefreshCw, Route, ScanLine } from "lucide-react";
import { useState } from "react";
import { label } from "@/lib/api";
import type { Snapshot } from "@/lib/types";
import LivingMap from "./living-map";
import MarsGlobe from "./mars-globe";

const datasets = [
  { id: "hirise", name: "HiRISE", detail: "High-resolution orbital imagery", asset: "/api/assets/jezero-hirise.png" },
  { id: "ctx", name: "CTX", detail: "Regional orbital context", asset: "/api/assets/jezero-ctx.png" },
  { id: "ground", name: "Navcam", detail: "Cached ground imagery", asset: "/api/assets/ground-navcam.jpg" },
] as const;

export default function IntelligenceCenter({ snapshot, refresh, loading, error }: {
  snapshot: Snapshot;
  refresh: () => Promise<boolean>;
  loading: boolean;
  error: string | null;
}) {
  const [dataset, setDataset] = useState<(typeof datasets)[number]["id"]>("hirise");
  const [eventId, setEventId] = useState("");
  const selected = datasets.find(item => item.id === dataset) ?? datasets[0];
  const manifest = snapshot.data_status.manifest;
  const available = selected.id === "ground" ? Boolean(manifest.ground) : Boolean(manifest[selected.id]);
  const events = [...snapshot.events].sort((a,b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));
  const event = events.find(item => item.id === eventId) ?? events[0];
  const evidence = snapshot.evidence.find(item => item.id === event?.evidence_id);
  const ground = snapshot.evidence.filter(item => item.source_type !== "orbital");
  const confirmed = ground.filter(item => item.verification_state === "CONFIRMED" && !item.superseded_by?.length);
  const active = snapshot.routes.find(item => item.id === snapshot.mission.active_route_id);
  const alpha = snapshot.routes.find(item => item.version === 1);
  const beta = active && active.version > 1 ? active : undefined;
  const stages = [
    {name:"Expect", done:Boolean(alpha)},
    {name:"Observe", done:ground.length > 0},
    {name:"Compare", done:ground.some(item => item.consequence.relevant)},
    {name:"Verify", done:confirmed.length > 0},
    {name:"Learn", done:Boolean(beta)},
    {name:"Inherit", done:snapshot.mission.inherited_evidence.length > 0},
  ];
  return <div className="intel-console">
    <section className="intel-top">
      <div><p className="eyebrow">MARSENSE / SCIENCE OPERATIONS</p><h2>Mars Intelligence Center</h2><p>NASA-derived context · mission intelligence · evidence provenance</p></div>
      <div className="intel-actions"><span className="intel-status" role="status"><Activity size={16}/>{error ? "Connection interrupted" : loading ? "Refreshing" : "Mission data loaded"}</span><button className="button secondary" disabled={loading} onClick={() => void refresh()}><RefreshCw size={15}/> Refresh data</button></div>
    </section>
    <section className="intel-flow" aria-label="Mission data flow">
      {stages.map((stage,i) => <div key={stage.name} data-complete={stage.done}><span>{String(i+1).padStart(2,"0")}</span><strong>{stage.name}</strong><small>{stage.done ? "Recorded" : "Pending"}</small></div>)}
    </section>
    <div className="intel-grid">
      <div className="intel-overview"><MarsGlobe/><section className="panel intel-briefing" aria-label="Current mission briefing"><div className="panel-heading"><h2><Route size={17}/> Current mission</h2><span className="badge neutral">{snapshot.mission.eva}</span></div><div className="panel-body"><span className="eyebrow">ACTIVE SCIENCE TARGET</span><h3>{snapshot.target.name}</h3><p>{snapshot.target.objective}</p><div className="intel-brief-metrics"><div><span>Active traverse</span><strong>{active?.name ?? "Unavailable"}</strong></div><div><span>Modeled distance</span><strong>{active && active.status !== "NO_ROUTE" ? `${active.distance_m.toFixed(0)} m` : "Unavailable"}</strong></div><div><span>Human-confirmed records</span><strong>{confirmed.length}</strong></div><div><span>Mission stages recorded</span><strong>{stages.filter(stage => stage.done).length} / {stages.length}</strong></div></div><p className="small muted">Derived from this mission snapshot. No live astronaut telemetry or certified safety claim.</p><Link className="button primary" href="/mission">Open mission control</Link></div></section></div>
      <section className="panel intel-datasets">
        <div className="panel-heading"><h2><Database size={17}/> NASA data inventory</h2></div>
        <div className="intel-source-list" aria-label="Select NASA imagery">
          {datasets.map(item => <button key={item.id} aria-pressed={dataset===item.id} onClick={()=>setDataset(item.id)}><Layers size={17}/><span><strong>{item.name}</strong><small>{item.detail}</small></span></button>)}
        </div>
        <div className="panel-body intel-provenance"><p className="eyebrow">SOURCE STATUS</p><p>{available ? "Cached source metadata available" : "Source metadata unavailable"}</p><p className="small muted">Terrain prior: {snapshot.data_status.terrain_prior}</p><p className="small muted">Slope: {snapshot.data_status.slope}</p><Link className="button secondary" href="https://github.com/SDAFIK/MARSENSE/blob/master/NASA_SOURCE_MATRIX.md">Source matrix ↗</Link></div>
      </section>
      <section className="panel intel-map">
        <div className="panel-heading"><h2><Radar size={17}/> Jezero / mission geography</h2><span className="small muted">{snapshot.mission.eva}</span></div>
        <LivingMap snapshot={snapshot} focusLocation={evidence?.location} warmPresentation/>
        <div className="panel-body intel-map-footer"><span>18.44° N · 77.45° E</span><span>Local metric geometry · illustrative mission</span></div>
      </section>
      <section className="panel intel-image">
        <div className="panel-heading"><h2><ScanLine size={17}/> {selected.name} image monitor</h2></div>
        <div className="intel-preview"><Image fill unoptimized sizes="(max-width: 768px) 95vw, 320px" src={selected.asset} alt={selected.detail}/></div>
        <div className="panel-body intel-provenance"><p>{selected.detail}</p><p className="small muted">{selected.id === "ground" ? manifest.ground?.registration ?? "Illustrative ground association; not live camera footage." : "Genuine cached NASA pixels. Mission overlays are illustrative."}</p><p className="eyebrow">ANALYSIS METHOD</p><p>{snapshot.data_status.model}</p><p className="small muted">Human verification determines whether evidence updates the map.</p><Link className="button secondary" href="/evidence">Open evidence inspector</Link></div>
      </section>
      <section className="panel intel-events">
        <div className="panel-heading"><h2><Activity size={17}/> Mission event console</h2><span className="small muted">{events.length} recorded</span></div>
        <div className="intel-event-list">{events.length ? events.map(item => <button key={item.id} aria-pressed={event?.id===item.id} onClick={()=>setEventId(item.id)}><span>{new Date(item.timestamp).toISOString().slice(11,19)} UTC</span><strong>{item.title}</strong><small>{label(item.kind)}</small></button>) : <p>No recorded events yet.</p>}</div>
        {event && <div className="panel-body intel-event-detail"><strong>{event.title}</strong><p>{event.detail}</p>{evidence && <p className="small muted">Evidence: {label(evidence.verification_state)} · {label(evidence.observed_value)}</p>}</div>}
      </section>
      <section className="panel intel-route">
        <div className="panel-heading"><h2><Route size={17}/> Route intelligence</h2><Link href="/comparison">Compare ↗</Link></div>
        <div className="intel-route-grid">{[alpha,beta].map((item,i)=><article key={i}><span className="eyebrow">{i===0 ? "ORIGINAL" : "ALTERNATIVE"}</span><h3>{item?.name ?? "Pending review"}</h3>{item ? <><strong>{item.status==="NO_ROUTE" ? "No route" : (item.distance_m/1000).toFixed(2)+" km"}</strong><p>{label(item.status)}</p><p className="small muted">{item.explanation}</p></> : <p className="small muted">Generated from supported, verified evidence when the route changes.</p>}</article>)}</div>
        <div className="intel-counts"><div><strong>{ground.length}</strong><span>Ground records</span></div><div><strong>{confirmed.length}</strong><span>Confirmed</span></div><div><strong>{snapshot.mission.inherited_evidence.length}</strong><span>Inherited</span></div></div>
        <p className="small muted intel-note">Modeled distances; no certified safety, energy or live astronaut telemetry is claimed.</p>
      </section>
    </div>
  </div>;
}
