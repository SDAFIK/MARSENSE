"use client";
import Link from "next/link";
import Image from "next/image";
import { Camera, Map, ScanLine, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { label } from "@/lib/api";
import type { Evidence, Snapshot } from "@/lib/types";
import LivingMap from "./living-map";
import RouteSummary from "./route-summary";
import ObservationPanel from "./observation-panel";
import EvidenceReview from "./evidence-review";
export default function AstronautWorkspace({
  snapshot,
  selected,
  missionId,
  busy,
  setBusy,
  observed,
  verified,
}: {
  snapshot: Snapshot;
  selected?: Evidence;
  missionId: string;
  busy: boolean;
  setBusy: (busy: boolean) => void;
  observed: (e: Evidence) => Promise<void>;
  verified: () => Promise<void>;
}) {
  const [context, setContext] = useState("OBSERVE");
  const route = snapshot.routes.find(
    (r) => r.id === snapshot.mission.active_route_id,
  );
  const pending =
    selected &&
    ["PROVISIONAL", "NEEDS_MORE_EVIDENCE"].includes(
      selected.verification_state,
    );
  return (
    <div className="astronaut-console">
      <aside className="panel">
        <div className="panel-heading">
          <h2>NEXT TARGET</h2>
        </div>
        <div className="panel-body">
          <h3>{snapshot.target.name}</h3>
          <dl>
            <dt>Modeled route distance</dt>
            <dd>{route?.distance_m.toFixed(0) ?? "Unavailable"} m</dd>
            <dt>Route state</dt>
            <dd>
              {route?.name} · {label(route?.status ?? "UNKNOWN")}
            </dd>
          </dl>
          <h3>RETURN-STATE ASSUMPTION</h3>
          <p>{snapshot.assumptions[0]?.statement}</p>
          <span className="badge neutral">
            {label(snapshot.assumptions[0]?.status ?? "UNKNOWN")}
          </span>
          {selected?.consequence.relevant && pending && (
            <div className="alert-banner">
              <strong>
                {selected.consequence.alert ?? "Route dependency challenged"}
              </strong>
              <p>{selected.consequence.explanation}</p>
            </div>
          )}
          {selected?.consequence.relevant && selected.verification_state === "CONFIRMED" && <div className="inherited-row"><strong>GROUND-OBSERVED EVIDENCE</strong><p>{label(selected.observed_value)} · confirmed by {selected.verified_by}. The active route reflects the supported footprint.</p></div>}
          <div className="astronaut-context-buttons">
            <button
              className="button secondary full"
              onClick={() => setContext("WHY")}
            >
              WHY THIS CHANGE?
            </button>
            <Link className="button secondary full" href="/comparison">
              COMPARE
            </Link>
            <button
              className="button secondary full"
              onClick={() => setContext("OBSERVE")}
            >
              REQUEST / RECORD EVIDENCE
            </button>
            {pending && (
              <button
                className="button primary full"
                onClick={() => setContext("VERIFY")}
              >
                HUMAN VERIFICATION
              </button>
            )}
          </div>
          <p className="annotation-note">
            Decision support. Field assessment required.
          </p>
        </div>
      </aside>
      <div className="astronaut-map-stage">
        <section className="panel ground-stage" aria-label="Ground observation view">
          <div className="panel-heading"><h2><Camera size={17}/> Ground observation</h2><span className="badge neutral">{selected ? label(selected.source_type) : "CACHED NASA NAVCAM"}</span></div>
          <div className="ground-stage-image"><Image unoptimized fill sizes="(max-width: 900px) 90vw, 820px" src={selected?.raw_asset_reference ?? "/api/assets/ground-navcam.jpg"} alt="Selected ground evidence or cached Perseverance Navcam context" /><div className="ground-caption"><span className="eyebrow">JEZERO · GROUND CONTEXT</span><strong>{selected ? label(selected.observed_value) : "Awaiting ground observation"}</strong><p>{selected?.source ?? "Cached NASA rover image, not a live astronaut camera."}</p></div></div>
          <div className="ground-actions"><button className="button primary" onClick={()=>setContext("OBSERVE")}><Camera size={15}/> Record observation</button><button className="button secondary" onClick={()=>setContext("WHY")}><Map size={15}/> Route context</button><Link href="/evidence" className="button secondary"><ScanLine size={15}/> Inspect evidence</Link>{pending && <button className="button secondary" onClick={()=>setContext("VERIFY")}><ShieldCheck size={15}/> Review evidence</button>}</div>
        </section>
        <LivingMap snapshot={snapshot} warmPresentation />
      </div>
      <aside className="panel astronaut-context">
        {context === "WHY" && <RouteSummary snapshot={snapshot} />}{" "}
        {context === "OBSERVE" && (
          <ObservationPanel
            missionId={missionId}
            busy={busy}
            setBusy={setBusy}
            onComplete={observed}
          />
        )}{" "}
        {context === "VERIFY" && selected && (
          <EvidenceReview
            key={selected.id}
            evidence={selected}
            reviewer={snapshot.astronaut.name}
            onVerified={verified}
          />
        )}
      </aside>
    </div>
  );
}
