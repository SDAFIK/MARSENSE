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
  const event = events.find((e) => e.id === selectedId);
  const evidence = snapshot.evidence.find((e) => e.id === event?.evidence_id);
  return (
    <div className="spatial-memory">
      <aside className="panel">
        <div className="panel-heading">
          <h2>MISSION TIMELINE · {snapshot.mission.eva}</h2>
        </div>
        <div className="spatial-event-list">
          {events.map((e) => (
            <button
              key={e.id}
              aria-pressed={e.id === selectedId}
              onClick={() => setSelectedId(e.id)}
            >
              <span>
                {new Date(e.timestamp).toISOString().slice(11, 19)} UTC
              </span>
              <strong>{e.title}</strong>
              <small>
                {e.evidence_id ? "Locate observation" : "Orbital context"}
              </small>
            </button>
          ))}
        </div>
      </aside>
      <div className="spatial-memory-map">
        <LivingMap
          snapshot={snapshot}
          focusLocation={evidence?.location}
          warmPresentation
        />
      </div>
      <aside className="panel">
        <div className="panel-heading">
          <h2>{evidence ? "SELECTED EVIDENCE" : "DURABLE MEMORY"}</h2>
        </div>
        <div className="panel-body">
          {event ? (
            <>
              <h3>{event.title}</h3>
              <p>{event.detail}</p>
              {evidence && (
                <>
                  <span className="badge green">
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
