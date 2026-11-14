"use client";
import Link from "next/link";
import Image from "next/image";
import { Camera, Map, ScanLine, ShieldCheck } from "lucide-react";
import { useRef, useState } from "react";
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
  const contextRef = useRef<HTMLElement>(null);
  const openContext = (next: string) => {
    setContext(next);
    if (window.matchMedia("(max-width: 1249px)").matches) requestAnimationFrame(() => contextRef.current?.scrollIntoView({ block: "start" }));
  };
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
          <div className="field-kicker"><ShieldCheck size={14}/> FIELD DECISION SUPPORT</div>
          <h3 className="field-target">{snapshot.target.name}</h3>
          <dl>
            <dt>Modeled route distance</dt>
            <dd className="field-metric">{route ? `${route.distance_m.toFixed(0)} m` : "Unavailable"}</dd>
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
              onClick={() => openContext("WHY")}
            >
              WHY THIS CHANGE?
            </button>
            <Link className="button secondary full" href="/comparison">
              COMPARE
            </Link>
            <button
              className="button secondary full"
              onClick={() => openContext("OBSERVE")}
            >
              REQUEST / RECORD EVIDENCE
            </button>
            {pending && (
              <button
                className="button primary full"
                onClick={() => openContext("VERIFY")}
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
          <div className="ground-actions"><button className="button primary" onClick={()=>openContext("OBSERVE")}><Camera size={15}/> Record observation</button><button className="button secondary" onClick={()=>openContext("WHY")}><Map size={15}/> Route context</button><Link href="/evidence" className="button secondary"><ScanLine size={15}/> Inspect evidence</Link>{pending && <button className="button secondary" onClick={()=>openContext("VERIFY")}><ShieldCheck size={15}/> Review evidence</button>}</div>
        </section>
        <LivingMap snapshot={snapshot} warmPresentation />
      </div>
      <aside ref={contextRef} className="panel astronaut-context" aria-label="Observation and decision controls">
        <div className="field-tabs" aria-label="Field controls">
          <button className="button secondary" aria-pressed={context === "OBSERVE"} onClick={() => setContext("OBSERVE")}>Observe</button>
          <button className="button secondary" aria-pressed={context === "WHY"} onClick={() => setContext("WHY")}>Route</button>
          {selected && <button className="button secondary" aria-pressed={context === "VERIFY"} onClick={() => setContext("VERIFY")}>Review</button>}
        </div>
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
