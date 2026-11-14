"use client";
import { useState } from "react";
import type { Snapshot } from "@/lib/types";
import { label } from "@/lib/api";
import LivingMap from "./living-map";
import { InheritedMemory } from "./mission-memory";
export default function SpatialMemory({
  snapshot,
  onFuture,
}: {
  snapshot: Snapshot;
  onFuture: () => void;
}) {
  const events = [...snapshot.events].sort(
    (a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp),
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  function selectMemory(id: string) {
    setSelectedId(id);
    if (window.matchMedia("(max-width: 1099px)").matches) requestAnimationFrame(() => document.getElementById("memory-detail")?.scrollIntoView({ block: "start" }));
  }
  const normalized = query.trim().toLowerCase();
  const filtered = events.filter((e) => {
    const record = snapshot.evidence.find((item) => item.id === e.evidence_id);
    return [e.title, e.detail, e.timestamp, record?.observed_value, record?.verification_state]
      .join(" ").toLowerCase().includes(normalized);
  });
  const event = filtered.find((e) => e.id === selectedId);
  const evidence = snapshot.evidence.find((e) => e.id === event?.evidence_id);
  return (
    <div className="spatial-memory"><section className="memory-hero"><p className="eyebrow">EXPLORATION MEMORY</p><h2>Knowledge that Lives On</h2><p>Every verified observation becomes part of the living map.</p><div className="memory-stats"><span>{snapshot.events.length} recorded events</span><span>{snapshot.evidence.filter(e=>e.source_type!=="orbital" && e.verification_state==="CONFIRMED").length} confirmed ground records</span><span>{snapshot.mission.inherited_evidence.length} inherited records</span></div></section>
      <aside className="panel">
        <div className="panel-heading">
          <h2>MISSION TIMELINE · {snapshot.mission.eva}</h2>
        </div>
        <div className="memory-search"><label htmlFor="memory-search">Search mission history</label><input id="memory-search" type="search" value={query} onChange={(e) => { setQuery(e.target.value); setSelectedId(null); }} placeholder="Terrain, decision, event…"/><p role="status" className="small muted">{filtered.length} of {events.length} events</p></div>
        <div className="spatial-event-list">
          {!filtered.length && <p className="small muted">No matching events. Try another search.</p>}
          {filtered.map((e) => (
            <button
              key={e.id}
              aria-pressed={e.id === selectedId}
              onClick={() => selectMemory(e.id)}
            >
              <span>
                {new Date(e.timestamp).toISOString().slice(11, 19)} UTC
              </span>
              <strong>{e.title}</strong>
              <small>
                {e.evidence_id ? "Inspect observation →" : "Orbital context →"}
              </small>
            </button>
          ))}
        </div>
      </aside>
      <div className="spatial-memory-map" id="memory-map">
        <LivingMap
          snapshot={snapshot}
          focusLocation={evidence?.location}
          warmPresentation
        />
      </div>
      <aside className="panel" id="memory-detail" aria-label="Selected memory details">
        <div className="panel-heading">
          <h2>{evidence ? "SELECTED EVIDENCE" : "DURABLE MEMORY"}</h2>
        </div>
        <div className="panel-body">
          {event ? (
            <>
              <h3>{event.title}</h3>
              <p>{event.detail}</p>
              {evidence && <button className="button secondary" onClick={() => document.getElementById("memory-map")?.scrollIntoView({ block: "start" })}>Locate on map</button>}
              {evidence && (
                <>
                  <span className={`badge ${evidence.verification_state === "CONFIRMED" ? "green" : "amber"}`}>
                    {label(evidence.verification_state)}
                  </span>
                  <p>
                    {label(evidence.observed_value)} ·{" "}
                    {evidence.verified_by ?? "Human review pending"}
                  </p>
                  <p>{evidence.verification_note}</p>
                </>
              )}
            </>
          ) : (
            <p>
              Select a chronological event to highlight its supported location
              and open the corresponding context.
            </p>
          )}
          <h3>INHERITED KNOWLEDGE</h3>
          {snapshot.evidence
            .filter(
              (e) =>
                e.verification_state === "CONFIRMED" &&
                e.source_type !== "orbital" &&
                e.persistence_type === "persistent" &&
                !e.superseded_by?.length,
            )
            .map((e) => (
              <p className="inherited-row" key={e.id}>
                {snapshot.regions.find((r) => r.id === e.region_id)?.name}
                <br />
                <strong>GROUND-OBSERVED</strong>
                <br />
                Recorded in {e.mission_id.toUpperCase()}
                {snapshot.mission.inherited_evidence.includes(e.id) &&
                  " · INHERITED FROM EVA-01"}
              </p>
            ))}
          <p className="small muted">
            Dynamic conditions expire and remain historical observations.
          </p>
        </div>
      </aside>
      <div className="memory-inheritance">
        <InheritedMemory
          snapshot={snapshot}
          onSwitch={snapshot.mission.id === "eva-01" ? onFuture : undefined}
        />
      </div>
    </div>
  );
}
