"use client";
import { useState } from "react";
import type { Snapshot } from "@/lib/types";
import LivingMap from "./living-map";
import RouteSummary from "./route-summary";
export default function BeforeAfter({ snapshot }: { snapshot: Snapshot }) {
  const [split, setSplit] = useState(50);
  const confirmed = snapshot.evidence.some(
    (e) =>
      e.source_type !== "orbital" &&
      e.verification_state === "CONFIRMED" &&
      !e.superseded_by?.length &&
      e.persistence_type === "persistent",
  );
  return (
    <div className="spatial-comparison">
      <section
        className="aligned-maps"
        aria-label="Aligned before and after Mars maps"
      >
        <div className="aligned-map before-map">
          <LivingMap snapshot={snapshot} before warmPresentation locked />
        </div>
        <div
          className="aligned-map after-map"
          style={{ clipPath: `inset(0 0 0 ${split}%)` }}
        >
          <LivingMap snapshot={snapshot} warmPresentation locked />
        </div>
        <div
          className="comparison-divider"
          style={{ left: `${split}%` }}
          aria-hidden="true"
        />
        <span className="comparison-label before-label">
          BEFORE · ORBITAL-ONLY
        </span>
        <span className="comparison-label after-label">
          {confirmed
            ? "AFTER · GROUND-OBSERVED"
            : "AFTER · AWAITING VERIFICATION"}
        </span>
      </section>
      <section className="comparison-controls panel">
        <div>
          <label htmlFor="map-split">Compare the same aligned map extent</label>
          <input
            id="map-split"
            aria-label="Before / After map slider"
            type="range"
            min="0"
            max="100"
            value={split}
            onChange={(e) => setSplit(Number(e.target.value))}
          />
        </div>
        <div className="comparison-toggles">
          <button
            className="button secondary"
            aria-pressed={split === 100}
            onClick={() => setSplit(100)}
          >
            Before
          </button>
          <button
            className="button secondary"
            aria-pressed={split === 50}
            onClick={() => setSplit(50)}
          >
            Split
          </button>
          <button
            className="button secondary"
            aria-pressed={split === 0}
            onClick={() => setSplit(0)}
          >
            After
          </button>
        </div>
        <p className="small muted">
          NASA prior retained. Only human-confirmed, supported footprints become
          persistent ground-observed evidence. Mission geometry is illustrative.
        </p>
      </section>
      <RouteSummary snapshot={snapshot} />
    </div>
  );
}
