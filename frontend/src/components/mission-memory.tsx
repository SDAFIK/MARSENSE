import { ArrowUpRight, CheckCircle2, History } from "lucide-react";
import Link from "next/link";
import { label } from "@/lib/api";
import type { Snapshot } from "@/lib/types";
export function MissionMemory({
  snapshot,
  compact = false,
}: {
  snapshot: Snapshot;
  compact?: boolean;
}) {
  const events = compact ? snapshot.events.slice(0, 3) : snapshot.events;
  return (
    <section className="panel memory-panel">
      <div className="panel-heading">
        <h2>
          <History size={17} />{" "}
          {compact ? "Mission activity" : "Exploration timeline"}
        </h2>
        <span className="small-mono">PERSISTENT MEMORY</span>
      </div>
      <div className="panel-body">
        <ol className="timeline">
          {events.map((event) => (
            <li key={event.id}>
              <span className="timeline-dot" />
              <span className="small-mono">
                {new Date(event.timestamp).toISOString().slice(11, 19)} UTC ·{" "}
                {label(event.kind)}
              </span>
              <h3>{event.title}</h3>
              <p>{event.detail}</p>
              {event.evidence_id && !compact && (
                <span className="small-mono muted">{event.evidence_id}</span>
              )}
            </li>
          ))}
        </ol>
        {compact && (
          <Link className="text-link" href="/memory">
            View exploration memory <ArrowUpRight size={14} />
          </Link>
        )}
      </div>
    </section>
  );
}
export function InheritedMemory({
  snapshot,
  onSwitch,
}: {
  snapshot: Snapshot;
  onSwitch?: () => void;
}) {
  const verified = snapshot.evidence.filter(
    (e) =>
      e.source_type !== "orbital" &&
      e.verification_state === "CONFIRMED" &&
      !e.superseded_by?.length &&
      e.persistence_type === "persistent",
  );
  return (
    <section className="inheritance-banner">
      <CheckCircle2 size={21} />
      <div>
        <span className="eyebrow">KNOWLEDGE THAT OUTLASTS THE EVA</span>
        <h2>
          {snapshot.mission.id === "eva-02" && verified.length
            ? "You’re starting where the last explorer left off."
            : verified.length
              ? "The next explorer won’t start from zero."
              : "Every verified observation becomes exploration memory."}
        </h2>
        <p>
          {verified.length
            ? `${verified.length} verified ground observation${verified.length === 1 ? "" : "s"} preserved. ${snapshot.mission.inherited_evidence.length} inherited by this EVA.`
            : "Confirm ground evidence to pass on a more informed route."}
        </p>
      </div>
      {onSwitch && (
        <button className="button secondary" onClick={onSwitch}>
          Start future EVA <ArrowUpRight size={15} />
        </button>
      )}
    </section>
  );
}
